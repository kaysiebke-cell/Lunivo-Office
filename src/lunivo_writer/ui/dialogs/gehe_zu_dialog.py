"""Dialog „Gehe zu“ (Strg+G): Ziel wählen, Nummer eingeben oder aus der Liste nehmen, springen."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QLabel, QListWidget, QPushButton, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from lunivo_writer.editor import gehe_zu as G


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
class GeheZuDialog(PanelFaehig, QDialog):
    def __init__(self, parent, ed, art: str = "Seite"):
        super().__init__(parent)
        self.setWindowTitle("Gehe zu")
        self.ed = ed
        v = QVBoxLayout(self)
        self.art = QComboBox()
        self.art.addItems(G.ARTEN)
        v.addWidget(QLabel("Gehe zu:"))
        v.addWidget(self.art)
        self.stapel = QStackedWidget()
        zahl = QWidget()
        zl = QVBoxLayout(zahl)
        self.nummer_text = QLabel("Seitennummer:")
        self.nummer = QSpinBox()
        zl.addWidget(self.nummer_text)
        zl.addWidget(self.nummer)
        zl.addStretch(1)
        self.liste = QListWidget()
        self.liste.itemDoubleClicked.connect(lambda _i: self.springen())
        self.stapel.addWidget(zahl)
        self.stapel.addWidget(self.liste)
        v.addWidget(self.stapel, 1)
        self.knopf = QPushButton("Gehe zu")
        self.knopf.setDefault(True)
        self.knopf.clicked.connect(self.springen)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.addButton(self.knopf, QDialogButtonBox.ActionRole)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
        self.art.currentTextChanged.connect(self._umstellen)
        self.art.setCurrentText(art)
        self._umstellen(art)
        self.resize(420, 360)

    def _umstellen(self, art: str) -> None:
        if art in G.NUMMERN:
            self.stapel.setCurrentIndex(0)
            self.nummer_text.setText("Seitennummer:" if art == "Seite" else "Zeilennummer (Absatz):")
            self.nummer.setRange(1, G.maximum(self.ed, art))
            self.nummer.setValue(self.ed.current_page() if art == "Seite" else self.ed.textCursor().blockNumber() + 1)
        else:
            self.stapel.setCurrentIndex(1)
            self.liste.clear()
            self._ziele = G.ziele(self.ed, art)
            for text, _pos in self._ziele:
                self.liste.addItem(text)
            if self._ziele:
                self.liste.setCurrentRow(0)
            else:
                self.liste.addItem(f"(Keine Einträge: {art})")
                self._ziele = []

    def ziel_position(self) -> int | None:
        art = self.art.currentText()
        if art == "Seite":
            return G.seitenstart(self.ed, self.nummer.value())
        if art == "Zeile":
            return G.zeilenstart(self.ed, self.nummer.value())
        row = self.liste.currentRow()
        return self._ziele[row][1] if 0 <= row < len(self._ziele) else None

    def springen(self) -> None:
        pos = self.ziel_position()
        if pos is not None:
            G.springen(self.ed, pos)
