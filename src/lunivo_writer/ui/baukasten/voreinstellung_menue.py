"""Auswahl von Voreinstellungen als Popup mit Bildchen in Abschnitten (Schatten: Kein, Außen, Innen, Perspektive; Leuchten; Spiegelung;
Material; Linien …).

    m = VoreinstellungMenue(parent, keine=("Kein Schatten", icon_oder_None))
    m.abschnitt("Außen", [("aussen1", icon, "Unten rechts"), …], spalten=3)
    m.gewaehlt.connect(lambda schluessel: …)         # "" = die Kein-Zeile
    m.exec(position)

Das Popup merkt nichts: es meldet nur den Schlüssel des gewählten Bildchens; wer es aufruft, setzt den Wert.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QGridLayout, QLabel, QMenu, QToolButton, QVBoxLayout, QWidget, QWidgetAction


class VoreinstellungMenue(QMenu):
    gewaehlt = Signal(str)

    def __init__(self, parent=None, *, keine: tuple[str, QIcon | None] | None = ("Keine", None), kachel: QSize = QSize(52, 40)):
        super().__init__(parent)
        self._kachel = kachel
        self._koerper = QWidget(); self._v = QVBoxLayout(self._koerper); self._v.setContentsMargins(6, 6, 6, 6); self._v.setSpacing(4)
        a = QWidgetAction(self); a.setDefaultWidget(self._koerper); self.addAction(a)
        self.aktuell: str | None = None
        if keine is not None:
            self._kopf(keine[0])
            if keine[1] is not None:
                self._gitter([("", keine[1], keine[0])], 1)

    def _kopf(self, text: str) -> None:
        l = QLabel(text); l.setStyleSheet("font-weight: 600; padding: 3px 2px; color: palette(text);")
        self._v.addWidget(l)

    def _gitter(self, eintraege: list[tuple[str, QIcon, str]], spalten: int) -> None:
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 0, 0, 0); g.setSpacing(3)
        for i, (schl, icon, tipp) in enumerate(eintraege):
            k = QToolButton(); k.setAutoRaise(True); k.setIcon(icon); k.setIconSize(self._kachel); k.setToolTip(tipp)
            k.setFixedSize(self._kachel + QSize(10, 8)); k.setCheckable(True); k.setChecked(schl == self.aktuell)
            k.setStyleSheet("QToolButton { border: 1px solid transparent; border-radius: 3px; }"
                            "QToolButton:hover { border-color: palette(highlight); } QToolButton:checked { border-color: palette(highlight); background: palette(midlight); }")
            k.clicked.connect(lambda _=False, s=schl: self._waehle(s))
            g.addWidget(k, i // spalten, i % spalten)
        self._v.addWidget(w)

    def abschnitt(self, titel: str, eintraege: list[tuple[str, QIcon, str]], spalten: int = 3) -> None:
        self._kopf(titel)
        self._gitter(eintraege, spalten)

    def _waehle(self, schluessel: str) -> None:
        self.gewaehlt.emit(schluessel)
        self.close()
