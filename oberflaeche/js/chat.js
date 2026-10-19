/* ==========================================================================
   Der KI-Chat.

   Ein eigener Bereich in der Schreibhilfe-Seitenleiste: Statt eines
   einzelnen Knopfes für eine feste Aufgabe (Korrigieren, Übersetzen,
   Zusammenfassen) steht hier ein offenes Gespräch — „was fehlt in diesem
   Brief noch", „wie fange ich eine Bewerbung an". Die Anfrage dahinter ist
   dieselbe wie überall in ki.js; neu ist nur, dass mehrere Runden
   zusammengehören und dass der Chat den Dokumenttext als Auskunft
   mitschickt, statt dass jemand ihn hineinkopiert.

   Jede Antwort der KI trägt eine Reihe kleiner Knöpfe — Kopieren,
   Einfügen, Ersetzen, Als Kommentar, Als Überprüfung —, wie im Vorbild.
   War beim Fragen ein Stück Text markiert, hält die Antwort diese
   Markierung fest (als DOM-Range, nicht als Zeichenkette), damit
   „Originaltext ersetzen" später noch weiß, welche Stelle gemeint war.

   WAS „umg" IST

   Vier Namen: „melde" für die Statuszeile, „tafelOffen" und „tafelZeigen"
   für die Seitenleiste — der Chat sitzt in ihr, und wer ihn mit F5
   zugemacht hat, soll sie beim Öffnen des Chats zurückbekommen. „slAuffrischen"
   sagt dem schmalen Symbolband ganz rechts, dass sich der Zustand geändert
   hat — sonst zeigte sein Chat-Knopf „an", obwohl über Strg+/ längst wieder
   zugemacht wurde. Für den Rest — Dokument, KI, Einstellungen — reichen die
   Programm-weiten Namen, wie kiteil.js es auch hält.
   ========================================================================== */
'use strict';

function CHAT_BAUEN(B, umg) {

const $ = (id) => document.getElementById(id);
const melde = (...a) => umg.melde(...a);
const dokFeld = () => Dokument.feld;

const alsSicher = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const alsHtmlZeilen = (text) => text.trim().split('\n').map(alsSicher).join('<br>');

/* Der Verlauf lebt nur im Fenster — ein Gespräch über den heutigen Brief
   ist morgen, bei einem anderen Brief, kein Gewinn mehr. Wer es doch
   braucht, kopiert die Antwort in den Brief. */
let verlauf = [];
let laeuft = false;

/* Die Markierung, die beim Absenden der Frage im Dokument stand — als
   Range, nicht als Text, damit „Originaltext ersetzen" später die
   richtige Stelle trifft, selbst wenn sich davor noch etwas geändert
   hat. Ein „selectionchange"-Zuhörer statt eines Griffs beim Klick auf
   „Senden": Ein echter Mausklick auf den Knopf nimmt dem Dokument die
   Auswahl, bevor der Klick-Handler überhaupt läuft — „mousedown
   preventDefault" allein reichte hier nicht durchgängig. */
let letzteMarkierung = null;

function markierungMerken() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) return;
  const range = auswahl.getRangeAt(0);
  const feld = dokFeld();
  if (!feld || !feld.contains(range.commonAncestorContainer)) return;
  const text = range.toString();
  if (!text.trim()) return;
  letzteMarkierung = { bereich: range.cloneRange(), text };
}
document.addEventListener('selectionchange', markierungMerken);

/* Wohin schreiben, wenn nichts markiert ist: an die aktuelle Schreibstelle
   im Dokument, oder ans Ende, wenn die Auswahl gerade woanders steht (im
   Frage-Feld zum Beispiel). */
function einfuegestelleSetzen() {
  const feld = dokFeld();
  const auswahl = window.getSelection();
  if (auswahl.rangeCount && feld.contains(auswahl.getRangeAt(0).commonAncestorContainer)) return true;
  feld.focus();
  const ende = document.createRange();
  ende.selectNodeContents(feld);
  ende.collapse(false);
  auswahl.removeAllRanges();
  auswahl.addRange(ende);
  return true;
}

