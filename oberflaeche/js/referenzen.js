/* ==========================================================================
   Referenzen: Fussnoten, Zitate, Verzeichnisse

   542 Zeilen aus zwei Stuecken von programm.js, die dasselbe meinen: alles,
   womit ein Text auf etwas anderes verweist. Fussnoten und Endnoten,
   Beschriftungen und das Abbildungsverzeichnis, Textmarken und
   Querverweise, das Stichwortverzeichnis, Quellen und das
   Literaturverzeichnis, das Inhaltsverzeichnis.

   Sie standen an zwei Stellen, weil sie in Word an zwei Stellen stehen --
   im Reiter „Referenzen" und noch einmal nachgereicht. In einer Datei ist
   das eine Sache.

   WAS „umg" IST

   Zehn Namen. Die meisten als Funktion, weil es sie in programm.js erst
   weiter unten gibt: „melde" bei 7.824, „auswahlMerken" bei 7.345,
   „geaendertMelden" bei 8.312.

   Beim Messen sah es nach zwoelf aus. „marken" und „auswahl" waren keine:
   Beides sind hier viermal eigene lokale Namen — die Liste der Fussnoten,
   der Endnoten, der Indexmarken, der Textmarken, und einmal
   window.getSelection(). Sechste und siebte Falle dieser Art.
   ========================================================================== */
'use strict';

