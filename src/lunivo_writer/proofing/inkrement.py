"""Inkrementelle Prüfung: nur die geänderte Stelle (plus Sicherheitsbereich) neu prüfen, den Rest verschieben und behalten.

Alles hier sind reine Funktionen auf Zeichenpositionen — die Anbindung an den Editor steht in proofing_service.py.

Grenzen (bewusst): Ein Fund, der über eine Absatzgrenze hinweg reicht, wird beim Neuprüfen eines Teilbereichs nicht neu erkannt;
„Gründlich prüfen“ und F7 prüfen immer den ganzen Text. Bei kurzen Texten und großen Änderungen wird ebenfalls alles geprüft."""
from __future__ import annotations

MIN_ZEICHEN = 2000          # darunter kostet die Gesamtprüfung nichts — dort lohnt der Aufwand nicht
SICHERHEIT_ABSAETZE = 1     # so viele Absätze vor und hinter der Änderung werden mitgeprüft
MAX_ANTEIL = 0.5            # größer als die Hälfte des Textes → gleich alles prüfen


def verschieben(funde: list[dict], pos: int, entfernt: int, hinzu: int) -> list[dict]:
    """Funde nach einer Änderung (pos, entfernt, hinzugefügt) umrechnen. Betroffene Funde entfallen."""
    delta, ende = hinzu - entfernt, pos + entfernt
    out = []
    for f in funde:
        if f["bis"] <= pos:
            out.append(f)
        elif f["von"] >= ende:
            out.append(dict(f, von=f["von"] + delta, bis=f["bis"] + delta))
    return out


def schmutz_abbilden(bereich: tuple[int, int] | None, pos: int, entfernt: int, hinzu: int) -> tuple[int, int]:
    """Den bisher ungeprüften Bereich in die neuen Positionen umrechnen und um die neue Änderung erweitern."""
    delta, ende = hinzu - entfernt, pos + entfernt
    neu = (pos, pos + hinzu)
    if bereich is None:
        return neu
    a, b = bereich
    a2 = a if a <= pos else (a + delta if a >= ende else pos)
    b2 = b if b <= pos else (b + delta if b >= ende else pos + hinzu)
    return min(a2, neu[0]), max(b2, neu[1])


def pruefbereich(text: str, a: int, b: int, absaetze: int = SICHERHEIT_ABSAETZE) -> tuple[int, int]:
    """Den geänderten Bereich auf ganze Absätze samt Sicherheitsbereich erweitern."""
    a = max(0, min(a, len(text))); b = max(a, min(b, len(text)))
    von = text.rfind("\n", 0, a) + 1
    for _ in range(absaetze):
        if von > 0:
            von = text.rfind("\n", 0, von - 1) + 1
    bis = text.find("\n", b)
    bis = len(text) if bis < 0 else bis
    for _ in range(absaetze):
        if bis < len(text):
            n = text.find("\n", bis + 1)
            bis = len(text) if n < 0 else n
    return von, bis


def lohnt(laenge: int, von: int, bis: int) -> bool:
    return laenge >= MIN_ZEICHEN and (bis - von) < laenge * MAX_ANTEIL


def einsetzen(alt: list[dict], von: int, bis: int, neue_relativ: list[dict]) -> list[dict]:
    """Funde im Bereich [von, bis) durch die neuen (Positionen relativ zum Bereich) ersetzen."""
    behalten = [f for f in alt if f["bis"] <= von or f["von"] >= bis]
    neu = [dict(f, von=f["von"] + von, bis=f["bis"] + von) for f in neue_relativ]
    return sorted(behalten + neu, key=lambda f: (f["von"], -(f["bis"] - f["von"])))
