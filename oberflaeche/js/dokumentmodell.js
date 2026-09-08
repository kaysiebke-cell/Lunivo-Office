/* ============================================================
   Das Dokumentmodell

   Übersetzt aus WPS Office/document_model.cpp — derselbe Aufbau, dieselben
   Namen. Wer beide nebeneinanderlegt, findet jede Klasse wieder.

   WOZU ES DA IST

   Bisher ist ein Dokument in diesem Programm ein einziges Feld voller
   HTML. Das trägt einen Brief, aber es kennt keine Abschnitte: Ein
   Deckblatt ohne Seitenzahl, gefolgt von einem Hauptteil mit Zahlen ab 1,
   gefolgt von einem Anhang quer — das sind drei Abschnitte mit je eigenem
   Seitenaufbau, eigener Kopf- und Fußzeile, eigener Nummerierung. Ohne
   Modell dafür gibt es keinen Ort, an dem das stehen könnte.

   DIE RÜCKRUFE SIND DER KERN

   Nicht die Klassen sind das Besondere, sondern die Kette dazwischen:

       Paragraph.addText()
            │
            ▼
       DocumentContent.notifyChanged()
            │
            ▼
       Section-Inhalt meldet sich
            │
            ▼
       Document.rebuildLanguageDocument()
            │
            ▼
       Sprachbrücke.textSetzen()

   Ändert irgendwo im Dokument ein Absatz seinen Text, weiß die
   Sprachprüfung davon — ohne dass jemand daran denken muss. Genau das
   steht im Prüfkatalog unter „Callbacks triggern Language Bridge Update".
   ============================================================ */
'use strict';

