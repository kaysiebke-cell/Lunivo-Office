import pytest
from PySide6.QtGui import QTextCursor, QTextDocument, QTextCharFormat, QFont

from native_qt.document_io import formats
from native_qt.document_io.report import DocumentIOError
from native_qt.editor.page import PageSettings


def test_txt_roundtrip_with_umlaute(app, tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes("Grüße\nzweite Zeile ß€".encode("utf-8"))
    l = formats.load(str(p))
    assert l.doc.toPlainText() == "Grüße\nzweite Zeile ß€"
    q = tmp_path / "b.txt"
    formats.save(str(q), l.doc, l.page)
    assert q.read_bytes() == p.read_bytes()


def test_txt_cp1252_fallback(app, tmp_path):
    p = tmp_path / "c.txt"; p.write_bytes("Käse".encode("cp1252"))
    assert formats.load(str(p)).doc.toPlainText() == "Käse"


def test_txt_save_warns_on_data_loss(app, tmp_path):
    d = QTextDocument(); c = QTextCursor(d)
    f = QTextCharFormat(); f.setFontWeight(QFont.Bold); c.insertText("fett", f)
    rep = formats.save(str(tmp_path / "x.txt"), d, PageSettings())
    assert rep and "Formatierung" in rep.warnings[0]


def test_odt_export_is_valid_zip(app, tmp_path):
    import zipfile
    d = QTextDocument(); QTextCursor(d).insertText("Hallo ODT")
    out = tmp_path / "x.odt"
    rep = formats.save(str(out), d, PageSettings())
    assert rep.warnings
    with zipfile.ZipFile(out) as z:
        assert b"Hallo ODT" in z.read("content.xml")


def test_missing_and_unknown(app, tmp_path):
    with pytest.raises(DocumentIOError):
        formats.load(str(tmp_path / "nicht-da.docx"))
    p = tmp_path / "x.xyz"; p.write_text("a")
    with pytest.raises(DocumentIOError):
        formats.load(str(p))


def test_save_to_unwritable_folder(app, tmp_path):
    d = QTextDocument(); QTextCursor(d).insertText("x")
    with pytest.raises(DocumentIOError):
        formats.save("/proc/nicht/möglich.docx", d, PageSettings())
