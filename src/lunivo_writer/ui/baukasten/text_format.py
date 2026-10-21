"""Textformat-Bausteine: Schriftname, Größe, Fett, Kursiv, Ausrichtung, Zeilenabstand — so wie im Band (Start ▸ Schriftart, Absatz).

Das Band und jedes Fenster, das Text formatiert (Neue Formatvorlage, später Zeichen- und Absatzfenster), bauen ihre Felder hier;
niemand baut sie nach. Die Bausteine kennen den Editor nicht: ``TextFormatLeiste`` meldet Werte, der Aufrufer tut damit, was er will.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat,
)
from PySide6.QtWidgets import QApplication, QButtonGroup, QComboBox, QFontComboBox, QFrame, QHBoxLayout, QToolButton, QWidget

from lunivo_writer.ui.widgets import icons

GROESSEN = (8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72)
AUSRICHTUNG = (("links", "Linksbündig"), ("mitte", "Zentriert"), ("rechts", "Rechtsbündig"), ("block", "Blocksatz"))
ZEILENABSTAND = ((1.0, "Einfach"), (1.5, "1,5 Zeilen"), (2.0, "Doppelt"))


def schrift_feld(combo: QComboBox | None = None, breite: int = 150) -> QComboBox:
    """Das Feld für den Schriftnamen (im Band mit Live-Vorschau, im Fenster ohne)."""
    c = combo if combo is not None else QFontComboBox()
    c.setFixedWidth(breite)
    return c


def groesse_feld(combo: QComboBox | None = None, breite: int = 62) -> QComboBox:
    """Das Feld für die Schriftgröße: zum Tippen und mit der Liste der üblichen Größen."""
    c = combo if combo is not None else QComboBox()
    c.setEditable(True)
    c.setFixedWidth(breite)
    c.addItems([f"{g:g}" for g in GROESSEN])
    return c


def text_knopf(symbol: str, tipp: str) -> QToolButton:
    """F, K oder U als Knopf zum Ein-/Ausschalten, in dem Schnitt, den er bedeutet (wie im Band)."""
    k = QToolButton()
    k.setAutoRaise(True); k.setCheckable(True); k.setText(symbol); k.setToolTip(tipp); k.setMinimumWidth(28)
    f = k.font()
    f.setBold(symbol == "F"); f.setItalic(symbol == "K"); f.setUnderline(symbol == "U")
    k.setFont(f)
    return k


def ausrichtung_knoepfe() -> dict[str, QToolButton]:
    """Linksbündig, Zentriert, Rechtsbündig, Blocksatz — gleiche Symbole und Namen wie im Band; immer höchstens einer gewählt."""
    gruppe = {}
    for schl, name in AUSRICHTUNG:
        k = QToolButton(); k.setAutoRaise(True); k.setCheckable(True); k.setToolTip(name)
        k.setIcon(icons.icon(schl, 18)); k.setIconSize(QSize(18, 18))
        gruppe[schl] = k
    return gruppe


def _symbol(zeichne) -> QIcon:
    pm = QPixmap(20, 20); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QApplication.palette().color(QPalette.ButtonText), 1.6, Qt.SolidLine, Qt.RoundCap))
    zeichne(p)
    p.end()
    return QIcon(pm)


def _zeilen_symbol(abstand: float) -> QIcon:
    def z(p):
        n = 3
        for i in range(n):
            y = 4 + i * (6 + (abstand - 1) * 2.4)
            p.drawLine(7, int(y), 18, int(y))
        p.drawLine(3, 4, 3, int(4 + (n - 1) * (6 + (abstand - 1) * 2.4))); p.drawLine(1, 6, 3, 4); p.drawLine(5, 6, 3, 4)
    return _symbol(z)


def _abstand_symbol(mehr: bool) -> QIcon:
    def z(p):
        p.drawLine(3, 4, 17, 4); p.drawLine(3, 16, 17, 16)
        if mehr:
            p.drawLine(10, 8, 10, 12); p.drawLine(8, 10, 10, 8); p.drawLine(12, 10, 10, 8); p.drawLine(8, 10, 12, 10)
        else:
            p.drawLine(8, 10, 12, 10)
    return _symbol(z)


def _einzug_symbol(mehr: bool) -> QIcon:
    def z(p):
        for y in (4, 16):
            p.drawLine(3, y, 17, y)
        p.drawLine(10, 8, 17, 8); p.drawLine(10, 12, 17, 12)
        x0, x1 = (3, 7) if mehr else (7, 3)
        p.drawLine(x0, 10, x1, 10); p.drawLine(x1, 10, x1 + (-2 if mehr else 2), 8); p.drawLine(x1, 10, x1 + (-2 if mehr else 2), 12)
    return _symbol(z)


class TextFormatLeiste(QWidget):
    """Zwei Zeilen wie im Band: Schrift, Größe, Fett, Kursiv · Ausrichtung (und mit ``absatz=True`` Zeilenabstand, Absatzabstand und
    Einzug). Meldet jede Änderung mit ``geaendert``; ``werte()`` und ``setze()`` lesen und schreiben alles auf einmal."""

    geaendert = Signal()
    SCHRITT_ABSTAND = 6.0        # pt je Klick auf „Absatzabstand“
    SCHRITT_EINZUG = 10.0        # mm je Klick auf „Einzug“

    def __init__(self, parent=None, *, absatz: bool = True):
        super().__init__(parent)
        from PySide6.QtWidgets import QVBoxLayout
        self.vor = self.nach = self.einzug = 0.0
        self.zeilen = 0.0
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(4)
        z1 = QHBoxLayout(); z1.setSpacing(2); v.addLayout(z1)
        self.schrift = schrift_feld(); self.groesse = groesse_feld()
        self.groesse.setCurrentIndex(-1)
        self.fett, self.kursiv = text_knopf("F", "Fett"), text_knopf("K", "Kursiv")
        for w in (self.schrift, self.groesse):
            z1.addWidget(w)
        z1.addSpacing(6); z1.addWidget(self.fett); z1.addWidget(self.kursiv); z1.addStretch(1)
        z2 = QHBoxLayout(); z2.setSpacing(2); v.addLayout(z2)
        self.ausr = ausrichtung_knoepfe()
        self._gruppe = QButtonGroup(self); self._gruppe.setExclusive(False)
        for schl, k in self.ausr.items():
            z2.addWidget(k)
            k.clicked.connect(lambda an, s=schl: self._ausrichtung(s, an))
        self.zeilen_knoepfe: dict[float, QToolButton] = {}
        self.knoepfe_absatz: list[QToolButton] = []
        if absatz:
            z2.addWidget(self._trenner())
            for f, name in ZEILENABSTAND:
                k = QToolButton(); k.setAutoRaise(True); k.setCheckable(True); k.setToolTip(name); k.setIcon(_zeilen_symbol(f)); k.setIconSize(QSize(20, 20))
                k.clicked.connect(lambda an, f=f: self._zeilenabstand(f, an))
                self.zeilen_knoepfe[f] = k; z2.addWidget(k)
            z2.addWidget(self._trenner())
            for name, mehr, fn in (("Absatzabstand vergrößern", True, lambda: self._abstand(+self.SCHRITT_ABSTAND)),
                                   ("Absatzabstand verkleinern", False, lambda: self._abstand(-self.SCHRITT_ABSTAND))):
                k = self._aktion(name, _abstand_symbol(mehr), fn); z2.addWidget(k)
            z2.addWidget(self._trenner())
            for name, mehr, fn in (("Einzug verkleinern", False, lambda: self._einzug(-self.SCHRITT_EINZUG)),
                                   ("Einzug vergrößern", True, lambda: self._einzug(+self.SCHRITT_EINZUG))):
                k = self._aktion(name, _einzug_symbol(mehr), fn); z2.addWidget(k)
        z2.addStretch(1)
        self.schrift.currentFontChanged.connect(lambda _f: self.geaendert.emit())
        self.groesse.editTextChanged.connect(lambda _t: self.geaendert.emit())
        self.fett.toggled.connect(lambda _a: self.geaendert.emit()); self.kursiv.toggled.connect(lambda _a: self.geaendert.emit())

    @staticmethod
    def _trenner() -> QFrame:
        t = QFrame(); t.setFrameShape(QFrame.VLine); t.setFrameShadow(QFrame.Sunken)
        return t

    @staticmethod
    def _aktion(name: str, symbol: QIcon, fn) -> QToolButton:
        k = QToolButton(); k.setAutoRaise(True); k.setToolTip(name); k.setIcon(symbol); k.setIconSize(QSize(20, 20))
        k.clicked.connect(lambda _c=False: fn())
        return k

    # ---- Bedienung
    def _ausrichtung(self, schl: str, an: bool) -> None:
        for s, k in self.ausr.items():
            k.setChecked(s == schl and an)
        self.geaendert.emit()

    def _zeilenabstand(self, f: float, an: bool) -> None:
        self.zeilen = f if an else 0.0
        self._zeige_zeilen()
        self.geaendert.emit()

    def _zeige_zeilen(self) -> None:
        for f, k in self.zeilen_knoepfe.items():
            k.setChecked(abs(f - self.zeilen) < 0.01)

    def _abstand(self, delta: float) -> None:
        self.vor, self.nach = max(0.0, self.vor + delta), max(0.0, self.nach + delta)
        self.geaendert.emit()

    def _einzug(self, delta: float) -> None:
        self.einzug = max(0.0, self.einzug + delta)
        self.geaendert.emit()

    # ---- Werte
    def werte(self) -> dict:
        try:
            gr = float(self.groesse.currentText().replace(",", "."))
        except ValueError:
            gr = 0.0
        return {"schrift": self.schrift.currentFont().family() if self._schrift_gesetzt else "", "groesse": gr,
                "fett": self.fett.isChecked(), "kursiv": self.kursiv.isChecked(),
                "ausr": next((s for s, k in self.ausr.items() if k.isChecked()), ""),
                "vor": self.vor, "nach": self.nach, "einzug": self.einzug, "zeilen": self.zeilen}

    _schrift_gesetzt = False

    def setze(self, d: dict) -> None:
        """Alle Felder auf die Werte einer Vorlage stellen (ohne ``geaendert`` zu melden)."""
        for w in (self.schrift, self.groesse, self.fett, self.kursiv):
            w.blockSignals(True)
        self._schrift_gesetzt = bool(d.get("schrift"))
        if d.get("schrift"):
            self.schrift.setCurrentFont(QFont(d["schrift"]))
        g = d.get("groesse") or 0
        self.groesse.setCurrentText(f"{g:g}" if g else "")
        self.fett.setChecked(bool(d.get("fett"))); self.kursiv.setChecked(bool(d.get("kursiv")))
        for s, k in self.ausr.items():
            k.setChecked(d.get("ausr") == s)
        self.vor, self.nach = float(d.get("vor") or 0), float(d.get("nach") or 0)
        self.einzug, self.zeilen = float(d.get("einzug") or 0), float(d.get("zeilen") or 0)
        self._zeige_zeilen()
        for w in (self.schrift, self.groesse, self.fett, self.kursiv):
            w.blockSignals(False)


# ---- Zeichenformat <-> Werte, gemeinsam für das Fenster „Schriftart“ und den Editor --------------------------------------------
UNTERSTREICHUNG = (("", "(Keine)"), ("einfach", "Einfach"), ("gepunktet", "Gepunktet"), ("gestrichelt", "Gestrichelt"),
                   ("strichpunkt", "Strich-Punkt"), ("strichpunktpunkt", "Strich-Punkt-Punkt"), ("wellig", "Wellenlinie"))
_UNTER_QT = {"einfach": QTextCharFormat.SingleUnderline, "gepunktet": QTextCharFormat.DotLine, "gestrichelt": QTextCharFormat.DashUnderline,
             "strichpunkt": QTextCharFormat.DashDotLine, "strichpunktpunkt": QTextCharFormat.DashDotDotLine, "wellig": QTextCharFormat.WaveUnderline}
ZEICHEN = {"schrift": "", "fett": False, "kursiv": False, "groesse": 0.0, "farbe": "", "unter": "", "unterfarbe": "",
           "durch": False, "hoch": False, "tief": False, "kapital": False, "gross": False, "versteckt": False,
           "abstand": 0.0, "kerning": True}


def zu_format(w: dict) -> QTextCharFormat:
    """Die Werte eines Zeichenfensters als Zeichenformat (zum Anwenden im Editor und für Vorschauen)."""
    f = QTextCharFormat()
    if w.get("schrift"):
        f.setFontFamilies([w["schrift"]])
    f.setFontWeight(QFont.Bold if w.get("fett") else QFont.Normal)
    f.setFontItalic(bool(w.get("kursiv")))
    if w.get("groesse"):
        f.setFontPointSize(float(w["groesse"]))
    if w.get("farbe"):
        f.setForeground(QColor(w["farbe"]))
    f.setUnderlineStyle(_UNTER_QT.get(w.get("unter"), QTextCharFormat.NoUnderline))
    if w.get("unter") and w.get("unterfarbe"):
        f.setUnderlineColor(QColor(w["unterfarbe"]))
    f.setFontStrikeOut(bool(w.get("durch")))
    f.setVerticalAlignment(QTextCharFormat.AlignSuperScript if w.get("hoch") else QTextCharFormat.AlignSubScript if w.get("tief")
                           else QTextCharFormat.AlignNormal)
    f.setFontCapitalization(QFont.AllUppercase if w.get("gross") else QFont.SmallCaps if w.get("kapital") else QFont.MixedCase)
    f.setFontLetterSpacingType(QFont.AbsoluteSpacing)
    f.setFontLetterSpacing(float(w.get("abstand") or 0) / 0.75)
    f.setFontKerning(bool(w.get("kerning", True)))
    return f


def aus_format(cf: QTextCharFormat, standard_schrift: str = "", standard_groesse: float = 0.0) -> dict:
    """Die Werte eines Zeichenformats (zum Vorbelegen eines Zeichenfensters)."""
    w = dict(ZEICHEN)
    fam = cf.fontFamilies()
    w["schrift"] = (fam[0] if fam else "") or standard_schrift
    w["fett"], w["kursiv"] = cf.fontWeight() >= 600, cf.fontItalic()
    w["groesse"] = cf.fontPointSize() or standard_groesse
    if cf.hasProperty(QTextFormat.ForegroundBrush) and cf.foreground().style() != Qt.NoBrush:
        w["farbe"] = cf.foreground().color().name()
    w["unter"] = next((k for k, q in _UNTER_QT.items() if cf.underlineStyle() == q), "")
    if w["unter"] and cf.underlineColor().isValid():
        w["unterfarbe"] = cf.underlineColor().name()
    w["durch"] = cf.fontStrikeOut()
    w["hoch"] = cf.verticalAlignment() == QTextCharFormat.AlignSuperScript
    w["tief"] = cf.verticalAlignment() == QTextCharFormat.AlignSubScript
    w["kapital"] = cf.fontCapitalization() == QFont.SmallCaps
    w["gross"] = cf.fontCapitalization() == QFont.AllUppercase
    w["abstand"] = round(cf.fontLetterSpacing() * 0.75, 1) if cf.fontLetterSpacingType() == QFont.AbsoluteSpacing else 0.0
    w["kerning"] = cf.fontKerning() if cf.hasProperty(QTextFormat.FontKerning) else True       # ohne Angabe gilt: an
    return w


def zeichne_absaetze(p: QPainter, rect, absaetze: list[tuple[QTextBlockFormat, QTextCharFormat, str]], mittig: bool = False) -> None:
    """Absätze (Absatzformat, Zeichenformat, Text) in ein Rechteck zeichnen — die Vorschau der Formatierungsfenster."""
    doc = QTextDocument(); doc.setDocumentMargin(0); doc.setTextWidth(rect.width())
    c = QTextCursor(doc)
    for i, (bf, cf, text) in enumerate(absaetze):
        c.setBlockFormat(bf) if i == 0 else c.insertBlock(bf)
        c.setCharFormat(cf); c.insertText(text)
    p.save()
    p.setClipRect(rect)
    p.translate(rect.left(), rect.top() + (max(0.0, (rect.height() - doc.size().height()) / 2) if mittig else 0))
    doc.drawContents(p, QRectF(0, 0, rect.width(), rect.height()))
    p.restore()
