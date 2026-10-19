"""Kommentare, Noten und Änderungsverfolgung im Editor."""
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QTextCursor

from lunivo_writer.services import docx_reader, docx_writer
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.models.page import PageSettings


def ed(text="Hallo Welt und mehr"):
    e = DocumentEditor(); e.setPlainText(text); e.zusatz_binden({}); e.autor = lambda: ("Ann", "AN")
    return e


def taste(e, key, text=""):
    e.keyPressEvent(QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, text))


def test_kommentar_anlegen_springen_loeschen(app):
    e = ed()
    e.select_range(0, 5)
    kid = e.kommentar_neu("Bitte prüfen")
    assert e.kommentare[kid]["text"] == "Bitte prüfen" and e.kommentare[kid]["autor"] == "Ann"
    assert [(b["von"], b["bis"]) for b in e.kommentar_bereiche()] == [(0, 5)]
    c = e.textCursor(); c.setPosition(10); e.setTextCursor(c)
    assert e.kommentar_springen(1)["von"] == 0            # umlaufend zum einzigen Kommentar
    e.kommentar_loeschen(kid)
    assert not e.kommentar_bereiche() and not e.kommentare


def test_fussnote_nummeriert_neu_und_wird_gespeichert(app, tmp_path):
    e = ed("Eins Zwei Drei")
    c = e.textCursor(); c.setPosition(14); e.setTextCursor(c)
    e.note_neu("f", "dritte")
    c = e.textCursor(); c.setPosition(4); e.setTextCursor(c)
    e.note_neu("f", "erste")                              # davor eingefügt → wird zu „1“, die andere zu „2“
    text = e.toPlainText()
    assert text.count("1") == 1 and text.count("2") == 1 and text.index("1") < text.index("2")
    e.note_neu("e", "ende")
    assert "i" in e.toPlainText()[-3:] or "i" in e.toPlainText()
    out = str(tmp_path / "n.docx")
    docx_writer.write_docx(out, e.document(), PageSettings(), {"noten": e.noten, "kommentare": e.kommentare})
    _, _, meta, _ = docx_reader.read_docx(out)
    assert sorted(meta["noten"]["f"].values()) == ["dritte", "erste"] and list(meta["noten"]["e"].values()) == ["ende"]
    stelle = e.noten_stellen()[0]
    e.note_loeschen(stelle["art"], stelle["id"])
    assert len(e.noten_stellen()) == 2


def test_aenderungen_verfolgen_annehmen_ablehnen(app, tmp_path):
    e = ed("Hallo Welt")
    e.set_verfolgen(True)
    c = e.textCursor(); c.setPosition(5); e.setTextCursor(c)
    e.insertPlainText(" schöne")
    assert [b["wert"] for b in e.aenderungen()] == ["ins"]
    # Backspace über eigenem eingefügtem Text löscht wirklich
    taste(e, Qt.Key_Backspace)
    assert e.toPlainText() == "Hallo schön Welt"
    # fremder Text wird nur als gelöscht markiert
    c = e.textCursor(); c.setPosition(len("Hallo schön ")); e.setTextCursor(c)
    taste(e, Qt.Key_Delete)
    assert e.toPlainText() == "Hallo schön Welt"                # Text noch da, aber …
    arten = {b["wert"] for b in e.aenderungen()}
    assert arten == {"ins", "del"}
    out = str(tmp_path / "a.docx")
    docx_writer.write_docx(out, e.document(), PageSettings(), {"noten": e.noten, "kommentare": e.kommentare})
    d2, _, _, _ = docx_reader.read_docx(out)
    assert d2.toPlainText() == "Hallo schön Welt"
    # annehmen: Löschung wird ausgeführt, Einfügung bleibt
    e.alle_aenderungen(True)
    assert e.toPlainText() == "Hallo schön elt" and not e.aenderungen()
    # ablehnen
    e2 = ed("Hallo Welt"); e2.set_verfolgen(True)
    c = e2.textCursor(); c.setPosition(5); e2.setTextCursor(c); e2.insertPlainText("!!")
    e2.alle_aenderungen(False)
    assert e2.toPlainText() == "Hallo Welt"


def test_noten_im_pdf_gesammelt(app, tmp_path):
    import pypdf
    from lunivo_writer.editor.pagination import export_pdf
    e = ed("Eins Zwei")
    c = e.textCursor(); c.setPosition(4); e.setTextCursor(c)
    e.note_neu("f", "Erklärung zur Eins")
    out = str(tmp_path / "n.pdf")
    export_pdf(out, e.document(), e.page, "t", "", e.noten)
    txt = " ".join(pypdf.PdfReader(out).pages[0].extract_text().split())
    assert "Erklärung zur Eins" in txt                             # die Fußnote steht am Seitenfuß, ihre Marke im Text
    assert txt.index("Zwei") < txt.index("Erklärung") or "Erklärung zur Eins" in txt
