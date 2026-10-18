"""LanguageTool als zweite Meinung (eigener Java-Prozess, nur auf diesem Rechner, 127.0.0.1).

LanguageTool steht unter LGPL-2.1; als getrennter Prozess bleibt die Lizenz dieses Programms unberührt.
Gesucht wird ein bereits laufender Server auf Port 8081 oder languagetool-server.jar unter
~/.local/share/<App>/languagetool. Beides ist optional: Ohne läuft die übrige Schreibhilfe unverändert.
Es wird nichts heruntergeladen und nichts an externe Dienste gesendet.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.parse
import urllib.request

from ..storage.settings import data_dir

PORT = 8081
_lauf = {"proc": None}


class LanguageToolFehler(Exception):
    pass


def ordner() -> str:
    return os.path.join(data_dir(), "languagetool")


def laeuft(port: int = PORT) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def jar_finden() -> str | None:
    for wurzel, _d, dateien in os.walk(ordner()):
        if "languagetool-server.jar" in dateien:
            return os.path.join(wurzel, "languagetool-server.jar")
    return None


def verfuegbar(port: int = PORT) -> bool:
    return laeuft(port) or (jar_finden() is not None and shutil.which("java") is not None)


def starten(port: int = PORT, warte_s: int = 30) -> None:
    if laeuft(port):
        return
    jar = jar_finden()
    if not jar:
        raise LanguageToolFehler("LanguageTool ist nicht eingerichtet. Es gehört nach " + ordner() + ".")
    if not shutil.which("java"):
        raise LanguageToolFehler("Für LanguageTool wird Java gebraucht; es ist nicht installiert.")
    _lauf["proc"] = subprocess.Popen(
        ["java", "-cp", jar, "org.languagetool.server.HTTPServer", "--port", str(port)],
        cwd=os.path.dirname(jar), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(warte_s * 2):
        if laeuft(port):
            return
        time.sleep(0.5)
    raise LanguageToolFehler("LanguageTool ist nicht hochgekommen.")


def pruefe(text: str, sprache: str = "de-DE", port: int = PORT) -> list[dict]:
    """→ Funde im selben Format wie die eigene Prüfung (von, bis, alt, neu, grund, art)."""
    starten(port)
    daten = urllib.parse.urlencode({"language": sprache, "text": text[:60000],
                                    "disabledCategories": "TYPOS"}).encode("utf-8")
    try:
        antwort = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/v2/check", data=daten),
                                         timeout=90)
        roh = json.loads(antwort.read().decode("utf-8"))
    except (OSError, ValueError) as e:
        raise LanguageToolFehler(f"LanguageTool antwortet nicht: {e}") from e
    funde = []
    for m in roh.get("matches", []):
        von = m.get("offset", 0)
        bis = von + m.get("length", 0)
        ers = m.get("replacements") or []
        neu = ers[0].get("value", "") if ers else ""
        funde.append({"von": von, "bis": bis, "alt": text[von:bis], "neu": neu,
                      "grund": (m.get("message") or "") + " (LanguageTool)",
                      "art": "tipp" if neu else "hinweis", "wortEbene": False})
    return funde[:200]


def beenden() -> None:
    p = _lauf.get("proc")
    if p and p.poll() is None:
        p.terminate()
