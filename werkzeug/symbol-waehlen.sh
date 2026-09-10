#!/usr/bin/env bash
#
# symbol-waehlen.sh — legt fest, welche Icon-Variante das Programm trägt.
#
#     werkzeug/symbol-waehlen.sh                    zeigt, was da ist
#     werkzeug/symbol-waehlen.sh klassisch-dunkel   setzt sie ein
#
# WARUM EIN BEFEHL UND KEIN HANDGRIFF
#
# Die Varianten liegen fertig in symbole/varianten/. Sie von Hand nach
# symbole/ zu kopieren geht auch — aber dann bleibt der Menüeintrag beim
# alten Bild stehen, weil der Arbeitsplatz sich die Symbole gemerkt hat.
# Das ist genau der Schritt, den man vergisst. Hier macht ihn der Befehl mit.

set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VARIANTEN="$HIER/symbole/varianten"

if [ $# -eq 0 ]; then
  echo "Vorhandene Varianten:"
  for V in "$VARIANTEN"/*/; do
    [ -d "$V" ] || continue
    echo "  $(basename "$V")"
  done
  echo
  echo "Aufruf:  werkzeug/symbol-waehlen.sh <name>"
  exit 0
fi

WAHL="$VARIANTEN/$1"
if [ ! -d "$WAHL" ]; then
  echo "Die Variante „$1“ gibt es nicht. Ohne Namen aufrufen zeigt die Liste." >&2
  exit 1
fi

cp -f "$WAHL"/icon-*.png "$WAHL"/icon.svg "$HIER/symbole/"
echo "symbole/ trägt jetzt „$1“."

# Erst damit sieht man es auch: der Arbeitsplatz liest die Symbole neu ein.
"$HIER/starten.sh" --nur-eintrag >/dev/null
echo "Menüeintrag und Symbolvorrat aufgefrischt."
