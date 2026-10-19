#!/usr/bin/env bash
#
# installieren.sh — richtet Lunivo-Office (GTK4) für den angemeldeten Benutzer ein:
#   - Startbefehl   ~/.local/bin/lunivo-office
#   - Symbol        ~/.local/share/icons/hicolor/…/apps/lunivo-office.png|svg
#   - Menüeintrag   ~/.local/share/applications/lunivo-office.desktop  (Cinnamon-Menü)
#
# Aufruf:   ./native/installieren.sh            installieren
#           ./native/installieren.sh --weg      wieder entfernen
#
# Es wird nichts im Projektordner verändert und keine Nutzerdaten angefasst.
set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJEKT="$(dirname "$HIER")"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor"
EINTRAG="$APPS/lunivo-office.desktop"

if [ "${1:-}" = "--weg" ]; then
  rm -f "$BIN/lunivo-office" "$EINTRAG" "$ICONS"/*/apps/lunivo-office.png "$ICONS/scalable/apps/lunivo-office.svg"
  update-desktop-database "$APPS" 2>/dev/null || true
  gtk-update-icon-cache -f -t "$ICONS" 2>/dev/null || true
  echo "Entfernt."; exit 0
fi

# ---- Abhängigkeiten prüfen (nur melden, nichts installieren)
fehlt=()
python3 -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk" 2>/dev/null \
  || fehlt+=("python3-gi gir1.2-gtk-4.0")
command -v node >/dev/null || fehlt+=("nodejs   (für die Schreibhilfe)")
command -v soffice >/dev/null || fehlt+=("libreoffice-writer   (für docx/odt/pdf)")
if [ ${#fehlt[@]} -gt 0 ]; then
  echo "Es fehlt noch:"; printf '  - %s\n' "${fehlt[@]}"
  echo "Installieren mit:  sudo apt install python3-gi gir1.2-gtk-4.0 nodejs libreoffice-writer"
fi

# ---- Startbefehl
mkdir -p "$BIN" "$APPS"
cat > "$BIN/lunivo-office" <<EOF
#!/usr/bin/env bash
exec python3 "$HIER/lunivo-office-gtk" "\$@"
EOF
chmod +x "$BIN/lunivo-office" "$HIER/lunivo-office-gtk"

# ---- Symbol (aus dem Entwurf in symbole/ in allen Größen)
QUELLE_SVG="$(ls "$PROJEKT"/symbole/varianten/Abstrakt/lunivo-konzept-master-1024.svg 2>/dev/null | head -1 || true)"
QUELLE_PNG="$(ls "$PROJEKT"/symbole/varianten/Abstrakt/lunivo-konzept-master-1024.png 2>/dev/null | head -1 || true)"
for g in 16 24 32 48 64 128 256 512; do
  mkdir -p "$ICONS/${g}x${g}/apps"
  ziel="$ICONS/${g}x${g}/apps/lunivo-office.png"
  if   [ -n "$QUELLE_SVG" ] && command -v rsvg-convert >/dev/null; then rsvg-convert -w $g -h $g "$QUELLE_SVG" -o "$ziel"
  elif [ -n "$QUELLE_PNG" ] && command -v convert >/dev/null;       then convert "$QUELLE_PNG" -resize ${g}x${g} "$ziel"
  elif [ -n "$QUELLE_PNG" ];                                        then cp -f "$QUELLE_PNG" "$ziel"
  fi
done
if [ -n "$QUELLE_SVG" ]; then
  mkdir -p "$ICONS/scalable/apps"; cp -f "$QUELLE_SVG" "$ICONS/scalable/apps/lunivo-office.svg"
fi

# ---- Menüeintrag
cat > "$EINTRAG" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Lunivo-Office
GenericName=Textverarbeitung
Comment=Schreibprogramm mit der Schreibhilfe fest an der Seite
Exec=$BIN/lunivo-office %F
Icon=lunivo-office
Terminal=false
Categories=Office;WordProcessor;GTK;
MimeType=application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/vnd.oasis.opendocument.text;text/html;text/plain;
StartupWMClass=de.lunivo.Office
Keywords=Text;Schreiben;Dokument;Office;
EOF
chmod +x "$EINTRAG"
update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache -f -t "$ICONS" 2>/dev/null || true

echo "Fertig. Lunivo-Office steht jetzt im Menü unter „Büro“ (oder: lunivo-office im Terminal)."
echo "Hinweis: Das alte Programm (starten.sh) schreibt beim Start denselben Menüeintrag neu."
