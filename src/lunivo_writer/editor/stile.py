"""Formatvorlagen des Katalogs (Start ▸ Stile) — Vorgaben und eigene Änderungen (Start ▸ Stile ▸ ↘ Formatvorlagen verwalten)."""
from __future__ import annotations

import json

# Name → Vorgabe. ebene: Überschriftsebene (0 = Fließtext); key: Name der Word-Vorlage, falls es eine gibt
VORGABE = {
    "Standard":      {"ebene": 0, "groesse": 0, "fett": False, "kursiv": False, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": ""},
    "Überschrift 1": {"ebene": 1, "groesse": 20, "fett": True, "kursiv": False, "farbe": "", "schrift": "", "vor": 9, "nach": 4.5, "ausr": ""},
    "Überschrift 2": {"ebene": 2, "groesse": 16, "fett": True, "kursiv": False, "farbe": "", "schrift": "", "vor": 6, "nach": 4.5, "ausr": ""},
    "Überschrift 3": {"ebene": 3, "groesse": 14, "fett": True, "kursiv": False, "farbe": "", "schrift": "", "vor": 6, "nach": 4.5, "ausr": ""},
    "Überschrift 4": {"ebene": 4, "groesse": 13, "fett": True, "kursiv": False, "farbe": "", "schrift": "", "vor": 4, "nach": 3, "ausr": ""},
    "Überschrift 5": {"ebene": 5, "groesse": 12, "fett": True, "kursiv": False, "farbe": "", "schrift": "", "vor": 4, "nach": 3, "ausr": ""},
    "Überschrift 6": {"ebene": 6, "groesse": 12, "fett": False, "kursiv": True, "farbe": "", "schrift": "", "vor": 4, "nach": 3, "ausr": ""},
    "Überschrift 7": {"ebene": 7, "groesse": 11, "fett": True, "kursiv": False, "farbe": "", "schrift": "", "vor": 4, "nach": 3, "ausr": ""},
    "Überschrift 8": {"ebene": 8, "groesse": 11, "fett": False, "kursiv": True, "farbe": "", "schrift": "", "vor": 4, "nach": 3, "ausr": ""},
    "Überschrift 9": {"ebene": 9, "groesse": 11, "fett": False, "kursiv": False, "farbe": "", "schrift": "", "vor": 4, "nach": 3, "ausr": ""},
    "Titel":         {"ebene": 0, "groesse": 26, "fett": False, "kursiv": False, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": "", "key": "Title"},
    "Untertitel":    {"ebene": 0, "groesse": 15, "fett": False, "kursiv": True, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": "", "key": "Subtitle"},
    "Zitat":         {"ebene": 0, "groesse": 0, "fett": False, "kursiv": True, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": "", "key": "Quote"},
    "Kein Abstand":  {"ebene": 0, "groesse": 0, "fett": False, "kursiv": False, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": "", "key": "No Spacing"},
}
NAMEN = list(VORGABE)
_EIGEN: dict[str, dict] = {}


def laden(text: str) -> None:
    global _EIGEN
    try:
        d = json.loads(text or "{}")
        _EIGEN = {k: v for k, v in d.items() if k in VORGABE and isinstance(v, dict)}
    except ValueError:
        _EIGEN = {}


def als_json() -> str:
    return json.dumps(_EIGEN, ensure_ascii=False)


def definition(name: str) -> dict:
    return {**VORGABE.get(name, VORGABE["Standard"]), **_EIGEN.get(name, {})}


def aendern(name: str, **felder) -> None:
    _EIGEN.setdefault(name, {}).update(felder)


def zuruecksetzen(name: str | None = None) -> None:
    if name is None:
        _EIGEN.clear()
    else:
        _EIGEN.pop(name, None)


def name_zu_key(name: str) -> str | None:
    return VORGABE.get(name, {}).get("key")


def key_zu_name(key: str) -> str | None:
    return next((n for n, d in VORGABE.items() if d.get("key") == key), None)
