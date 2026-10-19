/* ==========================================================================
   Drucken: die Vorschau und das Druckfenster

   Diese 1.136 Zeilen lagen in programm.js. Sie gehoeren zusammen und sonst
   zu nichts: Der Umbruch wird selbst gerechnet, darauf setzen zwei Fenster
   auf, und danach geht der Auftrag an den Drucker. Wer daran etwas aendert,
   hat im uebrigen Programm nichts zu suchen — und umgekehrt.

   WAS „umg" IST

   Diese Datei kennt das Programm nicht. Was sie von dort braucht, wird ihr
   gereicht und steht in programm.js an einer Stelle beisammen. Es sind
   wenige Namen, und das ist der Punkt: Man sieht, woran das Drucken haengt.

   „umg" und nicht „w", weil es hier schon ein „w" gibt — die Druckwahl.

   „seite()" gibt zurueck, wie die Seite gerade eingerichtet ist, und wird
   bei jedem Zugriff neu gefragt. Beim Bauen zu fragen waere falsch: Wer im
   Druckfenster das Papierformat umstellt, soll das im selben Augenblick im
   Blatt sehen. „seiteSetzen" ist der Weg zurueck — das Druckfenster ist die
   einzige Stelle, die von hier aus Papier und Ausrichtung aendert.
   ========================================================================== */
'use strict';

