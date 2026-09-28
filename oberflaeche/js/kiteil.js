/* ==========================================================================
   Die KI: korrigieren, vorschlagen, uebersetzen

   400 Zeilen, die zusammengehoeren: der Schluessel, das Modell, der Weg zu
   Claude oder zu Ollama auf diesem Rechner, die Vorschlaege in der
   Seitenleiste und das Einsetzen eines Vorschlags in den Text.

   Sie ist freiwillig. Ohne Schluessel und ohne ein Modell auf dem Rechner
   ist sie grau, und das Programm schreibt sich ohne sie zu Ende.

   WAS „umg" IST

   Acht Namen, mehr braucht diese Datei vom Programm nicht. Die meisten
   sind Handgriffe der Oberflaeche; „fundeLeeren" ist der einzige
   Schreibzugriff nach draussen: Wenn die KI Vorschlaege zeigt, muessen die
   Funde der Rechtschreibpruefung aus der Seitenleiste weichen — sie teilen
   sich denselben Platz. „fenster" baut den Dialog, in dem ein eigener
   Assistent angelegt wird — derselbe Baukasten, mit dem auch ein Baustein
   oder eine Formatvorlage entsteht. „kleinmenue" baut das kleine
   Klappmenü, mit dem die Hinweiskarte „Einfügen als" anbietet.

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
const kleinmenue  = (...a) => umg.kleinmenue(...a);

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
  ['btn-zusammenfassen', 'Zusammenfassen'],
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

/* ------------------------------------------------------------
   Ist Text markiert? Dann gilt der, nicht das ganze Dokument.

   Die Stellen (von/bis) stehen in derselben Zählung wie
   Dokument.lies().text — nicht im nativen Range.toString(), das bei
   einer Markierung über mehrere Absätze hinweg den Zeilenumbruch
   verschluckt, den Dokument.lies() sonst einfügt. Erkannt wird nur der
   häufige Fall, in dem Anfang und Ende der Auswahl direkt in einem
   Text-Knoten liegen (ein normales Ziehen mit der Maus). Alles andere —
   etwa eine ganze Zeile per Dreifachklick, deren Rand zwischen zwei
   Knoten liegt — fällt zurück auf den ganzen Text, statt an einer
   möglicherweise falschen Stelle zu schreiben. */
function markierungOffsets() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) return null;
  const range = auswahl.getRangeAt(0);
  if (!Dokument.feld.contains(range.commonAncestorContainer)) return null;
  if (range.startContainer.nodeType !== Node.TEXT_NODE
   || range.endContainer.nodeType !== Node.TEXT_NODE) return null;

  const { text, karte } = Dokument.lies();
  const start = karte.find((e) => e.knoten === range.startContainer);
  const ende = karte.find((e) => e.knoten === range.endContainer);
  if (!start || !ende) return null;

  const von = start.von + range.startOffset;
  const bis = ende.von + range.endOffset;
  if (bis <= von) return null;
  const markiert = text.slice(von, bis);
  return markiert.trim() ? { von, bis, text: markiert } : null;
}

/* Der gemeinsame Ablauf: Text holen, Knöpfe sperren, Ergebnis einsetzen.

   „eingabeText" im Rückgabewert ist genau das, was wirklich an die KI
   ging — Markierung oder ganzer Text. Wer das Ergebnis einsetzt, braucht
   sich den Ausgangstext nicht selbst noch einmal zu merken; zwei Lesungen
   kurz hintereinander (einmal hier, einmal beim Aufrufer) könnten sonst
   knapp auseinanderlaufen. */
