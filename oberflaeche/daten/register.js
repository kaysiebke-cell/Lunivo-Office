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
  ['Datei', [
    /* „Aus Vorlage" stand zuerst nur in der Menüleiste. Wer mit dem Band
       arbeitet, sah davon nichts und suchte einen Ordner, zu dem es keinen
       Weg gab. Ein Weg, den nur die Hälfte der Oberfläche kennt, ist keiner. */
    ['Neu', [['neu', 'Neu', () => B.neu(), 'gross'],
                    ['oeffnen', 'Öffnen', () => B.oeffnen(), 'gross'],
                    ['deckblatt', 'Aus Vorlage…', () => B.vorlagenWaehlen(), 'gross'],
                    ['zuletzt', 'Zuletzt geöffnet', () => B.zuletztOeffnen()],
                    ['oeffnen', 'Vorlagenordner öffnen', () => B.vorlagenOrdner()]]],
    /* Hier standen einmal acht Knöpfe für acht Dateiformate — lose
       nebeneinander, und obendrein doppelt: Der Speichern-Dialog des
       Systems bringt dieselbe Auswahl als Klappmenü „Dateityp" mit, samt
       Ordnern und Lesezeichen. Zwei Wege zur selben Sache, und der
       schlechtere nahm den meisten Platz.

       Jetzt zwei Knöpfe, wie im Writer und in Word: speichern, oder
       speichern unter — und dort das Format wählen. Im Menü „Datei"
       stehen die einzelnen Formate weiterhin, für den, der geradewegs
       dorthin will. */
    ['Speichern', [['speichern', 'Speichern', () => B.speichern(), 'gross'],
                    ['unter', 'Speichern unter…', () => B.speichernUnter(), 'gross']],
                  () => B.speichernUnter()],
    ['Drucken', [['drucken', 'Drucken', () => B.drucken(), 'gross'],
                    ['pdf', 'Als PDF', () => B.speichernPdf(), 'gross'],
                    ['vorschau', 'Druckvorschau', () => B.vorschau()],
                    ['drucker2', 'Druckereinstellungen…', () => B.druckerEinrichten()]], () => B.druckerEinrichten()],
    ['Informationen', [['notiz', 'Eigenschaften', () => B.eigenschaften(), 'gross'],
                    ['umbenennen', 'Umbenennen…', () => B.umbenennen()],
                    ['woerter', 'Wörter zählen', () => B.woerterZaehlen()],
                    ['sperren', 'Bearbeitung sperren', () => B.bearbeitungSperren()]]],
    ['Schließen', [['neuesfenster', 'Neues Fenster', () => B.neuesFenster()],
                    ['beenden', 'Beenden', () => B.beenden()]]],
    ['Hilfe', [['handbuch', 'Handbuch', () => B.handbuch(), 'gross'],
                    ['tasten', 'Tastenkürzel', () => B.tastenHilfe()],
                    ['Teile', 'Was zusätzlich geholt wurde', () => B.erweiterungen()],
                    ['ueberprog', 'Über Lunivo-Office', () => B.ueber()]]],
  ]],

  ['Start', [
    ['Zwischenablage', [['kleben', 'Einfügen', () => B.einfuegen(), 'gross'],
                    ['schere', 'Ausschneiden', () => B.ausschneiden()],
                    ['kopie', 'Kopieren', () => B.kopieren()],
                    ['pinsel', 'Format übertragen', () => B.formatUebertragen()],
                    ['ohneformat', 'Einfügen ohne Format', () => B.einfuegenOhne()],
                    ['zurueck', 'Rückgängig', () => B.rueckgaengig()],
                    ['vor', 'Wiederholen', () => B.wiederholen()]]],
    ['Schriftart', ['felder',
                    ['F', 'Fett', () => B.fett()],
                    ['K', 'Kursiv', () => B.kursiv()],
                    ['U', 'Unterstrichen', () => B.unter()],
                    ['S', 'Durchgestrichen', () => B.durch()],
                    ['groesserA', 'Größer', () => B.schriftGroesser()],
                    ['kleinerA', 'Kleiner', () => B.schriftKleiner()],
                    ['X²', 'Hochgestellt', () => B.hoch()],
                    ['X₂', 'Tiefgestellt', () => B.tief()],
                    ['farbe', 'Schriftfarbe', () => B.schriftfarbe()],
                    ['marker', 'Hervorheben', () => B.hervorheben()],
                    ['Aa', 'Groß- und Kleinschreibung', () => B.schreibweise()],
                    ['unterart', 'Art der Unterstreichung…', () => B.unterstrichArt()],
                    ['texteffekt', 'Texteffekt…', () => B.effekt()],
                    ['radierer', 'Format entfernen', () => B.schlicht()]], () => B.effekt()],
    ['Absatz', [['punkte', 'Aufzählung', () => B.punkte()],
                    ['zahlen', 'Nummerierung', () => B.zahlen()],
                    ['ebeneHoch', 'Listenebene höher', () => B.ebeneHoeher()],
                    ['ebeneTief', 'Listenebene tiefer', () => B.ebeneTiefer()],
                    ['links', 'Linksbündig', () => B.links()],
                    ['mitte', 'Zentriert', () => B.mitte()],
                    ['rechts', 'Rechtsbündig', () => B.rechts()],
                    ['block', 'Blocksatz', () => B.block()],
                    ['weniger', 'Einzug verkleinern', () => B.einzugWeniger()],
                    ['mehr', 'Einzug vergrößern', () => B.einzugMehr()],
                    ['abstand', 'Zeilenabstand', () => B.absatzabstand()],
                    ['rahmen', 'Absatzrahmen…', () => B.absatzRahmen()],
                    ['toenung', 'Schattierung…', () => B.absatzSchattierung()],
                    ['sortieren', 'Sortieren…', () => B.sortieren()],
                    ['¶', 'Steuerzeichen', () => B.steuerzeichenZeigen()]], () => B.einzugGenau()],
    ['Formatvorlagen', 'katalog'],
    ['Bearbeiten', [['lupe', 'Suchen und Ersetzen', () => w.sucheZeigen(true), 'gross'],
                    ['allesmark', 'Alles markieren', () => B.allesMarkieren()],
                    ['objekte', 'Objekte wählen', () => B.objekteWaehlen()]]],
  ]],

  ['Einfügen', [
    ['Seiten', [['deckblatt', 'Deckblatt…', () => B.deckblatt(), 'gross'],
                    ['leereseite', 'Leere Seite', () => B.leereSeite()],
                    ['umbruch', 'Seitenumbruch', () => B.seitenumbruch()]]],
    ['Tabellen', [['tabelle', 'Tabelle', () => B.tabelle(), 'gross'],
                    ['schnelltab', 'Schnelltabelle…', () => B.schnelltabelle()],
                    ['tabellenblatt', 'Tabellenblatt…', () => B.tabellenblatt()]]],
    ['Illustrationen', [['bild', 'Bild', () => B.bild(), 'gross'],
                    ['stift', 'Zeichnen', () => B.zeichnen(), 'gross'],
                    ['saeule', 'Diagramm', () => B.diagramm()],
                    ['bildfoto', 'Bildschirmfoto…', () => B.screenshot()],
                    ['smartart', 'SmartArt…', () => B.smartart()],
                    ['piktogramm', 'Piktogramm…', () => B.piktogramm()],
                    ['wordart', 'WordArt…', () => B.wordart()]]],
    ['Links', [['kette', 'Hyperlink', () => B.hyperlink(), 'gross'],
                    ['textmarke', 'Textmarke…', () => B.textmarke()],
                    ['querverweis', 'Querverweis…', () => B.querverweis()]]],
    ['Kopf- und Fußzeile', [['kopfz', 'Kopfzeile', () => B.kopfzeile(), 'gross'],
                    ['fussz', 'Fußzeile', () => B.fusszeile(), 'gross'],
                    ['zahl', 'Seitenzahl', () => B.seitennummer()]]],
    ['Text', [['textrahmen', 'Textfeld', () => B.textfeld(), 'gross'],
                    ['baustein', 'Textbaustein…', () => B.textbausteine(), 'gross'],
                    ['baustein', 'Schnellbaustein…', () => B.schnellbaustein()],
                    ['initiale', 'Initiale', () => B.initiale()],
                    ['datum', 'Datum', () => B.datum()],
                    ['uhrzeit', 'Uhrzeit', () => B.uhrzeit()],
                    ['ausdatei', 'Text aus Datei…', () => B.textAusDatei()]]],
    ['Symbole', [['omega', 'Sonderzeichen', () => B.sonderzeichen(), 'gross'],
                    ['formel', 'Formel…', () => B.formel()]]],
  ]],

  ['Layout', [
    /* Wie im Menüband von Word: „Seitenränder", „Ausrichtung", „Größe" und
       „Umbrüche" sind je ein Knopf mit Klappe, nicht je vier bis fünf
       Knöpfe nebeneinander. Was gerade gilt, trägt in der Klappe einen
       Haken — sonst wüsste man nicht, ob man schon auf A5 steht. */
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
                    ['umbruch', 'Umbrüche', [
                      ['Seitenumbruch', () => B.seitenumbruch()],
                      ['Spaltenumbruch', () => B.spaltenumbruch()],
                      ['Abschnittsumbruch', () => B.abschnittsumbruch()],
                    ], 'gross'],
                    ['spalten', 'Spalten…', () => B.spalten()]], () => B.seitenraender()],
    ['Absatz', [['einzug', 'Einzug genau…', () => B.einzugGenau(), 'gross'],
                    ['abstand', 'Absatzabstand', () => B.absatzabstand()],
                    ['zeilennr', 'Zeilennummern', () => B.zeilennummern()],
                    ['trennung', 'Silbentrennung', () => B.silbentrennung()]], () => B.einzugGenau()],
    ['Seitenhintergrund', [['farbe', 'Seitenfarbe…', () => B.seitenfarbe(), 'gross'],
                    ['wasserzeichen', 'Wasserzeichen…', () => B.wasserzeichen()],
                    ['rahmen', 'Seitenrahmen…', () => B.seitenrahmen()]]],
    ['Anordnen', [['anordnen', 'Bild anordnen…', () => B.anordnen(), 'gross']]],
  ]],

  ['Referenzen', [
    ['Inhaltsverzeichnis', [['inhalt', 'Inhaltsverzeichnis…', () => B.inhaltsverzeichnis(), 'gross'],
                    ['haken', 'Verzeichnisse auffrischen', () => B.verzeichnisseAktualisieren()]]],
    ['Fußnoten', [['fussnote', 'Fußnote', () => B.fussnote(), 'gross'],
                    ['endnote', 'Endnote', () => B.endnote(), 'gross'],
                    ['vor', 'Nächste Note', () => B.noteWeiter()],
                    ['zurueck', 'Vorige Note', () => B.noteZurueck()],
                    ['Zeigen', 'Notenbereich zeigen', () => B.notenZeigen()]]],
    ['Zitate und Literatur', [['zitat', 'Zitat einfügen…', () => B.zitat(), 'gross'],
                    ['Neu', 'Neue Quelle…', () => B.quelleNeu()],
                    ['Verwalten', 'Quellen verwalten…', () => B.quellenVerwalten()],
                    ['Stil', 'Zitierweise', () => B.zitierweise()],
                    ['Literatur', 'Literaturverzeichnis', () => B.literaturverzeichnis()]]],
    ['Beschriftungen', [['beschriftung', 'Beschriftung…', () => B.beschriftung(), 'gross'],
                    ['Abb.', 'Abbildungsverzeichnis…', () => B.abbildungsverzeichnis()],
                    ['querverweis', 'Querverweis…', () => B.querverweis()]]],
    ['Index', [['eintrag', 'Indexeintrag…', () => B.indexEintrag(), 'gross'],
                    ['Stichwort', 'Stichwortverzeichnis…', () => B.stichwortverzeichnis()]]],
  ]],

  ['Überprüfen', [
    ['Dokumentprüfung', [['haken', 'Prüfen', () => w.pruefen(), 'gross'],
                    ['gruendlich', 'Gründlich prüfen', () => B.gruendlichPruefen(), 'gross'],
                    ['Duden', 'Rechtschreibung des Systems', () => B.rechtschreibung()],
                    ['thesaurus', 'Thesaurus…', () => B.thesaurus()],
                    ['woerter', 'Wörter zählen', () => B.woerterZaehlen()]]],
    ['Sprache', [['sprache', 'Sprache für Korrekturhilfen…', () => B.pruefsprache(), 'gross'],
                    ['uebersetzen', 'Übersetzen', () => w.kiUebersetzen()]]],
    ['Barrierefreiheit', [['barrierefrei', 'Barrierefreiheit prüfen', () => B.barrierefrei(), 'gross']]],
    ['Kommentare', [['notiz', 'Neuer Kommentar', () => B.kommentar(), 'gross'],
                    ['vor', 'Nächster', () => B.kommentarWeiter()],
                    ['zurueck', 'Voriger', () => B.kommentarZurueck()],
                    ['kommentarweg', 'Kommentar löschen', () => B.kommentarWeg()],
                    ['kommentareweg', 'Alle Kommentare löschen', () => B.kommentareAlleWeg()]]],
    ['Nachverfolgung', [['verfolgt', 'Änderungen verfolgen', () => B.verfolgen(), 'gross'],
                    ['markup', 'Markup zeigen', () => B.markupUmschalten()],
                    ['bereich', 'Überarbeitungsbereich', () => B.ueberarbeitungsbereich()]]],
    ['Änderungen', [['annehmen', 'Änderung annehmen', () => B.aenderungAnnehmen(), 'gross'],
                    ['ablehnen', 'Änderung ablehnen', () => B.aenderungAblehnen(), 'gross'],
                    ['vor', 'Nächste Änderung', () => B.aenderungWeiter()],
                    ['zurueck', 'Vorige Änderung', () => B.aenderungZurueck()],
                    ['alleAn', 'Alle annehmen', () => B.aenderungenUebernehmen()],
                    ['alleAb', 'Alle verwerfen', () => B.aenderungenVerwerfen()]]],
    ['Schützen', [['sperren', 'Bearbeitung sperren', () => B.bearbeitungSperren(), 'gross']]],
  ]],

  ['Schreibhilfe', [
    ['Prüfen', [['haken', 'Prüfen', () => w.pruefen(), 'gross'],
                    ['gruendlich', 'Gründlich prüfen', () => B.gruendlichPruefen(), 'gross'],
                    ['Welche Hilfe', 'Welche Hilfe wann…', () => B.welcheHilfe()]]],
    ['Beim Schreiben', [['wellen', 'Rechtschreibprüfung', () => B.rechtschreibpruefung()],
                    ['Vorhersage', 'Wortvorhersage', () => B.vorhersage()],
                    ['autokorr', 'AutoKorrektur', () => B.autokorrektur()]]],
    ['Vorlesen', [['vorlesen', 'Vorlesen', () => B.vorlesen(), 'gross'],
                    ['abhier', 'Ab hier vorlesen', () => B.vorlesenAbSatz()],
                    ['halt', 'Anhalten', () => B.vorlesenStopp()],
                    ['stimme', 'Stimme und Tempo…', () => B.stimmeWaehlen()]]],
    ['KI', [['ki', 'KI-Korrektur', () => w.kiKorrigieren(), 'gross'],
                    ['vorschlag', 'Vorschläge holen', () => w.kiVorschlaege(), 'gross'],
                    ['uebersetzen', 'Übersetzen', () => w.kiUebersetzen()]]],
    ['Anzeigen', [['tafel', 'Seitenleiste Schreibhilfe', () => B.tafelZeigen(), 'gross'],
                    ['optionen', 'Optionen…', () => Einstellungen.oeffnen()]]],
  ]],

  ['Sendungen', [
    ['Erstellen', [['kette', 'Umschlag…', () => B.umschlag(), 'gross'],
                    ['etiketten', 'Etiketten…', () => B.etiketten(), 'gross']]],
    ['Seriendruck starten', [['serie', 'Seriendruck-Assistent…', () => B.seriendruck(), 'gross']]],
    ['Felder schreiben', [['seriefeld', 'Seriendruckfeld…', () => B.seriendruckfeld(), 'gross'],
                    ['adressblock', 'Adressblock', () => B.adressblock()],
                    ['Regel', 'Regel…', () => B.seriendruckregel()]]],
    ['Vorschau', [['vorschau', 'Vorschau auf Ergebnisse…', () => B.serienVorschau(), 'gross']]],
    ['Formular', [['formfeld', 'Textfeld', () => B.formTextfeld(), 'gross'],
                    ['kaestchen', 'Kontrollkästchen', () => B.formKasten()],
                    ['formknopf', 'Schaltfläche', () => B.formKnopf()]]],
    ['Makros', [['aufnahme', 'Aufzeichnen', () => B.makroAufnahme(), 'gross'],
                    ['aufnahmeende', 'Aufnahme beenden', () => B.makroBeenden()],
                    ['abspielen', 'Abspielen…', () => B.makroAbspielen()],
                    ['Verwalten', 'Verwalten…', () => B.makrosVerwalten()]]],
  ]],

  ['Ansicht', [
    ['Ansichten', [['blattansicht', 'Blatt (Druckbild)', () => w.setzeLayout('blatt')(), 'gross'],
                    ['lesen', 'Lesemodus', () => B.lesemodus(), 'gross'],
                    ['zweiblatt', 'Zwei Blätter nebeneinander', () => w.setzeLayout('doppelt')()],
                    ['fortlaufend', 'Fortlaufend (ohne Rand)', () => w.setzeLayout('web')()],
                    ['gliederung', 'Gliederung', () => B.gliederung()]]],
    ['Anzeigen', [['linealIcon', 'Lineal', () => B.linealZeigen()],
                    ['netz', 'Netzlinien', () => B.netzlinien()],
                    ['navigation', 'Navigationsbereich', () => B.navigation()],
                    ['steuerzeichen', 'Steuerzeichen', () => B.steuerzeichenZeigen()],
                    ['ecken', 'Textbegrenzungen', () => B.markenZeigen()],
                    ['tafel', 'Seitenleiste Schreibhilfe', () => B.tafelZeigen()],
                   ['brille', 'Lesehilfe…', () => B.lesehilfe(), 'gross'],
                   ['zeile', 'Zeilenfokus', () => B.zeilenfokus()]], () => B.lesehilfe()],
    ['Zoom', [['lupe', 'Vergrößern', () => B.groesser(), 'gross'],
                    ['kleinerLupe', 'Verkleinern', () => B.kleiner(), 'gross'],
                    ['100 %', 'Normalgröße', () => B.normal()],
                    ['seitenbreite', 'Seitenbreite', () => B.zoomBreite()],
                    ['eineSeite', 'Eine Seite', () => B.zoomSeite()],
                    ['Prozent', 'In Prozent…', () => B.zoomStufe()]], () => B.zoomStufe()],
    ['Fenster', [['neuesfenster', 'Neues Fenster', () => B.neuesFenster(), 'gross'],
                    ['Ordnen', 'Anordnen…', () => B.anordnen()],
                    ['fensterNeben', 'Nebeneinander', () => B.fensterNebeneinander()],
                    ['fensterUnter', 'Untereinander', () => B.fensterUntereinander()],
                    ['kacheln', 'Kacheln', () => B.fensterKacheln()],
                    ['fensterliste', 'Fensterliste', () => B.fensterListe()]]],
    ['Helligkeit', [['automatisch', 'Wie das System', () => w.setzeThema('auto')()],
                    ['hell', 'Immer hell', () => w.setzeThema('light')()],
                    ['dunkel', 'Immer dunkel', () => w.setzeThema('dark')()]]],
    ['Oberfläche', [['anpassen', 'Register anpassen…', () => B.registerAnpassen(), 'gross'],
                    ['piktogramm', 'Symbol austauschen…', () => B.symbolTauschen()],
                    ['Oberfläche', 'Benutzeroberfläche…', () => B.benutzeroberflaeche()],
                    ['menueleiste', 'Menüleiste', () => B.menueleisteZeigen()],
                    ['leisten', 'Symbolleisten', () => B.leistenZeigen()],
                    ['Vorlagen', 'Formatvorlagen verwalten…', () => B.vorlagenVerwalten()],
                    ['Zurück', 'Vorlagen zurücksetzen', () => B.vorlagenZurueck()]], () => B.registerAnpassen()],
  ]],

];
}
