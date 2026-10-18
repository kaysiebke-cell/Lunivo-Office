"""Sprechblasen: Kommentare/Änderungen als Blasen im Seitenrand (Anzeige), Einstellungen, Treffer, Druck und PDF."""
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest

from native_qt.editor import sprechblasen as SB
from native_qt.editor.editor_widget import DocumentEditor


def _ed(opts=None):
    ed = DocumentEditor()
    ed.setPlainText("Erster Absatz mit Text\nZweiter Absatz hier\nDritter Absatz zum Schluss")
    opts = opts or {}
    ed.opt_text = lambda n, s="": opts.get(n, s)
    ed.opt = lambda n, s=True: opts.get(n, s)
    ed.autor = lambda: ("Kay", "K")
    ed.show()
    return ed


def _kommentieren(ed, von, bis, text):
    c = ed.textCursor(); c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor); ed.setTextCursor(c)
    return ed.kommentar_neu(text)


def test_blasen_erscheinen_mit_dem_ersten_kommentar(app):
    ed = _ed()
    breite0 = ed.width()
    assert ed._blasen_flaeche is None or not ed._blasen_flaeche.isVisible()
    assert _kommentieren(ed, 7, 14, "Bitte prüfen") is not None
    assert ed._blasen_extra > 100 and ed.width() == breite0 + ed._blasen_extra
    assert ed._blasen_flaeche.isVisible() and ed._blasen_flaeche.width() == ed._blasen_extra
    lay = ed.blasen_layout(ed._blasen_extra)
    assert len(lay) == 1 and lay[0][0].text == "Bitte prüfen" and lay[0][0].autor == "Kay"
    # die Blase steht auf der Höhe ihrer Textzeile, die Seite selbst behält ihre Breite
    assert abs(lay[0][1].y() - ed.cursorRect(ed._cursor_at(7)).y()) < 4
    assert ed.viewport().width() == int(ed.width() - ed._blasen_extra) - 2 or abs(ed.viewport().width() - (ed.width() - ed._blasen_extra)) <= 4


def test_blasen_stapeln_ohne_ueberlappung_und_treffer(app):
    ed = _ed()
    for k, (v, b) in enumerate(((0, 6), (7, 14), (23, 30)), start=1):
        _kommentieren(ed, v, b, "Langer Kommentar " * 4 + str(k))
    lay = ed.blasen_layout(ed._blasen_extra)
    assert len(lay) == 3
    for (a, ra, _), (b, rb, _) in zip(lay, lay[1:]):
        assert rb.top() >= ra.bottom() - 0.5                         # nichts überlappt
    ed._blasen_flaeche.grab()                                         # zeichnet ohne Absturz
    # Klick auf eine Blase markiert den Text
    r = lay[1][1]
    QTest.mouseClick(ed._blasen_flaeche, Qt.LeftButton, Qt.NoModifier, QPoint(int(r.center().x()), int(r.center().y())))
    assert ed.textCursor().selectionStart() == lay[1][0].von and ed.textCursor().selectionEnd() == lay[1][0].bis


@pytest.mark.parametrize("opts, erwartet", [({"sprechblasen/verwenden": "Nie"}, False), ({"sprechblasen/rand": "Links"}, True),
                                             ({"sprechblasen/empfohlen": False, "sprechblasen/breite_mm": 90.0}, True)])
def test_einstellungen(app, opts, erwartet):
    ed = _ed(opts)
    _kommentieren(ed, 0, 6, "x")
    assert bool(ed._blasen_extra) is erwartet
    if opts.get("sprechblasen/rand") == "Links":
        assert ed.viewport().x() >= ed._blasen_extra
    if opts.get("sprechblasen/breite_mm") == 90.0:
        assert ed._blasen_extra > int(SB.breite_mm(SB.STANDARD) * 3.7795)       # breiter als die empfohlene Breite


