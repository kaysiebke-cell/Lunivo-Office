"""Reiter mit Bildchen über der Beschriftung (wie „Textfüllung und -kontur“ / „Effekte“ im WPS): zwei oder mehr Knöpfe oben, darunter die Seiten.

    r = IconReiter(); r.addTab(seite, icon, "TEXT"); r.setCurrentIndex(1)
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QStackedWidget, QToolButton, QVBoxLayout, QWidget


class IconReiter(QWidget):
    currentChanged = Signal(int)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(6)
        self._kopf = QHBoxLayout(); self._kopf.setContentsMargins(0, 0, 0, 0); self._kopf.setSpacing(0)
        v.addLayout(self._kopf)
        self._seiten = QStackedWidget(); v.addWidget(self._seiten, 1)
        self._gruppe = QButtonGroup(self); self._gruppe.setExclusive(True)
        self._gruppe.idClicked.connect(self.setCurrentIndex)

    def addTab(self, seite: QWidget, icon: QIcon, text: str) -> int:
        i = self._seiten.addWidget(seite)
        k = QToolButton(); k.setText(text); k.setIcon(icon); k.setIconSize(QSize(26, 26)); k.setCheckable(True)
        k.setToolButtonStyle(Qt.ToolButtonTextUnderIcon); k.setAutoRaise(True)
        k.setStyleSheet("QToolButton { border: none; border-bottom: 2px solid transparent; padding: 4px 14px; color: palette(mid); }"
                        "QToolButton:checked { color: palette(highlight); border-bottom: 2px solid palette(highlight); }")
        self._gruppe.addButton(k, i); self._kopf.addWidget(k)
        if i == 0:
            k.setChecked(True)
            self._kopf.addStretch(1) if False else None
        return i

    def setCurrentIndex(self, i: int) -> None:
        self._seiten.setCurrentIndex(i)
        b = self._gruppe.button(i)
        if b is not None:
            b.setChecked(True)
        self.currentChanged.emit(i)

    def currentIndex(self) -> int:
        return self._seiten.currentIndex()

    def currentWidget(self) -> QWidget:
        return self._seiten.currentWidget()

    def count(self) -> int:
        return self._seiten.count()

    def widget(self, i: int) -> QWidget:
        return self._seiten.widget(i)
