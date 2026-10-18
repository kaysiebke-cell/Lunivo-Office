# Abschlussbericht (Stand dieses Branches `native-qt6-port`)

Alle Angaben stammen aus tatsächlichen Läufen in der Entwicklungsumgebung (Linux, Qt „offscreen“). **Nicht** auf einem
echten Linux-Mint-Desktop mit Bildschirm getestet — das ist offen (siehe 6).

## 1. Dateien
`native_qt/` (≈ 8300 Zeilen Python), `tests/` (15 Dateien), `werkzeug/register-exportieren.js`, `werkzeug/abgleich-native.py`,
`starten-qt.sh`, `requirements*.txt`, `doku/native-qt/*`. Die alte Web-Oberfläche ist unverändert; auf `main` wurde nichts geändert.

## 2. Tatsächlich umgesetzt
* **Dokumente:** neu, öffnen, speichern (atomar), speichern unter, Kopie, Export; mehrere Dokumente in Reitern; Startseite;
  Schutz vor ungespeicherten Änderungen; **Absturzwiederherstellung** (Sicherung alle 60 s, Angebot beim nächsten Start).
* **DOCX (Priorität 1):** lesen/schreiben mit Schrift, Größe, Fett/Kursiv/Unterstrichen/Durchgestrichen/Hoch-Tief, Farbe,
  Hervorhebung, Ausrichtung, Einzüge, Abstände, Zeilenabstand, Tabstopps, Absatzschattierung, Überschriften, Titel/Untertitel/Zitat,
  Listen (mit Neustart der Nummerierung), Seitenumbrüche, Tabellen (inkl. verbundener Zellen), Bilder, Hyperlinks, Seitengröße,
  Ränder, Kopf-/Fußzeile mit Seitenzahlfeld. Roundtrip-Test: zweiter Durchlauf liefert identischen Text.
* **ODT, DOC, RTF:** über LibreOffice (`soffice --headless --convert-to`); Roundtrip getestet inkl. Fett, Überschrift, Fußzeilenfeld.
  Ohne LibreOffice: ODT-Export über Qt (mit Warnung), DOC/RTF melden die fehlende Abhängigkeit.
* **Seite:** Papier, Ausrichtung, Ränder (Vorgaben wie im alten Programm), Seitenumbruch, Kopf-/Fußzeile, Seitenzahlen,
  Seitenzählung, **PDF-Export und Drucken** mit Kopf-/Fußzeile (Seitenzahlen, Größe, Querformat per Test geprüft), Druckvorschau.
* **Bearbeiten:** Format, Listen, Stilkatalog, Tabellen (Zeilen/Spalten/Verbinden/Teilen/Rahmen/Schattierung/Ausrichtung),
  Bilder (Größe, Alternativtext), Suchen/Ersetzen (ein Undo-Schritt), Sortieren, Format übertragen, Sonderzeichen,
  Inhaltsverzeichnis, Navigationsbereich, Formatierungszeichen, Rückgängig/Wiederholen.
* **Oberfläche nach dem alten Layout:** Dokumentreiter oben, ☰-Menü (zwei Spalten, zuletzt verwendete Dateien), Schnellzugriff,
  Reiter **Datei · Start · Einfügen · Seitenlayout · Verweise · Überprüfen · KI · Ansicht** (aus `register.js` erzeugt, 1:1),
  Kontext-Register (Tabellen-/Bildtools erscheinen bei Bedarf), Lucide-Symbole, Hell/Dunkel, Eckmarken, Statusleiste, Optionen-Fenster
  (3 Zweige, 14 Seiten).
* **Schreibhilfe-Seitenleiste (rechts):** Bereiche *Überprüfen / Schreibhilfe / KI*. Prüfen mit den Regeln der Web-Fassung
  (Python-Fassung nachweislich gleich: `tests/test_pruefung_paritaet.py` vergleicht gegen `pruefung.js` in Node), Wellenlinien,
  Karten mit Begründung („Ändern“/„Lassen“), Wortvorhersage mit Themenwörtern („Für wen?“), AutoKorrektur (7 Schalter),
  Gedächtnis, Vorlesen (Piper/speech-dispatcher), Lesehilfe (Papierton, Buchstaben-/Wortabstand), Zeilenfokus, Lesemodus.
* **KI (freiwillig):** Korrigieren, Vorschläge, Übersetzen, Zusammenfassen, Text bearbeiten, Chat; Ollama / Claude / eigener
  Anbieter; Ergebnis wird wortweise eingesetzt (Formatierung bleibt, ein Undo-Schritt); Zustimmung vor jedem Weg ins Internet.

