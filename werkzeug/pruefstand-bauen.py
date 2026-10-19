#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Der Prüfstand: eine Seite, auf der er sieht, was erledigt ist.

WOZU

Am 16.09.2026: „kann ich nicht sehen, da du nie abhaken tust deine
Arbeit." Und er hat recht. Ich trug nach — in eine JSON-Datei in seinem
Download-Ordner, die er erst in seinen Bogen importieren müsste. Bis
dahin sieht er nichts.

Diese Seite zeigt denselben Stand zum Aufmachen: oben die Zahlen,
darunter je Abschnitt die offenen Punkte mit SEINER Notiz und die
erledigten mit dem, was ich gemacht habe.

WAS HIER NICHT STEHT

Punkte, die er noch gar nicht geprüft hat („open"). Die sind keine
Arbeit, die aussteht — die hat er nur noch nicht angesehen. Sie stehen
nur in der Zählung oben.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

QUELLE = sorted(Path.home().glob('Downloads/pruefkatalog_nachgetragen_*.json'))
ZIEL = Path('doku/pruefkatalog/pruefstand.html')
HEUTE = date.today().strftime('%d.%m.%Y')


def huebsch(text):
    return re.sub(r'\s+', ' ', text.replace('-', ' ')).strip()


def abschnittsname(schluessel):
    roh = schluessel.split('|')[0].rstrip('-')
    return huebsch(roh).title()


def main():
    if not QUELLE:
        print('  Kein Bogen in ~/Downloads gefunden.')
        return
    daten = json.loads(QUELLE[-1].read_text(encoding='utf-8'))
    items = daten['items']

    zahl = {'pass': 0, 'fail': 0, 'open': 0, 'andere': 0}
    for v in items.values():
        s = v.get('status')
        zahl[s if s in zahl else 'andere'] += 1

    # Nach Abschnitt sammeln, offene zuerst.
    abschnitte = {}
    for k, v in items.items():
        s = v.get('status')
        if s not in ('fail', 'pass'):
            continue
        note = (v.get('note') or '').strip()
        meins = ''
        seins = note
        if '— erledigt am' in note:
            seins, _, rest = note.partition('— erledigt am')
            seins = seins.strip()
            meins = rest.split(':', 1)[1].strip() if ':' in rest else rest.strip()
        if s == 'pass' and not meins:
            continue                      # von ihm selbst abgehakt, nichts zu zeigen
        name = abschnittsname(k)
        abschnitte.setdefault(name, {'offen': [], 'fertig': []})
        eintrag = {
            'punkt': huebsch(k.split('|', 1)[1]) if '|' in k else huebsch(k),
            'seins': seins,
            'meins': meins,
            'bilder': len(v.get('bilder') or []),
        }
        abschnitte[name]['offen' if s == 'fail' else 'fertig'].append(eintrag)

    teile = []
    for name in sorted(abschnitte, key=lambda n: (-len(abschnitte[n]['offen']), n)):
        gruppe = abschnitte[name]
        zeilen = []
        for e in gruppe['offen']:
            zeilen.append(
                '<li class="punkt punkt--offen">'
                '<span class="marke" aria-label="offen"></span>'
                '<div><h3>%s</h3>%s%s</div></li>' % (
                    html.escape(e['punkt'][:1].upper() + e['punkt'][1:]),
                    '<p class="seins">%s</p>' % html.escape(e['seins']) if e['seins'] else '',
                    '<p class="bilder">%d Bild%s dabei</p>' % (
                        e['bilder'], 'er' if e['bilder'] != 1 else '') if e['bilder'] else ''))
        for e in gruppe['fertig']:
            zeilen.append(
                '<li class="punkt punkt--fertig">'
                '<span class="marke" aria-label="erledigt">✓</span>'
                '<div><h3>%s</h3>%s<p class="meins">%s</p></div></li>' % (
                    html.escape(e['punkt'][:1].upper() + e['punkt'][1:]),
                    '<p class="seins">%s</p>' % html.escape(e['seins']) if e['seins'] else '',
                    html.escape(e['meins'])))
        teile.append(
            '<section class="abschnitt"><header><h2>%s</h2>'
            '<p class="stand"><b>%d</b> offen · <b>%d</b> erledigt</p></header>'
            '<ul class="punkte">%s</ul></section>'
            % (html.escape(name), len(gruppe['offen']), len(gruppe['fertig']),
               ''.join(zeilen)))

    seite = VORLAGE % {
        'datum': HEUTE,
        'fertig': zahl['pass'],
        'offen': zahl['fail'],
        'ungeprueft': zahl['open'],
        'gesamt': sum(zahl.values()),
        'abschnitte': ''.join(teile),
    }
    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(seite, encoding='utf-8')
    print('  %d erledigt · %d offen · %d ungeprüft → %s'
          % (zahl['pass'], zahl['fail'], zahl['open'], ZIEL))


VORLAGE = '''<title>Prüfstand Lunivo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap">
<style>
  /* Die Schrift ist Atkinson Hyperlegible — vom Braille Institute für
     Menschen gemacht, die Buchstaben schwer auseinanderhalten. Für einen
     Prüfbogen, der von einem Legastheniker gelesen wird, ist das keine
     Geschmacksfrage. Die Farben sind SEINE aus FARBEN in programm.js. */
  :root{
    --grund:#FBFAF7; --blatt:#FFFFFF; --rand:#E4E0D8;
    --schrift:#14181C; --schrift-2:#5F6B74;
    --gruen:#1F7A5A; --rot:#B5563F; --blau:#2F6FB5;
    --schatten:0 1px 2px rgba(20,24,28,.06), 0 6px 18px rgba(20,24,28,.05);
  }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      --grund:#14181C; --blatt:#1B2026; --rand:#2C333A;
      --schrift:#E6E9EC; --schrift-2:#95A1AB;
      --gruen:#4FB48A; --rot:#E08469; --blau:#6BA4E0;
      --schatten:0 1px 2px rgba(0,0,0,.4), 0 6px 18px rgba(0,0,0,.3);
    }
  }
  :root[data-theme="dark"]{
    --grund:#14181C; --blatt:#1B2026; --rand:#2C333A;
    --schrift:#E6E9EC; --schrift-2:#95A1AB;
    --gruen:#4FB48A; --rot:#E08469; --blau:#6BA4E0;
    --schatten:0 1px 2px rgba(0,0,0,.4), 0 6px 18px rgba(0,0,0,.3);
  }

  *{box-sizing:border-box}
  body{
    margin:0; background:var(--grund); color:var(--schrift);
    font:400 17px/1.65 "Atkinson Hyperlegible", "Noto Sans", system-ui, sans-serif;
    letter-spacing:.005em;
  }
  .rand{max-width:980px; margin:0 auto; padding:40px 24px 80px}

  header.kopf{display:flex; flex-direction:column; gap:6px; margin-bottom:28px}
  .kopf h1{margin:0; font-size:2.1rem; line-height:1.2; text-wrap:balance}
  .kopf .wann{color:var(--schrift-2); font-size:.95rem}

  .zahlen{
    display:grid; gap:14px; margin:0 0 36px;
    grid-template-columns:repeat(auto-fit, minmax(190px, 1fr));
  }
  .kachel{
    background:var(--blatt); border:1px solid var(--rand); border-radius:10px;
    padding:18px 20px; box-shadow:var(--schatten);
    display:flex; flex-direction:column; gap:2px;
  }
  .kachel b{font-size:2.4rem; line-height:1; font-variant-numeric:tabular-nums}
  .kachel span{color:var(--schrift-2); font-size:.92rem}
  .kachel--fertig b{color:var(--gruen)}
  .kachel--offen b{color:var(--rot)}

  .balken{
    display:flex; height:12px; border-radius:99px; overflow:hidden;
    border:1px solid var(--rand); margin:-14px 0 38px; background:var(--blatt);
  }
  .balken i{display:block}
  .balken .b-fertig{background:var(--gruen)}
  .balken .b-offen{background:var(--rot)}
  .balken .b-rest{background:var(--rand)}

  .abschnitt{margin:0 0 34px}
  .abschnitt header{
    display:flex; align-items:baseline; justify-content:space-between;
    gap:16px; flex-wrap:wrap;
    border-bottom:2px solid var(--rand); padding-bottom:7px; margin-bottom:14px;
  }
  .abschnitt h2{
    margin:0; font-size:1.02rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.09em; color:var(--schrift-2);
  }
  .stand{margin:0; color:var(--schrift-2); font-size:.9rem}
  .stand b{color:var(--schrift); font-variant-numeric:tabular-nums}

  .punkte{list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:10px}
  .punkt{
    display:flex; gap:14px; align-items:flex-start;
    background:var(--blatt); border:1px solid var(--rand); border-radius:9px;
    padding:14px 16px;
  }
  .punkt h3{margin:0 0 4px; font-size:1.06rem; line-height:1.35}
  .punkt p{margin:0 0 4px; max-width:66ch}
  .punkt p:last-child{margin-bottom:0}
  .marke{
    flex:0 0 22px; height:22px; margin-top:3px; border-radius:50%%;
    display:grid; place-items:center; font-size:.82rem; font-weight:700;
  }
  .punkt--fertig .marke{background:var(--gruen); color:var(--blatt)}
  .punkt--offen .marke{border:2px solid var(--rot)}
  .seins{color:var(--schrift-2); font-style:italic}
  .meins{color:var(--schrift)}
  .bilder{color:var(--blau); font-size:.9rem}

  .fuss{margin-top:44px; color:var(--schrift-2); font-size:.92rem; max-width:66ch}
</style>

<div class="rand">
  <header class="kopf">
    <h1>Was steht, und was noch nicht</h1>
    <p class="wann">Stand %(datum)s · aus deinem Prüfbogen, %(gesamt)d Punkte</p>
  </header>

  <div class="zahlen">
    <div class="kachel kachel--fertig"><b>%(fertig)d</b><span>erledigt</span></div>
    <div class="kachel kachel--offen"><b>%(offen)d</b><span>offen — von dir gemeldet</span></div>
    <div class="kachel"><b>%(ungeprueft)d</b><span>von dir noch nicht geprüft</span></div>
  </div>
  <div class="balken" role="img" aria-label="%(fertig)d erledigt, %(offen)d offen, %(ungeprueft)d ungeprüft">
    <i class="b-fertig" style="flex:%(fertig)d"></i>
    <i class="b-offen" style="flex:%(offen)d"></i>
    <i class="b-rest" style="flex:%(ungeprueft)d"></i>
  </div>

  %(abschnitte)s

  <p class="fuss">Die Abschnitte stehen nach Anzahl der offenen Punkte —
  oben, was noch aussteht. Kursiv steht deine Notiz aus dem Bogen,
  darunter bei den erledigten, was daran gemacht wurde. Die Punkte, die
  du noch nicht geprüft hast, stehen nur in der Zählung; sie sind keine
  ausstehende Arbeit.</p>
</div>
'''


if __name__ == '__main__':
    main()