async function neuGenerieren(nachricht) {
  if (laeuft) return;
  const index = verlauf.indexOf(nachricht);
  if (index !== verlauf.length - 1) return;   // nur die letzte Antwort lässt sich neu holen

  verlauf.pop();
  laeuft = true;
  zeichnen();
  const dokumentText = Dokument.lies().text;
  let ergebnis;
  try {
    ergebnis = await KI.chatNachricht(verlauf, dokumentText, nachricht.markierterText);
  } finally {
    laeuft = false;
  }
  if (ergebnis.fehler) {
    verlauf.push(nachricht);   // die alte Antwort bleibt lieber stehen als gar keine
    melde(ergebnis.fehler);
    zeichnen();
    return;
  }
  verlauf.push({
    rolle: 'ki', text: ergebnis.text.trim(),
    bereich: nachricht.bereich, markierterText: nachricht.markierterText,
  });
  zeichnen();
}

function kopieren(nachricht) {
  navigator.clipboard.writeText(nachricht.text).then(
    () => melde('In die Zwischenablage kopiert.'),
    () => melde('Kopieren ist nicht gegangen.'));
}

function ergebnisEinfuegen(nachricht) {
  einfuegestelleSetzen();
  Dokument.einfuegen(alsHtmlZeilen(nachricht.text));
  melde('Eingefügt. Strg+Z macht es rückgängig.');
}

/* Ersetzt den markierten Text durch die Antwort — „einfuegen" löscht die
   noch stehende Auswahl von selbst (execCommand insertHTML), genau das
   Verhalten, das „Ersetzen" hier braucht. */
function originaltextErsetzen(nachricht) {
  const feld = dokFeld();
  if (!nachricht.bereich || !feld.contains(nachricht.bereich.commonAncestorContainer)) {
    melde('Die markierte Stelle gibt es im Dokument nicht mehr.');
    return;
  }
  const auswahl = window.getSelection();
  auswahl.removeAllRanges();
  auswahl.addRange(nachricht.bereich.cloneRange());
  Dokument.einfuegen(alsHtmlZeilen(nachricht.text));
  melde('Text ersetzt. Strg+Z macht es rückgängig.');
}

/* Die Antwort als Kommentar an die markierte Stelle anhängen — der Text
   dort bleibt stehen, nur die Kommentar-Marke kommt dahinter, genau wie
   bei einem von Hand gesetzten Kommentar. Deshalb dieselbe Form:
   „span.kommentar" mit dem Text im Titel und einem Zeitstempel für die
   Sortierung in der Kommentare-Tafel. */
