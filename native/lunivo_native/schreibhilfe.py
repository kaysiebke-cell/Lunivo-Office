"""Die Schreibhilfe: die vorhandene Prüflogik (js/pruefung.js) über Node,
ohne Fenster. KI-Funktionen über Ollama auf diesem Rechner."""
import json
import os
import shutil
import subprocess
import urllib.request

from . import pfade


class PrueferFehler(RuntimeError):
    pass


_SH_ORDNER = os.environ.get("SCHREIBHILFE_ORDNER", "/home/kaysiebke/GidHub/schreibhilfe/linux")
_modul = None


def _eigene_pruefung():
    """Die eigene Prüfung des Menschen (schreibhilfe/linux/services/pruefung.py), unverändert geladen."""
    global _modul
    if _modul is not None:
        return _modul or None
    pfad = os.path.join(_SH_ORDNER, "services", "pruefung.py")
    if os.path.exists(pfad):
        import importlib.util
        spez = importlib.util.spec_from_file_location("schreibhilfe_pruefung", pfad)
        m = importlib.util.module_from_spec(spez)
        spez.loader.exec_module(m)
        _modul = m
        return m
    _modul = False
    return None


def gelernt():
    """Gelernte Wörter und „in Ruhe lassen“ aus den Einstellungen der Schreibhilfe (nur gelesen)."""
    try:
        with open(os.path.join(_SH_ORDNER, "benutzer", "einstellungen.json"), encoding="utf-8") as f:
            g = json.load(f).get("gelernt", {})
        return {"woerter": g.get("woerter", {}), "inRuhe": g.get("inRuhe", {})}
    except (OSError, ValueError):
        return {"woerter": {}, "inRuhe": {}}


OPT = {}          # wird vom Fenster gesetzt: werte["opt"]


def _opt(seite, name, standard=True):
    return OPT.get("%s|%s" % (seite, name), standard)


def _gefiltert(funde, text):
    """Die Optionen der Seite „Rechtschreibprüfung“ auf die Funde anwenden."""
    import re
    aus = []
    for f in funde:
        wort = f.get("alt", "")
        if not f.get("wortEbene") and not _opt("pruefung", "Grammatik mitprüfen"):
            continue
        if f.get("wortEbene"):
            if _opt("pruefung", "Wörter in GROSSBUCHSTABEN ignorieren") and len(wort) > 1 and wort.isupper():
                continue
            if _opt("pruefung", "Wörter mit Zahlen ignorieren") and re.search(r"\d", wort):
                continue
            if _opt("pruefung", "Internet- und Netzwerkpfade ignorieren") and re.search(r"[/\\@]|www\.|https?:", text[max(f["von"] - 8, 0):f["bis"] + 8]):
                continue
            if not _opt("pruefung", "Immer Korrekturvorschläge unterbreiten"):
                f = dict(f, neu=None)
        aus.append(f)
    return aus


def pruefen(text):
    """Alle Funde der Schreibhilfe (Regeln, Wörterliste, Tippfehler) — Positionen als Zeichen-Offsets.

    Läuft mit der eigenen Prüfung aus schreibhilfe/linux; fehlt sie, mit der Prüflogik von Lunivo (Node)."""
    m = _eigene_pruefung()
    if m is not None:
        return _gefiltert(m.finde_probleme(text, gelernt()), text)
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        raise PrueferFehler("Weder die Schreibhilfe (%s) noch Node.js gefunden." % _SH_ORDNER)
    lauf = subprocess.run([node, pfade.PRUEFER], input=text.encode("utf-8"), capture_output=True, timeout=60)
    if lauf.returncode != 0:
        raise PrueferFehler(lauf.stderr.decode("utf-8", "replace")[:300])
    return json.loads(lauf.stdout.decode("utf-8") or "[]")


def woerter_fehler(text):
    """Wortfehler fürs Unterstreichen beim Schreiben: [(von, bis, wort, [Vorschläge])]."""
    return [(f["von"], f["bis"], f["alt"], [f["neu"]] if f.get("neu") else [])
            for f in pruefen(text) if f.get("wortEbene")]


