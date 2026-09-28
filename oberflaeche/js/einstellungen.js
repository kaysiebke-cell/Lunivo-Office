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

/* Ein fehlendes Element hat einmal die ganze Seite lahmgelegt: Ein
   addEventListener auf null wirft, verdrahten() bricht ab, und ab da war
   kein einziger Knopf mehr angeschlossen — auch die neunzig anderen
   nicht. Passiert war es beim Umbau, als ein Knopf wegfiel und seine
   Zeile stehenblieb.

   Jetzt gibt $() für einen unbekannten Namen eine Attrappe zurück, an der
   sich gefahrlos horchen lässt. Die übrigen Knöpfe funktionieren weiter,
   und in der Konsole steht, welcher fehlt. */
const $ = (id) => {
  const gefunden = document.getElementById(id);
  if (gefunden) return gefunden;
  console.warn('einstellungen.js: „' + id + '" gibt es im Fenster nicht.');
  return {
    addEventListener() {}, removeEventListener() {}, click() {}, focus() {},
    querySelector: () => null, querySelectorAll: () => [],
    appendChild: (k) => k, insertBefore: (k) => k,
    scrollIntoView() {},
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    dataset: {}, style: {}, options: [], hidden: false, disabled: true,
    value: '', textContent: '', innerHTML: '', title: '', checked: false,
    scrollTop: 0, type: '',
  };
};

/* Die Griffe aus programm.js. Bis sie gereicht sind, tut hier nichts weh:
   leere Funktionen statt Abstürze, falls jemand die Reihenfolge umstellt. */
let griffe = {
  zoom: () => 100,
  zoomSetzen: () => {},
  thema: () => 'auto',
  themaWeiter: () => {},
  neuZeichnen: () => {},
  /* Die Schalter: leer, bis programm.js sie reicht. Ein fehlender Griff
     macht sein Kästchen grau statt das Fenster kaputt. */
  schalter: {},
  endungJetzt: () => 'odt',
  endungSetzen: () => {},
  registerAnpassen: () => {},
  vorlagenOrdner: () => {},
  vorlagenOrdnerWeg: () => '',
  /* Die Wahl der Oberfläche wird beim Aufgehen der Seite gelesen — vor
     dem Reichen der Griffe wäre das ein Absturz statt einer Vorauswahl. */
  flaecheJetzt: () => 'leisten',
  flaecheSetzen: () => {},
};

const verbinde = (neue) => { griffe = Object.assign(griffe, neue); };

/* ------------------------------------------------------------
   Der Baum links

   WO DIESE SEITE AUFGEHT

   Datei ▸ Optionen, oder F9. Auch weiterhin unter Schreibhilfe ▸ Anzeigen
   ▸ Optionen, wo sie zuerst stand — und wo sie niemand fand: letzter
   Reiter, letzte Gruppe, hinter Vorlesen und KI. WPS führt sie unter
   Datei, und dort sucht auch jeder zuerst.

   Die Reihenfolge und die Namen sind die aus dem Optionen-Fenster des WPS
   Writer — Kay hat es Seite für Seite geschickt. Wer von dort kommt,
   sucht nicht zweimal.

   FLACH, nicht als Baum. Vorher lagen die Seiten in drei Zweigen, die man
   erst aufklappen musste. Bei sechzehn Seiten ist das ein Umweg ohne
   Gewinn: Man sieht ohnehin alle auf einmal, und WPS macht es genauso.

   ALLE DREIZEHN SEITEN DES WPS WRITER, dazu drei eigene.

   Fünf davon fehlten lange mit Begründung — Sicherung, PDF, Drucken,
   Sicherheit, Schnellzugriff. Die Begründungen stimmten für sich
   genommen, nur stand am Ende ein Fenster da, das sich mit Kays
   Optionen-Fenster nicht mehr vergleichen ließ. Jetzt ist jede Seite da,
   und wo Lunivo etwas anders macht als WPS, steht das AUF der Seite statt
   in einem Kommentar, den niemand liest.

   Die eigenen drei — Schreibhilfe und KI, Gedächtnis, Erweitert — stehen
   dort, wo WPS nichts hat, das sie verdrängen könnten.

   ------------------------------------------------------------ */
const BEREICHE = [
  /* GANZ OBEN, als eigener Zweig, und das ist keine Geschmacksfrage.

     Lunivo ist ein Schreibprogramm für Menschen mit Legasthenie — die
     Lesehilfe ist nicht eine Einstellung unter vierzig, sie ist der Grund,
     warum es das Programm gibt. */
  ['lesen', 'Leichter lesen', [
    ['lesehilfe',   'Lesehilfe'],
    ['schriften',   'Schriftarten'],
    ['sprache',     'Sprache'],
    ['pruefung',    'Rechtschreibprüfung'],
  ]],

  /* Die dreizehn Seiten des WPS Writer, in seiner Reihenfolge und mit
     seinen Namen. */
  ['wps', 'Wie im WPS Writer', [
    ['ansicht',        'Ansicht'],
    ['bearbeiten',     'Bearbeiten'],
    ['speichern',      'Allgemein und Speichern'],
    ['sicherung',      'Sicherungseinstellungen'],
    ['pfade',          'Speicherort für Dateien'],
    ['verfolgen',      'Änderungen verfolgen'],
    ['pdf',            'In PDF exportieren'],
    ['benutzer',       'Benutzerinformationen'],
    ['drucken',        'Drucken'],
    ['sicherheit',     'Sicherheit'],
    ['band',           'Menüband anpassen'],
    ['schnellzugriff', 'Symbolleiste für den Schnellzugriff'],
  ]],

  /* Was WPS nicht hat. */
  ['lunivo', 'Nur bei Lunivo', [
    ['ki',          'Schreibhilfe und KI'],
    ['gedaechtnis', 'Gedächtnis'],
    ['erweitert',   'Erweitert'],
  ]],
];

/* Die Seite, die aufgeht: die Lesehilfe. Wer F9 drückt, ist meistens
   ihretwegen hier. */
let bereichJetzt = 'lesehilfe';
function bereichZeigen(kennung) {
  bereichJetzt = kennung;
  /* Führt ein Knopf auf eine Seite in einem zugeklappten Zweig — etwa
     „Zur Schriftwahl" —, klappt der Zweig auf. Sonst führte der Weg ins
     Leere. */
  for (const [zweigKennung, , blaetter] of BEREICHE) {
    if (blaetter.some(([k]) => k === kennung) && zweigeZu.has(zweigKennung)) {
      zweigeZu.delete(zweigKennung);
      baumBauen();
      return;
    }
  }
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

/* Der Baum mit seinen Zweigen.

   Er war einmal flach: sechzehn Seiten untereinander, jede gleich laut.
   Bei elf ging das noch, bei sechzehn sucht man. Der Stand im Git-Archiv
   hatte drei Zweige, und das war übersichtlicher — Kay hat darauf
   hingewiesen, und er hat recht.

   Alle Zweige stehen offen, wenn das Fenster aufgeht: Wer die Optionen
   zum ersten Mal aufmacht, soll sehen, was es gibt, statt drei
   zugeklappte Wörter. Zuklappen kann man sie danach. */
const zweigeZu = new Set();

function baumBauen() {
  const baum = $('einst-baum');
  baum.innerHTML = '';

  for (const [zweigKennung, zweigName, blaetter] of BEREICHE) {
    const kopf = document.createElement('button');
    kopf.type = 'button';
    kopf.className = 'optionen__zweig';
    const pfeil = document.createElement('span');
    pfeil.className = 'optionen__pfeil';
    pfeil.textContent = zweigeZu.has(zweigKennung) ? '▸' : '▾';
    const wort = document.createElement('span');
    wort.textContent = zweigName;
    kopf.append(pfeil, wort);
    kopf.setAttribute('aria-expanded', zweigeZu.has(zweigKennung) ? 'false' : 'true');
    kopf.addEventListener('click', () => {
      if (zweigeZu.has(zweigKennung)) zweigeZu.delete(zweigKennung);
      else zweigeZu.add(zweigKennung);
      baumBauen();
    });
    baum.appendChild(kopf);

    const kiste = document.createElement('div');
    kiste.className = 'optionen__blaetter';
    kiste.hidden = zweigeZu.has(zweigKennung);
    for (const [kennung, name] of blaetter) {
      const ast = document.createElement('button');
      ast.type = 'button';
      ast.className = 'optionen__ast';
      ast.dataset.bereich = kennung;
      ast.textContent = name;
      ast.setAttribute('role', 'tab');
      ast.addEventListener('click', () => bereichZeigen(kennung));
      kiste.appendChild(ast);
    }
    baum.appendChild(kiste);
  }

  bereichZeigen(bereichJetzt);
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
  } else if (KI.istEigenerAnbieter(modell)) {
    const anbieter = KI.Anbieter.holen(KI.eigenerAnbieterId(modell));
    hinweis.textContent = anbieter
      ? 'Läuft über „' + anbieter.name + '" — ' + anbieter.url + '. Verwenden für: '
        + (anbieter.verwendungFuer || []).map((t) => KI.ANBIETER_TAG_NAMEN[t]).filter(Boolean).join(', ') + '.'
      : 'Dieser Anbieter ist nicht mehr da — unten neu anlegen oder ein anderes Modell wählen.';
  } else {
    hinweis.textContent = 'Läuft im Netz: braucht Schlüssel und Guthaben, antwortet '
      + 'in Sekunden. Der Text geht dafür an Anthropic.';
  }
}

/* ------------------------------------------------------------
   KI-Konfiguration: welches Modell für welche Aufgabe.

   Fünf feste Zeilen (KI.AUFGABEN), jede ein Auswahlfeld mit „Standard"
   ganz oben — leer lassen heißt weiter das global gewählte „KI-Modell"
   verwenden, wie es bisher für alles galt. Die Liste der wählbaren
   Modelle kommt aus KI.alleModelle() und ändert sich mit „Eigene
   Anbieter" — deshalb wird diese Funktion überall dort mit aufgerufen,
   wo auch eigeneAnbieterZeigen() läuft.
   ------------------------------------------------------------ */
function aufgabenZeigen() {
  const kasten = $('einst-aufgaben-liste');
  kasten.innerHTML = '';

  const modelle = KI.alleModelle();
  const jetzt = modelle.find((m) => m.id === KI.modellJetzt());
  const standardName = jetzt ? jetzt.name : KI.modellJetzt();

  for (const [aufgabe, name] of KI.AUFGABEN) {
    const zeile = document.createElement('div');
    zeile.className = 'zeile';

    const label = document.createElement('span');
    label.textContent = name;

    const auswahl = document.createElement('select');
    const standard = document.createElement('option');
    standard.value = '';
    standard.textContent = 'Standard (' + standardName + ')';
    auswahl.appendChild(standard);
    for (const modell of modelle) {
      const o = document.createElement('option');
      o.value = modell.id;
      o.textContent = modell.name + (modell.lokal ? ' — auf diesem Rechner' : '');
      auswahl.appendChild(o);
    }
    auswahl.value = KI.aufgabenModellRoh(aufgabe);
    auswahl.addEventListener('change', () => KI.aufgabenModellSetzen(aufgabe, auswahl.value));

    zeile.append(label, auswahl);
    kasten.appendChild(zeile);
  }
}

