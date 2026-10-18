import os

from PySide6.QtCore import QEventLoop, QSettings, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest

from native_qt.storage.settings import Settings
from native_qt.windows.main_window import MainWindow


def win(tmp_path, monkeypatch):
    from native_qt.storage import gelernt
    monkeypatch.setattr(gelernt, "data_dir", lambda: str(tmp_path))
    from native_qt.services import ki_dienst
    monkeypatch.setattr(ki_dienst, "data_dir", lambda: str(tmp_path))
    from native_qt.storage import recovery
    monkeypatch.setattr(recovery, "recovery_dir", lambda: str(tmp_path))
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document()
    return w


def warte(sig_obj, timeout=8000):
    loop = QEventLoop()
    sig_obj.connect(lambda *_: loop.quit())
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()


def test_pruefen_findet_und_aendert(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    e = w.current_editor()
    e.setPlainText("Wir hat keine Zahlung erhalten.")
    w.assistant.pruefen()
    warte(w.assistant.fundeGeaendert)
    funde = w.assistant.funde
    assert any(f["neu"] == "Wir haben" for f in funde), funde
    # Wellenlinien stehen im Editor
    assert len(e.extraSelections()) == len(funde)
    f = next(f for f in funde if f["neu"] == "Wir haben")
    assert w.assistant.aendern(f)
    assert e.toPlainText().startswith("Wir haben keine")


def test_lassen_blendet_aus_und_lernt_ruhe(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    e = w.current_editor(); e.setPlainText("Das Wort steht steht doppelt.")
    w.assistant.pruefen(); warte(w.assistant.fundeGeaendert)
    f = w.assistant.funde[0]
    w.assistant.lassen(f)
    assert f not in w.assistant.funde and all(x["grund"] != f["grund"] for x in w.assistant.funde)


def test_autokorrektur_beim_tippen(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    e = w.current_editor(); e.setFocus()
    QTest.keyClicks(e, 'Er sagte "ja"... am montag ')
    assert e.toPlainText() == "Er sagte „ja“… am Montag " or e.toPlainText().startswith("Er sagte „ja“"), e.toPlainText()
    assert "…" in e.toPlainText() and "Montag" in e.toPlainText()


def test_autokorr_aus(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    w.assistant.setze("autokorr", False)
    e = w.current_editor(); e.setFocus()
    QTest.keyClicks(e, "Ende... ")
    assert e.toPlainText() == "Ende... "


def test_vorhersage_mit_thema(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    w.assistant.setze_thema("Amt")
    assert w.assistant.vorschlaege("wid")[0] == "widerspruch"
    assert w.assistant.vorschlaege("bes")[0] == "bescheid"
    w.assistant.setze("vorhersage", False)
    assert w.assistant.vorschlaege("wid") == []


def test_band_ist_das_alte_register(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    sichtbar = [w.band.reiter.tabText(i) for i in range(w.band.reiter.count()) if w.band.reiter.isTabVisible(i)]
    assert sichtbar == ["Datei", "Start", "Einfügen", "Seitenlayout", "Verweise", "Überprüfen", "KI", "Ansicht"]
    # Kontext-Register erscheinen nur bei Bedarf
    assert not w.band.reiter.isTabVisible(w.band.kontext_index["tabelle"])
    e0 = w.current_editor(); e0.insert_table(2, 2); w._sync_format()
    assert w.band.reiter.isTabVisible(w.band.kontext_index["tabelle"])
    # Nicht Umgesetztes ist sichtbar, aber ausgegraut — keine Attrappen
    ausgegraut = [k for k, _n, _b in w.band.knoepfe if k.property("fehlt")]
    assert ausgegraut and all(not k.isEnabled() for k in ausgegraut)
    # Fett aus dem Band wirkt wirklich
    e = w.current_editor(); e.setPlainText("x"); e.selectAll()
    w.befehle.fett()
    assert e.textCursor().charFormat().fontWeight() >= 600


def test_menue_tafel_listet_datei_punkte(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    w.show_main_menu()
    namen = [b.text() for b in w._tafel.findChildren(type(w.start.list.parent()) if False else __import__("PySide6.QtWidgets", fromlist=["x"]).QPushButton)]
    assert any(n.startswith("Neu") for n in namen) and any(n.startswith("Optionen") for n in namen)
    w._tafel.close()


def test_tabellentools_wirken(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    e = w.current_editor(); e.insert_table(2, 2)
    t = e.textCursor().currentTable()
    assert (t.rows(), t.columns()) == (2, 2)
    w.befehle.tabelleZeileUnten(); assert t.rows() == 3
    w.befehle.tabelleSpalteRechts(); assert t.columns() == 3
    w.befehle.tabelleZeileLoeschen(); assert t.rows() == 2
    e.setTextCursor(t.cellAt(0, 0).firstCursorPosition())
    w.befehle.tabelleRahmen(); assert t.format().border() == 0


def test_seitenleiste_bereiche(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    assert not hasattr(w.sidebar, "bereiche")          # keine Reiterknöpfe über der Schreibhilfe
    assert [b.text() for b in w.sidebar.chips.values()] == ["We", "Vo", "Ko"]
    assert all(b.toolTip() for b in w.sidebar.chips.values())
    w.sidebar.zeige_bereich(1)
    assert w.sidebar.stapel.currentIndex() == 1 and w.sidebar._seite_sh.widget() is not None


def test_ki_korrektur_ende_zu_ende(app, tmp_path, monkeypatch):
    """Knopf → (gefälschter) Ollama-Server → Text korrigiert, Formatierung bleibt, Strg+Z macht es rückgängig."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from PySide6.QtGui import QFont, QTextCharFormat
    from native_qt.services import ki as K

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
            body = json.dumps({"message": {"content": "Wir haben keine Zahlung erhalten."}}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(K, "OLLAMA_URL", f"http://127.0.0.1:{srv.server_address[1]}")
    try:
        w = win(tmp_path, monkeypatch)
        w.ki.konfig.d["modell"] = "ollama:test"
        e = w.current_editor()
        e.setPlainText("Wir hat keine Zahlung erhalten.")
        c = QTextCursor(e.document()); c.setPosition(len("Wir hat keine ")); c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        f = QTextCharFormat(); f.setFontWeight(QFont.Bold); c.mergeCharFormat(f)
        e.document().setModified(False)
        w.ki.korrigieren()
        warte(w.ki.laeuft, 8000); warte(w.ki.laeuft, 8000) if e.toPlainText().startswith("Wir hat") else None
        assert e.toPlainText() == "Wir haben keine Zahlung erhalten."
        # das fette „keine Zahlung erhalten." ist fett geblieben
        c2 = QTextCursor(e.document()); c2.setPosition(len("Wir haben keine "))
        c2.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        assert c2.charFormat().fontWeight() >= 600
        e.undo()
        assert e.toPlainText() == "Wir hat keine Zahlung erhalten."
        e.document().setModified(False)
    finally:
        srv.shutdown()


def test_ki_ohne_schluessel_oeffnet_nichts_nach_aussen(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    w.ki.konfig.d["modell"] = "claude-opus-5"; w.ki.konfig.d["apiKey"] = ""
    aufgerufen = []
    monkeypatch.setattr(w, "show_options", lambda seite=None: aufgerufen.append(seite))
    w.current_editor().setPlainText("Text")
    w.ki.korrigieren()
    assert aufgerufen == ["ki"] and not w.sidebar.ki_knoepfe[0].isEnabled()


def test_rechtschreib_ignorieren_schalter(app, tmp_path, monkeypatch):
    from native_qt.services import pruefung
    text = "Das Wiederspruch gegen WIEDERSPRUCH und kaysiebke-cell/wiederspruch."
    an = {f["alt"] for f in pruefung.finde_probleme(text, None, {"rsGrossIgnorieren": True, "rsPfadeIgnorieren": True})}
    aus = {f["alt"] for f in pruefung.finde_probleme(text, None, {"rsGrossIgnorieren": False, "rsPfadeIgnorieren": False})}
    assert "WIEDERSPRUCH" not in an and "WIEDERSPRUCH" in aus
    assert not any("wiederspruch" in a and a != "Wiederspruch" for a in an) and "wiederspruch" in aus


def test_rechtsklick_menue_vorschlaege_und_ignorieren(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMenu
    w = win(tmp_path, monkeypatch)
    e = w.current_editor(); e.setPlainText("Das ist vieleicht gut.")
    w.assistant.pruefen(); warte(w.assistant.fundeGeaendert)
    pos = e.toPlainText().index("vieleicht") + 3
    m = QMenu()
    w.assistant.erweitere_menue(m, pos)
    texte = [a.text() for a in m.actions() if a.text()]
    assert "vielleicht" in texte and "Einmal ignorieren" in texte and "Alle ignorieren" in texte
    # Vorschlag einsetzen
    next(a for a in m.actions() if a.text() == "vielleicht").trigger()
    assert "vielleicht" in e.toPlainText()
    # unbekanntes Wort ohne Fund: Wörterbuch + Ignorieren
    e.setPlainText("Das ist Zxqvbnk hier."); w.assistant.pruefen(); warte(w.assistant.fundeGeaendert)
    m2 = QMenu(); w.assistant.erweitere_menue(m2, e.toPlainText().index("Zxqvbnk") + 2)
    assert "Zum Wörterbuch hinzufügen" in [a.text() for a in m2.actions()]
    n = w.assistant.ignorierte_wieder_pruefen()
    assert n >= 0
