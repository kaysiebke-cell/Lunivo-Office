import docx
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextCursor

from native_qt.document_io import formats
from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import PageSettings


def make(app, text="Hallo Welt\nZweite Zeile"):
    e = DocumentEditor(); e.setPlainText(text); return e


def select_all(e):
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)


def test_format_commands_land_in_docx(app, tmp_path):
    e = make(app)
    select_all(e)
    e.toggle_bold(True); e.set_font_size(16); e.set_font_family("DejaVu Sans")
    e.set_text_color(QColor("#ff0000")); e.set_alignment(Qt.AlignHCenter); e.set_line_spacing(1.5)
    e.change_indent(10)
    out = str(tmp_path / "f.docx")
    formats.save(out, e.document(), e.page)
    d = docx.Document(out)
    p = d.paragraphs[0]
    assert p.alignment == 1
    assert p.runs[0].bold and p.runs[0].font.size.pt == 16 and p.runs[0].font.name == "DejaVu Sans"
    assert str(p.runs[0].font.color.rgb) == "FF0000"
    assert abs(p.paragraph_format.left_indent.mm - 10) < 0.5
    assert abs(p.paragraph_format.line_spacing - 1.5) < 0.01


def test_styles_and_lists(app, tmp_path):
    e = make(app, "Kopf\nA\nB")
    c = e.textCursor(); c.setPosition(0); e.setTextCursor(c)
    e.apply_style("Überschrift 2")
    assert e.current_style() == "Überschrift 2"
    c = e.textCursor(); c.movePosition(QTextCursor.NextBlock); c.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor); e.setTextCursor(c)
    e.toggle_list("bullet")
    out = str(tmp_path / "s.docx"); formats.save(out, e.document(), e.page)
    d = docx.Document(out)
    assert [p.style.name for p in d.paragraphs] == ["Heading 2", "List Bullet", "List Bullet"]


def test_find_replace_all(app):
    e = make(app, "foo Foo bar foo")
    assert e.replace_all("foo", "X") == 3 and e.toPlainText() == "X X bar X"
    e.undo()
    assert e.toPlainText() == "foo Foo bar foo"          # ein Schritt rückgängig
    assert e.replace_all("foo", "X", case=True) == 2


def test_find_wraps(app):
    e = make(app, "abc abc")
    assert e.find_text("abc") and e.find_text("abc") and e.find_text("abc")


def test_page_count_and_margin_change(app):
    e = make(app, "\n".join(f"Zeile {i}" for i in range(120)))
    e._recount()
    n = e.page_count
    assert n >= 2
    pg = e.page.copy(); pg.margin_left_mm = pg.margin_right_mm = 60
    e.page_settings_changed(pg); e._recount()
    assert e.page_count >= n and e.document().isModified()


def test_table_image_pagebreak_roundtrip(app, tmp_path):
    from PySide6.QtGui import QImage
    img = QImage(100, 50, QImage.Format_RGB32); img.fill(QColor("blue")); ip = str(tmp_path / "i.png"); img.save(ip)
    e = make(app, "Vor")
    e.moveCursor(QTextCursor.End)
    e.insert_table(2, 3); e.moveCursor(QTextCursor.End)
    assert e.insert_image(ip)
    e.insert_page_break(); e.insertPlainText("Nach")
    out = str(tmp_path / "t.docx"); formats.save(out, e.document(), e.page)
    d = docx.Document(out)
    assert len(d.tables) == 1 and len(d.tables[0].rows) == 2 and len(d.tables[0].columns) == 3
    assert len(d.inline_shapes) == 1
    assert any(p.paragraph_format.page_break_before for p in d.paragraphs)
    # und wieder einlesen
    l = formats.load(out)
    assert "Nach" in l.doc.toPlainText()
