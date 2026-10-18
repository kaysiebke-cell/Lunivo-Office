"""Wortvorhersage und Themenwörter (aus pruefung.js: faengtAnMit, themaSetzen; daten/themenwoerter.js)."""
from __future__ import annotations

import bisect
import os
import re

from .haeufig import HAEUFIG
from .pruefung import daten_ordner, lade_woerter

EMPFAENGER = ["egal", "Amt", "Arbeit", "Freunde", "Forum", "Bewerbung"]
_THEMEN: dict[str, frozenset] | None = None
_SORTIERT: list[str] | None = None
_EXTRA: set[str] = set()


def _ohne_js_kommentare(text: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def themenwoerter() -> dict[str, frozenset]:
    """Liest daten/themenwoerter.js: je Empfänger eine Kette aus Zeichenketten."""
    global _THEMEN
    if _THEMEN is not None:
        return _THEMEN
    _THEMEN = {}
    for ordner in daten_ordner():
        pfad = os.path.join(ordner, "themenwoerter.js")
        if not os.path.exists(pfad):
            continue
        text = _ohne_js_kommentare(open(pfad, encoding="utf-8").read())
        text = re.sub(r"(?m)//.*$", "", text)
        kopf = list(re.finditer(r"(?m)^\s*'([A-Za-zÄÖÜäöüß]+)'\s*:\s*\(", text))
        for k, m in enumerate(kopf):
            ende = kopf[k + 1].start() if k + 1 < len(kopf) else len(text)
            teil = text[m.end():ende]
            teil = teil[:teil.rfind(")")] if ")" in teil else teil
            ws = " ".join(re.findall(r"'([^']*)'", teil)).split()
            _THEMEN[m.group(1)] = frozenset(w.lower() for w in ws)
        break
    return _THEMEN


def thema_woerter(name: str) -> frozenset:
    return themenwoerter().get(name, frozenset())


def thema_aufnehmen(woerter) -> None:
    """Themenwörter sind richtig geschrieben und bekommen keine Wellenlinie."""
    lade_woerter().update(woerter)
    _EXTRA.update(woerter)
    global _SORTIERT
    _SORTIERT = None


def _liste() -> list[str]:
    global _SORTIERT
    if _SORTIERT is None:
        _SORTIERT = sorted(set(lade_woerter()) | _EXTRA)
    return _SORTIERT


def faengt_an_mit(anfang: str, hoechstens: int = 8, gelernt: dict | None = None,
                  thema: frozenset = frozenset()) -> list[str]:
    a = str(anfang).lower()
    if len(a) < 3 or len(a) > 20:
        return []
    liste = _liste()
    i = bisect.bisect_left(liste, a)
    treffer = []
    while i < len(liste) and liste[i].startswith(a):
        if len(liste[i]) > len(a):
            treffer.append(liste[i])
        i += 1
    if not treffer:
        return []
    schon = set((gelernt or {}).get("woerter", {}).values())
    treffer.sort(key=lambda w: (w not in schon, w not in thema, w not in HAEUFIG, len(w), w))
    return treffer[:hoechstens]
