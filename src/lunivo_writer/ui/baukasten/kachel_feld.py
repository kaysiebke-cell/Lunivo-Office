"""Beschriftete Kacheln zum Anklicken, immer genau eine gewählt (zum Beispiel die Umbruchart eines Bildes).

    k = KachelFeld(spalten=4, groesse=QSize(44, 44))
    k.hinzu("quadrat", "Quadrat", zeichner)          # zeichner: f(QPainter, QRectF), QIcon oder QPixmap
    k.gewaehlt.connect(lambda schluessel: ...)
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QGridLayout, QToolButton, QWidget

from lunivo_writer.ui.baukasten.raster_auswahl import _symbol


class KachelFeld(QWidget):
    gewaehlt = Signal(str)

    def __init__(self, parent=None, *, spalten: int = 4, groesse: QSize = QSize(44, 44), mit_text: bool = True):
        super().__init__(parent)
        self._spalten, self._groesse, self._text = spalten, groesse, mit_text
        self._gitter = QGridLayout(self); self._gitter.setContentsMargins(0, 0, 0, 0); self._gitter.setSpacing(4)
        self.knoepfe: dict[str, QToolButton] = {}
        self._aktuell: str | None = None

    def hinzu(self, schluessel: str, text: str, bild=None) -> QToolButton:
        b = QToolButton(); b.setCheckable(True); b.setAutoRaise(True); b.setFocusPolicy(Qt.NoFocus)
        b.setIcon(_symbol(bild, self._groesse) if bild is not None else QIcon()); b.setIconSize(self._groesse)
        b.setToolTip(text)
        if self._text:
            b.setText(text); b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.clicked.connect(lambda _c=False, k=schluessel: self.setze(k, True))
        n = len(self.knoepfe)
        self._gitter.addWidget(b, n // self._spalten, n % self._spalten)
        self.knoepfe[schluessel] = b
        return b

    def setze(self, schluessel: str | None, melden: bool = False) -> None:
        self._aktuell = schluessel
        for k, b in self.knoepfe.items():
            b.setChecked(k == schluessel)
        if melden and schluessel is not None:
            self.gewaehlt.emit(schluessel)

    def aktuell(self) -> str | None:
        return self._aktuell
