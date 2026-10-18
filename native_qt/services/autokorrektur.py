"""AutoKorrektur beim Tippen (aus programm.js: AUTOKORREKTUR). Greift erst, wenn ein Wort abgeschlossen ist."""
from __future__ import annotations

import re

WOCHENTAGE = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonnabend", "sonntag"]
HOCH = dict(zip("stnrdh", "ˢᵗⁿʳᵈʰ"))

# Schalter-Name → (Vorgabe, Beschriftung)
SCHALTER = {
    "akAnfuehrung": (True, "Gerade Anführungszeichen durch typografische ersetzen"),
    "akGedankenstrich": (True, "Zwei Bindestriche durch einen Gedankenstrich ersetzen"),
    "akAuslassung": (True, "Drei Punkte durch ein Auslassungszeichen ersetzen"),
    "akFeststelltaste": (True, "Unbeabsichtigtes Verwenden der fESTSTELLTASTE korrigieren"),
    "akSatzGross": (True, "Jeden Satz mit einem Großbuchstaben beginnen"),
    "akWochentage": (True, "Wochentage immer großschreiben"),
    "akOrdnungszahlen": (True, "Englische Ordnungszahlen hochstellen"),
}


def _ordnung(m):
    ende = "".join(HOCH.get(c, c) for c in m.group(2))
    return m.group(1) + ende


_REGELN = [
    ("akAnfuehrung", [(r'(^|[\s(\[])"', "\\1„"), (r'"', "“"), (r"(^|[\s(\[])'", "\\1‚"), (r"'", "’")]),
    ("akGedankenstrich", [(r"(\s)--(\s)", "\\1–\\2"), (r"(\d)\s*-\s*(\d)", "\\1–\\2")]),
    ("akAuslassung", [(r"\.\.\.", "…")]),
    ("akFeststelltaste", [(r"\b([a-zäöü])([A-ZÄÖÜ]{2,})\b", lambda m: m.group(1).upper() + m.group(2).lower())]),
    ("akSatzGross", [(r"(^|[.!?]\s)([a-zäöüß])(?=\w)", lambda m: m.group(1) + m.group(2).upper())]),
    ("akWochentage", [(r"\b(" + "|".join(WOCHENTAGE) + r")\b", lambda m: m.group(1)[0].upper() + m.group(1)[1:])]),
    ("akOrdnungszahlen", [(r"\b(\d+)(st|nd|rd|th)\b", _ordnung)]),
]


def korrigiere(text: str, an=lambda name: SCHALTER[name][0]) -> str:
    neu = text
    for name, regeln in _REGELN:
        if an(name):
            for muster, ersatz in regeln:
                neu = re.sub(muster, ersatz, neu)
    return neu


def kleinste_aenderung(alt: str, neu: str) -> tuple[int, int, str]:
    """→ (von, bis, ersatz): nur der Abschnitt, der sich wirklich ändert — Formatierung bleibt sonst unberührt."""
    p = 0
    while p < min(len(alt), len(neu)) and alt[p] == neu[p]:
        p += 1
    s = 0
    while s < min(len(alt), len(neu)) - p and alt[-1 - s] == neu[-1 - s]:
        s += 1
    return p, len(alt) - s, neu[p:len(neu) - s]
