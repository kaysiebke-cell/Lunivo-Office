"""Lesehilfe: Papierton, Buchstaben- und Wortabstand — wirkt nur auf die Anzeige, nicht auf das gespeicherte Dokument."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QVBoxLayout

PAPIERTOENE = {"Weiß": "#ffffff", "Creme": "#fbf4e2", "Gelblich": "#fff7cc", "Hellblau": "#e6f0fa",
               "Hellgrün": "#e8f5e9", "Hellgrau": "#eceff1"}


class LesehilfeDialog(QDialog):
    def __init__(self, fenster):
        super().__init__(fenster)
        self.setWindowTitle("Lesehilfe")
        self.w = fenster
        s = fenster.settings
        self.papier = QComboBox(); self.papier.addItems(list(PAPIERTOENE))
        self.papier.setCurrentText(s.get("lesehilfe/papier", "Weiß"))
        self.buchstaben = QDoubleSpinBox(); self.buchstaben.setRange(0, 6); self.buchstaben.setSingleStep(0.2)
        self.buchstaben.setSuffix(" px"); self.buchstaben.setValue(float(s.get("lesehilfe/buchstaben", 0)))
        self.wort = QDoubleSpinBox(); self.wort.setRange(0, 20); self.wort.setSingleStep(0.5)
        self.wort.setSuffix(" px"); self.wort.setValue(float(s.get("lesehilfe/wort", 0)))
        form = QFormLayout()
        form.addRow("Papierton", self.papier)
        form.addRow("Buchstabenabstand", self.buchstaben)
        form.addRow("Wortabstand", self.wort)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        bb.button(QDialogButtonBox.Reset).clicked.connect(self._zurueck)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)
        for w in (self.papier,):
            w.currentTextChanged.connect(lambda *_: self.anwenden())
        for w in (self.buchstaben, self.wort):
            w.valueChanged.connect(lambda *_: self.anwenden())

    def _zurueck(self):
        self.papier.setCurrentText("Weiß"); self.buchstaben.setValue(0); self.wort.setValue(0)

    def anwenden(self):
        s = self.w.settings
        s.set("lesehilfe/papier", self.papier.currentText())
        s.set("lesehilfe/buchstaben", self.buchstaben.value())
        s.set("lesehilfe/wort", self.wort.value())
        self.w.lesehilfe_anwenden()
