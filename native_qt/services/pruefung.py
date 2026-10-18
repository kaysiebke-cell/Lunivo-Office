# -*- coding: utf-8 -*-
"""
Die Prüfung ohne Internet — Wort für Wort dieselbe wie oberflaeche/js/pruefung.js.

Übernommen aus der LibreOffice-Erweiterung des Projekts „schreibhilfe“ (MIT, Kay Siebke)
und gegen pruefung.js geprüft (tests/test_pruefung_parität.py).

Das ist eine Übersetzung, keine Neuerfindung: dieselben Listen, dieselben
Muster, dieselbe Reihenfolge, dieselben Begründungen. Beide Fassungen werden
gegeneinander geprüft (siehe libreoffice/vergleiche.py); was hier anders
herauskäme, wäre ein Fehler.

Den Wortschatz trägt diese Datei nicht mehr selbst: Er steht einmal in
online/daten/regeln.js und wird von dort gelesen — von hier wie von app.js.
Eine Abschrift kann auseinanderlaufen, eine Datei nicht. Was hier bleibt, sind
die Regeln selbst; die tragen Baustücke als Code und lassen sich nicht als
Daten hinschreiben.

Wo JavaScript und Python auseinandergehen, steht es im Kommentar dabei.
"""

import json
import os
import re

_HIER = os.path.dirname(os.path.abspath(__file__))


def daten_ordner():
    """Wo regeln.js und woerter.txt liegen — eine Quelle, nicht zwei Abschriften.

    Reihenfolge: Umgebungsvariable LUNIVO_DATEN, native_qt/resources/daten,
    dann oberflaeche/daten im Projekt (dort liegen die Dateien heute).
    """
    wurzel = os.path.abspath(os.path.join(_HIER, '..', '..'))
    kandidaten = [os.environ.get('LUNIVO_DATEN', ''),
                  os.path.join(wurzel, 'native_qt', 'resources', 'daten'),
                  os.path.join(wurzel, 'oberflaeche', 'daten')]
    return [k for k in kandidaten if k]


def _ohne_kommentare(text):
    """Nimmt /* … */ und // … aus JavaScript heraus — Zeichenketten bleiben heil.

    Ein grobes Suchen-und-Ersetzen ginge irgendwann schief, sobald einmal ein
    Schrägstrich in einem Wort steht. Deshalb Zeichen für Zeichen, mit Blick
    darauf, ob wir gerade mitten in einer Zeichenkette stehen.
    """
    raus, i, n, in_kette = [], 0, len(text), False
    while i < n:
        z = text[i]
        if in_kette:
            raus.append(z)
            if z == '\\' and i + 1 < n:
                raus.append(text[i + 1])
                i += 2
                continue
            if z == '"':
                in_kette = False
            i += 1
            continue
        if z == '"':
            in_kette = True
            raus.append(z)
            i += 1
            continue
        if z == '/' and i + 1 < n and text[i + 1] == '*':
            ende = text.find('*/', i + 2)
            i = n if ende < 0 else ende + 2
            raus.append(' ')
            continue
        if z == '/' and i + 1 < n and text[i + 1] == '/':
            ende = text.find('\n', i)
            i = n if ende < 0 else ende
            continue
        raus.append(z)
        i += 1
    return ''.join(raus)


def _lies_regeln():
    """Holt den gemeinsamen Wortschatz aus regeln.js.

    Zwei Orte: gepackt liegt die Datei neben dieser hier (bauen.sh kopiert sie
    hinein), im Arbeitsbaum unter online/daten/. Fehlt sie an beiden, bricht das
    Laden ab — LAUT. Ein stilles Ausweichen auf leere Listen ließe die Prüfung
    scheinbar laufen und einfach nichts mehr finden; genau so eine stille
    Notlösung hat schon einmal einen grünen, aber wertlosen Vergleich erzeugt.
    """
    kandidaten = [os.path.join(d, 'regeln.js') for d in daten_ordner()]
    for k in kandidaten:
        if not os.path.exists(k):
            continue
        with open(k, 'r', encoding='utf-8') as datei:
            text = datei.read()
        marke = text.find('REGELDATEN')
        anfang = text.find('{', marke) if marke >= 0 else -1
        ende = text.rfind('}')
        if anfang < 0 or ende < anfang:
            raise ValueError('%s enthält kein REGELDATEN-Objekt.' % k)
        return json.loads(_ohne_kommentare(text[anfang:ende + 1]))
    raise IOError('Der gemeinsame Wortschatz fehlt. Gesucht wurde in:\n  %s'
                  % '\n  '.join(kandidaten))


_REGELN = _lies_regeln()

