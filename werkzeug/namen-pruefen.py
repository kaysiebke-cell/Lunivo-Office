#!/usr/bin/env python3
"""namen-pruefen.py — sucht Namen, die zweimal im selben Geltungsbereich stehen.

WARUM ES DAS GIBT

In JavaScript ist das kein Fehler, den irgendwer meldet:

    function aenderungen() { ... }        // die Liste der Aenderungen
    function aenderungen(alt, neu) { ... } // die Rechnung, die vergleicht

Die spaetere Deklaration gewinnt stillschweigend. Genau so waren "Naechste
Aenderung", "Annehmen" und "Ablehnen" monatelang kaputt: Sie riefen die
Vergleichsrechnung ohne Argumente auf, und die warf jedes Mal.

Bei "const" und "let" faellt es auf, weil das Programm gar nicht erst
laeuft. Bei "function" und "var" nicht. Und ueber Dateigrenzen hinweg
faellt gar nichts auf: Klassische Skripte teilen sich einen Namensraum,
also kann eine Datei einer anderen einen Namen wegnehmen.

WIE ES ARBEITET

Der Text wird Zeichen fuer Zeichen durchgegangen und die Klammertiefe
mitgezaehlt. Zeichenketten, Vorlagen, Kommentare und regulaere Ausdruecke
werden uebersprungen -- ein "{" in einem Kommentar ist keine Klammer.

Auf jeder Tiefe wird gemerkt, welche Namen dort deklariert wurden. Steht
einer zweimal auf derselben Tiefe im selben Block, wird er gemeldet.

Das ist keine vollstaendige Sprachanalyse, sondern eine Kontrolle, die
sich irren kann -- zugunsten von zu viel, nicht von zu wenig. Wer einen
Treffer nicht versteht, sieht sich die Zeilen an; sie stehen dabei.

    ./werkzeug/namen-pruefen.py               alle Dateien des Programms
    ./werkzeug/namen-pruefen.py datei.js ...  nur diese
"""
import sys, os, re
from collections import defaultdict

DATEIEN = [
    'oberflaeche/js/programm.js', 'oberflaeche/js/drucken.js',
    'oberflaeche/js/bausteine.js', 'oberflaeche/js/kiteil.js',
    'oberflaeche/js/referenzen.js', 'oberflaeche/js/vorlagen.js',
    'oberflaeche/js/ki.js', 'oberflaeche/js/pruefung.js',
    'oberflaeche/js/dateien.js', 'oberflaeche/js/dokument.js',
    'oberflaeche/js/einstellungen.js',
    'oberflaeche/daten/symbole.js', 'oberflaeche/daten/register.js',
    'oberflaeche/daten/themenwoerter.js', 'oberflaeche/daten/regeln.js',
    'oberflaeche/daten/vorlagenmuster.js', 'oberflaeche/daten/symbolkatalog.js',
]

WORT = re.compile(r'[A-Za-z_$][\w$]*')
# Nach diesen Zeichen faengt ein Schraegstrich einen regulaeren Ausdruck an,
# nicht eine Division.
VOR_REGEL = set('(,=:[!&|?{};+-*%~^<>') | {'\n'}
SCHLUESSEL = {
    'const','let','var','function','class','return','if','else','for','of','in',
    'while','do','switch','case','break','continue','new','typeof','instanceof',
    'delete','void','try','catch','finally','throw','extends','super','yield',
    'await','async','true','false','null','this','get','set','static','default',
    'from','as','export','import','with','debugger',
}


