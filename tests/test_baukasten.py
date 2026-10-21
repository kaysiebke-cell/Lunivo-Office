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


def test_weitere_farben_ueber_das_farbenfenster(app, monkeypatch):
    from lunivo_writer.ui.baukasten.farbwaehler import FarbenDialog
    _sauber()
    monkeypatch.setattr(FarbenDialog, "exec", lambda self: 1)
    monkeypatch.setattr(FarbenDialog, "farbe", lambda self: QColor("#123456"))
    pal = FarbPalette(); erhalten = []
    pal.gewaehlt.connect(erhalten.append)
    pal._weitere()
    assert erhalten[0].name() == "#123456" and F.zuletzt_laden()[0] == "#123456"
    monkeypatch.setattr(FarbenDialog, "exec", lambda self: 0)                    # Abbrechen
    pal._weitere()
    assert len(erhalten) == 1
    _sauber()


def test_farbfeld_uebernimmt_farbe_aus_der_palette(app, monkeypatch):
    feld = FarbFeld("#000000", "Test", keine_text="Keine")
    monkeypatch.setattr(FarbFeld, "_zeige_popup", lambda self, pal: pal.waehle(QColor("#2f9e44")))
    gemeldet = []
    feld.farbeGeaendert.connect(gemeldet.append)
    feld.click()
    assert feld.farbe == "#2f9e44" and gemeldet == ["#2f9e44"] and feld.text() == "#2F9E44" and feld.icon().pixmap(14, 14).toImage().pixelColor(7, 7).name() == "#2f9e44"
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


def test_rahmenfenster_liefert_linie_schattierung_und_seitenrand(app):
    from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog
    d = RahmenSchattierungDialog(None)
    assert d.rahmen() is None and d.schattierung() == (None, None) and d.seitenrand() is None
    d.p_rahmen.einstellung["kontur"].click()
    assert d.rahmen().seiten == "tblr"
    d.p_rahmen.kantenknoepfe["l"].toggle(); d.p_rahmen.kantenknoepfe["r"].toggle()
    assert d.rahmen().seiten == "tb" and d.p_rahmen.einstellung["anpassen"].isChecked()
    d.p_rahmen.einstellung["alle"].click()
    assert d.rahmen().seiten == "tblrh"
    d.p_schatt.fuell._uebernehmen(QColor("#fff3bf"))
    d.p_schatt.art.setCurrentIndex(d.p_schatt.art.findData("pct25"))
    assert d.schattierung() == ("#fff3bf", ("pct25", "#000000"))
    d.p_rand.einstellung["kontur"].click()
    assert d.seitenrand()["art"] == "einfach" and d.seitenrand()["abstand_mm"] == 8.0
    d2 = RahmenSchattierungDialog(None, rahmen=Linie("#000000", 1.0, "einfach", "lr"), fuell="#d0ebff", seite="schattierung")
    assert d2.rahmen().seiten == "lr" and d2.schattierung() == ("#d0ebff", None) and d2.reiter.currentIndex() == 2
    d.show(); app.processEvents()


def test_muster_kacheln_und_ooxml(app):
    from lunivo_writer.editor import muster as M
    assert len(M.MUSTER) == 37 and M.ooxml_von("pct12_5") == "pct12" and M.schluessel_von_ooxml("diagCross") == "dunkel_karo"
    assert M.aus_text(M.als_text("pct50", "#ff0000", None)) == ("pct50", "#ff0000", None)
    k = M.kachel("pct50", "#000000", "#ffffff").toImage()
    schwarz = sum(1 for y in range(8) for x in range(8) if k.pixelColor(x, y).name() == "#000000")
    assert schwarz == 32                                                           # 50 % von 64


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


def test_farbenfenster_wege_zur_selben_farbe(app):
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor
    from lunivo_writer.ui.baukasten.farbwaehler import FarbenDialog, _Flaeche, _Leiste, _Regler, _Ring
    d = FarbenDialog(None, QColor("#2f6fb5"), "Schriftfarbe")
    assert d.farbe().name() == "#2f6fb5"
    reg = d.findChildren(_Regler)[0]
    reg.hex.setText("#ff8800"); reg._hex()
    assert d.farbe().name() == "#ff8800" and reg.werte() == (255, 136, 0)
    ring = d.findChildren(_Ring)[0]
    ring._ziehen = "ring"; ring._wirke(QPointF(ring.mitte.x() + 100, ring.mitte.y()))      # drei Uhr = Farbton 90°
    assert abs(d.m.h - 0.25) < 0.01
    d.findChildren(_Leiste)[0]._setze(QPointF(5, 214))                                      # ganz unten = schwarz
    assert d.farbe().name() == "#000000"
    d.findChildren(_Flaeche)[0]._setze(QPointF(0, 0))                                       # links oben = Rot, voll
    d.findChildren(_Leiste)[0]._setze(QPointF(5, 0))
    assert d.farbe().name() == "#ff0000"


