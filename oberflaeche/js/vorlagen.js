/* ==========================================================================
   Die Seite „Neu" — Vorlagen als Blätter statt als Liste

   Vorher stand hier ein Klappmenü mit Namen und ein Auswahlfeld im Fenster.
   Beides beantwortet die Frage nicht, die man vor dem Öffnen hat: Wie sieht
   die aus? Word legt dafür eine ganze Fläche an, mit Miniaturblättern, und
   das ist die richtige Antwort — ein Dokument erkennt man am Blatt, nicht
   am Dateinamen.

   Die Fläche legt sich über alles, wie die Druckvorschau und die
   Einstellungen. Ein Fensterchen in der Mitte hätte für zwölf Blätter
   nicht gereicht, und beim dreizehnten hätte es gescrollt.

   WAS ES HIER NICHT GIBT

   Words linker Reiter holt Vorlagen aus dem Netz. Das geht hier nicht und
   soll nicht: Was geschrieben wird, bleibt auf diesem Rechner, und ein
   Programm, das beim Öffnen einer leeren Seite ins Internet greift, hält
   dieses Versprechen nicht. An die Stelle treten die Ordner, die wirklich
   da sind — und die füllt der Mensch selbst.

   Deshalb ist die leere Fläche die Ansicht, die zuerst und am längsten zu
   sehen ist. Sie darf nicht wie ein Fehler aussehen. Dort steht, was eine
   Vorlage überhaupt ist, wo der Ordner liegt und wie etwas hineinkommt.

   DIE MINIATURBLÄTTER sind keine Abbildung des Inhalts. Sie zeigen den
   Namen und graue Striche — genau wie Word bei den eigenen Vorlagen. Eine
   echte Abbildung hieße: LibreOffice rendert jede Datei, bei jedem
   Aufklappen. Das kostet Sekunden, die niemand hat, während er auf ein
   leeres Blatt wartet.

   WAS DIESE DATEI NICHT KENNT

   Das Programm nebenan. Was sie von dort braucht, wird ihr beim Start
   gereicht — sechs Griffe, mehr nicht. Sie liest keine Datei und fragt den
   Server nicht: Die Liste bekommt sie beim Öffnen gereicht, und geöffnet
   wird über die Nummer, die darin steht. Das Einzige, was sie selbst
   behält, sind die Nadeln — sie gehören zu dieser Fläche und sonst
   nirgendwohin.
   ========================================================================== */
'use strict';

