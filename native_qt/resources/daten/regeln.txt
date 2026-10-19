/* ==========================================================================
   Der gemeinsame Wortschatz der Prüfung — EINE Quelle für beide Fassungen.

   Dieselben Wörter braucht die App im Browser (online/js/app.js) und die
   Erweiterung für LibreOffice (libreoffice/schreibhilfe/pruefung.py). Solange
   jede Seite ihre eigene Abschrift trug, liefen sie auseinander, ohne dass es
   auffiel: FOLGT_NEBENSATZ stand in Python mit dreizehn Wörtern mehr da als in
   JavaScript — seit dem Tag, an dem die Übersetzung angelegt wurde, und der
   Vergleich in libreoffice/vergleiche.py lief trotzdem grün durch, weil keiner
   seiner Sätze diese Wörter benutzte.

   Zwei Abschriften bleiben nur gleich, solange jemand danebensteht. Eine Datei
   kann gar nicht erst auseinanderlaufen.

   ZUR FORM: Die Datei ist gleichzeitig gültiges JavaScript und — alles ab der
   geschweiften Klammer — gültiges JSON. Deshalb doppelte Anführungszeichen und
   kein Komma hinter dem letzten Eintrag. JavaScript liest sie als <script> ein,
   Python schneidet den Rumpf heraus und gibt ihn an json.loads. So braucht
   keine Seite die andere zu übersetzen.

   Die Wortgruppen stehen als Listen da, nicht als fertige „a|b|c“-Ketten:
   So sieht man beim Lesen jedes Wort einzeln, und beide Seiten fügen sie
   selbst mit „|“ zusammen.

   NICHT hier: die Regeln selbst. Die tragen Baustücke und Prüfungen als Code
   und lassen sich nicht als Daten hinschreiben — sie stehen weiter auf beiden
   Seiten und werden weiter von libreoffice/vergleiche.py gegeneinander
   gehalten.
   ========================================================================== */
