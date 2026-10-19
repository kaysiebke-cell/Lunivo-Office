# Mitmachen

Dieses Projekt sucht Leute. Nicht in erster Linie Programmierer.

Wohin es soll, steht in [RICHTUNG.md](../doku/RICHTUNG.md). Wer etwas vorschlägt,
sollte die eine Seite gelesen haben — dann reden wir über dasselbe.

## Am meisten hilft: erzählen, woran du hängenbleibst

Wenn dir Schreiben schwerfällt, bist du hier die wichtigste Person. Nicht
weil das nett klingt, sondern weil niemand ein Werkzeug bauen kann für eine
Not, von der er nichts weiß.

Ein Satz reicht:

> „Ich weiß nie, ob es das oder dass heißt, und der Kasten erklärt es mir
> zwar, aber ich verstehe die Erklärung nicht."

> „Ich schreibe Briefe ans Amt und traue mich nicht, sie abzuschicken."

> „Die Vorschläge kommen zu spät, ich habe das Wort da schon dreimal
> falsch getippt."

Dafür gibt es die Vorlage **„Wie es sich anfühlt"** unter *Issues ▸ New
issue*. Du brauchst keinen Fachausdruck und keinen Screenshot. Schreib es,
wie es dir einfällt — Rechtschreibung egal, das ist hier wirklich egal.

## Was sonst gebraucht wird

**Regeln für die Prüfung.** Kennst du eine Verwechslung, die ein
Rechtschreibprüfer nicht findet? „seit/seid", „wider/wieder", „größer
wie" sind drin. Was fehlt? Wichtig ist dabei der zweite Teil der Frage:
*Wann wäre die Regel falsch?* Eine Regel, die auch richtige Sätze
anmeckert, kommt nicht hinein — siehe RICHTUNG.md, Punkt 2.

**Ausprobieren auf anderen Rechnern.** Es ist auf Linux Mint gebaut und
läuft dort. Auf Fedora? Auf Arch? Mit Wayland? Ohne PulseAudio? Jede
Rückmeldung „bei mir startet es nicht, hier ist die Fehlermeldung" ist
brauchbar.

**Verpacken.** Es gibt kein Flatpak, kein AppImage, kein `.deb`. Wer so
etwas kann, hilft damit allen, die `./starten.sh` nicht zumutbar finden.

**Schriften und Lesbarkeit.** Die Bedienung lässt sich größer stellen, das
Blatt auch. Ob das reicht, weiß ich nicht — ich sehe mit meinen Augen.

**Andere Sprachen.** Als eigene Arbeit von jemandem, der die Sprache
spricht. Eine Übersetzung der deutschen Regeln wäre wertlos: „das/dass"
gibt es im Englischen nicht.

## Wenn du Quelltext beisteuern willst

Der Code ist auf Deutsch geschrieben — Funktionen, Variablen, Kommentare.
Das ist kein Spleen: Wer die Prüfung ändert, muss über deutsche Grammatik
nachdenken, und dabei stört ein englischer Bezeichner.

Drei Bitten:

1. **Erst ein Issue, dann der Code.** Sonst baust du vielleicht etwas, das
   gegen die Richtung geht, und wir werfen beide Arbeit weg.
2. **Kommentare erklären das Warum, nicht das Was.** `i++ // erhöht i` hilft
   niemandem. `// Ab dem zweiten Zeichen, sonst bleiben „ambesten" und
   „esgibt" liegen` schon.
3. **Keine neuen Abhängigkeiten ohne Grund.** Das Programm ist HTML, CSS,
   JavaScript und Python — nichts wird nachgeladen, nichts gebaut. Wer das
   ändert, sollte einen guten Grund nennen.

Es gibt keinen Testlauf und keine Formatvorschrift. Prüf, ob es tut, was du
willst, und ob es das Übrige nicht kaputt macht.

## Der Ton hier

Kurz: Man kann über eine Sache streiten, ohne über den Menschen zu reden.

Wer hier schreibt, hat womöglich Mühe damit. Rechtschreibung, Grammatik und
Form spielen in Issues und Diskussionen **keine Rolle** — das ausgerechnet
in diesem Projekt zum Thema zu machen wäre absurd. Wer jemanden deswegen
anspricht, ist hier falsch.

Ausführlicher in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Lizenz

Alles steht unter [MIT](../LICENSE). Was du beisteuerst, steht danach auch
darunter — benutzbar, änderbar, weitergebbar, auch gewerblich.
