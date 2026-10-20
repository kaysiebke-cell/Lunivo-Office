import pytest
from PySide6.QtGui import QTextCursor, QTextDocument, QTextCharFormat, QFont

from lunivo_writer.services import file_service as formats
from lunivo_writer.models.report import DocumentIOError
from lunivo_writer.models.page import PageSettings


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


def test_kennwort_roundtrip(app, tmp_path):
    import pytest
    pytest.importorskip("msoffcrypto")
    from PySide6.QtGui import QTextDocument
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.models.report import PasswortNoetig
    from lunivo_writer.models.page import PageSettings
    d = QTextDocument(); d.setPlainText("Streng geheim äöü")
    p = str(tmp_path / "g.docx")
    formats.save(p, d, PageSettings(), {"kennwort": "pw1"})
    with pytest.raises(PasswortNoetig):
        formats.load(p)
    with pytest.raises(PasswortNoetig) as ei:
        formats.load(p, "falsch")
    assert ei.value.falsch
    l = formats.load(p, "pw1")
    assert "Streng geheim äöü" in l.doc.toPlainText() and l.meta["kennwort"] == "pw1"
    with pytest.raises(DocumentIOError):                         # Webseiten werden nicht geschrieben
        formats.save(str(tmp_path / "x.html"), d, PageSettings())


def test_textbausteine_ohne_html(app, tmp_path, monkeypatch):
    """Ein Baustein wird mit Formatierung als einfache Absatzdaten gespeichert und wieder eingefügt."""
    import json
    from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment
    from lunivo_writer.services import bausteine
    monkeypatch.setattr(bausteine, "_pfad", lambda: str(tmp_path / "b.json"))
    d = QTextDocument(); c = QTextCursor(d)
    fett = QTextCharFormat(); fett.setFontWeight(QFont.Bold); fett.setForeground(QColor("#c92a2a")); fett.setFontPointSize(18)
    c.insertText("Guten ", QTextCharFormat()); c.insertText("Tag", fett); c.insertBlock(); c.insertText("Zweiter Absatz")
    bausteine.hinzufuegen("Gruss", QTextDocumentFragment(d))
    roh = (tmp_path / "b.json").read_text(encoding="utf-8")
    assert "html" not in roh.lower() and "<" not in roh
    eintrag = json.loads(roh)[0]
    assert eintrag["text"] == "Guten Tag\nZweiter Absatz" and len(eintrag["absaetze"]) == 2
    ziel = QTextDocument(); bausteine.einfuegen(QTextCursor(ziel), bausteine.laden()[0])
    assert ziel.toPlainText() == "Guten Tag\nZweiter Absatz"
    rc = QTextCursor(ziel); rc.setPosition(7); rc.setPosition(8, QTextCursor.KeepAnchor)
    f = rc.charFormat()
    assert f.fontWeight() >= QFont.Bold and f.foreground().color().name() == "#c92a2a" and f.fontPointSize() == 18
    # alter Eintrag ohne Absatzdaten: kommt als einfacher Text
    (tmp_path / "b.json").write_text(json.dumps([{"name": "alt", "text": "nur Text"}]), encoding="utf-8")
    z2 = QTextDocument(); bausteine.einfuegen(QTextCursor(z2), bausteine.laden()[0])
    assert z2.toPlainText() == "nur Text"
