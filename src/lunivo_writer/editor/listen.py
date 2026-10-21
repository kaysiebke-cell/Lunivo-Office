"""Aufzählungen und Nummerierungen: die Arten, die Lunivo zeichnet und in DOCX schreibt, und ihre Beschreibung als kleines Wörterbuch.

Eine Liste ist ``{"stil": Schlüssel aus STILE, "praefix": "", "suffix": ".", "start": 1}`` (Aufzählungen: nur ``stil``).
Eine Nummerierung kann ``"zeichen"`` tragen (Schrift, Fett, Kursiv, Größe, Farbe der Nummern, Werte wie in ``text_format.ZEICHEN``).
Als Text (für eine Formatvorlage) steht sie als ``stil|praefix|suffix|start|zeichen als JSON``; ein leerer Text heißt: keine Liste.
"""
from __future__ import annotations

import json

from PySide6.QtGui import QTextListFormat

# Schlüssel → (Name, Aufzählung?, Qt-Stil, Ziffernfolge für Vorschau und Zahlenformat)
STILE = {
    "disc": ("Punkt", True, QTextListFormat.ListDisc, ""),
    "circle": ("Kreis", True, QTextListFormat.ListCircle, ""),
    "square": ("Quadrat", True, QTextListFormat.ListSquare, ""),
    "dezimal": ("1, 2, 3, …", False, QTextListFormat.ListDecimal, "1|2|3"),
    "klein": ("a, b, c, …", False, QTextListFormat.ListLowerAlpha, "a|b|c"),
    "gross": ("A, B, C, …", False, QTextListFormat.ListUpperAlpha, "A|B|C"),
    "roem_klein": ("i, ii, iii, …", False, QTextListFormat.ListLowerRoman, "i|ii|iii"),
    "roem_gross": ("I, II, III, …", False, QTextListFormat.ListUpperRoman, "I|II|III"),
}
AUFZAEHLUNGEN = tuple(k for k, v in STILE.items() if v[1])
# Nummerierungen der Auswahl (Reiter „Nummerierung“): (Stil, Präfix, Suffix)
NUMMERIERUNGEN = (("dezimal", "", "."), ("dezimal", "", ")"), ("roem_gross", "", "."), ("gross", "", "."),
                  ("klein", "", ")"), ("klein", "", ""), ("roem_klein", "", "."))


ZEICHEN_FELDER = ("schrift", "fett", "kursiv", "groesse", "farbe")


def zeichen_filtern(w: dict | None) -> dict:
    """Aus den Werten eines Schriftart-Fensters nur das, was für Nummern gilt und gesetzt ist."""
    return {k: w[k] for k in ZEICHEN_FELDER if w and w.get(k)}


def liste(stil: str, praefix: str = "", suffix: str = ".", start: int = 1, zeichen: dict | None = None, pos: dict | None = None) -> dict:
    """``pos``: eigene Position der Nummer (``ausr``, ``ausr_art``, ``tab``, ``einzug`` in mm) — dann zeichnet Lunivo die Nummer selbst."""
    if STILE[stil][1]:
        return {"stil": stil, "praefix": "", "suffix": "", "start": 1}
    d = {"stil": stil, "praefix": praefix, "suffix": suffix, "start": max(1, int(start))}
    z = zeichen_filtern(zeichen)
    if z:
        d["zeichen"] = z
    if pos:
        d["pos"] = {k: pos[k] for k in ("ausr", "ausr_art", "tab", "einzug", "danach") if k in pos}
    return d


def marke(spec: dict) -> str | None:
    """Zeichenfolge für ``liste_zeichner`` (Vorschaubild) dieser Liste."""
    st = STILE[spec["stil"]]
    if st[1]:
        return spec["stil"]
    return "|".join(spec["praefix"] + z + spec["suffix"] for z in st[3].split("|"))


def zu_format(spec: dict, einzug: int = 1) -> QTextListFormat:
    f = QTextListFormat()
    f.setStyle(STILE[spec["stil"]][2]); f.setIndent(einzug)
    if not STILE[spec["stil"]][1]:
        f.setNumberPrefix(spec["praefix"]); f.setNumberSuffix(spec["suffix"])
        if spec["start"] != 1:
            f.setStart(spec["start"])
    return f


def aus_format(f: QTextListFormat) -> dict | None:
    stil = next((k for k, v in STILE.items() if v[2] == f.style()), None)
    if stil is None:
        return None
    return liste(stil, f.numberPrefix(), f.numberSuffix(), f.start() or 1)


def als_text(spec: dict | None) -> str:
    if not spec:
        return ""
    if "ebenen" in spec:
        from lunivo_writer.editor.mehrstufig import als_text as g
        return g(spec)
    t = "|".join((spec["stil"], spec["praefix"].replace("|", ""), spec["suffix"].replace("|", ""), str(spec["start"])))
    extra = {k: spec[k] for k in ("zeichen", "pos") if spec.get(k)}
    return t + "|" + json.dumps(extra, ensure_ascii=False) if extra else t


def aus_text(text: str | None) -> dict | None:
    if (text or "").startswith("g:"):
        from lunivo_writer.editor.mehrstufig import aus_text as g
        return g(text)
    t = (text or "").split("|", 4)
    if len(t) not in (4, 5) or t[0] not in STILE:
        return None
    try:
        extra = json.loads(t[4]) if len(t) == 5 else {}
        return liste(t[0], t[1], t[2], int(t[3]), extra.get("zeichen"), extra.get("pos"))
    except ValueError:
        return None