def test_seitenrand_einzelne_kanten_und_docx(app, tmp_path):
    from PySide6.QtCore import QPoint, QSettings, Qt
    from PySide6.QtTest import QTest
    from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog
    d = RahmenSchattierungDialog(None, seite="seitenrand"); d.show()
    r = d.p_rand
    assert all(b.isEnabled() for b in r.kantenknoepfe.values())                    # alle vier Kanten sind anklickbar
    r.kantenknoepfe["l"].click(); r.kantenknoepfe["b"].click()
    assert d.seitenrand()["seiten"] == "bl"
    v = r.vorschau; a = max(4.0, r.abstand_mm * 1.2)
    QTest.mouseClick(v, Qt.LeftButton, Qt.NoModifier, QPoint(int(v.width() - a), v.height() // 2))   # Klick auf die rechte Kante
    assert d.seitenrand()["seiten"] == "blr"
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document(); e = w.current_editor()
    w.befehle._seite_aendern(border=d.seitenrand())
    pfad = str(tmp_path / "r.docx"); w.current_tab().path = pfad; w.save()
    geladen = w.dokumente.laden(pfad)
    assert geladen.page.border["seiten"] == "blr"
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()


def test_galerie_meldet_gewaehlt_und_ueberfahren(app):
    from PySide6.QtGui import QFont
    from lunivo_writer.ui.baukasten import GalerieAuswahl
    g = GalerieAuswahl(None, titel="Stile")
    f = QFont("Liberation Sans"); f.setPointSizeF(20)
    g.kachel("a", "Eins", f, probe="AaBbCcD"); g.kachel("b", "Zwei", QFont("Liberation Sans"))
    seen, gewaehlt, weg = [], [], []
    g.ueberfahren.connect(seen.append); g.gewaehlt.connect(gewaehlt.append); g.verlassen.connect(lambda: weg.append(1))
    k = g.kacheln["a"]
    assert k.schrift.pointSizeF() < 20                                        # große Probe wird in die Kachel eingepasst
    k.darueber.emit("a"); k.weg.emit(); k.klick.emit("b")
    assert seen == ["a"] and weg == [1] and gewaehlt == ["b"]


def test_schriftart_fenster_werte_und_format(app):
    from lunivo_writer.ui.baukasten.schriftart_dialog import SchriftartDialog
    from lunivo_writer.ui.baukasten.text_format import aus_format, zu_format
    d = SchriftartDialog(None, {"schrift": "Liberation Sans", "groesse": 12.0})
    d.schnitt.setze("Fett Kursiv"); d.groesse.setze("18")
    d.unter.setCurrentIndex(d.unter.findData("gepunktet")); d.cb["durch"].setChecked(True); d.cb["hoch"].setChecked(True)
    d.cb["tief"].setChecked(True)                                                   # Hoch- und Tiefgestellt schließen sich aus
    w = d.werte()
    assert w["fett"] and w["kursiv"] and w["groesse"] == 18 and w["unter"] == "gepunktet" and w["tief"] and not w["hoch"]
    f = zu_format(w)
    assert f.fontWeight() >= 600 and f.fontItalic() and f.fontStrikeOut() and f.fontPointSize() == 18
    w2 = aus_format(f)
    assert w2["unter"] == "gepunktet" and w2["durch"] and w2["tief"] and w2["kerning"]
    v = SchriftartDialog(None, {"schrift": "Liberation Sans"}, umfang="vorlage")
    assert v.reiter.count() == 1 and not v.effekte.isVisibleTo(v)                   # in der Vorlage nur Schrift, Schnitt, Größe, Farbe


def test_formatvorlage_rahmen_und_schattierung(app):
    from lunivo_writer.editor import stile
    from lunivo_writer.editor.linie import Linie
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    li = Linie("#336699", 1.0, "einfach", "tblr")
    d = FormatvorlageDialog(None, start={"rahmen": li.text(), "fuell": "#d0ebff"}, vorlagen=["Standard"])
    erg = d.ergebnis()
    assert erg["rahmen"] == li.text() and erg["fuell"] == "#d0ebff" and erg["muster"] == ""
    assert stile.anlegen("RahmenTest", **{k: v for k, v in erg.items() if k not in ("name", "basis", "folge")}) is None
    e = DocumentEditor(); e.setPlainText("x")
    e._stil_auf_block(e.document().firstBlock(), "RahmenTest")
    assert e.absatzrahmen() is not None and e.absatzschatten()[0] == "#d0ebff"
    stile.loeschen("RahmenTest")


def test_listenfenster_und_formatvorlage_liste(app):
    from PySide6.QtCore import QSettings
    from lunivo_writer.editor import listen as L
    from lunivo_writer.editor import stile
    from lunivo_writer.ui.baukasten.liste_dialog import ListenDialog, NummerierungAnpassenDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    n = NummerierungAnpassenDialog(None, L.liste("roem_klein", "(", ")", 3))
    assert n.spec() == L.liste("roem_klein", "(", ")", 3)
    n.format.setText("Nr.")
    assert n.spec() is None and not n.ok.isEnabled()
    d = ListenDialog(None, L.liste("klein", "", ")"), seite="nummerierung")
    assert d.ergebnis() == L.liste("klein", "", ")") and d.reiter.currentWidget() is d.r_zahlen
    d.r_punkte.setCurrentRow(0); d.reiter.setCurrentWidget(d.r_punkte)
    assert d.ergebnis() is None
    e = DocumentEditor(); e.setPlainText("a\nb\nc")
    e.set_liste(L.liste("dezimal", "", ")", 4))
    assert e.liste_spec() == L.liste("dezimal", "", ")", 4)
    e.set_liste(None)
    assert e.liste_spec() is None
    assert L.aus_text(L.als_text(L.liste("gross", "(", ")", 2))) == L.liste("gross", "(", ")", 2)
    stile.anlegen("ListeTest", liste=L.als_text(L.liste("dezimal", "", ")")))
    e2 = DocumentEditor(); e2.setPlainText("x\ny")
    for b in (e2.document().firstBlock(), e2.document().firstBlock().next()):
        e2._stil_auf_block(b, "ListeTest")
    assert e2.document().firstBlock().textList() is e2.document().firstBlock().next().textList() or \
        e2.document().firstBlock().textList().count() == 2
    stile.loeschen("ListeTest")
    QSettings().remove("listen/benutzer")


def test_nummerierung_schriftart(app):
    from lunivo_writer.editor import listen as L
    from lunivo_writer.ui.baukasten.liste_dialog import NummerierungAnpassenDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    n = NummerierungAnpassenDialog(None, None)
    assert hasattr(n, "schrift") and n.spec().get("zeichen") is None
    n._zeichen = {"fett": True, "farbe": "#c92a2a"}
    s = n.spec()
    assert s["zeichen"] == {"fett": True, "farbe": "#c92a2a"} and L.aus_text(L.als_text(s)) == s
    e = DocumentEditor(); e.setPlainText("a\nb")
    e.set_liste(s)
    assert e.document().firstBlock().charFormat().fontWeight() >= 600 or e.document().firstBlock().blockFormat() is not None
    assert e.document().firstBlock().textList().format().style() == L.STILE["dezimal"][2]


def test_gliederung_mehrstufig(app):
    from PySide6.QtGui import QImage, QPainter, QTextCursor
    from lunivo_writer.editor import listen as L
    from lunivo_writer.editor import mehrstufig as M
    from lunivo_writer.editor.pagination import absatz_zusatz_zeichnen
    from lunivo_writer.ui.baukasten.liste_dialog import GliederungAnpassenDialog, ListenDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    assert [M.nummer_text("roem_klein", n) for n in (1, 4, 9)] == ["i", "iv", "ix"] and M.nummer_text("klein", 27) == "aa"
    g = M.VORLAGEN[0][1]
    z = [0] * 9
    erg = []
    for n in (1, 2, 2, 3, 1, 2):
        M.zaehlen(z, g, n); erg.append(M.nummer_der_ebene(g, z, n))
    assert erg == ["1.", "1.1.", "1.2.", "1.2.1.", "2.", "2.1."]
    assert L.aus_text(L.als_text(g)) == g
    e = DocumentEditor(); e.setPlainText("A\nB\nC")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e.set_liste(g)
    c = QTextCursor(e.document().findBlockByNumber(1)); e.setTextCursor(c); e.list_level(1)
    assert [x[1] for x in M.nummern(e.document())] == ["1.", "1.1.", "2."]
    assert e.liste_spec() == g
    img = QImage(300, 300, QImage.Format_RGB32); p = QPainter(img)
    absatz_zusatz_zeichnen(p, e.document()); p.end()
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e.set_liste(None)
    assert M.nummern(e.document()) == []
    d = GliederungAnpassenDialog(None, g)
    d.ebenen.setCurrentRow(1); d.format.setText("x"); d._lesen()
    assert not d.ok.isEnabled()
    d.format.setText("①-②"); d._lesen()
    assert d.ok.isEnabled() and d.defn()["ebenen"][1]["format"] == "①-②"
    ld = ListenDialog(None, g)
    assert ld.ergebnis() == g and ld.reiter.currentWidget() is ld.r_gl


def test_formatvorlage_verknuepfung(app):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeySequence
    from lunivo_writer.editor import stile
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.baukasten.tasten_dialog import TastenDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    t = TastenDialog(None, "Ctrl+Alt+7", belegt=lambda k: "Fett" if k == "Ctrl+B" else None)
    assert t.taste() == "Ctrl+Alt+7" and t.zuweisen.isEnabled()
    t.feld.setKeySequence(QKeySequence("Ctrl+B"))
    assert not t.zuweisen.isEnabled() and "Fett" in t.hinweis.text()
    d = FormatvorlageDialog(None, start={"taste": "Ctrl+Alt+7"}, vorlagen=["Standard"])
    assert d.ergebnis()["taste"] == "Ctrl+Alt+7"
    assert stile.anlegen("TastenTest", **{k: v for k, v in d.ergebnis().items() if k not in ("name", "basis", "folge")}) is None
    assert stile.anlegen("TastenKind", basis="TastenTest") is None and stile.definition("TastenKind")["taste"] == ""
    e = DocumentEditor(); e.stil_tasten()
    assert [s.key().toString(QKeySequence.PortableText) for s in e._stil_kurz] == ["Ctrl+Alt+7"]
    stile.loeschen("TastenTest"); stile.loeschen("TastenKind")


def test_texteffekte(app):
    from PySide6.QtCore import Qt
    from lunivo_writer.editor import stile, texteffekt as T
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = TexteffektDialog(None, {"farbe": "#c92a2a", "transparenz": 40, "kontur": True, "kontur_farbe": "#1864ab", "kontur_breite": 1.5,
                                "kontur_art": "gestrichelt"})
    w = d.werte()
    assert w["kontur"] and w["transparenz"] == 40 and w["kontur_art"] == "gestrichelt" and w["kontur_breite"] == 1.5
    f = T.zu_format(w)
    assert f.textOutline().style() == Qt.DashLine and round(f.foreground().color().alphaF(), 1) == 0.6
    assert T.aus_format(f)["kontur_farbe"] == "#1864ab" and T.aus_format(f)["transparenz"] == 40
    d.r_keine.setChecked(True)
    assert T.zu_format(d.werte()).foreground().color().alpha() == 0 and not d.farbe.isEnabled()
    t = T.als_text(w)
    assert T.aus_text(t, "#c92a2a")["kontur_art"] == "gestrichelt" and T.als_text(dict(T.EFFEKT)) == ""
    fd = FormatvorlageDialog(None, start={"effekt": t, "farbe": "#c92a2a"}, vorlagen=["Standard"])
    erg = fd.ergebnis()
    assert erg["effekt"] == t
    stile.anlegen("EffektTest", **{k: v for k, v in erg.items() if k not in ("name", "basis", "folge")})
    e = DocumentEditor(); e.setPlainText("x")
    e._stil_auf_block(e.document().firstBlock(), "EffektTest")
    cf = e.document().firstBlock().begin().fragment().charFormat()
    assert cf.textOutline().style() == Qt.DashLine
    stile.loeschen("EffektTest")
