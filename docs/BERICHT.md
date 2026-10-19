# Abschlussbericht (Stand dieses Branches `native-qt6-port`)

Alle Angaben stammen aus tatsächlichen Läufen in der Entwicklungsumgebung (Linux, Qt „offscreen“, LibreOffice 25.x vorhanden).
**Nicht** auf einem echten Linux-Mint-Desktop mit Bildschirm, Drucker, Ollama/Claude, LanguageTool, Piper oder WPS getestet —
das ist offen (siehe 6). Der Prüfbogen ([PRUEFBOGEN.md](PRUEFBOGEN.md)) ist der Maßstab: **415 Punkte, ✅ 328 · ◐ 66 · ⬜ 21**;
„✅“ heißt „Befehl/Funktion vorhanden“, einzeln durch `tests/` belegt nur dort, wo im Eintrag ein Test genannt ist.

## 1. Dateien
`src/lunivo_writer/` (Python-Paket mit core, ui, editor, models, services, ai, proofing), `tests/` (22 Testdateien, 171 Tests), `werkzeug/` (Abgleich-Skripte für Prüfbogen und Knöpfe), `starten-qt.sh`, `requirements*.txt`, `docs/*`.


## 2. Tatsächlich umgesetzt
* **Dokumente:** neu, öffnen, speichern (atomar), speichern unter, Kopie, Export (DOCX, ODT, DOC, RTF, TXT, HTML mit Codierung,
  PDF, PNG je Seite); mehrere Dokumente in Reitern und Fenstern (neues Fenster, anordnen, Fensterliste); Startseite; Schutz vor
  ungespeicherten Änderungen; **Absturzwiederherstellung** und optionale Zwischenstände; **Kennwortschutz** für DOCX
  (msoffcrypto-tool); Vorlagen (10 mitgelieferte Gerüste mit Lücken, eigene aus dem Vorlagenordner).
* **DOCX (Priorität 1) — lesen und schreiben:** Schrift, Größe, Fett/Kursiv/Unterstrichen (5 Arten)/Durchgestrichen/Hoch-Tief,
  Kapitälchen, Zeichenabstand, Umriss, Farbe, Hervorhebung, Ausrichtung (auch `start`/`end` von LibreOffice), Einzüge, Abstände,
  Zeilenabstand, Tabstopps, Absatzschattierung und **-rahmen**, Textrichtung, Überschriften, Titel/Untertitel/Zitat/Kein Abstand,
  Listen (Neustart der Nummerierung), Seitenumbrüche, Tabellen (verbundene Zellen), Bilder mit **Alternativtext**, Hyperlinks,
  **Textmarken**, Seitengröße, Ränder, **Seitenfarbe, Seitenrahmen, Zeilennummern**, Kopf-/Fußzeile mit Seitenzahlfeld,
  **„Erste Seite anders“**, **Fußnoten und Endnoten**, **Kommentare**, **nachverfolgte Änderungen** (`w:ins`/`w:del`),
  Felder (`SEQ`, `CITATION`, `XE`), **Verzeichnisse** (Inhalt, Abbildungen, Tabellen, Stichwörter, Literatur) an ihren
  Word-Vorlagen wiedererkannt, **Quellen** (Bibliografie-XML), Dokumentsprache. Inhaltssteuerelemente (z. B. ein
  Word-Inhaltsverzeichnis) werden gelesen. Geprüft u. a. mit einer **von LibreOffice erzeugten** Datei (Fußnote, Kommentar,
  Überarbeitungen, Textmarke, Tabelle), dem LibreOffice-Export des Handbuchs (26 000 Zeichen, Text nach Roundtrip identisch) und
  durch Öffnen unserer Ausgabe in LibreOffice (Fußnote, Rahmen, Verzeichnisse).
* **Seite und Ansicht:** Papier, Ausrichtung, Ränder, Kopf-/Fußzeile, Seitenzahlen, Seitenzählung, **PDF und Druck** (Duplex,
  umgekehrte Reihenfolge, Hintergründe, leere Seiten, Wasserzeichen, Seitenfarbe/-rahmen, Zeilennummern, Noten am Textende),
  Druckvorschau, **Zoom** (10–500 %, Strg+Mausrad, Dialog, Seitenbreite/Ganze Seite), **Lineale** mit ziehbaren Rändern und
  Einzügen, Gitternetz, Weblayout, Zwei-Seiten-Ansicht, Gliederungsansicht, Lesemodus, Vollbild.
