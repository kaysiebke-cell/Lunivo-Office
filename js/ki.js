/* ============================================================
   Die KI-Ebene — Korrigieren, Vorschläge, Übersetzen.

   Die Prüfung nebenan kommt ohne Internet aus und findet, was sich an
   Regeln festmachen lässt. Sie kann aber nicht wissen, wovon die Rede
   ist. „das" oder „dass" entscheidet sich am Sinn des Satzes, nicht am
   Wort — dafür ist das hier da.

   Zwei Wege, dieselbe Anfrage:
     · Claude im Netz  — braucht einen Schlüssel und Guthaben, antwortet
                         in Sekunden.
     · Ollama am Ort   — kostenlos, ohne Internet, der Text verlässt den
                         Rechner nicht. Bezahlt wird in Wartezeit.

   Alles, was hier gespeichert wird, hängt an eigenen Schlüsseln („sp."):
   Das Schreibprogramm fasst nichts an, was der Schreibhilfe-App gehört.
   Wer sein Gelerntes herüberholen will, nimmt „Einspielen" in den
   Einstellungen — das ist der bewusste Weg statt eines stillen Zugriffs.
   ============================================================ */
'use strict';

const KI = (() => {

const Speicher = {
  lies(name, ersatz) {
    try { const w = localStorage.getItem('sp.' + name); return w === null ? ersatz : JSON.parse(w); }
    catch (e) { return ersatz; }
  },
  schreib(name, wert) {
    try { localStorage.setItem('sp.' + name, JSON.stringify(wert)); } catch (e) { /* voll */ }
  },
  loesch(name) {
    try { localStorage.removeItem('sp.' + name); } catch (e) { /* egal */ }
  },
};

/* ============================================================
   1. Das Gedächtnis

   Die KI selbst lernt nichts: Jede Anfrage fängt bei null an. Merken kann
   sich nur dieses Programm — und das ist der bessere Ort. Was hier steht,
   bleibt auf dem Rechner, kostet nichts und wirkt auch ohne Internet.

   Gesammelt wird an genau einer Stelle: beim Druck auf „Ändern". Dort ist
   zweifelsfrei bekannt, was der Mensch wollte.
   ============================================================ */
const LERN_SCHWELLE = 5;      // so oft darf ein Kasten ungenutzt erscheinen

const Gedaechtnis = {
  _merker: null,

  lies() {
    if (this._merker) return this._merker;
    const g = Speicher.lies('gelernt', null);
    this._merker = {
      woerter: (g && g.woerter) || {},
      inRuhe:  (g && g.inRuhe)  || {},
      gezeigt: (g && g.gezeigt) || {},
    };
    return this._merker;
  },

  schreib(g) {
    this._merker = g;
    Speicher.schreib('gelernt', g);
    this.anPruefungGeben();
  },

  /* Die Prüfung hält ihre eigene, schlanke Fassung im Arbeitsspeicher.
     Ohne diese Zeile wüsste sie von dem, was auf der Platte liegt, nichts —
     dann fragte sie beim nächsten Start wieder nach längst Geklärtem. */
  anPruefungGeben() {
    const g = this.lies();
    Pruefung.Gelernt.daten.woerter = g.woerter;
    Pruefung.Gelernt.daten.inRuhe = g.inRuhe;
  },

  /* Beim Druck auf „Ändern". Gelernt wird nur, was sich auf das WORT
     bezieht: Ein fehlendes Komma gilt genau dort, wo es gefunden wurde —
     als Regel für immer wäre es Unfug. */
  merkeAenderung(fund) {
    if (!Pruefung.Gelernt.wortEbene(fund)) return;
    const wort = String(fund.alt).toLowerCase();
    const g = this.lies();
    g.woerter[wort] = fund.neu;
    delete g.gezeigt[wort];        // angenommen ist das Gegenteil von ignoriert
    delete g.inRuhe[wort];
    this.schreib(g);
  },

  /* Beim Anzeigen der Kästen. Wer denselben Kasten wieder und wieder
     stehen lässt, sagt damit: Das Wort ist richtig so. */
  merkeGezeigt(funde) {
    const g = this.lies();
    let geaendert = false;
    for (const fund of funde) {
      if (!Pruefung.Gelernt.wortEbene(fund)) continue;
      const wort = String(fund.alt).toLowerCase();
      if (g.woerter[wort] || g.inRuhe[wort]) continue;
      g.gezeigt[wort] = (g.gezeigt[wort] || 0) + 1;
      if (g.gezeigt[wort] >= LERN_SCHWELLE) {
        g.inRuhe[wort] = true;
        delete g.gezeigt[wort];
      }
      geaendert = true;
    }
    if (geaendert) this.schreib(g);
  },

  /* Der Steckbrief für die KI. Sie erinnert sich nicht — sie bekommt die
     Erinnerung bei jeder Anfrage frisch mit. Genannt werden nur die Wörter,
     die dieser Mensch wirklich oft falsch schreibt; eine lange Liste würde
     die eigentliche Anweisung verwässern. */
  steckbrief() {
    const g = this.lies();
    const teile = [];

    const paare = Object.entries(g.woerter).slice(-12);
    if (paare.length) {
      teile.push('Dieser Mensch schreibt erfahrungsgemäß diese Wörter falsch — '
        + 'achte besonders darauf: '
        + paare.map(([falsch, richtig]) => falsch + ' statt ' + richtig).join(', ') + '.');
    }

    const ruhe = Object.keys(g.inRuhe).slice(0, 12);
    if (ruhe.length) {
      teile.push('Diese Wörter sind so gewollt und bleiben unangetastet: '
        + ruhe.join(', ') + '.');
    }

    return teile.length ? ' ' + teile.join(' ') : '';
  },

  stand() {
    const g = this.lies();
    return { woerter: Object.keys(g.woerter).length, inRuhe: Object.keys(g.inRuhe).length };
  },

  leeren() {
    this._merker = null;
    Speicher.loesch('gelernt');
    this.anPruefungGeben();
  },
};

/* ============================================================
   2. Für wen der Text ist

   „Klarer" heißt beim Amt etwas anderes als in einer Nachricht an den
   Nachbarn. Die Wahl steht in der Seitenleiste gleich neben den Knöpfen.
   ============================================================ */
const EMPFAENGER = {
  'egal': {
    anweisung:
      'Lass den Tonfall genau so, wie er im Text steht: Förmliches bleibt '
      + 'förmlich, Lockeres bleibt locker. Ändere die Wortwahl nur da, wo sie '
      + 'falsch ist.',
  },
  'Amt': {
    anweisung:
      'Der Text geht an eine Behörde — Amt, Jobcenter, Krankenkasse, '
      + 'Versicherung, Gericht. Halte den Tonfall durchgehend förmlich und '
      + 'höflich: Siezen, vollständige Sätze, keine Umgangssprache, keine '
      + 'Abkürzungen mitten im Satz. Sachlich bleiben auch dort, wo der Text '
      + 'ärgerlich klingt — der Vorwurf darf inhaltlich stehen bleiben, aber im '
      + 'ruhigen Ton. Stehen Anrede, Betreff oder ein Aktenzeichen schon da, '
      + 'bring sie in die übliche Form; fehlen sie, erfinde sie nicht.',
  },
  'Arbeit': {
    anweisung:
      'Der Text geht an jemanden aus dem Beruf — Chefin, Kollege, Kundschaft. '
      + 'Höflich und knapp: keine Ausschmückung, keine Floskelketten, aber auch '
      + 'nicht schroff. Ob geduzt oder gesiezt wird, entscheidet der Text — '
      + 'dreh das nicht um.',
  },
  'Freunde': {
    anweisung:
      'Der Text geht an jemanden, den man kennt — Familie, Freundin, Nachbar. '
      + 'Duzen, freundlich und zugewandt, kurze Sätze, ruhig so, wie man redet. '
      + 'Nicht flapsig und nicht anbiedernd. Emojis, Ausrufezeichen und Anreden '
      + 'wie „Hey" bleiben stehen.',
  },
  'Forum': {
    anweisung:
      'Der Text wird öffentlich gelesen — Forum, Kommentar, Bewertung, '
      + 'soziales Netz. Er muss auch für Fremde verständlich sein, die die '
      + 'Vorgeschichte nicht kennen: klare Sätze, Absätze statt eines Blocks. '
      + 'Geduzt wird, wie es dort üblich ist. Nicht belehrend — eine deutliche '
      + 'Meinung darf deutlich bleiben, aber ohne Beleidigung.',
  },
  'Bewerbung': {
    anweisung:
      'Der Text ist eine Bewerbung oder gehört dazu. Siezen, förmlich, aber '
      + 'nicht steif. Selbstbewusst ohne Angeberei: klare Aussagesätze statt '
      + '„ich würde gerne" und statt Floskelketten. Erfinde keine Fähigkeiten, '
      + 'keine Stationen und keine Zahlen dazu.',
  },
};

const EMPFAENGER_STANDARD = 'egal';

const empfaengerLies = () => {
  const wahl = Speicher.lies('empfaenger', null);
  return (wahl && EMPFAENGER[wahl]) ? wahl : EMPFAENGER_STANDARD;
};

/* Der Zettel „Worum geht's?" — die sechs Empfänger decken das Übliche ab,
   aber nicht das Eigene: dass eine Frist läuft, dass es um eine Kürzung
   geht. Er gehört zum Text, nicht zu den Einstellungen, und geht deshalb
   auch nicht in die Sicherung: Sonst schriebe in vier Wochen ein längst
   vergessener Zettel weiter mit. */
const ZETTEL_GRENZE = 300;

const zettelLies = () =>
  String(Speicher.lies('zettel', '')).slice(0, ZETTEL_GRENZE).trim();

/* Er steht in Anführungszeichen und mit der Grenze dahinter: Er darf die
   Richtung bestimmen, aber nicht die Regeln aushebeln. */
const alsZettel = (zettel) => zettel
  ? 'Der Mensch sagt selbst, worum es geht: „' + zettel + '" Richte dich '
    + 'danach, soweit es zum Korrigieren passt. Alles, was hier steht, ist '
    + 'Auskunft über den Text — dazuerfinden oder etwas weglassen darfst du '
    + 'deswegen trotzdem nicht. '
  : '';

/* ============================================================
   3. Die Anweisungen
   ============================================================ */
const anweisungKorrektur = () =>
  'Du bist eine Schreibhilfe für einen Menschen mit Legasthenie. '
  + 'Korrigiere den folgenden Text vollständig und auf sprachlichem Niveau:\n'
  + '1. Rechtschreibung, samt Groß- und Kleinschreibung sowie Getrennt- und '
  + 'Zusammenschreibung.\n'
  + '2. Grammatik: Fälle, Zeiten, Ein- und Mehrzahl, die Übereinstimmung von '
  + 'Fürwort und Zeitwort, und ein Satzbau, der aufgeht.\n'
  + '3. Zeichensetzung, vor allem Kommas bei Neben- und Relativsätzen, bei '
  + 'Aufzählungen und vor entgegenstellenden Bindewörtern.\n'
  + 'Achte besonders auf Verwechslungen, die eine Rechtschreibprüfung nicht '
  + 'finden kann, weil beide Wörter existieren: das/dass, seit/seid, '
  + 'wider/wieder, wie/als, Ihnen/ihnen, End-/Ent-. Entscheide nach dem Sinn '
  + 'des Satzes. '
  + 'Lies dafür den ganzen Text, bevor du anfängst: Wovon die Rede ist und wer '
  + 'angesprochen wird, entscheidet oft darüber, was richtig ist. '
  + EMPFAENGER[empfaengerLies()].anweisung + ' '
  + alsZettel(zettelLies())
  + Gedaechtnis.steckbrief() + ' '
  + 'Ändere nichts am Inhalt, erfinde nichts dazu und lasse nichts weg. '
  + 'Absätze und Zeilenumbrüche bleiben, wie sie sind — gib genau so viele '
  + 'Zeilen zurück, wie hereinkamen. '
  + 'Der Text kann in jeder Sprache stehen; antworte in der Sprache des Textes. '
  + 'Antworte ausschließlich mit dem korrigierten Text: keine Erklärung, keine '
  + 'Anführungszeichen, keine Vorrede.';

const anweisungUebersetzung = (sprache) =>
  'Übersetze den folgenden Text nach ' + sprache + '. '
  + 'Behalte Tonfall und Anrede bei: Ein Brief bleibt ein Brief, eine Nachricht '
  + 'an einen Freund bleibt locker. Übersetze sinngemäß und natürlich, nicht Wort '
  + 'für Wort. Ist der Text schon auf ' + sprache + ', gib ihn unverändert zurück. '
  + 'Absätze und Zeilenumbrüche bleiben, wie sie sind — gib genau so viele '
  + 'Zeilen zurück, wie hereinkamen. '
  + 'Antworte ausschließlich mit der Übersetzung: keine Erklärung, keine '
  + 'Anführungszeichen, keine Vorrede.';

/* Umformulieren ist etwas anderes als Korrigieren: Hier darf sich die
   Wortwahl ändern. Deshalb kommt es nicht als fertiger Text zurück, sondern
   als Liste einzelner Sätze — jeder mit Begründung, jeder einzeln anzunehmen
   oder liegenzulassen. Der Text gehört dem Menschen, nicht der Maschine. */
const anweisungVorschlaege = () =>
  'Du bist eine Schreibhilfe für einen Menschen mit Legasthenie. Suche im '
  + 'folgenden Text die Sätze, die schwer zu lesen oder umständlich '
  + 'sind, und schlage für jeden eine klarere Fassung vor. '
  + 'Regeln: Ändere nichts am Inhalt und erfinde nichts dazu. '
  + EMPFAENGER[empfaengerLies()].anweisung + ' '
  + alsZettel(zettelLies())
  + 'Benutze einfache, gebräuchliche Wörter und kurze Sätze. '
  + 'Der Text kann in jeder Sprache stehen. "neu" bleibt in der Sprache des '
  + 'Textes, "grund" schreibst du immer auf Deutsch. '
  + 'Nimm höchstens sechs Sätze, nur die, bei denen es wirklich hilft; ist der '
  + 'Text schon gut, nimm weniger oder keinen. '
  + '"alt" ist der Satz zeichengenau aus dem Text — nicht kürzen, nicht '
  + 'glätten, nichts hinzufügen; er muss sich Zeichen für Zeichen im Text '
  + 'wiederfinden. "neu" ist die klarere Fassung, "grund" sagt in höchstens '
  + 'acht Wörtern, warum das leichter ist. '
  + 'Gibt es nichts zu verbessern, bleibt die Liste leer.';

/* Der Bauplan der Antwort. Er wird als JSON-Schema mitgeschickt, und die
   Antwort MUSS ihm entsprechen — kein Fließtext, kein Code-Zaun, keine
   fehlenden Felder. Was früher als Bitte in der Anweisung stand, ist damit
   eine Zusage der Schnittstelle. */
const VORSCHLAG_BAUPLAN = {
  type: 'object',
  properties: {
    vorschlaege: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          alt:   { type: 'string' },
          neu:   { type: 'string' },
          grund: { type: 'string' },
        },
        required: ['alt', 'neu', 'grund'],
        additionalProperties: false,
      },
    },
  },
  required: ['vorschlaege'],
  additionalProperties: false,
};