function REFERENZEN_BAUEN(B, umg) {

const { Speicher, feld } = umg;
const fenster          = (...a) => umg.fenster(...a);
const melde            = (...a) => umg.melde(...a);
const alsSicher        = (s)    => umg.alsSicher(s);
const auswahlMerken    = ()     => umg.auswahlMerken();
const auswahlZurueck   = ()     => umg.auswahlZurueck();
const elementEinfuegen = (...a) => umg.elementEinfuegen(...a);
const geaendertMelden  = ()     => umg.geaendertMelden();

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
/* ============================================================
   TEXTMARKE

   Nach seinem Bild des WPS-Fensters:

       Textmarkenname:  [____________________]
       [ Liste der vorhandenen Marken       ]
       Sortieren nach: (•) Namen  ( ) Speicherort
       [ ] Ausgeblendete Textmarken
       Hinzufügen   Löschen   Gehe zu        Abbrechen

   Vorher war es ein Feld mit einem Namen darin. Man konnte eine Marke
   setzen und danach nie wieder sehen, welche es gibt, keine loeschen und
   zu keiner springen. Er hat geschrieben: „ist ohne sichtbare Funktion?"
   — mit Fragezeichen, weil man von aussen nicht erkennen konnte, ob
   ueberhaupt etwas passiert ist.

   Die drei Knoepfe sind grau, solange nichts gewaehlt ist. Das ist keine
   Zier: „Gehe zu" ohne Ziel waere ein Klick ins Leere.
   ============================================================ */
B.textmarke = () => {
  auswahlMerken();

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog markenfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Textmarke</h3>';

  const zeileName = document.createElement('label');
  zeileName.className = 'dialog__zeile';
  zeileName.innerHTML = '<span>Textmarkenname:</span>';
  const eingabe = document.createElement('input');
  eingabe.type = 'text';
  zeileName.appendChild(eingabe);
  kasten.appendChild(zeileName);

  const liste = document.createElement('div');
  liste.className = 'markenliste';
  liste.setAttribute('role', 'listbox');
  kasten.appendChild(liste);

  const sortierzeile = document.createElement('div');
  sortierzeile.className = 'markenfenster__zeile';
  sortierzeile.innerHTML = '<span>Sortieren nach:</span>';
  let sortierung = 'name';
  for (const [wert, name] of [['name', 'Namen'], ['stelle', 'Speicherort']]) {
    const w = document.createElement('label');
    w.className = 'markenfenster__wahl';
    const r = document.createElement('input');
    r.type = 'radio'; r.name = 'markensortierung'; r.value = wert;
    if (wert === sortierung) r.checked = true;
    r.addEventListener('change', () => { sortierung = wert; auffrischen(); });
    w.appendChild(r);
    w.appendChild(document.createTextNode(' ' + name));
    sortierzeile.appendChild(w);
  }
  kasten.appendChild(sortierzeile);

  let auchVersteckte = false;
  const versteckt = document.createElement('label');
  versteckt.className = 'markenfenster__wahl';
  const haken = document.createElement('input');
  haken.type = 'checkbox';
  haken.addEventListener('change', () => { auchVersteckte = haken.checked; auffrischen(); });
  versteckt.appendChild(haken);
  versteckt.appendChild(document.createTextNode(' Ausgeblendete Textmarken'));
  kasten.appendChild(versteckt);

  let gewaehlt = null;

  const marken = () => {
    const alle = [...feld.querySelectorAll('.textmarke')].map((el, i) => ({
      el,
      name: decodeURIComponent(el.id.replace(/^marke-/, '')),
      stelle: i,
      leise: el.dataset.leise === 'ja',
    }));
    const sichtbar = auchVersteckte ? alle : alle.filter((m) => !m.leise);
    return sortierung === 'name'
      ? sichtbar.sort((a, b) => a.name.localeCompare(b.name, 'de'))
      : sichtbar;
  };

  const knoepfe = {};
  function auffrischen() {
    liste.textContent = '';
    const alle = marken();
    if (!alle.length) {
      const leer = document.createElement('p');
      leer.className = 'markenliste__leer';
      leer.textContent = 'Noch keine Textmarke im Dokument.';
      liste.appendChild(leer);
    }
    for (const m of alle) {
      const z = document.createElement('button');
      z.type = 'button';
      z.className = 'markenliste__zeile'
        + (gewaehlt === m.name ? ' markenliste__zeile--an' : '');
      z.textContent = m.name;
      z.addEventListener('click', () => {
        gewaehlt = m.name;
        eingabe.value = m.name;
        auffrischen();
      });
      liste.appendChild(z);
    }
    const name = eingabe.value.trim();
    const gibtsSchon = alle.some((m) => m.name === name);
    knoepfe.hinzu.disabled = !name || gibtsSchon;
    knoepfe.weg.disabled = !gibtsSchon;
    knoepfe.hin.disabled = !gibtsSchon;
  }

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe';

  const machKnopf = (name, tun, haupt) => {
    const k = document.createElement('button');
    k.type = 'button';
    k.className = haupt ? 'knopf knopf--haupt' : 'knopf';
    k.textContent = name;
    k.addEventListener('click', tun);
    fuss.appendChild(k);
    return k;
  };

  knoepfe.hinzu = machKnopf('Hinzufügen', () => {
    const name = eingabe.value.trim().replace(/[^A-Za-zÄÖÜäöüß0-9 _-]/g, '');
    if (!name) return;
    auswahlZurueck();
    elementEinfuegen('<span class="textmarke" id="marke-'
      + encodeURIComponent(name) + '" title="Textmarke: ' + alsSicher(name) + '"></span>');
    gewaehlt = name;
    melde('Textmarke „' + name + '" gesetzt.');
    auffrischen();
  }, true);

  knoepfe.weg = machKnopf('Löschen', () => {
    const m = marken().find((x) => x.name === eingabe.value.trim());
    if (!m) return;
    m.el.remove();
    gewaehlt = null;
    eingabe.value = '';
    geaendertMelden();
    melde('Textmarke gelöscht.');
    auffrischen();
  });

  knoepfe.hin = machKnopf('Gehe zu', () => {
    const m = marken().find((x) => x.name === eingabe.value.trim());
    if (!m) return;
    grund.remove();
    m.el.scrollIntoView({ block: 'center' });
    const r = document.createRange();
    r.selectNode(m.el);
    r.collapse(false);
    const auswahl = window.getSelection();
    auswahl.removeAllRanges();
    auswahl.addRange(r);
    feld.focus();
    melde('Bei „' + m.name + '".');
  });

  machKnopf('Abbrechen', () => grund.remove());

  eingabe.addEventListener('input', auffrischen);
  eingabe.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !knoepfe.hinzu.disabled) { e.preventDefault(); knoepfe.hinzu.click(); }
  });

  kasten.appendChild(fuss);
  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
  auffrischen();
  eingabe.focus();
};

