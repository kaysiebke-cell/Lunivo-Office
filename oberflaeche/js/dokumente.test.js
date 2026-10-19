/* ============================================================
   Prüflauf für die Dokumentverwaltung — ohne Fenster.

       node oberflaeche/js/dokumente.test.js

   Geprüft wird die Buchführung: Wer ist offen, wer liegt vorn, wohin
   zeigen die Speichernamen, und was passiert beim Schließen. Die
   Oberfläche kommt hier nicht vor; sie hängt an denselben Griffen.
   ============================================================ */
'use strict';

const path = require('path');
const { pruefhelferBauen } = require('./pruefhelfer.js');
const { stimmt, gleich, schluss } = pruefhelferBauen();

/* Ein Speicher, wie ihn der Browser hätte. Er lässt sich zurücksetzen —
   sonst nähme ein Prüfstück dem nächsten seine Ausgangslage. */
function speicherBauen(vorbelegt) {
  const s = Object.assign({}, vorbelegt || {});
  return {
    s,
    getItem(k) { return s[k] === undefined ? null : s[k]; },
    setItem(k, v) { s[k] = String(v); },
    removeItem(k) { delete s[k]; },
  };
}

/* Die Datei liest den Speicher beim Laden. Für jedes Prüfstück muss sie
   deshalb frisch geladen werden — sonst prüfte man immer dieselbe
   Ausgangslage. */
const WEG = path.resolve(__dirname, 'dokumente.js');
function frisch(vorbelegt) {
  global.localStorage = speicherBauen(vorbelegt);
  delete require.cache[WEG];
  return { Dokumente: require(WEG).Dokumente, speicher: global.localStorage };
}

/* Ein Fenster, das ordentlich zugemacht wurde, räumt seinen Platz. Ohne
   das hielte der Prüflauf jedes Neuladen für ein ZWEITES Fenster. */
function neustart(speicher) {
  const s = Object.assign({}, speicher.s);
  for (const k of Object.keys(s)) if (k.startsWith('sp.fenster.')) delete s[k];
  global.localStorage = speicherBauen(s);
  delete require.cache[WEG];
  return { Dokumente: require(WEG).Dokumente, speicher: global.localStorage };
}

console.log('\n=== Erster Start, nichts da ===');
{
  const { Dokumente } = frisch();
  gleich(Dokumente.anzahl(), 1, 'ein Dokument steht bereit');
  gleich(Dokumente.aktiv(), 1, 'und es liegt vorn');
}

console.log('\n=== Umzug: der Text von gestern geht nicht verloren ===');
{
  const { Dokumente, speicher } = frisch({
    'sp.inhalt': '"<p>Guten Tag</p>"',
    'sp.papier': '"a5"',
    'sp.zoom': '120',
  });
  gleich(speicher.getItem('sp.dok.1.inhalt'), '"<p>Guten Tag</p>"',
         'der Text liegt jetzt bei Dokument 1');
  gleich(speicher.getItem('sp.dok.1.papier'), '"a5"',
         'das Papierformat auch');
  gleich(speicher.getItem('sp.dok.1.zoom'), null,
         'die Vergrößerung nicht — die gehört dem Menschen, nicht dem Brief');
  gleich(speicher.getItem('sp.inhalt'), '"<p>Guten Tag</p>"',
         'das Alte bleibt liegen, falls jemand zurückgeht');
  gleich(Dokumente.schluessel('inhalt'), 'dok.1.inhalt', 'und der Name zeigt dorthin');
}

console.log('\n=== Der Umzug findet nur einmal statt ===');
{
  const gemeinsam = {
    'sp.inhalt': '"alt"',
    'sp.dokumente': '{"liste":[1,2],"aktiv":2,"naechste":3}',
    'sp.dok.1.inhalt': '"eins"',
  };
  const { Dokumente, speicher } = frisch(gemeinsam);
  gleich(speicher.getItem('sp.dok.1.inhalt'), '"eins"',
         'ein zweiter Start überschreibt Dokument 1 nicht mit dem Altbestand');
  gleich(Dokumente.aktiv(), 2, 'und merkt sich, welcher Reiter vorn lag');
}

