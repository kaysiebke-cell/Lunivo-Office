import zipfile

import docx as D
import pytest
from PySide6.QtGui import QTextCursor

from lunivo_writer.editor import stile
from lunivo_writer.models.page import PageSettings
from lunivo_writer.services import file_service as formats
from lunivo_writer.ui.document.document_editor import DocumentEditor


@pytest.fixture(autouse=True)
def sauber():
    stile.laden_neu("")
    yield
    stile.laden_neu("")


def test_anlegen_regeln():
    assert stile.anlegen("Merksatz", fett=True, groesse=13) is None
    assert stile.anlegen("Merksatz")                          # doppelt
    assert stile.anlegen("Titel")                             # eingebaut
    assert stile.anlegen("  ")                                # leer
    assert stile.anlegen("x:böse")
    assert stile.namen()[-1] == "Merksatz" and stile.ist_eigen("Merksatz") and not stile.ist_eigen("Titel")
    d = stile.definition("Merksatz")
    assert d["fett"] and d["groesse"] == 13 and d["ebene"] == 0 and d["key"] == "x:Merksatz"
    stile.aendern("Merksatz", kursiv=True, ebene=3)
    assert stile.definition("Merksatz")["kursiv"] and stile.definition("Merksatz")["ebene"] == 0
    stile.laden_neu(stile.als_json_neu())                     # überlebt Speichern/Laden
    assert stile.ist_eigen("Merksatz") and stile.definition("Merksatz")["kursiv"]
    assert stile.loeschen("Merksatz") and not stile.ist_eigen("Merksatz")


def test_aus_auswahl_anwenden_und_loeschen(app):
    ed = DocumentEditor()
    ed.setPlainText("Wichtig")
    c = QTextCursor(ed.document()); c.select(QTextCursor.Document); ed.setTextCursor(c)
    ed.set_bold(True) if hasattr(ed, "set_bold") else None
    c = QTextCursor(ed.document()); c.setPosition(0); ed.setTextCursor(c)
    d = ed.stil_aus_auswahl()
    assert stile.anlegen("Hinweis", **d) is None
    ed.setPlainText("Anderer Absatz")
    ed.apply_style("Hinweis")
    assert ed.current_style() == "Hinweis"
    assert ed.stil_neu_anwenden("Hinweis") == 1
    assert ed.stil_entfernen("Hinweis") == 1
    assert ed.current_style() == "Standard"


def test_docx_rundreise_eigene_vorlage(app, tmp_path):
    stile.anlegen("Merksatz", fett=True, kursiv=True, groesse=14, farbe="#c92a2a", vor=6, nach=6, ausr="mitte")
    ed = DocumentEditor()
    ed.setPlainText("Wichtiger Satz")
    ed.apply_style("Merksatz")
    pfad = str(tmp_path / "m.docx")
    formats.save(pfad, ed.document(), PageSettings())
    # in Word-Sicht: echte Absatzvorlage mit den Eigenschaften
    st = {s.name: s for s in D.Document(pfad).styles}["Merksatz"]
    assert st.font.bold and st.font.italic and st.font.size.pt == 14 and str(st.font.color.rgb) == "C92A2A"
    assert zipfile.ZipFile(pfad).read("word/document.xml").decode().count('w:val="Merksatz"') == 1
    # in einer frischen Sitzung (Katalog leer) wird sie aus dem Dokument übernommen
    stile.laden_neu("")
    neu = DocumentEditor(); neu.setDocument(formats.load(pfad).doc)
    assert stile.ist_eigen("Merksatz")
    d = stile.definition("Merksatz")
    assert d["fett"] and d["kursiv"] and d["groesse"] == 14 and d["farbe"].lower() == "#c92a2a" and d["ausr"] == "mitte"
    c = QTextCursor(neu.document()); c.setPosition(0); neu.setTextCursor(c)
    assert neu.current_style() == "Merksatz"
