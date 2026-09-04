/* ==========================================================================
   Die KI: korrigieren, vorschlagen, uebersetzen

   400 Zeilen, die zusammengehoeren: der Schluessel, das Modell, der Weg zu
   Claude oder zu Ollama auf diesem Rechner, die Vorschlaege in der
   Seitenleiste und das Einsetzen eines Vorschlags in den Text.

   Sie ist freiwillig. Ohne Schluessel und ohne ein Modell auf dem Rechner
   ist sie grau, und das Programm schreibt sich ohne sie zu Ende.

   WAS „umg" IST

   Fuenf Namen, mehr braucht diese Datei vom Programm nicht. Vier davon sind
   Handgriffe der Oberflaeche; der fuenfte, „fundeLeeren", ist der einzige
   Schreibzugriff nach draussen: Wenn die KI Vorschlaege zeigt, muessen die
   Funde der Rechtschreibpruefung aus der Seitenleiste weichen — sie teilen
   sich denselben Platz.

   Beim Messen sahen es erst sieben Namen aus. „geaendert" war keiner: Im
   KI-Block ist das ein eigener Zaehler und nicht das Flag des Programms.
   ========================================================================== */
'use strict';

function KI_BAUEN(B, umg) {

const $ = (id) => document.getElementById(id);
const melde      = (...a) => umg.melde(...a);
const leereFunde = (...a) => umg.leereFunde(...a);
const kuerze     = (s)    => umg.kuerze(s);
const menueBauen = ()     => umg.menueBauen();

/* ============================================================
   6b. Die KI: korrigieren, vorschlagen, übersetzen

   Die Prüfung nebenan kennt Regeln, aber nicht den Sinn. Was sich nur am
   Satz entscheidet — „das" oder „dass", ein Komma vor einem Relativsatz —
   kann nur jemand, der den Text liest. Dafür sind diese drei Knöpfe da.

   Alles Weitere steckt in js/ki.js. Hier steht nur, was mit dem Ergebnis
   im Dokument geschieht.
   ============================================================ */

let kiLaeuft = false;

const KI_KNOEPFE = [
  ['btn-ki', 'KI-Korrektur'],
  ['btn-vorschlaege', 'Vorschläge'],
  ['btn-uebersetzen', 'Übersetzen'],
];

/* Solange kein Schlüssel da ist, sehen die drei Knöpfe blass aus — aber sie
   bleiben drückbar. Ein grauer Knopf, bei dem nichts passiert, ist eine
   Sackgasse: Man drückt, es rührt sich nichts, und niemand sagt warum. So
   führt derselbe Druck an die Stelle, an der der Schlüssel hingehört. */
function kiKnoepfeAuffrischen() {
  const geht = KI.verfuegbar();
  const sprache = KI.Speicher.lies('sprache', 'Englisch');

  for (const [id, name] of KI_KNOEPFE) {
    const knopf = $(id);
    // Gesperrt wird nur, solange eine Anfrage läuft — zwei auf einmal
    // brächten zwei Antworten für denselben Text.
    knopf.disabled = kiLaeuft;
    knopf.classList.toggle('knopf--wartet', !geht);
    knopf.title = geht
      ? name + ' über ' + (KI.istLokal(KI.modellJetzt())
          ? KI.lokalerName(KI.modellJetzt()) + ' auf diesem Rechner'
          : KI.modellJetzt())
      : name + ' braucht einen KI-Schlüssel oder Ollama auf diesem Rechner. '
        + 'Drücken führt zu den Einstellungen (F9).';
  }
  $('btn-uebersetzen').textContent = 'Nach ' + sprache;
  kiHinweisZeigen(geht);
  menueBauen();
}

/* Warum die drei Knöpfe grau sind — und was dagegen hilft.

   Bisher stand der Grund nur im Tooltip. Wer drei blasse Knöpfe sieht,
   fährt aber nicht mit der Maus darüber und wartet; er hält sie für
   kaputt. Also steht es jetzt darunter.

   Und wenn auf diesem Rechner Ollama läuft, ist der Weg kein Kauf,
   sondern ein Klick: Die Modelle liegen schon da. */
let ollamaGesehen = null;          // null = noch nicht nachgesehen

async function kiHinweisZeigen(geht) {
  const zeile = $('ki-hinweis');
  if (!zeile) return;
  if (geht) { zeile.hidden = true; zeile.innerHTML = ''; return; }

  if (ollamaGesehen === null) {
    ollamaGesehen = [];
    try { ollamaGesehen = (await KI.ollamaModelle()) || []; }
    catch (e) { ollamaGesehen = []; }
    /* Zwischendurch kann ein Schlüssel eingetragen worden sein. */
    if (KI.verfuegbar()) { zeile.hidden = true; return; }
  }

  zeile.hidden = false;
  zeile.innerHTML = '';

  const satz = document.createElement('span');
  const knopf = document.createElement('button');
  knopf.type = 'button';
  knopf.className = 'knopf knopf--klein';

  if (ollamaGesehen.length) {
    const modell = ollamaGesehen[0];
    satz.textContent = 'Die drei Knöpfe sind grau, weil kein KI-Schlüssel '
      + 'gespeichert ist. Auf diesem Rechner läuft aber Ollama — damit gehen '
      + 'sie ohne Schlüssel und ohne Geld.';
    knopf.textContent = modell + ' nehmen';
    knopf.addEventListener('click', () => {
      KI.modellSetzen(KI.OLLAMA_MARKE + modell);
      kiKnoepfeAuffrischen();
      melde('KI läuft jetzt über ' + modell + ' auf diesem Rechner.');
    });
  } else {
    satz.textContent = 'Die drei Knöpfe brauchen einen KI-Schlüssel — oder '
      + 'Ollama auf diesem Rechner, dann kosten sie nichts.';
    knopf.textContent = 'Einrichten';
    knopf.addEventListener('click', () => Einstellungen.oeffnen('ki'));
  }

  zeile.append(satz, knopf);
}

/* Ein Absatz wird in Wörter zerlegt — mitsamt den Leerzeichen dazwischen,
   sonst ließe sich hinterher nicht sagen, wo im Text ein Stück anfängt. */
const STUECKE = /\s+|[^\s]+/g;
const stuecke = (zeile) => zeile.match(STUECKE) || [];

/* Welche Wörter haben sich geändert? Zurück kommen die Stellen in „alt"
   und das, was dort hingehört.

   Gesucht wird die längste gemeinsame Folge — dieselbe Rechnung, mit der
   auch „diff" arbeitet. Danach steht fest, welche Wörter geblieben sind;
   alles dazwischen ist die Änderung. Ein Absatz mit 300 Wörtern ergibt eine
   Tabelle mit 90.000 Feldern, das merkt niemand. Wird es mehr, lohnt der
   Aufwand nicht mehr und der Absatz wird am Stück getauscht. */
function aenderungen(alt, neu) {
  const a = stuecke(alt);
  const b = stuecke(neu);
  if (a.length * b.length > 400000) return null;

  const tabelle = [];
  for (let i = 0; i <= a.length; i++) tabelle.push(new Uint32Array(b.length + 1));
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      tabelle[i][j] = a[i] === b[j]
        ? tabelle[i + 1][j + 1] + 1
        : Math.max(tabelle[i + 1][j], tabelle[i][j + 1]);
    }
  }

  const bloecke = [];
  let offen = null;
  let stelle = 0;                        // Zeichenstelle in „alt"
  let i = 0;
  let j = 0;

  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) {
      if (offen) { bloecke.push(offen); offen = null; }
      stelle += a[i].length;
      i++; j++;
    } else if (j < b.length && (i === a.length || tabelle[i][j + 1] >= tabelle[i + 1][j])) {
      // Dazugekommen: steht in „neu", nicht in „alt".
      if (!offen) offen = { von: stelle, bis: stelle, text: '' };
      offen.text += b[j];
      j++;
    } else {
      // Weggefallen: steht in „alt", nicht in „neu".
      if (!offen) offen = { von: stelle, bis: stelle, text: '' };
      stelle += a[i].length;
      offen.bis = stelle;
      i++;
    }
  }
  if (offen) bloecke.push(offen);
  return bloecke;
}