# --------------------------------------------------------------------------
# a) Wörter, die ein Rechtschreibprüfer NICHT finden kann
#    — weil beide Schreibweisen für sich genommen richtig sind.
#
# Die Wörter stehen in online/daten/regeln.js, zusammen mit dem übrigen
# Wortschatz und der Begründung zu jedem Eintrag.
# --------------------------------------------------------------------------

WOERTERBUCH = _REGELN['WOERTERBUCH']

WORT_MUSTER = re.compile(r'[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)*')
GROSS_ANFANG = re.compile(r'^[A-ZÄÖÜ]')


def uebernimm_schreibweise(original, verbesserung):
    if GROSS_ANFANG.match(verbesserung):
        return verbesserung                                   # Hauptwort
    if original == original.upper() and len(original) > 1:
        return verbesserung.upper()
    if GROSS_ANFANG.match(original):
        return verbesserung[0].upper() + verbesserung[1:]
    return verbesserung


def mach_fund(von, bis, alt, neu, grund, art, wort_ebene=False):
    return {'von': von, 'bis': bis, 'alt': alt, 'neu': neu,
            'grund': grund, 'art': art, 'wortEbene': wort_ebene}


# --------------------------------------------------------------------------
# b) Wortgruppen für die Regeln
# --------------------------------------------------------------------------

_kette = lambda name: '|'.join(_REGELN[name])

FUERWOERTER = _kette('FUERWOERTER')
DENK_ZEITWOERTER = _kette('DENK_ZEITWOERTER')
DENK_ZEITWOERTER_ENG = _kette('DENK_ZEITWOERTER_ENG')
DASS_EIGENSCHAFTEN = _kette('DASS_EIGENSCHAFTEN')
ZEITANGABEN = _kette('ZEITANGABEN')
STEIGERUNGEN = _kette('STEIGERUNGEN')
FOLGT_NEBENSATZ = FUERWOERTER + '|' + _kette('FOLGT_NEBENSATZ_ZUSAETZLICH')

NEBENSATZ_WOERTER = [tuple(e) for e in _REGELN['NEBENSATZ_WOERTER']]
KEIN_KOMMA_DAVOR = set(_REGELN['KEIN_KOMMA_DAVOR'])
KEIN_HAUPTWORT = set(_REGELN['KEIN_HAUPTWORT'])

ABKUERZUNG = re.compile(
    r'(?:^|[\s(„"])(?:[A-Za-zÄÖÜäöüß]|ca|bzw|usw|evtl|ggf|inkl|exkl|vgl|bspw|'
    r'Nr|Dr|Prof|Abs|Mio|Mrd|Tel|Str)\.$')
# Gefragt wird das WORT an dieser Stelle, nicht die Nachbarschaft (wie wortUm/istAdresse in pruefung.js).
ADR_A = re.compile(r'[@]|https?:|^www\.', re.I)
ADR_B = re.compile(r'[A-Za-zÄÖÜäöü0-9_-]/[A-Za-zÄÖÜäöü0-9_-]')
ADR_C = re.compile(r'\.(de|com|org|net|eu|git|io|dev)\b', re.I)


def ist_abkuerzung(text, punkt):
    return bool(ABKUERZUNG.search(text[max(0, punkt - 9):punkt + 1]))


def wort_um(text, stelle):
    a = b = stelle
    while a > 0 and not text[a - 1].isspace():
        a -= 1
    while b < len(text) and not text[b].isspace():
        b += 1
    return text[a:b]


def ist_adresse(text, stelle):
    wort = wort_um(text, stelle)
    return bool(ADR_A.search(wort) or ADR_B.search(wort) or ADR_C.search(wort))


def gross_dahinter(m, text):
    return bool(re.match(r'^[ \t]+[A-ZÄÖÜ]', text[m.end():]))


# --------------------------------------------------------------------------
# c) Der Regelmotor
#
#    Eine Regel: Muster, Bauplan für den Ersatz, Begründung. Dazu drei
#    Schalter — pruefe (verwirft einen Treffer nachträglich), gruppe (grenzt
#    den Fund auf eine Klammer ein), art.
# --------------------------------------------------------------------------

def regel(muster, bau, grund, art='fehler', gruppe=None, pruefe=None, flags=0):
    return {'muster': re.compile(muster, flags), 'bau': bau, 'grund': grund,
            'art': art, 'gruppe': gruppe, 'pruefe': pruefe}