const Vorlagen = (() => {

const $ = (id) => document.getElementById(id);

/* Die Griffe aus programm.js. Bis sie gereicht sind, tut hier nichts weh. */
let griffe = {
  symbol: () => document.createElementNS('http://www.w3.org/2000/svg', 'svg'),
  oeffneNr: () => {},          /* eine Abschrift der n-ten Vorlage öffnen */
  leeresDokument: () => {},
  ordnerOeffnen: () => {},
  behalten: () => {},
  zurueck: () => {},           /* wieder ins Blatt, Schreibmarke dorthin */
  oeffneMuster: () => {},      /* ein mitgeliefertes Gerüst ins Blatt setzen */
  benutzer: () => ({}),        /* Name und Anschrift aus den Einstellungen */
};

const verbinde = (neue) => { griffe = Object.assign(griffe, neue); };

/* ------------------------------------------------------------
   Zustand

   „fest" sind die angehefteten Vorlagen. Gemerkt wird nicht die Nummer —
   die verschiebt sich, sobald eine Datei dazukommt —, sondern Ordner und
   Dateiname. Wer eine Vorlage wegwirft, verliert damit auch ihre Nadel,
   und das ist richtig so.
   ------------------------------------------------------------ */
let liste = [];
let fest = [];
let gruppeJetzt = null;        /* welcher Reiter offen ist; null = alle */
let suchwort = '';
let offen = false;

const marke = (v) => (v.muster
  ? 'muster/' + v.muster
  : (v.ordner || '') + '/' + (v.datei || v.name));

/* ------------------------------------------------------------
   Die Reiter — einer je Ordner

   Bei einem einzigen Ordner steht hier keiner. Ein Reiter, der nichts
   unterscheidet, ist eine Zeile Lärm über einer Fläche, die ohnehin knapp
   ist. Erst wenn wirklich zwei Ordner etwas enthalten, gibt es etwas zu
   wählen — und dann auch ein „Alle" davor.
   ------------------------------------------------------------ */
function reiterZeichnen() {
  const feld = $('neuseite-reiter');
  const gruppen = [];
  for (const v of liste) if (!gruppen.includes(v.gruppe)) gruppen.push(v.gruppe);

  feld.textContent = '';
  if (gruppen.length < 2) { feld.hidden = true; gruppeJetzt = null; return; }
  feld.hidden = false;

  /* Steht der offene Reiter nicht mehr in der Liste — der Ordner ist leer
     geräumt worden —, dann zurück auf „Alle" statt auf eine leere Fläche. */
  if (gruppeJetzt !== null && !gruppen.includes(gruppeJetzt)) gruppeJetzt = null;

  const alle = [[null, 'Alle', liste.length]];
  for (const g of gruppen) alle.push([g, g, liste.filter((v) => v.gruppe === g).length]);

  for (const [wert, name, zahl] of alle) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.setAttribute('aria-selected', String(gruppeJetzt === wert));
    knopf.append(name);
    const z = document.createElement('span');
    z.className = 'neuseite__zahl';
    z.textContent = zahl;
    knopf.appendChild(z);
    knopf.addEventListener('click', () => { gruppeJetzt = wert; zeichnen(); });
    feld.appendChild(knopf);
  }
}

/* ------------------------------------------------------------
   Die mitgelieferten Gerüste zu Blättern machen

   Aus einer Zeile in daten/vorlagenmuster.js wird ein Absatz. Die Zeichen
   am Anfang sagen, wie er aussieht, die «Winkel» werden zu Lücken — und
   das ist dieselbe Auszeichnung, die die Textbausteine schon benutzen:
   ein <span class="platzhalter">, das Tab anspringt und der Druck weglässt.

   Gebaut wird hier und nicht im Programm nebenan, weil die Kacheln
   dasselbe brauchen: Bei einem mitgelieferten Muster ist die Miniatur
   keine Attrappe aus grauen Strichen, sondern das Blatt selbst, klein
   gerechnet. Zweimal denselben Text zu bauen hieße, dass eines von beiden
   irgendwann etwas anderes zeigt.
   ------------------------------------------------------------ */
const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                'August', 'September', 'Oktober', 'November', 'Dezember'];

const musterListeRoh = () => (typeof VORLAGENMUSTER === 'undefined' ? [] : VORLAGENMUSTER);

/* Was in den Einstellungen steht, sonst eine Lücke. Wer seine Adresse
   einmal hinterlegt hat, findet sie in jedem Brief oben stehen — und wer
   nicht, bekommt an derselben Stelle die Aufforderung, sie einzutragen. */
function absenderZeilen(b, mitName) {
  const name = ((b.vorname || '') + ' ' + (b.nachname || '')).trim();
  const ort = ((b.plz || '') + ' ' + (b.ort || '')).trim();
  const zeilen = [];
  if (mitName) zeilen.push(name || '«Vorname Nachname»');
  zeilen.push(b.strasse || '«Straße und Hausnummer»');
  zeilen.push(ort || '«PLZ und Ort»');
  return zeilen;
}

function ortUndDatum(b) {
  const heute = new Date();
  return (b.ort || '«Ort»') + ', den ' + heute.getDate() + '. '
       + MONATE[heute.getMonth()] + ' ' + heute.getFullYear();
}

/* Die @-Zeichen auflösen: Danach ist jede Zeile nur noch Text mit
   höchstens einem Zeichen davor. */