console.log('\n=== Die Nummern laufen nicht davon ===');
{
  /* Hier stand einmal „hoechste bekannte Nummer, dann plus eins" — und
     das zaehlte bei JEDEM Start eine weiter, ob etwas angelegt wurde oder
     nicht. Nach dreimal Fenster auf und zu hiess das zweite Dokument
     „Unbenannt 5". */
  let lauf = frisch({ 'sp.dokumente': '{"liste":[1],"aktiv":1,"naechste":2}' });
  for (let mal = 0; mal < 4; mal++) lauf = neustart(lauf.speicher);
  gleich(lauf.Dokumente.anlegen(), 2,
         'nach vier Starts ohne Anlegen ist die naechste Nummer immer noch die 2');
}

console.log('\n=== Was zum Dokument gehört und was nicht ===');
{
  const { Dokumente } = frisch();
  for (const eigen of ['inhalt', 'kopfinhalt', 'papier', 'seitenrand', 'dateiname',
                       'abschnitte', 'verfolgen', 'design']) {
    stimmt(Dokumente.istEigen(eigen), eigen + ' wandert mit dem Reiter');
  }
  for (const gemein of ['zoom', 'thema', 'tafel', 'leisten', 'register', 'symbole',
                        'lineal', 'skalierung', 'benutzer', 'lebend', 'autokorrektur']) {
    stimmt(!Dokumente.istEigen(gemein), gemein + ' bleibt, wo es ist');
  }
  gleich(Dokumente.schluessel('zoom'), 'zoom', 'gemeinsame Namen werden nicht umgebogen');
}

console.log('\n=== Anlegen und Wechseln ===');
{
  const { Dokumente } = frisch();
  const zwei = Dokumente.anlegen();
  gleich(zwei, 2, 'das zweite bekommt die 2');
  gleich(Dokumente.aktiv(), 2, 'und liegt gleich vorn');
  gleich(Dokumente.name(2), 'Unbenannt 2', 'mit einem Namen für den Reiter');
  gleich(Dokumente.schluessel('inhalt'), 'dok.2.inhalt', 'der Text geht jetzt woandershin');

  stimmt(Dokumente.wechsle(1), 'zurück auf eins');
  gleich(Dokumente.schluessel('inhalt'), 'dok.1.inhalt', 'und der Name folgt');
  stimmt(!Dokumente.wechsle(1), 'auf den, der schon vorn liegt, wechselt niemand');
  stimmt(!Dokumente.wechsle(99), 'auf ein Dokument, das es nicht gibt, auch nicht');
  stimmt(!Dokumente.wechsle('dok.1.inhalt'), 'und auf gar keinen Fall auf etwas, das keine Zahl ist');
}

console.log('\n=== Der Wechsel überlebt den Neustart ===');
{
  const { Dokumente, speicher } = frisch();
  Dokumente.anlegen();
  Dokumente.anlegen();
  Dokumente.wechsle(2);

  const wieder = neustart(speicher).Dokumente;
  gleich(wieder.anzahl(), 3, 'drei Dokumente sind noch da');
  gleich(wieder.aktiv(), 2, 'und das zweite liegt wieder vorn');
  gleich(wieder.fenster(), 1, 'und es ist wieder Fenster 1');
}

console.log('\n=== Schließen ===');
{
  const { Dokumente, speicher } = frisch();
  Dokumente.anlegen();                     // 2
  Dokumente.anlegen();                     // 3
  speicher.setItem('sp.dok.2.inhalt', '"weg damit"');

  gleich(Dokumente.entfernen(2), 3, 'nach dem Schließen liegt der rechte Nachbar vorn');
  gleich(Dokumente.anzahl(), 2, 'zwei bleiben übrig');
  gleich(speicher.getItem('sp.dok.2.inhalt'), null,
         'und der Text des geschlossenen liegt nicht mehr herum');

  gleich(Dokumente.entfernen(3), 1, 'schließt man den letzten rechts, geht es nach links');
  gleich(Dokumente.entfernen(1), null,
         'der allerletzte lässt sich nicht schließen — sonst bliebe ein Fenster ohne Blatt');
  gleich(Dokumente.anzahl(), 1, 'er ist noch da');
}