def wende_regeln_an(text, regeln, funde):
    for r in regeln:
        for m in r['muster'].finditer(text):
            if r['pruefe'] and not r['pruefe'](m, text):
                continue
            gruppe = r['gruppe']
            # „gruppe“ heißt: Das Muster darf die Umgebung mitlesen, gemeint ist
            # nur diese Klammer. Der Versatz ist die Länge alles Vorherigen.
            versatz = sum(len(m.group(i) or '') for i in range(1, gruppe)) if gruppe else 0
            alt = m.group(gruppe) if gruppe else m.group(0)
            neu = r['bau'](m)
            if neu == alt:
                continue
            von = m.start() + versatz
            funde.append(mach_fund(von, von + len(alt), alt, neu, r['grund'], r['art']))


ZEICHEN_REGELN = [
    regel(r' {2,}', lambda m: ' ', 'Mehrere Leerzeichen hintereinander'),
    regel(r'[ \t]+([,.;:!?])', lambda m: m.group(1),
          'Vor dem Satzzeichen gehört kein Leerzeichen'),
    regel(r'([,;:])([A-Za-zÄÖÜäöüß])', lambda m: m.group(1) + ' ' + m.group(2),
          'Nach dem Satzzeichen fehlt ein Leerzeichen'),
    regel(r'([A-Za-zÄÖÜäöüß]{2}[.!?])([A-Za-zÄÖÜäöüß])',
          lambda m: m.group(1) + ' ' + m.group(2),
          'Nach dem Satzzeichen fehlt ein Leerzeichen',
          pruefe=lambda m, t: not ist_adresse(t, m.start())
                              and not ist_abkuerzung(t, m.start() + 2)),
    regel(r',{2,}', lambda m: ',', 'Das Komma steht doppelt da'),
    regel(r'([;:!?])\1+', lambda m: m.group(1), 'Das Satzzeichen steht doppelt da'),
    regel(r'\b([A-Za-zÄÖÜäöüß]+)([ \t]+)\1\b', lambda m: m.group(1),
          'Das Wort steht doppelt da', flags=re.I),
    regel(r'\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß]{1,})[\'’´`]s\b', lambda m: m.group(1) + 's',
          'Vor dem Genitiv-s steht im Deutschen kein Apostroph.', art='tipp'),
]

GROSS_REGELN = [
    regel(r'(^[ \t]*)([a-zäöüß])', lambda m: m.group(2).upper(),
          'Satzanfang großschreiben', gruppe=2),
    regel(r'([.!?]+["»›)]?\s+)([a-zäöüß])', lambda m: m.group(2).upper(),
          'Satzanfang großschreiben', gruppe=2,
          pruefe=lambda m, t: not re.match(r'^\.{2,}', m.group(1))
                              and not ist_abkuerzung(t, m.start())
                              and not ist_adresse(t, m.start() + len(m.group(1)))),
    regel(r'\b(beim|zum|vom|ans|aufs)([ \t]+)([a-zäöüß]{3,}en)\b',
          lambda m: m.group(3)[0].upper() + m.group(3)[1:],
          'Nach „beim/zum/vom“ wird aus dem Tunwort ein Hauptwort.',
          art='tipp', gruppe=3, flags=re.I,
          pruefe=lambda m, t: m.group(3).lower() not in KEIN_HAUPTWORT
                              and not re.search(r'sten$', m.group(3), re.I)
                              and not gross_dahinter(m, t)),
]

GRAMMATIK_REGELN = [
    regel(r'\b(' + DENK_ZEITWOERTER + r')(,?)([ \t]+)das\b'
          r'(?=[ \t]+(?:' + FUERWOERTER + r')\b)',
          lambda m: m.group(1) + ',' + m.group(3) + 'dass',
          'Hier leitet „dass“ den Nebensatz ein – mit Komma davor.',
          art='tipp', flags=re.I),
    regel(r'\b(' + DENK_ZEITWOERTER_ENG + r')(,?)([ \t]+)das\b'
          r'(?=[ \t]+(?:' + FOLGT_NEBENSATZ + r')\b)',
          lambda m: m.group(1) + ',' + m.group(3) + 'dass',
          'Hier leitet „dass“ den Nebensatz ein – mit Komma davor.',
          art='tipp', flags=re.I),
    regel(r'\b(' + DASS_EIGENSCHAFTEN + r')(,?)([ \t]+)das\b'
          r'(?=[ \t]+(?:' + FOLGT_NEBENSATZ + r')\b)',
          lambda m: m.group(1) + ',' + m.group(3) + 'dass',
          'Hier leitet „dass“ den Nebensatz ein – mit Komma davor.',
          art='tipp', flags=re.I),
    regel(r'\bseid([ \t]+)(?=(?:' + ZEITANGABEN + r')\b)',
          lambda m: 'seit' + m.group(1),
          'Bei Zeitangaben heißt es „seit“ – „seid“ nur bei „ihr seid“.',
          flags=re.I),
    regel(r'\bseit([ \t]+)ihr\b', lambda m: 'seid' + m.group(1) + 'ihr',
          '„ihr seid“ – hier gehört ein d ans Ende.', flags=re.I,
          pruefe=lambda m, t: not gross_dahinter(m, t)),
    regel(r'\bihr([ \t]+)seit\b(?![ \t]+(?:' + ZEITANGABEN + r')\b)',
          lambda m: 'ihr' + m.group(1) + 'seid',
          '„ihr seid“ – hier gehört ein d ans Ende.', flags=re.I),
    regel(r'\bseit([ \t]+)(ruhig|still|nett|lieb|vorsichtig|ehrlich|froh|'
          r'gegrüßt|willkommen|gespannt|unbesorgt|bereit)\b',
          lambda m: 'seid' + m.group(1) + m.group(2),
          'Aufforderung an mehrere: „seid ruhig“ mit d.', flags=re.I),
    regel(r'\b(' + STEIGERUNGEN + r')([ \t]+)wie\b',
          lambda m: m.group(1) + m.group(2) + 'als',
          'Nach der Steigerung heißt es „als“: größer als, lieber als.',
          flags=re.I),
    regel(r'\bals([ \t]+)wie\b', lambda m: 'als',
          '„als wie“ ist doppelt gemoppelt – „als“ reicht.', flags=re.I),
]

