# Bild gegen Bild: der Reiter Ansicht

Kay am 13.09.2026: *„das wird noch ein hartes Stück Arbeit, WPS und mein
Programm zu vergleichen"* — und dann zwei Aufnahmen geschickt: das Band
von WPS Writer und das eigene, beide auf dem Reiter Ansicht.

Diese Datei hält fest, was **auf den Bildern** zu sehen ist. Das ist
etwas anderes als [reiter-abgleich.md](reiter-abgleich.md): Der vergleicht
Listen gegen Listen — sein Prüfkatalog gegen `register.js` — und meldet
für Ansicht **alles gleich**. Die Bilder zeigen etwas, das keine Liste
zeigen kann.

## Der wichtigste Befund: die Beschriftung

**WPS beschriftet im Reiter Ansicht jeden Knopf.** Vollbildgröße,
Leseansicht, Drucklayout, Rahmen, Weblayout, Navigationsbereich,
Augenschutzmodus, Neues Fenster, Fenster teilen — jedes Symbol trägt sein
Wort. Die Schalter stehen sogar als Kontrollkästchen **mit** Text da:

    ☐ Lineal          ☐ Gitternetzlinien anzeigen   ☑ Tabellengitternetzlinien
    ☑ Markup          ☑ Task-Fenster

**Lunivo beschriftet sieben Knöpfe von siebenundzwanzig.** Beschriftet
sind nur die großen: Drucklayout, Lesemodus, Vergrößern, Verkleinern,
Neues Fenster, Anordnen, Register anpassen. Die übrigen zwanzig stehen
als bloßes Symbol da — Zwei Seiten, Weblayout, Gliederung, Lineal,
Vertikales Lineal, Gitternetzlinien, Navigationsbereich,
Textbegrenzungen, Seitenleiste Schreibhilfe, Seitenbreite, Eine Seite,
Zoom, Nebeneinander, Untereinander, Kacheln, Fensterliste, die drei
Helligkeiten und fünf der Oberflächen-Punkte.

Das erklärt einen Satz, der in seinem Prüfkatalog immer wieder steht:

> *„Icon ist als solches als Funktion nicht zu erkennen."*

Er steht dort bei Zeilenabstand, Durchgestrichen, Seitenumbruch,
Seitenzahl, Querverweis, Initiale, WordArt — sieben Mal dieselbe Sache.
Es ist kein Symbolproblem. Es ist ein Beschriftungsproblem.

Zweite Hälfte davon: **Lunivo zeigt keinen Schaltzustand.** In WPS sieht
man am Haken, ob das Lineal an ist. In Lunivo ist genau ein Symbol blau
hinterlegt; bei den übrigen sechs Schaltern der Gruppe *Anzeigen* ist von
außen nicht zu sehen, ob sie an sind.

## Was WPS hat und Lunivo nicht

| WPS | in Lunivo |
|---|---|
| Vollbildgröße | fehlt |
| Rahmen | fehlt |
| Tabellengitternetzlinien | fehlt |
| Fenster teilen | fehlt |
| Augenschutzmodus | ersetzt durch die Gruppe *Helligkeit* |
| Markup | steht in Lunivo unter Überprüfen, nicht unter Ansicht |

*Augenschutzmodus* ist kein Fehlen: WPS hat einen Knopf, Lunivo hat drei
(Wie das System · Immer hell · Immer dunkel). Das ist mehr, nicht
weniger — aber es ist nicht dasselbe, und deshalb steht es hier.

## Was Lunivo hat und WPS nicht

Gliederung · Vertikales Lineal · Textbegrenzungen · Seitenleiste
Schreibhilfe · Fensterliste · die ganze Gruppe *Helligkeit* · die ganze
Gruppe *Oberfläche* (Register anpassen, Symbol austauschen,
Benutzeroberfläche, Menüleiste, Symbolleisten, Vorlagen zurücksetzen)

Dazu ein Unterschied im Aufbau: **Lunivo beschriftet die Gruppen**
(DOKUMENTANSICHTEN · ANZEIGEN · ZOOM · FENSTER · HELLIGKEIT ·
OBERFLÄCHE), WPS nicht. Word macht es wie Lunivo.

## Zwei Fehler, die dabei aufgefallen sind

### 1. „Textbegrenzungen" steht zweimal im Band

In `oberflaeche/daten/register.js`, Gruppe *Anzeigen*:

    ['ecken', 'Textbegrenzungen', () => B.textbegrenzungen(), …]
    ['ecken', 'Textbegrenzungen', () => B.markenZeigen(),     …]

Gleiche Beschriftung, gleiches Symbol, **zwei verschiedene Befehle**.
Beide zeichnen die vier Ecken des Satzspiegels — einmal über die Klasse
`blatt--begrenzungen`, einmal über `.blatt__marken`. Es sind zwei
Umsetzungen derselben Sache, und im Band stehen sie nebeneinander.

Welche der beiden bleiben soll, entscheidet er — die eine ist vermutlich
älter als die andere, und das steht nirgends.

### 2. Der Haken zeigt den falschen Zustand

In `oberflaeche/js/programm.js` steht in der Tabelle `w.an` der Schlüssel
`textbegrenzungen` **zweimal**:

    textbegrenzungen: () => textbegrenzungen,   // Zeile 4025
    …
    textbegrenzungen: () => marken,             // Zeile 4032

In JavaScript gewinnt der letzte. Der Haken am Knopf *Textbegrenzungen*
zeigt deshalb nie, ob die Textbegrenzungen an sind, sondern immer, ob die
Marken an sind. Der erste Eintrag ist toter Code.

Das ist kein Ermessen — das ist ein Fehler. Er gehört behoben, sobald
entschieden ist, welcher der beiden Knöpfe aus Punkt 1 bleibt.

## Der Ansicht-Reiter in Lunivo, wie er heute ist

Aus `register.js` gelesen, in der Reihenfolge des Bandes:

| Gruppe | Knöpfe | beschriftet |
|---|---|---|
| Dokumentansichten | Drucklayout · Lesemodus · Zwei Seiten · Weblayout · Gliederung | 2 von 5 |
| Anzeigen | Lineal · Textbegrenzungen · Vertikales Lineal · Gitternetzlinien · Navigationsbereich · Textbegrenzungen · Seitenleiste Schreibhilfe | 0 von 7 |
| Zoom | Vergrößern · Verkleinern · 100 % · Seitenbreite · Eine Seite · Zoom | 2 von 6 |
| Fenster | Neues Fenster · Anordnen · Nebeneinander · Untereinander · Kacheln · Fensterliste | 2 von 6 |
| Helligkeit | Wie das System · Immer hell · Immer dunkel | 0 von 3 |
| Oberfläche | Register anpassen · Symbol austauschen · Benutzeroberfläche · Menüleiste · Symbolleisten · Vorlagen zurücksetzen | 1 von 6 |

In der Gruppe *Fenster* bietet die Klappe unter *Anordnen* dieselben drei
Befehle an, die daneben schon als eigene Knöpfe stehen: Nebeneinander,
Untereinander, Kacheln. Das ist kein Fehler, aber doppelt.

---

[← Zurück zum README](../README.md) ·
[Reiter für Reiter](reiter-abgleich.md) ·
[Was wirklich fehlt](was-fehlt-wirklich.md)
