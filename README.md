<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/images/lunivo-office-dunkel.png">
    <img src="assets/images/lunivo-office.png"
         style="max-width: 100%; height: auto;"
         alt="Lunivo-Office Logo">
  </picture>
<p align="center">
  Was geschrieben wird, bleibt auf diesem Rechner.<br>
  Nichts geht hinaus, ohne dass du es selbst schickst.
</p>

<hr>

Ein Schreibprogramm wie LibreOffice Writer oder Word — mit einem Unterschied:
Die **Schreibhilfe** sitzt fest an der Seite und sucht die Fehler, die ein
Rechtschreibprüfer **nicht** finden kann.

```text
das / dass       seit / seid       wider / wieder
„wir hat"  →  „wir haben"          „größer wie"  →  „größer als"
fehlende Kommas vor weil, dass, wenn, aber
zusammengetippte Wörter, doppelte Wörter, Satzanfänge
```

Nicht *für* Menschen mit Legasthenie gebaut, sondern *von* einem —
[wie es dazu kam](docs/ENTSTEHUNG.md).
Kein Konto, keine Anmeldung, kein Internet nötig.

![Lunivo Writer mit einem Widerspruchsbrief im Blatt, dem Menüband oben und der Schreibhilfe rechts an der Seite: Ein Tippfehler („wiederspreche“) ist unterschlängelt und steht als Karte mit Ändern und Lassen in der Seitenleiste](assets/images/qt-uebersicht.png)

## Mach mit

Dieses Projekt sucht Leute — **nicht in erster Linie Programmierer.**

Wenn dir Schreiben schwerfällt, bist du hier die wichtigste Person. Nicht
weil das nett klingt, sondern weil niemand ein Werkzeug bauen kann für eine
Not, von der er nichts weiß. Ein Satz darüber, woran du hängenbleibst, ist
mehr wert als der schönste Quelltext.

> [**Erzähl, woran du hängenbleibst**](../../issues/new?template=erfahrung.yml)
> · [Etwas geht nicht](../../issues/new?template=fehler.yml)
> · [Etwas fehlt](../../issues/new?template=wunsch.yml)
> · [Reden statt melden](../../discussions)

**Rechtschreibung ist dabei egal.** Wirklich — ausgerechnet hier wird
niemand darauf angesprochen.

Gebraucht wird außerdem: Regeln für die Prüfung (samt der Frage, wann sie
falsch wären), Ausprobieren auf anderen Linux-Systemen, ein Flatpak oder
AppImage, und andere Sprachen von Leuten, die sie sprechen.

## Deine Erfahrung zählt

Du möchtest erst einmal lesen, was hinter Lunivo-Office steckt, Fragen
stellen oder deine Erfahrungen teilen?

Dann komm in die [**GitHub Discussions**](../../discussions).

Dort kannst du erzählen, was dir beim Schreiben schwerfällt, Fragen stellen,
Vorschläge machen oder einfach mit anderen über das Projekt sprechen.

**Besonders wichtig:** Du musst dafür kein Programmierer sein. Und deine
Rechtschreibung spielt hier keine Rolle.

* [**RICHTUNG.md**](docs/RICHTUNG.md) — wohin das gehen soll, und was es *nicht* wird
* [MITMACHEN](.github/CONTRIBUTING.md) — wie, im Einzelnen
* [Der Ton hier](.github/CODE_OF_CONDUCT.md) — eine Seite statt fünf

## Warum noch ein Schreibprogramm?

Weil die vorhandenen an der falschen Stelle helfen. Ein Rechtschreibprüfer
findet Wörter, die es nicht gibt. Er findet nicht „das" statt „dass" — beide
Wörter gibt es ja. Genau daran scheitert man aber, wenn Schreiben schwerfällt.

Und weil die Prüfung hier **mit Absicht lückenhaft** ist. Regeln, die auch
richtige Sätze anmeckern würden, stehen nicht drin. Wer ohnehin unsicher ist,
den bringt ein falscher Alarm weiter vom Weg ab als eine übersehene Stelle.

Vor allem aber, weil das Problem bei den Wörtern nicht aufhört. Wer auf seine
Rechtschreibung angesprochen wird, wo es um etwas ganz anderes ging, schreibt
irgendwann lieber nichts mehr. Ein Text, der wegen seiner Form nicht gelesen
wird, kommt nicht an — gleich, was drinsteht.

Deshalb ist dieses Programm nicht *für* Menschen mit Legasthenie gebaut,
sondern *von* einem. Das ist kein Werbespruch, sondern der Grund, warum die
Vorschlagsleiste von selbst erscheint, warum auf jeder Karte ein Ohr sitzt
und warum unter *Neu aus Vorlage* fertige Gerüste liegen.

