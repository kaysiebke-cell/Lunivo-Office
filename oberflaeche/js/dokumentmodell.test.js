/* ============================================================
   Prüfläufe für das Dokumentmodell.

   node oberflaeche/js/dokumentmodell.test.js

   Geprüft wird vor allem die Rückrufkette: Ein Absatz ändert seinen Text,
   und die Sprachbrücke weiß davon — ohne dass jemand dazwischen daran
   denken muss. Das ist der Punkt des ganzen Modells.
   ============================================================ */
'use strict';

const { pruefhelferBauen } = require('./pruefhelfer.js');
const { stimmt, gleich, schluss } = pruefhelferBauen();

const { Dokumentmodell: M } = require('./dokumentmodell.js');

/* Eine gestellte Sprachbrücke: Sie merkt sich nur, was ihr gesagt wird. */
const brueckeBauen = () => ({ text: null, rufe: 0,
  textSetzen(t) { this.text = t; this.rufe++; } });

console.log('\nDokumentmodell\n');

console.log('Der Anfang');
{
  const d = new M.Document();
  gleich(d.getSections().length, 1, 'ein Dokument hat von Anfang an einen Abschnitt');
  stimmt(d.getCurrentSection() === d.getSection(0), 'und der ist der aktuelle');
  gleich(d.getSection(0).getId(), 1, 'Abschnitte werden ab 1 gezählt');
  gleich(d.getMetadata().title, '', 'ohne Titel');
}

console.log('\nAbschnitte');
{
  const d = new M.Document();
  const zwei = d.addSection();
  const drei = d.addSection();
  gleich(d.getSections().length, 3, 'zwei dazu macht drei');
  stimmt(zwei.previous() === d.getSection(0), 'der zweite kennt den ersten');
  stimmt(zwei.next() === drei, 'und den dritten');
  stimmt(d.getSection(0).previous() === null, 'vor dem ersten kommt nichts');
  stimmt(drei.next() === null, 'nach dem letzten auch nicht');

  stimmt(d.removeSection(zwei), 'ein Abschnitt lässt sich entfernen');
  gleich(d.getSections().length, 2, 'dann sind es zwei');
  stimmt(d.getSection(0).next() === drei, 'und die Nachbarschaft stimmt wieder');
}
{
  const d = new M.Document();
  stimmt(!d.removeSection(d.getSection(0)), 'der letzte Abschnitt bleibt stehen');
}

console.log('\nJeder Abschnitt hat seinen eigenen Seitenaufbau');
{
  const d = new M.Document();
  const a = d.getSection(0), b = d.addSection();
  a.getPageSetup().margins.left = 50;
  b.getPageSetup().orientation = M.Orientation.Landscape;
  gleich(b.getPageSetup().margins.left, 20, 'der Rand des einen färbt nicht auf den anderen ab');
  gleich(a.getPageSetup().orientation, M.Orientation.Portrait, 'die Ausrichtung ebenso wenig');

  a.getPageNumbering().startAt = 1;
  b.getPageNumbering().enabled = false;
  stimmt(a.getPageNumbering().enabled, 'und die Seitenzahlen gelten je Abschnitt');
}

console.log('\nAbschnittsumbruch');
{
  const d = new M.Document();
  const a = d.getSection(0);
  gleich(a.getBreakBefore(), null, 'zunächst keiner');
  a.insertBreak(M.SectionBreakType.EvenPage);
  gleich(a.getBreakBefore().type, 'EvenPage', 'einer lässt sich setzen');
  a.deleteBreak();
  gleich(a.getBreakBefore(), null, 'und wieder wegnehmen');
}

console.log('\nBlöcke');
{
  const inhalt = new M.DocumentContent();
  const p = inhalt.addParagraph('Hallo');
  const t = inhalt.addTable();
  const b = inhalt.addImage('/bild.png');
  gleich(inhalt.getBlocks().length, 3, 'drei Bausteine');
  gleich(p.typeName(), 'Paragraph', 'ein Absatz');
  gleich(t.typeName(), 'Table', 'eine Tabelle');
  gleich(b.typeName(), 'Image', 'ein Bild');
  stimmt(p.getId() !== t.getId(), 'jeder hat seine eigene Nummer');
  gleich(p.getText(), 'Hallo', 'der Absatz trägt seinen Text');

  let werfen = false;
  try { new M.Block(1); } catch (e) { werfen = true; }
  stimmt(werfen, 'die Wurzel selbst lässt sich nicht bauen');
}

console.log('\nAbsatz aus mehreren Läufen');
{
  const p = new M.Paragraph(1);
  p.addText('Sehr geehrte ');
  p.addText('Damen und Herren');
  gleich(p.runs.length, 2, 'zwei Läufe');
  gleich(p.getText(), 'Sehr geehrte Damen und Herren', 'zusammen ergeben sie den Satz');
  p.runs[1].bold = true;
  gleich(p.getText(), 'Sehr geehrte Damen und Herren', 'die Auszeichnung ändert den Text nicht');
}

console.log('\nTabelle');
{
  const inhalt = new M.DocumentContent();
  const t = inhalt.addTable();
  const z1 = t.addRow(); z1.addCell(); z1.addCell();
  const z2 = t.addRow(); z2.addCell(); z2.addCell();
  gleich(t.rows.length, 2, 'zwei Zeilen');
  gleich(t.rows[0].cells.length, 2, 'je zwei Zellen');
  z1.cells[0].content.addParagraph('links');
  z1.cells[1].content.addParagraph('rechts');
  stimmt(t.getPlainText().includes('links') && t.getPlainText().includes('rechts'),
         'der Text der Zellen zählt zum Text der Tabelle');
}

