#!/usr/bin/env python3
"""Schreibt docs/MENUESTRUKTUR.md: die vorgegebene Menüstruktur (12 Bereiche) Punkt für Punkt gegen das Programm.

Status: ✅ vorhanden · ◐ teilweise oder anders gelöst · ⬜ fehlt. Die Einträge sind von Hand begründet (Befehl im Band, Test oder
ehrliche Grenze); der Stand der Befehle kommt aus docs/PRUEFBOGEN.md und dem Band (werkzeug/pruefbogen-abgleich.py).
"""
import os

OK, TEIL, FEHLT = "✅", "◐", "⬜"
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = []


def bereich(titel, *zeilen):
    B.append((titel, zeilen))


bereich("1. Datei",
    ("Neu: Leeres Dokument · Aus Vorlage erstellen · Vorlagen durchsuchen", OK, "Backstage ▸ Neues Dokument / Von Vorlage; zehn Vorlagen"),
    ("Öffnen · Zuletzt verwendete Dokumente", OK, "Backstage ▸ Öffnen, Zuletzt benutzte Dokumente"),
    ("Speichern · Speichern unter · Kopie speichern", OK, "Backstage ▸ Speichern, Speichern als"),
    ("Exportieren: PDF · DOCX · DOC (optional) · RTF · TXT", OK, "Speichern als; dazu ODT und PNG; DOC/ODT/RTF brauchen LibreOffice"),
    ("Drucken: Druckvorschau · Drucker auswählen", OK, "Backstage ▸ Drucken"),
    ("Drucken: Seitenbereich · Druckeinstellungen", TEIL, "im Druckfenster des Systems; was gedruckt wird: Optionen ▸ Drucken"),
    ("Dokumentinformationen", OK, "Backstage ▸ Info (Statistik, Verfasser, Titel)"),
    ("Dokument schützen", OK, "Backstage ▸ Schützen (Kennwort, Bearbeitung sperren)"),
    ("Dokument teilen (optional)", FEHLT, "Knopf vorhanden, ausgegraut; keine Freigabe-Funktion"),
    ("Optionen / Einstellungen · Schließen", OK, "Backstage ▸ Erweiterte Einstellungen, Schließen"))

bereich("2. Start",
    ("Zwischenablage: Einfügen · Einfügen ohne Formatierung · Ausschneiden · Kopieren · Format übertragen", OK, "Reiter Start ▸ Zwischenablage"),
    ("Zwischenablage: Inhalte einfügen", TEIL, "Einfügeoptionen nach dem Einfügen (Optionen ▸ Bearbeiten); kein eigener Dialog"),
    ("Zwischenablage: Wort-Extras", FEHLT, "Knopf vorhanden, ausgegraut"),
    ("Schriftart: Schriftart/-größe · größer/kleiner · Formatierung löschen · Groß-/Kleinschreibung", OK, "Start ▸ Schriftart"),
    ("Schriftart: Fett · Kursiv · Unterstrichen (5 Linienarten) · Durchgestrichen · Hoch/Tief", OK, "Start ▸ Schriftart"),
    ("Schriftart: Hervorhebung · Textfarbe · Zeichenumriss · Texteffekte", OK, "Start ▸ Schriftart"),
    ("Schriftart: Zeichenabstand (optional)", TEIL, "nur global als Buchstabenabstand der Lesehilfe, nicht je Textstelle"),
    ("Schriftart: Schriftart-Dialog", OK, "Pfeil ↘ der Gruppe"),
    ("Absatz: Aufzählung · Nummerierung · Einzug · Ausrichtung (4 + verteilt) · Zeilenabstand", OK, "Start ▸ Absatz"),
    ("Absatz: Absatzabstand · Schattierung · Rahmenlinien · Formatierungszeichen", OK, "Start ▸ Absatz / Seitenlayout ▸ Absatz"),
    ("Absatz: Mehrstufige Liste", TEIL, "Listenebene erhöhen/verringern; kein Listenkatalog"),
    ("Absatz: Tabstopps", OK, "Dialog (links/zentriert/rechts/dezimal, mm); wird als DOCX-Tabstopp gespeichert — keine Füllzeichen (Punkte/Linie)"),
    ("Formatvorlagen: Standard · Überschrift · Titel · Untertitel · Zitat", OK, "Standard, Überschrift 1–9, Titel, Untertitel, Zitat, Kein Abstand"),
    ("Formatvorlagen: Listenformatvorlagen", FEHLT, "—"),
    ("Formatvorlagen: erstellen / ändern · Aufgabenbereich", TEIL, "vorhandene verwalten und ändern (Dialog); Anlegen/Löschen offen (Batch 7); kein Seitenbereich"),
    ("Bearbeiten: Suchen · Ersetzen · Weitersuchen · Alles/Objekte auswählen", OK, "Start ▸ Suchen oder ersetzen, Auswählen"),
    ("Bearbeiten: Gehe zu (Seite/Abschnitt/Zeile/Objekt)", TEIL, "Strg+G: Seite, Zeile, Überschrift, Textmarke, Beschriftung, Kommentar, Fuß-/Endnote, Tabelle, Bild; Abschnitt: alle Abschnitte; Gleichungen/Felder fehlen"))