> **Wie das alles entstanden ist**, steht in
> [ENTSTEHUNG.md](docs/ENTSTEHUNG.md) — vom zu kleinen Textfeld auf dem
> Handy bis hierher, aufgeschrieben von dem, der es gebaut hat.

## Was es kann

**Für Menschen, denen Lesen und Schreiben schwerfallen.** Die Grundschrift
ist OpenDyslexic, die Lesehilfe sitzt im Reiter *Schreibhilfe* — dort steht auch
alles andere beieinander, was dabei hilft: farbige Silben zum Einstellen, Vorlesen
(**F4**), Prüfen, KI — statt über fünf Reiter verteilt.

**Prüfung ohne Internet.** 355.322 Wörter und eigene Regeln finden, was ein
Rechtschreibprüfer nicht findet — das/dass, wider/wieder, Kommas. Die KI ist
freiwillig und braucht einen eigenen Schlüssel; ohne sie läuft alles Übrige.

**Ein vollständiges Schreibprogramm.** Neun Reiter nach dem Vorbild des
WPS Writer — *Datei* öffnet als Backstage-Ansicht wie bei ONLYOFFICE —, zwei
Oberflächen zur Wahl, Formatvorlagen, Tabellen, Spalten (live auf der Seite),
Fuß- und Endnoten, Kommentare als Sprechblasen, Formularfelder, Kopf- und
Fußzeilen, Seriendruck, Druckvorschau, PDF-Export. Die Optionen haben 17 Seiten
in drei Zweigen: *Leichter lesen*, *Wie im WPS Writer* und *Nur bei Lunivo*.
Das Hauptformat ist **DOCX**.

**Was geschrieben wird, bleibt hier.** Kein Konto, keine Cloud, kein
Mitlesen. Die Einstellungen liegen als lesbare Datei unter
`~/.config/Lunivo/Lunivo Writer.conf`.

---

## Die Dokumentation

Der README sagt, was es ist. Was es im Einzelnen tut, steht in den fünf
Dateien darunter — sonst wäre er dreißig Seiten lang und niemand fände
darin, was er sucht.

|                                                                | Worum es geht                                       |
| -------------------------------------------------------------- | --------------------------------------------------- |
| 1 · [Lesen und Schreiben](docs/lesen-und-schreiben.md)         | Lesehilfe, Schriften für Legasthenie, Vorlesen      |
| 2 · [Prüfung, Vorhersage und KI](docs/pruefung-und-ki.md)      | Was gefunden wird, und was die KI dabei tut         |
| 3 · [Schreiben und Dokumente](docs/schreiben-und-dokumente.md) | Das Blatt, Vorlagen, Speichern, Drucken             |
| 4 · [Die Oberfläche](docs/oberflaeche.md)                      | Band und Leisten, Lineale, Formatvorlagen, Anpassen |
| 5 · [Die Einstellungen](docs/einstellungen.md)                 | Das Optionen-Fenster, Sprachen, Kennwort            |

Dazu im Programm selbst: **☰ Menü → Hilfe → Handbuch** und **Datei → Hilfe**
(Tastenkürzel) — die kurze Einführung für die Qt-Oberfläche.

| Weiteres                                            |                                                   |
| --------------------------------------------------- | ------------------------------------------------- |
| [Was zusätzlich geholt wird](docs/erweiterungen.md) | LibreOffice, LanguageTool, Stimmen, Schriften     |
| [Der Aufbau des Projekts](docs/projektaufbau.md)    | Welche Datei was tut                              |
| [Die lange Fassung](docs/LIESMICH.md)               | Alles ausführlich, auf Deutsch                    |
| [Wie es entstanden ist](docs/ENTSTEHUNG.md)         | Die Geschichte dahinter                           |
| [Wohin es geht](docs/RICHTUNG.md)                   | Was noch kommen soll                              |
| [Der Aufbau des Bandes](docs/aufbau-band.md)        | Alle Reiter, mit Tabelle „wo finde ich was" (Stand der früheren Fassung) |
| [Der Aufbau der Optionen](docs/aufbau-optionen.md)  | Alle Seiten und Felder, ebenso                    |
| [Der Ist-Stand am Stück](docs/aufbau-ist-stand.md)  | Bänder und Optionen zusammen (Stand der früheren Fassung) |
| [Stand der Qt-Fassung (Bericht)](docs/BERICHT.md) | Was geht, was nicht, was ungetestet ist |
| [Menüstruktur-Abgleich](docs/MENUESTRUKTUR.md) | Ihre 12 Bereiche, Punkt für Punkt: da, teilweise, fehlt |
| [Prüfbogen-Abgleich](docs/PRUEFBOGEN.md) | 415 Punkte, jeder mit Beleg |
| [Aufbau der Qt-Fassung](docs/README.md) | Ordner und Zuständigkeiten |
| [Installation](docs/INSTALLATION.md) | Pakete und optionale Bausteine |

