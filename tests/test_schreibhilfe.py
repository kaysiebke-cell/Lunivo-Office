import os

from PySide6.QtCore import QEventLoop, QSettings, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest

from native_qt.storage.settings import Settings
from native_qt.windows.main_window import MainWindow


def win(tmp_path, monkeypatch):
    from native_qt.storage import gelernt
    monkeypatch.setattr(gelernt, "data_dir", lambda: str(tmp_path))
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
    namen = [w.band.reiter.tabText(i) for i in range(w.band.reiter.count())]
    assert namen == ["Start", "Einfügen", "Seitenlayout", "Referenzen", "Überprüfen", "Schreibhilfe", "Sendungen", "Ansicht"]
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
