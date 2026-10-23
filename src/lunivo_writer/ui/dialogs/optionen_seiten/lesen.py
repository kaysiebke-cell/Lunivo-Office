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
        p = _Seite(self.w, titel)
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
        erlaeutert.setStyleSheet("color: palette(window-text); font-size: 9pt;")
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
        f = p.gruppe("Vorlesen")
        p.aktion("Den Text hören", "Stimme und Tempo …", lambda: self.w.befehle.stimmeWaehlen())
        if not vorlesen.verfuegbar():
            p.hinweis("Es ist keine Sprachausgabe eingerichtet (speech-dispatcher oder Piper).")
        e = p.mehr()
        f = p.unter(e, "Silben farbig (Lesehilfe für Legasthenie)")
        p.haken(f, "lesehilfe/silben/an", "Silben farbig anzeigen", False, lambda _: self.w.silbenfarben_anwenden())
        b = QPushButton("Farben, Darstellung und Mindestlänge einstellen …")
        b.clicked.connect(lambda: self.w.befehle.silbenEinstellen())
        f.addRow(b)
        f = p.unter(e, "Silbentrennung")
        p.auswahl(f, "silben/sprache", "Sprache der Silbentrennung", ["de_DE", "de_AT", "de_CH", "en_US", "en_GB", "fr", "es", "it", "nl_NL", "pl_PL", "tr_TR"], "de_DE")
        self._lese_schriften(p, e)
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


    def _lese_schriften(self, p, e):
        """Die drei Schriften zum leichteren Lesen mit Probe; sagt, ob sie da sind."""
        f = p.unter(e, "Schriften zum leichteren Lesen")
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
            t.setStyleSheet("color: palette(window-text); font-size: 9pt;")
            kv.addWidget(t)
            rh.addWidget(k, 1)
        reihe.setProperty("optName", "Schriften zum leichteren Lesen")
        f.addRow(reihe)


    def _uebersetzung_oeffnen(self) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
        ausfuehren(KIEinstellungenDialog(self.w, 2))
        self.w.ki.geaendert.emit()