async function kiLauf(laeuft, arbeit) {
  if (kiLaeuft) return null;

  const markierung = markierungOffsets();
  const eingabeText = markierung ? markierung.text : Dokument.lies().text.trim();
  if (!eingabeText) { melde('Es steht noch kein Text da.'); return null; }
  if (!KI.verfuegbar()) {
    /* Nicht bloß melden, sondern hinbringen: Die Meldung allein ließe den
       Menschen mit der Frage stehen, wo denn nun dieser Schlüssel hingehört. */
    melde('Dafür fehlt der KI-Schlüssel — hier gehört er hin.');
    Einstellungen.oeffnen();
    return null;
  }

  kiLaeuft = true;
  kiKnoepfeAuffrischen();
  /* Wer eine Markierung hat, soll sehen, dass NUR sie gelesen wird —
     nicht dieselbe Meldung wie beim ganzen Text. */
  melde(markierung
    ? 'Die KI liest die Markierung (' + eingabeText.length + ' Zeichen) …'
    : laeuft);

  /* Welche Fassung des Textes gefragt wurde.

     Die Antwort kommt spät: Über Ollama, ohne Grafikkarte, dauert eine
     Anfrage bis zu zehn Minuten — und in zehn Minuten schreibt ein
     Mensch weiter. Käme die Antwort dann ungeprüft ins Blatt, würde sie
     über den neuen Text gelegt: ersetzeErgebnis rechnet alle Stellen aus
     dem Text von vorhin, und bei „ersetze(0, alt.length, neu)" fiele
     alles weg, was inzwischen dazugekommen ist. Bei einer Markierung
     wären „von"/„bis" ebenso nicht mehr verlässlich.

     Also wird die Fassung vorher gemerkt und nachher verglichen. */
  const fassungVorher = umg.fassung ? umg.fassung() : null;

  let ergebnis;
  try {
    ergebnis = await arbeit(eingabeText);
  } finally {
    kiLaeuft = false;
    kiKnoepfeAuffrischen();
  }

  if (ergebnis && ergebnis.fehler) { melde(ergebnis.fehler); return null; }

  if (fassungVorher !== null && umg.fassung() !== fassungVorher) {
    melde('Du hast weitergeschrieben, während die KI gelesen hat. '
        + 'Ihre Antwort passt nicht mehr zu dem, was jetzt dasteht — '
        + 'nichts wurde geändert. Noch einmal drücken fragt sie neu.');
    return null;
  }

  return { ...ergebnis, eingabeText, markierung };
}

const preisAnhang = (cent) =>
  (cent === null || cent === undefined) ? '' : ' · ' + KI.alsGeld(cent);

/* Eine Markierung wird zielgenau ersetzt (Dokument.ersetze mit ihren
   eigenen Stellen); der ganze Text weiter wie bisher über den
   Absatz-für-Absatz-Vergleich. Beides mündet in dieselbe Meldung, nur
   mit einem anderen ersten Wort — „Markierung" statt „Korrigiert" —,
   damit sichtbar bleibt, was gerade passiert ist. */
function ergebnisEinsetzen(ergebnis, wennGanzMeldung, wennMarkiertMeldung) {
  if (ergebnis.markierung) {
    Dokument.ersetze(ergebnis.markierung.von, ergebnis.markierung.bis, ergebnis.text);
    leereFunde();
    melde(wennMarkiertMeldung + ' Strg+Z macht es rückgängig.' + preisAnhang(ergebnis.cent));
    return;
  }
  const { zeilen, ganz } = ersetzeErgebnis(ergebnis.eingabeText, ergebnis.text);
  leereFunde();
  melde((ganz
    ? wennGanzMeldung + ' Strg+Z macht es rückgängig.'
    : zeilen + (zeilen === 1 ? ' Absatz geändert.' : ' Absätze geändert.')
      + ' Strg+Z macht es rückgängig.') + preisAnhang(ergebnis.cent));
}

/* ------------------------------------------------------------
   Text bearbeiten — Verbessern, Umformulieren, Kürzen, Erweitern,
   Professioneller/Einfacher formulieren, Tonalität ändern. Ein Dialog
   mit einer Wahl statt sieben Knöpfen, aus demselben Grund wie bei den
   Überschriften: sieben Knöpfe in der schmalen Leiste wären eine
   abgeschnittene Klappe, siehe [[rollende-kaesten-schneiden-ab]].
   ------------------------------------------------------------ */
