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
   Der Baum links

   Die Reihenfolge ist die des Writers, soweit es hier etwas dazu gibt:
   erst wer schreibt, dann womit, dann wie es aussieht, zuletzt das
   Zusätzliche. Wer den Writer kennt, sucht nicht zweimal.
   ------------------------------------------------------------ */
const BEREICHE = [
  ['programm', 'Schreibprogramm', [
    ['benutzer',  'Benutzerdaten'],
    ['ansicht',   'Ansicht'],
    ['schriften', 'Schriftarten'],
    ['pfade',     'Pfade'],
    ['erweitert', 'Erweitert'],
  ]],
  ['pruefung', 'Sprache und Prüfung', [
    ['sprache',   'Sprache'],
    ['schreiben', 'Beim Schreiben'],
  ]],
  ['hilfe', 'Schreibhilfe', [
    ['ki',          'Prüfung und KI'],
    ['gedaechtnis', 'Gedächtnis'],
  ]],
];

let bereichJetzt = 'benutzer';
/* Welche Zweige offen stehen. Alle drei zu Anfang: Wer die Optionen zum
   ersten Mal aufmacht, soll sehen, was es gibt, statt drei zugeklappte
   Wörter zu finden und raten zu müssen, was darunter liegt. */
const offeneZweige = new Set(BEREICHE.map(([kennung]) => kennung));

function bereichZeigen(kennung) {
  bereichJetzt = kennung;
  for (const gruppe of document.querySelectorAll('#einst-bereiche .gruppe[data-bereich]')) {
    gruppe.classList.toggle('gruppe--offen', gruppe.dataset.bereich === kennung);
  }
  for (const ast of document.querySelectorAll('.optionen__ast')) {
    const gewaehlt = ast.dataset.bereich === kennung;
    ast.classList.toggle('optionen__ast--offen', gewaehlt);
    ast.setAttribute('aria-selected', gewaehlt ? 'true' : 'false');
  }
  /* „Schlüssel löschen" gehört zur KI und sonst nirgendwohin. Unter den
     Benutzerdaten stehend liest er sich, als lösche er die Adresse. */
  $('einst-schluessel-weg').hidden = kennung !== 'ki';

  /* Beim Wechsel wieder nach oben: Wer von „Erweitert" nach
     „Benutzerdaten" springt, säße sonst mitten im neuen Bereich. */
  $('einst-bereiche').scrollTop = 0;
}

function baumBauen() {
  const baum = $('einst-baum');
  baum.innerHTML = '';

  for (const [zweigKennung, zweigName, blaetter] of BEREICHE) {
    const offen = offeneZweige.has(zweigKennung);

    const zweig = document.createElement('button');
    zweig.type = 'button';
    zweig.className = 'optionen__zweig';
    zweig.setAttribute('aria-expanded', offen ? 'true' : 'false');

    const pfeil = document.createElement('span');
    pfeil.className = 'optionen__pfeil';
    pfeil.textContent = offen ? '▾' : '▸';
    zweig.appendChild(pfeil);
    zweig.appendChild(document.createTextNode(zweigName));

    /* Ein Klick auf den Zweig klappt auf und zu. Er wählt selbst nichts aus:
       Hinter „Schreibprogramm" liegt keine Seite, sondern fünf. */
    zweig.addEventListener('click', () => {
      if (offeneZweige.has(zweigKennung)) offeneZweige.delete(zweigKennung);
      else offeneZweige.add(zweigKennung);
      baumBauen();
    });
    baum.appendChild(zweig);

    const kasten = document.createElement('div');
    kasten.className = 'optionen__blaetter';
    kasten.hidden = !offen;

    for (const [kennung, name] of blaetter) {
      const ast = document.createElement('button');
      ast.type = 'button';
      ast.className = 'optionen__ast';
      ast.dataset.bereich = kennung;
      ast.textContent = name;
      ast.setAttribute('role', 'tab');
      ast.addEventListener('click', () => bereichZeigen(kennung));
      kasten.appendChild(ast);
    }
    baum.appendChild(kasten);
  }

  bereichZeigen(bereichJetzt);
}

/* Zu welchem Zweig gehört ein Blatt? Wird gebraucht, wenn ein Menüpunkt
   geradewegs in einen Bereich springt, dessen Zweig zugeklappt ist. */