/* ---- Querverweis ----

   NACH SEINEM BILD (doku/pruefkatalog/bilder/einf-gen-querverweis/1.jpg).
   Was darauf steht, Punkt fuer Punkt:

     Querverweis
     Verweistyp: [Nummeriertes Element v]   Verweisen auf: [Seitenzahl v]
     [x] Als Hyperlink einfuegen   [ ] Oben/unten einschliessen (O)
     Fuer welches nummerierte Element:
     [ ................. grosse Liste ................. ]
                                     [Abbrechen] [Einfuegen]

   Vorher war es ein Feld mit einer Klappliste: „Verweis auf" und darin
   Textmarken und Ueberschriften gemischt. Man konnte weder waehlen,
   WORAUF verwiesen wird (Seitenzahl oder Text), noch sehen, was es
   ueberhaupt gibt. */

/* Die Arten, auf die man verweisen kann, und was von ihnen einsetzbar
   ist. Die Beschriftung ueber der Liste wechselt mit der Art — in WPS
   steht dort „Fuer welches nummerierte Element", „Fuer welche
   Ueberschrift", „Fuer welche Textmarke". */
const VERWEISARTEN = [
  { kuerzel: 'nummer',  name: 'Nummeriertes Element', frage: 'Für welches nummerierte Element:' },
  { kuerzel: 'ueber',   name: 'Überschrift',          frage: 'Für welche Überschrift:' },
  { kuerzel: 'marke',   name: 'Textmarke',            frage: 'Für welche Textmarke:' },
  { kuerzel: 'fussnote', name: 'Fußnote',             frage: 'Für welche Fußnote:' },
  { kuerzel: 'bild',    name: 'Abbildung',            frage: 'Für welche Abbildung:' },
  { kuerzel: 'tabelle', name: 'Tabelle',              frage: 'Für welche Tabelle:' },
];

/* „Verweisen auf" haengt von der Art ab: Bei einer Ueberschrift kann man
   den Text nehmen, bei einer Fussnote ihre Nummer. */
const VERWEISZIELE = {
  nummer:  [['seite', 'Seitenzahl'], ['nummer', 'Absatznummer'], ['text', 'Absatztext']],
  ueber:   [['text', 'Überschriftentext'], ['seite', 'Seitenzahl'], ['nummer', 'Absatznummer']],
  marke:   [['text', 'Textmarkentext'], ['seite', 'Seitenzahl']],
  fussnote: [['nummer', 'Fußnotennummer'], ['seite', 'Seitenzahl']],
  bild:    [['text', 'Gesamte Beschriftung'], ['nummer', 'Nur Nummer'], ['seite', 'Seitenzahl']],
  tabelle: [['text', 'Gesamte Beschriftung'], ['nummer', 'Nur Nummer'], ['seite', 'Seitenzahl']],
};

/* Was es im Dokument gibt. Jede Art holt ihre eigenen Ziele; steht nichts
   da, bleibt die Liste leer und „Einfuegen" grau — das ist ehrlicher, als
   die Arten zu verstecken, die gerade nichts finden. */
function verweiszieleSammeln(art) {
  const raus = [];
  if (art === 'ueber' || art === 'nummer') {
    for (const u of ueberschriftenSammeln()) {
      if (art === 'nummer' && !/^\s*[\d.]+\s/.test(u.text)) continue;
      raus.push({ kennung: u.kennung, text: u.text });
    }
  }
  if (art === 'nummer') {
    let zahl = 0;
    for (const li of feld.querySelectorAll('ol > li')) {
      zahl += 1;
      const text = li.textContent.trim();
      if (!text) continue;
      if (!li.id) li.id = 'liste-' + zahl + '-' + Math.random().toString(36).slice(2, 7);
      raus.push({ kennung: li.id, text: zahl + '. ' + text.slice(0, 70), nummer: String(zahl) });
    }
  }
  if (art === 'marke') {
    for (const el of feld.querySelectorAll('.textmarke')) {
      raus.push({ kennung: el.id, text: decodeURIComponent(el.id.replace(/^marke-/, '')) });
    }
  }
  if (art === 'fussnote') {
    let zahl = 0;
    for (const el of feld.querySelectorAll('.fussnoten li, sup.fussnote')) {
      zahl += 1;
      if (!el.id) el.id = 'fussnote-' + zahl;
      raus.push({ kennung: el.id, text: zahl + '. ' + el.textContent.trim().slice(0, 70), nummer: String(zahl) });
    }
  }
  if (art === 'bild' || art === 'tabelle') {
    const was = art === 'bild' ? 'Abbildung' : 'Tabelle';
    let zahl = 0;
    for (const el of feld.querySelectorAll('.beschriftung')) {
      const text = el.textContent.trim();
      if (!text.startsWith(was)) continue;
      zahl += 1;
      if (!el.id) el.id = art + '-' + zahl + '-' + Math.random().toString(36).slice(2, 7);
      raus.push({ kennung: el.id, text, nummer: String(zahl) });
    }
  }
  return raus;
}

