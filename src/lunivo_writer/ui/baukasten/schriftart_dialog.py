"""Das Fenster „Schriftart“ (Karteireiter Schriftart und Zeichenabstand) als Baustein.

    d = SchriftartDialog(parent, werte, umfang="text")      # umfang="vorlage": nur Schrift, Schnitt, Größe, Farbe
    if d.exec(): d.werte()                                  # dict, siehe ``ZEICHEN``; ``zu_format(werte)`` macht ein QTextCharFormat daraus

Das Fenster formatiert nichts selbst: Der Editor (Start ▸ Schriftart ↘) und das Fenster „Neue Formatvorlage“ rufen es mit ihren
Werten auf und tun mit dem Ergebnis, was zu ihnen gehört. Nur, was Lunivo wirklich zeichnen und speichern kann, steht darin.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QTextBlockFormat
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.linien import linien_symbol
from lunivo_writer.ui.baukasten.mass_feld import spin
from lunivo_writer.ui.baukasten.text_format import GROESSEN, UNTERSTREICHUNG, ZEICHEN, schrift_feld, zeichne_absaetze, zu_format

SCHNITTE = ("Regulär", "Kursiv", "Fett", "Fett Kursiv")


class _ListeMitFeld(QWidget):
    """Ein Eingabefeld mit der Liste darunter (Schriftschnitt, Größe): Wählen oder Tippen."""
    geaendert = Signal()

    def __init__(self, eintraege, zeilen: int = 4):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        self.feld = QLineEdit()
        self.liste = QListWidget(); self.liste.addItems(list(eintraege))
        self.liste.setFixedHeight(zeilen * 22 + 4)
        v.addWidget(self.feld); v.addWidget(self.liste)
        self.liste.currentTextChanged.connect(self._gewaehlt)
        self.feld.textEdited.connect(self._getippt)

    def _gewaehlt(self, t: str) -> None:
        if t and t != self.feld.text():
            self.feld.setText(t); self.geaendert.emit()

    def _getippt(self, t: str) -> None:
        for i in range(self.liste.count()):
            if self.liste.item(i).text().lower() == t.lower():
                self.liste.blockSignals(True); self.liste.setCurrentRow(i); self.liste.blockSignals(False)
                break
        self.geaendert.emit()

    def setze(self, t: str) -> None:
        self.feld.setText(t)
        for i in range(self.liste.count()):
            if self.liste.item(i).text() == t:
                self.liste.blockSignals(True); self.liste.setCurrentRow(i); self.liste.blockSignals(False)
                break

    def text(self) -> str:
        return self.feld.text().strip()


class SchriftartDialog(QDialog):
    def __init__(self, parent=None, werte: dict | None = None, *, umfang: str = "text"):
        super().__init__(parent)
        self.setWindowTitle("Schriftart")
        self.umfang = umfang
        w = {**ZEICHEN, **(werte or {})}
        v = QVBoxLayout(self)
        self.reiter = QTabWidget(); v.addWidget(self.reiter, 1)
        # ---- Karteireiter „Schriftart“
        s = QWidget(); g = QGridLayout(s); g.setHorizontalSpacing(12)
        for i, t in enumerate(("Schriftart:", "Schriftschnitt:", "Größe:")):
            g.addWidget(QLabel(t), 0, i)
        self.schrift = schrift_feld(breite=250)
        self.schnitt = _ListeMitFeld(SCHNITTE); self.groesse = _ListeMitFeld([f"{g:g}".replace(".", ",") for g in GROESSEN])
        g.addWidget(self.schrift, 1, 0, Qt.AlignTop); g.addWidget(self.schnitt, 1, 1); g.addWidget(self.groesse, 1, 2)
        g.setColumnStretch(0, 1)
        g.addWidget(QLabel("Alle Texte"), 2, 0, 1, 3)
        zeile = QWidget(); zh = QGridLayout(zeile); zh.setContentsMargins(0, 0, 0, 0); zh.setHorizontalSpacing(12)
        self.farbe = FarbFeld(w["farbe"], "Schriftfarbe", keine_text="Automatisch")
        self.unter = QComboBox(); self.unter.setIconSize(QSize(70, 14))
        for k, name in UNTERSTREICHUNG:
            self.unter.addItem(linien_symbol(k, QSize(70, 14), "#e6e9ec") if k else linien_symbol("einfach", QSize(1, 14)), name if not k else "", k)
        self.unterfarbe = FarbFeld(w["unterfarbe"], "Farbe der Unterstreichung", keine_text="Automatisch")
        for i, (t, wd) in enumerate((("Schriftfarbe:", self.farbe), ("Unterstreichung:", self.unter), ("Farbe:", self.unterfarbe))):
            zh.addWidget(QLabel(t), 0, i); zh.addWidget(wd, 1, i)
        g.addWidget(zeile, 3, 0, 1, 3)
        self.effekte = QGroupBox("Effekte"); eg = QGridLayout(self.effekte)
        self.cb = {k: QCheckBox(t) for k, t in (("durch", "Durchgestrichen"), ("hoch", "Hochgestellt"), ("tief", "Tiefgestellt"),
                                                ("kapital", "Kapitälchen"), ("gross", "Großbuchstaben"), ("versteckt", "Ausgeblendet"))}
        for i, k in enumerate(("durch", "hoch", "tief", "kapital", "gross", "versteckt")):
            eg.addWidget(self.cb[k], i % 3, i // 3)
        g.addWidget(self.effekte, 4, 0, 1, 3)
        g.setRowStretch(5, 1)
        self.reiter.addTab(s, "Schriftart")
        # ---- Karteireiter „Zeichenabstand“
        z = QWidget(); zg = QGridLayout(z); zg.setHorizontalSpacing(12)
        self.abstand_art = QComboBox(); self.abstand_art.addItems(["Normal", "Erweitert", "Schmal"])
        self.abstand_wert = spin(0.0, 0.0, 20.0, " pt", 0.1)
        self.kerning = QCheckBox("Unterschneidung (Zeichenpaare enger setzen)")
        zg.addWidget(QLabel("Abstand:"), 0, 0); zg.addWidget(self.abstand_art, 0, 1); zg.addWidget(QLabel("Von:"), 0, 2); zg.addWidget(self.abstand_wert, 0, 3)
        zg.addWidget(self.kerning, 1, 0, 1, 4)
        zg.setRowStretch(2, 1); zg.setColumnStretch(4, 1)
        self.reiter.addTab(z, "Zeichenabstand")
        # ---- Vorschau, Hinweis, Knöpfe
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 92); v.addWidget(self.vorschau)
        self._w = dict(ZEICHEN)
        self.hinweis = QLabel(); self.hinweis.setWordWrap(True); self.hinweis.setStyleSheet("color: palette(mid); font-size: 9pt;")
        v.addWidget(self.hinweis)
        zu = QHBoxLayout()
        self.effekt_knopf = QPushButton("Texteffekte …"); self.effekt_knopf.clicked.connect(self._texteffekte)
        zu.addWidget(self.effekt_knopf); zu.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(ok); v.addLayout(zu)
        if umfang == "vorlage":                                     # im Fenster „Neue Formatvorlage“ gibt es nur diese Felder
            for wd in (self.unter, self.unterfarbe, self.effekte, self.kerning, self.abstand_art, self.abstand_wert):
                wd.setVisible(False)
            for i in range(zeile.layout().count()):
                it = zeile.layout().itemAt(i).widget()
                if it is not None and it not in (self.farbe,) and not (isinstance(it, QLabel) and it.text() == "Schriftfarbe:"):
                    it.setVisible(False)
            self.reiter.removeTab(1)
            self.effekt_knopf.setVisible(False)             # eine Vorlage hat ihre eigenen Texteffekte im Menü „Format“
        self._effekt = None
        self.setze(w)
        for sig in (self.schrift.currentFontChanged, self.schnitt.geaendert, self.groesse.geaendert, self.farbe.farbeGeaendert,
                    self.unter.currentIndexChanged, self.unterfarbe.farbeGeaendert, self.abstand_art.currentIndexChanged,
                    self.abstand_wert.valueChanged, self.kerning.toggled):
            sig.connect(lambda *_: self._neu())
        for c in self.cb.values():
            c.toggled.connect(lambda *_: self._neu())
        self.cb["hoch"].toggled.connect(lambda an: an and self.cb["tief"].setChecked(False))
        self.cb["tief"].toggled.connect(lambda an: an and self.cb["hoch"].setChecked(False))
        self.cb["kapital"].toggled.connect(lambda an: an and self.cb["gross"].setChecked(False))
        self.cb["gross"].toggled.connect(lambda an: an and self.cb["kapital"].setChecked(False))
        self._neu()

    def setze(self, w: dict) -> None:
        if w["schrift"]:
            self.schrift.setCurrentFont(QFont(w["schrift"]))
        self.schnitt.setze("Fett Kursiv" if w["fett"] and w["kursiv"] else "Fett" if w["fett"] else "Kursiv" if w["kursiv"] else "Regulär")
        self.groesse.setze(f"{w['groesse']:g}".replace(".", ",") if w["groesse"] else "")
        self.unter.setCurrentIndex(max(0, self.unter.findData(w["unter"])))
        for k, c in self.cb.items():
            c.setChecked(bool(w[k]))
        a = w["abstand"]
        self.abstand_art.setCurrentIndex(0 if not a else 1 if a > 0 else 2)
        self.abstand_wert.setValue(abs(a)); self.kerning.setChecked(bool(w["kerning"]))
        self._schrift_gesetzt = bool(w["schrift"])

    def werte(self) -> dict:
        t = self.schnitt.text().lower()
        try:
            gr = float(self.groesse.text().replace(",", "."))
        except ValueError:
            gr = 0.0
        a = {0: 0.0, 1: 1.0, 2: -1.0}[self.abstand_art.currentIndex()] * self.abstand_wert.value()
        w = {"schrift": self.schrift.currentFont().family() if self._schrift_gesetzt else "", "fett": "fett" in t, "kursiv": "kursiv" in t,
             "groesse": gr, "farbe": self.farbe.farbe, "unter": self.unter.currentData() or "", "unterfarbe": self.unterfarbe.farbe,
             "abstand": a, "kerning": self.kerning.isChecked()}
        w.update({k: c.isChecked() for k, c in self.cb.items()})
        if self._effekt is not None:                       # nur wenn im Fenster „Texteffekte“ etwas geändert wurde
            w["effekt"] = self._effekt
        return w

    def _texteffekte(self) -> None:
        from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
        d = TexteffektDialog(self, {**(self._effekt or {}), "farbe": self.farbe.farbe})
        if d.exec():
            self._effekt = d.werte()
            self.farbe.setFarbe(self._effekt["farbe"]); self._neu()

    _schrift_gesetzt = False

    def _neu(self) -> None:
        self._schrift_gesetzt = True
        self.unterfarbe.setEnabled(bool(self.unter.currentData()))
        self.abstand_wert.setEnabled(self.abstand_art.currentIndex() != 0)
        w = self.werte()
        fam = self.schrift.currentFont().family()
        self.hinweis.setText("" if fam in QFontDatabase.families() else
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
        zeichne_absaetze(p, rect, [(bf, f, "Beispieltext AaBbCc")], mittig=True)