/* ------------------------------------------------------------
   Eigene Anbieter.

   Anders als bei Ollama steht die Liste schon da, sobald das Fenster
   aufgeht — sie kommt aus dem eigenen Speicher, nicht von einem Dienst,
   den man erst fragen muss. Trotzdem in einer eigenen Funktion, weil sie
   nach jedem Anlegen und jedem Entfernen neu gebaut werden muss.
   ------------------------------------------------------------ */
/* Wofür ein Anbieter steht, in einer Zeile — dieselbe Zusammensetzung an
   allen drei Stellen, die es zeigen (hier, „Liste der KI-Modelle", das
   Klappfeld „KI-Modell"). „Lokaler Anbieter" nur, wenn die Anschrift
   wirklich auf diesem Rechner liegt (siehe KI.istLokaleUrl) — Teil A4 #22
   will das erkennbar machen, nicht nur bei Ollamas eigenem, kürzerem Weg. */
function anbieterMetaText(anbieter) {
  const marken = (anbieter.verwendungFuer || [])
    .map((t) => KI.ANBIETER_TAG_NAMEN[t]).filter(Boolean).join(', ');
  return anbieter.modell + (marken ? ' · ' + marken : '')
    + (KI.istLokaleUrl(anbieter.url) ? ' · Lokaler Anbieter' : '');
}

function eigeneAnbieterZeigen() {
  const gewaehlt = KI.modellJetzt();
  const liste = KI.Anbieter.liste();

  const kasten = $('einst-modell-eigen');
  kasten.innerHTML = '';
  for (const anbieter of liste) {
    const eintrag = document.createElement('option');
    eintrag.value = KI.EIGEN_MARKE + anbieter.id;
    eintrag.textContent = anbieter.name + ' (' + anbieter.modell + ')'
      + (KI.istLokaleUrl(anbieter.url) ? ' — auf diesem Rechner' : '');
    kasten.appendChild(eintrag);
  }
  if (KI.istEigenerAnbieter(gewaehlt)) $('einst-modell').value = gewaehlt;

  const zeile = $('einst-anbieter-liste');
  zeile.innerHTML = '';
  if (!liste.length) {
    const leer = document.createElement('p');
    leer.className = 'anbieter-liste__leer';
    leer.textContent = 'Noch keiner eingetragen.';
    zeile.appendChild(leer);
    return;
  }

  for (const anbieter of liste) {
    const eintrag = document.createElement('div');
    eintrag.className = 'zeile';

    const namensfeld = document.createElement('span');
    namensfeld.className = 'anbieter-liste__name';
    namensfeld.textContent = anbieter.name;
    const meta = document.createElement('em');
    meta.className = 'anbieter-liste__meta';
    meta.textContent = anbieterMetaText(anbieter);
    namensfeld.appendChild(meta);

    const weg = document.createElement('button');
    weg.className = 'knopf';
    weg.type = 'button';
    weg.textContent = 'Entfernen';
    weg.addEventListener('click', () => {
      /* War er gerade gewählt, fällt die Wahl zurück auf Claude — sonst
         zeigt das Feld auf eine Option, die es nicht mehr gibt. */
      if (KI.modellJetzt() === KI.EIGEN_MARKE + anbieter.id) {
        KI.modellSetzen('claude-opus-5');
      }
      KI.Anbieter.entfernen(anbieter.id);
      eigeneAnbieterZeigen();
      aufgabenZeigen();
      $('einst-modell').value = KI.modellJetzt();
      modellHinweisZeigen();
    });

    eintrag.append(namensfeld, weg);
    zeile.appendChild(eintrag);
  }
}

/* ------------------------------------------------------------
   Eigene Assistenten — dieselbe Listenform wie „Eigene Anbieter" eben,
   nur mit zwei Knöpfen statt einem: „Starten" führt ihn sofort aus,
   „Entfernen" löscht ihn ohne Rückfrage, wie bei den Anbietern auch.
   Stand bis vor Kurzem als eigene Verwaltungsfläche in der Seitenleiste —
   jetzt nur noch hier. Anlegen läuft über denselben Dialog wie im
   Menüband (griffe.assistentErstellen, siehe kiteil.js). Starten schließt
   die Optionen zuerst, sonst liefe die KI-Antwort hinter einer Wand ab,
   die niemand sieht. */
function eigeneAssistentenZeigen() {
  const liste = KI.Assistenten.liste();
  const kasten = $('einst-assistenten-liste');
  kasten.innerHTML = '';

  if (!liste.length) {
    const leer = document.createElement('p');
    leer.className = 'anbieter-liste__leer';
    leer.textContent = 'Noch keiner angelegt.';
    kasten.appendChild(leer);
    return;
  }

  for (const assistent of liste) {
    const zeile = document.createElement('div');
    zeile.className = 'zeile';

    const namensfeld = document.createElement('span');
    namensfeld.className = 'anbieter-liste__name';
    namensfeld.textContent = assistent.name;
    const meta = document.createElement('em');
    meta.className = 'anbieter-liste__meta';
    meta.textContent = assistent.modus === 'ersetzen' ? 'Ersetzt den Text' : 'Zeigt einen Hinweis';
    namensfeld.appendChild(meta);

    const knoepfe = document.createElement('div');
    knoepfe.className = 'anbieter-liste__knoepfe';

    const start = document.createElement('button');
    start.className = 'knopf';
    start.type = 'button';
    start.textContent = 'Starten';
    start.title = assistent.prompt;
    start.addEventListener('click', () => {
      schliessen();
      griffe.assistentAusfuehren(assistent);
    });

    const weg = document.createElement('button');
    weg.className = 'knopf';
    weg.type = 'button';
    weg.textContent = 'Entfernen';
    weg.addEventListener('click', () => {
      KI.Assistenten.entfernen(assistent.id);
      eigeneAssistentenZeigen();
    });

    knoepfe.append(start, weg);
    zeile.append(namensfeld, knoepfe);
    kasten.appendChild(zeile);
  }
}

/* Bekannte Anbieter, mit der Anschrift, die sie selbst angeben — wählt man
   einen, füllt sich die Anschrift von selbst, wie im Vorbild. „Andere"
   lässt beides leer; wer dort landet, trägt seine eigene Anschrift ein. */
const ANBIETER_VORLAGEN = [
  ['andere', 'Andere', ''],
  /* Ollama läuft auf diesem Rechner bereits über einen eigenen, kürzeren
     Weg (das Feld „KI-Modell" weiter oben, „Auf diesem Rechner"). Diese
     Zeile ist der zweite, längere Weg dorthin — über dieselbe OpenAI-
     verträgliche Schnittstelle, die Ollama seit Version 0.x zusätzlich
     anbietet (Port 11434, Pfad „/v1"). Sie steht trotzdem hier, weil
     „Eigenen Anbieter hinzufügen" sonst so aussähe, als kenne es Ollama
     gar nicht — und genau das stiftet Verwirrung. */
  ['ollama', 'Ollama (auf diesem Rechner)', 'http://localhost:11434/v1'],
  ['openai', 'OpenAI', 'https://api.openai.com/v1'],
  ['mistral', 'Mistral', 'https://api.mistral.ai/v1'],
  ['groq', 'Groq', 'https://api.groq.com/openai/v1'],
  ['deepseek', 'DeepSeek', 'https://api.deepseek.com/v1'],
  ['together', 'Together AI', 'https://api.together.xyz/v1'],
];

/* Die Zeile „Modell" — ein Textfeld und ein Knopf, der die Liste beim
   Anbieter selbst abfragt. Ein eigener DOM-Knoten, weil „fenster()" kein
   Feld kennt, das während des Ausfüllens noch etwas nachlädt; er wird als
   „knoten" hereingereicht, sein Textfeld hält Kay selbst in der Hand.

   „bezug" hält die Verweise auf die Felder „Anschrift" und „Schlüssel" —
   „fenster()" baut sie erst, wenn der Dialog aufgeht, und reicht sie beim
   ersten Tippen in irgendein Feld über „beiWechsel" herein (siehe unten).
   Bis dahin steht hier {}; ein Tastendruck in die Anschrift selbst reicht
   schon, um die Verweise zu füllen — das ist keine besondere Handlung. */
function modellZeileBauen(bezug) {
  /* Dieselbe Zeilenform wie bei Name, Anbieter, URL und Schlüssel — Label
     links in derselben Breite, Inhalt rechts. „fenster()" baut das für
     seine eigenen Felder selbst; ein „knoten" muss es sich nachbauen,
     sonst fällt er aus der Reihe der anderen Felder heraus. */
  const kasten = document.createElement('div');
  kasten.className = 'dialog__zeile anbieter-modellzeile';
  const titel = document.createElement('span');
  titel.textContent = 'Modell *';
  kasten.appendChild(titel);

  const inhalt = document.createElement('div');
  inhalt.className = 'anbieter-modellzeile__inhalt';
  kasten.appendChild(inhalt);

  /* Das Feld allein in seiner Zeile — dieselbe Breite wie die Eingaben der
     anderen Felder, kein zweites Element daneben, das nach einer zweiten
     Beschriftung aussieht. Der Verweis zum Abrufen steht als eigene Zeile
     darunter, wie „Von Hand eintragen" es bei der Auswahl auch tut. */
  const reihe = document.createElement('div');
  reihe.className = 'anbieter-modellzeile__reihe';
  const feld = document.createElement('input');
  feld.type = 'text';
  feld.placeholder = 'z. B. gpt-4o-mini';
  const abrufen = document.createElement('button');
  abrufen.type = 'button';
  abrufen.className = 'verweis anbieter-modellzeile__vonhand';
  abrufen.textContent = 'Liste der Modelle aktualisieren';
  reihe.append(feld, abrufen);

  const stand = document.createElement('p');
  stand.className = 'hinweis';

  /* Die Liste als echtes Auswahlfeld, nicht als Kärtchenreihe — Kay wollte
     ein Dropdown, kein Getippe aus Knöpfen. Sie ersetzt das Textfeld dabei,
     statt daneben stehen zu bleiben: Beide zugleich zeigen denselben
     Namen doppelt und niemand weiß, welches der beiden jetzt gilt. Ein
     „Von Hand eintragen"-Verweis führt zurück, für Modelle, die der
     Anbieter nicht nennt. */
  const auswahl = document.createElement('select');
  auswahl.hidden = true;
  const vonHand = document.createElement('button');
  vonHand.type = 'button';
  vonHand.className = 'verweis anbieter-modellzeile__vonhand';
  vonHand.textContent = 'Von Hand eintragen';
  vonHand.hidden = true;

  const zeileZeigen = () => {
    reihe.hidden = false;
    auswahl.hidden = true;
    vonHand.hidden = true;
  };
  const auswahlZeigen = () => {
    reihe.hidden = true;
    auswahl.hidden = false;
    vonHand.hidden = false;
  };

  auswahl.addEventListener('change', () => {
    if (!auswahl.value) return;
    feld.value = auswahl.value;
    stand.textContent = '';
    zeileZeigen();
  });
  vonHand.addEventListener('click', () => { stand.textContent = ''; zeileZeigen(); });

  /* Als eigene Funktion, nicht nur als Klick-Handler — Ollama braucht
     keinen Schlüssel und antwortet auf dem eigenen Rechner, ohne dass
     jemand extra danach fragen sollte. Sie läuft deshalb auch von selbst:
     beim Öffnen mit der vorbelegten Ollama-Vorlage, und jedes Mal, wenn
     „Anbieter" auf eine Vorlage mit eigener URL wechselt. */
  async function abrufenLauf(still) {
    const url = (bezug.url ? bezug.url.value : '').trim();
    if (!url) { if (!still) stand.textContent = 'Erst die URL eintragen.'; return; }
    abrufen.disabled = true;
    stand.textContent = 'Wird geholt …';
    try {
      const namen = await KI.anbieterModelle(url, bezug.schluessel ? bezug.schluessel.value.trim() : '');
      if (!namen.length) { stand.textContent = 'Der Anbieter nennt keine Modelle.'; return; }
      stand.textContent = namen.length + ' gefunden:';
      auswahl.innerHTML = '';
      const erste = document.createElement('option');
      erste.value = '';
      erste.textContent = '— Modell wählen —';
      auswahl.appendChild(erste);
      for (const name of namen) {
        const eintrag = document.createElement('option');
        eintrag.value = name;
        eintrag.textContent = name;
        if (name === feld.value) eintrag.selected = true;
        auswahl.appendChild(eintrag);
      }
      auswahlZeigen();
    } catch (e) {
      /* Beim selbsttätigen Lauf — der Mensch hat nichts gedrückt — bleibt
         das still: Ein OpenAI ohne Schlüssel soll nicht gleich meckern,
         bevor überhaupt einer eingetragen ist. Nach einem echten Klick auf
         den Knopf dagegen schon. */
      stand.textContent = still ? '' : 'Ging nicht — stimmen URL und Schlüssel? (' + e.message + ')';
    } finally {
      abrufen.disabled = false;
    }
  }
  abrufen.addEventListener('click', () => abrufenLauf(false));

  inhalt.append(reihe, stand, auswahl, vonHand);
  return { knoten: kasten, feld, abrufenLauf };
}