const SPRACHEN = [
  'Englisch', 'Deutsch', 'Türkisch', 'Russisch', 'Ukrainisch', 'Polnisch',
  'Rumänisch', 'Arabisch', 'Französisch', 'Spanisch', 'Italienisch',
  'Griechisch', 'Niederländisch', 'Portugiesisch',
];

/* ============================================================
   4. Was die Anfrage gekostet hat

   Die Antwort sagt, wie viele Token hinein- und hinausgegangen sind. Mal
   dem Preis des Modells ergibt das den Betrag — auf den Bruchteil eines
   Cents genau, nicht geschätzt. Gerechnet wird in US-Cent, so rechnet
   Anthropic ab.
   ============================================================ */
const PREISE = {                       // Dollar je Million Token
  'claude-opus-5':    { hinein: 5, heraus: 25 },
  'claude-sonnet-5':  { hinein: 3, heraus: 15 },
  'claude-haiku-4-5': { hinein: 1, heraus: 5  },
};

function centFuer(modell, verbrauch) {
  if (!verbrauch) return null;
  const name = Object.keys(PREISE).find((k) => String(modell || '').startsWith(k));
  if (!name) return null;
  const preis = PREISE[name];
  const hinein = (verbrauch.input_tokens || 0)
               + (verbrauch.cache_read_input_tokens || 0)
               + (verbrauch.cache_creation_input_tokens || 0);
  const heraus = verbrauch.output_tokens || 0;
  return (hinein * preis.hinein + heraus * preis.heraus) / 1e6 * 100;
}

