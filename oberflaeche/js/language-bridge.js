/* ============================================================
   Die Sprachbrücke — ein Fehlerstand für alle Prüfer.

   WAS SIE IST UND WAS NICHT.

   Sie prüft nicht selbst. Geprüft wird in pruefung.js, und das seit
   langem: Wörterbuch, Vorschläge, Lautvergleich, die Regeln für Komma
   und Großschreibung, das Gelernte. Eine zweite Prüfung danebenzustellen
   hieße, dasselbe Wörterbuch ein zweites Mal zu führen — und zwei
   Abschriften bleiben nur gleich, solange jemand danebensteht.

   Sie hält den Zustand: welche Fassung des Textes geprüft wurde, welcher
   Prüflauf gerade zählt, was der Mensch angenommen oder weggewinkt hat.
   Das ist die Arbeit, die vorher niemand tat — und ohne die eine späte
   Antwort der KI Fehler an Stellen malt, an denen längst etwas anderes
   steht.

   Die Aufteilung folgt dem, was im Entwurf steht: Die Prüfer besitzen die
   Prüfungslogik, die Brücke besitzt den gemeinsamen Zustand. Dass
   Rechtschreibung und Grammatik dabei in einer Datei liegen statt in
   zweien, ist ausdrücklich erlaubt — die Zielstruktur beschreibt
   Zuständigkeiten, keine Dateinamen.

   WOHER DIE WÖRTER KOMMEN.

   Nicht von hier. Gelernte Wörter und die, die in Ruhe bleiben sollen,
   führt KI.Gedaechtnis; pruefung.js liest sie über Pruefung.Gelernt. Die
   Brücke fragt dort nach und legt keine eigene Liste an. Eine dritte
   Wortliste wäre genau der Zustand, den dieser Umbau abschaffen soll.
   ============================================================ */
'use strict';

