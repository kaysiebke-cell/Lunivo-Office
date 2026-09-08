/* ============================================================
   Prüfläufe für die Sprachbrücke.

   Laufen ohne das Fenster:  node oberflaeche/js/language-bridge.test.js

   Geprüft wird, was die Brücke selbst tut — den Zustand. Was sie an
   pruefung.js weiterreicht, wird hier durch einen gestellten Prüfer
   ersetzt: Der echte braucht REGELDATEN und ein Wörterbuch von viereinhalb
   Megabyte, und darum geht es hier nicht.
   ============================================================ */
'use strict';

let bestanden = 0;
const stimmt = (bedingung, was) => {
  if (!bedingung) { console.error('  FEHLT: ' + was); process.exitCode = 1; return; }
  bestanden++;
  console.log('  ok   ' + was);
};
const gleich = (ist, soll, was) =>
  stimmt(ist === soll, was + (ist === soll ? '' : '  (ist ' + ist + ', soll ' + soll + ')'));

/* Ein gestellter Prüfer. Er meldet, was ihm vorgelegt wird. */
let naechsteFunde = [];
global.Pruefung = {
  findeProbleme: () => naechsteFunde,
  Gelernt: {
    daten: { woerter: {}, inRuhe: {} },
    wort:   (w) => global.Pruefung.Gelernt.daten.woerter[String(w).toLowerCase()] || null,
    inRuhe: (w) => !!global.Pruefung.Gelernt.daten.inRuhe[String(w).toLowerCase()],
  },
};

const fund = (von, bis, alt, neu, wortEbene = true, art = 'fehler') =>
  ({ von, bis, alt, neu, grund: 'weil', art, wortEbene });

const { SprachBruecke } = require('./language-bridge.js');

console.log('\nSprachbrücke\n');

/* ---- Der Anfang ---- */
console.log('Der Anfang');
{
  const b = new SprachBruecke();
  gleich(b.sprache, 'de-DE', 'spricht zunächst Deutsch');
  gleich(b.fassung, 0, 'Fassung null');
  gleich(b.stand, 'ruht', 'ruht');
  gleich(b.offeneFehler().length, 0, 'kennt noch keinen Fehler');
}

/* ---- Der Text ---- */
console.log('\nDer Text');
{
  const b = new SprachBruecke();
  b.textSetzen('Ein Satz.');
  gleich(b.fassung, 1, 'neuer Text, neue Fassung');
  gleich(b.stand, 'veraltet', 'Geprüftes gilt nicht mehr');

  b.textSetzen('Ein Satz.');
  gleich(b.fassung, 1, 'derselbe Text zählt nicht als Änderung');

  b.textSetzen('Ein anderer Satz.');
  gleich(b.fassung, 2, 'anderer Text, nächste Fassung');
}

/* ---- Prüfen ---- */
console.log('\nPrüfen');
{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  const funde = b.pruefen('weiss der Himmel');

  gleich(funde.length, 1, 'gibt den Fund zurück');
  gleich(funde[0].alt, 'weiss', 'und zwar unverändert, wie das Programm ihn kennt');
  gleich(b.stand, 'fertig', 'danach: fertig');
  gleich(b.offeneFehler().length, 1, 'ein offener Fehler');
  gleich(b.offeneFehler()[0].quelle, 'rechtschreibung',
         'ein Wortfund zählt als Rechtschreibung');
  gleich(b.offeneFehler()[0].vorschlaege[0], 'weiß', 'mit Vorschlag');
}

{
  const b = new SprachBruecke();
  naechsteFunde = [fund(3, 6, 'das', 'dass', false, 'tipp')];
  b.pruefen('Ich das er kommt');
  gleich(b.offeneFehler()[0].quelle, 'grammatik',
         'was kein Wortfund ist, zählt als Grammatik');
}

/* ---- Übergehen ---- */
console.log('\nÜbergehen');
{
  const b = new SprachBruecke();
  const einer = fund(0, 5, 'weiss', 'weiß');
  naechsteFunde = [einer];

  b.pruefen('weiss der Himmel');
  gleich(b.offeneFehler().length, 1, 'erst da');

  stimmt(b.wegwinkenFund(einer), 'übergangen');
  gleich(b.offeneFehler().length, 0, 'dann weg');

  /* Und beim nächsten Mal nicht wieder — das ist der Punkt. */
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  const nochmal = b.pruefen('weiss der Himmel');
  gleich(nochmal.length, 0, 'kommt beim nächsten Prüfen nicht wieder');
}

{
  const b = new SprachBruecke();
  const einer = fund(0, 5, 'weiss', 'weiß');
  naechsteFunde = [einer];
  b.pruefen('weiss der Himmel');
  b.wegwinkenFund(einer);

  /* Ein anderes Wort ist ein anderer Fall. */
  naechsteFunde = [fund(0, 5, 'gross', 'groß')];
  gleich(b.pruefen('gross').length, 1, 'ein anderes Wort kommt weiter');
}

/* ---- Fehler an einer Stelle ---- */
console.log('\nFehler an einer Stelle');
{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  b.pruefen('weiss der Himmel');

  gleich(b.fehlerBei(0, 20).length, 1, 'wird gefunden, wo er liegt');
  gleich(b.fehlerBei(30, 40).length, 0, 'und nicht, wo er nicht liegt');
  gleich(b.fehlerBei(3, 8).length, 1, 'auch bei teilweiser Überschneidung');
}

/* ---- Wörter: gefragt wird das Gedächtnis ---- */
console.log('\nWörter');
{
  const b = new SprachBruecke();
  stimmt(!b.kenntWort('Lunivo'), 'ein fremdes Wort kennt sie nicht');

  global.Pruefung.Gelernt.daten.inRuhe['lunivo'] = true;
  stimmt(b.kenntWort('Lunivo'), 'was in Ruhe bleiben soll, kennt sie');
  stimmt(b.kenntWort('lunivo'), 'groß oder klein ist dabei gleich');
  global.Pruefung.Gelernt.daten.inRuhe = {};
}

/* ---- Späte Antworten ---- */
console.log('\nSpäte Antworten');
{
  const b = new SprachBruecke();
  naechsteFunde = [];
  b.pruefen('Ein Satz.');
  const alteFassung = b.fassung;
  const alterLauf = b.laufNr;

  b.textSetzen('Ein ganz anderer Satz.');       // dazwischen wurde getippt

  b.kiFragen(alteFassung, alterLauf);
  gleich(b.offeneFehler().length, 0,
         'eine Antwort zu einer alten Fassung wird verworfen');
}

/* ---- Ein stolpernder Prüfer ---- */
console.log('\nEin stolpernder Prüfer');
{
  const b = new SprachBruecke();
  const heil = global.Pruefung.findeProbleme;
  global.Pruefung.findeProbleme = () => { throw new Error('kaputt'); };

  const funde = b.pruefen('Ein Satz.');
  gleich(funde.length, 0, 'reißt den Sprachstand nicht mit');
  gleich(b.stand, 'fertig', 'das Programm läuft weiter');

  global.Pruefung.findeProbleme = heil;
}

/* ---- Die Auskunft ---- */
console.log('\nDie Auskunft');
{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  b.pruefen('weiss der Himmel');
  const a = b.auskunft();
  gleich(a.stand, 'fertig', 'sagt den Stand');
  gleich(a.offen, 1, 'sagt, wie viele offen sind');
  gleich(a.fassung, 1, 'sagt die Fassung');
}

console.log('\n' + bestanden + ' Prüfungen bestanden'
            + (process.exitCode ? ' — aber nicht alle.' : '.') + '\n');
