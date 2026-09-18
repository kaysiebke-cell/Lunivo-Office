/* ==========================================================================
   Der KI-Chat.

   Ein eigener Bereich in der Schreibhilfe-Seitenleiste: Statt eines
   einzelnen Knopfes für eine feste Aufgabe (Korrigieren, Übersetzen,
   Zusammenfassen) steht hier ein offenes Gespräch — „was fehlt in diesem
   Brief noch", „wie fange ich eine Bewerbung an". Die Anfrage dahinter ist
   dieselbe wie überall in ki.js; neu ist nur, dass mehrere Runden
   zusammengehören und dass der Chat den Dokumenttext als Auskunft
   mitschickt, statt dass jemand ihn hineinkopiert.

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

/* Der Verlauf lebt nur im Fenster — ein Gespräch über den heutigen Brief
   ist morgen, bei einem anderen Brief, kein Gewinn mehr. Wer es all das
   Mal braucht, kopiert die Antwort in den Brief; „Am Anfang einfügen" gibt
   es hier deshalb bewusst nicht, anders als bei der Hinweiskarte. */
let verlauf = [];
let laeuft = false;

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

  for (const nachricht of verlauf) {
    const zeile = document.createElement('div');
    zeile.className = 'chat__nachricht chat__nachricht--' + nachricht.rolle;
    zeile.textContent = nachricht.text;
    liste.appendChild(zeile);
  }

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

  verlauf.push({ rolle: 'mensch', text });
  feld.value = '';
  laeuft = true;
  $('chat-senden').disabled = true;
  zeichnen();

  const dokumentText = Dokument.lies().text;
  let ergebnis;
  try {
    ergebnis = await KI.chatNachricht(verlauf, dokumentText);
  } finally {
    laeuft = false;
    $('chat-senden').disabled = false;
  }

  if (ergebnis.fehler) {
    /* Die Frage bleibt sonst unbeantwortet im Verlauf stehen — besser, sie
       geht zurück ins Feld, damit „noch einmal senden" nicht neu getippt
       werden muss. */
    verlauf.pop();
    feld.value = text;
    melde(ergebnis.fehler);
    zeichnen();
    return;
  }

  verlauf.push({ rolle: 'ki', text: ergebnis.text.trim() });
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
if (knopfSenden) knopfSenden.addEventListener('click', senden);
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
