# Menüstruktur ↔ Programm

**✅ 71 · ◐ 27 · ⬜ 12** (zusammengefasste Zeilen).
Erzeugt von `werkzeug/menuestruktur-abgleich.py`. Die vorgegebene Struktur (12 Bereiche) Punkt für Punkt gegen das Programm: ✅ vorhanden · ◐ teilweise oder anders gelöst · ⬜ fehlt. Reiter-Reihenfolge und -Anordnung folgen den WPS-Bildschirmfotos; wo die Struktur davon abweicht (eigener KI-Reiter, Rechtschreibung unter Überprüfen), gilt die Anordnung nach WPS: Rechtschreibung und KI stehen im Reiter Schreibhilfe.

## 1. Datei

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Neu: Leeres Dokument · Aus Vorlage erstellen · Vorlagen durchsuchen | Backstage ▸ Neues Dokument / Von Vorlage; zehn Vorlagen |
| ✅ | Öffnen · Zuletzt verwendete Dokumente | Backstage ▸ Öffnen, Zuletzt benutzte Dokumente |
| ✅ | Speichern · Speichern unter · Kopie speichern | Backstage ▸ Speichern, Speichern als |
| ✅ | Exportieren: PDF · DOCX · DOC (optional) · RTF · TXT | Speichern als; dazu ODT und PNG; DOC/ODT/RTF brauchen LibreOffice |
| ✅ | Drucken: Druckvorschau · Drucker auswählen | Backstage ▸ Drucken |
| ◐ | Drucken: Seitenbereich · Druckeinstellungen | im Druckfenster des Systems; was gedruckt wird: Optionen ▸ Drucken |
| ✅ | Dokumentinformationen | Backstage ▸ Info (Statistik, Verfasser, Titel) |
| ✅ | Dokument schützen | Backstage ▸ Schützen (Kennwort, Bearbeitung sperren) |
| ⬜ | Dokument teilen (optional) | Knopf vorhanden, ausgegraut; keine Freigabe-Funktion |
| ✅ | Optionen / Einstellungen · Schließen | Backstage ▸ Erweiterte Einstellungen, Schließen |

## 2. Start

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Zwischenablage: Einfügen · Einfügen ohne Formatierung · Ausschneiden · Kopieren · Format übertragen | Reiter Start ▸ Zwischenablage |
| ◐ | Zwischenablage: Inhalte einfügen | Einfügeoptionen nach dem Einfügen (Optionen ▸ Bearbeiten); kein eigener Dialog |
| ⬜ | Zwischenablage: Wort-Extras | Knopf vorhanden, ausgegraut |
| ✅ | Schriftart: Schriftart/-größe · größer/kleiner · Formatierung löschen · Groß-/Kleinschreibung | Start ▸ Schriftart |
| ✅ | Schriftart: Fett · Kursiv · Unterstrichen (5 Linienarten) · Durchgestrichen · Hoch/Tief | Start ▸ Schriftart |
| ✅ | Schriftart: Hervorhebung · Textfarbe · Zeichenumriss · Texteffekte | Start ▸ Schriftart |
| ◐ | Schriftart: Zeichenabstand (optional) | nur global als Buchstabenabstand der Lesehilfe, nicht je Textstelle |
| ✅ | Schriftart: Schriftart-Dialog | Pfeil ↘ der Gruppe |
| ✅ | Absatz: Aufzählung · Nummerierung · Einzug · Ausrichtung (4 + verteilt) · Zeilenabstand | Start ▸ Absatz |
| ✅ | Absatz: Absatzabstand · Schattierung · Rahmenlinien · Formatierungszeichen | Start ▸ Absatz / Seitenlayout ▸ Absatz |
| ◐ | Absatz: Mehrstufige Liste | Listenebene erhöhen/verringern; kein Listenkatalog |
| ✅ | Absatz: Tabstopps | Dialog (links/zentriert/rechts/dezimal, mm); wird als DOCX-Tabstopp gespeichert — keine Füllzeichen (Punkte/Linie) |
| ✅ | Formatvorlagen: Standard · Überschrift · Titel · Untertitel · Zitat | Standard, Überschrift 1–9, Titel, Untertitel, Zitat, Kein Abstand |
| ⬜ | Formatvorlagen: Listenformatvorlagen | — |
| ◐ | Formatvorlagen: erstellen / ändern · Aufgabenbereich | vorhandene verwalten und ändern (Dialog); Anlegen/Löschen offen (Batch 7); kein Seitenbereich |
| ✅ | Bearbeiten: Suchen · Ersetzen · Weitersuchen · Alles/Objekte auswählen | Start ▸ Suchen oder ersetzen, Auswählen |
| ◐ | Bearbeiten: Gehe zu (Seite/Abschnitt/Zeile/Objekt) | Strg+G: Seite, Zeile, Überschrift, Textmarke, Beschriftung, Kommentar, Fuß-/Endnote, Tabelle, Bild; Abschnitt: alle Abschnitte; Gleichungen/Felder fehlen |

