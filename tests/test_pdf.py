import pypdf


def norm(s):
    return ' '.join(s.split())
from PySide6.QtGui import QTextDocument, QTextCursor, QTextBlockFormat, QTextFormat

from native_qt.editor.page import PageSettings, HeaderFooter
from native_qt.editor.pagination import export_pdf, page_count


def _doc(n_pages_text=200, brk=False):
    d = QTextDocument(); c = QTextCursor(d)
    for i in range(n_pages_text):
        c.insertText(f"Zeile {i} " + "Wort " * 12)
        c.insertBlock()
    return d


def test_pdf_pages_and_header_footer(app, tmp_path):
    page = PageSettings(); page.header = HeaderFooter("Kopf", "center"); page.footer = HeaderFooter("Seite {PAGE} von {PAGES}", "right")
    d = _doc()
    n = page_count(d, page)
    assert n >= 3
    out = str(tmp_path / "t.pdf")
    assert export_pdf(out, d, page, "T") == n
    r = pypdf.PdfReader(out)
    assert len(r.pages) == n
    t0 = norm(r.pages[0].extract_text())
    assert "Zeile 0" in t0 and "Kopf" in t0 and f"Seite 1 von {n}" in t0
    assert f"Seite {n} von {n}" in norm(r.pages[-1].extract_text())
    # A4
    box = r.pages[0].mediabox
    assert abs(float(box.width) / 72 * 25.4 - 210) < 1 and abs(float(box.height) / 72 * 25.4 - 297) < 1


def test_pdf_landscape_and_page_break(app, tmp_path):
    page = PageSettings(); page.set_orientation(True)
    d = QTextDocument(); c = QTextCursor(d); c.insertText("Eins")
    bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
    c.insertBlock(bf); c.insertText("Zwei")
    out = str(tmp_path / "l.pdf")
    assert export_pdf(out, d, page) == 2
    r = pypdf.PdfReader(out)
    assert float(r.pages[0].mediabox.width) > float(r.pages[0].mediabox.height)
    assert "Eins" in r.pages[0].extract_text() and "Zwei" in r.pages[1].extract_text()


def test_font_size_in_pdf_matches(app, tmp_path):
    """12 pt im Dokument müssen im PDF als 12 pt ankommen."""
    d = QTextDocument(); c = QTextCursor(d)
    from PySide6.QtGui import QTextCharFormat
    f = QTextCharFormat(); f.setFontPointSize(12); c.insertText("Größentest", f)
    out = str(tmp_path / "s.pdf")
    export_pdf(out, d, PageSettings())
    sizes = []
    def visitor(text, cm, tm, fd, fs):
        if "Größentest" in text:
            sizes.append(fs * abs(tm[3]) * abs(cm[3]) if cm else fs)
    pypdf.PdfReader(out).pages[0].extract_text(visitor_text=visitor)
    assert sizes and abs(sizes[0] - 12) < 0.8, sizes


def test_pdf_mit_seitenfarbe_und_wasserzeichen(app, tmp_path):
    from PySide6.QtGui import QTextDocument
    from native_qt.editor.page import PageSettings
    from native_qt.editor.pagination import export_pdf
    d = QTextDocument(); d.setPlainText("Inhalt")
    pg = PageSettings(color="#ffeecc", watermark={"text": "ENTWURF", "farbe": "#c0c0c0", "winkel": -45, "groesse_pt": 80},
                      border={"art": "einfach", "farbe": "#000000", "breite_pt": 1.0, "abstand_mm": 8.0})
    out = str(tmp_path / "w.pdf")
    export_pdf(out, d, pg, "t")
    import pypdf
    txt = pypdf.PdfReader(out).pages[0].extract_text()
    assert "Inhalt" in txt and "ENTWURF" in " ".join(txt.split())
