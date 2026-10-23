"""Gemeinsame Werte der Bausteine."""
from __future__ import annotations

import json
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget
from lunivo_writer.core import paths
from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.ui.baukasten.einklappgruppe import EinklappGruppe

MIN_HOEHE = 32                                      # Mindesthöhe der Bedienelemente (leicht zu treffen)
_ERKLAERUNGEN: dict | None = None


def erklaerung(name: str) -> str:
    """Der Satz zu einer Einstellung (aus resources/daten/optionen_erklaerungen.json); leer, wenn es keinen gibt."""
    global _ERKLAERUNGEN
    if _ERKLAERUNGEN is None:
        try:
            with open(os.path.join(paths.RESSOURCEN, "daten", "optionen_erklaerungen.json"), encoding="utf-8") as fh:
                _ERKLAERUNGEN = json.load(fh)
        except (OSError, ValueError):
            _ERKLAERUNGEN = {}
    n = " ".join(name.split())
    if n in _ERKLAERUNGEN:
        return _ERKLAERUNGEN[n]
    return next((v for k, v in _ERKLAERUNGEN.items() if len(k) >= 8 and (n.startswith(k) or k.startswith(n))), "")


class _Seite(QWidget):
    """Eine Optionenseite: Gruppen mit Zeilen; Werte stehen sofort in den Einstellungen.
    Mit leerem ``titel`` ist sie ein Einbau in eine andere Seite oder ein Fenster: ohne Überschrift und ohne Rand."""
    def __init__(self, fenster, titel: str, offen: list[str] | None = None):
        super().__init__()
        self.w = fenster
        self.s = fenster.settings
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(24, 16, 24, 16) if titel else self.lay.setContentsMargins(0, 0, 0, 0)
        if titel:
            self.lay.addWidget(text_label(titel, fett=True, pt=16, umbruch=False))
        self.gruppe_lay = None
        self.karten: list[_Karte] = []
        self.einklappe: list[EinklappGruppe] = []
        self._offen = offen or []

    def gruppe(self, name: str) -> QFormLayout:
        g = QGroupBox(name.upper())
        g.setProperty("optName", name)
        f = _Karte(g)
        self.karten.append(f)
        self.lay.addWidget(g)
        return f

    def mehr(self, name: str = "Weitere Einstellungen") -> EinklappGruppe:
        """Eingeklappter Bereich am Ende einer Seite; ``unter`` legt Gruppen hinein."""
        e = EinklappGruppe(name)
        self.einklappe.append(e)
        self.lay.addWidget(e)
        return e

    def unter(self, e: EinklappGruppe, name: str = "") -> QFormLayout:
        g = QGroupBox(name.upper())
        g.setProperty("optName", name)
        f = _Karte(g)
        self.karten.append(f)
        e.innen.addWidget(g)
        return f

    def haken(self, f, key, text, std, wirkt=None):
        c = QCheckBox(text)
        c.setProperty("optName", text)
        c.setMinimumHeight(MIN_HOEHE)
        c.setChecked(self.s.get_bool(key, std))

        def geaendert(on):
            self.s.set(key, on)
            if wirkt:
                wirkt(on)
        c.toggled.connect(geaendert)
        self._zeile(f, c, text)
        return c

    @staticmethod
    def _zeile(f, c: QCheckBox, text: str) -> None:
        """Haken in die Gruppe setzen; gibt es einen Erklärsatz, steht er immer sichtbar darunter (nicht nur als QuickInfo)."""
        satz = erklaerung(text)
        if not satz:
            f.addRow(c)
            return
        c.setAccessibleDescription(satz)
        zeile = QWidget(); zeile.setObjectName("optPaar"); zeile.setProperty("optName", text)
        v = QVBoxLayout(zeile); v.setContentsMargins(0, 2, 0, 6); v.setSpacing(0)
        v.addWidget(c)
        hinweis = text_label(satz)
        hinweis.setObjectName("optHinweis")                       # Aussehen steht in STIL (optionen.py): ein Stylesheet statt eines je Zeile
        v.addWidget(hinweis)
        f.addRow(zeile)

    def auswahl(self, f, key, label, werte: list[str], std, wirkt=None):
        c = QComboBox()
        c.setMinimumHeight(MIN_HOEHE)
        c.addItems(werte)
        c.setCurrentText(str(self.s.get(key, std)))

        def geaendert(t):
            self.s.set(key, t)
            if wirkt:
                wirkt(t)
        c.currentTextChanged.connect(geaendert)
        f.addRow(label, c)
        return c

    def wahl(self, f, key, label, eintraege: list[tuple[str, object]], std, wirkt=None):
        """Auswahl mit Anzeigetext und gespeichertem Wert (Text oder Ja/Nein)."""
        c = QComboBox()
        c.setMinimumHeight(MIN_HOEHE)
        for text, wert in eintraege:
            c.addItem(text, wert)
        aktuell = self.s.get_bool(key, std) if isinstance(std, bool) else self.s.get(key, std)
        c.setCurrentIndex(max(0, c.findData(aktuell)))

        def geaendert(_i):
            self.s.set(key, c.currentData())
            if wirkt:
                wirkt(c.currentData())
        c.currentIndexChanged.connect(geaendert)
        f.addRow(label, c)
        return c

    def schalter(self, f, text: str, ist, umschalten):
        """Haken, der den Zustand eines anderen Teils des Programms zeigt und schaltet (Navigationsbereich, Gitternetzlinien …)."""
        c = QCheckBox(text)
        c.setProperty("optName", text)
        c.setMinimumHeight(MIN_HOEHE)
        c.setChecked(bool(ist()))
        c.toggled.connect(lambda on: on != bool(ist()) and umschalten())
        self._zeile(f, c, text)
        return c

    def eingabe(self, key: str, platzhalter: str) -> QLineEdit:
        e = QLineEdit(str(self.s.get(key, "")))
        e.setPlaceholderText(platzhalter)
        e.setProperty("optName", platzhalter)
        e.setAccessibleName(platzhalter)
        e.textChanged.connect(lambda t: self.s.set(key, t))
        return e

    def felder(self, f, eintraege: list[tuple[str, str]], spalten: int = 2):
        """Eingabefelder im Raster, jedes mit seinem Platzhalter als Beschriftung."""
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 6, 0, 6); g.setHorizontalSpacing(10); g.setVerticalSpacing(8)
        for i, (key, platzhalter) in enumerate(eintraege):
            g.addWidget(self.eingabe(key, platzhalter), i // spalten, i % spalten)
        f.addRow(w)

    def pfad(self, f, key: str, text: str, platzhalter: str, wirkt=None):
        """Ordner-Zeile: Beschriftung, darunter Feld und „Wählen …“."""
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0, 6, 0, 8); v.setSpacing(6)
        v.addWidget(QLabel(text))
        h = QHBoxLayout()
        e = self.eingabe(key, platzhalter)
        e.setProperty("optName", text)
        k = QPushButton("Wählen …")

        def waehle():
            from PySide6.QtWidgets import QFileDialog
            ordner = QFileDialog.getExistingDirectory(self, text, e.text() or os.path.expanduser("~"))
            if ordner:
                e.setText(ordner)
        k.clicked.connect(waehle)
        h.addWidget(e, 1); h.addWidget(k)
        v.addLayout(h)
        f.addRow(w)
        return e

    def stufen(self, f, key, label, eintraege: list[tuple[str, float]], std, wirkt=None):
        """Auswahl aus benannten Stufen („normal“, „weit“ …), die als Zahl gespeichert werden."""
        c = QComboBox()
        c.setMinimumHeight(MIN_HOEHE)
        for text, wert in eintraege:
            c.addItem(text, wert)
        akt = float(self.s.get(key, std))
        c.setCurrentIndex(min(range(len(eintraege)), key=lambda i: abs(eintraege[i][1] - akt)))

        def geaendert(_i):
            self.s.set(key, c.currentData())
            if wirkt:
                wirkt(c.currentData())
        c.currentIndexChanged.connect(geaendert)
        f.addRow(label, c)
        return c

    def zahl(self, f, key, label, lo, hi, std, einheit="", dezimal=0, wirkt=None):
        c = QDoubleSpinBox() if dezimal else QSpinBox()
        c.setRange(lo, hi)
        if dezimal:
            c.setDecimals(dezimal)
        c.setSuffix(einheit)
        c.setValue(float(self.s.get(key, std)) if dezimal else self.s.get_int(key, std))

        def geaendert(v):
            self.s.set(key, v)
            if wirkt:
                wirkt(v)
        c.valueChanged.connect(geaendert)
        f.addRow(label, c)
        return c

    def zeile(self, f, text: str):
        l = QLabel(text)
        l.setWordWrap(True)
        l.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f.addRow(l)
        return l

    def hinweis(self, text: str):
        l = text_label(text)
        l.setStyleSheet("color: palette(window-text);")
        self.lay.addWidget(l)

    def aktion(self, text: str, knopf: str, aktion, name: str | None = None):
        """Zeile mit Text und Knopf in der Gruppe, die zuletzt begonnen wurde."""
        return self.karten[-1].aktion(text, knopf, aktion, name)

    def haken_aus(self, f, text: str, grund: str, an: bool = True):
        """Ein Haken, den es in der ersten Fassung gab und der hier noch nichts bewirkt: grau, mit Grund."""
        c = QCheckBox(text)
        c.setProperty("optName", text)
        c.setChecked(an); c.setEnabled(False); c.setToolTip(grund)
        f.addRow(c)
        return c

    def abschluss(self):
        for k in self.karten:
            k.ende()
        if self._offen:
            self.hinweis("Noch nicht umgesetzt (Einstellung ohne Wirkung): " + "; ".join(self._offen) + ".")
        self.lay.addStretch(1)

