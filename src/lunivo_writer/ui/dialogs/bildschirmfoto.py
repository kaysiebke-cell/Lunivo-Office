"""Bildschirmfoto: ganzer Bildschirm oder aufgezogener Bereich."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget


from lunivo_writer.core.farben import Farbe
class BereichWahl(QWidget):
    """Vollbild mit eingefrorenem Bildschirm; mit der Maus einen Bereich aufziehen (Esc bricht ab)."""
    fertig = Signal(object)          # QPixmap oder None

    def __init__(self, bild: QPixmap):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.bild = bild
        self.a = self.b = None
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(QApplication.primaryScreen().geometry())

    def paintEvent(self, ev):
        p = QPainter(self)
        p.drawPixmap(self.rect(), self.bild)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        if self.a and self.b:
            r = QRect(self.a, self.b).normalized()
            p.drawPixmap(r, self.bild, self._quelle(r))
            p.setPen(QPen(QColor(Farbe.AKZENT_DUNKEL), 2)); p.drawRect(r)
        p.end()

    def _quelle(self, r: QRect) -> QRect:
        fx = self.bild.width() / max(1, self.width()); fy = self.bild.height() / max(1, self.height())
        return QRect(int(r.x() * fx), int(r.y() * fy), int(r.width() * fx), int(r.height() * fy))

    def mousePressEvent(self, e):
        self.a = self.b = e.position().toPoint(); self.update()

    def mouseMoveEvent(self, e):
        if self.a:
            self.b = e.position().toPoint(); self.update()

    def mouseReleaseEvent(self, e):
        if self.a:
            r = QRect(self.a, e.position().toPoint()).normalized()
            self.hide()
            self.fertig.emit(self.bild.copy(self._quelle(r)) if r.width() > 4 and r.height() > 4 else None)
            self.deleteLater()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide(); self.fertig.emit(None); self.deleteLater()
