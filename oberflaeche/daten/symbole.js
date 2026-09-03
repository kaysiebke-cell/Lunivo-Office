/* ==========================================================================
   Die Zeichnungen der Oberfläche

   Jedes Symbol ist ein Pfad in einem Feld von 24 × 24, gezeichnet mit
   Strichen und ohne Füllung.

   HERKUNFT. Die meisten stammen aus Lucide (lucide.dev), einem freien
   Symbolsatz unter der ISC-Lizenz — derselben Bauart wie unsere: 24 × 24,
   Strich, runde Enden, keine Füllung. Sie wurden nicht abgemalt, sondern
   umgerechnet: Lucide setzt jede Form einzeln (<circle>, <rect>, <line>),
   unser symbol() setzt genau einen <path>. Aus einem Kreis werden zwei
   Halbbögen, aus einem Rechteck vier Linien.

   Dabei lauerte eine Falle: Ein Pfad, der mit kleinem "m" beginnt, meint
   allein stehend absolute Koordinaten — hinter einen anderen gehängt aber
   plötzlich relative, und die Zeichnung fällt auseinander. Deshalb steht
   dort jetzt ein großes M und dahinter ein ausdrückliches kleines l.

   Ein paar Symbole sind von Hand geblieben, weil sie etwas meinen, wofür
   ein allgemeiner Satz kein Bild hat: Kopfzeile, Fußzeile, Seitenzahl,
   Textbegrenzungen. Die kennt nur ein Schreibprogramm.

   WARUM PFADE UND KEINE .svg-DATEIEN. Wegen der Farbe. Gezeichnet wird mit
   "currentColor" — das Symbol nimmt die Farbe der Umgebung an. Deshalb ist
   es im hellen Modus dunkel und im dunklen hell, ohne zwei Sätze, und
   deshalb wird beim Überfahren eines Knopfes das Bild mit heller. Ein
   <img src="…svg"> kann das nicht. Der übliche Ausweg, eine Sammeldatei
   mit <use href="datei.svg#name">, führt hier auch nicht weiter: WebKit
   lädt keine Verweise in fremde Dateien, und dieses Programm läuft auf
   WebKit.

   EINE ZEICHNUNG AUSTAUSCHEN. In werkzeug/symbole.html liegen alle 1800
   Symbole von Lucide nebeneinander, mit Suchfeld — oben die, die hier
   benutzt werden. Ein Klick legt die fertige Zeile in die Zwischenablage;
   sie ersetzt dann einfach die alte hier. Kein Netz nötig, der Katalog
   liegt in daten/symbolkatalog.js.

   Ein Symbol prüfen, ohne das Programm zu starten:
       <svg viewBox="0 0 24 24" width="96" height="96" fill="none"
            stroke="#000" stroke-width="1.7" stroke-linecap="round"
            stroke-linejoin="round"><path d="HIER DER PFAD"/></svg>

   Lucide steht unter der ISC-Lizenz (Copyright Lucide Contributors), die
   Weitergabe erlaubt. Der Lizenztext liegt in doku/LIZENZ-LUCIDE.txt.
   ========================================================================== */

