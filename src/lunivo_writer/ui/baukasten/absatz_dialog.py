"""Das Fenster „Absatz“ (Einzüge und Abstände, Zeilen- und Seitenumbruch) als Baustein.

    d = AbsatzDialog(parent, werte)                      # alle Felder; ``umfang`` ist nur ein Name für den Aufrufer (Absatz oder Formatvorlage)
    if d.exec(): d.werte()                               # dict, siehe ``ABSATZ``

Das Fenster formatiert nichts selbst. Die Tabstopps stehen unter ``werte()["tabs"]`` (Liste aus mm und Ausrichtung) und kommen aus
dem Baustein ``TabstoppDialog``. Nur, was Lunivo wirklich zeichnen und speichern kann, steht darin: Qt kennt keine Regeln wie
„Absatz nicht trennen“, darum fehlen sie.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextBlockFormat, QTextCharFormat
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QRadioButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste
from lunivo_writer.editor import absatzopt
from lunivo_writer.ui.baukasten.mass_feld import _PT_MM, EinheitFeld, spin
from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog
from lunivo_writer.ui.baukasten.text_format import AUSRICHTUNG, zeichne_absaetze

ABSATZ = {"ausr": "links", "rtl": False, "einzug": 0.0, "rechts": 0.0, "erste": 0.0, "vor": 0.0, "nach": 0.0, "zeilen": 1.0,
          "zeilen_art": "faktor", "zeilen_pt": 12.0, "ebene": 0, "umbruch": False, "tabs": [], "opt": {}}
_MM = 2.2                                        # Bildpunkte je Millimeter in der Vorschau
_SONDER = (("keiner", "(Kein)"), ("erste", "Erste Zeile"), ("haengend", "Hängend"))
_ZEILEN = (("faktor", 1.0, "Einfach"), ("faktor", 1.5, "1,5 Zeilen"), ("faktor", 2.0, "Doppelt"), ("mindestens", 0.0, "Mindestens"),
           ("genau", 0.0, "Genau"), ("faktor", 0.0, "Mehrfach"))


class AbsatzDialog(QDialog):
    def __init__(self, parent=None, werte: dict | None = None, *, umfang: str = "text"):
        super().__init__(parent)
        self.setWindowTitle("Absatz")
        self.resize(574, 631)
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
        self.ebene = QComboBox(); self.ebene.addItem("Textkörper", 0)
        for i in range(1, 10):
            self.ebene.addItem(f"Ebene {i}", i)
        self.r_rtl, self.r_ltr = QRadioButton("Rechts nach links"), QRadioButton("Links-Nach-Rechts")
        self.richtung = QButtonGroup(self); self.richtung.addButton(self.r_rtl); self.richtung.addButton(self.r_ltr)
        rz = QHBoxLayout(); rz.addWidget(self.r_rtl); rz.addWidget(self.r_ltr); rz.addStretch(1)
        ag.addWidget(QLabel("Ausrichtung:"), 0, 0); ag.addWidget(self.ausr, 0, 1)
        ag.addWidget(QLabel("Gliederungsebene:"), 0, 2); ag.addWidget(self.ebene, 0, 3)
        ag.addWidget(QLabel("Richtung:"), 1, 0); ag.addLayout(rz, 1, 1, 1, 3)
        ag.setColumnStretch(1, 1); ag.setColumnStretch(3, 1)
        sv.addWidget(allg)
        ein = QGroupBox("Einzug"); eg = QGridLayout(ein)
        self.links = EinheitFeld(0.0, 0.0, 300.0); self.rechts = EinheitFeld(0.0, 0.0, 300.0); self.sonder = QComboBox()
        for k, name in _SONDER:
            self.sonder.addItem(name, k)
        self.sonder_mass = EinheitFeld(0.0, 0.0, 300.0)
        eg.addWidget(QLabel("Vor Text:"), 0, 0); eg.addWidget(self.links, 0, 1)
        eg.addWidget(QLabel("Sondereinzug:"), 0, 2); eg.addWidget(self.sonder, 0, 3)
        eg.addWidget(QLabel("Nach Text:"), 1, 0); eg.addWidget(self.rechts, 1, 1)
        eg.addWidget(QLabel("Von:"), 1, 2); eg.addWidget(self.sonder_mass, 1, 3)
        self.rest_einzug = QCheckBox("Bei Dokumentrasterdefinition rechten Einzug automatisch ausrichten")
        eg.addWidget(self.rest_einzug, 2, 0, 1, 4)
        sv.addWidget(ein)
        abst = QGroupBox("Abstand"); bg = QGridLayout(abst)
        self.vor = EinheitFeld(0.0, 0.0, 200 * _PT_MM, ("pt", "Zeile", "mm", "cm", "in"), "pt")
        self.nach = EinheitFeld(0.0, 0.0, 200 * _PT_MM, ("pt", "Zeile", "mm", "cm", "in"), "pt")
        self.zeilen_art = QComboBox()
        for art, f, name in _ZEILEN:
            self.zeilen_art.addItem(name, (art, f))
        self.zeilen = spin(1.0, 0.1, 10.0, " ×", 0.05, 2)
        self.zeilen_pt = spin(12.0, 1.0, 1000.0, " pt", 0.5, 1)
        bg.addWidget(QLabel("Vor:"), 0, 0); bg.addWidget(self.vor, 0, 1)
        bg.addWidget(QLabel("Zeilenabstand:"), 0, 2); bg.addWidget(self.zeilen_art, 0, 3)
        bg.addWidget(QLabel("Nach:"), 1, 0); bg.addWidget(self.nach, 1, 1)
        bg.addWidget(QLabel("Von:"), 1, 2); bg.addWidget(self.zeilen, 1, 3); bg.addWidget(self.zeilen_pt, 1, 3)
        self.raster = QCheckBox("Bei Dokumentrasterdefinition am Raster ausrichten")
        bg.addWidget(self.raster, 2, 0, 1, 4)
        sv.addWidget(abst)
        sv.addStretch(1)
        self.reiter.addTab(s, "Einzüge und Abstände")
        # ---- Zeilen- und Seitenumbruch
        u = QWidget(); uv = QVBoxLayout(u)
        pg = QGroupBox("Paginierung"); pgl = QGridLayout(pg)
        self.cb = {k: QCheckBox(t) for k, t in (
            ("kontrolle", "Absatzkontrolle"), ("nicht_trennen", "Nicht vom nächsten Absatz trennen"), ("zusammen", "Diesen Absatz zusammenhalten"),
            ("asiat", "Asiatische Regeln zum Steuern von Anfangs- und Endzeichen verwenden"),
            ("mitten", "Textumbruch in der Mitte eines Wortes für westlichen Text zulassen"), ("haengend", "Hängende Interpunktion zulassen"),
            ("kompr", "Interpunktion am Zeilenbeginn zum Komprimieren zulassen"),
            ("ade", "Abstand zwischen asiatischem und westlichem Text automatisch anpassen"),
            ("adn", "Abstand zwischen asiatischem Text und Zahlen automatisch anpassen"))}
        self.umbruch = QCheckBox("Seitenumbruch oberhalb")
        pgl.addWidget(self.cb["kontrolle"], 0, 0); pgl.addWidget(self.cb["nicht_trennen"], 0, 1)
        pgl.addWidget(self.cb["zusammen"], 1, 0); pgl.addWidget(self.umbruch, 1, 1)
        zg = QGroupBox("Zeilenumbruch"); zl = QVBoxLayout(zg)
        for k in ("asiat", "mitten", "haengend"):
            zl.addWidget(self.cb[k])
        ag2 = QGroupBox("Zeichenabstand"); al = QVBoxLayout(ag2)
        for k in ("kompr", "ade", "adn"):
            al.addWidget(self.cb[k])
        self.textausr = QComboBox()
        for k, name in (("auto", "Automatisch"), ("top", "Oben"), ("center", "Zentriert"), ("baseline", "Basislinie"), ("bottom", "Unten")):
            self.textausr.addItem(name, k)
        tz = QHBoxLayout(); tz.addWidget(QLabel("Textausrichtung:")); tz.addWidget(self.textausr); tz.addStretch(1)
        al.addLayout(tz)
        uv.addWidget(pg); uv.addWidget(zg); uv.addWidget(ag2); uv.addStretch(1)
        self.reiter.addTab(u, "Zeilen- und Seitenumbruch")
        # ---- Vorschau und Knöpfe
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 130); v.addWidget(self.vorschau)
        self.tabs_knopf = QPushButton("Tabstopps …"); self.tabs_knopf.clicked.connect(self._tabstopps)
        fussleiste(self, v, self.tabs_knopf)
        self.setze(w)
        for sig in (self.ausr.currentIndexChanged, self.r_rtl.toggled, self.links.valueChanged, self.rechts.valueChanged,
                    self.sonder.currentIndexChanged, self.sonder_mass.valueChanged, self.vor.valueChanged, self.nach.valueChanged,
                    self.zeilen.valueChanged):
            sig.connect(lambda *_: self._neu())
        self.zeilen_art.currentIndexChanged.connect(self._zeilenart)
        self.sonder.currentIndexChanged.connect(lambda *_: self._neu())
        self._neu()

    def setze(self, w: dict) -> None:
        self.ausr.setCurrentIndex(max(0, self.ausr.findData(w["ausr"])))
        (self.r_rtl if w["rtl"] else self.r_ltr).setChecked(True)
        self.ebene.setCurrentIndex(max(0, self.ebene.findData(w["ebene"])))
        self.links.setValue(w["einzug"]); self.rechts.setValue(w["rechts"])
        e = w["erste"]
        self.sonder.setCurrentIndex(1 if e > 0 else 2 if e < 0 else 0)
        self.sonder_mass.setValue(abs(e))
        self.vor.setValue(w["vor"] * _PT_MM); self.nach.setValue(w["nach"] * _PT_MM)      # Werte in pt, Felder in mm
        z = w["zeilen"] or 1.0
        self.zeilen_pt.setValue(w["zeilen_pt"])
        daten = [tuple(self.zeilen_art.itemData(k)) for k in range(self.zeilen_art.count())]
        wunsch = (w["zeilen_art"], 0.0) if w["zeilen_art"] != "faktor" else ("faktor", z)
        i = daten.index(wunsch) if wunsch in daten else daten.index(("faktor", 0.0)) if ("faktor", 0.0) in daten else 0
        self.zeilen_art.setCurrentIndex(max(0, i))
        self.zeilen.setValue(z)
        self.umbruch.setChecked(bool(w["umbruch"]))
        o = {**absatzopt.VORGABE, **w["opt"]}
        for k, c in self.cb.items():
            c.setChecked(o[k])
        self.rest_einzug.setChecked(o["rest_einzug"]); self.raster.setChecked(o["raster"])
        self.textausr.setCurrentIndex(max(0, self.textausr.findData(o["textausr"])))
        self._zeilenart()

    def _zeilenart(self, *_) -> None:
        art, f = tuple(self.zeilen_art.currentData())
        if art == "faktor" and f:
            self.zeilen.setValue(f)
        self.zeilen.setVisible(art == "faktor" and self.umfang != "x"); self.zeilen_pt.setVisible(art != "faktor" and self.umfang == "text")
        self.zeilen.setEnabled(art == "faktor" and not f)
        self._neu()

    def _neu(self) -> None:
        self.sonder_mass.setEnabled(self.sonder.currentData() != "keiner")
        self.vorschau.update()

    def werte(self) -> dict:
        s = self.sonder.currentData()
        m = self.sonder_mass.value()
        art = tuple(self.zeilen_art.currentData())[0]
        return {"ausr": self.ausr.currentData(), "rtl": self.r_rtl.isChecked(), "ebene": self.ebene.currentData(), "einzug": self.links.value(),
                "rechts": self.rechts.value(), "erste": m if s == "erste" else -m if s == "haengend" else 0.0,
                "vor": self.vor.value() / _PT_MM, "nach": self.nach.value() / _PT_MM, "zeilen": self.zeilen.value(), "zeilen_art": art,
                "zeilen_pt": self.zeilen_pt.value(), "opt": self._opt(), "umbruch": self.umbruch.isChecked(), "tabs": list(self._tabs)}

    def _opt(self) -> dict:
        o = {k: c.isChecked() for k, c in self.cb.items()}
        o.update(rest_einzug=self.rest_einzug.isChecked(), raster=self.raster.isChecked(), textausr=self.textausr.currentData())
        return o

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
        if w["zeilen_art"] == "faktor":
            bf.setLineHeight(w["zeilen"] * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        else:
            bf.setLineHeight(w["zeilen_pt"] / 0.75 * _MM / 3.78, {"genau": QTextBlockFormat.LineHeightTypes.FixedHeight,
                                                                   "mindestens": QTextBlockFormat.LineHeightTypes.MinimumHeight}[w["zeilen_art"]].value)
        bf.setAlignment({"mitte": Qt.AlignHCenter, "rechts": Qt.AlignRight, "block": Qt.AlignJustify}.get(w["ausr"], Qt.AlignLeft))
        if w["rtl"]:
            bf.setLayoutDirection(Qt.RightToLeft)
        zeichne_absaetze(p, rect.adjusted(6, 4, -6, -4), [
            (QTextBlockFormat(), grau, "Vorhergehender Absatz " * 6), (bf, f, "Beispieltext " * 14),
            (QTextBlockFormat(), grau, "Folgender Absatz " * 6)])