def test_aenderungen_nur_bei_immer(app):
    from native_qt.editor.zusatz import P_AENDERUNG, P_AUTOR, P_DATUM
    from PySide6.QtGui import QTextCharFormat
    for modus, n in (("Nur für Kommentare", 0), ("Immer", 1)):
        ed = _ed({"sprechblasen/verwenden": modus})
        c = QTextCursor(ed.document()); c.setPosition(7); c.setPosition(14, QTextCursor.KeepAnchor)
        f = QTextCharFormat(); f.setProperty(P_AENDERUNG, "ins"); f.setProperty(P_AUTOR, "Anna"); f.setProperty(P_DATUM, "2026-10-18T10:00:00")
        c.mergeCharFormat(f)
        ed._zus_geaendert()
        assert len(SB.sammeln(ed.document(), ed.kommentare, modus)) == n
        assert bool(ed._blasen_extra) == bool(n)


def _mit_kommentaren():
    ed = DocumentEditor()
    ed.setPlainText("\n".join(f"Zeile {i} mit etwas Text" for i in range(130)))
    ed.autor = lambda: ("Kay", "K")
    c = ed.textCursor(); c.setPosition(5); c.setPosition(12, QTextCursor.KeepAnchor); ed.setTextCursor(c); ed.kommentar_neu("Erster Kommentar")
    c = QTextCursor(ed.document().findBlockByNumber(100)); c.setPosition(c.position() + 2); c.setPosition(c.position() + 6, QTextCursor.KeepAnchor)
    ed.setTextCursor(c); ed.kommentar_neu("Zweiter Kommentar auf Seite zwei")
    return ed


def _bd(**k):
    return {"konfig": dict(SB.STANDARD, **k), "kommentare": None}


def test_druck_mit_blasen_pdf(app, tmp_path):
    from pypdf import PdfReader
    from native_qt.editor.page import PageSettings
    from native_qt.editor.pagination import blasen_geometrie, export_pdf
    ed = _mit_kommentaren()
    pg = PageSettings()
    bd = _bd(); bd["kommentare"] = {k: f'{v["autor"]}: {v["text"]}' for k, v in ed.kommentare.items()}
    bd["kommentare"] = dict(ed.kommentare)
    g = blasen_geometrie(pg, {"blasen": bd})
    assert g and 0.5 < g["f"] < 0.8 and g["x_blasen"] > g["pw"] * g["f"]
    # Beibehalten → Hochformat, Querformat → drehen
    for aus, quer in (("Beibehalten", False), ("Querformat", True)):
        b2 = {"blasen": {"konfig": dict(bd["konfig"], ausrichtung=aus), "kommentare": bd["kommentare"]}}
        assert blasen_geometrie(pg, b2)["quer"] is quer
    export_pdf(str(tmp_path / "b.pdf"), ed.document(), pg, "t", "", None, None, None, None, {"blasen": bd})
    r = PdfReader(str(tmp_path / "b.pdf"))
    t1 = " ".join(r.pages[0].extract_text().split())
    t2 = " ".join(r.pages[1].extract_text().split())
    assert "Erster Kommentar" in t1 and "Kay" in t1
    assert "Zweiter Kommentar auf Seite zwei" in t2 and "Zweiter Kommentar" not in t1
    assert float(r.pages[0].mediabox.width) < float(r.pages[0].mediabox.height) or g["quer"]


def test_druck_blasen_links_und_ohne(app, tmp_path):
    from pypdf import PdfReader
    from native_qt.editor.page import PageSettings
    from native_qt.editor.pagination import blasen_geometrie, export_pdf
    ed = _mit_kommentaren()
    pg = PageSettings()
    bd = {"konfig": dict(SB.STANDARD, rand="Links", ausrichtung="Beibehalten"), "kommentare": dict(ed.kommentare)}
    g = blasen_geometrie(pg, {"blasen": bd})
    assert g["links"] and g["x_page"] > 0 and g["x_blasen"] == 0
    export_pdf(str(tmp_path / "l.pdf"), ed.document(), pg, "t", "", None, None, None, None, {"blasen": bd})
    assert "Erster Kommentar" in " ".join(PdfReader(str(tmp_path / "l.pdf")).pages[0].extract_text().split())
    assert blasen_geometrie(pg, {}) is None and blasen_geometrie(pg, {"blasen": None}) is None
