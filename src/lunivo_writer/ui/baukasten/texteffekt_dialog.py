"""Das Fenster „Texteffekte formatieren“ (Textfüllung und -kontur) als Baustein.

    d = TexteffektDialog(parent, werte)          # Wörterbuch wie in ``editor.texteffekt.EFFEKT``
    if d.exec(): d.werte()                        # ``texteffekt.zu_format(werte)`` macht ein Zeichenformat daraus

Das Fenster formatiert nichts selbst: Der Editor (Schriftart-Fenster, Band) und die Formatvorlage rufen es auf und tun mit dem
Ergebnis, was zu ihnen gehört. Schatten, Spiegelung, Leuchten und 3D-Format fehlen, weil Qt sie am Text nicht zeichnet.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QTextBlockFormat
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QRadioButton, QSlider,
    QVBoxLayout, QWidget,
)

from lunivo_writer.editor import texteffekt as T
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.linien import linien_symbol
from lunivo_writer.ui.baukasten.text_format import zeichne_absaetze


class TexteffektDialog(QDialog):
    def __init__(self, parent=None, werte: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Texteffekte formatieren")
        self.setMinimumWidth(420)
        w = {**T.EFFEKT, **(werte or {})}
        v = QVBoxLayout(self)
        # ---- Textfüllung
        fg = QGroupBox("Textfüllung"); g = QGridLayout(fg)
        self.r_keine, self.r_farbe = QRadioButton("Keine Füllung"), QRadioButton("Einfarbige Füllung")
        g.addWidget(self.r_keine, 0, 0, 1, 3); g.addWidget(self.r_farbe, 1, 0, 1, 3)
        self.farbe = FarbFeld(w["farbe"], "Füllfarbe", keine_text="Automatisch")
        self.trans = QSlider(Qt.Horizontal); self.trans.setRange(0, 100)
        self.trans_wert = QDoubleSpinBox(); self.trans_wert.setRange(0, 100); self.trans_wert.setDecimals(0); self.trans_wert.setSuffix(" %")
        g.addWidget(QLabel("Farbe:"), 2, 0); g.addWidget(self.farbe, 2, 1, 1, 2)
        g.addWidget(QLabel("Transparenz:"), 3, 0); g.addWidget(self.trans, 3, 1); g.addWidget(self.trans_wert, 3, 2)
        g.setColumnStretch(1, 1)
        v.addWidget(fg)
        # ---- Textkontur
        kg = QGroupBox("Textkontur"); k = QGridLayout(kg)
        self.k_keine, self.k_linie = QRadioButton("Keine Linie"), QRadioButton("Durchgezogene Linie")
        k.addWidget(self.k_keine, 0, 0, 1, 3); k.addWidget(self.k_linie, 1, 0, 1, 3)
        self.k_farbe = FarbFeld(w["kontur_farbe"], "Konturfarbe")
        self.k_breite = QDoubleSpinBox(); self.k_breite.setRange(0.1, 20); self.k_breite.setDecimals(2); self.k_breite.setSingleStep(0.25); self.k_breite.setSuffix(" pt")
        self.k_art = QComboBox(); self.k_art.setIconSize(QSize(90, 14))
        for key, (name, _s) in T.KONTUR_ARTEN.items():
            self.k_art.addItem(linien_symbol(key, QSize(90, 14), "#343a40"), name, key)
        k.addWidget(QLabel("Farbe:"), 2, 0); k.addWidget(self.k_farbe, 2, 1, 1, 2)
        k.addWidget(QLabel("Breite:"), 3, 0); k.addWidget(self.k_breite, 3, 1, 1, 2)
        k.addWidget(QLabel("Linienart:"), 4, 0); k.addWidget(self.k_art, 4, 1, 1, 2)
        k.setColumnStretch(1, 1)
        v.addWidget(kg)
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 70); v.addWidget(self.vorschau)
        zu = QHBoxLayout()
        zr = QPushButton("Zurücksetzen"); zr.clicked.connect(lambda: self.setze(dict(T.EFFEKT)))
        zu.addWidget(zr); zu.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(ok); v.addLayout(zu)
        self.setze(w)
        self.r_keine.toggled.connect(self._neu); self.k_keine.toggled.connect(self._neu)
        self.farbe.farbeGeaendert.connect(self._neu); self.k_farbe.farbeGeaendert.connect(self._neu)
        self.trans.valueChanged.connect(lambda x: (self.trans_wert.setValue(x), self._neu()))
        self.trans_wert.valueChanged.connect(lambda x: (self.trans.setValue(int(x)), self._neu()))
        self.k_breite.valueChanged.connect(self._neu); self.k_art.currentIndexChanged.connect(self._neu)

    def setze(self, w: dict) -> None:
        self.r_keine.setChecked(w["fuell"] == "keine"); self.r_farbe.setChecked(w["fuell"] != "keine")
        self.k_linie.setChecked(bool(w["kontur"])); self.k_keine.setChecked(not w["kontur"])
        self.farbe.setFarbe(w["farbe"]); self.k_farbe.setFarbe(w["kontur_farbe"])
        self.trans.setValue(int(w["transparenz"])); self.trans_wert.setValue(int(w["transparenz"]))
        self.k_breite.setValue(w["kontur_breite"]); self.k_art.setCurrentIndex(max(0, self.k_art.findData(w["kontur_art"])))
        self._neu()

    def werte(self) -> dict:
        return {"fuell": "keine" if self.r_keine.isChecked() else "farbe", "farbe": self.farbe.farbe, "transparenz": int(self.trans.value()),
                "kontur": self.k_linie.isChecked(), "kontur_farbe": self.k_farbe.farbe or "#000000", "kontur_breite": self.k_breite.value(),
                "kontur_art": self.k_art.currentData()}

    def _neu(self, *_) -> None:
        fuell = self.r_farbe.isChecked()
        for x in (self.farbe, self.trans, self.trans_wert):
            x.setEnabled(fuell)
        for x in (self.k_farbe, self.k_breite, self.k_art):
            x.setEnabled(self.k_linie.isChecked())
        self.vorschau.update()

    def _male(self, p, rect) -> None:
        f = T.zu_format(self.werte())
        f.setFontPointSize(26); f.setFontFamilies(["Liberation Sans"]); f.setFontWeight(700)
        if f.foreground().style() == Qt.NoBrush:
            f.setForeground(QColor("#111417"))
        bf = QTextBlockFormat(); bf.setAlignment(Qt.AlignHCenter)
        zeichne_absaetze(p, rect, [(bf, f, "Beispieltext")], mittig=True)
