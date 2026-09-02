<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="bilder/lunivo-office-dunkel.png">
    <img src="bilder/lunivo-office.png" width="420"
         alt="Lunivo-Office — eine Schreibfeder, deren Kopf eine Glühbirne ist, und darin wächst ein Trieb">
  </picture>
</p>

# Lunivo-Office

**Ein Raum für Worte.**

Ein Schreibprogramm wie LibreOffice Writer oder Word — mit einem Unterschied:
Die **Schreibhilfe** sitzt fest an der Seite und sucht die Fehler, die ein
Rechtschreibprüfer **nicht** finden kann.

    das / dass       seit / seid       wider / wieder
    „wir hat"  →  „wir haben"          „größer wie"  →  „größer als"
    fehlende Kommas vor weil, dass, wenn, aber
    zusammengetippte Wörter, doppelte Wörter, Satzanfänge

Gebaut für Menschen mit Legasthenie. Kein Konto, keine Anmeldung, kein
Internet nötig. Was geschrieben wird, bleibt auf dem eigenen Rechner.

![Lunivo-Office mit einem Brief im Blatt und der Schreibhilfe rechts an der Seite](bilder/uebersicht.png)

> Die Adresse auf GitHub bleibt `…/schreibprogramm` — eine neue würde jeden
> Link brechen, der schon irgendwo steht. Und wer nach „Schreibprogramm"
> sucht, soll es weiter finden.


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

* [**RICHTUNG.md**](RICHTUNG.md) — wohin das gehen soll, und was es *nicht* wird
* [MITMACHEN](CONTRIBUTING.md) — wie, im Einzelnen
* [Der Ton hier](CODE_OF_CONDUCT.md) — eine Seite statt fünf

## Warum noch ein Schreibprogramm?

Weil die vorhandenen an der falschen Stelle helfen. Ein Rechtschreibprüfer
findet Wörter, die es nicht gibt. Er findet nicht „das" statt „dass" — beide
Wörter gibt es ja. Genau daran scheitert man aber, wenn Schreiben schwerfällt.

Und weil die Prüfung hier **mit Absicht lückenhaft** ist. Regeln, die auch
richtige Sätze anmeckern würden, stehen nicht drin. Wer ohnehin unsicher ist,
den bringt ein falscher Alarm weiter vom Weg ab als eine übersehene Stelle.

## Was es kann

**Schreiben.** A4, A5, A3, Letter, Legal — hoch oder quer. Überschriften,
Titel, Untertitel, alle Schriften des Rechners mit Vorschau, Farben,
Zeilen- und Absatzabstände, Spalten, Silbentrennung, Zeilennummern.
Tabellen, Bilder, Diagramme, Formen, Formeln, Kopf- und Fußzeilen,
Fußnoten, Endnoten, Inhalts-, Abbildungs- und Stichwortverzeichnis,
Zitate mit Quellenverwaltung, Seriendruck, Umschläge, Etiketten.

**Schnellzugriff.** Unter dem Prüfen-Knopf stehen drei Marken — Wellen,
Vorhersage, AutoKorrektur. Grün heißt an, ein Klick schaltet. Sie lagen
vorher in *Extras ▸ Beim Schreiben*, wo sie niemand fand. Daneben führt
**Welche Hilfe wann?** (F6) auf die Seite, die alle sechs Stufen erklärt —
und dort lässt sich jede auch gleich umlegen oder auslösen.

**Prüfen.** Der Knopf *Prüfen* (F7) legt jeden Fund als Karte in die
Seitenleiste und zieht im Text eine Wellenlinie darunter. Rechtsklick auf
ein angestrichenes Wort zeigt die Vorschläge — wie in Word.

![Rechtsklick auf ein angestrichenes Wort: darüber steht die Erklärung, darunter der Vorschlag „glaube, dass“ zum Übernehmen](bilder/rechtsklick.png)

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

**Wortvorhersage.** Ab drei Buchstaben stehen passende Wörter zur Wahl.
Wiedererkennen ist leichter als Erinnern.

