# Lunivo-Office

*Ein Raum für Worte.*

Ein Schreibprogramm wie LibreOffice Writer oder Word — mit einem
Unterschied: Die Schreibhilfe sitzt fest an der Seite und sucht die Fehler,
die ein Rechtschreibprüfer **nicht** finden kann.

    das / dass       seit / seid       wider / wieder
    „wir hat"  →  „wir haben"          „größer wie"  →  „größer als"
    fehlende Kommas vor weil, dass, wenn, aber
    zusammengetippte Wörter, doppelte Wörter, Satzanfänge

Kein Konto, keine Anmeldung, kein Internet. Was geschrieben wird, bleibt
auf dem eigenen Rechner — nichts geht hinaus, ohne dass man es selbst
schickt.

## Starten

    ./starten.sh

Das legt beim ersten Mal auch den Menüeintrag an. Danach steht
*Lunivo-Office* im Startmenü unter „Büro". Einen alten Eintrag
*Schreibprogramm* räumt der Start still mit weg.

Gebraucht wird dafür GTK mit WebKit:

    sudo apt install python3-gi gir1.2-webkit2-4.1

Ohne das geht es auch im Browser — einmal einen Server starten und die
Adresse aufmachen:

    python3 -m http.server 8322
    # dann http://localhost:8322/ öffnen

Der Umweg über einen Server statt `file://` hat einen Grund: Unter `file://`
gilt die Seite nicht als sicherer Ursprung, und dann merkt sich das Programm
nichts.

## Was es kann

**Schreiben.** Ein Blatt in A4, A5, A3, Letter oder Legal, hoch oder quer,
mit Seitenrändern nach Vorgabe oder auf den Millimeter. Überschriften, Titel
und Untertitel, fett, kursiv, unterstrichen (in fünf Linienstilen),
durchgestrichen, hoch- und tiefgestellt, Schrift- und Hervorhebungsfarbe.
Alle Schriften dieses Rechners — mit Vorschau und Suchfeld, jeder Name in
seiner eigenen Schrift. Links, zentriert, rechts und Blocksatz, Zeilen- und
Absatzabstand, Einzüge, Aufzählungen und Nummerierungen über mehrere Ebenen,
Sortieren, Schattierung und Rahmenlinien, Spalten, Silbentrennung und
Zeilennummern.

Dazu Tabellen mit Zeilen und Spalten zum Einfügen und Löschen, Bilder,
Diagramme (Balken, Linie, Kreis), gezeichnete Formen, Formeln, Textrahmen,
Kopf- und Fußzeilen mit Seitenzahl, Hyperlinks, Textmarken und Querverweise,
Fußnoten, Kommentare, Deckblatt, Wasserzeichen und Seitenrahmen.

Rückgängig und Wiederholen für alles — auch für das, was die Schreibhilfe
oder die KI geändert hat.

**Prüfen.** Der Knopf *Prüfen* (oder F7) legt jeden Fund als eigene Karte in
die Seitenleiste. Drei Sorten, und welche es ist, steht als Wort auf der
Karte — eine Farbe allein müsste man erst lernen:

* **Sicher falsch** — „Wir hat" wird zu „Wir haben".
* **Kommt drauf an** — das fehlende Komma, „dass" aus „das". Noch einmal lesen.
* **Zum Nachdenken** — ein Satz mit 45 Wörtern. Hier gibt es nichts zu
  ersetzen und deshalb auch keinen Knopf dafür.

*Zeigen* springt an die Stelle im Text, *Ändern* setzt sie ein. Nichts ändert
sich von allein.

Lieber eine Lücke als ein falscher Alarm: Regeln, die auch richtige Sätze
anmeckern würden, stehen mit Absicht nicht drin. „Das Buch, das ich gelesen
habe" bleibt deshalb in Ruhe.

**Speichern.** Vier Formate, und für jedes einen Grund:

| Format | wofür |
|---|---|
| `.odt`  | das Format von LibreOffice und OpenOffice — der Normalfall |
| `.fodt` | dasselbe als eine einzige XML-Datei, zum Hineinsehen |
| `.docx` | Word — für alle, die etwas anderes nicht öffnen können |
| `.pdf`  | zum Verschicken und Ausdrucken, unveränderlich |
| `.html` | öffnet sich in Word, im Browser, überall |
| `.txt`  | nur die Wörter — für Formulare im Netz |

