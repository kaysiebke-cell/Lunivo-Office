"""Die gemeinsamen Bausteine der Oberfläche: Farbpalette, Linien, Menü-Liste, Kachel-Auswahl, Maßfeld, Dialoggerüst."""
from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QColorDialog, QDialog, QLabel

from lunivo_writer.ui.baukasten import (
    DialogRahmen, FarbFeld, FarbKnopf, FarbPalette, Linie, LinienWahl, MassSpin, MenueListe, RahmenMenue, RahmenSeiten,
    RasterAuswahl, set_einheit,
)
from lunivo_writer.ui.baukasten import farben as F


def _sauber():
    from PySide6.QtCore import QSettings
    QSettings().remove(F.ZULETZT_SCHLUESSEL)


def test_abstufungen_und_raster(app):
    raster = F.thema_raster()
    assert len(raster) == 6 and all(len(z) == 10 for z in raster)
    assert raster[0] == list(F.THEMA_FARBEN)
    blau = F.abstufungen("#1971c2")
    assert len(blau) == 5 and QColor(blau[0]).lightness() > QColor("#1971c2").lightness() > QColor(blau[4]).lightness()
    assert all(QColor(f).isValid() for z in raster for f in z)


def test_palette_meldet_farbe_keine_und_merkt_zuletzt(app):
    _sauber()
    pal = FarbPalette(keine_text="Keine Farbe")
    erhalten = []
    pal.gewaehlt.connect(erhalten.append)
    pal.waehle(QColor("#c92a2a"))
    pal.waehle(None)
    assert [e.name() if e is not None else None for e in erhalten] == ["#c92a2a", None]
    assert F.zuletzt_laden() == ["#c92a2a"]
    # beim nächsten Öffnen steht „Zuletzt benutzt“ da
    assert any(l.text() == "Zuletzt benutzt" for l in FarbPalette().findChildren(QLabel))
    _sauber()


def test_palette_ueberfahren_meldet_vorschau(app):
    pal = FarbPalette()
    geseh, ende = [], []
    pal.ueberfahren.connect(lambda c: geseh.append(c.name())); pal.verlassen.connect(lambda: ende.append(1))
    from lunivo_writer.ui.baukasten.farbpalette import _Kachel
    k = pal.findChildren(_Kachel)[0]
    k.enterEvent(None); k.leaveEvent(None)
    assert geseh == [k.farbe] and ende == [1]


def test_weitere_farben_ueber_den_system_waehler(app, monkeypatch):
    _sauber()
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor("#123456")))
    pal = FarbPalette(); erhalten = []
    pal.gewaehlt.connect(erhalten.append)
    pal._weitere()
    assert erhalten[0].name() == "#123456" and F.zuletzt_laden()[0] == "#123456"
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor()))   # Abbruch
    pal._weitere()
    assert len(erhalten) == 1
    _sauber()


def test_farbfeld_uebernimmt_farbe_aus_der_palette(app, monkeypatch):
    feld = FarbFeld("#000000", "Test", keine_text="Keine")
    monkeypatch.setattr(FarbFeld, "_zeige_popup", lambda self, pal: pal.waehle(QColor("#2f9e44")))
    gemeldet = []
    feld.farbeGeaendert.connect(gemeldet.append)
    feld.click()
    assert feld.farbe == "#2f9e44" and gemeldet == ["#2f9e44"] and "#2f9e44" in feld.styleSheet()
    monkeypatch.setattr(FarbFeld, "_zeige_popup", lambda self, pal: pal.waehle(None))
    feld.click()
    assert feld.farbe == "" and feld.text() == "Keine"


def test_farbknopf_klick_wendet_letzte_farbe_an(app):
    from PySide6.QtGui import QIcon, QPixmap
    pm = QPixmap(22, 22); pm.fill(QColor("white"))
    k = FarbKnopf(QIcon(pm), "Schriftfarbe", "#c92a2a")
    erhalten = []
    k.angewendet.connect(erhalten.append)
    k.click()
    assert erhalten[-1].name() == "#c92a2a"
    k.menu().waehle(QColor("#1971c2"))
    assert k.farbe == "#1971c2" and erhalten[-1].name() == "#1971c2"
    k.click()
    assert erhalten[-1].name() == "#1971c2"
    _sauber()


