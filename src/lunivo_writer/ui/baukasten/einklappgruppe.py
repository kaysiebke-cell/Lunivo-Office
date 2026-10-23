"""Eingeklappte Gruppe („Weitere Einstellungen“): ein Knopf mit Pfeil, darunter der Inhalt, der erst auf Wunsch aufgeht.

Bedienbar mit Tab, Leertaste und Eingabetaste; ein Bildschirmleser meldet Namen und Zustand (ein-/ausgeklappt)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QWidget


class EinklappGruppe(QWidget):
    """Knopf plus Inhalt. Der Inhalt kommt in ``innen`` (ein ``QVBoxLayout``)."""

    def __init__(self, titel: str = "Weitere Einstellungen", parent: QWidget | None = None):
        super().__init__(parent)
        self.titel = titel
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 4, 0, 4)
        v.setSpacing(6)
        self.knopf = QToolButton()
        self.knopf.setCheckable(True)
        self.knopf.setAutoRaise(True)
        self.knopf.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.knopf.setText(titel)
        self.knopf.setMinimumHeight(32)
        self.knopf.setCursor(Qt.PointingHandCursor)
        self.knopf.setProperty("optName", titel)
        v.addWidget(self.knopf, 0, Qt.AlignLeft)
        self.inhalt = QWidget()
        self.innen = QVBoxLayout(self.inhalt)
        self.innen.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.inhalt)
        self.knopf.toggled.connect(self._zeigen)
        self._zeigen(False)

    def _zeigen(self, offen: bool) -> None:
        self.inhalt.setVisible(offen)
        self.knopf.setArrowType(Qt.DownArrow if offen else Qt.RightArrow)
        self.knopf.setAccessibleName(f"{self.titel}, {'ausgeklappt' if offen else 'eingeklappt'}")

    def ausklappen(self, offen: bool = True) -> None:
        self.knopf.setChecked(offen)

    def ist_offen(self) -> bool:
        return self.knopf.isChecked()