**Phonetische Suche.** Wer „kwalität" schreibt, meint *Qualität*; wer
„fileicht" schreibt, meint *vielleicht*. Ein Buchstabenabstand findet das
nicht — der Klang schon (Kölner Phonetik).

**KI, wenn man will.** Korrigieren, Umformulieren, Übersetzen — über Claude
im Netz oder über ein Modell auf dem eigenen Rechner (Ollama). Die Korrektur
richtet sich danach, **für wen** der Text ist: Ein Brief ans Amt wird anders
korrigiert als eine Nachricht an einen Freund.

**Speichern.** `.odt`, `.docx`, `.doc`, `.rtf`, `.fodt`, `.html`, `.txt`,
PDF und EPUB. Word-Dateien öffnen und wieder als Word speichern.

**Zwei Oberflächen.** *Ansicht ▸ Benutzeroberfläche* stellt zwischen
Symbolleisten (zwei Zeilen, alles sichtbar) und Registern (Reiter wie in
Word) um. Dieselben Befehle, anders sortiert.

Das Register hat acht Reiter — Datei, Start, Einfügen, Layout, Referenzen,
Überprüfen, Schreibhilfe, Ansicht — und einen neunten, der nur da ist, wenn
er etwas zu sagen hat: **Tabelle** erscheint, sobald der Zeiger in einer
Tabelle steht, und verschwindet wieder. Auf *Start* steht der
**Formatvorlagen-Katalog**: Er zeigt die Vorlage, statt sie zu benennen.
Wo eine Gruppe nicht alles zeigt, was es gibt, steht unten rechts ein
**Pfeil ⭨** zum vollen Dialog. Ein **Doppelklick auf den Reiter** klappt
das Band weg und wieder auf.

Im Register **tritt die Reiterzeile an die Stelle der Menüleiste** — sie
kommt nicht dazu. Beides übereinander fräße genau den Platz, den das
Register gewinnen soll. Das Menü bleibt über das Zeichen ☰ rechts in der
Reiterzeile erreichbar, oder über die Alt-Taste; Seriendruck, Makros und
die Verzeichnisse stehen nur dort. In der Symbolleisten-Ansicht lässt sich
die Menüleiste ebenfalls ausblenden. Symbolgröße und die Schrift der
Bedienung sind einstellbar — wer die Leisten nicht lesen kann, benutzt sie
nicht.

**Optionen** (F9). Wie im Writer: links ein Baum, rechts der Bereich.
Benutzerdaten, Ansicht, Schriftarten, Pfade, Sprache, Prüfung und KI,
Gedächtnis — und unter *Erweitert*, was zusätzlich geholt wurde und ob es
da ist. Unter *Extras ▸ Erweiterungsverwaltung* steht dasselbe noch einmal
als eigenes Fenster.

## So sieht es aus

Die Menüs sind nach Themen geordnet und haben Untermenüs, damit keine Liste
länger wird als der Bildschirm.

![Das Menü Format ist offen, daneben das Untermenü Schrift mit Fett, Kursiv, Schriftfarbe und Effekten](bilder/menues.png)

Die Schriftauswahl zeigt jede Schrift in sich selbst — oben die vier für
Fließtext, darunter alles, was auf dem Rechner liegt.

![Die Schriftliste mit Suchfeld; jeder Name ist in seiner eigenen Schrift gesetzt](bilder/schriften.png)

Hell oder dunkel, je nachdem, was den Augen bekommt. Das Blatt bleibt weiß —
Papier ist weiß.

![Dasselbe Fenster im dunklen Modus](bilder/dunkel.png)

Auf der Einstellungsseite stehen der Schlüssel für die KI, das Modell, der
Verbrauch und alles zur Darstellung.

![Die Einstellungsseite mit API-Schlüssel, KI-Modell, Verbrauch und Übersetzen](bilder/einstellungen.png)

## Starten

    ./starten.sh

Das legt beim ersten Mal auch den Menüeintrag an; danach steht
*Lunivo-Office* im Startmenü unter „Büro". Wer noch den alten Eintrag
*Schreibprogramm* hat: Der wird beim Start still mit weggeräumt, damit
nicht beide nebeneinander stehen.

