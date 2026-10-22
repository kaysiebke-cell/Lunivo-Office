"""Kommentare, Fuß-/Endnoten, nachverfolgte Änderungen und Textmarken: DOCX-Roundtrip."""
import os
import zipfile

import pytest
from PySide6.QtGui import QTextCharFormat, QTextCursor, QTextDocument

from lunivo_writer.services import docx_reader, docx_writer
from lunivo_writer.models.page import PageSettings
from lunivo_writer.editor.zusatz import P_AENDERUNG, P_AUTOR, P_DATUM, P_KOMMENTAR, P_NOTE


def _dokument():
    d = QTextDocument()
    d.setPlainText("Hallo Welt, gelöscht neu Ziel 1 hier")
    #               0         10        20        30
    c = QTextCursor(d); c.setPosition(0); c.setPosition(5, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setProperty(P_KOMMENTAR, 7); c.mergeCharFormat(f)
    c.setPosition(12); c.setPosition(20, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setProperty(P_AENDERUNG, "del"); f.setProperty(P_AUTOR, "Ann"); f.setProperty(P_DATUM, "2026-01-02T03:04:05Z")
    c.mergeCharFormat(f)
    c.setPosition(21); c.setPosition(24, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setProperty(P_AENDERUNG, "ins"); f.setProperty(P_AUTOR, "Bob"); c.mergeCharFormat(f)
    c.setPosition(25); c.setPosition(29, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setAnchor(True); f.setAnchorNames(["ziel"]); c.mergeCharFormat(f)
    c.setPosition(30)
    nf = QTextCharFormat(); nf.setVerticalAlignment(QTextCharFormat.AlignSuperScript); nf.setProperty(P_NOTE, "f:5")
    c.insertText("1", nf)
    return d


META = {"kommentare": {7: {"autor": "Ann", "initialen": "AN", "datum": "2026-01-02T03:04:05+00:00", "text": "Bitte prüfen\nZweite Zeile"}},
        "noten": {"f": {5: "Eine Fußnote."}, "e": {}}}


def test_zusatz_roundtrip(app, tmp_path):
    out = str(tmp_path / "z.docx")
    docx_writer.write_docx(out, _dokument(), PageSettings(), META)
    z = zipfile.ZipFile(out)
    assert "word/footnotes.xml" in z.namelist() and "word/comments.xml" in z.namelist()
    xml = z.read("word/document.xml").decode()
    assert "<w:del " in xml and "<w:delText" in xml and "<w:ins " in xml and "w:footnoteReference" in xml
    assert 'w:name="ziel"' in xml and "commentRangeStart" in xml

    d2, _, meta, rep = docx_reader.read_docx(out)
    assert not rep.warnings
    assert meta["kommentare"][0]["text"].startswith("Bitte prüfen") and meta["kommentare"][0]["autor"] == "Ann"
    assert list(meta["noten"]["f"].values()) == ["Eine Fußnote."]
    text = d2.toPlainText()
    assert "gelöscht" in text and "neu" in text           # gelöschter Text bleibt als solcher erhalten
    arten = {}
    c = QTextCursor(d2)
    for pos in range(len(text)):
        c.setPosition(pos + 1)
        cf = c.charFormat()
        if cf.hasProperty(P_AENDERUNG):
            arten[cf.stringProperty(P_AENDERUNG)] = (cf.stringProperty(P_AUTOR), cf.stringProperty(P_DATUM))
        if cf.hasProperty(P_KOMMENTAR):
            arten["komm"] = cf.property(P_KOMMENTAR)
        if cf.isAnchor() and "ziel" in cf.anchorNames():
            arten["lz"] = True
        if cf.hasProperty(P_NOTE):
            arten["note"] = cf.stringProperty(P_NOTE)
    assert arten["del"][0] == "Ann" and arten["ins"][0] == "Bob" and arten["del"][1].startswith("2026-01-02")
    assert arten["komm"] == 0 and arten["lz"] and arten["note"].startswith("f:")


def test_zusatz_datei_oeffnet_in_libreoffice(app, tmp_path):
    from lunivo_writer.services.integrations import libreoffice
    if not libreoffice.verfuegbar():
        pytest.skip("LibreOffice nicht installiert")
    out = str(tmp_path / "z.docx")
    docx_writer.write_docx(out, _dokument(), PageSettings(), META)
    pdf = str(tmp_path / "z.pdf")
    import subprocess
    r = subprocess.run([libreoffice.finde_soffice(), "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), out],
                       capture_output=True, timeout=120)
    assert os.path.exists(pdf), r.stderr
    import pypdf
    txt = " ".join(pypdf.PdfReader(pdf).pages[0].extract_text().split())
    assert "Eine Fußnote." in txt


def test_geloester_kommentar_ueberlebt_docx(app, tmp_path):
    """„Gelöst“ wird wie in Word als commentsExtended (w15:done) gespeichert und beim Öffnen wieder gelesen."""
    meta = {"kommentare": {7: {"autor": "Ann", "initialen": "AN", "datum": "2026-01-02T03:04:05+00:00", "text": "Erledigt", "geloest": True}},
            "noten": {"f": {5: "Eine Fußnote."}, "e": {}}}
    out = str(tmp_path / "g.docx")
    docx_writer.write_docx(out, _dokument(), PageSettings(), meta)
    z = zipfile.ZipFile(out)
    assert "word/commentsExtended.xml" in z.namelist() and 'done="1"' in z.read("word/commentsExtended.xml").decode()
    _d, _, meta2, _rep = docx_reader.read_docx(out)
    assert meta2["kommentare"][0]["geloest"] is True
    # offene Kommentare bleiben offen
    meta["kommentare"][7]["geloest"] = False
    docx_writer.write_docx(out, _dokument(), PageSettings(), meta)
    assert "word/commentsExtended.xml" not in zipfile.ZipFile(out).namelist()
    assert not read_offen(out)


def read_offen(pfad):
    _d, _, meta, _rep = docx_reader.read_docx(pfad)
    return [k for k in meta["kommentare"].values() if k.get("geloest")]
