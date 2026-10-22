"""Rahmen eines Feldes in einer Seitenleiste: Titel, davor/dahinter Knöpfe, ein Menü (⋯ oder ⚙) und ✕ zum Schließen; darunter der Inhalt.

Dieselbe Hülle für alle Felder links (Suchen und ersetzen, Kommentare, Überschriften …): gleiche Kopfzeile, gleiche Abstände, gleiche Bedienung."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QToolButton, QVBoxLayout, QWidget


def _knopf(text: str, tipp: str) -> QToolButton:
    b = QToolButton(); b.setText(text); b.setToolTip(tipp); b.setAccessibleName(tipp); b.setAutoRaise(True); b.setCursor(Qt.PointingHandCursor)
    b.setFixedSize(30, 30)
    return b


class PanelRahmen(QWidget):
    schliessen = Signal()

    def __init__(self, titel: str, menue_zeichen: str = "", menue: QMenu | None = None, knoepfe: tuple = ()):
        """``knoepfe``: Folge von (Zeichen, Tooltip, Funktion) — stehen vor dem Menü."""
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        kopf = QWidget(); h = QHBoxLayout(kopf); h.setContentsMargins(14, 8, 8, 8); h.setSpacing(2)
        self.titel = QLabel(titel); f = self.titel.font(); f.setBold(True); f.setPointSizeF(f.pointSizeF() + 1); self.titel.setFont(f)
        h.addWidget(self.titel, 1)
        self.knoepfe = []
        for zeichen, tipp, fn in knoepfe:
            b = _knopf(zeichen, tipp); b.clicked.connect(lambda _=False, fn=fn: fn()); h.addWidget(b); self.knoepfe.append(b)
        self.menue_knopf = None
        if menue is not None:
            self.menue_knopf = _knopf(menue_zeichen or "⋯", "Weitere Einstellungen")
            self.menue_knopf.setPopupMode(QToolButton.InstantPopup); self.menue_knopf.setMenu(menue)
            h.addWidget(self.menue_knopf)
        zu = _knopf("✕", "Schließen"); zu.clicked.connect(self.schliessen.emit); h.addWidget(zu)
        v.addWidget(kopf)
        linie = QFrame(); linie.setFrameShape(QFrame.HLine); linie.setFrameShadow(QFrame.Plain); linie.setStyleSheet("color: palette(midlight);")
        v.addWidget(linie)
        self.inhalt = QVBoxLayout(); self.inhalt.setContentsMargins(14, 10, 14, 10); self.inhalt.setSpacing(8)
        v.addLayout(self.inhalt, 1)
