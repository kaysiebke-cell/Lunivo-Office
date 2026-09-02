/* ============================================================
   Die Prüfung — Rechtschreibung, Grammatik, Satzbau.

   Gesucht wird ausdrücklich nur, was ein Rechtschreibprüfer NICHT finden
   kann: das/dass, seit/seid, „wir hat", das fehlende Komma vor „weil",
   zusammengetippte Wörter. Beide Schreibweisen sind für sich genommen
   richtig — deshalb übersieht sie jede gewöhnliche Prüfung.

   Drei Sorten von Funden:
     fehler   sicher falsch — „Wir hat" wird zu „Wir haben"
     tipp     kommt drauf an — das Komma, das „dass". Noch einmal lesen.
     hinweis  nur zum Nachdenken — ein Satz mit 45 Wörtern. Nichts zu ersetzen.

   Lieber eine Lücke als ein falscher Alarm: Regeln, die auch richtige Sätze
   anmeckern würden, stehen mit Absicht nicht drin.

   ------------------------------------------------------------
   Woher das kommt

   Die Regeln stammen aus der Schreibhilfe (kaysiebke-cell/schreibhilfe,
   online/js/app.js) und sind dort über viele Fassungen gewachsen. Sie
   liegen hier als eigene Kopie: Dieses Programm ist eigenständig und
   braucht jenes Projekt nicht, um zu laufen.

   Der Wortschatz dazu steht in daten/regeln.js, die große Wörterliste in
   daten/woerter.txt.
   ============================================================ */
'use strict';

