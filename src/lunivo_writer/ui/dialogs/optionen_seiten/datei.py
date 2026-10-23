"""Optionen: Schreiben, Speichern, Drucken und PDF."""
from __future__ import annotations

import os
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QComboBox, QLineEdit, QMessageBox, QPushButton, QSpinBox
from lunivo_writer.proofing import autokorrektur
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import _Seite


class DateiSeiten:
    """Optionen: Schreiben, Speichern, Drucken und PDF. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


    def _schreiben(self, titel):
        """Schrift für neuen Text, Prüfung, AutoKorrektur; im Einzelnen eingeklappt (alle AutoKorrektur-Fälle bleiben erhalten)."""
        p = _Seite(self.w, titel)
        f = p.gruppe("Schrift für neuen Text")
        fam = QComboBox(); fam.setEditable(True); fam.setMinimumHeight(32)
        fam.addItems(sorted(set(QFontDatabase.families())))
        fam.setCurrentText(p.s.get("standard/schrift", "Liberation Sans"))
        fam.currentTextChanged.connect(lambda t: p.s.set("standard/schrift", t))
        fam.setAccessibleName("Schrift für neuen Text")
        f.addRow("Schrift", fam)
        p.zahl(f, "standard/groesse", "Größe", 6, 72, 11, " pt", 1)
        f = p.gruppe("Prüfen")
        p.haken(f, "schreibhilfe/wellen", "Rechtschreibung während der Eingabe prüfen", True, lambda on: self.w.assistant.setze("wellen", on))
        p.haken(f, "rsGrammatik", "Grammatik mitprüfen", True, lambda _: self.w.assistant.pruefen(voll=True))
        self._silbentrennung_haken(p, f)
        p.aktion("Sprache für die Prüfung und Übersetzen nach", "KI-Einstellungen ▸ Sprache …", self._uebersetzung_oeffnen)
        f = p.gruppe("AutoKorrektur")
        p.haken(f, "schreibhilfe/autokorr", "AutoKorrektur", True, lambda on: self.w.assistant.setze("autokorr", on))
        p.haken(f, "schreibhilfe/vorhersage", "Wortvorhersage", True, lambda on: self.w.assistant.setze("vorhersage", on))
        e = p.mehr()
        f = p.unter(e, "AutoKorrektur: Groß- und Kleinschreibung")
        for name in ("akSatzGross", "akWochentage", "akFeststelltaste", "akOrdnungszahlen"):
            std, text = autokorrektur.SCHALTER[name]
            p.haken(f, "schreibhilfe/" + name, text, std)
        f = p.unter(e, "AutoKorrektur: Zeichen")
        for name in ("akAnfuehrung", "akGedankenstrich", "akAuslassung"):
            std, text = autokorrektur.SCHALTER[name]
            p.haken(f, "schreibhilfe/" + name, text, std)
        p.haken(f, "schreibhilfe/akPfade", "Internet- und Netzwerkpfade durch Hyperlinks ersetzen", True)
        f = p.unter(e, "AutoKorrektur: Einzüge und Leerzeichen")
        p.haken(f, "schreibhilfe/akErstzeile", "Leerzeichen am Absatzanfang mit Erstzeileneinzug", False)
        p.haken(f, "schreibhilfe/akRechtsLeer", "Leerzeichenformat am Ende rechtsbündiger Zeilen anpassen", False)
        p.haken(f, "schreibhilfe/akZentriert", "Bei zentriertem Ausrichten Erstzeileneinzug löschen", True)
        p.haken(f, "schreibhilfe/akTabEinzug", "Tabulator und Rücktaste setzen den Einzug", True)
        f = p.unter(e, "Prüfung im Einzelnen")
        p.haken(f, "schreibhilfe/vorschlaege", "Immer Korrekturvorschläge unterbreiten", True)
        p.haken(f, "rsGrossIgnorieren", "Wörter in GROSSBUCHSTABEN ignorieren", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.haken(f, "rsZahlenIgnorieren", "Wörter mit Zahlen ignorieren", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.haken(f, "rsPfadeIgnorieren", "Internet- und Netzwerkpfade ignorieren", True, lambda _: self.w.assistant.pruefen(voll=True))
        p.aktion("Weggewinkte Funde wieder anzeigen", "Wieder anzeigen",
                 lambda: (self.w.assistant._weg.clear(), self.w.assistant.pruefen(voll=True)))
        p.aktion("Gründlich prüfen", "Gründlich prüfen …", lambda: self.w.befehle.tun("gruendlichPruefen"))
        f = p.unter(e, "AutoFormat")
        p.haken(f, "autoformat/liste", "Automatisch nummerierte Listen", True)
        p.haken(f, "autoformat/punkte", "Aufzählungen erkennen", True)
        p.haken(f, "schreibhilfe/akKreiszahl", "Zahl automatisch im Kreis", False)
        f = p.unter(e, "Bearbeiten und Einfügen")
        p.haken(f, "bearbeiten/wortweise", "Wortweise markieren", True)
        p.haken(f, "bearbeiten/ziehen", "Text mit der Maus verschieben", True, lambda _: self.w.lesehilfe_anwenden())
        p.haken(f, "bearbeiten/tippen_ersetzt", "Tippen ersetzt die Auswahl", True)
        p.haken(f, "bearbeiten/einfuegen_schaltflaeche", "Schaltfläche nach dem Einfügen", True)
        p.haken(f, "bearbeiten/mittlere_taste", "Mittlere Maustaste fügt ein", True)
        from lunivo_writer.ui.document.document_editor import EINFUEGE_MODI
        p.wahl(f, "bearbeiten/einfuegen_standard", "Standardeinfügeformat", [(m, m) for m in EINFUEGE_MODI], EINFUEGE_MODI[0])
        f = p.unter(e, "Eigenes Wörterbuch und gelernte Schreibweisen")
        f.addRow(self._gedaechtnis(""))
        p.abschluss()
        return p


    def _speichern(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Speichern")
        p.wahl(f, "speichern/standard", "Dateien als Standard speichern", [("Microsoft Word (.docx)", ".docx"), ("Textdatei (.txt)", ".txt")], ".docx")
        p.pfad(f, "speichern/ordner", "Ordner zum Speichern", "Zuletzt benutzter Ordner")
        from lunivo_writer.ui.dialogs import dokument_dialoge as _d
        p.wahl(f, "ui/masseinheit", "Maßeinheit", [(n, n) for n in _d.EINHEITEN], "Millimeter", _d.set_einheit)
        f = p.gruppe("Sicherung")
        p.wahl(f, "sicherung/aktiv", "Wann gesichert wird", [("Laufend, nach jeder Änderung", True), ("Nie", False)], True)
        minuten = QSpinBox(); minuten.setRange(1, 120); minuten.setSuffix(" min"); minuten.setMinimumHeight(32)
        minuten.setValue(max(1, p.s.get_int("autosave_seconds", 60) // 60))

        def neu(m):
            p.s.set("autosave_seconds", m * 60)
            self.w.autosave.start(m * 60 * 1000)
        minuten.valueChanged.connect(neu)
        f.addRow("Abstand (Minuten)", minuten)
        e = p.mehr()
        f = p.unter(e, "Weiteres zum Speichern")
        p.haken(f, "start/letztes_oeffnen", "Beim Start das zuletzt geschriebene Dokument öffnen", False)
        p.haken(f, "speichern/bilder_nicht_komprimieren", "Bilder in der Datei nicht komprimieren", True)
        p.wahl(f, "ausgabe/ppi", "Standard-Ausgabeziel",
               [(t, t) for t in ("96 ppi (Bildschirm)", "150 ppi (Web, Entwurf)", "220 ppi (Druck)", "330 ppi (hohe Qualität)")],
               "150 ppi (Web, Entwurf)")
        p.pfad(f, "vorlagen/ordner", "Eigene Vorlagen", "~/Vorlagen")
        f = p.unter(e, "Zwischenstände")
        p.zahl(f, "sicherung/tage", "Aufbewahren (Tage)", 1, 365, 7, " Tage")
        p.aktion("Zwischenstände löschen", "Zwischenstände löschen", self._zwischenstaende_loeschen)
        f = p.unter(e, "Gedächtnis und Wörterbuch sichern")
        p.aktion("Sichern und zurückholen", "Sichern …", self._daten_sichern)
        zb = QPushButton("Einspielen …"); zb.clicked.connect(self._daten_zurueckholen)
        f.addRow(zb)
        ort = QLineEdit(p.s.q.fileName()); ort.setReadOnly(True); ort.setAccessibleName("Ort der Einstellungsdatei")
        f.addRow("Einstellungsdatei", ort)
        f = p.unter(e, "Dokument schützen und Änderungen")
        p.aktion("Kennwort, Bearbeitung sperren, Datenschutz", "Kennwort und Datenschutz …", lambda: self._anpassen("sicherheit"))
        p.aktion("Änderungen verfolgen: Markup, Farben, Sprechblasen", "Änderungen verfolgen …", lambda: self._anpassen("verfolgen"))
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
        """Drucken und PDF auf einer Seite: das Häufige sichtbar, der Rest eingeklappt."""
        p = _Seite(self.w, titel)
        f = p.gruppe("Drucken")
        p.haken(f, "drucken/hoch", "Hohe Qualität", True)
        p.haken(f, "drucken/hintergrund", "Hintergrundfarben und -bilder drucken", True)
        f = p.gruppe("PDF")
        p.haken(f, "pdf/oeffnen", "PDF nach dem Export öffnen", False)
        p.haken(f, "pdf/lz_ueberschriften", "Überschriften als Lesezeichen", False)
        e = p.mehr()
        f = p.unter(e, "Drucken im Einzelnen")
        p.wahl(f, "drucken/vorgabe", "Womit das Druckfenster aufgeht", [("Alle Seiten", "Alle Seiten"), ("Aktuelle Seite", "Aktuelle Seite")], "Alle Seiten")
        p.haken(f, "drucken/umgekehrt", "Umgekehrte Reihenfolge", False)
        p.haken(f, "drucken/zeichnungen", "Zeichnungsobjekte drucken", True)
        p.haken(f, "drucken/leere", "Leere Seiten mitdrucken", True)
        p.haken(f, "drucken/felder", "Felder vor dem Drucken aktualisieren", True)
        p.wahl(f, "drucken/versteckt", "Ausgeblendeter Text", [("Ausgeblendeten Text nicht drucken", False), ("Ausgeblendeten Text drucken", True)], False)
        f = p.unter(e, "PDF im Einzelnen")
        p.haken(f, "pdf/kommentare", "Kommentare als PDF-Notizen mitnehmen", False)
        p.haken(f, "pdf/eigenschaften", "Dokumenteigenschaften (Autor) in das PDF übernehmen", True)
        p.haken(f, "pdf/lz_textmarken", "Textmarken übernehmen", False)
        p.hinweis("Gedruckt wird über das Druckfenster des Systems (Datei ▸ Drucken). Kopf-/Fußzeile und Seitenzahlen werden mitgedruckt.")
        p.abschluss()
        return p
