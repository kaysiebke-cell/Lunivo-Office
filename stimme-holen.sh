#!/bin/bash
# ============================================================
# Stimmen holen, die nicht nach Maschine klingen.
#
# Auf den meisten Linux-Rechnern spricht speech-dispatcher über espeak-ng.
# Das ist ein Formantsynthesizer: Er rechnet Laute zusammen, statt sie aus
# Aufnahmen zu setzen, und KANN deshalb nicht menschlich klingen. Wer sich
# seinen Brief vorlesen lässt, um Fehler zu hören, hört sonst vor allem
# espeak.
#
# Piper ist ein neuronaler Synthesizer: offline, kostenlos, auf der CPU
# schneller als in Echtzeit.
#
# Alles landet unter ~/.local/share/schreibhilfe/piper — nichts im System,
# nichts im Projekt. Zum Entfernen genügt es, den Ordner zu löschen; dann
# spricht wieder espeak. Eine einzelne Stimme entfernt man, indem man ihre
# .onnx-Datei löscht.
#
#   ./stimme-holen.sh                 Thorsten (männlich), der Grundstock
#   ./stimme-holen.sh kerstin ramona  weitere dazu
#   ./stimme-holen.sh --alle          alles, was es auf Deutsch gibt
#   ./stimme-holen.sh --liste         nur zeigen, was es gibt
# ============================================================
set -e

ZIEL="$HOME/.local/share/schreibhilfe/piper"
PROGRAMM="https://github.com/rhasspy/piper/releases/download/2023.11.14-2"
STIMMEN="https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE"

# Name → Ordner bei der Quelle : Dateiname : Größe : wer spricht
declare -A WAHL=(
  [thorsten]="thorsten/medium:de_DE-thorsten-medium:63 MB:männlich"
  [thorsten-fein]="thorsten/high:de_DE-thorsten-high:114 MB:männlich, feiner"
  [karlsson]="karlsson/low:de_DE-karlsson-low:63 MB:männlich"
  [pavoque]="pavoque/low:de_DE-pavoque-low:63 MB:männlich"
  [kerstin]="kerstin/low:de_DE-kerstin-low:63 MB:weiblich"
  [ramona]="ramona/low:de_DE-ramona-low:63 MB:weiblich"
  [eva]="eva_k/x_low:de_DE-eva_k-x_low:21 MB:weiblich, sparsam"
)
REIHE=(thorsten thorsten-fein kerstin ramona eva karlsson pavoque)

zeige_liste() {
    echo "Diese Stimmen gibt es:"
    for name in "${REIHE[@]}"; do
        IFS=':' read -r _ datei groesse wer <<< "${WAHL[$name]}"
        if [ -f "$ZIEL/$datei.onnx" ]; then da="  ✓ liegt schon da"; else da=""; fi
        printf "  %-14s %-9s %-18s%s\n" "$name" "$groesse" "$wer" "$da"
    done
}

if [ "$1" = "--liste" ]; then zeige_liste; exit 0; fi

if [ "$1" = "--alle" ]; then
    GEWUENSCHT=("${REIHE[@]}")
elif [ $# -gt 0 ]; then
    GEWUENSCHT=("$@")
else
    GEWUENSCHT=(thorsten)
fi

for name in "${GEWUENSCHT[@]}"; do
    if [ -z "${WAHL[$name]:-}" ]; then
        echo "„$name\" kenne ich nicht."; echo; zeige_liste; exit 1
    fi
done

mkdir -p "$ZIEL"
cd "$ZIEL"

# Das Programm braucht es nur einmal, egal wie viele Stimmen folgen.
if [ ! -x "$ZIEL/piper/piper" ]; then
    echo "Piper (26 MB) …"
    curl -fSL --progress-bar -o piper.tar.gz "$PROGRAMM/piper_linux_x86_64.tar.gz"
    tar xzf piper.tar.gz
    rm piper.tar.gz
fi

for name in "${GEWUENSCHT[@]}"; do
    IFS=':' read -r ordner datei groesse wer <<< "${WAHL[$name]}"
    if [ -f "$ZIEL/$datei.onnx" ]; then
        echo "$name liegt schon da."
        continue
    fi
    echo "$name ($wer, $groesse) …"
    curl -fSL --progress-bar -o "$datei.onnx"      "$STIMMEN/$ordner/$datei.onnx"
    curl -fSL --progress-bar -o "$datei.onnx.json" "$STIMMEN/$ordner/$datei.onnx.json"

    echo "  Probe:"
    echo "$name. Guten Tag. So klingt diese Stimme." \
      | "$ZIEL/piper/piper" --model "$ZIEL/$datei.onnx" --output_file "$ZIEL/probe.wav" 2>/dev/null
    if   command -v paplay >/dev/null; then paplay "$ZIEL/probe.wav"
    elif command -v aplay  >/dev/null; then aplay -q "$ZIEL/probe.wav"; fi
    rm -f "$ZIEL/probe.wav"
done

echo
echo "Fertig. Zu finden unter Einstellungen ▸ Vorlesen (Schreibhilfe)"
echo "beziehungsweise Schreibhilfe ▸ Vorlesen ▸ Stimme und Tempo (Schreibprogramm)."
