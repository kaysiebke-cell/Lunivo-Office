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
    assert set(b.seiten) == {"zuletzt", "vorlage", "speichern_als", "drucken", "schuetzen", "info", "oeffnen_mit", "optionen", "hilfe"}
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


def test_menue_knopf_links_oeffnet_die_datei_ansicht(app, tmp_path):
    """„☰ Menü“ steht ganz links vor dem Schnellzugriff und ersetzt den sichtbaren Reiter „Datei“."""
    w = fenster(tmp_path)
    w.new_document()
    k, r = w.band.menue_knopf, w.band.reiter
    assert k.isVisible() and k.text() == "☰ Menü" and w.band.kopf.indexOf(k) == 0
    assert [r.tabText(i) for i in range(r.count()) if r.isTabVisible(i)][0] == "Start"      # kein Reiter „Datei“ mehr zu sehen
    k.click()
    assert w.backstage.isVisible() and k.isChecked() and not w.arbeit.isVisible()
    k.click()                                                                                # zweiter Klick: zurück zum Dokument
    assert not w.backstage.isVisible() and w.arbeit.isVisible() and not k.isChecked()


def test_dateisymbole_in_zuletzt_und_speichern_als(app, tmp_path, monkeypatch):
    """Die Liste „Zuletzt verwendet“ und die Ausgabeformate zeigen das Symbol des Dateiformats aus dem System-Theme."""
    from PySide6.QtGui import QColor, QIcon, QPixmap
    from PySide6.QtWidgets import QPushButton
    from lunivo_writer.ui import backstage as B
    pm = QPixmap(8, 8); pm.fill(QColor("red")); marke = QIcon(pm)
    gefragt = []
    monkeypatch.setattr(B, "datei_symbol", lambda n: (gefragt.append(n), marke)[1])
    w = fenster(tmp_path)
    w.new_document()
    datei = tmp_path / "brief.docx"; datei.write_bytes(b"x")
    w.settings.add_recent(str(datei))
    w.backstage.oeffnen("zuletzt")
    k = next(b for b in w.backstage.findChildren(QPushButton) if b.text().startswith("brief.docx"))
    assert k.icon().cacheKey() == marke.cacheKey() and str(datei) in gefragt
    assert k.text() == "brief.docx" and k.toolTip() == str(datei)                            # nur der Name; der Pfad steht im Tooltip
    w.backstage.oeffnen("speichern_als")
    assert {".pdf", ".docx", ".odt", ".rtf", ".txt"} <= set(gefragt)
    knoepfe = [b for b in w.backstage.findChildren(QPushButton) if b.text().startswith("Word-Dokument")]
    assert knoepfe and knoepfe[0].icon().cacheKey() == marke.cacheKey()


def test_optionen_stehen_in_der_datei_ansicht(app, tmp_path):
    """F9 / „Erweiterte Einstellungen“ öffnet die Optionen als Seite der Datei-Ansicht, nicht als eigenes Fenster."""
    from lunivo_writer.ui.dialogs.optionen import OptionenAnsicht
    w = fenster(tmp_path)
    w.new_document()
    w.show_options("ki")
    assert w.backstage.isVisible() and w.band.menue_knopf.isChecked()
    ph = w.backstage.seiten["optionen"]
    assert w.backstage.stapel.currentWidget() is ph and isinstance(ph._ansicht, OptionenAnsicht)
    assert ph._ansicht.baum.currentItem().data(0, 0x100) == "ki"                  # gleich auf der gewünschten Seite
    assert not w.backstage._links.isVisible()                                      # das Menü ist für die Dauer der Optionen weg
    w.show_options("sprache")
    assert w.backstage.seiten["optionen"]._ansicht.baum.currentItem().data(0, 0x100) == "schreiben"    # „sprache“ führt auf die neue Seite
    w.backstage_schliessen()
    assert not w.backstage.isVisible() and w.arbeit.isVisible() and not w.band.menue_knopf.isChecked()
    # Verlassen: oben „← Optionen“ oder unten rechts „Fertig“
    for knopf in ("_zurueck", "_fertig"):
        w.show_options()
        assert w.backstage.isVisible() and not w.backstage._links.isVisible()
        getattr(w.backstage.seiten["optionen"], knopf).click()
        assert not w.backstage.isVisible() and w.arbeit.isVisible()
    w.backstage_oeffnen("info")                                                    # danach ist das Menü wieder da
    assert w.backstage._links.isVisible()
    w.backstage_zu()
