#!/usr/bin/env python3
"""Aus seinem Prüfbogen einen Arbeitsplan machen.

WOZU

Am 15.09.2026: „du machst Sachen, die ich dir nicht aufgetragen habe. Du
hast mein Protokoll, dann gehe ich auch davon aus, dass du es gelesen und
verstanden hast und dir entsprechend einen Arbeitsplan gemacht hast, wie
du alles abarbeitest, ohne gleich alles zu schrotten."

Er hat recht. Ich habe mir eine Gruppe ausgesucht, darin gebaut, dabei
seine Farbpalette herausgeworfen, und den Rest improvisiert. Ein Bogen
mit 88 gemeldeten Fehlern ist kein Steinbruch, aus dem man sich etwas
heraussucht.

WIE DER PLAN ENTSTEHT

Nicht nach meinem Gefühl, sondern aus seinen eigenen Worten. Seine
Notizen sagen fast immer selbst, worum es geht — „Icon ist als Funktion
nicht zu erkennen", „doppelt gemoppelt", „nach Bildvorlage auszubauen",
„hier braucht es einen Konsens". Das sind die Pakete.

Innerhalb der Pakete gilt seine Reihenfolge: Start, Einfügen,
Seitenlayout, und so weiter, wie im Bogen.

„Siehe Fett", „Siehe Suchen" heißt: derselbe Auftrag. Solche Einträge
werden an den zusammengefasst, auf den sie zeigen — sonst steht dieselbe
Arbeit fünfmal im Plan.
"""
import io
import json
import re
from collections import OrderedDict
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
BOGEN = Path.home() / 'Downloads' / 'pruefkatalog_wps_lunivo_2026-09-13.json'
ZIEL = WURZEL / 'doku' / 'pruefkatalog' / 'arbeitsplan.md'

# Seine Worte -> das Paket. Die Reihenfolge entscheidet: Der erste
# Treffer gewinnt, darum steht das Eindeutige oben.
PAKETE = [
    ('konsens', 'Erst fragen, dann bauen',
     ['konsens', 'was soll das für eine funktion', 'müssen wir', 'braucht es von uns',
      'ist das so richtig', 'kann ich nicht', 'kein vergleich', 'beurteilen zu können'],
     'Hier will er eine Antwort, keinen Umbau. Wer hier baut, baut am '
     'Gespräch vorbei.'),
    ('doppelt', 'Doppeltes zusammenführen',
     ['doppelt gemoppelt', 'zusammenfassen', 'zusammengeführt', 'kann man in ein',
      'fast identisch'],
     'Zwei Knöpfe für eine Sache. Zusammenlegen ist wenig Arbeit und '
     'räumt die Leiste auf.'),
    ('tot', 'Knöpfe, die nichts tun',
     ['ohne funktion', 'ohne ersichtliche funktion', 'ohne sichtbare funktion',
      'rumpf ohne'],
     'Ein Knopf, der nichts tut, ist schlimmer als ein fehlender. Hat '
     'Vorrang vor allem Schönen.'),
    ('falsch', 'Falsche Funktion dahinter',
     ['falsche funktion', 'fehlerhaft', 'nichts mit', 'lediglich', 'blinden',
      'lässt sich nicht'],
     'Der Knopf tut etwas, aber das Falsche. Schlimmer als nichts zu tun, '
     'weil man es erst merkt, wenn der Text kaputt ist.'),
    ('icon', 'Zeichen, die man nicht lesen kann',
     ['icon ist', 'icon als', 'icon im', 'symbol ist', 'das icon', 'nicht zu erkennen',
      'missverständlich', 'nicht erkennbar', 'besser zu erkennen', 'zu erkennen ist'],
     'Für Legastheniker ist ein unlesbares Zeichen kein Schönheitsfehler, '
     'sondern die Funktion selbst.'),
    ('anordnung', 'Anordnung nach der Bildvorlage',
     ['anordnung', 'gehören nebeneinander', 'nach vorlage umzusetzen'],
     'Steht da, tut das Richtige, steht aber falsch.'),
    ('ausbauen', 'Nach Bildvorlage ausbauen',
     ['bildvorlage', 'nach vorlage', 'nach wps', 'auszubauen', 'ausbaufähig',
      'zu bauen', 'zu gestalten', 'anzupassen', 'umzubauen', 'zu ändern'],
     'Die größte Gruppe und die teuerste. Kommt zuletzt, weil jedes '
     'Stück ein eigenes Fenster ist.'),
]

