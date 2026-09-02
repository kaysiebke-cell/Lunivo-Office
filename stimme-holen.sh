#!/bin/bash
# ============================================================
# Eine Stimme holen, die nicht nach Maschine klingt.
#
# Auf den meisten Linux-Rechnern spricht speech-dispatcher über espeak-ng.
# Das ist ein Formantsynthesizer: Er rechnet Laute zusammen, statt sie aus
# Aufnahmen zu setzen, und KANN deshalb nicht menschlich klingen. Wer sich
# seinen Brief vorlesen lässt, um Fehler zu hören, hört sonst vor allem
# espeak.
#
# Piper ist ein neuronaler Synthesizer: offline, kostenlos, auf der CPU
# schneller als in Echtzeit. Die deutsche Stimme heißt „Thorsten".
#
# Es landet alles unter ~/.local/share/, nichts im System und nichts im
# Projekt — 90 MB gehören nicht ins Repo. Zum Entfernen genügt es, den
# Ordner zu löschen; dann spricht wieder espeak.
# ============================================================
set -e

ZIEL="${1:-$HOME/.local/share/schreibhilfe/piper}"
QUELLE="https://github.com/rhasspy/piper/releases/download/2023.11.14-2"
STIMMEN="https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium"
NAME="de_DE-thorsten-medium"

if [ -x "$ZIEL/piper/piper" ] && [ -f "$ZIEL/$NAME.onnx" ]; then
    echo "Die Stimme liegt schon in $ZIEL."
    exit 0
fi

echo "Es werden etwa 90 MB nach $ZIEL geladen."
mkdir -p "$ZIEL"
cd "$ZIEL"

if [ ! -x "$ZIEL/piper/piper" ]; then
    echo "  Programm (26 MB) …"
    curl -fSL -o piper.tar.gz "$QUELLE/piper_linux_x86_64.tar.gz"
    tar xzf piper.tar.gz
    rm piper.tar.gz
fi

if [ ! -f "$ZIEL/$NAME.onnx" ]; then
    echo "  Stimme Thorsten (63 MB) …"
    curl -fSL -o "$NAME.onnx"      "$STIMMEN/$NAME.onnx"
    curl -fSL -o "$NAME.onnx.json" "$STIMMEN/$NAME.onnx.json"
fi

echo "Probe:"
echo "Die Stimme ist eingerichtet. So klingt sie." \
  | "$ZIEL/piper/piper" --model "$ZIEL/$NAME.onnx" --output_file "$ZIEL/probe.wav" 2>/dev/null
if command -v paplay >/dev/null; then paplay "$ZIEL/probe.wav"
elif command -v aplay >/dev/null; then aplay -q "$ZIEL/probe.wav"
fi
rm -f "$ZIEL/probe.wav"

echo "Fertig. Beide Programme nehmen sie beim nächsten Start von selbst."
