"""Gemeinsame Werte der Bausteine."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject


class _QuickInfo(QObject):
    """Schluckt die Hinweistexte (QuickInfo) an Knöpfen und Feldern, wenn sie ausgeschaltet sind (Optionen ▸ Ansicht)."""

    def __init__(self):
        super().__init__()
        self.an = True

    def eventFilter(self, obj, ev):
        return (not self.an) and ev.type() == QEvent.ToolTip