bereich("3. Einfügen",
    ("Seiten: Deckblatt · Leere Seite · Seitenumbruch", OK, "Einfügen ▸ Seiten"),
    ("Seiten: Abschnittsumbruch", OK, "nächste Seite, fortlaufend, gerade, ungerade; DOCX w:sectPr"),
    ("Tabellen: Raster · Schnelltabelle", OK, "Einfügen ▸ Tabellen"),
    ("Tabellen: einzeichnen · aus Text · Excel-Objekt", FEHLT, "Excel-/Tabellenblatt-Objekte sind per Projektvorgabe ausgeschlossen"),
    ("Illustrationen: Bild aus Datei · Formen · Diagramm · Screenshot", OK, "Einfügen ▸ Illustrationen (+ Piktogramm)"),
    ("Illustrationen: Online-Bilder (optional) · SmartArt", FEHLT, "SmartArt: Knopf ausgegraut (Batch 6)"),
    ("Illustrationen: Bildunterschrift · Alternativtext", OK, "Verweise ▸ Beschriftung; Bildtools ▸ Alternativtext"),
    ("Links: Hyperlink einfügen/bearbeiten/entfernen · Textmarke · Querverweis", OK, "Einfügen ▸ Links; Rechtsklick auf den Link"),
    ("Kopf- und Fußzeile: Kopfzeile · Fußzeile · Seitenzahl", OK, "Einfügen ▸ Kopf- und Fußzeile; Rand-Doppelklick"),
    ("Kopf- und Fußzeile: Seitenzahlen formatieren/entfernen", TEIL, "Seitenzahl-Menü; Format einzeln nicht geprüft"),
    ("Text: Textfeld · Schnellbausteine · WordArt · Initiale · Datum und Uhrzeit", OK, "Einfügen ▸ Text; F3 für Bausteine"),
    ("Text: Dokumentinformationen / Feld · Signaturzeile (optional)", FEHLT, "—"),
    ("Text: Objekt einfügen", TEIL, "Text aus Datei; keine eingebetteten Objekte"),
    ("Symbole: Formel · Symbol · Sonderzeichen", OK, "Einfügen ▸ Symbole"))

bereich("4. Seitenlayout",
    ("Seite einrichten: Seitenränder (Vorgaben + vier Maßfelder) · Hoch-/Querformat · Papierformat", OK, "Seitenlayout ▸ Ränder, Seite einrichten"),
    ("Seite einrichten: Spalten (1–4, live) · Umbrüche · Zeilennummern", OK, "Seitenlayout ▸ Seite einrichten"),
    ("Seite einrichten: Silbentrennung", OK, "Reiter Schreibhilfe ▸ Sprache (nicht im Seitenlayout)"),
    ("Seite einrichten: Vertikale Seitenausrichtung (optional)", FEHLT, "—"),
    ("Seite einrichten: Dialog", OK, "Pfeil ↘ der Gruppe"),
    ("Seitenhintergrund: Wasserzeichen · Seitenfarbe · Seitenrand", OK, "Seitenlayout ▸ Seitenhintergrund"),
    ("Absatz: Einzug links/rechts · Abstand vor/nach", OK, "Seitenlayout ▸ Absatz"),
    ("Absatz: Tabstopps / Absatzdialog", OK, "Absatzdialog und Tabstopp-Dialog"),
    ("Anordnen: Textumbruch (links/rechts/oben-unten/Zeile) · Ausrichten · Drehen", OK, "Seitenlayout ▸ Anordnen"),
    ("Anordnen: Auswahlbereich", TEIL, "„Objekte auswählen“; kein Bereich mit Liste"),
    ("Anordnen: Nach vorne / Nach hinten · Gruppieren · Position sperren", TEIL, "Gruppieren/Aufheben für Formen (als Zeilenobjekt, nicht frei schwebend); Nach vorne/hinten und Position sperren fehlen — Qt kennt keine Z-Ordnung"),
    ("Anordnen: Größe / Seitenverhältnis", OK, "Bildtools ▸ Größe und Seitenverhältnis"))