/* ------------------------------------------------------------
   Das Ergebnis ins Dokument.

   Den ganzen Text auf einmal zu ersetzen wäre das Einfachste — und würde
   jede Überschrift, jedes fette Wort und jede Aufzählung einebnen. Deshalb
   wird zweimal fein gemacht: erst Absatz gegen Absatz (die Anweisung an die
   KI verlangt gleich viele Zeilen zurück), dann innerhalb des Absatzes Wort
   gegen Wort. Angefasst wird am Ende nur, was sich wirklich geändert hat.
   Ein fettes Wort mitten im Satz bleibt fett, solange die Korrektur es
   nicht selbst betrifft.

   Von hinten nach vorn, sonst verschieben sich die Stellen unter der Hand.
   ------------------------------------------------------------ */
function ersetzeErgebnis(alt, neu) {
  const alteZeilen = alt.split('\n');
  const neueZeilen = neu.split('\n');

  if (alteZeilen.length !== neueZeilen.length) {
    /* Die Zeilen gehen nicht auf. Lieber den ganzen Text tauschen als
       falsch zuordnen — Strg+Z holt ihn zurück, falls es misslingt. */
    Dokument.ersetze(0, alt.length, neu);
    return { zeilen: 0, ganz: true };
  }

  let stelle = alt.length;
  let geaendert = 0;
  for (let i = alteZeilen.length - 1; i >= 0; i--) {
    const anfang = stelle - alteZeilen[i].length;

    if (alteZeilen[i] !== neueZeilen[i]) {
      const bloecke = aenderungen(alteZeilen[i], neueZeilen[i]);
      if (bloecke === null) {
        Dokument.ersetze(anfang, stelle, neueZeilen[i]);
      } else {
        for (let k = bloecke.length - 1; k >= 0; k--) {
          const block = bloecke[k];
          if (block.von === block.bis && !block.text) continue;
          Dokument.ersetze(anfang + block.von, anfang + block.bis, block.text);
        }
      }
      geaendert++;
    }

    stelle = anfang - 1;                 // das Zeilenende davor
  }
  return { zeilen: geaendert, ganz: false };
}