Diese drei wurden aus dem Programm **erzeugt**, nicht geschrieben, und halten
den Stand der früheren Fassung fest. Wie die Qt-Fassung heute dasteht —
Reiter für Reiter gegen den Prüfbogen —, steht in [PRUEFBOGEN.md](docs/PRUEFBOGEN.md)
und [BERICHT.md](docs/BERICHT.md); beides wird mit `werkzeug/pruefbogen-*.py` aus dem Code abgeglichen.

## So sieht es aus

Die Bilder dieses Abschnitts zeigen die **Qt-Oberfläche** (aufgenommen mit
`python3 werkzeug/bildschirmfotos.py`, ohne Bildschirm erzeugt).

Das Fenster im Überblick — hell und dunkel: oben die Reiter, darunter das Band, in der Mitte das
Blatt, rechts die Schreibhilfe mit der Karte zum Fund.

![Das Fenster im hellen Thema](assets/images/qt-uebersicht.png)

![Dasselbe Fenster im dunklen Thema](assets/images/qt-uebersicht-dunkel.png)

Der Reiter **Schreibhilfe** trägt alles, was das Lesen und Schreiben erleichtert — Lesehilfe, farbige Silben,
Prüfen, Vorlesen, Sprache, Bausteine und die KI —, im dunklen Thema genauso.

![Der Reiter Schreibhilfe mit den Gruppen Lesen, Prüfen, Beim Schreiben, Vorlesen, Sprache, Bausteine, KI-Schreibwerkzeuge und KI](assets/images/qt-schreibhilfe.png)

![Der Reiter Schreibhilfe im dunklen Thema](assets/images/qt-schreibhilfe-dunkel.png)

**Datei** ist eine Backstage-Ansicht: links die Befehle, rechts die Seite dazu — hier *Info* mit Statistik,
Verfasser und Titel.

![Die Backstage-Ansicht des Reiters Datei mit der Seite Info](assets/images/qt-datei.png)

![Die Backstage-Ansicht im dunklen Thema](assets/images/qt-datei-dunkel.png)

**Spalten** stehen live auf der Seite, beim Schreiben — hier zwei Spalten auf einer A4-Seite.

![Eine A4-Seite mit zwei Spalten im Reiter Seitenlayout](assets/images/qt-spalten.png)

Die **Optionen** (**F9**) haben drei Zweige. Jede Wahl der Lesehilfe wirkt sofort auf dem Blatt.

![Die Optionen mit der Seite Lesehilfe: Papierton, Buchstaben- und Wortabstand, Zeilenfokus, Vorlesen, farbige Silben und Silbentrennung; links der Baum mit den drei Zweigen](assets/images/qt-optionen-lesehilfe.png)

Unter **Schriftarten** stehen die Leseschriften.

![Die Seite Schriftarten der Optionen](assets/images/qt-optionen-schriften.png)

### Die frühere Oberfläche (Bildschirmfotos der Fassung davor)

Der Reiter **Schreibhilfe** trägt alles, was das Lesen und Schreiben
erleichtert. Der Text steht in OpenDyslexic.

![Das Fenster mit dem offenen Reiter Schreibhilfe: die Gruppen Lesen, Prüfen, Beim Schreiben, Vorlesen, Sprache, KI und Anzeigen, rechts die Seitenleiste](assets/images/uebersicht.png)

Die **Lesehilfe** ist die erste Seite der Optionen (**F9**). Jede Wahl
wirkt sofort auf dem Blatt — kein „Übernehmen", kein Fenster, das über dem
Text liegt, den man beurteilen will.

![Die Optionen mit der offenen Seite Lesehilfe: Papierton, Buchstabenabstand, Wortabstand, Zeilenluft, Zeilenfokus und Vorlesen; links der Baum mit den drei Zweigen](assets/images/lesehilfe.png)

Unter **Schriftarten** stehen die drei Leseschriften als Knöpfe, jede in
ihrer eigenen Schrift — man muss ihren Namen nicht kennen.

![Die Seite Schriftarten mit der Schriftwahl und den drei Knöpfen OpenDyslexic, Lexend und Atkinson Hyperlegible, jeder in seiner eigenen Schrift](assets/images/schriften.png)