bereich("5. Abschnitt",
    ("Abschnitt erstellen: Abschnittsumbruch · Nächste Seite", OK, "Abschnitt ▸ Abschnitt hinzufügen"),
    ("Abschnitt erstellen: Fortlaufend · Gerade Seite · Ungerade Seite", TEIL, "alle vier Arten; fortlaufend mit anderer Geometrie beginnt in der Ausgabe auf neuer Seite"),
    ("Abschnitt verwalten: Vorheriger · Nächster · markieren · umbenennen · löschen", TEIL, "Vorheriger, Nächster, Löschen, Navigation (Strg+G); Markieren und Umbenennen fehlen"),
    ("Abschnittslayout: Ränder · Hoch/Quer · Papierformat · Spalten", OK, "gelten für den Abschnitt der Schreibmarke"),
    ("Abschnittslayout: Vertikale Seitenausrichtung", FEHLT, "—"),
    ("Kopf-/Fußzeilen: Erste Seite anders", OK, "Abschnitt ▸ Kopf- und Fußzeile"),
    ("Kopf-/Fußzeilen: Mit vorherigem verknüpfen · Gerade/ungerade · je Abschnitt", TEIL, "verknüpfen und je Abschnitt: ja; gerade/ungerade unterschiedlich: nein"),
    ("Seitennummerierung: beginnen/fortsetzen · Format · Anfangsseitenzahl", FEHLT, "—"),
    ("Abschnittsumbrüche anzeigen", OK, "gestrichelte Linie mit Beschriftung im Text"),
    ("Abschnittseinstellungen", OK, "Abschnitt ▸ Abschnitt einrichten … (Seite, Beginn)"))

bereich("6. Verweise",
    ("Inhaltsverzeichnis einfügen/aktualisieren", OK, "Verweise ▸ Inhaltsverzeichnis, Verzeichnisse aktualisieren"),
    ("Inhaltsverzeichnis formatieren · Text zur Gliederung hinzufügen", TEIL, "über die Überschriften-Stile; kein eigener Dialog"),
    ("Fußnote / Endnote einfügen · zur nächsten/vorigen · Notenbereich", OK, "Verweise ▸ Fußnoten; Fußnoten stehen am Seitenfuß"),
    ("Fußnotenoptionen / Nummerierung", TEIL, "automatisch; keine Optionen"),
    ("Zitieren: Stil · Quelle einfügen/bearbeiten · Quellen verwalten · Literaturverzeichnis", OK, "Verweise ▸ Zitate und Literatur"),
    ("Beschriftung · Abbildungsverzeichnis · Index/Stichwortverzeichnis · Querverweis", OK, "Verweise ▸ Beschriftungen, Index"))

bereich("7. Überprüfen  (Rechtschreibung, Sprache, KI stehen laut Ihrer Vorgabe im Reiter Schreibhilfe)",
    ("Korrekturhilfen: Rechtschreibprüfung · automatisch · Thesaurus · Korrektursprache", OK, "Schreibhilfe ▸ Dokumentprüfung, Beim Schreiben"),
    ("Korrekturhilfen: Wortanzahl", OK, "Überprüfen ▸ Dokument; Statusleiste"),
    ("Sprache: festlegen · Übersetzen", OK, "Schreibhilfe ▸ Sprache (Übersetzen mit KI)"),
    ("Kommentare: neu · bearbeiten · löschen · vorher/nächster · alle", OK, "Überprüfen ▸ Kommentare; Sprechblasen am Rand"),
    ("Änderungen: ein/aus · Anzeigeoptionen · Bereich · vorher/nächste · annehmen/ablehnen", OK, "Überprüfen ▸ Änderungen"),
    ("Vergleichen: Dokumente vergleichen · zusammenführen (optional)", TEIL, "Überprüfen ▸ Vergleichen/Zusammenführen: Text und Absätze als verfolgte Änderungen; keine Formatänderungen, keine Tabellenstruktur (tests/test_vergleich.py)"),
    ("Schützen: Dokument schützen", OK, "Überprüfen ▸ Schützen; Backstage ▸ Schützen"),
    ("Schützen: Bearbeitung einschränken · Schutz aufheben (optional)", TEIL, "Bearbeitung sperren/freigeben; Kennwort entfernen"))

