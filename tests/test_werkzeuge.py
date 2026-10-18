"""Kopfzeile erste Seite, Tabellen sortieren, Bild bearbeiten, PNG-Export, eigene Assistenten, Dokument schützen."""
import os

import pypdf
import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QImage, QTextCursor, QTextDocument
from PySide6.QtWidgets import QFileDialog, QInputDialog

from native_qt.document_io import docx_reader, docx_writer
from native_qt.editor import einfuegen as E
from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import HeaderFooter, PageSettings
from native_qt.editor.pagination import export_pdf
from native_qt.storage.settings import Settings
from native_qt.windows.main_window import MainWindow


def win(tmp_path):
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document(); w.show()
    return w


def fertig(w):
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()


def test_erste_seite_anders_pdf_und_docx(app, tmp_path):
    d = QTextDocument(); d.setPlainText("\n".join(f"Zeile {i}" for i in range(120)))
    pg = PageSettings(header=HeaderFooter("Kopf Folgeseite", "center"), diff_first=True,
                      first_header=HeaderFooter("Kopf Titelseite", "center"))
    out = str(tmp_path / "e.pdf")
    export_pdf(out, d, pg, "t")
    r = pypdf.PdfReader(out)
    assert len(r.pages) >= 2
    t0, t1 = (" ".join(r.pages[i].extract_text().split()) for i in (0, 1))
    assert "Kopf Titelseite" in t0 and "Kopf Folgeseite" not in t0
    assert "Kopf Folgeseite" in t1 and "Kopf Titelseite" not in t1
    docx = str(tmp_path / "e.docx")
    docx_writer.write_docx(docx, d, pg, {})
    _, p2, _, rep = docx_reader.read_docx(docx)
    assert p2.diff_first and p2.first_header.text == "Kopf Titelseite" and p2.header.text == "Kopf Folgeseite"
    assert not any("Erste Seite" in x for x in rep.warnings)


def test_tabelle_sortieren_und_eigenschaften(app, tmp_path, monkeypatch):
    w = win(tmp_path)
    e = w.current_editor()
    e.insert_table(4, 2)
    zellen = [("Name", "Zahl"), ("Cora", "10"), ("Anton", "9"), ("Berta", "100")]
    t = e.textCursor().currentTable()
    for r, (a, b) in enumerate(zellen):
        t.cellAt(r, 0).firstCursorPosition().insertText(a); t.cellAt(r, 1).firstCursorPosition().insertText(b)
    t.setFormat(_mit_kopf(t))
    c = t.cellAt(1, 0).firstCursorPosition(); e.setTextCursor(c)
    antworten = iter([("Spalte 2", True), ("Aufsteigend", True)])
    monkeypatch.setattr(QInputDialog, "getItem", staticmethod(lambda *a, **k: next(antworten)))
    w.befehle.tabelleSortieren()
    spalte2 = [t.cellAt(r, 1).firstCursorPosition().block().text() for r in range(4)]
    assert spalte2 == ["Zahl", "9", "10", "100"]                     # numerisch, Kopfzeile bleibt oben
    spalte1 = [t.cellAt(r, 0).firstCursorPosition().block().text() for r in range(4)]
    assert spalte1 == ["Name", "Anton", "Cora", "Berta"]
    fertig(w)


def _mit_kopf(t):
    f = t.format(); f.setHeaderRowCount(1); return f


