# Lunivo Writer — native Qt-Fassung

Eine Textverarbeitung für Linux Mint in **Python 3 + PySide6 (Qt 6 Widgets)**. Eine native Oberfläche aus Qt-Widgets,
ohne WebView und ohne lokalen Webserver. Startpfad: `starten-qt.sh` → `python -m native_qt`.
Ein Test (`tests/test_main_window.py::test_no_web_modules_loaded`) prüft in einem frischen Prozess, dass weder
QtWebEngine/WebKit noch ein Webserver geladen wird.

## Starten
```bash
./starten-qt.sh                # legt beim ersten Mal .venv an, installiert PySide6 + python-docx, startet das Programm
./starten-qt.sh brief.docx     # Datei direkt öffnen
./starten-qt.sh --test         # Tests ausführen
./starten-qt.sh --eintrag      # Menüeintrag anlegen
```
Weiteres: [INSTALLATION.md](INSTALLATION.md). Was fertig ist und was fehlt: [BERICHT.md](BERICHT.md) und [ABGLEICH.md](ABGLEICH.md).

## Aufbau
```
native_qt/
  main.py, theme.py
  windows/      main_window.py (Fenster), befehle.py (Aktionsname → Funktion)
  widgets/      register_band.py (Band aus register.json), reiterplan.py (Reiter nach der Struktur),
                schreibhilfe_panel.py (rechte Seitenleiste), chat_panel.py, optionen.py, menue_tafel.py (☰),
                navigation.py (Überschriften, Kommentare, Änderungen, Noten), doc_tabs.py, dialogs.py, lineal.py,
                symbolleisten.py (zweite Oberfläche), oberflaeche_dialoge.py, icons.py (Lucide, ISC), …
  editor/       editor_widget.py (QTextEdit-Editor), pagination.py (Seiten, PDF, Druck), page.py, verzeichnis.py,
                zusatz.py + zusatz_editor.py (Kommentare, Noten, Änderungen), verweise.py, literatur.py, einfuegen.py,
                sendungen.py, vorlagen.py, stile.py
  document_io/  docx_reader.py, docx_writer.py, formats.py (DOCX/ODT/DOC/RTF/TXT), report.py
  services/     pruefung.py (Regeln), writing_assistant.py, vorhersage.py, autokorrektur.py,
                ki.py + ki_dienst.py, vorlesen.py
  integrations/ libreoffice.py, languagetool.py, wps.py
  storage/      settings.py, recovery.py, gelernt.py
  resources/    register.json (Band), symbole.json (Lucide), fluent/ (Fluent-Symbole), daten/ (Regeln, Wörterbuch)
werkzeug/abgleich-native.py        erzeugt docs/ABGLEICH.md (jeder Knopf: umgesetzt/offen)
werkzeug/pruefbogen-*.py           Prüfbogen ↔ native Fassung (PRUEFBOGEN.md, 415 Punkte)
tests/                             pytest
```

## Grundsätze
* **Keine stille Abweichung:** Das Band wird aus `resources/register.json` *erzeugt*. Ein Knopf, den es nativ noch nicht gibt,
  steht ausgegraut da (Hinweis im Tooltip) — nicht fehlend, nicht als Attrappe.
* **Keine stillen Verluste:** Beim Öffnen/Speichern meldet ein Bericht alles, was nicht übernommen werden konnte
  (Textfelder, Formeln, Formen, mehrere Abschnitte, Wasserzeichen …). Fußnoten, Kommentare und nachverfolgte Änderungen werden
  seit dieser Fassung gelesen und geschrieben.
* **Privat:** Schlüssel nie im Quelltext, sondern in `ki.json` (0600) im Datenordner. Vor jedem Weg ins Internet fragt das
  Programm nach. Ollama läuft lokal.
* **Optional bleibt optional:** Ohne LibreOffice, LanguageTool, Piper, Ollama startet der Kern trotzdem.
