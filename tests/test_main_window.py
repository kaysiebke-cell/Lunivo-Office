import os

import docx
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor

from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ui.main_window import MainWindow


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
    monkeypatch.setattr("lunivo_writer.ui.main_window.QFileDialog.getSaveFileName", lambda *a, **k: (target, ""))
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
    monkeypatch.setattr("lunivo_writer.ui.main_window.QFileDialog.getSaveFileName", lambda *a, **k: (out, ""))
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
    from lunivo_writer.services import recovery
    monkeypatch.setattr(recovery, "recovery_dir", lambda: str(tmp_path / "rec") if os.makedirs(tmp_path / "rec", exist_ok=True) is None else "")
    w = win(tmp_path); w.new_document(); w.current_editor().insertPlainText("Rettungstext")
    w.autosave_now()
    ent = recovery.pending()
    assert len(ent) == 1
    from lunivo_writer.services import file_service as formats
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
        import lunivo_writer.app
        from lunivo_writer.ui.main_window import MainWindow
        w = MainWindow(); w.new_document()
        bad = [m for m in sys.modules if m.startswith(("PySide6.QtWebEngine", "PySide6.QtWebKit", "PySide6.QtWebChannel",
               "PySide6.QtWebView", "http.server", "socketserver", "flask", "gi.repository.WebKit"))]
        print("BAD", bad)
    """)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")))
    assert "BAD []" in r.stdout, r.stdout + r.stderr


def test_quelltext_ohne_web_oberflaeche():
    """Im neuen Programm kommt keine HTML/JS-Oberfläche vor."""
    import pathlib, re
    wurzel = pathlib.Path(__file__).resolve().parent.parent / "src" / "lunivo_writer"
    muster = re.compile(r"QtWebEngine|QtWebKit|QWebEngineView|WebKit2|http\.server|SimpleHTTPRequestHandler")
    treffer = [str(p) for p in wurzel.rglob("*.py") if muster.search(p.read_text(encoding="utf-8"))]
    assert treffer == []
    assert not list(wurzel.rglob("*.html")) and not list(wurzel.rglob("*.js"))


# Das Einfügen aus der Zwischenablage nimmt Inhalte aus fremden Programmen an (die liefern ihre Formatierung so); das ist keine
# Datei und kein Format von Lunivo. Für alles, was Lunivo selbst anlegt oder speichert, gilt: kein HTML. Neue Einträge: nicht vorgesehen.
HTML_NOCH_ERLAUBT = {"ui/document/base.py", "ui/document/document_editor.py"}


def test_kein_html_im_projekt():
    """Lunivo ist eine native Qt-Anwendung: HTML, JavaScript und CSS kommen weder als Dateien noch im Quelltext vor,
    auch nicht als Datei-, Daten- oder Zwischenformat (Textbausteine, Hilfe, Berichte, Werkzeuge)."""
    import pathlib, re
    wurzel = pathlib.Path(__file__).resolve().parent.parent
    ohne = {".venv", ".git", ".pytest_cache", "__pycache__", "node_modules"}
    projektdateien = [p for p in wurzel.rglob("*") if p.is_file() and not (ohne & set(p.relative_to(wurzel).parts))]
    web = [str(p.relative_to(wurzel)) for p in projektdateien if p.suffix.lower() in {".html", ".htm", ".js", ".mjs", ".css", ".ts"}]
    assert web == [], "Web-Dateien im Projekt: " + ", ".join(web)
    code = re.compile(r"toHtml|setHtml|insertHtml|fromHtml|hasHtml|\.html\(\)|import html\b|<html|<body|<img |<table|<br>|"
                      r"</?(?:b|i|s|u|br|p|h[1-6]|code|sup|sub|a|span|div|table|tr|td|ul|li|font|em|strong)(?:\s[^>]*)?/?>|"
                      r"[\"']\.html?[\"']|\"html\"|QtWebEngine|QtWebKit|QWebEngine|WebKit2|http\.server|SimpleHTTPRequestHandler")
    treffer = []
    for p in projektdateien:
        rel = p.relative_to(wurzel).as_posix()
        if p.suffix not in {".py", ".json", ".sh", ".toml"} or rel.startswith(("tests/", "src/lunivo_writer/resources/daten/")):
            continue
        if rel.removeprefix("src/lunivo_writer/") in HTML_NOCH_ERLAUBT or rel == "werkzeug/funktionspruefung.py":
            continue
        for n, z in enumerate(p.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if code.search(z):
                treffer.append(f"{rel}:{n}: {z.strip()[:90]}")
    assert treffer == [], "HTML im Quelltext:\n" + "\n".join(treffer)


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


def test_zoom_skaliert_ansicht_nicht_dokument(app, tmp_path):
    w = win(tmp_path)
    w.new_document()
    w.resize(1200, 800); w.show()
    e = w.current_editor()
    e.insertPlainText("Hallo Welt " * 30)
    breite, hoehe = e.width(), e.document().size().height()
    schrift = e.document().defaultFont().pointSizeF()
    e.set_zoom(2.0)
    assert abs(e.width() - 2 * breite) <= 2
    assert e.document().size().height() > 1.8 * hoehe
    assert e.document().defaultFont().pointSizeF() == schrift      # Dokument bleibt unverändert
    assert w.lbl_zoom.text() == "200 %" and w.zoom_regler.value() == 200
    w.befehle.normal()
    assert e.zoom == 1.0 and e.width() == breite
    w.befehle.zoomBreite()
    t = w.current_tab()
    assert abs(e.width() - (t.viewport().width() - 24)) <= 4
    w.befehle.zoomSeite()
    assert e.height() >= 0 and e.zoom <= 1.5
    e.document().setModified(False)
    w.close()


def test_lineale_zeigen_und_raender_ziehen(app, tmp_path):
    w = win(tmp_path)
    w.new_document()
    w.show()
    t = w.current_tab()
    assert not t.lineal_h.isVisibleTo(t)
    w.befehle.linealZeigen(); w.befehle.linealHochZeigen()
    assert t.lineal_h.isVisibleTo(t.widget()) and t.lineal_v.isVisibleTo(t.widget())
    assert w.befehle.an_linealZeigen() and w.befehle.an_linealHochZeigen()
    assert t.lineal_h.width() == t.viewport().width() and t.lineal_v.height() == t.viewport().height()    # fest am Fensterrand
    assert t.lineal_h.geometry().bottom() < t.viewport().geometry().top()                               # im Rand des Viewports
    t.lineal_h.randGeaendert.emit("links", 20.0)
    t.lineal_v.randGeaendert.emit("oben", 15.0)
    assert t.page.margin_left_mm == 20.0 and t.page.margin_top_mm == 15.0
    assert t.editor.document().isModified()
    t.editor.insertPlainText("Absatz")
    t.lineal_h.einzugGeaendert.emit(10.0, 5.0, 8.0)
    bf = t.editor.textCursor().blockFormat()
    assert abs(bf.leftMargin() / 3.7795 - 10) < 0.2 and abs(bf.textIndent() / 3.7795 - 8) < 0.2
    x_vorher = t.lineal_h._marken()["links"]
    t.editor.set_zoom(2.0)
    assert t.lineal_h.width() == t.viewport().width() and t.lineal_h._marken()["links"] > x_vorher      # die Marken folgen dem Zoom
    t.editor.document().setModified(False)
    w.close()


def test_ansichten_web_zwei_seiten_gliederung(app, tmp_path):
    from PySide6.QtGui import QTextCursor
    w = win(tmp_path)
    w.new_document(); w.resize(1200, 800); w.show()
    t = w.current_tab(); e = t.editor
    e.insertPlainText("Kapitel\nText A\nText B")
    c = QTextCursor(e.document()); e.setTextCursor(c); e.apply_style("Überschrift 1")
    # Weblayout
    w.befehle.w_setzeLayout(None, "web")
    assert e.web and e.width() <= t.viewport().width()
    # Zwei Seiten
    w.befehle.w_setzeLayout(None, "doppelt")
    assert t.widget() is not t._holder and t.widget().seiten >= 1
    w.befehle.w_setzeLayout(None, "blatt")
    assert t.widget() is t._holder and not e.web
    assert abs(e.width() - e.page.width_mm * 96 / 25.4) <= 2
    # Gliederung
    w.befehle.gliederung()
    bloecke = [b.isVisible() for b in _bloecke(e.document())]
    assert bloecke == [True, False, False]
    e.set_gliederung(False)
    assert all(b.isVisible() for b in _bloecke(e.document()))
    e.document().setModified(False)
    w.close()


def _bloecke(doc):
    b = doc.firstBlock()
    while b.isValid():
        yield b
        b = b.next()


def test_neues_fenster_und_anordnen(app, tmp_path):
    w = win(tmp_path)
    w.new_document()
    w.current_editor().insertPlainText("Inhalt")
    ziel = str(tmp_path / "f.docx")
    w.show()
    assert w._write(w.current_tab(), ziel)
    w.current_tab().set_path(ziel)
    w2 = w.neues_fenster()
    assert w2 is not None and w2.current_tab().editor.toPlainText() == "Inhalt"
    assert len(MainWindow.alle_fenster()) >= 2
    w.fenster_anordnen("nebeneinander")
    assert abs(w.width() - w2.width()) <= 10                 # Mindestbreite der Fenster hängt von Schrift und Bildschirm ab
    menue = w.fensterliste_menue()
    titel = [a.text() for a in menue.actions()]
    assert any("f.docx" in t for t in titel)
    for f in (w2, w):
        f.current_editor().document().setModified(False); f.close()


def test_absatzdialog_und_objekte_waehlen(app, tmp_path):
    from lunivo_writer.ui.baukasten.absatz_dialog import AbsatzDialog
    d = AbsatzDialog(None, {"ausr": "mitte", "einzug": 5, "erste": -8, "vor": 6, "nach": 12, "zeilen": 1.5, "umbruch": True, "tabs": [(30.0, "rechts")]})
    assert d.ausr.currentData() == "mitte" and d.umbruch.isChecked() and d.sonder.currentData() == "haengend"
    d.links.setValue(12); d.sonder.setCurrentIndex(1); d.zeilen_art.setCurrentIndex(2)
    g = AbsatzDialog(None, {"zeilen_art": "genau", "zeilen_pt": 14})
    assert g.werte()["zeilen_art"] == "genau" and g.werte()["zeilen_pt"] == 14
    w = d.werte()
    assert abs(w["einzug"] - 12) < 1e-6 and abs(w["erste"] - 8) < 1e-6 and w["zeilen"] == 2.0 and w["tabs"] == [(30.0, "rechts")]
    v = AbsatzDialog(None, {"vor": 3}, umfang="vorlage")
    assert v.reiter.count() == 2 and abs(v.werte()["vor"] - 3) < 1e-6          # in der Vorlage dasselbe Fenster mit beiden Reitern
    w = win(tmp_path)
    w.new_document()
    e = w.current_editor()
    e.insertPlainText("vorher ")
    from PySide6.QtGui import QImage, QTextImageFormat
    img = QImage(20, 20, QImage.Format_RGB32); img.fill(0xff0000)
    e.document().addResource(3, "bild1", img)       # QTextDocument.ImageResource
    f = QTextImageFormat(); f.setName("bild1"); f.setWidth(20); f.setHeight(20)
    e.textCursor().insertImage(f)
    e.insertPlainText(" nachher")
    c = e.textCursor(); c.setPosition(0); e.setTextCursor(c)
    w.befehle.objekteWaehlen()
    assert e.textCursor().selectedText() == "￼"
    e.document().setModified(False); w.close()


def test_kommentar_note_verfolgen_ueber_befehle(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QInputDialog
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.insertPlainText("Ein Satz zum Prüfen.")
    monkeypatch.setattr(QInputDialog, "getMultiLineText", staticmethod(lambda *a, **k: ("Mein Text", True)))      # für die Fußnote weiter unten
    e.select_range(0, 3)
    w.befehle.kommentar()                                     # öffnet das Feld „Kommentare“ links mit dem Eingabefeld
    assert w.navigation.isVisible() and not w.navigation.neu_feld.isHidden()
    w.navigation.neu_text.setPlainText("Mein Text"); w.navigation.neu_ok.click()
    assert len(e.kommentare) == 1 and w.navigation.anzahl("kommentare") == 1
    c = e.textCursor(); c.setPosition(e.document().characterCount() - 1); e.setTextCursor(c)
    w.befehle.fussnote()
    w.noten_feld.eingabe.setPlainText("Mein Text")                              # unten im Notenfeld getippt
    w.navigation.aktualisieren()
    assert len(e.noten["f"]) == 1 and w.navigation.anzahl("noten") == 1
    assert not w.befehle.an_verfolgen()
    w.befehle.verfolgen()
    assert w.befehle.an_verfolgen()
    ziel = str(tmp_path / "k.docx")
    assert w._write(w.current_tab(), ziel)
    w.current_tab().editor.document().setModified(False)
    w2 = win(tmp_path / "x") if (tmp_path / "x").mkdir() is None else None
    w2.open_path(ziel)
    e2 = w2.current_editor()
    assert list(e2.kommentare.values())[0]["text"] == "Mein Text" and list(e2.noten["f"].values())[0] == "Mein Text"
    for f in (w, w2):
        f.current_editor().document().setModified(False); f.close()


def test_oberflaeche_wechseln_register_anpassen_symbole_tauschen(app, tmp_path):
    import json
    from lunivo_writer.ui.widgets import icons
    from lunivo_writer.ui.ribbon.toolbars import Symbolleisten
    from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand
    w = win(tmp_path)
    w.new_document(); w.resize(1380, 860); w.show()
    assert isinstance(w.band, RegisterBand)
    assert [w.band.reiter.tabText(i) for i in range(8)][:3] == ["Datei", "Start", "Einfügen"]
    # Reiter ausblenden und umordnen
    w.settings.set("ui/register_plan", json.dumps({"reihenfolge": ["Datei", "Ansicht", "Start"], "versteckt": ["Verweise", "KI"]}))
    w.neu_bauen_band()
    namen = [w.band.reiter.tabText(i) for i in range(w.band.reiter.count()) if w.band.reiter.isTabVisible(i)]
    assert namen[:2] == ["Ansicht", "Start"] and "Datei" not in namen and "Verweise" not in namen and "KI" not in namen
    assert w.band.reiter.tabText(w.band.reiter.currentIndex()) == "Start"
    # Schnellzugriff
    w.settings.set("ui/schnellzugriff", json.dumps(["speichern", "neu"]))
    w.neu_bauen_band()
    assert w.band.schnell.count() == 2
    # Symbolleisten-Oberfläche
    w.oberflaeche_aendern("symbolleisten", True)
    assert isinstance(w.band, Symbolleisten) and w.menuBar().isVisible()
    assert w.sidebar.isVisible() and w.band.felder["font"] is not None
    w.befehle.fett()
    w.current_editor().insertPlainText("x")
    w.band.aktualisieren(True)
    w.oberflaeche_aendern("register", False)
    # Symbol austauschen und zurücksetzen
    orig = icons.pfade_original()["fett"] if "fett" in icons.pfade_original() else None
    name = next(iter(icons.pfade_original()))
    icons.uebersteuern({name: "heart"})
    assert icons.pfade()[name] == icons.katalog()["heart"] and icons.pfade_original()[name] != icons.katalog()["heart"]
    icons.uebersteuern({})
    assert icons.pfade()[name] == icons.pfade_original()[name]
    w.current_editor().document().setModified(False); w.close()


def test_linke_seitenleiste_suchen_kommentare_ueberschriften(app, tmp_path, monkeypatch):
    """Die Leiste links öffnet die Felder; Suchen/Ersetzen, Kommentare (sortieren, filtern, gelöst, neu) und Überschriften (Menü) funktionieren."""
    from PySide6.QtGui import QTextCursor
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.setPlainText("Kapitel Eins\nText hier und mehr Text zum Suchen.\nKapitel Zwei\nNoch Text.")
    for n in (0, 2):
        c = QTextCursor(e.document().findBlockByNumber(n)); bf = c.blockFormat(); bf.setHeadingLevel(1); c.setBlockFormat(bf)
    # Leiste links: Klick öffnet, zweiter Klick schließt
    assert not w.navigation.isVisible()
    w._links_klick("kommentare")
    assert w.navigation.isVisible() and w.navigation.aktuelle_seite == "kommentare" and w._links["kommentare"].isChecked()
    w._links_klick("kommentare")
    assert not w.navigation.isVisible() and not w._links["kommentare"].isChecked()
    # Suchen und ersetzen
    nav = w.navigation
    nav.suche_zeigen("Text")
    assert nav.aktuelle_seite == "suche" and nav.treffer.text().endswith("von 3") or "3" in nav.treffer.text()
    assert len(e._such_bereiche) == 3                    # alle Treffer sind im Text farbig hinterlegt
    nav.ersatzfeld.setText("Wort")
    nav._ersetzen_alle()
    assert "Text" not in e.toPlainText() and e.toPlainText().count("Wort") == 3
    nav.suchfeld.setText("gibtesnicht")
    assert nav.treffer.text() == "Keine Suchergebnisse" and not e._such_bereiche
    nav.suchfeld.setText("Wort"); assert len(e._such_bereiche) == 3
    nav.hide(); assert not e._such_bereiche               # mit dem Feld verschwindet die Markierung
    nav.show()
    # Kommentare: zwei anlegen, sortieren, als gelöst markieren, filtern
    e.select_range(0, 7); e.kommentar_neu("Erster"); e.select_range(13, 17); e.kommentar_neu("Zweiter")
    nav.zeige_tab("kommentare")
    assert nav.anzahl("kommentare") == 2
    texte = lambda: [e.kommentare[k.kid]["text"] for k in nav._karten]              # noqa: E731
    nav._sortieren("oben"); assert texte() == ["Erster", "Zweiter"]
    nav._sortieren("unten"); assert texte() == ["Zweiter", "Erster"]
    kid = int(nav._karten[0].kid)
    e.kommentar_geloest(kid, True); nav.aktualisieren()
    nav._anzeigen("offen"); assert nav.anzahl("kommentare") == 1
    nav._anzeigen("geloest"); assert nav.anzahl("kommentare") == 1
    nav._anzeigen("alle"); assert nav.anzahl("kommentare") == 2
    # Überschriften: Menü
    nav.zeige_tab("ueberschriften")
    assert nav.baum.topLevelItemCount() == 2
    nav.baum.collapseAll(); nav._ebene(2)
    nav._schrift("gross"); assert nav.baum.font().pointSizeF() == 13.0
    nav._umbrechen(False); assert not nav.baum.wordWrap()


def test_kommentar_nachbearbeiten_und_schriftgroesse(app, tmp_path):
    """Ein Kommentar lässt sich in seiner Karte bearbeiten (Blase und Karte zeigen den neuen Text); die Schriftgröße gilt für Karten und Blasen."""
    from lunivo_writer.editor import sprechblasen as SB
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.setPlainText("Bewerbung als Änderungsschneider,")
    e.select_range(14, 32); kid = e.kommentar_neu("alter Text")
    nav = w.navigation
    nav.zeige_tab("kommentare"); nav.show()
    assert nav.anzahl("kommentare") == 1
    e.kommentar_bearbeiten(kid)                                   # Doppelklick auf die Blase
    assert nav._bearbeite == kid and hasattr(nav._karten[0], "eingabe")
    nav._karten[0].eingabe.setPlainText("neuer Text")
    nav._bearbeiten_speichern(kid, "neuer Text")
    assert e.kommentare[kid]["text"] == "neuer Text" and nav._bearbeite is None and not hasattr(nav._karten[0], "eingabe")
    assert any(bl.text == "neuer Text" for bl, _r, _y in e.blasen_layout(300))                # die Blase am Rand zeigt ihn
    # Schriftgröße: groß macht die Blasen höher
    vorher = SB.messen(next(iter(e.blasen_layout(300)))[0], 280, __import__("PySide6.QtGui", fromlist=["QFont"]).QFont("Sans", 10))
    nav._kommentar_schrift("gross")
    assert w.settings.get("kommentare/schrift") == "gross" and SB.blasen_px("gross") > SB.blasen_px("mittel") > SB.blasen_px("klein")
    assert SB.karten_pt("gross") > SB.karten_pt("klein") and vorher > 0


def test_geoeffnetes_dokument_zeigt_kommentar_blasen_sofort(app, tmp_path):
    """Nach Speichern und Wieder-Öffnen stehen die Kommentare nicht nur links, sondern auch als Blasen am Seitenrand — ohne dass erst etwas geändert werden muss."""
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.setPlainText("Bewerbung als Änderungsschneider,\nText hier.")
    e.select_range(14, 32); e.kommentar_neu("bleibt erhalten")
    pfad = str(tmp_path / "k.docx")
    assert w._write(w.current_tab(), pfad)
    w.open_path(pfad)
    ed = w.current_editor()
    assert len(ed.kommentare) == 1 and ed._blasen_flaeche is not None and ed._blasen_flaeche.isVisible()
    assert len(ed.blasen_layout(300)) == 1


def test_aenderungen_und_noten_im_feld_links_sind_echte_funktionen(app, tmp_path, monkeypatch):
    """Änderungen: verfolgen ein/aus, Karten mit Zeigen/Annehmen/Ablehnen, alle auf einmal. Noten: Fußnote/Endnote anlegen, Karten mit Zeigen/Bearbeiten/Löschen."""
    from PySide6.QtWidgets import QInputDialog
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.setPlainText("Ein Satz zum Prüfen.")
    nav = w.navigation
    monkeypatch.setattr(QInputDialog, "getMultiLineText", staticmethod(lambda *a, **k: ("Notiztext", True)))
    # --- Änderungen
    nav.zeige_tab("aenderungen"); nav.show()
    assert nav.anzahl("aenderungen") == 0 and not nav._aend_leer.isHidden()
    nav.verfolgen_knopf.click()                                                  # schaltet das Verfolgen ein
    assert w.befehle.an_verfolgen() and nav.verfolgen_knopf.text() == "an"
    c = e.textCursor(); c.setPosition(len("Ein Satz zum Prüfen.")); e.setTextCursor(c)
    e.insertPlainText(" Neu dazu.")
    e.select_range(0, 3)
    e.insertPlainText("Das")                                                      # zweite verfolgte Änderung
    nav.aktualisieren()
    assert nav.anzahl("aenderungen") >= 1
    erste = nav._aend_karten[0]
    anz = nav.anzahl("aenderungen")
    [b for b in erste.findChildren(type(nav.verfolgen_knopf)) if b.text() == "Annehmen"][0].click()      # eine Änderung annehmen
    assert nav.anzahl("aenderungen") == anz - 1
    nav._befehl("aenderungenUebernehmen")                                          # alle annehmen
    assert nav.anzahl("aenderungen") == 0
    # --- Noten
    nav.zeige_tab("noten")
    assert nav.anzahl("noten") == 0 and not nav._noten_leer.isHidden()
    c = e.textCursor(); c.setPosition(3); e.setTextCursor(c)
    nav._befehl("fussnote")
    assert nav.anzahl("noten") == 1 and len(e.noten["f"]) == 1
    nav._befehl("endnote")
    assert nav.anzahl("noten") == 2
    karte = nav._noten_karten[0]
    [b for b in karte.findChildren(type(nav.verfolgen_knopf)) if b.text() == "Löschen"][0].click()
    assert nav.anzahl("noten") == 1


def test_tastenkuerzel_fuer_fussnote_und_endnote(app, tmp_path, monkeypatch):
    """Strg+Alt+F setzt eine Fußnote, Strg+Alt+D eine Endnote (wie in der Hilfe beschrieben)."""
    from PySide6.QtWidgets import QInputDialog
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.insertPlainText("Ein Satz mit Quelle.")
    monkeypatch.setattr(QInputDialog, "getMultiLineText", staticmethod(lambda *a, **k: ("Beleg", True)))
    kuerzel = {sc.key().toString(): sc for sc in w._kuerzel}
    kuerzel["Ctrl+Alt+F"].activated.emit()
    kuerzel["Ctrl+Alt+D"].activated.emit()
    assert len(e.noten["f"]) == 1 and len(e.noten["e"]) == 1


def test_notenfeld_unten_schreibt_in_dieselbe_note_wie_das_feld_links(app, tmp_path):
    """Strg+Alt+F öffnet unten das Notenfeld mit dem Cursor darin; Tippen, Klick aufs Zeichen und das Feld links arbeiten an derselben Note."""
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    w = win(tmp_path)
    w.new_document(); w.show()
    e = w.current_editor()
    e.insertPlainText("Ein Satz mit Quelle.")
    w.befehle.fussnote()
    assert w.noten_feld.isVisible()
    assert w.noten_feld.titel.text() == "Fußnote 1"
    w.noten_feld.eingabe.setPlainText("Müller 2025, S. 4")                          # getippt: steht sofort in der Note
    assert list(e.noten["f"].values()) == ["Müller 2025, S. 4"]
    w.navigation.aktualisieren()
    assert w.navigation.anzahl("noten") == 1
    QTest.keyClick(w.noten_feld.eingabe, Qt.Key_Escape)                           # Esc: Feld zu, Text bleibt
    assert not w.noten_feld.isVisible() and list(e.noten["f"].values()) == ["Müller 2025, S. 4"]
    nid = next(iter(e.noten["f"]))
    e.noteAngeklickt.emit("f", nid)                                                 # Klick auf das Zeichen im Text
    assert w.noten_feld.isVisible() and w.noten_feld.eingabe.toPlainText() == "Müller 2025, S. 4"
    w.noten_feld.zumachen()
    w.befehle.note_bearbeiten("f", nid)                                            # „Bearbeiten“ im Feld links: dasselbe Feld
    assert w.noten_feld.isVisible()
    w.befehle.endnote()
    assert w.noten_feld.titel.text() == "Endnote i"
