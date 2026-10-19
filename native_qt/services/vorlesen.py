"""Vorlesen: Piper (offline, gute Stimme) wenn eingerichtet, sonst speech-dispatcher (spd-say).

Übernommen aus der alten Web-Fassung (Zweig main, start.py) (piper_*, vorlesen_*): gleiche Suchorte, gleiche Stimmennamen. Es wird nichts
heruntergeladen — Piper kommt über ./stimme-holen.sh, auf ausdrücklichen Wunsch.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading

PIPER_ORTE = [os.path.expanduser("~/.local/share/lunivo-office/piper"),
              os.path.expanduser("~/.local/share/schreibhilfe/piper")]
PIPER_NAMEN = {
    "de_DE-thorsten-medium": "Thorsten (männlich)", "de_DE-thorsten-high": "Thorsten, feiner (männlich)",
    "de_DE-thorsten-low": "Thorsten, gröber (männlich)", "de_DE-karlsson-low": "Karlsson (männlich)",
    "de_DE-pavoque-low": "Pavoque (männlich)", "de_DE-kerstin-low": "Kerstin (weiblich)",
    "de_DE-ramona-low": "Ramona (weiblich)", "de_DE-eva_k-x_low": "Eva (weiblich)",
    "de_DE-mls-medium": "Gemischt (mehrere Sprecher)",
    "de_DE-thorsten_emotional-medium": "Thorsten mit Gefühl (männlich)",
}
MAX_ZEICHEN = 20000
_lauf: dict = {"ton": None, "rechner": None}


class VorlesenFehler(Exception):
    pass


def piper_programm():
    for ort in PIPER_ORTE:
        p = os.path.join(ort, "piper", "piper")
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p, ort
    return None, None


def piper_stimmen() -> list[dict]:
    programm, ort = piper_programm()
    if not programm:
        return []
    stufe = {"high": 0, "medium": 1, "low": 2, "x_low": 3}
    out = []
    for d in sorted(os.listdir(ort)):
        if d.endswith(".onnx"):
            k = d[:-5]
            out.append((stufe.get(k.rsplit("-", 1)[-1], 9), k, PIPER_NAMEN.get(k, k.replace("de_DE-", ""))))
    out.sort(key=lambda e: (e[0], e[2]))
    return [{"kennung": k, "name": n} for _r, k, n in out]


def _abspieler():
    if shutil.which("paplay"):
        return ["paplay", "--raw", "--rate=22050", "--format=s16le", "--channels=1"]
    if shutil.which("aplay"):
        return ["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-c", "1", "-t", "raw", "-"]
    return None


def piper_da() -> bool:
    return bool(piper_programm()[0] and piper_stimmen() and _abspieler())


def spd_da() -> bool:
    return shutil.which("spd-say") is not None


def verfuegbar() -> bool:
    return piper_da() or spd_da()


def tempo_piper(tempo: int) -> float:
    t = max(-100, min(100, int(tempo or 0)))
    return 1.0 - t * (0.4 / 100) if t > 0 else 1.0 - t * (0.5 / 100)


def stimmen() -> list[dict]:
    """Alle wählbaren Stimmen: zuerst Piper, dann die deutschen des Sprachdienstes."""
    liste = [{"kennung": "piper:" + s["kennung"], "name": s["name"]} for s in piper_stimmen()]
    if spd_da():
        try:
            r = subprocess.run(["spd-say", "-L"], capture_output=True, encoding="utf-8", errors="replace", timeout=15)
            for z in r.stdout.splitlines():
                t = z.split()
                if len(t) >= 2 and t[1] == "de":
                    liste.append({"kennung": t[0], "name": t[0] + " (Sprachdienst)"})
        except (OSError, subprocess.SubprocessError):
            pass
    return liste[:60]


def beenden() -> None:
    for k in ("ton", "rechner"):
        p = _lauf.get(k)
        _lauf[k] = None
        if p and p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=2)
            except (OSError, subprocess.SubprocessError):
                pass
    if spd_da():
        try:
            subprocess.run(["spd-say", "-C"], timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass


def lies_vor(text: str, stimme: str = "", tempo: int = 0) -> bool:
    beenden()
    text = text.strip()[:MAX_ZEICHEN]
    if not text:
        return False
    if not verfuegbar():
        raise VorlesenFehler("Auf diesem Rechner ist keine Sprachausgabe eingerichtet. Installieren Sie "
                             "speech-dispatcher (sudo apt install speech-dispatcher) oder holen Sie mit "
                             "./stimme-holen.sh die Stimme Piper.")
    if stimme.startswith("piper:") or (piper_da() and not stimme):
        programm, ort = piper_programm()
        kennung = stimme[6:] if stimme.startswith("piper:") else piper_stimmen()[0]["kennung"]
        modell = os.path.join(ort, kennung + ".onnx")
        if not os.path.isfile(modell):
            modell = os.path.join(ort, piper_stimmen()[0]["kennung"] + ".onnx")
        sprechen = subprocess.Popen([programm, "--model", modell, "--output_raw", "--length_scale",
                                     "%.2f" % tempo_piper(tempo)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
        ton = subprocess.Popen(_abspieler(), stdin=sprechen.stdout, stderr=subprocess.DEVNULL, start_new_session=True)
        sprechen.stdout.close()

        def fuettern():
            try:
                sprechen.stdin.write(text.encode("utf-8"))
                sprechen.stdin.close()
            except (OSError, ValueError):
                pass
        threading.Thread(target=fuettern, daemon=True).start()
        _lauf["ton"], _lauf["rechner"] = ton, sprechen
        return True
    befehl = ["spd-say", "-l", "de", "-w"] + (["-y", stimme] if stimme else []) + \
             ["-r", str(max(-100, min(100, int(tempo or 0)))), text]
    _lauf["ton"] = subprocess.Popen(befehl, start_new_session=True)
    return True
