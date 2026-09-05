# Vorlesen

**Vorlesen** (F4). Über einen Fehler liest das Auge hinweg; das Ohr stolpert
darüber. Tempo einstellbar.

Die Stimmen des Systems (espeak-ng) klingen dabei zwangsläufig blechern — das
ist Bauart, nicht Einstellung: Sie rechnen Laute zusammen, statt sie aus
Aufnahmen zu setzen. Wer sich einen ganzen Brief anhören will, hört sonst vor
allem espeak. Ein Aufruf holt deshalb eine aufgenommene Stimme:

    ./stimme-holen.sh

Das lädt Piper und die deutsche Stimme „Thorsten" nach `~/.local/share/` —
90 MB, offline, kostenlos, nichts im System und nichts im Projekt. Danach
spricht sie von selbst.

Es gibt sieben deutsche Stimmen, männlich und weiblich:

    ./stimme-holen.sh --liste          zeigen, was es gibt
    ./stimme-holen.sh kerstin ramona   weitere dazu
    ./stimme-holen.sh --alle           alle sieben (~450 MB)

Nach jedem Laden kommt eine Probe. Gewählt wird unter *Schreibhilfe ▸
Vorlesen ▸ Stimme und Tempo*; die espeak-Stimmen bleiben darunter stehen.
Zum Entfernen genügt es, die `.onnx`-Datei zu löschen.
