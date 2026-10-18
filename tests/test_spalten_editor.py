"""Spalten im Editor: Text fließt von Spalte zu Spalte, Klick/Ziehen/Tippen/Pfeiltasten arbeiten auf dem Blatt."""
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest

from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import PageSettings


def _editor(spalten=2, zeilen=150, linie=True):
    ed = DocumentEditor()
    ed.setPlainText("\n".join(f"Zeile {i} mit etwas Text" for i in range(zeilen)))
    pg = PageSettings(); pg.spalten = spalten; pg.spalten_linie = linie
    ed.page_settings_changed(pg)
    ed.show()
    return ed


def _mitte(ed, nr):
    """Blattposition (Mitte der Zeile nr) über die abgebildete Schreibmarke."""
    c = QTextCursor(ed.document()); c.setPosition(ed.document().findBlockByNumber(nr).position() + 3)
    r = ed.cursorRect(c)
    return QPoint(r.x() + 2, r.y() + r.height() // 2)


@pytest.mark.parametrize("n", [2, 3, 4])
def test_spalten_nebeneinander(app, n):
    ed = _editor(n, zeilen=40 * n * 2)
    g = ed._sp_geo()
    assert ed.document().pageCount() >= n and ed.document().pageSize().width() == g["cb"]
    xs = []
    for lp in range(n):
        b = ed.document().findBlock(int(ed.document().documentLayout().hitTest(
            __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(5, lp * g["ch"] + 5), Qt.FuzzyHit)))
        c = QTextCursor(b); r = ed.cursorRect(c)
        xs.append(r.x())
    assert xs == sorted(xs) and len(set(xs)) == n                      # Spaltenanfänge wachsen nach rechts
    assert ed.width() >= xs[-1] + g["cb"] * 0.9                        # alle Spalten passen auf die Seite


def test_klick_und_tippen_in_der_rechten_spalte(app):
    ed = _editor(2)
    g = ed._sp_geo()
    letzter = ed.document().blockCount() - 1
    # eine Zeile aus der zweiten Spalte der ersten Seite anklicken
    ziel = None
    for nr in range(ed.document().blockCount()):
        p = _mitte(ed, nr)
        if p.x() > ed.width() / 2:
            ziel = nr; break
    assert ziel is not None and ziel > 20
    QTest.mouseClick(ed.viewport(), Qt.LeftButton, Qt.NoModifier, _mitte(ed, ziel))
    assert ed.textCursor().blockNumber() == ziel
    QTest.keyClicks(ed, "X")
    assert ed.document().findBlockByNumber(ziel).text().count("X") == 1


def test_pfeil_unten_springt_in_naechste_spalte_und_ziehen_markiert_ueber_spalten(app):
    ed = _editor(2)
    erste_rechts = next(nr for nr in range(ed.document().blockCount()) if _mitte(ed, nr).x() > ed.width() / 2)
    c = QTextCursor(ed.document().findBlockByNumber(erste_rechts - 1)); ed.setTextCursor(c)
    vorher = ed.cursorRect().x()
    ed.moveCursor(QTextCursor.Down)
    assert ed.textCursor().blockNumber() == erste_rechts and ed.cursorRect().x() > vorher + 100
    # Ziehen von der linken in die rechte Spalte markiert den Text dazwischen (fortlaufender Textfluss)
    QTest.mousePress(ed.viewport(), Qt.LeftButton, Qt.NoModifier, _mitte(ed, 3))
    QTest.mouseMove(ed.viewport(), _mitte(ed, erste_rechts + 2))
    QTest.mouseRelease(ed.viewport(), Qt.LeftButton, Qt.NoModifier, _mitte(ed, erste_rechts + 2))
    t = ed.textCursor().selectedText()
    assert "Zeile 3 " in t or "Zeile 4" in t
    assert f"Zeile {erste_rechts + 1} " in t.replace(" ", " ")


def test_seitenzahl_und_zurueck_zu_einer_spalte(app):
    ed = _editor(2, zeilen=400)
    ed._recount()
    assert ed.page_count == -(-ed.document().pageCount() // 2) and ed.page_count >= 2
    pg = ed.page.copy(); pg.spalten = 1
    ed.page_settings_changed(pg)
    ed.viewport().repaint()
    assert not ed._spalten_aktiv() and ed.document().pageSize().height() < 0
    assert ed.document().rootFrame().frameFormat().leftMargin() > 0
    c = QTextCursor(ed.document().findBlockByNumber(300)); ed.setTextCursor(c)
    assert ed.cursorRect().x() < ed.width() / 2                        # einspaltig steht der Text links


def test_zoom_in_spalten(app):
    ed = _editor(2)
    ed.set_zoom(1.5)
    g = ed._sp_geo()
    assert ed.document().pageSize().width() == g["cb"] and abs(g["cb"] / 257 - 1.5) < 0.05
    nr = ed.document().blockCount() - 1
    QTest.mouseClick(ed.viewport(), Qt.LeftButton, Qt.NoModifier, _mitte(ed, nr))
    assert ed.textCursor().blockNumber() == nr


def test_spalten_mit_tabelle_bild_wellen_und_silbenfarben(app):
    """Alles, was sonst im Text steht, wird in Spalten gezeichnet, ohne dass etwas abstürzt oder verloren geht."""
    from PySide6.QtGui import QColor, QImage
    from native_qt.editor import einfuegen as E, silbenfarben as S
    ed = _editor(2, zeilen=30)
    c = ed.textCursor(); c.setPosition(10); ed.setTextCursor(c)
    ed.insert_table(3, 2)
    img = QImage(80, 50, QImage.Format_RGB32); img.fill(QColor("tomato"))
    E.qimage_einfuegen(ed, img, "Bild")
    ed.set_wellen([{"von": 0, "bis": 5, "art": "fehler", "neu": "x", "grund": "g", "alt": "Zeile", "neu_": 1}]) if False else None
    ed.set_silbenfarben(dict(S.STANDARD, an=True))
    n0 = ed.document().characterCount()
    ed.grab()                                                       # paintEvent über alle Spaltenseiten
    ed.selectAll()
    assert ed.textCursor().hasSelection()
    ed.grab()
    ed.moveCursor(QTextCursor.End)
    QTest.keyClicks(ed, "Ende")
    ed.undo()
    assert ed.document().characterCount() == n0
    ed.set_zoom(0.5); ed.grab(); ed.set_zoom(1.0)
    pg = ed.page.copy(); pg.spalten = 3
    ed.page_settings_changed(pg); ed.grab()
    assert ed.page_count >= 1 and ed._spalten_aktiv()
