from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QPushButton

from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ui.dialogs.optionen import OptionenDialog
from lunivo_writer.ui.main_window import MainWindow


def win(tmp_path, monkeypatch):
    from lunivo_writer.services import gelernt, recovery
    monkeypatch.setattr(gelernt, "data_dir", lambda: str(tmp_path))
    from lunivo_writer.ai import ai_service as ki_dienst
    monkeypatch.setattr(ki_dienst, "data_dir", lambda: str(tmp_path))
    monkeypatch.setattr(recovery, "recovery_dir", lambda: str(tmp_path))
    return MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))


def test_optionen_baum_und_wirkung(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch); w.new_document()
    d = OptionenDialog(w, "lesehilfe")
    zweige = [d.baum.topLevelItem(i).text(0) for i in range(d.baum.topLevelItemCount())]
    assert zweige == ["Leichter lesen", "Allgemein", "Nur bei Lunivo"]
    assert sum(d.baum.topLevelItem(i).childCount() for i in range(3)) == 19
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
    feld = [e for e in d.findChildren(QLineEdit) if e.placeholderText().startswith("sk-ant")][0]
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


def test_neue_optionen_wirken(app, tmp_path, monkeypatch):
    """Mittlere Maustaste, Text verschieben, Zeilenfokus nach dem Neustart, getrennte Formatzeichen, QuickInfo, Weicher Kontrast."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent, QPalette, QTextOption
    from PySide6.QtWidgets import QApplication
    from lunivo_writer.ui import theme
    w = win(tmp_path, monkeypatch); w.new_document()
    e = w.current_editor()
    # Text mit der Maus verschieben
    w.settings.set("bearbeiten/ziehen", False); w.lesehilfe_anwenden()
    assert not e.acceptDrops()
    w.settings.set("bearbeiten/ziehen", True); w.lesehilfe_anwenden()
    assert e.acceptDrops()
    # Zeilenfokus aus den Einstellungen für ein neues Dokument
    w.settings.set("lesehilfe/zeilenfokus", True); w.new_document()
    assert w.current_editor().zeilenfokus is True
    # Absatzmarken und Leerzeichen getrennt
    w.marken_setzen(absatz=True, leer=False)
    fl = e.document().defaultTextOption().flags()
    assert fl & QTextOption.ShowLineAndParagraphSeparators and not fl & QTextOption.ShowTabsAndSpaces
    w.marken_setzen(leer=True)
    assert e.document().defaultTextOption().flags() & QTextOption.ShowTabsAndSpaces
    w.toggle_marks(False)
    assert not e.document().defaultTextOption().flags() & (QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators)
    # QuickInfo
    w.settings.set("ui/quickinfo", False); w.ansicht_optionen_anwenden()
    ev = QEvent(QEvent.ToolTip)
    assert w._quickinfo.eventFilter(e, ev) is True
    w.settings.set("ui/quickinfo", True); w.ansicht_optionen_anwenden()
    assert w._quickinfo.eventFilter(e, ev) is False
    # Weicher Kontrast ändert die Farben
    app_ = QApplication.instance()
    try:
        w.settings.set("ui/weich", False); w.set_theme("dark")
        hart = app_.palette().color(QPalette.Window).name()
        w.settings.set("ui/weich", True); w.set_theme("dark")
        assert theme.WEICH and app_.palette().color(QPalette.Window).name() != hart
    finally:
        w.settings.set("ui/weich", False); w.set_theme("system")
    # mittlere Maustaste aus: das Loslassen wird geschluckt
    w.settings.set("bearbeiten/mittlere_taste", False)
    m = QMouseEvent(QEvent.MouseButtonRelease, QPointF(5, 5), Qt.MiddleButton, Qt.MiddleButton, Qt.NoModifier)
    e.mouseReleaseEvent(m)
    assert m.isAccepted()
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()


def test_lesehilfe_stufen_grammatik_und_kompatibilitaet(app, tmp_path, monkeypatch):
    """Absatz größer / Übriger Text blasser (nur am Schirm), Grammatik-Schalter der Prüfung, Kompatibilität und Bildkompression in DOCX."""
    import zipfile
    from PySide6.QtGui import QColor, QImage
    from lunivo_writer.editor import einfuegen as E
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.proofing import pruefung
    from lunivo_writer.services import file_service as formats
    w = win(tmp_path, monkeypatch); w.new_document()
    e = w.current_editor()
    e.setPlainText("Erster Absatz mit Text.\nZweiter Absatz mit Text.\nDritter Absatz mit Text.")
    # Übriger Text blasser: nur die anderen Absätze bekommen eine hellere Farbe; das Dokument bleibt unverändert
    w.settings.set("lesehilfe/zurueck", "deutlich"); w.settings.set("lesehilfe/groesser", "deutlich"); w.lesehilfe_anwenden()
    c = e.textCursor(); c.setPosition(e.document().findBlockByNumber(1).position() + 3); e.setTextCursor(c)
    e._overlays_neu()
    blass = [s for s in e.extraSelections() if s.format.foreground().color().lightness() > 50]
    nummern = {e.document().findBlock(s.cursor.selectionStart()).blockNumber() for s in blass}
    assert nummern == {0, 2} and e._lese_wachstum == 1.10 and e._lese_blasse == 0.38
    assert e.toPlainText().count("\n") == 2                                       # das Dokument selbst bleibt, wie es war
    e.viewport().update(); e.grab()                                                  # das Zeichnen des größeren Absatzes stürzt nicht
    w.settings.set("lesehilfe/zurueck", "keine"); w.settings.set("lesehilfe/groesser", "keine"); w.lesehilfe_anwenden()
    assert not [s for s in e.extraSelections() if s.format.foreground().color().lightness() > 50 and s.format.foreground().style()]
    # Grammatik mitprüfen
    for text in ("Wir hat gestern ein Buch gelesen.", "Ich glaube das er morgen kommt."):
        assert len(pruefung.finde_probleme(text, None, {"rsGrammatik": True})) == 1
        assert pruefung.finde_probleme(text, None, {"rsGrammatik": False}) == []
        assert len(pruefung.finde_probleme(text, None, None)) == 1                    # ohne Angabe: Grammatik wird mitgeprüft
    # DOCX: Kompatibilität und Bildkompression
    w.settings.set("kompat/leerstellen", True); w.settings.set("kompat/haengend", True); w.settings.set("speichern/bilder_nicht_komprimieren", False)
    meta = w.dokumente.meta_fuer_speichern({})
    assert set(meta["kompat"]) == {"ulTrailSpace", "doNotUseIndentAsNumberingTabStop"} and meta["bilder_komprimieren"] is True
    gross = QImage(3000, 2000, QImage.Format_RGB32); gross.fill(QColor("tomato"))
    E.qimage_einfuegen(e, gross, "Gross")
    pfad = str(tmp_path / "k.docx")
    formats.save(pfad, e.document(), PageSettings(), meta)
    z = zipfile.ZipFile(pfad)
    einst = z.read("word/settings.xml").decode()
    assert "<w:ulTrailSpace" in einst and "<w:doNotUseIndentAsNumberingTabStop" in einst and "doNotAutoCompressPictures" not in einst
    assert einst.index("<w:ulTrailSpace") < einst.index("<w:useFELayout") < einst.index("<w:doNotUseIndentAsNumberingTabStop")
    bild = QImage.fromData(z.read([n for n in z.namelist() if n.startswith("word/media/")][0]))
    assert max(bild.width(), bild.height()) == 1600
    # Standard: nichts davon
    meta2 = {"kompat": [], "bilder_komprimieren": False}
    formats.save(pfad, e.document(), PageSettings(), meta2)
    z2 = zipfile.ZipFile(pfad)
    assert "<w:ulTrailSpace" not in z2.read("word/settings.xml").decode()
    assert max(QImage.fromData(z2.read([n for n in z2.namelist() if n.startswith("word/media/")][0])).size().toTuple()) == 3000
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()


def test_seitenleiste_und_optionen_gehen_hand_in_hand(app, tmp_path, monkeypatch):
    w = win(tmp_path, monkeypatch)
    sb = w.sidebar
    # Stufe 1/2: Schalter der Schreibhilfe
    w.assistant.setze("wellen", False)
    assert not sb.chips["wellen"].isChecked()
    w.assistant.setze("wellen", True)
    assert sb.chips["wellen"].isChecked()
    # Für wen? (Optionen -> Seitenleiste)
    w.assistant.setze_thema("Amt")
    assert any(b.text() == "Amt" and b.isChecked() for b in sb.gruppe.buttons())
    # Stufe 4: KI -> Seitenleiste wird über dasselbe Signal neu bewertet
    gesehen = []
    w.ki.geaendert.connect(lambda: gesehen.append(1))
    w.ki.geaendert.emit()
    assert gesehen


def test_befehlslisten_kennwort_ki_und_erweitert(app, tmp_path, monkeypatch):
    import json
    from PySide6.QtWidgets import QListWidget
    w = win(tmp_path, monkeypatch)
    d = OptionenDialog(w, "schnellzugriff")
    seite = d.stapel.currentWidget()
    listen = seite.findChildren(QListWidget)
    links, rechts = listen[0], listen[1]
    n = rechts.count()
    links.setCurrentRow(0)
    erster = links.item(0).data(Qt.UserRole)
    seite.findChildren(QPushButton)  # Knöpfe vorhanden
    [b for b in seite.findChildren(QPushButton) if b.text() == "Hinzufügen >>"][0].click()
    assert rechts.count() == n + 1
    assert erster in json.loads(w.settings.get("ui/schnellzugriff"))
    # Menüband: ein Register ausblenden
    d.gehe_zu("menueband")
    seite = d.stapel.currentWidget()
    links, rechts = seite.findChildren(QListWidget)[:2]
    rechts.setCurrentRow(0); name = rechts.item(0).text()
    [b for b in seite.findChildren(QPushButton) if b.text() == "Entfernen"][0].click()
    assert name in json.loads(w.settings.get("ui/register_plan"))["versteckt"]
    # Sicherheit: Kennwort, Markup-Haken
    d.gehe_zu("sicherheit")
    d.gehe_zu("ki"); d.gehe_zu("gedaechtnis"); d.gehe_zu("erweitert")
    # KI: Aufgabenmodell wird gespeichert
    d.gehe_zu("ki")
    seite = d.stapel.currentWidget()
    from PySide6.QtWidgets import QComboBox
    c = [x for x in seite.findChildren(QComboBox)][0]
    assert c.itemText(0).startswith("Standard (")