## 3. Einfügen

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Seiten: Deckblatt · Leere Seite · Seitenumbruch | Einfügen ▸ Seiten |
| ✅ | Seiten: Abschnittsumbruch | nächste Seite, fortlaufend, gerade, ungerade; DOCX w:sectPr |
| ✅ | Tabellen: Raster · Schnelltabelle | Einfügen ▸ Tabellen |
| ⬜ | Tabellen: einzeichnen · aus Text · Excel-Objekt | Excel-/Tabellenblatt-Objekte sind per Projektvorgabe ausgeschlossen |
| ✅ | Illustrationen: Bild aus Datei · Formen · Diagramm · Screenshot | Einfügen ▸ Illustrationen (+ Piktogramm) |
| ◐ | Illustrationen: Online-Bilder (optional) · SmartArt | SmartArt: 5 Layouts, bearbeitbar (SmartArt-Tools); in DOCX ein Bild; Online-Bilder fehlen |
| ✅ | Illustrationen: Bildunterschrift · Alternativtext | Verweise ▸ Beschriftung; Bildtools ▸ Alternativtext |
| ✅ | Links: Hyperlink einfügen/bearbeiten/entfernen · Textmarke · Querverweis | Einfügen ▸ Links; Rechtsklick auf den Link |
| ✅ | Kopf- und Fußzeile: Kopfzeile · Fußzeile · Seitenzahl | Einfügen ▸ Kopf- und Fußzeile; Rand-Doppelklick |
| ◐ | Kopf- und Fußzeile: Seitenzahlen formatieren/entfernen | Seitenzahl-Menü; Format einzeln nicht geprüft |
| ✅ | Text: Textfeld · Schnellbausteine · WordArt · Initiale · Datum und Uhrzeit | Einfügen ▸ Text; F3 für Bausteine |
| ⬜ | Text: Dokumentinformationen / Feld · Signaturzeile (optional) | — |
| ◐ | Text: Objekt einfügen | Text aus Datei; keine eingebetteten Objekte |
| ✅ | Symbole: Formel · Symbol · Sonderzeichen | Einfügen ▸ Symbole |

## 4. Seitenlayout

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Seite einrichten: Seitenränder (Vorgaben + vier Maßfelder) · Hoch-/Querformat · Papierformat | Seitenlayout ▸ Ränder, Seite einrichten |
| ✅ | Seite einrichten: Spalten (1–4, live) · Umbrüche · Zeilennummern | Seitenlayout ▸ Seite einrichten |
| ✅ | Seite einrichten: Silbentrennung | Reiter Schreibhilfe ▸ Sprache (nicht im Seitenlayout) |
| ⬜ | Seite einrichten: Vertikale Seitenausrichtung (optional) | — |
| ✅ | Seite einrichten: Dialog | Pfeil ↘ der Gruppe |
| ✅ | Seitenhintergrund: Wasserzeichen · Seitenfarbe · Seitenrand | Seitenlayout ▸ Seitenhintergrund |
| ✅ | Absatz: Einzug links/rechts · Abstand vor/nach | Seitenlayout ▸ Absatz |
| ✅ | Absatz: Tabstopps / Absatzdialog | Absatzdialog und Tabstopp-Dialog |
| ✅ | Anordnen: Textumbruch (links/rechts/oben-unten/Zeile) · Ausrichten · Drehen | Seitenlayout ▸ Anordnen |
| ◐ | Anordnen: Auswahlbereich | „Objekte auswählen“; kein Bereich mit Liste |
| ◐ | Anordnen: Nach vorne / Nach hinten · Gruppieren · Position sperren | Gruppieren/Aufheben für Formen (als Zeilenobjekt, nicht frei schwebend); Nach vorne/hinten und Position sperren fehlen — Qt kennt keine Z-Ordnung |
| ✅ | Anordnen: Größe / Seitenverhältnis | Bildtools ▸ Größe und Seitenverhältnis |

