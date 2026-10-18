# Abschlussbericht (Stand dieses Branches `native-qt6-port`)

Alle Angaben stammen aus tatsächlichen Läufen in der Entwicklungsumgebung (Linux, Qt „offscreen“, LibreOffice 25.x vorhanden).
**Nicht** auf einem echten Linux-Mint-Desktop mit Bildschirm, Drucker, Ollama/Claude, LanguageTool, Piper oder WPS getestet —
das ist offen (siehe 6). Der Prüfbogen ([PRUEFBOGEN.md](PRUEFBOGEN.md)) ist der Maßstab: **415 Punkte, ✅ 295 · ◐ 70 · ⬜ 50**;
„✅“ heißt „Befehl/Funktion vorhanden“, einzeln durch `tests/` belegt nur dort, wo im Eintrag ein Test genannt ist.

## 1. Dateien
`native_qt/` (≈ 15 700 Zeilen Python in 7 Paketen), `tests/` (22 Testdateien, 133 Tests), `werkzeug/` (Exportskripte für Register,
Symbolkatalog, Vorlagen, Handbuch; Abgleich-Skripte), `starten-qt.sh`, `requirements*.txt`, `doku/native-qt/*`. Die alte
Web-Oberfläche (`oberflaeche/`, `start.py`) ist unverändert; auf `main` wurde nichts geändert.

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
* **Schreibhilfe-Seitenleiste (rechts):** *Überprüfen / Schreibhilfe / KI*. Prüfregeln der Web-Fassung (Python nachweislich gleich:
  `tests/test_pruefung_paritaet.py` vergleicht gegen `pruefung.js` in Node), Wellenlinien, Karten (Ändern/Lassen), Wortvorhersage,
  Gedächtnis (Zählung wie in `ki.js`), Vorlesen, Lesehilfe, Zeilenfokus, **Barrierefreiheit-Prüfung**, **Thesaurus** (KI).
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
| Lucide-Symbole | Symbole (231 + Katalog 1800) | ISC | `native_qt/resources/LIZENZ-LUCIDE.txt` |
Nicht eingebunden: `odfpy` (ließ sich hier nicht bauen), PyMuPDF, pyphen (Qt kann Silbentrennung nicht nutzen).

## 4. WPS-Schnittstellen
Recherche: Für WPS Writer unter Linux fand ich **keine offiziell dokumentierte englischsprachige Automatisierungsschnittstelle**.
Hinweise: JSAPI-Erweiterungen laut Entwicklerdokumentation auf open.wps.cn (chinesisch) und das Drittprojekt *pywpsrpc*
(nur Linux). WPS ist auf dem Testrechner nicht installiert; beides wurde **nicht** eingebaut. Umgesetzt ist nur die unterste Stufe:
„Mit WPS Writer öffnen“ ruft ein installiertes `wps` auf (`integrations/wps.py`, per Test mit Attrappe). Direkte Integration ≠
Steuerung ≠ Bibliothek: Das Programm benutzt **keine** WPS-Interna.

## 5. Tests (tatsächlich ausgeführt)
`pytest tests`: **133 bestanden, 0 fehlgeschlagen** (≈ 45 s). Neben den Grundlagen (DOCX-Roundtrip, PDF, Einstellungen, Editor,
Fenster, KI mit Fake-Servern) jetzt auch: Zoom, Lineale, Weblayout/Zwei Seiten/Gliederung, Seitenfarbe/-rahmen/Wasserzeichen,
Kommentare/Noten/Änderungen (Editor und DOCX), Verweise und Verzeichnisse (mit LibreOffice-Öffnung), Einfügen, Sendungen,
Vorlagen und Lücken, Hilfe/Funktionstasten, Oberfläche wechseln, Werkzeug-Reiter, Gedächtnis, Kennwort, HTML-Codierung, eine
LibreOffice-erzeugte DOCX-Datei. **Nicht** durch Tests belegt: Bildschirmfoto am echten Bildschirm, Duplex-/Hintergrund-/Qualität-
Druckoptionen am Drucker, Zwischenstände, Sichern/Zurückholen, Gitternetz, Dunkelmodus (nur per Screenshot gesehen).

## 6. Offen und bekannte Einschränkungen
* **Nicht getestet:** echter Mint-Desktop (X11/Wayland, HiDPI), echter Drucker, Claude/Ollama/LanguageTool/Piper/WPS in Wirklichkeit.
* **Qt-bedingt nicht möglich (im Prüfbogen ⬜):** Spalten und Spaltenumbruch, Abschnitte (nur „Nächste Seite“), automatische
  Silbentrennung, frei schwebende Objekte/Textumbruch/Gruppieren, Formularsteuerelemente, PDF-Lesezeichen, Begrenzung des
  Rückgängig-Stapels, ausgeblendeter Text, Objektanker. Formen, WordArt, Diagramm, Piktogramm, Formel (als Bild bzw. Text) sind nach dem
  Einfügen nicht als Objekt bearbeitbar; das Wasserzeichen wird in DOCX **nicht** gespeichert (Warnung beim Speichern).
* **Fußnoten** stehen im PDF/Druck gesammelt am Textende, nicht am Seitenfuß; im DOCX sind es echte Fußnoten.
* **Nicht übertragen:** Tabellenblatt/Diagramm-Tools/SmartArt/Gleichungswerkzeuge/Zeichentools (Tabellenkalkulation und
  Präsentation sind ausgeschlossen), Sprechblasen bei Änderungen, „Gerade/ungerade Seiten“, „Dokument teilen“, Maßeinheit,
  Zuschnittsmarken drucken, Live-Vorschau/Minisymbolleiste, Wort-Extras.
* **Optionen** (Rest): siehe `PRUEFBOGEN.md` (Abschnitt OPTIONEN) — 50 Punkte insgesamt offen.
* Das **Handbuch** ist das der Web-Fassung (als Markdown); es beschreibt teils die Web-Oberfläche.
* Keine Behauptung vollständiger Word- oder WPS-Kompatibilität; Word selbst stand nicht zum Gegenprüfen zur Verfügung
  (geprüft mit LibreOffice und python-docx).

## 7. Installation und Start
Siehe [INSTALLATION.md](INSTALLATION.md): `./starten-qt.sh`.

### Nachtrag: KI-Konfiguration und Bildgenerierung
KI-Konfiguration (Aufgaben Chatbot, Zusammenfassen, Übersetzung, Textanalyse, Bildgenerierung), „Liste der KI-Modelle“ und
„Eigenen Anbieter hinzufügen“ (Vorlagen, Modellliste per `GET <URL>/models`, Fähigkeiten-Marken) nach dem alten Lunivo. „Text in Bild“
(KI-Reiter, Rechtsklick auf Markierung, Knopf „Bild“ im KI-Chat) schickt die Beschreibung an `POST <URL>/images/generations` des
Anbieters mit „Bilder“. Getestet gegen einen gefälschten OpenAI-Server; **nicht** gegen einen echten Bilddienst.
