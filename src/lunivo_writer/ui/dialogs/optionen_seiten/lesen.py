"""Optionen: Leichter lesen, Sprache."""
from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QRadioButton, QPushButton, QVBoxLayout, QWidget
from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.ui import lesestufen as LS
from lunivo_writer.services import vorlesen
from lunivo_writer.ui.dialogs.lesehilfe_dialog import PAPIERTOENE
from lunivo_writer.core.farben import Farbe
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import LESESCHRIFTEN, _Seite


class LesenSeiten:
    """Optionen: Leichter lesen, Sprache. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


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
            lab.setStyleSheet(f"background: {PAPIERTOENE.get(str(p.s.get('lesehilfe/papier', 'Weiß')), Farbe.WEISS)}; color: #111417; "
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
            refs["luft"].setCurrentIndex(refs["luft"].findData(st["luft"]))
            refs["groesser"].setCurrentIndex(refs["groesser"].findData(st["groesser"]))
            refs["zurueck"].setCurrentIndex(refs["zurueck"].findData(st["zurueck"]))
            erlaeutert.setText(" ".join(st["text"]))
            anwenden()

        f = p.gruppe("Leichter lesen")
        refs["papier"] = p.auswahl(f, "lesehilfe/papier", "Papierton", list(PAPIERTOENE), "Weiß", anwenden)
        refs["buch"] = p.stufen(f, "lesehilfe/buchstaben", "Buchstabenabstand",
                                LS.BUCHSTABEN, 0.0, anwenden)
        refs["wort"] = p.stufen(f, "lesehilfe/wort", "Wortabstand",
                                LS.WORT, 0.0, anwenden)
        refs["luft"] = p.stufen(f, "lesehilfe/zeilenluft", "Zeilenluft", LS.ZEILENLUFT, 1.0, anwenden)
        f = p.gruppe("Beim Schreiben")
        refs["fokus"] = p.haken(f, "lesehilfe/zeilenfokus", "Zeilenfokus", False, lambda on: self.w.lesehilfe_anwenden())
        refs["groesser"] = p.wahl(f, "lesehilfe/groesser", "Absatz beim Schreiben",
                                  LS.GROESSER, "keine", anwenden)
        refs["zurueck"] = p.wahl(f, "lesehilfe/zurueck", "Übriger Text",
                                 LS.ZURUECK, "keine", anwenden)
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


    def _uebersetzung_oeffnen(self) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
        ausfuehren(KIEinstellungenDialog(self.w, 2))
        self.w.ki.geaendert.emit()


    def _sprache(self, titel):
        p = _Seite(self.w, titel, ["Weitere Prüfsprachen (derzeit Deutsch)"])
        f = p.gruppe("Sprache")
        p.aktion("Sprache für die Überprüfung und Übersetzen nach", "KI-Einstellungen ▸ Sprache …", self._uebersetzung_oeffnen)
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
        p.aktion("Sprache für die Prüfung", "KI-Einstellungen ▸ Sprache …", self._uebersetzung_oeffnen)
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
