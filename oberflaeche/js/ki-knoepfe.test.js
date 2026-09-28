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
const pfad = require('path');
const { pruefhelferBauen } = require('./pruefhelfer.js');
const { stimmt, gleich, schluss } = pruefhelferBauen();

const lies = (datei) => fs.readFileSync(pfad.join(__dirname, datei), 'utf8');

const html     = lies('../index.html');
const kiteil   = lies('kiteil.js');
const programm = lies('programm.js');
const register = lies('../daten/register.js');
const einst    = lies('einstellungen.js');

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

/* ---- Eigene Assistenten — jetzt ausschließlich in den Optionen ----

   Seit „Eigene Assistenten" aus der Seitenleiste verschwunden ist (Anlegen,
   Liste, Entfernen ausschließlich über Optionen ▸ Schreibhilfe und KI),
   liegen Knopf und Klick-Handler in einstellungen.js statt in programm.js.
   Der Weg dorthin führt über „griffe" — programm.js reicht KIteil.xxx erst
   bei Einstellungen.verbinde({...}) hinein, siehe unten. */
console.log('\n=== „Neuen Assistenten erstellen …" (Optionen) ===');
stimmt(/id="einst-assistenten-neu"/.test(html), 'steht als Knopf im HTML');
stimmt(/id="einst-assistenten-liste"/.test(html), 'die Liste hat einen Platz im HTML');

const neuKlick = einst.match(
  /\$\('einst-assistenten-neu'\)\.addEventListener\('click',\s*\(\)\s*=>\s*griffe\.(\w+)\(/);
stimmt(!!neuKlick, 'hat einen Klick-Handler in einstellungen.js, der über „griffe" geht');

const startKlick = einst.match(/griffe\.(assistentAusfuehren)\(assistent\)/);
stimmt(!!startKlick, 'der „Starten"-Knopf je Zeile ruft griffe.assistentAusfuehren(assistent)');

/* „griffe.xxx" ist nur ein Name, bis programm.js ihn bei
   Einstellungen.verbinde({...}) mit einer echten KIteil-Funktion
   verbindet — genau das prüfen die beiden Zeilen hier. */
const verbindeStelle = programm.indexOf('Einstellungen.verbinde({');
stimmt(verbindeStelle !== -1, 'Einstellungen.verbinde({...}) steht in programm.js');
const verbindeEnde = verbindeStelle === -1 ? -1 : programm.indexOf('\n});', verbindeStelle);
const verbindeBlock = verbindeStelle === -1 ? ''
  : programm.slice(verbindeStelle, verbindeEnde === -1 ? undefined : verbindeEnde);

for (const [label, griffName] of [['Anlegen', neuKlick && neuKlick[1]],
                                    ['Starten', startKlick && startKlick[1]]]) {
  if (!griffName) continue;
  const weitergereicht = verbindeBlock.match(
    new RegExp(griffName + ':\\s*\\([^)]*\\)\\s*=>\\s*KIteil\\.(\\w+)\\('));
  stimmt(!!weitergereicht, '„' + label + '": griffe.' + griffName
    + ' steht bei Einstellungen.verbinde und zeigt auf KIteil');
  if (weitergereicht) stimmt(gibtHeraus(weitergereicht[1]),
    '„' + label + '": KIteil.' + weitergereicht[1] + '() — die gibt es auch');
}

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
   von dort aus wieder bei einer echten Funktion ankommen — sei es
   KIteil (die meisten KI-Knöpfe) oder ein anderes Modul wie Einstellungen
   („KI-Einstellungen" öffnet die Optionsseite direkt, ruft also nicht
   KIteil). Sonst zeigt der Ribbon-Knopf ins Leere, genauso still wie oben. */
console.log('\n=== Das Register „Schreibhilfe" (w.kiXxx) ===');
const umgebungStelle = programm.indexOf('const REGISTER = REGISTER_BAUEN(B, {');
stimmt(umgebungStelle !== -1, 'REGISTER_BAUEN(B, {...}) steht in programm.js');
const umgebungEnde = umgebungStelle === -1 ? -1 : programm.indexOf('\n});', umgebungStelle);
const umgebungBlock = umgebungStelle === -1 ? ''
  : programm.slice(umgebungStelle, umgebungEnde === -1 ? undefined : umgebungEnde);
/* Jeder Eintrag als [griffName, modul, funktion] — „modul" ist z. B.
   „KIteil" oder „Einstellungen", je nachdem, wohin der Pfeil zeigt. */
const umgebung = new Map(
  [...umgebungBlock.matchAll(/(\w+):\s*\([^)]*\)\s*=>\s*(\w+)\.(\w+)\(/g)]
    .map(([, key, modul, fn]) => [key, { modul, fn }]));

/* Existiert die Funktion wirklich in ihrem Modul? Für KIteil zählt der
   Rückgabeblock oben (gibtHeraus); für alle anderen genügt der Beleg,
   dass „function fn(" oder „fn:" irgendwo in dessen Quelltext steht —
   das Modul selbst zu parsen wäre mehr, als die Frage braucht. */
const quellen = { Einstellungen: einst, KIteil: kiteil, Chat: lies('chat.js'), B: programm };
function gibtWirklichHeraus(modul, fn) {
  if (modul === 'KIteil') return gibtHeraus(fn);
  const quelle = quellen[modul];
  if (!quelle) return null;                    // unbekanntes Modul — nicht geprüft, nicht verneint
  return new RegExp('\\bfunction ' + fn + '\\(|\\b' + fn + ':').test(quelle);
}

/* Nur die Gruppe „KI" im Register — dieselbe Eingrenzung wie beim Menü
   oben. Andernorts im Register stehen genauso parameterlose w.xxx() (Zoom,
   Seitenrand, …), die mit KI nichts zu tun haben und nicht hierher
   gehören; ihre eigene Verdrahtung ist nicht die Frage dieses Laufs. */
const registerKiStelle = register.indexOf("['KI', [");
stimmt(registerKiStelle !== -1, "die Gruppe 'KI' steht in register.js");
const registerKiEnde = registerKiStelle === -1 ? -1 : register.indexOf("]],\n", registerKiStelle);
const registerKiBlock = registerKiStelle === -1 ? ''
  : register.slice(registerKiStelle, registerKiEnde === -1 ? undefined : registerKiEnde);

const registerAufrufe = [...registerKiBlock.matchAll(/w\.(\w+)\(\)/g)].map((m) => m[1]);
stimmt(registerAufrufe.length >= 1, 'die Gruppe „KI" ruft mindestens eine parameterlose Funktion über w auf (sind '
  + registerAufrufe.length + ')');
for (const name of new Set(registerAufrufe)) {
  const eintrag = umgebung.get(name);
  const hatUmgebung = !!eintrag;
  stimmt(hatUmgebung, 'w.' + name + '() steht in der Umgebung, die programm.js REGISTER_BAUEN mitgibt');
  if (!hatUmgebung) continue;
  const gefunden = gibtWirklichHeraus(eintrag.modul, eintrag.fn);
  if (gefunden === null) {
    console.log('  ??   w.' + name + '() ruft ' + eintrag.modul + '.' + eintrag.fn
      + '() — unbekanntes Modul, nicht geprüft');
    continue;
  }
  stimmt(gefunden, 'w.' + name + '() ruft ' + eintrag.modul + '.' + eintrag.fn + '() — die gibt es auch');
}

schluss();
