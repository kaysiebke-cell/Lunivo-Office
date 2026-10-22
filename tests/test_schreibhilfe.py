import os

from PySide6.QtCore import QEventLoop, QSettings, QTimer, Qt
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtTest import QTest

from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ui.main_window import MainWindow


def win(tmp_path, monkeypatch):
    from lunivo_writer.services import gelernt
    monkeypatch.setattr(gelernt, "data_dir", lambda: str(tmp_path))
    from lunivo_writer.ai import ai_service as ki_dienst
    monkeypatch.setattr(ki_dienst, "data_dir", lambda: str(tmp_path))
    from lunivo_writer.services import recovery
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
    for _ in range(5):                                    # eine frühere (leere) Meldung nicht für das Ergebnis halten
        warte(w.assistant.fundeGeaendert, 3000)
        if any(f["neu"] == "Wir haben" for f in w.assistant.funde):
            break
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
    assert sichtbar == ["Start", "Einfügen", "Seitenlayout", "Verweise", "Überprüfen", "Schreibhilfe", "Ansicht", "Abschnitt"]   # „Datei“ steht links als ☰ Menü
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
    namen = [b.text() for b in w._tafel.findChildren(__import__("PySide6.QtWidgets", fromlist=["x"]).QPushButton)]
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
    assert w.sidebar.stapel.count() == 2 and w.sidebar._seite_ki.widget() is not None
    w._rechts_klick(1)
    assert w.sidebar.stapel.currentIndex() == 1 and w._rechts[1].isChecked() and not w._rechts[0].isChecked()
    w._rechts_klick(1)
    assert w.sidebar.isHidden() and not w._rechts[1].isChecked()


