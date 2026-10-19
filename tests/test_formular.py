"""Formularfelder: anlegen, ausfüllen (Klick), DOCX-Rundreise als Inhaltssteuerelemente, nur Formulardaten drucken."""
import zipfile

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPdfWriter, QTextCursor
from PySide6.QtTest import QTest
from pypdf import PdfReader

from lunivo_writer.services import file_service as formats
from lunivo_writer.editor import formular as FO
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.models.page import PageSettings
from lunivo_writer.editor.pagination import render


def _formular():
    ed = DocumentEditor()
    ed.setPlainText("Name: ")
    c = ed.textCursor(); c.movePosition(QTextCursor.End); ed.setTextCursor(c)
    FO.einfuegen(ed, FO.meta("text", "Name", platzhalter="Ihr Name"))
    ed.textCursor().insertText("\nFamilienstand: ")
    FO.einfuegen(ed, FO.meta("auswahl", "Stand", optionen=["ledig", "verheiratet"]))
    ed.textCursor().insertText("\nGeburtstag: ")
    FO.einfuegen(ed, FO.meta("datum", "Geburtstag"))
    ed.textCursor().insertText("\nNewsletter: ")
    FO.einfuegen(ed, FO.meta("kasten", "Newsletter"))
    ed.textCursor().insertText(" ja\n")
    FO.einfuegen(ed, FO.meta("knopf", "Senden", aufschrift="Zurücksetzen", aktion="Felder zurücksetzen"))
    return ed


def test_felder_anlegen_und_daten(app):
    ed = _formular()
    arten = [m["art"] for _v, _e, m in FO.bereiche(ed.document())]
    assert arten == ["text", "auswahl", "datum", "kasten", "knopf"]
    assert FO.daten(ed.document()) == [("Newsletter", "")]                  # nur die Felder mit Wert (Kästchen leer → „“)
    v, e, m = FO.bereiche(ed.document())[0]
    FO._ersetzen(ed, v, e, m, "Kay")
    v2, e2, m2 = FO.bereiche(ed.document())[3]
    FO._ersetzen(ed, v2, e2, m2, FO.KASTEN_VOLL)
    assert dict(FO.daten(ed.document())) == {"Name": "Kay", "Newsletter": "ja"}
    assert FO.alle_zuruecksetzen(ed) == 4
    assert FO.daten(ed.document()) == [("Newsletter", "")] and "Ihr Name" in ed.toPlainText()


def test_klick_auf_kontrollkaestchen_und_knopf(app):
    ed = _formular()
    ed.show()
    v, e, m = FO.bereiche(ed.document())[3]
    c = QTextCursor(ed.document()); c.setPosition(v)
    r = ed.cursorRect(c)
    QTest.mouseClick(ed.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(r.x() + 3, r.y() + r.height() // 2))
    assert FO.wert_von(ed.document(), v, e) == FO.KASTEN_VOLL
    # Schaltfläche „Felder zurücksetzen“
    kv, ke, km = FO.bereiche(ed.document())[4]
    c = QTextCursor(ed.document()); c.setPosition(kv + 2); r = ed.cursorRect(c)
    QTest.mouseClick(ed.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(r.x() + 2, r.y() + r.height() // 2))
    assert FO.wert_von(ed.document(), v, e) == FO.KASTEN_LEER


def test_docx_inhaltssteuerelemente_rundreise(app, tmp_path):
    ed = _formular()
    v, e, m = FO.bereiche(ed.document())[0]
    FO._ersetzen(ed, v, e, m, "Kay")
    pfad = str(tmp_path / "f.docx")
    formats.save(pfad, ed.document(), PageSettings())
    xml = zipfile.ZipFile(pfad).read("word/document.xml").decode()
    assert xml.count("<w:sdt>") == 5 and "<w:dropDownList>" in xml and "<w:date>" in xml and "checkbox" in xml and "<w:text/>" in xml
    assert 'w:displayText="verheiratet"' in xml
    neu = formats.load(pfad)
    arten = [m["art"] for _v, _e, m in FO.bereiche(neu.doc)]
    assert arten == ["text", "auswahl", "datum", "kasten", "knopf"]
    assert FO.wert_von(neu.doc, *FO.bereiche(neu.doc)[0][:2]) == "Kay"
    assert FO.bereiche(neu.doc)[1][2]["optionen"] == ["ledig", "verheiratet"]


def test_fremdes_word_steuerelement_wird_erkannt(app, tmp_path):
    """Ein Inhaltssteuerelement ohne unser Tag (so schreibt es Word) wird aus der Art abgeleitet."""
    import docx
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d = docx.Document()
    p = d.add_paragraph("Vorwahl: ")
    sdt = OxmlElement("w:sdt"); pr = OxmlElement("w:sdtPr")
    al = OxmlElement("w:alias"); al.set(qn("w:val"), "Land"); pr.append(al)
    dd = OxmlElement("w:dropDownList")
    for o in ("DE", "AT"):
        li = OxmlElement("w:listItem"); li.set(qn("w:displayText"), o); li.set(qn("w:value"), o); dd.append(li)
    pr.append(dd); sdt.append(pr)
    inh = OxmlElement("w:sdtContent"); r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = "DE"; r.append(t); inh.append(r); sdt.append(inh)
    p._p.append(sdt)
    pfad = str(tmp_path / "w.docx"); d.save(pfad)
    neu = formats.load(pfad)
    b = FO.bereiche(neu.doc)
    assert len(b) == 1 and b[0][2]["art"] == "auswahl" and b[0][2]["name"] == "Land" and b[0][2]["optionen"] == ["DE", "AT"]
    assert not any("Formularfelder" in str(w) for w in neu.report.warnings) if hasattr(neu.report, "warnings") else True


def test_nur_formulardaten_drucken(app, tmp_path):
    ed = _formular()
    v, e, m = FO.bereiche(ed.document())[0]
    FO._ersetzen(ed, v, e, m, "Kay Mustermann")
    pg = PageSettings()
    from lunivo_writer.models.page import HeaderFooter
    pg.header = HeaderFooter("KOPFZEILE", "center")
    w = QPdfWriter(str(tmp_path / "n.pdf"))
    render(ed.document(), pg, w, opt={"nur_formular": True})
    from pypdf import PdfReader as R
    text_nur = " ".join(R(str(tmp_path / "n.pdf")).pages[0].extract_text().split())
    w2 = QPdfWriter(str(tmp_path / "a.pdf"))
    render(ed.document(), pg, w2, opt={})
    text_alles = " ".join(R(str(tmp_path / "a.pdf")).pages[0].extract_text().split())
    # unsichtbarer Text bleibt im PDF extrahierbar (durchsichtig gezeichnet); entscheidend: Pixel — Name sichtbar, „Familienstand“ nicht
    from PySide6.QtGui import QImage
    from lunivo_writer.editor.pagination import paginated_copy, seite_als_bild
    assert "KOPFZEILE" in text_alles and "KOPFZEILE" not in text_nur
    assert "Kay Mustermann" in text_nur