console.log('\n=== Strg+Tab läuft im Kreis ===');
{
  const { Dokumente } = frisch();
  Dokumente.anlegen();                     // 2
  Dokumente.anlegen();                     // 3
  Dokumente.wechsle(1);
  gleich(Dokumente.weiter(1), 2, 'von eins nach zwei');
  Dokumente.wechsle(3);
  gleich(Dokumente.weiter(1), 1, 'und vom letzten wieder auf den ersten');
  gleich(Dokumente.weiter(-1), 2, 'rückwärts auf den davor');
  Dokumente.wechsle(1);
  gleich(Dokumente.weiter(-1), 3, 'vom ersten rückwärts auf den letzten');
}

console.log('\n=== Reiter umsortieren ===');
{
  const { Dokumente } = frisch();
  Dokumente.anlegen();                     // 2
  Dokumente.anlegen();                     // 3
  stimmt(Dokumente.verschieben(3, 0), 'der dritte nach ganz vorn');
  gleich(Dokumente.liste().join(','), '3,1,2', 'die Reihenfolge stimmt');
  gleich(Dokumente.aktiv(), 3, 'ziehen wechselt den Reiter nicht');
  stimmt(!Dokumente.verschieben(3, 0), 'an dieselbe Stelle ziehen ändert nichts');
  stimmt(Dokumente.verschieben(3, 99), 'zu weit gezogen landet am Ende');
  gleich(Dokumente.liste().join(','), '1,2,3', 'und nicht daneben');
}

console.log('\n=== Kaputte Buchführung wirft niemanden hinaus ===');
{
  gleich(frisch({ 'sp.dokumente': 'kein JSON' }).Dokumente.anzahl(), 1,
         'unlesbar: es geht mit einem Dokument weiter');
  gleich(frisch({ 'sp.dokumente': '{"liste":[]}' }).Dokumente.anzahl(), 1,
         'leere Liste: dasselbe');
  const doppelt = frisch({ 'sp.dokumente': '{"liste":[1,1,2],"aktiv":9,"naechste":1}' }).Dokumente;
  gleich(doppelt.liste().join(','), '1,2', 'doppelte Nummern wären zwei Reiter auf einen Text');
  gleich(doppelt.aktiv(), 1, 'ein Vorderster, den es nicht gibt, wird zum ersten');
  gleich(doppelt.anlegen(), 3, 'und die nächste Nummer kollidiert nicht mit einer vergebenen');
}

console.log('\n=== Mehrere Fenster teilen sich nichts ===');
{
  /* Fenster 1 geht auf und schreibt. */
  const eins = frisch();
  eins.speicher.setItem('sp.' + eins.Dokumente.schluessel('inhalt'), '"Brief"');
  gleich(eins.Dokumente.fenster(), 1, 'das erste Fenster nimmt Platz 1');
  gleich(eins.Dokumente.schluessel('inhalt'), 'dok.1.inhalt',
         'und schreibt ohne Vorsatz — der Altbestand liegt dort');

  /* Fenster 2 geht auf, WÄHREND Fenster 1 noch offen ist: derselbe
     Speicher, aber es darf nichts von Fenster 1 anfassen. */
  global.localStorage = speicherBauen(eins.speicher.s);
  delete require.cache[WEG];
  const zwei = require(WEG).Dokumente;
  gleich(zwei.fenster(), 2, 'das zweite nimmt Platz 2');
  gleich(zwei.schluessel('inhalt'), 'f2.dok.1.inhalt', 'und schreibt woandershin');
  gleich(global.localStorage.getItem('sp.dok.1.inhalt'), '"Brief"',
         'der Brief in Fenster 1 bleibt unangetastet');
  gleich(zwei.anzahl(), 1, 'Fenster 2 fängt mit einem leeren Dokument an');
  gleich(zwei.schluessel('zoom'), 'zoom',
         'die Vergrößerung gehört dem Menschen und gilt in beiden Fenstern');
}

