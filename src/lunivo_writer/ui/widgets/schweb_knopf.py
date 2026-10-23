"""Ein runder Knopf, der unten rechts über dem Blatt schwebt (wie der KI-Chat-Knopf in ONLYOFFICE)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QSize
from PySide6.QtWidgets import QToolButton

from lunivo_writer.ui.widgets import icons


from lunivo_writer.core.farben import Farbe
class SchwebKnopf(QToolButton):
    RAND = 16

    def __init__(self, editor, symbol: str, tipp: str, aktion):
        super().__init__(editor)
        self.editor = editor
        icons.setze(self, symbol, 26); self.setIconSize(QSize(26, 26)); self.setToolTip(tipp); self.setAccessibleName(tipp)
        self.setFixedSize(48, 48)
        self.setCursor(self.cursor())
        self.setStyleSheet(('QToolButton { background: palette(button); border: 1px solid palette(mid); border-radius: 8px; }QToolButton:hover { background: palette(alternate-base); }QToolButton:focus { border: 2px solid ' + Farbe.AKZENT + '; }'))
        self.clicked.connect(lambda: aktion())
        editor.installEventFilter(self)
        self.platzieren()

    def platzieren(self) -> None:
        r = self.editor.rect()                                   # das Blatt-Fenster (der Reiter des Dokuments), nicht das lange Blatt
        bar = self.editor.verticalScrollBar().width() if self.editor.verticalScrollBar().isVisible() else 0
        unten = self.editor.horizontalScrollBar().height() if self.editor.horizontalScrollBar().isVisible() else 0
        self.move(r.width() - self.width() - self.RAND - bar, r.height() - self.height() - self.RAND - unten)
        self.raise_()

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        if e.type() in (QEvent.Resize, QEvent.Show):
            self.platzieren()
        return False
