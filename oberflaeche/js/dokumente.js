/* ============================================================
   Mehrere Dokumente in einem Fenster

   Bis hierher hielt ein Fenster genau ein Dokument. „Neu" leerte das
   Blatt, „Öffnen" ersetzte den Text — wer zwei Briefe nebeneinander
   brauchte, musste zwei Fenster aufmachen. Und das ging schief: Beide
   Fenster schrieben ihre Sicherung an dieselbe Stelle und überschrieben
   einander.

   Jetzt trägt ein Fenster mehrere Dokumente, und oben steht für jedes
   ein Reiter — so wie es WPS Writer macht.

   WIE DIE TRENNUNG LÄUFT

   Alles, was das Programm über ein Dokument weiß, liegt im Speicher des
   Browsers unter einem Namen: „inhalt", „kopfinhalt", „papier", „seitenrand".
   Bisher stand da genau ein Satz Werte. Jetzt bekommt jedes Dokument
   seinen eigenen Satz, und der Name wird umgeleitet:

       sp.inhalt          →   sp.dok.1.inhalt      (Dokument 1)
                              sp.dok.2.inhalt      (Dokument 2)

   Umgeleitet wird nur, was WIRKLICH zum Dokument gehört (die Liste
   EIGEN weiter unten). Die Vergrößerung, die Helligkeit, welche Leisten
   sichtbar sind — das ist die Gewohnheit des Menschen und gilt für alle
   Dokumente. Ein Reiterwechsel darf nicht die halbe Oberfläche umstellen.

   Damit war das Umschalten fast von selbst da: Das Programm schreibt
   seine Werte ohnehin schon bei jeder Änderung in den Speicher. Wechselt
   der Reiter, ändert sich nur, WOHIN diese Namen zeigen — und das
   Programm liest sie neu ein.

   MEHRERE FENSTER

   „Fenster ▸ Neues Fenster" startet einen zweiten Programmlauf, der sich
   an denselben Server hängt — und damit an denselben Speicher. Ohne
   Weiteres führten beide Fenster dieselbe Reiterliste und schrieben ihre
   Sicherung übereinander. Wer in zwei Fenstern schrieb, verlor einen der
   beiden Texte.

   Deshalb nimmt sich jedes Fenster beim Aufgehen einen PLATZ: die
   kleinste Nummer, die gerade niemand hat. Der Platz kommt vor den Namen:

       Fenster 1:  sp.dokumente        sp.dok.1.inhalt
       Fenster 2:  sp.f2.dokumente     sp.f2.dok.1.inhalt

   Fenster 1 bleibt ohne Vorsatz. Das ist kein Schönheitsfehler, sondern
   Absicht: Wer bisher einen Text hatte, findet ihn wieder, ohne dass
   irgendetwas umziehen muss.

   Wer den Platz hat, sagt er alle paar Sekunden. Bleibt die Meldung aus
   — Fenster zu, oder abgestürzt —, ist der Platz nach einer Viertelminute
   wieder frei, und das nächste Fenster erbt die Dokumente, die dort noch
   offen waren. Zwei Fenster, die im selben Augenblick aufgehen, greifen
   nicht nach demselben Platz: Wer schreibt, liest gleich nach, ob er
   wirklich dasteht.

   Was NICHT je Fenster getrennt wird: die Gewohnheiten des Menschen —
   Vergrößerung, Helligkeit, welche Leisten er mag. Die gehören ihm, nicht
   dem Fenster, und sollen in jedem gleich sein.

   Diese Datei führt Buch: welche Dokumente offen sind, welches vorn
   liegt, und unter welchem Namen die Werte des vordersten liegen. Sie
   fasst die Oberfläche nicht an; das tut programm.js.
   ============================================================ */
'use strict';

