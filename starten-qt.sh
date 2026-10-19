#!/usr/bin/env bash
#
# starten-qt.sh — startet Lunivo Writer (native Qt-Oberfläche, kein Browser, kein Webserver).
#
# Beim ersten Start wird eine eigene Python-Umgebung (.venv) angelegt und
# PySide6 sowie python-docx hineininstalliert. Das System-Python bleibt unberührt.
#
#   ./starten-qt.sh [Datei.docx …]   startet das Programm
#   ./starten-qt.sh --eintrag        legt zusätzlich einen Menüeintrag an
#   ./starten-qt.sh --test           führt die Tests aus
#   ./starten-qt.sh --weg            nimmt den Menüeintrag zurück (Dokumente bleiben unberührt)
set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$HIER/.venv"
EINTRAG="$HOME/.local/share/applications/lunivo-writer.desktop"

if [ "${1:-}" = "--weg" ]; then
  rm -f "$EINTRAG"; echo "Menüeintrag entfernt. Die Umgebung $VENV und Ihre Dokumente bleiben bestehen."; exit 0
fi

command -v python3 >/dev/null || { echo "python3 fehlt. Installation: sudo apt install python3 python3-venv" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || { echo "Python 3.9 oder neuer wird gebraucht." >&2; exit 1; }
python3 -c 'import venv, ensurepip' 2>/dev/null \
  || { echo "python3-venv fehlt. Installation: sudo apt install python3-venv" >&2; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  echo "Lege die Python-Umgebung an (einmalig) …"
  python3 -m venv "$VENV"
fi
if ! "$VENV/bin/python" -c 'import PySide6, docx' 2>/dev/null; then
  echo "Installiere Abhängigkeiten …"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet -r "$HIER/requirements.txt" \
    || { echo "Installation fehlgeschlagen. Prüfen Sie die Internetverbindung." >&2; exit 1; }
fi

if [ "${1:-}" = "--eintrag" ]; then
  mkdir -p "$(dirname "$EINTRAG")"
  cat > "$EINTRAG" <<D
[Desktop Entry]
Type=Application
Name=Lunivo Writer
Comment=Textverarbeitung
Exec=$HIER/starten-qt.sh %F
Icon=$HIER/assets/symbole/varianten/Abstrakt/icon-256.png
Terminal=false
Categories=Office;WordProcessor;
MimeType=application/vnd.openxmlformats-officedocument.wordprocessingml.document;text/plain;
D
  echo "Menüeintrag angelegt: $EINTRAG"; shift
fi

if [ "${1:-}" = "--test" ]; then
  "$VENV/bin/pip" install --quiet -r "$HIER/requirements-dev.txt"
  cd "$HIER" && QT_QPA_PLATFORM=offscreen exec "$VENV/bin/python" -m pytest tests -q
fi

cd "$HIER"
PYTHONPATH="$HIER/src" exec "$VENV/bin/python" -m lunivo_writer "$@"