# ------------------------------------------------------------------ Ollama

def ki_modelle(adresse):
    with urllib.request.urlopen(adresse.rstrip("/") + "/api/tags", timeout=5) as r:
        return [m["name"] for m in json.load(r).get("models", [])]


def ki_fragen(adresse, modell, anweisung, text):
    ladung = json.dumps({
        "model": modell, "stream": False,
        "messages": [
            {"role": "system", "content": anweisung},
            {"role": "user", "content": text},
        ],
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    anfrage = urllib.request.Request(adresse.rstrip("/") + "/api/chat", data=ladung,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=600) as r:
        antwort = json.load(r)["message"]["content"]
    # Denk-Blöcke mancher Modelle entfernen
    while "<think>" in antwort and "</think>" in antwort:
        a, b = antwort.index("<think>"), antwort.index("</think>") + 8
        antwort = antwort[:a] + antwort[b:]
    return antwort.strip()


ANWEISUNGEN = {
    "korrektur": "Du korrigierst deutschen Text. Behebe nur Rechtschreib-, Grammatik- und Zeichensetzungsfehler. Ändere weder Inhalt noch Stil. Gib ausschließlich den korrigierten Text zurück, ohne Erklärung.",
    "kurz": "Fasse den deutschen Text in wenigen klaren Sätzen zusammen. Gib nur die Zusammenfassung zurück.",
    "englisch": "Übersetze den Text ins Englische. Gib nur die Übersetzung zurück.",
}


# ------------------------------------------------------------------ Anbieter (Ollama und OpenAI-kompatibel)
def anbieter_liste(werte):
    liste = werte.setdefault("anbieter", [])
    if not liste:
        liste.append({"name": "Ollama (auf diesem Rechner)", "typ": "ollama",
                      "url": werte.get("ki_adresse", "http://localhost:11434"),
                      "modell": werte.get("ki_modell", ""), "schluessel": ""})
    return liste


def anbieter_aktiv(werte):
    liste = anbieter_liste(werte)
    i = min(max(int(werte.get("anbieter_aktiv", 0)), 0), len(liste) - 1)
    return liste[i]


def modelle_von(anbieter):
    url = anbieter["url"].rstrip("/")
    if anbieter.get("typ", "ollama") == "ollama":
        with urllib.request.urlopen(url + "/api/tags", timeout=5) as r:
            return [m["name"] for m in json.load(r).get("models", [])]
    anfrage = urllib.request.Request(url + "/models", headers=_kopf(anbieter))
    with urllib.request.urlopen(anfrage, timeout=8) as r:
        return [m["id"] for m in json.load(r).get("data", [])]


def _kopf(anbieter):
    k = {"Content-Type": "application/json"}
    if anbieter.get("schluessel"):
        k["Authorization"] = "Bearer " + anbieter["schluessel"]
    return k


def chat(anbieter, nachrichten, temperatur=0.2):
    """nachrichten: [{"role": "system"|"user"|"assistant", "content": "…"}] → Antworttext."""
    url = anbieter["url"].rstrip("/")
    if anbieter.get("typ", "ollama") == "ollama":
        ladung = {"model": anbieter["modell"], "stream": False, "messages": nachrichten,
                  "options": {"temperature": temperatur}}
        ziel = url + "/api/chat"
    else:
        ladung = {"model": anbieter["modell"], "messages": nachrichten, "temperature": temperatur}
        ziel = url + "/chat/completions"
    anfrage = urllib.request.Request(ziel, data=json.dumps(ladung).encode("utf-8"), headers=_kopf(anbieter))
    with urllib.request.urlopen(anfrage, timeout=600) as r:
        antwort = json.load(r)
    text = antwort["message"]["content"] if "message" in antwort else antwort["choices"][0]["message"]["content"]
    while "<think>" in text and "</think>" in text:
        a, b = text.index("<think>"), text.index("</think>") + 8
        text = text[:a] + text[b:]
    return text.strip()
