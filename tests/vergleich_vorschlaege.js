// Führt oberflaeche/js/pruefung.js aus und gibt für jedes Wort (JSON-Zeile auf stdin) Vorschläge, Klangschlüssel und „klingt wie“ aus.
const fs = require('fs'), path = require('path');
const wurzel = path.resolve(__dirname, '..');
const regeln = fs.readFileSync(path.join(wurzel, 'oberflaeche/daten/regeln.js'), 'utf8');
const quelle = fs.readFileSync(path.join(wurzel, 'oberflaeche/js/pruefung.js'), 'utf8').replace('let WOERTERBUCH_GROSS = null;', '');
const woerter = new Set(fs.readFileSync(path.join(wurzel, 'oberflaeche/daten/woerter.txt'), 'utf8').split('\n'));
const P = new Function('WOERTERBUCH_GROSS', regeln + '\n' + quelle + '\nreturn Pruefung;')(woerter);
for (const zeile of fs.readFileSync(0, 'utf8').split('\n').filter((z) => z.length)) {
  const e = JSON.parse(zeile);
  P.Gelernt.daten = e.gelernt || { woerter: {}, inRuhe: {} };
  process.stdout.write(JSON.stringify({ v: P.vorschlaegeFuer(e.wort), k: P.koelnerPhonetik(e.wort), kw: P.klingtWie(e.wort) }) + '\n');
}
