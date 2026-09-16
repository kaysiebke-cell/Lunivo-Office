/* ============================================================
   Das Programm: Menüs, Werkzeuge, Tafel, Statuszeile.

   Die Menüs stehen weiter unten als Liste. Wer einen Punkt hinzufügen
   will, schreibt eine Zeile — die Leiste baut sich daraus selbst.
   ============================================================ */
'use strict';

(() => {

const $ = (id) => document.getElementById(id);
const feld = Dokument.feld;

/* Der Speicher hängt an eigenen Schlüsseln („sp.", von Schreibprogramm —
   der Name von früher, und er bleibt: Wer ihn jetzt änderte, nähme jedem
   beim ersten Start nach dem Update seinen Text und seine Einstellungen
   weg. Lunivo-Office ist ein eigenes Programm; es fasst nichts an, was
   der App gehört. */
/* Und er weiß seit den Dokumentreitern, zu WEM ein Wert gehört. „inhalt"
   ist nicht mehr ein Text, sondern der Text des Dokuments, das gerade
   vorn liegt — dokumente.js biegt den Namen um. Das ist der ganze
   Kunstgriff hinter den Reitern: Das Programm schreibt weiter, was es
   immer schrieb, nur landet es woanders. Was allen Dokumenten gehört
   (Vergrößerung, Helligkeit, welche Leisten sichtbar sind), geht
   ungebogen durch. */
const Speicher = {
  ort(name) {
    return 'sp.' + (typeof Dokumente !== 'undefined' ? Dokumente.schluessel(name) : name);
  },
  lies(name, ersatz) {
    try { const w = localStorage.getItem(this.ort(name)); return w === null ? ersatz : JSON.parse(w); }
    catch (e) { return ersatz; }
  },
  schreib(name, wert) {
    try { localStorage.setItem(this.ort(name), JSON.stringify(wert)); } catch (e) { /* voll */ }
    Einstellungsdatei.merken();
  },
};

/* Der Speicher ist das Abbild in der Datei schuldig — geschrieben wird
   sie in js/einstellungsdatei.js, gebündelt und nicht bei jedem Zug. */

/* Wer fragt? Der Server merkt sich zwischen dem Dateidialog und dem
   Lesen genau EINEN Weg — welche Datei gewählt wurde. Bei zwei offenen
   Fenstern reicht das nicht: Wählt das eine eine Datei, während das
   andere seine noch nicht abgeholt hat, bekäme es die fremde. Also sagt
   jeder Aufruf, aus welchem Fenster er kommt. */
function amFenster(pfad) {
  return pfad + (pfad.includes('?') ? '&' : '?') + 'f=' + Dokumente.fenster();
}

/* Die Sprachbrücke hält den Fehlerstand: welche Fassung geprüft wurde,
   was weggewinkt ist, und ob eine späte Antwort der KI noch zum Text von
   jetzt gehört. Geprüft wird weiter in pruefung.js. Steht sie einmal
   nicht zur Verfügung, prüft das Programm wie vorher direkt. */
const Bruecke = typeof SprachBruecke !== 'undefined' ? new SprachBruecke() : null;

/* ============================================================
   Abschnitte

   Ein Abschnitt ist der Teil eines Dokuments mit eigenem Seitenaufbau:
   eigene Ränder, eigene Ausrichtung, eigene Kopf- und Fußzeile, eigene
   Seitennummerierung. Ein Deckblatt ohne Zahl, ein Hauptteil mit Zahlen
   ab eins, ein Anhang quer — das sind drei davon.

   Bisher gab es nur einen: Papier, Ränder und Kopfzeile galten für das
   ganze Dokument, und „Abschnittsumbruch" zog bloß eine Linie.

   WIE ES ZUSAMMENGEHT

   Der Text bleibt, wo er ist — im Feld, als HTML. Was dazukommt, ist der
   AUFBAU: Das Dokumentmodell (dokumentmodell.js) führt die Abschnitte
   und je Abschnitt den Seitenaufbau. Im Text stehen nur Trennlinien; wo
   der Zeiger steht, sagt, in welchem Abschnitt man ist.

   Der Bogen zeigt immer den Abschnitt, in dem geschrieben wird — so wie
   im Writer und in Word. Wer den Zeiger über eine Trennlinie bewegt,
   sieht die Ränder wechseln.

   Die Sprachbrücke bekommt der Aufbau NICHT gereicht: Den Text meldet
   das Feld ihr schon selbst, und ein zweiter Melder hieße, dass sie
   abwechselnd den ganzen Text und einen leeren bekäme.
   ============================================================ */
const Aufbau = typeof Dokumentmodell !== 'undefined'
  ? new Dokumentmodell.Document(null) : null;

let abschnittJetztNr = 0;

/* In welchem Abschnitt steht der Zeiger? Gezählt werden die Trennlinien
   davor — die Reihenfolge im Text ist die Reihenfolge der Abschnitte. */
function abschnittNummerAnStelle() {
  if (!Aufbau) return 0;
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return abschnittJetztNr;
  let knoten = auswahl.anchorNode;
  if (knoten && knoten.nodeType === Node.TEXT_NODE) knoten = knoten.parentElement;
  if (!knoten || !feld.contains(knoten)) return abschnittJetztNr;

  const marken = [...feld.querySelectorAll('hr.abschnitt')];
  let zahl = 0;
  for (const marke of marken) {
    /* DOCUMENT_POSITION_PRECEDING: Die Marke steht im Text vor dem Zeiger. */
    if (knoten.compareDocumentPosition(marke) & Node.DOCUMENT_POSITION_PRECEDING) zahl++;
  }
  return Math.min(zahl, Aufbau.getSections().length - 1);
}

/* Den Seitenaufbau eines Abschnitts auf den Bogen legen. */
function abschnittAnwenden(nr) {
  if (!Aufbau) return;
  const abschnitt = Aufbau.getSection(nr);
  if (!abschnitt) return;

  const aufbau = abschnitt.getPageSetup();
  papier = aufbau.pageSize.type.name.toLowerCase();
  quer = aufbau.orientation === Dokumentmodell.Orientation.Landscape;
  seitenrand = {
    oben: aufbau.margins.top, unten: aufbau.margins.bottom,
    links: aufbau.margins.left, rechts: aufbau.margins.right,
  };

  /* Kopf- und Fußzeile des Abschnitts — mit „Wie vorherige" kann das die
     eines früheren sein. */
  const kopf = abschnitt.wirksameKopfzeile();
  const fuss = abschnitt.wirksameFusszeile();
  kopfAn = kopf.enabled && !!abschnitt.header.sichtbar;
  fussAn = fuss.enabled && !!abschnitt.footer.sichtbar;
  $('kopfzeile').innerHTML = kopf.html || '<br>';
  $('fusszeile').innerHTML = fuss.html || '<br>';

  papierAnwenden();
  seiteAnwenden();
  kopfFussAnwenden();
  linealAuffrischen();
}

/* Was am Bogen steht, in den Abschnitt zurückschreiben. Ohne das wäre
   jede Einstellung beim nächsten Wechsel wieder weg. */
function abschnittMerken(nr) {
  if (!Aufbau) return;
  const abschnitt = Aufbau.getSection(nr);
  if (!abschnitt) return;
  const aufbau = abschnitt.getPageSetup();
  const masse = PAPIERE[papier] || PAPIERE.a4;
  aufbau.pageSize.type.name = papier.toUpperCase();
  aufbau.pageSize.width = masse.breite;
  aufbau.pageSize.height = masse.hoehe;
  aufbau.orientation = quer ? Dokumentmodell.Orientation.Landscape
                            : Dokumentmodell.Orientation.Portrait;
  aufbau.margins.top = seitenrand.oben;
  aufbau.margins.bottom = seitenrand.unten;
  aufbau.margins.left = seitenrand.links;
  aufbau.margins.right = seitenrand.rechts;
  abschnitt.header.sichtbar = kopfAn;
  abschnitt.footer.sichtbar = fussAn;
  abschnitt.header.html = $('kopfzeile').innerHTML;
  abschnitt.footer.html = $('fusszeile').innerHTML;
  abschnitteSichern();
}

/* Nachsehen, ob der Zeiger den Abschnitt gewechselt hat. */
function abschnittPruefen() {
  if (!Aufbau) return;
  const nr = abschnittNummerAnStelle();
  if (nr === abschnittJetztNr) return;
  abschnittMerken(abschnittJetztNr);
  abschnittJetztNr = nr;
  abschnittAnwenden(nr);
  const zahl = Aufbau.getSections().length;
  if (zahl > 1) melde('Abschnitt ' + (nr + 1) + ' von ' + zahl + '.');
}

/* Was das Programm behält: je Abschnitt der Seitenaufbau und die beiden
   Zeilen. Der Text selbst liegt weiter unter „inhalt". */
function abschnitteSichern() {
  if (!Aufbau) return;
  Speicher.schreib('abschnitte', Aufbau.getSections().map((a) => ({
    aufbau: a.getPageSetup(),
    nummerierung: a.getPageNumbering(),
    umbruch: a.getBreakBefore(),
    kopf: { sichtbar: !!a.header.sichtbar, html: a.header.html || '',
            wieVorherige: a.header.linkedToPrevious },
    fuss: { sichtbar: !!a.footer.sichtbar, html: a.footer.html || '',
            wieVorherige: a.footer.linkedToPrevious },
  })));
}

function abschnitteHolen() {
  if (!Aufbau) return;
  const gespeichert = Speicher.lies('abschnitte', null);
  if (!Array.isArray(gespeichert) || !gespeichert.length) return;
  while (Aufbau.getSections().length < gespeichert.length) Aufbau.addSection();
  gespeichert.forEach((stand, i) => {
    const a = Aufbau.getSection(i);
    if (!a || !stand) return;
    if (stand.aufbau) Object.assign(a.getPageSetup(), stand.aufbau);
    if (stand.nummerierung) Object.assign(a.getPageNumbering(), stand.nummerierung);
    a.breakBefore = stand.umbruch || null;
    if (stand.kopf) { a.header.sichtbar = stand.kopf.sichtbar;
                      a.header.html = stand.kopf.html;
                      a.header.linkedToPrevious = !!stand.kopf.wieVorherige; }
    if (stand.fuss) { a.footer.sichtbar = stand.fuss.sichtbar;
                      a.footer.html = stand.fuss.html;
                      a.footer.linkedToPrevious = !!stand.fuss.wieVorherige; }
  });
}

/* ============================================================
   1. Zustand
   ============================================================ */

let dateiname = Speicher.lies('dateiname', 'Unbenannt 1');
let geaendert = false;
let funde = [];
let pruefungLaeuft = false;
let zoom = Speicher.lies('zoom', 100);
let marken = Speicher.lies('marken', true);
let tafelOffen = Speicher.lies('tafel', true);
let thema = Speicher.lies('thema', 'auto');
/* Die lebende Prüfung — das, was der Schalter „Rote Wellenlinien" jetzt
   steuert. Vorher schaltete er die Prüfung des Systems an und aus. */
let lebendAn = Speicher.lies('lebend', true);

const CM = 37.795275590551185;     // ein Zentimeter in Bildpunkten bei 96 dpi

/* ============================================================
   2. Die Befehle. Menü, Werkzeugleiste und Tastenkürzel greifen alle
      auf dieselbe Liste zu — ein Befehl steht genau einmal da.
   ============================================================ */

const B = {};

/* ---- Datei ---- */

/* „Neu" leerte einmal das Blatt. Mit den Dokumentreitern tut es, was es
   in jedem anderen Schreibprogramm tut: Es legt ein zweites Dokument an
   und stellt es nach vorn. Der Brief, an dem gerade geschrieben wurde,
   bleibt offen — es geht nichts mehr verloren, und deshalb muss auch
   niemand mehr gefragt werden. */
B.neu = () => {
  dokumentNeu();
  melde('Neues Blatt — ' + Dokumente.anzahl() + ' Dokumente offen.');
};

/* Welches Format beim Speichern genommen wird, wenn eine Datei dieser Art
   geöffnet wurde. Was sich nicht zurückschreiben lässt, kommt dem Nächsten
   gleich: Eine Word-Vorlage wird zur Word-Datei. */
const SCHREIBBAR = {
  odt: 'odt', fodt: 'fodt', docx: 'docx', doc: 'doc', rtf: 'rtf',
  html: 'html', htm: 'html', txt: 'txt', md: 'txt',
  dotx: 'docx', docm: 'docx', odf: 'odt', ott: 'odt', dot: 'doc',
};

/* Auch „Öffnen" verwirft nichts mehr: Die Datei kommt in einen eigenen
   Reiter, wenn im vordersten schon etwas steht. */
B.oeffnen = async () => {
  /* Erst der Dateibrowser des Systems — der kennt die Ordner des Menschen,
     seine Lesezeichen und die gewohnte Bedienung. Nur wenn es ihn nicht gibt
     (im Browser statt im eigenen Fenster), bleibt der schlichte Dateiwähler. */
  let wahl = null;
  try {
    const antwort = await fetch(amFenster('oeffnen-dialog'), { method: 'POST' });
    if (antwort.ok) wahl = await antwort.json();
  } catch (e) { /* kein eigenes Fenster — weiter unten */ }

  if (wahl && wahl.abgebrochen) { melde('Nicht geöffnet.'); return; }

  if (wahl && wahl.pfad) {
    try {
      const daten = await fetch(amFenster('lesen'));
      if (!daten.ok) {
        let grund = 'Fehler ' + daten.status;
        try { grund = (await daten.json()).fehler || grund; } catch (e) { /* egal */ }
        throw new Error(grund);
      }
      await dateiUebernehmen(new File([await daten.blob()], wahl.name || 'Dokument'));
      await zuletztHolen();
    } catch (grund) {
      melde('Die Datei ließ sich nicht öffnen: ' + grund.message);
    }
    return;
  }

  const waehler = document.createElement('input');
  waehler.type = 'file';
  waehler.accept = '.odt,.ott,.fodt,.docx,.dotx,.doc,.dot,.rtf,.html,.htm,'
                 + '.txt,.md,.xml,text/plain,text/html';
  waehler.addEventListener('change', async () => {
    const datei = waehler.files && waehler.files[0];
    if (datei) await dateiUebernehmen(datei);
  });
  waehler.click();
};

/* Die zuletzt geöffneten Dateien.

   Die Liste selbst führt der Server; hier steht nur eine Abschrift. Der
   Grund ist die Bauart des Menüs: Es wird im Augenblick des Aufklappens
   gezeichnet und kann dabei nicht auf eine Antwort warten. Also wird die
   Abschrift nachgeführt, sobald sich etwas geändert haben kann — beim
   Start, nach jedem Öffnen, nach jedem Speichern.

   Geöffnet wird über die Nummer in der Liste, nicht über den Pfad. Die
   Seite erfährt gar nicht, wo die Datei liegt; das weiß der Server. */
let zuletztListe = [];

async function zuletztHolen() {
  try {
    const antwort = await fetch('zuletzt');
    zuletztListe = antwort.ok ? await antwort.json() : [];
  } catch (e) {
    zuletztListe = [];                 /* kein eigenes Fenster, kein Server */
  }
}

function zuletztPunkte() {
  if (!zuletztListe.length) {
    return [{ name: 'Noch nichts geöffnet', tun: () => {} }];
  }
  return zuletztListe.map((eintrag, nr) => ({
    name: eintrag.name,
    tun: () => B.zuletztOeffnen(nr),
  }));
}

B.zuletztOeffnen = async (nr) => {
  try {
    const antwort = await fetch(amFenster('zuletzt-oeffnen?nr=' + nr), { method: 'POST' });
    if (!antwort.ok) {
      let grund = 'Fehler ' + antwort.status;
      try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
      throw new Error(grund);
    }
    const wahl = await antwort.json();
    const daten = await fetch(amFenster('lesen'));
    if (!daten.ok) throw new Error('Fehler ' + daten.status);
    await dateiUebernehmen(new File([await daten.blob()], wahl.name || 'Dokument'));
  } catch (grund) {
    melde('Die Datei ließ sich nicht öffnen: ' + grund.message);
  }
  /* In beiden Fällen: Ist die Datei inzwischen weg, fällt sie beim
     Nachfragen aus der Liste und steht beim nächsten Aufklappen nicht mehr da. */
  await zuletztHolen();
};

/* ------------------------------------------------------------
   Neu aus Vorlage

   Eine ganze Vorlage ist ein Dokument, kein Textbaustein: Der Baustein
   nimmt nur den Text, und bei einer ganzen Seite käme dabei genau das weg,
   was sie ausmacht — Briefkopf, Ränder, Schriften.

   Geöffnet wird eine Abschrift. Der Name im Fenster ist der der Vorlage,
   der Weg zur Datei aber nicht: Strg+S legt wie immer eine neue Datei an,
   und „Speichern unter" steht im letzten Ordner, in dem gearbeitet wurde,
   nicht in den Vorlagen. Eine Vorlage, die beim dritten Brief überschrieben
   ist, war keine.

   Die Liste führt der Server, aus Ordnern. Wer eine Vorlage aus dem
   Internet hat, legt sie hinein — „Vorlagenordner öffnen" ruft dafür die
   Dateiverwaltung des Arbeitsplatzes. Ein eigenes Fenster zum Verwalten
   von Dateien zu bauen hieße, eine schlechtere Dateiverwaltung zu
   schreiben als die, die schon da ist.

   Gezeigt wird sie als Fläche mit Miniaturblättern — js/vorlagen.js. Hier
   steht nur, was mit dem Server zu tun hat: holen, öffnen, ablegen.
   ------------------------------------------------------------ */
let vorlagenListe = [];

async function vorlagenHolen() {
  try {
    const antwort = await fetch('vorlagen.json');
    vorlagenListe = antwort.ok ? await antwort.json() : [];
  } catch (e) {
    vorlagenListe = [];                /* kein eigenes Fenster, kein Server */
  }
}

B.vorlageOeffnen = async (nr) => {
  try {
    const antwort = await fetch(amFenster('vorlage-oeffnen?nr=' + nr), { method: 'POST' });
    if (!antwort.ok) {
      let grund = 'Fehler ' + antwort.status;
      try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
      throw new Error(grund);
    }
    const wahl = await antwort.json();
    const daten = await fetch(amFenster('lesen'));
    if (!daten.ok) throw new Error('Fehler ' + daten.status);
    await dateiUebernehmen(new File([await daten.blob()], wahl.name || 'Vorlage'));
    melde('Abschrift von „' + (wahl.name || 'Vorlage') + '" — die Vorlage selbst '
        + 'bleibt, wie sie ist.');
  } catch (grund) {
    melde('Die Vorlage ließ sich nicht öffnen: ' + grund.message);
  }
  /* Ist sie inzwischen weggeworfen, fällt sie beim Nachfragen aus der Liste. */
  await vorlagenHolen();
};

/* Beide Oberflächen gehen denselben Weg: Das Menü ruft dies, und das Band
   ruft dies. Vorher hing an der Menüleiste ein Klappmenü mit Namen und am
   Band ein Auswahlfeld — zwei Wege zur selben Sache, und der eine kannte
   nicht, was der andere konnte.

   Gezeichnet wird die Seite in js/vorlagen.js. Frisch geholt wird die
   Liste bei jedem Öffnen: Wer eine Datei hineinlegt, während das Programm
   läuft, soll sie sehen, ohne neu zu starten. */
B.vorlagenWaehlen = async () => {
  await vorlagenHolen();
  /* Die Nummer ist der Platz in der Liste, die der Server gerade gelesen
     hat — sie muss die eigene bleiben, auch wenn die Gerüste davorstehen.
     Deshalb wird sie hier festgeschrieben und nicht in der Fläche gezählt. */
  const eigene = vorlagenListe.map((v, nr) => Object.assign({ nr }, v));
  Vorlagen.oeffnen(Vorlagen.musterListe().concat(eigene));
};

/* Ein mitgeliefertes Gerüst ins Blatt setzen.

   Es wird keine Datei geöffnet und keine angelegt: Das Muster steht in
   daten/vorlagenmuster.js, wird zu HTML und ersetzt den Inhalt. Von da an
   ist es ein Dokument wie jedes andere — Strg+S legt eine neue Datei an,
   und die Gerüste selbst kann niemand überschreiben, weil es sie als Datei
   gar nicht gibt.

   Der Name im Fenster ist der des Gerüsts. Wer „Bewerbung" öffnet und
   speichert, bekommt „Bewerbung" vorgeschlagen und muss ihn nicht tippen. */
B.musterOeffnen = (kennung) => {
  const html = Vorlagen.musterHtml(kennung);
  if (!html) { melde('Dieses Gerüst gibt es nicht mehr.'); return; }
  const muster = VORLAGENMUSTER.find((m) => m[0] === kennung);

  /* Steht im vordersten Reiter schon etwas, bekommt das Gerüst einen
     eigenen — es soll niemandem seinen Brief wegnehmen. */
  dokumentPlatzSchaffen();

  /* Wie bei „Neu": Das Stilblatt der zuletzt geöffneten Datei muss weg,
     sonst schriebe man den Lebenslauf im Format eines fremden Briefes. */
  Dateien.stileSetzen('');
  Speicher.schreib('importstil', '');
  Dokument.setzeInhalt(html);
  $('kopfzeile').innerHTML = '<br>';
  $('fusszeile').innerHTML = '<br>';
  Speicher.schreib('kopfinhalt', '<br>');
  Speicher.schreib('fussinhalt', '<br>');

  dateiname = muster ? muster[1] : 'Unbenannt 1';
  geaendert = false;
  leereFunde('Noch nicht geprüft.');
  merkeText();
  titelSetzen();

  /* Gleich in die erste Lücke, wie beim Baustein: Man soll tippen können,
     ohne vorher zu zielen. */
  setTimeout(() => {
    const erster = feld.querySelector('.platzhalter');
    if (erster) {
      Bausteine.platzhalterNehmen(erster);
      melde('„' + (muster ? muster[1] : 'Gerüst') + '" — Tab springt zur nächsten '
          + 'Lücke, Tippen ersetzt sie.');
    } else {
      feld.focus();
      melde('„' + (muster ? muster[1] : 'Gerüst') + '" steht im Blatt.');
    }
  }, 0);
};

B.vorlageBehalten = async () => {
  fenster('Als Vorlage behalten', [
    { art: 'satz', text: 'Das Dokument wird so, wie es jetzt ist, in den eigenen '
                       + 'Vorlagenordner gelegt. Danach steht es unter '
                       + '„Datei → Neu aus Vorlage".' },
    { schluessel: 'name', name: 'Name', art: 'text', wert: dateiname },
  ], async (werte) => {
    const name = (werte.name || '').trim();
    if (!name) { melde('Ohne Namen findet man sie nicht wieder — nichts abgelegt.'); return; }

    /* Vorlagen werden als ODF abgelegt, gleich in welchem Format gerade
       gearbeitet wird: Das liest dieses Programm ohne LibreOffice, und eine
       Vorlage, die nur mit installiertem Motor aufgeht, ist eine Falle. */
    const endung = 'odt';
    let wahl;
    try {
      const antwort = await fetch(amFenster('vorlage-ziel?name=' + encodeURIComponent(name)
                                + '&format=' + endung), { method: 'POST' });
      if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
      wahl = await antwort.json();
    } catch (e) {
      melde('Ohne das eigene Fenster gibt es keinen Vorlagenordner. '
          + 'Speichere die Datei stattdessen über „Speichern unter".');
      return;
    }

    melde(wahl.ersetzt ? 'Wird abgelegt und ersetzt die bisherige …' : 'Wird abgelegt …');
    try {
      const inhalt = ohneMarken(Dokument.inhalt());
      let datei;
      try {
        datei = await Dateien.baueMitMotor(endung, inhalt);
      } catch (e) {
        /* Ohne LibreOffice schreibt das Programm die .odt selbst. Das ist
           gröber — keine Tabellen —, aber eine Vorlage, die nur mit
           installiertem Motor entsteht, wäre gar keine. */
        datei = Dateien.baue(endung, inhalt, Dokument.lies().text);
      }
      const geschrieben = await fetch(amFenster('schreiben'), { method: 'POST', body: datei });
      if (!geschrieben.ok) {
        let grund = 'Fehler ' + geschrieben.status;
        try { grund = (await geschrieben.json()).fehler || grund; } catch (e) { /* egal */ }
        throw new Error(grund);
      }
      await vorlagenHolen();
      melde('Als Vorlage „' + name + '" behalten — unter Datei → Neu aus Vorlage.');
    } catch (grund) {
      melde('Das ging nicht: ' + grund.message);
    }
  }, 'Behalten');
};

B.vorlagenOrdner = async () => {
  try {
    const antwort = await fetch('vorlagen-ordner', { method: 'POST' });
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    const wahl = await antwort.json();
    melde('Vorlagenordner geöffnet: ' + (wahl.ordner || '')
        + ' — was du hineinlegst, steht danach im Menü.');
    /* Wer gerade eine Datei hineinlegt, soll sie ohne Neustart finden. */
    setTimeout(vorlagenHolen, 3000);
  } catch (e) {
    melde('Ohne das eigene Fenster lässt sich der Ordner nicht öffnen.');
  }
};

/* Eine Datei ins Blatt holen — gleich, ob sie aus dem Dialog des Systems
   oder aus dem Dateiwähler kommt. */
async function dateiUebernehmen(datei) {
  try {
    /* Erst lesen, dann den Reiter anlegen: Geht das Lesen schief, soll
       kein leerer Reiter zurückbleiben. */
    const gelesen = await Dateien.oeffne(datei);
    dokumentPlatzSchaffen();
    Dokument.setzeInhalt(gelesen);

    /* Das Stilblatt der Datei gehört zum Dokument. Ohne es stünde derselbe
       Brief nach dem nächsten Start wieder anders da. */
    Speicher.schreib('importstil', Dateien.stileLesen());

    /* Wer einen Brief in Word mit 2,5 cm Rand geschrieben hat, will ihn
       hier nicht plötzlich mit 2 cm sehen — das verschiebt jede Zeile. */
    const seite = Dateien.seiteZuletzt();
    if (seite) {
      for (const kante of ['oben', 'unten', 'links', 'rechts']) {
        if (typeof seite[kante] === 'number' && seite[kante] >= 0 && seite[kante] <= 80) {
          seitenrand[kante] = seite[kante];
        }
      }
      seiteAnwenden();
    }

    dateiname = datei.name.replace(/\.[^.]+$/, '');

    /* In dem Format weiterspeichern, in dem die Datei kam.
       Wer einen Word-Brief öffnet, ändert und Strg+S drückt, erwartet
       wieder eine Word-Datei — und nicht eine .odt, die sein Gegenüber
       womöglich gar nicht aufbekommt. */
    const endung = (datei.name.match(/\.([^.]+)$/) || [, ''])[1].toLowerCase();
    if (SCHREIBBAR[endung]) Speicher.schreib('endung', SCHREIBBAR[endung]);

    geaendert = false;
    leereFunde('Noch nicht geprüft.');
    merkeText();
    titelSetzen();
    melde('Geöffnet: ' + datei.name);
  } catch (fehler) {
    melde('Die Datei ließ sich nicht öffnen: ' + fehler.message);
  }
}


const speichereAls = async (endung) => {
  const name = dateiname + '.' + endung;

  /* Word-Dateien und PDF schreibt LibreOffice im Hintergrund. Das dauert
     beim ersten Mal ein paar Sekunden — ohne diese Zeile stünde das Fenster
     stumm da, und niemand wüsste, ob es arbeitet oder hängt. */
  if (Dateien.brauchtMotor(endung)) {
    melde('Wird nach ' + endung.toUpperCase() + ' umgewandelt …');
    try {
      const fertig = await Dateien.baueMitMotor(endung, ohneMarken(Dokument.inhalt()));
      Dateien.gib(fertig, name);
      if (endung !== 'pdf') { geaendert = false; titelSetzen(); }
      melde(endung === 'pdf' ? 'Als ' + name + ' ausgegeben.' : 'Gespeichert als ' + name + '.');
    } catch (grund) {
      /* Für .odt gibt es einen eigenen Schreiber im Programm. Fehlt
         LibreOffice, ist der zwar gröber — aber besser als gar keine Datei. */
      if (endung === 'odt') {
        Dateien.gib(Dateien.baue('odt', ohneMarken(Dokument.inhalt()), Dokument.lies().text), name);
        geaendert = false;
        titelSetzen();
        melde('Gespeichert als ' + name + ' — ohne LibreOffice, deshalb ohne Tabellen.');
        return;
      }
      melde('Das ging nicht: ' + grund.message);
    }
    return;
  }

  Dateien.gib(Dateien.baue(endung, ohneMarken(Dokument.inhalt()), Dokument.lies().text), name);
  geaendert = false;
  titelSetzen();
  melde('Gespeichert als ' + name + '.');
};

B.speichern      = () => speichereAls(Speicher.lies('endung', 'odt'));

/* Für jedes Format ein eigener Befehl — das stand hier einmal, acht Stück,
   und im Band acht Knöpfe dazu. Das Format gehört aber dorthin, wo man
   ohnehin den Ordner und den Namen wählt: in den Speichern-Dialog, der
   sein Klappmenü „Dateityp" mitbringt. Ein zweiter Weg zur selben Sache
   kostet Platz und stiftet Zweifel, welcher der richtige ist. */

/* ------------------------------------------------------------
   „Speichern unter…"

   Ein Dialog statt neun Menüzeilen: Ort und Format an einer Stelle, so wie
   man es aus jedem Schreibprogramm kennt. Der Dialog gehört dem Arbeitsplatz
   — nur er kennt die Ordner, die Lesezeichen und die gewohnte Bedienung.

   Danach baut das Programm die Datei im gewählten Format und schickt sie an
   den gewählten Ort. Dass dabei nur genau dieser eine Ort beschrieben werden
   darf, wacht start.py.
   ------------------------------------------------------------ */
B.speichernUnter = async () => {
  let wahl;
  try {
    const antwort = await fetch(
      amFenster('speichern-dialog?name=' + encodeURIComponent(dateiname)
              + '&format=' + encodeURIComponent(Speicher.lies('endung', 'odt'))),
      { method: 'POST' });
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    wahl = await antwort.json();
  } catch (e) {
    /* Im Browser statt im eigenen Fenster gibt es diesen Dialog nicht.
       Dann bleibt der gewohnte Weg über den Download-Ordner. */
    formatFragen();
    return;
  }

  if (!wahl || wahl.abgebrochen || !wahl.pfad) { melde('Nicht gespeichert.'); return; }

  const endung = wahl.endung || 'odt';
  melde('Wird als ' + endung.toUpperCase() + ' geschrieben …');

  try {
    const inhalt = ohneMarken(Dokument.inhalt());
    const datei = Dateien.brauchtMotor(endung)
      ? await Dateien.baueMitMotor(endung, inhalt)
      : Dateien.baue(endung, inhalt, Dokument.lies().text);

    const geschrieben = await fetch(amFenster('schreiben'), { method: 'POST', body: datei });
    if (!geschrieben.ok) {
      let grund = 'Fehler ' + geschrieben.status;
      try { grund = (await geschrieben.json()).fehler || grund; } catch (e) { /* egal */ }
      throw new Error(grund);
    }

    /* Der Name in der Titelzeile folgt der Datei, und Strg+S bleibt in
       diesem Format — wer einmal als Word gespeichert hat, will beim
       nächsten Mal nicht wieder danach suchen. */
    dateiname = wahl.pfad.replace(/^.*\//, '').replace(/\.[^.]+$/, '');
    if (endung !== 'pdf' && endung !== 'epub') Speicher.schreib('endung', endung);
    geaendert = false;
    titelSetzen();
    await zuletztHolen();
    melde('Gespeichert: ' + wahl.pfad);
  } catch (grund) {
    melde('Das ging nicht: ' + grund.message);
  }
};

/* Ohne eigenes Fenster: wenigstens nach dem Format fragen. */
function formatFragen() {
  fenster('Speichern unter', [
    { art: 'satz', text: 'Ohne das eigene Fenster kann das Programm den Ordner nicht öffnen.\n'
                       + 'Die Datei landet dort, wo Downloads landen.' },
    { schluessel: 'endung', name: 'Format', art: 'auswahl', werte: [
      ['odt', 'ODF-Textdokument (.odt)'], ['docx', 'Word-Dokument (.docx)'],
      ['doc', 'Word 97–2003 (.doc)'], ['rtf', 'Rich Text Format (.rtf)'],
      ['fodt', 'Flaches ODF (.fodt)'], ['html', 'Webseite (.html)'],
      ['txt', 'Reiner Text (.txt)'], ['pdf', 'PDF-Dokument (.pdf)'],
      ['epub', 'E-Book (.epub)'],
    ], wert: Speicher.lies('endung', 'odt') },
  ], (werte) => {
    if (werte.endung !== 'pdf' && werte.endung !== 'epub') Speicher.schreib('endung', werte.endung);
    speichereAls(werte.endung);
  }, 'Speichern');
}
/* PDF ist kein Format zum Weiterschreiben — es wird ausgegeben, nicht
   gespeichert. Deshalb merkt es sich das Programm auch nicht als die Art,
   in der künftig gesichert wird. */
B.speichernPdf   = () => speichereAls('pdf');
/* „Export as Image" aus dem Foto. LibreOffice wandelt das Blatt in ein
   PNG; gebraucht wird es fuer Anhaenge und fuer alles, was kein PDF
   annimmt. */
B.speichernBild  = () => speichereAls('png');

B.umbenennen = () => {
  fenster('Umbenennen', [
    { schluessel: 'name', name: 'Name', art: 'text', wert: dateiname },
  ], (werte) => {
    /* Leer heißt: nichts tun. Nicht „Unbenannt 1" — ein Dokument
       umzubenennen, ohne einen Namen zu nennen, ist kein Wunsch. */
    const neu = (werte.name || '').trim();
    if (!neu) { melde('Ohne Namen bleibt es, wie es hieß.'); return; }
    dateiname = neu;
    titelSetzen();
    melde('Heißt jetzt „' + neu + '".');
  }, 'Umbenennen');
};

/* „Drucken…“ öffnet das Druckfenster — siehe den Abschnitt
   „Drucken: die Vorschau und das Druckfenster“ weiter unten. */

/* „Beenden" schließt das Fenster — und damit alle Dokumente darin. Die
   Rückfrage muss deshalb auch die betreffen, die gerade nicht vorn
   liegen; sonst verlöre man einen Brief, den man nie wieder zu Gesicht
   bekommen hat. */
B.beenden = () => {
  const offen = Dokumente.liste().filter(
    (nr) => (nr === Dokumente.aktiv() ? geaendert : !!geaendertJe[nr]));
  if (!offen.length) { window.close(); return; }
  fenster('Nicht gespeichert', [
    { art: 'satz', text: offen.length === 1
        ? '„' + Dokumente.name(offen[0]) + '" hat Änderungen, die in keiner Datei '
          + 'stehen. Wer weitermacht, verliert sie.'
        : offen.length + ' Dokumente haben Änderungen, die in keiner Datei stehen: '
          + offen.map((nr) => '„' + Dokumente.name(nr) + '"').join(', ')
          + '. Wer weitermacht, verliert sie.' },
  ], () => window.close(), 'Trotzdem beenden');
};

/* „Schließen" schließt das Dokument, nicht das Programm: Es bleibt ein
   leeres Blatt stehen, auf dem sich weiterschreiben lässt. Wer das Fenster
   loswerden will, nimmt „Beenden". */
B.schliessen = () => dokumentSchliessen();

/* Im Aufbau stehen „Suchen" und „Ersetzen" einzeln neben „Suchen und
   Ersetzen". Es ist dieselbe Leiste — sie stellt nur die Schreibstelle
   gleich dorthin, wo man hinwollte. */
B.suchen = () => { sucheZeigen(true); $('suche-was').focus(); };
B.ersetzen = () => { sucheZeigen(true); $('suche-womit').focus(); };

/* ---- Bearbeiten ---- */

B.rueckgaengig = () => Dokument.befehl('undo');
B.wiederholen  = () => Dokument.befehl('redo');
B.ausschneiden = () => Dokument.befehl('cut');
B.kopieren     = () => Dokument.befehl('copy');
B.einfuegen    = () => { feld.focus(); document.execCommand('paste'); };

/* ============================================================
   EINFUEGEN — DIE KLAPPE AUS SEINEM BILD

   „Im Moment besteht die Funktion nur im blinden Einfuegen in Lunivo.
   Funktion ist nach Bildvorlage auszubauen."

   Blind war das richtige Wort: Ein Klick, und was kam, kam. In WPS
   traegt der Knopf einen Pfeil, und darunter steht, WIE eingefuegt
   werden soll:

       Formatierter Text
       Passend formatiert einfuegen
       Unformatierter Text            Strg+Alt+T
       ─────
       Inhalte einfuegen…             Strg+Alt+V
       Standard zum Einfuegen festlegen…

   Der Unterschied ist nicht klein. Text aus einer Webseite bringt
   Farben, Schriftgroessen und ganze Geruste mit. „Passend formatiert"
   heisst: den Text nehmen, das Aussehen des Dokuments behalten — das
   ist fast immer das Gewollte, und bisher gab es dafuer keinen Weg.
   ============================================================ */
let nurText = false;
let einfuegeArt = Speicher.lies('einfuegeArt', 'passend');

B.einfuegenOhne = () => { nurText = true; feld.focus(); document.execCommand('paste'); };

/* „Passend formatiert": Der Text kommt, die Formatierung des Ziels
   bleibt. Technisch derselbe Weg wie beim nackten Text — nur dass
   Absaetze und Zeilenumbrueche erhalten bleiben. */
let passendEinfuegen = false;
B.einfuegenPassend = () => { passendEinfuegen = true; feld.focus(); document.execCommand('paste'); };
B.einfuegenFormatiert = () => { nurText = false; passendEinfuegen = false; feld.focus(); document.execCommand('paste'); };

const EINFUEGEARTEN = [
  ['formatiert', 'Formatierter Text', 'kleben',
   () => B.einfuegenFormatiert(), ''],
  ['passend',    'Passend formatiert einfügen', 'ohneformat',
   () => B.einfuegenPassend(), ''],
  ['nurtext',    'Unformatierter Text', 'Aa',
   () => B.einfuegenOhne(), 'Strg+Alt+T'],
];

B.einfuegenKlappe = (knopf) => {
  designTafelZeigen(knopf, 'Einfügen', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [kuerzel, name, bild, tun, taste] of EINFUEGEARTEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile'
        + (einfuegeArt === kuerzel ? ' richtungszeile--gilt' : '');
      if (SYMBOLE[bild]) k.appendChild(symbol(bild));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      if (taste) {
        const t = document.createElement('em');
        t.className = 'klappzeile__taste';
        t.textContent = taste;
        k.appendChild(t);
      }
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => { designTafelWeg(); tun(); });
      tafel.appendChild(k);
    }

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    const zeile = (bild, name, taste, tun) => {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      if (SYMBOLE[bild]) k.appendChild(symbol(bild));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      if (taste) {
        const t = document.createElement('em');
        t.className = 'klappzeile__taste';
        t.textContent = taste;
        k.appendChild(t);
      }
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => { designTafelWeg(); tun(); });
      tafel.appendChild(k);
    };
    zeile('ohneformat', 'Inhalte einfügen…', 'Strg+Alt+V', () => B.inhalteEinfuegen());
    zeile('zahnrad', 'Standard zum Einfügen festlegen…', '', () => B.einfuegeStandard());
  });
};

/* „Inhalte einfuegen…": Was liegt in der Ablage, und wie soll es
   hinein? In WPS ein Fenster mit einer Liste der Formen. */
B.inhalteEinfuegen = async () => {
  let hat = { html: false, text: false };
  try {
    const stuecke = await navigator.clipboard.read();
    for (const st of stuecke) {
      if (st.types.includes('text/html')) hat.html = true;
      if (st.types.includes('text/plain')) hat.text = true;
    }
  } catch (e) {
    /* Ohne Erlaubnis sagt der Browser nichts ueber die Ablage. Dann
       stehen beide Formen da, und der Versuch entscheidet. */
    hat = { html: true, text: true };
  }
  fenster('Inhalte einfügen', [
    { art: 'satz', text: 'Wie soll das Eingefügte aussehen?' },
    { schluessel: 'art', name: 'Als', art: 'auswahl', wert: einfuegeArt,
      werte: EINFUEGEARTEN.map(([k, name]) => [k, name]) },
  ], (werte) => {
    const eintrag = EINFUEGEARTEN.find(([k]) => k === werte.art) || EINFUEGEARTEN[1];
    eintrag[3]();
  }, 'Einfügen');
};

B.einfuegeStandard = () => {
  fenster('Standard zum Einfügen', [
    { art: 'satz', text: 'Was Strg+V tut, wenn nichts anderes gewählt wurde. '
                       + '„Passend formatiert" nimmt den Text und behält das '
                       + 'Aussehen dieses Dokuments — für Text aus dem Netz '
                       + 'ist das fast immer das Richtige.' },
    { schluessel: 'art', name: 'Standard', art: 'auswahl', wert: einfuegeArt,
      werte: EINFUEGEARTEN.map(([k, name]) => [k, name]) },
  ], (werte) => {
    einfuegeArt = werte.art;
    Speicher.schreib('einfuegeArt', einfuegeArt);
    melde('Standard zum Einfügen: '
      + (EINFUEGEARTEN.find(([k]) => k === einfuegeArt) || EINFUEGEARTEN[1])[1] + '.');
  });
};

/* ------------------------------------------------------------
   Was beim Einfügen ankommt

   Text aus einer Webseite bringt alles mit: Farben, Schriftgrößen,
   Klassennamen, manchmal ganze Gerüste aus <div> und <span>. Ungefiltert
   eingesetzt sieht der Absatz danach aus wie die Webseite und nicht wie
   das Dokument — und die Schriftwahl in der Werkzeugleiste greift nicht
   mehr, weil an jedem Wort schon eine eigene steht.

   Deshalb kommt nur durch, was ein Dokument braucht: Absätze,
   Überschriften, Listen, Tabellen, fett/kursiv/unterstrichen, Verweise.
   Farben und Schriften bleiben draußen — die stellt man hier ein.
   ------------------------------------------------------------ */
const EINFUEGEN_ERLAUBT = new Set([
  'P', 'BR', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
  'UL', 'OL', 'LI', 'BLOCKQUOTE', 'PRE', 'HR',
  'STRONG', 'B', 'EM', 'I', 'U', 'S', 'STRIKE', 'SUP', 'SUB', 'CODE',
  'TABLE', 'THEAD', 'TBODY', 'TR', 'TH', 'TD', 'A',
]);

function eingefuegtesSaeubern(html) {
  const hilfe = document.createElement('div');
  hilfe.innerHTML = html;

  for (const weg of hilfe.querySelectorAll('script,style,meta,link,head,title')) {
    weg.remove();
  }

  /* Rückwärts durch alle Elemente: Wer ein Elternteil auflöst, während er
     noch in ihm steht, verliert den Rest der Liste. */
  const alle = [...hilfe.querySelectorAll('*')].reverse();
  for (const el of alle) {
    if (!EINFUEGEN_ERLAUBT.has(el.tagName)) {
      /* Nicht wegwerfen — auflösen. Der Text darin ist das, was gewollt war;
         nur der Kasten drumherum gehört nicht hierher. */
      el.replaceWith(...el.childNodes);
      continue;
    }
    for (const name of [...el.getAttributeNames()]) {
      const behalten = (el.tagName === 'A' && name === 'href')
                    || (el.tagName === 'TD' && (name === 'colspan' || name === 'rowspan'))
                    || (el.tagName === 'TH' && (name === 'colspan' || name === 'rowspan'));
      if (!behalten) el.removeAttribute(name);
    }
  }
  return hilfe.innerHTML;
}

/* Reiner Text wird zu Absätzen: Eine Leerzeile trennt, eine einfache
   Zeilenschaltung bleibt eine Zeilenschaltung. Ohne das käme ein ganzer
   Aufsatz als ein Klumpen an. */
function textAlsAbsaetze(text) {
  const schutz = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return text.split(/\n\s*\n/)
    .map((teil) => teil.trim())
    .filter(Boolean)
    .map((teil) => '<p>' + schutz(teil).replace(/\n/g, '<br>') + '</p>')
    .join('') || '<p><br></p>';
}

for (const teil of [feld, $('kopfzeile'), $('fusszeile')]) {
  if (!teil) continue;
  teil.addEventListener('paste', (e) => {
    const daten = e.clipboardData;
    if (!daten) return;                       // dann macht es WebKit selbst
    e.preventDefault();

    /* Drei Wege, wie er sie im Bild hat:
         formatiert   alles mitnehmen, nur geputzt
         passend      Absaetze behalten, Aussehen des Dokuments
         nurtext      der nackte Text
       Ohne ausdrueckliche Wahl gilt, was unter „Standard zum Einfuegen
       festlegen" steht. */
    const art = nurText ? 'nurtext' : (passendEinfuegen ? 'passend' : null);
    const wie = art || einfuegeArt;
    nurText = false;
    passendEinfuegen = false;

    const roh = wie === 'formatiert' ? daten.getData('text/html') : '';
    const html = roh
      ? eingefuegtesSaeubern(roh)
      : textAlsAbsaetze(daten.getData('text/plain') || '');

    /* Über execCommand, damit Strg+Z es zurücknimmt. */
    document.execCommand('insertHTML', false, html);
    document.dispatchEvent(new CustomEvent('dokument:geaendert'));
  });
}
B.allesMarkieren = () => { feld.focus(); document.execCommand('selectAll'); };

/* ---- Format ---- */

B.fett    = () => Dokument.befehl('bold');
B.kursiv  = () => Dokument.befehl('italic');
B.unter   = () => Dokument.befehl('underline');
B.durch   = () => Dokument.befehl('strikeThrough');
B.links   = () => Dokument.befehl('justifyLeft');
B.mitte   = () => Dokument.befehl('justifyCenter');
B.rechts  = () => Dokument.befehl('justifyRight');
B.block   = () => Dokument.befehl('justifyFull');
/* ---- Aufzaehlung und Nummerierung ----

   „ist ohne Funktion" — sie tat etwas, aber das Ergebnis war nicht zu
   sehen. execCommand('insertUnorderedList') baut die Liste IN den
   Absatz hinein:

       <p><ul><li>Erste Zeile</li></ul></p>

   Ein <ul> darf nicht in einem <p> stehen. Der Browser rueckt das beim
   naechsten Neuzeichnen zurecht, und dabei geht der Punkt verloren oder
   der Absatzabstand legt sich darueber. Man klickt, und es passiert
   scheinbar nichts.

   Also nach dem Befehl aufraeumen: Liste aus dem Absatz herausheben,
   den leeren Absatz wegwerfen. */
/* ============================================================
   EINEN BLOCK EINFUEGEN

   execCommand('insertHTML') fuegt in den laufenden Text ein, und der
   laufende Text ist ein Absatz. Ein <div> darf dort nicht stehen — der
   Browser macht daraus stillschweigend ein <span> und wirft den Kasten
   weg.

   Genau das war sein Befund: „Der Rahmen laesst sich nicht entfernen."
   Er liess sich nicht entfernen, weil es ihn gar nicht gab. Im Text
   stand ein <span> mit grauem Hintergrund.

   Nachtraeglich geradeziehen hilft nicht: Der Block ist schon weg,
   bevor man ihn suchen kann. Also gar nicht erst durch execCommand,
   sondern neben den Absatz gesetzt.
   ============================================================ */
function blockEinfuegen(el, hinein) {
  const auswahl = window.getSelection();
  let absatz = null;
  if (auswahl && auswahl.rangeCount) {
    let k = auswahl.getRangeAt(0).startContainer;
    if (k && k.nodeType === Node.TEXT_NODE) k = k.parentElement;
    absatz = k && k.closest ? k.closest('.dokument > *') : null;
  }
  if (absatz && feld.contains(absatz)) absatz.parentNode.insertBefore(el, absatz.nextSibling);
  else feld.appendChild(el);

  /* Dahinter eine leere Zeile, sonst kommt man hinter dem Block nicht
     mehr zum Schreiben. */
  const danach = document.createElement('p');
  danach.innerHTML = '<br>';
  el.parentNode.insertBefore(danach, el.nextSibling);

  const ziel = hinein ? (el.querySelector('p') || el) : danach;
  const r = document.createRange();
  r.selectNodeContents(ziel);
  r.collapse(true);
  auswahl.removeAllRanges();
  auswahl.addRange(r);
  feld.focus();
  return el;
}

/* DASSELBE GILT FUER JEDEN BLOCK IM ABSATZ.

   Ein <div> darf so wenig in einem <p> stehen wie ein <ul>. Beim
   Textfeld fiel das erst auf, als er schrieb: „Der Rahmen laesst sich
   nicht entfernen." Er liess sich nicht entfernen, weil es ihn gar
   nicht gab — der Browser hatte aus dem <div class="textrahmen"> beim
   Einfuegen ein <span> gemacht und den Kasten dabei verloren.

   Also nicht nur Listen geradeziehen, sondern jeden Block. */
function bloeckeGeradeziehen() {
  listeGeradeziehen();
  for (const block of [...feld.querySelectorAll('p > div, p > table')]) {
    const absatz = block.parentElement;
    absatz.parentNode.insertBefore(block, absatz);
    if (!absatz.textContent.trim() && !absatz.querySelector('img, svg')) absatz.remove();
  }
}

function listeGeradeziehen() {
  for (const liste of [...feld.querySelectorAll('p > ul, p > ol')]) {
    const absatz = liste.parentElement;
    absatz.parentNode.insertBefore(liste, absatz);
    /* Was im Absatz noch stand, gehoert vor die Liste — sonst
       verschwindet Text, den jemand geschrieben hat. */
    if (absatz.textContent.trim()) {
      absatz.parentNode.insertBefore(absatz, liste);
    } else {
      absatz.remove();
    }
  }
}

B.punkte = () => {
  Dokument.befehl('insertUnorderedList');
  listeGeradeziehen();
  geaendertMelden();
};
B.zahlen = () => {
  Dokument.befehl('insertOrderedList');
  listeGeradeziehen();
  geaendertMelden();
};
B.einzugMehr    = () => Dokument.befehl('indent');
B.einzugWeniger = () => Dokument.befehl('outdent');
B.schlicht      = () => { Dokument.befehl('removeFormat'); Dokument.befehl('formatBlock', 'p'); };

const absatz = (was) => Dokument.befehl('formatBlock', was);

/* Titel, Untertitel und „Kein Leerraum" sind Absatzformate mit einem Zusatz:
   Sie sehen anders aus als eine gewöhnliche Überschrift oder ein gewöhnlicher
   Absatz. Der Zusatz steht als Klasse am Absatz — so greift die Vorlage
   darauf zu, und ein späteres Ändern der Vorlage wirkt überall. */
function vorlageSetzen(tag, klasse) {
  Dokument.befehl('formatBlock', tag);
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return;
  let el = auswahl.anchorNode;
  while (el && el !== feld && el.parentNode !== feld) el = el.parentNode;
  if (!el || el === feld) return;
  /* Die anderen Zusätze müssen weg — ein Absatz ist entweder Titel oder
     Untertitel, nicht beides. Und er trägt höchstens EINE eigene Vorlage:
     Ohne diese Schleife sammelte ein Absatz beim Umformatieren
     „eigen-1 eigen-2 eigen-3" an, und welche davon gilt, entschiede die
     Reihenfolge im Stilblatt — also der Zufall. */
  el.classList.remove('titel', 'untertitel', 'ohne-abstand');
  for (const klasseDa of [...el.classList]) {
    if (klasseDa.startsWith('eigen-')) el.classList.remove(klasseDa);
  }
  if (!klasse && !el.classList.length) el.removeAttribute('class');
  if (klasse) el.classList.add(klasse);
  geaendertMelden();
}

/* Die Schriftgröße kennt execCommand nur in sieben Stufen. Der Umweg:
   die größte Stufe setzen und die dabei entstandenen Kästchen danach auf
   die gewünschte Punktgröße stellen. Das ist der übliche Weg — anders
   käme die Änderung nicht in den Rückgängig-Stapel. */
function schriftgroesse(pt) {
  Dokument.befehl('fontSize', '7');
  for (const alt of [...feld.querySelectorAll('font[size="7"]')]) {
    const neu = document.createElement('span');
    neu.style.fontSize = pt + 'pt';
    while (alt.firstChild) neu.appendChild(alt.firstChild);
    alt.replaceWith(neu);
  }
  for (const s of feld.querySelectorAll('span')) {
    if (/x-large$/.test(s.style.fontSize)) s.style.fontSize = pt + 'pt';
  }
  geaendertMelden();
}

const schriftart = (name) => Dokument.befehl('fontName', name);

/* ---- Einfügen ---- */

const zweiStellen = (n) => String(n).padStart(2, '0');

B.datum = () => {
  const d = new Date();
  Dokument.einfuegen(zweiStellen(d.getDate()) + '.' + zweiStellen(d.getMonth() + 1) + '.' + d.getFullYear());
};
B.uhrzeit = () => {
  const d = new Date();
  Dokument.einfuegen(zweiStellen(d.getHours()) + ':' + zweiStellen(d.getMinutes()));
};

/* ============================================================
   DATUM UND UHRZEIT

   Nach seinem Bild des WPS-Fensters:

       Verfügbare Formate:            Sprache:
       ┌──────────────────────┐ ▲     [Deutsch (Deutschland) ▾]
       │ 15.09.2026           │ │
       │ Dienstag, 15. Sep…   │ │
       │ …                    │ ▼     [ ] Automatisch aktualisieren
       └──────────────────────┘
                                      Abbrechen        OK

   Meine erste Fassung war ein Klappfeld mit sieben Eintraegen. Er hat
   beide Bilder nebeneinander geschickt und gefragt, ob das nach seiner
   Vorgabe aussieht. Nein.

   DIE LISTE HAENGT AN DER SPRACHE. Das ist der Grund, warum die
   Sprachauswahl daneben steht und nicht in den Optionen: Wer ein
   Schreiben auf Englisch aufsetzt, will „September 15, 2026" und nicht
   „15. September 2026" — im selben Fenster, im selben Augenblick.
   ============================================================ */
const ZEITSPRACHEN = [
  ['de-DE', 'Deutsch (Deutschland)'],
  ['de-AT', 'Deutsch (Österreich)'],
  ['de-CH', 'Deutsch (Schweiz)'],
  ['en-US', 'Englisch (die USA)'],
  ['en-GB', 'Englisch (Großbritannien)'],
  ['fr-FR', 'Französisch (Frankreich)'],
];

/* Die Formen, die WPS anbietet — als Rechenvorschrift, damit sie in
   jeder Sprache stimmen. */
const ZEITFORMEN = [
  (d, l) => d.toLocaleDateString(l),
  (d, l) => d.toLocaleDateString(l, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }),
  (d, l) => d.toLocaleDateString(l, { day: 'numeric', month: 'long', year: 'numeric' }),
  (d, l) => d.toLocaleDateString(l, { day: '2-digit', month: '2-digit', year: '2-digit' }),
  (d) => d.getFullYear() + '-' + zweiStellen(d.getMonth() + 1) + '-' + zweiStellen(d.getDate()),
  (d, l) => d.toLocaleDateString(l, { day: '2-digit', month: 'short', year: '2-digit' }),
  (d, l) => d.toLocaleDateString(l, { day: 'numeric', month: 'numeric', year: 'numeric' }),
  (d, l) => d.toLocaleDateString(l, { day: 'numeric', month: 'short', year: '2-digit' }),
  (d, l) => d.toLocaleDateString(l, { day: 'numeric', month: 'long', year: 'numeric' }).replace('.', ''),
  (d, l) => d.toLocaleDateString(l, { month: 'long', year: '2-digit' }),
  (d, l) => d.toLocaleDateString(l, { month: 'short', year: '2-digit' }),
  (d, l) => d.toLocaleDateString(l) + ' ' + d.toLocaleTimeString(l, { hour: '2-digit', minute: '2-digit' }),
  (d, l) => d.toLocaleDateString(l) + ' ' + d.toLocaleTimeString(l),
  (d, l) => d.toLocaleTimeString(l, { hour: '2-digit', minute: '2-digit' }),
  (d, l) => d.toLocaleTimeString(l),
];

let zeitSprache = Speicher.lies('zeitSprache', 'de-DE');
let zeitForm = Speicher.lies('zeitForm', 0);

B.datumUhrzeit = () => {
  auswahlMerken();

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog zeitfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Datum und Uhrzeit</h3>';

  const koerper = document.createElement('div');
  koerper.className = 'zeitfenster__koerper';

  /* --- links: die Formate --- */
  const links = document.createElement('div');
  links.className = 'zeitfenster__spalte';
  const kopfL = document.createElement('p');
  kopfL.className = 'zeitfenster__kopf';
  kopfL.textContent = 'Verfügbare Formate:';
  links.appendChild(kopfL);

  const liste = document.createElement('div');
  liste.className = 'zeitliste';
  liste.setAttribute('role', 'listbox');
  links.appendChild(liste);
  koerper.appendChild(links);

  /* --- rechts: Sprache und der Haken --- */
  const rechts = document.createElement('div');
  rechts.className = 'zeitfenster__spalte';
  const kopfR = document.createElement('p');
  kopfR.className = 'zeitfenster__kopf';
  kopfR.textContent = 'Sprache:';
  rechts.appendChild(kopfR);

  const sprache = document.createElement('select');
  sprache.className = 'zeitfenster__sprache';
  for (const [wert, name] of ZEITSPRACHEN) {
    const o = document.createElement('option');
    o.value = wert; o.textContent = name;
    if (wert === zeitSprache) o.selected = true;
    sprache.appendChild(o);
  }
  sprache.addEventListener('change', () => { zeitSprache = sprache.value; listeBauen(); });
  rechts.appendChild(sprache);

  const frisch = document.createElement('label');
  frisch.className = 'zeitfenster__haken';
  const haken = document.createElement('input');
  haken.type = 'checkbox';
  frisch.appendChild(haken);
  frisch.appendChild(document.createTextNode(' Automatisch aktualisieren'));
  rechts.appendChild(frisch);

  const satz = document.createElement('p');
  satz.className = 'zeitfenster__satz';
  satz.textContent = 'Ohne Haken steht das Datum fest im Text. Mit Haken '
                   + 'rechnet es sich beim Öffnen neu — gut für eine Vorlage, '
                   + 'schlecht für einen Brief, der abgeschickt ist.';
  rechts.appendChild(satz);
  koerper.appendChild(rechts);
  kasten.appendChild(koerper);

  function listeBauen() {
    liste.textContent = '';
    const jetzt = new Date();
    /* Auf Deutsch fallen ein paar Formen zusammen — „15.9.2026" kommt
       aus zwei Rechenvorschriften. Zweimal dieselbe Zeile in einer
       Auswahlliste ist ein Fehler, den jeder sofort sieht. */
    const schon = new Set();
    ZEITFORMEN.forEach((mach, i) => {
      let text;
      try { text = mach(jetzt, zeitSprache); } catch (e) { return; }
      if (schon.has(text)) return;
      schon.add(text);
      const z = document.createElement('button');
      z.type = 'button';
      z.className = 'zeitliste__zeile' + (i === zeitForm ? ' zeitliste__zeile--an' : '');
      z.textContent = text;
      z.addEventListener('click', () => {
        zeitForm = i;
        [...liste.children].forEach((c) => c.classList.remove('zeitliste__zeile--an'));
        z.classList.add('zeitliste__zeile--an');
      });
      z.addEventListener('dblclick', () => uebernehmen());
      liste.appendChild(z);
    });
  }

  function uebernehmen() {
    const mach = ZEITFORMEN[zeitForm] || ZEITFORMEN[0];
    const text = mach(new Date(), zeitSprache);
    Speicher.schreib('zeitSprache', zeitSprache);
    Speicher.schreib('zeitForm', zeitForm);
    grund.remove();
    auswahlZurueck();
    if (haken.checked) {
      /* Ein Feld, das sich beim Oeffnen neu rechnet. Es traegt seine
         Vorschrift bei sich, sonst wuesste beim naechsten Mal niemand,
         welche Form gemeint war. */
      Dokument.einfuegen('<span class="zeitfeld" data-zeitform="' + zeitForm
        + '" data-zeitsprache="' + zeitSprache + '">' + alsSicher(text) + '</span>&#8203;');
    } else {
      Dokument.einfuegen(alsSicher(text));
    }
    geaendertMelden();
    melde('Eingefügt: ' + text + (haken.checked ? ' — rechnet sich neu.' : ''));
  }

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  ab.addEventListener('click', () => grund.remove());
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'OK';
  ok.addEventListener('click', uebernehmen);
  fuss.appendChild(ab); fuss.appendChild(ok);
  kasten.appendChild(fuss);

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
  listeBauen();
};

/* Beim Oeffnen eines Dokuments die Felder nachrechnen, die es sollen. */
function zeitfelderAuffrischen() {
  for (const feldchen of feld.querySelectorAll('.zeitfeld')) {
    const i = parseInt(feldchen.dataset.zeitform, 10) || 0;
    const l = feldchen.dataset.zeitsprache || 'de-DE';
    const mach = ZEITFORMEN[i] || ZEITFORMEN[0];
    try { feldchen.textContent = mach(new Date(), l); } catch (e) { /* Sprache weg */ }
  }
}

/* ============================================================
   SEITENUMBRUCH — SICHTBAR, NICHT NUR IM DRUCK

   Seine Meldung: „Funktion als solche nicht zu erkennen. Die Funktion
   selbst fehlt."

   Beides stimmte. Eingefuegt wurde ein Absatz mit page-break-before: im
   Druck ein Umbruch, auf dem Bildschirm nichts. Man klickte und sah eine
   Leerzeile; die Statuszeile blieb bei „Seite 1 von 1".

   Jetzt ein Block, der den Rest der laufenden Seite auffuellt. Der Text
   dahinter faengt wirklich oben auf der naechsten an, die Seitenzahl
   zaehlt mit, und auf der Linie steht, was sie ist. Gedruckt wird nur
   der Umbruch, nicht die Linie.
   ============================================================ */
B.seitenumbruch = () => {
  const strich = document.createElement('div');
  strich.className = 'seitenumbruch';
  strich.contentEditable = 'false';
  strich.title = 'Seitenumbruch — mit Entf wieder weg';
  blockEinfuegen(strich, false);
  geaendertMelden();
  requestAnimationFrame(() => requestAnimationFrame(zahlenAuffrischen));
  melde('Seitenumbruch eingefügt. Mit Entf wieder weg.');
};

/* Wie hoch muss der Block sein, damit die naechste Zeile oben auf der
   folgenden Seite steht? So hoch wie der Rest der laufenden Seite. Das
   haengt an Papier, Ausrichtung und Raendern und muss deshalb nach jeder
   Aenderung neu gemessen werden — hier, an einer Stelle. */
function umbruecheAuffrischen() {
  const bloecke = feld.querySelectorAll('.seitenumbruch');
  if (!bloecke.length) return;
  const masse = PAPIERE[papier] || PAPIERE.a4;
  const hoeheMm = (quer ? masse.breite : masse.hoehe) - seitenrand.oben - seitenrand.unten;
  const proSeite = Math.max(1, hoeheMm * CM / 10);
  /* Erst alle auf null: Sonst misst der zweite Umbruch die Hoehe, die
     der erste gerade noch hatte, und der Text rutscht bei jedem
     Tastendruck eine Seite weiter. */
  for (const b of bloecke) b.style.height = '0px';
  const obenFeld = feld.getBoundingClientRect().top;
  for (const b of bloecke) {
    const oben = b.getBoundingClientRect().top - obenFeld;
    let rest = proSeite - (oben % proSeite);
    /* Steht der Umbruch zufaellig genau am Seitenanfang, waere der Rest
       fast die ganze Seite — dann ist nichts zu fuellen. */
    if (rest > proSeite - 2) rest = 0;
    b.style.height = Math.max(0, rest) + 'px';
  }
}

B.bild = () => {
  const waehler = document.createElement('input');
  waehler.type = 'file';
  waehler.accept = 'image/*';
  waehler.addEventListener('change', () => {
    const datei = waehler.files && waehler.files[0];
    if (!datei) return;
    const leser = new FileReader();
    leser.onload = () => Dokument.einfuegen('<img src="' + leser.result + '" alt="">');
    leser.readAsDataURL(datei);
  });
  waehler.click();
};

/* ============================================================
   DER RASTER-WÄHLER FÜR TABELLEN

   Vorlage ist WPS: Ein Klick auf „Tabelle ▾" öffnet ein Raster. Man fährt
   darüber, oben steht mitlaufend „2 * 3 Tabelle", man klickt, und die
   Tabelle steht.

   Warum das besser ist als zwei Zahlenfelder — und es GAB hier zwei
   Zahlenfelder: Man muss sich nichts vorstellen. Eine Tabelle ist etwas
   Räumliches; „3 Zeilen, 4 Spalten" ist die Übersetzung davon in Zahlen,
   und wer mit Zahlen schlechter umgeht als mit Formen, übersetzt zweimal.
   Für ein Programm, das für Legastheniker gebaut ist, ist das Raster
   nicht Zierde, sondern der eigentliche Weg.

   Die Zahlenfelder bleiben darunter stehen („Tabelle einfügen…"): Für
   zwölf Spalten ist Zielen mit der Maus mühsam, und wer mit der Tastatur
   arbeitet, kommt über das Raster gar nicht hin.
   ============================================================ */

const RASTER_ZEILEN = 10;
const RASTER_SPALTEN = 10;

let tabellenKlappe = null;

function tabellenKlappeWeg() {
  if (tabellenKlappe) { tabellenKlappe.remove(); tabellenKlappe = null; }
}

function tabelleBauen(zeilen, spalten) {
  auswahlZurueck();
  const zeile = '<tr>' + '<td><br></td>'.repeat(spalten) + '</tr>';
  Dokument.einfuegen('<table>' + zeile.repeat(zeilen) + '</table><p><br></p>');
  melde('Tabelle mit ' + zeilen + ' Zeilen und ' + spalten + ' Spalten eingefügt.');
}

function tabellenKlappeZeigen(knopf) {
  if (tabellenKlappe) { tabellenKlappeWeg(); return; }
  auswahlMerken();

  const tafel = document.createElement('div');
  tafel.className = 'katalogklappe tabellenklappe';

  /* Die Überschrift läuft mit: Sie sagt, was der Klick jetzt ergäbe.
     Ohne sie müsste man die Kästchen zählen. */
  const kopf = document.createElement('p');
  kopf.className = 'katalogklappe__kopf';
  kopf.textContent = 'Tabelle einfügen';
  tafel.appendChild(kopf);

  const gitter = document.createElement('div');
  gitter.className = 'tabellenklappe__gitter';
  gitter.style.setProperty('--spalten', String(RASTER_SPALTEN));

  const kaestchen = [];
  const zeigen = (zeilen, spalten) => {
    kopf.textContent = (zeilen && spalten)
      ? zeilen + ' × ' + spalten + ' Tabelle'
      : 'Tabelle einfügen';
    for (const k of kaestchen) {
      k.classList.toggle('tabellenklappe__feld--an',
        k.dataset.zeile <= zeilen && k.dataset.spalte <= spalten);
    }
  };

  for (let z = 1; z <= RASTER_ZEILEN; z++) {
    for (let sp = 1; sp <= RASTER_SPALTEN; sp++) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'tabellenklappe__feld';
      k.dataset.zeile = String(z);
      k.dataset.spalte = String(sp);
      k.title = z + ' × ' + sp;
      k.setAttribute('aria-label', z + ' Zeilen, ' + sp + ' Spalten');
      k.addEventListener('mouseenter', () => zeigen(z, sp));
      /* Auch für die Tastatur: Wer sich mit Tabulator durch das Raster
         bewegt, soll dieselbe Rückmeldung bekommen wie mit der Maus. */
      k.addEventListener('focus', () => zeigen(z, sp));
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        tabellenKlappeWeg();
        tabelleBauen(z, sp);
      });
      kaestchen.push(k);
      gitter.appendChild(k);
    }
  }
  /* Fährt die Maus aus dem Raster heraus, ohne zu klicken, soll die
     Vorschau nicht stehenbleiben — sonst behauptet die Überschrift eine
     Größe, die niemand mehr meint. */
  gitter.addEventListener('mouseleave', () => zeigen(0, 0));
  tafel.appendChild(gitter);

  const strich = document.createElement('div');
  strich.className = 'katalogklappe__strich';
  tafel.appendChild(strich);

  const punkt = (name, tun, aus) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'katalogklappe__punkt' + (aus ? ' katalogklappe__punkt--aus' : '');
    k.textContent = name;
    if (aus) { k.disabled = true; tafel.appendChild(k); return; }
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => { tabellenKlappeWeg(); tun(); });
    tafel.appendChild(k);
  };

  punkt('Tabelle einfügen…', () => B.tabelle());
  punkt('Schnelltabelle…', () => B.schnelltabelle());
  punkt('Eigenschaften der Tabelle…', () => B.tabelleEigenschaften(),
        !zelleOderZuletzt());

  document.body.appendChild(tafel);
  tabellenKlappe = tafel;

  /* Unter den Knopf, und nach innen gerückt, wenn rechts kein Platz mehr
     ist. Erst einhängen, dann messen — vorher hat die Tafel keine Maße. */
  const platz = knopf.getBoundingClientRect();
  const masse = tafel.getBoundingClientRect();
  const rand = 6;
  let links = platz.left;
  if (links + masse.width > window.innerWidth - rand) {
    links = Math.max(rand, window.innerWidth - rand - masse.width);
  }
  tafel.style.left = Math.max(rand, links) + 'px';
  let oben = platz.bottom + 2;
  if (oben + masse.height > window.innerHeight - rand) {
    oben = Math.max(rand, platz.top - masse.height - 2);
  }
  tafel.style.top = oben + 'px';

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(ev) {
      if (tafel.contains(ev.target) || knopf.contains(ev.target)) return;
      tabellenKlappeWeg();
      document.removeEventListener('mousedown', zu);
    });
  }, 0);
}

/* Der Weg von außen: Band und Leiste rufen ihn, und beide reichen ihren
   eigenen Knopf mit — die Klappe soll unter dem stehen, den man gedrückt
   hat, nicht unter irgendeinem. */
/* ============================================================
   DIE TABELLE VERSCHIEBEN

   Kay: „ich kann die Tabelle nicht frei verschieben." Stimmt — sie stand
   da, wo sie eingefügt wurde, und kam von dort nur weg, indem man sie
   ausschnitt und woanders einfügte. In WPS hat jede Tabelle links oben
   einen Griff, an dem man sie zieht.

   WAS „FREI" HIER HEISST. Eine Tabelle mitten in den Text zu legen und
   den Text drumherum fließen zu lassen, wäre das eine — es ist in Word
   die Ausnahme, macht Ärger beim Drucken und ist selten das, was jemand
   will. Gemeint ist fast immer: an eine andere Stelle im Text. Genau das
   macht dieser Griff, und weil die Tabelle dabei im Textfluss bleibt,
   bleibt auch alles heil — Seitenumbruch, Vorlesen, Export.

   Für das andere gibt es die Ausrichtung: links, mittig, rechts. Eine
   Tabelle, die nicht über die ganze Breite geht, steht sonst immer links.
   ============================================================ */

/* Die Griffe, die an einer Tabelle hängen. Vorlage ist WPS: links oben
   der Griff zum Verschieben, rechts oben das ⊗ zum Löschen, unten und
   rechts je ein + für eine weitere Zeile oder Spalte.

   Warum überhaupt Griffe, wo es die Befehle doch in der Leiste gibt: Weil
   „hier noch eine Zeile" ein Gedanke am Ort ist. Der Weg über eine Leiste
   verlangt, ihn zu übersetzen — erst hinsehen, dann hinaufsehen, dann den
   richtigen von dreizehn Knöpfen finden und darauf vertrauen, dass er die
   Zeile dort einfügt, wo man gerade steht. Ein + an der Kante fragt
   nichts und erklärt nichts; es ist da, wo es wirkt. */
const TABELLENGRIFFE = [
  { art: 'schieben', zeichen: '✥', name: 'Tabelle frei verschieben — ziehen' },
  { art: 'weg',      zeichen: '×', name: 'Ganze Tabelle löschen' },
  { art: 'zeile',    zeichen: '+', name: 'Zeile anhängen' },
  { art: 'spalte',   zeichen: '+', name: 'Spalte anhängen' },
  { art: 'groesse',  zeichen: '⤡', name: 'Tabelle größer oder kleiner ziehen' },
];

/* Die Tabelle, ueber der die Maus gerade steht. Sie wird verfolgt, damit
   die Griffe schon beim Hinfahren dastehen und nicht erst nach einem
   Klick — so haelt es WPS, und so sucht man sie. */
let tabelleUnterMaus = null;

let griffe = {};            /* art → Knopf */
let griffZiel = null;       /* die Tabelle, an der sie hängen */
let legeMarke = null;       /* die Linie, die zeigt, wo sie landet */

function griffWeg() {
  for (const k of Object.values(griffe)) k.remove();
  griffe = {};
  griffZiel = null;
}

function legeMarkeWeg() {
  if (legeMarke) { legeMarke.remove(); legeMarke = null; }
}

/* Eine Zeile unten anhängen: so breit wie die breiteste Zeile, damit
   keine Lücke entsteht. */
function zeileAnhaengen(tabelle) {
  const spalten = Math.max(...[...tabelle.rows].map((r) => r.cells.length));
  const zeile = tabelle.insertRow(-1);
  for (let i = 0; i < spalten; i++) {
    const z = zeile.insertCell(-1);
    z.innerHTML = '<br>';
    /* Die Maße der Zelle darüber übernehmen — sonst steht die neue Zeile
       ohne Rahmen und ohne Luft unter einer gestalteten Tabelle. */
    const vorbild = tabelle.rows[tabelle.rows.length - 2];
    const muster = vorbild && vorbild.cells[i];
    if (muster) {
      z.style.border = muster.style.border;
      z.style.padding = muster.style.padding;
    }
  }
  geaendertMelden();
  melde('Zeile angehängt.');
}

function spalteAnhaengen(tabelle) {
  for (const zeile of tabelle.rows) {
    const muster = zeile.cells[zeile.cells.length - 1];
    /* In der Kopfzeile ein <th>, sonst ein <td>: Die Bedeutung der Zeile
       gilt auch für die neue Spalte. */
    const neu = document.createElement(muster && muster.tagName === 'TH' ? 'th' : 'td');
    neu.innerHTML = '<br>';
    if (muster) {
      neu.style.border = muster.style.border;
      neu.style.padding = muster.style.padding;
      neu.style.background = muster.style.background;
    }
    zeile.appendChild(neu);
  }
  geaendertMelden();
  melde('Spalte angehängt.');
}

function griffTun(art, tabelle) {
  if (art === 'zeile') { zeileAnhaengen(tabelle); griffNachmessen(); return; }
  if (art === 'spalte') { spalteAnhaengen(tabelle); griffNachmessen(); return; }
  if (art === 'weg') {
    tabelle.remove();
    griffWeg();
    geaendertMelden();
    melde('Tabelle gelöscht.');
  }
}

/* Der Block, vor oder hinter dem die Tabelle landen soll.

   Gesucht wird unter den direkten Kindern des Schreibfeldes: Absätze,
   Überschriften, andere Tabellen. Tiefer zu greifen hieße, die Tabelle in
   eine Zelle einer anderen Tabelle zu legen — das will niemand, der zieht. */
function blockUnter(y, ausser) {
  let treffer = null;
  for (const block of feld.children) {
    /* Die Tabelle, die man zieht, ist kein Ziel — sie kann nicht vor sich
       selbst landen. Vorher zeigte die Linie beim Überfahren der eigenen
       Tabelle deren Oberkante, und beim Loslassen geschah nichts: eine
       Rückmeldung, die etwas verspricht und nichts hält. */
    if (block === ausser) continue;
    const r = block.getBoundingClientRect();
    if (y >= r.top) treffer = { block, dahinter: y > r.top + r.height / 2 };
    else if (!treffer) return { block, dahinter: false };
  }
  return treffer;
}

function legeMarkeZeigen(ziel) {
  if (!ziel) { legeMarkeWeg(); return; }
  if (!legeMarke) {
    legeMarke = document.createElement('div');
    legeMarke.className = 'legemarke';
    document.body.appendChild(legeMarke);
  }
  const r = ziel.block.getBoundingClientRect();
  legeMarke.style.left = r.left + 'px';
  legeMarke.style.width = r.width + 'px';
  legeMarke.style.top = (ziel.dahinter ? r.bottom : r.top) - 1 + 'px';
}

/* Die Griffe an der Tabelle ausrichten — OHNE die Sperre fuer das
   Ziehen. Waehrend gezogen wird, bewegt sich die Tabelle ja, und die
   Griffe muessen mit; nur das Wegraeumen darf dann nicht passieren. */
/* NUR STELLEN, NICHT NEU ENTSCHEIDEN.

   Hier stand: Sperre kurz aufheben, griffAuffrischen() laufen lassen,
   Sperre zurueck. Das war ein schwerer Fehler. griffAuffrischen()
   entscheidet naemlich auch, OB es Griffe gibt — und waehrend eines Zuges
   steht der Zeiger auf dem Griff und nicht in einer Zelle. Also raeumte
   es die Griffe weg, mitten im Zug. Der Knopf, der den Zeiger gefangen
   hielt, verschwand damit aus dem Dokument, sein pointerup kam nie an,
   und „aufhoeren" lief nie: Die Klasse zieht-tabelle blieb auf dem body
   liegen, mit cursor:move und user-select:none ueber allem. Der Zeiger
   war gefangen, und Text liess sich nicht mehr markieren.

   Diese Fassung stellt die Griffe nur um. Sie nimmt nichts weg und baut
   nichts auf. */
function griffAuffrischenRoh() {
  if (!griffZiel || !griffe.schieben) return;
  griffeStellen(griffZiel);
}

function griffAuffrischen() {
  /* MITTEN IM ZIEHEN NICHT ANFASSEN.

     Das Rollen am Rand setzt scrollTop, das löst „scroll" aus, und der
     Horcher dort rief diese Funktion ungeschützt auf. Steht der Zeiger
     dabei nicht mehr in einer Zelle, räumt sie die Griffe weg — mitten
     im Zug, an dem die Hand gerade hängt. Der Zug endete dann ins Leere,
     und es sah aus, als ließe sich die Tabelle nicht fassen. */
  if (zieht) return;

  /* WELCHE TABELLE GEMEINT IST — und das war der eigentliche Fehler.

     Bisher hing das allein am Zeiger IM Text: Erst hineinklicken, dann
     erscheinen die Griffe. In WPS ist es umgekehrt — man faehrt mit der
     Maus ueber die Tabelle, und der Griff links oben ist da. Wer also
     nach WPS-Art hinfaehrt und zugreifen will, greift bei mir ins Leere:
     Es steht dort nichts, weil noch nicht hineingeklickt wurde.

     Genau das meinte Kay mit „ich kann links oben die Tabelle nicht
     erfassen" — und alles, was ich vorher repariert habe (Pointer-
     Ereignisse, Klemmen, Rollen), war richtig und half ihm trotzdem
     nicht, weil die Griffe zu diesem Zeitpunkt gar nicht dastanden.

     Jetzt zaehlt beides: die Tabelle unter dem Zeiger der Maus ODER die,
     in der die Schreibmarke steht. Die Maus hat Vorrang, denn wer
     hinfaehrt, meint die dort. */
  const zelle = zelleJetzt();
  const tabelle = tabelleUnterMaus || (zelle && zelle.closest('table'));
  if (!tabelle || !feld.contains(tabelle)) { griffWeg(); return; }

  if (!griffe.schieben) {
    for (const { art, zeichen, name } of TABELLENGRIFFE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'tabellengriff tabellengriff--' + art;
      k.title = name;
      k.setAttribute('aria-label', name);
      k.textContent = zeichen;
      if (art === 'schieben') k.addEventListener('pointerdown', griffZiehenBeginnen);
      else if (art === 'groesse') k.addEventListener('pointerdown', groesseZiehenBeginnen);
      else {
        /* Die Auswahl behalten: Sonst ist der Zeiger nach dem Klick nicht
           mehr in der Tabelle, und beim nächsten Messen verschwinden alle
           Griffe unter der Hand. */
        k.addEventListener('mousedown', (e) => e.preventDefault());
        k.addEventListener('click', () => griffTun(art, griffZiel));
      }
      griffe[art] = k;
      document.body.appendChild(k);
    }
  }
  griffZiel = tabelle;

  /* Fest am Fenster ausgerichtet und nicht im Blatt eingehängt: Das Blatt
     wird gezoomt (CSS-zoom), und ein Kind darin bekäme dieselbe Verzerrung
     — die Griffe wären bei 200 % doppelt so groß wie ein Knopf daneben. */
  griffeStellen(tabelle);
}

/* Die Griffe an das Rechteck der Tabelle setzen. */
function griffeStellen(tabelle) {
  const r = tabelle.getBoundingClientRect();
  const flaeche = $('arbeitsflaeche').getBoundingClientRect();

  /* Im Arbeitsbereich bleiben.

     Eine breite Tabelle ragt über das Blatt hinaus — und mit ihr ragten
     die Griffe hinaus: Nach der dritten Spalte lagen × und + über der
     Schreibhilfe rechts daneben. Sie sind am Fenster ausgerichtet und
     wissen von sich aus nichts davon, wo das Blatt aufhört. */
  /* Die Größe wird gemessen, nicht angenommen: Sie hängt an der
     Symbolgröße, die der Anwender einstellt — eine feste Zahl hier wäre
     beim nächsten Umstellen falsch. */
  const GRIFF = griffe.schieben.offsetWidth || 24;
  const luft = 3;
  const haltenX = (x) => Math.max(flaeche.left + 2,
                                  Math.min(x, flaeche.right - 2 - GRIFF));
  /* AUCH NACH OBEN UND UNTEN HALTEN.

     Hier wurde nur waagerecht geklemmt. Steht die Tabelle dicht unter der
     Werkzeugleiste, landete der Griff darueber — also ausserhalb der
     Arbeitsflaeche, halb hinter der Leiste. Sichtbar war er dann noch,
     greifbar nicht mehr, und genau das ist die Klage: "ich kann links
     oben die Tabelle nicht erfassen". */
  const haltenY = (y) => Math.max(flaeche.top + 2,
                                  Math.min(y, flaeche.bottom - 2 - GRIFF));
  const stelle = (art, x, y) => {
    griffe[art].style.left = Math.round(haltenX(x)) + 'px';
    griffe[art].style.top = Math.round(haltenY(y)) + 'px';
  };
  stelle('schieben', r.left - GRIFF - luft, r.top - GRIFF - luft);
  stelle('weg',      r.right + luft,        r.top - GRIFF - luft);
  stelle('zeile',    r.left + r.width / 2 - GRIFF / 2, r.bottom + luft);
  stelle('spalte',   r.right + luft,        r.top + r.height / 2 - GRIFF / 2);
  stelle('groesse',  r.right + luft,        r.bottom + luft);

  /* Rutscht die Tabelle aus dem sichtbaren Bereich, gehen die Griffe mit. */
  const versteckt = r.bottom < flaeche.top || r.top > flaeche.bottom;
  for (const k of Object.values(griffe)) k.hidden = versteckt;
}

let zieht = false;

/* ------------------------------------------------------------
   DAS SICHERHEITSNETZ: DEN ZEIGER IMMER WIEDER FREIGEBEN

   Kay: „kannst du mal den Cursor loslassen!" — und er hatte recht. Beim
   Ziehen liegt die Klasse „zieht-tabelle" auf dem body; sie setzt
   cursor:move und user-select:none ueber ALLES. Bleibt sie liegen, ist
   der Zeiger gefangen und Text laesst sich nicht mehr markieren.

   Liegenbleiben kann sie, wenn das abschliessende pointerup nicht
   ankommt — weil der Knopf verschwunden ist, weil das System
   dazwischenfunkt, weil das Fenster den Fokus verliert. Die Ursache ist
   behoben (siehe griffeStellen); trotzdem gehoert hier ein Netz
   darunter. Ein Programm darf den Zeiger nicht behalten — und wenn doch,
   dann hoechstens bis zum naechsten Loslassen der Taste.
   ------------------------------------------------------------ */
function zugBeenden() {
  if (!zieht && !document.body.classList.contains('zieht-tabelle')) return;
  zieht = false;
  document.body.classList.remove('zieht-tabelle');
  if (typeof legeMarkeWeg === 'function') legeMarkeWeg();
}

window.addEventListener('pointerup', zugBeenden, true);
window.addEventListener('pointercancel', zugBeenden, true);
window.addEventListener('blur', zugBeenden);
/* Auch die Maus-Nachbildung: Wer mit gedrueckter Taste ueber den
   Fensterrand hinausfaehrt und dort loslaesst, bekommt manchmal nur
   dieses hier. */
window.addEventListener('mouseup', zugBeenden, true);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') zugBeenden(); });


/* ============================================================
   FREI VERSCHIEBEN UND AUFZIEHEN

   Kay hat es dreimal gesagt: "ich kann die Tabelle nicht frei
   verschieben" und "nicht gross und klein ziehen". Ich habe zweimal
   etwas anderes gebaut — ein Verschieben zwischen den Absaetzen — und
   dabei erklaert, warum das besser sei. Das war nicht meine
   Entscheidung.

   WIE ES JETZT GEHT. Beim Zug am Griff loest sich die Tabelle aus dem
   Textfluss: Sie bekommt position:absolute im Blatt und liegt von da an
   dort, wo man sie hinzieht — WAEHREND des Zuges, nicht erst beim
   Loslassen. Genau das hat gefehlt; vorher bewegte sich nichts ausser
   einer Linie, und es fuehlte sich an wie festgenagelt.

   Gerechnet wird in Millimetern, nicht in Bildpunkten: Das Blatt wird
   gezoomt, und bei 75 % ist ein Bildpunkt etwas anderes als bei 150 %.
   Millimeter gelten auf dem Papier.

   DER RUECKWEG IST PFLICHT. Eine Tabelle, die einmal schwebt, muss sich
   wieder einreihen lassen — sonst ist der erste Zug eine Einbahnstrasse.

   WAS DAS KOSTET, und das gehoert dazugesagt: Eine schwebende Tabelle
   wandert beim Schreiben nicht mehr mit. Wer oberhalb Zeilen einfuegt,
   schiebt sie nicht nach unten. Deshalb ist es in Word die Ausnahme —
   aber es ist seine Entscheidung, nicht meine.
   ============================================================ */

/* IM BLATT BLEIBEN.

   „Frei verschieben" heisst frei AUF DER SEITE, nicht daneben. Beim
   Pruefen ist ein Bild unter das Blatt gerutscht und war weg — die
   Griffe standen noch da, das Bild nicht mehr. Wer etwas aus dem
   Sichtbaren hinauszieht, hat es verloren und weiss nicht, wohin.

   Geklemmt wird so, dass immer mindestens ein Zentimeter im Blatt
   bleibt: Wer ueber den Rand hinaus will, darf das — aber der Griff
   muss erreichbar bleiben. */
function imBlattHalten(gegenstand, linksMm, obenMm) {
  const bogen = gegenstand.closest('.dokument') || feld;
  const massstab = (zoom || 100) / 100;
  const b = bogen.getBoundingClientRect();
  const g = gegenstand.getBoundingClientRect();
  const breiteMm = inMillimeter(g.width / massstab);
  const hoeheMm = inMillimeter(g.height / massstab);
  const bogenBreite = inMillimeter(b.width / massstab);
  const bogenHoehe = inMillimeter(b.height / massstab);
  const rest = 10;                       /* ein Zentimeter bleibt drin */
  return {
    links: Math.max(rest - breiteMm, Math.min(linksMm, bogenBreite - rest)),
    oben: Math.max(rest - hoeheMm, Math.min(obenMm, bogenHoehe - rest)),
  };
}

function istFrei(tabelle) {
  return tabelle.classList.contains('tabelle--frei');
}

function inMillimeter(px) {
  return Math.round((px / 96) * 25.4 * 10) / 10;
}

function freiMachen(tabelle) {
  if (istFrei(tabelle)) return;
  const bogen = tabelle.closest('.dokument') || feld;
  const t = tabelle.getBoundingClientRect();
  const b = bogen.getBoundingClientRect();
  const massstab = (zoom || 100) / 100;
  /* Erst die Breite festhalten, dann loesen: Eine Tabelle ueber die ganze
     Breite schrumpft sonst im Moment des Loesens auf ihren Inhalt
     zusammen und springt unter der Hand weg. */
  tabelle.style.width = inMillimeter(t.width / massstab) + 'mm';
  tabelle.style.left = inMillimeter((t.left - b.left) / massstab) + 'mm';
  tabelle.style.top = inMillimeter((t.top - b.top) / massstab) + 'mm';
  tabelle.style.marginLeft = '';
  tabelle.style.marginRight = '';
  tabelle.classList.add('tabelle--frei');
}

B.tabelleEinreihen = () => mitTabelle((zelle, zeile, tabelle) => {
  if (!istFrei(tabelle)) { melde('Diese Tabelle steht schon im Text.'); return; }
  tabelle.classList.remove('tabelle--frei');
  tabelle.style.left = '';
  tabelle.style.top = '';
  tabelle.style.width = '100%';
  geaendertMelden();
  melde('Tabelle wieder im Text — sie wandert jetzt wieder mit.');
  griffNachmessen();
});

function griffZiehenBeginnen(fall) {
  fall.preventDefault();
  if (!griffZiel) return;
  const tabelle = griffZiel;
  const knopf = fall.currentTarget;
  try { knopf.setPointerCapture(fall.pointerId); } catch (e) { /* aelter */ }

  const warFrei = istFrei(tabelle);
  const zurueck = { links: tabelle.style.left, oben: tabelle.style.top,
                    breite: tabelle.style.width };
  const davor = tabelle.previousElementSibling;

  freiMachen(tabelle);
  zieht = true;
  document.body.classList.add('zieht-tabelle');

  const massstab = (zoom || 100) / 100;
  const start = { x: fall.clientX, y: fall.clientY };
  const anfang = { links: parseFloat(tabelle.style.left) || 0,
                   oben: parseFloat(tabelle.style.top) || 0 };

  const bewegen = (e) => {
    const dx = inMillimeter((e.clientX - start.x) / massstab);
    const dy = inMillimeter((e.clientY - start.y) / massstab);
    const gehalten = imBlattHalten(tabelle, anfang.links + dx, anfang.oben + dy);
    tabelle.style.left = Math.round(gehalten.links * 10) / 10 + 'mm';
    tabelle.style.top = Math.round(gehalten.oben * 10) / 10 + 'mm';
    griffAuffrischenRoh();
  };

  const aufhoeren = () => {
    zieht = false;
    knopf.removeEventListener('pointermove', bewegen);
    knopf.removeEventListener('pointerup', loslassen);
    knopf.removeEventListener('pointercancel', abbrechen);
    document.removeEventListener('keydown', tasteAb);
    document.body.classList.remove('zieht-tabelle');
    try { knopf.releasePointerCapture(fall.pointerId); } catch (e) { /* weg */ }
  };

  const zuruecksetzen = () => {
    if (!warFrei) {
      tabelle.classList.remove('tabelle--frei');
      if (davor) davor.after(tabelle);
    }
    tabelle.style.left = zurueck.links;
    tabelle.style.top = zurueck.oben;
    tabelle.style.width = zurueck.breite;
  };

  const abbrechen = () => { aufhoeren(); zuruecksetzen(); griffNachmessen(); };

  const tasteAb = (e) => {
    if (e.key !== 'Escape') return;
    e.preventDefault();
    aufhoeren(); zuruecksetzen(); griffNachmessen();
    melde('Verschieben abgebrochen.');
  };

  const loslassen = () => {
    aufhoeren();
    geaendertMelden();
    melde(warFrei ? 'Tabelle verschoben.'
                  : 'Tabelle schwebt jetzt frei. Zurueck mit "Wieder in den Text".');
    griffNachmessen();
  };

  knopf.addEventListener('pointermove', bewegen);
  knopf.addEventListener('pointerup', loslassen);
  knopf.addEventListener('pointercancel', abbrechen);
  document.addEventListener('keydown', tasteAb);
}

/* GROESSER UND KLEINER ZIEHEN, am Eck unten rechts.

   Geaendert wird die Breite; die Hoehe ergibt sich aus dem Inhalt, wie
   bei jeder Tabelle. Wer sie schmaler zieht, bekommt mehr Zeilen je
   Zelle — das ist richtig so und kein Fehler. */
function groesseZiehenBeginnen(fall) {
  fall.preventDefault();
  if (!griffZiel) return;
  const tabelle = griffZiel;
  const knopf = fall.currentTarget;
  try { knopf.setPointerCapture(fall.pointerId); } catch (e) { /* aelter */ }

  const zurueck = tabelle.style.width;
  const massstab = (zoom || 100) / 100;
  const startX = fall.clientX;
  const anfangsBreite = tabelle.getBoundingClientRect().width / massstab;
  const bogen = (tabelle.closest('.dokument') || feld).getBoundingClientRect();
  const grenze = bogen.width / massstab;
  zieht = true;
  document.body.classList.add('zieht-tabelle');

  const bewegen = (e) => {
    const neu = anfangsBreite + (e.clientX - startX) / massstab;
    const mindestens = 20 * 96 / 25.4;          /* zwei Zentimeter */
    tabelle.style.width =
      inMillimeter(Math.max(mindestens, Math.min(neu, grenze))) + 'mm';
    griffAuffrischenRoh();
  };

  const aufhoeren = () => {
    zieht = false;
    knopf.removeEventListener('pointermove', bewegen);
    knopf.removeEventListener('pointerup', loslassen);
    knopf.removeEventListener('pointercancel', abbrechen);
    document.removeEventListener('keydown', tasteAb);
    document.body.classList.remove('zieht-tabelle');
    try { knopf.releasePointerCapture(fall.pointerId); } catch (e) { /* weg */ }
  };

  const abbrechen = () => {
    aufhoeren(); tabelle.style.width = zurueck; griffNachmessen();
  };
  const tasteAb = (e) => {
    if (e.key !== 'Escape') return;
    e.preventDefault(); abbrechen(); melde('Aufziehen abgebrochen.');
  };
  const loslassen = () => {
    aufhoeren(); geaendertMelden();
    melde('Tabellenbreite: ' + tabelle.style.width);
    griffNachmessen();
  };

  knopf.addEventListener('pointermove', bewegen);
  knopf.addEventListener('pointerup', loslassen);
  knopf.addEventListener('pointercancel', abbrechen);
  document.addEventListener('keydown', tasteAb);
}

/* Nach jedem Verschieben dasselbe: Hinter einer Tabelle muss ein Absatz
   stehen, sonst kommt man mit dem Zeiger nicht mehr dahinter — die alte
   Falle jedes Editors mit Tabellen am Textende. */
function tabelleAbschliessen(tabelle) {
  if (!tabelle.nextElementSibling) {
    const p = document.createElement('p');
    p.innerHTML = '<br>';
    tabelle.after(p);
  }
  geaendertMelden();
}

/* DER WEG OHNE MAUS.

   Einen Griff von siebzehn Pixeln zu treffen und zielgenau abzulegen ist
   Feinmotorik. Fuer ein Programm, das Menschen die Arbeit leichter machen
   soll, darf das nicht der einzige Weg sein. Diese beiden schieben die
   Tabelle um einen Block — im Menue, in der Leiste, und damit auch ueber
   die Tastatur erreichbar. */
/* ============================================================
   ZELLEN ZUSAMMENFÜHREN UND TEILEN

   Die größte Lücke aus dem Abgleich mit WPS
   (doku/wps-tabellen-und-steuerung.md). Ohne Zusammenführen lässt sich
   keine Überschrift über zwei Spalten bauen — und das braucht jeder, der
   je eine Tabelle mit einem Titel gemacht hat.

   Beides gehört zusammen und wird deshalb zusammen gebaut: Ein Befehl,
   den man nicht zurücknehmen kann, ist eine Falle. Wer zwei Zellen
   zusammenführt und es sich anders überlegt, teilt sie wieder.

   WIE DIE AUSWAHL GELESEN WIRD. In einem contenteditable gibt es keine
   „markierten Zellen" wie in einer Tabellenkalkulation — es gibt einen
   Textbereich, der über mehrere Zellen reicht. containsNode(zelle, true)
   fragt genau das ab: Liegt diese Zelle ganz oder teilweise in dem, was
   markiert ist.
   ============================================================ */

/* Die Zellen, die gerade markiert sind — oder die eine unter dem Zeiger. */
function zellenGewaehlt(tabelle) {
  const auswahl = window.getSelection();
  const alle = [...tabelle.querySelectorAll('td, th')];
  if (!auswahl || auswahl.isCollapsed || !auswahl.rangeCount) {
    const eine = zelleOderZuletzt();
    return eine && tabelle.contains(eine) ? [eine] : [];
  }
  return alle.filter((z) => {
    try { return auswahl.containsNode(z, true); } catch (e) { return false; }
  });
}

/* Wo eine Zelle im Raster wirklich sitzt.

   cellIndex zählt nur die Zellen der Zeile — bei einer Tabelle mit
   zusammengeführten Zellen ist das nicht die Spalte. Eine Zelle mit
   colSpan=2 belegt zwei Spalten, und alles dahinter rutscht. Ohne dieses
   Raster meldet „rechteckig?" bei jeder schon einmal zusammengeführten
   Tabelle Unsinn. */
function tabellenRaster(tabelle) {
  const raster = [];
  const belegt = {};
  [...tabelle.rows].forEach((zeile, z) => {
    raster[z] = raster[z] || [];
    let sp = 0;
    for (const zelle of zeile.cells) {
      while (belegt[z + ':' + sp]) sp++;
      const breit = zelle.colSpan || 1;
      const hoch = zelle.rowSpan || 1;
      for (let dz = 0; dz < hoch; dz++) {
        for (let ds = 0; ds < breit; ds++) {
          belegt[(z + dz) + ':' + (sp + ds)] = zelle;
          (raster[z + dz] = raster[z + dz] || [])[sp + ds] = zelle;
        }
      }
      sp += breit;
    }
  });
  return raster;
}

function zelleImRaster(raster, gesucht) {
  for (let z = 0; z < raster.length; z++) {
    const reihe = raster[z] || [];
    for (let sp = 0; sp < reihe.length; sp++) {
      if (reihe[sp] === gesucht) return { zeile: z, spalte: sp };
    }
  }
  return null;
}

B.zellenVerbinden = () => mitTabelle((zelle, zeile, tabelle) => {
  const gewaehlt = zellenGewaehlt(tabelle);
  if (gewaehlt.length < 2) {
    melde('Dafür müssen zwei oder mehr Zellen markiert sein — '
        + 'mit gedrückter Maustaste über sie fahren.');
    return;
  }

  const raster = tabellenRaster(tabelle);
  const stellen = gewaehlt.map((z) => zelleImRaster(raster, z)).filter(Boolean);
  const zeilen = stellen.map((s) => s.zeile);
  const spalten = stellen.map((s) => s.spalte);
  const z1 = Math.min(...zeilen), z2 = Math.max(...zeilen);
  const s1 = Math.min(...spalten), s2 = Math.max(...spalten);

  /* Nur ein Rechteck lässt sich zusammenführen. Eine Treppe ergäbe eine
     Zelle, die es in HTML nicht gibt — und in Word bekommt man dort
     dieselbe Absage. */
  const felder = (z2 - z1 + 1) * (s2 - s1 + 1);
  const eindeutig = new Set();
  for (let z = z1; z <= z2; z++) {
    for (let sp = s1; sp <= s2; sp++) {
      const da = (raster[z] || [])[sp];
      if (!da || !gewaehlt.includes(da)) {
        melde('Zusammenführen geht nur bei einem Rechteck aus Zellen.');
        return;
      }
      eindeutig.add(da);
    }
  }
  if (!felder) return;

  const erste = (raster[z1] || [])[s1];
  /* Der Inhalt aller Zellen wandert in die erste, jeder in einem eigenen
     Absatz. Ihn einfach aneinanderzuhängen ergäbe einen Wortbrei — und
     wer zusammenführt, will die Texte behalten, nicht verschmelzen. */
  const stuecke = [];
  for (const z of eindeutig) {
    const text = z.innerHTML.replace(/<br\s*\/?>/gi, '').trim();
    if (text) stuecke.push(text);
  }
  erste.innerHTML = stuecke.length ? stuecke.join('<br>') : '<br>';
  erste.colSpan = s2 - s1 + 1;
  erste.rowSpan = z2 - z1 + 1;

  for (const z of eindeutig) if (z !== erste) z.remove();

  window.getSelection().removeAllRanges();
  melde('Zellen zusammengeführt. Rückgängig mit Strg+Z, '
      + 'oder mit „Zellen teilen".');
  griffNachmessen();
});

B.zellenTeilen = () => mitTabelle((zelle, zeile, tabelle) => {
  const ziel = zellenGewaehlt(tabelle)[0] || zelle;
  if (!ziel) return;

  fenster('Zellen teilen', [
    { art: 'satz', text: 'In wie viele Teile soll diese Zelle zerfallen?' },
    { schluessel: 'spalten', name: 'Spalten', art: 'number', wert: '2' },
    { schluessel: 'zeilen', name: 'Zeilen', art: 'number', wert: '1' },
  ], (werte) => {
    const spalten = Math.max(1, Math.min(20, parseInt(werte.spalten, 10) || 1));
    const zeilen = Math.max(1, Math.min(20, parseInt(werte.zeilen, 10) || 1));
    if (spalten === 1 && zeilen === 1) { melde('Dann bleibt alles, wie es ist.'); return; }

    /* Erst die Spannweiten zurücknehmen — eine zusammengeführte Zelle zu
       teilen heißt, sie wieder aufzumachen. */
    const warBreit = ziel.colSpan || 1;
    const warHoch = ziel.rowSpan || 1;
    ziel.colSpan = 1;
    ziel.rowSpan = 1;

    const neueInZeile = Math.max(spalten, warBreit);
    const muster = () => {
      const n = document.createElement(ziel.tagName.toLowerCase());
      n.innerHTML = '<br>';
      n.style.border = ziel.style.border;
      n.style.padding = ziel.style.padding;
      n.style.background = ziel.style.background;
      return n;
    };

    /* Die zusätzlichen Spalten kommen direkt hinter die Zelle. */
    let letzte = ziel;
    for (let i = 1; i < neueInZeile; i++) {
      const n = muster();
      letzte.after(n);
      letzte = n;
    }

    /* Und die zusätzlichen Zeilen darunter — nur so breit wie das
       geteilte Stück, nicht wie die ganze Tabelle. */
    const zeileVon = ziel.parentElement;
    for (let i = 1; i < Math.max(zeilen, warHoch); i++) {
      const neueZeile = document.createElement('tr');
      for (let j = 0; j < neueInZeile; j++) neueZeile.appendChild(muster());
      zeileVon.after(neueZeile);
    }

    melde('Zelle geteilt: ' + neueInZeile + ' Spalten, '
        + Math.max(zeilen, warHoch) + ' Zeilen.');
    griffNachmessen();
  }, 'Teilen');
});

B.tabelleHoch = () => mitTabelle((zelle, zeile, tabelle) => {
  const davor = tabelle.previousElementSibling;
  if (!davor) { melde('Die Tabelle steht schon ganz oben.'); return; }
  davor.before(tabelle);
  tabelleAbschliessen(tabelle);
  melde('Tabelle eins nach oben.');
  griffNachmessen();
});

B.tabelleRunter = () => mitTabelle((zelle, zeile, tabelle) => {
  const dahinter = tabelle.nextElementSibling;
  if (!dahinter) { melde('Die Tabelle steht schon ganz unten.'); return; }
  dahinter.after(tabelle);
  tabelleAbschliessen(tabelle);
  melde('Tabelle eins nach unten.');
  griffNachmessen();
});

/* Zweimal messen, und das ist kein Luxus: Beim ersten Klick in eine
   Tabelle taucht gleichzeitig die Leiste „Tabellenwerkzeuge" auf und
   schiebt das Blatt nach unten. Wer nur einmal misst, setzt den Griff an
   die Stelle, an der die Tabelle eine Zwanzigstelsekunde vorher war. */
function griffNachmessen() {
  /* Nicht mitten im Ziehen: Die Griffe sitzen an der Tabelle, die gerade
     unterwegs ist — sie wuerden unter der Hand wegspringen. */
  if (zieht) return;
  griffAuffrischen();
  requestAnimationFrame(griffAuffrischen);
}

/* Beim Fahren ueber das Blatt: Steht der Zeiger ueber einer Tabelle,
   gehoeren ihr die Griffe. Verlaesst er das Blatt, bleiben sie an der
   Tabelle, in der die Schreibmarke steht — sonst blitzten sie bei jeder
   Mausbewegung auf und wieder weg. */
feld.addEventListener('pointerover', (e) => {
  if (zieht) return;
  const ziel = e.target && e.target.closest ? e.target.closest('table') : null;
  const neuTab = ziel && feld.contains(ziel) ? ziel : null;
  if (neuTab === tabelleUnterMaus) return;
  tabelleUnterMaus = neuTab;
  griffAuffrischen();
});

feld.addEventListener('pointerleave', () => {
  if (zieht) return;
  if (!tabelleUnterMaus) return;
  tabelleUnterMaus = null;
  griffAuffrischen();
});

document.addEventListener('selectionchange', griffNachmessen);
window.addEventListener('resize', griffNachmessen);

B.tabelleRaster = (knopf) => tabellenKlappeZeigen(knopf || wzTabelle);

B.tabelle = () => {
  auswahlMerken();
  /* Zwei Fragen nacheinander waren zwei Fenster. Eines mit zwei Zeilen ist
     dasselbe in einem Blick — und man kann die erste noch ändern, bevor man
     die zweite beantwortet hat. */
  fenster('Tabelle einfügen', [
    { schluessel: 'zeilen', name: 'Zeilen', art: 'text', wert: '3' },
    { schluessel: 'spalten', name: 'Spalten', art: 'text', wert: '3' },
  ], (werte) => {
    const zeilen = parseInt(werte.zeilen, 10);
    const spalten = parseInt(werte.spalten, 10);
    if (!zeilen || zeilen < 1 || !spalten || spalten < 1) {
      melde('Zeilen und Spalten müssen Zahlen ab 1 sein.');
      return;
    }
    auswahlZurueck();
    const zeile = '<tr>' + '<td><br></td>'.repeat(Math.min(spalten, 20)) + '</tr>';
    Dokument.einfuegen('<table>' + zeile.repeat(Math.min(zeilen, 200)) + '</table><p><br></p>');
    melde('Tabelle mit ' + Math.min(zeilen, 200) + ' Zeilen und '
        + Math.min(spalten, 20) + ' Spalten eingefügt.');
  }, 'Einfügen');
};

const zeichen = (z) => () => Dokument.einfuegen(z === ' ' ? '&nbsp;' : z);

/* ============================================================
   2b. Ein Fenster für Rückfragen

   „prompt" reicht für eine Zahl. Sobald mehrere Angaben zusammengehören —
   Titel, Verfasser, Stichwörter — braucht es einen Kasten, in dem man sie
   nebeneinander sieht und die Eingabe auch abbrechen kann.
   ============================================================ */
/* „beiAb" ist der Rückweg: Was ein Fenster schon angewandt hat, während es
   offen stand, muss beim Abbrechen zurückgenommen werden. Ohne diesen Griff
   stünde neben einer sofort wirkenden Einstellung ein Knopf „Abbrechen",
   der nichts abbricht — und das ist schlimmer als kein Knopf. */
/* „beiWechsel" ist der Blick nach draußen: Ein Fenster, das damit gebaut
   wird, wendet jede Änderung sofort an, während es offen steht. Wer eine
   Farbe wählt, sieht sie — er muss nicht auf „Übernehmen" drücken und
   hoffen.

   Das ist mehr als bequem. Ein Fenster, das erst am Ende wirkt, hat genau
   einen Griff, an dem alles hängt, und daneben liegt der graue Grund: Ein
   Klick zwei Finger breit neben dem Knopf schließt es, ohne etwas zu tun,
   und es sieht aus, als täte die Einstellung nichts. Was schon gewirkt hat,
   kann so nicht verloren gehen — und „Abbrechen" nimmt es über „beiAb"
   zurück. */
function fenster(titel, felder, beiOk, knopfName = 'Übernehmen', breit = false, beiAb = null,
                 beiWechsel = null) {
  const grund = document.createElement('div');
  grund.className = beiWechsel ? 'dialoggrund dialoggrund--schaut' : 'dialoggrund';

  const kasten = document.createElement('div');
  kasten.className = breit ? 'dialog dialog--breit' : 'dialog';
  kasten.innerHTML = '<h3 class="dialog__titel"></h3>';
  kasten.querySelector('.dialog__titel').textContent = titel;

  /* Die Felder in einen eigenen Kasten, der rollen kann.
   *
   * Vorher rollte das ganze Fenster. Bei einem langen — „Neue
   * Formatvorlage" hat elf Zeilen und eine Vorschau — standen Abbrechen
   * und Übernehmen unterhalb des Bildschirmrandes, und man musste erst an
   * allem vorbeirollen, um sie zu finden. Jetzt bleiben Überschrift und
   * Knöpfe stehen, und nur das dazwischen rollt.
   */
  const inhalt = document.createElement('div');
  inhalt.className = 'dialog__inhalt';

  const eingaben = {};
  for (const feldChen of felder) {
    if (feldChen.art === 'satz') {
      const p = document.createElement('p');
      p.className = 'dialog__satz';
      p.textContent = feldChen.text;
      inhalt.appendChild(p);
      continue;
    }
    /* Ein fertig gebauter Block. Für Seiten, die mehr sind als ein Absatz —
       die Hilfe etwa, die eine Treppe zeichnet statt einen Satz zu schreiben. */
    if (feldChen.art === 'knoten') {
      inhalt.appendChild(feldChen.knoten);
      continue;
    }
    const zeile = document.createElement('label');
    zeile.className = 'dialog__zeile';
    const name = document.createElement('span');
    name.textContent = feldChen.name;
    zeile.appendChild(name);

    let eingabe;
    if (feldChen.art === 'flaeche') {
      eingabe = document.createElement('textarea');
      eingabe.rows = feldChen.zeilen || 6;
      zeile.classList.add('dialog__zeile--hoch');
    } else if (feldChen.art === 'auswahl') {
      eingabe = document.createElement('select');
      for (const [wert, beschriftung] of feldChen.werte) {
        const o = document.createElement('option');
        o.value = wert; o.textContent = beschriftung;
        eingabe.appendChild(o);
      }
    } else {
      eingabe = document.createElement('input');
      eingabe.type = feldChen.art || 'text';
    }
    if (feldChen.wert !== undefined) eingabe.value = feldChen.wert;
    if (feldChen.schritt) eingabe.step = feldChen.schritt;
    zeile.appendChild(eingabe);
    inhalt.appendChild(zeile);
    eingaben[feldChen.schluessel] = eingabe;
  }

  const werteLesen = () => {
    const werte = {};
    for (const [name, eingabe] of Object.entries(eingaben)) werte[name] = eingabe.value;
    return werte;
  };

  if (beiWechsel) {
    /* Zweites Argument: die Eingabefelder selbst. Wer „basiert auf"
       umstellt, soll die anderen Felder mitwandern sehen — und dafür muss
       jemand hineinschreiben können, nicht nur herauslesen. */
    const gewechselt = () => beiWechsel(werteLesen(), eingaben);
    for (const eingabe of Object.values(eingaben)) {
      eingabe.addEventListener('change', gewechselt);
      eingabe.addEventListener('input', gewechselt);
    }
  }

  const knoepfe = document.createElement('div');
  knoepfe.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  const ok = document.createElement('button');
  ok.className = 'knopf knopf--haupt'; ok.textContent = knopfName;
  knoepfe.append(ab, ok);
  kasten.appendChild(inhalt);
  kasten.appendChild(knoepfe);
  grund.appendChild(kasten);
  document.body.appendChild(grund);

  const zu = () => { grund.remove(); auswahlZurueck(); };
  const zurueckNehmen = () => { if (beiAb) beiAb(); zu(); };
  ab.addEventListener('click', zurueckNehmen);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) zurueckNehmen(); });
  ok.addEventListener('click', () => {
    const werte = werteLesen();
    zu();
    beiOk(werte);
  });
  document.addEventListener('keydown', function flucht(e) {
    if (!document.body.contains(grund)) { document.removeEventListener('keydown', flucht); return; }
    /* Escape ist derselbe Weg wie „Abbrechen" — sonst bliebe stehen, was das
       Fenster schon angewandt hat, und der Rückweg wäre verbaut. */
    if (e.key === 'Escape') { e.preventDefault(); zurueckNehmen(); }
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') { e.preventDefault(); ok.click(); }
  });

  const erstes = kasten.querySelector('input,select');
  if (erstes) { erstes.focus(); if (erstes.select) erstes.select(); }
}

/* ============================================================
   2c. Was LibreOffice in seinen Leisten anbietet

   Die Liste stammt aus dem Writer. Vieles davon ist im Kern dasselbe wie
   das, was hier schon steht — hier kommt dazu, was noch fehlte.
   ============================================================ */

/* ---- Zeichen: hoch, tief, Farbe, Hervorhebung ---- */
B.hoch = () => Dokument.befehl('superscript');
B.tief = () => Dokument.befehl('subscript');

/* ------------------------------------------------------------
   Farbe wählen.

   Ein eigenes Feld statt des Farbfensters vom System: Im eigenen Fenster
   geht dieses gar nicht auf — man drückte auf „Schriftfarbe" und es passierte
   nichts. Zwölf Farben in einem Raster genügen für einen Brief, und wer eine
   ganz bestimmte braucht, tippt sie unten ein.

   Wie bei der Schriftauswahl gilt: Das Antippen nimmt den Fokus, deshalb wird
   die Markierung vorher festgehalten und danach zurückgegeben.
   ------------------------------------------------------------ */
const FARBEN = [
  ['#111417', 'Schwarz'],   ['#4C555E', 'Dunkelgrau'], ['#8B949C', 'Grau'],     ['#FFFFFF', 'Weiß'],
  ['#B5563F', 'Rot'],       ['#D08A3E', 'Orange'],     ['#C9A227', 'Gelb'],     ['#3E9C7A', 'Grün'],
  ['#2F6FB5', 'Blau'],      ['#7A5EA8', 'Violett'],    ['#A0522D', 'Braun'],    ['#1F7A5A', 'Dunkelgrün'],
];

/* ============================================================
   DAS FARBEN-FENSTER

   Seine Vorlage sind drei Bilder aus WPS: ein Fenster „Farben" mit den
   Karteireitern Standard, Benutzerdefiniert und Erweitert, rechts
   untereinander OK und Abbrechen und darunter zwei Felder „Neu" und
   „Aktuell".

   - Standard: ein Raster aus Farbtoenen in sechs Helligkeiten, darunter
     eine Reihe Graustufen.
   - Benutzerdefiniert: eine Flaeche fuer Ton und Saettigung, daneben ein
     Helligkeitsband, darunter Rot, Gruen, Blau.
   - Erweitert: derselbe Aufbau, aber als Farbkreis.

   Vorher gab es dafuer ein kleines Taefelchen mit zwoelf Punkten und
   einem Systemfarbwaehler. „Weitere Fuellfarben…" fuehrt jetzt hierher.

   beiFarbe bekommt den Hex-Wert. Wer nur eine Farbe braucht, ruft
   farbFenster(start, beiFarbe) — der Rest ist dieses Fenster.
   ============================================================ */

/* Die Toene der Standard-Karte: zwoelf Farbwinkel in sechs Helligkeiten.
   Die Winkel stammen aus SEINER Palette — nicht aus WPS. Ich habe diese
   Palette einmal eigenmaechtig getauscht; das kommt nicht wieder. */
function farbrasterBauen() {
  const reihen = [];
  const stufen = [0.88, 0.76, 0.62, 0.48, 0.34, 0.22];
  for (const helligkeit of stufen) {
    const reihe = [];
    for (const [hex] of FARBEN) {
      const [h, sa] = hexZuHsl(hex);
      reihe.push(hslZuHex(h, Math.max(0.12, sa), helligkeit));
    }
    reihen.push(reihe);
  }
  return reihen;
}

function farbFenster(start, beiFarbe) {
  let gewaehlt = start || '#2F6FB5';
  const vorher = gewaehlt;

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog farbfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Farben</h3>';

  /* Links die Karten, rechts die Knoepfe und die beiden Proben — so
     steht es auf seinen drei Bildern. */
  const koerper = document.createElement('div');
  koerper.className = 'farbfenster__koerper';
  const links = document.createElement('div');
  links.className = 'farbfenster__links';
  const rechts = document.createElement('div');
  rechts.className = 'farbfenster__rechts';

  const reiter = document.createElement('div');
  reiter.className = 'rahmentafel__reiter';
  const buehne = document.createElement('div');
  buehne.className = 'farbfenster__buehne';
  links.appendChild(reiter);
  links.appendChild(buehne);

  /* ---- rechts: OK, Abbrechen, Neu, Aktuell ---- */
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'OK';
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  rechts.appendChild(ok);
  rechts.appendChild(ab);

  const proben = document.createElement('div');
  proben.className = 'farbfenster__proben';
  const neuName = document.createElement('span');
  neuName.className = 'farbfenster__probenname';
  neuName.textContent = 'Neu';
  const neu = document.createElement('div');
  neu.className = 'farbfenster__probe';
  const altName = document.createElement('span');
  altName.className = 'farbfenster__probenname';
  altName.textContent = 'Aktuell';
  const alt = document.createElement('div');
  alt.className = 'farbfenster__probe';
  alt.style.background = vorher;
  proben.appendChild(neuName); proben.appendChild(neu);
  proben.appendChild(altName); proben.appendChild(alt);
  rechts.appendChild(proben);

  let beiWahl = null;
  function setze(hex, vonKarte) {
    gewaehlt = hex;
    neu.style.background = hex;
    if (beiWahl && !vonKarte) beiWahl(hex);
  }
  setze(gewaehlt, true);

  /* ---- Karte 1: Standard ---- */
  function karteStandard() {
    const k = document.createElement('div');
    k.className = 'farbfenster__karte';
    const gitter = document.createElement('div');
    gitter.className = 'farbfenster__raster';
    for (const reihe of farbrasterBauen()) {
      for (const ton of reihe) {
        const f = document.createElement('button');
        f.type = 'button';
        f.className = 'farbfenster__feld';
        f.style.background = ton;
        f.title = ton;
        f.addEventListener('mousedown', (e) => e.preventDefault());
        f.addEventListener('click', () => setze(ton, true));
        gitter.appendChild(f);
      }
    }
    k.appendChild(gitter);

    /* Die Graustufenreihe unten — auf seinem Bild steht sie abgesetzt. */
    const grau = document.createElement('div');
    grau.className = 'farbfenster__grau';
    for (let i = 0; i <= 11; i++) {
      const wert = Math.round(255 - (255 / 11) * i);
      const ton = '#' + [wert, wert, wert].map((z) => z.toString(16).padStart(2, '0')).join('');
      const f = document.createElement('button');
      f.type = 'button';
      f.className = 'farbfenster__feld';
      f.style.background = ton;
      f.title = ton;
      f.addEventListener('mousedown', (e) => e.preventDefault());
      f.addEventListener('click', () => setze(ton, true));
      grau.appendChild(f);
    }
    k.appendChild(grau);
    return k;
  }

  /* ---- Gemeinsames fuer Karte 2 und 3: die RGB-Felder ---- */
  function rgbFelder(beiAenderung) {
    const kiste = document.createElement('div');
    kiste.className = 'farbfenster__rgb';

    const modell = document.createElement('label');
    modell.className = 'absatzfenster__feld';
    const mt = document.createElement('span');
    mt.textContent = 'Farbmodell';
    const mw = document.createElement('select');
    mw.className = 'feld';
    for (const n of ['RGB', 'HSL']) {
      const o = document.createElement('option');
      o.value = n; o.textContent = n;
      mw.appendChild(o);
    }
    modell.appendChild(mt); modell.appendChild(mw);
    kiste.appendChild(modell);

    const eingaben = {};
    const machen = (name, schluessel, hoechst) => {
      const w = document.createElement('label');
      w.className = 'absatzfenster__feld';
      const t = document.createElement('span');
      t.textContent = name;
      const e = document.createElement('input');
      e.type = 'number'; e.className = 'feld';
      e.min = '0'; e.max = String(hoechst);
      w.appendChild(t); w.appendChild(e);
      kiste.appendChild(w);
      eingaben[schluessel] = e;
      e.addEventListener('input', () => beiAenderung(lies()));
    };

    const lies = () => {
      if (mw.value === 'RGB') {
        const z = ['rot', 'gruen', 'blau'].map((s) => Math.max(0, Math.min(255, parseInt(eingaben[s].value, 10) || 0)));
        return '#' + z.map((x) => x.toString(16).padStart(2, '0')).join('');
      }
      return hslZuHex((parseInt(eingaben.rot.value, 10) || 0) / 360,
                      (parseInt(eingaben.gruen.value, 10) || 0) / 100,
                      (parseInt(eingaben.blau.value, 10) || 0) / 100);
    };

    machen('Rot', 'rot', 255);
    machen('Grün', 'gruen', 255);
    machen('Blau', 'blau', 255);

    const schreib = (hex) => {
      if (mw.value === 'RGB') {
        eingaben.rot.value = parseInt(hex.slice(1, 3), 16);
        eingaben.gruen.value = parseInt(hex.slice(3, 5), 16);
        eingaben.blau.value = parseInt(hex.slice(5, 7), 16);
      } else {
        const [h, sa, l] = hexZuHsl(hex);
        eingaben.rot.value = Math.round(h * 360);
        eingaben.gruen.value = Math.round(sa * 100);
        eingaben.blau.value = Math.round(l * 100);
      }
    };

    mw.addEventListener('change', () => {
      const namen = mw.value === 'RGB' ? ['Rot', 'Grün', 'Blau'] : ['Farbton', 'Sättigung', 'Helligkeit'];
      [...kiste.querySelectorAll('.absatzfenster__feld')].slice(1).forEach((w, i) => {
        w.firstChild.textContent = namen[i];
      });
      schreib(gewaehlt);
    });

    kiste.schreib = schreib;
    return kiste;
  }

  /* ---- Karte 2: Benutzerdefiniert ---- */
  function karteEigen() {
    const k = document.createElement('div');
    k.className = 'farbfenster__karte';

    const oben = document.createElement('div');
    oben.className = 'farbfenster__mischer';
    const flaeche = document.createElement('div');
    flaeche.className = 'farbfenster__flaeche';
    const punkt = document.createElement('i');
    punkt.className = 'farbfenster__punkt';
    flaeche.appendChild(punkt);
    const band = document.createElement('div');
    band.className = 'farbfenster__band';
    const griff = document.createElement('i');
    griff.className = 'farbfenster__griff';
    band.appendChild(griff);
    oben.appendChild(flaeche); oben.appendChild(band);
    k.appendChild(oben);

    let [h, sa, l] = hexZuHsl(gewaehlt);
    const zeichne = () => {
      flaeche.style.background =
        'linear-gradient(to top, #000, transparent), '
        + 'linear-gradient(to right, #fff, hsl(' + (h * 360) + ',100%,50%))';
      punkt.style.left = (sa * 100) + '%';
      punkt.style.top = ((1 - l) * 100) + '%';
      griff.style.top = (h * 100) + '%';
      band.style.background = 'linear-gradient(to bottom,'
        + [0, 1, 2, 3, 4, 5, 6].map((i) => 'hsl(' + (i * 60) + ',100%,50%)').join(',') + ')';
    };
    zeichne();

    const felder = rgbFelder((hex) => { setze(hex, true); [h, sa, l] = hexZuHsl(hex); zeichne(); });
    felder.schreib(gewaehlt);
    k.appendChild(felder);

    const ausFlaeche = (e) => {
      const r = flaeche.getBoundingClientRect();
      sa = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
      l = Math.max(0, Math.min(1, 1 - (e.clientY - r.top) / r.height));
      const hex = hslZuHex(h, sa, l);
      setze(hex, true); felder.schreib(hex); zeichne();
    };
    const ausBand = (e) => {
      const r = band.getBoundingClientRect();
      h = Math.max(0, Math.min(0.999, (e.clientY - r.top) / r.height));
      const hex = hslZuHex(h, sa, l);
      setze(hex, true); felder.schreib(hex); zeichne();
    };
    for (const [el, tun] of [[flaeche, ausFlaeche], [band, ausBand]]) {
      el.addEventListener('mousedown', (e) => {
        e.preventDefault(); tun(e);
        const zieh = (z) => tun(z);
        const los = () => {
          window.removeEventListener('mousemove', zieh);
          window.removeEventListener('mouseup', los);
        };
        window.addEventListener('mousemove', zieh);
        window.addEventListener('mouseup', los);
      });
    }
    return k;
  }

  /* ---- Karte 3: Erweitert ---- */
  function karteKreis() {
    const k = document.createElement('div');
    k.className = 'farbfenster__karte';

    const kreisKiste = document.createElement('div');
    kreisKiste.className = 'farbfenster__kreiskiste';
    const kreis = document.createElement('div');
    kreis.className = 'farbfenster__kreis';
    const marke = document.createElement('i');
    marke.className = 'farbfenster__kreismarke';
    kreis.appendChild(marke);
    kreisKiste.appendChild(kreis);
    k.appendChild(kreisKiste);

    let [h, sa, l] = hexZuHsl(gewaehlt);
    const zeichne = () => {
      const winkel = h * 360;
      marke.style.left = (50 + 42 * Math.cos((winkel - 90) * Math.PI / 180)) + '%';
      marke.style.top = (50 + 42 * Math.sin((winkel - 90) * Math.PI / 180)) + '%';
    };
    zeichne();

    const felder = rgbFelder((hex) => { setze(hex, true); [h, sa, l] = hexZuHsl(hex); zeichne(); });
    felder.schreib(gewaehlt);
    k.appendChild(felder);

    kreis.addEventListener('mousedown', (e) => {
      const r = kreis.getBoundingClientRect();
      const x = e.clientX - r.left - r.width / 2;
      const y = e.clientY - r.top - r.height / 2;
      h = ((Math.atan2(y, x) * 180 / Math.PI + 90 + 360) % 360) / 360;
      const hex = hslZuHex(h, sa || 0.7, l || 0.5);
      setze(hex, true); felder.schreib(hex); zeichne();
    });
    return k;
  }

  const KARTEN = [
    ['standard', 'Standard', karteStandard],
    ['eigen', 'Benutzerdefiniert', karteEigen],
    ['kreis', 'Erweitert', karteKreis],
  ];
  const zeige = (kuerzel) => {
    const eintrag = KARTEN.find(([k]) => k === kuerzel) || KARTEN[0];
    buehne.textContent = '';
    buehne.appendChild(eintrag[2]());
    [...reiter.children].forEach((c) => {
      c.classList.toggle('rahmentafel__reiter--an', c.dataset.karte === eintrag[0]);
    });
  };
  for (const [kuerzel, name] of KARTEN) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rahmentafel__reiter-knopf';
    k.dataset.karte = kuerzel;
    k.textContent = name;
    k.addEventListener('click', () => zeige(kuerzel));
    reiter.appendChild(k);
  }

  koerper.appendChild(links);
  koerper.appendChild(rechts);
  kasten.appendChild(koerper);

  ab.addEventListener('click', () => grund.remove());
  ok.addEventListener('click', () => {
    grund.remove();
    if (beiFarbe) beiFarbe(gewaehlt);
  });

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
  zeige('standard');
}

function farbeWaehlen(befehl, titel, knopf) {
  auswahlMerken();

  const alt = document.querySelector('.farbtafel');
  if (alt) { alt.remove(); return; }

  const tafel = document.createElement('div');
  tafel.className = 'farbtafel';

  const kopf = document.createElement('div');
  kopf.className = 'farbtafel__titel';
  kopf.textContent = titel;
  tafel.appendChild(kopf);

  const gitter = document.createElement('div');
  gitter.className = 'farbgitter';
  for (const [wert, name] of FARBEN) {
    const punkt = document.createElement('button');
    punkt.type = 'button';
    punkt.className = 'farbpunkt';
    punkt.style.background = wert;
    punkt.title = name;
    punkt.addEventListener('mousedown', (e) => e.preventDefault());
    punkt.addEventListener('click', () => {
      tafel.remove();
      auswahlZurueck();
      Dokument.befehl(befehl, wert);
      melde(titel + ': ' + name);
    });
    gitter.appendChild(punkt);
  }
  tafel.appendChild(gitter);

  /* „Keine" heißt bei der Hervorhebung: durchsichtig. Ohne diesen Knopf
     bekäme man eine einmal gesetzte Markierung nicht wieder weg. */
  if (befehl === 'hiliteColor') {
    const weg = document.createElement('button');
    weg.type = 'button';
    weg.className = 'knopf knopf--klein farbtafel__weg';
    weg.textContent = 'Keine Hervorhebung';
    weg.addEventListener('mousedown', (e) => e.preventDefault());
    weg.addEventListener('click', () => {
      tafel.remove();
      auswahlZurueck();
      Dokument.befehl('hiliteColor', 'transparent');
      melde('Hervorhebung entfernt.');
    });
    tafel.appendChild(weg);
  }

  /* Der Systemfarbwaehler ist weg: Sein Bild zeigt an dieser Stelle ein
     eigenes Fenster mit drei Karteireitern. */
  const eigene = document.createElement('button');
  eigene.type = 'button';
  eigene.className = 'knopf knopf--klein farbtafel__weg';
  eigene.textContent = 'Weitere Farben…';
  eigene.addEventListener('mousedown', (e) => e.preventDefault());
  eigene.addEventListener('click', () => {
    tafel.remove();
    farbFenster('#2F6FB5', (hex) => {
      auswahlZurueck();
      Dokument.befehl(befehl, hex);
      melde(titel + ' gesetzt.');
    });
  });
  tafel.appendChild(eigene);

  /* Unter den Knopf, der sie geöffnet hat — sonst stünde sie am Bildrand
     und man suchte den Zusammenhang. */
  const bezug = (knopf || document.body).getBoundingClientRect();
  tafel.style.left = Math.max(8, Math.min(window.innerWidth - 230, bezug.left)) + 'px';
  tafel.style.top = (bezug.bottom + 4) + 'px';
  document.body.appendChild(tafel);

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(e) {
      if (!tafel.contains(e.target)) { tafel.remove(); document.removeEventListener('mousedown', zu); }
    });
  }, 0);
}

B.schriftfarbe = (e) => farbeWaehlen('foreColor', 'Schriftfarbe',
                                     e && e.currentTarget ? e.currentTarget : null);
B.hervorheben  = (e) => farbeWaehlen('hiliteColor', 'Hervorhebungsfarbe',
                                     e && e.currentTarget ? e.currentTarget : null);

/* ---- Der geteilte Knopf: Zeichen wirkt, Pfeil waehlt ----

   Er hat zu „Hervorheben" geschrieben: „Icon ist ohne Funktion." Das
   stimmte fast. Der Knopf oeffnete eine Farbtafel — wer einmal Gelb
   gewaehlt hatte und danach die naechste Stelle faerben wollte, musste
   jedes Mal wieder durch die Tafel. In WPS faerbt ein Klick auf den
   Marker sofort mit der zuletzt gewaehlten Farbe, und nur der Pfeil
   daneben zeigt die Tafel. Genau das ist der Unterschied zwischen einem
   Werkzeug und einem Menue.

   Zu „Schriftfarbe" schrieb er: „die Funktion aus dem Bild ist nicht
   vorhanden" — dasselbe: das A mit dem Farbbalken darunter faerbt, der
   Pfeil waehlt. */
let letzteMarkerfarbe = Speicher.lies('markerfarbe', '#F4E7B0');   /* Gelb aus FARBEN, aufgehellt */
let letzteSchriftfarbe = Speicher.lies('schriftfarbeZuletzt', '#B5563F');   /* Rot aus FARBEN */

function farbeAnwenden(befehl, farbe) {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) {
    melde(befehl === 'hiliteColor'
      ? 'Erst den Text markieren, der hervorgehoben werden soll.'
      : 'Erst den Text markieren, der die Farbe bekommen soll.');
    return;
  }
  document.execCommand('styleWithCSS', false, true);
  document.execCommand(befehl, false, farbe);
  geaendertMelden();
}

B.hervorhebenJetzt = () => {
  farbeAnwenden('hiliteColor', letzteMarkerfarbe);
  melde('Hervorgehoben.');
};

B.schriftfarbeJetzt = () => {
  farbeAnwenden('foreColor', letzteSchriftfarbe);
  melde('Schriftfarbe gesetzt.');
};

/* Die Tafel merkt sich, was gewaehlt wurde — sonst waere der Klick auf
   das Zeichen daneben wieder ein Ratespiel. */
function farbeKlappe(knopf, titel, befehl, merken) {
  auswahlMerken();
  designTafelZeigen(knopf, titel, (tafel) => {
    tafel.classList.add('designtafel--breit', 'farbtafel');

    const nimm = (hex, name) => {
      merken(hex);
      designTafelWeg();
      auswahlZurueck();
      farbeAnwenden(befehl, hex);
      melde(titel + ': ' + (name || hex.toUpperCase()) + '.');
    };

    /* SEINE ZWOELF FARBEN, nicht die aus WPS.

       Ich hatte hier die WPS-Standardfarben eingesetzt — #FF0000,
       #FFFF00, reines Blau. Das sind Signalfarben. FARBEN steht seit je
       in dieser Datei und ist etwas anderes: zwoelf gedaempfte Toene mit
       deutschen Namen, ausgesucht fuer ein Programm, in dem Lesen leicht
       sein soll. Ein #FF0000 auf Papier sticht, und genau das will hier
       niemand.

       Er hat es so gesagt: „danke dass du meine Farbpaletten killst." */
    const reihe = document.createElement('div');
    reihe.className = 'farbtafel__reihe farbtafel__reihe--zwoelf';
    for (const [hex, name] of FARBEN) {
      const feld = farbfeld(hex, () => nimm(hex, name));
      feld.title = name;
      feld.setAttribute('aria-label', titel + ': ' + name);
      reihe.appendChild(feld);
    }
    tafel.appendChild(reihe);

    /* Fuer den Marker dieselben Farben, nur aufgehellt: Ein Text unter
       dunkelblauem Marker ist nicht mehr zu lesen. Aufgehellt statt
       ausgetauscht — so bleibt es seine Palette. */
    if (befehl === 'hiliteColor') {
      const hell = document.createElement('div');
      hell.className = 'farbtafel__reihe farbtafel__reihe--zwoelf';
      for (const [hex, name] of FARBEN) {
        const [h, sa, l] = hexZuHsl(hex);
        const licht = hslZuHex(h, Math.min(0.62, sa), Math.max(l, 0.84));
        const feld = farbfeld(licht, () => nimm(licht, name + ', hell'));
        feld.title = name + ', hell';
        feld.setAttribute('aria-label', titel + ': ' + name + ', hell');
        hell.appendChild(feld);
      }
      tafel.insertBefore(hell, reihe);
    }

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    const weg = document.createElement('button');
    weg.type = 'button';
    weg.className = 'designtafel__zeile richtungszeile';
    weg.appendChild(symbol('radierer'));
    const w = document.createElement('span');
    w.textContent = befehl === 'hiliteColor' ? 'Hervorhebung entfernen' : 'Automatisch';
    weg.appendChild(w);
    weg.addEventListener('mousedown', (e) => e.preventDefault());
    weg.addEventListener('click', () => {
      designTafelWeg();
      auswahlZurueck();
      farbeAnwenden(befehl, befehl === 'hiliteColor' ? 'transparent' : '#111417');
      melde('Zurückgesetzt.');
    });
    tafel.appendChild(weg);
  });
}

B.hervorhebenKlappe = (knopf) => farbeKlappe(knopf, 'Hervorheben', 'hiliteColor',
  (hex) => { letzteMarkerfarbe = hex; Speicher.schreib('markerfarbe', hex); });

B.schriftfarbeKlappe = (knopf) => farbeKlappe(knopf, 'Schriftfarbe', 'foreColor',
  (hex) => { letzteSchriftfarbe = hex; Speicher.schreib('schriftfarbeZuletzt', hex); });

/* ---- Format übertragen (der Pinsel) ---- */
let pinsel = null;

B.formatUebertragen = () => {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) { melde('Erst eine Stelle antippen, deren Format übertragen werden soll.'); return; }

  if (pinsel) { pinsel = null; melde('Pinsel abgelegt.'); werkzeugeAuffrischen(); return; }

  let knoten = auswahl.anchorNode;
  if (knoten && knoten.nodeType === Node.TEXT_NODE) knoten = knoten.parentElement;
  if (!knoten || !feld.contains(knoten)) { melde('Das geht nur im Text.'); return; }

  const wie = getComputedStyle(knoten);
  pinsel = {
    schrift: wie.fontFamily.split(',')[0].replace(/["']/g, ''),
    groesse: Math.round(parseFloat(wie.fontSize) * 72 / 96) + 'pt',
    fett: parseInt(wie.fontWeight, 10) >= 600,
    kursiv: wie.fontStyle === 'italic',
    unter: wie.textDecorationLine.includes('underline'),
    farbe: wie.color,
  };
  melde('Format aufgenommen. Jetzt die Stelle markieren, die es bekommen soll.');
  werkzeugeAuffrischen();
};

/* Der zweite Halt des Pinsels: auf das, was danach markiert wird. */
function pinselAnwenden() {
  if (!pinsel) return;
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) return;

  Dokument.befehl('removeFormat');
  Dokument.befehl('fontName', pinsel.schrift);
  schriftgroesse(parseFloat(pinsel.groesse));
  if (pinsel.fett)   Dokument.befehl('bold');
  if (pinsel.kursiv) Dokument.befehl('italic');
  if (pinsel.unter)  Dokument.befehl('underline');
  Dokument.befehl('foreColor', pinsel.farbe);

  pinsel = null;
  melde('Format übertragen.');
  werkzeugeAuffrischen();
}

/* ---- Absatz: Zeilenabstand, Abstand davor und danach ---- */
function aufAbsaetze(tun) {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return;
  const bereich = auswahl.getRangeAt(0);

  const betroffen = [...feld.children].filter((el) => bereich.intersectsNode(el));
  for (const el of (betroffen.length ? betroffen : [feld.firstElementChild].filter(Boolean))) tun(el);
  geaendertMelden();
}

const zeilenabstand = (wert) => () => aufAbsaetze((el) => { el.style.lineHeight = wert; });

/* „Icon ist als solches nicht erkennbar, Funktion ist nach WPS
   auszubauen."

   Das Zeichen war ein Paar senkrechter Balken — das heisst nichts.
   Jetzt Zeilen mit einem Doppelpfeil daneben, wie ueberall.

   Und dahinter lag nur ein Fenster fuer den Abstand ZWISCHEN Absaetzen.
   In WPS haengt am Zeilenabstand eine Klappe mit den Massen, die man
   wirklich nimmt — 1, 1,15, 1,5, 2 —, und darunter erst das Feine. Wer
   „anderthalbzeilig" braucht, soll einmal klicken. */
/* Nach seinem WPS-Bild: Zahlen, kein „Anderthalbfach", kein 1,15. Ein
   Haken beim geltenden Wert, rechts die Kuerzel. Hier standen Woerter
   und daneben gezeichnete Probezeilen — beides steht so in keiner
   Vorlage. */
const ZEILENABSTAENDE = [
  ['1',   '1,0', 1,   'Strg+1'],
  ['1.5', '1,5', 1.5, ''],
  ['2',   '2,0', 2,   'Strg+2'],
  ['2.5', '2,5', 2.5, ''],
  ['3',   '3,0', 3,   ''],
];

/* Welcher Abstand gilt gerade? Fuer den Haken. Ohne eigene Angabe steht
   der Absatz auf dem Wert des Blattes; der zaehlt als 1,0. */
function zeilenabstandJetzt() {
  const ziele = absaetzeInAuswahl();
  if (!ziele.length) return null;
  const eigen = ziele[0].style.lineHeight;
  if (!eigen) return 1;
  const zahl = parseFloat(eigen);
  return Number.isFinite(zahl) ? zahl : null;
}

function zeilenabstandSetzen(wert, name) {
  const ziele = absaetzeInAuswahl();
  if (!ziele.length) { melde('Dafür muss der Zeiger in einem Absatz stehen.'); return; }
  for (const a of ziele) a.style.lineHeight = String(wert);
  geaendertMelden();
  melde('Zeilenabstand: ' + (name || wert) + '.');
}

B.zeilenabstandKlappe = (knopf) => {
  designTafelZeigen(knopf, 'Zeilenabstand', (tafel) => {
    tafel.classList.add('designtafel--breit');
    const jetzt = zeilenabstandJetzt();
    for (const [, name, wert, kuerzel] of ZEILENABSTAENDE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile abstandzeile';

      /* Der Haken steht links und haelt seinen Platz auch dann frei,
         wenn er leer ist — sonst ruecken die Zahlen gegeneinander. */
      const haken = document.createElement('span');
      haken.className = 'designtafel__haken';
      haken.textContent = (jetzt !== null && Math.abs(jetzt - wert) < 0.001) ? '✓' : '';
      k.appendChild(haken);

      const w = document.createElement('span');
      w.className = 'designtafel__wort';
      w.textContent = name;
      k.appendChild(w);

      if (kuerzel) {
        const t = document.createElement('span');
        t.className = 'designtafel__taste';
        t.textContent = kuerzel;
        k.appendChild(t);
      }

      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        zeilenabstandSetzen(wert, name);
      });
      tafel.appendChild(k);
    }

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    /* In WPS heisst der letzte Punkt „Mehr…" und fuehrt zu den Abstaenden
       ueber und unter dem Absatz. */
    const mehr = document.createElement('button');
    mehr.type = 'button';
    mehr.className = 'designtafel__zeile abstandzeile';
    const leer = document.createElement('span');
    leer.className = 'designtafel__haken';
    mehr.appendChild(leer);
    const w = document.createElement('span');
    w.className = 'designtafel__wort';
    w.textContent = 'Mehr…';
    mehr.appendChild(w);
    mehr.addEventListener('mousedown', (e) => e.preventDefault());
    mehr.addEventListener('click', () => { designTafelWeg(); B.absatzabstand(); });
    tafel.appendChild(mehr);
  });
};

/* ============================================================
   DAS ABSATZ-FENSTER

   Seine Vorlage ist der WPS-Dialog „Absatz": zwei Karteireiter,
   Allgemein / Einzug / Abstand, darunter eine Vorschau, unten links
   „Tabstopps…".

   Es gab dafuer ZWEI Fenster — „Einzug" mit drei Feldern und
   „Absatzabstand" mit zweien. Er hat das zweimal gemeldet: „an einem
   Ort gebuendelt", „das Dialogfenster doppelt gemoppelt". Beide Namen
   fuehren jetzt hierher.

   Masse: Einzug in Millimetern, Abstand in Millimetern. Sein Bild zeigt
   „char" und „line", weil in WPS das Dokumentraster laeuft; Millimeter
   sind hier ehrlicher, weil das Blatt in Millimetern gerechnet wird.
   ============================================================ */

const ABSATZ_AUSRICHTUNGEN = [
  ['left', 'Links'], ['center', 'Zentriert'],
  ['right', 'Rechts'], ['justify', 'Blocksatz'],
];

const ABSATZ_EBENEN = [
  ['', 'Textkörper'], ['1', 'Ebene 1'], ['2', 'Ebene 2'], ['3', 'Ebene 3'],
  ['4', 'Ebene 4'], ['5', 'Ebene 5'], ['6', 'Ebene 6'],
];

const ABSATZ_SONDER = [
  ['keine', '(Keine)'], ['erste', 'Erste Zeile'], ['haengend', 'Hängend'],
];

const ABSATZ_ZEILEN = [
  ['1', 'Einfach'], ['1.5', '1,5 Zeilen'], ['2', 'Doppelt'],
  ['mehrfach', 'Mehrfach'],
];

/* Was steht gerade am Absatz? Ohne diese Abfrage oeffnete das Fenster
   immer mit Nullen, und wer nur den Abstand aendern wollte, setzte den
   Einzug ungewollt zurueck. */
function absatzStandLesen() {
  const el = absaetzeInAuswahl()[0];
  const mm = (wert) => {
    const zahl = parseFloat(wert);
    if (!Number.isFinite(zahl)) return 0;
    if (String(wert).endsWith('mm')) return zahl;
    /* Der Rechner gibt Pixel zurueck; CM ist die Zahl der Bildpunkte je
       Zentimeter, die das Programm ohnehin fuer das Lineal fuehrt. */
    return Math.round((zahl / CM) * 10 * 10) / 10;
  };
  if (!el) {
    return { ausrichtung: 'left', ebene: '', richtung: 'ltr', links: 0, rechts: 0,
             sonder: 'keine', sonderVon: 0, oben: 0, unten: 0,
             zeilen: '1', zeilenVon: 1, umbruchVor: false, zusammen: false,
             ohneTrennung: false, kontrolle: true, mitNaechstem: false,
             mittenImWort: false, textausrichtung: 'auto' };
  }
  const s = el.style;
  const einzug = mm(s.textIndent);
  return {
    ausrichtung: s.textAlign || 'left',
    ebene: el.dataset.ebene || '',
    richtung: el.dir === 'rtl' ? 'rtl' : 'ltr',
    links: mm(s.marginLeft),
    rechts: mm(s.marginRight),
    sonder: einzug > 0 ? 'erste' : (einzug < 0 ? 'haengend' : 'keine'),
    sonderVon: Math.abs(einzug),
    oben: mm(s.marginTop),
    unten: mm(s.marginBottom),
    zeilen: ['1', '1.5', '2'].includes(String(parseFloat(s.lineHeight)))
            ? String(parseFloat(s.lineHeight))
            : (s.lineHeight ? 'mehrfach' : '1'),
    zeilenVon: parseFloat(s.lineHeight) || 1,
    umbruchVor: s.breakBefore === 'page' || s.pageBreakBefore === 'always',
    zusammen: s.breakInside === 'avoid',
    ohneTrennung: el.dataset.trennung === 'aus',
    kontrolle: el.dataset.kontrolle !== 'aus',
    mitNaechstem: el.dataset.mitnaechstem === 'ja',
    mittenImWort: el.dataset.mittenimwort === 'ja',
    textausrichtung: el.dataset.textausrichtung || 'auto',
  };
}

B.absatz = (karteZuerst) => {
  const stand = absatzStandLesen();

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog dialog--breit absatzfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Absatz</h3>';

  const reiter = document.createElement('div');
  reiter.className = 'rahmentafel__reiter';
  const buehne = document.createElement('div');
  buehne.className = 'rahmentafel__buehne absatzfenster__buehne';

  /* ---- kleine Bausteine, damit die Karten kurz bleiben ---- */
  function block(titel) {
    const b = document.createElement('fieldset');
    b.className = 'absatzfenster__block';
    b.innerHTML = '<legend>' + titel + '</legend>';
    return b;
  }
  function zeile() {
    const z = document.createElement('div');
    z.className = 'absatzfenster__zeile';
    return z;
  }
  function beschriftet(name, el) {
    const w = document.createElement('label');
    w.className = 'absatzfenster__feld';
    const t = document.createElement('span');
    t.textContent = name;
    w.appendChild(t);
    w.appendChild(el);
    return w;
  }
  function waehler(liste, wert) {
    const s = document.createElement('select');
    s.className = 'feld feld--waehler';
    for (const [k, name] of liste) {
      const o = document.createElement('option');
      o.value = k; o.textContent = name;
      if (k === String(wert)) o.selected = true;
      s.appendChild(o);
    }
    return s;
  }
  function zahlfeld(wert, schritt, einheit) {
    const h = document.createElement('span');
    h.className = 'absatzfenster__zahl';
    const e = document.createElement('input');
    e.type = 'number'; e.className = 'feld';
    e.value = String(wert); e.step = String(schritt || 1);
    h.appendChild(e);
    if (einheit) {
      const m = document.createElement('span');
      m.className = 'absatzfenster__einheit';
      m.textContent = einheit;
      h.appendChild(m);
    }
    h.eingabe = e;
    return h;
  }
  function haken(name, an) {
    const w = document.createElement('label');
    w.className = 'absatzfenster__haken';
    const e = document.createElement('input');
    e.type = 'checkbox'; e.checked = !!an;
    w.appendChild(e);
    const t = document.createElement('span');
    t.textContent = name;
    w.appendChild(t);
    w.eingabe = e;
    return w;
  }

  /* ---- Die Vorschau ----
     Wie in WPS: der Absatz zwischen zwei grauen Nachbarn, mit echtem
     Text. Hier standen erst nur Striche — Kay: "zudem hast du die
     Vorschau nur als Attrappe gebaut mit Strichen." Sie ist jetzt keine
     Zeichnung, sondern derselbe Absatz: Die Vorschau bekommt genau die
     Stile, die OK setzen wuerde. Was man sieht, ist, was passiert. */
  const BEISPIELSATZ = 'Dieser Absatz zeigt, wie der Text mit den '
    + 'eingestellten Maßen aussieht. Einzug, Ausrichtung und Abstand '
    + 'wirken hier genauso wie später im Blatt. ';

  const schau = document.createElement('div');
  schau.className = 'absatzprobe';
  let schauSatz = null;
  function schauBauen() {
    schau.textContent = '';
    for (const wo of ['vor', 'satz', 'nach']) {
      const p = document.createElement('p');
      p.className = 'absatzprobe__satz absatzprobe__satz--' + wo;
      if (wo === 'satz') {
        p.textContent = BEISPIELSATZ + BEISPIELSATZ;
        schauSatz = p;
      } else {
        p.textContent = (wo === 'vor' ? 'Vorhergehender' : 'Folgender')
                      + ' Absatz. ' + (wo === 'vor' ? 'Vorhergehender' : 'Folgender')
                      + ' Absatz.';
      }
      schau.appendChild(p);
    }
  }
  schauBauen();

  let felder = null;
  /* Dieselbe Rechnung wie beim Uebernehmen — einmal geschrieben, zweimal
     benutzt. Sonst zeigte die Vorschau etwas anderes, als OK tut. */
  function stileAusFeldern(ziel, massstab) {
    if (!felder) return;
    const m = massstab || 1;
    const mm = (wert) => (wert * m) + 'mm';
    ziel.style.textAlign = felder.ausrichtung.value;
    ziel.style.marginLeft = mm(parseFloat(felder.links.eingabe.value) || 0);
    ziel.style.marginRight = mm(parseFloat(felder.rechts.eingabe.value) || 0);
    const von = parseFloat(felder.sonderVon.eingabe.value) || 0;
    ziel.style.textIndent = felder.sonder.value === 'erste' ? mm(von)
                          : felder.sonder.value === 'haengend' ? mm(-von) : '';
    ziel.style.marginTop = mm(parseFloat(felder.oben.eingabe.value) || 0);
    ziel.style.marginBottom = mm(parseFloat(felder.unten.eingabe.value) || 0);
    ziel.style.lineHeight = felder.zeilen.value === 'mehrfach'
      ? String(parseFloat(felder.zeilenVon.eingabe.value) || 1)
      : felder.zeilen.value;
    const rtl = felder.richtung.querySelector('input[value="rtl"]');
    ziel.dir = (rtl && rtl.checked) ? 'rtl' : '';
  }
  function schauAuffrischen() {
    if (schauSatz) stileAusFeldern(schauSatz, 1);
  }

  /* ---- Karte 1: Einzüge und Abstände ---- */
  function karteMasse() {
    const k = document.createElement('div');
    k.className = 'rahmentafel__karte absatzfenster__karte';

    const allg = block('Allgemein');
    const z1 = zeile();
    const ausrichtung = waehler(ABSATZ_AUSRICHTUNGEN, stand.ausrichtung);
    const ebene = waehler(ABSATZ_EBENEN, stand.ebene);
    z1.appendChild(beschriftet('Ausrichtung', ausrichtung));
    z1.appendChild(beschriftet('Gliederungsebene', ebene));
    allg.appendChild(z1);

    const z2 = zeile();
    const richtung = document.createElement('div');
    richtung.className = 'absatzfenster__wahlpaar';
    for (const [wert, name] of [['rtl', 'Rechts nach links'], ['ltr', 'Links nach rechts']]) {
      const w = document.createElement('label');
      w.className = 'absatzfenster__haken';
      const e = document.createElement('input');
      e.type = 'radio'; e.name = 'absatz-richtung'; e.value = wert;
      e.checked = stand.richtung === wert;
      w.appendChild(e);
      const t = document.createElement('span');
      t.textContent = name;
      w.appendChild(t);
      richtung.appendChild(w);
    }
    z2.appendChild(beschriftet('Richtung', richtung));
    allg.appendChild(z2);
    k.appendChild(allg);

    const ein = block('Einzug');
    const z3 = zeile();
    const links = zahlfeld(stand.links, 1, 'mm');
    const rechts = zahlfeld(stand.rechts, 1, 'mm');
    z3.appendChild(beschriftet('Vor Text', links));
    z3.appendChild(beschriftet('Nach Text', rechts));
    ein.appendChild(z3);

    const z4 = zeile();
    const sonder = waehler(ABSATZ_SONDER, stand.sonder);
    const sonderVon = zahlfeld(stand.sonderVon, 1, 'mm');
    z4.appendChild(beschriftet('Sondereinzug', sonder));
    z4.appendChild(beschriftet('Von', sonderVon));
    ein.appendChild(z4);
    k.appendChild(ein);

    const ab = block('Abstand');
    const z5 = zeile();
    const oben = zahlfeld(stand.oben, 0.5, 'mm');
    const unten = zahlfeld(stand.unten, 0.5, 'mm');
    z5.appendChild(beschriftet('Vor', oben));
    z5.appendChild(beschriftet('Nach', unten));
    ab.appendChild(z5);

    const z6 = zeile();
    const zeilen = waehler(ABSATZ_ZEILEN, stand.zeilen);
    const zeilenVon = zahlfeld(stand.zeilenVon, 0.05, '');
    z6.appendChild(beschriftet('Zeilenabstand', zeilen));
    z6.appendChild(beschriftet('Von', zeilenVon));
    ab.appendChild(z6);
    k.appendChild(ab);

    felder = { ausrichtung, ebene, links, rechts, sonder, sonderVon,
               oben, unten, zeilen, zeilenVon, richtung };

    /* „Von" gilt nur bei Mehrfach — sonst steht dort eine Zahl, die
       nichts bewirkt, und man sucht den Fehler bei sich. */
    const vonPruefen = () => {
      const an = zeilen.value === 'mehrfach';
      zeilenVon.eingabe.disabled = !an;
      zeilenVon.classList.toggle('absatzfenster__zahl--aus', !an);
      const anS = sonder.value !== 'keine';
      sonderVon.eingabe.disabled = !anS;
      sonderVon.classList.toggle('absatzfenster__zahl--aus', !anS);
    };
    vonPruefen();

    for (const el of k.querySelectorAll('input, select')) {
      el.addEventListener('input', () => { vonPruefen(); schauAuffrischen(); });
      el.addEventListener('change', () => { vonPruefen(); schauAuffrischen(); });
    }
    requestAnimationFrame(schauAuffrischen);
    return k;
  }

  /* ---- Karte 2: Zeilen- und Seitenumbruch ----
     Nach seinem zweiten Bild: Paginierung mit vier Haken, darunter der
     Zeilenumbruch und die Textausrichtung.

     WAS HIER FEHLT UND WARUM: In WPS stehen unter „Zeilenumbruch" und
     „Zeichenabstand" fuenf Punkte zu asiatischen Zeichen — Regeln fuer
     Anfangs- und Endzeichen, haengende Interpunktion, Abstand zwischen
     asiatischem und westlichem Text. „sorry ich bin ein deutscher und
     kein schinese." Sie sind weg. */
  let umbruchFelder = null;
  function karteUmbruch() {
    const k = document.createElement('div');
    k.className = 'rahmentafel__karte absatzfenster__karte';

    const pag = block('Paginierung');
    const z1 = zeile();
    const kontrolle = haken('Absatzkontrolle', stand.kontrolle);
    const mitNaechstem = haken('Nicht vom nächsten Absatz trennen', stand.mitNaechstem);
    z1.appendChild(kontrolle); z1.appendChild(mitNaechstem);
    pag.appendChild(z1);
    const z2 = zeile();
    const zusammen = haken('Diesen Absatz zusammenhalten', stand.zusammen);
    const umbruchVor = haken('Seitenumbruch oberhalb', stand.umbruchVor);
    z2.appendChild(zusammen); z2.appendChild(umbruchVor);
    pag.appendChild(z2);
    k.appendChild(pag);

    const um = block('Zeilenumbruch');
    const mittenImWort = haken('Textumbruch in der Mitte eines Wortes zulassen', stand.mittenImWort);
    const ohneTrennung = haken('Keine Silbentrennung in diesem Absatz', stand.ohneTrennung);
    um.appendChild(mittenImWort); um.appendChild(ohneTrennung);
    k.appendChild(um);

    const aus = block('Textausrichtung');
    const z3 = zeile();
    const textausrichtung = waehler([
      ['auto', 'Automatisch'], ['oben', 'Oben'],
      ['mitte', 'Zentriert'], ['unten', 'Unten'],
    ], stand.textausrichtung);
    z3.appendChild(beschriftet('Textausrichtung', textausrichtung));
    aus.appendChild(z3);
    k.appendChild(aus);

    umbruchFelder = { kontrolle, mitNaechstem, zusammen, umbruchVor,
                      mittenImWort, ohneTrennung, textausrichtung };
    return k;
  }

  const KARTEN = [
    ['masse',   'Einzüge und Abstände',     karteMasse],
    ['umbruch', 'Zeilen- und Seitenumbruch', karteUmbruch],
  ];

  const zeige = (kuerzel) => {
    const eintrag = KARTEN.find(([k]) => k === kuerzel) || KARTEN[0];
    buehne.textContent = '';
    buehne.appendChild(eintrag[2]());
    [...reiter.children].forEach((c) => {
      c.classList.toggle('rahmentafel__reiter--an', c.dataset.karte === eintrag[0]);
    });
  };
  for (const [kuerzel, name] of KARTEN) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rahmentafel__reiter-knopf';
    k.dataset.karte = kuerzel;
    k.textContent = name;
    k.addEventListener('click', () => zeige(kuerzel));
    reiter.appendChild(k);
  }

  kasten.appendChild(reiter);
  kasten.appendChild(buehne);

  const schaurahmen = document.createElement('div');
  schaurahmen.className = 'absatzfenster__schau';
  schaurahmen.innerHTML = '<h4>Vorschau</h4>';
  schaurahmen.appendChild(schau);
  kasten.appendChild(schaurahmen);

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe absatzfenster__fuss';
  const tabs = document.createElement('button');
  tabs.type = 'button'; tabs.className = 'knopf'; tabs.textContent = 'Tabstopps…';
  tabs.addEventListener('click', () => { grund.remove(); if (B.tabstopps) B.tabstopps(); });
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  ab.addEventListener('click', () => grund.remove());
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'OK';
  ok.addEventListener('click', () => {
    /* Stand der Zeiger nirgends, galt der Klick auf OK bisher als Fehler:
       Das Fenster ging zu und nichts geschah. In WPS wirkt er dann auf den
       Absatz, in dem zuletzt gearbeitet wurde. Notfalls auf den ersten —
       ein Fenster, das man ausfuellt und das nichts tut, ist schlimmer als
       eine Einstellung an der falschen Stelle, die man zuruecknehmen kann. */
    let ziele = absaetzeInAuswahl();
    if (!ziele.length) {
      const einer = (typeof absatzJetzt === 'function' && absatzJetzt())
                 || feld.querySelector('p, h1, h2, h3, h4, li');
      ziele = einer ? [einer] : [];
    }
    if (!ziele.length) { melde('Dafür braucht es einen Absatz im Blatt.'); grund.remove(); return; }
    for (const el of ziele) {
      if (felder) {
        stileAusFeldern(el, 1);
        const ebene = felder.ebene.value;
        if (ebene) el.dataset.ebene = ebene; else delete el.dataset.ebene;
      }
      if (umbruchFelder) {
        const u = umbruchFelder;
        el.style.breakBefore = u.umbruchVor.eingabe.checked ? 'page' : '';
        el.style.pageBreakBefore = u.umbruchVor.eingabe.checked ? 'always' : '';
        el.style.breakInside = u.zusammen.eingabe.checked ? 'avoid' : '';
        el.style.breakAfter = u.mitNaechstem.eingabe.checked ? 'avoid' : '';
        /* Absatzkontrolle: keine einzelne Zeile allein auf einer Seite.
           Der Browser kann das von sich aus — abschalten heisst 2 auf 1. */
        el.style.widows = u.kontrolle.eingabe.checked ? '2' : '1';
        el.style.orphans = u.kontrolle.eingabe.checked ? '2' : '1';
        el.style.overflowWrap = u.mittenImWort.eingabe.checked ? 'anywhere' : '';
        el.style.hyphens = u.ohneTrennung.eingabe.checked ? 'none' : '';
        el.style.verticalAlign = '';
        for (const [feld, wert] of [
          ['kontrolle', u.kontrolle.eingabe.checked ? '' : 'aus'],
          ['mitnaechstem', u.mitNaechstem.eingabe.checked ? 'ja' : ''],
          ['mittenimwort', u.mittenImWort.eingabe.checked ? 'ja' : ''],
          ['trennung', u.ohneTrennung.eingabe.checked ? 'aus' : ''],
          ['textausrichtung', u.textausrichtung.value === 'auto' ? '' : u.textausrichtung.value],
        ]) {
          if (wert) el.dataset[feld] = wert; else delete el.dataset[feld];
        }
      }
    }
    geaendertMelden();
    melde('Absatz gesetzt.');
    grund.remove();
  });
  fuss.appendChild(tabs); fuss.appendChild(ab); fuss.appendChild(ok);
  kasten.appendChild(fuss);

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
  zeige(karteZuerst || 'masse');
};

/* Beide alten Namen zeigen hierher. Zwei Fenster fuer einen Absatz
   waren genau das, was er „doppelt gemoppelt" genannt hat. */
B.einzugGenau = () => B.absatz('masse');
B.absatzabstand = () => B.absatz('masse');

/* ---- Seite: Ränder und Spalten ---- */
let seitenrand = Speicher.lies('seitenrand', { oben: 20, unten: 20, links: 20, rechts: 20 });
let spalten = Speicher.lies('spalten', 1);

function seiteAnwenden() {
  const blatt = $('blatt');
  blatt.style.paddingTop = seitenrand.oben + 'mm';
  blatt.style.paddingBottom = seitenrand.unten + 'mm';
  blatt.style.paddingLeft = seitenrand.links + 'mm';
  blatt.style.paddingRight = seitenrand.rechts + 'mm';
  /* Dieselben Maße noch einmal als Eigenschaften: Kopf- und Fußzeile
     sitzen im Rand und müssen wissen, wie breit er ist. Aus dem Polster
     allein lässt sich das im Stilblatt nicht ablesen. */
  for (const kante of ['oben', 'unten', 'links', 'rechts']) {
    blatt.style.setProperty('--rand-' + kante, seitenrand[kante] + 'mm');
  }
  feld.style.columnCount = spalten > 1 ? spalten : '';
  feld.style.columnGap = spalten > 1 ? '8mm' : '';
  Speicher.schreib('seitenrand', seitenrand);
  Speicher.schreib('spalten', spalten);
  linealAuffrischen();
}

B.seitenraender = () => {
  fenster('Seitenränder', [
    { art: 'satz', text: 'In Millimetern. Ein Brief hat üblicherweise 20 mm ringsum.' },
    { schluessel: 'oben', name: 'oben', art: 'number', wert: seitenrand.oben },
    { schluessel: 'unten', name: 'unten', art: 'number', wert: seitenrand.unten },
    { schluessel: 'links', name: 'links', art: 'number', wert: seitenrand.links },
    { schluessel: 'rechts', name: 'rechts', art: 'number', wert: seitenrand.rechts },
  ], (werte) => {
    for (const seite of ['oben', 'unten', 'links', 'rechts']) {
      const zahl = parseFloat(werte[seite]);
      if (!Number.isNaN(zahl)) seitenrand[seite] = Math.max(0, Math.min(80, zahl));
    }
    seiteAnwenden();
    abschnittMerken(abschnittJetztNr);
    melde('Seitenränder gesetzt.');
  });
};

/* Eins, zwei oder drei direkt aus der Klappe — ohne Fenster dazwischen.
   In WPS sind das drei Klicks weniger als ueber „Mehr Spalten…". */
B.spaltenSetzen = (zahl) => {
  spalten = Math.max(1, Math.min(3, parseInt(zahl, 10) || 1));
  seiteAnwenden();
  melde(spalten === 1 ? 'Eine Spalte.' : spalten + ' Spalten.');
};

B.spalten = () => {
  fenster('Spalten', [
    { art: 'satz', text: 'Wie viele Spalten der Text bekommt.' },
    { schluessel: 'zahl', name: 'Spalten', art: 'auswahl',
      werte: [['1', 'eine'], ['2', 'zwei'], ['3', 'drei']], wert: String(spalten) },
  ], (werte) => {
    spalten = parseInt(werte.zahl, 10) || 1;
    seiteAnwenden();
    melde(spalten === 1 ? 'Eine Spalte.' : spalten + ' Spalten.');
  });
};

/* ---- Einfügen: Hyperlink, Kommentar, Textfeld, Sonderzeichen ---- */
B.hyperlink = () => {
  const auswahl = window.getSelection();
  const markiert = auswahl.rangeCount ? auswahl.toString() : '';
  auswahlMerken();
  fenster('Hyperlink einfügen', [
    { schluessel: 'text', name: 'Beschriftung', wert: markiert },
    { schluessel: 'ziel', name: 'Adresse', wert: 'https://' },
  ], (werte) => {
    const ziel = werte.ziel.trim();
    /* Nur Adressen, die auch aufgehen können. „javascript:" in einem
       Dokument ist nichts, was jemand hineinschreiben wollte. */
    if (!/^(https?|mailto):/i.test(ziel)) { melde('Das ist keine brauchbare Adresse.'); return; }
    const text = (werte.text.trim() || ziel).replace(/[<>&]/g, '');
    auswahlZurueck();
    Dokument.einfuegen('<a href="' + ziel.replace(/"/g, '&quot;') + '">' + text + '</a>');
    melde('Hyperlink eingefügt.');
  }, 'Einfügen');
};

/* Einen vorhandenen Hyperlink ändern oder wegnehmen.
 *
 * Beides gibt es nur unter der rechten Maustaste, und das ist richtig so:
 * Man kann es nur tun, wenn man auf einem Link steht — und dann zeigt man
 * ohnehin schon darauf. Im Menü stünden zwei Punkte, die meistens grau
 * sind.
 */
B.linkBearbeiten = (a) => {
  if (!a) return;
  fenster('Hyperlink bearbeiten', [
    { schluessel: 'text', name: 'Beschriftung', wert: a.textContent },
    { schluessel: 'ziel', name: 'Adresse', wert: a.getAttribute('href') || '' },
  ], (werte) => {
    const ziel = werte.ziel.trim();
    if (!/^(https?|mailto):/i.test(ziel)) { melde('Das ist keine brauchbare Adresse.'); return; }
    a.setAttribute('href', ziel);
    a.textContent = werte.text.trim() || ziel;
    geaendertMelden();
    melde('Hyperlink geändert.');
  }, 'Übernehmen');
};

/* Der Text bleibt, der Link geht. „removeFormat" täte das nicht — es
   nimmt Fett und Farbe weg und lässt das <a> stehen. */
B.linkEntfernen = (a) => {
  if (!a || !a.parentNode) return;
  const text = document.createTextNode(a.textContent);
  a.parentNode.replaceChild(text, a);
  geaendertMelden();
  melde('Hyperlink entfernt — der Text bleibt.');
};

/* Die Adresse in die Zwischenablage. Erst der neue Weg, dann der alte:
   Im eigenen Fenster ist die Berechtigung für die Zwischenablage nicht
   immer da, und ein Menüpunkt, der still nichts tut, ist schlimmer als
   keiner. */
B.linkKopieren = async (a) => {
  const ziel = a ? a.getAttribute('href') || '' : '';
  if (!ziel) return;
  try {
    await navigator.clipboard.writeText(ziel);
    melde('Adresse kopiert.');
    return;
  } catch (e) { /* dann der alte Weg */ }
  const feldchen = document.createElement('textarea');
  feldchen.value = ziel;
  feldchen.style.position = 'fixed';
  feldchen.style.opacity = '0';
  document.body.appendChild(feldchen);
  feldchen.select();
  let ging = false;
  try { ging = document.execCommand('copy'); } catch (e) { ging = false; }
  feldchen.remove();
  feld.focus();
  melde(ging ? 'Adresse kopiert.' : 'Die Adresse ließ sich nicht kopieren: ' + ziel);
};

B.kommentar = () => {
  auswahlMerken();
  fenster('Kommentar', [
    { art: 'satz', text: 'Steht am Rand und wird nicht mitgedruckt.' },
    { schluessel: 'text', name: 'Anmerkung' },
  ], (werte) => {
    const text = werte.text.trim();
    if (!text) return;
    auswahlZurueck();
    const marke = '<span class="kommentar" contenteditable="false" title="'
                + text.replace(/"/g, '&quot;') + '">✎</span>';
    elementEinfuegen(marke);
    melde('Kommentar gesetzt — er wird nicht mitgedruckt.');
  }, 'Setzen');
};

/* ============================================================
   DIE BEFEHLE DER TEXTTOOLS

   „Du setzt hier einen Text mit Rahmen. Der Rahmen laesst sich nicht
   entfernen in Lunivo."

   Er liess sich nicht entfernen, weil es keinen Ort gab, an dem man es
   haette tun koennen: Das Textfeld kam mit einem Rahmen aus dem
   Stilblatt, und kein Befehl fasste ihn an.

   Jetzt gilt: Was am Textfeld steht, steht IM Textfeld — als eigene
   Angabe, die das Stilblatt schlaegt. „Kein Rahmen" ist damit eine
   Einstellung und keine Unmoeglichkeit.
   ============================================================ */
function mitRahmen(tun) {
  const r = textrahmenJetzt();
  if (!r) { melde('Dafür muss der Zeiger in einem Textfeld stehen.'); return null; }
  return tun(r);
}

/* Die Farbtafel, die schon fuer Schrift und Marker da ist — mit seiner
   Palette. Hier nur mit anderem Ziel. */
function rahmenFarbtafel(knopf, titel, setzen, ohneName) {
  mitRahmen((r) => {
    designTafelZeigen(knopf, titel, (tafel) => {
      tafel.classList.add('designtafel--breit', 'farbtafel');
      const reihe = document.createElement('div');
      reihe.className = 'farbtafel__reihe farbtafel__reihe--zwoelf';
      for (const [hex, name] of FARBEN) {
        const feldchen = farbfeld(hex, () => {
          designTafelWeg();
          setzen(r, hex);
          geaendertMelden();
          melde(titel + ': ' + name + '.');
        });
        feldchen.title = name;
        reihe.appendChild(feldchen);
      }
      tafel.appendChild(reihe);

      const strichel = document.createElement('hr');
      strichel.className = 'designtafel__strich';
      tafel.appendChild(strichel);

      const ohne = document.createElement('button');
      ohne.type = 'button';
      ohne.className = 'designtafel__zeile richtungszeile';
      ohne.appendChild(symbol('radierer'));
      const w = document.createElement('span');
      w.textContent = ohneName;
      ohne.appendChild(w);
      ohne.addEventListener('mousedown', (e) => e.preventDefault());
      ohne.addEventListener('click', () => {
        designTafelWeg();
        setzen(r, '');
        geaendertMelden();
        melde(ohneName + '.');
      });
      tafel.appendChild(ohne);
    });
  });
}

B.rahmenFuellung = (knopf) => rahmenFarbtafel(knopf, 'Füllung',
  (r, hex) => { r.style.background = hex || 'transparent'; }, 'Keine Füllung');

B.rahmenKontur = (knopf) => rahmenFarbtafel(knopf, 'Kontur',
  (r, hex) => {
    /* DAS IST SEIN PUNKT: „Kein Rahmen" muss gehen. Eine leere Angabe
       hiesse „nimm, was im Stilblatt steht" — und dort steht ein
       Rahmen. Also ausdruecklich keiner. */
    r.style.border = hex ? ((r.dataset.konturstaerke || 1) + 'px solid ' + hex) : 'none';
    r.dataset.konturfarbe = hex;
  }, 'Kein Rahmen');

B.rahmenTextfarbe = (knopf) => rahmenFarbtafel(knopf, 'Textfüllung',
  (r, hex) => { r.style.color = hex; }, 'Automatisch');

B.rahmenTextkontur = (knopf) => rahmenFarbtafel(knopf, 'Textkontur',
  (r, hex) => {
    r.style.webkitTextStroke = hex ? '0.7px ' + hex : '';
  }, 'Keine Kontur');

const RAHMENEFFEKTE = [
  ['keiner',   'Kein Effekt',     ''],
  ['schatten', 'Schatten',        '0 2px 6px rgba(0,0,0,.25)'],
  ['tief',     'Tiefer Schatten', '3px 5px 10px rgba(0,0,0,.35)'],
  ['leuchten', 'Leuchten',        '0 0 10px rgba(47,111,181,.5)'],
  ['weich',    'Weicher Rand',    '0 0 0 4px rgba(127,127,127,.12)'],
];

B.rahmenEffekt = (knopf) => mitRahmen((r) => {
  designTafelZeigen(knopf, 'Effekte', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [, name, schatten] of RAHMENEFFEKTE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      const probe = document.createElement('span');
      probe.className = 'rahmenprobe--klein';
      probe.style.boxShadow = schatten;
      k.appendChild(probe);
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        r.style.boxShadow = schatten;
        geaendertMelden();
        melde('Effekt: ' + name + '.');
      });
      tafel.appendChild(k);
    }
  });
});

B.rahmenGroesse = () => mitRahmen((r) => {
  fenster('Größe des Textfelds', [
    { art: 'satz', text: 'Leer lassen heißt: so breit wie der Text es braucht.' },
    { schluessel: 'breite', name: 'Breite (mm)', art: 'number', wert: '' },
    { schluessel: 'hoehe', name: 'Mindesthöhe (mm)', art: 'number', wert: '' },
  ], (werte) => {
    r.style.width = werte.breite ? werte.breite + 'mm' : '';
    r.style.minHeight = werte.hoehe ? werte.hoehe + 'mm' : '';
    geaendertMelden();
    melde('Größe gesetzt.');
  });
});

B.rahmenEinstellungen = () => mitRahmen((r) => {
  fenster('Textfeld', [
    { schluessel: 'staerke', name: 'Konturstärke (px)', art: 'number',
      wert: r.dataset.konturstaerke || '1', schritt: '0.5' },
    { schluessel: 'rund', name: 'Ecken runden (px)', art: 'number',
      wert: String(parseFloat(r.style.borderRadius) || 4) },
    { schluessel: 'innen', name: 'Innenabstand (mm)', art: 'number',
      wert: String(parseFloat(r.style.padding) || 3) },
  ], (werte) => {
    r.dataset.konturstaerke = werte.staerke;
    if (r.dataset.konturfarbe) {
      r.style.border = werte.staerke + 'px solid ' + r.dataset.konturfarbe;
    }
    r.style.borderRadius = werte.rund + 'px';
    r.style.padding = werte.innen + 'mm';
    geaendertMelden();
    melde('Textfeld eingestellt.');
  });
});

B.rahmenWeg = () => mitRahmen((r) => {
  /* Der Text bleibt, der Kasten geht — sonst waere „Textfeld loeschen"
     dasselbe wie „Text loeschen", und das will selten jemand. */
  const eltern = r.parentNode;
  while (r.firstChild) eltern.insertBefore(r.firstChild, r);
  r.remove();
  geaendertMelden();
  melde('Textfeld aufgelöst — der Text bleibt.');
});

B.textfeld = () => {
  /* Rahmenfarbe und -staerke stehen AM Kasten, nicht nur im Stilblatt.
     Sonst liesse sich „kein Rahmen" nicht einstellen — genau das war
     sein zweiter Befund. */
  const kasten = document.createElement('div');
  kasten.className = 'textrahmen';
  kasten.dataset.konturfarbe = '#9AA3AB';
  kasten.dataset.konturstaerke = '1';
  kasten.style.border = '1px solid #9AA3AB';
  kasten.innerHTML = '<p>Text im Rahmen</p>';
  blockEinfuegen(kasten, true);
  geaendertMelden();
  melde('Textrahmen eingefügt.');
};

const SONDERZEICHEN = ['§', '€', '£', '©', '®', '™', '°', '±', '×', '÷', '≈', '≠', '≤', '≥',
                       '½', '¼', '¾', '‰', '†', '•', '–', '—', '„', '“', '”', '‚', '‘', '’',
                       '«', '»', 'α', 'β', 'π', 'Ω', '∑', '√', '∞', '→', '←', '↔', '✓', '✗'];

B.sonderzeichen = () => {
  auswahlMerken();
  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog';
  kasten.innerHTML = '<h3 class="dialog__titel">Sonderzeichen</h3>';
  const gitter = document.createElement('div');
  gitter.className = 'zeichengitter';
  for (const z of SONDERZEICHEN) {
    const k = document.createElement('button');
    k.className = 'zeichenknopf';
    k.textContent = z;
    k.addEventListener('click', () => {
      grund.remove();
      auswahlZurueck();
      Dokument.einfuegen(z === '&' ? '&amp;' : z);
    });
    gitter.appendChild(k);
  }
  kasten.appendChild(gitter);
  const zu = document.createElement('button');
  zu.className = 'knopf'; zu.textContent = 'Schließen';
  zu.addEventListener('click', () => { grund.remove(); auswahlZurueck(); });
  const reihe = document.createElement('div');
  reihe.className = 'dialog__knoepfe'; reihe.appendChild(zu);
  kasten.appendChild(reihe);
  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) { grund.remove(); auswahlZurueck(); } });
  document.body.appendChild(grund);
};

/* ---- Kopf- und Fußzeile ---- */
let kopfAn = Speicher.lies('kopfAn', false);
let fussAn = Speicher.lies('fussAn', false);

function kopfFussAnwenden() {
  $('kopfzeile').hidden = !kopfAn;
  $('fusszeile').hidden = !fussAn;
  Speicher.schreib('kopfAn', kopfAn);
  Speicher.schreib('fussAn', fussAn);
  menueBauen();
  /* Der Reiter „Kopf- und Fußzeile" hängt nicht nur an der Schreibstelle,
     sondern auch daran, ob die Zeile überhaupt dasteht. Wird sie ein- oder
     ausgeschaltet, bewegt sich die Schreibstelle nicht — ohne diese Zeile
     bliebe der Reiter also weg (oder stehen), bis man das nächste Mal
     irgendwohin klickt. */
  if (typeof zusammenhangPruefen === 'function') zusammenhangPruefen();
}
B.kopfzeile = () => { kopfAn = !kopfAn; kopfFussAnwenden(); if (kopfAn) $('kopfzeile').focus(); };
B.fusszeile = () => { fussAn = !fussAn; kopfFussAnwenden(); if (fussAn) $('fusszeile').focus(); };

/* Hin und zurück zwischen Blatt und Kopf-/Fußzeile.

   Mit der Maus ist der Weg zurück der schwierigere: Die Zeilen sind
   schmal, das Blatt ist groß — hinein trifft man leicht, heraus nicht.
   „Hin" schaltet die Zeile ein, falls sie aus war; sonst führte ein Knopf
   an eine Stelle, die es gerade nicht gibt. */
B.zurKopfzeile = () => {
  if (!kopfAn) { kopfAn = true; kopfFussAnwenden(); }
  $('kopfzeile').focus();
};
B.zurFusszeile = () => {
  if (!fussAn) { fussAn = true; kopfFussAnwenden(); }
  $('fusszeile').focus();
};
B.zurueckInText = () => feld.focus();

/* ============================================================
   Die Werkzeuge für das, was im Text steht

   Bisher ließ sich alles nur einfügen. Eine Form, ein Diagramm, ein
   SmartArt, eine Formel — einmal im Text, waren sie ein Bild: löschen und
   neu machen ging, ändern nicht. Wer sich bei einer Zahl vertippt hatte,
   tippte alle noch einmal.

   Möglich wird das Ändern dadurch, dass jedes Objekt seine Quelle
   mitträgt (siehe merkeQuelle). Die Werkzeuge lesen sie, zeigen sie im
   selben Fenster wie beim Einfügen und setzen das Ergebnis an dieselbe
   Stelle.
   ============================================================ */

/* Ein Objekt an Ort und Stelle durch ein neues ersetzen. */
function objektErsetzen(alt, neuerText) {
  const halter = document.createElement('div');
  halter.innerHTML = neuerText;
  const neu = halter.firstElementChild;
  if (!neu) return false;
  alt.replaceWith(neu);
  geaendertMelden();
  return true;
}

/* ---- Zeichentools ---- */

B.formAendern = () => {
  const form = formJetzt();
  if (!form) { melde('Im Text steht keine Form.'); return; }
  const q = quelleLesen(form) || { form: 'linie', farbe: '#2F6FB5' };
  fenster('Form', [
    { schluessel: 'form', name: 'Form', art: 'auswahl', wert: q.form,
      werte: [['linie', 'Linie'], ['pfeil', 'Pfeil'], ['rechteck', 'Rechteck'], ['kreis', 'Kreis']] },
  ], (werte) => formNeuZeichnen(form, Object.assign({}, q, { form: werte.form })));
};

B.formFuellung = () => {
  const form = formJetzt();
  if (!form) { melde('Im Text steht keine Form.'); return; }
  const q = quelleLesen(form) || {};
  /* Linie und Pfeil haben keine Fläche — eine Füllung wäre dort ein
     Knopf, der nichts tut. */
  if (q.form === 'linie' || q.form === 'pfeil') {
    melde('Eine Linie hat keine Fläche zum Füllen.'); return;
  }
  fenster('Füllung', [
    { schluessel: 'wie', name: 'Fläche', art: 'auswahl',
      wert: q.fuellung === 'none' ? 'ohne' : 'farbe',
      werte: [['farbe', 'Mit Farbe füllen'], ['ohne', 'Ohne Füllung']] },
    { schluessel: 'fuellung', name: 'Farbe der Fläche', art: 'color',
      wert: q.fuellung && q.fuellung !== 'none' ? q.fuellung : '#E3EBF5' },
  ], (werte) => formNeuZeichnen(form, Object.assign({}, q, {
    fuellung: werte.wie === 'ohne' ? 'none' : werte.fuellung })));
};

B.formKontur = () => {
  const form = formJetzt();
  if (!form) { melde('Im Text steht keine Form.'); return; }
  const q = quelleLesen(form) || {};
  fenster('Kontur', [
    { schluessel: 'farbe', name: 'Farbe der Linie', art: 'color', wert: q.farbe || '#2F6FB5' },
    { schluessel: 'strich', name: 'Dicke (1 bis 8)', art: 'number',
      wert: String(q.strich || 2), schritt: '1' },
  ], (werte) => formNeuZeichnen(form, Object.assign({}, q, {
    farbe: werte.farbe,
    strich: Math.max(1, Math.min(8, Number(werte.strich) || 2)) })));
};

B.formGroesse = () => {
  const form = formJetzt();
  if (!form) { melde('Im Text steht keine Form.'); return; }
  fenster('Größe', [
    { schluessel: 'breite', name: 'Breite (Bildpunkte)', art: 'number',
      wert: String(form.getAttribute('width') || 120), schritt: '10' },
    { schluessel: 'hoehe', name: 'Höhe (Bildpunkte)', art: 'number',
      wert: String(form.getAttribute('height') || 60), schritt: '10' },
  ], (werte) => {
    const b = Math.max(20, Math.min(1200, Number(werte.breite) || 120));
    const h = Math.max(20, Math.min(1200, Number(werte.hoehe) || 60));
    form.setAttribute('width', b);
    form.setAttribute('height', h);
    geaendertMelden();
    melde('Größe geändert.');
  });
};

/* Zeichnet die Form aus ihrer Quelle neu — Form, Farbe, Füllung, Dicke.
   Die Maße bleiben, was sie waren: Wer die Farbe wechselt, will nicht
   auch die Größe zurückgesetzt bekommen. */
function formNeuZeichnen(alt, q) {
  const kennung = 'p' + Date.now().toString(36);
  let innen = (FORMEN[q.form] || FORMEN.linie)
    .replace(/COLOR/g, q.farbe || '#2F6FB5')
    .replace(/MID/g, kennung);
  if (q.strich && q.strich !== 2) {
    innen = innen.replace(/stroke-width="2"/g, 'stroke-width="' + q.strich + '"');
  }
  if (q.fuellung && q.fuellung !== 'none') {
    innen = innen.replace(/fill="none"/g, 'fill="' + q.fuellung + '"');
  }
  const b = alt.getAttribute('width') || 120;
  const h = alt.getAttribute('height') || 60;
  const neu = merkeQuelle('<svg class="zeichnung" xmlns="http://www.w3.org/2000/svg" '
    + 'viewBox="0 0 120 60" width="' + b + '" height="' + h + '">' + innen + '</svg>', q);
  if (objektErsetzen(alt, neu)) melde('Form geändert.');
}

/* ---- Diagrammwerkzeuge ---- */

/* Entwurf und Daten öffnen dasselbe Fenster; nur der Anlass ist ein
   anderer. „Daten" ist der häufigere Weg — eine Zahl stimmt nicht —,
   „Entwurf" der seltenere: Überschrift und Art. */
/* ============================================================
   DATEN BEARBEITEN — ALS TABELLE

   Er hat es so beschrieben: „Es oeffnet sich ein Mini-Spreadsheet.
   Tragen Sie dort Ihre Zeilen- und Spaltenbeschriftungen sowie Werte
   ein. Speichern, um das Diagramm im Text zu aktualisieren."

   Vorher war es ein Kasten, in den man „Miete: 480" tippte. Wer eine
   Tabelle im Kopf hat, tippt keine Doppelpunkte — und wer sich
   vertippt, sieht es nicht.

   In einer Tabelle sieht man die Spalte. Man kann eine Zeile anhaengen,
   eine wegnehmen, und was man eintraegt, steht da, wo es hingehoert.
   ============================================================ */
function datenTabelle(punkte, beiAenderung) {
  const kasten = document.createElement('div');
  kasten.className = 'datentabelle';

  const tabelle = document.createElement('table');
  tabelle.className = 'datentabelle__gitter';
  tabelle.innerHTML = '<thead><tr><th>Beschriftung</th><th>Wert</th><th></th></tr></thead>';
  const koerper = document.createElement('tbody');
  tabelle.appendChild(koerper);

  const zeilen = punkte.length
    ? punkte.map((p) => ({ name: p.name, wert: p.wert }))
    : [{ name: '', wert: '' }];

  function melden() {
    if (beiAenderung) beiAenderung(zeilen.filter((z) => String(z.wert).trim() !== ''));
  }

  function bauen() {
    koerper.textContent = '';
    zeilen.forEach((z, i) => {
      const tr = document.createElement('tr');

      const tdName = document.createElement('td');
      const name = document.createElement('input');
      name.type = 'text';
      name.value = z.name;
      name.placeholder = 'Rubrik ' + (i + 1);
      name.addEventListener('input', () => { z.name = name.value; melden(); });
      tdName.appendChild(name);
      tr.appendChild(tdName);

      const tdWert = document.createElement('td');
      const wert = document.createElement('input');
      wert.type = 'text';
      wert.inputMode = 'decimal';
      wert.value = z.wert;
      wert.addEventListener('input', () => { z.wert = wert.value; melden(); });
      /* Enter haengt eine Zeile an — wer Zahlen eintraegt, will nicht
         zwischendurch zur Maus greifen. */
      wert.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        if (i === zeilen.length - 1) { zeilen.push({ name: '', wert: '' }); bauen(); }
        const naechste = koerper.children[i + 1];
        if (naechste) naechste.querySelector('input').focus();
      });
      tdWert.appendChild(wert);
      tr.appendChild(tdWert);

      const tdWeg = document.createElement('td');
      const weg = document.createElement('button');
      weg.type = 'button';
      weg.className = 'datentabelle__weg';
      weg.textContent = '×';
      weg.title = 'Zeile löschen';
      weg.disabled = zeilen.length <= 1;
      weg.addEventListener('click', () => {
        zeilen.splice(i, 1);
        if (!zeilen.length) zeilen.push({ name: '', wert: '' });
        bauen(); melden();
      });
      tdWeg.appendChild(weg);
      tr.appendChild(tdWeg);

      koerper.appendChild(tr);
    });
  }

  bauen();
  kasten.appendChild(tabelle);

  const mehr = document.createElement('button');
  mehr.type = 'button';
  mehr.className = 'knopf datentabelle__mehr';
  mehr.textContent = '+ Zeile';
  mehr.addEventListener('click', () => {
    zeilen.push({ name: '', wert: '' });
    bauen();
    koerper.lastElementChild.querySelector('input').focus();
  });
  kasten.appendChild(mehr);

  kasten.alsText = () => zeilen
    .filter((z) => String(z.wert).trim() !== '')
    .map((z) => (z.name || 'Ohne Namen') + ': ' + z.wert).join('\n');
  return kasten;
}

B.diagrammDaten = () => {
  const bild = diagrammJetzt();
  if (!bild) { melde('Dafür muss ein Diagramm gewählt sein.'); return; }
  const q = quelleLesen(bild);
  if (!q) {
    melde('Dieses Diagramm stammt aus einer älteren Fassung — '
        + 'es trägt seine Zahlen nicht mit und lässt sich nur neu einfügen.');
    return;
  }

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog dialog--breit datenfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Daten bearbeiten</h3>';

  const koerper = document.createElement('div');
  koerper.className = 'datenfenster__koerper';

  const links = document.createElement('div');
  links.className = 'datenfenster__links';

  const titelzeile = document.createElement('label');
  titelzeile.className = 'dialog__zeile';
  titelzeile.innerHTML = '<span>Diagrammtitel</span>';
  const titel = document.createElement('input');
  titel.type = 'text';
  titel.value = q.titel || '';
  titelzeile.appendChild(titel);
  links.appendChild(titelzeile);

  /* Die Vorschau rechts rechnet bei jedem Tastendruck mit. So sieht man
     beim Eintragen, was daraus wird — das ist der Sinn der Tabelle. */
  const schau = document.createElement('div');
  schau.className = 'datenfenster__schau';

  let punkteJetzt = zahlenLesen(q.daten || '');
  const zeichnen = () => {
    schau.innerHTML = diagrammZeichnen(q.art, punkteJetzt.length ? punkteJetzt
      : [{ name: '—', wert: 1 }], titel.value.trim(), {
      farben: diagrammSatz(q.satz), werte: q.werte, legende: q.legende,
    });
  };
  titel.addEventListener('input', zeichnen);

  const tabelle = datenTabelle(punkteJetzt, (neu) => {
    punkteJetzt = neu.map((z) => ({
      name: z.name,
      wert: parseFloat(String(z.wert).replace(',', '.')) || 0,
    }));
    zeichnen();
  });
  links.appendChild(tabelle);
  koerper.append(links, schau);
  kasten.appendChild(koerper);
  zeichnen();

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  ab.addEventListener('click', () => grund.remove());
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'Speichern';
  ok.addEventListener('click', () => {
    const text = tabelle.alsText();
    if (!zahlenLesen(text).length) { melde('Es steht keine Zahl in der Tabelle.'); return; }
    grund.remove();
    diagrammNeuZeichnen(bild, Object.assign({}, q, {
      daten: text, titel: titel.value.trim(),
    }));
  });
  fuss.append(ab, ok);
  kasten.appendChild(fuss);

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
};

function diagrammFenster(titel, nurDaten) {
  const bild = diagrammJetzt();
  if (!bild) { melde('Im Text steht kein Diagramm.'); return; }
  const q = quelleLesen(bild);
  if (!q) {
    melde('Dieses Diagramm stammt aus einer älteren Fassung — '
        + 'es trägt seine Zahlen nicht mit und lässt sich nur neu einfügen.');
    return;
  }
  const felder = [{ art: 'satz', text: 'Je Zeile ein Wert: „Miete: 480".' }];
  if (!nurDaten) {
    felder.push({ schluessel: 'titel', name: 'Überschrift', wert: q.titel || '' });
    felder.push({ schluessel: 'art', name: 'Art', art: 'auswahl', wert: q.art,
      werte: [['balken', 'Balken'], ['linie', 'Linie'], ['kuchen', 'Kreis']] });
  }
  felder.push({ schluessel: 'daten', name: 'Zahlen', art: 'flaeche', zeilen: 7,
                wert: q.daten || '' });

  fenster(titel, felder, (werte) => {
    const neuQ = {
      art: nurDaten ? q.art : werte.art,
      titel: nurDaten ? (q.titel || '') : werte.titel.trim(),
      daten: werte.daten,
    };
    diagrammNeuZeichnen(bild, neuQ);
  });
}

/* ============================================================
   DIAGRAMMTOOLS

   Nach seinem Bild der WPS-Leiste, die erscheint, sobald ein Diagramm
   gewaehlt ist:

     Diagrammelement hinzufuegen ▾ · Schnelllayout ▾ · Farbe aendern ▾
     [ Vier Formatvorlagen zur Auswahl ]
     Diagrammtyp aendern · [kleine Typzeichen]
     Daten auswaehlen · Daten bearbeiten
     Diagrammbereich ▾ · Formatieren · Formatvorlage zuruecksetzen

   Vorher standen dort vier grosse Knoepfe, die vier Fenster oeffneten.
   Ein Diagramm aendert man aber nicht in einem Fenster, sondern indem
   man hinsieht und etwas anklickt.

   DIE FARBSAETZE KOMMEN AUS SEINER PALETTE. FARBEN steht seit je in
   dieser Datei; ich habe sie schon einmal gegen WPS-Signalfarben
   getauscht und dafuer zu Recht Aerger bekommen.
   ============================================================ */
const DIAGRAMMSAETZE = [
  ['bunt',   'Bunt',        ['#2F6FB5', '#3E9C7A', '#C08A2E', '#B5563F', '#7A5EA8', '#1F7A5A']],
  ['blau',   'Blautöne',    ['#1F4E79', '#2F6FB5', '#4A8BCB', '#6FA6DA', '#9BC3E8', '#C6DDF3']],
  ['warm',   'Warm',        ['#8A3324', '#B5563F', '#C08A2E', '#D08A3E', '#C9A227', '#A0522D']],
  ['gruen',  'Grüntöne',    ['#1F7A5A', '#3E9C7A', '#6BB79A', '#93CDB7', '#BCE0D3', '#E0F0E9']],
  ['grau',   'Graustufen',  ['#111417', '#3A4149', '#5C666F', '#8B949C', '#B6BDC3', '#DDE1E4']],
];

function diagrammSatz(kuerzel) {
  return (DIAGRAMMSAETZE.find(([k]) => k === kuerzel) || DIAGRAMMSAETZE[0])[2];
}

/* Was am Diagramm dranstehen soll: Titel, Legende, Werte. */
const DIAGRAMMTEILE = [
  ['titel',    'Diagrammtitel'],
  ['legende',  'Legende'],
  ['werte',    'Datenbeschriftungen'],
];

function mitDiagramm(tun) {
  const bild = diagrammJetzt();
  if (!bild) { melde('Dafür muss ein Diagramm gewählt sein.'); return null; }
  const q = quelleLesen(bild);
  if (!q) { melde('Dieses Diagramm trägt seine Zahlen nicht mit.'); return null; }
  return tun(bild, q);
}

B.diagrammElement = (knopf) => mitDiagramm((bild, q) => {
  designTafelZeigen(knopf, 'Diagrammelement hinzufügen', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [schluessel, name] of DIAGRAMMTEILE) {
      const an = q[schluessel] !== false;
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile'
        + (an ? ' designtafel__zeile--gilt' : '');
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        diagrammNeuZeichnen(bild, Object.assign({}, q, { [schluessel]: !an }));
      });
      tafel.appendChild(k);
    }
  });
});

const SCHNELLLAYOUTS = [
  ['voll',   'Mit Titel, Legende und Werten', { titel: true,  legende: true,  werte: true }],
  ['schlicht','Nur die Balken',               { titel: false, legende: false, werte: false }],
  ['zahlen', 'Mit Werten, ohne Legende',      { titel: true,  legende: false, werte: true }],
  ['legende','Mit Legende, ohne Werte',       { titel: true,  legende: true,  werte: false }],
];

B.diagrammLayout = (knopf) => mitDiagramm((bild, q) => {
  designTafelZeigen(knopf, 'Schnelllayout', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [, name, wie] of SCHNELLLAYOUTS) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        diagrammNeuZeichnen(bild, Object.assign({}, q, wie));
      });
      tafel.appendChild(k);
    }
  });
});

B.diagrammFarbe = (knopf) => mitDiagramm((bild, q) => {
  designTafelZeigen(knopf, 'Farbe ändern', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [kuerzel, name, farben] of DIAGRAMMSAETZE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__wahl'
        + ((q.satz || 'bunt') === kuerzel ? ' designtafel__wahl--an' : '');
      const streifen = document.createElement('span');
      streifen.className = 'designtafel__streifen';
      for (const c of farben) {
        const i = document.createElement('i');
        i.style.background = c;
        streifen.appendChild(i);
      }
      const w = document.createElement('span');
      w.className = 'designtafel__name';
      w.textContent = name;
      k.append(streifen, w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        diagrammNeuZeichnen(bild, Object.assign({}, q, { satz: kuerzel }));
      });
      tafel.appendChild(k);
    }
  });
});

/* „Diagrammtyp aendern" — in seinem Bild stehen die Typen als kleine
   Zeichen daneben, nicht in einem Fenster. */
const DIAGRAMMARTEN = [
  ['balken', 'Balken', 'saeule'],
  ['linie',  'Linie',  'linie'],
  ['kuchen', 'Kreis',  'kreis'],
];

B.diagrammArt = (art) => mitDiagramm((bild, q) =>
  diagrammNeuZeichnen(bild, Object.assign({}, q, { art })));

/* Die Formatvorlagen aus seinem Bild: vier Kacheln, jede zeigt
   dasselbe Diagramm in einer anderen Aufmachung. Man waehlt ein
   Aussehen, nicht eine Einstellung. */
const DIAGRAMMSTILE = [
  ['schlicht', 'Schlicht',      { satz: 'bunt',  werte: false, legende: true }],
  ['zahlen',   'Mit Zahlen',    { satz: 'bunt',  werte: true,  legende: true }],
  ['blau',     'Blau, ruhig',   { satz: 'blau',  werte: false, legende: true }],
  ['grau',     'Grau, sachlich',{ satz: 'grau',  werte: true,  legende: false }],
  ['warm',     'Warm',          { satz: 'warm',  werte: false, legende: true }],
];

/* ============================================================
   DOPPELKLICK AUF EIN EINZELNES STUECK

   Aus seiner Beschreibung: „Ein Doppelklick auf ein beliebiges Element
   des Diagramms (z. B. eine einzelne Saeule oder den Hintergrund)
   oeffnet das rechte Formatierungsmenue fuer individuelle Farben,
   Schatten und Linienstaerken."

   Ich hatte den Punkt aufgezaehlt statt gebaut. Er hat gefragt, warum.
   Es gab keinen Grund.

   JEDES STUECK TRAEGT SEINEN NAMEN — wert-0, wert-1, grund, titel,
   linie. Was jemand daran aendert, steht am Diagramm und ueberlebt das
   Neuzeichnen: Wer eine Saeule rot macht und danach die Zahlen aendert,
   will sie nicht wieder blau vorfinden.
   ============================================================ */
const TEILNAMEN = {
  grund: 'Hintergrund',
  titel: 'Diagrammtitel',
  linie: 'Linie',
};

function teilName(teil, punkte) {
  if (TEILNAMEN[teil]) return TEILNAMEN[teil];
  const m = /^wert-(\d+)$/.exec(teil);
  if (m) {
    const p = punkte[Number(m[1])];
    return p ? p.name || ('Wert ' + (Number(m[1]) + 1)) : 'Wert';
  }
  return 'Element';
}

/* Was jemand von Hand gesetzt hat, nach dem Neuzeichnen wieder
   auftragen. */
function teileAnwenden(svg, teile) {
  if (!svg || !teile) return;
  for (const [teil, wie] of Object.entries(teile)) {
    const el = svg.querySelector('[data-teil="' + teil + '"]');
    if (!el) continue;
    if (wie.farbe) el.setAttribute('fill', wie.farbe);
    if (wie.randfarbe) el.setAttribute('stroke', wie.randfarbe);
    if (wie.rand !== undefined) el.setAttribute('stroke-width', wie.rand);
    el.style.filter = wie.schatten
      ? 'drop-shadow(2px 3px 3px rgba(0,0,0,.35))' : '';
  }
}

let formatleiste = null;

function formatleisteWeg() {
  if (formatleiste) { formatleiste.remove(); formatleiste = null; }
}

/* Die Leiste steht rechts, wie in seiner Beschreibung — nicht als
   Fenster ueber dem Blatt. Man sieht das Diagramm und aendert daneben. */
function diagrammTeilFormat(svg, teil) {
  formatleisteWeg();
  const q = quelleLesen(svg) || {};
  const punkte = zahlenLesen(q.daten || '');
  const teile = Object.assign({}, q.teile || {});
  const wie = Object.assign({ farbe: '', randfarbe: '', rand: 0, schatten: false },
                            teile[teil] || {});

  const el = svg.querySelector('[data-teil="' + teil + '"]');
  const kasten = document.createElement('aside');
  kasten.className = 'formatleiste';

  const kopf = document.createElement('div');
  kopf.className = 'formatleiste__kopf';
  const wort = document.createElement('strong');
  wort.textContent = teilName(teil, punkte);
  const zu = document.createElement('button');
  zu.type = 'button';
  zu.className = 'formatleiste__zu';
  zu.textContent = '×';
  zu.title = 'Schließen';
  zu.addEventListener('click', formatleisteWeg);
  kopf.append(wort, zu);
  kasten.appendChild(kopf);

  const satz = document.createElement('p');
  satz.className = 'formatleiste__satz';
  satz.textContent = 'Gilt nur für dieses Stück. Über „Formatvorlage '
                   + 'zurücksetzen" ist es wieder wie vorher.';
  kasten.appendChild(satz);

  const merken = () => {
    teile[teil] = wie;
    svg.dataset.quelle = JSON.stringify(Object.assign({}, q, { teile }));
    teileAnwenden(svg, teile);
    geaendertMelden();
  };

  const zeile = (name, bauen) => {
    const l = document.createElement('label');
    l.className = 'formatleiste__zeile';
    const w = document.createElement('span');
    w.textContent = name;
    l.appendChild(w);
    l.appendChild(bauen());
    kasten.appendChild(l);
  };

  zeile('Farbe', () => {
    const f = document.createElement('input');
    f.type = 'color';
    f.value = wie.farbe || (el && el.getAttribute('fill')) || '#2F6FB5';
    f.addEventListener('input', () => { wie.farbe = f.value; merken(); });
    return f;
  });

  zeile('Linienfarbe', () => {
    const f = document.createElement('input');
    f.type = 'color';
    f.value = wie.randfarbe || '#111417';
    f.addEventListener('input', () => { wie.randfarbe = f.value; merken(); });
    return f;
  });

  zeile('Linienstärke', () => {
    const n = document.createElement('input');
    n.type = 'number'; n.min = '0'; n.max = '8'; n.step = '0.5';
    n.value = String(wie.rand || 0);
    n.addEventListener('input', () => {
      wie.rand = Math.max(0, Math.min(8, parseFloat(n.value) || 0));
      merken();
    });
    return n;
  });

  zeile('Schatten', () => {
    const h = document.createElement('input');
    h.type = 'checkbox';
    h.checked = !!wie.schatten;
    h.addEventListener('change', () => { wie.schatten = h.checked; merken(); });
    return h;
  });

  const weg = document.createElement('button');
  weg.type = 'button';
  weg.className = 'knopf formatleiste__zurueck';
  weg.textContent = 'Dieses Stück zurücksetzen';
  weg.addEventListener('click', () => {
    delete teile[teil];
    svg.dataset.quelle = JSON.stringify(Object.assign({}, q, { teile }));
    diagrammNeuZeichnen(svg, Object.assign({}, q, { teile }));
    formatleisteWeg();
  });
  kasten.appendChild(weg);

  document.body.appendChild(kasten);
  formatleiste = kasten;
}

/* Doppelklick im Blatt: Welches Stueck war gemeint? */
feld.addEventListener('dblclick', (e) => {
  const svg = e.target && e.target.closest ? e.target.closest('svg.diagramm') : null;
  if (!svg) return;
  const stueck = e.target.closest('[data-teil]');
  if (!stueck) return;
  e.preventDefault();
  diagrammTeilFormat(svg, stueck.dataset.teil);
});

B.diagrammStile = (knopf) => mitDiagramm((bild, q) => {
  designTafelZeigen(knopf, 'Formatvorlagen', (tafel) => {
    tafel.classList.add('designtafel--breit');
    const gitter = document.createElement('div');
    gitter.className = 'stilgitter';
    const punkte = zahlenLesen(q.daten || '');
    for (const [, name, wie] of DIAGRAMMSTILE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'stilkachel';
      k.title = name;
      const bildchen = document.createElement('span');
      bildchen.className = 'stilkachel__bild';
      bildchen.innerHTML = diagrammZeichnen(q.art, punkte.slice(0, 4), '', {
        farben: diagrammSatz(wie.satz), werte: wie.werte, legende: wie.legende,
      });
      const w = document.createElement('span');
      w.className = 'stilkachel__name';
      w.textContent = name;
      k.append(bildchen, w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        diagrammNeuZeichnen(bild, Object.assign({}, q, wie));
      });
      gitter.appendChild(k);
    }
    tafel.appendChild(gitter);
  });
});

B.diagrammZurueck = () => mitDiagramm((bild, q) =>
  diagrammNeuZeichnen(bild, {
    art: q.art, titel: q.titel, daten: q.daten,
    titelAn: true, legende: true, werte: false, satz: 'bunt', teile: {},
  }));

/* ============================================================
   DIE KNOEPFE AM DIAGRAMM

   „vergiss die Bearbeitungsfunktionen nicht rechts am Diagramm."

   Auf seinem WPS-Bild haengen fuenf kleine Knoepfe an der rechten Kante
   des gewaehlten Diagramms. Sie sind dort, wo man hinsieht: Man aendert
   ein Diagramm nicht, indem man in die Leiste hinaufgreift, sondern
   indem man es ansieht und danebengreift.

   Gebaut wie die Knoepfe am Bild — dieselben Klassen, dieselbe Stelle,
   dasselbe Verhalten. Ein zweites System dafuer waere der Fehler, den
   ich heute schon einmal gemacht habe.
   ============================================================ */
const DIAGRAMMSCHNELL = [
  { art: 'layout', bild: 'anordnen',   name: 'Schnelllayout',
    tun: (k) => B.diagrammLayout(k) },
  { art: 'teile',  bild: 'saeule',     name: 'Diagrammelement hinzufügen',
    tun: (k) => B.diagrammElement(k) },
  { art: 'farbe',  bild: 'pinselchen', name: 'Farbe ändern',
    tun: (k) => B.diagrammFarbe(k) },
  { art: 'daten',  bild: 'filter',     name: 'Daten auswählen',
    tun: () => B.diagrammDaten() },
  { art: 'form',   bild: 'zahnrad',    name: 'Formatieren',
    tun: () => B.diagrammFormat() },
];

/* Die Schnellknoepfe am Diagramm. Die Griffe, das Ziehen, das
   Loeschkreuz kommen aus dem Bildsystem — siehe GEGENSTAENDE weiter
   unten. Hier steht nur noch, WAS neben einem Diagramm zu stehen hat.

   Vorher stand hier ein zweites Griffsystem, das ich neben das
   vorhandene gebaut hatte. Er hat es gesehen: „schau doch einfach bei
   den Bildern und Tabellen rein, da liegen die Funktionen schon." */
B.diagrammEntwurf = () => diagrammFenster('Diagrammentwurf', false);
/* B.diagrammDaten steht weiter oben und oeffnet die Tabelle.
   Hier stand die alte Fassung mit dem Textkasten — zwei gleichnamige
   Zuweisungen, von denen die spaetere gewinnt: Die Tabelle waere nie
   aufgegangen. */

B.diagrammTyp = () => {
  const bild = diagrammJetzt();
  if (!bild) { melde('Im Text steht kein Diagramm.'); return; }
  const q = quelleLesen(bild);
  if (!q) { melde('Dieses Diagramm trägt seine Zahlen nicht mit.'); return; }
  fenster('Diagrammtyp', [
    { schluessel: 'art', name: 'Art', art: 'auswahl', wert: q.art,
      werte: [['balken', 'Balken'], ['linie', 'Linie'], ['kuchen', 'Kreis']] },
  ], (werte) => diagrammNeuZeichnen(bild, Object.assign({}, q, { art: werte.art })));
};

B.diagrammFormat = () => {
  const bild = diagrammJetzt();
  if (!bild) { melde('Im Text steht kein Diagramm.'); return; }
  fenster('Formatierung', [
    { art: 'satz', text: 'Wie groß das Diagramm im Text steht.' },
    { schluessel: 'breite', name: 'Breite (Bildpunkte)', art: 'number',
      wert: String(bild.getAttribute('width') || 480), schritt: '20' },
  ], (werte) => {
    const b = Math.max(120, Math.min(1600, Number(werte.breite) || 480));
    const kasten = (bild.getAttribute('viewBox') || '0 0 480 260').split(/\s+/);
    const verhaeltnis = (Number(kasten[3]) || 260) / (Number(kasten[2]) || 480);
    bild.setAttribute('width', b);
    bild.setAttribute('height', Math.round(b * verhaeltnis));
    geaendertMelden();
    melde('Größe geändert.');
  });
};

function diagrammNeuZeichnen(alt, q) {
  const punkte = zahlenLesen(q.daten);
  if (!punkte.length) { melde('Darin standen keine Zahlen, mit denen sich zeichnen ließe.'); return; }
  const wie = { farben: diagrammSatz(q.satz), werte: q.werte, legende: q.legende };
  const titel = q.titel === false ? '' : (q.titel || '').trim();
  if (objektErsetzen(alt, merkeQuelle(diagrammZeichnen(q.art, punkte, titel, wie), q))) {
    /* Was jemand an einzelnen Stuecken geaendert hat, wieder auftragen —
       sonst waere eine rot gemachte Saeule nach der naechsten
       Zahlenaenderung wieder blau. */
    const neu = feld.querySelector('svg.diagramm[data-quelle*="' + (q.art || '') + '"]');
    teileAnwenden(neu || feld.querySelector('svg.diagramm'), q.teile);
    melde('Diagramm mit ' + punkte.length + ' Werten geändert.');
  }
}

/* ---- SmartArt-Werkzeuge ---- */

/* ============================================================
   SMARTART: ZWEI REITER, WIE AUF SEINEN BILDERN

   „Falsche Funktion. Funktion ist nach WPS-Bildvorlage zu bauen +
   Diagrammfunktionen. Im Reiter erscheinen dann zwei neue Reiter, siehe
   Bilder."

   In WPS heissen sie „WPSArt-Design" und „WPSArt-Format". Hier
   „SmartArt-Entwurf" und „SmartArt-Format", wie es sein SOLL vorgibt.

   Vorher stand dahinter je ein grosser Knopf, der ein Fenster oeffnete —
   zwei Reiter mit je einem Knopf. Auf seinem Bild stehen im Entwurf
   acht Befehle, eine Farbklappe, eine Stilgalerie und die Groesse.
   ============================================================ */
const SMARTARTFARBEN = [
  ['bunt',   'Bunt',       ['#2F6FB5', '#3E9C7A', '#C08A2E', '#B5563F', '#7A5EA8', '#1F7A5A']],
  ['blau',   'Blautöne',   ['#1F4E79', '#2F6FB5', '#4A8BCB', '#6FA6DA', '#9BC3E8', '#C6DDF3']],
  ['warm',   'Warm',       ['#8A3324', '#B5563F', '#C08A2E', '#D08A3E', '#A0522D', '#C9A227']],
  ['gruen',  'Grüntöne',   ['#1F7A5A', '#3E9C7A', '#6BB79A', '#93CDB7', '#BCE0D3', '#7A8C2E']],
  ['grau',   'Graustufen', ['#3A4149', '#5C666F', '#8B949C', '#A8B0B7', '#C4CACF', '#DDE1E4']],
];

function mitSmartart(tun) {
  const bild = smartartJetzt();
  if (!bild) { melde('Dafür muss ein SmartArt gewählt sein.'); return null; }
  const q = quelleLesen(bild);
  if (!q) { melde('Dieses SmartArt trägt seine Kästen nicht mit.'); return null; }
  return tun(bild, q);
}

function smartartNeu(bild, q) {
  const schritte = String(q.text || '').split(/\r?\n/)
    .map((z) => z.trim()).filter(Boolean).slice(0, 8);
  if (!schritte.length) { melde('Da stand keine Zeile.'); return; }
  const bauer = { ablauf: smartartAblauf, kreis: smartartKreis,
                  gliederung: smartartGliederung, liste: smartartListe }[q.art] || smartartAblauf;
  const farben = (SMARTARTFARBEN.find(([k]) => k === q.satz) || SMARTARTFARBEN[0])[2];
  /* DIE KLASSE MUSS MIT. svgHuelle() schreibt „diagramm" an jedes SVG;
     erst „smartart" daneben trennt die beiden. Ohne sie war das
     umgebaute SmartArt fuer alle Werkzeuge ein Diagramm — und fuer
     smartartJetzt() gar nicht mehr da. */
  const neuesSvg = merkeQuelle(bauer(schritte, farben), q)
    .replace('class="diagramm"', 'class="diagramm smartart"');
  if (objektErsetzen(bild, neuesSvg)) {
    melde('SmartArt geändert.');
  }
}

/* „Form einfuegen" — ein Kasten mehr. In WPS haengt daran eine Klappe
   mit „davor" und „dahinter"; hier dasselbe, weil ein Ablauf sonst nur
   hinten waechst. */
B.smartartFormEin = (knopf) => mitSmartart((bild, q) => {
  designTafelZeigen(knopf, 'Form einfügen', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [name, wohin] of [['Dahinter einfügen', 'hinten'],
                                 ['Davor einfügen', 'vorn']]) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      k.appendChild(symbol('smartart'));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        const zeilen = String(q.text || '').split(/\r?\n/).filter(Boolean);
        if (zeilen.length >= 8) { melde('Acht Kästen sind genug — mehr liest niemand.'); return; }
        if (wohin === 'vorn') zeilen.unshift('Neuer Schritt');
        else zeilen.push('Neuer Schritt');
        smartartNeu(bild, Object.assign({}, q, { text: zeilen.join('\n') }));
      });
      tafel.appendChild(k);
    }
  });
});

/* Vorwaerts und Rueckwaerts: den letzten Kasten nach vorn oder hinten
   schieben. In WPS bezieht es sich auf den gewaehlten; hier gibt es
   keine Auswahl einzelner Kaesten, darum auf den letzten. */
B.smartartVor = () => mitSmartart((bild, q) => {
  const z = String(q.text || '').split(/\r?\n/).filter(Boolean);
  if (z.length < 2) { melde('Dafür braucht es mindestens zwei Kästen.'); return; }
  z.unshift(z.pop());
  smartartNeu(bild, Object.assign({}, q, { text: z.join('\n') }));
});
B.smartartZurueck = () => mitSmartart((bild, q) => {
  const z = String(q.text || '').split(/\r?\n/).filter(Boolean);
  if (z.length < 2) { melde('Dafür braucht es mindestens zwei Kästen.'); return; }
  z.push(z.shift());
  smartartNeu(bild, Object.assign({}, q, { text: z.join('\n') }));
});

B.smartartUmdrehen = () => mitSmartart((bild, q) => {
  const z = String(q.text || '').split(/\r?\n/).filter(Boolean).reverse();
  smartartNeu(bild, Object.assign({}, q, { text: z.join('\n') }));
  melde('Reihenfolge umgedreht.');
});

const SMARTARTFORMEN = [
  ['ablauf',     'Ablauf (Pfeile)'],
  ['kreis',      'Kreislauf'],
  ['gliederung', 'Gliederung'],
  ['liste',      'Liste mit Kästen'],
];

B.smartartLayout = (knopf) => mitSmartart((bild, q) => {
  designTafelZeigen(knopf, 'Layout', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [kuerzel, name] of SMARTARTFORMEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile'
        + (q.art === kuerzel ? ' richtungszeile--gilt' : '');
      k.appendChild(symbol('smartart'));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        smartartNeu(bild, Object.assign({}, q, { art: kuerzel }));
      });
      tafel.appendChild(k);
    }
  });
});

B.smartartFarben = (knopf) => mitSmartart((bild, q) => {
  designTafelZeigen(knopf, 'Farben ändern', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [kuerzel, name, farben] of SMARTARTFARBEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__wahl'
        + ((q.satz || 'bunt') === kuerzel ? ' designtafel__wahl--an' : '');
      const streifen = document.createElement('span');
      streifen.className = 'designtafel__streifen';
      for (const c of farben) {
        const i = document.createElement('i');
        i.style.background = c;
        streifen.appendChild(i);
      }
      const w = document.createElement('span');
      w.className = 'designtafel__name';
      w.textContent = name;
      k.append(streifen, w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        smartartNeu(bild, Object.assign({}, q, { satz: kuerzel }));
      });
      tafel.appendChild(k);
    }
  });
});

B.smartartText = () => mitSmartart((bild, q) => {
  fenster('Kästen bearbeiten', [
    { art: 'satz', text: 'Je Zeile ein Kasten. Bei der Gliederung ist die '
                       + 'erste Zeile oben. Mehr als acht liest niemand.' },
    { schluessel: 'text', name: 'Kästen', art: 'flaeche', zeilen: 8, wert: q.text || '' },
  ], (werte) => smartartNeu(bild, Object.assign({}, q, { text: werte.text })), 'Übernehmen');
});

/* Der zweite Reiter faerbt: Kontur und Effekt am ganzen SmartArt. */
B.smartartKontur = (knopf) => mitSmartart((bild) => {
  designTafelZeigen(knopf, 'Kontur', (tafel) => {
    tafel.classList.add('designtafel--breit', 'farbtafel');
    const reihe = document.createElement('div');
    reihe.className = 'farbtafel__reihe farbtafel__reihe--zwoelf';
    for (const [hex, name] of FARBEN) {
      const feldchen = farbfeld(hex, () => {
        designTafelWeg();
        for (const teil of bild.querySelectorAll('rect, circle, ellipse, path')) {
          if (teil.getAttribute('fill') === 'none') continue;
          teil.setAttribute('stroke', hex);
          teil.setAttribute('stroke-width', '1.5');
        }
        geaendertMelden();
        melde('Kontur: ' + name + '.');
      });
      feldchen.title = name;
      reihe.appendChild(feldchen);
    }
    tafel.appendChild(reihe);

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    const ohne = document.createElement('button');
    ohne.type = 'button';
    ohne.className = 'designtafel__zeile richtungszeile';
    ohne.appendChild(symbol('radierer'));
    const w = document.createElement('span');
    w.textContent = 'Keine Kontur';
    ohne.appendChild(w);
    ohne.addEventListener('mousedown', (e) => e.preventDefault());
    ohne.addEventListener('click', () => {
      designTafelWeg();
      for (const teil of bild.querySelectorAll('[stroke]')) {
        if (teil.getAttribute('fill') === 'none') continue;
        teil.removeAttribute('stroke');
        teil.removeAttribute('stroke-width');
      }
      geaendertMelden();
      melde('Kontur entfernt.');
    });
    tafel.appendChild(ohne);
  });
});

B.smartartEffekt = (knopf) => mitSmartart((bild) => {
  designTafelZeigen(knopf, 'Effekte', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [, name, filter] of DESIGNEFFEKTE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      const probe = document.createElement('span');
      probe.className = 'rahmenprobe--klein';
      probe.style.filter = filter || 'none';
      k.appendChild(probe);
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        bild.style.filter = filter || '';
        geaendertMelden();
        melde('Effekt: ' + name + '.');
      });
      tafel.appendChild(k);
    }
  });
});

B.smartartGroesse = () => mitSmartart((bild) => {
  const r = bild.getBoundingClientRect();
  fenster('Größe', [
    { art: 'satz', text: 'In Millimetern. Die Höhe folgt der Breite.' },
    { schluessel: 'breite', name: 'Breite (mm)', art: 'number',
      wert: String(Math.round(inMillimeter(r.width / ((zoom || 100) / 100)))) },
  ], (werte) => {
    const mm = Math.max(30, Math.min(400, parseFloat(werte.breite) || 120));
    bild.style.width = mm + 'mm';
    bild.style.height = 'auto';
    geaendertMelden();
    melde('Breite: ' + mm + ' mm.');
  });
});

function smartartFenster(titel, nurForm) {
  const bild = smartartJetzt();
  if (!bild) { melde('Im Text steht kein SmartArt.'); return; }
  const q = quelleLesen(bild);
  if (!q) {
    melde('Dieses SmartArt stammt aus einer älteren Fassung — '
        + 'es trägt seine Kästen nicht mit und lässt sich nur neu einfügen.');
    return;
  }
  const felder = [{ schluessel: 'art', name: 'Form', art: 'auswahl', wert: q.art, werte: [
    ['ablauf', 'Ablauf (Pfeile)'], ['kreis', 'Kreislauf'],
    ['gliederung', 'Gliederung'], ['liste', 'Liste mit Kästen'],
  ] }];
  if (!nurForm) {
    felder.unshift({ art: 'satz', text: 'Je Zeile ein Kasten.' });
    felder.push({ schluessel: 'text', name: 'Kästen', art: 'flaeche', zeilen: 6, wert: q.text || '' });
  }
  fenster(titel, felder, (werte) => {
    const neuQ = { art: werte.art, text: nurForm ? q.text : werte.text };
    const schritte = String(neuQ.text).split(/\r?\n/).map((z) => z.trim()).filter(Boolean).slice(0, 8);
    if (!schritte.length) { melde('Da stand keine Zeile.'); return; }
    const bauer = { ablauf: smartartAblauf, kreis: smartartKreis,
                    gliederung: smartartGliederung, liste: smartartListe }[neuQ.art] || smartartAblauf;
    const neu = merkeQuelle(bauer(schritte), neuQ)
      .replace('class="diagramm"', 'class="diagramm smartart"');
    if (objektErsetzen(bild, neu)) melde('SmartArt mit ' + schritte.length + ' Kästen geändert.');
  });
}

B.smartartEntwurf = () => smartartFenster('SmartArt-Entwurf', false);
B.smartartFormat  = () => smartartFenster('SmartArt-Format', true);

/* ---- Tabellenwerkzeuge: was noch fehlte ---- */

B.zellengroesse = () => mitTabelle((zelle, zeile, tabelle) => {
  fenster('Zellengröße', [
    { art: 'satz', text: 'Gilt für die Spalte, in der der Zeiger steht.' },
    { schluessel: 'breite', name: 'Breite (mm, 0 = automatisch)', art: 'number',
      wert: '0', schritt: '5' },
    { schluessel: 'hoehe', name: 'Zeilenhöhe (mm, 0 = automatisch)', art: 'number',
      wert: '0', schritt: '2' },
  ], (werte) => {
    const spalte = [...zeile.cells].indexOf(zelle);
    const breite = Number(werte.breite) || 0;
    const hoehe = Number(werte.hoehe) || 0;
    if (breite > 0) {
      for (const r of tabelle.rows) {
        if (r.cells[spalte]) r.cells[spalte].style.width = breite + 'mm';
      }
    }
    if (hoehe > 0) zeile.style.height = hoehe + 'mm';
    geaendertMelden();
    melde('Zellengröße gesetzt.');
  });
});

B.zellenAusrichtung = () => mitTabelle((zelle, zeile, tabelle) => {
  fenster('Ausrichtung', [
    { art: 'satz', text: 'Gilt für die Zelle, in der der Zeiger steht.' },
    { schluessel: 'quer', name: 'Waagerecht', art: 'auswahl', werte: [
      ['left', 'Links'], ['center', 'Zentriert'], ['right', 'Rechts'] ] },
    { schluessel: 'hoch', name: 'Senkrecht', art: 'auswahl', werte: [
      ['top', 'Oben'], ['middle', 'Mitte'], ['bottom', 'Unten'] ] },
    { schluessel: 'wofuer', name: 'Wofür', art: 'auswahl', werte: [
      ['zelle', 'Nur diese Zelle'], ['zeile', 'Ganze Zeile'], ['tabelle', 'Ganze Tabelle'] ] },
  ], (werte) => {
    const ziel = werte.wofuer === 'tabelle' ? [...tabelle.querySelectorAll('td, th')]
               : werte.wofuer === 'zeile' ? [...zeile.cells]
               : [zelle];
    for (const z of ziel) {
      z.style.textAlign = werte.quer;
      z.style.verticalAlign = werte.hoch;
    }
    geaendertMelden();
    melde(ziel.length === 1 ? 'Zelle ausgerichtet.' : ziel.length + ' Zellen ausgerichtet.');
  });
});

/* ============================================================
   DIE EIGENSCHAFTEN EINER TABELLE

   Hier stand „Tabellenformatierung": zwei Klappfelder, Streifen und
   Rahmen. Zwei Dinge fehlten, und beide hat Kay benannt — eine Vorlage,
   die man der Tabelle im Ganzen geben kann, und eine farbige erste Zeile.

   Ein dritter Fehler fiel dabei auf: Das alte Fenster LAS den Zustand
   nicht. Es ging an einer gestreiften Tabelle mit „Nein" auf, und wer
   nur den Rahmen ändern wollte, nahm die Streifen versehentlich mit.
   Ein Fenster, das den Ist-Zustand nicht zeigt, ist kein Fenster zum
   Ändern, sondern eines zum Neusetzen.

   ES ZEIGT, WÄHREND ES OFFEN STEHT. fenster() kann das über „beiWechsel":
   Jede Änderung wirkt sofort auf die Tabelle im Blatt. Wer eine Farbe
   wählt, sieht sie an seiner eigenen Tabelle, nicht an einem Muster.
   „Abbrechen" setzt über „beiAb" den Stand von vorher zurück — dafür wird
   beim Aufgehen das ganze outerHTML weggelegt.
   ============================================================ */

/* Die Vorlagen. Jede ist nur ein Satz Werte für dieselben Felder — wer
   eine wählt, sieht die Felder darunter mitwandern und kann danach
   einzeln nachbessern. Genau das meint „Vorlage": ein Anfang, keine
   Sperre. */
const TABELLENVORLAGEN = {
  einfach:   { kopf: 'nein', kopffarbe: '#E8EDF3', streifen: 'nein',
               streifenfarbe: '#F2F4F7', linien: 'alle', linienfarbe: '#9AA3AB',
               breite: 'ganz', stellung: 'links', abstand: '6' },
  kopfzeile: { kopf: 'ja',   kopffarbe: '#D6E4F0', streifen: 'nein',
               streifenfarbe: '#F2F4F7', linien: 'alle', linienfarbe: '#9AA3AB',
               breite: 'ganz', stellung: 'links', abstand: '6' },
  gestreift: { kopf: 'ja',   kopffarbe: '#D6E4F0', streifen: 'ja',
               streifenfarbe: '#F2F4F7', linien: 'keine', linienfarbe: '#9AA3AB',
               breite: 'ganz', stellung: 'links', abstand: '7' },
  liste:     { kopf: 'ja',   kopffarbe: '#FFFFFF', streifen: 'nein',
               streifenfarbe: '#F2F4F7', linien: 'aussen', linienfarbe: '#4C555E',
               breite: 'ganz', stellung: 'links', abstand: '7' },
  ohne:      { kopf: 'nein', kopffarbe: '#E8EDF3', streifen: 'nein',
               streifenfarbe: '#F2F4F7', linien: 'keine', linienfarbe: '#9AA3AB',
               breite: 'inhalt', stellung: 'links', abstand: '4' },
};

/* Eine Farbe aus dem Blatt in die Form bringen, die <input type="color">
   versteht: immer #rrggbb. Der Browser gibt "rgb(214, 228, 240)" zurück,
   und ein leeres Feld gibt "" — beides würde den Farbwähler auf Schwarz
   stellen, und der Anwender bekäme eine Farbe, die er nie gewählt hat. */
function farbeAlsHex(wert, ersatz) {
  if (!wert) return ersatz;
  const t = String(wert).trim();
  if (/^#[0-9a-f]{6}$/i.test(t)) return t;
  const m = t.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
  if (!m) return ersatz;
  const hex = (n) => Number(n).toString(16).padStart(2, '0');
  return '#' + hex(m[1]) + hex(m[2]) + hex(m[3]);
}

/* Den Ist-Zustand aus der Tabelle herauslesen. Gefragt wird das Blatt
   selbst, nicht ein gemerkter Wert: Eine Tabelle kann aus einem Word-
   Dokument gekommen sein, und dann hat nie jemand hier etwas eingestellt. */
/* NICHT „tabelleLesen" — den Namen gibt es weiter unten schon, und zwar
   fuer etwas ganz anderes: Sie macht aus Rohdaten eine Tabelle. Zwei
   Funktionen desselben Namens in derselben Datei sind kein Fehler, den
   irgendwer meldet — die spaetere gewinnt stillschweigend, und der
   Aufruf hier bekam ploetzlich null zurueck. */
function tabellenstandLesen(tabelle) {
  const ersteZeile = tabelle.rows[0];
  const kopf = !!(ersteZeile && ersteZeile.children[0]
                  && ersteZeile.children[0].tagName === 'TH');
  const kopfZelle = ersteZeile && ersteZeile.children[0];
  const zweiteZeile = tabelle.rows[1];
  const zweiteZelle = zweiteZeile && zweiteZeile.cells[0];

  const irgendeine = tabelle.querySelector('td, th');
  const randStil = irgendeine ? getComputedStyle(irgendeine) : null;
  const zelleRand = randStil && randStil.borderTopStyle !== 'none'
                 && parseFloat(randStil.borderTopWidth) > 0;
  const tabelleRand = getComputedStyle(tabelle).borderTopStyle !== 'none'
                   && parseFloat(getComputedStyle(tabelle).borderTopWidth) > 0;

  return {
    vorlage: 'eigene',
    kopf: kopf ? 'ja' : 'nein',
    kopffarbe: farbeAlsHex(kopfZelle && kopfZelle.style.background, '#D6E4F0'),
    /* Gestreift heißt: die ZWEITE Zeile ist getönt. Die erste kann die
       Kopfzeile sein und hat ihre eigene Farbe. */
    streifen: (zweiteZelle && zweiteZelle.style.background) ? 'ja' : 'nein',
    streifenfarbe: farbeAlsHex(zweiteZelle && zweiteZelle.style.background, '#F2F4F7'),
    linien: zelleRand ? 'alle' : (tabelleRand ? 'aussen' : 'keine'),
    linienfarbe: farbeAlsHex(randStil && randStil.borderTopColor, '#9AA3AB'),
    breite: tabelle.style.width === 'auto' ? 'inhalt' : 'ganz',
    stellung: tabelle.style.marginLeft === 'auto'
      ? (tabelle.style.marginRight === 'auto' ? 'mitte' : 'rechts') : 'links',
    abstand: String(Math.round(parseFloat(
      (irgendeine && getComputedStyle(irgendeine).paddingTop) || '6')) || 6),
  };
}

/* Die erste Zeile zu <th> machen oder zurück zu <td>.

   Der Inhalt wandert mit, die Auszeichnung nicht: Ein <th> ist fett und
   mittig, weil es eine Überschrift IST — das gehört zur Bedeutung, nicht
   zur Farbe. */
function kopfzeileSetzen(tabelle, an) {
  const erste = tabelle.rows[0];
  if (!erste) return;
  const istKopf = erste.children[0] && erste.children[0].tagName === 'TH';
  if (istKopf === an) return;
  for (const z of [...erste.children]) {
    const neu = document.createElement(an ? 'th' : 'td');
    neu.innerHTML = z.innerHTML;
    neu.style.cssText = z.style.cssText;
    z.replaceWith(neu);
  }
}

function tabelleAnwenden(tabelle, w) {
  kopfzeileSetzen(tabelle, w.kopf === 'ja');

  const abstand = Math.max(0, Math.min(40, parseInt(w.abstand, 10) || 0));
  tabelle.style.width = w.breite === 'inhalt' ? 'auto' : '100%';
  /* Ausrichten geht über die Außenabstände: „auto" links UND rechts ist
     mittig, nur links ist rechtsbündig. Das ist die Art, wie ein Blatt
     rechnet — nicht text-align, das richtet den Inhalt der Zellen aus. */
  tabelle.style.marginLeft = (w.stellung === 'mitte' || w.stellung === 'rechts') ? 'auto' : '';
  tabelle.style.marginRight = (w.stellung === 'mitte') ? 'auto' : '';
  tabelle.style.borderCollapse = 'collapse';
  tabelle.style.border = w.linien === 'keine'
    ? 'none' : '1px solid ' + w.linienfarbe;

  [...tabelle.rows].forEach((zeile, nr) => {
    const istKopf = nr === 0 && w.kopf === 'ja';
    for (const z of zeile.cells) {
      z.style.border = w.linien === 'alle' ? '1px solid ' + w.linienfarbe : 'none';
      z.style.padding = abstand + 'px';
      /* Die Reihenfolge entscheidet: Die Kopfzeile hat ihre eigene Farbe
         und wird vom Streifenmuster nicht überschrieben. Sonst bekäme sie
         bei „gestreift" die Streifenfarbe, obwohl daneben eine eigene
         Kopffarbe steht — und die Einstellung sähe kaputt aus. */
      if (istKopf) z.style.background = w.kopffarbe;
      else if (w.streifen === 'ja' && nr % 2 === 1) z.style.background = w.streifenfarbe;
      else z.style.background = '';
    }
  });
}

B.tabelleEigenschaften = () => mitTabelle((zelle, zeile, tabelle) => {
  /* Der Rückweg für „Abbrechen": der ganze Stand von vorher. */
  const vorher = tabelle.outerHTML;
  const ist = tabellenstandLesen(tabelle);
  /* Damit die Tabelle nicht beim Aufgehen des Fensters schon springt,
     merkt sich diese Liste, welche Vorlage zuletzt gewählt war. Erst wenn
     jemand sie umstellt, werden die anderen Felder überschrieben. */
  let vorlageVorher = 'eigene';

  fenster('Eigenschaften der Tabelle', [
    { schluessel: 'vorlage', name: 'Vorlage', art: 'auswahl', wert: 'eigene', werte: [
      ['eigene',    'Eigene Einstellung'],
      ['einfach',   'Einfach — Raster, ohne Farbe'],
      ['kopfzeile', 'Mit Kopfzeile — erste Zeile getönt'],
      ['gestreift', 'Gestreift — jede zweite Zeile getönt'],
      ['liste',     'Liste — nur Linie oben und unten'],
      ['ohne',      'Ohne Rahmen'],
    ] },

    { art: 'satz', text: 'Die erste Zeile' },
    { schluessel: 'kopf', name: 'Erste Zeile als Kopf', art: 'auswahl', wert: ist.kopf,
      werte: [['ja', 'Ja — fett und mittig'], ['nein', 'Nein']] },
    { schluessel: 'kopffarbe', name: 'Farbe der Kopfzeile', art: 'color', wert: ist.kopffarbe },

    { art: 'satz', text: 'Die übrigen Zeilen' },
    { schluessel: 'streifen', name: 'Jede zweite Zeile tönen', art: 'auswahl',
      wert: ist.streifen, werte: [['nein', 'Nein'], ['ja', 'Ja']] },
    { schluessel: 'streifenfarbe', name: 'Farbe der Streifen', art: 'color',
      wert: ist.streifenfarbe },

    { art: 'satz', text: 'Rahmen und Maße' },
    { schluessel: 'linien', name: 'Rahmenlinien', art: 'auswahl', wert: ist.linien, werte: [
      ['alle', 'Um jede Zelle'], ['aussen', 'Nur außen'], ['keine', 'Keine'] ] },
    { schluessel: 'linienfarbe', name: 'Farbe der Linien', art: 'color', wert: ist.linienfarbe },
    { schluessel: 'breite', name: 'Breite', art: 'auswahl', wert: ist.breite, werte: [
      ['ganz', 'Über die ganze Textbreite'], ['inhalt', 'So breit wie der Inhalt'] ] },
    /* Nur sinnvoll, wenn die Tabelle nicht die ganze Breite einnimmt —
       sonst gibt es nichts auszurichten. Das Feld bleibt trotzdem stehen:
       Ein Feld, das mal da ist und mal nicht, lässt sich nicht lernen. */
    { schluessel: 'stellung', name: 'Stellung auf der Seite', art: 'auswahl',
      wert: ist.stellung, werte: [
      ['links', 'Links'], ['mitte', 'Mittig'], ['rechts', 'Rechts'] ] },
    { schluessel: 'abstand', name: 'Luft in den Zellen (Punkt)', art: 'number',
      wert: ist.abstand },
  ],
  () => {
    geaendertMelden();
    melde('Eigenschaften der Tabelle übernommen.');
  },
  'Übernehmen', true,
  /* Abbrechen: den gemerkten Stand zurückschreiben. */
  () => {
    const jetzt = zelleJetzt() && zelleJetzt().closest('table');
    const ziel = jetzt || tabelle;
    if (ziel && ziel.outerHTML !== vorher) {
      const huelle = document.createElement('div');
      huelle.innerHTML = vorher;
      if (huelle.firstElementChild) ziel.replaceWith(huelle.firstElementChild);
    }
  },
  /* Bei jeder Änderung: sofort anwenden. */
  (werte, eingaben) => {
    if (werte.vorlage !== vorlageVorher && werte.vorlage !== 'eigene') {
      const v = TABELLENVORLAGEN[werte.vorlage];
      if (v) for (const [name, wert] of Object.entries(v)) {
        if (eingaben[name]) { eingaben[name].value = wert; werte[name] = wert; }
      }
    }
    vorlageVorher = werte.vorlage;
    tabelleAnwenden(tabelle, werte);
  });
});

/* Der alte Name bleibt als Weg bestehen: Er steht im Rechtsklickmenü und
   im Band, und ein Befehl, den jemand kennt, soll nicht verschwinden. */
B.tabelleFormat = () => B.tabelleEigenschaften();

/* ---- Gleichungswerkzeuge ---- */

B.formelAendern = () => {
  const formel = formelJetzt();
  if (!formel) { melde('Im Text steht keine Formel.'); return; }
  const q = quelleLesen(formel);
  if (!q || !q.formel) {
    melde('Diese Formel stammt aus einer älteren Fassung — '
        + 'sie trägt ihren Text nicht mit und lässt sich nur neu einfügen.');
    return;
  }
  fenster('Formel ändern', [
    { art: 'satz', text: 'So tippen, wie man es sagt:\n'
        + 'x^2   hoch      H_2O   tief\n'
        + '(a+b)/2   Bruch      sqrt(9)   Wurzel' },
    { schluessel: 'formel', name: 'Formel', wert: q.formel },
  ], (werte) => {
    const mathml = formelBauen(werte.formel);
    if (!mathml) return;
    const neu = mathml.replace('<math ', '<math data-quelle="'
      + JSON.stringify({ formel: werte.formel }).replace(/"/g, '&quot;') + '" ');
    if (objektErsetzen(formel, neu)) melde('Formel geändert.');
  });
};

/* Die Seitenzahl steht als Platzhalter da und wird beim Drucken vom Browser
   selbst gefüllt — im Blatt kann sie nicht stimmen, dort gibt es noch keine
   Seiten. */
B.seitennummer = () => {
  if (!fussAn) { fussAn = true; kopfFussAnwenden(); }
  $('fusszeile').focus();
  document.execCommand('insertHTML', false, '<span class="seitenzahl">Seite</span>');
  melde('Die Zahl erscheint beim Drucken.');
};

/* ---- Ansicht: Lineal, Steuerzeichen ---- */
let lineal = Speicher.lies('lineal', false);
/* Zwei Lineale, zwei Schalter — so hält es der WPS Writer, und nur so
   lässt sich der Stand abbilden, den Kay dort eingestellt hat: senkrecht
   an, waagerecht aus. */
let linealHoch = Speicher.lies('linealHoch', false);
let steuerzeichen = Speicher.lies('steuerzeichen', false);
let leistenAn = Speicher.lies('leisten', true);

function ansichtExtras() {
  $('lineal').hidden = !lineal;
  $('lineal-hoch').hidden = !linealHoch;
  /* Die Ecke gehört zum senkrechten: Ohne es hätte sie nichts zu füllen
     und schöbe das waagerechte Lineal nur um ihre Breite nach rechts. */
  $('lineal-ecke').hidden = !linealHoch;
  /* Erst sichtbar machen, dann zeichnen: Ein verstecktes Lineal hat keine
     Breite, und ohne Breite lässt sich nichts ausmessen. */
  if (lineal) linealZeichnen();
  if (linealHoch) linealHochZeichnen();
  feld.classList.toggle('dokument--steuerzeichen', steuerzeichen);
  zeichenAnwenden();
  $('werkzeugleiste').hidden = !leistenAn;
  $('werkzeugleiste2').hidden = !leistenAn;
  /* Die dritte Leiste haengt an denselben Schalter — und daran, ob es
     ueberhaupt etwas zu zeigen gibt. */
  if (typeof zusammenhangsleisteBauen === 'function') zusammenhangsleisteBauen();
  Speicher.schreib('lineal', lineal);
  Speicher.schreib('linealHoch', linealHoch);
  Speicher.schreib('steuerzeichen', steuerzeichen);
  Speicher.schreib('leisten', leistenAn);
  menueBauen();
}
B.linealZeigen = () => { lineal = !lineal; ansichtExtras(); };
B.linealHochZeigen = () => { linealHoch = !linealHoch; ansichtExtras(); };

/* ------------------------------------------------------------
   Die einfachen Schalter aus dem Optionen-Fenster

   Der WPS Writer führt in seinen dreizehn Seiten weit über hundert
   Kästchen. Die meisten davon merken sich nichts weiter als an oder aus
   und lösen beim Umlegen eine Kleinigkeit aus — eine Klasse am Blatt,
   eine Leiste weg, ein Zeichen mehr.

   Einzeln verdrahtet wären das je zwanzig fast gleiche Zeilen: ein
   Zustand, ein Lesen aus dem Speicher, ein Schreiben, ein B.-Befehl, ein
   Griff für die Optionenseite. Bei sechzig Schaltern ist das nicht mehr
   zu übersehen, und die einundsechzigste Zeile vergisst man.

   Deshalb stehen sie hier als Tabelle: Name, Standardwert, Wirkung.
   Alles Übrige — Speichern, Umlegen, der Griff für die Optionenseite —
   entsteht daraus von selbst.

   WAS HIER NICHT HINEINGEHÖRT

   Schalter, die mehr tun als eine Kleinigkeit: Lineal, Navigationsbereich,
   Änderungen verfolgen. Die haben ihren eigenen Befehl, weil an ihnen
   noch anderes hängt.
   ------------------------------------------------------------ */
const SCHALTER = {

  /* ---- Ansicht ▸ Darstellung ---- */

  /* Der weiche Kontrast. Er hängt nicht an einer Klasse am body, sondern
     an einem Attribut an der Wurzel — die Farben sind dort definiert, und
     dort muss auch der Schalter greifen. Deshalb ruft er den Befehl, statt
     selbst etwas umzustellen: Sonst stünde dieselbe Logik an zwei Stellen,
     und die eine wäre irgendwann anders als die andere. */
  weicherKontrast: {
    standard: false,
    wirkt: (an) => {
      /* An der Wurzel und nicht am body: Die Farben sind dort definiert,
         und dort muss der Schalter greifen. */
      if (an) document.documentElement.dataset.weich = 'ja';
      else delete document.documentElement.dataset.weich;
    },
  },

  /* ---- Ansicht ▸ Anzeigen ---- */

  /* Bei WPS „Statusleiste". Sie trägt Seitenzahl, Wortzahl und den Zoom;
     wer den Platz braucht, schaltet sie weg. */
  statusleiste: { standard: true, wirkt: (an) =>
    document.body.classList.toggle('ohne-statuszeile', !an) },

  /* Bei WPS „Startaufgabenfenster": ob die Seitenleiste beim Öffnen des
     Programms schon aufgeklappt ist. Nicht, ob es sie gibt — das steht
     unter Ansicht. */
  tafelBeimStart: { standard: true, wirkt: () => {} },

  /* Bei WPS „QuickInfo": die kleinen Erklärungen an den Knöpfen. Sie
     werden nicht gelöscht, nur unterdrückt — sonst wären sie nach dem
     Ausschalten für immer weg. */
  quickinfo: { standard: true, wirkt: (an) =>
    document.body.classList.toggle('ohne-quickinfo', !an) },

  /* Bei WPS „Live-Vorschau aktivieren": ob das Überfahren eines Stils den
     Text schon probeweise umstellt. */
  livevorschau: { standard: true, wirkt: () => {} },

  /* Die beiden Minisymbolleisten: die schwebende Formatleiste, die bei
     einer Auswahl erscheint, und dieselbe beim Rechtsklick. */
  minileisteAuswahl: { standard: true, wirkt: () => {} },
  minileisteRechts:  { standard: true, wirkt: () => {} },

  /* Bei WPS „Tipp für Kopf- bzw. Fußzeile eingeben": der Hinweis, der im
     leeren Kopfbereich steht und sagt, was man dort tun kann. */
  kopfzeilenTipp: { standard: true, wirkt: (an) =>
    document.body.classList.toggle('ohne-kopftipp', !an) },

  /* ---- Ansicht ▸ Formatierungszeichen ----

     WPS zeigt sechs Kästchen, wo Lunivo bisher eines hatte. Sie wirken
     einzeln: jedes schaltet eine Klasse am Blatt, und das Stilblatt
     entscheidet, was dann sichtbar wird. */
  fzAbsatzmarken: { standard: true,  wirkt: () => zeichenAnwenden() },
  fzLeerzeichen:  { standard: true,  wirkt: () => zeichenAnwenden() },
  fzTabstopp:     { standard: true,  wirkt: () => zeichenAnwenden() },
  fzObjektanker:  { standard: false, wirkt: () => zeichenAnwenden() },
  fzAusgeblendet: { standard: false, wirkt: () => zeichenAnwenden() },

  /* ---- Ansicht ▸ Menübandoptionen ---- */

  /* Bei WPS „Auf Registerkarte doppelklicken, um Menüband auszublenden". */
  bandDoppelklick: { standard: true, wirkt: () => {} },
  /* Bei WPS „Use CTRL + Click to follow hyperlink": ob ein Klick allein
     dem Verweis folgt oder erst mit Strg. */
  strgKlickLink:   { standard: true, wirkt: () => {} },

  /* ---- Bearbeiten ▸ AutoKorrektur ----

     Elf Kästchen bei WPS. Was sie auslösen, steht in AUTOKORREKTUR — jede
     Regel dort nennt den Schalter, an dem sie hängt. */
  akAnfuehrung:     { standard: true,  wirkt: () => {} },
  akGedankenstrich: { standard: true,  wirkt: () => {} },
  akAuslassung:     { standard: true,  wirkt: () => {} },
  akSatzGross:      { standard: false, wirkt: () => {} },
  akWochentage:     { standard: false, wirkt: () => {} },
  akOrdnungszahlen: { standard: true,  wirkt: () => {} },
  akFeststelltaste: { standard: false, wirkt: () => {} },

  /* ---- Bearbeiten ▸ Bearbeitungsoptionen ---- */

  /* Bei WPS „Textbearbeitung durch Drag _Drop". Aus gesehen lässt sich
     markierter Text nicht mehr mit der Maus verschieben — für alle, denen
     beim Markieren die Hand verrutscht und der Absatz plötzlich woanders
     steht. */
  ziehenUndLegen: { standard: true, wirkt: (an) => {
    const feld = $('dokument');
    if (feld) feld.classList.toggle('ohne-ziehen', !an);
  } },

  /* Bei WPS „Intelligente Absatzmarkierung verwenden": ob beim Markieren
     ganze Wörter genommen werden statt einzelner Buchstaben. */
  wortweiseMarkieren: { standard: true, wirkt: () => {} },

  /* ---- Bearbeiten ▸ Ausschneide- und Einfügeoptionen ---- */

  /* Bei WPS „Enable middle button paste": unter Linux fügt die mittlere
     Maustaste ein, was zuletzt markiert war. Wer sie versehentlich
     drückt, hat plötzlich fremden Text im Brief. */
  mittelklickEinfuegen: { standard: false, wirkt: () => {} },

  /* Bei WPS „Schaltflächen für Einfügeoptionen anzeigen": das Kästchen,
     das nach dem Einfügen erscheint und fragt, mit oder ohne Format. */
  einfuegeKnopf: { standard: true, wirkt: () => {} },

  /* ---- Bearbeiten ▸ AutoFormat ----

     „1." oder „- " am Zeilenanfang macht aus dem Absatz eine Liste. Was
     die beiden auslösen, steht in autoListeLaufen(). */
  autoNummerierung: { standard: true, wirkt: () => {} },
  autoAufzaehlung:  { standard: true, wirkt: () => {} },

  /* ---- Rechtschreibprüfung ----

     Fünf Kästchen bei WPS, die Lunivo noch nicht führte. Sie greifen in
     pruefung.js: Was hier aus ist, wird gar nicht erst angestrichen. */
  rsGrossIgnorieren:  { standard: true,  wirkt: () => {} },
  rsZahlenIgnorieren: { standard: true,  wirkt: () => {} },
  rsPfadeIgnorieren:  { standard: true,  wirkt: () => {} },
  rsIgnorierteZeigen: { standard: false, wirkt: () => {} },
  rsGrammatik:        { standard: true,  wirkt: () => {} },

  /* ---- In PDF exportieren ----

     Was beim Export mitgeht. Gelesen wird das in B.speichernPdf. */
  pdfKommentare:    { standard: false, wirkt: () => {} },
  pdfHyperlinks:    { standard: true,  wirkt: () => {} },
  pdfUeberschriften:{ standard: true,  wirkt: () => {} },
  pdfEigenschaften: { standard: true,  wirkt: () => {} },
  pdfNachExport:    { standard: false, wirkt: () => {} },

  /* ---- Drucken ----

     Die Standardwerte, mit denen das Druckfenster aufgeht. Dort lassen
     sie sich für den einzelnen Auftrag noch ändern — hier steht, womit
     es anfängt. */
  drHohequalitaet:  { standard: true,  wirkt: () => {} },
  drUmgekehrt:      { standard: false, wirkt: () => {} },
  drHintergrund:    { standard: false, wirkt: () => {} },
  drZeichnungen:    { standard: true,  wirkt: () => {} },
  drLeereSeiten:    { standard: true,  wirkt: () => {} },

  /* ---- Sicherheit ---- */

  /* Bei WPS „Ausgeblendete Markups beim Öffnen oder Speichern anzeigen":
     ob verborgene Änderungen und Kommentare beim Öffnen sichtbar werden.
     Ein Brief, den man weitergibt, trägt sonst ungesehen mit, was darin
     einmal stand. */
  markupBeimOeffnen: { standard: true, wirkt: () => {} },
  /* Bei WPS „Beim Speichern persönliche Daten aus Dateieigenschaften
     entfernen". */
  datenBeimSpeichernWeg: { standard: false, wirkt: () => {} },

  /* ---- Ansicht ▸ Druckoptionen ----
     Bei WPS eine eigene Gruppe AUF der Ansicht-Seite. Sie sagt, was beim
     Drucken mitgeht — die Seite „Drucken" sagt, WIE gedruckt wird. */
  dpHervorheben:      { standard: true,  wirkt: () => {} },
  dpTextbegrenzungen: { standard: false, wirkt: () => {} },
  dpZuschnittsmarken: { standard: false, wirkt: () => {} },
  dpFeldfunktionen:   { standard: false, wirkt: () => {} },
  dpTextmarken:       { standard: false, wirkt: () => {} },

  /* ---- Bearbeiten, was noch fehlte ---- */
  tippenErsetzt:      { standard: true,  wirkt: () => {} },
  akHyperlink:        { standard: true,  wirkt: () => {} },
  akKreiszahl:        { standard: true,  wirkt: () => {} },
  akErstzeileneinzug: { standard: true,  wirkt: () => {} },
  akLeerzeichenRechts:{ standard: true,  wirkt: () => {} },
  akEinzugZentriert:  { standard: false, wirkt: () => {} },
  akTabEinzug:        { standard: true,  wirkt: () => {} },

  /* ---- Allgemein und Speichern ---- */
  bilderNichtKomprimieren: { standard: false, wirkt: () => {} },
  kompUnterstreichen:      { standard: true,  wirkt: () => {} },
  kompUmbruchTeilen:       { standard: false, wirkt: () => {} },
  kompHaengendTabstopp:    { standard: false, wirkt: () => {} },
  kompZeilenhoeheRaster:   { standard: true,  wirkt: () => {} },
  kompFussnotenWord97:     { standard: false, wirkt: () => {} },

  /* ---- Änderungen verfolgen ---- */
  spVerbindungslinien: { standard: true, wirkt: () => {} },
  spEmpfohleneBreite:  { standard: true, wirkt: () => {} },

  /* ---- In PDF exportieren, was noch fehlte ---- */
  pdfFussEndnoten:    { standard: true,  wirkt: () => {} },
  pdfTextmarken:      { standard: false, wirkt: () => {} },
  pdfAndereStile:     { standard: false, wirkt: () => {} },
  pdfEigeneStile:     { standard: false, wirkt: () => {} },

  /* ---- Benutzerinformationen ---- */
  benutzerVerwenden:  { standard: false, wirkt: () => {} },

  /* ---- Drucken, was noch fehlte ---- */
  drFelderAktualisieren: { standard: false, wirkt: () => {} },
  drFeldfunktionen:      { standard: false, wirkt: () => {} },
  drNurFormulardaten:    { standard: false, wirkt: () => {} },
  drBlattvorderseite:    { standard: true,  wirkt: () => {} },
  drBlattrueckseite:     { standard: true,  wirkt: () => {} },

  /* ---- Rechtschreibprüfung ---- */
  rsImmerVorschlaege: { standard: true, wirkt: () => {} },
};

/* Die Auswahlfelder und Zahlen aus dem Optionen-Fenster.

   Nicht alles dort ist ein Kästchen: WPS führt Klappmenüs und Zahlenfelder
   — Maßeinheit, Feldschattierung, Standardeinfügeformat, die Farben und
   Striche des Markups, die Sprechblasenbreite. Sie brauchen einen Wert
   statt an/aus, sonst dieselbe Behandlung. */
const WERTE = {
  /* Ansicht ▸ Druckoptionen */
  feldschattierung: { standard: 'auswahl' },   // nie | immer | auswahl
  /* Bearbeiten */
  rueckgaengigZahl: { standard: 0 },           // 0 = unbegrenzt
  einfuegeformat:   { standard: 'ursprung' },  // ursprung | ziel | nurtext
  /* Allgemein und Speichern */
  masseinheit:      { standard: 'mm' },        // mm | cm | zoll | punkt
  ausgabeziel:      { standard: 220 },         // ppi
  webKodierung:     { standard: 'utf-8' },
  /* Änderungen verfolgen */
  markupEinfuegung: { standard: 'unterstrichen' },
  markupLoeschung:  { standard: 'durchgestrichen' },
  markupZeilen:     { standard: 'aussen' },
  markupFarbe:      { standard: 'autor' },
  spBlasen:         { standard: 'blasen' },
  spSeitenrand:     { standard: 'rechts' },
  spBreite:         { standard: 94 },          // in mm
  spPapier:         { standard: 'behalten' },
  /* Drucken */
  drAusgeblendet:   { standard: 'nicht' },
  drAutor:          { standard: 'vollstaendig' },
  /* Sicherungseinstellungen */
  sicherungsart:    { standard: 'laufend' },   // laufend | schliessen | zeit
  sicherungMinuten: { standard: 10 },
  cacheTage:        { standard: 90 },
  /* Benutzerinformationen */
  initialen:        { standard: '' },
};

const werteStand = {};
for (const name of Object.keys(WERTE)) {
  werteStand[name] = Speicher.lies(name, WERTE[name].standard);
}
const wertLesen = (name) => werteStand[name];
function wertSetzen(name, wert) {
  if (!WERTE[name]) return;
  werteStand[name] = wert;
  Speicher.schreib(name, wert);
  wertAnwenden(name);
}
function wertAnwenden(name) {
  /* Was sich am Blatt zeigen lässt, zeigt sich sofort. */
  const feld = $('dokument');
  if (!feld) return;
  if (name === 'feldschattierung') {
    feld.classList.toggle('feldschatten--immer',   wertLesen(name) === 'immer');
    feld.classList.toggle('feldschatten--auswahl', wertLesen(name) === 'auswahl');
  }
  if (name === 'markupEinfuegung' || name === 'markupLoeschung' || name === 'markupZeilen') {
    feld.dataset[name] = wertLesen(name);
  }
}
function alleWerteAnwenden() {
  for (const name of Object.keys(WERTE)) wertAnwenden(name);
}

/* Listen beim Tippen erkennen.

   WPS führt dafür zwei Kästchen unter AutoFormat. Lunivo konnte Listen,
   aber nur auf Knopfdruck — wer „1." schrieb, bekam einen Absatz, der wie
   eine Liste aussah und sich nicht wie eine verhielt.

   Ausgelöst wird beim Leerzeichen, wie überall: Erst wenn jemand hinter
   „1." weiterschreibt, ist es als Aufzählung gemeint. Und nur am Anfang
   eines noch leeren Absatzes — mitten im Satz ist „1. " eine Zahl. */
function autoListeLaufen() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || !auswahl.isCollapsed) return false;
  const knoten = auswahl.anchorNode;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return false;

  const absatz = knoten.parentElement && knoten.parentElement.closest('p,div');
  if (!absatz || absatz.closest('li')) return false;

  const bis = auswahl.anchorOffset;
  const vorn = knoten.data.slice(0, bis);
  /* Nur wenn davor nichts steht: Der Absatz fängt hier an. */
  if (vorn !== knoten.data.slice(0, bis) || absatz.textContent.slice(0, bis) !== vorn) return false;

  const nummer = schalterAn('autoNummerierung') && /^\s*\d+[.)]$/.test(vorn);
  const punkt  = schalterAn('autoAufzaehlung')  && /^\s*[-*•]$/.test(vorn);
  if (!nummer && !punkt) return false;

  /* Das Zeichen wegnehmen, das die Liste angekündigt hat — es steht
     nachher als Aufzählungszeichen da und wäre sonst doppelt. */
  knoten.data = knoten.data.slice(bis);
  const bereich = document.createRange();
  bereich.setStart(knoten, 0);
  bereich.collapse(true);
  auswahl.removeAllRanges();
  auswahl.addRange(bereich);

  Dokument.befehl(nummer ? 'insertOrderedList' : 'insertUnorderedList');
  listeGeradeziehen();
  return true;
}

/* Der Stand jedes Schalters, aus dem Speicher geholt. */
const schalterStand = {};
for (const name of Object.keys(SCHALTER)) {
  schalterStand[name] = Speicher.lies(name, SCHALTER[name].standard);
}
const schalterAn = (name) => !!schalterStand[name];

function schalterAnwenden(name) {
  try { SCHALTER[name].wirkt(schalterStand[name]); } catch (e) { /* still */ }
}
function schalterUmlegen(name) {
  if (!SCHALTER[name]) return;
  schalterStand[name] = !schalterStand[name];
  Speicher.schreib(name, schalterStand[name]);
  schalterAnwenden(name);
}
/* Beim Start einmal alle anwenden: Ein gespeicherter Schalter, der beim
   Öffnen nicht wirkt, ist so gut wie nicht gespeichert. */
function alleSchalterAnwenden() {
  for (const name of Object.keys(SCHALTER)) schalterAnwenden(name);
}

/* Ein Fenster für die anderen Bausteine.

   pruefung.js, drucken.js und dateien.js müssen wissen, wie ein Schalter
   steht — pruefung.js etwa, ob GROSSBUCHSTABEN übergangen werden sollen.
   Sie sollen dafür nicht in programm.js hineingreifen: Ein einziger
   benannter Zugang ist leichter zu übersehen als zwanzig verstreute.

   Es steht am window, weil die Bausteine vor programm.js geladen werden
   und sonst nichts voneinander sehen. */
/* ------------------------------------------------------------
   Die Symbolleiste für den Schnellzugriff

   WPS führt dafür eine eigene Optionsseite mit zwei Listen. Sie fehlte
   hier ganz — die Begründung war, es gebe die Leiste nicht. Es gibt sie:
   die obere Werkzeugleiste. Was darin liegt, stand nur fest im Quelltext.
   ------------------------------------------------------------ */
const SZ_STANDARD = ['Neu', 'Öffnen', 'Speichern', 'Drucken', 'Druckvorschau',
                     'Rückgängig', 'Wiederholen'];
/* Alles, was hineingelegt werden kann. Die Namen sind die der Befehle,
   damit die Liste lesbar bleibt und in der Einstellungsdatei etwas sagt. */
const SZ_ANGEBOT = [
  'Neu', 'Öffnen', 'Speichern', 'Speichern unter', 'Drucken', 'Druckvorschau',
  'Als PDF exportieren', 'Rückgängig', 'Wiederholen', 'Ausschneiden', 'Kopieren',
  'Einfügen', 'Format übertragen', 'Fett', 'Kursiv', 'Unterstrichen',
  'Suchen', 'Ersetzen', 'Prüfen', 'Tabelle einfügen', 'Bild', 'Hyperlink',
  'Kopfzeile', 'Fußzeile', 'Seitenzahl', 'Sonderzeichen', 'Optionen',
];
let szLeiste = Speicher.lies('schnellzugriff', SZ_STANDARD.slice());
const szSichern = () => { Speicher.schreib('schnellzugriff', szLeiste); };

/* ------------------------------------------------------------
   Das Dokumentkennwort

   AES-256-GCM, der Schlüssel mit PBKDF2 aus dem Kennwort — beides bringt
   der Browser mit. Das Kennwort selbst wird nirgends gespeichert, nur der
   Hinweis darauf; ohne es ist der Text nicht mehr zu lesen, auch nicht
   von Lunivo.

   Der Sinn: Ein Feld, das nur so tut, wäre gefährlicher als keines. Wer
   sein Kennwort einträgt, soll geschützt sein.
   ------------------------------------------------------------ */
let kennwortSchluessel = null;   /* nur im Speicher, nie auf der Platte */

async function schluesselAus(kennwort, salz) {
  const roh = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(kennwort), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: salz, iterations: 210000, hash: 'SHA-256' },
    roh, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}

async function kennwortSetzen(kennwort, hinweis) {
  if (!kennwort) {
    kennwortSchluessel = null;
    Speicher.schreib('kennwortSalz', '');
    Speicher.schreib('kennwortHinweis', '');
    melde('Kennwort entfernt — die Datei ist wieder im Klartext lesbar.');
    return;
  }
  const salz = crypto.getRandomValues(new Uint8Array(16));
  kennwortSchluessel = await schluesselAus(kennwort, salz);
  Speicher.schreib('kennwortSalz', Array.from(salz).join(','));
  Speicher.schreib('kennwortHinweis', hinweis || '');
  melde('Kennwort gesetzt. Ohne es kommt niemand mehr an den Text — auch du nicht.');
}

/* Verschlüsseln und entschlüsseln, für dateien.js beim Speichern und
   Öffnen. Ohne gesetztes Kennwort geben beide den Text unverändert
   zurück — dann ändert sich am bisherigen Verhalten nichts. */
async function textVerschluesseln(text) {
  if (!kennwortSchluessel) return text;
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const roh = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv }, kennwortSchluessel, new TextEncoder().encode(text));
  return 'LUNIVO-AES256:' + btoa(String.fromCharCode(...iv))
       + ':' + btoa(String.fromCharCode(...new Uint8Array(roh)));
}
async function textEntschluesseln(text) {
  if (typeof text !== 'string' || !text.startsWith('LUNIVO-AES256:')) return text;
  if (!kennwortSchluessel) throw new Error('Für diese Datei braucht es das Kennwort.');
  const [, ivB, datenB] = text.split(':');
  const iv = Uint8Array.from(atob(ivB), (c) => c.charCodeAt(0));
  const daten = Uint8Array.from(atob(datenB), (c) => c.charCodeAt(0));
  const roh = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, kennwortSchluessel, daten);
  return new TextDecoder().decode(roh);
}
window.Kennwort = { setzen: kennwortSetzen, ver: textVerschluesseln, ent: textEntschluesseln,
                    gesetzt: () => !!kennwortSchluessel };

window.Optionen = {
  an: (name) => schalterAn(name),
  um: (name) => schalterUmlegen(name),
  wert: (name) => wertLesen(name),
  setze: (name, wert) => wertSetzen(name, wert),
  /* Alle auf einmal — für das Druckfenster, das seine Voreinstellungen
     in einem Zug übernimmt. */
  alle: () => Object.assign({}, schalterStand),
};

/* ---- Was die Schalter am Verhalten ändern ----

   Vier von ihnen genügt keine Klasse im Stilblatt: Sie müssen ein
   Ereignis abfangen. Die Zuhörer hängen einmal und fragen bei jedem Zug
   nach, wie der Schalter gerade steht — so wirkt ein Umlegen sofort,
   ohne dass jemand sie neu anschließen müsste. */
(() => {
  const feld = $('dokument');

  /* „Textbearbeitung durch Drag & Drop". Aus gesehen bleibt markierter
     Text liegen, wo er ist. */
  if (feld) feld.addEventListener('dragstart', (e) => {
    /* BILDER GEHOEREN UNS.

       Der Schalter "Textbearbeitung durch Drag & Drop" meint TEXT. Fuer
       ein Bild startet der Browser sonst sein eigenes Ziehen — und das
       schneidet unseres ab: pointerdown kommt noch an, pointermove nicht
       mehr. Genau deshalb liess sich ein Bild nicht verschieben, obwohl
       der Griff da war und der Code stimmte.

       Auch eine Tabelle darf so nicht davongetragen werden. */
    const ziel = e.target;
    if (ziel && ziel.closest
        && (ziel.tagName === 'IMG' || ziel.closest('table'))) {
      e.preventDefault();
      return;
    }
    if (!schalterAn('ziehenUndLegen')) e.preventDefault();
  });

  /* „Enable middle button paste". Unter Linux fügt die mittlere Maustaste
     ein, was zuletzt irgendwo markiert wurde — auch aus einem fremden
     Fenster. Wer sie streift, hat plötzlich fremden Text im Brief. */
  if (feld) feld.addEventListener('auxclick', (e) => {
    if (e.button === 1 && !schalterAn('mittelklickEinfuegen')) e.preventDefault();
  });
  if (feld) feld.addEventListener('paste', (e) => {
    /* Auch das Einfügen selbst abfangen: Manche Umgebungen melden den
       Mittelklick nicht als auxclick, sondern gleich als Einfügen. */
    if (e.inputType === 'insertFromPasteAsQuotation'
        && !schalterAn('mittelklickEinfuegen')) e.preventDefault();
  });

  /* „Use CTRL + Click to follow hyperlink". An gesehen öffnet ein Klick
     allein den Verweis nicht — dann lässt sich der Text davor bearbeiten,
     ohne dass der Browser wegspringt. */
  if (feld) feld.addEventListener('click', (e) => {
    const verweis = e.target.closest && e.target.closest('a[href]');
    if (!verweis) return;
    if (schalterAn('strgKlickLink') && !(e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      melde('Mit Strg anklicken, um dem Verweis zu folgen.');
    }
  });

  /* „Auf Registerkarte doppelklicken, um Menüband auszublenden." */
  const reiter = $('register-reiter');
  if (reiter) reiter.addEventListener('dblclick', () => {
    if (!schalterAn('bandDoppelklick')) return;
    const band = $('register-band');
    if (band) band.hidden = !band.hidden;
  });
})();

/* Die Formatierungszeichen zusammen: „Steuerzeichen" ist der Hauptschalter,
   die fünf darunter sagen, welche davon. Aus gesehen ist alles aus — so
   hält es auch WPS, wo „Alle" die anderen mitzieht. */
function zeichenAnwenden() {
  const feld = $('dokument');
  if (!feld) return;
  feld.classList.toggle('zeichen--absatz',      steuerzeichen && schalterAn('fzAbsatzmarken'));
  feld.classList.toggle('zeichen--leer',        steuerzeichen && schalterAn('fzLeerzeichen'));
  feld.classList.toggle('zeichen--tab',         steuerzeichen && schalterAn('fzTabstopp'));
  feld.classList.toggle('zeichen--anker',       steuerzeichen && schalterAn('fzObjektanker'));
  feld.classList.toggle('zeichen--ausgeblendet',steuerzeichen && schalterAn('fzAusgeblendet'));
}

/* ------------------------------------------------------------
   Das Lineal

   Es war bisher ein weißer Streifen mit zwei blauen Kanten — 17 cm breit,
   fest im Stilblatt eingetragen. Auf A5 log es, im Querformat auch, und
   messen konnte man damit ohnehin nichts.

   Jetzt rechnet es mit dem wirklichen Blatt: Es legt sich genau darüber,
   folgt der Vergrößerung und dem Papierformat, zeigt den Satzspiegel hell
   und die Ränder grau. Die Zahlen zählen vom Satzspiegel aus nach beiden
   Seiten — so steht es im Writer und in Word, und deshalb sucht dort auch
   niemand die Null am Blattrand.

   Und es tut etwas: Die drei Marken verschieben die Einzüge des Absatzes,
   in dem der Zeiger steht. Ein Lineal, an dem man nichts einstellen kann,
   ist ein Bild von einem Lineal.
   ------------------------------------------------------------ */
const MM = CM / 10;

/* Der Absatz, in dem der Zeiger gerade steht. */
function absatzJetzt() {
  let knoten = window.getSelection().anchorNode;
  while (knoten && knoten !== feld) {
    if (knoten.parentNode === feld) return knoten.nodeType === Node.ELEMENT_NODE ? knoten : null;
    knoten = knoten.parentNode;
  }
  return feld.firstElementChild;
}

function einzugLesen() {
  const absatz = absatzJetzt();
  if (!absatz || absatz.nodeType !== Node.ELEMENT_NODE) return { links: 0, rechts: 0, erste: 0 };
  const stil = getComputedStyle(absatz);
  return {
    links: (parseFloat(stil.marginLeft) || 0) / MM,
    rechts: (parseFloat(stil.marginRight) || 0) / MM,
    erste: (parseFloat(stil.textIndent) || 0) / MM,
  };
}

let linealUhr = null;
function linealAuffrischen() {
  /* Beim Tippen wandert der Zeiger bei jedem Anschlag. Das Lineal jedes
     Mal neu zu zeichnen wäre zu spüren — einmal am Ende reicht.

     Hier stand erst requestAnimationFrame. Das war falsch: Ein Fenster im
     Hintergrund zeichnet keine Bilder, der Aufruf blieb liegen, und das
     Lineal zeigte hinterher noch A4, während längst A5 quer eingestellt
     war. setTimeout kommt auch dann. */
  if (linealUhr) return;
  linealUhr = setTimeout(() => {
    linealUhr = null;
    linealZeichnen(); linealHochZeichnen(); linealNachmessen();
  }, 0);
}

/* Ein zweiter Blick, nachdem das Fenster fertig umgebaut hat.

   Wird das Fenster schmaler, kommt „resize" sofort — das Blatt steht zu
   diesem Zeitpunkt aber noch, wo es vorher stand. Das Lineal misst dann
   die alte Stelle, zeichnet sich dorthin, und danach ruft es niemand
   mehr: Die Bahn blieb stehen, während das Blatt nach links rutschte.
   Gemeldet am 03.09.2026 als „das Lineal bleibt starr".

   Statt eine Wartezeit zu raten, die auf jedem Rechner anders ausfällt,
   wird nachgesehen: Liegt die Bahn nicht mehr über dem Blatt, wird noch
   einmal gezeichnet. Einmal — sonst liefe es im Kreis, wenn die beiden
   sich aus einem anderen Grund nie treffen. */
let linealZweiterBlick = false;
function linealNachmessen() {
  if (linealZweiterBlick) { linealZweiterBlick = false; return; }
  const balken = $('lineal');
  if (balken.hidden) return;
  linealZweiterBlick = true;
  setTimeout(() => {
    const bahn = $('lineal-bahn');
    const blatt = $('blatt');
    const rb = bahn.getBoundingClientRect();
    const rBlatt = blatt.getBoundingClientRect();
    if (Math.abs(rb.left - rBlatt.left) > 1 || Math.abs(rb.width - rBlatt.width) > 1) {
      linealZeichnen();
    }
    linealZweiterBlick = false;
  }, 120);
}

/* Das Lineal hängt am Blatt, nicht an einer Liste von Stellen, die daran
   denken müssen. Ändert sich das Blatt — anderes Papier, andere Ränder,
   andere Vergrößerung, anderes Fenster —, zeichnet es sich neu. */
if (typeof ResizeObserver === 'function') {
  const wache = new ResizeObserver(linealAuffrischen);
  wache.observe($('blatt'));
  /* Die Arbeitsfläche wird auch schmaler, wenn jemand die Schreibhilfe
     breiter zieht — das Blatt bleibt dabei gleich groß. */
  wache.observe($('arbeitsflaeche'));
  /* Auch die Werkbank selbst: Sie ist es, die schmaler wird, wenn die
     Schreibhilfe wächst. */
  const werkbank = document.querySelector('.werkbank');
  if (werkbank) wache.observe(werkbank);
}

function linealZeichnen() {
  const balken = $('lineal');
  if (balken.hidden) return;
  const bahn = $('lineal-bahn');
  const blatt = $('blatt');

  const masse = PAPIERE[papier] || PAPIERE.a4;
  const breiteMm = quer ? masse.hoehe : masse.breite;

  const rBalken = balken.getBoundingClientRect();
  const rBlatt = blatt.getBoundingClientRect();
  if (!rBlatt.width) return;

  bahn.style.left = (rBlatt.left - rBalken.left) + 'px';
  bahn.style.width = rBlatt.width + 'px';

  /* Nicht mit CM rechnen, sondern mit dem, was das Blatt wirklich misst:
     Die Vergrößerung steckt schon darin. */
  const proMm = rBlatt.width / breiteMm;
  const feldVon = seitenrand.links * proMm;
  const feldBis = (breiteMm - seitenrand.rechts) * proMm;

  bahn.textContent = '';

  const band = document.createElement('div');
  band.className = 'lineal__feld';
  bahn.appendChild(band);

  for (let mm = 0; mm <= breiteMm + 0.01; mm += 5) {
    const x = mm * proMm;
    const abCm = (mm - seitenrand.links) / 10;
    const ganz = Math.abs(abCm - Math.round(abCm)) < 0.01;

    const strich = document.createElement('span');
    strich.className = 'lineal__strich' + (ganz ? '' : ' lineal__strich--klein');
    strich.style.left = x + 'px';
    bahn.appendChild(strich);

    /* Am äußersten Rand keine Zahl: Sie stünde halb außerhalb des Blattes
       und würde abgeschnitten — im Writer steht dort auch keine. */
    const platz = x > 9 && x < rBlatt.width - 9;
    if (ganz && Math.round(abCm) !== 0 && platz) {
      const zahl = document.createElement('span');
      const draussen = mm < seitenrand.links - 0.01 || mm > breiteMm - seitenrand.rechts + 0.01;
      zahl.className = 'lineal__zahl' + (draussen ? ' lineal__zahl--rand' : '');
      zahl.style.left = x + 'px';
      zahl.textContent = String(Math.abs(Math.round(abCm)));
      bahn.appendChild(zahl);
    }
  }

  const einzug = einzugLesen();
  const stellen = [
    ['erste',  'Erste Zeile',    feldVon + (einzug.links + einzug.erste) * proMm],
    ['links',  'Linker Einzug',  feldVon + einzug.links * proMm],
    ['rechts', 'Rechter Einzug', feldBis - einzug.rechts * proMm],
  ];
  for (const [welche, name, x] of stellen) {
    const marke = document.createElement('span');
    marke.className = 'lineal__marke lineal__marke--' + welche;
    marke.style.left = x + 'px';
    marke.dataset.welche = welche;
    marke.title = name + ' — ziehen zum Verschieben';
    bahn.appendChild(marke);
  }

  const lot = document.createElement('span');
  lot.className = 'lineal__lot';
  lot.id = 'lineal-lot';
  lot.hidden = true;
  bahn.appendChild(lot);

  linealBandSetzen();
}

/* Das senkrechte Lineal zeichnen.

   Dieselbe Rechnung wie waagerecht, nur an der anderen Achse: Gemessen
   wird nicht mit einer Zahl aus dem Stilblatt, sondern mit dem, was das
   Blatt gerade wirklich hoch ist — die Vergrößerung steckt schon darin.

   Die Null sitzt am oberen Rand des Satzspiegels, dort also, wo die
   erste Zeile steht. Über ihr laufen die Zentimeter weiter, nur blass:
   Das ist der Rand, und dort steht nichts.

   Marken zum Ziehen gibt es hier keine. Waagerecht hängen drei davon,
   weil Einzüge waagerecht sind; senkrecht gäbe es nur die Seitenränder,
   und die stehen im Dialog „Seitenränder" mit einer Zahl, die man lesen
   kann — genauer, als eine Maus je zieht. */
function linealHochZeichnen() {
  const balken = $('lineal-hoch');
  if (balken.hidden) return;
  const bahn = $('lineal-hoch-bahn');
  const blatt = $('blatt');

  const masse = PAPIERE[papier] || PAPIERE.a4;
  const hoeheMm = quer ? masse.breite : masse.hoehe;

  const rBalken = balken.getBoundingClientRect();
  const rBlatt = blatt.getBoundingClientRect();
  if (!rBlatt.height) return;

  bahn.style.top = (rBlatt.top - rBalken.top) + 'px';
  bahn.style.height = rBlatt.height + 'px';

  const proMm = rBlatt.height / hoeheMm;
  const feldVon = seitenrand.oben * proMm;
  const feldBis = (hoeheMm - seitenrand.unten) * proMm;

  bahn.textContent = '';

  const band = document.createElement('div');
  band.className = 'lineal-hoch__feld';
  band.style.top = feldVon + 'px';
  band.style.height = Math.max(0, feldBis - feldVon) + 'px';
  bahn.appendChild(band);

  for (let mm = 0; mm <= hoeheMm + 0.01; mm += 5) {
    const y = mm * proMm;
    const abCm = (mm - seitenrand.oben) / 10;
    const ganz = Math.abs(abCm - Math.round(abCm)) < 0.01;

    const strich = document.createElement('span');
    strich.className = 'lineal-hoch__strich' + (ganz ? '' : ' lineal-hoch__strich--klein');
    strich.style.top = y + 'px';
    bahn.appendChild(strich);

    /* Am äußersten Rand keine Zahl: Sie stünde halb außerhalb des
       Blattes und würde abgeschnitten. */
    const platz = y > 9 && y < rBlatt.height - 9;
    if (ganz && Math.round(abCm) !== 0 && platz) {
      const zahl = document.createElement('span');
      const draussen = mm < seitenrand.oben - 0.01 || mm > hoeheMm - seitenrand.unten + 0.01;
      zahl.className = 'lineal-hoch__zahl' + (draussen ? ' lineal-hoch__zahl--rand' : '');
      zahl.style.top = y + 'px';
      zahl.textContent = String(Math.abs(Math.round(abCm)));
      bahn.appendChild(zahl);
    }
  }
}

/* Beim Scrollen wandert das Blatt unter dem Lineal weg. Waagerecht fällt
   das nicht auf — die Fläche scrollt senkrecht. Hier schon: Ohne diese
   Zeile bliebe die Skala stehen, während der Text unter ihr durchläuft,
   und zeigte ab der zweiten Bildschirmhöhe überall die falsche Zahl.

   „passive": Das Lineal hält das Scrollen nicht auf, es sieht nur zu. */
$('arbeitsflaeche').addEventListener('scroll', () => {
  /* Der Griff der Tabelle ist am Fenster ausgerichtet und muss beim
     Rollen nachgeführt werden — sonst bleibt er stehen, während die
     Tabelle darunter wegwandert. */
  if (typeof griffAuffrischen === 'function') griffAuffrischen();
  if (!$('lineal-hoch').hidden) linealHochZeichnen();
}, { passive: true });

/* Das helle Band spannt sich zwischen den Marken auf. Es liest ihre
   Stellung aus dem Lineal selbst — dann stimmt es auch mitten im Ziehen,
   wo der Absatz seinen neuen Einzug noch gar nicht kennt.

   Links zählt die weiter außen stehende der beiden oberen Marken: Hängt
   die erste Zeile heraus, steht dort Text, und das Band muss ihn
   einschließen. */
function linealBandSetzen() {
  const bahn = $('lineal-bahn');
  const band = bahn.querySelector('.lineal__feld');
  if (!band) return;
  const breite = bahn.getBoundingClientRect().width;
  const stelle = (welche, ersatz) => {
    const marke = bahn.querySelector('.lineal__marke--' + welche);
    const wert = marke ? parseFloat(marke.style.left) : NaN;
    return isNaN(wert) ? ersatz : wert;
  };
  const von = Math.max(0, Math.min(stelle('links', 0), stelle('erste', 0)));
  const bis = Math.min(breite, stelle('rechts', breite));
  band.style.left = von + 'px';
  band.style.width = Math.max(0, bis - von) + 'px';
}

/* ---- Die Marken ziehen ----
   Gerechnet wird in Millimetern und auf einen halben gerundet: Feiner
   trifft die Maus ohnehin nicht, und krumme Werte wie 24,3178 mm stünden
   nachher im Dialog „Einzug". */
(() => {
  let zieht = null;

  const mmAusX = (seitenX) => {
    const bahn = $('lineal-bahn');
    const masse = PAPIERE[papier] || PAPIERE.a4;
    const breiteMm = quer ? masse.hoehe : masse.breite;
    const r = bahn.getBoundingClientRect();
    if (!r.width) return 0;
    const mm = (seitenX - r.left) / (r.width / breiteMm);
    return Math.max(0, Math.min(breiteMm, Math.round(mm * 2) / 2));
  };

  $('lineal').addEventListener('mousedown', (e) => {
    const marke = e.target.closest('.lineal__marke');
    if (!marke) return;
    e.preventDefault();
    const erste = $('lineal-bahn').querySelector('.lineal__marke--erste');
    zieht = {
      welche: marke.dataset.welche,
      marke,
      erste,
      /* Wer den ganzen Absatz verschiebt, nimmt die erste Zeile mit — sie
         behält ihren Abstand zum Rest. Ohne das bliebe ihre Marke beim
         Ziehen stehen, und das helle Band rührte sich erst beim
         Loslassen. */
      vonX: parseFloat(marke.style.left) || 0,
      ersteX: erste ? (parseFloat(erste.style.left) || 0) : 0,
    };
    marke.classList.add('lineal__marke--zieht');
  });

  window.addEventListener('mousemove', (e) => {
    if (!zieht) return;
    const bahn = $('lineal-bahn');
    const r = bahn.getBoundingClientRect();
    const x = Math.max(0, Math.min(r.width, e.clientX - r.left));
    zieht.marke.style.left = x + 'px';
    if (zieht.welche === 'links' && zieht.erste) {
      zieht.erste.style.left = (zieht.ersteX + (x - zieht.vonX)) + 'px';
    }
    const lot = document.getElementById('lineal-lot');
    if (lot) { lot.hidden = false; lot.style.left = x + 'px'; }
    /* Damit man schon beim Ziehen sieht, wie breit der Text wird. */
    linealBandSetzen();
  });

  window.addEventListener('mouseup', (e) => {
    if (!zieht) return;
    const welche = zieht.welche;
    zieht.marke.classList.remove('lineal__marke--zieht');
    zieht = null;
    const lot = document.getElementById('lineal-lot');
    if (lot) lot.hidden = true;

    const masse = PAPIERE[papier] || PAPIERE.a4;
    const breiteMm = quer ? masse.hoehe : masse.breite;
    const stelle = mmAusX(e.clientX);
    const alt = einzugLesen();

    if (welche === 'links') {
      const wert = Math.max(0, stelle - seitenrand.links);
      /* Der Erstzeileneinzug hängt am linken: Wer den ganzen Absatz
         verschiebt, will die erste Zeile nicht zurücklassen. */
      einzugSetzen({ links: wert });
      melde('Linker Einzug: ' + wert.toFixed(1).replace('.', ',') + ' mm.');
    } else if (welche === 'rechts') {
      const wert = Math.max(0, (breiteMm - seitenrand.rechts) - stelle);
      einzugSetzen({ rechts: wert });
      melde('Rechter Einzug: ' + wert.toFixed(1).replace('.', ',') + ' mm.');
    } else {
      const wert = stelle - seitenrand.links - alt.links;
      einzugSetzen({ erste: wert });
      melde('Erste Zeile: ' + wert.toFixed(1).replace('.', ',') + ' mm.');
    }
    linealZeichnen();
  });

  function einzugSetzen(was) {
    aufAbsaetze((el) => {
      if (was.links !== undefined) el.style.marginLeft = was.links + 'mm';
      if (was.rechts !== undefined) el.style.marginRight = was.rechts + 'mm';
      if (was.erste !== undefined) el.style.textIndent = was.erste + 'mm';
    });
  }
})();

B.steuerzeichenZeigen = () => { steuerzeichen = !steuerzeichen; ansichtExtras(); };
B.leistenZeigen = () => { leistenAn = !leistenAn; ansichtExtras(); };

/* ------------------------------------------------------------
   Menüleiste ein und aus

   Im Writer geht sie weg, und die Alt-Taste holt sie zurück. Ohne diesen
   Rückweg wäre der Menüpunkt eine Falle: Wer die Leiste ausblendet, hat
   damit auch den Menüpunkt ausgeblendet, mit dem er sie wiederholt.
   ------------------------------------------------------------ */
let menueleisteAn = Speicher.lies('menueleiste', true);

/* In der Register-Ansicht ist die Menüleiste weg — das Register TRITT AN
   IHRE STELLE, es kommt nicht dazu. Beides übereinander frisst genau den
   Platz, den das Register gewinnen soll, und niemand baut es so: Weder Word
   noch der Writer zeigen Menü und Reiter zugleich.

   Erreichbar bleibt sie über Ansicht ▸ Oberfläche ▸ Menüleiste und über die
   Alt-Taste. Das ☰ links in der Reiterzeile ist etwas anderes: Es klappt
   das Datei-Menü auf, so wie im WPS Writer, und schaltet nichts um. */
let menueImRegister = false;

function menueleisteAnwenden() {
  const zeigen = flaeche === 'register' ? menueImRegister : menueleisteAn;
  $('menueleiste').hidden = !zeigen;
}

B.menueleisteZeigen = () => {
  if (flaeche === 'register') {
    menueImRegister = !menueImRegister;
    menueleisteAnwenden();
    registerBauen();
    return;
  }
  menueleisteAn = !menueleisteAn;
  Speicher.schreib('menueleiste', menueleisteAn);
  menueleisteAnwenden();
  if (!menueleisteAn) melde('Menüleiste aus. Die Alt-Taste holt sie zurück.');
  menueBauen();
};

document.addEventListener('keydown', (e) => {
  const schonDa = flaeche === 'register' ? menueImRegister : menueleisteAn;
  if (e.key !== 'Alt' || e.ctrlKey || e.shiftKey || schonDa) return;
  e.preventDefault();
  $('menueleiste').hidden = false;
  /* Nur so lange, wie sie gebraucht wird: Wer daneben klickt, wollte sie
     nicht dauerhaft. Wer im Menü auf „Menüleiste" geht, schaltet sie an. */
  const wiederWeg = (ereignis) => {
    if ($('menueleiste').contains(ereignis.target)) return;
    menueleisteAnwenden();
    document.removeEventListener('mousedown', wiederWeg, true);
  };
  document.addEventListener('mousedown', wiederWeg, true);
});

/* ------------------------------------------------------------
   Die Register-Ansicht („In Registern")

   Dieselben Befehle wie in den Symbolleisten, nur in Reitern statt in zwei
   Zeilen. Sie werden hier NICHT neu geschrieben, sondern verwiesen: Jeder
   Eintrag nennt ein Symbol und einen Befehl aus B, und beide Ansichten
   greifen auf dasselbe zu. Zwei Listen derselben Knöpfe liefen nach der
   dritten Änderung auseinander.
   ------------------------------------------------------------ */
/* Ein Eintrag ist [Symbol, Name, Befehl] — und mit einem vierten Wert
   „gross" wird daraus der große Knopf links in der Gruppe, mit Beschriftung
   darunter. Genau die trägt ein Ribbon: Was man ständig braucht, steht groß
   und lesbar da, der Rest klein daneben. */
/* Ein Eintrag ist [Symbol, Name, Befehl] — mit einem vierten Wert „gross"
   wird daraus der große Knopf links in der Gruppe, mit Beschriftung darunter.

   Eine Gruppe ist [Name, Einträge] — mit einem dritten Wert bekommt sie unten
   rechts den kleinen Pfeil, der den vollen Dialog öffnet. Word nennt ihn
   Dialogfeldstarter; er ist das Versprechen, dass die Gruppe nicht alles
   zeigt, was es gibt. */
/* Die Liste der Reiter und Gruppen steht in daten/register.js. Was sie von
   hier braucht, steht in dieser Aufstellung — und nur das. Jeder Eintrag
   ist eine Funktion, denn manches davon gibt es hier erst weiter unten,
   und die Haken müssen beim Aufklappen nachsehen, nicht beim Bauen. */
const REGISTER = REGISTER_BAUEN(B, {
  pruefen:          ()     => pruefen(),
  kiKorrigieren:    ()     => KIteil.kiKorrigieren(),
  kiVorschlaege:    ()     => KIteil.kiVorschlaege(),
  kiUebersetzen:    ()     => KIteil.kiUebersetzen(),
  sucheZeigen:      (an)   => sucheZeigen(an),
  setzeLayout:      (wahl) => setzeLayout(wahl),
  setzePapier:      (art)  => setzePapier(art),
  setzeThema:       (wahl) => setzeThema(wahl),
  setzeRandVorgabe: (art)  => setzeRandVorgabe(art),
  papierJetzt:      ()     => papier,
  /* Welche Randvorgabe gerade gilt — damit die Klappe einen Haken setzen
     kann. Verglichen wird ueber die Zahlen, nicht ueber einen Merker:
     Wer die Raender von Hand auf Normal stellt, soll denselben Haken
     sehen wie der, der auf „Normal" geklickt hat. */
  randVorgabeJetzt: () => {
    for (const [art, wie] of Object.entries(RANDVORGABEN)) {
      if (wie.oben === seitenrand.oben && wie.unten === seitenrand.unten
       && wie.links === seitenrand.links && wie.rechts === seitenrand.rechts) return art;
    }
    return '';
  },
  spaltenJetzt:     ()     => spalten,
  querJetzt:        ()     => quer,
  /* Die Optionen auf einer bestimmten Seite aufmachen. Ein Knopf im Band,
     der die Optionen öffnet und den Menschen dann selbst suchen lässt,
     bringt ihn nur einen halben Schritt weiter. */
  optionenOeffnen:  (seite) => Einstellungen.oeffnen(seite),
  /* Ob ein Schalter im Band gerade an ist. Ein Zugang für alle statt
     zwanzig einzelne Namen — und register.js bleibt eine Liste, die
     nichts vom Programm wissen muss. */
  an: (was) => ({
    zeilennummern:  () => zeilennummern,
    silbentrennung: () => trennung,
    steuerzeichen:  () => steuerzeichen,
    lineal:         () => !$('lineal').hidden,
    linealHoch:     () => !$('lineal-hoch').hidden,
    netzlinien:     () => netzlinien,
    navigation:     () => navOffen,
    textbegrenzungen: () => marken,
    tafel:          () => tafelOffen,
    zeilenfokus:    () => lesehilfe.fokus,
    verfolgen:      () => verfolgenAn,
    kopfzeile:      () => kopfAn,
    fusszeile:      () => fussAn,
    rechtschreibung: () => lebendAn,
    lesemodus:      () => lesemodus,
  }[was] || (() => false))(),
});

/* Kontextabhängige Reiter: Sie stehen nur da, wenn sie etwas zu sagen haben.
   Word blendet „Tabellentools" ein, sobald der Zeiger in einer Tabelle steht,
   und wieder aus, sobald er heraus ist. Ein Reiter, dessen Knöpfe ins Leere
   griffen, wäre schlimmer als keiner. */
const REGISTER_IM_ZUSAMMENHANG = [
  {
    name: 'Tabellenwerkzeuge',
    gilt: () => !!zelleJetzt(),
    /* Die Kennungen sind die aus symbole.js und stehen dort klein.
       Vorher standen hier „Oben", „Weg", „Löschen" — Namen, die es dort
       nicht gibt. symbolPfad() fand nichts, und alle zehn Knöpfe dieses
       Reiters standen ohne Bild da. Ein Knopf ohne Bild sieht aus wie
       einer, der noch nicht fertig ist. */
    gruppen: [
      ['Tabelle', [['kopfz', 'Erste Zeile als Kopf', () => B.kopfzeileTabelle(), 'gross'],
                   ['fortlaufend', 'Wieder in den Text einreihen', () => B.tabelleEinreihen()],
                   ['ebeneHoch', 'Tabelle nach oben', () => B.tabelleHoch()],
                   ['ebeneTief', 'Tabelle nach unten', () => B.tabelleRunter()],
                   ['sortieren', 'Sortieren', () => B.sortieren()],
                   ['radierer', 'Ganze Tabelle löschen', () => B.tabelleWeg()]]],
      ['Zellen', [['zweiblatt', 'Zellen zusammenführen', () => B.zellenVerbinden(), 'gross'],
                   ['spalten', 'Zellen teilen', () => B.zellenTeilen(), 'gross']]],
      ['Zeilen und Spalten', [['tabelle', 'Zeile darüber', () => B.zeileOben(), 'gross'],
                   ['tabelle', 'Zeile darunter', () => B.zeileUnten(), 'gross'],
                   ['spalten', 'Spalte links', () => B.spalteLinks(), 'gross'],
                   ['spalten', 'Spalte rechts', () => B.spalteRechts(), 'gross'],
                   ['radierer', 'Zeile löschen', () => B.zeileWeg()],
                   ['radierer', 'Spalte löschen', () => B.spalteWeg()]]],
      ['Zellengröße', [['ecken', 'Zellengröße', () => B.zellengroesse(), 'gross']]],
      ['Ausrichtung', [['ausrichtung', 'Ausrichtung', () => B.zellenAusrichtung(), 'gross']]],
      ['Tabellenformatierung', [['rahmen', 'Rahmen ein/aus', () => B.tabelleRahmen(), 'gross'],
                   ['toenung', 'Eigenschaften', () => B.tabelleEigenschaften(), 'gross']]],
    ],
  },
  {
    /* Wie „Tabellenwerkzeuge", nur fuer Bilder. Bisher gab es fuer sie
       nur das Fenster „Anordnen" — die Befehle, die man staendig
       braucht, standen nirgends griffbereit. */
    name: 'Bildtools',
    gilt: () => {
      const b = bildAnStelle();
      return !!(b && b.tagName === 'IMG');
    },
    gruppen: [
      ['Bild', [['bild', 'Bild einfügen', () => B.bild(), 'gross'],
                ['anordnen', 'Anordnen', () => B.anordnen(), 'gross']]],
      ['Größe', [['lupe', 'Größe genau angeben', () => B.bildGroesse(), 'gross'],
                 ['ecken', 'Größe zurücksetzen', () => B.bildGroesseZurueck()]]],
      ['Zuschneiden', [['schere', 'Zuschneiden (Winkel ziehen)', () => B.schnittModus(), 'gross'],
                       ['ecken', 'Nach Form oder Verhältnis', () => B.bildZuschneiden()],
                       ['zurueck', 'Zuschnitt aufheben', () => B.bildSchnittWeg()]]],
      ['Drehen und Spiegeln',
        [['zurueck', 'Nach links drehen (90°)', () => B.bildLinks90(), 'gross'],
         ['vor', 'Nach rechts drehen (90°)', () => B.bildRechts90(), 'gross'],
         ['ebeneHoch', 'Waagerecht spiegeln', () => B.bildSpiegelnWaagerecht()],
         ['ebeneTief', 'Senkrecht spiegeln', () => B.bildSpiegelnSenkrecht()],
         ['radierer', 'Drehung zurücksetzen', () => B.bildDrehenZurueck()]]],
      ['Farbe', [['toenung', 'Farbe, Helligkeit, Kontrast', () => B.bildFarbe(), 'gross'],
                 ['radierer', 'Farbe zurücksetzen', () => B.bildFarbeZurueck()]]],
      ['Stellung', [['fortlaufend', 'Wieder in den Text einreihen',
                     () => B.bildEinreihen(), 'gross']]],
    ],
  },
  {
    /* TEXTTOOLS — „In WPS erscheint im Reiter ein neuer Eintrag Text
       Tools fuer erweiterte Funktionen." Und daran haengt sein anderer
       Befund: „Der Rahmen laesst sich nicht entfernen in Lunivo." Es gab
       keinen Ort, an dem man ihn haette entfernen koennen.

       Nach seinem Bild, von links nach rechts:
         Textfeld · Format uebertragen
         Textfuellung · Textkontur · Texteffekte   (fuer den TEXT)
         Fuellung · Kontur · Effekte               (fuer den RAHMEN)
         Verknuepfung · Einstellungen                                  */
    name: 'Texttools',
    gilt: () => !!textrahmenJetzt(),
    gruppen: [
      ['Textfeld', [['textrahmen', 'Textfeld einfügen', () => B.textfeld(), 'gross'],
                    ['pinsel', 'Format übertragen', () => B.formatUebertragen()]]],
      ['WordArt-Stile', [
        ['schriftfarbe', 'Textfüllung', (k) => B.rahmenTextfarbe(k), 'gross'],
        ['umriss', 'Textkontur', (k) => B.rahmenTextkontur(k), 'gross'],
        ['eingeschlossen', 'Texteffekte', (k) => B.effekt(k), 'gross']]],
      ['Formenarten', [
        ['toenung', 'Füllung', (k) => B.rahmenFuellung(k), 'gross'],
        ['rahmen', 'Kontur', (k) => B.rahmenKontur(k), 'gross'],
        ['texteffekt', 'Effekte', (k) => B.rahmenEffekt(k), 'gross']]],
      ['Anordnen', [['anordnen', 'Textfluss', () => B.anordnen(), 'gross'],
                    ['ecken', 'Größe', () => B.rahmenGroesse()]]],
      ['Einstellungen', [['zahnrad', 'Einstellungen', () => B.rahmenEinstellungen(), 'gross'],
                         ['radierer', 'Textfeld löschen', () => B.rahmenWeg()]]],
    ],
  },
  {
    name: 'Zeichentools',
    gilt: () => !!formJetzt(),
    gruppen: [
      ['Formen', [['stift', 'Formen', () => B.formAendern(), 'gross']]],
      ['Füllung', [['toenung', 'Füllung', () => B.formFuellung(), 'gross']]],
      ['Kontur', [['rahmen', 'Kontur', () => B.formKontur(), 'gross']]],
      ['Anordnen', [['anordnen', 'Anordnen', () => B.anordnen(), 'gross']]],
      ['Größe', [['ecken', 'Größe', () => B.formGroesse(), 'gross']]],
    ],
  },
  {
    name: 'Diagrammtools',
    gilt: () => !!diagrammJetzt(),
    gruppen: [
      /* NACH SEINEM BILD DER WPS-LEISTE, von links nach rechts:
           Diagrammelement hinzufuegen · Schnelllayout · Farbe aendern
           [ Formatvorlagen ]
           Diagrammtyp aendern · [ die Arten als Zeichen ]
           Daten auswaehlen · Daten bearbeiten
           Formatieren · Formatvorlage zuruecksetzen                */
      ['Diagrammentwurf', [
        ['diagrammteil', 'Diagrammelement hinzufügen', (k) => B.diagrammElement(k), 'gross'],
        ['anordnen', 'Schnelllayout', (k) => B.diagrammLayout(k), 'gross'],
        ['pinselchen', 'Farbe ändern', (k) => B.diagrammFarbe(k), 'gross']]],
      ['Formatvorlagen', [
        ['toenung', 'Formatvorlagen', (k) => B.diagrammStile(k), 'gross']]],
      ['Diagrammtyp', [
        ['saeule', 'Diagrammtyp ändern', () => B.diagrammTyp(), 'gross'],
        ['saeule', 'Säule', () => B.diagrammArt('saeule')],
        ['linie', 'Linie', () => B.diagrammArt('linie')],
        ['kreis', 'Kreis', () => B.diagrammArt('kuchen')],
        ['punktwolke', 'X Y (Punkt)', () => B.diagrammArt('punkte')],
        ['//'],
        ['balkenquer', 'Balken', () => B.diagrammArt('balken')],
        ['flaeche', 'Fläche', () => B.diagrammArt('flaeche')],
        ['kreis', 'Ring', () => B.diagrammArt('ring')],
        ['saeule', 'Gestapelt', () => B.diagrammArt('saeulegest')]]],
      ['Daten', [
        ['filter', 'Daten auswählen', () => B.diagrammDaten(), 'gross'],
        ['zahlen', 'Daten bearbeiten', () => B.diagrammDaten(), 'gross']]],
      ['Formatierung', [
        ['zahnrad', 'Formatieren', () => B.diagrammFormat(), 'gross'],
        ['Zurück', 'Formatvorlage zurücksetzen', () => B.diagrammZurueck()],
        ['vorlage', 'Als Vorlage merken', () => B.diagrammVorlageMerken()]]],
    ],
  },
  {
    /* Auf seinem Bild sind es ZWEI Reiter: „WPSArt-Design" und
       „WPSArt-Format". Sein SOLL nennt sie SmartArt-Entwurf und
       SmartArt-Format. Der Entwurf baut, das Format faerbt. */
    name: 'SmartArt-Entwurf',
    gilt: () => !!smartartJetzt(),
    gruppen: [
      /* NACH SEINEM BILD. In WPS heisst der Reiter „WPSArt-Design", und
         darin stehen von links nach rechts: Form einfuegen, Level
         erhoehen/reduzieren, Vorwaerts/Rueckwaerts, Layout von rechts
         nach links, Layout — dann Farben aendern, dann die Stile, dann
         Textfluss/Ausrichten, dann Hoehe und Breite. */
      ['Formen', [['smartart', 'Form einfügen', (k) => B.smartartFormEin(k), 'gross'],
                  ['ebeneHoch', 'Vorwärts', () => B.smartartVor()],
                  ['ebeneTief', 'Rückwärts', () => B.smartartZurueck()],
                  ['objektdrehen', 'Reihenfolge umdrehen', () => B.smartartUmdrehen()],
                  ['Aa', 'Kästen bearbeiten', () => B.smartartText()]]],
      ['Layout', [['smartart', 'Layout', (k) => B.smartartLayout(k), 'gross']]],
      ['Farben', [['toenung', 'Farben ändern', (k) => B.smartartFarben(k), 'gross']]],
      ['Anordnen', [['anordnen', 'Textfluss', () => B.anordnen(), 'gross'],
                    ['ausrichten', 'Ausrichten', (k) => B.objektAusrichten(k)],
                    ['ecken', 'Größe', () => B.smartartGroesse()]]],
    ],
  },
  {
    name: 'SmartArt-Format',
    gilt: () => !!smartartJetzt(),
    gruppen: [
      ['Formenarten', [['toenung', 'Füllung', (k) => B.smartartFarben(k), 'gross'],
                       ['rahmen', 'Kontur', (k) => B.smartartKontur(k), 'gross'],
                       ['texteffekt', 'Effekte', (k) => B.smartartEffekt(k), 'gross']]],
      ['Größe', [['ecken', 'Größe', () => B.smartartGroesse(), 'gross']]],
      ['Anordnen', [['anordnen', 'Textfluss', () => B.anordnen(), 'gross'],
                    ['ausrichten', 'Ausrichten', (k) => B.objektAusrichten(k)],
                    ['objektdrehen', 'Drehen', (k) => B.objektDrehen(k)]]],
    ],
  },
  {
    name: 'Gleichungswerkzeuge',
    gilt: () => !!formelJetzt(),
    gruppen: [
      ['Formeleditor-Funktionen', [['formel', 'Formel ändern', () => B.formelAendern(), 'gross']]],
    ],
  },
  {
    /* Wer in der Kopfzeile steht, will Seitenzahl, Datum — und vor allem
       wieder heraus. Der Weg zurück ist mit der Maus der fummeligste:
       Man trifft die schmale Zeile leichter, als man sie wieder verlässt. */
    name: 'Kopf- und Fußzeilenwerkzeuge',
    gilt: () => !!kopfFussJetzt(),
    gruppen: [
      ['Kopfzeile', [['kopfz', 'Kopfzeile', () => B.kopfzeile(), 'gross']]],
      ['Fußzeile', [['fussz', 'Fußzeile', () => B.fusszeile(), 'gross']]],
      ['Seitenzahl', [['zahlen', 'Seitenzahl', () => B.seitennummer(), 'gross'],
                      ['datum', 'Datum', () => B.datum()],
                      ['uhrzeit', 'Uhrzeit', () => B.uhrzeit()]]],
      ['Navigation', [['zurueck', 'Zurück in den Text', () => B.zurueckInText(), 'gross'],
                      ['kopfz', 'Zur Kopfzeile', () => B.zurKopfzeile()],
                      ['fussz', 'Zur Fußzeile', () => B.zurFusszeile()]]],
    ],
  },
];

/* Steht die Schreibstelle in der Kopf- oder Fußzeile?

   Anders als zelleJetzt() wird bis zum Seitenkörper hinaufgegangen: Die
   beiden Zeilen liegen neben dem Blatt, nicht darin. */
/* ============================================================
   Was steht gerade unter dem Zeiger?

   Die kontextabhängigen Register hängen daran. Gesucht wird erst am
   Zeiger; steht er daneben — nach dem Einfügen ist das der Normalfall —,
   gilt das zuletzt eingefügte Objekt seiner Art.
   ============================================================ */
function objektAnStelle(waehler, klasse) {
  const auswahl = window.getSelection();
  let knoten = auswahl.rangeCount ? auswahl.anchorNode : null;
  if (knoten && knoten.nodeType === Node.TEXT_NODE) knoten = knoten.parentElement;
  const nah = knoten && knoten.closest ? knoten.closest(waehler) : null;
  if (nah && feld.contains(nah)) {
    /* Ein SmartArt ist auch ein Diagramm — wer nach dem Diagramm sucht,
       darf das SmartArt nicht mitnehmen, sonst stünden beide Register da. */
    if (klasse === false && nah.classList.contains('smartart')) return null;
    return nah;
  }
  const alle = feld.querySelectorAll(waehler);
  for (let i = alle.length - 1; i >= 0; i--) {
    if (klasse === false && alle[i].classList.contains('smartart')) continue;
    return alle[i];
  }
  return null;
}

const formJetzt     = () => objektAnStelle('svg.zeichnung');

/* Das Textfeld, in dem der Zeiger steht. Braucht die Texttools-Leiste. */
function textrahmenJetzt() {
  const auswahl = window.getSelection();
  let k = auswahl && auswahl.anchorNode;
  if (k && k.nodeType === Node.TEXT_NODE) k = k.parentElement;
  const r = k && k.closest ? k.closest('.textrahmen') : null;
  return (r && feld.contains(r)) ? r : null;
}
const diagrammJetzt = () => objektAnStelle('svg.diagramm', false);
const smartartJetzt = () => objektAnStelle('svg.smartart');
const formelJetzt   = () => objektAnStelle('math');

function kopfFussJetzt() {
  let k = window.getSelection().anchorNode;
  while (k && k !== document.body) {
    if (k.nodeType === Node.ELEMENT_NODE
        && (k.id === 'kopfzeile' || k.id === 'fusszeile')) {
      /* Nur wenn die Zeile auch dasteht. Eine ausgeblendete Kopfzeile
         behält ihren Inhalt und damit ihre Schreibstelle — der Reiter
         käme sonst zu einer Zeile, die niemand sieht. */
      return k.offsetParent === null ? null : k;
    }
    k = k.parentNode;
  }
  return null;
}

function zusammenhangReiter() {
  return REGISTER_IM_ZUSAMMENHANG.filter((r) => {
    try { return r.gilt(); } catch (e) { return false; }
  });
}

/* ------------------------------------------------------------
   Der Formatvorlagen-Katalog

   Ein Auswahlfeld sagt „Überschrift 1"; der Katalog ZEIGT sie. Wer mit
   Schrift kämpft, erkennt eine Form schneller, als er einen Namen liest —
   und genau darum baut Word ihn seit zwanzig Jahren so.
   ------------------------------------------------------------ */
const KATALOG = [
  ['Standard',     'Aa', () => absatz('p'),                        'kat--p'],
  ['Überschrift 1','Aa', () => absatz('h1'),                       'kat--h1'],
  ['Überschrift 2','Aa', () => absatz('h2'),                       'kat--h2'],
  ['Überschrift 3','Aa', () => absatz('h3'),                       'kat--h3'],
  ['Titel',        'Aa', () => vorlageSetzen('h1', 'titel'),       'kat--titel'],
  ['Untertitel',   'Aa', () => vorlageSetzen('h2', 'untertitel'),  'kat--untertitel'],
  ['Zitat',        'Aa', () => absatz('blockquote'),               'kat--zitat'],
  ['Kein Abstand', 'Aa', () => vorlageSetzen('p', 'ohne-abstand'), 'kat--p'],
];

/* Die acht mitgelieferten Vorlagen und dahinter die selbst angelegten.
   Die eigenen tragen keine feste Klasse für die Vorschau — ihre Form
   steht in „vorlagenStile", und die Kachel malt sich danach. */
function katalogEintraege() {
  const eigene = Object.entries(vorlagenStile)
    .filter(([, wie]) => wie.eigen)
    .map(([tag, wie]) => {
      const [grund, klasse] = tag.split('.');
      return [wie.name, 'Aa', () => vorlageSetzen(grund, klasse), '', wie];
    });
  return KATALOG.concat(eigene);
}

/* Eine Kachel des Katalogs. Sie trägt die Form, die sie setzt — sonst
   wäre der Katalog acht gleiche Kästchen mit verschiedenen Wörtern
   darunter. */
function katalogStueck([name, probe, tun, klasse, wie], gross) {
  const k = document.createElement('button');
  k.type = 'button';
  k.className = 'katalog__stueck' + (gross ? ' katalog__stueck--gross' : '');
  k.title = name;
  k.setAttribute('aria-label', name);

  const bild = document.createElement('span');
  bild.className = 'katalog__probe ' + (klasse || '');
  bild.textContent = probe;
  /* Eine eigene Vorlage hat keine Klasse im Stilblatt, die man hier
     anhängen könnte — sie wird deshalb unmittelbar gemalt. Größe gedeckelt:
     Eine Vorlage mit 60 pt sprengte sonst die Kachel. */
  if (wie) {
    bild.style.fontWeight = wie.fett ? '700' : '400';
    bild.style.fontStyle = wie.kursiv ? 'italic' : 'normal';
    bild.style.fontSize = Math.min(gross ? 21 : 15, Math.max(11, wie.groesse)) + 'px';
    if (wie.schrift) bild.style.fontFamily = '"' + wie.schrift.replace(/"/g, '') + '"';
  }
  const wort = document.createElement('span');
  wort.className = 'katalog__name';
  wort.textContent = name;

  k.append(bild, wort);
  k.addEventListener('mousedown', (e) => e.preventDefault());
  k.addEventListener('click', () => { katalogKlappeWeg(); tun(); });
  return k;
}

/* ------------------------------------------------------------
   Der Formatvorlagen-Katalog im Band

   Er stand als EINE Zeile da und zog sich über die halbe Breite des
   Fensters: acht Kacheln nebeneinander, und darunter allein in der Mitte
   das Zeichen zum Verwalten mit der Aufschrift „STILE". Das sah aus wie
   eine Gruppe, die aus dem Leim gegangen ist.

   Der WPS Writer macht daraus ein Gitter mit zwei Zeilen und einen Pfeil
   daneben, der alles aufklappt. Das ist die bessere Form, und zwar nicht
   aus Geschmack: Eine Gruppe im Band ist so hoch wie das Band. Wer die
   Höhe nicht nutzt, braucht die doppelte Breite — und die fehlt dann den
   Gruppen dahinter.
   ------------------------------------------------------------ */
function katalogBauen() {
  const kiste = document.createElement('div');
  kiste.className = 'katalogkiste';

  const gitter = document.createElement('div');
  gitter.className = 'katalog';
  /* Im Band nur die acht mitgelieferten — sonst wüchse die Gruppe mit
     jeder eigenen Vorlage weiter ins Band hinein. Alle stehen in der
     Klappe. */
  for (const eintrag of KATALOG) gitter.appendChild(katalogStueck(eintrag));
  kiste.appendChild(gitter);

  const mehr = document.createElement('button');
  mehr.className = 'katalog__mehr';
  mehr.type = 'button';
  mehr.title = 'Mehr zu den Formatvorlagen';
  mehr.setAttribute('aria-label', 'Mehr zu den Formatvorlagen');
  mehr.setAttribute('aria-haspopup', 'true');
  mehr.textContent = '⌄';
  mehr.addEventListener('mousedown', (e) => e.preventDefault());
  mehr.addEventListener('click', () => katalogKlappeZeigen(mehr));
  kiste.appendChild(mehr);

  return kiste;
}

let katalogKlappe = null;

function katalogKlappeWeg() {
  if (katalogKlappe) { katalogKlappe.remove(); katalogKlappe = null; }
}

/* Das Klappmenü der Gruppe „Stile".
 *
 * Es zeigt ALLE Vorlagen — und legt sich dabei ÜBER die Gruppe im Band.
 * Das ist der Punkt, und er hat zwei Anläufe gekostet.
 *
 * Erst standen alle acht darin, während dieselben acht zwei Zentimeter
 * darüber im Band stehen blieben: „das ist so doppelt gemoppelt". Dann
 * habe ich die acht weggelassen — auch falsch, denn dann findet man im
 * Klappmenü nicht, was man dort sucht.
 *
 * Der WPS Writer macht es anders und besser: Das Menü geht an der STELLE
 * der Gruppe auf und verdeckt sie. Es steht dann alles einmal da, nur
 * größer und vollständig — mit den eigenen Vorlagen, die im Band keinen
 * Platz haben, und den Befehlen darunter. Doppelt ist nichts, weil man
 * beides nie zugleich sieht.
 *
 * Es hängt am Fenster und nicht im Band: Das Band rollt seitlich, und was
 * auf einer Achse rollt, schneidet der Browser auch auf der anderen ab.
 * Genau daran war einmal die Schriftliste als Streifen von zwanzig Pixeln
 * geendet.
 */
function katalogKlappeZeigen(knopf) {
  if (katalogKlappe) { katalogKlappeWeg(); return; }

  const tafel = document.createElement('div');
  tafel.className = 'katalogklappe';

  /* Die Überschrift trägt den Namen der Gruppe — das Menü steht ja an
     deren Stelle, und ohne sie wüsste man beim Aufgehen nicht, was gerade
     verdeckt wurde. */
  const kopf = document.createElement('p');
  kopf.className = 'katalogklappe__kopf';
  kopf.textContent = 'Stile';
  tafel.appendChild(kopf);

  const gitter = document.createElement('div');
  gitter.className = 'katalogklappe__gitter';
  for (const eintrag of katalogEintraege()) gitter.appendChild(katalogStueck(eintrag, true));
  tafel.appendChild(gitter);

  const strichchen = document.createElement('div');
  strichchen.className = 'katalogklappe__strich';
  tafel.appendChild(strichchen);

  const punkt = (name, tun, aus) => {
    const k = document.createElement('button');
    k.className = 'katalogklappe__punkt' + (aus ? ' katalogklappe__punkt--aus' : '');
    k.type = 'button';
    k.textContent = name;
    if (aus) { k.disabled = true; tafel.appendChild(k); return; }
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => { katalogKlappeWeg(); tun(); });
    tafel.appendChild(k);
  };

  punkt('Neue Formatvorlage…', () => B.vorlageNeu());
  /* Grau, solange es nichts zu löschen gibt: Die mitgelieferten Vorlagen
     bleiben. Ein Punkt, der mal da ist und mal nicht, lässt sich nicht
     lernen. */
  punkt('Formatvorlage löschen…', () => B.vorlageLoeschen(),
        !Object.values(vorlagenStile).some((wie) => wie.eigen));
  punkt('Formatvorlagen verwalten…', () => B.vorlagenVerwalten());

  document.body.appendChild(tafel);
  katalogKlappe = tafel;

  /* An die Stelle der Gruppe, nicht unter den Pfeil. Erst einhängen, dann
     messen — vorher hat die Tafel keine Breite. */
  const gruppe = knopf.closest('.register__gruppe') || knopf;
  const platz = gruppe.getBoundingClientRect();
  const masse = tafel.getBoundingClientRect();
  const rand = 6;

  let links = platz.left - 6;
  if (links + masse.width > window.innerWidth - rand) {
    links = Math.max(rand, window.innerWidth - rand - masse.width);
  }
  if (links < rand) links = rand;
  tafel.style.left = links + 'px';

  /* Oben bündig mit der Gruppe. Reicht sie nach unten aus dem Fenster,
     rutscht sie hinauf — lieber ein Stück über dem Band als halb
     abgeschnitten. */
  let oben = platz.top - 4;
  if (oben + masse.height > window.innerHeight - rand) {
    oben = Math.max(rand, window.innerHeight - rand - masse.height);
  }
  tafel.style.top = oben + 'px';

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(ev) {
      if (tafel.contains(ev.target) || knopf.contains(ev.target)) return;
      katalogKlappeWeg();
      document.removeEventListener('mousedown', zu);
    });
  }, 0);
}

let registerOffen = Speicher.lies('register', 'Start');
/* Eingeklappt zeigt das Register nur die Reiterzeile — wie in Word, wo ein
   Doppelklick auf den Reiter das Band wegräumt. Auf einem kleinen Bildschirm
   sind hundert Pixel viel. */
let registerEingeklappt = Speicher.lies('registerZu', false);

/* Die drei Wähler — Formatvorlage, Schrift, Größe. Sie stehen bei Word in
   der Gruppe „Schriftart", zusammen mit F, K und U; hier ebenso. Deshalb
   sind sie ein Baustein und keine eigene Gruppe mehr. */
/* Die vier Raender als Zahlenfelder, wie sie in WPS mitten im Band
   stehen. Bisher lagen sie hinter „Eigene Raender…" in einem Fenster —
   drei Klicks fuer eine Zahl, die man im Blick haben will, waehrend man
   sie aendert. */
function raenderKiste() {
  const kiste = document.createElement('div');
  kiste.className = 'register__raender';
  for (const [seite, name] of [['oben', 'Oben'], ['unten', 'Unten'],
                               ['links', 'Links'], ['rechts', 'Rechts']]) {
    const zeile = document.createElement('label');
    zeile.className = 'register__rand';

    const wort = document.createElement('span');
    wort.textContent = name + ':';
    zeile.appendChild(wort);

    const eingabe = document.createElement('input');
    eingabe.type = 'number';
    eingabe.min = '0'; eingabe.max = '90'; eingabe.step = '1';
    eingabe.value = String(seitenrand[seite]);
    eingabe.title = name + 'er Rand in Millimetern';
    /* Erst beim Verlassen oder bei Enter — sonst springt die Seite bei
       jedem getippten Zeichen, und aus „25" wird kurz „2". */
    const uebernehmen = () => {
      const zahl = parseFloat(String(eingabe.value).replace(',', '.'));
      if (Number.isNaN(zahl)) { eingabe.value = String(seitenrand[seite]); return; }
      seitenrand[seite] = Math.max(0, Math.min(90, zahl));
      eingabe.value = String(seitenrand[seite]);
      seiteAnwenden();
      abschnittMerken(abschnittJetztNr);
      melde(name + 'er Rand: ' + seitenrand[seite] + ' mm.');
    };
    eingabe.addEventListener('change', uebernehmen);
    eingabe.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); uebernehmen(); }
    });
    zeile.appendChild(eingabe);

    const mm = document.createElement('span');
    mm.className = 'register__einheit';
    mm.textContent = 'mm';
    zeile.appendChild(mm);

    kiste.appendChild(zeile);
  }
  return kiste;
}

function felderKiste() {
  const kiste = document.createElement('div');
  kiste.className = 'register__felder';

  /* ZWEI ZEILEN, NICHT DREI.

     Vorher standen Formatvorlage, Schrift und Groesse untereinander.
     Drei Zeilen neben zwei Knopfreihen: Die Gruppe wurde doppelt so
     hoch wie noetig, die Knoepfe rutschten nach rechts weg, und
     zwischen Waehlern und Knoepfen klaffte eine Luecke, in der nichts
     stand.

     In WPS steht die Schrift neben der Groesse, und die erste
     Knopfreihe faengt gleich daneben an. */
  if (wzVorlage) kiste.appendChild(wzVorlage);

  const untere = document.createElement('div');
  untere.className = 'register__felder-zeile';
  if (wzSchrift && wzSchrift.parentNode) untere.appendChild(wzSchrift.parentNode);
  if (wzGroesse) untere.appendChild(wzGroesse);
  kiste.appendChild(untere);
  return kiste;
}

/* Die rechte Spalte der Tafel.

   Sie hat zwei Zustaende. Im Ruhezustand stehen dort die zuletzt benutzten
   Dateien. Faehrt man ueber einen Punkt mit Pfeil, stehen dort dessen
   Unterpunkte.

   WARUM NICHT ALS EIGENES FENSTER

   Zuerst hingen die Untermenues als schwebende Klappen an den Punkten und
   legten sich ueber die Dateiliste. Zwei Kaesten uebereinander, der untere
   halb verdeckt — und die zweite Spalte, fuer die die Tafel ueberhaupt so
   breit ist, stand nutzlos dahinter. Im WPS Writer fuellt das Untermenue
   die rechte Spalte; die Tafel bleibt EIN Kasten. So jetzt auch hier. */
function tafelRechtsLeeren(rechts) {
  rechts.innerHTML = '';
}

/* Zustand eins: die zuletzt benutzten Dateien. */
function tafelRechtsZuletzt(rechts) {
  tafelRechtsLeeren(rechts);
  rechts.classList.remove('tafel__zuletzt--unter');

  const kopf = document.createElement('div');
  kopf.className = 'tafel__titel';
  kopf.textContent = 'Liste zuletzt verwendeter Dateien';

  const frisch = document.createElement('button');
  frisch.type = 'button';
  frisch.className = 'tafel__frisch';
  frisch.textContent = '↻';
  frisch.title = 'Liste neu holen';
  frisch.addEventListener('click', async (e) => {
    e.stopPropagation();
    await zuletztHolen();
    tafelRechtsZuletzt(rechts);
  });
  kopf.appendChild(frisch);
  rechts.appendChild(kopf);

  const rumpf = document.createElement('div');
  rumpf.className = 'tafel__liste';
  rechts.appendChild(rumpf);
  tafelListeFuellen(rumpf, rechts);
}

function tafelListeFuellen(rumpf, rechts) {
  rumpf.innerHTML = '';
  if (!zuletztListe.length) {
    const leer = document.createElement('div');
    leer.className = 'tafel__leer';
    leer.textContent = 'Noch nichts geöffnet.';
    rumpf.appendChild(leer);
    return;
  }
  zuletztListe.forEach((eintrag, nr) => {
    const zeile = document.createElement('div');
    zeile.className = 'tafel__zeile';

    const auf = document.createElement('button');
    auf.type = 'button';
    auf.className = 'tafel__datei';
    auf.addEventListener('click', () => { menueSchliessen(); B.zuletztOeffnen(nr); });

    const name = document.createElement('span');
    name.className = 'tafel__name';
    name.textContent = eintrag.name;
    auf.appendChild(name);

    const ordner = document.createElement('span');
    ordner.className = 'tafel__ordner';
    ordner.textContent = eintrag.ordner || '';
    auf.appendChild(ordner);
    zeile.appendChild(auf);

    const weg = document.createElement('button');
    weg.type = 'button';
    weg.className = 'tafel__weg';
    weg.textContent = '×';
    weg.title = 'Aus der Liste nehmen (die Datei bleibt)';
    weg.setAttribute('aria-label', 'Aus der Liste nehmen');
    weg.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        const antwort = await fetch('zuletzt-weg?nr=' + nr, { method: 'POST' });
        if (antwort.ok) zuletztListe = await antwort.json();
      } catch (f) { /* kein Server - dann bleibt die Liste, wie sie ist */ }
      tafelListeFuellen(rumpf, rechts);
    });
    zeile.appendChild(weg);
    rumpf.appendChild(zeile);
  });
}

/* Zustand zwei: die Unterpunkte eines Punktes mit Pfeil. */
function tafelRechtsUnter(rechts, titel, punkte) {
  tafelRechtsLeeren(rechts);
  rechts.classList.add('tafel__zuletzt--unter');

  const kopf = document.createElement('div');
  kopf.className = 'tafel__titel';
  kopf.textContent = titel;
  rechts.appendChild(kopf);

  const rumpf = document.createElement('div');
  rumpf.className = 'tafel__liste';
  for (const punkt of punkte) {
    if (punkt === strich) {
      const linie = document.createElement('div');
      linie.className = 'menue__strich';
      rumpf.appendChild(linie);
      continue;
    }
    const knopf = document.createElement('button');
    knopf.className = 'menue__punkt';
    knopf.setAttribute('role', 'menuitem');

    const haken = document.createElement('span');
    haken.className = 'haken';
    haken.textContent = punkt.haken && punkt.haken() ? '✓' : '';
    knopf.appendChild(haken);
    knopf.appendChild(document.createTextNode(punkt.name));

    if (punkt.taste) {
      const taste = document.createElement('span');
      taste.className = 'taste';
      taste.textContent = punkt.taste;
      knopf.appendChild(taste);
    }
    knopf.addEventListener('click', () => { menueSchliessen(); menuePunktTun(punkt); });
    rumpf.appendChild(knopf);
  }
  rechts.appendChild(rumpf);
}

/* Die linke Spalte. Eigener Bauer statt punkteBauen(): Der haengt an einen
   Punkt mit Unterpunkten eine schwebende Klappe, und genau die soll hier
   nicht entstehen. Punkte ohne Pfeil verhalten sich wie ueberall. */
function tafelBefehleBauen(links, rechts, punkte) {
  links.innerHTML = '';

  const nichtsOffen = () => {
    for (const a of links.querySelectorAll('.menue__punkt--offen')) {
      a.classList.remove('menue__punkt--offen');
    }
  };

  for (const punkt of punkte) {
    if (punkt === strich) {
      const linie = document.createElement('div');
      linie.className = 'menue__strich';
      links.appendChild(linie);
      continue;
    }

    const knopf = document.createElement('button');
    knopf.className = 'menue__punkt' + (punkt.unter ? ' menue__punkt--auf' : '');
    knopf.setAttribute('role', 'menuitem');

    const haken = document.createElement('span');
    haken.className = 'haken';
    haken.textContent = punkt.haken && punkt.haken() ? '✓' : '';
    knopf.appendChild(haken);
    knopf.appendChild(document.createTextNode(punkt.name));

    if (punkt.unter) {
      knopf.setAttribute('aria-haspopup', 'true');
      const pfeil = document.createElement('span');
      pfeil.className = 'menue__pfeil';
      pfeil.textContent = '›';
      knopf.appendChild(pfeil);

      const zeigen = () => {
        nichtsOffen();
        knopf.classList.add('menue__punkt--offen');
        tafelRechtsUnter(rechts, punkt.name,
                         typeof punkt.unter === 'function' ? punkt.unter() : punkt.unter);
      };
      knopf.addEventListener('mouseenter', zeigen);
      /* Ein Klick auf den Kopf fuehrt nichts aus und schliesst nichts —
         er zeigt nur, was rechts steht. Fuer die Tastatur und fuer den,
         der lieber klickt als faehrt. */
      knopf.addEventListener('click', (e) => { e.stopPropagation(); zeigen(); });
    } else {
      if (punkt.taste) {
        const taste = document.createElement('span');
        taste.className = 'taste';
        taste.textContent = punkt.taste;
        knopf.appendChild(taste);
      }
      /* Zurueck zur Dateiliste: Wer von "Drucken" nach "Oeffnen" faehrt,
         soll nicht die Druckpunkte rechts stehen lassen. */
      knopf.addEventListener('mouseenter', () => {
        if (!links.querySelector('.menue__punkt--offen')) return;
        nichtsOffen();
        tafelRechtsZuletzt(rechts);
      });
      knopf.addEventListener('click', () => { menueSchliessen(); menuePunktTun(punkt); });
    }
    links.appendChild(knopf);
  }
}

/* Die Befehle links in der Tafel — nach dem Foto des WPS-Menues.

   Elf Punkte, drei Striche, in genau dieser Reihenfolge. Das Foto ist die
   Vorgabe, nicht der Aufbau-Baum: Der fuehrt DATEI als flache Liste von
   siebzehn Punkten, und die stehen weiter so in der Menueleiste. Hier
   nicht.

   WAS AUS DEN SIEBZEHN WURDE

   Kein Befehl ist weggefallen, sie liegen nur anders. Die vier Pfeile des
   Fotos nehmen auf, was auf der ersten Ebene keinen Platz mehr hat:
   Vorlagen unter "Neu", Umbenennen und Eigenschaften unter "Speichern
   unter", Vorschau und Einstellungen unter "Drucken".

   Zwei Punkte des Fotos gab es hier nicht und sind gebaut worden: der
   Bild-Export (LibreOffice wandelt nach PNG) und die Verschluesselung
   (fuehrt auf die vorhandene Kennwort-Seite).

   "Zuletzt geoeffnet" ist kein Punkt mehr, sondern die rechte Spalte —
   auch das steht so im Foto. Und "Schliessen" fehlt dort; ein Dokument
   schliesst man ueber das Kreuz an seinem Reiter. */
function dateiTafelPunkte() {
  return [
    { name: 'Neu', unter: [
      { name: 'Leeres Dokument', tun: B.neu, taste: 'Strg+N' },
      { name: 'Neu aus Vorlage', tun: B.vorlagenWaehlen },
      { name: 'Vorlagenordner', tun: B.vorlagenOrdner },
    ] },
    { name: 'Öffnen', tun: B.oeffnen, taste: 'Strg+O' },
    { name: 'Speichern', tun: B.speichern, taste: 'Strg+S' },
    { name: 'Speichern unter', unter: [
      { name: 'Speichern unter …', tun: B.speichernUnter, taste: 'Strg+Umschalt+S' },
      { name: 'Umbenennen', tun: B.umbenennen },
      { name: 'Dokumenteigenschaften', tun: B.eigenschaften },
    ] },
    { name: 'Als PDF exportieren', tun: B.speichernPdf },
    /* Im Foto steht hier "Export as Image" — Englisch, weil WPS diese eine
       Zeile nicht uebersetzt hat. Eine fremde Luecke schreibe ich nicht ab. */
    { name: 'Als Bild exportieren', tun: B.speichernBild },
    { name: 'Drucken', unter: [
      { name: 'Drucken …', tun: B.drucken, taste: 'Strg+P' },
      { name: 'Druckvorschau', tun: B.vorschau },
      { name: 'Druckereinstellungen', tun: B.druckerEinrichten },
    ] },
    strich,
    { name: 'Dokumentverschlüsselung', unter: [
      { name: 'Kennwort setzen oder entfernen …',
        tun: () => Einstellungen.oeffnen('sicherheit') },
    ] },
    strich,
    { name: 'Hilfe', unter: [
      { name: 'Handbuch', tun: B.handbuch },
      { name: 'Tastenkürzel', tun: B.tastenHilfe },
      { name: 'Erweiterungen', tun: B.erweiterungen },
      { name: 'Über Lunivo Office', tun: B.ueber },
    ] },
    { name: 'Optionen', tun: () => Einstellungen.oeffnen(), taste: 'F9' },
    { name: 'Beenden', tun: B.beenden },
  ];
}

/* Der Schnellzugriff rechts vom Menuezeichen - die Handvoll Befehle, die
   man staendig braucht, ohne dafuer den Reiter zu wechseln. So steht er im
   Foto: gleich neben dem Menuezeichen, in derselben Zeile. */
const SCHNELLZUGRIFF = [
  ['oeffnen', 'Öffnen', () => B.oeffnen()],
  ['speichern', 'Speichern', () => B.speichern()],
  ['pdf', 'Als PDF exportieren', () => B.speichernPdf()],
  ['drucken', 'Drucken', () => B.drucken()],
  ['vorschau', 'Druckvorschau', () => B.vorschau()],
  ['zurueck', 'Rückgängig', () => B.rueckgaengig()],
  ['vor', 'Wiederholen', () => B.wiederholen()],
];

function schnellleisteBauen() {
  const leiste = $('register-schnell');
  if (!leiste) return;
  leiste.innerHTML = '';
  for (const [kennung, name, tun] of SCHNELLZUGRIFF) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'register__schnellknopf';
    k.title = name;
    k.setAttribute('aria-label', name);
    const bild = symbol(kennung);
    if (bild) k.appendChild(bild); else k.textContent = name;
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', tun);
    leiste.appendChild(k);
  }
}


/* Das ☰ Menü. Es steht an ZWEI Stellen, und das ist Absicht:

   Register       links vor den Reitern
   Symbolleisten  links am Anfang der oberen Leiste

   Vorher hing es nur am Register. Wer mit Symbolleisten arbeitete, hatte
   kein ☰ — die Datei-Befehle lagen dort verstreut zwischen den Symbolen,
   und der ganze Weg dorthin war die Menüleiste, die sich abschalten
   laesst. Damit trugen die drei Oberflaechen nicht mehr denselben Aufbau.

   Jeder Aufruf baut einen eigenen Kasten; geteilt wird nur die Liste der
   Punkte. Zwei Kaesten stoeren sich nicht: Offen ist immer nur einer,
   darauf passt menueSchliessen() auf. */
function menueKnopfBauen() {
  const kasten = document.createElement('div');
  kasten.className = 'menue menue--haupt';

  const knopf = document.createElement('button');
  knopf.type = 'button';
  knopf.className = 'menue__titel menue__hauptknopf';
  knopf.textContent = '\u2630 Menü \u25be';
  knopf.title = 'Neu, öffnen, speichern, drucken, Optionen, beenden';
  knopf.setAttribute('aria-haspopup', 'true');
  kasten.appendChild(knopf);

  /* Zwei Spalten, wie im Foto: links die Befehle, rechts die zuletzt
     benutzten Dateien. */
  const klappe = document.createElement('div');
  klappe.className = 'menue__klappe menue__tafel';
  klappe.setAttribute('role', 'menu');

  const links = document.createElement('div');
  links.className = 'tafel__befehle';
  klappe.appendChild(links);

  const rechts = document.createElement('div');
  rechts.className = 'tafel__zuletzt';
  klappe.appendChild(rechts);

  /* Erst die rechte Spalte, dann die linke: Die Punkte mit Pfeil brauchen
     beim Bauen schon den Kasten, den sie fuellen sollen. */
  tafelRechtsZuletzt(rechts);
  tafelBefehleBauen(links, rechts, dateiTafelPunkte());

  /* Faehrt der Zeiger aus der Tafel heraus, steht wieder die Dateiliste da
     — sonst begruesst das naechste Aufklappen mit den Druckpunkten. */
  klappe.addEventListener('mouseleave', () => {
    for (const a of links.querySelectorAll('.menue__punkt--offen')) {
      a.classList.remove('menue__punkt--offen');
    }
    tafelRechtsZuletzt(rechts);
  });

  kasten.appendChild(klappe);

  knopf.addEventListener('click', (e) => {
    e.stopPropagation();
    const warOffen = kasten.classList.contains('menue--offen');
    menueSchliessen();
    if (!warOffen) {
      kasten.classList.add('menue--offen');
      offenesMenue = kasten;
      seiteWaehlen(klappe);
    }
  });
  return kasten;
}

function registerBauen() {
  const reiter = $('register-reiter');
  const band = $('register-band');
  if (!reiter || !band) return;

  reiter.innerHTML = '';

  /* Links vor den Reitern das ☰ Menü. Es ist KEIN Reiter: Es schaltet das
     Band nicht um, es klappt senkrecht auf, und es bleibt stehen, welcher
     Reiter auch offen ist. So steht es im WPS Writer.

     Hier lag ein Reiter „Datei" mit sieben Gruppen. Wer speichern wollte,
     musste das Band wegschalten, speichern, und den alten Reiter wieder
     suchen — für einen Befehl, der im Menü einen Klick weit weg liegt.

     Die Punkte kommen aus MENUES, damit Menüleiste und ☰ nicht
     auseinanderlaufen. */
  const menueStelle = $('register-menue');
  if (menueStelle) {
    menueStelle.innerHTML = '';
    menueStelle.appendChild(menueKnopfBauen());
  }
  schnellleisteBauen();

  const zusatz = zusammenhangReiter();
  const alle = REGISTER.map(([name]) => [name, false])
    .concat(zusatz.map((r) => [r.name, true]));

  /* Steht der Zeiger nicht mehr in der Tabelle, ist der Reiter weg — und mit
     ihm der offene Bereich. Dann zurück auf Start, statt auf einen Reiter zu
     zeigen, den es nicht mehr gibt. */
  if (!alle.some(([name]) => name === registerOffen)) registerOffen = 'Start';

  for (const [name, imZusammenhang] of alle) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.textContent = name;
    knopf.setAttribute('role', 'tab');
    knopf.className = (name === registerOffen ? 'register--offen ' : '')
                    + (imZusammenhang ? 'register__zusatz' : '');
    if (imZusammenhang) knopf.title = 'Nur da, solange der Zeiger in einer Tabelle steht';
    knopf.addEventListener('click', () => {
      /* Ein Klick auf den offenen Reiter klappt wieder auf, wenn eingeklappt
         war. So kommt man an das Band, ohne die Einstellung zu ändern. */
      if (name === registerOffen && registerEingeklappt) {
        registerEingeklappt = false;
        Speicher.schreib('registerZu', false);
      }
      registerOffen = name;
      if (!imZusammenhang) Speicher.schreib('register', name);
      registerBauen();
    });
    /* Doppelklick klappt ein und aus — wie in Word. */
    knopf.addEventListener('dblclick', () => {
      registerEingeklappt = !registerEingeklappt;
      Speicher.schreib('registerZu', registerEingeklappt);
      registerBauen();
    });
    reiter.appendChild(knopf);
  }

  /* Hier stand ein zweites ☰ ganz rechts, das die ganze Menüleiste ein- und
     ausblendete. Neben dem ☰ Menü links sind das zwei gleiche Zeichen mit
     zwei verschiedenen Bedeutungen in einer Zeile — das erklärt niemand.

     Weggenommen, nicht versteckt: Die Menüleiste kommt über
     Ansicht ▸ Oberfläche ▸ Menüleiste und über die Alt-Taste. */

  band.hidden = registerEingeklappt;
  document.body.classList.toggle('register--zu', registerEingeklappt);
  band.innerHTML = '';
  /* Die Knöpfe von vorhin gibt es gleich nicht mehr. */
  registerSchalter = [];
  if (registerEingeklappt) { registerPfeile(); return; }

  const ausZusatz = zusatz.find((r) => r.name === registerOffen);
  const gewaehlt = ausZusatz
    ? ausZusatz.gruppen
    : registerGruppenFuer(registerOffen,
        (REGISTER.find(([name]) => name === registerOffen) || REGISTER[0])[1]);

  for (const [gruppenName, eintraege, oeffner] of gewaehlt) {
    const gruppe = document.createElement('div');
    gruppe.className = 'register__gruppe';

    /* Der Katalog zeigt die Formatvorlagen, statt sie zu benennen. */
    if (eintraege === 'katalog') {
      /* „Formatvorlagen verwalten" stand hier einmal als eigenes Zeichen
         unter dem Katalog — allein in der Mitte, unter einer Reihe, die
         doppelt so breit war. Es steht jetzt in der Klappe, dort, wo man
         ohnehin hinsieht, wenn man mehr Vorlagen sucht. */
      gruppe.appendChild(katalogBauen());

      const name = document.createElement('span');
      name.className = 'register__name';
      name.textContent = gruppenName;
      gruppe.appendChild(name);
      band.appendChild(gruppe);
      continue;
    }

    /* Die Wähler wandern aus der Werkzeugleiste hierher. Beim Zurückschalten
       baut werkzeugeBauen() sie ohnehin neu — es geht also nichts verloren. */
    if (eintraege === 'raender') {
      gruppe.appendChild(raenderKiste());

      const name = document.createElement('span');
      name.className = 'register__name';
      name.textContent = gruppenName;
      gruppe.appendChild(name);
      band.appendChild(gruppe);
      continue;
    }

    if (eintraege === 'felder') {
      gruppe.appendChild(felderKiste());

      const name = document.createElement('span');
      name.className = 'register__name';
      name.textContent = gruppenName;
      gruppe.appendChild(name);
      band.appendChild(gruppe);
      continue;
    }

    const reihe = document.createElement('div');
    reihe.className = 'register__reihe';

    /* Die großen zuerst, links, mit Beschriftung. Die kleinen sammeln sich
       rechts davon in einem Gitter — so entsteht die Form, die ein Ribbon
       ausmacht: wenige große Ziele und viel Kleines daneben. */
    const kleineKiste = document.createElement('div');
    kleineKiste.className = 'register__klein';

    const bauen = (zeichen, titel, tun, gross) => {
      const k = document.createElement('button');
      k.className = gross ? 'wz register__gross' : 'wz';
      k.type = 'button';
      k.title = titel;
      k.setAttribute('aria-label', titel);
      /* Steht im Vorrat ein Symbol dieses Namens, kommt das Bild; sonst
         das Wort selbst. F, K, U und S sind in deutschen Schreibprogrammen
         Buchstaben, kein Behelf. */
      const hatSymbol = !!SYMBOLE[zeichen];
      if (hatSymbol) k.appendChild(symbol(zeichen));
      else if (!gross) {
        const wort = document.createElement('span');
        wort.className = 'register__zeichen';
        wort.textContent = zeichen;
        /* F, K, U und S sind in deutschen Schreibprogrammen Buchstaben,
           kein Behelf — und sie zeigen ihre Wirkung an sich selbst: das F
           fett, das K kursiv, das U unterstrichen, das S durchgestrichen.
           So steht es in der Symbolleiste, und so gehört es auch hier. */
        const wieDasWort = { 'F': 'wz--fett', 'K': 'wz--kursiv',
                             'U': 'wz--unter', 'S': 'wz--durch' }[zeichen];
        if (wieDasWort) k.classList.add(wieDasWort);
        k.appendChild(wort);
        /* Ein Knopf, der ein Wort trägt, bekommt einen eigenen Rand.
           Ohne ihn standen „Unterart" und „Aa" nebeneinander und lasen
           sich als ein Wort — für jemanden mit Legasthenie die
           unnötigste aller Hürden. */
        k.classList.add('wz--wort');
      }
      /* Ein großer Knopf ohne Symbol trägt nur sein Wort. Sonst stünde bei
         „Übersetzen" zweimal dasselbe untereinander. */
      if (gross) {
        const beschriftung = document.createElement('span');
        beschriftung.className = hatSymbol
          ? 'register__beschriftung'
          : 'register__beschriftung register__beschriftung--allein';
        beschriftung.textContent = titel;
        k.appendChild(beschriftung);
      }
      k.addEventListener('mousedown', (e) => e.preventDefault());
      /* Ist statt eines Befehls eine Liste angegeben, klappt der Knopf sie
         auf — wie „Größe" oder „Seitenränder" im Menüband von Word. Fünf
         Papierformate nebeneinander sind fünf Knöpfe; einer mit Klappe ist
         einer, und man sieht trotzdem, welches gerade gilt. */
      if (Array.isArray(tun)) {
        k.classList.add('wz--klappe');
        const pfeil = document.createElement('span');
        pfeil.className = 'wz__pfeil';
        pfeil.textContent = '▾';
        k.appendChild(pfeil);
        k.addEventListener('click', () => registerKlappe(k, tun));
      } else {
        /* Nach dem Klick nachsehen, was jetzt an ist. Ein Schalter, der
           seinen Zustand erst beim nächsten Neubau des Bandes zeigt,
           leuchtet noch, wenn er längst aus ist. */
        /* Der Knopf wird mitgereicht: Wer eine Klappe darunter aufgehen
           lässt — der Rasterwähler der Tabellen —, muss wissen, wo er
           steht. Alle anderen Befehle nehmen kein Argument und merken
           nichts davon. */
        k.addEventListener('click', () => { tun(k); registerSchalterAuffrischen(); });
      }
      return k;
    };

    /* Ein geteilter Knopf: links das Zeichen, rechts ein Pfeil.
       In WPS hat das U einen Pfeil fuer die Strichvorlagen, der Marker
       einen fuer die Farben, das A einen fuer die Schriftfarbe. Ein
       Klick auf das Zeichen wirkt sofort mit dem, was zuletzt galt; der
       Pfeil zeigt die Auswahl.

       Er hat es so aufgeschrieben: „Die Strichvorlagen aus dem Bild
       fehlen aktuell." Sie fehlten nicht — sie lagen hinter einem
       zweiten, gleich aussehenden U-Knopf daneben. Zwei Knoepfe mit
       demselben Buchstaben sind schlimmer als ein fehlender Pfeil. */
    const bauenGeteilt = (zeichen, titel, tun, klappe, gross) => {
      const kiste = document.createElement('span');
      kiste.className = 'wz-geteilt' + (gross ? ' wz-geteilt--gross' : '');

      const k = bauen(zeichen, titel, tun, !!gross);
      k.classList.add('wz-geteilt__tat');
      kiste.appendChild(k);

      const pfeil = document.createElement('button');
      pfeil.type = 'button';
      pfeil.className = 'wz wz-geteilt__pfeil';
      pfeil.title = titel + ' — Auswahl';
      pfeil.setAttribute('aria-label', titel + ' — Auswahl');
      pfeil.textContent = '▾';
      pfeil.addEventListener('mousedown', (e) => e.preventDefault());
      pfeil.addEventListener('click', () => klappe(pfeil));
      kiste.appendChild(pfeil);
      return { kiste, knopf: k };
    };

    /* ZEILENWEISE STATT SPALTENWEISE.

       Das Gitter der kleinen Knoepfe fuellt sich sonst spaltenweise: Wer
       F, K, U, S auflistet, bekommt F und U untereinander und K und S
       daneben. Auf seinem Bildschirmfoto standen darum Fett und Kursiv
       in verschiedenen Zeilen, Hoch- und Tiefgestellt auseinander. Er
       hat es genau so aufgeschrieben: „Hoch- und tiefgestellt gehoeren
       nebeneinander als Gruppe zur selben Funktion."

       Steht ein ['//'] in der Liste, wird die Gruppe in feste Reihen
       gebaut — dann steht dort, was er sieht, und nicht, was das Gitter
       daraus macht. */
    const inReihen = eintraege.some((e) => Array.isArray(e) && e[0] === '//');
    if (inReihen) kleineKiste.classList.add('register__klein--reihen');
    let zeileJetzt = null;
    const neueZeile = () => {
      zeileJetzt = document.createElement('span');
      zeileJetzt.className = 'register__knopfreihe';
      kleineKiste.appendChild(zeileJetzt);
      return zeileJetzt;
    };
    if (inReihen) neueZeile();

    for (const eintrag of eintraege) {
      /* Ein 'felder' mitten in der Liste heißt: hier stehen die Wähler.

         IN EINER GRUPPE MIT FESTEN ZEILEN gehoeren sie IN die erste
         Zeile, nicht daneben. In WPS steht die Schrift, daneben die
         Groesse, daneben A⁺ A⁻ ◇ Aa — alles eine Linie —, und die
         zweite Knopfreihe laeuft darunter durch, bis an den linken
         Rand. Setzt man die Waehler als eigenen Block davor, steht die
         Gruppe in zwei Saeulen statt in zwei Zeilen, und genau das hat
         er auf dem Bildschirmfoto gesehen. */
      if (eintrag === 'felder') {
        (inReihen ? zeileJetzt : reihe).appendChild(felderKiste());
        continue;
      }
      if (Array.isArray(eintrag) && eintrag[0] === '//') { neueZeile(); continue; }
      const [zeichen, titel, tun, gross, zustand] = eintrag;

      /* Ist statt eines Befehls ein Paar angegeben, wird es ein
         geteilter Knopf: { tun, klappe }. */
      if (tun && typeof tun === 'object' && typeof tun.tun === 'function') {
        const { kiste, knopf } = bauenGeteilt(zeichen, titel, tun.tun, tun.klappe, !!gross);
        if (typeof zustand === 'function') registerSchalter.push({ knopf, ist: zustand });
        /* Ein grosser geteilter Knopf gehoert in die Reihe, nicht in das
           Gitter der kleinen — sonst steht „Einfuegen" plotzlich
           zwischen den Zeichen. */
        if (gross) reihe.appendChild(kiste);
        else (zeileJetzt || kleineKiste).appendChild(kiste);
        continue;
      }

      const k = bauen(zeichen, titel, tun, !!gross);
      if (typeof zustand === 'function') registerSchalter.push({ knopf: k, ist: zustand });
      if (gross) reihe.appendChild(k);
      else (zeileJetzt || kleineKiste).appendChild(k);
    }
    if (kleineKiste.childNodes.length) reihe.appendChild(kleineKiste);
    gruppe.appendChild(reihe);

    /* Der Fuß trägt den Namen — und rechts den Pfeil, wenn es mehr gibt,
       als in die Gruppe passt. */
    const fuss = document.createElement('div');
    fuss.className = 'register__fuss';

    const name = document.createElement('span');
    name.className = 'register__name';
    name.textContent = gruppenName;
    fuss.appendChild(name);

    if (typeof oeffner === 'function') {
      const pfeil = document.createElement('button');
      pfeil.type = 'button';
      pfeil.className = 'register__starter';
      pfeil.textContent = '⭨';
      pfeil.title = gruppenName + ' — alle Einstellungen';
      pfeil.setAttribute('aria-label', gruppenName + ' — alle Einstellungen');
      pfeil.addEventListener('mousedown', (e) => e.preventDefault());
      pfeil.addEventListener('click', () => oeffner(pfeil));
      fuss.appendChild(pfeil);
    }

    gruppe.appendChild(fuss);
    band.appendChild(gruppe);
  }

  registerSchalterAuffrischen();
  registerPfeile();
}

/* ------------------------------------------------------------
   Ein Symbol austauschen

   LibreOffice kann das für seine Symbolleisten (Anpassen ▸ Symbolleisten ▸
   Ändern ▸ Symbol austauschen), für sein Symbolband aber nicht — dort
   lassen sich nur Befehle an- und abwählen. Hier geht beides.

   Getauscht wird die Zeichnung, nicht der Knopf: Wer „notiz" ersetzt,
   ändert sie überall, wo sie benutzt wird. Das Fenster sagt deshalb dazu,
   welche Befehle daran hängen.

   Der Katalog mit 1800 Zeichnungen wird erst geholt, wenn dieses Fenster
   aufgeht. Beim Start wären 300 KB für etwas, das man selten braucht, zu
   spüren.
   ------------------------------------------------------------ */
let symbolWahl = Speicher.lies('symbole', {});   /* unten gleich nachgebaut */
let katalogGeladen = false;

/* Der Pfad, der wirklich gezeichnet wird: die eigene Wahl, sonst der
   Auslieferungszustand. */
function symbolPfad(name) {
  return (symbolWahl && symbolWahl[name]) || SYMBOLE[name];
}

function katalogHolen() {
  if (katalogGeladen || typeof SYMBOLKATALOG !== 'undefined') { katalogGeladen = true; return Promise.resolve(true); }
  return new Promise((fertig) => {
    const stueck = document.createElement('script');
    stueck.src = 'daten/symbolkatalog.js';
    stueck.onload = () => { katalogGeladen = true; fertig(true); };
    stueck.onerror = () => fertig(false);
    document.head.appendChild(stueck);
  });
}

/* Welche Befehle hängen an dieser Zeichnung? Das beantwortet die Frage
   „was ändere ich hier eigentlich?", bevor man sie ändert.

   Gesucht wird an zwei Stellen, und beide sind nötig: im Register stehen
   alle Reiter, auch die gerade nicht sichtbaren — dort hilft die Liste.
   Die Symbolleisten dagegen werden gebaut, nicht aufgelistet; sie kennt
   nur der Baum. Ohne den zweiten Blick hieß es bei „Hochgestellt", es
   werde nirgends benutzt, während der Knopf danebenstand. */
function symbolBefehle(name) {
  const namen = [];
  const merken = (wort) => {
    const sauber = (wort || '').replace(/\s*\([^)]*\)\s*$/, '').trim();
    if (sauber && !namen.includes(sauber)) namen.push(sauber);
  };

  for (const [, gruppen] of REGISTER) {
    for (const [, eintraege] of gruppen) {
      if (!Array.isArray(eintraege)) continue;
      for (const eintrag of eintraege) {
        if (Array.isArray(eintrag) && eintrag[0] === name) merken(eintrag[1]);
      }
    }
  }

  const pfad = symbolPfad(name);
  for (const knopf of document.querySelectorAll('.werkzeugleiste .wz')) {
    const strich = knopf.querySelector('svg path');
    if (strich && strich.getAttribute('d') === pfad) merken(knopf.title);
  }
  return namen;
}

/* ---- Eigene Zeichnungen ----

   Der Katalog hat 1800 Zeichnungen, und trotzdem fehlt manchmal genau die
   eine. Deshalb kann man hier eine eigene hereingeben: eine SVG-Datei, wie
   sie im Netz steht, oder nur die Pfaddaten.

   Zwei Dinge muessen dabei passieren.

   ERSTENS DAS MASS. Unsere Symbole sitzen in einem Feld von 24 x 24. Eine
   fremde Zeichnung hat ihr eigenes Mass, oft 16, 32 oder 512. Aus ihrer
   viewBox wird ausgerechnet, wie sie zu verkleinern und zu ruecken ist,
   damit sie mittig in unser Feld passt.

   ZWEITENS DIE SICHERHEIT. Was hereingereicht wird, ist fremder Text. Er
   wird nicht uebernommen, sondern nachgebaut: Aus der eingelesenen
   Zeichnung werden nur die Formen abgeschrieben, die wir kennen, und von
   ihnen nur die Masszahlen. Alles andere — Skripte, Verweise, Stile,
   Ereignisse — bleibt draussen. Was hinterher im Speicher steht, haben wir
   selbst geschrieben. */
const SVG_RAUM = 'http://www.w3.org/2000/svg';

const SVG_FORMEN = {
  path:     ['d'],
  circle:   ['cx', 'cy', 'r'],
  ellipse:  ['cx', 'cy', 'rx', 'ry'],
  rect:     ['x', 'y', 'width', 'height', 'rx', 'ry'],
  line:     ['x1', 'y1', 'x2', 'y2'],
  polyline: ['points'],
  polygon:  ['points'],
};
/* Was in einer Masszahl stehen darf — und in Pfaddaten zusaetzlich die
   Buchstaben der Befehle. Mehr nicht. */
const NUR_ZAHLEN = /^[0-9eE.,+\-\s]*$/;
const NUR_PFAD   = /^[0-9eE.,+\-\sMmLlHhVvCcSsQqTtAaZz]*$/;

/** Baut aus fremdem SVG-Text eine eigene Zeichnung fuer unser 24er-Feld.
    Gibt die Markierung zurueck oder null, wenn nichts Brauchbares drin war. */
function eigeneZeichnung(roh, gefuellt) {
  const text = String(roh || '').trim();
  if (!text) return null;

  /* Nur Pfaddaten, ohne Huelle: Dann ist das Mass schon unseres. */
  if (text.indexOf('<') === -1) {
    return NUR_PFAD.test(text) ? text : null;
  }

  let baum;
  try {
    baum = new DOMParser().parseFromString(text, 'image/svg+xml');
  } catch (e) { return null; }
  if (!baum || baum.querySelector('parsererror')) return null;
  const wurzel = baum.documentElement;
  if (!wurzel || wurzel.localName !== 'svg') return null;

  /* Das Mass der fremden Zeichnung. Fehlt die viewBox, tun es Breite und
     Hoehe; fehlen auch die, wird 24 angenommen. */
  let vx = 0, vy = 0, vb = 24, vh = 24;
  const kasten = (wurzel.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(Number);
  if (kasten.length === 4 && kasten.every((z) => Number.isFinite(z)) && kasten[2] > 0 && kasten[3] > 0) {
    [vx, vy, vb, vh] = kasten;
  } else {
    const b = parseFloat(wurzel.getAttribute('width'));
    const h = parseFloat(wurzel.getAttribute('height'));
    if (b > 0 && h > 0) { vb = b; vh = h; }
  }

  const gruppe = document.createElementNS(SVG_RAUM, 'g');
  let formen = 0;
  for (const el of wurzel.querySelectorAll(Object.keys(SVG_FORMEN).join(','))) {
    const art = el.localName;
    const erlaubt = SVG_FORMEN[art];
    if (!erlaubt) continue;
    const neu = document.createElementNS(SVG_RAUM, art);
    let hatMass = false;
    for (const eigen of erlaubt) {
      const wert = el.getAttribute(eigen);
      if (wert === null) continue;
      const pruefer = eigen === 'd' ? NUR_PFAD : NUR_ZAHLEN;
      if (!pruefer.test(wert)) { hatMass = false; break; }
      neu.setAttribute(eigen, wert.trim());
      hatMass = true;
    }
    if (!hatMass) continue;
    gruppe.appendChild(neu);
    formen++;
  }
  if (!formen) return null;

  /* Mittig hineinlegen, Seitenverhaeltnis behalten. */
  const mass = Math.min(24 / vb, 24 / vh);
  const nachRechts = (24 - vb * mass) / 2 - vx * mass;
  const nachUnten  = (24 - vh * mass) / 2 - vy * mass;
  const kurz = (z) => (Math.round(z * 1000) / 1000);
  gruppe.setAttribute('transform',
    'translate(' + kurz(nachRechts) + ' ' + kurz(nachUnten) + ') scale(' + kurz(mass) + ')');
  /* Ein gefuelltes Zeichen als Strich zu malen gaebe eine leere Huelle.
     Deshalb die Wahl — und die Strichbreite muss dabei mitverkleinert
     werden, sonst wird sie durch die Skalierung dicker oder duenner als
     bei allen anderen Symbolen. */
  if (gefuellt) {
    gruppe.setAttribute('fill', 'currentColor');
    gruppe.setAttribute('stroke', 'none');
  } else {
    gruppe.setAttribute('stroke-width', String(kurz(1.7 / mass)));
  }
  return new XMLSerializer().serializeToString(gruppe);
}

/* Was aus dem Speicher kommt, wird noch einmal durch denselben Nachbau
   geschickt. Der Speicher gehoert dem Menschen und niemandem sonst — aber
   eine Zeichnung, die niemand geprueft hat, wird hier nicht gezeichnet. */
function wahlSaeubern(wahl) {
  const rein = {};
  for (const [name, inhalt] of Object.entries(wahl || {})) {
    if (typeof inhalt !== 'string') continue;
    if (inhalt.indexOf('<') === -1) { if (NUR_PFAD.test(inhalt)) rein[name] = inhalt; continue; }
    const gepruefte = eigeneZeichnung(
      '<svg xmlns="' + SVG_RAUM + '" viewBox="0 0 24 24">' + inhalt + '</svg>',
      /fill="currentColor"/.test(inhalt));
    if (gepruefte) rein[name] = gepruefte;
  }
  return rein;
}

/* Beim Start einmal durch den Nachbau — siehe wahlSaeubern. Das Ergebnis
   wird gleich zurueckgeschrieben: Was nicht gezeichnet wird, soll auch
   nicht im Speicher liegen bleiben. */
symbolWahl = wahlSaeubern(symbolWahl);
Speicher.schreib('symbole', symbolWahl);

function symbolNeuZeichnen() {
  Speicher.schreib('symbole', symbolWahl);
  werkzeugeBauen();
  registerBauen();
  werkzeugeAuffrischen();
}

/* Welches Symbol steckt in dem Knopf, auf den geklickt wurde? Gesucht wird
   über den gezeichneten Pfad — der Knopf selbst trägt seinen Namen nicht,
   und ihn überall mitzuschreiben wäre eine zweite Buchführung. */
function symbolUnter(ziel) {
  const knopf = ziel && ziel.closest && ziel.closest('.wz');
  const bild = knopf && knopf.querySelector('svg');
  if (!bild) return null;
  /* Seit das Bild seinen Namen traegt, steht er einfach da. Der Weg ueber
     den Pfad bleibt fuer Knoepfe, die vor dieser Aenderung gezeichnet
     wurden — und fuer den Fall, dass irgendwo noch einer von Hand gebaut
     wird. Bei eigenen Zeichnungen gibt es keinen einzelnen Pfad. */
  if (bild.dataset && bild.dataset.symbol) return bild.dataset.symbol;
  const strich = bild.querySelector('path');
  if (!strich) return null;
  const d = strich.getAttribute('d');
  return Object.keys(SYMBOLE).find((n) => symbolPfad(n) === d) || null;
}

/* Dieselbe Bedienung an den klassischen Symbolleisten. Wer von dort kommt,
   soll nicht erst ins Register wechseln müssen, um ein Bild zu tauschen. */
(() => {
  for (const leiste of ['werkzeugleiste', 'werkzeugleiste2']) {
    const kasten = $(leiste);
    if (!kasten) continue;
    kasten.addEventListener('contextmenu', (e) => {
      const name = symbolUnter(e.target);
      if (!name) return;                 /* daneben: nichts abfangen */
      e.preventDefault();
      B.symbolTauschen(name);
    });
  }
})();

/* Das Fenster fuer eine eigene Zeichnung. Die Vorschau zeichnet mit,
   waehrend getippt wird: Ob eine fremde SVG bei uns brauchbar aussieht,
   sieht man erst, wenn man sie sieht. */
function eigeneFragen(welches, danach) {
  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog dialog--breit';
  kasten.innerHTML =
    '<h3 class="dialog__titel">Eigene Zeichnung</h3>'
    + '<p class="dialog__satz">Eine SVG-Datei hier hineinkopieren — oder nur '
    + 'die Pfaddaten. Sie wird auf 24 &#215; 24 gebracht und mittig eingepasst.</p>'
    + '<div class="eigenzeichen">'
    + '<textarea class="eigenzeichen__feld" spellcheck="false" '
    + 'placeholder="&lt;svg viewBox=&quot;0 0 24 24&quot;&gt;&#8230;&lt;/svg&gt;"></textarea>'
    + '<div class="eigenzeichen__schau"><div class="eigenzeichen__bild"></div>'
    + '<span class="eigenzeichen__wort">Noch nichts</span></div>'
    + '</div>'
    + '<label class="eigenzeichen__wahl"><input type="checkbox"> '
    + 'Gef&#252;llt zeichnen (f&#252;r Zeichnungen aus Fl&#228;chen statt Strichen)</label>';

  const feld     = kasten.querySelector('.eigenzeichen__feld');
  const bild     = kasten.querySelector('.eigenzeichen__bild');
  const wort     = kasten.querySelector('.eigenzeichen__wort');
  const gefuellt = kasten.querySelector('.eigenzeichen__wahl input');

  let fertig = null;
  const schauen = () => {
    fertig = eigeneZeichnung(feld.value, gefuellt.checked);
    bild.textContent = '';
    if (!fertig) {
      wort.textContent = feld.value.trim() ? 'Daraus wird keine Zeichnung.' : 'Noch nichts';
      return;
    }
    const s = document.createElementNS(SVG_RAUM, 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('width', '48'); s.setAttribute('height', '48');
    s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor');
    s.setAttribute('stroke-width', '1.7');
    s.setAttribute('stroke-linecap', 'round');
    s.setAttribute('stroke-linejoin', 'round');
    if (fertig.indexOf('<') === -1) {
      const pf = document.createElementNS(SVG_RAUM, 'path');
      pf.setAttribute('d', fertig);
      s.appendChild(pf);
    } else { s.innerHTML = fertig; }
    bild.appendChild(s);
    wort.textContent = 'So kommt sie in die Leiste.';
  };
  feld.addEventListener('input', schauen);
  gefuellt.addEventListener('change', schauen);

  const knoepfe = document.createElement('div');
  knoepfe.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  const ok = document.createElement('button');
  ok.className = 'knopf knopf--haupt'; ok.textContent = 'Übernehmen';
  knoepfe.append(ab, ok);
  kasten.appendChild(knoepfe);
  grund.appendChild(kasten);
  document.body.appendChild(grund);
  feld.focus();

  const zu = () => grund.remove();
  ab.addEventListener('click', zu);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) zu(); });
  document.addEventListener('keydown', function flucht(e) {
    if (!document.body.contains(grund)) { document.removeEventListener('keydown', flucht); return; }
    if (e.key === 'Escape') { e.preventDefault(); zu(); }
  });
  ok.addEventListener('click', () => {
    if (!fertig) { melde('Daraus wird keine Zeichnung — steht wirklich eine SVG darin?'); return; }
    symbolWahl[welches] = fertig;
    zu();
    if (danach) danach();
    melde('Eigene Zeichnung übernommen.');
  });
  schauen();
}

B.symbolTauschen = async (vorgabe) => {
  const da = await katalogHolen();
  if (!da) { melde('Der Symbolkatalog ließ sich nicht laden.'); return; }

  const knoten = document.createElement('div');
  knoten.className = 'tausch';

  /* Oben: welches Symbol gerade gemeint ist. */
  const kopf = document.createElement('div');
  kopf.className = 'tausch__kopf';
  const jetztBild = document.createElement('span');
  jetztBild.className = 'tausch__jetzt';
  const jetztWort = document.createElement('div');
  jetztWort.className = 'tausch__wort';
  kopf.append(jetztBild, jetztWort);
  knoten.appendChild(kopf);

  const suchfeld = document.createElement('input');
  suchfeld.className = 'feld tausch__suche';
  suchfeld.type = 'search';
  suchfeld.placeholder = 'Zeichnung suchen … (englisch: table, clock, save)';
  knoten.appendChild(suchfeld);

  const gitter = document.createElement('div');
  gitter.className = 'tausch__gitter';
  knoten.appendChild(gitter);

  const fuss = document.createElement('div');
  fuss.className = 'tausch__fuss';
  const zurueck = document.createElement('button');
  zurueck.type = 'button';
  zurueck.className = 'knopf knopf--klein';
  zurueck.textContent = 'Dieses zurücksetzen';
  const alleZurueck = document.createElement('button');
  alleZurueck.type = 'button';
  alleZurueck.className = 'knopf knopf--klein';
  alleZurueck.textContent = 'Alle zurücksetzen';
  /* Der Katalog hat 1800 Zeichnungen, und trotzdem fehlt manchmal genau
     die eine. Dann bringt man seine eigene mit. */
  const eigene = document.createElement('button');
  eigene.type = 'button';
  eigene.className = 'knopf knopf--klein';
  eigene.textContent = 'Eigene Zeichnung…';
  fuss.append(eigene, zurueck, alleZurueck);
  knoten.appendChild(fuss);

  /* Welches Symbol wird bearbeitet. Ohne Vorgabe das erste des Registers. */
  let welches = vorgabe && SYMBOLE[vorgabe] ? vorgabe : Object.keys(SYMBOLE)[0];

  const kopfZeigen = () => {
    jetztBild.textContent = '';
    jetztBild.appendChild(symbol(welches));
    const befehle = symbolBefehle(welches);
    jetztWort.textContent = befehle.length
      ? befehle.slice(0, 4).join(', ') + (befehle.length > 4 ? ' und weitere' : '')
      : 'Wird zurzeit nirgends im Register benutzt.';
    zurueck.disabled = !symbolWahl[welches];
  };

  const GRENZE = 240;
  const gitterZeigen = () => {
    const wort = suchfeld.value.trim().toLowerCase();
    gitter.textContent = '';
    let gezeigt = 0, gefunden = 0;
    for (const [name, pfad] of Object.entries(SYMBOLKATALOG)) {
      if (wort && name.toLowerCase().indexOf(wort) === -1) continue;
      gefunden++;
      if (gezeigt >= GRENZE) continue;
      gezeigt++;
      const feld = document.createElement('button');
      feld.type = 'button';
      feld.className = 'tausch__feld';
      feld.title = name;
      const bild = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      bild.setAttribute('viewBox', '0 0 24 24');
      bild.setAttribute('width', '24'); bild.setAttribute('height', '24');
      bild.setAttribute('fill', 'none'); bild.setAttribute('stroke', 'currentColor');
      bild.setAttribute('stroke-width', '1.7');
      bild.setAttribute('stroke-linecap', 'round');
      bild.setAttribute('stroke-linejoin', 'round');
      const strich = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      strich.setAttribute('d', pfad);
      bild.appendChild(strich);
      feld.appendChild(bild);
      feld.addEventListener('click', () => {
        symbolWahl[welches] = pfad;
        symbolNeuZeichnen();
        kopfZeigen();
        melde('Symbol getauscht: ' + name + '.');
      });
      gitter.appendChild(feld);
    }
    if (!gefunden) {
      const leer = document.createElement('p');
      leer.className = 'tausch__leer';
      leer.textContent = 'Keine Zeichnung mit diesem Namen.';
      gitter.appendChild(leer);
    } else if (gefunden > GRENZE) {
      const mehr = document.createElement('p');
      mehr.className = 'tausch__leer';
      mehr.textContent = gefunden + ' gefunden, ' + GRENZE
        + ' gezeigt — die Suche genauer machen.';
      gitter.appendChild(mehr);
    }
  };

  suchfeld.addEventListener('input', gitterZeigen);
  eigene.addEventListener('click', () => eigeneFragen(welches, () => {
    symbolNeuZeichnen();
    kopfZeigen();
  }));
  zurueck.addEventListener('click', () => {
    delete symbolWahl[welches];
    symbolNeuZeichnen();
    kopfZeigen();
    melde('Zurückgesetzt.');
  });
  alleZurueck.addEventListener('click', () => {
    symbolWahl = {};
    symbolNeuZeichnen();
    kopfZeigen();
    melde('Alle Symbole wieder wie ausgeliefert.');
  });

  kopfZeigen();
  gitterZeigen();

  fenster('Symbol austauschen', [
    { art: 'satz', text: 'Getauscht wird die Zeichnung, nicht der Knopf — sie ändert sich\n'
                       + 'überall, wo sie benutzt wird. Oben steht, wo das ist.' },
    { art: 'knoten', knoten },
  ], null, 'Fertig', true);
};

/* ---- Die Klappe eines Bandknopfes ----
   Sie hängt am Körper, nicht am Knopf: Im Band wird abgeschnitten, was
   übersteht, und eine Klappe im Knopf wäre nach zwei Zeilen weg. Deshalb
   steht sie fest im Fenster und wird an die Stelle des Knopfes gerechnet.

   Ein Haken zeigt, was gerade gilt — sonst müsste man raten, ob man schon
   auf A5 steht. */
let klappeOffen = null;

function klappeSchliessen() {
  if (!klappeOffen) return;
  klappeOffen.remove();
  klappeOffen = null;
}

/* Ein kleines Blatt mit angedeutetem Satzspiegel — vier Zahlen als Bild.
   In WPS steht neben jedem Randmass so eine Kachel, und sie zeigt auf
   einen Blick, was „Breit" bedeutet. */
function randbild(rand) {
  const ns = 'http://www.w3.org/2000/svg';
  const sv = document.createElementNS(ns, 'svg');
  sv.setAttribute('viewBox', '0 0 24 32');
  sv.setAttribute('class', 'klappzeile__bild klappzeile__blatt');
  sv.setAttribute('aria-hidden', 'true');

  const blatt = document.createElementNS(ns, 'rect');
  blatt.setAttribute('x', '1'); blatt.setAttribute('y', '1');
  blatt.setAttribute('width', '22'); blatt.setAttribute('height', '30');
  blatt.setAttribute('fill', 'none');
  blatt.setAttribute('stroke', 'currentColor');
  sv.appendChild(blatt);

  /* Die Raender in Millimetern auf ein Blatt von 210 x 297 umgerechnet. */
  const x = 1 + 22 * rand.links / 210;
  const y = 1 + 30 * rand.oben / 297;
  const b = 22 * (210 - rand.links - rand.rechts) / 210;
  const h = 30 * (297 - rand.oben - rand.unten) / 297;
  const satz = document.createElementNS(ns, 'rect');
  satz.setAttribute('x', x.toFixed(1)); satz.setAttribute('y', y.toFixed(1));
  satz.setAttribute('width', b.toFixed(1)); satz.setAttribute('height', h.toFixed(1));
  satz.setAttribute('fill', 'currentColor');
  satz.setAttribute('opacity', '.28');
  satz.setAttribute('stroke', 'none');
  sv.appendChild(satz);
  return sv;
}

function registerKlappe(knopf, punkte) {
  const warOffen = klappeOffen && klappeOffen.dataset.von === knopf.title;
  klappeSchliessen();
  if (warOffen) return;                    /* zweiter Klick schließt wieder */

  const klappe = document.createElement('div');
  klappe.className = 'register__klappe';
  klappe.dataset.von = knopf.title;

  /* Ein Punkt ist entweder schlicht — [Name, tun, haken] — oder
     ausfuehrlich: ein Kaestchen mit Bild, fettem Namen, einer Zeile mit
     den Massen und rechts der Tastenfolge. So steht es in WPS bei
     „Raender", „Groesse", „Ausrichtung", „Spalten" und „Umbrueche", und
     es ist dort kein Schmuck: „Normal" und „Moderat" unterscheiden sich
     nur in den Zahlen darunter. Ohne sie muesste man alle vier
     ausprobieren. */
  for (const punkt of punkte) {
    const reich = !Array.isArray(punkt);
    const name  = reich ? punkt.name : punkt[0];
    const tun   = reich ? punkt.tun  : punkt[1];
    const haken = reich ? punkt.haken : punkt[2];

    if (name === '-') {
      const strichEl = document.createElement('div');
      strichEl.className = 'menue__strich';
      klappe.appendChild(strichEl);
      continue;
    }
    const zeile = document.createElement('button');
    zeile.type = 'button';
    zeile.className = reich ? 'menue__punkt klappzeile' : 'menue__punkt';

    let gilt = false;
    try { gilt = typeof haken === 'function' && haken(); } catch (e) { gilt = false; }

    if (reich) {
      if (punkt.bild && SYMBOLE[punkt.bild]) {
        const b = symbol(punkt.bild);
        b.classList.add('klappzeile__bild');
        zeile.appendChild(b);
      } else if (punkt.blatt) {
        zeile.appendChild(randbild(punkt.blatt));
      } else {
        const leer = document.createElement('span');
        leer.className = 'klappzeile__bild';
        zeile.appendChild(leer);
      }

      const text = document.createElement('span');
      text.className = 'klappzeile__text';
      const oben = document.createElement('strong');
      oben.textContent = (gilt ? '✓ ' : '') + name;
      text.appendChild(oben);
      if (punkt.mass) {
        const unten = document.createElement('span');
        unten.className = 'klappzeile__mass';
        unten.textContent = punkt.mass;
        text.appendChild(unten);
      }
      zeile.appendChild(text);

      if (punkt.taste) {
        const t = document.createElement('span');
        t.className = 'klappzeile__taste';
        t.textContent = punkt.taste;
        zeile.appendChild(t);
      }
    } else {
      const marke = document.createElement('span');
      marke.className = 'haken';
      marke.textContent = gilt ? '✓' : '';
      zeile.appendChild(marke);

      const wort = document.createElement('span');
      wort.textContent = name;
      zeile.appendChild(wort);
    }

    zeile.addEventListener('mousedown', (e) => e.preventDefault());
    zeile.addEventListener('click', () => { klappeSchliessen(); tun(); });
    klappe.appendChild(zeile);
  }

  document.body.appendChild(klappe);
  const r = knopf.getBoundingClientRect();
  klappe.style.left = Math.min(r.left, window.innerWidth - klappe.offsetWidth - 8) + 'px';
  klappe.style.top = r.bottom + 2 + 'px';
  klappeOffen = klappe;
}

document.addEventListener('mousedown', (e) => {
  if (klappeOffen && !klappeOffen.contains(e.target) && !e.target.closest('.wz--klappe')) {
    klappeSchliessen();
  }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') klappeSchliessen(); });

/* ---- Der Weg zu dem, was nicht mehr hineinpasst ----
   Bei „Start" sind es sieben Gruppen; in ein schmales Fenster passen die
   nicht. Die Rollleiste ist ausgeblendet, weil sie unter einem Band
   hässlich aussieht — also zwei Pfeile, und die nur dann, wenn wirklich
   etwas übersteht. Ein Pfeil, der ins Leere zeigt, ist schlimmer als
   keiner. */
function registerPfeile() {
  const band = $('register-band');
  const links = $('register-links');
  const rechts = $('register-rechts');
  if (!band || !links || !rechts) return;
  const ueber = band.scrollWidth > band.clientWidth + 2;
  links.hidden = !ueber || band.scrollLeft < 4;
  rechts.hidden = !ueber || band.scrollLeft + band.clientWidth > band.scrollWidth - 4;
}

/* Der Kontextreiter muss kommen und gehen, während der Zeiger wandert. Neu
   gebaut wird aber nur, wenn sich wirklich etwas ändert — bei jedem
   Tastendruck das ganze Band neu zu zeichnen wäre beim Schreiben zu spüren. */
let zusammenhangStand = '';

/* Welche Knöpfe im Band einen Zustand haben — und wie er gerade steht.

   Der Kopf von register.js versprach das seit jeher („Ein vierter Eintrag
   als Funktion, die true oder false gibt, setzt einen Haken"), aber der
   Baukasten las ihn nie aus. Also zeigte kein Schalter im Band, ob er an
   ist: Wer versehentlich die Zeilennummern anschaltete, sah Zahlen neben
   jeder Zeile und fand den Knopf nicht wieder, der sie gebracht hatte.

   Die Liste wird bei jedem Neubau des Bandes neu gefüllt — die Knöpfe von
   vorhin gibt es dann nicht mehr. */
let registerSchalter = [];

function registerSchalterAuffrischen() {
  for (const { knopf, ist } of registerSchalter) {
    let an = false;
    try { an = !!ist(); } catch (e) { an = false; }
    knopf.classList.toggle('wz--an', an);
    knopf.setAttribute('aria-pressed', an ? 'true' : 'false');
  }
}

/* ------------------------------------------------------------
   DIE LEISTE ZUM GEWÄHLTEN (nur bei „Symbolleisten")

   REGISTER_IM_ZUSAMMENHANG kannte bisher nur eine Oberfläche: In
   Registern erschien „Tabellenwerkzeuge", sobald der Zeiger in einer
   Tabelle stand. Bei Symbolleisten erschien nichts — die Befehle waren
   gebaut und für diese Hälfte der Anwender unerreichbar. Kay hat es
   gemerkt und gefragt, warum er die Tabelle nicht einstellen kann.

   Dieselbe Liste, zweite Darstellung: eine dritte Leiste, die auftaucht,
   wenn es etwas zu sagen gibt, und sonst weg ist. Vorn steht, wozu sie
   gehört — „Tabellenwerkzeuge" —, denn eine Leiste, die kommt und geht,
   muss sagen, warum.
   ------------------------------------------------------------ */
function zusammenhangsleisteBauen() {
  const leiste = $('werkzeugleiste3');
  if (!leiste || !leiste.appendChild) return;

  /* Nur bei Symbolleisten: In Registern sagen die Reiter dasselbe, und
     zweimal dasselbe untereinander ist keine Hilfe, sondern Lärm. */
  const reiter = flaeche === 'register' ? [] : zusammenhangReiter();
  if (!reiter.length || !leistenAn) {
    leiste.hidden = true;
    leiste.innerHTML = '';
    return;
  }

  leisteBauen('werkzeugleiste3', ({ knopf, trenner, leiste: l }) => {
    let ersterReiter = true;
    for (const r of reiter) {
      if (!ersterReiter) trenner();
      ersterReiter = false;

      const marke = document.createElement('span');
      marke.className = 'wz__marke';
      marke.textContent = r.name;
      l.appendChild(marke);

      for (const [, befehle] of r.gruppen) {
        trenner();
        for (const [bild, name, tun] of befehle) knopf(bild, name, tun);
      }
    }
  });
  leiste.hidden = false;
  /* Die Leiste hat das Blatt verschoben — der Griff der Tabelle sitzt
     jetzt falsch und muss neu gemessen werden. */
  if (typeof griffAuffrischen === 'function') requestAnimationFrame(griffAuffrischen);
  if (typeof bildGriffeAuffrischen === 'function') requestAnimationFrame(bildGriffeAuffrischen);
}

let zusammenhangStandLeiste = '';

function zusammenhangPruefen() {
  const jetzt = zusammenhangReiter().map((r) => r.name).join(',');
  if (flaeche === 'register') {
    if (jetzt === zusammenhangStand) return;
    zusammenhangStand = jetzt;
    registerBauen();
    return;
  }
  /* Bei Symbolleisten: nur neu bauen, wenn sich wirklich etwas ändert.
     Ein „selectionchange" feuert bei jedem Tastendruck — die Leiste bei
     jedem Buchstaben neu zu zeichnen ließe sie flackern. */
  if (jetzt === zusammenhangStandLeiste) return;
  zusammenhangStandLeiste = jetzt;
  zusammenhangsleisteBauen();
}

document.addEventListener('selectionchange', zusammenhangPruefen);
/* Wandert der Zeiger über eine Trennlinie, gilt ein anderer Abschnitt —
   und der Bogen muss ihn zeigen. */
document.addEventListener('selectionchange', abschnittPruefen);

/* ------------------------------------------------------------
   Symbolleisten oder Register
   ------------------------------------------------------------ */
let flaeche = Speicher.lies('flaeche', 'leisten');

function flaecheAnwenden() {
  document.body.classList.toggle('flaeche--register', flaeche === 'register');
  menueleisteAnwenden();
  if (flaeche === 'register') {
    registerBauen();
  } else {
    /* Das Band leeren, BEVOR die Leisten neu gebaut werden. Sonst bleiben die
       alten Wähler im ausgeblendeten Register stehen, während daneben neue
       entstehen — dann gibt es zwei Schriftwähler mit zwei Ständen, und der
       im Blatt sichtbare ist nicht der, den man anklickt. */
    const band = $('register-band');
    const reiter = $('register-reiter');
    if (band) band.innerHTML = '';
    if (reiter) reiter.innerHTML = '';
    const menueStelle = $('register-menue');
    if (menueStelle) menueStelle.innerHTML = '';
    const schnell = $('register-schnell');
    if (schnell) schnell.innerHTML = '';
    werkzeugeBauen();
    werkzeugeAuffrischen();
  }
  /* Beim Wechsel zwischen den Oberflaechen: In Registern verschwindet die
     dritte Leiste, bei Symbolleisten kommt sie zurueck. */
  zusammenhangStandLeiste = '';
  zusammenhangsleisteBauen();
}

/* Ansicht ▸ Oberfläche ▸ Benutzeroberfläche.

   Hier stand ein eigenes Fenster: zwei Absätze Text und ein Klappfeld mit
   den Wörtern „Symbolleisten" und „In Registern". Dieselbe Einstellung
   steht seit dem Umbau in den Optionen — dort aber mit zwei gezeichneten
   Fassungen, die zeigen, was man bekommt.

   Zwei Türen zu einer Einstellung sind in Ordnung. Zwei Türen zu ZWEI
   verschieden guten Fassungen derselben Einstellung sind es nicht: Wer
   den Menüweg nimmt, bekäme die schlechtere und wüsste nie, dass es die
   bessere gibt. Also führt der Menüweg jetzt an dieselbe Stelle. */
B.benutzeroberflaeche = () => Einstellungen.flaecheAnspringen();

/* ------------------------------------------------------------
   Das Register anpassen

   Word nennt es „Menüband anpassen", der Writer „Symbolleisten anpassen".
   Beide können dasselbe: die Reihenfolge der Gruppen ändern und einzelne
   ausblenden. Wer die Ansicht zuerst nach der Oberfläche sortiert haben
   will und den Zoom zuletzt, soll das einstellen können — es ist seine
   Arbeit, nicht meine.

   Verschoben wird mit zwei Knöpfen, nicht mit der Maus. Ziehen und Ablegen
   sieht moderner aus, verlangt aber eine ruhige Hand und trifft schlecht;
   ein Pfeil nach oben trifft immer.
   ------------------------------------------------------------ */
let registerOrdnung = Speicher.lies('registerOrdnung', {});

/* Die Gruppen eines Reiters in der eingestellten Reihenfolge, ohne die
   ausgeblendeten. Was seit der letzten Einstellung dazugekommen ist,
   hängt sich hinten an: Ein neuer Befehl soll nicht unsichtbar bleiben,
   nur weil die Einstellung ihn noch nicht kennt. */
function registerGruppenFuer(name, gruppen) {
  const wunsch = registerOrdnung[name];
  if (!Array.isArray(wunsch) || !wunsch.length) return gruppen;
  const uebrig = new Map(gruppen.map((g) => [g[0], g]));
  const raus = [];
  for (const eintrag of wunsch) {
    const gruppe = uebrig.get(eintrag && eintrag.name);
    if (!gruppe) continue;
    uebrig.delete(eintrag.name);
    if (eintrag.an !== false) raus.push(gruppe);
  }
  for (const gruppe of uebrig.values()) raus.push(gruppe);
  return raus;
}

/* Dieselbe Liste, aber vollständig — auch die ausgeblendeten. Sie ist es,
   die im Anpassen-Fenster steht. */
/* Was jemand sich selbst angelegt hat: neue Registerkarten, neue Gruppen,
   umbenannte, und die Befehle, die er hineingelegt hat.

   REGISTER selbst steht in daten/register.js und ist beim Start immer
   gleich. Die Zusätze daneben zu speichern hat einen Grund: Wenn dort ein
   neuer Knopf dazukommt, bekommt ihn auch, wer schon angepasst hat — eine
   ganze Kopie im Speicher würde die Änderung verschlucken.

   Gespeichert wird nur, was sich benennen lässt: Name der Karte, Name der
   Gruppe, Namen der Befehle. Die Funktionen dahinter werden beim Laden aus
   dem Band geholt — Funktionen lassen sich nicht speichern. */
function eigeneRegisterSichern() {
  const eigene = [];
  for (const [reiterName, gruppen] of REGISTER) {
    for (const g of gruppen) {
      if (!Array.isArray(g[1])) continue;
      const befehle = g[1].filter((e) => Array.isArray(e) && typeof e[1] === 'string')
                          .map((e) => e[1]);
      eigene.push({ reiter: reiterName, gruppe: g[0], befehle });
    }
  }
  Speicher.schreib('registerEigene', eigene);
}

/* Beim Start: die eigenen Karten und Gruppen wieder anlegen.

   Nur, was es noch nicht gibt — alles Übrige steht schon in register.js
   und würde sonst doppelt erscheinen. */
function eigeneRegisterHolen() {
  const eigene = Speicher.lies('registerEigene', null);
  if (!Array.isArray(eigene)) return;

  /* Einen Befehl im ganzen Band suchen, um sein Symbol mitzunehmen. */
  const suchen = (name) => {
    for (const [, gruppen] of REGISTER) {
      for (const g of gruppen) {
        const liste = Array.isArray(g[1]) ? g[1] : [];
        const e = liste.find((x) => Array.isArray(x) && x[1] === name);
        if (e) return e;
      }
    }
    return null;
  };

  for (const eintrag of eigene) {
    if (!eintrag || !eintrag.reiter || !eintrag.gruppe) continue;
    let reiter = REGISTER.find(([n]) => n === eintrag.reiter);
    if (!reiter) { reiter = [eintrag.reiter, []]; REGISTER.push(reiter); }
    let gruppe = reiter[1].find((g) => g[0] === eintrag.gruppe);
    if (!gruppe) { gruppe = [eintrag.gruppe, []]; reiter[1].push(gruppe); }
    if (!Array.isArray(gruppe[1])) continue;
    for (const name of (eintrag.befehle || [])) {
      if (gruppe[1].some((e) => Array.isArray(e) && e[1] === name)) continue;
      const vorlage = suchen(name);
      if (vorlage) gruppe[1].push(vorlage.slice());
    }
  }
}
eigeneRegisterHolen();

/* Das Symbol zu einem Befehlsnamen, aus dem Band herausgesucht.

   Die Listen im Optionen-Fenster kennen oft nur den Namen — die Leiste
   für den Schnellzugriff speichert nur ihn, denn Funktionen lassen sich
   nicht speichern. Ohne Bild wäre ein Befehl in einer Liste von hundert
   kaum wiederzufinden: Das Auge sucht die Form, nicht das Wort. */
function symbolZuBefehl(name) {
  for (const [, gruppen] of REGISTER) {
    for (const g of gruppen) {
      const liste = Array.isArray(g[1]) ? g[1] : [];
      const e = liste.find((x) => Array.isArray(x) && x[1] === name);
      if (e) return e[0];
      /* Auch in den Untermenüs nachsehen — sie tragen das Symbol des
         Knopfes, unter dem sie hängen. */
      for (const x of liste) {
        if (Array.isArray(x) && Array.isArray(x[2])
            && x[2].some((u) => Array.isArray(u) && u[0] === name)) return x[0];
      }
    }
  }
  return '';
}

function registerListeFuer(name) {
  const gefunden = REGISTER.find(([n]) => n === name);
  const roh = gefunden ? gefunden[1] : [];
  const wunsch = Array.isArray(registerOrdnung[name]) ? registerOrdnung[name] : [];
  const uebrig = new Map(roh.map((g) => [g[0], g]));
  const liste = [];
  for (const eintrag of wunsch) {
    if (!eintrag || !uebrig.has(eintrag.name)) continue;
    uebrig.delete(eintrag.name);
    liste.push({ name: eintrag.name, an: eintrag.an !== false });
  }
  for (const gruppenName of uebrig.keys()) liste.push({ name: gruppenName, an: true });
  return liste;
}

B.registerAnpassen = () => {
  const knoten = document.createElement('div');
  knoten.className = 'anpassen';

  /* Welcher Reiter. Voreingestellt der, der gerade offen ist — meistens
     will man genau den ändern, den man vor sich hat. */
  const kopf = document.createElement('label');
  kopf.className = 'anpassen__kopf';
  const kopfWort = document.createElement('span');
  kopfWort.textContent = 'Reiter';
  const wahl = document.createElement('select');
  wahl.className = 'wz-wahl';
  for (const [name] of REGISTER) {
    const punkt = document.createElement('option');
    punkt.value = name;
    punkt.textContent = name;
    wahl.appendChild(punkt);
  }
  wahl.value = REGISTER.some(([n]) => n === registerOffen) ? registerOffen : 'Start';
  kopf.append(kopfWort, wahl);
  knoten.appendChild(kopf);

  /* Die Liste und die beiden Pfeile daneben.

     Sie standen einmal IN jeder Zeile, einer je Gruppe. Das ließ sich
     genau einen Schritt weit bedienen: Nach dem Klick wurde die Liste neu
     gezeichnet, die Zeile war weggewandert, und unter dem Zeiger stand
     jetzt die nachgerückte. Ein zweiter Klick schob sie wieder zurück.
     Gemeldet als „nur um eine Position, in beide Richtungen".

     Jetzt wird eine Zeile ausgewählt, und die Pfeile stehen fest daneben —
     so hält es auch WPS in „Menüband anpassen". Die Knöpfe bleiben unter
     dem Zeiger, während die Auswahl wandert; damit lässt sich eine Gruppe
     in einem Zug von unten nach oben schieben. */
  const mitte = document.createElement('div');
  mitte.className = 'anpassen__mitte';

  const kasten = document.createElement('div');
  kasten.className = 'anpassen__liste';
  kasten.setAttribute('role', 'listbox');
  kasten.setAttribute('aria-label', 'Gruppen dieses Reiters');

  const pfeile = document.createElement('div');
  pfeile.className = 'anpassen__pfeile';
  const hoch = document.createElement('button');
  hoch.type = 'button';
  hoch.className = 'wz';
  hoch.textContent = '▲';
  hoch.title = 'Die gewählte Gruppe nach oben';
  hoch.setAttribute('aria-label', 'Die gewählte Gruppe nach oben');
  const runter = document.createElement('button');
  runter.type = 'button';
  runter.className = 'wz';
  runter.textContent = '▼';
  runter.title = 'Die gewählte Gruppe nach unten';
  runter.setAttribute('aria-label', 'Die gewählte Gruppe nach unten');
  pfeile.append(hoch, runter);

  mitte.append(kasten, pfeile);
  knoten.appendChild(mitte);

  const fuss = document.createElement('div');
  fuss.className = 'anpassen__fuss';
  const zurueck = document.createElement('button');
  zurueck.type = 'button';
  zurueck.className = 'knopf knopf--klein';
  zurueck.textContent = 'Diesen Reiter zurücksetzen';
  const alleZurueck = document.createElement('button');
  alleZurueck.type = 'button';
  alleZurueck.className = 'knopf knopf--klein';
  alleZurueck.textContent = 'Alle zurücksetzen';
  fuss.append(zurueck, alleZurueck);
  knoten.appendChild(fuss);

  let liste = [];
  /* Welche Zeile gewählt ist — nicht als Nummer, sondern als Name: Die
     Nummer wandert beim Verschieben, der Name nicht. */
  let gewaehlt = null;

  const sichern = () => {
    registerOrdnung[wahl.value] = liste.map(({ name, an }) => ({ name, an }));
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
  };

  const pfeileStellen = () => {
    const i = liste.findIndex((e) => e.name === gewaehlt);
    hoch.disabled = i <= 0;
    runter.disabled = i < 0 || i === liste.length - 1;
  };

  /* Verschieben: um eine Stelle, und die Auswahl geht mit. Sie bleibt am
     Namen hängen, deshalb steht sie danach wieder auf derselben Gruppe —
     nur eine Zeile weiter oben. Der nächste Klick schiebt weiter. */
  const schieben = (wohin) => {
    const i = liste.findIndex((e) => e.name === gewaehlt);
    const ziel = i + wohin;
    if (i < 0 || ziel < 0 || ziel >= liste.length) return;
    [liste[ziel], liste[i]] = [liste[i], liste[ziel]];
    sichern();
    zeichnen();
  };
  hoch.addEventListener('click', () => schieben(-1));
  runter.addEventListener('click', () => schieben(1));

  const zeichnen = () => {
    kasten.textContent = '';
    /* Ohne Auswahl die erste: Sonst stünden beide Pfeile grau da und man
       müsste erst erraten, dass man etwas anklicken soll. */
    if (!liste.some((e) => e.name === gewaehlt)) gewaehlt = liste.length ? liste[0].name : null;

    liste.forEach((eintrag, i) => {
      const zeile = document.createElement('div');
      zeile.className = 'anpassen__zeile'
                      + (eintrag.an ? '' : ' anpassen__zeile--aus')
                      + (eintrag.name === gewaehlt ? ' anpassen__zeile--gewaehlt' : '');
      zeile.setAttribute('role', 'option');
      zeile.setAttribute('aria-selected', eintrag.name === gewaehlt ? 'true' : 'false');

      const schalter = document.createElement('input');
      schalter.type = 'checkbox';
      schalter.checked = eintrag.an;
      schalter.id = 'anpassen-' + i;
      schalter.addEventListener('change', () => {
        eintrag.an = schalter.checked;
        gewaehlt = eintrag.name;
        sichern();
        zeichnen();
      });

      const name = document.createElement('label');
      name.className = 'anpassen__name';
      name.htmlFor = schalter.id;
      name.textContent = eintrag.name;

      /* Der Klick auf die Zeile wählt sie — nicht auf das Kästchen, das
         hat seine eigene Aufgabe, und nicht auf die Beschriftung, die
         gehört zum Kästchen. */
      zeile.addEventListener('mousedown', (e) => {
        if (e.target === schalter || e.target === name) return;
        gewaehlt = eintrag.name;
        zeichnen();
      });

      zeile.append(schalter, name);
      kasten.appendChild(zeile);
    });
    pfeileStellen();
  };

  const laden = () => { liste = registerListeFuer(wahl.value); zeichnen(); };

  wahl.addEventListener('change', () => {
    /* Beim Wechsel gleich mitgehen: Wer den Reiter im Fenster wählt, will
       ihn auch dahinter sehen. */
    registerOffen = wahl.value;
    Speicher.schreib('register', registerOffen);
    registerBauen();
    laden();
  });
  zurueck.addEventListener('click', () => {
    delete registerOrdnung[wahl.value];
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
    laden();
  });
  alleZurueck.addEventListener('click', () => {
    registerOrdnung = {};
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
    laden();
  });

  laden();

  /* Der Stand beim Öffnen, für den Fall, dass jemand doch nur schauen
     wollte. Eine flache Kopie reichte nicht: Die Listen darin werden
     ersetzt, nicht verändert — aber sicher ist sicher. */
  const vorher = JSON.parse(JSON.stringify(registerOrdnung));

  fenster('Register anpassen', [
    { art: 'satz', text: 'Die Reihenfolge der Gruppen und was davon zu sehen ist.\n'
                       + '„Fertig" behält die Änderungen, „Abbrechen" nimmt sie zurück.' },
    { art: 'knoten', knoten },
  ], null, 'Fertig', false, () => {
    registerOrdnung = vorher;
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
  });
};

/* Ein blauer Lesehilfe-Knopf stand hier einmal neben den Reitern, damit
   sie von überall erreichbar ist. Er war gut gemeint und doppelt: Direkt
   darunter steht im Reiter „Schreibhilfe" die Gruppe „Lesen" mit
   demselben Knopf — und Platz nahm er auch noch. F6 tut dasselbe, ohne im
   Weg zu stehen. */

/* Die Pfeile werden einmal angeschlossen — registerBauen() leert nur das
   Band, nicht den Streifen darum. */
(() => {
  const band = $('register-band');
  const rollen = (weite) => { band.scrollLeft += weite; setTimeout(registerPfeile, 350); };
  $('register-links').addEventListener('click', () => rollen(-Math.round(band.clientWidth * 0.7)));
  $('register-rechts').addEventListener('click', () => rollen(Math.round(band.clientWidth * 0.7)));
  band.addEventListener('scroll', registerPfeile);
  window.addEventListener('resize', registerPfeile);
  /* Rechtsklick auf das Band führt zum Anpassen — so kennt man es aus
     Word, und man sucht es genau dort. */
  band.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    /* Auf einem Knopf ist das Symbol gemeint, daneben die Anordnung — so
       hält es der Writer auch, nur dass er es beim Symbolband gar nicht
       anbietet. */
    const name = symbolUnter(e.target);
    if (name) { B.symbolTauschen(name); return; }
    B.registerAnpassen();
  });
})();

/* ------------------------------------------------------------
   Wie groß die Symbole und die Schrift der Leisten sind

   Steht im Writer unter Optionen ▸ Ansicht, und es ist keine Spielerei:
   Wer die Leisten nicht lesen kann, benutzt sie nicht.
   ------------------------------------------------------------ */
const SYMBOLGROESSEN = [['klein', 16], ['mittel', 20], ['gross', 24], ['riesig', 30]];

function bedienungAnwenden() {
  const marke = Speicher.lies('symbolgroesse', 'mittel');
  const paar = SYMBOLGROESSEN.find(([m]) => m === marke) || SYMBOLGROESSEN[1];
  const skala = Math.max(80, Math.min(180, Number(Speicher.lies('skalierung', 100)) || 100));
  const wurzel = document.documentElement;
  wurzel.style.setProperty('--symbolgroesse', paar[1] + 'px');
  wurzel.style.setProperty('--bedienschrift', (13 * skala / 100).toFixed(1) + 'px');
  wurzel.style.setProperty('--bedienskala', String(skala / 100));
}

/* ============================================================
   Drucken: die Vorschau und das Druckfenster

   Steht in js/drucken.js — 1.136 Zeilen, die zusammengehoeren und sonst zu
   nichts. Was sie von hier braucht, steht in dieser Aufstellung und nur
   hier. Jeder Eintrag ist eine Funktion oder ein Objekt, das es schon gibt:
   Manches, was das Drucken liest, wird weiter unten erst gesetzt, und was
   es liest, muss der Stand von jetzt sein und nicht der vom Bauen.
   ============================================================ */
const Druck = DRUCKEN_BAUEN(B, {
  Speicher, feld, CM,
  fenster:        (...a) => fenster(...a),
  melde:          (...a) => melde(...a),
  ohneMarken:     (...a) => ohneMarken(...a),
  papierAnwenden: ()     => papierAnwenden(),
  papiere:        ()     => PAPIERE,

  /* Wie die Seite eingerichtet ist. Ein Griff statt acht: Das Drucken
     braucht sie immer zusammen, und so bleibt die Verbindung schmal. */
  seite: () => ({ papier, quer, seitenrand, seitenfarbe, wasserzeichen,
                  zeilennummern, spalten, trennung }),

  /* Der einzige Weg zurueck. Das Druckfenster darf Papier und Ausrichtung
     aendern — sonst nichts. */
  seiteSetzen: (neu) => {
    if (neu.papier !== undefined) papier = neu.papier;
    if (neu.quer !== undefined) quer = neu.quer;
  },
});

/* ---- Tabelle ---- */
function zelleJetzt() {
  let k = window.getSelection().anchorNode;
  while (k && k !== feld) {
    if (k.nodeType === Node.ELEMENT_NODE && (k.tagName === 'TD' || k.tagName === 'TH')) return k;
    k = k.parentNode;
  }
  return null;
}

/* Die zuletzt besuchte Zelle.

   Jeder Tabellenbefehl fragt „steht der Zeiger in einer Tabelle?" — und
   bekam beim Weg über die Menüleiste „nein". Der Grund: Ein Klick auf
   „Einfügen" nimmt dem Blatt die Auswahl, und bis der Befehl feuert, weiß
   niemand mehr, wo man war. Wer also über das Menü ging statt über den
   Rechtsklick, bekam bei JEDEM Tabellenbefehl dieselbe Absage — Rahmen,
   Kopfzeile, Zeile einfügen, alles.

   Deshalb wird die Zelle gemerkt, solange der Zeiger darin steht. Sie
   gilt nur, wenn sie noch im Blatt hängt: Eine gelöschte Tabelle darf
   nicht als „die aktuelle" weiterleben. */
let letzteZelle = null;

document.addEventListener('selectionchange', () => {
  const z = zelleJetzt();
  if (z) letzteZelle = z;
});

function zelleOderZuletzt() {
  const jetzt = zelleJetzt();
  if (jetzt) return jetzt;
  if (letzteZelle && letzteZelle.isConnected && feld.contains(letzteZelle)) {
    return letzteZelle;
  }
  letzteZelle = null;
  return null;
}

function mitTabelle(tun) {
  const zelle = zelleOderZuletzt();
  if (!zelle) { melde('Dafür muss der Zeiger in einer Tabelle stehen.'); return; }
  tun(zelle, zelle.parentElement, zelle.closest('table'));
  geaendertMelden();
}

const neueZelle = () => { const z = document.createElement('td'); z.innerHTML = '<br>'; return z; };

B.zeileOben = () => mitTabelle((zelle, zeile) => {
  const neu = zeile.cloneNode(false);
  for (let i = 0; i < zeile.children.length; i++) neu.appendChild(neueZelle());
  zeile.parentElement.insertBefore(neu, zeile);
});
B.zeileUnten = () => mitTabelle((zelle, zeile) => {
  const neu = zeile.cloneNode(false);
  for (let i = 0; i < zeile.children.length; i++) neu.appendChild(neueZelle());
  zeile.parentElement.insertBefore(neu, zeile.nextSibling);
});
B.spalteLinks = () => mitTabelle((zelle, zeile, tabelle) => {
  const stelle = [...zeile.children].indexOf(zelle);
  for (const z of tabelle.rows) z.insertBefore(neueZelle(), z.children[stelle] || null);
});
B.spalteRechts = () => mitTabelle((zelle, zeile, tabelle) => {
  const stelle = [...zeile.children].indexOf(zelle);
  for (const z of tabelle.rows) z.insertBefore(neueZelle(), z.children[stelle + 1] || null);
});
B.zeileWeg = () => mitTabelle((zelle, zeile, tabelle) => {
  if (tabelle.rows.length <= 1) { tabelle.remove(); melde('Die letzte Zeile war es — die Tabelle ist weg.'); return; }
  zeile.remove();
});
B.spalteWeg = () => mitTabelle((zelle, zeile, tabelle) => {
  const stelle = [...zeile.children].indexOf(zelle);
  if (zeile.children.length <= 1) { tabelle.remove(); melde('Die letzte Spalte war es — die Tabelle ist weg.'); return; }
  for (const z of tabelle.rows) if (z.children[stelle]) z.children[stelle].remove();
});
B.tabelleWeg = () => mitTabelle((zelle, zeile, tabelle) => tabelle.remove());
B.tabelleRahmen = () => mitTabelle((zelle, zeile, tabelle) => {
  tabelle.classList.toggle('tabelle--ohne-rahmen');
});
B.kopfzeileTabelle = () => mitTabelle((zelle, zeile, tabelle) => {
  const erste = tabelle.rows[0];
  const schonKopf = erste.children[0] && erste.children[0].tagName === 'TH';
  for (const z of [...erste.children]) {
    const neu = document.createElement(schonKopf ? 'td' : 'th');
    neu.innerHTML = z.innerHTML;
    z.replaceWith(neu);
  }
});

/* ---- Formular ---- */
B.formTextfeld = () => {
  Dokument.einfuegen('<input class="formfeld" type="text" placeholder="Text eingeben">');
  melde('Textfeld eingefügt.');
};
B.formKasten = () => {
  Dokument.einfuegen('<label class="formkasten"><input type="checkbox"> Auswahl</label>');
  melde('Kontrollkästchen eingefügt.');
};
/* „Schaltflaeche ohne ersichtliche Funktion. Die Schaltflaeche laesst
   sich nicht loeschen."

   Beides stimmte. Ein <button> im Text nimmt den Klick selbst an — der
   Zeiger kommt nicht daneben, und ohne Zeiger daneben gibt es nichts zu
   loeschen. Und ein Formularknopf, den man nicht beschriften kann, ist
   ein Platzhalter.

   Jetzt: nicht anklickbar im Schreiben (er gehoert ins Formular, nicht
   in die Bedienung), aber markierbar wie jedes andere Zeichen. Ein
   Doppelklick fragt nach der Aufschrift. Entf loescht ihn, weil der
   Zeiger wieder danebenkommt. */
B.formKnopf = () => {
  fenster('Schaltfläche', [
    { art: 'satz', text: 'Eine Schaltfläche für ein Formular. Zum Ändern '
                       + 'später doppelt darauf klicken; mit Entf ist sie weg.' },
    { schluessel: 'wort', name: 'Aufschrift', wert: 'Absenden' },
  ], (werte) => {
    const wort = (werte.wort || 'Schaltfläche').trim() || 'Schaltfläche';
    Dokument.einfuegen('<span class="formknopf" contenteditable="false" '
      + 'data-formknopf="1">' + alsSicher(wort) + '</span>&#8203;');
    geaendertMelden();
    melde('Schaltfläche „' + wort + '" eingefügt. Entf löscht sie.');
  }, 'Einfügen');
};

/* Doppelklick auf eine Schaltflaeche: Aufschrift aendern. */
feld.addEventListener('dblclick', (e) => {
  const knopf = e.target.closest && e.target.closest('[data-formknopf]');
  if (!knopf) return;
  e.preventDefault();
  fenster('Schaltfläche', [
    { schluessel: 'wort', name: 'Aufschrift', wert: knopf.textContent },
  ], (werte) => {
    knopf.textContent = (werte.wort || '').trim() || 'Schaltfläche';
    geaendertMelden();
    melde('Aufschrift geändert.');
  }, 'Übernehmen');
});

/* ---- Extras ---- */
/* „Rechtschreibung & Grammatik" wie in der Leiste des Writers: Beides auf
   einmal. Die Wellenlinien des Systems finden falsch geschriebene Wörter,
   die Schreibhilfe findet, was danach noch schiefsteht. */
/* „Prüfen" — der Lauf, nicht der Schalter. Die beiden Namen liegen
   dicht beieinander: „rechtschreibpruefung" prüft JETZT,
   „rechtschreibung" schaltet die Wellenlinien an und aus.

   Hier standen einmal zwei Zeilen, die beide aus einer Zeit stammen, als
   der Schalter die Prüfung des SYSTEMS steuerte: Er wurde eingeschaltet,
   und das Feld verlor und bekam den Fokus, damit WebKit neu anstrich.
   Seit §8 streicht Lunivo selbst an — und die zwei Zeilen richteten
   Schaden an: Wer die Wellenlinien ausgeschaltet hatte und auf „Prüfen"
   drückte, hatte sie wieder. Am Ende ließ sich der Schalter überhaupt
   nicht mehr ausschalten, weil der Knopf im Band, der wie der Schalter
   aussah, in Wahrheit hierher zeigte. Gemeldet am 09.09.2026. */
B.rechtschreibpruefung = () => pruefen();

B.rechtschreibung = () => {
  /* Der Schalter steuert seit dem Umbau die EIGENEN Wellenlinien, nicht
     die des Systems. Der Entwurf verlangt genau das (§8): Was
     angestrichen wird, entscheidet Lunivo — mit seinen 355.322 Wörtern
     und seinen Regeln —, nicht zwei Prüfer nebeneinander.

     Ausgeschaltet werden nur die Striche. Die Funde bleiben in der
     Seitenleiste stehen, und beim Wiedereinschalten muss nichts neu
     geprüft werden. */
  lebendAn = !lebendAn;
  Speicher.schreib('lebend', lebendAn);
  if (lebendAn) {
    lebendPruefen();
    melde('Rote Wellenlinien an — von Lunivo, beim Schreiben.');
  } else {
    markenEntfernen();
    melde('Rote Wellenlinien aus. Die Funde bleiben in der Seitenleiste.');
  }
  menueBauen();
};

B.woerterZaehlen = () => {
  const text = Dokument.lies().text;
  const woerter = text.trim() ? text.trim().split(/\s+/).length : 0;
  const saetze = (text.match(/[.!?]+(\s|$)/g) || []).length;
  const absaetze = feld.children.length;
  const ohneLeer = text.replace(/\s/g, '').length;
  fenster('Wörter zählen', [
    { art: 'satz', text:
        woerter + (woerter === 1 ? ' Wort' : ' Wörter') + '\n'
      + text.length + ' Zeichen mit Leerzeichen\n'
      + ohneLeer + ' Zeichen ohne Leerzeichen\n'
      + saetze + (saetze === 1 ? ' Satz' : ' Sätze') + '\n'
      + absaetze + (absaetze === 1 ? ' Absatz' : ' Absätze') },
  ], () => {}, 'Schließen');
};

B.eigenschaften = () => {
  const jetzt = Speicher.lies('eigenschaften', { titel: '', verfasser: '', stichworte: '' });
  fenster('Dokumenteigenschaften', [
    { art: 'satz', text: 'Sie gehen mit in die gespeicherte Datei.' },
    { schluessel: 'titel', name: 'Titel', wert: jetzt.titel },
    { schluessel: 'verfasser', name: 'Verfasser', wert: jetzt.verfasser },
    { schluessel: 'stichworte', name: 'Stichwörter', wert: jetzt.stichworte },
  ], (werte) => {
    Speicher.schreib('eigenschaften', werte);
    melde('Eigenschaften gespeichert.');
  });
};

/* ============================================================
   Diagramme

   Ein Diagramm ist hier kein fremdes Bauteil, sondern eine Zeichnung, die
   das Programm selbst aus den Zahlen macht: SVG. Das hat drei Vorteile — es
   bleibt beim Vergrößern scharf, es steht als Text im Dokument und geht
   damit in jede gespeicherte Datei mit.
   ============================================================ */
function zahlenLesen(roh) {
  const punkte = [];
  for (const zeile of String(roh).split(/\r?\n/)) {
    if (!zeile.trim()) continue;
    /* „Miete: 480" oder „Miete 480" oder „Miete;480" — wer Zahlen eintippt,
       soll nicht erst eine Schreibweise lernen müssen. */
    /* MEHRERE ZAHLEN JE ZEILE sind mehrere Datenreihen:
         Rubrik 1: 4; 2; 3
       Eine Zahl bleibt eine Zahl — wer nur eine schreibt, merkt von den
       Reihen nichts. Gebraucht werden sie fuer Kurs (hoch, tief,
       schluss) und fuer Kombination (Saeulen und Linie zusammen). */
    const treffer = /^(.*?)[\s:;\t]+(-?[\d.,;\s]+)$/.exec(zeile.trim());
    if (!treffer) continue;
    const roheWerte = treffer[2].split(/[;]|,(?=\s)|\s+/)
      .map((t) => t.trim()).filter(Boolean)
      .map((t) => parseFloat(t.replace(/\.(?=\d{3}\b)/g, '').replace(',', '.')))
      .filter((z) => !Number.isNaN(z));
    if (!roheWerte.length) continue;
    punkte.push({ name: treffer[1].trim(), wert: roheWerte[0], werte: roheWerte });
  }
  return punkte;
}

const DIAGRAMMFARBEN = ['#2F6FB5', '#3E9C7A', '#C08A2E', '#B5563F', '#7A5EA8',
                        '#4A8FD8', '#5FB79A', '#D8A94E'];

/* ============================================================
   DIE ARTEN AUS DER AUSWAHL

   Neun Formen stehen im Fenster zur Wahl, also muessen neun gezeichnet
   werden. Eine Auswahl, in der die Haelfte dasselbe malt, ist eine
   Auswahl, die luegt.

   „Gestapelt" mit einer einzigen Reihe ist ein Sonderfall: In WPS wird
   daraus eine Saeule, in der die Werte uebereinanderliegen. Genau so
   steht es hier.
   ============================================================ */
function diagrammZeichnen(art, punkte, titel, wie) {
  const bauer = {
    saeule:     saeulenSvg,
    saeulegest: (p, t, w) => gestapeltSvg(p, t, w, false),
    balken:     (p, t, w) => balkenQuerSvg(p, t, w),
    balkengest: (p, t, w) => gestapeltSvg(p, t, w, true),
    linie:      linienSvg,
    liniepunkt: (p, t, w) => linienSvg(p, t, Object.assign({}, w, { punkte: true })),
    kuchen:     kuchenSvg,
    ring:       (p, t, w) => kuchenSvg(p, t, Object.assign({}, w, { loch: true })),
    flaeche:    (p, t, w) => linienSvg(p, t, Object.assign({}, w, { fuellen: true })),
    saeuleproz: (p, t, w) => gestapeltSvg(p, t, Object.assign({}, w, { prozent: true }), false),
    punkte:     punktwolkeSvg,
    netz:       netzSvg,
    kurs:       kursSvg,
    kombi:      kombiSvg,
  }[art];
  return (bauer || saeulenSvg)(punkte, titel, wie);
}

/* ============================================================
   NETZ, KURS UND KOMBINATION

   Vier Gruppen seiner Vorlage fehlten: Kurs, Netz, Kombination und
   Vorlagen. Drei davon brauchen MEHRERE ZAHLEN je Zeile, und genau die
   nimmt zahlenLesen() jetzt entgegen:

       Montag: 12; 8; 10        hoch, tief, schluss

   Eine Zahl bleibt eine Zahl — wer nur eine schreibt, merkt von den
   Reihen nichts.
   ============================================================ */

/* NETZ (Radar): ein Vieleck ueber so vielen Achsen, wie es Werte gibt.
   Gut, wenn man Eigenschaften vergleicht, die keine Reihenfolge haben —
   fuenf Faecher, fuenf Noten. */
function netzSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const breite = 480, hoehe = 300;
  const mitteX = breite / 2, mitteY = (titel ? 36 : 14) + 120;
  const r = 110;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + mitteX + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';

  const ecke = (i, anteil) => {
    const w = (i / punkte.length) * Math.PI * 2 - Math.PI / 2;
    return [mitteX + Math.cos(w) * r * anteil, mitteY + Math.sin(w) * r * anteil];
  };

  /* Das Netz dahinter — vier Ringe, damit man ablesen kann. */
  for (const ring of [0.25, 0.5, 0.75, 1]) {
    const punkteRing = punkte.map((p, i) => ecke(i, ring).map((z) => z.toFixed(1)).join(','));
    aus += '<polygon points="' + punkteRing.join(' ') + '" fill="none" stroke="#D5D9DD"/>';
  }
  punkte.forEach((p, i) => {
    const [x, y] = ecke(i, 1);
    aus += '<line x1="' + mitteX + '" y1="' + mitteY + '" x2="' + x.toFixed(1)
         + '" y2="' + y.toFixed(1) + '" stroke="#D5D9DD"/>';
    const [tx, ty] = ecke(i, 1.16);
    aus += '<text x="' + tx.toFixed(1) + '" y="' + ty.toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
  });

  const netz = punkte.map((p, i) =>
    ecke(i, Math.abs(p.wert) / groesste).map((z) => z.toFixed(1)).join(','));
  aus += '<polygon data-teil="linie" points="' + netz.join(' ') + '" fill="'
       + farben[0] + '" fill-opacity=".3" stroke="' + farben[0] + '" stroke-width="2"/>';
  punkte.forEach((p, i) => {
    const [x, y] = ecke(i, Math.abs(p.wert) / groesste);
    aus += '<circle data-teil="wert-' + i + '" cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1)
         + '" r="4" fill="' + farben[0] + '"/>';
  });
  return svgHuelle(breite, hoehe, aus);
}

/* KURS: je Zeile hoch, tief und Schluss. Ein Strich von tief nach hoch,
   ein Querbalken am Schluss — so steht es in WPS unter „Hoch, Niedrig,
   Schliessen". Wer nur zwei Zahlen schreibt, bekommt hoch und tief. */
function kursSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const breite = 480, hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const alle = punkte.flatMap((p) => p.werte || [p.wert]);
  const groesste = Math.max(...alle.map(Math.abs), 1);
  const luecke = flaeche / punkte.length;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  const y = (w) => rand.oben + hoch - Math.abs(w) / groesste * hoch;
  punkte.forEach((p, i) => {
    const w = p.werte && p.werte.length ? p.werte : [p.wert];
    const hochW = Math.max(...w), tiefW = Math.min(...w);
    const schluss = w.length > 2 ? w[2] : null;
    const x = rand.links + i * luecke + luecke / 2;
    const farbe = farben[i % farben.length];
    aus += '<line data-teil="wert-' + i + '" x1="' + x.toFixed(1) + '" y1="' + y(hochW).toFixed(1)
         + '" x2="' + x.toFixed(1) + '" y2="' + y(tiefW).toFixed(1)
         + '" stroke="' + farbe + '" stroke-width="2"/>';
    if (schluss !== null) {
      aus += '<line x1="' + (x - 7).toFixed(1) + '" y1="' + y(schluss).toFixed(1)
           + '" x2="' + (x + 7).toFixed(1) + '" y2="' + y(schluss).toFixed(1)
           + '" stroke="' + farbe + '" stroke-width="2"/>';
    }
    aus += '<text x="' + x.toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
  });
  aus += '<text x="10" y="' + (hoehe - 10) + '" font-size="10" fill="#4C555E">'
       + 'Je Zeile: hoch; tief; Schluss</text>';
  return svgHuelle(breite, hoehe, aus);
}

/* KOMBINATION: die erste Reihe als Saeulen, die zweite als Linie
   darueber. Umsatz und Anteil im selben Bild — dafuer gibt es sie. */
function kombiSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const breite = 480, hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const ersten = punkte.map((p) => Math.abs(p.wert));
  const zweiten = punkte.map((p) => Math.abs((p.werte || [])[1] || 0));
  const g1 = Math.max(...ersten, 1);
  const g2 = Math.max(...zweiten, 1);
  const luecke = flaeche / punkte.length;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  punkte.forEach((p, i) => {
    const h = ersten[i] / g1 * hoch;
    const x = rand.links + i * luecke + luecke * 0.2;
    const b = luecke * 0.6;
    aus += '<rect data-teil="wert-' + i + '" x="' + x.toFixed(1) + '" y="'
         + (rand.oben + hoch - h).toFixed(1) + '" width="' + b.toFixed(1)
         + '" height="' + h.toFixed(1) + '" fill="' + farben[i % farben.length] + '"/>';
    aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
  });

  if (zweiten.some((z) => z > 0)) {
    const stellen = punkte.map((p, i) => [
      rand.links + i * luecke + luecke / 2,
      rand.oben + hoch - zweiten[i] / g2 * hoch,
    ]);
    aus += '<polyline data-teil="linie" fill="none" stroke="#111417" stroke-width="2" points="'
         + stellen.map(([x, y]) => x.toFixed(1) + ',' + y.toFixed(1)).join(' ') + '"/>';
    for (const [x, y] of stellen) {
      aus += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="3.5" fill="#111417"/>';
    }
  } else {
    aus += '<text x="10" y="' + (hoehe - 10) + '" font-size="10" fill="#4C555E">'
         + 'Zweite Zahl je Zeile ergibt die Linie — „Rubrik 1: 4; 2"</text>';
  }
  return svgHuelle(breite, hoehe, aus);
}

/* X Y (Punkt): nur die Marker, keine Linie dazwischen. Man sieht, wo
   die Werte liegen, ohne dass eine Linie eine Ordnung behauptet, die es
   nicht gibt. */
function punktwolkeSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const breite = 480, hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);
  const schritt = punkte.length > 1 ? flaeche / (punkte.length - 1) : 0;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';
  aus += '<line x1="' + rand.links + '" y1="' + rand.oben + '" x2="' + rand.links
       + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  punkte.forEach((p, i) => {
    const x = rand.links + i * schritt;
    const y = rand.oben + hoch - Math.abs(p.wert) / groesste * hoch;
    aus += '<circle data-teil="wert-' + i + '" cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1)
         + '" r="5" fill="' + farben[i % farben.length] + '"/>';
    aus += '<text x="' + x.toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
  });
  if (wie.legende === true) aus += legendeSvg(punkte, farben, breite, hoehe);
  return svgHuelle(breite, hoehe + (wie.legende === true ? 22 : 0), aus);
}

/* Balken, die liegen — das ist in WPS „Balken", die stehenden heissen
   „Saeule". Die Namen sind nicht austauschbar, und als Bild sieht man
   den Unterschied sofort. */
function balkenQuerSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const werteAn = wie.werte !== false;
  const breite = 480, hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 16, links: 96, rechts: 40 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);
  const luecke = hoch / punkte.length;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';
  aus += '<line x1="' + rand.links + '" y1="' + rand.oben + '" x2="' + rand.links
       + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  punkte.forEach((p, i) => {
    const b = Math.abs(p.wert) / groesste * flaeche;
    const y = rand.oben + i * luecke + luecke * 0.18;
    const h = luecke * 0.64;
    aus += '<rect data-teil="wert-' + i + '" x="' + rand.links + '" y="' + y.toFixed(1)
         + '" width="' + b.toFixed(1)
         + '" height="' + h.toFixed(1) + '" fill="' + farben[i % farben.length] + '"/>';
    aus += '<text x="' + (rand.links - 6) + '" y="' + (y + h / 2 + 3.5).toFixed(1)
         + '" text-anchor="end" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
    if (werteAn) {
      aus += '<text x="' + (rand.links + b + 5).toFixed(1) + '" y="' + (y + h / 2 + 3.5).toFixed(1)
           + '" font-size="10" fill="#111417">' + alsText(String(p.wert)) + '</text>';
    }
  });
  if (wie.legende === true) aus += legendeSvg(punkte, farben, breite, hoehe);
  return svgHuelle(breite, hoehe + (wie.legende === true ? 22 : 0), aus);
}

/* Gestapelt: alle Werte in einem Stueck uebereinander, waagerecht oder
   senkrecht. Man sieht das Ganze und die Anteile daran. */
function gestapeltSvg(punkte, titel, wie, quer) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const werteAn = wie.werte !== false;
  const breite = 480, hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 30, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const summe = punkte.reduce((a, p) => a + Math.abs(p.wert), 0) || 1;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';

  let gelaufen = 0;
  punkte.forEach((p, i) => {
    const teil = Math.abs(p.wert) / summe;
    if (quer) {
      const x = rand.links + gelaufen * flaeche;
      const b = teil * flaeche;
      aus += '<rect x="' + x.toFixed(1) + '" y="' + (rand.oben + hoch * 0.3).toFixed(1)
           + '" width="' + b.toFixed(1) + '" height="' + (hoch * 0.4).toFixed(1)
           + '" fill="' + farben[i % farben.length] + '"/>';
      if (werteAn && teil > 0.08) {
        aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (rand.oben + hoch * 0.53).toFixed(1)
             + '" text-anchor="middle" font-size="10" fill="#fff">'
             + (wie.prozent ? Math.round(teil * 100) + ' %' : alsText(String(p.wert))) + '</text>';
      }
    } else {
      const h = teil * hoch;
      const y = rand.oben + hoch - (gelaufen + teil) * hoch;
      const x = rand.links + flaeche * 0.3;
      const b = flaeche * 0.4;
      aus += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + b.toFixed(1)
           + '" height="' + h.toFixed(1) + '" fill="' + farben[i % farben.length] + '"/>';
      if (werteAn && teil > 0.08) {
        aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (y + h / 2 + 3.5).toFixed(1)
             + '" text-anchor="middle" font-size="10" fill="#fff">'
             + (wie.prozent ? Math.round(teil * 100) + ' %' : alsText(String(p.wert))) + '</text>';
      }
    }
    gelaufen += teil;
  });
  aus += legendeSvg(punkte, farben, breite, hoehe - 14);
  return svgHuelle(breite, hoehe + 8, aus);
}

/* Die drei Bauer nehmen jetzt entgegen, was die Diagrammtools setzen:
   welche Farben, ob Werte an den Balken stehen, ob eine Legende kommt.
   Ohne das waeren die neuen Knoepfe Knoepfe, die nichts tun. */
function saeulenSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const werteAn = wie.werte !== false;
  const legendeAn = wie.legende === true;
  const breite = 480;
  const hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);
  const luecke = flaeche / punkte.length;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';

  // Die Grundlinie: ohne sie schweben die Balken im Nichts.
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  punkte.forEach((p, i) => {
    const h = Math.abs(p.wert) / groesste * hoch;
    const x = rand.links + i * luecke + luecke * 0.15;
    const b = luecke * 0.7;
    const y = rand.oben + hoch - h;
    aus += '<rect data-teil="wert-' + i + '" x="' + x.toFixed(1) + '" y="' + y.toFixed(1)
         + '" width="' + b.toFixed(1)
         + '" height="' + h.toFixed(1) + '" fill="' + farben[i % farben.length] + '"/>';
    if (werteAn) {
      aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (y - 5).toFixed(1)
           + '" text-anchor="middle" font-size="10" fill="#111417">' + alsText(String(p.wert)) + '</text>';
    }
    aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
  });
  if (legendeAn) aus += legendeSvg(punkte, farben, breite, hoehe);
  return svgHuelle(breite, hoehe + (legendeAn ? 22 : 0), aus);
}

/* Eine Legende unter dem Bild: Farbfleck und Name, nebeneinander. */
function legendeSvg(punkte, farben, breite, hoehe) {
  const proStueck = Math.min(110, breite / Math.max(1, punkte.length));
  let aus = '';
  punkte.forEach((p, i) => {
    const x = 10 + i * proStueck;
    const y = hoehe + 12;
    aus += '<rect x="' + x + '" y="' + (y - 8) + '" width="9" height="9" fill="'
         + farben[i % farben.length] + '"/>';
    aus += '<text x="' + (x + 13) + '" y="' + y + '" font-size="10" fill="#4C555E">'
         + alsText(p.name) + '</text>';
  });
  return aus;
}

function linienSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const mitPunkten = wie.punkte === true;
  const gefuellt = wie.fuellen === true;
  const breite = 480;
  const hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);
  const schritt = punkte.length > 1 ? flaeche / (punkte.length - 1) : 0;

  let aus = '';
  if (titel) aus += '<text data-teil="titel" x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  const stellen = punkte.map((p, i) => [rand.links + i * schritt,
                                        rand.oben + hoch - Math.abs(p.wert) / groesste * hoch]);
  const linienfarbe = farben[0];
  /* „Flaeche" ist dieselbe Linie mit dem, was darunter liegt. */
  if (gefuellt) {
    aus += '<polygon fill="' + linienfarbe + '" fill-opacity=".28" points="'
         + (rand.links + ',' + (rand.oben + hoch)) + ' '
         + stellen.map(([x, y]) => x.toFixed(1) + ',' + y.toFixed(1)).join(' ') + ' '
         + (stellen[stellen.length - 1][0].toFixed(1) + ',' + (rand.oben + hoch)) + '"/>';
  }
  aus += '<polyline data-teil="linie" fill="none" stroke="' + linienfarbe + '" stroke-width="2" points="'
       + stellen.map(([x, y]) => x.toFixed(1) + ',' + y.toFixed(1)).join(' ') + '"/>';
  stellen.forEach(([x, y], i) => {
    if (mitPunkten || !gefuellt) {
      aus += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="'
           + (mitPunkten ? 4.5 : 3.5) + '" fill="' + linienfarbe + '"/>';
    }
    if (wie.werte !== false) {
      aus += '<text x="' + x.toFixed(1) + '" y="' + (y - 8).toFixed(1)
           + '" text-anchor="middle" font-size="10" fill="#111417">'
           + alsText(String(punkte[i].wert)) + '</text>';
    }
    aus += '<text x="' + x.toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(punkte[i].name) + '</text>';
  });
  return svgHuelle(breite, hoehe, aus);
}

function kuchenSvg(punkte, titel, wie) {
  wie = wie || {};
  const farben = wie.farben || DIAGRAMMFARBEN;
  const mitLoch = wie.loch === true;
  const breite = 480;
  const hoehe = 280;
  const mitteX = 150;
  const mitteY = titel ? 155 : 140;
  const r = 100;
  const summe = punkte.reduce((z, p) => z + Math.abs(p.wert), 0) || 1;

  let aus = '';
  if (titel) aus += '<text x="' + (breite / 2) + '" y="22" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';

  let winkel = -Math.PI / 2;
  punkte.forEach((p, i) => {
    const teil = Math.abs(p.wert) / summe * Math.PI * 2;
    const x1 = mitteX + r * Math.cos(winkel);
    const y1 = mitteY + r * Math.sin(winkel);
    winkel += teil;
    const x2 = mitteX + r * Math.cos(winkel);
    const y2 = mitteY + r * Math.sin(winkel);
    const gross = teil > Math.PI ? 1 : 0;
    const farbe = farben[i % farben.length];
    /* Ein einziges Stück wäre ein Kreis — und ein Kreisbogen über volle 360°
       zeichnet nichts. Deshalb dieser Sonderfall. */
    aus += punkte.length === 1
      ? '<circle data-teil="wert-' + i + '" cx="' + mitteX + '" cy="' + mitteY + '" r="' + r + '" fill="' + farbe + '"/>'
      : '<path data-teil="wert-' + i + '" d="M' + mitteX + ',' + mitteY + ' L' + x1.toFixed(1) + ',' + y1.toFixed(1)
        + ' A' + r + ',' + r + ' 0 ' + gross + ',1 ' + x2.toFixed(1) + ',' + y2.toFixed(1)
        + ' Z" fill="' + farbe + '"/>';

    const yl = (titel ? 60 : 46) + i * 22;
    aus += '<rect x="290" y="' + (yl - 10) + '" width="12" height="12" fill="' + farbe + '"/>';
    aus += '<text x="' + 310 + '" y="' + yl + '" font-size="11" fill="#111417">'
         + alsText(p.name) + ' — ' + Math.round(Math.abs(p.wert) / summe * 100) + ' %</text>';
  });
  /* Der Ring ist der Kreis mit einem Loch in der Mitte. Ein Kreis in
     Blattfarbe darauf ist der kuerzeste ehrliche Weg dorthin. */
  if (mitLoch) {
    aus += '<circle cx="' + mitteX + '" cy="' + mitteY + '" r="' + (r * 0.55).toFixed(1)
         + '" fill="var(--blatt, #ffffff)"/>';
  }
  return svgHuelle(breite, hoehe, aus);
}

const alsText = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/* Was ein Objekt zum Ändern braucht, hängt an ihm selbst.

   Ein Diagramm ist nach dem Einfügen erst einmal nur ein Bild: Die Zahlen,
   aus denen es entstand, stehen nirgends mehr. Wer eine davon ändern will,
   müsste alle neu tippen. Deshalb wandern sie als Angabe ins Element —
   dieselbe Stelle, an der auch die Werkzeuge sie später suchen.

   Sie stehen als JSON in einem einzigen Attribut, nicht in fünf einzelnen:
   So bleibt beim Speichern und Wiederöffnen alles beisammen, und ein
   neuer Wert braucht keine neue Zeile hier. */
function merkeQuelle(svgText, quelle) {
  const daten = JSON.stringify(quelle).replace(/"/g, '&quot;');
  return svgText.replace('<svg ', '<svg data-quelle="' + daten + '" ');
}

function quelleLesen(el) {
  if (!el || !el.dataset || !el.dataset.quelle) return null;
  try { return JSON.parse(el.dataset.quelle); } catch (e) { return null; }
}

const svgHuelle = (b, h, innen) =>
  '<svg class="diagramm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + b + ' ' + h + '"'
  + ' width="' + b + '" height="' + h + '" role="img">'
  + '<rect data-teil="grund" width="' + b + '" height="' + h + '" fill="#FFFFFF"/>'
  + innen + '</svg>';

/* ============================================================
   DIAGRAMM EINFUEGEN

   Nach seinem Bild des WPS-Fensters, Stueck fuer Stueck:

     ┌────────────┬──────────────────────────────────┐
     │ Spalte     │  [▮▮] [▮▮] [▮▮]                  │
     │ Linie      │                                  │
     │ Kreis      │  Gruppierte Säule                │
     │ Balken     │  ┌────────────────────────────┐  │
     │ Fläche     │  │      grosse Vorschau       │  │
     │ X Y (Punkt)│  └────────────────────────────┘  │
     │ …          │                                  │
     └────────────┴──────────────────────────────────┘
                                      OK   Abbrechen

   Erst die Gruppe links, dann die Art oben, dann sieht man gross, was
   man bekommt — und der Name steht dabei. „Gruppierte Saeule" und
   „Gestapelte Saeule" sind als Woerter fast gleich; als Bild nicht.

   Zahlen werden hier NICHT eingegeben. In WPS auch nicht — die kommen
   danach ueber „Daten bearbeiten". Wer erst die Form waehlt und dann
   die Zahlen, muss nicht beides gleichzeitig im Kopf haben.
   ============================================================ */
const DIAGRAMMKATALOG = [
  ['spalte', 'Spalte', 'saeule', [
    ['saeule',      'Gruppierte Säule'],
    ['saeulegest',  'Gestapelte Säule'],
    ['saeuleproz',  'Gestapelte Säule (100 %)'],
  ]],
  ['linie', 'Linie', 'linie', [
    ['linie',       'Linie'],
    ['liniepunkt',  'Linie mit Datenpunkten'],
  ]],
  ['kreis', 'Kreis', 'kreis', [
    ['kuchen',      'Kreis'],
    ['ring',        'Ring'],
  ]],
  ['balken', 'Balken', 'balkenquer', [
    ['balken',      'Gruppierte Balken'],
    ['balkengest',  'Gestapelte Balken'],
  ]],
  ['flaeche', 'Fläche', 'flaeche', [
    ['flaeche',     'Fläche'],
  ]],
  ['punkt', 'X Y (Punkt)', 'punktwolke', [
    ['punkte',      'Punkte (nur Marker)'],
  ]],
  ['kurs', 'Kurs', 'kurs', [
    ['kurs',        'Hoch, Niedrig, Schließen'],
  ]],
  ['netz', 'Netz', 'netz', [
    ['netz',        'Netz'],
  ]],
  ['kombi', 'Kombination', 'kombination', [
    ['kombi',       'Säulen und Linie'],
  ]],
  ['vorlagen', 'Vorlagen', 'vorlage', []],
];

/* „Vorlagen" ist in WPS kein Diagrammtyp, sondern die Liste dessen, was
   man sich selbst aufgehoben hat. Darum steht sie in der Gruppenspalte
   und zeigt rechts keine Arten, sondern die gemerkten Diagramme. */
let diagrammVorlagen = Speicher.lies('diagrammVorlagen', []);

function vorlageMerken(q, name) {
  diagrammVorlagen = diagrammVorlagen.filter((v) => v.name !== name);
  diagrammVorlagen.push({ name, art: q.art, satz: q.satz,
                          werte: q.werte, legende: q.legende });
  Speicher.schreib('diagrammVorlagen', diagrammVorlagen);
}

B.diagrammVorlageMerken = () => mitDiagramm((bild, q) => {
  fenster('Als Vorlage merken', [
    { art: 'satz', text: 'Gemerkt werden Art, Farben und was dranstehen soll — '
                       + 'nicht die Zahlen.' },
    { schluessel: 'name', name: 'Name', wert: diagrammName(q.art) },
  ], (werte) => {
    const name = (werte.name || '').trim();
    if (!name) return;
    vorlageMerken(q, name);
    melde('Als Vorlage „' + name + '" gemerkt.');
  }, 'Merken');
});

/* Vier Rubriken mit je drei Zahlen — dieselbe Beispielreihe, die auf
   seinem WPS-Bild in der Vorschau steht. Die zweite und dritte Zahl
   braucht nur, wer Kurs oder Kombination ansieht; alle anderen nehmen
   die erste. */
const DIAGRAMMPROBE = [
  { name: 'Rubrik 1', wert: 4.3, werte: [4.3, 2.4, 2] },
  { name: 'Rubrik 2', wert: 2.5, werte: [2.5, 4.4, 2] },
  { name: 'Rubrik 3', wert: 3.5, werte: [3.5, 1.8, 3] },
  { name: 'Rubrik 4', wert: 4.5, werte: [4.5, 2.8, 5] },
];

function diagrammName(kuerzel) {
  for (const [, , , arten] of DIAGRAMMKATALOG) {
    const t = arten.find(([k]) => k === kuerzel);
    if (t) return t[1];
  }
  return 'Diagramm';
}

B.diagramm = () => {
  auswahlMerken();
  let art = Speicher.lies('diagrammArt', 'saeule');
  let gruppeJetzt = (DIAGRAMMKATALOG.find(([, , , arten]) =>
    arten.some(([k]) => k === art)) || DIAGRAMMKATALOG[0])[0];
  let vorlageJetzt = null;

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog dialog--breit diagrammfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Diagramm einfügen</h3>';

  const koerper = document.createElement('div');
  koerper.className = 'diagrammfenster__koerper';

  const spalte = document.createElement('div');
  spalte.className = 'diagrammfenster__gruppen';
  const rechts = document.createElement('div');
  rechts.className = 'diagrammfenster__rechts';

  const reihe = document.createElement('div');
  reihe.className = 'diagrammfenster__arten';
  const ueberschrift = document.createElement('h4');
  ueberschrift.className = 'diagrammfenster__name';
  const gross = document.createElement('div');
  gross.className = 'diagrammfenster__vorschau';
  rechts.append(reihe, ueberschrift, gross);

  function rechtsBauen() {
    const g = DIAGRAMMKATALOG.find(([k]) => k === gruppeJetzt) || DIAGRAMMKATALOG[0];

    /* „Vorlagen" zeigt keine Arten, sondern das Gemerkte. */
    if (gruppeJetzt === 'vorlagen') {
      reihe.textContent = '';
      ueberschrift.textContent = diagrammVorlagen.length
        ? 'Gemerkte Vorlagen' : 'Noch keine Vorlage';
      gross.textContent = '';
      if (!diagrammVorlagen.length) {
        const satz = document.createElement('p');
        satz.className = 'zeitfenster__satz';
        satz.textContent = 'Ein Diagramm wählen, in den Diagrammtools '
                         + 'einstellen, wie es aussehen soll, und dort über '
                         + '„Als Vorlage merken" aufheben. Es steht dann hier.';
        gross.appendChild(satz);
        return;
      }
      const gitter = document.createElement('div');
      gitter.className = 'stilgitter';
      for (const v of diagrammVorlagen) {
        const k = document.createElement('button');
        k.type = 'button';
        k.className = 'stilkachel' + (art === v.art ? ' diagrammart--an' : '');
        k.title = v.name;
        const b = document.createElement('span');
        b.className = 'stilkachel__bild';
        b.innerHTML = diagrammZeichnen(v.art, DIAGRAMMPROBE, '', {
          farben: diagrammSatz(v.satz), werte: v.werte, legende: v.legende,
        });
        const w = document.createElement('span');
        w.className = 'stilkachel__name';
        w.textContent = v.name;
        k.append(b, w);
        k.addEventListener('click', () => {
          art = v.art;
          vorlageJetzt = v;
          [...gitter.children].forEach((c) => c.classList.remove('diagrammart--an'));
          k.classList.add('diagrammart--an');
        });
        k.addEventListener('dblclick', weiter);
        gitter.appendChild(k);
      }
      gross.appendChild(gitter);
      return;
    }
    vorlageJetzt = null;

    if (!g[3].some(([k]) => k === art)) art = g[3][0][0];

    reihe.textContent = '';
    for (const [kuerzel, name] of g[3]) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'diagrammart' + (art === kuerzel ? ' diagrammart--an' : '');
      k.title = name;
      k.innerHTML = diagrammZeichnen(kuerzel, DIAGRAMMPROBE.slice(0, 3), '', {
        farben: diagrammSatz('bunt'), werte: false, legende: false, klein: true,
      });
      k.addEventListener('click', () => { art = kuerzel; rechtsBauen(); });
      k.addEventListener('dblclick', weiter);
      reihe.appendChild(k);
    }
    ueberschrift.textContent = diagrammName(art);
    gross.innerHTML = diagrammZeichnen(art, DIAGRAMMPROBE, 'Diagrammtitel', {
      farben: diagrammSatz('bunt'), werte: false, legende: true,
    });
  }

  for (const [kuerzel, name, bild] of DIAGRAMMKATALOG) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'diagrammfenster__gruppe'
      + (kuerzel === gruppeJetzt ? ' diagrammfenster__gruppe--an' : '');
    if (SYMBOLE[bild]) k.appendChild(symbol(bild));
    const w = document.createElement('span');
    w.textContent = name;
    k.appendChild(w);
    k.addEventListener('click', () => {
      gruppeJetzt = kuerzel;
      [...spalte.children].forEach((c) => c.classList.remove('diagrammfenster__gruppe--an'));
      k.classList.add('diagrammfenster__gruppe--an');
      rechtsBauen();
    });
    spalte.appendChild(k);
  }

  koerper.append(spalte, rechts);
  kasten.appendChild(koerper);

  function weiter() {
    Speicher.schreib('diagrammArt', art);
    grund.remove();
    auswahlZurueck();
    /* Mit Beispielzahlen, wie in WPS: Das Diagramm steht sofort da, und
       „Daten bearbeiten" macht die eigenen daraus. Ein leeres Diagramm
       waere ein weisser Kasten, bei dem niemand weiss, was zu tun ist. */
    const daten = 'Rubrik 1: 4\nRubrik 2: 3\nRubrik 3: 5\nRubrik 4: 2';
    const punkte = zahlenLesen(daten);
    const quelle = vorlageJetzt
      ? { art: vorlageJetzt.art, titel: 'Diagrammtitel', daten,
          satz: vorlageJetzt.satz, werte: vorlageJetzt.werte,
          legende: vorlageJetzt.legende }
      : { art, titel: 'Diagrammtitel', daten,
          satz: 'bunt', werte: true, legende: true };
    Dokument.einfuegen('<p>' + merkeQuelle(
      diagrammZeichnen(quelle.art, punkte, quelle.titel, {
        farben: diagrammSatz(quelle.satz), werte: quelle.werte,
        legende: quelle.legende,
      }), quelle) + '</p><p><br></p>');
    geaendertMelden();
    melde(diagrammName(art) + ' eingefügt — die Zahlen ändern Sie mit '
        + '„Daten bearbeiten" in den Diagrammtools.');
  }

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe';
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'OK';
  ok.addEventListener('click', weiter);
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  ab.addEventListener('click', () => grund.remove());
  fuss.append(ok, ab);
  kasten.appendChild(fuss);

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
  rechtsBauen();
};


/* ============================================================
   Formeln

   Geschrieben wird, wie man es tippt: x^2, H_2O, (a+b)/2, sqrt(9).
   Daraus wird MathML — die Sprache, in der Formeln im Netz und in
   Office-Dateien stehen. Ein Bild wäre einfacher gewesen und beim
   Vergrößern unscharf.
   ============================================================ */
function formelBauen(roh) {
  const quelle = String(roh).trim();
  if (!quelle) return '';

  let stelle = 0;
  const zeichenVoraus = () => quelle[stelle];

  function ausdruck() {
    let teile = [begriff()];
    while (stelle < quelle.length && '+-'.includes(zeichenVoraus())) {
      const zeichen = quelle[stelle++];
      teile.push('<mo>' + (zeichen === '-' ? '−' : '+') + '</mo>', begriff());
    }
    return teile.join('');
  }

  function begriff() {
    let links = potenz();
    while (stelle < quelle.length && '*/·'.includes(zeichenVoraus())) {
      const zeichen = quelle[stelle++];
      const rechts = potenz();
      links = zeichen === '/'
        ? '<mfrac>' + einhuellen(links) + einhuellen(rechts) + '</mfrac>'
        : links + '<mo>·</mo>' + rechts;
    }
    return links;
  }

  function potenz() {
    let grund = teil();
    while (stelle < quelle.length && '^_'.includes(zeichenVoraus())) {
      const zeichen = quelle[stelle++];
      const oben = teil();
      grund = (zeichen === '^' ? '<msup>' : '<msub>')
            + einhuellen(grund) + einhuellen(oben)
            + (zeichen === '^' ? '</msup>' : '</msub>');
    }
    return grund;
  }

  function teil() {
    while (quelle[stelle] === ' ') stelle++;

    if (quelle.startsWith('sqrt', stelle)) {
      stelle += 4;
      return '<msqrt>' + einhuellen(klammer()) + '</msqrt>';
    }
    if (zeichenVoraus() === '(') return klammer();

    const zahl = /^[\d.,]+/.exec(quelle.slice(stelle));
    if (zahl) { stelle += zahl[0].length; return '<mn>' + alsText(zahl[0]) + '</mn>'; }

    const wort = /^[A-Za-zÄÖÜäöüß]+/.exec(quelle.slice(stelle));
    if (wort) { stelle += wort[0].length; return '<mi>' + alsText(wort[0]) + '</mi>'; }

    const einzeln = quelle[stelle++] || '';
    return einzeln ? '<mo>' + alsText(einzeln) + '</mo>' : '';
  }

  function klammer() {
    if (zeichenVoraus() !== '(') return teil();
    stelle++;                                   // die Klammer selbst
    const innen = ausdruck();
    if (zeichenVoraus() === ')') stelle++;
    return innen;
  }

  /* MathML erwartet an manchen Stellen genau EIN Element. Steht dort mehr,
     kommt es in eine Reihe — sonst rutscht der Bruchstrich an die falsche
     Stelle. */
  const einhuellen = (teilStueck) =>
    /^<m[a-z]+[^>]*>[\s\S]*<\/m[a-z]+>$/.test(teilStueck) && (teilStueck.match(/^<(m[a-z]+)/) || [])[1]
      && teilStueck.indexOf('</') === teilStueck.lastIndexOf('</')
      ? teilStueck
      : '<mrow>' + teilStueck + '</mrow>';

  return '<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">'
       + ausdruck() + '</math>';
}

B.formel = () => {
  auswahlMerken();
  fenster('Formel einfügen', [
    { art: 'satz', text: 'So tippen, wie man es sagt:\n'
        + 'x^2   hoch      H_2O   tief\n'
        + '(a+b)/2   Bruch      sqrt(9)   Wurzel' },
    { schluessel: 'formel', name: 'Formel', wert: '(a+b)/2' },
  ], (werte) => {
    const mathml = formelBauen(werte.formel);
    if (!mathml) return;
    auswahlZurueck();
    /* Die getippte Formel bleibt am Element: MathML lässt sich lesen, aber
       nicht zurückverwandeln — „(a+b)/2" wäre sonst für immer weg. */
    Dokument.einfuegen(mathml.replace('<math ',
      '<math data-quelle="' + JSON.stringify({ formel: werte.formel }).replace(/"/g, '&quot;') + '" '));
    melde('Formel eingefügt.');
  }, 'Einfügen');
};

/* ============================================================
   Zeichnen

   Vier Formen, die in einem Schreibprogramm wirklich vorkommen: Linie,
   Pfeil, Rechteck, Kreis. Auch sie sind SVG und damit Teil des Textes.
   ============================================================ */
/* ============================================================
   DIE FORMEN-GALERIE

   WPS bietet acht Gruppen mit rund hundertfuenfzig Formen. Lunivo hatte
   vier: Linie, Pfeil, Rechteck, Kreis — in einem Klappfeld, in dem man
   den Namen lesen und sich die Form vorstellen musste.

   Jede Form ist ein Pfad in einem Feld von 100 x 100 und wird beim
   Einfuegen auf die gewuenschte Groesse gezogen. Ein Pfad statt eines
   fertigen SVG je Form: So lassen sie sich alle gleich behandeln —
   faerben, umranden, spaeter drehen.

   VIERECKIGE UND RUNDE FORMEN sind Pfade; die Linie und der Pfeil
   bleiben Sonderfaelle, weil sie keine Flaeche haben und der Pfeil eine
   Spitze braucht.
   ============================================================ */
const FORMGRUPPEN = [
  ['Linie', [
    ['linie',       'Linie',              'M4 96 L96 4'],
    ['linie-waag',  'Waagerechte Linie',  'M4 50 L96 50'],
    ['linie-senk',  'Senkrechte Linie',   'M50 4 L50 96'],
    ['winkel',      'Winkel',             'M4 4 L4 96 L96 96'],
    ['zickzack',    'Zickzack',           'M4 76 L28 24 L52 76 L76 24 L96 60'],
    ['bogen',       'Bogen',              'M6 92 Q50 -12 94 92'],
    ['welle',       'Welle',              'M4 50 Q20 14 36 50 T68 50 T96 50'],
  ]],
  ['Rechteck', [
    ['rechteck',    'Rechteck',           'M6 18 H94 V82 H6 Z'],
    ['rund',        'Abgerundet',         'M20 18 H80 A14 14 0 0 1 94 32 V68 A14 14 0 0 1 80 82 H20 A14 14 0 0 1 6 68 V32 A14 14 0 0 1 20 18 Z'],
    ['ecke-ab',     'Ecke abgeschnitten', 'M6 18 H78 L94 34 V82 H6 Z'],
    ['ecke-rund',   'Eine Ecke rund',     'M6 18 H78 A16 16 0 0 1 94 34 V82 H6 Z'],
    ['raute-recht', 'Parallelogramm',     'M22 18 H94 L78 82 H6 Z'],
    ['trapez',      'Trapez',             'M22 18 H78 L94 82 H6 Z'],
  ]],
  ['Standardformen', [
    ['kreis',       'Kreis',              'M50 6 A44 44 0 1 1 49.9 6 Z'],
    ['ellipse',     'Ellipse',            'M50 18 A44 32 0 1 1 49.9 18 Z'],
    ['dreieck',     'Dreieck',            'M50 8 L94 92 H6 Z'],
    ['dreieck-r',   'Rechtwinkliges Dreieck', 'M6 92 V8 L94 92 Z'],
    ['raute',       'Raute',              'M50 6 L94 50 L50 94 L6 50 Z'],
    ['fuenfeck',    'Fünfeck',            'M50 6 L94 39 L77 92 H23 L6 39 Z'],
    ['sechseck',    'Sechseck',           'M28 10 H72 L94 50 L72 90 H28 L6 50 Z'],
    ['achteck',     'Achteck',            'M32 6 H68 L94 32 V68 L68 94 H32 L6 68 V32 Z'],
    ['kreuz',       'Kreuz',              'M36 6 H64 V36 H94 V64 H64 V94 H36 V64 H6 V36 H36 Z'],
    ['herz',        'Herz',               'M50 92 C10 62 6 36 22 22 C34 12 46 18 50 30 C54 18 66 12 78 22 C94 36 90 62 50 92 Z'],
    ['mond',        'Mond',               'M62 6 A46 46 0 1 0 62 94 A36 36 0 1 1 62 6 Z'],
    ['tropfen',     'Tropfen',            'M50 6 C74 34 88 50 88 64 A38 38 0 0 1 12 64 C12 50 26 34 50 6 Z'],
    ['wolke',       'Wolke',              'M26 78 A18 18 0 0 1 24 44 A20 20 0 0 1 60 30 A18 18 0 0 1 86 48 A16 16 0 0 1 80 78 Z'],
    ['blitz',       'Blitz',              'M56 4 L26 54 H48 L40 96 L74 42 H52 Z'],
    ['klammer-a',   'Geschweifte Klammer auf', 'M62 6 C46 6 50 44 34 50 C50 56 46 94 62 94'],
    ['klammer-z',   'Geschweifte Klammer zu',  'M38 6 C54 6 50 44 66 50 C50 56 54 94 38 94'],
  ]],
  ['Blockpfeile', [
    ['pfeil-r',     'Pfeil nach rechts',  'M6 36 H58 V16 L94 50 L58 84 V64 H6 Z'],
    ['pfeil-l',     'Pfeil nach links',   'M94 36 H42 V16 L6 50 L42 84 V64 H94 Z'],
    ['pfeil-o',     'Pfeil nach oben',    'M36 94 V42 H16 L50 6 L84 42 H64 V94 Z'],
    ['pfeil-u',     'Pfeil nach unten',   'M36 6 V58 H16 L50 94 L84 58 H64 V6 Z'],
    ['pfeil-lr',    'Pfeil nach links und rechts', 'M6 50 L30 24 V38 H70 V24 L94 50 L70 76 V62 H30 V76 Z'],
    ['pfeil-ou',    'Pfeil nach oben und unten',   'M50 6 L76 30 H62 V70 H76 L50 94 L24 70 H38 V30 H24 Z'],
    ['pfeil-kreuz', 'Pfeil in vier Richtungen',    'M50 4 L68 26 H58 V42 H74 V32 L96 50 L74 68 V58 H58 V74 H68 L50 96 L32 74 H42 V58 H26 V68 L4 50 L26 32 V42 H42 V26 H32 Z'],
    ['pfeil-ecke',  'Pfeil um die Ecke',  'M6 94 V40 A30 30 0 0 1 36 10 H58 V0 L94 22 L58 44 V34 H40 A8 8 0 0 0 32 42 V94 Z'],
  ]],
  ['Formelformen', [
    ['plus',        'Plus',               'M40 14 H60 V40 H86 V60 H60 V86 H40 V60 H14 V40 H40 Z'],
    ['minus',       'Minus',              'M14 40 H86 V60 H14 Z'],
    ['mal',         'Mal',                'M22 8 L50 36 L78 8 L92 22 L64 50 L92 78 L78 92 L50 64 L22 92 L8 78 L36 50 L8 22 Z'],
    ['geteilt',     'Geteilt',            'M40 14 A10 10 0 1 1 60 14 A10 10 0 1 1 40 14 Z M14 40 H86 V60 H14 Z M40 86 A10 10 0 1 1 60 86 A10 10 0 1 1 40 86 Z'],
    ['gleich',      'Gleich',             'M14 28 H86 V44 H14 Z M14 56 H86 V72 H14 Z'],
    ['ungleich',    'Ungleich',           'M14 28 H86 V44 H14 Z M14 56 H86 V72 H14 Z M34 92 L58 8 H70 L46 92 Z'],
  ]],
  ['Flussdiagramm', [
    ['fd-prozess',  'Prozess',            'M6 24 H94 V76 H6 Z'],
    ['fd-ent',      'Entscheidung',       'M50 10 L94 50 L50 90 L6 50 Z'],
    ['fd-daten',    'Daten',              'M24 24 H94 L76 76 H6 Z'],
    ['fd-start',    'Anfang oder Ende',   'M30 24 H70 A26 26 0 0 1 70 76 H30 A26 26 0 0 1 30 24 Z'],
    ['fd-doku',     'Dokument',           'M6 20 H94 V72 Q72 88 50 76 T6 80 Z'],
    ['fd-hand',     'Manuelle Eingabe',   'M6 36 L94 18 V80 H6 Z'],
    ['fd-vor',      'Vorbereitung',       'M24 24 H76 L94 50 L76 76 H24 L6 50 Z'],
    ['fd-speicher', 'Gespeicherte Daten', 'M18 24 H94 A14 26 0 0 0 94 76 H18 A14 26 0 0 1 18 24 Z'],
    ['fd-verbind',  'Verbindung',         'M50 12 A38 38 0 1 1 49.9 12 Z'],
  ]],
  ['Sterne und Banner', [
    ['stern4',      'Stern mit 4 Zacken', 'M50 4 L62 38 L96 50 L62 62 L50 96 L38 62 L4 50 L38 38 Z'],
    ['stern5',      'Stern mit 5 Zacken', 'M50 4 L61 36 L96 36 L68 57 L79 90 L50 69 L21 90 L32 57 L4 36 L39 36 Z'],
    ['stern6',      'Stern mit 6 Zacken', 'M50 4 L65 30 L95 30 L80 56 L95 82 L65 82 L50 108 L35 82 L5 82 L20 56 L5 30 L35 30 Z'],
    ['stern8',      'Stern mit 8 Zacken', 'M50 4 L59 32 L86 18 L72 45 L96 50 L72 55 L86 82 L59 68 L50 96 L41 68 L14 82 L28 55 L4 50 L28 45 L14 18 L41 32 Z'],
    ['explosion',   'Explosion',          'M50 2 L58 26 L78 12 L74 36 L98 34 L82 50 L98 66 L74 64 L78 88 L58 74 L50 98 L42 74 L22 88 L26 64 L2 66 L18 50 L2 34 L26 36 L22 12 L42 26 Z'],
    ['band',        'Band',               'M6 28 H94 V72 H76 L84 86 L60 72 H6 Z'],
    ['schriftrolle','Schriftrolle',       'M14 26 A8 8 0 0 1 14 42 H86 A8 8 0 0 1 86 58 H14 A8 8 0 0 1 14 74 H86'],
  ]],
  ['Legenden', [
    ['legende-e',   'Legende, eckig',     'M6 14 H94 V64 H56 L40 86 L38 64 H6 Z'],
    ['legende-r',   'Legende, rund',      'M50 14 A44 26 0 1 1 49.9 14 Z M36 62 L30 88 L52 66 Z'],
    ['legende-w',   'Gedankenblase',      'M50 12 A40 26 0 1 1 49.9 12 Z M30 66 A7 7 0 1 1 29.9 66 Z M20 82 A5 5 0 1 1 19.9 82 Z'],
    ['legende-l',   'Linienlegende',      'M34 14 H94 V54 H34 Z M34 34 L6 86'],
  ]],
];

/* Die Linie und der Pfeil haben keine Flaeche — sie werden nur
   gestrichelt gezeichnet, nie gefuellt. */
const NUR_STRICH = new Set(['linie', 'linie-waag', 'linie-senk', 'winkel',
  'zickzack', 'bogen', 'welle', 'klammer-a', 'klammer-z', 'schriftrolle']);

function formPfad(kennung) {
  for (const [, formen] of FORMGRUPPEN) {
    for (const [k, , d] of formen) if (k === kennung) return d;
  }
  return null;
}

function formBauen(kennung, fuellung, strichfarbe, breite, hoehe) {
  const d = formPfad(kennung);
  if (!d) return null;
  const nurStrich = NUR_STRICH.has(kennung);
  return '<svg class="zeichnung" xmlns="http://www.w3.org/2000/svg" '
       + 'viewBox="0 0 100 100" preserveAspectRatio="none" '
       + 'width="' + breite + '" height="' + hoehe + '">'
       + '<path d="' + d + '" fill="' + (nurStrich ? 'none' : fuellung) + '" '
       + 'stroke="' + strichfarbe + '" stroke-width="3" '
       + 'stroke-linejoin="round" stroke-linecap="round" '
       + 'vector-effect="non-scaling-stroke"/></svg>';
}

/* Die Galerie. Aufbau wie bei WPS: Gruppenueberschrift, darunter die
   Formen als Bildchen — man sieht, was man bekommt, statt einen Namen
   zu lesen und sich die Form vorzustellen. */
let formenKlappe = null;

function formenKlappeWeg() {
  if (formenKlappe) { formenKlappe.remove(); formenKlappe = null; }
}

B.formenGalerie = (knopf) => {
  if (formenKlappe) { formenKlappeWeg(); return; }
  auswahlMerken();

  const tafel = document.createElement('div');
  tafel.className = 'katalogklappe formenklappe';

  const kopf = document.createElement('p');
  kopf.className = 'katalogklappe__kopf';
  kopf.textContent = 'Form einfügen';
  tafel.appendChild(kopf);

  for (const [name, formen] of FORMGRUPPEN) {
    const h = document.createElement('p');
    h.className = 'formenklappe__gruppe';
    h.textContent = name;
    tafel.appendChild(h);

    const gitter = document.createElement('div');
    gitter.className = 'formenklappe__gitter';
    for (const [kennung, anzeige, d] of formen) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'formenklappe__form';
      k.title = anzeige;
      k.setAttribute('aria-label', anzeige);
      k.innerHTML = '<svg viewBox="-6 -6 112 112" aria-hidden="true">'
        + '<path d="' + d + '" fill="none" stroke="currentColor" '
        + 'stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/></svg>';
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        formenKlappeWeg();
        formEinfuegen(kennung, anzeige);
      });
      gitter.appendChild(k);
    }
    tafel.appendChild(gitter);
  }

  document.body.appendChild(tafel);
  formenKlappe = tafel;

  const r = (knopf && knopf.getBoundingClientRect)
    ? knopf.getBoundingClientRect()
    : { left: 200, bottom: 120, top: 120, right: 240 };
  const m = tafel.getBoundingClientRect();
  let links = r.left;
  if (links + m.width > window.innerWidth - 8) {
    links = Math.max(8, window.innerWidth - 8 - m.width);
  }
  tafel.style.left = Math.round(links) + 'px';
  tafel.style.top = Math.round(Math.min(r.bottom + 4,
    Math.max(8, window.innerHeight - 8 - m.height))) + 'px';

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(ev) {
      if (tafel.contains(ev.target) || (knopf && knopf.contains(ev.target))) return;
      formenKlappeWeg();
      document.removeEventListener('mousedown', zu);
    });
  }, 0);
};

function formEinfuegen(kennung, anzeige) {
  const roh = formBauen(kennung, '#D6E4F0', '#2F6FB5', 120, 90);
  if (!roh) return;
  auswahlZurueck();
  Dokument.einfuegen(merkeQuelle(roh,
    { form: kennung, farbe: '#2F6FB5', fuellung: '#D6E4F0', strich: 3 }));
  melde(anzeige + ' eingefügt — anfassen und ziehen wie ein Bild.');
}

/* Der alte Weg bleibt: Wer eine Farbe gleich mitgeben will, bekommt
   weiter das Fenster. */
B.zeichnen = () => {
  auswahlMerken();
  const alle = [];
  for (const [gruppe, formen] of FORMGRUPPEN) {
    for (const [k, n] of formen) alle.push([k, gruppe + ' — ' + n]);
  }
  fenster('Form einfügen', [
    { art: 'satz', text: 'Die Form kommt an die Stelle des Zeigers und '
        + 'lässt sich danach wie ein Bild behandeln.\n'
        + 'Schneller geht es über das Formen-Raster in der Leiste.' },
    { schluessel: 'form', name: 'Form', art: 'auswahl', werte: alle },
    { schluessel: 'fuellung', name: 'Füllung', art: 'color', wert: '#D6E4F0' },
    { schluessel: 'farbe', name: 'Linie', art: 'color', wert: '#2F6FB5' },
  ], (werte) => {
    const roh = formBauen(werte.form, werte.fuellung, werte.farbe, 120, 90);
    if (!roh) { melde('Diese Form kenne ich nicht.'); return; }
    auswahlZurueck();
    Dokument.einfuegen(merkeQuelle(roh,
      { form: werte.form, farbe: werte.farbe, fuellung: werte.fuellung, strich: 3 }));
    melde('Form eingefügt.');
  }, 'Einfügen');
};

/* ============================================================
   AutoKorrektur

   Was jedes Schreibprogramm still im Hintergrund tut: gerade
   Anführungszeichen zu deutschen machen, zwei Bindestriche zu einem
   Gedankenstrich, drei Punkte zu einem Auslassungszeichen.

   Sie greift erst beim Leerzeichen oder Satzzeichen danach — mitten im
   Wort einzugreifen wäre Bevormundung.
   ============================================================ */
let autokorrekturAn = Speicher.lies('autokorrektur', true);

/* Die AutoKorrektur, nach Regeln geordnet.

   Sie war eine Liste von sieben Ersetzungen, die nur zusammen an- oder
   auszuschalten waren. WPS führt an derselben Stelle elf einzelne
   Kästchen — „Jeden Satz mit einem Großbuchstaben beginnen",
   „Wochentage immer großschreiben" und so fort.

   Damit die Kästchen etwas bewirken und nicht bloß dastehen, hängt jede
   Ersetzung jetzt an einem Namen aus SCHALTER. Was es dafür noch nicht
   gab — Satzanfang, Wochentage, Ordnungszahlen, Feststelltaste, Verweise
   — ist dazugekommen; die Kästchen wären sonst Attrappen.

   Der Hauptschalter „AutoKorrektur" bleibt darüber: Aus gesehen läuft
   keine einzige, gleich was darunter angekreuzt ist. */
const WOCHENTAGE = ['montag', 'dienstag', 'mittwoch', 'donnerstag',
                    'freitag', 'samstag', 'sonnabend', 'sonntag'];

const AUTOKORREKTUR = [
  { schalter: 'akAnfuehrung', regeln: [
    [/(^|[\s(\[])"/g, '$1„'],          // öffnendes Anführungszeichen
    [/"/g, '"'],                        // schließendes
    [/(^|[\s(\[])'/g, '$1‚'],
    [/'/g, "'"],
  ] },
  { schalter: 'akGedankenstrich', regeln: [
    [/(\s)--(\s)/g, '$1–$2'],
    [/(\d)\s*-\s*(\d)/g, '$1–$2'],     // Zahlenbereich: 10–20
  ] },
  { schalter: 'akAuslassung', regeln: [
    [/\.\.\./g, '…'],
  ] },

  /* Neu, für die Kästchen, die WPS führt und Lunivo noch nicht hatte. */

  /* „Unbeabsichtigtes Verwenden der fESTSTELLTASTE korrigieren": ein
     kleiner erster Buchstabe, danach lauter große — das passiert nur mit
     eingerasteter Taste.

     Steht VOR der Satzanfang-Regel, und das ist kein Zufall: Die macht aus
     dem kleinen f ein großes, und danach ist „fESTSTELLTASTE" nur noch ein
     Wort in Großbuchstaben, dem man nichts mehr ansieht. Geprüft am
     laufenden Programm — vorher kam „FESTSTELLTASTE" heraus. */
  { schalter: 'akFeststelltaste', regeln: [
    [/\b([a-zäöü])([A-ZÄÖÜ]{2,})\b/g, (_, erst, rest) =>
      erst.toUpperCase() + rest.toLowerCase()],
  ] },

  /* „Jeden Satz mit einem Großbuchstaben beginnen." Nur nach Punkt,
     Ruf- oder Fragezeichen und einem Leerzeichen — und nicht hinter
     einer Abkürzung wie „z. B.", wo der Punkt keinen Satz beendet. */
  { schalter: 'akSatzGross', regeln: [
    [/(^|[.!?]\s)([a-zäöüß])(?=\w)/g, (_, vorn, b) => vorn + b.toUpperCase()],
  ] },

  /* „Wochentage immer großschreiben." */
  { schalter: 'akWochentage', regeln: [
    [new RegExp('\\b(' + WOCHENTAGE.join('|') + ')\\b', 'g'),
     (w) => w.charAt(0).toUpperCase() + w.slice(1)],
  ] },

  /* „Englisch Ordnungszahlen hochstellen": 1st, 2nd, 3rd, 4th. */
  { schalter: 'akOrdnungszahlen', regeln: [
    [/\b(\d+)(st|nd|rd|th)\b/g, (_, zahl, endung) =>
      zahl + endung.replace(/./g, (c) => 'ˢᵗⁿᵈʳᵈᵗʰ'['stnrdh'.indexOf(c)] || c)],
  ] },

];

/* Flach und nur das, was gerade gelten soll. */
function autokorrekturRegeln() {
  const liste = [];
  for (const teil of AUTOKORREKTUR) {
    if (schalterAn(teil.schalter)) liste.push(...teil.regeln);
  }
  return liste;
}

function autokorrekturLaufen() {
  if (!autokorrekturAn) return;
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || !auswahl.isCollapsed) return;

  const knoten = auswahl.anchorNode;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return;

  const bis = auswahl.anchorOffset;
  const alt = knoten.data.slice(0, bis);
  let neu = alt;
  for (const [suche, ersatz] of autokorrekturRegeln()) neu = neu.replace(suche, ersatz);
  if (neu === alt) return;

  /* Gleiche Länge vorausgesetzt bleibt der Zeiger, wo er war. Wird der Text
     kürzer (drei Punkte werden eins), wandert er entsprechend mit. */
  knoten.data = neu + knoten.data.slice(bis);
  const stelle = Math.max(0, bis - (alt.length - neu.length));
  const bereich = document.createRange();
  bereich.setStart(knoten, Math.min(stelle, knoten.data.length));
  bereich.collapse(true);
  auswahl.removeAllRanges();
  auswahl.addRange(bereich);
}

B.autokorrektur = () => {
  autokorrekturAn = !autokorrekturAn;
  Speicher.schreib('autokorrektur', autokorrekturAn);
  melde(autokorrekturAn ? 'AutoKorrektur an.' : 'AutoKorrektur aus.');
  menueBauen();
};

/* ============================================================
   Änderungen verfolgen

   Angeschaltet wird nichts mehr still ersetzt: Neues kommt als <ins> dazu,
   Gelöschtes bleibt als <del> stehen und wird nur durchgestrichen. Am Ende
   entscheidet ein Mensch — alles übernehmen oder alles verwerfen.

   Der Weg führt über „beforeinput": Dort ist die Änderung noch nicht
   geschehen, und man kann sie durch eine eigene ersetzen.
   ============================================================ */
let verfolgenAn = Speicher.lies('verfolgen', false);

function verfolgenAbfangen(e) {
  if (!verfolgenAn) return;

  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return;
  const bereich = auswahl.getRangeAt(0);
  if (!feld.contains(bereich.commonAncestorContainer)) return;

  /* Schon Gelöschtes noch einmal zu löschen ergäbe <del> in <del>. Und in
     eigenem <ins> darf normal getippt werden — es ist ja neu. */
  const drin = (name) => {
    let k = bereich.startContainer;
    while (k && k !== feld) {
      if (k.nodeType === Node.ELEMENT_NODE && k.tagName === name) return true;
      k = k.parentNode;
    }
    return false;
  };

  if (e.inputType === 'insertText' && e.data) {
    if (drin('INS')) return;                    // im eigenen Neuen: einfach tippen
    e.preventDefault();
    if (!bereich.collapsed) verfolgtLoeschen(bereich);
    const neu = document.createElement('ins');
    neu.className = 'verfolgt';
    neu.textContent = e.data;
    const jetzt = window.getSelection().getRangeAt(0);
    jetzt.insertNode(neu);
    const danach = document.createRange();
    danach.setStartAfter(neu);
    danach.collapse(true);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(danach);
    geaendertMelden();
    return;
  }

  if (e.inputType.startsWith('delete')) {
    e.preventDefault();
    let ziel = bereich;
    if (bereich.collapsed) {
      /* Ein Tastendruck löscht ein Zeichen — welches, sagt die Richtung. */
      const rueckwaerts = e.inputType.includes('Backward');
      ziel = bereich.cloneRange();
      try {
        if (rueckwaerts) ziel.setStart(bereich.startContainer, Math.max(0, bereich.startOffset - 1));
        else ziel.setEnd(bereich.endContainer, bereich.endOffset + 1);
      } catch (fehler) { return; }
    }
    verfolgtLoeschen(ziel);
    geaendertMelden();
  }
}

function verfolgtLoeschen(bereich) {
  if (bereich.collapsed) return;
  const stueck = bereich.extractContents();

  /* Was gerade erst dazukam, muss beim Löschen nicht als gelöscht markiert
     werden — es hat den Text nie erreicht. */
  const nurNeues = [...stueck.childNodes].every(
    (k) => k.nodeType === Node.ELEMENT_NODE && k.tagName === 'INS');
  if (nurNeues) { window.getSelection().collapse(bereich.startContainer, bereich.startOffset); return; }

  const weg = document.createElement('del');
  weg.className = 'verfolgt';
  weg.appendChild(stueck);
  bereich.insertNode(weg);

  const danach = document.createRange();
  danach.setStartAfter(weg);
  danach.collapse(true);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(danach);
}

B.verfolgen = () => {
  verfolgenAn = !verfolgenAn;
  Speicher.schreib('verfolgen', verfolgenAn);
  feld.classList.toggle('dokument--verfolgt', verfolgenAn);
  melde(verfolgenAn
    ? 'Änderungen werden verfolgt: Neues steht unterstrichen, Gelöschtes durchgestrichen.'
    : 'Änderungen werden nicht mehr verfolgt.');
  menueBauen();
};

B.aenderungenUebernehmen = () => {
  const neu = feld.querySelectorAll('ins.verfolgt');
  const weg = feld.querySelectorAll('del.verfolgt');
  if (!neu.length && !weg.length) { melde('Es steht nichts an.'); return; }
  for (const el of neu) el.replaceWith(...el.childNodes);
  for (const el of weg) el.remove();
  geaendertMelden();
  melde(neu.length + ' übernommen, ' + weg.length + ' entfernt.');
};

B.aenderungenVerwerfen = () => {
  const neu = feld.querySelectorAll('ins.verfolgt');
  const weg = feld.querySelectorAll('del.verfolgt');
  if (!neu.length && !weg.length) { melde('Es steht nichts an.'); return; }
  for (const el of neu) el.remove();
  for (const el of weg) el.replaceWith(...el.childNodes);
  geaendertMelden();
  melde('Alles zurückgenommen: ' + neu.length + ' verworfen, ' + weg.length + ' wiederhergestellt.');
};

/* ============================================================
   Seriendruck

   Ein Brief, viele Empfänger. Im Text stehen Platzhalter in doppelten
   geschweiften Klammern; die Namen dafür stehen in der ersten Zeile der
   Tabelle. Für jede weitere Zeile entsteht ein Brief, getrennt durch einen
   Seitenumbruch.
   ============================================================ */
function tabelleLesen(roh) {
  const zeilen = String(roh).split(/\r?\n/).filter((z) => z.trim());
  if (zeilen.length < 2) return null;
  const trenner = zeilen[0].includes('\t') ? '\t' : (zeilen[0].includes(';') ? ';' : ',');
  const spalten = zeilen[0].split(trenner).map((z) => z.trim());
  const saetze = [];
  for (const zeile of zeilen.slice(1)) {
    const werte = zeile.split(trenner).map((z) => z.trim());
    const satz = {};
    spalten.forEach((name, i) => { satz[name] = werte[i] || ''; });
    saetze.push(satz);
  }
  return { spalten, saetze };
}

B.seriendruck = () => {
  const vorlage = Dokument.inhalt();
  const platzhalter = [...new Set((Dokument.lies().text.match(/\{\{\s*[^}]+\s*\}\}/g) || [])
                                  .map((p) => p.replace(/[{}\s]/g, '')))];

  fenster('Seriendruck', [
    { art: 'satz', text: platzhalter.length
        ? 'Im Text gefunden: ' + platzhalter.map((p) => '{{' + p + '}}').join(', ')
          + '\nDie erste Zeile unten muss diese Namen enthalten.'
        : 'Im Text stehen noch keine Platzhalter. Schreibe {{Name}} hinein, wo\n'
          + 'der Name stehen soll, und komm dann hierher zurück.' },
    { schluessel: 'daten', name: 'Empfänger', art: 'flaeche', zeilen: 7,
      wert: Speicher.lies('empfaengerliste', '')
            || (platzhalter.length ? platzhalter.join(';') + '\n'
                                   : 'Name;Ort\nFrau Meier;Kiel\nHerr Schmidt;Bonn') },
  ], (werte) => {
    const tabelle = tabelleLesen(werte.daten);
    if (!tabelle) { melde('Dafür braucht es eine Kopfzeile und mindestens einen Empfänger.'); return; }

    /* Die Liste bleibt gespeichert: Für die Vorschau und den nächsten
       Seriendruck soll niemand sie zweimal eintippen. */
    Speicher.schreib('empfaengerliste', werte.daten);

    const briefe = tabelle.saetze.map((satz) => serienEinsetzen(vorlage, satz));

    /* Alle Briefe in EIN Dokument, durch Seitenumbrüche getrennt: So lässt
       sich alles auf einmal drucken oder als eine Datei ablegen. */
    Dokument.setzeInhalt(briefe.join('<p style="page-break-after:always"></p>'));
    dateiname = dateiname + ' — Seriendruck';
    titelSetzen();
    melde(briefe.length + ' Briefe erzeugt. Strg+Z holt die Vorlage zurück.');
  }, 'Briefe erzeugen');
};

/* ============================================================
   Formatvorlagen verwalten

   Zuweisen konnte das Programm schon. Hier lässt sich ändern, WIE eine
   Vorlage aussieht — und das gilt dann für jeden Absatz, der sie trägt.
   Genau darin liegt der Sinn von Vorlagen: einmal ändern, überall wirksam.

   Die Angaben landen in einem eigenen Stilblatt, nicht an den Absätzen
   selbst. Sonst müsste beim Ändern jeder Absatz angefasst werden.
   ============================================================ */
const VORLAGEN_STANDARD = {
  p:          { name: 'Fließtext',      groesse: 12, fett: false, farbe: '#111417', abstand: 2.5 },
  /* „Titel" und „Untertitel" stehen in Word über den Überschriften: Sie
     benennen das ganze Schreiben, nicht einen Abschnitt darin. */
  'h1.titel':      { name: 'Titel',      groesse: 28, fett: true,  farbe: '#111417', abstand: 2 },
  'h2.untertitel': { name: 'Untertitel', groesse: 16, fett: false, farbe: '#4C555E', abstand: 6 },
  'p.ohne-abstand': { name: 'Kein Leerraum', groesse: 12, fett: false, farbe: '#111417', abstand: 0 },
  h1:         { name: 'Überschrift 1',  groesse: 20, fett: true,  farbe: '#111417', abstand: 4 },
  h2:         { name: 'Überschrift 2',  groesse: 16, fett: true,  farbe: '#111417', abstand: 3.5 },
  h3:         { name: 'Überschrift 3',  groesse: 14, fett: true,  farbe: '#111417', abstand: 3 },
  h4:         { name: 'Überschrift 4',  groesse: 12, fett: true,  farbe: '#111417', abstand: 3 },
  blockquote: { name: 'Zitat',          groesse: 12, fett: false, farbe: '#4C555E', abstand: 3 },
  pre:        { name: 'Vorformatiert',  groesse: 11, fett: false, farbe: '#111417', abstand: 2.5 },
};

let vorlagenStile = Object.assign({}, VORLAGEN_STANDARD, Speicher.lies('vorlagenstile', {}));

/* Was eine Vorlage außer Größe, Fett, Farbe und Abstand noch tragen kann.
 *
 * Diese Felder sind später dazugekommen — für den Dialog „Neue
 * Formatvorlage". Sie sind alle FREIWILLIG: Steht nichts drin, schreibt
 * das Stilblatt dazu auch nichts, und der Absatz nimmt, was das Blatt
 * vorgibt. Ohne das verlören alle Vorlagen, die schon auf einem Rechner
 * liegen, beim ersten Start ihre Schrift und ihre Ausrichtung — sie
 * kennen die neuen Felder ja nicht.
 */
const VORLAGE_ZUSATZ = {
  schrift: '',        /* leer: die Schrift des Blattes */
  kursiv: false,
  ausrichtung: '',    /* leer: wie das Blatt, also links */
  zeilen: 0,          /* 0: wie das Blatt */
  abstandVor: 0,      /* mm */
  einzug: 0,          /* mm, nur die erste Zeile */
};

function vorlagenAnwenden() {
  let blatt = document.getElementById('vorlagenblatt');
  if (!blatt) {
    blatt = document.createElement('style');
    blatt.id = 'vorlagenblatt';
    document.head.appendChild(blatt);
  }
  let css = '';
  for (const [tag, wie] of Object.entries(vorlagenStile)) {
    css += '.dokument ' + tag + '{' + vorlageZuCss(wie) + '}';
  }
  blatt.textContent = css;
  Speicher.schreib('vorlagenstile', vorlagenStile);
}

/* Eine Vorlage als Stilangaben. Steht sie auch in der Vorschau des
   Dialogs, muss beides dieselbe Rechnung nehmen — sonst zeigte die
   Vorschau etwas anderes, als hinterher im Blatt steht. */
function vorlageZuCss(wie) {
  let css = 'font-size:' + wie.groesse + 'pt;'
          + 'font-weight:' + (wie.fett ? '700' : '400') + ';'
          + 'color:' + wie.farbe + ';'
          + 'margin-bottom:' + wie.abstand + 'mm;';
  if (wie.schrift) css += 'font-family:"' + wie.schrift.replace(/"/g, '') + '";';
  if (wie.kursiv) css += 'font-style:italic;';
  if (wie.ausrichtung) css += 'text-align:' + wie.ausrichtung + ';';
  if (wie.zeilen) css += 'line-height:' + wie.zeilen + ';';
  if (wie.abstandVor) css += 'margin-top:' + wie.abstandVor + 'mm;';
  if (wie.einzug) css += 'text-indent:' + wie.einzug + 'mm;';
  return css;
}

/* ------------------------------------------------------------
   Formatvorlagen anlegen und ändern

   Vorher gab es nur Ändern, und auch das nur an vier Stellschrauben:
   Größe, Schriftschnitt, Farbe, Abstand danach. Eine EIGENE Vorlage
   anzulegen ging gar nicht — wer für seine Briefe eine „Anschrift"
   brauchte, musste sie in jedem Absatz von Hand nachbauen.

   Der Dialog ist der aus WPS Writer, ohne die Griffe, die es hier nicht
   gibt: „Formatvorlagentyp" stünde auf „Absatz" und ließe sich nicht
   ändern (Zeichenvorlagen kennt das Programm nicht), und „Vorlage für den
   folgenden Absatz" verlangte, dass die Eingabetaste die Vorlage wechselt
   — auch das gibt es nicht. Ein Klappfeld mit einem Eintrag ist kein
   Angebot, sondern eine Attrappe.

   Was es dafür gibt: eine Vorschau, die sich beim Tippen mitändert. Sie
   rechnet mit derselben Funktion wie das Blatt (vorlageZuCss) — sonst
   zeigte sie etwas anderes, als hinterher dasteht.
   ------------------------------------------------------------ */

/* Die Ausrichtung steht als vier Tasten da, nicht als Klappfeld — der
   Zeilenabstand als Klappfeld, weil „eineinhalb" kein Zeichen hat, das
   jeder auf Anhieb liest. */
const VORLAGE_ZEILEN = [
  ['0', 'wie das Blatt'], ['1.15', 'einfach'], ['1.6', 'eineinhalb'], ['2.1', 'doppelt'],
];

const inGrenzen = (wert, klein, gross, ersatz) => {
  const z = parseFloat(wert);
  return Number.isFinite(z) ? Math.max(klein, Math.min(gross, z)) : ersatz;
};

/* Die Vorschau: ein grauer Absatz davor, die Probe, ein grauer danach.
   Die grauen zeigen, wie die Abstände wirken — eine Probe allein steht im
   Nichts, und Abstand sieht man nur zu etwas. */
function vorlagenschauBauen() {
  const kiste = document.createElement('div');
  kiste.className = 'vorlagenschau';

  const grau = (text) => {
    const p = document.createElement('p');
    p.className = 'vorlagenschau__grau';
    p.textContent = text;
    return p;
  };

  const probe = document.createElement('p');
  probe.className = 'vorlagenschau__probe';
  probe.textContent = 'Beispieltext Beispieltext Beispieltext Beispieltext '
                    + 'Beispieltext Beispieltext Beispieltext Beispieltext '
                    + 'Beispieltext Beispieltext Beispieltext Beispieltext';

  kiste.append(grau('Vorhergehender Absatz Vorhergehender Absatz Vorhergehender Absatz'),
               probe,
               grau('Folgender Absatz Folgender Absatz Folgender Absatz'));
  return { kiste, probe };
}

/* Was in den Feldern steht, als Vorlage. */
function werteZuVorlage(werte, alt) {
  const wie = Object.assign({}, VORLAGE_ZUSATZ, alt || {});
  if (werte.name !== undefined) {
    wie.name = String(werte.name).trim().slice(0, 40) || wie.name || 'Formatvorlage';
  }
  wie.groesse    = inGrenzen(werte.groesse, 6, 72, wie.groesse);
  wie.fett       = werte.schnitt === 'fett' || werte.schnitt === 'fettkursiv';
  wie.kursiv     = werte.schnitt === 'kursiv' || werte.schnitt === 'fettkursiv';
  wie.farbe      = werte.farbe || wie.farbe;
  wie.schrift    = werte.schrift || '';
  wie.ausrichtung = werte.ausrichtung || '';
  wie.zeilen     = parseFloat(werte.zeilen) || 0;
  wie.abstandVor = inGrenzen(werte.abstandVor, 0, 40, 0);
  wie.abstand    = inGrenzen(werte.abstand, 0, 40, 0);
  wie.einzug     = inGrenzen(werte.einzug, 0, 60, 0);
  return wie;
}

/* ------------------------------------------------------------
   Das Formular

   Erst stand hier eine Zeile je Griff: elf Beschriftungen links, elf
   Felder rechts, jedes so breit wie das Fenster. Das ist viel Platz für
   wenig — und es liest sich als Liste, obwohl es Gruppen sind.

   WPS Writer legt dieselben Griffe in ZWEI LEISTEN: oben, was die Schrift
   angeht (Schriftart, Größe, fett, kursiv, Farbe), darunter, was den
   Absatz angeht (Ausrichtung, Zeilenabstand, Abstände, Einzug). Das ist
   nicht nur kürzer, sondern richtiger sortiert: Was zusammen wirkt, steht
   zusammen, und man sieht es auf einen Blick statt es zu lesen.

   Die kleinen Zahlenfelder tragen ihre Beschriftung darüber und nicht
   daneben — als Zeichen allein („⇕ 2,5") wüsste niemand, ob das der
   Abstand davor oder danach ist.
   ------------------------------------------------------------ */
function vorlageFormBauen(start, mitName, basisAnfang) {
  const block = document.createElement('div');
  block.className = 'vorlageform';
  const feldChen = {};

  const ueberschrift = (text) => {
    const p = document.createElement('p');
    p.className = 'vorlageform__gruppe';
    p.textContent = text;
    block.appendChild(p);
  };

  const zeile = (name, el) => {
    const l = document.createElement('label');
    l.className = 'vorlageform__zeile';
    const wort = document.createElement('span');
    wort.textContent = name;
    l.append(wort, el);
    block.appendChild(l);
  };

  const leiste = () => {
    const l = document.createElement('div');
    l.className = 'vorlageform__leiste';
    block.appendChild(l);
    return l;
  };

  const teiler = (wo) => {
    const s = document.createElement('span');
    s.className = 'vorlageform__teiler';
    wo.appendChild(s);
  };

  const klappe = (schluessel, eintraege, wert, titel, klasse) => {
    const w = document.createElement('select');
    w.className = 'vorlageform__wahl' + (klasse ? ' ' + klasse : '');
    w.title = titel;
    w.setAttribute('aria-label', titel);
    for (const [k, n] of eintraege) {
      const o = document.createElement('option');
      o.value = String(k); o.textContent = String(n);
      w.appendChild(o);
    }
    w.value = String(wert);
    feldChen[schluessel] = w;
    return w;
  };

  /* Ein Schalter, der an oder aus ist — fett, kursiv, die vier
     Ausrichtungen. Sein Zustand steht in „dataset.an", damit ihn dieselbe
     Stelle liest, die auch die Klappfelder liest. */
  const schalter = (schluessel, zeichen, titel, an, klasse) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'vorlageform__knopf' + (klasse ? ' ' + klasse : '');
    k.title = titel;
    k.setAttribute('aria-label', titel);
    k.dataset.an = an ? 'ja' : 'nein';
    k.classList.toggle('vorlageform__knopf--an', !!an);
    if (SYMBOLE[zeichen]) k.appendChild(symbol(zeichen));
    else k.appendChild(document.createTextNode(zeichen));
    k.addEventListener('mousedown', (e) => e.preventDefault());
    feldChen[schluessel] = k;
    return k;
  };

  const zahl = (schluessel, name, wert, gross) => {
    const kiste = document.createElement('label');
    kiste.className = 'vorlageform__zahl';
    const wort = document.createElement('span');
    wort.textContent = name;
    const e = document.createElement('input');
    e.type = 'number';
    e.step = '0.5';
    e.min = '0';
    e.max = String(gross);
    e.value = wert;
    e.title = name + ' (mm)';
    kiste.append(wort, e);
    feldChen[schluessel] = e;
    return kiste;
  };

  /* ---- Eigenschaften ---- */
  if (mitName) {
    ueberschrift('Eigenschaften');
    const name = document.createElement('input');
    name.type = 'text';
    name.value = start.name;
    feldChen.name = name;
    zeile('Name', name);
    zeile('Baut auf', klappe('basis',
      Object.entries(vorlagenStile).map(([tag, wie]) => [tag, wie.name]),
      basisAnfang, 'Worauf die Vorlage aufbaut', 'vorlageform__wahl--voll'));
  }

  /* ---- Formatierung: erst die Schrift ---- */
  ueberschrift('Formatierung');
  const oben = leiste();
  const schriften = (alleSchriften && alleSchriften.length ? alleSchriften : SCHRIFTEN);
  oben.appendChild(klappe('schrift',
    [['', 'wie das Blatt']].concat(schriften.map((s) => [s, s])),
    start.schrift || '', 'Schriftart', 'vorlageform__wahl--breit'));
  oben.appendChild(klappe('groesse', GROESSEN.map((g) => [g, g]),
    start.groesse, 'Größe in Punkt', 'vorlageform__wahl--eng'));
  oben.appendChild(schalter('fett', 'F', 'Fett', start.fett, 'vorlageform__knopf--fett'));
  oben.appendChild(schalter('kursiv', 'K', 'Kursiv', start.kursiv, 'vorlageform__knopf--kursiv'));
  teiler(oben);
  const farbe = document.createElement('input');
  farbe.type = 'color';
  farbe.className = 'vorlageform__farbe';
  farbe.value = start.farbe;
  farbe.title = 'Schriftfarbe';
  feldChen.farbe = farbe;
  oben.appendChild(farbe);

  /* ---- und dann der Absatz ---- */
  const unten = leiste();
  const RICHTUNGEN = [['', 'links', 'Wie das Blatt (linksbündig)'],
                      ['left', 'links', 'Linksbündig'],
                      ['center', 'mitte', 'Zentriert'],
                      ['right', 'rechts', 'Rechtsbündig'],
                      ['justify', 'block', 'Blocksatz']];
  /* „wie das Blatt" ist keine fünfte Taste, sondern der Zustand, in dem
     keine der vier gedrückt ist — sonst müsste man raten, was der
     Unterschied zwischen „wie das Blatt" und „linksbündig" ist. */
  for (const [wert, zeichen, titel] of RICHTUNGEN.slice(1)) {
    const k = schalter('richtung_' + wert, zeichen, titel, start.ausrichtung === wert);
    k.dataset.wert = wert;
    k.classList.add('vorlageform__knopf--richtung');
    unten.appendChild(k);
  }
  teiler(unten);
  unten.appendChild(klappe('zeilen', VORLAGE_ZEILEN, String(start.zeilen || 0),
    'Zeilenabstand', 'vorlageform__wahl--eng'));
  teiler(unten);
  unten.appendChild(zahl('abstandVor', 'Abstand davor', start.abstandVor || 0, 40));
  unten.appendChild(zahl('abstand', 'danach', start.abstand, 40));
  teiler(unten);
  unten.appendChild(zahl('einzug', 'Einzug 1. Zeile', start.einzug || 0, 60));

  const { kiste, probe } = vorlagenschauBauen();
  block.appendChild(kiste);

  /* Was in den Griffen steht — in derselben Form, die „werteZuVorlage"
     erwartet. So bleibt die Umrechnung an einer Stelle. */
  const lesen = () => {
    let richtung = '';
    for (const [schluessel, el] of Object.entries(feldChen)) {
      if (schluessel.startsWith('richtung_') && el.dataset.an === 'ja') richtung = el.dataset.wert;
    }
    return {
      name: feldChen.name ? feldChen.name.value : undefined,
      basis: feldChen.basis ? feldChen.basis.value : undefined,
      schrift: feldChen.schrift.value,
      groesse: feldChen.groesse.value,
      schnitt: (feldChen.fett.dataset.an === 'ja')
        ? (feldChen.kursiv.dataset.an === 'ja' ? 'fettkursiv' : 'fett')
        : (feldChen.kursiv.dataset.an === 'ja' ? 'kursiv' : 'normal'),
      farbe: feldChen.farbe.value,
      ausrichtung: richtung,
      zeilen: feldChen.zeilen.value,
      abstandVor: feldChen.abstandVor.value,
      abstand: feldChen.abstand.value,
      einzug: feldChen.einzug.value,
    };
  };

  /* Die Griffe aus einer Vorlage füllen — für „Baut auf". */
  const fuellen = (wie) => {
    const voll = Object.assign({}, VORLAGE_ZUSATZ, wie);
    feldChen.schrift.value = voll.schrift || '';
    feldChen.groesse.value = String(voll.groesse);
    if (!GROESSEN.includes(voll.groesse)) feldChen.groesse.value = String(GROESSEN[0]);
    setzeSchalter(feldChen.fett, voll.fett);
    setzeSchalter(feldChen.kursiv, voll.kursiv);
    feldChen.farbe.value = voll.farbe;
    for (const [schluessel, el] of Object.entries(feldChen)) {
      if (schluessel.startsWith('richtung_')) {
        setzeSchalter(el, el.dataset.wert === (voll.ausrichtung || ''));
      }
    }
    feldChen.zeilen.value = String(voll.zeilen || 0);
    feldChen.abstandVor.value = voll.abstandVor || 0;
    feldChen.abstand.value = voll.abstand;
    feldChen.einzug.value = voll.einzug || 0;
  };

  return { block, probe, feldChen, lesen, fuellen };
}

function setzeSchalter(k, an) {
  k.dataset.an = an ? 'ja' : 'nein';
  k.classList.toggle('vorlageform__knopf--an', !!an);
}

/* Der gemeinsame Dialog. „basisAnfang" bestimmt, ob oben Name und
   „Baut auf" stehen — die braucht nur das Anlegen. */
function vorlageDialog(titel, start, knopfName, beiOk, basisAnfang) {
  const form = vorlageFormBauen(start, !!basisAnfang, basisAnfang);
  const zeigen = () => {
    form.probe.style.cssText = vorlageZuCss(werteZuVorlage(form.lesen(), start));
  };
  zeigen();

  /* Die Schalter melden sich nicht von selbst — sie sind Knöpfe, keine
     Eingabefelder. Also hier verdrahtet, an einer Stelle für alle. */
  for (const [schluessel, el] of Object.entries(form.feldChen)) {
    if (el.tagName === 'BUTTON') {
      el.addEventListener('click', () => {
        if (schluessel.startsWith('richtung_')) {
          /* Vier Tasten, von denen höchstens eine gedrückt ist. Noch
             einmal auf die gedrückte heißt „wie das Blatt". */
          const anVorher = el.dataset.an === 'ja';
          for (const [s2, e2] of Object.entries(form.feldChen)) {
            if (s2.startsWith('richtung_')) setzeSchalter(e2, false);
          }
          setzeSchalter(el, !anVorher);
        } else {
          setzeSchalter(el, el.dataset.an !== 'ja');
        }
        zeigen();
      });
      continue;
    }
    el.addEventListener('change', () => {
      /* Wer „Baut auf" umstellt, will die Werte von dort sehen — sonst
         hieße „baut auf Überschrift 1" nur, dass ein Name dasteht. */
      if (schluessel === 'basis' && vorlagenStile[el.value]) form.fuellen(vorlagenStile[el.value]);
      zeigen();
    });
    el.addEventListener('input', zeigen);
  }

  /* „breit": Die zweite Leiste trägt vier Ausrichtungen, den
     Zeilenabstand und drei Zahlenfelder. In 520 Bildpunkten bricht sie
     um, und dann steht „Einzug 1. Zeile" allein in einer dritten Zeile —
     was zusammengehört, sähe aus, als gehörte es nicht dazu. */
  fenster(titel, [{ art: 'knoten', knoten: form.block }],
    () => beiOk(werteZuVorlage(form.lesen(), start)),
    knopfName, true);
}

/* Ein Name, den es noch nicht gibt.
 *
 * Zwei Vorlagen „Anschrift" nebeneinander sind im Katalog, im Klappfeld
 * und in der Verwaltung nicht auseinanderzuhalten — man wählt eine und
 * bekommt vielleicht die andere. Also hängt der zweite eine Zahl an,
 * still: Wer den Namen schon vergeben hat, weiß es meistens nicht mehr,
 * und eine Fehlermeldung stünde zwischen ihm und seiner Arbeit.
 */
function freierName(wunsch) {
  const namen = new Set(Object.values(vorlagenStile).map((wie) => wie.name));
  if (!namen.has(wunsch)) return wunsch;
  for (let n = 2; n < 100; n++) {
    if (!namen.has(wunsch + ' ' + n)) return wunsch + ' ' + n;
  }
  return wunsch;
}

/* Der nächste freie Platz für eine eigene Vorlage. Sie hängt als Klasse
   am Absatz: <p class="eigen-3">. */
function eigenerSchluessel() {
  for (let n = 1; n < 1000; n++) {
    if (!vorlagenStile['p.eigen-' + n]) return 'p.eigen-' + n;
  }
  return null;
}

B.vorlageNeu = () => {
  const schluessel = eigenerSchluessel();
  if (!schluessel) { melde('Mehr eigene Vorlagen gehen nicht.'); return; }

  /* Sie fängt bei dem an, worin der Zeiger gerade steht — das ist
     meistens das, was man abwandeln will. */
  const jetzt = vorlageSchluesselAnStelle();
  const basis = vorlagenStile[jetzt] ? jetzt : 'p';
  const start = Object.assign({}, VORLAGE_ZUSATZ, vorlagenStile[basis], {
    name: 'Formatvorlage ' + schluessel.replace('p.eigen-', ''),
    eigen: true,
  });

  auswahlMerken();
  vorlageDialog('Neue Formatvorlage', start, 'Anlegen', (wie) => {
    wie.eigen = true;
    wie.name = freierName(wie.name);
    vorlagenStile[schluessel] = wie;
    vorlagenAnwenden();
    werkzeugeBauen();
    registerBauen();
    menueBauen();
    /* Und gleich anwenden: Wer eine Vorlage anlegt, während der Zeiger in
       einem Absatz steht, meint diesen Absatz. */
    auswahlZurueck();
    vorlageSetzen('p', schluessel.slice('p.'.length));
    melde('Vorlage „' + wie.name + '" angelegt und auf diesen Absatz gesetzt.');
  }, basis);
};

/* In welcher Vorlage steht der Zeiger? Der Schlüssel, wie ihn
   „vorlagenStile" führt — also mit Klasse, wenn eine dranhängt. */
function vorlageSchluesselAnStelle() {
  let k = window.getSelection().anchorNode;
  while (k && k !== feld) {
    if (k.nodeType === Node.ELEMENT_NODE && k.tagName && k.parentNode === feld) {
      const grund = k.tagName.toLowerCase();
      for (const klasse of k.classList) {
        if (vorlagenStile[grund + '.' + klasse]) return grund + '.' + klasse;
      }
      return vorlagenStile[grund] ? grund : 'p';
    }
    k = k.parentNode;
  }
  return 'p';
}

B.vorlagenVerwalten = () => {
  const tags = Object.keys(vorlagenStile);
  fenster('Formatvorlagen verwalten', [
    { art: 'satz', text: 'Eine Vorlage ändern gilt für jeden Absatz, der sie trägt.' },
    { schluessel: 'tag', name: 'Vorlage', art: 'auswahl',
      werte: tags.map((t) => [t, vorlagenStile[t].name
        + (vorlagenStile[t].eigen ? ' (eigene)' : '')]),
      wert: vorlageSchluesselAnStelle() },
  ], (werte) => vorlageBearbeiten(werte.tag), 'Bearbeiten');
};

function vorlageBearbeiten(tag) {
  const wie = vorlagenStile[tag];
  if (!wie) return;
  const start = Object.assign({}, VORLAGE_ZUSATZ, wie);
  vorlageDialog('Vorlage: ' + wie.name, start, 'Übernehmen', (neu) => {
    Object.assign(wie, neu);
    vorlagenAnwenden();
    werkzeugeBauen();
    registerBauen();
    melde('Vorlage „' + wie.name + '" geändert — überall, wo sie steht.');
  });
}

/* Eine eigene Vorlage wieder loswerden. Die mitgelieferten nicht: „Titel"
   oder „Überschrift 1" zu löschen hieße, ein Dokument zu hinterlassen, in
   dem Absätze auf etwas zeigen, das es nicht mehr gibt. */
B.vorlageLoeschen = () => {
  const eigene = Object.entries(vorlagenStile).filter(([, wie]) => wie.eigen);
  if (!eigene.length) {
    melde('Es gibt keine eigene Vorlage — gelöscht werden nur die selbst angelegten.');
    return;
  }
  fenster('Formatvorlage löschen', [
    { art: 'satz', text: 'Absätze, die sie tragen, werden wieder Fließtext. '
                       + 'Der Text bleibt, wie er ist.' },
    { schluessel: 'tag', name: 'Vorlage', art: 'auswahl',
      werte: eigene.map(([tag, wie]) => [tag, wie.name]) },
  ], (werte) => {
    const wie = vorlagenStile[werte.tag];
    if (!wie) return;
    const klasse = werte.tag.split('.')[1];
    for (const el of feld.querySelectorAll('.' + klasse)) {
      el.classList.remove(klasse);
      /* Und das leere Attribut gleich mit. „classList.remove" lässt
         class="" stehen, und das wandert in die gespeicherte Datei —
         eine Spur von etwas, das es nicht mehr gibt. */
      if (!el.classList.length) el.removeAttribute('class');
    }
    delete vorlagenStile[werte.tag];
    vorlagenAnwenden();
    werkzeugeBauen();
    registerBauen();
    geaendertMelden();
    melde('Vorlage „' + wie.name + '" gelöscht.');
  }, 'Löschen');
};

B.vorlagenZurueck = () => {
  vorlagenStile = JSON.parse(JSON.stringify(VORLAGEN_STANDARD));
  vorlagenAnwenden();
  melde('Alle Vorlagen auf den Ausgangszustand zurückgesetzt.');
};

/* ============================================================
   Layout-Modi

   Drei Arten, dasselbe Dokument anzusehen: als Blatt (so kommt es aufs
   Papier), zwei Blätter nebeneinander (zum Blättern in Langem) und als
   fortlaufende Seite ohne Rand (zum Schreiben, wenn das Papier noch nicht
   zählt).
   ============================================================ */
let layout = Speicher.lies('layout', 'blatt');

function layoutAnwenden() {
  const flaeche = $('arbeitsflaeche');
  flaeche.classList.toggle('arbeitsflaeche--doppelt', layout === 'doppelt');
  $('blatt').classList.toggle('blatt--web', layout === 'web');
  Speicher.schreib('layout', layout);
  menueBauen();
}

/* statuszeileAuffrischen() mit dazu: Wird die Ansicht über das Menü
   gewechselt, muss unten rechts derselbe Knopf aufleuchten. */
const setzeLayout = (wahl) => () => {
  layout = wahl; layoutAnwenden();
  if (typeof statuszeileAuffrischen === 'function') statuszeileAuffrischen();
};

/* ============================================================
   Aus dem Start-Tab von Word
   ============================================================ */

/* ---- Schriftgrad größer und kleiner ----
   Nicht zu verwechseln mit der Ansicht: Strg++ vergrößert das ganze Blatt,
   das hier vergrößert die markierte Schrift — so wie die beiden A-Knöpfe
   in Word. */
function schriftgradAendern(richtung) {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) {
    melde('Erst den Text markieren, dessen Größe sich ändern soll.');
    return;
  }
  let knoten = auswahl.anchorNode;
  if (knoten && knoten.nodeType === Node.TEXT_NODE) knoten = knoten.parentElement;
  const jetzt = knoten ? Math.round(parseFloat(getComputedStyle(knoten).fontSize) * 72 / 96) : 12;

  /* Dieselben Stufen wie im Größenfeld — sonst landet man auf 13,7 pt und
     findet den Wert dort nicht wieder. */
  const stelle = GROESSEN.findIndex((g) => g >= jetzt);
  let neu;
  if (richtung > 0) neu = GROESSEN[Math.min(GROESSEN.length - 1, (stelle < 0 ? GROESSEN.length - 1 : stelle) + 1)];
  else neu = GROESSEN[Math.max(0, (stelle < 0 ? GROESSEN.length - 1 : stelle) - 1)];

  schriftgroesse(neu);
  if (wzGroesse) wzGroesse.value = String(neu);
  melde('Schriftgröße ' + neu + ' pt.');
}
B.schriftGroesser = () => schriftgradAendern(1);
B.schriftKleiner = () => schriftgradAendern(-1);

/* ---- Groß- und Kleinschreibung anpassen ----
   Vier Formen, wie in Word. Der markierte Text wird umgeschrieben, der
   Rest bleibt. */
const SCHREIBWEISEN = [
  ['satz', 'Wie am Satzanfang', (t) => t.toLowerCase().replace(/(^|[.!?]\s+)([a-zäöüß])/g,
                                                             (g, vor, b) => vor + b.toUpperCase())],
  ['klein', 'alles klein', (t) => t.toLowerCase()],
  ['gross', 'ALLES GROSS', (t) => t.toUpperCase()],
  ['woerter', 'Jedes Wort Groß', (t) => t.toLowerCase().replace(/(^|\s)(\S)/g,
                                                               (g, vor, b) => vor + b.toUpperCase())],
];

/* ============================================================
   VIER PUNKTE AUS DEM START-REITER

   Sie standen seit dem ersten Abgleich in doku/menue-abgleich-wps.md
   als „fehlt" — und mein eigener Bogen meldete trotzdem „0 fehlen",
   weil sie in seinem SOLL-Baum nicht vorkommen. Zwei Listen, die
   einander nicht kennen, ergeben keine Deckung, sondern einen blinden
   Fleck.
   ============================================================ */

/* ---- Eingeschlossene Zeichen ----
   Ein Buchstabe in einem Kreis, wie ⓐ. In WPS „Eingeschlossene
   Zeichen"; gebraucht fuer Nummerierungen, die im Text stehen sollen.

   Vier Formen, und — wichtiger — vier ECHTE ZEICHEN, wo es sie gibt:
   ⓐ ① ㊀ sind Unicode und ueberleben Kopieren, Speichern und Word.
   Nur wo Unicode nichts hat, wird gezeichnet. */
const RINGZEICHEN = {
  kreis: { name: 'Kreis', form: '50%',
           tabelle: { a: 'ⓐ', b: 'ⓑ', c: 'ⓒ', d: 'ⓓ', e: 'ⓔ', f: 'ⓕ', g: 'ⓖ', h: 'ⓗ',
                      i: 'ⓘ', j: 'ⓙ', k: 'ⓚ', l: 'ⓛ', m: 'ⓜ', n: 'ⓝ', o: 'ⓞ', p: 'ⓟ',
                      q: 'ⓠ', r: 'ⓡ', s: 'ⓢ', t: 'ⓣ', u: 'ⓤ', v: 'ⓥ', w: 'ⓦ', x: 'ⓧ',
                      y: 'ⓨ', z: 'ⓩ',
                      A: 'Ⓐ', B: 'Ⓑ', C: 'Ⓒ', D: 'Ⓓ', E: 'Ⓔ', F: 'Ⓕ', G: 'Ⓖ', H: 'Ⓗ',
                      I: 'Ⓘ', J: 'Ⓙ', K: 'Ⓚ', L: 'Ⓛ', M: 'Ⓜ', N: 'Ⓝ', O: 'Ⓞ', P: 'Ⓟ',
                      Q: 'Ⓠ', R: 'Ⓡ', S: 'Ⓢ', T: 'Ⓣ', U: 'Ⓤ', V: 'Ⓥ', W: 'Ⓦ', X: 'Ⓧ',
                      Y: 'Ⓨ', Z: 'Ⓩ',
                      '0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④',
                      '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨' } },
  quadrat:  { name: 'Quadrat',  form: '0',   tabelle: {} },
  raute:    { name: 'Raute',    form: '0',   tabelle: {}, gedreht: true },
  dreieck:  { name: 'Dreieck',  form: '0',   tabelle: {}, dreieck: true },
};

B.eingeschlosseneZeichen = () => {
  const auswahl = window.getSelection();
  const text = auswahl ? auswahl.toString() : '';
  if (!text || text.length > 2) {
    melde('Erst ein einzelnes Zeichen markieren — ein Buchstabe oder eine Ziffer.');
    return;
  }
  fenster('Eingeschlossene Zeichen', [
    { art: 'satz', text: 'Setzt „' + text + '" in eine Umrandung. '
                       + 'Wo es das Zeichen fertig gibt — ⓐ, ①, Ⓩ —, wird es '
                       + 'genommen: Es übersteht Kopieren, Speichern und Word.' },
    { schluessel: 'form', name: 'Form', art: 'auswahl',
      werte: Object.entries(RINGZEICHEN).map(([k, v]) => [k, v.name]), wert: 'kreis' },
  ], (werte) => {
    const art = RINGZEICHEN[werte.form] || RINGZEICHEN.kreis;
    const fertig = art.tabelle[text];
    if (fertig) {
      Dokument.einfuegen(fertig);
      melde('Eingeschlossen: ' + fertig);
      return;
    }
    const klassen = ['eingeschlossen', 'eingeschlossen--' + werte.form];
    Dokument.einfuegen('<span class="' + klassen.join(' ') + '">'
      + text.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))
      + '</span>');
    melde('Eingeschlossen: ' + art.name + '.');
  });
};

/* ---- Zeichenumriss ----
   Buchstaben, die nur aus ihrer Kontur bestehen. In WPS ein eigener
   Knopf neben der Schriftfarbe. */
B.zeichenumriss = () => {
  const auswahl = window.getSelection();
  if (!auswahl || !auswahl.rangeCount || auswahl.isCollapsed) {
    melde('Erst den Text markieren, der einen Umriss bekommen soll.');
    return;
  }
  const drin = auswahl.anchorNode && auswahl.anchorNode.parentElement
    && auswahl.anchorNode.parentElement.closest('.umriss');
  if (drin) {
    /* Zweimal derselbe Knopf nimmt ihn wieder weg — sonst muesste man
       raten, wie man ihn loswird. */
    const eltern = drin.parentNode;
    while (drin.firstChild) eltern.insertBefore(drin.firstChild, drin);
    drin.remove();
    geaendertMelden();
    melde('Umriss entfernt.');
    return;
  }
  fenster('Zeichenumriss', [
    { art: 'satz', text: 'Die Buchstaben stehen dann nur als Linie da. '
                       + 'Gut für eine Überschrift, schlecht für einen Absatz — '
                       + 'Umrisse sind schwerer zu lesen als volle Buchstaben.' },
    { schluessel: 'farbe', name: 'Farbe der Linie', art: 'color', wert: '#1F4E79' },
    { schluessel: 'staerke', name: 'Stärke (px)', art: 'number', wert: '1', schritt: '0.5' },
  ], (werte) => {
    const dick = Math.max(0.5, Math.min(4, parseFloat(werte.staerke) || 1));
    Dokument.einfuegen('<span class="umriss" style="-webkit-text-stroke:'
      + dick + 'px ' + werte.farbe + '">'
      + (window.getSelection().toString() || 'Umriss') + '</span>');
    melde('Zeichenumriss gesetzt. Derselbe Knopf nimmt ihn wieder weg.');
  });
};

/* ---- Formatpipette ----
   Nimmt eine Farbe aus dem Dokument auf und gibt sie dem markierten
   Text. NICHT dasselbe wie „Format uebertragen": Der Pinsel nimmt das
   ganze Format einer Stelle, die Pipette nur die Farbe — und die auch
   von einem Bild, wo es gar kein Format gibt. */
B.formatpipette = async () => {
  const auswahl = window.getSelection();
  if (!auswahl || auswahl.isCollapsed) {
    melde('Erst den Text markieren, der die Farbe bekommen soll.');
    return;
  }
  if (typeof EyeDropper !== 'function') {
    melde('Die Pipette gibt es in diesem Fenster nicht — die Schriftfarbe daneben tut dasselbe von Hand.');
    return;
  }
  try {
    const griff = await new EyeDropper().open();
    Dokument.befehl('foreColor', griff.sRGBHex);
    melde('Farbe ' + griff.sRGBHex.toUpperCase() + ' aufgenommen und gesetzt.');
  } catch (e) {
    melde('Abgebrochen.');
  }
};

/* ---- Die acht Wort-Extras ----
   In WPS ein eigener Block. Acht Handgriffe an Absaetzen, die man sonst
   von Hand macht — und bei einem langen Text eine halbe Stunde lang.

   Wer eine Datei aus dem Netz einfuegt, hat oft jede Zeile als eigenen
   Absatz oder umgekehrt einen Block ohne Absaetze. Das von Hand zu
   richten ist genau die Arbeit, die jemanden mit Legasthenie am
   laengsten aufhaelt. */
function absaetzeGewaehlt() {
  const drin = absaetzeInAuswahl();
  return drin.length ? drin : [...feld.querySelectorAll('p')];
}

const WORT_EXTRAS = [
  ['leereWeg', 'Leere Absätze löschen', () => {
    const weg = [...feld.querySelectorAll('p')].filter(
      (p) => !p.textContent.trim() && !p.querySelector('img, svg, table'));
    weg.forEach((p) => p.remove());
    return weg.length + (weg.length === 1 ? ' leerer Absatz entfernt.'
                                          : ' leere Absätze entfernt.');
  }],
  ['leereRein', 'Leerzeile zwischen Absätze setzen', () => {
    const alle = [...feld.querySelectorAll('p')];
    let n = 0;
    for (const p of alle) {
      if (!p.textContent.trim()) continue;
      const naechst = p.nextElementSibling;
      if (naechst && naechst.tagName === 'P' && naechst.textContent.trim()) {
        const leer = document.createElement('p');
        leer.appendChild(document.createElement('br'));
        p.after(leer);
        n++;
      }
    }
    return n + (n === 1 ? ' Leerzeile eingefügt.' : ' Leerzeilen eingefügt.');
  }],
  ['umbruchZuAbsatz', 'Zeilenumbrüche in Absätze umwandeln', () => {
    let n = 0;
    for (const p of absaetzeGewaehlt()) {
      const stuecke = p.innerHTML.split(/<br\s*\/?>/i);
      if (stuecke.length < 2) continue;
      const neu = stuecke.map((teil) => {
        const a = document.createElement('p');
        a.innerHTML = teil.trim() || '<br>';
        return a;
      });
      p.replaceWith(...neu);
      n += neu.length - 1;
    }
    return n + (n === 1 ? ' Umbruch wurde ein Absatz.'
                        : ' Umbrüche wurden Absätze.');
  }],
  ['absatzZuUmbruch', 'Absätze in Zeilenumbrüche umwandeln', () => {
    const alle = absaetzeGewaehlt().filter((p) => p.tagName === 'P');
    if (alle.length < 2) return 'Dafür braucht es mindestens zwei Absätze.';
    const erste = alle[0];
    for (const p of alle.slice(1)) {
      erste.appendChild(document.createElement('br'));
      while (p.firstChild) erste.appendChild(p.firstChild);
      p.remove();
    }
    return alle.length + ' Absätze wurden einer.';
  }],
  ['einzugRein', 'Erste Zeile um zwei Zeichen einrücken', () => {
    const alle = absaetzeGewaehlt();
    alle.forEach((p) => { p.style.textIndent = '2em'; });
    return alle.length + ' Absätze eingerückt.';
  }],
  ['einzugRaus', 'Einrückung der ersten Zeile aufheben', () => {
    const alle = absaetzeGewaehlt();
    alle.forEach((p) => { p.style.textIndent = ''; });
    return 'Einrückung bei ' + alle.length + ' Absätzen aufgehoben.';
  }],
  ['leerzeichen', 'Doppelte Leerzeichen zusammenziehen', () => {
    let n = 0;
    for (const p of absaetzeGewaehlt()) {
      const gehen = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
      let k;
      while ((k = gehen.nextNode())) {
        const neu = k.data.replace(/[ \t]{2,}/g, ' ');
        if (neu !== k.data) { n += 1; k.data = neu; }
      }
    }
    return n === 0 ? 'Keine doppelten Leerzeichen gefunden.'
                   : 'An ' + n + ' Stellen zusammengezogen.';
  }],
  ['umdrehen', 'Reihenfolge der Absätze umdrehen', () => {
    const alle = absaetzeGewaehlt();
    if (alle.length < 2) return 'Dafür braucht es mindestens zwei Absätze.';
    const nach = alle[alle.length - 1].nextSibling;
    const eltern = alle[0].parentNode;
    /* RUECKWAERTS durchgehen. Vorwaerts vor denselben Anker gesetzt
       ergibt genau die alte Reihenfolge: Der erste landet hinten, der
       zweite dahinter, und am Ende steht alles wie zuvor. Der Knopf
       meldete „3 Absätze umgedreht" und hatte nichts getan — die
       schlimmste Art Fehler, weil sie sich als Erfolg ausgibt. */
    for (const p of alle.slice().reverse()) eltern.insertBefore(p, nach);
    return alle.length + ' Absätze umgedreht.';
  }],
];

B.wortExtras = (knopf) => designTafelZeigen(knopf, 'Wort-Extras', (tafel) => {
  tafel.classList.add('designtafel--breit');
  const satz = document.createElement('p');
  satz.className = 'layouttafel__satz';
  satz.textContent = 'Ohne Markierung gilt es für das ganze Blatt, mit '
                   + 'Markierung nur für die markierten Absätze. '
                   + 'Strg+Z nimmt jeden Handgriff zurück.';
  tafel.appendChild(satz);

  for (const [, name, tun] of WORT_EXTRAS) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'designtafel__zeile';
    k.textContent = name;
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      let meldung;
      try { meldung = tun(); } catch (e) { meldung = 'Das ging nicht: ' + e.message; }
      geaendertMelden();
      designTafelWeg();
      melde(meldung);
    });
    tafel.appendChild(k);
  }
});

B.schreibweise = () => {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) {
    melde('Erst den Text markieren, dessen Schreibweise sich ändern soll.');
    return;
  }
  auswahlMerken();
  fenster('Groß- und Kleinschreibung', [
    { schluessel: 'art', name: 'Umstellen auf', art: 'auswahl',
      werte: SCHREIBWEISEN.map(([kuerzel, name]) => [kuerzel, name]) },
  ], (werte) => {
    const regel = SCHREIBWEISEN.find(([kuerzel]) => kuerzel === werte.art);
    if (!regel) return;
    auswahlZurueck();
    const jetzt = window.getSelection();
    if (!jetzt.rangeCount || jetzt.isCollapsed) return;
    const text = jetzt.toString();
    document.execCommand('insertText', false, regel[2](text));
    melde('Schreibweise geändert.');
  }, 'Umstellen');
};

/* ---- Unterstreichen mit Linienstil ---- */
let unterstrichFarbe = '#111417';

const UNTERSTRICHE = [
  ['solid', 'durchgezogen'], ['double', 'doppelt'],
  ['dotted', 'gepunktet'], ['dashed', 'gestrichelt'], ['wavy', 'gewellt'],
];

/* ============================================================
   DIE KLAPPEN AM GETEILTEN KNOPF

   In WPS traegt das U einen Pfeil, und dahinter liegen die Linien — als
   Striche, nicht als Namen. Er hat geschrieben: „Die Strichvorlagen aus
   dem Bild fehlen aktuell." Sie lagen hinter einem zweiten U-Knopf
   daneben, und ein Klappfeld mit den Woertern „durchgezogen, doppelt,
   gepunktet" ist nicht dasselbe wie fuenf gezeichnete Striche.

   Wer wissen will, wie „gewellt" aussieht, will es sehen.
   ============================================================ */
function strichbild(art) {
  const zeile = document.createElement('span');
  zeile.className = 'strichprobe';
  zeile.style.borderBottom = '2px ' + art + ' currentColor';
  return zeile;
}

/* Der Pfeil unten rechts an der Gruppe.

   In seinem Bild hat die WPS-Zeile genau zehn Zeichen, und mehr passen
   auch nicht hinein, ohne dass sie zur Suchaufgabe wird. „Eingeschlossene
   Zeichen" und die „Formatpipette" stehen im SOLL trotzdem unter
   Schriftart — sie gehoeren also hierher, nur nicht in die Reihe.

   Dafuer ist der Pfeil da: In WPS oeffnet er die vollen Einstellungen
   der Gruppe. Bei mir zeigt er, was die Reihe nicht fasst, statt es zu
   verstecken. Ein Befehl, den man nicht findet, ist nicht gebaut. */
B.schriftartMehr = (knopf) => {
  designTafelZeigen(knopf, 'Schriftart', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [bild, name, tun] of [
      ['texteffekt', 'Texteffekte…', (k) => B.effekt(k)],
      ['eingeschlossen', 'Eingeschlossene Zeichen', () => B.eingeschlosseneZeichen()],
      ['umriss', 'Zeichenumriss', () => B.zeichenumriss()],
      ['unterart', 'Unterstreichungsart…', () => B.unterstrichArt()],
      ['pinsel', 'Formatpipette', () => B.formatpipette()],
      ['radierer', 'Formatierung löschen', () => B.schlicht()],
    ]) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      if (SYMBOLE[bild]) k.appendChild(symbol(bild));
      const wort = document.createElement('span');
      wort.textContent = name;
      k.appendChild(wort);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => { designTafelWeg(); tun(); });
      tafel.appendChild(k);
    }
  });
};

B.unterstrichKlappe = (knopf) => {
  auswahlMerken();
  designTafelZeigen(knopf, 'Unterstreichen', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [art, name] of UNTERSTRICHE) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      k.appendChild(strichbild(art));
      const wort = document.createElement('span');
      wort.textContent = name;
      k.appendChild(wort);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        unterstrichSetzen(art, unterstrichFarbe);
      });
      tafel.appendChild(k);
    }
    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    const weg = document.createElement('button');
    weg.type = 'button';
    weg.className = 'designtafel__zeile richtungszeile';
    weg.appendChild(symbol('radierer'));
    const w1 = document.createElement('span');
    w1.textContent = 'Unterstreichung entfernen';
    weg.appendChild(w1);
    weg.addEventListener('mousedown', (e) => e.preventDefault());
    weg.addEventListener('click', () => { designTafelWeg(); auswahlZurueck(); B.unter(); });
    tafel.appendChild(weg);

    const mehr = document.createElement('button');
    mehr.type = 'button';
    mehr.className = 'layouttafel__weiter';
    mehr.textContent = 'Farbe und Linie wählen…';
    mehr.addEventListener('click', () => { designTafelWeg(); B.unterstrichArt(); });
    tafel.appendChild(mehr);
  });
};

/* Die vier Schreibweisen aus WPS als Klappe statt als Fenster. Er hat
   dazu geschrieben: „Icon ohne Funktion, Linksklick ist nicht vorhanden
   mit der Maus." Ein Fenster, das erst nach einem markierten Text fragt,
   sieht von aussen aus wie ein Knopf, der nichts tut. */
B.schreibweiseKlappe = (knopf) => {
  designTafelZeigen(knopf, 'Groß- und Kleinschreibung', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [kuerzel, name, wandeln] of SCHREIBWEISEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      const probe = document.createElement('span');
      probe.className = 'schreibprobe';
      probe.textContent = wandeln('Ein Satz als Probe.');
      k.appendChild(probe);
      const wort = document.createElement('span');
      wort.textContent = name;
      k.appendChild(wort);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        schreibweiseSetzen(kuerzel);
      });
      tafel.appendChild(k);
    }
  });
};

/* Beides einmal als Funktion, damit Klappe und Fenster dasselbe tun und
   nicht zwei Fassungen auseinanderlaufen. */
function unterstrichSetzen(art, farbe) {
  auswahlZurueck();
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) {
    melde('Erst den Text markieren, der unterstrichen werden soll.');
    return;
  }
  unterstrichFarbe = farbe || unterstrichFarbe;
  /* execCommand kennt nur „unterstrichen ja/nein". Für einen Linienstil
     braucht es ein eigenes Element um die Markierung herum. */
  const huelle = document.createElement('span');
  huelle.style.textDecoration = 'underline ' + art + ' ' + unterstrichFarbe;
  try {
    auswahl.getRangeAt(0).surroundContents(huelle);
    geaendertMelden();
    melde('Unterstrichen: '
          + (UNTERSTRICHE.find((u) => u[0] === art) || [, art])[1] + '.');
  } catch (e) {
    /* Reicht die Markierung über mehrere Absätze, lässt sie sich nicht in
       ein Element fassen. Dann tut es die schlichte Unterstreichung. */
    Dokument.befehl('underline');
    melde('Über mehrere Absätze geht nur die einfache Linie.');
  }
}

function schreibweiseSetzen(kuerzel) {
  const regel = SCHREIBWEISEN.find(([k]) => k === kuerzel);
  if (!regel) return;
  const jetzt = window.getSelection();
  if (!jetzt.rangeCount || jetzt.isCollapsed) {
    melde('Erst den Text markieren, dessen Schreibweise sich ändern soll.');
    return;
  }
  document.execCommand('insertText', false, regel[2](jetzt.toString()));
  geaendertMelden();
  melde('Schreibweise: ' + regel[1] + '.');
}

B.unterstrichArt = () => {
  auswahlMerken();
  fenster('Unterstreichen', [
    { schluessel: 'art', name: 'Linie', art: 'auswahl', werte: UNTERSTRICHE },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#111417' },
  ], (werte) => unterstrichSetzen(werte.art, werte.farbe), 'Anwenden');
};

/* ---- Liste mit mehreren Ebenen ----
   Tiefer heißt: eine Liste in der Liste. Genau das macht Word, wenn man in
   einer Aufzählung die Tabulatortaste drückt. */
B.ebeneTiefer = () => {
  Dokument.befehl('indent');
  melde('Eine Ebene tiefer.');
};
B.ebeneHoeher = () => {
  Dokument.befehl('outdent');
  melde('Eine Ebene höher.');
};

/* ---- Sortieren ---- */
B.sortieren = () => {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) { melde('Erst markieren, was sortiert werden soll.'); return; }
  const bereich = auswahl.getRangeAt(0);

  /* Eine Liste sortiert ihre Punkte, sonst werden die markierten Absätze
     sortiert. Beides ist dasselbe Bedürfnis: Zeilen in eine Ordnung bringen. */
  let liste = bereich.commonAncestorContainer;
  while (liste && liste !== feld && !(liste.tagName === 'UL' || liste.tagName === 'OL')) {
    liste = liste.parentNode;
  }

  auswahlMerken();
  fenster('Sortieren', [
    { art: 'satz', text: liste && liste !== feld
        ? 'Die Punkte dieser Liste werden sortiert.'
        : 'Die markierten Absätze werden sortiert.' },
    { schluessel: 'richtung', name: 'Reihenfolge', art: 'auswahl',
      werte: [['auf', 'A → Z'], ['ab', 'Z → A']] },
  ], (werte) => {
    const rueckwaerts = werte.richtung === 'ab';
    const ordnen = (a, b) => (rueckwaerts ? -1 : 1)
      * a.textContent.trim().localeCompare(b.textContent.trim(), 'de', { numeric: true });

    if (liste && liste !== feld) {
      const punkte = [...liste.children].filter((k) => k.tagName === 'LI');
      punkte.sort(ordnen).forEach((k) => liste.appendChild(k));
      geaendertMelden();
      melde(punkte.length + ' Punkte sortiert.');
      return;
    }

    const betroffen = [...feld.children].filter((el) => bereich.intersectsNode(el));
    if (betroffen.length < 2) { melde('Dafür müssen mindestens zwei Absätze markiert sein.'); return; }
    const danach = betroffen[betroffen.length - 1].nextSibling;
    betroffen.sort(ordnen).forEach((el) => feld.insertBefore(el, danach));
    geaendertMelden();
    melde(betroffen.length + ' Absätze sortiert.');
  }, 'Sortieren');
};

/* ---- Schattierung und Rahmenlinien ----
   In Word sitzt beides nebeneinander in der Absatz-Gruppe: eine Hinterlegung
   und ein Rahmen um den Absatz. */
/* Die alte Fassung stand hier — ein Farbfeld ohne Vorschau. Sie wurde
   von der spaeteren Zuweisung ohnehin ueberschrieben, still: die
   fuenfte Namensdopplung diese Woche. Jetzt steht der Befehl nur noch
   einmal, oben bei B.absatzRahmen. */

/* „Hier wird eine Funktion fehlerhaft ausgefuehrt mit einer falschen
   Funktion. Icon ist als Funktion nicht zu erkennen. Stop hier geraet
   was mit den Funktionen durcheinander."

   Dahinter lag ein eigenes kleines Fenster namens „Rahmenlinien" — ein
   Klappfeld mit fuenf Woertern, keine Vorschau, und ein zweiter Weg
   neben dem, den es schon gab. In WPS oeffnet der Absatzrahmen dasselbe
   Fenster wie der Seitenrand: „Rahmen und Schattierung", nur auf der
   Karte „Rahmen" statt auf „Seitenrand".

   Also fuehrt er jetzt dorthin. Ein Fenster, drei Karten, eine
   Vorschau, in die man hineinklickt — und nicht zwei Fenster, die
   dasselbe halb koennen. */
/* Die Klappe aus seinem Bild — zwoelf Zeilen in vier Gruppen:

     Rahmenlinie unten · oben · links · rechts
     Kein Rahmen · Alle Rahmenlinien · aussen · innen
     Innere waagerechte · innere senkrechte Rahmenlinie
     Rahmen und Schattierung…

   Ich hatte den Knopf zuerst geradewegs auf das Fenster gelegt. Das
   ist eine Stufe zu weit: Wer nur einen Strich unter den Absatz will,
   soll ihn in einem Klick bekommen — dafuer steht die Klappe da. Das
   Fenster ist der letzte Punkt darin, nicht der erste Schritt. */
/* Je Zeile ein eigenes Zeichen. Elf gleiche Kaestchen in einer Liste
   sind keine Liste — er hat es gemeldet: „die Symbole sind nicht lesbar
   in der Liste." Der graue Kasten ist ueberall gleich, die betonte
   Kante sagt, welche gemeint ist. */
const RAHMENLINIEN = [
  ['kanteUnten',  'Rahmenlinie unten',  ['unten']],
  ['kanteOben',   'Rahmenlinie oben',   ['oben']],
  ['kanteLinks',  'Rahmenlinie links',  ['links']],
  ['kanteRechts', 'Rahmenlinie rechts', ['rechts']],
  ['-'],
  ['kanteKeine',  'Kein Rahmen',        []],
  ['kanteAlle',   'Alle Rahmenlinien',  ['oben', 'unten', 'links', 'rechts']],
  ['kanteAussen', 'Rahmenlinien außen', ['oben', 'unten', 'links', 'rechts']],
  ['kanteInnen',  'Rahmenlinie innen',  'innen'],
  ['-'],
  ['kanteWaage',  'Innere horizontale Rahmenlinie', 'waagerecht'],
  ['kanteSenk',   'Innere vertikale Rahmenlinie',   'senkrecht'],
];

function absatzRahmenSetzen(kanten) {
  const ziele = absaetzeInAuswahl();
  if (!ziele.length) { melde('Dafür muss der Zeiger in einem Absatz stehen.'); return; }
  const linie = absatzrahmen.breite + 'px ' + absatzrahmen.art + ' ' + absatzrahmen.farbe;
  for (const a of ziele) {
    for (const [kante, seite] of [['oben', 'Top'], ['unten', 'Bottom'],
                                  ['links', 'Left'], ['rechts', 'Right']]) {
      a.style['border' + seite] = kanten.includes(kante) ? linie : '';
    }
    a.style.padding = kanten.length ? '2mm 3mm' : '';
  }
  geaendertMelden();
  melde(kanten.length
    ? (ziele.length === 1 ? 'Rahmen gesetzt.' : 'Rahmen um ' + ziele.length + ' Absätze.')
    : 'Rahmen entfernt.');
}

/* Die „inneren" Linien meinen die Kanten ZWISCHEN den markierten
   Absaetzen: der erste bekommt keine oben, der letzte keine unten.
   Bei einem einzigen Absatz gibt es nichts dazwischen — dann sagt es
   das, statt nichts zu tun. */
function absatzRahmenInnen(art) {
  const ziele = absaetzeInAuswahl();
  if (ziele.length < 2) {
    melde('Innere Linien brauchen mehrere markierte Absätze — '
        + 'zwischen einem einzigen liegt nichts.');
    return;
  }
  const linie = absatzrahmen.breite + 'px ' + absatzrahmen.art + ' ' + absatzrahmen.farbe;
  ziele.forEach((a, i) => {
    if (art === 'waagerecht' || art === 'innen') {
      a.style.borderTop = i === 0 ? '' : linie;
      a.style.borderBottom = '';
    }
    if (art === 'senkrecht' || art === 'innen') {
      /* Senkrecht zwischen Absaetzen gibt es nicht — Absaetze stehen
         untereinander. In WPS ist der Punkt fuer Tabellen da; hier sagt
         er das, statt so zu tun. */
      melde('Senkrechte Linien gibt es nur in Tabellen — Absätze stehen untereinander.');
    }
  });
  geaendertMelden();
  if (art !== 'senkrecht') melde('Linien zwischen den Absätzen gesetzt.');
}

B.absatzRahmen = (knopf) => {
  designTafelZeigen(knopf, 'Absatzrahmen', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const eintrag of RAHMENLINIEN) {
      if (eintrag[0] === '-') {
        const strichel = document.createElement('hr');
        strichel.className = 'designtafel__strich';
        tafel.appendChild(strichel);
        continue;
      }
      const [kuerzel, name, kanten] = eintrag;
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      k.appendChild(symbol(kuerzel));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        if (typeof kanten === 'string') absatzRahmenInnen(kanten);
        else absatzRahmenSetzen(kanten);
      });
      tafel.appendChild(k);
    }

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    const mehr = document.createElement('button');
    mehr.type = 'button';
    mehr.className = 'designtafel__zeile richtungszeile';
    mehr.appendChild(symbol('absatzrahmen'));
    const w = document.createElement('span');
    w.textContent = 'Rahmen und Schattierung…';
    mehr.appendChild(w);
    mehr.addEventListener('mousedown', (e) => e.preventDefault());
    mehr.addEventListener('click', () => { designTafelWeg(); B.seitenraenderRahmen('rahmen'); });
    tafel.appendChild(mehr);
  });
};

/* „Du hast das Dialogfenster doppelt gemoppelt."

   Stimmte: Absatzrahmen und Absatzschattierung zeigten beide auf
   dasselbe Fenster, und dasselbe Fenster haengt schon am Seitenrand.
   Drei Knoepfe, ein Fenster.

   In WPS ist die Schattierung eine FARBKLAPPE — man waehlt eine Farbe
   und fertig. Das Fenster steht darin als letzter Punkt, fuer die, die
   mehr wollen. Genau wie beim Rahmen daneben. */
/* Welche Farbe hat der Absatz gerade? Damit das Farbenfenster bei
   „Aktuell" nicht irgendetwas zeigt. */
function gewaehlteSchattierung() {
  const el = absaetzeInAuswahl()[0];
  if (!el || !el.style.backgroundColor) return '#FFFFFF';
  const m = el.style.backgroundColor.match(/\d+/g);
  if (!m) return '#FFFFFF';
  return '#' + m.slice(0, 3).map((z) => (+z).toString(16).padStart(2, '0')).join('');
}

B.absatzSchattierung = (knopf) => {
  designTafelZeigen(knopf, 'Schattierung', (tafel) => {
    tafel.classList.add('designtafel--breit', 'farbtafel');

    const nimm = (hex, name) => {
      const ziele = absaetzeInAuswahl();
      if (!ziele.length) { melde('Dafür muss der Zeiger in einem Absatz stehen.'); return; }
      for (const a of ziele) {
        a.style.backgroundColor = hex || '';
        a.style.padding = hex ? '2mm 3mm' : '';
      }
      geaendertMelden();
      melde(hex ? 'Hinterlegt: ' + name + '.' : 'Hinterlegung entfernt.');
    };

    const zeile = (bild, name, tun) => {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      k.appendChild(symbol(bild));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', tun);
      tafel.appendChild(k);
    };

    const ueberschrift = (text) => {
      const h = document.createElement('div');
      h.className = 'farbtafel__gruppe';
      h.textContent = text;
      tafel.appendChild(h);
    };

    /* AUFBAU NACH SEINEM WPS-BILD
       „Keine Farbe" ganz oben, dann „Thema-Farben" als Raster mit
       Abstufungen, dann „Standard-Farben", unten „Weitere Fuellfarben".
       Vorher standen zwei Farbreihen ohne Ueberschrift da und „Keine
       Fuellung" unten.

       DIE FARBEN SIND SEINE. Das Raster berechnet die Abstufungen aus
       FARBEN — den zwoelf Toenen, die er ausgesucht hat. Ich habe diese
       Palette einmal gegen WPS-Signalfarben getauscht; das kommt nicht
       wieder. */
    zeile('radierer', 'Keine Füllung', () => { designTafelWeg(); nimm('', ''); });

    ueberschrift('Themenfarben');
    const gitter = document.createElement('div');
    gitter.className = 'farbtafel__gitter';
    /* Eine Spalte je Farbe, von hell nach dunkel — wie in WPS. Oben der
       Grundton, darunter fuenf Stufen. */
    for (const [hex, name] of FARBEN) {
      const spalte = document.createElement('div');
      spalte.className = 'farbtafel__spalte';
      const [h, sa, l] = hexZuHsl(hex);
      const stufen = [
        [hex, name],
        [hslZuHex(h, Math.min(0.55, sa), Math.min(0.94, l + 0.34)), name + ', sehr hell'],
        [hslZuHex(h, Math.min(0.62, sa), Math.min(0.88, l + 0.22)), name + ', hell'],
        [hslZuHex(h, sa, Math.max(0.18, l - 0.10)), name + ', dunkel'],
        [hslZuHex(h, sa, Math.max(0.12, l - 0.20)), name + ', dunkler'],
        [hslZuHex(h, sa, Math.max(0.08, l - 0.30)), name + ', am dunkelsten'],
      ];
      for (const [ton, wie] of stufen) {
        const feldchen = farbfeld(ton, () => { designTafelWeg(); nimm(ton, wie); });
        feldchen.title = wie;
        spalte.appendChild(feldchen);
      }
      gitter.appendChild(spalte);
    }
    tafel.appendChild(gitter);

    ueberschrift('Standardfarben');
    const voll = document.createElement('div');
    voll.className = 'farbtafel__reihe farbtafel__reihe--zwoelf';
    for (const [hex, name] of FARBEN) {
      const feldchen = farbfeld(hex, () => { designTafelWeg(); nimm(hex, name); });
      feldchen.title = name;
      voll.appendChild(feldchen);
    }
    tafel.appendChild(voll);

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    zeile('farbe', 'Weitere Füllfarben…', () => {
      designTafelWeg();
      farbFenster(gewaehlteSchattierung(), (hex) => nimm(hex, hex));
    });
    zeile('absatztoenung', 'Rahmen und Schattierung…',
          () => { designTafelWeg(); B.seitenraenderRahmen('schatten'); });
  });
};

/* ============================================================
   Aus den Tabs Entwurf und Layout von Word
   ============================================================ */

/* ---- Papierformat und Ausrichtung ----
   Das Blatt hatte bisher eine feste Größe: A4 hoch. Wer einen Aushang quer
   schreibt oder auf A5 druckt, braucht beides. */
/* WPS zeigt hinter A4 und A3 acht chinesische Formate — 8开, 16开,
   3号信封 und so fort. Hier stehen die, die in Deutschland jemand
   braucht: die A- und B-Reihe, die amerikanischen zwei und die drei
   Umschlaege nach DIN. */
const PAPIERE = {
  a4:      { name: 'A4',                breite: 210, hoehe: 297 },
  a3:      { name: 'A3',                breite: 297, hoehe: 420 },
  a5:      { name: 'A5',                breite: 148, hoehe: 210 },
  b5:      { name: 'B5',                breite: 176, hoehe: 250 },
  letter:  { name: 'Letter',            breite: 216, hoehe: 279 },
  legal:   { name: 'Legal',             breite: 216, hoehe: 356 },
  dinlang: { name: 'Umschlag DIN lang', breite: 220, hoehe: 110 },
  c5:      { name: 'Umschlag C5',       breite: 229, hoehe: 162 },
  c6:      { name: 'Umschlag C6',       breite: 162, hoehe: 114 },
};

const papierEigen = Speicher.lies('papierEigen', null);
if (papierEigen) PAPIERE.eigen = papierEigen;
let papier = Speicher.lies('papier', 'a4');
let quer = Speicher.lies('quer', false);

function papierAnwenden() {
  const masse = PAPIERE[papier] || PAPIERE.a4;
  const breite = quer ? masse.hoehe : masse.breite;
  const hoehe = quer ? masse.breite : masse.hoehe;

  const blatt = $('blatt');
  blatt.style.width = breite + 'mm';
  blatt.style.minHeight = hoehe + 'mm';

  /* Auch der Druck muss es wissen — sonst sieht das Blatt am Bildschirm quer
     aus und käme hochkant aus dem Drucker. */
  let regel = document.getElementById('seitenregel');
  if (!regel) {
    regel = document.createElement('style');
    regel.id = 'seitenregel';
    document.head.appendChild(regel);
  }
  regel.textContent = '@page{size:' + breite + 'mm ' + hoehe + 'mm;margin:0}';

  Speicher.schreib('papier', papier);
  Speicher.schreib('quer', quer);
  menueBauen();
  zahlenAuffrischen();
  linealAuffrischen();
}

const setzePapier = (art) => () => {
  papier = art; papierAnwenden(); abschnittMerken(abschnittJetztNr);
  melde(PAPIERE[art].name + (Aufbau && Aufbau.getSections().length > 1
    ? ' — für Abschnitt ' + (abschnittJetztNr + 1) + '.' : '.'));
};
B.querformat = () => {
  quer = !quer;
  papierAnwenden();
  abschnittMerken(abschnittJetztNr);
  const wo = Aufbau && Aufbau.getSections().length > 1
    ? ' — für Abschnitt ' + (abschnittJetztNr + 1) + '.' : '.';
  melde((quer ? 'Querformat' : 'Hochformat') + wo);
};

/* ---- Seitenränder als Vorgaben ----
   „Normal", „Schmal", „Mittel", „Breit" wie in Word — die eigenen Werte
   bleiben daneben bestehen. */
/* Die Masse stehen in WPS in Zoll; hier in Millimetern, weil das
   Programm ueberall in Millimetern rechnet. Die Namen und die Werte
   sind dieselben. */
const RANDVORGABEN = {
  normal:  { name: 'Normal',  oben: 25, unten: 25, links: 32, rechts: 32 },
  schmal:  { name: 'Schmal',  oben: 13, unten: 13, links: 13, rechts: 13 },
  moderat: { name: 'Moderat', oben: 25, unten: 25, links: 19, rechts: 19 },
  breit:   { name: 'Breit',   oben: 25, unten: 25, links: 51, rechts: 51 },
};

const setzeRandVorgabe = (art) => () => {
  const wie = RANDVORGABEN[art];
  seitenrand.oben = wie.oben; seitenrand.unten = wie.unten;
  seitenrand.links = wie.links; seitenrand.rechts = wie.rechts;
  seiteAnwenden();
  abschnittMerken(abschnittJetztNr);
  melde('Seitenränder: ' + wie.name + '.');
};

/* ---- Einzug links und rechts, auf den Millimeter ----
   Die beiden Knöpfe in der Leiste rücken in Sprüngen ein. Wer einen genauen
   Wert braucht — etwa für ein eingerücktes Zitat —, gibt ihn hier ein. */
/* ---- Zeilennummern ----
   Für Verträge und Schriftsätze: Jede Zeile bekommt links eine Zahl, auf
   die man sich beziehen kann. Gezählt werden Absätze — echte Zeilenumbrüche
   kennt nur der Zeichensatz beim Umbrechen, und die Zahl stünde bei jeder
   Fensterbreite woanders. */
let zeilennummern = Speicher.lies('zeilennummern', false);
let zeilennummernArt = Speicher.lies('zeilennummernArt', 'keine');
let zeilennummernBeginn = Speicher.lies('zeilennummernBeginn', 1);
let zeilennummernSchritt = Speicher.lies('zeilennummernSchritt', 1);
let zeilennummernOhneLeere = Speicher.lies('zeilennummernOhneLeere', false);

function zeilennummernAnwenden() {
  feld.classList.toggle('dokument--zeilennummern', zeilennummern);
  feld.classList.toggle('dokument--nummern-ohne-leere', zeilennummernOhneLeere);
  feld.dataset.nummernart = zeilennummernArt;
  /* Der Zaehler beginnt, wo der Anwender ihn haben will, und zeigt nur
     jede n-te Nummer — beides ueber Eigenschaften, die das Stilblatt
     abgreift. */
  feld.style.setProperty('--nummern-beginn', String(zeilennummernBeginn - 1));
  feld.style.setProperty('--nummern-schritt', String(zeilennummernSchritt));
  Speicher.schreib('zeilennummern', zeilennummern);
  Speicher.schreib('zeilennummernArt', zeilennummernArt);
  Speicher.schreib('zeilennummernBeginn', zeilennummernBeginn);
  Speicher.schreib('zeilennummernSchritt', zeilennummernSchritt);
  Speicher.schreib('zeilennummernOhneLeere', zeilennummernOhneLeere);
  menueBauen();
}
/* WPS hat hier keinen Schalter, sondern eine Liste. Die uebernehme ich:
     Keine · Fortlaufend · Jede Seite neu beginnen · Jeden Abschnitt neu
     beginnen · Für aktuellen Paragraphen unterdrücken · Verstecke
     Zeilennummern für leere Zeilen · Einstellungen…
   Gezaehlt wird hier der Absatz, nicht die gesetzte Zeile — der Browser
   bricht selbst um, und wo er es tut, haengt vom Fenster ab. */
const ZEILENNUMMERN_ARTEN = [
  ['keine',     'Keine'],
  ['laufend',   'Fortlaufend'],
  ['proSeite',  'Jede Seite neu beginnen'],
  ['proAbschnitt', 'Jeden Abschnitt neu beginnen'],
];

B.zeilennummern = (knopf) => {
  designTafelZeigen(knopf, 'Zeilennummern', (tafel) => {
    for (const [kuerzel, name] of ZEILENNUMMERN_ARTEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile';
      k.textContent = name;
      if ((zeilennummernArt || 'keine') === kuerzel) k.classList.add('designtafel__zeile--gilt');
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        zeilennummernArt = kuerzel;
        zeilennummern = kuerzel !== 'keine';
        zeilennummernAnwenden();
        designTafelWeg();
        melde('Zeilennummern: ' + name + '.');
      });
      tafel.appendChild(k);
    }

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    for (const [schluessel, name] of [
      ['stumm', 'Für aktuellen Paragraphen unterdrücken'],
      ['ohneLeere', 'Verstecke Zeilennummern für leere Zeilen'],
    ]) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile';
      k.textContent = name;
      if (schluessel === 'ohneLeere' && zeilennummernOhneLeere) k.classList.add('designtafel__zeile--gilt');
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        if (schluessel === 'ohneLeere') {
          zeilennummernOhneLeere = !zeilennummernOhneLeere;
          zeilennummernAnwenden();
          melde(zeilennummernOhneLeere ? 'Leere Zeilen bekommen keine Nummer.'
                                       : 'Leere Zeilen werden mitgezählt.');
        } else {
          const absatz = absatzJetzt();
          if (!absatz) { melde('Dafür muss der Zeiger in einem Absatz stehen.'); return; }
          absatz.classList.toggle('ohne-zeilennummer');
          geaendertMelden();
          melde(absatz.classList.contains('ohne-zeilennummer')
            ? 'Dieser Absatz bekommt keine Nummer.' : 'Dieser Absatz wird wieder gezählt.');
        }
        designTafelWeg();
      });
      tafel.appendChild(k);
    }

    const mehr = document.createElement('button');
    mehr.type = 'button';
    mehr.className = 'layouttafel__weiter';
    mehr.textContent = 'Zeilennummerierungs-Einstellungen…';
    mehr.addEventListener('click', () => { designTafelWeg(); B.zeilennummernFenster(); });
    tafel.appendChild(mehr);
  });
};

B.zeilennummernFenster = () => {
  fenster('Zeilennummerierung', [
    { art: 'satz', text: 'Gezählt werden Absätze. Wo der Browser eine Zeile '
                       + 'umbricht, hängt von der Fensterbreite ab — eine '
                       + 'Nummer daran wäre nicht dieselbe wie im Druck.' },
    { schluessel: 'art', name: 'Zählweise', art: 'auswahl',
      werte: ZEILENNUMMERN_ARTEN, wert: zeilennummernArt || 'keine' },
    { schluessel: 'beginn', name: 'Beginnen bei', art: 'number',
      wert: String(zeilennummernBeginn) },
    { schluessel: 'schritt', name: 'Nur jede n-te Nummer zeigen', art: 'number',
      wert: String(zeilennummernSchritt) },
  ], (werte) => {
    zeilennummernArt = werte.art;
    zeilennummern = werte.art !== 'keine';
    zeilennummernBeginn = Math.max(0, parseInt(werte.beginn, 10) || 1);
    zeilennummernSchritt = Math.max(1, parseInt(werte.schritt, 10) || 1);
    zeilennummernAnwenden();
    melde('Zeilennummerierung übernommen.');
  });
};

/* ---- Silbentrennung ----
   Der Browser trennt selbst, wenn man es ihm erlaubt und die Sprache kennt.
   Im Blocksatz macht das den Unterschied zwischen Löchern und einem
   ruhigen Satzbild. */
let trennung = Speicher.lies('trennung', false);

function trennungAnwenden() {
  feld.style.hyphens = trennung ? 'auto' : '';
  feld.lang = 'de';
  Speicher.schreib('trennung', trennung);
  menueBauen();
}
B.silbentrennung = () => {
  trennung = !trennung;
  trennungAnwenden();
  melde(trennung ? 'Silbentrennung an.' : 'Silbentrennung aus.');
};

/* ---- Seitenfarbe und Wasserzeichen ---- */
let seitenfarbe = Speicher.lies('seitenfarbe', '');

function seitenfarbeAnwenden() {
  Speicher.schreib('seitenfarbe', seitenfarbe);
  /* Welche Farbe das Blatt am Ende trägt, entscheidet lesehilfeAnwenden():
     Die Seitenfarbe gehört dem Dokument und geht mit aufs Papier, der
     Papierton nur an den Bildschirm. Zwei Stellen, die dieselbe
     Eigenschaft setzen, löschen sich sonst gegenseitig. */
  lesehilfeAnwenden();
}

/* ============================================================
   DESIGNS: FARBEN, SCHRIFTEN, EFFEKTE

   Der groesste fehlende Block aus dem Abgleich mit WPS. Dort steht er
   ganz links im Seitenlayout: Designs, Farben, Schriftarten, Effekte.

   WAS EIN DESIGN IST. Kein Aussehen des Programms, sondern eines des
   DOKUMENTS: Welche Farbe haben die Ueberschriften, welche Schrift die
   Ueberschriften und welche der Fliesstext, wie sind Tabellen getoent.
   Wer ein Design waehlt, trifft ein Dutzend Entscheidungen mit einem
   Klick — und genau darum geht es hier: Fuer jemanden, der an der Form
   scheitert und nicht am Schreiben, ist das der Unterschied zwischen
   "sieht aus wie ein Brief" und "sieht aus wie Text auf Papier".

   WIE ES WIRKT. Ueber vier Eigenschaften am Blatt: --ds-akzent,
   --ds-akzent-hell, --ds-ueberschrift, --ds-text. Die Stilvorlage
   greift sie ab. Nichts davon steht im Text selbst — ein Wechsel des
   Designs aendert kein einziges Zeichen, und Word-Dateien bringen ihre
   eigene Formatierung weiter mit.
   ============================================================ */

/* Die Farbschemata. Die Namen sind die aus WPS — wer von dort kommt,
   findet seines wieder. Je Schema: Akzent, heller Akzent, Farbe der
   Ueberschriften, Farbe des Fliesstexts. */
const FARBSCHEMATA = [
  ['standard',   'Standard',     ['#2F6FB5', '#D6E4F0', '#1F4E79', '#111417']],
  ['larissa',    'Larissa',      ['#37618E', '#DCE6F1', '#1F3864', '#14181C']],
  ['naehe',      'Nähe',         ['#8C7B62', '#EAE3D8', '#5C4E3A', '#1B1A17']],
  ['winkel',     'Winkel',       ['#2E5E4E', '#D9E8E1', '#1B4132', '#12201A']],
  ['ananke',     'Ananke',       ['#6D5B8E', '#E3DCEE', '#453868', '#1A1622']],
  ['apotheke',   'Apotheke',     ['#A34A3C', '#F2DFDB', '#71271C', '#201310']],
  ['ganymed',    'Ganymed',      ['#1F6F78', '#D5EBED', '#0F484F', '#0E1E20']],
  ['austin',     'Austin',       ['#7A8C2E', '#E8EFCF', '#4C5A14', '#191D0C']],
  ['smoking',    'Smoking',      ['#4A4A4A', '#E2E2E2', '#232323', '#111111']],
  ['kalligrafie','Kalligrafie',  ['#7B2D3B', '#F0DCE0', '#4E121C', '#1E0D11']],
  ['cronus',     'Cronus',       ['#B07A1E', '#F6E8CC', '#7A5210', '#22190A']],
  ['klarheit',   'Klarheit',     ['#C24A3A', '#FADFDA', '#8A2818', '#1F100D']],
  ['zusammen',   'Zusammenhalt', ['#5B7B7A', '#DFE9E8', '#33514F', '#141C1B']],
  ['deimos',     'Deimos',       ['#2B4C7E', '#D8E2F0', '#16305A', '#101722']],
  ['couture',    'Couture',      ['#8E7F6B', '#EDE7DD', '#5E5243', '#1C1917']],
  ['drachen',    'Drachen',      ['#1D4E6B', '#D6E7F0', '#0D3145', '#0E1A21']],
  ['elementar',  'Elementar',    ['#3E7CB1', '#DEEBF5', '#22557E', '#121B22']],
  ['dactylos',   'Dactylos',     ['#8C4A3F', '#F0DFDB', '#5E2A21', '#1E1310']],
  ['essenz',     'Essenz',       ['#C0392B', '#FADBD8', '#85251B', '#200F0D']],
  ['executive',  'Executive',    ['#3D5A80', '#DCE4EE', '#22374F', '#111720']],
  ['lueftung',   'Lüftung',      ['#6E8B3D', '#E6EDD6', '#455A22', '#161B0F']],
  ['fluss',      'Fluss',        ['#0E7C86', '#D2EDEF', '#06515A', '#0B1E20']],
  ['phoebe',     'Phoebe',       ['#7E6B8F', '#E7E0EC', '#50415E', '#1A1620']],
  ['graustufen', 'Graustufen',   ['#5A5A5A', '#E4E4E4', '#2E2E2E', '#141414']],
  ['raster',     'Raster',       ['#7D6E5D', '#EAE4DC', '#4F443A', '#1A1714']],
  ['hardcover',  'Hardcover',    ['#8A3324', '#F1DED9', '#5C1F14', '#1D100C']],
  ['horizon',    'Horizon',      ['#C87A1E', '#F8E5CB', '#8A5010', '#22170A']],
  ['galathea',   'Galathea',     ['#4A6FA5', '#DEE6F2', '#2A4670', '#131A24']],
  ['lapetus',    'Lapetus',      ['#9A6B3F', '#F0E3D4', '#654122', '#1F1611']],
];

/* ACHT FELDER JE ZEILE, wie auf seinem Bild.

   In WPS zeigt jede Zeile acht Farbfelder und dahinter den Namen. Meine
   Fassung zeigte vier. Vier Felder sehen bei zwoelf Schemata gleich aus;
   acht unterscheiden sie.

   Hinterlegt sind je Schema vier Farben mit einer Bedeutung — Akzent,
   heller Akzent, Ueberschrift, Text. Die fehlenden vier entstehen
   daraus: Weiss als Gegenstueck zum Text, und drei Geschwister des
   Akzents, um den Farbkreis gedreht. So bleibt die Zeile bunt wie in
   WPS, ohne dass ich 27 mal acht Farben erfinde, die dann doch nicht
   die aus WPS waeren.

   Die Reihenfolge folgt dem Bild: erst dunkel, dann hell, dann die
   Akzente. */
function hexZuHsl(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const sa = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h, sa, l];
}

function hslZuHex(h, sa, l) {
  h = ((h % 1) + 1) % 1;
  const f = (n) => {
    const k = (n + h * 12) % 12;
    const a = sa * Math.min(l, 1 - l);
    const v = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return Math.round(v * 255).toString(16).padStart(2, '0');
  };
  return '#' + f(0) + f(8) + f(4);
}

function schemaFelder(farben) {
  const [akzent, hell, ueber, text] = farben;
  const [h, sa, l] = hexZuHsl(akzent);
  return [text, '#FFFFFF', ueber, hell, akzent,
          hslZuHex(h + 0.11, sa, l),
          hslZuHex(h - 0.11, sa, Math.min(0.72, l + 0.08)),
          hslZuHex(h + 0.42, sa * 0.85, l)];
}

/* Die Schriftpaare: eine fuer die Ueberschriften, eine fuer den Text.

   Die Leseschriften stehen vorn und werden auch so benannt — in diesem
   Programm sind sie nicht eine Moeglichkeit unter vielen. */
const DESIGNSCHRIFTEN = [
  ['lesen',    'Zum leichteren Lesen', 'OpenDyslexic', 'OpenDyslexic'],
  ['lexend',   'Lexend',               'Lexend', 'Lexend'],
  ['atkinson', 'Atkinson Hyperlegible','Atkinson Hyperlegible', 'Atkinson Hyperlegible'],
  ['klassisch','Klassisch',            'Georgia', 'Georgia'],
  ['amt',      'Amtlich',              'Liberation Sans', 'Liberation Serif'],
  ['modern',   'Modern',               'Lexend', 'Liberation Sans'],
  ['buch',     'Wie ein Buch',         'Liberation Serif', 'Liberation Serif'],
  ['gemischt', 'Überschrift serifenlos','Liberation Sans', 'Liberation Serif'],
];

/* Die Effekte gelten fuer Formen und Bilder — das ist in WPS dasselbe. */
const DESIGNEFFEKTE = [
  ['keiner',  'Kein Effekt',    ''],
  ['schatten','Schatten',       'drop-shadow(2px 3px 4px rgba(0,0,0,.35))'],
  ['weich',   'Weicher Rand',   'blur(0.4px) drop-shadow(0 0 3px rgba(0,0,0,.25))'],
  ['leuchten','Leuchten',       'drop-shadow(0 0 6px rgba(47,111,181,.65))'],
  ['tief',    'Tiefer Schatten','drop-shadow(4px 6px 8px rgba(0,0,0,.45))'],
];

/* DIESE DREI STEHEN NEBEN dem vorhandenen Design, nicht darueber.

   Lunivo hatte bereits DESIGNS (Amtlich, Klassisch, Modern, Warm,
   Ruhig): ein Schriftpaar und zwei Farben, die auf die Formatvorlagen
   wirken. Das bleibt, wie es ist. Ich hatte beinahe ein zweites daneben
   gebaut — und das waere genau der Fehler gewesen, den ich mir schon
   notiert habe: erst nachsehen, was da ist.

   Was hier dazukommt, ist das Feinere: ein Farbschema fuer Akzente und
   Tabellen, ein Schriftpaar zur Auswahl und ein Effekt fuer Formen und
   Bilder. Der Designkatalog weiter unten setzt beides zusammen. */
const farbschemaEigen = Speicher.lies('farbschemaEigen', null);
if (farbschemaEigen) FARBSCHEMATA.push(farbschemaEigen);

let designFein = Object.assign(
  { farben: 'standard', schriften: 'lesen', effekt: 'keiner' },
  Speicher.lies('designFein', {}));

function designFeinAnwenden() {
  const blatt = $('blatt');
  if (!blatt) return;
  const f = FARBSCHEMATA.find(([m]) => m === designFein.farben) || FARBSCHEMATA[0];
  blatt.style.setProperty('--ds-akzent', f[2][0]);
  blatt.style.setProperty('--ds-akzent-hell', f[2][1]);
  blatt.style.setProperty('--ds-ueberschrift', f[2][2]);
  blatt.style.setProperty('--ds-text', f[2][3]);

  const sch = DESIGNSCHRIFTEN.find(([m]) => m === designFein.schriften) || DESIGNSCHRIFTEN[0];
  blatt.style.setProperty('--ds-schrift-ueber', '"' + sch[2] + '"');
  blatt.style.setProperty('--ds-schrift-text', '"' + sch[3] + '"');

  const ef = DESIGNEFFEKTE.find(([m]) => m === designFein.effekt) || DESIGNEFFEKTE[0];
  blatt.style.setProperty('--ds-effekt', ef[2] || 'none');
}

function designFeinSetzen(teil, wert) {
  designFein[teil] = wert;
  Speicher.schreib('designFein', designFein);
  designFeinAnwenden();
  geaendertMelden();
}

/* Eine Tafel mit Proben — wie bei WPS: Man sieht die Farben, statt einen
   Namen zu lesen. */
let designTafel = null;
function designTafelWeg() {
  if (designTafel) { designTafel.remove(); designTafel = null; }
}

function designTafelZeigen(knopf, titel, bauen) {
  if (designTafel) { designTafelWeg(); return; }
  const tafel = document.createElement('div');
  tafel.className = 'katalogklappe designtafel';
  const kopf = document.createElement('p');
  kopf.className = 'katalogklappe__kopf';
  kopf.textContent = titel;
  tafel.appendChild(kopf);
  bauen(tafel);
  document.body.appendChild(tafel);
  designTafel = tafel;

  const r = (knopf && knopf.getBoundingClientRect)
    ? knopf.getBoundingClientRect() : { left: 120, bottom: 120 };
  const m = tafel.getBoundingClientRect();
  tafel.style.left = Math.round(Math.max(8,
    Math.min(r.left, window.innerWidth - 8 - m.width))) + 'px';
  tafel.style.top = Math.round(Math.max(8,
    Math.min(r.bottom + 4, window.innerHeight - 8 - m.height))) + 'px';

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(ev) {
      if (tafel.contains(ev.target) || (knopf && knopf.contains(ev.target))) return;
      designTafelWeg();
      document.removeEventListener('mousedown', zu);
    });
  }, 0);
}

B.farbschema = (knopf) => designTafelZeigen(knopf, 'Farben', (tafel) => {
  tafel.classList.add('designtafel--farben');

  const ueberschrift = document.createElement('p');
  ueberschrift.className = 'designtafel__kopfzeile';
  ueberschrift.textContent = 'Standardfarben';
  tafel.appendChild(ueberschrift);

  const gitter = document.createElement('div');
  gitter.className = 'designtafel__gitter';
  for (const [marke, name, farben] of FARBSCHEMATA) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'designtafel__wahl'
      + (designFein.farben === marke ? ' designtafel__wahl--an' : '');
    k.title = name;
    const streifen = document.createElement('span');
    streifen.className = 'designtafel__streifen';
    for (const c of schemaFelder(farben)) {
      const stueck = document.createElement('i');
      stueck.style.background = c;
      streifen.appendChild(stueck);
    }
    const wort = document.createElement('span');
    wort.className = 'designtafel__name';
    wort.textContent = name;
    k.append(streifen, wort);
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      designFeinSetzen('farben', marke);
      designTafelWeg();
      melde('Farben: ' + name);
    });
    gitter.appendChild(k);
  }
  tafel.appendChild(gitter);

  /* Unten in der Vorlage: „Custom color…". Auf Deutsch heisst das
     „Eigene Farbe…", und es setzt den Akzent, an dem Ueberschriften,
     Kopfzeilen von Tabellen und Formen haengen. */
  const eigen = document.createElement('button');
  eigen.type = 'button';
  eigen.className = 'designtafel__zeile richtungszeile';
  eigen.appendChild(symbol('farbe'));
  const wort = document.createElement('span');
  wort.textContent = 'Eigene Farbe…';
  eigen.appendChild(wort);
  eigen.addEventListener('mousedown', (e) => e.preventDefault());
  eigen.addEventListener('click', () => { designTafelWeg(); B.eigeneAkzentfarbe(); });
  tafel.appendChild(eigen);
});

B.eigeneAkzentfarbe = () => {
  const jetzt = FARBSCHEMATA.find(([m]) => m === designFein.farben) || FARBSCHEMATA[0];
  fenster('Eigene Farbe', [
    { art: 'satz', text: 'Die Akzentfarbe. An ihr hängen Überschriften, die '
                       + 'Kopfzeile einer Tabelle und die Farbe neuer Formen.' },
    { schluessel: 'farbe', name: 'Akzent', art: 'color', wert: jetzt[2][0] },
  ], (werte) => {
    const [h, sa, l] = hexZuHsl(werte.farbe);
    const eintrag = ['eigen', 'Eigene Farbe',
      [werte.farbe, hslZuHex(h, Math.max(0.12, sa * 0.28), 0.90),
       hslZuHex(h, sa, Math.max(0.18, l - 0.18)), '#14181C']];
    const alt = FARBSCHEMATA.findIndex(([m]) => m === 'eigen');
    if (alt >= 0) FARBSCHEMATA[alt] = eintrag; else FARBSCHEMATA.push(eintrag);
    Speicher.schreib('farbschemaEigen', eintrag);
    designFeinSetzen('farben', 'eigen');
    melde('Eigene Farbe gesetzt.');
  });
};

/* Aufgebaut wie in der Vorlage: links eine Kachel mit „Aa", rechts der
   Name des Paares klein darueber, dann die Ueberschriftenschrift gross
   und die Textschrift darunter — jede in sich selbst gesetzt.

   MEINE FASSUNG SCHRIEB „Überschrift" und „Fließtext, wie er auf dem
   Blatt steht". Das sagt, was die Zeile tut, aber nicht, WELCHE Schrift
   man bekommt. In WPS steht dort der Name der Schrift, in dieser
   Schrift — „Cambria" in Cambria. Das ist die Probe und die Antwort in
   einem. */
B.designSchriften = (knopf) => designTafelZeigen(knopf, 'Schriftarten', (tafel) => {
  tafel.classList.add('designtafel--breit');
  for (const [marke, name, ueber, text] of DESIGNSCHRIFTEN) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'schriftzeile'
      + (designFein.schriften === marke ? ' schriftzeile--an' : '');

    const kachel = document.createElement('span');
    kachel.className = 'schriftzeile__kachel';
    kachel.textContent = 'Aa';
    kachel.style.fontFamily = "'" + ueber + "', Georgia, serif";
    k.appendChild(kachel);

    const spalte = document.createElement('span');
    spalte.className = 'schriftzeile__spalte';

    const wort = document.createElement('em');
    wort.className = 'schriftzeile__name';
    wort.textContent = name;
    spalte.appendChild(wort);

    const oben = document.createElement('strong');
    oben.className = 'schriftzeile__ueber';
    oben.style.fontFamily = "'" + ueber + "', Georgia, serif";
    oben.textContent = ueber;
    spalte.appendChild(oben);

    const unten = document.createElement('span');
    unten.className = 'schriftzeile__text';
    unten.style.fontFamily = "'" + text + "', Georgia, serif";
    unten.textContent = text;
    spalte.appendChild(unten);

    k.appendChild(spalte);
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      designFeinSetzen('schriften', marke);
      designTafelWeg();
      melde('Schriftarten: ' + name);
    });
    tafel.appendChild(k);
  }
});

/* Vier nebeneinander, jede Kachel mit demselben Pfeil — so steht es in
   der Vorlage. Derselbe Gegenstand in jeder Kachel ist der Punkt: Nur
   dann sieht man, was der Effekt aendert, und nicht, was die Form
   aendert. */
function effektpfeil() {
  const ns = 'http://www.w3.org/2000/svg';
  const sv = document.createElementNS(ns, 'svg');
  sv.setAttribute('viewBox', '0 0 48 40');
  sv.setAttribute('class', 'effektkachel__bild');
  sv.setAttribute('aria-hidden', 'true');
  const pfeil = document.createElementNS(ns, 'path');
  pfeil.setAttribute('d', 'M4 14h22V6l16 14-16 14v-8H4z');
  pfeil.setAttribute('fill', 'var(--ds-akzent, #4a90d9)');
  pfeil.setAttribute('stroke', 'var(--ds-ueberschrift, #2a5f92)');
  pfeil.setAttribute('stroke-width', '1.5');
  pfeil.setAttribute('stroke-linejoin', 'round');
  sv.appendChild(pfeil);
  return sv;
}

B.designEffekte = (knopf) => designTafelZeigen(knopf, 'Effekte', (tafel) => {
  tafel.classList.add('designtafel--breit');
  const gitter = document.createElement('div');
  gitter.className = 'effektgitter';
  for (const [marke, name, filter] of DESIGNEFFEKTE) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'effektkachel'
      + (designFein.effekt === marke ? ' effektkachel--an' : '');
    k.title = name;

    const rahmen = document.createElement('span');
    rahmen.className = 'effektkachel__rahmen';
    const bild = effektpfeil();
    bild.style.filter = filter || 'none';
    rahmen.appendChild(bild);
    k.appendChild(rahmen);

    const wort = document.createElement('span');
    wort.className = 'effektkachel__name';
    wort.textContent = name;
    k.appendChild(wort);

    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      designFeinSetzen('effekt', marke);
      designTafelWeg();
      melde('Effekt: ' + name + ' — gilt für Formen und Bilder.');
    });
    gitter.appendChild(k);
  }
  tafel.appendChild(gitter);
});

/* „Designs" ist das Ganze auf einmal: Farben und Schriften zusammen.
   Wer nicht einzeln waehlen will, nimmt eines von hier.

   NICHT „DESIGNS" — den Namen gibt es weiter unten schon. Zum zweiten
   Mal an einem Tag dieselbe Falle: Zwei gleichnamige Konstanten in einer
   Datei sind kein stiller Fehler wie bei Funktionen, sondern ein
   Absturz beim Laden. Der faellt wenigstens sofort auf. */
const DESIGNPAARE = [
  ['modern',    'Schlicht',    'standard',   'lesen'],
  ['amt',       'Amtlich',     'deimos',     'amt'],
  ['warm',      'Warm',        'naehe',      'klassisch'],
  ['ruhig',     'Ruhig',       'winkel',     'lexend'],
  ['klassisch', 'Klassisch',   'kalligrafie','buch'],
];

B.designs = (knopf) => designTafelZeigen(knopf, 'Designs', (tafel) => {
  for (const [grund, name, farben, schriften] of DESIGNPAARE) {
    const f = FARBSCHEMATA.find(([m]) => m === farben) || FARBSCHEMATA[0];
    const sch = DESIGNSCHRIFTEN.find(([m]) => m === schriften) || DESIGNSCHRIFTEN[0];
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'designtafel__zeile';
    k.innerHTML = '<span class="designtafel__probe" style="font-family:\''
      + sch[2] + '\',serif;color:' + f[2][2] + '">Überschrift</span>'
      + '<span class="designtafel__streifen">'
      + f[2].map((c) => '<i style="background:' + c + '"></i>').join('')
      + '</span><span class="designtafel__name">' + name + '</span>';
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      /* Beides auf einmal: das vorhandene Design fuer die Vorlagen,
         das Feine fuer Akzente und Schriften. */
      designAnwenden(grund);
      designFein.farben = farben;
      designFein.schriften = schriften;
      Speicher.schreib('designFein', designFein);
      designFeinAnwenden();
      geaendertMelden();
      designTafelWeg();
      melde('Design: ' + name);
    });
    tafel.appendChild(k);
  }
});

/* ============================================================
   OBJEKTE AUSRICHTEN UND DREHEN

   Aus dem Abgleich: WPS hat im Seitenlayout rechts „Ausrichten",
   „Gruppieren", „Drehen". Ausrichten und Drehen gehen hier, sobald ein
   Gegenstand frei auf der Seite liegt — und das koennen Bilder,
   Tabellen und Formen seit dieser Sitzung.

   AUSGERICHTET WIRD AM BLATT, nicht an anderen Gegenstaenden. Das
   Zweite braucht eine Mehrfachauswahl, die es hier nicht gibt; das
   Erste ist ohnehin der haeufigere Fall — ein Bild mittig setzen.
   ============================================================ */
function gegenstandJetzt() {
  const b = (typeof bildGemeint === 'function') ? bildGemeint() : null;
  if (b) return b;
  const auswahl = window.getSelection();
  let k = auswahl && auswahl.anchorNode;
  if (k && k.nodeType === Node.TEXT_NODE) k = k.parentElement;
  const form = k && k.closest ? k.closest('svg.zeichnung, table') : null;
  if (form && feld.contains(form)) return form;
  const letzte = feld.querySelector('svg.zeichnung');
  return letzte || null;
}

const OBJEKT_STELLEN = [
  ['links',  'Links am Rand',   (b, g) => ({ x: 0 })],
  ['mitte',  'Waagerecht mittig', (b, g) => ({ x: (b.breite - g.breite) / 2 })],
  ['rechts', 'Rechts am Rand',  (b, g) => ({ x: b.breite - g.breite })],
  ['oben',   'Oben',            (b, g) => ({ y: 0 })],
  ['mitte-s','Senkrecht mittig', (b, g) => ({ y: (b.hoehe - g.hoehe) / 2 })],
  ['unten',  'Unten',           (b, g) => ({ y: b.hoehe - g.hoehe })],
];

B.objektAusrichten = (knopf) => {
  const g = gegenstandJetzt();
  if (!g) { melde('Dafür muss ein Bild, eine Form oder eine Tabelle gewählt sein.'); return; }

  designTafelZeigen(knopf, 'Ausrichten', (tafel) => {
    const satz = document.createElement('p');
    satz.className = 'layouttafel__satz';
    satz.textContent = 'Ausgerichtet wird am Blatt. Der Gegenstand löst sich '
                     + 'dafür aus dem Textfluss, falls er noch darin steht.';
    for (const [, name, rechne] of OBJEKT_STELLEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile';
      k.textContent = name;
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        objektStellen(g, rechne);
        designTafelWeg();
        melde(name + '.');
      });
      tafel.appendChild(k);
    }
    tafel.appendChild(satz);
  });
};

function objektStellen(g, rechne) {
  /* Erst loesen: Was im Textfluss steht, laesst sich nicht stellen. */
  if (g.tagName === 'TABLE') { if (!istFrei(g)) freiMachen(g); }
  else if (!bildIstFrei(g)) bildFreiMachen(g);

  const bogen = g.closest('.dokument') || feld;
  const massstab = (zoom || 100) / 100;
  const br = bogen.getBoundingClientRect();
  const gr = g.getBoundingClientRect();
  const blatt = { breite: inMillimeter(br.width / massstab),
                  hoehe: inMillimeter(br.height / massstab) };
  const gegen = { breite: inMillimeter(gr.width / massstab),
                  hoehe: inMillimeter(gr.height / massstab) };
  const neu = rechne(blatt, gegen);
  if (neu.x !== undefined) g.style.left = Math.round(neu.x * 10) / 10 + 'mm';
  if (neu.y !== undefined) g.style.top = Math.round(neu.y * 10) / 10 + 'mm';
  geaendertMelden();
  if (typeof bildGriffeNachmessen === 'function') bildGriffeNachmessen();
  if (typeof griffNachmessen === 'function') griffNachmessen();
}

/* ============================================================
   GRUPPIEREN

   In WPS steht der Knopf neben Ausrichten und Drehen, und er ist grau,
   solange nichts gewaehlt ist. Ich habe ihn beim letzten Mal ganz
   weggelassen, weil es hier keine Mehrfachauswahl mit der Maus gibt.
   Das war zu schnell aufgegeben: Eine Auswahl ueber mehrere Bilder
   hinweg gibt es sehr wohl — mit gedrueckter Umschalttaste oder von
   einer Stelle im Text bis zu einer anderen.

   Was in dieser Auswahl an Bildern und Formen liegt, kommt in eine
   Huelle. Die laesst sich danach als ein Stueck verschieben, stellen
   und drehen, weil gegenstandJetzt() sie findet wie ein einzelnes Bild.
   ============================================================ */
function gegenstaendeInAuswahl() {
  const auswahl = window.getSelection();
  if (!auswahl || auswahl.rangeCount === 0 || auswahl.isCollapsed) return [];
  const alle = [...feld.querySelectorAll('img, svg.zeichnung, .gruppe')];
  return alle.filter((g) => auswahl.containsNode(g, true));
}

B.gruppieren = (knopf) => {
  const huelle = (() => {
    const g = gegenstandJetzt();
    return g && g.closest ? g.closest('.gruppe') : null;
  })();
  const gewaehlt = gegenstaendeInAuswahl();

  designTafelZeigen(knopf, 'Gruppieren', (tafel) => {
    const zeile = (name, moeglich, tun) => {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile';
      k.textContent = name;
      k.disabled = !moeglich;
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => { tun(); designTafelWeg(); });
      tafel.appendChild(k);
    };

    zeile('Gruppieren', gewaehlt.length > 1, () => {
      const hu = document.createElement('span');
      hu.className = 'gruppe';
      gewaehlt[0].parentNode.insertBefore(hu, gewaehlt[0]);
      for (const g of gewaehlt) hu.appendChild(g);
      geaendertMelden();
      melde(gewaehlt.length + ' Gegenstände sind jetzt ein Stück.');
    });

    zeile('Gruppierung aufheben', !!huelle, () => {
      const eltern = huelle.parentNode;
      const zahl = huelle.children.length;
      while (huelle.firstChild) eltern.insertBefore(huelle.firstChild, huelle);
      huelle.remove();
      geaendertMelden();
      melde(zahl + ' Gegenstände stehen wieder einzeln.');
    });

    const satz = document.createElement('p');
    satz.className = 'layouttafel__satz';
    satz.textContent = gewaehlt.length > 1
      ? gewaehlt.length + ' Gegenstände liegen in der Auswahl.'
      : 'Markieren Sie erst mehrere Bilder oder Formen — vom Text davor '
        + 'bis hinter das letzte.';
    tafel.appendChild(satz);
  });
};

const OBJEKT_DREHUNGEN = [
  ['Nach rechts drehen (90°)',  90],
  ['Nach links drehen (90°)',  -90],
  ['Um 180 Grad',              180],
];

B.objektDrehen = (knopf) => {
  const g = gegenstandJetzt();
  if (!g) { melde('Dafür muss ein Bild, eine Form oder eine Tabelle gewählt sein.'); return; }
  designTafelZeigen(knopf, 'Drehen', (tafel) => {
    for (const [name, grad] of OBJEKT_DREHUNGEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile';
      k.textContent = name;
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        const jetzt = (Number(g.dataset.drehung || 0) + grad + 360) % 360;
        g.dataset.drehung = String(jetzt);
        if (typeof bildVerwandlung === 'function' && g.tagName === 'IMG') {
          bildVerwandlung(g);
        } else {
          g.style.transform = jetzt ? 'rotate(' + jetzt + 'deg)' : '';
        }
        geaendertMelden();
        designTafelWeg();
        melde('Steht auf ' + jetzt + ' Grad.');
      });
      tafel.appendChild(k);
    }
    const zurueck = document.createElement('button');
    zurueck.type = 'button';
    zurueck.className = 'layouttafel__weiter';
    zurueck.textContent = 'Drehung zurücksetzen';
    zurueck.addEventListener('click', () => {
      g.dataset.drehung = '0';
      if (typeof bildVerwandlung === 'function' && g.tagName === 'IMG') bildVerwandlung(g);
      else g.style.transform = '';
      geaendertMelden();
      designTafelWeg();
      melde('Drehung zurückgesetzt.');
    });
    tafel.appendChild(zurueck);
  });
};

/* ============================================================
   TEXTRICHTUNG

   Sechs Punkte und ein Fenster, genau wie in WPS:

     Horizontal
     Vertikal von rechts nach links
     Vertikal von links nach rechts
     Gesamten Text um 90 Grad drehen
     Gesamten Text um 270 Grad drehen
     Asiatische Zeichen um 270 Grad drehen
     Textrichtung ändern…

   SIE GILT FÜR DIE SEITE, nicht fuer ein Wort. Meine erste Fassung
   verlangte einen Zeiger in einer Tabellenzelle und tat sonst nichts —
   wer sie aus dem Menue aufrief, bekam einen Satz statt einer Wirkung.
   Das war falsch: In WPS richtet dieser Knopf den ganzen Text der Seite
   aus. Steht der Zeiger in einer Zelle oder einem Rahmen, gilt sie nur
   dort; sonst fuer das Blatt.
   ============================================================ */
/* Jede Richtung zeigt sich an sich selbst — ein Kaestchen mit dem Wort
   „Abc", genau so gekippt, wie der Text danach steht. Das ist der Grund,
   warum in WPS neben jedem Punkt ein Bild steht und nicht nur ein Wort:
   „Vertikal von rechts nach links" und „Vertikal von links nach rechts"
   sind als Saetze kaum zu unterscheiden, als Bild sofort.

   MIT DEUTSCHEN BUCHSTABEN. In WPS steht in den Kaestchen „文字" neben
   „ABC" — das Programm kommt aus China und zeigt beide Schriften. Hier
   schreibt niemand chinesisch. Ich hatte die Zeichen mitgenommen, weil
   sie im Bild standen; abmalen ist nicht dasselbe wie uebernehmen.

   Zwei Woerter je Kaestchen, weil eine einzelne Spalte nicht verraet, ob
   der Text rechts oder links anfaengt: „Abc" ist die erste Spalte, „def"
   die zweite. */
function richtungsbild(kuerzel) {
  const ns = 'http://www.w3.org/2000/svg';
  const sv = document.createElementNS(ns, 'svg');
  sv.setAttribute('viewBox', '0 0 32 32');
  sv.setAttribute('class', 'richtungsbild');
  sv.setAttribute('aria-hidden', 'true');

  const rahmen = document.createElementNS(ns, 'rect');
  rahmen.setAttribute('x', '1.5'); rahmen.setAttribute('y', '1.5');
  rahmen.setAttribute('width', '29'); rahmen.setAttribute('height', '29');
  rahmen.setAttribute('fill', 'none');
  rahmen.setAttribute('stroke', 'currentColor');
  sv.appendChild(rahmen);

  /* Wort, x, y, Drehung — erst die erste Zeile/Spalte, dann die zweite. */
  const stand = {
    horizontal: [['Abc', 6, 14, 0], ['def', 6, 25, 0]],
    vrl:        [['Abc', 22, 7, 90], ['def', 11, 7, 90]],
    vlr:        [['Abc', 11, 7, 90], ['def', 22, 7, 90]],
    d90:        [['Abc', 22, 7, 90], ['def', 11, 7, 90]],
    d270:       [['Abc', 11, 25, 270], ['def', 22, 25, 270]],
  }[kuerzel] || [];

  for (const [wort, x, y, grad] of stand) {
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', String(x)); t.setAttribute('y', String(y));
    t.setAttribute('font-size', '9');
    t.setAttribute('fill', 'currentColor');
    if (grad) t.setAttribute('transform', 'rotate(' + grad + ' ' + x + ' ' + y + ')');
    t.textContent = wort;
    sv.appendChild(t);
  }
  return sv;
}

const TEXTRICHTUNGEN = [
  ['horizontal', 'Horizontal'],
  ['vrl',        'Vertikal von rechts nach links'],
  ['vlr',        'Vertikal von links nach rechts'],
  ['d90',        'Gesamten Text um 90 Grad drehen'],
  ['d270',       'Gesamten Text um 270 Grad drehen'],
  /* WPS hat hier noch „Asiatische Zeichen um 270 Grad drehen". Der Punkt
     dreht ausschliesslich chinesische, japanische und koreanische
     Zeichen und laesst lateinische stehen — in einem deutschen
     Schreibprogramm eine Zeile, die nie etwas tut. */
];

function richtungsziel() {
  const zelle = (typeof zelleOderZuletzt === 'function') ? zelleOderZuletzt() : null;
  if (zelle) return zelle;
  const auswahl = window.getSelection();
  let k = auswahl && auswahl.anchorNode;
  if (k && k.nodeType === Node.TEXT_NODE) k = k.parentElement;
  const rahmen = k && k.closest ? k.closest('.textrahmen') : null;
  if (rahmen && feld.contains(rahmen)) return rahmen;
  return feld;   /* sonst das ganze Blatt — so hält es WPS */
}

function textrichtungSetzen(ziel, kuerzel) {
  if (kuerzel === 'horizontal') delete ziel.dataset.richtung;
  else ziel.dataset.richtung = kuerzel;
  geaendertMelden();
  if (typeof bildGriffeNachmessen === 'function') bildGriffeNachmessen();
  if (typeof griffNachmessen === 'function') griffNachmessen();
}

B.textrichtung = (knopf) => {
  const ziel = richtungsziel();
  const jetzt = ziel.dataset.richtung || 'horizontal';

  designTafelZeigen(knopf, 'Textrichtung', (tafel) => {
    tafel.classList.add('designtafel--breit');
    for (const [kuerzel, name] of TEXTRICHTUNGEN) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile';
      k.appendChild(richtungsbild(kuerzel));
      const wort = document.createElement('span');
      wort.textContent = name;
      k.appendChild(wort);
      if (kuerzel === jetzt) k.classList.add('richtungszeile--gilt');
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        textrichtungSetzen(ziel, kuerzel);
        designTafelWeg();
        melde('Textrichtung: ' + name + '.');
      });
      tafel.appendChild(k);
    }

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    const mehr = document.createElement('button');
    mehr.type = 'button';
    mehr.className = 'designtafel__zeile richtungszeile';
    mehr.appendChild(symbol('textrichtung'));
    const wort = document.createElement('span');
    wort.textContent = 'Textrichtung ändern…';
    mehr.appendChild(wort);
    mehr.addEventListener('mousedown', (e) => e.preventDefault());
    mehr.addEventListener('click', () => { designTafelWeg(); B.textrichtungFenster(); });
    tafel.appendChild(mehr);
  });
};

B.textrichtungFenster = () => {
  const ziel = richtungsziel();
  const wohin = ziel === feld ? 'das ganze Blatt'
              : (ziel.tagName === 'TD' || ziel.tagName === 'TH') ? 'die Zelle'
              : 'den Rahmen';
  fenster('Textrichtung ändern', [
    { art: 'satz', text: 'Gilt für ' + wohin + '.' },
    { schluessel: 'richtung', name: 'Richtung', art: 'auswahl',
      werte: TEXTRICHTUNGEN, wert: ziel.dataset.richtung || 'horizontal' },
  ], (werte) => {
    const name = (TEXTRICHTUNGEN.find(([k]) => k === werte.richtung) || TEXTRICHTUNGEN[0])[1];
    textrichtungSetzen(ziel, werte.richtung);
    melde('Textrichtung: ' + name + '.');
  });
};

/* „Weitere Papierformate…" — Breite und Hoehe von Hand, wie in WPS
   hinter demselben Punkt. Etiketten, Klappkarten, alte Formate: Wer sie
   braucht, braucht sie genau und nicht ungefaehr. */
B.papierformatFenster = () => {
  const jetzt = PAPIERE[papier] || PAPIERE.a4;
  fenster('Papierformat', [
    { art: 'satz', text: 'In Millimetern. Hochformat; für Querformat gibt es '
                       + 'den eigenen Knopf daneben.' },
    { schluessel: 'breite', name: 'Breite (mm)', art: 'number', wert: String(jetzt.breite) },
    { schluessel: 'hoehe',  name: 'Höhe (mm)',   art: 'number', wert: String(jetzt.hoehe) },
  ], (werte) => {
    const zahl = (x, ersatz) => {
      const n = parseFloat(String(x).replace(',', '.'));
      return Number.isNaN(n) ? ersatz : Math.max(20, Math.min(1200, n));
    };
    PAPIERE.eigen = { name: 'Eigenes Format',
                      breite: zahl(werte.breite, jetzt.breite),
                      hoehe:  zahl(werte.hoehe,  jetzt.hoehe) };
    papier = 'eigen';
    Speicher.schreib('papier', papier);
    Speicher.schreib('papierEigen', PAPIERE.eigen);
    papierAnwenden();
    abschnittMerken(abschnittJetztNr);
    melde('Papier: ' + PAPIERE.eigen.breite + ' × ' + PAPIERE.eigen.hoehe + ' mm.');
  });
};

/* Eine Farbe ohne Fenster setzen — die Schattierungskarte braucht das,
   und die Farbtafel spaeter auch. */
B.seitenfarbeSetzen = (farbe) => {
  seitenfarbe = (!farbe || String(farbe).toLowerCase() === '#ffffff') ? '' : farbe;
  seitenfarbeAnwenden();
};

/* ============================================================
   SEITENFARBE

   In der Vorlage keine Zeile, sondern eine Tafel: Keine Farbe, dann die
   Themafarben als Gitter, die Standardfarben als Reihe, ein Verlauf,
   Automatisch, Weitere Fuellfarben, Pipette, Hintergrundbild, Anderer
   Hintergrund, Wasserzeichen.

   Dahinter lag ein Fenster mit einem einzigen Farbfeld. Wer die Seite
   hell beige haben wollte, musste die Zahl kennen.

   DIE THEMAFARBEN KOMMEN AUS DEM GEWAEHLTEN SCHEMA, nicht aus einer
   festen Liste. Das ist der Sinn von „Thema": Wer Apotheke gewaehlt hat,
   bekommt hier die Toene von Apotheke — und die Seite passt zu den
   Ueberschriften, ohne dass jemand Farben vergleicht.
   ============================================================ */
/* Die Reihe unter „Standardfarben" in der Seitenfarb-Tafel.

   In WPS stehen dort zehn Signalfarben — #FF0000, #FFFF00, reines
   Blau. Auf einem Blatt, das jemand lesen soll, hat keine davon etwas
   verloren. Hier stehen darum SEINE zwoelf Toene aus FARBEN, und
   darueber eine Reihe derselben Toene als Papierfarbe aufgehellt. */
const STANDARDFARBEN = FARBEN.map(([hex]) => hex);

/* Sechs Helligkeiten je Themafarbe — dieselbe Farbe, heller und
   dunkler. Fuer ein Blatt taugt fast nur die helle Haelfte, darum
   stehen die hellen oben. */
function themareihe(hex) {
  const [h, sa, l] = hexZuHsl(hex);
  return [0.94, 0.86, 0.76, 0.62, l, Math.max(0.12, l - 0.14)]
    .map((neu) => hslZuHex(h, sa, neu));
}

function farbfeld(hex, wie) {
  const k = document.createElement('button');
  k.type = 'button';
  k.className = 'farbtafel__feld';
  k.style.background = hex;
  k.title = hex.toUpperCase();
  k.setAttribute('aria-label', 'Seitenfarbe ' + hex.toUpperCase());
  k.addEventListener('mousedown', (e) => e.preventDefault());
  k.addEventListener('click', () => { wie(hex); });
  return k;
}

B.seitenfarbe = (knopf) => designTafelZeigen(knopf, 'Seitenfarbe', (tafel) => {
  tafel.classList.add('designtafel--breit', 'farbtafel');

  const nehmen = (hex) => {
    B.seitenfarbeSetzen(hex);
    designTafelWeg();
    melde(hex ? 'Seitenfarbe ' + hex.toUpperCase() + '.' : 'Seite wieder weiß.');
  };

  const zeile = (bild, name, tun) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'designtafel__zeile richtungszeile';
    if (SYMBOLE[bild]) k.appendChild(symbol(bild));
    const w = document.createElement('span');
    w.textContent = name;
    k.appendChild(w);
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', tun);
    return k;
  };

  tafel.appendChild(zeile('radierer', 'Keine Farbe', () => nehmen('')));

  const kopf = (text) => {
    const p = document.createElement('p');
    p.className = 'designtafel__kopfzeile';
    p.textContent = text;
    tafel.appendChild(p);
  };

  /* --- Themafarben: aus dem gewaehlten Schema --- */
  kopf('Themafarben');
  const schema = FARBSCHEMATA.find(([m]) => m === designFein.farben) || FARBSCHEMATA[0];
  const grund = schemaFelder(schema[2]);
  const gitter = document.createElement('div');
  gitter.className = 'farbtafel__gitter';
  for (let reihe = 0; reihe < 6; reihe++) {
    for (const farbe of grund) {
      gitter.appendChild(farbfeld(themareihe(farbe)[reihe], nehmen));
    }
  }
  tafel.appendChild(gitter);

  /* --- Standardfarben --- */
  kopf('Standardfarben');
  const reihe = document.createElement('div');
  reihe.className = 'farbtafel__reihe';
  for (const farbe of STANDARDFARBEN) reihe.appendChild(farbfeld(farbe, nehmen));
  tafel.appendChild(reihe);

  /* --- Verlauf ---
     In WPS ist das eine Reihe von Farbverlaeufen. Auf dem Blatt ist ein
     Verlauf selten das, was jemand will, aber er steht in der Vorlage —
     also steht er hier, und er wirkt. */
  kopf('Farbverlauf');
  const verlaufe = document.createElement('div');
  verlaufe.className = 'farbtafel__reihe';
  for (const farbe of STANDARDFARBEN) {
    const [h, sa, l] = hexZuHsl(farbe);
    const hell = hslZuHex(h, sa, Math.min(0.95, l + 0.34));
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'farbtafel__feld';
    k.style.background = 'linear-gradient(180deg, ' + hell + ', ' + farbe + ')';
    k.title = 'Verlauf';
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      seitenfarbe = 'linear-gradient(180deg, ' + hell + ', ' + farbe + ')';
      seitenfarbeAnwenden();
      designTafelWeg();
      melde('Seitenfarbe: Verlauf.');
    });
    verlaufe.appendChild(k);
  }
  tafel.appendChild(verlaufe);

  const strichel = document.createElement('hr');
  strichel.className = 'designtafel__strich';
  tafel.appendChild(strichel);

  tafel.appendChild(zeile('farbe', 'Weitere Füllfarben…', () => {
    designTafelWeg(); B.seitenfarbeFenster();
  }));
  tafel.appendChild(zeile('marker', 'Pipette', () => {
    designTafelWeg(); B.seitenfarbePipette();
  }));
  tafel.appendChild(zeile('bild', 'Hintergrundbild…', () => {
    designTafelWeg(); B.seitenbild();
  }));
  tafel.appendChild(zeile('wasserzeichen', 'Wasserzeichen…', () => {
    designTafelWeg(); B.wasserzeichen();
  }));
});

B.seitenfarbeFenster = () => {
  fenster('Seitenfarbe', [
    { art: 'satz', text: 'Färbt das Blatt. Beim Drucken kostet das Farbe —\n'
                       + 'für ein Schreiben ans Amt lieber weiß lassen.' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color',
      wert: (seitenfarbe && seitenfarbe.startsWith('#')) ? seitenfarbe : '#FFFFFF' },
  ], (werte) => {
    B.seitenfarbeSetzen(werte.farbe);
    melde(seitenfarbe ? 'Seitenfarbe gesetzt.' : 'Seite wieder weiß.');
  });
};

/* Die Pipette nimmt die Farbe von irgendwo auf dem Blatt. Der Browser
   hat dafuer ein eigenes Werkzeug; wo es fehlt, sagen wir das, statt
   einen Knopf anzubieten, der nichts tut. */
B.seitenfarbePipette = async () => {
  if (typeof EyeDropper !== 'function') {
    melde('Die Pipette gibt es in diesem Fenster nicht — „Weitere Füllfarben…" tut dasselbe von Hand.');
    return;
  }
  try {
    const griff = await new EyeDropper().open();
    B.seitenfarbeSetzen(griff.sRGBHex);
    melde('Seitenfarbe ' + griff.sRGBHex.toUpperCase() + ' aufgenommen.');
  } catch (e) {
    melde('Abgebrochen.');
  }
};

/* „Hintergrundbild" in der Vorlage. Das Bild liegt hinter dem Text und
   nimmt keine Klicks an — sonst koennte man nicht mehr schreiben. */
B.seitenbild = () => {
  const waehler = document.createElement('input');
  waehler.type = 'file';
  waehler.accept = 'image/*';
  waehler.addEventListener('change', () => {
    const datei = waehler.files && waehler.files[0];
    if (!datei) return;
    const leser = new FileReader();
    leser.onload = () => {
      seitenfarbe = 'url("' + leser.result + '") center / cover no-repeat';
      seitenfarbeAnwenden();
      melde('Hintergrundbild gesetzt. Über „Keine Farbe" wieder weg.');
    };
    leser.readAsDataURL(datei);
  });
  waehler.click();
};

let wasserzeichen = Speicher.lies('wasserzeichen', '');

function wasserzeichenAnwenden() {
  let marke = document.getElementById('wasserzeichen');
  if (!wasserzeichen) { if (marke) marke.remove(); Speicher.schreib('wasserzeichen', ''); return; }
  if (!marke) {
    marke = document.createElement('div');
    marke.id = 'wasserzeichen';
    marke.className = 'wasserzeichen';
    marke.setAttribute('aria-hidden', 'true');
    $('blatt').appendChild(marke);
  }
  marke.textContent = wasserzeichen;
  Speicher.schreib('wasserzeichen', wasserzeichen);
}

B.wasserzeichen = () => {
  fenster('Wasserzeichen', [
    { art: 'satz', text: 'Steht groß und blass quer über dem Blatt — „ENTWURF",\n„VERTRAULICH", „KOPIE". Leer lassen nimmt es weg.' },
    { schluessel: 'text', name: 'Text', wert: wasserzeichen },
  ], (werte) => {
    wasserzeichen = werte.text.trim().slice(0, 40);
    wasserzeichenAnwenden();
    melde(wasserzeichen ? 'Wasserzeichen gesetzt.' : 'Wasserzeichen entfernt.');
  });
};

/* ---- Seitenrahmen ---- */
let seitenrahmen = Speicher.lies('seitenrahmen', '');

function seitenrahmenAnwenden() {
  $('blatt').style.outline = seitenrahmen || '';
  $('blatt').style.outlineOffset = seitenrahmen ? '-8mm' : '';
  Speicher.schreib('seitenrahmen', seitenrahmen);
}

/* ============================================================
   RAHMEN UND SCHATTIERUNG

   Der Knopf „Seitenränder" rechts im Seitenlayout. In WPS oeffnet er ein
   Fenster mit drei Karten — Rahmen, Seitenrand, Schattierung — und mit
   einer Vorschau, in die man hineinklicken kann.

   Vorher lag dahinter ein Fenster mit drei Feldern, das nur die Linie um
   das ganze Blatt konnte. Alles andere, was der Knopf in der Vorlage
   verspricht — ein Rahmen um einen Absatz, eine Hinterlegung —, fehlte.

   DIE VORSCHAU IST KEINE ZIERDE. „Kontur" und „Anpassen" unterscheiden
   sich nur darin, welche der vier Kanten stehen. Ohne Bild muesste man
   das Fenster schliessen, hinsehen, wieder aufmachen.
   ============================================================ */
const RAHMEN_LINIEN = [
  ['solid',  'durchgezogen'],
  ['double', 'doppelt'],
  ['dashed', 'gestrichelt'],
  ['dotted', 'gepunktet'],
  ['groove', 'vertieft'],
  ['ridge',  'erhaben'],
];

const RAHMEN_KANTEN = [['oben', 'Oben'], ['unten', 'Unten'],
                       ['links', 'Links'], ['rechts', 'Rechts']];

let absatzrahmen = Speicher.lies('absatzrahmen',
  { art: 'solid', farbe: '#7C858E', breite: 1, kanten: ['oben', 'unten', 'links', 'rechts'] });
let blattrahmen = Speicher.lies('blattrahmen',
  { art: 'solid', farbe: '#7C858E', breite: 2, kanten: ['oben', 'unten', 'links', 'rechts'] });
let schattierung = Speicher.lies('schattierung', { farbe: '#FFF6D8', wohin: 'absatz' });

function rahmenAlsCss(r, kante) {
  if (!r.kanten.includes(kante)) return '0';
  return r.breite + 'px ' + r.art + ' ' + r.farbe;
}

function blattrahmenAnwenden() {
  const blatt = $('blatt');
  if (!blatt) return;
  const r = blattrahmen;
  const an = r.kanten.length > 0 && r.art !== 'keine';
  for (const [kante, seite] of [['oben', 'Top'], ['unten', 'Bottom'],
                                ['links', 'Left'], ['rechts', 'Right']]) {
    blatt.style['border' + seite] = an ? rahmenAlsCss(r, kante) : '';
  }
  Speicher.schreib('blattrahmen', blattrahmen);
}

/* Die Vorschau: ein Blatt mit angedeuteten Textzeilen und den Kanten,
   die gerade gesetzt sind. Ein Klick auf eine Kante schaltet sie um —
   genau wie in WPS, wo „Diagramm oder Schaltflaechen klicken" darueber
   steht. */
function rahmenVorschau(r, beiKlick) {
  const kasten = document.createElement('div');
  kasten.className = 'rahmentafel__vorschau';

  /* DER SATZ STEHT UEBER DEM KASTEN, NICHT DARIN.

     „was soll der Text da drin?" — In WPS steht die Zeile „Diagramm
     oder Schaltflaechen klicken, um Rahmen hinzuzufuegen" unter der
     Ueberschrift „Vorschau" und AUSSERHALB des Feldes. Bei mir stand
     sie im Feld, nahm ein Drittel davon weg und schob das Blatt nach
     unten.

     Eine Anleitung gehoert neben das, was sie erklaert — nicht
     hinein. */
  const satz = document.createElement('p');
  satz.className = 'rahmentafel__hinweis';
  satz.textContent = 'Auf eine Kante klicken oder einen Knopf daneben — '
                   + 'beides schaltet sie an und aus.';
  kasten.appendChild(satz);

  const feld_ = document.createElement('div');
  feld_.className = 'rahmenfeld';

  /* DIE KNOEPFE RINGS UM DIE VORSCHAU.

     „ich kann hier nicht die Rahmenlinien eintragen in der Vorschau,
     wie es WPS kann."

     Die Klickflaechen waren da — aber unsichtbar und sieben Pixel
     breit. Wer nicht weiss, dass sie da sind, findet sie nicht, und wer
     es weiss, trifft sie nicht. In WPS stehen kleine Knoepfe mit dem
     Zeichen der Kante links und unter der Vorschau. Beides gibt es
     jetzt: sichtbare Knoepfe UND die Kante selbst. */
  const gitter = document.createElement('div');
  gitter.className = 'rahmengitter';

  const blatt = document.createElement('div');
  blatt.className = 'rahmenprobe';
  for (let i = 0; i < 7; i++) {
    const zeile = document.createElement('span');
    zeile.className = 'rahmenprobe__zeile';
    blatt.appendChild(zeile);
  }

  const auffrischen = () => {
    for (const [kante, seite] of [['oben', 'Top'], ['unten', 'Bottom'],
                                  ['links', 'Left'], ['rechts', 'Right']]) {
      /* „AUS" DARF NICHT WIE EINE LINIENART AUSSEHEN.

         Die abgeschaltete Kante war gestrichelt-grau — und „gestrichelt"
         ist eine Formatvorlage, die man waehlen kann. Wer sie waehlte,
         sah dasselbe Bild wie bei „aus" und wusste nicht mehr, was gilt.
         Jetzt ist „aus" eine ganz blasse durchgezogene Linie; die gibt
         es als Wahl nicht. */
      /* DIE KANTE MUSS ZU SEHEN SEIN, AUCH WENN SIE AUS IST.

         Ich hatte sie erst gestrichelt gemacht (sah aus wie die
         Formatvorlage „gestrichelt"), dann fast durchsichtig — und
         damit unsichtbar. Man kann nicht anklicken, was man nicht
         sieht; er hat dreimal gesagt, die Funktion sei nicht da.

         In WPS zeigt die Vorschau immer einen grauen Kasten. Der ist
         der Ort zum Klicken. Eine gesetzte Kante wird darueber
         gezeichnet, in ihrer Farbe und Staerke. */
      /* GESETZT ODER NICHT — DAS MUSS MAN SEHEN.

         „wo soll ich da bitte den Rahmen sehen?"

         Ich hatte die abgeschaltete Kante erst gestrichelt gemalt (sah
         aus wie die Formatvorlage „gestrichelt"), dann fast
         durchsichtig, dann hellgrau — und jedes Mal war entweder nichts
         zu sehen oder nicht zu unterscheiden, was gilt.

         Jetzt zeichnet die abgeschaltete Kante GAR NICHTS. Wo der Platz
         zum Klicken ist, sagt ein fester duenner Umriss um das Blatt
         (im Stilblatt, als outline). Eine gesetzte Kante wird darueber
         gelegt und ist damit immer die einzige Linie am Blatt. */
      blatt.style['border' + seite] = r.kanten.includes(kante)
        ? Math.max(1, r.breite) + 'px ' + r.art + ' ' + r.farbe
        : '1px solid transparent';
    }
    for (const k of gitter.querySelectorAll('.rahmengitter__knopf')) {
      k.classList.toggle('rahmengitter__knopf--an', r.kanten.includes(k.dataset.kante));
    }
  };

  const umschalten = (kante) => {
    const drin = r.kanten.indexOf(kante);
    if (drin >= 0) r.kanten.splice(drin, 1); else r.kanten.push(kante);
    if (r.kanten.length && r.art === 'keine') r.art = 'solid';
    auffrischen();
    if (beiKlick) beiKlick();
  };

  /* Die Kante selbst bleibt anklickbar — nur breiter als vorher. */
  for (const [kante, name] of RAHMEN_KANTEN) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rahmenprobe__kante rahmenprobe__kante--' + kante;
    k.title = name + ' an- oder abschalten';
    k.setAttribute('aria-label', k.title);
    k.addEventListener('click', () => umschalten(kante));
    blatt.appendChild(k);
  }

  /* Und die sichtbaren Knoepfe: links oben und unten, unten links und
     rechts — wie auf seinem Bild. */
  const knopfBauen = (kante, zeichen, name, stelle) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rahmengitter__knopf rahmengitter__knopf--' + stelle;
    k.dataset.kante = kante;
    k.title = name;
    k.setAttribute('aria-label', name);
    k.appendChild(symbol(zeichen));
    k.addEventListener('click', () => umschalten(kante));
    return k;
  };

  const linksSpalte = document.createElement('div');
  linksSpalte.className = 'rahmengitter__seite';
  linksSpalte.append(
    knopfBauen('oben', 'kanteOben', 'Obere Rahmenlinie', 'oben'),
    knopfBauen('unten', 'kanteUnten', 'Untere Rahmenlinie', 'unten'));

  const untenReihe = document.createElement('div');
  untenReihe.className = 'rahmengitter__fuss';
  untenReihe.append(
    knopfBauen('links', 'kanteLinks', 'Linke Rahmenlinie', 'links'),
    knopfBauen('rechts', 'kanteRechts', 'Rechte Rahmenlinie', 'rechts'));

  gitter.append(linksSpalte, blatt, untenReihe);
  feld_.appendChild(gitter);
  kasten.appendChild(feld_);
  auffrischen();
  kasten.auffrischen = auffrischen;
  return kasten;
}

/* WAS IST, NICHT WAS VOREINGESTELLT IST.

   „Linien sind immer noch nicht eintragbar in der Vorschau."

   Sie waren es nicht, weil beim Oeffnen alle vier Kanten AN standen —
   ein fester Anfangswert, unabhaengig vom Absatz. Jeder Klick konnte
   also nur wegnehmen. Wer eine Linie EINTRAGEN wollte, fand nichts zum
   Eintragen: Es war schon alles voll.

   Jetzt liest das Fenster den Absatz (oder das Blatt) und zeigt dessen
   Kanten. Ein Absatz ohne Rahmen kommt leer herein — und dann traegt
   jeder Klick eine Linie ein, genau wie in WPS. */
function kantenLesen(el) {
  if (!el) return [];
  const da = [];
  for (const [kante, seite] of [['oben', 'Top'], ['unten', 'Bottom'],
                                ['links', 'Left'], ['rechts', 'Right']]) {
    const w = parseFloat(getComputedStyle(el)['border' + seite + 'Width']) || 0;
    const art = getComputedStyle(el)['border' + seite + 'Style'];
    if (w > 0 && art && art !== 'none') da.push(kante);
  }
  return da;
}

B.seitenraenderRahmen = (karteZuerst) => {
  /* Den Stand aus dem Dokument holen, bevor die Karten gebaut werden. */
  const absatzJetztEl = (typeof absatzJetzt === 'function') ? absatzJetzt() : null;
  absatzrahmen.kanten = kantenLesen(absatzJetztEl);
  blattrahmen.kanten = kantenLesen($('blatt'));

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog dialog--breit rahmentafel';
  kasten.innerHTML = '<h3 class="dialog__titel">Rahmen und Schattierung</h3>';

  const reiter = document.createElement('div');
  reiter.className = 'rahmentafel__reiter';
  const buehne = document.createElement('div');
  buehne.className = 'rahmentafel__buehne';

  const KARTEN = [
    ['rahmen',   'Rahmen',       () => karteRahmen(absatzrahmen, 'absatz')],
    ['seite',    'Seitenrand',   () => karteRahmen(blattrahmen, 'blatt')],
    ['schatten', 'Schattierung', () => karteSchatten()],
  ];

  function karteRahmen(r, wohin) {
    const k = document.createElement('div');
    k.className = 'rahmentafel__karte';

    const links = document.createElement('div');
    links.className = 'rahmentafel__spalte';
    links.innerHTML = '<h4>Einstellung</h4>';
    let vorschau = null;
    /* Fuenf Einstellungen wie auf seinem Bild. „Alle" und „Raster"
       meinen die Linien ZWISCHEN den Zellen — die gibt es nur in einer
       Tabelle. In WPS stehen sie darum grau, wenn keine da ist. Grau
       und sichtbar ist besser als weggelassen: Man sieht, dass es sie
       gibt, und warum sie hier nicht gehen. */
    const inTabelle = !!(typeof zelleOderZuletzt === 'function' && zelleOderZuletzt());
    for (const [wert, name, kanten, nurTabelle] of [
      ['ohne',    'Ohne',    [], false],
      ['kontur',  'Kontur',  ['oben', 'unten', 'links', 'rechts'], false],
      ['alle',    'Alle',    ['oben', 'unten', 'links', 'rechts'], true],
      ['raster',  'Raster',  ['oben', 'unten', 'links', 'rechts'], true],
      ['anpassen','Anpassen', null, false],
    ]) {
      const knopf = document.createElement('button');
      knopf.type = 'button';
      knopf.className = 'rahmentafel__wahl';
      knopf.textContent = name;
      if (nurTabelle && !inTabelle) {
        knopf.disabled = true;
        knopf.title = 'Gilt für die Linien zwischen Zellen — dafür muss der '
                    + 'Zeiger in einer Tabelle stehen.';
      }
      knopf.addEventListener('click', () => {
        if (kanten) r.kanten = kanten.slice();
        if (wert === 'ohne') r.art = 'keine';
        else if (r.art === 'keine') r.art = 'solid';
        r.innen = (wert === 'alle' || wert === 'raster');
        if (vorschau) vorschau.auffrischen();
      });
      links.appendChild(knopf);
    }
    k.appendChild(links);

    const mitte = document.createElement('div');
    mitte.className = 'rahmentafel__spalte';
    mitte.innerHTML = '<h4>Formatvorlage</h4>';

    const liste = document.createElement('div');
    liste.className = 'rahmentafel__linien';
    for (const [wert, name] of RAHMEN_LINIEN) {
      const z = document.createElement('button');
      z.type = 'button';
      z.className = 'rahmentafel__linie';
      z.title = name;
      const strich = document.createElement('span');
      strich.style.borderTop = '3px ' + wert + ' currentColor';
      z.appendChild(strich);
      const wort = document.createElement('em');
      wort.textContent = name;
      z.appendChild(wort);
      z.addEventListener('click', () => {
        r.art = wert;
        if (!r.kanten.length) r.kanten = ['oben', 'unten', 'links', 'rechts'];
        [...liste.children].forEach((c) => c.classList.remove('rahmentafel__linie--an'));
        z.classList.add('rahmentafel__linie--an');
        if (vorschau) vorschau.auffrischen();
      });
      if (r.art === wert) z.classList.add('rahmentafel__linie--an');
      liste.appendChild(z);
    }
    mitte.appendChild(liste);

    const farbzeile = document.createElement('label');
    farbzeile.className = 'rahmentafel__feld';
    farbzeile.innerHTML = '<span>Farbe</span>';
    const farbe = document.createElement('input');
    farbe.type = 'color'; farbe.value = r.farbe;
    farbe.addEventListener('input', () => { r.farbe = farbe.value; if (vorschau) vorschau.auffrischen(); });
    farbzeile.appendChild(farbe);
    mitte.appendChild(farbzeile);

    const breitzeile = document.createElement('label');
    breitzeile.className = 'rahmentafel__feld';
    breitzeile.innerHTML = '<span>Breite</span>';
    const breit = document.createElement('input');
    breit.type = 'number'; breit.min = '0.5'; breit.max = '12'; breit.step = '0.5';
    breit.value = String(r.breite);
    breit.addEventListener('input', () => {
      r.breite = Math.max(0.5, Math.min(12, parseFloat(breit.value) || 1));
      if (vorschau) vorschau.auffrischen();
    });
    breitzeile.appendChild(breit);
    const pt = document.createElement('span');
    pt.className = 'rahmentafel__einheit'; pt.textContent = 'px';
    breitzeile.appendChild(pt);
    mitte.appendChild(breitzeile);
    k.appendChild(mitte);

    const rechts = document.createElement('div');
    rechts.className = 'rahmentafel__spalte rahmentafel__spalte--weit';
    rechts.innerHTML = '<h4>Vorschau</h4>';
    vorschau = rahmenVorschau(r);
    rechts.appendChild(vorschau);

    const wohinZeile = document.createElement('label');
    wohinZeile.className = 'rahmentafel__feld';
    wohinZeile.innerHTML = '<span>Übernehmen für</span>';
    const wahl = document.createElement('select');
    for (const [wert, name] of (wohin === 'blatt'
        ? [['dokument', 'Gesamtes Dokument'], ['abschnitt', 'Dieser Abschnitt']]
        : [['absatz', 'Absatz'], ['auswahl', 'Markierte Absätze'],
           ['zelle', 'Tabellenzelle']])) {
      const o = document.createElement('option');
      o.value = wert; o.textContent = name;
      wahl.appendChild(o);
    }
    wohinZeile.appendChild(wahl);
    rechts.appendChild(wohinZeile);
    k.appendChild(rechts);

    k.uebernehmen = () => {
      if (wohin === 'blatt') {
        blattrahmenAnwenden();
        melde(r.kanten.length && r.art !== 'keine'
          ? 'Seitenrand gesetzt.' : 'Seitenrand entfernt.');
      } else {
        const ziele = wahl.value === 'auswahl' ? absaetzeInAuswahl() : [absatzJetzt()].filter(Boolean);
        if (!ziele.length) { melde('Dafür muss der Zeiger in einem Absatz stehen.'); return; }
        for (const a of ziele) {
          for (const [kante, seite] of [['oben', 'Top'], ['unten', 'Bottom'],
                                        ['links', 'Left'], ['rechts', 'Right']]) {
            a.style['border' + seite] = (r.art === 'keine') ? '' : rahmenAlsCss(r, kante);
          }
          a.style.padding = (r.art === 'keine') ? '' : '2mm 3mm';
        }
        Speicher.schreib('absatzrahmen', absatzrahmen);
        geaendertMelden();
        melde(ziele.length === 1 ? 'Rahmen um den Absatz.'
                                 : 'Rahmen um ' + ziele.length + ' Absätze.');
      }
    };
    return k;
  }

  function karteSchatten() {
    const k = document.createElement('div');
    k.className = 'rahmentafel__karte';

    const links = document.createElement('div');
    links.className = 'rahmentafel__spalte';
    links.innerHTML = '<h4>Füllung</h4>';
    const farbe = document.createElement('input');
    farbe.type = 'color'; farbe.value = schattierung.farbe;
    links.appendChild(farbe);

    const keine = document.createElement('button');
    keine.type = 'button';
    keine.className = 'rahmentafel__wahl';
    keine.textContent = 'Keine Füllung';
    keine.addEventListener('click', () => { schattierung.farbe = ''; probe.style.background = ''; });
    links.appendChild(keine);
    k.appendChild(links);

    const rechts = document.createElement('div');
    rechts.className = 'rahmentafel__spalte rahmentafel__spalte--weit';
    rechts.innerHTML = '<h4>Vorschau</h4>';
    const probe = document.createElement('div');
    probe.className = 'rahmenprobe rahmenprobe--satt';
    probe.style.background = schattierung.farbe;
    for (let i = 0; i < 7; i++) {
      const zeile = document.createElement('span');
      zeile.className = 'rahmenprobe__zeile';
      probe.appendChild(zeile);
    }
    farbe.addEventListener('input', () => {
      schattierung.farbe = farbe.value;
      probe.style.background = farbe.value;
    });
    rechts.appendChild(probe);

    const wohinZeile = document.createElement('label');
    wohinZeile.className = 'rahmentafel__feld';
    wohinZeile.innerHTML = '<span>Übernehmen für</span>';
    const wahl = document.createElement('select');
    for (const [wert, name] of [['absatz', 'Absatz'],
                                ['auswahl', 'Markierte Absätze'],
                                ['dokument', 'Gesamtes Dokument']]) {
      const o = document.createElement('option');
      o.value = wert; o.textContent = name;
      if (schattierung.wohin === wert) o.selected = true;
      wahl.appendChild(o);
    }
    wohinZeile.appendChild(wahl);
    rechts.appendChild(wohinZeile);
    k.appendChild(rechts);

    k.uebernehmen = () => {
      schattierung.wohin = wahl.value;
      Speicher.schreib('schattierung', schattierung);
      if (wahl.value === 'dokument') {
        B.seitenfarbeSetzen(schattierung.farbe);
        melde(schattierung.farbe ? 'Seitenfarbe gesetzt.' : 'Seitenfarbe entfernt.');
        return;
      }
      const ziele = wahl.value === 'auswahl' ? absaetzeInAuswahl() : [absatzJetzt()].filter(Boolean);
      if (!ziele.length) { melde('Dafür muss der Zeiger in einem Absatz stehen.'); return; }
      for (const a of ziele) a.style.background = schattierung.farbe || '';
      geaendertMelden();
      melde(ziele.length === 1 ? 'Absatz hinterlegt.'
                               : ziele.length + ' Absätze hinterlegt.');
    };
    return k;
  }

  let offen = null;
  const zeige = (kuerzel) => {
    const eintrag = KARTEN.find(([k]) => k === kuerzel) || KARTEN[0];
    buehne.textContent = '';
    offen = eintrag[2]();
    buehne.appendChild(offen);
    [...reiter.children].forEach((c) => {
      c.classList.toggle('rahmentafel__reiter--an', c.dataset.karte === eintrag[0]);
    });
  };

  for (const [kuerzel, name] of KARTEN) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rahmentafel__reiter-knopf';
    k.dataset.karte = kuerzel;
    k.textContent = name;
    k.addEventListener('click', () => zeige(kuerzel));
    reiter.appendChild(k);
  }

  kasten.appendChild(reiter);
  kasten.appendChild(buehne);

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  ab.addEventListener('click', () => grund.remove());
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'Übernehmen';
  ok.addEventListener('click', () => {
    if (offen && offen.uebernehmen) offen.uebernehmen();
    grund.remove();
  });
  fuss.appendChild(ab); fuss.appendChild(ok);
  kasten.appendChild(fuss);

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
  zeige(karteZuerst || 'seite');
};

/* Alle Absaetze, die die Auswahl beruehrt. */
function absaetzeInAuswahl() {
  const auswahl = window.getSelection();
  if (!auswahl || auswahl.rangeCount === 0) return [];
  const alle = [...feld.querySelectorAll('p, h1, h2, h3, h4, li')];
  const drin = alle.filter((a) => auswahl.containsNode(a, true));
  if (drin.length) return drin;
  const einer = absatzJetzt();
  return einer ? [einer] : [];
}

B.seitenrahmen = () => {
  fenster('Seitenrahmen', [
    { schluessel: 'art', name: 'Linie', art: 'auswahl', werte: [
      ['keine', 'keiner'], ['solid', 'durchgezogen'], ['double', 'doppelt'], ['dashed', 'gestrichelt'],
    ] },
    { schluessel: 'staerke', name: 'Stärke (pt)', art: 'number', wert: '2', schritt: '0.5' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#7C858E' },
  ], (werte) => {
    seitenrahmen = werte.art === 'keine' ? ''
      : (parseFloat(werte.staerke) || 2) + 'pt ' + werte.art + ' ' + werte.farbe;
    seitenrahmenAnwenden();
    melde(seitenrahmen ? 'Seitenrahmen gesetzt.' : 'Seitenrahmen entfernt.');
  }, 'Anwenden');
};

/* ---- Deckblatt und leere Seite ---- */
B.deckblatt = () => {
  fenster('Deckblatt', [
    { schluessel: 'titel', name: 'Titel', wert: dateiname },
    { schluessel: 'untertitel', name: 'Untertitel', wert: '' },
    { schluessel: 'verfasser', name: 'Verfasser',
      wert: (Speicher.lies('eigenschaften', {}) || {}).verfasser || '' },
  ], (werte) => {
    const heute = new Date().toLocaleDateString('de-DE',
      { day: 'numeric', month: 'long', year: 'numeric' });
    const seite =
      '<p style="text-align:center;margin-top:60mm"><span style="font-size:28pt">'
      + alsSicher(werte.titel) + '</span></p>'
      + (werte.untertitel ? '<p style="text-align:center"><span style="font-size:16pt">'
                          + alsSicher(werte.untertitel) + '</span></p>' : '')
      + '<p style="text-align:center;margin-top:20mm">' + alsSicher(werte.verfasser) + '</p>'
      + '<p style="text-align:center">' + heute + '</p>'
      + '<p style="page-break-after:always"></p>';
    feld.insertAdjacentHTML('afterbegin', seite);
    geaendertMelden();
    melde('Deckblatt eingefügt.');
  }, 'Einfügen');
};

const alsSicher = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/* ============================================================
   LEERE SEITE

   Seine Meldung: „Funktion in Lunivo fehlerhaft, da sie lediglich nur
   Leerzeilen einfuegt, keine leeren Seiten in Hoch- und Querformat."

   Beides stimmte. Eingefuegt wurde ein Absatz mit page-break-after —
   im Druck ein Umbruch, auf dem Bildschirm nichts. Die Seitenzahl in
   der Statuszeile rechnet mit der Hoehe des Textes; ein Umbruch hat
   keine Hoehe, also blieb es bei „Seite 1 von 1". Wer eine leere Seite
   einfuegte, sah eine Leerzeile.

   In WPS wird daraus eine wirkliche zweite Seite, und der Knopf traegt
   einen Pfeil fuer Hoch- und Querformat.

   Jetzt ein Block, der so hoch ist wie eine Seite: Er ist auf dem
   Bildschirm zu sehen, er zaehlt bei den Seiten mit, und im Druck
   stehen Umbrueche davor und dahinter.
   ============================================================ */
function leereSeiteBauen(querformat) {
  const masse = PAPIERE[papier] || PAPIERE.a4;
  /* Quer heisst: die Seite liegt. Steht das Dokument hochkant, liegt
     nur diese eine Seite — dafuer tauschen Breite und Hoehe. */
  const liegt = querformat ? !quer : quer;
  const hoehe = (liegt ? masse.breite : masse.hoehe)
                - seitenrand.oben - seitenrand.unten;
  return '<div class="leereseite" contenteditable="false" data-quer="'
       + (querformat ? 'ja' : 'nein') + '" style="height:' + hoehe + 'mm"'
       + ' title="Leere Seite (' + (querformat ? 'Querformat' : 'Hochformat')
       + ') — mit Entf wieder weg"></div><p><br></p>';
}

B.leereSeite = (querformat) => {
  const huelle = document.createElement('div');
  huelle.innerHTML = leereSeiteBauen(!!querformat);
  blockEinfuegen(huelle.firstElementChild, false);
  geaendertMelden();
  /* Erst nachzaehlen, wenn der Block wirklich steht. Direkt danach
     gefragt, ist scrollHeight noch der alte — in der Statuszeile stand
     „Seite 1 von 1", waehrend die leere Seite schon zu sehen war. */
  requestAnimationFrame(() => requestAnimationFrame(zahlenAuffrischen));
  melde('Leere Seite eingefügt — '
        + (querformat ? 'Querformat' : 'Hochformat') + '. Mit Entf wieder weg.');
};

/* ============================================================
   Referenzen: Fussnoten, Zitate, Verzeichnisse

   Stehen in js/referenzen.js. Zehn Namen gehen hinein, einer kommt heraus.
   ============================================================ */
const Referenzen = REFERENZEN_BAUEN(B, {
  Speicher, feld,
  fenster:          (...a) => fenster(...a),
  melde:            (...a) => melde(...a),
  alsSicher:        (s)    => alsSicher(s),
  auswahlMerken:    ()     => auswahlMerken(),
  auswahlZurueck:   ()     => auswahlZurueck(),
  elementEinfuegen: (...a) => elementEinfuegen(...a),
  geaendertMelden:  ()     => geaendertMelden(),
});

/* ============================================================
   Aus dem Überprüfen-Tab von Word
   ============================================================ */

/* ---- Kommentare durchgehen und löschen ----
   Bisher konnte man Kommentare nur setzen. Wer zwanzig davon im Text hat,
   will sie auch der Reihe nach finden und einzeln wieder loswerden. */
let kommentarStelle = -1;

function kommentare() { return [...feld.querySelectorAll('span.kommentar')]; }

B.kommentarWeiter = () => {
  const alle = kommentare();
  if (!alle.length) { melde('Es steht kein Kommentar im Text.'); return; }
  kommentarStelle = (kommentarStelle + 1) % alle.length;
  const marke = alle[kommentarStelle];
  marke.scrollIntoView({ block: 'center' });
  marke.classList.add('kommentar--gezeigt');
  setTimeout(() => marke.classList.remove('kommentar--gezeigt'), 1500);
  melde('Kommentar ' + (kommentarStelle + 1) + ' von ' + alle.length + ': ' + marke.title);
};

B.kommentarZurueck = () => {
  const alle = kommentare();
  if (!alle.length) { melde('Es steht kein Kommentar im Text.'); return; }
  kommentarStelle = (kommentarStelle - 1 + alle.length) % alle.length;
  const marke = alle[kommentarStelle];
  marke.scrollIntoView({ block: 'center' });
  marke.classList.add('kommentar--gezeigt');
  setTimeout(() => marke.classList.remove('kommentar--gezeigt'), 1500);
  melde('Kommentar ' + (kommentarStelle + 1) + ' von ' + alle.length + ': ' + marke.title);
};

B.kommentarWeg = () => {
  const alle = kommentare();
  if (!alle.length) { melde('Es steht kein Kommentar im Text.'); return; }
  const marke = alle[Math.max(0, Math.min(kommentarStelle, alle.length - 1))];
  const text = marke.title;
  marke.remove();
  kommentarStelle = -1;
  geaendertMelden();
  melde('Kommentar gelöscht: ' + text);
};

B.kommentareAlleWeg = () => {
  const alle = kommentare();
  if (!alle.length) { melde('Es steht kein Kommentar im Text.'); return; }
  for (const marke of alle) marke.remove();
  kommentarStelle = -1;
  geaendertMelden();
  melde(alle.length + ' Kommentare gelöscht.');
};

/* ---- Einzelne Änderungen annehmen und ablehnen ----
   „Alles übernehmen" gab es schon. Wer eine Überarbeitung durchgeht, will
   aber Stelle für Stelle entscheiden. */
/* Hiess einmal „aenderungen". Weiter unten steht aber noch eine Funktion
   dieses Namens — die Rechnung, die zwei Fassungen vergleicht. Zwei
   Funktionen gleichen Namens auf derselben Ebene sind in JavaScript kein
   Fehler: Die spaetere gewinnt stillschweigend. Dadurch riefen „Naechste
   Aenderung", „Annehmen" und „Ablehnen" die Vergleichsrechnung ohne
   Argumente auf und warfen jedes Mal. Jetzt heisst jede, was sie tut. */
function verfolgteStellen() {
  return [...feld.querySelectorAll('ins.verfolgt, del.verfolgt')];
}

let aenderungStelle = -1;

function aenderungZeigen(stelle) {
  const alle = verfolgteStellen();
  if (!alle.length) { melde('Es steht keine Änderung an.'); return null; }
  aenderungStelle = (stelle + alle.length) % alle.length;
  const el = alle[aenderungStelle];
  el.scrollIntoView({ block: 'center' });
  el.classList.add('verfolgt--gezeigt');
  setTimeout(() => el.classList.remove('verfolgt--gezeigt'), 1500);
  melde('Änderung ' + (aenderungStelle + 1) + ' von ' + alle.length
      + (el.tagName === 'INS' ? ' — neu: „' : ' — gelöscht: „') + el.textContent.trim() + '"');
  return el;
}

B.aenderungWeiter = () => aenderungZeigen(aenderungStelle + 1);
B.aenderungZurueck = () => aenderungZeigen(aenderungStelle - 1);

B.aenderungAnnehmen = () => {
  const alle = verfolgteStellen();
  if (!alle.length) { melde('Es steht keine Änderung an.'); return; }
  const el = alle[Math.max(0, Math.min(aenderungStelle, alle.length - 1))];
  if (el.tagName === 'INS') el.replaceWith(...el.childNodes);
  else el.remove();
  aenderungStelle = Math.max(-1, aenderungStelle - 1);
  geaendertMelden();
  melde('Angenommen. Es bleiben ' + verfolgteStellen().length + '.');
};

B.aenderungAblehnen = () => {
  const alle = verfolgteStellen();
  if (!alle.length) { melde('Es steht keine Änderung an.'); return; }
  const el = alle[Math.max(0, Math.min(aenderungStelle, alle.length - 1))];
  if (el.tagName === 'INS') el.remove();
  else el.replaceWith(...el.childNodes);
  aenderungStelle = Math.max(-1, aenderungStelle - 1);
  geaendertMelden();
  melde('Abgelehnt. Es bleiben ' + verfolgteStellen().length + '.');
};

/* ---- Markup-Ansicht ----
   „Alle Markups" zeigt das Kommen und Gehen, „Einfaches Markup" zeigt den
   Text, wie er nach dem Annehmen aussähe. Verworfen wird dabei nichts. */
let markupZeigen = Speicher.lies('markup', true);

function markupAnwenden() {
  feld.classList.toggle('dokument--markup-schlicht', !markupZeigen);
  Speicher.schreib('markup', markupZeigen);
  menueBauen();
}
B.markupUmschalten = () => {
  markupZeigen = !markupZeigen;
  markupAnwenden();
  melde(markupZeigen ? 'Alle Markups.' : 'Einfaches Markup — so sähe der Text angenommen aus.');
};

/* ---- Sprache für die Korrekturhilfen ---- */
const SPRACHEN_PRUEFUNG = [
  ['de', 'Deutsch'], ['de-AT', 'Deutsch (Österreich)'], ['de-CH', 'Deutsch (Schweiz)'],
  ['en', 'Englisch'], ['en-GB', 'Englisch (UK)'], ['fr', 'Französisch'],
  ['es', 'Spanisch'], ['it', 'Italienisch'], ['nl', 'Niederländisch'],
  ['pl', 'Polnisch'], ['ru', 'Russisch'], ['tr', 'Türkisch'],
];

B.pruefsprache = () => {
  fenster('Sprache für die Korrekturhilfen', [
    { art: 'satz', text: 'Danach richtet sich die Rechtschreibprüfung des Systems.\n'
                       + 'Die Schreibhilfe selbst prüft weiter auf Deutsch.' },
    { schluessel: 'sprache', name: 'Sprache', art: 'auswahl', werte: SPRACHEN_PRUEFUNG,
      wert: Speicher.lies('pruefsprache', 'de') },
  ], (werte) => {
    Speicher.schreib('pruefsprache', werte.sprache);
    feld.lang = werte.sprache;
    feld.blur(); feld.focus();
    const name = (SPRACHEN_PRUEFUNG.find(([k]) => k === werte.sprache) || [, werte.sprache])[1];
    melde('Korrekturhilfen auf ' + name + '.');
  });
};

/* ---- Thesaurus ----
   Synonyme kann die Wörterliste nicht liefern — sie weiß, wie Wörter
   geschrieben werden, nicht was sie bedeuten. Dafür ist die KI da. */
B.thesaurus = async () => {
  const stelle = wortAnPunktAusAuswahl();
  if (!stelle) { melde('Erst ein Wort markieren oder den Zeiger hineinsetzen.'); return; }

  if (!KI.verfuegbar()) {
    melde('Für Synonyme fehlt der KI-Schlüssel — Schreibhilfe → Einstellungen (F9).');
    Einstellungen.oeffnen();
    return;
  }

  melde('Suche Wörter für „' + stelle.wort + '" …');
  const ergebnis = await KI.synonyme(stelle.wort, Dokument.lies().text.slice(
    Math.max(0, stelle.textVon - 120), stelle.textVon + 120));
  if (ergebnis.fehler) { melde(ergebnis.fehler); return; }
  if (!ergebnis.woerter.length) { melde('Dazu ist der KI nichts eingefallen.'); return; }

  fenster('Wörter für „' + stelle.wort + '"', [
    { art: 'satz', text: 'Ausgewählt wird das Wort im Text ersetzt.' },
    { schluessel: 'wort', name: 'Statt dessen', art: 'auswahl',
      werte: ergebnis.woerter.map((w) => [w, w]) },
  ], (werte) => {
    wortErsetzen(stelle, wieGeschrieben(stelle.wort, werte.wort));
    melde('„' + stelle.wort + '" zu „' + werte.wort + '" geändert.');
  }, 'Ersetzen');
};

/* Das Wort an der Schreibstelle — ohne Maus, für Menü und Tastatur. */
function wortAnPunktAusAuswahl() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return null;
  const bereich = auswahl.getRangeAt(0);
  const knoten = bereich.startContainer;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return null;

  const text = knoten.data;
  let von = Math.min(bereich.startOffset, text.length);
  let bis = auswahl.isCollapsed ? von : Math.min(bereich.endOffset, text.length);
  while (von > 0 && IST_WORTZEICHEN.test(text[von - 1])) von--;
  while (bis < text.length && IST_WORTZEICHEN.test(text[bis])) bis++;
  if (bis <= von) return null;
  return { knoten, von, bis, wort: text.slice(von, bis), textVon: von };
}

/* ============================================================
   Aus dem Ansicht-Tab von Word
   ============================================================ */

/* ---- Lesemodus ----
   Alles weg, was nicht der Text ist: Leisten, Seitenleiste, Statuszeile.
   Zum Lesen, nicht zum Schreiben — deshalb ist das Blatt dabei gesperrt. */
let lesemodus = false;

B.lesemodus = () => {
  lesemodus = !lesemodus;
  document.body.classList.toggle('lesen', lesemodus);
  feld.contentEditable = lesemodus ? 'false' : 'true';
  melde(lesemodus ? 'Lesemodus — Escape beendet ihn.' : 'Lesemodus beendet.');
  menueBauen();
  if (typeof statuszeileAuffrischen === 'function') statuszeileAuffrischen();
};

/* ============================================================
   Textbausteine

   Stehen in js/bausteine.js. Was sie von hier brauchen, steht in dieser
   Aufstellung und nur hier — acht Namen. Die meisten als Funktion, denn es
   gibt sie weiter unten erst.
   ============================================================ */
const Bausteine = BAUSTEINE_BAUEN(B, {
  Speicher, feld,
  fenster:         (...a) => fenster(...a),
  melde:           (...a) => melde(...a),
  alsSicher:       (s)    => alsSicher(s),
  auswahlMerken:   ()     => auswahlMerken(),
  auswahlZurueck:  ()     => auswahlZurueck(),
  /* Eine Abfrage, kein Wert: Was markiert war, aendert sich zwischen dem
     Bauen und dem Klick auf „Aus Markierung". */
  gemerkteAuswahl: ()     => gemerkteAuswahl,
});

/* ============================================================
   Lesehilfe — was das Lesen am Bildschirm erleichtert

   Vier Dinge, die in jedem Ratgeber für Legasthenie ganz oben stehen:
   kein reines Weiß, mehr Luft zwischen Buchstaben und Wörtern, mehr Luft
   zwischen den Zeilen, und eine Hervorhebung der Zeile, in der man gerade
   ist.

   Sie ändern das Dokument NICHT. Kein Buchstabe der Datei wird davon
   anders, und auf dem Papier steht nachher, was dort stehen soll — der
   Ausdruck wird aus dem Text gebaut, nicht aus dieser Ansicht. Das ist der
   Unterschied zu „Seitenfarbe": Die färbt das Papier und kostet Tinte.
   Hier wird nur der Schirm freundlicher.
   ============================================================ */
const PAPIERTOENE = [
  ['weiss', 'Weiß', ''],
  ['creme', 'Creme', '#FBF6EC'],
  ['sand', 'Sandgrau', '#F2EFE9'],
  ['gelb', 'Blassgelb', '#FCF8DC'],
  ['blau', 'Blassblau', '#EDF4FA'],
  ['gruen', 'Blassgrün', '#EEF6EE'],
  ['rosa', 'Blassrosa', '#FBF0F2'],
];

const ABSTUFUNG = [
  ['keine', 'normal', 0],
  ['etwas', 'etwas mehr', 1],
  ['mehr', 'deutlich mehr', 2],
  ['viel', 'sehr viel', 3],
];

let lesehilfe = Object.assign(
  { ton: 'weiss', zeichen: 'keine', wort: 'keine', zeilen: 'keine',
    fokus: false, groesser: 'keine', zurueck: 'keine' },
  Speicher.lies('lesehilfe', {}));

/* ------------------------------------------------------------
   DIE DREI LESESTUFEN

   Sieben Einstellungen ergeben zusammen ein Schriftbild. Wer weiß, was
   „Buchstabenabstand: deutlich mehr" mit einem Text macht, stellt sie
   einzeln. Wer es nicht weiß — und das ist die Zielgruppe dieses
   Programms —, muss sie erst einzeln ausprobieren, um herauszufinden, was
   ihm hilft. Sechs Klappfelder sind dafür der falsche Anfang.

   Deshalb drei fertige Stufen. Sie stellen dieselben Felder, die man auch
   von Hand stellen kann, und sie sind KEIN Käfig: Jedes Feld bleibt
   darunter stehen und veränderbar. Wer eines anfasst, steht auf „Eigene
   Einstellung", und keine Stufe ist mehr angekreuzt — nichts wird
   versteckt, nichts geht verloren.

   WARUM „SEHR LEICHT LESEN" NICHT DEN HÄRTESTEN WERT NIMMT

   Bei „Übriger Text" gibt es „deutlich blasser" (0,38). In der Probe war
   zu sehen, was das heißt: Die Nachbarabsätze sind fast weg. Als Maximum
   von Hand ist das richtig — als Voreinstellung, die jemand anklickt,
   ohne zu wissen, was kommt, ist es zu viel. Die Stufe nimmt deshalb
   „etwas blasser"; der harte Wert bleibt eine Handbreite entfernt.

   WAS DIE STUFEN NICHT ANFASSEN: die Schrift. Sie steht ohnehin schon auf
   OpenDyslexic (siehe schriftJetzt weiter unten) — und hat jemand für ein
   Schreiben bewusst eine andere gewählt, hat eine Darstellungsstufe sie
   nicht hinter seinem Rücken zurückzustellen.
   ------------------------------------------------------------ */
const LESESTUFEN = [
  ['standard', 'Standard',
   { ton: 'weiss', zeichen: 'keine', wort: 'keine', zeilen: 'keine',
     groesser: 'keine', zurueck: 'keine' }],
  ['leichter', 'Leichter lesen',
   { ton: 'creme', zeichen: 'etwas', wort: 'etwas', zeilen: 'etwas',
     groesser: 'etwas', zurueck: 'etwas' }],
  ['sehr', 'Sehr leicht lesen',
   { ton: 'gelb', zeichen: 'mehr', wort: 'mehr', zeilen: 'viel',
     groesser: 'deutlich', zurueck: 'etwas' }],
];

/* Auf welcher Stufe steht die Lesehilfe gerade — oder auf keiner.

   Gefragt wird nur nach den Feldern, die eine Stufe stellt. Der
   Zeilenfokus gehört nicht dazu: Er ist ein eigener Schalter, und wer ihn
   anhat, soll deswegen nicht aus seiner Stufe fallen. */
function lesestufeJetzt() {
  const treffer = LESESTUFEN.find(([, , werte]) =>
    Object.keys(werte).every((feld) => lesehilfe[feld] === werte[feld]));
  return treffer ? treffer[0] : '';
}

function lesestufeSetzen(marke) {
  const stufe = LESESTUFEN.find(([m]) => m === marke);
  if (!stufe) return;
  Object.assign(lesehilfe, stufe[2]);
  lesehilfeAnwenden();
  Speicher.schreib('lesehilfe', lesehilfe);
}

/* Wie stark der Absatz wächst, in dem der Zeiger steht. Vergrößert wird
   mit „transform" und nicht mit einer größeren Schrift: Eine größere
   Schrift bricht anders um, die Zeile wird eine andere, der Zeiger
   springt — und das schaukelt sich beim Tippen auf. Eine Verzerrung
   verschiebt nichts; sie zeichnet nur größer.

   Gewachsen wird aus der Mitte heraus. Der Text ragt dann links und
   rechts in den Seitenrand, und der ist leer: Bei 2 cm Rand und 5 %
   Wachstum sind das gut 4 mm je Seite — es bleibt auf dem Blatt. */
const VERGROESSERN = [
  ['keine', 'nicht vergrößern', 1],
  ['etwas', 'etwas größer', 1.05],
  ['deutlich', 'deutlich größer', 1.10],
];

/* Hervorheben wirkt erst, wenn das Übrige zurücktritt. Ein Absatz, der
   fünf Prozent größer ist, fällt zwischen zwanzig gleich lauten kaum auf;
   zwischen zwanzig leisen sofort. Deshalb die Gegenrichtung: Was gerade
   nicht bearbeitet wird, wird blasser — lesbar bleibt es, aber es drängt
   sich nicht mehr vor. */
const ZURUECKNEHMEN = [
  ['keine', 'gleich lassen', 1],
  ['etwas', 'etwas blasser', 0.62],
  ['deutlich', 'deutlich blasser', 0.38],
];

function lesehilfeAnwenden() {
  const blatt = $('blatt');
  const ton = PAPIERTOENE.find(([m]) => m === lesehilfe.ton);
  /* Die Seitenfarbe gehört dem Dokument und hat Vorrang: Wer sein Blatt
     absichtlich blau gefärbt hat, soll es blau sehen. */
  blatt.style.background = seitenfarbe || (ton ? ton[2] : '') || '';

  /* Die drei Abstände hingen bisher am Feld und wurden vererbt. Vererbung
     ist aber das Schwächste, was es gibt: Ein Absatz, dem die Leiste
     „Zeilen 1,5" mitgegeben hat, trägt seinen eigenen Zeilenabstand im
     style-Attribut — und der schlägt jede Vererbung. Dieselbe Falle stellt
     jedes eingefügte Dokument, das seine Abstände mitbringt.

     Wer am Bildschirm mehr Luft braucht, hat sie dann genau dort nicht, wo
     der Text schon einmal angefasst wurde, und die Einstellung sieht aus,
     als täte sie nichts. Deshalb geht sie jetzt über eine Regel mit
     „!important" an die Absätze selbst — die schlägt auch das
     style-Attribut. Das Dokument bleibt unangetastet: Die Regel greift nur,
     solange die Auszeichnung am Feld hängt, und die steht in keiner Datei. */
  const stufe = (marke) => (ABSTUFUNG.find(([m]) => m === marke) || ABSTUFUNG[0])[2];
  feld.style.setProperty('--lese-zeichen',
    stufe(lesehilfe.zeichen) ? (stufe(lesehilfe.zeichen) * 0.03) + 'em' : 'normal');
  feld.style.setProperty('--lese-wort',
    stufe(lesehilfe.wort) ? (stufe(lesehilfe.wort) * 0.12) + 'em' : 'normal');
  feld.style.setProperty('--lese-zeilen',
    stufe(lesehilfe.zeilen) ? (1.55 + stufe(lesehilfe.zeilen) * 0.22).toFixed(2) : '1.55');
  feld.classList.toggle('dokument--abstaende',
    !!(stufe(lesehilfe.zeichen) || stufe(lesehilfe.wort) || stufe(lesehilfe.zeilen)));

  const wachstum = (VERGROESSERN.find(([m]) => m === lesehilfe.groesser)
                    || VERGROESSERN[0])[2];
  feld.style.setProperty('--fokus-wachstum', wachstum);

  const blasse = (ZURUECKNEHMEN.find(([m]) => m === lesehilfe.zurueck)
                  || ZURUECKNEHMEN[0])[2];
  feld.style.setProperty('--rest-blaesse', blasse);
  /* Ob wirklich zurückgetreten wird, entscheidet absatzFokusSetzen(): Es
     weiß als Einziges, ob es überhaupt etwas gibt, wovor der Rest
     zurücktreten könnte. */

  document.body.classList.toggle('lesehilfe--fokus', !!lesehilfe.fokus);
  if (!lesehilfe.fokus) fokusBalkenWeg();
  else fokusBalkenSetzen();
  absatzFokusSetzen();

  Speicher.schreib('lesehilfe', lesehilfe);
  menueBauen();
}

/* ---- Der Zeilenfokus ----
   Eine Zeile ist im Fließtext kein Element — sie entsteht erst beim
   Umbrechen. Deshalb wird sie nicht eingefärbt, sondern ein Balken
   dahintergelegt: Aus den Rechtecken des Absatzes wird das gesucht, in dem
   der Zeiger steht.

   Der Balken liegt im Blatt und nicht im Text. Im Text stünde er in der
   Datei, sobald jemand speichert. */
let fokusBalken = null;

function fokusBalkenWeg() {
  if (fokusBalken) { fokusBalken.remove(); fokusBalken = null; }
}

function fokusBalkenSetzen() {
  if (!lesehilfe.fokus) return;
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || !feld.contains(auswahl.anchorNode)) { fokusBalkenWeg(); return; }

  const bereich = auswahl.getRangeAt(0).cloneRange();
  bereich.collapse(true);
  let kasten = bereich.getClientRects()[0];
  if (!kasten) {
    /* Am Zeilenanfang und in leeren Absätzen liefert ein
       zusammengeklappter Bereich kein Rechteck. Dann fragen wir den
       Absatz, in dem wir stehen. */
    let knoten = auswahl.anchorNode;
    while (knoten && knoten.nodeType !== Node.ELEMENT_NODE) knoten = knoten.parentNode;
    if (!knoten || knoten === feld) { fokusBalkenWeg(); return; }
    kasten = knoten.getClientRects()[0];
    if (!kasten) { fokusBalkenWeg(); return; }
  }

  const blatt = $('blatt');
  if (!fokusBalken) {
    fokusBalken = document.createElement('div');
    fokusBalken.className = 'fokusbalken';
    fokusBalken.setAttribute('aria-hidden', 'true');
    blatt.appendChild(fokusBalken);
  }
  const rBlatt = blatt.getBoundingClientRect();
  /* Das Blatt kann vergrößert sein; die Rechtecke kommen in Bildpunkten
     des Schirms, der Balken sitzt im vergrößerten Blatt. */
  const skala = zoom / 100;
  fokusBalken.style.top = ((kasten.top - rBlatt.top) / skala - 2) + 'px';
  fokusBalken.style.height = (kasten.height / skala + 4) + 'px';
}

/* ---- Der Absatz, in dem geschrieben wird ----
   Er bekommt eine Auszeichnung, das Stilblatt macht daraus die Größe.
   Gesucht wird das Kind von „feld", in dem der Zeiger steht — nicht das
   innerste Element: Ein fett gesetztes Wort ist kein Absatz.

   Ein leerer Absatz zählt nicht. In einer leeren Zeile gibt es nichts zu
   vergrößern, und wenn trotzdem der ganze übrige Text zurückträte, bliebe
   von der Einstellung nur eines übrig: Alles ist blasser geworden und
   nichts steht hervor. Genau so sah es aus, als wäre die Lesehilfe kaputt.
   Deshalb entscheidet sich hier — und nicht schon beim Anwenden —, ob
   zurückgetreten wird: Zurücktreten gibt es nur, wo auch etwas hervortritt. */
function absatzFokusSetzen() {
  const vorher = feld.querySelector('.absatz--fokus');
  const blasse = (ZURUECKNEHMEN.find(([m]) => m === lesehilfe.zurueck)
                  || ZURUECKNEHMEN[0])[2];
  const an = (lesehilfe.groesser && lesehilfe.groesser !== 'keine') || blasse < 1;
  if (!an) {
    if (vorher) vorher.classList.remove('absatz--fokus');
    feld.classList.remove('dokument--fokus');
    return;
  }

  const auswahl = window.getSelection();
  let knoten = auswahl.rangeCount ? auswahl.anchorNode : null;
  while (knoten && knoten.parentNode !== feld) knoten = knoten.parentNode;
  let absatz = (knoten && knoten.nodeType === Node.ELEMENT_NODE) ? knoten : null;
  if (absatz && !absatz.textContent.trim()) absatz = null;

  feld.classList.toggle('dokument--fokus', blasse < 1 && !!absatz);
  if (vorher === absatz) return;
  if (vorher) vorher.classList.remove('absatz--fokus');
  if (absatz) absatz.classList.add('absatz--fokus');
}

let fokusUhr = null;
function fokusAuffrischen() {
  if (fokusUhr) return;
  if (!lesehilfe.fokus
      && (!lesehilfe.groesser || lesehilfe.groesser === 'keine')
      && (!lesehilfe.zurueck || lesehilfe.zurueck === 'keine')) return;
  fokusUhr = setTimeout(() => {
    fokusUhr = null;
    absatzFokusSetzen();
    fokusBalkenSetzen();
  }, 0);
}

/* Was gerade gilt, in einem Satz. „Gesetzt" allein sagte nur, dass ein Knopf
   gedrückt wurde — nicht, ob überhaupt etwas eingestellt ist. Wer alle sieben
   Felder auf „normal" stehen lässt und dann nichts sieht, soll lesen können,
   woran es liegt. */
function lesehilfeSatz() {
  const nameVon = (liste, marke) => {
    const eintrag = liste.find(([m]) => m === marke);
    return eintrag ? eintrag[1] : '';
  };
  const teile = [];
  if (lesehilfe.ton && lesehilfe.ton !== 'weiss') teile.push(nameVon(PAPIERTOENE, lesehilfe.ton));
  if (lesehilfe.zeichen !== 'keine') teile.push('Buchstaben ' + nameVon(ABSTUFUNG, lesehilfe.zeichen));
  if (lesehilfe.wort !== 'keine') teile.push('Wörter ' + nameVon(ABSTUFUNG, lesehilfe.wort));
  if (lesehilfe.zeilen !== 'keine') teile.push('Zeilen ' + nameVon(ABSTUFUNG, lesehilfe.zeilen));
  if (lesehilfe.fokus) teile.push('Zeilenfokus');
  if (lesehilfe.groesser !== 'keine') teile.push('Absatz ' + nameVon(VERGROESSERN, lesehilfe.groesser));
  if (lesehilfe.zurueck !== 'keine') teile.push('übriger Text ' + nameVon(ZURUECKNEHMEN, lesehilfe.zurueck));
  return teile.length
    ? 'Lesehilfe: ' + teile.join(' · ') + '. Nur am Bildschirm.'
    : 'Lesehilfe: alles steht auf „normal" — am Bildschirm ändert sich dadurch nichts.';
}

B.lesehilfe = () => {
  /* Der Stand von vorher, für den Rückweg. */
  const vorher = Object.assign({}, lesehilfe);
  const setzen = (werte) => {
    lesehilfe = {
      ton: werte.ton, zeichen: werte.zeichen, wort: werte.wort,
      zeilen: werte.zeilen, fokus: werte.fokus === 'ja',
      groesser: werte.groesser, zurueck: werte.zurueck,
    };
    lesehilfeAnwenden();
  };

  fenster('Lesehilfe', [
    { art: 'satz', text: 'Erleichtert das Lesen am Bildschirm. Das Dokument bleibt, wie es ist —\n'
                       + 'auf dem Papier steht nachher nichts davon.' },
    { schluessel: 'ton', name: 'Papierton', art: 'auswahl',
      werte: PAPIERTOENE.map(([marke, name]) => [marke, name]), wert: lesehilfe.ton },
    { schluessel: 'zeichen', name: 'Buchstabenabstand', art: 'auswahl',
      werte: ABSTUFUNG.map(([marke, name]) => [marke, name]), wert: lesehilfe.zeichen },
    { schluessel: 'wort', name: 'Wortabstand', art: 'auswahl',
      werte: ABSTUFUNG.map(([marke, name]) => [marke, name]), wert: lesehilfe.wort },
    { schluessel: 'zeilen', name: 'Zeilenluft', art: 'auswahl',
      werte: ABSTUFUNG.map(([marke, name]) => [marke, name]), wert: lesehilfe.zeilen },
    { schluessel: 'fokus', name: 'Zeilenfokus', art: 'auswahl',
      werte: [['nein', 'aus'], ['ja', 'die Zeile hervorheben']],
      wert: lesehilfe.fokus ? 'ja' : 'nein' },
    { schluessel: 'groesser', name: 'Absatz beim Schreiben', art: 'auswahl',
      werte: VERGROESSERN.map(([marke, name]) => [marke, name]),
      wert: lesehilfe.groesser },
    { schluessel: 'zurueck', name: 'Übriger Text', art: 'auswahl',
      werte: ZURUECKNEHMEN.map(([marke, name]) => [marke, name]),
      wert: lesehilfe.zurueck },
  ], (werte) => {
    setzen(werte);
    melde(lesehilfeSatz());
  }, 'Übernehmen', false,
  /* Abbrechen, Escape, Klick daneben: zurück auf den Stand von vorher. */
  () => { lesehilfe = vorher; lesehilfeAnwenden(); },
  /* Und während das Fenster steht, wirkt jede Wahl sofort. */
  setzen);
};

B.zeilenfokus = () => {
  lesehilfe.fokus = !lesehilfe.fokus;
  lesehilfeAnwenden();
  melde(lesehilfe.fokus ? 'Zeilenfokus an.' : 'Zeilenfokus aus.');
};

/* ---- Netzlinien ---- */
let netzlinien = Speicher.lies('netzlinien', false);

function netzAnwenden() {
  $('blatt').classList.toggle('blatt--netz', netzlinien);
  Speicher.schreib('netzlinien', netzlinien);
  menueBauen();
}
B.netzlinien = () => {
  netzlinien = !netzlinien;
  netzAnwenden();
  melde(netzlinien ? 'Gitternetzlinien an — alle 5 mm eine Linie.'
                   : 'Gitternetzlinien aus.');
};

/* ---- Navigationsbereich ----
   Die Überschriften als Liste zum Anspringen — bei einem langen Schreiben
   der schnellste Weg zur richtigen Stelle. */
let navOffen = false;

function navBauen() {
  const kasten = $('navigation');
  const punkte = Referenzen.ueberschriftenSammeln();
  kasten.innerHTML = '<p class="navigation__titel">Überschriften</p>';

  if (!punkte.length) {
    const leer = document.createElement('p');
    leer.className = 'navigation__leer';
    leer.textContent = 'Noch keine Überschriften. Vergib welche über Formatvorlagen — '
                     + 'dann steht hier der Aufbau deines Textes.';
    kasten.appendChild(leer);
    return;
  }

  for (const punkt of punkte) {
    const zeile = document.createElement('button');
    zeile.type = 'button';
    zeile.className = 'navigation__zeile navigation__zeile--' + punkt.ebene;
    zeile.textContent = punkt.text;
    zeile.addEventListener('click', () => {
      const ziel = document.getElementById(punkt.kennung);
      if (ziel) ziel.scrollIntoView({ block: 'start' });
    });
    kasten.appendChild(zeile);
  }
}

B.navigation = () => {
  navOffen = !navOffen;
  $('navigation').hidden = !navOffen;
  if (navOffen) navBauen();
  menueBauen();
};

/* ---- Zoom-Stufen wie in Word ---- */
function zoomAufBreite() {
  const flaeche = $('arbeitsflaeche');
  const masse = PAPIERE[papier] || PAPIERE.a4;
  const breiteMm = quer ? masse.hoehe : masse.breite;
  const breitePx = breiteMm * 96 / 25.4;
  const platz = flaeche.clientWidth - 48;         // der Rand ringsum
  setzeZoom(Math.max(50, Math.min(300, Math.round(platz / breitePx * 100))));
  melde('Seitenbreite.');
}

function zoomGanzeSeite() {
  const flaeche = $('arbeitsflaeche');
  const masse = PAPIERE[papier] || PAPIERE.a4;
  const hoeheMm = quer ? masse.breite : masse.hoehe;
  const hoehePx = hoeheMm * 96 / 25.4;
  const platz = flaeche.clientHeight - 60;
  setzeZoom(Math.max(30, Math.min(300, Math.round(platz / hoehePx * 100))));
  melde('Eine Seite.');
}

B.zoomBreite = zoomAufBreite;
B.zoomSeite = zoomGanzeSeite;
B.zoomStufe = () => {
  fenster('Zoom', [
    { schluessel: 'wert', name: 'Ansicht (%)', art: 'number', wert: String(zoom), schritt: '10' },
  ], (werte) => {
    const zahl = parseInt(werte.wert, 10);
    if (zahl) { setzeZoom(zahl); melde('Ansicht ' + zoom + ' %.'); }
  });
};

/* ============================================================
   Noch aus dem Einfügen-Tab
   ============================================================ */

/* ---- WordArt ---- */
B.wordart = () => {
  const auswahl = window.getSelection();
  const markiert = auswahl.rangeCount ? auswahl.toString().trim() : '';
  auswahlMerken();
  fenster('Schmuckschrift', [
    { schluessel: 'text', name: 'Text', wert: markiert || 'Überschrift' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#2F6FB5' },
    { schluessel: 'groesse', name: 'Größe (pt)', art: 'number', wert: '36', schritt: '2' },
  ], (werte) => {
    auswahlZurueck();
    const groesse = Math.max(10, Math.min(120, parseFloat(werte.groesse) || 36));
    elementEinfuegen('<span class="wordart" style="font-size:' + groesse + 'pt;color:'
      + werte.farbe + '">' + alsSicher(werte.text) + '</span>');
    melde('Schmuckschrift eingefügt.');
  }, 'Einfügen');
};

/* ---- Initiale ----
   Der große Buchstabe am Absatzanfang. In Word „Initialen", im Buchdruck
   seit Jahrhunderten dasselbe. */
B.initiale = () => {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) { melde('Erst in den Absatz klicken.'); return; }
  let absatz = auswahl.anchorNode;
  while (absatz && absatz !== feld && absatz.parentNode !== feld) absatz = absatz.parentNode;
  if (!absatz || absatz === feld) { melde('Erst in den Absatz klicken.'); return; }

  const text = absatz.textContent;
  if (!text.trim()) { melde('Der Absatz ist leer.'); return; }
  if (absatz.querySelector('.initiale')) {
    absatz.querySelector('.initiale').outerHTML = absatz.querySelector('.initiale').textContent;
    geaendertMelden();
    melde('Initiale entfernt.');
    return;
  }

  const erster = text.trim()[0];
  const stelle = text.indexOf(erster);
  absatz.innerHTML = '<span class="initiale">' + alsSicher(erster) + '</span>'
                   + alsSicher(text.slice(stelle + 1));
  geaendertMelden();
  melde('Initiale gesetzt.');
};

/* ---- Text aus Datei ----
   Ein zweites Dokument an den Zeiger holen, ohne das erste zu verlieren. */
B.textAusDatei = async () => {
  let wahl = null;
  try {
    const antwort = await fetch(amFenster('oeffnen-dialog'), { method: 'POST' });
    if (antwort.ok) wahl = await antwort.json();
  } catch (e) { /* kein eigenes Fenster */ }

  if (!wahl || wahl.abgebrochen || !wahl.pfad) { melde('Nichts eingefügt.'); return; }

  try {
    const daten = await fetch(amFenster('lesen'));
    if (!daten.ok) throw new Error('Fehler ' + daten.status);
    const html = await Dateien.oeffne(new File([await daten.blob()], wahl.name || 'Dokument'));
    Dokument.einfuegen(html);
    melde('Eingefügt: ' + wahl.name);
  } catch (grund) {
    melde('Das ging nicht: ' + grund.message);
  }
};

/* ============================================================
   Nachgereicht: Einfügen
   ============================================================ */

/* ------------------------------------------------------------
   Ein fertiges Element an den Zeiger setzen.

   Nicht über „execCommand": Der Browser räumt dabei auf und wirft Klasse,
   Kennung und Datenfelder weg — aus <span class="zitat" data-quelle="q1">
   wurde <span style="color:…">. Für gewöhnlichen Text ist das gleichgültig,
   für Marken nicht: An ihnen hängt, dass sich ein Zitat später erneuern
   lässt oder ein Seriendruckfeld gefunden wird.

   Der Preis: Strg+Z holt diese eine Einfügung nicht zurück — der
   Rückgängig-Stapel des Browsers kennt sie nicht. Ein verlorenes Zitat
   wäre schlimmer.
   ------------------------------------------------------------ */
function elementEinfuegen(html) {
  const huelle = document.createElement('div');
  huelle.innerHTML = html;
  const teile = [...huelle.childNodes];
  if (!teile.length) return null;

  feld.focus();
  const auswahl = window.getSelection();
  let bereich;
  if (auswahl.rangeCount && feld.contains(auswahl.getRangeAt(0).startContainer)) {
    bereich = auswahl.getRangeAt(0);
    bereich.deleteContents();
  } else {
    bereich = document.createRange();
    bereich.selectNodeContents(feld);
    bereich.collapse(false);
  }

  const stueck = document.createDocumentFragment();
  for (const teil of teile) stueck.appendChild(teil);
  const letztes = stueck.lastChild;
  bereich.insertNode(stueck);

  if (letztes) {
    const danach = document.createRange();
    danach.setStartAfter(letztes);
    danach.collapse(true);
    auswahl.removeAllRanges();
    auswahl.addRange(danach);
  }
  geaendertMelden();
  return letztes;
}

/* ---- Objekte auswählen ----
   Alles, was kein Text ist, auf einmal markieren: Bilder, Formen,
   Diagramme, Tabellen. In Word heißt das „Objekte auswählen". */
B.objekteWaehlen = () => {
  const objekte = feld.querySelectorAll('img, svg, table, .textrahmen');
  if (!objekte.length) { melde('Im Text steht kein Objekt.'); return; }
  feld.classList.add('dokument--objekte');
  melde(objekte.length + (objekte.length === 1 ? ' Objekt' : ' Objekte')
      + ' hervorgehoben. Ein Klick ins Blatt hebt es wieder auf.');
  const weg = () => {
    feld.classList.remove('dokument--objekte');
    feld.removeEventListener('mousedown', weg);
  };
  feld.addEventListener('mousedown', weg);
};

/* ---- Piktogramme ----
   Ein kleiner Satz Zeichen, wie Word ihn unter „Piktogramme" führt. Als
   SVG gezeichnet, damit sie beim Vergrößern scharf bleiben und in jede
   gespeicherte Datei mitgehen. */
const PIKTOGRAMME = {
  Haus:      'M4 12L14 4l10 8v11a1 1 0 0 1-1 1h-6v-7h-6v7H5a1 1 0 0 1-1-1z',
  Brief:     'M3 6h22v16H3z M3 6l11 8 11-8',
  Telefon:   'M6 4h5l2 5-3 2a12 12 0 0 0 7 7l2-3 5 2v5a2 2 0 0 1-2 2C11 24 4 17 4 6a2 2 0 0 1 2-2z',
  Uhr:       'M14 3a11 11 0 1 0 0 22 11 11 0 0 0 0-22 M14 7v7l5 3',
  Kalender:  'M4 7h20v18H4z M4 13h20 M9 3v6 M19 3v6',
  Person:    'M14 5a5 5 0 1 0 0 10 5 5 0 0 0 0-10 M4 25a10 10 0 0 1 20 0',
  Ordner:    'M3 7h8l3 3h11v14H3z',
  Haken:     'M4 15l7 7L24 6',
  Warnung:   'M14 3l12 21H2z M14 11v6 M14 20h.01',
  Stern:     'M14 3l3.5 7.5 8 1-6 5.5 1.5 8-7-4-7 4 1.5-8-6-5.5 8-1z',
  Schloss:   'M7 13h14v11H7z M10 13V9a4 4 0 0 1 8 0v4',
  Karte:     'M14 3a7 7 0 0 1 7 7c0 5-7 15-7 15S7 15 7 10a7 7 0 0 1 7-7 M14 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4',
};

B.piktogramm = () => {
  auswahlMerken();
  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog';
  kasten.innerHTML = '<h3 class="dialog__titel">Piktogramm einfügen</h3>';

  const gitter = document.createElement('div');
  gitter.className = 'zeichengitter zeichengitter--bilder';
  for (const [name, pfad] of Object.entries(PIKTOGRAMME)) {
    const knopf = document.createElement('button');
    knopf.className = 'zeichenknopf zeichenknopf--bild';
    knopf.title = name;
    knopf.innerHTML = '<svg viewBox="0 0 28 28" width="26" height="26" fill="none" '
      + 'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
      + '<path d="' + pfad + '"/></svg>';
    knopf.addEventListener('mousedown', (e) => e.preventDefault());
    knopf.addEventListener('click', () => {
      grund.remove();
      auswahlZurueck();
      Dokument.einfuegen('<svg class="piktogramm" xmlns="http://www.w3.org/2000/svg" '
        + 'viewBox="0 0 28 28" width="22" height="22" fill="none" stroke="currentColor" '
        + 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" role="img" '
        + 'aria-label="' + name + '"><path d="' + pfad + '"/></svg>');
      melde('Piktogramm „' + name + '" eingefügt.');
    });
    gitter.appendChild(knopf);
  }
  kasten.appendChild(gitter);

  const zu = document.createElement('button');
  zu.className = 'knopf'; zu.textContent = 'Schließen';
  zu.addEventListener('click', () => { grund.remove(); auswahlZurueck(); });
  const reihe = document.createElement('div');
  reihe.className = 'dialog__knoepfe'; reihe.appendChild(zu);
  kasten.appendChild(reihe);
  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) { grund.remove(); auswahlZurueck(); } });
  document.body.appendChild(grund);
};

/* ---- SmartArt ----
   Vier Formen, die in einem Schreiben wirklich vorkommen: ein Ablauf, ein
   Kreislauf, eine Gliederung und eine Aufzählung mit Kästen. Auch das ist
   SVG und damit Teil des Textes — kein fremdes Bauteil. */
function smartartAblauf(schritte, farben) {
  farben = farben || DIAGRAMMFARBEN;
  const breite = 520;
  const hoehe = 90;
  const kasten = Math.min(120, (breite - (schritte.length - 1) * 26) / schritte.length);
  let aus = '';
  schritte.forEach((text, i) => {
    const x = i * (kasten + 26);
    aus += '<rect x="' + x + '" y="20" width="' + kasten + '" height="50" rx="7" fill="'
         + farben[i % farben.length] + '"/>'
         + '<text x="' + (x + kasten / 2) + '" y="50" text-anchor="middle" font-size="12" '
         + 'fill="#FFFFFF">' + alsText(kuerzeWort(text, 14)) + '</text>';
    if (i < schritte.length - 1) {
      const px = x + kasten + 5;
      aus += '<path d="M' + px + ',45 L' + (px + 16) + ',45 M' + (px + 10) + ',40 L'
           + (px + 16) + ',45 L' + (px + 10) + ',50" stroke="#7C858E" stroke-width="2" fill="none"/>';
    }
  });
  return svgHuelle(breite, hoehe, aus);
}

function smartartKreis(schritte, farben) {
  farben = farben || DIAGRAMMFARBEN;
  const groesse = 320;
  const mitte = groesse / 2;
  const r = 105;
  let aus = '';
  schritte.forEach((text, i) => {
    const winkel = -Math.PI / 2 + i * (Math.PI * 2 / schritte.length);
    const x = mitte + r * Math.cos(winkel);
    const y = mitte + r * Math.sin(winkel);
    aus += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="38" fill="'
         + farben[i % farben.length] + '"/>'
         + '<text x="' + x.toFixed(1) + '" y="' + (y + 4).toFixed(1) + '" text-anchor="middle" '
         + 'font-size="11" fill="#FFFFFF">' + alsText(kuerzeWort(text, 10)) + '</text>';
  });
  return svgHuelle(groesse, groesse, aus);
}

function smartartGliederung(schritte, farben) {
  farben = farben || DIAGRAMMFARBEN;
  const breite = 460;
  const hoehe = 60 + (schritte.length - 1) * 62;
  let aus = '<rect x="150" y="10" width="160" height="42" rx="7" fill="' + DIAGRAMMFARBEN[0] + '"/>'
          + '<text x="230" y="36" text-anchor="middle" font-size="12" fill="#FFFFFF">'
          + alsText(kuerzeWort(schritte[0], 20)) + '</text>';
  schritte.slice(1).forEach((text, i) => {
    const y = 72 + i * 62;
    aus += '<path d="M230,52 L230,' + (y - 8) + ' L120,' + (y - 8) + ' L120,' + y + '" '
         + 'stroke="#9AA3AB" stroke-width="2" fill="none"/>'
         + '<rect x="40" y="' + y + '" width="160" height="42" rx="7" fill="'
         + DIAGRAMMFARBEN[(i + 1) % DIAGRAMMFARBEN.length] + '"/>'
         + '<text x="120" y="' + (y + 26) + '" text-anchor="middle" font-size="12" fill="#FFFFFF">'
         + alsText(kuerzeWort(text, 20)) + '</text>';
  });
  return svgHuelle(breite, hoehe, aus);
}

function smartartListe(schritte, farben) {
  farben = farben || DIAGRAMMFARBEN;
  const breite = 460;
  const hoehe = schritte.length * 52 + 10;
  let aus = '';
  schritte.forEach((text, i) => {
    const y = i * 52 + 5;
    aus += '<rect x="0" y="' + y + '" width="' + breite + '" height="42" rx="7" fill="'
         + farben[i % farben.length] + '"/>'
         + '<text x="16" y="' + (y + 27) + '" font-size="13" fill="#FFFFFF">'
         + alsText(kuerzeWort(text, 48)) + '</text>';
  });
  return svgHuelle(breite, hoehe, aus);
}

const kuerzeWort = (t, n) => String(t).length > n ? String(t).slice(0, n - 1) + '…' : String(t);

B.smartart = () => {
  auswahlMerken();
  fenster('SmartArt', [
    { art: 'satz', text: 'Je Zeile ein Kasten. Bei der Gliederung ist die erste Zeile oben.' },
    { schluessel: 'art', name: 'Form', art: 'auswahl', werte: [
      ['ablauf', 'Ablauf (Pfeile)'], ['kreis', 'Kreislauf'],
      ['gliederung', 'Gliederung'], ['liste', 'Liste mit Kästen'],
    ] },
    { schluessel: 'text', name: 'Kästen', art: 'flaeche', zeilen: 6,
      wert: 'Antrag stellen\nUnterlagen einreichen\nBescheid abwarten' },
  ], (werte) => {
    const schritte = werte.text.split(/\r?\n/).map((z) => z.trim()).filter(Boolean).slice(0, 8);
    if (!schritte.length) { melde('Da stand keine Zeile.'); return; }
    const bauer = { ablauf: smartartAblauf, kreis: smartartKreis,
                    gliederung: smartartGliederung, liste: smartartListe }[werte.art] || smartartAblauf;
    auswahlZurueck();
    /* Die eigene Klasse trennt SmartArt vom Diagramm: Beide entstehen aus
       svgHuelle und trügen sonst denselben Namen — die Werkzeuge könnten
       nicht auseinanderhalten, was vor ihnen steht. */
    Dokument.einfuegen('<p>' + merkeQuelle(bauer(schritte), {
      art: werte.art, text: werte.text,
    }).replace('class="diagramm"', 'class="diagramm smartart"')
      + '</p><p><br></p>');
    melde('SmartArt mit ' + schritte.length + ' Kästen eingefügt.');
  }, 'Einfügen');
};

/* ---- Schnelltabellen ----
   Fertige Tabellen für das, was oft gebraucht wird: ein Kalender, eine
   Aufstellung, ein Terminplan. Wer sie von Hand baut, tippt zehn Minuten. */
const SCHNELLTABELLEN = {
  aufstellung: { name: 'Aufstellung mit Summe', bauen: () =>
    '<table><tr><th>Posten</th><th>Betrag</th></tr>'
    + '<tr><td>&nbsp;</td><td>&nbsp;</td></tr>'.repeat(4)
    + '<tr><th>Summe</th><th>&nbsp;</th></tr></table>' },
  termine: { name: 'Terminplan', bauen: () =>
    '<table><tr><th>Datum</th><th>Uhrzeit</th><th>Was</th><th>Wo</th></tr>'
    + '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>'.repeat(5)
    + '</table>' },
  kontakte: { name: 'Kontaktliste', bauen: () =>
    '<table><tr><th>Name</th><th>Telefon</th><th>E-Mail</th></tr>'
    + '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>'.repeat(5)
    + '</table>' },
  monat: { name: 'Monatskalender', bauen: () => {
    let aus = '<table><tr><th>Mo</th><th>Di</th><th>Mi</th><th>Do</th><th>Fr</th><th>Sa</th><th>So</th></tr>';
    for (let z = 0; z < 5; z++) {
      aus += '<tr>' + '<td>&nbsp;</td>'.repeat(7) + '</tr>';
    }
    return aus + '</table>';
  } },
};

B.schnelltabelle = () => {
  auswahlMerken();
  fenster('Schnelltabelle', [
    { schluessel: 'art', name: 'Vorlage', art: 'auswahl',
      werte: Object.entries(SCHNELLTABELLEN).map(([k, v]) => [k, v.name]) },
  ], (werte) => {
    const vorlage = SCHNELLTABELLEN[werte.art];
    if (!vorlage) return;
    auswahlZurueck();
    Dokument.einfuegen(vorlage.bauen() + '<p><br></p>');
    melde('„' + vorlage.name + '" eingefügt.');
  }, 'Einfügen');
};

/* ---- Schnellbausteine ----
   Angaben, die das Programm selbst kennt: Titel, Verfasser, Datum,
   Dateiname. In Word heißen sie „Felder" und stehen unter
   „Schnellbausteine". */
B.schnellbaustein = () => {
  auswahlMerken();
  const eigen = Speicher.lies('eigenschaften', { titel: '', verfasser: '', stichworte: '' });
  const heute = new Date();
  const felder = {
    titel:     ['Titel des Dokuments', eigen.titel || dateiname],
    verfasser: ['Verfasser', eigen.verfasser || '—'],
    stichworte:['Stichwörter', eigen.stichworte || '—'],
    dateiname: ['Dateiname', dateiname],
    datum:     ['Datum von heute', heute.toLocaleDateString('de-DE',
                 { day: 'numeric', month: 'long', year: 'numeric' })],
    zeit:      ['Uhrzeit', heute.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })],
    woerter:   ['Anzahl Wörter', String(Dokument.zaehle().woerter)],
  };

  fenster('Schnellbaustein einfügen', [
    { art: 'satz', text: 'Der Wert wird jetzt eingesetzt — er rechnet sich später nicht neu.' },
    { schluessel: 'feld', name: 'Angabe', art: 'auswahl',
      werte: Object.entries(felder).map(([k, [name, wert]]) => [k, name + ' — ' + wert]) },
  ], (werte) => {
    const eintrag = felder[werte.feld];
    if (!eintrag) return;
    auswahlZurueck();
    Dokument.einfuegen(alsSicher(eintrag[1]));
    melde(eintrag[0] + ' eingefügt.');
  }, 'Einfügen');
};

/* ---- Bildschirmfoto ----
   Ein Fenster ist keine Webseite: Von hier aus kommt man nicht an den
   Bildschirm. Der Rechner selbst kann es — start.py fragt ihn. */
B.screenshot = async () => {
  fenster('Bildschirmfoto', [
    { art: 'satz', text: 'Das Fenster geht kurz aus dem Weg, dann wird aufgenommen.' },
    { schluessel: 'was', name: 'Aufnehmen', art: 'auswahl', werte: [
      ['bereich', 'Bereich mit der Maus wählen'],
      ['ganz', 'Ganzer Bildschirm'],
    ] },
  ], async (werte) => {
    melde('Bildschirmfoto wird aufgenommen …');
    try {
      const antwort = await fetch('bildschirmfoto?was=' + encodeURIComponent(werte.was),
                                  { method: 'POST' });
      if (!antwort.ok) {
        let grund = 'Fehler ' + antwort.status;
        try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
        throw new Error(grund);
      }
      const bild = await antwort.blob();
      const leser = new FileReader();
      leser.onload = () => {
        Dokument.einfuegen('<img src="' + leser.result + '" alt="Bildschirmfoto" '
                         + 'style="max-width:100%">');
        melde('Bildschirmfoto eingefügt.');
      };
      leser.readAsDataURL(bild);
    } catch (grund) {
      melde('Das ging nicht: ' + grund.message);
    }
  }, 'Aufnehmen');
};

/* ---- Tabellenblatt einbetten ----
   Eine Tabellenkalkulation ist kein Text, aber ihre Zahlen gehören oft in
   einen Brief. LibreOffice kann sie lesen — also holt das Programm das
   Blatt als Tabelle herein. */
B.tabellenblatt = async () => {
  let wahl = null;
  try {
    const antwort = await fetch(amFenster('oeffnen-dialog?nur=tabellen'), { method: 'POST' });
    if (antwort.ok) wahl = await antwort.json();
  } catch (e) { /* kein eigenes Fenster */ }

  if (!wahl || wahl.abgebrochen || !wahl.pfad) { melde('Nichts eingefügt.'); return; }

  melde('Tabellenblatt wird gelesen …');
  try {
    const daten = await fetch(amFenster('lesen'));
    if (!daten.ok) throw new Error('Fehler ' + daten.status);
    const roh = await daten.blob();
    const endung = (wahl.name.match(/\.([^.]+)$/) || [, 'xlsx'])[1].toLowerCase();

    /* Über flaches ODF: Daraus liest dieses Programm ohnehin schon. */
    const fertig = await Dateien.umwandelnRoh(roh, endung, 'fodt');
    const html = Dateien.odfAlsHtml(await fertig.text());

    const hilfe = document.createElement('div');
    hilfe.innerHTML = html;
    const tabelle = hilfe.querySelector('table');
    if (!tabelle) { melde('In dieser Datei stand keine Tabelle.'); return; }

    Dokument.einfuegen(tabelle.outerHTML + '<p><br></p>');
    melde('Tabellenblatt eingefügt: ' + wahl.name);
  } catch (grund) {
    melde('Das ging nicht: ' + grund.message);
  }
};

/* ============================================================
   Nachgereicht: Entwurf und Layout
   ============================================================ */

/* ---- Design: Schriften, Farben, Wirkung ----
   Ein Design ist in Word kein Zierrat, sondern ein Paar Schriften und ein
   Satz Farben, die überall zugleich gelten. Hier ändert es die
   Formatvorlagen — also alles, was diese Vorlagen trägt. */
const DESIGNS = {
  amt:      { name: 'Amtlich',   ueber: 'Liberation Sans', text: 'Liberation Serif',
              farbe: '#1F3864', zweit: '#4C555E' },
  klassisch:{ name: 'Klassisch', ueber: 'Liberation Serif', text: 'Liberation Serif',
              farbe: '#111417', zweit: '#4C555E' },
  modern:   { name: 'Modern',    ueber: 'DejaVu Sans', text: 'DejaVu Sans',
              farbe: '#2F6FB5', zweit: '#5A6B7A' },
  warm:     { name: 'Warm',      ueber: 'Liberation Serif', text: 'Liberation Serif',
              farbe: '#7A4B15', zweit: '#6B5A46' },
  ruhig:    { name: 'Ruhig',     ueber: 'DejaVu Serif', text: 'DejaVu Serif',
              farbe: '#1F5C4A', zweit: '#4C6058' },
};

function designAnwenden(kuerzel) {
  const wie = DESIGNS[kuerzel];
  if (!wie) return;

  /* Die Vorlagen tragen die Farbe, das Blatt die Schrift: So wirkt das
     Design auf alles, was noch keine eigene Angabe hat. */
  for (const [tag, vorlage] of Object.entries(vorlagenStile)) {
    vorlage.farbe = /^h|titel/.test(tag) ? wie.farbe
                  : (tag.includes('blockquote') || tag.includes('untertitel')) ? wie.zweit
                  : '#111417';
  }
  vorlagenAnwenden();

  let blatt = document.getElementById('designblatt');
  if (!blatt) {
    blatt = document.createElement('style');
    blatt.id = 'designblatt';
    document.head.appendChild(blatt);
  }
  blatt.textContent =
    '.dokument{font-family:"' + wie.text + '",Georgia,serif}'
    + '.dokument h1,.dokument h2,.dokument h3,.dokument h4{font-family:"' + wie.ueber + '",sans-serif}';

  Speicher.schreib('design', kuerzel);
  menueBauen();
}

const setzeDesign = (kuerzel) => () => {
  designAnwenden(kuerzel);
  melde('Design „' + DESIGNS[kuerzel].name + '" — Schriften und Farben der Vorlagen geändert.');
};

let design = Speicher.lies('design', '');

/* ---- Formatvorlagensätze ----
   Dasselbe für die Größen: enger oder luftiger, ohne jede Vorlage einzeln
   anzufassen. */
const VORLAGENSAETZE = {
  eng:    { name: 'Eng',     grund: 11, sprung: 3,   abstand: 1.5 },
  normal: { name: 'Normal',  grund: 12, sprung: 4,   abstand: 2.5 },
  luftig: { name: 'Luftig',  grund: 12, sprung: 5,   abstand: 4 },
  gross:  { name: 'Groß',    grund: 14, sprung: 6,   abstand: 3.5 },
};

const setzeVorlagensatz = (kuerzel) => () => {
  const satz = VORLAGENSAETZE[kuerzel];
  if (!satz) return;
  const stufen = { p: 0, 'p.ohne-abstand': 0, blockquote: 0, pre: -1,
                   h4: 1, h3: 2, h2: 3, 'h2.untertitel': 2, h1: 5, 'h1.titel': 8 };
  for (const [tag, vorlage] of Object.entries(vorlagenStile)) {
    const stufe = stufen[tag] === undefined ? 0 : stufen[tag];
    vorlage.groesse = Math.max(8, satz.grund + stufe * satz.sprung / 2);
    vorlage.abstand = satz.abstand + (stufe > 0 ? stufe * 0.4 : 0);
  }
  vorlagenAnwenden();
  Speicher.schreib('vorlagensatz', kuerzel);
  melde('Formatvorlagensatz „' + satz.name + '".');
};

/* ---- Effekte ----
   Word nennt es „Effekte": Schatten, Kontur, Relief für Überschriften.
   Mehr als drei braucht in einem Brief niemand. */
/* ============================================================
   TEXTEFFEKTE

   Seine Meldung: „ist nach WPS-Bildvorlage auszubauen." Dahinter lag
   ein Klappfeld mit fuenf Woertern — „Schatten, Relief, Kontur,
   Leuchten". Wer wissen will, wie „Relief" aussieht, muss es
   ausprobieren, zuruecknehmen, das naechste ausprobieren.

   In WPS ist es eine Galerie: Jede Kachel zeigt ein A, so wie der Text
   danach aussieht. Genau so steht es jetzt hier — und zwoelf statt
   fuenf, weil eine Galerie mit fuenf Kacheln keine ist.
   ============================================================ */
const EFFEKTE = {
  keiner:  { name: 'kein Effekt', css: '' },
  schatten:{ name: 'Schatten',    css: 'text-shadow:1px 1px 2px rgba(0,0,0,.35)' },
  weit:    { name: 'Weiter Schatten', css: 'text-shadow:3px 4px 5px rgba(0,0,0,.4)' },
  relief:  { name: 'Relief',      css: 'text-shadow:1px 1px 0 rgba(255,255,255,.8),2px 2px 2px rgba(0,0,0,.3)' },
  vertieft:{ name: 'Vertieft',    css: 'text-shadow:-1px -1px 0 rgba(255,255,255,.7),1px 1px 2px rgba(0,0,0,.45)' },
  kontur:  { name: 'Kontur',      css: '-webkit-text-stroke:0.6px currentColor;color:transparent' },
  konturfett:{ name: 'Starke Kontur', css: '-webkit-text-stroke:1.4px currentColor;color:transparent' },
  leuchten:{ name: 'Leuchten',    css: 'text-shadow:0 0 6px rgba(47,111,181,.65)' },
  warm:    { name: 'Warmes Leuchten', css: 'text-shadow:0 0 7px rgba(200,122,30,.7)' },
  spiegel: { name: 'Spiegelung',  css: '-webkit-box-reflect:below 1px linear-gradient(transparent 55%, rgba(255,255,255,.35))' },
  verlauf: { name: 'Farbverlauf', css: 'background:linear-gradient(90deg,var(--blau),var(--warm,#C08A2E));-webkit-background-clip:text;background-clip:text;color:transparent' },
  hohl:    { name: 'Hohl mit Schatten', css: '-webkit-text-stroke:0.8px currentColor;color:transparent;text-shadow:2px 3px 3px rgba(0,0,0,.3)' },
};

/* Die Galerie: zwoelf Kacheln, jede zeigt ein A in ihrem Effekt. */
B.effekt = (knopf) => {
  auswahlMerken();
  designTafelZeigen(knopf, 'Texteffekte', (tafel) => {
    tafel.classList.add('designtafel--breit');
    const gitter = document.createElement('div');
    gitter.className = 'effektgalerie';
    for (const [kuerzel, wie] of Object.entries(EFFEKTE)) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'effektprobe';
      k.title = wie.name;
      const a = document.createElement('span');
      a.className = 'effektprobe__a';
      a.setAttribute('style', wie.css);
      a.textContent = 'Aa';
      const w = document.createElement('span');
      w.className = 'effektprobe__name';
      w.textContent = wie.name;
      k.append(a, w);
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        designTafelWeg();
        effektSetzen(kuerzel);
      });
      gitter.appendChild(k);
    }
    tafel.appendChild(gitter);

    const mehr = document.createElement('button');
    mehr.type = 'button';
    mehr.className = 'layouttafel__weiter';
    mehr.textContent = 'Eigene Farbe und Stärke…';
    mehr.addEventListener('click', () => { designTafelWeg(); B.effektFenster(); });
    tafel.appendChild(mehr);
  });
};

function effektSetzen(art) {
  auswahlZurueck();
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || auswahl.isCollapsed) {
    melde('Erst den Text markieren, der den Effekt bekommen soll.');
    return;
  }
  const wie = EFFEKTE[art];
  if (!wie || art === 'keiner') {
    Dokument.befehl('removeFormat');
    melde('Effekt entfernt.');
    return;
  }
  const huelle = document.createElement('span');
  huelle.className = 'effekt';
  huelle.setAttribute('style', wie.css);
  try {
    auswahl.getRangeAt(0).surroundContents(huelle);
    geaendertMelden();
    melde('Effekt „' + wie.name + '" gesetzt.');
  } catch (e) {
    melde('Über mehrere Absätze geht das nicht — kleiner markieren.');
  }
}

B.effektFenster = () => {
  auswahlMerken();
  fenster('Effekt', [
    { art: 'satz', text: 'Wirkt auf den markierten Text.' },
    { schluessel: 'art', name: 'Effekt', art: 'auswahl',
      werte: Object.entries(EFFEKTE).map(([k, v]) => [k, v.name]) },
  ], (werte) => effektSetzen(werte.art), 'Anwenden');
};

/* ---- Umbrüche ---- */
/* Der Textflussumbruch bricht die Zeile, ohne einen neuen Absatz zu
   beginnen — Shift+Enter. In WPS steht er zwischen Spalten- und
   Abschnittsumbruch; hier fehlte er ganz. */
B.textflussumbruch = () => {
  Dokument.einfuegen('<br>');
  melde('Zeilenumbruch gesetzt — derselbe Absatz geht weiter.');
};

B.spaltenumbruch = () => {
  Dokument.einfuegen('<span class="spaltenumbruch"></span>');
  melde('Spaltenumbruch gesetzt — er wirkt, sobald mehrere Spalten eingestellt sind.');
};

/* Die vier Arten, die Word und WPS kennen. Der Name steht am Strich,
   damit man auf dem Blatt sieht, welche es war — ein gestrichelter
   Strich allein sagt das nicht. */
const ABSCHNITTSARTEN = {
  NextPage:   ['Nächste Seite', 'Der Abschnitt beginnt auf einer neuen Seite.'],
  Continuous: ['Fortlaufend', 'Der Abschnitt beginnt auf derselben Seite.'],
  EvenPage:   ['Gerade Seite', 'Der Abschnitt beginnt auf der nächsten geraden Seite.'],
  OddPage:    ['Ungerade Seite', 'Der Abschnitt beginnt auf der nächsten ungeraden Seite.'],
};

B.abschnittsumbruch = (art = 'NextPage') => {
  if (!ABSCHNITTSARTEN[art]) art = 'NextPage';
  /* Ein Abschnitt trennt Teile mit eigenem Aussehen — etwa ein Deckblatt
     vom Rest. Sichtbar als Linie, im Druck als Seitenwechsel.

     Die Linie allein war früher alles. Jetzt entsteht dahinter ein
     wirklicher Abschnitt im Aufbau: Er erbt zunächst den Seitenaufbau des
     Abschnitts, in dem der Zeiger stand — alles andere wäre eine
     Überraschung —, lässt sich danach aber eigenständig einstellen. */
  if (Aufbau) {
    abschnittMerken(abschnittJetztNr);
    const vorher = Aufbau.getSection(abschnittJetztNr);
    const neuer = Aufbau.addSection();
    if (vorher) {
      neuer.getPageSetup().margins = Object.assign({}, vorher.getPageSetup().margins);
      neuer.getPageSetup().orientation = vorher.getPageSetup().orientation;
      neuer.getPageSetup().pageSize = JSON.parse(JSON.stringify(vorher.getPageSetup().pageSize));
      /* Die Kopfzeile läuft zunächst weiter — „Wie vorherige", wie im
         Writer. Wer sie im neuen Abschnitt anders haben will, schaltet
         das ab. */
      neuer.header.linkedToPrevious = true;
      neuer.footer.linkedToPrevious = true;
    }
    neuer.insertBreak(Dokumentmodell.SectionBreakType[art]);
    abschnitteSichern();
  }
  /* Fortlaufend heisst: kein Seitenwechsel. Das muss der Strich selbst
     wissen, sonst druckt er trotzdem eine neue Seite. */
  Dokument.einfuegen('<hr class="abschnitt" data-abschnitt="1" data-art="'
    + art + '" data-name="' + ABSCHNITTSARTEN[art][0] + '"><p><br></p>');
  melde(Aufbau ? 'Abschnitt ' + Aufbau.getSections().length + ' beginnt hier: '
                 + ABSCHNITTSARTEN[art][0] + '.'
               : 'Abschnittsumbruch: ' + ABSCHNITTSARTEN[art][0] + '.');
};

/* ---- Bilder anordnen ----
   Wie der Text um ein Bild läuft, welche Ebene es hat, wie es gedreht ist.
   In Word ist das die Gruppe „Anordnen". */
/* ============================================================
   DIE GRIFFE AM BILD

   Dasselbe wie bei den Tabellen, und aus demselben Grund: Kay hat es
   verlangt, und bei Bildern ist es noch selbstverstaendlicher. Ein Bild
   ist ein Gegenstand auf dem Blatt; man fasst es an und schiebt es
   hin. Bisher ging das nur ueber ein Fenster mit Zahlen.

   Acht Griffe ringsum wie in WPS: vier Ecken halten das Seitenverhaeltnis,
   vier Kanten ziehen nur in eine Richtung. Darueber der Griff zum Drehen,
   daneben das Kreuz zum Loeschen. Das Bild selbst ist der Griff zum
   Verschieben — man packt an, was man meint.

   Gerechnet wird in Millimetern, aus demselben Grund wie bei den
   Tabellen: Das Blatt wird gezoomt, Millimeter gelten auf dem Papier.
   ============================================================ */

const BILDGRIFFE = [
  { art: 'nw', x: 0,   y: 0,   zeiger: 'nwse-resize', name: 'Ecke oben links' },
  { art: 'n',  x: 0.5, y: 0,   zeiger: 'ns-resize',   name: 'Oberkante' },
  { art: 'ne', x: 1,   y: 0,   zeiger: 'nesw-resize', name: 'Ecke oben rechts' },
  { art: 'e',  x: 1,   y: 0.5, zeiger: 'ew-resize',   name: 'Rechte Kante' },
  { art: 'se', x: 1,   y: 1,   zeiger: 'nwse-resize', name: 'Ecke unten rechts' },
  { art: 's',  x: 0.5, y: 1,   zeiger: 'ns-resize',   name: 'Unterkante' },
  { art: 'sw', x: 0,   y: 1,   zeiger: 'nesw-resize', name: 'Ecke unten links' },
  { art: 'w',  x: 0,   y: 0.5, zeiger: 'ew-resize',   name: 'Linke Kante' },
];

let bildGriffe = {};
let bildZiel = null;
let bildUnterMaus = null;
let bildGewaehlt = null;        /* bleibt, bis woanders hingeklickt wird */

function bildGriffeWeg() {
  bildGewaehlt = null;
  for (const k of Object.values(bildGriffe)) k.remove();
  bildGriffe = {};
  bildZiel = null;
  if (bildBeobachter) { bildBeobachter.disconnect(); bildBeobachter = null; }
  bildBewacht = null;
}

function bildIstFrei(bild) {
  return bild.classList.contains('bild--frei');
}

function bildFreiMachen(bild) {
  if (bildIstFrei(bild)) return;
  const bogen = bild.closest('.dokument') || feld;
  const r = bild.getBoundingClientRect();
  const b = bogen.getBoundingClientRect();
  const massstab = (zoom || 100) / 100;
  bild.style.width = inMillimeter(r.width / massstab) + 'mm';
  bild.style.height = inMillimeter(r.height / massstab) + 'mm';
  bild.style.left = inMillimeter((r.left - b.left) / massstab) + 'mm';
  bild.style.top = inMillimeter((r.top - b.top) / massstab) + 'mm';
  bild.classList.add('bild--frei');
}

B.bildEinreihen = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild) { melde('Im Text steht kein Bild.'); return; }
  if (!bildIstFrei(bild)) { melde('Dieses Bild steht schon im Text.'); return; }
  bild.classList.remove('bild--frei');
  bild.style.left = '';
  bild.style.top = '';
  geaendertMelden();
  melde('Bild wieder im Text — es wandert jetzt wieder mit.');
  bildGriffeAuffrischen();
};

/* ------------------------------------------------------------
   SPIEGELN, DREHEN IN SCHRITTEN, FARBE

   Aus dem Abgleich mit WPS (doku/wps-tabellen-und-steuerung.md). Alle
   vier sind billig, weil das Blatt sie ohnehin kann — sie mussten nur
   erreichbar werden.

   Drehung und Spiegelung stehen zusammen in EINER transform-Angabe: Zwei
   getrennte Anweisungen ueberschreiben einander, und das Bild waere nach
   dem Spiegeln wieder gerade. Deshalb werden beide gemerkt und jedes Mal
   zusammen gesetzt.
   ------------------------------------------------------------ */
function bildVerwandlung(bild) {
  const grad = Number(bild.dataset.drehung || 0);
  const wx = bild.dataset.spiegelX === 'ja' ? -1 : 1;
  const wy = bild.dataset.spiegelY === 'ja' ? -1 : 1;
  const teile = [];
  if (grad) teile.push('rotate(' + grad + 'deg)');
  if (wx < 0 || wy < 0) teile.push('scale(' + wx + ',' + wy + ')');
  bild.style.transform = teile.join(' ');
}

function bildJetzt() {
  const b = bildZiel || bildAnStelle();
  if (!b || b.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return null; }
  return b;
}

B.bildSpiegelnWaagerecht = () => {
  const bild = bildJetzt();
  if (!bild) return;
  bild.dataset.spiegelX = bild.dataset.spiegelX === 'ja' ? 'nein' : 'ja';
  bildVerwandlung(bild);
  geaendertMelden();
  melde('Bild waagerecht gespiegelt — links und rechts vertauscht.');
  bildGriffeNachmessen();
};

B.bildSpiegelnSenkrecht = () => {
  const bild = bildJetzt();
  if (!bild) return;
  bild.dataset.spiegelY = bild.dataset.spiegelY === 'ja' ? 'nein' : 'ja';
  bildVerwandlung(bild);
  geaendertMelden();
  melde('Bild senkrecht gespiegelt — oben und unten vertauscht.');
  bildGriffeNachmessen();
};

/* Die zwei festen Knoepfe neben dem freien Drehgriff. Wer ein hochkant
   fotografiertes Blatt einfuegt, will nicht zielen muessen. */
function bildDrehenUm(grad) {
  const bild = bildJetzt();
  if (!bild) return;
  const neu = (Number(bild.dataset.drehung || 0) + grad + 360) % 360;
  bild.dataset.drehung = String(neu);
  bildVerwandlung(bild);
  geaendertMelden();
  melde('Bild steht auf ' + neu + ' Grad.');
  bildGriffeNachmessen();
}

B.bildLinks90 = () => bildDrehenUm(-90);
B.bildRechts90 = () => bildDrehenUm(90);

/* ------------------------------------------------------------
   DIE FARBE EINES BILDES

   Graustufen, Schwarzweiss, verblasst — und Helligkeit und Kontrast.
   Alles ueber CSS-Filter: Das Bild bleibt unangetastet, die Datei wird
   nicht groesser, und jeder Schritt ist ruecknehmbar.

   „Verblasst" ist der, den man wirklich braucht: Ein Bild hinter dem
   Text muss zurueckgenommen werden, sonst ist der Text nicht mehr
   lesbar — und das ist in diesem Programm kein Schoenheitsfehler. */
const BILDFARBEN = [
  ['keine',   'Wie aufgenommen', ''],
  ['grau',    'Graustufen',      'grayscale(1)'],
  ['sw',      'Schwarzweiß',     'grayscale(1) contrast(2.6)'],
  ['blass',   'Verblasst',       'opacity(.42) saturate(.6)'],
  ['warm',    'Warm',            'sepia(.45) saturate(1.3)'],
  ['kalt',    'Kühl',            'hue-rotate(-12deg) saturate(1.2)'],
];

function bildFilterSetzen(bild) {
  const grund = BILDFARBEN.find(([m]) => m === (bild.dataset.farbe || 'keine'));
  const teile = [];
  if (grund && grund[2]) teile.push(grund[2]);
  const hell = Number(bild.dataset.helligkeit || 100);
  const kontrast = Number(bild.dataset.kontrast || 100);
  if (hell !== 100) teile.push('brightness(' + (hell / 100).toFixed(2) + ')');
  if (kontrast !== 100) teile.push('contrast(' + (kontrast / 100).toFixed(2) + ')');
  bild.style.filter = teile.join(' ');
}

B.bildFarbe = () => {
  const bild = bildJetzt();
  if (!bild) return;
  fenster('Farbe des Bildes', [
    { schluessel: 'farbe', name: 'Fassung', art: 'auswahl',
      wert: bild.dataset.farbe || 'keine',
      werte: BILDFARBEN.map(([m, n]) => [m, n]) },
    { schluessel: 'hell', name: 'Helligkeit (%)', art: 'number',
      wert: String(bild.dataset.helligkeit || 100), schritt: '5' },
    { schluessel: 'kontrast', name: 'Kontrast (%)', art: 'number',
      wert: String(bild.dataset.kontrast || 100), schritt: '5' },
  ], () => {
    geaendertMelden();
    melde('Farbe übernommen.');
  }, 'Übernehmen', false,
  /* Abbrechen: zurueck auf den Stand von vorher. */
  ((alt) => () => {
    bild.dataset.farbe = alt.farbe;
    bild.dataset.helligkeit = alt.hell;
    bild.dataset.kontrast = alt.kontrast;
    bildFilterSetzen(bild);
  })({ farbe: bild.dataset.farbe || 'keine',
       hell: bild.dataset.helligkeit || '100',
       kontrast: bild.dataset.kontrast || '100' }),
  /* Und waehrend das Fenster offen steht, sofort zeigen. */
  (werte) => {
    bild.dataset.farbe = werte.farbe;
    bild.dataset.helligkeit = String(Math.max(20, Math.min(200,
      parseInt(werte.hell, 10) || 100)));
    bild.dataset.kontrast = String(Math.max(20, Math.min(200,
      parseInt(werte.kontrast, 10) || 100)));
    bildFilterSetzen(bild);
  });
};

B.bildFarbeZurueck = () => {
  const bild = bildJetzt();
  if (!bild) return;
  delete bild.dataset.farbe;
  delete bild.dataset.helligkeit;
  delete bild.dataset.kontrast;
  bild.style.filter = '';
  geaendertMelden();
  melde('Farbe zurückgesetzt.');
};

B.bildDrehenZurueck = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild) { melde('Im Text steht kein Bild.'); return; }
  bild.dataset.drehung = '0';
  delete bild.dataset.spiegelX;
  delete bild.dataset.spiegelY;
  bildVerwandlung(bild);
  geaendertMelden();
  melde('Drehung und Spiegelung zurückgesetzt.');
  bildGriffeAuffrischen();
};

B.bildGroesseZurueck = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild) { melde('Im Text steht kein Bild.'); return; }
  bild.style.width = '';
  bild.style.height = '';
  geaendertMelden();
  melde('Größe zurückgesetzt.');
  bildGriffeAuffrischen();
};

/* ------------------------------------------------------------
   DIE DREI SCHNELLKNÖPFE NEBEN DEM BILD

   Vorlage ist WPS: Neben einem gewählten Bild steht eine kleine
   senkrechte Leiste mit den drei Dingen, die man an einem Bild fast
   immer will — wie der Text drumherum läuft, wie groß es ist, und was
   davon zu sehen sein soll.

   Warum neben dem Bild und nicht nur oben in der Leiste: Es ist
   derselbe Gedanke wie beim + an der Tabelle. „Dieses Bild etwas
   kleiner" ist ein Gedanke am Ort. Der Weg nach oben verlangt, ihn zu
   übersetzen.
   ------------------------------------------------------------ */
const BILDSCHNELL = [
  { art: 'umbruch', bild: 'anordnen', name: 'Layoutoptionen — wie der Text läuft',
    tun: (k) => B.layoutoptionen(k) },
  { art: 'lupe', bild: 'lupe', name: 'Bild groß ansehen',
    tun: () => B.bildVorschau() },
  { art: 'schnitt', bild: 'schere', name: 'Zuschneiden — Winkel nach innen ziehen',
    tun: () => B.schnittModus() },
  /* KEIN VIERTER KNOPF. Ich hatte „Nach Form" hier danebengestellt — in
     WPS stehen drei, und Kay hat das Bild ein zweites Mal geschickt.
     Formen und Verhältnisse stehen im Reiter Bildtools; der Schnittmodus
     ist der Weg, den man am Bild braucht. */
];

/* ------------------------------------------------------------
   DIE LAYOUTOPTIONEN

   Die kleine Tafel, die in WPS am ersten Schnellknopf aufgeht. Sie
   zeigt den Textumbruch als BILDER, nicht als Wörter — und das ist der
   ganze Punkt: „Quadrat", „Eng", „Transparent" sagt niemandem etwas,
   ein Bildchen mit Text drumherum sofort.

   Darunter die zwei Knöpfe, die es in WPS auch gibt: Wandert das Bild
   mit dem Text mit, oder bleibt es auf der Seite stehen?
   ------------------------------------------------------------ */
const UMBRUCH_ARTEN = [
  { art: 'zeile',  name: 'Mit Text in Zeile',
    satz: 'Das Bild steht wie ein großer Buchstabe mitten im Text.' },
  { art: 'links',  name: 'Rechts umfließen',
    satz: 'Das Bild steht links, der Text läuft rechts daran vorbei.' },
  { art: 'rechts', name: 'Links umfließen',
    satz: 'Das Bild steht rechts, der Text läuft links daran vorbei.' },
  { art: 'oben',   name: 'Oben und unten',
    satz: 'Der Text hört über dem Bild auf und geht darunter weiter.' },
  { art: 'hinter', name: 'Hinter dem Text',
    satz: 'Das Bild liegt unter dem Text — für Hintergründe.' },
  { art: 'vor',    name: 'Vor dem Text',
    satz: 'Das Bild liegt über dem Text und verdeckt ihn.' },
];

/* Ein kleines Bild des Umbruchs: graue Zeilen, ein blauer Kasten. So
   sieht man in einem Blick, was passiert. */
function umbruchBildchen(art) {
  const zeile = (x, y, b) =>
    '<rect x="' + x + '" y="' + y + '" width="' + b + '" height="2.4" rx="1.2"/>';
  let text = '';
  let kasten = '';
  if (art === 'zeile') {
    text = zeile(2, 3, 40) + zeile(2, 9, 40) + zeile(20, 15, 22) + zeile(2, 27, 40);
    kasten = '<rect x="2" y="13" width="15" height="9" rx="1.5" class="uv-kasten"/>';
  } else if (art === 'links') {
    text = zeile(20, 3, 22) + zeile(20, 9, 22) + zeile(20, 15, 22) + zeile(2, 27, 40);
    kasten = '<rect x="2" y="3" width="15" height="18" rx="1.5" class="uv-kasten"/>';
  } else if (art === 'rechts') {
    text = zeile(2, 3, 22) + zeile(2, 9, 22) + zeile(2, 15, 22) + zeile(2, 27, 40);
    kasten = '<rect x="27" y="3" width="15" height="18" rx="1.5" class="uv-kasten"/>';
  } else if (art === 'oben') {
    text = zeile(2, 3, 40) + zeile(2, 27, 40);
    kasten = '<rect x="10" y="9" width="24" height="12" rx="1.5" class="uv-kasten"/>';
  } else {
    text = zeile(2, 3, 40) + zeile(2, 9, 40) + zeile(2, 15, 40) + zeile(2, 21, 40)
         + zeile(2, 27, 40);
    kasten = '<rect x="12" y="7" width="20" height="17" rx="1.5" class="uv-kasten"'
           + (art === 'hinter' ? ' opacity=".45"' : '') + '/>';
  }
  const reihenfolge = art === 'hinter' ? kasten + text : text + kasten;
  return '<svg viewBox="0 0 44 32" class="uv-bild"><g class="uv-zeilen">'
       + (art === 'hinter' ? '' : '') + reihenfolge + '</g></svg>';
}

function bildUmbruchJetzt(bild) {
  for (const k of ['links', 'rechts', 'oben', 'hinter', 'vor']) {
    if (bild.classList.contains('bild--' + k)) return k;
  }
  return 'zeile';
}

function bildUmbruchSetzen(bild, art) {
  for (const k of ['links', 'rechts', 'oben', 'hinter', 'vor']) {
    bild.classList.remove('bild--' + k);
  }
  if (art !== 'zeile') bild.classList.add('bild--' + art);
  /* „Mit Text in Zeile" und ein schwebendes Bild schliessen einander aus:
     Was im Textfluss steht, kann nicht gleichzeitig frei liegen. */
  if (art === 'zeile' && bildIstFrei(bild)) {
    bild.classList.remove('bild--frei');
    bild.style.left = '';
    bild.style.top = '';
  }
  geaendertMelden();
  bildGriffeNachmessen();
}

let layoutTafel = null;

function layoutTafelWeg() {
  if (layoutTafel) { layoutTafel.remove(); layoutTafel = null; }
}

B.layoutoptionen = (knopf) => {
  const bild = bildZiel || bildAnStelle();
  if (!bild || bild.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return; }
  if (layoutTafel) { layoutTafelWeg(); return; }

  const tafel = document.createElement('div');
  tafel.className = 'layouttafel';

  const kopf = document.createElement('div');
  kopf.className = 'layouttafel__kopf';
  const titel = document.createElement('span');
  titel.textContent = 'Layoutoptionen';
  const zu = document.createElement('button');
  zu.type = 'button';
  zu.className = 'layouttafel__zu';
  zu.textContent = '×';
  zu.title = 'Schließen';
  zu.addEventListener('click', layoutTafelWeg);
  kopf.append(titel, zu);
  tafel.appendChild(kopf);

  const satzzeile = document.createElement('p');
  satzzeile.className = 'layouttafel__satz';

  const gruppe = (name, arten) => {
    const h = document.createElement('p');
    h.className = 'layouttafel__gruppe';
    h.textContent = name;
    tafel.appendChild(h);
    const kasten = document.createElement('div');
    kasten.className = 'layouttafel__gitter';
    for (const art of arten) {
      const eintrag = UMBRUCH_ARTEN.find((u) => u.art === art);
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'layouttafel__wahl';
      k.title = eintrag.name;
      k.setAttribute('aria-label', eintrag.name);
      k.innerHTML = umbruchBildchen(art);
      if (bildUmbruchJetzt(bild) === art) k.classList.add('layouttafel__wahl--an');
      k.addEventListener('mouseenter', () => { satzzeile.textContent = eintrag.satz; });
      k.addEventListener('focus', () => { satzzeile.textContent = eintrag.satz; });
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => {
        bildUmbruchSetzen(bild, art);
        for (const anderer of tafel.querySelectorAll('.layouttafel__wahl')) {
          anderer.classList.remove('layouttafel__wahl--an');
        }
        k.classList.add('layouttafel__wahl--an');
        melde(eintrag.name + ' — ' + eintrag.satz);
      });
      kasten.appendChild(k);
    }
    tafel.appendChild(kasten);
  };

  gruppe('Mit Text in Zeile', ['zeile']);
  gruppe('Zeilenumbruch', ['links', 'rechts', 'oben', 'hinter', 'vor']);

  tafel.appendChild(satzzeile);
  satzzeile.textContent = UMBRUCH_ARTEN.find(
    (u) => u.art === bildUmbruchJetzt(bild)).satz;

  /* Die zwei Knöpfe aus WPS: Wandert das Bild mit dem Text mit, oder
     bleibt es stehen, wo es liegt? */
  const strich = document.createElement('div');
  strich.className = 'layouttafel__strich';
  tafel.appendChild(strich);

  const wahlKasten = document.createElement('div');
  wahlKasten.className = 'layouttafel__stellung';
  for (const [wert, name, satz] of [
    ['mit', 'Mit Text verschieben',
     'Fügst du oberhalb Zeilen ein, wandert das Bild mit nach unten.'],
    ['fest', 'Fester Text',
     'Das Bild bleibt auf der Seite stehen, egal was darüber geschrieben wird.'],
  ]) {
    const l = document.createElement('label');
    const r = document.createElement('input');
    r.type = 'radio';
    r.name = 'bild-stellung';
    r.checked = (wert === 'fest') === bildIstFrei(bild);
    r.addEventListener('change', () => {
      if (wert === 'fest') bildFreiMachen(bild);
      else B.bildEinreihen();
      melde(satz);
    });
    const t = document.createElement('span');
    t.textContent = name;
    l.append(r, t);
    wahlKasten.appendChild(l);
  }
  tafel.appendChild(wahlKasten);

  document.body.appendChild(tafel);
  layoutTafel = tafel;

  const r = (knopf && knopf.getBoundingClientRect)
    ? knopf.getBoundingClientRect() : bild.getBoundingClientRect();
  const m = tafel.getBoundingClientRect();
  let links = r.right + 8;
  if (links + m.width > window.innerWidth - 8) links = Math.max(8, r.left - m.width - 8);
  tafel.style.left = Math.round(links) + 'px';
  tafel.style.top = Math.round(Math.max(8,
    Math.min(r.top, window.innerHeight - 8 - m.height))) + 'px';

  setTimeout(() => {
    document.addEventListener('mousedown', function zuMachen(ev) {
      if (tafel.contains(ev.target) || (knopf && knopf.contains(ev.target))) return;
      layoutTafelWeg();
      document.removeEventListener('mousedown', zuMachen);
    });
  }, 0);
};

/* ------------------------------------------------------------
   BILD GROSS ANSEHEN

   Der zweite Schnellknopf, die Lupe. In WPS legt sie das Bild groß über
   das Fenster, mit „1:1" und „einpassen" darunter. Das ist keine
   Spielerei: Wer prüfen will, ob ein eingescanntes Schreiben lesbar ist,
   muss es groß sehen, ohne es dafür im Dokument zu vergrößern.
   ------------------------------------------------------------ */
B.bildVorschau = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild || bild.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return; }

  const grund = document.createElement('div');
  grund.className = 'bildschau';

  const gross = document.createElement('img');
  gross.src = bild.src;
  gross.alt = bild.alt || '';
  gross.className = 'bildschau__bild';
  grund.appendChild(gross);

  const leiste = document.createElement('div');
  leiste.className = 'bildschau__leiste';
  const knopf = (text, titel, tun) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'bildschau__knopf';
    k.textContent = text;
    k.title = titel;
    k.addEventListener('click', tun);
    leiste.appendChild(k);
    return k;
  };
  knopf('1:1', 'In Originalgröße zeigen', () => {
    gross.classList.add('bildschau__bild--echt');
  });
  knopf('⛶', 'Ins Fenster einpassen', () => {
    gross.classList.remove('bildschau__bild--echt');
  });
  grund.appendChild(leiste);

  const zu = document.createElement('button');
  zu.type = 'button';
  zu.className = 'bildschau__zu';
  zu.textContent = '×';
  zu.title = 'Schließen (Escape)';
  grund.appendChild(zu);

  const weg = () => {
    grund.remove();
    document.removeEventListener('keydown', taste);
  };
  const taste = (e) => { if (e.key === 'Escape') { e.preventDefault(); weg(); } };
  zu.addEventListener('click', weg);
  grund.addEventListener('click', (e) => { if (e.target === grund) weg(); });
  document.addEventListener('keydown', taste);

  document.body.appendChild(grund);
  zu.focus();
};


/* Die Größe in Zahlen — für alle, die nicht ziehen wollen oder können.

   Das Seitenverhältnis ist standardmäßig gesperrt, wie in WPS: Ein
   verzerrtes Foto ist fast nie gewollt, und wer es doch will, nimmt den
   Haken heraus. */
B.bildGroesse = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild || bild.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return; }
  const massstab = (zoom || 100) / 100;
  const r = bild.getBoundingClientRect();
  const breite = inMillimeter(r.width / massstab);
  const hoehe = inMillimeter(r.height / massstab);
  const verhaeltnis = hoehe / breite || 1;

  fenster('Größe des Bildes', [
    { schluessel: 'breite', name: 'Breite (mm)', art: 'number', wert: String(breite) },
    { schluessel: 'hoehe', name: 'Höhe (mm)', art: 'number', wert: String(hoehe) },
    { schluessel: 'sperre', name: 'Seitenverhältnis sperren', art: 'auswahl',
      wert: 'ja', werte: [['ja', 'Ja'], ['nein', 'Nein']] },
  ], (werte) => {
    let b = Math.max(5, parseFloat(werte.breite) || breite);
    let h = Math.max(5, parseFloat(werte.hoehe) || hoehe);
    /* Gesperrt heißt: Die Breite führt. Wer beide Felder ändert und die
       Sperre stehen lässt, bekommt sonst eine Höhe, die er nicht wollte,
       und weiß nicht, welche der beiden Zahlen gewonnen hat. */
    if (werte.sperre === 'ja') h = Math.round(b * verhaeltnis * 10) / 10;
    bild.style.width = b + 'mm';
    bild.style.height = h + 'mm';
    geaendertMelden();
    melde('Bild: ' + b + ' mm breit, ' + h + ' mm hoch.');
    bildGriffeNachmessen();
  });
};

/* ZUSCHNEIDEN.

   Geschnitten wird mit clip-path und nicht durch Neuberechnen der
   Bilddaten: Das Bild bleibt unangetastet, der Schnitt ist jederzeit
   rücknehmbar, und die Datei wird nicht größer. Wer zurückwill, nimmt
   „Zuschnitt aufheben" — in WPS heißt das „Bild zurücksetzen".

   Angegeben wird in Prozent je Kante, weil das Bild danach noch
   vergrößert werden kann und Prozent das überleben. */
function schnittLesen(bild) {
  const roh = bild.dataset.schnitt;
  if (!roh) return { oben: 0, rechts: 0, unten: 0, links: 0 };
  try { return JSON.parse(roh); }
  catch (e) { return { oben: 0, rechts: 0, unten: 0, links: 0 }; }
}

function schnittAnwenden(bild, s) {
  const alle = [s.oben, s.rechts, s.unten, s.links];
  bild.dataset.schnitt = JSON.stringify(s);
  if (alle.every((w) => !w)) {
    bild.style.clipPath = '';
    delete bild.dataset.schnitt;
    return;
  }
  bild.style.clipPath = 'inset(' + alle.map((w) => w + '%').join(' ') + ')';
}

/* ------------------------------------------------------------
   ZUSCHNEIDEN — NACH FORM UND NACH VERHÄLTNIS

   In WPS hat der Schnitt zwei Karten: „Nach Form zuschneiden" mit
   Rechteck, Kreis, Dreieck, Stern und so weiter — und „Nach Skala
   zuschneiden" mit 1:1, 4:3, 16:9.

   Beides geht über clip-path. Das Bild bleibt unangetastet: Der Schnitt
   ist eine Anweisung an die Darstellung, keine Änderung an den Daten.
   Deshalb ist er jederzeit rücknehmbar, und die Datei wird nicht größer.
   ------------------------------------------------------------ */
const SCHNITTFORMEN = [
  ['keine',    'Ganz (kein Schnitt)', ''],
  ['rechteck', 'Rechteck mit runden Ecken',
   'inset(0 0 0 0 round 8%)'],
  ['kreis',    'Kreis',      'circle(50% at 50% 50%)'],
  ['ellipse',  'Ellipse',    'ellipse(50% 50% at 50% 50%)'],
  ['dreieck',  'Dreieck',    'polygon(50% 0%, 100% 100%, 0% 100%)'],
  ['raute',    'Raute',      'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'],
  ['fuenfeck', 'Fünfeck',
   'polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%)'],
  ['sechseck', 'Sechseck',
   'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)'],
  ['stern',    'Stern',
   'polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, '
   + '21% 91%, 32% 57%, 2% 35%, 39% 35%)'],
  ['herz',     'Herz',
   'polygon(50% 100%, 10% 60%, 0% 35%, 10% 12%, 30% 8%, 50% 25%, '
   + '70% 8%, 90% 12%, 100% 35%, 90% 60%)'],
  ['pfeil',    'Pfeil nach rechts',
   'polygon(0% 25%, 60% 25%, 60% 0%, 100% 50%, 60% 100%, 60% 75%, 0% 75%)'],
];

/* Seitenverhältnisse. Geschnitten wird mittig — was übersteht, fällt
   links und rechts oder oben und unten gleichmäßig weg. Alles andere
   müsste man verschieben können, und das ist ein eigenes Stück Arbeit. */
const SCHNITTMASSE = [
  ['1:1',  1],
  ['4:3',  4 / 3],
  ['3:2',  3 / 2],
  ['16:9', 16 / 9],
  ['3:4',  3 / 4],
  ['9:16', 9 / 16],
];

function schnittNachMass(bild, verhaeltnis) {
  const r = bild.getBoundingClientRect();
  const ist = r.width / r.height;
  let oben = 0, unten = 0, links = 0, rechts = 0;
  if (ist > verhaeltnis) {
    /* Zu breit: an den Seiten wegnehmen. */
    const weg = (1 - verhaeltnis / ist) / 2 * 100;
    links = rechts = Math.round(weg * 10) / 10;
  } else {
    const weg = (1 - ist / verhaeltnis) / 2 * 100;
    oben = unten = Math.round(weg * 10) / 10;
  }
  bild.dataset.schnitt = JSON.stringify({ oben, rechts, unten, links });
  bild.style.clipPath = 'inset(' + oben + '% ' + rechts + '% '
                      + unten + '% ' + links + '%)';
}

let schnittTafel = null;
function schnittTafelWeg() {
  if (schnittTafel) { schnittTafel.remove(); schnittTafel = null; }
}

B.bildZuschneiden = (knopf) => {
  const bild = bildZiel || bildAnStelle();
  if (!bild || bild.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return; }
  if (schnittTafel) { schnittTafelWeg(); return; }

  const tafel = document.createElement('div');
  tafel.className = 'layouttafel schnitttafel';

  const kopf = document.createElement('div');
  kopf.className = 'layouttafel__kopf';
  const titel = document.createElement('span');
  titel.textContent = 'Zuschneiden';
  const zu = document.createElement('button');
  zu.type = 'button';
  zu.className = 'layouttafel__zu';
  zu.textContent = '×';
  zu.addEventListener('click', schnittTafelWeg);
  kopf.append(titel, zu);
  tafel.appendChild(kopf);

  const ueber = (name) => {
    const h = document.createElement('p');
    h.className = 'layouttafel__gruppe';
    h.textContent = name;
    tafel.appendChild(h);
  };

  ueber('Nach Form');
  const formen = document.createElement('div');
  formen.className = 'schnitttafel__formen';
  for (const [art, name, pfad] of SCHNITTFORMEN) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'schnitttafel__form';
    k.title = name;
    k.setAttribute('aria-label', name);
    const innen = document.createElement('span');
    innen.className = 'schnitttafel__probe';
    if (pfad) innen.style.clipPath = pfad;
    k.appendChild(innen);
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      bild.style.clipPath = pfad;
      if (pfad) bild.dataset.form = art; else delete bild.dataset.form;
      delete bild.dataset.schnitt;
      geaendertMelden();
      melde(pfad ? 'Zugeschnitten: ' + name : 'Das Bild ist wieder ganz.');
      bildGriffeNachmessen();
    });
    formen.appendChild(k);
  }
  tafel.appendChild(formen);

  ueber('Nach Verhältnis');
  const masse = document.createElement('div');
  masse.className = 'schnitttafel__masse';
  for (const [name, wert] of SCHNITTMASSE) {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'schnitttafel__mass';
    k.textContent = name;
    k.title = 'Mittig auf ' + name + ' schneiden';
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => {
      delete bild.dataset.form;
      schnittNachMass(bild, wert);
      geaendertMelden();
      melde('Zugeschnitten auf ' + name + '.');
      bildGriffeNachmessen();
    });
    masse.appendChild(k);
  }
  tafel.appendChild(masse);

  const strich = document.createElement('div');
  strich.className = 'layouttafel__strich';
  tafel.appendChild(strich);

  const zurueck = document.createElement('button');
  zurueck.type = 'button';
  zurueck.className = 'layouttafel__weiter';
  zurueck.textContent = 'Zuschnitt aufheben';
  zurueck.addEventListener('click', () => { B.bildSchnittWeg(); schnittTafelWeg(); });
  tafel.appendChild(zurueck);

  const genau = document.createElement('button');
  genau.type = 'button';
  genau.className = 'layouttafel__weiter';
  genau.textContent = 'Kante für Kante in Prozent…';
  genau.addEventListener('click', () => { schnittTafelWeg(); B.bildSchnittGenau(); });
  tafel.appendChild(genau);

  document.body.appendChild(tafel);
  schnittTafel = tafel;

  const r = (knopf && knopf.getBoundingClientRect)
    ? knopf.getBoundingClientRect() : bild.getBoundingClientRect();
  const m = tafel.getBoundingClientRect();
  let links = r.right + 8;
  if (links + m.width > window.innerWidth - 8) links = Math.max(8, r.left - m.width - 8);
  tafel.style.left = Math.round(links) + 'px';
  tafel.style.top = Math.round(Math.max(8,
    Math.min(r.top, window.innerHeight - 8 - m.height))) + 'px';

  setTimeout(() => {
    document.addEventListener('mousedown', function zuMachen(ev) {
      if (tafel.contains(ev.target) || (knopf && knopf.contains(ev.target))) return;
      schnittTafelWeg();
      document.removeEventListener('mousedown', zuMachen);
    });
  }, 0);
};

/* Der genaue Weg bleibt daneben stehen: Wer weiss, dass oben zwölf
   Prozent wegsollen, soll nicht mit der Maus zielen muessen. */
B.bildSchnittGenau = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild || bild.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return; }
  const jetzt = schnittLesen(bild);
  fenster('Zuschneiden — Kante für Kante', [
    { art: 'satz', text: 'Wie viel von jeder Kante soll wegfallen? In Prozent.' },
    { schluessel: 'oben', name: 'Oben (%)', art: 'number', wert: String(jetzt.oben) },
    { schluessel: 'unten', name: 'Unten (%)', art: 'number', wert: String(jetzt.unten) },
    { schluessel: 'links', name: 'Links (%)', art: 'number', wert: String(jetzt.links) },
    { schluessel: 'rechts', name: 'Rechts (%)', art: 'number', wert: String(jetzt.rechts) },
  ], (werte) => {
    const zahl = (x) => Math.max(0, Math.min(45, parseFloat(x) || 0));
    delete bild.dataset.form;
    schnittAnwenden(bild, { oben: zahl(werte.oben), rechts: zahl(werte.rechts),
                            unten: zahl(werte.unten), links: zahl(werte.links) });
    geaendertMelden();
    melde(bild.dataset.schnitt ? 'Bild zugeschnitten.' : 'Zuschnitt aufgehoben.');
    bildGriffeNachmessen();
  }, 'Zuschneiden');
};

B.bildSchnittWeg = () => {
  const bild = bildZiel || bildAnStelle();
  if (!bild || bild.tagName !== 'IMG') { melde('Im Text steht kein Bild.'); return; }
  /* Auch eine Form ist ein Schnitt — sonst bliebe der Kreis stehen und
     „aufheben" täte scheinbar nichts. */
  delete bild.dataset.form;
  bild.style.clipPath = '';
  schnittAnwenden(bild, { oben: 0, rechts: 0, unten: 0, links: 0 });
  geaendertMelden();
  melde('Zuschnitt aufgehoben — das Bild ist wieder ganz.');
  bildGriffeNachmessen();
};

function bildGriffeBauen() {
  const machen = (art, name, zeiger, zeichen) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'bildgriff bildgriff--' + art;
    k.title = name;
    k.setAttribute('aria-label', name);
    if (zeichen) k.textContent = zeichen;
    if (zeiger) k.style.cursor = zeiger;
    bildGriffe[art] = k;
    document.body.appendChild(k);
    return k;
  };

  for (const { art, zeiger, name } of BILDGRIFFE) {
    const k = machen(art, 'Größe ziehen — ' + name, zeiger, '');
    k.addEventListener('pointerdown', (e) => {
      /* Im Schnittmodus ziehen dieselben acht Griffe den Schnitt statt
         der Groesse. Zwei Saetze Griffe uebereinander waeren ein Gewirr;
         in WPS wechseln sie ebenfalls ihre Bedeutung. */
      if (schnittModus) bildSchnittZiehen(e, art);
      else bildGroesseZiehen(e, art);
    });
  }
  machen('drehen', 'Bild drehen — ziehen', 'grab', '↻')
    .addEventListener('pointerdown', bildDrehenZiehen);
  /* Alle Schnellknoepfe beider Saetze anlegen; gezeigt wird je nach
     Gegenstand nur einer. Zwei getrennte Bauten waeren wieder zwei
     Systeme. */
  const alleSchnell = [...BILDSCHNELL, ...DIAGRAMMSCHNELL];
  for (const { art, bild: symbolName, name, tun } of alleSchnell) {
    const k = machen('schnell-' + art, name, 'pointer', '');
    k.classList.add('bildgriff--schnell');
    if (SYMBOLE[symbolName]) k.appendChild(symbol(symbolName));
    k.addEventListener('mousedown', (e) => e.preventDefault());
    /* Der Knopf reicht sich selbst mit: Die Tafel soll neben ihm aufgehen
       und nicht irgendwo. */
    k.addEventListener('click', () => tun(k));
  }

  machen('weg', 'Löschen', 'pointer', '×').addEventListener('click', () => {
    if (!bildZiel) return;
    bildZiel.remove();
    bildGriffeWeg();
    geaendertMelden();
    melde('Bild gelöscht. Rückgängig mit Strg+Z.');
  });
}

/* Das Bild, auf das sich die Griffe beziehen — oder keines.

   Hier stand bildAnStelle() als Rueckfall. Die Funktion liefert aber,
   wenn am Zeiger kein Bild steht, DAS ZULETZT EINGEFUEGTE. Damit gab es
   immer ein Bild, also immer Griffe: Wer das Bild verliess, behielt die
   Schnittmarken auf dem Blatt stehen. Genau das war Kays Befund.

   Jetzt zaehlt nur, was wirklich gemeint ist: das Bild unter der Maus
   oder das, IN dem die Schreibmarke steht — nicht irgendeines. */
/* ============================================================
   EIN SYSTEM FUER ALLE GEGENSTAENDE

   „schau doch einfach bei den Bildern und Tabellen rein, da liegen die
   Funktionen schon."

   Er hat recht, und es war der dritte Anlauf: Griffe, Ziehen,
   Groesse, Loeschkreuz — das steht hier seit Wochen fuer Bilder, und
   nebenan noch einmal fuer Tabellen. Ich habe daneben ein DRITTES
   gebaut, fuer Diagramme, statt das vorhandene zu oeffnen.

   Jetzt nimmt es jeden Gegenstand an: ein Bild, ein Diagramm, eine
   Zeichnung. Was sich unterscheidet, sind die Schnellknoepfe daneben —
   ein Bild will zugeschnitten werden, ein Diagramm nicht.
   ============================================================ */
const GEGENSTAENDE = 'img, svg.diagramm, svg.zeichnung, svg.smartart';

function istGegenstand(el) {
  return !!(el && el.matches && el.matches(GEGENSTAENDE));
}

/* Welche Schnellknoepfe neben diesem Gegenstand stehen. */
function schnellFuer(el) {
  if (el && el.classList && el.classList.contains('diagramm')) return DIAGRAMMSCHNELL;
  return BILDSCHNELL;
}

function bildGemeint() {
  /* EIN ANGEKLICKTES BILD BLEIBT GEWAEHLT.

     Kay: „ich kann die Symbole nicht erreichen, wenn ich das Bild
     anklicke." Der Grund: Ein Klick auf ein Bild setzt die Schreibmarke
     NEBEN das Bild, nicht darauf. Bewegte er die Maus dann zu den
     Knoepfen, verliess er das Blatt — und die Griffe verschwanden auf
     halbem Weg, weil weder Maus noch Schreibmarke auf dem Bild standen.

     Deshalb wird ein angeklicktes Bild gemerkt und bleibt gewaehlt, bis
     woanders hingeklickt wird. So haelt es jedes Programm mit
     Gegenstaenden auf einem Blatt. */
  if (bildGewaehlt && feld.contains(bildGewaehlt)) return bildGewaehlt;
  if (bildUnterMaus && feld.contains(bildUnterMaus)) return bildUnterMaus;
  const auswahl = window.getSelection();
  if (!auswahl || !auswahl.rangeCount) return null;
  let k = auswahl.anchorNode;
  if (k && k.nodeType === Node.TEXT_NODE) k = k.parentElement;
  if (!k || !k.closest) return null;
  /* Ein Bild ist markiert, wenn die Auswahl es umschliesst — dann steht
     es als einziges Kind im Bereich. */
  if (istGegenstand(k)) return feld.contains(k) ? k : null;
  const drin = [...k.querySelectorAll(GEGENSTAENDE)].filter((b) => {
    try { return auswahl.containsNode(b, true); } catch (e) { return false; }
  });
  return drin.length === 1 && feld.contains(drin[0]) ? drin[0] : null;
}

function bildGriffeAuffrischen() {
  if (zieht) return;
  const bild = bildGemeint();
  if (!bild || !feld.contains(bild)) {
    /* Auch der Schnittmodus endet: Marken auf einem Blatt ohne gewaehltes
       Bild sind Zierde, die niemand mehr wegbekommt. */
    if (schnittModus) schnittModusAus();
    bildGriffeWeg();
    return;
  }
  /* Ein anderes Bild — der Schnitt am alten ist beendet. */
  if (schnittModus && bildZiel && bildZiel !== bild) schnittModusAus();

  if (!bildGriffe.nw) bildGriffeBauen();
  bildZiel = bild;
  bildWache(bild);
  bildGriffeStellen(bild);
}

/* EINE WACHE AM BILD.

   Die Griffe wurden einmal gemessen und blieben dann liegen. Ein Bild
   aendert seine Groesse aber noch, nachdem gemessen wurde: Es laedt
   fertig, das Blatt wird gezoomt, eine Zeile darueber kommt dazu. Dann
   steht das Rechteck der Griffe um ein Vielfaches neben dem Bild — genau
   das war auf Kays Bildschirmfoto zu sehen.

   Ein ResizeObserver meldet jede Aenderung, und load faengt den Fall ab,
   dass das Bild beim Messen noch gar nicht da war. */
let bildBeobachter = null;
let bildBewacht = null;

function bildWache(bild) {
  if (bildBewacht === bild) return;
  if (bildBeobachter) bildBeobachter.disconnect();
  bildBewacht = bild;
  if (typeof ResizeObserver === 'undefined') return;
  bildBeobachter = new ResizeObserver(() => {
    if (!zieht && bildZiel === bild) bildGriffeStellen(bild);
  });
  bildBeobachter.observe(bild);
  if (bild.tagName === 'IMG' && !bild.complete) {
    bild.addEventListener('load', () => {
      if (bildZiel === bild) bildGriffeStellen(bild);
    }, { once: true });
  }
}

/* Nur stellen, nicht neu entscheiden — siehe griffeStellen(). Waehrend
   eines Zuges darf nichts weggeraeumt werden: Der Knopf, der den Zeiger
   gefangen haelt, verschwaende sonst mitsamt seinem pointerup, und der
   Zeiger bliebe im Zieh-Zustand haengen. */
function bildGriffeStellen(bild) {
  const voll = bild.getBoundingClientRect();
  const flaeche = $('arbeitsflaeche').getBoundingClientRect();
  const G = 11;
  const setz = (art, x, y) => {
    const k = bildGriffe[art];
    if (!k) return;
    k.style.left = Math.round(x - G / 2) + 'px';
    k.style.top = Math.round(y - G / 2) + 'px';
  };

  /* DIE MARKEN SITZEN AM AUSSCHNITT, NICHT AM BILD.

     clip-path schneidet die Darstellung, nicht das Kaestchen:
     getBoundingClientRect() liefert weiter das ganze Bild. Die acht
     Marken standen deshalb an der Bildkante und sprangen beim Ziehen
     sofort dorthin zurueck — es sah aus, als liesse sich nichts
     zuschneiden. Genau das war Kays Befund.

     Im Schnittmodus wird das Rechteck deshalb um den Schnitt
     eingerueckt. Ausserhalb des Modus ist der Schnitt null und es
     aendert sich nichts. */
  const sch = schnittModus ? schnittLesen(bild)
                           : { oben: 0, rechts: 0, unten: 0, links: 0 };
  const r = {
    left: voll.left + voll.width * sch.links / 100,
    top: voll.top + voll.height * sch.oben / 100,
    width: voll.width * (100 - sch.links - sch.rechts) / 100,
    height: voll.height * (100 - sch.oben - sch.unten) / 100,
  };
  r.right = r.left + r.width;
  r.bottom = r.top + r.height;

  for (const { art, x, y } of BILDGRIFFE) {
    setz(art, r.left + r.width * x, r.top + r.height * y);
  }
  setz('drehen', voll.left + voll.width / 2, voll.top - 22);
  setz('weg', voll.right + 20, voll.top - 14);
  /* Die drei Schnellknöpfe untereinander an der rechten Seite, unter dem
     Kreuz — so steht es in WPS, und so verdecken sie das Bild nicht. */
  /* Nur die Knoepfe, die zu diesem Gegenstand gehoeren. Ein Diagramm
     laesst sich nicht zuschneiden, ein Bild hat keine Datenreihe. */
  const meine = schnellFuer(bild);
  const fremd = new Set([...BILDSCHNELL, ...DIAGRAMMSCHNELL]
    .filter((e) => !meine.includes(e)).map((e) => 'schnell-' + e.art));
  meine.forEach(({ art }, i) => {
    setz('schnell-' + art, voll.right + 20, voll.top + 18 + i * 26);
  });

  const versteckt = voll.bottom < flaeche.top || voll.top > flaeche.bottom;
  for (const [art, k] of Object.entries(bildGriffe)) {
    k.hidden = versteckt || fremd.has(art);
  }
}

/* Das Bild selbst ist der Griff zum Verschieben. */
function bildZiehenBeginnen(fall) {
  const bild = fall.target && fall.target.closest
    ? fall.target.closest(GEGENSTAENDE) : null;
  if (!bild || !feld.contains(bild)) return;
  bildGewaehlt = bild;
  fall.preventDefault();
  bildUnterMaus = bild;
  bildGriffeAuffrischen();

  const warFrei = bildIstFrei(bild);
  const zurueck = { links: bild.style.left, oben: bild.style.top };
  /* ERST BEWEGEN, DANN LOESEN.

     Hier wurde das Bild schon beim Druck aus dem Textfluss geloest. Ein
     blosser Klick — zum Auswaehlen, um an die Knoepfe zu kommen —
     machte es damit schwebend, ohne dass jemand gezogen haette. Erst ab
     vier Pixeln Bewegung ist es ein Zug. */
  let geloest = false;
  zieht = true;
  document.body.classList.add('zieht-tabelle');

  const massstab = (zoom || 100) / 100;
  const start = { x: fall.clientX, y: fall.clientY };
  let anfang = { links: 0, oben: 0 };

  try { bild.setPointerCapture(fall.pointerId); } catch (e) { /* aelter */ }

  const bewegen = (e) => {
    if (!geloest) {
      if (Math.abs(e.clientX - start.x) < 4 && Math.abs(e.clientY - start.y) < 4) return;
      bildFreiMachen(bild);
      anfang = { links: parseFloat(bild.style.left) || 0,
                 oben: parseFloat(bild.style.top) || 0 };
      geloest = true;
    }
    const gehalten = imBlattHalten(bild,
      anfang.links + inMillimeter((e.clientX - start.x) / massstab),
      anfang.oben + inMillimeter((e.clientY - start.y) / massstab));
    bild.style.left = Math.round(gehalten.links * 10) / 10 + 'mm';
    bild.style.top = Math.round(gehalten.oben * 10) / 10 + 'mm';
    bildGriffeStellen(bild);
  };
  const aufhoeren = () => {
    zieht = false;
    bild.removeEventListener('pointermove', bewegen);
    bild.removeEventListener('pointerup', fertig);
    document.removeEventListener('keydown', taste);
    document.body.classList.remove('zieht-tabelle');
    try { bild.releasePointerCapture(fall.pointerId); } catch (e) { /* weg */ }
  };
  const taste = (e) => {
    if (e.key !== 'Escape') return;
    e.preventDefault();
    aufhoeren();
    if (!warFrei && geloest) bild.classList.remove('bild--frei');
    bild.style.left = zurueck.links; bild.style.top = zurueck.oben;
    bildGriffeAuffrischen();
    melde('Verschieben abgebrochen.');
  };
  const fertig = () => {
    aufhoeren();
    /* Ohne Bewegung war es ein Klick zum Auswaehlen — nichts geaendert,
       also auch nichts gemeldet. */
    if (!geloest) { bildGriffeNachmessen(); return; }
    geaendertMelden();
    melde(warFrei ? 'Bild verschoben.'
                  : 'Bild schwebt jetzt frei. Zurück mit „Wieder in den Text".');
    bildGriffeAuffrischen();
  };

  bild.addEventListener('pointermove', bewegen);
  bild.addEventListener('pointerup', fertig);
  document.addEventListener('keydown', taste);
}

/* ============================================================
   DER SCHNITTMODUS

   Kay: „wenn ich auf Zuschneiden klicke, fehlen die Marker am Bild."
   Stimmt — ich hatte nur eine Tafel gebaut. In WPS werden beim
   Zuschneiden die acht runden Griffe zu WINKELN, und man zieht sie nach
   innen: Das Bild bleibt stehen, der Ausschnitt wird kleiner.

   Warum das besser ist als vier Prozentzahlen: Man sieht, was wegfaellt,
   waehrend man es wegnimmt. Prozente muss man sich vorstellen.

   Waehrend des Schnittmodus bleibt das ganze Bild sichtbar, nur blasser
   ausserhalb des Ausschnitts — sonst schneidet man blind und weiss nicht,
   was noch da waere. Dafuer liegt eine zweite, ungeschnittene Fassung
   hinter dem Bild.
   ============================================================ */
let schnittModus = false;
let schnittSchatten = null;      /* die blasse Fassung dahinter */

function schnittModusAn(bild) {
  if (schnittModus) return;
  schnittModus = true;
  document.body.classList.add('schneidet');
  /* NUR die acht Ziehgriffe werden zu Winkeln. Die Schnellknoepfe
     daneben sind keine Griffe am Bild, sondern Knoepfe — sie hatten die
     Marken-Form mitbekommen und sahen aus wie leere Kaesten. */
  for (const { art } of BILDGRIFFE) {
    if (bildGriffe[art]) bildGriffe[art].classList.add('bildgriff--marke');
  }

  /* Die blasse Fassung: dasselbe Bild, an derselben Stelle, ohne
     Schnitt. Sie liegt darunter und zeigt, was wegfaellt. */
  schnittSchatten = bild.cloneNode(false);
  schnittSchatten.className = 'schnittschatten';
  schnittSchatten.style.cssText = bild.style.cssText;
  schnittSchatten.style.clipPath = '';
  schnittSchatten.style.filter = '';
  schnittSchatten.style.position = 'absolute';
  schnittSchatten.style.pointerEvents = 'none';
  const r = bild.getBoundingClientRect();
  const bogen = (bild.closest('.dokument') || feld).getBoundingClientRect();
  const massstab = (zoom || 100) / 100;
  schnittSchatten.style.left = inMillimeter((r.left - bogen.left) / massstab) + 'mm';
  schnittSchatten.style.top = inMillimeter((r.top - bogen.top) / massstab) + 'mm';
  (bild.closest('.dokument') || feld).appendChild(schnittSchatten);

  melde('Schnittmodus: die Winkel nach innen ziehen. '
      + 'Eingabetaste beendet, Escape bricht ab.');
}

function schnittModusAus() {
  if (!schnittModus) return;
  schnittModus = false;
  document.body.classList.remove('schneidet');
  for (const { art } of BILDGRIFFE) {
    if (bildGriffe[art]) bildGriffe[art].classList.remove('bildgriff--marke');
  }
  if (schnittSchatten) { schnittSchatten.remove(); schnittSchatten = null; }
}

B.schnittModus = () => {
  const bild = bildJetzt();
  if (!bild) return;
  if (schnittModus) {
    schnittModusAus();
    geaendertMelden();
    melde('Zuschnitt übernommen.');
    return;
  }
  /* Eine Form und ein Kantenschnitt schliessen einander aus. */
  if (bild.dataset.form) {
    delete bild.dataset.form;
    bild.style.clipPath = '';
  }
  schnittModusAn(bild);
  bildGriffeNachmessen();
};

/* Einen der acht Winkel ziehen: Er verschiebt genau die Kante, an der er
   sitzt. Die Ecken verschieben zwei. */
function bildSchnittZiehen(fall, art) {
  fall.preventDefault();
  const bild = bildZiel;
  if (!bild) return;
  const knopf = fall.currentTarget;
  try { knopf.setPointerCapture(fall.pointerId); } catch (e) { /* aelter */ }

  const r = bild.getBoundingClientRect();
  const anfang = schnittLesen(bild);
  const zurueck = Object.assign({}, anfang);
  const start = { x: fall.clientX, y: fall.clientY };
  zieht = true;
  document.body.classList.add('zieht-tabelle');

  const bewegen = (e) => {
    const dx = (e.clientX - start.x) / r.width * 100;
    const dy = (e.clientY - start.y) / r.height * 100;
    const s = Object.assign({}, anfang);
    if (art.indexOf('w') > -1) s.links = anfang.links + dx;
    if (art.indexOf('e') > -1) s.rechts = anfang.rechts - dx;
    if (art.indexOf('n') === 0) s.oben = anfang.oben + dy;
    if (art === 's' || art === 'se' || art === 'sw') s.unten = anfang.unten - dy;
    /* Nie mehr als 90 Prozent wegnehmen, und nie ins Negative: Ein Bild
       ohne Flaeche liesse sich nicht mehr anfassen. */
    for (const k of ['oben', 'rechts', 'unten', 'links']) {
      s[k] = Math.max(0, Math.min(90, Math.round(s[k] * 10) / 10));
    }
    if (s.oben + s.unten > 90) { s.oben = anfang.oben; s.unten = anfang.unten; }
    if (s.links + s.rechts > 90) { s.links = anfang.links; s.rechts = anfang.rechts; }
    schnittAnwenden(bild, s);
    bildGriffeStellen(bild);
  };

  const aufhoeren = () => {
    zieht = false;
    knopf.removeEventListener('pointermove', bewegen);
    knopf.removeEventListener('pointerup', fertig);
    document.removeEventListener('keydown', taste);
    document.body.classList.remove('zieht-tabelle');
    try { knopf.releasePointerCapture(fall.pointerId); } catch (e) { /* weg */ }
  };
  const taste = (e) => {
    if (e.key !== 'Escape') return;
    e.preventDefault(); aufhoeren();
    schnittAnwenden(bild, zurueck); bildGriffeStellen(bild);
    melde('Schnitt abgebrochen.');
  };
  const fertig = () => {
    aufhoeren(); geaendertMelden();
    const s = schnittLesen(bild);
    melde('Schnitt: oben ' + s.oben + ' %, unten ' + s.unten
        + ' %, links ' + s.links + ' %, rechts ' + s.rechts + ' %.');
  };

  knopf.addEventListener('pointermove', bewegen);
  knopf.addEventListener('pointerup', fertig);
  document.addEventListener('keydown', taste);
}

/* Eingabetaste beendet den Schnittmodus, Escape auch — so wie in jedem
   Programm, das einen Modus kennt. */
document.addEventListener('keydown', (e) => {
  if (!schnittModus) return;
  if (e.key === 'Enter') {
    e.preventDefault();
    schnittModusAus();
    geaendertMelden();
    melde('Zuschnitt übernommen.');
  } else if (e.key === 'Escape') {
    schnittModusAus();
    melde('Schnittmodus beendet.');
  }
});

function bildGroesseZiehen(fall, art) {
  fall.preventDefault();
  const bild = bildZiel;
  if (!bild) return;
  const knopf = fall.currentTarget;
  try { knopf.setPointerCapture(fall.pointerId); } catch (e) { /* aelter */ }

  const massstab = (zoom || 100) / 100;
  const r = bild.getBoundingClientRect();
  const anfang = { breite: r.width / massstab, hoehe: r.height / massstab };
  const verhaeltnis = anfang.hoehe / anfang.breite || 1;
  const start = { x: fall.clientX, y: fall.clientY };
  const zurueck = { b: bild.style.width, h: bild.style.height };
  const ecke = art.length === 2;         /* nw, ne, se, sw */
  const nachWesten = art.indexOf('w') > -1;
  const nachNorden = art.indexOf('n') === 0;
  zieht = true;
  document.body.classList.add('zieht-tabelle');

  const bewegen = (e) => {
    let dx = (e.clientX - start.x) / massstab;
    let dy = (e.clientY - start.y) / massstab;
    if (nachWesten) dx = -dx;
    if (nachNorden) dy = -dy;

    let breite = anfang.breite;
    let hoehe = anfang.hoehe;
    if (ecke) {
      /* Ecken halten das Seitenverhaeltnis — sonst wird jedes Bild beim
         Ziehen schief, und niemand will ein verzerrtes Foto. */
      breite = anfang.breite + dx;
      hoehe = breite * verhaeltnis;
    } else if (art === 'e' || art === 'w') {
      breite = anfang.breite + dx;
    } else {
      hoehe = anfang.hoehe + dy;
    }
    const mind = 10 * 96 / 25.4;          /* ein Zentimeter */
    bild.style.width = inMillimeter(Math.max(mind, breite)) + 'mm';
    bild.style.height = inMillimeter(Math.max(mind, hoehe)) + 'mm';
    bildGriffeStellen(bild);
  };
  const aufhoeren = () => {
    zieht = false;
    knopf.removeEventListener('pointermove', bewegen);
    knopf.removeEventListener('pointerup', fertig);
    document.removeEventListener('keydown', taste);
    document.body.classList.remove('zieht-tabelle');
    try { knopf.releasePointerCapture(fall.pointerId); } catch (e) { /* weg */ }
  };
  const taste = (e) => {
    if (e.key !== 'Escape') return;
    e.preventDefault(); aufhoeren();
    bild.style.width = zurueck.b; bild.style.height = zurueck.h;
    bildGriffeAuffrischen(); melde('Größe abgebrochen.');
  };
  const fertig = () => {
    aufhoeren(); geaendertMelden();
    melde('Bild: ' + bild.style.width + ' breit, ' + bild.style.height + ' hoch.');
    bildGriffeAuffrischen();
  };

  knopf.addEventListener('pointermove', bewegen);
  knopf.addEventListener('pointerup', fertig);
  document.addEventListener('keydown', taste);
}

function bildDrehenZiehen(fall) {
  fall.preventDefault();
  const bild = bildZiel;
  if (!bild) return;
  const knopf = fall.currentTarget;
  try { knopf.setPointerCapture(fall.pointerId); } catch (e) { /* aelter */ }

  const r = bild.getBoundingClientRect();
  const mitte = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  const zurueck = bild.style.transform;
  zieht = true;
  document.body.classList.add('zieht-tabelle');

  const bewegen = (e) => {
    const winkel = Math.atan2(e.clientY - mitte.y, e.clientX - mitte.x)
                 * 180 / Math.PI + 90;
    /* In Schritten von fuenf Grad, solange Umschalt nicht gedrueckt ist:
       Ein Bild, das um 1,7 Grad schief haengt, sieht nach Versehen aus. */
    const fein = e.shiftKey ? winkel : Math.round(winkel / 5) * 5;
    bild.dataset.drehung = String(Math.round(fein));
    /* Ueber bildVerwandlung, damit eine Spiegelung nicht verlorengeht. */
    bildVerwandlung(bild);
    bildGriffeStellen(bild);
  };
  const aufhoeren = () => {
    zieht = false;
    knopf.removeEventListener('pointermove', bewegen);
    knopf.removeEventListener('pointerup', fertig);
    document.removeEventListener('keydown', taste);
    document.body.classList.remove('zieht-tabelle');
    try { knopf.releasePointerCapture(fall.pointerId); } catch (e) { /* weg */ }
  };
  const taste = (e) => {
    if (e.key !== 'Escape') return;
    e.preventDefault(); aufhoeren();
    bild.style.transform = zurueck; bildGriffeAuffrischen();
    melde('Drehen abgebrochen.');
  };
  const fertig = () => {
    aufhoeren(); geaendertMelden();
    melde('Bild um ' + (bild.dataset.drehung || 0) + ' Grad gedreht.');
    bildGriffeAuffrischen();
  };

  knopf.addEventListener('pointermove', bewegen);
  knopf.addEventListener('pointerup', fertig);
  document.addEventListener('keydown', taste);
}

/* Beim Fahren ueber das Blatt: Steht der Zeiger auf einem Bild, gehoeren
   ihm die Griffe — wie bei den Tabellen, und aus demselben Grund. */
feld.addEventListener('pointerover', (e) => {
  if (zieht) return;
  const ziel = e.target && e.target.tagName === 'IMG' ? e.target : null;
  const neu = ziel && feld.contains(ziel) ? ziel : null;
  if (neu === bildUnterMaus) return;
  bildUnterMaus = neu;
  bildGriffeNachmessen();
});

feld.addEventListener('pointerdown', bildZiehenBeginnen);

/* Abgewaehlt wird nur durch einen Druck woanders — nicht dadurch, dass
   die Maus ueber den Rand faehrt. Griffe, Tafeln und die Bildtools-
   Leiste zaehlen dabei zum Bild: Wer sie drueckt, meint es ja. */
document.addEventListener('pointerdown', (e) => {
  if (zieht || !bildGewaehlt) return;
  const z = e.target;
  if (!z || !z.closest) return;
  if (z.tagName === 'IMG' && feld.contains(z)) return;
  if (z.closest('.bildgriff, .layouttafel, .schnitttafel, .bildschau')) return;
  if (z.closest('#werkzeugleiste3')) return;
  bildGewaehlt = null;
  bildGriffeNachmessen();
}, true);
/* Zweimal messen — genau wie bei den Tabellen, und aus demselben Grund:
   Beim ersten Berühren eines Bildes taucht gleichzeitig die Leiste
   „Bildtools" auf und schiebt das Blatt nach unten. Wer nur einmal misst,
   setzt die Griffe dorthin, wo das Bild eine Zwanzigstelsekunde vorher
   war — und sie liegen als Punkte verstreut daneben. */
function bildGriffeNachmessen() {
  if (zieht) return;
  bildGriffeAuffrischen();
  requestAnimationFrame(bildGriffeAuffrischen);
}

document.addEventListener('selectionchange', bildGriffeNachmessen);
window.addEventListener('resize', bildGriffeNachmessen);
$('arbeitsflaeche').addEventListener('scroll', () => {
  if (!zieht) bildGriffeAuffrischen();
});

function bildAnStelle() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return null;
  let knoten = auswahl.anchorNode;
  if (knoten && knoten.nodeType === Node.TEXT_NODE) knoten = knoten.parentElement;
  /* Erst am Zeiger suchen, sonst das zuletzt eingefügte Bild nehmen —
     nach dem Einfügen steht der Zeiger meist daneben, nicht darauf. */
  const nah = knoten && knoten.closest ? knoten.closest('img, svg, .textrahmen') : null;
  if (nah && feld.contains(nah)) return nah;
  const alle = feld.querySelectorAll('img, svg.diagramm, svg.zeichnung, .textrahmen');
  return alle.length ? alle[alle.length - 1] : null;
}

B.anordnen = () => {
  const bild = bildAnStelle();
  if (!bild) { melde('Im Text steht kein Bild und keine Form.'); return; }

  fenster('Anordnen', [
    { art: 'satz', text: 'Gilt für das Bild oder die Form am Zeiger — sonst für die letzte im Text.' },
    { schluessel: 'umbruch', name: 'Textumbruch', art: 'auswahl', werte: [
      ['zeile', 'Mit Text in Zeile'], ['links', 'Links umfließen'],
      ['rechts', 'Rechts umfließen'], ['oben', 'Oben und unten'],
      ['hinter', 'Hinter dem Text'],
    ] },
    { schluessel: 'ebene', name: 'Ebene', art: 'auswahl', werte: [
      ['normal', 'wie gehabt'], ['vorne', 'nach vorn'], ['hinten', 'nach hinten'],
    ] },
    { schluessel: 'drehen', name: 'Drehen (Grad)', art: 'number', wert: '0', schritt: '15' },
    { schluessel: 'breite', name: 'Breite (mm, 0 = wie gehabt)', art: 'number', wert: '0', schritt: '5' },
  ], (werte) => {
    bild.classList.remove('bild--links', 'bild--rechts', 'bild--oben', 'bild--hinter');
    if (werte.umbruch === 'links') bild.classList.add('bild--links');
    else if (werte.umbruch === 'rechts') bild.classList.add('bild--rechts');
    else if (werte.umbruch === 'oben') bild.classList.add('bild--oben');
    else if (werte.umbruch === 'hinter') bild.classList.add('bild--hinter');

    if (werte.ebene === 'vorne') bild.style.zIndex = '3';
    else if (werte.ebene === 'hinten') bild.style.zIndex = '0';
    else bild.style.zIndex = '';

    const grad = parseFloat(werte.drehen) || 0;
    bild.style.transform = grad ? 'rotate(' + grad + 'deg)' : '';

    const breite = parseFloat(werte.breite) || 0;
    if (breite > 0) bild.style.width = breite + 'mm';

    geaendertMelden();
    melde('Angeordnet.');
  });
};

/* ============================================================
   Nachgereicht: Sendungen
   ============================================================ */

/* ---- Umschläge ----
   DIN lang ist das Format, in dem in Deutschland fast jeder Brief steckt.
   Das Sichtfenster sitzt genormt — deshalb stehen Absender und Empfänger
   hier an festen Stellen und nicht irgendwo. */
const UMSCHLAEGE = {
  dl:  { name: 'DIN lang (220 × 110 mm)', breite: 220, hoehe: 110 },
  c6:  { name: 'C6 (162 × 114 mm)',       breite: 162, hoehe: 114 },
  c5:  { name: 'C5 (229 × 162 mm)',       breite: 229, hoehe: 162 },
  c4:  { name: 'C4 (324 × 229 mm)',       breite: 324, hoehe: 229 },
};

B.umschlag = () => {
  const eigen = Speicher.lies('eigenschaften', {});
  const absender = Speicher.lies('absender', eigen.verfasser || '');
  fenster('Umschlag', [
    { art: 'satz', text: 'Das Blatt wird auf Umschlagformat gestellt und beides eingesetzt.\nDanach steht der Umschlag allein im Dokument.' },
    { schluessel: 'format', name: 'Format', art: 'auswahl',
      werte: Object.entries(UMSCHLAEGE).map(([k, v]) => [k, v.name]) },
    { schluessel: 'absender', name: 'Absender', wert: absender },
    { schluessel: 'empfaenger', name: 'Empfänger', art: 'flaeche', zeilen: 4,
      wert: 'Vorname Nachname\nStraße 1\n12345 Ort' },
  ], (werte) => {
    const masse = UMSCHLAEGE[werte.format] || UMSCHLAEGE.dl;
    Speicher.schreib('absender', werte.absender.trim());

    /* Das Blatt bekommt Umschlagmaße. Der Druck folgt über dieselbe Regel,
       die auch das Papierformat setzt. */
    const blatt = $('blatt');
    blatt.style.width = masse.breite + 'mm';
    blatt.style.minHeight = masse.hoehe + 'mm';
    let regel = document.getElementById('seitenregel');
    if (!regel) { regel = document.createElement('style'); regel.id = 'seitenregel'; document.head.appendChild(regel); }
    regel.textContent = '@page{size:' + masse.breite + 'mm ' + masse.hoehe + 'mm;margin:0}';
    seitenrand.oben = 12; seitenrand.unten = 10; seitenrand.links = 15; seitenrand.rechts = 12;
    seiteAnwenden();

    const empfaenger = werte.empfaenger.split(/\r?\n/).filter((z) => z.trim())
      .map((z) => alsSicher(z.trim())).join('<br>');

    Dokument.setzeInhalt(
      '<p class="umschlag__absender">' + alsSicher(werte.absender.trim()) + '</p>'
      + '<p class="umschlag__empfaenger">' + empfaenger + '</p>');

    dateiname = 'Umschlag';
    titelSetzen();
    melde('Umschlag im Format ' + masse.name + ' angelegt.');
  }, 'Anlegen');
};

/* ---- Etiketten ----
   Ein Bogen voller gleicher Aufkleber. Die Maße stammen von den
   gebräuchlichen Bögen; wer andere hat, gibt sie selbst ein. */
/* Die Schlüssel tragen ein „b" davor, und das mit Absicht: Bei rein
   numerischen Namen ordnet JavaScript die Einträge nach ihrer Zahl um,
   und im Kasten stand dann der seltenste Bogen ganz oben statt des
   gebräuchlichsten. */
const ETIKETTEN = {
  b3475: { name: '70 × 37 mm — 24 Stück (3 × 8)', spalten: 3, zeilen: 8, breite: 70, hoehe: 37 },
  b3474: { name: '70 × 42,3 mm — 21 Stück (3 × 7)', spalten: 3, zeilen: 7, breite: 70, hoehe: 42 },
  b3483: { name: '70 × 50,8 mm — 15 Stück (3 × 5)', spalten: 3, zeilen: 5, breite: 70, hoehe: 50 },
  b3652: { name: '105 × 42,3 mm — 14 Stück (2 × 7)', spalten: 2, zeilen: 7, breite: 105, hoehe: 42 },
  b3422: { name: '105 × 148 mm — 4 Stück (2 × 2)', spalten: 2, zeilen: 2, breite: 105, hoehe: 148 },
};

B.etiketten = () => {
  fenster('Etiketten', [
    { art: 'satz', text: 'Ein Bogen wird angelegt. Steht überall dasselbe, kommt der Text\nin jedes Feld; sonst je Zeile eines.' },
    { schluessel: 'bogen', name: 'Bogen', art: 'auswahl',
      werte: Object.entries(ETIKETTEN).map(([k, v]) => [k, v.name]) },
    { schluessel: 'text', name: 'Aufschrift', art: 'flaeche', zeilen: 4,
      wert: 'Vorname Nachname\nStraße 1\n12345 Ort' },
    { schluessel: 'gleich', name: 'Überall dasselbe', art: 'auswahl',
      werte: [['ja', 'ja — derselbe Text'], ['nein', 'nein — je Zeile ein Etikett']] },
  ], (werte) => {
    const bogen = ETIKETTEN[werte.bogen] || ETIKETTEN.b3475;
    const zeilen = werte.text.split(/\r?\n/).map((z) => z.trim()).filter(Boolean);
    const gleich = werte.gleich === 'ja';

    /* Der Bogen ist A4 hoch, die Etiketten sitzen als Tabelle darauf —
       so kommt jedes an dieselbe Stelle wie auf dem gekauften Bogen. */
    papier = 'a4'; quer = false; papierAnwenden();
    seitenrand.oben = 8; seitenrand.unten = 8; seitenrand.links = 5; seitenrand.rechts = 5;
    seiteAnwenden();

    let aus = '<table class="etiketten">';
    let zaehler = 0;
    for (let z = 0; z < bogen.zeilen; z++) {
      aus += '<tr>';
      for (let sp = 0; sp < bogen.spalten; sp++) {
        const inhalt = gleich
          ? zeilen.map(alsSicher).join('<br>')
          : (zeilen[zaehler] ? alsSicher(zeilen[zaehler]) : '&nbsp;');
        zaehler++;
        aus += '<td style="width:' + bogen.breite + 'mm;height:' + bogen.hoehe + 'mm">'
             + inhalt + '</td>';
      }
      aus += '</tr>';
    }
    aus += '</table>';

    Dokument.setzeInhalt(aus);
    dateiname = 'Etiketten';
    titelSetzen();
    melde('Bogen mit ' + (bogen.spalten * bogen.zeilen) + ' Etiketten angelegt.');
  }, 'Anlegen');
};

/* ---- Seriendruckfelder ----
   Ein Platzhalter an der Stelle des Zeigers. Beim Seriendruck wird er
   durch den Wert aus der Empfängerliste ersetzt. */
B.seriendruckfeld = () => {
  auswahlMerken();
  fenster('Seriendruckfeld', [
    { art: 'satz', text: 'Der Name muss in der Kopfzeile der Empfängerliste stehen.' },
    { schluessel: 'name', name: 'Feldname', wert: 'Name' },
  ], (werte) => {
    const name = werte.name.trim().replace(/[{}]/g, '');
    if (!name) return;
    auswahlZurueck();
    elementEinfuegen('<span class="seriendruckfeld">{{' + alsSicher(name) + '}}</span>');
    melde('Feld {{' + name + '}} eingefügt.');
  }, 'Einfügen');
};

B.adressblock = () => {
  auswahlMerken();
  fenster('Adressblock und Grußzeile', [
    { art: 'satz', text: 'Setzt die üblichen Felder auf einmal ein.\nDie Namen müssen in der Empfängerliste so heißen.' },
    { schluessel: 'was', name: 'Einfügen', art: 'auswahl', werte: [
      ['adresse', 'Adressblock (Name, Straße, Ort)'],
      ['gruss', 'Grußzeile (Anrede + Name)'],
      ['beides', 'Adressblock und Grußzeile'],
    ] },
  ], (werte) => {
    const adresse = '<span class="seriendruckfeld">{{Name}}</span><br>'
                  + '<span class="seriendruckfeld">{{Straße}}</span><br>'
                  + '<span class="seriendruckfeld">{{PLZ}}</span> '
                  + '<span class="seriendruckfeld">{{Ort}}</span>';
    const gruss = 'Sehr geehrte<span class="seriendruckfeld">{{Anrede}}</span> '
                + '<span class="seriendruckfeld">{{Name}}</span>,';
    auswahlZurueck();
    if (werte.was === 'adresse') elementEinfuegen('<p>' + adresse + '</p>');
    else if (werte.was === 'gruss') elementEinfuegen('<p>' + gruss + '</p>');
    else elementEinfuegen('<p>' + adresse + '</p><p><br></p><p>' + gruss + '</p>');
    melde('Eingesetzt. Die Werte kommen beim Seriendruck.');
  }, 'Einfügen');
};

/* ---- Regeln ----
   „Wenn … dann …" im Serienbrief: Damit steht bei Frauen „Sehr geehrte
   Frau" und bei Männern „Sehr geehrter Herr", ohne zwei Briefe zu
   schreiben. */
B.seriendruckregel = () => {
  auswahlMerken();
  fenster('Regel', [
    { art: 'satz', text: 'Wenn das Feld den Wert hat, steht der erste Text da — sonst der zweite.' },
    { schluessel: 'feld', name: 'Feld', wert: 'Geschlecht' },
    { schluessel: 'wert', name: 'ist gleich', wert: 'w' },
    { schluessel: 'dann', name: 'dann', wert: 'Sehr geehrte Frau' },
    { schluessel: 'sonst', name: 'sonst', wert: 'Sehr geehrter Herr' },
  ], (werte) => {
    const feldname = werte.feld.trim().replace(/[{}]/g, '');
    if (!feldname) return;
    auswahlZurueck();
    elementEinfuegen('<span class="serienregel" data-feld="' + alsSicher(feldname)
      + '" data-wert="' + alsSicher(werte.wert.trim())
      + '" data-dann="' + alsSicher(werte.dann) + '" data-sonst="' + alsSicher(werte.sonst) + '">'
      + alsSicher(werte.dann) + '</span>');
    melde('Regel gesetzt: wenn ' + feldname + ' = „' + werte.wert + '".');
  }, 'Einfügen');
};

/* ---- Vorschau auf einen Empfänger ----
   Vor dem Erzeugen sehen, wie der Brief aussieht. Word nennt es „Vorschau
   auf Ergebnisse". */
function serienEinsetzen(html, satz) {
  let brief = html;

  /* Erst die Regeln: Sie entscheiden anhand eines Feldes, welcher Text
     stehen bleibt. */
  const hilfe = document.createElement('div');
  hilfe.innerHTML = brief;
  for (const regel of hilfe.querySelectorAll('.serienregel')) {
    const wert = (satz[regel.dataset.feld] || '').trim();
    regel.textContent = (wert === (regel.dataset.wert || '').trim())
      ? (regel.dataset.dann || '') : (regel.dataset.sonst || '');
  }
  brief = hilfe.innerHTML;

  for (const [name, wert] of Object.entries(satz)) {
    brief = brief.replace(
      new RegExp('\\{\\{\\s*' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*\\}\\}', 'g'),
      String(wert).replace(/[<>&]/g, ''));
  }
  return brief;
}

B.serienVorschau = () => {
  const daten = Speicher.lies('empfaengerliste', '');
  if (!daten) {
    melde('Erst die Empfänger eingeben — Extras ▸ Seriendruck-Assistent.');
    return;
  }
  const tabelle = tabelleLesen(daten);
  if (!tabelle || !tabelle.saetze.length) { melde('In der Liste steht kein Empfänger.'); return; }

  fenster('Vorschau auf Ergebnisse', [
    { art: 'satz', text: tabelle.saetze.length + ' Empfänger. Die Vorschau ersetzt den Text\nnicht — sie zeigt nur, wie er aussähe.' },
    { schluessel: 'nummer', name: 'Empfänger', art: 'auswahl',
      werte: tabelle.saetze.map((satz, i) =>
        [String(i), (i + 1) + '. ' + Object.values(satz).slice(0, 2).join(', ')]) },
  ], (werte) => {
    const satz = tabelle.saetze[parseInt(werte.nummer, 10) || 0];
    const hilfe = document.createElement('div');
    hilfe.innerHTML = serienEinsetzen(Dokument.inhalt(), satz);
    fenster('Vorschau: ' + Object.values(satz)[0], [
      { art: 'satz', text: hilfe.textContent.trim().slice(0, 900) },
    ], () => {}, 'Schließen');
  }, 'Zeigen');
};

/* ============================================================
   Nachgereicht: Überprüfen und Ansicht
   ============================================================ */

/* ---- Barrierefreiheit prüfen ----
   Was einem Menschen mit Sehbehinderung den Text unlesbar macht: Bilder
   ohne Beschreibung, übersprungene Überschriftenebenen, Tabellen ohne
   Kopfzeile, zu blasse Schrift. Alles vier lässt sich hier nachsehen. */
function kontrastVerhaeltnis(vorne, hinten) {
  const zahl = (farbe) => {
    const t = document.createElement('div');
    t.style.color = farbe;
    document.body.appendChild(t);
    const roh = getComputedStyle(t).color.match(/[\d.]+/g) || [0, 0, 0];
    t.remove();
    return roh.slice(0, 3).map(Number);
  };
  const hell = (c) => {
    const [r, g, b] = c.map((n) => {
      const v = n / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const a = hell(zahl(vorne)) + 0.05;
  const b = hell(zahl(hinten)) + 0.05;
  return (Math.max(a, b) / Math.min(a, b));
}

B.barrierefrei = () => {
  const funde = [];

  const bilder = [...feld.querySelectorAll('img')];
  const ohneText = bilder.filter((b) => !(b.alt || '').trim());
  if (ohneText.length) {
    funde.push(ohneText.length + (ohneText.length === 1 ? ' Bild hat' : ' Bilder haben')
      + ' keine Beschreibung. Wer nicht sieht, erfährt nicht, was darauf ist.');
  }

  const ueber = [...feld.querySelectorAll('h1,h2,h3,h4')].map((el) => +el.tagName[1]);
  let sprung = 0;
  for (let i = 1; i < ueber.length; i++) if (ueber[i] - ueber[i - 1] > 1) sprung++;
  if (sprung) {
    funde.push(sprung + (sprung === 1 ? ' übersprungene Ebene' : ' übersprungene Ebenen')
      + ' bei den Überschriften — etwa Überschrift 1 direkt gefolgt von Überschrift 3.');
  }
  if (!ueber.length && Dokument.zaehle().woerter > 150) {
    funde.push('Der Text hat keine Überschriften. Ab etwa einer Seite fällt das Zurechtfinden schwer.');
  }

  const tabellen = [...feld.querySelectorAll('table')];
  const ohneKopf = tabellen.filter((t) => !t.querySelector('th'));
  if (ohneKopf.length) {
    funde.push(ohneKopf.length + (ohneKopf.length === 1 ? ' Tabelle hat' : ' Tabellen haben')
      + ' keine Kopfzeile. Ohne sie ist unklar, wofür eine Spalte steht.');
  }

  const blattfarbe = getComputedStyle($('blatt')).backgroundColor || '#FFFFFF';
  const blass = [...feld.querySelectorAll('*')].filter((el) => {
    if (!el.textContent.trim()) return false;
    const farbe = getComputedStyle(el).color;
    return kontrastVerhaeltnis(farbe, blattfarbe) < 4.5;
  });
  if (blass.length) {
    funde.push(blass.length + (blass.length === 1 ? ' Stelle ist' : ' Stellen sind')
      + ' zu blass — unter dem Verhältnis 4,5 zu 1, das für Fließtext empfohlen wird.');
  }

  const links = [...feld.querySelectorAll('a')].filter((a) =>
    /^(hier|klick|mehr|link|weiter)/i.test(a.textContent.trim()));
  if (links.length) {
    funde.push(links.length === 1
      ? 'Ein Verweis heißt nur „hier" oder „mehr". Wer sich Verweise vorlesen lässt, '
        + 'hört das ohne Zusammenhang.'
      : links.length + ' Verweise heißen nur „hier" oder „mehr". Wer sich Verweise vorlesen '
        + 'lässt, hört das ohne Zusammenhang.');
  }

  fenster('Barrierefreiheit', [
    { art: 'satz', text: funde.length
        ? funde.map((f, i) => (i + 1) + '. ' + f).join('\n\n')
        : 'Nichts gefunden. Bilder beschrieben, Überschriften der Reihe nach,\n'
          + 'Tabellen mit Kopfzeile, Schrift kräftig genug.' },
  ], () => {}, 'Schließen');
};

/* ---- Überarbeitungsbereich ----
   Alle Änderungen auf einen Blick, statt sie im Text zu suchen. Word zeigt
   ihn als Leiste daneben; hier steht er in der Seitenleiste der
   Schreibhilfe, wo ohnehin die Funde stehen. */
B.ueberarbeitungsbereich = () => {
  const alle = verfolgteStellen();
  const kommentareAlle = kommentare();
  if (!alle.length && !kommentareAlle.length) {
    leereFunde('Es steht keine Änderung und kein Kommentar an.');
    return;
  }

  funde = [];
  KIteil.vorschlaegeLeeren();
  const liste = $('funde');
  liste.innerHTML = '';

  const kopf = document.createElement('p');
  kopf.className = 'tafel__ueberschrift';
  kopf.textContent = alle.length + ' Änderungen · ' + kommentareAlle.length + ' Kommentare';
  liste.appendChild(kopf);

  const karte = (art, text, farbe, hin) => {
    const k = document.createElement('div');
    k.className = 'fund fund--' + farbe;
    const sorte = document.createElement('span');
    sorte.className = 'fund__sorte';
    sorte.textContent = art;
    k.appendChild(sorte);
    const inhalt = document.createElement('div');
    inhalt.className = 'fund__stelle';
    inhalt.textContent = kuerze(text);
    k.appendChild(inhalt);
    const knoepfe = document.createElement('div');
    knoepfe.className = 'fund__knoepfe';
    const zeigen = document.createElement('button');
    zeigen.className = 'knopf knopf--klein';
    zeigen.textContent = 'Zeigen';
    zeigen.addEventListener('click', hin);
    knoepfe.appendChild(zeigen);
    k.appendChild(knoepfe);
    liste.appendChild(k);
  };

  for (const el of alle) {
    karte(el.tagName === 'INS' ? 'Neu' : 'Gelöscht', el.textContent,
          el.tagName === 'INS' ? 'vorschlag' : 'fehler',
          () => { el.scrollIntoView({ block: 'center' });
                  el.classList.add('verfolgt--gezeigt');
                  setTimeout(() => el.classList.remove('verfolgt--gezeigt'), 1500); });
  }
  for (const marke of kommentareAlle) {
    karte('Kommentar', marke.title, 'tipp',
          () => { marke.scrollIntoView({ block: 'center' });
                  marke.classList.add('kommentar--gezeigt');
                  setTimeout(() => marke.classList.remove('kommentar--gezeigt'), 1500); });
  }

  if (!tafelOffen) B.tafelZeigen();
  melde('Überarbeitungsbereich: ' + alle.length + ' Änderungen, '
      + kommentareAlle.length + ' Kommentare.');
};

/* ---- Bearbeitung einschränken ----
   Kein Schutz vor jemandem, der es darauf anlegt — die Datei liegt offen
   auf der Platte. Ein Schutz davor, aus Versehen im eigenen Text zu
   tippen, während man ihn nur durchsieht. Genau dafür benutzt man es. */
let gesperrt = false;

B.bearbeitungSperren = () => {
  gesperrt = !gesperrt;
  feld.contentEditable = gesperrt ? 'false' : 'true';
  $('kopfzeile').contentEditable = gesperrt ? 'false' : 'true';
  $('fusszeile').contentEditable = gesperrt ? 'false' : 'true';
  document.body.classList.toggle('gesperrt', gesperrt);
  menueBauen();
  melde(gesperrt
    ? 'Bearbeitung gesperrt — Lesen und Drucken geht weiter. Nochmal wählen hebt es auf.'
    : 'Bearbeitung wieder frei.');
};

/* ---- Gliederungsansicht ----
   Nur die Überschriften, eingerückt nach Ebene. So sieht man den Aufbau
   eines langen Textes, ohne zu blättern. */
let gliederung = false;

B.gliederung = () => {
  gliederung = !gliederung;
  feld.classList.toggle('dokument--gliederung', gliederung);
  if (gliederung && !feld.querySelector('h1,h2,h3,h4')) {
    melde('Der Text hat noch keine Überschriften — in der Gliederung bleibt er leer.');
  } else {
    melde(gliederung ? 'Gliederung — nur die Überschriften.' : 'Wieder der ganze Text.');
  }
  menueBauen();
  if (typeof statuszeileAuffrischen === 'function') statuszeileAuffrischen();
};

/* ---- Fenster anordnen ----
   Mehrere Fenster nebeneinander legen. Das kann nur der Arbeitsplatz —
   start.py fragt ihn. */
async function fensterOrdnen(wie) {
  try {
    const antwort = await fetch('fenster-ordnen?wie=' + encodeURIComponent(wie), { method: 'POST' });
    if (!antwort.ok) {
      let grund = 'Fehler ' + antwort.status;
      try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
      throw new Error(grund);
    }
    const ergebnis = await antwort.json();
    melde(ergebnis.zahl > 1
      ? ergebnis.zahl + ' Fenster angeordnet.'
      : 'Dafür braucht es mindestens zwei Fenster — Fenster ▸ Neues Fenster.');
  } catch (grund) {
    melde('Das geht nur im eigenen Fenster: ' + grund.message);
  }
}

B.fensterNebeneinander = () => fensterOrdnen('nebeneinander');
B.fensterUntereinander = () => fensterOrdnen('untereinander');
B.fensterKacheln = () => fensterOrdnen('kacheln');

/* ============================================================
   Vorlesen

   Für Legasthenie das Wirksamste überhaupt: Über einen Fehler liest das
   Auge hinweg — das Ohr stolpert darüber. Wer seinen eigenen Brief einmal
   gehört hat, findet darin mehr als beim dritten Durchlesen.

   WebKit selbst kann es nicht; der Sprachdienst des Arbeitsplatzes schon.
   Also fragt start.py ihn.
   ============================================================ */
let spricht = false;

async function vorlesenLassen(text) {
  if (!text.trim()) { melde('Es steht kein Text da.'); return; }
  try {
    const antwort = await fetch('vorlesen?stimme=' + encodeURIComponent(Speicher.lies('stimme', ''))
                              + '&tempo=' + encodeURIComponent(Speicher.lies('lesetempo', 0)),
                                { method: 'POST', body: text });
    if (!antwort.ok) {
      let grund = 'Fehler ' + antwort.status;
      try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
      throw new Error(grund);
    }
    spricht = true;
    menueBauen();
    melde('Wird vorgelesen — nochmal wählen hält an.');
  } catch (grund) {
    melde('Vorlesen ging nicht: ' + grund.message);
  }
}

B.vorlesen = async () => {
  if (spricht) { B.vorlesenStopp(); return; }
  const auswahl = window.getSelection();
  const markiert = auswahl.rangeCount ? auswahl.toString().trim() : '';
  await vorlesenLassen(markiert || Dokument.lies().text);
};

B.vorlesenAbSatz = async () => {
  /* Von der Schreibstelle bis zum Ende — so hört man weiter, wo man
     aufgehört hat, statt jedes Mal von vorn. */
  const auswahl = window.getSelection();
  const text = Dokument.lies().text;
  if (!auswahl.rangeCount) { await vorlesenLassen(text); return; }

  let absatz = auswahl.anchorNode;
  while (absatz && absatz !== feld && absatz.parentNode !== feld) absatz = absatz.parentNode;
  if (!absatz || absatz === feld) { await vorlesenLassen(text); return; }

  const ab = text.indexOf(absatz.textContent.trim().slice(0, 40));
  await vorlesenLassen(ab >= 0 ? text.slice(ab) : text);
};

B.vorlesenStopp = async () => {
  try { await fetch('vorlesen-stopp', { method: 'POST' }); } catch (e) { /* egal */ }
  spricht = false;
  menueBauen();
  melde('Vorlesen angehalten.');
};

B.stimmeWaehlen = async () => {
  let stimmen = [];          // die des Systems (espeak)
  let gut = [];              // die aufgenommenen (Piper)
  try {
    const antwort = await fetch('stimmen');
    if (antwort.ok) {
      const daten = await antwort.json();
      stimmen = daten.stimmen || [];
      gut = daten.gut || [];
    }
  } catch (e) { /* kein eigenes Fenster */ }

  if (!stimmen.length && !gut.length) {
    melde('Es sind keine deutschen Stimmen eingerichtet.');
    return;
  }

  /* Die aufgenommenen zuerst, und mit Abstand. Sie stehen nicht gleichrangig
     neben den espeak-Stimmen: Ein Formantsynthesizer klingt zwangsläufig nach
     Maschine, und wer das nicht weiß, probiert sich durch hundert Varianten
     und wundert sich, dass keine besser wird. */
  const auswahl = gut.map((s) => ['piper:' + s.kennung, s.name]);
  if (gut.length && stimmen.length) auswahl.push(['', '— aus dem System —']);
  for (const n of stimmen) auswahl.push([n, n]);
  if (!gut.length) auswahl.unshift(['', 'Voreinstellung']);

  const erklaerung = gut.length
    ? (gut.length === 1 ? 'Eine aufgenommene Stimme steht bereit'
                        : gut.length + ' aufgenommene Stimmen stehen bereit')
      + ' (Piper). Die ' + stimmen.length + ' darunter kommen von espeak und '
      + 'klingen zwangsläufig blechern — sie lohnen nur, wenn eine der oberen '
      + 'ein bestimmtes Wort falsch betont.\n\n'
      + 'Weitere holt ./stimme-holen.sh.'
    : stimmen.length + ' deutsche Stimmen stehen zur Wahl. Alle kommen von '
      + 'espeak und klingen nach Maschine. ./stimme-holen.sh holt eine '
      + 'aufgenommene.';

  fenster('Stimme und Tempo', [
    { art: 'satz', text: erklaerung },
    { schluessel: 'stimme', name: 'Stimme', art: 'auswahl',
      werte: auswahl, wert: Speicher.lies('stimme', '') },
    { schluessel: 'tempo', name: 'Tempo (−100 bis 100)', art: 'number',
      wert: String(Speicher.lies('lesetempo', 0)), schritt: '10' },
  ], (werte) => {
    Speicher.schreib('stimme', werte.stimme);
    Speicher.schreib('lesetempo', Math.max(-100, Math.min(100, parseInt(werte.tempo, 10) || 0)));
    /* Gleich hören statt „gemerkt" lesen: Bei einer Stimme ist die Probe die
       Antwort, nicht die Bestätigung. */
    vorlesenLassen('Guten Tag. So klingt diese Stimme.');
  });
};

/* ============================================================
   Wortvorhersage beim Tippen

   Nach drei Buchstaben stehen passende Wörter über der Schreibstelle. Wer
   unsicher schreibt, muss das Wort nicht zu Ende raten — er erkennt es
   wieder. Wiedererkennen ist leichter als Erinnern.

   Angeboten wird nur, wo es hilft: mitten im Wort, nicht dahinter, und
   nicht bei etwas, das ohnehin schon richtig ist.
   ============================================================ */
/* An, nicht aus. Sie stand auf „aus", und damit fand sie niemand: Wer
   Wortvorhersage braucht, sucht sie nicht in einem Untermenü — er merkt
   nur, dass sie nicht kommt. Sie ist eine der Hilfen, für die es dieses
   Programm gibt; sie gehört nicht hinter einen Schalter.

   Abschalten geht weiterhin: Extras ▸ Beim Schreiben ▸ Wortvorhersage. */
let vorhersageAn = Speicher.lies('vorhersage', true);
let vorhersageKasten = null;
let vorhersageStelle = null;
let vorhersageUhr = null;

function vorhersageWeg() {
  if (vorhersageKasten) { vorhersageKasten.remove(); vorhersageKasten = null; }
  vorhersageStelle = null;
}

function vorhersageZeigen() {
  vorhersageWeg();
  if (!vorhersageAn || lesemodus || gesperrt) return;

  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || !auswahl.isCollapsed) return;
  const knoten = auswahl.anchorNode;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return;

  const text = knoten.data;
  const bis = auswahl.anchorOffset;

  /* Nur wenn der Zeiger am Wortende steht — mitten im Wort wäre jeder
     Vorschlag ein Eingriff in etwas, das gerade entsteht. */
  if (bis < text.length && IST_WORTZEICHEN.test(text[bis])) return;

  let von = bis;
  while (von > 0 && IST_WORTZEICHEN.test(text[von - 1])) von--;
  const anfang = text.slice(von, bis);
  if (anfang.length < 3) return;

  const woerter = Pruefung.faengtAnMit(anfang, 6);
  if (!woerter.length) return;

  const bereich = document.createRange();
  bereich.setStart(knoten, von);
  bereich.setEnd(knoten, bis);
  const masse = bereich.getBoundingClientRect();
  if (!masse.width && !masse.height) return;

  vorhersageStelle = { knoten, von, bis, anfang };

  const kasten = document.createElement('div');
  kasten.className = 'vorhersage';
  woerter.forEach((wort, i) => {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.className = 'vorhersage__wort';
    /* Die Ziffer davor ist kein Zierrat: Mit Strg und der Ziffer nimmt man
       das Wort, ohne die Hand von der Tastatur zu nehmen. */
    knopf.innerHTML = '<span class="vorhersage__zahl">' + (i + 1) + '</span>' + alsSicher(wort);
    knopf.addEventListener('mousedown', (e) => e.preventDefault());
    knopf.addEventListener('click', () => vorhersageNehmen(wort));
    kasten.appendChild(knopf);
  });

  kasten.style.left = Math.max(6, Math.min(window.innerWidth - 260, masse.left)) + 'px';
  kasten.style.top = (masse.bottom + 4) + 'px';
  document.body.appendChild(kasten);
  vorhersageKasten = kasten;
}

function vorhersageNehmen(wort) {
  if (!vorhersageStelle) return;
  const { knoten, von, bis, anfang } = vorhersageStelle;
  vorhersageWeg();

  const bereich = document.createRange();
  bereich.setStart(knoten, von);
  bereich.setEnd(knoten, bis);
  feld.focus();
  Dokument.waehle(bereich);
  /* Die Schreibweise des Anfangs übernehmen: Wer „Ver" getippt hat, will
     „Verzeihung", nicht „verzeihung". */
  document.execCommand('insertText', false, wieGeschrieben(anfang, wort));
  geaendertMelden();
}

B.vorhersage = () => {
  vorhersageAn = !vorhersageAn;
  Speicher.schreib('vorhersage', vorhersageAn);
  if (!vorhersageAn) vorhersageWeg();
  melde(vorhersageAn
    ? 'Wortvorhersage an — ab drei Buchstaben. Strg+1 bis Strg+6 nimmt einen Vorschlag.'
    : 'Wortvorhersage aus.');
  menueBauen();
};

/* ============================================================
   LanguageTool als zweite Meinung

   Bewusst ein eigener Knopf und standardmäßig aus. LanguageTool will
   möglichst viel finden — die Schreibhilfe will möglichst wenig falschen
   Alarm schlagen. Beides zugleich geht nicht, und für jemanden, der
   ohnehin unsicher ist, ist der falsche Alarm das Schlimmere.

   Als zweite Meinung auf Verlangen ist es aber ein Gewinn: Es findet, was
   die eigenen Regeln mit Absicht weglassen.
   ============================================================ */
B.gruendlichPruefen = async () => {
  const text = Dokument.lies().text;
  if (!text.trim()) { melde('Es steht kein Text da.'); return; }

  /* Erst der eigene Prüfer und die KI, dann LanguageTool. Alle drei
     landen im selben Stand. */
  if (Bruecke) {
    funde = Bruecke.pruefen(text, true);
    zeichneFunde(true);
    /* Hier wird nicht geschont: Wer „Gründlich prüfen" drückt, tippt
       gerade nicht — er will sehen, was gefunden wurde. */
    markiereFunde();
  }
  melde('LanguageTool prüft … das dauert beim ersten Mal.');
  let treffer;
  try {
    const antwort = await fetch('languagetool', { method: 'POST', body: text });
    if (!antwort.ok) {
      let grund = 'Fehler ' + antwort.status;
      try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
      throw new Error(grund);
    }
    treffer = await antwort.json();
  } catch (grund) {
    melde('Gründliche Prüfung ging nicht: ' + grund.message);
    return;
  }

  if (!treffer.length) {
    /* Nichts gefunden heißt nicht: alles wegwerfen. Vorher leerte dieser
       Zweig die Liste — wer gründlich prüfte, verlor damit die Funde der
       Schreibhilfe und der KI, weil LanguageTool nichts beizutragen
       hatte. */
    if (Bruecke) {
      funde = Bruecke.offeneFehler().map((f) => f.fund).filter(Boolean);
      zeichneFunde();
      markiereFunde();
      meldeFunde(text.length);
    }
    melde(funde.length
      ? 'LanguageTool hat nichts gefunden — die ' + funde.length
        + (funde.length === 1 ? ' Fund bleibt' : ' Funde bleiben') + ' stehen.'
      : 'LanguageTool hat nichts gefunden.');
    return;
  }

  /* Die Funde in dieselbe Form bringen wie die eigenen — dann zeichnet die
     Seitenleiste sie ohne Sonderbehandlung, und „Zeigen" und „Ändern"
     arbeiten wie gewohnt. */
  KIteil.vorschlaegeLeeren();
  const fremde = treffer.map((t) => ({
    von: t.von, bis: t.bis,
    alt: text.slice(t.von, t.bis),
    neu: t.vorschlag || '',
    zeigeAlt: text.slice(t.von, t.bis) || '(hier)',
    zeigeNeu: t.vorschlag || '—',
    grund: t.grund,
    art: t.vorschlag ? 'tipp' : 'hinweis',
    vonLanguageTool: true,
  }));

  /* Alles in EINEN Fehlerstand. Vorher warf „Gründlich prüfen" die eigenen
     Funde weg und zeigte nur die von LanguageTool — wer gründlich prüfte,
     sah weniger als vorher. Der Entwurf will das Gegenteil (§21): Die
     Quellen laufen zusammen, gleiche Stellen werden vereint. */
  let dazu = fremde.length;
  if (Bruecke) {
    dazu = Bruecke.fremdeFundeAufnehmen(fremde, 'languagetool');
    funde = Bruecke.offeneFehler().map((f) => f.fund).filter(Boolean);
  } else {
    funde = funde.concat(fremde);
  }

  zeichneFunde();
  markiereFunde();
  meldeFunde(text.length);
  melde(dazu + (dazu === 1 ? ' Fund' : ' Funde') + ' von LanguageTool'
      + (Bruecke ? ' — dazu, was die Schreibhilfe schon hatte.'
                 : ' — zusätzlich zu dem, was die Schreibhilfe sucht.'));
};

/* ---- Fenster und Hilfe ---- */

/* Welche Fenster dieses Programms sind gerade offen? Das weiß nur der
   Arbeitsplatz, nicht die Seite — also fragt start.py für sie nach. */
B.fensterListe = async () => {
  let fenstern;
  try {
    const antwort = await fetch('fenster');
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    fenstern = await antwort.json();
  } catch (e) {
    melde('Die Fensterliste gibt es nur im eigenen Fenster.');
    return;
  }
  if (!fenstern.length) { melde('Es ist nur dieses eine Fenster offen.'); return; }

  fenster('Fenster wechseln', [
    { art: 'satz', text: fenstern.length === 1
        ? 'Ein Fenster ist offen.' : fenstern.length + ' Fenster sind offen.' },
    { schluessel: 'kennung', name: 'Fenster', art: 'auswahl',
      werte: fenstern.map((f, i) => [f.kennung, (i + 1) + '. ' + f.titel]) },
  ], async (werte) => {
    try {
      await fetch('fenster-zeigen?kennung=' + encodeURIComponent(werte.kennung), { method: 'POST' });
      melde('Gewechselt.');
    } catch (e) { melde('Das ging nicht: ' + e.message); }
  }, 'Hinwechseln');
};

/* Das Handbuch ist unser eigenes und liegt als handbuch.html neben der
   Oberfläche. Vorher zeigte dieser Punkt auf die Hilfeseite von
   LibreOffice — der bequeme Weg und der falsche: Sie beschreibt ein
   anderes Programm, mit Knöpfen, die es hier nicht gibt, und ohne die, die
   es hier gibt. */
B.handbuch = async () => {
  try {
    const antwort = await fetch('handbuch', { method: 'POST' });
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    melde('Das Handbuch öffnet sich im Browser.');
  } catch (e) {
    /* Ohne eigenes Fenster gibt es keinen, der eine Datei öffnen könnte —
       dann tut es der Weg, den die Seite selbst kennt. */
    window.open('handbuch.html', '_blank');
    melde('Das Handbuch steht in handbuch.html neben dem Programm.');
  }
};

B.neuesFenster = async () => {
  try {
    const antwort = await fetch('neues-fenster', { method: 'POST' });
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    melde('Neues Fenster geöffnet.');
  } catch (e) {
    melde('Das ging nur im eigenen Fenster: ' + e.message);
  }
};

B.tastenHilfe = () => {
  fenster('Tastenkombinationen', [
    { art: 'satz', text:
        'DOKUMENTE\n'
      + 'Strg+N  Neues Dokument   Strg+W  Schließen\n'
      + 'Strg+Tab  Nächstes       Strg+Umschalt+Tab  Voriges\n'
      + 'Strg+O  Öffnen           Strg+S  Speichern\n'
      + 'Strg+Umschalt+S  Speichern unter\n'
      + 'Strg+P  Drucken\n'
      + '\n'
      + 'SCHREIBEN\n'
      + 'Strg+Z  Rückgängig       Strg+Y  Wiederholen\n'
      + 'Strg+B  Fett             Strg+I  Kursiv\n'
      + 'Strg+U  Unterstrichen    Strg+K  Hyperlink\n'
      + 'Strg+F  Suchen           Strg+A  Alles auswählen\n'
      + 'Strg+Enter  Seitenumbruch\n'
      + 'Strg++  Größer           Strg+−  Kleiner\n'
      + 'Strg+0  Normalgröße      Strg+1…6  Vorschlag nehmen\n'
      + 'F3  Textbaustein         Tab  Zur nächsten Lücke\n'
      + '\n'
      + 'HILFE\n'
      + 'F4  Vorlesen             F5  Seitenleiste\n'
      + 'F6  Welche Hilfe wann    F7  Prüfen\n'
      + 'F8  KI-Korrektur         F9  Einstellungen' },
  ], () => {}, 'Schließen');
};

/* ------------------------------------------------------------
   Schnellzugriff auf die Stufen

   Drei Hilfen lassen sich an- und ausschalten, und alle drei lagen in
   Extras ▸ Beim Schreiben. Wer sie nicht kennt, findet sie dort nie — und
   genau das ist passiert: Die Wortvorhersage stand ab Werk auf aus, und
   niemand konnte wissen, dass es sie überhaupt gibt.

   Jetzt stehen sie unter dem Prüfen-Knopf, wo man beim Schreiben ohnehin
   hinsieht. Ein Klick schaltet, die Farbe sagt den Stand.
   ------------------------------------------------------------ */
const SCHNELL = [
  { name: 'Wellen',     lang: 'Rote Wellenlinien unter unbekannten Wörtern',
    an: () => lebendAn,             tun: () => B.rechtschreibung() },
  { name: 'Vorhersage', lang: 'Wortvorhersage ab drei Buchstaben',
    an: () => vorhersageAn,         tun: () => B.vorhersage() },
  { name: 'AutoKorr',   lang: 'AutoKorrektur beim Tippen',
    an: () => autokorrekturAn,      tun: () => B.autokorrektur() },
];

function schnellzugriffBauen() {
  const kiste = $('hilfe-schnell');
  if (!kiste) return;
  kiste.innerHTML = '';

  for (const stufe of SCHNELL) {
    const k = document.createElement('button');
    k.type = 'button';
    const an = !!stufe.an();
    k.className = 'schnell__marke' + (an ? ' schnell__marke--an' : '');
    k.textContent = stufe.name;
    k.title = stufe.lang + (an ? ' — an' : ' — aus');
    k.setAttribute('aria-pressed', an ? 'true' : 'false');
    k.addEventListener('mousedown', (e) => e.preventDefault());
    k.addEventListener('click', () => { stufe.tun(); schnellzugriffBauen(); });
    kiste.appendChild(k);
  }

  /* Und der Weg zur ganzen Erklärung — für den, der wissen will, was die
     drei Wörter bedeuten und was es sonst noch gibt. */
  const mehr = document.createElement('button');
  mehr.type = 'button';
  mehr.className = 'schnell__mehr';
  mehr.textContent = 'Welche Hilfe wann?';
  mehr.title = 'Alle sechs Stufen erklärt (F6)';
  mehr.addEventListener('click', () => B.welcheHilfe());
  kiste.appendChild(mehr);
}

/* ============================================================
   Welche Hilfe wann
   ------------------------------------------------------------
   Die Hilfen sind nicht gleichwertig, sie sind gestuft: oben steht,
   was sofort und umsonst geschieht, unten, was Zeit, ein Programm
   oder Geld kostet. Wer das weiß, geht nur so weit hinunter, wie er
   muss. Deshalb steht es hier und nicht in einer Anleitung, die
   niemand aufmacht.
   ============================================================ */

/* Ein sechster Wert macht die Zeile schaltbar: {an, tun}. Die Seite
   erklärt die Stufen ohnehin — dann soll man sie hier auch umlegen können,
   statt sich die Erklärung zu merken und danach ins Menü zu gehen. */
const HILFE_STUFEN = [
  ['1', 'Rote Wellenlinien', '', 'Gibt es das Wort überhaupt?',
   'sofort beim Tippen',
   { an: () => lebendAn, tun: () => B.rechtschreibung() }],
  ['1', 'Wortvorhersage', '', 'Wie ging das Wort weiter?',
   'ab drei Buchstaben',
   { an: () => vorhersageAn, tun: () => B.vorhersage() }],
  ['1', 'AutoKorrektur', '', 'Bessert das Offensichtliche beim Tippen',
   'zum Beispiel „dass" nach Komma',
   { an: () => autokorrekturAn, tun: () => B.autokorrektur() }],
  ['2', 'Rechtsklick auf ein Wort', '', 'Welches Wort war gemeint?',
   'sucht auch nach dem Klang'],
  ['3', 'Prüfen', 'F7', 'Ist es das richtige Wort? das/dass, wider/wieder',
   'die Schreibhilfe rechts', { jetzt: () => pruefen() }],
  ['4', 'Vorlesen', 'F4', 'Klingt der Satz rund?',
   'Stimmen aus dem System', { jetzt: () => B.vorlesen() }],
  ['5', 'Gründlich prüfen', '', 'Stimmt die Grammatik?',
   'LanguageTool, einmal 400 MB', { jetzt: () => B.gruendlichPruefen() }],
  ['6', 'KI-Korrektur', 'F8', 'Versteht das jemand? Passt der Ton?',
   'Internet und Guthaben', { jetzt: () => KIteil.kiKorrigieren() }],
];

/* Die drei Etiketten sind dieselben, die auch auf den Karten stehen —
   deshalb dieselben Klassen: Wer sie hier sieht, erkennt sie dort wieder. */
const HILFE_SORTEN = [
  ['fehler',  'Sicher falsch',   'Da ist kein Zweifel.',        'blind übernehmen'],
  ['tipp',    'Kommt drauf an',  'Hängt vom Satz ab.',          'kurz hinschauen'],
  ['hinweis', 'Zum Nachdenken',  'Nur ein Anstoß, keine Regel.', 'oft übergehen'],
];

const HILFE_WEG = [
  'Schreiben, ohne auf die Wellenlinien zu achten.',
  'F7 drücken und „Alles Eindeutige übernehmen“ wählen.',
  'Die übrigen Karten einzeln durchgehen.',
  'F4 — einmal vorlesen lassen. Da fällt auf, was keine Regel findet.',
  'Nur wenn der Text sitzen muss: F8.',
];

function hilfeSeiteBauen() {
  const seite = document.createElement('div');
  seite.className = 'hilfeseite';

  const oben = document.createElement('p');
  oben.className = 'hilfeseite__satz';
  oben.textContent = 'Jede Stufe ist langsamer als die darüber und klüger '
    + 'als sie. Fang oben an und geh nur so weit hinunter, wie du musst. '
    + 'Die Stufen 1 bis 5 brauchen kein Internet und kein Konto.';
  seite.appendChild(oben);

  const t1 = document.createElement('h4');
  t1.className = 'hilfeseite__titel';
  t1.textContent = 'Welche Hilfe wann';
  seite.appendChild(t1);

  const treppe = document.createElement('div');
  treppe.className = 'stufen';
  for (const [zahl, name, taste, frage, dazu, schalter] of HILFE_STUFEN) {
    const zeile = document.createElement('div');
    zeile.className = 'stufe';

    const nr = document.createElement('span');
    nr.className = 'stufe__zahl';
    nr.textContent = zahl;
    zeile.appendChild(nr);

    const mitte = document.createElement('div');
    mitte.className = 'stufe__mitte';

    const kopf = document.createElement('div');
    kopf.className = 'stufe__name';
    kopf.appendChild(document.createTextNode(name));
    if (taste) {
      const k = document.createElement('span');
      k.className = 'stufe__taste';
      k.textContent = taste;
      kopf.appendChild(k);
    }
    mitte.appendChild(kopf);

    const f = document.createElement('div');
    f.className = 'stufe__frage';
    f.textContent = frage;
    mitte.appendChild(f);

    zeile.appendChild(mitte);

    const rechts = document.createElement('span');
    rechts.className = 'stufe__dazu';
    rechts.textContent = dazu;
    zeile.appendChild(rechts);

    /* Was sich schalten lässt, bekommt eine Marke; was man nur auslösen
       kann, einen Knopf. Eine Stufe wie „Rechtsklick auf ein Wort" hat
       beides nicht — die ist einfach da. */
    if (schalter && schalter.an) {
      const marke = document.createElement('button');
      marke.type = 'button';
      const an = !!schalter.an();
      marke.className = 'stufe__schalter' + (an ? ' stufe__schalter--an' : '');
      marke.textContent = an ? 'an' : 'aus';
      marke.setAttribute('aria-pressed', an ? 'true' : 'false');
      marke.title = name + (an ? ' ausschalten' : ' einschalten');
      marke.addEventListener('click', () => {
        schalter.tun();
        marke.className = 'stufe__schalter' + (schalter.an() ? ' stufe__schalter--an' : '');
        marke.textContent = schalter.an() ? 'an' : 'aus';
        marke.setAttribute('aria-pressed', schalter.an() ? 'true' : 'false');
      });
      zeile.appendChild(marke);
    } else if (schalter && schalter.jetzt) {
      const knopf = document.createElement('button');
      knopf.type = 'button';
      knopf.className = 'stufe__jetzt';
      knopf.textContent = 'jetzt';
      knopf.title = name + ' jetzt ausführen';
      knopf.addEventListener('click', () => {
        /* Das Fenster zumachen, sonst liegt die Erklärung über dem, was
           sie gerade ausgelöst hat. */
        const grund = knopf.closest('.dialoggrund');
        if (grund) grund.remove();
        schalter.jetzt();
      });
      zeile.appendChild(knopf);
    } else {
      const leer = document.createElement('span');
      leer.className = 'stufe__leer';
      zeile.appendChild(leer);
    }

    treppe.appendChild(zeile);
  }
  seite.appendChild(treppe);

  const t2 = document.createElement('h4');
  t2.className = 'hilfeseite__titel';
  t2.textContent = 'Wie sicher ein Fund ist';
  seite.appendChild(t2);

  const zwei = document.createElement('p');
  zwei.className = 'hilfeseite__satz';
  zwei.textContent = 'Auch innerhalb von F7 gibt es Stufen. Jede Karte in '
    + 'der Seitenleiste trägt eins von drei Etiketten.';
  seite.appendChild(zwei);

  const sorten = document.createElement('div');
  sorten.className = 'stufen';
  for (const [art, name, was, tun] of HILFE_SORTEN) {
    const zeile = document.createElement('div');
    zeile.className = 'stufe stufe--sorte fund--' + art;

    const marke = document.createElement('span');
    marke.className = 'fund__sorte';
    marke.textContent = name;
    zeile.appendChild(marke);

    const mitte = document.createElement('div');
    mitte.className = 'stufe__mitte';
    const f = document.createElement('div');
    f.className = 'stufe__frage';
    f.textContent = was;
    mitte.appendChild(f);
    zeile.appendChild(mitte);

    const rechts = document.createElement('span');
    rechts.className = 'stufe__dazu';
    rechts.textContent = tun;
    zeile.appendChild(rechts);

    sorten.appendChild(zeile);
  }
  seite.appendChild(sorten);

  const drei = document.createElement('p');
  drei.className = 'hilfeseite__satz';
  drei.textContent = '„Alles Eindeutige übernehmen“ fasst nur die erste '
    + 'Sorte an und lässt die anderen beiden in Ruhe. Wenn es eilt, ist das '
    + 'der eine Klick, den du brauchst.';
  seite.appendChild(drei);

  const t3 = document.createElement('h4');
  t3.className = 'hilfeseite__titel';
  t3.textContent = 'Ein Weg durch einen Brief';
  seite.appendChild(t3);

  const liste = document.createElement('ol');
  liste.className = 'hilfeseite__weg';
  for (const schritt of HILFE_WEG) {
    const li = document.createElement('li');
    li.textContent = schritt;
    liste.appendChild(li);
  }
  seite.appendChild(liste);

  const vier = document.createElement('p');
  vier.className = 'hilfeseite__satz';
  vier.textContent = 'Für einen Zettel an die Tür reicht Stufe 1. '
    + 'Für den Widerspruch ans Amt geht man bis 6.';
  seite.appendChild(vier);

  return seite;
}

B.welcheHilfe = () => {
  fenster('Welche Hilfe wann',
    [{ art: 'knoten', knoten: hilfeSeiteBauen() }],
    () => {}, 'Schließen', true);
};

/* ------------------------------------------------------------
   Erweiterungsverwaltung

   Im Writer stehen hier Erweiterungen von fremder Hand. Hier gibt es keine
   — dieses Programm nimmt keine an, und ein leerer Kasten mit einem
   „Hinzufügen"-Knopf, der nichts hinzufügt, wäre Kulisse.

   Was es aber gibt, ist dasselbe in der Sache: Teile, die nicht im Programm
   stecken, einzeln kommen und gehen, und über die man wissen will, ob sie da
   sind. Genau die stehen hier.
   ------------------------------------------------------------ */
B.erweiterungen = async () => {
  let teile = [];
  try {
    const antwort = await fetch('teile');
    if (antwort.ok) teile = await antwort.json();
  } catch (e) { /* im Browser gibt es diese Adresse nicht */ }

  if (!teile.length) {
    melde('Nur im eigenen Fenster zu sehen — im Browser weiß die Seite '
        + 'nichts über den Rechner.');
    return;
  }

  const kasten = document.createElement('div');
  kasten.className = 'teile';
  for (const teil of teile) {
    const zeile = document.createElement('div');
    zeile.className = 'teil' + (teil.da ? ' teil--da' : '');

    const stand = document.createElement('span');
    stand.className = 'teil__stand';
    stand.textContent = teil.da ? 'da' : 'fehlt';

    const mitte = document.createElement('div');
    mitte.className = 'teil__mitte';
    const name = document.createElement('span');
    name.className = 'teil__name';
    name.textContent = teil.name;
    const satz = document.createElement('em');
    satz.className = 'teil__satz';
    satz.textContent = teil.da ? teil.wofuer : teil.wofuer + ' — ' + teil.holen;
    mitte.append(name, satz);

    const groesse = document.createElement('span');
    groesse.className = 'teil__groesse';
    groesse.textContent = teil.groesse;

    zeile.append(stand, mitte, groesse);
    kasten.appendChild(zeile);
  }

  fenster('Erweiterungen', [
    { art: 'satz', text:
        'Drei Teile liegen außerhalb des Programms, weil sie zu groß sind. '
      + 'Sie werden geholt, wenn sie zum ersten Mal gebraucht werden — und '
      + 'ohne sie läuft alles Übrige weiter: Schreiben, Prüfen, ODF.' },
    { art: 'knoten', knoten: kasten },
    { art: 'satz', text:
        'Erweiterungen von fremder Hand nimmt dieses Programm nicht an. Was '
      + 'es kann, steckt im Programm — und was nicht, steht in der Liste der '
      + 'Lücken im LIESMICH.' },
  ], () => {}, 'Schließen', true);
};

B.ueber = () => {
  fenster('Über Lunivo-Office', [
    { art: 'satz', text:
        'Lunivo-Office 1.2\n'
      + 'Ein Raum für Worte\n\n'
      + 'Die Prüfung und der Wortschatz stammen aus der Schreibhilfe.\n'
      + 'Word-Dateien und PDF macht LibreOffice im Hintergrund.\n\n'
      /* Der Satz ist ein Versprechen, also muss er in jedem Fall stimmen.
         Die drei KI-Knöpfe können den Text an einen Dienst im Netz geben —
         aber nur, wenn dafür ein Schlüssel hinterlegt wurde. Ohne Schlüssel
         und mit einem Modell auf diesem Rechner geht nichts hinaus. Genau
         das sagt der zweite Halbsatz, und ohne ihn wäre der erste zu
         großzügig. */
      + 'Was geschrieben wird, bleibt auf diesem Rechner.\n'
      + 'Nichts geht hinaus, ohne dass du es selbst schickst.' },
  ], () => {}, 'Schließen');
};


/* ---- Ansicht ---- */

function setzeZoom(wert) {
  zoom = Math.max(50, Math.min(300, Math.round(wert)));
  $('blatt').style.zoom = (zoom / 100).toFixed(2);
  /* Zahl und Schieber unten rechts entstehen erst in statuszeileBauen(),
     ganz am Ende der Datei — setzeZoom() läuft aber schon vorher, wenn
     der gespeicherte Wert angewandt wird. Ohne diese zwei Prüfungen warf
     der Start hier und brach ab: Die Statuszeile blieb leer, und mit ihr
     alles, was danach kam. */
  const szZahl = document.getElementById('status-zoom');
  if (szZahl) szZahl.textContent = zoom + ' %';
  const szSchieber = document.getElementById('status-schieber');
  if (szSchieber) szSchieber.value = String(zoom);
  Speicher.schreib('zoom', zoom);
  linealAuffrischen();
  fokusAuffrischen();
}
/* ------------------------------------------------------------
   UNTEN RECHTS: die Ansichten und der Vergrößerungsschieber

   Beides gab es schon: die vier Ansichten unter Ansicht ▸
   Dokumentansichten, die Vergrößerung über Strg+ und Strg−. Nur stand
   unten rechts eine Zahl, die man nicht anfassen konnte — und die vier
   Ansichten zwei Menüebenen tief.

   Diese Ecke sieht in jedem Schreibprogramm gleich aus: links die
   Ansichten, rechts der Schieber. Wer von Word oder WPS kommt, greift
   dorthin, ohne nachzudenken. Sie nachzubauen kostet nichts an neuer
   Fähigkeit — es ist ein zweiter, sichtbarer Weg zu dem, was da ist.
   ------------------------------------------------------------ */

/* Die vier Ansichten. „Zwei Seiten" bleibt im Menü: In Word stehen unten
   auch nur vier, und die fünfte hätte die Reihe überladen. */
const SZ_ANSICHTEN = [
  ['blatt',      'blattansicht', 'Drucklayout'],
  ['gliederung', 'gliederung',   'Gliederung'],
  ['lesen',      'lesen',        'Lesemodus'],
  ['web',        'weblayout',    'Weblayout'],
];

function szKnopf(bild, name, tun) {
  const k = document.createElement('button');
  k.type = 'button';
  k.className = 'sz-knopf';
  k.title = name;
  k.setAttribute('aria-label', name);
  k.appendChild(symbol(bild));
  k.addEventListener('click', tun);
  return k;
}

/* Welche Ansicht gerade gilt. Lesemodus und Gliederung sind Schalter mit
   eigenem Zustand, Drucklayout und Weblayout zwei Werte von „layout" —
   unten rechts sollen sie trotzdem wie vier Geschwister aussehen. */
function szAnsichtJetzt() {
  if (lesemodus) return 'lesen';
  if (gliederung) return 'gliederung';
  return layout === 'web' ? 'web' : 'blatt';
}

function szAnsichtWaehlen(wahl) {
  /* Erst die beiden Sonderzustände abräumen, dann den neuen setzen. Ohne
     das säße man im Lesemodus UND in der Gliederung, und kein Knopf käme
     wieder heraus. */
  if (lesemodus && wahl !== 'lesen') B.lesemodus();
  if (gliederung && wahl !== 'gliederung') B.gliederung();
  if (wahl === 'lesen' && !lesemodus) B.lesemodus();
  else if (wahl === 'gliederung' && !gliederung) B.gliederung();
  else if (wahl === 'blatt' || wahl === 'web') setzeLayout(wahl)();
  statuszeileAuffrischen();
}

/* An die Fensterbreite anpassen: die Vergrößerung so wählen, dass das
   Blatt gerade hineinpasst. Gerechnet wird mit der ungezoomten Breite —
   offsetWidth ist bereits gezoomt, und zweimal zu zoomen schaukelt sich
   bei jedem Klick weiter auf. */
B.einpassen = () => {
  const flaeche = $('arbeitsflaeche');
  const blatt = $('blatt');
  if (!flaeche || !blatt) return;
  /* offsetWidth ist hier bereits die UNGEZOOMTE Breite: CSS-zoom skaliert
     die Darstellung, nicht das Layout — anders als transform:scale, das
     offsetWidth ebenfalls unberührt lässt, aber getBoundingClientRect()
     verkleinert. Nachgemessen: offsetWidth 449 bei zoom 0.5, während das
     Rechteck 225 breit ist. Wer hier noch einmal durch zoom teilt, rechnet
     zweimal und der Wert schaukelt sich bei jedem Klick auf. */
  const breiteRoh = blatt.offsetWidth;
  if (!breiteRoh) return;
  /* 48 px Luft: der Rollbalken rechts und ein Rand, damit das Blatt nicht
     an der Kante klebt. */
  setzeZoom(((flaeche.clientWidth - 48) / breiteRoh) * 100);
};

const SZ_STUFEN = [50, 75, 100, 125, 150, 200, 300];

function statuszeileBauen() {
  const kasten = $('status-werkzeuge');
  if (!kasten || !kasten.appendChild) return;
  kasten.innerHTML = '';

  const gruppe = document.createElement('span');
  gruppe.className = 'sz-gruppe';
  gruppe.setAttribute('role', 'group');
  gruppe.setAttribute('aria-label', 'Ansicht');
  for (const [marke, bild, name] of SZ_ANSICHTEN) {
    const k = szKnopf(bild, name, () => szAnsichtWaehlen(marke));
    k.dataset.ansicht = marke;
    gruppe.appendChild(k);
  }
  kasten.appendChild(gruppe);

  const strich = document.createElement('span');
  strich.className = 'sz-trenner';
  kasten.appendChild(strich);

  kasten.appendChild(szKnopf('einpassen', 'An die Fensterbreite anpassen',
                             () => B.einpassen()));

  /* Die Zahl ist ein Knopf: Sie führt durch die üblichen Stufen. Ein
     Klappmenü wäre an dieser Stelle eine Klappe von zwei Zentimetern
     Breite am unteren Bildschirmrand — schwer zu treffen. */
  const prozent = document.createElement('button');
  prozent.type = 'button';
  prozent.className = 'sz-prozent';
  prozent.id = 'status-zoom';
  prozent.title = 'Vergrößerung — klicken für die nächste Stufe';
  prozent.textContent = zoom + ' %';
  prozent.addEventListener('click', () => {
    const naechste = SZ_STUFEN.find((s) => s > zoom) || SZ_STUFEN[0];
    setzeZoom(naechste);
  });
  kasten.appendChild(prozent);

  kasten.appendChild(szKnopfText('−', 'Kleiner', () => B.kleiner()));

  const schieber = document.createElement('input');
  schieber.type = 'range';
  schieber.className = 'sz-schieber';
  schieber.id = 'status-schieber';
  /* Schrittweite 5 und nicht 10: Sonst rastet der Schieber bei 125 % auf
     130 — die Zahl daneben sagte „125 %", der Knopf stand woanders, und
     beide meinten dasselbe. Mit 5 sind alle Stufen aus SZ_STUFEN
     erreichbar. */
  schieber.min = '50'; schieber.max = '300'; schieber.step = '5';
  schieber.value = String(zoom);
  schieber.title = 'Vergrößerung';
  schieber.setAttribute('aria-label', 'Vergrößerung');
  schieber.addEventListener('input', () => setzeZoom(Number(schieber.value)));
  kasten.appendChild(schieber);

  kasten.appendChild(szKnopfText('+', 'Größer', () => B.groesser()));

  kasten.appendChild(szKnopf('vollbild', 'Vollbild', () => B.vollbild()));

  statuszeileAuffrischen();
}

/* Plus und Minus als Zeichen und nicht als Zeichnung: Sie sind in jedem
   Programm Schrift, und ein gezeichnetes Plus sähe daneben fremd aus. */
function szKnopfText(zeichen, name, tun) {
  const k = document.createElement('button');
  k.type = 'button';
  k.className = 'sz-knopf sz-knopf--zeichen';
  k.title = name;
  k.setAttribute('aria-label', name);
  k.textContent = zeichen;
  k.addEventListener('click', tun);
  return k;
}

function statuszeileAuffrischen() {
  const jetzt = szAnsichtJetzt();
  for (const k of document.querySelectorAll('.sz-knopf[data-ansicht]')) {
    const an = k.dataset.ansicht === jetzt;
    k.classList.toggle('sz-knopf--an', an);
    k.setAttribute('aria-pressed', an ? 'true' : 'false');
  }
  const schieber = document.getElementById('status-schieber');
  if (schieber) schieber.value = String(zoom);
}

/* Vollbild. Der Ausstieg ist Escape — das macht der Browser selbst, und
   der Knopf wechselt sein Bild nicht: Er ist ein Umschalter. */
B.vollbild = () => {
  if (document.fullscreenElement) {
    if (document.exitFullscreen) document.exitFullscreen();
    return;
  }
  const wurzel = document.documentElement;
  if (wurzel.requestFullscreen) {
    wurzel.requestFullscreen().catch(() => melde('Vollbild geht hier nicht.'));
  } else {
    melde('Vollbild geht in diesem Fenster nicht.');
  }
};

B.groesser = () => setzeZoom(zoom + 10);
B.kleiner  = () => setzeZoom(zoom - 10);
B.normal   = () => setzeZoom(100);

B.tafelZeigen = () => {
  tafelOffen = !tafelOffen;
  Speicher.schreib('tafel', tafelOffen);
  ansichtAnwenden();
};
B.markenZeigen = () => {
  marken = !marken;
  Speicher.schreib('marken', marken);
  ansichtAnwenden();
};

const THEMEN = ['auto', 'light', 'dark'];

/* ------------------------------------------------------------
   WEICHER KONTRAST

   Kay: „bitte nicht mit diesem Schwarz, das erschlägt einen" — und
   gleich darauf: „es sei denn, du machst das optional."

   Er hat mit beidem recht. Der dunkle Grund ist #1F2225, also fast
   schwarz, und daneben steht ein cremefarbenes Blatt. Nicht die Dunkelheit
   erschlägt, sondern der SPRUNG dazwischen: Das Auge stellt sich bei
   jedem Blick vom Blatt zur Leiste neu ein. Für ein Programm, dessen
   Anwender ohnehin länger auf einer Zeile brauchen, ist das teuer.

   Aber es ist Geschmack, und Geschmack gehört nicht in eine Vorgabe.
   Deshalb ein Schalter statt einer Entscheidung — und deshalb auch kein
   viertes und fünftes Thema: Wer „hell" und „dunkel" kennt, soll nicht
   plötzlich zwischen fünf Wörtern wählen müssen. Der Schalter dämpft das,
   was gerade eingestellt ist.

   Dunkel wird dabei nicht heller im Sinne von blasser — es wird ein
   Grauton statt eines Schwarztons. Hell wird warm statt kühlgrau, damit
   es zum Papierton des Blattes passt.
   ------------------------------------------------------------ */
/* Der Schalter selbst liegt in SCHALTER („weicherKontrast") und wird von
   dort gespeichert und angewandt — hier steht nur, was das Thema angeht.
   Zwei Stellen, die dasselbe Attribut setzen, wären eine zu viel. */
function themaAnwenden() {
  const dunkel = thema === 'dark'
    || (thema === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.dataset.theme = dunkel ? 'dark' : 'light';
}

B.weicherKontrast = () => {
  schalterUmlegen('weicherKontrast');
  menueBauen();
  melde(schalterAn('weicherKontrast')
    ? 'Weicher Kontrast an — der Rand um das Blatt ist jetzt gedämpft.'
    : 'Weicher Kontrast aus.');
};

const setzeThema = (wahl) => () => {
  thema = wahl;
  Speicher.schreib('thema', wahl);
  themaAnwenden();
  menueBauen();
};

function ansichtAnwenden() {
  $('tafel').classList.toggle('tafel--zu', !tafelOffen);
  $('griff').classList.toggle('griff--zu', !tafelOffen);
  $('blatt').classList.toggle('blatt--ohne-marken', !marken);
  menueBauen();
}

/* ============================================================
   3. Die Menüs
   ============================================================ */

const strich = '-';

const MENUES = [
  ['Datei', [
    { name: 'Neu', tun: B.neu, taste: 'Strg+N' },
    { name: 'Öffnen', tun: B.oeffnen, taste: 'Strg+O' },
    { name: 'Zuletzt geöffnet', tun: B.zuletztOeffnen },
    { name: 'Neu aus Vorlage', tun: B.vorlagenWaehlen },
    { name: 'Vorlagenordner', tun: B.vorlagenOrdner },
    strich,
    { name: 'Speichern', tun: B.speichern, taste: 'Strg+S' },
    { name: 'Speichern unter', tun: B.speichernUnter, taste: 'Strg+Umschalt+S' },
    strich,
    { name: 'Drucken', tun: B.drucken, taste: 'Strg+P' },
    { name: 'Druckvorschau', tun: B.vorschau },
    { name: 'Als PDF exportieren', tun: B.speichernPdf },
    { name: 'Druckereinstellungen', tun: B.druckerEinrichten },
    strich,
    { name: 'Dokumenteigenschaften', tun: B.eigenschaften },
    { name: 'Umbenennen', tun: B.umbenennen },
    strich,
    { name: 'Schließen', tun: B.schliessen },
    strich,
    /* Die letzten drei stehen in der Reihenfolge des WPS-Menüs: Hilfe,
       Optionen, Beenden. Dort ganz unten, mit Zahnrad, gleich über dem
       Ausgang — Kay hat das Menü abfotografiert, so steht es darin.

       Sie standen kurz im Band unter „Start ▸ Einstellungen". Das war ein
       Fehlschluss: WPS führt zwar eine Bandgruppe dieses Namens, aber die
       Optionen selbst liegen im Menü hinter dem ☰ und nirgends sonst. */
    { name: 'Hilfe', unter: [
      { name: 'Handbuch', tun: B.handbuch },
      { name: 'Tastenkürzel', tun: B.tastenHilfe },
      { name: 'Erweiterungen', tun: B.erweiterungen },
      { name: 'Über Lunivo Office', tun: B.ueber },
    ] },
    { name: 'Optionen', tun: () => Einstellungen.oeffnen(), taste: 'F9' },
    { name: 'Beenden', tun: B.beenden },
  ]],

  ['Start', [
    { name: 'Zwischenablage', unter: [
      { name: 'Einfügen', tun: B.einfuegen, taste: 'Strg+V' },
      { name: 'Einfügen ohne Formatierung', tun: B.einfuegenOhne },
      { name: 'Ausschneiden', tun: B.ausschneiden, taste: 'Strg+X' },
      { name: 'Kopieren', tun: B.kopieren, taste: 'Strg+C' },
      { name: 'Format übertragen', tun: B.formatUebertragen },
      { name: 'Verlauf', unter: [
        { name: 'Rückgängig', tun: B.rueckgaengig, taste: 'Strg+Z' },
        { name: 'Wiederholen', tun: B.wiederholen, taste: 'Strg+Y' },
      ] },
    ] },
    { name: 'Schriftart', unter: [
      { name: 'Schriftart', tun: () => { const k = document.querySelector('.wz-wahl--schrift'); if (k) k.click(); } },
      { name: 'Schriftgröße', tun: () => { const k = document.querySelector('.wz-wahl--groesse'); if (k) k.focus(); } },
      { name: 'Schrift vergrößern', tun: B.schriftGroesser },
      { name: 'Schrift verkleinern', tun: B.schriftKleiner },
      { name: 'Formatierung löschen', tun: B.schlicht },
      strich,
      { name: 'Fett', tun: B.fett, taste: 'Strg+B' },
      { name: 'Kursiv', tun: B.kursiv, taste: 'Strg+I' },
      { name: 'Unterstrichen', tun: B.unter, taste: 'Strg+U' },
      { name: 'Durchgestrichen', tun: B.durch },
      { name: 'Hochgestellt', tun: B.hoch },
      { name: 'Tiefgestellt', tun: B.tief },
      { name: 'Hervorheben', tun: B.hervorheben },
      { name: 'Schriftfarbe', tun: B.schriftfarbe },
      { name: 'Groß-/Kleinschreibung', tun: B.schreibweise },
      { name: 'Eingeschlossene Zeichen', tun: B.eingeschlosseneZeichen },
      { name: 'Zeichenumriss', tun: B.zeichenumriss },
      { name: 'Formatpipette', tun: B.formatpipette },
      { name: 'Wort-Extras', tun: () => B.wortExtras(null) },
      { name: 'Unterstreichungsart', tun: B.unterstrichArt },
      { name: 'Texteffekte', tun: B.effekt },
    ] },
    { name: 'Absatz', unter: [
      { name: 'Aufzählung', tun: B.punkte },
      { name: 'Nummerierung', tun: B.zahlen },
      { name: 'Einzug & Listenebene', unter: [
        { name: 'Einzug verringern', tun: B.einzugWeniger },
        { name: 'Einzug vergrößern', tun: B.einzugMehr },
        { name: 'Listenebene erhöhen', tun: B.ebeneHoeher },
        { name: 'Listenebene verringern', tun: B.ebeneTiefer },
      ] },
      { name: 'Linksbündig', tun: B.links },
      { name: 'Zentriert', tun: B.mitte },
      { name: 'Rechtsbündig', tun: B.rechts },
      { name: 'Blocksatz', tun: B.block },
      { name: 'Zeilenabstand', unter: [
        { name: 'Einfach (1,0)', tun: zeilenabstand('1.15') },
        { name: 'Eineinhalb (1,5)', tun: zeilenabstand('1.6') },
        { name: 'Doppelt (2,0)', tun: zeilenabstand('2.1') },
      ] },
      { name: 'Absatzrahmen', tun: B.absatzRahmen },
      { name: 'Absatzschattierung', tun: B.absatzSchattierung },
      { name: 'Sortieren', tun: B.sortieren },
      { name: 'Steuerzeichen', tun: B.steuerzeichenZeigen },
    ] },
    { name: 'Stile', unter: [
      { name: 'Formatvorlagen', unter: [
        { name: 'Formatvorlage auswählen', unter: () =>
            vorlagenFuerFeld().map(([wert, name]) => (
              { name, tun: () => vorlageAusFeld(wert) })) },
        { name: 'Neue Formatvorlage…', tun: B.vorlageNeu },
        { name: 'Formatvorlagen verwalten', tun: B.vorlagenVerwalten },
        { name: 'Formatvorlage löschen…', tun: B.vorlageLoeschen },
      ] },
    ] },
    { name: 'Bearbeiten', unter: [
      { name: 'Suchen', tun: B.suchen, taste: 'Strg+F' },
      { name: 'Ersetzen', tun: B.ersetzen },
      { name: 'Suchen und Ersetzen', tun: () => sucheZeigen(true) },
      { name: 'Alles auswählen', tun: B.allesMarkieren, taste: 'Strg+A' },
      { name: 'Objekte auswählen', tun: B.objekteWaehlen },
    ] },
  ]],

  ['Einfügen', [
    { name: 'Seiten', unter: [
      { name: 'Deckblatt', tun: B.deckblatt },
      { name: 'Leere Seite (Hochformat)', tun: () => B.leereSeite(false) },
      { name: 'Leere Seite (Querformat)', tun: () => B.leereSeite(true) },
      { name: 'Seitenumbruch', tun: B.seitenumbruch, taste: 'Strg+Enter' },
    ] },
    { name: 'Tabellen', unter: [
      { name: 'Tabelle einfügen', tun: B.tabelle },
      /* Gleich darunter: Wer eine Tabelle eingefügt hat, will als
         Nächstes, dass sie aussieht wie gewünscht. */
      { name: 'Eigenschaften der Tabelle', tun: B.tabelleEigenschaften },
      { name: 'Schnelltabelle', tun: B.schnelltabelle },
      { name: 'Tabellenblatt', tun: B.tabellenblatt },
    ] },
    { name: 'Illustrationen', unter: [
      { name: 'Bild', tun: B.bild },
      { name: 'Formen', tun: () => B.formenGalerie() },
      { name: 'Form mit eigener Farbe…', tun: B.zeichnen },
      { name: 'Diagramm', tun: B.diagramm },
      { name: 'Bildschirmfoto', tun: B.screenshot },
      { name: 'SmartArt', tun: B.smartart },
      { name: 'Piktogramm', tun: B.piktogramm },
      { name: 'WordArt', tun: B.wordart },
    ] },
    { name: 'Links', unter: [
      { name: 'Hyperlink', tun: B.hyperlink },
      { name: 'Lesezeichen / Textmarke', tun: B.textmarke },
      { name: 'Querverweis', tun: B.querverweis },
    ] },
    { name: 'Kopf- und Fußzeile', unter: [
      { name: 'Kopfzeile', tun: B.kopfzeile, haken: () => kopfAn },
      { name: 'Fußzeile', tun: B.fusszeile, haken: () => fussAn },
      { name: 'Seitenzahl', tun: B.seitennummer },
    ] },
    { name: 'Text', unter: [
      { name: 'Textfeld', tun: B.textfeld },
      { name: 'Bausteine', unter: [
        { name: 'Textbaustein', tun: B.textbausteine, taste: 'F3' },
        { name: 'Schnellbaustein', tun: B.schnellbaustein },
      ] },
      { name: 'Initiale', tun: B.initiale },
      { name: 'Datum', tun: B.datum },
      { name: 'Uhrzeit', tun: B.uhrzeit },
      { name: 'Text aus Datei', tun: B.textAusDatei },
    ] },
    { name: 'Symbole', unter: [
      { name: 'Sonderzeichen', tun: B.sonderzeichen },
      { name: 'Formel', tun: B.formel },
    ] },
  ]],

  ['Seitenlayout', [
    { name: 'Seite einrichten', unter: [
      { name: 'Ränder', unter: [
        { name: 'Normal — oben/unten 25, links/rechts 32 mm', tun: setzeRandVorgabe('normal') },
        { name: 'Schmal — 13 mm ringsum', tun: setzeRandVorgabe('schmal') },
        { name: 'Moderat — oben/unten 25, links/rechts 19 mm', tun: setzeRandVorgabe('moderat') },
        { name: 'Breit — oben/unten 25, links/rechts 51 mm', tun: setzeRandVorgabe('breit') },
        strich,
        { name: 'Benutzerdefinierte Seitenränder…', tun: B.seitenraender },
      ] },
      { name: 'Ausrichtung', unter: [
        { name: 'Hochformat', tun: () => { if (quer) B.querformat(); }, haken: () => !quer },
        { name: 'Querformat', tun: () => { if (!quer) B.querformat(); }, haken: () => quer },
      ] },
      { name: 'Papierformat', unter: [
        { name: 'A4', tun: setzePapier('a4'), haken: () => papier === 'a4' },
        { name: 'A5', tun: setzePapier('a5'), haken: () => papier === 'a5' },
        { name: 'A3', tun: setzePapier('a3'), haken: () => papier === 'a3' },
        { name: 'Letter', tun: setzePapier('letter'), haken: () => papier === 'letter' },
        { name: 'Legal', tun: setzePapier('legal'), haken: () => papier === 'legal' },
      ] },
      { name: 'Spalten', tun: B.spalten },
      { name: 'Textrichtung', tun: () => B.textrichtung(null) },
      /* Sieben Punkte, in der Reihenfolge aus WPS. */
      { name: 'Umbrüche', unter: [
        { name: 'Seitenumbruch', tun: B.seitenumbruch },
        { name: 'Spaltenumbruch', tun: B.spaltenumbruch },
        { name: 'Textflussumbruch', tun: B.textflussumbruch },
        strich,
        { name: 'Abschnittsumbruch auf nächster Seite', tun: () => B.abschnittsumbruch('NextPage') },
        { name: 'Fortlaufender Abschnittsumbruch', tun: () => B.abschnittsumbruch('Continuous') },
        { name: 'Abschnittsumbruch (gerade Seite)', tun: () => B.abschnittsumbruch('EvenPage') },
        { name: 'Abschnittsumbruch auf ungerader Seite', tun: () => B.abschnittsumbruch('OddPage') },
      ] },
    ] },
    { name: 'Absatz', unter: [
      /* Ein Punkt, ein Fenster: Einzug UND Abstand stehen darin. */
      { name: 'Absatz…', tun: () => B.absatz('masse') },
      { name: 'Zeilennummern', tun: () => B.zeilennummern(null) },
      { name: 'Silbentrennung', tun: B.silbentrennung },
    ] },
    { name: 'Anordnen', unter: [
      { name: 'Textumbruch', tun: B.anordnen },
      strich,
      { name: 'Ausrichten', tun: () => B.objektAusrichten(null) },
      { name: 'Drehen', tun: () => B.objektDrehen(null) },
    ] },
    { name: 'Seitenhintergrund', unter: [
      { name: 'Seitenfarbe', tun: () => B.seitenfarbe(null) },
      { name: 'Wasserzeichen', tun: B.wasserzeichen },
      { name: 'Seitenrahmen', tun: B.seitenrahmen },
    ] },
    { name: 'Anordnen', unter: [
      { name: 'Bild/Objekt anordnen', tun: B.anordnen },
    ] },
  ]],

  ['Referenzen', [
    { name: 'Inhaltsverzeichnis', unter: [
      { name: 'Inhaltsverzeichnis', tun: B.inhaltsverzeichnis },
      { name: 'Verzeichnisse aktualisieren', tun: B.verzeichnisseAktualisieren },
    ] },
    { name: 'Fußnoten', unter: [
      { name: 'Fußnote', tun: B.fussnote },
      { name: 'Endnote', tun: B.endnote },
      { name: 'Nächste Note', tun: B.noteWeiter },
      { name: 'Vorige Note', tun: B.noteZurueck },
      { name: 'Notenbereich', tun: B.notenZeigen },
    ] },
    { name: 'Zitate und Literatur', unter: [
      { name: 'Zitat einfügen', tun: B.zitat },
      { name: 'Neue Quelle', tun: B.quelleNeu },
      { name: 'Quellen verwalten', tun: B.quellenVerwalten },
      { name: 'Zitierweise', tun: B.zitierweise },
      { name: 'Literaturverzeichnis', tun: B.literaturverzeichnis },
    ] },
    { name: 'Beschriftungen', unter: [
      { name: 'Beschriftung', tun: B.beschriftung },
      { name: 'Abbildungsverzeichnis', tun: B.abbildungsverzeichnis },
      { name: 'Querverweis', tun: B.querverweis },
    ] },
    { name: 'Index', unter: [
      { name: 'Indexeintrag', tun: B.indexEintrag },
      { name: 'Stichwortverzeichnis', tun: B.stichwortverzeichnis },
    ] },
  ]],

  ['Überprüfen', [
    { name: 'Dokumentprüfung', unter: [
      { name: 'Prüfen', tun: () => pruefen(), taste: 'F7' },
      { name: 'Gründlich prüfen', tun: B.gruendlichPruefen },
      { name: 'Rechtschreibung', tun: B.rechtschreibung, haken: () => lebendAn },
      { name: 'Thesaurus', tun: B.thesaurus },
      { name: 'Wörter zählen', tun: B.woerterZaehlen },
    ] },
    { name: 'Sprache', unter: [
      { name: 'Korrektursprache', tun: B.pruefsprache },
    ] },
    { name: 'Barrierefreiheit', unter: [
      { name: 'Barrierefreiheit prüfen', tun: B.barrierefrei },
    ] },
    { name: 'Kommentare', unter: [
      { name: 'Neuer Kommentar', tun: B.kommentar },
      { name: 'Nächster Kommentar', tun: B.kommentarWeiter },
      { name: 'Voriger Kommentar', tun: B.kommentarZurueck },
      { name: 'Kommentar löschen', tun: B.kommentarWeg },
      { name: 'Alle Kommentare löschen', tun: B.kommentareAlleWeg },
    ] },
    { name: 'Änderungen', unter: [
      { name: 'Änderungen verfolgen', tun: B.verfolgen, haken: () => verfolgenAn },
      { name: 'Markup anzeigen', tun: B.markupUmschalten },
      { name: 'Überarbeitungsbereich', tun: B.ueberarbeitungsbereich },
      { name: 'Änderung annehmen', tun: B.aenderungAnnehmen },
      { name: 'Änderung ablehnen', tun: B.aenderungAblehnen },
      { name: 'Nächste Änderung', tun: B.aenderungWeiter },
      { name: 'Vorige Änderung', tun: B.aenderungZurueck },
      { name: 'Alle annehmen', tun: B.aenderungenUebernehmen },
      { name: 'Alle verwerfen', tun: B.aenderungenVerwerfen },
    ] },
    { name: 'Schützen', unter: [
      { name: 'Bearbeitung sperren', tun: B.bearbeitungSperren },
    ] },
  ]],

  ['Schreibhilfe', [
    { name: 'Prüfen', unter: [
      { name: 'Dokumentprüfung', unter: [
        { name: 'Prüfen', tun: () => pruefen() },
        { name: 'Gründlich prüfen', tun: B.gruendlichPruefen },
        { name: 'Welche Hilfe wann', tun: B.welcheHilfe },
      ] },
    ] },
    { name: 'Beim Schreiben', unter: [
      /* Ein Schalter, kein Prüflauf: Die Gruppe heißt „Beim Schreiben",
         und daneben stehen zwei weitere Schalter. */
      { name: 'Rechtschreibprüfung', tun: B.rechtschreibung, haken: () => lebendAn },
      { name: 'Wortvorhersage', tun: B.vorhersage },
      { name: 'AutoKorrektur', tun: B.autokorrektur },
    ] },
    { name: 'Vorlesen', unter: [
      { name: 'Vorlesen', unter: [
        { name: 'Vorlesen', tun: B.vorlesen, taste: 'F4' },
        { name: 'Ab hier vorlesen', tun: B.vorlesenAbSatz },
        { name: 'Anhalten', tun: B.vorlesenStopp },
        { name: 'Stimme und Tempo', tun: B.stimmeWaehlen },
      ] },
    ] },
    { name: 'KI', unter: [
      { name: 'KI-Korrektur', tun: () => KIteil.kiKorrigieren(), taste: 'F8' },
      { name: 'Vorschläge', tun: () => KIteil.kiVorschlaege() },
    ] },
    { name: 'Anzeigen', unter: [
      { name: 'Seitenleiste Schreibhilfe', tun: B.tafelZeigen, taste: 'F5' },
      { name: 'Optionen', tun: () => Einstellungen.oeffnen() },
    ] },
  ]],

  ['Sendungen', [
    { name: 'Erstellen', unter: [
      { name: 'Umschlag', tun: B.umschlag },
      { name: 'Etiketten', tun: B.etiketten },
    ] },
    { name: 'Seriendruck', unter: [
      { name: 'Seriendruck-Assistent', tun: B.seriendruck },
      { name: 'Seriendruckfeld', tun: B.seriendruckfeld },
      { name: 'Adressblock', tun: B.adressblock },
      { name: 'Regeln', tun: B.seriendruckregel },
    ] },
    { name: 'Vorschau', unter: [
      { name: 'Ergebnisse anzeigen', tun: B.serienVorschau },
    ] },
    { name: 'Formular', unter: [
      { name: 'Textfeld', tun: B.formTextfeld },
      { name: 'Kontrollkästchen', tun: B.formKasten },
      { name: 'Schaltfläche', tun: B.formKnopf },
    ] },
  ]],

  ['Ansicht', [
    { name: 'Dokumentansichten', unter: [
      { name: 'Drucklayout', tun: setzeLayout('blatt'), haken: () => layout === 'blatt' },
      { name: 'Lesemodus', tun: B.lesemodus },
      { name: 'Zwei Seiten', tun: setzeLayout('doppelt'), haken: () => layout === 'doppelt' },
      { name: 'Weblayout', tun: setzeLayout('web'), haken: () => layout === 'web' },
      { name: 'Gliederung', tun: B.gliederung },
    ] },
    /* Ganz oben im Ansicht-Menü, mit Taste — nicht im Untermenü
       „Anzeigen", wo sie zwei Ebenen tief stand. */
    { name: 'Lesehilfe', tun: B.lesehilfe, taste: 'F2' },
    strich,
    { name: 'Anzeigen', unter: [
      { name: 'Lineal', tun: B.linealZeigen, haken: () => lineal },
      { name: 'Vertikales Lineal', tun: B.linealHochZeigen, haken: () => linealHoch },
      { name: 'Gitternetzlinien', tun: B.netzlinien },
      { name: 'Navigationsbereich', tun: B.navigation },
      { name: 'Textbegrenzungen', tun: B.markenZeigen, haken: () => marken },
      { name: 'Seitenleiste Schreibhilfe', tun: B.tafelZeigen },
      { name: 'Zeilenfokus', tun: B.zeilenfokus },
    ] },
    { name: 'Zoom', unter: [
      { name: 'Vergrößern', tun: B.groesser, taste: 'Strg++' },
      { name: 'Verkleinern', tun: B.kleiner, taste: 'Strg+−' },
      { name: '100 %', tun: B.normal, taste: 'Strg+0' },
      { name: 'Seitenbreite', tun: B.zoomBreite },
      { name: 'Eine Seite', tun: B.zoomSeite },
      { name: 'Zoom', tun: B.zoomStufe },
    ] },
    /* Als Funktion, nicht als Liste: Welche Dokumente offen sind, ändert
       sich, während das Fenster steht. Eine einmal gebaute Liste zeigte
       den Stand von damals — derselbe Grund wie bei „Zuletzt geöffnet". */
    { name: 'Fenster', unter: () => [
      /* Erst die Dokumente in DIESEM Fenster, dann die Fenster selbst.
         Die Reihenfolge ist nicht beliebig: Wer „Fenster" aufklappt, weil
         er zu einem anderen Brief will, meint meistens einen Reiter und
         nicht ein zweites Fenster. */
      ...Dokumente.liste().map((nr) => ({
        name: Dokumente.name(nr)
            + ((nr === Dokumente.aktiv() ? geaendert : geaendertJe[nr]) ? ' *' : ''),
        tun: () => dokumentWechseln(nr),
        haken: () => nr === Dokumente.aktiv(),
      })),
      strich,
      { name: 'Neues Dokument', tun: B.neu, taste: 'Strg+N' },
      { name: 'Dokument schließen', tun: () => dokumentSchliessen(), taste: 'Strg+W' },
      { name: 'Nächstes Dokument', tun: () => dokumentWechseln(Dokumente.weiter(1)),
        taste: 'Strg+Tab' },
      strich,
      { name: 'Neues Fenster', tun: B.neuesFenster },
      { name: 'Anordnen', unter: [
        { name: 'Nebeneinander', tun: B.fensterNebeneinander },
        { name: 'Untereinander', tun: B.fensterUntereinander },
        { name: 'Kacheln', tun: B.fensterKacheln },
      ] },
      { name: 'Nebeneinander', tun: B.fensterNebeneinander },
      { name: 'Untereinander', tun: B.fensterUntereinander },
      { name: 'Kacheln', tun: B.fensterKacheln },
      { name: 'Fensterliste', tun: B.fensterListe },
    ] },
    { name: 'Helligkeit', unter: [
      { name: 'Wie das System', tun: setzeThema('auto'), haken: () => thema === 'auto' },
      { name: 'Immer hell', tun: setzeThema('light'), haken: () => thema === 'light' },
      { name: 'Immer dunkel', tun: setzeThema('dark'), haken: () => thema === 'dark' },
      /* Kein viertes Thema, sondern ein Schalter daneben: Wer „hell" und
         „dunkel" kennt, soll nicht plötzlich zwischen fünf Wörtern wählen. */
      { name: 'Weicher Kontrast', tun: () => B.weicherKontrast(),
        haken: () => schalterAn('weicherKontrast') },
    ] },
    { name: 'Oberfläche', unter: [
      { name: 'Register anpassen', tun: B.registerAnpassen },
      { name: 'Symbol austauschen', tun: B.symbolTauschen },
      { name: 'Benutzeroberfläche', tun: B.benutzeroberflaeche },
      { name: 'Menüleiste', tun: B.menueleisteZeigen },
      { name: 'Symbolleisten', tun: B.leistenZeigen },
      { name: 'Vorlagen zurücksetzen', tun: B.vorlagenZurueck },
    ] },
  ]],
];

let offenesMenue = null;

function menuePunktTun(punkt) {
  punkt.tun();
}

/* Ein Menüpunkt kann selbst wieder eine Liste tragen — dann klappt sie zur
   Seite auf. Ohne das würden die Menüs endlos: Was zusammengehört, gehört
   auch zusammengefasst, sonst sucht man in dreißig Zeilen. */
function punkteBauen(klappe, punkte) {
  for (const punkt of punkte) {
    if (punkt === strich) {
      const linie = document.createElement('div');
      linie.className = 'menue__strich';
      klappe.appendChild(linie);
      continue;
    }

    if (punkt.unter) {
      const huelle = document.createElement('div');
      huelle.className = 'untermenue';

      const kopf = document.createElement('button');
      kopf.className = 'menue__punkt menue__punkt--auf';
      kopf.setAttribute('role', 'menuitem');
      kopf.setAttribute('aria-haspopup', 'true');

      const platz = document.createElement('span');
      platz.className = 'haken';
      kopf.appendChild(platz);
      kopf.appendChild(document.createTextNode(punkt.name));

      const pfeil = document.createElement('span');
      pfeil.className = 'menue__pfeil';
      pfeil.textContent = '›';
      kopf.appendChild(pfeil);

      /* Der Kopf selbst führt nichts aus — er macht nur auf. Ein Klick darf
         das Menü deshalb nicht schließen. */
      kopf.addEventListener('click', (e) => e.stopPropagation());
      huelle.appendChild(kopf);

      const unterklappe = document.createElement('div');
      unterklappe.className = 'menue__klappe menue__klappe--unter';
      unterklappe.setAttribute('role', 'menu');

      /* Steht statt der Liste eine Funktion da, wird sie beim Aufklappen
         gefragt — für Einträge, die sich ändern, während das Fenster steht.
         Die zuletzt benutzten Dateien sind der Fall dafür: Einmal beim Bauen
         gezeichnet, zeigte das Menü bis zum Neustart den Stand von damals. */
      const fuellen = () => {
        unterklappe.innerHTML = '';
        punkteBauen(unterklappe,
                    typeof punkt.unter === 'function' ? punkt.unter() : punkt.unter);
      };
      fuellen();
      huelle.appendChild(unterklappe);

      /* Auf- und zugeklappt wird von Hand, nicht über „:hover" im Stilblatt.
         Der Grund ist die Messung: Nach welcher Seite Platz ist, lässt sich
         erst sagen, wenn die Klappe sichtbar ist — und beim Hover übers
         Stilblatt ist sie das im Augenblick des Ereignisses noch nicht.
         So ist die Reihenfolge festgelegt: erst zeigen, dann messen. */
      huelle.addEventListener('mouseenter', () => {
        if (typeof punkt.unter === 'function') fuellen();
        for (const andere of huelle.parentNode.querySelectorAll('.untermenue--offen')) {
          andere.classList.remove('untermenue--offen');
        }
        huelle.classList.add('untermenue--offen');
        seiteWaehlen(unterklappe);
      });
      huelle.addEventListener('mouseleave', () => huelle.classList.remove('untermenue--offen'));

      klappe.appendChild(huelle);
      continue;
    }

    const eintrag = document.createElement('button');
    eintrag.className = 'menue__punkt';
    eintrag.setAttribute('role', 'menuitem');

    const haken = document.createElement('span');
    haken.className = 'haken';
    haken.textContent = punkt.haken && punkt.haken() ? '✓' : '';
    eintrag.appendChild(haken);
    eintrag.appendChild(document.createTextNode(punkt.name));

    if (punkt.taste) {
      const taste = document.createElement('span');
      taste.className = 'taste';
      taste.textContent = punkt.taste;
      eintrag.appendChild(taste);
    }
    eintrag.addEventListener('click', () => { menueSchliessen(); menuePunktTun(punkt); });
    klappe.appendChild(eintrag);
  }
}

/* Passt die Klappe noch nach rechts, oder muss sie nach links?

   Gemessen wird erst, wenn sie sichtbar ist — vorher hat sie keine Maße.
   „requestAnimationFrame" wartet genau den einen Augenblick ab, den der
   Zeichner dafür braucht. */
function seiteWaehlen(klappe) {
  messenUndKippen(klappe);
  /* Und gleich noch einmal, sobald der Zeichner fertig ist: Wird ein Menü
     im selben Augenblick geöffnet, in dem die Klappe aufgeht, kann die erste
     Messung noch die alte Lage sehen. Die zweite hat immer die richtige. */
  setTimeout(() => messenUndKippen(klappe), 0);
}

function messenUndKippen(klappe) {
  klappe.classList.remove('menue__klappe--links');

  /* Sofort messen, nicht im nächsten Zeichenschritt: „getBoundingClientRect"
     erzwingt das Rechnen selbst. Über „requestAnimationFrame" ging es schief,
     sobald das Fenster gerade nicht gezeichnet wird — dann lief der Rückruf
     nie, und die Klappe stand weiter über dem Rand. */
  const masse = klappe.getBoundingClientRect();
  if (!masse.width) return;                         // noch nicht sichtbar

  if (masse.right > window.innerWidth - 6) {
    klappe.classList.add('menue__klappe--links');

    /* Bei einem sehr schmalen Fenster steht sie links genauso über. Dann
       lieber zurück nach rechts und dort so weit hereinrücken, wie es geht —
       ein abgeschnittener Rand ist besser als ein unerreichbares Menü. */
    const jetzt = klappe.getBoundingClientRect();
    if (jetzt.left < 4) {
      klappe.classList.remove('menue__klappe--links');
      klappe.style.left = 'auto';
      klappe.style.right = (-(window.innerWidth - masse.right) - 6) + 'px';
      return;
    }
  }
  klappe.style.left = '';
  klappe.style.right = '';
}

function menueBauen() {
  /* Die drei Schalter stehen an DREI Stellen — im Menü, in der
     Seitenleiste und im Band. Wer einen umlegt, soll ihn überall wechseln
     sehen; sonst widersprechen sie sich, und man drückt weiter auf einen,
     der schon umgelegt ist.

     Die Lampen im Band hingen vorher hinterher: Sie frischten sich erst
     auf, wenn die Schreibstelle sich das nächste Mal bewegte. Wer die
     Wellenlinien in der Seitenleiste ausschaltete, sah im Band noch eine
     Weile „an". */
  schnellzugriffBauen();
  registerSchalterAuffrischen();
  const leiste = $('menueleiste');
  leiste.innerHTML = '';
  for (const [titel, punkte] of MENUES) {
    const kasten = document.createElement('div');
    kasten.className = 'menue';

    const knopf = document.createElement('button');
    knopf.className = 'menue__titel';
    knopf.textContent = titel;
    knopf.setAttribute('aria-haspopup', 'true');
    kasten.appendChild(knopf);

    const klappe = document.createElement('div');
    klappe.className = 'menue__klappe';
    klappe.setAttribute('role', 'menu');
    punkteBauen(klappe, punkte);

    kasten.appendChild(klappe);
    knopf.addEventListener('click', (e) => {
      e.stopPropagation();
      const warOffen = kasten.classList.contains('menue--offen');
      menueSchliessen();
      if (!warOffen) {
        kasten.classList.add('menue--offen');
        offenesMenue = kasten;
        seiteWaehlen(klappe);
      }
    });
    /* Wie überall: Ist ein Menü offen, klappt beim Vorbeiziehen das nächste
       auf. Ist keines offen, passiert beim Vorbeiziehen nichts. */
    knopf.addEventListener('mouseenter', () => {
      if (!offenesMenue || offenesMenue === kasten) return;
      menueSchliessen();
      kasten.classList.add('menue--offen');
      offenesMenue = kasten;
      seiteWaehlen(klappe);
    });

    leiste.appendChild(kasten);
  }
}

function menueSchliessen() {
  for (const offen of document.querySelectorAll('.untermenue--offen')) {
    offen.classList.remove('untermenue--offen');
  }
  if (offenesMenue) offenesMenue.classList.remove('menue--offen');
  offenesMenue = null;
}
document.addEventListener('click', menueSchliessen);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') menueSchliessen(); });

/* ============================================================
   4. Die Werkzeugleiste
   ============================================================ */

/* Die Schriften, mit denen ein Brief lesbar wird — Serifen zum Lesen,
   Serifenlose für Überschriften und Formulare, eine mit fester Breite.
   Sie stehen oben, weil eine Liste mit fünfhundert Namen zwar vollständig
   wäre, aber niemandem bei der Wahl hilft. Was sonst noch installiert ist,
   trägt der Server darunter nach. */
const SCHRIFTEN = ['Georgia', 'Liberation Serif', 'Times New Roman', 'Liberation Sans',
                   'Arial', 'Verdana', 'DejaVu Sans', 'DejaVu Serif', 'Courier New'];

/* ------------------------------------------------------------
   Die Schriftauswahl.

   Sie ist kein <select>, und das hat einen Grund. Ein Klappfeld zeichnet
   das System, nicht die Seite — jeder Name stünde dort in derselben
   Schrift. Bei „Liberation Serif" mag das reichen; bei einer Sammlung mit
   „Bleeding Cowboys", „Butch & Sundance Chrome" und „BILLY THE KID" sagt
   der Name nichts darüber, wie sie aussieht. Und mit fünfhundert Namen
   scrollt man sich zu Tode.

   Also eine eigene Liste: jeder Name in seiner eigenen Schrift, ein
   Suchfeld darüber. Genau das, was LibreOffice an dieser Stelle auch tut.
   ------------------------------------------------------------ */
let wzSchrift = null;        // der Knopf, der den Namen zeigt
let schriftListe = null;     // die aufklappbare Liste

/* Das Suchfeld in der Liste braucht den Fokus, damit man tippen kann — und
   in dem Augenblick verliert der markierte Text im Blatt seine Markierung.
   Wer drei Wörter markiert und eine Schrift wählt, bekäme sie dann nicht auf
   die drei Wörter, sondern auf gar nichts. Also wird die Markierung
   festgehalten, bevor der Fokus weggeht, und vor dem Anwenden wieder
   hergestellt. */
let gemerkteAuswahl = null;

function auswahlMerken() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) { gemerkteAuswahl = null; return; }
  const bereich = auswahl.getRangeAt(0);
  gemerkteAuswahl = feld.contains(bereich.commonAncestorContainer)
    ? bereich.cloneRange()
    : null;
}

function auswahlZurueck() {
  feld.focus();
  if (gemerkteAuswahl) Dokument.waehle(gemerkteAuswahl);
}
let alleSchriften = SCHRIFTEN.slice();
/* Was im Schriftknopf steht, wenn noch nie etwas gewählt wurde.

   Es war SCHRIFTEN[0] — Georgia. Seit die Grundschrift OpenDyslexic ist,
   stand dort ein Name, der nicht stimmte: Das Blatt zeigte die eine
   Schrift, der Knopf nannte die andere. Liegt OpenDyslexic auf diesem
   Rechner nicht, fällt es weiter unten auf die erste zurück, die da ist. */
let schriftJetzt = Speicher.lies('schrift', 'OpenDyslexic');

/* ------------------------------------------------------------
   Die Grundschrift des Blattes

   Die Schrift in der Werkzeugleiste färbt das Markierte. Was ein neu
   angefangener Text bekommt, stand bisher nur im Stylesheet — 12pt Georgia,
   für jeden gleich. Wer immer in 14pt schreibt, stellte es bei jedem
   Dokument von Hand ein.

   Gesetzt wird am Element, nicht als Regel: Ein <span> mit eigener Schrift
   im Text bleibt davon unberührt, und beim Speichern nach ODF wandert die
   Grundschrift als Absatzvorlage mit.
   ------------------------------------------------------------ */
function grundschriftAnwenden(name, groesse) {
  if (name !== undefined) Speicher.schreib('grundschrift', name || '');
  if (groesse !== undefined) Speicher.schreib('grundgroesse', Number(groesse) || 12);

  const schrift = Speicher.lies('grundschrift', '');
  const punkte = Number(Speicher.lies('grundgroesse', 12)) || 12;
  for (const teil of [feld, $('kopfzeile'), $('fusszeile')]) {
    if (!teil) continue;
    teil.style.fontFamily = schrift ? '"' + schrift + '"' : '';
    teil.style.fontSize = punkte + 'pt';
  }
}

function schriftKnopfBauen() {
  const huelle = document.createElement('span');
  huelle.className = 'schriftwahl';

  wzSchrift = document.createElement('button');
  wzSchrift.className = 'wz-wahl wz-wahl--schrift';
  wzSchrift.type = 'button';
  wzSchrift.textContent = schriftJetzt;
  wzSchrift.title = 'Schriftart';
  wzSchrift.addEventListener('mousedown', (e) => {
    e.preventDefault();          // den Fokus im Blatt lassen
    auswahlMerken();             // und wissen, was dort markiert war
  });
  wzSchrift.addEventListener('click', () => schriftListeZeigen(!schriftListe.hidden ? false : true));

  schriftListe = document.createElement('div');
  schriftListe.className = 'schriftliste';
  schriftListe.hidden = true;

  huelle.append(wzSchrift, schriftListe);
  return huelle;
}

/* Wie viele Zeilen auf einmal. Fünfhundert Vorschauen gleichzeitig zu
   zeichnen dauert im Fenster mehrere Sekunden — man drückt auf den Knopf und
   glaubt, es sei nichts passiert. Also erst so viele, wie in die Liste
   passen, und beim Rollen kommt der Rest nach. */
const SCHRIFT_HAPPEN = 40;

let schriftTreffer = [];      // die gefilterte Liste, flach: Gruppen und Namen
let schriftGezeigt = 0;

/* Schriften, die eigens fürs leichtere Lesen gemacht sind. Sie liegen
   nicht im Projekt — ./schrift-holen.sh holt sie. Steht eine davon auf dem
   Rechner, gehört sie ganz nach oben: Wer sie geholt hat, sucht sie, und
   zwischen neunhundert anderen findet man sie nicht. */
const LESESCHRIFTEN = ['OpenDyslexic', 'Lexend', 'Atkinson Hyperlegible'];

function schriftListeBauen(suche = '') {
  const wort = suche.trim().toLowerCase();
  const passt = (name) => !wort || name.toLowerCase().includes(wort);
  const lesbar = LESESCHRIFTEN.filter((s) => alleSchriften.includes(s));
  const bewaehrt = SCHRIFTEN.filter(
    (s) => alleSchriften.includes(s) && !lesbar.includes(s));
  const uebrige = alleSchriften.filter(
    (s) => !bewaehrt.includes(s) && !lesbar.includes(s));

  schriftTreffer = [];
  for (const [titel, namen] of [['Leichter zu lesen', lesbar],
                                ['Für Fließtext', bewaehrt.length ? bewaehrt : SCHRIFTEN],
                                ['Alle Schriften auf diesem Rechner', uebrige]]) {
    const treffer = namen.filter(passt);
    if (!treffer.length) continue;
    schriftTreffer.push({ gruppe: titel });
    for (const name of treffer) schriftTreffer.push({ name });
  }

  const kasten = schriftListe.querySelector('.schriftliste__rollen');
  kasten.innerHTML = '';
  kasten.scrollTop = 0;
  schriftGezeigt = 0;

  if (!schriftTreffer.length) {
    const leer = document.createElement('p');
    leer.className = 'schriftliste__leer';
    leer.textContent = 'Keine Schrift mit „' + suche + '" im Namen.';
    kasten.appendChild(leer);
    return;
  }

  schriftZeilenNachlegen();
}

function schriftZeilenNachlegen() {
  const kasten = schriftListe.querySelector('.schriftliste__rollen');
  const bis = Math.min(schriftGezeigt + SCHRIFT_HAPPEN, schriftTreffer.length);

  for (; schriftGezeigt < bis; schriftGezeigt++) {
    const eintrag = schriftTreffer[schriftGezeigt];

    if (eintrag.gruppe) {
      const kopf = document.createElement('div');
      kopf.className = 'schriftliste__gruppe';
      kopf.textContent = eintrag.gruppe;
      kasten.appendChild(kopf);
      continue;
    }

    const name = eintrag.name;
    const zeile = document.createElement('button');
    zeile.type = 'button';
    zeile.className = 'schriftzeile' + (name === schriftJetzt ? ' schriftzeile--an' : '');

    /* Der Name in seiner eigenen Schrift — und darunter klein noch einmal.
       Manche Sammlerschrift schreibt ihren eigenen Namen so verschnörkelt,
       dass man ihn sonst nicht entziffert. */
    const probe = document.createElement('span');
    probe.className = 'schriftzeile__probe';
    probe.style.fontFamily = '"' + name.replace(/"/g, '') + '"';
    probe.textContent = name;

    const klein = document.createElement('small');
    klein.className = 'schriftzeile__name';
    klein.textContent = name;

    zeile.append(probe, klein);
    zeile.addEventListener('mousedown', (e) => e.preventDefault());
    zeile.addEventListener('click', () => {
      schriftJetzt = name;
      Speicher.schreib('schrift', name);
      wzSchrift.textContent = name;
      auswahlZurueck();          // erst die Markierung zurück, dann färben
      schriftart(name);
      schriftListeZeigen(false);
    });
    kasten.appendChild(zeile);
  }
}

/* Die Liste an den Knopf hängen — aber nicht in ihn hinein.

   Im Register steckt der Knopf im Band, und das Band rollt seitlich. Was
   aber auf einer Achse rollt, schneidet der Browser auch auf der anderen
   ab: Die Liste stand dann als Streifen von zwanzig Pixeln unter dem Knopf,
   und von neunhundert Schriften war eine halbe zu sehen.

   Deshalb wird sie aus dem Band gelöst und über das Fenster gelegt. Die
   Stelle des Knopfes sagt, wohin — und was das Fenster noch hergibt, wie
   hoch. */
function schriftListeStellen() {
  const platz = wzSchrift.getBoundingClientRect();
  const breite = schriftListe.offsetWidth || 330;

  schriftListe.style.position = 'fixed';
  schriftListe.style.top = (platz.bottom + 4) + 'px';
  /* Nicht über den rechten Rand hinaus: Steht der Knopf weit rechts, rutscht
     die Liste so weit nach links, dass sie ganz im Fenster liegt. */
  schriftListe.style.left =
    Math.max(8, Math.min(platz.left, window.innerWidth - breite - 8)) + 'px';

  /* Höher als das Fenster darf sie nicht werden — sonst reicht sie unten
     hinaus und die letzten Zeilen sind nicht zu erreichen. */
  const rollen = schriftListe.querySelector('.schriftliste__rollen');
  if (rollen) {
    const rest = window.innerHeight - platz.bottom - 24 - 44;   // 44: das Suchfeld
    rollen.style.maxHeight = Math.max(140, Math.min(340, rest)) + 'px';
  }
}

function schriftListeZeigen(an) {
  if (an) {
    if (!schriftListe.querySelector('.schriftliste__rollen')) {
      const suchfeld = document.createElement('input');
      suchfeld.type = 'search';
      suchfeld.className = 'schriftliste__suche';
      suchfeld.placeholder = 'Schrift suchen…';
      suchfeld.addEventListener('input', () => schriftListeBauen(suchfeld.value));
      suchfeld.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { e.stopPropagation(); schriftListeZeigen(false); }
      });
      const rollen = document.createElement('div');
      rollen.className = 'schriftliste__rollen';
      /* Nahe am Ende: den nächsten Happen anhängen. So bleibt das Aufklappen
         schnell, und wer wirklich bis „Zapfino" rollt, bekommt es auch. */
      rollen.addEventListener('scroll', () => {
        if (rollen.scrollTop + rollen.clientHeight > rollen.scrollHeight - 200) {
          schriftZeilenNachlegen();
        }
      });
      schriftListe.append(suchfeld, rollen);
    }
    schriftListe.hidden = false;
    schriftListeStellen();
    schriftListeBauen('');
    const suchfeld = schriftListe.querySelector('.schriftliste__suche');
    suchfeld.value = '';
    suchfeld.focus();
    /* Die gewählte Schrift ins Bild rollen. Steht sie weit hinten, ist sie
       noch gar nicht gezeichnet — dann so lange nachlegen, bis sie da ist.
       Die Grenze verhindert, dass eine Suche ohne Treffer hier hängen
       bleibt. */
    for (let schutz = 0; schutz < 40; schutz++) {
      if (schriftListe.querySelector('.schriftzeile--an')) break;
      if (schriftGezeigt >= schriftTreffer.length) break;
      schriftZeilenNachlegen();
    }
    const gewaehlt = schriftListe.querySelector('.schriftzeile--an');
    if (gewaehlt) gewaehlt.scrollIntoView({ block: 'center' });
  } else {
    schriftListe.hidden = true;
    /* Die Maße wieder abnehmen: Beim nächsten Mal steht der Knopf vielleicht
       woanders, und ein alter Wert setzte die Liste an die Stelle von gestern. */
    schriftListe.style.position = '';
    schriftListe.style.top = '';
    schriftListe.style.left = '';
    auswahlZurueck();
  }
}

/* Woanders hingeklickt heißt: nicht mehr gebraucht. */
document.addEventListener('mousedown', (e) => {
  if (schriftListe && !schriftListe.hidden && !e.target.closest('.schriftwahl')) {
    schriftListeZeigen(false);
  }
});

/* Ändert sich das Fenster oder rollt das Band weiter, während die Liste
   offen steht, stünde sie sonst neben dem Knopf, zu dem sie gehört.
   „Rollen" steigt nicht auf, deshalb wird es auf dem Weg nach unten
   abgefangen. */
window.addEventListener('resize', () => {
  if (schriftListe && !schriftListe.hidden) schriftListeStellen();
});
document.addEventListener('scroll', (e) => {
  if (!schriftListe || schriftListe.hidden) return;
  /* Nicht, wenn die Liste in sich selbst rollt — dann steht der Knopf ja
     still, und neu zu messen hieße nur, bei jeder Zeile zu rechnen. */
  if (e.target instanceof Node && schriftListe.contains(e.target)) return;
  schriftListeStellen();
}, true);

/* Welche Schriften liegen auf diesem Rechner? Nur das Fenster weiß es —
   eine Seite im Browser darf danach nicht fragen. Läuft sie doch einmal im
   Browser, bleibt es bei der kurzen Liste; deshalb hängt hier nichts davon
   ab, dass die Auskunft ankommt. */
async function schriftenNachtragen() {
  let alle;
  try {
    const antwort = await fetch('schriften.json');
    if (!antwort.ok) return;
    alle = await antwort.json();
  } catch (e) { return; }
  if (!Array.isArray(alle) || !alle.length || !wzSchrift) return;

  alleSchriften = alle;

  /* Georgia, Arial und Times New Roman gehören Microsoft und Apple; auf
     einem Linux-Rechner fehlen sie meistens. Das Blatt zeigt dann die freie
     Entsprechung — und im Knopf stünde ein Name, den es hier gar nicht
     gibt. Also die erste, die wirklich da ist. */
  if (!alle.includes(schriftJetzt)) {
    /* Erst die Leseschriften, dann die bewährten: Fehlt OpenDyslexic,
       ist Lexend die nächste, die demselben Zweck dient. */
    schriftJetzt = LESESCHRIFTEN.find((s) => alle.includes(s))
                || SCHRIFTEN.find((s) => alle.includes(s)) || alle[0];
    wzSchrift.textContent = schriftJetzt;
  }

  wzSchrift.title = 'Schriftart — ' + alle.length + ' auf diesem Rechner';
  if (!schriftListe.hidden) schriftListeBauen('');
}
const GROESSEN = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36];
const VORLAGEN = [['p', 'Fließtext'], ['h1', 'Überschrift 1'],
                  ['h2', 'Überschrift 2'], ['h3', 'Überschrift 3']];

/* Dasselbe für das Klappfeld und das Menü — mitgelieferte Vorlagen und
   dahinter die selbst angelegten. Als Funktion und nicht als feste Liste:
   Wer eine Vorlage anlegt, soll sie sofort dort finden. */
function vorlagenFuerFeld() {
  const eigene = Object.entries(vorlagenStile)
    .filter(([, wie]) => wie.eigen)
    .map(([tag, wie]) => [tag, wie.name]);
  return VORLAGEN.concat(eigene);
}

/* Der Wert ist entweder ein Grundelement („h1") oder eines mit Klasse
   („p.eigen-2"). Zwei Wege, ein Feld. */
function vorlageAusFeld(wert) {
  const [grund, klasse] = String(wert).split('.');
  if (klasse) vorlageSetzen(grund, klasse);
  else absatz(grund);
}

/* Ein Eintrag ist [Wert, Beschriftung]. Steht statt der Beschriftung eine
   Liste, wird daraus eine Gruppe mit Überschrift — so wie die Schriften
   dieses Rechners unter denen stehen, die sich für Fließtext bewährt haben. */
function auswahl(klasse, eintraege, beiWahl, titel) {
  const w = document.createElement('select');
  w.className = 'wz-wahl ' + klasse;
  w.title = titel;
  fuelleAuswahl(w, eintraege);
  w.addEventListener('change', () => { beiWahl(w.value); feld.focus(); });
  return w;
}

function fuelleAuswahl(w, eintraege) {
  w.innerHTML = '';
  for (const [wert, name] of eintraege) {
    if (Array.isArray(name)) {
      const gruppe = document.createElement('optgroup');
      gruppe.label = wert;
      for (const [w2, n2] of name) {
        const o = document.createElement('option');
        o.value = w2; o.textContent = n2;
        gruppe.appendChild(o);
      }
      w.appendChild(gruppe);
    } else {
      const o = document.createElement('option');
      o.value = wert; o.textContent = name;
      w.appendChild(o);
    }
  }
}

let wzVorlage = null;
let wzPinsel = null;
let wzTabelle = null;
let wzFormen = null;
let wzVerfolgt = null;
let wzGroesse = null;

/* Kleine Strichzeichnungen statt Buchstaben-Behelfen. Sie stehen hier im
   Code und nicht als Bilddateien daneben: ein Symbol, eine Zeile. */
/* Die Zeichnungen stehen in daten/symbole.js — dort beieinander und ohne
   Programm drumherum. Warum als Pfade und nicht als Dateien, steht dort
   im Kopf erklärt. */


function symbol(name) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', '0 0 24 24');
  s.setAttribute('width', '16');
  s.setAttribute('height', '16');
  s.setAttribute('fill', 'none');
  s.setAttribute('stroke', 'currentColor');
  s.setAttribute('stroke-width', '1.7');
  s.setAttribute('stroke-linecap', 'round');
  s.setAttribute('stroke-linejoin', 'round');
  s.setAttribute('aria-hidden', 'true');
  /* Der Name steht am Bild. Frueher wurde beim Rechtsklick ueber den
     gezeichneten Pfad zurueckgerechnet, welches Symbol gemeint ist — bei
     einer eigenen Zeichnung gibt es aber gar keinen einzelnen Pfad mehr. */
  s.dataset.symbol = name;
  const inhalt = symbolPfad(name) || '';
  if (inhalt.indexOf('<') === -1) {
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', inhalt);
    s.appendChild(p);
  } else {
    /* Eine eigene Zeichnung. Sie wurde beim Anlegen und beim Laden
       nachgebaut; hier steht nur noch, was wir selbst geschrieben haben. */
    s.innerHTML = inhalt;
  }
  return s;
}

function leisteBauen(wohin, aufbau) {
  const leiste = $(wohin);
  leiste.innerHTML = '';

  const trenner = () => {
    const t = document.createElement('span');
    t.className = 'wz__trenner';
    leiste.appendChild(t);
  };
  /* „inhalt" ist entweder der Name eines Symbols oder ein Buchstabe.
     Fett, Kursiv, Unterstrichen und Durchgestrichen zeigt man in
     deutschen Schreibprogrammen als F K U S — das ist kein Behelf,
     das ist die gewohnte Beschriftung. */
  const knopf = (inhalt, titel, tun, klasse = '', zustand = null) => {
    const k = document.createElement('button');
    k.className = 'wz ' + klasse;
    if (SYMBOLE[inhalt]) k.appendChild(symbol(inhalt));
    else k.textContent = inhalt;
    k.title = titel;
    k.setAttribute('aria-label', titel);
    if (zustand) k.dataset.zustand = zustand;
    k.addEventListener('mousedown', (e) => e.preventDefault());   // die Auswahl behalten
    k.addEventListener('click', tun);
    leiste.appendChild(k);
    return k;
  };

  aufbau({ knopf, trenner, leiste });
}

/* ------------------------------------------------------------
   Die obere Leiste: was mit der Datei und dem Dokument zu tun hat.
   Die Reihenfolge ist die aus dem Writer — wer sie kennt, greift
   blind an dieselbe Stelle.
   ------------------------------------------------------------ */
function werkzeugeBauen() {
  leisteBauen('werkzeugleiste', ({ knopf, trenner, leiste }) => {
    /* Ganz vorn dasselbe ☰ wie im Register — gleicher Aufbau, gleiche
       Stelle, gleiche Tafel. */
    leiste.appendChild(menueKnopfBauen());
    trenner();

    /* Die Reihenfolge und die Benennung stammen aus dem Aufbau — DATEI,
       dann START ▸ ZWISCHENABLAGE und ▸ BEARBEITEN, dann das aus
       EINFÜGEN und ÜBERPRÜFEN, was man ständig braucht. Die Leiste ist
       die kurze Fassung desselben Aufbaus, nicht ein zweiter. */
    knopf('neu', 'Neu (Strg+N)', B.neu);
    knopf('oeffnen', 'Öffnen (Strg+O)', B.oeffnen);
    knopf('speichern', 'Speichern (Strg+S)', B.speichern);
    knopf('unter', 'Speichern unter', B.speichernUnter);
    trenner();
    knopf('drucken', 'Drucken (Strg+P)', B.drucken);
    knopf('vorschau', 'Druckvorschau', B.vorschau);
    knopf('pdf', 'Als PDF exportieren', B.speichernPdf);
    trenner();
    knopf('kleben', 'Einfügen (Strg+V)', B.einfuegen);
    knopf('ohneformat', 'Einfügen ohne Formatierung', B.einfuegenOhne);
    knopf('schere', 'Ausschneiden (Strg+X)', B.ausschneiden);
    knopf('kopie', 'Kopieren (Strg+C)', B.kopieren);
    wzPinsel = knopf('pinsel', 'Format übertragen', B.formatUebertragen);
    knopf('zurueck', 'Rückgängig (Strg+Z)', B.rueckgaengig);
    knopf('vor', 'Wiederholen (Strg+Y)', B.wiederholen);
    trenner();
    knopf('lupe', 'Suchen und Ersetzen (Strg+F)', () => sucheZeigen(true));
    trenner();
    knopf('haken', 'Prüfen (F7)', B.rechtschreibpruefung);
    knopf('gruendlich', 'Gründlich prüfen', B.gruendlichPruefen);
    trenner();
    knopf('umbruch', 'Seitenumbruch (Strg+Enter)', B.seitenumbruch);
    /* Der Knopf öffnet das Raster, nicht mehr sofort die zwei
       Zahlenfelder — die stehen im Raster als erster Punkt darunter. */
    wzTabelle = knopf('tabelle', 'Tabelle einfügen', () => B.tabelleRaster(wzTabelle));
    knopf('bild', 'Bild', B.bild);
    wzFormen = knopf('stift', 'Formen', () => B.formenGalerie(wzFormen));
    knopf('saeule', 'Diagramm', B.diagramm);
    trenner();
    knopf('kette', 'Hyperlink', B.hyperlink);
    knopf('kopfz', 'Kopfzeile', B.kopfzeile);
    knopf('fussz', 'Fußzeile', B.fusszeile);
    knopf('zahl', 'Seitenzahl', B.seitennummer);
    trenner();
    knopf('textrahmen', 'Textfeld', B.textfeld);
    knopf('omega', 'Sonderzeichen', B.sonderzeichen);
    trenner();
    wzVerfolgt = knopf('verfolgt', 'Änderungen verfolgen', B.verfolgen);
    knopf('notiz', 'Neuer Kommentar', B.kommentar);
    trenner();
    /* Die Optionen gehören auch hierher. Sie standen erst nur im Band und
       im Menü — dann trug die Leiste einen Befehl nicht, den die anderen
       beiden führten, und wer mit Symbolleisten arbeitet, kam nicht an
       seine Einstellungen. Die Leiste ist die kurze Fassung desselben
       Aufbaus, nicht ein zweiter. */
    knopf('optionen', 'Optionen (F9)', () => Einstellungen.oeffnen());
  });

  /* ------------------------------------------------------------
     Die untere Leiste: alles, was den Text selbst betrifft.
     ------------------------------------------------------------ */
  leisteBauen('werkzeugleiste2', ({ knopf, trenner, leiste }) => {
    /* SCHRIFTART, dann ABSATZ, dann STILE — die Reihenfolge des Aufbaus.
       Das Absatzformat stand vorher ganz vorn; im Aufbau kommen die Stile
       nach dem Absatz, und dort stehen sie jetzt auch. */
    leiste.appendChild(schriftKnopfBauen());
    wzGroesse = auswahl('wz-wahl--groesse', GROESSEN.map((g) => [g, g]),
                        (g) => schriftgroesse(+g), 'Schriftgröße');
    wzGroesse.value = '12';                    // so groß steht der Text im Blatt
    leiste.appendChild(wzGroesse);
    knopf('groesserA', 'Schrift vergrößern', B.schriftGroesser);
    knopf('kleinerA', 'Schrift verkleinern', B.schriftKleiner);
    knopf('radierer', 'Formatierung löschen', B.schlicht);
    trenner();

    knopf('F', 'Fett (Strg+B)', B.fett, 'wz--fett', 'bold');
    knopf('K', 'Kursiv (Strg+I)', B.kursiv, 'wz--kursiv', 'italic');
    knopf('U', 'Unterstrichen (Strg+U)', B.unter, 'wz--unter', 'underline');
    knopf('S', 'Durchgestrichen', B.durch, 'wz--durch', 'strikeThrough');
    knopf('hoch', 'Hochgestellt', B.hoch, '', 'superscript');
    knopf('tief', 'Tiefgestellt', B.tief, '', 'subscript');
    knopf('marker', 'Hervorheben', B.hervorheben);
    knopf('farbe', 'Schriftfarbe', B.schriftfarbe);
    knopf('Aa', 'Groß-/Kleinschreibung', B.schreibweise);
    knopf('unterart', 'Unterstreichungsart', B.unterstrichArt);
    knopf('texteffekt', 'Texteffekte', B.effekt);
    trenner();

    knopf('punkte', 'Aufzählung', B.punkte, '', 'insertUnorderedList');
    knopf('zahlen', 'Nummerierung', B.zahlen, '', 'insertOrderedList');
    knopf('weniger', 'Einzug verringern', B.einzugWeniger);
    knopf('mehr', 'Einzug vergrößern', B.einzugMehr);
    knopf('ebeneHoch', 'Listenebene erhöhen', B.ebeneHoeher);
    knopf('ebeneTief', 'Listenebene verringern', B.ebeneTiefer);
    knopf('links', 'Linksbündig', B.links, '', 'justifyLeft');
    knopf('mitte', 'Zentriert', B.mitte, '', 'justifyCenter');
    knopf('rechts', 'Rechtsbündig', B.rechts, '', 'justifyRight');
    knopf('block', 'Blocksatz', B.block, '', 'justifyFull');

    /* Der Zeilenabstand ist eine Wahl aus dreien — als drei einzelne Knöpfe
       wäre die Leiste noch länger, und man sähe nicht, welcher gerade gilt. */
    const abstand = auswahl('wz-wahl--abstand',
      [['1.15', 'Zeilen 1,0'], ['1.6', 'Zeilen 1,5'], ['2.1', 'Zeilen 2,0']],
      (wert) => zeilenabstand(wert)(), 'Zeilenabstand');
    leiste.appendChild(abstand);

    knopf('rahmen', 'Absatzrahmen', B.absatzRahmen);
    knopf('toenung', 'Absatzschattierung', B.absatzSchattierung);
    knopf('sortieren', 'Sortieren', B.sortieren);
    knopf('steuerzeichen', 'Steuerzeichen', B.steuerzeichenZeigen);
    trenner();

    wzVorlage = auswahl('wz-wahl--vorlage', vorlagenFuerFeld(), vorlageAusFeld, 'Formatvorlage');
    leiste.appendChild(wzVorlage);
  });
}

function werkzeugeAuffrischen() {
  registerSchalterAuffrischen();
  for (const k of $('werkzeugleiste').querySelectorAll('.wz[data-zustand]')) {
    k.classList.toggle('wz--an', Dokument.anGeschaltet(k.dataset.zustand));
  }
  if (wzVorlage) {
    /* Erst der genaue Schlüssel — der trifft auch eine eigene Vorlage.
       Sonst das Grundelement, sonst Fließtext. */
    const drin = (wert) => [...wzVorlage.options].some((o) => o.value === wert);
    const genau = vorlageSchluesselAnStelle();
    const grund = Dokument.absatzformat();
    wzVorlage.value = drin(genau) ? genau : (drin(grund) ? grund : 'p');
  }
}

/* ============================================================
   5. Suchen und Ersetzen
   ============================================================ */

function sucheZeigen(an) {
  $('suchleiste').hidden = !an;
  if (an) $('suche-was').focus();
  else feld.focus();
}

function suche(ab) {
  const was = $('suche-was').value;
  if (!was) return -1;
  const text = Dokument.lies().text;
  let stelle = text.toLowerCase().indexOf(was.toLowerCase(), ab);
  if (stelle === -1) stelle = text.toLowerCase().indexOf(was.toLowerCase());
  return stelle;
}

let sucheAb = 0;

function sucheWeiter() {
  const stelle = suche(sucheAb);
  const was = $('suche-was').value;
  if (stelle === -1) { $('suche-meldung').textContent = 'Nicht gefunden.'; return null; }
  $('suche-meldung').textContent = '';
  Dokument.zeige(stelle, stelle + was.length);
  sucheAb = stelle + was.length;
  return stelle;
}

/* ============================================================
   6. Die Tafel: prüfen, zeigen, ändern
   ============================================================ */

const SORTEN = { tipp: 'Kommt drauf an', hinweis: 'Zum Nachdenken' };

function leereFunde(meldung) {
  funde = [];
  markenEntfernen();
  $('funde').innerHTML = '';
  if (meldung) $('status-pruefung').textContent = meldung;
  $('status-pruefung').classList.remove('statuszeile__fund');
}

function melde(satz) {
  $('status-pruefung').textContent = satz;
  $('status-pruefung').classList.remove('statuszeile__fund');
}

function kuerze(satz) {
  return satz.length > 70 ? satz.slice(0, 68) + '…' : satz;
}

/* Gezeichnet wird oft, gezählt wird selten.

   KI.Gedaechtnis.merkeGezeigt legt ein Wort still, wenn es fünfmal
   angezeigt und nie geändert wurde — die Annahme dahinter: Wer es
   fünfmal stehen lässt, meint es so. Das war richtig gerechnet, solange
   nur auf Knopfdruck geprüft wurde.

   Mit der lebenden Prüfung wird alle 900 Millisekunden neu gezeichnet.
   Dieselbe Zählung hätte jedes angestrichene Wort binnen Sekunden
   stillgelegt — und der Mensch hätte gesehen, wie seine Wellenlinien
   von selbst verschwinden, ohne dass er etwas getan hat.

   Gezählt wird deshalb nur, wenn jemand ausdrücklich prüfen lässt. */
function zeichneFunde(zaehlen) {
  const liste = $('funde');
  liste.innerHTML = '';
  /* Was ignoriert wurde, faellt hier heraus — an EINER Stelle, damit die
     Liste, die Anstriche und die Zaehlung dasselbe zeigen. Drei Stellen
     waeren drei Gelegenheiten, dass sie auseinanderlaufen. */
  if (einmalRuhig.size || ganzRuhig.size) {
    funde = funde.filter((f) => !istIgnoriert(f));
  }
  if (zaehlen) KI.Gedaechtnis.merkeGezeigt(funde);

  if (!funde.length) {
    const leer = document.createElement('p');
    leer.className = 'tafel__leer';
    leer.textContent = 'Nichts gefunden. Das heißt nicht, dass alles richtig ist — '
                     + 'die Schreibhilfe sucht nur die Fehler, die ein Rechtschreibprüfer '
                     + 'nicht finden kann.';
    liste.appendChild(leer);
    return;
  }

  for (const fund of funde) {
    const karte = document.createElement('div');
    karte.className = 'fund fund--' + fund.art;

    const sorte = document.createElement('span');
    sorte.className = 'fund__sorte';
    sorte.textContent = SORTEN[fund.art] || 'Sicher falsch';
    karte.appendChild(sorte);

    if (fund.art === 'hinweis') {
      if (fund.stelle) {
        const stelle = document.createElement('div');
        stelle.className = 'fund__stelle';
        stelle.textContent = '„' + kuerze(fund.stelle) + '“';
        karte.appendChild(stelle);
      }
    } else {
      const zeile = document.createElement('div');
      zeile.className = 'fund__wort';
      const alt = document.createElement('span');
      alt.className = 'fund__falsch'; alt.textContent = fund.zeigeAlt;
      const pfeil = document.createElement('span');
      pfeil.className = 'fund__pfeil'; pfeil.textContent = '→';
      const neu = document.createElement('span');
      neu.className = 'fund__richtig'; neu.textContent = fund.zeigeNeu;
      zeile.append(alt, pfeil, neu);
      karte.appendChild(zeile);
    }

    const grund = document.createElement('small');
    grund.className = 'fund__grund';
    grund.textContent = fund.grund;
    karte.appendChild(grund);

    const knoepfe = document.createElement('div');
    knoepfe.className = 'fund__knoepfe';

    const zeigen = document.createElement('button');
    zeigen.className = 'knopf knopf--klein';
    zeigen.textContent = 'Zeigen';
    zeigen.addEventListener('click', () => Dokument.zeige(fund.von, fund.bis));
    knoepfe.appendChild(zeigen);

    /* Beim Hinweis gibt es nichts zu ersetzen — deshalb auch keinen Knopf
       dafür. Genau wie in der App und in LibreOffice. */
    if (fund.art !== 'hinweis') {
      const aendern = document.createElement('button');
      aendern.className = 'knopf knopf--klein';
      aendern.textContent = 'Ändern';
      aendern.addEventListener('click', () => uebernimm(fund));
      knoepfe.appendChild(aendern);
    }

    /* Anhören. Wer zwischen „das" und „dass" nicht sicher ist, hört den
       Unterschied oft schneller, als er ihn sieht — vorausgesetzt, der
       Satz wird mitgesprochen. Deshalb wird nicht das nackte Wort
       vorgelesen, sondern der Vorschlag samt Begründung. */
    const hoeren = document.createElement('button');
    hoeren.className = 'knopf knopf--klein fund__hoeren';
    hoeren.type = 'button';
    hoeren.title = 'Vorschlag vorlesen';
    hoeren.setAttribute('aria-label', 'Vorschlag vorlesen');
    hoeren.appendChild(symbol('hoeren'));
    hoeren.addEventListener('click', () => {
      const satz = fund.art === 'hinweis'
        ? fund.grund
        : (fund.zeigeNeu || fund.neu || '') + '. ' + (fund.grund || '');
      vorlesenLassen(satz.trim());
    });
    knoepfe.appendChild(hoeren);

    karte.appendChild(knoepfe);
    liste.appendChild(karte);
  }
}

/* ============================================================
   Die Funde im Text selbst

   In der Seitenleiste stehen sie schon. Aber ein Fehler gehört dorthin, wo
   er steht — sonst sucht man ihn beim Lesen. Also bekommt jede Fundstelle
   eine farbige Wellenlinie, genau wie die Rechtschreibprüfung des Systems
   sie zieht.

   Die Markierungen sind kein Teil des Textes: Sie kommen nach dem Prüfen
   hinein und werden vor dem Speichern wieder herausgenommen. Sonst stünden
   sie in der Datei, die jemand anders öffnet.
   ============================================================ */
function markenEntfernen() {
  const marken = feld.querySelectorAll('span.fundmarke');
  for (const marke of marken) {
    const eltern = marke.parentNode;
    while (marke.firstChild) eltern.insertBefore(marke.firstChild, marke);
    marke.remove();
  }
  /* Nach dem Auspacken stehen Textstücke nebeneinander, die zusammengehören.
     Ohne dieses Zusammenlegen zerfiele der Text mit jedem Prüfen weiter, bis
     die Stellenangaben nicht mehr stimmen. */
  if (marken.length) feld.normalize();
}

/* Der Absatz, in dem gerade geschrieben wird — dort wird nicht markiert.

   Die Markierung zerteilt Textknoten. Solange jemand in einem Absatz
   tippt, hält die AutoKorrektur, die Wortvorhersage und der Browser
   selbst Verweise auf genau diese Knoten. Werden sie unter ihnen
   zerschnitten, landen Zeichen an falschen Stellen — im Versuch wurde
   aus „Das ist garnicht weiss und wiederspiegelt." ein „Das ist nd
   wiedegarnicht weiss u".

   Andere Schreibprogramme machen es genauso: Die Zeile, in der der
   Zeiger steht, wird beim Tippen nicht neu gesetzt. Sobald er sie
   verlässt, holt die nächste Prüfung sie nach. */
function absatzAmZeiger() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return null;
  let knoten = auswahl.anchorNode;
  if (knoten && knoten.nodeType === Node.TEXT_NODE) knoten = knoten.parentElement;
  if (!knoten || !feld.contains(knoten)) return null;
  return knoten.closest('p, li, td, th, h1, h2, h3, h4, div') || null;
}

function markiereFunde(schoneAbsatz) {
  markenEntfernen();

  /* Sind die Wellenlinien ausgeschaltet, wird nichts angestrichen — auch
     nicht nach einem ausdrücklichen „Prüfen". Die Funde stehen dann in
     der Seitenleiste, und genau das verspricht der Schalter. Ohne diese
     Zeile zeichnete „Prüfen" sie ungefragt wieder ins Blatt. */
  if (!lebendAn) return;

  /* Von hinten nach vorn: Jede eingesetzte Markierung teilt Textknoten auf.
     Vorn beginnend verschöben sich alle folgenden Stellen. */
  for (let i = funde.length - 1; i >= 0; i--) {
    const fund = funde[i];
    const { text, karte } = Dokument.lies();
    if (text.slice(fund.von, fund.bis) !== (fund.alt || text.slice(fund.von, fund.bis))) continue;

    const bereich = Dokument.bereich(karte, fund.von, fund.bis);

    /* Nicht im Absatz, in dem geschrieben wird. */
    if (schoneAbsatz) {
      const wo = bereich.startContainer.nodeType === Node.TEXT_NODE
        ? bereich.startContainer.parentElement : bereich.startContainer;
      if (wo && schoneAbsatz.contains(wo)) continue;
    }

    /* Reicht ein Fund über mehrere Absätze oder mitten durch eine
       Auszeichnung, ließe er sich nicht in EIN Element fassen. Solche
       Stellen bleiben unmarkiert — sie stehen weiter in der Seitenleiste. */
    if (bereich.startContainer !== bereich.endContainer
        || bereich.startContainer.nodeType !== Node.TEXT_NODE) continue;

    const marke = document.createElement('span');
    marke.className = 'fundmarke fundmarke--' + fund.art;
    marke.dataset.fund = String(i);
    marke.title = fund.grund || '';
    try { bereich.surroundContents(marke); } catch (e) { /* dann eben nicht */ }
  }
}

/* Was gespeichert wird, darf die Markierungen nicht enthalten. */
function ohneMarken(html) {
  if (html.indexOf('fundmarke') === -1 && html.indexOf('absatz--fokus') === -1) return html;
  const hilfe = document.createElement('div');
  hilfe.innerHTML = html;
  for (const marke of hilfe.querySelectorAll('span.fundmarke')) {
    const eltern = marke.parentNode;
    while (marke.firstChild) eltern.insertBefore(marke.firstChild, marke);
    marke.remove();
  }
  /* Die Auszeichnung des Absatzes, in dem gerade geschrieben wird, gehört
     zur Ansicht und nicht zum Text. In der Datei hätte sie nichts zu
     suchen, und auf dem Papier wäre ein Absatz größer als die anderen. */
  for (const absatz of hilfe.querySelectorAll('.absatz--fokus')) {
    absatz.classList.remove('absatz--fokus');
    if (!absatz.getAttribute('class')) absatz.removeAttribute('class');
  }
  return hilfe.innerHTML;
}

/* ============================================================
   Das Menü unter der rechten Maustaste

   So kennt man es aus jedem Schreibprogramm: rechts auf ein angestrichenes
   Wort, und oben stehen die Vorschläge. Ein Klick setzt sie ein.

   Steht der Zeiger nicht auf einem Fund, kommen die üblichen Befehle —
   Ausschneiden, Kopieren, Einfügen.
   ============================================================ */
let rechtsMenue = null;
/* Die kleine Formatleiste, die über dem Menü schwebt. Sie ist ein eigener
   Kasten, kein Teil des Menüs — so hält es der WPS Writer, und es hat
   einen Grund: Das Menü ist eine Liste zum Lesen, die Leiste eine Fläche
   zum Zielen. Zwei verschiedene Dinge gehören nicht ineinander. */
let rechtsLeiste = null;

function rechtsMenueSchliessen() {
  if (rechtsMenue) { rechtsMenue.remove(); rechtsMenue = null; }
  if (rechtsLeiste) { rechtsLeiste.remove(); rechtsLeiste = null; }
}

/* ------------------------------------------------------------
   Das Wort unter dem Mauszeiger.

   Für das Menü unter der rechten Maustaste: Wer auf ein rot angestrichenes
   Wort geht, will Vorschläge sehen — und zwar für dieses Wort, egal ob
   vorher geprüft wurde oder nicht.

   Gefragt wird nach der Schreibstelle an den Bildpunkten, an denen geklickt
   wurde; von dort aus wächst die Auswahl nach links und rechts, solange
   Buchstaben kommen.
   ------------------------------------------------------------ */
const IST_WORTZEICHEN = /[A-Za-zÄÖÜäöüßáàéèíìóòúùâêîôûçñ-]/;

function wortAnPunkt(x, y) {
  let bereich = null;
  if (document.caretRangeFromPoint) {
    bereich = document.caretRangeFromPoint(x, y);
  } else if (document.caretPositionFromPoint) {
    const stelle = document.caretPositionFromPoint(x, y);
    if (stelle) {
      bereich = document.createRange();
      bereich.setStart(stelle.offsetNode, stelle.offset);
    }
  }
  if (!bereich) return null;

  const knoten = bereich.startContainer;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return null;

  const text = knoten.data;
  let von = Math.min(bereich.startOffset, text.length);
  let bis = von;
  while (von > 0 && IST_WORTZEICHEN.test(text[von - 1])) von--;
  while (bis < text.length && IST_WORTZEICHEN.test(text[bis])) bis++;
  if (bis <= von) return null;

  /* Bindestriche am Rand gehören zum Satz, nicht zum Wort. */
  while (bis > von && text[bis - 1] === '-') bis--;
  while (von < bis && text[von] === '-') von++;
  if (bis <= von) return null;

  return { knoten, von, bis, wort: text.slice(von, bis) };
}

/* Setzt ein Wort an seiner Stelle durch ein anderes.
   Über execCommand, damit Strg+Z es zurückholt. */
/* ============================================================
   IGNORIEREN — EINMAL ODER GANZ

   „Einmal ignorieren" gilt fuer DIESE Stelle. „Alle ignorieren" fuer
   dieses Wort im ganzen Dokument, aber nur hier — beim naechsten
   Dokument faengt es wieder an. Das ist der Unterschied zum
   Woerterbuch: Dort steht, was immer richtig ist.

   Wer einen Tippfehler in einem Zitat stehen lassen muss, will ihn
   nicht ins Woerterbuch aufnehmen. Bisher gab es nur diesen einen Weg.
   ============================================================ */
/* Die Klappe an der Rechtschreibpruefung — aus seiner Beschreibung:

   „Wenn die Vorschlaege nicht zur Sprache des Textes passen: In die
   Registerkarte Ueberpruefen wechseln, auf den Pfeil neben
   Rechtschreibpruefung klicken und Sprache fuer Rechtschreibpruefung
   festlegen auswaehlen."

   Dazu die zwei anderen Wege aus seinem Text: der Schalter „Waehrend
   der Eingabe pruefen" und das Bedienfeld mit F7. */
B.pruefungKlappe = (knopf) => {
  designTafelZeigen(knopf, 'Rechtschreibprüfung', (tafel) => {
    tafel.classList.add('designtafel--breit');
    const zeile = (bild, name, taste, tun, gilt) => {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'designtafel__zeile richtungszeile'
        + (gilt ? ' richtungszeile--gilt' : '');
      if (SYMBOLE[bild]) k.appendChild(symbol(bild));
      const w = document.createElement('span');
      w.textContent = name;
      k.appendChild(w);
      if (taste) {
        const t = document.createElement('em');
        t.className = 'klappzeile__taste';
        t.textContent = taste;
        k.appendChild(t);
      }
      k.addEventListener('mousedown', (e) => e.preventDefault());
      k.addEventListener('click', () => { designTafelWeg(); tun(); });
      tafel.appendChild(k);
    };

    zeile('wellen', 'Während der Eingabe prüfen', '',
          () => B.rechtschreibung(), schalterAn('rechtschreibung'));
    zeile('Duden', 'Bedienfeld öffnen', 'F7', () => B.rechtschreibpruefung());

    const strichel = document.createElement('hr');
    strichel.className = 'designtafel__strich';
    tafel.appendChild(strichel);

    zeile('sprache', 'Sprache für Rechtschreibprüfung festlegen…', '',
          () => Einstellungen.oeffnen('sprache'));
    zeile('woerterbuch', 'Eigener Wortschatz…', '',
          () => Einstellungen.oeffnen('rechtschreibpruefung'));

    /* Was in diesem Dokument ignoriert wurde, laesst sich hier
       zuruecknehmen — sonst waere „alle ignorieren" ein Weg ohne
       Rueckweg. */
    if (einmalRuhig.size || ganzRuhig.size) {
      const zweiter = document.createElement('hr');
      zweiter.className = 'designtafel__strich';
      tafel.appendChild(zweiter);
      zeile('radierer',
            'Ignorierte Stellen wieder prüfen (' + (einmalRuhig.size + ganzRuhig.size) + ')',
            '', () => {
              einmalRuhig = new Set();
              ganzRuhig = new Set();
              pruefen();
              melde('Alle Ausnahmen aufgehoben.');
            });
    }
  });
};

let einmalRuhig = new Set();
let ganzRuhig = new Set();

function ruheSchluessel(stelle) {
  /* Der Fund zaehlt im GANZEN Text, das Wort unter dem Zeiger nur in
     seinem Textknoten. Ohne diese Umrechnung traefe „Einmal ignorieren"
     nie die gemeinte Stelle — oder zufaellig eine andere. Die Karte aus
     Dokument.lies() sagt, wo jeder Knoten im Text beginnt. */
  let von = stelle.von;
  try {
    const { karte } = Dokument.lies();
    for (const e of karte) {
      if (e.knoten === stelle.knoten) { von = e.von + stelle.von; break; }
    }
  } catch (fehler) { /* Dann bleibt der Versatz im Knoten — besser als nichts. */ }
  return (stelle.wort || '') + '@' + (von != null ? von : '?');
}

function einmalIgnorieren(stelle) {
  einmalRuhig.add(ruheSchluessel(stelle));
  if (funde.length) pruefen();
}

function alleIgnorieren(wort) {
  ganzRuhig.add(String(wort).toLowerCase());
  if (funde.length) pruefen();
}

/* Gilt diese Stelle als ignoriert? */
function istIgnoriert(fund) {
  if (!fund) return false;
  const wort = String(fund.alt || '').toLowerCase();
  if (wort && ganzRuhig.has(wort)) return true;
  return einmalRuhig.has((fund.alt || '') + '@' + (fund.von != null ? fund.von : '?'));
}

/* Ein neues Dokument faengt ohne Ausnahmen an — sonst truege man die
   Nachsicht aus einem Text in den naechsten. */
document.addEventListener('dokument:gewechselt', () => {
  einmalRuhig = new Set();
  ganzRuhig = new Set();
});

function wortErsetzen(stelle, ersatz) {
  const bereich = document.createRange();
  bereich.setStart(stelle.knoten, stelle.von);
  bereich.setEnd(stelle.knoten, stelle.bis);
  feld.focus();
  Dokument.waehle(bereich);
  document.execCommand('insertText', false, ersatz);
  geaendertMelden();
}

/* Die Wortliste ist durchgehend kleingeschrieben — sie weiß von Hauptwörtern
   nichts. Für einen Teil davon braucht sie es auch nicht: Diese Endungen sind
   im Deutschen ausnahmslos Hauptwörter. Das ist keine Schätzung, sondern
   Wortbildung — es gibt kein Eigenschaftswort auf -ung, -keit oder -schaft.

   Die Mindestlänge muss sein: „jung" endet auf -ung und ist keines. Ab sieben
   Buchstaben bleibt von den kurzen Ausreißern nichts übrig.

   Das deckt Qualität, Berechnung, Zahlung, Bestätigung ab — nicht Bescheid,
   Unterlagen, Widerspruch. Dafür bräuchte es eine Hauptwortliste, die es hier
   nicht gibt. Bei denen bleibt es beim Muster des Ersetzten, und das trifft
   meistens: Wer „Kwalität" schreibt, hat den großen Buchstaben schon. */
const HAUPTWORT_ENDE =
  /(ung|ungen|heit|heiten|keit|keiten|schaft|schaften|tion|tionen|tät|täten|nis|nisse|tum|ismus|ment|mente)$/;

const istHauptwort = (wort) => wort.length >= 7 && HAUPTWORT_ENDE.test(wort);

/* „hallo" statt „Hallo" wäre am Satzanfang wieder falsch. Also übernimmt der
   Vorschlag die Schreibweise des Wortes, das er ersetzt. */
function wieGeschrieben(alt, neu) {
  if (!alt || !neu) return neu;
  if (alt === alt.toUpperCase() && alt.length > 1) return neu.toUpperCase();
  if (alt[0] === alt[0].toUpperCase()) return neu[0].toUpperCase() + neu.slice(1);
  if (neu[0] === neu[0].toUpperCase()) return neu;      // bringt sie schon mit
  if (istHauptwort(neu)) return neu[0].toUpperCase() + neu.slice(1);
  return neu;
}

function fundAnStelle(ziel) {
  const marke = ziel && ziel.closest ? ziel.closest('span.fundmarke') : null;
  if (!marke) return null;
  const nummer = parseInt(marke.dataset.fund, 10);
  return Number.isNaN(nummer) ? null : funde[nummer] || null;
}

/* Steht die Schreibstelle da, wo geklickt wurde?
 *
 * Die Befehle des Menüs arbeiten mit der Schreibstelle, nicht mit dem
 * Mauszeiger: „Zeile darüber" fragt, in welcher Zelle der Zeiger steht.
 * Wer in eine andere Zelle rechtsklickt, meint aber die, auf die er
 * zeigt. Also wird der Zeiger dorthin gesetzt — es sei denn, es ist
 * etwas markiert und man hat in die Markierung geklickt: Dann will man
 * mit der Markierung etwas tun und nicht sie verlieren.
 */
function zeigerZumKlick(e) {
  const auswahl = window.getSelection();
  if (auswahl && auswahl.rangeCount && !auswahl.isCollapsed) {
    const r = auswahl.getRangeAt(0);
    for (const kasten of r.getClientRects()) {
      if (e.clientX >= kasten.left && e.clientX <= kasten.right
          && e.clientY >= kasten.top && e.clientY <= kasten.bottom) return;
    }
  }
  let bereich = null;
  if (document.caretRangeFromPoint) {
    bereich = document.caretRangeFromPoint(e.clientX, e.clientY);
  } else if (document.caretPositionFromPoint) {
    const stelle = document.caretPositionFromPoint(e.clientX, e.clientY);
    if (stelle) {
      bereich = document.createRange();
      bereich.setStart(stelle.offsetNode, stelle.offset);
      bereich.collapse(true);
    }
  }
  if (bereich && feld.contains(bereich.startContainer)) Dokument.waehle(bereich);
}

/* ------------------------------------------------------------
   Die schwebende Formatleiste

   Sie geht mit dem Menü zusammen auf und steht darüber. Darin: Schrift,
   Größe, größer, kleiner, Zeilenabstand — und darunter fett, kursiv,
   unterstrichen, hervorheben, Schriftfarbe, Ausrichtung, Pinsel.

   Warum überhaupt eine Leiste und nicht Menüzeilen? Weil das die Sachen
   sind, die man beim Schreiben zehnmal in der Minute anfasst. Als Zeilen
   in einer Liste müsste man sie jedes Mal lesen; als Fläche zielt man
   hin. Der WPS Writer macht das so, und es ist die bessere Lösung.

   Die Auswahlfelder brauchen einen Umweg: Wer ein Klappfeld anklickt,
   nimmt dem Blatt die Schreibstelle. Deshalb wird sie beim Aufgehen
   gemerkt und vor dem Anwenden zurückgeholt — derselbe Weg, den auch die
   Schriftliste im Band geht.
   ------------------------------------------------------------ */
function rechtsLeisteBauen(gesperrt) {
  const leiste = document.createElement('div');
  leiste.className = 'minileiste';

  const reihe = () => {
    const r = document.createElement('div');
    r.className = 'minileiste__reihe';
    leiste.appendChild(r);
    return r;
  };

  const zeichen = (r, name, titel, tun, klasse) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'minileiste__knopf' + (klasse ? ' ' + klasse : '')
                + (gesperrt ? ' minileiste__knopf--aus' : '');
    k.title = titel;
    k.setAttribute('aria-label', titel);
    if (SYMBOLE[name]) k.appendChild(symbol(name));
    else k.appendChild(document.createTextNode(name));
    if (gesperrt) { k.disabled = true; r.appendChild(k); return k; }
    /* Kein Fokuswechsel: So bleibt die Markierung im Blatt stehen. */
    k.addEventListener('mousedown', (ev) => ev.preventDefault());
    k.addEventListener('click', () => {
      tun();
      /* Und gleich neu merken, was jetzt markiert ist. Ohne das griff der
         nächste Griff ins Leere: Wer erst „fett" drückt und dann die Größe
         wählt, hätte die Markierung von VOR dem Fettmachen zurückgeholt —
         und die zeigt auf Textknoten, die es nach dem Umbauen nicht mehr
         gibt. Beim Prüfen aufgefallen. */
      auswahlMerken();
    });
    r.appendChild(k);
    return k;
  };

  const klappfeld = (r, eintraege, jetzt, titel, tun, breit) => {
    const w = document.createElement('select');
    w.className = 'minileiste__wahl' + (breit ? ' minileiste__wahl--breit' : '');
    w.title = titel;
    w.setAttribute('aria-label', titel);
    for (const [wert, name] of eintraege) {
      const o = document.createElement('option');
      o.value = String(wert);
      o.textContent = String(name);
      w.appendChild(o);
    }
    if (jetzt !== undefined && jetzt !== null) w.value = String(jetzt);
    w.disabled = gesperrt;
    /* Vor dem Aufklappen merken, nicht vorher: „mousedown" kommt, bevor
       das Klappfeld den Fokus nimmt — in diesem Augenblick steht die
       Markierung noch im Blatt. */
    w.addEventListener('mousedown', auswahlMerken);
    w.addEventListener('change', () => { auswahlZurueck(); tun(w.value); auswahlMerken(); });
    r.appendChild(w);
    return w;
  };

  /* Erste Reihe: alles, was mit der Größe der Schrift zu tun hat. */
  const oben = reihe();
  klappfeld(oben, (alleSchriften && alleSchriften.length ? alleSchriften : SCHRIFTEN)
                    .map((s) => [s, s]),
            schriftJetzt, 'Schriftart', (name) => { schriftJetzt = name; schriftart(name); }, true);
  klappfeld(oben, GROESSEN.map((g) => [g, g]), 12, 'Schriftgröße', (g) => schriftgroesse(+g));
  zeichen(oben, 'groesserA', 'Schrift vergrößern', B.schriftGroesser);
  zeichen(oben, 'kleinerA', 'Schrift verkleinern', B.schriftKleiner);
  klappfeld(oben, [['1.15', '1,0'], ['1.6', '1,5'], ['2.1', '2,0']],
            null, 'Zeilenabstand', (wert) => zeilenabstand(wert)());

  /* Zweite Reihe: wie der Text aussieht. */
  const unten = reihe();
  zeichen(unten, 'F', 'Fett (Strg+B)', B.fett, 'minileiste__knopf--fett');
  zeichen(unten, 'K', 'Kursiv (Strg+I)', B.kursiv, 'minileiste__knopf--kursiv');
  zeichen(unten, 'U', 'Unterstrichen (Strg+U)', B.unter, 'minileiste__knopf--unter');
  zeichen(unten, 'marker', 'Hervorheben', B.hervorheben);
  zeichen(unten, 'farbe', 'Schriftfarbe', B.schriftfarbe);
  const teiler = document.createElement('span');
  teiler.className = 'minileiste__teiler';
  unten.appendChild(teiler);
  zeichen(unten, 'links', 'Linksbündig', B.links);
  zeichen(unten, 'mitte', 'Zentriert', B.mitte);
  zeichen(unten, 'rechts', 'Rechtsbündig', B.rechts);
  zeichen(unten, 'block', 'Blocksatz', B.block);
  zeichen(unten, 'pinsel', 'Format übertragen', B.formatUebertragen);

  return leiste;
}

/* ------------------------------------------------------------
   Das Menü unter der rechten Maustaste

   Es stand einmal auf vier Zeilen: Ausschneiden, Kopieren, Einfügen,
   Rechtschreibung. Das ist zu wenig — die rechte Maustaste ist für die
   meisten der kürzeste Weg zu einem Befehl. Der zweite Anlauf war dann
   zu viel: zwanzig Zeilen untereinander. Eine lange Liste ist nicht mehr
   Hilfe als eine kurze, sondern weniger — man muss sie lesen, statt sie
   zu sehen.

   Jetzt sind es zwei Kästen, wie im WPS Writer:

       DIE FORMATLEISTE schwebt darüber (rechtsLeisteBauen). Sie trägt,
       was man beim Schreiben ständig anfasst.

       DAS MENÜ ist eine kurze Liste. Links das Bild, rechts die
       Tastenkombination — beides hilft dem, der den Punkt beim zweiten
       Mal wiederfinden will, ohne zu lesen.

   Und es zeigt nur, was hier etwas bewirkt: auf einem Link anderes als
   in einer Tabelle, in einer Tabelle anderes als in einem Bild. Was
   selten gebraucht wird, steht in einem Untermenü; was gar nicht geht,
   steht grau da statt zu fehlen — ein Punkt, der mal da ist und mal
   nicht, lässt sich nicht lernen.

   Was hier NICHT steht, steht in den Leisten: Wörter zählen, Vorlesen,
   Alles auswählen, Texteffekte. Die rechte Maustaste ist für das, was
   man an dieser Stelle tut — nicht für alles, was das Programm kann.
   ------------------------------------------------------------ */
/* Ein Objekt aus dem Text nehmen — und den Absatz gleich mit, wenn er
   nur dafuer da war. Sonst bleibt eine leere Zeile stehen, die niemand
   sieht und alle wundert. */
function objektLoeschen(el, wie) {
  if (!el || !el.isConnected) return;
  const absatz = el.closest('p');
  el.remove();
  if (absatz && !absatz.textContent.trim() && !absatz.querySelector('img, svg, table')) {
    absatz.remove();
  }
  /* Griffe weg, wenn das Geloeschte das gewaehlte war. */
  if (typeof bildGewaehlt !== 'undefined' && bildGewaehlt === el) {
    bildGewaehlt = null;
    bildGriffeAuffrischen();
  }
  geaendertMelden();
  melde(wie + ' gelöscht.');
}

function rechtsMenueZeigen(e) {
  e.preventDefault();
  rechtsMenueSchliessen();
  zeigerZumKlick(e);
  /* Für die Klappfelder der Leiste: Sie nehmen dem Blatt beim Anklicken
     die Schreibstelle, und ohne sie wüsste der Befehl nicht, worauf er
     sich bezieht. */
  auswahlMerken();

  const kasten = document.createElement('div');
  kasten.className = 'rechtsmenue';

  /* ---- Bausteine ---- */

  const knopfBauen = (p) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rechtsmenue__punkt' + (p.klasse ? ' ' + p.klasse : '')
                + (p.aus ? ' rechtsmenue__punkt--aus' : '');

    /* Links das Bild — und wo keins ist, bleibt der Platz frei, damit
       alle Beschriftungen auf einer Linie stehen. */
    const bildchen = document.createElement('span');
    bildchen.className = 'rechtsmenue__bild';
    if (p.zeichen && SYMBOLE[p.zeichen]) bildchen.appendChild(symbol(p.zeichen));
    k.appendChild(bildchen);

    const wort = document.createElement('span');
    wort.className = 'rechtsmenue__wort';
    wort.textContent = p.name;
    k.appendChild(wort);

    /* Rechts die Tastenkombination — wer sie zweimal gelesen hat, braucht
       das Menü beim dritten Mal nicht mehr. */
    if (p.taste) {
      const taste = document.createElement('span');
      taste.className = 'rechtsmenue__taste';
      taste.textContent = p.taste;
      k.appendChild(taste);
    }

    if (p.aus) { k.disabled = true; return k; }
    /* Ohne dies nähme der Klick dem Blatt die Schreibstelle — und der
       Befehl wüsste nicht mehr, worauf er sich bezieht. */
    k.addEventListener('mousedown', (ev) => ev.preventDefault());
    k.addEventListener('click', () => { rechtsMenueSchliessen(); p.tun(); });
    return k;
  };

  const eintrag = (p) => { const k = knopfBauen(p); kasten.appendChild(k); return k; };

  const kopfzeileSetzen = (text) => {
    const kopf = document.createElement('div');
    kopf.className = 'rechtsmenue__kopf';
    kopf.textContent = text;
    kasten.appendChild(kopf);
  };

  /* Eine Trennlinie, die nur kommt, wenn darüber wirklich etwas steht.
     Sonst begänne das Menü an mancher Stelle mit einem Strich, und an
     anderer stünden zwei übereinander. */
  const trennlinie = () => {
    if (!kasten.lastElementChild
        || kasten.lastElementChild.classList.contains('rechtsmenue__strich')) return;
    const s = document.createElement('div');
    s.className = 'rechtsmenue__strich';
    kasten.appendChild(s);
  };

  /* Ein Untermenü. Es klappt zur Seite auf — nach rechts, wenn dort
     Platz ist, sonst nach links. Gemessen wird erst, wenn es sichtbar
     ist; vorher hat es keine Breite. */
  const gruppe = (zeichen, name, punkte) => {
    const huelle = document.createElement('div');
    huelle.className = 'rechtsmenue__gruppe';

    const kopf = knopfBauen({ zeichen: zeichen, name: name, tun: () => {} });
    kopf.classList.add('rechtsmenue__punkt--auf');
    const pfeil = document.createElement('span');
    pfeil.className = 'rechtsmenue__pfeil';
    pfeil.textContent = '›';
    kopf.appendChild(pfeil);
    huelle.appendChild(kopf);

    const klappe = document.createElement('div');
    klappe.className = 'rechtsmenue__klappe';
    for (const p of punkte) {
      if (p === strich) {
        const s = document.createElement('div');
        s.className = 'rechtsmenue__strich';
        klappe.appendChild(s);
        continue;
      }
      klappe.appendChild(knopfBauen(p));
    }
    huelle.appendChild(klappe);

    huelle.addEventListener('mouseenter', () => {
      for (const andere of kasten.querySelectorAll('.rechtsmenue__gruppe--offen')) {
        andere.classList.remove('rechtsmenue__gruppe--offen');
      }
      huelle.classList.add('rechtsmenue__gruppe--offen');
      klappe.classList.remove('rechtsmenue__klappe--links');
      if (klappe.getBoundingClientRect().right > window.innerWidth - 6) {
        klappe.classList.add('rechtsmenue__klappe--links');
      }
    });
    huelle.addEventListener('mouseleave', () => huelle.classList.remove('rechtsmenue__gruppe--offen'));

    kasten.appendChild(huelle);
  };

  /* ---- Wo ist geklickt worden? ---- */

  const ziel = e.target && e.target.closest ? e.target : null;
  const link = ziel ? ziel.closest('a[href]') : null;
  const zelle = ziel ? ziel.closest('td, th') : null;
  const bild = ziel ? ziel.closest('img') : null;
  const form = ziel ? ziel.closest('svg.zeichnung') : null;
  const diagramm = ziel ? ziel.closest('svg.diagramm') : null;
  const smartart = ziel ? ziel.closest('svg.smartart') : null;
  const formel = ziel ? ziel.closest('math') : null;

  const auswahl = window.getSelection();
  const markiert = !!(auswahl && auswahl.rangeCount && !auswahl.isCollapsed
                      && auswahl.toString().length);
  const gesperrt = feld.contentEditable === 'false';

  /* ---- 1. Das Wort, auf das gezeigt wurde ---- */

  const stelle = wortAnPunkt(e.clientX, e.clientY);

  /* Zeigt der Zeiger auf ein angestrichenes Wort, hatte das Menue den
     Punkt zweimal: einmal aus dem Wort unter dem Zeiger, einmal aus der
     Marke darunter — zwei gleiche Ueberschriften, zwei gleiche
     Vorschlaege, fuenf Aktionen statt drei. Hier wird gemerkt, ob das
     Wort schon oben stand; der Block darunter haelt dann still. */
  let wortGezeigt = null;

  /* Was der Prüfer selbst zu diesem Wort sagt.
   *
   * Hier stand vorher nur die Klangliste („vorschlaegeFuer"), und die ist
   * blind: Auf „garnicht" bot sie „gereinigt, krankt, kränkt" an. Der
   * Prüfer weiß es besser — er kennt die Regel und antwortet „gar nicht".
   * Er wird deshalb zuerst gefragt, und zwar nur nach diesem einen Wort;
   * das ist schnell genug, um es bei jedem Rechtsklick zu tun.
   *
   * Und es gilt auch für Wörter, die IM Wörterbuch stehen: „wiederspiegelt"
   * ist ein richtiges Wort und trotzdem falsch. Vorher kam dafür gar
   * nichts, solange nicht vorher geprüft worden war.
   */
  const kurz = !stelle || stelle.wort.length < 4;
  let rat = null;
  if (!kurz) {
    try {
      rat = (Pruefung.findeProbleme(stelle.wort) || [])
        .find((f) => f.neu && f.alt === stelle.wort && f.art !== 'hinweis') || null;
    } catch (fehler) { rat = null; }
  }

  /* Kurze Wörter nicht: „A" in einer Tabellenzelle steht in keinem
     Wörterbuch, ist aber kein Fehler. Die Tippfehlerprüfung fängt aus
     demselben Grund erst bei vier Buchstaben an (pruefung.js) — und wenn
     die Seitenleiste ein Wort nicht anstreicht, darf das Menü unter der
     rechten Taste es nicht als unbekannt melden. */
  const unbekannt = !kurz && !Pruefung.kennt(stelle.wort);

  /* Die Klangliste nur, wenn der Prüfer nichts weiß. Weiß er es —
     „garnicht" → „gar nicht" —, wären sechs Wörter daneben, die zufällig
     ähnlich klingen, kein Angebot, sondern Lärm; man muss dann erst
     wieder suchen, welches gemeint ist. Und wenn sie kommt, dann kurz:
     Wer unter fünf Vorschlägen nicht fündig wird, wird es unter zehn
     auch nicht. */
  const vorschlaege = (unbekannt && !rat)
    ? Pruefung.vorschlaegeFuer(stelle.wort).slice(0, 5) : [];

  if (rat || unbekannt) {
    kopfzeileSetzen(rat ? (rat.grund || 'Schreibweise')
      : vorschlaege.length
        ? '„' + stelle.wort + '" steht nicht im Wörterbuch'
        : '„' + stelle.wort + '" steht nicht im Wörterbuch — kein Vorschlag gefunden');

    /* Der Rat des Prüfers steht oben und fett — er ist der Grund, weshalb
       jemand die rechte Taste gedrückt hat. Die Groß- und Kleinschreibung
       bringt er schon mit; sie noch einmal anzupassen machte aus „gar
       nicht" womöglich „Gar Nicht". */
    if (rat) {
      eintrag({ name: rat.neu, klasse: 'rechtsmenue__punkt--vorschlag', tun: () => {
        wortErsetzen(stelle, rat.neu);
        KI.Gedaechtnis.merkeAenderung({ wortEbene: true, alt: stelle.wort, neu: rat.neu });
        melde('„' + stelle.wort + '" zu „' + rat.neu + '" geändert.');
      } });
    }

    for (const wort of vorschlaege) {
      const ersatz = wieGeschrieben(stelle.wort, wort);
      eintrag({ name: ersatz, klasse: 'rechtsmenue__punkt--vorschlag', tun: () => {
        wortErsetzen(stelle, ersatz);
        /* Was hier von Hand gewählt wird, soll das Programm sich merken —
           beim nächsten Mal steht es dann gleich oben. */
        KI.Gedaechtnis.merkeAenderung({ wortEbene: true, alt: stelle.wort, neu: ersatz });
        melde('„' + stelle.wort + '" zu „' + ersatz + '" geändert.');
      } });
    }

    /* ============================================================
       DER UNTERE TEIL DES MENUES

       Aus seiner Beschreibung: „Aktions- und Einstellungsbereich
       (unterer Bereich): Ignorieren / Einmal ignorieren — ueberspringt
       die aktuelle Markierung. Alle ignorieren — entfernt die rote
       Unterstreichung fuer dieses Wort im gesamten Dokument. Zum
       Woerterbuch hinzufuegen — nimmt das Wort in das
       Benutzerwoerterbuch auf."

       Es gab nur den letzten Punkt, und er hiess anders. Die beiden
       anderen fehlten — und sie sind die haeufigeren: Ein Eigenname
       gehoert ins Woerterbuch, ein Tippfehler in einem Zitat nicht.
       ============================================================ */
    eintrag({ zeichen: 'haken', name: 'Einmal ignorieren', tun: () => {
      einmalIgnorieren(stelle);
      melde('Diese Stelle bleibt stehen.');
    } });

    eintrag({ zeichen: 'haken', name: 'Alle ignorieren', tun: () => {
      alleIgnorieren(stelle.wort);
      melde('„' + stelle.wort + '" wird in diesem Dokument nicht mehr angestrichen.');
    } });

    /* Nur bei einem Wort, das WIRKLICH keiner kennt. Bei „wiederspiegelt"
       wäre der Punkt falsch: Das Wort ist bekannt, nur an dieser Stelle
       das verkehrte. */
    if (unbekannt) {
      eintrag({ zeichen: 'duden', name: 'Zum Wörterbuch hinzufügen', tun: () => {
        const g = KI.Gedaechtnis.lies();
        g.inRuhe[stelle.wort.toLowerCase()] = true;
        KI.Gedaechtnis.schreib(g);
        melde('„' + stelle.wort + '" steht jetzt im Wörterbuch.');
        if (funde.length) pruefen();
      } });
    }
    wortGezeigt = String(stelle.wort || '').toLowerCase();
    trennlinie();
  }

  /* ---- 2. Die angestrichene Stelle ---- */
  const fund = fundAnStelle(e.target);
  const doppelt = !!(fund && wortGezeigt
                     && String(fund.alt || '').toLowerCase() === wortGezeigt);

  if (fund && !doppelt) {
    kopfzeileSetzen(fund.grund || 'Gefundene Stelle');

    if (fund.art !== 'hinweis' && fund.neu) {
      eintrag({ name: fund.neu, klasse: 'rechtsmenue__punkt--vorschlag',
                tun: () => uebernimm(fund) });
    }

    if (fund.alt && /^[A-Za-zÄÖÜäöüß-]+$/.test(fund.alt)) {
      eintrag({ zeichen: 'haken', name: 'Wort in Ruhe lassen', tun: () => {
        /* §9: Der Weg führt durch die Brücke. Sie schreibt ins Gedächtnis
           und weiß zugleich, dass das Geprüfte damit nicht mehr stimmt. */
        if (Bruecke) {
          Bruecke.benutzerwortHinzufuegen(fund.alt);
        } else {
          const g = KI.Gedaechtnis.lies();
          g.inRuhe[fund.alt.toLowerCase()] = true;
          KI.Gedaechtnis.schreib(g);
        }
        melde('„' + fund.alt + '" wird künftig nicht mehr angestrichen.');
        pruefen();
      } });
    }

    eintrag({ name: 'Übergehen', tun: () => {
      /* Auch der Brücke sagen — sonst steht der Fund beim nächsten Prüfen
         wieder da, und man übergeht ihn zum dritten Mal. */
      if (Bruecke) Bruecke.wegwinkenFund(fund);
      funde = funde.filter((f) => f !== fund);
      zeichneFunde();
      markiereFunde();
      meldeFunde(Dokument.lies().text.length);
    } });
    trennlinie();
  }

  /* ---- 3. Der Hyperlink ---- */
  if (link) {
    const wohin = link.getAttribute('href') || '';
    kopfzeileSetzen(wohin.length > 52 ? wohin.slice(0, 49) + '…' : wohin);
    eintrag({ zeichen: 'kette', name: 'Hyperlink bearbeiten…',
              tun: () => B.linkBearbeiten(link), aus: gesperrt });
    eintrag({ zeichen: 'kopie', name: 'Adresse kopieren', tun: () => B.linkKopieren(link) });
    eintrag({ zeichen: 'radierer', name: 'Hyperlink entfernen',
              tun: () => B.linkEntfernen(link), aus: gesperrt });
    trennlinie();
  }

  /* ---- 4. Bild, Zeichnung, Diagramm, SmartArt, Formel ----
     Dieselben Befehle, die auch der Reiter im Zusammenhang anbietet. Sie
     hier ein zweites Mal zu schreiben wäre falsch; sie werden gerufen. */
  if (bild) {
    eintrag({ zeichen: 'anordnen', name: 'Anordnen und Umbruch…',
              tun: () => B.anordnen(), aus: gesperrt });
    trennlinie();
  } else if (form) {
    gruppe('stift', 'Zeichnung', [
      { name: 'Form ändern…', tun: () => B.formAendern(), aus: gesperrt },
      { name: 'Füllung…', tun: () => B.formFuellung(), aus: gesperrt },
      { name: 'Kontur…', tun: () => B.formKontur(), aus: gesperrt },
      { name: 'Größe…', tun: () => B.formGroesse(), aus: gesperrt },
      { name: 'Anordnen…', tun: () => B.anordnen(), aus: gesperrt },
    ]);
    eintrag({ zeichen: 'radierer', name: 'Form löschen',
              tun: () => objektLoeschen(form, 'Form'), aus: gesperrt });
    trennlinie();
  } else if (diagramm) {
    gruppe('saeule', 'Diagramm', [
      { name: 'Daten bearbeiten…', tun: () => B.diagrammDaten(), aus: gesperrt },
      { name: 'Diagrammtyp…', tun: () => B.diagrammTyp(), aus: gesperrt },
      { name: 'Entwurf…', tun: () => B.diagrammEntwurf(), aus: gesperrt },
      { name: 'Format…', tun: () => B.diagrammFormat(), aus: gesperrt },
    ]);
    /* „mit Rechtsklick laesst sich das Diagramm nicht bei Bedarf
       entfernen." Stimmte: vier Punkte zum Aendern, keiner zum
       Wegnehmen. Was man einfuegen kann, muss man auch loeschen
       koennen — und zwar dort, wo man es anfasst. */
    eintrag({ zeichen: 'radierer', name: 'Diagramm löschen',
              tun: () => objektLoeschen(diagramm, 'Diagramm'), aus: gesperrt });
    trennlinie();
  } else if (smartart) {
    gruppe('smartart', 'SmartArt', [
      { name: 'Entwurf…', tun: () => B.smartartEntwurf(), aus: gesperrt },
      { name: 'Format…', tun: () => B.smartartFormat(), aus: gesperrt },
    ]);
    eintrag({ zeichen: 'radierer', name: 'SmartArt löschen',
              tun: () => objektLoeschen(smartart, 'SmartArt'), aus: gesperrt });
    trennlinie();
  } else if (formel) {
    eintrag({ zeichen: 'formel', name: 'Formel ändern…',
              tun: () => B.formelAendern(), aus: gesperrt });
    trennlinie();
  }

  /* ---- 5. Die Tabelle ----
     „Einfügen" und „Löschen" heißen hier „Zellen einfügen" und „Zellen
     löschen": Zwei Zeilen weiter unten steht das Einfügen aus der
     Zwischenablage, und zwei Punkte gleichen Namens in einem Menü sind
     eine Falle. */
  if (zelle) {
    gruppe('tabelle', 'Zellen einfügen', [
      { name: 'Zeile darüber', tun: () => B.zeileOben(), aus: gesperrt },
      { name: 'Zeile darunter', tun: () => B.zeileUnten(), aus: gesperrt },
      { name: 'Spalte links', tun: () => B.spalteLinks(), aus: gesperrt },
      { name: 'Spalte rechts', tun: () => B.spalteRechts(), aus: gesperrt },
    ]);
    gruppe('radierer', 'Zellen löschen', [
      { name: 'Zeile', tun: () => B.zeileWeg(), aus: gesperrt },
      { name: 'Spalte', tun: () => B.spalteWeg(), aus: gesperrt },
      strich,
      { name: 'Ganze Tabelle', tun: () => B.tabelleWeg(), aus: gesperrt },
    ]);
    gruppe('rahmen', 'Tabelle', [
      { name: 'Erste Zeile als Kopf', tun: () => B.kopfzeileTabelle(), aus: gesperrt },
      { name: 'Zellengröße…', tun: () => B.zellengroesse(), aus: gesperrt },
      { name: 'Ausrichtung…', tun: () => B.zellenAusrichtung(), aus: gesperrt },
      { name: 'Zellen zusammenführen', tun: () => B.zellenVerbinden(), aus: gesperrt },
      { name: 'Zellen teilen…', tun: () => B.zellenTeilen(), aus: gesperrt },
      { name: 'Wieder in den Text einreihen', tun: () => B.tabelleEinreihen(), aus: gesperrt },
      { name: 'Tabelle nach oben', tun: () => B.tabelleHoch(), aus: gesperrt },
      { name: 'Tabelle nach unten', tun: () => B.tabelleRunter(), aus: gesperrt },
      { name: 'Rahmen ein/aus', tun: () => B.tabelleRahmen(), aus: gesperrt },
      { name: 'Eigenschaften der Tabelle…', tun: () => B.tabelleEigenschaften(), aus: gesperrt },
      strich,
      { name: 'Sortieren…', tun: () => B.sortieren(), aus: gesperrt },
    ]);
    trennlinie();
  }

  /* ---- 6. Die Zwischenablage ---- */
  eintrag({ zeichen: 'kopie', name: 'Kopieren', taste: 'Strg+C',
            tun: B.kopieren, aus: !markiert });
  eintrag({ zeichen: 'schere', name: 'Ausschneiden', taste: 'Strg+X',
            tun: B.ausschneiden, aus: !markiert || gesperrt });
  eintrag({ zeichen: 'kleben', name: 'Einfügen', taste: 'Strg+V',
            tun: B.einfuegen, aus: gesperrt });
  eintrag({ zeichen: 'ohneformat', name: 'Einfügen ohne Formatierung',
            tun: B.einfuegenOhne, aus: gesperrt });
  trennlinie();

  /* ---- 7. Absatz, Listen, Vorlagen ---- */
  if (markiert) {
    eintrag({ zeichen: 'unterart', name: 'Groß-/Kleinschreibung…',
              tun: B.schreibweise, aus: gesperrt });
  }
  gruppe('abstand', 'Absatz', [
    { name: 'Absatz…', tun: () => B.absatz('masse'), aus: gesperrt },
    { name: 'Einzug vergrößern', tun: B.einzugMehr, aus: gesperrt },
    { name: 'Einzug verringern', tun: B.einzugWeniger, aus: gesperrt },
    strich,
    { name: 'Rahmen…', tun: B.absatzRahmen, aus: gesperrt },
    { name: 'Schattierung…', tun: B.absatzSchattierung, aus: gesperrt },
  ]);
  gruppe('punkte', 'Aufzählung und Nummerierung', [
    { name: 'Aufzählung', tun: B.punkte, aus: gesperrt },
    { name: 'Nummerierung', tun: B.zahlen, aus: gesperrt },
    strich,
    { name: 'Listenebene erhöhen', tun: B.ebeneHoeher, aus: gesperrt },
    { name: 'Listenebene verringern', tun: B.ebeneTiefer, aus: gesperrt },
  ]);
  /* Die Formatvorlagen kommen aus dem Katalog — derselben Liste, die auch
     der Katalog im Band zeigt. Zwei Listen liefen auseinander. */
  gruppe('inhalt', 'Formatvorlage', KATALOG.map(([name, , tun]) => (
    { name: name, tun: tun, aus: gesperrt })));
  trennlinie();

  /* ---- 8. Was man an dieser Stelle einfügt ----
     Auf einem Link stünde „Hyperlink…" daneben und machte einen zweiten
     daraus — dort steht oben schon „bearbeiten". */
  if (!link) {
    eintrag({ zeichen: 'kette', name: 'Hyperlink…', taste: 'Strg+K',
              tun: B.hyperlink, aus: gesperrt });
  }
  eintrag({ zeichen: 'notiz', name: 'Kommentar einfügen', tun: B.kommentar, aus: gesperrt });
  trennlinie();

  /* ---- 9. Sprache ----
     Der Thesaurus nur, wenn überhaupt ein Wort dasteht — sonst hat er
     nichts nachzuschlagen. */
  if (stelle || markiert) {
    eintrag({ zeichen: 'thesaurus', name: 'Thesaurus', tun: B.thesaurus });
  }
  eintrag({ zeichen: 'wellen', name: 'Rechtschreibung und Grammatik', taste: 'F7',
            tun: B.rechtschreibpruefung });

  /* ---- Hinstellen ----
     Erst einhängen, dann messen: Wie hoch das Menü ist, hängt daran, wie
     viel an dieser Stelle zu bieten war — und das steht erst jetzt fest.
     Vorher stand hier eine feste Zahl (260 Bildpunkte), und das längere
     Menü ragte unten aus dem Fenster heraus. */
  const leiste = rechtsLeisteBauen(gesperrt);
  leiste.style.left = '0px';
  leiste.style.top = '0px';
  document.body.appendChild(leiste);
  rechtsLeiste = leiste;

  kasten.style.left = '0px';
  kasten.style.top = '0px';
  document.body.appendChild(kasten);
  rechtsMenue = kasten;

  const rand = 6;
  const lMasse = leiste.getBoundingClientRect();
  const mMasse = kasten.getBoundingClientRect();
  const breite = Math.max(lMasse.width, mMasse.width);

  let x = e.clientX;
  if (x + breite > window.innerWidth - rand) x = Math.max(rand, window.innerWidth - rand - breite);

  /* Die Leiste steht über dem Menü und beide zusammen sollen ins Fenster
     passen. Ist unten kein Platz, rutscht das Gespann hinauf; ist auch
     dann keiner, bekommt das Menü eine Rolle. */
  const zusammen = lMasse.height + 4 + mMasse.height;
  let oben = e.clientY;
  if (oben + zusammen > window.innerHeight - rand) {
    oben = Math.max(rand, window.innerHeight - rand - zusammen);
  }

  leiste.style.left = x + 'px';
  leiste.style.top = oben + 'px';
  kasten.style.left = x + 'px';
  kasten.style.top = (oben + lMasse.height + 4) + 'px';

  if (zusammen > window.innerHeight - 2 * rand) {
    leiste.style.top = rand + 'px';
    kasten.style.top = (rand + lMasse.height + 4) + 'px';
    kasten.style.maxHeight = (window.innerHeight - 2 * rand - lMasse.height - 4) + 'px';
    kasten.style.overflowY = 'auto';
  }

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(ev) {
      if (kasten.contains(ev.target) || leiste.contains(ev.target)) return;
      rechtsMenueSchliessen();
      document.removeEventListener('mousedown', zu);
    });
  }, 0);
}

function meldeFunde(zeichenZahl) {
  const zahl = funde.length;
  const wort = zahl === 1 ? '1 Fund' : zahl + ' Funde';
  $('status-pruefung').textContent = zeichenZahl + ' Zeichen geprüft, ' + wort + '.';
  $('status-pruefung').classList.toggle('statuszeile__fund', zahl > 0);
}

/* ============================================================
   Die lebende Prüfung

   Bisher gab es rote Wellenlinien nur vom System — der eigenen Prüfung
   sah man beim Schreiben nichts an, sie sprach erst auf Knopfdruck. Der
   Entwurf verlangt es umgekehrt: Lunivos eigene Funde sollen die
   Wellenlinien sein (§7, §8).

   WARUM DAS NICHT TRIVIAL IST

   Die Markierung setzt <span> in den Text und zerteilt dabei Textknoten.
   Wer das tut, während jemand schreibt, verschiebt ihm die Schreibstelle
   mitten im Wort. Deshalb wird die Stelle vorher als ZEICHENZAHL gemerkt
   und hinterher daraus zurückgerechnet — ein geklonter Bereich überlebt
   die Zerteilung nicht.

   Und es wird nicht bei jedem Anschlag geprüft, sondern erst, wenn eine
   Weile nichts kam. Bei dreihundert Wörtern ist eine Prüfung nicht zu
   spüren, bei dreißigtausend schon.
   ============================================================ */

let lebendUhr = null;
let lebendLaeuft = false;
const LEBEND_WARTEN = 900;      // Millisekunden Ruhe, bevor geprüft wird

/* Die Schreibstelle als Zeichenzahl im Text.

   Der Zeiger hängt nicht immer in einem Textknoten. Steht er am Ende
   eines Absatzes oder in einem leeren, ist der Anker der Absatz selbst,
   und die Zahl daneben zählt Kindknoten, nicht Zeichen. Wer das nicht
   auflöst, findet in der Karte nichts, gibt null zurück — und dann setzt
   die Markierung den Zeiger irgendwohin. Genau das war zu sehen: Nach
   dem Prüfen stand er wieder hinter „Da". */
function zeigerStelle() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount) return null;
  let knoten = auswahl.anchorNode;
  let versatz = auswahl.anchorOffset;
  if (!knoten || !feld.contains(knoten)) return null;

  /* Vom Element zum Textknoten hinabsteigen. */
  if (knoten.nodeType === Node.ELEMENT_NODE) {
    const kinder = knoten.childNodes;
    if (versatz > 0 && kinder[versatz - 1]) {
      /* Hinter das Ende des Knotens davor. */
      const vorher = kinder[versatz - 1];
      const letzter = letzterTextknoten(vorher);
      if (letzter) { knoten = letzter; versatz = letzter.data.length; }
    } else if (kinder[versatz]) {
      const erster = ersterTextknoten(kinder[versatz]);
      if (erster) { knoten = erster; versatz = 0; }
    }
  }
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE) return null;

  const { karte } = Dokument.lies();
  for (const e of karte) {
    if (e.knoten === knoten) return e.von + Math.min(versatz, knoten.data.length);
  }
  return null;
}

function ersterTextknoten(knoten) {
  if (knoten.nodeType === Node.TEXT_NODE) return knoten;
  const gehe = document.createTreeWalker(knoten, NodeFilter.SHOW_TEXT);
  return gehe.nextNode();
}

function letzterTextknoten(knoten) {
  if (knoten.nodeType === Node.TEXT_NODE) return knoten;
  const gehe = document.createTreeWalker(knoten, NodeFilter.SHOW_TEXT);
  let letzter = null, jetzt;
  while ((jetzt = gehe.nextNode())) letzter = jetzt;
  return letzter;
}

function zeigerSetzen(stelle) {
  if (stelle === null) return;
  try {
    const { karte } = Dokument.lies();
    Dokument.waehle(Dokument.bereich(karte, stelle, stelle));
  } catch (e) { /* Steht der Text nicht mehr so da, bleibt der Zeiger, wo er ist. */ }
}

function lebendAnstossen() {
  if (!Bruecke || !lebendAn) return;
  clearTimeout(lebendUhr);
  lebendUhr = setTimeout(lebendPruefen, LEBEND_WARTEN);
}

function lebendPruefen() {
  if (!Bruecke || !lebendAn || pruefungLaeuft || lebendLaeuft) return;
  /* Während ein Fenster offen steht, wird nichts im Text verschoben. */
  if (document.querySelector('.dialoggrund')) return;

  lebendLaeuft = true;
  try {
    const text = Dokument.lies().text;
    const stelle = zeigerStelle();
    funde = Bruecke.pruefen(text);
    zeichneFunde();
    markiereFunde(absatzAmZeiger());
    zeigerSetzen(stelle);
    meldeFunde(text.length);
  } finally {
    lebendLaeuft = false;
  }
}

function pruefen() {
  if (pruefungLaeuft) return;
  pruefungLaeuft = true;
  const text = Dokument.lies().text;
  KIteil.vorschlaegeLeeren();
  markenEntfernen();
  funde = Bruecke ? Bruecke.pruefen(text) : Pruefung.findeProbleme(text);
  zeichneFunde(true);
  markiereFunde();
  meldeFunde(text.length);
  pruefungLaeuft = false;
}

/** Ein einzelner Fund — der Knopf „Ändern". */
function uebernimm(fund) {
  const text = Dokument.lies().text;
  if (text.slice(fund.von, fund.bis) !== fund.alt) {
    /* Der Text hat sich verschoben, seit geprüft wurde. Statt daneben zu
       greifen, lieber neu prüfen — dann stimmen alle Stellen wieder. */
    pruefen();
    return;
  }
  Dokument.ersetze(fund.von, fund.bis, fund.neu);
  /* Was hier gelernt wird, soll das Schließen des Fensters überleben —
     sonst fragt das Programm morgen wieder nach längst Geklärtem. */
  KI.Gedaechtnis.merkeAenderung(fund);
  /* §23: Der Brücke sagen, dass dieser Fehler erledigt ist. Nur den Text
     zu ändern ließe ihn in ihrem Stand als offen stehen. */
  if (Bruecke) {
    const dazu = Bruecke.offeneFehler().find((f) => f.fund === fund);
    if (dazu) Bruecke.korrekturAnwenden(dazu.id, fund.neu, Dokument.lies().text);
  }
  pruefen();
}

/** Alles Eindeutige auf einmal — von hinten nach vorn, sonst verrutscht es. */
function allesUebernehmen() {
  const eindeutig = funde.filter((f) => f.art === 'fehler' && f.alt && f.neu)
                         .sort((a, b) => b.von - a.von);
  if (!eindeutig.length) { melde('Nichts dabei, was eindeutig wäre.'); return; }
  for (const fund of eindeutig) {
    const text = Dokument.lies().text;
    if (text.slice(fund.von, fund.bis) !== fund.alt) continue;
    Dokument.ersetze(fund.von, fund.bis, fund.neu);
  }
  pruefen();
}

/* ============================================================
   Die KI: korrigieren, vorschlagen, uebersetzen

   Steht in js/kiteil.js. Fuenf Namen gehen hinein, sechs kommen heraus.
   ============================================================ */
const KIteil = KI_BAUEN(B, {
  melde:       (...a) => melde(...a),
  leereFunde:  (...a) => leereFunde(...a),
  kuerze:      (s)    => kuerze(s),
  menueBauen:  ()     => menueBauen(),
  /* Der einzige Schreibzugriff nach drinnen: Zeigt die KI Vorschlaege,
     muessen die Funde der Rechtschreibpruefung aus der Seitenleiste
     weichen — sie teilen sich denselben Platz. */
  fundeLeeren: ()     => { funde = []; },
  /* Welche Fassung des Textes gerade gilt. Die KI braucht sie, weil ihre
     Antwort spät kommt: Über Ollama dauert eine Anfrage bis zu zehn
     Minuten, und in zehn Minuten schreibt ein Mensch weiter. */
  fassung:     ()     => (Bruecke ? Bruecke.fassung : null),
});

/* ============================================================
   7. Statuszeile, Titel, Sicherheitsnetz
   ============================================================ */

function titelSetzen() {
  /* Bei mehreren Fenstern gehört die Nummer in den Titel. Zwei Fenster
     mit „Unbenannt 1 — Lunivo-Office" sind in der Fensterliste des
     Systems nicht auseinanderzuhalten — und genau dort sucht man sie. */
  const fensterNr = Dokumente.fenster();
  document.title = dateiname + (geaendert ? ' *' : '') + ' — Lunivo-Office'
                 + (fensterNr > 1 ? ' (Fenster ' + fensterNr + ')' : '');
  Speicher.schreib('dateiname', dateiname);
  /* Im Reiter steht derselbe Name und derselbe Punkt für „nicht
     gespeichert". Beides hier nachzuziehen ist der einzige Weg, der
     keine Stelle vergisst: Jede Umbenennung und jede erste Änderung
     kommt hier vorbei. */
  if (typeof dokumentleisteBauen === 'function') dokumentleisteBauen();
}

function zahlenAuffrischen() {
  /* Zuerst die Umbrueche: Ihre Hoehe geht in die Seitenzahl ein. */
  umbruecheAuffrischen();
  const { zeichen: z, woerter } = Dokument.zaehle();
  $('status-zahl').textContent = woerter + (woerter === 1 ? ' Wort, ' : ' Wörter, ')
                               + z + (z === 1 ? ' Zeichen' : ' Zeichen');
  /* Wie viele Seiten das sind. Hier stand einmal fest „29,7 cm minus 2 cm
     Rand" — das galt für A4 mit den Standardrändern und log auf allem
     anderen. Jetzt wird mit dem wirklichen Blatt gerechnet.

     Und mit zwei Bildpunkten Nachsicht: Ein Text, der eine Seite genau
     füllt, ist eine Seite. Ohne das machte ein einziger Punkt Rundung aus
     einem einseitigen Brief zwei — in der Statuszeile stand „Seite 1 von
     2", während nur ein Blatt da war. */
  const masse = PAPIERE[papier] || PAPIERE.a4;
  const hoeheMm = (quer ? masse.breite : masse.hoehe) - seitenrand.oben - seitenrand.unten;
  const proSeite = Math.max(1, hoeheMm * CM / 10);
  const seiten = Math.max(1, Math.ceil((feld.scrollHeight - 2) / proSeite));
  $('status-seiten').textContent = 'Seite 1 von ' + seiten;
}

let merkUhr = null;
function merkeText() {
  clearTimeout(merkUhr);
  merkUhr = setTimeout(() => Speicher.schreib('inhalt', ohneMarken(Dokument.inhalt())), 400);
}

function geaendertMelden() {
  if (!geaendert) { geaendert = true; titelSetzen(); }
  zahlenAuffrischen();
  merkeText();
  /* Der Brücke sagen, dass das Geprüfte nicht mehr zum Text passt. */
  if (Bruecke) Bruecke.textSetzen(Dokument.lies().text);
  /* Und nach einer Weile Ruhe von selbst nachsehen. */
  if (!lebendLaeuft) lebendAnstossen();
}

/* Nicht nur das vorderste: Wird das Fenster über das Kreuz des Systems
   zugemacht, gehen alle Reiter darin mit. */
window.addEventListener('beforeunload', (e) => {
  const offen = geaendert
    || Dokumente.liste().some((nr) => nr !== Dokumente.aktiv() && geaendertJe[nr]);
  if (!offen) return;
  e.preventDefault();
  e.returnValue = '';
});

/* ============================================================
   8. Tastenkürzel
   ============================================================ */

const KUERZEL = {
  n: B.neu, o: B.oeffnen, s: B.speichern, p: B.drucken,
  h: () => sucheZeigen(true), f: () => sucheZeigen(true),
  0: B.normal, '+': B.groesser, '-': B.kleiner,
};

document.addEventListener('keydown', (e) => {
  /* Die zwei Kuerzel aus seinem Bild der Einfuegen-Klappe. Sie stehen
     dort neben den Punkten, also muessen sie auch wirken — ein Kuerzel,
     das nur dasteht, ist eine Behauptung. */
  if ((e.ctrlKey || e.metaKey) && e.altKey && !e.shiftKey) {
    const t = e.key.toLowerCase();
    if (t === 't') { e.preventDefault(); B.einfuegenOhne(); return; }
    if (t === 'v') { e.preventDefault(); B.inhalteEinfuegen(); return; }
  }
  /* Strg+Tab und Strg+Umschalt+Tab wechseln den Reiter — wie überall.
     Das muss vor dem Tab weiter unten stehen, das die Lücken der
     Bausteine anspringt: Sonst käme man aus einem Gerüst nie heraus. */
  if (e.key === 'Tab' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    dokumentWechseln(Dokumente.weiter(e.shiftKey ? -1 : 1));
    return;
  }
  /* Strg+W schließt den Reiter, Strg+F4 auch — die eine Taste kommt von
     den Browsern, die andere von Word. */
  if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'w')
      || ((e.ctrlKey || e.metaKey) && e.key === 'F4')) {
    e.preventDefault(); dokumentSchliessen(); return;
  }
  if (e.key === 'F4') { e.preventDefault(); B.vorlesen(); return; }
  /* F2: die Lesehilfe. Sie hatte als einzige der großen Hilfen keine
     Taste — F4 liest vor, F5 öffnet die Seitenleiste, F7 prüft.

     Erst stand sie auf F6. Das war ein Fehler: F6 hatte „Welche Hilfe
     wann" schon, und weil dieser Zuhörer weiter oben steht, war der
     andere damit tot — ohne dass es jemandem aufgefallen wäre. F2 ist
     frei. */
  if (e.key === 'F2') { e.preventDefault(); B.lesehilfe(); return; }
  if (e.key === 'F7') { e.preventDefault(); pruefen(); return; }
  /* Kürzel tippen, F3 drücken — wie in LibreOffice. Findet sich kein
     Baustein zu dem Wort, passiert nichts; F3 ist sonst nicht belegt. */
  if (e.key === 'F3' && !document.querySelector('.dialoggrund')) {
    e.preventDefault(); Bausteine.bausteinUeberKuerzel(); return;
  }
  /* Tab springt von Lücke zu Lücke — aber nur, solange welche da sind.
     Sind keine mehr offen, gehört Tab wieder dem Einzug. */
  if (e.key === 'Tab' && !e.ctrlKey && !e.altKey
      && !document.querySelector('.dialoggrund')
      && feld.contains(document.activeElement === feld ? feld : document.activeElement)
      && feld.querySelector('.platzhalter')) {
    if (Bausteine.platzhalterWeiter(e.shiftKey)) { e.preventDefault(); return; }
  }
  /* Strg und eine Ziffer nimmt einen Vorschlag der Wortvorhersage — so
     bleibt die Hand auf der Tastatur. */
  if ((e.ctrlKey || e.metaKey) && vorhersageKasten && /^[1-6]$/.test(e.key)) {
    const knopf = vorhersageKasten.querySelectorAll('.vorhersage__wort')[+e.key - 1];
    if (knopf) { e.preventDefault(); knopf.click(); return; }
  }
  /* Strg+1 und Strg+2 setzen den Zeilenabstand — so steht es auf seinem
     WPS-Bild. Sie stehen HINTER der Wortvorhersage: Ist deren Kasten
     offen, nimmt sie den Vorschlag, wie bisher. Sonst waere ein eigener
     Befehl fuer einen fremden verschwunden. */
  if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && !vorhersageKasten
      && (e.key === '1' || e.key === '2')) {
    e.preventDefault();
    zeilenabstandSetzen(e.key === '1' ? 1 : 2, e.key === '1' ? '1,0' : '2,0');
    return;
  }
  if (e.key === 'Escape' && vorhersageKasten) { vorhersageWeg(); return; }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 's') {
    e.preventDefault(); B.speichernUnter(); return;
  }
  if (e.key === 'F8') { e.preventDefault(); KIteil.kiKorrigieren(); return; }
  if (e.key === 'F9') { e.preventDefault(); Einstellungen.oeffnen(); return; }
  if (e.key === 'F5') { e.preventDefault(); B.tafelZeigen(); return; }
  /* Zuerst die Fenster, die über allem liegen: Wer sie nicht mehr
     zubekommt, kommt an gar nichts mehr heran. Ein Rückfrage-Kasten liegt
     noch darüber und bringt seinen eigenen Ausgang mit — solange einer
     offen steht, ist er gemeint und nicht das Fenster darunter. */
  if (e.key === 'Escape' && !document.querySelector('.dialoggrund')) {
    if (Vorlagen.offen()) { Vorlagen.schliessen(); return; }
    if (!$('druckfenster').hidden) { Druck.druckFensterSchliessen(); return; }
    if (Druck.vorschauOffen()) { Druck.vorschauSchliessen(); return; }
  }
  if (e.key === 'Escape' && lesemodus) { B.lesemodus(); return; }
  if (e.key === 'Escape' && Einstellungen.offen()) { Einstellungen.schliessen(); return; }
  if (e.key === 'F6') { e.preventDefault(); B.welcheHilfe(); return; }
  if (e.key === 'Escape' && !$('suchleiste').hidden) { sucheZeigen(false); return; }
  if (!(e.ctrlKey || e.metaKey) || e.altKey) return;

  if (e.key === 'Enter') { e.preventDefault(); B.seitenumbruch(); return; }
  const tun = KUERZEL[e.key.toLowerCase()];
  if (tun) { e.preventDefault(); tun(); }
});

/* ============================================================
   9. Der Griff zwischen Fläche und Tafel
   ============================================================ */

(() => {
  const griff = $('griff');
  const tafel = $('tafel');
  const breite = Speicher.lies('tafelbreite', 360);
  tafel.style.flexBasis = breite + 'px';

  let zieht = false;
  griff.addEventListener('mousedown', (e) => { zieht = true; e.preventDefault(); });
  window.addEventListener('mousemove', (e) => {
    if (!zieht) return;
    const neu = Math.max(250, Math.min(640, window.innerWidth - e.clientX));
    tafel.style.flexBasis = neu + 'px';
    /* Die Arbeitsfläche wird dabei schmaler, und das Blatt rutscht — also
       muss das Lineal mit. Die Größenbeobachtung allein hat das nicht
       zuverlässig gemeldet; hier weiß das Programm es ohnehin. */
    linealAuffrischen();
  });
  window.addEventListener('mouseup', () => {
    if (!zieht) return;
    zieht = false;
    Speicher.schreib('tafelbreite', parseInt(tafel.style.flexBasis, 10) || 360);
  });
})();

/* ============================================================
   10. Anschalten
   ============================================================ */

/* Die Wortvorhersage folgt dem Tippen — mit kurzer Verzögerung, sonst
   flackert der Kasten bei jedem Anschlag. */
feld.addEventListener('input', () => {
  clearTimeout(vorhersageUhr);
  vorhersageUhr = setTimeout(vorhersageZeigen, 180);
});
/* Ein Klick in eine Lücke nimmt sie ganz. Sonst stünde der Zeiger mitten in
   «Abonnement o.ä.», und das Tippen schöbe sich zwischen die Buchstaben —
   man müsste erst löschen, was einem eigentlich helfen sollte. */
feld.addEventListener('click', (e) => {
  const platz = e.target.closest && e.target.closest('.platzhalter');
  if (platz && feld.contains(platz)) setTimeout(() => Bausteine.platzhalterNehmen(platz), 0);
});

feld.addEventListener('blur', () => setTimeout(vorhersageWeg, 200));
document.addEventListener('selectionchange', () => { if (vorhersageKasten) vorhersageWeg(); });

feld.addEventListener('contextmenu', rechtsMenueZeigen);
feld.addEventListener('beforeinput', verfolgenAbfangen);
feld.addEventListener('input', geaendertMelden);
/* Die AutoKorrektur greift, wenn ein Wort abgeschlossen ist — nicht
   mitten hinein. */
feld.addEventListener('keyup', (e) => {
  if (e.key === ' ') autoListeLaufen();
  if (e.key === ' ' || e.key === 'Enter' || '.,;:!?"\''.includes(e.key)) autokorrekturLaufen();
});
document.addEventListener('dokument:geaendert', geaendertMelden);
document.addEventListener('selectionchange', werkzeugeAuffrischen);
/* Die Einzugsmarken zeigen den Absatz, in dem der Zeiger steht — also
   müssen sie ihm folgen. */
document.addEventListener('selectionchange', linealAuffrischen);
/* Der Zeilenfokus folgt dem Zeiger — und dem Blatt, wenn es sich bewegt. */
document.addEventListener('selectionchange', fokusAuffrischen);
feld.addEventListener('input', fokusAuffrischen);
$('arbeitsflaeche').addEventListener('scroll', fokusAuffrischen);
window.addEventListener('resize', fokusAuffrischen);
window.addEventListener('resize', linealAuffrischen);
$('arbeitsflaeche').addEventListener('scroll', linealAuffrischen);
/* Der Pinsel wartet auf die nächste Markierung. Beim Loslassen der Maus
   steht fest, was sie umfasst — vorher wäre es ein halber Satz. */
feld.addEventListener('mouseup', () => setTimeout(pinselAnwenden, 0));

$('btn-pruefen').addEventListener('click', () => pruefen());
$('suche-weiter').addEventListener('click', sucheWeiter);
$('suche-zu').addEventListener('click', () => sucheZeigen(false));
$('suche-ersetze').addEventListener('click', () => {
  const stelle = suche(Math.max(0, sucheAb - $('suche-was').value.length));
  if (stelle === -1) { $('suche-meldung').textContent = 'Nicht gefunden.'; return; }
  Dokument.ersetze(stelle, stelle + $('suche-was').value.length, $('suche-womit').value);
  sucheAb = stelle + $('suche-womit').value.length;
});
$('suche-alle').addEventListener('click', () => {
  const was = $('suche-was').value;
  if (!was) return;
  let zahl = 0;
  for (let schutz = 0; schutz < 500; schutz++) {
    const text = Dokument.lies().text;
    const stelle = text.toLowerCase().indexOf(was.toLowerCase());
    if (stelle === -1) break;
    Dokument.ersetze(stelle, stelle + was.length, $('suche-womit').value);
    zahl++;
    if ($('suche-womit').value.toLowerCase().includes(was.toLowerCase())) break;  // sonst endlos
  }
  $('suche-meldung').textContent = zahl + (zahl === 1 ? ' Stelle ersetzt.' : ' Stellen ersetzt.');
});
$('zettel').addEventListener('change', () => {
  /* Der Zettel steht im Speicher der KI-Ebene: Sie liest ihn bei jeder
     Anfrage, und zwei Kopien desselben Satzes gingen irgendwann auseinander. */
  KI.Speicher.schreib('zettel', $('zettel').value.slice(0, KI.ZETTEL_GRENZE));
});

$('btn-ki').addEventListener('click', () => KIteil.kiKorrigieren());
$('btn-vorschlaege').addEventListener('click', () => KIteil.kiVorschlaege());
$('btn-uebersetzen').addEventListener('click', () => KIteil.kiUebersetzen());

/* Die Einstellungsseite verstellt Schriftgröße, Helligkeit und die vier
   Ecken nicht selbst — sie ruft die Griffe hier. Sonst gäbe es zwei Stellen,
   die dasselbe tun, und irgendwann widersprächen sie sich. */
Einstellungen.verbinde({
  zoom: () => zoom,
  zoomSetzen: setzeZoom,
  thema: () => thema,
  themaWeiter: () => setzeThema(THEMEN[(THEMEN.indexOf(thema) + 1) % THEMEN.length])(),
  /* „marken" und „wellen" standen hier einmal einzeln. Sie sind jetzt zwei
     von zehn Schaltern und stehen weiter unten in einer Liste — einzeln
     verdrahtet wären es zwanzig fast gleiche Zeilen, und die elfte
     vergisst man. */
  neuZeichnen: () => KIteil.kiKnoepfeAuffrischen(),

  /* Die Optionenseite füllt jetzt auch Listen, die das Programm führt. Sie
     hier zu reichen ist richtiger, als sie ein zweites Mal zu schreiben:
     Zwei Listen derselben Sache laufen irgendwann auseinander. */
  /* „alleSchriften" trägt die des Rechners, sobald sie da sind — SCHRIFTEN
     ist nur die kurze Startliste, mit der das Fenster aufgeht. In den
     Optionen stünden sonst zehn statt neunhundert. */
  /* Die Gruppenliste des Menübands, jetzt auch auf der Optionenseite.
     Sie greift auf dieselbe Ordnung wie das Anpassen-Fenster — zwei
     Listen derselben Sache liefen irgendwann auseinander. */
  /* Die Lesehilfe, jetzt auch von der Optionenseite aus.

     Sie war nur über ihren Dialog zu erreichen — und ein Dialog legt sich
     über den Text, an dem man gerade beurteilen will, ob die Einstellung
     etwas taugt. Auf der Seite wirkt jede Wahl sofort auf dem Blatt. */
  lesehilfeWerte: () => ({
    ton:      PAPIERTOENE.map(([m, n]) => [m, n]),
    zeichen:  ABSTUFUNG.map(([m, n]) => [m, n]),
    wort:     ABSTUFUNG.map(([m, n]) => [m, n]),
    zeilen:   ABSTUFUNG.map(([m, n]) => [m, n]),
    groesser: VERGROESSERN.map(([m, n]) => [m, n]),
    zurueck:  ZURUECKNEHMEN.map(([m, n]) => [m, n]),
  }),
  lesehilfeStand: () => Object.assign({}, lesehilfe),
  lesehilfeSetzen: (feld, wert) => {
    lesehilfe[feld] = wert;
    lesehilfeAnwenden();
    Speicher.schreib('lesehilfe', lesehilfe);
  },
  /* Die fertig gerechneten Werte für das Probeblatt der Einstellungsseite.

     Die Formeln (0,03em je Stufe, 1,55 + 0,22 je Stufe …) stehen in
     lesehilfeAnwenden() und sollen an genau einer Stelle stehen. Gäbe ich
     die Marken heraus und rechnete die Einstellungsseite selbst, wäre es
     eine zweite Abschrift — und beim nächsten Verstellen einer Zahl
     stimmte die Probe nicht mehr mit dem Blatt überein. */
  leseprobeWerte: () => {
    const stufe = (marke) => (ABSTUFUNG.find(([m]) => m === marke) || ABSTUFUNG[0])[2];
    const ton = PAPIERTOENE.find(([m]) => m === lesehilfe.ton);
    return {
      ton: (ton && ton[2]) || '',
      zeichen: stufe(lesehilfe.zeichen) ? (stufe(lesehilfe.zeichen) * 0.03) + 'em' : 'normal',
      wort: stufe(lesehilfe.wort) ? (stufe(lesehilfe.wort) * 0.12) + 'em' : 'normal',
      zeilen: stufe(lesehilfe.zeilen)
        ? (1.55 + stufe(lesehilfe.zeilen) * 0.22).toFixed(2) : '1.55',
      wachstum: String((VERGROESSERN.find(([m]) => m === lesehilfe.groesser)
                        || VERGROESSERN[0])[2]),
      blaesse: String((ZURUECKNEHMEN.find(([m]) => m === lesehilfe.zurueck)
                       || ZURUECKNEHMEN[0])[2]),
      schrift: schriftJetzt,
    };
  },
  lesestufen: () => LESESTUFEN.map(([marke, name]) => [marke, name]),
  lesestufeJetzt: () => lesestufeJetzt(),
  lesestufeSetzen: (marke) => lesestufeSetzen(marke),
  stimmeWaehlen: () => B.stimmeWaehlen(),

  bandReiter: () => REGISTER.map(([name]) => name),
  tastenHilfe: () => B.tastenHilfe(),

  /* Die Befehlsliste links in beiden Fenstern. „Häufig verwendete" ist die
     kurze Auswahl, die WPS voreinstellt; „Alle Befehle" holt alles aus dem
     Band zusammen, und die dritte Sorte zeigt eine einzelne Registerkarte.

     Gelesen wird aus REGISTER selbst — eine zweite Liste danebenzustellen
     hieße, sie beim nächsten neuen Knopf zu vergessen. */
  befehle: (quelle) => {
    const haeufigNamen = ['Neu', 'Öffnen', 'Speichern', 'Speichern unter',
      'Als PDF exportieren', 'Drucken', 'Druckvorschau', 'Rückgängig',
      'Wiederholen', 'Einfügen', 'Kopieren', 'Ausschneiden', 'Fett', 'Kursiv',
      'Unterstrichen', 'Format übertragen', 'Suchen', 'Ersetzen', 'Prüfen',
      'Zentriert', 'Linksbündig', 'Schrift vergrößern', 'Schriftfarbe',
      'Tabelle einfügen', 'Bild', 'Hyperlink', 'Kopfzeile', 'Fußzeile',
      'Seitenzahl', 'Sonderzeichen', 'Optionen'];
    if (quelle === 'Häufig verwendete Befehle' || !quelle) {
      return haeufigNamen.map((n) => ({ name: n, symbol: symbolZuBefehl(n) }));
    }

    /* Aus einem Reiter alle Knopfnamen holen. Ein Eintrag ist
       [symbol, name, tun, …]; Untermenüs stehen als Liste an dritter
       Stelle und werden mit aufgenommen. */
    /* Name UND Symbol: In der Liste steht bei WPS vor jedem Befehl seine
       Zeichnung. Ein Befehl ohne Bild ist in einer Liste von hundert kaum
       wiederzufinden — das Auge sucht die Form, nicht das Wort. */
    const ausReiter = (reiter) => {
      const raus = [];
      const gefunden = REGISTER.find(([n]) => n === reiter);
      if (!gefunden) return raus;
      for (const gruppe of gefunden[1]) {
        const eintraege = Array.isArray(gruppe[1]) ? gruppe[1] : [];
        for (const e of eintraege) {
          if (!Array.isArray(e)) continue;
          if (typeof e[1] === 'string') raus.push({ name: e[1], symbol: e[0] });
          /* Untermenüs: Sie tragen kein eigenes Symbol, deshalb das des
             Knopfes, unter dem sie hängen. */
          if (Array.isArray(e[2])) {
            for (const u of e[2]) {
              if (Array.isArray(u) && typeof u[0] === 'string') {
                raus.push({ name: u[0], symbol: e[0] });
              }
            }
          }
        }
      }
      return raus;
    };

    if (quelle.startsWith('Registerkarte: ')) return ausReiter(quelle.slice(15));

    const alle = [];
    for (const [name] of REGISTER) alle.push(...ausReiter(name));
    /* Doppelte heraus: „Suchen" steht in Start und in Überprüfen. */
    const gesehen = new Set();
    const einmalig = alle.filter((e) => {
      if (gesehen.has(e.name)) return false;
      gesehen.add(e.name); return true;
    });
    return einmalig.sort((a, b) => a.name.localeCompare(b.name, 'de'));
  },

  /* Das Symbol zu einem Befehlsnamen — für die Listen, die nur den Namen
     kennen (die Leiste für den Schnellzugriff etwa). */
  symbolZu: (name) => symbolZuBefehl(name),
  /* Den Pfad zu einer Symbolkennung — das Zeichnen selbst macht die
     Optionenseite, sie bekommt hier nur die Linien. */
  symbolLinien: (kennung) => symbolPfad(kennung),

  /* „Neue Registerkarte", „Neue Gruppe", „Umbenennen" — die drei Knöpfe
     unter dem Baum. Sie fragen nach dem Namen und legen ihn ab; das Band
     baut sich danach neu. */
  bandNeueKarte: () => {
    const name = window.prompt('Name der neuen Registerkarte:', 'Neue Registerkarte');
    if (!name) return;
    if (REGISTER.some(([n]) => n === name)) { melde('Diesen Reiter gibt es schon.'); return; }
    REGISTER.push([name, []]);
    eigeneRegisterSichern();
    registerBauen();
  },
  bandNeueGruppe: (reiter) => {
    const name = window.prompt('Name der neuen Gruppe:', 'Neue Gruppe');
    if (!name) return;
    const gefunden = REGISTER.find(([n]) => n === reiter);
    if (!gefunden) return;
    if (gefunden[1].some((g) => g[0] === name)) { melde('Diese Gruppe gibt es schon.'); return; }
    gefunden[1].push([name, []]);
    eigeneRegisterSichern();
    registerBauen();
  },
  bandUmbenennen: (reiter, gruppe) => {
    const alt = gruppe || reiter;
    const name = window.prompt('Neuer Name:', alt);
    if (!name || name === alt) return;
    if (gruppe) {
      const gefunden = REGISTER.find(([n]) => n === reiter);
      const treffer = gefunden && gefunden[1].find((g) => g[0] === gruppe);
      if (treffer) treffer[0] = name;
      /* Die gespeicherte Ordnung kennt den alten Namen — mitziehen, sonst
         steht die Gruppe nachher zweimal da. */
      const ordnung = registerOrdnung[reiter];
      if (Array.isArray(ordnung)) {
        const e = ordnung.find((x) => x && x.name === gruppe);
        if (e) e.name = name;
      }
    } else {
      const gefunden = REGISTER.find(([n]) => n === reiter);
      if (gefunden) gefunden[0] = name;
      if (registerOrdnung[reiter]) {
        registerOrdnung[name] = registerOrdnung[reiter];
        delete registerOrdnung[reiter];
      }
      if (registerOffen === reiter) registerOffen = name;
    }
    Speicher.schreib('registerOrdnung', registerOrdnung);
    eigeneRegisterSichern();
    registerBauen();
  },

  /* Einen Befehl in eine Gruppe legen. */
  bandBefehlDazu: (reiter, gruppe, befehl) => {
    if (!gruppe) { melde('Erst eine Gruppe im Baum rechts wählen.'); return; }
    const gefunden = REGISTER.find(([n]) => n === reiter);
    const treffer = gefunden && gefunden[1].find((g) => g[0] === gruppe);
    if (!treffer || !Array.isArray(treffer[1])) { melde('In diese Gruppe geht das nicht.'); return; }
    if (treffer[1].some((e) => Array.isArray(e) && e[1] === befehl)) {
      melde('Dieser Befehl steht dort schon.'); return;
    }
    /* Den Befehl im Band suchen und mitsamt seinem Symbol übernehmen —
       ein Knopf ohne Bild sieht aus, als wäre er nicht fertig. */
    let vorlage = null;
    for (const [, gruppen] of REGISTER) {
      for (const g of gruppen) {
        const liste = Array.isArray(g[1]) ? g[1] : [];
        const e = liste.find((x) => Array.isArray(x) && x[1] === befehl);
        if (e) { vorlage = e; break; }
      }
      if (vorlage) break;
    }
    treffer[1].push(vorlage ? vorlage.slice() : ['punkt', befehl, () => melde(befehl)]);
    eigeneRegisterSichern();
    registerBauen();
  },

  bandGruppen: (reiter) => registerListeFuer(reiter),
  bandGruppeZeigen: (reiter, name, an) => {
    const liste = registerListeFuer(reiter);
    const treffer = liste.find((e) => e.name === name);
    if (treffer) treffer.an = an;
    registerOrdnung[reiter] = liste.map(({ name: n, an: a }) => ({ name: n, an: a }));
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
  },
  bandGruppeSchieben: (reiter, name, wohin) => {
    const liste = registerListeFuer(reiter);
    const i = liste.findIndex((e) => e.name === name);
    const ziel = i + wohin;
    if (i < 0 || ziel < 0 || ziel >= liste.length) return;
    [liste[ziel], liste[i]] = [liste[i], liste[ziel]];
    registerOrdnung[reiter] = liste.map(({ name: n, an: a }) => ({ name: n, an: a }));
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
  },
  bandZuruecksetzen: (reiter) => {
    if (reiter) delete registerOrdnung[reiter];
    else registerOrdnung = {};
    Speicher.schreib('registerOrdnung', registerOrdnung);
    registerBauen();
  },

  /* Die Symbolleiste für den Schnellzugriff. */
  szAlle: () => SZ_ANGEBOT.filter((n) => !szLeiste.includes(n)),
  szDrin: () => szLeiste.slice(),
  szDazu: (name) => { if (!szLeiste.includes(name)) { szLeiste.push(name); szSichern(); } },
  szWeg:  (name) => { szLeiste = szLeiste.filter((n) => n !== name); szSichern(); },
  szSchieben: (name, wohin) => {
    const i = szLeiste.indexOf(name), ziel = i + wohin;
    if (i < 0 || ziel < 0 || ziel >= szLeiste.length) return;
    [szLeiste[ziel], szLeiste[i]] = [szLeiste[i], szLeiste[ziel]];
    szSichern();
  },
  szZurueck: () => { szLeiste = SZ_STANDARD.slice(); szSichern(); },

  /* Das Dokumentkennwort. */
  kennwortGesetzt: () => window.Kennwort.gesetzt(),
  kennwortSetzen: (kennwort, hinweis) => window.Kennwort.setzen(kennwort, hinweis),

  schriften: () => (alleSchriften && alleSchriften.length ? alleSchriften : SCHRIFTEN),
  /* Die drei, die fürs Lesen gemacht sind — und ob sie auf diesem Rechner
     überhaupt liegen. Die Schriftkiste im Band stellt sie längst nach oben;
     die Optionenseite tat es nicht, und dort ging OpenDyslexic zwischen
     neunhundert anderen unter. */
  leseschriften: () => LESESCHRIFTEN.filter((s) => alleSchriften.includes(s)),
  groessen: () => GROESSEN,
  pruefsprachen: () => SPRACHEN_PRUEFUNG,
  schriftJetzt: () => Speicher.lies('grundschrift', ''),
  groesseJetzt: () => Number(Speicher.lies('grundgroesse', 12)),
  grundschriftSetzen: (name, groesse) => grundschriftAnwenden(name, groesse),
  symbolgroessen: () => SYMBOLGROESSEN.map(([marke]) => marke),
  symbolgroesseJetzt: () => Speicher.lies('symbolgroesse', 'mittel'),
  skalierungJetzt: () => Number(Speicher.lies('skalierung', 100)) || 100,
  bedienungSetzen: (marke, skala) => {
    if (marke !== undefined) Speicher.schreib('symbolgroesse', marke);
    if (skala !== undefined) Speicher.schreib('skalierung', Number(skala) || 100);
    bedienungAnwenden();
  },
  /* Die Schalter der Optionenseite. Jeder sagt, wie es steht, und legt
     denselben Griff um, den auch das Menü und das Band benutzen — ein
     Schalter, drei Stellen, ein Zustand. Die Seite fasst nichts selbst an;
     sie wüsste auch gar nicht, was „Lineal an" bedeutet. */
  schalter: {
    lineal:        { an: () => lineal,          um: () => B.linealZeigen() },
    linealHoch:    { an: () => linealHoch,      um: () => B.linealHochZeigen() },
    /* Die Schalter aus der Tabelle kommen von selbst dazu — siehe
       weiter unten, wo das Objekt zusammengesetzt wird. */
    navigation:    { an: () => !$('navigation').hidden, um: () => B.navigation() },
    marken:        { an: () => marken,          um: () => B.markenZeigen() },
    netzlinien:    { an: () => netzlinien,      um: () => B.netzlinien() },
    steuerzeichen: { an: () => steuerzeichen,   um: () => B.steuerzeichenZeigen() },
    autokorrektur: { an: () => autokorrekturAn, um: () => B.autokorrektur() },
    vorhersage:    { an: () => vorhersageAn,    um: () => B.vorhersage() },
    verfolgen:     { an: () => verfolgenAn,     um: () => B.verfolgen() },
    markup:        { an: () => markupZeigen,    um: () => B.markupUmschalten() },
    wellen:        { an: () => lebendAn,        um: () => B.rechtschreibung() },
    /* Und die aus SCHALTER: Name für Name, mit demselben Zuschnitt aus
       „an" und „um". Von Hand geschrieben wären es hier sechzig Zeilen,
       die sich nur im Namen unterscheiden. */
    ...Object.fromEntries(Object.keys(SCHALTER).map((name) => [name, {
      an: () => schalterAn(name),
      um: () => schalterUmlegen(name),
    }])),
  },

  /* Das Format, mit dem „Speichern unter" aufgeht. Es gehört zum Dokument
     (Dokumente.EIGEN), nicht zum Programm — wer einen Word-Brief offen
     hat, soll ihn als Word behalten. */
  endungJetzt: () => Speicher.lies('endung', 'odt'),
  endungSetzen: (endung) => Speicher.schreib('endung', endung),

  registerAnpassen: () => B.registerAnpassen(),
  vorlagenOrdner: () => B.vorlagenOrdner(),
  vorlagenOrdnerWeg: () => '~/Vorlagen',

  flaecheJetzt: () => flaeche,
  flaecheSetzen: (wahl) => {
    flaeche = wahl === 'register' ? 'register' : 'leisten';
    Speicher.schreib('flaeche', flaeche);
    flaecheAnwenden();
    menueBauen();
  },
  pruefspracheJetzt: () => Speicher.lies('pruefsprache', 'de'),
  pruefspracheSetzen: (kennung) => {
    Speicher.schreib('pruefsprache', kennung);
    feld.lang = kennung;
    /* Eine andere Sprache heißt: Das Geprüfte gilt nicht mehr. */
    if (Bruecke) Bruecke.spracheSetzen(kennung);
    feld.blur(); feld.focus();
  },
});

/* Die Seite „Neu" kennt das Programm nicht. Sechs Griffe reichen ihr, was
   sie braucht — mehr ist die Verbindung nicht breit, und man sieht auf
   einen Blick, woran sie hängt. */
Vorlagen.verbinde({
  symbol,
  oeffneNr: (nr) => B.vorlageOeffnen(nr),
  leeresDokument: () => B.neu(),
  ordnerOeffnen: () => B.vorlagenOrdner(),
  behalten: () => B.vorlageBehalten(),
  zurueck: () => feld.focus(),
  oeffneMuster: (kennung) => B.musterOeffnen(kennung),
  benutzer: () => Speicher.lies('benutzer', {}) || {},
});

/* ============================================================
   Die Dokumentreiter

   Ein Fenster trägt mehrere Dokumente. Oben steht für jedes ein Reiter,
   und ein Klick darauf bringt es nach vorn.

   WIE DER WECHSEL FUNKTIONIERT

   Nicht, indem das Programm zwei Texte gleichzeitig im Fenster hält —
   das gäbe zwei Schreibfelder, und jede Stelle im Programm, die „das
   Dokument" sagt, müsste erst fragen, welches gemeint ist.

   Sondern über den Speicher. Alles, was ein Dokument ausmacht, steht dort
   ohnehin schon: der Text, die Kopfzeile, das Papier, die Abschnitte.
   dokumente.js gibt jedem Dokument seine eigene Ecke darin. Der Wechsel
   ist deshalb nur:

       1. was jetzt im Fenster steht, in die Ecke des alten schreiben
       2. die Ecke wechseln
       3. alles neu einlesen — genau wie beim Start des Programms

   Schritt 3 ist derselbe Ablauf, den auch der Programmstart nimmt. Er
   steht deshalb nur einmal da, als „dokumentZustandLaden".

   WAS DABEI NICHT MITGEHT

   Das Rückgängig des Browsers hängt am Schreibfeld, nicht am Text. Wer
   den Reiter wechselt, kann im anderen Dokument nicht mehr über den
   Wechsel hinaus zurückgehen. Der Text ist vollständig da — nur die
   Schrittfolge dorthin nicht. Anders ginge es nur mit einem eigenen
   Rückgängig, das jeden Tastendruck selbst mitschreibt; das wäre ein
   eigenes Stück Arbeit und keins, das man nebenbei richtig hinbekommt.
   ============================================================ */

/* Ob ein Dokument ungesicherte Änderungen hat. Für das vorderste sagt
   das „geaendert"; für die anderen muss es sich jemand merken, sonst
   ginge beim Beenden eine Warnung verloren. */
const geaendertJe = {};

/* Der Speicher schreibt den Text erst nach einer kurzen Ruhe (merkeText).
   Beim Reiterwechsel ist das genau falsch: Die Uhr liefe ab, NACHDEM der
   Speicher schon auf das neue Dokument zeigt — und schriebe den alten
   Text in das neue. Also vorher anhalten und sofort schreiben. */
function textJetztSichern() {
  clearTimeout(merkUhr);
  Speicher.schreib('inhalt', ohneMarken(Dokument.inhalt()));
}

/* Was im Fenster steht, in die Ecke des Dokuments schreiben, das gerade
   vorn liegt. */
function dokumentZustandSichern() {
  abschnittMerken(abschnittJetztNr);          /* schreibt auch die Abschnitte */
  textJetztSichern();
  Speicher.schreib('kopfinhalt', $('kopfzeile').innerHTML);
  Speicher.schreib('fussinhalt', $('fusszeile').innerHTML);
  Speicher.schreib('dateiname', dateiname);
  geaendertJe[Dokumente.aktiv()] = geaendert;
}

/* Der Aufbau gehört dem Dokument, nicht dem Fenster. Vor dem Einlesen
   muss er leer sein — „abschnitteHolen" legt nur Abschnitte an, es nimmt
   keine weg. Ohne diese Zeilen behielte ein Brief mit einem Abschnitt die
   drei des vorigen. */
function abschnitteLeeren() {
  if (!Aufbau) return;
  while (Aufbau.getSections().length > 1) {
    Aufbau.removeSection(Aufbau.getSections()[Aufbau.getSections().length - 1]);
  }
  const erster = Aufbau.getSection(0);
  if (!erster) return;
  Object.assign(erster.getPageSetup(), Dokumentmodell.PageSetup());
  Object.assign(erster.getPageNumbering(), Dokumentmodell.PageNumbering());
  erster.breakBefore = null;
  for (const zeile of [erster.header, erster.footer]) {
    zeile.sichtbar = false;
    zeile.html = '';
    zeile.linkedToPrevious = false;
  }
}

/* Alles einlesen und anwenden, was zum vordersten Dokument gehört. Das
   ist derselbe Ablauf wie beim Start — die Reihenfolge stammt von dort
   und ist nicht beliebig: erst die Schrift, dann der Text, dann die
   Seite, ganz zuletzt der Aufbau. */
function dokumentZustandLaden() {
  dateiname = Speicher.lies('dateiname', 'Unbenannt');

  /* Die Werte, die als eigene Variablen im Programm stehen. Sie werden
     beim Start aus dem Speicher gelesen; hier noch einmal, weil der
     Speicher jetzt woandershin zeigt. */
  spalten       = Speicher.lies('spalten', 1);
  layout        = Speicher.lies('layout', 'blatt');
  zeilennummern = Speicher.lies('zeilennummern', false);
  trennung      = Speicher.lies('trennung', false);
  seitenfarbe   = Speicher.lies('seitenfarbe', '');
  wasserzeichen = Speicher.lies('wasserzeichen', '');
  seitenrahmen  = Speicher.lies('seitenrahmen', '');
  markupZeigen  = Speicher.lies('markup', true);
  verfolgenAn   = Speicher.lies('verfolgen', false);
  design        = Speicher.lies('design', '');
  vorlagenStile = Object.assign({}, VORLAGEN_STANDARD, Speicher.lies('vorlagenstile', {}));

  grundschriftAnwenden();
  Dateien.stileSetzen(Speicher.lies('importstil', ''));
  Dokument.setzeInhalt(Speicher.lies('inhalt', '<p><br></p>'));
  $('kopfzeile').innerHTML = Speicher.lies('kopfinhalt', '');
  $('fusszeile').innerHTML = Speicher.lies('fussinhalt', '');

  layoutAnwenden();
  vorlagenAnwenden();
  if (design) designAnwenden(design);
  zeilennummernAnwenden();
  trennungAnwenden();
  seitenfarbeAnwenden();
  wasserzeichenAnwenden();
  seitenrahmenAnwenden();
  markupAnwenden();
  feld.classList.toggle('dokument--verfolgt', verfolgenAn);

  /* Papier, Ränder und die beiden Zeilen kommen aus dem Abschnitt, in dem
     der Zeiger steht — nicht aus dem Speicher. „abschnittAnwenden" setzt
     sie und ruft papierAnwenden, seiteAnwenden und kopfFussAnwenden. */
  abschnitteLeeren();
  abschnitteHolen();
  abschnittJetztNr = 0;
  abschnittAnwenden(0);

  /* Der Fehlerstand gehört zum Text. Ein Fund aus dem anderen Dokument
     zeigte auf eine Stelle, die es hier nicht gibt. */
  leereFunde('Noch nicht geprüft.');
  if (Bruecke) Bruecke.textSetzen(Dokument.lies().text);

  /* Erst ganz zuletzt, und das ist der Punkt: „Dokument.setzeInhalt"
     weiter oben schreibt in das Feld, und das Feld meldet jede Schreibung
     als Änderung. Wer den Reiter wechselt, hätte danach in JEDEM Dokument
     einen Stern und beim Schließen eine Rückfrage, die niemand verdient
     hat. Der Änderungsstand ist der gemerkte, nicht der eben ausgelöste. */
  geaendert = !!geaendertJe[Dokumente.aktiv()];

  setzeZoom(zoom);
  titelSetzen();
  zahlenAuffrischen();
  werkzeugeAuffrischen();
  registerSchalterAuffrischen();
  menueBauen();
}

/** Auf einen anderen Reiter. */
function dokumentWechseln(nr) {
  if (nr === Dokumente.aktiv()) { feld.focus(); return; }
  dokumentZustandSichern();
  if (!Dokumente.wechsle(nr)) return;
  dokumentZustandLaden();
  dokumentleisteBauen();
  feld.focus();
  melde('Dokument: ' + dateiname);
}

/** Ein neues, leeres Dokument in einem neuen Reiter. */
function dokumentNeu(wieHeisst) {
  dokumentZustandSichern();
  const nr = Dokumente.anlegen(wieHeisst);
  geaendertJe[nr] = false;
  dokumentZustandLaden();
  dokumentleisteBauen();
  feld.focus();
  return nr;
}

/* „Öffnen" soll keinen leeren Reiter hinterlassen. Steht im vordersten
   noch nichts und wurde nichts geändert, kommt die Datei dorthin; sonst
   bekommt sie einen eigenen. So macht es jedes Programm mit Reitern. */
function dokumentPlatzSchaffen() {
  const leer = !Dokument.lies().text.trim()
            && !$('kopfzeile').textContent.trim()
            && !$('fusszeile').textContent.trim();
  if (leer && !geaendert) return;
  dokumentNeu();
}

/**
 * Einen Reiter schließen. Beim letzten wird nicht geschlossen, sondern
 * geleert — ein Fenster ohne Blatt hätte nichts, worin man schreiben
 * könnte.
 */
function dokumentSchliessen(nr) {
  const ziel = nr === undefined ? Dokumente.aktiv() : nr;
  const seins = ziel === Dokumente.aktiv();
  const hatAenderung = seins ? geaendert : !!geaendertJe[ziel];

  const tun = () => {
    if (Dokumente.anzahl() < 2) {
      /* Der letzte: leeren statt schließen. */
      Dateien.stileSetzen('');
      Speicher.schreib('importstil', '');
      Speicher.schreib('inhalt', '<p><br></p>');
      Speicher.schreib('kopfinhalt', '<br>');
      Speicher.schreib('fussinhalt', '<br>');
      Speicher.schreib('abschnitte', null);
      Speicher.schreib('dateiname', 'Unbenannt 1');
      geaendertJe[ziel] = false;
      geaendert = false;
      dokumentZustandLaden();
      dokumentleisteBauen();
      feld.focus();
      melde('Dokument geschlossen.');
      return;
    }

    /* Wer einen anderen als den vordersten schließt, soll nicht plötzlich
       woanders stehen: Erst das Sichtbare sichern, dann wegräumen. */
    dokumentZustandSichern();
    const name = Dokumente.name(ziel);
    delete geaendertJe[ziel];
    const jetzt = Dokumente.entfernen(ziel);
    if (jetzt === null) return;
    if (seins) dokumentZustandLaden();
    dokumentleisteBauen();
    feld.focus();
    melde('Geschlossen: ' + name);
  };

  if (!hatAenderung) { tun(); return; }
  fenster('Nicht gespeichert', [
    { art: 'satz', text: '„' + Dokumente.name(ziel) + '" hat Änderungen, die in keiner '
                       + 'Datei stehen. Wer weitermacht, verliert sie.' },
  ], tun, 'Trotzdem schließen');
}

/* ------------------------------------------------------------
   Die Leiste zeichnen

   Sie wird neu gebaut, wenn sich etwas an ihr ändert — beim Wechsel, beim
   Anlegen, beim Schließen und immer, wenn der Titel sich ändert (dann
   kommt oder geht der Punkt für „nicht gespeichert").
   ------------------------------------------------------------ */
let ziehtNr = null;              /* welcher Reiter gerade gezogen wird */

function dokumentleisteBauen() {
  const leiste = $('dokumentleiste');
  if (!leiste) return;
  leiste.innerHTML = '';

  for (const nr of Dokumente.liste()) {
    const vorn = nr === Dokumente.aktiv();
    const offen = vorn ? geaendert : !!geaendertJe[nr];

    const reiter = document.createElement('div');
    reiter.className = 'dokumentreiter' + (vorn ? ' dokumentreiter--vorn' : '');
    reiter.setAttribute('role', 'tab');
    reiter.setAttribute('aria-selected', vorn ? 'true' : 'false');
    reiter.tabIndex = vorn ? 0 : -1;
    reiter.draggable = true;
    reiter.dataset.nr = String(nr);
    reiter.title = Dokumente.name(nr) + (offen ? ' — nicht gespeichert' : '');

    const name = document.createElement('span');
    name.className = 'dokumentreiter__name';
    name.textContent = Dokumente.name(nr);
    reiter.appendChild(name);

    /* Der Punkt und das Kreuz teilen sich denselben Platz — welches zu
       sehen ist, entscheidet das Stilblatt. */
    const punkt = document.createElement('span');
    punkt.className = 'dokumentreiter__punkt';
    punkt.textContent = offen ? '\u2022' : '';
    punkt.setAttribute('aria-hidden', 'true');
    reiter.appendChild(punkt);

    const zu = document.createElement('button');
    zu.className = 'dokumentreiter__zu';
    zu.type = 'button';
    zu.textContent = '\u00D7';
    zu.setAttribute('aria-label', Dokumente.name(nr) + ' schließen');
    zu.addEventListener('click', (e) => { e.stopPropagation(); dokumentSchliessen(nr); });
    reiter.appendChild(zu);

    reiter.addEventListener('click', () => dokumentWechseln(nr));
    /* Mit der mittleren Taste schließen — wie überall, wo es Reiter gibt. */
    reiter.addEventListener('auxclick', (e) => {
      if (e.button === 1) { e.preventDefault(); dokumentSchliessen(nr); }
    });
    reiter.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); dokumentWechseln(nr); }
    });

    /* Ziehen ordnet um. Die Nummern bleiben, was sie sind; nur die
       Reihenfolge der Liste ändert sich. */
    reiter.addEventListener('dragstart', (e) => {
      ziehtNr = nr;
      reiter.classList.add('dokumentreiter--zieht');
      try { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(nr)); }
      catch (fehler) { /* manche Umgebungen mögen das nicht */ }
    });
    reiter.addEventListener('dragend', () => { ziehtNr = null; dokumentleisteBauen(); });
    reiter.addEventListener('dragover', (e) => {
      if (ziehtNr === null || ziehtNr === nr) return;
      e.preventDefault();
      reiter.classList.add('dokumentreiter--ziel');
    });
    reiter.addEventListener('dragleave', () => reiter.classList.remove('dokumentreiter--ziel'));
    reiter.addEventListener('drop', (e) => {
      e.preventDefault();
      reiter.classList.remove('dokumentreiter--ziel');
      if (ziehtNr === null || ziehtNr === nr) return;
      Dokumente.verschieben(ziehtNr, Dokumente.liste().indexOf(nr));
      ziehtNr = null;
      dokumentleisteBauen();
    });

    leiste.appendChild(reiter);
  }

  const plus = document.createElement('button');
  plus.className = 'dokumentleiste__neu';
  plus.type = 'button';
  plus.textContent = '+';
  plus.title = 'Neues Dokument (Strg+N)';
  plus.setAttribute('aria-label', 'Neues Dokument');
  plus.addEventListener('click', () => B.neu());
  leiste.appendChild(plus);
}

/* Das Zuletztgeschriebene zurückholen — wie in der App. Ein Fenster, das
   beim Öffnen leer ist, obwohl gestern etwas drinstand, ist ein Verlust. */
grundschriftAnwenden();
Dateien.stileSetzen(Speicher.lies('importstil', ''));
Dokument.setzeInhalt(Speicher.lies('inhalt', '<p><br></p>'));
$('kopfzeile').innerHTML = Speicher.lies('kopfinhalt', '');
$('fusszeile').innerHTML = Speicher.lies('fussinhalt', '');
for (const teil of ['kopfzeile', 'fusszeile']) {
  $(teil).addEventListener('input', () => {
    Speicher.schreib(teil === 'kopfzeile' ? 'kopfinhalt' : 'fussinhalt', $(teil).innerHTML);
  });
}
geaendert = false;
$('zettel').value = KI.zettelLies();

/* Damit Fett und Kursiv als <b>/<i> herauskommen und nicht als Stilangaben:
   Das lässt sich später leichter nach ODF übersetzen. */
try { document.execCommand('styleWithCSS', false, false); } catch (e) { /* egal */ }

menueBauen();
werkzeugeBauen();
KIteil.empfaengerBauen();
KIteil.kiKnoepfeAuffrischen();
ansichtAnwenden();
/* Erst die Schalter aus der Tabelle, dann das Übrige: „Steuerzeichen"
   fragt die fünf Formatierungszeichen ab, und die müssen dafür stehen. */
alleSchalterAnwenden();
alleWerteAnwenden();
ansichtExtras();
kopfFussAnwenden();
seiteAnwenden();
layoutAnwenden();
vorlagenAnwenden();
if (design) designAnwenden(design);
papierAnwenden();
zeilennummernAnwenden();
trennungAnwenden();
seitenfarbeAnwenden();
lesehilfeAnwenden();
wasserzeichenAnwenden();
seitenrahmenAnwenden();
markupAnwenden();
netzAnwenden();
feld.lang = Speicher.lies('pruefsprache', 'de');
feld.classList.toggle('dokument--verfolgt', verfolgenAn);
schriftenNachtragen();
zuletztHolen();
vorlagenHolen();
setzeZoom(zoom);
titelSetzen();
zahlenAuffrischen();
werkzeugeAuffrischen();

/* Die Abschnitte kommen vor dem Text: Der Bogen soll gleich beim Öffnen
   den Aufbau des ersten Abschnitts tragen und nicht erst, wenn jemand
   hineinklickt. */
/* Antwortet die KI spät, muss jemand es zeichnen — sonst käme ihr Fund an
   und bliebe unsichtbar. */
if (Bruecke) {
  Bruecke.beiAenderung = () => {
    if (pruefungLaeuft || lebendLaeuft) return;
    funde = Bruecke.offeneFehler().map((f) => f.fund).filter(Boolean);
    zeichneFunde();
    markiereFunde(absatzAmZeiger());
    meldeFunde(Dokument.lies().text.length);
  };
}

abschnitteHolen();
abschnittAnwenden(0);

if (Bruecke) Bruecke.textSetzen(Dokument.lies().text);

/* Ganz zuletzt: Beide brauchen SYMBOLE und symbol(), und die stehen weiter
   unten in der Datei. Weiter oben aufgerufen liefe das Register ins Leere. */
menueleisteAnwenden();
bedienungAnwenden();
flaecheAnwenden();
/* Farbschema, Schriftpaar und Effekt auf das Blatt legen. */
designFeinAnwenden();
/* Felder, die sich neu rechnen sollen, beim Start nachziehen. */
zeitfelderAuffrischen();
/* Unten rechts: Ansichten und Schieber. Auch hier erst jetzt, weil die
   Knöpfe ihre Zeichnungen aus SYMBOLE holen. */
statuszeileBauen();

/* Die Reiter der offenen Dokumente. Ganz zuletzt, weil sie Namen und
   Änderungsstand aller Dokumente zeigt — beides steht erst jetzt fest. */
dokumentleisteBauen();


})();