def test_linie_text_stift_und_zeichnen(app):
    li = Linie("#c92a2a", 1.5, "gestrichelt")
    assert li.text() == "#c92a2a|1.5|gestrichelt"
    assert Linie.aus_text(li.text()) == li
    assert Linie.aus_text("") is None and Linie.aus_text("x|y") is None
    assert li.stift(96 / 72).widthF() == 1.5 * 96 / 72
    bild = QImage(60, 20, QImage.Format_ARGB32); bild.fill(QColor("white"))
    p = QPainter(bild)
    Linie("#000000", 3.0, "doppelt").zeichne(p, 2, 10, 58, 10)
    p.end()
    zeilen = [bild.pixelColor(30, y).lightness() < 128 for y in range(20)]
    assert sum(zeilen) >= 2                            # doppelt: zwei getrennte Striche


def test_linienwahl_meldet_aenderungen(app):
    w = LinienWahl(Linie("#000000", 1.0, "einfach"))
    gemeldet = []
    w.geaendert.connect(gemeldet.append)
    w.art.setCurrentIndex(w.art.findData("gepunktet"))
    w.breite.setCurrentIndex(w.breite.findData(3.0))
    w.farbe._uebernehmen(QColor("#1971c2"))
    assert w.linie() == Linie("#1971c2", 3.0, "gepunktet") and gemeldet[-1] == w.linie()
    w.setLinie(Linie("#c92a2a", 0.75, "doppelt"))
    assert w.linie() == Linie("#c92a2a", 0.75, "doppelt")


def test_rahmenmenue_meldet_seiten(app):
    m = RahmenMenue()
    gemeldet = []
    m.gewaehlt.connect(lambda s, k: gemeldet.append((k, s)))
    namen = {a.text(): a for a in m.actions() if a.text()}
    namen["Rahmenlinie unten"].trigger(); namen["Rahmenlinien außen"].trigger(); namen["Kein Rahmen"].trigger()
    assert gemeldet[0] == ("unten", RahmenSeiten.UNTEN)
    assert gemeldet[1][1] == RahmenSeiten.AUSSEN and RahmenSeiten.OBEN in gemeldet[1][1] and RahmenSeiten.INNEN_H not in gemeldet[1][1]
    assert gemeldet[2] == ("kein", RahmenSeiten.KEINE)
    assert "Innere horizontale Rahmenlinie" not in [a.text() for a in RahmenMenue(innen=False).actions()]


def test_menueliste_aus_beschreibung(app):
    ausgeloest = []
    m = MenueListe.aus_liste([
        {"text": "Öffnen", "kuerzel": "Strg+O", "aktion": lambda: ausgeloest.append("auf")},
        {"text": "Fett", "haken": True, "aktion": lambda: ausgeloest.append("fett")},
        "-",
        {"text": "Mehr", "untermenue": [{"text": "Innen", "aktion": lambda: ausgeloest.append("innen")}]},
        {"text": "Grau", "aktiv": False},
    ])
    a = m.actions()
    assert a[0].text() == "Öffnen\tStrg+O" and a[1].isCheckable() and a[1].isChecked() and a[2].isSeparator()
    a[0].trigger(); a[3].menu().actions()[0].trigger()
    assert ausgeloest == ["auf", "innen"] and not a[4].isEnabled()


def test_rasterauswahl_meldet_schluessel(app):
    r = RasterAuswahl(spalten=2)
    r.kacheln([("a", "Eins", None), ("b", "Zwei", lambda p, rc: p.drawRect(rc)), ("c", "Drei", None)], aktuell="b")
    gemeldet, fuss = [], []
    r.gewaehlt.connect(gemeldet.append)
    r.fuss("Mehr …", lambda: fuss.append(1))
    assert r.knoepfe["b"].isChecked() and not r.knoepfe["a"].isChecked()
    r.knoepfe["c"].click()
    assert gemeldet == ["c"]


def test_massfeld_versteht_einheiten(app):
    try:
        set_einheit("Zentimeter")
        s = MassSpin(); s.setRange(0, 500)
        s.setValue(25.0)
        assert s.text() == "2,50 cm"
        assert abs(s.valueFromText("30 mm") - 30.0) < 1e-6 and abs(s.valueFromText("2 cm") - 20.0) < 1e-6
    finally:
        set_einheit("Millimeter")