function musterZeilen(muster) {
  const b = griffe.benutzer() || {};
  const name = ((b.vorname || '') + ' ' + (b.nachname || '')).trim();
  const fertig = [];
  for (const roh of muster[3]) {
    if (roh === '@absender') fertig.push(...absenderZeilen(b, true));
    else if (roh === '@absender2') fertig.push(...absenderZeilen(b, false));
    else if (roh === '@ortdatum') fertig.push('>' + ortUndDatum(b));
    else if (roh === '@name') fertig.push(name || '«Vorname Nachname»');
    else if (roh.includes('@name')) fertig.push(roh.replace('@name', name || '«Vorname Nachname»'));
    /* Ist die Adresse bekannt, steht sie da — dann ist sie keine Lücke
       mehr. Ist sie es nicht, wird an derselben Stelle eine daraus. */
    else if (roh.includes('@mail')) {
      fertig.push(roh.replace('@mail', b.email || '«E-Mail-Adresse»'));
    }
    else fertig.push(roh);
  }
  return fertig;
}

const sicher = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/* Erst sichern, dann die Winkel zu Lücken machen — nicht umgekehrt. Sonst
   würde das <span>, das gerade entstanden ist, gleich wieder zu Text. */
function mitLuecken(text) {
  return sicher(text).replace(/«([^»]*)»/g,
    (_, wort) => '<span class="platzhalter">«' + wort + '»</span>');
}

function zeileAlsHtml(zeile) {
  let art = '';
  let text = zeile;
  if (text.startsWith('#')) { art = 'gross'; text = text.slice(1); }
  else if (text.startsWith('!')) { art = 'fett'; text = text.slice(1); }
  else if (text.startsWith('>')) { art = 'rechts'; text = text.slice(1); }

  if (!text) return '<p><br></p>';
  const innen = mitLuecken(text);
  if (art === 'gross') return '<h1 class="titel">' + innen + '</h1>';
  if (art === 'fett') return '<p><b>' + innen + '</b></p>';
  if (art === 'rechts') return '<p style="text-align:right">' + innen + '</p>';
  return '<p>' + innen + '</p>';
}

/* Was ohne Leerzeile untereinandersteht, gehört zusammen und wird EIN
   Absatz mit Zeilenumbrüchen darin.

   Vorher war jede Zeile ein eigener Absatz — und der Absatzabstand des
   Fließtextes steht auf 2,5 mm. Damit stand die eigene Anschrift so weit
   auseinandergezogen im Briefkopf, als wären es drei Gedanken statt einer
   Adresse. Ein Empfängerfeld ist ein Block, kein Aufzählung.

   Ausgezeichnete Zeilen — Betreff, Überschrift, Ort und Datum — bleiben
   für sich: Sie sehen anders aus, also sind sie ein eigener Absatz. */