console.log('\nDie Rückrufkette — darum geht es');
{
  const br = brueckeBauen();
  const d = new M.Document(br);
  const rufeVorher = br.rufe;

  const p = d.getCurrentSection().getContent().addParagraph('Erster Satz.');
  stimmt(br.rufe > rufeVorher, 'ein neuer Absatz meldet sich bei der Brücke');
  stimmt(br.text.includes('Erster Satz.'), 'und ihr Text enthält ihn');

  p.addText(' Zweiter Satz.');
  stimmt(br.text.includes('Zweiter Satz.'), 'ein geänderter Absatz ebenso');

  d.getCurrentSection().getHeader().content.addParagraph('Briefkopf');
  stimmt(br.text.includes('Briefkopf'), 'die Kopfzeile zählt mit');

  d.getCurrentSection().getFooter().content.addParagraph('Seite');
  stimmt(br.text.includes('Seite'), 'die Fußzeile auch');
}

console.log('\nDie Kette reicht bis in die Tabellenzelle');
{
  const br = brueckeBauen();
  const d = new M.Document(br);
  const t = d.getCurrentSection().getContent().addTable();
  const zeile = t.addRow();
  const zelle = zeile.addCell();
  zelle.content.addParagraph('in der Zelle');
  stimmt(br.text.includes('in der Zelle'), 'auch ein Wort in einer Zelle erreicht die Brücke');
}

console.log('\nEin neuer Abschnitt ist gleich angeschlossen');
{
  const br = brueckeBauen();
  const d = new M.Document(br);
  const zwei = d.addSection();
  zwei.getContent().addParagraph('Im zweiten Abschnitt');
  stimmt(br.text.includes('Im zweiten Abschnitt'), 'ohne dass jemand ihn verdrahten muss');
}

console.log('\nDeckblatt und Reihenfolge des Textes');
{
  const br = brueckeBauen();
  const d = new M.Document(br);
  d.getCurrentSection().getContent().addParagraph('Hauptteil');
  const deck = d.setCoverPage('Schlicht');
  deck.content.addParagraph('Titelblatt');
  stimmt(br.text.indexOf('Titelblatt') < br.text.indexOf('Hauptteil'),
         'das Deckblatt steht vor dem Hauptteil');
  stimmt(d.removeCoverPage(), 'es lässt sich wieder entfernen');
  stimmt(!br.text.includes('Titelblatt'), 'dann ist es aus dem Text heraus');
}

console.log('\nWie vorherige');
{
  const d = new M.Document();
  const a = d.getSection(0), b = d.addSection();
  a.getHeader().content.addParagraph('Kopf des ersten');
  b.getHeader().linkedToPrevious = true;
  stimmt(b.wirksameKopfzeile() === a.getHeader(), 'der zweite zeigt die Kopfzeile des ersten');
  b.getHeader().linkedToPrevious = false;
  stimmt(b.wirksameKopfzeile() === b.getHeader(), 'abgeschaltet hat er wieder seine eigene');
}

console.log('\nAbsätze werden nicht aneinandergeklebt');
{
  const inhalt = new M.DocumentContent();
  inhalt.addParagraph('Ende');
  inhalt.addParagraph('Anfang');
  stimmt(inhalt.getPlainText().includes('Ende\nAnfang'),
         'zwischen zwei Absätzen steht ein Umbruch');
}

console.log('\nOhne Brücke läuft es auch');
{
  const d = new M.Document();
  d.getCurrentSection().getContent().addParagraph('Text');
  stimmt(d.getPlainText().includes('Text'), 'das Modell hängt nicht an ihr');
  const br = brueckeBauen();
  d.setLanguageBridge(br);
  stimmt(br.text.includes('Text'), 'wird sie nachgereicht, bekommt sie den Stand');
}

console.log('\nDie Griffe, die das C++-Beispiel benutzt');
{
  /* main() in document_model.cpp ruft diese Namen — der Port muss sie
     kennen, sonst laesst sich das Beispiel nicht nachbauen. */
  const d = new M.Document();
  const noetig = ['addSection','getSection','getCurrentSection','sectionCount',
                  'getMetadata','getLanguageBridge','getDocumentVersion',
                  'createCoverPage','createTableOfContents','removeSection'];
  for (const n of noetig) stimmt(typeof d[n] === 'function', 'Document.' + n + '()');

  const a = d.getCurrentSection();
  for (const n of ['getContent','getPageSetup','getHeader','getFooter',
                   'getPageNumbering','getId','insertBreak','previous','next']) {
    stimmt(typeof a[n] === 'function', 'Section.' + n + '()');
  }
  const inhalt = a.getContent();
  for (const n of ['addParagraph','addTable','addImage','addShape']) {
    stimmt(typeof inhalt[n] === 'function', 'DocumentContent.' + n + '()');
  }
  gleich(d.sectionCount(), 1, 'sectionCount zaehlt die Abschnitte');
}
{
  const d = new M.Document();
  const inhalt = d.getCurrentSection().getContent();
  const bild = inhalt.addImage('/bild.png');
  const form = inhalt.addShape(M.ShapeType.Rectangle);
  bild.getPosition().x = 20; bild.getPosition().y = 30;
  form.getPosition().x = 50; form.getPosition().y = 80;
  gleich(bild.getPosition().x, 20, 'Bild und Form tragen eine Position');
  gleich(form.getPosition().y, 80, 'jede ihre eigene');
}
{
  const v = new M.TableOfContents();
  gleich(v.title, 'Inhaltsverzeichnis', 'das Verzeichnis hat einen Titel');
  gleich(v.depth, 3, 'und eine Tiefe');
  const e = v.addEntry('Kapitel eins', 7, 1);
  gleich(e.pageNumber, 7, 'ein Eintrag traegt seine Seitenzahl');
  gleich(e.level, 1, 'und seine Ebene');
}

schluss();
