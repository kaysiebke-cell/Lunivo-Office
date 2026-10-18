import os

import docx
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor

from native_qt.storage.settings import Settings
from native_qt.windows.main_window import MainWindow


def win(tmp_path):
    return MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))


def test_new_edit_save_reopen(app, tmp_path, monkeypatch):
    w = win(tmp_path)
    w.new_document()
    e = w.current_editor()
    e.insertPlainText("Erster Absatz\nZweiter Absatz")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    w.befehle.fett()
    assert e.document().isModified() and "●" in w.tabs.tabText(w.tabs.currentIndex())
    assert e.textCursor().charFormat().fontWeight() >= 600
    target = str(tmp_path / "doc.docx")
    monkeypatch.setattr("native_qt.windows.main_window.QFileDialog.getSaveFileName", lambda *a, **k: (target, ""))
    assert w.save()
    assert not e.document().isModified()
    assert docx.Document(target).paragraphs[0].runs[0].bold
    w2 = win(tmp_path)
    assert w2.open_path(target)
    assert w2.current_editor().toPlainText() == "Erster Absatz\nZweiter Absatz"
    assert target in w2.settings.recent()


def test_pdf_export_and_status(app, tmp_path, monkeypatch):
    w = win(tmp_path); w.new_document()
    w.current_editor().insertPlainText("\n".join(f"Z{i}" for i in range(150)))
    w.current_editor()._recount()
    w._sync_status()
    assert " von 3" in w.lbl_page.text() or " von 2" in w.lbl_page.text()
    out = str(tmp_path / "x.pdf")
    monkeypatch.setattr("native_qt.windows.main_window.QFileDialog.getSaveFileName", lambda *a, **k: (out, ""))
    w.export_pdf_dialog()
    assert os.path.getsize(out) > 500


def test_close_asks_when_modified(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    w = win(tmp_path); w.new_document(); w.current_editor().insertPlainText("x")
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Cancel)
    assert w.close_tab(0) is False and w.tabs.count() == 1
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Discard)
    assert w.close_tab(0) is True and w.tabs.count() == 0


def test_invalid_file_is_reported_not_crashing(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: shown.append(a))
    bad = tmp_path / "kaputt.docx"; bad.write_bytes(b"nope")
    w = win(tmp_path)
    assert w.open_path(str(bad)) is False and shown and w.tabs.count() == 0


def test_autosave_and_recovery(app, tmp_path, monkeypatch):
    from native_qt.storage import recovery
    monkeypatch.setattr(recovery, "recovery_dir", lambda: str(tmp_path / "rec") if os.makedirs(tmp_path / "rec", exist_ok=True) is None else "")
    w = win(tmp_path); w.new_document(); w.current_editor().insertPlainText("Rettungstext")
    w.autosave_now()
    ent = recovery.pending()
    assert len(ent) == 1
    from native_qt.document_io import formats
    assert "Rettungstext" in formats.load(ent[0].docx_path).doc.toPlainText()
    w.current_editor().document().setModified(False); w.close_tab(0)
    assert recovery.pending() == []


def test_no_web_modules_loaded(app):
    """Frischer Prozess: der neue Startpfad lädt weder WebEngine noch WebKit noch einen Webserver."""
    import subprocess, sys, textwrap
    code = textwrap.dedent("""
        import os, sys
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        import native_qt.main
        from native_qt.windows.main_window import MainWindow
        w = MainWindow(); w.new_document()
        bad = [m for m in sys.modules if m.startswith(("PySide6.QtWebEngine", "PySide6.QtWebKit", "PySide6.QtWebChannel",
               "PySide6.QtWebView", "http.server", "socketserver", "flask", "gi.repository.WebKit"))]
        print("BAD", bad)
    """)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert "BAD []" in r.stdout, r.stdout + r.stderr


def test_quelltext_ohne_web_oberflaeche():
    """Im neuen Programm kommt keine HTML/JS-Oberfläche vor."""
    import pathlib, re
    wurzel = pathlib.Path(__file__).resolve().parent.parent / "native_qt"
    muster = re.compile(r"QtWebEngine|QtWebKit|QWebEngineView|WebKit2|http\.server|SimpleHTTPRequestHandler")
    treffer = [str(p) for p in wurzel.rglob("*.py") if muster.search(p.read_text(encoding="utf-8"))]
    assert treffer == []
    assert not list(wurzel.rglob("*.html")) and not list(wurzel.rglob("*.js"))


def test_tastenkuerzel_fett(app, tmp_path):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    w = win(tmp_path); w.new_document(); w.show()
    e = w.current_editor(); e.setPlainText("abc"); e.selectAll(); e.setFocus()
    w.a_bold.trigger()                                   # das Kürzel Strg+B löst genau diese Aktion aus
    assert w.a_bold.shortcut().toString() == "Ctrl+B"
    assert e.textCursor().charFormat().fontWeight() >= 600
    w.a_bold.trigger()
    assert e.textCursor().charFormat().fontWeight() < 600       # zweites Mal schaltet aus
    e.document().setModified(False)
    w.close()


def test_bearbeitung_sperren_und_band_einklappen(app, tmp_path):
    w = win(tmp_path)
    w.new_document()
    w.befehle.bearbeitungSperren()
    assert w.current_editor().isReadOnly()
    w.befehle.bearbeitungSperren()
    assert not w.current_editor().isReadOnly()
    b = w.band
    b.einklappen_umschalten()
    assert b._eingeklappt and not b.stapel.isVisibleTo(b)
    b.einklappen_umschalten()
    assert b.stapel.isVisibleTo(b)
    w.current_editor().document().setModified(False)
    w.close()