const SprachBruecke = (() => {

  /* ------------------------------------------------------------
     Der Prüfer: pruefung.js, in die einheitliche Fehlerform gebracht.

     Ein Fund von dort heißt {von, bis, alt, neu, grund, art} und trägt
     wortEbene, wenn er ein einzelnes Wort richtigstellt. Daraus wird
     hier ein Fehler mit Quelle, Zustand und Fassungsnummer — dieselbe
     Form, in der später auch die KI antwortet.
     ------------------------------------------------------------ */
  function pruefEngineLauf(text, fassung, laufNr) {
    if (typeof Pruefung === 'undefined') return [];

    let funde;
    try {
      funde = Pruefung.findeProbleme(text) || [];
    } catch (grund) {
      /* Ein Prüfer, der stolpert, darf nicht den ganzen Sprachstand
         mitreißen. Die KI kann trotzdem noch antworten. */
      console.warn('Die Prüfung ist gestolpert:', grund);
      return [];
    }

    return funde.map((fund, i) => ({
      id: 'pruefung-' + fassung + '-' + i,
      quelle: fund.wortEbene ? 'rechtschreibung' : 'grammatik',
      art: fund.art,                       // fehler | tipp | hinweis
      von: fund.von,
      bis: fund.bis,
      text: fund.alt,
      vorschlaege: fund.neu ? [fund.neu] : [],
      grund: fund.grund,
      sicherheit: fund.art === 'fehler' ? 1 : 0.6,
      fassung,
      laufNr,
      stand: 'offen',
      fund,                                // das Original, für uebernimm()
    }));
  }

  /* Die KI.

     Sie ist der Grund, warum es die Brücke gibt: Ihre Antwort kommt spät —
     über Ollama bis zu zehn Minuten —, und bis dahin kann der Text ein
     anderer sein. Wer sie ungeprüft ins Blatt legte, malte Wellenlinien
     über Stellen, an denen längst etwas anderes steht.

     Gefragt wird nur, wenn ein Modell gewählt ist. Ohne eines wäre jede
     Prüfung ein Fehlschlag, den niemand bestellt hat. */
  async function kiEngineLauf(text, fassung, laufNr, kenntWort) {
    if (typeof KI === 'undefined' || !KI.verfuegbar || !KI.verfuegbar()) return [];
    if (!text || !text.trim()) return [];

    /* Was der Mensch schon erlaubt hat, geht mit — sonst schlägt die KI
       seinen Nachnamen vor. */
    let eigene = [];
    try {
      const g = KI.Gedaechtnis.lies();
      eigene = Object.keys(g.woerter || {}).concat(Object.keys(g.inRuhe || {}));
    } catch (e) { eigene = []; }

    const { funde, fehler } = await KI.sprachfunde(text, eigene);
    if (fehler || !funde) return [];

    return funde
      .filter((f) => !kenntWort || !kenntWort(f.alt))
      .map((f, i) => ({
        id: 'ki-' + fassung + '-' + laufNr + '-' + i,
        quelle: 'ki',
        art: f.sicherheit >= 0.9 ? 'fehler' : (f.art === 'stil' ? 'hinweis' : 'tipp'),
        von: f.von,
        bis: f.bis,
        text: f.alt,
        vorschlaege: [f.neu],
        grund: f.grund,
        sicherheit: f.sicherheit,
        fassung,
        laufNr,
        stand: 'offen',
        /* Ein Fund in der Form, die das Programm kennt — damit „Ändern"
           in der Seitenleiste auch bei KI-Funden greift. */
        fund: { von: f.von, bis: f.bis, alt: f.alt, neu: f.neu,
                zeigeAlt: f.alt, zeigeNeu: f.neu,
                grund: f.grund,
                art: f.sicherheit >= 0.9 ? 'fehler' : (f.art === 'stil' ? 'hinweis' : 'tipp'),
                wortEbene: /^[A-Za-zÄÖÜäöüß-]+$/.test(f.alt) },
      }));
  }

  return class SprachBrueckeKlasse {
    constructor() {
      this.sprache = 'de-DE';
      this.text = '';
      this.fassung = 0;               // steigt bei jeder Textänderung
      this.laufNr = 0;                // welcher Prüflauf gerade zählt
      this.naechsterLauf = 1;

      this.fehler = [];
      this.weggewinkt = new Set();    // Fehlerkennungen, die nicht mehr kommen sollen
      this.stand = 'ruht';            // ruht | fertig | veraltet
      this.geaendert = null;          // wo sich seit der letzten Prüfung etwas tat
      /* Wird gerufen, wenn sich am Fehlerstand etwas geändert hat —
         etwa weil die KI spät geantwortet hat. Ohne das käme ihre Antwort
         an, und niemand sähe sie: Gezeichnet wird, wenn geprüft wird. */
      this.beiAenderung = null;
    }

    melden() { if (this.beiAenderung) this.beiAenderung(); }

    /* ---- Sprache ---- */

    spracheSetzen(sprache) {
      if (this.sprache === sprache) return;
      this.sprache = sprache;
      this.veralten();
    }

    /* ---- Der Text ---- */

    textSetzen(text) {
      if (this.text === text) return;
      const alt = this.text;
      this.text = text;
      this.fassung++;
      this.aendernGemerkt(alt, text);
      this.veralten();
    }

    /* Wo hat sich der Text geändert?

       Verglichen wird von vorn und von hinten: Was an beiden Enden gleich
       geblieben ist, kann nicht die Änderung sein. Was dazwischen liegt,
       ist sie — und die Längendifferenz sagt, um wie viel alles dahinter
       verrutscht ist.

       Das ist keine Schätzung. Bei „Hallo Welt" → „Hallo schöne Welt"
       stehen vorn sechs und hinten vier Zeichen unverändert; geändert hat
       sich genau die Lücke dazwischen, und alles danach ist sieben Zeichen
       weiter rechts. */
    aendernGemerkt(alt, neu) {
      let vorn = 0;
      const kuerzer = Math.min(alt.length, neu.length);
      while (vorn < kuerzer && alt[vorn] === neu[vorn]) vorn++;

      let hinten = 0;
      while (hinten < kuerzer - vorn
             && alt[alt.length - 1 - hinten] === neu[neu.length - 1 - hinten]) hinten++;

      const bereich = {
        von: vorn,
        bisAlt: alt.length - hinten,
        bisNeu: neu.length - hinten,
        verschiebung: neu.length - alt.length,
      };

      /* Mehrere Änderungen zwischen zwei Prüfungen werden zu einer
         zusammengefasst — die Prüfung sieht ohnehin nur den Endstand. */
      if (!this.geaendert) {
        this.geaendert = bereich;
      } else {
        this.geaendert = {
          von: Math.min(this.geaendert.von, bereich.von),
          bisAlt: Math.max(this.geaendert.bisAlt, bereich.bisAlt),
          bisNeu: Math.max(this.geaendert.bisNeu + bereich.verschiebung, bereich.bisNeu),
          verschiebung: this.geaendert.verschiebung + bereich.verschiebung,
        };
      }
    }

    /* Der Bereich, der geprüft werden muss — mit Sicherheitsrand.

       Ein geändertes Wort kann den Satz davor und danach betreffen:
       Satzgrenzen, Kommas, Groß- und Kleinschreibung. Deshalb wird bis zur
       nächsten Satzgrenze in beide Richtungen ausgedehnt, mindestens aber
       um zweihundert Zeichen. Der Entwurf verlangt genau das (§14). */
    pruefbereich() {
      if (!this.geaendert) return null;
      const rand = 200;
      let von = Math.max(0, this.geaendert.von - rand);
      let bis = Math.min(this.text.length, this.geaendert.bisNeu + rand);

      /* Bis zur Satzgrenze zurück und vor. */
      while (von > 0 && !'.!?\n'.includes(this.text[von - 1])) von--;
      while (bis < this.text.length && !'.!?\n'.includes(this.text[bis])) bis++;
      if (bis < this.text.length) bis++;
      return { von, bis };
    }

    /* Der Text hat sich geändert: Was geprüft war, gilt nicht mehr.

       Verschoben wird hier nichts. Steht vor einem Fehler ein neues Wort,
       rutschen seine Stellen — und ein Fehler an der falschen Stelle ist
       schlimmer als keiner.

       Von selbst geprüft wird deshalb aber nicht. Das Programm prüft, wenn
       jemand „Prüfen" drückt, und dabei bleibt es: Eine Prüfung, die bei
       jeder Tippause im Hintergrund mitläuft, kostet bei neunhundert
       Wörtern spürbar Zeit und niemand hat sie bestellt. */
    veralten() {
      this.stand = 'veraltet';
    }

    /* ---- Wörter: gefragt wird das Gedächtnis, nicht die Brücke ---- */

    kenntWort(wort) {
      if (typeof Pruefung === 'undefined' || !wort) return false;
      return !!(Pruefung.Gelernt.wort(wort) || Pruefung.Gelernt.inRuhe(wort));
    }

    /* ---- Fehler ---- */

    offeneFehler() {
      return this.fehler.filter((f) => f.stand === 'offen');
    }

    fehlerBei(von, bis) {
      return this.offeneFehler().filter((f) => f.von < bis && f.bis > von);
    }

    /* Eine Kennung, die den Fehler überlebt, auch wenn er beim nächsten
       Lauf an anderer Stelle steht: Quelle, Wort, Vorschlag. Die Stelle
       gehört nicht hinein — sonst käme dasselbe weggewinkte Wort im
       nächsten Absatz wieder. */
    static kennung(fehler) {
      return [fehler.quelle, fehler.text, fehler.vorschlaege[0] || ''].join('|');
    }

    wegwinken(id) {
      return this.wegwinkenFehler(this.fehler.find((f) => f.id === id));
    }

    /* „Übergehen" im Rechtsmenü reicht den Fund selbst herein. Nur ihn aus
       der Liste zu nehmen genügt nicht: Beim nächsten Prüfen stünde er
       wieder da, und man übergeht dasselbe zum dritten Mal.

       Gemerkt wird für dieses Fenster, nicht für immer — dafür gibt es
       „Wort in Ruhe lassen", und das schreibt ins Gedächtnis. */
    wegwinkenFund(fund) {
      return this.wegwinkenFehler(this.fehler.find((f) => f.fund === fund));
    }

    wegwinkenFehler(fehler) {
      if (!fehler) return false;
      fehler.stand = 'weggewinkt';
      this.weggewinkt.add(SprachBrueckeKlasse.kennung(fehler));
      return true;
    }

    erledigt(id) {
      const fehler = this.fehler.find((f) => f.id === id);
      if (!fehler) return false;
      fehler.stand = 'erledigt';
      return true;
    }

    /* ---- Prüfen ---- */

    /* Prüft den übergebenen Text und gibt die Funde zurück — in der Form,
       die das Programm schon kennt. Der Prüfer arbeitet sofort; nur die KI
       antwortet später und läuft deshalb nebenher weiter. */
    pruefen(text, mitKI = false) {
      if (typeof text === 'string') this.textSetzen(text);

      const fassung = this.fassung;
      const laufNr = this.naechsterLauf++;
      this.laufNr = laufNr;

      /* Nur den geänderten Bereich neu prüfen, wenn das reicht.

         Bei einem Brief ist der Unterschied nicht zu spüren. Bei einem
         Text von dreißigtausend Wörtern schon: Dort dauert eine volle
         Prüfung mehrere Sekunden, und die lebende Prüfung liefe nach
         jeder Tippause hinein. */
      const bereich = mitKI ? null : this.pruefbereich();

      if (bereich && this.fehler.length) {
        const teil = this.text.slice(bereich.von, bereich.bis);
        const neueImBereich = pruefEngineLauf(teil, fassung, laufNr)
          .map((f) => Object.assign({}, f, {
            von: f.von + bereich.von,
            bis: f.bis + bereich.von,
            id: f.id + '-t' + bereich.von,
            fund: Object.assign({}, f.fund, {
              von: f.fund.von + bereich.von, bis: f.fund.bis + bereich.von,
            }),
          }));

        /* Was außerhalb lag, bleibt — verschoben um das, was sich an
           Länge geändert hat. Verschoben wird nur, was HINTER der
           Änderung stand; davor hat sich nichts bewegt. */
        const v = this.geaendert.verschiebung;
        const bisAlt = this.geaendert.bisAlt;
        const draussen = [];
        for (const f of this.fehler) {
          if (f.stand !== 'offen') { draussen.push(f); continue; }
          if (f.bis <= bereich.von) { draussen.push(f); continue; }
          if (f.von >= bisAlt) {
            /* Dahinter: um die Längendifferenz weiterrücken. */
            const neu = Object.assign({}, f, { von: f.von + v, bis: f.bis + v });
            neu.fund = Object.assign({}, f.fund,
              { von: f.fund.von + v, bis: f.fund.bis + v });
            if (neu.von >= bereich.bis) draussen.push(neu);
            continue;
          }
          /* Mitten im geprüften Bereich: fällt weg, der Lauf hat ihn neu. */
        }

        this.fehler = draussen.concat(
          neueImBereich.filter((f) => !this.weggewinkt.has(SprachBrueckeKlasse.kennung(f))));
      } else {
        const gefunden = pruefEngineLauf(this.text, fassung, laufNr);
        this.fehler = gefunden.filter(
          (f) => !this.weggewinkt.has(SprachBrueckeKlasse.kennung(f)));
      }

      this.geaendert = null;
      this.stand = 'fertig';

      /* Die KI wird nicht bei jedem Lauf gefragt.

         Die lebende Prüfung läuft nach jeder Tippause. Eine Anfrage an
         Ollama dauert bis zu zehn Minuten und rechnet auf demselben
         Rechner, an dem geschrieben wird — sie alle 900 ms zu stellen
         hieße, das Programm unbenutzbar zu machen. Gefragt wird deshalb
         nur, wenn jemand es verlangt: „Gründlich prüfen". */
      if (mitKI) this.kiFragen(fassung, laufNr);
      /* Nur was aus pruefung.js kam, trägt einen Original-Fund. Was die KI
         später beisteuert, hat keinen — es kommt über offeneFehler(). */
      return this.offeneFehler().map((f) => f.fund).filter(Boolean);
    }

    async kiFragen(fassung, laufNr) {
      let gefunden;
      try {
        gefunden = await kiEngineLauf(this.text, fassung, laufNr,
                                      (w) => this.kenntWort(w));
      } catch (grund) {
        console.warn('Die KI hat nicht geantwortet:', grund);
        return;
      }
      /* Beide Fragen müssen ja lauten: Ist es noch derselbe Text, und ist
         es noch derselbe Lauf? Sonst käme die Antwort von vorhin über den
         Text von jetzt. */
      if (this.fassung !== fassung || this.laufNr !== laufNr) return;

      for (const fehler of gefunden) {
        if (this.weggewinkt.has(SprachBrueckeKlasse.kennung(fehler))) continue;
        if (this.kenntWort(fehler.text)) continue;
        /* Was der Prüfer schon gemeldet hat, wird nicht zweimal
           angestrichen — die Vorschläge kommen zusammen. */
        const schon = this.fehler.find((f) => f.stand === 'offen'
          && f.von < fehler.bis && f.bis > fehler.von);
        if (schon) {
          this.zusammenfuehren(schon, fehler);
          continue;
        }
        this.fehler.push(fehler);
      }
      this.melden();
    }

    /* Funde von anderswo — LanguageTool zum Beispiel — in denselben Stand.

       Sie ersetzen nichts: Der Entwurf will einen Fehlerstand, in dem alle
       Quellen zusammenlaufen (§21). Vorher warf „Gründlich prüfen" die
       eigenen Funde weg und zeigte nur die fremden. */
    fremdeFundeAufnehmen(funde, quelle, sicherheit = 0.7) {
      if (!Array.isArray(funde)) return 0;
      let dazu = 0;
      for (const fund of funde) {
        const fehler = {
          id: quelle + '-' + this.fassung + '-' + dazu,
          quelle,
          art: fund.art,
          von: fund.von, bis: fund.bis,
          text: fund.alt,
          vorschlaege: fund.neu ? [fund.neu] : [],
          grund: fund.grund,
          sicherheit,
          fassung: this.fassung, laufNr: this.laufNr,
          stand: 'offen',
          fund,
        };
        if (this.weggewinkt.has(SprachBrueckeKlasse.kennung(fehler))) continue;
        const schon = this.fehler.find((f) => f.stand === 'offen'
          && f.von < fehler.bis && f.bis > fehler.von);
        if (schon) { this.zusammenfuehren(schon, fehler); continue; }
        this.fehler.push(fehler);
        dazu++;
      }
      this.melden();
      return dazu;
    }

    /* Zwei Prüfer über derselben Stelle.

       Der Entwurf sagt, was hier NICHT passieren darf (§21, §22): Ein
       guter Vorschlag darf nicht von einem schlechteren überschrieben
       werden, und es darf nicht einfach der zuletzt eingegangene gelten.

       Also bleiben beide Vorschläge stehen, geordnet nach Sicherheit —
       der beste zuerst, denn den bietet die Oberfläche als Erstes an.
       Doppelte fallen weg: Schlagen Prüfer und KI dasselbe vor, ist das
       ein Vorschlag und nicht zwei.

       Die Begründung kommt von dem, der sicherer ist. Zwei Erklärungen
       für eine Stelle helfen niemandem. */
    zusammenfuehren(bleibt, dazu) {
      const beide = [];
      const nehmen = (fehler) => {
        for (const v of fehler.vorschlaege) {
          if (!v) continue;
          const da = beide.find((e) => e.text === v);
          if (da) { da.sicher = Math.max(da.sicher, fehler.sicherheit); continue; }
          beide.push({ text: v, sicher: fehler.sicherheit });
        }
      };
      nehmen(bleibt);
      nehmen(dazu);
      beide.sort((a, b) => b.sicher - a.sicher);
      bleibt.vorschlaege = beide.map((e) => e.text);

      if (dazu.sicherheit > bleibt.sicherheit) {
        bleibt.grund = dazu.grund || bleibt.grund;
        bleibt.sicherheit = dazu.sicherheit;
        /* Der Fund fürs Programm zeigt auf den besseren Vorschlag. */
        if (bleibt.fund && bleibt.vorschlaege.length) {
          bleibt.fund.neu = bleibt.vorschlaege[0];
          bleibt.fund.zeigeNeu = bleibt.vorschlaege[0];
        }
      }
      /* Woher der Fund kam, bleibt nachvollziehbar. */
      bleibt.auch = (bleibt.auch || []).concat(dazu.quelle);
      return bleibt;
    }

    /* ---- Auskunft ---- */

    auskunft() {
      return {
        stand: this.stand,
        sprache: this.sprache,
        fassung: this.fassung,
        laufNr: this.laufNr,
        offen: this.offeneFehler().length,
        weggewinkt: this.weggewinkt.size,
      };
    }
  };
})();

/* Für die Prüfläufe außerhalb des Fensters (language-bridge.test.js). */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SprachBruecke };
}
