/* ==========================================================================
   Themenwörter — was in dieser Art Text anders heißt

   Ein Brief ans Amt benutzt andere Wörter als eine Nachricht an einen
   Freund. Nicht andere Grammatik, nicht mehr Wörter — andere. Wer „wid"
   tippt, meint im Widerspruch an die Krankenkasse „Widerspruch" und im
   Gespräch mit dem Nachbarn eher „widerlich". Die Vorhersage konnte das
   bisher nicht wissen: Sie hatte eine einzige Liste mit 355.324 Wörtern und
   keinen Begriff davon, worum es gerade geht.

   Hier steht deshalb je Empfänger, welche Wörter in dieser Lage vorne
   stehen sollen. Die Marken oben in der Schreibhilfe — Amt, Arbeit,
   Freunde, Forum, Bewerbung — schalten zwischen ihnen um.

   ZWEIERLEI TUT EINE LISTE:

   1. Sie SORTIERT. Wer „bes" tippt und „Amt" gewählt hat, bekommt
      „Bescheid" vor „besonders" — beides steht im Wörterbuch, aber nur
      eines schreibt man in einem Widerspruch.

   2. Sie ERGÄNZT. „Widerspruchsfrist", „Rechtsbehelf", „Kostenübernahme",
      „Deckungszusage" stehen in der großen Liste gar nicht drin. Ohne sie
      wurden sie nicht vorgeschlagen UND von der Prüfung als Fehler
      unterringelt — ausgerechnet die Wörter, auf die es in so einem Brief
      ankommt. Was hier steht, kennt das Programm ab sofort.

   FORM. Alles klein und mit Umlauten, wie in daten/woerter.txt. Die
   Schreibweise beim Einsetzen richtet sich ohnehin danach, wie der Anfang
   getippt wurde: Wer „Wid" schreibt, bekommt „Widerspruch".

   UMFANG. 200 bis 400 Wörter je Thema reichen. Es geht nicht um den
   Wortschatz eines Fachgebiets, sondern um den Unterschied zum Alltag. Was
   in jedem Text vorkommt, steht schon in HAEUFIG in pruefung.js und braucht
   hier nicht noch einmal zu stehen.

   Die Namen sind die aus EMPFAENGER in js/ki.js. „egal" bekommt keine
   Liste — wer nichts gewählt hat, soll auch nicht gelenkt werden.
   ========================================================================== */
'use strict';

