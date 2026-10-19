#!/usr/bin/env python3
"""Schreibt auf, wie das Programm aufgebaut ist — aus dem Programm selbst.

    python3 werkzeug/aufbau-schreiben.py

Erzeugt drei Dateien:

    doku/aufbau-band.md          die neun Reiter
    doku/aufbau-optionen.md      das Optionen-Fenster
    doku/aufbau-ist-stand.md     beides am Stück — der IST-Stand

NIEMALS IN DIE VORLAGE SCHREIBEN

    WPS Office/Lunivo-Office_WPS-Writer-Struktur.md

ist von Hand geschrieben und die verbindliche VORGABE — das SOLL, nicht
das IST. Dieses Werkzeug hat sie am 09.09.2026 überschrieben und damit
ein Wochenende Arbeit gelöscht; zurückgeholt wurde sie aus 75438b6.
Wer hier ein Schreibziel hinzufügt, prüft vorher, ob der Pfad von Hand
gepflegt wird. Der Vergleich SOLL gegen IST geht über einen Diff der
beiden Dateien, nie über ein Überschreiben.

WARUM ERZEUGT UND NICHT GESCHRIEBEN

Eine abgeschriebene Liste stimmt beim ersten Mal und lügt beim vierten.
Der Aufbau hat sich in einer einzigen Nacht dreimal geändert — die
Lesehilfe wanderte von Ansicht nach Schreibhilfe, die Optionen bekamen
Zweige, das Menü eine neue Reihenfolge. Jedes Mal hätte jemand vier
Dateien nachziehen müssen, und beim dritten Mal hätte er es vergessen.

Gelesen wird aus den Dateien, die es wirklich steuern:

    oberflaeche/daten/register.js      Reiter, Gruppen, Knöpfe des Bandes
    oberflaeche/js/einstellungen.js    die Zweige und Seiten der Optionen
    oberflaeche/index.html             die Gruppen und Felder je Seite

WAS DIE DATEIEN LEISTEN SOLLEN

Ein Baum sagt, WAS es gibt und wie es gegliedert ist. Zum Nachschlagen
taugt er nicht: Wer wissen will, wo die Silbentrennung sitzt, scrollt
durch fünfhundert Zeilen. Deshalb steht unter jedem Baum eine
alphabetische Tabelle „Befehl → wo er steht". Sie ist der eigentliche
Gewinn, und von Hand wäre sie nicht zu pflegen.
"""

import io
import os
import re
import sys

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lies(pfad):
    with io.open(os.path.join(HIER, pfad), encoding='utf-8') as datei:
        return datei.read()


def schreib(pfad, text):
    ziel = os.path.join(HIER, pfad)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    with io.open(ziel, 'w', encoding='utf-8') as datei:
        datei.write(text)
    print('  %-52s %6d Zeichen' % (pfad, len(text)))


# ------------------------------------------------------------
# Das Band lesen
# ------------------------------------------------------------
def band_lesen():
    """[(Reiter, [(Gruppe, [Befehl, …]), …]), …]"""
    quelle = lies('oberflaeche/daten/register.js')
    anfang = quelle.index('function REGISTER_BAUEN')
    block = quelle[anfang:]

    reiter = [(m.start(), m.group(1))
              for m in re.finditer(r"^  \['([^']+)', \[", block, re.M)]
    raus = []
    for i, (stelle, name) in enumerate(reiter):
        bis = reiter[i + 1][0] if i + 1 < len(reiter) else len(block)
        teil = block[stelle:bis]
        gruppen = [(m.start(), m.group(1))
                   for m in re.finditer(r"^    \['([A-ZÄÖÜ][^']*)',", teil, re.M)]
        gefunden = []
        for k, (gstelle, gname) in enumerate(gruppen):
            gbis = gruppen[k + 1][0] if k + 1 < len(gruppen) else len(teil)
            gteil = teil[gstelle:gbis]
            # ['symbol', 'Name', …] — der zweite String ist der Name
            namen = re.findall(r"'[a-zA-ZäöüÄÖÜ0-9²₂¶]+',\s*'([^']+)'", gteil)
            # Untermenüs stehen als ['Name', () => …]
            for u in re.findall(r"^\s*\['([A-ZÄÖÜ][^']*)',\s*\(\)", gteil, re.M):
                if u not in namen:
                    namen.append(u)
            gefunden.append((gname, namen))
        raus.append((name, gefunden))
    return raus


