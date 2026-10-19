# Lesen und Schreiben

Wofür Lunivo gebaut ist: die Lesehilfe, die Schriften, das Vorlesen.

**Für wen das gebaut ist.** Die Grundschrift ist **OpenDyslexic** — die
Buchstaben sind unten schwerer als oben, damit sie nicht kippen, und b/d
und p/q sehen verschieden aus statt gespiegelt gleich. Georgia steht als
Rückfall dahinter, falls sie auf einem Rechner fehlt. Daneben liegen

**Alles an einer Stelle.** Der Reiter **Schreibhilfe** trägt, was das
Lesen und Schreiben erleichtert: Lesehilfe, Zeilenfokus, Lesemodus,
Schriftwahl, Prüfung, Wortvorhersage, AutoKorrektur, Vorlesen,
Silbentrennung, Übersetzen, Thesaurus, KI. Vorher lag das über fünf
Reiter verstreut — jedes an seinem sachlich richtigen Platz, zusammen
aber nur zu finden, wenn man wusste, wo man suchen muss. Die

**Lesehilfe** hat dazu die Taste **F2**.

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

**Lexend** und **Atkinson Hyperlegible**; in den Optionen unter
*Schriftarten* stehen alle drei als Knöpfe, jeder in seiner eigenen
Schrift und mit einem Satz dazu, was sie tut — man muss ihren Namen nicht
kennen.

---

[← Zurück zum README](../README.md)