Schriftart und Schriftgröße stehen mit in der Datei und kommen beim Öffnen
zurück — auch aus Word.

**Verzeichnisse.** Ein Inhaltsverzeichnis baut sich aus den Überschriften,
ein Abbildungsverzeichnis aus den Beschriftungen, ein Stichwortverzeichnis
aus den festgelegten Einträgen. Alle drei erneuern sich über *Referenzen →
Verzeichnisse aktualisieren*; dabei werden auch die Fußnoten und
Beschriftungen neu durchnummeriert.

**Überarbeiten.** *Änderungen verfolgen* schreibt mit: Neues steht
unterstrichen, Gelöschtes durchgestrichen und bleibt stehen, bis jemand
entscheidet. Einzeln annehmen oder ablehnen, vor und zurück, oder alles auf
einmal. Kommentare lassen sich durchgehen und löschen.

**Seriendruck.** Platzhalter wie `{{Name}}` in den Text, die Empfänger als
Tabelle daneben — daraus entsteht für jede Zeile ein Brief, getrennt durch
Seitenumbrüche.

**Makros.** Aufzeichnen, was man aus den Menüs wählt, unter einem Namen
sichern und später wieder abspielen.

## Wie die Menüs aufgebaut sind

Vierzehn Menüs, und was zusammengehört, steht in einem Untermenü statt
untereinander. Das *Format*-Menü hatte zwischenzeitlich einunddreißig Zeilen
— darin sucht man, statt zu finden. Jetzt sind es fünf: Schrift, Absatz,
Listen, Rahmen und Farbe, und darunter das Zurücksetzen.

    Datei · Bearbeiten · Ansicht · Einfügen · Format · Formatvorlagen
    Layout · Referenzen · Tabelle · Formular · Extras · Schreibhilfe
    Fenster · Hilfe

## Der Motor für Word und PDF

Word-Dateien und PDF macht dieses Programm nicht selbst. Die Filter, die eine
Word-Datei richtig lesen, sind das Ergebnis von Jahrzehnten; sie nachzubauen
wäre aussichtslos. Also erledigt es **LibreOffice im Hintergrund** — ohne
Fenster, ohne dass man es merkt.

Das Programm bringt seinen eigenen mit. Er liegt ausgepackt unter

    ~/.local/share/schreibprogramm/libreoffice/

und wird bevorzugt benutzt. Ist er nicht da, nimmt das Programm das
LibreOffice des Systems. Ist auch das nicht da, sagen die beiden Menüpunkte
das — statt stillschweigend eine kaputte Datei zu schreiben.

Der eigene Motor hat einen Grund: So hängt das Programm nicht daran, was
gerade installiert ist, und ein Update des Systems nimmt ihm nichts weg.
Er belegt allerdings gut 700 MB. Wer das nicht will, löscht den Ordner —
dann übernimmt das LibreOffice des Systems.

Gebraucht wird der Motor nur für `.docx`, `.doc`, `.rtf` und PDF. Alles
andere — schreiben, prüfen, `.odt`, `.fodt`, `.html`, `.txt` — läuft ohne ihn.

Geöffnet werden alle vier. *Drucken* (Strg+P) druckt das Blatt ohne Menü,
Leiste und Seitenleiste — und über „In Datei drucken" wird daraus ein PDF.

## Tasten

| | |
|---|---|
| Strg+N / O / S / P | Neu, Öffnen, Speichern, Drucken |
| Strg+Umschalt+S | Speichern unter (mit Formatauswahl) |
| Strg+Z / Y | Rückgängig, Wiederholen |
| Strg+B / I / U | Fett, Kursiv, Unterstrichen |
| Strg+F, Strg+H | Suchen und Ersetzen |
| Strg + + / − / 0 | Größer, kleiner, Normalgröße |
| Strg+Enter | Seitenumbruch |
| F7 | Prüfen |
| F8 | KI-Korrektur |
| F9 | Einstellungen |
| F5 | Seitenleiste ein und aus |

