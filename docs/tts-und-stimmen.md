# Vorlesen & Stimmen

Vorlesen (F4) nutzt standardmäßig espeak-ng für TTS. Für natürlichere Stimmen gibt es Piper‑Meldungen, die optional heruntergeladen werden.

Stimmen herunterladen

    ./stimme-holen.sh

Beispiele:

    ./stimme-holen.sh --liste          # Verfügbare Stimmen anzeigen
    ./stimme-holen.sh kerstin ramona   # weitere Stimmen herunterladen
    ./stimme-holen.sh --alle           # alle (~450 MB)

Die Stimmen werden nach `~/.local/share/` gelegt und sind anschließend in den Einstellungen auswählbar.

Entfernen einer Stimme: die .onnx‑Datei löschen oder `./stimme-holen.sh --weg` (je nach Skript‑Support).
