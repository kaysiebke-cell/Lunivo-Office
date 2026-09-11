#!/usr/bin/env python3
"""Wie tief geht ein Befehl wirklich?

Kay: "du hast so viele funktionen ausgelassen und nur ansatzweise
gebaut." Das laesst sich nicht mit Ansehen beantworten, sondern nur mit
Zaehlen — und zwar an der richtigen Stelle. Ein Reiter voller Knoepfe
sagt nichts darueber, ob hinter den Knoepfen etwas steht.

Dieses Werkzeug liest register.js (welche Befehle das Band anbietet) und
programm.js (was diese Befehle tun) und stuft jeden ein:

  FEHLT        es gibt B.<name> gar nicht — der Knopf greift ins Leere
  RUDIMENTAER  hoechstens zwei Zeilen, oder nur eine Meldung
  KNAPP        drei bis sechs Zeilen
  AUSGEBAUT    mehr

Die Zeilenzahl ist ein grobes Mass und kein Urteil ueber Qualitaet — ein
guter Befehl kann kurz sein. Aber "nur eine Meldung ausgeben" ist kein
Befehl, und das findet diese Zaehlung zuverlaessig.
"""
import io
import re
import sys


def koerper_lesen(quelle):
    """Jede Zuweisung B.name = ... samt Rumpf bis zur naechsten."""
    stellen = [(m.group(1), m.end())
               for m in re.finditer(r'^B\.([a-zA-Z0-9_]+)\s*=\s*', quelle, re.M)]
    koerper = {}
    for i, (name, start) in enumerate(stellen):
        ende = stellen[i + 1][1] if i + 1 < len(stellen) else len(quelle)
        koerper[name] = quelle[start:ende]
    return koerper


def urteil(koerper, name):
    k = koerper.get(name)
    if k is None:
        return ('FEHLT', 0)
    zeilen = [z for z in k.split('\n')
              if z.strip() and not z.strip().startswith(('*', '/*', '//'))]
    n = len(zeilen)
    text = '\n'.join(zeilen)

    # Ein Befehl, der nur eine Meldung ausgibt, TUT nichts — egal wie
    # lang er ist. Das ist der eigentliche Platzhalter.
    if re.match(r'^\s*\(\)\s*=>\s*(\{\s*)?melde\(', text):
        return ('NUR MELDUNG', n)
    # B.fett = () => document.execCommand('bold') ist zwei Zeilen lang
    # und vollstaendig richtig. Zeilen zaehlen allein waere Unsinn.
    if re.search(r'execCommand|Dokument\.|fenster\(|Speicher\.|classList|style\.', text):
        return ('AUSGEBAUT', n)
    if n <= 2:
        return ('DUENN', n)
    if n <= 6:
        return ('KNAPP', n)
    return ('AUSGEBAUT', n)


def main():
    quelle = io.open('oberflaeche/js/programm.js', encoding='utf-8').read()
    register = io.open('oberflaeche/daten/register.js', encoding='utf-8').read()
    koerper = koerper_lesen(quelle)

    reiter = None
    gefunden = []
    for zeile in register.split('\n'):
        # Die Reiter stehen auf der zweiten Einrueckungsstufe: "  ['Start', ["
        # Die Gruppen darunter tiefer. Nur die Reiter zaehlen hier.
        kopf = re.match(r"^  \['([^']+)',\s*\[\s*$", zeile)
        if kopf:
            reiter = kopf.group(1)
        befehl = re.search(
            r"\['([a-zA-Z0-9]+)',\s*'([^']+)',\s*\(\)\s*=>\s*B\.([a-zA-Z0-9_]+)\(",
            zeile)
        if befehl:
            gefunden.append((reiter or '?', befehl.group(2), befehl.group(3)))

    zaehler = {'FEHLT': 0, 'NUR MELDUNG': 0, 'DUENN': 0, 'KNAPP': 0, 'AUSGEBAUT': 0}
    zeilen = []
    for r, anzeige, fn in gefunden:
        stufe, n = urteil(koerper, fn)
        zaehler[stufe] += 1
        zeilen.append((r, anzeige, fn, stufe, n))

    print('%d Befehle im Band.' % len(zeilen))
    for stufe in ('FEHLT', 'NUR MELDUNG', 'DUENN', 'KNAPP', 'AUSGEBAUT'):
        print('  %-12s %d' % (stufe, zaehler[stufe]))
    print()
    for stufe in ('FEHLT', 'NUR MELDUNG', 'DUENN'):
        treffer = [z for z in zeilen if z[3] == stufe]
        if not treffer:
            continue
        print('=== %s (%d) ===' % (stufe, len(treffer)))
        for r, anzeige, fn, _, n in sorted(treffer):
            print('  %-14s %-36s B.%s (%d)' % (r, anzeige[:35], fn, n))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