bereich("8. KI  (kein eigener Reiter: Reiter Schreibhilfe und Seitenleiste)",
    ("Text entwerfen · umformulieren · zusammenfassen · übersetzen", OK, "Schreibhilfe ▸ KI-Schreibwerkzeuge, Übersetzen"),
    ("KI-Korrektur · Verbesserungsvorschläge", OK, "Seitenleiste (F8); KI-Chat"),
    ("Öffnet die rechte Seitenleiste", TEIL, "KI-Chat und Schreibhilfe-Knopf schalten sie; der Reiter selbst nicht"),
    ("Zusätzlich (nicht in Ihrer Liste): Text in Bild · eigener Assistent · eigener Anbieter · KI-Konfiguration", OK, "Schreibhilfe ▸ KI"))

bereich("9. Ansicht",
    ("Ansichten: Drucklayout · Weblayout · Lesemodus · Gliederung · Vollbild", OK, "Ansicht ▸ Dokumentansichten"),
    ("Einblenden: Lineal · Gitternetz · Navigationsbereich · Formatierungszeichen", OK, "Ansicht ▸ Anzeigen; Start ▸ ¶"),
    ("Einblenden: Dokumentstruktur", TEIL, "Navigationsbereich zeigt die Überschriften"),
    ("Zoom: Dialog · 100 % · Ganze Seite · Seitenbreite · Regler", OK, "Ansicht ▸ Zoom; Statusleiste"),
    ("Fenster: Neues Fenster · Alle anordnen · Nebeneinander · Fensterwechsel", OK, "Ansicht ▸ Fenster"),
    ("Fenster: Teilen · Synchroner Bildlauf (optional)", FEHLT, "—"),
    ("Seitenleiste: ein-/ausblenden", OK, "F5, schmale Leiste rechts"),
    ("Seitenleiste: Breite anpassen", TEIL, "nicht einzeln geprüft"))

bereich("10. Kontextabhängige Registerkarten",
    ("Tabellentools: Schattierung · Rahmenlinien · Zeilen/Spalten einfügen/löschen · verbinden/teilen · sortieren · ausrichten · Eigenschaften", OK, "Reiter Tabellentools"),
    ("Tabellentools: Tabellenformatvorlagen · Formatoptionen · Linienstil/Effekte · Formel · Textrichtung", TEIL, "Vorlagen (7), Kopfzeile/gebänderte Zeilen/erste Spalte, Rahmen, Schattierung; keine lebende Verknüpfung (Vorlage wird auf die Zellen angewendet); Linienstil/Effekte, Formel, Textrichtung fehlen"),
    ("Tabellentools: Zellengröße Höhe/Breite", TEIL, "über Eigenschaften"),
    ("Bildtools: Helligkeit/Kontrast/Farbe · Zuschneiden · Größe · Textumbruch · Alternativtext", OK, "Reiter Bildtools"),
    ("Bildtools: Transparenz · Bildstile/Rahmen · Position/Ausrichten", FEHLT, "—"),
    ("Form- und WordArt-Tools: Formvorlagen · Füllung · Kontur · Effekte · Gruppieren", TEIL, "Formvorlagen (8), Füllung, Kontur/Stärke, Text in der Form, Gruppieren; Effekte fehlen; Formen sind Bilder mit gespeicherten Parametern"),
    ("Kopf- und Fußzeilentools: Kopf/Fuß bearbeiten · Seitenzahl · Erste Seite anders · schließen", OK, "Reiter Kopf- und Fußzeilentools"),
    ("Kopf- und Fußzeilentools: Gerade/ungerade · Verknüpfen · Dokumenttext anzeigen", FEHLT, "—"))

