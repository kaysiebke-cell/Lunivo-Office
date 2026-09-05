# Entwickler-Werkzeuge

Skripte im Ordner `werkzeug/`:

- namen-pruefen.py — prüft doppelte Namen im Code
- katalog-bauen.py — erstellt Symbolkatalog aus SVGs
- svg-zu-pfad.py — konvertiert elementare SVG‑Elemente in Pfade
- bildschirmfoto.py — erstellt Screenshots für das README

Git‑Hooks

- `werkzeug/haken-an.sh` richtet Prüfungen bei jedem Commit ein (setzt core.hooksPath im Repository).

Tests & Prüfer

- Der JS‑Prüfer läuft bei Commit und meldet Probleme; bei Bedarf mit `git commit --no-verify` umgehen.

Beitragende sollten `.github/CONTRIBUTING.md` lesen.