/* Die Zeile „Modell verwenden für" — dieselben acht Marken wie in der
   Liste „Eigene Anbieter" (KI.ANBIETER_TAGS), nur als Kärtchenreihe zum
   An- und Abwählen statt als Dropdown mit genau einem Treffer. Ein Modell
   kann mehr als eine Fähigkeit haben — „gpt-4o-mini" versteht Text UND
   Bilder —, darum hier mehrere zugleich wählbar, wie die Marken bei
   „Für wen?" in der Seitenleiste. „Alle" ist eine Abkürzung, kein neunter
   Wert: Sie setzt oder leert die anderen acht in einem Klick. */
function verwendungChipsBauen(anfangswerte) {
  const kasten = document.createElement('div');
  kasten.className = 'dialog__zeile anbieter-modellzeile';
  const titel = document.createElement('span');
  titel.textContent = 'Modell verwenden für';
  kasten.appendChild(titel);

  const inhalt = document.createElement('div');
  inhalt.className = 'verwendung-chips';
  kasten.appendChild(inhalt);

  const alleSchluessel = KI.ANBIETER_TAGS.map(([k]) => k);
  let ausgewaehlt = new Set(anfangswerte && anfangswerte.length ? anfangswerte : ['text']);
  const chips = new Map();

  const alleChip = document.createElement('button');
  alleChip.type = 'button';
  alleChip.className = 'marke';
  alleChip.textContent = 'Alle';

  function zeichne() {
    for (const [schluessel, chip] of chips) chip.classList.toggle('marke--an', ausgewaehlt.has(schluessel));
    alleChip.classList.toggle('marke--an', alleSchluessel.every((k) => ausgewaehlt.has(k)));
  }
  alleChip.addEventListener('click', () => {
    ausgewaehlt = alleSchluessel.every((k) => ausgewaehlt.has(k)) ? new Set() : new Set(alleSchluessel);
    zeichne();
  });
  inhalt.appendChild(alleChip);

  for (const [schluessel, name] of KI.ANBIETER_TAGS) {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'marke';
    chip.textContent = name;
    chip.addEventListener('click', () => {
      if (ausgewaehlt.has(schluessel)) ausgewaehlt.delete(schluessel); else ausgewaehlt.add(schluessel);
      zeichne();
    });
    chips.set(schluessel, chip);
    inhalt.appendChild(chip);
  }
  zeichne();

  return { knoten: kasten, werte: () => [...ausgewaehlt] };
}

/* „bestehender" ist null beim Anlegen — dann heißt es „Eigenen Anbieter
   hinzufügen" und schreibt einen neuen Eintrag. Ist ein Anbieter gegeben
   (Bearbeiten-Symbol in „Liste der KI-Modelle"), heißt der Dialog
   „Modell bearbeiten" und ändert genau diesen Eintrag — derselbe Kasten,
   dieselben Felder, kein zweites Formular. „nachSpeichern" ruft — falls
   gegeben — die Liste auf, aus der heraus bearbeitet wurde. */
/* Der Verweis „Benutzerdefinierte Anbieter" unten im Formular — führt zur
   Liste aller eigenen Anbieter (Bearbeiten, Löschen, Anlegen), statt das
   hier offene Formular ein zweites Mal anzubieten. Schließt sich selbst,
   wie „Abbrechen" es täte, und öffnet direkt danach die Liste. */
function benutzerdefinierteAnbieterLinkBauen() {
  const link = document.createElement('button');
  link.type = 'button';
  link.className = 'verweis anbieter-modellzeile__vonhand';
  link.textContent = 'Benutzerdefinierte Anbieter';
  link.addEventListener('click', (e) => {
    const grund = e.target.closest('.dialoggrund');
    if (grund) grund.remove();
    modelleListeOeffnen();
  });
  return link;
}

/* Ollama braucht in der Standardeinrichtung keinen Schlüssel — statt
   einer künstlichen Pflicht dazu steht das eindeutig am Feld selbst,
   nicht nur im Fließtext darüber, den man leicht überliest. */
function schluesselPlatzhalterSetzen(feld, vorlageKey) {
  if (!feld) return;
  feld.placeholder = vorlageKey === 'ollama' ? 'Nicht erforderlich' : 'z. B. sk-…';
  feld.title = vorlageKey === 'ollama'
    ? 'Ollama braucht in der Standardeinrichtung keinen Schlüssel.' : '';
}

function anbieterFormular(bestehender, nachSpeichern) {
  if (!griffe.fenster) return;

  const bezug = {};
  const modellZeile = modellZeileBauen(bezug);
  if (bestehender) modellZeile.feld.value = bestehender.modell;
  const verwendungChips = verwendungChipsBauen(bestehender ? bestehender.verwendungFuer : ['text']);
  const vorDenDialogen = new Set(document.querySelectorAll('.dialoggrund'));
  /* Die Vorlage, mit der das Feld aufgeht — „beiWechsel" vergleicht damit,
     ob sich „Anbieter" wirklich geändert hat. Beim Bearbeiten: die Vorlage,
     deren Anschrift zur gespeicherten passt, sonst „Andere". */
  let letzteVorlage = bestehender
    ? (ANBIETER_VORLAGEN.find(([, , url]) => url === bestehender.url)?.[0] || 'andere')
    : 'ollama';

  griffe.fenster(bestehender ? 'Modell bearbeiten' : 'Eigenen Anbieter hinzufügen', [
    { schluessel: 'name', name: 'Modellname *', art: 'text',
      wert: bestehender ? bestehender.name : 'Ollama (auf diesem Rechner)' },
    { art: 'unterkopf', text: 'Anbieter' },
    { art: 'satz', text: 'Oben den Anbieter wählen — die URL darunter füllt sich von '
                       + 'selbst und lässt sich danach noch ändern. Nur bei „Andere" '
                       + 'bleibt sie leer und will von Hand eingetragen werden.' },
    { schluessel: 'vorlage', name: 'Name *', art: 'auswahl',
      werte: ANBIETER_VORLAGEN.map(([k, n]) => [k, n]), wert: letzteVorlage },
    { schluessel: 'url', name: 'URL *', art: 'text',
      wert: bestehender ? bestehender.url : 'http://localhost:11434/v1' },
    { schluessel: 'schluessel', name: 'Schlüssel', art: 'password',
      wert: bestehender ? bestehender.schluessel : '' },
    { art: 'knoten', name: 'Modell', knoten: modellZeile.knoten },
    { art: 'knoten', name: 'Modell verwenden für', knoten: verwendungChips.knoten },
    { art: 'knoten', name: '', knoten: benutzerdefinierteAnbieterLinkBauen() },
  ], (werte) => {
    const name = (werte.name || '').trim();
    const url = (werte.url || '').trim();
    const modell = modellZeile.feld.value.trim();
    if (!name || !url || !modell) {
      $('einst-modell-hinweis').textContent =
        'Modellname, URL und Modell werden gebraucht — nichts angelegt.';
      return;
    }
    const angaben = { name, url, schluessel: werte.schluessel, modell,
      verwendungFuer: verwendungChips.werte() };
    if (bestehender) {
      KI.Anbieter.aktualisieren(bestehender.id, angaben);
    } else {
      const angelegt = KI.Anbieter.hinzufuegen(angaben);
      KI.modellSetzen(KI.EIGEN_MARKE + angelegt.id);
      $('einst-modell').value = KI.modellJetzt();
    }
    eigeneAnbieterZeigen();
    aufgabenZeigen();
    modellHinweisZeigen();
    if (typeof nachSpeichern === 'function') nachSpeichern();
  }, bestehender ? 'Speichern' : 'Hinzufügen', false, null, (werte, eingaben) => {
    /* Die Verweise auf „Anschrift" und „Schlüssel" — der Modell-Knopf
       braucht sie, kennt die Felder selbst aber nicht, weil „fenster()"
       sie erst beim Aufgehen baut. Jeder Wechsel reicht sie nach; billig
       genug, um es bei jedem einfach neu zu tun. */
    bezug.url = eingaben.url;
    bezug.schluessel = eingaben.schluessel;

    /* „beiWechsel" meldet jeden Tastendruck in jedem Feld, nicht nur den
       Wechsel des Anbieters — ohne diesen Vergleich liefe die Modell-
       Abfrage bei jedem Buchstaben im Modellnamen neu an. */
    if (werte.vorlage === letzteVorlage) return;
    letzteVorlage = werte.vorlage;
    schluesselPlatzhalterSetzen(eingaben.schluessel, werte.vorlage);

    const vorlage = ANBIETER_VORLAGEN.find(([k]) => k === werte.vorlage);
    if (!vorlage) return;
    const [, anbieterName, url] = vorlage;
    eingaben.url.value = url;
    /* Den Modellnamen nur vorschlagen, wenn noch nichts Eigenes dasteht —
       wer schon getippt hat, soll nicht überschrieben werden. */
    if (!eingaben.name.value.trim() && anbieterName !== 'Andere') eingaben.name.value = anbieterName;
    /* Und gleich nachsehen, was der Anbieter für Modelle hat — bei Ollama
       auf dem eigenen Rechner kostet das nichts und niemand soll extra
       danach fragen müssen. Still, wenn es nicht klappt: Ein Wechsel auf
       „OpenAI" ohne Schlüssel ist noch kein Fehler, nur ein Zwischenstand. */
    if (url) modellZeile.abrufenLauf(true);
  });

  /* „fenster()" baut den Dialog, bevor es zurückkehrt — direkt danach steht
     er schon im DOM, und der Modell-Knopf muss nicht erst auf einen
     Wechsel warten, den es nie gibt: Wer die vorbelegte Anschrift stehen
     lässt und gleich auf „Liste der Modelle abrufen" drückt, rührt „url"
     und „schluessel" nie an, und „beiWechsel" käme dann nie. Der neue
     Dialog ist der einzige, der vorher noch nicht da war. */
  const neuerDialog = [...document.querySelectorAll('.dialoggrund')]
    .find((d) => !vorDenDialogen.has(d));
  if (neuerDialog) {
    /* In der Reihenfolge der Felder oben: Modellname zuerst, Anschrift
       als zweites Textfeld. Über den Namen zu suchen ginge nicht — die
       Felder tragen keinen. */
    const textfelder = [...neuerDialog.querySelectorAll('.dialog__zeile input[type="text"]')];
    bezug.url = textfelder[1];
    bezug.schluessel = neuerDialog.querySelector('.dialog__zeile input[type="password"]');
    schluesselPlatzhalterSetzen(bezug.schluessel, letzteVorlage);
    /* Die Vorlage, mit der das Feld aufgeht, ist Ollama — gleich nachsehen,
       welche Modelle da sind, ohne dass erst ein Wechsel nötig wäre. */
    modellZeile.abrufenLauf(true);
  }
}

