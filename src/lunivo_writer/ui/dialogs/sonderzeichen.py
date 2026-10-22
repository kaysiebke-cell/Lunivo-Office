"""Sonderzeichen einfügen: Tabelle nach Gruppen, Doppelklick fügt ein."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDialog, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout

GRUPPEN = {
    "Satzzeichen": "„“‚‘»«›‹–—…·•†‡§¶©®™°′″‰¿¡",
    "Währung": "€$£¥¢₣₹₽₩฿₺",
    "Mathematik": "±×÷≠≈≤≥∞√∑∏∫∂∆∇∈∉∩∪⊂⊃⊆⊇∧∨¬∀∃",
    "Pfeile": "←↑→↓↔↕⇐⇑⇒⇓⇔↩↪↦",
    "Hoch/Tief": "⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉½⅓¼¾⅔",
    "Griechisch": "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψω",
    "Lateinisch": "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿßẞŒœ",
    "Symbole": "✓✗★☆♥♦♣♠☎✉☀☁☂♪♫⚠✂✎",
}


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
class SonderzeichenDialog(QDialog):
    def __init__(self, parent, einfuegen):
        super().__init__(parent)
        self.setWindowTitle("Sonderzeichen")
        self.einfuegen = einfuegen
        v = QVBoxLayout(self)
        self.gruppe = QComboBox()
        self.gruppe.addItems(list(GRUPPEN))
        self.gruppe.currentTextChanged.connect(self.fuellen)
        v.addWidget(self.gruppe)
        self.tabelle = QTableWidget()
        self.tabelle.setColumnCount(12)
        self.tabelle.horizontalHeader().hide(); self.tabelle.verticalHeader().hide()
        self.tabelle.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabelle.cellDoubleClicked.connect(self._klick)
        self.tabelle.currentCellChanged.connect(self._zeige)
        v.addWidget(self.tabelle)
        self.info = QLabel("Doppelklick fügt das Zeichen ein.")
        v.addWidget(self.info)
        self.resize(520, 360)
        self.fuellen(self.gruppe.currentText())

    def fuellen(self, name: str):
        zs = GRUPPEN[name]
        self.tabelle.setRowCount((len(zs) + 11) // 12)
        for c in range(12):
            self.tabelle.setColumnWidth(c, 38)
        self.tabelle.clearContents()
        for i, z in enumerate(zs):
            it = QTableWidgetItem(z)
            it.setTextAlignment(Qt.AlignCenter)
            f = it.font(); f.setPointSize(14); it.setFont(f)
            self.tabelle.setItem(i // 12, i % 12, it)

    def _klick(self, r, c):
        it = self.tabelle.item(r, c)
        if it:
            self.einfuegen(it.text())

    def _zeige(self, r, c, *_):
        it = self.tabelle.item(r, c)
        if it:
            self.info.setText(f"U+{ord(it.text()):04X}  —  Doppelklick fügt ein.")
