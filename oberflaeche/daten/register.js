/* ==========================================================================
   Das Register — die Reiter und Gruppen des Bandes

   Hier steht, was im Band unter welchem Reiter in welcher Gruppe liegt. Es
   ist eine Liste, kein Programm: Wer einen Knopf hinzufügen will, schreibt
   eine Zeile, und das Band baut sich daraus selbst.

   Deshalb steht es in einer eigenen Datei. In programm.js lagen diese 275
   Zeilen mitten zwischen der Arbeitsweise des Bandes — und wer nur einen
   Knopf verschieben wollte, musste erst durch 10.000 Zeilen suchen, in
   denen er nichts zu ändern hatte.

   AUFBAU EINER ZEILE

       ['Kennung des Symbols', 'Beschriftung', () => was es tut, 'gross']

   „gross" macht den Knopf zum großen Knopf oben in der Gruppe; ohne das
   steht er klein darunter. Ein vierter Eintrag als Funktion, die true oder
   false gibt, setzt einen Haken.

   AUFBAU EINER GRUPPE

       ['Name der Gruppe', [ ...Knöpfe... ], () => was der Pfeil unten
                                                   rechts öffnet]

   WAS „w" IST

   Diese Datei kennt das Programm nicht und soll es nicht kennen. Was sie
   von dort braucht, wird ihr gereicht: B mit allen Befehlen und w mit den
   zwölf übrigen Namen. Jeder davon ist eine Funktion, auch die beiden
   Abfragen „papierJetzt" und „querJetzt" — der Haken bei „A4" muss beim
   Aufklappen nachsehen, wie es gerade steht, nicht wie es beim Bauen
   stand.

   Wächst diese Liste, bleibt die Verbindung dieselbe zwölf Namen breit.
   Das ist der Sinn: Man sieht auf einen Blick, woran das Register hängt.
   ========================================================================== */
'use strict';