/* Der bisherige Name — Menüband, Menü und der Knopf hier auf der Seite
   rufen ihn unverändert; „anbieterFormular(null)" ist genau der
   Anlegen-Fall von eben. */
function eigenenAnbieterHinzufuegen() { anbieterFormular(null); }

/* ------------------------------------------------------------
   Liste der KI-Modelle — alle eigenen Anbieter an einer Stelle, mit
   Anlegen-, Bearbeiten- und Löschen-Symbol. Die Seite „Schreibhilfe und
   KI" zeigt „Eigene Anbieter" zwar schon direkt (Löschen genügte bisher),
   aber ein Bearbeiten-Symbol braucht ein eigenes Formular — dasselbe wie
   beim Anlegen, nur mit einem vorhandenen Eintrag gefüttert. Dieses
   Fenster bündelt beides, wie „Liste der KI-Modelle" es vorgibt: ein
   Knopf „+" oben, darunter jede Zeile mit ✎ und 🗑.
   ------------------------------------------------------------ */
function modelleListeBauen() {
  const kasten = document.createElement('div');
  kasten.className = 'modelle-liste';

  function zeichne() {
    kasten.innerHTML = '';
    const liste = KI.Anbieter.liste();

    if (!liste.length) {
      const leer = document.createElement('p');
      leer.className = 'anbieter-liste__leer';
      leer.textContent = 'Noch keiner eingetragen.';
      kasten.appendChild(leer);
    }

    for (const anbieter of liste) {
      const zeile = document.createElement('div');
      zeile.className = 'zeile';

      const namensfeld = document.createElement('span');
      namensfeld.className = 'anbieter-liste__name';
      namensfeld.textContent = anbieter.name;
      const meta = document.createElement('em');
      meta.className = 'anbieter-liste__meta';
      meta.textContent = anbieterMetaText(anbieter);
      namensfeld.appendChild(meta);

      const knoepfe = document.createElement('div');
      knoepfe.className = 'anbieter-liste__knoepfe';

      const bearbeiten = document.createElement('button');
      bearbeiten.className = 'knopf'; bearbeiten.type = 'button';
      bearbeiten.textContent = '✎';
      bearbeiten.title = '„' + anbieter.name + '" bearbeiten';
      bearbeiten.setAttribute('aria-label', 'Bearbeiten');
      bearbeiten.addEventListener('click', () => anbieterFormular(anbieter, zeichne));

      const weg = document.createElement('button');
      weg.className = 'knopf'; weg.type = 'button';
      weg.textContent = '🗑';
      weg.title = '„' + anbieter.name + '" löschen';
      weg.setAttribute('aria-label', 'Löschen');
      weg.addEventListener('click', () => {
        if (KI.modellJetzt() === KI.EIGEN_MARKE + anbieter.id) KI.modellSetzen('claude-opus-5');
        KI.Anbieter.entfernen(anbieter.id);
        zeichne();
        eigeneAnbieterZeigen();
        aufgabenZeigen();
        $('einst-modell').value = KI.modellJetzt();
        modellHinweisZeigen();
      });

      knoepfe.append(bearbeiten, weg);
      zeile.append(namensfeld, knoepfe);
      kasten.appendChild(zeile);
    }

    const neu = document.createElement('button');
    neu.className = 'knopf'; neu.type = 'button';
    neu.textContent = '+ Modell hinzufügen …';
    neu.addEventListener('click', () => anbieterFormular(null, zeichne));
    kasten.appendChild(neu);
  }

  zeichne();
  return kasten;
}

function modelleListeOeffnen() {
  if (!griffe.fenster) return;
  griffe.fenster('Liste der KI-Modelle', [
    { art: 'knoten', name: '', knoten: modelleListeBauen() },
  ], () => {}, 'Schließen');
}

/* ------------------------------------------------------------
   Übersetzen nach — eine Sprache aus einer Liste wählen, nicht aus einem
   Klappfeld. Eine Zeile je Sprache, angeklickt heißt gewählt; „OK"
   übernimmt erst dann. Der gespeicherte Wert bleibt derselbe String wie
   bisher (KI.Speicher „sprache") — nur der Weg dorthin ist neu.
   ------------------------------------------------------------ */
function spracheKnopfZeigen() {
  $('einst-sprache-knopf').textContent = KI.Speicher.lies('sprache', 'Englisch');
}

function sprachlisteBauen(anfangswert) {
  const kasten = document.createElement('div');
  kasten.className = 'sprachliste';
  let gewaehlt = anfangswert;
  const zeilen = new Map();

  function markiere() {
    for (const [sprache, zeile] of zeilen) {
      zeile.classList.toggle('sprachliste__zeile--an', sprache === gewaehlt);
    }
  }
  for (const sprache of KI.SPRACHEN) {
    const zeile = document.createElement('button');
    zeile.type = 'button';
    zeile.className = 'sprachliste__zeile';
    zeile.textContent = sprache;
    zeile.addEventListener('click', () => { gewaehlt = sprache; markiere(); });
    zeilen.set(sprache, zeile);
    kasten.appendChild(zeile);
  }
  markiere();
  return { knoten: kasten, wert: () => gewaehlt };
}

