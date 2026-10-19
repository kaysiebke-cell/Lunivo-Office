"""Reiter Seitenlayout (Anordnung wie WPS): Maßfelder für die Ränder, Spalten 1 bis 4."""
from PySide6.QtCore import QSettings

from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ui.main_window import MainWindow


def fenster(tmp_path):
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.show()
    w.new_document()
    return w


def test_randfelder_setzen_den_rand_und_zeigen_ihn_an(app, tmp_path):
    w = fenster(tmp_path)
    f = w.band.felder
    assert {"rand_oben", "rand_unten", "rand_links", "rand_rechts"} <= set(f)
    w._sync_format()
    t = w.current_tab()
    assert abs(f["rand_links"].value() - t.page.margin_left_mm) < 0.01
    f["rand_links"].setValue(40.0)                                   # wirkt wie eine Eingabe im Feld
    assert abs(t.page.margin_left_mm - 40.0) < 0.01
    assert abs(t.page.margin_top_mm - 25.0) < 0.01                   # die anderen Ränder bleiben
    t.page.margin_top_mm = 30.0                                      # von außen geändert (Dialog): das Feld folgt
    w._sync_format()
    assert abs(f["rand_oben"].value() - 30.0) < 0.01


def test_reihenfolge_der_gruppen_und_vier_spalten(app, tmp_path):
    w = fenster(tmp_path)
    r = w.band.reiter
    i = next(i for i in range(r.count()) if r.tabText(i) == "Seitenlayout")
    from PySide6.QtWidgets import QLabel
    seite = w.band.stapel.widget(i).widget()
    titel = [l.text() for l in seite.findChildren(QLabel) if l.text() in ("DESIGNS", "RÄNDER", "SEITE EINRICHTEN", "SEITENHINTERGRUND", "ANORDNEN", "ABSATZ")]
    assert titel == ["DESIGNS", "RÄNDER", "SEITE EINRICHTEN", "SEITENHINTERGRUND", "ANORDNEN", "ABSATZ"]
    w.befehle.tun("spaltenSetzen:[4]")
    assert w.current_tab().page.spalten == 4


def test_reiter_einfuegen_verweise_ansicht_wie_wps(app, tmp_path):
    from PySide6.QtWidgets import QLabel
    w = fenster(tmp_path)
    r = w.band.reiter
    erwartet = {
        "Einfügen": ["SEITEN", "TABELLEN", "ILLUSTRATIONEN", "KOMMENTAR", "KOPF- UND FUSSZEILE", "TEXT", "SYMBOLE", "LINKS", "FORMULARE"],
        "Verweise": ["INHALTSVERZEICHNIS", "FUSSNOTEN", "BESCHRIFTUNGEN", "INDEX", "ZITATE UND LITERATUR", "SERIENDRUCK"],
        "Ansicht": ["DOKUMENTANSICHTEN", "ANZEIGEN", "ZOOM", "HELLIGKEIT", "FENSTER", "OBERFLÄCHE"],
    }
    for name, soll in erwartet.items():
        i = next(i for i in range(r.count()) if r.tabText(i) == name)
        seite = w.band.stapel.widget(i).widget()
        titel = [l.text() for l in seite.findChildren(QLabel) if l.text().isupper() and l.text() in soll]
        assert titel == soll, (name, titel)
    assert w.befehle.hat("vollbild")


def test_pruefung_steht_in_der_schreibhilfe_und_ueberpruefen_hat_den_rest(app, tmp_path):
    from PySide6.QtWidgets import QToolButton
    w = fenster(tmp_path)
    r = w.band.reiter
    texte = {}
    for name in ("Schreibhilfe", "Überprüfen"):
        i = next(i for i in range(r.count()) if r.tabText(i) == name)
        seite = w.band.stapel.widget(i).widget()
        texte[name] = [k.toolTip() for k in seite.findChildren(QToolButton)]
        if name == "Schreibhilfe":
            knopf = next(k for k in seite.findChildren(QToolButton) if k.toolTip().startswith("Dokumentprüfung"))
            assert knopf.isEnabled() and knopf.menu() is not None          # früher: Menü fehlte, Knopf war grau
            namen = [a.text() for a in knopf.menu().actions()]
            assert {"Prüfen", "Rechtschreibung", "Thesaurus", "Barrierefreiheit prüfen"} <= set(namen)
    for verboten in ("Rechtschreibung", "Thesaurus", "Gründlich prüfen", "Korrektursprache", "Barrierefreiheit prüfen"):
        assert not any(t.startswith(verboten) for t in texte["Überprüfen"]), verboten
    assert any(t.startswith("Neuer Kommentar") for t in texte["Überprüfen"])