Die Optionen übernehmen die Seiten des WPS Writer, zweispaltig
und kompakt wie dort — hier die Seite *Ansicht*.

![Die Seite Ansicht der Optionen, zweispaltig: Anzeigen, Druckoptionen, Formatierungszeichen, Menübandoptionen und Darstellung](assets/images/einstellungen.png)

Wer die Reiter aus Word gewohnt ist, findet sie unter *Ansicht ▸
Darstellung ▸ Benutzeroberfläche*. Über dem Blatt liegt das Lineal mit den
Einzugsmarken, links das senkrechte.

![Das Register mit dem Reiter Start: Zwischenablage, Schriftart, Absatz, Absatzlayout und Bearbeiten](assets/images/register.png)

Hell oder dunkel, je nachdem, was den Augen bekommt.

![Dasselbe Fenster im hellen Thema](assets/images/hell.png)

## Starten

Lunivo Writer ist eine **native Qt-Anwendung** (Python 3 + PySide6) — ohne Browser, ohne WebKit.

```text
sudo apt install python3 python3-venv libxcb-cursor0 libegl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0
./starten-qt.sh
```

Beim ersten Start legt das Skript eine eigene Umgebung (`.venv`) an und installiert PySide6 und die übrigen Pakete;
`./starten-qt.sh --eintrag` legt zusätzlich einen Menüeintrag an. Genaueres und optionale Teile:
[docs/INSTALLATION.md](docs/INSTALLATION.md). Direkt aus dem Projektordner geht auch `python3 main.py`.

## Eine Hilfe, kein Ersatz

> Lunivo-Office ist eine Hilfe und kein Ersatz für eine Kontrolle durch
> eine andere Person. Es kann nicht garantieren, dass der Text oder sein Inhalt
> am Ende vollständig korrekt ist.
>
> Gerade für Menschen mit Legasthenie ist eine zusätzliche Kontrolle durch eine
> zweite Person wichtig. Eigene Fehler werden beim späteren Lesen nicht immer
> erkannt, weil das Gehirn das Geschriebene teilweise so wahrnimmt, wie es
> gemeint war.

Deshalb gibt es *Vorlesen* (F4): Über einen Fehler liest das Auge hinweg, das
Ohr stolpert darüber. Es ersetzt die zweite Person nicht — es kommt ihr nur am
nächsten, wenn gerade niemand da ist.

## Was nicht drin ist

SmartArt als echtes Word-Diagramm (Lunivo-SmartArt ist ein bearbeitbares Bild), 3D-Modelle, eingebettete Tabellenkalkulation,
Design-Themes, Bildumfluss mit Ebenen, Endnoten-Querverweise nach APA im
vollen Umfang, Barrierefreiheitsprüfung über das Geprüfte hinaus,
Gliederungsansicht zum Verschieben,
Fenster teilen mit Synchronscrollen.

Bei den meisten wäre der Aufwand groß und der Nutzen für einen Brief gering.

## Herkunft

Wie das alles entstanden ist, steht in
[ENTSTEHUNG.md](docs/ENTSTEHUNG.md) — siehe oben.

Die Prüfung und der Wortschatz stammen aus der
[Schreibhilfe](https://github.com/kaysiebke-cell/schreibhilfe) und sind dort
über viele Fassungen gewachsen. Sie liegen hier als eigene Kopie: Dieses
Programm ist eigenständig und braucht jenes Projekt nicht, um zu laufen.

Die Wörterliste (`src/lunivo_writer/resources/daten/woerter.txt`, 355.324 Wörter) ist über viele Sitzungen
selbst aufgebaut worden. Sie stammt aus keiner fremden Quelle und steht
deshalb wie der übrige Code unter MIT.

## Lizenz

[MIT](LICENSE) — benutzen, ändern und weitergeben ist erlaubt, auch
gewerblich. Der Urhebervermerk muss mitgehen.

LanguageTool und LibreOffice stehen unter eigenen Lizenzen (LGPL-2.1 und
MPL-2.0) und werden als eigene Prozesse aufgerufen, nicht eingebunden.

Die Zeichnungen der Knöpfe stammen aus den
[Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons)
(Microsoft, MIT; Lizenztext in [assets/icons/fluent/LIZENZ.txt](assets/icons/fluent/LIZENZ.txt))
und zum Teil aus [Lucide](https://lucide.dev) (ISC; Lizenztext in
[docs/LIZENZ-LUCIDE.txt](docs/LIZENZ-LUCIDE.txt)).
Ein paar sind von Hand gezeichnet — Kopfzeile, Fußzeile, Seitenzahl,
Textbegrenzungen: die kennt nur ein Schreibprogramm.

