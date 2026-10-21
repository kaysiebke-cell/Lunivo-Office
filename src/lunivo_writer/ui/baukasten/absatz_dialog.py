"""Das Fenster „Absatz“ (Einzüge und Abstände, Zeilen- und Seitenumbruch) als Baustein.

    d = AbsatzDialog(parent, werte, umfang="text")      # umfang="vorlage": nur Ausrichtung, Einzug links, Abstände, Zeilenabstand
    if d.exec(): d.werte()                               # dict, siehe ``ABSATZ``

Das Fenster formatiert nichts selbst. Die Tabstopps stehen unter ``werte()["tabs"]`` (Liste aus mm und Ausrichtung) und kommen aus
dem Baustein ``TabstoppDialog``. Nur, was Lunivo wirklich zeichnen und speichern kann, steht darin: Qt kennt keine Regeln wie
„Absatz nicht trennen“, darum fehlen sie.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextBlockFormat, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche
from lunivo_writer.ui.baukasten.mass_feld import spin
from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog
from lunivo_writer.ui.baukasten.text_format import AUSRICHTUNG, zeichne_absaetze

ABSATZ = {"ausr": "links", "rtl": False, "einzug": 0.0, "rechts": 0.0, "erste": 0.0, "vor": 0.0, "nach": 0.0, "zeilen": 1.0,
          "umbruch": False, "tabs": []}
_MM = 2.2                                        # Bildpunkte je Millimeter in der Vorschau
_SONDER = (("keiner", "(Kein)"), ("erste", "Erste Zeile"), ("haengend", "Hängend"))
_ZEILEN = ((1.0, "Einfach"), (1.5, "1,5 Zeilen"), (2.0, "Doppelt"), (0.0, "Mehrfach"))


class AbsatzDialog(QDialog):
    def __init__(self, parent=None, werte: dict | None = None, *, umfang: str = "text"):
        super().__init__(parent)
        self.setWindowTitle("Absatz")
        self.umfang = umfang
        w = {**ABSATZ, **(werte or {})}
        self._tabs = list(w["tabs"])
        v = QVBoxLayout(self)
        self.reiter = QTabWidget(); v.addWidget(self.reiter, 1)
        # ---- Einzüge und Abstände
        s = QWidget(); sv = QVBoxLayout(s)
        allg = QGroupBox("Allgemein"); ag = QGridLayout(allg)
        self.ausr = QComboBox()
        for k, name in AUSRICHTUNG:
            self.ausr.addItem(name, k)
        self.richtung = QComboBox(); self.richtung.addItem("Von links nach rechts", False); self.richtung.addItem("Von rechts nach links", True)
        ag.addWidget(QLabel("Ausrichtung:"), 0, 0); ag.addWidget(self.ausr, 0, 1)
        ag.addWidget(QLabel("Textrichtung:"), 0, 2); ag.addWidget(self.richtung, 0, 3)
        ag.setColumnStretch(1, 1); ag.setColumnStretch(3, 1)
        sv.addWidget(allg)
        ein = QGroupBox("Einzug"); eg = QGridLayout(ein)
        self.links = spin(0.0, 0.0, 300.0); self.rechts = spin(0.0, 0.0, 300.0); self.sonder = QComboBox()
        for k, name in _SONDER:
            self.sonder.addItem(name, k)
        self.sonder_mass = spin(0.0, 0.0, 300.0)
        eg.addWidget(QLabel("Vor Text:"), 0, 0); eg.addWidget(self.links, 0, 1)
        eg.addWidget(QLabel("Nach Text:"), 0, 2); eg.addWidget(self.rechts, 0, 3)
        eg.addWidget(QLabel("Sondereinzug:"), 1, 0); eg.addWidget(self.sonder, 1, 1)
        eg.addWidget(QLabel("Um:"), 1, 2); eg.addWidget(self.sonder_mass, 1, 3)
        sv.addWidget(ein)
        abst = QGroupBox("Abstand"); bg = QGridLayout(abst)
        self.vor = spin(0.0, 0.0, 200.0, " pt"); self.nach = spin(0.0, 0.0, 200.0, " pt")
        self.zeilen_art = QComboBox()
        for f, name in _ZEILEN:
            self.zeilen_art.addItem(name, f)
        self.zeilen = spin(1.0, 0.1, 10.0, " ×", 0.05, 2)
        bg.addWidget(QLabel("Vor Absatz:"), 0, 0); bg.addWidget(self.vor, 0, 1)
        bg.addWidget(QLabel("Nach Absatz:"), 0, 2); bg.addWidget(self.nach, 0, 3)
        bg.addWidget(QLabel("Zeilenabstand:"), 1, 0); bg.addWidget(self.zeilen_art, 1, 1)
        bg.addWidget(QLabel("Faktor:"), 1, 2); bg.addWidget(self.zeilen, 1, 3)
        sv.addWidget(abst)
        sv.addStretch(1)
        self.reiter.addTab(s, "Einzüge und Abstände")
        # ---- Zeilen- und Seitenumbruch
        u = QWidget(); uv = QVBoxLayout(u)
        self.umbruch = QCheckBox("Seitenumbruch oberhalb")
        uv.addWidget(self.umbruch); uv.addStretch(1)
        self.reiter.addTab(u, "Zeilen- und Seitenumbruch")
        # ---- Vorschau und Knöpfe
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 130); v.addWidget(self.vorschau)
        zu = QHBoxLayout()
        self.tabs_knopf = QPushButton("Tabstopps …"); self.tabs_knopf.clicked.connect(self._tabstopps)
        zu.addWidget(self.tabs_knopf); zu.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(ok); v.addLayout(zu)
        if umfang == "vorlage":                      # eine Vorlage kennt nur diese Felder
            for wd in (self.richtung, self.rechts, self.sonder, self.sonder_mass, self.tabs_knopf):
                wd.setVisible(False)
            for lab in (allg, ein, abst):
                for q in lab.findChildren(QLabel):
                    if q.text() in ("Textrichtung:", "Nach Text:", "Sondereinzug:", "Um:"):
                        q.setVisible(False)
            ein.setTitle("Einzug"); self.reiter.removeTab(1)
        self.setze(w)
        for sig in (self.ausr.currentIndexChanged, self.richtung.currentIndexChanged, self.links.valueChanged, self.rechts.valueChanged,
                    self.sonder.currentIndexChanged, self.sonder_mass.valueChanged, self.vor.valueChanged, self.nach.valueChanged,
                    self.zeilen.valueChanged):
            sig.connect(lambda *_: self._neu())
        self.zeilen_art.currentIndexChanged.connect(self._zeilenart)
        self.sonder.currentIndexChanged.connect(lambda *_: self._neu())
        self._neu()

    def setze(self, w: dict) -> None:
        self.ausr.setCurrentIndex(max(0, self.ausr.findData(w["ausr"])))
        self.richtung.setCurrentIndex(1 if w["rtl"] else 0)
        self.links.setValue(w["einzug"]); self.rechts.setValue(w["rechts"])
        e = w["erste"]
        self.sonder.setCurrentIndex(1 if e > 0 else 2 if e < 0 else 0)
        self.sonder_mass.setValue(abs(e))
        self.vor.setValue(w["vor"]); self.nach.setValue(w["nach"])
        z = w["zeilen"] or 1.0
        i = self.zeilen_art.findData(z)
        self.zeilen_art.setCurrentIndex(i if i >= 0 else self.zeilen_art.count() - 1)
        self.zeilen.setValue(z)
        self.umbruch.setChecked(bool(w["umbruch"]))
        self._zeilenart()

    def _zeilenart(self, *_) -> None:
        f = self.zeilen_art.currentData()
        if f:
            self.zeilen.setValue(f)
        self.zeilen.setEnabled(not f)
        self._neu()

    def _neu(self) -> None:
        self.sonder_mass.setEnabled(self.sonder.currentData() != "keiner")
        self.vorschau.update()

    def werte(self) -> dict:
        s = self.sonder.currentData()
        m = self.sonder_mass.value()
        return {"ausr": self.ausr.currentData(), "rtl": bool(self.richtung.currentData()), "einzug": self.links.value(),
                "rechts": self.rechts.value(), "erste": m if s == "erste" else -m if s == "haengend" else 0.0,
                "vor": self.vor.value(), "nach": self.nach.value(), "zeilen": self.zeilen.value(),
                "umbruch": self.umbruch.isChecked(), "tabs": list(self._tabs)}

    def _tabstopps(self) -> None:
        d = TabstoppDialog(self, self._tabs)
        if d.exec():
            self._tabs = d.stopps()

    def _male(self, p, rect) -> None:
        """Vorhergehender Absatz (grau), der eigene mit Einzügen und Abständen, folgender Absatz (grau)."""
        w = self.werte()
        grau = QTextCharFormat(); grau.setForeground(Qt.gray); grau.setFontPointSize(7.5); grau.setFontFamilies(["Liberation Sans"])
        f = QTextCharFormat(); f.setFontPointSize(9); f.setFontFamilies(["Liberation Sans"]); f.setForeground(Qt.black)
        bf = QTextBlockFormat()
        bf.setLeftMargin(w["einzug"] * _MM); bf.setRightMargin(w["rechts"] * _MM)
        bf.setTextIndent(w["erste"] * _MM)
        bf.setTopMargin(w["vor"] * 0.8); bf.setBottomMargin(w["nach"] * 0.8)
        bf.setLineHeight(w["zeilen"] * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        bf.setAlignment({"mitte": Qt.AlignHCenter, "rechts": Qt.AlignRight, "block": Qt.AlignJustify}.get(w["ausr"], Qt.AlignLeft))
        if w["rtl"]:
            bf.setLayoutDirection(Qt.RightToLeft)
        zeichne_absaetze(p, rect.adjusted(6, 4, -6, -4), [
            (QTextBlockFormat(), grau, "Vorhergehender Absatz " * 6), (bf, f, "Beispieltext " * 14),
            (QTextBlockFormat(), grau, "Folgender Absatz " * 6)])