## Was wo liegt

    start.py          das Fenster (GTK + WebKit), der kleine Server,
                      die Schriftliste und der Weg zu LibreOffice
    starten.sh        startet es und schreibt den Menüeintrag neu

    oberflaeche/      alles, was im Fenster zu sehen ist — und nur das
                      liefert der kleine Server aus
      index.html      die Oberfläche
      css/programm.css  das Aussehen
      js/programm.js  Menüs, Werkzeuge, Seitenleiste, Statuszeile
      js/dokument.js  das Dokument: lesen, zeigen, ersetzen, formatieren
      js/dateien.js   öffnen und speichern — .odt, .fodt, .docx, .doc,
                      .rtf, .pdf, .epub, .html, .txt
      js/pruefung.js  die Prüfung selbst
      js/ki.js        Claude und Ollama, das Gedächtnis, die Sicherung
      js/kiteil.js    die KI im Programm: korrigieren, vorschlagen,
                      übersetzen, die Marken „Für wen?"
      js/drucken.js   Seitenumbruch, Druckvorschau, Druckfenster
      js/referenzen.js  Fußnoten, Zitate, Verzeichnisse
      js/bausteine.js Textbausteine und die Lücken zum Ausfüllen
      js/vorlagen.js  die Seite „Neu" mit den Vorlagen
      js/einstellungen.js  die Einstellungsseite
      daten/regeln.js   der Wortschatz der Prüfung
      daten/woerter.txt die deutsche Wörterliste (355.322 Wörter)

    werkzeug/         Prüfungen für den Quelltext, nicht für den Text
      namen-pruefen.py  sucht Namen, die zweimal im selben Bereich stehen

    symbole/icon.svg  das Symbol des Programms
    symbole/          dasselbe in allen Größen (16 bis 512)
    bilder/marke.png  das freigestellte Zeichen, aus dem sie gerechnet sind
    doku/             diese Seite, ENTSTEHUNG und RICHTUNG

## Namen prüfen, bevor man sich wundert

    ./werkzeug/namen-pruefen.py

In JavaScript ist das hier kein Fehler, den irgendwer meldet:

    function aenderungen() { ... }          // die Liste der Änderungen
    function aenderungen(alt, neu) { ... }  // die Rechnung, die vergleicht

Die spätere Deklaration gewinnt stillschweigend. Genau so waren „Nächste
Änderung", „Annehmen" und „Ablehnen" monatelang kaputt: Sie riefen die
Vergleichsrechnung ohne Argumente auf, und die warf jedes Mal — in die
Konsole, wo es niemand sieht.

Bei `const` und `let` fällt so etwas auf, weil das Programm gar nicht
erst lädt. Bei `function` und `var` nicht. Und über Dateigrenzen hinweg
fällt gar nichts auf: Klassische Skripte teilen sich einen Namensraum,
also kann eine Datei einer anderen einen Namen wegnehmen.

Der Prüfer geht den Quelltext Zeichen für Zeichen durch und zählt die
Klammertiefe mit — Zeichenketten, Kommentare und reguläre Ausdrücke
werden übersprungen. Er meldet, was zweimal im selben Block steht, und
sagt dazu, ob es beim Laden auffällt oder eben nicht. Er gibt 1 zurück,
wenn er etwas findet.

Er kann sich irren, und zwar zugunsten von zu viel: Wer einen Treffer
nicht versteht, sieht sich die genannten Zeilen an.

## Das Symbol

Die Glühbirne mit der Federspitze aus dem Logo, freigestellt, auf einer
dunkelblauen Kachel — dasselbe Zeichen, das auch den Schriftzug trägt.

Die Kachel ist nicht Zierde. Die Linien des Zeichens sind hell, und auf einer
hellen Fensterleiste bliebe bei 16 Bildpunkten davon kaum etwas übrig. Auf dem
Dunkelblau des Schriftzugs bleiben sie sichtbar, gleich ob die Leiste hell oder
dunkel ist, und das Symbol sieht überall gleich aus.

Das Zeichen liegt als Bild in der Datei, nicht als Pfade. Das Logo ist gemalt,
nicht konstruiert — es in Kurven nachzubauen hieße, es neu zu erfinden. Die
freigestellte Vorlage liegt als `bilder/marke.png` dabei; daraus lässt sich der
ganze Satz jederzeit neu rechnen.

Es liegt in neun Größen bereit statt nur in einer. Eine große Datei würde
überall heruntergerechnet, und was bei 16 Bildpunkten dabei herauskommt, hängt
davon ab, wer rechnet. Die neun Dateien sind einmal sauber gerechnet und bleiben
überall dieselben.

