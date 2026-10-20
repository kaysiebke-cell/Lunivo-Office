#!/bin/bash
# Startet den Icon-Zeichner (Doppelklick im Dateimanager: „Im Terminal ausführen“ oder „Ausführen“ wählen).
cd "$(dirname "$0")/.." || exit 1
exec .venv/bin/python werkzeug/icon-zeichner.py "$@"
