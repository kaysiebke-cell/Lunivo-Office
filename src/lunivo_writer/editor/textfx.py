"""Texteffekte, die Qt am Text nicht kennt und die Lunivo über den Umrissen der Buchstaben selbst zeichnet: Farbverlauf in Füllung und Kontur,
Schatten, Spiegelung, Leuchten und 3D-Format.

Ein Effekt (``fx``) ist ein Wörterbuch; nicht gesetzte Teile fehlen:

* ``verlauf``: {"farbe1", "farbe2", "winkel"} — Farbverlauf als Füllung (dann ist ``fuell`` = "verlauf")
* ``kontur_verlauf``: wie ``verlauf``, für die Kontur
* ``kontur_form``: "einfach" | "doppelt" | "dick_duenn" — mehrfache Konturlinien
* ``schatten``: {"art": "aussen" | "innen" | "persp", "farbe", "transparenz" %, "groesse" %, "weich" pt, "abstand" pt, "winkel" Grad}
* ``reflektion``: {"groesse" %, "transparenz" %, "weich" pt, "abstand" pt}
* ``leuchten``: {"farbe", "groesse" pt, "transparenz" %}
* ``d3``: {"tiefe" pt, "tiefe_farbe", "kontur" pt, "kontur_farbe", "material", "beleuchtung", "winkel" Grad}

``fx_zeichnen`` malt die Effekte zu einem Pfad (den Umrissen eines Textstücks) hinter und über den Text; ``absaetze_zeichnen`` holt die Pfade
aus dem Layout des Dokuments (Editor und PDF rufen es zusammen mit den Rahmen und Nummern auf).
"""
from __future__ import annotations

import json
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPainterPathStroker, QPen, QTransform

PX = 96 / 72                                    # Punkt → Bildpunkt

MATERIAL = (("matt", "Matt"), ("plastik", "Plastik"), ("metall", "Metall"), ("dunkel", "Dunkle Kanten"), ("weich", "Weicher Rand"), ("hell", "Hell"))
BELEUCHTUNG = (("neutral", "Neutral"), ("weich", "Weich"), ("hart", "Hart"), ("warm", "Warm"), ("kalt", "Kalt"), ("kontrast", "Kontrast"))


def _farbe(hexwert: str, transparenz: float = 0.0) -> QColor:
    c = QColor(hexwert or "#000000")
    c.setAlphaF(max(0.0, min(1.0, 1.0 - transparenz / 100)))
    return c


def hat_effekt(fx: dict | None) -> bool:
    return bool(fx) and any(k in fx for k in ("verlauf", "kontur_verlauf", "kontur_form", "schatten", "reflektion", "leuchten", "d3"))


