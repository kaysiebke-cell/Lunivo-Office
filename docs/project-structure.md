# Projektstruktur

Wichtigste Dateien und Ordner (Kurzreferenz):

- start.py — Fenster, Server, Schriften, LibreOffice‑Integration, Vorlesen
- starten.sh — Startscript, legt Menüeintrag an
- stimme-holen.sh — lädt Piper‑Stimmen (optional)
- schrift-holen.sh — lädt lesefreundliche Schriften (optional)

- oberflaeche/ — alles, was das Fenster liefert
  - index.html
  - css/programm.css
  - js/programm.js, js/dokument.js, js/dateien.js, js/pruefung.js, js/ki.js, js/einstellungen.js
  - daten/ — regeln.js, woerter.txt, symbole.js, symbolkatalog

- werkzeug/ — Hilfsprogramme für die Entwicklung
  - katalog-bauen.py, svg-zu-pfad.py, namen-pruefen.py, bildschirmfoto.py

- bilder/ — Logos und Screenshots
- symbole/ — Icon SVGs
- doku/ — ENTSTEHUNG.md, LIESMICH.md (vollständige Langfassung)

Siehe auch docs/dev-tools.md für Entwicklerhinweise.