# ------------------------------------------------------------
# Das Optionen-Fenster lesen
# ------------------------------------------------------------
def optionen_lesen():
    """[(Zweig, [(Seite, [(Gruppe, [Feld, …]), …]), …]), …]"""
    seiten_quelle = lies('oberflaeche/index.html')
    baum_quelle = lies('oberflaeche/js/einstellungen.js')
    treffer = re.search(r"const BEREICHE = \[(.*?)\n\];", baum_quelle, re.S)
    zweige = re.findall(r"\['([a-z]+)',\s*'([^']+)',\s*\[(.*?)\]\]",
                        treffer.group(1), re.S)

    raus = []
    for _, zweigname, inhalt in zweige:
        seiten = []
        for kennung, seitenname in re.findall(r"\['([a-z]+)',\s*'([^']+)'\]", inhalt):
            a = seiten_quelle.index('data-bereich="%s"' % kennung)
            b = seiten_quelle.find('<div class="gruppe" data-bereich=', a + 10)
            block = seiten_quelle[a:b if b > 0 else len(seiten_quelle)]

            gruppen = re.findall(
                r'<span class="gruppe__titel">([^<]+)</span>(.*?)'
                r'(?=<span class="gruppe__titel">|$)', block, re.S)
            gefunden = []
            if gruppen:
                for titel, teil in gruppen:
                    felder = [re.sub(r'\s+', ' ', n).strip() for n in
                              re.findall(r'class="feld__name"[^>]*>\s*([^<]+)', teil)]
                    if felder:
                        gefunden.append((titel.strip(), felder))
            else:
                # „Menüband anpassen" und „Schnellzugriff" haben keine Gruppen,
                # sondern zwei Listen nebeneinander.
                felder = [re.sub(r'\s+', ' ', n).strip() for n in
                          re.findall(r'class="anp__titel"[^>]*>([^<]+)<', block)]
                if felder:
                    gefunden.append(('', felder))
            seiten.append((seitenname, gefunden))
        raus.append((zweigname, seiten))
    return raus


# ------------------------------------------------------------
# Bäume zeichnen
# ------------------------------------------------------------
def baum(eintraege, tiefe=0, vorn=''):
    """Aus verschachtelten (Name, Kinder)-Paaren einen Baum mit Strichen."""
    zeilen = []
    for i, (name, kinder) in enumerate(eintraege):
        letzte = (i == len(eintraege) - 1)
        zeilen.append(vorn + ('└── ' if letzte else '├── ') + name)
        weiter = vorn + ('    ' if letzte else '│   ')
        if isinstance(kinder, list) and kinder:
            if isinstance(kinder[0], tuple):
                zeilen += baum(kinder, tiefe + 1, weiter)
            else:
                for k, kind in enumerate(kinder):
                    zeilen.append(weiter + ('└── ' if k == len(kinder) - 1 else '├── ') + kind)
    return zeilen


def anker(text):
    """Aus „Menüband anpassen" wird „menüband-anpassen" — wie GitHub es macht."""
    text = text.lower().replace(' ', '-')
    return re.sub(r'[^\wäöüß-]', '', text)


# ------------------------------------------------------------
# Die Suchtabelle — der eigentliche Gewinn
# ------------------------------------------------------------
def tabelle(paare, was='Befehl', wo='Wo er steht'):
    """Alphabetisch: Name → wo er steht. Mehrfach vorkommende zusammengefasst."""
    orte = {}
    for name, ort in paare:
        orte.setdefault(name, [])
        if ort not in orte[name]:
            orte[name].append(ort)
    zeilen = ['| %s | %s |' % (was, wo), '|---|---|']
    for name in sorted(orte, key=lambda w: w.lower()):
        zeilen.append('| %s | %s |' % (name, ' · '.join(orte[name])))
    return '\n'.join(zeilen)


# ------------------------------------------------------------
# Die vier Dateien
# ------------------------------------------------------------
def band_datei(band):
    kopf = """# Der Aufbau des Bandes

**Diese Datei wird erzeugt.** `python3 werkzeug/aufbau-schreiben.py` liest
`oberflaeche/daten/register.js` und schreibt sie neu. Von Hand geändert,
ist die Änderung beim nächsten Lauf wieder weg.

Neun Reiter. Das Band zeigt einen davon; welchen, sagt die Reiterzeile.
Dieselben Befehle stehen auch in der Menüleiste und in den beiden
Symbolleisten — welche Oberfläche sichtbar ist, sagt
*Ansicht ▸ Darstellung ▸ Benutzeroberfläche*.

## Die Reiter im Überblick

| Reiter | Wofür |
|---|---|"""
    wofuer = {
        'Datei': 'Neu, öffnen, speichern, drucken, Optionen, beenden',
        'Start': 'Zwischenablage, Schrift, Absatz, Formatvorlagen',
        'Einfügen': 'Alles, was in den Text hineinkommt',
        'Seitenlayout': 'Ränder, Spalten, Umbrüche, Wasserzeichen',
        'Referenzen': 'Verzeichnisse, Fußnoten, Querverweise',
        'Überprüfen': 'Prüfen, Kommentare, Änderungen verfolgen',
        'Schreibhilfe': 'Was das Lesen und Schreiben erleichtert — der zentrale Reiter',
        'Sendungen': 'Umschläge, Etiketten, Seriendruck',
        'Ansicht': 'Ansichten, Zoom, Fenster, Helligkeit, Oberfläche',
    }
    zeilen = [kopf]
    for name, _ in band:
        satz = wofuer.get(name, '')
        zeilen.append('| [%s](#%s) | %s |' % (name, anker(name), satz))

    zeilen.append('\n---\n')
    for name, gruppen in band:
        zeilen.append('## %s\n' % name)
        zeilen.append('```')
        zeilen.append(name.upper())
        zeilen += baum([(g, b) for g, b in gruppen])
        zeilen.append('```\n')

    paare = [(befehl, '%s ▸ %s' % (reiter, gruppe))
             for reiter, gruppen in band for gruppe, befehle in gruppen
             for befehl in befehle]
    zeilen.append('---\n')
    zeilen.append('## Wo finde ich was?\n')
    zeilen.append('Alphabetisch. Steht ein Befehl an mehreren Stellen, sind alle')
    zeilen.append('genannt — das ist Absicht: ein Schalter, mehrere Stellen, ein Zustand.\n')
    zeilen.append(tabelle(paare))
    zeilen.append('\n---\n')
    zeilen.append('[← Zurück zum README](../README.md) · '
                  '[Der Aufbau der Optionen](aufbau-optionen.md)')
    return '\n'.join(zeilen) + '\n'