def als_text(fx: dict | None) -> str:
    """Nur die Teile, die Lunivo selbst zeichnet, als JSON für das Zeichenformat (leer = keiner)."""
    if not hat_effekt(fx):
        return ""
    erlaubt = ["verlauf", "kontur_verlauf", "kontur_form", "schatten", "reflektion", "leuchten", "d3"]
    if "kontur_verlauf" in fx or fx.get("kontur_form"):                  # die Kontur zeichnet dann Lunivo: Farbe, Breite und Strichart gehören dazu
        erlaubt += ["kontur_art", "kontur_breite", "kontur_farbe"]
    return json.dumps({k: v for k, v in fx.items() if k in erlaubt}, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def aus_text(text: str | None) -> dict:
    try:
        d = json.loads(text) if text else {}
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


# ---- Bausteine -------------------------------------------------------------------------------------------------------------
def _verlauf(rect: QRectF, v: dict) -> QLinearGradient:
    w = math.radians(v.get("winkel", 90))
    mitte = rect.center()
    r = (abs(math.cos(w)) * rect.width() + abs(math.sin(w)) * rect.height()) / 2 or 1.0       # halbe Länge der Verlaufsstrecke durch das Rechteck
    d = QPointF(math.cos(w) * r, math.sin(w) * r)
    g = QLinearGradient(mitte - d, mitte + d)
    g.setColorAt(0, QColor(v.get("farbe1", "#000000"))); g.setColorAt(1, QColor(v.get("farbe2", "#ffffff")))
    return g


def _weich(p: QPainter, pfad: QPainterPath, farbe: QColor, radius: float, ausserhalb: bool = True) -> None:
    """Pfad mit weichem Rand: gefüllt, dazu Striche in wachsender Breite und sinkender Deckkraft."""
    if radius <= 0.3:
        p.fillPath(pfad, farbe); return
    schritte = 7
    a = farbe.alphaF()
    kern = QColor(farbe); kern.setAlphaF(a * 0.55)
    p.fillPath(pfad, kern)
    for k in range(1, schritte + 1):
        f = QColor(farbe); f.setAlphaF(a * 0.45 / schritte * (1.0 + (schritte - k) / schritte))
        pen = QPen(f, 2 * radius * k / schritte); pen.setJoinStyle(Qt.RoundJoin); pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.drawPath(pfad)
    p.setPen(Qt.NoPen)


def _richtung(winkel: float) -> QPointF:
    w = math.radians(winkel)
    return QPointF(math.cos(w), math.sin(w))


def _helligkeit(c: QColor, f: float) -> QColor:
    return c.lighter(int(100 * f)) if f >= 1.0 else c.darker(int(100 / max(f, 0.05)))


def _kontur_pfade(pfad: QPainterPath, breite: float, form: str, art: str = "einfach") -> list[QPainterPath]:
    """Die Flächen einer Konturlinie: einfach ein Strich, doppelt zwei Streifen mit Lücke, dick–dünn ein dicker und ein dünner."""
    from lunivo_writer.editor.texteffekt import KONTUR_ARTEN
    st = KONTUR_ARTEN.get(art, KONTUR_ARTEN["einfach"])[1]

    def strich(w: float, gestrichelt: bool = False) -> QPainterPath:
        s = QPainterPathStroker(); s.setWidth(max(0.1, w)); s.setJoinStyle(Qt.RoundJoin)
        s.setCapStyle(Qt.FlatCap if gestrichelt else Qt.RoundCap)
        if gestrichelt and st != Qt.SolidLine:
            s.setDashPattern(st)
        return s.createStroke(pfad)
    if form == "einfach":
        return [strich(breite, True)]
    if form == "doppelt":
        return [strich(3 * breite).subtracted(strich(breite))]
    if form == "dick_duenn":
        return [strich(3 * breite).subtracted(strich(1.8 * breite)), strich(0.6 * breite)]
    return [strich(breite)]


def fx_zeichnen(p: QPainter, pfad: QPainterPath, fx: dict, grundlinie: float, schrift_px: float, basis_farbe: QColor | None = None,
                kontur: tuple[QColor, float, str] | None = None) -> None:
    """Die Effekte zu einem Textstück zeichnen. ``pfad``: Umrisse in Zeichenkoordinaten, ``grundlinie``: y der Schriftlinie, ``schrift_px``: Schriftgröße.
    Der Text selbst ist schon gezeichnet (Qt); alles, was hinter ihm liegt, wird auf die Fläche außerhalb der Buchstaben beschränkt."""
    if pfad.isEmpty():
        return
    p.save(); p.setRenderHint(QPainter.Antialiasing)
    grenze = QPainterPath(); grenze.addRect(pfad.boundingRect().adjusted(-200, -200, 200, 400 + schrift_px))
    aussen = grenze.subtracted(pfad)
    rect = pfad.boundingRect()
    # ---- hinter dem Text
    r = fx.get("reflektion")
    if r:
        sp = QTransform().translate(0, 2 * grundlinie + r.get("abstand", 0) * PX).scale(1, -1)
        spiegel = sp.map(pfad)
        hoch = max(1.0, schrift_px * 1.0 * r.get("groesse", 50) / 100)
        g = QLinearGradient(0, grundlinie + r.get("abstand", 0) * PX, 0, grundlinie + r.get("abstand", 0) * PX + hoch)
        g.setColorAt(0, _farbe(basis_farbe.name() if basis_farbe else "#000000", r.get("transparenz", 50)))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        p.save(); p.setClipPath(aussen)
        if r.get("weich", 0) > 0:
            _weich(p, spiegel, _farbe(basis_farbe.name() if basis_farbe else "#000000", 85), r["weich"] * PX * 0.5)
        else:
            p.fillPath(spiegel, QBrush(g))
        p.restore()
    d3 = fx.get("d3")
    if d3 and d3.get("tiefe", 0) > 0:
        tiefe = d3["tiefe"] * PX
        richt = _richtung(d3.get("winkel", 45) + 45)
        n = max(2, int(tiefe))
        basis = QColor(d3.get("tiefe_farbe", "#808080"))
        mat, licht = d3.get("material", "matt"), d3.get("beleuchtung", "neutral")
        p.save(); p.setClipPath(aussen); p.setPen(Qt.NoPen)
        for k in range(n, 0, -1):
            t = k / n
            f = 1.0
            if mat == "plastik":
                f = 1.25 - 0.5 * t
            elif mat == "metall":
                f = 1.0 + 0.45 * math.sin(t * math.pi * 2)
            elif mat == "dunkel":
                f = 0.6 + 0.4 * (1 - t)
            elif mat == "weich":
                f = 1.15 - 0.25 * t
            elif mat == "hell":
                f = 1.3
            f *= {"neutral": 1.0, "weich": 1.08, "hart": 0.8 + 0.5 * (1 - t), "warm": 1.0, "kalt": 1.0, "kontrast": 0.7 + 0.7 * t}.get(licht, 1.0)
            c = _helligkeit(basis, max(0.3, f))
            if licht == "warm":
                c = QColor(min(255, c.red() + 25), c.green(), max(0, c.blue() - 20))
            elif licht == "kalt":
                c = QColor(max(0, c.red() - 20), c.green(), min(255, c.blue() + 25))
            p.fillPath(QTransform().translate(richt.x() * tiefe * t, richt.y() * tiefe * t).map(pfad), c)
        if d3.get("kontur", 0) > 0:
            pen = QPen(QColor(d3.get("kontur_farbe", "#404040")), d3["kontur"] * PX)
            pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(pen); p.drawPath(QTransform().translate(richt.x() * tiefe, richt.y() * tiefe).map(pfad)); p.drawPath(pfad)
        p.restore()
    s = fx.get("schatten")
    if s and s.get("art", "aussen") != "innen":
        abst = s.get("abstand", 3) * PX
        dr = _richtung(s.get("winkel", 45))
        sk = s.get("groesse", 100) / 100
        farbe = _farbe(s.get("farbe", "#000000"), s.get("transparenz", 50))
        t = QTransform().translate(dr.x() * abst, dr.y() * abst)
        if s.get("art") == "persp":                       # flach auf den Boden gelegt und in Richtung des Lichts geneigt
            t = QTransform()
            t.translate(dr.x() * abst * 0.5, grundlinie + abst * 0.3); t.shear(-dr.x() * 0.8, 0); t.scale(sk, -0.4 * sk); t.translate(0, -grundlinie)
        else:
            t = QTransform().translate(rect.center().x(), rect.center().y()).scale(sk, sk).translate(-rect.center().x(), -rect.center().y()) \
                * QTransform().translate(dr.x() * abst, dr.y() * abst)
        p.save(); p.setClipPath(aussen); p.setPen(Qt.NoPen)
        _weich(p, t.map(pfad), farbe, s.get("weich", 4) * PX * 0.6)
        p.restore()
    g = fx.get("leuchten")
    if g and g.get("groesse", 0) > 0:
        farbe = _farbe(g.get("farbe", "#4c6ef5"), g.get("transparenz", 60))
        p.save(); p.setClipPath(aussen); p.setPen(Qt.NoPen)
        _weich(p, pfad, farbe, g["groesse"] * PX)
        p.restore()
    # ---- über dem Text
    if "verlauf" in fx:
        p.save(); p.setClipPath(pfad); p.fillRect(rect.adjusted(-2, -2, 2, 2), QBrush(_verlauf(rect, fx["verlauf"]))); p.restore()
    if s and s.get("art") == "innen":
        abst = s.get("abstand", 3) * PX
        dr = _richtung(s.get("winkel", 45))
        farbe = _farbe(s.get("farbe", "#000000"), s.get("transparenz", 50))
        innen = QPainterPath(); innen.addRect(rect.adjusted(-50, -50, 50, 50))
        loch = QTransform().translate(dr.x() * abst, dr.y() * abst).map(pfad)
        p.save(); p.setClipPath(pfad); p.setPen(Qt.NoPen)
        _weich(p, innen.subtracted(loch), farbe, s.get("weich", 4) * PX * 0.5)
        p.restore()
    if kontur is not None or "kontur_verlauf" in fx or fx.get("kontur_form", "einfach") != "einfach":
        farbe, breite, form, *rest = kontur if kontur else (QColor("#000000"), 0.75 * PX, fx.get("kontur_form", "einfach"))
        brush = QBrush(_verlauf(rect, fx["kontur_verlauf"])) if "kontur_verlauf" in fx else QBrush(farbe)
        for flaeche in _kontur_pfade(pfad, breite, fx.get("kontur_form", form), rest[0] if rest else fx.get("kontur_art", "einfach")):
            p.fillPath(flaeche, brush)
    p.restore()


def _woerter(text: str) -> list[tuple[int, int]]:
    """Die Wörter eines Textes als (Anfang, Ende); Leerzeichen bleiben frei („Nur Wörter“)."""
    aus, start = [], None
    for i, ch in enumerate(text + " "):
        if ch.isspace():
            if start is not None:
                aus.append((start, i)); start = None
        elif start is None:
            start = i
    return aus


# Strichmuster der selbst gezeichneten Unterstreichungen (in Linienbreiten) und ob sie dick, doppelt oder wellig sind
_UNTER_MUSTER = {"einfach": ([], 1, False), "gepunktet": ([1.0, 1.0], 1, False), "gestrichelt": ([3.0, 2.0], 1, False),
                 "strichpunkt": ([4.0, 2.0, 1.0, 2.0], 1, False), "strichpunktpunkt": ([4.0, 2.0, 1.0, 2.0, 1.0, 2.0], 1, False),
                 "wellig": ([], 1, True), "woerter": ([], 1, False), "doppelt": ([], 1, False), "dick": ([], 2, False), "dick_gepunktet": ([1.0, 1.0], 2, False),
                 "dick_gestrichelt": ([3.0, 2.0], 2, False), "lang": ([7.0, 3.0], 1, False), "dick_lang": ([7.0, 3.0], 2, False),
                 "dick_strichpunkt": ([4.0, 2.0, 1.0, 2.0], 2, False), "dick_strichpunktpunkt": ([4.0, 2.0, 1.0, 2.0, 1.0, 2.0], 2, False),
                 "dick_wellig": ([], 2, True), "doppelwellig": ([], 1, True)}


def _unterstrich(p: QPainter, strecken: list[tuple[float, float]], art: str, grundlinie: float, groesse: float, farbe: QColor) -> None:
    """Unterstreichungen, die Qt nicht kennt: doppelt, dick, lang gestrichelt, Wellen in zwei Stärken, nur Wörter."""
    muster, dicke, wellig = _UNTER_MUSTER.get(art, ([], 1, False))
    w = max(1.0, groesse * 0.05) * dicke
    y = grundlinie + max(1.5, groesse * 0.12)
    p.save(); p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(farbe, w); pen.setCapStyle(Qt.FlatCap)
    if muster:
        pen.setDashPattern(muster)
    p.setPen(pen)
    for x0, x1 in strecken:
        if x1 <= x0:
            continue
        zeilen = (y, y + w * 2.2) if art == "doppelt" else (y,)
        for yy in zeilen:
            if wellig:
                pf = QPainterPath(); pf.moveTo(x0, yy)
                x, rich = x0, 1
                schritt = max(2.0, groesse * 0.12)
                while x < x1:
                    pf.quadTo(x + schritt / 2, yy + rich * schritt * 0.5, min(x + schritt, x1), yy); x += schritt; rich = -rich
                p.drawPath(pf)
                if art == "doppelwellig":
                    p.translate(0, w * 2.6); p.drawPath(pf); p.translate(0, -w * 2.6)
            else:
                p.drawLine(QPointF(x0, yy), QPointF(x1, yy))
    p.restore()


def unter_symbol(art: str, groesse=(70, 16), farbe: str = "#e6e9ec"):
    """Bildchen einer Unterstreichungsart für Auswahllisten (dieselbe Zeichnung wie im Text)."""
    from PySide6.QtGui import QIcon, QPixmap
    pm = QPixmap(*groesse); pm.fill(Qt.transparent)
    p = QPainter(pm)
    if art:
        _unterstrich(p, [(3, groesse[0] - 3)], art, groesse[1] * 0.38, 9.0, QColor(farbe))
    p.end()
    return QIcon(pm)


def _doppelt_durch(p: QPainter, rect: QRectF, grundlinie: float, groesse: float, farbe: QColor) -> None:
    """Die zweite Durchstreichlinie (die erste zeichnet Qt): zwei Linien in Höhe der Kleinbuchstaben."""
    p.save(); p.setPen(QPen(farbe, max(1.0, groesse * 0.05)))
    for dy in (0.26, 0.38):
        y = grundlinie - groesse * dy
        p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
    p.restore()


def _betonung(p: QPainter, glyphen: list[tuple[float, float, float]], art: str, grundlinie: float, groesse: float, farbe: QColor) -> None:
    """Betonungszeichen: ein Punkt, Kreis oder Komma über (oder ein Punkt unter) jedem Buchstaben."""
    r = max(1.2, groesse * 0.065)
    p.save(); p.setRenderHint(QPainter.Antialiasing)
    for x, oben, unten in glyphen:
        if art == "unten":
            p.setPen(Qt.NoPen); p.setBrush(farbe); p.drawEllipse(QPointF(x, max(unten, grundlinie) + r * 2.2), r, r)
            continue
        y = oben - r * 2.2
        if art == "kreis":
            p.setPen(QPen(farbe, max(0.8, r * 0.5))); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(x, y), r, r)
        elif art == "komma":
            p.setPen(Qt.NoPen); p.setBrush(farbe); p.drawEllipse(QPointF(x, y), r, r)
            p.setPen(QPen(farbe, max(0.8, r * 0.6))); p.drawLine(QPointF(x + r * 0.6, y + r * 0.4), QPointF(x - r * 0.4, y + r * 2.0))
        else:
            p.setPen(Qt.NoPen); p.setBrush(farbe); p.drawEllipse(QPointF(x, y), r, r)
    p.restore()


