"""Herkunft und Sicherheit eines Fundes; Auflösung, wenn mehrere Quellen dieselbe Stelle melden.

Jeder Fund trägt `quelle` ("eigen" | "languagetool" | "ki") und `konfidenz` (0…1). Eigene Regeln und LanguageTool liefern keine
echte Wahrscheinlichkeit; ihre Werte sind feste Schätzungen je Fundart (unten), nur bei der KI kommt die Zahl vom Modell.
Bei Überschneidung gewinnt: höchste Konfidenz, dann Art (Fehler vor Tipp vor Hinweis), dann Quelle (eigen vor LanguageTool vor KI)."""
from __future__ import annotations

ART_RANG = {"fehler": 0, "tipp": 1, "hinweis": 2}
QUELLE_RANG = {"eigen": 0, "languagetool": 1, "ki": 2}
STANDARD = {("eigen", True): 0.9, ("eigen", False): 0.8, ("languagetool", True): 0.7, ("languagetool", False): 0.5,
            ("ki", True): 0.5, ("ki", False): 0.5}


def klemmen(wert, vorgabe: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(wert)))
    except (TypeError, ValueError):
        return vorgabe


def markieren(funde: list[dict], quelle: str) -> list[dict]:
    """Quelle und – falls nicht vorhanden – Standard-Konfidenz eintragen (liefert Kopien)."""
    out = []
    for f in funde:
        wort_oder_vorschlag = bool(f.get("wortEbene")) or f.get("art") == "fehler"
        out.append(dict(f, quelle=f.get("quelle", quelle),
                        konfidenz=klemmen(f["konfidenz"]) if "konfidenz" in f
                        else STANDARD.get((quelle, wort_oder_vorschlag), 0.5)))
    return out


def _rang(f: dict):
    return (-f.get("konfidenz", 0.5), ART_RANG.get(f.get("art"), 3), QUELLE_RANG.get(f.get("quelle", "eigen"), 3),
            f["von"], -(f["bis"] - f["von"]))


def loesen(funde: list[dict]) -> list[dict]:
    """Überschneidende Funde auflösen: der beste bleibt, die unterlegenen werden nicht angezeigt, aber als `verdraengt` vermerkt."""
    belegt: list[dict] = []
    for f in sorted(funde, key=_rang):
        gegner = [b for b in belegt if f["von"] < b["bis"] and b["von"] < f["bis"]]
        if gegner:
            gegner[0].setdefault("verdraengt", []).append(
                {"quelle": f.get("quelle"), "neu": f.get("neu"), "grund": f.get("grund"), "konfidenz": f.get("konfidenz")})
        else:
            belegt.append(f)
    return sorted(belegt, key=lambda f: (f["von"], -(f["bis"] - f["von"])))