* **Bearbeiten:** Format, Listen, Stilkatalog und **Formatvorlagen verwalten**, Tabellen (+ Sortieren, Eigenschaften), Bilder
  (Größe, Alternativtext, Farbe, Zuschneiden, Drehen), Suchen/Ersetzen, Format übertragen, Sonderzeichen, Wortvorhersage, AutoKorrektur
  und AutoFormat (Listen, Pfade → Links, Einzüge), **Kommentare, Fuß-/Endnoten, Änderungen verfolgen/annehmen/ablehnen**,
  Beschriftungen mit automatischer Nummerierung, Textmarken, Querverweise, Stichwörter, Zitate und Literaturverzeichnis.
* **Einfügen:** Formen, WordArt, Diagramme (QtCharts), 1800 Piktogramme (Lucide), Bildschirmfoto, Formel (einfache Schreibweise),
  Schnelltabellen, Deckblatt, Text aus Datei, Textbausteine, Datum/Uhrzeit-Dialog, Initiale, Textfeld; **Sendungen**: Umschlag,
  Etiketten, Seriendruck (Felder, Adressblock, Regeln, Vorschau), Formularfelder.
* **Oberfläche (modern, flach, Hell/Dunkel):** Register **Datei · Start · Einfügen · Seitenlayout · Verweise · Überprüfen · KI ·
  Ansicht** (+ Kontext-Register; „Sendungen“ nach Register anpassen), alternativ **Symbolleisten** mit Menüleiste; Register anpassen,
  Schnellzugriff, Symbole austauschen; Optionen-Fenster (3 Zweige, 17 Seiten); Hilfe (Handbuch, Tastenkürzel, Erweiterungen).
* **Schreibhilfe-Seitenleiste (rechts):** *Überprüfen / Schreibhilfe / KI*. Prüfregeln (Rechtschreibung, Grammatik, Zeichensetzung), Wellenlinien, Karten (Ändern/Lassen), Wortvorhersage,
  Gedächtnis (Zählung je Fund), Vorlesen, Lesehilfe, Zeilenfokus, **Barrierefreiheit-Prüfung**, **Thesaurus** (KI).
* **KI (freiwillig):** Korrigieren, Vorschläge, Übersetzen, Zusammenfassen, Text bearbeiten, Chat, Thesaurus, **eigene
  Assistenten**; Ollama / Claude / eigener Anbieter; Ergebnis wortweise eingesetzt; Zustimmung vor jedem Weg ins Internet.

## 3. Eingebundene Bibliotheken
| Bibliothek | Aufgabe | Lizenz | Hinweis |
|---|---|---|---|
| PySide6 / Qt 6 (inkl. QtCharts, QtSvg) | Oberfläche, Text-Engine, Druck, PDF, Diagramme | LGPL | |
| python-docx 1.2 | DOCX lesen/schreiben, Kommentare | MIT | Fuß-/Endnoten, Felder, Änderungen, Bibliografie per eigenem XML |
| msoffcrypto-tool | DOCX-Kennwort (AES) | MIT | |
| pypdf (nur Tests) | PDF prüfen | BSD | |
| LibreOffice (Programm) | ODT/DOC/RTF-Umwandlung | MPL | nur Kommandozeile, optional |
| LanguageTool (Programm) | Grammatik | LGPL | getrennter Prozess, optional, **nur gegen Fake-Server getestet** |
| Lucide-Symbole | Symbole (231 + Katalog 1800) | ISC | `assets/icons/LIZENZ-LUCIDE.txt` |
Nicht eingebunden: `odfpy` (ließ sich hier nicht bauen), PyMuPDF, pyphen (Qt kann Silbentrennung nicht nutzen).

## 4. WPS-Schnittstellen
Recherche: Für WPS Writer unter Linux fand ich **keine offiziell dokumentierte englischsprachige Automatisierungsschnittstelle**.
Hinweise: JSAPI-Erweiterungen laut Entwicklerdokumentation auf open.wps.cn (chinesisch) und das Drittprojekt *pywpsrpc*
(nur Linux). WPS ist auf dem Testrechner nicht installiert; beides wurde **nicht** eingebaut. Umgesetzt ist nur die unterste Stufe:
„Mit WPS Writer öffnen“ ruft ein installiertes `wps` auf (`integrations/wps.py`, per Test mit Attrappe). Direkte Integration ≠
Steuerung ≠ Bibliothek: Das Programm benutzt **keine** WPS-Interna.

