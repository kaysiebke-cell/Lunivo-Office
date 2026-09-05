# Funktionen

**Schreiben.** A4, A5, A3, Letter, Legal — hoch oder quer. Überschriften,
Titel, Untertitel, alle Schriften des Rechners mit Vorschau, Farben,
Zeilen- und Absatzabstände, Spalten, Silbentrennung, Zeilennummern.
Tabellen, Bilder, Diagramme, Formen, Formeln, Kopf- und Fußzeilen,
Fußnoten, Endnoten, Inhalts-, Abbildungs- und Stichwortverzeichnis,
Zitate mit Quellenverwaltung, Seriendruck, Umschläge, Etiketten.

**Nicht vor dem leeren Blatt stehen.** *Datei ▸ Neu aus Vorlage* legt alle
Vorlagen als Blätter nebeneinander, mit Suchfeld — so, wie man es aus Word
kennt. Zehn Gerüste sind dabei: Brief, Brief an eine Behörde, Widerspruch,
Bewerbung, Lebenslauf, Krankmeldung, Kündigung, Rechnung, Einladung,
Protokoll.

Darin steht **kein fertiger Text** — nur der Aufbau nach DIN 5008 und in
jeder Lücke ein Wort, das sagt, was dort hinkommt: `«Aktenzeichen des
Bescheids»`. Tab springt zur nächsten Lücke, Tippen ersetzt sie, gedruckt
wird sie nicht. Wer seine Anschrift einmal hinterlegt hat, findet sie samt
Ort und heutigem Datum schon oben stehen.

Denn wer an einem Behördenbrief scheitert, scheitert selten am Schreiben.
Er scheitert an einer Form, die man kennen muss und nirgends erklärt
bekommt.

Die Gerüste werden **nicht** in `~/Vorlagen` geschrieben — der Ordner
gehört dem Menschen. Was dort liegt, steht im zweiten Reiter daneben.

**Schnellzugriff.** Unter dem Prüfen-Knopf stehen drei Marken — Wellen,
Vorhersage, AutoKorrektur. Grün heißt an, ein Klick schaltet. Sie lagen
vorher in *Extras ▸ Beim Schreiben*, wo sie niemand fand. Daneben führt
**Welche Hilfe wann?** (F6) auf die Seite, die alle sechs Stufen erklärt —
und dort lässt sich jede auch gleich umlegen oder auslösen.

**Prüfen.** Der Knopf *Prüfen* (F7) legt jeden Fund als Karte in die
Seitenleiste und zieht im Text eine Wellenlinie darunter. Rechtsklick auf
ein angestrichenes Wort zeigt die Vorschläge — wie in Word. Auf jeder Karte
steht ein **Ohr**: Es liest den Vorschlag samt Begründung vor. Wer zwischen
„das" und „dass" unsicher ist, hört den Unterschied oft schneller, als er
ihn sieht.

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

**Lesehilfe** (*Ansicht ▸ Lesehilfe*). Was in jedem Ratgeber zu Legasthenie
oben steht, an einer Stelle: kein reines Weiß, sondern ein Papierton für den
Bildschirm — Creme, Sandgrau, Blassgelb, Blassblau, Blassgrün oder Blassrosa.
Dazu mehr Luft zwischen Buchstaben, Wörtern und Zeilen, in vier Stufen.

Und die **Schreibstelle**: Der Absatz, in dem der Zeiger steht, wird auf
Wunsch etwas größer, der übrige Text tritt zurück. Ein Farbband allein sagt
nur „hier" — lesbarer wird eine Stelle erst, wenn sie größer ist als das,
was um sie herum steht. Vergrößert wird dabei nicht die Schrift, sondern
das Bild: Eine größere Schrift bricht anders um, die Zeile wird eine
andere, und beim Tippen schaukelt sich das auf.

Passend dazu holt `./schrift-holen.sh` drei Schriften, die eigens fürs
leichtere Lesen gemacht sind (siehe unten).

Das alles ändert das Dokument **nicht**. Kein Buchstabe der Datei wird davon
anders, und auf dem Papier steht nachher, was dort stehen soll. Das ist der
Unterschied zu *Seitenfarbe*: Die färbt das Papier und kostet Tinte. Hier
wird nur der Schirm freundlicher.

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

**Drucken.** Das Programm rechnet den Seitenumbruch selbst aus, statt ihn
dem Browser zu überlassen: Es füllt ein Blatt, bis es voll ist, und fängt
ein neues an. Kopfzeile, Fußzeile und die *wirkliche* Seitenzahl stehen
deshalb auf jeder Seite. Die **Druckvorschau** zeigt den ganzen Stapel zum
Durchblättern — eine, zwei oder vier Seiten nebeneinander, oder als
aufgeschlagenes Buch.

