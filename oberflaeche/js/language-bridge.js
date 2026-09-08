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

  /* Die KI. Sie ist das einzige, was es noch nicht gibt — und das einzige,
     wofür die Brücke wirklich gebraucht wird: Ihre Antwort kommt später,
     und bis dahin kann der Text ein anderer sein. */
  async function kiEngineLauf() {
    return [];
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
    }

    /* ---- Sprache ---- */

    spracheSetzen(sprache) {
      if (this.sprache === sprache) return;
      this.sprache = sprache;
      this.veralten();
    }

    /* ---- Der Text ---- */

    textSetzen(text) {
      if (this.text === text) return;
      this.text = text;
      this.fassung++;
      this.veralten();
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
    pruefen(text) {
      if (typeof text === 'string') this.textSetzen(text);

      const fassung = this.fassung;
      const laufNr = this.naechsterLauf++;
      this.laufNr = laufNr;

      const gefunden = pruefEngineLauf(this.text, fassung, laufNr);

      this.fehler = gefunden.filter(
        (f) => !this.weggewinkt.has(SprachBrueckeKlasse.kennung(f)));
      this.stand = 'fertig';

      this.kiFragen(fassung, laufNr);
      /* Nur was aus pruefung.js kam, trägt einen Original-Fund. Was die KI
         später beisteuert, hat keinen — es kommt über offeneFehler(). */
      return this.offeneFehler().map((f) => f.fund).filter(Boolean);
    }

    async kiFragen(fassung, laufNr) {
      let gefunden;
      try {
        gefunden = await kiEngineLauf(this.text, fassung, laufNr);
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
        const schon = this.fehler.find(
          (f) => f.von === fehler.von && f.bis === fehler.bis);
        if (schon) {
          for (const v of fehler.vorschlaege) {
            if (!schon.vorschlaege.includes(v)) schon.vorschlaege.push(v);
          }
          continue;
        }
        this.fehler.push(fehler);
      }
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