bereich("11. Zusätzliche Oberflächenelemente",
    ("Schnellzugriff: Speichern · Rückgängig/Wiederholen · anpassen", OK, "Leiste links der Reiter; Optionen ▸ Symbolleiste für den Schnellzugriff"),
    ("Dokumentregister: wechseln · neu · schließen", OK, "Reiter oben (Strg+Tab, +, ×)"),
    ("Dokumentregister: Kontextmenü", OK, "Schließen, Andere/Alle schließen, Speichern, Pfad kopieren, Ordner öffnen"),
    ("Aufgabenbereiche: Navigation/Suchen", OK, "Navigationsbereich, Suchen-Fenster"),
    ("Aufgabenbereiche: Formatvorlagen · Auswahlbereich · Zwischenablage", FEHLT, "—"),
    ("Statusleiste: Seite · Wörter · Zoomregler · Zoom-Prozent", OK, "unten"),
    ("Statusleiste: Korrekturstatus · Ansichtswechsel", TEIL, "Meldung („n Zeichen geprüft“); keine Ansichtsknöpfe"))

bereich("12. Rechte Seitenleiste",
    ("Rahmen: öffnen/schließen · Bereich wechseln · Inhalt anzeigen", OK, "F5; schmale Leiste rechts"),
    ("KI: KI-Korrektur · Vorschläge · Übersetzen · Chat", OK, "Bereich KI"),
    ("KI: entwerfen · umformulieren · zusammenfassen", TEIL, "im Reiter Schreibhilfe, nicht in der Seitenleiste"),
    ("Überprüfen: Dokumentprüfung · Gründlich · Hinweiskarten · Vorschläge · Begründung", OK, "Bereich Schreibhilfe (Prüfen, Karten)"),
    ("Schreibhilfe: Rechtschreibung (We) · Wortvorhersage (Vo) · Korrektur (Ko)", OK, "Kopf der Seitenleiste"),
    ("Schreibhilfe: Lesehilfe · Zeilenfokus · Vorlesen · Silben/Thesaurus · Textbausteine · Optionen", TEIL, "im Band, nicht in der Seitenleiste"))

z = {OK: 0, TEIL: 0, FEHLT: 0}
txt = ["# Menüstruktur ↔ Programm", "",
       "Erzeugt von `werkzeug/menuestruktur-abgleich.py`. Die vorgegebene Struktur (12 Bereiche) Punkt für Punkt gegen das Programm: "
       "✅ vorhanden · ◐ teilweise oder anders gelöst · ⬜ fehlt. Reiter-Reihenfolge und -Anordnung folgen den WPS-Bildschirmfotos; "
       "wo die Struktur davon abweicht (eigener KI-Reiter, Rechtschreibung unter Überprüfen), gilt die Anordnung nach WPS: Rechtschreibung "
       "und KI stehen im Reiter Schreibhilfe.", ""]
for titel, zeilen in B:
    txt += [f"## {titel}", "", "| | Punkt | Beleg / Grenze |", "|---|---|---|"]
    for p, s, b in zeilen:
        z[s] += 1
        txt.append(f"| {s} | {p} | {b} |")
    txt.append("")
txt += ["## Vorhanden, aber nicht in der Struktur", "",
        "* **Sendungen** (ausblendbarer Reiter): Seriendruck, Umschläge, Etiketten, Adressblock, Formularfelder.",
        "* **Lesehilfe für Menschen mit Legasthenie:** farbige Silben mit Einstellungen, Zeilenfokus, Leseschriften, Vorlesen.",
        "* **Backstage-Ansicht** für *Datei* mit Info, Öffnen mit … (WPS, LibreOffice).",
        "* **Sprechblasen** für Kommentare, **Fußnoten am Seitenfuß**, **Spalten live** auf der Seite.",
        "* **Hilfe:** Handbuch, Tastenkürzel, „Welche Hilfe wann“.",
        "* **Hell/Dunkel**, Register anpassen, Symbole austauschen, zweite Oberfläche (Symbolleisten).", ""]
txt.insert(2, f"**✅ {z[OK]} · ◐ {z[TEIL]} · ⬜ {z[FEHLT]}** (zusammengefasste Zeilen).")
open(os.path.join(W, "docs", "MENUESTRUKTUR.md"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
print(z)