function REGISTER_BAUEN(B, w) {
  return [
  /* ------------------------------------------------------------
     KEIN DATEI-REITER

     Hier stand einmal ein Reiter „Datei" mit sieben Gruppen. Das war der
     Fehler, an dem der ganze Aufbau hing: WPS Writer hat keinen
     Datei-Reiter. Links vor den Reitern sitzt ein ☰ Menü, und das klappt
     senkrecht auf — Kay hat es abfotografiert.

     Deshalb führt der Aufbau DATEI auch ohne Gruppen auf, als flache
     Liste, während START und EINFÜGEN Gruppen tragen. Das war die
     Ansage, und ich habe sie als Formsache gelesen und Gruppen erfunden.

     Die Punkte des Menüs stehen in MENUES['Datei'] in programm.js —
     einmal, für die Menüleiste und für das ☰ gleichermaßen.
     ------------------------------------------------------------ */
  ['Start', [
    ['Zwischenablage', [['kleben', 'Einfügen', () => B.einfuegen(), 'gross'],
                    ['ohneformat', 'Einfügen ohne Formatierung', () => B.einfuegenOhne()],
                    ['schere', 'Ausschneiden', () => B.ausschneiden()],
                    ['kopie', 'Kopieren', () => B.kopieren()],
                    ['pinsel', 'Format übertragen', () => B.formatUebertragen()],
                    ['wortextras', 'Wort-Extras', (k) => B.wortExtras(k)],
                    /* „Doppelt gemoppelt": Rueckgaengig und Wiederholen
                       stehen im Schnellzugriff oben, wo sie in jedem Reiter
                       erreichbar sind. Hier waren sie ein zweites Mal — und
                       nur hier, also schlechter. */
                    ]],
    /* GENAU NACH SEINEM BILD DER WPS-LEISTE:
         Zeile 1   [Schriftart] [Größe]  A⁺  A⁻  ◇  Aa▾
         Zeile 2   B  I  U▾  S▾  X²  X₂  A  🖍▾  A▾  Ⓐ
       Vorher fuellte sich das Gitter spaltenweise, und dabei kamen Fett
       und Kursiv in verschiedene Zeilen, Hoch- und Tiefgestellt
       auseinander. ['//'] beginnt eine neue Zeile. */
    ['Schriftart', ['felder',
                    ['groesserA', 'Schrift vergrößern', () => B.schriftGroesser()],
                    ['kleinerA', 'Schrift verkleinern', () => B.schriftKleiner()],
                    ['radierer', 'Formatierung löschen', () => B.schlicht()],
                    ['Aa', 'Groß-/Kleinschreibung',
                      { tun: () => B.schreibweise(), klappe: (k) => B.schreibweiseKlappe(k) }],
                    ['//'],
                    ['F', 'Fett', () => B.fett()],
                    ['K', 'Kursiv', () => B.kursiv()],
                    ['U', 'Unterstrichen',
                      { tun: () => B.unter(), klappe: (k) => B.unterstrichKlappe(k) }],
                    ['S', 'Durchgestrichen', () => B.durch()],
                    ['X²', 'Hochgestellt', () => B.hoch()],
                    ['X₂', 'Tiefgestellt', () => B.tief()],
                    ['umriss', 'Zeichenumriss', () => B.zeichenumriss()],
                    ['marker', 'Hervorheben',
                      { tun: (k) => B.hervorhebenJetzt(k), klappe: (k) => B.hervorhebenKlappe(k) }],
                    ['schriftfarbe', 'Schriftfarbe',
                      { tun: (k) => B.schriftfarbeJetzt(k), klappe: (k) => B.schriftfarbeKlappe(k) }],
                    /* Das Ⓐ am Ende der Zeile ist in WPS „Texteffekte". */
                    ['eingeschlossen', 'Texteffekte', () => B.effekt()],
                   ], () => B.schriftartMehr()],
    /* ZWEI ZEILEN NACH SEINEM WPS-BILD:
         Zeile 1  Aufzählung▾  Nummerierung▾  Einzug−  Einzug+  Listenebene  Sortieren  ¶
         Zeile 2  links  zentriert  rechts  Blocksatz  Zeilenabstand▾  Schattierung▾  Rahmen▾
       Der Einzug bleibt als Klappe gebündelt — das hat er ausdrücklich
       so gewollt: „Funktionen, die dieselbe Aufgabe haben, an einem Ort". */
    ['Absatz', [['punkte', 'Aufzählung', () => B.punkte()],
                    ['zahlen', 'Nummerierung', () => B.zahlen()],
                    ['einzug', 'Einzug & Listenebene', [
                      ['Einzug vergrößern', () => B.einzugMehr()],
                      ['Einzug verringern', () => B.einzugWeniger()],
                      ['Genaues Maß…', () => B.einzugGenau()],
                      ['-'],
                      ['Listenebene erhöhen', () => B.ebeneHoeher()],
                      ['Listenebene verringern', () => B.ebeneTiefer()],
                    ]],
                    ['sortieren', 'Sortieren', () => B.sortieren()],
                    ['¶', 'Steuerzeichen', () => B.steuerzeichenZeigen(), false, () => w.an('steuerzeichen')],
                    ['//'],
                    ['links', 'Linksbündig', () => B.links()],
                    ['mitte', 'Zentriert', () => B.mitte()],
                    ['rechts', 'Rechtsbündig', () => B.rechts()],
                    ['block', 'Blocksatz', () => B.block()],
                    ['abstand', 'Zeilenabstand', () => B.absatzabstand()],
                    ['toenung', 'Absatzschattierung', () => B.absatzSchattierung()],
                    ['rahmen', 'Absatzrahmen', () => B.absatzRahmen()]], () => B.einzugGenau()],
    /* ABSATZLAYOUT steht in der Vorlage VOR den Stilen, nicht dahinter.
       Hier stand es einmal umgekehrt, mit der Begründung, es gehöre
       „zwischen Formatvorlagen und Bearbeiten" — das war falsch gelesen.

       Und Zeilenabstand, Absatzrahmen und Absatzschattierung stehen in
       der Vorlage in BEIDEN Gruppen: oben in ABSATZ, wo man sie beim
       Schreiben sucht, und noch einmal hier. Sie waren aus ABSATZ
       herausgenommen worden, weil das doppelt aussah. Es ist nicht
       doppelt, es ist so gewollt. */
    ['Absatzlayout', [['abstand', 'Zeilenabstand', () => B.absatzabstand(), 'gross'],
                    /* „Funktionen, die dieselbe Aufgabe haben, an einem Ort
                       gebuendelt." Der Einzug steht in Start ▸ Absatz, hier
                       nicht mehr — sonst ist es wieder an zwei Stellen. */
                    ['rahmen', 'Absatzrahmen', () => B.absatzRahmen()],
                    ['toenung', 'Absatzschattierung', () => B.absatzSchattierung()]],
                  () => B.einzugGenau()],
    ['Stile', 'katalog'],
    ['Bearbeiten', [['lupe', 'Suchen', () => B.suchen(), 'gross'],
                    ['uebersetzen', 'Ersetzen', () => B.ersetzen()],
                    ['lupe', 'Suchen und Ersetzen', () => w.sucheZeigen(true)],
                    ['allesmark', 'Alles auswählen', () => B.allesMarkieren()],
                    ['objekte', 'Objekte auswählen', () => B.objekteWaehlen()]]],
  ]],

  ['Einfügen', [
    ['Seiten', [['deckblatt', 'Deckblatt', () => B.deckblatt(), 'gross'],
                    ['leereseite', 'Leere Seite', () => B.leereSeite()],
                    ['umbruch', 'Seitenumbruch', () => B.seitenumbruch()]]],
    ['Tabellen', [['tabelle', 'Tabelle einfügen', (knopf) => B.tabelleRaster(knopf), 'gross'],
                    ['schnelltab', 'Schnelltabelle', () => B.schnelltabelle()],
                    ['tabellenblatt', 'Tabellenblatt', () => B.tabellenblatt()],
                    ['toenung', 'Eigenschaften', () => B.tabelleEigenschaften()]]],
    ['Illustrationen', [['bild', 'Bild', () => B.bild(), 'gross'],
                    ['stift', 'Formen', (knopf) => B.formenGalerie(knopf), 'gross'],
                    ['stift', 'Form mit eigener Farbe…', () => B.zeichnen()],
                    ['saeule', 'Diagramm', () => B.diagramm()],
                    ['bildfoto', 'Bildschirmfoto', () => B.screenshot()],
                    ['smartart', 'SmartArt', () => B.smartart()],
                    ['piktogramm', 'Piktogramm', () => B.piktogramm()],
                    ['wordart', 'WordArt', () => B.wordart()]]],
    ['Links', [['kette', 'Hyperlink', () => B.hyperlink(), 'gross'],
                    ['textmarke', 'Lesezeichen / Textmarke', () => B.textmarke()],
                    ['querverweis', 'Querverweis', () => B.querverweis()]]],
    /* „Kopf- und Fusszeile kann man in einem Icon mit Funktion
       zusammenfassen." Ein Knopf, eine Klappe, beide Wege darin. */
    ['Kopf- und Fußzeile', [['kopffuss', 'Kopf- und Fußzeile', [
                      ['Kopfzeile bearbeiten', () => B.kopfzeile(), () => w.an('kopfzeile')],
                      ['Fußzeile bearbeiten', () => B.fusszeile(), () => w.an('fusszeile')],
                      ['-'],
                      ['Seitenzahl einfügen', () => B.seitennummer()],
                    ], 'gross']]],
    ['Text', [['textrahmen', 'Textfeld', () => B.textfeld(), 'gross'],
                    /* „Textbaustein ist ein Pluspunkt fuer Legastheniker,
                       was WPS nicht so in der Form hat. Das gehoert eher in
                       die Schreibhilfe." Steht dort jetzt — hier nicht mehr,
                       damit es nicht an zwei Stellen liegt. */
                    ['initiale', 'Initiale', () => B.initiale()],
                    /* „Uhrzeit und Datum kann man in einer Funktion
                       zusammenfassen." Auf seinem WPS-Bild ist es ein
                       GROSSER Knopf mit Beschriftung darunter und einem
                       Kalender mit Uhr darauf — nicht ein kleiner in der
                       Reihe. */
                    ['datumuhrzeit', 'Datum und Uhrzeit', () => B.datumUhrzeit(), 'gross'],
                    ['ausdatei', 'Text aus Datei', () => B.textAusDatei()]]],
    ['Symbole', [['omega', 'Sonderzeichen', () => B.sonderzeichen(), 'gross'],
                    ['formel', 'Formel', () => B.formel()]]],
  ]],

  ['Seitenlayout', [
    /* Ganz links, wie in WPS: Designs, Farben, Schriftarten, Effekte. */
    ['Designs', [['toenung', 'Designs', (k) => B.designs(k), 'gross'],
                 ['farbe', 'Farben', (k) => B.farbschema(k)],
                 ['Aa', 'Schriftarten', (k) => B.designSchriften(k)],
                 ['texteffekt', 'Effekte', (k) => B.designEffekte(k)]]],
    ['Ränder', [
                    ['raender', 'Ränder', [
                      { name: 'Normal', bild: null, blatt: { oben: 25, unten: 25, links: 32, rechts: 32 },
                        mass: 'Oben: 25 mm   Unten: 25 mm   Links: 32 mm   Rechts: 32 mm',
                        tun: () => w.setzeRandVorgabe('normal')(), haken: () => w.randVorgabeJetzt() === 'normal' },
                      { name: 'Schmal', blatt: { oben: 13, unten: 13, links: 13, rechts: 13 },
                        mass: 'Oben: 13 mm   Unten: 13 mm   Links: 13 mm   Rechts: 13 mm',
                        tun: () => w.setzeRandVorgabe('schmal')(), haken: () => w.randVorgabeJetzt() === 'schmal' },
                      { name: 'Moderat', blatt: { oben: 25, unten: 25, links: 19, rechts: 19 },
                        mass: 'Oben: 25 mm   Unten: 25 mm   Links: 19 mm   Rechts: 19 mm',
                        tun: () => w.setzeRandVorgabe('moderat')(), haken: () => w.randVorgabeJetzt() === 'moderat' },
                      { name: 'Breit', blatt: { oben: 25, unten: 25, links: 51, rechts: 51 },
                        mass: 'Oben: 25 mm   Unten: 25 mm   Links: 51 mm   Rechts: 51 mm',
                        tun: () => w.setzeRandVorgabe('breit')(), haken: () => w.randVorgabeJetzt() === 'breit' },
                      ['-'],
                      { name: 'Benutzerdefinierte Seitenränder…', bild: 'raender',
                        tun: () => B.seitenraender() },
                    ], 'gross']]],
    /* Die vier Raender als Zahlen, mitten im Band — so steht es in WPS. */
    ['Seitenränder', 'raender'],
    ['Seite einrichten', [
                    ['ausrichtung', 'Ausrichtung', [
                      { name: 'Hochformat', blatt: { oben: 25, unten: 25, links: 25, rechts: 25 },
                        tun: () => { if (w.querJetzt()) B.querformat(); }, haken: () => !w.querJetzt() },
                      { name: 'Querformat', bild: 'querformat',
                        tun: () => { if (!w.querJetzt()) B.querformat(); }, haken: () => w.querJetzt() },
                    ], 'gross'],
                    /* In WPS stehen hier hinter A4 und A3 acht chinesische
                       Formate — 8开, 16开, 3号信封 und so fort. Die deutsche
                       Fassung hat dieselbe Form und die Formate, die hier
                       jemand braucht: die A-Reihe, die amerikanischen zwei
                       und die drei Briefumschlaege nach DIN. */
                    ['papiergroesse', 'Größe', [
                      { name: 'A4', mass: '210 × 297 mm', bild: 'papiergroesse',
                        tun: () => w.setzePapier('a4')(), haken: () => w.papierJetzt() === 'a4' },
                      { name: 'A3', mass: '297 × 420 mm', bild: 'papiergroesse',
                        tun: () => w.setzePapier('a3')(), haken: () => w.papierJetzt() === 'a3' },
                      { name: 'A5', mass: '148 × 210 mm', bild: 'papiergroesse',
                        tun: () => w.setzePapier('a5')(), haken: () => w.papierJetzt() === 'a5' },
                      { name: 'B5', mass: '176 × 250 mm', bild: 'papiergroesse',
                        tun: () => w.setzePapier('b5')(), haken: () => w.papierJetzt() === 'b5' },
                      { name: 'Letter', mass: '216 × 279 mm', bild: 'papiergroesse',
                        tun: () => w.setzePapier('letter')(), haken: () => w.papierJetzt() === 'letter' },
                      { name: 'Legal', mass: '216 × 356 mm', bild: 'papiergroesse',
                        tun: () => w.setzePapier('legal')(), haken: () => w.papierJetzt() === 'legal' },
                      { name: 'Umschlag DIN lang', mass: '220 × 110 mm', bild: 'briefumschlag',
                        tun: () => w.setzePapier('dinlang')(), haken: () => w.papierJetzt() === 'dinlang' },
                      { name: 'Umschlag C5', mass: '229 × 162 mm', bild: 'briefumschlag',
                        tun: () => w.setzePapier('c5')(), haken: () => w.papierJetzt() === 'c5' },
                      { name: 'Umschlag C6', mass: '162 × 114 mm', bild: 'briefumschlag',
                        tun: () => w.setzePapier('c6')(), haken: () => w.papierJetzt() === 'c6' },
                      ['-'],
                      { name: 'Weitere Papierformate…', bild: 'papiergroesse',
                        tun: () => B.papierformatFenster() },
                    ], 'gross'],
                    ['spalten', 'Spalten', [
                      { name: 'Eins', bild: 'spalte1', tun: () => B.spaltenSetzen(1), haken: () => w.spaltenJetzt() === 1 },
                      { name: 'Zwei', bild: 'spalte2', tun: () => B.spaltenSetzen(2), haken: () => w.spaltenJetzt() === 2 },
                      { name: 'Drei', bild: 'spalte3', tun: () => B.spaltenSetzen(3), haken: () => w.spaltenJetzt() === 3 },
                      ['-'],
                      { name: 'Mehr Spalten…', bild: 'spalten', tun: () => B.spalten() },
                    ]],
                    ['textrichtung', 'Textrichtung', (k) => B.textrichtung(k)],
                    ['umbruch', 'Umbrüche', [
                      { name: 'Seitenumbruch', bild: 'umbruch', taste: 'Strg+Enter',
                        tun: () => B.seitenumbruch() },
                      { name: 'Spaltenumbruch', bild: 'spaltenumbruch',
                        tun: () => B.spaltenumbruch() },
                      { name: 'Textflussumbruch', bild: 'textflussumbruch', taste: 'Umschalt+Enter',
                        tun: () => B.textflussumbruch() },
                      ['-'],
                      { name: 'Abschnittsumbruch auf nächster Seite', bild: 'abschnitt',
                        tun: () => B.abschnittsumbruch('NextPage') },
                      { name: 'Fortlaufender Abschnittsumbruch', bild: 'abschnittlaufend',
                        tun: () => B.abschnittsumbruch('Continuous') },
                      { name: 'Abschnittsumbruch (gerade Seite)', bild: 'abschnittgerade',
                        tun: () => B.abschnittsumbruch('EvenPage') },
                      { name: 'Abschnittsumbruch auf ungerader Seite', bild: 'abschnittungerade',
                        tun: () => B.abschnittsumbruch('OddPage') },
                    ]],
                    ['zeilennr', 'Zeilennummern', (k) => B.zeilennummern(k)]], () => B.seitenraender()],
    ['Absatz', [['einzug', 'Einzug', () => B.einzugGenau(), 'gross'],
                    ['abstand', 'Absatzabstand', () => B.absatzabstand()],
                    ['trennung', 'Silbentrennung', () => B.silbentrennung(), false, () => w.an('silbentrennung')]], () => B.einzugGenau()],
    ['Seitenhintergrund', [['farbe', 'Seitenfarbe', (k) => B.seitenfarbe(k), 'gross'],
                    ['wasserzeichen', 'Wasserzeichen', () => B.wasserzeichen()],
                    ['rahmen', 'Seitenränder', () => B.seitenraenderRahmen('seite')]]],
    /* Ganz rechts, wie in WPS: Textfluss, Ausrichten, Gruppieren, Drehen. */
    ['Anordnen', [['anordnen', 'Textfluss', () => B.anordnen(), 'gross'],
                  ['ausrichten', 'Ausrichten', (k) => B.objektAusrichten(k)],
                  ['gruppieren', 'Gruppieren', (k) => B.gruppieren(k)],
                  ['objektdrehen', 'Drehen', (k) => B.objektDrehen(k)]]],
  ]],

  ['Referenzen', [
    ['Inhaltsverzeichnis', [['inhalt', 'Inhaltsverzeichnis', () => B.inhaltsverzeichnis(), 'gross'],
                    ['haken', 'Verzeichnisse aktualisieren', () => B.verzeichnisseAktualisieren()]]],
    ['Fußnoten', [['fussnote', 'Fußnote', () => B.fussnote(), 'gross'],
                    ['endnote', 'Endnote', () => B.endnote(), 'gross'],
                    ['vor', 'Nächste Note', () => B.noteWeiter()],
                    ['zurueck', 'Vorige Note', () => B.noteZurueck()],
                    ['bereich', 'Notenbereich', () => B.notenZeigen()]]],
    ['Zitate und Literatur', [['zitat', 'Zitat einfügen', () => B.zitat(), 'gross'],
                    ['eintrag', 'Neue Quelle', () => B.quelleNeu()],
                    ['anpassen', 'Quellen verwalten', () => B.quellenVerwalten()],
                    ['Stil', 'Zitierweise', () => B.zitierweise()],
                    ['inhalt', 'Literaturverzeichnis', () => B.literaturverzeichnis()]]],
    ['Beschriftungen', [['beschriftung', 'Beschriftung', () => B.beschriftung(), 'gross'],
                    ['bild', 'Abbildungsverzeichnis', () => B.abbildungsverzeichnis()],
                    ['querverweis', 'Querverweis', () => B.querverweis()]]],
    ['Index', [['eintrag', 'Indexeintrag', () => B.indexEintrag(), 'gross'],
                    ['inhalt', 'Stichwortverzeichnis', () => B.stichwortverzeichnis()]]],
  ]],

  ['Überprüfen', [
    ['Dokumentprüfung', [['haken', 'Prüfen', () => w.pruefen(), 'gross'],
                    ['gruendlich', 'Gründlich prüfen', () => B.gruendlichPruefen(), 'gross'],
                    ['Duden', 'Rechtschreibung', () => B.rechtschreibung(), false, () => w.an('rechtschreibung')],
                    ['thesaurus', 'Thesaurus', () => B.thesaurus()],
                    ['woerter', 'Wörter zählen', () => B.woerterZaehlen()]]],
    ['Sprache', [['sprache', 'Korrektursprache', () => B.pruefsprache(), 'gross']]],
    ['Barrierefreiheit', [['barrierefrei', 'Barrierefreiheit prüfen', () => B.barrierefrei(), 'gross']]],
    ['Kommentare', [['notiz', 'Neuer Kommentar', () => B.kommentar(), 'gross'],
                    ['vor', 'Nächster Kommentar', () => B.kommentarWeiter()],
                    ['zurueck', 'Voriger Kommentar', () => B.kommentarZurueck()],
                    ['kommentarweg', 'Kommentar löschen', () => B.kommentarWeg()],
                    ['kommentareweg', 'Alle Kommentare löschen', () => B.kommentareAlleWeg()]]],
    ['Änderungen', [['verfolgt', 'Änderungen verfolgen', () => B.verfolgen(), 'gross', () => w.an('verfolgen')],
                    ['markup', 'Markup anzeigen', () => B.markupUmschalten()],
                    ['bereich', 'Überarbeitungsbereich', () => B.ueberarbeitungsbereich()],
                    /* Ohne „gross": Große Knöpfe zeichnet das Band zuerst, und
                       dann stünde das Annehmen vor dem Markup — im Aufbau
                       steht es dahinter. */
                    ['annehmen', 'Änderung annehmen', () => B.aenderungAnnehmen()],
                    ['ablehnen', 'Änderung ablehnen', () => B.aenderungAblehnen()],
                    ['vor', 'Nächste Änderung', () => B.aenderungWeiter()],
                    ['zurueck', 'Vorige Änderung', () => B.aenderungZurueck()],
                    ['alleAn', 'Alle annehmen', () => B.aenderungenUebernehmen()],
                    ['alleAb', 'Alle verwerfen', () => B.aenderungenVerwerfen()]]],
    ['Schützen', [['sperren', 'Bearbeitung sperren', () => B.bearbeitungSperren(), 'gross']]],
  ]],

  ['Schreibhilfe', [
    /* GANZ VORN: was das Lesen erleichtert.

       Es lag über fünf Reiter verstreut — die Lesehilfe unter Ansicht, die
       Silbentrennung im Seitenlayout, die Schriftwahl in den Optionen, der
       Thesaurus unter Überprüfen. Jedes an seinem sachlich richtigen Platz,
       zusammen aber nur zu finden, wenn man weiß, wo man sucht. */
    ['Lesen', [['brille', 'Lesehilfe', () => B.lesehilfe(), 'gross'],
                    ['zeile', 'Zeilenfokus', () => B.zeilenfokus(), false, () => w.an('zeilenfokus')],
                    ['buch', 'Lesemodus', () => B.lesemodus(), false, () => w.an('lesemodus')],
                    ['groesserA', 'Schrift zum Lesen', () => w.optionenOeffnen('schriften')]],
                  () => B.lesehilfe()],
    ['Prüfen', [['haken', 'Dokumentprüfung', [
                      ['Prüfen', () => w.pruefen()],
                      ['Gründlich prüfen', () => B.gruendlichPruefen()],
                      ['-'],
                      ['Welche Hilfe wann', () => B.welcheHilfe()],
                    ], 'gross']]],
    /* Ein SCHALTER, kein Prüflauf. Er zeigte seinen Stand an, tat aber
       etwas anderes: Er rief den Lauf, und der schaltete sich selbst ein.
       Damit stand die Lampe immer auf „an" und ging nie wieder aus. */
    ['Beim Schreiben', [['wellen', 'Rechtschreibprüfung', () => B.rechtschreibung(), false, () => w.an('rechtschreibung')],
                    ['Vorhersage', 'Wortvorhersage', () => B.vorhersage()],
                    ['autokorr', 'AutoKorrektur', () => B.autokorrektur()]]],
    ['Vorlesen', [['vorlesen', 'Vorlesen', [
                      ['Vorlesen', () => B.vorlesen()],
                      ['Ab hier vorlesen', () => B.vorlesenAbSatz()],
                      ['Anhalten', () => B.vorlesenStopp()],
                      ['-'],
                      ['Stimme und Tempo', () => B.stimmeWaehlen()],
                    ], 'gross']]],
    ['Sprache', [['silben', 'Silbentrennung', () => B.silbentrennung(), 'gross', () => w.an('silbentrennung')],
                    ['uebersetzen', 'Übersetzen', () => w.kiUebersetzen()],
                    ['woerterbuch', 'Thesaurus', () => B.thesaurus()],
                    ['sprache', 'Sprache und Prüfung', () => w.optionenOeffnen('sprache')]],
                  () => w.optionenOeffnen('sprache')],
    ['Bausteine', [['baustein', 'Textbausteine', [
                      ['Bausteine verwalten…', () => B.textbausteine()],
                      ['Schnellbaustein einfügen', () => B.schnellbaustein()],
                    ], 'gross']]],
    ['KI', [['ki', 'KI-Korrektur', () => w.kiKorrigieren(), 'gross'],
                    ['vorschlag', 'Vorschläge', () => w.kiVorschlaege(), 'gross']]],
    ['Anzeigen', [['tafel', 'Seitenleiste Schreibhilfe', () => B.tafelZeigen(), 'gross'],
                    ['optionen', 'Optionen', () => Einstellungen.oeffnen()]]],
  ]],

  ['Sendungen', [
    ['Erstellen', [['kette', 'Umschlag', () => B.umschlag(), 'gross'],
                    ['etiketten', 'Etiketten', () => B.etiketten(), 'gross']]],
    ['Seriendruck', [['serie', 'Seriendruck-Assistent', () => B.seriendruck(), 'gross'],
                    ['seriefeld', 'Seriendruckfeld', () => B.seriendruckfeld(), 'gross'],
                    ['adressblock', 'Adressblock', () => B.adressblock()],
                    ['eintrag', 'Regeln', () => B.seriendruckregel()]]],
    ['Vorschau', [['vorschau', 'Ergebnisse anzeigen', () => B.serienVorschau(), 'gross']]],
    ['Formular', [['formfeld', 'Textfeld', () => B.formTextfeld(), 'gross'],
                    ['kaestchen', 'Kontrollkästchen', () => B.formKasten()],
                    ['formknopf', 'Schaltfläche', () => B.formKnopf()]]],
  ]],

  ['Ansicht', [
    /* Die Lesehilfe stand hier kurz als eigene Gruppe. Sie ist nach
       „Schreibhilfe" gewandert, wo jetzt alles beieinandersteht, was das
       Lesen erleichtert — an zwei Stellen wäre es wieder verteilt. Der
       blaue Knopf neben den Reitern führt von überall dorthin. */
    ['Dokumentansichten', [['blattansicht', 'Drucklayout', () => w.setzeLayout('blatt')(), 'gross'],
                    ['lesen', 'Lesemodus', () => B.lesemodus(), 'gross', () => w.an('lesemodus')],
                    ['zweiblatt', 'Zwei Seiten', () => w.setzeLayout('doppelt')()],
                    ['fortlaufend', 'Weblayout', () => w.setzeLayout('web')()],
                    ['gliederung', 'Gliederung', () => B.gliederung()]]],
    ['Anzeigen', [['linealIcon', 'Lineal', () => B.linealZeigen(), false, () => w.an('lineal')],
                    ['linealHochIcon', 'Vertikales Lineal', () => B.linealHochZeigen(), false, () => w.an('linealHoch')],
                    ['netz', 'Gitternetzlinien', () => B.netzlinien(), false, () => w.an('netzlinien')],
                    ['navigation', 'Navigationsbereich', () => B.navigation(), false, () => w.an('navigation')],
                    ['ecken', 'Textbegrenzungen', () => B.markenZeigen(), false, () => w.an('textbegrenzungen')]],
                    /* „doppelt gemoppelt, denn sie ist schon im Reiter
                       Schreibhilfe" — dort steht sie, hier nicht mehr. */
                    () => B.lesehilfe()],
    ['Zoom', [['lupe', 'Vergrößern', () => B.groesser(), 'gross'],
                    ['kleinerLupe', 'Verkleinern', () => B.kleiner(), 'gross'],
                    ['100 %', '100 %', () => B.normal()],
                    ['seitenbreite', 'Seitenbreite', () => B.zoomBreite()],
                    ['eineSeite', 'Eine Seite', () => B.zoomSeite()],
                    ['Prozent', 'Zoom', () => B.zoomStufe()]], () => B.zoomStufe()],
    /* „Anordnen" zeigte auf B.anordnen — das Fenster für Bilder und Formen.
       In der Gruppe „Fenster" ist damit nichts anzufangen; gemeint sind die
       Fenster des Programms. */
    ['Fenster', [['neuesfenster', 'Neues Fenster', () => B.neuesFenster(), 'gross'],
                    ['kacheln', 'Anordnen', [
                      ['Nebeneinander', () => B.fensterNebeneinander()],
                      ['Untereinander', () => B.fensterUntereinander()],
                      ['Kacheln', () => B.fensterKacheln()],
                    ], 'gross'],
                    ['fensterNeben', 'Nebeneinander', () => B.fensterNebeneinander()],
                    ['fensterUnter', 'Untereinander', () => B.fensterUntereinander()],
                    ['kacheln', 'Kacheln', () => B.fensterKacheln()],
                    ['fensterliste', 'Fensterliste', () => B.fensterListe()]]],
    ['Helligkeit', [['automatisch', 'Wie das System', () => w.setzeThema('auto')()],
                    ['hell', 'Immer hell', () => w.setzeThema('light')()],
                    ['dunkel', 'Immer dunkel', () => w.setzeThema('dark')()]]],
    ['Oberfläche', [['anpassen', 'Register anpassen', () => B.registerAnpassen(), 'gross'],
                    ['piktogramm', 'Symbol austauschen', () => B.symbolTauschen()],
                    ['Oberfläche', 'Benutzeroberfläche', () => B.benutzeroberflaeche()],
                    ['menueleiste', 'Menüleiste', () => B.menueleisteZeigen()],
                    ['leisten', 'Symbolleisten', () => B.leistenZeigen()],
                    ['Zurück', 'Vorlagen zurücksetzen', () => B.vorlagenZurueck()]], () => B.registerAnpassen()],
  ]],
];
}