function bloecke(zeilen) {
  const raus = [];
  let lauf = [];
  const abschliessen = () => { if (lauf.length) { raus.push(lauf); lauf = []; } };

  for (const zeile of zeilen) {
    if (!zeile) { abschliessen(); raus.push(null); continue; }
    if (/^[#!>]/.test(zeile)) { abschliessen(); raus.push([zeile]); continue; }
    lauf.push(zeile);
  }
  abschliessen();
  return raus;
}

function blockAlsHtml(block) {
  if (block === null) return '<p><br></p>';
  if (block.length === 1) return zeileAlsHtml(block[0]);
  return '<p>' + block.map(mitLuecken).join('<br>') + '</p>';
}

/** Das ganze Blatt eines Musters als HTML — das, was ins Dokument kommt. */
function musterHtml(kennung) {
  const muster = musterListeRoh().find((m) => m[0] === kennung);
  if (!muster) return '';
  return bloecke(musterZeilen(muster)).map(blockAlsHtml).join('');
}

/** Die Muster als Einträge für die Fläche, in derselben Form wie die
    Dateien aus den Ordnern. */
function musterListe() {
  return musterListeRoh().map((m) => ({
    muster: m[0], name: m[1], zweck: m[2], gruppe: 'Mitgeliefert',
  }));
}

/* ------------------------------------------------------------
   Ein Miniaturblatt

   Der Farbstreifen oben trägt keine Bedeutung. Er hilft, zehn weiße
   Blätter auseinanderzuhalten, und richtet sich fest nach dem Namen —
   dieselbe Vorlage bekommt jedes Mal denselben Streifen. Wäre er zufällig,
   sähe die Fläche bei jedem Öffnen anders aus, und dann hilft er nicht
   mehr beim Wiedererkennen, sondern stört.
   ------------------------------------------------------------ */
const STREIFEN = ['', ' mini__balken--gruen', ' mini__balken--warm'];

function streifen(name) {
  let summe = 0;
  for (let i = 0; i < name.length; i++) summe += name.charCodeAt(i);
  return STREIFEN[summe % STREIFEN.length];
}

function endung(datei) {
  const punkt = (datei || '').lastIndexOf('.');
  return punkt > 0 ? datei.slice(punkt + 1).toLowerCase() : '';
}

function striche(mini) {
  /* Sieben Striche mit einer Lücke in der Mitte: der Umriss eines Briefes,
     mehr soll es nicht sein. */
  const breiten = ['', '', ' mini__strich--halb', 'luft', '', '', ' mini__strich--kurz'];
  for (const b of breiten) {
    const zeile = document.createElement('div');
    zeile.className = b === 'luft' ? 'mini__luft' : 'mini__strich' + b;
    mini.appendChild(zeile);
  }
}

function kachelLeeresBlatt() {
  const knopf = document.createElement('button');
  knopf.type = 'button';
  knopf.className = 'kachel';

  const blatt = document.createElement('div');
  blatt.className = 'kachel__blatt';
  const mini = document.createElement('div');
  mini.className = 'mini mini--leer';
  mini.appendChild(griffe.symbol('neu'));
  blatt.appendChild(mini);

  const name = document.createElement('span');
  name.className = 'kachel__name';
  name.textContent = 'Leeres Dokument';

  knopf.append(blatt, name);
  knopf.addEventListener('click', () => { schliessen(); griffe.leeresDokument(); });
  return knopf;
}

function kachelVorlage(v) {
  const angeheftet = fest.includes(marke(v));
  const knopf = document.createElement('button');
  knopf.type = 'button';
  knopf.className = 'kachel' + (angeheftet ? ' kachel--fest' : '');

  const blatt = document.createElement('div');
  blatt.className = 'kachel__blatt';

  if (v.muster) {
    /* Ein mitgeliefertes Gerüst kennen wir Wort für Wort — also zeigt die
       Kachel das Blatt selbst, klein gerechnet, und keine Attrappe. Genau
       das ist der Unterschied zwischen Words linkem und rechtem Reiter:
       Was das Programm kennt, kann es zeigen; was in einem fremden Ordner
       liegt, müsste es erst öffnen. */
    const mini = document.createElement('div');
    mini.className = 'mini mini--echt';
    const seite = document.createElement('div');
    seite.className = 'mini__seite';
    seite.innerHTML = musterHtml(v.muster);
    mini.appendChild(seite);
    blatt.appendChild(mini);
  } else {
    const mini = document.createElement('div');
    mini.className = 'mini';
    const balken = document.createElement('div');
    balken.className = 'mini__balken' + streifen(v.name);
    const kopf = document.createElement('div');
    kopf.className = 'mini__kopf';
    kopf.textContent = v.name;               /* nicht innerHTML: Dateinamen
                                                kommen aus einem Ordner, in
                                                den jeder legen darf, was er
                                                will — auch spitze Klammern. */
    mini.append(balken, kopf);
    striche(mini);
    blatt.appendChild(mini);

    const art = document.createElement('span');
    art.className = 'kachel__art';
    art.textContent = endung(v.datei);
    blatt.appendChild(art);
  }

  /* Die Nadel liegt im Blatt, ist aber kein Knopf im Knopf — das wäre
     ungültiges HTML und ein Klick landete beim falschen von beiden.
     Deshalb ein <span> mit Rolle und Tastaturzugang. */
  const nadel = document.createElement('span');
  nadel.className = 'kachel__nadel';
  nadel.setAttribute('role', 'button');
  nadel.setAttribute('tabindex', '0');
  nadel.title = angeheftet ? 'Nicht mehr anheften' : 'Anheften';
  nadel.setAttribute('aria-label', nadel.title + ': ' + v.name);
  nadel.appendChild(griffe.symbol('nadel'));
  const umlegen = (e) => {
    e.stopPropagation();
    e.preventDefault();
    const m = marke(v);
    fest = angeheftet ? fest.filter((x) => x !== m) : fest.concat([m]);
    KI.Speicher.schreib('vorlagenFest', fest);
    zeichnen();
  };
  nadel.addEventListener('click', umlegen);
  nadel.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') umlegen(e);
  });
  blatt.appendChild(nadel);

  const name = document.createElement('span');
  name.className = 'kachel__name';
  name.append(v.name);
  /* Woher sie kommt, steht nur dann darunter, wenn beide Ordner
     durcheinanderliegen. Im eigenen Reiter wüsste man es ohnehin. */
  if (gruppeJetzt === null && v.gruppe === 'Früher abgelegt') {
    const wo = document.createElement('span');
    wo.className = 'kachel__wo';
    wo.textContent = v.gruppe;
    name.appendChild(wo);
  }

  /* Wofür das Gerüst gut ist, steht als Kurzhinweis am Zeiger — im Gitter
     ist für einen Satz je Kachel kein Platz, aber wer zögert, fährt hin. */
  if (v.zweck) knopf.title = v.name + ' — ' + v.zweck;

  knopf.append(blatt, name);
  knopf.addEventListener('click', () => {
    schliessen();
    if (v.muster) griffe.oeffneMuster(v.muster); else griffe.oeffneNr(v.nr);
  });
  return knopf;
}