/* Der gemeinsame Ablauf: Text holen, Knöpfe sperren, Ergebnis einsetzen. */
async function kiLauf(laeuft, arbeit) {
  if (kiLaeuft) return null;
  const text = Dokument.lies().text.trim();
  if (!text) { melde('Es steht noch kein Text da.'); return null; }
  if (!KI.verfuegbar()) {
    /* Nicht bloß melden, sondern hinbringen: Die Meldung allein ließe den
       Menschen mit der Frage stehen, wo denn nun dieser Schlüssel hingehört. */
    melde('Dafür fehlt der KI-Schlüssel — hier gehört er hin.');
    Einstellungen.oeffnen();
    return null;
  }

  kiLaeuft = true;
  kiKnoepfeAuffrischen();
  melde(laeuft);

  let ergebnis;
  try {
    ergebnis = await arbeit(Dokument.lies().text);
  } finally {
    kiLaeuft = false;
    kiKnoepfeAuffrischen();
  }

  if (ergebnis && ergebnis.fehler) { melde(ergebnis.fehler); return null; }
  return ergebnis;
}

const preisAnhang = (cent) =>
  (cent === null || cent === undefined) ? '' : ' · ' + KI.alsGeld(cent);

async function kiKorrigieren() {
  const vorher = Dokument.lies().text;
  const ergebnis = await kiLauf('Die KI liest den ganzen Text …',
                                (text) => KI.korrigieren(text));
  if (!ergebnis) return;

  if (ergebnis.text.trim() === vorher.trim()) {
    melde('Die KI hat nichts zu ändern gefunden.' + preisAnhang(ergebnis.cent));
    return;
  }

  const { zeilen, ganz } = ersetzeErgebnis(vorher, ergebnis.text);
  leereFunde();
  melde((ganz
    ? 'Korrigiert. Strg+Z macht es rückgängig.'
    : zeilen + (zeilen === 1 ? ' Absatz geändert.' : ' Absätze geändert.')
      + ' Strg+Z macht es rückgängig.') + preisAnhang(ergebnis.cent));
}

async function kiUebersetzen() {
  const sprache = KI.Speicher.lies('sprache', 'Englisch');
  const vorher = Dokument.lies().text;
  const ergebnis = await kiLauf('Wird nach ' + sprache + ' übersetzt …',
                                (text) => KI.uebersetzen(text, sprache));
  if (!ergebnis) return;

  const { zeilen, ganz } = ersetzeErgebnis(vorher, ergebnis.text);
  leereFunde();
  melde('Nach ' + sprache + ' übersetzt'
    + (ganz ? '' : ' (' + zeilen + ' Absätze)')
    + '. Strg+Z macht es rückgängig.' + preisAnhang(ergebnis.cent));
}

/* ------------------------------------------------------------
   Vorschläge.

   Sie kommen nicht als fertiger Text zurück, sondern als Liste einzelner
   Sätze — jeder mit Begründung, jeder einzeln anzunehmen oder liegen zu
   lassen. Der Text gehört dem Menschen, nicht der Maschine. Angezeigt
   werden sie in derselben Leiste wie die Funde, mit denselben zwei
   Knöpfen: Man soll nicht zweierlei bedienen lernen müssen.
   ------------------------------------------------------------ */
let vorschlaege = [];

async function kiVorschlaege() {
  const ergebnis = await kiLauf('Die KI sucht umständliche Sätze …',
                                (text) => KI.vorschlaege(text));
  if (!ergebnis) return;

  vorschlaege = ergebnis.vorschlaege;
  if (!vorschlaege.length) {
    leereFunde('Die KI hat nichts gefunden, was klarer ginge.' + preisAnhang(ergebnis.cent));
    zeichneVorschlaege();
    return;
  }

  umg.fundeLeeren();
  zeichneVorschlaege();
  const zahl = vorschlaege.length;
  melde(zahl === 1 ? '1 Vorschlag.' : zahl + ' Vorschläge.' + preisAnhang(ergebnis.cent));
}

