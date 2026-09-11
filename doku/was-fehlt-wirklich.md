# Was wirklich fehlt

**Wiederholbar:** `python3 werkzeug/tiefe-messen.py`

Kay am 11.09.2026: *„das wird eine ganze Stange Arbeit die Funktionen
auszuarbeiten, da vieles rudimentär ist. Du hast so viele Funktionen
ausgelassen und nur ansatzweise gebaut."*

Er hatte recht — aber „vieles ist rudimentär" ist kein Befund, mit dem
sich arbeiten lässt. Also gezählt statt geschätzt: `register.js` sagt,
welche Befehle das Band anbietet, `programm.js` sagt, was sie tun.

## Das Ergebnis

**150 Befehle im Band.**

| | |
|---|---|
| **Fehlen ganz** — der Knopf greift ins Leere | **19** |
| Kurz, aber vollständig (reichen an eine andere Stelle weiter) | 13 |
| Knapp | 3 |
| Ausgebaut | 115 |

Die Zeilenzahl allein wäre ein schlechtes Maß: `B.fett` ist zwei Zeilen
lang und vollständig richtig. Gezählt wird deshalb, ob der Rumpf
überhaupt etwas anfasst — das Dokument, den Speicher, ein Fenster, eine
Stilklasse. Wer nur eine Meldung ausgibt, tut nichts.

## Die 19, die ins Leere greifen

**Reiter Referenzen — siebzehn Stück, also der ganze Reiter:**

Inhaltsverzeichnis · Abbildungsverzeichnis · Stichwortverzeichnis ·
Literaturverzeichnis · Verzeichnisse aktualisieren · Fußnote · Endnote ·
Nächste Note · Vorige Note · Notenbereich · Beschriftung · Querverweis ·
Indexeintrag · Zitat einfügen · Neue Quelle · Quellen verwalten ·
Zitierweise

**Reiter Einfügen — zwei Stück:**

Lesezeichen / Textmarke · Querverweis

Sie stehen im Band, tragen ein Symbol, lassen sich anklicken — und
`B.fussnote` gibt es in `programm.js` nicht. Ein Klick tut nichts, und
es kommt nicht einmal eine Meldung.

## Was das für die drei Reiter heißt, die Kay fotografiert hat

| Reiter | Befund |
|---|---|
| **Start** | Alle Befehle haben eine Umsetzung. |
| **Einfügen** | Zwei greifen ins Leere: Textmarke, Querverweis. |
| **Seitenlayout** | Alle Befehle haben eine Umsetzung. |

Das heißt nicht, dass dort alles so tief geht wie in WPS — ein Befehl
kann vorhanden und trotzdem dünner sein als sein Vorbild. Es heißt: Der
Knopf tut etwas.

## Die Reihenfolge, in der ich es angehen würde

1. **Fußnote und Endnote.** Der meistgebrauchte der siebzehn, und ohne
   ihn ist kein Schreiben mit Belegen möglich.
2. **Lesezeichen und Querverweis.** Beide stehen doppelt (Einfügen und
   Referenzen) und sind der Weg zurück an eine Stelle.
3. **Inhaltsverzeichnis.** Lunivo kennt die Überschriften bereits — die
   Gliederung zeigt sie. Daraus ein Verzeichnis zu bauen ist weniger
   Arbeit, als es aussieht.
4. **Beschriftung** für Bilder und Tabellen, dann darauf aufbauend das
   **Abbildungsverzeichnis**.
5. Zitate, Quellen, Stichwortverzeichnis — das ist wissenschaftliches
   Schreiben und kommt zuletzt.

---

Der Rohbericht steht in [was-fehlt-wirklich-roh.txt](was-fehlt-wirklich-roh.txt).

[← Zurück zum README](../README.md) · [Der Aufbau des Bandes](aufbau-band.md)