Gebraucht wird GTK mit WebKit:

    sudo apt install python3-gi gir1.2-webkit2-4.1

## Was zusätzlich geholt wird

Zwei Dinge liegen **nicht** in diesem Verzeichnis, weil sie zu groß sind, und
werden bei Bedarf nach `~/.local/share/schreibprogramm/` gelegt — der
Ordner behält seinen alten Namen mit Absicht, denn dort liegt auch alles
Geschriebene und Gelernte:

| | wofür | Größe | nötig? |
|---|---|---|---|
| LibreOffice | Word-Dateien, PDF, EPUB | ~700 MB | nur dafür |
| [LanguageTool](https://languagetool.org/) | „Gründlich prüfen" | ~400 MB | nein, freiwillig |
| [Piper](https://github.com/rhasspy/piper) + Thorsten | eine Stimme, die nicht nach Maschine klingt | ~90 MB | nein, `./stimme-holen.sh` |

Ist LibreOffice im System installiert, genügt das auch. LanguageTool läuft
als **eigener Prozess** — seine LGPL-Lizenz berührt dieses Programm nicht.

Schreiben, Prüfen, Vorlesen und die ODF-Formate gehen ohne beides.

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

SmartArt in Word-Qualität, 3D-Modelle, eingebettete Tabellenkalkulation,
Design-Themes, Bildumfluss mit Ebenen, Endnoten-Querverweise nach APA im
vollen Umfang, Barrierefreiheitsprüfung über das Geprüfte hinaus,
Dokumentschutz mit Kennwort, Gliederungsansicht zum Verschieben,
Fenster teilen mit Synchronscrollen.

Bei den meisten wäre der Aufwand groß und der Nutzen für einen Brief gering.

## Herkunft

**Wie das alles entstanden ist**, steht in
[ENTSTEHUNG.md](ENTSTEHUNG.md) — vom zu kleinen Textfeld auf dem Handy bis
zu diesem Programm, aufgeschrieben von dem, der es gebaut hat.

Die Prüfung und der Wortschatz stammen aus der
[Schreibhilfe](https://github.com/kaysiebke-cell/schreibhilfe) und sind dort
über viele Fassungen gewachsen. Sie liegen hier als eigene Kopie: Dieses
Programm ist eigenständig und braucht jenes Projekt nicht, um zu laufen.

Die Wörterliste (`daten/woerter.txt`, 355.321 Wörter) ist über viele Sitzungen
selbst aufgebaut worden. Sie stammt aus keiner fremden Quelle und steht
deshalb wie der übrige Code unter MIT.

## Aufbau

    index.html           die Oberfläche
    css/programm.css     das Aussehen
    js/programm.js       Menüs, Werkzeuge, Seitenleiste, Statuszeile
    js/dokument.js       das Dokument: lesen, zeigen, ersetzen, formatieren
    js/dateien.js        öffnen und speichern
    js/pruefung.js       die Prüfung, Phonetik, Wortvorhersage
    js/ki.js             Claude und Ollama, Gedächtnis, Sicherung
    js/einstellungen.js  die Einstellungsseite
    ENTSTEHUNG.md        wie es dazu kam
    RICHTUNG.md          wohin das Projekt geht, und was es nicht wird
    CONTRIBUTING.md      wie man mitmacht
    daten/regeln.js      der Wortschatz der Prüfung
    daten/woerter.txt    355.321 deutsche Wörter
    start.py             Fenster, Server, Schriften, LibreOffice, Vorlesen
    starten.sh           startet es und schreibt den Menüeintrag
    stimme-holen.sh      holt Piper und die Stimme „Thorsten" (freiwillig)

Ausführlicher steht alles in [LIESMICH.md](LIESMICH.md).

## Lizenz

[MIT](LICENSE) — benutzen, ändern und weitergeben ist erlaubt, auch
gewerblich. Der Urhebervermerk muss mitgehen.

LanguageTool und LibreOffice stehen unter eigenen Lizenzen (LGPL-2.1 und
MPL-2.0) und werden als eigene Prozesse aufgerufen, nicht eingebunden.
