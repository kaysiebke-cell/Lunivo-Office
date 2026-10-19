"""Barrierefreiheit, Thesaurus, Dokumentsprache."""
from PySide6.QtGui import QImage, QTextCharFormat, QTextCursor, QTextImageFormat

from lunivo_writer.services import docx_reader, docx_writer
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.models.page import PageSettings
from lunivo_writer.ai import ki as K
from lunivo_writer.proofing.barrierefreiheit import kontrast, pruefe
from lunivo_writer.ui.main_window import MainWindow
from lunivo_writer.services.settings_service import Settings
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor


def test_barrierefreiheit_findet_alle_vier_klassen(app):
    e = DocumentEditor(); e.setPlainText("Ein Text.\nUnd mehr.\nHier klicken")
    e.zusatz_binden({})
    c = e.textCursor(); c.setPosition(0); e.setTextCursor(c); e.apply_style("Überschrift 1")
    c.setPosition(10); e.setTextCursor(c); e.apply_style("Überschrift 3")           # Ebene übersprungen
    img = QImage(10, 10, QImage.Format_RGB32); img.fill(0)
    e.document().addResource(3, "b", img)
    f = QTextImageFormat(); f.setName("b"); f.setWidth(10); f.setHeight(10)
    c = e.textCursor(); c.movePosition(QTextCursor.End); c.insertImage(f)             # ohne Alternativtext
    c.setPosition(e.toPlainText().index("Und")); c.setPosition(c.position() + 3, QTextCursor.KeepAnchor)
    blass = QTextCharFormat(); blass.setForeground(QColor("#dddddd")); c.mergeCharFormat(blass)
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    e.insert_table(2, 2)                                                                 # Tabelle ohne Kopfzeile
    funde = " ".join(pruefe(e))
    assert "keine Beschreibung" in funde and "übersprungene Ebene" in funde and "keine Kopfzeile" in funde and "zu blass" in funde
    assert kontrast(QColor("black"), QColor("white")) > 20


def test_thesaurus_ersetzt_wort_mit_grossschreibung(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QInputDialog
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document(); w.show()
    e = w.current_editor(); e.insertPlainText("Das ist ein schönes Haus.")
    c = e.textCursor(); c.setPosition(e.toPlainText().index("schönes") + 2); e.setTextCursor(c)
    monkeypatch.setattr(K.KI, "verfuegbar", lambda self: True)
    monkeypatch.setattr(K.KI, "schickt_nach_aussen", lambda self, m=None: None)
    monkeypatch.setattr(K.KI, "synonyme", lambda self, wort, umg="": {"woerter": ["hübsches", "nettes"], "cent": None})
    monkeypatch.setattr(QInputDialog, "getItem", staticmethod(lambda *a, **k: ("hübsches", True)))
    w.befehle.thesaurus()
    w.ki._pool.waitForDone(5000)
    for _ in range(50):
        app.processEvents()
        if "hübsches" in e.toPlainText():
            break
    assert e.toPlainText() == "Das ist ein hübsches Haus."
    e.document().setModified(False); w.close()


def test_dokumentsprache_roundtrip(app, tmp_path):
    from PySide6.QtGui import QTextDocument
    d = QTextDocument(); d.setPlainText("Text")
    out = str(tmp_path / "s.docx")
    docx_writer.write_docx(out, d, PageSettings(), {"sprache": "en-GB"})
    _, _, meta, _ = docx_reader.read_docx(out)
    assert meta["sprache"] == "en-GB"