## 5. Tests (tatsächlich ausgeführt)
`pytest tests`: **171 bestanden, 0 fehlgeschlagen** (≈ 45 s). Neben den Grundlagen (DOCX-Roundtrip, PDF, Einstellungen, Editor,
Fenster, KI mit Fake-Servern) jetzt auch: Zoom, Lineale, Weblayout/Zwei Seiten/Gliederung, Seitenfarbe/-rahmen/Wasserzeichen,
Kommentare/Noten/Änderungen (Editor und DOCX), Verweise und Verzeichnisse (mit LibreOffice-Öffnung), Einfügen, Sendungen,
Vorlagen und Lücken, Hilfe/Funktionstasten, Oberfläche wechseln, Werkzeug-Reiter, Gedächtnis, Kennwort, HTML-Codierung, eine
LibreOffice-erzeugte DOCX-Datei. **Nicht** durch Tests belegt: Bildschirmfoto am echten Bildschirm, Duplex-/Hintergrund-/Qualität-
Druckoptionen am Drucker, Zwischenstände, Sichern/Zurückholen, Gitternetz, Dunkelmodus (nur per Screenshot gesehen).

## 6. Offen und bekannte Einschränkungen
* **Eigene Formatvorlagen (neu):** Start ▸ Stile ▸ Formatvorlagen verwalten ▸ „Neue Vorlage aus der Auswahl“, ändern, löschen. In DOCX echte Absatzvorlagen;
  Vorlagen aus fremden DOCX-Dateien (bis 20) werden in den Katalog übernommen. **Grenzen:** die Vorlagen gelten für das Programm, nicht je Dokument;
  eigene Vorlagen sind Absatzvorlagen ohne Überschriftsebene; Änderungen wirken auf Absätze beim Übernehmen, nicht als lebende Verknüpfung in Word.
* **Rückgängig-Limit:** weiter offen — Qt kann den ältesten Schritt nicht verwerfen, nur den ganzen Stapel leeren.
* **SmartArt (neu):** Liste, Prozess, Hierarchie, Zyklus, Pyramide aus eingerücktem Text, fünf Farbschemata, bearbeitbar über den Reiter
  SmartArt-Tools und nach DOCX-Speichern/Öffnen in Lunivo weiter bearbeitbar. **Grenze:** In DOCX steht es als Bild — Word und LibreOffice zeigen es,
  bearbeiten es aber nicht als SmartArt (kein DrawingML-Diagramm).
* **Vergleichen/Zusammenführen (neu):** Überprüfen ▸ Vergleichen (zwei Dokumente) und Zusammenführen (mehrere Fassungen mit je einem Autor)
  schreiben Unterschiede als verfolgte Änderungen. **Grenzen:** nur Text und Absätze (keine Formatänderungen, keine Tabellenstruktur);
  ein zusammengeführter Absatz erscheint als gelöscht + neu; bei Überschneidung verschiedener Autoren gilt der erste, der andere wird als Konflikt gemeldet.
* **Abschnitte (neu):** mehrere Abschnitte mit eigener Seitengröße, Orientierung, Rändern, Spalten und Kopf-/Fußzeilen; DOCX-Rundreise
  (`w:sectPr` im letzten Absatz jedes Abschnitts) und Ausgabe als PDF mit LibreOffice gegengeprüft. **Grenzen:** Bearbeitungsansicht in der
  Geometrie des ersten Abschnitts; fortlaufender Umbruch mit anderer Geometrie → in der Ausgabe neue Seite; Noten je Abschnitt neu
  nummeriert; PDF-Kommentar- und Linkpositionen nutzen die Ränder des ersten Abschnitts; Drucken mit wechselndem Papier nur über die PDF-Ausgabe
  geprüft, nicht an einem echten Drucker.
* **Nicht getestet:** echter Mint-Desktop (X11/Wayland, HiDPI), echter Drucker, Claude/Ollama/LanguageTool/Piper/WPS in Wirklichkeit.
* **Qt-bedingt nicht möglich (im Prüfbogen ⬜):** Spalten und Spaltenumbruch, automatische
  Silbentrennung, frei schwebende Objekte/Textumbruch/Gruppieren, Formularsteuerelemente, PDF-Lesezeichen, Begrenzung des
  Rückgängig-Stapels, ausgeblendeter Text, Objektanker. Formen, WordArt, Diagramm, Piktogramm, Formel (als Bild bzw. Text) sind nach dem
  Einfügen nicht als Objekt bearbeitbar; das Wasserzeichen wird in DOCX **nicht** gespeichert (Warnung beim Speichern).
