"""Fußnoten am Seitenfuß (Druck, PDF, Seitenansicht) und Sprungverweise im PDF."""
from PySide6.QtGui import QPdfWriter, QTextCharFormat, QTextCursor
from pypdf import PdfReader

from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import PageSettings
from native_qt.editor.pagination import export_pdf, fussnoten_am_seitenende, paginated_copy
from native_qt.editor.zusatz import P_NOTE


def _mit_noten(zeilen=140, marken=(10, 60, 61)):
    ed = DocumentEditor()
    ed.setPlainText("\n".join(f"Zeile {i} mit Text" for i in range(zeilen)))
    noten = {"f": {}, "e": {}}
    for k, nr in enumerate(marken, start=1):
        c = QTextCursor(ed.document().findBlockByNumber(nr))
        c.movePosition(QTextCursor.EndOfBlock)
        f = QTextCharFormat(); f.setVerticalAlignment(QTextCharFormat.AlignSuperScript); f.setProperty(P_NOTE, f"f:{k}")
        c.insertText(str(k), f)
        noten["f"][k] = f"Text der Fußnote {k}"
    ed.noten = noten
    return ed


def test_fussnoten_stehen_am_seitenfuss(app, tmp_path):
    ed = _mit_noten()
    pg = PageSettings()
    d = paginated_copy(ed.document(), pg, ed.noten)
    assert "Text der Fußnote 1" not in d.toPlainText()                    # nicht mehr gesammelt am Textende angehängt
    fuss = d._fussnoten
    seiten = sorted(fuss)
    assert seiten and seiten[0] == 1 and len(fuss[1]["noten"]) == 1
    assert 2 in fuss and len(fuss[2]["noten"]) == 2                       # die beiden Marken auf Seite 2 stehen gemeinsam
    # Der Text jeder Seite endet über dem Fußnotenbereich
    from native_qt.editor.pagination import _zeilenbereiche
    ch = pg.content_height_px
    for seite, info in fuss.items():
        letzte = max(u for (o, u, _p, _b) in _zeilenbereiche(d) if (o + 0.5) // ch == seite - 1)
        assert letzte - (seite - 1) * ch <= ch - info["hoehe"] + 1.5
    # PDF: Fußnote 1 steht auf Seite 1, nicht erst auf der letzten
    export_pdf(str(tmp_path / "n.pdf"), ed.document(), pg, "t", "", ed.noten)
    r = PdfReader(str(tmp_path / "n.pdf"))
    assert "Text der Fußnote 1" in " ".join(r.pages[0].extract_text().split())
    assert "Text der Fußnote 2" in " ".join(r.pages[1].extract_text().split())


def test_mehrspaltig_sammelt_fussnoten_am_ende(app):
    ed = _mit_noten(zeilen=60)
    pg = PageSettings(); pg.spalten = 2
    d = paginated_copy(ed.document(), pg, ed.noten)
    assert "Text der Fußnote 1" in d.toPlainText() and not hasattr(d, "_fussnoten")


def test_ohne_fussnoten_bleibt_alles_wie_vorher(app):
    ed = DocumentEditor(); ed.setPlainText("\n".join(f"Zeile {i}" for i in range(100)))
    d = paginated_copy(ed.document(), PageSettings(), {"f": {}, "e": {}})
    assert not hasattr(d, "_fussnoten") and d.pageCount() >= 2


def test_pdf_sprungverweise_zwischen_marke_und_note(app, tmp_path):
    ed = _mit_noten()
    export_pdf(str(tmp_path / "l.pdf"), ed.document(), PageSettings(), "t", "", ed.noten, None, None, None, {"notenlinks": True})
    r = PdfReader(str(tmp_path / "l.pdf"))
    ziele = []
    for nr, seite in enumerate(r.pages):
        for a in (seite.get("/Annots") or []):
            a = a.get_object()
            if a.get("/Subtype") == "/Link" and "/Dest" in a:
                ziele.append((nr, r.get_page_number(a["/Dest"][0].get_object())))
    # drei Marken und drei Notentexte → sechs Verweise; Marke auf Seite 1 führt auf Seite 1 (Fußnote 1), die auf Seite 2 auf Seite 2
    assert len(ziele) == 6
    assert (0, 0) in ziele and (1, 1) in ziele


def test_endnoten_im_pdf_verlinkt(app, tmp_path):
    ed = DocumentEditor(); ed.setPlainText("Satz mit Endnote\n" + "\n".join(f"Zeile {i}" for i in range(80)))
    c = QTextCursor(ed.document().findBlockByNumber(0)); c.movePosition(QTextCursor.EndOfBlock)
    f = QTextCharFormat(); f.setVerticalAlignment(QTextCharFormat.AlignSuperScript); f.setProperty(P_NOTE, "e:1")
    c.insertText("i", f)
    noten = {"f": {}, "e": {1: "Quelle der Endnote"}}
    export_pdf(str(tmp_path / "e.pdf"), ed.document(), PageSettings(), "t", "", noten, None, None, None, {"notenlinks": True})
    r = PdfReader(str(tmp_path / "e.pdf"))
    ziel_seite = len(r.pages) - 1
    ann = [a.get_object() for s in r.pages for a in (s.get("/Annots") or []) if a.get_object().get("/Subtype") == "/Link"]
    assert len(ann) == 2 and ziel_seite >= 1
    assert {r.get_page_number(a["/Dest"][0].get_object()) for a in ann} == {0, ziel_seite}
