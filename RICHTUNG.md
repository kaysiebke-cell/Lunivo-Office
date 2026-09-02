# Wohin das gehen soll

Dieses Programm wird kein zweites Word. Es gibt Word, es gibt LibreOffice,
und beide sind besser darin, Word zu sein, als es dieses Projekt je wäre.

Es gibt aber etwas, das beide nicht tun.

Wie es dazu kam, steht in [ENTSTEHUNG.md](ENTSTEHUNG.md).

## Das Problem

Ein Rechtschreibprüfer findet Wörter, die es nicht gibt. Er findet nicht
„das" statt „dass" — beide Wörter gibt es ja. Er findet nicht „wir hat",
nicht das fehlende Komma vor „weil", nicht „größer wie".

Genau daran scheitert man aber, wenn Schreiben schwerfällt.

Wer Legasthenie hat, verschreibt sich außerdem selten um einen Buchstaben.
Er schreibt, wie er hört: „kwalität", „fileicht", „ferzeihung". Von
„kwalität" zu „Qualität" sind es drei Änderungen — für jede
Tippfehlersuche zu weit. Über den Klang ist es dasselbe Wort.

## Die Richtung

**1. Die Hilfe steht neben dem Text, nicht in einem Menü.**
Jeder Fund ist eine Karte mit Erklärung. Nichts ändert sich von allein.
Wer nachlesen will, warum, findet es dort — nicht in einer Hilfe-Datei.

**2. Lieber eine Lücke als ein falscher Alarm.**
Regeln, die auch richtige Sätze anmeckern würden, kommen nicht hinein.
Wer ohnehin unsicher ist, den bringt ein falscher Alarm weiter vom Weg ab
als eine übersehene Stelle. Das ist der wichtigste Satz auf dieser Seite,
und er kostet Funde. Mit Absicht.

**3. Es läuft ohne Konto, ohne Anmeldung, ohne Internet.**
Was geschrieben wird, bleibt auf dem Rechner. Die KI ist freiwillig,
kostet Geld und wird ausdrücklich angetippt — oder man nimmt ein Modell
auf dem eigenen Rechner und zahlt gar nichts.

**4. Deutsch zuerst.**
Nicht aus Prinzip, sondern weil die Prüfung an der Sprache hängt: Die
Kölner Phonetik ist fürs Deutsche gemacht, das/dass gibt es im Englischen
nicht. Andere Sprachen sind willkommen — aber als eigene Arbeit von
jemandem, der sie spricht, nicht als Übersetzung dieser Regeln.

**5. Gebaut von jemandem, der es braucht.**
Nicht für Betroffene, sondern von einem. Das ist kein Werbespruch, das
ist der Grund, warum die Vorschlagsleiste von selbst erscheint und warum
„Alles Eindeutige übernehmen" existiert.

## Was es nicht wird

* Kein Abo, keine Anmeldung, keine Datensammlung.
* Kein Cloud-Speicher. Die Datei liegt, wo du sie hinlegst.
* Keine Lernstands-Auswertung, keine Statistik über deine Fehler.
* Keine Bevormundung: Nichts wird automatisch geändert.
* Kein Nachbau von SmartArt, 3D-Modellen oder eingebetteter
  Tabellenkalkulation. Der Aufwand wäre groß, der Nutzen für einen Brief
  gering.

## Woran gerade gearbeitet wird

Der Stand ändert sich; das hier ist die Richtung, nicht der Plan.

| | |
|---|---|
| **Prüfung** | mehr Regeln für das, was ein Prüfer nicht findet — jede einzeln gemessen gegen falsche Alarme |
| **Klang** | die Kölner Phonetik trifft „kwalität", aber noch nicht jede Verwechslung |
| **Hauptwörter** | die Wortliste kennt keine Großschreibung; „bescheid" wird nicht zu „Bescheid" |
| **Vorlesen** | läuft; die Stimmen liegen außerhalb, weil sie 90 MB wiegen |
| **Register** | die Ribbon-Ansicht steht, kontextabhängige Reiter erst für Tabellen |
| **Verpacken** | es gibt kein Flatpak, kein AppImage, kein `.deb` — nur `starten.sh` |

## Wenn du das hier liest und etwas beitragen willst

Steht in [MITMACHEN](CONTRIBUTING.md). Die kürzeste Antwort: **Erzähl,
woran du hängengeblieben bist.** Ein Satz darüber, was dich beim Schreiben
aufhält, ist mehr wert als der schönste Quelltext — weil niemand ein
Werkzeug bauen kann für eine Not, von der er nichts weiß.
