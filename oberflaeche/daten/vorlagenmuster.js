/* ==========================================================================
   Die mitgelieferten Gerüste

   Zehn Dokumente, die niemand von Hand aufbauen sollte, weil ihr Aufbau
   feststeht: wo der Absender hingehört, wo der Betreff, wo die Anrede. Wer
   an dieser Stelle scheitert, scheitert nicht am Schreiben, sondern an
   einer Form, die man kennen muss und nirgends erklärt bekommt.

   SIE SIND LEER. Es steht kein fertiger Brief darin und soll keiner
   darinstehen — nur das Gerüst und in jeder Lücke ein Wort, das sagt, was
   dort hingehört. Was jemand der Krankenkasse schreibt, weiß er selbst;
   dass zwischen Betreff und Anrede eine Leerzeile gehört, weiß er nicht,
   und muss es auch nicht wissen.

   SIE LIEGEN NICHT IM VORLAGENORDNER. Sie werden nicht beim ersten Start
   irgendwohin geschrieben: Der Ordner ~/Vorlagen gehört dem Menschen, und
   ein Programm, das ihn ungefragt mit zehn Dateien füllt, nimmt ihn ihm
   weg. Sie stehen hier, werden ins Blatt gesetzt und sind von da an ein
   Dokument wie jedes andere. Wer eins verändert und behalten will, legt es
   selbst als eigene Vorlage ab — dann steht es im anderen Reiter.

   AUFBAU EINER ZEILE

   Ein Muster ist ein Name, ein Satz darüber, wofür es gut ist, und eine
   Liste von Absätzen. Ein Absatz ist eine Zeichenkette. Darin gilt:

       «Wort»      eine Lücke. Sie fällt im Blatt auf, Tab springt zur
                   nächsten, Tippen ersetzt sie, im Druck ist sie weg.
       ''          eine Leerzeile
       '!Text'     fett — der Betreff, die Überschrift einer Rubrik
       '#Text'     Überschrift des Dokuments (groß, für Lebenslauf & Co.)
       '>Text'     rechtsbündig — Ort und Datum stehen rechts
       '@absender' die eigenen drei Zeilen aus den Benutzerdaten; sind
                   keine hinterlegt, stehen dort Lücken
       '@absender2' dieselben ohne den Namen — im Lebenslauf steht der
                   Name schon in der Zeile darüber
       '@ortdatum' „Berlin, 4. September 2026" — der Ort aus den
                   Benutzerdaten, das Datum von heute, rechtsbündig
       '@name'     der eigene Name, für unter die Unterschrift

   Mehr Zeichen gibt es nicht. Wer ein Muster ändern will, ändert Text —
   kein Programm.

   WAS ZUSAMMENSTEHT, WIRD EIN ABSATZ. Zeilen ohne Leerzeile dazwischen
   werden zu einem Absatz mit Umbrüchen darin — eine Anschrift ist ein
   Block und keine Aufzählung. Erst die Leerzeile fängt einen neuen Absatz
   an, genau wie beim Schreiben. Ausgezeichnete Zeilen (!, #, >) stehen
   immer für sich.

   WARUM DIN 5008 UND NICHT SCHÖNER. Der Aufbau der Briefe ist der der
   Norm: Absender oben, Empfängerfeld darunter, Ort und Datum rechts,
   Betreff ohne das Wort „Betreff", Leerzeile, Anrede. So sehen die Briefe
   aus, die jeden Tag bei Behörden ankommen — und ein Brief, der aussieht
   wie die anderen, wird gelesen wie die anderen.
   ========================================================================== */
'use strict';