async function kiTextAktionAusfuehren(aktion) {
  const namen = Object.fromEntries(KI.TEXT_AKTIONEN);
  const ergebnis = await kiLauf('„' + namen[aktion] + '" …',
                                (text) => KI.textAktion(text, aktion));
  if (!ergebnis) return;

  if (ergebnis.text.trim() === ergebnis.eingabeText.trim()) {
    melde('Die KI hat nichts geändert.' + preisAnhang(ergebnis.cent));
    return;
  }
  ergebnisEinsetzen(ergebnis, namen[aktion] + '.', 'Markierung: ' + namen[aktion] + '.');
}

/* ------------------------------------------------------------
   Text- und Wortanalyse — ersetzt nichts, zeigt nur, was die KI über
   den Text sagt. Deshalb kein „ergebnisEinsetzen", sondern ein Fenster,
   genau wie das Vorbild es für diese eine Aktion vorsieht. */
async function kiTextAnalyse() {
  const ergebnis = await kiLauf('Die KI liest den Text …', (text) => KI.textAnalyse(text));
  if (!ergebnis) return;
  umg.fenster('Text- und Wortanalyse', [
    { art: 'satz', text: ergebnis.text.trim() },
  ], () => {}, 'Schließen');
}

function textAktionDialog() {
  umg.fenster('Text bearbeiten', [
    { art: 'satz', text: 'Wirkt auf die Markierung, wenn Text markiert ist — '
                       + 'sonst auf den ganzen Text.' },
    { schluessel: 'aktion', name: 'Aktion', art: 'auswahl',
      werte: KI.TEXT_AKTIONEN, wert: 'verbessern' },
  ], (werte) => kiTextAktionAusfuehren(werte.aktion), 'Los');
}

async function kiKorrigieren() {
  const ergebnis = await kiLauf('Die KI liest den ganzen Text …',
                                (text) => KI.korrigieren(text));
  if (!ergebnis) return;

  if (ergebnis.text.trim() === ergebnis.eingabeText.trim()) {
    melde('Die KI hat nichts zu ändern gefunden.' + preisAnhang(ergebnis.cent));
    return;
  }

  ergebnisEinsetzen(ergebnis, 'Korrigiert.', 'Markierung korrigiert.');
}

async function kiUebersetzen() {
  const sprache = KI.Speicher.lies('sprache', 'Englisch');
  const ergebnis = await kiLauf('Wird nach ' + sprache + ' übersetzt …',
                                (text) => KI.uebersetzen(text, sprache));
  if (!ergebnis) return;

  ergebnisEinsetzen(ergebnis, 'Nach ' + sprache + ' übersetzt.',
                             'Markierung nach ' + sprache + ' übersetzt.');
}

/* ------------------------------------------------------------
   Die Hinweiskarte.

   Manche Antworten dürfen den Text nicht einfach ersetzen — eine
   Zusammenfassung lässt absichtlich das meiste weg, und „ersetzeErgebnis"
   über den ganzen Text gelegt würde den Brief selbst wegwerfen. Sie stehen
   deshalb als Karte in der Seitenleiste, wie ein Vorschlag, und werden nur
   auf ausdrücklichen Wunsch vorn eingefügt. Zusammenfassen nutzt das
   genauso wie ein eigener Assistent im Modus „Hinweis" — eine Karte, kein
   zweites Stück Code. */
let hinweisKarte = null;         // { titel, text, cent }

function hinweisKarteZeigen(titel, text, cent) {
  hinweisKarte = { titel, text: String(text).trim(), cent };
  umg.fundeLeeren();
  zeichneHinweisKarte();
}

const alsHtmlSicher = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const alsHtmlZeilenLokal = (text) => text.trim().split('\n').map(alsHtmlSicher).join('<br>');

/* Vier Wege, wie eine Hinweiskarte ins Dokument kommt — dieselben vier,
   die auch die Zusammenfassung im Vorbild anbietet. Keiner ist der eine
   „richtige" Weg; welcher passt, hängt davon ab, ob das Ergebnis mit dem
   Text mitgedruckt werden soll (Rezension, Ersetzen, Am Ende) oder nur
   als Randbemerkung dabeisteht (Kommentar). */
