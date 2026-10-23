# Die Einstellungen

Das Optionen-Fenster, die Sprachen, das Kennwort, die Einstellungsdatei.

**Optionen** — *☰ Menü ▸ Optionen*, oder **F9**. Links die Suche und eine flache Liste mit sechs Seiten
(*Lesen, Anzeige, Schreiben, Speichern, Drucken und PDF, Name und KI*), rechts die Seite. Jede Seite zeigt das Häufige; der Rest
steht unter *Weitere Einstellungen*. Aufbau: [aufbau-optionen.md](aufbau-optionen.md).

**Hell oder Dunkel** — ganz oben unter *Anzeige*, oder mit **Strg+Umschalt+D**, im Menü *Ansicht* und über den Knopf in der Statusleiste.

*Menüband anpassen* und *Symbolleiste für den Schnellzugriff* öffnen als eigenes Fenster (*Anzeige ▸ Weitere Einstellungen*):
links die Befehle mit Klappliste, Suchfeld und ihren Zeichnungen, in der Mitte Hinzufügen und Entfernen, rechts das
Ziel — beim Menüband ein Baum aus Registerkarten und Gruppen, bei der Leiste ihr Inhalt. Neue Registerkarten und Gruppen lassen sich
anlegen und umbenennen.

**Das Dokumentkennwort** verschlüsselt wirklich: AES-256, den Schlüssel
mit PBKDF2 aus dem Kennwort, beides vom Programm selbst gerechnet. Ohne das
Kennwort ist der Inhalt nicht mehr zu lesen, auch nicht von Lunivo — und
ein vergessenes kann niemand wiederherstellen.

**Die Einstellungen liegen in einer Datei**, lesbar, eine Zeile je
Einstellung: `~/.config/lunivo-office/einstellungen.conf` — dort, wo auch
 seine ablegt. Sie lässt sich sichern, auf einen zweiten Rechner
mitnehmen und von Hand ändern. Der Speicher des Fensters bleibt, was er
war; die Datei ist sein Abbild, beim Start gelesen und nach jeder
Änderung neu geschrieben.

---

[← Zurück zum README](../README.md)
