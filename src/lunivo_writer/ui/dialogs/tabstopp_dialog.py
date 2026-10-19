"""Dialog „Tabstopps“ für die markierten Absätze: Position (mm), Ausrichtung; hinzufügen, entfernen, alle löschen."""
from __future__ import annotations

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QListWidget, QPushButton, QVBoxLayout,
)

from lunivo_writer.models.page import mm_to_px, px_to_mm

ARTEN = [("Links", QTextOption.LeftTab), ("Zentriert", QTextOption.CenterTab), ("Rechts", QTextOption.RightTab),
         ("Dezimal", QTextOption.DelimiterTab)]


def _text(mm: float, art) -> str:
    name = next(n for n, a in ARTEN if a == art)
    return f"{mm:.1f} mm  ·  {name}".replace(".", ",")


class TabstoppDialog(QDialog):
    def __init__(self, parent, stopps):
        super().__init__(parent)
        self.setWindowTitle("Tabstopps")
        self._stopps: list[tuple[float, object]] = sorted(((round(px_to_mm(t.position), 1), t.type) for t in stopps),
                                                          key=lambda x: x[0])
        v = QVBoxLayout(self)
        f = QFormLayout()
        self.pos = QDoubleSpinBox(); self.pos.setRange(0, 1000); self.pos.setSuffix(" mm"); self.pos.setDecimals(1)
        self.art = QComboBox(); self.art.addItems([n for n, _a in ARTEN])
        f.addRow("Position:", self.pos)
        f.addRow("Ausrichtung:", self.art)
        v.addLayout(f)
        self.liste = QListWidget()
        v.addWidget(self.liste, 1)
        h = QHBoxLayout()
        for text, fn in (("Festlegen", self.festlegen), ("Löschen", self.loeschen), ("Alle löschen", self.alle)):
            b = QPushButton(text); b.clicked.connect(fn); h.addWidget(b)
        v.addLayout(h)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        v.addWidget(bb)
        self.liste.currentRowChanged.connect(self._zeile)
        self._fuellen()

    def _fuellen(self):
        self.liste.clear()
        self.liste.addItems([_text(m, a) for m, a in self._stopps])

    def _zeile(self, i):
        if 0 <= i < len(self._stopps):
            m, a = self._stopps[i]
            self.pos.setValue(m)
            self.art.setCurrentIndex(next(k for k, (_n, x) in enumerate(ARTEN) if x == a))

    def festlegen(self):
        m = round(self.pos.value(), 1)
        self._stopps = [s for s in self._stopps if s[0] != m] + [(m, ARTEN[self.art.currentIndex()][1])]
        self._stopps.sort(key=lambda x: x[0])
        self._fuellen()

    def loeschen(self):
        i = self.liste.currentRow()
        if 0 <= i < len(self._stopps):
            del self._stopps[i]
            self._fuellen()

    def alle(self):
        self._stopps = []
        self._fuellen()

    def ergebnis(self):
        return [QTextOption.Tab(mm_to_px(m), a) for m, a in self._stopps]
