#!/usr/bin/env python3
"""Reiter für Reiter: was in beiden steht, was fehlt, was eigen ist — samt Symbol.

WOZU

Kay hat es am 12.09.2026 so gesagt: „das schwierige ist das wps und meine
Anwendung an vielen stellen auseinander laufen was es schwierig macht die
Funktionen nach zu bauen das betrifft auch die Icons im Reiter."

Solange das Auseinanderlaufen ein Gefühl ist, streiten wir jedes Mal neu
darüber. Als Liste ist es etwas, das man abhaken kann.

DIE REGEL, NACH DER HIER GEURTEILT WIRD

  gleich   Der Punkt steht im SOLL und im Band. Name muss stimmen.
  fehlt    Steht im SOLL, nicht im Band. Das ist ein Fehler, kein Ermessen.
  eigen    Steht im Band, nicht im SOLL. Erlaubt, wenn es Lunivos eigenes
           ist — aber es soll dastehen, damit man es sieht.
  ohne Bild  Der Punkt hat einen Symbolnamen, den es in symbole.js nicht
           gibt. Dann zeichnet das Band das Wort statt eines Bildes.

Das SOLL wird NICHT geschrieben, nur gelesen. Geschrieben wird allein
doku/reiter-abgleich.md.
"""
import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
SOLL = WURZEL / 'doku' / 'wps-soll-lesekopie.txt'
REGISTER = WURZEL / 'oberflaeche' / 'daten' / 'register.js'
SYMBOLE = WURZEL / 'oberflaeche' / 'daten' / 'symbole.js'
ZIEL = WURZEL / 'doku' / 'reiter-abgleich.md'

STRICHE = '│├└─'


def soll_lesen():
    """Den Baum aus der Lesekopie holen: Reiter -> Gruppe -> [(Name, eigen)]."""
    text = SOLL.read_text(encoding='utf-8')
    anfang = text.index('DIE BÄNDER')
    ende = text.index('OPTIONEN —', anfang)
    reiter, gruppe = None, None
    baum = {}

    for zeile in text[anfang:ende].split('\n'):
        roh = zeile.rstrip()
        if not roh or set(roh) <= {'═', ' '}:
            continue
        # Wie tief? An den senkrechten Strichen abzählen.
        tiefe = len(re.match(r'^[│ ]*', roh).group(0)) // 4
        inhalt = roh.lstrip(STRICHE + ' ')
        if not inhalt:
            continue
        eigen = '← Lunivo' in inhalt
        name = inhalt.split('←')[0].split('(')[0].strip().rstrip('—').strip()
        if not name:
            continue

        if tiefe == 0 and name.isupper():
            reiter, gruppe = name.title(), None
            baum[reiter] = {}
        elif tiefe == 1 and name.isupper() and reiter:
            gruppe = name.title()
            baum[reiter][gruppe] = []
        elif reiter and gruppe and tiefe >= 2:
            # Beschreibungssätze unter einem Punkt überspringen: Der Baum
            # trägt auch Fließtext, und der ist kein Befehl.
            # Bemerkungen im Baum sind keine Befehle: „(Verlauf
            # gestrichen: …)" stand sonst als fehlender Punkt im Bogen.
            if name.startswith('(') or inhalt.startswith('('):
                continue
            if (len(name) > 42 or name.endswith(':') or name.endswith('.')
                    or '▸' in name or ' — ' in name or name.count(' ') > 3):
                continue
            baum[reiter][gruppe].append((name, eigen))
    return baum


# Ein Knopf im Band: ['symbolname', 'Titel', …]
# Der Symbolname darf alles sein, was kein Anführungszeichen ist: X², X₂
# und ¶ sind gültige Namen, und eine Zeichenklasse aus Buchstaben und
# Ziffern warf sie stumm weg. Hochgestellt, Tiefgestellt und
# Steuerzeichen standen daraufhin als „fehlt" in der Liste, obwohl sie
# seit Monaten im Band sind.
KNOPF = re.compile(r"\['([^']*)',\s*'([^']+)'")
# Ein Punkt in einer Klappe: ['Titel', () => …]  oder  ['Titel', w.…]
KLAPPE = re.compile(r"\['([^']+)',\s*(?:\(\)|w\.|B\.|function)")
# Ein ausführlicher Klappenpunkt: { name: 'Titel', … bild: 'x' }
REICH = re.compile(r"\{ name: '([^']+)'((?:[^}]|\n){0,400}?)\}", re.S)
BILD_IM_REICHEN = re.compile(r"bild: '([^']+)'")