B.querverweis = () => {
  auswahlMerken();

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  /* EIGENER NAME FUER DAS FENSTER. Hier stand 'querverweis' — dieselbe
     Klasse, die der eingefuegte Verweis im Text traegt. Eine Suche nach
     '.querverweis' fand danach beides, das Fenster und jeden Verweis im
     Blatt. */
  kasten.className = 'dialog dialog--breit verweisfenster';
  kasten.innerHTML = '<h3 class="dialog__titel">Querverweis</h3>';

  /* Zeile 1: Verweistyp und Verweisen auf, nebeneinander wie im Bild. */
  const zeile1 = document.createElement('div');
  zeile1.className = 'verweisfenster__zeile';

  const artFeld = document.createElement('label');
  artFeld.className = 'absatzfenster__feld';
  artFeld.innerHTML = '<span>Verweistyp:</span>';
  const artWahl = document.createElement('select');
  artWahl.className = 'feld';
  for (const a of VERWEISARTEN) {
    const o = document.createElement('option');
    o.value = a.kuerzel; o.textContent = a.name;
    artWahl.appendChild(o);
  }
  artFeld.appendChild(artWahl);

  const zielFeld = document.createElement('label');
  zielFeld.className = 'absatzfenster__feld';
  zielFeld.innerHTML = '<span>Verweisen auf:</span>';
  const zielWahl = document.createElement('select');
  zielWahl.className = 'feld';
  zielFeld.appendChild(zielWahl);

  zeile1.appendChild(artFeld);
  zeile1.appendChild(zielFeld);
  kasten.appendChild(zeile1);

  /* Zeile 2: die beiden Haken. */
  const zeile2 = document.createElement('div');
  zeile2.className = 'verweisfenster__zeile';
  const hakenBauen = (text, an) => {
    const w = document.createElement('label');
    w.className = 'absatzfenster__haken';
    const e = document.createElement('input');
    e.type = 'checkbox'; e.checked = !!an;
    w.appendChild(e);
    const t = document.createElement('span');
    t.textContent = text;
    w.appendChild(t);
    w.eingabe = e;
    return w;
  };
  const alsLink = hakenBauen('Als Hyperlink einfügen', true);
  const obenUnten = hakenBauen('Oben/unten einschließen', false);
  zeile2.appendChild(alsLink);
  zeile2.appendChild(obenUnten);
  kasten.appendChild(zeile2);

  /* Die Frage und die Liste. */
  const frage = document.createElement('div');
  frage.className = 'verweisfenster__frage';
  kasten.appendChild(frage);

  const liste = document.createElement('div');
  liste.className = 'verweisfenster__liste';
  liste.setAttribute('role', 'listbox');
  kasten.appendChild(liste);

  const fuss = document.createElement('div');
  fuss.className = 'dialog__knoepfe';
  const ab = document.createElement('button');
  ab.type = 'button'; ab.className = 'knopf'; ab.textContent = 'Abbrechen';
  const ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'knopf knopf--haupt'; ok.textContent = 'Einfügen';
  ok.disabled = true;
  fuss.appendChild(ab); fuss.appendChild(ok);
  kasten.appendChild(fuss);

  let gewaehlt = null;

  function listeFuellen() {
    const art = artWahl.value;
    const eintrag = VERWEISARTEN.find((a) => a.kuerzel === art);
    frage.textContent = eintrag ? eintrag.frage : '';

    zielWahl.innerHTML = '';
    for (const [wert, name] of (VERWEISZIELE[art] || [])) {
      const o = document.createElement('option');
      o.value = wert; o.textContent = name;
      zielWahl.appendChild(o);
    }

    liste.innerHTML = '';
    gewaehlt = null;
    ok.disabled = true;
    const ziele = verweiszieleSammeln(art);
    if (!ziele.length) {
      const leer = document.createElement('p');
      leer.className = 'verweisfenster__leer';
      leer.textContent = 'Im Dokument steht nichts von dieser Art.';
      liste.appendChild(leer);
      return;
    }
    for (const z of ziele) {
      const k = document.createElement('button');
      k.type = 'button';
      k.className = 'verweisfenster__eintrag';
      k.textContent = z.text;
      k.addEventListener('click', () => {
        gewaehlt = z;
        ok.disabled = false;
        [...liste.children].forEach((c) => c.classList.remove('verweisfenster__eintrag--an'));
        k.classList.add('verweisfenster__eintrag--an');
      });
      k.addEventListener('dblclick', () => { gewaehlt = z; ok.click(); });
      liste.appendChild(k);
    }
  }

  artWahl.addEventListener('change', listeFuellen);
  listeFuellen();

  ab.addEventListener('click', () => grund.remove());
  ok.addEventListener('click', () => {
    if (!gewaehlt) return;
    grund.remove();
    auswahlZurueck();

    /* Was eingesetzt wird, haengt an „Verweisen auf". Die Seitenzahl kann
       hier niemand ausrechnen — das Blatt entscheidet beim Umbrechen. Ein
       Feld mit der Kennung steht da, und beim Drucken traegt sie sich
       ein; bis dahin zeigt sie die Seite, auf der das Ziel gerade steht. */
    let text = gewaehlt.text;
    if (zielWahl.value === 'nummer') text = gewaehlt.nummer || '1';
    if (zielWahl.value === 'seite') {
      const ziel = document.getElementById(gewaehlt.kennung);
      text = 'Seite ' + seiteVonElement(ziel);
    }
    if (obenUnten.eingabe.checked) {
      const ziel = document.getElementById(gewaehlt.kennung);
      text += ' ' + (obenOderUnten(ziel) ? 'oben' : 'unten');
    }

    const inhalt = alsSicher(text);
    /* Ueber elementEinfuegen, nicht ueber Dokument.einfuegen: Das setzt
       execCommand('insertHTML') ein, und das machte aus dem <span> mit
       Kennung einen nackten Stil-<span> — der Verweis wusste danach nicht
       mehr, wohin er zeigt. Beim <a> fiel es nicht auf, weil ein Link
       stehen bleibt. */
    if (alsLink.eingabe.checked) {
      elementEinfuegen('<a class="querverweis" href="#' + gewaehlt.kennung
        + '" data-verweis="' + zielWahl.value + '">' + inhalt + '</a>');
    } else {
      elementEinfuegen('<span class="querverweis" data-ziel="' + gewaehlt.kennung
        + '" data-verweis="' + zielWahl.value + '">' + inhalt + '</span>');
    }
    melde('Querverweis eingefügt.');
    geaendertMelden();
  });

  grund.appendChild(kasten);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) grund.remove(); });
  document.addEventListener('keydown', function zu(e) {
    if (e.key === 'Escape' && grund.isConnected) { grund.remove(); document.removeEventListener('keydown', zu); }
  });
  document.body.appendChild(grund);
};