/* ------------------------------------------------------------
   Die leere Fläche

   Das erste Bild, und für eine Weile das einzige. Es sagt drei Dinge: was
   eine Vorlage ist, wo sie hingehört, und wie eine hineinkommt — einmal
   von außen (Ordner öffnen) und einmal von innen (dieses Blatt behalten).
   ------------------------------------------------------------ */
function leerZeichnen(wohin) {
  const kasten = document.createElement('div');
  kasten.className = 'leerfeld';

  const blatt = document.createElement('div');
  blatt.className = 'leerfeld__blatt';
  blatt.appendChild(griffe.symbol('leereseite'));

  const titel = document.createElement('h3');
  titel.textContent = 'Hier ist noch nichts.';

  const satz = document.createElement('p');
  satz.append('Eine Vorlage ist ein ganzes Dokument, das du immer wieder '
            + 'brauchst — ein Briefkopf, ein Formular, ein Zettel mit deiner '
            + 'Adresse oben. Leg eine Datei in den Ordner ');
  const ordner = document.createElement('code');
  ordner.textContent = '~/Vorlagen';
  satz.appendChild(ordner);
  satz.append(', dann steht sie hier. Oder schreib etwas im Blatt und behalte '
            + 'es von dort aus.');

  const wege = document.createElement('div');
  wege.className = 'leerfeld__wege';
  for (const [beschriftung, art, tun] of [
    ['Vorlagenordner öffnen', 'knopf knopf--haupt', () => griffe.ordnerOeffnen()],
    ['Dieses Dokument als Vorlage behalten…', 'knopf',
      () => { schliessen(); griffe.behalten(); }],
    ['Leeres Dokument', 'knopf', () => { schliessen(); griffe.leeresDokument(); }],
  ]) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.className = art;
    knopf.textContent = beschriftung;
    knopf.addEventListener('click', tun);
    wege.appendChild(knopf);
  }

  kasten.append(blatt, titel, satz, wege);
  wohin.appendChild(kasten);
}

/* ------------------------------------------------------------
   Alles zeichnen
   ------------------------------------------------------------ */