function hinweisAlsRezension() {
  if (!hinweisKarte) return;
  const { karte } = Dokument.lies();
  Dokument.waehle(Dokument.bereich(karte, 0, 0));
  Dokument.einfuegen('<ins class="verfolgt">' + alsHtmlZeilenLokal(hinweisKarte.text) + '</ins><br><br>');
  hinweisKarte = null;
  zeichneHinweisKarte();
  melde('Als Rezension eingefügt — sichtbar im Überarbeitungsbereich.');
}

function hinweisAlsKommentar() {
  if (!hinweisKarte) return;
  const { karte } = Dokument.lies();
  Dokument.waehle(Dokument.bereich(karte, 0, 0));
  const autor = (KI.Speicher.lies('kommentarAutor', '') || '').trim() || 'Ich';
  const marke = '<span class="kommentar" contenteditable="false" data-zeit="' + Date.now()
              + '" data-autor="' + autor.replace(/"/g, '&quot;')
              + '" title="' + hinweisKarte.text.replace(/"/g, '&quot;') + '">✎</span>';
  Dokument.einfuegen(marke);
  hinweisKarte = null;
  zeichneHinweisKarte();
  melde('Als Kommentar eingefügt. Strg+Z macht es rückgängig.');
}

function hinweisOriginaltextErsetzen() {
  if (!hinweisKarte) return;
  const { text } = Dokument.lies();
  Dokument.ersetze(0, text.length, hinweisKarte.text);
  hinweisKarte = null;
  zeichneHinweisKarte();
  leereFunde();
  melde('Text ersetzt. Strg+Z macht es rückgängig.');
}

function hinweisAmEndeEinfuegen() {
  if (!hinweisKarte) return;
  const { text } = Dokument.lies();
  Dokument.ersetze(text.length, text.length, '\n\n' + hinweisKarte.text);
  hinweisKarte = null;
  zeichneHinweisKarte();
  melde('Am Ende eingefügt. Strg+Z macht es rückgängig.');
}

function zeichneHinweisKarte() {
  const liste = $('funde');
  liste.innerHTML = '';
  if (!hinweisKarte) return;

  const karte = document.createElement('div');
  karte.className = 'fund fund--vorschlag';

  const sorte = document.createElement('span');
  sorte.className = 'fund__sorte';
  sorte.textContent = hinweisKarte.titel;
  karte.appendChild(sorte);

  const text = document.createElement('div');
  text.className = 'fund__neu';
  text.textContent = hinweisKarte.text;
  karte.appendChild(text);

  const knoepfe = document.createElement('div');
  knoepfe.className = 'fund__knoepfe';

  const einfuegen = document.createElement('button');
  einfuegen.className = 'knopf knopf--klein';
  einfuegen.textContent = 'Einfügen als ▾';
  einfuegen.addEventListener('click', () => {
    kleinmenue(einfuegen, [
      { name: 'Als Rezension', tun: hinweisAlsRezension },
      { name: 'Als Kommentar', tun: hinweisAlsKommentar },
      { name: 'Den Originaltext ersetzen', tun: hinweisOriginaltextErsetzen },
      { name: 'Am Ende des Dokuments', tun: hinweisAmEndeEinfuegen },
    ]);
  });
  knoepfe.appendChild(einfuegen);

  const verwerfen = document.createElement('button');
  verwerfen.className = 'knopf knopf--klein';
  verwerfen.textContent = 'Verwerfen';
  verwerfen.addEventListener('click', () => {
    hinweisKarte = null;
    zeichneHinweisKarte();
  });
  knoepfe.appendChild(verwerfen);

  karte.appendChild(knoepfe);
  liste.appendChild(karte);
}

/* ------------------------------------------------------------
   Zusammenfassen.
   ------------------------------------------------------------ */
async function kiZusammenfassen() {
  const ergebnis = await kiLauf('Die KI liest den ganzen Text, um ihn zusammenzufassen …',
                                (text) => KI.zusammenfassen(text));
  if (!ergebnis) return;

  hinweisKarteZeigen('Zusammenfassung', ergebnis.text, ergebnis.cent);
  melde('Zusammengefasst.' + preisAnhang(ergebnis.cent));
}

/* ------------------------------------------------------------
   Eigene Assistenten.

   Ein Assistent ist ein Name und ein Prompt, mehr nicht — die Anfrage
   dahinter läuft über denselben „kiLauf" wie die drei Knöpfe oben. Der
   Modus entscheidet nur, was mit dem Ergebnis geschieht: „ersetzen" wie
   Korrigieren, „hinweis" wie Zusammenfassen.
   ------------------------------------------------------------ */
async function kiAssistentAusfuehren(assistent) {
  if (assistent.modus === 'ersetzen') {
    const ergebnis = await kiLauf('„' + assistent.name + '" arbeitet …',
                                  (text) => KI.assistentAusfuehren(assistent, text));
    if (!ergebnis) return;

    if (ergebnis.text.trim() === ergebnis.eingabeText.trim()) {
      melde('„' + assistent.name + '" hat nichts geändert.' + preisAnhang(ergebnis.cent));
      return;
    }
    ergebnisEinsetzen(ergebnis, 'Ersetzt.', 'Markierung ersetzt.');
    return;
  }

  const ergebnis = await kiLauf('„' + assistent.name + '" arbeitet …',
                                (text) => KI.assistentAusfuehren(assistent, text));
  if (!ergebnis) return;
  hinweisKarteZeigen(assistent.name, ergebnis.text, ergebnis.cent);
  melde('„' + assistent.name + '" fertig.' + preisAnhang(ergebnis.cent));
}

/* Name, Prompt, Modus erfragen — über den Dialogbaukasten aus programm.js,
   denselben, mit dem auch ein Baustein oder eine Formatvorlage angelegt
   wird. Eine eigene Fenstersorte dafür wäre nur eine vierte Abschrift
   desselben Kastens.

   „nachAnlegen" ist die einzige Verbindung zu dem, was nach dem Anlegen
   eine Liste zeigen will: Früher zeichnete diese Funktion die Liste in
   der Seitenleiste gleich selbst neu — seit die Verwaltung ausschließlich
   in den Optionen steht (siehe einstellungen.js, eigeneAssistentenZeigen),
   kennt sie deren Seite nicht mehr. Ruft das Menüband ohne Rückfrage-
   Wunsch, bleibt der Parameter leer und es passiert einfach nichts weiter. */
function assistentErstellen(nachAnlegen) {
  umg.fenster('Neuen Assistenten erstellen', [
    { art: 'satz', text: 'Ein eigener Knopf für eine Textaufgabe, die immer '
                       + 'wiederkehrt — zum Beispiel „Fakten prüfen" oder '
                       + '„In Stichpunkte fassen".' },
    { schluessel: 'name', name: 'Name', art: 'text', wert: '' },
    { schluessel: 'prompt', name: 'Prompt', art: 'flaeche', zeilen: 4, wert: '' },
    { schluessel: 'modus', name: 'Aktion', art: 'auswahl', werte: [
        ['hinweis', 'Hinweis — zeigt das Ergebnis als Karte'],
        ['ersetzen', 'Ersetzen — tauscht den Text aus'],
      ], wert: 'hinweis' },
  ], (werte) => {
    const name = (werte.name || '').trim();
    const prompt = (werte.prompt || '').trim();
    if (!name || !prompt) {
      melde('Name und Prompt werden gebraucht — nichts angelegt.');
      return;
    }
    KI.Assistenten.hinzufuegen({ name, prompt, modus: werte.modus });
    if (typeof nachAnlegen === 'function') nachAnlegen();
    melde('„' + name + '" angelegt.');
  }, 'Erstellen');
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
  kiKorrigieren, kiVorschlaege, kiUebersetzen, kiZusammenfassen,
  kiKnoepfeAuffrischen, empfaengerBauen, assistentErstellen, kiAssistentAusfuehren,
  textAktionDialog, kiTextAktionAusfuehren, kiTextAnalyse,
  vorschlaegeLeeren: () => { vorschlaege = []; },
};
}
