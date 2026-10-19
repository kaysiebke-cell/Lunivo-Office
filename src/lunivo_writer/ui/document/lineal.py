"""Waagerechtes und senkrechtes Lineal über/neben der Seite.

Zeigt Millimeter (mit dem Zoom der Ansicht), die Seitenränder (abgedunkelt) und – waagerecht – Einzüge des
aktuellen Absatzes. Ränder und Einzüge lassen sich mit der Maus ziehen.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from lunivo_writer.models.page import PX_PER_MM, px_to_mm

HOEHE = 22
FANG = 5


class _Lineal(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.e = editor
        self._zieh = None
        self._wert = None
        self.setMouseTracking(True)
        editor.zoomChanged.connect(lambda *_: self._neu())
        editor.pageApplied.connect(self._neu)
        editor.cursorPositionChanged.connect(self.update)

    def _neu(self):
        self._groesse()
        self.update()

    def _groesse(self):
        raise NotImplementedError

    def px(self, mm: float) -> float:
        return mm * PX_PER_MM * self.e.zoom

    def farben(self):
        pal = self.palette()
        return (pal.color(self.backgroundRole()), pal.color(self.foregroundRole()), pal.color(pal.ColorRole.Highlight))


class LinealH(_Lineal):
    randGeaendert = Signal(str, float)            # "links"|"rechts", neuer Rand in mm
    einzugGeaendert = Signal(float, float, float)  # links, rechts, erste Zeile (mm)

    def _groesse(self):
        self.setFixedSize(self.e.width(), HOEHE)

    def _einzuege(self):
        bf = self.e.textCursor().blockFormat()
        return px_to_mm(bf.leftMargin()), px_to_mm(bf.rightMargin()), px_to_mm(bf.textIndent())

    def _marken(self):
        """Name → x-Position (Bildpunkte) der ziehbaren Marken."""
        pg = self.e.page
        l, r, f = self._einzuege()
        if self._zieh and self._wert is not None:
            n, w = self._zieh, self._wert
            if n == "links": pg = pg.copy(); pg.margin_left_mm = w
            if n == "rechts": pg = pg.copy(); pg.margin_right_mm = w
            if n == "einzug_links": l = w
            if n == "einzug_rechts": r = w
            if n == "einzug_erste": f = w
        x0 = 1 + self.px(pg.margin_left_mm)
        x1 = 1 + self.px(pg.width_mm - pg.margin_right_mm)
        return {"links": x0, "rechts": x1, "einzug_erste": x0 + self.px(l + f), "einzug_links": x0 + self.px(l),
                "einzug_rechts": x1 - self.px(r)}

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg, fg, ak = self.farben()
        p.fillRect(self.rect(), bg)
        m = self._marken()
        grau = QColor(fg); grau.setAlpha(40)
        p.fillRect(QRectF(0, 0, m["links"], HOEHE), grau)
        p.fillRect(QRectF(m["rechts"], 0, self.width() - m["rechts"], HOEHE), grau)
        p.setPen(QPen(fg, 1))
        f = p.font(); f.setPointSizeF(7); p.setFont(f)
        z = self.e.zoom
        schritt = 5 if z >= 0.6 else 10
        mm = 0
        pgb = self.e.page.width_mm
        while mm <= pgb:
            x = 1 + self.px(mm)
            if mm % 10 == 0:
                p.drawLine(QPointF(x, HOEHE - 9), QPointF(x, HOEHE - 1))
                if mm:
                    p.drawText(QRectF(x - 14, 1, 28, 11), Qt.AlignCenter, str(mm // 10))
            else:
                p.drawLine(QPointF(x, HOEHE - 5), QPointF(x, HOEHE - 1))
            mm += schritt
        p.setBrush(ak); p.setPen(Qt.NoPen)
        for n in ("einzug_erste", "einzug_links", "einzug_rechts"):
            x = m[n]
            if n == "einzug_erste":
                p.drawPolygon(QPolygonF([QPointF(x - 4, 1), QPointF(x + 4, 1), QPointF(x, 7)]))
            else:
                p.drawPolygon(QPolygonF([QPointF(x - 4, HOEHE - 1), QPointF(x + 4, HOEHE - 1), QPointF(x, HOEHE - 7)]))
        p.end()

    def _treffer(self, x, y):
        m = self._marken()
        if y < 9 and abs(x - m["einzug_erste"]) <= FANG:
            return "einzug_erste"
        if y > 11:
            for n in ("einzug_links", "einzug_rechts"):
                if abs(x - m[n]) <= FANG:
                    return n
        for n in ("links", "rechts"):
            if abs(x - m[n]) <= 2:
                return n
        return None

    def mouseMoveEvent(self, ev):
        if self._zieh:
            self._wert = self._mm(ev.position().x(), self._zieh)
            self.update()
            return
        self.setCursor(Qt.SizeHorCursor if self._treffer(ev.position().x(), ev.position().y()) else Qt.ArrowCursor)

    def _mm(self, x, name):
        pg = self.e.page
        mm = (x - 1) / (PX_PER_MM * self.e.zoom)
        l0 = pg.margin_left_mm
        r0 = pg.width_mm - pg.margin_right_mm
        if name == "links":
            return max(0.0, min(mm, r0 - 30))
        if name == "rechts":
            return max(0.0, min(pg.width_mm - mm, pg.width_mm - l0 - 30))
        if name == "einzug_links":
            return max(0.0, mm - l0)
        if name == "einzug_rechts":
            return max(0.0, r0 - mm)
        l, _r, _f = self._einzuege()
        return mm - l0 - l                  # erste Zeile relativ zum linken Einzug

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._zieh = self._treffer(ev.position().x(), ev.position().y())
            self._wert = None

    def mouseReleaseEvent(self, ev):
        n, w = self._zieh, self._wert
        self._zieh = self._wert = None
        if n and w is not None:
            if n in ("links", "rechts"):
                self.randGeaendert.emit(n, round(w, 1))
            else:
                l, r, f = self._einzuege()
                if n == "einzug_links": l = w
                if n == "einzug_rechts": r = w
                if n == "einzug_erste": f = w
                self.einzugGeaendert.emit(round(l, 1), round(r, 1), round(f, 1))
        self.update()


class LinealV(_Lineal):
    randGeaendert = Signal(str, float)            # "oben"|"unten"

    def _groesse(self):
        self.setFixedSize(HOEHE, max(self.e.height(), 10))

    def paintEvent(self, ev):
        p = QPainter(self)
        bg, fg, _ = self.farben()
        p.fillRect(self.rect(), bg)
        pg = self.e.page
        t = self.px(pg.margin_top_mm)
        if self._zieh == "oben" and self._wert is not None:
            t = self.px(self._wert)
        ph = self.px(pg.height_mm)
        grau = QColor(fg); grau.setAlpha(40)
        p.fillRect(QRectF(0, 0, HOEHE, t), grau)
        p.fillRect(QRectF(0, ph - self.px(pg.margin_bottom_mm), HOEHE, self.px(pg.margin_bottom_mm)), grau)
        p.setPen(QPen(fg, 1))
        f = p.font(); f.setPointSizeF(7); p.setFont(f)
        schritt = 5 if self.e.zoom >= 0.6 else 10
        mm = 0
        while self.px(mm) <= self.height():
            y = self.px(mm)
            if mm % 10 == 0:
                p.drawLine(QPointF(HOEHE - 9, y), QPointF(HOEHE - 1, y))
                if mm:
                    p.save(); p.translate(8, y); p.rotate(-90)
                    p.drawText(QRectF(-14, -6, 28, 12), Qt.AlignCenter, str(mm // 10)); p.restore()
            else:
                p.drawLine(QPointF(HOEHE - 5, y), QPointF(HOEHE - 1, y))
            mm += schritt
        p.end()

    def _treffer(self, y):
        pg = self.e.page
        if abs(y - self.px(pg.margin_top_mm)) <= 3:
            return "oben"
        return None

    def mouseMoveEvent(self, ev):
        if self._zieh:
            mm = ev.position().y() / (PX_PER_MM * self.e.zoom)
            self._wert = max(0.0, min(mm, self.e.page.height_mm - self.e.page.margin_bottom_mm - 40))
            self.update()
            return
        self.setCursor(Qt.SizeVerCursor if self._treffer(ev.position().y()) else Qt.ArrowCursor)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._zieh = self._treffer(ev.position().y())
            self._wert = None

    def mouseReleaseEvent(self, ev):
        n, w = self._zieh, self._wert
        self._zieh = self._wert = None
        if n and w is not None:
            self.randGeaendert.emit(n, round(w, 1))
        self.update()
