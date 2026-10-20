"""Zellenraster: wie bei WPS die Tabelle einfügen — mit der Maus über Zellen fahren, „3 × 4“ lesen, klicken."""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QLabel, QMenu, QVBoxLayout, QWidget, QWidgetAction


class _Gitter(QWidget):
    def __init__(self, raster: "ZellenRaster", zeilen: int, spalten: int, zelle: int = 20):
        super().__init__()
        self._r, self.zeilen, self.spalten, self.zelle = raster, zeilen, spalten, zelle
        self.an = (0, 0)                                  # (Zeilen, Spalten) unter der Maus; (0, 0) = keine
        self.setMouseTracking(True)
        self.setFixedSize(spalten * zelle + 1, zeilen * zelle + 1)

    def _zelle_bei(self, pos) -> tuple[int, int]:
        s, z = int(pos.x() // self.zelle) + 1, int(pos.y() // self.zelle) + 1
        return (z, s) if 1 <= z <= self.zeilen and 1 <= s <= self.spalten else (0, 0)

    def setze(self, z: int, s: int) -> None:
        self.an = (z, s)
        self._r._beschriften(z, s)
        self.update()

    def mouseMoveEvent(self, e):
        self.setze(*self._zelle_bei(e.position()))

    def leaveEvent(self, e):
        self.setze(0, 0)

    def mouseReleaseEvent(self, e):
        z, s = self._zelle_bei(e.position())
        if z:
            self._r.waehle(z, s)

    def paintEvent(self, e):
        p = QPainter(self)
        pal = self.palette()
        for z in range(self.zeilen):
            for s in range(self.spalten):
                r = QRectF(s * self.zelle + 1, z * self.zelle + 1, self.zelle - 2, self.zelle - 2)
                an = z < self.an[0] and s < self.an[1]
                p.setPen(QPen(pal.highlight().color() if an else pal.mid().color(), 1))
                p.setBrush(pal.highlight().color().lighter(170) if an else pal.base())
                p.drawRect(r)


class ZellenRaster(QMenu):
    """Meldet ``gewaehlt(zeilen, spalten)``. Darunter lassen sich mit ``fuss(...)`` weitere Einträge anhängen."""

    gewaehlt = Signal(int, int)

    def __init__(self, parent=None, zeilen: int = 8, spalten: int = 10, *, leer_text: str = "Tabelle einfügen"):
        super().__init__(parent)
        self._leer = leer_text
        wid = QWidget()
        v = QVBoxLayout(wid); v.setContentsMargins(8, 6, 8, 8); v.setSpacing(4)
        self.beschriftung = QLabel(leer_text)
        self.gitter = _Gitter(self, zeilen, spalten)
        v.addWidget(self.beschriftung); v.addWidget(self.gitter)
        a = QWidgetAction(self); a.setDefaultWidget(wid); self.addAction(a)

    def _beschriften(self, z: int, s: int) -> None:
        self.beschriftung.setText(f"{z} × {s} Tabelle" if z else self._leer)

    def waehle(self, zeilen: int, spalten: int) -> None:
        self.gewaehlt.emit(zeilen, spalten)
        self.close()

    def fuss(self, text: str, aktion) -> None:
        self.addSeparator()
        self.addAction(text, aktion)
