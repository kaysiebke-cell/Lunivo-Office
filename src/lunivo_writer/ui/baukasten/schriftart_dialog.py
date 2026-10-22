"""Das Fenster „Schriftart“ (Karteireiter Schriftart und Zeichenabstand) als Baustein.

    d = SchriftartDialog(parent, werte)             # werte: dict wie ``text_format.ZEICHEN``
    if d.exec(): d.werte()                           # dasselbe dict; ``zu_format(werte)`` macht ein QTextCharFormat daraus

Aufbau wie in der Vorlage: Schriftart, Schriftschnitt und Größe für asiatischen Text, für westlichen Text und für komplexe Schriftzeichen; Schriftfarbe,
Unterstreichung (mit Farbe), Betonungszeichen; Effekte (durchgestrichen, doppelt durchgestrichen, hoch-/tiefgestellt, Kapitälchen, Großbuchstaben,
ausgeblendet); Vorschau; „Standard …“ und „Texteffekte …“. Der zweite Reiter hat den Zeichenabstand.

Das Fenster formatiert nichts selbst: Der Editor (Start ▸ Schriftart ↘) und das Fenster „Neue Formatvorlage“ rufen es mit ihren Werten auf und tun
mit dem Ergebnis, was zu ihnen gehört. Schrift für asiatische und komplexe Zeichen steht in der Familienliste hinter der westlichen Schrift: Qt nimmt sie
für Zeichen, die die erste Schrift nicht hat.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QTextBlockFormat
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFontComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.linien import linien_symbol
from lunivo_writer.ui.baukasten.mass_feld import _PT_MM, EinheitFeld, spin
from lunivo_writer.ui.baukasten.text_format import BETONUNG, UNTERSTREICHUNG, ZEICHEN, groesse_feld, zeichne_absaetze, zu_format

SCHNITTE = ("Regulär", "Kursiv", "Fett", "Fett Kursiv")
_THEMA = {"+Textkörper": "", "+Überschrift": "", "+Textkörper asiatisch": "", "+Überschrift asiatisch": "", "+Textkörper komplex": "", "+Überschrift komplex": ""}


def zeichen_waehlen(parent, zeichen: dict | None) -> dict | None:
    """Das Schriftart-Fenster für Nummern und Vorlagen. → die gewählten Werte (alle Felder von ``ZEICHEN``) oder None bei „Abbrechen“.
    Wer es aufruft, übernimmt das Ergebnis."""
    d = SchriftartDialog(parent, {**ZEICHEN, **(zeichen or {})}, umfang="vorlage")
    return d.werte() if d.exec() else None


def _schrift_combo(thema: tuple[str, ...] = ()) -> QFontComboBox:
    """Schriftauswahl; ``thema``: Einträge wie „+Textkörper“ davor (die Vorgabe des Dokuments, hier: keine bestimmte Schrift)."""
    c = QFontComboBox(); c.setEditable(True)
    for i, t in enumerate(thema):
        c.insertItem(i, t)
    c.setMinimumWidth(200)
    return c


def _schnitt_combo() -> QComboBox:
    c = QComboBox(); c.setEditable(True); c.addItems(SCHNITTE); c.setMinimumWidth(110)
    return c


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
class SchriftartDialog(PanelFaehig, QDialog):
    def __init__(self, parent=None, werte: dict | None = None, *, umfang: str = "text"):
        super().__init__(parent)
        self.setWindowTitle("Schriftart"); self.resize(504, 721)
        self.umfang = umfang
        w = {**ZEICHEN, **(werte or {})}
        v = QVBoxLayout(self)
        self.reiter = QTabWidget(); v.addWidget(self.reiter, 1)
        # ---- Karteireiter „Schriftart“
        s = QWidget(); g = QGridLayout(s); g.setHorizontalSpacing(12); g.setVerticalSpacing(4)
        self.asien, self.schnitt_asien, self.groesse_asien = _schrift_combo(("+Überschrift asiatisch", "+Textkörper asiatisch")), _schnitt_combo(), groesse_feld(breite=90)
        self.schrift, self.schnitt, self.groesse = _schrift_combo(("+Überschrift", "+Textkörper")), _schnitt_combo(), groesse_feld(breite=90)
        self.komplex, self.schnitt_komplex, self.groesse_komplex = _schrift_combo(("+Überschrift komplex", "+Textkörper komplex")), _schnitt_combo(), groesse_feld(breite=90)
        zeile = 0
        for kopf, felder in (("Schriftart für asiatischen Text:", (self.asien, self.schnitt_asien, self.groesse_asien)),
                             ("Schriftart für westlichen Text:", (self.schrift, self.schnitt, self.groesse))):
            for i, t in enumerate((kopf, "Schriftschnitt:", "Größe:")):
                g.addWidget(QLabel(t), zeile, i)
            for i, f in enumerate(felder):
                g.addWidget(f, zeile + 1, i)
            zeile += 2
        g.addWidget(QLabel("Komplexe Schriftzeichen"), zeile, 0, 1, 3); zeile += 1
        for i, t in enumerate(("Schriftart:", "Schriftschnitt:", "Größe:")):
            g.addWidget(QLabel(t), zeile, i)
        for i, f in enumerate((self.komplex, self.schnitt_komplex, self.groesse_komplex)):
            g.addWidget(f, zeile + 1, i)
        zeile += 2
        g.addWidget(QLabel("Alle Texte"), zeile, 0, 1, 3); zeile += 1
        alle = QWidget(); ah = QGridLayout(alle); ah.setContentsMargins(0, 0, 0, 0); ah.setHorizontalSpacing(12)
        self.farbe = FarbFeld(w["farbe"], "Schriftfarbe", keine_text="Automatisch")
        self.unter = QComboBox(); self.unter.setIconSize(QSize(70, 14))
        from lunivo_writer.editor.textfx import unter_symbol
        self.unter.setIconSize(QSize(70, 16))
        for k, name in UNTERSTREICHUNG:
            self.unter.addItem(unter_symbol(k, (70, 16), "#e6e9ec") if k and k != "woerter" else QIcon(), name if k in ("", "woerter") else "", k)
        self.unterfarbe = FarbFeld(w["unterfarbe"], "Farbe der Unterstreichung", keine_text="Automatisch")
        self.betonung = QComboBox()
        for k, name in BETONUNG:
            self.betonung.addItem(name, k)
        for i, (t, wd) in enumerate((("Schriftfarbe:", self.farbe), ("Unterstreichung:", self.unter), ("Farbe:", self.unterfarbe), ("Betonungszeichen:", self.betonung))):
            ah.addWidget(QLabel(t), 0, i); ah.addWidget(wd, 1, i)
        g.addWidget(alle, zeile, 0, 1, 3); zeile += 1
        self.effekte = QGroupBox("Effekte"); eg = QGridLayout(self.effekte)
        namen = (("durch", "Durchgestrichen"), ("doppelt", "Doppelt durchgestrichen"), ("hoch", "Hochgestellt"), ("tief", "Tiefgestellt"),
                 ("kapital", "Kapitälchen"), ("gross", "Großbuchstaben"), ("versteckt", "Ausgeblendet"))
        self.cb = {k: QCheckBox(t) for k, t in namen}
        for i, (k, _t) in enumerate(namen):
            eg.addWidget(self.cb[k], i % 4 if i < 4 else i - 4, 0 if i < 4 else 1)
        g.addWidget(self.effekte, zeile, 0, 1, 3)
        g.setColumnStretch(0, 3); g.setColumnStretch(1, 2); g.setColumnStretch(2, 1)
        self.reiter.addTab(s, "Schriftart")
        # ---- Karteireiter „Zeichenabstand“
        z = QWidget(); zg = QGridLayout(z); zg.setHorizontalSpacing(12); zg.setVerticalSpacing(8)
        self.skala = QComboBox(); self.skala.setEditable(True); self.skala.addItems(["200%", "150%", "100%", "90%", "80%", "66%", "50%", "33%"])
        self.abstand_art = QComboBox(); self.abstand_art.addItems(["Normal", "Erweitert", "Schmal"])
        self.abstand_wert = EinheitFeld(0.0, 0.0, 20 * _PT_MM, ("mm", "cm", "in", "pt"), "pt", leer_bei_null=True)
        self.pos_art = QComboBox(); self.pos_art.addItems(["Normal", "Höher", "Tiefer"])
        self.pos_wert = EinheitFeld(0.0, 0.0, 100 * _PT_MM, ("mm", "cm", "in", "pt"), "pt", leer_bei_null=True)
        self.kerning = QCheckBox("Unterschneidung ab:"); self.kern_ab = spin(0.0, 0.0, 200.0, "", 0.5, 1)
        self.raster = QCheckBox("Bei Dokumentrasterdefinition am Raster ausrichten")
        zg.addWidget(QLabel("Skalieren:"), 0, 0); zg.addWidget(self.skala, 0, 1)
        zg.addWidget(QLabel("Abstand:"), 1, 0); zg.addWidget(self.abstand_art, 1, 1); zg.addWidget(QLabel("Von:"), 1, 2); zg.addWidget(self.abstand_wert, 1, 3)
        zg.addWidget(QLabel("Position:"), 2, 0); zg.addWidget(self.pos_art, 2, 1); zg.addWidget(QLabel("Von:"), 2, 2); zg.addWidget(self.pos_wert, 2, 3)
        zg.addWidget(self.kerning, 3, 0, 1, 2); zg.addWidget(self.kern_ab, 3, 2); zg.addWidget(QLabel("Punkte und größer"), 3, 3)
        zg.addWidget(self.raster, 4, 0, 1, 4)
        zg.setRowStretch(5, 1); zg.setColumnStretch(3, 1)
        self.reiter.addTab(z, "Zeichenabstand")
        # ---- Vorschau, Hinweis, Knöpfe
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 92); v.addWidget(self.vorschau)
        self._w = dict(ZEICHEN)
        self.hinweis = QLabel(); self.hinweis.setWordWrap(True); self.hinweis.setStyleSheet("color: palette(mid); font-size: 9pt;")
        v.addWidget(self.hinweis)
        self.standard_knopf = QPushButton("Standard …"); self.standard_knopf.setToolTip("Diese Schrift für neue Dokumente merken")
        self.standard_knopf.clicked.connect(self._standard)
        self.effekt_knopf = QPushButton("Texteffekte …"); self.effekt_knopf.clicked.connect(self._texteffekte)
        fussleiste(self, v, self.standard_knopf, self.effekt_knopf)
        if umfang == "vorlage":                                     # in der Formatvorlage hat „Format ▸ Texteffekte …“ ihren eigenen Platz
            self.effekt_knopf.setVisible(False); self.standard_knopf.setVisible(False)
        self._effekt = None
        self._als_standard = False
        self.setze(w)
        for sig in (self.asien.currentTextChanged, self.schrift.currentTextChanged, self.komplex.currentTextChanged,
                    self.schnitt_asien.currentTextChanged, self.schnitt.currentTextChanged, self.schnitt_komplex.currentTextChanged,
                    self.groesse_asien.currentTextChanged, self.groesse.currentTextChanged, self.groesse_komplex.currentTextChanged,
                    self.farbe.farbeGeaendert, self.unter.currentIndexChanged, self.unterfarbe.farbeGeaendert, self.betonung.currentIndexChanged,
                    self.abstand_art.currentIndexChanged, self.abstand_wert.valueChanged, self.kerning.toggled, self.skala.currentTextChanged,
                    self.pos_art.currentIndexChanged, self.pos_wert.valueChanged, self.kern_ab.valueChanged, self.raster.toggled):
            sig.connect(lambda *_: self._neu())
        for c in self.cb.values():
            c.toggled.connect(lambda *_: self._neu())
        for a, b in (("hoch", "tief"), ("tief", "hoch"), ("kapital", "gross"), ("gross", "kapital"), ("durch", "doppelt"), ("doppelt", "durch")):
            self.cb[a].toggled.connect(lambda an, b=b: an and self.cb[b].setChecked(False))
        self._neu()

    # ---- Werte
    @staticmethod
    def _schnitt_setzen(c: QComboBox, fett: bool, kursiv: bool) -> None:
        c.setCurrentText("Fett Kursiv" if fett and kursiv else "Fett" if fett else "Kursiv" if kursiv else "Regulär")

    @staticmethod
    def _schnitt_lesen(t: str) -> tuple[bool, bool]:
        t = t.lower()
        return "fett" in t, "kursiv" in t

    @staticmethod
    def _groesse_lesen(t: str) -> float:
        try:
            return float(t.replace(",", "."))
        except ValueError:
            return 0.0

    @staticmethod
    def _groesse_setzen(c: QComboBox, g: float) -> None:
        c.setCurrentText(f"{g:g}".replace(".", ",") if g else "")

    def setze(self, w: dict) -> None:
        self._schrift_gesetzt = bool(w["schrift"])
        self.schrift.setCurrentText(w["schrift"] or "+Textkörper")
        self.asien.setCurrentText(w["schrift_asien"] or "+Textkörper asiatisch"); self.komplex.setCurrentText(w["schrift_komplex"] or "+Textkörper komplex")
        self._schnitt_setzen(self.schnitt, w["fett"], w["kursiv"])
        self.schnitt_asien.setCurrentText(w["schnitt_asien"] or "Regulär"); self.schnitt_komplex.setCurrentText(w["schnitt_komplex"] or "Regulär")
        self._groesse_setzen(self.groesse, w["groesse"]); self._groesse_setzen(self.groesse_asien, w["groesse_asien"] or w["groesse"])
        self._groesse_setzen(self.groesse_komplex, w["groesse_komplex"] or w["groesse"])
        self.unter.setCurrentIndex(max(0, self.unter.findData(w["unter"])))
        self.betonung.setCurrentIndex(max(0, self.betonung.findData(w["betonung"])))
        for k, c in self.cb.items():
            c.setChecked(bool(w.get(k)))
        a = w["abstand"]
        self.abstand_art.setCurrentIndex(0 if not a else 1 if a > 0 else 2)
        self.abstand_wert.setValue(abs(a) * _PT_MM)
        p_ = w["position"]
        self.pos_art.setCurrentIndex(0 if not p_ else 1 if p_ > 0 else 2); self.pos_wert.setValue(abs(p_) * _PT_MM)
        self.skala.setCurrentText(f"{w['skala']:g}%")
        self.kerning.setChecked(w["kern_ab"] > 0); self.kern_ab.setValue(w["kern_ab"]); self.raster.setChecked(bool(w["raster"]))
        self.farbe.setFarbe(w["farbe"]); self.unterfarbe.setFarbe(w["unterfarbe"])

    def werte(self) -> dict:
        fett, kursiv = self._schnitt_lesen(self.schnitt.currentText())
        a = {0: 0.0, 1: 1.0, 2: -1.0}[self.abstand_art.currentIndex()] * self.abstand_wert.value() / _PT_MM
        pos = {0: 0.0, 1: 1.0, 2: -1.0}[self.pos_art.currentIndex()] * self.pos_wert.value() / _PT_MM
        name = self.schrift.currentText().strip()
        w = {"schrift": "" if (name in _THEMA or not name or not self._schrift_gesetzt) else name, "fett": fett, "kursiv": kursiv,
             "groesse": self._groesse_lesen(self.groesse.currentText()), "farbe": self.farbe.farbe, "unter": self.unter.currentData() or "",
             "unterfarbe": self.unterfarbe.farbe, "abstand": a, "kerning": True, "betonung": self.betonung.currentData() or "",
             "position": pos, "skala": self._groesse_lesen(self.skala.currentText().replace("%", "")) or 100.0, "raster": self.raster.isChecked(),
             "kern_ab": self.kern_ab.value() if self.kerning.isChecked() else 0.0}
        for art, schrift, schnitt, gr in (("asien", self.asien, self.schnitt_asien, self.groesse_asien), ("komplex", self.komplex, self.schnitt_komplex, self.groesse_komplex)):
            t = schrift.currentText().strip()
            w[f"schrift_{art}"] = "" if t in _THEMA else t
            w[f"schnitt_{art}"] = "" if schnitt.currentText() == "Regulär" else schnitt.currentText()
            w[f"groesse_{art}"] = 0.0 if self._groesse_lesen(gr.currentText()) == w["groesse"] else self._groesse_lesen(gr.currentText())
        w.update({k: c.isChecked() for k, c in self.cb.items()})
        if self._effekt is not None:                       # nur wenn im Fenster „Texteffekte“ etwas geändert wurde
            w["effekt"] = self._effekt
        if self._als_standard:
            w["als_standard"] = True
        return w

    _schrift_gesetzt = False

    def _texteffekte(self) -> None:
        from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        d = TexteffektDialog(self, {**(self._effekt or {}), "farbe": self.farbe.farbe})

        def fertig() -> None:
            self._effekt = d.werte()
            self.farbe.setFarbe(self._effekt["farbe"]); self._neu()
        zeige_unter(self, d, fertig)

    def _standard(self) -> None:
        """„Standard …“: diese Schrift gilt künftig für neue Dokumente (der Aufrufer speichert sie)."""
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Standard", "Die gewählte Schrift als Standard für neue Dokumente festlegen?") == QMessageBox.Yes:
            self._als_standard = True
            self.accept()

    def _neu(self) -> None:
        self._schrift_gesetzt = True
        self.unterfarbe.setEnabled(bool(self.unter.currentData()))
        self.abstand_wert.setEnabled(self.abstand_art.currentIndex() != 0); self.pos_wert.setEnabled(self.pos_art.currentIndex() != 0)
        self.kern_ab.setEnabled(self.kerning.isChecked())
        w = self.werte()
        fam = w["schrift"] or self.schrift.currentText()
        self.hinweis.setText("" if (not w["schrift"] or fam in QFontDatabase.families()) else
                             "Diese Schriftart wurde nicht installiert. Es wird die ähnlichste verfügbare Schriftart zum Drucken verwendet.")
        self._w = w
        self.vorschau.update()

    def _male(self, p, rect) -> None:
        w = self._w
        f = zu_format(w)
        f.setFontPointSize(min(26.0, max(7.0, w.get("groesse") or 12.0)))
        if not f.fontFamilies():
            f.setFontFamilies(["Liberation Sans"])
        if not w.get("farbe"):
            f.setForeground(QColor("#111417"))
        bf = QTextBlockFormat(); bf.setAlignment(Qt.AlignHCenter)
        zeichne_absaetze(p, rect, [(bf, f, "Lunivo entspannt die Arbeit AaBbCc")], mittig=True)
