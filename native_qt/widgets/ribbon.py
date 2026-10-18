"""Ribbon aus nativen Qt-Widgets: Reiter → Gruppen → Knöpfe."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)


class RibbonGroup(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setFrameShape(QFrame.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 2, 6, 0)
        outer.setSpacing(1)
        self.rows = QVBoxLayout()
        self.rows.setSpacing(2)
        outer.addLayout(self.rows, 1)
        lab = QLabel(title)
        lab.setAlignment(Qt.AlignHCenter)
        lab.setStyleSheet("font-size: 9pt; color: palette(mid);")
        outer.addWidget(lab)
        self._row: QHBoxLayout | None = None

    def row(self) -> QHBoxLayout:
        r = QHBoxLayout()
        r.setSpacing(2)
        r.setAlignment(Qt.AlignLeft)
        self.rows.addLayout(r)
        self._row = r
        return r

    def add_widget(self, w: QWidget, new_row: bool = False) -> QWidget:
        if self._row is None or new_row:
            self.row()
        self._row.addWidget(w)
        return w

    def add_action(self, action: QAction, big: bool = False, new_row: bool = False,
                   menu: QMenu | None = None) -> QToolButton:
        b = QToolButton()
        b.setDefaultAction(action)
        b.setAutoRaise(True)
        if big:
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setMinimumWidth(max(56, b.fontMetrics().horizontalAdvance(action.text().replace("&", "")) + 18))
        else:
            b.setToolButtonStyle(Qt.ToolButtonTextOnly if action.icon().isNull() else Qt.ToolButtonIconOnly)
            b.setMinimumWidth(max(26, b.fontMetrics().horizontalAdvance(action.text().replace("&", "")) + 18))
        if menu is not None:
            b.setMenu(menu)
            b.setPopupMode(QToolButton.MenuButtonPopup if big else QToolButton.InstantPopup)
        self.add_widget(b, new_row)
        return b


class Ribbon(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setDocumentMode(True)
        self.setFixedHeight(118)
        self._tabs: dict[str, QHBoxLayout] = {}

    def add_tab(self, name: str) -> "RibbonTab":
        page = QWidget()
        lay = QHBoxLayout(page)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignLeft)
        self.addTab(page, name)
        return RibbonTab(lay)


class RibbonTab:
    def __init__(self, lay: QHBoxLayout):
        self.lay = lay

    def group(self, title: str) -> RibbonGroup:
        if self.lay.count():
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setFrameShadow(QFrame.Sunken)
            self.lay.addWidget(sep)
        g = RibbonGroup(title)
        self.lay.addWidget(g)
        return g
