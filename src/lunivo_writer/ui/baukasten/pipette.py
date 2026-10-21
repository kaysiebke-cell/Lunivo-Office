"""Die Pipette: eine Farbe vom Bildschirm aufnehmen.

    c = farbe_vom_bildschirm(parent)      # QColor oder None (Esc, oder der Bildschirm lässt sich nicht aufnehmen)

Ein Bild des Bildschirms füllt ein Fenster ohne Rand; unter dem Mauszeiger zeigt eine Lupe die Farbe. Ein Klick nimmt sie auf.
"""
from __future__ import annotations

from PySide6.QtCore import QEventLoop, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class _Pipette(QWidget):
    fertig = Signal(object)

    def __init__(self, bild: QPixmap, geometrie: QRect):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self._bild = bild
        self._img = bild.toImage()
        self.setGeometry(geometrie)
        self.setCursor(Qt.CrossCursor); self.setMouseTracking(True)
        self._pos = QPoint(geometrie.width() // 2, geometrie.height() // 2)

    def _farbe_bei(self, p: QPoint) -> QColor:
        f = self._bild.devicePixelRatio()
        return QColor(self._img.pixel(int(p.x() * f), int(p.y() * f))) if self._img.rect().contains(int(p.x() * f), int(p.y() * f)) else QColor("#000000")

    def paintEvent(self, _e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._bild)
        c = self._farbe_bei(self._pos)
        r = QRect(self._pos.x() + 18, self._pos.y() + 18, 120, 44)                 # Anzeige neben dem Zeiger: Farbfeld und Hex-Wert
        p.setPen(QPen(QColor("#212529"), 1)); p.setBrush(QColor("#ffffff")); p.drawRect(r)
        p.setBrush(c); p.drawRect(QRect(r.left() + 6, r.top() + 6, 32, 32))
        p.setPen(QColor("#212529")); p.drawText(QRect(r.left() + 44, r.top(), 74, r.height()), Qt.AlignVCenter, c.name().upper())

    def mouseMoveEvent(self, e):
        self._pos = e.position().toPoint(); self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.fertig.emit(self._farbe_bei(e.position().toPoint())); self.close()
        else:
            self.fertig.emit(None); self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.fertig.emit(None); self.close()


def farbe_vom_bildschirm(parent=None) -> QColor | None:
    """Die Farbe unter dem nächsten Mausklick (blockiert, bis geklickt wird); None bei Esc oder wenn der Bildschirm nicht aufnehmbar ist."""
    schirm = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
    bild = schirm.grabWindow(0)
    if bild.isNull():
        return None
    w = _Pipette(bild, schirm.geometry())
    erg: list = []
    schleife = QEventLoop()
    w.fertig.connect(lambda c: (erg.append(c), schleife.quit()))
    w.show(); w.activateWindow(); w.setFocus()
    schleife.exec()
    return erg[0] if erg else None