function zeichnen() {
  reiterZeichnen();
  $('neuseite-suchzeile').hidden = liste.length === 0;

  const feld = $('neuseite-feld');
  feld.textContent = '';

  if (!liste.length) { leerZeichnen(feld); return; }

  let sichtbar = liste.filter((v) => gruppeJetzt === null || v.gruppe === gruppeJetzt);
  if (suchwort) {
    sichtbar = sichtbar.filter((v) => v.name.toLowerCase().includes(suchwort));
  }

  if (!sichtbar.length) {
    const satz = document.createElement('p');
    satz.className = 'nichtsgefunden';
    satz.textContent = 'Keine Vorlage heißt so.';
    feld.appendChild(satz);
    return;
  }

  /* Angeheftetes steht vorn, aber im selben Gitter. Ein eigener Abschnitt
     dafür kostete eine ganze Reihe Höhe und trennte drei Blätter von sechs,
     die zusammengehören. */
  const sortiert = sichtbar.filter((v) => fest.includes(marke(v)))
    .concat(sichtbar.filter((v) => !fest.includes(marke(v))));

  const gitter = document.createElement('div');
  gitter.className = 'kacheln';
  /* Das leere Blatt nur, solange nicht gesucht wird: Wer „Rechnung" tippt,
     meint keine leere Seite. */
  if (!suchwort) gitter.appendChild(kachelLeeresBlatt());
  for (const v of sortiert) gitter.appendChild(kachelVorlage(v));
  feld.appendChild(gitter);

  /* Solange nur die mitgelieferten Gerüste da sind, weiß niemand, dass es
     auch eigene geben kann. Die große leere Ansicht wäre dafür zu viel —
     es ist ja etwas da. Also eine Zeile unter dem Gitter, und nur, wenn
     wirklich keine eigene Vorlage abgelegt ist. */
  if (!suchwort && !liste.some((v) => !v.muster)) {
    const hinweis = document.createElement('p');
    hinweis.className = 'neuseite__hinweis';
    hinweis.append('Das sind die mitgelieferten Gerüste. Deine eigenen Vorlagen '
                 + 'kommen daneben, sobald du eine Datei nach ');
    const ordner = document.createElement('code');
    ordner.textContent = '~/Vorlagen';
    hinweis.appendChild(ordner);
    hinweis.append(' legst — oder dieses Blatt unten als Vorlage behältst.');
    feld.appendChild(hinweis);
  }
}

/* ------------------------------------------------------------
   Auf und zu
   ------------------------------------------------------------ */
function oeffnen(neueListe) {
  /* Die Nummer ist der Platz in der Liste, die der Server gerade gelesen
     hat — über sie wird geöffnet. Sie wird hier festgehalten, weil Suchen
     und Anheften die Reihenfolge auf dem Schirm verändern. */
  liste = (neueListe || []).map((v, nr) => Object.assign({ nr }, v));
  fest = KI.Speicher.lies('vorlagenFest', []);
  if (!Array.isArray(fest)) fest = [];
  suchwort = '';
  $('neuseite-suche').value = '';
  zeichnen();
  $('neuseite').hidden = false;
  offen = true;
  $('neuseite-feld').scrollTop = 0;
  /* Die Schreibmarke gehört ins Suchfeld: Wer zwölf Vorlagen hat, tippt
     schneller drei Buchstaben, als er hinsieht. */
  if (liste.length) $('neuseite-suche').focus();
}

function schliessen() {
  if (!offen) return;
  $('neuseite').hidden = true;
  $('neuseite-feld').textContent = '';
  offen = false;
  griffe.zurueck();
}

/* ------------------------------------------------------------
   Verdrahtung
   ------------------------------------------------------------ */
function verdrahten() {
  $('neuseite-zurueck').addEventListener('click', () => schliessen());

  /* Die beiden Wege in die Sammlung hinein stehen unten und immer da. In
     der leeren Ansicht stehen sie ein zweites Mal — dort sind sie das
     Einzige, was zu tun ist, und gehören in die Mitte statt an den Rand. */
  $('neuseite-ordner').addEventListener('click', () => griffe.ordnerOeffnen());
  $('neuseite-behalten').addEventListener('click', () => {
    schliessen();
    griffe.behalten();
  });

  $('neuseite-suche').addEventListener('input', (e) => {
    suchwort = e.target.value.trim().toLowerCase();
    zeichnen();
  });
  /* Escape im Suchfeld leert erst das Feld und schließt erst dann die
     Seite. Sonst verliert man beim Vertippen die ganze Fläche. */
  $('neuseite-suche').addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && e.target.value) {
      e.stopPropagation();
      e.target.value = '';
      suchwort = '';
      zeichnen();
    }
  });
}

verdrahten();

return { oeffnen, schliessen, verbinde, offen: () => offen, musterListe, musterHtml };
})();