def test_dialograhmen_vorschau_und_zusatzknopf(app):
    gemalt = []
    class D(DialogRahmen):
        def ergebnis(self): return 42
    d = D(None, "Titel", lambda p, r: gemalt.append(r))
    d.zeile("Name", QLabel("x"))
    kn = d.zusatzknopf("Entfernen")
    d.resize(300, 300); d.show(); d.aktualisieren(); app.processEvents()
    assert d.windowTitle() == "Titel" and gemalt and d.ergebnis() == 42 and kn.text() == "Entfernen"
    kn.click()
    assert d.result() == QDialog.Accepted


# ---- Absatzrahmen: einzelne Seiten ---------------------------------------------------------------------------------------

def test_linie_seiten_im_text_und_alt_kompatibel(app):
    assert Linie.aus_text("#ff0000|1.5|doppelt").seiten == "tblr"                      # alter Text: alle vier Seiten
    assert Linie("#ff0000", 1.5, "doppelt").text() == "#ff0000|1.5|doppelt"
    li = Linie("#000000", 1.0, "einfach", "bh")
    assert li.text() == "#000000|1|einfach|bh" and Linie.aus_text(li.text()) == li
    assert li.mit_seiten("hbt").seiten == "tbh"                                         # feste Reihenfolge


def _absatz_editor(wert):
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    e = DocumentEditor(); e.setPlainText("Eins\nZwei\nDrei"); e.zusatz_binden({})
    e.select_range(0, len("Eins\nZwei\nDrei"))
    e.set_absatzrahmen(wert)
    return e


def test_absatzrahmen_nur_gewaehlte_seiten_in_docx(app, tmp_path):
    import zipfile
    from lunivo_writer.services import docx_reader, docx_writer
    e = _absatz_editor("#1971c2|2.25|gestrichelt|bh")
    out = str(tmp_path / "s.docx")
    docx_writer.write_docx(out, e.document(), e.page, {})
    xml = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert "<w:bottom " in xml and "<w:between " in xml and "<w:top " not in xml and "<w:left " not in xml
    assert 'w:val="dashed"' in xml and 'w:color="1971C2"' in xml
    d2, _, _, _ = docx_reader.read_docx(out)
    from lunivo_writer.editor.zusatz import B_RAHMEN
    b, texte = d2.firstBlock(), []
    while b.isValid():
        if b.blockFormat().hasProperty(B_RAHMEN):
            texte.append(b.blockFormat().stringProperty(B_RAHMEN))
        b = b.next()
    assert texte and all(t == "#1971c2|2.25|gestrichelt|bh" for t in texte)


def test_absatzrahmen_zeichnet_nur_die_gewaehlten_seiten(app):
    from lunivo_writer.editor.pagination import absatzrahmen_zeichnen

    def dunkel(wert):
        e = _absatz_editor(wert)
        bild = QImage(400, 260, QImage.Format_ARGB32); bild.fill(QColor("white"))
        p = QPainter(bild); p.translate(30, 30); absatzrahmen_zeichnen(p, e.document()); p.end()
        return sum(1 for x in range(0, 400) for y in range(0, 260) if bild.pixelColor(x, y).lightness() < 128)
    alle, unten, keine = dunkel("#000000|1|einfach"), dunkel("#000000|1|einfach|b"), dunkel("#000000|1|einfach|")
    assert alle > unten > 0 and keine == 0


def test_rahmenmenue_schaltet_seiten_im_absatz(app, tmp_path):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document()
    e = w.current_editor(); e.insertPlainText("Ein Absatz")
    b = w.befehle
    b._rahmen_seite("unten");  assert e.absatzrahmen().seiten == "b"
    b._rahmen_seite("oben");   assert e.absatzrahmen().seiten == "tb"
    b._rahmen_seite("unten");  assert e.absatzrahmen().seiten == "t"
    b._rahmen_seite("alle");   assert e.absatzrahmen().seiten == "tblrh"
    b._rahmen_seite("aussen"); assert e.absatzrahmen().seiten == "tblr"
    b._rahmen_seite("kein");   assert e.absatzrahmen() is None
    m = b.menue_absatzRahmen()
    assert "Innere vertikale Rahmenlinie" not in [a.text() for a in m.actions()]
    assert "Innere horizontale Rahmenlinie" in [a.text() for a in m.actions()]
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()