def text_pfad(text: str, font, ursprung: QPointF) -> tuple[QPainterPath, float]:
    """Umrisse eines Textes (für Vorschauen); → (Pfad, y der Grundlinie)."""
    pf = QPainterPath()
    pf.addText(ursprung, font, text)
    return pf, ursprung.y()


def vorschau_zeichnen(p: QPainter, rect: QRectF, text: str, font, fx: dict, farbe: QColor, kontur: tuple[QColor, float, str] | None = None) -> None:
    """Text mit Effekt zentriert in ein Rechteck zeichnen (Kacheln und Vorschau der Fenster); der Text selbst wird hier mitgezeichnet."""
    from PySide6.QtGui import QFontMetricsF
    fm = QFontMetricsF(font)
    x = rect.center().x() - fm.horizontalAdvance(text) / 2
    y = rect.center().y() + (fm.ascent() - fm.descent()) / 2
    pfad, gl = text_pfad(text, font, QPointF(x, y))
    p.save(); p.setRenderHint(QPainter.Antialiasing)
    if farbe.alpha() > 0:                                   # erst der Text (wie im Dokument, wo Qt ihn zeichnet), dann die Effekte
        p.fillPath(pfad, farbe)
    fx_zeichnen(p, pfad, fx, gl, font.pixelSize() if font.pixelSize() > 0 else font.pointSizeF() * PX, farbe, kontur)
    p.restore()


