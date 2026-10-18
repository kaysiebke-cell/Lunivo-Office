"""Die Fläche neben der Seite, auf der die Sprechblasen des Editors stehen (Kommentare, verfolgte Änderungen)."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from ..editor import sprechblasen as SB


class BlasenFlaeche(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.ed = editor
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)
        self._treffer: list[tuple[QRectF, SB.Blase]] = []

    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        hell = self.ed.palette().window().color().lightness() > 128
        p.fillRect(self.rect(), QColor("#f1f3f5" if hell else "#2b2f33"))
        self._treffer = []
        layout = self.ed.blasen_layout(self.width())
        if not layout:
            p.end()
            return
        font = QFont(self.ed.font())
        font.setPixelSize(max(7, int(11 * self.ed.zoom)))
        rechts = self.ed.blasen_rand() == "Rechts"
        for bl, r, y_text in layout:
            if r.bottom() < e.rect().top() - 4 or r.top() > e.rect().bottom() + 4:
                self._treffer.append((r, bl))
                continue
            if self.ed.blasen_linien():
                SB.verbindung(p, bl, 0 if rechts else self.width(), y_text, r, rechts)
            SB.zeichnen(p, bl, r, font)
            self._treffer.append((r, bl))
        p.end()

    def _blase_bei(self, pos: QPointF):
        for r, bl in self._treffer:
            if r.contains(pos):
                return bl
        return None

    def mousePressEvent(self, e) -> None:
        bl = self._blase_bei(e.position())
        if bl is not None:
            self.ed.select_range(bl.von, bl.bis)
            self.ed.setFocus()

    def mouseDoubleClickEvent(self, e) -> None:
        bl = self._blase_bei(e.position())
        if bl is not None and bl.kid is not None:
            self.ed.kommentar_bearbeiten(bl.kid)
