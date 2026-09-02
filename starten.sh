#!/usr/bin/env bash
#
# starten.sh — startet das Schreibprogramm als eigenes Fenster.
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
EINTRAG="$HOME/.local/share/applications/schreibprogramm.desktop"
SYMBOLE="$HOME/.local/share/icons/hicolor"

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
    cp -f "$HIER/symbole/icon-$G.png" "$ORDNER/schreibprogramm.png" 2>/dev/null || true
  done
  mkdir -p "$SYMBOLE/scalable/apps"
  cp -f "$HIER/icon.svg" "$SYMBOLE/scalable/apps/schreibprogramm.svg" 2>/dev/null || true
}

eintrag_schreiben() {
  mkdir -p "$(dirname "$EINTRAG")"
  symbole_ablegen
  cat > "$EINTRAG" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Schreibprogramm
GenericName=Textverarbeitung
Comment=Schreiben wie in LibreOffice — mit der Schreibhilfe fest an der Seite
Exec="$HIER/starten.sh"
Path=$HIER
Icon=schreibprogramm
StartupWMClass=schreibprogramm
Terminal=false
Categories=Office;WordProcessor;
Keywords=Schreiben;Text;Brief;Rechtschreibung;Korrektur;ODT;
StartupNotify=true
DESKTOP
  chmod +x "$EINTRAG" "$HIER/start.py"
  gtk-update-icon-cache -f -t "$SYMBOLE" 2>/dev/null || true
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
}

if [ "${1:-}" = "--weg" ]; then
  rm -f "$EINTRAG" "$SYMBOLE"/*/apps/schreibprogramm.png "$SYMBOLE/scalable/apps/schreibprogramm.svg"
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
  echo "Menüeintrag entfernt."
  exit 0
fi

eintrag_schreiben

if [ "${1:-}" = "--nur-eintrag" ]; then
  echo "Menüeintrag „Schreibprogramm“ zeigt jetzt auf: $HIER"
  exit 0
fi

if ! python3 -c "import gi; gi.require_version('WebKit2','4.1')" 2>/dev/null; then
  command -v zenity >/dev/null && zenity --error \
    --text="WebKit2GTK 4.1 fehlt.\nBitte installieren:\n  sudo apt install gir1.2-webkit2-4.1 python3-gi" 2>/dev/null || \
    echo "WebKit2GTK 4.1 fehlt: sudo apt install gir1.2-webkit2-4.1 python3-gi" >&2
  exit 1
fi

exec python3 "$HIER/start.py"