function alsGeld(cent) {
  if (cent === null || cent === undefined) return '';
  if (cent < 1) return 'unter 1 Cent';
  return (cent / 100).toFixed(2).replace('.', ',') + ' $';
}

function merkeKosten(cent) {
  if (!cent) return;
  const bisher = Speicher.lies('kosten', 0);
  Speicher.schreib('kosten', bisher + cent);
}

const kostenStand = () => Speicher.lies('kosten', 0);
const kostenLeeren = () => Speicher.loesch('kosten');

/* ============================================================
   5. Welches Modell?
   ============================================================ */
const OLLAMA_ADRESSE = 'http://localhost:11434';
const OLLAMA_MARKE = 'ollama:';
const OLLAMA_GEDULD = 600000;        // zehn Minuten: ohne Grafikkarte dauert es

const modellJetzt = () => Speicher.lies('modell', 'claude-opus-5');
const modellSetzen = (wert) => Speicher.schreib('modell', wert);

const istLokal = (modell) => String(modell || '').startsWith(OLLAMA_MARKE);

/* „ollama:qwen3:8b" → „qwen3:8b". Der Doppelpunkt gehört zum Modellnamen
   dazu, deshalb wird nur die Marke vorne abgeschnitten, nicht gesplittet. */
const lokalerName = (modell) => String(modell || '').slice(OLLAMA_MARKE.length);