def optionen_datei(optionen):
    kopf = """# Der Aufbau der Optionen

**Diese Datei wird erzeugt.** `python3 werkzeug/aufbau-schreiben.py` liest
`oberflaeche/js/einstellungen.js` und `oberflaeche/index.html` und schreibt
sie neu.

Das Optionen-Fenster geht mit **F9** auf, oder über *Datei ▸ Optionen*.
Links ein Baum mit drei Zweigen, rechts der Bereich.

## Die Zweige

| Zweig | Wofür |
|---|---|"""
    wofuer = {
        'Leichter lesen': 'Wofür dieses Programm gebaut ist — steht deshalb zuoberst',
        'Wie im WPS Writer': 'Alle dreizehn Seiten in seiner Reihenfolge und mit seinen Namen',
        'Nur bei Lunivo': 'Was WPS nicht hat',
    }
    zeilen = [kopf]
    for zweig, _ in optionen:
        zeilen.append('| [%s](#%s) | %s |' % (zweig, anker(zweig), wofuer.get(zweig, '')))

    zeilen.append('\n---\n')
    for zweig, seiten in optionen:
        zeilen.append('## %s\n' % zweig)
        for seite, gruppen in seiten:
            zeilen.append('### %s\n' % seite)
            zeilen.append('```')
            if len(gruppen) == 1 and gruppen[0][0] == '':
                zeilen += baum([(f, []) for f in gruppen[0][1]])
            else:
                zeilen += baum([(g, f) for g, f in gruppen])
            zeilen.append('```\n')

    paare = []
    for zweig, seiten in optionen:
        for seite, gruppen in seiten:
            for gruppe, felder in gruppen:
                ort = seite if not gruppe else '%s ▸ %s' % (seite, gruppe)
                for feld in felder:
                    paare.append((feld, ort))
    zeilen.append('---\n')
    zeilen.append('## Wo finde ich was?\n')
    zeilen.append('Alphabetisch, mit Seite und Gruppe.\n')
    zeilen.append(tabelle(paare, 'Einstellung', 'Wo sie steht'))
    zeilen.append('\n---\n')
    zeilen.append('[← Zurück zum README](../README.md) · '
                  '[Der Aufbau des Bandes](aufbau-band.md)')
    return '\n'.join(zeilen) + '\n'


def struktur_datei(band, optionen):
    """Beides am Stück — für das Artifact und zum Überfliegen."""
    zeilen = ['WPS WRITER + LUNIVO OFFICE — der Aufbau', '',
              'Erzeugt von werkzeug/aufbau-schreiben.py, nicht von Hand geschrieben.',
              'Nach Themen aufgeteilt und mit einer Suchtabelle steht dasselbe in',
              'doku/aufbau-band.md und doku/aufbau-optionen.md.', '',
              'DIE BÄNDER', '│']
    zeilen += baum([(r, [(g, b) for g, b in gr]) for r, gr in band])
    zeilen += ['', '', '═' * 63, '', 'DAS OPTIONEN-FENSTER — Datei ▸ Optionen (F9)', '│']
    zeilen += baum([(z, [(s, [(g, f) for g, f in gr]) for s, gr in seiten])
                    for z, seiten in optionen])
    return '\n'.join(zeilen) + '\n'


def main():
    print('Lese das Programm …')
    band = band_lesen()
    optionen = optionen_lesen()
    print('  %d Reiter, %d Gruppen, %d Knöpfe' % (
        len(band), sum(len(g) for _, g in band),
        sum(len(b) for _, g in band for _, b in g)))
    print('  %d Zweige, %d Seiten, %d Felder' % (
        len(optionen), sum(len(s) for _, s in optionen),
        sum(len(f) for _, s in optionen for _, g in s for _, f in g)))

    print('Schreibe:')
    schreib('doku/aufbau-band.md', band_datei(band))
    schreib('doku/aufbau-optionen.md', optionen_datei(optionen))
    schreib('doku/aufbau-ist-stand.md', struktur_datei(band, optionen))
    return 0


if __name__ == '__main__':
    sys.exit(main())