const THEMENWOERTER = {

  /* ---------- Amt ----------
     Behörde, Jobcenter, Krankenkasse, Versicherung, Gericht. Der Wortschatz
     ist über weite Strecken derselbe: Es geht um einen Vorgang, eine Frist,
     eine Leistung und darum, etwas nachzuweisen. */
  'Amt': (
    /* Der Vorgang und seine Papiere */
    'antrag anträge antragstellung antragsteller antragstellerin bescheid bescheide '
    + 'bescheinigung bescheinigungen widerspruch widerspruchsfrist '
    + 'widerspruchsbescheid einspruch rechtsbehelf rechtsbehelfsbelehrung klage anhörung '
    + 'akteneinsicht aktenzeichen geschäftszeichen vorgang vorgangsnummer kundennummer '
    + 'versichertennummer versicherungsnummer mitgliedsnummer rentenversicherungsnummer '
    + 'steuernummer schreiben anschreiben anlage anlagen nachweis nachweise unterlagen '
    + 'kopie kopien beleg belege quittung formular vordruck erklärung mitteilung '
    + 'benachrichtigung aufforderung erinnerung mahnung bestätigung empfangsbestätigung '
    + 'stellungnahme begründung sachverhalt angelegenheit sachstand sachstandsanfrage '
    + 'wiedervorlage bearbeitungsstand bearbeitungszeit '

    /* Wer dort sitzt */
    + 'sachbearbeiter sachbearbeiterin ansprechpartner ansprechpartnerin behörde behörden '
    + 'amt ämter jobcenter arbeitsagentur agentur sozialamt jugendamt finanzamt ordnungsamt '
    + 'krankenkasse pflegekasse rentenversicherung berufsgenossenschaft versicherung '
    + 'versicherer versicherungsnehmer dienststelle geschäftsstelle widerspruchsstelle '
    + 'abteilung zuständigkeit zuständig unzuständig gericht sozialgericht amtsgericht '
    + 'verwaltungsgericht vollmacht bevollmächtigte bevollmächtigter betreuer betreuerin '

    /* Fristen */
    + 'frist fristen fristgerecht fristwahrend fristablauf rechtzeitig unverzüglich '
    + 'umgehend zeitnah verspätet verjährt eingang eingangsdatum poststempel zugang '
    + 'zugegangen datiert gültig gültigkeit laufzeit kündigungsfrist monatsfrist '
    + 'stichtag termin terminvereinbarung verlängerung '

    /* Geld und Leistung */
    + 'leistung leistungen leistungsbescheid leistungsfall bewilligung bewilligt ablehnung '
    + 'abgelehnt kostenübernahme kostenerstattung erstattung rückerstattung nachzahlung '
    + 'rückzahlung beitrag beiträge beitragsbescheid zuzahlung eigenanteil selbstbeteiligung '
    + 'gebühr gebühren betrag rechnung überweisung lastschrift bankverbindung kontonummer '
    + 'zahlungseingang mahngebühr säumniszuschlag pfändung ratenzahlung stundung '
    + 'bürgergeld wohngeld kindergeld krankengeld arbeitslosengeld grundsicherung '

    /* Versicherung im Besonderen */
    + 'schaden schadensfall schadensmeldung schadennummer police versicherungsschein '
    + 'tarif deckung deckungszusage haftung haftpflicht regulierung gutachten gutachter '
    + 'sachverständiger kulanz obliegenheit vertragsnummer '

    /* Was man tut */
    + 'beantragen beantrage beantragt mitteilen mitteile übersenden übersende übermitteln '
    + 'einreichen einreiche vorlegen vorlege beifügen beigefügt widersprechen widerspreche '
    + 'einlegen einlege bitten ersuchen auffordern bestätigen bestätige nachweisen '
    + 'begründen begründe erläutern kündigen kündige widerrufen widerrufe anfechten '
    + 'beanstanden zurückweisen prüfen überprüfen veranlassen bearbeiten entscheiden '
    + 'gewähren bewilligen ablehnen erstatten überweisen nachreichen absehen '

    /* Die Wendungen, an denen so ein Brief hängt */
    + 'hiermit hierzu hierfür diesbezüglich bezugnehmend bezüglich betreffend '
    + 'gemäß entsprechend beiliegend anbei nachfolgend obenstehend genannten genannte '
    + 'sehr geehrte geehrter geehrten damen herren hochachtungsvoll freundlichen grüßen '
    + 'betreff verbleibe rückfragen rücksprache '

    /* Wie man dort urteilt */
    + 'sachlich rechtswidrig rechtmäßig unrichtig unvollständig unzutreffend '
    + 'nachvollziehbar nachweislich ausdrücklich versehentlich irrtümlich '
    + 'unstrittig strittig erforderlich notwendig zulässig unzulässig begründet '
    + 'unbegründet vorsorglich hilfsweise ergänzend'
  ).split(' '),

  /* ---------- Arbeit ----------
     Der Ton im Haus: Kollegen, Vorgesetzte, Kunden. Höflich, aber nicht
     behördlich — man schreibt „kurz Bescheid geben", nicht „mitteilen". */
  'Arbeit': (
    /* Wer und wo */
    'kollege kollegin kollegen team teams abteilung bereich fachbereich vorgesetzter '
    + 'vorgesetzte chefin geschäftsführung leitung projektleitung führungskraft '
    + 'kunde kundin kunden auftraggeber lieferant dienstleister partner schnittstelle '
    + 'zuständig verantwortlich vertretung urlaubsvertretung '

    /* Termine und Absprachen */
    + 'termin termine besprechung besprechungen meeting jourfixe abstimmung abstimmungen '
    + 'rücksprache absprache runde austausch schaltung telefonat kalender einladung '
    + 'tagesordnung agenda protokoll notizen beschluss ergebnis ergebnisse zusammenfassung '
    + 'verschieben verschoben nachholen vorziehen absagen zusagen anberaumen '

    /* Die Arbeit selbst */
    + 'projekt projekte aufgabe aufgaben vorgang ablauf abläufe prozess prozesse '
    + 'zwischenstand stand fortschritt umsetzung planung entwurf konzept vorlage version '
    + 'freigabe freigegeben abnahme abstimmen umsetzen erledigen erledigt offen '
    + 'anstehend priorität dringend nachrangig aufwand kapazität ressourcen auslastung '
    + 'zuarbeit zulieferung übergabe einarbeitung schulung '

    /* Zeit und Druck */
    + 'deadline abgabe abgabetermin frist fristgerecht zeitplan zeitrahmen meilenstein '
    + 'quartal halbjahr geschäftsjahr wochenanfang wochenende kurzfristig mittelfristig '
    + 'langfristig zeitnah rechtzeitig verzögerung verzögert engpass puffer '

    /* Geld und Papiere */
    + 'angebot angebote auftrag aufträge auftragsbestätigung rechnung rechnungen '
    + 'kostenstelle budget kalkulation nachtrag vertrag verträge vereinbarung konditionen '
    + 'reisekosten spesen stundenzettel zeiterfassung überstunden gleitzeit '

    /* Was man dazu schreibt */
    + 'anhängen angehängt beiliegend weiterleiten weitergeleitet zurückkommen melden '
    + 'bescheid rückmeldung feedback nachfassen erinnern kümmern klären abklären '
    + 'einplanen berücksichtigen bestätigen zusammentragen aufsetzen '
    + 'schauen prüfen sichten durchgehen ergänzen anpassen überarbeiten '

    /* Wendungen */
    + 'hallo moin liebe lieber liebes grüße gruß viele beste danke vorab '
    + 'kurz gerne unkompliziert halber sinnvoll machbar passend '
    + 'gegebenenfalls voraussichtlich vermutlich soweit sobald sofern anbei '
    + 'melde meldet gemeldet halte gehalten laufenden'
  ).split(' '),

  /* ---------- Freunde ----------
     Der Alltag. Hier gehören nicht Fachwörter her, sondern die Wörter, die
     in einem Brief ans Amt nie vorkommen — Wochenende, Kaffee, Kinder. */
  'Freunde': (
    /* Die Leute */
    'freund freundin freunde kumpel nachbar nachbarin nachbarn familie eltern mama papa '
    + 'mutter vater oma opa geschwister bruder schwester kinder kind sohn tochter enkel '
    + 'tante onkel cousin cousine bekannte gruppe leute jungs mädels '

    /* Verabreden */
    + 'treffen treffe getroffen sehen sehe wiedersehen besuch besuchen vorbeikommen '
    + 'vorbeischauen abholen mitkommen mitbringen dabei zusammen gemeinsam spontan '
    + 'lust zeit klappt klappen passt passen melden schreiben anrufen zurückrufen '
    + 'quatschen reden erzählen hören gehört '

    /* Wann */
    + 'heute morgen übermorgen gestern vorgestern gleich nachher später vormittags '
    + 'mittags nachmittags abends nachts wochenende samstag sonntag feiertag brückentag '
    + 'urlaub ferien frei ausschlafen früh spät nächste letzte diese woche wochen '

    /* Was man macht */
    + 'kaffee kuchen frühstück mittagessen abendessen essen kochen backen grillen '
    + 'kneipe restaurant café bar biergarten kino konzert kirmes markt fest geburtstag '
    + 'feier feiern party hochzeit spazieren laufen wandern radfahren schwimmen sport '
    + 'training fußball garten balkon terrasse strand see wald spielen '
    + 'fernsehen serie film musik lesen buch spiel spiele karten '

    /* Wie es geht */
    + 'geht gehts gut prima klasse super schön toll nett lustig witzig komisch '
    + 'anstrengend stressig müde kaputt erschöpft krank erkältet schnupfen fieber '
    + 'besser bessern gesund genesung glückwunsch gratuliere freut freue gefreut '
    + 'schade ärgerlich blöd egal schlimm sorgen mut '

    /* Wendungen */
    + 'hallo hey hi servus moin tschüss ciao bis dann bald liebe liebes '
    + 'grüße grüß dich alles gute liebste lieben dank danke bitte gern gerne '
    + 'ehrlich wirklich eigentlich sowieso irgendwie irgendwann vielleicht bestimmt '
    + 'natürlich klar sicher schon mal halt eben grad einfach ziemlich echt '
    + 'kurz lange nochmal nochmals wieder trotzdem deswegen darum weil'
  ).split(' '),

  /* ---------- Forum ----------
     Öffentlich schreiben: Frage stellen, Antwort geben, ein Problem
     schildern, damit ein Fremder es nachvollziehen kann. */
  'Forum': (
    /* Der Beitrag */
    'beitrag beiträge thread themenstrang thema themen frage fragen antwort antworten '
    + 'kommentar kommentare rückfrage nachfrage nachtrag ergänzung zitat zitieren '
    + 'überschrift titel unterforum kategorie stichwort suchfunktion suche '
    + 'moderator moderation regeln forenregeln nutzer mitglied gast '

    /* Das Problem schildern */
    + 'problem problematik fehler fehlermeldung meldung ursache auslöser symptom '
    + 'verhalten reproduzieren nachstellen auftritt auftreten tritt sporadisch '
    + 'reproduzierbar dauerhaft plötzlich seitdem seither vorher nachher zuvor '
    + 'situation umstände zusammenhang hintergrund beschreibung schilderung '
    + 'beispiel beispiele screenshot bildschirmfoto protokoll ausgabe zeile '

    /* Was man ausprobiert hat */
    + 'versucht probiert getestet ausprobiert neugestartet zurückgesetzt deinstalliert '
    + 'neuinstalliert aktualisiert eingestellt umgestellt geändert überprüft verglichen '
    + 'gesucht gefunden gelesen ohne erfolg erfolglos vergeblich geholfen '
    + 'lösung lösungen ansatz vorschlag hinweis tipp anleitung schritt schritte '
    + 'abhilfe umgehung behelf '

    /* Technik im Alltag */
    + 'rechner laptop handy gerät geräte betriebssystem version programm anwendung '
    + 'einstellung einstellungen konto zugang passwort anmeldung abmeldung netzwerk '
    + 'verbindung internet router drucker datei dateien ordner sicherung update '
    + 'treiber speicher festplatte browser link seite server '

    /* Miteinander reden */
    + 'danke vielen dank vorab hilfe hilfreich weiterhelfen weiterhilft unterstützung '
    + 'gerne ungern bitte entschuldigung sorry richtig falsch stimmt zustimmen '
    + 'widerspruch einwand meinung ansicht erfahrung erfahrungen betroffen betroffene '
    + 'ähnlich gleiches selbe ebenfalls auch ebenso zusätzlich außerdem allerdings '
    + 'jedoch dennoch trotzdem deshalb daher folglich womöglich offenbar scheinbar '
    + 'anscheinend vermutlich möglicherweise eventuell nachvollziehbar verständlich '
    + 'unklar unverständlich ausführlich knapp kurz gefasst zusammengefasst '
    + 'gelöst erledigt behoben funktioniert läuft klappt'
  ).split(' '),

  /* ---------- Bewerbung ----------
     Anschreiben und Lebenslauf. Der Wortschatz ist eng und wiederholt sich —
     genau darum lohnt hier eine Liste am meisten. */
  'Bewerbung': (
    /* Die Papiere */
    'bewerbung bewerbungen bewerber bewerberin anschreiben lebenslauf motivationsschreiben '
    + 'zeugnis zeugnisse arbeitszeugnis abschlusszeugnis zwischenzeugnis zertifikat '
    + 'nachweis referenz referenzen anlage anlagen unterlagen bewerbungsunterlagen '
    + 'mappe portfolio arbeitsprobe arbeitsproben lichtbild '

    /* Die Stelle */
    + 'stelle stellenangebot stellenanzeige stellenausschreibung ausschreibung position '
    + 'aufgabe aufgaben aufgabengebiet tätigkeit tätigkeiten tätigkeitsfeld verantwortung '
    + 'anforderungen anforderungsprofil profil qualifikation qualifikationen voraussetzungen '
    + 'unternehmen firma arbeitgeber haus betrieb branche standort abteilung '
    + 'vollzeit teilzeit befristet unbefristet festanstellung praktikum ausbildung '
    + 'werkstudent volontariat traineeprogramm homeoffice '

    /* Was man mitbringt */
    + 'erfahrung berufserfahrung praxiserfahrung kenntnisse fachkenntnisse vorkenntnisse '
    + 'fähigkeiten stärken werdegang laufbahn studium studiengang abschluss '
    + 'bachelor master diplom lehre weiterbildung fortbildung schulung '
    + 'schwerpunkt spezialisierung fremdsprachen sprachkenntnisse führerschein '
    + 'selbstständig eigenverantwortlich strukturiert sorgfältig zuverlässig belastbar '
    + 'teamfähig kommunikativ lernbereit engagiert motiviert flexibel gewissenhaft '
    + 'lösungsorientiert kundenorientiert '

    /* Der Weg */
    + 'vorstellungsgespräch gespräch einladung auswahlverfahren bewerbungsgespräch '
    + 'probearbeit probezeit eintritt eintrittstermin frühestens kündigungsfrist '
    + 'verfügbar verfügbarkeit gehaltsvorstellung gehalt vergütung jahresgehalt '
    + 'zusage absage rückmeldung entscheidung bescheid nachricht '

    /* Was man schreibt */
    + 'bewerbe bewerben interessiert interesse aufmerksam gelesen gestoßen gefunden '
    + 'reize reizt anspricht überzeugt zutraue zutrauen einbringen beitragen '
    + 'unterstützen mitwirken mitgestalten weiterentwickeln vertiefen anwenden '
    + 'übernehmen verantworten betreut betreute verantwortete leitete begleitete '
    + 'entwickelte erstellte koordinierte organisierte '

    /* Wendungen */
    + 'sehr geehrte geehrter geehrten damen herren hiermit gerne freuen freue '
    + 'freundlichen grüßen kennenlernen persönlich vorstellen '
    + 'überzeugen gelegenheit möglichkeit chance beiliegend anbei entnehmen '
    + 'weiteren angaben rückfragen verfügung stehe bereit baldigen positiven '
    + 'aussagekräftige'
  ).split(' '),
};
