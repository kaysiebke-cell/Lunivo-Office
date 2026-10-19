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

    ./starten-qt.sh

Beim ersten Mal legt das Skript eine eigene Python-Umgebung (`.venv`) an und
installiert PySide6 und die übrigen Pakete; `./starten-qt.sh --eintrag` legt
zusätzlich den Menüeintrag an, danach steht *Lunivo Writer* im Startmenü unter „Büro".
Direkt aus dem Projektordner geht auch `python3 main.py`.

Gebraucht werden nur ein paar Qt-Systembibliotheken:

    sudo apt install python3 python3-venv libxcb-cursor0 libegl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0

Das Programm ist eine **native Qt-Anwendung** — kein Browser, kein WebKit und kein
Server. Einzelheiten und die freiwilligen Teile (LibreOffice, LanguageTool, Piper, Ollama):
[INSTALLATION.md](INSTALLATION.md).

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
oder die KI geändert hat. Über einen Reiterwechsel hinaus reicht es nicht:
Es hängt am Schreibfeld, nicht am Text.

**Mehrere Dokumente.** Ein Fenster trägt mehrere; oben steht für jedes ein
Reiter. Strg+N legt eins an, Strg+W schließt es, Strg+Tab wechselt, Ziehen
ordnet um. Jedes bringt seine ganze Seite mit — Papier, Ränder, Kopf- und
Fußzeile, Abschnitte, Formatvorlagen. Was dem Menschen gehört, wechselt
nicht mit: Vergrößerung, Helligkeit, welche Leisten er mag.

Auch mehrere **Fenster** (*Ansicht ▸ Fenster ▸ Neues Fenster*) kommen einander nicht ins Gehege:
Jedes hat seine eigene Reiterzeile, und was im einen geschrieben wird, steht nur dort.

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

## Wie die Menüs aufgebaut sind

Acht Reiter und neun Menüs (*Sendungen* gehört dazu, ist im Register aber erst nach *Anpassen* sichtbar), und sie tragen dieselben Namen —
die Vorlage dafür ist WPS Writer. Was zusammengehört, steht in einem
Untermenü statt untereinander: Das *Format*-Menü hatte zwischenzeitlich
einunddreißig Zeilen, und darin sucht man, statt zu finden.

    Datei · Start · Einfügen · Seitenlayout · Verweise
    Überprüfen · Schreibhilfe · Ansicht · (Sendungen)

Makros gibt es nicht. In einem Textdokument wird nicht programmiert —
alles, was damit zu tun hatte, ist wieder heraus.

## Word-Dateien und PDF

**DOCX** liest und schreibt das Programm **selbst** (python-docx und eigenes XML) — es ist das Hauptformat.
Auch PDF entsteht ohne Fremdprogramm: Das Programm rechnet den Seitenumbruch selbst und schreibt das PDF
mit Lesezeichen, Kommentaren und Fußnoten-Verknüpfungen.

**LibreOffice im Hintergrund** (ohne Fenster) braucht es nur für `.odt`, `.doc` und `.rtf`. Es wird
benutzt, wenn es auf dem Rechner installiert ist; ist es nicht da, sagen die Menüpunkte das — statt
stillschweigend eine kaputte Datei zu schreiben. Ein eigener mitgelieferter Motor wie früher
(gut 700 MB) ist nicht mehr nötig.

Gelesen werden `.docx`, `.odt`, `.doc`, `.rtf`, `.html` und `.txt`. *Drucken* (Strg+P) druckt das Blatt ohne
Menü, Leiste und Seitenleiste; was dabei nicht übernommen werden kann, meldet ein Bericht.

## Tasten

| | |
|---|---|
| Strg+N / O / S / P | Neues Dokument, Öffnen, Speichern, Drucken |
| Strg+W | Dokument schließen |
| Strg+Tab | Nächstes Dokument (mit Umschalt das vorige) |
| Strg+Umschalt+S | Speichern unter (mit Formatauswahl) |
| Strg+Z / Y | Rückgängig, Wiederholen |
| Strg+B / I / U | Fett, Kursiv, Unterstrichen |
| Strg+F, Strg+H | Suchen und Ersetzen |
| Strg+K | Hyperlink einfügen |
| Strg + + / − / 0 | Größer, kleiner, Normalgröße |
| Strg+Enter | Seitenumbruch |
| F7 | Prüfen |
| F8 | KI-Korrektur |
| F9 | Einstellungen |
| F5 | Seitenleiste ein und aus |
| F6 | Welche Hilfe wann |
| F4 | Vorlesen |

## Was wo liegt

Die ausführliche Fassung steht in [README.md](README.md) (Aufbau der Qt-Fassung) und im
Kapitel [Der Aufbau des Projekts](projektaufbau.md). Kurz:

    main.py, starten-qt.sh   starten das Programm
    src/lunivo_writer/       das Programm: core (Kern), ui (alles Sichtbare: ribbon, document,
                             sidebar, contextual, dialogs, statusbar), editor, models, services,
                             ai, proofing, resources
    assets/                  Zeichnungen (Fluent, Lucide), Logo, Bilder
    docs/                    diese Seite, ENTSTEHUNG, RICHTUNG, die Mini-Dateien, Bericht, Prüfbogen
    werkzeug/                Abgleich-Skripte (Prüfbogen gegen das Programm)
    tests/                   automatische Tests

## Prüfläufe

Die Tests laufen ohne Fenster:

    ./starten-qt.sh --test

Sie prüfen den Editor, DOCX-Lesen und -Schreiben (auch gegen LibreOffice), das Band, die
Backstage-Ansicht, die Schreibhilfe, PDF und Druck. Was sie nicht prüfen können, ist alles,
was einen echten Bildschirm, Drucker oder Dienst braucht — dafür gibt es keinen Ersatz
außer Hinsehen. Welche Punkte belegt und welche offen sind, steht in [PRUEFBOGEN.md](PRUEFBOGEN.md).

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

`./starten-qt.sh --eintrag` legt alle Größen unter `~/.local/share/icons/hicolor/` ab.
`./starten-qt.sh --weg` räumt sie wieder fort.

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

Über **Datei ▸ Erweiterte Einstellungen**, **☰ Menü ▸ Optionen** oder **F9**. Drei Zweige:
*Leichter lesen*, *Wie im WPS Writer* und *Nur bei Lunivo* (Schreibhilfe und KI, Gedächtnis, Erweitert).
Mehr dazu in [einstellungen.md](einstellungen.md).

## Was noch fehlt

Der Zurück-Eimer der App — dort landet gelöschter Text und lässt sich
zurückholen. Hier tut das Strg+Z, aber nur solange das Fenster offen ist.

Mit Absicht fehlen: 3D-Modelle, eingebettete Tabellenblätter und Design-Themes.
Noch offen sind SmartArt, die Zeichen-, Diagramm- und Gleichungswerkzeuge, das Anlegen eigener
Formatvorlagen und Fenster teilen mit Synchronscrollen. Wo die Qt-Fassung steht — Punkt für Punkt
gegen den Prüfbogen —, steht in [PRUEFBOGEN.md](PRUEFBOGEN.md) und [BERICHT.md](BERICHT.md). Bei den meisten
fehlenden Dingen wäre der Aufwand groß und der Nutzen für einen Brief gering.
