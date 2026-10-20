"""Kachel-Auswahl: ein Popup mit Bildchen im Raster und einem „Mehr …“-Fuß (Aufzählung, Vorlagen, Ränder, Deckblätter …)."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QMenu, QPushButton, QToolButton, QVBoxLayout, QWidget, QWidgetAction


def _symbol(bild, groesse: QSize) -> QIcon:
    """Aus QIcon, QPixmap oder einer Zeichenfunktion ``f(QPainter, QRectF)`` ein Symbol machen."""
    if bild is None:
        return QIcon()
    if isinstance(bild, QIcon):
        return bild
    if isinstance(bild, QPixmap):
        return QIcon(bild)
    pm = QPixmap(groesse); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    bild(p, QRectF(0, 0, groesse.width(), groesse.height()))
    p.end()
    return QIcon(pm)


class RasterAuswahl(QMenu):
    """Meldet den Schlüssel der gewählten Kachel."""

    gewaehlt = Signal(str)

    def __init__(self, parent=None, *, titel: str = "", spalten: int = 4, groesse: QSize = QSize(56, 56)):
        super().__init__(parent)
        self._spalten, self._groesse = spalten, groesse
        self._wid = QWidget()
        self._v = QVBoxLayout(self._wid)
        self._v.setContentsMargins(6, 6, 6, 6); self._v.setSpacing(4)
        if titel:
            t = QLabel(titel); t.setStyleSheet("color: palette(mid); font-size: 11px;")
            self._v.addWidget(t)
        self._gitter = QGridLayout(); self._gitter.setSpacing(4)
        self._v.addLayout(self._gitter)
        self._n = 0
        self.knoepfe: dict[str, QToolButton] = {}
        a = QWidgetAction(self); a.setDefaultWidget(self._wid); self.addAction(a)

    def kachel(self, schluessel: str, beschriftung: str = "", bild=None, *, aktuell: bool = False) -> QToolButton:
        b = QToolButton()
        b.setIcon(_symbol(bild, self._groesse)); b.setIconSize(self._groesse)
        b.setToolTip(beschriftung or schluessel); b.setCheckable(True); b.setChecked(aktuell)
        b.setFixedSize(self._groesse + QSize(10, 10))
        b.clicked.connect(lambda _c=False, k=schluessel: self._klick(k))
        self._gitter.addWidget(b, self._n // self._spalten, self._n % self._spalten)
        self._n += 1
        self.knoepfe[schluessel] = b
        return b

    def kacheln(self, eintraege, aktuell: str | None = None) -> None:
        """``eintraege``: Liste aus (schluessel, beschriftung, bild)."""
        for schl, text, bild in eintraege:
            self.kachel(schl, text, bild, aktuell=schl == aktuell)

    def fuss(self, text: str, aktion: Callable) -> QPushButton:
        """Zeile unter dem Raster, z. B. „Weitere Aufzählungszeichen …“."""
        b = QPushButton(text); b.setFlat(True); b.setStyleSheet("text-align: left; padding: 4px 6px;")
        b.clicked.connect(lambda: (self.close(), aktion()))
        self._v.addWidget(b)
        return b

    def _klick(self, schluessel: str) -> None:
        self.gewaehlt.emit(schluessel)
        self.close()
