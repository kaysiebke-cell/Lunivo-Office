# Lunivo Writer — native Qt-Fassung

Eine Textverarbeitung für Linux Mint in **Python 3 + PySide6 (Qt 6 Widgets)**. Eine native Oberfläche aus Qt-Widgets,
ohne WebView und ohne lokalen Webserver. Startpfad: `starten-qt.sh` → `python -m lunivo_writer`.
Ein Test (`tests/test_main_window.py::test_no_web_modules_loaded`) prüft in einem frischen Prozess, dass weder
QtWebEngine/WebKit noch ein Webserver geladen wird.

## Starten
```bash
./starten-qt.sh                # legt beim ersten Mal .venv an, installiert PySide6 + python-docx, startet das Programm
./starten-qt.sh brief.docx     # Datei direkt öffnen
./starten-qt.sh --test         # Tests ausführen
./starten-qt.sh --eintrag      # Menüeintrag anlegen
```
Weiteres: [INSTALLATION.md](INSTALLATION.md). Was fertig ist und was fehlt: [BERICHT.md](BERICHT.md).

## Aufbau
```
main.py, pyproject.toml, requirements*.txt, starten-qt.sh      Start (python3 main.py  |  ./starten-qt.sh)
assets/        icons/ (Fluent- und Lucide-Symbole + Lizenzen), images/ (Logos), fonts/
docs/          diese Dokumentation (BERICHT, INSTALLATION, PRUEFBOGEN, pruefbogen/, pruefkatalog/)
src/lunivo_writer/
  app.py                 Einstieg (python -m lunivo_writer)
  core/                  application.py (QApplication, Theme, Start/Ende), document_manager.py (Laden, Speichern, Sicherung,
                         Wiederherstellung, zuletzt benutzt), commands.py (Aktionsname → Funktion), paths.py
  ui/                    main_window.py (koordiniert nur), theme.py, backstage.py (Reiter „Datei“), kuerzel.py
    ribbon/              ribbon_bar.py (Band aus resources/register.json), plan.py (Reihenfolge), tabs/ (ein Modul je Reiter),
                         toolbars.py (zweite Oberfläche), menubar.py, menue_tafel.py
    document/            document_editor.py (QTextEdit), document_area.py (Seitenfläche), document_tabs.py (Dokumentreiter),
                         lineal.py, navigation.py, seiten_ansicht.py, start_page.py, blasen_flaeche.py, zusatz_editor.py
    sidebar/             sidebar.py (Seitenleiste), panels/ (ai_panel = KI-Chat, writing_panel = Funde/Vorschläge/Hinweise)
    contextual/          table_tools.py, image_tools.py (Bild, Form), header_footer_tools.py
    widgets/             icons.py, flow_layout.py, live_vorschau.py, mini_leiste.py
    dialogs/             Optionen, Seite einrichten, Einfügen, KI, Hilfe, Formulare, …
    statusbar/           status_bar.py
  editor/                Dokumentlogik: pagination (Seiten, PDF, Druck), stile, umbruch, formular, verzeichnis, verweise, …
  models/                page.py (Seiteneinrichtung), report.py (Bericht über nicht Übernommenes)
  services/              file_service.py (DOCX/ODT/DOC/RTF/TXT), docx_reader/writer, settings_service.py, recovery.py,
                         bausteine.py, gelernt.py, vorlesen.py, integrations/ (LibreOffice, LanguageTool, WPS)
  ai/                    ki.py (Anbieter, Aufgaben), ai_service.py (Dienst für die Oberfläche)
  proofing/              pruefung.py (Regeln), proofing_service.py (Schreibhilfe), vorhersage, autokorrektur, barrierefreiheit, silben_de
  resources/             register.json, vorlagenmuster.json, handbuch.md, daten/ (regeln.json, themenwoerter.json, woerter.txt)
tests/                   pytest (ohne Bildschirm: QT_QPA_PLATFORM=offscreen)
werkzeug/                Abgleich-Skripte (Prüfbogen ↔ Programm)
```

Zuständigkeit in einem Satz: **core** steuert, **ui** zeigt, **editor** kennt das Dokument, **models** hält Daten, **services**
liest/schreibt Dateien und Einstellungen, **ai** und **proofing** sind die Schreibhilfe-Schicht (ohne Oberfläche).

## Grundsätze
* **Keine stille Abweichung:** Das Band wird aus `resources/register.json` *erzeugt*. Ein Knopf, den es nativ noch nicht gibt,
  steht ausgegraut da (Hinweis im Tooltip) — nicht fehlend, nicht als Attrappe.
* **Keine stillen Verluste:** Beim Öffnen/Speichern meldet ein Bericht alles, was nicht übernommen werden konnte
  (Textfelder, Formeln, Formen, mehrere Abschnitte, Wasserzeichen …). Fußnoten, Kommentare und nachverfolgte Änderungen werden
  seit dieser Fassung gelesen und geschrieben.
* **Privat:** Schlüssel nie im Quelltext, sondern in `ki.json` (0600) im Datenordner. Vor jedem Weg ins Internet fragt das
  Programm nach. Ollama läuft lokal.
* **Optional bleibt optional:** Ohne LibreOffice, LanguageTool, Piper, Ollama startet der Kern trotzdem.
