"""Grundgerüst für kleine Dialoge: Formular, optionale Vorschau, OK/Abbrechen und Zusatzknöpfe wie „Entfernen“."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QPushButton, QVBoxLayout, QWidget


class VorschauFlaeche(QWidget):
    """Weißes Blatt, auf das der Dialog mit ``zeichne(painter, rect)`` seine Vorschau malt."""

    def __init__(self, zeichne: Callable[[QPainter, QRect], None], hoehe: int = 120):
        super().__init__()
        self._zeichne = zeichne
        self.setMinimumHeight(hoehe)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), Qt.white)
        p.setPen(self.palette().mid().color()); p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        self._zeichne(p, self.rect().adjusted(8, 8, -8, -8))


class DialogRahmen(QDialog):
    """Unterklassen füllen ``self.form`` (``zeile(...)``) und liefern ``ergebnis()``. Wer sich ändert, ruft ``aktualisieren()``."""

    def __init__(self, parent=None, titel: str = "", vorschau: Callable[[QPainter, QRect], None] | None = None):
        super().__init__(parent)
        self.setWindowTitle(titel)
        v = QVBoxLayout(self)
        self.form = QFormLayout()
        v.addLayout(self.form)
        self.vorschau = VorschauFlaeche(vorschau) if vorschau else None
        if self.vorschau:
            v.addWidget(self.vorschau)
        self.knoepfe = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.knoepfe.accepted.connect(self.accept)
        self.knoepfe.rejected.connect(self.reject)
        v.addWidget(self.knoepfe)

    def zeile(self, beschriftung: str, widget) -> None:
        self.form.addRow(beschriftung, widget)

    def zusatzknopf(self, text: str, aktion: Callable | None = None, *, schliesst: bool = True) -> QPushButton:
        """Knopf neben OK/Abbrechen (z. B. „Entfernen“); ``schliesst`` beendet den Dialog mit OK."""
        k = self.knoepfe.addButton(text, QDialogButtonBox.DestructiveRole)
        def klick():
            if aktion:
                aktion()
            if schliesst:
                self.accept()
        k.clicked.connect(klick)
        return k

    def aktualisieren(self, *_) -> None:
        if self.vorschau:
            self.vorschau.update()

    def ergebnis(self):
        raise NotImplementedError
