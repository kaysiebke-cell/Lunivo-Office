# Konzept: Das Optionen-Fenster, leicht und barrierefrei

Stand: umgesetzt (Rahmen, sechs Seiten, Suche, Hell/Dunkel). Aufbau im Einzelnen: [aufbau-optionen.md](aufbau-optionen.md).
Abweichungen vom Entwurf: Das Gedächtnis (gelernte Schreibweisen) steht unter *Schreiben ▸ Weitere Einstellungen*; Kennwort und
Änderungsverfolgung öffnen vorerst als Fenster aus *Speichern ▸ Weitere Einstellungen* (der Umzug nach *Datei ▸ Dokument schützen*
und in den Reiter *Überprüfen* steht noch aus).

## Das Problem heute

- 3 Zweige, 21 Seiten, 87 Schalter, 20 Klapplisten. Das ist ein Baum zum Suchen, kein Fenster zum Einstellen.
- Dieselbe Einstellung steht an mehreren Stellen (Rechtschreibung auf 3 Seiten, „Feldfunktionen drucken“ auf 2, Silbentrennung auf 2).
- Vieles ist Word-Erbe, das für Lunivos Zweck („leichter lesen und schreiben“) nichts beiträgt (Kompatibilität, Zuschnittsmarken, Feldschattierung, Duplexdruck, PDF-Formatvorlagen).
- Wer wenig sieht oder nur mit Tastatur arbeitet, muss durch einen Baum, dessen Äste alle gleich laut sind.

## Leitsätze

1. **Wenige Seiten, flach.** Eine Liste links, höchstens 6 Einträge, kein Baum, keine Zweige.
2. **Das Wichtige zuerst.** Jede Seite zeigt nur ihre 3 bis 7 häufigen Einstellungen. Der Rest steht hinter *Weitere Einstellungen* (eingeklappt, per Tastatur erreichbar).
3. **Eine Einstellung, ein Ort.** Keine Doppelungen. Menü und Band bleiben Abkürzungen auf denselben Zustand.
4. **Sofort wirksam.** Kein OK/Übernehmen/Abbrechen-Rätsel. Jede Änderung gilt gleich und ist sichtbar (kleine Vorschau). Pro Seite *Auf Standard zurücksetzen*.
5. **Klare Sprache.** Beschriftung sagt, was passiert („Text größer anzeigen“), nicht, wie es heißt („Live-Vorschau“). Eine Zeile Erklärung unter jedem Schalter, immer sichtbar, nicht nur als QuickInfo.
6. **Suche oben.** Ein Suchfeld findet jede Einstellung, auch die eingeklappten, und springt hin.

## Neue Gliederung (6 Seiten)

| Seite | Inhalt (sichtbar) | Weitere Einstellungen (eingeklappt) |
|---|---|---|
| **1 Lesen** | Lesestufe, Papierton, Buchstaben-/Wort-/Zeilenabstand, Zeilenfokus, Vorlesen | Schrift zum leichteren Lesen prüfen |
| **2 Anzeige** | **Hell / Dunkel / Wie das System** (drei große Schaltflächen ganz oben), Textgröße der Bedienung, Symbolgröße, Helligkeit/Kontrast, Lineal, Statusleiste, Formatierungszeichen (ein Schalter) | Navigationsbereich, Minisymbolleiste, Seitenleiste beim Start |
| **3 Schreiben** | Schrift und Größe für neuen Text, Sprache, Rechtschreibung und Grammatik prüfen, Silbentrennung, eigenes Wörterbuch, AutoKorrektur (Hauptschalter) | **Alle AutoKorrektur-Fälle bleiben erhalten**, nur eingeklappt und nach Gruppen geordnet (Groß-/Kleinschreibung, Anführungszeichen und Striche, Einzüge und Leerzeichen, Ordnungszahlen). Außerdem Einfügen, Rückgängig-Schritte, Wortvorhersage |
| **4 Speichern** | Standardformat, Ordner, automatische Sicherung (an/aus, Minuten), Maßeinheit | Aufbewahrungsdauer der Zwischenstände, Einstellungsdatei sichern/zurückholen |
| **5 Drucken und PDF** | Hohe Qualität, Hintergründe drucken, PDF: Lesezeichen aus Überschriften, Hyperlinks | Umgekehrte Reihenfolge, Kommentare mitnehmen |
| **6 Name und KI** | Name, Initialen, KI an/aus, API-Schlüssel, Modell | Verbrauch, Gedächtnis (gelernte Schreibweisen) |

Zielgröße: von 87 auf etwa 35 Schalter, davon höchstens 8 pro Seite sichtbar.

## Was raus muss

**Ersatzlos streichen** (Wirkung zu klein, zu technisch oder nicht Lunivos Zweck):
- Kompatibilitätsoptionen (alle 5, Word-6/95/97-Verhalten)
- Zuschnittsmarken, Feldschattierung, Feldfunktionen/Textmarken drucken, Duplexdruck (Blattvorder-/rückseite), Formulardaten drucken
- PDF: Umwandlung fremder/eigener Formatvorlagen in Lesezeichen, Verknüpfung Fuß-/Endnoten
- Tipp für Kopf-/Fußzeile, Minisymbolleiste bei Rechtsklick (doppelt zur Auswahl-Variante)
- Sprechblasen-Feinheiten (Breite, Seitenrand, Verbindungslinien, Papierausrichtung): feste, gute Voreinstellung
- Seite *Erweitert* („was zusätzlich geholt wurde“): wird zu einer Statuszeile in *Name und KI*, nur sichtbar, wenn etwas fehlt