const VORLAGENMUSTER = [

['brief', 'Brief',
 'Der gewöhnliche Brief: Absender, Empfänger, Betreff, Anrede, Gruß.', [
  '@absender',
  '',
  '',
  '«Name des Empfängers»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!«Worum es geht»',
  '',
  'Sehr geehrte Damen und Herren,',
  '',
  '«hier steht, was du sagen willst. Ein Satz reicht oft.»',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
]],

['behoerde', 'Brief an eine Behörde',
 'Wie der Brief, aber mit Aktenzeichen — daran findet das Amt deinen Vorgang.', [
  '@absender',
  '',
  '',
  '«Name der Behörde»',
  '«Abteilung oder Sachbearbeiter, falls bekannt»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!«Worum es geht»',
  'Mein Zeichen: «Aktenzeichen, steht oben auf jedem Brief des Amtes»',
  '',
  'Sehr geehrte Damen und Herren,',
  '',
  '«worum du bittest oder was du mitteilst. Kurze Sätze sind hier besser als lange.»',
  '',
  '«Was du mitschickst, steht unten unter „Anlagen".»',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
  '',
  '',
  '!Anlagen',
  '«was du mitschickst»',
]],

['widerspruch', 'Widerspruch',
 'Gegen einen Bescheid, mit dem du nicht einverstanden bist.', [
  '@absender',
  '',
  '',
  '«Name der Behörde»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!Widerspruch gegen den Bescheid vom «TT.MM.JJJJ»',
  'Mein Zeichen: «Aktenzeichen des Bescheids»',
  '',
  'Sehr geehrte Damen und Herren,',
  '',
  'gegen den oben genannten Bescheid lege ich hiermit Widerspruch ein.',
  '',
  '!Begründung',
  '«warum der Bescheid aus deiner Sicht nicht stimmt. Ein oder zwei Sätze reichen; '
  + 'du kannst die Begründung auch nachreichen.»',
  '',
  'Ich bitte Sie, den Bescheid aufzuheben und neu zu entscheiden.',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
]],

['bewerbung', 'Bewerbung',
 'Das Anschreiben. Der Lebenslauf ist ein eigenes Muster.', [
  '@absender',
  '',
  '',
  '«Name der Firma»',
  '«Ansprechpartner, falls einer genannt ist»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!Bewerbung als «Berufsbezeichnung»',
  '',
  'Sehr geehrte «Frau Muster / Herr Muster»,',
  '',
  '«warum du dich bewirbst und wo du die Stelle gefunden hast.»',
  '',
  '«was du bisher gemacht hast und was du gut kannst. Zwei, drei Sätze.»',
  '',
  '«ab wann du anfangen könntest.»',
  '',
  'Über eine Einladung zu einem Gespräch freue ich mich.',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
  '',
  '',
  '!Anlagen',
  'Lebenslauf, «Zeugnisse»',
]],

['lebenslauf', 'Lebenslauf',
 'Tabellarisch, wie er erwartet wird: neueste Sache zuerst.', [
  '#Lebenslauf',
  '',
  '!Persönliche Daten',
  '@name',
  '@absender2',
  'Geboren am «TT.MM.JJJJ» in «Ort»',
  'Telefon: «Nummer»',
  'E-Mail: @mail',
  '',
  '!Berufserfahrung',
  '«MM.JJJJ – MM.JJJJ»  «Tätigkeit», «Firma», «Ort»',
  '«MM.JJJJ – MM.JJJJ»  «Tätigkeit», «Firma», «Ort»',
  '',
  '!Schule und Ausbildung',
  '«MM.JJJJ – MM.JJJJ»  «Abschluss», «Schule oder Betrieb», «Ort»',
  '',
  '!Kenntnisse',
  '«was du kannst — Sprachen, Programme, Führerschein»',
  '',
  '',
  '@ortdatum',
  '',
  '',
  '@name',
]],

['krankmeldung', 'Krankmeldung',
 'An den Arbeitgeber, die Schule oder die Krankenkasse.', [
  '@absender',
  '',
  '',
  '«Name des Empfängers»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!Krankmeldung',
  '',
  'Sehr geehrte Damen und Herren,',
  '',
  'hiermit melde ich mich krank. Ich bin seit dem «TT.MM.JJJJ» arbeitsunfähig, '
  + 'voraussichtlich bis zum «TT.MM.JJJJ».',
  '',
  '«Die Bescheinigung vom Arzt liegt bei / reiche ich nach.»',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
]],

['kuendigung', 'Kündigung',
 'Für einen Vertrag, ein Abonnement, eine Mitgliedschaft.', [
  '@absender',
  '',
  '',
  '«Name der Firma»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!Kündigung «Vertrag oder Mitgliedschaft»',
  'Kundennummer: «Nummer»',
  '',
  'Sehr geehrte Damen und Herren,',
  '',
  'hiermit kündige ich den oben genannten Vertrag zum nächstmöglichen Zeitpunkt.',
  '',
  'Bitte bestätigen Sie mir die Kündigung schriftlich und nennen Sie mir das '
  + 'Datum, zu dem sie wirksam wird.',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
]],

['rechnung', 'Rechnung',
 'Für eine einzelne Leistung. Die Nummer darf es nur einmal geben.', [
  '@absender',
  '',
  '',
  '«Name des Kunden»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '@ortdatum',
  '',
  '!Rechnung Nr. «Nummer»',
  '',
  'Sehr geehrte Damen und Herren,',
  '',
  'für meine Leistung berechne ich Ihnen:',
  '',
  '«Was du gemacht hast»  ·  «Wann»  ·  «Betrag» €',
  '',
  '!Gesamtbetrag: «Betrag» €',
  '',
  '«Im Betrag sind 19 % Umsatzsteuer enthalten. / Kein Ausweis der '
  + 'Umsatzsteuer nach § 19 UStG — Kleinunternehmer. Streich, was nicht gilt.»',
  '',
  'Bitte überweisen Sie den Betrag bis zum «TT.MM.JJJJ» auf das unten genannte Konto.',
  '',
  'Mit freundlichen Grüßen',
  '',
  '',
  '@name',
  '',
  '',
  '!Bankverbindung',
  '«Kontoinhaber»',
  'IBAN «DE00 0000 0000 0000 0000 00»',
  '«Name der Bank»',
  'Steuernummer: «Nummer»',
]],

['einladung', 'Einladung',
 'Geburtstag, Feier, Treffen — wann, wo, und bis wann Bescheid.', [
  '#Einladung',
  '',
  'Liebe «Name», lieber «Name»,',
  '',
  'ich lade dich ein zu «Anlass».',
  '',
  '!Wann',
  '«Tag», den «TT.MM.JJJJ», um «Uhrzeit» Uhr',
  '',
  '!Wo',
  '«Name des Ortes»',
  '«Straße und Hausnummer»',
  '«PLZ und Ort»',
  '',
  '«Was du mitbringen sollst — oder: bring nichts mit.»',
  '',
  'Bitte sag mir bis zum «TT.MM.JJJJ» Bescheid, ob du kommst.',
  '',
  'Ich freue mich auf dich!',
  '',
  '@name',
]],

['protokoll', 'Protokoll',
 'Wer war da, was wurde besprochen, wer macht was bis wann.', [
  '#Protokoll',
  '',
  '!«Thema der Besprechung»',
  '',
  'Datum: «TT.MM.JJJJ», «Uhrzeit» Uhr',
  'Ort: «wo»',
  'Teilnehmer: «wer»',
  'Protokoll: @name',
  '',
  '!Besprochen',
  '«Punkt 1 — was gesagt wurde»',
  '«Punkt 2»',
  '',
  '!Beschlossen',
  '«was entschieden wurde»',
  '',
  '!Wer macht was bis wann',
  '«Name» — «Aufgabe» — bis «TT.MM.JJJJ»',
  '«Name» — «Aufgabe» — bis «TT.MM.JJJJ»',
  '',
  '!Nächster Termin',
  '«TT.MM.JJJJ», «Uhrzeit» Uhr, «Ort»',
]],

];
