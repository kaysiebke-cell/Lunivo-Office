# Was zusätzlich geholt wird

Vier Dinge liegen außerhalb des Programms, weil sie zu groß sind. Ohne sie läuft alles Übrige weiter.

Sie liegen **nicht** im Projektordner und werden bei Bedarf unter `~/.local/share/` abgelegt
(LanguageTool unter `~/.local/share/Lunivo Writer/languagetool` — dort liegt auch alles
Geschriebene und Gelernte):

| | wofür | Größe | nötig? |
|---|---|---|---|
| LibreOffice | ODT, DOC und RTF öffnen und speichern | ~700 MB | nur dafür |
| [LanguageTool](https://languagetool.org/) | „Gründlich prüfen" | ~400 MB | nein, freiwillig |
| [Piper](https://github.com/rhasspy/piper) + Thorsten | eine Stimme, die nicht nach Maschine klingt | ~90 MB | nein, `./stimme-holen.sh` |
| Schriften zum leichteren Lesen | OpenDyslexic, Lexend, Atkinson Hyperlegible | ~4 MB | nein, `./schrift-holen.sh` |

Ist LibreOffice im System installiert, genügt das auch. LanguageTool läuft
als **eigener Prozess** — seine LGPL-Lizenz berührt dieses Programm nicht.

Schreiben, Prüfen, Speichern als DOCX, PDF-Export und Drucken gehen ohne alles davon.

**Die Schriften** landen unter `~/.local/share/fonts/lunivo-office` und
stehen danach oben in der Schriftliste unter *Leichter zu lesen*:

    ./schrift-holen.sh                  OpenDyslexic
    ./schrift-holen.sh lexend atkinson  weitere dazu
    ./schrift-holen.sh --alle           alle drei (~4 MB)
    ./schrift-holen.sh --liste          zeigen, was es gibt
    ./schrift-holen.sh --weg            wieder entfernen

**OpenDyslexic** macht die Buchstaben unten schwerer als oben. Das gibt
ihnen ein Gewicht, und ein Gewicht hat eine Richtung — b und d, p und q
lassen sich dann nicht mehr so leicht verwechseln. **Lexend** ist nicht
gegen das Verwechseln gemacht, sondern für das Tempo: weite Buchstaben,
viel Luft dazwischen. **Atkinson Hyperlegible** kommt vom Braille Institute
und unterscheidet, was einander ähnelt — I, l und 1; O und 0. Alle drei
stehen unter der SIL Open Font License.

---

[← Zurück zum README](../README.md)