**Zusammenführen** (heute mehrfach):
- Rechtschreibung/Grammatik/Silbentrennung: von 3 Seiten (Lesehilfe, Sprache, Rechtschreibprüfung) auf **eine** Stelle in *Schreiben*
- Formatierungszeichen: ein Schalter *Absatzmarken und Leerzeichen zeigen*, die Einzelzeichen nur eingeklappt
- Druckoptionen aus *Ansicht* und *Drucken*: eine Gruppe in *Drucken und PDF*

**Aus dem Fenster herausnehmen** (eigene, gezielte Aufrufe statt Optionen):
- *Menüband anpassen* und *Schnellzugriffsleiste*: eigener Dialog aus dem Band (Rechtsklick ▸ Anpassen). Es ist ein Werkzeug, keine Einstellung.
- *Dokumentkennwort* und *Bearbeitung sperren*: gehören in *Datei ▸ Dokument schützen*, nicht in globale Optionen (gilt pro Dokument).
- *Änderungen verfolgen* (Markup-Farben): in den Reiter *Überprüfen*, wo man es braucht.

## Hell und Dunkel: leichter Zugang

Heute (siehe Bildschirmfoto): „Thema der Benutzeroberfläche“ als Klappliste und daneben ein „Dunkelmodus aktivieren“, das ausgegraut und damit unbedienbar ist. Das fliegt raus.

- **Eine Wahl statt zwei Schalter:** drei große Schaltflächen mit Vorschau-Symbol: *Hell*, *Dunkel*, *Wie das System*. Immer genau eine ist gewählt. Kein ausgegrauter Schalter.
- **Ganz oben auf der Seite Anzeige**, vor allem anderen.
- **Ohne Optionen erreichbar:** ein Eintrag im Hauptmenü (*Ansicht ▸ Hell/Dunkel wechseln*), ein Knopf in der Statusleiste und ein Tastenkürzel (Vorschlag: Strg+Umschalt+D). Alle drei zeigen denselben Zustand (ein Schalter, mehrere Stellen, wie heute).
- **Sofort sichtbar**, kein Neustart, und der Zustand wird gemerkt.
- **Stil der Registerkarte** und **Farbe der Symbolleiste als Hintergrund** wandern nach „Weitere Einstellungen“ der Seite Anzeige; sie ändern nur Feinheiten.
- Die Farbe selbst kommt aus der Palette im `ui/baukasten/` (kein Fremdbestand), Kontrast in beiden Modi mindestens 4,5:1.

## Barrierefreiheit (verbindlich für den Umbau)

- **Tastatur:** F9 öffnet, Esc schließt, Tab-Reihenfolge folgt der Leserichtung, Pfeiltasten wechseln die Seite, Strg+F springt ins Suchfeld, jedes Element hat ein Alt-Kürzel. Keine Falle im Fenster.
- **Bildschirmleser:** jeder Schalter hat `accessibleName` und `accessibleDescription` (die Erklärzeile). Die Seitenliste meldet „Seite 2 von 6“. Eingeklappte Bereiche melden „eingeklappt/ausgeklappt“.
- **Größe:** Das Fenster richtet sich nach der eingestellten Schriftgröße, nichts wird abgeschnitten, es ist in der Größe veränderbar und merkt sich Größe und letzte Seite.
- **Kontrast und Farbe:** mindestens 4,5:1, nie Farbe als einziges Zeichen, Fokusrahmen immer sichtbar (mindestens 2 px).
- **Ziele:** Schalter und Listen mindestens 32 px hoch, genug Abstand, ein Bedienelement pro Zeile (zweispaltig nur bei großem Fenster, sonst eine Spalte).
- **Rückmeldung:** Änderung wird mit Wirkung gezeigt (Vorschau), nicht nur gespeichert. Fehler stehen im Text neben dem Feld, nicht nur in einem Hinweisfenster.
- **Zurück:** jede Seite hat *Auf Standard zurücksetzen*; ein einzelner Schalter lässt sich per Rechtsklick/Kontexttaste zurücksetzen.

## Umsetzung (modular, bestehende Bausteine)

- Rahmen und Seiten bleiben in `ui/dialogs/optionen.py` und `ui/dialogs/optionen_seiten/`; die Seiten werden zusammengelegt, Schalter behalten ihre Schlüssel im Speicher (Einstellungsdatei bleibt kompatibel, nichts geht verloren, auch Gestrichenes behält seinen Standardwert).
- Eingeklappte Gruppe, Erklärzeile und Suchfeld als neue Bausteine in `ui/baukasten/`, damit auch andere Dialoge sie nutzen.
- Reihenfolge: (1) Schalter-Inventur mit Entscheidung behalten/streichen/verschieben, (2) Rahmen mit 6 Seiten und Suche, (3) Seiten nacheinander umziehen, (4) Barrierefreiheits-Prüfung per Tastatur und mit großer Schrift, (5) `docs/aufbau-optionen.md` und `docs/einstellungen.md` nachziehen.
- Tests nur gezielt: Optionen-Dialog, Suche, Speicher-Schlüssel unverändert; Volltest erst am Schluss wegen der Änderung an einer zentralen Oberfläche.

## Entscheidungen, die bei Ihnen liegen

1. Soll die Streichliste (ohne AutoKorrektur, die bleibt) so gelten, oder bleibt etwas davon (z. B. Duplexdruck)?
2. Dürfen Kennwort und Änderungsverfolgung aus den Optionen wandern?
3. Soll KI als eigene Seite sichtbar bleiben, auch wenn sie ausgeschaltet ist?