function uebersetzungsSpracheOeffnen() {
  if (!griffe.fenster) return;
  const liste = sprachlisteBauen(KI.Speicher.lies('sprache', 'Englisch'));
  griffe.fenster('Einstellungen der Übersetzung', [
    { art: 'satz', text: 'Sprache für die KI-Übersetzung wählen.' },
    { art: 'knoten', name: '', knoten: liste.knoten },
  ], () => {
    KI.Speicher.schreib('sprache', liste.wert());
    spracheKnopfZeigen();
    griffe.neuZeichnen();
  }, 'OK');
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
function speichernZeigen() {
  const w = $('einst-endung');
  const jetzt = griffe.endungJetzt();
  w.value = [...w.options].some((o) => o.value === jetzt) ? jetzt : 'odt';
  $('einst-vorlagenordner').value = griffe.vorlagenOrdnerWeg() || '~/Vorlagen';
}

function darstellungZeigen() {
  const zoom = griffe.zoom();
  $('einst-zoom-stand').textContent = 'Schriftgröße: ' + zoom + ' %';
  $('einst-probe').style.fontSize = (12 * zoom / 100).toFixed(1) + 'pt';
  schalterZeigen();
  /* Die drei Listen, die auf Griffe aus programm.js angewiesen sind. */
  bandZeichnen();
  szZeichnen();
  kennwortStandZeigen();
}

/* ------------------------------------------------------------
   Die Schalter

   Zehn Stück, und alle machen dasselbe: Sie fragen das Programm, wie es
   gerade steht, und legen den Griff um. Sie einzeln zu verdrahten hieße
   zwanzig fast gleiche Zeilen — und die elfte vergisst man.

   Am Kästchen steht, welcher Griff gemeint ist (data-schalter). Die
   Griffe selbst liegen in programm.js: Nur dort weiß jemand, was „Lineal
   an" bedeutet. */
function schalterGriff(kasten) {
  return (griffe.schalter || {})[kasten.dataset.schalter] || null;
}

/* Die Klappmenüs und Zahlenfelder.

   Nicht alles im Optionen-Fenster ist ein Kästchen: WPS führt Maßeinheit,
   Feldschattierung, Standardeinfügeformat, die Striche und Farben des
   Markups, die Breite der Sprechblasen. Sie tragen data-wert statt
   data-schalter und holen ihren Stand aus derselben Quelle.

   Verdrahtet wird über window.Optionen — programm.js reicht es dorthin,
   und die Optionenseite muss dafür nichts über das Programm wissen. */
const OPT = () => (typeof window !== 'undefined' && window.Optionen) || null;

/* Die Erklärungen als Tooltip.

   Sie standen unter jedem Namen und machten die Zeile dreimal so hoch —
   WPS hat dort nichts, und deshalb passt bei ihm eine ganze Seite auf
   eine Seite. Weggeworfen sind sie damit nicht: Sie hängen jetzt an der
   Zeile, und wer sie braucht, hält kurz die Maus darauf.

   Läuft einmal beim Öffnen; danach steht der Text und ändert sich nicht
   mehr. */
let tooltipsGesetzt = false;
function tooltipsSetzen() {
  if (tooltipsGesetzt) return;
  tooltipsGesetzt = true;
  /* Auch die Klapplisten und Zahlenfelder: Ihre Erklärung steht jetzt
     ebenfalls im Tooltip, nicht mehr in der Zeile. */
  for (const zeile of document.querySelectorAll('#einst-bereiche .karte > .feld:not(.feld--schalter)')) {
    const satz = zeile.querySelector('.feld__satz');
    const name = zeile.querySelector('.feld__name');
    if (satz && name) zeile.title = name.textContent.trim() + ' — ' + satz.textContent.trim();
  }
  for (const zeile of document.querySelectorAll('#einst-bereiche .feld--schalter')) {
    const satz = zeile.querySelector('.feld__satz');
    const name = zeile.querySelector('.feld__name');
    if (!satz || !name) continue;
    /* Der Name steht im selben Element wie der Satz — deshalb nicht
       textContent des Namens nehmen, sondern beide zusammensetzen. */
    const kurz = name.childNodes[0] ? String(name.childNodes[0].textContent).trim() : '';
    zeile.title = (kurz ? kurz + ' — ' : '') + satz.textContent.trim();
  }
}

/* Die Lesehilfe auf der ersten Seite.

   Die Klapplisten füllen sich aus dem Programm — dieselben Stufen wie im
   Dialog, damit nicht zwei Listen nebeneinanderstehen und auseinander
   laufen. Und jede Wahl wirkt sofort: Wer sehen will, ob ihm mehr
   Buchstabenabstand hilft, muss dafür nicht erst „Übernehmen" drücken. */
/* ------------------------------------------------------------
   DIE DREI LESESTUFEN

   Die Wahl steht oben auf der Seite „Lesehilfe", die sechs Klappfelder
   darunter. Sie stellt dieselben Felder, die man auch einzeln stellen
   kann — und wer eines von Hand anfasst, landet auf „Eigene Einstellung":
   Dann ist keine Stufe mehr angekreuzt, und nichts ist verschwunden.

   Das Probeblatt daneben ist kein Bild, sondern ein Stück Blatt mit den
   echten Werten. Es stimmt deshalb auch auf „Eigene Einstellung", wo eine
   Zeichnung je Stufe nichts mehr zu zeigen hätte.
   ------------------------------------------------------------ */

const LESESTUFE_SATZ = {
  standard:
    'Weißes Blatt, normale Abstände, kein Absatzfokus. So, wie jedes '
  + 'andere Schreibprogramm es zeigt.\n'
  + 'Vorgesehen für alle, die beim Lesen keine Hilfe brauchen.',
  leichter:
    'Cremefarbenes Blatt, etwas mehr Luft zwischen Buchstaben, Wörtern und '
  + 'Zeilen. Der Absatz, in dem du stehst, tritt hervor; die übrigen treten '
  + 'zurück — aber sie bleiben lesbar.\n'
  + 'Vorgesehen als der Normalfall dieses Programms.',
  sehr:
    'Blassgelbes Blatt, deutlich mehr Luft, starker Absatzfokus. Auf das '
  + 'Blatt passt weniger Text — das ist der Preis und der Zweck zugleich.\n'
  + 'Vorgesehen, wenn Lesen wirklich schwerfällt.',
  '':
    'Eigene Einstellung: Die Felder darunter stehen auf einer Mischung, die '
  + 'zu keiner der drei Stufen passt. Das ist kein Fehler — so sieht es aus, '
  + 'wenn man selbst gestellt hat.\n'
  + 'Eine Stufe anklicken stellt alle sechs Felder auf einmal um.',
};

let lesestufenGebaut = false;

function lesestufenBauen() {
  if (lesestufenGebaut || !griffe.lesestufen) return;
  const kasten = $('einst-lesestufe');
  if (!kasten || !kasten.querySelector) return;
  const liste = kasten.querySelector('.flaechenwahl__liste');
  if (!liste) return;

  for (const [marke, name] of griffe.lesestufen()) {
    const wahl = document.createElement('label');
    wahl.className = 'flaechenwahl__wahl';
    const knopf = document.createElement('input');
    knopf.type = 'radio';
    knopf.name = 'einst-lesestufe-wahl';
    knopf.value = marke;
    const wort = document.createElement('span');
    wort.textContent = name;
    wahl.append(knopf, wort);
    liste.appendChild(wahl);
  }
  lesestufenGebaut = true;
}

function leseprobeZeigen() {
  if (!griffe.leseprobeWerte) return;
  const probe = $('einst-leseprobe');
  if (!probe || !probe.style || !probe.style.setProperty) return;
  const w = griffe.leseprobeWerte();
  /* Ohne Ton bleibt das Blatt weiß — dann darf hier NICHTS stehen, sonst
     wäre die Farbe die leere Zeichenkette und das Blatt durchsichtig. */
  if (w.ton) probe.style.setProperty('--probe-ton', w.ton);
  else probe.style.removeProperty('--probe-ton');
  probe.style.setProperty('--probe-schrift', w.schrift ? '"' + w.schrift + '"' : '');
  probe.style.setProperty('--lese-zeichen', w.zeichen);
  probe.style.setProperty('--lese-wort', w.wort);
  probe.style.setProperty('--lese-zeilen', w.zeilen);
  probe.style.setProperty('--fokus-wachstum', w.wachstum);
  probe.style.setProperty('--rest-blaesse', w.blaesse);
}

function lesestufeZeigen() {
  if (!griffe.lesestufeJetzt) return;
  lesestufenBauen();
  const jetzt = griffe.lesestufeJetzt();
  for (const knopf of document.querySelectorAll('input[name="einst-lesestufe-wahl"]')) {
    knopf.checked = knopf.value === jetzt;
  }
  const satz = $('einst-lesestufe-satz');
  if (satz) satz.textContent = LESESTUFE_SATZ[jetzt] || LESESTUFE_SATZ[''];
  leseprobeZeigen();
}

function lesestufeVerdrahten() {
  const kasten = $('einst-lesestufe');
  if (!kasten || !kasten.addEventListener) return;
  /* Ein Horcher am Kasten, nicht drei einzelne: Die Knöpfe entstehen erst
     beim Aufgehen, und eine vierte Stufe soll nichts weiter kosten. */
  kasten.addEventListener('change', (fall) => {
    const knopf = fall.target;
    if (!knopf || knopf.name !== 'einst-lesestufe-wahl') return;
    if (griffe.lesestufeSetzen) griffe.lesestufeSetzen(knopf.value);
    /* Die sechs Klappfelder darunter zeigen jetzt etwas anderes an — sie
       müssen mitgeführt werden, sonst stünde dort der alte Stand. */
    lesehilfeZeigen();
    lesestufeZeigen();
  });
}

let lesehilfeGefuellt = false;

function lesehilfeZeigen() {
  if (!griffe.lesehilfeStand || !griffe.lesehilfeWerte) return;
  const werte = griffe.lesehilfeWerte();
  const stand = griffe.lesehilfeStand();

  for (const feld of document.querySelectorAll('#einst-bereiche [data-lesehilfe]')) {
    const name = feld.dataset.lesehilfe;
    if (!lesehilfeGefuellt && werte[name]) {
      feld.innerHTML = '';
      for (const [marke, wort] of werte[name]) {
        const punkt = document.createElement('option');
        punkt.value = marke; punkt.textContent = wort;
        feld.appendChild(punkt);
      }
    }
    if (stand[name] !== undefined) feld.value = String(stand[name]);
  }
  lesehilfeGefuellt = true;
}

function lesehilfeVerdrahten() {
  for (const feld of document.querySelectorAll('#einst-bereiche [data-lesehilfe]')) {
    feld.addEventListener('change', () => {
      if (griffe.lesehilfeSetzen) griffe.lesehilfeSetzen(feld.dataset.lesehilfe, feld.value);
      /* Wer hier von Hand stellt, fällt womöglich aus seiner Stufe — dann
         muss oben das Kreuz verschwinden und die Probe nachziehen. Ohne
         das stünde dort weiter „Leichter lesen", während das Blatt längst
         etwas anderes zeigt. */
      lesestufeZeigen();
    });
  }
  const zurPruefung = $('einst-zur-pruefung');
  if (zurPruefung) zurPruefung.addEventListener('click', () => bereichZeigen('pruefung'));
  const zumGed2 = $('einst-zum-gedaechtnis2');
  if (zumGed2) zumGed2.addEventListener('click', () => bereichZeigen('gedaechtnis'));

  const zuErweitert = $('einst-schriften-pruefen');
  if (zuErweitert) zuErweitert.addEventListener('click', () => bereichZeigen('erweitert'));

  const zurSchrift = $('einst-lh-zur-schrift');
  if (zurSchrift) zurSchrift.addEventListener('click', () => {
    bereichZeigen('schriften');
    const wahl = $('einst-schrift');
    if (wahl) { wahl.scrollIntoView({ block: 'center' }); wahl.focus(); }
  });
  const stimme = $('einst-lh-stimme');
  if (stimme) stimme.addEventListener('click', () => {
    schliessen();
    if (griffe.stimmeWaehlen) griffe.stimmeWaehlen();
  });
}

function werteZeigen() {
  const o = OPT();
  for (const feld of document.querySelectorAll('#einst-bereiche [data-wert]')) {
    if (!o) { feld.disabled = true; continue; }
    feld.disabled = false;
    try {
      const wert = o.wert(feld.dataset.wert);
      if (wert !== undefined && wert !== null) feld.value = String(wert);
    } catch (e) { /* still */ }
  }
}

/* ------------------------------------------------------------
   „Menüband anpassen" und „Symbolleiste für den Schnellzugriff"

   Beide Seiten sind nach dem WPS-Fenster gebaut: links eine Klappliste
   mit Suchfeld und darunter die Befehle, in der Mitte „Hinzufügen" und
   „Entfernen", rechts das Ziel — beim Menüband ein Baum aus
   Registerkarten und ihren Gruppen, beim Schnellzugriff die Leiste
   selbst. Die Pfeile stehen rechts daneben und bleiben stehen, während
   die Auswahl wandert.

   Vorher stand hier eine schmale Liste mit Kästchen und zwei Pfeilen.
   Das war dieselbe Sache, aber nicht derselbe Aufbau.
   ------------------------------------------------------------ */

/* Das kleine Bild vor einem Befehl.

   Bei WPS steht in der Befehlsliste vor jedem Namen seine Zeichnung —
   und das ist keine Zier: In einer Liste von hundert Namen sucht das Auge
   die Form, nicht das Wort. Hier standen erst nur Wörter.

   Gezeichnet wird aus denselben Linien wie im Band; programm.js reicht
   sie durch symbolLinien(). Findet sich keine, bleibt die Stelle leer —
   dann rückt der Name nicht ein und die Liste bleibt bündig. */
const SVG_RAUM = 'http://www.w3.org/2000/svg';

function anpBild(kennung) {
  const o = OPT();
  const platz = document.createElement('span');
  platz.className = 'anp__bild';
  platz.setAttribute('aria-hidden', 'true');
  if (!kennung || !griffe.symbolLinien) return platz;

  let linien = '';
  try { linien = griffe.symbolLinien(kennung) || ''; } catch (e) { linien = ''; }
  if (!linien) {
    /* Manche Knöpfe tragen statt einer Zeichnung einen Buchstaben — „F"
       für fett, „K" für kursiv. Dann steht der da. */
    if (kennung.length <= 2) platz.textContent = kennung;
    return platz;
  }

  const bild = document.createElementNS(SVG_RAUM, 'svg');
  bild.setAttribute('viewBox', '0 0 24 24');
  bild.setAttribute('width', '15'); bild.setAttribute('height', '15');
  bild.setAttribute('fill', 'none'); bild.setAttribute('stroke', 'currentColor');
  bild.setAttribute('stroke-width', '1.8');
  bild.setAttribute('stroke-linecap', 'round');
  bild.setAttribute('stroke-linejoin', 'round');
  if (linien.indexOf('<') === -1) {
    const pfad = document.createElementNS(SVG_RAUM, 'path');
    pfad.setAttribute('d', linien);
    bild.appendChild(pfad);
  } else {
    bild.innerHTML = linien;
  }
  platz.appendChild(bild);
  return platz;
}

/* Eine Zeile in einer der vier Listen. */
function anpZeile(text, gewaehlt, klick, zusatz, symbol) {
  const zeile = document.createElement('div');
  zeile.className = 'anp__zeile' + (gewaehlt ? ' anp__zeile--gewaehlt' : '')
                  + (zusatz ? ' ' + zusatz : '');
  zeile.setAttribute('role', 'option');
  zeile.setAttribute('aria-selected', gewaehlt ? 'true' : 'false');
  if (symbol !== undefined) zeile.appendChild(anpBild(symbol));
  const wort = document.createElement('span');
  wort.className = 'anp__wort';
  wort.textContent = text;
  zeile.appendChild(wort);
  zeile.title = text;
  zeile.addEventListener('mousedown', (e) => { e.preventDefault(); klick(); });
  return zeile;
}

/* Was in der linken Klappliste steht: dieselben Gruppen wie bei WPS. */
function anpQuellenFuellen(wahl) {
  if (!wahl || wahl.options.length) return;
  const namen = ['Häufig verwendete Befehle', 'Alle Befehle'];
  if (griffe.bandReiter) namen.push(...griffe.bandReiter().map((n) => 'Registerkarte: ' + n));
  for (const name of namen) {
    const punkt = document.createElement('option');
    punkt.value = name; punkt.textContent = name;
    wahl.appendChild(punkt);
  }
}

/* Die Befehle zu einer Quelle, gefiltert nach dem Suchwort. */
function anpBefehle(quelle, suche) {
  if (!griffe.befehle) return [];
  /* Sie kommen als { name, symbol } — ältere Fassungen gaben nur Namen
     zurück, deshalb beides annehmen. */
  let liste = (griffe.befehle(quelle) || []).map(
    (e) => (typeof e === 'string' ? { name: e, symbol: '' } : e));
  const wort = (suche || '').trim().toLowerCase();
  if (wort) liste = liste.filter((e) => e.name.toLowerCase().includes(wort));
  return liste;
}

/* ---- Menüband anpassen ---- */
let bandGewaehltBefehl = null;   /* links */
let bandGewaehlt = null;         /* rechts: { reiter, gruppe } */
const bandOffen = new Set();     /* welche Registerkarten aufgeklappt sind */

function bandBefehleZeichnen() {
  const kasten = $('einst-band-befehle');
  if (!kasten) return;
  kasten.textContent = '';
  for (const e of anpBefehle($('einst-band-quelle').value, $('einst-band-suche').value)) {
    kasten.appendChild(anpZeile(e.name, e.name === bandGewaehltBefehl, () => {
      bandGewaehltBefehl = e.name; bandBefehleZeichnen(); bandKnoepfeStellen();
    }, '', e.symbol));
  }
}

function bandBaumZeichnen() {
  const kasten = $('einst-band-baum');
  if (!kasten || !griffe.bandReiter) return;
  kasten.textContent = '';
  for (const reiter of griffe.bandReiter()) {
    const auf = bandOffen.has(reiter);
    const gewaehlt = bandGewaehlt && bandGewaehlt.reiter === reiter && !bandGewaehlt.gruppe;
    const zeile = anpZeile(reiter, gewaehlt, () => {
      bandGewaehlt = { reiter, gruppe: null };
      if (auf) bandOffen.delete(reiter); else bandOffen.add(reiter);
      bandBaumZeichnen(); bandKnoepfeStellen();
    });
    const pfeil = document.createElement('span');
    pfeil.className = 'anp__pfeil';
    pfeil.textContent = auf ? '▼' : '▶';
    zeile.insertBefore(pfeil, zeile.firstChild);
    kasten.appendChild(zeile);

    if (!auf) continue;
    for (const eintrag of (griffe.bandGruppen(reiter) || [])) {
      const gew = bandGewaehlt && bandGewaehlt.reiter === reiter
               && bandGewaehlt.gruppe === eintrag.name;
      const g = anpZeile(eintrag.name, gew, () => {
        bandGewaehlt = { reiter, gruppe: eintrag.name };
        bandBaumZeichnen(); bandKnoepfeStellen();
      }, 'anp__zeile--gruppe');
      const kaestchen = document.createElement('input');
      kaestchen.type = 'checkbox';
      kaestchen.checked = eintrag.an;
      kaestchen.addEventListener('mousedown', (e) => e.stopPropagation());
      kaestchen.addEventListener('change', () => {
        griffe.bandGruppeZeigen(reiter, eintrag.name, kaestchen.checked);
        bandBaumZeichnen();
      });
      g.insertBefore(kaestchen, g.firstChild);
      kasten.appendChild(g);
    }
  }
}

function bandKnoepfeStellen() {
  const g = bandGewaehlt;
  const liste = g && g.gruppe ? (griffe.bandGruppen(g.reiter) || []) : [];
  const i = g && g.gruppe ? liste.findIndex((e) => e.name === g.gruppe) : -1;
  $('einst-band-hoch').disabled = i <= 0;
  $('einst-band-runter').disabled = i < 0 || i === liste.length - 1;
  $('einst-band-dazu').disabled = !bandGewaehltBefehl || !g;
  $('einst-band-raus').disabled = !(g && g.gruppe);
}

function bandZeichnen() {
  anpQuellenFuellen($('einst-band-quelle'));
  bandBefehleZeichnen();
  bandBaumZeichnen();
  bandKnoepfeStellen();
}

function bandListeVerdrahten() {
  if (!$('einst-band-baum')) return;
  $('einst-band-quelle').addEventListener('change', bandBefehleZeichnen);
  $('einst-band-suche').addEventListener('input', bandBefehleZeichnen);

  const schieben = (wohin) => {
    const g = bandGewaehlt;
    if (!g || !g.gruppe || !griffe.bandGruppeSchieben) return;
    griffe.bandGruppeSchieben(g.reiter, g.gruppe, wohin);
    bandBaumZeichnen(); bandKnoepfeStellen();
  };
  $('einst-band-hoch').addEventListener('click', () => schieben(-1));
  $('einst-band-runter').addEventListener('click', () => schieben(1));

  $('einst-band-dazu').addEventListener('click', () => {
    if (!bandGewaehltBefehl || !bandGewaehlt || !griffe.bandBefehlDazu) return;
    griffe.bandBefehlDazu(bandGewaehlt.reiter, bandGewaehlt.gruppe, bandGewaehltBefehl);
    bandOffen.add(bandGewaehlt.reiter);
    bandZeichnen();
  });
  $('einst-band-raus').addEventListener('click', () => {
    const g = bandGewaehlt;
    if (!g || !g.gruppe || !griffe.bandGruppeZeigen) return;
    /* „Entfernen" heißt bei einer Gruppe: ausblenden. Gelöscht wird nichts
       — sonst wäre sie mit „Zurücksetzen" nicht wiederzuholen. */
    griffe.bandGruppeZeigen(g.reiter, g.gruppe, false);
    bandBaumZeichnen();
  });

  $('einst-band-neuekarte').addEventListener('click', () => {
    if (griffe.bandNeueKarte) { griffe.bandNeueKarte(); bandZeichnen(); }
  });
  $('einst-band-neuegruppe').addEventListener('click', () => {
    if (bandGewaehlt && griffe.bandNeueGruppe) {
      griffe.bandNeueGruppe(bandGewaehlt.reiter);
      bandOffen.add(bandGewaehlt.reiter);
      bandZeichnen();
    }
  });
  $('einst-band-umbenennen').addEventListener('click', () => {
    if (bandGewaehlt && griffe.bandUmbenennen) {
      griffe.bandUmbenennen(bandGewaehlt.reiter, bandGewaehlt.gruppe);
      bandZeichnen();
    }
  });
  $('einst-band-zuruecksetzen').addEventListener('click', () => {
    if (griffe.bandZuruecksetzen) { griffe.bandZuruecksetzen(null); bandZeichnen(); }
  });
  $('einst-band-tasten').addEventListener('click', () => {
    if (griffe.tastenHilfe) griffe.tastenHilfe();
  });
}

/* ---- Symbolleiste für den Schnellzugriff ---- */
let szLinks = null, szRechts = null;

function szZeichnen() {
  if (!$('einst-sz-alle') || !griffe.szDrin) return;
  anpQuellenFuellen($('einst-sz-quelle'));

  const drin = griffe.szDrin();
  const links = $('einst-sz-alle');
  links.textContent = '';
  for (const e of anpBefehle($('einst-sz-quelle').value, $('einst-sz-suche').value)) {
    if (drin.includes(e.name)) continue;
    links.appendChild(anpZeile(e.name, e.name === szLinks, () => {
      szLinks = e.name; szRechts = null; szZeichnen();
    }, '', e.symbol));
  }

  const rechts = $('einst-sz-drin');
  rechts.textContent = '';
  for (const name of drin) {
    rechts.appendChild(anpZeile(name, name === szRechts, () => {
      szRechts = name; szLinks = null; szZeichnen();
    }, '', griffe.symbolZu ? griffe.symbolZu(name) : ''));
  }

  const i = drin.indexOf(szRechts);
  $('einst-sz-hoch').disabled = i <= 0;
  $('einst-sz-runter').disabled = i < 0 || i === drin.length - 1;
  $('einst-sz-dazu').disabled = !szLinks;
  $('einst-sz-weg').disabled = !szRechts;
}

function schnellzugriffVerdrahten() {
  if (!$('einst-sz-alle')) return;
  $('einst-sz-quelle').addEventListener('change', szZeichnen);
  $('einst-sz-suche').addEventListener('input', szZeichnen);
  $('einst-sz-dazu').addEventListener('click', () => {
    if (szLinks && griffe.szDazu) { griffe.szDazu(szLinks); szRechts = szLinks; szLinks = null; szZeichnen(); }
  });
  $('einst-sz-weg').addEventListener('click', () => {
    if (szRechts && griffe.szWeg) { griffe.szWeg(szRechts); szRechts = null; szZeichnen(); }
  });
  $('einst-sz-hoch').addEventListener('click', () => {
    if (szRechts && griffe.szSchieben) { griffe.szSchieben(szRechts, -1); szZeichnen(); }
  });
  $('einst-sz-runter').addEventListener('click', () => {
    if (szRechts && griffe.szSchieben) { griffe.szSchieben(szRechts, 1); szZeichnen(); }
  });
  $('einst-sz-zurueck').addEventListener('click', () => {
    if (griffe.szZurueck) griffe.szZurueck();
    szLinks = szRechts = null; szZeichnen();
  });
}

/* ------------------------------------------------------------
   Das Dokumentkennwort

   Hier stand einmal, Lunivo könne das nicht, und ein Feld dafür wäre
   gefährlich. Das erste stimmte, das zweite war ein Vorwand: Der Browser
   bringt AES-256 mit, und ein Schlüssel aus dem Kennwort ist mit PBKDF2
   in zehn Zeilen gerechnet. Jetzt verschlüsselt es wirklich.
   ------------------------------------------------------------ */
function kennwortStandZeigen() {
  const stand = $('einst-kennwort-stand');
  if (!stand || !griffe.kennwortGesetzt) return;
  stand.textContent = griffe.kennwortGesetzt()
    ? 'Dieses Dokument ist verschlüsselt.'
    : 'Ohne Kennwort — die Datei ist im Klartext lesbar.';
}

function kennwortVerdrahten() {
  const setzen = $('einst-kennwort-setzen');
  if (!setzen) return;
  setzen.addEventListener('click', async () => {
    const eins = $('einst-kennwort').value;
    const zwei = $('einst-kennwort2').value;
    const stand = $('einst-kennwort-stand');
    if (!eins) { stand.textContent = 'Bitte ein Kennwort eingeben.'; return; }
    if (eins !== zwei) { stand.textContent = 'Die beiden Kennwörter sind nicht gleich.'; return; }
    await griffe.kennwortSetzen(eins, $('einst-kennwort-hinweis').value);
    $('einst-kennwort').value = $('einst-kennwort2').value = '';
    kennwortStandZeigen();
  });
  $('einst-kennwort-weg').addEventListener('click', async () => {
    await griffe.kennwortSetzen('', '');
    kennwortStandZeigen();
  });
  kennwortStandZeigen();
}

function werteVerdrahten() {
  for (const feld of document.querySelectorAll('#einst-bereiche [data-wert]')) {
    feld.addEventListener('change', () => {
      const o = OPT();
      if (!o) return;
      /* Zahlenfelder als Zahl zurückgeben — sonst stünde „220" als Text
         in der Einstellungsdatei und käme als Text zurück. */
      const roh = feld.value;
      const wert = feld.type === 'number' ? Number(roh) : roh;
      o.setze(feld.dataset.wert, wert);
    });
  }
}

function schalterZeigen() {
  werteZeigen();
  lesehilfeZeigen();
  lesestufeZeigen();
  tooltipsSetzen();
  for (const kasten of document.querySelectorAll('#einst-bereiche [data-schalter]')) {
    const griff = schalterGriff(kasten);
    /* Beides, an UND aus: Ein Kästchen, das einmal grau wurde, blieb es
       sonst für immer — auch wenn der Griff längst da ist. Genau das war
       der Fall, als die Seite ihre Schalter verdrahtete, bevor
       programm.js sie gereicht hatte: zehn graue Kästchen. */
    kasten.disabled = !griff;
    if (!griff) { kasten.checked = false; continue; }
    try { kasten.checked = !!griff.an(); } catch (e) { kasten.checked = false; }
  }
}

function schalterVerdrahten() {
  werteVerdrahten();
  lesehilfeVerdrahten();
  lesestufeVerdrahten();
  bandListeVerdrahten();
  schnellzugriffVerdrahten();
  kennwortVerdrahten();
  for (const kasten of document.querySelectorAll('#einst-bereiche [data-schalter]')) {
    kasten.addEventListener('change', () => {
      /* Erst beim Klick nachsehen, welcher Griff gemeint ist — beim
         Verdrahten gibt es ihn womöglich noch nicht. */
      const griff = schalterGriff(kasten);
      if (!griff) return;
      griff.um();
      /* Danach alle noch einmal nachsehen: Manche Schalter ziehen andere
         mit — „Änderungen verfolgen" aus heißt auch, dass das Markup
         nichts mehr zu zeigen hat. */
      schalterZeigen();
    });
  }
}

/* ------------------------------------------------------------
   Auf- und zumachen
   ------------------------------------------------------------ */
let offen = false;

function oeffnen(bereich) {
  $('einstellungen').hidden = false;
  offen = true;

  if (bereich) bereichJetzt = bereich;
  baumBauen();

  benutzerZeigen();
  schriftenZeigen();
  leseschriftenZeigen();
  spracheZeigen();
  pfadZeigen();
  bedienungZeigen();
  teileZeigen();

  $('einst-schluessel').value = KI.schluesselLies();
  $('einst-modell').value = KI.modellJetzt();
  eigeneAnbieterZeigen();
  eigeneAssistentenZeigen();
  aufgabenZeigen();
  schluesselStandZeigen();
  modellHinweisZeigen();
  kostenZeigen();
  gedaechtnisZeigen();
  darstellungZeigen();
  speichernZeigen();

  /* Beim Aufgehen steht dort die Anleitung, nicht der Satz von letztem
     Mal — der gehörte zu einem Feld, auf das jetzt niemand zeigt. */
  erklaerungLeeren();

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
/* Die drei Leseschriften als Knöpfe, jede in ihrer eigenen Schrift.

   Ein Name allein hilft nicht: „OpenDyslexic" fällt niemandem ein, wenn
   er sie braucht — Kay ging es gerade so. Die Form dagegen erkennt man
   sofort, und ein Klick stellt sie ein. */
const LESESCHRIFTEN_SATZ = {
  'OpenDyslexic': 'Die Buchstaben sind unten schwerer — sie kippen nicht.',
  'Lexend': 'Weitere Abstände, ruhigeres Zeilenbild.',
  'Atkinson Hyperlegible': 'Unterscheidet Zeichen, die sich ähneln: l, I und 1.',
};

function leseschriftenZeigen() {
  const kasten = $('einst-leseschriften');
  if (!kasten || !kasten.appendChild || !griffe.leseschriften) return;
  const da = griffe.leseschriften();
  const jetzt = griffe.schriftJetzt();
  kasten.textContent = '';

  for (const name of Object.keys(LESESCHRIFTEN_SATZ)) {
    const vorhanden = da.includes(name);
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.className = 'schriftprobe-knopf'
                    + (name === jetzt ? ' schriftprobe-knopf--gewaehlt' : '')
                    + (vorhanden ? '' : ' schriftprobe-knopf--fehlt');
    knopf.disabled = !vorhanden;

    const wort = document.createElement('span');
    wort.className = 'schriftprobe-knopf__name';
    wort.textContent = name;
    /* In ihrer eigenen Schrift — sonst sieht man nicht, worum es geht. */
    if (vorhanden) wort.style.fontFamily = '"' + name + '", serif';

    const satz = document.createElement('span');
    satz.className = 'schriftprobe-knopf__satz';
    satz.textContent = vorhanden ? LESESCHRIFTEN_SATZ[name]
                                 : 'Noch nicht geholt — siehe Erweitert.';

    knopf.append(wort, satz);
    knopf.addEventListener('click', () => {
      if (!vorhanden || !griffe.grundschriftSetzen) return;
      griffe.grundschriftSetzen(name === jetzt ? "" : name, undefined);
      schriftenZeigen();
      leseschriftenZeigen();
    });
    kasten.appendChild(knopf);
  }
}

function schriftenZeigen() {
  const wahl = $('einst-schrift');
  const alle = griffe.schriften();
  const jetzt = griffe.schriftJetzt();

  wahl.innerHTML = '';
  /* „Wie voreingestellt" statt eines Namens: Wer nie etwas eingestellt
     hat, soll nicht raten müssen, welche der 900 Schriften gerade gilt.
     Voreingestellt ist seit dem Umbau OpenDyslexic — die Schrift, für
     deren Leser dieses Programm gebaut ist. */
  const grund = document.createElement('option');
  grund.value = '';
  grund.textContent = 'Wie voreingestellt (OpenDyslexic)';
  wahl.appendChild(grund);
  /* Nach Gruppen, mit den Leseschriften zuoberst.

     Vorher standen alle neunhundert in einer Reihe, alphabetisch. Wer
     OpenDyslexic suchte — die Schrift, deretwegen viele überhaupt hier
     sind —, musste bis zum O rollen und den Namen genau kennen. Die
     Schriftkiste im Band macht es seit jeher richtig; diese Liste nicht. */
  const lesbar = griffe.leseschriften ? griffe.leseschriften() : [];
  const uebrige = alle.filter((n) => !lesbar.includes(n));

  const gruppeBauen = (titel, namen) => {
    if (!namen.length) return;
    const kiste = document.createElement('optgroup');
    kiste.label = titel;
    for (const name of namen) {
      const o = document.createElement('option');
      o.value = name; o.textContent = name;
      if (name === jetzt) o.selected = true;
      kiste.appendChild(o);
    }
    wahl.appendChild(kiste);
  };
  gruppeBauen('Leichter zu lesen', lesbar);
  gruppeBauen('Alle Schriften', uebrige);
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
  flaecheZeigen();
}

/* Die Wahl der Oberfläche: welches Bild den Rand trägt, und welcher Satz
   darunter steht.

   Die beiden Sätze stehen hier und nicht im Fenster, weil sie zusammen
   gelesen werden müssen — sie sind ein Vergleich, kein Beipackzettel.
   Getrennt in zwei <p> im HTML wären sie beim nächsten Umbau auseinander
   gelaufen. */
/* Die Sätze sind nach der Vorlage gebaut: erst, was die Fassung IST,
   dann, für WEN sie gedacht ist. LibreOffice schreibt „Die standardmäßige
   Benutzeroberfläche … Vorgesehen für Benutzer, die mit der klassischen
   Oberfläche vertraut sind." Dieselben zwei Sätze, in Kays Sprache. */
const FLAECHEN_SATZ = {
  leisten:
    'Menüleiste oben, darunter zwei Zeilen mit allen Werkzeugen. Nichts '
  + 'ist weggeklappt, nichts muss man aufsuchen — dafür ist es viel auf '
  + 'einmal.\n'
  + 'Vorgesehen für alle, denen die klassische Oberfläche vertraut ist — '
  + 'etwa aus LibreOffice.',
  register:
    'Menüleiste oben, darunter Reiter: Start, Einfügen, Layout. Jeder '
  + 'Reiter zeigt nur seine eigenen Werkzeuge, in Gruppen mit Namen '
  + 'darunter.\n'
  + 'Vorgesehen für alle, die weniger auf einmal sehen wollen — und für '
  + 'alle, die es aus Word kennen.',
};

/* ------------------------------------------------------------
   DIE ERKLÄRZEILE

   Zu fast jedem Feld dieser Seiten steht im Fenster ein
   <em class="feld__satz"> mit einem Satz, der sagt, was die Einstellung
   tut — hundertvierzig Stück. Die Stilvorlage blendet sie aus, und das aus
   gutem Grund: untereinander gestellt brauchten sie die dreifache Höhe,
   und aus der Seite wurde eine Wand.

   Hier wird immer nur EINER hervorgeholt: der zu dem Feld, auf dem der
   Zeiger steht oder das den Tastaturfokus hat. Die Seite wird dadurch
   keine Zeile höher, nichts klappt auf, nichts springt.

   EIN HORCHER AM GANZEN BEREICH, nicht hundertvierzig einzelne. Teile der
   Seiten entstehen erst beim Aufgehen; einzeln angehängte Horcher hätten
   die später gebauten Felder nicht erwischt.
   ------------------------------------------------------------ */

const ERKLAERUNG_LEER = 'Zeig auf eine Einstellung — hier steht, was sie tut.';

/* Der Name des Feldes ohne seinen Satz.

   Bei den Schaltern steckt der Satz INNERHALB der Beschriftung:
   <span class="feld__name">Lineal <em class="feld__satz">…</em></span>.
   Einfach textContent zu nehmen ergäbe „Lineal Zentimeter über dem
   Blatt…" — Name und Erklärung in einem Wortbrei. Also eine Kopie machen,
   den Satz herausnehmen, dann lesen. */
function feldName(feld) {
  const name = feld.querySelector('.feld__name');
  if (!name) return '';
  const kopie = name.cloneNode(true);
  for (const satz of kopie.querySelectorAll('.feld__satz')) satz.remove();
  return kopie.textContent.replace(/\s+/g, ' ').trim();
}

function erklaerungLeeren() {
  const zeile = $('einst-erklaerung');
  if (!zeile || !zeile.classList) return;
  zeile.textContent = ERKLAERUNG_LEER;
  zeile.classList.add('erklaerzeile--leer');
}

function erklaerungSetzen(feld) {
  const zeile = $('einst-erklaerung');
  if (!zeile || !zeile.classList) return;
  const kasten = feld && feld.querySelector ? feld.querySelector('.feld__satz') : null;
  const satz = kasten ? kasten.textContent.replace(/\s+/g, ' ').trim() : '';
  /* Kein Satz geschrieben: dann die Anleitung stehen lassen statt den
     Namen allein — „Lineal" erklärt nichts. */
  if (!satz) { erklaerungLeeren(); return; }

  zeile.classList.remove('erklaerzeile--leer');
  zeile.textContent = '';
  /* Alles in EIN Stück: Die Zeile ist ein Flex-Kasten, damit ein kurzer
     Satz senkrecht in der Mitte steht. Name und Satz einzeln hineingelegt
     wären zwei Flex-Teile — der Name bekäme eine eigene Spalte und bräche
     darin um, statt im Fließtext zu stehen. */
  const stueck = document.createElement('span');
  const name = feldName(feld);
  if (name) {
    const fett = document.createElement('b');
    fett.textContent = name;
    stueck.append(fett, document.createTextNode(' — '));
  }
  stueck.append(document.createTextNode(satz));
  zeile.append(stueck);
}

function erklaerzeileVerdrahten() {
  const bereich = $('einst-bereiche');
  if (!bereich || !bereich.addEventListener) return;

  const feldUnter = (fall) => {
    const ziel = fall.target;
    return ziel && ziel.closest ? ziel.closest('.feld') : null;
  };

  /* Die Maus. pointerover statt mouseover: So zählt auch der Finger auf
     einem Bildschirm, den man anfassen kann. */
  bereich.addEventListener('pointerover', (fall) => {
    const feld = feldUnter(fall);
    if (feld) erklaerungSetzen(feld);
  });
  bereich.addEventListener('pointerleave', erklaerungLeeren);

  /* Die Tastatur. Wer sich mit Tabulator durch die Seite arbeitet, braucht
     dieselbe Erklärung — und für ihn ist sie wichtiger als für den, der
     mit der Maus darüberfährt. */
  bereich.addEventListener('focusin', (fall) => {
    const feld = feldUnter(fall);
    if (feld) erklaerungSetzen(feld);
  });
  bereich.addEventListener('focusout', (fall) => {
    /* Nur leeren, wenn der Fokus den Bereich wirklich verlässt — sonst
       flackerte die Zeile bei jedem Sprung von Feld zu Feld. */
    const hin = fall.relatedTarget;
    if (!hin || !bereich.contains(hin)) erklaerungLeeren();
  });

  erklaerungLeeren();
}

/* Der Weg zur Wahl der Oberfläche.

   Sie steht unten auf der Seite „Ansicht", hinter sechsundzwanzig
   Häkchen — Kay hat sie beim ersten Hinsehen nicht gefunden, und das
   war kein Zufall: Die Seite ist doppelt so hoch wie das Fenster. Wer
   die Oberfläche umstellen will, sucht sie im Menü, nicht am Fuß einer
   Optionenseite.

   Deshalb springt Ansicht ▸ Oberfläche ▸ Benutzeroberfläche hierher,
   statt ein zweites, ärmeres Fenster mit denselben zwei Wörtern
   aufzumachen. Eine Einstellung, eine Stelle — aber zwei Wege dorthin. */
function flaecheAnspringen() {
  /* Aus dem Menü heraus steht die Seite noch zu — dann muss sie erst
     aufgehen. Vom Knopf auf der Schnellzugriff-Seite aus ist sie längst
     offen, und oeffnen() frischt sie nur auf. Beides ist gutartig. */
  if (!offen) oeffnen('ansicht');
  bereichZeigen('ansicht');
  const wahl = $('einst-flaeche');
  if (!wahl || !wahl.scrollIntoView) return;
  wahl.scrollIntoView({ block: 'center' });
  /* Auf den Knopf der gewählten Fassung, nicht auf den Kasten: Ein <div>
     nimmt keinen Fokus an, und die Tastatur stünde im Leeren. */
  const gewaehlt = wahl.querySelector('input:checked')
                || wahl.querySelector('input');
  if (gewaehlt) gewaehlt.focus();
}

function flaecheZeigen() {
  const jetzt = griffe.flaecheJetzt();
  for (const knopf of document.querySelectorAll('input[name="einst-flaeche-wahl"]')) {
    knopf.checked = knopf.value === jetzt;
  }
  /* Welches Bild in der Vorschau steht, sagt das Attribut am Kasten — das
     Umschalten selbst macht die Stilvorlage. */
  $('einst-flaeche').dataset.fassung = jetzt;
  $('einst-flaeche-satz').textContent = FLAECHEN_SATZ[jetzt] || '';
}

/* Die Prüfsprache steht an zwei Stellen: auf der Seite „Sprache", wo man
   sie sucht, und auf der Seite „Rechtschreibprüfung", wo WPS sie führt.
   Beide zeigen denselben Wert und stellen denselben um — ein Feld, zwei
   Stellen, ein Zustand. */
function spracheZeigen() {
  const jetzt = griffe.pruefspracheJetzt();
  for (const id of ['einst-pruefsprache', 'einst-pruefsprache2']) {
    const wahl = $(id);
    if (!wahl || !wahl.appendChild) continue;
    wahl.innerHTML = '';
    for (const [kennung, name] of griffe.pruefsprachen()) {
      const o = document.createElement('option');
      o.value = kennung; o.textContent = name;
      if (kennung === jetzt) o.selected = true;
      wahl.appendChild(o);
    }
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
  spracheKnopfZeigen();
  $('einst-sprache-knopf').addEventListener('click', uebersetzungsSpracheOeffnen);

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
    /* Die Vorbelegung „Standard (…)" in der KI-Konfiguration nennt den
       Namen dieses Modells — bei einem Wechsel muss sie mitziehen. */
    aufgabenZeigen();
    griffe.neuZeichnen();
  });

  $('einst-anbieter-neu').addEventListener('click', eigenenAnbieterHinzufuegen);
  $('einst-modelle-liste').addEventListener('click', modelleListeOeffnen);

  $('einst-assistenten-neu').addEventListener('click',
    () => griffe.assistentErstellen(eigeneAssistentenZeigen));

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
    spracheKnopfZeigen();
    modellHinweisZeigen();
    gedaechtnisZeigen();
    eigeneAnbieterZeigen();
    eigeneAssistentenZeigen();
    aufgabenZeigen();
    griffe.neuZeichnen();

    $('einst-gelernt-stand').textContent = 'Eingespielt: ' + ergebnis.neueWoerter
      + ' Schreibweisen, ' + ergebnis.neueRuhe + ' Wörter in Ruhe, '
      + ergebnis.neueAssistenten + ' eigene Assistenten. '
      + 'Was hier schon stand, blieb erhalten.';
  });

  /* Alle Schalter über einen Kamm — siehe schalterVerdrahten. Jeder geht
     denselben Weg wie sein Zwilling im Band; sonst hätten zwei Stellen
     dieselbe Sache zu sagen und widersprächen sich beim nächsten Start. */
  schalterVerdrahten();

  $('einst-endung').addEventListener('change', () => {
    griffe.endungSetzen($('einst-endung').value);
  });

  $('einst-zum-gedaechtnis').addEventListener('click', () => bereichZeigen('gedaechtnis'));
  /* Der Knopf „Register anpassen…" ist weg: Die beiden Listen stehen jetzt
     auf der Seite selbst, wie im WPS-Fenster. Das eigene Fenster gibt es
     weiterhin — es hängt am Rechtsklick aufs Band. */
  $('einst-vorlagenordner-auf').addEventListener('click', () => griffe.vorlagenOrdner());

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
  /* Die zwei Knöpfe auf den neuen Seiten tun dasselbe wie die auf der
     Gedächtnis-Seite. Sie noch einmal zu bauen hieße, zwei Fassungen zu
     pflegen — sie leiten deshalb einfach weiter. */
  const weiterleiten = (von, zu) => {
    const knopf = $(von), ziel = $(zu);
    if (knopf && ziel) knopf.addEventListener('click', () => ziel.click());
  };
  weiterleiten('einst-sichern2', 'einst-sichern');
  weiterleiten('einst-einspielen2', 'einst-einspielen');

  /* „Zur Benutzeroberfläche" auf der Schnellzugriff-Seite: Sie steht auf
     der Seite Ansicht, und dorthin führt der Knopf. Ein Verweis, dem man
     nicht folgen kann, ist keiner. */
  erklaerzeileVerdrahten();

  const zurFlaeche = $('einst-zur-flaeche');
  if (zurFlaeche) zurFlaeche.addEventListener('click', flaecheAnspringen);

  /* Ein Horcher für beide Knöpfe, am gemeinsamen Kasten. Zwei einzelne
     hätten beim nächsten Zuwachs — eine dritte Fassung — vergessen werden
     können. */
  $('einst-flaeche').addEventListener('change', (fall) => {
    const knopf = fall.target;
    if (!knopf || knopf.name !== 'einst-flaeche-wahl') return;
    griffe.flaecheSetzen(knopf.value);
    flaecheZeigen();
  });

  const zweite = $('einst-pruefsprache2');
  if (zweite && zweite.addEventListener) zweite.addEventListener('change', () => {
    griffe.pruefspracheSetzen(zweite.value);
    spracheZeigen();
  });
  $('einst-pruefsprache').addEventListener('change', () => {
    griffe.pruefspracheSetzen($('einst-pruefsprache').value);
    spracheZeigen();
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

  $('einst-fassung').textContent = 'Lunivo-Office 1.2 · Prüfung und Wortschatz '
    + 'aus der Schreibhilfe';

  /* Die Wellenlinien setzt jetzt programm.js beim Start — hier ist nichts
     mehr zu tun. Die Prüfung des Browsers bleibt aus. */
}

verdrahten();

/* Menüband und Schnellmenü führen jetzt nur noch zur Optionsseite selbst
   (Einstellungen.oeffnen('ki')) — keine eigene Provider-/API-Konfiguration
   außerhalb von Optionen mehr, siehe Teil A2 des Auftrags. Der Dialog
   „Eigenen Anbieter hinzufügen" bleibt dadurch ausschließlich über den
   Knopf hier auf der Seite und über „Liste der KI-Modelle" erreichbar. */
return { oeffnen, schliessen, verbinde, offen: () => offen, gedaechtnisZeigen,
         flaecheAnspringen };
})();
