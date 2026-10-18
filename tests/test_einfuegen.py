"""Einfügen: Formen, WordArt, Diagramm, Piktogramm, Formel, Schnelltabelle, Deckblatt, Text aus Datei, Bausteine."""
import pytest
from PySide6.QtGui import QImage, QTextCursor, QTextDocument

from native_qt.document_io import docx_reader, docx_writer, formats
from native_qt.editor import einfuegen as E
from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import PageSettings
from native_qt.storage import bausteine


def ed(text="Anfang"):
    e = DocumentEditor(); e.setPlainText(text); e.zusatz_binden({})
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    return e


def bilder(doc):
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isImageFormat():
                yield f.charFormat().toImageFormat()
            it += 1
        b = b.next()


def test_bilder_aus_formen_wordart_diagramm_piktogramm_mit_alternativtext(app, tmp_path):
    e = ed()
    for f in E.FORMEN:
        img = E.form_bild(f, 100, 60, text="x" if f == "Rechteck" else "")
        assert not img.isNull() and img.width() == 100
    E.qimage_einfuegen(e, E.form_bild("Stern"), "Form: Stern")
    for st in E.WORDART_STILE:
        assert not E.wordart_bild("Test", st).isNull()
    E.qimage_einfuegen(e, E.wordart_bild("Test", "Verlauf"), "WordArt: Test")
    for art in E.DIAGRAMMARTEN:
        img = E.diagramm_bild(art, "T", ["a", "b"], {"R1": [1, 2], "R2": [3, 1]})
        assert img.width() == 640 and img.pixelColor(320, 5) is not None
    E.qimage_einfuegen(e, E.diagramm_bild("Säulen", "Umsatz", ["a", "b"], {"R": [1, 2]}), "Säulendiagramm: Umsatz")
    E.qimage_einfuegen(e, E.piktogramm_bild("heart", 64), "Piktogramm: heart")
    out = str(tmp_path / "i.docx")
    docx_writer.write_docx(out, e.document(), e.page, {})
    d2, _, _, rep = docx_reader.read_docx(out)
    alts = [f.property(0x100000 + 2) for f in bilder(d2)]
    assert alts == ["Form: Stern", "WordArt: Test", "Säulendiagramm: Umsatz", "Piktogramm: heart"]


def test_formel_hoch_tief_wurzel_griechisch(app):
    teile = E.formel_teile("E = m c^2 + x_{12} + sqrt(y) + \\alpha")
    assert ("2", "hoch") in teile and ("12", "tief") in teile
    assert "√(y)" in "".join(t for t, _ in teile) and "α" in "".join(t for t, _ in teile)
    e = ed("")
    E.formel_einfuegen(e, "a^2 + b^2 = c^2")
    assert e.toPlainText().startswith("a2 + b2 = c2")
    c = QTextCursor(e.document()); c.setPosition(1); c.setPosition(2, QTextCursor.KeepAnchor)
    assert c.charFormat().verticalAlignment().name == "AlignSuperScript"


def test_schnelltabellen_deckblatt_initiale_textfeld(app):
    for n in E.SCHNELLTABELLEN:
        e = ed(""); E.schnelltabelle(e, n)
        assert e.textCursor().currentTable() is not None
    e = ed("Hallo Welt")
    E.deckblatt_einfuegen(e, "Mit Linie", "Mein Titel", "Untertitel", "Ann", "1. Januar 2026")
    t = e.toPlainText()
    assert t.startswith("\nMein Titel") or "Mein Titel" in t[:40]
    assert t.rstrip().endswith("Hallo Welt")
    e2 = ed("Erster Satz hier.")
    c = e2.textCursor(); c.setPosition(2); e2.setTextCursor(c)
    assert E.initiale(e2)
    c = QTextCursor(e2.document()); c.setPosition(0); c.setPosition(1, QTextCursor.KeepAnchor)
    assert c.charFormat().fontPointSize() > 20
    e3 = ed(""); E.textfeld(e3)
    assert e3.textCursor().currentTable().rows() == 1 and e3.textCursor().currentTable().format().border() > 1


def test_text_aus_datei_mit_bild_und_baustein(app, tmp_path, monkeypatch):
    quelle = ed("Fremder Text")
    E.qimage_einfuegen(quelle, E.form_bild("Ellipse", 50, 50), "Kreis")
    pfad = str(tmp_path / "q.docx")
    docx_writer.write_docx(pfad, quelle.document(), quelle.page, {})
    e = ed("Vorher ")
    E.text_aus_datei(e, pfad)
    assert "Fremder Text" in e.toPlainText() and len(list(bilder(e.document()))) == 1
    img = e.document().resource(QTextDocument.ImageResource, __import__("PySide6.QtCore", fromlist=["QUrl"]).QUrl(next(bilder(e.document())).name()))
    assert img is not None and not QImage(img).isNull()
    # Textbausteine
    import native_qt.storage.bausteine as B
    monkeypatch.setattr(B, "_pfad", lambda: str(tmp_path / "b.json"))
    c = e.textCursor(); c.setPosition(0); c.setPosition(6, QTextCursor.KeepAnchor); e.setTextCursor(c)
    from PySide6.QtGui import QTextDocumentFragment
    B.hinzufuegen("Gruß", QTextDocumentFragment(c))
    assert [b["name"] for b in B.laden()] == ["Gruß"]
    e2 = ed("")
    B.einfuegen(e2.textCursor(), B.laden()[0])
    assert e2.toPlainText().strip() == "Vorher"
    B.entfernen("Gruß")
    assert not B.laden()
    assert E.datum_text("dd.MM.yyyy").count(".") == 2