# ---- im Dokument -----------------------------------------------------------------------------------------------------------
def absaetze_zeichnen(p: QPainter, d) -> None:
    """Die Effekte aller Textstücke des Dokuments zeichnen (Textstücke mit ``P_EFFEKT``). Koordinaten: Dokument."""
    from PySide6.QtGui import QTextFormat
    b = d.firstBlock()
    while b.isValid():
        tl = b.layout()
        if tl is not None and b.isVisible() and tl.lineCount():
            it = b.begin()
            while not it.atEnd():
                fr = it.fragment()
                cf = fr.charFormat()
                if fr.isValid() and hat_zeichen_effekt(cf):
                    _stueck(p, b, tl, fr.position() - b.position(), fr.length(), cf, aus_text(cf.stringProperty(_P("P_EFFEKT"))))
                it += 1
        b = b.next()


def _P(name: str):
    from lunivo_writer.editor import zusatz
    return getattr(zusatz, name)


def hat_zeichen_effekt(cf) -> bool:
    """Hat dieses Zeichenformat etwas, das Lunivo selbst zeichnet: Effekte, doppelt durchgestrichen oder Betonungszeichen?"""
    return bool(cf.stringProperty(_P("P_EFFEKT")) or cf.stringProperty(_P("P_BETONUNG")) or cf.stringProperty(_P("P_UNTER"))
                or (cf.hasProperty(_P("P_DOPPELT")) and cf.property(_P("P_DOPPELT"))))