const schluesselLies = () => Speicher.lies('apiKey', '');
const schluesselSetzen = (wert) => Speicher.schreib('apiKey', String(wert).trim());
const schluesselLoeschen = () => Speicher.loesch('apiKey');

/* Ein lokales Modell braucht keinen Schlüssel — ohne diese Unterscheidung
   blieben die Knöpfe dort für immer grau. */
const verfuegbar = () => istLokal(modellJetzt()) || !!schluesselLies();

/* ============================================================
   6. Eine Anfrage, drei Anwendungen

   Korrigieren, Übersetzen und Vorschläge unterscheiden sich nur in der
   Anweisung — alles andere ist dasselbe.
   ============================================================ */
async function anfrage(anweisung, text, bauplan) {
  return istLokal(modellJetzt())
    ? ollamaAnfrage(anweisung, text, bauplan)
    : claudeAnfrage(anweisung, text, bauplan);
}

async function claudeAnfrage(anweisung, text, bauplan) {
  const schluessel = schluesselLies();
  const modell = modellJetzt();
  if (!schluessel) {
    return { fehler: 'Es ist kein Schlüssel gespeichert. Schreibhilfe → Einstellungen.' };
  }

  const bitte = {
    model: modell,
    /* Reichlich Platz: Das Nachdenken zählt gegen dieselbe Grenze wie die
       Antwort. Mit 4000 könnte ein langer Brief abgeschnitten zurückkommen.
       Bezahlt wird, was wirklich verbraucht wird — eine hohe Grenze kostet
       für sich genommen nichts. */
    max_tokens: 16000,
    system: anweisung,
    messages: [{ role: 'user', content: text }],
  };

  const ausgabe = {};

  if (modell !== 'claude-haiku-4-5') {
    // „effort" gibt es nur bei den neueren Modellen — Haiku wirft damit einen Fehler.
    ausgabe.effort = 'low';
    /* Nachdenken bleibt an. Abgeschaltet schreibt Opus 5 gelegentlich seine
       internen <thinking>-Klammern mit in die Antwort — und die landete hier
       ungefiltert im Brief. Es kostet ein paar Sekunden und macht die
       Korrektur obendrein besser. */
    bitte.thinking = { type: 'adaptive' };
  }

  /* Der Bauplan ist ein JSON-Schema. Damit ist die Antwort keine Prosa mehr,
     sondern zwingend eine Struktur in genau dieser Form — die KI KANN gar
     nicht mit „Der Text ist bereits gut verständlich." antworten. */
  if (bauplan) ausgabe.format = { type: 'json_schema', schema: bauplan };

  if (Object.keys(ausgabe).length) bitte.output_config = ausgabe;

  // Ohne Abbruch wartet „fetch" notfalls ewig — etwa wenn mitten in der
  // Anfrage das Netz wegbricht. Dann bliebe der Knopf für immer grau.
  const abbruch = new AbortController();
  const wecker = setTimeout(() => abbruch.abort(), 90000);

  try {
    const antwort = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': schluessel,
        'anthropic-version': '2023-06-01',
        // Erlaubt den Aufruf direkt aus der Seite heraus
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify(bitte),
      signal: abbruch.signal,
    });

    if (!antwort.ok) {
      const texte = {
        401: 'Der Schlüssel wird abgelehnt. Er wird nur bei der Erstellung einmal '
           + 'angezeigt — hast du ihn vollständig kopiert? Sonst auf '
           + 'console.anthropic.com einen neuen anlegen.',
        400: 'Die Anfrage wurde abgelehnt.',
        429: 'Zu viele Anfragen. Bitte kurz warten und noch einmal versuchen.',
      };
      let zusatz = '';
      try { zusatz = (await antwort.json())?.error?.message || ''; } catch (e) { /* egal */ }
      // Kein Guthaben mehr: Das steht als englischer Fließtext in der Antwort,
      // und niemand soll raten müssen, was „credit balance is too low" heißt.
      if (/credit balance/i.test(zusatz)) {
        return { fehler: 'Das Guthaben ist aufgebraucht. In den Einstellungen steht '
                       + 'ein Verweis zum Aufladen.' };
      }
      return { fehler: (texte[antwort.status] || 'Fehler ' + antwort.status)
                     + (zusatz ? ' (' + zusatz + ')' : '') };
    }

    const daten = await antwort.json();
    if (daten.stop_reason === 'refusal') {
      return { fehler: 'Die KI wollte diesen Text nicht bearbeiten.' };
    }

    const ergebnis = (daten.content || [])
      .filter((block) => block.type === 'text')
      .map((block) => block.text)
      .join('')
      .trim();

    const cent = centFuer(daten.model || modell, daten.usage);
    return ergebnis ? { ergebnis, cent } : { fehler: 'Es kam keine Antwort zurück.' };

  } catch (fehler) {
    // Reihenfolge wichtig: „navigator.onLine" meldet auch dann noch „online",
    // wenn die Verbindung längst hängt. Der Abbruch ist das sichere Zeichen.
    if (fehler.name === 'AbortError') {
      return { fehler: 'Die KI hat zu lange gebraucht. Bitte noch einmal versuchen.' };
    }
    if (!navigator.onLine) return { fehler: 'Kein Internet. Die KI braucht eine Verbindung.' };
    return { fehler: 'Es hat nicht geklappt: ' + fehler.message };
  } finally {
    clearTimeout(wecker);
  }
}