const Pruefung = (() => {

  /* Das Gedächtnis: Wörter, die schon einmal geändert wurden, und solche,
     die in Ruhe bleiben sollen — der Nachname, ein Wort aus der Gegend.
     Die Prüfung fragt es an vier Stellen. */
  const Gelernt = {
    daten: { woerter: {}, inRuhe: {} },
    wort: (w) => Gelernt.daten.woerter[String(w).toLowerCase()] || null,
    inRuhe: (w) => !!Gelernt.daten.inRuhe[String(w).toLowerCase()],
    /* Nur was ein einzelnes Wort richtigstellt, lässt sich lernen —
       ein fehlendes Komma nicht. */
    wortEbene: (fund) =>
      !!fund && fund.wortEbene === true &&
      typeof fund.alt === 'string' && typeof fund.neu === 'string' &&
      /^[A-Za-zÄÖÜäöüß-]+$/.test(fund.alt) &&
      fund.neu.trim() === fund.neu && fund.neu !== '',
  };

  const WOERTERBUCH = REGELDATEN.WOERTERBUCH;

  /* ------------------------------------------------------------
     Ist das überhaupt eine Korrektur?

     Eine Rechtschreibkorrektur sieht dem falschen Wort ähnlich: „vieleicht" →
     „vielleicht", „Termien" → „Termin". Androids Prüfer liefert aber auch dann
     einen Vorschlag, wenn er ein Wort schlicht nicht kennt — und dann rät er.
     Für „Zahnriemenspanner-Kettenrolle" schlug er „Unannehmlichkeiten" vor:
     kein gemeinsamer Buchstabe, nichts. Das ist kein Verschreiber, das ist ein
     fremdes Wort.

     Gemessen wird der Abstand (ein Buchstabe weg, dazu, ersetzt) im Verhältnis
     zur Wortlänge. Ein Drittel darf abweichen, mindestens aber ein Buchstabe —
     sonst fielen kurze Wörter wie „seid" → „seit" durch.
     ------------------------------------------------------------ */
  /* Zwei vertauschte Buchstaben zählen als EIN Handgriff — „shcon" ist ein
     Vertipper, kein anderes Wort. Genau so zählt es auch die Tippfehler-Regel
     weiter unten; zwei verschiedene Maßstäbe in einer App wären ein Fehler in
     sich. */
  function wortAbstand(a, b) {
    const zeilen = [Array.from({ length: b.length + 1 }, (_, i) => i)];
    for (let i = 1; i <= a.length; i++) {
      const zeile = new Array(b.length + 1);
      zeile[0] = i;
      for (let j = 1; j <= b.length; j++) {
        const kosten = a[i - 1] === b[j - 1] ? 0 : 1;
        zeile[j] = Math.min(
          zeilen[i - 1][j] + 1,            // Buchstabe weg
          zeile[j - 1] + 1,                // Buchstabe dazu
          zeilen[i - 1][j - 1] + kosten,   // ersetzt
        );
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          zeile[j] = Math.min(zeile[j], zeilen[i - 2][j - 2] + 1);   // vertauscht
        }
      }
      zeilen.push(zeile);
    }
    return zeilen[a.length][b.length];
  }

  function istKorrektur(falsch, richtig) {
    const a = String(falsch).toLowerCase();
    const b = String(richtig).toLowerCase();
    if (!a || !b || a === b) return false;
    /* Zwei Handgriffe sind immer erlaubt — „Halloch“ → „Hallo“ ist eine
       richtige Korrektur, und die wäre bei einem sonst durchgefallen. */
    const erlaubt = Math.max(2, Math.floor(Math.min(a.length, b.length) / 3));
    return wortAbstand(a, b) <= erlaubt;
  }

  /* Wörter inklusive Umlauten, ß und Bindestrich */
  const WORT_MUSTER = /[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)*/g;

  function uebernimmSchreibweise(original, verbesserung) {
    if (/^[A-ZÄÖÜ]/.test(verbesserung)) return verbesserung;          // Hauptwort
    if (original === original.toUpperCase() && original.length > 1) return verbesserung.toUpperCase();
    if (/^[A-ZÄÖÜ]/.test(original)) return verbesserung[0].toUpperCase() + verbesserung.slice(1);
    return verbesserung;
  }

  /* Leerzeichen sind unsichtbar. Wo genau sie der Fehler sind, muss man sie sehen. */
  const zeigeLeer = (s) => s.replace(/ /g, '␣').replace(/\n/g, '⏎');

  /* Jeder Fund hat eine von drei Arten:
     fehler  – sicher falsch (oranger Balken)
     tipp    – kommt auf den Zusammenhang an, deshalb selbst noch einmal lesen
     hinweis – nur zum Nachdenken, es gibt nichts zum Ändern (kein Knopf) */
  function machFund(von, bis, alt, neu, grund, art, leer) {
    return {
      von, bis, alt, neu,
      zeigeAlt: leer ? zeigeLeer(alt) : alt,
      zeigeNeu: leer ? zeigeLeer(neu) : neu,
      grund, art,
    };
  }

  /* ------------------------------------------------------------
     Der Regelmotor.
     Eine Regel besteht aus einem Muster, einem Bauplan für den Ersatz und
     einer Begründung in einfachen Worten. Dazu drei Schalter:
       pruefe   – darf einen Treffer nachträglich verwerfen
       gruppe   – grenzt den Fund auf eine Klammer ein: das Muster darf die
                  Umgebung mitlesen, angezeigt und ersetzt wird nur die Klammer
       leer     – macht Leerzeichen im Vorher/Nachher sichtbar
     ------------------------------------------------------------ */
  function wendeRegelnAn(text, regeln, funde) {
    for (const regel of regeln) {
      for (const treffer of text.matchAll(regel.muster)) {
        if (regel.pruefe && !regel.pruefe(treffer, text)) continue;
        const versatz = regel.gruppe ? treffer.slice(1, regel.gruppe).join('').length : 0;
        const alt = regel.gruppe ? treffer[regel.gruppe] : treffer[0];
        const neu = regel.bau(...treffer);
        if (neu === alt) continue;
        const von = treffer.index + versatz;
        funde.push(machFund(von, von + alt.length, alt, neu,
                            regel.grund, regel.art || 'fehler', regel.leer));
      }
    }
  }

  /* ------------------------------------------------------------
     a) Wörter aus der Liste oben
     ------------------------------------------------------------ */
  function pruefeWoerter(text, funde) {
    for (const treffer of text.matchAll(WORT_MUSTER)) {
      const wort = treffer[0];
      /* Erst die mitgelieferte Liste, dann die selbst gelernte. Was dieser
         Mensch schon einmal richtiggestellt hat, steht beim nächsten Mal sofort
         da — ohne KI, ohne Internet. */
      const ausListe = WOERTERBUCH[wort.toLowerCase()];
      const gelernt = ausListe ? null : Gelernt.wort(wort);
      const richtig = ausListe || gelernt;
      if (!richtig) continue;
      // Selbst Gelerntes muss dem Wort ähnlich sehen, sonst war es nie eine
      // Korrektur — siehe istKorrektur() weiter oben.
      if (gelernt && !istKorrektur(wort, gelernt)) continue;
      const ersatz = uebernimmSchreibweise(wort, richtig);
      if (ersatz === wort) continue;
      /* Was aus der mitgelieferten Liste kommt, ist sicher falsch. Was dieser
         Mensch der App selbst beigebracht hat, kam aus EINEM Antippen — das ist
         ein guter Hinweis, aber keine Gewissheit. Deshalb steht es als Tipp da
         und sagt auch, woher es stammt. */
      funde.push(machFund(treffer.index, treffer.index + wort.length,
                          wort, ersatz,
                          gelernt ? 'So hast du es schon einmal geändert' : 'Schreibweise',
                          gelernt ? 'tipp' : 'fehler'));
    }
  }

  /* ------------------------------------------------------------
     b) Abstände und Satzzeichen
     ------------------------------------------------------------ */

  /* Steht direkt vor dieser Stelle eine Abkürzung („z. B.“, „usw.“)? Dann ist der
     Punkt kein Satzende, und weder Leerzeichen noch Großschreibung fehlen. */
  const ABKUERZUNG = /(?:^|[\s(„"])(?:[A-Za-zÄÖÜäöüß]|ca|bzw|usw|evtl|ggf|inkl|exkl|vgl|bspw|Nr|Dr|Prof|Abs|Mio|Mrd|Tel|Str)\.$/;
  const istAbkuerzung = (text, punkt) => ABKUERZUNG.test(text.slice(Math.max(0, punkt - 9), punkt + 1));

  /* Web- und E-Mail-Adressen haben ihre eigenen Punkte. */
  /* Adressen, Pfade und Namen aus Programmen sind kein Fließtext.

     Vorher stand hier nur eine Suche nach „@", „http" und Endungen wie „.de".
     „kaysiebke-cell/schreibhilfe. Git." fiel durch das Raster: Der Punkt in
     der Mitte sah nach Satzende aus, und das „k" danach bekam „Satzanfang
     großschreiben" — zweimal in einem Absatz.

     Ein Schrägstrich zwischen zwei Wörtern ist ein sicheres Zeichen, ebenso
     ein Bindestrich-Name ohne Leerzeichen. Beides kommt in deutschen Sätzen
     so gut wie nie vor, in Adressen dauernd. */
  /* Gefragt wird das WORT an dieser Stelle, nicht die Nachbarschaft.

     Zuerst stand hier ein Fenster von dreißig Zeichen. Damit verschwand
     zwar der falsche Fund in „kaysiebke-cell/schreibhilfe" — aber gleich
     mit ihm der richtige drei Wörter weiter: „helfe mir mein beitrag"
     gehört großgeschrieben, und der Schrägstrich davor hatte damit nichts
     zu tun. Eine Regel, die zu viel wegschneidet, ist so falsch wie eine,
     die zu viel anstreicht. */
  const wortUm = (text, stelle) => {
    let a = stelle;
    let b = stelle;
    while (a > 0 && !/\s/.test(text[a - 1])) a--;
    while (b < text.length && !/\s/.test(text[b])) b++;
    return text.slice(a, b);
  };

  const istAdresse = (text, stelle) => {
    const wort = wortUm(text, stelle);
    return /[@]|https?:|^www\./i.test(wort)
        || /[A-Za-zÄÖÜäöü0-9_-]\/[A-Za-zÄÖÜäöü0-9_-]/.test(wort)
        || /\.(de|com|org|net|eu|git|io|dev)\b/i.test(wort);
  };

  /* Folgt hinter dem Treffer ein großgeschriebenes Wort?
     Muss außerhalb des Musters stehen: Regeln mit „i“ sehen den Unterschied
     zwischen groß und klein nicht mehr — auch nicht in [A-ZÄÖÜ]. */
  const grossDahinter = (treffer, text) =>
    /^[ \t]+[A-ZÄÖÜ]/.test(text.slice(treffer.index + treffer[0].length));

  /* ------------------------------------------------------------
     Wortgrenzen, die Umlaute kennen

     „\b“ kennt in JavaScript nur ASCII. Zwischen einem Leerzeichen und „ä“
     sieht es deshalb KEINE Wortgrenze, und /\bälter\b/ hat nie gegriffen —
     /\bgrößer\b/ dagegen schon, weil „g“ ein ASCII-Buchstabe ist. In Python
     gibt es das Problem nicht, dort ist \b von Haus aus Unicode-tauglich.

     Die beiden Prüfer standen damit auseinander: „älter wie“, „öfter wie“ und
     „ärmer wie“ rügte nur LibreOffice, der Browser ließ sie durch. Aufgefallen
     ist es erst beim Vergleich über 7183 Sätze; die 56 Sätze in vergleiche.py
     treffen keines der drei Wörter.

     WG_VOR und WG_NACH tun dasselbe wie \b, kennen aber Umlaute und ß.
     \p{L}\p{N}_ ist genau das, was Python unter \w versteht: jeder Buchstabe,
     jede Ziffer, der Unterstrich. Eine ausgeschriebene Liste „A-Za-zÄÖÜäöüß“
     täte es fast — aber eben nur fast: An „caféälter“ ginge sie auseinander,
     weil „é“ darin fehlte und Python es mitzählt.

     Dafür braucht es den Schalter „u“. Der bringt noch etwas mit, das hier
     gerade recht kommt: Mit „u“ trifft „ß“ bei Kleinschreibung auch das große
     „ẞ“ — so wie Python es tut, und anders als JavaScript ohne den Schalter.
     ------------------------------------------------------------ */
  const WORTZEICHEN = '\\p{L}\\p{N}_';
  const WG_VOR  = '(?<![' + WORTZEICHEN + '])';   // wie \b, vor einem Wort
  const WG_NACH = '(?![' + WORTZEICHEN + '])';    // wie \b, hinter einem Wort

  const ZEICHEN_REGELN = [
    { muster:/ {2,}/g,                        bau:() => ' ', leer:true,
      grund:'Mehrere Leerzeichen hintereinander' },
    { muster:/[ \t]+([,.;:!?])/g,             bau:(m, z) => z, leer:true,
      grund:'Vor dem Satzzeichen gehört kein Leerzeichen' },
    { muster:/([,;:])([A-Za-zÄÖÜäöüß])/g,     bau:(m, z, b) => z + ' ' + b, leer:true,
      grund:'Nach dem Satzzeichen fehlt ein Leerzeichen' },
    /* Punkt/Ausrufe-/Fragezeichen, direkt gefolgt vom nächsten Satz.
       Mindestens zwei Buchstaben davor, damit Abkürzungen wie „z.B.“ in Ruhe
       gelassen werden – die beiden Wächter halten den Rest raus. */
    { muster:/([A-Za-zÄÖÜäöüß]{2}[.!?])([A-Za-zÄÖÜäöüß])/g,
      bau:(m, z, b) => z + ' ' + b, leer:true,
      pruefe:(treffer, text) => !istAdresse(text, treffer.index)
                             && !istAbkuerzung(text, treffer.index + 2),
      grund:'Nach dem Satzzeichen fehlt ein Leerzeichen' },
    /* Drei Punkte sind Absicht, zwei sind ein Versehen. */
    { muster:/,{2,}/g,                        bau:() => ',',
      grund:'Das Komma steht doppelt da' },
    { muster:/([;:!?])\1+/g,                  bau:(m, z) => z,
      grund:'Das Satzzeichen steht doppelt da' },
    { muster:new RegExp(WG_VOR + '([A-Za-zÄÖÜäöüß]+)([ \\t]+)\\1' + WG_NACH, 'giu'),
      bau:(m, w) => w,
      grund:'Das Wort steht doppelt da' },
    /* „Peter's Auto“ – der Apostroph kommt aus dem Englischen. */
    { muster:new RegExp(WG_VOR + "([A-ZÄÖÜ][A-Za-zÄÖÜäöüß]{1,})['’´`]s" + WG_NACH, 'gu'),
      bau:(m, name) => name + 's',
      art:'tipp',
      grund:'Vor dem Genitiv-s steht im Deutschen kein Apostroph.' },
  ];

  /* ------------------------------------------------------------
     c) Großschreibung
     ------------------------------------------------------------ */

  const KEIN_HAUPTWORT = new Set(REGELDATEN.KEIN_HAUPTWORT);

  const GROSS_REGELN = [
    // Der allererste Buchstabe
    { muster:/(^[ \t]*)([a-zäöüß])/g, gruppe:2,
      bau:(m, vor, b) => b.toUpperCase(),
      grund:'Satzanfang großschreiben' },
    /* Nach Punkt, Ausrufe- oder Fragezeichen — auch über einen Zeilenumbruch
       hinweg. Eine neue Zeile allein ist kein Satzanfang: nach der Anrede
       („Liebe Anna,“) geht es klein weiter, und umbrochene Absätze aus anderen
       Apps stünden sonst voller falscher Funde.
       Auslassungspunkte („warte … dann“) sind ebenfalls kein Satzende. */
    { muster:/([.!?]+["»›)]?\s+)([a-zäöüß])/g, gruppe:2,
      bau:(m, vor, b) => b.toUpperCase(),
      /* Geprüft wird das Wort, das mit dem gefundenen Buchstaben ANFÄNGT —
         nicht das davor. „treffer.index" zeigt auf den Punkt, und dort steht
         „Umwege."; die Adresse ist das Wort dahinter. Mit der falschen Stelle
         blieb „kaysiebke-cell/schreibhilfe" unerkannt. */
      pruefe:(treffer, text) => !/^\.{2,}/.test(treffer[1])
                             && !istAbkuerzung(text, treffer.index)
                             && !istAdresse(text, treffer.index + treffer[1].length),
      grund:'Satzanfang großschreiben' },
    // „beim schreiben“ → „beim Schreiben“. Folgt ein großgeschriebenes Wort,
    // ist das -en-Wort ein Eigenschaftswort davor („zum neuen Haus“) — Finger weg.
    { muster:new RegExp(WG_VOR + '(beim|zum|vom|ans|aufs)([ \\t]+)([a-zäöüß]{3,}en)'
                        + WG_NACH, 'giu'),
      gruppe:3,
      bau:(m, vor, l, wort) => wort[0].toUpperCase() + wort.slice(1),
      pruefe:(treffer, text) => !KEIN_HAUPTWORT.has(treffer[3].toLowerCase())
                             && !/sten$/i.test(treffer[3])
                             && !grossDahinter(treffer, text),
      art:'tipp',
      grund:'Nach „beim/zum/vom“ wird aus dem Tunwort ein Hauptwort.' },
  ];

  /* ------------------------------------------------------------
     d) Grammatik: die Verwechslungen, die kein Rechtschreibprüfer sieht
     ------------------------------------------------------------ */

  const FUERWOERTER          = REGELDATEN.FUERWOERTER.join('|');
  const DENK_ZEITWOERTER     = REGELDATEN.DENK_ZEITWOERTER.join('|');
  const DENK_ZEITWOERTER_ENG = REGELDATEN.DENK_ZEITWOERTER_ENG.join('|');
  const DASS_EIGENSCHAFTEN   = REGELDATEN.DASS_EIGENSCHAFTEN.join('|');
  const ZEITANGABEN          = REGELDATEN.ZEITANGABEN.join('|');
  const STEIGERUNGEN         = REGELDATEN.STEIGERUNGEN.join('|');
  const FOLGT_NEBENSATZ =
    FUERWOERTER + '|' + REGELDATEN.FOLGT_NEBENSATZ_ZUSAETZLICH.join('|');

  const GRAMMATIK_REGELN = [
    /* das/dass nach einem Zeitwort des Denkens und Sagens. Fehlt auch noch das
       Komma, kommt es gleich mit — beides gehört zusammen. */
    { muster:new RegExp(WG_VOR + '(' + DENK_ZEITWOERTER + ')(,?)([ \\t]+)das' + WG_NACH +
                        '(?=[ \\t]+(?:' + FUERWOERTER + ')' + WG_NACH + ')', 'giu'),
      bau:(m, verb, komma, l) => verb + ',' + l + 'dass',
      art:'tipp',
      grund:'Hier leitet „dass“ den Nebensatz ein – mit Komma davor.' },
    { muster:new RegExp(WG_VOR + '(' + DENK_ZEITWOERTER_ENG + ')(,?)([ \\t]+)das' + WG_NACH +
                        '(?=[ \\t]+(?:' + FOLGT_NEBENSATZ + ')' + WG_NACH + ')', 'giu'),
      bau:(m, verb, komma, l) => verb + ',' + l + 'dass',
      art:'tipp',
      grund:'Hier leitet „dass“ den Nebensatz ein – mit Komma davor.' },
    { muster:new RegExp(WG_VOR + '(' + DASS_EIGENSCHAFTEN + ')(,?)([ \\t]+)das' + WG_NACH +
                        '(?=[ \\t]+(?:' + FOLGT_NEBENSATZ + ')' + WG_NACH + ')', 'giu'),
      bau:(m, wort, komma, l) => wort + ',' + l + 'dass',
      art:'tipp',
      grund:'Hier leitet „dass“ den Nebensatz ein – mit Komma davor.' },

    /* seit/seid */
    { muster:new RegExp(WG_VOR + 'seid([ \\t]+)(?=(?:' + ZEITANGABEN + ')' + WG_NACH + ')', 'giu'),
      bau:(m, l) => 'seit' + l,
      grund:'Bei Zeitangaben heißt es „seit“ – „seid“ nur bei „ihr seid“.' },
    /* „Seit ihr das wisst …“ – aber „Seit ihr Vater gestorben ist“ bleibt stehen:
       folgt ein Hauptwort, gehört „ihr“ dazu und „seit“ ist richtig. */
    { muster:new RegExp(WG_VOR + 'seit([ \\t]+)ihr' + WG_NACH, 'giu'),
      bau:(m, l) => 'seid' + l + 'ihr',
      pruefe:(treffer, text) => !grossDahinter(treffer, text),
      grund:'„ihr seid“ – hier gehört ein d ans Ende.' },
    { muster:new RegExp(WG_VOR + 'ihr([ \\t]+)seit' + WG_NACH
                        + '(?![ \\t]+(?:' + ZEITANGABEN + ')' + WG_NACH + ')', 'giu'),
      bau:(m, l) => 'ihr' + l + 'seid',
      grund:'„ihr seid“ – hier gehört ein d ans Ende.' },
    { muster:new RegExp(WG_VOR + 'seit([ \\t]+)(ruhig|still|nett|lieb|vorsichtig|ehrlich|'
                        + 'froh|gegrüßt|willkommen|gespannt|unbesorgt|bereit)' + WG_NACH, 'giu'),
      bau:(m, l, wort) => 'seid' + l + wort,
      grund:'Aufforderung an mehrere: „seid ruhig“ mit d.' },

    /* Vergleich: größer als, nicht größer wie */
    { muster:new RegExp(WG_VOR + '(' + STEIGERUNGEN + ')([ \\t]+)wie' + WG_NACH, 'giu'),
      bau:(m, wort, l) => wort + l + 'als',
      grund:'Nach der Steigerung heißt es „als“: größer als, lieber als.' },
    { muster:new RegExp(WG_VOR + 'als([ \\t]+)wie' + WG_NACH, 'giu'),
      bau:() => 'als',
      grund:'„als wie“ ist doppelt gemoppelt – „als“ reicht.' },
  ];

  /* ------------------------------------------------------------
     e) Komma vor dem Nebensatz
     ------------------------------------------------------------ */

  const KEIN_KOMMA_DAVOR = new Set(REGELDATEN.KEIN_KOMMA_DAVOR);
  const NEBENSATZ_WOERTER = REGELDATEN.NEBENSATZ_WOERTER;

  const KOMMA_REGELN = NEBENSATZ_WOERTER.map(([wort, nurVorFuerwort]) => ({
    muster: new RegExp(WG_VOR + '([A-Za-zÄÖÜäöüß]{2,})([ \\t]+)(' + wort + ')' + WG_NACH +
                       (nurVorFuerwort ? '(?=[ \\t]+(?:' + FUERWOERTER + ')' + WG_NACH + ')' : ''), 'giu'),
    bau: (m, davor, l, schluessel) => davor + ',' + l + schluessel,
    pruefe: (treffer) => !KEIN_KOMMA_DAVOR.has(treffer[1].toLowerCase()),
    art: 'tipp',
    grund: 'Vor „' + wort + '“ beginnt ein Nebensatz – da gehört ein Komma hin.',
  })).concat([
    /* „aber/sondern/denn“ verbinden zwei Sätze — dann steht ein Komma davor.
       Nur mit Fürwort dahinter, sonst gerät „Das ist aber schön“ mit hinein. */
    { muster:new RegExp(WG_VOR + '([A-Za-zÄÖÜäöüß]{2,})([ \\t]+)(aber|sondern|denn)' + WG_NACH +
                        '(?=[ \\t]+(?:' + FUERWOERTER + ')' + WG_NACH + ')', 'giu'),
      bau:(m, davor, l, wort) => davor + ',' + l + wort,
      pruefe:(treffer) => !KEIN_KOMMA_DAVOR.has(treffer[1].toLowerCase()),
      art:'tipp',
      grund:'Hier stoßen zwei Sätze aneinander – davor gehört ein Komma.' },
  ]);

  /* ------------------------------------------------------------
     f) Passt das Zeitwort zum Fürwort?

     Die Formen stehen in daten/regeln.js; dort steht auch, warum nur acht
     Zeitwörter geprüft werden und warum „sie“, „ihr“ und „es“ fehlen.
     ------------------------------------------------------------ */
  const ZEITWOERTER = REGELDATEN.ZEITWOERTER;
  const SPALTE = REGELDATEN.SPALTE;
  const FORM_ZU_ZEITWORT = new Map();
  for (const zeile of ZEITWOERTER) {
    for (const form of Object.values(zeile)) FORM_ZU_ZEITWORT.set(form, zeile);
  }

  const KONGRUENZ_MUSTER = [
    // „wir hat“
    { muster:new RegExp(WG_VOR + '(ich|du|er|man|wir)([ \\t]+)([a-zäöüß]+)' + WG_NACH, 'giu'),
      fuerwort:1, form:3 },
    // „hat wir“ — in Fragen und nach vorangestelltem Satzteil
    { muster:new RegExp(WG_VOR + '([a-zäöüß]+)([ \\t]+)(ich|du|er|man|wir)' + WG_NACH, 'giu'),
      fuerwort:3, form:1 },
  ];

  function pruefeKongruenz(text, funde) {
    for (const stelle of KONGRUENZ_MUSTER) {
      for (const treffer of text.matchAll(stelle.muster)) {
        const fuerwort = treffer[stelle.fuerwort];
        const form = treffer[stelle.form];
        const zeile = FORM_ZU_ZEITWORT.get(form.toLowerCase());
        if (!zeile) continue;
        const richtig = zeile[SPALTE[fuerwort.toLowerCase()]];
        if (!richtig || richtig === form.toLowerCase()) continue;

        const alt = treffer[0];
        const neu = stelle.form === 1
          ? uebernimmSchreibweise(form, richtig) + treffer[2] + fuerwort
          : fuerwort + treffer[2] + uebernimmSchreibweise(form, richtig);
        funde.push(machFund(treffer.index, treffer.index + alt.length, alt, neu,
          'So passt das Zeitwort zum Fürwort: „' + fuerwort.toLowerCase() + ' ' + richtig + '“.',
          'fehler'));
      }
    }
  }

  /* ------------------------------------------------------------
     g) Der Punkt am Ende
     ------------------------------------------------------------ */
  function pruefeSatzende(text, funde) {
    const bisEnde = text.replace(/\s+$/, '');
    if (!bisEnde || /[.!?:…»"'\)\]]$/.test(bisEnde)) return;
    /* Gezählt wird nur die letzte Zeile: „Herzliche Grüße“ und ein Name darunter
       sind ganze Sätze, brauchen aber keinen Punkt. */
    const woerter = bisEnde.slice(bisEnde.lastIndexOf('\n') + 1).trim().split(/\s+/);
    if (woerter.length < 5) return;
    const letztes = woerter[woerter.length - 1];
    if (!/[A-Za-zÄÖÜäöüß0-9]$/.test(letztes)) return;
    const von = bisEnde.length - letztes.length;
    funde.push(machFund(von, bisEnde.length, letztes, letztes + '.',
                        'Am Ende fehlt der Punkt.', 'tipp'));
  }

  /* ------------------------------------------------------------
     h) Satzbau: Hinweise ohne Knopf

     Hier gibt es nichts zu ersetzen — der Satz ist nicht falsch, er ist nur
     schwer zu lesen. Deshalb steht kein „Ändern“ daneben, nur der Hinweis.
     ------------------------------------------------------------ */
  function machHinweis(von, bis, grund, stelle) {
    return { von, bis, alt:'', neu:'', grund, stelle, art:'hinweis' };
  }

  function pruefeSatzbau(text, hinweise) {
    for (const treffer of text.matchAll(/[^.!?\n]+/g)) {
      const roh = treffer[0];
      const satz = roh.trim();
      if (!satz) continue;
      const anfang = treffer.index + roh.indexOf(satz[0]);
      const woerter = satz.split(/\s+/).length;
      const binder = (satz.match(/\b(und|oder|aber|dann|weil)\b/gi) || []).length;

      if (woerter > 25) {
        hinweise.push(machHinweis(anfang, anfang + satz.length,
          'Langer Satz: ' + woerter + ' Wörter. Zwei kürzere Sätze liest man leichter.', satz));
      } else if (woerter >= 12 && binder >= 3) {
        hinweise.push(machHinweis(anfang, anfang + satz.length,
          'Der Satz hängt an vielen Bindewörtern. Ein Punkt dazwischen tut ihm gut.', satz));
      }
    }

    /* Zeichen, die immer zu zweit auftreten. Fehlt der Partner, merkt man es
       beim Schreiben selten. */
    const paare = [
      ['(', ')', 'Klammern'],
      ['„', '“', 'Anführungszeichen'],
    ];
    for (const [auf, zu, name] of paare) {
      const offen = text.split(auf).length - 1;
      const geschlossen = text.split(zu).length - 1;
      if (offen !== geschlossen) {
        hinweise.push(machHinweis(text.length, text.length,
          name + ': ' + offen + '-mal geöffnet, ' + geschlossen + '-mal geschlossen.', ''));
      }
    }
    const geraden = text.split('"').length - 1;
    if (geraden % 2 === 1) {
      hinweise.push(machHinweis(text.length, text.length,
        'Ein Anführungszeichen steht allein da.', ''));
    }
  }

  /* ------------------------------------------------------------
     Zwei Funde an derselben Stelle gehen nicht: die erste Änderung würde die
     zweite ins Leere laufen lassen. Nach dem Ändern wird ohnehin neu gesucht,
     dann taucht der verdeckte Fund von selbst wieder auf.

     Wer dabei weichen muss, ist nicht egal. Ein falsch geschriebenes Wort wiegt
     schwerer als ein fehlendes Komma daneben — und die Komma-Regeln greifen über
     zwei Wörter, verdecken also leicht einen Vertipper im ersten davon.
     („geschriben aber" → Komma verdeckte „geschriben → geschrieben".)
     Deshalb kommen die Wort-Funde zuerst dran, die Regel-Funde füllen die Lücken.
     ------------------------------------------------------------ */
  function ohneUeberschneidung(funde) {
    const belegt = [];
    const passt = (f) => belegt.every((b) => f.bis <= b.von || f.von >= b.bis);
    const nachStelle = (a, b) => a.von - b.von || (b.bis - b.von) - (a.bis - a.von);

    for (const durchgang of [funde.filter((f) => f.wortEbene),
                             funde.filter((f) => !f.wortEbene)]) {
      for (const fund of durchgang.sort(nachStelle)) {
        if (passt(fund)) belegt.push(fund);
      }
    }
    return belegt.sort(nachStelle);
  }

  /* Sucht alle Stellen, die auffällig sind. */

  /* ------------------------------------------------------------
     Zusammengeschriebene Wörter trennen: „halloich“ → „hallo ich“.

     Die Tastatur unterringelt so etwas zwar rot, weiß aber nicht, WO die
     Lücke hingehört. Genau da hilft diese Regel.

     Getrennt wird nur, wenn der zweite Teil ein kurzes Funktionswort ist —
     Pronomen, Artikel, Hilfsverb. Deutsche Zusammensetzungen enden praktisch
     nie darauf: „Haustür“ ja, „Hausich“ nein. Das hält die Regel eng.

     Die Schutzliste ist nicht geraten, sondern gemessen: die Regel lief gegen
     die 356.010 Wörter von /usr/share/dict/ngerman, und genau diese Wörter
     hätte sie fälschlich zerlegt. „wieder“ und „werden“ sind die wichtigsten.
     ------------------------------------------------------------ */
  /* ------------------------------------------------------------
     Zusammengeschriebene Wörter trennen: „dasgar“ → „das gar“.

     Die frühere Fassung verlangte, dass der zweite Teil ein kurzes
     Funktionswort ist. Damit blieben genau die Fälle liegen, die beim Tippen
     wirklich entstehen: „dasgar“, „nichtgemacht“. Jetzt entscheidet ein
     richtiges Wörterbuch (355.322 Wörter, daten/woerter.txt).

     Drei Bedingungen, damit nichts zerrissen wird, was zusammengehört:
       1. Steht das Wort selbst im Wörterbuch, bleibt es unangetastet.
          Das schützt Zusammensetzungen wie „Haustür“ oder „Arbeitsamt“.
       2. Beide Teile müssen im Wörterbuch stehen.
       3. Einer der Teile muss ein häufiges kurzes Wort sein. Sonst würde
          „Bürgergeldbescheid“, das im Wörterbuch fehlt, in zwei richtige
          Wörter zerlegt.

     Hier stand „gegen die vollständige Liste geprüft: null Fehlalarme“. Das
     war zu schön: Bedingung 1 schützt jedes Wort, das in der Liste STEHT — an
     denen kann sich nichts zeigen. Gefährlich sind die Wörter außerhalb der
     Liste, und dort trennt auch diese Fassung gelegentlich falsch
     („Untermietvertrag“ → „unter mietvertrag“).

     Ehrlich gemessen, an 1308 Wörtern aus den Texten dieses Projekts und an
     41 Behörden-Zusammensetzungen wie „Bürgergeldbescheid“:
       3 bzw. 1 Fehlalarm — vor wie nach der Lockerung unten dieselben.
     Von 23 typisch zusammengetippten Wörtern werden 21 erkannt (vorher 14).
     ------------------------------------------------------------ */
  const TRENN_KURZ = new Set(REGELDATEN.TRENN_KURZ);

  /** Wird beim Start im Hintergrund geladen; bis dahin wird nicht getrennt. */
  let WOERTERBUCH_GROSS = null;

  (async () => {
    try {
      const antwort = await fetch('daten/woerter.txt');
      if (!antwort.ok) return;
      WOERTERBUCH_GROSS = new Set((await antwort.text()).split('\n'));
    } catch { /* Ohne Liste entfällt nur das Trennen, alles andere läuft. */ }
  })();

  function trenneZusammen(wort) {
    if (!WOERTERBUCH_GROSS) return null;
    const w = wort.toLowerCase();
    if (w.length < 6 || WOERTERBUCH_GROSS.has(w)) return null;
    /* Ab dem ZWEITEN Zeichen, nicht erst ab dem dritten: Sonst bleiben genau die
       Fälle liegen, die beim Tippen am häufigsten entstehen — „ambesten",
       „esgibt", „zuviel", „imanhang". Ein Teil mit nur zwei Zeichen muss dafür
       aus TRENN_KURZ stammen; die große Liste allein wäre hier zu großzügig. */
    for (let i = 2; i <= w.length - 2; i++) {
      const vorn = w.slice(0, i);
      const hinten = w.slice(i);
      if (!WOERTERBUCH_GROSS.has(vorn) || !WOERTERBUCH_GROSS.has(hinten)) continue;
      if (vorn.length < 3 && !TRENN_KURZ.has(vorn)) continue;
      if (hinten.length < 3 && !TRENN_KURZ.has(hinten)) continue;
      if (!TRENN_KURZ.has(vorn) && !TRENN_KURZ.has(hinten)) continue;
      return vorn + ' ' + hinten;
    }
    return null;
  }

  function pruefeZusammengeschrieben(text, funde) {
    for (const treffer of text.matchAll(WORT_MUSTER)) {
      const wort = treffer[0];
      const getrennt = trenneZusammen(wort);
      if (!getrennt) continue;
      /* Großschreibung übertragen — und am Satzanfang gleich mit erledigen.
         Sonst bliebe „halloich" → „hallo ich" klein: die Regel für den
         Satzanfang greift auf dieselbe Stelle zu und wird als Überschneidung
         verworfen. */
      const davor = text.slice(0, treffer.index);
      const satzAnfang = davor.trim() === '' || /[.!?]\s+$/.test(davor);
      const gross = /^[A-ZÄÖÜ]/.test(wort) || satzAnfang;
      const neu = gross ? getrennt[0].toUpperCase() + getrennt.slice(1) : getrennt;
      funde.push(machFund(
        treffer.index, treffer.index + wort.length, wort, neu,
        'Zwei Wörter ohne Lücke', 'wort', false
      ));
    }
  }


  /* ------------------------------------------------------------
     Tippfehler: ein Buchstabe daneben.

     „vieleicht“ → „vielleicht“, „shcon“ → „schon“. Gesucht wird nach Wörtern,
     die sich um genau einen Handgriff unterscheiden: ein Buchstabe zu viel,
     zu wenig, falsch, oder zwei vertauscht.

     Bewusst NICHT eingebaut: Trennen und Tippfehler zusammen. „Halloch“ würde
     damit zu „aal loch“, „ichhab“ zu „ich ab“ — die Suche wird so weit, dass
     sie Unsinn findet. Wörter wie „Halloch“ bleiben der KI überlassen.

     Vorschläge erscheinen als Hinweis-Kasten und ändern nichts von allein:
     Bei Namen und Fremdwörtern liegt die Suche zwangsläufig manchmal daneben,
     und dann tippt man den Kasten einfach nicht an.
     ------------------------------------------------------------ */
  const ABC = 'abcdefghijklmnopqrstuvwxyzäöüß';

  function nachbarWoerter(w) {
    const aus = new Set();
    for (let i = 0; i <= w.length; i++) {
      if (i < w.length) {
        aus.add(w.slice(0, i) + w.slice(i + 1));                     // Buchstabe weg
        for (const c of ABC) aus.add(w.slice(0, i) + c + w.slice(i + 1));  // ersetzt
        if (i < w.length - 1) {
          aus.add(w.slice(0, i) + w[i + 1] + w[i] + w.slice(i + 2));  // vertauscht
        }
      }
      for (const c of ABC) aus.add(w.slice(0, i) + c + w.slice(i));   // eingefügt
    }
    return aus;
  }

  function tippfehlerVorschlag(wort) {
    if (!WOERTERBUCH_GROSS) return null;
    const w = wort.toLowerCase();
    if (w.length < 4 || w.length > 20 || WOERTERBUCH_GROSS.has(w)) return null;

    const treffer = [];
    for (const kandidat of nachbarWoerter(w)) {
      if (!WOERTERBUCH_GROSS.has(kandidat)) continue;
      /* Zwei Vorschläge, die nie einer sind:

         Erstens der Stummel. „Apps" steht nicht in der Liste, „pps" schon —
         also wurde aus einem richtigen Wort ein Nichtwort. Ein Vorschlag
         unter vier Buchstaben für ein längeres Wort ist kein Tippfehler,
         sondern ein Fund in einer Liste, die auch Bruchstücke enthält.

         Zweitens der abgeschnittene Anfang. Den ersten Buchstaben verfehlt
         man beim Tippen kaum — die Hand liegt bereit, wenn das Wort
         anfängt. Wer „Apps" schreibt, meinte nicht „pps". */
      if (kandidat.length < 4 && w.length >= 4) continue;
      if (kandidat === w.slice(1)) continue;
      treffer.push(kandidat);
    }
    if (!treffer.length) return null;

    /* Bei mehreren Möglichkeiten gewinnt die naheliegendste.
       Ausschlaggebend ist die Art des Fehlers, nicht die Länge:

       Wer einen Buchstaben vergisst, tippt eine Teilfolge des richtigen Wortes
       — „gemcht" steckt Buchstabe für Buchstabe in „gemacht". Das ist der
       häufigste Vertipper und bekommt Vorrang. Danach kommt der umgekehrte
       Fall (ein Buchstabe zu viel), erst dann vertauscht oder falsch getroffen.

       Ohne diese Reihenfolge gewann „gemäht" gegen „gemacht", nur weil es
       gleich lang ist. */
    const istTeilfolge = (kurz, lang) => {
      let i = 0;
      for (const c of lang) if (i < kurz.length && kurz[i] === c) i++;
      return i === kurz.length;
    };
    const rang = (k) => istTeilfolge(w, k) ? 0 : istTeilfolge(k, w) ? 1 : 2;

    /* Bleiben mehrere gleich nah, gewinnt das Wort mit dem längeren gemeinsamen
       Anfang. Vertippt wird meist in der Mitte, der Wortanfang sitzt.
       So gewinnt „könnten" gegen „klönten" — vorher entschied das Alphabet. */
    const gleicherAnfang = (k) => {
      let i = 0;
      while (i < k.length && i < w.length && k[i] === w[i]) i++;
      return i;
    };

    treffer.sort((a, b) =>
      rang(a) - rang(b) ||
      gleicherAnfang(b) - gleicherAnfang(a) ||
      (TRENN_KURZ.has(b) ? 1 : 0) - (TRENN_KURZ.has(a) ? 1 : 0) ||
      a.length - b.length ||
      a.localeCompare(b, 'de'));
    return treffer[0];
  }

  /* ------------------------------------------------------------
     Vorschläge für ein einzelnes Wort — für das Menü unter der rechten
     Maustaste.

     Die Prüfung nimmt sich sonst nur den besten Treffer; im Menü sollen
     mehrere stehen, so wie man es aus jedem Schreibprogramm kennt. Gesucht
     wird mit demselben Verfahren und in derselben Reihenfolge, damit oben
     dasselbe Wort steht, das auch die Prüfung vorschlagen würde.

     Anders als beim Prüfen greift das hier auch bei kurzen Wörtern: Wer mit
     der rechten Taste auf ein Wort geht, will eine Antwort — und sei es
     „dazu nichts gefunden".
     ------------------------------------------------------------ */
  function vorschlaegeFuer(wort, hoechstens = 6) {
    if (!WOERTERBUCH_GROSS) return [];
    const w = String(wort).toLowerCase();
    if (w.length < 2 || w.length > 24 || WOERTERBUCH_GROSS.has(w)) return [];

    const treffer = [];
    for (const kandidat of nachbarWoerter(w)) {
      if (WOERTERBUCH_GROSS.has(kandidat)) treffer.push(kandidat);
    }

    /* Dazu, was genauso klingt. Der Buchstabenabstand findet „vieleicht →
       vielleicht", aber nicht „kwalität → Qualität" — dorthin sind es drei
       Änderungen. Über den Klang ist es derselbe. */
    for (const kandidat of klingtWie(w)) {
      if (!treffer.includes(kandidat)) treffer.push(kandidat);
    }

    /* Was die App über diesen Menschen gelernt hat, gehört nach ganz oben:
       Wer „Halloch" schon einmal zu „Hallo" gemacht hat, will es wieder. */
    const gelernt = Gelernt.wort(w);
    if (gelernt && !treffer.includes(gelernt)) treffer.unshift(gelernt);

    const istTeilfolge = (kurz, lang) => {
      let i = 0;
      for (const c of lang) if (i < kurz.length && kurz[i] === c) i++;
      return i === kurz.length;
    };
    const klangGleich = new Set(klingtWie(w));
    const rang = (k) => k === gelernt ? -1
      : istTeilfolge(w, k) ? 0
      : istTeilfolge(k, w) ? 1
      : klangGleich.has(k) ? 1        // klingt gleich: so nah wie ein fehlender Buchstabe
      : 2;
    const gleicherAnfang = (k) => {
      let i = 0;
      while (i < k.length && i < w.length && k[i] === w[i]) i++;
      return i;
    };

    /* Innerhalb derselben Nähe entscheidet der tatsächliche Abstand, nicht
       der gemeinsame Wortanfang — sonst verliert „vielleicht" gegen
       „flaggt", nur weil beide mit f beginnen wie das Getippte. */
    const gewicht = (k) => abstand(w, k) - (HAEUFIG.has(k) ? 2 : 0);

    treffer.sort((a, b) =>
      rang(a) - rang(b) ||
      gewicht(a) - gewicht(b) ||
      gleicherAnfang(b) - gleicherAnfang(a) ||
      a.length - b.length ||
      a.localeCompare(b, 'de'));

    return [...new Set(treffer)].slice(0, hoechstens);
  }

  /* ------------------------------------------------------------
     Kölner Phonetik

     Wer Legasthenie hat, verschreibt sich selten um einen Buchstaben —
     er schreibt, wie er hört. „kwalität", „fileicht", „ferzeihung",
     „exdra". Ein Abstandsmaß über Buchstaben findet das nicht: Von
     „kwalität" zu „Qualität" sind es drei Änderungen, das ist zu weit.

     Die Kölner Phonetik übersetzt ein Wort in seinen Klang. Klingen zwei
     Wörter gleich, haben sie denselben Schlüssel — egal wie verschieden
     sie geschrieben sind. Sie stammt von 1969 und ist für das Deutsche
     gemacht, anders als Soundex, das fürs Englische gebaut wurde.
     ------------------------------------------------------------ */
  function koelnerPhonetik(wort) {
    const w = String(wort).toUpperCase()
      .replace(/Ä/g, 'A').replace(/Ö/g, 'O').replace(/Ü/g, 'U').replace(/ß/g, 'SS')
      /* „Qu" spricht man „kw" — Qualität und kwalität klingen gleich, und
         genau so verschreibt man sich. Die Kölner Phonetik von 1969 sieht
         das nicht vor; ohne diese Zeile bekämen die beiden verschiedene
         Schlüssel, und der häufigste Fall wäre nicht erfasst. */
      .replace(/QU/g, 'KW')
      /* Ebenso „Ph": Philosophie klingt wie Filosofie. */
      .replace(/PH/g, 'F')
      .replace(/[^A-Z]/g, '');
    if (!w) return '';

    const laute = [];
    for (let i = 0; i < w.length; i++) {
      const c = w[i];
      const vor = w[i - 1];
      const nach = w[i + 1];
      let code = null;

      if ('AEIOUYJ'.includes(c)) code = '0';
      else if (c === 'B') code = '1';
      else if (c === 'P') code = nach === 'H' ? '3' : '1';
      else if ('DT'.includes(c)) code = 'CSZ'.includes(nach) ? '8' : '2';
      else if ('FVW'.includes(c)) code = '3';
      else if ('GKQ'.includes(c)) code = '4';
      else if (c === 'C') {
        /* „C" ist der schwierige Fall: In „Christian" klingt es wie K, in
           „Cent" wie Z. Es hängt davon ab, was davor und danach steht. */
        if (i === 0) code = 'AHKLOQRUX'.includes(nach) ? '4' : '8';
        else if ('SZ'.includes(vor)) code = '8';
        else code = 'AHKOQUX'.includes(nach) ? '4' : '8';
      }
      else if (c === 'X') code = 'CKQ'.includes(vor) ? '8' : '48';
      else if (c === 'L') code = '5';
      else if ('MN'.includes(c)) code = '6';
      else if (c === 'R') code = '7';
      else if ('SZ'.includes(c)) code = '8';
      else if (c === 'H') code = null;                 // H trägt keinen eigenen Laut

      if (code !== null) laute.push(code);
    }

    /* Doppelte zusammenziehen und die Nullen streichen — außer der ersten.
       Vokale unterscheiden im Deutschen zu wenig, um sie mitzuzählen. */
    let aus = '';
    for (let i = 0; i < laute.length; i++) {
      for (const z of laute[i]) {
        if (z !== aus[aus.length - 1]) aus += z;
      }
    }
    return aus[0] + aus.slice(1).replace(/0/g, '');
  }

  /* Der Klangschlüssel für jedes Wort im Wörterbuch — einmal gebaut, dann
     nachgeschlagen. Ohne diese Tabelle müsste bei jeder Suche die ganze
     Liste durchgerechnet werden; bei 355.322 Wörtern merkt man das. */
  let KLANGTAFEL = null;

  function klangtafelBauen() {
    if (KLANGTAFEL || !WOERTERBUCH_GROSS) return KLANGTAFEL;
    KLANGTAFEL = new Map();
    for (const wort of WOERTERBUCH_GROSS) {
      /* Sehr kurze Wörter klingen zu oft gleich („er", „ehr", „eher") —
         die brächten mehr Verwirrung als Hilfe. */
      if (wort.length < 4) continue;
      const klang = koelnerPhonetik(wort);
      if (!klang) continue;
      /* Keine Begrenzung beim Sammeln: Zuerst stand hier eine Grenze von
         zwölf Wörtern je Klang — und weil das Wörterbuch alphabetisch
         durchlaufen wird, fiel ausgerechnet „vielleicht" hinten heraus,
         während zwölf Wörter mit „fl…" davor standen. Begrenzt wird erst
         bei der Ausgabe, und dort nach Ähnlichkeit. */
      const gleiche = KLANGTAFEL.get(klang);
      if (gleiche) gleiche.push(wort);
      else KLANGTAFEL.set(klang, [wort]);
    }
    return KLANGTAFEL;
  }

  /** Wörter, die so klingen wie das eingetippte — die ähnlichsten zuerst. */
  function klingtWie(wort, hoechstens = 15) {
    const tafel = klangtafelBauen();
    if (!tafel) return [];
    const w = String(wort).toLowerCase();
    if (w.length < 4) return [];
    const klang = koelnerPhonetik(w);
    if (!klang) return [];

    const gleiche = (tafel.get(klang) || []).filter((k) => k !== w);
    if (gleiche.length <= 1) return gleiche;

    /* Gleicher Klang heißt nicht gleich nah: „fileicht" klingt wie
       „vielleicht" und wie „flaggt". Geordnet wird nach dem tatsächlichen
       Abstand der Schreibweisen.

       Nach dem gemeinsamen Wortanfang zu ordnen wäre naheliegend und wäre
       falsch: Gerade die häufigste deutsche Verwechslung — f statt v in
       „vielleicht", „Verzeihung", „Vater" — hat gar keinen gemeinsamen
       Anfang. „flaggt" gewann damit gegen „vielleicht". */
    /* Ein geläufiges Wort zählt, als läge es zwei Buchstaben näher. Sonst
       gewinnt jedes seltene Wort, das zufällig kürzer daneben liegt. */
    const gewicht = (k) => abstand(w, k) - (HAEUFIG.has(k) ? 2 : 0);

    return gleiche
      .slice()
      .sort((a, b) => gewicht(a) - gewicht(b)
                   || Math.abs(a.length - w.length) - Math.abs(b.length - w.length)
                   || a.localeCompare(b, 'de'))
      .slice(0, hoechstens);
  }

  /* ------------------------------------------------------------
     Die Wörter, die im Deutschen ständig vorkommen.

     Ohne sie gewinnt beim Vorschlagen der kürzere Abstand — und „fileicht"
     wurde zu „flicht" statt zu „vielleicht". Beides klingt gleich, beides
     steht im Wörterbuch; nur eines davon schreibt jemand wirklich.

     Eine vollständige Häufigkeitsliste wäre eine eigene Datei. Diese hier
     deckt ab, was in einem Brief vorkommt, und wiegt beim Sortieren so viel
     wie zwei Buchstaben Abstand.
     ------------------------------------------------------------ */
  const HAEUFIG = new Set(('der die das den dem des ein eine einen einem einer eines und oder aber '
    + 'ich du er sie es wir ihr mich dich sich uns euch mir dir ihm ihnen mein dein sein unser '
    + 'ist sind war waren bin bist wird werden wurde wurden haben hat hatte hatten habe '
    + 'kann können konnte konnten muss müssen musste mussten will wollen wollte darf dürfen '
    + 'soll sollen sollte möchte mag nicht kein keine keinen nichts noch schon nur auch sehr '
    + 'mehr weniger viel viele vielen wenig alle alles jeder jede jedes man jemand niemand '
    + 'für mit von zu zum zur bei nach aus über unter vor hinter neben zwischen ohne gegen um '
    + 'auf an in im ins am seit bis durch wegen trotz während innerhalb außerhalb '
    + 'wenn dann weil dass ob wie was wer wo wann warum wieder immer nie oft manchmal '
    + 'heute gestern morgen jetzt bald später früher hier dort da dahin dorthin '
    + 'vielleicht sicher bestimmt wirklich eigentlich natürlich leider hoffentlich '
    + 'gut gute guten besser beste schlecht groß große klein kleine neu neue alt alte '
    + 'lang lange kurz kurze hoch hohe tief richtig falsch wichtig einfach schwierig '
    + 'jahr jahre monat monate woche wochen tag tage stunde minute zeit zeiten '
    + 'mensch menschen frau frauen mann männer kind kinder familie vater mutter '
    + 'haus häuser wohnung stadt land straße weg geld arbeit beruf schule '
    + 'brief antrag bescheid amt behörde termin termine unterlagen frist widerspruch '
    + 'anlage kopie original nachweis bestätigung mitteilung schreiben antwort '
    + 'sehr geehrte geehrter damen herren freundlichen grüßen hochachtungsvoll '
    + 'bitte danke gern gerne leid entschuldigung verzeihung '
    + 'machen macht gemacht tun getan geben gibt gegeben nehmen nimmt genommen '
    + 'sagen sagt gesagt sehen sieht gesehen kommen kommt gekommen gehen geht gegangen '
    + 'stehen steht gestanden liegen liegt gelegen bleiben bleibt geblieben '
    + 'finden findet gefunden bringen bringt gebracht halten hält gehalten '
    + 'sprechen spricht gesprochen schreiben schreibt geschrieben lesen liest gelesen '
    + 'verstehen versteht verstanden wissen weiß gewusst denken denkt gedacht '
    + 'brauchen braucht gebraucht helfen hilft geholfen fragen fragt gefragt '
    + 'arbeiten arbeitet gearbeitet warten wartet gewartet zahlen zahlt gezahlt '
    + 'bekommen bekommt erhalten erhält beantragen beantragt prüfen prüft geprüft '
    + 'stellen stellt gestellt setzen setzt gesetzt legen legt gelegt '
    + 'stimmt stimmen berechnung zahlung betrag summe kosten rechnung '
    + 'grund gründe fall fälle frage fragen sache sachen ding dinge teil teile '
    + 'seite seiten stelle stellen art weise möglichkeit grundlage '
    + 'wohl doch schon eben halt zwar also somit deshalb darum dafür dagegen '
    + 'qualität quittung quartal').split(/\s+/).filter(Boolean));

  /* Wie viele Änderungen trennen zwei Wörter? Einfügen, Löschen, Ersetzen —
     das gewohnte Maß. Auf Wortlänge gerechnet ist das billig genug, um es
     für ein paar hundert Kandidaten zu tun. */
  function abstand(a, b) {
    if (a === b) return 0;
    const m = a.length;
    const n = b.length;
    if (!m) return n;
    if (!n) return m;

    let zeile = new Array(n + 1);
    for (let j = 0; j <= n; j++) zeile[j] = j;

    for (let i = 1; i <= m; i++) {
      let vorherige = zeile[0];
      zeile[0] = i;
      for (let j = 1; j <= n; j++) {
        const diagonal = vorherige;
        vorherige = zeile[j];
        zeile[j] = Math.min(
          zeile[j] + 1,                                   // löschen
          zeile[j - 1] + 1,                               // einfügen
          diagonal + (a[i - 1] === b[j - 1] ? 0 : 1));    // ersetzen
      }
    }
    return zeile[n];
  }

  /** Steht das Wort so im Wörterbuch? */
  function kennt(wort) {
    if (!WOERTERBUCH_GROSS) return true;      // ohne Liste nichts anmeckern
    return WOERTERBUCH_GROSS.has(String(wort).toLowerCase());
  }

  function pruefeTippfehler(text, funde) {
    for (const treffer of text.matchAll(WORT_MUSTER)) {
      const wort = treffer[0];
      // Was eine andere Regel schon anfasst, bleibt hier außen vor.
      if (WOERTERBUCH[wort.toLowerCase()] || trenneZusammen(wort)) continue;
      // In Adressen und Pfaden steht kein Deutsch — dort nichts vorschlagen.
      if (istAdresse(text, treffer.index)) continue;
      const vorschlag = tippfehlerVorschlag(wort);
      if (!vorschlag) continue;
      const neu = /^[A-ZÄÖÜ]/.test(wort)
        ? vorschlag[0].toUpperCase() + vorschlag.slice(1)
        : vorschlag;
      if (neu === wort) continue;
      funde.push(machFund(treffer.index, treffer.index + wort.length,
                          wort, neu, 'Tippfehler? Ein Buchstabe daneben', 'tipp', false));
    }
  }

  function findeProbleme(text) {
    // Alles, was ein einzelnes Wort richtigstellt, bekommt bei Überschneidungen
    // den Vorrang vor den Regeln (siehe ohneUeberschneidung).
    const korrekturen = [];
    pruefeWoerter(text, korrekturen);
    pruefeZusammengeschrieben(text, korrekturen);
    pruefeTippfehler(text, korrekturen);
    for (const fund of korrekturen) fund.wortEbene = true;

    /* Wörter, deren Kasten immer wieder stehen geblieben ist, sind so gewollt —
       der Nachname, ein Wort aus der Gegend, ein Fachbegriff. Die App hört auf,
       sie anzumeckern. Was selbst gelernt wurde, bleibt davon unberührt. */
    for (let i = korrekturen.length - 1; i >= 0; i--) {
      const fund = korrekturen[i];
      if (Gelernt.wortEbene(fund) && !Gelernt.wort(fund.alt) && Gelernt.inRuhe(fund.alt)) {
        korrekturen.splice(i, 1);
      }
    }

    wendeRegelnAn(text, ZEICHEN_REGELN, korrekturen);
    wendeRegelnAn(text, GROSS_REGELN, korrekturen);
    wendeRegelnAn(text, GRAMMATIK_REGELN, korrekturen);
    wendeRegelnAn(text, KOMMA_REGELN, korrekturen);
    pruefeKongruenz(text, korrekturen);
    pruefeSatzende(text, korrekturen);

    const hinweise = [];
    pruefeSatzbau(text, hinweise);

    // Erst das zum Ändern, danach das zum Nachdenken.
    return ohneUeberschneidung(korrekturen).concat(hinweise);
  }

  /* ------------------------------------------------------------
     Wortvorhersage

     Nach drei Buchstaben stehen die Wörter zur Wahl, die so anfangen. Wer
     unsicher schreibt, muss das Wort dann nicht mehr zu Ende raten — er
     erkennt es wieder. Wiedererkennen ist leichter als Erinnern, und genau
     darauf beruht jede Schreibhilfe dieser Art.

     Zuerst kommt, was dieser Mensch schon einmal gewählt hat, dann das
     Kürzeste: Kurze Wörter sind die häufigeren.
     ------------------------------------------------------------ */
  function faengtAnMit(anfang, hoechstens = 8) {
    if (!WOERTERBUCH_GROSS) return [];
    const a = String(anfang).toLowerCase();
    if (a.length < 3 || a.length > 20) return [];

    const treffer = [];
    for (const wort of WOERTERBUCH_GROSS) {
      if (wort.length > a.length && wort.startsWith(a)) treffer.push(wort);
    }
    if (!treffer.length) return [];

    const gelernte = Gelernt.daten.woerter || {};
    const schonGewaehlt = new Set(Object.values(gelernte));

    /* Die Reihenfolge entscheidet alles. Zuerst stand hier „das kürzeste
       zuerst" — und bei „wid" kamen Widder und widern, während
       „Widerspruch" fehlte; bei „unt" kamen Untat und untadlig statt
       „Unterlagen". Kurz heißt nicht häufig.

       Jetzt zählt: was dieser Mensch schon einmal gewählt hat, dann was
       im Deutschen ohnehin ständig vorkommt, und erst danach die Länge.

       Und gesucht wird durch die ganze Liste: Die frühere Grenze von 400
       Treffern brach die alphabetische Suche mittendrin ab — bei „ver"
       kam sie nie bis „verstehen". */
    treffer.sort((x, y) =>
      (schonGewaehlt.has(y) ? 1 : 0) - (schonGewaehlt.has(x) ? 1 : 0)
      || (HAEUFIG.has(y) ? 1 : 0) - (HAEUFIG.has(x) ? 1 : 0)
      || x.length - y.length
      || x.localeCompare(y, 'de'));

    return treffer.slice(0, hoechstens);
  }

  return { findeProbleme, Gelernt, vorschlaegeFuer, kennt,
           klingtWie, koelnerPhonetik, faengtAnMit };
})();
