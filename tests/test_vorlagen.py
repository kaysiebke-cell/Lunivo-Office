import pypdf
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from lunivo_writer.editor import vorlagen
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.editor.pagination import export_pdf

BENUTZER = {"name": "Ann Muster", "strasse": "Weg 1", "plz_ort": "12345 Stadt", "ort": "Stadt", "mail": "ann@example.org"}


def neu():
    e = DocumentEditor(); e.zusatz_binden({}); return e


def test_alle_zehn_geruest_bauen_sich_auf(app):
    liste = vorlagen.muster()
    assert len(liste) == 10
    for m in liste:
        e = neu()
        vorlagen.aufbauen(e, m["zeilen"], BENUTZER, "1. Januar 2026")
        t = e.toPlainText()
        assert t.strip() and "@" not in t.replace("@example", "")
    brief = next(m for m in liste if m["id"] == "brief")
    e = neu(); vorlagen.aufbauen(e, brief["zeilen"], BENUTZER, "1. Januar 2026")
    t = e.toPlainText()
    assert t.startswith("Ann Muster\nWeg 1\n") and "Stadt, 1. Januar 2026" in t and t.rstrip().endswith("Ann Muster")
    lb = next(m for m in liste if m["id"] == "lebenslauf")
    e2 = neu(); vorlagen.aufbauen(e2, lb["zeilen"], BENUTZER, "1. Januar 2026")
    assert "E-Mail: ann@example.org" in e2.toPlainText()


def test_luecken_tab_springt_tippen_ersetzt_druck_ohne_luecken(app, tmp_path):
    e = neu()
    e.setPlainText("Hallo «Name», wir treffen uns «wann».")
    c = e.textCursor(); c.setPosition(0); e.setTextCursor(c)
    e.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier, "\t"))
    assert e.textCursor().selectedText() == "«Name»"
    e.insertPlainText("Ann")
    e.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier, "\t"))
    assert e.textCursor().selectedText() == "«wann»"
    e.insertPlainText("morgen")
    assert e.toPlainText() == "Hallo Ann, wir treffen uns morgen."
    e.setPlainText("Rest «offen» bleibt.")
    out = str(tmp_path / "l.pdf")
    export_pdf(out, e.document(), e.page, "t")
    txt = " ".join(pypdf.PdfReader(out).pages[0].extract_text().split())
    assert "«" not in txt and "Rest" in txt and "bleibt" in txt


def test_neu_aus_vorlage_im_fenster(app, tmp_path, monkeypatch):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.settings.set("benutzer/name", "Ann Muster")
    m = vorlagen.muster()[3]                       # Bewerbung
    w.neu_aus_wahl("geruest", m)
    t = w.current_tab()
    assert t.title == "Bewerbung" and "Bewerbung als" in t.editor.toPlainText() and "Ann Muster" in t.editor.toPlainText()
    # eigene Vorlage aus Datei
    from lunivo_writer.services import docx_writer
    ziel = str(tmp_path / "Meine.docx")
    docx_writer.write_docx(ziel, t.editor.document(), t.page, {})
    w.neu_aus_wahl("datei", ziel)
    t2 = w.current_tab()
    assert t2 is not t and t2.title == "Meine" and t2.path is None and "Bewerbung als" in t2.editor.toPlainText()
    for x in w._doc_tabs():
        x.editor.document().setModified(False)
    w.close()


def test_hilfe_dialoge_und_kuerzel(app, tmp_path):
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QKeySequence
    from PySide6.QtWidgets import QTextBrowser
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.dialogs import hilfe_dialoge
    from lunivo_writer.ui import kuerzel
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    d = hilfe_dialoge.handbuch(w)
    text = d.findChild(QTextBrowser).toPlainText()
    assert "Das erste Blatt" in text and "WPS" not in text and "LibreOffice" not in text and "ONLYOFFICE" not in text.upper()
    from PySide6.QtWidgets import QLabel
    assert "F7" in " ".join(x.text() for x in hilfe_dialoge.tastenkuerzel(w).findChildren(QLabel))
    t = " ".join(x.text() for x in hilfe_dialoge.erweiterungen(w).findChildren(QLabel))
    assert "LanguageTool" in t and "Umwandlungsprogramm" in t
    # alle in der Hilfe genannten F-Tasten sind wirklich belegt
    belegt = {sc.key().toString() for sc in w._kuerzel} | {a.shortcut().toString() for a in w.findChildren(__import__("PySide6.QtGui", fromlist=["QAction"]).QAction)}
    for taste in ("F3", "F4", "F5", "F6", "F7", "F8", "F9", "F11"):
        assert taste in belegt, taste
    w.new_document(); w.new_document()
    w.tabs.setCurrentIndex(0)
    w._tab_weiter(1); assert w.tabs.currentIndex() == 1
    for x in w._doc_tabs():
        x.editor.document().setModified(False)
    w.close()