function DRUCKEN_BAUEN(B, umg) {

const $ = (id) => document.getElementById(id);
const { Speicher, feld, CM } = umg;
const fenster        = (...a) => umg.fenster(...a);
const melde          = (...a) => umg.melde(...a);
const ohneMarken     = (...a) => umg.ohneMarken(...a);
const papierAnwenden = ()     => umg.papierAnwenden();

/* ============================================================
   Drucken: die Vorschau und das Druckfenster

   Bisher war beides ein Aufruf: window.print(). Der Browser bekam ein
   einziges, sehr langes Blatt und schnitt es in Streifen. Kopfzeile und
   Fußzeile standen deshalb genau einmal da statt auf jeder Seite, die
   Seitenzahl blieb der Platzhalter, der sie im Text ist, und wo der Text
   umbricht, erfuhr man erst auf dem Papier.

   Jetzt rechnet das Programm den Umbruch selbst: Es füllt ein Blatt, bis es
   voll ist, und fängt ein neues an. Der alte Einwand gegen einen eigenen
   Nachbau — dass er irgendwann vom Ausdruck abwiche — ist damit erledigt,
   denn es ist kein Nachbau: Gedruckt werden genau diese Blätter.

   Darauf setzen zwei Fenster auf, wie im Writer:
     • die Druckvorschau — der ganze Stapel, zum Durchblättern;
     • das Druckfenster — links dasselbe Blatt, rechts die Einstellungen.
   Beide rechnen mit derselben Funktion, also zeigen sie dasselbe.

   Was das Programm NICHT kann: den Drucker aussuchen, die Papierschublade
   wählen, beidseitig einstellen. Das gehört dem System, und danach fragt
   sein eigenes Fenster, sobald gedruckt wird. Hier steht deshalb keine
   erfundene Druckerliste — nur das, was wirklich hier entschieden wird.
   ============================================================ */

/* ------------------------------------------------------------
   Was gedruckt wird und wie. Die Vorgaben sind die des Writers.
   ------------------------------------------------------------ */
const DRUCK_VORGABE = {
  bereich: 'alle',          /* alle | auswahl | seiten */
  seiten: '',               /* „1-3, 5" */
  kopien: 1,
  sortieren: true,
  blattseiten: 'alle',      /* alle | ungerade | gerade */
  proBlatt: 1,
  hintergrund: true,
  bilder: true,
  platzhalter: false,
  steuerelemente: true,
  kommentare: 'keine',      /* keine | ende */
  schwarz: false,
  leere: true,
};
let druckWahl = Object.assign({}, DRUCK_VORGABE, Speicher.lies('druck', {}));
/* Was beim Öffnen des Druckfensters markiert war. Der Griff danach muss
   sofort passieren: Sobald der Kasten aufgeht, ist die Markierung weg. */
let druckAuswahl = '';

/* Was das System über seine Drucker sagt. Es wird beim ersten Öffnen des
   Druckfensters geholt und danach gemerkt: Ein Drucker kommt nicht alle
   paar Sekunden dazu, und die Auskunft kostet ein paar Aufrufe von lpstat. */
let druckerListe = [];
let druckerSelbst = false;      /* ob das Programm selbst drucken kann */
let druckerName = Speicher.lies('drucker', '');
let druckerDuplex = Speicher.lies('druckerduplex', 'einseitig');
let druckerGeraet = Speicher.lies('druckergeraet', {});

function druckWahlSichern() {
  Speicher.schreib('druck', druckWahl);
}

/* Was zum einzelnen Auftrag gehört, fängt jedes Mal von vorn an: der
   Bereich, die Zahl der Kopien, die Blattseiten, die Seiten pro Blatt.
   Wer gestern die ungeraden Seiten gedruckt hat, will heute nicht wieder
   nur die ungeraden bekommen — und würde es erst am Stapel merken.

   Was zur Vorliebe gehört, bleibt: ob Bilder mitkommen, ob der Text
   schwarz wird, was mit den Kommentaren geschieht. Das entscheidet man
   einmal und nicht bei jedem Ausdruck neu. */
function druckAuftragZuruecksetzen() {
  for (const feldname of ['bereich', 'seiten', 'kopien', 'sortieren', 'blattseiten', 'proBlatt']) {
    druckWahl[feldname] = DRUCK_VORGABE[feldname];
  }
}

/* ------------------------------------------------------------
   Das Papier
   ------------------------------------------------------------ */
function vorschauMasse() {
  const masse = umg.papiere()[umg.seite().papier] || umg.papiere().a4;
  return umg.seite().quer ? { breite: masse.hoehe, hoehe: masse.breite }
              : { breite: masse.breite, hoehe: masse.hoehe };
}

/* ------------------------------------------------------------
   Die Vorlage: der Text, so wie er gedruckt werden soll

   Hier fällt weg, was laut Einstellung nicht mit aufs Papier soll. Es
   geschieht an einer Kopie — im Dokument selbst wird nichts angefasst.
   ------------------------------------------------------------ */
function druckQuelle(wahl) {
  const quelle = document.createElement('div');
  const roh = (wahl.bereich === 'auswahl' && druckAuswahl) ? druckAuswahl : feld.innerHTML;
  quelle.innerHTML = ohneMarken(roh);

  /* Eine Markierung fängt selten am Absatzanfang an. Was dabei als nackter
     Text herausfällt, bekommt hier einen Absatz — sonst hätte die Seite ein
     Kind, das kein Element ist, und der Umbruch zählt nur Elemente. */
  for (const knoten of Array.from(quelle.childNodes)) {
    if (knoten.nodeType !== Node.ELEMENT_NODE) {
      if (!knoten.textContent.trim()) { knoten.remove(); continue; }
      const absatz = document.createElement('p');
      quelle.replaceChild(absatz, knoten);
      absatz.appendChild(knoten);
    }
  }

  if (!wahl.bilder) {
    for (const bild of quelle.querySelectorAll('img,svg,.diagramm,.zeichnung')) bild.remove();
  }
  if (!wahl.platzhalter) {
    for (const stelle of quelle.querySelectorAll('.seriendruckfeld')) stelle.remove();
  }
  if (!wahl.steuerelemente) {
    for (const stueck of quelle.querySelectorAll('.formfeld,.formknopf,.formkasten')) stueck.remove();
  }

  /* Die Kommentarmarken stehen mitten im Satz und sollen dort nie
     mitgedruckt werden. Wer sie braucht, bekommt sie hinten als Liste —
     durchnummeriert, damit man die Stelle wiederfindet. */
  const marken = Array.from(quelle.querySelectorAll('.kommentar'));
  for (const marke of marken) marke.remove();
  if (wahl.kommentare === 'ende' && marken.length) {
    const ueber = document.createElement('h3');
    ueber.textContent = 'Kommentare';
    ueber.style.pageBreakBefore = 'always';
    quelle.appendChild(ueber);
    marken.forEach((marke, i) => {
      const zeile = document.createElement('p');
      zeile.textContent = (i + 1) + '. ' + (marke.getAttribute('title') || '');
      quelle.appendChild(zeile);
    });
  }
  return quelle;
}

/* ------------------------------------------------------------
   Ein leeres Blatt in den Maßen der Seite
   ------------------------------------------------------------ */
function vorschauBlatt(nummer, wahl) {
  const { breite, hoehe } = vorschauMasse();

  const fach = document.createElement('div');
  fach.className = 'vorschau__fach';

  const seite = document.createElement('div');
  seite.className = 'vorschau__seite';
  seite.style.width = breite + 'mm';
  seite.style.height = hoehe + 'mm';
  seite.style.paddingTop = umg.seite().seitenrand.oben + 'mm';
  seite.style.paddingBottom = umg.seite().seitenrand.unten + 'mm';
  seite.style.paddingLeft = umg.seite().seitenrand.links + 'mm';
  seite.style.paddingRight = umg.seite().seitenrand.rechts + 'mm';
  if (wahl.hintergrund && umg.seite().seitenfarbe) seite.style.background = umg.seite().seitenfarbe;

  if (wahl.hintergrund && umg.seite().wasserzeichen) {
    const marke = document.createElement('div');
    marke.className = 'wasserzeichen';
    marke.setAttribute('aria-hidden', 'true');
    marke.textContent = umg.seite().wasserzeichen;
    seite.appendChild(marke);
  }

  if (!$('kopfzeile').hidden) seite.appendChild(vorschauZeile('kopfzeile', nummer));

  const koerper = document.createElement('div');
  koerper.className = 'dokument vorschau__koerper';
  koerper.lang = 'de';
  if (umg.seite().zeilennummern) koerper.classList.add('dokument--zeilennummern');
  if (wahl.schwarz) koerper.classList.add('vorschau__koerper--schwarz');
  if (umg.seite().spalten > 1) { koerper.style.columnCount = umg.seite().spalten; koerper.style.columnGap = '8mm'; }
  if (umg.seite().trennung) koerper.style.hyphens = 'auto';
  seite.appendChild(koerper);

  if (!$('fusszeile').hidden) seite.appendChild(vorschauZeile('fusszeile', nummer));

  fach.appendChild(seite);

  const zahl = document.createElement('span');
  zahl.className = 'vorschau__nummer';
  zahl.setAttribute('aria-hidden', 'true');
  zahl.textContent = String(nummer);
  fach.appendChild(zahl);
  return fach;
}

/* Kopf- und Fußzeile gehören zur Seite, nicht zum Text — also stehen sie
   auf jedem Blatt, und der Platzhalter „Seite" wird hier zu der Zahl, die
   dieses Blatt trägt. Vorher blieb er ein Wort, weil niemand wusste, die
   wievielte Seite gerade gedruckt wird. */
function vorschauZeile(welche, nummer) {
  const zeile = document.createElement('div');
  zeile.className = welche + ' vorschau__zeile';
  zeile.innerHTML = ohneMarken($(welche).innerHTML);
  for (const stelle of zeile.querySelectorAll('.seitenzahl')) stelle.textContent = String(nummer);
  return zeile;
}

/* ------------------------------------------------------------
   Der Umbruch

   Gefüllt wird, bis es nicht mehr passt: Jeder Absatz kommt auf das Blatt
   und wird gemessen. Passt er nicht mehr, wandert er auf das nächste — und
   wenn er allein schon zu hoch ist, wird er geteilt.

   Gemessen wird am wirklichen Blatt, nicht an einer Rechnung nebenher.
   Zusammenfallende Ränder, ein Bild, eine Tabelle, eine größere Schrift:
   Das alles müsste man sonst einzeln nachrechnen und läge doch daneben.
   ------------------------------------------------------------ */
function vorschauUmbrechen(ziel, wahl) {
  ziel.style.zoom = '';                    /* beim Messen nichts verzerren */
  ziel.textContent = '';

  const quelle = druckQuelle(wahl);
  const warteschlange = Array.from(quelle.children);
  /* Eine Notbremse. Sollte eine Teilung wider Erwarten nicht vorankommen,
     ist eine unvollständige Vorschau immer noch besser als ein Fenster,
     das steht. */
  const grenze = warteschlange.length * 4 + 400;

  let koerper = null;
  const neuesBlatt = () => {
    const fach = vorschauBlatt(ziel.children.length + 1, wahl);
    ziel.appendChild(fach);
    koerper = fach.querySelector('.vorschau__koerper');
  };
  neuesBlatt();

  let runden = 0;
  while (warteschlange.length && ++runden < grenze) {
    const block = warteschlange.shift();

    /* Der Abschnittsstrich ist eine Marke, kein Inhalt: Er bricht um und
       wird selbst nicht gedruckt. */
    if (block.tagName === 'HR' && block.dataset.abschnitt) {
      if (koerper.childElementCount) neuesBlatt();
      continue;
    }
    if (koerper.childElementCount && vorschauUmbruchDavor(block)) neuesBlatt();

    koerper.appendChild(block);
    if (vorschauPasst(koerper)) continue;

    if (koerper.childElementCount === 1) {
      /* Allein auf dem Blatt und trotzdem zu hoch. Ein durchlaufender
         Absatz wird geteilt; bei einem Bild oder einer Tabelle geht das
         nicht — die bleibt stehen, und was übersteht, ist ab. Unschön,
         aber ehrlich: Genauso käme es aus dem Drucker. */
      const rest = vorschauTeilen(koerper, block);
      if (!rest) continue;
      warteschlange.unshift(rest);
      neuesBlatt();
      continue;
    }

    koerper.removeChild(block);
    neuesBlatt();
    warteschlange.unshift(block);
  }

  /* Ein leeres letztes Blatt entsteht, wenn der letzte Absatz gerade eben
     umgebrochen ist. Es gehört nicht dazu. */
  while (ziel.children.length > 1 && vorschauLeer(ziel.lastElementChild)) {
    ziel.lastElementChild.remove();
  }
  return ziel.children.length;
}

function vorschauPasst(koerper) {
  /* Ein Bildpunkt Luft: Beim Rechnen mit Millimetern bleibt sonst ein Rest
     übrig, der keiner ist. */
  return koerper.scrollHeight <= koerper.clientHeight + 1;
}

function vorschauLeer(fach) {
  const koerper = fach.querySelector('.vorschau__koerper');
  return !koerper || !koerper.textContent.trim();
}

function vorschauUmbruchDavor(block) {
  const wie = block.style;
  return wie.pageBreakBefore === 'always' || wie.breakBefore === 'page';
}

/* ---- Einen zu hohen Absatz teilen ----
   Wie viel davon passt, weiß nur der Zeichensatz — also wird gesucht statt
   gerechnet: die Hälfte probieren, dann die Hälfte davon, und so weiter.
   Bei tausend Zeichen sind das zehn Versuche. */
function vorschauTeilen(koerper, block) {
  const urbild = block.cloneNode(true);
  const text = urbild.textContent;
  /* Was kein durchlaufender Text ist, lässt sich nicht in der Mitte
     auseinanderschneiden: eine Tabelle, ein Bild, eine Liste, eine Formel. */
  if (text.length < 8 || block.querySelector('table,img,svg,math,hr,li')) return null;

  let passend = 0, tief = 1, hoch = text.length;
  while (tief <= hoch) {
    const mitte = (tief + hoch) >> 1;
    vorschauAusschnitt(block, urbild, 0, mitte);
    if (vorschauPasst(koerper)) { passend = mitte; tief = mitte + 1; }
    else hoch = mitte - 1;
  }

  /* Nicht mitten im Wort trennen: zurück bis zum letzten Zwischenraum. */
  let schnitt = passend;
  while (schnitt > 0 && !/\s/.test(text.charAt(schnitt))) schnitt--;
  if (schnitt < 2) { vorschauAusschnitt(block, urbild, 0, text.length); return null; }

  vorschauAusschnitt(block, urbild, 0, schnitt);
  const rest = urbild.cloneNode(false);       /* dasselbe Element, nur leer */
  vorschauAusschnitt(rest, urbild, schnitt + 1, text.length);
  return rest;
}

/* Setzt in „ziel" den Teil von „urbild", der die Zeichen von…bis enthält —
   samt allem, was darin ausgezeichnet ist. Zeichen abzuzählen reicht nicht:
   Ein fett gesetztes Wort in der Mitte muss fett bleiben. */
function vorschauAusschnitt(ziel, urbild, von, bis) {
  const stueck = urbild.cloneNode(true);
  const laeufer = document.createTreeWalker(stueck, NodeFilter.SHOW_TEXT);
  const weg = [];
  let gelesen = 0, knoten;
  while ((knoten = laeufer.nextNode())) {
    const anfang = gelesen;
    gelesen += knoten.data.length;
    const a = Math.max(anfang, von), b = Math.min(gelesen, bis);
    if (a >= b) { weg.push(knoten); continue; }
    knoten.data = knoten.data.slice(a - anfang, b - anfang);
  }
  for (const knoten of weg) knoten.remove();
  ziel.innerHTML = stueck.innerHTML;
}

/* ============================================================
   Die Druckvorschau — der ganze Stapel zum Durchblättern
   ============================================================ */

/* Marke, Name, Spalten, Reihen, ob die erste Seite allein steht. */
const VORSCHAU_REIHEN = [
  ['eine', 'Eine Seite',  1, 1, false],
  ['zwei', 'Zwei Seiten', 2, 1, false],
  ['buch', 'Buchansicht', 2, 1, true],
  ['vier', 'Vier Seiten', 2, 2, false],
];

let vorschauReihe = Speicher.lies('vorschaureihe', 'eine');
/* 0 heißt „einpassen": so groß, dass die gewählte Zahl Blätter ins Fenster
   passt. Jede andere Zahl ist eine feste Vergrößerung in Prozent. */
let vorschauStufe = Speicher.lies('vorschaustufe', 0);
let vorschauSeite = 1;
let vorschauOffen = false;
let vorschauBereit = false;

function vorschauArt() {
  return VORSCHAU_REIHEN.find(([marke]) => marke === vorschauReihe) || VORSCHAU_REIHEN[0];
}

function vorschauAufbauen() {
  /* Nur rechnen, wenn die Seite auch gesetzt ist. Ein verstecktes Blatt hat
     keine Höhe, und ohne Höhe passt alles auf eine Seite — herauskäme eine
     Vorschau mit einer einzigen, endlos langen Seite. */
  if ($('vorschau').hidden) return 0;
  const blaetter = $('vorschau-blaetter');
  const art = vorschauArt();
  blaetter.classList.toggle('vorschau__blaetter--buch', art[4]);
  blaetter.style.setProperty('--vorschau-spalten', String(art[2]));
  const anzahl = vorschauUmbrechen(blaetter, druckWahl);
  $('vorschau-von').textContent = '/ ' + anzahl;
  $('vorschau-nummer').max = String(anzahl);
  vorschauZoomAnwenden();
  if (vorschauSeite > anzahl) vorschauSeite = anzahl;
  vorschauStandZeigen();
  return anzahl;
}

function vorschauEinpassung() {
  const art = vorschauArt();
  const flaeche = $('vorschau-flaeche');
  const { breite, hoehe } = vorschauMasse();
  const luft = 20;                       /* der Abstand zwischen den Blättern */
  const platzBreit = flaeche.clientWidth - 44 - (art[2] - 1) * luft;
  const platzHoch = flaeche.clientHeight - 44 - (art[3] - 1) * luft;
  const skala = Math.min(platzBreit / (art[2] * breite * CM / 10),
                         platzHoch / (art[3] * hoehe * CM / 10));
  return Math.max(10, Math.min(400, Math.round(skala * 100)));
}

function vorschauZoomAnwenden() {
  const stufe = vorschauStufe || vorschauEinpassung();
  $('vorschau-blaetter').style.zoom = (stufe / 100).toFixed(3);
  $('vorschau-stufe').textContent = stufe + ' %';
}

function vorschauStufeSetzen(schritt) {
  const jetzt = vorschauStufe || vorschauEinpassung();
  vorschauStufe = Math.max(20, Math.min(400, jetzt + schritt));
  Speicher.schreib('vorschaustufe', vorschauStufe);
  vorschauZoomAnwenden();
}

function vorschauZuSeite(nummer) {
  const blaetter = $('vorschau-blaetter');
  const anzahl = blaetter.children.length;
  if (!anzahl) return;
  vorschauSeite = Math.max(1, Math.min(anzahl, Math.round(nummer) || 1));
  const fach = blaetter.children[vorschauSeite - 1];
  if (fach) fach.scrollIntoView({ block: 'start' });
  vorschauStandZeigen();
}

function vorschauStandZeigen() {
  const blaetter = $('vorschau-blaetter');
  $('vorschau-nummer').value = String(vorschauSeite);
  for (let i = 0; i < blaetter.children.length; i++) {
    const seite = blaetter.children[i].firstElementChild;
    if (seite) seite.classList.toggle('vorschau__seite--hier', i === vorschauSeite - 1);
  }
}

function vorschauBereitMachen() {
  if (vorschauBereit) return;
  vorschauBereit = true;

  const wahl = $('vorschau-reihe');
  for (const [marke, name] of VORSCHAU_REIHEN) {
    const punkt = document.createElement('option');
    punkt.value = marke;
    punkt.textContent = name;
    wahl.appendChild(punkt);
  }
  wahl.value = vorschauReihe;
  wahl.addEventListener('change', () => {
    vorschauReihe = wahl.value;
    Speicher.schreib('vorschaureihe', vorschauReihe);
    vorschauAufbauen();
    vorschauZuSeite(vorschauSeite);
  });

  $('vorschau-erste').addEventListener('click', () => vorschauZuSeite(1));
  $('vorschau-zurueck').addEventListener('click', () => vorschauZuSeite(vorschauSeite - 1));
  $('vorschau-vor').addEventListener('click', () => vorschauZuSeite(vorschauSeite + 1));
  $('vorschau-letzte').addEventListener('click',
    () => vorschauZuSeite($('vorschau-blaetter').children.length));
  $('vorschau-nummer').addEventListener('change',
    (e) => vorschauZuSeite(parseInt(e.target.value, 10)));

  $('vorschau-kleiner').addEventListener('click', () => vorschauStufeSetzen(-10));
  $('vorschau-groesser').addEventListener('click', () => vorschauStufeSetzen(10));
  $('vorschau-einpassen').addEventListener('click', () => {
    vorschauStufe = 0;
    Speicher.schreib('vorschaustufe', 0);
    vorschauZoomAnwenden();
  });

  $('vorschau-drucken').addEventListener('click', () => B.drucken());
  $('vorschau-zu').addEventListener('click', () => vorschauSchliessen());

  /* Beim Rollen wandert die Zahl in der Leiste mit — sonst stünde dort
     „Seite 1", während längst die vierte zu sehen ist. */
  $('vorschau-flaeche').addEventListener('scroll', () => {
    const blaetter = $('vorschau-blaetter');
    const oben = $('vorschau-flaeche').getBoundingClientRect().top;
    let hier = vorschauSeite;
    for (let i = 0; i < blaetter.children.length; i++) {
      if (blaetter.children[i].getBoundingClientRect().bottom > oben + 8) { hier = i + 1; break; }
    }
    if (hier !== vorschauSeite) { vorschauSeite = hier; vorschauStandZeigen(); }
  });

  /* Ändert sich das Fenster, ändert sich auch, was hineinpasst. */
  window.addEventListener('resize', () => { if (vorschauOffen && !vorschauStufe) vorschauZoomAnwenden(); });
}

B.vorschau = () => {
  if (vorschauOffen) { vorschauSchliessen(); return; }
  vorschauBereitMachen();
  const seite = $('vorschau');
  seite.hidden = false;
  seite.classList.remove('vorschau--still');
  vorschauOffen = true;
  vorschauSeite = 1;
  const anzahl = vorschauAufbauen();
  $('vorschau-flaeche').scrollTop = 0;
  melde('Druckvorschau: ' + anzahl + (anzahl === 1 ? ' Seite.' : ' Seiten.'));
};

function vorschauSchliessen() {
  if (!vorschauOffen) return;
  $('vorschau').hidden = true;
  $('vorschau-blaetter').textContent = '';
  vorschauOffen = false;
  feld.focus();
  melde('Vorschau geschlossen.');
}

/* ============================================================
   Das Druckfenster

   Links das Blatt, rechts die Einstellungen, unten die drei Knöpfe — die
   Aufteilung, die jeder kennt, der schon einmal im Writer gedruckt hat.
   ============================================================ */
let druckBereit = false;
let druckSeite = 1;

function druckLesen() {
  const w = druckWahl;
  const gewaehlt = document.querySelector('input[name="druckbereich"]:checked');
  w.bereich = gewaehlt ? gewaehlt.value : 'alle';
  w.seiten = $('druck-seiten').value.trim();
  w.kopien = Math.max(1, Math.min(99, parseInt($('druck-kopien').value, 10) || 1));
  w.sortieren = $('druck-sortieren').checked;
  w.blattseiten = $('druck-blattseiten').value;
  w.proBlatt = parseInt($('druck-problatt').value, 10) || 1;
  w.hintergrund = $('druck-hintergrund').checked;
  w.bilder = $('druck-bilder').checked;
  w.platzhalter = $('druck-platzhalter').checked;
  w.steuerelemente = $('druck-steuer').checked;
  w.kommentare = $('druck-kommentare').value;
  w.schwarz = $('druck-schwarz').checked;
  w.leere = $('druck-leere').checked;
  druckWahlSichern();
}

function druckSchreiben() {
  const w = druckWahl;
  for (const knopf of document.querySelectorAll('input[name="druckbereich"]')) {
    knopf.checked = knopf.value === w.bereich;
  }
  $('druck-seiten').value = w.seiten;
  $('druck-kopien').value = String(w.kopien);
  $('druck-sortieren').checked = w.sortieren;
  $('druck-blattseiten').value = w.blattseiten;
  $('druck-problatt').value = String(w.proBlatt);
  $('druck-hintergrund').checked = w.hintergrund;
  $('druck-bilder').checked = w.bilder;
  $('druck-platzhalter').checked = w.platzhalter;
  $('druck-steuer').checked = w.steuerelemente;
  $('druck-kommentare').value = w.kommentare;
  $('druck-schwarz').checked = w.schwarz;
  $('druck-leere').checked = w.leere;
  $('druck-papier').value = umg.seite().papier;
  $('druck-e-papier').value = umg.seite().papier;
  $('druck-quer').value = umg.seite().quer ? 'quer' : 'hoch';
  $('druck-e-quer').value = umg.seite().quer ? 'quer' : 'hoch';
}

/* ------------------------------------------------------------
   Die Drucker des Systems

   LibreOffice fragt CUPS, den Druckerdienst des Arbeitsplatzes, und
   bekommt von dort den Namen, den Zustand und alles, was ein Drucker kann.
   Hier geschieht dasselbe — start.py fragt für uns, weil eine Seite im
   Browser nicht an den Druckerdienst herankommt.

   Was zurückkommt, wird nicht ausgeschmückt: Meldet ein Drucker keine
   Duplexeinheit, bleibt der Schalter dafür grau. Ein Schalter, der nichts
   bewirkt, ist schlimmer als keiner.
   ------------------------------------------------------------ */
async function druckerHolen() {
  try {
    const antwort = await fetch('drucker');
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    const daten = await antwort.json();
    druckerListe = daten.drucker || [];
    druckerSelbst = !!daten.selbst;
    if (!druckerJetzt() && daten.standard) druckerName = daten.standard;
    if (!druckerJetzt() && druckerListe.length) druckerName = druckerListe[0].name;
  } catch (e) {
    /* Im Browser statt im eigenen Fenster gibt es diesen Weg nicht. Dann
       druckt der Browser, und sein Fenster fragt nach dem Drucker. */
    druckerListe = [];
    druckerSelbst = false;
  }
  druckerZeigen();
}

function druckerJetzt() {
  return druckerListe.find((d) => d.name === druckerName) || null;
}

/* Die Optionen des Druckers ohne „Duplex" — das steht als eigene Zeile
   darüber, weil man es öfter braucht als den Papierschacht. */
function druckerGeraeteteile(drucker) {
  return (drucker ? drucker.optionen || [] : []).filter((o) => o.schluessel !== 'Duplex');
}

function druckerZeigen() {
  const wahl = $('druck-name');
  wahl.textContent = '';
  if (!druckerListe.length) {
    const punkt = document.createElement('option');
    punkt.value = '';
    punkt.textContent = druckerSelbst ? 'Kein Drucker eingerichtet' : 'Über das Fenster des Systems';
    wahl.appendChild(punkt);
    wahl.disabled = true;
  } else {
    wahl.disabled = false;
    for (const drucker of druckerListe) {
      const punkt = document.createElement('option');
      punkt.value = drucker.name;
      punkt.textContent = drucker.name + (drucker.standard ? ' (Standard)' : '');
      wahl.appendChild(punkt);
    }
    wahl.value = druckerName;
  }

  const jetzt = druckerJetzt();
  const stand = !druckerListe.length
    ? (druckerSelbst ? 'Kein Drucker eingerichtet — es wird das Fenster des Systems geöffnet.'
                     : 'Der Browser druckt — sein eigenes Fenster fragt nach dem Drucker.')
    : (jetzt && jetzt.bereit ? 'Bereit' : 'Nicht bereit')
      + (jetzt && jetzt.standard ? ' · Standarddrucker' : '');
  $('druck-status').textContent = stand;

  $('druck-e-name').textContent = jetzt ? jetzt.name : '—';
  $('druck-e-status').textContent = stand;
  $('druck-e-typ').textContent = (jetzt && jetzt.typ) || '—';
  $('druck-e-ort').textContent = (jetzt && jetzt.ort) || '—';
  $('druck-e-kommentar').textContent = (jetzt && jetzt.kommentar) || '—';

  /* Beidseitig nur, wenn der Drucker es meldet. */
  const duplex = (jetzt ? jetzt.optionen || [] : []).find((o) => o.schluessel === 'Duplex');
  $('druck-duplex').disabled = !duplex;
  $('druck-duplex').value = duplex ? druckerDuplex : 'einseitig';

  druckerGeraetBauen(jetzt);
}

/* Papierschacht, Farbe, Auflösung — was davon da ist, sagt der Drucker. */
function druckerGeraetBauen(drucker) {
  const kasten = $('druck-geraet');
  kasten.textContent = '';
  const teile = druckerGeraeteteile(drucker);
  if (!teile.length) {
    const zeile = document.createElement('div');
    zeile.className = 'druckzeile';
    const wert = document.createElement('span');
    wert.className = 'druckzeile__wert';
    wert.textContent = drucker ? 'Dieser Drucker meldet keine weiteren Einstellungen.'
                               : 'Erst einen Drucker wählen.';
    zeile.appendChild(wert);
    kasten.appendChild(zeile);
    return;
  }

  for (const teil of teile) {
    const zeile = document.createElement('label');
    zeile.className = 'druckzeile';
    const name = document.createElement('span');
    name.className = 'druckzeile__wort druckzeile__wort--fest';
    name.textContent = teil.name;
    const wahl = document.createElement('select');
    wahl.className = 'wz-wahl';
    for (const wert of teil.werte) {
      const punkt = document.createElement('option');
      punkt.value = wert;
      punkt.textContent = wert;
      wahl.appendChild(punkt);
    }
    wahl.value = druckerGeraet[teil.schluessel] || teil.jetzt || teil.werte[0];
    wahl.addEventListener('change', () => {
      druckerGeraet[teil.schluessel] = wahl.value;
      Speicher.schreib('druckergeraet', druckerGeraet);
    });
    zeile.appendChild(name);
    zeile.appendChild(wahl);
    kasten.appendChild(zeile);
  }
}

/* Zu einem der drei Reiter springen — von außen und von „Eigenschaften…". */
function druckReiterZeigen(marke) {
  for (const knopf of document.querySelectorAll('.druckreiter__knopf')) {
    const gemeint = knopf.dataset.blatt === marke;
    knopf.classList.toggle('druckreiter__knopf--an', gemeint);
    knopf.setAttribute('aria-selected', String(gemeint));
  }
  for (const blatt of document.querySelectorAll('.druckfenster__blatt')) {
    blatt.hidden = blatt.dataset.blatt !== marke;
  }
}

/* ---- Der Blick nach links ----
   Ein Blatt, so groß wie es der Platz zulässt. Es wird nicht neu gerechnet,
   sondern aus dem Stapel geholt und verkleinert dargestellt. */
function druckBlickZeigen() {
  const buehne = $('druck-buehne');
  const stapel = $('druck-stapel');
  const anzahl = stapel.children.length;
  buehne.textContent = '';
  if (!$('druck-vorschau-an').checked || !anzahl) {
    $('druck-von').textContent = '/ ' + anzahl;
    return;
  }
  druckSeite = Math.max(1, Math.min(anzahl, druckSeite));

  const { breite, hoehe } = vorschauMasse();
  const abbild = stapel.children[druckSeite - 1].firstElementChild.cloneNode(true);
  abbild.classList.remove('vorschau__seite--hier');

  const platzB = buehne.clientWidth || 280;
  const platzH = buehne.clientHeight || 380;
  const skala = Math.min(platzB / (breite * CM / 10), platzH / (hoehe * CM / 10));
  abbild.style.transform = 'scale(' + skala.toFixed(4) + ')';
  abbild.style.transformOrigin = 'top left';
  abbild.style.position = 'absolute';
  abbild.style.left = Math.max(0, (platzB - breite * CM / 10 * skala) / 2) + 'px';
  abbild.style.top = '0';
  buehne.appendChild(abbild);

  $('druck-mass').textContent = breite + ' mm (' + (umg.papiere()[umg.seite().papier] || umg.papiere().a4).name.split(' ')[0] + ')';
  $('druck-hoehe').textContent = hoehe + ' mm';
  $('druck-nummer').value = String(druckSeite);
  $('druck-von').textContent = '/ ' + anzahl;
}

function druckStapelBauen() {
  druckLesen();
  const anzahl = vorschauUmbrechen($('druck-stapel'), druckWahl);
  $('druck-nummer').max = String(anzahl);
  druckBlickZeigen();
  return anzahl;
}

function druckBereitMachen() {
  if (druckBereit) return;
  druckBereit = true;

  /* Dieselbe Liste an zwei Stellen: unter „Seitenlayout" und bei den
     Eigenschaften des Druckers. So hält es der Writer auch — beide Wege
     führen zu derselben Einstellung, und sie zeigen immer dasselbe an. */
  for (const feldname of ['druck-papier', 'druck-e-papier']) {
    for (const marke of Object.keys(umg.papiere())) {
      const punkt = document.createElement('option');
      punkt.value = marke;
      punkt.textContent = umg.papiere()[marke].name;
      $(feldname).appendChild(punkt);
    }
  }

  /* Die Reiter. Der zweite heißt im Writer nach dem Programm, weil dort
     steht, was nur dieses Programm kennt — hier ist es genauso. */
  for (const knopf of document.querySelectorAll('.druckreiter__knopf')) {
    knopf.addEventListener('click', () => druckReiterZeigen(knopf.dataset.blatt));
  }

  /* Jede Änderung wird sofort sichtbar: Wer „Bilder" abschaltet, sieht
     links, dass sie weg sind — und nicht erst auf dem Papier. */
  const neuRechnen = ['druck-hintergrund', 'druck-bilder', 'druck-platzhalter',
                      'druck-steuer', 'druck-kommentare', 'druck-schwarz', 'druck-leere'];
  for (const name of neuRechnen) {
    $(name).addEventListener('change', () => { druckStapelBauen(); });
  }
  for (const knopf of document.querySelectorAll('input[name="druckbereich"]')) {
    knopf.addEventListener('change', () => { druckStapelBauen(); });
  }
  $('druck-seiten').addEventListener('input', () => {
    /* Wer eine Seitenzahl eintippt, meint auch „Seiten:" — den Knopf
       daneben noch einmal anzuklicken ist eine Hürde ohne Grund. */
    $('druck-bereich-seiten').checked = true;
    druckLesen();
  });
  $('druck-kopien').addEventListener('change', druckLesen);
  $('druck-sortieren').addEventListener('change', druckLesen);
  $('druck-blattseiten').addEventListener('change', druckLesen);
  $('druck-problatt').addEventListener('change', druckLesen);

  for (const feldname of ['druck-papier', 'druck-e-papier']) {
    $(feldname).addEventListener('change', () => {
      umg.seiteSetzen({ papier: $(feldname).value });
      papierAnwenden();
      druckSchreiben();
      druckStapelBauen();
    });
  }
  for (const feldname of ['druck-quer', 'druck-e-quer']) {
    $(feldname).addEventListener('change', () => {
      umg.seiteSetzen({ quer: $(feldname).value === 'quer' });
      papierAnwenden();
      druckSchreiben();
      druckStapelBauen();
    });
  }

  /* Der Drucker und was er kann. */
  $('druck-name').addEventListener('change', () => {
    druckerName = $('druck-name').value;
    Speicher.schreib('drucker', druckerName);
    druckerZeigen();
  });
  $('druck-eigenschaften').addEventListener('click', () => druckReiterZeigen('drucker'));
  $('druck-duplex').addEventListener('change', () => {
    druckerDuplex = $('druck-duplex').value;
    Speicher.schreib('druckerduplex', druckerDuplex);
  });

  $('druck-vorschau-an').addEventListener('change', druckBlickZeigen);
  $('druck-erste').addEventListener('click', () => { druckSeite = 1; druckBlickZeigen(); });
  $('druck-zurueck').addEventListener('click', () => { druckSeite--; druckBlickZeigen(); });
  $('druck-vor').addEventListener('click', () => { druckSeite++; druckBlickZeigen(); });
  $('druck-letzte').addEventListener('click',
    () => { druckSeite = $('druck-stapel').children.length; druckBlickZeigen(); });
  $('druck-nummer').addEventListener('change', (e) => {
    druckSeite = parseInt(e.target.value, 10) || 1;
    druckBlickZeigen();
  });

  $('druck-ab').addEventListener('click', druckFensterSchliessen);
  /* Der dunkle Grund ringsum ist auch ein Ausgang — so kennt man es
     von jedem Kasten, der sich über die Arbeit legt. */
  $('druckfenster').addEventListener('mousedown', (e) => {
    if (e.target === $('druckfenster')) druckFensterSchliessen();
  });
  /* Alles, was erklärt werden muss, steht hier — nicht als kleingedruckte
     Zeile unter jedem Schalter. Im Fenster selbst bleibt nur das Wort und
     der Schalter dazu, so wie im Writer. */
  $('druck-hilfe').addEventListener('click', () => {
    fenster('Drucken', [
      { art: 'satz', text:
        'Links steht das Blatt, wie es aus dem Drucker kommt: mit Kopfzeile,\n'
      + 'Fußzeile und der Seitenzahl auf jeder einzelnen Seite.\n\n'

      + 'Den Drucker selbst wählst du nicht hier. Das Fenster des Systems\n'
      + 'fragt danach, sobald du auf „Drucken“ drückst — dort stehen auch\n'
      + 'die Papierschublade und der beidseitige Druck.\n\n'

      + 'Seiten: Einzelne Zahlen und Bereiche, mit Komma getrennt. „1-3, 5“\n'
      + 'druckt die ersten drei Seiten und die fünfte.\n\n'

      + 'Sortieren: Bei drei Kopien kommt erst das ganze Schreiben, dann\n'
      + 'noch einmal das ganze. Ohne Sortieren kommt jede Seite dreimal\n'
      + 'hintereinander.\n\n'

      + 'Blattseiten: Erst die ungeraden drucken, den Stapel umdrehen, dann\n'
      + 'die geraden. So druckst du beidseitig auf einem Drucker, der es\n'
      + 'selbst nicht kann.\n\n'

      + 'Papiergröße und Ausrichtung gehören zum Dokument: Was du hier\n'
      + 'wählst, gilt auch auf dem Bildschirm weiter.\n\n'

      + 'Seitenhintergrund: die Seitenfarbe und das Wasserzeichen. Beides\n'
      + 'kostet Farbe — für ein Schreiben ans Amt lieber aus.\n\n'

      + 'Textplatzhalter: die Seriendruckfelder wie {{Name}}. Aus heißt,\n'
      + 'die Stelle bleibt leer.\n\n'

      + 'Leere Seiten: Eine entsteht, wo ein Seitenumbruch steht und danach\n'
      + 'nichts mehr kommt. Beim beidseitigen Druck ist sie manchmal\n'
      + 'gewollt.' },
    ], null, 'Verstanden');
  });
  $('druck-los').addEventListener('click', () => {
    druckLesen();
    druckFensterSchliessen();
    druckAusfuehren();
  });
}

B.drucken = () => {
  druckBereitMachen();

  /* Die Markierung jetzt greifen: Sobald der Kasten aufgeht, ist sie fort. */
  const auswahl = window.getSelection();
  druckAuswahl = '';
  if (auswahl.rangeCount && !auswahl.isCollapsed
      && feld.contains(auswahl.getRangeAt(0).commonAncestorContainer)) {
    const hilfe = document.createElement('div');
    hilfe.appendChild(auswahl.getRangeAt(0).cloneContents());
    druckAuswahl = hilfe.innerHTML;
  }
  druckAuftragZuruecksetzen();
  $('druck-bereich-auswahl').disabled = !druckAuswahl;
  /* Ist etwas markiert, ist das fast immer das Gemeinte — so hält es der
     Writer auch. */
  if (druckAuswahl) druckWahl.bereich = 'auswahl';

  $('druckfenster').hidden = false;
  druckReiterZeigen('standard');
  druckSchreiben();
  druckSeite = 1;
  druckStapelBauen();
  /* Die Druckerliste wird nebenher geholt: Sie kommt aus ein paar Aufrufen
     an den Druckerdienst, und darauf soll das Fenster nicht warten. */
  druckerHolen();
};

/* „Druckereinstellungen…" führt geradewegs zu den Eigenschaften — ohne den
   Umweg über das Blättern und den Knopf „Eigenschaften…". */
B.druckerEinrichten = () => {
  B.drucken();
  druckReiterZeigen('drucker');
};

function druckFensterSchliessen() {
  $('druckfenster').hidden = true;
  $('druck-stapel').textContent = '';
  $('druck-buehne').textContent = '';
}

/* ------------------------------------------------------------
   Welche Seiten wirklich gedruckt werden

   „1-3, 5" wird zu einer Liste von Nummern. Was außerhalb liegt oder
   keine Zahl ist, fällt still weg — ein Tippfehler soll den Druck nicht
   abbrechen, sondern nur nicht mitzählen.
   ------------------------------------------------------------ */
function druckBereichLesen(text, anzahl) {
  const dabei = [];
  for (const stueck of text.split(/[,;]/)) {
    const teile = stueck.trim().match(/^(\d+)\s*(?:[-–]\s*(\d+))?$/);
    if (!teile) continue;
    const von = parseInt(teile[1], 10);
    const bis = teile[2] ? parseInt(teile[2], 10) : von;
    for (let i = Math.min(von, bis); i <= Math.max(von, bis); i++) {
      if (i >= 1 && i <= anzahl && !dabei.includes(i)) dabei.push(i);
    }
  }
  return dabei;
}

function druckReihenfolge(anzahl, wahl) {
  let nummern = [];
  for (let i = 1; i <= anzahl; i++) nummern.push(i);

  if (wahl.bereich === 'seiten' && wahl.seiten) {
    const gewaehlt = druckBereichLesen(wahl.seiten, anzahl);
    if (gewaehlt.length) nummern = gewaehlt;
  }
  if (wahl.blattseiten === 'ungerade') nummern = nummern.filter((n) => n % 2 === 1);
  if (wahl.blattseiten === 'gerade') nummern = nummern.filter((n) => n % 2 === 0);

  const kopien = Math.max(1, wahl.kopien);
  if (kopien === 1) return nummern;

  /* Sortiert heißt: erst das ganze Schreiben, dann noch einmal das ganze.
     Unsortiert heißt: jede Seite so oft hintereinander, wie Kopien
     gewünscht sind — so, wie ein Stapelleger es braucht. */
  const folge = [];
  if (wahl.sortieren) {
    for (let k = 0; k < kopien; k++) folge.push(...nummern);
  } else {
    for (const n of nummern) for (let k = 0; k < kopien; k++) folge.push(n);
  }
  return folge;
}

/* ------------------------------------------------------------
   Drucken

   Der Stapel wird gebaut, die gewünschten Seiten werden herausgeholt und
   in der gewünschten Reihenfolge in einen eigenen Kasten gelegt. Nur
   dieser Kasten ist beim Drucken sichtbar — der Browser bekommt also
   genau die Blätter, die die Vorschau zeigt.
   ------------------------------------------------------------ */
/* Was nach dem Drucken wieder wegzuräumen ist. Es steht hier draußen, weil
   nicht jeder Browser „afterprint" meldet: Ohne diesen Griff bliebe ein
   unaufgeräumter Druck stehen und sperrte den nächsten. */
let druckAufraeumen = null;

function druckAusfuehren() {
  /* Ein zweiter Druck räumt den ersten ab, statt sich abweisen zu lassen.
     Wer zweimal hintereinander druckt, soll nicht auf eine Uhr warten, von
     der er nichts weiß. */
  if (druckAufraeumen) druckAufraeumen();
  const seite = $('vorschau');
  const warZu = !vorschauOffen;

  /* Messen lässt sich nur, was der Browser auch setzt. Ist die Vorschau
     zu, wird sie dafür kurz gebaut — unsichtbar, aber vorhanden. */
  vorschauBereitMachen();
  if (warZu) {
    seite.hidden = false;
    seite.classList.add('vorschau--still');
  }
  const anzahl = vorschauUmbrechen($('vorschau-blaetter'), druckWahl);
  const folge = druckReihenfolge(anzahl, druckWahl);

  if (!folge.length) {
    if (warZu) { seite.hidden = true; seite.classList.remove('vorschau--still'); }
    melde('Dieser Seitenbereich liegt außerhalb des Dokuments — nichts zu drucken.');
    return;
  }

  const bogen = $('druckbogen');
  bogen.textContent = '';
  druckBogenFuellen(bogen, $('vorschau-blaetter'), folge, druckWahl);

  document.body.classList.add('druckt');

  let fertig = false;
  const aufraeumen = () => {
    if (fertig) return;
    fertig = true;
    druckAufraeumen = null;
    document.body.classList.remove('druckt');
    bogen.textContent = '';
    window.removeEventListener('afterprint', aufraeumen);
    if (warZu) {
      seite.hidden = true;
      seite.classList.remove('vorschau--still');
      $('vorschau-blaetter').textContent = '';
    } else {
      vorschauZoomAnwenden();
      vorschauStandZeigen();
    }
  };
  window.addEventListener('afterprint', aufraeumen);
  druckAufraeumen = aufraeumen;

  druckAbschicken(bogen.children.length, aufraeumen);
}

/* ------------------------------------------------------------
   Der Weg zum Drucker

   Zwei Wege, und der erste ist der gute: start.py hängt den Auftrag an
   dieselbe Ansicht, die gerade die Blätter zeigt, und gibt ihn mit den
   Einstellungen aus diesem Fenster an den Druckerdienst weiter. Dann
   kommt kein zweites Fenster mehr, und der Drucker, das Beidseitige und
   der Papierschacht sind die, die hier eingestellt wurden.

   Geht das nicht — im Browser statt im eigenen Fenster, oder es ist gar
   kein Drucker eingerichtet —, dann öffnet das Fenster des Systems. Der
   Ausdruck ist derselbe; nur gefragt wird woanders.
   ------------------------------------------------------------ */
async function druckAbschicken(blaetter, aufraeumen) {
  const wieviel = blaetter + (blaetter === 1 ? ' Blatt' : ' Blätter');

  if (druckerSelbst && druckerName) {
    melde(wieviel + ' an ' + druckerName + ' …');
    try {
      const antwort = await fetch('drucken', {
        method: 'POST',
        body: JSON.stringify({
          drucker: druckerName,
          /* Die Kopien liegen schon als Blätter im Bogen — der Drucker
             darf sie nicht ein zweites Mal vervielfachen. */
          kopien: 1,
          duplex: $('druck-duplex').disabled ? 'einseitig' : druckerDuplex,
          optionen: druckerGeraet,
          breite: druckBogenMass.breite,
          hoehe: druckBogenMass.hoehe,
        }),
      });
      if (!antwort.ok) {
        let grund = 'Fehler ' + antwort.status;
        try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
        throw new Error(grund);
      }
      melde(wieviel + ' an ' + druckerName + ' gegeben.');
      aufraeumen();
      return;
    } catch (grund) {
      melde('Der Drucker ging nicht: ' + grund.message + ' — es kommt das Fenster des Systems.');
    }
  } else {
    melde(wieviel + ' — das Fenster des Systems fragt nach dem Drucker.');
  }

  window.print();
  /* Nicht jeder Browser meldet „afterprint". Nach dem Druckfenster des
     Systems wird deshalb so oder so aufgeräumt. */
  setTimeout(aufraeumen, 15000);
}

/* Seiten pro Blatt: Bei „1" ist ein Blatt eine Seite. Bei „2" oder „4"
   werden mehrere Seiten verkleinert auf ein Blatt gestellt — wie im
   Writer unter „Seiten pro Blatt". */
let druckBogenMass = { breite: 210, hoehe: 297 };

function druckBogenFuellen(bogen, stapel, folge, wahl) {
  const { breite, hoehe } = vorschauMasse();
  const proBlatt = [1, 2, 4].includes(wahl.proBlatt) ? wahl.proBlatt : 1;

  const holen = (nummer) => stapel.children[nummer - 1].firstElementChild.cloneNode(true);

  if (proBlatt === 1) {
    for (const nummer of folge) {
      const seite = holen(nummer);
      seite.classList.remove('vorschau__seite--hier');
      bogen.appendChild(seite);
    }
    druckPapierregel(breite, hoehe);
    druckBogenMass = { breite, hoehe };
    return;
  }

  /* Zwei Seiten liegen nebeneinander auf einem quergedrehten Blatt, vier
     stehen zu zweit übereinander. So macht es der Writer, und so faltet
     man es hinterher. */
  const spalten = proBlatt === 2 ? 2 : 2;
  const reihen = proBlatt === 2 ? 1 : 2;
  const blattBreite = proBlatt === 2 ? hoehe : breite;
  const blattHoehe = proBlatt === 2 ? breite : hoehe;
  const luft = 4;                                   /* Millimeter Rand */
  const fachBreite = (blattBreite - luft * (spalten + 1)) / spalten;
  const fachHoehe = (blattHoehe - luft * (reihen + 1)) / reihen;
  const skala = Math.min(fachBreite / breite, fachHoehe / hoehe);

  for (let i = 0; i < folge.length; i += proBlatt) {
    const blatt = document.createElement('div');
    blatt.className = 'druckbogen__blatt';
    blatt.style.width = blattBreite + 'mm';
    blatt.style.height = blattHoehe + 'mm';
    blatt.style.padding = luft + 'mm';
    blatt.style.gap = luft + 'mm';
    blatt.style.gridTemplateColumns = 'repeat(' + spalten + ', 1fr)';

    for (let k = 0; k < proBlatt && i + k < folge.length; k++) {
      const fach = document.createElement('div');
      fach.className = 'druckbogen__fach';
      const seite = holen(folge[i + k]);
      seite.classList.remove('vorschau__seite--hier');
      seite.style.transform = 'scale(' + skala.toFixed(4) + ')';
      seite.style.transformOrigin = 'top left';
      fach.appendChild(seite);
      blatt.appendChild(fach);
    }
    bogen.appendChild(blatt);
  }
  /* Mehrere Seiten auf einem Blatt heißt: Das Blatt liegt quer, wenn zwei
     Hochformatseiten nebeneinanderstehen. Der Drucker muss das wissen. */
  druckPapierregel(blattBreite, blattHoehe);
  druckBogenMass = { breite: blattBreite, hoehe: blattHoehe };
}

function druckPapierregel(breite, hoehe) {
  let regel = document.getElementById('bogenregel');
  if (!regel) {
    regel = document.createElement('style');
    regel.id = 'bogenregel';
    document.head.appendChild(regel);
  }
  regel.textContent = '@media print{@page{size:' + breite + 'mm ' + hoehe + 'mm;margin:0}}';
}

/* Was das uebrige Programm von hier braucht: die Escape-Taste macht das
   oberste offene Fenster zu, und dafuer muss sie wissen, ob eines offen
   ist. „vorschauOffen" geht als Funktion hinaus, nicht als Wert — sonst
   waere es der Stand von damals. */
return { vorschauOffen: () => vorschauOffen, vorschauSchliessen, druckFensterSchliessen };
}
