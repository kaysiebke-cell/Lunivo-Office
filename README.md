# Schreibprogramm

Ein Schreibprogramm wie LibreOffice Writer oder Word — mit einem Unterschied:
Die **Schreibhilfe** sitzt fest an der Seite und sucht die Fehler, die ein
Rechtschreibprüfer **nicht** finden kann.

    das / dass       seit / seid       wider / wieder
    „wir hat"  →  „wir haben"          „größer wie"  →  „größer als"
    fehlende Kommas vor weil, dass, wenn, aber
    zusammengetippte Wörter, doppelte Wörter, Satzanfänge

Gebaut für Menschen mit Legasthenie. Kein Konto, keine Anmeldung, kein
Internet nötig. Was geschrieben wird, bleibt auf dem eigenen Rechner.

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

**Prüfen.** Der Knopf *Prüfen* (F7) legt jeden Fund als Karte in die
Seitenleiste und zieht im Text eine Wellenlinie darunter. Rechtsklick auf
ein angestrichenes Wort zeigt die Vorschläge — wie in Word.

**Vorlesen** (F4). Über einen Fehler liest das Auge hinweg; das Ohr stolpert
darüber. 60 deutsche Stimmen, Tempo einstellbar.

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

## Starten

    ./starten.sh

Das legt beim ersten Mal auch den Menüeintrag an; danach steht
*Schreibprogramm* im Startmenü unter „Büro".

Gebraucht wird GTK mit WebKit:

    sudo apt install python3-gi gir1.2-webkit2-4.1

## Was zusätzlich geholt wird

Zwei Dinge liegen **nicht** in diesem Verzeichnis, weil sie zu groß sind, und
werden bei Bedarf nach `~/.local/share/schreibprogramm/` gelegt:

| | wofür | Größe | nötig? |
|---|---|---|---|
| LibreOffice | Word-Dateien, PDF, EPUB | ~700 MB | nur dafür |
| [LanguageTool](https://languagetool.org/) | „Gründlich prüfen" | ~400 MB | nein, freiwillig |

Ist LibreOffice im System installiert, genügt das auch. LanguageTool läuft
als **eigener Prozess** — seine LGPL-Lizenz berührt dieses Programm nicht.

Schreiben, Prüfen, Vorlesen und die ODF-Formate gehen ohne beides.

## Was nicht drin ist

SmartArt in Word-Qualität, 3D-Modelle, eingebettete Tabellenkalkulation,
Design-Themes, Bildumfluss mit Ebenen, Endnoten-Querverweise nach APA im
vollen Umfang, Barrierefreiheitsprüfung über das Geprüfte hinaus,
Dokumentschutz mit Kennwort, Gliederungsansicht zum Verschieben,
Fenster teilen mit Synchronscrollen.

Bei den meisten wäre der Aufwand groß und der Nutzen für einen Brief gering.

## Herkunft

Die Prüfung und der Wortschatz stammen aus der
[Schreibhilfe](https://github.com/kaysiebke-cell/schreibhilfe) und sind dort
über viele Fassungen gewachsen. Sie liegen hier als eigene Kopie: Dieses
Programm ist eigenständig und braucht jenes Projekt nicht, um zu laufen.

## Aufbau

    index.html           die Oberfläche
    css/programm.css     das Aussehen
    js/programm.js       Menüs, Werkzeuge, Seitenleiste, Statuszeile
    js/dokument.js       das Dokument: lesen, zeigen, ersetzen, formatieren
    js/dateien.js        öffnen und speichern
    js/pruefung.js       die Prüfung, Phonetik, Wortvorhersage
    js/ki.js             Claude und Ollama, Gedächtnis, Sicherung
    js/einstellungen.js  die Einstellungsseite
    daten/regeln.js      der Wortschatz der Prüfung
    daten/woerter.txt    355.321 deutsche Wörter
    start.py             Fenster, Server, Schriften, LibreOffice, Vorlesen
    starten.sh           startet es und schreibt den Menüeintrag

Ausführlicher steht alles in [LIESMICH.md](LIESMICH.md).

## Lizenz

[MIT](LICENSE) — benutzen, ändern und weitergeben ist erlaubt, auch
gewerblich. Der Urhebervermerk muss mitgehen.

LanguageTool und LibreOffice stehen unter eigenen Lizenzen (LGPL-2.1 und
MPL-2.0) und werden als eigene Prozesse aufgerufen, nicht eingebunden.
