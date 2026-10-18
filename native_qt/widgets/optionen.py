"""Optionen — das Fenster hinter „☰ Menü ▸ Optionen“ (F9), aufgebaut wie im alten Programm in drei Zweigen:
Leichter lesen · Wie im WPS Writer · Nur bei Lunivo. Links der Baum, rechts die Seite.

Was hier steht, wirkt. Was aus dem alten Fenster noch keine Wirkung hat, steht je Seite unter „Noch nicht umgesetzt“,
damit nichts stillschweigend verschwindet.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMessageBox, QPushButton, QScrollArea, QSpinBox, QStackedWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..services import autokorrektur, ki as K, vorlesen
from ..services.vorhersage import EMPFAENGER
from .lesehilfe_dialog import PAPIERTOENE

LESESCHRIFTEN = ("OpenDyslexic", "Lexend", "Atkinson Hyperlegible")


class _Seite(QWidget):
    """Eine Optionenseite: Gruppen mit Zeilen; Werte stehen sofort in den Einstellungen."""
    def __init__(self, fenster, titel: str, offen: list[str] | None = None):
        super().__init__()
        self.w = fenster
        self.s = fenster.settings
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(24, 16, 24, 16)
        t = QLabel(f"<h2>{titel}</h2>")
        self.lay.addWidget(t)
        self.gruppe_lay = None
        self._offen = offen or []

    def gruppe(self, name: str) -> QFormLayout:
        g = QGroupBox(name)
        f = QFormLayout(g)
        self.lay.addWidget(g)
        return f

    def haken(self, f, key, text, std, wirkt=None):
        c = QCheckBox(text)
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
        l = QLabel(text)
        l.setWordWrap(True)
        l.setStyleSheet("color: palette(mid);")
        self.lay.addWidget(l)

    def abschluss(self):
        if self._offen:
            self.hinweis("<b>Noch nicht umgesetzt</b> (im alten Programm vorhanden): " + "; ".join(self._offen) + ".")
        self.lay.addStretch(1)


class OptionenDialog(QDialog):
    def __init__(self, fenster, seite: str | None = None):
        super().__init__(fenster)
        self.setWindowTitle("Optionen")
        self.resize(900, 640)
        self.w = fenster
        h = QHBoxLayout(self)
        self.baum = QTreeWidget()
        self.baum.setHeaderHidden(True)
        self.baum.setFixedWidth(230)
        self.stapel = QStackedWidget()
        self.stapel.setMinimumWidth(560)
        h.addWidget(self.baum)
        rechts = QVBoxLayout()
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(self.stapel); sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        rechts.addWidget(sc, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText("Fertig")
        bb.rejected.connect(self.accept)
        rechts.addWidget(bb)
        h.addLayout(rechts, 1)
        self.knoten: dict[str, QTreeWidgetItem] = {}
        zweige = [
            ("Leichter lesen", [("lesehilfe", "Lesehilfe", self._lesehilfe), ("schriften", "Schriftarten", self._schriften),
                                ("sprache", "Sprache", self._sprache), ("rechtschreibung", "Rechtschreibprüfung", self._rechtschreibung)]),
            ("Wie im WPS Writer", [("ansicht", "Ansicht", self._ansicht), ("bearbeiten", "Bearbeiten", self._bearbeiten),
                                   ("speichern", "Allgemein und Speichern", self._speichern),
                                   ("sicherung", "Sicherungseinstellungen", self._sicherung),
                                   ("drucken", "Drucken", self._drucken), ("benutzer", "Benutzerinformationen", self._benutzer),
                                   ("sicherheit", "Sicherheit", self._sicherheit),
                                   ("menueband", "Menüband anpassen", self._menueband),
                                   ("schnellzugriff", "Symbolleiste für den Schnellzugriff", self._schnellzugriff),
                                   ("verfolgen", "Änderungen verfolgen", self._verfolgen)]),
            ("Nur bei Lunivo", [("ki", "Schreibhilfe und KI", self._ki), ("gedaechtnis", "Gedächtnis", self._gedaechtnis),
                                ("erweitert", "Erweitert", self._erweitert)]),
        ]
        for zweig, seiten in zweige:
            z = QTreeWidgetItem([zweig])
            z.setFlags(z.flags() & ~Qt.ItemIsSelectable)
            f = z.font(0); f.setBold(True); z.setFont(0, f)
            self.baum.addTopLevelItem(z)
            for key, titel, bauer in seiten:
                it = QTreeWidgetItem([titel])
                it.setData(0, Qt.UserRole, key)
                z.addChild(it)
                self.knoten[key] = it
                self.stapel.addWidget(bauer(titel))
                it.setData(0, Qt.UserRole + 1, self.stapel.count() - 1)
        self.baum.expandAll()
        self.baum.currentItemChanged.connect(lambda cur, _p: cur and cur.data(0, Qt.UserRole + 1) is not None
                                             and self.stapel.setCurrentIndex(cur.data(0, Qt.UserRole + 1)))
        self.gehe_zu(seite or "lesehilfe")

    def gehe_zu(self, key: str):
        it = self.knoten.get(key) or self.knoten["lesehilfe"]
        self.baum.setCurrentItem(it)

    # ================= Leichter lesen =================
    def _lesehilfe(self, titel):
        p = _Seite(self.w, titel, ["Lesestufe", "Zeilenluft", "Absatz beim Schreiben / Übriger Text (Abdunkeln)"])
        f = p.gruppe("Leichter lesen")
        p.auswahl(f, "lesehilfe/papier", "Papierton", list(PAPIERTOENE), "Weiß", lambda _: self.w.lesehilfe_anwenden())
        p.zahl(f, "lesehilfe/buchstaben", "Buchstabenabstand", 0, 6, 0, " px", 1, lambda _: self.w.lesehilfe_anwenden())
        p.zahl(f, "lesehilfe/wort", "Wortabstand", 0, 20, 0, " px", 1, lambda _: self.w.lesehilfe_anwenden())
        f = p.gruppe("Beim Schreiben")
        c = p.haken(f, "lesehilfe/zeilenfokus", "Zeilenfokus", False,
                    lambda on: [t.editor.set_zeilenfokus(on) for t in self.w._doc_tabs()])
        f = p.gruppe("Schrift und Sprache")
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe prüfen (Wellenlinien)", True,
                lambda on: self.w.assistant.setze("wellen", on))
        f = p.gruppe("Vorlesen")
        liste = vorlesen.stimmen()
        v = QComboBox(); v.addItem("Automatisch", "")
        for s in liste:
            v.addItem(s["name"], s["kennung"])
        v.setCurrentIndex(max(0, v.findData(p.s.get("vorlesen/stimme", ""))))
        v.currentIndexChanged.connect(lambda _: p.s.set("vorlesen/stimme", v.currentData()))
        f.addRow("Stimme", v)
        p.zahl(f, "vorlesen/tempo", "Tempo (−100 bis 100)", -100, 100, 0)
        if not vorlesen.verfuegbar():
            p.hinweis("Es ist keine Sprachausgabe eingerichtet (speech-dispatcher oder Piper).")
        f = p.gruppe("Silben farbig (Lesehilfe für Legasthenie)")
        p.haken(f, "lesehilfe/silben/an", "Silben farbig anzeigen", False, lambda _: self.w.silbenfarben_anwenden())
        b = QPushButton("Farben, Darstellung und Mindestlänge einstellen …")
        b.clicked.connect(lambda: self.w.befehle.silbenEinstellen())
        f.addRow(b)
        f = p.gruppe("Silbentrennung")
        p.auswahl(f, "silben/sprache", "Sprache der Silbentrennung", ["de_DE", "de_AT", "de_CH", "en_US", "en_GB", "fr", "es", "it", "nl_NL", "pl_PL", "tr_TR"], "de_DE")
        p.zeile(f, "Ein/Aus: Reiter Schreibhilfe ▸ Sprache ▸ Silbentrennung. Wirkt in Seitenansicht, Druck und PDF; in DOCX wird der Schalter „automatische Silbentrennung“ gespeichert.")
        p.abschluss()
        return p

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
        vorhanden = {n.lower() for n in QFontDatabase.families()}
        for n in LESESCHRIFTEN:
            p.zeile(f, f"{n}: " + ("ist da ✔" if n.lower() in vorhanden else "fehlt — ./schrift-holen.sh holt sie"))
        p.hinweis("Gilt für neue Dokumente. Bestehende Dokumente behalten ihre Schrift.")
        p.abschluss()
        return p

    def _sprache(self, titel):
        p = _Seite(self.w, titel, ["Weitere Prüfsprachen (derzeit Deutsch)", "Alle Prüfoptionen"])
        f = p.gruppe("Sprache")
        c = QComboBox(); c.addItems(K.SPRACHEN)
        c.setCurrentText(self.w.ki.konfig["sprache"])
        c.currentTextChanged.connect(lambda t: (self.w.ki.konfig.setze("sprache", t), self.w.ki.geaendert.emit()))
        f.addRow("Übersetzen nach", c)
        f = p.gruppe("Was geprüft wird")
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe", True, lambda on: self.w.assistant.setze("wellen", on))
        p.abschluss()
        return p

    def _rechtschreibung(self, titel):
        p = _Seite(self.w, titel, ["Immer Korrekturvorschläge unterbreiten", "Grammatik mitprüfen (LanguageTool einrichten, siehe INSTALLATION.md)",
                                   "Benutzerwörterbuch (siehe Gedächtnis)"])
        f = p.gruppe("Rechtschreibprüfung")
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe prüfen", True, lambda on: self.w.assistant.setze("wellen", on))
        p.haken(f, "rsGrossIgnorieren", "Wörter in GROSSBUCHSTABEN ignorieren", True, lambda _: self.w.assistant.pruefen())
        p.haken(f, "rsZahlenIgnorieren", "Wörter mit Zahlen ignorieren", True, lambda _: self.w.assistant.pruefen())
        p.haken(f, "rsPfadeIgnorieren", "Internet- und Netzwerkpfade ignorieren", True, lambda _: self.w.assistant.pruefen())
        b = QPushButton("Weggewinkte Funde wieder anzeigen")
        b.clicked.connect(lambda: (self.w.assistant._weg.clear(), self.w.assistant.pruefen()))
        f.addRow(b)
        p.abschluss()
        return p

    # ================= Wie im WPS Writer =================
    def _ansicht(self, titel):
        p = _Seite(self.w, titel, ["Lineal", "Vertikales Lineal", "Gitternetzlinien",
                                   "Live-Vorschau", "Tipp für Kopf-/Fußzeile",
                                   "Feldfunktionen drucken, Feldschattierung",
                                   "Ausgeblendeter Text, Objektanker"])
        f = p.gruppe("Anzeigen")
        p.haken(f, "ui/marken", "Textbegrenzungen (Eckmarken)", True, self.w.set_marken)
        p.haken(f, "ui/seitenleiste", "Seitenleiste beim Start", True)
        p.haken(f, "ui/navigation", "Navigationsbereich beim Start", False)
        f = p.gruppe("Minisymbolleiste")
        p.haken(f, "ui/mini_auswahl", "Minisymbolleiste beim Markieren von Text zeigen", True)
        p.haken(f, "ui/mini_rechtsklick", "Minisymbolleiste beim Rechtsklick zeigen", True)
        f = p.gruppe("Druckoptionen der Ansicht")
        p.haken(f, "drucken/hervorhebungen", "Hervorhebungen drucken (Textmarker)", True)
        p.haken(f, "drucken/textgrenzen", "Textbegrenzungen drucken (gestrichelter Rahmen um die Textfläche)", False)
        p.haken(f, "drucken/zuschnitt", "Zuschnittsmarken drucken (Ecken der Textfläche)", False)
        p.haken(f, "drucken/textmarken", "Textmarken drucken (in eckigen Klammern)", False)
        f = p.gruppe("Formatierungszeichen")
        p.haken(f, "ui/steuerzeichen", "Absatzmarken, Leerzeichen und Tabstoppzeichen anzeigen", False,
                lambda on: self.w.a_marks.setChecked(on))
        p.haken(f, "ui/statusleiste", "Statusleiste anzeigen", True, lambda on: self.w.statusBar().setVisible(on))
        p.haken(f, "ui/band_doppelklick", "Doppelklick auf einen Reiter blendet das Band aus", True,
                lambda on: setattr(self.w.band, "einklappbar", on))
        p.haken(f, "ui/strg_klick_link", "Strg + Klick öffnet Hyperlinks", True)
        f = p.gruppe("Darstellung")
        p.auswahl(f, "ui/icongroesse", "Symbolgröße", ["klein", "mittel", "gross"], "mittel", lambda _: self.w.ansicht_optionen_anwenden())
        p.zahl(f, "ui/bedienschrift_groesse", "Schriftgröße der Bedienelemente (0 = System)", 0, 24, 0, " pt",
               wirkt=lambda _: self.w.ansicht_optionen_anwenden())
        p.auswahl(f, "theme", "Helligkeit", ["system", "light", "dark"], "system", self.w.set_theme)
        p.abschluss()
        return p

    def _bearbeiten(self, titel):
        p = _Seite(self.w, titel, ["Text mit der Maus verschieben", "Maximale Rückgängig-Schritte",
                                   ])
        f = p.gruppe("AutoKorrektur")
        p.haken(f, "schreibhilfe/autokorr", "AutoKorrektur (Hauptschalter)", True, lambda on: self.w.assistant.setze("autokorr", on))
        for name, (std, text) in autokorrektur.SCHALTER.items():
            p.haken(f, "schreibhilfe/" + name, text, std)
        f = p.gruppe("Eingabe")
        p.haken(f, "bearbeiten/tippen_ersetzt", "Eingabe ersetzt die Markierung", True)
        from ..editor.editor_widget import EINFUEGE_MODI
        p.auswahl(f, "bearbeiten/einfuegen_standard", "Standardeinfügeformat (Strg+V)", EINFUEGE_MODI, EINFUEGE_MODI[0])
        p.haken(f, "bearbeiten/einfuegen_schaltflaeche", "Schaltfläche mit Einfügeoptionen nach dem Einfügen zeigen", True)
        p.haken(f, "schreibhilfe/vorschlaege", "Im Rechtsklickmenü immer Korrekturvorschläge anbieten", True)
        p.haken(f, "bearbeiten/wortweise", "Wortweise markieren (Ziehen mit der Maus erweitert auf ganze Wörter)", True)
        p.haken(f, "autoformat/liste", "Listen beim Tippen erkennen (1.  a)  -  *)", True)
        p.haken(f, "autoformat/punkte", "„- “ und „* “ am Zeilenanfang werden zur Aufzählung", True)
        p.haken(f, "schreibhilfe/akPfade", "Internet- und Netzwerkpfade durch Hyperlinks ersetzen", True)
        p.haken(f, "schreibhilfe/akTabEinzug", "Tab / Rücktaste am Absatzanfang ändert den Einzug", True)
        p.haken(f, "schreibhilfe/akErstzeile", "Leerzeichen am Absatzanfang werden Erstzeileneinzug", False)
        p.haken(f, "schreibhilfe/akZentriert", "Zentrieren hebt den Erstzeileneinzug auf", True)
        f = p.gruppe("Wortvorhersage")
        p.haken(f, "schreibhilfe/vorhersage", "Wortvorhersage", True, lambda on: self.w.assistant.setze("vorhersage", on))
        p.abschluss()
        return p

    def _speichern(self, titel):
        p = _Seite(self.w, titel, ["Bilder nicht komprimieren", "Kompatibilitätsoptionen"])
        f = p.gruppe("Maßeinheit")
        from . import dialogs as _d
        p.auswahl(f, "ui/masseinheit", "Maßeinheit in Dialogen (Seitenränder, Einzüge …)", list(_d.EINHEITEN), "Millimeter", _d.set_einheit)
        f = p.gruppe("Speichern")
        p.auswahl(f, "speichern/standard", "Dateien standardmäßig speichern als", [".docx", ".txt"], ".docx")
        p.zeile(f, "Standardordner (leer = zuletzt benutzter)")
        e = QLineEdit(p.s.get("speichern/ordner", "")); e.textChanged.connect(lambda t: p.s.set("speichern/ordner", t)); f.addRow("Ordner", e)
        f = p.gruppe("Neue Dokumente")
        e = QLineEdit(p.s.get("standard/schrift", "Liberation Sans")); e.textChanged.connect(lambda t: p.s.set("standard/schrift", t)); f.addRow("Schriftart", e)
        p.zahl(f, "standard/groesse", "Schriftgröße", 6, 72, 11, " pt")
        f = p.gruppe("Webseite")
        from ..document_io import formats as _f
        p.auswahl(f, "speichern/codierung", "Webseitencodierung (Speichern als .html)", _f.WEB_CODIERUNGEN, "UTF-8")
        f = p.gruppe("PDF")
        p.haken(f, "pdf/oeffnen", "PDF nach dem Export öffnen", False)
        p.haken(f, "pdf/eigenschaften", "Dokumenteigenschaften (Autor) in das PDF übernehmen", True)
        p.haken(f, "pdf/lz_ueberschriften", "Überschriften als Lesezeichen", False)
        p.haken(f, "pdf/lz_textmarken", "Textmarken übernehmen", False)
        p.haken(f, "pdf/lz_andere", "Titel, Untertitel und Zitat als Lesezeichen (andere Formatvorlagen)", False)
        p.haken(f, "pdf/kommentare", "Kommentare als PDF-Notizen mitnehmen", False)
        f3 = p.gruppe("Vorlagen")
        ve = QLineEdit(p.s.get("vorlagen/ordner", "")); ve.setPlaceholderText("leer = ~/Vorlagen")
        ve.textChanged.connect(lambda t: p.s.set("vorlagen/ordner", t)); f3.addRow("Vorlagenordner", ve)
        p.hinweis("DOCX ist das Austauschformat mit der höchsten Treue. ODT, DOC und RTF gehen über LibreOffice (Datei ▸ Exportieren).")
        p.abschluss()
        return p

    def _sicherung(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Sicherung")
        p.haken(f, "sicherung/aktiv", "Automatisch sichern (Absturzschutz)", True)
        p.haken(f, "sicherung/staende", "Zwischenstände aufheben", False)
        p.zahl(f, "sicherung/tage", "Zwischenstände aufheben (Tage)", 1, 365, 7, " Tage")
        p.zahl(f, "autosave_seconds", "Abstand der automatischen Sicherung", 10, 3600, 60, " s",
               wirkt=lambda v: self.w.autosave.start(int(v) * 1000))
        f2 = p.gruppe("Einstellungen und Gelerntes sichern")
        sb = QPushButton("Sichern …"); zb = QPushButton("Zurückholen …")
        sb.clicked.connect(self._daten_sichern); zb.clicked.connect(self._daten_zurueckholen)
        f2.addRow(sb); f2.addRow(zb)
        p.hinweis("Gesichert werden Gedächtnis und Wörterbuch (ohne API-Schlüssel) als ZIP-Datei.")
        from ..storage import recovery
        p.zeile(f, "Gesichert wird nach: " + recovery.recovery_dir())
        from ..storage.settings import data_dir
        p.zeile(f, "Einstellungen und Daten liegen in: " + data_dir())
        p.abschluss()
        return p

    def _daten_sichern(self):
        import zipfile
        from PySide6.QtWidgets import QFileDialog
        from ..storage.settings import data_dir
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
        from ..storage.settings import data_dir
        pfad, _ = QFileDialog.getOpenFileName(self, "Zurückholen", "", "ZIP (*.zip)")
        if not pfad:
            return
        try:
            with zipfile.ZipFile(pfad) as z:
                if "gelernt.json" in z.namelist():
                    z.extract("gelernt.json", data_dir())
            self.w.assistant.gelernt.laden(); self.w.assistant.pruefen()
        except (OSError, zipfile.BadZipFile) as ex:
            QMessageBox.warning(self, "Zurückholen", f"Das ging nicht: {ex}")
            return
        QMessageBox.information(self, "Zurückholen", "Zurückgeholt.")

    def _drucken(self, titel):
        p = _Seite(self.w, titel, ["Womit das Druckfenster aufgeht", "Textbegrenzungen / Zuschnittsmarken drucken"])
        f = p.gruppe("Drucken")
        p.haken(f, "drucken/hoch", "Hohe Qualität (Druckerauflösung)", True)
        p.haken(f, "drucken/umgekehrt", "Seiten in umgekehrter Reihenfolge drucken", False)
        p.haken(f, "drucken/hintergrund", "Hintergrundfarben und Bilder drucken", True)
        p.haken(f, "drucken/leere", "Leere Seiten drucken", True)
        p.haken(f, "drucken/felder", "Felder (Verzeichnisse) vor dem Drucken aktualisieren", True)
        p.auswahl(f, "drucken/duplex", "Beidseitig von Hand", ["alle", "vorder", "rueck"], "alle")
        p.hinweis("Gedruckt wird über das Druckfenster des Systems (Datei ▸ Drucken). Kopf-/Fußzeile und Seitenzahlen werden mitgedruckt.")
        p.abschluss()
        return p

    def _menueband(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Register")
        p.zeile(f, "Reiter ein- und ausblenden und die Reihenfolge ändern.")
        b = QPushButton("Register anpassen …"); b.clicked.connect(self.w.befehle.registerAnpassen); f.addRow(b)
        f = p.gruppe("Aussehen")
        b2 = QPushButton("Benutzeroberfläche wählen …"); b2.clicked.connect(self.w.befehle.benutzeroberflaeche); f.addRow(b2)
        b3 = QPushButton("Symbole austauschen …"); b3.clicked.connect(self.w.befehle.symbolTauschen); f.addRow(b3)
        b4 = QPushButton("Auf die Vorgabe zurücksetzen …"); b4.clicked.connect(self.w.befehle.vorlagenZurueck); f.addRow(b4)
        p.abschluss()
        return p

    def _schnellzugriff(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Schnellzugriff")
        p.zeile(f, "Welche Knöpfe neben dem ☰-Menü stehen.")
        b = QPushButton("Schnellzugriff anpassen …"); b.clicked.connect(self.w.befehle.schnellzugriffAnpassen); f.addRow(b)
        p.abschluss()
        return p

    def _benutzer(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Benutzerdaten")
        e = QLineEdit(p.s.get("benutzer/name", ""))
        e.textChanged.connect(lambda t: p.s.set("benutzer/name", t))
        f.addRow("Name (Autor in DOCX-Dokumenten)", e)
        for key, text in (("benutzer/initialen", "Initialen (Kommentare)"), ("benutzer/strasse", "Straße und Hausnummer"),
                          ("benutzer/plz_ort", "PLZ und Ort"), ("benutzer/ort", "Ort (für „Ort, Datum“)"),
                          ("benutzer/telefon", "Telefon"), ("benutzer/mail", "E-Mail")):
            le = QLineEdit(p.s.get(key, ""))
            le.textChanged.connect(lambda t, k=key: p.s.set(k, t))
            f.addRow(text, le)
        p.haken(f, "benutzer/verwenden", "Benutzerdaten in Dokumenten verwenden", True)
        p.haken(f, "sicherheit/personendaten_weg", "Beim Speichern persönliche Daten entfernen", False)
        p.abschluss()
        return p

    def _sicherheit(self, titel):
        p = _Seite(self.w, titel, ["Ausgeblendete Markups beim Öffnen anzeigen"])
        f = p.gruppe("Kennwortschutz (aktuelles Dokument)")
        t = self.w.current_tab()
        lab = QLabel()
        f.addRow(lab)

        def stand():
            lab.setText("Kein Dokument geöffnet." if not t else
                        "Das Dokument wird beim Speichern verschlüsselt." if t.meta.get("kennwort") else "Kein Kennwort gesetzt.")
        stand()
        if t:
            setzen = QPushButton("Kennwort setzen / ändern …")
            weg = QPushButton("Kennwort entfernen")

            def setze():
                from PySide6.QtWidgets import QInputDialog
                a, ok = QInputDialog.getText(self, "Kennwort", "Neues Kennwort:", QLineEdit.Password)
                if not ok or not a:
                    return
                b, ok = QInputDialog.getText(self, "Kennwort", "Zur Bestätigung noch einmal:", QLineEdit.Password)
                if not ok or a != b:
                    QMessageBox.information(self, "Kennwort", "Die Eingaben stimmen nicht überein.")
                    return
                t.meta["kennwort"] = a
                t.editor.document().setModified(True)
                stand()
            setzen.clicked.connect(setze)
            weg.clicked.connect(lambda: (t.meta.pop("kennwort", None), t.editor.document().setModified(True), stand()))
            f.addRow(setzen); f.addRow(weg)
        p.hinweis("Verschlüsselt wird DOCX nach dem Office-Standard (AES) mit dem Paket msoffcrypto-tool. Ein vergessenes Kennwort "
                  "lässt sich nicht wiederherstellen.")
        f = p.gruppe("Datenschutz")
        p.haken(f, "sicherheit/personendaten_weg", "Beim Speichern persönliche Daten (Autor) entfernen", False)
        p.abschluss()
        return p

    def _verfolgen(self, titel):
        p = _Seite(self.w, titel, ["Sprechblasen (Breite, Seitenrand, Verbindungslinien, Drucken mit Sprechblasen)",
                                   "Farbe und Darstellung je Änderungsart einstellen"])
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
        p.hinweis("Einfügungen stehen unterstrichen, Löschungen durchgestrichen, in einer Farbe je Autor. Der Autor kommt aus "
                  "Optionen ▸ Benutzerinformationen. Änderungen und Kommentare werden in DOCX als echte Überarbeitungen gespeichert.")
        p.abschluss()
        return p

    # ================= Nur bei Lunivo =================
    def _ki(self, titel):
        p = _Seite(self.w, titel)
        k = self.w.ki.konfig
        f = p.gruppe("Modell")
        c = QComboBox()
        c.addItem("(keines)", "")
        for mid, name in K.MODELLE_FEST:
            c.addItem(name, mid)
        modelle = self.w.ki.ki.ollama_modelle()
        for m in modelle:
            c.addItem(f"Auf diesem Rechner: {m}", K.OLLAMA_MARKE + m)
        for a in k["anbieter"]:
            c.addItem(f"{a['name']} ({a['modell']})", K.EIGEN_MARKE + a["id"])
        c.setCurrentIndex(max(0, c.findData(k["modell"])))
        c.currentIndexChanged.connect(lambda _: (k.setze("modell", c.currentData()), self.w.ki.geaendert.emit()))
        f.addRow("KI-Modell", c)
        if not modelle:
            p.zeile(f, "Ollama ist auf diesem Rechner nicht erreichbar — oder es ist kein Modell geholt.")
        f = p.gruppe("Claude (Anthropic)")
        e = QLineEdit(k["apiKey"]); e.setEchoMode(QLineEdit.Password); e.setPlaceholderText("Schlüssel (sk-ant-…)")
        e.editingFinished.connect(lambda: (k.setze("apiKey", e.text().strip()), self.w.ki.geaendert.emit()))
        f.addRow("Schlüssel", e)
        f.addRow(QLabel(f"Gespeichert in {k.pfad} (nur für Sie lesbar). Bei Nutzung geht der Text an Anthropic — "
                        "vorher fragt das Programm um Erlaubnis."))
        p.zeile(f, f"Bisherige Kosten: {(K.als_geld(k['kosten']) if k['kosten'] else '0 $')}")
        f = p.gruppe("Anbieter und Aufgaben")
        p.zeile(f, "Eigene Anbieter (OpenAI-kompatibel, auch Ollama unter /v1) und welches Modell welche Aufgabe übernimmt — "
                   "Chatbot, Zusammenfassen, Übersetzung, Textanalyse, Bildgenerierung.")
        for text, fn in (("KI-Konfiguration …", self.w.befehle.w_kiKonfiguration),
                         ("Eigenen Anbieter hinzufügen …", self.w.befehle.w_eigenenAnbieterHinzufuegen)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, fn=fn: fn())
            f.addRow(b)
        f = p.gruppe("Für wen schreiben Sie? (Standard)")
        e2 = QComboBox(); e2.addItems(EMPFAENGER)
        e2.setCurrentText(self.w.assistant.thema)
        e2.currentTextChanged.connect(self.w.assistant.setze_thema)
        f.addRow("Empfänger", e2)
        p.abschluss()
        return p

    def _gedaechtnis(self, titel):
        p = _Seite(self.w, titel)
        g = self.w.assistant.gelernt
        f = p.gruppe("Was das Programm gelernt hat")
        lab = QLabel()
        f.addRow(lab)

        def stand():
            d = g.daten
            lab.setText(f"{len(d['woerter'])} Wörter, die Sie richtiggestellt haben · {len(d['inRuhe'])} Wörter, die in Ruhe bleiben.")
        stand()
        f = p.gruppe("Gelernte Schreibweisen")
        from PySide6.QtWidgets import QListWidget
        liste = QListWidget(); liste.setMinimumHeight(140)

        def fuellen():
            liste.clear()
            for alt, neu in sorted(g.daten["woerter"].items()):
                liste.addItem(f"{alt} → {neu}")
            for w_ in sorted(g.daten["inRuhe"]):
                liste.addItem(f"{w_} (in Ruhe lassen)")
        fuellen()
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
            g.speichern(); fuellen(); stand(); self.w.assistant.pruefen()
        eb.clicked.connect(eintrag_weg)
        f.addRow(eb)
        b = QPushButton("Alles Gelernte vergessen")

        def weg():
            if QMessageBox.question(self, "Vergessen", "Wirklich alles Gelernte löschen?") == QMessageBox.Yes:
                g.vergessen(); fuellen(); stand(); self.w.assistant.pruefen()
        b.clicked.connect(weg)
        f.addRow(b)
        p.hinweis("Das Gedächtnis liegt als Datei auf diesem Rechner und wird nur auf Ihren Wunsch an eine KI mitgeschickt (als Steckbrief).")
        p.abschluss()
        return p

    def _erweitert(self, titel):
        from ..integrations import languagetool, libreoffice
        from ..storage.settings import data_dir
        p = _Seite(self.w, titel)
        f = p.gruppe("Angebundene Programme")
        p.zeile(f, "LibreOffice (ODT/DOC/RTF-Umwandlung): " + (libreoffice.finde_soffice() or "nicht installiert"))
        p.zeile(f, "LanguageTool (gründliche Prüfung): " + ("bereit" if languagetool.verfuegbar() else "nicht eingerichtet"))
        p.zeile(f, "Sprachausgabe: " + ("Piper" if vorlesen.piper_da() else "speech-dispatcher" if vorlesen.spd_da() else "nicht eingerichtet"))
        f = p.gruppe("Daten")
        p.zeile(f, data_dir())
        p.abschluss()
        return p