def zusatz_lesen():
    """Die sechs kontextabhaengigen Register aus programm.js.

    Sie stehen nicht in register.js, sondern in REGISTER_IM_ZUSAMMENHANG,
    und tauchten darum im Bogen gar nicht auf — ein Sechstel der Leiste
    ungeprueft."""
    text = (WURZEL / 'oberflaeche' / 'js' / 'programm.js').read_text(encoding='utf-8')
    anfang = text.index('REGISTER_IM_ZUSAMMENHANG')
    ende = text.index('\n];', anfang)
    block = text[anfang:ende]

    # Jeder Eintrag faengt mit "name: '…'" an; die Gruppen darunter
    # stehen auf ihrer eigenen Einrueckungsstufe.
    register = {}
    stellen = [(m.group(1), m.end())
               for m in re.finditer(r"^    name: '([^']+)',", block, re.M)]
    for i, (name, start) in enumerate(stellen):
        schluss = stellen[i + 1][1] if i + 1 < len(stellen) else len(block)
        teil = block[start:schluss]
        register[name] = re.findall(r"^      \['([^']+)',", teil, re.M)
    return register


def zusatz_soll():
    """Derselbe Baum aus der Lesekopie."""
    text = SOLL.read_text(encoding='utf-8')
    anfang = text.index('KONTEXTABHÄNGIGE REGISTER')
    ende = text.index('OPTIONEN —', anfang)
    baum, jetzt = {}, None
    for zeile in text[anfang:ende].split('\n'):
        m = re.match(r'^[├└]── ([A-ZÄÖÜ][A-ZÄÖÜ ÜSS-]+?)\s*(?:\(|$)', zeile)
        if m:
            # Den Namen so schreiben, wie das Programm ihn schreibt —
            # der Bogen wird gelesen, nicht nur verglichen. Aus
            # „KOPF- UND FUSSZEILENWERKZEUGE" darf weder
            # „Kopf- Und Fusszeilenwerkzeuge" werden noch
            # „Kopf- und fusszeilenwerkzeuge".
            NAMEN = {
                'TABELLENWERKZEUGE': 'Tabellenwerkzeuge',
                'ZEICHENTOOLS': 'Zeichentools',
                'DIAGRAMMTOOLS': 'Diagrammtools',
                'SMARTART-TOOLS': 'SmartArt-Tools',
                'GLEICHUNGSWERKZEUGE': 'Gleichungswerkzeuge',
                'KOPF- UND FUSSZEILENWERKZEUGE': 'Kopf- und Fußzeilenwerkzeuge',
            }
            roh = m.group(1).strip()
            jetzt = NAMEN.get(roh, roh[0] + roh[1:].lower())
            baum[jetzt] = []
            continue
        m = re.match(r'^[│ ]   [├└]── (.+)$', zeile)
        if m and jetzt:
            baum[jetzt].append(m.group(1).strip())
    return baum


def optionen_soll():
    """Der Optionen-Baum aus der Lesekopie: Seite -> [Gruppe -> [Feld]]."""
    text = SOLL.read_text(encoding='utf-8')
    block = text[text.index('OPTIONEN —'):]
    seiten, seite, gruppe = {}, None, None
    for zeile in block.split('\n'):
        if re.match(r'^│   [├└]── [A-ZÄÖÜ]', zeile) or re.match(r'^    [├└]── [A-ZÄÖÜ]', zeile):
            seite = zeile.split('── ', 1)[1].split('←')[0].strip()
            seite = seite[0] + seite[1:].lower()
            seiten[seite] = {}
            gruppe = None
        elif seite is not None and re.match(r'^[│ ]   [│ ]   [├└]── ', zeile):
            gruppe = zeile.split('── ', 1)[1].strip()
            seiten[seite][gruppe] = []
        elif gruppe is not None and re.match(r'^[│ ]   [│ ]   [│ ]   [├└]── ', zeile):
            seiten[seite][gruppe].append(zeile.split('── ', 1)[1].strip())
    return seiten