/* ------------------------------------------------------------
   Dieselbe Anfrage, nur an den eigenen Rechner.

   Ollama ist kein Programm mit Fenster, sondern ein Dienst im Hintergrund:
   Er läuft mit dem Rechner an und wartet auf Port 11434. Kein Schlüssel,
   keine Kosten, kein Internet — der Text verlässt das Gerät nicht. Bezahlt
   wird in Wartezeit: Ohne Grafikkarte rechnet ein 8-Milliarden-Modell an
   einem Brief mehrere Minuten, wo Claude Sekunden braucht.
   ------------------------------------------------------------ */
async function ollamaAnfrage(anweisung, text, bauplan) {
  const modell = lokalerName(modellJetzt());
  if (!modell) return { fehler: 'Es ist noch kein Modell gewählt. In den Einstellungen nachholen.' };

  const bitte = {
    model: modell,
    /* Stückweise ankommen lassen bringt nichts: Der Text wird ohnehin erst
       am Stück eingesetzt. */
    stream: false,
    /* Die Anweisung steht als „system", genau wie bei Claude — sonst
       korrigierte der eigene Rechner nach anderen Regeln. */
    messages: [
      { role: 'system', content: anweisung },
      { role: 'user',   content: text },
    ],
    /* Wenig Fantasie: Korrigieren ist kein Dichten. Ohne diese Zeile
       schreiben die kleinen Modelle gern ganze Sätze um. */
    options: { temperature: 0.2 },
    /* Denkmodelle wie qwen3 grübeln sonst minutenlang, bevor das erste Wort
       kommt. Modelle, die gar nicht denken können, lehnen die Zeile mit
       Fehler 400 ab; dann fragen wir gleich noch einmal ohne sie. */
    think: false,
  };
  if (bauplan) bitte.format = bauplan;

  const abbruch = new AbortController();
  const wecker = setTimeout(() => abbruch.abort(), OLLAMA_GEDULD);

  const schicke = () => fetch(OLLAMA_ADRESSE + '/api/chat', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(bitte),
    signal: abbruch.signal,
  });

  try {
    let antwort = await schicke();

    if (antwort.status === 400) {
      const grund = await antwort.text().catch(() => '');
      if (/think/i.test(grund)) {
        delete bitte.think;
        antwort = await schicke();
      } else {
        return { fehler: 'Ollama hat die Anfrage abgelehnt'
                       + (grund ? ' (' + grund + ')' : '') + '.' };
      }
    }

    if (!antwort.ok) {
      let grund = '';
      try { grund = (await antwort.json())?.error || ''; } catch (e) { /* egal */ }
      if (antwort.status === 404) {
        return { fehler: 'Das Modell „' + modell + '" liegt nicht auf diesem Rechner. '
                       + 'In den Einstellungen ein anderes wählen — oder es im '
                       + 'Terminal holen: ollama pull ' + modell };
      }
      return { fehler: 'Ollama meldet Fehler ' + antwort.status
                     + (grund ? ' (' + grund + ')' : '') };
    }

    const daten = await antwort.json();
    const ergebnis = ohneGruebeln(daten?.message?.content || '').trim();
    /* Kein Preis, kein Zähler: Der eigene Rechner schickt keine Rechnung. */
    return ergebnis ? { ergebnis } : { fehler: 'Es kam keine Antwort zurück.' };

  } catch (fehler) {
    if (fehler.name === 'AbortError') {
      return { fehler: 'Der eigene Rechner hat zu lange gebraucht. Ein kleineres '
                     + 'Modell in den Einstellungen geht deutlich schneller.' };
    }
    /* Ein blockierter Aufruf kommt nicht als Fehlernummer zurück, sondern gar
       nicht: „fetch" wirft dann einen TypeError. Ob der Dienst aus ist oder ob
       er dieser Seite bloß nicht antworten darf, sieht von hier aus gleich aus
       — deshalb nennt die Meldung beide Ursachen. */
    if (fehler instanceof TypeError) {
      return { fehler: 'Ollama ist unter ' + OLLAMA_ADRESSE + ' nicht zu erreichen. '
                     + 'Läuft der Dienst — und darf diese Seite ihn fragen? '
                     + 'Notfalls einmal mit OLLAMA_ORIGINS=* starten.' };
    }
    return { fehler: 'Es hat nicht geklappt: ' + fehler.message };
  } finally {
    clearTimeout(wecker);
  }
}

