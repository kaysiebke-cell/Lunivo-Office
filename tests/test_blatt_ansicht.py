"""Echte DIN-A4-Blattansicht: Blätter mit Zwischenraum, Umbruch an der Textfläche, manueller Umbruch, PDF = Ansicht."""
import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QDropEvent, QTextCursor

from lunivo_writer.editor.pagination import export_pdf
from lunivo_writer.models.page import PageSettings, mm_to_px
from lunivo_writer.ui.document.document_editor import DocumentEditor
from tests.blatt_dokument import fuelle


def _editor(kapitel=6):
    ed = DocumentEditor()
    ed.show()
    fuelle(ed, kapitel)
    ed._recount()
    return ed


def test_a4_blaetter_mit_grauem_zwischenraum(app):
    ed = _editor()
    g = ed._sp_geo()
    assert ed.page_count >= 5 and ed.document().pageCount() == ed.page_count
    assert abs(g["H"] - mm_to_px(297)) < 0.01 and abs(g["gap"] - 32) < 0.01                      # DIN A4 hoch + fester Abstand
    assert ed.height() == int(g["top"] + ed.page_count * (g["H"] + g["gap"]))
    img = ed.grab().toImage()
    grau, papier = ed._arbeitsflaeche().rgb(), QColor("white").rgb()
    for k in range(3):
        mitte_gap = int(ed.blatt_oben(k) + g["H"] + g["gap"] * 0.8)               # unterhalb des Schattens
        assert img.pixel(img.width() // 2, mitte_gap) == grau                      # Arbeitsfläche sichtbar
    assert img.pixel(3, int(ed.blatt_oben(0) + 10)) in (papier, QColor("#b8bec6").rgb(), QColor("#5c6166").rgb())


def test_text_bleibt_in_der_textflaeche_jedes_blattes(app):
    ed = _editor()
    ch = ed.page.content_height_px * ed.zoom
    lay = ed.document().documentLayout()
    b = ed.document().firstBlock()
    while b.isValid():
        tl = b.layout()
        if tl is not None and tl.lineCount() and b.isVisible():
            top = lay.blockBoundingRect(b).top()
            for i in range(tl.lineCount()):
                ln = tl.lineAt(i)
                y0, y1 = top + ln.y(), top + ln.y() + ln.height()
                assert int((y0 + 0.5) // ch) == int((y1 - 0.5) // ch), "Zeile über eine Seitengrenze hinweg"
        b = b.next()


def test_manueller_seitenumbruch_beginnt_neues_blatt(app):
    ed = _editor()
    b = ed.document().begin()
    while b.isValid() and not b.text().startswith("Nach dem manuellen"):
        b = b.next()
    c = QTextCursor(b); ed.setTextCursor(c)
    y = ed.cursorRect().y()
    g = ed._sp_geo()
    k = int((y - g["top"]) // (g["H"] + g["gap"]))
    assert abs(y - (ed.blatt_oben(k) + g["mt"])) < 4                               # steht oben auf einem frischen Blatt


@pytest.mark.parametrize("zoom", [0.5, 1.0, 1.5])
def test_umbruch_unabhaengig_vom_zoom(app, zoom):
    ed = _editor()
    n1 = ed.page_count
    ed.set_zoom(zoom)
    ed._recount()
    assert ed.page_count == n1
    ed.grab()


def test_aenderung_loest_neuberechnung_aus_und_nichts_geht_verloren(app):
    ed = _editor(3)
    n0, z0 = ed.page_count, len(ed.document().toPlainText())
    c = ed.textCursor(); c.setPosition(0); ed.setTextCursor(c)
    for _ in range(40):
        ed.insertPlainText("Zusätzlicher Absatz, der die Seitenaufteilung verändert. " * 8 + "\n")
    ed._recount()
    assert ed.page_count > n0 and ed.height() > 0
    assert len(ed.document().toPlainText()) > z0


def test_klick_auf_zweitem_blatt_trifft_die_richtige_zeile(app):
    ed = _editor()
    c = QTextCursor(ed.document().findBlockByNumber(ed.document().blockCount() - 2)); c.setPosition(c.position() + 3)
    r = ed.cursorRect(c)
    ziel = QPoint(r.x() + 2, r.y() + r.height() // 2)
    assert ed.cursorForPosition(ziel).blockNumber() == c.blockNumber()


def test_ablegen_landet_an_der_blattposition(app):
    ed = _editor(2)
    c = QTextCursor(ed.document().findBlockByNumber(5)); c.setPosition(c.position() + 4)
    r = ed.cursorRect(c)
    m = QMimeData(); m.setText("DROP")
    ev = QDropEvent(QPointF(r.x() + 1, r.y() + r.height() // 2), Qt.CopyAction, m, Qt.LeftButton, Qt.NoModifier)
    ed.dropEvent(ev)
    assert "DROP" in ed.document().findBlockByNumber(5).text()


def test_pdf_hat_dieselbe_seitenzahl_wie_die_ansicht(app, tmp_path):
    from pypdf import PdfReader
    ed = _editor()
    pdf = str(tmp_path / "t.pdf")
    export_pdf(pdf, ed.document(), ed.page, noten=ed.noten)
    assert len(PdfReader(pdf).pages) == ed.page_count
    w, h = (float(x) for x in PdfReader(pdf).pages[0].mediabox[2:])
    assert abs(w / 72 * 25.4 - 210) < 1 and abs(h / 72 * 25.4 - 297) < 1


def test_querformat_und_ränder(app):
    ed = _editor(2)
    pg = ed.page.copy(); pg.set_orientation(True); pg.margin_left_mm = pg.margin_right_mm = 20
    ed.page_settings_changed(pg)
    g = ed._sp_geo()
    assert abs(g["H"] - mm_to_px(210)) < 1 and ed.document().pageSize().width() == round(mm_to_px(257))
    assert ed.page_count >= 2
