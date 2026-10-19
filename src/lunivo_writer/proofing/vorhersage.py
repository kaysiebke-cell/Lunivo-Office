"""Wortvorhersage und Themenwörter (daten/themenwoerter.json)."""
from __future__ import annotations

import bisect
import json
import os
import re

from lunivo_writer.proofing.haeufig import HAEUFIG
from lunivo_writer.proofing.pruefung import daten_ordner, lade_woerter

EMPFAENGER = ["egal", "Amt", "Arbeit", "Freunde", "Forum", "Bewerbung"]
_THEMEN: dict[str, frozenset] | None = None
_SORTIERT: list[str] | None = None
_EXTRA: set[str] = set()


def themenwoerter() -> dict[str, frozenset]:
    """Liest daten/themenwoerter.json: je Empfänger eine Liste von Wörtern."""
    global _THEMEN
    if _THEMEN is not None:
        return _THEMEN
    _THEMEN = {}
    for ordner in daten_ordner():
        pfad = os.path.join(ordner, "themenwoerter.json")
        if not os.path.exists(pfad):
            continue
        with open(pfad, encoding="utf-8") as fh:
            _THEMEN = {k: frozenset(w.lower() for w in v) for k, v in json.load(fh).items()}
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