KOMMA_REGELN = [
    regel(r'\b([A-Za-zÄÖÜäöüß]{2,})([ \t]+)(' + wort + r')\b'
          + (r'(?=[ \t]+(?:' + FUERWOERTER + r')\b)' if nur_vor_fuerwort else ''),
          lambda m: m.group(1) + ',' + m.group(2) + m.group(3),
          'Vor „' + wort + '“ beginnt ein Nebensatz – da gehört ein Komma hin.',
          art='tipp', flags=re.I,
          pruefe=lambda m, t: m.group(1).lower() not in KEIN_KOMMA_DAVOR)
    for wort, nur_vor_fuerwort in NEBENSATZ_WOERTER
] + [
    regel(r'\b([A-Za-zÄÖÜäöüß]{2,})([ \t]+)(aber|sondern|denn)\b'
          r'(?=[ \t]+(?:' + FUERWOERTER + r')\b)',
          lambda m: m.group(1) + ',' + m.group(2) + m.group(3),
          'Hier stoßen zwei Sätze aneinander – davor gehört ein Komma.',
          art='tipp', flags=re.I,
          pruefe=lambda m, t: m.group(1).lower() not in KEIN_KOMMA_DAVOR),
]


# --------------------------------------------------------------------------
# d) Zeitwort und Fürwort müssen zueinander passen
# --------------------------------------------------------------------------

ZEITWOERTER = _REGELN['ZEITWOERTER']
SPALTE = _REGELN['SPALTE']
FORM_ZU_ZEITWORT = {}
for _zeile in ZEITWOERTER:
    for _form in _zeile.values():
        FORM_ZU_ZEITWORT[_form] = _zeile

KONGRUENZ_MUSTER = [
    (re.compile(r'\b(ich|du|er|man|wir)([ \t]+)([a-zäöüß]+)\b', re.I), 1, 3),
    (re.compile(r'\b([a-zäöüß]+)([ \t]+)(ich|du|er|man|wir)\b', re.I), 3, 1),
]


def pruefe_kongruenz(text, funde):
    for muster, nr_fuerwort, nr_form in KONGRUENZ_MUSTER:
        for m in muster.finditer(text):
            fuerwort = m.group(nr_fuerwort)
            form = m.group(nr_form)
            zeile = FORM_ZU_ZEITWORT.get(form.lower())
            if not zeile:
                continue
            richtig = zeile.get(SPALTE.get(fuerwort.lower(), ''))
            if not richtig or richtig == form.lower():
                continue
            alt = m.group(0)
            if nr_form == 1:
                neu = uebernimm_schreibweise(form, richtig) + m.group(2) + fuerwort
            else:
                neu = fuerwort + m.group(2) + uebernimm_schreibweise(form, richtig)
            funde.append(mach_fund(
                m.start(), m.start() + len(alt), alt, neu,
                'So passt das Zeitwort zum Fürwort: „%s %s“.'
                % (fuerwort.lower(), richtig), 'fehler'))


# --------------------------------------------------------------------------
# e) Die große Wörterliste — für Trennen und Tippfehler
# --------------------------------------------------------------------------

TRENN_KURZ = set(_REGELN['TRENN_KURZ'])

ABC = 'abcdefghijklmnopqrstuvwxyzäöüß'

_WOERTER = None