## 3. Eingebundene Bibliotheken
| Bibliothek | Aufgabe | Lizenz | Hinweis |
|---|---|---|---|
| PySide6 / Qt 6 | Oberfläche, Text-Engine, Druck, PDF | LGPL | |
| python-docx | DOCX lesen/schreiben | MIT | |
| pypdf (nur Tests) | PDF prüfen | BSD | |
| LibreOffice (Programm) | ODT/DOC/RTF-Umwandlung | MPL | nur Kommandozeile, optional |
| LanguageTool (Programm) | Grammatik | LGPL | getrennter Prozess, optional, **nur gegen Fake-Server getestet** |
| Lucide-Symbole | Symbole | ISC | `native_qt/resources/LIZENZ-LUCIDE.txt` |
Nicht eingebunden: `odfpy` (ließ sich hier nicht bauen; ODT läuft über LibreOffice/Qt), PyMuPDF (nicht nötig).

## 4. WPS-Schnittstellen
Recherche: Für WPS Writer unter Linux fand ich **keine offiziell dokumentierte englischsprachige Automatisierungsschnittstelle**.
Hinweise: JSAPI-Erweiterungen laut Entwicklerdokumentation auf open.wps.cn (chinesisch) und das Drittprojekt *pywpsrpc*
(Python-Anbindung an eine WPS-RPC-Schnittstelle, nur Linux). WPS ist auf dem Testrechner nicht installiert; beides wurde **nicht** eingebaut.
Umgesetzt ist nur die unterste Stufe: „Mit WPS Writer öffnen“ ruft ein installiertes `wps` auf (`integrations/wps.py`, per Test mit Attrappe).
Direkte Integration ≠ Steuerung ≠ Bibliothek: Das Programm benutzt **keine** WPS-Interna.

## 5. Tests (tatsächlich ausgeführt)
`pytest tests`: **67 bestanden, 0 fehlgeschlagen** (≈ 24 s). Abgedeckt: DOCX-Roundtrip, ungültige Dateien, Meldung nicht unterstützter
Inhalte, PDF (Seiten, Kopf/Fuß, Querformat, Schriftgröße), TXT/ODT, LibreOffice-Roundtrip ODT/DOC/RTF, Einstellungen, Wiederherstellung,
Editor-Befehle, Suchen/Ersetzen, Tabellentools, Fenster (neu/bearbeiten/speichern/erneut öffnen), Tastenkürzel (Aktion),
Schutz vor Verlust, Prüfung (Parität zu JS), Wellen, AutoKorr, Vorhersage, KI mit Fake-Servern (Ollama/Claude/eigen),
Optionen, „keine Web-Module“.

## 6. Offen und bekannte Einschränkungen
* **Nicht getestet:** echter Mint-Desktop (X11/Wayland, HiDPI), echter Drucker, echtes Claude/Ollama/LanguageTool, WPS, Piper.
* **Seitenansicht:** eine durchgehende Fläche mit Seitenbreite, **keine** sichtbaren Seitengrenzen und kein **Zoom**, **kein Lineal**.
  Seitenzahl und Umbrüche stimmen für PDF/Druck.
* **Noch nicht umgesetzt** (112 Knöpfe, siehe `ABGLEICH.md`, im Programm ausgegraut): Fußnoten/Endnoten, Kommentare, Änderungen
  verfolgen, Zitate/Literatur, Beschriftungen/Index, Seriendruck/Umschlag/Etiketten/Formulare, Formen/SmartArt/WordArt/Diagramm,
  Spalten, Textfelder, Silbentrennung, Zeilennummern, Wasserzeichen/Seitenfarbe, Fenster-Anordnung, mehrere Abschnitte,
  Hilfsmittel „Textbausteine“, Vorlagen, Dokument schützen/teilen, Barrierefreiheit, Thesaurus.
* **Zweite Oberfläche „Symbolleisten“** (Menüleiste + zwei Symbolleisten wie `bilder/menues.png`) ist noch nicht gebaut; es gibt die
  Register-Oberfläche. Eine Menüleiste lässt sich über `ui/menueleiste` einblenden (enthält nur den Basisumfang).
* DOCX-Treue: Fußnoten, Textfelder, Kommentare, nachverfolgte Änderungen, Formeln, Formen, mehrere Abschnitte, „erste Seite anders“
  werden **gemeldet, aber nicht erhalten** — beim Speichern gehen sie verloren (Warnung beim Öffnen).
* Keine Behauptung vollständiger Word- oder WPS-Kompatibilität.

## 7. Installation und Start
Siehe [INSTALLATION.md](INSTALLATION.md): `./starten-qt.sh`.