const REGELDATEN =
{

  /* ------------------------------------------------------------------------
     a) Wörter, die ein Rechtschreibprüfer NICHT finden kann
        — weil beide Schreibweisen für sich genommen richtige Wörter sind.
     ------------------------------------------------------------------------ */
  "WOERTERBUCH": {
    /* wider (= gegen) und wieder (= noch einmal): beide Wörter gibt es.
       Der Rechtschreibprüfer sieht hier nichts Falsches. */
    "wiederspiegeln": "widerspiegeln", "wiederspiegelt": "widerspiegelt",
    "wiedersprechen": "widersprechen", "wiederspricht": "widerspricht",
    "wiederspruch": "Widerspruch", "wiederstand": "Widerstand",
    "widerholen": "wiederholen", "widerholt": "wiederholt",
    "widersehen": "Wiedersehen",

    /* ss statt ß, wo die falsche Form ebenfalls ein gültiges Wort ist.
       Nicht aufgenommen: masse/Maße und busse/Buße – „Masse“ und „Busse“
       sind selbst richtige Wörter, das gäbe falsche Treffer. */
    "weiss": "weiß", "gross": "groß",

    /* Zusammengeschrieben: die Tastatur meckert, kennt aber die Trennstelle
       nicht. */
    "garnicht": "gar nicht", "garnichts": "gar nichts",
    "garkein": "gar kein", "garkeine": "gar keine",
    "garkeinen": "gar keinen", "aufjedenfall": "auf jeden Fall",
    "aufeinmal": "auf einmal", "ausversehen": "aus Versehen",
    "zumbeispiel": "zum Beispiel", "immoment": "im Moment",
    "inordnung": "in Ordnung", "imgrunde": "im Grunde",
    "vorallem": "vor allem", "desweiteren": "des Weiteren",
    "nachwievor": "nach wie vor", "zumindestens": "zumindest",
    "zumteil": "zum Teil", "jedesmal": "jedes Mal",

    /* Englisch/Deutsch-Dubletten, die als Wort durchgehen. */
    "tip": "Tipp", "tips": "Tipps", "email": "E-Mail", "emails": "E-Mails"
  },

  /* ------------------------------------------------------------------------
     b) Großschreibung
     ------------------------------------------------------------------------ */

  /* Nach „beim/zum/vom“ wird aus dem Tunwort ein Hauptwort: „beim Schreiben“.
     Diese Wörter sehen genauso aus, sind aber keine Hauptwörter — sie stehen
     vor einem Hauptwort oder bilden eine feste Wendung („zum einen“). */
  "KEIN_HAUPTWORT": [
    "allen", "alten", "anderen", "beiden", "besten", "deinen", "diesen",
    "dritten", "eigenen", "einen", "ersten", "euren", "falschen", "ganzen",
    "gleichen", "großen", "guten", "hohen", "ihren", "jenen", "jungen",
    "kalten", "keinen", "kleinen", "kommenden", "kurzen", "langen",
    "letzten", "meinen", "meisten", "neuen", "nächsten", "richtigen",
    "schönen", "seinen", "selben", "solchen", "teuren", "tiefen",
    "unseren", "vergangenen", "vielen", "vierten", "warmen", "wenigen",
    "wenigsten", "zweiten"
  ],

  /* ------------------------------------------------------------------------
     c) Grammatik: die Verwechslungen, die kein Rechtschreibprüfer sieht
     ------------------------------------------------------------------------ */

  "FUERWOERTER": [
    "ich", "du", "er", "sie", "es", "wir", "ihr", "man"
  ],

  /* Zeitwörter, nach denen „dass“ folgt. Absichtlich nur die gebeugten Formen:
     nach einem Mittelwort („das Buch gelesen, das ich …“) steht oft ein
     Bezugswort, da wäre „das“ richtig. */
  "DENK_ZEITWOERTER": [
    "denke", "denkst", "denkt", "dachte", "dachtest", "dachten", "glaube",
    "glaubst", "glaubt", "glaubte", "glaubten", "hoffe", "hoffst", "hofft",
    "hoffte", "meine", "meinst", "meint", "meinte", "finde", "findest",
    "findet", "fand", "weiß", "weißt", "wissen", "wusste", "wusstest",
    "wussten", "sage", "sagst", "sagt", "sagte", "sagten", "erzähle",
    "erzählst", "erzählt", "erzählte", "verstehe", "verstehst", "versteht",
    "vermute", "vermutest", "vermutet", "fürchte", "fürchtest", "fürchtet",
    "bedeutet", "heißt", "hieß", "merke", "merkst", "merkt", "merkte",
    "sehe", "siehst", "sieht", "höre", "hörst", "hört", "schreibe",
    "schreibst", "schreibt", "schrieb", "verspreche", "versprichst",
    "verspricht", "bemerke", "bemerkt", "entschuldige"
  ],

  /* Zeitwörter ohne Wem-Fall: „Ich glaube, dass der Zug kommt“. Nach „sagen“
     oder „schreiben“ darf hinter dem „das“ auch ein Wem-Fall stehen („Ich
     schreibe das der Firma“) — deshalb stehen die hier nicht mit drin. */
  "DENK_ZEITWOERTER_ENG": [
    "glaube", "glaubst", "glaubt", "glaubte", "denke", "denkst", "denkt",
    "dachte", "meine", "meinst", "meint", "meinte", "hoffe", "hoffst",
    "hofft", "hoffte", "weiß", "weißt", "wusste", "vermute", "vermutet",
    "fürchte", "fürchtet", "verstehe", "versteht", "bedeutet", "heißt"
  ],

  /* Eigenschaftswörter, nach denen ein „dass“-Satz folgt: „Es ist gut, dass …“ */
  "DASS_EIGENSCHAFTEN": [
    "wichtig", "wichtiger", "gut", "schön", "schade", "klar", "froh",
    "sicher", "möglich", "schlimm", "toll", "blöd", "traurig", "nett",
    "richtig", "falsch", "schlecht", "logisch", "normal", "selten"
  ],

  /* Was hinter dem „dass“ stehen darf, ohne dass es ein Bezugswort sein könnte
     — zusätzlich zu den Fürwörtern oben, an die diese Liste angehängt wird.
     „ein/eine“ fehlt mit Absicht: „das eine Auto“ ist richtig so. */
  "FOLGT_NEBENSATZ_ZUSAETZLICH": [
    "die", "der", "den", "dem", "kein", "keine", "keinen"
  ],

  /* Zeitangaben nach „seit“. Das „?“ hinter „Jahren?“ und den anderen gehört
     zum regulären Ausdruck, in den diese Wörter eingesetzt werden. */
  "ZEITANGABEN": [
    "einem", "einer", "dem", "der", "den", "ein", "zwei", "drei", "vier",
    "fünf", "sechs", "sieben", "acht", "neun", "zehn", "vielen",
    "mehreren", "einigen", "kurzem", "langem", "längerem", "geraumer",
    "damals", "gestern", "heute", "neuestem", "jeher", "wann", "Jahren?",
    "Monaten?", "Wochen?", "Tagen?", "Stunden?", "Minuten?",
    "Jahrzehnten?", "Ewigkeiten", "Anfang", "Beginn", "Montag", "Dienstag",
    "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"
  ],

  /* Steigerungsformen. Danach heißt es „als“, nie „wie“. Bewusst als Liste und
     nicht als Endung „-er“: sonst geriete jedes „der wie …“ in die Fänge. */
  "STEIGERUNGEN": [
    "größer", "kleiner", "besser", "schlechter", "schneller", "langsamer",
    "älter", "jünger", "höher", "tiefer", "länger", "kürzer", "stärker",
    "schwächer", "lieber", "teurer", "billiger", "schöner", "hässlicher",
    "einfacher", "leichter", "schwerer", "öfter", "näher", "dicker",
    "dünner", "wärmer", "kälter", "klüger", "dümmer", "lauter", "leiser",
    "glücklicher", "müder", "wichtiger", "schlimmer", "ruhiger", "netter",
    "freundlicher", "klarer", "heller", "dunkler", "weicher", "härter",
    "süßer", "gesünder", "reicher", "ärmer", "sicherer", "genauer",
    "deutlicher", "häufiger", "seltener", "breiter", "schmaler",
    "hübscher", "mehr", "weniger", "anders"
  ],

  /* ------------------------------------------------------------------------
     d) Komma vor dem Nebensatz
     ------------------------------------------------------------------------ */

  /* Wort → braucht es ein Fürwort dahinter, damit es sicher ein Nebensatz ist?
     „damit“ und „während“ gibt es auch ohne Nebensatz („damit bin ich
     zufrieden“, „während des Essens“) — da wäre ein Komma falsch. */
  "NEBENSATZ_WOERTER": [
    ["dass", false],
    ["weil", false],
    ["obwohl", false],
    ["sodass", false],
    ["sobald", false],
    ["solange", false],
    ["bevor", false],
    ["nachdem", false],
    ["falls", false],
    ["sofern", false],
    ["indem", false],
    ["wenn", false],
    ["ob", false],
    ["damit", true],
    ["während", true]
  ],

  /* Steht eines dieser Wörter vor dem Nebensatz-Wort, gehört dort KEIN Komma
     hin — „und dass“, „oder ob“, „so dass“. */
  "KEIN_KOMMA_DAVOR": [
    "aber", "allem", "als", "auch", "außer", "besonders", "dann", "denn",
    "doch", "eben", "egal", "erst", "ganz", "gerade", "geschweige",
    "immer", "je", "kaum", "noch", "nur", "oder", "schon", "selbst", "so",
    "sogar", "sondern", "und", "vor", "wie"
  ],

  /* ------------------------------------------------------------------------
     e) Passt das Zeitwort zum Fürwort?

     „ich habe“, „du hast“, „er hat“ — wer da durcheinanderkommt, hört es beim
     eigenen Lesen oft nicht. Geprüft werden die acht häufigsten Zeitwörter und
     nur die Fürwörter, die eindeutig sind: „sie“, „ihr“ und „es“ bleiben außen
     vor, weil dort beide Formen richtig sein können („sie ist“ und „sie sind“,
     „ihr ist kalt“, „es sind viele gekommen“).
     ------------------------------------------------------------------------ */
  "ZEITWOERTER": [
    { "ich": "bin",    "du": "bist",     "er": "ist",    "wir": "sind" },
    { "ich": "habe",   "du": "hast",     "er": "hat",    "wir": "haben" },
    { "ich": "werde",  "du": "wirst",    "er": "wird",   "wir": "werden" },
    { "ich": "kann",   "du": "kannst",   "er": "kann",   "wir": "können" },
    { "ich": "muss",   "du": "musst",    "er": "muss",   "wir": "müssen" },
    { "ich": "will",   "du": "willst",   "er": "will",   "wir": "wollen" },
    { "ich": "soll",   "du": "sollst",   "er": "soll",   "wir": "sollen" },
    { "ich": "darf",   "du": "darfst",   "er": "darf",   "wir": "dürfen" }
  ],

  /* Welche Spalte oben gilt für welches Fürwort. „man“ wird wie „er“ gebeugt. */
  "SPALTE": { "ich": "ich", "du": "du", "er": "er", "man": "er", "wir": "wir" },

  /* ------------------------------------------------------------------------
     f) Kurze Wörter, die beim Trennen zusammengetippter Wörter als Teil
        gelten dürfen. Die große Wörterliste wäre hier zu großzügig.
     ------------------------------------------------------------------------ */
  "TRENN_KURZ": [
    "aber", "als", "am", "auch", "auf", "aus", "bei", "bin", "bist",
    "bitte", "da", "danke", "dann", "darf", "das", "dass", "dem", "den",
    "denn", "der", "des", "dich", "die", "dir", "doch", "du", "ein",
    "eine", "einem", "einen", "einer", "eines", "er", "es", "euch",
    "freundlichen", "ganz", "gar", "geehrte", "geehrten", "geehrter",
    "guten", "hab", "habe", "haben", "hallo", "hat", "hatte", "herzlichen",
    "hier", "ich", "ihr", "ihre", "ihrem", "ihren", "ihrer", "im", "in",
    "ist", "ja", "jetzt", "kann", "kannst", "kein", "keine", "keinem",
    "keinen", "keiner", "liebe", "lieber", "mag", "mal", "man", "mein",
    "meine", "meinem", "meinen", "meiner", "mich", "mir", "mit", "muss",
    "nach", "nein", "nicht", "noch", "nur", "ob", "oder", "schon", "sehr",
    "sich", "sie", "sind", "soll", "um", "und", "uns", "unser", "unsere",
    "unter", "viel", "viele", "vielen", "von", "vor", "wann", "war",
    "warst", "warum", "weil", "wenn", "wer", "werden", "wie", "will",
    "wir", "wird", "wo", "zu", "zum", "zur", "über"
  ]
};