/* Auf welcher Seite steht das Ziel? Gerechnet wie in der Statuszeile: die
   Hoehe des Textes darueber, geteilt durch die Hoehe einer Seite. */
function seiteVonElement(el) {
  if (!el) return 1;
  const hoehe = feld.clientHeight || 1;
  const seiten = Math.max(1, Math.round(feld.scrollHeight / Math.max(1, hoehe)));
  const anteil = el.offsetTop / Math.max(1, feld.scrollHeight);
  return Math.max(1, Math.min(seiten, Math.floor(anteil * seiten) + 1));
}

/* Steht das Ziel vor oder hinter der Stelle, an der der Zeiger steht? */
function obenOderUnten(el) {
  if (!el) return true;
  const auswahl = window.getSelection();
  if (!auswahl || !auswahl.rangeCount) return true;
  const hier = auswahl.getRangeAt(0).startContainer;
  const knoten = hier && hier.nodeType === Node.TEXT_NODE ? hier.parentElement : hier;
  if (!knoten) return true;
  return !!(el.compareDocumentPosition(knoten) & Node.DOCUMENT_POSITION_FOLLOWING);
}

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

/* Der Navigationsbereich braucht die Ueberschriften — dieselbe Sammlung,
   aus der auch das Inhaltsverzeichnis entsteht. */
return { ueberschriftenSammeln };
}
