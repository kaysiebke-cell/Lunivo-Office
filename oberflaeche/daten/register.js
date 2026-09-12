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
                    ['zurueck', 'Verlauf', [
                      ['Rückgängig', () => B.rueckgaengig()],
                      ['Wiederholen', () => B.wiederholen()],
                    ]]]],
    ['Schriftart', ['felder',
                    ['groesserA', 'Schrift vergrößern', () => B.schriftGroesser()],
                    ['kleinerA', 'Schrift verkleinern', () => B.schriftKleiner()],
                    ['radierer', 'Formatierung löschen', () => B.schlicht()],
                    ['F', 'Fett', () => B.fett()],
                    ['K', 'Kursiv', () => B.kursiv()],
                    ['U', 'Unterstrichen', () => B.unter()],
                    ['S', 'Durchgestrichen', () => B.durch()],
                    ['X²', 'Hochgestellt', () => B.hoch()],
                    ['X₂', 'Tiefgestellt', () => B.tief()],
                    ['marker', 'Hervorheben', () => B.hervorheben()],
                    ['farbe', 'Schriftfarbe', () => B.schriftfarbe()],
                    ['Aa', 'Groß-/Kleinschreibung', () => B.schreibweise()],
                    ['unterart', 'Unterstreichungsart', () => B.unterstrichArt()],
                    ['texteffekt', 'Texteffekte', () => B.effekt()]], () => B.effekt()],
    ['Absatz', [['punkte', 'Aufzählung', () => B.punkte()],
                    ['zahlen', 'Nummerierung', () => B.zahlen()],
                    ['einzug', 'Einzug & Listenebene', [
                      ['Einzug verringern', () => B.einzugWeniger()],
                      ['Einzug vergrößern', () => B.einzugMehr()],
                      ['-'],
                      ['Listenebene erhöhen', () => B.ebeneHoeher()],
                      ['Listenebene verringern', () => B.ebeneTiefer()],
                    ]],
                    ['links', 'Linksbündig', () => B.links()],
                    ['mitte', 'Zentriert', () => B.mitte()],
                    ['rechts', 'Rechtsbündig', () => B.rechts()],
                    ['block', 'Blocksatz', () => B.block()],
                    ['abstand', 'Zeilenabstand', () => B.absatzabstand()],
                    ['rahmen', 'Absatzrahmen', () => B.absatzRahmen()],
                    ['toenung', 'Absatzschattierung', () => B.absatzSchattierung()],
                    ['sortieren', 'Sortieren', () => B.sortieren()],
                    ['¶', 'Steuerzeichen', () => B.steuerzeichenZeigen(), false, () => w.an('steuerzeichen')]], () => B.einzugGenau()],
    /* ABSATZLAYOUT steht in der Vorlage VOR den Stilen, nicht dahinter.
       Hier stand es einmal umgekehrt, mit der Begründung, es gehöre
       „zwischen Formatvorlagen und Bearbeiten" — das war falsch gelesen.

       Und Zeilenabstand, Absatzrahmen und Absatzschattierung stehen in
       der Vorlage in BEIDEN Gruppen: oben in ABSATZ, wo man sie beim
       Schreiben sucht, und noch einmal hier. Sie waren aus ABSATZ
       herausgenommen worden, weil das doppelt aussah. Es ist nicht
       doppelt, es ist so gewollt. */
    ['Absatzlayout', [['abstand', 'Zeilenabstand', () => B.absatzabstand(), 'gross'],
                    ['einzug', 'Einzug genau', () => B.einzugGenau()],
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
    ['Kopf- und Fußzeile', [['kopfz', 'Kopfzeile', () => B.kopfzeile(), 'gross', () => w.an('kopfzeile')],
                    ['fussz', 'Fußzeile', () => B.fusszeile(), 'gross', () => w.an('fusszeile')],
                    ['zahl', 'Seitenzahl', () => B.seitennummer()]]],
    ['Text', [['textrahmen', 'Textfeld', () => B.textfeld(), 'gross'],
                    ['baustein', 'Bausteine', [
                      ['Textbaustein', () => B.textbausteine()],
                      ['Schnellbaustein', () => B.schnellbaustein()],
                    ], 'gross'],
                    ['initiale', 'Initiale', () => B.initiale()],
                    ['datum', 'Datum', () => B.datum()],
                    ['uhrzeit', 'Uhrzeit', () => B.uhrzeit()],
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
    /* „Anordnen" wie in WPS: Was frei auf der Seite liegt, laesst sich
       stellen und drehen. */
    ['Anordnen', [['ausrichten', 'Ausrichten', (k) => B.objektAusrichten(k)],
                  ['objektdrehen', 'Drehen', (k) => B.objektDrehen(k)]]],
    ['Seite einrichten', [
                    ['raender', 'Seitenränder', [
                      ['Normal (2,5 cm)', () => w.setzeRandVorgabe('normal')()],
                      ['Schmal (1,3 cm)', () => w.setzeRandVorgabe('schmal')()],
                      ['Mittel', () => w.setzeRandVorgabe('mittel')()],
                      ['Breit', () => w.setzeRandVorgabe('breit')()],
                      ['-'],
                      ['Eigene Ränder…', () => B.seitenraender()],
                    ], 'gross'],
                    ['ausrichtung', 'Ausrichtung', [
                      ['Hochformat', () => { if (w.querJetzt()) B.querformat(); }, () => !w.querJetzt()],
                      ['Querformat', () => { if (!w.querJetzt()) B.querformat(); }, () => w.querJetzt()],
                    ], 'gross'],
                    ['papiergroesse', 'Papierformat', [
                      ['A4 (21 × 29,7 cm)', () => w.setzePapier('a4')(), () => w.papierJetzt() === 'a4'],
                      ['A5 (14,8 × 21 cm)', () => w.setzePapier('a5')(), () => w.papierJetzt() === 'a5'],
                      ['A3 (29,7 × 42 cm)', () => w.setzePapier('a3')(), () => w.papierJetzt() === 'a3'],
                      ['Letter (21,6 × 27,9 cm)', () => w.setzePapier('letter')(), () => w.papierJetzt() === 'letter'],
                      ['Legal (21,6 × 35,6 cm)', () => w.setzePapier('legal')(), () => w.papierJetzt() === 'legal'],
                    ], 'gross'],
                    ['spalten', 'Spalten', () => B.spalten()],
                    ['umbruch', 'Umbruch', [
                      ['Seitenumbruch', () => B.seitenumbruch()],
                      ['Spaltenumbruch', () => B.spaltenumbruch()],
                      ['Abschnittsumbruch', () => B.abschnittsumbruch()],
                    ]]], () => B.seitenraender()],
    ['Absatz', [['einzug', 'Einzug', () => B.einzugGenau(), 'gross'],
                    ['abstand', 'Absatzabstand', () => B.absatzabstand()],
                    ['zeilennr', 'Zeilennummern', () => B.zeilennummern(), false, () => w.an('zeilennummern')],
                    ['trennung', 'Silbentrennung', () => B.silbentrennung(), false, () => w.an('silbentrennung')]], () => B.einzugGenau()],
    ['Textumbruch', [['anordnen', 'Textumbruch', () => B.anordnen(), 'gross']]],
    ['Seitenhintergrund', [['farbe', 'Seitenfarbe', () => B.seitenfarbe(), 'gross'],
                    ['wasserzeichen', 'Wasserzeichen', () => B.wasserzeichen()],
                    ['rahmen', 'Seitenrahmen', () => B.seitenrahmen()]]],
    ['Anordnen', [['anordnen', 'Bild/Objekt anordnen', () => B.anordnen(), 'gross']]],
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
                    ['ecken', 'Textbegrenzungen', () => B.markenZeigen(), false, () => w.an('textbegrenzungen')],
                    ['tafel', 'Seitenleiste Schreibhilfe', () => B.tafelZeigen(), false, () => w.an('tafel')]], () => B.lesehilfe()],
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
