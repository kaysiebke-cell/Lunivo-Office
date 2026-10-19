/* ==========================================================================
   Textbausteine

   382 Zeilen, die zusammengehoeren: die mitgelieferten Bausteine aus
   LibreOffice, die eigenen aus einer Markierung, die Luecken zum Ausfuellen
   und der kurze Weg ueber Kuerzel und F3.

   WAS „umg" IST

   Diese Datei kennt das Programm nicht. Was sie von dort braucht, sind acht
   Namen, und sie stehen in programm.js an einer Stelle beisammen. Die
   meisten sind Funktionen, weil es sie dort erst weiter unten gibt als
   diese Datei — „melde" und „auswahlMerken" etwa stehen tausende Zeilen
   spaeter. „gemerkteAuswahl" ist eine Abfrage und kein Wert: Was markiert
   war, aendert sich zwischen dem Bauen und dem Klick.
   ========================================================================== */
'use strict';

function BAUSTEINE_BAUEN(B, umg) {

const { Speicher, feld } = umg;
const fenster        = (...a) => umg.fenster(...a);
const melde          = (...a) => umg.melde(...a);
const alsSicher      = (s)    => umg.alsSicher(s);
const auswahlMerken  = ()     => umg.auswahlMerken();
const auswahlZurueck = ()     => umg.auswahlZurueck();

/* ============================================================
   Textbausteine

   LibreOffice bringt fertige Absätze mit — Kündigung, Anfrage, „Sehr
   geehrte Damen und Herren". Sie liegen in .bau-Dateien auf der Platte;
   start.py macht sie auf und reicht sie unter „bausteine.json" herein.

   Der Gewinn ist nicht die Sammlung, es sind die PLATZHALTER darin:

     hiermit kündige ich «Abonnement o.ä.» zum nächstmöglichen Termin.

   Ein benanntes Feld mitten im Satz, das sagt, was dort hingehört. Wer vor
   einem leeren Blatt sitzt, muss den Satz nicht erfinden — er muss eine
   Lücke füllen, und die Lücke sagt ihm, womit. Genau das ist der
   Unterschied, der jemandem hilft, dem das Schreiben schwerfällt.

   Deshalb ist der Platzhalter hier kein Text, sondern ein Stück mit
   Auszeichnung: Ein Klick nimmt ihn ganz, Tab springt zum nächsten, und was
   man tippt, ersetzt ihn im Ganzen statt sich dazwischenzuschieben.
   ============================================================ */
let bausteine = null;          // null = noch nicht geholt, [] = keine da
let bausteinGewaehlt = null;

/* ---- Die eigenen ----
   Die mitgelieferten Bausteine stammen aus LibreOffice und sind aus
   Firmensicht geschrieben — Angebot, Bestellung, Mahnung. Wer an sein Amt
   oder seine Versicherung schreibt, braucht andere, und die kennt nur er
   selbst.

   Sie liegen im Speicher des Programms und nicht in der .bau-Datei von
   LibreOffice. Das ist Absicht: In dessen Profil zu schreiben hieße, an
   einem fremden Programm zu hantieren, das nebenher läuft — und wenn dabei
   etwas schiefgeht, ist nicht ein Baustein weg, sondern seine Einstellungen.
   Der Preis ist, dass die eigenen Bausteine in LibreOffice nicht auftauchen. */
let eigeneBausteine = Speicher.lies('bausteine', []);

const EIGENE_GRUPPE = 'Meine Bausteine';

async function bausteineHolen() {
  if (!bausteine) {
    try {
      const antwort = await fetch('bausteine.json');
      bausteine = antwort.ok ? await antwort.json() : [];
    } catch (e) {
      /* Im Browser statt im eigenen Fenster gibt es den Server nicht. Dann
         bleibt die Liste leer — kein Fehler, nur nichts anzubieten. */
      bausteine = [];
    }
  }
  /* Die eigenen ganz oben: Wer sich einen angelegt hat, sucht ihn zuerst. */
  return (eigeneBausteine.length
    ? [{ gruppe: EIGENE_GRUPPE, eigen: true, bausteine: eigeneBausteine }]
    : []).concat(bausteine);
}

/* ---- Aus einer Markierung einen Baustein ----
   Genommen wird der Text, nicht die Auszeichnung: Fett und Schriftgröße
   gehören dem Dokument, aus dem er stammt, und säßen im nächsten schief.

   Die spitzen Anführungszeichen sind die Lücken. Das ist kein Zufall,
   sondern dieselbe Schreibweise, in der das Programm sie anzeigt: Was man
   als «Betrag» in den Text schreibt, ist beim nächsten Einsetzen eine
   Lücke. Und ein Baustein, der aus einem eingesetzten Baustein entsteht,
   behält dessen Lücken von selbst. */
function bausteinAusText(text) {
  return text.split(/\r?\n/).map((zeile) => {
    const teile = [];
    let rest = 0;
    for (const treffer of zeile.matchAll(/«([^»]*)»/g)) {
      if (treffer.index > rest) teile.push({ text: zeile.slice(rest, treffer.index) });
      teile.push({ platz: treffer[1] });
      rest = treffer.index + treffer[0].length;
    }
    if (rest < zeile.length) teile.push({ text: zeile.slice(rest) });
    return teile;
  });
}

/* Der Text einer Markierung mit Absatzgrenzen. „bereich.toString()" kennt
   die nicht — aus zwei Absätzen wird dort eine Zeile, und der Baustein
   klebt später zusammen. „innerText" kennt sie, verlangt dafür aber, dass
   das Stück im Dokument hängt; darum der kurze Umweg über eine Hilfe, die
   niemand sieht. */
function auswahlAlsText(bereich) {
  if (!bereich) return '';
  const hilfe = document.createElement('div');
  hilfe.appendChild(bereich.cloneContents());
  hilfe.style.cssText = 'position:fixed;left:-9999px;top:0;white-space:pre-wrap';
  document.body.appendChild(hilfe);
  const text = hilfe.innerText;
  hilfe.remove();
  return text.replace(/\u00a0/g, ' ').replace(/\n{3,}/g, '\n\n').trim();
}

function eigeneSichern() {
  Speicher.schreib('bausteine', eigeneBausteine);
}

/* Aus den Teilen eines Bausteins das Stück Dokument. Der Platzhalter wird
   ein <span>, und zwar mit „contenteditable=false" nicht: Er soll ja
   überschrieben werden. Die Auszeichnung genügt. */
function bausteinAlsHtml(absaetze) {
  const sicher = (t) => alsSicher(t);
  return absaetze.map((teile) => {
    const inhalt = teile.map((teil) => (teil.platz !== undefined
      ? '<span class="platzhalter">«' + sicher(teil.platz) + '»</span>'
      : sicher(teil.text || ''))).join('');
    return '<p>' + (inhalt || '<br>') + '</p>';
  }).join('');
}

/* Der erste Platzhalter wird gleich genommen — man soll tippen können, ohne
   vorher zu zielen. */
function platzhalterNehmen(welcher) {
  if (!welcher) return false;
  const bereich = document.createRange();
  bereich.selectNodeContents(welcher);
  feld.focus();
  Dokument.waehle(bereich);
  welcher.scrollIntoView({ block: 'nearest' });
  return true;
}

/** Zum nächsten Platzhalter nach der Schreibstelle — oder zum ersten. */
function platzhalterWeiter(rueckwaerts = false) {
  const alle = [...feld.querySelectorAll('.platzhalter')];
  if (!alle.length) return false;

  const auswahl = window.getSelection();
  let jetzt = -1;
  if (auswahl.rangeCount) {
    let knoten = auswahl.anchorNode;
    while (knoten && knoten !== feld && !(knoten.classList && knoten.classList.contains('platzhalter'))) {
      knoten = knoten.parentNode;
    }
    jetzt = alle.indexOf(knoten);
  }
  const naechster = rueckwaerts
    ? alle[(jetzt <= 0 ? alle.length : jetzt) - 1]
    : alle[(jetzt + 1) % alle.length];
  return platzhalterNehmen(naechster);
}

function bausteinEinfuegen(baustein) {
  if (!baustein) return;
  Dokument.einfuegen(bausteinAlsHtml(baustein.absaetze));
  /* Nach dem Einsetzen gleich in die erste Lücke. */
  setTimeout(() => {
    const erster = feld.querySelector('.platzhalter');
    if (erster) {
      platzhalterNehmen(erster);
      melde('Eingesetzt. Tab springt zur nächsten Lücke, Tippen ersetzt sie.');
    } else {
      melde('„' + baustein.name + '" eingesetzt.');
    }
  }, 0);
}

/* ---- Das Fenster ----
   Zwei Spalten wie in LibreOffice: links die Liste, rechts der Text, den man
   bekommt. Ohne die Vorschau wählt man nach dem Namen — und „Anlage" oder
   „Zahlungsbedingung" sagt einem nichts, bevor man es einmal eingesetzt
   hat. */
B.textbausteine = async () => {
  auswahlMerken();
  const gruppen = await bausteineHolen();

  const grund = document.createElement('div');
  grund.className = 'dialoggrund';
  const kasten = document.createElement('div');
  kasten.className = 'dialog dialog--breit baustein';
  kasten.innerHTML =
    '<h3 class="dialog__titel">Textbausteine</h3>'
    + '<div class="baustein__kopf">'
    + '<span>Name:</span><input class="baustein__name" readonly>'
    + '<span>Kürzel:</span><input class="baustein__kurz" readonly>'
    + '</div>'
    + '<div class="baustein__mitte">'
    + '<div class="baustein__liste" tabindex="0"></div>'
    + '<div class="baustein__vorschau"></div>'
    + '</div>'
    + '<p class="baustein__fuss">Eigene kommen aus dem Markierten, die '
    + 'übrigen aus LibreOffice. '
    + '«So gesetzte Stellen» sind Lücken: Tab springt von einer zur nächsten, '
    + 'Tippen ersetzt sie.</p>';

  const liste = kasten.querySelector('.baustein__liste');
  const vorschau = kasten.querySelector('.baustein__vorschau');
  const nameFeld = kasten.querySelector('.baustein__name');
  const kurzFeld = kasten.querySelector('.baustein__kurz');

  /* „Löschen" gilt nur für die eigenen. Die mitgelieferten liegen in einer
     Datei von LibreOffice; die zu ändern steht diesem Programm nicht zu.
     Der Knopf entsteht weiter unten, die Liste braucht ihn aber schon —
     darum vorerst ein Handgriff, der nichts tut. */
  let loeschbar = () => {};

  const zeigen = (baustein, knopf, eigen) => {
    bausteinGewaehlt = baustein;
    loeschbar(!!eigen);
    nameFeld.value = baustein ? baustein.name : '';
    kurzFeld.value = baustein ? (baustein.kurz || '') : '';
    vorschau.innerHTML = baustein ? bausteinAlsHtml(baustein.absaetze) : '';
    for (const anderer of liste.querySelectorAll('.baustein__eintrag--an')) {
      anderer.classList.remove('baustein__eintrag--an');
    }
    if (knopf) {
      knopf.classList.add('baustein__eintrag--an');
      /* Sonst steht die gewählte Zeile außerhalb des Bildes und das Fenster
         sieht aus, als hätte es sich nichts gemerkt. */
      knopf.scrollIntoView({ block: 'nearest' });
    }
  };

  /* Die Liste wird neu gebaut, sooft sich die eigenen Bausteine ändern —
     angelegt, gelöscht. Ohne das müsste man das Fenster zumachen und wieder
     aufmachen, um zu sehen, dass etwas angekommen ist. */
  const listeFuellen = async (auswaehlen) => {
    const alle = await bausteineHolen();
    liste.innerHTML = '';
    if (!alle.length) {
      liste.innerHTML = '<p class="baustein__leer">Noch keine Bausteine. '
        + 'Markiere im Text, was du behalten willst, und drücke unten auf '
        + '„Aus Markierung".<br><br>Die mitgelieferten gehören zu LibreOffice — '
        + 'fehlen sie, bringt sie „sudo apt install libreoffice-writer" mit.</p>';
    }
    let ersterKnopf = null;
    let zuWaehlen = null;
    for (const gruppe of alle) {
      const titel = document.createElement('div');
      titel.className = 'baustein__gruppe';
      titel.textContent = gruppe.gruppe;
      liste.appendChild(titel);
      for (const baustein of gruppe.bausteine) {
        const knopf = document.createElement('button');
        knopf.type = 'button';
        knopf.className = 'baustein__eintrag';
        knopf.textContent = baustein.name;
        knopf.addEventListener('click', () => zeigen(baustein, knopf, !!gruppe.eigen));
        knopf.addEventListener('dblclick', () => { zu(); bausteinEinfuegen(baustein); });
        liste.appendChild(knopf);
        if (!ersterKnopf) ersterKnopf = knopf;
        if (auswaehlen && baustein.name === auswaehlen) zuWaehlen = knopf;
      }
    }
    const nehmen = zuWaehlen || ersterKnopf;
    if (nehmen) nehmen.click();
    else zeigen(null, null, false);
  };

  const knoepfe = document.createElement('div');
  knoepfe.className = 'dialog__knoepfe dialog__knoepfe--zweiseitig';

  /* Links das Anlegen und Wegnehmen, rechts das Verlassen und Einsetzen —
     wie im Fenster von LibreOffice. Was den Bestand ändert, steht nicht
     neben dem Knopf, den man am häufigsten drückt. */
  const links = document.createElement('div');
  links.className = 'dialog__knoepfe-links';
  const neu = document.createElement('button');
  neu.className = 'knopf'; neu.textContent = 'Aus Markierung…';
  neu.title = 'Das im Text Markierte als eigenen Baustein behalten';
  const weg = document.createElement('button');
  weg.className = 'knopf'; weg.textContent = 'Löschen';
  weg.disabled = true;
  links.append(neu, weg);

  const ab = document.createElement('button');
  ab.className = 'knopf'; ab.textContent = 'Schließen';
  const ok = document.createElement('button');
  ok.className = 'knopf knopf--haupt'; ok.textContent = 'Einfügen';
  const rechts = document.createElement('div');
  rechts.className = 'dialog__knoepfe-rechts';
  rechts.append(ab, ok);

  knoepfe.append(links, rechts);
  kasten.appendChild(knoepfe);
  grund.appendChild(kasten);
  document.body.appendChild(grund);

  loeschbar = (eigen) => { weg.disabled = !eigen; };
  loeschbar(bausteinGewaehlt && eigeneBausteine.includes(bausteinGewaehlt));

  const zu = () => { grund.remove(); auswahlZurueck(); };
  ab.addEventListener('click', zu);
  grund.addEventListener('mousedown', (e) => { if (e.target === grund) zu(); });
  ok.addEventListener('click', () => {
    if (!bausteinGewaehlt) { melde('Erst einen Baustein in der Liste wählen.'); return; }
    const gewaehlt = bausteinGewaehlt;
    zu();
    bausteinEinfuegen(gewaehlt);
  });

  neu.addEventListener('click', () => {
    const text = auswahlAlsText(umg.gemerkteAuswahl());
    if (!text.trim()) {
      melde('Erst im Text markieren, was der Baustein enthalten soll — dann hierher.');
      return;
    }
    bausteinAnlegen(text, (angelegt) => listeFuellen(angelegt.name));
  });

  weg.addEventListener('click', () => {
    const gewaehlt = bausteinGewaehlt;
    if (!gewaehlt || !eigeneBausteine.includes(gewaehlt)) return;
    eigeneBausteine = eigeneBausteine.filter((b) => b !== gewaehlt);
    eigeneSichern();
    listeFuellen();
    melde('„' + gewaehlt.name + '" gelöscht.');
  });

  document.addEventListener('keydown', function flucht(e) {
    if (!document.body.contains(grund)) { document.removeEventListener('keydown', flucht); return; }
    if (e.key === 'Escape') { e.preventDefault(); zu(); }
  });

  listeFuellen();
};

/* Name und Kürzel erfragen und den Baustein behalten. Das Kürzel wird
   vorgeschlagen — es ist der schnelle Weg (tippen und F3), aber niemand
   denkt sich beim Anlegen eines aus. */
function bausteinAnlegen(text, danach) {
  const erstesWort = (text.trim().split(/\s+/)[0] || 'Baustein').replace(/[^\wÄÖÜäöüß]/g, '');
  const vorschlag = erstesWort.slice(0, 4).toUpperCase() || 'BST';

  fenster('Baustein behalten', [
    { art: 'satz', text: 'Aus dem Markierten wird ein Baustein. Schreib «so etwas» '
                       + 'hinein, wo später eine Lücke zum Ausfüllen sein soll.' },
    { schluessel: 'name', name: 'Name', art: 'text', wert: '' },
    { schluessel: 'kurz', name: 'Kürzel', art: 'text', wert: vorschlag },
  ], (werte) => {
    const name = (werte.name || '').trim();
    if (!name) { melde('Ohne Namen findet man ihn nicht wieder — nichts behalten.'); return; }
    const kurz = (werte.kurz || '').trim();

    /* Gleicher Name heißt ersetzen, nicht danebenlegen: Wer denselben
       Baustein noch einmal anlegt, hat ihn verbessert. */
    eigeneBausteine = eigeneBausteine.filter((b) => b.name !== name);
    const angelegt = { name, kurz, absaetze: bausteinAusText(text) };
    eigeneBausteine.push(angelegt);
    eigeneBausteine.sort((a, b) => a.name.localeCompare(b.name, 'de'));
    eigeneSichern();
    melde('„' + name + '" behalten' + (kurz ? ' — ' + kurz + ' und F3 setzt ihn ein.' : '.'));
    if (danach) danach(angelegt);
  }, 'Behalten');
}

/* ---- Der kurze Weg: Kürzel tippen, F3 drücken ----
   Wie in LibreOffice. Wer „KÜ" schreibt und F3 drückt, hat die Kündigung
   stehen. Für die tägliche Arbeit ist das der Weg; das Fenster ist zum
   Suchen da, nicht zum Einsetzen. */
async function bausteinUeberKuerzel() {
  const auswahl = window.getSelection();
  if (!auswahl.rangeCount || !auswahl.isCollapsed) return false;
  const knoten = auswahl.anchorNode;
  if (!knoten || knoten.nodeType !== Node.TEXT_NODE || !feld.contains(knoten)) return false;

  const bis = auswahl.anchorOffset;
  const text = knoten.data;
  let von = bis;
  while (von > 0 && /[\wÄÖÜäöüß]/.test(text[von - 1])) von--;
  const kuerzel = text.slice(von, bis);
  if (!kuerzel) return false;

  const gruppen = await bausteineHolen();
  let treffer = null;
  for (const gruppe of gruppen) {
    for (const baustein of gruppe.bausteine) {
      if ((baustein.kurz || '').toLowerCase() === kuerzel.toLowerCase()) treffer = baustein;
    }
  }
  if (!treffer) return false;

  const bereich = document.createRange();
  bereich.setStart(knoten, von);
  bereich.setEnd(knoten, bis);
  feld.focus();
  Dokument.waehle(bereich);
  bausteinEinfuegen(treffer);
  return true;
}

/* Was das uebrige Programm von hier braucht: F3 setzt ueber das Kuerzel
   ein, Tab springt von Luecke zu Luecke, und nach dem Einsetzen einer
   Vorlage wird die erste Luecke genommen. */
return { bausteinUeberKuerzel, platzhalterNehmen, platzhalterWeiter };
}
