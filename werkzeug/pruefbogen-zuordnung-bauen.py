#!/usr/bin/env python3
"""Schreibt doku/native-qt/pruefbogen/zuordnung.json — die von Hand begründete Zuordnung Prüfpunkt → native Fassung.

Jede Zeile: "Kategorie|Punkt": {"status": "✅|◐|⬜", "wo": "…"}. Ändert sich der Stand, wird DIESE Datei angepasst und
danach werkzeug/pruefbogen-abgleich.py ausgeführt. Kein Status ohne Beleg im Code oder in tests/.
"""
import json
import os

Z = {}


def s(cat, punkte, status, wo):
    for p in punkte.split(";"):
        p = p.strip()
        if p:
            Z[f"{cat}|{p}"] = {"status": status, "wo": wo}


OK, TEIL, OFFEN = "✅", "◐", "⬜"
# ---------------------------------------------------------------- DATEI / MENÜ
s("DATEI", "Neu; Öffnen; Speichern; Speichern unter; Schließen; Drucken; Druckvorschau; Als PDF exportieren", OK, "Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)")
s("DATEI", "Zuletzt geöffnet; Umbenennen; Beenden; Optionen (F9)", OK, "☰-Menü (widgets/menue_tafel.py), Optionen F9")
s("DATEI", "Hilfe > Über Lunivo Office", OK, "☰-Menü ▸ Hilfe ▸ Über")
s("DATEI", "Druckereinstellungen; Dokumenteigenschaften", TEIL, "Drucken öffnet den Systemdialog; Dokumentinformationen nur lesend")
s("DATEI", "Neu aus Vorlage; Vorlagenordner; Hilfe > Handbuch; Hilfe > Tastenkürzel; Hilfe > Erweiterungen", OFFEN, "nicht übertragen")
s("MENÜ UND SCHNELLZUGRIFF", "☰ Menü links vor den Reitern; Tafel mit zwei Spalten; Untermenü füllt die rechte Spalte, kein eigenes Fenster; Liste zuletzt verwendeter Dateien rechts; × nimmt einen Eintrag aus der Liste; ↻ holt die Liste neu; Schnellzugriff in der Reiterzeile", OK, "widgets/menue_tafel.py, widgets/register_band.py")
s("MENÜ UND SCHNELLZUGRIFF", "Kein Datei-Reiter mehr", TEIL, "Widerspruch: die neue Struktur („1. DATEI“) hat einen Datei-Reiter — beides ist vorhanden")
s("MENÜ UND SCHNELLZUGRIFF", "☰ Menü auch am Anfang der Symbolleiste", TEIL, "widgets/symbolleisten.py gebaut, noch nicht als Oberfläche wählbar")
s("MENÜ UND SCHNELLZUGRIFF", "Als Bild exportieren (PNG); Dokumentverschlüsselung", OFFEN, "nicht übertragen")
# ---------------------------------------------------------------- START
s("START > Zwischenablage", "Verlauf > Rückgängig; Verlauf > Wiederholen", OK, "Schnellzugriff (wie im Bogen: dort statt im Reiter)")
s("START > Schriftart", "Schriftart; Schriftgröße", OK, "Felder im Band (widgets/register_band.py)")
s("START > Schriftart", "Unterstreichungsart", OFFEN, "nicht übertragen")
s("START > Absatzlayout", "Einzug genau", TEIL, "Absatz-Dialog (widgets/dialogs.py) — einfacher als das Vorlagenbild (zwei Karteireiter, Vorschau)")
s("START > Einstellungen", "Optionen", OK, "Datei-Reiter / ☰ / F9")
s("START > Stile & Bearbeiten", "Formatvorlage auswählen", OK, "Stilkatalog + Feld im Band")
s("START > Stile & Bearbeiten", "Formatvorlagen verwalten", OFFEN, "nicht übertragen")
# ---------------------------------------------------------------- EINFÜGEN / LAYOUT
s("EINFÜGEN", "Kopfzeile; Fußzeile", OK, "Dialoge (widgets/dialogs.py), PDF/Druck/DOCX getestet")
s("EINFÜGEN", "Datum; Uhrzeit", TEIL, "Datum einfügen; Fenster mit Formatliste/Sprache fehlt")
s("EINFÜGEN", "Zeichnen; Textbaustein; Schnellbaustein", OFFEN, "nicht übertragen")
s("SEITENLAYOUT", "Papierformat", OK, "Reiter Seitenlayout ▸ Größe (Befehle.w_setzePapier)")
s("SEITENLAYOUT", "Textumbruch; Seitenrahmen; Bild/Objekt anordnen", OFFEN, "nicht übertragen")
s("SCHREIBHILFE (Lunivo)", "KI > Vorschläge; Anzeigen > Optionen", OK, "Seitenleiste / KI-Reiter (test_schreibhilfe)")
s("SENDUNGEN (Lunivo)", "Umschlag; Etiketten; Seriendruck-Assistent; Seriendruckfeld; Adressblock; Regeln; Ergebnisse anzeigen; Formular > Kontrollkästchen; Formular > Schaltfläche", OFFEN, "Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten")
s("KONTEXTTABELLEN", "Tabellenwerkzeuge", TEIL, "Reiter erscheint in der Tabelle (test_tabellentools_wirken); ohne Tabellenformatvorlagen")
s("KONTEXTTABELLEN", "Kopf- und Fußzeilenwerkzeuge", TEIL, "Reiter vorhanden, Kopf/Fuß über Dialog statt am Blatt")
s("KONTEXTTABELLEN", "Zeichentools; Diagrammtools; SmartArt-Tools; Gleichungswerkzeuge", OFFEN, "nicht übertragen")
# ---------------------------------------------------------------- LANGUAGE BRIDGE
LB = "services/writing_assistant.py"
s("LANGUAGE BRIDGE (Architektur)", "Zentrale Sprachkontext-Verwaltung; Keine parallelen Wörterbücher; Benutzerwörter zentral speichern; Akzeptierte Korrektionen speichern", OK, LB + ", storage/gelernt.py")
s("LANGUAGE BRIDGE (Architektur)", "Dokumentversion-Tracking", OK, "QTextDocument.revision() — verworfen, wenn sich der Text änderte (test_ki_korrektur_ende_zu_ende)")
s("LANGUAGE BRIDGE (Architektur)", "Prüfungs-ID-System; Einheitlicher Fehlerstatus; Fehler-Lebenszyklus (active/accepted/ignored/corrected); Ignorierte Wörter zentral speichern", TEIL, "Revision statt Prüf-ID; Fund = dict; Zustände nur angenommen/weggewinkt")
s("LANGUAGE BRIDGE (Spelling Engine)", "Native Browser-Spellcheck deaktiviert", OK, "gegenstandslos: kein Browser")
s("LANGUAGE BRIDGE (Spelling Engine)", "Lunivo-Regeln verwenden statt Browser; Benutzerwörter in Rechtschreibung beachten", OK, "services/pruefung.py (Parität zu pruefung.js getestet)")
s("LANGUAGE BRIDGE (Spelling Engine)", "Ignorierte Wörter in Rechtschreibung beachten; Fehler als unified language-issue", TEIL, "inRuhe/weggewinkt beachtet; einheitliches Fund-dict")
s("LANGUAGE BRIDGE (Grammar Engine)", "Dieselbe Sprachkontext wie Spelling; Grammatikregeln aus regeln.js nutzen", OK, "gleiche Engine, regeln.js gelesen")
s("LANGUAGE BRIDGE (Grammar Engine)", "Benutzerwörter in Grammatik beachten; Fehler als unified language-issue", TEIL, "gemeinsame Funde")
s("LANGUAGE BRIDGE (AI Engine)", "Asynchrone KI-Requests mit Validierung; Dokumentversion überprüfen; Keine veralteten Ergebnisse akzeptieren", OK, "services/ki_dienst.py (Revision geprüft)")
s("LANGUAGE BRIDGE (AI Engine)", "CheckId überprüfen", TEIL, "Revision statt Check-ID")
s("LANGUAGE BRIDGE (AI Engine)", "KI-Konfidenz-Score speichern", OFFEN, "nicht übertragen")
s("LANGUAGE BRIDGE (Fehler-Zusammenführung)", "Fehler-Signatur für Identify verwenden", OK, "WritingAssistant._key")
s("LANGUAGE BRIDGE (Fehler-Zusammenführung)", "Mehrere Quellen für gleiche Position zusammenführen; Hochwertige Vorschläge nicht überschreiben", TEIL, "LanguageTool-Funde ergänzen nur nicht überlappende (WritingAssistant._lt_fertig)")
s("LANGUAGE BRIDGE (Fehler-Zusammenführung)", "Konflikt-Auflösung nach Quelle/Konfidenz/Typ", OFFEN, "nicht übertragen")
s("LANGUAGE BRIDGE (Invalidierung & Debouncing)", "Debouncing für schnelle Eingaben; Vollständige Prüfung möglich (Gründlich prüfen)", OK, "Timer 900 ms; Gründlich prüfen")
s("LANGUAGE BRIDGE (Invalidierung & Debouncing)", "Bereichs-Invalidierung bei Änderungen; Sicherheitsbereich um geänderte Stelle", OFFEN, "es wird der ganze Text neu geprüft")
s("SCHREIBHILFE (Sidebar-Integration)", "Fehler aus Language Bridge anzeigen; Rote Wellenlinien aus Bridge-Status; Fehler annehmen/ignorieren/korrigieren", OK, "widgets/schreibhilfe_panel.py, editor_widget.set_wellen")
s("SCHREIBHILFE (Sidebar-Integration)", "Kontextmenü für Fehler-Aktionen", OFFEN, "Rechtsklick-Menü fehlt")
s("SCHREIBHILFE (Sidebar-Integration)", "Schalter 'Rote Wellenlinien' zeigt/versteckt nur", TEIL, "Schalter hält auch die Prüfung an")
s("SCHREIBHILFE (Menü-Integration)", "Prüfen-Knopf löst check() aus; Gründlich prüfen-Knopf für volle Prüfung; Welche Hilfe wann anzeigen", OK, "Seitenleiste + Band")
s("SCHREIBHILFE (Menü-Integration)", "Schreibhilfe-Register im Band", TEIL, "nach der neuen Struktur in der rechten Seitenleiste (Bereich „Schreibhilfe“)")
s("SCHREIBHILFE (Menü-Integration)", "Vorlesen-Integration", TEIL, "services/vorlesen.py — nur mit Attrappe getestet")
s("SCHREIBHILFE (Menü-Integration)", "Beim Schreiben-Optionen; KI-Korrektur-Optionen; Anzeigen-Optionen", TEIL, "Optionen-Fenster, nicht alle Schalter des Vorbilds")
s("DOKUMENTMODELL (Structure)", "DocumentContent mit Blocks", OK, "QTextDocument (Blöcke, Tabellen, Bilder)")
s("DOKUMENTMODELL (Structure)", "Document-Klasse mit Sections; Section mit Inhalt, Header, Footer; PageSetup mit Margins, PageSize, Columns", TEIL, "ein Abschnitt: PageSettings (Papier, Ränder, Kopf/Fuß); keine Spalten, keine mehreren Abschnitte")
s("DOKUMENTMODELL (Structure)", "Block-Vererbung (Paragraph, Table, Image, Shape)", TEIL, "Absatz, Tabelle, Bild; keine Formen")
s("DOKUMENTMODELL (Callbacks)", "Änderungs-Callbacks für Paragraph; Änderungs-Callbacks für Table; Änderungs-Callbacks für DocumentContent; Callbacks triggern Language Bridge Update", OK, "Qt-Signal contentsChanged → WritingAssistant.dokument_geaendert")
json.dump(Z, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "doku/native-qt/pruefbogen/zuordnung.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(Z), "Zuordnungen (Teil 1)")