`./starten.sh` legt alle Größen unter `~/.local/share/icons/hicolor/` ab.
`./starten.sh --weg` räumt sie wieder fort.

## Herkunft

Die Prüfung stammt aus der **Schreibhilfe**
(<https://github.com/kaysiebke-cell/schreibhilfe>) und ist dort über viele
Fassungen gewachsen. Sie liegt hier als eigene Kopie: Dieses Programm ist
eigenständig und braucht jenes Projekt nicht, um zu laufen.

**Die KI.** Drei Knöpfe unter den Funden, und sie können etwas, das kein
Wörterbuch kann: den Satz verstehen.

* **KI-Korrektur** (F8) liest den ganzen Text und stellt Rechtschreibung,
  Grammatik und Kommas richtig. Eingesetzt wird Wort für Wort — was fett,
  kursiv oder eine Überschrift war, bleibt es.
* **Vorschläge** sucht umständliche Sätze und legt für jeden eine Karte an.
  Jeder einzeln anzunehmen oder liegenzulassen. Der Text gehört dir.
* **Nach Englisch** übersetzt den ganzen Text. Die Sprache steht in den
  Einstellungen — vierzehn zur Wahl.

Alle drei richten sich nach **Für wen?** und dem Zettel **Worum geht's?**:
Ein Brief ans Amt wird anders korrigiert als eine Nachricht an einen Freund.
Strg+Z holt jede KI-Änderung zurück.

Zwei Wege stehen offen, beide in den Einstellungen (F9):

| | |
|---|---|
| **Claude im Netz** | braucht einen Schlüssel und Guthaben, antwortet in Sekunden |
| **Ollama auf diesem Rechner** | kostenlos, ohne Internet, der Text bleibt hier — dauert länger |

Was verbraucht wurde, zählt das Programm selbst mit und zeigt es in den
Einstellungen. Ohne Schlüssel bleiben die Knöpfe blass, führen beim Drücken
aber genau dorthin, wo er hingehört.

**Das Gedächtnis.** Jedes „Ändern" bringt dem Programm etwas bei: „Halloch →
Hallo" steht beim nächsten Mal sofort da, ohne KI und ohne Internet. Wörter,
deren Kasten fünfmal stehen blieb — der Nachname, ein Wort aus der Gegend —
werden künftig in Ruhe gelassen. Was gelernt wurde, steht in den
Einstellungen und lässt sich einzeln nachsehen und wieder vergessen.

**Sichern und Einspielen.** Handy, App und Lunivo-Office lernen jedes für
sich. Der Sicherungs-Text ist die Brücke: hier kopieren, dort einsetzen.
Er hat dasselbe Format wie in der Schreibhilfe-App — was dort gelernt wurde,
kommt hier an. Eingespielt wird zusammengeführt, nicht ersetzt. Der Schlüssel
bleibt bewusst draußen; er gehört nicht in einen Text, den man verschickt.

## Einstellungen

Über **Schreibhilfe → Einstellungen** oder **F9**. Vier Gruppen: KI-Werkzeuge
(Schlüssel, Modell, Verbrauch, Zielsprache), Beim Schreiben
(Textbegrenzungen, rote Wellenlinien), Gedächtnis und Darstellung
(Schriftgröße, hell/dunkel).

## Was noch fehlt

Der Zurück-Eimer der App — dort landet gelöschter Text und lässt sich
zurückholen. Hier tut das Strg+Z, aber nur solange das Fenster offen ist.

Kopf- und Fußzeile erscheinen im Blatt und im Druck, gehen aber noch nicht
in die `.odt`.

Aus dem Funktionsumfang von Word fehlen mit Absicht: SmartArt, Piktogramme,
3D-Modelle, Screenshots und eingebettete Tabellenblätter; Design-Themes; das
Anordnen von Bildern mit Textumbruch und Ebenen; Zitate und
Literaturverzeichnis nach APA oder MLA; Endnoten; Umschläge und Etiketten;
die Barrierefreiheitsprüfung; der Dokumentschutz; die Gliederungsansicht;
Fenster teilen und nebeneinander mit Synchronscrollen. Bei den meisten wäre
der Aufwand groß und der Nutzen für einen Brief gering.