function alsKommentarEinfuegen(nachricht) {
  if (!nachricht.bereich || nachricht.eingefuegt) return;
  const feld = dokFeld();

  const ende = nachricht.bereich.cloneRange();
  if (!feld.contains(ende.endContainer)) {
    melde('Die markierte Stelle gibt es im Dokument nicht mehr.');
    return;
  }
  ende.collapse(false);
  const auswahl = window.getSelection();
  auswahl.removeAllRanges();
  auswahl.addRange(ende);

  const autor = (KI.Speicher.lies('kommentarAutor', '') || '').trim() || 'Ich';
  const marke = '<span class="kommentar" contenteditable="false" data-zeit="' + Date.now()
              + '" data-autor="' + autor.replace(/"/g, '&quot;')
              + '" title="' + nachricht.text.replace(/"/g, '&quot;') + '">✎</span>';
  Dokument.einfuegen(marke);
  nachricht.eingefuegt = true;
  zeichnen();
  melde('Als Kommentar eingefügt. Strg+Z macht es rückgängig.');
}

/* Wie ein von Hand getippter Text bei eingeschaltetem „Änderungen
   verfolgen": Neues steht in <ins>, Ersetztes bleibt durchgestrichen in
   <del> stehen — unabhängig davon, ob „Änderungen verfolgen" gerade an
   ist. Dieselben zwei Klassennamen wie dort (programm.js), damit
   „Alle übernehmen/verwerfen" und der Überarbeitungsbereich sie finden. */
function alsUeberpruefungEinfuegen(nachricht) {
  const feld = dokFeld();
  const ins = document.createElement('ins');
  ins.className = 'verfolgt';
  ins.textContent = nachricht.text.trim();

  if (nachricht.bereich) {
    if (!feld.contains(nachricht.bereich.commonAncestorContainer)) {
      melde('Die markierte Stelle gibt es im Dokument nicht mehr.');
      return;
    }
    const bereich = nachricht.bereich.cloneRange();
    const del = document.createElement('del');
    del.className = 'verfolgt';
    del.appendChild(bereich.extractContents());
    bereich.insertNode(del);
    del.after(ins);
  } else {
    einfuegestelleSetzen();
    const auswahl = window.getSelection();
    const ziel = auswahl.getRangeAt(0);
    ziel.deleteContents();
    ziel.insertNode(ins);
  }

  document.dispatchEvent(new CustomEvent('dokument:geaendert'));
  melde('Als Überprüfung eingefügt — sichtbar im Überarbeitungsbereich.');
}

/* Die Knopfreihe unter jeder KI-Antwort. Immer da: Neu generieren (nur
   bei der letzten Antwort drückbar), Kopieren, Ergebnis einfügen. Nur
   wenn beim Fragen etwas markiert war, dazu: Originaltext ersetzen,
   In Kommentar (nur einmal — „eingefuegt" sperrt sie danach), Als
   Überprüfung. */
function aktionenBauen(nachricht, index) {
  const reihe = document.createElement('div');
  reihe.className = 'chat__aktionen';

  const knopf = (text, tun, aus) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'chat__aktion';
    k.textContent = text;
    k.disabled = !!aus;
    if (!aus) k.addEventListener('click', tun);
    return k;
  };

  reihe.appendChild(knopf('Neu generieren', () => neuGenerieren(nachricht), index !== verlauf.length - 1));
  reihe.appendChild(knopf('Kopieren', () => kopieren(nachricht)));
  reihe.appendChild(knopf('Ergebnis einfügen', () => ergebnisEinfuegen(nachricht)));

  if (nachricht.bereich) {
    reihe.appendChild(knopf('Originaltext ersetzen', () => originaltextErsetzen(nachricht)));
    reihe.appendChild(knopf('In Kommentar', () => alsKommentarEinfuegen(nachricht), !!nachricht.eingefuegt));
    reihe.appendChild(knopf('Als Überprüfung', () => alsUeberpruefungEinfuegen(nachricht)));
  }

  return reihe;
}

function zeichnen() {
  const liste = $('chat-verlauf');
  if (!liste) return;
  liste.innerHTML = '';

  if (!verlauf.length) {
    const leer = document.createElement('p');
    leer.className = 'chat__leer';
    leer.textContent = 'Frag etwas zum Text oder zum Schreiben — zum Beispiel '
                      + '„Was fehlt in diesem Brief noch?"';
    liste.appendChild(leer);
  }

  verlauf.forEach((nachricht, index) => {
    const zeile = document.createElement('div');
    zeile.className = 'chat__nachricht chat__nachricht--' + nachricht.rolle;
    zeile.textContent = nachricht.text;
    liste.appendChild(zeile);

    if (nachricht.rolle === 'ki') liste.appendChild(aktionenBauen(nachricht, index));
  });

  if (laeuft) {
    const wartet = document.createElement('div');
    wartet.className = 'chat__nachricht chat__nachricht--ki chat__nachricht--wartet';
    wartet.textContent = 'Die KI überlegt …';
    liste.appendChild(wartet);
  }

  liste.scrollTop = liste.scrollHeight;
}

async function senden() {
  const feld = $('chat-eingabe');
  const text = feld.value.trim();
  if (!text || laeuft) return;

  if (!KI.verfuegbar()) {
    melde('Dafür fehlt der KI-Schlüssel — hier gehört er hin.');
    Einstellungen.oeffnen();
    return;
  }

  /* Die Markierung wird JETZT verbraucht — beantwortet die Frage nicht
     diese Runde, gilt sie auch für die nächste nicht mehr automatisch.
     Schlägt die Anfrage fehl, kommt sie zurück (siehe unten), damit ein
     zweiter Versuch nicht ohne sie dasteht. */
  const markierung = letzteMarkierung;
  letzteMarkierung = null;

  verlauf.push({ rolle: 'mensch', text });
  feld.value = '';
  laeuft = true;
  $('chat-senden').disabled = true;
  zeichnen();

  const dokumentText = Dokument.lies().text;
  let ergebnis;
  try {
    ergebnis = await KI.chatNachricht(verlauf, dokumentText, markierung ? markierung.text : '');
  } finally {
    laeuft = false;
    $('chat-senden').disabled = false;
  }

  if (ergebnis.fehler) {
    verlauf.pop();
    feld.value = text;
    letzteMarkierung = markierung;
    melde(ergebnis.fehler);
    zeichnen();
    return;
  }

  verlauf.push({
    rolle: 'ki', text: ergebnis.text.trim(),
    bereich: markierung ? markierung.bereich : null,
    markierterText: markierung ? markierung.text : '',
  });
  zeichnen();
}

/* ---- Auf- und zumachen ----

   Der Chat ersetzt die gewohnte Schreibhilfe-Ansicht, statt neben ihr zu
   stehen — die Seitenleiste ist schmal, für beides nebeneinander reicht
   der Platz nicht. „Zur Schreibhilfe" führt zurück; nichts geht dabei
   verloren, der Verlauf bleibt, bis das Fenster schließt. */
function offen() {
  return !$('tafel-chat').hidden;
}

function zeigen() {
  $('tafel-schreibhilfe').hidden = true;
  $('tafel-chat').hidden = false;
  zeichnen();
  $('chat-eingabe').focus();
  if (umg.slAuffrischen) umg.slAuffrischen();
}

function verbergen() {
  $('tafel-chat').hidden = true;
  $('tafel-schreibhilfe').hidden = false;
  if (umg.slAuffrischen) umg.slAuffrischen();
}

function umschalten() {
  /* Die Seitenleiste kann zu sein (F5) — dann zuerst auf, sonst sieht man
     den Chat nicht, obwohl er offen ist. */
  if (!umg.tafelOffen()) umg.tafelZeigen();
  if (offen()) verbergen(); else zeigen();
}

const knopfSenden = $('chat-senden');
const feldEingabe = $('chat-eingabe');
const knopfSchliessen = $('chat-schliessen');
if (knopfSenden) {
  /* Ein echter Klick nimmt dem Dokument die Auswahl, bevor „senden"
     läuft — „mousedown preventDefault" schützt davor, genau wie bei den
     Knöpfen im Rechtsklickmenü. Der „selectionchange"-Zuhörer oben fängt
     den Rest ab, der hierdurch nicht abgedeckt ist. */
  knopfSenden.addEventListener('mousedown', (e) => e.preventDefault());
  knopfSenden.addEventListener('click', senden);
}
if (knopfSchliessen) knopfSchliessen.addEventListener('click', verbergen);
if (feldEingabe) {
  /* Enter schickt ab, Umschalt+Enter macht eine neue Zeile — wie überall,
     wo mehrzeilig getippt werden kann. */
  feldEingabe.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); senden(); }
  });
}

return { umschalten, zeigen, verbergen };
}
