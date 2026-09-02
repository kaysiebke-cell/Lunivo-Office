#!/usr/bin/env bash
#
# starten.sh — startet Lunivo-Office als eigenes Fenster.
#
# Der Menüeintrag wird bei JEDEM Start frisch geschrieben. Eine .desktop-Datei
# braucht feste Pfade, und Pfade ändern sich — verschiebt man den Ordner,
# zeigt der Eintrag ins Leere. Einmal von hier starten genügt, dann stimmt
# er wieder.
#
# Aufruf:  ./starten.sh                 startet das Programm
#          ./starten.sh --nur-eintrag   legt nur den Menüeintrag an
#          ./starten.sh --weg           nimmt den Menüeintrag zurück

set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"     # der Projektordner
EINTRAG="$HOME/.local/share/applications/lunivo-office.desktop"
SYMBOLE="$HOME/.local/share/icons/hicolor"

# Wie der Eintrag hieß, bevor das Programm Lunivo-Office wurde. Er wird bei
# jedem Start mit weggeräumt — sonst stünde die alte Fassung noch einmal im
# Menü, zeigte auf denselben Ordner und niemand wüsste, welche der beiden
# die richtige ist.
ALT_EINTRAG="$HOME/.local/share/applications/schreibprogramm.desktop"
ALT_NAME="schreibprogramm"
NAME="lunivo-office"

# Das Symbol in allen Größen ablegen.
#
# Eine einzige große Datei würde überall herunterskaliert — und bei 16
# Bildpunkten in der Fensterleiste bliebe davon ein Fleck. Deshalb liegt für
# jede Größe eine eigene Datei bereit, für die kleinen sogar eine eigens
# vereinfachte Zeichnung. Dazu die SVG-Fassung: Aus ihr rechnet sich der
# Arbeitsplatz jede Größe selbst, die hier nicht steht.
symbole_ablegen() {
  for G in 16 22 24 32 48 64 128 256 512; do
    ORDNER="$SYMBOLE/${G}x${G}/apps"
    [ -f "$HIER/symbole/icon-$G.png" ] || continue
    mkdir -p "$ORDNER"
    cp -f "$HIER/symbole/icon-$G.png" "$ORDNER/$NAME.png" 2>/dev/null || true
    rm -f "$ORDNER/$ALT_NAME.png"
  done
  mkdir -p "$SYMBOLE/scalable/apps"
  cp -f "$HIER/icon.svg" "$SYMBOLE/scalable/apps/$NAME.svg" 2>/dev/null || true
  rm -f "$SYMBOLE/scalable/apps/$ALT_NAME.svg" "$ALT_EINTRAG"
}

eintrag_schreiben() {
  mkdir -p "$(dirname "$EINTRAG")"
  symbole_ablegen
  cat > "$EINTRAG" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Lunivo-Office
GenericName=Textverarbeitung
Comment=Ein Raum für Worte — schreiben wie in LibreOffice, mit der Schreibhilfe fest an der Seite
Exec="$HIER/starten.sh"
Path=$HIER
Icon=lunivo-office
StartupWMClass=lunivo-office
Terminal=false
Categories=Office;WordProcessor;
Keywords=Schreiben;Text;Brief;Rechtschreibung;Korrektur;ODT;Lunivo;Schreibprogramm;Textverarbeitung;
StartupNotify=true
DESKTOP
  chmod +x "$EINTRAG" "$HIER/start.py"
  gtk-update-icon-cache -f -t "$SYMBOLE" 2>/dev/null || true
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
}

if [ "${1:-}" = "--weg" ]; then
  rm -f "$EINTRAG" "$ALT_EINTRAG" \
        "$SYMBOLE"/*/apps/lunivo-office.png "$SYMBOLE/scalable/apps/lunivo-office.svg" \
        "$SYMBOLE"/*/apps/schreibprogramm.png "$SYMBOLE/scalable/apps/schreibprogramm.svg"
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
  echo "Menüeintrag entfernt."
  exit 0
fi

eintrag_schreiben

if [ "${1:-}" = "--nur-eintrag" ]; then
  echo "Menüeintrag „Lunivo-Office“ zeigt jetzt auf: $HIER"
  exit 0
fi

if ! python3 -c "import gi; gi.require_version('WebKit2','4.1')" 2>/dev/null; then
  command -v zenity >/dev/null && zenity --error \
    --text="WebKit2GTK 4.1 fehlt.\nBitte installieren:\n  sudo apt install gir1.2-webkit2-4.1 python3-gi" 2>/dev/null || \
    echo "WebKit2GTK 4.1 fehlt: sudo apt install gir1.2-webkit2-4.1 python3-gi" >&2
  exit 1
fi

exec python3 "$HIER/start.py"