def _stueck(p: QPainter, b, tl, von: int, laenge: int, cf, fx: dict) -> None:
    from PySide6.QtGui import QTextFormat
    for i in range(tl.lineCount()):
        z = tl.lineAt(i)
        a, e = max(von, z.textStart()), min(von + laenge, z.textStart() + z.textLength())
        if e <= a:
            continue
        pfad = QPainterPath()
        for run in z.glyphRuns(a, e - a):
            rf = run.rawFont()
            for idx, pos in zip(run.glyphIndexes(), run.positions()):
                g = rf.pathForGlyph(idx); g.translate(pos); pfad.addPath(g)
        if pfad.isEmpty():
            continue
        ursprung = tl.position() + z.position()
        pfad.translate(ursprung)
        glyphen = []                                          # Mitte, Ober- und Unterkante jedes Buchstabens (für Betonungszeichen)
        for run in z.glyphRuns(a, e - a):
            rf = run.rawFont()
            for idx, pos in zip(run.glyphIndexes(), run.positions()):
                gp = rf.pathForGlyph(idx)
                if not gp.isEmpty():
                    br = gp.boundingRect().translated(pos + ursprung)
                    glyphen.append((br.center().x(), br.top(), br.bottom()))
        farbe = cf.foreground().color() if cf.hasProperty(QTextFormat.ForegroundBrush) else QColor("black")
        if farbe.alpha() == 0:
            farbe = QColor("black")
        kontur = None
        if "kontur_verlauf" in fx or fx.get("kontur_form", "einfach") != "einfach":
            kontur = (QColor(fx.get("kontur_farbe", "#000000")), max(0.1, fx.get("kontur_breite", 0.75)) * PX, fx.get("kontur_form", "einfach"),
                      fx.get("kontur_art", "einfach"))
        groesse = cf.font().pixelSize() if cf.font().pixelSize() > 0 else cf.font().pointSizeF() * PX
        grundlinie = ursprung.y() + z.ascent()
        if fx:
            fx_zeichnen(p, pfad, fx, grundlinie, groesse, farbe, kontur)
        if cf.hasProperty(_P("P_DOPPELT")) and cf.property(_P("P_DOPPELT")):
            _doppelt_durch(p, pfad.boundingRect(), grundlinie, groesse, farbe)
        art = cf.stringProperty(_P("P_UNTER"))
        if art:
            x0, x1 = tl.position().x() + z.cursorToX(a)[0], tl.position().x() + z.cursorToX(e)[0]
            woerter = [(tl.position().x() + z.cursorToX(a + i)[0], tl.position().x() + z.cursorToX(a + j)[0]) for i, j in _woerter(b.text()[a:e])] \
                if art == "woerter" else [(x0, x1)]
            _unterstrich(p, woerter, art, grundlinie, groesse, cf.underlineColor() if cf.underlineColor().isValid() and cf.underlineStyle() != 0 else farbe)
        betonung = cf.stringProperty(_P("P_BETONUNG"))
        if betonung:
            _betonung(p, glyphen, betonung, grundlinie, groesse, farbe)


