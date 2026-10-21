"""Texteffekte, die Lunivo zeichnet: Füllung des Textes (Farbe, Transparenz) und Kontur (Farbe, Breite, Linienart).

Ein Effekt ist ``{"fuell": "farbe"|"keine", "farbe": "#rrggbb"|"", "transparenz": 0…100, "kontur": bool, "kontur_farbe": "#rrggbb",
"kontur_breite": pt, "kontur_art": Schlüssel aus ``KONTUR_ARTEN``}``. Als Text (für eine Formatvorlage): ``transparenz|kontur_farbe|breite|art``
(leer = kein Effekt; die Füllfarbe steht bei der Vorlage in ihrem Feld „farbe“). Schatten, Spiegelung, Leuchten und 3D gibt es nicht,
weil Qt sie am Text nicht zeichnet.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QTextCharFormat, QTextFormat

from lunivo_writer.editor import textfx

# Schlüssel → (Name, Qt-Strichart oder Strichmuster in Linienbreiten, DOCX-Wert ``a:prstDash``)
KONTUR_ARTEN = {"einfach": ("Durchgezogen", Qt.SolidLine, "solid"), "gepunktet": ("Gepunktet", Qt.DotLine, "sysDot"),
                "fein": ("Fein gestrichelt", [3.0, 1.0], "sysDash"), "gestrichelt": ("Gestrichelt", Qt.DashLine, "dash"),
                "lang": ("Lang gestrichelt", [8.0, 3.0], "lgDash"), "strichpunkt": ("Strich-Punkt", Qt.DashDotLine, "dashDot"),
                "lang_strichpunkt": ("Lang Strich-Punkt", [8.0, 3.0, 1.0, 3.0], "lgDashDot"),
                "strichpunktpunkt": ("Strich-Punkt-Punkt", Qt.DashDotDotLine, "lgDashDotDot")}
# Formen der Konturlinie (zusammen mit der Breite die Spalten der Linienauswahl): einfach, doppelt, dick–dünn
KONTUR_FORMEN = (("einfach", "Einfach"), ("doppelt", "Doppelt"), ("dick_duenn", "Dick–dünn"))


def strich_setzen(pen: QPen, art: str) -> None:
    """Strichart (Muster oder Qt-Stil) in einen Stift schreiben."""
    st = KONTUR_ARTEN.get(art, KONTUR_ARTEN["einfach"])[1]
    if isinstance(st, list):
        pen.setDashPattern(st)
    else:
        pen.setStyle(st)


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
    if w["kontur"] and not ("kontur_verlauf" in w or w.get("kontur_form", "einfach") != "einfach"):   # sonst zeichnet Lunivo die Kontur (textfx)
        p = QPen(QColor(w["kontur_farbe"]), max(0.1, w["kontur_breite"]) / 0.75)
        strich_setzen(p, w["kontur_art"])
    else:
        p = QPen(Qt.NoPen)
    f.setTextOutline(p)
    from lunivo_writer.editor.zusatz import P_EFFEKT
    f.setProperty(P_EFFEKT, textfx.als_text(w))                                  # immer setzen: beim Zusammenführen löscht ein leerer Wert einen alten Effekt
    if w["fuell"] == "verlauf" and w.get("verlauf"):
        f.setForeground(QColor(w["verlauf"].get("farbe1", "#000000")))         # sichtbar, auch wo der Verlauf nicht gezeichnet wird
    return f


def aus_format(cf: QTextCharFormat) -> dict:
    w = dict(EFFEKT)
    if cf.hasProperty(QTextFormat.ForegroundBrush) and cf.foreground().style() != Qt.NoBrush:
        c = cf.foreground().color()
        if c.alpha() == 0:
            w["fuell"] = "keine"
        else:
            w["farbe"] = c.name(); w["transparenz"] = round(100 - c.alphaF() * 100)
    from lunivo_writer.editor.zusatz import P_EFFEKT
    if cf.hasProperty(P_EFFEKT):
        w.update(textfx.aus_text(cf.stringProperty(P_EFFEKT)))
        if "verlauf" in w:
            w["fuell"] = "verlauf"; w["farbe"] = ""
        if "kontur_verlauf" in w or w.get("kontur_form"):
            w["kontur"] = True
    p = cf.textOutline()
    if p.style() != Qt.NoPen:
        w["kontur"] = True; w["kontur_farbe"] = p.color().name(); w["kontur_breite"] = round(p.widthF() * 0.75, 2)
        w["kontur_art"] = next((k for k, v in KONTUR_ARTEN.items() if not isinstance(v[1], list) and v[1] == p.style()), "einfach")
        if p.style() == Qt.CustomDashLine:
            w["kontur_art"] = next((k for k, v in KONTUR_ARTEN.items() if isinstance(v[1], list) and v[1] == list(p.dashPattern())), "einfach")
    return w


def als_text(w: dict | None) -> str:
    """Nur Transparenz und Kontur; ``""`` wenn weder noch."""
    if not w or not (w.get("kontur") or w.get("transparenz") or textfx.hat_effekt(w)):
        return ""
    basis = f"{int(w.get('transparenz', 0))}|{w['kontur_farbe'] if w.get('kontur') else ''}|{w.get('kontur_breite', 0.75):g}|{w.get('kontur_art', 'einfach')}"
    extra = textfx.als_text(w)
    return basis + "|" + extra if extra else basis


def aus_text(text: str | None, farbe: str = "") -> dict | None:
    t = (text or "").split("|", 4)
    if len(t) not in (4, 5):
        return None
    try:
        w = {**EFFEKT, "farbe": farbe, "transparenz": int(t[0]), "kontur": bool(t[1]), "kontur_farbe": t[1] or "#000000",
             "kontur_breite": float(t[2]), "kontur_art": t[3] if t[3] in KONTUR_ARTEN else "einfach"}
        if len(t) == 5:
            w.update(textfx.aus_text(t[4]))
            if "verlauf" in w:
                w["fuell"] = "verlauf"
            if "kontur_verlauf" in w or w.get("kontur_form"):
                w["kontur"] = True
        return w
    except ValueError:
        return None


# ---- DOCX (Word-2010-Erweiterung w14:textOutline und w14:textFill) ----------------------------------------------------------
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
_DASH = {k: v[2] for k, v in KONTUR_ARTEN.items()}


def _q(name: str) -> str:
    return f"{{{W14}}}{name}"


_MATERIAL = {"matt": "matte", "plastik": "plastic", "metall": "metal", "dunkel": "dkEdge", "weich": "softEdge", "hell": "flat"}
_FORM = {"doppelt": "dbl", "dick_duenn": "thickThin"}
_EMU_PT = 12700


def _farbelement(eltern, hexwert: str, alpha_pct: float | None = None):
    from lxml import etree
    c = etree.SubElement(eltern, _q("srgbClr")); c.set(_q("val"), (hexwert or "#000000")[1:].upper())
    if alpha_pct is not None and alpha_pct < 100:
        etree.SubElement(c, _q("alpha")).set(_q("val"), str(int(round(alpha_pct * 1000))))
    return c


def _verlauf_element(eltern, v: dict) -> None:
    from lxml import etree
    g = etree.SubElement(eltern, _q("gradFill"))
    lst = etree.SubElement(g, _q("gsLst"))
    for pos, farbe in ((0, v.get("farbe1", "#000000")), (100000, v.get("farbe2", "#ffffff"))):
        gs = etree.SubElement(lst, _q("gs")); gs.set(_q("pos"), str(pos)); _farbelement(gs, farbe)
    lin = etree.SubElement(g, _q("lin")); lin.set(_q("ang"), str(int(round(v.get("winkel", 90) * 60000)))); lin.set(_q("scaled"), "0")


def in_rpr(rpr, cf: QTextCharFormat) -> None:
    """Texteffekte des Zeichenformats als w14-Elemente an ``w:rPr`` schreiben, in der Reihenfolge des Schemas (nichts, wenn es keinen Effekt gibt)."""
    from lxml import etree
    w = aus_format(cf)
    g = w.get("leuchten")
    if g and g.get("groesse", 0) > 0:
        e = etree.SubElement(rpr, _q("glow")); e.set(_q("rad"), str(int(g["groesse"] * _EMU_PT)))
        _farbelement(e, g.get("farbe", "#4c6ef5"), 100 - g.get("transparenz", 60))
    s = w.get("schatten")
    if s and s.get("art") != "innen":                                       # Innenschatten kennt DOCX nicht
        e = etree.SubElement(rpr, _q("shadow"))
        e.set(_q("blurRad"), str(int(s.get("weich", 0) * _EMU_PT))); e.set(_q("dist"), str(int(s.get("abstand", 0) * _EMU_PT)))
        e.set(_q("dir"), str(int(round(s.get("winkel", 45) * 60000)))); e.set(_q("sx"), str(int(s.get("groesse", 100) * 1000)))
        persp = s.get("art") == "persp"
        e.set(_q("sy"), str(int(s.get("groesse", 100) * 1000 * (-0.4 if persp else 1)))); e.set(_q("kx"), "0"); e.set(_q("ky"), "0")
        e.set(_q("algn"), "b" if persp else "ctr")
        _farbelement(e, s.get("farbe", "#000000"), 100 - s.get("transparenz", 50))
    r = w.get("reflektion")
    if r:
        e = etree.SubElement(rpr, _q("reflection"))
        e.set(_q("blurRad"), str(int(r.get("weich", 0) * _EMU_PT))); e.set(_q("stA"), str(int((100 - r.get("transparenz", 50)) * 1000)))
        e.set(_q("stPos"), "0"); e.set(_q("endA"), "300"); e.set(_q("endPos"), str(int(r.get("groesse", 50) * 1000)))
        e.set(_q("dist"), str(int(r.get("abstand", 0) * _EMU_PT))); e.set(_q("dir"), "5400000"); e.set(_q("fadeDir"), "5400000")
        e.set(_q("sx"), "100000"); e.set(_q("sy"), "-100000"); e.set(_q("kx"), "0"); e.set(_q("ky"), "0"); e.set(_q("algn"), "bl")
    if w["kontur"]:
        o = etree.SubElement(rpr, _q("textOutline"))
        o.set(_q("w"), str(int(round(w["kontur_breite"] * _EMU_PT)))); o.set(_q("cap"), "flat"); o.set(_q("cmpd"), _FORM.get(w.get("kontur_form"), "sng")); o.set(_q("algn"), "ctr")
        if "kontur_verlauf" in w:
            _verlauf_element(o, w["kontur_verlauf"])
        else:
            _farbelement(etree.SubElement(o, _q("solidFill")), w["kontur_farbe"])
        etree.SubElement(o, _q("prstDash")).set(_q("val"), _DASH.get(w["kontur_art"], "solid"))
        etree.SubElement(o, _q("round"))
    if w["fuell"] == "keine":
        etree.SubElement(etree.SubElement(rpr, _q("textFill")), _q("noFill"))
    elif w["fuell"] == "verlauf" and "verlauf" in w:
        _verlauf_element(etree.SubElement(rpr, _q("textFill")), w["verlauf"])
    elif w["transparenz"]:
        c = _farbelement(etree.SubElement(etree.SubElement(rpr, _q("textFill")), _q("solidFill")), w["farbe"] or "#000000")
        etree.SubElement(c, _q("alpha")).set(_q("val"), str(int(round((100 - w["transparenz"]) * 1000))))
    d = w.get("d3")
    if d and d.get("tiefe", 0) > 0:
        e = etree.SubElement(rpr, _q("props3d")); e.set(_q("extrusionH"), str(int(d["tiefe"] * _EMU_PT)))
        e.set(_q("contourW"), str(int(d.get("kontur", 0) * _EMU_PT))); e.set(_q("prstMaterial"), _MATERIAL.get(d.get("material", "matt"), "matte"))
        _farbelement(etree.SubElement(e, _q("extrusionClr")), d.get("tiefe_farbe", "#868e96"))
        _farbelement(etree.SubElement(e, _q("contourClr")), d.get("kontur_farbe", "#343a40"))


def _wert(e, name: str, vorgabe: float = 0.0) -> float:
    try:
        return float(e.get(_q(name)))
    except (TypeError, ValueError):
        return vorgabe


def _farbe_aus(e) -> tuple[str, float]:
    """(Farbe, Transparenz in %) eines Elements mit w14:srgbClr darunter."""
    c = e.find(_q("srgbClr")) if e is not None else None
    if c is None:
        return "#000000", 0.0
    a = c.find(_q("alpha"))
    return "#" + (c.get(_q("val")) or "000000"), (100 - _wert(a, "val", 100000) / 1000) if a is not None else 0.0


def _verlauf_aus(g) -> dict:
    stopps = [(_wert(gs, "pos"), "#" + ((gs.find(_q("srgbClr")).get(_q("val"))) if gs.find(_q("srgbClr")) is not None else "000000")) for gs in g.iter(_q("gs"))]
    stopps.sort()
    lin = g.find(_q("lin"))
    return {"farbe1": stopps[0][1] if stopps else "#000000", "farbe2": stopps[-1][1] if stopps else "#ffffff",
            "winkel": round(_wert(lin, "ang", 5400000) / 60000) % 360 if lin is not None else 90}


def aus_rpr(rpr, cf: QTextCharFormat) -> None:
    """Das Gegenstück zu ``in_rpr``: die w14-Elemente von ``w:rPr`` ins Zeichenformat lesen."""
    if rpr is None:
        return
    w: dict = dict(EFFEKT)
    extra = False
    o = rpr.find(_q("textOutline"))
    if o is not None:
        w["kontur"] = True
        g = o.find(_q("gradFill"))
        farbe = o.find(f"{_q('solidFill')}/{_q('srgbClr')}")
        dash = o.find(_q("prstDash"))
        w["kontur_art"] = next((k for k, v in _DASH.items() if dash is not None and v == dash.get(_q("val"))), "einfach")
        w["kontur_breite"] = max(0.1, _wert(o, "w", 9525) / _EMU_PT)
        w["kontur_farbe"] = "#" + (farbe.get(_q("val")) if farbe is not None else "000000")
        if g is not None:
            w["kontur_verlauf"] = _verlauf_aus(g)
        form = next((k for k, v in _FORM.items() if v == o.get(_q("cmpd"))), None)
        if form:
            w["kontur_form"] = form
    f = rpr.find(_q("textFill"))
    if f is not None:
        if f.find(_q("noFill")) is not None:
            w["fuell"] = "keine"
        elif f.find(_q("gradFill")) is not None:
            w["fuell"] = "verlauf"; w["verlauf"] = _verlauf_aus(f.find(_q("gradFill")))
        else:
            farbe, trans = _farbe_aus(f.find(_q("solidFill")))
            w["farbe"] = farbe; w["transparenz"] = int(round(trans))
    g = rpr.find(_q("glow"))
    if g is not None:
        farbe, trans = _farbe_aus(g)
        w["leuchten"] = {"farbe": farbe, "groesse": _wert(g, "rad") / _EMU_PT, "transparenz": trans}
    s = rpr.find(_q("shadow"))
    if s is not None:
        farbe, trans = _farbe_aus(s)
        w["schatten"] = {"art": "persp" if _wert(s, "sy", 100000) < 0 else "aussen", "farbe": farbe, "transparenz": trans,
                         "groesse": abs(_wert(s, "sx", 100000)) / 1000, "weich": _wert(s, "blurRad") / _EMU_PT, "abstand": _wert(s, "dist") / _EMU_PT,
                         "winkel": round(_wert(s, "dir") / 60000) % 360}
    r = rpr.find(_q("reflection"))
    if r is not None:
        w["reflektion"] = {"groesse": _wert(r, "endPos", 50000) / 1000, "transparenz": 100 - _wert(r, "stA", 50000) / 1000, "weich": _wert(r, "blurRad") / _EMU_PT,
                           "abstand": _wert(r, "dist") / _EMU_PT}
    d = rpr.find(_q("props3d"))
    if d is not None and _wert(d, "extrusionH") > 0:
        tf, _t = _farbe_aus(d.find(_q("extrusionClr"))); kf, _t = _farbe_aus(d.find(_q("contourClr")))
        w["d3"] = {"tiefe": _wert(d, "extrusionH") / _EMU_PT, "tiefe_farbe": tf, "kontur": _wert(d, "contourW") / _EMU_PT, "kontur_farbe": kf,
                   "material": next((k for k, v in _MATERIAL.items() if v == d.get(_q("prstMaterial"))), "matt"), "beleuchtung": "neutral", "winkel": 0}
    if w == dict(EFFEKT):
        return
    fmt = zu_format(w)
    cf.merge(fmt)