* **Fußnoten** stehen im PDF/Druck gesammelt am Textende, nicht am Seitenfuß; im DOCX sind es echte Fußnoten.
* **Nicht übertragen:** Tabellenblatt/Diagramm-Tools/Gleichungswerkzeuge/Zeichentools (Tabellenkalkulation und
  Präsentation sind ausgeschlossen), Sprechblasen bei Änderungen, „Gerade/ungerade Seiten“, „Dokument teilen“, Maßeinheit,
  Zuschnittsmarken drucken, Live-Vorschau/Minisymbolleiste, Wort-Extras.
* **Optionen** (Rest): siehe `PRUEFBOGEN.md` (Abschnitt OPTIONEN) — 21 Punkte insgesamt offen.
* Das **Handbuch** (Hilfe ▸ Handbuch) ist eine kurze Einführung; Einzelheiten stehen in dieser Dokumentation.
* Keine Behauptung vollständiger Word- oder WPS-Kompatibilität; Word selbst stand nicht zum Gegenprüfen zur Verfügung
  (geprüft mit LibreOffice und python-docx).

## 7. Installation und Start
Siehe [INSTALLATION.md](INSTALLATION.md): `./starten-qt.sh`.

### Nachtrag: KI-Konfiguration und Bildgenerierung
KI-Konfiguration (Aufgaben Chatbot, Zusammenfassen, Übersetzung, Textanalyse, Bildgenerierung), „Liste der KI-Modelle“ und
„Eigenen Anbieter hinzufügen“ (Vorlagen, Modellliste per `GET <URL>/models`, Fähigkeiten-Marken) nach dem alten Lunivo. „Text in Bild“
(KI-Reiter, Rechtsklick auf Markierung, Knopf „Bild“ im KI-Chat) schickt die Beschreibung an `POST <URL>/images/generations` des
Anbieters mit „Bilder“. Getestet gegen einen gefälschten OpenAI-Server; **nicht** gegen einen echten Bilddienst.

### Nachtrag: Silben farbig (Lesehilfe für Legasthenie), Silbentrennung, Textumbruch
* **Silben farbig** (Reiter Schreibhilfe ▸ Lesen, Optionen ▸ Leichter lesen): jede Silbe abwechselnd in einer anderen Farbe, nur als Anzeige
  (`QSyntaxHighlighter`) — Text und Datei bleiben unverändert. Einstellbar: Farbpaare, eigene Farben (2 oder 3), Schriftfarbe/Marker/beides,
  fett, Mindestlänge, einsilbige Wörter, Farbwechsel je Wort, nur Absatz mit dem Cursor, auch beim Drucken/PDF.
  Die Silben sind **deutsche Sprechsilben** (`services/silben_de.py`, eigene Regeln: Vokalkerne, Konsonantenhäufungen, ch/sch/ck/qu/ß,
  Mitlaut+l/r, getrennt gesprochene Vokale; Wortbausteine in Zusammensetzungen aus den pyphen-Mustern, gefiltert). Trefferquote:
  **228 von 228** in der Soll-Liste (von mir von Hand aufgestellt und beim Entwickeln benutzt — also nicht unabhängig) und
  **49 von 52** in einer harten, vorher nicht gesehenen Liste (Fremdwörter, seltene Zusammensetzungen). Bekannte Fehler: Zusammensetzungen
  mit vokalischem zweiten Teil, die pyphen nicht kennt (Zusammenarbeit → Zu-sam-me-nar-beit), einzelne Fremdwörter (Chirurg, Restaurant),
  Namen. Gilt nur für Deutsch. Nicht von Menschen mit Legasthenie erprobt; die Voreinstellungen (Blau/Rot, ab 4 Buchstaben) sind eine Annahme.
* **Silbentrennung** (wie im alten Lunivo: Zeilenumbruch mit Trennstrichen): pyphen, wirkt in Seitenansicht, Druck, PDF; DOCX `autoHyphenation`.
  Die Bearbeitungsansicht zeigt keine Trennstriche.
* **Textumbruch um Bilder**: links/rechts, Text umfließt; DOCX `wp:anchor` mit `wrapSquare` (gelesen und geschrieben, mit LibreOffice geprüft).