VERWEIS = re.compile(r'^\s*s(?:ie)?he\s+(.+?)\.?\s*$', re.I)


def paket_fuer(notiz):
    n = (notiz or '').lower()
    for kuerzel, name, woerter, warum in PAKETE:
        if any(w in n for w in woerter):
            return kuerzel
    return 'ausbauen'


def main():
    bogen = json.loads(BOGEN.read_text(encoding='utf-8'))
    items = bogen['items']

    # Bereiche in der Reihenfolge des Bogens.
    reihenfolge = []
    for k in items:
        b = k.split('|')[0]
        if b not in reihenfolge:
            reihenfolge.append(b)

    # „Siehe Fett" an den hängen, auf den es zeigt.
    anhang = {}
    eigene = OrderedDict()
    for k, v in items.items():
        if v.get('status') != 'fail':
            continue
        notiz = (v.get('note') or '').strip()
        m = VERWEIS.match(notiz)
        if m:
            anhang.setdefault(m.group(1).strip().lower(), []).append(k)
        else:
            eigene[k] = v

    def angehaengte(schluessel):
        punkt = schluessel.split('|')[-1].replace('-', ' ')
        raus = []
        for zeigt_auf, liste in anhang.items():
            if zeigt_auf in punkt or punkt in zeigt_auf:
                raus += liste
        return raus

    nach_paket = OrderedDict((p[0], []) for p in PAKETE)
    for k, v in eigene.items():
        nach_paket[paket_fuer(v.get('note'))].append((k, v))

    z = ['# Arbeitsplan aus seinem Prüfbogen', '',
         'Gebaut von `werkzeug/arbeitsplan-bauen.py` aus seinem Export vom',
         '13.09.2026. Die Pakete kommen aus seinen eigenen Notizen, nicht aus',
         'meinem Gefühl.', '',
         '## Die Regel, die vorher gefehlt hat', '',
         'Nur anfassen, was in dem Punkt steht, an dem ich gerade arbeite.',
         'Beim Umbau der Schriftart-Gruppe habe ich seine Farbpalette gegen',
         'WPS-Signalfarben getauscht — danach stand `#FF0000` in einem',
         'Programm, in dem Lesen leicht sein soll. Das hatte niemand',
         'verlangt.', '',
         '## Reihenfolge der Pakete', '']

    for i, (kuerzel, name, _, warum) in enumerate(PAKETE, 1):
        z.append('%d. **%s** — %d Punkte. %s'
                 % (i, name, len(nach_paket[kuerzel]), warum))
    z.append('')

    gesamt = 0
    for kuerzel, name, _, warum in PAKETE:
        eintraege = nach_paket[kuerzel]
        if not eintraege:
            continue
        z.append('## %s' % name)
        z.append('')
        z.append('_%s_' % warum)
        z.append('')
        # In der Reihenfolge des Bogens.
        eintraege.sort(key=lambda e: reihenfolge.index(e[0].split('|')[0]))
        for schluessel, wert in eintraege:
            bereich, punkt = schluessel.split('|', 1)
            mit = angehaengte(schluessel)
            z.append('### %s ▸ %s%s'
                     % (bereich, punkt,
                        (' _(+ %s)_' % ', '.join(p.split('|')[-1] for p in mit))
                        if mit else ''))
            z.append('')
            z.append('> ' + (wert.get('note') or '(ohne Notiz)').replace('\n', '  \n> '))
            z.append('')
            bilder = len(wert.get('bilder') or [])
            if bilder:
                z.append('%d Bild%s: `doku/pruefkatalog/bilder/%s/`'
                         % (bilder, '' if bilder == 1 else 'er',
                            re.sub(r'[^a-z0-9]+', '-', schluessel.lower())))
                z.append('')
            gesamt += 1 + len(mit)

    z.append('---')
    z.append('')
    z.append('%d Punkte, zu %d Aufgaben zusammengefasst.'
             % (gesamt, sum(len(v) for v in nach_paket.values())))

    ZIEL.write_text('\n'.join(z) + '\n', encoding='utf-8')
    print('  %s' % ZIEL.relative_to(WURZEL))
    for kuerzel, name, _, _ in PAKETE:
        print('  %-34s %d' % (name, len(nach_paket[kuerzel])))


if __name__ == '__main__':
    main()