/* Denkmodelle schreiben ihr Grübeln in <think>-Klammern mit. Ollama trennt
   es sauber ab, sobald es vom Denken weiß — nur eben nicht bei jedem Modell.
   Was durchrutscht, hat im Brief eines Menschen nichts zu suchen. */
function ohneGruebeln(roh) {
  const ohne = String(roh).replace(/<think>[\s\S]*?<\/think>/gi, '');
  /* Eine Klammer, die nur zugeht: Alles davor war Grübeln. */
  return ohne.includes('</think>') ? ohne.slice(ohne.lastIndexOf('</think>') + 8) : ohne;
}

/* Welche Modelle liegen auf dem Rechner? Die Liste kommt vom Dienst selbst —
   eine fest eingebaute wäre schon falsch, sobald jemand ein Modell holt. */
async function ollamaModelle() {
  const antwort = await fetch(OLLAMA_ADRESSE + '/api/tags', { headers: { accept: 'application/json' } });
  if (!antwort.ok) throw new Error('Fehler ' + antwort.status);
  const daten = await antwort.json();
  return sortiereModelle((daten?.models || []).map((m) => m.name).filter(Boolean));
}

/* Alphabetisch allein wäre schädlich: „codellama" stünde ganz oben und damit
   als Vorauswahl da — ein Modell für Programmcode, das an einem Brief ans Amt
   nichts Gutes tut. Also sinken die Code-Modelle nach unten. */
