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
# zeilen: Zeilenabstand als Vielfaches (0 = nichts setzen), einzug: linker Einzug in mm (0 = nichts setzen)
# rahmen: ``Linie.text()`` des Absatzrahmens, fuell/muster/musterfarbe: Schattierung, liste: ``listen.als_text``, tabs: ``tabstopp_dialog.als_text``, effekt: ``texteffekt.als_text`` (Kontur, Transparenz der Farbe), taste: Tastenkombination ("" = nichts setzen; die Taste erbt eine Vorlage nicht von ihrer Basis)
VORLAGE = {"ebene": 0, "groesse": 0, "fett": False, "kursiv": False, "farbe": "", "schrift": "", "vor": 0, "nach": 0, "ausr": "",
           "zeilen": 0, "einzug": 0, "rahmen": "", "fuell": "", "muster": "", "musterfarbe": "", "liste": "", "taste": "", "effekt": "", "tabs": "",
           # die übrigen Felder des Fensters „Schriftart“
           "unter": "", "unterfarbe": "", "durch": False, "doppelt": False, "hoch": False, "tief": False, "kapital": False, "gross": False,
           "versteckt": False, "abstand": 0.0, "kerning": True, "betonung": "", "schrift_asien": "", "schnitt_asien": "", "groesse_asien": 0.0,
           "schrift_komplex": "", "schnitt_komplex": "", "groesse_komplex": 0.0, "skala": 100.0, "position": 0.0, "kern_ab": 0.0, "raster": True,
           # die übrigen Felder des Fensters „Absatz“
           "rechts": 0, "erste": 0, "rtl": False, "umbruch": False, "zeilen_art": "faktor", "zeilen_pt": 12.0, "gliederung": 0, "opt": ""}
FELDER = tuple(VORLAGE)                 # die Felder, die eine Vorlage festlegen kann
MAX_BASIS = 6                           # so tief darf „basiert auf“ verschachtelt sein
PRAEFIX = "x:"                          # Kennung am Absatz: "x:Name" = selbst angelegte Vorlage


def namen() -> list[str]:
    return NAMEN + list(_NEU)


def ist_eigen(name: str) -> bool:
    return name in _NEU


def laden_neu(text: str) -> None:
    global _NEU
    try:
        d = json.loads(text or "{}")
        _NEU = {k: {**VORLAGE, **{f: v for f, v in x.items() if f in VORLAGE}, **_meta(x)} for k, x in d.items()
                if isinstance(x, dict) and k and k not in VORGABE}
    except ValueError:
        _NEU = {}


def _meta(x: dict) -> dict:
    """„basiert auf“, „folgender Absatz“ und die Abweichungen von der Basis (nur bei Vorlagen mit Basis)."""
    m = {}
    if isinstance(x.get("basis"), str) and x["basis"]:
        m["basis"] = x["basis"]
        m["abw"] = {f: v for f, v in (x.get("abw") or {}).items() if f in VORLAGE and f != "ebene"}
    if isinstance(x.get("folge"), str) and x["folge"]:
        m["folge"] = x["folge"]
    return m


def als_json_neu() -> str:
    return json.dumps(_NEU, ensure_ascii=False)


def pruefe_name(name: str) -> str | None:
    """Darf eine neue Vorlage so heißen? → None, sonst der Grund."""
    name = " ".join(name.split())
    if not name:
        return "Bitte einen Namen eingeben."
    if name in VORGABE or name in _NEU or name == "Fließtext":
        return f"Eine Formatvorlage „{name}“ gibt es schon."
    if PRAEFIX in name[:2] or "|" in name:
        return "Der Name darf nicht mit „x:“ beginnen und kein „|“ enthalten."
    return None


def anlegen(name: str, *, basis: str = "", folge: str = "", **felder) -> str | None:
    """Neue Vorlage anlegen. → None bei Erfolg, sonst der Grund (Name leer oder schon vergeben).
    ``basis``: Vorlage, auf der sie aufbaut — was die neue nicht selbst ändert, folgt der Basis. ``folge``: Vorlage des nächsten Absatzes."""
    name = " ".join(name.split())
    grund = pruefe_name(name)
    if grund:
        return grund
    werte = {f: v for f, v in felder.items() if f in VORLAGE and f != "ebene"}
    if basis and (basis in _NEU or basis in VORGABE) and basis != name:
        b = definition(basis)                                    # nur das, was von der Basis abweicht, gehört der Vorlage selbst
        eintrag = {**VORLAGE, "ebene": 0, "basis": basis, "abw": {f: v for f, v in werte.items() if b.get(f) != v}}
    else:
        eintrag = {**VORLAGE, **werte, "ebene": 0}
    if folge and folge != name and (folge in _NEU or folge in VORGABE):
        eintrag["folge"] = folge
    _NEU[name] = eintrag
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


def definition(name: str, _tiefe: int = 0) -> dict:
    if name in _NEU:
        e = _NEU[name]
        if e.get("basis") and _tiefe < MAX_BASIS and (e["basis"] in _NEU or e["basis"] in VORGABE):
            d = {**definition(e["basis"], _tiefe + 1), **e.get("abw", {}), "ebene": 0}
            d.pop("folge", None)
            d["taste"] = e.get("abw", {}).get("taste", "")
        else:
            d = {k: e[k] for k in VORLAGE}
        d["key"] = PRAEFIX + name
        if e.get("folge"):
            d["folge"] = e["folge"]
        return d
    return {**VORLAGE, **VORGABE.get(name, VORGABE["Standard"]), **_EIGEN.get(name, {})}


def aendern(name: str, **felder) -> None:
    if name in _NEU:
        neu = {f: v for f, v in felder.items() if f in VORLAGE and f != "ebene"}
        if _NEU[name].get("basis"):
            _NEU[name].setdefault("abw", {}).update(neu)
        else:
            _NEU[name].update(neu)
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
