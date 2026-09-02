/* ============================================================
   Die Einstellungsseite.

   Sie legt sich über das Blatt statt als Fensterchen mittendrin zu sitzen:
   Schlüssel, Modell und Gedächtnis sind nichts, was man im Vorbeigehen
   einstellt.

   Was das Blatt selbst betrifft — Schriftgröße, Helligkeit, die vier Ecken —
   gehört dem Programm nebenan. Diese Seite fasst es nicht selbst an, sondern
   ruft die Griffe, die programm.js ihr beim Start reicht. Sonst gäbe es zwei
   Stellen, die dasselbe verstellen, und irgendwann widersprächen sie sich.
   ============================================================ */
'use strict';

const Einstellungen = (() => {

const $ = (id) => document.getElementById(id);

/* Die Griffe aus programm.js. Bis sie gereicht sind, tut hier nichts weh:
   leere Funktionen statt Abstürze, falls jemand die Reihenfolge umstellt. */
let griffe = {
  zoom: () => 100,
  zoomSetzen: () => {},
  thema: () => 'auto',
  themaWeiter: () => {},
  marken: () => true,
  markenSetzen: () => {},
  neuZeichnen: () => {},
};

const verbinde = (neue) => { griffe = Object.assign(griffe, neue); };

/* ------------------------------------------------------------
   Der Schlüssel
   ------------------------------------------------------------ */
let schluesselSichtbar = false;
let versteckUhr = null;

function schluesselStandZeigen() {
  const gespeichert = KI.schluesselLies();
  const stand = $('einst-schluessel-stand');
  if (gespeichert) {
    /* Nur Anfang und Ende: Genug, um zwei Schlüssel auseinanderzuhalten,
       zu wenig, um über die Schulter mitgelesen zu werden. */
    stand.textContent = 'Gespeichert: ' + gespeichert.slice(0, 11) + '…'
                      + gespeichert.slice(-4);
  } else if (KI.istLokal(KI.modellJetzt())) {
    stand.textContent = 'Kein Schlüssel — für das Modell auf diesem Rechner '
                      + 'braucht es auch keinen.';
  } else {
    stand.textContent = 'Kein Schlüssel gespeichert — deshalb sind die KI-Knöpfe grau.';
  }
}

function schluesselZeigen() {
  const feld = $('einst-schluessel');
  schluesselSichtbar = !schluesselSichtbar;
  feld.type = schluesselSichtbar ? 'text' : 'password';
  $('einst-zeigen').textContent = schluesselSichtbar ? '👁 Verbergen' : '👁 Anzeigen';

  clearTimeout(versteckUhr);
  /* Von selbst wieder zu: Ein Schlüssel, der offen stehen bleibt, wird
     irgendwann vergessen — und dann steht er offen, während jemand anders
     auf den Bildschirm sieht. */
  if (schluesselSichtbar) versteckUhr = setTimeout(schluesselZeigen, 20000);
}

async function kopiere(text, meldung, ziel) {
  try {
    await navigator.clipboard.writeText(text);
    ziel.textContent = meldung;
  } catch (e) {
    /* Ohne Zwischenablage bleibt der alte Weg: markieren und Strg+C. Besser
       als eine Meldung, die sagt, es ginge nicht. */
    const feld = document.createElement('textarea');
    feld.value = text;
    feld.setAttribute('readonly', '');
    feld.style.position = 'fixed';
    feld.style.left = '-1000px';
    document.body.appendChild(feld);
    feld.select();
    const ging = document.execCommand('copy');
    document.body.removeChild(feld);
    ziel.textContent = ging ? meldung : 'Das Kopieren hat nicht geklappt.';
  }
}

/* ------------------------------------------------------------
   Das Modell

   Was auf diesem Rechner liegt, weiß nur der Rechner. Die Liste kommt
   deshalb beim Öffnen frisch vom Dienst — eine fest eingebaute wäre schon
   falsch, sobald jemand ein Modell dazuholt.
   ------------------------------------------------------------ */
async function lokaleModelleNachtragen() {
  const kasten = $('einst-modell-lokal');
  const gewaehlt = KI.modellJetzt();

  try {
    const namen = await KI.ollamaModelle();
    kasten.innerHTML = '';

    if (!namen.length) {
      kasten.disabled = true;
      kasten.label = 'Auf diesem Rechner — kein Modell geladen';
      return;
    }

    kasten.disabled = false;
    kasten.label = 'Auf diesem Rechner — kostenlos, ohne Internet';
    for (const name of namen) {
      const eintrag = document.createElement('option');
      eintrag.value = KI.OLLAMA_MARKE + name;
      eintrag.textContent = name;
      kasten.appendChild(eintrag);
    }

    /* Erst jetzt lässt sich ein lokales Modell wieder auswählen: Vorher gab
       es den Eintrag noch gar nicht, und das Feld wäre auf Opus gesprungen. */
    if (KI.istLokal(gewaehlt)) $('einst-modell').value = gewaehlt;
    modellHinweisZeigen();

  } catch (e) {
    kasten.innerHTML = '';
    kasten.disabled = true;
    /* Läuft der Dienst nicht, ist das kein Fehler, sondern der Normalfall.
       Also steht es als Beschriftung da und nicht als Warnung. */
    kasten.label = 'Auf diesem Rechner — Ollama läuft nicht';
  }
}

function modellHinweisZeigen() {
  const modell = $('einst-modell').value;
  const hinweis = $('einst-modell-hinweis');
  if (KI.istLokal(modell)) {
    hinweis.textContent = 'Läuft auf diesem Rechner: kostenlos, ohne Internet, der '
      + 'Text bleibt hier. Dauert länger und korrigiert gröber als Claude.';
  } else {
    hinweis.textContent = 'Läuft im Netz: braucht Schlüssel und Guthaben, antwortet '
      + 'in Sekunden. Der Text geht dafür an Anthropic.';
  }
}

/* ------------------------------------------------------------
   Verbrauch und Gedächtnis
   ------------------------------------------------------------ */
function kostenZeigen() {
  const cent = KI.kostenStand();
  $('einst-kosten-stand').textContent = cent
    ? 'Bisher ' + KI.alsGeld(cent) + ' — von diesem Programm mitgezählt.'
    : 'Noch nichts verbraucht.';
  $('einst-kosten-weg').hidden = !cent;
}

function gedaechtnisZeigen() {
  const { woerter, inRuhe } = KI.Gedaechtnis.stand();
  const teile = [];
  if (woerter) teile.push(woerter === 1 ? '1 eigene Schreibweise' : woerter + ' eigene Schreibweisen');
  if (inRuhe)  teile.push(inRuhe === 1 ? '1 Wort in Ruhe gelassen' : inRuhe + ' Wörter in Ruhe gelassen');

  $('einst-gelernt-stand').textContent = teile.length
    ? teile.join(' · ')
    : 'Noch nichts gelernt. Jedes „Ändern" bringt dem Programm etwas bei.';
  $('einst-gelernt-weg').hidden = teile.length === 0;
}

/* ------------------------------------------------------------
   Darstellung
   ------------------------------------------------------------ */
function darstellungZeigen() {
  const zoom = griffe.zoom();
  $('einst-zoom-stand').textContent = 'Schriftgröße: ' + zoom + ' %';
  $('einst-probe').style.fontSize = (12 * zoom / 100).toFixed(1) + 'pt';
  $('einst-marken').checked = griffe.marken();
  $('einst-wellen').checked = Dokument.feld.spellcheck;
}

/* ------------------------------------------------------------
   Auf- und zumachen
   ------------------------------------------------------------ */
let offen = false;

function oeffnen() {
  $('einstellungen').hidden = false;
  offen = true;

  $('einst-schluessel').value = KI.schluesselLies();
  $('einst-modell').value = KI.modellJetzt();
  schluesselStandZeigen();
  modellHinweisZeigen();
  kostenZeigen();
  gedaechtnisZeigen();
  darstellungZeigen();

  /* Dauert einen Moment und darf das Aufgehen nicht aufhalten. */
  lokaleModelleNachtragen();
}

function schliessen() {
  /* Was im Schlüsselfeld steht, gilt beim Zumachen — ein eigener
     „Speichern"-Knopf für ein einzelnes Feld wäre eine Falle: Wer ihn
     übersieht, hat den Schlüssel eingetippt und trotzdem keinen. */
  schluesselUebernehmen();
  $('einstellungen').hidden = true;
  offen = false;
  if (schluesselSichtbar) schluesselZeigen();
  griffe.neuZeichnen();
}

function schluesselUebernehmen() {
  const wert = $('einst-schluessel').value.trim();
  if (wert && wert !== KI.schluesselLies()) KI.schluesselSetzen(wert);
}

/* ------------------------------------------------------------
   Verdrahtung
   ------------------------------------------------------------ */
function verdrahten() {
  for (const sprache of KI.SPRACHEN) {
    const eintrag = document.createElement('option');
    eintrag.value = sprache;
    eintrag.textContent = sprache;
    $('einst-sprache').appendChild(eintrag);
  }
  $('einst-sprache').value = KI.Speicher.lies('sprache', 'Englisch');
  $('einst-sprache').addEventListener('change', (e) => {
    KI.Speicher.schreib('sprache', e.target.value);
    griffe.neuZeichnen();
  });

  $('einst-zu').addEventListener('click', schliessen);
  $('einst-fertig').addEventListener('click', schliessen);

  $('einst-zeigen').addEventListener('click', schluesselZeigen);

  $('einst-kopieren').addEventListener('click', () => {
    const wert = $('einst-schluessel').value.trim() || KI.schluesselLies();
    if (!wert) { $('einst-schluessel-stand').textContent = 'Es steht kein Schlüssel da.'; return; }
    kopiere(wert, 'Schlüssel kopiert.', $('einst-schluessel-stand'));
  });

  $('einst-schluessel').addEventListener('change', () => {
    schluesselUebernehmen();
    schluesselStandZeigen();
    griffe.neuZeichnen();
  });

  $('einst-schluessel-weg').addEventListener('click', () => {
    KI.schluesselLoeschen();
    $('einst-schluessel').value = '';
    schluesselStandZeigen();
    griffe.neuZeichnen();
  });

  $('einst-modell').addEventListener('change', (e) => {
    KI.modellSetzen(e.target.value);
    modellHinweisZeigen();
    schluesselStandZeigen();
    griffe.neuZeichnen();
  });

  $('einst-kosten-weg').addEventListener('click', () => { KI.kostenLeeren(); kostenZeigen(); });

  $('einst-gelernt-weg').addEventListener('click', () => { KI.Gedaechtnis.leeren(); gedaechtnisZeigen(); });

  $('einst-sichern').addEventListener('click', () => {
    const { woerter, inRuhe } = KI.Gedaechtnis.stand();
    if (!woerter && !inRuhe) {
      $('einst-gelernt-stand').textContent = 'Noch nichts gelernt — es gibt nichts zu sichern.';
      return;
    }
    kopiere(KI.sicherungBauen(),
            'Gedächtnis kopiert. Auf dem anderen Gerät „Einspielen" drücken.',
            $('einst-gelernt-stand'));
  });

  $('einst-einspielen').addEventListener('click', () => {
    const roh = window.prompt('Sicherungs-Text vom anderen Gerät hier einfügen:');
    if (roh === null || !roh.trim()) return;

    const ergebnis = KI.sicherungEinspielen(roh);
    if (ergebnis.fehler) { $('einst-gelernt-stand').textContent = ergebnis.fehler; return; }

    // Die Einstellungen können sich geändert haben — die Felder nachziehen.
    $('einst-modell').value = KI.modellJetzt();
    $('einst-sprache').value = KI.Speicher.lies('sprache', 'Englisch');
    modellHinweisZeigen();
    gedaechtnisZeigen();
    griffe.neuZeichnen();

    $('einst-gelernt-stand').textContent = 'Eingespielt: ' + ergebnis.neueWoerter
      + ' Schreibweisen, ' + ergebnis.neueRuhe + ' Wörter in Ruhe. '
      + 'Was hier schon stand, blieb erhalten.';
  });

  $('einst-marken').addEventListener('change', (e) => griffe.markenSetzen(e.target.checked));

  $('einst-wellen').addEventListener('change', (e) => {
    Dokument.feld.spellcheck = e.target.checked;
    KI.Speicher.schreib('wellen', e.target.checked);
    /* Der Browser prüft erst beim nächsten Hineinklicken neu. Einmal weg und
       wieder her, dann verschwinden die Linien sofort. */
    Dokument.feld.blur();
    Dokument.feld.focus();
  });

  $('einst-kleiner').addEventListener('click', () => { griffe.zoomSetzen(griffe.zoom() - 10); darstellungZeigen(); });
  $('einst-groesser').addEventListener('click', () => { griffe.zoomSetzen(griffe.zoom() + 10); darstellungZeigen(); });
  $('einst-thema').addEventListener('click', () => { griffe.themaWeiter(); darstellungZeigen(); });

  $('einst-fassung').textContent = 'Schreibprogramm 1.1 · Prüfung und Wortschatz '
    + 'aus der Schreibhilfe';

  /* Die Wellenlinien gelten ab dem Start, nicht erst nach einem Besuch hier. */
  Dokument.feld.spellcheck = KI.Speicher.lies('wellen', true);
}

verdrahten();

return { oeffnen, schliessen, verbinde, offen: () => offen, gedaechtnisZeigen };
})();
