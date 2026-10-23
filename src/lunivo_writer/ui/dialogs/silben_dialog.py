"""Einstellungen für „Silben farbig“: alles, was jemand mit Legasthenie braucht, um es für sich passend zu machen."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QVBoxLayout, QWidget,
)

from lunivo_writer.editor import silbenfarben as S
from lunivo_writer.ui.baukasten import weitere_farben


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.core.farben import Farbe
class SilbenDialog(PanelFaehig, QDialog):
    def __init__(self, fenster):
        super().__init__(fenster)
        self.w = fenster
        self.setWindowTitle("Silben farbig — Einstellungen")
        self.setMinimumWidth(520)
        self._alt = S.konfig_lesen(fenster.settings)
        k = dict(self._alt)
        v = QVBoxLayout(self)
        info = QLabel("Jede Silbe eines Wortes bekommt abwechselnd eine andere Farbe. Das ändert nur die Anzeige — nicht den Text, "
                      "nicht die Datei. Die Silben sind deutsche Sprechsilben (Wan-de-rung); bei Fremdwörtern, Namen und seltenen Zusammensetzungen kann eine Grenze falsch liegen.")
        info.setWordWrap(True)
        info.setStyleSheet("color: palette(mid);")
        v.addWidget(info)
        self.an = QCheckBox("Silben farbig anzeigen")
        self.an.setChecked(k["an"])
        v.addWidget(self.an)
        f = QFormLayout()
        self.palette = QComboBox()
        self.palette.addItems(list(S.PALETTEN))
        self.palette.setCurrentText(k["palette"])
        f.addRow("Farben", self.palette)
        self.eigene_box = QWidget()
        eh = QHBoxLayout(self.eigene_box)
        eh.setContentsMargins(0, 0, 0, 0)
        self.eigene = list(k["eigene"])
        self.eigene_knoepfe = []
        for i in range(3):
            b = QPushButton()
            b.setFixedSize(44, 26)
            b.clicked.connect(lambda _=False, i=i: self._farbe_waehlen(i))
            self.eigene_knoepfe.append(b)
            eh.addWidget(b)
        self.anzahl = QSpinBox()
        self.anzahl.setRange(2, 3)
        self.anzahl.setValue(k["anzahl_eigene"])
        self.anzahl.setPrefix("Anzahl: ")
        eh.addWidget(self.anzahl)
        eh.addStretch(1)
        f.addRow("Eigene Farben", self.eigene_box)
        self.darstellung = QComboBox()
        self.darstellung.addItems(S.DARSTELLUNGEN)
        self.darstellung.setCurrentText(k["darstellung"])
        f.addRow("Darstellung", self.darstellung)
        self.fett = QCheckBox("Fett")
        self.fett.setChecked(k["fett"])
        f.addRow("", self.fett)
        self.mindestens = QSpinBox()
        self.mindestens.setRange(2, 10)
        self.mindestens.setValue(k["mindestens"])
        self.mindestens.setSuffix(" Buchstaben")
        f.addRow("Wörter einfärben ab", self.mindestens)
        self.einsilbig = QCheckBox("Auch Wörter einfärben, die sich nicht teilen lassen")
        self.einsilbig.setChecked(k["einsilbig"])
        f.addRow("", self.einsilbig)
        self.neu = QCheckBox("Jedes Wort beginnt wieder mit der ersten Farbe")
        self.neu.setChecked(k["neu_pro_wort"])
        f.addRow("", self.neu)
        self.absatz = QCheckBox("Nur im Absatz mit dem Cursor (ruhigeres Bild)")
        self.absatz.setChecked(k["nur_absatz"])
        f.addRow("", self.absatz)
        self.drucken = QCheckBox("Auch beim Drucken und im PDF")
        self.drucken.setChecked(k["drucken"])
        f.addRow("", self.drucken)
        v.addLayout(f)
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = QTextEdit()
        self.vorschau.setReadOnly(True)
        self.vorschau.setPlainText(S.BEISPIEL)
        self.vorschau.setFixedHeight(90)
        self.vorschau.setStyleSheet("QTextEdit { background: white; color: #222; font-size: 15pt; }")
        self._hl = S.SilbenFarben(self.vorschau.document(), {**k, "an": True, "nur_absatz": False})
        v.addWidget(self.vorschau)
        self.hinweis = QLabel("")
        self.hinweis.setStyleSheet(('color: ' + Farbe.ROT + ';'))
        v.addWidget(self.hinweis)
        standard = QPushButton("Standard"); standard.clicked.connect(self._standard)
        v.addWidget(knopfzeile(self, standard))
        for c in (self.an, self.fett, self.einsilbig, self.neu, self.absatz, self.drucken):
            c.toggled.connect(lambda *_: self.anwenden())
        for c in (self.palette, self.darstellung):
            c.currentTextChanged.connect(lambda *_: self.anwenden())
        for c in (self.mindestens, self.anzahl):
            c.valueChanged.connect(lambda *_: self.anwenden())
        self._knoepfe_faerben()
        self._zustand()

    def _farbe_waehlen(self, i: int) -> None:
        c = weitere_farben(self, self.eigene[i], "Farbe für Silbe " + str(i + 1))
        if c is not None:
            self.eigene[i] = c.name()
            self._knoepfe_faerben()
            self.anwenden()

    def _knoepfe_faerben(self) -> None:
        for b, c in zip(self.eigene_knoepfe, self.eigene):
            b.setStyleSheet(f"QPushButton {{ background: {c}; border: 1px solid palette(mid); border-radius: 4px; }}")

    def _zustand(self) -> None:
        eigene = self.palette.currentText() == "Eigene Farben"
        self.eigene_box.setEnabled(eigene)
        self.eigene_knoepfe[2].setEnabled(eigene and self.anzahl.value() == 3)

    def konfig(self) -> dict:
        return {"an": self.an.isChecked(), "palette": self.palette.currentText(), "eigene": list(self.eigene),
                "anzahl_eigene": self.anzahl.value(), "darstellung": self.darstellung.currentText(), "fett": self.fett.isChecked(),
                "einsilbig": self.einsilbig.isChecked(), "neu_pro_wort": self.neu.isChecked(), "mindestens": self.mindestens.value(),
                "nur_absatz": self.absatz.isChecked(), "drucken": self.drucken.isChecked(), "sprache": "de_DE"}

    def anwenden(self) -> None:
        """Wirkt sofort auf Vorschau und alle offenen Dokumente (Abbrechen stellt den alten Stand wieder her)."""
        self._zustand()
        k = self.konfig()
        self._hl.neu_konfigurieren({**k, "an": True, "nur_absatz": False})
        S.konfig_speichern(self.w.settings, k)
        self.w.silbenfarben_anwenden()

    def _standard(self) -> None:
        d = dict(S.STANDARD, an=self.an.isChecked())
        self.palette.setCurrentText(d["palette"]); self.eigene = list(d["eigene"]); self.anzahl.setValue(d["anzahl_eigene"])
        self.darstellung.setCurrentText(d["darstellung"]); self.fett.setChecked(d["fett"]); self.mindestens.setValue(d["mindestens"])
        self.einsilbig.setChecked(d["einsilbig"]); self.neu.setChecked(d["neu_pro_wort"]); self.absatz.setChecked(d["nur_absatz"])
        self.drucken.setChecked(d["drucken"])
        self._knoepfe_faerben()
        self.anwenden()

    def reject(self) -> None:
        S.konfig_speichern(self.w.settings, self._alt)
        self.w.silbenfarben_anwenden()
        super().reject()