### Nachtrag: Spalten, Minisymbolleiste, Einfügeoptionen
* **Spalten** (Seitenlayout ▸ Spalten, Seite einrichten): 1–4 Spalten mit Abstand und Trennlinie, **auch beim Schreiben**: Der Text fließt auf der
  A4-Seite von Spalte zu Spalte, Klicken, Markieren über Spalten hinweg, Pfeiltasten, Zoom und Rechtschreibwellen arbeiten darauf. Technik:
  Das Dokument wird in Spaltenbreite und -höhe in „Spaltenseiten“ geteilt, `paintEvent` setzt sie nebeneinander, Mausereignisse und
  `cursorRect`/`cursorForPosition` werden abgebildet (`editor_widget._sp_*`). Ebenso in Seitenansicht, Druck, PDF und DOCX (`w:cols`,
  Spaltenumbruch; mit LibreOffice geprüft). **Grenzen:** gilt für das ganze Dokument (keine Abschnitte mit verschiedener Spaltenzahl); bei
  mehreren Spalten wirkt ein Seitenumbruch wie ein Spaltenumbruch; Ziehen und Ablegen von Text ist in Spalten abgeschaltet; Zeilennummern
  fehlen bei mehreren Spalten; die Spaltenumbrüche der Ansicht stammen aus Qts Seitenaufteilung und können in Randfällen (Tabellen,
  hohe Bilder) vom Druck um eine Zeile abweichen.
* **Minisymbolleiste** bei Auswahl und Rechtsklick; **Einfügeoptionen** (Standardformat, Schaltfläche nach dem Einfügen); **PDF**: Kommentare als
  Notizen, Lesezeichen aus Titel/Untertitel/Zitat; Schalter „Immer Korrekturvorschläge“.

### Nachtrag: Fußnoten am Seitenfuß, Verknüpfungen, Anzeige- und Druckoptionen
* **Fußnoten am Seitenfuß** (Seitenansicht, Druck, PDF, Seitenzählung): Die Kopie wird so umbrochen, dass die Fußnoten der Seite unter dem Text
  Platz haben (Absätze werden dazu geteilt); mit Trennstrich. Endnoten stehen am Textende. **Grenzen:** bei mehreren Spalten stehen die Fußnoten
  weiter gesammelt am Ende; eine Fußnote läuft nie auf die nächste Seite weiter; in der Bearbeitungsansicht stehen die Noten im Navigationsbereich.
* **PDF-Sprungverweise** Marke ↔ Note (Fuß- und Endnoten), Kommentare als Notizen, Lesezeichen aus Überschriften/Textmarken/Titel.
* Ausgeblendeter Text (DOCX `w:vanish`), Objektanker, Feldschattierung und -codes, Zahl im Kreis, Kopf-/Fußzeile im Seitenrand (Tipp, Doppelklick),
  Zeichnungsobjekte drucken, Änderungsbalken, Spalten live im Editor.
* **Sprechblasen**: Kommentare (und mit „Immer“ auch Einfügungen/Löschungen) als Blasen neben der Seite, mit Autor, Datum, Text, Verbindungslinien,
  gestapelt ohne Überlappung; Klick markiert den Text, Doppelklick bearbeitet den Kommentar. Einstellbar: Breite, Seitenrand links/rechts, Linien.
  Im Druck/PDF: Seite verkleinert neben den Blasen, Papierausrichtung automatisch/beibehalten/Querformat. Markup (Einfügungen, Löschungen,
  Farbe, Änderungsbalken) einstellbar. **Grenzen:** Blasen für Formatänderungen gibt es nicht; mit mehreren Spalten stehen die Blasen neben der
  ganzen Seite; im Druck ist die Anordnung eine Näherung an Word (Seite verkleinert statt Text umbrochen).

## Symbole (Fluent-Stil)

Die Symbole der Oberfläche stammen aus den **Fluent UI System Icons** (Microsoft, MIT; `assets/icons/fluent/`, Lizenztext in `LIZENZ.txt`) — derselben Formensprache wie die Segoe-Fluent-Symbole, die RibbonSpace benutzt (RibbonSpace selbst liefert keine Symboldateien, nur Schriftzeichen-Codes der Windows-Schrift). Zuordnung Symbolname → Fluent-Datei: `resources/fluent/zuordnung.json` (229 Symbole, je kleine 20-px- und große 28-px-Fassung). Ohne Zuordnung oder nach „Symbol austauschen“ greift weiter der Lucide-Strich. Einzelne Zuordnungen sind Annäherungen (z. B. „Sonderzeichen“) und können in der Datei geändert werden.
