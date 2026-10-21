"""Das Fenster „Tastenkombination“ als Baustein: eine Tastenkombination aufnehmen und zuweisen.

    d = TastenDialog(parent, aktuell="Ctrl+Alt+1", belegt=lambda taste: "Name" | None)
    if d.exec(): d.taste()          # "Ctrl+Alt+1" im Portable-Format, "" = Zuordnung entfernt

Das Fenster weist nichts selbst zu; wer es aufruft (Formatvorlage, später Makro oder Textbaustein), speichert die Taste.
``belegt`` meldet, wer die Kombination schon hat; dann lässt sich nicht zuweisen.
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QKeySequenceEdit, QLabel, QPushButton, QVBoxLayout


class TastenDialog(QDialog):
    def __init__(self, parent=None, aktuell: str = "", *, belegt=None):
        super().__init__(parent)
        self.setWindowTitle("Tastenkombination")
        self._belegt = belegt
        v = QVBoxLayout(self)
        g = QGroupBox("Tasten"); h = QHBoxLayout(g)
        h.addWidget(QLabel("Tastenkombination:"))
        self.feld = QKeySequenceEdit(QKeySequence(aktuell)); self.feld.setMaximumSequenceLength(1)
        h.addWidget(self.feld, 1)
        v.addWidget(g)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet("color: #e8590c;"); self.hinweis.setWordWrap(True)
        v.addWidget(self.hinweis)
        zu = QHBoxLayout(); zu.addStretch(1)
        self.zuweisen = QPushButton("Zuweisen"); self.zuweisen.setDefault(True)
        schliessen = QPushButton("Schließen")
        self.zuweisen.clicked.connect(self.accept); schliessen.clicked.connect(self.reject)
        zu.addWidget(self.zuweisen); zu.addWidget(schliessen); v.addLayout(zu)
        self.feld.keySequenceChanged.connect(self._pruefen)
        self._pruefen()

    def taste(self) -> str:
        return self.feld.keySequence().toString(QKeySequence.PortableText)

    def _pruefen(self, *_) -> None:
        t = self.taste()
        wer = self._belegt(t) if (t and self._belegt) else None
        self.hinweis.setText(f"Diese Tastenkombination hat schon: {wer}" if wer else "")
        self.zuweisen.setEnabled(not wer)