LESESCHRIFTEN = ("OpenDyslexic", "Lexend", "Atkinson Hyperlegible")

class _Karte(QFormLayout):
    """Zeilen einer Gruppe. Haken stehen wie in der ersten Fassung zu zweit nebeneinander, mit Linie zwischen den Zeilen;
    alles andere (Auswahl, Zahlen, Text) steht in einer eigenen Zeile. Verhält sich sonst wie ein ``QFormLayout``."""

    def __init__(self, eltern):
        super().__init__(eltern)
        self._offen = None                                  # Zeile mit einem Haken, in die noch ein zweiter passt
        self.paare: list[QWidget] = []
        self.setHorizontalSpacing(12); self.setVerticalSpacing(6)

    def addRow(self, *args):
        if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], QWidget):
            self._offen = None
            zeile = QWidget(); zeile.setObjectName("optPaar")
            h = QHBoxLayout(zeile); h.setContentsMargins(0, 4, 0, 6); h.setSpacing(12)
            l = QLabel(args[0]); l.setWordWrap(False)
            if not args[1].accessibleName():
                args[1].setAccessibleName(args[0])               # Bildschirmleser: das Feld heißt wie seine Beschriftung
            h.addWidget(l); h.addWidget(args[1], 1)
            args[1].setProperty("optName", args[0])
            self.paare.append(zeile)
            super().addRow(zeile)
            return
        if len(args) == 1 and isinstance(args[0], QCheckBox) and len(args[0].text()) > 42:
            self._offen = None                               # langer Text: eine ganze Zeile, sonst wird er abgeschnitten
            super().addRow(args[0])
            return
        if len(args) == 1 and isinstance(args[0], QCheckBox):
            if self._offen is not None:
                self._offen.layout().addWidget(args[0], 1)
                self._offen = None
                return
            paar = QWidget(); paar.setObjectName("optPaar")
            h = QHBoxLayout(paar); h.setContentsMargins(0, 2, 0, 6); h.setSpacing(18)
            h.addWidget(args[0], 1)
            self.paare.append(paar)
            self._offen = paar
            super().addRow(paar)
            return
        self._offen = None
        super().addRow(*args)

    def aktion(self, text: str, knopf: str, aktion, name: str | None = None) -> QPushButton:
        """Zeile aus Text und darunter einem Knopf („Den Text hören“ / „Stimme und Tempo …“)."""
        self._offen = None
        zeile = QWidget(); zeile.setObjectName("optPaar")
        v = QVBoxLayout(zeile); v.setContentsMargins(0, 6, 0, 8); v.setSpacing(8)
        v.addWidget(QLabel(text))
        k = QPushButton(knopf)
        k.clicked.connect(lambda _=False: aktion())
        h = QHBoxLayout(); h.addWidget(k); h.addStretch(1)
        v.addLayout(h)
        zeile.setProperty("optName", name or text)
        self.paare.append(zeile)
        super().addRow(zeile)
        return k

    def ende(self):
        """Unterste Linie der letzten Haken-Zeile weg (die Karte hat selbst einen Rand); halbe Zeile mit Platz auffüllen."""
        if self._offen is not None:
            self._offen.layout().addStretch(1)
        if self.paare:
            self.paare[-1].setStyleSheet("QWidget#optPaar { border-bottom: none; }")