def lade_woerter(pfad=None):
    """Liest die deutsche Wörterliste. Sie liegt neben dieser Datei; fehlt sie,
    wird die des Systems genommen. Ohne Liste arbeiten Trennen und
    Tippfehler-Vorschläge einfach nicht — der Rest läuft weiter."""
    global _WOERTER
    if _WOERTER is not None:
        return _WOERTER
    kandidaten = [pfad] if pfad else []
    kandidaten += [os.path.join(d, 'woerter.txt') for d in daten_ordner()]
    kandidaten += ['/usr/share/dict/ngerman', '/usr/share/dict/german']
    for k in kandidaten:
        if not k or not os.path.exists(k):
            continue
        try:
            with open(k, 'r', encoding='utf-8', errors='ignore') as datei:
                _WOERTER = {z.strip().lower() for z in datei if z.strip()}
            return _WOERTER
        except OSError:
            continue
    _WOERTER = set()
    return _WOERTER


def trenne_zusammen(wort):
    woerter = lade_woerter()
    if not woerter:
        return None
    w = wort.lower()
    if len(w) < 6 or w in woerter:
        return None
    # Ab dem ZWEITEN Zeichen — sonst bleiben „ambesten“, „esgibt“, „zuviel“
    # liegen. Zwei-Zeichen-Teile nur aus TRENN_KURZ, die große Liste wäre
    # hier zu großzügig. (Gleiche Regel wie in online/js/app.js.)
    for i in range(2, len(w) - 1):
        vorn, hinten = w[:i], w[i:]
        if vorn not in woerter or hinten not in woerter:
            continue
        if len(vorn) < 3 and vorn not in TRENN_KURZ:
            continue
        if len(hinten) < 3 and hinten not in TRENN_KURZ:
            continue
        if vorn not in TRENN_KURZ and hinten not in TRENN_KURZ:
            continue
        return vorn + ' ' + hinten
    return None


def pruefe_zusammengeschrieben(text, funde):
    for m in WORT_MUSTER.finditer(text):
        wort = m.group(0)
        getrennt = trenne_zusammen(wort)
        if not getrennt:
            continue
        davor = text[:m.start()]
        satz_anfang = davor.strip() == '' or bool(re.search(r'[.!?]\s+$', davor))
        gross = bool(GROSS_ANFANG.match(wort)) or satz_anfang
        neu = (getrennt[0].upper() + getrennt[1:]) if gross else getrennt
        funde.append(mach_fund(m.start(), m.start() + len(wort), wort, neu,
                               'Zwei Wörter ohne Lücke', 'wort'))


def nachbar_woerter(w):
    """Alle Wörter, die genau einen Handgriff entfernt sind."""
    aus = set()
    for i in range(len(w) + 1):
        if i < len(w):
            aus.add(w[:i] + w[i + 1:])                          # Buchstabe weg
            for c in ABC:
                aus.add(w[:i] + c + w[i + 1:])                  # ersetzt
            if i < len(w) - 1:
                aus.add(w[:i] + w[i + 1] + w[i] + w[i + 2:])    # vertauscht
        for c in ABC:
            aus.add(w[:i] + c + w[i:])                          # eingefügt
    return aus


# JavaScript sortiert mit localeCompare('de'): ä zählt wie a, ö wie o,
# ü wie u, ß wie ss. Pythons eigener Vergleich sortiert nach Zahlenwert und
# stellte alle Umlaute ans Ende — bei gleichrangigen Vorschlägen käme dann ein
# anderer heraus als am Handy.
_DE_ERSATZ = {'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss'}


def _de_schluessel(wort):
    grob = ''.join(_DE_ERSATZ.get(c, c) for c in wort)
    return (grob, wort)


def tippfehler_vorschlag(wort):
    woerter = lade_woerter()
    if not woerter:
        return None
    w = wort.lower()
    if len(w) < 4 or len(w) > 20 or w in woerter:
        return None

    treffer = []
    for k in nachbar_woerter(w):
        if k not in woerter:
            continue
        # Stummel (unter vier Buchstaben für ein längeres Wort) und abgeschnittener Anfang sind keine Tippfehler
        if len(k) < 4 and len(w) >= 4:
            continue
        if k == w[1:]:
            continue
        treffer.append(k)
    if not treffer:
        return None

    def ist_teilfolge(kurz, lang):
        i = 0
        for c in lang:
            if i < len(kurz) and kurz[i] == c:
                i += 1
        return i == len(kurz)

    def rang(k):
        return 0 if ist_teilfolge(w, k) else (1 if ist_teilfolge(k, w) else 2)

    def gleicher_anfang(k):
        i = 0
        while i < len(k) and i < len(w) and k[i] == w[i]:
            i += 1
        return i

    treffer.sort(key=lambda k: (rang(k), -gleicher_anfang(k),
                                0 if k in TRENN_KURZ else 1,
                                len(k), _de_schluessel(k)))
    return treffer[0]