function sortiereModelle(namen) {
  const fuerCode = (name) => /cod(e|er)/i.test(name);
  return namen.sort((a, b) => (fuerCode(a) - fuerCode(b)) || a.localeCompare(b));
}

/* Antworten auf eine Anfrage mit Bauplan kommen als Text an, der JSON
   enthält — mal blank, mal in einem Code-Zaun. Beides muss hier heraus. */
function alsJson(antwort) {
  const roh = String(antwort).trim().replace(/^```(?:json)?\s*|\s*```$/g, '');
  try { return JSON.parse(roh); } catch (e) { /* weiter unten */ }
  // Notnagel: die äußerste geschweifte Klammer suchen.
  const auf = roh.indexOf('{');
  const zu = roh.lastIndexOf('}');
  if (auf === -1 || zu <= auf) return null;
  try { return JSON.parse(roh.slice(auf, zu + 1)); } catch (e) { return null; }
}

/* ============================================================
   7. Die drei Anwendungen
   ============================================================ */

/** Den ganzen Text korrigieren. Gibt { text } oder { fehler } zurück. */
async function korrigieren(text) {
  const { ergebnis, fehler, cent } = await anfrage(anweisungKorrektur(), text);
  if (fehler) return { fehler };
  if (cent) merkeKosten(cent);
  return { text: ergebnis, cent };
}

/** Übersetzen. Dieselbe Anfrage, andere Anweisung. */
async function uebersetzen(text, sprache) {
  const { ergebnis, fehler, cent } = await anfrage(anweisungUebersetzung(sprache), text);
  if (fehler) return { fehler };
  if (cent) merkeKosten(cent);
  return { text: ergebnis, cent };
}

/** Vorschläge holen. Gibt { vorschlaege } oder { fehler } zurück. */
async function vorschlaege(text) {
  const { ergebnis, fehler, cent } = await anfrage(anweisungVorschlaege(), text, VORSCHLAG_BAUPLAN);
  if (fehler) return { fehler };
  if (cent) merkeKosten(cent);

  const daten = alsJson(ergebnis);
  if (!daten || !Array.isArray(daten.vorschlaege)) {
    return { fehler: 'Die Antwort kam nicht in der erwarteten Form.' };
  }

  /* Nur was sich zeichengenau im Text wiederfindet, lässt sich auch
     einsetzen. Der Rest wäre ein Knopf, der ins Leere greift. */
  const brauchbar = daten.vorschlaege.filter((v) =>
    v && typeof v.alt === 'string' && typeof v.neu === 'string'
    && v.alt.trim() && v.neu.trim() && v.alt !== v.neu
    && text.includes(v.alt));

  return { vorschlaege: brauchbar, cent };
}

/** Synonyme für ein Wort — der Thesaurus.

    Die Wörterliste weiß, wie Wörter geschrieben werden, nicht was sie
    bedeuten. Für Bedeutungsverwandtes braucht es jemanden, der den Satz
    versteht — deshalb geht das nur mit KI.

    Der Satz drumherum geht mit: „Bank" ist im Park etwas anderes als in
    der Innenstadt. */
async function synonyme(wort, umgebung) {
  const anweisung =
    'Nenne gebräuchliche deutsche Wörter, die statt „' + wort + '" an dieser '
    + 'Stelle stehen könnten. Achte auf den Zusammenhang: Dasselbe Wort bedeutet '
    + 'je nach Satz Verschiedenes. '
    + 'Nimm einfache, geläufige Wörter — dieser Text wird von einem Menschen mit '
    + 'Legasthenie geschrieben, und ein seltenes Fremdwort hilft ihm nicht. '
    + 'Höchstens acht, jedes in der Form, in der es im Satz stehen müsste. '
    + 'Fällt dir nichts Passendes ein, bleibt die Liste leer.';

  const bauplan = {
    type: 'object',
    properties: { woerter: { type: 'array', items: { type: 'string' } } },
    required: ['woerter'],
    additionalProperties: false,
  };

  const { ergebnis, fehler, cent } = await anfrage(anweisung, umgebung || wort, bauplan);
  if (fehler) return { fehler, woerter: [] };
  if (cent) merkeKosten(cent);

  const daten = alsJson(ergebnis);
  if (!daten || !Array.isArray(daten.woerter)) {
    return { fehler: 'Die Antwort kam nicht in der erwarteten Form.', woerter: [] };
  }

  const sauber = daten.woerter
    .filter((w) => typeof w === 'string' && w.trim() && w.length < 40)
    .map((w) => w.trim())
    .filter((w) => w.toLowerCase() !== String(wort).toLowerCase());

  return { woerter: [...new Set(sauber)].slice(0, 8) };
}

