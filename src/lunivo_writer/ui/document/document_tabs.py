"""Dokumentreiter ganz oben (mit „+“) und der Stapel der Dokumente darunter."""
from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QTabBar, QToolButton, QWidget


class DocTabs(QObject):
    """Wie ein QTabWidget, nur dass Reiterleiste und Inhalt getrennt eingebaut werden."""
    currentChanged = Signal(int)
    tabCloseRequested = Signal(int)
    newRequested = Signal()
    kontextGewuenscht = Signal(int, object)      # (Reiter, globale Position)

    def __init__(self):
        super().__init__()
        self.bar = QTabBar()
        self.bar.setObjectName("dokReiter")
        self.bar.setTabsClosable(True)
        self.bar.setMovable(True)
        self.bar.setExpanding(False)
        self.bar.setDocumentMode(True)
        self.bar.setDrawBase(False)
        self.stack = QStackedWidget()
        self.leiste = QWidget()
        self.leiste.setObjectName("dokLeiste")
        h = QHBoxLayout(self.leiste)
        h.setContentsMargins(6, 3, 6, 0)
        h.setSpacing(2)
        h.addWidget(self.bar)
        plus = QToolButton()
        plus.setText("+")
        plus.setAutoRaise(True)
        plus.setToolTip("Neues Dokument (Strg+N)")
        plus.clicked.connect(self.newRequested)
        h.addWidget(plus)
        h.addStretch(1)
        self._w: list[QWidget] = []
        self.bar.currentChanged.connect(self._bar_changed)
        self.bar.tabCloseRequested.connect(self.tabCloseRequested)
        self.bar.tabMoved.connect(self._moved)
        self.bar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bar.customContextMenuRequested.connect(
            lambda p: self.kontextGewuenscht.emit(self.bar.tabAt(p), self.bar.mapToGlobal(p)))

    def _moved(self, von, nach):
        self._w.insert(nach, self._w.pop(von))

    def _bar_changed(self, i):
        if 0 <= i < len(self._w):
            self.stack.setCurrentWidget(self._w[i])
        self.currentChanged.emit(i)

    def addTab(self, w: QWidget, title: str) -> int:
        self._w.append(w)
        self.stack.addWidget(w)
        return self.bar.addTab(title)

    def count(self): return len(self._w)
    def widget(self, i): return self._w[i] if 0 <= i < len(self._w) else None
    def currentIndex(self): return self.bar.currentIndex()
    def currentWidget(self): return self.widget(self.bar.currentIndex())
    def setCurrentIndex(self, i): self.bar.setCurrentIndex(i)
    def setCurrentWidget(self, w): self.bar.setCurrentIndex(self._w.index(w))
    def setTabText(self, i, t): self.bar.setTabText(i, t)
    def tabText(self, i): return self.bar.tabText(i)
    def setTabToolTip(self, i, t): self.bar.setTabToolTip(i, t)

    def removeTab(self, i: int) -> None:
        w = self._w.pop(i)
        self.bar.removeTab(i)
        self.stack.removeWidget(w)
