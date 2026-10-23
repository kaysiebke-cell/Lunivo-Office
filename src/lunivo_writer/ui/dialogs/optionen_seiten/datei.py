"""Optionen: Bearbeiten, Speichern, Drucken."""
from __future__ import annotations

import os
from PySide6.QtWidgets import QCheckBox, QLineEdit, QMessageBox, QPushButton, QSpinBox
from lunivo_writer.proofing import autokorrektur
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import _Seite


class DateiSeiten:
    """Optionen: Bearbeiten, Speichern, Drucken. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


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
