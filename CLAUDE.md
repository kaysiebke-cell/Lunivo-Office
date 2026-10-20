# Lunivo Writer — Regeln für dieses Projekt

**Lunivo ist eine native Desktop-Anwendung in Python 3 mit PySide6 (Qt Widgets). Es ist keine Web-Anwendung und war nie eine.**

## Kein HTML — nirgends

Das gilt ausnahmslos und auch „nur intern“: **kein HTML, kein JavaScript, kein CSS, kein Browser, kein WebEngine/WebKit,
kein lokaler Webserver** — weder als Oberfläche noch als Dateiformat, Datenformat, Zwischenformat, Vorschau, Bericht oder
Werkzeug-Ausgabe. Sobald irgendwo HTML steckt, baut die nächste Arbeit darauf auf und das Projekt kippt Richtung Webanwendung.
Deshalb gar nicht erst anfangen.

- Text im Dokument: `QTextDocument`, `QTextCursor`, `QTextCharFormat`, `QTextBlockFormat` — niemals `toHtml`, `setHtml`,
  `insertHtml`, `fromHtml`.
- Speichern und Öffnen: DOCX, ODT, TXT, PDF (keine Webseite).
- Eigene Daten (Textbausteine u. a.): JSON ohne Markup, siehe `src/lunivo_writer/editor/textdaten.py`.
- Hilfe- und Infotexte: Markdown mit `QTextBrowser.setMarkdown`, Formeln und Vorschauen mit `QTextDocument` und `QPainter`.
- Berichte und Dokumentation: Markdown. Werkzeuge in `werkzeug/` schreiben kein HTML.
- Sieht eine Aufgabe nach HTML aus, einen Qt-Weg suchen. Gibt es keinen, dem Eigentümer melden — nicht ausweichen.

Gemeint sind Lunivos **eigene** Dateien, Daten und Code. Einzige Ausnahme: das Einfügen aus der Zwischenablage nimmt Inhalte aus
fremden Programmen an (`ui/document/base.py`, `document_editor.py`) — das ist keine Datei und kein Format von Lunivo.

Der Wächtertest `tests/test_main_window.py::test_kein_html_im_projekt` muss grün bleiben. Seine Liste `HTML_NOCH_ERLAUBT` darf
nur kleiner werden, nie größer.

## Arbeitsweise

- Aufbau des Projekts: `docs/README.md`. Gemeinsame Oberflächen-Bausteine (Farbpalette, Linien, Menüs, Dialoggerüst):
  `src/lunivo_writer/ui/baukasten/` und `docs/baukasten.md` — dort nachsehen, bevor etwas Neues gebaut wird.
- Tests: `.venv/bin/python -m pytest` (laufen ohne Bildschirm). Funktionsprüfung des Bandes: `werkzeug/funktionspruefung.py`.
- Das Projekt liegt nicht unter Git. Vor größeren Löschungen oder Umbauten eine Sicherung anlegen.
- WPS Office ist nur ein Aussehens-Vorbild (Bildschirmfotos). Keine WPS-Dateien, -Grafiken oder -Farbtabellen übernehmen.