def optionen_ist():
    """Dasselbe aus doku/aufbau-optionen.md, das aufbau-schreiben.py
    aus dem laufenden Programm zieht."""
    text = (WURZEL / 'doku' / 'aufbau-optionen.md').read_text(encoding='utf-8')
    seiten, seite, gruppe = {}, None, None
    for zeile in text.split('\n'):
        m = re.match(r'^### (.+)$', zeile)
        if m:
            seite = m.group(1).strip()
            seiten[seite] = {}
            gruppe = None
            continue
        if seite is None:
            continue
        m = re.match(r'^[├└]── (.+)$', zeile)
        if m:
            gruppe = m.group(1).strip()
            seiten[seite][gruppe] = []
            continue
        m = re.match(r'^[│ ]   [├└]── (.+)$', zeile)
        if m and gruppe is not None:
            seiten[seite][gruppe].append(m.group(1).strip())
    return seiten


def band_lesen():
    """Aus register.js: Reiter -> [(Symbolname, Titel)].

    Drei Schreibweisen stehen in der Datei nebeneinander, und sie sehen
    einander ähnlich genug, dass ein einziger Ausdruck sie verwechselt:
    Beim ersten Lauf bekam „A4" das Symbol „farbe" angehängt, weil der
    Ausdruck über zwei Einträge hinweg gepaart hatte. Darum drei
    Ausdrücke, jeder an etwas festgemacht, das nur bei ihm vorkommt."""
    text = REGISTER.read_text(encoding='utf-8')
    band = {}
    for m in re.finditer(r"^  \['([^']+)', \[", text, re.M):
        reiter = m.group(1)
        start = m.end()
        weiter = re.search(r"^  \['", text[start:], re.M)
        block = text[start:start + weiter.start()] if weiter else text[start:]

        punkte = [(p.group(1), p.group(2)) for p in KNOPF.finditer(block)]
        punkte += [('', p.group(1)) for p in KLAPPE.finditer(block)]
        for p in REICH.finditer(block):
            bild = BILD_IM_REICHEN.search(p.group(2))
            punkte.append((bild.group(1) if bild else '', p.group(1)))

        # Die Gruppenarten sind keine Befehle: ['Seitenränder', 'raender']
        # sagt dem Band, welche Art Gruppe kommt. Sie standen als „eigen"
        # in der Liste — vier Zeilen Rauschen in einem Bogen, den er
        # abhaken soll.
        punkte = [(z, t) for z, t in punkte
                  if t not in ('raender', 'felder', 'katalog')]

        # Die Wähler stehen als Gruppenart „felder" im Band, nicht als Knopf.
        if "'felder'" in block:
            punkte += [('', 'Formatvorlage'), ('', 'Schriftart'), ('', 'Schriftgröße')]
        if "'katalog'" in block:
            punkte.append(('', 'Katalog'))
        band[reiter] = punkte
    return band


def symbole_lesen():
    text = SYMBOLE.read_text(encoding='utf-8')
    return set(re.findall(r"^  ([A-Za-zÄÖÜäöü0-9_]+): *'", text, re.M))


# F, K, U und S sind in deutschen Schreibprogrammen Buchstaben, kein
# Behelf — und sie zeigen ihre Wirkung an sich selbst. Dasselbe gilt für
# ¶, X², Aa. Der erste Lauf meldete sie als „ohne Bild"; das war falsch,
# und genau die Art Rauschen, die eine Liste unbrauchbar macht.
BUCHSTABEN = {'F', 'K', 'U', 'S', 'X²', 'X₂', 'Aa', '¶', '§', 'Ω', 'A'}


def istBuchstabe(zeichen):
    return zeichen in BUCHSTABEN or len(zeichen) <= 2


def finde(namen, gesucht):
    """Erst auf den Buchstaben genau, dann ungefähr.

    „Sprechblasen" steckt in „Drucken (mit Sprechblasen)". Wer beide in
    einem Durchgang sucht, greift die falsche Gruppe und meldet danach,
    die Papierausrichtung fehle — sie stand die ganze Zeit da.

    Denselben Fehler hatte ich weiter oben schon bei „Umbruch" und
    „Seitenumbruch" gemacht und dort behoben, hier aber neu gebaut. Also
    steht er jetzt an einer Stelle, für alle drei Vergleiche."""
    for streng in (True, False):
        for n in namen:
            if gleich(n, gesucht, genau=streng):
                return n
    return None