def test_ki_korrektur_ende_zu_ende(app, tmp_path, monkeypatch):
    """Knopf → (gefälschter) Ollama-Server → Text korrigiert, Formatierung bleibt, Strg+Z macht es rückgängig."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from PySide6.QtGui import QFont, QTextCharFormat
    from lunivo_writer.ai import ki as K

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
    from lunivo_writer.proofing import pruefung
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


def test_text_in_bild_ende_zu_ende(app, tmp_path, monkeypatch):
    """Markierter Text → Anbieter mit „Bilder“ → Bild steht im Dokument an Stelle der Markierung; Strg+Z holt den Text zurück."""
    import base64, json, threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtGui import QColor, QImage
    img = QImage(16, 16, QImage.Format_RGB32); img.fill(QColor("blue"))
    buf = QBuffer(); buf.open(QIODevice.WriteOnly); img.save(buf, "PNG")
    png = base64.b64encode(bytes(buf.data())).decode()

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            body = json.dumps({"data": [{"b64_json": png}]}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    w = win(tmp_path, monkeypatch)
    k = w.ki.konfig
    a = k.anbieter_hinzufuegen("Lokal", f"http://127.0.0.1:{srv.server_port}/v1", "", "bild", ["bilder"])
    k.aufgabe_setzen("bildgenerierung", "eigen:" + a["id"])
    e = w.current_editor()
    e.setPlainText("Ein blauer Würfel")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    w.ki.bild_aus_text()
    warte(w.ki._sig.fertig)
    assert "￼" in e.document().toPlainText() and "Würfel" not in e.document().toPlainText()
    e.undo()
    assert "Ein blauer Würfel" in e.document().toPlainText() or e.document().toPlainText().count("￼") == 0


def test_ki_dialoge(app, tmp_path, monkeypatch):
    from lunivo_writer.ui.dialogs.ki_dialoge import AnbieterDialog, KIKonfigurationDialog, ModellListeDialog
    w = win(tmp_path, monkeypatch)
    k = w.ki.konfig
    d = AnbieterDialog(w, k)
    assert d.url.text().endswith(":11434/v1") and d.tags["text"].isChecked()
    d.name.setText("X"); d.modell.setCurrentText("m"); d.tags["bilder"].setChecked(True)
    d._ok()
    assert k["anbieter"][0]["verwendungFuer"] == ["text", "bilder"]
    kd = KIKonfigurationDialog(w)
    assert list(kd.felder) == ["chatbot", "zusammenfassen", "uebersetzung", "textanalyse", "bildgenerierung"]
    assert kd.felder["bildgenerierung"].count() == 2 and kd.felder["chatbot"].count() == 5
    kd.felder["bildgenerierung"].setCurrentIndex(1); kd._ok()
    assert k["aufgaben"]["bildgenerierung"].startswith("eigen:")
    ModellListeDialog(w, k)._fuellen()


def test_silbenfarben_befehl_und_dialog(app, tmp_path, monkeypatch):
    from lunivo_writer.ui.dialogs.silben_dialog import SilbenDialog
    w = win(tmp_path, monkeypatch)
    e = w.current_editor()
    e.setPlainText("Wanderung und Schmetterling")
    assert w.befehle.hat("silbenfarben") and w.befehle.hat("silbenEinstellen") and not w.befehle.zustand("silbenfarben")
    w.befehle.tun("silbenfarben")
    assert w.befehle.zustand("silbenfarben") and e.document().firstBlock().layout().formats()
    d = SilbenDialog(w)
    d.palette.setCurrentText("Blau / Orange"); d.mindestens.setValue(9); d.absatz.setChecked(False)
    assert w.settings.get("lesehilfe/silben/palette") == "Blau / Orange"
    assert {r.format.foreground().color().name() for r in e.document().firstBlock().layout().formats()} <= {"#1f5fbf", "#d9480f"}
    d.reject()                                                         # Abbrechen stellt den alten Stand wieder her
    assert w.settings.get("lesehilfe/silben/palette") == "Blau / Rot"
    w.befehle.tun("silbenfarben")
    assert not e.document().firstBlock().layout().formats()
    # neue Dokumente übernehmen die Einstellung
    w.settings.set("lesehilfe/silben/an", True)
    w.new_document()
    w.current_editor().setPlainText("Wanderung")
    assert w.current_editor().document().firstBlock().layout().formats()


def test_minisymbolleiste(app, tmp_path, monkeypatch):
    from PySide6.QtCore import QPoint
    w = win(tmp_path, monkeypatch)
    e = w.current_editor()
    e.setPlainText("Ein Text zum Markieren")
    c = e.textCursor(); c.setPosition(3); c.setPosition(7, QTextCursor.KeepAnchor); e.setTextCursor(c)
    w.mini_zeigen(e, QPoint(200, 200))
    assert w._mini.isVisible()
    w._mini.knoepfe["fett"].click()
    assert e.textCursor().charFormat().fontWeight() >= 600 and w._mini.knoepfe["fett"].isChecked()
    w._mini.knoepfe["kursiv"].click(); assert e.textCursor().charFormat().fontItalic()
    c = e.textCursor(); c.clearSelection(); e.setTextCursor(c)                  # Auswahl weg → Leiste verschwindet
    assert not w._mini.isVisible()
    w.mini_zeigen(e, QPoint(200, 200), True)
    assert w._mini.isVisible()                                                     # Rechtsklick: bleibt ohne Auswahl
    w.mini_zeigen(None, None)
    assert not w._mini.isVisible()


def test_live_vorschau(app, tmp_path, monkeypatch):
    from PySide6.QtCore import QEvent
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QApplication, QToolButton
    w = win(tmp_path, monkeypatch)
    e = w.current_editor()
    e.setPlainText("Ein Text zum Probieren")
    e.document().setModified(False)
    c = e.textCursor(); c.setPosition(3); c.setPosition(7, QTextCursor.KeepAnchor); e.setTextCursor(c)
    d = e.document()
    schritte = d.availableUndoSteps()

    def fett(): return QTextCursor(d).charFormat().fontWeight()
    # 1) Formatvorlage über der Galerie überfahren: sichtbar, dann restlos weg (kein Rückgängig-/Wiederholen-Rest, nicht „geändert“)
    knopf = next(b for b in w.band.findChildren(QToolButton) if b.text().endswith("Überschrift 1"))
    QApplication.sendEvent(knopf, QEvent(QEvent.Enter))
    assert d.firstBlock().blockFormat().headingLevel() == 1 and w.vorschau.aktiv
    QApplication.sendEvent(knopf, QEvent(QEvent.Leave))
    assert d.firstBlock().blockFormat().headingLevel() == 0 and not w.vorschau.aktiv
    assert d.availableUndoSteps() == schritte and not d.isModified() and not d.isRedoAvailable()
    # 2) Schriftgröße im Auswahlfeld
    gr = w.band.felder["groesse"]
    idx = gr.findText("24")
    gr.highlighted.emit(idx)
    assert abs(QTextCursor(e.textCursor()).charFormat().fontPointSize() - 24) < 0.1
    gr.hidePopup()
    assert abs(e.textCursor().charFormat().fontPointSize() - 24) > 1 and d.availableUndoSteps() == schritte
    # 3) Farbmenü: Überfahren zeigt, Schließen nimmt zurück, Klick übernimmt wirklich
    m = w.befehle.menue_schriftfarbeKlappe()
    rot = QColor("#c92a2a")
    m.ueberfahren.emit(rot)
    assert e.textCursor().charFormat().foreground().color().name() == "#c92a2a"
    m.aboutToHide.emit()
    assert e.textCursor().charFormat().foreground().color().name() != "#c92a2a"
    m.waehle(rot)
    assert e.textCursor().charFormat().foreground().color().name() == "#c92a2a" and d.isModified()
    # 4) ausgeschaltet: keine Vorschau
    w.settings.set("ui/live_vorschau", False)
    w.vorschau.zeigen(lambda ed: ed.toggle_bold(True))
    assert not w.vorschau.aktiv


def test_ki_einstellungen_schnelle_aktion_und_chat(app, tmp_path, monkeypatch):
    """Ein Fenster „KI-Einstellungen“ (Reiter grau, bis ein Modell da ist), Schnelle KI-Aktion als Assistent, Chat ohne Bandgruppen."""
    from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog, SchnelleAktionDialog
    w = win(tmp_path, monkeypatch)
    k = w.ki.konfig
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: False)
    d = KIEinstellungenDialog(w)
    assert [d.reiter.isTabEnabled(i) for i in range(5)] == [True, False, False, False, False]
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    d2 = KIEinstellungenDialog(w, 1)
    assert d2.reiter.currentIndex() == 1 and all(d2.reiter.isTabEnabled(i) for i in range(5))
    a = SchnelleAktionDialog(w)
    a._vorlage("Kürzer machen", "Kürze den Text.")
    a.r_schnell.setChecked(True); a.ergebnis.setCurrentIndex(1)
    e = k.assistent_hinzufuegen(*a.werte())
    assert e["modus"] == "anhaengen" and e["zugriff"] == "schnell" and k["assistenten"][-1] is e
    w.ki_schnell_zeigen()
    assert len(w.band._ki_schnell_knoepfe) == 1
    # Chat: ohne Modell der Hinweis, mit Modell Verlauf und Eingabe — und keine Bandgruppen darin
    c = w.sidebar.chat
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: False)
    c.zustand()
    assert c.hinweis.isVisibleTo(c) and not c.eingabezeile.isVisibleTo(c)
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    c.zustand()
    assert not c.hinweis.isVisibleTo(c) and c.eingabezeile.isVisibleTo(c)


def test_ki_ergebnisse_und_band(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QToolButton
    from lunivo_writer.ui.dialogs.ki_dialoge import ErgebnisseDialog
    w = win(tmp_path, monkeypatch)
    w.ki.merke_ergebnis("Zusammenfassen", "Kurz gesagt: ...", "langer Text")
    w.ki.merke_ergebnis("Übersetzen", "Hello")
    d = ErgebnisseDialog(w)
    assert d.liste.count() == 2 and d.text.toPlainText() == "Hello" and d.einfuegen.isEnabled()
    d.liste.setCurrentRow(1)
    assert d.text.toPlainText().startswith("Kurz gesagt")
    namen = {k.toolTip() for k in w.band.findChildren(QToolButton)}
    assert {"Alle Ergebnisse anzeigen", "Grammatik & Rechtschreibung"} <= namen
    assert w.befehle.hat("w.kiErgebnisse")


def test_chat_erweiterte_einstellungen(app, tmp_path, monkeypatch):
    """Die erweiterten Einstellungen des Chats stehen in der KI-Konfiguration, wirken auf Anfragen und teilen sich die Modellwahl mit der Zuweisung."""
    import json as _json
    from lunivo_writer.ai import ki as K
    w = win(tmp_path, monkeypatch)
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    k = w.ki.konfig
    c = w.sidebar.chat
    c.s_temp.setValue(7); c.s_top.setValue(9); c.s_laenge.setValue(300); c.stopp.setText("ENDE, ###"); c.direkt.setChecked(True)
    o = k.chat_optionen()
    assert o["temperatur"] == 0.7 and o["topP"] == 0.9 and o["maxLaenge"] == 300 and o["stopp"] == "ENDE, ###" and o["direkt"]
    c.eingabe.setText("a" * 40)
    assert c.tokens.text() == "Tokens: 10"
    # Das Modell des Chats ist die „Chatbot“-Zuweisung — keine zweite Einstellung
    k.anbieter_hinzufuegen("Lokal", "http://localhost:11434/v1", "", "m", ["text"])
    c._modelle_neu()
    c.modell.setCurrentIndex(c.modell.findData(K.EIGEN_MARKE + k["anbieter"][0]["id"]))
    assert k["aufgaben"]["chatbot"] == K.EIGEN_MARKE + k["anbieter"][0]["id"]
    # Die Werte gehen in die Anfrage an einen eigenen Anbieter
    gesehen = {}

    class _R:
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def read(s): return _json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()

    def falsch(url, kopf, body, timeout):
        gesehen.update(body); return _R()
    monkeypatch.setattr(K, "_post", falsch)
    assert w.ki.ki.chat([{"rolle": "mensch", "text": "hi"}])["text"] == "ok"
    assert gesehen["temperature"] == 0.7 and gesehen["top_p"] == 0.9 and gesehen["max_tokens"] == 300 and gesehen["stop"] == ["ENDE", "###"]
    # Andere KI-Aufgaben (Korrektur, Übersetzung …) bleiben bei ihren festen Werten
    gesehen.clear()
    w.ki.ki.zusammenfassen("Text")
    assert "temperature" not in gesehen and "top_p" not in gesehen


def test_mcp_und_websuche_im_chat(app, tmp_path, monkeypatch):
    """Mit verbundenem Modell sind alle Reiter frei; ein MCP-Server liefert Werkzeuge, die Websuche bringt Quellen in die Anweisung."""
    import json as _json
    import pathlib
    import sys as _sys
    from lunivo_writer.ai import ki as K, mcp as M, websuche as W
    from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
    w = win(tmp_path, monkeypatch)
    k = w.ki.konfig
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    d = KIEinstellungenDialog(w, 3)
    assert all(d.reiter.isTabEnabled(i) for i in range(5)) and d.reiter.currentIndex() == 3
    # MCP: Verbindung testen und Werkzeug aufrufen
    befehl = f"{_sys.executable} {pathlib.Path(__file__).parent / 'fake_mcp_server.py'}"
    assert [t["name"] for t in M.pruefen(befehl)] == ["echo"]
    e = k.mcp_speichern(None, "Fake", befehl, True)
    d.mcp.fuellen()
    assert d.mcp.liste.count() == 1
    # Chat mit Werkzeug: erst verlangt das Modell „echo“, dann antwortet es mit dem Ergebnis
    k.anbieter_hinzufuegen("Lokal", "http://localhost:11434/v1", "", "m", ["text"])
    k.setze("modell", K.EIGEN_MARKE + k["anbieter"][0]["id"])
    zuege = []

    class _R:
        def __init__(s, d): s.d = d
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def read(s): return _json.dumps(s.d).encode()

    def falsch(url, kopf, body, timeout):
        zuege.append(body)
        if len(zuege) == 1:
            return _R({"choices": [{"message": {"content": "", "tool_calls": [{"id": "1", "function": {"name": "echo", "arguments": '{"text": "hallo"}'}}]}}]})
        return _R({"choices": [{"message": {"content": "Antwort: " + zuege[-1]["messages"][-1]["content"]}}]})
    monkeypatch.setattr(K, "_post", falsch)
    monkeypatch.setattr(w.ki.ki, "werkzeug_frage", lambda n, a, s: True)
    r = w.ki.ki.chat([{"rolle": "mensch", "text": "Sag hallo"}])
    assert r["text"] == "Antwort: ECHO:hallo" and zuege[0]["tools"][0]["function"]["name"] == "echo"
    # abgelehnter Aufruf wird nicht ausgeführt
    zuege.clear()
    monkeypatch.setattr(w.ki.ki, "werkzeug_frage", lambda n, a, s: False)
    assert "abgelehnt" in w.ki.ki.chat([{"rolle": "mensch", "text": "Sag hallo"}])["text"]
    k.mcp_entfernen(e["id"])
    # Websuche: die Treffer stehen in der Anweisung
    gesehen = {}

    class _S:
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def read(s): return _json.dumps({"results": [{"title": "Titel", "url": "http://q", "content": "Inhalt"}]}).encode()
    monkeypatch.setattr(W.urllib.request, "urlopen", lambda req, timeout=0: _S())
    assert W.suche({"anbieter": "searxng", "url": "http://x", "anzahl": 3}, "was")[0]["titel"] == "Titel"
    k.websuche_setzen(an=True, anbieter="searxng", url="http://x")
    zuege.clear()

    def falsch2(url, kopf, body, timeout):
        gesehen.update(body)
        return _R({"choices": [{"message": {"content": "ok"}}]})
    monkeypatch.setattr(K, "_post", falsch2)
    assert w.ki.ki.chat([{"rolle": "mensch", "text": "was"}])["text"] == "ok"
    assert "Websuche" in gesehen["messages"][0]["content"] and "http://q" in gesehen["messages"][0]["content"]


def test_sprache_tab(app, tmp_path, monkeypatch):
    from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
    w = win(tmp_path, monkeypatch)
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    d = KIEinstellungenDialog(w, 2)
    assert d.reiter.tabText(2) == "Sprache" and d.reiter.currentIndex() == 2
    d.sprache.sprache.setCurrentText("Türkisch")
    d.sprache.pruefung.setCurrentIndex(d.sprache.pruefung.findData("en-US"))
    d._ok()
    assert w.ki.konfig["sprache"] == "Türkisch" and w.befehle.pruefsprache_aktuell() == "en-US"


def test_ki_einstellungen_bleiben_in_einem_fenster(app, tmp_path, monkeypatch):
    """„+“, „✎“ in KI-Modelle und MCP-Server öffnen ihr Formular als Seite im selben Fenster (Fensterstapel), nicht als neues Fenster."""
    from lunivo_writer.ui.baukasten.fenster_stapel import FensterStapel
    from lunivo_writer.ui.dialogs.ki_dialoge import AnbieterDialog, KIEinstellungenDialog, McpDialog
    w = win(tmp_path, monkeypatch)
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    d = KIEinstellungenDialog(w, 0)
    host = FensterStapel(d, w)
    d.liste._neu()
    assert len(host._seiten) == 2 and isinstance(host._seiten[-1][0], AnbieterDialog)
    host._seiten[-1][0].reject()
    assert len(host._seiten) == 1
    d.reiter.setCurrentIndex(3)
    d.mcp._neu()
    assert len(host._seiten) == 2 and isinstance(host._seiten[-1][0], McpDialog)
    top = host._seiten[-1][0]
    top.name.setText("Test"); top.befehl.setText("echo"); top.accept()
    assert len(host._seiten) == 1 and w.ki.konfig["mcp"][-1]["name"] == "Test" and d.mcp.liste.count() == 1


def test_aktionen_in_schreibhilfe_und_chat(app, tmp_path, monkeypatch):
    """Eine Schnelle KI-Aktion steht aus derselben Liste im Band, in der Schreibhilfe-Seitenleiste und im KI-Chat; ihr Ergebnis erscheint im Chat."""
    from lunivo_writer.ai import ki as K
    w = win(tmp_path, monkeypatch)
    monkeypatch.setattr(type(w.ki), "verfuegbar", lambda self: True)
    k = w.ki.konfig
    e = k.assistent_hinzufuegen("Kürzer", "Kürze den Text.", "hinweis", "kontext")
    w.ki.geaendert.emit()
    namen = lambda leiste: [b.text() for b in leiste.knoepfe]            # noqa: E731
    assert namen(w.sidebar.aktionen) == ["Kürzer", "＋ Neue Aktion"] and namen(w.sidebar.chat.aktionen) == ["Kürzer", "＋ Neue Aktion"]
    # Entfernen wirkt überall
    k.assistent_entfernen(e["id"]); w.ki.geaendert.emit()
    assert namen(w.sidebar.aktionen) == ["＋ Neue Aktion"] and namen(w.sidebar.chat.aktionen) == ["＋ Neue Aktion"]
    # Das Ergebnis einer Aktion kommt als Antwort in den Chat und in die Ergebnisliste
    e = k.assistent_hinzufuegen("Kürzer", "Kürze den Text.", "hinweis")
    w.current_editor().setPlainText("Ein langer Text, der gekürzt werden soll.")
    import time
    for _ in range(40):                                  # die Seitenverwaltung ändert das Blatt kurz nach dem Setzen; erst danach fragen (sonst „weitergeschrieben“)
        app.processEvents(); time.sleep(0.03)
    monkeypatch.setattr(w.ki, "_einwilligung", lambda modell=None: True)
    monkeypatch.setattr(w.ki.ki, "eigener_assistent", lambda text, prompt: {"text": "Kurz.", "cent": None})
    w.ki._pool.setMaxThreadCount(1)
    w.ki.assistent(e)
    for _ in range(300):
        app.processEvents()
        if any(z["text"] == "Kurz." for z in w.sidebar.chat.verlauf):
            break
        time.sleep(0.02)
    assert w.ki.ergebnisse and w.ki.ergebnisse[-1]["text"] == "Kurz."
    assert any(z["text"] == "Kurz." for z in w.sidebar.chat.verlauf)


def test_textbausteine_welche_hilfe_und_zusammenfassen(app, tmp_path, monkeypatch):
    from PySide6.QtGui import QTextCursor
    from lunivo_writer.services import bausteine
    from lunivo_writer.ui.dialogs.einfuegen_dialoge import BausteinDialog
    from lunivo_writer.ui.dialogs.welche_hilfe import HilfeWannDialog
    w = win(tmp_path, monkeypatch)
    monkeypatch.setattr(bausteine, "_pfad", lambda: str(tmp_path / "b.json"))
    # Seitenleiste: der vierte KI-Knopf
    assert [b.text() for b in w.sidebar.ki_knoepfe][-1] == "Zusammenfassen" and len(w.sidebar.ki_knoepfe) == 4
    # Mitgelieferte Bausteine mit Kürzel; F3 setzt das Kürzel ein
    assert len(bausteine.standard()) >= 10 and bausteine.finde_kuerzel("BT")["name"] == "Blindtext"
    e = w.current_editor()
    e.setPlainText("BT")
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    w.befehle.schnellbaustein()
    assert e.toPlainText().startswith("Er hörte leise Schritte")
    # Dialog: eigene aus Markierung mit Kürzel, mitgelieferte nicht löschbar
    e.setPlainText("Mit freundlichen Grüßen")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    d = BausteinDialog(w, e)
    d.name.setText("Gruß"); d.kuerzel.setText("MFG"); d._neu()
    assert [b["name"] for b in bausteine.laden()] == ["Gruß"] and bausteine.finde_kuerzel("MFG")["name"] == "Gruß"
    assert d._aktuell()["name"] == "Gruß" and d.loeschen.isEnabled()
    d.liste.setCurrentRow(1)
    assert not d.loeschen.isEnabled() and d._aktuell()["name"] == "Anfrage" and "Angebot" in d.vorschau.toPlainText()
    # Welche Hilfe wann: Schalter sind die der Seitenleiste
    h = HilfeWannDialog(w)
    h.schalter["wellen"].setChecked(False)
    assert not w.assistant.an("wellen")
    w.assistant.setze("wellen", True)
    assert h.schalter["wellen"].isChecked()
    assert w.befehle.hat("textbausteine")
