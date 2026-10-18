from PySide6.QtCore import QSettings

from native_qt.storage.settings import Settings
from native_qt.widgets.optionen import OptionenDialog
from native_qt.windows.main_window import MainWindow


def win(tmp_path, monkeypatch):
    from native_qt.storage import gelernt, recovery
    monkeypatch.setattr(gelernt, "data_dir", lambda: str(tmp_path))
    from native_qt.services import ki_dienst
    monkeypatch.setattr(ki_dienst, "data_dir", lambda: str(tmp_path))
    monkeypatch.setattr(recovery, "recovery_dir", lambda: str(tmp_path))
    return MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))


def test_optionen_baum_und_wirkung(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch); w.new_document()
    d = OptionenDialog(w, "lesehilfe")
    zweige = [d.baum.topLevelItem(i).text(0) for i in range(d.baum.topLevelItemCount())]
    assert zweige == ["Leichter lesen", "Wie im WPS Writer", "Nur bei Lunivo"]
    assert sum(d.baum.topLevelItem(i).childCount() for i in range(3)) == 14
    # Papierton wirkt auf den Editor und wird gespeichert
    from PySide6.QtWidgets import QComboBox
    seite = d.stapel.widget(d.baum.currentItem().data(0, 0x101))
    box = seite.findChildren(QComboBox)[0]
    box.setCurrentText("Creme")
    assert w.settings.get("lesehilfe/papier") == "Creme"
    assert "#fbf4e2" in w.current_editor().styleSheet()


def test_optionen_ki_seite_speichert_schluessel_privat(app, tmp_path, monkeypatch):
    import os
    w = win(tmp_path, monkeypatch)
    d = OptionenDialog(w, "ki")
    from PySide6.QtWidgets import QLineEdit
    feld = [e for e in d.findChildren(QLineEdit) if e.placeholderText().startswith("Schlüssel (sk-")][0]
    feld.setText("sk-ant-test"); feld.editingFinished.emit()
    assert w.ki.konfig["apiKey"] == "sk-ant-test"
    assert oct(os.stat(w.ki.konfig.pfad).st_mode & 0o777) == "0o600"
    assert w.sidebar.ki_knoepfe[0].isEnabled()            # Knöpfe werden frei, sobald ein Schlüssel da ist


def test_autokorr_einzelschalter_wirkt(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch); w.new_document()
    w.settings.set("schreibhilfe/akAuslassung", False)
    from PySide6.QtTest import QTest
    e = w.current_editor(); e.setFocus()
    QTest.keyClicks(e, "Ende... ")
    assert "..." in e.toPlainText() and "…" not in e.toPlainText()