const Dokumentmodell = (() => {

/* ---- Aufzählungen ---- */

const Orientation = Object.freeze({ Portrait: 'Portrait', Landscape: 'Landscape' });

const SectionBreakType = Object.freeze({
  NextPage: 'NextPage', Continuous: 'Continuous',
  EvenPage: 'EvenPage', OddPage: 'OddPage',
});

const PageNumberFormat = Object.freeze({
  Arabic: 'Arabic', RomanLower: 'RomanLower', RomanUpper: 'RomanUpper',
  LetterLower: 'LetterLower', LetterUpper: 'LetterUpper',
});

const Alignment = Object.freeze({
  Left: 'Left', Center: 'Center', Right: 'Right',
  Justify: 'Justify', Distributed: 'Distributed',
});

const TextWrapping = Object.freeze({
  None: 'None', Square: 'Square', Tight: 'Tight', Through: 'Through',
  TopAndBottom: 'TopAndBottom', BehindText: 'BehindText', InFrontOfText: 'InFrontOfText',
});

const ShapeType = Object.freeze({
  Rectangle: 'Rectangle', Ellipse: 'Ellipse', Line: 'Line', Arrow: 'Arrow',
});

/* ---- Einfache Werte ----

   In C++ sind das structs mit Vorgabewerten. Hier reichen Funktionen, die
   ein frisches Objekt bauen: Ein gemeinsames Vorgabe-Objekt wäre geteilt,
   und der zweite Abschnitt bekäme die Ränder des ersten mit. */

const Position = (x = 0, y = 0) => ({ x, y });
const Color = (r = 0, g = 0, b = 0) => ({ r, g, b });
const Font = (name = 'Arial') => ({ name });
const ImageSource = (path = '') => ({ path });

const DocumentMetadata = () => ({ title: '', author: '', subject: '' });

/* Maße in Millimetern, wie in der Vorlage. */
const Margins  = () => ({ top: 20, bottom: 20, left: 20, right: 20 });
const PageSize = () => ({ width: 210, height: 297, type: { name: 'A4' } });
const Columns  = () => ({ count: 1, spacing: 5, equalWidth: true });

const PageSetup = () => ({
  margins: Margins(),
  orientation: Orientation.Portrait,
  pageSize: PageSize(),
  columns: Columns(),
});

const SectionBreak = (type = SectionBreakType.NextPage) => ({ type });

const PageNumbering = () => ({
  enabled: true,
  startAt: 1,
  format: PageNumberFormat.Arabic,
  differentFirstPage: false,
  differentOddEven: false,
});

const ParagraphProperties = () => ({
  alignment: Alignment.Left,
  lineSpacing: 1.0,
  beforeSpacing: 0, afterSpacing: 0,
  leftIndent: 0, rightIndent: 0, firstLineIndent: 0,
});

/* ---- TextRun ----

   Ein Stück Text mit einer Auszeichnung. Ein Absatz besteht aus mehreren:
   „Sehr geehrte " (normal) + „Damen und Herren" (fett) sind zwei Läufe in
   einem Absatz. */
class TextRun {
  constructor(text = '') {
    this.text = text;
    this.font = Font();
    this.fontSize = 11;
    this.bold = false;
    this.italic = false;
    this.underline = false;
    this.color = Color();
  }
}

/* ---- Block ----

   Die gemeinsame Wurzel von allem, was in einem Dokument untereinander
   steht. In C++ ist sie abstrakt; hier verhindert der Aufruf im
   Baukasten, dass jemand sie selbst benutzt. */
class Block {
  constructor(id) {
    if (new.target === Block) {
      throw new TypeError('Block ist die Wurzel, kein eigener Baustein.');
    }
    this.id = id;
    this.position = Position();
    this.onChange = null;
  }

  getId() { return this.id; }
  getPosition() { return this.position; }

  setChangeCallback(rueckruf) { this.onChange = rueckruf || null; }

  melde() { if (this.onChange) this.onChange(); }

  typeName() { throw new Error('typeName fehlt'); }

  /* Was dieser Baustein an Text beisteuert. Die Sprachprüfung liest
     nichts anderes. */
  getPlainText() { return ''; }
}

class Paragraph extends Block {
  constructor(id) {
    super(id);
    this.runs = [];
    this.properties = ParagraphProperties();
  }

  addText(text) {
    this.runs.push(new TextRun(text));
    this.melde();
    return this;
  }

  setText(text) {
    this.runs = text ? [new TextRun(text)] : [];
    this.melde();
    return this;
  }

  getText() { return this.runs.map((r) => r.text).join(''); }
  getPlainText() { return this.getText(); }
  typeName() { return 'Paragraph'; }
}

class Cell {
  constructor() {
    this.content = new DocumentContent();
  }
}

class Row {
  constructor() {
    this.cells = [];
    this.onChange = null;
  }

  /* Der Rückruf wandert bis in die Zellen hinunter: Ein Wort, das in
     einer Tabellenzelle geändert wird, ist eine Änderung am Dokument wie
     jede andere. */
  setChangeCallback(rueckruf) {
    this.onChange = rueckruf || null;
    for (const zelle of this.cells) {
      if (zelle && zelle.content) zelle.content.setChangeCallback(this.onChange);
    }
  }

  addCell() {
    const zelle = new Cell();
    zelle.content.setChangeCallback(this.onChange);
    this.cells.push(zelle);
    if (this.onChange) this.onChange();
    return zelle;
  }
}

const TableProperties = () => ({ borders: true });

class Table extends Block {
  constructor(id) {
    super(id);
    this.rows = [];
    this.properties = TableProperties();
  }

  setChangeCallback(rueckruf) {
    super.setChangeCallback(rueckruf);
    for (const zeile of this.rows) zeile.setChangeCallback(this.onChange);
  }

  addRow() {
    const zeile = new Row();
    zeile.setChangeCallback(this.onChange);
    this.rows.push(zeile);
    this.melde();
    return zeile;
  }

  getPlainText() {
    const stuecke = [];
    for (const zeile of this.rows) {
      for (const zelle of zeile.cells) stuecke.push(zelle.content.getPlainText());
    }
    return stuecke.filter(Boolean).join('\n');
  }

  typeName() { return 'Table'; }
}

class Image extends Block {
  constructor(id, pfad = '') {
    super(id);
    this.source = ImageSource(pfad);
    this.width = 0;
    this.height = 0;
    this.wrapping = TextWrapping.Square;
    this.alt = '';
  }
  /* Der Alternativtext zählt als Text: Er wird gelesen — von der
     Vorlesestimme und von jedem, der das Bild nicht sieht. */
  getPlainText() { return this.alt || ''; }
  typeName() { return 'Image'; }
}

class Shape extends Block {
  constructor(id, art = ShapeType.Rectangle) {
    super(id);
    this.shapeType = art;
    this.width = 0;
    this.height = 0;
    this.wrapping = TextWrapping.Square;
  }
  typeName() { return 'Shape'; }
}

class PageBreak extends Block {
  typeName() { return 'PageBreak'; }
}

/* ---- DocumentContent ----

   Eine Folge von Blöcken und die Stelle, an der Änderungen zusammenlaufen.
   Jeder Block, der hier hineinkommt, bekommt seinen Rückruf verdrahtet —
   deshalb muss niemand beim Einfügen daran denken. */
class DocumentContent {
  constructor() {
    this.blocks = [];
    this.nextBlockId = 1;
    this.onChange = null;
  }

  notifyChanged() { if (this.onChange) this.onChange(); }

  bindBlock(block) {
    if (block instanceof Paragraph || block instanceof Table) {
      block.setChangeCallback(() => this.notifyChanged());
    }
  }

  setChangeCallback(rueckruf) {
    this.onChange = rueckruf || null;
    for (const block of this.blocks) this.bindBlock(block);
  }

  _aufnehmen(block) {
    this.bindBlock(block);
    this.blocks.push(block);
    this.notifyChanged();
    return block;
  }

  addParagraph(text = '') {
    const absatz = new Paragraph(this.nextBlockId++);
    if (text) absatz.runs.push(new TextRun(text));
    return this._aufnehmen(absatz);
  }

  addTable()          { return this._aufnehmen(new Table(this.nextBlockId++)); }
  addImage(pfad = '') { return this._aufnehmen(new Image(this.nextBlockId++, pfad)); }
  addShape(art)       { return this._aufnehmen(new Shape(this.nextBlockId++, art)); }
  addPageBreak()      { return this._aufnehmen(new PageBreak(this.nextBlockId++)); }

  getBlocks() { return this.blocks.slice(); }
  getBlock(i) { return this.blocks[i] || null; }

  removeBlock(block) {
    const stelle = this.blocks.indexOf(block);
    if (stelle < 0) return false;
    this.blocks.splice(stelle, 1);
    this.notifyChanged();
    return true;
  }

  /* Absatzweise mit Zeilenumbruch dazwischen: Ohne ihn liefe das letzte
     Wort des einen Absatzes ins erste des nächsten, und die Prüfung
     fände einen Fehler, den niemand geschrieben hat. */
  getPlainText() {
    return this.blocks.map((b) => b.getPlainText()).filter(Boolean).join('\n');
  }
}

/* ---- Kopf- und Fußzeile ----

   „linkedToPrevious" ist der Schalter, den Word „Wie vorherige" nennt:
   Der Abschnitt führt dann keine eigene Kopfzeile, sondern zeigt die des
   Abschnitts davor. */
class Header {
  constructor() {
    this.enabled = true;
    this.linkedToPrevious = false;
    this.content = new DocumentContent();
  }
}

class Footer {
  constructor() {
    this.enabled = true;
    this.linkedToPrevious = false;
    this.content = new DocumentContent();
  }
}

class CoverPage {
  constructor(vorlage = 'Standard') {
    this.template = { name: vorlage };
    this.content = new DocumentContent();
  }
}

class TOCEntry {
  constructor(text, ebene, seite) {
    this.text = text; this.level = ebene; this.page = seite;
  }
}

class TableOfContents {
  constructor() { this.entries = []; this.maxLevel = 3; }

  /* Aus den Überschriften des Dokuments. Die Seitenzahl bleibt offen —
     die weiß erst der Umbruch, nicht das Modell. */
  rebuild(document) {
    this.entries = [];
    for (const abschnitt of document.getSections()) {
      for (const block of abschnitt.getContent().getBlocks()) {
        if (!(block instanceof Paragraph)) continue;
        const ebene = block.properties.outlineLevel || 0;
        if (ebene > 0 && ebene <= this.maxLevel) {
          this.entries.push(new TOCEntry(block.getText(), ebene, null));
        }
      }
    }
    return this.entries;
  }
}

/* ---- Section ----

   Ein Abschnitt ist das, was einen eigenen Seitenaufbau hat: eigene
   Ränder, eigene Ausrichtung, eigene Kopf- und Fußzeile, eigene
   Seitennummerierung. */
class Section {
  constructor(id) {
    this.id = id;
    this.content = new DocumentContent();
    this.pageSetup = PageSetup();
    this.header = new Header();
    this.footer = new Footer();
    this.pageNumbering = PageNumbering();
    this.breakBefore = null;
    this.document = null;
  }

  getId()            { return this.id; }
  getContent()       { return this.content; }
  getPageSetup()     { return this.pageSetup; }
  getHeader()        { return this.header; }
  getFooter()        { return this.footer; }
  getPageNumbering() { return this.pageNumbering; }

  insertBreak(art)   { this.breakBefore = SectionBreak(art); }
  deleteBreak()      { this.breakBefore = null; }
  getBreakBefore()   { return this.breakBefore; }

  setDocument(doc)   { this.document = doc; }

  /* Nachbarn kommen aus der Liste des Dokuments, nicht aus Zeigern am
     Abschnitt selbst. Zwei Zeiger, die gepflegt werden müssen, laufen
     irgendwann auseinander — der Index kann das nicht. */
  previous() {
    if (!this.document) return null;
    const alle = this.document.getSections();
    const i = alle.indexOf(this);
    return i > 0 ? alle[i - 1] : null;
  }

  next() {
    if (!this.document) return null;
    const alle = this.document.getSections();
    const i = alle.indexOf(this);
    return i >= 0 && i < alle.length - 1 ? alle[i + 1] : null;
  }

  /* Die Kopfzeile, die für diesen Abschnitt gilt — mit „Wie vorherige"
     kann das die eines früheren sein. */
  wirksameKopfzeile() {
    let hier = this;
    while (hier && hier.header.linkedToPrevious) hier = hier.previous();
    return hier ? hier.header : this.header;
  }

  wirksameFusszeile() {
    let hier = this;
    while (hier && hier.footer.linkedToPrevious) hier = hier.previous();
    return hier ? hier.footer : this.footer;
  }
}

/* ---- Document ---- */
class Document {
  constructor(bruecke = null) {
    this.metadata = DocumentMetadata();
    this.sections = [];
    this.coverPage = null;
    this.tableOfContents = null;
    this.nextSectionId = 1;
    this.currentSectionIndex = 0;
    /* Die Sprachbrücke wird hereingereicht, nicht hier gebaut: Es gibt
       genau eine im Programm, und ein zweites Exemplar hieße ein zweiter
       Fehlerstand. */
    this.languageBridge = bruecke;
    this.addSection();
  }

  getLanguageBridge() { return this.languageBridge; }
  setLanguageBridge(bruecke) {
    this.languageBridge = bruecke;
    this.rebuildLanguageDocument();
  }

  getMetadata() { return this.metadata; }

  /* Der ganze Text des Dokuments, in der Reihenfolge, in der er dasteht:
     Deckblatt, dann je Abschnitt Kopfzeile, Inhalt, Fußzeile. */
  getPlainText() {
    const stuecke = [];
    if (this.coverPage) stuecke.push(this.coverPage.content.getPlainText());
    for (const abschnitt of this.sections) {
      stuecke.push(abschnitt.getHeader().content.getPlainText());
      stuecke.push(abschnitt.getContent().getPlainText());
      stuecke.push(abschnitt.getFooter().content.getPlainText());
    }
    return stuecke.filter(Boolean).join('\n');
  }

  rebuildLanguageDocument() {
    if (!this.languageBridge) return;
    this.languageBridge.textSetzen(this.getPlainText());
  }

  /* Jeder Ort, an dem Text stehen kann, meldet seine Änderung hierher. */
  connectLanguageBridge(abschnitt) {
    const melden = () => this.rebuildLanguageDocument();
    abschnitt.getContent().setChangeCallback(melden);
    abschnitt.getHeader().content.setChangeCallback(melden);
    abschnitt.getFooter().content.setChangeCallback(melden);
  }

  addSection() {
    const abschnitt = new Section(this.nextSectionId++);
    abschnitt.setDocument(this);
    this.sections.push(abschnitt);
    this.currentSectionIndex = this.sections.length - 1;
    this.connectLanguageBridge(abschnitt);
    this.rebuildLanguageDocument();
    return abschnitt;
  }

  /* Der letzte Abschnitt bleibt stehen. Ein Dokument ohne Abschnitt hätte
     keinen Ort für Text und keinen Seitenaufbau. */
  removeSection(abschnitt) {
    if (this.sections.length <= 1) return false;
    const stelle = this.sections.indexOf(abschnitt);
    if (stelle < 0) return false;
    this.sections.splice(stelle, 1);
    if (this.currentSectionIndex >= this.sections.length) {
      this.currentSectionIndex = this.sections.length - 1;
    } else if (stelle < this.currentSectionIndex) {
      this.currentSectionIndex--;
    }
    this.rebuildLanguageDocument();
    return true;
  }

  getSections()       { return this.sections; }
  getSection(i)       { return this.sections[i] || null; }
  getCurrentSection() { return this.getSection(this.currentSectionIndex); }

  setCurrentSection(i) {
    if (i < 0 || i >= this.sections.length) return false;
    this.currentSectionIndex = i;
    return true;
  }

  setCoverPage(vorlage) {
    this.coverPage = new CoverPage(vorlage);
    this.coverPage.content.setChangeCallback(() => this.rebuildLanguageDocument());
    this.rebuildLanguageDocument();
    return this.coverPage;
  }

  removeCoverPage() {
    if (!this.coverPage) return false;
    this.coverPage = null;
    this.rebuildLanguageDocument();
    return true;
  }

  setTableOfContents() {
    this.tableOfContents = new TableOfContents();
    this.tableOfContents.rebuild(this);
    return this.tableOfContents;
  }
}

return {
  Orientation, SectionBreakType, PageNumberFormat, Alignment, TextWrapping, ShapeType,
  Position, Color, Font, ImageSource, DocumentMetadata,
  Margins, PageSize, Columns, PageSetup, SectionBreak, PageNumbering,
  ParagraphProperties, TextRun,
  Block, Paragraph, Table, Row, Cell, TableProperties, Image, Shape, PageBreak,
  DocumentContent, Header, Footer, CoverPage, TOCEntry, TableOfContents,
  Section, Document,
};
})();

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Dokumentmodell };
}