function zeichneVorschlaege() {
  const liste = $('funde');
  liste.innerHTML = '';

  if (!vorschlaege.length) {
    const leer = document.createElement('p');
    leer.className = 'tafel__leer';
    leer.textContent = 'Die KI hat nichts gefunden, was klarer ginge. '
                     + 'Das ist ein gutes Zeichen.';
    liste.appendChild(leer);
    return;
  }

  for (const vorschlag of vorschlaege) {
    const karte = document.createElement('div');
    karte.className = 'fund fund--vorschlag';

    const sorte = document.createElement('span');
    sorte.className = 'fund__sorte';
    sorte.textContent = 'Vorschlag';
    karte.appendChild(sorte);

    const alt = document.createElement('div');
    alt.className = 'fund__stelle';
    alt.textContent = '„' + kuerze(vorschlag.alt) + '“';
    karte.appendChild(alt);

    const neu = document.createElement('div');
    neu.className = 'fund__neu';
    neu.textContent = vorschlag.neu;
    karte.appendChild(neu);

    const grund = document.createElement('small');
    grund.className = 'fund__grund';
    grund.textContent = vorschlag.grund || '';
    karte.appendChild(grund);

    const knoepfe = document.createElement('div');
    knoepfe.className = 'fund__knoepfe';

    const zeigen = document.createElement('button');
    zeigen.className = 'knopf knopf--klein';
    zeigen.textContent = 'Zeigen';
    zeigen.addEventListener('click', () => {
      const stelle = Dokument.lies().text.indexOf(vorschlag.alt);
      if (stelle === -1) { melde('Der Satz steht nicht mehr so im Text.'); return; }
      Dokument.zeige(stelle, stelle + vorschlag.alt.length);
    });
    knoepfe.appendChild(zeigen);

    const aendern = document.createElement('button');
    aendern.className = 'knopf knopf--klein';
    aendern.textContent = 'Ändern';
    aendern.addEventListener('click', () => {
      const stelle = Dokument.lies().text.indexOf(vorschlag.alt);
      if (stelle === -1) { melde('Der Satz steht nicht mehr so im Text.'); return; }
      Dokument.ersetze(stelle, stelle + vorschlag.alt.length, vorschlag.neu);
      /* Angenommen ist erledigt: Die Karte verschwindet, damit niemand
         denselben Satz zweimal einsetzt. */
      vorschlaege = vorschlaege.filter((v) => v !== vorschlag);
      zeichneVorschlaege();
      melde('Eingesetzt. Strg+Z macht es rückgängig.');
    });
    knoepfe.appendChild(aendern);

    karte.appendChild(knoepfe);
    liste.appendChild(karte);
  }
}

/* ---- Für wen? und der Zettel ---- */

const EMPFAENGER = Object.keys(KI.EMPFAENGER);

/* Die Marke sagt nicht nur der KI, in welchem Ton sie schreiben soll — sie
   sagt auch der Wortvorhersage, worum es geht. Wer „Amt" gewählt hat und
   „bes" tippt, bekommt „Bescheid" vor „besonders".

   Die Listen stehen in daten/themenwoerter.js. Fehlt eine, passiert nichts
   Schlimmes: Dann sortiert die Vorhersage wie bisher. */
function themaAnwenden() {
  const liste = (typeof THEMENWOERTER === 'object' && THEMENWOERTER)
    ? THEMENWOERTER[KI.empfaengerLies()]
    : null;
  Pruefung.themaSetzen(liste || []);
}

function empfaengerBauen() {
  const kasten = $('empfaenger');
  const gewaehlt = KI.empfaengerLies();
  kasten.innerHTML = '';
  for (const name of EMPFAENGER) {
    const marke = document.createElement('button');
    marke.className = 'marke' + (name === gewaehlt ? ' marke--an' : '');
    marke.textContent = name;
    marke.addEventListener('click', () => {
      KI.Speicher.schreib('empfaenger', name);
      themaAnwenden();
      empfaengerBauen();
    });
    kasten.appendChild(marke);
  }
  themaAnwenden();
}

/* Was das uebrige Programm braucht: die drei Befehle hinter den Knoepfen
   und Menuepunkten, das Auffrischen der Knoepfe, die Marken „Fuer wen?" —
   und „vorschlaegeLeeren". Das Letzte ist der Weg, den die
   Rechtschreibpruefung geht, wenn sie die Seitenleiste fuer sich
   beansprucht: Vorher stand dort dreimal „vorschlaege = []", ein roher
   Griff in fremden Zustand. Jetzt hat er einen Namen. */
return {
  kiKorrigieren, kiVorschlaege, kiUebersetzen,
  kiKnoepfeAuffrischen, empfaengerBauen,
  vorschlaegeLeeren: () => { vorschlaege = []; },
};
}