const Dokumente = (() => {

/* ------------------------------------------------------------
   Der Platz dieses Fensters
   ------------------------------------------------------------ */

const WACH_ALLE = 5000;      /* so oft meldet sich ein Fenster */
const WACH_TOT = 15000;      /* danach gilt sein Platz als frei */
const PLAETZE = 32;          /* mehr Fenster macht niemand auf */

function wachName(n) { return 'sp.fenster.' + n + '.wach'; }

/* Welchen Platz DIESES Fenster zuletzt hatte.
 *
 * Der Merkzettel liegt im sessionStorage, und das ist der ganze Grund,
 * warum er hilft: Der gehört dem einen Fenster, überlebt ein Neuladen und
 * geht mit dem Fenster unter. Genau die Frage, die hier zu beantworten
 * ist.
 *
 * Ohne ihn nahm ein neu geladenes Fenster wieder den kleinsten freien
 * Platz — und das war womöglich der eines inzwischen geschlossenen
 * Fensters. Dann lud Fenster 3 nach einem Neustart plötzlich die
 * Dokumente von Fenster 2. Ein Fenster soll bei seinen Sachen bleiben.
 */
const MERK = 'sp.fenster.platz';
function platzGemerkt() {
  try {
    const n = Number(sessionStorage.getItem(MERK));
    return Number.isInteger(n) && n >= 1 && n <= PLAETZE ? n : null;
  } catch (e) { return null; }
}
function platzMerken(n) {
  try { sessionStorage.setItem(MERK, String(n)); } catch (e) { /* egal */ }
}

/* Ist der Platz frei? Frei heißt: Da hat sich lange niemand gemeldet. */
function platzFrei(n) {
  const da = roh(wachName(n), null);
  return !(da && typeof da.zeit === 'number' && Date.now() - da.zeit < WACH_TOT);
}

/* Draufschreiben und gleich nachsehen, ob wirklich wir dastehen. Zwei
   Fenster, die im selben Augenblick aufgehen, schreiben sonst beide auf
   denselben Platz und merken es nie. Der spätere Schreiber gewinnt; der
   frühere liest eine fremde Marke und geht eins weiter. */
function platzGreifen(n, marke) {
  rohSchreib(wachName(n), { marke: marke, zeit: Date.now() });
  const jetzt = roh(wachName(n), null);
  return !!(jetzt && jetzt.marke === marke);
}

function platzNehmen() {
  const marke = Date.now().toString(36) + '.' + Math.random().toString(36).slice(2, 10);

  /* Erst der eigene von vorhin — ein Neuladen soll nichts verschieben. */
  const eigener = platzGemerkt();
  if (eigener !== null && platzFrei(eigener) && platzGreifen(eigener, marke)) {
    return { nr: eigener, marke: marke };
  }

  for (let n = 1; n <= PLAETZE; n++) {
    if (!platzFrei(n)) continue;
    if (platzGreifen(n, marke)) { platzMerken(n); return { nr: n, marke: marke }; }
  }
  /* Zweiunddreißig Fenster offen. Dann eben zu zweit auf Platz eins —
     das ist besser, als gar nicht aufzugehen. */
  return { nr: 1, marke: marke };
}

const PLATZ = platzNehmen();

/* Fenster 1 schreibt ohne Vorsatz — so findet ein Mensch, der bisher ein
   Fenster hatte, seinen Text an derselben Stelle wieder. */
const VORSATZ = PLATZ.nr === 1 ? '' : 'f' + PLATZ.nr + '.';

/* Sagen, dass es uns noch gibt — und beim Zumachen den Platz räumen,
   damit das nächste Fenster nicht eine Viertelminute warten muss. */
if (typeof window !== 'undefined') {
  window.setInterval(() => {
    rohSchreib(wachName(PLATZ.nr), { marke: PLATZ.marke, zeit: Date.now() });
  }, WACH_ALLE);
  window.addEventListener('pagehide', () => rohWeg(wachName(PLATZ.nr)));
}

/* Der Schlüssel, unter dem die Buchführung selbst liegt. Er gehört dem
   Fenster, nicht einem Dokument — sonst könnte man ihn nicht finden,
   ohne vorher zu wissen, was drinsteht. */
const BUCH = 'sp.' + VORSATZ + 'dokumente';

/* Was zum Dokument gehört und deshalb mit dem Reiter wechselt.
 *
 * Die Liste ist mit Absicht aufgeschrieben und nicht erraten. Ein
 * Schlüssel zu viel darin heißt: Der Mensch stellt etwas ein, wechselt
 * den Reiter, und es ist wieder weg. Ein Schlüssel zu wenig heißt: Zwei
 * Briefe teilen sich ein Papierformat. Beides fällt auf, beides ärgert.
 *
 * Die Faustregel: Steht es in der Datei, wenn man sie weitergibt, gehört
 * es zum Dokument. Sieht es nur der, der hier sitzt, gehört es zum
 * Programm.
 */
const EIGEN = new Set([
  /* Der Text und was unmittelbar dazugehört */
  'inhalt', 'kopfinhalt', 'fussinhalt', 'kopfAn', 'fussAn',

  /* Die Datei dahinter */
  'dateiname', 'endung', 'importstil', 'eigenschaften',

  /* Der Aufbau: Abschnitte mit eigenem Seitenbild */
  'abschnitte',

  /* Die Seite */
  'papier', 'quer', 'seitenrand', 'spalten', 'layout',
  'seitenfarbe', 'seitenrahmen', 'wasserzeichen',
  'zeilennummern', 'trennung',

  /* Wie der Text aussieht */
  'grundschrift', 'grundgroesse', 'design', 'vorlagensatz', 'vorlagenstile',

  /* Überarbeiten */
  'markup', 'verfolgen',
]);

/* Lesen und Schreiben ohne Umweg — diese Datei läuft, bevor programm.js
   seinen eigenen Speicher hat, und darf sich nicht darauf stützen. */
function roh(name, ersatz) {
  try { const w = localStorage.getItem(name); return w === null ? ersatz : JSON.parse(w); }
  catch (e) { return ersatz; }
}
function rohSchreib(name, wert) {
  try { localStorage.setItem(name, JSON.stringify(wert)); } catch (e) { /* voll */ }
}
function rohWeg(name) {
  try { localStorage.removeItem(name); } catch (e) { /* egal */ }
}

/* Die Buchführung. Sie steht bewusst als eine einzige Zeile im Speicher:
   Liste, Vorderster, nächste freie Nummer. Drei getrennte Schlüssel
   könnten auseinanderlaufen, wenn zwischen zwei Schreibvorgängen etwas
   dazwischenkommt. */
let buch = { liste: [1], aktiv: 1, naechste: 2 };

function buchSchreiben() { rohSchreib(BUCH, buch); }

/* Nummern sind Zahlen und sollen Zahlen bleiben — sie werden zu einem
   Schlüsselnamen zusammengesetzt, und was dort landet, darf nichts
   Fremdes sein. */
function nummer(wert) {
  const n = Number(wert);
  return Number.isInteger(n) && n > 0 && n < 1e9 ? n : null;
}

function buchLesen() {
  const gelesen = roh(BUCH, null);
  if (!gelesen || !Array.isArray(gelesen.liste)) return false;

  const liste = gelesen.liste.map(nummer).filter((n) => n !== null);
  if (!liste.length) return false;

  /* Doppelte Nummern wären zwei Reiter auf denselben Text. */
  buch.liste = [...new Set(liste)];
  buch.aktiv = buch.liste.includes(nummer(gelesen.aktiv)) ? nummer(gelesen.aktiv) : buch.liste[0];
  /* Die naechste freie Nummer: die gemerkte, mindestens aber eine ueber
     der hoechsten vergebenen. Hier stand einmal „hoechste von allem, dann
     plus eins" — das zaehlte bei jedem Start eine Nummer weiter, und das
     zweite Dokument hiess „Unbenannt 3". */
  buch.naechste = Math.max(nummer(gelesen.naechste) || 1, Math.max(...buch.liste) + 1);
  return true;
}

/* Der Name eines Werts für ein bestimmtes Dokument. Ohne „sp." — den
   setzt der Speicher in programm.js davor, und zwei Stellen, die
   dasselbe Vorwort anhängen, sind eine zu viel. */
function schluesselVon(nr, name) {
  return VORSATZ + 'dok.' + nr + '.' + name;
}

/* ------------------------------------------------------------
   Der erste Start nach dieser Änderung

   Auf dem Rechner liegt ein Text unter „sp.inhalt", eine Kopfzeile unter
   „sp.kopfinhalt", ein Papierformat unter „sp.papier". Diese Werte
   einfach stehen zu lassen hieße: Das Fenster geht mit einem leeren
   Blatt auf, obwohl gestern etwas drinstand. Das ist ein Verlust, und
   zwar der schlimmste, den ein Schreibprogramm zufügen kann.

   Also wird umgezogen, einmalig: Was da ist, wird Dokument 1. Die alten
   Schlüssel bleiben liegen — sie stören nicht, und wer diese Fassung
   wieder zurücknimmt, findet seinen Text vor.
   ------------------------------------------------------------ */
function umziehen() {
  /* Nur Fenster 1. Der Altbestand ist EIN Text — ihn in jedes neue
     Fenster zu kopieren hieße, denselben Brief mehrfach offen zu haben
     und beim Speichern nicht zu wissen, welcher gilt. */
  if (VORSATZ) return;
  for (const name of EIGEN) {
    const alt = localStorage.getItem('sp.' + name);
    if (alt === null) continue;
    try { localStorage.setItem('sp.' + schluesselVon(1, name), alt); }
    catch (e) { /* voll — dann eben ohne */ }
  }
}

function starten() {
  if (buchLesen()) return;
  umziehen();
  buch = { liste: [1], aktiv: 1, naechste: 2 };
  buchSchreiben();
}

starten();

/* ------------------------------------------------------------
   Was das Programm damit tut
   ------------------------------------------------------------ */

/** Gehört dieser Wert zum Dokument — wandert er also mit dem Reiter? */
function istEigen(name) { return EIGEN.has(name); }

/** Der Speichername für das Dokument, das gerade vorn liegt. */
function schluessel(name) {
  return istEigen(name) ? schluesselVon(buch.aktiv, name) : name;
}

function liste() { return buch.liste.slice(); }
function aktiv() { return buch.aktiv; }
function anzahl() { return buch.liste.length; }

/** Wie der Reiter heißt. Der Dateiname des Dokuments, sonst „Unbenannt". */
function name(nr) {
  return roh('sp.' + schluesselVon(nr, 'dateiname'), 'Unbenannt') || 'Unbenannt';
}

/** Ein neues, leeres Dokument. Es kommt ans Ende und wird zum vordersten. */
function anlegen(wieHeisst) {
  const nr = buch.naechste;
  buch.naechste += 1;
  buch.liste.push(nr);
  buch.aktiv = nr;
  /* Der Name muss gleich stehen — der Reiter wird gezeichnet, bevor das
     Programm irgendetwas hineingeschrieben hat. */
  rohSchreib('sp.' + schluesselVon(nr, 'dateiname'), wieHeisst || 'Unbenannt ' + nr);
  buchSchreiben();
  return nr;
}

/** Den Reiter wechseln. Gibt zurück, ob sich etwas geändert hat. */
function wechsle(nr) {
  const n = nummer(nr);
  if (n === null || !buch.liste.includes(n) || n === buch.aktiv) return false;
  buch.aktiv = n;
  buchSchreiben();
  return true;
}

/** Der Nachbar, der vorn liegt, wenn dieser hier geht. */
function nachbarVon(nr) {
  const stelle = buch.liste.indexOf(nr);
  if (stelle === -1) return buch.aktiv;
  /* Nach rechts, wie in jedem Programm mit Reitern — außer beim letzten,
     da bleibt nur links. */
  return buch.liste[stelle + 1] !== undefined ? buch.liste[stelle + 1] : buch.liste[stelle - 1];
}

/**
 * Ein Dokument schließen. Der letzte lässt sich nicht schließen — dann
 * bliebe ein Fenster ohne Blatt stehen, und darin ließe sich nicht
 * schreiben. Wer das Fenster loswerden will, nimmt „Beenden".
 *
 * @returns {number|null} die Nummer des Dokuments, das jetzt vorn liegt,
 *                        oder null, wenn nichts geschlossen wurde.
 */
function entfernen(nr) {
  const n = nummer(nr);
  if (n === null || !buch.liste.includes(n) || buch.liste.length < 2) return null;

  const naechster = nachbarVon(n);
  buch.liste = buch.liste.filter((x) => x !== n);
  if (buch.aktiv === n) buch.aktiv = naechster;
  buchSchreiben();
  aufraeumen(n);
  return buch.aktiv;
}

/** Die Werte eines geschlossenen Dokuments wegräumen. */
function aufraeumen(nr) {
  for (const name of EIGEN) rohWeg('sp.' + schluesselVon(nr, name));
}

/** Zum Reiter davor oder danach — für Strg+Tab. Rundet um. */
function weiter(richtung) {
  if (buch.liste.length < 2) return buch.aktiv;
  const stelle = buch.liste.indexOf(buch.aktiv);
  const ziel = (stelle + (richtung < 0 ? -1 : 1) + buch.liste.length) % buch.liste.length;
  return buch.liste[ziel];
}

/**
 * Die Reihenfolge ändern — ein Reiter wird an eine andere Stelle gezogen.
 * Die Nummern bleiben, was sie sind; nur die Liste wird umsortiert.
 */
function verschieben(nr, anStelle) {
  const n = nummer(nr);
  const von = buch.liste.indexOf(n);
  if (von === -1) return false;
  const ziel = Math.max(0, Math.min(buch.liste.length - 1, Math.trunc(anStelle)));
  if (von === ziel) return false;
  buch.liste.splice(von, 1);
  buch.liste.splice(ziel, 0, n);
  buchSchreiben();
  return true;
}

/** Der Platz dieses Fensters. 1 ist das erste. */
function fenster() { return PLATZ.nr; }

return {
  EIGEN, istEigen, schluessel, schluesselVon, fenster,
  liste, aktiv, anzahl, name,
  anlegen, wechsle, entfernen, weiter, verschieben, nachbarVon,
};
})();

/* Für die Prüfläufe ohne Fenster. */
if (typeof module !== 'undefined' && module.exports) module.exports = { Dokumente };