## 5. Abschnitt

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Abschnitt erstellen: Abschnittsumbruch · Nächste Seite | Abschnitt ▸ Abschnitt hinzufügen |
| ◐ | Abschnitt erstellen: Fortlaufend · Gerade Seite · Ungerade Seite | alle vier Arten; fortlaufend mit anderer Geometrie beginnt in der Ausgabe auf neuer Seite |
| ◐ | Abschnitt verwalten: Vorheriger · Nächster · markieren · umbenennen · löschen | Vorheriger, Nächster, Löschen, Navigation (Strg+G); Markieren und Umbenennen fehlen |
| ✅ | Abschnittslayout: Ränder · Hoch/Quer · Papierformat · Spalten | gelten für den Abschnitt der Schreibmarke |
| ⬜ | Abschnittslayout: Vertikale Seitenausrichtung | — |
| ✅ | Kopf-/Fußzeilen: Erste Seite anders | Abschnitt ▸ Kopf- und Fußzeile |
| ◐ | Kopf-/Fußzeilen: Mit vorherigem verknüpfen · Gerade/ungerade · je Abschnitt | verknüpfen und je Abschnitt: ja; gerade/ungerade unterschiedlich: nein |
| ⬜ | Seitennummerierung: beginnen/fortsetzen · Format · Anfangsseitenzahl | — |
| ✅ | Abschnittsumbrüche anzeigen | gestrichelte Linie mit Beschriftung im Text |
| ✅ | Abschnittseinstellungen | Abschnitt ▸ Abschnitt einrichten … (Seite, Beginn) |

## 6. Verweise

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Inhaltsverzeichnis einfügen/aktualisieren | Verweise ▸ Inhaltsverzeichnis, Verzeichnisse aktualisieren |
| ◐ | Inhaltsverzeichnis formatieren · Text zur Gliederung hinzufügen | über die Überschriften-Stile; kein eigener Dialog |
| ✅ | Fußnote / Endnote einfügen · zur nächsten/vorigen · Notenbereich | Verweise ▸ Fußnoten; Fußnoten stehen am Seitenfuß |
| ◐ | Fußnotenoptionen / Nummerierung | automatisch; keine Optionen |
| ✅ | Zitieren: Stil · Quelle einfügen/bearbeiten · Quellen verwalten · Literaturverzeichnis | Verweise ▸ Zitate und Literatur |
| ✅ | Beschriftung · Abbildungsverzeichnis · Index/Stichwortverzeichnis · Querverweis | Verweise ▸ Beschriftungen, Index |

## 7. Überprüfen  (Rechtschreibung, Sprache, KI stehen laut Ihrer Vorgabe im Reiter Schreibhilfe)

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Korrekturhilfen: Rechtschreibprüfung · automatisch · Thesaurus · Korrektursprache | Schreibhilfe ▸ Dokumentprüfung, Beim Schreiben |
| ✅ | Korrekturhilfen: Wortanzahl | Überprüfen ▸ Dokument; Statusleiste |
| ✅ | Sprache: festlegen · Übersetzen | Schreibhilfe ▸ Sprache (Übersetzen mit KI) |
| ✅ | Kommentare: neu · bearbeiten · löschen · vorher/nächster · alle | Überprüfen ▸ Kommentare; Sprechblasen am Rand |
| ✅ | Änderungen: ein/aus · Anzeigeoptionen · Bereich · vorher/nächste · annehmen/ablehnen | Überprüfen ▸ Änderungen |
| ◐ | Vergleichen: Dokumente vergleichen · zusammenführen (optional) | Überprüfen ▸ Vergleichen/Zusammenführen: Text und Absätze als verfolgte Änderungen; keine Formatänderungen, keine Tabellenstruktur (tests/test_vergleich.py) |
| ✅ | Schützen: Dokument schützen | Überprüfen ▸ Schützen; Backstage ▸ Schützen |
| ◐ | Schützen: Bearbeitung einschränken · Schutz aufheben (optional) | Bearbeitung sperren/freigeben; Kennwort entfernen |

## 8. KI  (kein eigener Reiter: Reiter Schreibhilfe und Seitenleiste)

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Text entwerfen · umformulieren · zusammenfassen · übersetzen | Schreibhilfe ▸ KI-Schreibwerkzeuge, Übersetzen |
| ✅ | KI-Korrektur · Verbesserungsvorschläge | Seitenleiste (F8); KI-Chat |
| ◐ | Öffnet die rechte Seitenleiste | KI-Chat und Schreibhilfe-Knopf schalten sie; der Reiter selbst nicht |
| ✅ | Zusätzlich (nicht in Ihrer Liste): Text in Bild · eigener Assistent · eigener Anbieter · KI-Konfiguration | Schreibhilfe ▸ KI |

## 9. Ansicht

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Ansichten: Drucklayout · Weblayout · Lesemodus · Gliederung · Vollbild | Ansicht ▸ Dokumentansichten |
| ✅ | Einblenden: Lineal · Gitternetz · Navigationsbereich · Formatierungszeichen | Ansicht ▸ Anzeigen; Start ▸ ¶ |
| ◐ | Einblenden: Dokumentstruktur | Navigationsbereich zeigt die Überschriften |
| ✅ | Zoom: Dialog · 100 % · Ganze Seite · Seitenbreite · Regler | Ansicht ▸ Zoom; Statusleiste |
| ✅ | Fenster: Neues Fenster · Alle anordnen · Nebeneinander · Fensterwechsel | Ansicht ▸ Fenster |
| ⬜ | Fenster: Teilen · Synchroner Bildlauf (optional) | — |
| ✅ | Seitenleiste: ein-/ausblenden | F5, schmale Leiste rechts |
| ◐ | Seitenleiste: Breite anpassen | nicht einzeln geprüft |

