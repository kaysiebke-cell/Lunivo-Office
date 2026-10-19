// Prüfer-Helfer: liest Text aus stdin, gibt die Funde der Schreibhilfe als JSON aus.
// Nutzt die vorhandene Prüflogik (daten/regeln.js, js/pruefung.js) unverändert.
'use strict';
const vm = require('vm'), fs = require('fs'), path = require('path');
const wurzel = path.join(__dirname, '..', 'oberflaeche');
const c = { console };
vm.createContext(c);
vm.runInContext(fs.readFileSync(path.join(wurzel, 'daten/regeln.js'), 'utf8') + '\n;this.REGELDATEN=REGELDATEN;', c);
vm.runInContext(fs.readFileSync(path.join(wurzel, 'js/pruefung.js'), 'utf8') + '\n;this.Pruefung=Pruefung;', c);
let eingabe = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (d) => { eingabe += d; });
process.stdin.on('end', () => {
  let funde = [];
  try { funde = c.Pruefung.findeProbleme(eingabe) || []; } catch (e) { process.stderr.write(String(e)); }
  process.stdout.write(JSON.stringify(funde));
});