def gleich(a, b, genau=False):
    """Namen vergleichen, ohne an einem Bindestrich oder einer Klammer zu
    scheitern — aber streng genug, dass „A4" nicht auf „Farben" passt.
    Ziffern zählen mit: sonst sind A4, A5 und A3 dasselbe Wort."""
    # ß und ss sind dasselbe Wort. „Fußzeilenwerkzeuge" stand als
    # „fehlt ganz" im Bogen, weil die eine Schreibweise aus dem Baum kam
    # und die andere aus dem Programm.
    saeubern = lambda s: re.sub(r'[^a-zäöü0-9]', '', s.lower().replace('ß', 'ss'))
    ka, kb = saeubern(a), saeubern(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    if genau:
        return False
    return len(ka) >= 5 and len(kb) >= 5 and (ka in kb or kb in ka)


def main():
    baum = soll_lesen()
    band = band_lesen()
    symbole = symbole_lesen()

    zeilen = ['# Reiter für Reiter: WPS gegen Lunivo', '',
              'Geschrieben von `werkzeug/reiter-abgleich.py`. Das SOLL kommt aus',
              'seinem Prüfkatalog (Lesekopie in `doku/wps-soll-lesekopie.txt`),',
              'der IST-Stand aus `oberflaeche/daten/register.js`.', '',
              '- **fehlt** — steht im SOLL, nicht im Band. Kein Ermessen.',
              '- **eigen** — steht im Band, nicht im SOLL. Das heißt nicht',
              '  „gibt es in WPS nicht": vieles davon steht dort sehr wohl,',
              '  nur führt das SOLL die Klappe nicht Punkt für Punkt auf.',
              '- **ohne Bild** — der Symbolname steht in keiner Zeile von `symbole.js`;',
              '  das Band zeichnet dann das Wort.', '',
              'Wenn ein Punkt als **fehlt** dasteht, den es im Band gibt, ist er',
              'umbenannt worden — meist nach einer neueren Aufnahme, die das SOLL',
              'noch nicht kennt: „Mittel" heißt in WPS heute „Moderat",',
              '„Seitenrahmen" heißt „Seitenränder", „Textumbruch" heißt',
              '„Textfluss". Dann gehört die Zeile im SOLL nachgezogen, nicht der',
              'Name im Band zurückgedreht. Das entscheidet er, nicht ich.', '']

    summe = {'gleich': 0, 'fehlt': 0, 'eigen': 0, 'ohneBild': 0}

    for reiter, gruppen in baum.items():
        # Der Reiter kann im Band anders heißen (Verweise/Referenzen).
        treffer = finde(band, reiter)
        hat = band.get(treffer, []) if treffer else []
        zeilen.append('## ' + reiter
                      + ('' if treffer else '  — **im Band nicht gefunden**'))
        zeilen.append('')

        # ZWEI DURCHGÄNGE, und zwar in dieser Reihenfolge.
        #
        # „Umbruch" steckt in „Seitenumbruch". Wer beide in einem Durchgang
        # sucht und dabei ungenaue Treffer zulässt, lässt „Umbruch" den
        # „Seitenumbruch" wegschnappen — und meldet danach, der
        # Seitenumbruch fehle. Genau das stand im zweiten Lauf in der
        # Liste, obwohl er seit je im Band steht.
        #
        # Also erst alle, die auf den Buchstaben genau passen. Was dann
        # noch offen ist, darf ungefähr suchen.
        genommen = set()
        alleNamen = [n for pp in gruppen.values() for n, _ in pp]
        for name in alleNamen:
            i = next((k for k, (_, t) in enumerate(hat)
                      if k not in genommen and gleich(t, name, genau=True)), None)
            if i is not None:
                genommen.add(i)
        fest = dict()
        for name in alleNamen:
            i = next((k for k, (_, t) in enumerate(hat)
                      if gleich(t, name, genau=True) and k in genommen
                      and k not in fest.values()), None)
            if i is not None:
                fest[name] = i

        for gruppe, punkte in gruppen.items():
            zeilen.append('### ' + gruppe)
            zeilen.append('')
            zeilen.append('| Punkt | Stand | Bild |')
            zeilen.append('|---|---|---|')
            for name, eigen in punkte:
                i = fest.get(name)
                if i is None:
                    i = next((k for k, (_, t) in enumerate(hat)
                              if k not in genommen and gleich(t, name)), None)
                    if i is not None:
                        genommen.add(i)
                if i is None:
                    zeilen.append('| %s | **fehlt**%s | — |'
                                  % (name, ' (eigen vorgesehen)' if eigen else ''))
                    summe['fehlt'] += 1
                    continue
                zeichen = hat[i][0]
                if zeichen and istBuchstabe(zeichen):
                    zeilen.append('| %s | gleich | Buchstabe `%s` |' % (name, zeichen))
                    summe['gleich'] += 1
                    continue
                if zeichen and zeichen not in symbole:
                    bild = '**ohne Bild** (`%s`)' % zeichen
                    summe['ohneBild'] += 1
                elif zeichen:
                    bild = '`%s`' % zeichen
                else:
                    bild = '—'
                zeilen.append('| %s | gleich | %s |' % (name, bild))
                summe['gleich'] += 1
            zeilen.append('')

        uebrig = [t for k, (_, t) in enumerate(hat) if k not in genommen]
        if uebrig:
            zeilen.append('### Eigen — im Band, nicht im SOLL')
            zeilen.append('')
            for t in uebrig:
                zeilen.append('- ' + t)
                summe['eigen'] += 1
            zeilen.append('')

    # Die Zahl gehört unter die Überschrift, nicht mitten in die Legende.
    zeilen.insert(6, '**%d gleich · %d fehlen · %d eigen · %d ohne Bild**'
                  % (summe['gleich'], summe['fehlt'], summe['eigen'], summe['ohneBild']))
    zeilen.insert(7, '')

    # --- Die sechs kontextabhaengigen Register ---
    zusatz, zusollen = zusatz_lesen(), zusatz_soll()
    zeilen.append('## Kontextabhängige Register')
    zeilen.append('')
    zeilen.append('Sechs Leisten, die nur erscheinen, wo der Zeiger steht. Sie stehen')
    zeilen.append('nicht in `register.js`, sondern in `REGISTER_IM_ZUSAMMENHANG` —')
    zeilen.append('und fehlten darum im Bogen ganz.')
    zeilen.append('')
    zeilen.append('| Leiste | Gruppe | Stand |')
    zeilen.append('|---|---|---|')
    for name, gruppen in zusollen.items():
        treffer = finde(zusatz, name)
        if not treffer:
            zeilen.append('| %s | — | **fehlt ganz** |' % name)
            summe['fehlt'] += 1
            continue
        hat = zusatz[treffer]
        for g in gruppen:
            da = any(gleich(h, g) for h in hat)
            zeilen.append('| %s | %s | %s |' % (name, g, 'gleich' if da else '**fehlt**'))
            summe['gleich' if da else 'fehlt'] += 1
        for h in hat:
            if not any(gleich(h, g) for g in gruppen):
                zeilen.append('| %s | %s | eigen |' % (name, h))
                summe['eigen'] += 1
    zeilen.append('')

    # --- Das Optionen-Fenster: drei Zweige, neunzehn Seiten ---
    osoll, oist = optionen_soll(), optionen_ist()
    zeilen.append('## Optionen')
    zeilen.append('')
    zeilen.append('Neunzehn Seiten. Der IST-Stand kommt aus `doku/aufbau-optionen.md`,')
    zeilen.append('das `aufbau-schreiben.py` aus dem laufenden Programm zieht.')
    zeilen.append('')
    zeilen.append('| Seite | Gruppe | Stand |')
    zeilen.append('|---|---|---|')
    for seite, gruppen in osoll.items():
        treffer = finde(oist, seite)
        if not treffer:
            zeilen.append('| %s | — | **fehlt ganz** |' % seite)
            summe['fehlt'] += 1
            continue
        hat = oist[treffer]
        for g, felder in gruppen.items():
            hatG = finde(hat, g)
            if not hatG:
                zeilen.append('| %s | %s | **fehlt** |' % (seite, g))
                summe['fehlt'] += 1
                continue
            fehlen = [f for f in felder if not any(gleich(x, f) for x in hat[hatG])]
            if fehlen:
                zeilen.append('| %s | %s | **fehlt darin:** %s |'
                              % (seite, g, ', '.join(fehlen)))
                summe['fehlt'] += len(fehlen)
            else:
                zeilen.append('| %s | %s | gleich (%d Felder) |'
                              % (seite, g, len(felder)))
                summe['gleich'] += 1
    zeilen.append('')

    zeilen[6] = ('**%d gleich · %d fehlen · %d eigen · %d ohne Bild**'
                 % (summe['gleich'], summe['fehlt'], summe['eigen'], summe['ohneBild']))

    ZIEL.write_text('\n'.join(zeilen) + '\n', encoding='utf-8')
    print('  %-52s %d Zeichen' % (ZIEL.relative_to(WURZEL), ZIEL.stat().st_size))
    print('  %d gleich, %d fehlen, %d eigen, %d ohne Bild'
          % (summe['gleich'], summe['fehlt'], summe['eigen'], summe['ohneBild']))


if __name__ == '__main__':
    main()
