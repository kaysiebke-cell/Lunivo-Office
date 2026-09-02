/* ============================================================
   Das Programm: Menüs, Werkzeuge, Tafel, Statuszeile.

   Die Menüs stehen weiter unten als Liste. Wer einen Punkt hinzufügen
   will, schreibt eine Zeile — die Leiste baut sich daraus selbst.
   ============================================================ */
'use strict';

(() => {

const $ = (id) => document.getElementById(id);
const feld = Dokument.feld;

/* Der Speicher hängt an eigenen Schlüsseln. Das Schreibprogramm ist ein
   eigenes Programm; es fasst nichts an, was der App gehört. */
const Speicher = {
  lies(name, ersatz) {
    try { const w = localStorage.getItem('sp.' + name); return w === null ? ersatz : JSON.parse(w); }
    catch (e) { return ersatz; }
  },
  schreib(name, wert) {
    try { localStorage.setItem('sp.' + name, JSON.stringify(wert)); } catch (e) { /* voll */ }
  },
};

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

const CM = 37.795275590551185;     // ein Zentimeter in Bildpunkten bei 96 dpi

/* ============================================================
   2. Die Befehle. Menü, Werkzeugleiste und Tastenkürzel greifen alle
      auf dieselbe Liste zu — ein Befehl steht genau einmal da.
   ============================================================ */

const B = {};

/* ---- Datei ---- */

B.neu = () => {
  if (!darfVerwerfen()) return;
  /* Ein neues Blatt hat nichts mit der zuletzt geöffneten Datei zu tun —
     ihr Stilblatt muss weg, sonst schriebe man im Format eines fremden
     Briefes weiter. */
  Dateien.stileSetzen('');
  Speicher.schreib('importstil', '');
  Dokument.setzeInhalt('<p><br></p>');
  dateiname = 'Unbenannt 1';
  geaendert = false;
  leereFunde('Noch nicht geprüft.');
  merkeText();
  titelSetzen();
};

/* Welches Format beim Speichern genommen wird, wenn eine Datei dieser Art
   geöffnet wurde. Was sich nicht zurückschreiben lässt, kommt dem Nächsten
   gleich: Eine Word-Vorlage wird zur Word-Datei. */
const SCHREIBBAR = {
  odt: 'odt', fodt: 'fodt', docx: 'docx', doc: 'doc', rtf: 'rtf',
  html: 'html', htm: 'html', txt: 'txt', md: 'txt',
  dotx: 'docx', docm: 'docx', odf: 'odt',
};

B.oeffnen = async () => {
  if (!darfVerwerfen()) return;

  /* Erst der Dateibrowser des Systems — der kennt die Ordner des Menschen,
     seine Lesezeichen und die gewohnte Bedienung. Nur wenn es ihn nicht gibt
     (im Browser statt im eigenen Fenster), bleibt der schlichte Dateiwähler. */
  let wahl = null;
  try {
    const antwort = await fetch('oeffnen-dialog', { method: 'POST' });
    if (antwort.ok) wahl = await antwort.json();
  } catch (e) { /* kein eigenes Fenster — weiter unten */ }

  if (wahl && wahl.abgebrochen) { melde('Nicht geöffnet.'); return; }

  if (wahl && wahl.pfad) {
    try {
      const daten = await fetch('lesen');
      if (!daten.ok) {
        let grund = 'Fehler ' + daten.status;
        try { grund = (await daten.json()).fehler || grund; } catch (e) { /* egal */ }
        throw new Error(grund);
      }
      await dateiUebernehmen(new File([await daten.blob()], wahl.name || 'Dokument'));
    } catch (grund) {
      melde('Die Datei ließ sich nicht öffnen: ' + grund.message);
    }
    return;
  }

  const waehler = document.createElement('input');
  waehler.type = 'file';
  waehler.accept = '.odt,.fodt,.docx,.doc,.rtf,.html,.htm,.txt,.md,.xml,text/plain,text/html';
  waehler.addEventListener('change', async () => {
    const datei = waehler.files && waehler.files[0];
    if (datei) await dateiUebernehmen(datei);
  });
  waehler.click();
};

/* Eine Datei ins Blatt holen — gleich, ob sie aus dem Dialog des Systems
   oder aus dem Dateiwähler kommt. */
async function dateiUebernehmen(datei) {
  try {
    Dokument.setzeInhalt(await Dateien.oeffne(datei));

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
B.speichernOdt   = () => { Speicher.schreib('endung', 'odt');  speichereAls('odt'); };
B.speichernFodt  = () => { Speicher.schreib('endung', 'fodt'); speichereAls('fodt'); };
B.speichernHtml  = () => { Speicher.schreib('endung', 'html'); speichereAls('html'); };
B.speichernTxt   = () => { Speicher.schreib('endung', 'txt');  speichereAls('txt'); };
B.speichernDocx  = () => { Speicher.schreib('endung', 'docx'); speichereAls('docx'); };

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
    const antwort = await fetch('speichern-dialog?name=' + encodeURIComponent(dateiname)
                              + '&format=' + encodeURIComponent(Speicher.lies('endung', 'odt')),
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

    const geschrieben = await fetch('schreiben', { method: 'POST', body: datei });
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
B.speichernDoc   = () => { Speicher.schreib('endung', 'doc');  speichereAls('doc'); };
B.speichernRtf   = () => { Speicher.schreib('endung', 'rtf');  speichereAls('rtf'); };
/* PDF ist kein Format zum Weiterschreiben — es wird ausgegeben, nicht
   gespeichert. Deshalb merkt es sich das Programm auch nicht als die Art,
   in der künftig gesichert wird. */
B.speichernPdf   = () => speichereAls('pdf');
B.speichernEpub  = () => speichereAls('epub');

B.umbenennen = () => {
  const neu = prompt('Wie soll das Dokument heißen?', dateiname);
  if (neu === null) return;
  dateiname = neu.trim() || 'Unbenannt 1';
  titelSetzen();
};

B.drucken = () => window.print();

B.beenden = () => { if (darfVerwerfen()) window.close(); };

/* ---- Bearbeiten ---- */

B.rueckgaengig = () => Dokument.befehl('undo');
B.wiederholen  = () => Dokument.befehl('redo');
B.ausschneiden = () => Dokument.befehl('cut');
B.kopieren     = () => Dokument.befehl('copy');
B.einfuegen    = async () => {
  /* Strg+V macht der Browser selbst. Über das Menü geht es nur mit der
     Zwischenablage-Erlaubnis — klappt sie nicht, sagen wir das auch. */
  try {
    const text = await navigator.clipboard.readText();
    feld.focus();
    document.execCommand('insertText', false, text);
  } catch (e) {
    melde('Einfügen geht hier nur mit Strg+V.');
  }
};
B.einfuegenOhne = B.einfuegen;
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
B.punkte  = () => Dokument.befehl('insertUnorderedList');
B.zahlen  = () => Dokument.befehl('insertOrderedList');
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
     Untertitel, nicht beides. */
  el.classList.remove('titel', 'untertitel', 'ohne-abstand');
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
B.seitenumbruch = () => Dokument.einfuegen('<p style="page-break-before:always"><br></p>');

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

B.tabelle = () => {
  const zeilen = parseInt(prompt('Wie viele Zeilen?', '3'), 10);
  if (!zeilen || zeilen < 1) return;
  const spalten = parseInt(prompt('Wie viele Spalten?', '3'), 10);
  if (!spalten || spalten < 1) return;
  const zeile = '<tr>' + '<td><br></td>'.repeat(Math.min(spalten, 20)) + '</tr>';
  Dokument.einfuegen('<table>' + zeile.repeat(Math.min(zeilen, 200)) + '</table><p><br></p>');
};

const zeichen = (z) => () => Dokument.einfuegen(z === ' ' ? '&nbsp;' : z);

/* ============================================================
   2b. Ein Fenster für Rückfragen

   „prompt" reicht für eine Zahl. Sobald mehrere Angaben zusammengehören —
   Titel, Verfasser, Stichwörter — braucht es einen Kasten, in dem man sie
   nebeneinander sieht und die Eingabe auch abbrechen kann.
   ============================================================ */
function fenster(titel, felder, beiOk, knopfName = 'Übernehmen', breit = false) {
  const grund = document.createElement('div');
  grund.className = 'dialoggrund';

  const kasten = document.createElement('div');
  kasten.className = breit ? 'dialog dialog--breit' : 'dialog';
  kasten.innerHTML = '<h3 class="dialog__titel"></h3>';
  kasten.querySelector('.dialog__titel').textContent = titel;

  const eingaben = {};
  for (const feldChen of felder) {
    if (feldChen.art === 'satz') {
      const p = document.createElement('p');
      p.className = 'dialog__satz';
      p.textContent = feldChen.text;
      kasten.appendChild(p);
      continue;
    }
    /* Ein fertig gebauter Block. Für Seiten, die mehr sind als ein Absatz —
       die Hilfe etwa, die eine Treppe zeichnet statt einen Satz zu schreiben. */
    if (feldChen.art === 'knoten') {
      kasten.appendChild(feldChen.knoten);
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
    kasten.appendChild(zeile);
    eingaben[feldChen.schluessel] = eingabe;
  }

  const knoepfe = document.createElement('div');
  knoepfe.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  const ok = document.createElement('button');
  ok.className = 'knopf knopf--haupt'; ok.textContent = knopfName;
  knoepfe.append(ab, ok);
  kasten.appendChild(knoepfe);
  grund.appendChild(kasten);
  document.body.appendChild(grund);

  const zu = () => { grund.remove(); auswahlZurueck(); };
  ab.addEventListener('click', zu);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) zu(); });
  ok.addEventListener('click', () => {
    const werte = {};
    for (const [name, eingabe] of Object.entries(eingaben)) werte[name] = eingabe.value;
    zu();
    beiOk(werte);
  });
  document.addEventListener('keydown', function flucht(e) {
    if (!document.body.contains(grund)) { document.removeEventListener('keydown', flucht); return; }
    if (e.key === 'Escape') { e.preventDefault(); zu(); }
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

  const eigene = document.createElement('label');
  eigene.className = 'farbtafel__eigene';
  eigene.textContent = 'Eigene Farbe ';
  const feldChen = document.createElement('input');
  feldChen.type = 'color';
  feldChen.value = '#2F6FB5';
  feldChen.addEventListener('input', () => {
    tafel.remove();
    auswahlZurueck();
    Dokument.befehl(befehl, feldChen.value);
    melde(titel + ' gesetzt.');
  });
  eigene.appendChild(feldChen);
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

B.absatzabstand = () => {
  fenster('Absatzabstand', [
    { art: 'satz', text: 'Der Abstand über und unter dem Absatz, in Millimetern.' },
    { schluessel: 'oben', name: 'darüber', art: 'number', wert: '0', schritt: '0.5' },
    { schluessel: 'unten', name: 'darunter', art: 'number', wert: '2.5', schritt: '0.5' },
  ], (werte) => {
    aufAbsaetze((el) => {
      el.style.marginTop = (parseFloat(werte.oben) || 0) + 'mm';
      el.style.marginBottom = (parseFloat(werte.unten) || 0) + 'mm';
    });
    melde('Absatzabstand gesetzt.');
  });
};

/* ---- Seite: Ränder und Spalten ---- */
let seitenrand = Speicher.lies('seitenrand', { oben: 20, unten: 20, links: 20, rechts: 20 });
let spalten = Speicher.lies('spalten', 1);

function seiteAnwenden() {
  const blatt = $('blatt');
  blatt.style.paddingTop = seitenrand.oben + 'mm';
  blatt.style.paddingBottom = seitenrand.unten + 'mm';
  blatt.style.paddingLeft = seitenrand.links + 'mm';
  blatt.style.paddingRight = seitenrand.rechts + 'mm';
  feld.style.columnCount = spalten > 1 ? spalten : '';
  feld.style.columnGap = spalten > 1 ? '8mm' : '';
  Speicher.schreib('seitenrand', seitenrand);
  Speicher.schreib('spalten', spalten);
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
    melde('Seitenränder gesetzt.');
  });
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

B.textfeld = () => {
  Dokument.einfuegen('<div class="textrahmen"><p>Text im Rahmen</p></div><p><br></p>');
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
}
B.kopfzeile = () => { kopfAn = !kopfAn; kopfFussAnwenden(); if (kopfAn) $('kopfzeile').focus(); };
B.fusszeile = () => { fussAn = !fussAn; kopfFussAnwenden(); if (fussAn) $('fusszeile').focus(); };

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
let steuerzeichen = Speicher.lies('steuerzeichen', false);
let leistenAn = Speicher.lies('leisten', true);

function ansichtExtras() {
  $('lineal').hidden = !lineal;
  feld.classList.toggle('dokument--steuerzeichen', steuerzeichen);
  $('werkzeugleiste').hidden = !leistenAn;
  $('werkzeugleiste2').hidden = !leistenAn;
  Speicher.schreib('lineal', lineal);
  Speicher.schreib('steuerzeichen', steuerzeichen);
  Speicher.schreib('leisten', leistenAn);
  menueBauen();
}
B.linealZeigen = () => { lineal = !lineal; ansichtExtras(); };
B.steuerzeichenZeigen = () => { steuerzeichen = !steuerzeichen; ansichtExtras(); };
B.leistenZeigen = () => { leistenAn = !leistenAn; ansichtExtras(); };

/* ------------------------------------------------------------
   Menüleiste ein und aus

   Im Writer geht sie weg, und die Alt-Taste holt sie zurück. Ohne diesen
   Rückweg wäre der Menüpunkt eine Falle: Wer die Leiste ausblendet, hat
   damit auch den Menüpunkt ausgeblendet, mit dem er sie wiederholt.
   ------------------------------------------------------------ */
let menueleisteAn = Speicher.lies('menueleiste', true);

function menueleisteAnwenden() {
  $('menueleiste').hidden = !menueleisteAn;
}

B.menueleisteZeigen = () => {
  menueleisteAn = !menueleisteAn;
  Speicher.schreib('menueleiste', menueleisteAn);
  menueleisteAnwenden();
  if (!menueleisteAn) melde('Menüleiste aus. Die Alt-Taste holt sie zurück.');
  menueBauen();
};

document.addEventListener('keydown', (e) => {
  if (e.key !== 'Alt' || e.ctrlKey || e.shiftKey || menueleisteAn) return;
  e.preventDefault();
  $('menueleiste').hidden = false;
  /* Nur so lange, wie sie gebraucht wird: Wer daneben klickt, wollte sie
     nicht dauerhaft. Wer im Menü auf „Menüleiste" geht, schaltet sie an. */
  const wiederWeg = (ereignis) => {
    if ($('menueleiste').contains(ereignis.target)) return;
    if (!menueleisteAn) $('menueleiste').hidden = true;
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
const REGISTER = [
  ['Datei', [
    ['Neu', [['neu', 'Neu', () => B.neu(), 'gross'],
             ['oeffnen', 'Öffnen', () => B.oeffnen(), 'gross'],
             ['speichern', 'Speichern', () => B.speichern(), 'gross']]],
    ['Ausgeben', [['pdf', 'Als PDF', () => B.alsPdf(), 'gross'],
                  ['drucken', 'Drucken', () => B.drucken(), 'gross'],
                  ['vorschau', 'Ansicht', () => B.seitenansicht()],
                  ['kette', 'Senden', () => B.senden ? B.senden() : B.alsPdf()]]],
    ['Zuletzt', [['zurueck', 'Rückgängig', () => B.zurueck()],
                 ['vor', 'Wiederholen', () => B.vor()]]],
  ]],

  ['Start', [
    ['Ablage', [['kleben', 'Einfügen', () => B.einfuegen(), 'gross'],
                ['schere', 'Ausschneiden', () => B.ausschneiden()],
                ['kopie', 'Kopieren', () => B.kopieren()],
                ['pinsel', 'Format übertragen', () => B.formatPinsel()]]],
    ['Schrift', [['F', 'Fett', () => B.fett()], ['K', 'Kursiv', () => B.kursiv()],
                 ['U', 'Unterstrichen', () => B.unter()], ['S', 'Durchgestrichen', () => B.durch()],
                 ['hoch', 'Hochgestellt', () => B.hoch()], ['tief', 'Tiefgestellt', () => B.tief()],
                 ['farbe', 'Schriftfarbe', () => B.schriftfarbe()],
                 ['marker', 'Hervorheben', () => B.hervorheben()],
                 ['radierer', 'Formatierung entfernen', () => B.schlicht()]]],
    ['Absatz', [['links', 'Linksbündig', () => B.links()], ['mitte', 'Zentriert', () => B.mitte()],
                ['rechts', 'Rechtsbündig', () => B.rechts()], ['block', 'Blocksatz', () => B.block()],
                ['punkte', 'Aufzählung', () => B.punkte()], ['zahlen', 'Nummerierung', () => B.zahlen()],
                ['mehr', 'Einzug vergrößern', () => B.einzugMehr()],
                ['weniger', 'Einzug verkleinern', () => B.einzugWeniger()],
                ['abstand', 'Zeilenabstand', () => B.zeilenabstand()]]],
    ['Suchen', [['lupe', 'Suchen und Ersetzen', () => B.suchen(), 'gross']]],
  ]],

  ['Einfügen', [
    ['Tabelle', [['tabelle', 'Tabelle', () => B.tabelle(), 'gross']]],
    ['Bilder', [['bild', 'Bild', () => B.bild(), 'gross'],
                ['saeule', 'Diagramm', () => B.diagramm(), 'gross'],
                ['rahmen', 'Textrahmen', () => B.textrahmen()]]],
    ['Kopf und Fuß', [['kopfz', 'Kopfzeile', () => B.kopfzeile(), 'gross'],
                      ['fussz', 'Fußzeile', () => B.fusszeile(), 'gross'],
                      ['zahl', 'Seitenzahl', () => B.seitenzahl()],
                      ['umbruch', 'Umbruch', () => B.seitenumbruch()]]],
    ['Sonstiges', [['kette', 'Verknüpfung', () => B.verknuepfung()],
                   ['notiz', 'Kommentar', () => B.kommentar()],
                   ['omega', 'Sonderzeichen', () => B.sonderzeichen()]]],
  ]],

  ['Layout', [
    ['Seite', [['A4', 'Format', () => B.seitenformat(), 'gross'],
               ['Rand', 'Ränder', () => B.seitenraender(), 'gross'],
               ['Spalten', 'Spalten', () => B.spalten(), 'gross']]],
    ['Absatz', [['mehr', 'Einzug vergrößern', () => B.einzugMehr()],
                ['weniger', 'Einzug verkleinern', () => B.einzugWeniger()],
                ['abstand', 'Zeilenabstand', () => B.zeilenabstand()]]],
    ['Seitenwechsel', [['umbruch', 'Umbruch', () => B.seitenumbruch(), 'gross']]],
  ]],

  ['Schreibhilfe', [
    ['Prüfen', [['haken', 'Prüfen', () => pruefen(), 'gross'],
                ['verfolgt', 'Gründlich', () => B.gruendlichPruefen(), 'gross'],
                ['stift', 'Alles Eindeutige', () => allesUebernehmen()]]],
    ['Hören', [['lupe', 'Vorlesen', () => B.vorlesen(), 'gross'],
               ['Stimme', 'Stimme und Tempo', () => B.stimmeWaehlen()]]],
    ['KI', [['KI', 'Korrektur', () => kiKorrigieren(), 'gross'],
            ['Vorschlag', 'Vorschläge', () => kiVorschlaege(), 'gross'],
            ['Übersetzen', 'Übersetzen', () => kiUebersetzen(), 'gross']]],
    ['Zeigen', [['Tafel', 'Seitenleiste', () => B.tafelZeigen()]]],
  ]],

  ['Ansicht', [
    ['Zoom', [['lupe', 'Vergrößern', () => B.groesser(), 'gross'],
              ['weniger', 'Verkleinern', () => B.kleiner(), 'gross'],
              ['100 %', 'Normal', () => B.normal()]]],
    ['Zeigen', [['Lineal', 'Lineal', () => B.linealZeigen()],
                ['Tafel', 'Seitenleiste', () => B.tafelZeigen()],
                ['Hell', 'Hell/Dunkel', () => setzeThema(THEMEN[(THEMEN.indexOf(thema) + 1) % THEMEN.length])()]]],
    ['Oberfläche', [['mehr', 'Benutzeroberfläche', () => B.benutzeroberflaeche(), 'gross']]],
  ]],
];

let registerOffen = Speicher.lies('register', 'Start');

function registerBauen() {
  const reiter = $('register-reiter');
  const band = $('register-band');
  if (!reiter || !band) return;

  reiter.innerHTML = '';
  for (const [name] of REGISTER) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.textContent = name;
    knopf.setAttribute('role', 'tab');
    if (name === registerOffen) knopf.className = 'register--offen';
    knopf.addEventListener('click', () => {
      registerOffen = name;
      Speicher.schreib('register', name);
      registerBauen();
    });
    reiter.appendChild(knopf);
  }

  band.innerHTML = '';
  const gewaehlt = (REGISTER.find(([name]) => name === registerOffen) || REGISTER[1])[1];

  for (const [gruppenName, eintraege] of gewaehlt) {
    const gruppe = document.createElement('div');
    gruppe.className = 'register__gruppe';

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
        k.appendChild(wort);
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
      k.addEventListener('click', tun);
      return k;
    };

    for (const [zeichen, titel, tun, gross] of eintraege) {
      if (gross) reihe.appendChild(bauen(zeichen, titel, tun, true));
      else kleineKiste.appendChild(bauen(zeichen, titel, tun, false));
    }
    if (kleineKiste.childNodes.length) reihe.appendChild(kleineKiste);
    gruppe.appendChild(reihe);

    const name = document.createElement('span');
    name.className = 'register__name';
    name.textContent = gruppenName;
    gruppe.appendChild(name);

    band.appendChild(gruppe);
  }
}

/* ------------------------------------------------------------
   Symbolleisten oder Register
   ------------------------------------------------------------ */
let flaeche = Speicher.lies('flaeche', 'leisten');

function flaecheAnwenden() {
  document.body.classList.toggle('flaeche--register', flaeche === 'register');
  if (flaeche === 'register') registerBauen();
}

B.benutzeroberflaeche = () => {
  fenster('Benutzeroberfläche', [
    { art: 'satz', text:
        'Dieselben Befehle, anders sortiert. Die Symbolleisten stehen in '
      + 'zwei Zeilen immer alle da; die Register zeigen weniger auf einmal, '
      + 'dafür mit Namen daneben.\n\n'
      + 'Die Menüleiste bleibt in beiden Fällen — sie ist der Weg zu allem, '
      + 'was in keine Leiste passt.' },
    { schluessel: 'wahl', name: 'Ansicht', art: 'auswahl',
      werte: [['leisten', 'Symbolleisten (wie bisher)'],
              ['register', 'In Registern (wie Word)']],
      wert: flaeche },
  ], (werte) => {
    flaeche = werte.wahl === 'register' ? 'register' : 'leisten';
    Speicher.schreib('flaeche', flaeche);
    flaecheAnwenden();
    menueBauen();
  });
};

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

B.vorschau = () => {
  /* Die Druckvorschau ist der Druckdialog selbst: Er zeigt das Blatt so, wie
     es auf Papier kommt. Ein eigener Nachbau daneben wiche irgendwann davon
     ab — und dann wüsste niemand, welcher der beiden stimmt. */
  melde('Die Vorschau steht im Druckfenster.');
  window.print();
};

/* ---- Tabelle ---- */
function zelleJetzt() {
  let k = window.getSelection().anchorNode;
  while (k && k !== feld) {
    if (k.nodeType === Node.ELEMENT_NODE && (k.tagName === 'TD' || k.tagName === 'TH')) return k;
    k = k.parentNode;
  }
  return null;
}

function mitTabelle(tun) {
  const zelle = zelleJetzt();
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
B.formKnopf = () => {
  Dokument.einfuegen('<button class="formknopf" type="button">Schaltfläche</button>');
  melde('Schaltfläche eingefügt.');
};

/* ---- Extras ---- */
/* „Rechtschreibung & Grammatik" wie in der Leiste des Writers: Beides auf
   einmal. Die Wellenlinien des Systems finden falsch geschriebene Wörter,
   die Schreibhilfe findet, was danach noch schiefsteht. */
B.rechtschreibpruefung = () => {
  if (!feld.spellcheck) { feld.spellcheck = true; KI.Speicher.schreib('wellen', true); }
  feld.blur(); feld.focus();
  pruefen();
};

B.rechtschreibung = () => {
  const an = !feld.spellcheck;
  feld.spellcheck = an;
  KI.Speicher.schreib('wellen', an);
  feld.blur(); feld.focus();
  melde(an ? 'Rote Wellenlinien an.' : 'Rote Wellenlinien aus.');
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
    const treffer = /^(.*?)[\s:;,\t]+(-?[\d.,]+)\s*$/.exec(zeile.trim());
    if (!treffer) continue;
    const wert = parseFloat(treffer[2].replace(/\./g, '').replace(',', '.'));
    if (Number.isNaN(wert)) continue;
    punkte.push({ name: treffer[1].trim(), wert });
  }
  return punkte;
}

const DIAGRAMMFARBEN = ['#2F6FB5', '#3E9C7A', '#C08A2E', '#B5563F', '#7A5EA8',
                        '#4A8FD8', '#5FB79A', '#D8A94E'];

function balkenSvg(punkte, titel) {
  const breite = 480;
  const hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);
  const luecke = flaeche / punkte.length;

  let aus = '';
  if (titel) aus += '<text x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';

  // Die Grundlinie: ohne sie schweben die Balken im Nichts.
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  punkte.forEach((p, i) => {
    const h = Math.abs(p.wert) / groesste * hoch;
    const x = rand.links + i * luecke + luecke * 0.15;
    const b = luecke * 0.7;
    const y = rand.oben + hoch - h;
    aus += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + b.toFixed(1)
         + '" height="' + h.toFixed(1) + '" fill="' + DIAGRAMMFARBEN[i % DIAGRAMMFARBEN.length] + '"/>';
    aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (y - 5).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#111417">' + alsText(String(p.wert)) + '</text>';
    aus += '<text x="' + (x + b / 2).toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(p.name) + '</text>';
  });
  return svgHuelle(breite, hoehe, aus);
}

function linienSvg(punkte, titel) {
  const breite = 480;
  const hoehe = 260;
  const rand = { oben: titel ? 34 : 14, unten: 44, links: 46, rechts: 14 };
  const flaeche = breite - rand.links - rand.rechts;
  const hoch = hoehe - rand.oben - rand.unten;
  const groesste = Math.max(...punkte.map((p) => Math.abs(p.wert)), 1);
  const schritt = punkte.length > 1 ? flaeche / (punkte.length - 1) : 0;

  let aus = '';
  if (titel) aus += '<text x="' + (breite / 2) + '" y="20" text-anchor="middle" '
                  + 'font-size="14" font-weight="600" fill="#111417">' + alsText(titel) + '</text>';
  aus += '<line x1="' + rand.links + '" y1="' + (rand.oben + hoch) + '" x2="'
       + (breite - rand.rechts) + '" y2="' + (rand.oben + hoch) + '" stroke="#9AA3AB"/>';

  const stellen = punkte.map((p, i) => [rand.links + i * schritt,
                                        rand.oben + hoch - Math.abs(p.wert) / groesste * hoch]);
  aus += '<polyline fill="none" stroke="#2F6FB5" stroke-width="2" points="'
       + stellen.map(([x, y]) => x.toFixed(1) + ',' + y.toFixed(1)).join(' ') + '"/>';
  stellen.forEach(([x, y], i) => {
    aus += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="3.5" fill="#2F6FB5"/>';
    aus += '<text x="' + x.toFixed(1) + '" y="' + (rand.oben + hoch + 15).toFixed(1)
         + '" text-anchor="middle" font-size="10" fill="#4C555E">' + alsText(punkte[i].name) + '</text>';
  });
  return svgHuelle(breite, hoehe, aus);
}

function kuchenSvg(punkte, titel) {
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
    const farbe = DIAGRAMMFARBEN[i % DIAGRAMMFARBEN.length];
    /* Ein einziges Stück wäre ein Kreis — und ein Kreisbogen über volle 360°
       zeichnet nichts. Deshalb dieser Sonderfall. */
    aus += punkte.length === 1
      ? '<circle cx="' + mitteX + '" cy="' + mitteY + '" r="' + r + '" fill="' + farbe + '"/>'
      : '<path d="M' + mitteX + ',' + mitteY + ' L' + x1.toFixed(1) + ',' + y1.toFixed(1)
        + ' A' + r + ',' + r + ' 0 ' + gross + ',1 ' + x2.toFixed(1) + ',' + y2.toFixed(1)
        + ' Z" fill="' + farbe + '"/>';

    const yl = (titel ? 60 : 46) + i * 22;
    aus += '<rect x="290" y="' + (yl - 10) + '" width="12" height="12" fill="' + farbe + '"/>';
    aus += '<text x="' + 310 + '" y="' + yl + '" font-size="11" fill="#111417">'
         + alsText(p.name) + ' — ' + Math.round(Math.abs(p.wert) / summe * 100) + ' %</text>';
  });
  return svgHuelle(breite, hoehe, aus);
}

const alsText = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const svgHuelle = (b, h, innen) =>
  '<svg class="diagramm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + b + ' ' + h + '"'
  + ' width="' + b + '" height="' + h + '" role="img">'
  + '<rect width="' + b + '" height="' + h + '" fill="#FFFFFF"/>' + innen + '</svg>';

B.diagramm = () => {
  auswahlMerken();
  fenster('Diagramm einfügen', [
    { art: 'satz', text: 'Je Zeile ein Wert: „Miete: 480". Punkt oder Komma sind beide recht.' },
    { schluessel: 'titel', name: 'Überschrift', wert: '' },
    { schluessel: 'art', name: 'Art', art: 'auswahl',
      werte: [['balken', 'Balken'], ['linie', 'Linie'], ['kuchen', 'Kreis']] },
    { schluessel: 'daten', name: 'Zahlen', art: 'flaeche', zeilen: 7,
      wert: 'Miete: 480\nStrom: 95\nVersicherung: 60' },
  ], (werte) => {
    const punkte = zahlenLesen(werte.daten);
    if (!punkte.length) { melde('Darin standen keine Zahlen, mit denen sich zeichnen ließe.'); return; }
    const bauer = { balken: balkenSvg, linie: linienSvg, kuchen: kuchenSvg }[werte.art] || balkenSvg;
    auswahlZurueck();
    Dokument.einfuegen('<p>' + bauer(punkte, werte.titel.trim()) + '</p><p><br></p>');
    melde('Diagramm mit ' + punkte.length + ' Werten eingefügt.');
  }, 'Einfügen');
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
    Dokument.einfuegen(mathml);
    melde('Formel eingefügt.');
  }, 'Einfügen');
};

/* ============================================================
   Zeichnen

   Vier Formen, die in einem Schreibprogramm wirklich vorkommen: Linie,
   Pfeil, Rechteck, Kreis. Auch sie sind SVG und damit Teil des Textes.
   ============================================================ */
const FORMEN = {
  linie:    '<line x1="6" y1="34" x2="114" y2="6" stroke="COLOR" stroke-width="2"/>',
  pfeil:    '<defs><marker id="MID" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">'
          + '<path d="M0,0 L7,3 L0,6 Z" fill="COLOR"/></marker></defs>'
          + '<line x1="6" y1="20" x2="106" y2="20" stroke="COLOR" stroke-width="2" marker-end="url(#MID)"/>',
  rechteck: '<rect x="6" y="6" width="108" height="48" fill="none" stroke="COLOR" stroke-width="2"/>',
  kreis:    '<circle cx="60" cy="30" r="26" fill="none" stroke="COLOR" stroke-width="2"/>',
};

B.zeichnen = () => {
  auswahlMerken();
  fenster('Form einfügen', [
    { art: 'satz', text: 'Die Form kommt an die Stelle des Zeigers und lässt sich danach wie ein Bild behandeln.' },
    { schluessel: 'form', name: 'Form', art: 'auswahl',
      werte: [['linie', 'Linie'], ['pfeil', 'Pfeil'], ['rechteck', 'Rechteck'], ['kreis', 'Kreis']] },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#2F6FB5' },
  ], (werte) => {
    const kennung = 'p' + Date.now().toString(36);
    const innen = (FORMEN[werte.form] || FORMEN.linie)
      .replace(/COLOR/g, werte.farbe)
      .replace(/MID/g, kennung);
    auswahlZurueck();
    Dokument.einfuegen('<svg class="zeichnung" xmlns="http://www.w3.org/2000/svg" '
      + 'viewBox="0 0 120 60" width="120" height="60">' + innen + '</svg>');
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

const AUTOKORREKTUR = [
  [/(^|[\s(\[])"/g, '$1„'],          // öffnendes Anführungszeichen
  [/"/g, '"'],                        // schließendes
  [/(^|[\s(\[])'/g, '$1‚'],
  [/'/g, "'"],
  [/(\s)--(\s)/g, '$1–$2'],
  [/\.\.\./g, '…'],
  [/(\d)\s*-\s*(\d)/g, '$1–$2'],     // Zahlenbereich: 10–20
];

function autokorrekturLaufen() {
  if (!autokorrekturAn) return;
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || !auswahl.isCollapsed) return;

  const knoten = auswahl.anchorNode;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return;

  const bis = auswahl.anchorOffset;
  const alt = knoten.data.slice(0, bis);
  let neu = alt;
  for (const [suche, ersatz] of AUTOKORREKTUR) neu = neu.replace(suche, ersatz);
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
   Makros

   Aufgezeichnet werden die Befehle, die ein Mensch aus dem Menü oder der
   Leiste auslöst — nicht jeder Tastendruck. Ein Makro ist damit eine Folge
   von Handgriffen, kein Mitschnitt.
   ============================================================ */
let makroLaeuft = null;             // sammelt beim Aufzeichnen

function makroMerken(name) {
  if (makroLaeuft && name) makroLaeuft.push(name);
}

/* Zu jedem Namen der Befehl aus den Menüs — beim Abspielen wird darüber
   nachgeschlagen. */
function befehlZuName(name) {
  for (const [, punkte] of MENUES) {
    for (const punkt of punkte) {
      if (punkt !== strich && punkt.name === name) return punkt.tun;
    }
  }
  return null;
}

B.makroAufnahme = () => {
  if (makroLaeuft) { melde('Es läuft schon eine Aufnahme. „Aufnahme beenden" hält sie an.'); return; }
  makroLaeuft = [];
  melde('Aufnahme läuft. Jeder Menüpunkt, den du jetzt wählst, kommt hinein.');
  menueBauen();
};

B.makroBeenden = () => {
  if (!makroLaeuft) { melde('Es läuft keine Aufnahme.'); return; }
  const schritte = makroLaeuft;
  makroLaeuft = null;
  menueBauen();

  if (!schritte.length) { melde('Nichts aufgezeichnet.'); return; }

  fenster('Makro sichern', [
    { art: 'satz', text: schritte.length + ' Schritte:\n' + schritte.join('\n') },
    { schluessel: 'name', name: 'Name', wert: 'Mein Makro' },
  ], (werte) => {
    const alle = Speicher.lies('makros', {});
    alle[werte.name.trim() || 'Ohne Namen'] = schritte;
    Speicher.schreib('makros', alle);
    melde('Makro „' + werte.name + '" gesichert.');
    menueBauen();
  }, 'Sichern');
};

B.makroAbspielen = () => {
  const alle = Speicher.lies('makros', {});
  const namen = Object.keys(alle);
  if (!namen.length) { melde('Es ist noch kein Makro aufgezeichnet.'); return; }

  fenster('Makro abspielen', [
    { schluessel: 'name', name: 'Makro', art: 'auswahl', werte: namen.map((n) => [n, n]) },
  ], (werte) => {
    const schritte = alle[werte.name] || [];
    let gelaufen = 0;
    for (const name of schritte) {
      const tun = befehlZuName(name);
      /* Was ein Fenster aufmacht, taugt nicht zum Abspielen — das Makro
         bliebe beim ersten Kasten stehen und wartete auf eine Eingabe. */
      if (!tun || /…$/.test(name)) continue;
      try { tun(); gelaufen++; } catch (e) { /* der nächste Schritt darf es versuchen */ }
    }
    melde(gelaufen + ' von ' + schritte.length + ' Schritten ausgeführt.');
  }, 'Abspielen');
};

B.makrosVerwalten = () => {
  const alle = Speicher.lies('makros', {});
  const namen = Object.keys(alle);
  if (!namen.length) { melde('Es ist noch kein Makro aufgezeichnet.'); return; }
  fenster('Makros', [
    { art: 'satz', text: namen.map((n) => n + ' — ' + alle[n].length + ' Schritte').join('\n') },
    { schluessel: 'weg', name: 'löschen', art: 'auswahl',
      werte: [['', '— nichts —']].concat(namen.map((n) => [n, n])) },
  ], (werte) => {
    if (!werte.weg) return;
    delete alle[werte.weg];
    Speicher.schreib('makros', alle);
    melde('Makro „' + werte.weg + '" gelöscht.');
    menueBauen();
  });
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

function vorlagenAnwenden() {
  let blatt = document.getElementById('vorlagenblatt');
  if (!blatt) {
    blatt = document.createElement('style');
    blatt.id = 'vorlagenblatt';
    document.head.appendChild(blatt);
  }
  let css = '';
  for (const [tag, wie] of Object.entries(vorlagenStile)) {
    css += '.dokument ' + tag + '{'
         + 'font-size:' + wie.groesse + 'pt;'
         + 'font-weight:' + (wie.fett ? '700' : '400') + ';'
         + 'color:' + wie.farbe + ';'
         + 'margin-bottom:' + wie.abstand + 'mm;'
         + '}';
  }
  blatt.textContent = css;
  Speicher.schreib('vorlagenstile', vorlagenStile);
}

B.vorlagenVerwalten = () => {
  const tags = Object.keys(vorlagenStile);
  fenster('Formatvorlagen verwalten', [
    { art: 'satz', text: 'Eine Vorlage ändern gilt für jeden Absatz, der sie trägt.' },
    { schluessel: 'tag', name: 'Vorlage', art: 'auswahl',
      werte: tags.map((t) => [t, vorlagenStile[t].name]) },
  ], (werte) => vorlageBearbeiten(werte.tag), 'Bearbeiten');
};

function vorlageBearbeiten(tag) {
  const wie = vorlagenStile[tag];
  if (!wie) return;
  fenster('Vorlage: ' + wie.name, [
    { schluessel: 'groesse', name: 'Größe (pt)', art: 'number', wert: wie.groesse },
    { schluessel: 'fett', name: 'Schriftschnitt', art: 'auswahl',
      werte: [['nein', 'normal'], ['ja', 'fett']], wert: wie.fett ? 'ja' : 'nein' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: wie.farbe },
    { schluessel: 'abstand', name: 'Abstand danach (mm)', art: 'number', wert: wie.abstand, schritt: '0.5' },
  ], (werte) => {
    wie.groesse = Math.max(6, Math.min(72, parseFloat(werte.groesse) || wie.groesse));
    wie.fett = werte.fett === 'ja';
    wie.farbe = werte.farbe;
    wie.abstand = Math.max(0, Math.min(40, parseFloat(werte.abstand) || 0));
    vorlagenAnwenden();
    melde('Vorlage „' + wie.name + '" geändert — überall, wo sie steht.');
  });
}

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

const setzeLayout = (wahl) => () => { layout = wahl; layoutAnwenden(); };

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
const UNTERSTRICHE = [
  ['solid', 'durchgezogen'], ['double', 'doppelt'],
  ['dotted', 'gepunktet'], ['dashed', 'gestrichelt'], ['wavy', 'gewellt'],
];

B.unterstrichArt = () => {
  auswahlMerken();
  fenster('Unterstreichen', [
    { schluessel: 'art', name: 'Linie', art: 'auswahl', werte: UNTERSTRICHE },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#111417' },
  ], (werte) => {
    auswahlZurueck();
    const auswahl = window.getSelection();
    if (!auswahl.rangeCount || auswahl.isCollapsed) { melde('Nichts markiert.'); return; }
    /* execCommand kennt nur „unterstrichen ja/nein". Für einen Linienstil
       braucht es ein eigenes Element um die Markierung herum. */
    const huelle = document.createElement('span');
    huelle.style.textDecoration = 'underline ' + werte.art + ' ' + werte.farbe;
    try {
      auswahl.getRangeAt(0).surroundContents(huelle);
      geaendertMelden();
      melde('Unterstrichen: ' + (UNTERSTRICHE.find((u) => u[0] === werte.art) || [, werte.art])[1] + '.');
    } catch (e) {
      /* Reicht die Markierung über mehrere Absätze, lässt sie sich nicht in
         ein Element fassen. Dann tut es die schlichte Unterstreichung. */
      Dokument.befehl('underline');
      melde('Über mehrere Absätze geht nur die einfache Linie.');
    }
  }, 'Anwenden');
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
B.absatzSchattierung = () => {
  auswahlMerken();
  fenster('Schattierung', [
    { art: 'satz', text: 'Hinterlegt den Absatz mit einer Farbe.' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#EEF2F7' },
  ], (werte) => {
    auswahlZurueck();
    aufAbsaetze((el) => { el.style.backgroundColor = werte.farbe; el.style.padding = '2mm 3mm'; });
    melde('Absatz hinterlegt.');
  }, 'Anwenden');
};

B.absatzRahmen = () => {
  auswahlMerken();
  fenster('Rahmenlinien', [
    { schluessel: 'wo', name: 'Rahmen', art: 'auswahl', werte: [
      ['alle', 'ringsum'], ['oben', 'nur oben'], ['unten', 'nur unten'],
      ['links', 'nur links'], ['keine', 'keine'],
    ] },
    { schluessel: 'staerke', name: 'Stärke (pt)', art: 'number', wert: '1', schritt: '0.5' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: '#7C858E' },
  ], (werte) => {
    auswahlZurueck();
    const linie = (parseFloat(werte.staerke) || 1) + 'pt solid ' + werte.farbe;
    aufAbsaetze((el) => {
      el.style.border = '';
      el.style.borderTop = el.style.borderBottom = el.style.borderLeft = el.style.borderRight = '';
      if (werte.wo === 'alle') { el.style.border = linie; el.style.padding = '2mm 3mm'; }
      else if (werte.wo === 'oben') { el.style.borderTop = linie; el.style.paddingTop = '2mm'; }
      else if (werte.wo === 'unten') { el.style.borderBottom = linie; el.style.paddingBottom = '2mm'; }
      else if (werte.wo === 'links') { el.style.borderLeft = linie; el.style.paddingLeft = '3mm'; }
    });
    melde(werte.wo === 'keine' ? 'Rahmen entfernt.' : 'Rahmen gesetzt.');
  }, 'Anwenden');
};

/* ============================================================
   Aus den Tabs Entwurf und Layout von Word
   ============================================================ */

/* ---- Papierformat und Ausrichtung ----
   Das Blatt hatte bisher eine feste Größe: A4 hoch. Wer einen Aushang quer
   schreibt oder auf A5 druckt, braucht beides. */
const PAPIERE = {
  a4:     { name: 'A4 (21 × 29,7 cm)',      breite: 210, hoehe: 297 },
  a5:     { name: 'A5 (14,8 × 21 cm)',      breite: 148, hoehe: 210 },
  a3:     { name: 'A3 (29,7 × 42 cm)',      breite: 297, hoehe: 420 },
  letter: { name: 'Letter (21,6 × 27,9 cm)', breite: 216, hoehe: 279 },
  legal:  { name: 'Legal (21,6 × 35,6 cm)',  breite: 216, hoehe: 356 },
};

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
}

const setzePapier = (art) => () => { papier = art; papierAnwenden(); melde(PAPIERE[art].name + '.'); };
B.querformat = () => {
  quer = !quer;
  papierAnwenden();
  melde(quer ? 'Querformat.' : 'Hochformat.');
};

/* ---- Seitenränder als Vorgaben ----
   „Normal", „Schmal", „Mittel", „Breit" wie in Word — die eigenen Werte
   bleiben daneben bestehen. */
const RANDVORGABEN = {
  normal: { name: 'Normal (2,5 cm)', oben: 25, unten: 25, links: 25, rechts: 25 },
  schmal: { name: 'Schmal (1,27 cm)', oben: 13, unten: 13, links: 13, rechts: 13 },
  mittel: { name: 'Mittel (2,54 / 1,91 cm)', oben: 25, unten: 25, links: 19, rechts: 19 },
  breit:  { name: 'Breit (2,54 / 5,08 cm)', oben: 25, unten: 25, links: 51, rechts: 51 },
};

const setzeRandVorgabe = (art) => () => {
  const wie = RANDVORGABEN[art];
  seitenrand.oben = wie.oben; seitenrand.unten = wie.unten;
  seitenrand.links = wie.links; seitenrand.rechts = wie.rechts;
  seiteAnwenden();
  melde('Seitenränder: ' + wie.name + '.');
};

/* ---- Einzug links und rechts, auf den Millimeter ----
   Die beiden Knöpfe in der Leiste rücken in Sprüngen ein. Wer einen genauen
   Wert braucht — etwa für ein eingerücktes Zitat —, gibt ihn hier ein. */
B.einzugGenau = () => {
  auswahlMerken();
  fenster('Einzug', [
    { art: 'satz', text: 'In Millimetern, vom Seitenrand aus gerechnet.' },
    { schluessel: 'links', name: 'links', art: 'number', wert: '0', schritt: '1' },
    { schluessel: 'rechts', name: 'rechts', art: 'number', wert: '0', schritt: '1' },
    { schluessel: 'erste', name: 'erste Zeile', art: 'number', wert: '0', schritt: '1' },
  ], (werte) => {
    auswahlZurueck();
    aufAbsaetze((el) => {
      el.style.marginLeft = (parseFloat(werte.links) || 0) + 'mm';
      el.style.marginRight = (parseFloat(werte.rechts) || 0) + 'mm';
      el.style.textIndent = (parseFloat(werte.erste) || 0) + 'mm';
    });
    melde('Einzug gesetzt.');
  });
};

/* ---- Zeilennummern ----
   Für Verträge und Schriftsätze: Jede Zeile bekommt links eine Zahl, auf
   die man sich beziehen kann. Gezählt werden Absätze — echte Zeilenumbrüche
   kennt nur der Zeichensatz beim Umbrechen, und die Zahl stünde bei jeder
   Fensterbreite woanders. */
let zeilennummern = Speicher.lies('zeilennummern', false);

function zeilennummernAnwenden() {
  feld.classList.toggle('dokument--zeilennummern', zeilennummern);
  Speicher.schreib('zeilennummern', zeilennummern);
  menueBauen();
}
B.zeilennummern = () => {
  zeilennummern = !zeilennummern;
  zeilennummernAnwenden();
  melde(zeilennummern ? 'Zeilennummern an — gezählt werden Absätze.' : 'Zeilennummern aus.');
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
  $('blatt').style.background = seitenfarbe || '';
  Speicher.schreib('seitenfarbe', seitenfarbe);
}

B.seitenfarbe = () => {
  fenster('Seitenfarbe', [
    { art: 'satz', text: 'Färbt das Blatt. Beim Drucken kostet das Farbe —\nfür ein Schreiben ans Amt lieber weiß lassen.' },
    { schluessel: 'farbe', name: 'Farbe', art: 'color', wert: seitenfarbe || '#FFFFFF' },
  ], (werte) => {
    seitenfarbe = werte.farbe.toLowerCase() === '#ffffff' ? '' : werte.farbe;
    seitenfarbeAnwenden();
    melde(seitenfarbe ? 'Seitenfarbe gesetzt.' : 'Seite wieder weiß.');
  });
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

B.leereSeite = () => {
  Dokument.einfuegen('<p style="page-break-after:always"><br></p><p><br></p>');
  melde('Leere Seite eingefügt.');
};

/* ============================================================
   Aus dem Referenzen-Tab von Word

   Diese Werkzeuge haben eines gemeinsam: Sie erzeugen Text, der sich aus
   dem Dokument selbst ergibt — Verzeichnisse, Nummern, Verweise. Wird der
   Text danach geändert, stimmt das Erzeugte nicht mehr; deshalb hat jedes
   ein „Aktualisieren".
   ============================================================ */

/* ---- Inhaltsverzeichnis ---- */
function ueberschriftenSammeln() {
  const gefunden = [];
  for (const el of feld.querySelectorAll('h1,h2,h3,h4')) {
    const text = el.textContent.trim();
    if (!text) continue;
    if (!el.id) el.id = 'ueber-' + gefunden.length + '-' + Math.random().toString(36).slice(2, 7);
    gefunden.push({ ebene: parseInt(el.tagName[1], 10), text, kennung: el.id });
  }
  return gefunden;
}

function inhaltsverzeichnisBauen(bisEbene) {
  const punkte = ueberschriftenSammeln().filter((u) => u.ebene <= bisEbene);
  if (!punkte.length) return null;

  let aus = '<div class="verzeichnis" data-art="inhalt" data-ebenen="' + bisEbene + '">'
          + '<p class="verzeichnis__titel">Inhaltsverzeichnis</p>';
  for (const punkt of punkte) {
    aus += '<p class="verzeichnis__zeile verzeichnis__zeile--' + punkt.ebene + '">'
         + '<a href="#' + punkt.kennung + '">' + alsSicher(punkt.text) + '</a></p>';
  }
  return aus + '</div>';
}

B.inhaltsverzeichnis = () => {
  fenster('Inhaltsverzeichnis', [
    { art: 'satz', text: 'Wird aus den Überschriften im Dokument gebaut.\n'
                       + 'Sind noch keine da, vergib erst welche über Formatvorlagen.' },
    { schluessel: 'ebenen', name: 'Bis Ebene', art: 'auswahl',
      werte: [['1', 'nur Überschrift 1'], ['2', 'bis Überschrift 2'],
              ['3', 'bis Überschrift 3'], ['4', 'bis Überschrift 4']], wert: '3' },
  ], (werte) => {
    const html = inhaltsverzeichnisBauen(parseInt(werte.ebenen, 10) || 3);
    if (!html) { melde('Im Dokument stehen noch keine Überschriften.'); return; }
    const altes = feld.querySelector('.verzeichnis[data-art="inhalt"]');
    if (altes) altes.outerHTML = html;
    else feld.insertAdjacentHTML('afterbegin', html + '<p><br></p>');
    geaendertMelden();
    melde(altes ? 'Inhaltsverzeichnis erneuert.' : 'Inhaltsverzeichnis eingefügt.');
  }, 'Einfügen');
};

B.verzeichnisseAktualisieren = () => {
  let erneuert = 0;

  const inhalt = feld.querySelector('.verzeichnis[data-art="inhalt"]');
  if (inhalt) {
    const html = inhaltsverzeichnisBauen(parseInt(inhalt.dataset.ebenen, 10) || 3);
    if (html) { inhalt.outerHTML = html; erneuert++; }
  }

  const abbildungen = feld.querySelector('.verzeichnis[data-art="abbildungen"]');
  if (abbildungen) {
    const html = abbildungsverzeichnisBauen();
    if (html) { abbildungen.outerHTML = html; erneuert++; }
  }

  const stichworte = feld.querySelector('.verzeichnis[data-art="index"]');
  if (stichworte) {
    const html = indexBauen();
    if (html) { stichworte.outerHTML = html; erneuert++; }
  }

  const literatur = feld.querySelector('.verzeichnis[data-art="literatur"]');
  if (literatur) {
    const html = literaturBauen();
    if (html) { literatur.outerHTML = html; erneuert++; }
  }

  /* Die Zitate im Text nach der aktuellen Zitierweise neu setzen. */
  const weise = Speicher.lies('zitierweise', 'apa');
  const quellen = quellenLesen();
  for (const marke of feld.querySelectorAll('.zitat')) {
    const quelle = quellen.find((q) => q.kennung === marke.dataset.quelle);
    if (!quelle) continue;
    marke.textContent = zitatAlsText(
      Object.assign({}, quelle, { seite: marke.dataset.seite || '' }),
      weise, quellen.indexOf(quelle) + 1);
  }

  fussnotenNumerieren();
  endnotenNumerieren();
  beschriftungenNumerieren();

  geaendertMelden();
  melde(erneuert ? erneuert + ' Verzeichnisse erneuert, Nummern nachgezogen.'
                 : 'Nummern nachgezogen — Verzeichnisse gibt es noch keine.');
};

/* ---- Fußnoten ----
   Die Zahl im Text und der Eintrag unten gehören zusammen. Beide werden
   durchnummeriert, sobald sich etwas ändert — von Hand gezählt stimmte es
   nach der ersten Einfügung nicht mehr. */
function fussnotenBereich() {
  let bereich = feld.querySelector('.fussnoten');
  if (!bereich) {
    bereich = document.createElement('div');
    bereich.className = 'fussnoten';
    bereich.contentEditable = 'true';
    feld.appendChild(bereich);
  }
  return bereich;
}

function fussnotenNumerieren() {
  const marken = [...feld.querySelectorAll('sup.fussnote')];
  const bereich = feld.querySelector('.fussnoten');
  marken.forEach((marke, i) => {
    marke.textContent = String(i + 1);
    const eintrag = bereich && bereich.querySelector('[data-fuss="' + marke.dataset.fuss + '"]');
    if (eintrag) {
      const zahl = eintrag.querySelector('.fussnote__zahl');
      if (zahl) zahl.textContent = (i + 1) + '. ';
    }
  });
  /* Steht keine Marke mehr im Text, hat auch der Bereich unten nichts mehr
     zu suchen. */
  if (bereich && !marken.length) bereich.remove();
  return marken.length;
}

B.fussnote = () => {
  auswahlMerken();
  fenster('Fußnote', [
    { art: 'satz', text: 'Die Zahl kommt an die Stelle des Zeigers,\nder Text ans Ende des Dokuments.' },
    { schluessel: 'text', name: 'Fußnote' },
  ], (werte) => {
    const text = werte.text.trim();
    if (!text) return;
    const kennung = 'f' + Date.now().toString(36);

    auswahlZurueck();
    Dokument.einfuegen('<sup class="fussnote" data-fuss="' + kennung + '">0</sup>');

    const bereich = fussnotenBereich();
    const zeile = document.createElement('p');
    zeile.className = 'fussnote__zeile';
    zeile.dataset.fuss = kennung;
    zeile.innerHTML = '<span class="fussnote__zahl"></span>' + alsSicher(text);
    bereich.appendChild(zeile);

    const zahl = fussnotenNumerieren();
    geaendertMelden();
    melde('Fußnote ' + zahl + ' gesetzt.');
  }, 'Einfügen');
};

/* ---- Beschriftungen und Abbildungsverzeichnis ---- */
function beschriftungenNumerieren() {
  const zaehler = {};
  for (const el of feld.querySelectorAll('.beschriftung')) {
    const art = el.dataset.art || 'Abbildung';
    zaehler[art] = (zaehler[art] || 0) + 1;
    const kopf = el.querySelector('.beschriftung__nummer');
    if (kopf) kopf.textContent = art + ' ' + zaehler[art] + ': ';
    if (!el.id) el.id = 'besch-' + art + '-' + zaehler[art];
  }
}

B.beschriftung = () => {
  auswahlMerken();
  fenster('Beschriftung', [
    { art: 'satz', text: 'Kommt unter das Bild oder die Tabelle, an der der Zeiger steht.' },
    { schluessel: 'art', name: 'Art', art: 'auswahl',
      werte: [['Abbildung', 'Abbildung'], ['Tabelle', 'Tabelle'], ['Formel', 'Formel']] },
    { schluessel: 'text', name: 'Text' },
  ], (werte) => {
    auswahlZurueck();
    Dokument.einfuegen('<p class="beschriftung" data-art="' + werte.art + '">'
      + '<span class="beschriftung__nummer"></span>' + alsSicher(werte.text) + '</p>');
    beschriftungenNumerieren();
    geaendertMelden();
    melde('Beschriftung eingefügt.');
  }, 'Einfügen');
};

function abbildungsverzeichnisBauen() {
  beschriftungenNumerieren();
  const punkte = [...feld.querySelectorAll('.beschriftung')];
  if (!punkte.length) return null;
  let aus = '<div class="verzeichnis" data-art="abbildungen">'
          + '<p class="verzeichnis__titel">Abbildungsverzeichnis</p>';
  for (const el of punkte) {
    aus += '<p class="verzeichnis__zeile"><a href="#' + el.id + '">'
         + alsSicher(el.textContent.trim()) + '</a></p>';
  }
  return aus + '</div>';
}

B.abbildungsverzeichnis = () => {
  const html = abbildungsverzeichnisBauen();
  if (!html) { melde('Es sind noch keine Beschriftungen vergeben.'); return; }
  const altes = feld.querySelector('.verzeichnis[data-art="abbildungen"]');
  if (altes) altes.outerHTML = html;
  else { feld.insertAdjacentHTML('beforeend', '<p><br></p>' + html); }
  geaendertMelden();
  melde(altes ? 'Abbildungsverzeichnis erneuert.' : 'Abbildungsverzeichnis eingefügt.');
};

/* ---- Stichwortverzeichnis ---- */
B.indexEintrag = () => {
  const auswahl = window.getSelection();
  const markiert = auswahl.rangeCount ? auswahl.toString().trim() : '';
  auswahlMerken();
  fenster('Eintrag für das Stichwortverzeichnis', [
    { schluessel: 'wort', name: 'Stichwort', wert: markiert },
  ], (werte) => {
    const wort = werte.wort.trim();
    if (!wort) return;
    auswahlZurueck();
    const kennung = 'i' + Date.now().toString(36);
    /* Die Marke selbst ist unsichtbar — sie merkt sich nur die Stelle. */
    elementEinfuegen('<span class="indexmarke" id="' + kennung + '" data-wort="'
      + alsSicher(wort).replace(/"/g, '&quot;') + '"></span>');
    melde('„' + wort + '" ins Stichwortverzeichnis aufgenommen.');
  }, 'Festlegen');
};

function indexBauen() {
  const marken = [...feld.querySelectorAll('.indexmarke')];
  if (!marken.length) return null;
  const nach = {};
  for (const marke of marken) {
    const wort = marke.dataset.wort || '';
    if (!wort) continue;
    (nach[wort] = nach[wort] || []).push(marke.id);
  }
  let aus = '<div class="verzeichnis" data-art="index">'
          + '<p class="verzeichnis__titel">Stichwortverzeichnis</p>';
  for (const wort of Object.keys(nach).sort((a, b) => a.localeCompare(b, 'de'))) {
    aus += '<p class="verzeichnis__zeile"><a href="#' + nach[wort][0] + '">'
         + alsSicher(wort) + '</a>'
         + (nach[wort].length > 1 ? ' <span class="verzeichnis__zahl">('
            + nach[wort].length + ' Stellen)</span>' : '') + '</p>';
  }
  return aus + '</div>';
}

B.stichwortverzeichnis = () => {
  const html = indexBauen();
  if (!html) { melde('Es sind noch keine Stichwörter festgelegt.'); return; }
  const altes = feld.querySelector('.verzeichnis[data-art="index"]');
  if (altes) altes.outerHTML = html;
  else feld.insertAdjacentHTML('beforeend', '<p><br></p>' + html);
  geaendertMelden();
  melde(altes ? 'Stichwortverzeichnis erneuert.' : 'Stichwortverzeichnis eingefügt.');
};

/* ---- Textmarke und Querverweis ---- */
B.textmarke = () => {
  auswahlMerken();
  fenster('Textmarke', [
    { art: 'satz', text: 'Eine Stelle im Dokument benennen, auf die man später verweisen kann.' },
    { schluessel: 'name', name: 'Name', wert: 'Stelle' },
  ], (werte) => {
    const name = werte.name.trim().replace(/[^A-Za-zÄÖÜäöüß0-9 _-]/g, '');
    if (!name) return;
    auswahlZurueck();
    elementEinfuegen('<span class="textmarke" id="marke-'
      + encodeURIComponent(name) + '" title="Textmarke: ' + alsSicher(name) + '"></span>');
    melde('Textmarke „' + name + '" gesetzt.');
  }, 'Setzen');
};

B.querverweis = () => {
  const marken = [...feld.querySelectorAll('.textmarke')]
    .map((el) => [el.id, decodeURIComponent(el.id.replace(/^marke-/, ''))]);
  const ueberschriften = ueberschriftenSammeln().map((u) => [u.kennung, u.text]);
  const alle = marken.concat(ueberschriften);

  if (!alle.length) { melde('Es gibt noch keine Textmarken und keine Überschriften.'); return; }

  auswahlMerken();
  fenster('Querverweis', [
    { schluessel: 'ziel', name: 'Verweis auf', art: 'auswahl', werte: alle },
  ], (werte) => {
    const eintrag = alle.find(([kennung]) => kennung === werte.ziel);
    if (!eintrag) return;
    auswahlZurueck();
    Dokument.einfuegen('<a class="querverweis" href="#' + eintrag[0] + '">'
      + alsSicher(eintrag[1]) + '</a>');
    melde('Querverweis eingefügt.');
  }, 'Einfügen');
};

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
function aenderungen() {
  return [...feld.querySelectorAll('ins.verfolgt, del.verfolgt')];
}

let aenderungStelle = -1;

function aenderungZeigen(stelle) {
  const alle = aenderungen();
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
  const alle = aenderungen();
  if (!alle.length) { melde('Es steht keine Änderung an.'); return; }
  const el = alle[Math.max(0, Math.min(aenderungStelle, alle.length - 1))];
  if (el.tagName === 'INS') el.replaceWith(...el.childNodes);
  else el.remove();
  aenderungStelle = Math.max(-1, aenderungStelle - 1);
  geaendertMelden();
  melde('Angenommen. Es bleiben ' + aenderungen().length + '.');
};

B.aenderungAblehnen = () => {
  const alle = aenderungen();
  if (!alle.length) { melde('Es steht keine Änderung an.'); return; }
  const el = alle[Math.max(0, Math.min(aenderungStelle, alle.length - 1))];
  if (el.tagName === 'INS') el.remove();
  else el.replaceWith(...el.childNodes);
  aenderungStelle = Math.max(-1, aenderungStelle - 1);
  geaendertMelden();
  melde('Abgelehnt. Es bleiben ' + aenderungen().length + '.');
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
};

/* ---- Netzlinien ---- */
let netzlinien = Speicher.lies('netzlinien', false);

function netzAnwenden() {
  $('blatt').classList.toggle('blatt--netz', netzlinien);
  Speicher.schreib('netzlinien', netzlinien);
  menueBauen();
}
B.netzlinien = () => { netzlinien = !netzlinien; netzAnwenden(); };

/* ---- Navigationsbereich ----
   Die Überschriften als Liste zum Anspringen — bei einem langen Schreiben
   der schnellste Weg zur richtigen Stelle. */
let navOffen = false;

function navBauen() {
  const kasten = $('navigation');
  const punkte = ueberschriftenSammeln();
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
    const antwort = await fetch('oeffnen-dialog', { method: 'POST' });
    if (antwort.ok) wahl = await antwort.json();
  } catch (e) { /* kein eigenes Fenster */ }

  if (!wahl || wahl.abgebrochen || !wahl.pfad) { melde('Nichts eingefügt.'); return; }

  try {
    const daten = await fetch('lesen');
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
function smartartAblauf(schritte) {
  const breite = 520;
  const hoehe = 90;
  const kasten = Math.min(120, (breite - (schritte.length - 1) * 26) / schritte.length);
  let aus = '';
  schritte.forEach((text, i) => {
    const x = i * (kasten + 26);
    aus += '<rect x="' + x + '" y="20" width="' + kasten + '" height="50" rx="7" fill="'
         + DIAGRAMMFARBEN[i % DIAGRAMMFARBEN.length] + '"/>'
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

function smartartKreis(schritte) {
  const groesse = 320;
  const mitte = groesse / 2;
  const r = 105;
  let aus = '';
  schritte.forEach((text, i) => {
    const winkel = -Math.PI / 2 + i * (Math.PI * 2 / schritte.length);
    const x = mitte + r * Math.cos(winkel);
    const y = mitte + r * Math.sin(winkel);
    aus += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="38" fill="'
         + DIAGRAMMFARBEN[i % DIAGRAMMFARBEN.length] + '"/>'
         + '<text x="' + x.toFixed(1) + '" y="' + (y + 4).toFixed(1) + '" text-anchor="middle" '
         + 'font-size="11" fill="#FFFFFF">' + alsText(kuerzeWort(text, 10)) + '</text>';
  });
  return svgHuelle(groesse, groesse, aus);
}

function smartartGliederung(schritte) {
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

function smartartListe(schritte) {
  const breite = 460;
  const hoehe = schritte.length * 52 + 10;
  let aus = '';
  schritte.forEach((text, i) => {
    const y = i * 52 + 5;
    aus += '<rect x="0" y="' + y + '" width="' + breite + '" height="42" rx="7" fill="'
         + DIAGRAMMFARBEN[i % DIAGRAMMFARBEN.length] + '"/>'
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
    Dokument.einfuegen('<p>' + bauer(schritte) + '</p><p><br></p>');
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
    const antwort = await fetch('oeffnen-dialog?nur=tabellen', { method: 'POST' });
    if (antwort.ok) wahl = await antwort.json();
  } catch (e) { /* kein eigenes Fenster */ }

  if (!wahl || wahl.abgebrochen || !wahl.pfad) { melde('Nichts eingefügt.'); return; }

  melde('Tabellenblatt wird gelesen …');
  try {
    const daten = await fetch('lesen');
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
const EFFEKTE = {
  keiner:  { name: 'kein Effekt', css: '' },
  schatten:{ name: 'Schatten',    css: 'text-shadow:1px 1px 2px rgba(0,0,0,.35)' },
  relief:  { name: 'Relief',      css: 'text-shadow:1px 1px 0 rgba(255,255,255,.8),2px 2px 2px rgba(0,0,0,.3)' },
  kontur:  { name: 'Kontur',      css: '-webkit-text-stroke:0.6px currentColor;color:transparent' },
  leuchten:{ name: 'Leuchten',    css: 'text-shadow:0 0 6px rgba(47,111,181,.65)' },
};

B.effekt = () => {
  auswahlMerken();
  fenster('Effekt', [
    { art: 'satz', text: 'Wirkt auf den markierten Text.' },
    { schluessel: 'art', name: 'Effekt', art: 'auswahl',
      werte: Object.entries(EFFEKTE).map(([k, v]) => [k, v.name]) },
  ], (werte) => {
    auswahlZurueck();
    const auswahl = window.getSelection();
    if (!auswahl.rangeCount || auswahl.isCollapsed) { melde('Nichts markiert.'); return; }
    const wie = EFFEKTE[werte.art];
    if (werte.art === 'keiner') {
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
  }, 'Anwenden');
};

/* ---- Umbrüche ---- */
B.spaltenumbruch = () => {
  Dokument.einfuegen('<span class="spaltenumbruch"></span>');
  melde('Spaltenumbruch gesetzt — er wirkt, sobald mehrere Spalten eingestellt sind.');
};

B.abschnittsumbruch = () => {
  /* Ein Abschnitt trennt Teile mit eigenem Aussehen — etwa ein Deckblatt
     vom Rest. Sichtbar als Linie, im Druck als Seitenwechsel. */
  Dokument.einfuegen('<hr class="abschnitt" data-abschnitt="1"><p><br></p>');
  melde('Abschnittsumbruch gesetzt.');
};

/* ---- Bilder anordnen ----
   Wie der Text um ein Bild läuft, welche Ebene es hat, wie es gedreht ist.
   In Word ist das die Gruppe „Anordnen". */
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
   Nachgereicht: Referenzen
   ============================================================ */

/* ---- Endnoten ----
   Wie Fußnoten, nur ganz am Ende und mit römischen Zahlen — so hält Word
   beide auseinander, und so sieht man auf einen Blick, welche Sorte
   gemeint ist. */
const ROEMISCH = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                  'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'];

function endnotenBereich() {
  let bereich = feld.querySelector('.endnoten');
  if (!bereich) {
    bereich = document.createElement('div');
    bereich.className = 'endnoten';
    bereich.innerHTML = '<p class="endnoten__titel">Endnoten</p>';
    feld.appendChild(bereich);
  }
  return bereich;
}

function endnotenNumerieren() {
  const marken = [...feld.querySelectorAll('sup.endnote')];
  const bereich = feld.querySelector('.endnoten');
  marken.forEach((marke, i) => {
    marke.textContent = ROEMISCH[i] || String(i + 1);
    const eintrag = bereich && bereich.querySelector('[data-end="' + marke.dataset.end + '"]');
    if (eintrag) {
      const zahl = eintrag.querySelector('.fussnote__zahl');
      if (zahl) zahl.textContent = (ROEMISCH[i] || (i + 1)) + '. ';
    }
  });
  if (bereich && !marken.length) bereich.remove();
  return marken.length;
}

B.endnote = () => {
  auswahlMerken();
  fenster('Endnote', [
    { art: 'satz', text: 'Die Zahl kommt an den Zeiger, der Text ganz ans Ende —\nhinter die Fußnoten, mit römischer Zählung.' },
    { schluessel: 'text', name: 'Endnote' },
  ], (werte) => {
    const text = werte.text.trim();
    if (!text) return;
    const kennung = 'e' + Date.now().toString(36);
    auswahlZurueck();
    Dokument.einfuegen('<sup class="endnote" data-end="' + kennung + '">0</sup>');

    const bereich = endnotenBereich();
    const zeile = document.createElement('p');
    zeile.className = 'fussnote__zeile';
    zeile.dataset.end = kennung;
    zeile.innerHTML = '<span class="fussnote__zahl"></span>' + alsSicher(text);
    bereich.appendChild(zeile);

    const zahl = endnotenNumerieren();
    geaendertMelden();
    melde('Endnote ' + (ROEMISCH[zahl - 1] || zahl) + ' gesetzt.');
  }, 'Einfügen');
};

/* ---- Von Fußnote zu Fußnote ---- */
let notenStelle = -1;

function noteZeigen(schritt) {
  const alle = [...feld.querySelectorAll('sup.fussnote, sup.endnote')];
  if (!alle.length) { melde('Im Text steht keine Fuß- oder Endnote.'); return; }
  notenStelle = (notenStelle + schritt + alle.length) % alle.length;
  const marke = alle[notenStelle];
  marke.scrollIntoView({ block: 'center' });
  marke.classList.add('note--gezeigt');
  setTimeout(() => marke.classList.remove('note--gezeigt'), 1500);
  const art = marke.classList.contains('endnote') ? 'Endnote' : 'Fußnote';
  melde(art + ' ' + marke.textContent + ' — ' + (notenStelle + 1) + ' von ' + alle.length + '.');
}
B.noteWeiter = () => noteZeigen(1);
B.noteZurueck = () => noteZeigen(-1);

B.notenZeigen = () => {
  const fuss = feld.querySelectorAll('sup.fussnote').length;
  const end = feld.querySelectorAll('sup.endnote').length;
  if (!fuss && !end) { melde('Im Text steht keine Fuß- oder Endnote.'); return; }
  const bereich = feld.querySelector('.fussnoten') || feld.querySelector('.endnoten');
  if (bereich) bereich.scrollIntoView({ block: 'start' });
  melde(fuss + ' Fußnoten, ' + end + ' Endnoten.');
};

/* ============================================================
   Zitate und Literaturverzeichnis

   Die Quellen stehen an einer Stelle und werden von dort zitiert. Wer eine
   Quelle später ändert, ändert sie damit überall — genau dafür sind
   Quellenverwaltungen da.

   Vier Zitierweisen: Sie unterscheiden sich nur in der Reihenfolge und
   Zeichensetzung, nicht in den Angaben. Deshalb liegt die Quelle einmal da
   und wird je nach Wahl anders gesetzt.
   ============================================================ */
const ZITIERWEISEN = {
  apa:     'APA',
  mla:     'MLA',
  chicago: 'Chicago',
  ieee:    'IEEE',
  dinnorm: 'DIN 1505',
};

const quellenLesen = () => Speicher.lies('quellen', []);
const quellenSchreiben = (liste) => Speicher.schreib('quellen', liste);

function quelleAlsText(quelle, weise, nummer) {
  const a = quelle.verfasser || 'Ohne Verfasser';
  const t = quelle.titel || 'Ohne Titel';
  const j = quelle.jahr || 'o. J.';
  const o = quelle.ort || '';
  const v = quelle.verlag || '';

  if (weise === 'mla') return a + ': ' + t + '. ' + (o ? o + ': ' : '') + v + ', ' + j + '.';
  if (weise === 'chicago') return a + '. ' + t + '. ' + (o ? o + ': ' : '') + v + ', ' + j + '.';
  if (weise === 'ieee') return '[' + (nummer || 1) + '] ' + a + ', „' + t + '", '
                              + (v ? v + ', ' : '') + j + '.';
  if (weise === 'dinnorm') return a + ': ' + t + '. ' + (o ? o : '') + (v ? ' : ' + v : '') + ', ' + j + '.';
  return a + ' (' + j + '). ' + t + '. ' + (v ? v + '.' : '');       // APA
}

function zitatAlsText(quelle, weise, nummer) {
  const name = (quelle.verfasser || 'Ohne Verfasser').split(',')[0].split(' ').pop();
  if (weise === 'ieee') return '[' + (nummer || 1) + ']';
  if (weise === 'mla') return '(' + name + (quelle.seite ? ' ' + quelle.seite : '') + ')';
  if (weise === 'chicago') return '(' + name + ' ' + (quelle.jahr || 'o. J.')
                                 + (quelle.seite ? ', ' + quelle.seite : '') + ')';
  return '(' + name + ', ' + (quelle.jahr || 'o. J.')
       + (quelle.seite ? ', S. ' + quelle.seite : '') + ')';         // APA, DIN
}

B.quelleNeu = () => {
  fenster('Quelle aufnehmen', [
    { art: 'satz', text: 'Die Angaben stehen einmal hier und gelten für jedes Zitat daraus.' },
    { schluessel: 'verfasser', name: 'Verfasser', wert: '' },
    { schluessel: 'titel', name: 'Titel', wert: '' },
    { schluessel: 'jahr', name: 'Jahr', wert: '' },
    { schluessel: 'verlag', name: 'Verlag', wert: '' },
    { schluessel: 'ort', name: 'Ort', wert: '' },
  ], (werte) => {
    if (!werte.titel.trim() && !werte.verfasser.trim()) {
      melde('Ohne Verfasser und Titel lässt sich nichts zitieren.');
      return;
    }
    const liste = quellenLesen();
    liste.push({
      kennung: 'q' + Date.now().toString(36),
      verfasser: werte.verfasser.trim(), titel: werte.titel.trim(),
      jahr: werte.jahr.trim(), verlag: werte.verlag.trim(), ort: werte.ort.trim(),
    });
    quellenSchreiben(liste);
    melde('Quelle aufgenommen — jetzt unter „Zitat einfügen" zu finden.');
  }, 'Aufnehmen');
};

B.quellenVerwalten = () => {
  const liste = quellenLesen();
  if (!liste.length) { melde('Es ist noch keine Quelle aufgenommen.'); return; }
  const weise = Speicher.lies('zitierweise', 'apa');
  fenster('Quellen', [
    { art: 'satz', text: liste.map((q, i) => (i + 1) + '. ' + quelleAlsText(q, weise, i + 1)).join('\n') },
    { schluessel: 'weg', name: 'Löschen', art: 'auswahl',
      werte: [['', '— nichts —']].concat(liste.map((q) => [q.kennung,
        (q.verfasser || 'Ohne Verfasser') + ': ' + (q.titel || 'Ohne Titel')])) },
  ], (werte) => {
    if (!werte.weg) return;
    quellenSchreiben(liste.filter((q) => q.kennung !== werte.weg));
    melde('Quelle gelöscht.');
  });
};

B.zitierweise = () => {
  fenster('Zitierweise', [
    { art: 'satz', text: 'Gilt für die Zitate im Text und für das Literaturverzeichnis.' },
    { schluessel: 'weise', name: 'Nach', art: 'auswahl',
      werte: Object.entries(ZITIERWEISEN), wert: Speicher.lies('zitierweise', 'apa') },
  ], (werte) => {
    Speicher.schreib('zitierweise', werte.weise);
    melde('Zitierweise: ' + ZITIERWEISEN[werte.weise] + '. '
        + 'Vorhandene Zitate ändern sich beim Aktualisieren.');
  });
};

B.zitat = () => {
  const liste = quellenLesen();
  if (!liste.length) {
    melde('Erst eine Quelle aufnehmen — Referenzen ▸ Zitate ▸ Quelle aufnehmen.');
    return;
  }
  auswahlMerken();
  fenster('Zitat einfügen', [
    { schluessel: 'quelle', name: 'Quelle', art: 'auswahl',
      werte: liste.map((q) => [q.kennung,
        (q.verfasser || 'Ohne Verfasser') + ': ' + (q.titel || 'Ohne Titel')]) },
    { schluessel: 'seite', name: 'Seite (freiwillig)', wert: '' },
  ], (werte) => {
    const quelle = liste.find((q) => q.kennung === werte.quelle);
    if (!quelle) return;
    const weise = Speicher.lies('zitierweise', 'apa');
    const nummer = liste.indexOf(quelle) + 1;
    const text = zitatAlsText(Object.assign({}, quelle, { seite: werte.seite.trim() }), weise, nummer);
    auswahlZurueck();
    elementEinfuegen('<span class="zitat" data-quelle="' + quelle.kennung + '" data-seite="'
      + alsSicher(werte.seite.trim()) + '">' + alsSicher(text) + '</span>');
    melde('Zitat eingefügt: ' + text);
  }, 'Einfügen');
};

function literaturBauen() {
  /* Nur die Quellen, die auch zitiert wurden — ein Verzeichnis mit
     ungenutzten Einträgen wäre falsch. Steht kein Zitat im Text, kommen
     alle hinein; dann ist es als Leseliste gemeint. */
  const liste = quellenLesen();
  if (!liste.length) return null;
  const weise = Speicher.lies('zitierweise', 'apa');

  const zitiert = new Set([...feld.querySelectorAll('.zitat')].map((z) => z.dataset.quelle));
  const genommen = zitiert.size ? liste.filter((q) => zitiert.has(q.kennung)) : liste;
  if (!genommen.length) return null;

  const sortiert = weise === 'ieee' ? genommen
    : genommen.slice().sort((a, b) =>
        (a.verfasser || '').localeCompare(b.verfasser || '', 'de'));

  let aus = '<div class="verzeichnis" data-art="literatur">'
          + '<p class="verzeichnis__titel">Literaturverzeichnis</p>';
  sortiert.forEach((q, i) => {
    aus += '<p class="verzeichnis__zeile verzeichnis__quelle">'
         + alsSicher(quelleAlsText(q, weise, i + 1)) + '</p>';
  });
  return aus + '</div>';
}

B.literaturverzeichnis = () => {
  const html = literaturBauen();
  if (!html) { melde('Es ist noch keine Quelle aufgenommen.'); return; }
  const altes = feld.querySelector('.verzeichnis[data-art="literatur"]');
  if (altes) altes.outerHTML = html;
  else feld.insertAdjacentHTML('beforeend', '<p><br></p>' + html);
  geaendertMelden();
  melde(altes ? 'Literaturverzeichnis erneuert.' : 'Literaturverzeichnis eingefügt.');
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
  const alle = aenderungen();
  const kommentareAlle = kommentare();
  if (!alle.length && !kommentareAlle.length) {
    leereFunde('Es steht keine Änderung und kein Kommentar an.');
    return;
  }

  funde = [];
  vorschlaege = [];
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
let vorhersageAn = Speicher.lies('vorhersage', false);
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
    leereFunde('LanguageTool hat nichts gefunden.');
    return;
  }

  /* Die Funde in dieselbe Form bringen wie die eigenen — dann zeichnet die
     Seitenleiste sie ohne Sonderbehandlung, und „Zeigen" und „Ändern"
     arbeiten wie gewohnt. */
  vorschlaege = [];
  funde = treffer.map((t) => ({
    von: t.von, bis: t.bis,
    alt: text.slice(t.von, t.bis),
    neu: t.vorschlag || '',
    zeigeAlt: text.slice(t.von, t.bis) || '(hier)',
    zeigeNeu: t.vorschlag || '—',
    grund: t.grund,
    art: t.vorschlag ? 'tipp' : 'hinweis',
    vonLanguageTool: true,
  }));

  zeichneFunde();
  markiereFunde();
  meldeFunde(text.length);
  melde(funde.length + (funde.length === 1 ? ' Fund' : ' Funde')
      + ' von LanguageTool — zusätzlich zu dem, was die Schreibhilfe sucht.');
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

B.handbuch = async () => {
  try {
    const antwort = await fetch('handbuch', { method: 'POST' });
    if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
    melde('Das Handbuch öffnet sich im Browser.');
  } catch (e) {
    melde('Das Handbuch steht unter help.libreoffice.org/latest/de/text/swriter/main0000.html');
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
        'Strg+N  Neu           Strg+O  Öffnen\n'
      + 'Strg+S  Speichern     Strg+P  Drucken\n'
      + 'Strg+Z  Rückgängig    Strg+Y  Wiederholen\n'
      + 'Strg+B  Fett          Strg+I  Kursiv\n'
      + 'Strg+U  Unterstrichen Strg+F  Suchen\n'
      + 'Strg++  Größer        Strg+−  Kleiner\n'
      + 'Strg+Enter  Seitenumbruch\n'
      + 'F5  Seitenleiste      F7  Prüfen\n'
      + 'F8  KI-Korrektur      F9  Einstellungen' },
  ], () => {}, 'Schließen');
};

/* ============================================================
   Welche Hilfe wann
   ------------------------------------------------------------
   Die Hilfen sind nicht gleichwertig, sie sind gestuft: oben steht,
   was sofort und umsonst geschieht, unten, was Zeit, ein Programm
   oder Geld kostet. Wer das weiß, geht nur so weit hinunter, wie er
   muss. Deshalb steht es hier und nicht in einer Anleitung, die
   niemand aufmacht.
   ============================================================ */

const HILFE_STUFEN = [
  ['1', 'Rote Wellenlinien', '', 'Gibt es das Wort überhaupt?',
   'sofort beim Tippen'],
  ['1', 'Wortvorhersage', '', 'Wie ging das Wort weiter?',
   'ab drei Buchstaben'],
  ['2', 'Rechtsklick auf ein Wort', '', 'Welches Wort war gemeint?',
   'sucht auch nach dem Klang'],
  ['3', 'Prüfen', 'F7', 'Ist es das richtige Wort? das/dass, wider/wieder',
   'die Schreibhilfe rechts'],
  ['4', 'Vorlesen', 'F4', 'Klingt der Satz rund?',
   'Stimmen aus dem System'],
  ['5', 'Gründlich prüfen', '', 'Stimmt die Grammatik?',
   'LanguageTool, einmal 400 MB'],
  ['6', 'KI-Korrektur', 'F8', 'Versteht das jemand? Passt der Ton?',
   'Internet und Guthaben'],
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
  for (const [zahl, name, taste, frage, dazu] of HILFE_STUFEN) {
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
  fenster('Über das Schreibprogramm', [
    { art: 'satz', text:
        'Schreibprogramm 1.2\n\n'
      + 'Die Prüfung und der Wortschatz stammen aus der Schreibhilfe.\n'
      + 'Word-Dateien und PDF macht LibreOffice im Hintergrund.\n\n'
      + 'Was geschrieben wird, bleibt auf diesem Rechner.' },
  ], () => {}, 'Schließen');
};


/* ---- Ansicht ---- */

function setzeZoom(wert) {
  zoom = Math.max(50, Math.min(300, Math.round(wert)));
  $('blatt').style.zoom = (zoom / 100).toFixed(2);
  $('status-zoom').textContent = zoom + ' %';
  Speicher.schreib('zoom', zoom);
}
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
const setzeThema = (wahl) => () => {
  thema = wahl;
  Speicher.schreib('thema', wahl);
  const dunkel = wahl === 'dark'
    || (wahl === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.dataset.theme = dunkel ? 'dark' : 'light';
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
    { name: 'Öffnen…', tun: B.oeffnen, taste: 'Strg+O' },
    strich,
    { name: 'Speichern', tun: B.speichern, taste: 'Strg+S' },
    { name: 'Speichern unter…', tun: B.speichernUnter, taste: 'Strg+Umschalt+S' },
    strich,
    { name: 'Umbenennen…', tun: B.umbenennen },
    { name: 'Dokumenteigenschaften…', tun: B.eigenschaften },
    strich,
    { name: 'Druckvorschau', tun: B.vorschau },
    { name: 'Drucken…', tun: B.drucken, taste: 'Strg+P' },
    strich,
    { name: 'Beenden', tun: B.beenden },
  ]],

  ['Bearbeiten', [
    { name: 'Rückgängig', tun: B.rueckgaengig, taste: 'Strg+Z' },
    { name: 'Wiederholen', tun: B.wiederholen, taste: 'Strg+Y' },
    strich,
    { name: 'Ausschneiden', tun: B.ausschneiden, taste: 'Strg+X' },
    { name: 'Kopieren', tun: B.kopieren, taste: 'Strg+C' },
    { name: 'Einfügen', tun: B.einfuegen, taste: 'Strg+V' },
    { name: 'Format übertragen', tun: B.formatUebertragen, haken: () => !!pinsel },
    strich,
    { name: 'Alles markieren', tun: B.allesMarkieren, taste: 'Strg+A' },
    { name: 'Objekte hervorheben', tun: B.objekteWaehlen },
    { name: 'Suchen und Ersetzen…', tun: () => sucheZeigen(true), taste: 'Strg+H' },
    strich,
    { name: 'Änderungen', unter: [
      { name: 'Änderungen verfolgen', tun: B.verfolgen, haken: () => verfolgenAn },
      { name: 'Alle Markups zeigen', tun: B.markupUmschalten, haken: () => markupZeigen },
      strich,
      { name: 'Nächste Änderung', tun: B.aenderungWeiter },
      { name: 'Vorherige Änderung', tun: B.aenderungZurueck },
      { name: 'Änderung annehmen', tun: B.aenderungAnnehmen },
      { name: 'Änderung ablehnen', tun: B.aenderungAblehnen },
      strich,
      { name: 'Alle übernehmen', tun: B.aenderungenUebernehmen },
      { name: 'Alle verwerfen', tun: B.aenderungenVerwerfen },
    ] },
  ]],

  ['Ansicht', [
    { name: 'Zoom', unter: [
      { name: 'Vergrößern', tun: B.groesser, taste: 'Strg++' },
      { name: 'Verkleinern', tun: B.kleiner, taste: 'Strg+−' },
      { name: 'Normalgröße', tun: B.normal, taste: 'Strg+0' },
      strich,
      { name: 'Seitenbreite', tun: B.zoomBreite },
      { name: 'Eine Seite', tun: B.zoomSeite },
      { name: 'In Prozent…', tun: B.zoomStufe },
    ] },
    { name: 'Darstellung', unter: [
      { name: 'Blatt (Druckbild)', tun: setzeLayout('blatt'), haken: () => layout === 'blatt' },
      { name: 'Zwei Blätter nebeneinander', tun: setzeLayout('doppelt'), haken: () => layout === 'doppelt' },
      { name: 'Fortlaufend (ohne Rand)', tun: setzeLayout('web'), haken: () => layout === 'web' },
      strich,
      { name: 'Lesemodus', tun: B.lesemodus, haken: () => lesemodus },
      { name: 'Gliederung', tun: B.gliederung, haken: () => gliederung },
    ] },
    { name: 'Anzeigen', unter: [
      { name: 'Benutzeroberfläche…', tun: B.benutzeroberflaeche },
      strich,
      { name: 'Menüleiste', tun: B.menueleisteZeigen, haken: () => menueleisteAn },
      { name: 'Symbolleisten', tun: B.leistenZeigen, haken: () => leistenAn },
      { name: 'Lineal', tun: B.linealZeigen, haken: () => lineal },
      { name: 'Steuerzeichen', tun: B.steuerzeichenZeigen, haken: () => steuerzeichen },
      { name: 'Textbegrenzungen', tun: B.markenZeigen, haken: () => marken },
      { name: 'Netzlinien', tun: B.netzlinien, haken: () => netzlinien },
      strich,
      { name: 'Navigationsbereich', tun: B.navigation, haken: () => navOffen },
      { name: 'Seitenleiste Schreibhilfe', tun: B.tafelZeigen, haken: () => tafelOffen, taste: 'F5' },
    ] },
    strich,
    { name: 'Helligkeit', unter: [
      { name: 'Wie das System', tun: setzeThema('auto'), haken: () => thema === 'auto' },
      { name: 'Immer hell', tun: setzeThema('light'), haken: () => thema === 'light' },
      { name: 'Immer dunkel', tun: setzeThema('dark'), haken: () => thema === 'dark' },
    ] },
  ]],

  ['Einfügen', [
    { name: 'Seiten', unter: [
      { name: 'Deckblatt…', tun: B.deckblatt },
      { name: 'Leere Seite', tun: B.leereSeite },
      { name: 'Seitenumbruch', tun: B.seitenumbruch, taste: 'Strg+Enter' },
    ] },
    strich,
    { name: 'Tabellen', unter: [
      { name: 'Tabelle einfügen…', tun: B.tabelle },
      { name: 'Schnelltabelle…', tun: B.schnelltabelle },
      { name: 'Tabellenblatt einbetten…', tun: B.tabellenblatt },
    ] },
    { name: 'Bilder und Formen', unter: [
      { name: 'Bild…', tun: B.bild },
      { name: 'Bildschirmfoto…', tun: B.screenshot },
      strich,
      { name: 'Diagramm…', tun: B.diagramm },
      { name: 'SmartArt…', tun: B.smartart },
      strich,
      { name: 'Form zeichnen…', tun: B.zeichnen },
      { name: 'Piktogramm…', tun: B.piktogramm },
      strich,
      { name: 'Anordnen…', tun: B.anordnen },
    ] },
    { name: 'Textrahmen', tun: B.textfeld },
    strich,
    { name: 'Kopf- und Fußzeile', unter: [
      { name: 'Kopfzeile', tun: B.kopfzeile, haken: () => kopfAn },
      { name: 'Fußzeile', tun: B.fusszeile, haken: () => fussAn },
      { name: 'Seitennummer', tun: B.seitennummer },
    ] },
    { name: 'Verweise', unter: [
      { name: 'Hyperlink…', tun: B.hyperlink },
      { name: 'Textmarke…', tun: B.textmarke },
      { name: 'Querverweis…', tun: B.querverweis },
      strich,
      { name: 'Kommentar…', tun: B.kommentar },
    ] },
    { name: 'Text', unter: [
      { name: 'Schmuckschrift…', tun: B.wordart },
      { name: 'Initiale', tun: B.initiale },
      { name: 'Text aus Datei…', tun: B.textAusDatei },
      { name: 'Schnellbaustein…', tun: B.schnellbaustein },
      strich,
      { name: 'Datum', tun: B.datum },
      { name: 'Uhrzeit', tun: B.uhrzeit },
    ] },
    { name: 'Zeichen', unter: [
      { name: 'Formel…', tun: B.formel },
      { name: 'Sonderzeichen…', tun: B.sonderzeichen },
      strich,
      { name: 'Anführungszeichen „ “', tun: zeichen('„“') },
      { name: 'Gedankenstrich –', tun: zeichen('–') },
      { name: 'Geschütztes Leerzeichen', tun: zeichen(' ') },
    ] },
  ]],

  ['Format', [
    { name: 'Schrift', unter: [
      { name: 'Fett', tun: B.fett, taste: 'Strg+B', haken: () => Dokument.anGeschaltet('bold') },
      { name: 'Kursiv', tun: B.kursiv, taste: 'Strg+I', haken: () => Dokument.anGeschaltet('italic') },
      { name: 'Unterstrichen', tun: B.unter, taste: 'Strg+U', haken: () => Dokument.anGeschaltet('underline') },
      { name: 'Durchgestrichen', tun: B.durch },
      strich,
      { name: 'Hochgestellt', tun: B.hoch },
      { name: 'Tiefgestellt', tun: B.tief },
      strich,
      { name: 'Größer', tun: B.schriftGroesser },
      { name: 'Kleiner', tun: B.schriftKleiner },
      { name: 'Groß- und Kleinschreibung…', tun: B.schreibweise },
      { name: 'Unterstreichen…', tun: B.unterstrichArt },
      strich,
      { name: 'Schriftfarbe…', tun: B.schriftfarbe },
      { name: 'Hervorhebungsfarbe…', tun: B.hervorheben },
      { name: 'Effekt…', tun: B.effekt },
    ] },
    { name: 'Absatz', unter: [
      { name: 'Linksbündig', tun: B.links },
      { name: 'Zentriert', tun: B.mitte },
      { name: 'Rechtsbündig', tun: B.rechts },
      { name: 'Blocksatz', tun: B.block },
      strich,
      { name: 'Zeilenabstand 1,0', tun: zeilenabstand('1.15') },
      { name: 'Zeilenabstand 1,5', tun: zeilenabstand('1.6') },
      { name: 'Zeilenabstand 2,0', tun: zeilenabstand('2.1') },
      { name: 'Absatzabstand…', tun: B.absatzabstand },
      strich,
      { name: 'Einzug vergrößern', tun: B.einzugMehr },
      { name: 'Einzug verkleinern', tun: B.einzugWeniger },
      { name: 'Einzug genau…', tun: B.einzugGenau },
    ] },
    { name: 'Listen', unter: [
      { name: 'Aufzählung', tun: B.punkte },
      { name: 'Nummerierung', tun: B.zahlen },
      strich,
      { name: 'Ebene tiefer', tun: B.ebeneTiefer },
      { name: 'Ebene höher', tun: B.ebeneHoeher },
      strich,
      { name: 'Sortieren…', tun: B.sortieren },
    ] },
    { name: 'Rahmen und Farbe', unter: [
      { name: 'Schattierung…', tun: B.absatzSchattierung },
      { name: 'Rahmenlinien…', tun: B.absatzRahmen },
    ] },
    strich,
    { name: 'Formatierung entfernen', tun: B.schlicht },
  ]],

  ['Formatvorlagen', [
    { name: 'Titel', tun: () => vorlageSetzen('h1', 'titel') },
    { name: 'Untertitel', tun: () => vorlageSetzen('h2', 'untertitel') },
    strich,
    { name: 'Fließtext', tun: () => absatz('p') },
    { name: 'Kein Leerraum', tun: () => vorlageSetzen('p', 'ohne-abstand') },
    { name: 'Überschriften', unter: [
      { name: 'Überschrift 1', tun: () => absatz('h1') },
      { name: 'Überschrift 2', tun: () => absatz('h2') },
      { name: 'Überschrift 3', tun: () => absatz('h3') },
      { name: 'Überschrift 4', tun: () => absatz('h4') },
    ] },
    { name: 'Weitere', unter: [
      { name: 'Zitat', tun: () => absatz('blockquote') },
      { name: 'Vorformatiert', tun: () => absatz('pre') },
    ] },
    strich,
    { name: 'Design', unter: Object.entries(DESIGNS).map(([k, v]) =>
      ({ name: v.name, tun: setzeDesign(k), haken: () => design === k })) },
    { name: 'Formatvorlagensatz', unter: Object.entries(VORLAGENSAETZE).map(([k, v]) =>
      ({ name: v.name, tun: setzeVorlagensatz(k) })) },
    strich,
    { name: 'Verwalten', unter: [
      { name: 'Vorlagen verwalten…', tun: B.vorlagenVerwalten },
      { name: 'Vorlagen zurücksetzen', tun: B.vorlagenZurueck },
      strich,
      { name: 'Seitenvorlage: Ränder…', tun: B.seitenraender },
      { name: 'Seitenvorlage: Spalten…', tun: B.spalten },
      { name: 'Rahmenvorlage: Textrahmen', tun: B.textfeld },
    ] },
    strich,
    { name: 'Zeichen zurücksetzen', tun: B.schlicht },
  ]],

  ['Layout', [
    { name: 'Papierformat', unter: [
      { name: 'Hochformat / Querformat', tun: B.querformat, haken: () => quer },
      strich,
      { name: 'A4', tun: setzePapier('a4'), haken: () => papier === 'a4' },
      { name: 'A5', tun: setzePapier('a5'), haken: () => papier === 'a5' },
      { name: 'A3', tun: setzePapier('a3'), haken: () => papier === 'a3' },
      { name: 'Letter', tun: setzePapier('letter'), haken: () => papier === 'letter' },
      { name: 'Legal', tun: setzePapier('legal'), haken: () => papier === 'legal' },
    ] },
    { name: 'Seitenränder', unter: [
      { name: 'Normal (2,5 cm)', tun: setzeRandVorgabe('normal') },
      { name: 'Schmal (1,3 cm)', tun: setzeRandVorgabe('schmal') },
      { name: 'Mittel', tun: setzeRandVorgabe('mittel') },
      { name: 'Breit', tun: setzeRandVorgabe('breit') },
      strich,
      { name: 'Eigene…', tun: B.seitenraender },
    ] },
    { name: 'Spalten…', tun: B.spalten },
    { name: 'Umbrüche', unter: [
      { name: 'Seitenumbruch', tun: B.seitenumbruch, taste: 'Strg+Enter' },
      { name: 'Spaltenumbruch', tun: B.spaltenumbruch },
      { name: 'Abschnittsumbruch', tun: B.abschnittsumbruch },
    ] },
    strich,
    { name: 'Seitenhintergrund', unter: [
      { name: 'Seitenfarbe…', tun: B.seitenfarbe },
      { name: 'Wasserzeichen…', tun: B.wasserzeichen },
      { name: 'Seitenrahmen…', tun: B.seitenrahmen },
    ] },
    strich,
    { name: 'Zeilennummern', tun: B.zeilennummern, haken: () => zeilennummern },
    { name: 'Silbentrennung', tun: B.silbentrennung, haken: () => trennung },
  ]],

  ['Referenzen', [
    { name: 'Inhaltsverzeichnis einfügen…', tun: B.inhaltsverzeichnis },
    { name: 'Verzeichnisse aktualisieren', tun: B.verzeichnisseAktualisieren },
    strich,
    { name: 'Fuß- und Endnoten', unter: [
      { name: 'Fußnote einfügen…', tun: B.fussnote },
      { name: 'Endnote einfügen…', tun: B.endnote },
      strich,
      { name: 'Nächste Note', tun: B.noteWeiter },
      { name: 'Vorige Note', tun: B.noteZurueck },
      { name: 'Noten anzeigen', tun: B.notenZeigen },
    ] },
    { name: 'Zitate', unter: [
      { name: 'Zitat einfügen…', tun: B.zitat },
      strich,
      { name: 'Quelle aufnehmen…', tun: B.quelleNeu },
      { name: 'Quellen verwalten…', tun: B.quellenVerwalten },
      { name: 'Zitierweise…', tun: B.zitierweise },
      strich,
      { name: 'Literaturverzeichnis einfügen', tun: B.literaturverzeichnis },
    ] },
    { name: 'Querverweis…', tun: B.querverweis },
    strich,
    { name: 'Abbildungen', unter: [
      { name: 'Beschriftung einfügen…', tun: B.beschriftung },
      { name: 'Abbildungsverzeichnis einfügen', tun: B.abbildungsverzeichnis },
    ] },
    { name: 'Stichwortverzeichnis', unter: [
      { name: 'Eintrag festlegen…', tun: B.indexEintrag },
      { name: 'Verzeichnis einfügen', tun: B.stichwortverzeichnis },
    ] },
  ]],

  ['Tabelle', [
    { name: 'Tabelle einfügen…', tun: B.tabelle },
    strich,
    { name: 'Einfügen', unter: [
      { name: 'Zeile darüber', tun: B.zeileOben },
      { name: 'Zeile darunter', tun: B.zeileUnten },
      { name: 'Spalte links', tun: B.spalteLinks },
      { name: 'Spalte rechts', tun: B.spalteRechts },
    ] },
    { name: 'Löschen', unter: [
      { name: 'Zeile', tun: B.zeileWeg },
      { name: 'Spalte', tun: B.spalteWeg },
      { name: 'Ganze Tabelle', tun: B.tabelleWeg },
    ] },
    strich,
    { name: 'Erste Zeile als Kopfzeile', tun: B.kopfzeileTabelle },
    { name: 'Rahmen ein und aus', tun: B.tabelleRahmen },
  ]],

  ['Formular', [
    { name: 'Textfeld', tun: B.formTextfeld },
    { name: 'Kontrollkästchen', tun: B.formKasten },
    { name: 'Schaltfläche', tun: B.formKnopf },
  ]],

  ['Extras', [
    { name: 'Rechtschreibung und Grammatik', tun: B.rechtschreibpruefung, taste: 'F7' },
    { name: 'Gründlich prüfen (LanguageTool)', tun: B.gruendlichPruefen },
    { name: 'Wörter für…  (Thesaurus)', tun: B.thesaurus },
    { name: 'Wörter zählen…', tun: B.woerterZaehlen },
    strich,
    { name: 'Beim Schreiben', unter: [
      { name: 'Wortvorhersage', tun: B.vorhersage, haken: () => vorhersageAn },
      { name: 'Rote Wellenlinien', tun: B.rechtschreibung, haken: () => feld.spellcheck },
      { name: 'AutoKorrektur', tun: B.autokorrektur, haken: () => autokorrekturAn },
      { name: 'Sprache für Korrekturhilfen…', tun: B.pruefsprache },
    ] },
    { name: 'Kommentare', unter: [
      { name: 'Nächster Kommentar', tun: B.kommentarWeiter },
      { name: 'Voriger Kommentar', tun: B.kommentarZurueck },
      strich,
      { name: 'Kommentar löschen', tun: B.kommentarWeg },
      { name: 'Alle löschen', tun: B.kommentareAlleWeg },
    ] },
    { name: 'Makros', unter: [
      { name: 'Aufzeichnen', tun: B.makroAufnahme, haken: () => !!makroLaeuft },
      { name: 'Aufnahme beenden…', tun: B.makroBeenden },
      strich,
      { name: 'Abspielen…', tun: B.makroAbspielen },
      { name: 'Verwalten…', tun: B.makrosVerwalten },
    ] },
    strich,
    { name: 'Sendungen', unter: [
      { name: 'Seriendruck-Assistent…', tun: B.seriendruck },
      { name: 'Vorschau auf Ergebnisse…', tun: B.serienVorschau },
      strich,
      { name: 'Seriendruckfeld…', tun: B.seriendruckfeld },
      { name: 'Adressblock und Grußzeile…', tun: B.adressblock },
      { name: 'Regel (Wenn–Dann)…', tun: B.seriendruckregel },
      strich,
      { name: 'Umschlag…', tun: B.umschlag },
      { name: 'Etiketten…', tun: B.etiketten },
    ] },
    strich,
    { name: 'Barrierefreiheit prüfen…', tun: B.barrierefrei },
    { name: 'Überarbeitungsbereich', tun: B.ueberarbeitungsbereich },
    { name: 'Bearbeitung sperren', tun: B.bearbeitungSperren, haken: () => gesperrt },
    strich,
    { name: 'Erweiterungsverwaltung…', tun: B.erweiterungen },
    { name: 'Optionen…', tun: () => Einstellungen.oeffnen(), taste: 'F9' },
  ]],

  ['Schreibhilfe', [
    { name: 'Vorlesen', unter: [
      { name: 'Vorlesen', tun: B.vorlesen, taste: 'F4' },
      { name: 'Ab hier vorlesen', tun: B.vorlesenAbSatz },
      { name: 'Anhalten', tun: B.vorlesenStopp },
      strich,
      { name: 'Stimme und Tempo…', tun: B.stimmeWaehlen },
    ] },
    strich,
    { name: 'Prüfen', tun: () => pruefen(), taste: 'F7' },
    { name: 'Gründlich prüfen (LanguageTool)', tun: B.gruendlichPruefen },
    { name: 'Alles Eindeutige übernehmen', tun: () => allesUebernehmen() },
    strich,
    { name: 'KI-Korrektur', tun: () => kiKorrigieren(), taste: 'F8' },
    { name: 'Vorschläge holen', tun: () => kiVorschlaege() },
    { name: 'Übersetzen', tun: () => kiUebersetzen() },
    strich,
    { name: 'Seitenleiste zeigen', tun: B.tafelZeigen, haken: () => tafelOffen },
    { name: 'Welche Hilfe wann…', tun: B.welcheHilfe },
    { name: 'Optionen…', tun: () => Einstellungen.oeffnen('ki'), taste: 'F9' },
    strich,
    { name: 'Was die Schreibhilfe sucht…', tun: () => melde(
      'Gesucht wird, was ein Rechtschreibprüfer nicht finden kann: das/dass, '
      + 'seit/seid, „wir hat", fehlende Kommas, zusammengetippte Wörter. '
      + 'Die Regeln kommen unverändert aus der Schreibhilfe-App.') },
  ]],

  ['Fenster', [
    { name: 'Neues Fenster', tun: B.neuesFenster },
    { name: 'Fenster wechseln…', tun: B.fensterListe },
    strich,
    { name: 'Anordnen', unter: [
      { name: 'Nebeneinander', tun: B.fensterNebeneinander },
      { name: 'Untereinander', tun: B.fensterUntereinander },
      { name: 'Gekachelt', tun: B.fensterKacheln },
    ] },
  ]],

  ['Hilfe', [
    { name: 'Welche Hilfe wann…', tun: B.welcheHilfe },
    strich,
    { name: 'LibreOffice-Handbuch', tun: B.handbuch },
    { name: 'Tastenkombinationen…', tun: B.tastenHilfe },
    strich,
    { name: 'Über das Schreibprogramm…', tun: B.ueber },
  ]],
];

let offenesMenue = null;

/* Beim Aufzeichnen eines Makros soll jeder gewählte Menüpunkt seinen Namen
   hinterlassen. Das geschieht hier an einer Stelle statt in jedem Befehl. */
function menuePunktTun(punkt) {
  makroMerken(punkt.name);
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
      punkteBauen(unterklappe, punkt.unter);
      huelle.appendChild(unterklappe);

      /* Auf- und zugeklappt wird von Hand, nicht über „:hover" im Stilblatt.
         Der Grund ist die Messung: Nach welcher Seite Platz ist, lässt sich
         erst sagen, wenn die Klappe sichtbar ist — und beim Hover übers
         Stilblatt ist sie das im Augenblick des Ereignisses noch nicht.
         So ist die Reihenfolge festgelegt: erst zeigen, dann messen. */
      huelle.addEventListener('mouseenter', () => {
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
let schriftJetzt = Speicher.lies('schrift', SCHRIFTEN[0]);

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

function schriftListeBauen(suche = '') {
  const wort = suche.trim().toLowerCase();
  const passt = (name) => !wort || name.toLowerCase().includes(wort);
  const bewaehrt = SCHRIFTEN.filter((s) => alleSchriften.includes(s));
  const uebrige = alleSchriften.filter((s) => !bewaehrt.includes(s));

  schriftTreffer = [];
  for (const [titel, namen] of [['Für Fließtext', bewaehrt.length ? bewaehrt : SCHRIFTEN],
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
    auswahlZurueck();
  }
}

/* Woanders hingeklickt heißt: nicht mehr gebraucht. */
document.addEventListener('mousedown', (e) => {
  if (schriftListe && !schriftListe.hidden && !e.target.closest('.schriftwahl')) {
    schriftListeZeigen(false);
  }
});

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
    schriftJetzt = SCHRIFTEN.find((s) => alle.includes(s)) || alle[0];
    wzSchrift.textContent = schriftJetzt;
  }

  wzSchrift.title = 'Schriftart — ' + alle.length + ' auf diesem Rechner';
  if (!schriftListe.hidden) schriftListeBauen('');
}
const GROESSEN = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36];
const VORLAGEN = [['p', 'Fließtext'], ['h1', 'Überschrift 1'],
                  ['h2', 'Überschrift 2'], ['h3', 'Überschrift 3']];

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
let wzVerfolgt = null;
let wzGroesse = null;

/* Kleine Strichzeichnungen statt Buchstaben-Behelfen. Sie stehen hier im
   Code und nicht als Bilddateien daneben: ein Symbol, eine Zeile. */
const SYMBOLE = {
  speichern: 'M4 4h11l5 5v11H4z M8 4v5h6V4 M8 20v-6h8v6',
  drucken:   'M7 9V4h10v5 M7 17H5a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-2 M7 14h10v6H7z',
  zurueck:   'M4 10h10a5 5 0 1 1 0 10h-3 M8 6l-4 4 4 4',
  vor:       'M20 10H10a5 5 0 1 0 0 10h3 M16 6l4 4-4 4',
  links:     'M4 6h16 M4 11h10 M4 16h16 M4 21h10',
  mitte:     'M4 6h16 M7 11h10 M4 16h16 M7 21h10',
  rechts:    'M4 6h16 M10 11h10 M4 16h16 M10 21h10',
  block:     'M4 6h16 M4 11h16 M4 16h16 M4 21h16',
  punkte:    'M9 7h11 M9 12h11 M9 17h11 M5 7h.01 M5 12h.01 M5 17h.01',
  zahlen:    'M10 7h10 M10 12h10 M10 17h10 M4 6h2v4 M4 10h3',
  mehr:      'M4 6h16 M4 18h16 M10 12h10 M4 12l3-2.5v5z',
  weniger:   'M4 6h16 M4 18h16 M10 12h10 M7 12L4 9.5v5z',
  haken:     'M4 12.5l5 5L20 6.5',
  neu:       'M6 3h8l4 4v14H6z M14 3v5h4',
  oeffnen:   'M3 7h6l2 2h10v10H3z',
  pdf:       'M6 3h8l4 4v14H6z M14 3v5h4 M9 14h1.5a1.5 1.5 0 0 0 0-3H9v6 M14 12h3 M14 15h2',
  vorschau:  'M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
  schere:    'M6 4l12 12 M18 4L6 16 M6 18a2 2 0 1 0 0 .01 M18 18a2 2 0 1 0 0 .01',
  kopie:     'M8 8h11v13H8z M5 16H3V3h13v2',
  kleben:    'M9 3h6v3H9z M6 5h2v2h8V5h2v16H6z',
  pinsel:    'M4 20h6 M7 20v-5 M5 15h10a3 3 0 0 0 3-3V4H8v8a3 3 0 0 0 3 3',
  tabelle:   'M3 4h18v16H3z M3 10h18 M3 15h18 M9 4v16 M15 4v16',
  bild:      'M3 5h18v14H3z M3 15l5-5 4 4 3-3 6 6',
  rahmen:    'M3 6h18v12H3z M7 10h10 M7 14h6',
  umbruch:   'M4 7h16 M4 17h16 M9 12h11 M6 12l2-2v4z',
  kette:     'M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1 M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1',
  kopfz:     'M3 4h18v5H3z M5 13h14 M5 17h10',
  fussz:     'M3 15h18v5H3z M5 7h14 M5 11h10',
  zahl:      'M3 4h18v11H3z M8 20h8 M12 17v3',
  notiz:     'M4 4h16v12H9l-5 4z',
  omega:     'M6 20h4v-2a7 7 0 1 1 4 0v2h4',
  hoch:      'M4 18l7-11 M11 18L4 7 M16 9h4 M18 7v4',
  tief:      'M4 16l7-11 M11 16L4 5 M16 19h4 M18 17v4',
  radierer:  'M7 20h13 M4 15l7-7 6 6-5 5H6z',
  farbe:     'M6 17h12 M8 14l4-9 4 9 M9.5 11h5',
  marker:    'M4 20h16 M7 16l8-8 3 3-8 8z M13 6l3 3',
  abstand:   'M6 4v16 M4 6l2-2 2 2 M4 18l2 2 2-2 M11 7h9 M11 12h9 M11 17h9',
  lupe:      'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M16 16l5 5',
  saeule:    'M3 20h18 M6 20V11h3v9 M11 20V6h3v14 M16 20v-6h3v6',
  stift:     'M4 20h4L20 8l-4-4L4 16z M14 6l4 4',
  verfolgt:  'M5 19h14 M8 15l9-9 3 3-9 9H8z M6 4h5 M8.5 2v4',
};

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
  const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  p.setAttribute('d', SYMBOLE[name]);
  s.appendChild(p);
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
  leisteBauen('werkzeugleiste', ({ knopf, trenner }) => {
    knopf('neu', 'Neu (Strg+N)', B.neu);
    knopf('oeffnen', 'Öffnen (Strg+O)', B.oeffnen);
    knopf('speichern', 'Speichern (Strg+S)', B.speichern);
    trenner();
    knopf('pdf', 'Als PDF ausgeben', B.speichernPdf);
    knopf('drucken', 'Drucken (Strg+P)', B.drucken);
    knopf('vorschau', 'Druckvorschau', B.vorschau);
    trenner();
    knopf('schere', 'Ausschneiden (Strg+X)', B.ausschneiden);
    knopf('kopie', 'Kopieren (Strg+C)', B.kopieren);
    knopf('kleben', 'Einfügen (Strg+V)', B.einfuegen);
    wzPinsel = knopf('pinsel', 'Format übertragen', B.formatUebertragen);
    trenner();
    knopf('zurueck', 'Rückgängig (Strg+Z)', B.rueckgaengig);
    knopf('vor', 'Wiederholen (Strg+Y)', B.wiederholen);
    trenner();
    knopf('haken', 'Rechtschreibung und Grammatik (F7)', B.rechtschreibpruefung);
    trenner();
    knopf('tabelle', 'Tabelle einfügen', B.tabelle);
    knopf('bild', 'Bild einfügen', B.bild);
    knopf('saeule', 'Diagramm einfügen', B.diagramm);
    knopf('rahmen', 'Textrahmen einfügen', B.textfeld);
    trenner();
    knopf('umbruch', 'Seitenumbruch (Strg+Enter)', B.seitenumbruch);
    knopf('kette', 'Hyperlink einfügen', B.hyperlink);
    trenner();
    knopf('kopfz', 'Kopfzeile', B.kopfzeile);
    knopf('fussz', 'Fußzeile', B.fusszeile);
    knopf('zahl', 'Seitennummer', B.seitennummer);
    trenner();
    wzVerfolgt = knopf('verfolgt', 'Änderungen verfolgen', B.verfolgen);
    knopf('notiz', 'Kommentar', B.kommentar);
    trenner();
    knopf('omega', 'Sonderzeichen', B.sonderzeichen);
    knopf('stift', 'Form zeichnen', B.zeichnen);
  });

  /* ------------------------------------------------------------
     Die untere Leiste: alles, was den Text selbst betrifft.
     ------------------------------------------------------------ */
  leisteBauen('werkzeugleiste2', ({ knopf, trenner, leiste }) => {
    wzVorlage = auswahl('wz-wahl--vorlage', VORLAGEN, absatz, 'Absatzformat');
    leiste.appendChild(wzVorlage);
    leiste.appendChild(schriftKnopfBauen());
    wzGroesse = auswahl('wz-wahl--groesse', GROESSEN.map((g) => [g, g]),
                        (g) => schriftgroesse(+g), 'Schriftgröße');
    wzGroesse.value = '12';                    // so groß steht der Text im Blatt
    leiste.appendChild(wzGroesse);
    trenner();

    knopf('F', 'Fett (Strg+B)', B.fett, 'wz--fett', 'bold');
    knopf('K', 'Kursiv (Strg+I)', B.kursiv, 'wz--kursiv', 'italic');
    knopf('U', 'Unterstrichen (Strg+U)', B.unter, 'wz--unter', 'underline');
    knopf('S', 'Durchgestrichen', B.durch, 'wz--durch', 'strikeThrough');
    knopf('hoch', 'Hochgestellt', B.hoch, '', 'superscript');
    knopf('tief', 'Tiefgestellt', B.tief, '', 'subscript');
    knopf('radierer', 'Formatierung entfernen', B.schlicht);
    trenner();

    knopf('farbe', 'Schriftfarbe', B.schriftfarbe);
    knopf('marker', 'Hervorhebungsfarbe', B.hervorheben);
    trenner();

    knopf('links', 'Linksbündig', B.links, '', 'justifyLeft');
    knopf('mitte', 'Zentriert', B.mitte, '', 'justifyCenter');
    knopf('rechts', 'Rechtsbündig', B.rechts, '', 'justifyRight');
    knopf('block', 'Blocksatz', B.block, '', 'justifyFull');
    trenner();

    knopf('punkte', 'Aufzählung', B.punkte, '', 'insertUnorderedList');
    knopf('zahlen', 'Nummerierung', B.zahlen, '', 'insertOrderedList');
    knopf('mehr', 'Einzug vergrößern', B.einzugMehr);
    knopf('weniger', 'Einzug verkleinern', B.einzugWeniger);
    trenner();

    /* Der Zeilenabstand ist eine Wahl aus dreien — als drei einzelne Knöpfe
       wäre die Leiste noch länger, und man sähe nicht, welcher gerade gilt. */
    const abstand = auswahl('wz-wahl--abstand',
      [['1.15', 'Zeilen 1,0'], ['1.6', 'Zeilen 1,5'], ['2.1', 'Zeilen 2,0']],
      (wert) => zeilenabstand(wert)(), 'Zeilenabstand');
    leiste.appendChild(abstand);
  });
}

function werkzeugeAuffrischen() {
  for (const k of $('werkzeugleiste').querySelectorAll('.wz[data-zustand]')) {
    k.classList.toggle('wz--an', Dokument.anGeschaltet(k.dataset.zustand));
  }
  if (wzVorlage) {
    const jetzt = Dokument.absatzformat();
    wzVorlage.value = VORLAGEN.some(([w]) => w === jetzt) ? jetzt : 'p';
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

function zeichneFunde() {
  const liste = $('funde');
  liste.innerHTML = '';
  KI.Gedaechtnis.merkeGezeigt(funde);

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

function markiereFunde() {
  markenEntfernen();

  /* Von hinten nach vorn: Jede eingesetzte Markierung teilt Textknoten auf.
     Vorn beginnend verschöben sich alle folgenden Stellen. */
  for (let i = funde.length - 1; i >= 0; i--) {
    const fund = funde[i];
    const { text, karte } = Dokument.lies();
    if (text.slice(fund.von, fund.bis) !== (fund.alt || text.slice(fund.von, fund.bis))) continue;

    const bereich = Dokument.bereich(karte, fund.von, fund.bis);

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
  if (html.indexOf('fundmarke') === -1) return html;
  const hilfe = document.createElement('div');
  hilfe.innerHTML = html;
  for (const marke of hilfe.querySelectorAll('span.fundmarke')) {
    const eltern = marke.parentNode;
    while (marke.firstChild) eltern.insertBefore(marke.firstChild, marke);
    marke.remove();
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

function rechtsMenueSchliessen() {
  if (rechtsMenue) { rechtsMenue.remove(); rechtsMenue = null; }
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

function rechtsMenueZeigen(e) {
  e.preventDefault();
  rechtsMenueSchliessen();

  const kasten = document.createElement('div');
  kasten.className = 'rechtsmenue';

  const eintrag = (beschriftung, tun, klasse = '') => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = 'rechtsmenue__punkt ' + klasse;
    k.textContent = beschriftung;
    k.addEventListener('mousedown', (ev) => ev.preventDefault());
    k.addEventListener('click', () => { rechtsMenueSchliessen(); tun(); });
    kasten.appendChild(k);
    return k;
  };
  const trennlinie = () => {
    const t = document.createElement('div');
    t.className = 'rechtsmenue__strich';
    kasten.appendChild(t);
  };

  /* Erst das Wort, auf das gezeigt wurde: Rechtschreibvorschläge stehen
     ganz oben, so wie es jedes Schreibprogramm hält. Sie brauchen keine
     vorherige Prüfung — das Wörterbuch liegt ohnehin im Speicher. */
  const stelle = wortAnPunkt(e.clientX, e.clientY);
  const unbekannt = stelle && !Pruefung.kennt(stelle.wort);
  const vorschlaege = unbekannt ? Pruefung.vorschlaegeFuer(stelle.wort) : [];

  if (unbekannt) {
    const kopf = document.createElement('div');
    kopf.className = 'rechtsmenue__kopf';
    kopf.textContent = vorschlaege.length
      ? '„' + stelle.wort + '" steht nicht im Wörterbuch'
      : '„' + stelle.wort + '" steht nicht im Wörterbuch — kein Vorschlag gefunden';
    kasten.appendChild(kopf);

    for (const wort of vorschlaege) {
      const ersatz = wieGeschrieben(stelle.wort, wort);
      eintrag(ersatz, () => {
        wortErsetzen(stelle, ersatz);
        /* Was hier von Hand gewählt wird, soll das Programm sich merken —
           beim nächsten Mal steht es dann gleich oben. */
        KI.Gedaechtnis.merkeAenderung({ wortEbene: true, alt: stelle.wort, neu: ersatz });
        melde('„' + stelle.wort + '" zu „' + ersatz + '" geändert.');
      }, 'rechtsmenue__punkt--vorschlag');
    }

    eintrag('Wort ins Gedächtnis aufnehmen', () => {
      const g = KI.Gedaechtnis.lies();
      g.inRuhe[stelle.wort.toLowerCase()] = true;
      KI.Gedaechtnis.schreib(g);
      melde('„' + stelle.wort + '" gilt künftig als richtig.');
      if (funde.length) pruefen();
    });
    trennlinie();
  }

  const fund = fundAnStelle(e.target);

  if (fund) {
    const kopf = document.createElement('div');
    kopf.className = 'rechtsmenue__kopf';
    kopf.textContent = fund.grund || 'Gefundene Stelle';
    kasten.appendChild(kopf);

    if (fund.art !== 'hinweis' && fund.neu) {
      /* Der Vorschlag steht fett und ganz oben — er ist der Grund, weshalb
         jemand die rechte Taste gedrückt hat. */
      eintrag(fund.neu, () => uebernimm(fund), 'rechtsmenue__punkt--vorschlag');
    }

    eintrag('Diese Stelle zeigen', () => Dokument.zeige(fund.von, fund.bis));

    if (fund.alt && /^[A-Za-zÄÖÜäöüß-]+$/.test(fund.alt)) {
      eintrag('Wort in Ruhe lassen', () => {
        const g = KI.Gedaechtnis.lies();
        g.inRuhe[fund.alt.toLowerCase()] = true;
        KI.Gedaechtnis.schreib(g);
        melde('„' + fund.alt + '" wird künftig nicht mehr angestrichen.');
        pruefen();
      });
    }

    eintrag('Übergehen', () => {
      funde = funde.filter((f) => f !== fund);
      zeichneFunde();
      markiereFunde();
      meldeFunde(Dokument.lies().text.length);
    });
    trennlinie();
  }

  eintrag('Ausschneiden', B.ausschneiden);
  eintrag('Kopieren', B.kopieren);
  eintrag('Einfügen', B.einfuegen);
  trennlinie();
  eintrag('Rechtschreibung und Grammatik', B.rechtschreibpruefung);

  kasten.style.left = Math.min(e.clientX, window.innerWidth - 250) + 'px';
  kasten.style.top = Math.min(e.clientY, window.innerHeight - 260) + 'px';
  document.body.appendChild(kasten);
  rechtsMenue = kasten;

  setTimeout(() => {
    document.addEventListener('mousedown', function zu(ev) {
      if (!kasten.contains(ev.target)) { rechtsMenueSchliessen(); document.removeEventListener('mousedown', zu); }
    });
  }, 0);
}

function meldeFunde(zeichenZahl) {
  const zahl = funde.length;
  const wort = zahl === 1 ? '1 Fund' : zahl + ' Funde';
  $('status-pruefung').textContent = zeichenZahl + ' Zeichen geprüft, ' + wort + '.';
  $('status-pruefung').classList.toggle('statuszeile__fund', zahl > 0);
}

function pruefen() {
  if (pruefungLaeuft) return;
  pruefungLaeuft = true;
  const text = Dokument.lies().text;
  vorschlaege = [];
  markenEntfernen();
  funde = Pruefung.findeProbleme(Dokument.lies().text);
  zeichneFunde();
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
  menueBauen();
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

  funde = [];
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
      empfaengerBauen();
    });
    kasten.appendChild(marke);
  }
}

/* ============================================================
   7. Statuszeile, Titel, Sicherheitsnetz
   ============================================================ */

function titelSetzen() {
  document.title = dateiname + (geaendert ? ' *' : '') + ' — Schreibhilfe';
  Speicher.schreib('dateiname', dateiname);
}

function zahlenAuffrischen() {
  const { zeichen: z, woerter } = Dokument.zaehle();
  $('status-zahl').textContent = woerter + (woerter === 1 ? ' Wort, ' : ' Wörter, ')
                               + z + (z === 1 ? ' Zeichen' : ' Zeichen');
  /* Wie viele Seiten das sind: die Texthöhe geteilt durch das, was auf eine
     A4-Seite passt (29,7 cm minus 2 cm Rand oben und unten). */
  const proSeite = 25.7 * CM;
  const seiten = Math.max(1, Math.ceil(feld.scrollHeight / proSeite));
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
}

function darfVerwerfen() {
  if (!geaendert) return true;
  return confirm('Das Dokument ist nicht gespeichert. Trotzdem weitermachen?');
}

window.addEventListener('beforeunload', (e) => {
  if (!geaendert) return;
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
  if (e.key === 'F4') { e.preventDefault(); B.vorlesen(); return; }
  if (e.key === 'F7') { e.preventDefault(); pruefen(); return; }
  /* Strg und eine Ziffer nimmt einen Vorschlag der Wortvorhersage — so
     bleibt die Hand auf der Tastatur. */
  if ((e.ctrlKey || e.metaKey) && vorhersageKasten && /^[1-6]$/.test(e.key)) {
    const knopf = vorhersageKasten.querySelectorAll('.vorhersage__wort')[+e.key - 1];
    if (knopf) { e.preventDefault(); knopf.click(); return; }
  }
  if (e.key === 'Escape' && vorhersageKasten) { vorhersageWeg(); return; }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 's') {
    e.preventDefault(); B.speichernUnter(); return;
  }
  if (e.key === 'F8') { e.preventDefault(); kiKorrigieren(); return; }
  if (e.key === 'F9') { e.preventDefault(); Einstellungen.oeffnen(); return; }
  if (e.key === 'F5') { e.preventDefault(); B.tafelZeigen(); return; }
  if (e.key === 'Escape' && lesemodus) { B.lesemodus(); return; }
  if (e.key === 'Escape' && Einstellungen.offen()) { Einstellungen.schliessen(); return; }
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
feld.addEventListener('blur', () => setTimeout(vorhersageWeg, 200));
document.addEventListener('selectionchange', () => { if (vorhersageKasten) vorhersageWeg(); });

feld.addEventListener('contextmenu', rechtsMenueZeigen);
feld.addEventListener('beforeinput', verfolgenAbfangen);
feld.addEventListener('input', geaendertMelden);
/* Die AutoKorrektur greift, wenn ein Wort abgeschlossen ist — nicht
   mitten hinein. */
feld.addEventListener('keyup', (e) => {
  if (e.key === ' ' || e.key === 'Enter' || '.,;:!?"\''.includes(e.key)) autokorrekturLaufen();
});
document.addEventListener('dokument:geaendert', geaendertMelden);
document.addEventListener('selectionchange', werkzeugeAuffrischen);
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

$('btn-ki').addEventListener('click', () => kiKorrigieren());
$('btn-vorschlaege').addEventListener('click', () => kiVorschlaege());
$('btn-uebersetzen').addEventListener('click', () => kiUebersetzen());

/* Die Einstellungsseite verstellt Schriftgröße, Helligkeit und die vier
   Ecken nicht selbst — sie ruft die Griffe hier. Sonst gäbe es zwei Stellen,
   die dasselbe tun, und irgendwann widersprächen sie sich. */
Einstellungen.verbinde({
  zoom: () => zoom,
  zoomSetzen: setzeZoom,
  thema: () => thema,
  themaWeiter: () => setzeThema(THEMEN[(THEMEN.indexOf(thema) + 1) % THEMEN.length])(),
  marken: () => marken,
  markenSetzen: (an) => { if (an !== marken) B.markenZeigen(); },
  neuZeichnen: kiKnoepfeAuffrischen,

  /* Die Optionenseite füllt jetzt auch Listen, die das Programm führt. Sie
     hier zu reichen ist richtiger, als sie ein zweites Mal zu schreiben:
     Zwei Listen derselben Sache laufen irgendwann auseinander. */
  /* „alleSchriften" trägt die des Rechners, sobald sie da sind — SCHRIFTEN
     ist nur die kurze Startliste, mit der das Fenster aufgeht. In den
     Optionen stünden sonst zehn statt neunhundert. */
  schriften: () => (alleSchriften && alleSchriften.length ? alleSchriften : SCHRIFTEN),
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
    feld.blur(); feld.focus();
  },
});

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
empfaengerBauen();
kiKnoepfeAuffrischen();
ansichtAnwenden();
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
wasserzeichenAnwenden();
seitenrahmenAnwenden();
markupAnwenden();
netzAnwenden();
feld.lang = Speicher.lies('pruefsprache', 'de');
feld.classList.toggle('dokument--verfolgt', verfolgenAn);
schriftenNachtragen();
setzeZoom(zoom);
titelSetzen();
zahlenAuffrischen();
werkzeugeAuffrischen();

/* Ganz zuletzt: Beide brauchen SYMBOLE und symbol(), und die stehen weiter
   unten in der Datei. Weiter oben aufgerufen liefe das Register ins Leere. */
menueleisteAnwenden();
bedienungAnwenden();
flaecheAnwenden();


})();