/* ============================================================
   8. Die Sicherung — die Brücke zwischen den Geräten

   Handy, App und Schreibprogramm lernen jedes für sich. „Sichern" legt
   alles Gelernte als Text ab, „Einspielen" nimmt ihn anderswo wieder auf.

   Zwei Dinge bleiben bewusst draußen:
     · Der API-Schlüssel. Ein Schlüssel gehört nicht in einen Text, den man
       durch die Gegend schickt — er ist anderswo in einer Minute neu
       eingetragen.
     · Der Zähler „gezeigt". Er zählt Prüfungen auf DIESEM Gerät.

   Eingespielt wird ZUSAMMENGEFÜHRT, nicht ersetzt: Was hier schon gelernt
   war, bleibt. Sonst löschte die Reise vom Handy zum PC das Gelernte des
   PCs aus.
   ============================================================ */
const SICHERUNG_FASSUNG = 1;
const SICHERBAR = ['empfaenger', 'tonfall', 'modell', 'sprache'];
const SICHERUNG_GRENZE = 2000;              // so viele Wörter höchstens
const GELERNTES_WORT = /^[a-zäöüß-]{1,40}$/;

function sicherungBauen() {
  const g = Gedaechtnis.lies();
  const einstellungen = {};
  for (const name of SICHERBAR) {
    const wert = Speicher.lies(name, undefined);
    if (wert !== undefined) einstellungen[name] = wert;
  }
  return JSON.stringify({
    schreibhilfe: SICHERUNG_FASSUNG,
    woerter: g.woerter,
    inRuhe: g.inRuhe,
    einstellungen,
  });
}

/* Alles hier Ankommende ist ungeprüft — es kann aus jeder Quelle stammen
   und landet dauerhaft im Speicher. Deshalb wird jeder Eintrag einzeln
   geprüft und alles Unpassende stillschweigend übergangen. */
function sicherungEinspielen(roh) {
  let daten;
  try { daten = JSON.parse(String(roh).trim()); }
  catch (e) { return { fehler: 'Das war kein Sicherungs-Text.' }; }

  if (!daten || daten.schreibhilfe !== SICHERUNG_FASSUNG) {
    return { fehler: 'Das ist kein Sicherungs-Text der Schreibhilfe.' };
  }

  const g = Gedaechtnis.lies();
  let neueWoerter = 0;
  let neueRuhe = 0;

  for (const [falsch, richtig] of Object.entries(daten.woerter || {})) {
    if (Object.keys(g.woerter).length >= SICHERUNG_GRENZE) break;
    if (!GELERNTES_WORT.test(falsch)) continue;
    if (typeof richtig !== 'string' || !richtig.trim() || richtig.length > 60) continue;
    if (g.woerter[falsch] !== richtig) neueWoerter++;
    g.woerter[falsch] = richtig;
  }

  for (const wort of Object.keys(daten.inRuhe || {})) {
    if (Object.keys(g.inRuhe).length >= SICHERUNG_GRENZE) break;
    if (!GELERNTES_WORT.test(wort)) continue;
    if (!g.inRuhe[wort]) neueRuhe++;
    g.inRuhe[wort] = true;
  }

  Gedaechtnis.schreib(g);

  for (const [name, wert] of Object.entries(daten.einstellungen || {})) {
    if (SICHERBAR.includes(name)) Speicher.schreib(name, wert);
  }

  return { neueWoerter, neueRuhe };
}

/* Das Gelernte gilt ab dem ersten Zeichen — nicht erst, wenn jemand die
   Einstellungen aufmacht. */
Gedaechtnis.anPruefungGeben();

return {
  Speicher, Gedaechtnis,
  EMPFAENGER, EMPFAENGER_STANDARD, empfaengerLies,
  zettelLies, ZETTEL_GRENZE, SPRACHEN,
  verfuegbar, modellJetzt, modellSetzen, istLokal, lokalerName, OLLAMA_MARKE,
  schluesselLies, schluesselSetzen, schluesselLoeschen,
  ollamaModelle, korrigieren, uebersetzen, vorschlaege, synonyme,
  centFuer, alsGeld, kostenStand, kostenLeeren,
  sicherungBauen, sicherungEinspielen,
};
})();