function zweigVon(blatt) {
  for (const [zweigKennung, , blaetter] of BEREICHE) {
    if (blaetter.some(([kennung]) => kennung === blatt)) return zweigKennung;
  }
  return null;
}

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

function oeffnen(bereich) {
  $('einstellungen').hidden = false;
  offen = true;

  if (bereich) {
    bereichJetzt = bereich;
    const zweig = zweigVon(bereich);
    if (zweig) offeneZweige.add(zweig);
  }
  baumBauen();

  benutzerZeigen();
  schriftenZeigen();
  spracheZeigen();
  pfadZeigen();
  bedienungZeigen();
  teileZeigen();

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

/* ------------------------------------------------------------
   Benutzerdaten

   Sie stehen im Writer ganz oben, und das aus gutem Grund: Umschlag,
   Etiketten, Seriendruck und der Verfasser eines Dokuments fragen alle
   nach demselben. Wer sie hier einträgt, tippt sie nirgends noch einmal.
   ------------------------------------------------------------ */
const BENUTZER_FELDER = ['vorname', 'nachname', 'firma', 'strasse',
                         'plz', 'ort', 'telefon', 'email'];

function benutzerLies() {
  return KI.Speicher.lies('benutzer', {});
}

function benutzerZeigen() {
  const daten = benutzerLies();
  for (const name of BENUTZER_FELDER) {
    const feld = $('einst-' + name);
    if (feld) feld.value = daten[name] || '';
  }
}

function benutzerMerken() {
  const daten = {};
  for (const name of BENUTZER_FELDER) {
    const feld = $('einst-' + name);
    if (feld && feld.value.trim()) daten[name] = feld.value.trim();
  }
  KI.Speicher.schreib('benutzer', daten);
}

/* ------------------------------------------------------------
   Schriftarten und Sprache
   ------------------------------------------------------------ */
function schriftenZeigen() {
  const wahl = $('einst-schrift');
  const alle = griffe.schriften();
  const jetzt = griffe.schriftJetzt();

  wahl.innerHTML = '';
  /* „Wie im Blatt" statt eines Namens: Wer nie etwas eingestellt hat, soll
     nicht raten müssen, welche der 900 Schriften gerade gilt. */
  const grund = document.createElement('option');
  grund.value = '';
  grund.textContent = 'Wie voreingestellt (Georgia)';
  wahl.appendChild(grund);
  for (const name of alle) {
    const o = document.createElement('option');
    o.value = name; o.textContent = name;
    if (name === jetzt) o.selected = true;
    wahl.appendChild(o);
  }
  if (!jetzt) grund.selected = true;

  const gr = $('einst-schriftgroesse');
  gr.innerHTML = '';
  for (const punkte of griffe.groessen()) {
    const o = document.createElement('option');
    o.value = String(punkte); o.textContent = punkte + ' pt';
    if (Number(punkte) === griffe.groesseJetzt()) o.selected = true;
    gr.appendChild(o);
  }
}

/* Größe der Bedienung und die Wahl der Oberfläche. */
function bedienungZeigen() {
  const gr = $('einst-symbolgroesse');
  if (gr) gr.value = griffe.symbolgroesseJetzt();
  const skala = $('einst-skalierung');
  if (skala) {
    skala.value = String(griffe.skalierungJetzt());
    $('einst-skalierung-stand').textContent = skala.value + ' %';
  }
  const fl = $('einst-flaeche');
  if (fl) fl.value = griffe.flaecheJetzt();
}

function spracheZeigen() {
  const wahl = $('einst-pruefsprache');
  const jetzt = griffe.pruefspracheJetzt();
  wahl.innerHTML = '';
  for (const [kennung, name] of griffe.pruefsprachen()) {
    const o = document.createElement('option');
    o.value = kennung; o.textContent = name;
    if (kennung === jetzt) o.selected = true;
    wahl.appendChild(o);
  }
}

/* ------------------------------------------------------------
   Pfade
   ------------------------------------------------------------ */
function pfadZeigen() {
  const feld = $('einst-ordner');
  const gemerkt = KI.Speicher.lies('ordner', '');
  feld.value = gemerkt || '';
  feld.placeholder = gemerkt ? '' : 'Zuletzt benutzter Ordner';
}

/* ------------------------------------------------------------
   Was zusätzlich geholt wurde

   Der Writer nennt diesen Bereich „Erweitert" und meint Java. Hier ist
   gemeint, was außerhalb des Programms liegt, weil es zu groß ist. Ob es
   da ist, kann nur der Rechner sagen — die Seite fragt ihn.
   ------------------------------------------------------------ */
async function teileZeigen() {
  const kasten = $('einst-teile');
  if (!kasten) return;
  kasten.innerHTML = '<p class="hinweis">Wird nachgesehen …</p>';

  let teile = [];
  try {
    const antwort = await fetch('teile');
    if (antwort.ok) teile = await antwort.json();
  } catch (e) { /* im Browser gibt es diese Adresse nicht */ }

  if (!teile.length) {
    kasten.innerHTML = '<p class="hinweis">Nur im eigenen Fenster zu sehen — '
      + 'im Browser weiß die Seite nichts über den Rechner.</p>';
    return;
  }

  kasten.innerHTML = '';
  for (const teil of teile) {
    const zeile = document.createElement('div');
    zeile.className = 'teil' + (teil.da ? ' teil--da' : '');

    const stand = document.createElement('span');
    stand.className = 'teil__stand';
    stand.textContent = teil.da ? 'da' : 'fehlt';
    zeile.appendChild(stand);

    const mitte = document.createElement('div');
    mitte.className = 'teil__mitte';
    const name = document.createElement('span');
    name.className = 'teil__name';
    name.textContent = teil.name;
    const satz = document.createElement('em');
    satz.className = 'teil__satz';
    satz.textContent = teil.da ? teil.wofuer : teil.wofuer + ' — ' + teil.holen;
    mitte.append(name, satz);
    zeile.appendChild(mitte);

    const groesse = document.createElement('span');
    groesse.className = 'teil__groesse';
    groesse.textContent = teil.groesse;
    zeile.appendChild(groesse);

    kasten.appendChild(zeile);
  }
}

function schliessen() {
  benutzerMerken();
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

  /* Benutzerdaten beim Verlassen des Feldes merken — ein eigener
     Speichern-Knopf für acht Felder wäre eine Falle. */
  for (const name of BENUTZER_FELDER) {
    const feld = $('einst-' + name);
    if (feld) feld.addEventListener('change', benutzerMerken);
  }

  $('einst-schrift').addEventListener('change', () => {
    griffe.grundschriftSetzen($('einst-schrift').value, undefined);
  });
  $('einst-schriftgroesse').addEventListener('change', () => {
    griffe.grundschriftSetzen(undefined, $('einst-schriftgroesse').value);
  });
  $('einst-symbolgroesse').addEventListener('change', () => {
    griffe.bedienungSetzen($('einst-symbolgroesse').value, undefined);
  });
  $('einst-skalierung').addEventListener('input', () => {
    const wert = $('einst-skalierung').value;
    $('einst-skalierung-stand').textContent = wert + ' %';
    griffe.bedienungSetzen(undefined, wert);
  });
  $('einst-flaeche').addEventListener('change', () => {
    griffe.flaecheSetzen($('einst-flaeche').value);
  });

  $('einst-pruefsprache').addEventListener('change', () => {
    griffe.pruefspracheSetzen($('einst-pruefsprache').value);
  });

  $('einst-ordner-waehlen').addEventListener('click', async () => {
    try {
      const antwort = await fetch('ordner-waehlen', { method: 'POST' });
      if (!antwort.ok) return;
      const weg = (await antwort.json()).ordner || '';
      if (weg) KI.Speicher.schreib('ordner', weg);
      pfadZeigen();
    } catch (e) { /* nur im eigenen Fenster */ }
  });
  $('einst-ordner-weg').addEventListener('click', () => {
    KI.Speicher.loesch ? KI.Speicher.loesch('ordner') : KI.Speicher.schreib('ordner', '');
    pfadZeigen();
  });

  $('einst-fassung').textContent = 'Schreibprogramm 1.2 · Prüfung und Wortschatz '
    + 'aus der Schreibhilfe';

  /* Die Wellenlinien gelten ab dem Start, nicht erst nach einem Besuch hier. */
  Dokument.feld.spellcheck = KI.Speicher.lies('wellen', true);
}

verdrahten();

return { oeffnen, schliessen, verbinde, offen: () => offen, gedaechtnisZeigen };
})();