def test_rahmendialog_liefert_linie_und_schattierung(app):
    from lunivo_writer.ui.dialogs.rahmen_dialog import AbsatzRahmenDialog
    d = AbsatzRahmenDialog(None, None)
    assert d.ergebnis() == (None, None)
    d.setze_seiten("tb")
    d.linie.setLinie(Linie("#c92a2a", 3.0, "doppelt"))
    d.schatt._uebernehmen(QColor("#fff3bf"))
    li, farbe = d.ergebnis()
    assert li == Linie("#c92a2a", 3.0, "doppelt", "tb") and farbe == "#fff3bf"
    d2 = AbsatzRahmenDialog(None, Linie("#000000", 1.0, "einfach", "lr"), "#d0ebff")
    assert d2.seiten() == "lr" and d2.ergebnis()[1] == "#d0ebff"
    d.show(); d.aktualisieren(); app.processEvents()


# ---- Aufzählung, Nummerierung, Tabellenraster ----------------------------------------------------------------------------

def _fenster(tmp_path):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document()
    return w


def _zu(w):
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()


def test_listenraster_setzt_und_entfernt_listen(app, tmp_path):
    from PySide6.QtGui import QTextListFormat
    w = _fenster(tmp_path)
    e = w.current_editor(); e.insertPlainText("Eins\nZwei")
    r = w.befehle.menue_aufzaehlungKlappe()
    assert set(r.knoepfe) == {"keine", "disc", "circle", "square"} and r.knoepfe["keine"].isChecked()
    r.knoepfe["circle"].click()
    assert e.textCursor().currentList().format().style() == QTextListFormat.ListCircle
    n = w.befehle.menue_nummerierungKlappe()
    assert set(n.knoepfe) == {"keine", "dezimal", "klein", "gross", "roem_klein", "roem_gross"}
    n.knoepfe["roem_gross"].click()
    assert e.textCursor().currentList().format().style() == QTextListFormat.ListUpperRoman
    n2 = w.befehle.menue_nummerierungKlappe()
    assert n2.knoepfe["roem_gross"].isChecked() and not n2.knoepfe["dezimal"].isChecked()
    n2.knoepfe["roem_gross"].click()                       # gleiche Art nochmal: bleibt (kein Umschalten wie beim Knopf)
    assert e.textCursor().currentList() is not None
    n2.knoepfe["keine"].click()
    assert e.textCursor().currentList() is None
    _zu(w)


def test_zellenraster_meldet_zeilen_und_spalten(app, tmp_path):
    from PySide6.QtCore import QPointF
    from lunivo_writer.ui.baukasten import ZellenRaster
    gemeldet = []
    z = ZellenRaster(); z.gewaehlt.connect(lambda a, b: gemeldet.append((a, b)))
    g = z.gitter
    g.setze(*g._zelle_bei(QPointF(3 * g.zelle + 5, 2 * g.zelle + 5)))
    assert g.an == (3, 4) and z.beschriftung.text() == "3 × 4 Tabelle"
    g.setze(0, 0); assert z.beschriftung.text() == "Tabelle einfügen"
    z.waehle(3, 4)
    assert gemeldet == [(3, 4)] and g._zelle_bei(QPointF(-5, 5)) == (0, 0)


def test_tabellenmenue_fuegt_tabelle_ein(app, tmp_path):
    w = _fenster(tmp_path)
    e = w.current_editor(); e.insertPlainText("x")
    m = w.befehle.menue_tabelleKlappe()
    m.waehle(2, 3)
    t = e.textCursor().currentTable()
    assert t is not None and t.rows() == 2 and t.columns() == 3
    assert [a.text() for a in m.actions() if a.text()] == ["Tabelle einfügen …", "Schnelltabelle …"]
    _zu(w)


