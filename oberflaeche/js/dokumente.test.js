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
  let stand = { 'sp.dokumente': '{"liste":[1],"aktiv":1,"naechste":2}' };
  for (let mal = 0; mal < 4; mal++) {
    global.localStorage = speicherBauen(stand);
    delete require.cache[WEG];
    require(WEG);
    stand = global.localStorage.s;
  }
  global.localStorage = speicherBauen(stand);
  delete require.cache[WEG];
  gleich(require(WEG).Dokumente.anlegen(), 2,
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

  global.localStorage = speicherBauen(speicher.s);
  delete require.cache[WEG];
  const wieder = require(WEG).Dokumente;
  gleich(wieder.anzahl(), 3, 'drei Dokumente sind noch da');
  gleich(wieder.aktiv(), 2, 'und das zweite liegt wieder vorn');
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

schluss();