## 10. Kontextabhängige Registerkarten

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Tabellentools: Schattierung · Rahmenlinien · Zeilen/Spalten einfügen/löschen · verbinden/teilen · sortieren · ausrichten · Eigenschaften | Reiter Tabellentools |
| ◐ | Tabellentools: Tabellenformatvorlagen · Formatoptionen · Linienstil/Effekte · Formel · Textrichtung | Vorlagen (7), Kopfzeile/gebänderte Zeilen/erste Spalte, Rahmen, Schattierung; keine lebende Verknüpfung (Vorlage wird auf die Zellen angewendet); Linienstil/Effekte, Formel, Textrichtung fehlen |
| ◐ | Tabellentools: Zellengröße Höhe/Breite | über Eigenschaften |
| ✅ | Bildtools: Helligkeit/Kontrast/Farbe · Zuschneiden · Größe · Textumbruch · Alternativtext | Reiter Bildtools |
| ⬜ | Bildtools: Transparenz · Bildstile/Rahmen · Position/Ausrichten | — |
| ◐ | Form- und WordArt-Tools: Formvorlagen · Füllung · Kontur · Effekte · Gruppieren | Formvorlagen (8), Füllung, Kontur/Stärke, Text in der Form, Gruppieren; Effekte fehlen; Formen sind Bilder mit gespeicherten Parametern |
| ✅ | Kopf- und Fußzeilentools: Kopf/Fuß bearbeiten · Seitenzahl · Erste Seite anders · schließen | Reiter Kopf- und Fußzeilentools |
| ⬜ | Kopf- und Fußzeilentools: Gerade/ungerade · Verknüpfen · Dokumenttext anzeigen | — |

## 11. Zusätzliche Oberflächenelemente

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Schnellzugriff: Speichern · Rückgängig/Wiederholen · anpassen | Leiste links der Reiter; Optionen ▸ Symbolleiste für den Schnellzugriff |
| ✅ | Dokumentregister: wechseln · neu · schließen | Reiter oben (Strg+Tab, +, ×) |
| ✅ | Dokumentregister: Kontextmenü | Schließen, Andere/Alle schließen, Speichern, Pfad kopieren, Ordner öffnen |
| ✅ | Aufgabenbereiche: Navigation/Suchen | Navigationsbereich, Suchen-Fenster |
| ⬜ | Aufgabenbereiche: Formatvorlagen · Auswahlbereich · Zwischenablage | — |
| ✅ | Statusleiste: Seite · Wörter · Zoomregler · Zoom-Prozent | unten |
| ◐ | Statusleiste: Korrekturstatus · Ansichtswechsel | Meldung („n Zeichen geprüft“); keine Ansichtsknöpfe |

## 12. Rechte Seitenleiste

| | Punkt | Beleg / Grenze |
|---|---|---|
| ✅ | Rahmen: öffnen/schließen · Bereich wechseln · Inhalt anzeigen | F5; schmale Leiste rechts |
| ✅ | KI: KI-Korrektur · Vorschläge · Übersetzen · Chat | Bereich KI |
| ◐ | KI: entwerfen · umformulieren · zusammenfassen | im Reiter Schreibhilfe, nicht in der Seitenleiste |
| ✅ | Überprüfen: Dokumentprüfung · Gründlich · Hinweiskarten · Vorschläge · Begründung | Bereich Schreibhilfe (Prüfen, Karten) |
| ✅ | Schreibhilfe: Rechtschreibung (We) · Wortvorhersage (Vo) · Korrektur (Ko) | Kopf der Seitenleiste |
| ◐ | Schreibhilfe: Lesehilfe · Zeilenfokus · Vorlesen · Silben/Thesaurus · Textbausteine · Optionen | im Band, nicht in der Seitenleiste |

## Vorhanden, aber nicht in der Struktur

* **Sendungen** (ausblendbarer Reiter): Seriendruck, Umschläge, Etiketten, Adressblock, Formularfelder.
* **Lesehilfe für Menschen mit Legasthenie:** farbige Silben mit Einstellungen, Zeilenfokus, Leseschriften, Vorlesen.
* **Backstage-Ansicht** für *Datei* mit Info, Öffnen mit … (WPS, LibreOffice).
* **Sprechblasen** für Kommentare, **Fußnoten am Seitenfuß**, **Spalten live** auf der Seite.
* **Hilfe:** Handbuch, Tastenkürzel, „Welche Hilfe wann“.
* **Hell/Dunkel**, Register anpassen, Symbole austauschen, zweite Oberfläche (Symbolleisten).