def pruefe_tippfehler(text, funde, gelernt=None):
    for m in WORT_MUSTER.finditer(text):
        wort = m.group(0)
        # Was eine andere Regel schon anfasst, bleibt hier außen vor.
        if WOERTERBUCH.get(wort.lower()) or trenne_zusammen(wort):
            continue
        # In Adressen und Pfaden steht kein Deutsch — dort nichts vorschlagen.
        if ist_adresse(text, m.start()):
            continue
        vorschlag = tippfehler_vorschlag(wort)
        if not vorschlag:
            continue
        neu = (vorschlag[0].upper() + vorschlag[1:]) if GROSS_ANFANG.match(wort) else vorschlag
        if neu == wort:
            continue
        funde.append(mach_fund(m.start(), m.start() + len(wort), wort, neu,
                               'Tippfehler? Ein Buchstabe daneben', 'tipp'))


def wort_abstand(a, b):
    """Wie viele Handgriffe liegen zwischen zwei Wörtern? Zwei vertauschte
    Buchstaben zählen als EINER — „shcon“ ist ein Vertipper, kein anderes
    Wort. (Gleiches Maß wie wortAbstand() in online/js/app.js.)"""
    zeilen = [list(range(len(b) + 1))]
    for i in range(1, len(a) + 1):
        zeile = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            kosten = 0 if a[i - 1] == b[j - 1] else 1
            zeile[j] = min(zeilen[i - 1][j] + 1,
                           zeile[j - 1] + 1,
                           zeilen[i - 1][j - 1] + kosten)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                zeile[j] = min(zeile[j], zeilen[i - 2][j - 2] + 1)
        zeilen.append(zeile)
    return zeilen[len(a)][len(b)]


