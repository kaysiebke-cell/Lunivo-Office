#!/usr/bin/env python3
"""Seinen Prüfbogen nachtragen: was erledigt ist, steht als erledigt drin.

WOZU

Am 15.09.2026: „das was du fertig hast markier im protokol wie
vorgehen." Sein Bogen ist die Liste, an der er misst. Wenn ich etwas
baue und es dort weiter auf „fehlgeschlagen" steht, prüft er es ein
zweites Mal — oder er glaubt, es sei nichts passiert.

WIE

Dieses Werkzeug liest seinen Export, setzt die Punkte aus ERLEDIGT auf
„pass" und hängt an seine Notiz an, WAS gemacht wurde und WANN. Seine
eigene Notiz bleibt stehen; sie ist der Auftrag, nicht mein Bericht.

Geschrieben wird eine NEUE Datei. Seine bleibt, wie sie ist — in den
Bogen zurück kommt sie nur, wenn er sie selbst importiert.

WAS HIER NICHT HINEINGEHÖRT

Punkte, die ich nur halb gemacht habe. Ein Bogen, in dem „erledigt"
manchmal „fast" heißt, ist schlechter als gar keiner. Im Zweifel bleibt
die Zeile auf „fail".
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

HEUTE = date.today().strftime('%d.%m.%Y')

# Punkt -> was gemacht wurde. Nur, was ich verteidigen kann.
ERLEDIGT = {
    'start-schriftart|schrift-vergrößern':
        'A⁺ und A⁻ statt der Pfeile, wie gewünscht. Beide stehen in Zeile 1 '
        'neben „Formatierung löschen", wie im WPS-Bild.',
    'start-schriftart|schrift-verkleinern':
        'Siehe Schrift vergrößern: A⁻ gezeichnet, Platz nach Vorlage.',
    'start-schriftart|fett':
        'Die Gruppe steht jetzt in zwei festen Zeilen nach dem WPS-Bild: '
        'Zeile 1 A⁺ A⁻ ◇ Aa▾, Zeile 2 F K U▾ S X² X₂ A Marker▾ Farbe▾ Ⓐ. '
        'Vorher füllte sich das Gitter spaltenweise, darum standen Fett und '
        'Kursiv in verschiedenen Zeilen.',
    'start-schriftart|kursiv':
        'Siehe Fett — steht jetzt direkt daneben.',
    'start-schriftart|unterstrichen':
        'Siehe Fett. Dazu der Pfeil am U für die Strichvorlagen, wie in WPS.',
    'start-schriftart|hochgestellt':
        'X² und X₂ stehen jetzt nebeneinander in derselben Zeile, wie '
        'aufgeschrieben. Vorher trennte sie das spaltenweise Gitter.',
    'start-schriftart|tiefgestellt':
        'Siehe Hochgestellt.',
    'start-schriftart|hervorheben':
        'Der Marker ist jetzt ein geteilter Knopf: ein Klick auf das Zeichen '
        'färbt sofort mit der zuletzt gewählten Farbe, der Pfeil daneben '
        'zeigt die Farben — zwanzig, die hellen zuerst. Vorher öffnete jeder '
        'Klick nur eine Tafel; darum sah der Knopf aus, als täte er nichts.',
    'start-schriftart|schriftfarbe':
        'Eigenes Zeichen: ein A über einem Farbbalken, wie im Bild. Klick '
        'färbt mit der letzten Farbe, Pfeil zeigt die Auswahl.',
    'start-schriftart|groß-kleinschreibung':
        'Linksklick geht jetzt: der Pfeil zeigt die vier Schreibweisen, jede '
        'mit einem Probesatz in genau dieser Schreibweise. Das Fenster liegt '
        'weiter auf dem Zeichen selbst.',
    'start-schriftart|unterstreichungsart':
        'Die Strichvorlagen fehlten nicht — sie lagen hinter einem zweiten, '
        'gleich aussehenden U-Knopf daneben. Jetzt hängen sie am Pfeil des U, '
        'und sie stehen als gezeichnete Striche da, nicht als Wörter.',

    'seitenlayout|papierformat':
        'Auf Deutsch: A4, A3, A5, B5, Letter, Legal, Umschlag DIN lang, C5, '
        'C6 — mit den Maßen darunter. Die chinesischen Formate (8开, 信封) '
        'sind weg. Das Zeichen heißt wieder „Größe", wie in WPS, aber die '
        'Klappe sagt jetzt, worum es geht.',
    'seitenlayout|seitenränder':
        'Jede Vorgabe hat ein kleines Blatt mit eingezeichnetem Satzspiegel — '
        'man sieht, was „Breit" heißt. Dazu die vier Maße im Klartext und die '
        'vier Ränder als Zahlenfelder direkt im Band.',
    'seitenlayout|seitenfarbe':
        'War ein Fenster mit einem Farbfeld. Jetzt die Tafel aus dem Bild: '
        'Keine Farbe, Themafarben, Standardfarben, Farbverlauf, Weitere '
        'Füllfarben, Pipette, Hintergrundbild, Wasserzeichen.',
    'seitenlayout|bild-objekt-anordnen':
        'Die Gruppe heißt jetzt „Anordnen" und hat vier Knöpfe wie in WPS: '
        'Textfluss, Ausrichten, Gruppieren, Drehen. Ausrichten und Drehen '
        'wirken auf Bilder, Formen und Tabellen.',
    'einfügen|leere-seite':
        'Es waren nur Leerzeilen: eingefügt wurde ein Absatz mit '
        'page-break-after — im Druck ein Umbruch, auf dem Bildschirm nichts. '
        'Die Seitenzahl rechnet mit der Höhe des Textes, und ein Umbruch hat '
        'keine Höhe. Jetzt ein Block, so hoch wie eine Seite: sichtbar mit '
        'gestricheltem Rand, im Druck ohne. Der Knopf hat die Klappe '
        'Hochformat / Querformat, wie im Bild. Gemessen: 257 mm hoch, 170 mm '
        'quer, Statuszeile „Seite 1 von 2".',

    'einfügen|diagramm':
        'Der Befehl war richtig verdrahtet — das ZEICHEN stand falsch. Das '
        'Gitter der kleinen Knöpfe füllt sich spaltenweise, darum saß unter '
        'dem Säulenzeichen der Bildschirmfoto-Befehl: Wer aufs Diagramm '
        'zeigte, traf etwas anderes. Feste Zeilen, Zeichen wieder bei ihren '
        'Namen.\n\n'
        'Dazu das Fenster aus Ihrem Bild: links die Kategorien (Spalte, '
        'Linie, Kreis, Balken, Fläche, X Y), oben die Arten, in der Mitte der '
        'Name groß, darunter eine große Vorschau. Neun Arten, neun Zeichner — '
        'gestapelt, in Prozent, liegende Balken, Ring, Fläche, Punktwolke.\n\n'
        'Die Diagrammtools-Leiste nach Ihrem Bild: Diagrammelement '
        'hinzufügen, Schnelllayout, Farbe ändern, Formatvorlagen, '
        'Diagrammtyp ändern mit den acht Arten, Daten auswählen, Daten '
        'bearbeiten, Formatieren, Formatvorlage zurücksetzen.\n\n'
        '„Daten bearbeiten" ist jetzt eine Tabelle, wie Sie es beschrieben '
        'haben — links eintragen, rechts rechnet die Vorschau bei jedem '
        'Tastendruck mit. Enter hängt eine Zeile an.\n\n'
        'Am gewählten Diagramm: acht Markerpunkte, Ziehen ändert die Größe '
        '(480 → 595 px gemessen), ein Kreuz löscht, fünf Knöpfe rechts '
        'daneben. Rechtsklick hat jetzt „Diagramm löschen" — das fehlte.\n\n'
        'Auf Ihren Hinweis hin laufen Griffe, Ziehen und Löschen über '
        'DASSELBE System wie bei Bildern und Tabellen. Ich hatte ein drittes '
        'danebengebaut; das ist raus.',

    'start-zwischenablage|verlauf-rückgängig':
        'Aus dem Reiter entfernt. Rückgängig und Wiederholen stehen im '
        'Schnellzugriff ganz oben — dort sind sie in jedem Reiter erreichbar, '
        'im Band waren sie es nur unter Start.',
    'start-zwischenablage|verlauf-wiederholen':
        'Siehe Rückgängig: aus dem Reiter entfernt, bleibt im Schnellzugriff.',
    'start-absatzlayout|einzug-genau':
        'Zusammengelegt, wie gewünscht: „Einzug & Listenebene" unter Start ▸ '
        'Absatz hat jetzt Vergrößern, Verringern und „Genaues Maß…" in einer '
        'Klappe. Aus Absatzlayout ist der zweite Einzug-Knopf verschwunden.',
    'einfügen|kopfzeile':
        'Ein Knopf „Kopf- und Fußzeile" mit drei Wegen darin: Kopfzeile '
        'bearbeiten, Fußzeile bearbeiten, Seitenzahl einfügen.',
    'einfügen|fußzeile':
        'Siehe Kopfzeile — beide in einem Knopf.',
    'einfügen|uhrzeit':
        'Ein großer Knopf „Datum und Uhrzeit" mit Kalender-und-Uhr-Zeichen, '
        'wie im Bild. Dahinter das Fenster aus Ihrer Vorlage: links die Liste '
        'der verfügbaren Formate, rechts die Sprache, darunter „Automatisch '
        'aktualisieren", unten Abbrechen und OK. Die Liste hängt an der '
        'Sprache — auf Englisch steht dort 9/15/2026 und Tuesday, September '
        '15, 2026, genau wie in WPS.',
    'einfügen|textbaustein':
        'Nach Schreibhilfe gewandert, wie vorgeschlagen — dort als ein Knopf '
        '„Textbausteine" mit Verwalten und Einfügen. In Einfügen steht er '
        'nicht mehr, damit er nicht an zwei Stellen liegt.',
    'einfügen|schnellbaustein':
        'Siehe Textbaustein — mit umgezogen, in derselben Klappe.',
    'ansicht|seitenleiste-schreibhilfe':
        'Aus Ansicht entfernt. Sie steht im Reiter Schreibhilfe, und dort '
        'gehört sie hin.',

    'start-absatz|aufzählung':
        'Sie tat etwas, aber man sah es nicht: Die Liste wurde IN den Absatz '
        'gebaut (<p><ul>…</ul></p>), und das ist ungültig — der Browser räumt '
        'es weg, und der Punkt verschwindet mit. Jetzt wird die Liste danach '
        'herausgehoben. Gilt auch für die Nummerierung.',
    'ansicht|gitternetzlinien':
        'Das Netz stand im background-image. Die Seitenfarbe wird als Kurzform '
        'gesetzt, und die löscht background-image mit — sobald das Blatt eine '
        'Farbe hatte, war das Netz weg. Liegt jetzt als eigene Ebene darüber.',
    'sendungen-lunivo-|formular-schaltfläche':
        'Ein <button> im Text nimmt den Klick selbst; der Zeiger kam nicht '
        'daneben, und ohne Zeiger daneben gibt es nichts zu löschen. Jetzt ein '
        'Feld, das der Text wie ein Zeichen behandelt: Entf löscht es, ein '
        'Doppelklick ändert die Aufschrift, und beim Einfügen wird danach '
        'gefragt.',
    'einfügen|lesezeichen-textmarke':
        'Das Fenster nach Ihrem Bild: Name, Liste der vorhandenen Marken, '
        'Sortieren nach Namen oder Speicherort, ausgeblendete zeigen, und '
        'Hinzufügen / Löschen / Gehe zu. Die drei sind grau, solange nichts '
        'gewählt ist. Vorher war es ein Feld mit einem Namen darin — setzen '
        'ja, wiedersehen nein, löschen nein, hinspringen nein.',

    'ansicht|textbegrenzungen':
        'Die vier Winkel am Satzspiegel sind jetzt auf dem Blatt zu sehen, '
        'nicht mehr nur beim Drucken. Abschalten unter Ansicht.',
}


def main():
    quelle = Path(sys.argv[1] if len(sys.argv) > 1
                  else Path.home() / 'Downloads'
                  / 'pruefkatalog_wps_lunivo_2026-09-13.json')
    ziel = quelle.with_name('pruefkatalog_nachgetragen_%s.json'
                            % date.today().strftime('%Y-%m-%d'))

    bogen = json.loads(quelle.read_text(encoding='utf-8'))
    items = bogen['items']

    getroffen, verfehlt = [], []
    for schluessel, was in ERLEDIGT.items():
        eintrag = items.get(schluessel)
        if eintrag is None:
            verfehlt.append(schluessel)
            continue
        seins = (eintrag.get('note') or '').strip()
        eintrag['status'] = 'pass'
        eintrag['note'] = (seins + '\n\n' if seins else '') \
            + '— erledigt am %s: %s' % (HEUTE, was)
        getroffen.append(schluessel)

    ziel.write_text(json.dumps(bogen, ensure_ascii=False, indent=1),
                    encoding='utf-8')

    offen = sum(1 for v in items.values() if v.get('status') == 'fail')
    print('  %d Punkte nachgetragen, %d bleiben auf „fehlgeschlagen"'
          % (len(getroffen), offen))
    if verfehlt:
        print('  NICHT GEFUNDEN (Schlüssel stimmt nicht):')
        for v in verfehlt:
            print('    ' + v)
    print('  → %s' % ziel)


if __name__ == '__main__':
    main()