# ---- Voreinstellungen der Auswahlen im Fenster „Texteffekte formatieren“ ---------------------------------------------------
_RICHTUNGEN = (("Unten rechts", 45), ("Unten", 90), ("Unten links", 135), ("Rechts", 0), ("Zentriert", 0), ("Links", 180),
               ("Oben rechts", 315), ("Oben", 270), ("Oben links", 225))


def schatten_vorgaben() -> list[tuple[str, str, dict]]:
    """[(Abschnitt, Name, Schatten)] — Außen, Innen (je 9) und Perspektive (5)."""
    aus = []
    for art, abschnitt in (("aussen", "Außen"), ("innen", "Innen")):
        for name, w in _RICHTUNGEN:
            zentral = name == "Zentriert"
            aus.append((abschnitt, name, {"art": art, "farbe": "#000000", "transparenz": 50 if art == "aussen" else 40, "groesse": 100,
                                          "weich": 6 if zentral else 3, "abstand": 0 if zentral else 4, "winkel": w}))
    for i, (name, w) in enumerate((("Perspektive diagonal unten rechts", 45), ("Perspektive diagonal unten links", 135), ("Perspektive unten", 90),
                                   ("Perspektive rechts", 0), ("Perspektive links", 180))):
        aus.append(("Perspektive", name, {"art": "persp", "farbe": "#000000", "transparenz": 55, "groesse": 100, "weich": 2, "abstand": 8, "winkel": w}))
    return aus


