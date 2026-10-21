import pytest
from lunivo_writer.editor import gehe_zu as G
from lunivo_writer.ui.dialogs.gehe_zu_dialog import GeheZuDialog
from lunivo_writer.ui.document.document_editor import DocumentEditor


@pytest.fixture
def ed(app):
    return DocumentEditor()


def test_zeile_und_ueberschrift(ed):
    ed.setPlainText("Eins\nZwei\nDrei")
    assert G.zeilenstart(ed, 2) == 5
    d = GeheZuDialog(None, ed, "Zeile")
    d.nummer.setValue(3)
    d.springen()
    assert ed.textCursor().blockNumber() == 2


def test_listen_leer(ed):
    ed.setPlainText("x")
    for a in G.LISTEN:
        assert isinstance(G.ziele(ed, a), list)
    assert G.ziele(ed, "Abschnitt")[0][1] == 0


def test_ueberschrift_4_bis_9_docx(app, tmp_path):
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    ed = DocumentEditor()
    for n in range(4, 10):
        ed.textCursor().insertText(f"Titel {n}")
        ed.apply_style(f"Überschrift {n}")
        ed.textCursor().insertBlock()
    pfad = str(tmp_path / "u.docx")
    formats.save(pfad, ed.document(), PageSettings())
    doc = formats.load(pfad).doc
    assert [doc.findBlockByNumber(i).blockFormat().headingLevel() for i in range(6)] == [4, 5, 6, 7, 8, 9]


def test_tabstopps_dialog_und_docx(app, tmp_path):
    from PySide6.QtGui import QTextOption
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog
    ed = DocumentEditor()
    ed.setPlainText("a\tb")
    d = TabstoppDialog(None, [])
    d.pos.setValue(50); d.art.button(2).setChecked(True); d.festlegen()
    d.pos.setValue(100); d.art.button(1).setChecked(True); d.festlegen()
    ed.set_tabstopps(d.stopps())
    pfad = str(tmp_path / "t.docx")
    formats.save(pfad, ed.document(), PageSettings())
    t = formats.load(pfad).doc.firstBlock().blockFormat().tabPositions()
    assert [x.type for x in t] == [QTextOption.RightTab, QTextOption.CenterTab]
    assert abs(sum(1 for _ in t) - 2) == 0