const SYMBOLE = {
  vorlesen:   'M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z M16 9a5 5 0 0 1 0 6 M19.364 18.364a9 9 0 0 0 0-12.728',   /* lucide: volume-2 */
  hoeren:     'M6 8.5a6.5 6.5 0 1 1 13 0c0 6-6 6-6 10a3.5 3.5 0 1 1-7 0 M15 8.5a2.5 2.5 0 0 0-5 0v1a2 2 0 1 1 0 4',   /* lucide: ear */
  brille:     'M2 15a4 4 0 1 0 8 0a4 4 0 1 0 -8 0 M14 15a4 4 0 1 0 8 0a4 4 0 1 0 -8 0 M14 15a2 2 0 0 0-2-2 2 2 0 0 0-2 2 M2.5 13 5 7c.7-1.3 1.4-2 3-2 M21.5 13 19 7c-.7-1.3-1.5-2-3-2',   /* lucide: glasses */
  zeile:      'M3 7V5a2 2 0 0 1 2-2h2 M17 3h2a2 2 0 0 1 2 2v2 M21 17v2a2 2 0 0 1-2 2h-2 M7 21H5a2 2 0 0 1-2-2v-2 M7 12h10',   /* lucide: scan-line */
  ohneformat:    'M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-6a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1z M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2 M9 12v-1h6v1 M11 17h2 M12 11v6',   /* lucide: clipboard-type */
  groesserA:     'M14 11 l4-4 4 4 M18 16V7 M2 16 l4.039-9.69a.5.5 0 0 1 .923 0L11 16 M3.304 13h6.392',   /* lucide: a-arrow-up */
  kleinerA:      'M14 12 l4 4 4-4 M18 16V7 M2 16 l4.039-9.69a.5.5 0 0 1 .923 0L11 16 M3.304 13h6.392',   /* lucide: a-arrow-down */
  unterart:      'M6 4v6a6 6 0 0 0 12 0V4 M4 20L20 20',   /* lucide: underline */
  texteffekt:    'M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z M20 2v4 M22 4h-4 M2 20a2 2 0 1 0 4 0a2 2 0 1 0 -4 0',   /* lucide: sparkles */
  ebeneHoch:     'M8 5h13 M13 12h8 M13 19h8 M3 10a2 2 0 0 0 2 2h3 M3 5v12a2 2 0 0 0 2 2h3',   /* lucide: list-tree */
  ebeneTief:     'M10 6h11 M10 12h11 M10 18h11 M6 4h.01 M6 10h.01 M6 16h.01 M4 19l2 2 2-2',   /* von Hand */
  toenung:       'M11 7 6 2 M18.992 12H2.041 M21.145 18.38A3.34 3.34 0 0 1 20 16.5a3.3 3.3 0 0 1-1.145 1.88c-.575.46-.855 1.02-.855 1.595A2 2 0 0 0 20 22a2 2 0 0 0 2-2.025c0-.58-.285-1.13-.855-1.595 M8.5 4.5 l2.148-2.148a1.205 1.205 0 0 1 1.704 0l7.296 7.296a1.205 1.205 0 0 1 0 1.704l-7.592 7.592a3.615 3.615 0 0 1-5.112 0l-3.888-3.888a3.615 3.615 0 0 1 0-5.112L5.67 7.33',   /* lucide: paint-bucket */
  sortieren:     'M3 16 l4 4 4-4 M7 20V4 M20 8h-5 M15 10V6.5a2.5 2.5 0 0 1 5 0V10 M15 14h5l-5 6h5',   /* lucide: arrow-down-a-z */
  allesmark:     'M12.034 12.681a.498.498 0 0 1 .647-.647l9 3.5a.5.5 0 0 1-.033.943l-3.444 1.068a1 1 0 0 0-.66.66l-1.067 3.443a.5.5 0 0 1-.943.033z M5 3a2 2 0 0 0-2 2 M19 3a2 2 0 0 1 2 2 M5 21a2 2 0 0 1-2-2 M9 3h1 M9 21h2 M14 3h1 M3 9v1 M21 9v2 M3 14v1',   /* lucide: square-dashed-mouse-pointer */
  objekte:       'M4.037 4.688a.495.495 0 0 1 .651-.651l16 6.5a.5.5 0 0 1-.063.947l-6.124 1.58a2 2 0 0 0-1.438 1.435l-1.579 6.126a.5.5 0 0 1-.947.063z',   /* lucide: mouse-pointer-2 */
  leereseite:    'M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z M14 2v5a1 1 0 0 0 1 1h5',   /* lucide: file */
  schnelltab:    'M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18',   /* lucide: table-2 */
  tabellenblatt: 'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M3 9L21 9 M3 15L21 15 M9 9L9 21 M15 9L15 21',   /* lucide: sheet */
  bildfoto:      'M4 3h16a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-10a2 2 0 0 1 2 -2z M8 21L16 21 M12 17L12 21',   /* lucide: monitor */
  smartart:      'M5 3h4a2 2 0 0 1 2 2v4a2 2 0 0 1 -2 2h-4a2 2 0 0 1 -2 -2v-4a2 2 0 0 1 2 -2z M7 11v4a2 2 0 0 0 2 2h4 M15 13h4a2 2 0 0 1 2 2v4a2 2 0 0 1 -2 2h-4a2 2 0 0 1 -2 -2v-4a2 2 0 0 1 2 -2z',   /* lucide: workflow */
  piktogramm:    'M7 8a5 5 0 1 0 10 0a5 5 0 1 0 -10 0 M20 21a8 8 0 0 0-16 0',   /* lucide: user-round */
  wordart:       'M12 4v16 M4 7V5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v2 M9 20h6',   /* lucide: type */
  textmarke:     'M17 3a2 2 0 0 1 2 2v15a1 1 0 0 1-1.496.868l-4.512-2.578a2 2 0 0 0-1.984 0l-4.512 2.578A1 1 0 0 1 5 20V5a2 2 0 0 1 2-2z',   /* lucide: bookmark */
  querverweis:   'M3 5v14 M21 12H7 M15 18 l6-6-6-6',   /* lucide: arrow-right-from-line */
  nadel:         'M12 17v5 M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z',   /* lucide: pin */
  baustein:      'M10 22V7a1 1 0 0 0-1-1H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5a1 1 0 0 0-1-1H2 M15 2h6a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-6a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1z',   /* lucide: blocks */
  initiale:      'M14 3v11 M14 9h-3a3 3 0 0 1 0-6h9 M18 3v11 M22 18H2l4-4 M6 22 l-4-4',   /* lucide: pilcrow-left */
  datum:         'M8 2v3 M16 2v3 M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M3 9h18',   /* lucide: calendar */
  uhrzeit:       'M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M12 6v6l4 2',   /* lucide: clock */
  ausdatei:      'M4 11V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.706.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1 M14 2v5a1 1 0 0 0 1 1h5 M2 15h10 M9 18 l3-3-3-3',   /* lucide: file-input */
  formel:        'M18 7V5a1 1 0 0 0-1-1H6.5a.5.5 0 0 0-.4.8l4.5 6a2 2 0 0 1 0 2.4l-4.5 6a.5.5 0 0 0 .4.8H17a1 1 0 0 0 1-1v-2',   /* lucide: sigma */
  spalten:       'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M12 3v18',   /* lucide: columns-2 */
  zeilennr:      'M11 5h10 M11 12h10 M11 19h10 M4 4h1v5 M4 9h2 M6.5 20H3.4c0-1 2.6-1.925 2.6-3.5a1.5 1.5 0 0 0-2.6-1.02',   /* lucide: list-ordered */
  trennung:      'M4 12h5 M11 12h2 M15 12h5 M6.5 7v10 M17.5 7v10',   /* von Hand */
  wasserzeichen: 'M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97',   /* lucide: droplets */
  thesaurus:     'M12 5v16 M16 13h2 M16 9h2 M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z M6 13h2 M6 9h2',   /* lucide: book-open-text */
  uebersetzen:   'M5 8 l6 6 M4 14 l6-6 2-3 M2 5h12 M7 2h1 M22 22 l-5-10-5 10 M14 18h6',   /* lucide: languages */
  kommentarweg:  'M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z M14.5 8.5 l-5 5 M9.5 8.5 l5 5',   /* lucide: message-square-x */
  kommentareweg: 'M16 10a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 14.286V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z M20 9a2 2 0 0 1 2 2v10.286a.71.71 0 0 1-1.212.502l-2.202-2.202A2 2 0 0 0 17.172 19H10a2 2 0 0 1-2-2v-1',   /* lucide: messages-square */
  markup:        'M14.364 13.634a2 2 0 0 0-.506.854l-.837 2.87a.5.5 0 0 0 .62.62l2.87-.837a2 2 0 0 0 .854-.506l4.013-4.009a1 1 0 0 0-3.004-3.004z M14.487 7.858A1 1 0 0 1 14 7V2 M20 19.645V20a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l2.516 2.516 M8 18h1',   /* lucide: file-pen-line */
  bereich:       'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M9 3v18',   /* lucide: panel-left */
  alleAn:        'M18 6 7 17l-5-5 M22 10 l-7.5 7.5L13 16',   /* lucide: check-check */
  alleAb:        'M16 5H3 M11 12H3 M16 19H3 M15.5 9.5 l5 5 M20.5 9.5 l-5 5',   /* lucide: list-x */
  wellen:        'M20 15 l-5.5 5.5L12 18 M4 16 l6-12 5.115 10.23 M6 12h8',   /* lucide: spell-check */
  autokorr:      'M21.64 3.64 l-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72 M14 7 l3 3 M5 6v4 M19 14v4 M10 2v2 M7 8H3 M21 16h-4 M11 3H9',   /* lucide: wand-sparkles */
  abhier:        'M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z',   /* lucide: play */
  halt:          'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z',   /* lucide: square */
  stimme:        'M2 10v3 M6 6v11 M10 3v18 M14 8v7 M18 5v13 M22 10v3',   /* lucide: audio-lines */
  optionen:      'M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915 M9 12a3 3 0 1 0 6 0a3 3 0 1 0 -6 0',   /* lucide: settings */
  adressblock:   'M16 2v2 M7 21v-2a2 2 0 012-2h6a2 2 0 012 2v2 M8 2v2 M9 10a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z',   /* lucide: contact */
  kaestchen:     'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M16 9 l-5.5 5.5L8 12',   /* lucide: square-check */
  formknopf:     'M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-8a2 2 0 0 1 2 -2z',   /* lucide: rectangle-horizontal */
  aufnahmeende:  'M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M10 9h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-4a1 1 0 0 1 1 -1z',   /* lucide: circle-stop */
  abspielen:     'M9 9.003a1 1 0 0 1 1.517-.859l4.997 2.997a1 1 0 0 1 0 1.718l-4.997 2.997A1 1 0 0 1 9 14.996z M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0',   /* lucide: circle-play */
  zweiblatt:     'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20',   /* lucide: book */
  fortlaufend:   'M15 12h-5 M15 8h-5 M19 17V5a2 2 0 0 0-2-2H4 M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3',   /* lucide: scroll-text */
  gliederung:    'M8 5h13 M13 12h8 M13 19h8 M3 10a2 2 0 0 0 2 2h3 M3 5v12a2 2 0 0 0 2 2h3',   /* lucide: list-tree */
  linealIcon:    'M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z M14.5 12.5 l2-2 M11.5 9.5 l2-2 M8.5 6.5 l2-2 M17.5 15.5 l2-2',   /* lucide: ruler */
  netz:          'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M3 9h18 M3 15h18 M9 3v18 M15 3v18',   /* lucide: grid-3x3 */
  navigation:    'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M9 3v18',   /* lucide: panel-left */
  steuerzeichen: 'M13 4v16 M17 4v16 M13 4H9.5a4 4 0 0 0 0 8H13 M3 20l3-4 3 4',   /* von Hand */
  ecken:         'M4 4h5 M4 4v5 M20 4h-5 M20 4v5 M4 20h5 M4 20v-5 M20 20h-5 M20 20v-5',   /* von Hand */
  seitenbreite:  'M18 8 l4 4-4 4 M2 12h20 M6 8 l-4 4 4 4',   /* lucide: move-horizontal */
  eineSeite:     'M12 2v20 M8 18 l4 4 4-4 M8 6 l4-4 4 4',   /* lucide: move-vertical */
  fensterNeben:  'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M12 3v18',   /* lucide: columns-2 */
  fensterUnter:  'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M3 12h18',   /* lucide: rows-2 */
  kacheln:       'M12 3v18 M3 12h18 M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z',   /* lucide: grid-2x2 */
  fensterliste:  'M3 5h.01 M3 12h.01 M3 19h.01 M8 5h13 M8 12h13 M8 19h13',   /* lucide: list */
  hell:          'M8 12a4 4 0 1 0 8 0a4 4 0 1 0 -8 0 M12 2v2 M12 20v2 M4.93 4.93 l1.41 1.41 M17.66 17.66 l1.41 1.41 M2 12h2 M20 12h2 M6.34 17.66 l-1.41 1.41 M19.07 4.93 l-1.41 1.41',   /* lucide: sun */
  dunkel:        'M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401',   /* lucide: moon */
  automatisch:   'M12 2v2 M14.837 16.385a6 6 0 1 1-7.223-7.222c.624-.147.97.66.715 1.248a4 4 0 0 0 5.26 5.259c.589-.255 1.396.09 1.248.715 M16 12a4 4 0 0 0-4-4 M19 5 l-1.256 1.256 M20 12h2',   /* lucide: sun-moon */
  menueleiste:   'M4 5h16 M4 12h16 M4 19h16',   /* lucide: menu */
  leisten:       'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M3 9h18',   /* lucide: panel-top */
  drucker2:      'M13.5 22H7a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v.5 M16 19 l2 2 4-4 M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v2 M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6',   /* lucide: printer-check */
  umbenennen:    'M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z M15 5 l4 4',   /* lucide: pencil */
  woerter:       'M2 16 l4.039-9.69a.5.5 0 0 1 .923 0L11 16 M22 9v7 M3.304 13h6.392 M15 12.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0 -7 0',   /* lucide: case-sensitive */
  beenden:       'M12 2v10 M18.4 6.6a9 9 0 1 1-12.77.04',   /* lucide: power */
  tasten:        'M10 8h.01 M12 12h.01 M14 8h.01 M16 12h.01 M18 8h.01 M6 8h.01 M7 16h10 M8 12h.01 M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2z',   /* lucide: keyboard */
  ueberprog:     'M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M12 16v-4 M12 8h.01',   /* lucide: info */
  zuletzt:       'M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M12 6v6l4 2',   /* lucide: clock-4 */
  unter:         'M10 2v3a1 1 0 0 0 1 1h5 M18 18v-6a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6 M18 22H4a2 2 0 0 1-2-2V6 M8 18a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9.172a2 2 0 0 1 1.414.586l2.828 2.828A2 2 0 0 1 22 6.828V16a2 2 0 0 1-2.01 2z',   /* lucide: save-all */
  handbuch:      'M12 5v16 M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z',   /* lucide: book-open */
  deckblatt:     'M13 22h5a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v3.3 M14 2v5a1 1 0 0 0 1 1h5 M7.69 16.479 l1.29 4.88a.5.5 0 0 1-.698.591l-1.843-.849a1 1 0 0 0-.879.001l-1.846.85a.5.5 0 0 1-.692-.593l1.29-4.88 M3 14a3 3 0 1 0 6 0a3 3 0 1 0 -6 0',   /* lucide: file-badge */
  textrahmen:    'M10 9.5 8 12l2 2.5 M14 21h1 M14 9.5 l2 2.5-2 2.5 M5 21a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2 M9 21h1',   /* lucide: square-dashed-bottom-code */
  einzug:        'M21 5H11 M21 12H11 M21 19H11 M3 8 l4 4-4 4',   /* lucide: list-indent-increase */
  anordnen:      'M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12 M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17',   /* lucide: layers */
  inhalt:        'M8 5h13 M13 12h8 M13 19h8 M3 10a2 2 0 0 0 2 2h3 M3 5v12a2 2 0 0 0 2 2h3',   /* lucide: list-tree */
  fussnote:      'M4 16v-2.38C4 11.5 2.97 10.5 3 8c.03-2.72 1.49-6 4.5-6C9.37 2 10 3.8 10 5.5c0 3.11-2 5.66-2 8.68V16a2 2 0 1 1-4 0Z M20 20v-2.38c0-2.12 1.03-3.12 1-5.62-.03-2.72-1.49-6-4.5-6C14.63 6 14 7.8 14 9.5c0 3.11 2 5.66 2 8.68V20a2 2 0 1 0 4 0Z M16 17h4 M4 13h4',   /* lucide: footprints */
  endnote:       'M10 2v8l3-3 3 3V2 M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20',   /* lucide: book-marked */
  zitat:         'M16 3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2 1 1 0 0 1 1 1v1a2 2 0 0 1-2 2 1 1 0 0 0-1 1v2a1 1 0 0 0 1 1 6 6 0 0 0 6-6V5a2 2 0 0 0-2-2z M5 3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2 1 1 0 0 1 1 1v1a2 2 0 0 1-2 2 1 1 0 0 0-1 1v2a1 1 0 0 0 1 1 6 6 0 0 0 6-6V5a2 2 0 0 0-2-2z',   /* lucide: quote */
  beschriftung:  'M16 5h6 M19 2v6 M21 11.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7.5 M21 15 l-3.086-3.086a2 2 0 0 0-2.828 0L6 21 M7 9a2 2 0 1 0 4 0a2 2 0 1 0 -4 0',   /* lucide: image-plus */
  eintrag:       'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20 M8 13 l4-7 4 7 M9.1 11h5.7',   /* lucide: book-a */
  gruendlich:    'M8 11 l2 2 4-4 M3 11a8 8 0 1 0 16 0a8 8 0 1 0 -16 0 M21 21 l-4.3-4.3',   /* lucide: search-check */
  sprache:       'M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20 M2 12h20',   /* lucide: globe */
  barrierefrei:  'M15 4a1 1 0 1 0 2 0a1 1 0 1 0 -2 0 M18 19 l1-7-6 1 M5 8 l3-3 5.5 3-2.36 3.5 M4.24 14.5a5 5 0 0 0 6.88 6 M13.76 17.5a5 5 0 0 0-6.88-6',   /* lucide: accessibility */
  annehmen:      'M20 6 9 17l-5-5',   /* lucide: check */
  ablehnen:      'M18 6 6 18 M6 6 l12 12',   /* lucide: x */
  sperren:       'M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-7a2 2 0 0 1 2 -2z M7 11V7a5 5 0 0 1 10 0v4',   /* lucide: lock */
  ki:            'M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z M20 2v4 M22 4h-4 M2 20a2 2 0 1 0 4 0a2 2 0 1 0 -4 0',   /* lucide: sparkles */
  vorschlag:     'M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5 M9 18h6 M10 22h4',   /* lucide: lightbulb */
  tafel:         'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M15 3v18',   /* lucide: panel-right */
  etiketten:     'M13.172 2a2 2 0 0 1 1.414.586l6.71 6.71a2.4 2.4 0 0 1 0 3.408l-4.592 4.592a2.4 2.4 0 0 1-3.408 0l-6.71-6.71A2 2 0 0 1 6 9.172V3a1 1 0 0 1 1-1z M2 7v6.172a2 2 0 0 0 .586 1.414l6.71 6.71a2.4 2.4 0 0 0 3.191.193 M10 6.5a0.5 0.5 0 1 0 1 0a0.5 0.5 0 1 0 -1 0',   /* lucide: tags */
  serie:         'M22 7 l-8.991 5.727a2 2 0 0 1-2.009 0L2 7 M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2z',   /* lucide: mail */
  seriefeld:     'M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1 M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1',   /* lucide: braces */
  formfeld:      'M12 20h-1a2 2 0 0 1-2-2 2 2 0 0 1-2 2H6 M13 8h7a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-7 M5 16H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h1 M6 4h1a2 2 0 0 1 2 2 2 2 0 0 1 2-2h1 M9 6v12',   /* lucide: text-cursor-input */
  aufnahme:      'M11 12a1 1 0 1 0 2 0a1 1 0 1 0 -2 0 M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0',   /* lucide: circle-dot */
  blattansicht:  'M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z M14 2v5a1 1 0 0 0 1 1h5 M10 9H8 M16 13H8 M16 17H8',   /* lucide: file-text */
  lesen:         'M12 5v16 M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z',   /* lucide: book-open */
  kleinerLupe:   'M3 11a8 8 0 1 0 16 0a8 8 0 1 0 -16 0 M21 21L16.65 16.65 M8 11L14 11',   /* lucide: zoom-out */
  neuesfenster:  'M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2z M10 4v4 M2 8h20 M6 4v4',   /* lucide: app-window */
  anpassen:      'M10 5H3 M12 19H3 M14 3v4 M16 17v4 M21 12h-9 M21 19h-5 M21 5h-7 M8 10v4 M8 12H3',   /* lucide: sliders-horizontal */
  raender:       'M3 7V5a2 2 0 0 1 2-2h2 M17 3h2a2 2 0 0 1 2 2v2 M21 17v2a2 2 0 0 1-2 2h-2 M7 21H5a2 2 0 0 1-2-2v-2',   /* lucide: scan */
  ausrichtung:   'M15.194 13.707 l3.814 1.86-1.86 3.814 M16.47214 7.52786 A 5 10 0 1 0 13 21.79796 M21.79796 11 A 10 5 0 1 0 19 15.57071',   /* lucide: rotate-3d */
  papiergroesse: 'M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z M14.5 12.5 l2-2 M11.5 9.5 l2-2 M8.5 6.5 l2-2 M17.5 15.5 l2-2',   /* lucide: ruler */
  speichern:     'M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7 M7 3v4a1 1 0 0 0 1 1h7',   /* lucide: save */
  drucken:       'M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2 M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6 M7 14h10a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-10a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1z',   /* lucide: printer */
  zurueck:       'M9 14 4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11',   /* lucide: undo-2 */
  vor:           'M15 14 l5-5-5-5 M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13',   /* lucide: redo-2 */
  links:         'M21 5H3 M15 12H3 M17 19H3',   /* lucide: text-align-start */
  mitte:         'M21 5H3 M17 12H7 M19 19H5',   /* lucide: text-align-center */
  rechts:        'M21 5H3 M21 12H9 M21 19H7',   /* lucide: text-align-end */
  block:         'M3 5h18 M3 12h18 M3 19h18',   /* lucide: text-align-justify */
  punkte:        'M3 5h.01 M3 12h.01 M3 19h.01 M8 5h13 M8 12h13 M8 19h13',   /* lucide: list */
  zahlen:        'M11 5h10 M11 12h10 M11 19h10 M4 4h1v5 M4 9h2 M6.5 20H3.4c0-1 2.6-1.925 2.6-3.5a1.5 1.5 0 0 0-2.6-1.02',   /* lucide: list-ordered */
  mehr:          'M21 5H11 M21 12H11 M21 19H11 M3 8 l4 4-4 4',   /* lucide: list-indent-increase */
  weniger:       'M21 5H11 M21 12H11 M21 19H11 M7 8 l-4 4 4 4',   /* lucide: list-indent-decrease */
  haken:         'M20 6 9 17l-5-5',   /* lucide: check */
  neu:           'M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z M14 2v5a1 1 0 0 0 1 1h5 M9 15h6 M12 18v-6',   /* lucide: file-plus */
  oeffnen:       'M6 14 l1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2',   /* lucide: folder-open */
  pdf:           'M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z M14 2v5a1 1 0 0 0 1 1h5 M10 9H8 M16 13H8 M16 17H8',   /* lucide: file-text */
  vorschau:      'M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0 M9 12a3 3 0 1 0 6 0a3 3 0 1 0 -6 0',   /* lucide: eye */
  schere:        'M3 6a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M8.12 8.12 12 12 M20 4 8.12 15.88 M3 18a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 M14.8 14.8 20 20',   /* lucide: scissors */
  kopie:         'M10 8h10a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2v-10a2 2 0 0 1 2 -2z M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2',   /* lucide: copy */
  kleben:        'M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-6a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1z M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2',   /* lucide: clipboard */
  pinsel:        'M14.622 17.897 l-10.68-2.913 M18.376 2.622a1 1 0 1 1 3.002 3.002L17.36 9.643a.5.5 0 0 0 0 .707l.944.944a2.41 2.41 0 0 1 0 3.408l-.944.944a.5.5 0 0 1-.707 0L8.354 7.348a.5.5 0 0 1 0-.707l.944-.944a2.41 2.41 0 0 1 3.408 0l.944.944a.5.5 0 0 0 .707 0z M9 8c-1.804 2.71-3.97 3.46-6.583 3.948a.507.507 0 0 0-.302.819l7.32 8.883a1 1 0 0 0 1.185.204C12.735 20.405 16 16.792 16 15',   /* lucide: paintbrush */
  tabelle:       'M12 3v18 M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M3 9h18 M3 15h18',   /* lucide: table */
  bild:          'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z M7 9a2 2 0 1 0 4 0a2 2 0 1 0 -4 0 M21 15 l-3.086-3.086a2 2 0 0 0-2.828 0L6 21',   /* lucide: image */
  rahmen:        'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2z',   /* lucide: square */
  umbruch:       'M16 16 l-4 4-4-4 M3 12h18 M8 8 l4-4 4 4',   /* lucide: separator-horizontal */
  kette:         'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71 M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',   /* lucide: link */
  kopfz:         'M3 4h18v5H3z M5 13h14 M5 17h10',   /* von Hand */
  fussz:         'M3 15h18v5H3z M5 7h14 M5 11h10',   /* von Hand */
  zahl:          'M3 4h18v11H3z M8 20h8 M12 17v3',   /* von Hand */
  notiz:         'M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z',   /* lucide: message-square */
  omega:         'M3 20h4.5a.5.5 0 0 0 .5-.5v-.282a.52.52 0 0 0-.247-.437 8 8 0 1 1 8.494-.001.52.52 0 0 0-.247.438v.282a.5.5 0 0 0 .5.5H21',   /* lucide: omega */
  hoch:          'M4 19 l8-8 M12 19 l-8-8 M20 12h-4c0-1.5.442-2 1.5-2.5S20 8.334 20 7.002c0-.472-.17-.93-.484-1.29a2.105 2.105 0 0 0-2.617-.436c-.42.239-.738.614-.899 1.06',   /* lucide: superscript */
  tief:          'M4 5 l8 8 M12 5 l-8 8 M20 19h-4c0-1.5.44-2 1.5-2.5S20 15.33 20 14c0-.47-.17-.93-.48-1.29a2.11 2.11 0 0 0-2.62-.44c-.42.24-.74.62-.9 1.07',   /* lucide: subscript */
  radierer:      'M21 21H8a2 2 0 0 1-1.42-.587l-3.994-3.999a2 2 0 0 1 0-2.828l10-10a2 2 0 0 1 2.829 0l5.999 6a2 2 0 0 1 0 2.828L12.834 21 M5.082 11.09 l8.828 8.828',   /* lucide: eraser */
  farbe:         'M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z M13 6.5a0.5 0.5 0 1 0 1 0a0.5 0.5 0 1 0 -1 0 M17 10.5a0.5 0.5 0 1 0 1 0a0.5 0.5 0 1 0 -1 0 M6 12.5a0.5 0.5 0 1 0 1 0a0.5 0.5 0 1 0 -1 0 M8 7.5a0.5 0.5 0 1 0 1 0a0.5 0.5 0 1 0 -1 0',   /* lucide: palette */
  marker:        'M9 11 l-6 6v3h9l3-3 M22 12 l-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4',   /* lucide: highlighter */
  abstand:       'M6 2h2a2 2 0 0 1 2 2v16a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2v-16a2 2 0 0 1 2 -2z M16 2h2a2 2 0 0 1 2 2v16a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2v-16a2 2 0 0 1 2 -2z',   /* lucide: stretch-vertical */
  lupe:          'M3 11a8 8 0 1 0 16 0a8 8 0 1 0 -16 0 M21 21L16.65 16.65 M11 8L11 14 M8 11L14 11',   /* lucide: zoom-in */
  saeule:        'M3 3v16a2 2 0 0 0 2 2h16 M18 17V9 M13 17V5 M8 17v-3',   /* lucide: chart-column */
  stift:         'M15.707 21.293a1 1 0 0 1-1.414 0l-1.586-1.586a1 1 0 0 1 0-1.414l5.586-5.586a1 1 0 0 1 1.414 0l1.586 1.586a1 1 0 0 1 0 1.414z M18 13 l-1.375-6.874a1 1 0 0 0-.746-.776L3.235 2.028a1 1 0 0 0-1.207 1.207L5.35 15.879a1 1 0 0 0 .776.746L13 18 M2.3 2.3 l7.286 7.286 M9 11a2 2 0 1 0 4 0a2 2 0 1 0 -4 0',   /* lucide: pen-tool */
  verfolgt:      'M16 22h2a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v2.85 M14 2v5a1 1 0 0 0 1 1h5 M8 14v2.2l1.6 1 M2 16a6 6 0 1 0 12 0a6 6 0 1 0 -12 0',   /* lucide: file-clock */
};