def reflektion_vorgaben() -> list[tuple[str, dict]]:
    """9 Spiegelungen: drei Größen (eng, halb, voll) mal drei Abstände."""
    aus = []
    for groesse, gname in ((35, "enge"), (50, "halbe"), (90, "volle")):
        for abstand in (0, 4, 8):
            aus.append((f"{gname.capitalize()} Spiegelung, Abstand {abstand} pt", {"groesse": groesse, "transparenz": 55 if groesse < 90 else 65, "weich": 0, "abstand": abstand}))
    return aus


def leuchten_vorgaben() -> list[tuple[str, dict]]:
    """24 Leuchtvarianten: sechs Farben mal vier Größen."""
    aus = []
    for groesse in (5, 8, 11, 18):
        for name, farbe in (("Blau", "#4c6ef5"), ("Rot", "#fa5252"), ("Grau", "#868e96"), ("Gelb", "#fab005"), ("Hellblau", "#339af0"), ("Grün", "#40c057")):
            aus.append((f"{name}, {groesse} pt", {"farbe": farbe, "groesse": groesse, "transparenz": 60}))
    return aus


def voreinstellung_icon(fx: dict, groesse=(52, 40), text: str = "A", farbe: str = "#adb5bd"):
    """Kachelbild einer Voreinstellung: ein „A“ mit dem Effekt auf weißem Grund."""
    from PySide6.QtGui import QFont, QIcon, QPixmap
    pm = QPixmap(*groesse); pm.fill(QColor("white"))
    p = QPainter(pm)
    f = QFont("Liberation Sans"); f.setPixelSize(int(groesse[1] * 0.62)); f.setBold(True)
    vorschau_zeichnen(p, QRectF(0, 0, groesse[0], groesse[1] * 0.92), text, f, fx, QColor(farbe))
    p.end()
    return QIcon(pm)


