/* ============================================================
   Prüflauf: Zeigt jeder KI-Knopf wirklich auf eine Funktion?

       node oberflaeche/js/ki-knoepfe.test.js

   Ein Knopf, der im HTML steht und einen Klick-Handler hat, der aber eine
   Funktion ruft, die KIteil nie herausgibt — den gibt es, ohne dass der
   Browser meckert. Der Klick landet in einem stillen TypeError, den nur
   die Konsole sieht; für den Menschen ist es „ein Knopf ohne Funktion".
   Genau das prüft dieser Lauf, an allen drei Stellen, an denen ein
   KI-Befehl auftauchen kann: der Knopfleiste unten, dem Menü „KI" und
   dem Register „Schreibhilfe" (daten/register.js).

   Er liest nur Quelltext, öffnet kein Fenster — wie die Prüfläufe daneben.
   ============================================================ */
'use strict';

const fs = require('fs');
const path = require('path');
const { pruefhelferBauen } = require('./pruefhelfer.js');
const { stimmt, gleich, schluss } = pruefhelferBauen();

const lies = (datei) => fs.readFileSync(path.join(__dirname, datei), 'utf8');

const html     = lies('../index.html');
const kiteil   = lies('kiteil.js');
const programm = lies('programm.js');
const register = lies('../daten/register.js');

/* ---- Was KIteil tatsächlich herausgibt ----

   Der Rückgabeblock steht als Letztes in KI_BAUEN — „return {" kommt in
   der Datei kein zweites Mal in dieser Form vor. Ab da bis zum Dateiende
   reicht als Text, in dem nach Namen gesucht wird; ihn exakt zu
   parsen wäre mehr, als die Frage braucht. */
const rueckgabeStelle = kiteil.lastIndexOf('\nreturn {');
stimmt(rueckgabeStelle !== -1, 'KI_BAUEN hat einen Rückgabeblock');
const rueckgabe = rueckgabeStelle !== -1 ? kiteil.slice(rueckgabeStelle) : '';
const gibtHeraus = (name) => new RegExp('\\b' + name + '\\b').test(rueckgabe);

/* ---- Die Knopfleiste unten (KI_KNOEPFE in kiteil.js) ---- */
console.log('\n=== Die Knopfleiste ===');
const knoepfe = [...kiteil.matchAll(/\[\s*'(btn-[\w-]+)'\s*,\s*'([^']+)'\s*\]/g)]
  .map(([, id, name]) => ({ id, name }));
stimmt(knoepfe.length >= 4, 'mindestens vier Knöpfe in KI_KNOEPFE gefunden (sind '
  + knoepfe.length + ')');

for (const { id, name } of knoepfe) {
  console.log('  -- ' + name + ' (' + id + ') --');
  stimmt(new RegExp('id="' + id + '"').test(html), '  steht als Knopf im HTML');

  const klick = programm.match(new RegExp(
    "\\$\\('" + id + "'\\)\\.addEventListener\\('click',\\s*\\(\\)\\s*=>\\s*KIteil\\.(\\w+)\\("));
  stimmt(!!klick, '  hat einen Klick-Handler in programm.js');
  if (klick) stimmt(gibtHeraus(klick[1]),
    '  Klick ruft KIteil.' + klick[1] + '() — die gibt es auch');
}

/* ---- Der feste „+"-Knopf für eigene Assistenten ---- */
console.log('\n=== „+ Eigener Assistent" ===');
stimmt(/id="ki-eigene-neu"/.test(html), 'steht als Knopf im HTML');
const neuKlick = programm.match(
  /\$\('ki-eigene-neu'\)\.addEventListener\('click',\s*\(\)\s*=>\s*KIteil\.(\w+)\(/);
stimmt(!!neuKlick, 'hat einen Klick-Handler in programm.js');
if (neuKlick) stimmt(gibtHeraus(neuKlick[1]),
  'Klick ruft KIteil.' + neuKlick[1] + '() — die gibt es auch');

/* ---- Das Menü „KI" (in programm.js) ---- */
console.log('\n=== Das Menü „KI" ===');
const menuStelle = programm.indexOf("{ name: 'KI', unter: [");
stimmt(menuStelle !== -1, 'das Menü „KI" steht in programm.js');
if (menuStelle !== -1) {
  const menuEnde = programm.indexOf('\n    ] },', menuStelle);
  const menuBlock = programm.slice(menuStelle, menuEnde === -1 ? undefined : menuEnde);
  const eintraege = [...menuBlock.matchAll(/\{\s*name:\s*'([^']+)',\s*tun:\s*\(\)\s*=>\s*KIteil\.(\w+)\(/g)];
  stimmt(eintraege.length >= 2, 'hat mindestens zwei Einträge, die KIteil rufen (sind '
    + eintraege.length + ')');
  for (const [, name, fn] of eintraege) {
    stimmt(gibtHeraus(fn), '„' + name + '“ ruft KIteil.' + fn + '() — die gibt es auch');
  }
}

/* ---- Das Register „Schreibhilfe" (daten/register.js) ----

   Dort steht nicht KIteil.xxx(), sondern w.xxx() — „w" ist die Umgebung,
   die REGISTER_BAUEN(B, {...}) in programm.js mitbekommt. Ein Name, der
   dort im Register aufgerufen wird, muss in dieser Umgebung stehen UND
   von dort aus wieder bei einer echten KIteil-Funktion ankommen — sonst
   zeigt der Ribbon-Knopf ins Leere, genauso still wie oben. */
console.log('\n=== Das Register „Schreibhilfe" (w.kiXxx) ===');
const umgebungStelle = programm.indexOf('const REGISTER = REGISTER_BAUEN(B, {');
stimmt(umgebungStelle !== -1, 'REGISTER_BAUEN(B, {...}) steht in programm.js');
const umgebungEnde = umgebungStelle === -1 ? -1 : programm.indexOf('\n});', umgebungStelle);
const umgebungBlock = umgebungStelle === -1 ? ''
  : programm.slice(umgebungStelle, umgebungEnde === -1 ? undefined : umgebungEnde);
const umgebung = new Map(
  [...umgebungBlock.matchAll(/(\w+):\s*\([^)]*\)\s*=>\s*KIteil\.(\w+)\(/g)]
    .map(([, key, fn]) => [key, fn]));

const registerAufrufe = [...register.matchAll(/w\.(ki\w+|assistentErstellen)\(\)/g)].map((m) => m[1]);
stimmt(registerAufrufe.length >= 1, 'das Register ruft mindestens eine KI-Funktion über w auf (sind '
  + registerAufrufe.length + ')');
for (const name of new Set(registerAufrufe)) {
  const hatUmgebung = umgebung.has(name);
  stimmt(hatUmgebung, 'w.' + name + '() steht in der Umgebung, die programm.js REGISTER_BAUEN mitgibt');
  if (hatUmgebung) stimmt(gibtHeraus(umgebung.get(name)),
    'w.' + name + '() ruft KIteil.' + umgebung.get(name) + '() — die gibt es auch');
}

schluss();