def durchgehen(text):
    """Gibt (tiefe, weg, zeile, art, name) fuer jede Deklaration zurueck.

    "weg" ist der Pfad der Bloecke bis hierher — damit zwei Namen nur dann
    als gleich gelten, wenn sie wirklich im selben Block stehen und nicht
    bloss auf derselben Tiefe in verschiedenen Bloecken.
    """
    i, n = 0, len(text)
    zeile = 1
    tiefe = 0
    weg = [0]          # laufende Nummer des Blocks je Tiefe
    zaehler = [0]
    letzte = ''        # letztes bedeutsames Zeichen, fuer die Regex-Frage
    gefunden = []
    # Der Kopf einer Schleife steht VOR der geschweiften Klammer:
    #     for (const teil of ...) { ... }
    # Ohne Sonderbehandlung landet "teil" im umgebenden Block, und zwei
    # Schleifen im selben Zweig saehen aus wie eine Dopplung. Jeder
    # Schleifenkopf bekommt deshalb einen eigenen Bereich.
    klammern = []      # offene runde Klammern: None oder eine eigene Nummer
    kopfNr = 0
    vorwort = ''       # letztes Wort vor einer runden Klammer

    while i < n:
        c = text[i]
        zwei = text[i:i+2]

        if c == '\n':
            zeile += 1; i += 1; continue
        if zwei == '//':
            j = text.find('\n', i)
            i = n if j < 0 else j
            continue
        if zwei == '/*':
            j = text.find('*/', i + 2)
            if j < 0: break
            zeile += text.count('\n', i, j)
            i = j + 2
            continue
        if c in '\'"`':
            ende = c
            j = i + 1
            while j < n:
                if text[j] == '\\': j += 2; continue
                if text[j] == ende: break
                if text[j] == '\n': zeile += 1
                j += 1
            i = j + 1
            letzte = 'x'
            continue
        if c == '/' and (letzte == '' or letzte in VOR_REGEL):
            j = i + 1
            inKlasse = False
            while j < n:
                if text[j] == '\\': j += 2; continue
                if text[j] == '[': inKlasse = True
                elif text[j] == ']': inKlasse = False
                elif text[j] == '/' and not inKlasse: break
                elif text[j] == '\n': break
                j += 1
            i = j + 1
            letzte = 'x'
            continue
        if c == '(':
            if vorwort in ('for', 'catch'):
                kopfNr += 1
                klammern.append(kopfNr)
            else:
                klammern.append(None)
            letzte = c; vorwort = ''; i += 1; continue
        if c == ')':
            if klammern: klammern.pop()
            letzte = c; vorwort = ''; i += 1; continue
        if c == '{':
            tiefe += 1
            if len(zaehler) <= tiefe: zaehler.append(0); weg.append(0)
            zaehler[tiefe] += 1
            weg[tiefe] = zaehler[tiefe]
            letzte = c; i += 1; continue
        if c == '}':
            if tiefe > 0:
                for t in range(tiefe + 1, len(zaehler)): zaehler[t] = 0
                tiefe -= 1
            letzte = c; i += 1; continue

        m = WORT.match(text, i)
        if m:
            wort = m.group(0)
            if wort in ('const', 'let', 'var', 'function', 'class'):
                j = m.end()
                if wort == 'function':
                    # "function" kann auch namenlos sein (Ausdruck)
                    while j < n and text[j] in ' \t*': j += 1
                nm = WORT.match(text, j) if j < n else None
                # bei const/let/var darf Leerraum davor stehen
                if wort in ('const', 'let', 'var', 'class'):
                    k = m.end()
                    while k < n and text[k] in ' \t': k += 1
                    nm = WORT.match(text, k)
                if nm and nm.group(0) not in SCHLUESSEL:
                    kopf = next((k for k in reversed(klammern) if k is not None), None)
                    ort = tuple(weg[:tiefe+1]) + (('kopf', kopf) if kopf else ())
                    gefunden.append((tiefe, ort, zeile, wort, nm.group(0)))
            i = m.end()
            letzte = 'x'; vorwort = wort
            continue

        if not c.isspace(): letzte = c
        i += 1
    return gefunden


def pruefen(pfade):
    proDatei = {}
    globale = defaultdict(list)     # Name -> [(datei, zeile, art)]
    treffer = 0

    for pfad in pfade:
        if not os.path.isfile(pfad):
            print(f'  fehlt: {pfad}'); continue
        text = open(pfad, encoding='utf-8').read()
        eintraege = durchgehen(text)
        proDatei[pfad] = eintraege

        # 1. Doppelt im selben Block
        nachOrt = defaultdict(list)
        for tiefe, weg, zeile, art, name in eintraege:
            nachOrt[(weg, name)].append((zeile, art))
        for (weg, name), stellen in sorted(nachOrt.items(), key=lambda p: p[1][0][0]):
            if len(stellen) < 2: continue
            arten = {a for _, a in stellen}
            # zwei "var" derselben Sache sind erlaubt und harmlos
            if arten == {'var'}: continue
            treffer += 1
            wie = 'faellt beim Laden auf' if arten & {'const','let','class'} \
                  else 'FAELLT NICHT AUF — die spaetere gewinnt'
            print(f'\n  {pfad}')
            print(f'    "{name}" steht {len(stellen)}x im selben Block ({wie})')
            for zeile, art in stellen:
                print(f'      Zeile {zeile:6}  {art} {name}')

        # 2. Was diese Datei in den gemeinsamen Namensraum legt
        for tiefe, weg, zeile, art, name in eintraege:
            if tiefe == 0 and 'kopf' not in weg:
                globale[name].append((pfad, zeile, art))

    # 3. Ueber Dateigrenzen
    ueber = {n: s for n, s in globale.items() if len({d for d, _, _ in s}) > 1}
    if ueber:
        for name, stellen in sorted(ueber.items()):
            treffer += 1
            print(f'\n  ZWISCHEN DATEIEN: "{name}" wird von mehreren Dateien')
            print( '                    in denselben Namensraum gelegt:')
            for d, z, a in stellen:
                print(f'      {d}:{z}  {a} {name}')

    print()
    if treffer:
        print(f'{treffer} Stelle(n) zum Ansehen.')
    else:
        print('Keine Namensdopplung gefunden.')
    return 1 if treffer else 0


if __name__ == '__main__':
    hier = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(hier)
    sys.exit(pruefen(sys.argv[1:] or DATEIEN))