def ist_korrektur(falsch, richtig):
    """Sieht die Verbesserung dem Wort überhaupt ähnlich? Ein Rechtschreib-
    prüfer, der ein Wort nicht kennt, rät — und dann kommt für
    „Zahnriemenspanner-Kettenrolle“ eben „Unannehmlichkeiten“ heraus."""
    a, b = str(falsch).lower(), str(richtig).lower()
    if not a or not b or a == b:
        return False
    erlaubt = max(2, min(len(a), len(b)) // 3)
    return wort_abstand(a, b) <= erlaubt


# Was gar nicht erst geprüft wird (Optionen ▸ Rechtschreibprüfung; Vorgabe: alle drei an, wie in pruefung.js)
SCHALTER_STANDARD = {'rsGrossIgnorieren': True, 'rsZahlenIgnorieren': True, 'rsPfadeIgnorieren': True}


def uebergehen(wort, text, stelle, schalter):
    if schalter.get('rsGrossIgnorieren', True) and len(wort) > 1 and wort == wort.upper() \
            and re.search(r'[A-ZÄÖÜ]', wort):
        return True
    if schalter.get('rsZahlenIgnorieren', True) and re.search(r'\d', wort):
        return True
    if schalter.get('rsPfadeIgnorieren', True) and ist_adresse(text, stelle):
        return True
    return False


def pruefe_woerter(text, funde, gelernt=None, schalter=None):
    eigene = (gelernt or {}).get('woerter', {})
    schalter = schalter or SCHALTER_STANDARD
    for m in WORT_MUSTER.finditer(text):
        wort = m.group(0)
        if uebergehen(wort, text, m.start(), schalter):
            continue
        aus_liste = WOERTERBUCH.get(wort.lower())
        selbst = None if aus_liste else eigene.get(wort.lower())
        richtig = aus_liste or selbst
        if not richtig:
            continue
        # Selbst Gelerntes muss dem Wort ähnlich sehen, sonst war es nie eine
        # Korrektur.
        if selbst and not ist_korrektur(wort, selbst):
            continue
        ersatz = uebernimm_schreibweise(wort, richtig)
        if ersatz == wort:
            continue
        # Was aus der mitgelieferten Liste kommt, ist sicher falsch. Was dieser
        # Mensch selbst beigebracht hat, kam aus EINEM Antippen — ein guter
        # Hinweis, keine Gewissheit.
        funde.append(mach_fund(
            m.start(), m.start() + len(wort), wort, ersatz,
            'So hast du es schon einmal geändert' if selbst else 'Schreibweise',
            'tipp' if selbst else 'fehler'))


def pruefe_satzende(text, funde):
    bis_ende = re.sub(r'\s+$', '', text)
    if not bis_ende or re.search(r'[.!?:…»"\'\)\]]$', bis_ende):
        return
    woerter = bis_ende[bis_ende.rfind('\n') + 1:].strip().split()
    if len(woerter) < 5:
        return
    letztes = woerter[-1]
    if not re.search(r'[A-Za-zÄÖÜäöüß0-9]$', letztes):
        return
    von = len(bis_ende) - len(letztes)
    funde.append(mach_fund(von, len(bis_ende), letztes, letztes + '.',
                           'Am Ende fehlt der Punkt.', 'tipp'))


def mach_hinweis(von, bis, grund, stelle):
    return {'von': von, 'bis': bis, 'alt': '', 'neu': '', 'grund': grund,
            'stelle': stelle, 'art': 'hinweis', 'wortEbene': False}


def pruefe_satzbau(text, hinweise):
    for m in re.finditer(r'[^.!?\n]+', text):
        roh = m.group(0)
        satz = roh.strip()
        if not satz:
            continue
        anfang = m.start() + roh.index(satz[0])
        anzahl = len(satz.split())
        binder = len(re.findall(r'\b(und|oder|aber|dann|weil)\b', satz, re.I))
        if anzahl > 25:
            hinweise.append(mach_hinweis(
                anfang, anfang + len(satz),
                'Langer Satz: %d Wörter. Zwei kürzere Sätze liest man leichter.' % anzahl,
                satz))
        elif anzahl >= 12 and binder >= 3:
            hinweise.append(mach_hinweis(
                anfang, anfang + len(satz),
                'Der Satz hängt an vielen Bindewörtern. Ein Punkt dazwischen tut ihm gut.',
                satz))

    for auf, zu, name in (('(', ')', 'Klammern'), ('„', '“', 'Anführungszeichen')):
        offen, geschlossen = text.count(auf), text.count(zu)
        if offen != geschlossen:
            hinweise.append(mach_hinweis(
                len(text), len(text),
                '%s: %d-mal geöffnet, %d-mal geschlossen.' % (name, offen, geschlossen), ''))

    if text.count('"') % 2 == 1:
        hinweise.append(mach_hinweis(len(text), len(text),
                                     'Ein Anführungszeichen steht allein da.', ''))


# --------------------------------------------------------------------------
# f) Überschneidungen auflösen und alles zusammenführen
# --------------------------------------------------------------------------

def ohne_ueberschneidung(funde):
    """Zwei Funde an derselben Stelle gehen nicht — die erste Änderung ließe
    die zweite ins Leere laufen. Wort-Funde haben Vorrang: Ein falsch
    geschriebenes Wort wiegt schwerer als ein fehlendes Komma daneben."""
    belegt = []

    def passt(f):
        return all(f['bis'] <= b['von'] or f['von'] >= b['bis'] for b in belegt)

    def nach_stelle(f):
        return (f['von'], -(f['bis'] - f['von']))

    for durchgang in ([f for f in funde if f.get('wortEbene')],
                      [f for f in funde if not f.get('wortEbene')]):
        for fund in sorted(durchgang, key=nach_stelle):
            if passt(fund):
                belegt.append(fund)
    return sorted(belegt, key=nach_stelle)


def finde_probleme(text, gelernt=None, schalter=None):
    """Alle Stellen, die auffällig sind — in derselben Reihenfolge wie am Handy."""
    gelernt = gelernt or {'woerter': {}, 'inRuhe': {}}

    korrekturen = []
    pruefe_woerter(text, korrekturen, gelernt, schalter)
    pruefe_zusammengeschrieben(text, korrekturen)
    pruefe_tippfehler(text, korrekturen, gelernt)
    for fund in korrekturen:
        fund['wortEbene'] = True

    # Wörter auf der Ruhe-Liste sind so gewollt.
    in_ruhe = gelernt.get('inRuhe', {})
    eigene = gelernt.get('woerter', {})
    korrekturen = [f for f in korrekturen
                   if not (in_ruhe.get(f['alt'].lower())
                           and not eigene.get(f['alt'].lower()))]

    wende_regeln_an(text, ZEICHEN_REGELN, korrekturen)
    wende_regeln_an(text, GROSS_REGELN, korrekturen)
    wende_regeln_an(text, GRAMMATIK_REGELN, korrekturen)
    wende_regeln_an(text, KOMMA_REGELN, korrekturen)
    pruefe_kongruenz(text, korrekturen)
    pruefe_satzende(text, korrekturen)

    hinweise = []
    pruefe_satzbau(text, hinweise)

    # Erst das zum Ändern, danach das zum Nachdenken.
    return ohne_ueberschneidung(korrekturen) + hinweise


# --------------------------------------------------------------------------
# Vorschläge für ein einzelnes Wort (Rechtsklick-Menü) — Übertragung aus pruefung.js:
# vorschlaegeFuer, klingtWie, koelnerPhonetik, abstand
# --------------------------------------------------------------------------
from .haeufig import HAEUFIG  # noqa: E402


def abstand(a, b):
    if a == b:
        return 0
    m, n = len(a), len(b)
    if not m:
        return n
    if not n:
        return m
    zeile = list(range(n + 1))
    for i in range(1, m + 1):
        vorherige = zeile[0]
        zeile[0] = i
        for j in range(1, n + 1):
            diagonal = vorherige
            vorherige = zeile[j]
            zeile[j] = min(zeile[j] + 1, zeile[j - 1] + 1, diagonal + (0 if a[i - 1] == b[j - 1] else 1))
    return zeile[n]


def koelner_phonetik(wort):
    w = str(wort).upper().replace('Ä', 'A').replace('Ö', 'O').replace('Ü', 'U').replace('ß', 'SS')
    w = w.replace('QU', 'KW').replace('PH', 'F')
    w = re.sub(r'[^A-Z]', '', w)
    if not w:
        return ''
    laute = []
    for i, c in enumerate(w):
        vor = w[i - 1] if i > 0 else ''
        nach = w[i + 1] if i + 1 < len(w) else ''
        code = None
        if c in 'AEIOUYJ':
            code = '0'
        elif c == 'B':
            code = '1'
        elif c == 'P':
            code = '3' if nach == 'H' else '1'
        elif c in 'DT':
            code = '8' if (nach and nach in 'CSZ') else '2'
        elif c in 'FVW':
            code = '3'
        elif c in 'GKQ':
            code = '4'
        elif c == 'C':
            if i == 0:
                code = '4' if (nach and nach in 'AHKLOQRUX') else '8'
            elif vor and vor in 'SZ':
                code = '8'
            else:
                code = '4' if (nach and nach in 'AHKOQUX') else '8'
        elif c == 'X':
            code = '8' if (vor and vor in 'CKQ') else '48'
        elif c == 'L':
            code = '5'
        elif c in 'MN':
            code = '6'
        elif c == 'R':
            code = '7'
        elif c in 'SZ':
            code = '8'
        elif c == 'H':
            code = None
        if code is not None:
            laute.append(code)
    aus = ''
    for l in laute:
        for z in l:
            if not aus or z != aus[-1]:
                aus += z
    return aus[0] + aus[1:].replace('0', '') if aus else ''


_KLANGTAFEL = None


def _klangtafel():
    global _KLANGTAFEL
    if _KLANGTAFEL is None:
        _KLANGTAFEL = {}
        for wort in lade_woerter():
            if len(wort) < 4:
                continue
            k = koelner_phonetik(wort)
            if k:
                _KLANGTAFEL.setdefault(k, []).append(wort)
    return _KLANGTAFEL


def klingt_wie(wort, hoechstens=15):
    w = str(wort).lower()
    if len(w) < 4 or not lade_woerter():
        return []
    klang = koelner_phonetik(w)
    if not klang:
        return []
    gleiche = [k for k in _klangtafel().get(klang, []) if k != w]
    if len(gleiche) <= 1:
        return gleiche

    def gewicht(k):
        return abstand(w, k) - (2 if k in HAEUFIG else 0)
    return sorted(gleiche, key=lambda k: (gewicht(k), abs(len(k) - len(w)), _de_schluessel(k)))[:hoechstens]


def vorschlaege_fuer(wort, hoechstens=6, gelernt=None):
    woerter = lade_woerter()
    if not woerter:
        return []
    w = str(wort).lower()
    if len(w) < 2 or len(w) > 24 or w in woerter:
        return []
    treffer = [k for k in nachbar_woerter(w) if k in woerter]
    for k in klingt_wie(w):
        if k not in treffer:
            treffer.append(k)
    eigen = ((gelernt or {}).get('woerter') or {}).get(w)
    if eigen and eigen not in treffer:
        treffer.insert(0, eigen)

    def ist_teilfolge(kurz, lang):
        i = 0
        for c in lang:
            if i < len(kurz) and kurz[i] == c:
                i += 1
        return i == len(kurz)
    klang_gleich = set(klingt_wie(w))

    def rang(k):
        if k == eigen:
            return -1
        if ist_teilfolge(w, k):
            return 0
        if ist_teilfolge(k, w):
            return 1
        if k in klang_gleich:
            return 1
        return 2

    def gleicher_anfang(k):
        i = 0
        while i < len(k) and i < len(w) and k[i] == w[i]:
            i += 1
        return i

    def gewicht(k):
        return abstand(w, k) - (2 if k in HAEUFIG else 0)
    treffer.sort(key=lambda k: (rang(k), gewicht(k), -gleicher_anfang(k), len(k), _de_schluessel(k)))
    seen, out = set(), []
    for k in treffer:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out[:hoechstens]
