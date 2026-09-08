'use strict';
(async () => {
/* ============================================================
   Prüfläufe für die Sprachbrücke.

   Laufen ohne das Fenster:  node oberflaeche/js/language-bridge.test.js

   Geprüft wird, was die Brücke selbst tut — den Zustand. Was sie an
   pruefung.js weiterreicht, wird hier durch einen gestellten Prüfer
   ersetzt: Der echte braucht REGELDATEN und ein Wörterbuch von viereinhalb
   Megabyte, und darum geht es hier nicht.
   ============================================================ */

const { pruefhelferBauen } = require('./pruefhelfer.js');
const { stimmt, gleich, schluss } = pruefhelferBauen();

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
  gleich(b.stand, 'fehler', 'der Stand sagt, dass etwas schiefging (§31)');
  stimmt(!!b.letzterFehler, 'und was es war');

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

/* ---- Die KI ---- */
console.log('\nDie KI');

/* Eine gestellte KI. Sie antwortet, wann wir es sagen. */
function kiStellen(funde, warten = 0) {
  global.KI = {
    verfuegbar: () => true,
    Gedaechtnis: { lies: () => ({ woerter: {}, inRuhe: {} }) },
    sprachfunde: async () => {
      if (warten) await new Promise((r) => setTimeout(r, warten));
      return { funde };
    },
  };
}

const kiFund = (von, bis, alt, neu, sicherheit = 0.8, art = 'grammatik') =>
  ({ von, bis, alt, neu, grund: 'weil die KI das sagt', art, sicherheit });

{
  const b = new SprachBruecke();
  naechsteFunde = [];
  kiStellen([kiFund(4, 7, 'ist', 'sind')]);
  b.pruefen('Das ist so.', true);
  await new Promise((r) => setTimeout(r, 20));
  gleich(b.offeneFehler().length, 1, 'ein KI-Fund kommt in den Fehlerstand');
  gleich(b.offeneFehler()[0].quelle, 'ki', 'und ist als KI-Fund erkennbar');
  gleich(b.offeneFehler()[0].sicherheit, 0.8, 'mit seiner Sicherheit');
  stimmt(!!b.offeneFehler()[0].fund, 'und in der Form, die das Programm kennt');
}

{
  const b = new SprachBruecke();
  naechsteFunde = [];
  kiStellen([kiFund(0, 3, 'Das', 'Dass', 0.95)]);
  b.pruefen('Das ist so.', true);
  await new Promise((r) => setTimeout(r, 20));
  gleich(b.offeneFehler()[0].art, 'fehler', 'ab 0,9 gilt es als sicher falsch');
}

{
  const b = new SprachBruecke();
  naechsteFunde = [];
  kiStellen([kiFund(0, 3, 'Das', 'Dies', 0.4, 'stil')]);
  b.pruefen('Das ist so.', true);
  await new Promise((r) => setTimeout(r, 20));
  gleich(b.offeneFehler()[0].art, 'hinweis', 'ein Stilvorschlag ist nur ein Hinweis');
}

console.log('\nEine späte Antwort der KI');
{
  const b = new SprachBruecke();
  naechsteFunde = [];
  kiStellen([kiFund(4, 7, 'ist', 'sind')], 60);
  b.pruefen('Das ist so.', true);
  b.textSetzen('Ein ganz anderer Text.');   // dazwischen wurde getippt
  await new Promise((r) => setTimeout(r, 140));
  gleich(b.offeneFehler().length, 0,
         'wird verworfen, wenn der Text sich geändert hat');
}

{
  const b = new SprachBruecke();
  naechsteFunde = [];
  kiStellen([kiFund(4, 7, 'ist', 'sind')], 60);
  b.pruefen('Das ist so.', true);
  b.pruefen('Das ist so.', true);                 // zweiter Lauf über denselben Text
  await new Promise((r) => setTimeout(r, 140));
  gleich(b.offeneFehler().length, 1,
         'ein überholter Lauf bringt seinen Fund nicht doppelt');
}

console.log('\nWörter, die der Mensch erlaubt hat');
{
  const b = new SprachBruecke();
  naechsteFunde = [];
  global.Pruefung.Gelernt.daten.inRuhe['lunivo'] = true;
  kiStellen([kiFund(0, 6, 'Lunivo', 'Luniva', 0.9)]);
  b.pruefen('Lunivo ist gut.', true);
  await new Promise((r) => setTimeout(r, 20));
  gleich(b.offeneFehler().length, 0, 'die KI darf sie nicht bemängeln');
  global.Pruefung.Gelernt.daten.inRuhe = {};
}

console.log('\nZwei Prüfer über derselben Stelle');
{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];       // Prüfer: sicher
  kiStellen([kiFund(0, 5, 'weiss', 'weiss?', 0.3)]);   // KI: unsicher
  b.pruefen('weiss der Himmel', true);
  await new Promise((r) => setTimeout(r, 20));

  gleich(b.offeneFehler().length, 1, 'wird zu einem Fehler zusammengeführt');
  const f = b.offeneFehler()[0];
  gleich(f.vorschlaege[0], 'weiß', 'der sicherere Vorschlag steht vorn');
  gleich(f.vorschlaege.length, 2, 'der andere geht nicht verloren');
  gleich(f.grund, 'weil', 'die Begründung kommt vom sichereren');
}

{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß', true, 'tipp')];   // 0,6
  kiStellen([kiFund(0, 5, 'weiss', 'weiß', 0.95)]);              // gleicher Vorschlag
  b.pruefen('weiss der Himmel', true);
  await new Promise((r) => setTimeout(r, 20));
  const f = b.offeneFehler()[0];
  gleich(f.vorschlaege.length, 1, 'derselbe Vorschlag zählt einmal');
  gleich(f.sicherheit, 0.95, 'die höhere Sicherheit gilt');
}

console.log('\nOhne Modell');
{
  const b = new SprachBruecke();
  naechsteFunde = [];
  global.KI = { verfuegbar: () => false };
  b.pruefen('Das ist so.', true);
  await new Promise((r) => setTimeout(r, 20));
  gleich(b.offeneFehler().length, 0, 'wird die KI gar nicht erst gefragt');
  gleich(b.stand, 'fertig', 'und das Prüfen läuft trotzdem durch');
}

console.log('\nEine stolpernde KI');
{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  global.KI = { verfuegbar: () => true,
                Gedaechtnis: { lies: () => ({ woerter: {}, inRuhe: {} }) },
                sprachfunde: async () => { throw new Error('kaputt'); } };
  const funde = b.pruefen('weiss der Himmel');
  await new Promise((r) => setTimeout(r, 20));
  gleich(funde.length, 1, 'die Funde des Prüfers bleiben stehen');
  gleich(b.stand, 'fertig', 'und der Stand ist in Ordnung');
}

console.log('\nWo hat sich der Text geändert?');
{
  const b = new SprachBruecke();
  b.textSetzen('Hallo Welt');
  b.geaendert = null;
  b.textSetzen('Hallo schöne Welt');
  gleich(b.geaendert.von, 6, 'vorn steht „Hallo " unverändert');
  gleich(b.geaendert.verschiebung, 7, 'sieben Zeichen sind dazugekommen');
}
{
  const b = new SprachBruecke();
  b.textSetzen('Ein Satz mit Fehler drin.');
  b.geaendert = null;
  b.textSetzen('Ein Satz drin.');
  stimmt(b.geaendert.verschiebung < 0, 'beim Löschen wird die Verschiebung negativ');
}
{
  const b = new SprachBruecke();
  b.textSetzen('abc');
  b.geaendert = null;
  b.textSetzen('abXc');
  b.textSetzen('abXYc');
  gleich(b.geaendert.von, 2, 'zwei Änderungen werden zu einer zusammengefasst');
  gleich(b.geaendert.verschiebung, 2, 'und die Verschiebungen addiert');
}

console.log('\nDer Sicherheitsrand');
{
  const b = new SprachBruecke();
  const lang = 'Satz eins. ' + 'x'.repeat(500) + '. Satz drei. Satz vier.';
  b.textSetzen(lang);
  b.geaendert = null;
  b.textSetzen(lang.replace('Satz drei', 'Satz DREI'));
  const bereich = b.pruefbereich();
  stimmt(bereich !== null, 'es gibt einen Bereich');
  stimmt(bereich.bis - bereich.von >= 200, 'er ist mindestens 200 Zeichen breit');
  stimmt(bereich.von === 0 || '.!?\n'.includes(lang[bereich.von - 1]),
         'er beginnt an einer Satzgrenze');
}

console.log('\nGeprüft wird nur der Bereich');
{
  const b = new SprachBruecke();
  const text = 'Hier steht weiss. ' + 'Fülltext. '.repeat(40) + 'Und hier gross.';
  naechsteFunde = [fund(11, 16, 'weiss', 'weiß'),
                   fund(text.length - 6, text.length - 1, 'gross', 'groß')];
  b.pruefen(text);
  gleich(b.offeneFehler().length, 2, 'erst beide Funde');

  /* Am Ende etwas ändern: Der Fund vorn darf nicht neu gesucht werden. */
  const neuerText = text.replace('Und hier gross.', 'Und hier gross gemacht.');
  b.textSetzen(neuerText);
  naechsteFunde = [fund(neuerText.length - 14, neuerText.length - 9, 'gross', 'groß')];
  b.pruefen();
  const offen = b.offeneFehler();
  gleich(offen.length, 2, 'beide stehen weiter');
  stimmt(offen.some((f) => f.text === 'weiss'), 'der vordere blieb erhalten');
  gleich(neuerText.slice(offen.find((f) => f.text === 'weiss').von,
                         offen.find((f) => f.text === 'weiss').bis), 'weiss',
         'und steht noch an seiner Stelle');
}

console.log('\nVerschiebung nach einer Einfügung davor');
{
  const b = new SprachBruecke();
  /* Lang genug, dass der Sicherheitsrand vorn nicht bis hinten reicht —
     sonst würde der hintere Fund ohnehin neu gesucht. */
  const text = 'Anfang. ' + 'Ein Satz zum Füllen. '.repeat(30) + 'Hier steht gross am Ende.';
  const stelle = text.indexOf('gross');
  naechsteFunde = [fund(stelle, stelle + 5, 'gross', 'groß')];
  b.pruefen(text);
  gleich(b.offeneFehler().length, 1, 'ein Fund hinten');

  /* Ganz vorn etwas einfügen. */
  const neuerText = 'Neu davor. ' + text;
  b.textSetzen(neuerText);
  naechsteFunde = [];                       // im geprüften Bereich vorn nichts
  b.pruefen();
  const f = b.offeneFehler()[0];
  stimmt(!!f, 'der Fund hinten ist noch da');
  gleich(neuerText.slice(f.von, f.bis), 'gross', 'und zeigt weiter auf dasselbe Wort');
}

console.log('\nMit KI wird immer alles geprüft');
{
  const b = new SprachBruecke();
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  b.pruefen('weiss der Himmel');
  b.textSetzen('weiss der Himmel. Und mehr.');
  global.KI = { verfuegbar: () => false };
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  b.pruefen(undefined, true);
  gleich(b.offeneFehler().length, 1, 'die volle Prüfung bleibt möglich');
}

console.log('\nDie Griffe aus §4');
{
  const b = new SprachBruecke();
  const gedaechtnis = { woerter: {}, inRuhe: {} };
  global.KI = { verfuegbar: () => false,
                Gedaechtnis: { lies: () => gedaechtnis, schreib: (g) => Object.assign(gedaechtnis, g) } };
  naechsteFunde = [fund(0, 6, 'Lunivo', 'Luniva')];
  b.pruefen('Lunivo ist gut.');
  gleich(b.offeneFehler().length, 1, 'erst wird das Wort bemängelt');

  stimmt(b.benutzerwortHinzufuegen('Lunivo'), 'es lässt sich erlauben (§9)');
  gleich(b.offeneFehler().length, 0, 'dann ist es nicht mehr angestrichen');
  stimmt(b.benutzerwoerter().includes('lunivo'), 'und steht bei den erlaubten');
  gleich(b.stand, 'veraltet', 'das Geprüfte gilt nicht mehr');

  stimmt(b.benutzerwortEntfernen('Lunivo'), 'und wieder zurücknehmen');
  stimmt(!b.benutzerwoerter().includes('lunivo'), 'dann ist es wieder fremd');
}
{
  const b = new SprachBruecke();
  const gedaechtnis = { woerter: {}, inRuhe: {} };
  global.KI = { verfuegbar: () => false,
                Gedaechtnis: { lies: () => gedaechtnis, schreib: (g) => Object.assign(gedaechtnis, g) } };
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  b.pruefen('weiss der Himmel');
  const id = b.offeneFehler()[0].id;

  stimmt(b.annehmen(id), 'ein Vorschlag lässt sich annehmen (§26)');
  gleich(b.offeneFehler().length, 0, 'danach ist der Fehler weg');
  stimmt(b.benutzerwoerter().includes('weiß'), 'und der Vorschlag gilt als erlaubtes Wort');
}
{
  const b = new SprachBruecke();
  global.KI = { verfuegbar: () => false };
  naechsteFunde = [fund(0, 5, 'weiss', 'weiß')];
  b.pruefen('weiss der Himmel');
  const id = b.offeneFehler()[0].id;

  stimmt(b.korrekturAnwenden(id, 'weiß', 'weiß der Himmel'),
         'eine Korrektur lässt sich anwenden (§23)');
  gleich(b.fehler.find((f) => f.id === id).stand, 'erledigt', 'der Fehler gilt als erledigt');
  gleich(b.stand, 'veraltet', 'und der Text muss neu geprüft werden');
}
{
  const b = new SprachBruecke();
  b.textSetzen('Ein Satz.');
  const k = b.kontext();
  stimmt(!!k.sprache && typeof k.fassung === 'number', 'der Sprachkontext steht bereit (§3)');
  stimmt(Array.isArray(k.benutzerwoerter), 'mit den erlaubten Wörtern');
  stimmt(Array.isArray(k.fehler), 'und den offenen Fehlern');
}

schluss();

})();
