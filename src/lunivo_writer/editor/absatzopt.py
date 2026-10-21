"""Absatzoptionen des Absatz-Fensters (Reiter „Zeilen- und Seitenumbruch“ und die Raster-Haken): Vorgaben, Speichern am Absatz, DOCX.

Am Absatz steht ``B_ABSATZOPT`` als ``"Schlüssel=Wert;…"``, aber nur, was von der Vorgabe abweicht. Die Umbruchregeln (``kontrolle``,
``nicht_trennen``, ``zusammen``) wirkt ``seitenfluss.py`` beim Seitenumbruch; die übrigen Optionen schreibt und liest DOCX
(``w:kinsoku``, ``w:wordWrap`` …) und Lunivo hält sie am Absatz.
"""
from __future__ import annotations

VORGABE = {"kontrolle": True, "nicht_trennen": False, "zusammen": False, "asiat": True, "mitten": False, "haengend": True, "kompr": False,
           "ade": True, "adn": True, "textausr": "auto", "rest_einzug": True, "raster": True}
# Schlüssel → (DOCX-Element, Art): "an" = Element mit w:val (aus = "0"); "keep" = Element nur, wenn an; "text" = w:val mit Text
_DOCX = {"kontrolle": ("w:widowControl", "an"), "nicht_trennen": ("w:keepNext", "keep"), "zusammen": ("w:keepLines", "keep"),
         "asiat": ("w:kinsoku", "an"), "mitten": ("w:wordWrap", "umgekehrt"), "haengend": ("w:overflowPunct", "an"),
         "kompr": ("w:topLinePunct", "keep"), "ade": ("w:autoSpaceDE", "an"), "adn": ("w:autoSpaceDN", "an"),
         "textausr": ("w:textAlignment", "text"), "rest_einzug": ("w:adjustRightInd", "an"), "raster": ("w:snapToGrid", "an")}
_FOLGE = ("w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr", "w:widowControl", "w:numPr", "w:suppressLineNumbers",
          "w:pBdr", "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE",
          "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents",
          "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle",
          "w:rPr", "w:sectPr", "w:pPrChange")


def lesen(bf) -> dict:
    """Alle Absatzoptionen eines Absatzformats (Vorgabe, wo nichts gesetzt ist)."""
    from lunivo_writer.editor.zusatz import B_ABSATZOPT
    w = dict(VORGABE)
    if bf.hasProperty(B_ABSATZOPT):
        for teil in bf.stringProperty(B_ABSATZOPT).split(";"):
            k, _s, v = teil.partition("=")
            if k in VORGABE:
                w[k] = v if isinstance(VORGABE[k], str) else v == "1"
    return w


def setzen(bf, w: dict) -> None:
    from lunivo_writer.editor.zusatz import B_ABSATZOPT
    teile = [f"{k}={v if isinstance(VORGABE[k], str) else int(bool(v))}" for k, v in w.items() if k in VORGABE and v != VORGABE[k]]
    if teile:
        bf.setProperty(B_ABSATZOPT, ";".join(teile))
    else:
        bf.clearProperty(B_ABSATZOPT)


def als_text(w: dict | None) -> str:
    """Die Abweichungen von der Vorgabe als ``Schlüssel=Wert;…`` (für eine Formatvorlage; leer = nur Vorgaben)."""
    return ";".join(f"{k}={v if isinstance(VORGABE[k], str) else int(bool(v))}" for k, v in (w or {}).items() if k in VORGABE and v != VORGABE[k])


def aus_text(text: str | None) -> dict:
    w = dict(VORGABE)
    for teil in (text or "").split(";"):
        k, _s, v = teil.partition("=")
        if k in VORGABE:
            w[k] = v if isinstance(VORGABE[k], str) else v == "1"
    return w


def in_ppr(ppr, w: dict) -> None:
    """Abweichungen von der Vorgabe als Elemente an ``w:pPr`` schreiben (in der Reihenfolge, die das Schema verlangt)."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for k, (tag, art) in _DOCX.items():
        if w.get(k, VORGABE[k]) == VORGABE[k] or ppr.find(qn(tag)) is not None:
            continue
        e = OxmlElement(tag)
        if art == "text":
            e.set(qn("w:val"), w[k])
        elif art == "an":
            e.set(qn("w:val"), "1" if w[k] else "0")
        elif art == "umgekehrt":                              # w:wordWrap w:val="0" = Umbruch auch mitten im Wort
            e.set(qn("w:val"), "0" if w[k] else "1")
        ppr.insert_element_before(e, *_FOLGE[_FOLGE.index(tag) + 1:])


def aus_ppr(ppr) -> dict:
    """Das Gegenstück zu ``in_ppr``: die Absatzoptionen aus ``w:pPr`` (nur, was gesetzt ist)."""
    from docx.oxml.ns import qn
    w = {}
    if ppr is None:
        return w
    for k, (tag, art) in _DOCX.items():
        e = ppr.find(qn(tag))
        if e is None:
            continue
        v = e.get(qn("w:val"))
        if art == "text":
            w[k] = v or "auto"
        elif art == "keep":
            w[k] = v not in ("0", "false", "off")
        elif art == "umgekehrt":
            w[k] = v in ("0", "false", "off")
        else:
            w[k] = v not in ("0", "false", "off")
    return w