console.log('\n=== Der Umzug des Altbestands geschieht nur in Fenster 1 ===');
{
  const eins = frisch({ 'sp.inhalt': '"von gestern"' });
  gleich(eins.speicher.getItem('sp.dok.1.inhalt'), '"von gestern"',
         'Fenster 1 erbt den Text von gestern');

  global.localStorage = speicherBauen(eins.speicher.s);
  delete require.cache[WEG];
  const zwei = require(WEG).Dokumente;
  gleich(global.localStorage.getItem('sp.f2.dok.1.inhalt'), null,
         'Fenster 2 erbt ihn nicht — sonst stünde derselbe Brief zweimal offen');
  gleich(zwei.fenster(), 2, 'und es ist wirklich das zweite');
}

console.log('\n=== Ein zugemachtes Fenster gibt seinen Platz zurück ===');
{
  const eins = frisch();
  global.localStorage = speicherBauen(eins.speicher.s);
  delete require.cache[WEG];
  gleich(require(WEG).Dokumente.fenster(), 2, 'zwei Fenster: Platz 1 und Platz 2');

  /* Jetzt geht Fenster 1 zu — sein Lebenszeichen verschwindet. */
  const ohne = Object.assign({}, global.localStorage.s);
  delete ohne['sp.fenster.1.wach'];
  global.localStorage = speicherBauen(ohne);
  delete require.cache[WEG];
  gleich(require(WEG).Dokumente.fenster(), 1,
         'das nächste Fenster erbt Platz 1 und damit die Dokumente, die dort standen');
}

console.log('\n=== Ein Fenster bleibt beim Neuladen auf seinem Platz ===');
{
  /* Ohne diesen Merkzettel nahm ein neu geladenes Fenster wieder den
     kleinsten freien Platz — und lud damit die Dokumente eines fremden,
     inzwischen geschlossenen Fensters. */
  const merk = { wert: null };
  global.sessionStorage = {
    getItem(k) { return k === 'sp.fenster.platz' ? merk.wert : null; },
    setItem(k, v) { if (k === 'sp.fenster.platz') merk.wert = String(v); },
  };

  const eins = frisch();
  gleich(eins.Dokumente.fenster(), 1, 'das erste Fenster nimmt Platz 1');

  /* Fenster 2 und 3 gehen auf. Jedes hat einen eigenen Merkzettel — hier
     wird nur der von Fenster 3 weiterverfolgt. */
  merk.wert = null;
  global.localStorage = speicherBauen(eins.speicher.s);
  delete require.cache[WEG];
  gleich(require(WEG).Dokumente.fenster(), 2, 'das zweite nimmt Platz 2');
  merk.wert = null;
  global.localStorage = speicherBauen(global.localStorage.s);
  delete require.cache[WEG];
  gleich(require(WEG).Dokumente.fenster(), 3, 'das dritte nimmt Platz 3');

  /* Fenster 2 geht zu — Platz 2 wird frei. Und jetzt lädt Fenster 3 neu:
     Es räumt beim Weggehen seinen Platz und nimmt ihn gleich wieder. */
  const stand = Object.assign({}, global.localStorage.s);
  delete stand['sp.fenster.2.wach'];
  delete stand['sp.fenster.3.wach'];
  global.localStorage = speicherBauen(stand);
  delete require.cache[WEG];
  gleich(require(WEG).Dokumente.fenster(), 3,
         'nach dem Neuladen ist es wieder Fenster 3 — nicht das freie 2');

  delete global.sessionStorage;
}

console.log('\n=== Ein abgestürztes Fenster blockiert nicht für immer ===');
{
  const alt = Date.now() - 60000;   /* eine Minute her: niemand mehr da */
  const nach = frisch({ 'sp.fenster.1.wach': JSON.stringify({ marke: 'x', zeit: alt }) });
  gleich(nach.Dokumente.fenster(), 1, 'ein altes Lebenszeichen gibt den Platz frei');

  const jetzt = frisch({ 'sp.fenster.1.wach': JSON.stringify({ marke: 'x', zeit: Date.now() }) });
  gleich(jetzt.Dokumente.fenster(), 2, 'ein frisches nicht');

  const kaputt = frisch({ 'sp.fenster.1.wach': 'kein JSON' });
  gleich(kaputt.Dokumente.fenster(), 1, 'und unlesbares sperrt auch nicht');
}

schluss();
