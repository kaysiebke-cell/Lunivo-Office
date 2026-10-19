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
NAMEN = list(VORGABE)                  # nur die eingebauten; mit den selbst angelegten: namen()
_EIGEN: dict[str, dict] = {}            # Änderungen an eingebauten Vorlagen
_NEU: dict[str, dict] = {}              # selbst angelegte Vorlagen (Name → Definition)
VORLAGE = {"ebene": 0, "groesse": 0, "fett": False, "kursiv": False, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": ""}
PRAEFIX = "x:"                          # Kennung am Absatz: "x:Name" = selbst angelegte Vorlage


def namen() -> list[str]:
    return NAMEN + list(_NEU)


def ist_eigen(name: str) -> bool:
    return name in _NEU


def laden_neu(text: str) -> None:
    global _NEU
    try:
        d = json.loads(text or "{}")
        _NEU = {k: {**VORLAGE, **{f: v for f, v in x.items() if f in VORLAGE}} for k, x in d.items()
                if isinstance(x, dict) and k and k not in VORGABE}
    except ValueError:
        _NEU = {}


def als_json_neu() -> str:
    return json.dumps(_NEU, ensure_ascii=False)


def anlegen(name: str, **felder) -> str | None:
    """Neue Vorlage anlegen. → None bei Erfolg, sonst der Grund (Name leer oder schon vergeben)."""
    name = " ".join(name.split())
    if not name:
        return "Bitte einen Namen eingeben."
    if name in VORGABE or name in _NEU or name == "Fließtext":
        return f"Eine Formatvorlage „{name}“ gibt es schon."
    if PRAEFIX in name[:2] or "|" in name:
        return "Der Name darf nicht mit „x:“ beginnen und kein „|“ enthalten."
    _NEU[name] = {**VORLAGE, **{f: v for f, v in felder.items() if f in VORLAGE}, "ebene": 0}
    return None


def loeschen(name: str) -> bool:
    return _NEU.pop(name, None) is not None


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
    if name in _NEU:
        return {**_NEU[name], "key": PRAEFIX + name}
    return {**VORGABE.get(name, VORGABE["Standard"]), **_EIGEN.get(name, {})}


def aendern(name: str, **felder) -> None:
    if name in _NEU:
        _NEU[name].update({f: v for f, v in felder.items() if f in VORLAGE and f != "ebene"})
        return
    _EIGEN.setdefault(name, {}).update(felder)


def zuruecksetzen(name: str | None = None) -> None:
    if name is None:
        _EIGEN.clear()
    else:
        _EIGEN.pop(name, None)


def name_zu_key(name: str) -> str | None:
    return VORGABE.get(name, {}).get("key")


def key_zu_name(key: str) -> str | None:
    if key and key.startswith(PRAEFIX):
        n = key[len(PRAEFIX):]
        return n if n in _NEU else None
    return next((n for n, d in VORGABE.items() if d.get("key") == key), None)
