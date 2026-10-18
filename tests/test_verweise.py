"""Beschriftungen, Verzeichnisse, Textmarken, Querverweise, Stichwörter, Zitate — Editor und DOCX."""
import os
import subprocess

import pytest
from PySide6.QtGui import QTextCursor

from native_qt.document_io import docx_reader, docx_writer
from native_qt.editor import verweise
from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import PageSettings
from native_qt.editor.verzeichnis import verzeichnis_aktualisieren, verzeichnis_einfuegen
from native_qt.editor.zusatz import B_ART, B_CAP, B_TOC, P_FELD, P_INDEX


def ed(text):
    e = DocumentEditor(); e.setPlainText(text); e.zusatz_binden({}); return e


def speichern_lesen(e, tmp_path, name="v.docx"):
    out = str(tmp_path / name)
    meta = dict(e._meta)
    docx_writer.write_docx(out, e.document(), e.page, meta)
    d2, p2, m2, rep = docx_reader.read_docx(out)
    e2 = DocumentEditor(); e2.set_document_and_page(d2, p2); e2.zusatz_binden(m2)
    return out, e2, rep


def test_beschriftungen_nummerieren_und_verzeichnis(app, tmp_path):
    e = ed("Kapitel\nText\nErste Stelle\nZweite Stelle")
    c = e.textCursor(); c.setPosition(0); e.setTextCursor(c); e.apply_style("Überschrift 1")
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    verweise.beschriftung_einfuegen(e, "Abbildung", "Zweite")
    c = e.textCursor(); c.setPosition(e.toPlainText().index("Erste")); e.setTextCursor(c)
    verweise.beschriftung_einfuegen(e, "Abbildung", "Erste")           # davor eingefügt → wird 1, die andere 2
    text = e.toPlainText()
    assert "Abbildung 1: Erste" in text and "Abbildung 2: Zweite" in text
    assert verzeichnis_einfuegen(e, "abb") == 2 and verzeichnis_einfuegen(e, "toc") == 1
    t = e.toPlainText()
    assert "Abbildungsverzeichnis" in t and "Inhaltsverzeichnis" in t and "Abbildung 2: Zweite\t1" in t
    # Roundtrip: Verzeichnisse werden wiedererkannt und lassen sich aktualisieren, Nummern sind Felder
    out, e2, rep = speichern_lesen(e, tmp_path)
    arten = {b.blockFormat().property(B_ART) for b in _bloecke(e2.document()) if b.blockFormat().hasProperty(B_TOC)}
    assert arten == {"abb", "toc"}
    felder = [f.charFormat().stringProperty(P_FELD) for f in e2._fragmente() if f.charFormat().hasProperty(P_FELD)]
    assert felder and all(x.startswith("SEQ Abbildung") for x in felder)
    assert sum(1 for b in _bloecke(e2.document()) if b.blockFormat().hasProperty(B_CAP)) == 2
    verzeichnis_aktualisieren(e2)
    assert "Abbildung 2: Zweite" in e2.toPlainText()


def _bloecke(doc):
    b = doc.firstBlock()
    while b.isValid():
        yield b
        b = b.next()


def test_textmarke_querverweis_roundtrip(app, tmp_path):
    e = ed("Einleitung\nHier steht das Ziel.\nVerweis: ")
    e.select_range(e.toPlainText().index("Ziel"), e.toPlainText().index("Ziel") + 4)
    assert verweise.lesezeichen_setzen(e, "mein_ziel")
    assert [d["name"] for d in verweise.lesezeichen_liste(e)] == ["mein_ziel"]
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    ziel = next(z for z in verweise.querverweis_ziele(e) if z["art"] == "Textmarke")
    verweise.querverweis_einfuegen(e, ziel, "text")
    out, e2, _ = speichern_lesen(e, tmp_path)
    assert [d["name"] for d in verweise.lesezeichen_liste(e2)] == ["mein_ziel"]
    hrefs = {f.charFormat().anchorHref() for f in e2._fragmente() if f.charFormat().anchorHref()}
    assert hrefs == {"#mein_ziel"}
    # Strg+Klick auf den Verweis springt zur Textmarke
    e2.select_range(0, 0)
    assert verweise.intern_springen(e2, "#mein_ziel") and e2.textCursor().selectedText() == "Ziel"
    verweise.lesezeichen_loeschen(e2, "mein_ziel")
    assert not verweise.lesezeichen_liste(e2)


def test_stichwoerter_und_zitate_roundtrip(app, tmp_path):
    e = ed("Der Apfel fällt nicht weit vom Stamm. Apfel noch einmal.")
    e.select_range(4, 9)
    assert verweise.index_markieren(e, "Apfel")
    q = {"typ": "Buch", "autor": "Müller, Hans; Meier, Eva", "titel": "Obst und Bäume", "jahr": "2020", "verlag": "Grün", "ort": "Berlin", "url": ""}
    q["tag"] = verweise.quelle_tag(e.quellen, q)
    e.quellen.append(q)
    assert q["tag"] == "Müller2020"
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    verweise.zitat_einfuegen(e, q)
    assert "(Müller, 2020)" in e.toPlainText()
    assert verzeichnis_einfuegen(e, "index") == 1 and verzeichnis_einfuegen(e, "lit") == 1
    assert "Apfel\t1" in e.toPlainText() and "Müller, Hans & Meier, Eva (2020). Obst und Bäume. Berlin, Grün." in e.toPlainText()
    out, e2, rep = speichern_lesen(e, tmp_path)
    assert not rep.warnings
    assert any(f.charFormat().hasProperty(P_INDEX) and f.charFormat().stringProperty(P_INDEX) == "Apfel" for f in e2._fragmente())
    assert e2.quellen and e2.quellen[0]["autor"] == "Müller, Hans; Meier, Eva" and e2.quellen[0]["jahr"] == "2020"
    assert e2.zitierweise == "APA"


def test_datei_mit_verweisen_oeffnet_in_libreoffice(app, tmp_path):
    from native_qt.integrations import libreoffice
    if not libreoffice.verfuegbar():
        pytest.skip("LibreOffice nicht installiert")
    e = ed("Kapitel\nText")
    c = e.textCursor(); c.setPosition(0); e.setTextCursor(c); e.apply_style("Überschrift 1")
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    verweise.beschriftung_einfuegen(e, "Tabelle", "Werte")
    e.select_range(0, 3); verweise.index_markieren(e, "Kap")
    verzeichnis_einfuegen(e, "toc")
    q = {"typ": "Buch", "autor": "A, B", "titel": "T", "jahr": "1999", "verlag": "", "ort": "", "url": "", "tag": "A1999"}
    e.quellen.append(q)
    out = str(tmp_path / "l.docx")
    docx_writer.write_docx(out, e.document(), e.page, dict(e._meta))
    r = subprocess.run([libreoffice.finde_soffice(), "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), out],
                       capture_output=True, timeout=120)
    assert os.path.exists(str(tmp_path / "l.pdf")), r.stderr
