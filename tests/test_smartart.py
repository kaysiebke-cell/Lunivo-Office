from PySide6.QtGui import QTextCursor

from lunivo_writer.editor import formen
from lunivo_writer.editor import smartart as SA
from lunivo_writer.models.page import PageSettings
from lunivo_writer.services import file_service as formats
from lunivo_writer.ui.document.document_editor import DocumentEditor


def test_punkte_ebenen():
    assert SA.punkte("A\n  B\n    C\n\nD") == [(0, "A"), (1, "B"), (2, "C"), (0, "D")]
    assert SA.punkte("A\n\tB") == [(0, "A"), (1, "B")]


def test_jedes_layout_zeichnet(app):
    for lay in SA.LAYOUTS:
        for farben in SA.FARBEN:
            img = SA.zeichnen({"layout": lay, "farben": farben, "text": SA.MUSTER[lay]})
            assert img.width() > 100 and img.height() > 40
            # nicht leer: irgendwo ein deckendes Pixel
            assert any(img.pixelColor(x, y).alpha() > 200 for x in range(0, img.width(), 7) for y in range(0, img.height(), 7))


def test_hoehe_waechst_mit_punkten(app):
    kurz = SA.zeichnen({"layout": "Liste", "text": "a\nb"})
    lang = SA.zeichnen({"layout": "Liste", "text": "a\nb\nc\nd\ne"})
    assert lang.height() > kurz.height()


def test_einfuegen_aendern_docx_rundreise(app, tmp_path):
    ed = DocumentEditor()
    SA.einfuegen(ed, {"layout": "Prozess", "farben": "Blau", "text": "Eins\nZwei\nDrei"})
    c = QTextCursor(ed.document()); c.setPosition(0); ed.setTextCursor(c)
    assert SA.daten_der_auswahl(ed)["layout"] == "Prozess"
    assert SA.aendern(ed, layout="Pyramide", text="Oben\nMitte\nUnten\nBasis")
    d = SA.daten_der_auswahl(ed)
    assert d["layout"] == "Pyramide" and d["text"].startswith("Oben") and d["farben"] == "Blau"
    pfad = str(tmp_path / "s.docx")
    formats.save(pfad, ed.document(), PageSettings())
    neu = DocumentEditor(); neu.setDocument(formats.load(pfad).doc)
    c = QTextCursor(neu.document()); c.setPosition(0); neu.setTextCursor(c)
    d2 = SA.daten_der_auswahl(neu)
    assert d2 == d                                                     # nach dem Öffnen noch bearbeitbar
    assert (formen.objekt(neu.bild_format()) or {}).get("art") == "smartart"
    assert SA.aendern(neu, farben="Grün") and SA.daten_der_auswahl(neu)["farben"] == "Grün"


def test_kein_smartart_wird_nicht_geaendert(app):
    ed = DocumentEditor()
    ed.setPlainText("Text")
    assert SA.daten_der_auswahl(ed) is None and not SA.aendern(ed, layout="Liste")
