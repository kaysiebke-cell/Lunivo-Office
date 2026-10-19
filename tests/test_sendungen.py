from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QTextCursor, QTextDocument, QTextFormat

from lunivo_writer.editor import sendungen as S
from lunivo_writer.ui.document.document_editor import DocumentEditor


def ed(text=""):
    e = DocumentEditor(); e.setPlainText(text); e.zusatz_binden({})
    c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
    return e


def test_umschlag_und_etiketten(app):
    e = ed()
    pg = S.umschlag_aufbauen(e, "DIN lang (220 × 110 mm)", "Ann Muster\nWeg 1\n12345 Stadt", "Herr Meier\nStraße 2\n54321 Ort")
    assert (pg.width_mm, pg.height_mm) == (220, 110) and "Herr Meier" in e.toPlainText() and e.toPlainText().startswith("Ann Muster")
    e2 = ed()
    pg2 = S.etiketten_aufbauen(e2, "70 × 37 mm — 24 Stück (3 × 8)", "Ann Muster\nWeg 1", True)
    c = QTextCursor(e2.document()); c.setPosition(1)
    t = c.currentTable()
    assert t is not None and (t.rows(), t.columns()) == (8, 3)
    assert e2.toPlainText().count("Ann Muster") == 24 and pg2.margin_left_mm == 5
    e3 = ed()
    S.etiketten_aufbauen(e3, "105 × 148 mm — 4 Stück (2 × 2)", "Eins\nZwei\nDrei", False)
    assert [x for x in e3.toPlainText().split("\n") if x.strip()][:3] == ["Eins", "Zwei", "Drei"]


def test_serienbrief_mit_feldern_regeln_und_seitenumbruechen(app):
    e = ed("Hallo ")
    S.feld_einfuegen(e, "Name")
    e.insertPlainText(", wohnhaft in ")
    S.feld_einfuegen(e, "Ort")
    e.insertPlainText(". ")
    S.regel_einfuegen(e, "Geschlecht", "w", "Sehr geehrte Frau", "Sehr geehrter Herr")
    assert S.felder_im_text(e.document()) == ["Name", "Ort"]
    tab = S.tabelle_lesen("Name;Ort;Geschlecht\nMeier;Kiel;w\nSchmidt;Bonn;m")
    assert tab[0] == ["Name", "Ort", "Geschlecht"] and len(tab[1]) == 2
    ziel = QTextDocument()
    n = S.serienbrief_erzeugen(e.document(), tab[1], ziel)
    text = ziel.toPlainText()
    assert n == 2 and "Hallo Meier, wohnhaft in Kiel. Sehr geehrte Frau" in text and "Hallo Schmidt, wohnhaft in Bonn. Sehr geehrter Herr" in text
    assert "{{" not in text
    umbrueche = [b for b in _bloecke(ziel) if b.blockFormat().pageBreakPolicy() & QTextFormat.PageBreak_AlwaysBefore]
    assert len(umbrueche) == 1
    assert S.tabelle_lesen("nur eine Zeile") is None
    # Vorlage bleibt unverändert
    assert "{{Name}}" in e.toPlainText()
    S.adressblock_einfuegen(e, "beides")
    assert "{{Straße}}" in e.toPlainText() and "Sehr geehrte{{Anrede}} {{Name}}," in e.toPlainText()


def _bloecke(doc):
    b = doc.firstBlock()
    while b.isValid():
        yield b
        b = b.next()


def test_kontrollkaestchen_umschalten_und_formularfelder(app):
    e = ed("")
    S.form_kasten(e, "Ja")
    S.form_textfeld(e, "Name")
    S.form_knopf(e, "Absenden")
    t = e.toPlainText()
    assert t.startswith("☐ Ja") and "[ Name ]" in t and "Absenden" in t
    assert S.kasten_umschalten(e, 0) and e.toPlainText().startswith("☒ Ja")
    assert S.kasten_umschalten(e, 1) and e.toPlainText().startswith("☐ Ja")           # auch direkt hinter dem Zeichen
    assert not S.kasten_umschalten(e, 5)


def test_sendungen_reiter_im_band(app, tmp_path):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    standard = [w.band.reiter.tabText(i) for i in range(w.band.reiter.count()) if w.band.reiter.isTabVisible(i)]
    assert "Sendungen" not in standard                           # neue Struktur: acht Reiter
    import json
    w.settings.set("ui/register_plan", json.dumps({"reihenfolge": [], "versteckt": []}))
    w.neu_bauen_band()
    namen = [w.band.reiter.tabText(i) for i in range(w.band.reiter.count())]
    assert namen[:9] == ["Datei", "Start", "Einfügen", "Seitenlayout", "Verweise", "Überprüfen", "Schreibhilfe", "Ansicht", "Sendungen"]
    assert not w.band.bandfehler or "umschlag" not in w.band.bandfehler
    for n in ("umschlag", "etiketten", "seriendruck", "seriendruckfeld", "adressblock", "seriendruckregel", "serienVorschau",
              "formTextfeld", "formKasten", "formKnopf"):
        assert w.befehle.hat(n), n
    w.close()
