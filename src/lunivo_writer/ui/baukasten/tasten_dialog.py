"""Das Fenster „Tastenkombination“ als Baustein: eine Tastenkombination aufnehmen und zuweisen.

    d = TastenDialog(parent, aktuell="Ctrl+Alt+1", belegt=lambda taste: "Name" | None)
    if d.exec(): d.taste()          # "Ctrl+Alt+1" im Portable-Format, "" = Zuordnung entfernt

Das Fenster weist nichts selbst zu; wer es aufruft (Formatvorlage, später Makro oder Textbaustein), speichert die Taste.
``belegt`` meldet, wer die Kombination schon hat; dann lässt sich nicht zuweisen.
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QKeySequenceEdit, QLabel, QVBoxLayout

from lunivo_writer.ui.baukasten.dialog_rahmen import fussleiste


from lunivo_writer.core.farben import Farbe
class TastenDialog(QDialog):
    def __init__(self, parent=None, aktuell: str = "", *, belegt=None):
        super().__init__(parent)
        self.setWindowTitle("Tastenkombination"); self.resize(311, 122)
        self._belegt = belegt
        v = QVBoxLayout(self)
        g = QGroupBox("Tasten"); h = QHBoxLayout(g)
        h.addWidget(QLabel("Tastenkombination:"))
        self.feld = QKeySequenceEdit(QKeySequence(aktuell)); self.feld.setMaximumSequenceLength(1)
        h.addWidget(self.feld, 1)
        v.addWidget(g)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet(('color: ' + Farbe.ORANGE + ';')); self.hinweis.setWordWrap(True)
        v.addWidget(self.hinweis)
        self.zuweisen = fussleiste(self, v, ok_text="Zuweisen", abbrechen_text="Schließen")
        self.feld.keySequenceChanged.connect(self._pruefen)
        self._pruefen()

    def taste(self) -> str:
        return self.feld.keySequence().toString(QKeySequence.PortableText)

    def _pruefen(self, *_) -> None:
        t = self.taste()
        wer = self._belegt(t) if (t and self._belegt) else None
        self.hinweis.setText(f"Diese Tastenkombination hat schon: {wer}" if wer else "")
        self.zuweisen.setEnabled(not wer)
