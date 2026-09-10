# Die Einstellungen

Das Optionen-Fenster, die Sprachen, das Kennwort, die Einstellungsdatei.

**Optionen** — *☰ Menü ▸ Optionen*, oder **F9**. Links ein Baum mit drei
Zweigen, rechts der Bereich, zweispaltig und kompakt wie im WPS Writer.

*Leichter lesen* steht zuoberst: **Lesehilfe**, **Schriftarten**,

**Sprache**, **Rechtschreibprüfung**. Darunter *Wie im WPS Writer* mit

**allen dreizehn Seiten** in seiner Reihenfolge und mit seinen Namen, und
zuletzt *Nur bei Lunivo* — Schreibhilfe und KI, Gedächtnis und
*Erweitert*, wo steht, was zusätzlich geholt wurde und ob es da ist.

86 Schalter und 20 Klapplisten, keiner davon eine Attrappe. Die Schalter
sind dieselben wie im Menü und im Band — ein Schalter, drei Stellen, ein
Zustand; wer ihn irgendwo umlegt, sieht ihn überall wechseln.

*Menüband anpassen* und *Symbolleiste für den Schnellzugriff* sind nach
demselben Bild gebaut: links die Befehle mit Klappliste, Suchfeld und
ihren Zeichnungen, in der Mitte Hinzufügen und Entfernen, rechts das
Ziel — beim Menüband ein Baum aus Registerkarten und Gruppen, bei der
Leiste ihr Inhalt. Neue Registerkarten und Gruppen lassen sich anlegen
und umbenennen.

**Das Dokumentkennwort** verschlüsselt wirklich: AES-256, den Schlüssel
mit PBKDF2 aus dem Kennwort, beides vom Browser selbst gerechnet. Ohne das
Kennwort ist der Inhalt nicht mehr zu lesen, auch nicht von Lunivo — und
ein vergessenes kann niemand wiederherstellen.

**Die Einstellungen liegen in einer Datei**, lesbar, eine Zeile je
Einstellung: `~/.config/lunivo-office/einstellungen.conf` — dort, wo auch
WPS seine ablegt. Sie lässt sich sichern, auf einen zweiten Rechner
mitnehmen und von Hand ändern. Der Speicher des Fensters bleibt, was er
war; die Datei ist sein Abbild, beim Start gelesen und nach jeder
Änderung neu geschrieben.

---

[← Zurück zum README](../README.md)