def test_beschriftungen_ohne_html(app):
    from PySide6.QtCore import Qt
    from lunivo_writer.ui.baukasten import md_escape, md_label, text_label
    t = text_label("<b>kein Markup</b>\nzweite Zeile", fett=True, pt=13)
    assert t.textFormat() == Qt.PlainText and t.text().startswith("<b>") and t.font().bold() and t.font().pointSizeF() == 13
    m = md_label(f"~~{md_escape('a <b> *x*')}~~ → **{md_escape('neu_1')}**")
    assert m.textFormat() == Qt.MarkdownText
    d = __import__("PySide6.QtGui", fromlist=["QTextDocument"]).QTextDocument()
    d.setMarkdown("~~alt~~ → **neu**")
    assert d.toPlainText().strip() == "alt → neu"
    f = d.begin().begin().fragment().charFormat()
    assert f.fontStrikeOut()
    assert md_escape("a*b_c") == "a\\*b\\_c"


def test_ausrichtung_menue_setzt_hoch_und_querformat(app, tmp_path):
    from lunivo_writer.ui.ribbon.ribbon_bar import lade_register
    w = _fenster(tmp_path)
    ed = w.current_editor()
    b = w.befehle
    b.tun("w.setzeQuer:[true]");  assert ed.abschnitt_seite().landscape
    b.tun("w.setzeQuer:[false]"); assert not ed.abschnitt_seite().landscape
    assert "w.setzeQuer:[true]" in str(lade_register()) and "w.setzeQuer:[false]" in str(lade_register())
    _zu(w)


def test_dunkles_system_nutzt_die_lunivo_palette(app, monkeypatch):
    """Bei „Wie das System“ und dunklem System muss der Nebentext (palette(mid)) lesbar bleiben."""
    from PySide6.QtGui import QPalette
    from lunivo_writer.ui import theme
    alt = app.palette()
    try:
        monkeypatch.setattr(theme, "_ist_dunkel", lambda a: a.palette().color(QPalette.Window).lightness() < 128)
        theme._setze(app, "dark")
        assert app.palette().color(QPalette.Mid).name() == "#7c858e" and app.palette().color(QPalette.Window).name() == "#2a2e32"
        # System meldet dunkel: die Standardpalette wird durch die Lunivo-Palette ersetzt
        monkeypatch.setattr(app.style().__class__, "standardPalette", lambda self: app.palette(), raising=False)
        theme._setze(app, "system")
        assert app.palette().color(QPalette.Mid).lightness() > 100
    finally:
        app.setPalette(alt)


def test_dateisymbole_aus_dem_icon_theme(app, monkeypatch):
    from PySide6.QtGui import QIcon, QPixmap
    from lunivo_writer.ui.baukasten import datei_symbole as D
    namen = D.icon_namen(".pdf")
    assert namen[0] == "application-pdf" and "x-office-document" in namen              # MIME-Typ zuerst, dann Rückfälle
    assert D.icon_namen("/home/x/brief.txt")[0] == "text-plain" and D.icon_namen(".odt")[0].startswith("application-vnd.oasis")
    # Das Symbol kommt aus dem Theme des Systems: der erste Name, den es kennt, gewinnt
    pm = QPixmap(8, 8); pm.fill("red"); da = QIcon(pm)
    gefragt = []
    def theme(n):
        gefragt.append(n)
        return da if n == "x-office-document" else QIcon()
    monkeypatch.setattr(QIcon, "fromTheme", staticmethod(theme))
    assert not D.datei_symbol(".pdf").isNull() and gefragt[0] == "application-pdf" and gefragt[-1] == "x-office-document"


def test_speichern_unter_untermenue_mit_formaten(app, tmp_path):
    from lunivo_writer.ui.ribbon.ribbon_bar import lade_register
    reg = lade_register()
    datei = next(m for m in reg["menues"] if m.get("name") == "Datei") if isinstance(reg.get("menues"), list) else None
    punkte = datei["unter"] if datei and "unter" in datei else None
    text = str(reg)
    for ext in (".docx", ".odt", ".doc", ".rtf", ".txt", ".pdf"):
        assert f"'datei': '{ext}'" in text
    w = _fenster(tmp_path)
    ziel = str(tmp_path / "brief.txt")
    gefragt = []
    w._ask_path = lambda tab, titel, only=None: (gefragt.append(only), ziel)[1]
    w.current_editor().setPlainText("Hallo")
    w.befehle.tun('w.speichernAls:[".txt"]')
    assert gefragt == [".txt"] and (tmp_path / "brief.txt").read_text(encoding="utf-8") == "Hallo" and w.current_tab().path == ziel
    _zu(w)
