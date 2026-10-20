import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from lunivo_writer.editor import einfuegen as E
from lunivo_writer.editor import formen
from lunivo_writer.models.page import PageSettings
from lunivo_writer.services import file_service as formats
from lunivo_writer.ui.document.document_editor import DocumentEditor


def _form(ed, name="Rechteck", **d):
    daten = {"form": name}; daten.update(d)
    E.qimage_einfuegen(ed, E.form_bild(name), "Form", "form", daten)


def _vor_bild(ed, nr=0):
    c = QTextCursor(ed.document()); c.setPosition(nr); ed.setTextCursor(c)


def test_fuellung_kontur_vorlage(app):
    ed = DocumentEditor()
    _form(ed)
    _vor_bild(ed)
    assert formen.aendern(ed, fuell="#ff0000")
    assert formen.aendern(ed, linie="#00ff00", strich=5.0)
    o = formen.objekt(ed.bild_format())
    assert o["daten"]["fuell"] == "#ff0000" and o["daten"]["linie"] == "#00ff00" and o["daten"]["strich"] == 5.0
    assert formen.vorlage(ed, "Nur Kontur")
    assert formen.objekt(ed.bild_format())["daten"]["fuell"] == ""
    img = ed.document().resource(2, __import__("PySide6.QtCore", fromlist=["QUrl"]).QUrl(ed.bild_format().name()))
    assert img.pixelColor(img.width() // 2, img.height() // 2).alpha() == 0     # ohne Füllung transparent


def test_gruppieren_aufheben_docx(app, tmp_path):
    ed = DocumentEditor()
    _form(ed, "Rechteck"); _form(ed, "Ellipse", fuell="#ff0000")
    c = QTextCursor(ed.document()); c.select(QTextCursor.Document); ed.setTextCursor(c)
    assert formen.gruppieren(ed) == ""
    _vor_bild(ed)
    o = formen.objekt(ed.bild_format())
    assert o["art"] == "gruppe" and len(o["daten"]["kinder"]) == 2
    pfad = str(tmp_path / "g.docx")
    formats.save(pfad, ed.document(), PageSettings())
    neu = DocumentEditor(); neu.setDocument(formats.load(pfad).doc)
    _vor_bild(neu)
    assert formen.objekt(neu.bild_format())["art"] == "gruppe"
    assert formen.gruppe_aufheben(neu) == ""
    _vor_bild(neu)
    assert formen.objekt(neu.bild_format())["daten"]["form"] == "Rechteck"
    assert neu.document().toPlainText().count("￼") == 2


def test_gruppieren_braucht_zwei(app):
    ed = DocumentEditor()
    _form(ed)
    c = QTextCursor(ed.document()); c.select(QTextCursor.Document); ed.setTextCursor(c)
    assert formen.gruppieren(ed)


def test_tabellenvorlage_docx(app, tmp_path):
    from PySide6.QtGui import QTextCharFormat, QTextTableFormat
    from lunivo_writer.editor import tabellenstil as TS
    ed = DocumentEditor()
    t = ed.textCursor().insertTable(3, 2, QTextTableFormat())
    assert TS.anwenden(t, "Blau", kopf=True, streifen=True, spalte=False)
    assert t.cellAt(0, 0).format().background().color().name() == "#2f6fb5"
    assert t.cellAt(2, 0).format().background().color().name() == "#e7f0fa"
    assert t.cellAt(1, 0).format().background().style() == Qt.NoBrush
    cf = t.cellAt(2, 1).format().toTableCellFormat()
    cf.setVerticalAlignment(QTextCharFormat.AlignMiddle); t.cellAt(2, 1).setFormat(cf)
    pfad = str(tmp_path / "t.docx")
    formats.save(pfad, ed.document(), PageSettings())
    doc = formats.load(pfad).doc
    n = doc.rootFrame().childFrames()[0]
    assert n.cellAt(0, 0).format().background().color().name() == "#2f6fb5"
    assert n.cellAt(2, 0).format().background().color().name() == "#e7f0fa"
    assert n.cellAt(2, 1).format().toTableCellFormat().verticalAlignment() == QTextCharFormat.AlignMiddle
    assert n.format().border() == 0.5
