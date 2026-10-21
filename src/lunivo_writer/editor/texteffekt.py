"""Texteffekte, die Lunivo zeichnet: Füllung des Textes (Farbe, Transparenz) und Kontur (Farbe, Breite, Linienart).

Ein Effekt ist ``{"fuell": "farbe"|"keine", "farbe": "#rrggbb"|"", "transparenz": 0…100, "kontur": bool, "kontur_farbe": "#rrggbb",
"kontur_breite": pt, "kontur_art": Schlüssel aus ``KONTUR_ARTEN``}``. Als Text (für eine Formatvorlage): ``transparenz|kontur_farbe|breite|art``
(leer = kein Effekt; die Füllfarbe steht bei der Vorlage in ihrem Feld „farbe“). Schatten, Spiegelung, Leuchten und 3D gibt es nicht,
weil Qt sie am Text nicht zeichnet.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QTextCharFormat, QTextFormat

KONTUR_ARTEN = {"einfach": ("Durchgezogen", Qt.SolidLine), "gepunktet": ("Gepunktet", Qt.DotLine), "gestrichelt": ("Gestrichelt", Qt.DashLine),
                "strichpunkt": ("Strich-Punkt", Qt.DashDotLine), "strichpunktpunkt": ("Strich-Punkt-Punkt", Qt.DashDotDotLine)}
EFFEKT = {"fuell": "farbe", "farbe": "", "transparenz": 0, "kontur": False, "kontur_farbe": "#000000", "kontur_breite": 0.75, "kontur_art": "einfach"}


def zu_format(w: dict) -> QTextCharFormat:
    """Zeichenformat, das den Effekt zeichnet (zum Anwenden im Editor und für Vorschauen)."""
    w = {**EFFEKT, **w}
    f = QTextCharFormat()
    if w["fuell"] == "keine":
        f.setForeground(QColor(0, 0, 0, 0))
    elif w["farbe"] or w["transparenz"]:
        c = QColor(w["farbe"] or "#000000")
        c.setAlphaF(1.0 - w["transparenz"] / 100)
        f.setForeground(c)
    if w["kontur"]:
        p = QPen(QColor(w["kontur_farbe"]), max(0.1, w["kontur_breite"]) / 0.75, KONTUR_ARTEN.get(w["kontur_art"], KONTUR_ARTEN["einfach"])[1])
    else:
        p = QPen(Qt.NoPen)
    f.setTextOutline(p)
    return f


def aus_format(cf: QTextCharFormat) -> dict:
    w = dict(EFFEKT)
    if cf.hasProperty(QTextFormat.ForegroundBrush) and cf.foreground().style() != Qt.NoBrush:
        c = cf.foreground().color()
        if c.alpha() == 0:
            w["fuell"] = "keine"
        else:
            w["farbe"] = c.name(); w["transparenz"] = round(100 - c.alphaF() * 100)
    p = cf.textOutline()
    if p.style() != Qt.NoPen:
        w["kontur"] = True; w["kontur_farbe"] = p.color().name(); w["kontur_breite"] = round(p.widthF() * 0.75, 2)
        w["kontur_art"] = next((k for k, v in KONTUR_ARTEN.items() if v[1] == p.style()), "einfach")
    return w


def als_text(w: dict | None) -> str:
    """Nur Transparenz und Kontur; ``""`` wenn weder noch."""
    if not w or not (w.get("kontur") or w.get("transparenz")):
        return ""
    return f"{int(w.get('transparenz', 0))}|{w['kontur_farbe'] if w.get('kontur') else ''}|{w.get('kontur_breite', 0.75):g}|{w.get('kontur_art', 'einfach')}"


def aus_text(text: str | None, farbe: str = "") -> dict | None:
    t = (text or "").split("|")
    if len(t) != 4:
        return None
    try:
        return {**EFFEKT, "farbe": farbe, "transparenz": int(t[0]), "kontur": bool(t[1]), "kontur_farbe": t[1] or "#000000",
                "kontur_breite": float(t[2]), "kontur_art": t[3] if t[3] in KONTUR_ARTEN else "einfach"}
    except ValueError:
        return None


# ---- DOCX (Word-2010-Erweiterung w14:textOutline und w14:textFill) ----------------------------------------------------------
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
_DASH = {"einfach": "solid", "gepunktet": "sysDot", "gestrichelt": "dash", "strichpunkt": "dashDot", "strichpunktpunkt": "lgDashDotDot"}


def _q(name: str) -> str:
    return f"{{{W14}}}{name}"


def in_rpr(rpr, cf: QTextCharFormat) -> None:
    """Kontur, Linienart und Transparenz des Zeichenformats als w14-Elemente an ``w:rPr`` schreiben (nichts, wenn es keinen Effekt gibt)."""
    from lxml import etree
    w = aus_format(cf)
    if w["kontur"]:
        o = etree.SubElement(rpr, _q("textOutline"))
        o.set(_q("w"), str(int(round(w["kontur_breite"] * 12700)))); o.set(_q("cap"), "flat"); o.set(_q("cmpd"), "sng"); o.set(_q("algn"), "ctr")
        c = etree.SubElement(etree.SubElement(o, _q("solidFill")), _q("srgbClr")); c.set(_q("val"), w["kontur_farbe"][1:].upper())
        etree.SubElement(o, _q("prstDash")).set(_q("val"), _DASH.get(w["kontur_art"], "solid"))
        etree.SubElement(o, _q("round"))
    if w["fuell"] == "keine":
        etree.SubElement(etree.SubElement(rpr, _q("textFill")), _q("noFill"))
    elif w["transparenz"]:
        c = etree.SubElement(etree.SubElement(etree.SubElement(rpr, _q("textFill")), _q("solidFill")), _q("srgbClr"))
        c.set(_q("val"), (w["farbe"] or "#000000")[1:].upper())
        etree.SubElement(c, _q("alpha")).set(_q("val"), str(int(round((100 - w["transparenz"]) * 1000))))


def aus_rpr(rpr, cf: QTextCharFormat) -> None:
    """Das Gegenstück zu ``in_rpr``: w14:textOutline und w14:textFill von ``w:rPr`` ins Zeichenformat lesen."""
    if rpr is None:
        return
    o = rpr.find(_q("textOutline"))
    if o is not None:
        farbe = o.find(f"{_q('solidFill')}/{_q('srgbClr')}")
        dash = o.find(_q("prstDash"))
        art = next((k for k, v in _DASH.items() if dash is not None and v == dash.get(_q("val"))), "einfach")
        try:
            breite = int(o.get(_q("w")) or 9525) / 12700
        except ValueError:
            breite = 0.75
        cf.setTextOutline(QPen(QColor("#" + (farbe.get(_q("val")) if farbe is not None else "000000")), max(0.1, breite) / 0.75,
                               KONTUR_ARTEN[art][1]))
    f = rpr.find(_q("textFill"))
    if f is not None:
        if f.find(_q("noFill")) is not None:
            cf.setForeground(QColor(0, 0, 0, 0))
        else:
            c = f.find(f"{_q('solidFill')}/{_q('srgbClr')}")
            if c is not None and c.get(_q("val")):
                farbe = QColor("#" + c.get(_q("val")))
                a = c.find(_q("alpha"))
                if a is not None:
                    try:
                        farbe.setAlphaF(int(a.get(_q("val"))) / 100000)
                    except (TypeError, ValueError):
                        pass
                cf.setForeground(farbe)
