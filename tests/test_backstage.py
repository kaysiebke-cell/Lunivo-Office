"""Backstage-Ansicht des Reiters „Datei“."""
from PySide6.QtCore import QSettings

from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ui.main_window import MainWindow


def fenster(tmp_path):
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.show()
    return w


def test_datei_reiter_oeffnet_backstage_und_anderer_reiter_schliesst(app, tmp_path):
    w = fenster(tmp_path)
    w.new_document()
    r = w.band.reiter
    assert not w.backstage.isVisible() and w.arbeit.isVisible()
    r.setCurrentIndex(0)
    assert w.backstage.isVisible() and not w.arbeit.isVisible() and not w.band.stapel.isVisible()
    r.setCurrentIndex(2)                                           # Einfügen
    assert not w.backstage.isVisible() and w.arbeit.isVisible() and w.band.stapel.isVisible()
    r.setCurrentIndex(0)
    w.backstage.schliessen.emit()                                  # „Zurück zum Dokument“ / Esc → letzter Reiter
    assert not w.backstage.isVisible() and r.tabText(r.currentIndex()) == "Einfügen"


def test_seiten_und_befehle(app, tmp_path):
    w = fenster(tmp_path)
    w.new_document()
    w.backstage_oeffnen()
    b = w.backstage
    assert set(b.seiten) == {"zuletzt", "speichern_als", "drucken", "schuetzen", "info", "oeffnen_mit"}
    b._zeigen("info")
    t = w.current_tab()
    # Eigenschaften werden ins Dokument übernommen
    from PySide6.QtWidgets import QLineEdit
    felder = b.seiten["info"].findChildren(QLineEdit)
    felder[0].setText("Kay"); felder[0].editingFinished.emit()
    assert t.meta["author"] == "Kay"
    # Eintrag mit Befehl schließt die Ansicht und führt ihn aus
    gerufen = []
    w.befehle.schliessen = lambda k=None: gerufen.append(1)
    b._gewaehlt(b.zeilen["schliessen"])
    assert gerufen and not b.isVisible()
    w.backstage_zu()


def test_ohne_dokument_nur_zuletzt(app, tmp_path):
    w = fenster(tmp_path)
    w.backstage_oeffnen("info")
    assert w.backstage.stapel.currentWidget() is w.backstage.seiten["zuletzt"]
    from PySide6.QtCore import Qt
    assert not (w.backstage.zeilen["speichern"].flags() & Qt.ItemIsEnabled)       # ohne Dokument gesperrt
    assert w.backstage.zeilen["neu"].flags() & Qt.ItemIsEnabled
