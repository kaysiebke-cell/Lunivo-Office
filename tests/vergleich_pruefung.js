// Führt oberflaeche/js/pruefung.js unverändert in Node aus und gibt zu jedem Satz
// (eine JSON-Zeile je Fall auf stdin) die Funde aus — Gegenstück zu native_qt/services/pruefung.py.
const fs = require('fs'), path = require('path');
const wurzel = path.resolve(__dirname, '..');
const regeln = fs.readFileSync(path.join(wurzel, 'oberflaeche/daten/regeln.js'), 'utf8');
const quelle = fs.readFileSync(path.join(wurzel, 'oberflaeche/js/pruefung.js'), 'utf8')
  .replace('let WOERTERBUCH_GROSS = null;', '');
const woerter = new Set(fs.readFileSync(path.join(wurzel, 'oberflaeche/daten/woerter.txt'), 'utf8').split('\n'));
const bauen = new Function('WOERTERBUCH_GROSS', regeln + '\n' + quelle + '\nreturn Pruefung;');
const P = bauen(woerter);
for (const zeile of fs.readFileSync(0, 'utf8').split('\n').filter((z) => z.length)) {
  const e = JSON.parse(zeile);
  P.Gelernt.daten = e.gelernt || { woerter: {}, inRuhe: {} };
  const funde = P.findeProbleme(e.text).map((f) => ({ von: f.von, bis: f.bis, alt: f.alt, neu: f.neu, grund: f.grund, art: f.art }));
  process.stdout.write(JSON.stringify(funde) + '\n');
}
