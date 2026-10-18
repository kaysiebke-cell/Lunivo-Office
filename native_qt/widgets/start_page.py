"""Startseite: neues Dokument, Öffnen, zuletzt bearbeitete Dokumente."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)


class StartPage(QWidget):
    newRequested = Signal()
    openRequested = Signal()
    openPath = Signal(str)

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(48, 32, 48, 32)
        title = QLabel("Lunivo Writer")
        title.setStyleSheet("font-size: 26pt; font-weight: bold;")
        sub = QLabel("Was geschrieben wird, bleibt auf diesem Rechner.")
        sub.setStyleSheet("color: palette(mid);")
        lay.addWidget(title); lay.addWidget(sub)
        row = QHBoxLayout()
        b1 = QPushButton("Neues leeres Dokument"); b1.clicked.connect(self.newRequested)
        b2 = QPushButton("Dokument öffnen …"); b2.clicked.connect(self.openRequested)
        for b in (b1, b2):
            b.setMinimumHeight(44); row.addWidget(b)
        row.addStretch(1)
        lay.addSpacing(16); lay.addLayout(row); lay.addSpacing(20)
        lay.addWidget(QLabel("Zuletzt bearbeitet"))
        self.list = QListWidget()
        self.list.itemActivated.connect(lambda it: self.openPath.emit(it.data(Qt.UserRole)))
        lay.addWidget(self.list, 1)
        self.empty = QLabel("Noch keine Dokumente geöffnet.")
        self.empty.setStyleSheet("color: palette(mid);")
        lay.addWidget(self.empty)

    def set_recent(self, paths: list[str]) -> None:
        self.list.clear()
        for p in paths:
            it = QListWidgetItem(f"{os.path.basename(p)}\n{os.path.dirname(p)}")
            it.setData(Qt.UserRole, p)
            self.list.addItem(it)
        self.empty.setVisible(not paths)