Das **Druckfenster** ist aufgeteilt wie im Writer: links das Blatt, rechts
in drei Reitern die Einstellungen, unten die Knöpfe. Seitenbereich („1-3,
5"), Kopien, Sortieren, nur gerade oder ungerade Blattseiten, Seiten pro
Blatt. Dazu, was auf das Papier kommt: Seitenhintergrund, Bilder,
Formularfelder, Kommentare, Text schwarz drucken, leere Seiten.

Im dritten Reiter steht der **Drucker** selbst — Name, Zustand, Typ, Ort,
mit Papierformat, beidseitigem Druck, Schacht und Auflösung. Diese Angaben
sind nicht erfunden: Sie kommen von CUPS, dem Druckerdienst des Systems,
derselben Quelle, aus der auch LibreOffice sie hat. Meldet ein Drucker
keine Duplexeinheit, bleibt der Schalter dafür grau. Gedruckt wird direkt
über den Druckerdienst; ist keiner eingerichtet, öffnet das Fenster des
Systems.

**Das Lineal** misst wirklich: Zentimeter mit Zahlen, vom Satzspiegel aus
gezählt wie im Writer, und drei Marken für die Einzüge, die sich ziehen
lassen — erste Zeile, links, rechts. Das helle Band zeigt, wo Text steht,
und wandert beim Ziehen mit.

**Zuletzt verwendet.** Unter *Datei* stehen die letzten zehn Dokumente mit
Namen — ein Klick, und das Blatt ist wieder da. Wer eine Datei inzwischen
verschoben oder weggeworfen hat, findet sie nicht mehr in der Liste: Geprüft
wird beim Aufklappen, nicht beim Merken.

**Zwei Oberflächen.** *Ansicht ▸ Benutzeroberfläche* stellt zwischen
Symbolleisten (zwei Zeilen, alles sichtbar) und Registern (Reiter wie in
Word) um. Dieselben Befehle, anders sortiert.

Das Register hat neun Reiter — Datei, Start, Einfügen, Layout, Referenzen,
Überprüfen, Schreibhilfe, Sendungen, Ansicht — und einen zehnten, der nur
da ist, wenn er etwas zu sagen hat: **Tabelle** erscheint, sobald der
Zeiger in einer Tabelle steht, und verschwindet wieder. Die Gruppen folgen
dem Menüband von Word: *Start* trägt Zwischenablage, Schriftart, Absatz,
Formatvorlagen und Bearbeiten, *Ansicht* beginnt mit den Ansichten und
nicht mit dem Zoom. Jeder der 185 Befehle ist von dort erreichbar. Auf *Start* steht der
**Formatvorlagen-Katalog**: Er zeigt die Vorlage, statt sie zu benennen.
Wo eine Gruppe nicht alles zeigt, was es gibt, steht unten rechts ein
**Pfeil ⭨** zum vollen Dialog. Ein **Doppelklick auf den Reiter** klappt
das Band weg und wieder auf.

Im Register **tritt die Reiterzeile an die Stelle der Menüleiste** — sie
kommt nicht dazu. Beides übereinander fräße genau den Platz, den das
Register gewinnen soll. Das Menü bleibt über das Zeichen ☰ rechts in der
Reiterzeile erreichbar, oder über die Alt-Taste. In der Symbolleisten-Ansicht lässt sich
die Menüleiste ebenfalls ausblenden. Symbolgröße und die Schrift der
Bedienung sind einstellbar — wer die Leisten nicht lesen kann, benutzt sie
nicht.

**Das Register anpassen.** Rechtsklick auf eine freie Stelle im Band, oder
*Ansicht ▸ Oberfläche ▸ Anpassen*: Die Gruppen eines Reiters lassen sich
umsortieren und einzeln ausblenden. Verschoben wird mit zwei Pfeilen und
nicht mit der Maus — Ziehen und Ablegen verlangt eine ruhige Hand, ein
Pfeil nach oben trifft immer. Ausgeblendetes bleibt blass in der Liste
stehen, damit man es zurückholen kann.

**Ein Symbol austauschen.** Rechtsklick auf einen Knopf — im Band wie in
den Symbolleisten. Ein Fenster zeigt, wo die Zeichnung überall benutzt
wird, dazu ein Suchfeld und **1801 Zeichnungen** zur Wahl. Ein Klick, und
sie ist getauscht; „Zurücksetzen" holt die alte zurück. LibreOffice kann
das für seine Symbolleisten, für sein Symbolband nicht — hier geht beides.

**Optionen** (F9). Wie im Writer: links ein Baum, rechts der Bereich.
Benutzerdaten, Ansicht, Schriftarten, Pfade, Sprache, Prüfung und KI,
Gedächtnis — und unter *Erweitert*, was zusätzlich geholt wurde und ob es
da ist. Unter *Extras ▸ Erweiterungsverwaltung* steht dasselbe noch einmal
als eigenes Fenster.

## Was nicht drin ist

SmartArt in Word-Qualität, 3D-Modelle, eingebettete Tabellenkalkulation,
Design-Themes, Bildumfluss mit Ebenen, Endnoten-Querverweise nach APA im
vollen Umfang, Barrierefreiheitsprüfung über das Geprüfte hinaus,
Dokumentschutz mit Kennwort, Gliederungsansicht zum Verschieben,
Fenster teilen mit Synchronscrollen.

Bei den meisten wäre der Aufwand groß und der Nutzen für einen Brief gering.