def test_bild_farbe_zuschneiden_drehen_original(app, tmp_path):
    e = DocumentEditor(); e.zusatz_binden({})
    img = QImage(40, 20, QImage.Format_RGB32); img.fill(QColor("#ff0000"))
    E.qimage_einfuegen(e, img, "rot")
    c = e.textCursor(); c.setPosition(0); c.setPosition(1, QTextCursor.KeepAnchor); e.setTextCursor(c)
    assert E.bild_ersetzen(e, lambda i: E.farbe_anwenden(i, "Graustufen"))
    f = e.bild_format()
    neu = QImage(e.document().resource(2, __import__("PySide6.QtCore", fromlist=["QUrl"]).QUrl(f.name())))
    px = neu.pixelColor(5, 5)
    assert abs(px.red() - px.green()) < 3 and abs(px.green() - px.blue()) < 3         # grau
    assert E.bild_ersetzen(e, lambda i: E.zuschneiden(i, 10, 0, 10, 5))
    f = e.bild_format()
    assert round(f.width()) == 20 and round(f.height()) == 15
    assert E.bild_ersetzen(e, lambda i: E.drehen(i, "rechts"))
    f = e.bild_format()
    assert round(f.width()) == 15 and round(f.height()) == 20
    assert f.property(E.ORIGINAL_PROP) and E.bild_original(e)
    f = e.bild_format()
    assert round(f.width()) == 40 and round(f.height()) == 20 and f.property(E.STYLE_PROP + 1) == "rot"


def test_png_export_pro_seite(app, tmp_path, monkeypatch):
    w = win(tmp_path)
    w.current_editor().insertPlainText("\n".join(f"Zeile {i}" for i in range(140)))
    ziel = str(tmp_path / "seiten.png")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (ziel, "")))
    w.befehle.exportierenPng()
    dateien = sorted(f for f in os.listdir(tmp_path) if f.startswith("seiten") and f.endswith(".png"))
    assert len(dateien) >= 2 and dateien[0] == "seiten-1.png"
    b = QImage(str(tmp_path / dateien[0]))
    assert not b.isNull() and b.width() > 1000
    fertig(w)


def test_eigener_assistent_speichern_und_ausfuehren(app, tmp_path, monkeypatch):
    from native_qt.services import ki as K
    w = win(tmp_path)
    monkeypatch.setattr(w.ki.konfig, "pfad", str(tmp_path / "ki.json"))
    a = w.ki.konfig.assistent_hinzufuegen("Förmlicher", "Schreibe förmlicher.", "ersetzen")
    assert w.ki.konfig["assistenten"][0]["name"] == "Förmlicher" and a["modus"] == "ersetzen"
    m = w.befehle.menue_assistenten()
    assert "Förmlicher" in [x.text() for x in m.actions()]
    e = w.current_editor(); e.insertPlainText("Hallo du.")
    monkeypatch.setattr(K.KI, "verfuegbar", lambda self: True)
    monkeypatch.setattr(K.KI, "schickt_nach_aussen", lambda self, m=None: None)
    monkeypatch.setattr(K.KI, "eigener_assistent", lambda self, text, prompt: {"text": "Guten Tag.", "cent": None})
    w.ki.assistent(a)
    w.ki._pool.waitForDone(5000)
    for _ in range(50):
        app.processEvents()
        if e.toPlainText() == "Guten Tag.":
            break
    assert e.toPlainText() == "Guten Tag."
    w.ki.konfig.assistent_entfernen(a["id"])
    assert not w.ki.konfig["assistenten"]
    fertig(w)


def test_dokument_schuetzen_und_abschnittsumbruch(app, tmp_path, monkeypatch):
    w = win(tmp_path)
    t = w.current_tab()
    wahl = iter([("Kennwort zum Öffnen setzen / ändern …", True)])
    monkeypatch.setattr(QInputDialog, "getItem", staticmethod(lambda *a, **k: next(wahl)))
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("geheim", True)))
    w.befehle.dokumentSchuetzen()
    assert t.meta["kennwort"] == "geheim"
    w.befehle.abschnittsumbruch(None, "NextPage")
    assert " " in t.editor.document().toPlainText() or t.editor.document().blockCount() >= 2
    w.befehle.abschnittsumbruch(None, "EvenPage")             # nicht möglich → nur Hinweis
    assert t.editor.document().blockCount() <= 3
    fertig(w)
