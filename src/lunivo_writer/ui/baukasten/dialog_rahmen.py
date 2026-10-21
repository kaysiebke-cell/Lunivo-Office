"""Grundgerüst für kleine Dialoge: Formular, optionale Vorschau, OK/Abbrechen und Zusatzknöpfe wie „Entfernen“."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPalette, QPen
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget


def fussleiste(dialog: QDialog, layout, *links: QPushButton, bei_ok: Callable | None = None, ok_text: str = "OK",
               abbrechen_text: str = "Abbrechen", nur_ok: bool = False) -> QPushButton:
    """Knopfzeile unten im Dialog: links die Zusatzknöpfe, rechts „Abbrechen“ und „OK“. Gibt den OK-Knopf zurück
    (``bei_ok`` ersetzt ``accept``, z. B. zum Prüfen vor dem Schließen)."""
    zu = QHBoxLayout(); zu.setSpacing(10)
    for k in links:
        k.setMinimumHeight(34)
        zu.addWidget(k)
    zu.addStretch(1)
    ab, ok = QPushButton(abbrechen_text), QPushButton(ok_text); ok.setDefault(True)
    ab.setIcon(_symbol("kreuz")); ok.setIcon(_symbol("haken"))
    for k in (ab, ok): # wie in der Vorlage: breite Knöpfe mit Symbol
        k.setMinimumSize(100, 34); k.setIconSize(QSize(16, 16))
    ab.clicked.connect(dialog.reject); ok.clicked.connect(bei_ok or dialog.accept)
    if not nur_ok:
        zu.addWidget(ab)
    zu.addWidget(ok)
    layout.addLayout(zu)
    return ok


def _symbol(art: str):
    """Das Symbol auf „Abbrechen“ (Kreuz) und „OK“ (Haken)."""
    from PySide6.QtGui import QColor, QIcon, QPixmap
    pm = QPixmap(16, 16); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    pal = QApplication.palette().color(QPalette.ButtonText)
    p.setPen(QPen(pal, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if art == "kreuz":
        p.drawLine(3, 3, 13, 13); p.drawLine(13, 3, 3, 13)
    else:
        p.drawLine(2, 9, 6, 13); p.drawLine(6, 13, 14, 3)
    p.end()
    return QIcon(pm)


class VorschauFlaeche(QWidget):
    """Weißes Blatt, auf das der Dialog mit ``zeichne(painter, rect)`` seine Vorschau malt."""

    def __init__(self, zeichne: Callable[[QPainter, QRect], None], hoehe: int = 120, flaeche: bool = True):
        """``flaeche=False``: kein weißes Feld mit Rand; ``zeichne`` malt direkt auf den Fensterhintergrund (z. B. ein einzelnes Blatt)."""
        super().__init__()
        self._zeichne = zeichne
        self._flaeche = flaeche
        self.setMinimumHeight(hoehe)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._flaeche:
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
