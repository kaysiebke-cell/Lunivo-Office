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