def wordart_vorgaben() -> list[tuple[str, dict]]:
    """Die 15 Formatvorlagen im Menü „Texteffekte ▸ WordArt“: Füllung, Kontur, Schatten (vollständige Effekte, ersetzen die bisherigen)."""
    def e(**k):
        return {"fuell": "farbe", "farbe": "#111417", "transparenz": 0, "kontur": False, "kontur_farbe": "#000000", "kontur_breite": 0.75, "kontur_art": "einfach", **k}
    sch = {"art": "aussen", "farbe": "#000000", "transparenz": 55, "groesse": 100, "weich": 2, "abstand": 3, "winkel": 45}
    return [("Schwarz", e()), ("Blau", e(farbe="#4a90d9")), ("Orange", e(farbe="#f08c2e")),
            ("Blaue Kontur", e(fuell="keine", kontur=True, kontur_farbe="#4a90d9", kontur_breite=1.25)), ("Gelb", e(farbe="#ffc61a")), ("Grau", e(farbe="#7f8790")),
            ("Blau mit Schatten", e(farbe="#2f6fb5", schatten=sch)), ("Gelbe Kontur", e(fuell="keine", kontur=True, kontur_farbe="#ffc61a", kontur_breite=1.25)),
            ("Hellblaue Kontur", e(fuell="keine", kontur=True, kontur_farbe="#8fb8ea", kontur_breite=1.0)), ("Dunkelgrau", e(farbe="#495057")),
            ("Schwarz mit Schatten", e(schatten=sch)), ("Schwarz mit blauer Kontur", e(kontur=True, kontur_farbe="#4a90d9", kontur_breite=1.0)),
            ("Blauer Verlauf", e(fuell="verlauf", farbe="", verlauf={"farbe1": "#5b9be0", "farbe2": "#1c4fa3", "winkel": 90}, schatten=sch)),
            ("Orange Kontur", e(fuell="keine", kontur=True, kontur_farbe="#f08c2e", kontur_breite=1.25)), ("Graue Kontur", e(fuell="keine", kontur=True, kontur_farbe="#868e96", kontur_breite=1.25))]


def wordart_icon(w: dict, groesse=(52, 40)):
    """Kachelbild einer WordArt-Formatvorlage."""
    from PySide6.QtGui import QFont, QIcon, QPixmap
    pm = QPixmap(*groesse); pm.fill(QColor("white"))
    p = QPainter(pm)
    f = QFont("Liberation Sans"); f.setPixelSize(int(groesse[1] * 0.7)); f.setBold(True)
    face = QColor(0, 0, 0, 0) if w.get("fuell") == "keine" else QColor((w.get("verlauf") or {}).get("farbe1") or w.get("farbe") or "#111417")
    kontur = (QColor(w["kontur_farbe"]), w.get("kontur_breite", 1.0) * PX, "einfach", "einfach") if w.get("kontur") else None
    fx = {k: v for k, v in w.items() if k in ("verlauf", "schatten", "reflektion", "leuchten", "d3")}
    vorschau_zeichnen(p, QRectF(0, 0, groesse[0], groesse[1] * 0.95), "A", f, fx, face, kontur)
    p.end()
    return QIcon(pm)
