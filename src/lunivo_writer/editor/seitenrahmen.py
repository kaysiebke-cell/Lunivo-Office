"""Der Rahmen um die Seite („Rahmen und Schattierung“ ▸ Seitenrand): Lage, Abstände, Kunstrahmen.

Ein Seitenrahmen ist ein Wörterbuch (``PageSettings.border``): ``farbe``, ``breite_pt``, ``art`` (Linienart), ``seiten`` („tblr“) und dazu

* ``abstand``: "oben,unten,links,rechts" in pt; fehlt es, gilt ``abstand_mm`` (ältere Dateien) rundherum
* ``messen``: "text" (vom Text aus nach außen) oder "seitenrand" (vom Blattrand nach innen); ohne Angabe: Seitenrand
* ``ausrichten``: Absatzrahmen und Tabellenränder am Seitenrand ausrichten; ``vordergrund`` (Vorgabe: an); ``kopf`` / ``fuss``: Kopf-/Fußzeile umgeben
* ``kunst``: Art des Rahmens aus ``KUNST`` (leer = Linie)
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF

from lunivo_writer.models.page import mm_to_px

from lunivo_writer.core.farben import Farbe
KUNST = (("", "(keine)"), ("stars", "Sterne"), ("hearts", "Herzen"), ("triangles", "Dreiecke"), ("gems", "Edelsteine"), ("zigZag", "Zickzack"))
KOPF_MM = 12.5                      # Abstand der Kopf- und Fußzeile vom Blattrand, soweit der Rahmen sie umgeben soll


def abstaende_pt(b: dict) -> tuple[float, float, float, float]:
    """(oben, unten, links, rechts) in pt."""
    try:
        o, u, l, r = (float(x) for x in str(b.get("abstand", "")).split(","))
        return o, u, l, r
    except ValueError:
        pt = b.get("abstand_mm", 8.0) / 25.4 * 72
        return pt, pt, pt, pt


def rechteck(b: dict, page, seite: QRectF) -> QRectF:
    """Das Rechteck des Rahmens in Bildpunkten, auf einer Seite mit dem Rechteck ``seite``."""
    o, u, l, r = (x * 96 / 72 for x in abstaende_pt(b))
    if b.get("messen", "seitenrand") == "text":
        ml, mt, mr, mb = (mm_to_px(m) for m in (page.margin_left_mm, page.margin_top_mm, page.margin_right_mm, page.margin_bottom_mm))
        text = seite.adjusted(ml, mt, -mr, -mb)
        oben = seite.top() + min(mt, mm_to_px(KOPF_MM)) if b.get("kopf") else text.top()
        unten = seite.bottom() - min(mb, mm_to_px(KOPF_MM)) if b.get("fuss") else text.bottom()
        return QRectF(text.left() - l, oben - o, text.width() + l + r, unten - oben + o + u)
    return seite.adjusted(l, o, -r, -u)


def _figur(art: str, mitte: QPointF, groesse: float) -> QPainterPath:
    pf = QPainterPath()
    r = groesse / 2
    if art == "stars":
        pt = [QPointF(mitte.x() + (r if i % 2 == 0 else r * 0.42) * math.sin(i * math.pi / 5), mitte.y() - (r if i % 2 == 0 else r * 0.42) * math.cos(i * math.pi / 5))
              for i in range(10)]
        pf.addPolygon(QPolygonF(pt + [pt[0]]))
    elif art == "hearts":
        pf.moveTo(mitte.x(), mitte.y() + r)
        pf.cubicTo(mitte.x() - r * 1.6, mitte.y() - r * 0.2, mitte.x() - r * 0.5, mitte.y() - r * 1.2, mitte.x(), mitte.y() - r * 0.35)
        pf.cubicTo(mitte.x() + r * 0.5, mitte.y() - r * 1.2, mitte.x() + r * 1.6, mitte.y() - r * 0.2, mitte.x(), mitte.y() + r)
    elif art == "triangles":
        pf.addPolygon(QPolygonF([QPointF(mitte.x(), mitte.y() - r), QPointF(mitte.x() + r, mitte.y() + r), QPointF(mitte.x() - r, mitte.y() + r), QPointF(mitte.x(), mitte.y() - r)]))
    else:                                                                          # Edelsteine: Rauten
        pf.addPolygon(QPolygonF([QPointF(mitte.x(), mitte.y() - r), QPointF(mitte.x() + r * 0.7, mitte.y()), QPointF(mitte.x(), mitte.y() + r),
                                 QPointF(mitte.x() - r * 0.7, mitte.y()), QPointF(mitte.x(), mitte.y() - r)]))
    return pf


def kunst_zeichnen(p: QPainter, rect: QRectF, art: str, breite_px: float, farbe: QColor) -> None:
    """Einen Kunstrahmen entlang der Kanten: Figuren in regelmäßigem Abstand (Zickzack als Linienzug)."""
    g = max(8.0, breite_px)
    p.save(); p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(farbe, 1)); p.setBrush(farbe)
    kanten = ((rect.topLeft(), rect.topRight()), (rect.topRight(), rect.bottomRight()), (rect.bottomRight(), rect.bottomLeft()), (rect.bottomLeft(), rect.topLeft()))
    for a, z in kanten:
        laenge = math.hypot(z.x() - a.x(), z.y() - a.y())
        n = max(2, int(laenge // (g * 1.5)))
        if art == "zigZag":
            pf = QPainterPath(a)
            dx, dy = (z.x() - a.x()) / n, (z.y() - a.y()) / n
            nx, ny = -dy / max(1e-6, math.hypot(dx, dy)) * g / 2, dx / max(1e-6, math.hypot(dx, dy)) * g / 2
            for i in range(1, n + 1):
                s = 1 if i % 2 else -1
                pf.lineTo(a.x() + dx * (i - 0.5) + nx * s, a.y() + dy * (i - 0.5) + ny * s)
                pf.lineTo(a.x() + dx * i, a.y() + dy * i)
            p.setBrush(Qt.NoBrush); p.setPen(QPen(farbe, max(1.0, g / 6))); p.drawPath(pf); p.setBrush(farbe)
            continue
        for i in range(n):
            t = (i + 0.5) / n
            p.drawPath(_figur(art, QPointF(a.x() + (z.x() - a.x()) * t, a.y() + (z.y() - a.y()) * t), g))
    p.restore()


def zeichnen(p: QPainter, b: dict, page, seite: QRectF) -> None:
    """Den Seitenrahmen auf eine Seite zeichnen (Linie in ihrer Art oder Kunstrahmen)."""
    from lunivo_writer.editor.linie import Linie
    rect = rechteck(b, page, seite)
    breite = float(b.get("breite_pt", 1.0))
    if b.get("kunst"):
        kunst_zeichnen(p, rect, b["kunst"], breite * 96 / 72, QColor(b.get("farbe", Farbe.SCHWARZ)))
        return
    Linie(b.get("farbe", Farbe.SCHWARZ), breite, b.get("art", "einfach"), b.get("seiten", "tblr")).rahmen_zeichnen(p, rect, 96 / 72)
