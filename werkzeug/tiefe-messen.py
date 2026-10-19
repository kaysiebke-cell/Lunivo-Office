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


# Jeder Aufruf in einem kurzen Rumpf. Nicht nur der erste: Bei
#   B.linealZeigen = () => { lineal = !lineal; ansichtExtras(); }
# steht vor dem Aufruf noch eine Zuweisung, und ein Ausdruck, der am
# Zeilenanfang festgemacht ist, findet ansichtExtras nie.
AUFRUF = re.compile(r"\b([a-zA-Z_$][\w$]*)\s*\(")
# Oder gleich ein anderer Name: B.zoomSeite = zoomGanzeSeite;
GLEICHSETZUNG = re.compile(r"^\s*([a-zA-Z_$][\w$]*)\s*;?\s*$")
# Was kein Weiterreichen ist, sondern Handwerkszeug.
KEIN_ZIEL = {'if', 'for', 'while', 'switch', 'return', 'typeof', 'catch',
             'melde', 'parseInt', 'parseFloat', 'String', 'Number'}


def hinterher(quelle, name, tiefe=0):
    """Wenn ein Befehl nur weiterreicht, misst der Bericht die falsche
    Stelle.

    B.groesser = () => setzeZoom(zoom + 10) ist eine Zeile lang und
    vollstaendig richtig; die Arbeit steckt in setzeZoom. Fuenfzehn
    solcher Einzeiler standen als DUENN im Bericht — Suchen, Ersetzen,
    Kopfzeile, Lineal, Vergroessern. Wer dem geglaubt haette, haette
    fuenfzehn fertige Befehle nachgebaut.

    Also: dem Namen nachgehen, bis etwas kommt, das selbst arbeitet."""
    if tiefe > 3:
        return None
    # „async function fensterOrdnen(" — das Wort davor gehoert dazu.
    m = re.search(r"^(?:async\s+)?(?:function\s+)?" + re.escape(name)
                  + r"\s*(?:=\s*)?(?:async\s*)?(?:function\s*)?\(", quelle, re.M)
    if not m:
        return None
    start = m.start()
    naechste = re.search(r"^(?:function\s+|B\.|const |let )", quelle[start + 1:], re.M)
    return quelle[start:start + 1 + naechste.start()] if naechste else quelle[start:]


def urteil(koerper, name, quelle=''):
    k = koerper.get(name)
    if k is None:
        return ('FEHLT', 0)

    # Reicht der Befehl nur weiter? Dann zaehlt, wohin er reicht.
    kern = [z for z in k.split('\n')
            if z.strip() and not z.strip().startswith(('*', '/*', '//'))]
    if len(kern) <= 2 and quelle:
        # koerper_lesen schneidet hinter dem Gleichheitszeichen ab, der
        # Rumpf faengt also schon mit „() =>" an.
        rumpf = kern[0] if kern else ''
        ziele = [g for g in AUFRUF.findall(rumpf) if g not in KEIN_ZIEL]
        g = GLEICHSETZUNG.match(rumpf)
        if g:
            ziele.append(g.group(1))
        for ziel in ziele:
            weiter = hinterher(quelle, ziel)
            if weiter and len([z for z in weiter.split('\n') if z.strip()]) > 2:
                art, n = urteil({name: weiter}, name)
                return (art, n)
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
    # ALLE Module, nicht nur programm.js.
    #
    # Vorher las das Werkzeug eine einzige Datei — und meldete daraufhin
    # neunzehn Befehle als FEHLT, darunter den ganzen Referenzen-Reiter:
    # Fussnote, Endnote, Inhaltsverzeichnis, Beschriftung, Zitat. Die
    # stehen seit je in oberflaeche/js/referenzen.js. Ich haette sie ein
    # zweites Mal gebaut, schlechter, wenn ich dem Bericht geglaubt
    # haette statt nachzusehen.
    #
    # Ein Massstab, der die halbe Werkstatt nicht kennt, misst nicht zu
    # streng, sondern falsch.
    from pathlib import Path
    teile = sorted(Path('oberflaeche/js').glob('*.js'))
    quelle = '\n'.join(t.read_text(encoding='utf-8')
                       for t in teile if not t.name.endswith('.test.js'))
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
        stufe, n = urteil(koerper, fn, quelle)
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
