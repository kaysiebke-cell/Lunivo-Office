"""Optionen — das Fenster hinter „☰ Menü ▸ Optionen“ (F9), aufgebaut in drei Zweigen:
Leichter lesen · Allgemein · Nur bei Lunivo. Links der Baum, rechts die Seite.

Was hier steht, wirkt. Was noch keine Wirkung hat, steht je Seite unter „Noch nicht umgesetzt“,
damit nichts stillschweigend verschwindet.
"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import QEvent, QSize, QTimer, Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QRadioButton, QPushButton, QScrollArea, QSlider, QSpinBox, QStackedWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.proofing import autokorrektur
from lunivo_writer.ai import ki as K
from lunivo_writer.core import paths
from lunivo_writer.ui import lesestufen as LS
from lunivo_writer.services import vorlesen
from lunivo_writer.proofing.vorhersage import EMPFAENGER
from lunivo_writer.ui.dialogs.lesehilfe_dialog import PAPIERTOENE

ERKLAERUNG_LEER = "Zeig auf eine Einstellung — hier steht, was sie tut."
_ERKLAERUNGEN: dict | None = None


def _erklaerung(name: str) -> str:
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


LESESCHRIFTEN = ("OpenDyslexic", "Lexend", "Atkinson Hyperlegible")


class _Seite(QWidget):
    """Eine Optionenseite: Gruppen mit Zeilen; Werte stehen sofort in den Einstellungen."""
    def __init__(self, fenster, titel: str, offen: list[str] | None = None):
        super().__init__()
        self.w = fenster
        self.s = fenster.settings
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(24, 16, 24, 16)
        t = text_label(titel, fett=True, pt=16, umbruch=False)
        self.lay.addWidget(t)
        self.gruppe_lay = None
        self.karten: list[_Karte] = []
        self._offen = offen or []

    def gruppe(self, name: str) -> QFormLayout:
        g = QGroupBox(name.upper())
        f = _Karte(g)
        self.karten.append(f)
        self.lay.addWidget(g)
        return f

    def haken(self, f, key, text, std, wirkt=None):
        c = QCheckBox(text)
        c.setProperty("optName", text)
        c.setChecked(self.s.get_bool(key, std))

        def geaendert(on):
            self.s.set(key, on)
            if wirkt:
                wirkt(on)
        c.toggled.connect(geaendert)
        f.addRow(c)
        return c

    def auswahl(self, f, key, label, werte: list[str], std, wirkt=None):
        c = QComboBox()
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
        c.setChecked(bool(ist()))
        c.toggled.connect(lambda on: on != bool(ist()) and umschalten())
        f.addRow(c)
        return c

    def eingabe(self, key: str, platzhalter: str) -> QLineEdit:
        e = QLineEdit(str(self.s.get(key, "")))
        e.setPlaceholderText(platzhalter)
        e.setProperty("optName", platzhalter)
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
        l.setStyleSheet("color: palette(mid);")
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
        fuss = text_label("Lunivo-Office · Prüfung und Wortschatz aus der Schreibhilfe", umbruch=False)
        fuss.setStyleSheet("color: palette(mid); font-size: 8pt; padding-top: 6px;")
        self.lay.addWidget(fuss)
        if self._offen:
            self.hinweis("Noch nicht umgesetzt (Einstellung ohne Wirkung): " + "; ".join(self._offen) + ".")
        self.lay.addStretch(1)


STIL = """
QTreeWidget#optNavigation { background: transparent; border: none; outline: none; }
QTreeWidget#optNavigation::item { padding: 6px 10px; margin: 1px 8px 1px 0; border-radius: 6px; color: palette(mid); }
QTreeWidget#optNavigation::item:selected { background: #2f6fb5; color: white; font-weight: 600; }
QTreeWidget#optNavigation::item:hover:!selected { background: palette(midlight); }
QTreeWidget#optNavigation::branch, QTreeWidget#optNavigation::branch:selected { background: transparent; }
QScrollArea#optSeite, QScrollArea#optSeite > QWidget > QWidget { background: transparent; border: none; }
QGroupBox { border: 1px solid palette(midlight); border-radius: 10px; margin-top: 26px; padding: 8px 10px 8px 10px; background: transparent; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 2px; padding: 0; color: palette(mid); font-size: 8pt; font-weight: 600; }
QWidget#optPaar { border-bottom: 1px solid palette(midlight); }
QLabel#optErklaerung { color: palette(mid); font-style: italic; padding: 12px 24px; border-top: 1px solid palette(midlight); }
QFrame#optSchriftkarte { border: 1px solid palette(midlight); border-radius: 8px; }
QLabel#optVorschau { background: white; color: #111417; border-radius: 6px; padding: 16px 20px; }
"""


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


class OptionenAnsicht(QWidget):
    """Alle Optionen als Ansicht (Navigation links, Seite rechts) — sie steht in der Datei-Ansicht („☰ Menü ▸ Erweiterte
    Einstellungen“) und im Dialog `OptionenDialog`. Werte gelten sofort."""

    def __init__(self, fenster, seite: str | None = None):
        super().__init__()
        self.w = fenster
        self.setStyleSheet(STIL)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        self.baum = QTreeWidget()
        self.baum.setObjectName("optNavigation")
        self.baum.setHeaderHidden(True)
        self.baum.setRootIsDecorated(True)
        self.baum.setIndentation(14)
        self.baum.setFocusPolicy(Qt.NoFocus)
        self.baum.setFixedWidth(250)
        self.stapel = QStackedWidget()
        self.stapel.setMinimumWidth(520)
        self.stapel.setMaximumWidth(860)
        h.addWidget(self.baum)
        sc = QScrollArea(); sc.setObjectName("optSeite"); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        halter = QWidget(); hl = QHBoxLayout(halter); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.stapel); hl.addStretch(1)                      # Seite links, nicht über die ganze Breite gezogen
        sc.setWidget(halter)
        rechts = QWidget(); rv = QVBoxLayout(rechts); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(0)
        rv.addWidget(sc, 1)
        self.erklaerzeile = text_label(ERKLAERUNG_LEER, umbruch=True)
        self.erklaerzeile.setObjectName("optErklaerung")
        rv.addWidget(self.erklaerzeile)
        h.addWidget(rechts, 1)
        self.knoten: dict[str, QTreeWidgetItem] = {}
        zweige = [
            ("Leichter lesen", [("lesehilfe", "Lesehilfe", self._lesehilfe), ("schriften", "Schriftarten", self._schriften),
                                ("sprache", "Sprache", self._sprache), ("rechtschreibung", "Rechtschreibprüfung", self._rechtschreibung)]),
            ("Allgemein", [("ansicht", "Ansicht", self._ansicht), ("bearbeiten", "Bearbeiten", self._bearbeiten),
                                   ("speichern", "Allgemein und Speichern", self._speichern),
                                   ("sicherung", "Sicherungseinstellungen", self._sicherung),
                                   ("speicherort", "Speicherort für Dateien", self._speicherort),
                                   ("verfolgen", "Änderungen verfolgen", self._verfolgen),
                                   ("pdf", "In PDF exportieren", self._pdf),
                                   ("benutzer", "Benutzerinformationen", self._benutzer),
                                   ("drucken", "Drucken", self._drucken),
                                   ("sicherheit", "Sicherheit", self._sicherheit),
                                   ("menueband", "Menüband anpassen", self._menueband),
                                   ("schnellzugriff", "Symbolleiste für den Schnellzugriff", self._schnellzugriff)]),
            ("Nur bei Lunivo", [("ki", "Schreibhilfe und KI", self._ki), ("gedaechtnis", "Gedächtnis", self._gedaechtnis),
                                ("erweitert", "Erweitert", self._erweitert)]),
        ]
        for zweig, seiten in zweige:
            z = QTreeWidgetItem([zweig])
            z.setFlags(z.flags() & ~Qt.ItemIsSelectable)
            f = z.font(0); f.setBold(True); f.setPointSizeF(max(7.5, f.pointSizeF() - 1.5)); f.setCapitalization(QFont.AllUppercase)
            z.setFont(0, f)
            z.setForeground(0, self.palette().mid())
            self.baum.addTopLevelItem(z)
            for key, titel, bauer in seiten:
                it = QTreeWidgetItem([titel])
                it.setData(0, Qt.UserRole, key)
                z.addChild(it)
                self.knoten[key] = it
                self.stapel.addWidget(bauer(titel))
                it.setData(0, Qt.UserRole + 1, self.stapel.count() - 1)
        self.baum.expandAll()
        self.baum.itemClicked.connect(lambda it, _c: it.parent() is None and it.setExpanded(not it.isExpanded()))   # Gruppen auf-/zuklappen
        self.baum.currentItemChanged.connect(lambda cur, _p: cur and cur.data(0, Qt.UserRole + 1) is not None
                                             and self.stapel.setCurrentIndex(cur.data(0, Qt.UserRole + 1)))
        for wid in self.stapel.findChildren(QWidget):                 # Zeigen auf eine Einstellung erklärt sie unten
            wid.installEventFilter(self)
        self.gehe_zu(seite or "lesehilfe")

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Enter, QEvent.FocusIn) and isinstance(obj, QWidget):
            w = obj
            while w is not None and not w.property("optName"):
                w = w.parentWidget()
            if w is not None:
                self._erklaere(str(w.property("optName")))
        elif ev.type() == QEvent.Leave:
            self.erklaerzeile.setText(ERKLAERUNG_LEER)
        return super().eventFilter(obj, ev)

    def _erklaere(self, name: str) -> None:
        satz = _erklaerung(name)
        self.erklaerzeile.setText(f"{name} — {satz}" if satz else ERKLAERUNG_LEER)

    def gehe_zu(self, key: str):
        it = self.knoten.get(key) or self.knoten["lesehilfe"]
        self.baum.setCurrentItem(it)

    # ================= Leichter lesen =================
    def _lesehilfe(self, titel):
        p = _Seite(self.w, titel, ["Zeilenluft"])
        refs: dict = {}
        stufen = LS.STUFEN
        proben = ("Sehr geehrte Damen und Herren, hiermit kündige ich meinen Vertrag fristgerecht zum nächstmöglichen Termin.",
                  "Bitte bestätigen Sie mir den Eingang und das Datum, zu dem die Kündigung wirksam wird.",
                  "Mit freundlichen Grüßen")

        def anwenden(_=None):
            self.w.lesehilfe_anwenden()
            vorschau_neu()

        def vorschau_neu():
            lab = refs.get("vorschau")
            if lab is None:
                return
            px_b, px_w = float(p.s.get("lesehilfe/buchstaben", 0)), float(p.s.get("lesehilfe/wort", 0))
            fnt = lab.font(); fnt.setLetterSpacing(QFont.AbsoluteSpacing, px_b); fnt.setWordSpacing(px_w); lab.setFont(fnt)
            lab.setStyleSheet(f"background: {PAPIERTOENE.get(str(p.s.get('lesehilfe/papier', 'Weiß')), '#ffffff')}; color: #111417; "
                              "border-radius: 6px; padding: 16px 20px;")

        # ---- Lesestufe: drei Voreinstellungen, die die Einstellungen darunter setzen
        f = p.gruppe("Lesestufe")
        karte = QWidget()
        kv = QVBoxLayout(karte); kv.setContentsMargins(0, 4, 0, 4)
        kv.addWidget(QLabel("Wie leicht soll es zu lesen sein?"))
        spalten = QHBoxLayout(); spalten.setSpacing(24)
        links = QVBoxLayout()
        links.addWidget(text_label("Lesestufe", fett=True, umbruch=False))
        gruppe = QButtonGroup(karte)
        aktuell = LS.aktuell(p.s)
        erlaeutert = text_label(" ".join(stufen[aktuell]["text"] if aktuell else LS.EIGENE))
        erlaeutert.setStyleSheet("color: palette(mid); font-size: 9pt;")
        for name in stufen:
            r = QRadioButton(name)
            r.setProperty("optName", "Lesestufe")
            r.setChecked(name == aktuell)
            gruppe.addButton(r)
            links.addWidget(r)
            r.toggled.connect(lambda an, n=name: an and waehle_stufe(n))
        links.addStretch(1)
        rechts = QVBoxLayout()
        rechts.addWidget(text_label("Vorschau", fett=True, umbruch=False))
        vorschau = QLabel("\n\n".join(proben)); vorschau.setWordWrap(True); vorschau.setObjectName("optVorschau")
        refs["vorschau"] = vorschau
        rechts.addWidget(vorschau); rechts.addWidget(erlaeutert)
        spalten.addLayout(links, 1); spalten.addLayout(rechts, 2)
        kv.addLayout(spalten)
        f.addRow(karte)

        def waehle_stufe(name):
            st = stufen[name]
            p.s.set("lesehilfe/stufe", name)
            refs["papier"].setCurrentText(st["papier"])
            refs["buch"].setCurrentIndex(refs["buch"].findData(st["buchstaben"]))
            refs["wort"].setCurrentIndex(refs["wort"].findData(st["wort"]))
            refs["groesser"].setCurrentIndex(refs["groesser"].findData(st["groesser"]))
            refs["zurueck"].setCurrentIndex(refs["zurueck"].findData(st["zurueck"]))
            erlaeutert.setText(" ".join(st["text"]))
            anwenden()

        f = p.gruppe("Leichter lesen")
        refs["papier"] = p.auswahl(f, "lesehilfe/papier", "Papierton", list(PAPIERTOENE), "Weiß", anwenden)
        refs["buch"] = p.stufen(f, "lesehilfe/buchstaben", "Buchstabenabstand",
                                [("normal", 0.0), ("etwas mehr", 0.45), ("deutlich mehr", 0.9), ("sehr viel", 1.35)], 0.0, anwenden)
        refs["wort"] = p.stufen(f, "lesehilfe/wort", "Wortabstand",
                                [("normal", 0.0), ("etwas mehr", 1.8), ("deutlich mehr", 3.6), ("sehr viel", 5.4)], 0.0, anwenden)
        f = p.gruppe("Beim Schreiben")
        refs["fokus"] = p.haken(f, "lesehilfe/zeilenfokus", "Zeilenfokus", False, lambda on: self.w.lesehilfe_anwenden())
        refs["groesser"] = p.wahl(f, "lesehilfe/groesser", "Absatz beim Schreiben",
                                  [("nicht vergrößern", "keine"), ("etwas größer", "etwas"), ("deutlich größer", "deutlich")], "keine", anwenden)
        refs["zurueck"] = p.wahl(f, "lesehilfe/zurueck", "Übriger Text",
                                 [("gleich lassen", "keine"), ("etwas blasser", "etwas"), ("deutlich blasser", "deutlich")], "keine", anwenden)
        c = QComboBox(); c.addItem("normal"); c.setEnabled(False)
        c.setToolTip("Zeilenluft braucht einen eigenen Textsatz: Qt kennt den Zeilenabstand nur als Format des Absatzes, das das Dokument "
                     "(und den Rückgängig-Verlauf) ändern würde. Der Zeilenabstand der Absätze steht unter Start ▸ Absatz.")
        c.setProperty("optName", "Zeilenluft")
        f.addRow("Zeilenluft", c)
        f = p.gruppe("Schrift und Sprache")
        p.aktion("Schrift zum leichteren Lesen", "Zur Schriftwahl", lambda: self.gehe_zu("schriften"))
        self._silbentrennung_haken(p, f)
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe prüfen", True,
                lambda on: self.w.assistant.setze("wellen", on))
        f = p.gruppe("Vorlesen")
        p.aktion("Den Text hören", "Stimme und Tempo …", lambda: self.w.befehle.stimmeWaehlen())
        if not vorlesen.verfuegbar():
            p.hinweis("Es ist keine Sprachausgabe eingerichtet (speech-dispatcher oder Piper).")
        f = p.gruppe("Silben farbig (Lesehilfe für Legasthenie)")
        p.haken(f, "lesehilfe/silben/an", "Silben farbig anzeigen", False, lambda _: self.w.silbenfarben_anwenden())
        b = QPushButton("Farben, Darstellung und Mindestlänge einstellen …")
        b.clicked.connect(lambda: self.w.befehle.silbenEinstellen())
        f.addRow(b)
        f = p.gruppe("Silbentrennung")
        p.auswahl(f, "silben/sprache", "Sprache der Silbentrennung", ["de_DE", "de_AT", "de_CH", "en_US", "en_GB", "fr", "es", "it", "nl_NL", "pl_PL", "tr_TR"], "de_DE")
        vorschau_neu()
        p.abschluss()
        return p

    def _silbentrennung_haken(self, p, f):
        """Haken „Silbentrennung“: gilt für das Dokument, das gerade offen ist (derselbe Schalter wie im Reiter Schreibhilfe)."""
        c = QCheckBox("Silbentrennung")
        c.setProperty("optName", "Silbentrennung")
        c.setChecked(bool(self.w.befehle.an_silbentrennung()))
        c.toggled.connect(lambda on: on != bool(self.w.befehle.an_silbentrennung()) and self.w.befehle.silbentrennung())
        f.addRow(c)
        return c

    def _schriften(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Schrift für neuen Text")
        fam = QComboBox(); fam.setEditable(True)
        fam.addItems(sorted(set(QFontDatabase.families())))
        fam.setCurrentText(p.s.get("standard/schrift", "Liberation Sans"))
        fam.currentTextChanged.connect(lambda t: p.s.set("standard/schrift", t))
        f.addRow("Schrift", fam)
        p.zahl(f, "standard/groesse", "Größe", 6, 72, 11, " pt", 1)
        f = p.gruppe("Zum leichteren Lesen")
        f.addRow(QLabel("Drei Schriften sind dafür gemacht"))
        vorhanden = {n.lower() for n in QFontDatabase.families()}
        beschreibung = {"OpenDyslexic": "Die Buchstaben sind unten schwerer — sie kippen nicht.",
                        "Lexend": "Weitere Abstände, ruhigeres Zeilenbild.",
                        "Atkinson Hyperlegible": "Unterscheidet Zeichen wie I, l und 1."}
        reihe = QWidget(); rh = QHBoxLayout(reihe); rh.setContentsMargins(0, 4, 0, 4); rh.setSpacing(10)
        for n in LESESCHRIFTEN:
            k = QFrame(); k.setObjectName("optSchriftkarte")
            kv = QVBoxLayout(k)
            name = QLabel(n)
            if n.lower() in vorhanden:
                fnt = QFont(n); fnt.setPointSizeF(13); name.setFont(fnt)
            kv.addWidget(name)
            t = text_label(beschreibung.get(n, "") + ("" if n.lower() in vorhanden else "  (fehlt — ./schrift-holen.sh holt sie)"))
            t.setStyleSheet("color: palette(mid); font-size: 8pt;")
            kv.addWidget(t)
            rh.addWidget(k, 1)
        f.addRow(reihe)
        p.aktion("Sind sie da?", "Zu Erweitert", lambda: self.gehe_zu("erweitert"))
        p.hinweis("Gilt für neue Dokumente. Bestehende Dokumente behalten ihre Schrift.")
        p.abschluss()
        return p

    def _sprache(self, titel):
        p = _Seite(self.w, titel, ["Weitere Prüfsprachen (derzeit Deutsch)"])
        f = p.gruppe("Sprache")
        pr = QComboBox(); pr.addItem("Deutsch"); pr.setToolTip("Weitere Prüfsprachen gibt es in der Qt-Fassung noch nicht")
        f.addRow("Sprache für die Prüfung", pr)
        c = QComboBox(); c.addItems(K.SPRACHEN)
        c.setCurrentText(self.w.ki.konfig["sprache"])
        c.currentTextChanged.connect(lambda t: (self.w.ki.konfig.setze("sprache", t), self.w.ki.geaendert.emit()))
        f.addRow("Übersetzen nach", c)
        f = p.gruppe("Was geprüft wird")
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe", True, lambda on: self.w.assistant.setze("wellen", on))
        p.haken(f, "rsGrammatik", "Grammatik mitprüfen", True, lambda _: self.w.assistant.pruefen(voll=True))
        self._silbentrennung_haken(p, f)
        p.aktion("Alle Prüfoptionen", "Zur Rechtschreibprüfung", lambda: self.gehe_zu("rechtschreibung"))
        f = p.gruppe("Wörter, die Lunivo kennt")
        p.aktion("Dein eigener Wortschatz", "Zum Gedächtnis", lambda: self.gehe_zu("gedaechtnis"))
        p.aktion("Gründlich prüfen", "Gründlich prüfen …", lambda: self.w.befehle.tun("gruendlichPruefen"))
        p.abschluss()
        return p

    def _rechtschreibung(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Rechtschreibprüfung")
        pr = QComboBox(); pr.addItem("Deutsch"); pr.setToolTip("Weitere Prüfsprachen gibt es in der Qt-Fassung noch nicht")
        f.addRow("Sprache für die Prüfung", pr)
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe prüfen", True, lambda on: self.w.assistant.setze("wellen", on))
        p.haken(f, "schreibhilfe/vorschlaege", "Immer Korrekturvorschläge unterbreiten", True)
        p.haken(f, "rsGrammatik", "Grammatik mitprüfen", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.haken(f, "rsGrossIgnorieren", "Wörter in GROSSBUCHSTABEN ignorieren", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.haken(f, "rsZahlenIgnorieren", "Wörter mit Zahlen ignorieren", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.haken(f, "rsPfadeIgnorieren", "Internet- und Netzwerkpfade ignorieren", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.aktion("Weggewinkte Funde wieder anzeigen", "Wieder anzeigen",
                 lambda: (self.w.assistant._weg.clear(), self.w.assistant.pruefen(voll=True)))
        f = p.gruppe("Benutzerwörterbuch")
        p.aktion("Was das Programm gelernt hat", "Zum Gedächtnis", lambda: self.gehe_zu("gedaechtnis"))
        p.abschluss()
        return p

    # ================= Wie im WPS Writer =================
    def _ansicht(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Anzeigen")
        p.haken(f, "ansicht/lineal", "Lineal", False, lambda _: self.w.lineale_anwenden())
        p.haken(f, "ansicht/lineal_hoch", "Vertikales Lineal", False, lambda _: self.w.lineale_anwenden())
        p.schalter(f, "Navigationsbereich", lambda: self.w.navigation.isVisible(), self.w.toggle_navigation)
        p.haken(f, "ui/marken", "Textbegrenzungen", False, self.w.set_marken)
        p.schalter(f, "Gitternetzlinien", lambda: bool(self.w.befehle.an_netzlinien()), lambda: self.w.befehle.netzlinien())
        p.haken(f, "ui/statusleiste", "Statusleiste", True, lambda on: self.w.statusBar().setVisible(on))
        p.haken(f, "ui/seitenleiste", "Seitenleiste beim Start", True)
        p.haken(f, "ui/quickinfo", "QuickInfo", True, lambda _: self.w.ansicht_optionen_anwenden())
        p.haken(f, "ui/live_vorschau", "Live-Vorschau", True, lambda _: self.w.vorschau.ende())
        p.haken(f, "ui/mini_auswahl", "Minisymbolleiste bei Auswahl", True)
        p.haken(f, "ui/mini_rechtsklick", "Minisymbolleiste bei Rechtsklick", True)
        p.haken(f, "ui/kopffuss_tipp", "Tipp für Kopf- bzw. Fußzeile", True)
        f = p.gruppe("Druckoptionen")
        p.haken(f, "drucken/hervorhebungen", "Hervorhebungen drucken", True)
        p.haken(f, "drucken/textgrenzen", "Textbegrenzungen drucken", False)
        p.haken(f, "drucken/zuschnitt", "Zuschnittsmarken anzeigen", False)
        p.haken(f, "drucken/felder_code", "Feldfunktionen drucken", False)
        p.haken(f, "drucken/textmarken", "Textmarken drucken", False)
        p.wahl(f, "ui/feldschattierung", "Feldschattierung", [("Nie", "Nie"), ("Wenn ausgewählt", "Bei Auswahl"), ("Immer", "Immer")],
               "Bei Auswahl", lambda _: [t.editor._overlays_neu() for t in self.w._doc_tabs()])
        f = p.gruppe("Formatierungszeichen")
        alle, absatz, leer = QCheckBox("Alle anzeigen"), QCheckBox("Absatzmarken"), QCheckBox("Leerzeichen und Tabstoppzeichen")
        for c in (alle, absatz, leer):
            c.setProperty("optName", c.text())

        def stand():
            alt = p.s.get_bool("ui/steuerzeichen", False)
            a, l = p.s.get_bool("ui/marken_absatz", alt), p.s.get_bool("ui/marken_leer", alt)
            for c, v in ((alle, a and l), (absatz, a), (leer, l)):
                c.blockSignals(True); c.setChecked(v); c.blockSignals(False)

        def setze(a=None, l=None):
            self.w.marken_setzen(a, l)
            stand()
        stand()
        alle.toggled.connect(lambda on: setze(on, on))
        absatz.toggled.connect(lambda on: setze(absatz=on))
        leer.toggled.connect(lambda on: setze(leer=on))
        for c in (alle, absatz, leer):
            f.addRow(c)
        p.haken(f, "ui/objektanker", "Objektanker", True)
        p.haken(f, "ui/versteckt_zeigen", "Ausgeblendeter Text", False, lambda _: self.w.versteckt_anwenden())
        f = p.gruppe("Menübandoptionen")
        p.haken(f, "ui/band_doppelklick", "Doppelklick blendet das Band aus", True, lambda on: setattr(self.w.band, "einklappbar", on))
        p.haken(f, "ui/strg_klick_link", "Strg+Klick folgt einem Verweis", True)
        f = p.gruppe("Darstellung")
        self._darstellung(p, f)
        p.abschluss()
        return p

    def _darstellung(self, p, f):
        """Schrift und Helligkeit, Weicher Kontrast, Größe der Symbole, Schrift der Bedienung, Benutzeroberfläche."""
        kopf = QWidget(); v = QVBoxLayout(kopf); v.setContentsMargins(0, 6, 0, 8); v.setSpacing(8)
        v.addWidget(QLabel("Schrift und Helligkeit"))
        knoepfe = QHBoxLayout()
        klein, gross, hell = QPushButton("A−  kleiner"), QPushButton("A+  größer"), QPushButton("◐  Hell/Dunkel")
        for k in (klein, gross, hell):
            knoepfe.addWidget(k)
        knoepfe.addStretch(1)
        v.addLayout(knoepfe)
        zeile = QHBoxLayout()
        probe = QLabel("So groß schreibst du.")
        probe.setObjectName("optVorschau")
        stand = QLabel()
        stand.setStyleSheet("color: palette(mid); font-size: 9pt;")
        zeile.addWidget(probe); zeile.addWidget(stand); zeile.addStretch(1)
        v.addLayout(zeile)

        def zoom_zeigen():
            e = self.w.current_editor()
            z = e.zoom if e is not None else 1.0
            fnt = probe.font(); fnt.setPointSizeF(12 * z); probe.setFont(fnt)
            stand.setText(f"Schriftgröße: {round(z * 100)} %")

        def um(faktor):
            self.w.befehle._zoom_um(faktor)
            zoom_zeigen()
        klein.clicked.connect(lambda: um(1 / 1.1))
        gross.clicked.connect(lambda: um(1.1))
        hell.clicked.connect(lambda: self.w.set_theme("light" if QApplication.instance().palette().window().color().lightness() < 128 else "dark"))
        zoom_zeigen()
        kopf.setProperty("optName", "Schrift und Helligkeit")
        f.addRow(kopf)
        p.haken(f, "ui/weich", "Weicher Kontrast", False, lambda _: self.w.set_theme(self.w.settings.get("theme", "system")))
        p.wahl(f, "ui/icongroesse", "Größe der Symbole", [("Klein", "klein"), ("Mittel", "mittel"), ("Groß", "gross")], "mittel",
               lambda _: self.w.ansicht_optionen_anwenden())
        regler = QWidget(); rv = QVBoxLayout(regler); rv.setContentsMargins(0, 6, 0, 8); rv.addWidget(QLabel("Schrift der Bedienung"))
        rh = QHBoxLayout()
        sl = QSlider(Qt.Horizontal); sl.setRange(80, 140); sl.setSingleStep(5); sl.setPageStep(10)
        sl.setValue(p.s.get_int("ui/bedien_prozent", 100))
        prozent = QLabel(f"{sl.value()} %"); prozent.setStyleSheet("color: palette(mid);")

        def neu_wert(w):
            p.s.set("ui/bedien_prozent", w)
            prozent.setText(f"{w} %")
            if not sl.isSliderDown():
                self.w.ansicht_optionen_anwenden()
        sl.valueChanged.connect(neu_wert)
        sl.sliderReleased.connect(self.w.ansicht_optionen_anwenden)
        rh.addWidget(sl, 1); rh.addWidget(prozent)
        rv.addLayout(rh)
        regler.setProperty("optName", "Schrift der Bedienung")
        f.addRow(regler)
        oberfl = QWidget(); ov = QVBoxLayout(oberfl); ov.setContentsMargins(0, 6, 0, 8); ov.addWidget(QLabel("Benutzeroberfläche"))
        gr = QButtonGroup(oberfl)
        beschreibung = text_label("", umbruch=True)
        beschreibung.setStyleSheet("color: palette(mid); font-size: 9pt;")
        texte = {"symbolleisten": "Menüleiste, darunter zwei Zeilen Symbole: alles ist sichtbar, nichts ist versteckt.",
                 "register": "Menüleiste oben, darunter Reiter: Start, Einfügen, Layout. Jeder Reiter hat seine eigenen Werkzeuge, in Gruppen mit Namen darunter."}
        aktuell = p.s.get("ui/oberflaeche", "register")
        for schl, name in (("symbolleisten", "Symbolleisten"), ("register", "In Registern")):
            r = QRadioButton(name); r.setChecked(schl == aktuell); r.setProperty("optName", "Benutzeroberfläche")
            gr.addButton(r); ov.addWidget(r)
            r.toggled.connect(lambda an, k=schl: an and (beschreibung.setText(texte[k]),
                                                         self.w.oberflaeche_aendern(k, self.w.menubar_wanted if k == "register" else True)))
        beschreibung.setText(texte.get(aktuell, ""))
        ov.addWidget(beschreibung)
        oberfl.setProperty("optName", "Benutzeroberfläche")
        f.addRow(oberfl)

    def _bearbeiten(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Bearbeitungsoptionen")
        p.haken(f, "bearbeiten/wortweise", "Wortweise markieren", True)
        p.haken(f, "bearbeiten/ziehen", "Text mit der Maus verschieben", True, lambda _: self.w.lesehilfe_anwenden())
        p.haken(f, "bearbeiten/tippen_ersetzt", "Tippen ersetzt die Auswahl", True)
        f = p.gruppe("AutoFormat")
        p.haken(f, "autoformat/liste", "Automatisch nummerierte Listen", True)
        p.haken(f, "autoformat/punkte", "Aufzählungen erkennen", True)
        p.haken(f, "schreibhilfe/akKreiszahl", "Zahl automatisch im Kreis", False)
        f = p.gruppe("AutoKorrektur")
        p.haken(f, "schreibhilfe/autokorr", "AutoKorrektur", True, lambda on: self.w.assistant.setze("autokorr", on))
        for name, (std, text) in autokorrektur.SCHALTER.items():
            p.haken(f, "schreibhilfe/" + name, text, std)
        p.haken(f, "schreibhilfe/akPfade", "Internet- und Netzwerkpfade durch Hyperlinks ersetzen", True)
        p.haken(f, "schreibhilfe/akErstzeile", "Leerzeichen am Absatzanfang mit Erstzeileneinzug", False)
        p.haken(f, "schreibhilfe/akRechtsLeer", "Leerzeichenformat am Ende rechtsbündiger Zeilen anpassen", False)
        p.haken(f, "schreibhilfe/akZentriert", "Bei zentriertem Ausrichten Erstzeileneinzug löschen", True)
        p.haken(f, "schreibhilfe/akTabEinzug", "Tabulator und Rücktaste setzen den Einzug", True)
        p.haken(f, "schreibhilfe/vorhersage", "Wortvorhersage", True, lambda on: self.w.assistant.setze("vorhersage", on))
        f = p.gruppe("Ausschneiden und Einfügen")
        p.haken(f, "bearbeiten/einfuegen_schaltflaeche", "Schaltfläche nach dem Einfügen", True)
        p.haken(f, "bearbeiten/mittlere_taste", "Mittlere Maustaste fügt ein", True)
        from lunivo_writer.ui.document.document_editor import EINFUEGE_MODI
        p.wahl(f, "bearbeiten/einfuegen_standard", "Standardeinfügeformat", [(m, m) for m in EINFUEGE_MODI], EINFUEGE_MODI[0])
        p.abschluss()
        return p

    def _speichern(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Speichern")
        p.wahl(f, "speichern/standard", "Dateien als Standard speichern", [("Microsoft Word (.docx)", ".docx"), ("Textdatei (.txt)", ".txt")], ".docx")
        f = p.gruppe("Allgemeine Optionen")
        from lunivo_writer.ui.dialogs import dokument_dialoge as _d
        p.wahl(f, "ui/masseinheit", "Maßeinheit", [(n, n) for n in _d.EINHEITEN], "Millimeter", _d.set_einheit)
        p.haken(f, "start/letztes_oeffnen", "Beim Start das zuletzt geschriebene Dokument öffnen", False)
        p.haken(f, "speichern/bilder_nicht_komprimieren", "Bilder in der Datei nicht komprimieren", True)
        p.wahl(f, "ausgabe/ppi", "Standard-Ausgabeziel",
               [(t, t) for t in ("96 ppi (Bildschirm)", "150 ppi (Web, Entwurf)", "220 ppi (Druck)", "330 ppi (hohe Qualität)")],
               "150 ppi (Web, Entwurf)")
        f = p.gruppe("Kompatibilitätsoptionen")
        for key, text in (("kompat/seitenumbruch", "Seitenumbruch und Absatzmarke aufteilen"),
                          ("kompat/haengend", "Hängenden Einzug nicht als Tabstopp verwenden"),
                          ("kompat/leerstellen", "Nachstehende Leerstellen unterstreichen"),
                          ("kompat/fussnoten", "Layout von Fußnoten wie Word 6/95/97"),
                          ("kompat/zeilenhoehe", "Zeilenhöhe in Tabellen auf Rasterhöhe anpassen")):
            p.haken(f, key, text, False)
        p.hinweis("Die Kompatibilitätsoptionen werden als Einstellungen in die DOCX-Datei geschrieben; Word liest sie beim Öffnen. "
                  "Bilder werden nur verkleinert (auf höchstens 1600 Punkte Kantenlänge), wenn „nicht komprimieren“ aus ist.")
        p.hinweis("DOCX ist das Austauschformat mit der höchsten Treue. ODT, DOC und RTF gehen über ein Umwandlungsprogramm (Datei ▸ Exportieren).")
        p.abschluss()
        return p

    def _speicherort(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Speicherort für Dateien")
        p.pfad(f, "speichern/ordner", "Ordner zum Speichern", "Zuletzt benutzter Ordner")
        p.pfad(f, "vorlagen/ordner", "Eigene Vorlagen", "~/Vorlagen")
        p.abschluss()
        return p

    def _pdf(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Exportoptionen")
        p.haken(f, "pdf/oeffnen", "PDF nach dem Export öffnen", False)
        p.haken(f, "pdf/eigenschaften", "Dokumenteigenschaften (Autor) in das PDF übernehmen", True)
        p.haken(f, "pdf/lz_ueberschriften", "Überschriften als Lesezeichen", False)
        p.haken(f, "pdf/lz_textmarken", "Textmarken übernehmen", False)
        p.haken(f, "pdf/lz_andere", "Titel, Untertitel und Zitat als Lesezeichen (andere Formatvorlagen)", False)
        p.haken(f, "pdf/kommentare", "Kommentare als PDF-Notizen mitnehmen", False)
        p.haken(f, "pdf/notenlinks", "Fuß- und Endnoten mit ihrer Marke verknüpfen (Sprungverweise)", True)
        p.abschluss()
        return p

    def _sicherung(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Sicherung")
        p.wahl(f, "sicherung/aktiv", "Wann gesichert wird", [("Laufend, nach jeder Änderung", True), ("Nie", False)], True)
        minuten = QSpinBox(); minuten.setRange(1, 120); minuten.setSuffix(" min")
        minuten.setValue(max(1, p.s.get_int("autosave_seconds", 60) // 60))

        def neu(m):
            p.s.set("autosave_seconds", m * 60)
            self.w.autosave.start(m * 60 * 1000)
        minuten.valueChanged.connect(neu)
        f.addRow("Abstand (Minuten)", minuten)
        ort = QLineEdit(p.s.q.fileName()); ort.setReadOnly(True)
        f.addRow("Wo die Einstellungen liegen", ort)
        f = p.gruppe("Zwischenstände aufheben")
        p.zahl(f, "sicherung/tage", "Wie lange (Tage)", 1, 365, 7, " Tage")
        p.aktion("Zwischenstände löschen", "Zwischenstände löschen", self._zwischenstaende_loeschen)
        f = p.gruppe("Was im Speicher steht")
        p.aktion("Sichern und zurückholen", "Sichern …", self._daten_sichern)
        zb = QPushButton("Einspielen …"); zb.clicked.connect(self._daten_zurueckholen)
        f.addRow(zb)
        p.hinweis("Gesichert werden Gedächtnis und Wörterbuch (ohne API-Schlüssel) als ZIP-Datei.")
        p.abschluss()
        return p

    def _zwischenstaende_loeschen(self):
        import shutil
        from lunivo_writer.services import recovery
        ordner = recovery.recovery_dir()
        if QMessageBox.question(self, "Zwischenstände löschen", f"Alle gesicherten Zwischenstände in\n{ordner}\nwirklich löschen?") != QMessageBox.Yes:
            return
        n = 0
        for name in os.listdir(ordner) if os.path.isdir(ordner) else []:
            pfad = os.path.join(ordner, name)
            try:
                shutil.rmtree(pfad) if os.path.isdir(pfad) else os.remove(pfad)
                n += 1
            except OSError:
                pass
        QMessageBox.information(self, "Zwischenstände löschen", f"{n} Zwischenstände gelöscht.")

    def _daten_sichern(self):
        import zipfile
        from PySide6.QtWidgets import QFileDialog
        from lunivo_writer.services.settings_service import data_dir
        pfad, _ = QFileDialog.getSaveFileName(self, "Sichern", "lunivo-sicherung.zip", "ZIP (*.zip)")
        if not pfad:
            return
        with zipfile.ZipFile(pfad, "w", zipfile.ZIP_DEFLATED) as z:
            for n in ("gelernt.json",):
                f = os.path.join(data_dir(), n)
                if os.path.exists(f):
                    z.write(f, n)
        QMessageBox.information(self, "Sichern", "Gesichert: " + pfad)

    def _daten_zurueckholen(self):
        import zipfile
        from PySide6.QtWidgets import QFileDialog
        from lunivo_writer.services.settings_service import data_dir
        pfad, _ = QFileDialog.getOpenFileName(self, "Zurückholen", "", "ZIP (*.zip)")
        if not pfad:
            return
        try:
            with zipfile.ZipFile(pfad) as z:
                if "gelernt.json" in z.namelist():
                    z.extract("gelernt.json", data_dir())
            self.w.assistant.gelernt.laden(); self.w.assistant.pruefen(voll=True)
        except (OSError, zipfile.BadZipFile) as ex:
            QMessageBox.warning(self, "Zurückholen", f"Das ging nicht: {ex}")
            return
        QMessageBox.information(self, "Zurückholen", "Zurückgeholt.")

    def _drucken(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Druckoptionen")
        p.wahl(f, "drucken/vorgabe", "Womit das Druckfenster aufgeht", [("Alle Seiten", "Alle Seiten"), ("Aktuelle Seite", "Aktuelle Seite")], "Alle Seiten")
        p.haken(f, "drucken/hoch", "Hohe Qualität", True)
        p.haken(f, "drucken/umgekehrt", "Umgekehrte Reihenfolge", False)
        p.haken(f, "drucken/zeichnungen", "Zeichnungsobjekte drucken", True)
        p.haken(f, "drucken/hintergrund", "Hintergrundfarben und -bilder drucken", True)
        p.haken(f, "drucken/leere", "Leere Seiten mitdrucken", True)
        p.haken(f, "drucken/felder", "Felder vor dem Drucken aktualisieren", True)
        p.haken(f, "drucken/felder_code", "Feldfunktionen drucken", False)
        p.wahl(f, "drucken/versteckt", "Ausgeblendeter Text", [("Ausgeblendeten Text nicht drucken", False), ("Ausgeblendeten Text drucken", True)], False)
        f = p.gruppe("Nur für das aktuelle Dokument")
        p.haken(f, "drucken/nur_formular", "Nur Formulardaten drucken", False)
        f = p.gruppe("Duplexdruck")
        wert = str(p.s.get("drucken/duplex", "alle"))
        vorne, hinten = QCheckBox("Blattvorderseite"), QCheckBox("Blattrückseite")
        vorne.setChecked(wert in ("alle", "vorder")); hinten.setChecked(wert in ("alle", "rueck"))

        def duplex(_=None):
            neu = "alle" if vorne.isChecked() == hinten.isChecked() else ("vorder" if vorne.isChecked() else "rueck")
            p.s.set("drucken/duplex", neu)
        for c in (vorne, hinten):
            c.setProperty("optName", "Duplexdruck"); c.toggled.connect(duplex); f.addRow(c)
        p.hinweis("Gedruckt wird über das Druckfenster des Systems (Datei ▸ Drucken). Kopf-/Fußzeile und Seitenzahlen werden mitgedruckt.")
        p.abschluss()
        return p

    # ---- Befehlslisten (Menüband, Schnellzugriff): zwei Listen mit Hinzufügen / Entfernen, wie in der Vorlage ---------------------------
    def _band_merken(self) -> None:
        """Die Änderung steht in den Einstellungen; das Band wird beim Verlassen der Seite neu gebaut (nicht bei jedem Klick)."""
        self._band_neu = True

    def _band_jetzt(self, *_a) -> None:
        if getattr(self, "_band_neu", False):
            self._band_neu = False
            QTimer.singleShot(0, self.w.neu_bauen_band)

    def hideEvent(self, ev):
        self._band_jetzt()
        super().hideEvent(ev)

    def _zwei_listen(self, p, links_kopf: str, rechts_kopf: str, hinzu: str, weg: str, kategorie: str):
        """Gerüst der Vorlage: links „Befehle auswählen“ (Auswahl, Suche, Liste), in der Mitte Hinzufügen/Entfernen, rechts die Liste
        der aktuellen Einträge mit Pfeilen. Gibt (links, rechts, suche, b_hinzu, b_weg, auf, ab, unten) zurück."""
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 8, 0, 0); g.setHorizontalSpacing(14); g.setVerticalSpacing(6)
        g.setColumnStretch(0, 5); g.setColumnStretch(2, 5)
        g.addWidget(QLabel(links_kopf), 0, 0)
        kopf = QHBoxLayout()
        auswahl = QComboBox(); auswahl.addItem(kategorie)
        suche = QLineEdit(); suche.setPlaceholderText("Befehl suchen"); suche.setClearButtonEnabled(True)
        kopf.addWidget(auswahl, 1); kopf.addWidget(suche, 1)
        g.addLayout(kopf, 1, 0)
        links = QListWidget(); links.setMinimumHeight(250); links.setIconSize(QSize(18, 18))
        g.addWidget(links, 2, 0)
        mitte = QVBoxLayout(); mitte.addStretch(1)
        b_hinzu = QPushButton(hinzu); b_weg = QPushButton(weg)
        mitte.addWidget(b_hinzu); mitte.addWidget(b_weg); mitte.addStretch(1)
        g.addLayout(mitte, 2, 1)
        g.addWidget(QLabel(rechts_kopf), 0, 2)
        rechts = QListWidget(); rechts.setMinimumHeight(250); rechts.setIconSize(QSize(18, 18))
        pf = QVBoxLayout()
        auf = QPushButton("▲"); ab = QPushButton("▼")
        for b in (auf, ab):
            b.setFixedWidth(34)
        pf.addStretch(1); pf.addWidget(auf); pf.addWidget(ab); pf.addStretch(1)
        rz = QHBoxLayout(); rz.addWidget(rechts, 1); rz.addLayout(pf)
        g.addLayout(rz, 1, 2, 2, 1)
        unten = QHBoxLayout(); unten.setContentsMargins(0, 4, 0, 0)
        g.addLayout(unten, 3, 0, 1, 3)
        p.lay.addWidget(w)
        return links, rechts, suche, b_hinzu, b_weg, auf, ab, unten

    @staticmethod
    def _schieben(liste: QListWidget, d: int) -> None:
        i = liste.currentRow(); j = i + d
        if i < 0 or not 0 <= j < liste.count():
            return
        it = liste.takeItem(i)
        liste.insertItem(j, it)
        liste.setCurrentRow(j)

    def _menueband(self, titel):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import IMMER, lade_json
        from lunivo_writer.ui.ribbon.plan import plan
        from lunivo_writer.ui.ribbon.ribbon_bar import STANDARD_VERSTECKT
        p = _Seite(self.w, titel)
        links, rechts, suche, b_hinzu, b_weg, auf, ab, unten = self._zwei_listen(
            p, "Register, die ausgeblendet sind", "Menüband anpassen", "Hinzufügen", "Entfernen", "Ausgeblendete Register")
        namen = [r["name"] for r in plan(self.w.band.daten) if not r.get("kontext") and r["name"] not in IMMER]
        cfg = lade_json(self.w.settings, "ui/register_plan", {})
        reihenfolge = [n for n in cfg.get("reihenfolge", []) if n in namen] + [n for n in namen if n not in cfg.get("reihenfolge", [])]
        versteckt = set(cfg["versteckt"] if "versteckt" in cfg else STANDARD_VERSTECKT)
        for n in reihenfolge:
            (links if n in versteckt else rechts).addItem(n)

        def speichern():
            sichtbar = [rechts.item(i).text() for i in range(rechts.count())]
            weg = [links.item(i).text() for i in range(links.count())]
            self.w.settings.set("ui/register_plan", json.dumps({"reihenfolge": sichtbar + weg, "versteckt": weg}))
            self._band_merken()

        def verschiebe(von, nach):
            it = von.currentItem()
            if it is None or (nach is links and it.text() in IMMER):
                return
            if nach is links and rechts.count() <= 1 and von is rechts:
                return                                           # mindestens ein Register bleibt
            von.takeItem(von.row(it)); nach.addItem(it); nach.setCurrentItem(it)
            speichern()
        b_hinzu.clicked.connect(lambda: verschiebe(links, rechts))
        b_weg.clicked.connect(lambda: verschiebe(rechts, links))
        links.itemDoubleClicked.connect(lambda _i: verschiebe(links, rechts))
        auf.clicked.connect(lambda: (self._schieben(rechts, -1), speichern()))
        ab.clicked.connect(lambda: (self._schieben(rechts, 1), speichern()))
        suche.textChanged.connect(lambda t: [links.item(i).setHidden(t.lower() not in links.item(i).text().lower())
                                             for i in range(links.count())])
        from PySide6.QtWidgets import QMenu
        unten.addWidget(QLabel("Tastenkombinationen:"))
        tk = QPushButton("Anzeigen …")
        tk.clicked.connect(lambda: __import__("lunivo_writer.ui.dialogs.hilfe_dialoge", fromlist=["x"]).tastenkuerzel(self.w).show())
        unten.addWidget(tk); unten.addStretch(1)
        unten.addWidget(QLabel("Anpassungen:"))
        zr = QPushButton("Zurücksetzen ▾")
        m = QMenu(zr)
        m.addAction("Nur das Menüband", lambda: (self.w.settings.remove("ui/register_plan"), self._band_merken(), self._band_jetzt()))
        m.addAction("Alle Anpassungen (Register, Schnellzugriff, Symbole) …", self.w.befehle.vorlagenZurueck)
        zr.setMenu(m)
        unten.addWidget(zr)
        f = p.gruppe("Aussehen")
        for text, fn in (("Benutzeroberfläche wählen …", self.w.befehle.benutzeroberflaeche),
                         ("Symbole austauschen …", self.w.befehle.symbolTauschen)):
            b = QPushButton(text); b.clicked.connect(lambda _=False, fn=fn: fn()); f.addRow(b)
        p.abschluss()
        return p

    def _schnellzugriff(self, titel):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import lade_json
        from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand
        from lunivo_writer.ui.widgets import icons
        p = _Seite(self.w, titel)
        links, rechts, suche, b_hinzu, b_weg, auf, ab, unten = self._zwei_listen(
            p, "Befehle auswählen", "Derzeit angezeigte Optionen", "Hinzufügen >>", "<< Entfernen", "Häufig verwendete Befehle")
        alle = {aktion: (sym, name) for sym, name, aktion in RegisterBand.SCHNELL_ALLE}
        vorgabe = [a for _s, _n, a in RegisterBand.SCHNELL]

        def eintrag(aktion):
            sym, name = alle[aktion]
            it = QListWidgetItem(icons.icon(sym, 18), name)
            it.setData(Qt.UserRole, aktion)
            return it

        def fuellen(aktuell):
            links.clear(); rechts.clear()
            for a in aktuell:
                if a in alle:
                    rechts.addItem(eintrag(a))
            for a in alle:
                if a not in aktuell:
                    links.addItem(eintrag(a))
        fuellen(lade_json(self.w.settings, "ui/schnellzugriff", None) or vorgabe)

        def speichern():
            self.w.settings.set("ui/schnellzugriff", json.dumps([rechts.item(i).data(Qt.UserRole) for i in range(rechts.count())]))
            self._band_merken()

        def verschiebe(von, nach):
            it = von.currentItem()
            if it is None:
                return
            von.takeItem(von.row(it)); nach.addItem(it); nach.setCurrentItem(it)
            speichern()
        b_hinzu.clicked.connect(lambda: verschiebe(links, rechts))
        b_weg.clicked.connect(lambda: verschiebe(rechts, links))
        links.itemDoubleClicked.connect(lambda _i: verschiebe(links, rechts))
        rechts.itemDoubleClicked.connect(lambda _i: verschiebe(rechts, links))
        auf.clicked.connect(lambda: (self._schieben(rechts, -1), speichern()))
        ab.clicked.connect(lambda: (self._schieben(rechts, 1), speichern()))
        suche.textChanged.connect(lambda t: [links.item(i).setHidden(t.lower() not in links.item(i).text().lower())
                                             for i in range(links.count())])
        unten.addStretch(1)
        zr = QPushButton("Zurücksetzen")
        zr.clicked.connect(lambda: (self.w.settings.remove("ui/schnellzugriff"), fuellen(vorgabe), self._band_merken()))
        unten.addWidget(zr)
        p.abschluss()
        return p

    def _benutzer(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Benutzerdaten")
        f.addRow(QLabel("Wer schreibt"))
        p.felder(f, [("benutzer/name", "Name (Autor in DOCX-Dokumenten)"), ("benutzer/strasse", "Straße und Hausnummer"),
                     ("benutzer/plz_ort", "PLZ und Ort"), ("benutzer/ort", "Ort (für „Ort, Datum“)"),
                     ("benutzer/telefon", "Telefon"), ("benutzer/mail", "E-Mail")])
        p.zeile(f, "Bleibt auf diesem Rechner und geht nie mit einem Text an die KI.")
        f.addRow("Initialen", p.eingabe("benutzer/initialen", "z. B. KS"))
        p.haken(f, "benutzer/verwenden", "Diese Benutzerinformationen verwenden", True)
        p.haken(f, "sicherheit/personendaten_weg", "Beim Speichern persönliche Daten entfernen", False)
        p.abschluss()
        return p

    def _sicherheit(self, titel):
        p = _Seite(self.w, titel)
        t = self.w.current_tab()
        f = p.gruppe("Kennwortschutz")
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 4, 0, 4); g.setHorizontalSpacing(10); g.setVerticalSpacing(8)
        g.addWidget(QLabel("Dokumentkennwort"), 0, 0)
        k1 = QLineEdit(); k1.setEchoMode(QLineEdit.Password); k1.setPlaceholderText("Kennwort")
        k2 = QLineEdit(); k2.setEchoMode(QLineEdit.Password); k2.setPlaceholderText("Kennwort erneut eingeben")
        g.addWidget(k1, 0, 1); g.addWidget(k2, 0, 2)
        g.setColumnStretch(1, 1); g.setColumnStretch(2, 1)
        f.addRow(w)
        w.setProperty("optName", "Dokumentkennwort")
        stand = QLabel(); stand.setWordWrap(True)
        setzen = QPushButton("Kennwort setzen"); weg = QPushButton("Kennwort entfernen")
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(setzen); h.addWidget(weg); h.addStretch(1)
        f.addRow(zeile)
        f.addRow(stand)

        def zeige(meldung: str = ""):
            if not t:
                stand.setText("Kein Dokument geöffnet — das Kennwort gehört zum Dokument im aktuellen Fenster.")
            elif meldung:
                stand.setText(meldung)
            else:
                stand.setText("Das Dokument wird beim Speichern verschlüsselt." if t.meta.get("kennwort")
                              else "Ohne Kennwort — die Datei ist im Klartext lesbar.")
        for c in (k1, k2, setzen, weg):
            c.setEnabled(t is not None)

        def setze():
            if not k1.text():
                zeige("Bitte ein Kennwort eingeben."); return
            if k1.text() != k2.text():
                zeige("Die beiden Eingaben stimmen nicht überein."); return
            t.meta["kennwort"] = k1.text()
            t.editor.document().setModified(True)
            k1.clear(); k2.clear()
            zeige("Gesetzt — das Dokument wird ab dem nächsten Speichern verschlüsselt.")
        setzen.clicked.connect(setze)
        weg.clicked.connect(lambda: (t.meta.pop("kennwort", None), t.editor.document().setModified(True), k1.clear(), k2.clear(),
                                     zeige("Entfernt — gilt ab dem nächsten Speichern.")))
        zeige()
        warn = md_label("**Ein vergessenes Kennwort kann niemand wiederherstellen.** Bewahre es an einem sicheren Ort auf.")
        warn.setWordWrap(True); warn.setStyleSheet("color: palette(mid);")
        f.addRow(warn)
        sperre = QCheckBox("Bearbeitung sperren")
        sperre.setChecked(bool(t and getattr(t, "gesperrt", False))); sperre.setEnabled(t is not None)
        sperre.toggled.connect(lambda on: t and on != bool(getattr(t, "gesperrt", False)) and self.w.toggle_sperre())
        f.addRow(sperre)
        f = p.gruppe("Datenschutz")
        p.haken(f, "sicherheit/markup_oeffnen", "Ausgeblendete Markups beim Öffnen anzeigen", True)
        p.haken(f, "sicherheit/personendaten_weg", "Beim Speichern persönliche Daten entfernen", False)
        p.abschluss()
        return p

    def _verfolgen(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Änderungen verfolgen")
        b = QCheckBox("Änderungen im aktuellen Dokument verfolgen")
        e = self.w.current_editor()
        b.setChecked(bool(e and e.verfolgen)); b.setEnabled(e is not None)
        b.toggled.connect(lambda on: self.w.current_editor() and self.w.current_editor().set_verfolgen(on))
        f.addRow(b)
        m = QCheckBox("Markup anzeigen (Kommentare, Einfügungen, Löschungen)")
        m.setChecked(bool(e.markup) if e else True); m.setEnabled(e is not None)
        m.toggled.connect(lambda on: self.w.current_editor() and self.w.current_editor().set_markup(on))
        f.addRow(m)
        from lunivo_writer.editor import sprechblasen as SB
        from lunivo_writer.ui.document.zusatz_editor import DEL_STILE, FESTE_FARBEN, INS_STILE
        neu = lambda _=None: self.w.markup_neu()                                               # noqa: E731
        f = p.gruppe("Markup")
        p.auswahl(f, "aenderungen/ins_stil", "Einfügungen", INS_STILE, "Unterstrichen", neu)
        p.auswahl(f, "aenderungen/del_stil", "Löschvorgänge", DEL_STILE, "Durchgestrichen", neu)
        p.auswahl(f, "aenderungen/balken", "Geänderte Zeilen (Balken im Rand)", ["links", "rechts", "außen", "keine"], "links", neu)
        p.auswahl(f, "aenderungen/farbe", "Farbe", ["Nach Autor"] + list(FESTE_FARBEN), "Nach Autor", neu)
        f = p.gruppe("Sprechblasen")
        p.auswahl(f, "sprechblasen/verwenden", "Sprechblasen verwenden", SB.VERWENDEN, SB.STANDARD["verwenden"], neu)
        p.haken(f, "sprechblasen/empfohlen", "Empfohlene Breite verwenden (60 mm)", True, neu)
        p.zahl(f, "sprechblasen/breite_mm", "Bevorzugte Breite", 30, 120, 60, " mm", 1, neu)
        p.auswahl(f, "sprechblasen/rand", "Seitenrand", SB.RAND, "Rechts", neu)
        p.haken(f, "sprechblasen/linien", "Verbindungslinien zum Text anzeigen", True, neu)
        f = p.gruppe("Drucken (mit Sprechblasen)")
        p.haken(f, "sprechblasen/drucken", "Sprechblasen mitdrucken und exportieren", False)
        p.auswahl(f, "sprechblasen/ausrichtung", "Papierausrichtung", SB.AUSRICHTUNG, "Automatisch")
        p.hinweis("Einfügungen und Löschungen stehen in einer Farbe je Autor (oder in einer festen Farbe). Der Autor kommt aus "
                  "Optionen ▸ Benutzerinformationen. Änderungen und Kommentare werden in DOCX als echte Überarbeitungen gespeichert. "
                  "Beim Drucken mit Sprechblasen wird die Seite verkleinert, damit rechts oder links Platz für die Blasen bleibt.")
        p.abschluss()
        return p

    # ================= Nur bei Lunivo =================
    def _ki(self, titel):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        p = _Seite(self.w, titel)
        k = self.w.ki.konfig
        geaendert = self.w.ki.geaendert
        f = p.gruppe("Prüfung und KI")
        f.addRow(text_label("KI-Konfiguration", pt=11, umbruch=False))
        combos: dict[str, QComboBox] = {}

        def standard_name() -> str:
            mid = k["modell"]
            if not mid:
                return "(keines)"
            for m in k.alle_modelle():
                if m["id"] == mid:
                    return m["name"]
            return mid[len(K.OLLAMA_MARKE):] if mid.startswith(K.OLLAMA_MARKE) else mid

        def aufgaben_fuellen():
            for aufgabe, c in combos.items():
                c.blockSignals(True); c.clear()
                c.addItem(f"Standard ({standard_name()})", "")
                for m in k.alle_modelle():
                    if aufgabe == "bildgenerierung" and ("bilder" not in m["verwendungFuer"] or not m["id"].startswith(K.EIGEN_MARKE)):
                        continue
                    c.addItem(m["name"] + ("  · lokal" if m["lokal"] else ""), m["id"])
                c.setCurrentIndex(max(0, c.findData(k["aufgaben"].get(aufgabe, ""))))
                c.blockSignals(False)
        for aufgabe, name in K.AUFGABEN:
            c = QComboBox()
            combos[aufgabe] = c
            c.currentIndexChanged.connect(lambda _i, a=aufgabe, c=c: (k.aufgabe_setzen(a, c.currentData() or ""), geaendert.emit()))
            f.addRow(name, c)
        mb = QPushButton("KI-Modelle bearbeiten"); mb.setFlat(True); mb.setCursor(Qt.PointingHandCursor)
        mb.setStyleSheet("QPushButton { color: #5b9bd5; text-align: left; border: none; padding: 4px 0; }")
        f.addRow(mb)

        schluessel = QLineEdit(k["apiKey"]); schluessel.setEchoMode(QLineEdit.Password); schluessel.setPlaceholderText("sk-ant-…")
        schluessel.setProperty("optName", "API-Schlüssel")
        f.addRow("API-Schlüssel", schluessel)
        hinweis = QLabel(); hinweis.setStyleSheet("color: palette(mid); font-size: 9pt;"); hinweis.setWordWrap(True)
        f.addRow(hinweis)
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 0, 0, 0)
        zeigen = QPushButton("Anzeigen"); zeigen.setCheckable(True)
        kopie = QPushButton("Kopieren")
        loeschen = QPushButton("Schlüssel löschen")
        erstellen = QPushButton("Schlüssel erstellen ↗"); erstellen.setFlat(True); erstellen.setCursor(Qt.PointingHandCursor)
        erstellen.setStyleSheet("QPushButton { color: #5b9bd5; border: none; }")
        for b in (zeigen, kopie, loeschen, erstellen):
            h.addWidget(b)
        h.addStretch(1)
        f.addRow(zeile)

        def schluessel_stand():
            hinweis.setText("Gespeichert in " + k.pfad + " (nur für dich lesbar). Bei Nutzung von Claude geht der Text an Anthropic — "
                            "vorher fragt das Programm um Erlaubnis." if k["apiKey"] else
                            "Kein Schlüssel — für das Modell auf diesem Rechner braucht es auch keinen.")
            for b in (zeigen, kopie, loeschen):
                b.setEnabled(bool(schluessel.text().strip()))
        schluessel.editingFinished.connect(lambda: (k.setze("apiKey", schluessel.text().strip()), schluessel_stand(), geaendert.emit()))
        schluessel.textChanged.connect(lambda _t: [b.setEnabled(bool(schluessel.text().strip())) for b in (zeigen, kopie, loeschen)])
        zeigen.toggled.connect(lambda an: (schluessel.setEchoMode(QLineEdit.Normal if an else QLineEdit.Password),
                                           zeigen.setText("Verbergen" if an else "Anzeigen")))
        kopie.clicked.connect(lambda: QApplication.clipboard().setText(schluessel.text().strip()))

        def loesche():
            if QMessageBox.question(self, "Schlüssel löschen", "Den gespeicherten Schlüssel wirklich löschen?") == QMessageBox.Yes:
                schluessel.clear(); k.setze("apiKey", ""); schluessel_stand(); geaendert.emit()
        loeschen.clicked.connect(loesche)
        erstellen.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.anthropic.com/settings/keys")))

        modell = QComboBox()
        f.addRow("KI-Modell", modell)

        def modell_fuellen():
            modell.blockSignals(True); modell.clear()
            modell.addItem("(keines)", "")
            for mid, name in K.MODELLE_FEST:
                modell.addItem(name, mid)
            for m in self.w.ki.ki.ollama_modelle():
                modell.addItem(f"Auf diesem Rechner: {m}", K.OLLAMA_MARKE + m)
            for a in k["anbieter"]:
                modell.addItem(f"{a['name']} ({a['modell']})", K.EIGEN_MARKE + a["id"])
            modell.setCurrentIndex(max(0, modell.findData(k["modell"])))
            modell.blockSignals(False)
        modell.currentIndexChanged.connect(lambda _i: (k.setze("modell", modell.currentData()), aufgaben_fuellen(), geaendert.emit()))

        anb = QWidget(); av = QVBoxLayout(anb); av.setContentsMargins(0, 4, 0, 4); av.setSpacing(6)
        anb.setProperty("optName", "Eigene Anbieter")
        f.addRow(QLabel("Eigene Anbieter"))
        f.addRow(anb)
        neuer = QPushButton("Anbieter hinzufügen …")
        f.addRow(neuer)

        def anbieter_fuellen():
            while av.count():
                it = av.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            if not k["anbieter"]:
                av.addWidget(QLabel("Noch keiner angelegt — Ollama, OpenAI, OpenRouter, Gemini, Mistral …"))
            for a in k["anbieter"]:
                z = QWidget(); zh = QHBoxLayout(z); zh.setContentsMargins(0, 0, 0, 0)
                teile = [a["modell"], "Lokaler Anbieter" if K.ist_lokale_url(a["url"]) else "Über das Internet"]
                zh.addWidget(QLabel(f"{a['name']}  ·  {' · '.join(t for t in teile if t)}"), 1)
                eb = QPushButton("Entfernen")
                eb.clicked.connect(lambda _=False, i=a["id"]: (k.anbieter_entfernen(i), alles_neu(), geaendert.emit()))
                zh.addWidget(eb)
                av.addWidget(z)

        def alles_neu():
            aufgaben_fuellen(); modell_fuellen(); anbieter_fuellen()

        def anbieter_neu():
            from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
            KIEinstellungenDialog(self.w, 0).exec()
            alles_neu(); geaendert.emit()

        def modelle_bearbeiten():
            from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
            KIEinstellungenDialog(self.w, 0).exec()
            alles_neu(); geaendert.emit()
        neuer.clicked.connect(anbieter_neu)
        mb.clicked.connect(modelle_bearbeiten)

        f.addRow(QLabel("Eigene Assistenten"))
        ass = QWidget(); sv = QVBoxLayout(ass); sv.setContentsMargins(0, 4, 0, 4); sv.setSpacing(6)
        ass.setProperty("optName", "Eigene Assistenten")
        f.addRow(ass)
        na = QPushButton("Neuen Assistenten erstellen …")
        f.addRow(na)

        def assistenten_fuellen():
            while sv.count():
                it = sv.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            if not k["assistenten"]:
                sv.addWidget(QLabel("Noch keiner angelegt."))
            for a in k["assistenten"]:
                z = QWidget(); zh = QHBoxLayout(z); zh.setContentsMargins(0, 0, 0, 0)
                zh.addWidget(QLabel(a["name"]), 1)
                eb = QPushButton("Entfernen")
                eb.clicked.connect(lambda _=False, i=a["id"]: (k.assistent_entfernen(i), assistenten_fuellen()))
                zh.addWidget(eb)
                sv.addWidget(z)
        na.clicked.connect(lambda: (self.w.befehle.w_assistentErstellen(), assistenten_fuellen()))

        wen = QComboBox(); wen.addItems(EMPFAENGER)
        wen.setCurrentText(self.w.assistant.thema)
        wen.currentTextChanged.connect(self.w.assistant.setze_thema)
        self.w.assistant.themaGeaendert.connect(lambda t: wen.currentText() != t and (wen.blockSignals(True), wen.setCurrentText(t), wen.blockSignals(False)))
        f.addRow("Für wen der Text ist", wen)

        verbrauch = QWidget(); vh = QHBoxLayout(verbrauch); vh.setContentsMargins(0, 2, 0, 2)
        vh.addWidget(QLabel("Verbrauch"))
        vh.addWidget(QLabel("Noch nichts verbraucht." if not k["kosten"] else f"Bisherige Kosten: {K.als_geld(k['kosten'])}"))
        auf = QPushButton("Guthaben aufladen ↗"); auf.setFlat(True); auf.setCursor(Qt.PointingHandCursor)
        auf.setStyleSheet("QPushButton { color: #5b9bd5; border: none; }")
        auf.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.anthropic.com/settings/billing")))
        vh.addWidget(auf); vh.addStretch(1)
        f.addRow(verbrauch)
        alles_neu(); assistenten_fuellen(); schluessel_stand()
        self.w.ki.geaendert.connect(lambda: (aufgaben_fuellen(), modell_fuellen(), anbieter_fuellen()))
        p.abschluss()
        return p

    def _gedaechtnis(self, titel):
        from PySide6.QtWidgets import QFileDialog, QListWidget
        p = _Seite(self.w, titel)
        g = self.w.assistant.gelernt
        f = p.gruppe("Gelernte Schreibweisen")
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 2, 0, 2)
        lab = QLabel(); lab.setStyleSheet("color: palette(mid);")
        vergessen = QPushButton("vergessen")
        h.addWidget(lab, 1); h.addWidget(vergessen)
        f.addRow(zeile)
        zeile.setProperty("optName", "Gelernte Schreibweisen")
        liste = QListWidget(); liste.setMinimumHeight(120)

        def fuellen():
            d = g.daten
            lab.setText(f"{len(d['woerter'])} eigene Schreibweisen · {len(d['inRuhe'])} Wörter in Ruhe gelassen")
            liste.clear()
            for alt, neu in sorted(d["woerter"].items()):
                liste.addItem(f"{alt} → {neu}")
            for w_ in sorted(d["inRuhe"]):
                liste.addItem(f"{w_} (in Ruhe lassen)")
            vergessen.setEnabled(bool(d["woerter"] or d["inRuhe"] or d["gezeigt"] or d["ki"]))
        f.addRow(liste)
        eb = QPushButton("Markierten Eintrag entfernen")

        def eintrag_weg():
            it = liste.currentItem()
            if not it:
                return
            t = it.text()
            if " → " in t:
                g.daten["woerter"].pop(t.split(" → ")[0], None)
            else:
                g.daten["inRuhe"].pop(t.replace(" (in Ruhe lassen)", ""), None)
            g.speichern(); fuellen(); self.w.assistant.pruefen(voll=True)
        eb.clicked.connect(eintrag_weg)

        def weg():
            if QMessageBox.question(self, "Vergessen", "Wirklich alles Gelernte löschen?") == QMessageBox.Yes:
                g.vergessen(); fuellen(); self.w.assistant.pruefen(voll=True)
        vergessen.clicked.connect(weg)

        def sichern():
            pfad, _ = QFileDialog.getSaveFileName(self, "Gelerntes sichern", "gelernt.json", "JSON (*.json)")
            if pfad:
                try:
                    with open(pfad, "w", encoding="utf-8") as fh:
                        json.dump(g.daten, fh, ensure_ascii=False, indent=1)
                except OSError as ex:
                    QMessageBox.warning(self, "Sichern", f"Das ging nicht: {ex}")

        def einspielen():
            pfad, _ = QFileDialog.getOpenFileName(self, "Gelerntes einspielen", "", "JSON (*.json)")
            if not pfad:
                return
            try:
                with open(pfad, encoding="utf-8") as fh:
                    neu = json.load(fh)
                for key in g.daten:
                    if isinstance(neu.get(key), dict):
                        g.daten[key].update(neu[key])
            except (OSError, ValueError) as ex:
                QMessageBox.warning(self, "Einspielen", f"Das ging nicht: {ex}")
                return
            g.speichern(); fuellen(); self.w.assistant.pruefen(voll=True)
        z2 = QWidget(); h2 = QHBoxLayout(z2); h2.setContentsMargins(0, 2, 0, 2)
        b1 = QPushButton("Sichern"); b2 = QPushButton("Einspielen")
        b1.clicked.connect(sichern); b2.clicked.connect(einspielen)
        h2.addWidget(b1); h2.addWidget(b2); h2.addWidget(eb); h2.addStretch(1)
        f.addRow(z2)
        fuellen()
        p.hinweis("Das Gedächtnis liegt als Datei auf diesem Rechner und wird nur auf deinen Wunsch an eine KI mitgeschickt (als Steckbrief).")
        p.abschluss()
        return p

    def _erweitert(self, titel):
        from lunivo_writer.services.integrations import languagetool, libreoffice
        from lunivo_writer.services.settings_service import data_dir
        p = _Seite(self.w, titel)

        def groesse(pfad) -> str:
            gesamt = 0
            if pfad and os.path.exists(pfad):
                if os.path.isfile(pfad):
                    gesamt = os.path.getsize(pfad)
                for wurzel, _d, dateien in os.walk(pfad):
                    for n in dateien:
                        try:
                            gesamt += os.path.getsize(os.path.join(wurzel, n))
                        except OSError:
                            pass
            mb = gesamt / 1048576
            return "" if not gesamt else (f"{mb:.0f} MB" if mb >= 10 else f"{mb:.1f} MB".replace(".", ","))

        soffice = libreoffice.finde_soffice()
        lo_pfad = os.path.dirname(os.path.realpath(soffice)) if soffice else ""
        lt = languagetool.jar_finden()
        _prog, piper = vorlesen.piper_programm()
        stimmen = vorlesen.piper_stimmen() if piper else []
        schriften = [n for n in LESESCHRIFTEN if n in QFontDatabase.families()]
        schr_ordner = os.path.expanduser("~/.local/share/fonts/lunivo-office")
        karten = [
            ("Umwandlungsprogramm", "ODT, DOC, RTF und EPUB", bool(soffice), lo_pfad, "nicht installiert"),
            ("LanguageTool", "„Gründlich prüfen“ — Grammatik über die eigenen Regeln hinaus", bool(lt), languagetool.ordner(), "./… holen"),
            (f"Stimmen zum Vorlesen ({len(stimmen)})", "aufgenommene Stimmen statt der blechernen des Systems", bool(stimmen), piper, "stimme-holen.sh"),
            (f"Schriften zum leichteren Lesen ({len(schriften)})", ", ".join(schriften) or "OpenDyslexic, Lexend, Atkinson Hyperlegible",
             bool(schriften), schr_ordner, "schrift-holen.sh"),
        ]
        f = p.gruppe("Was zusätzlich geholt wurde")
        for name, beschr, da, pfad, fehlt in karten:
            k = QFrame(); k.setObjectName("optSchriftkarte")
            h = QHBoxLayout(k); h.setContentsMargins(12, 10, 12, 10)
            badge = QLabel("DA" if da else "—")
            badge.setAlignment(Qt.AlignCenter); badge.setFixedWidth(36)
            badge.setStyleSheet("background: %s; color: white; border-radius: 4px; font-weight: 700; font-size: 8pt; padding: 3px;"
                                % ("#3aa57a" if da else "#6b7280"))
            h.addWidget(badge, 0, Qt.AlignTop)
            v = QVBoxLayout(); v.setSpacing(2)
            v.addWidget(text_label(name, fett=True, umbruch=False))
            b = QLabel(beschr if da else f"{beschr} — nicht vorhanden ({fehlt})")
            b.setWordWrap(True); b.setStyleSheet("color: palette(mid); font-style: italic;")
            v.addWidget(b)
            h.addLayout(v, 1)
            gr = QLabel(groesse(pfad) if da else ""); gr.setStyleSheet("color: palette(mid); font-size: 9pt;")
            h.addWidget(gr, 0, Qt.AlignTop)
            f.addRow(k)
        f = p.gruppe("Daten")
        p.zeile(f, data_dir())
        p.abschluss()
        return p


class OptionenDialog(QDialog):
    """Die Optionen als eigenes Fenster (für Aufrufe außerhalb der Datei-Ansicht); gleicher Inhalt wie `OptionenAnsicht`."""

    def __init__(self, fenster, seite: str | None = None):
        super().__init__(fenster)
        self.setWindowTitle("Optionen")
        self.resize(1000, 680)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 8)
        self.ansicht = OptionenAnsicht(fenster, seite)
        self.baum, self.stapel, self.knoten, self.gehe_zu = self.ansicht.baum, self.ansicht.stapel, self.ansicht.knoten, self.ansicht.gehe_zu
        v.addWidget(self.ansicht, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText("Fertig")
        bb.rejected.connect(self.accept)
        v.addWidget(bb)
