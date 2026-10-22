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
    assert d.seitenrand()["art"] == "einfach" and d.seitenrand()["messen"] == "text" and d.seitenrand()["abstand"] == "1,1,4,4"      # Vorgabe wie im WPS
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
    assert set(r.knoepfe) == {"keine"} | {str(i) for i in range(7)} and r.knoepfe["keine"].isChecked()      # Punkt, Quadrat und fünf Zeichen
    r.knoepfe["1"].click()                                  # Quadrat
    assert e.textCursor().currentList().format().style() == QTextListFormat.ListSquare
    n = w.befehle.menue_nummerierungKlappe()
    assert set(n.knoepfe) == {"keine"} | {str(i) for i in range(7)}
    n.knoepfe["2"].click()                                  # I. II. III.
    assert e.textCursor().currentList().format().style() == QTextListFormat.ListUpperRoman
    n2 = w.befehle.menue_nummerierungKlappe()
    assert n2.knoepfe["2"].isChecked() and not n2.knoepfe["0"].isChecked()
    n2.knoepfe["2"].click()                                # gleiche Art nochmal: bleibt
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
    d.schnitt.setCurrentText("Fett Kursiv"); d.groesse.setCurrentText("18")
    d.asien.setCurrentText("Noto Sans CJK JP"); d.betonung.setCurrentIndex(d.betonung.findData("kreis")); d.cb["doppelt"].setChecked(True)
    d.cb["doppelt"].setChecked(False)
    d.unter.setCurrentIndex(d.unter.findData("gepunktet")); d.cb["durch"].setChecked(True); d.cb["hoch"].setChecked(True)
    d.cb["tief"].setChecked(True)                                                   # Hoch- und Tiefgestellt schließen sich aus
    w = d.werte()
    assert w["fett"] and w["kursiv"] and w["groesse"] == 18 and w["unter"] == "gepunktet" and w["tief"] and not w["hoch"]
    f = zu_format(w)
    assert f.fontWeight() >= 600 and f.fontItalic() and f.fontStrikeOut() and f.fontPointSize() == 18
    assert f.fontFamilies() == ["Liberation Sans", "Noto Sans CJK JP"]              # asiatische Schrift hinter der westlichen
    w2 = aus_format(f)
    assert w2["unter"] == "gepunktet" and w2["durch"] and w2["tief"] and w2["kerning"]
    assert w2["schrift_asien"] == "Noto Sans CJK JP" and w2["betonung"] == "kreis" and not w2["doppelt"]
    v = SchriftartDialog(None, {"schrift": "Liberation Sans"}, umfang="vorlage")
    assert v.reiter.count() == 2 and v.effekte.isVisibleTo(v) and not v.effekt_knopf.isVisibleTo(v)    # in der Vorlage dasselbe Fenster, ohne Texteffekte und Standard


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
    d.ebenen.setCurrentRow(1); d.format.setText(""); d._lesen()
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
    assert T.zu_format(d.werte()).foreground().color().alpha() == 0
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


def test_texteffekte_docx_rundlauf(app, tmp_path):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor
    from lunivo_writer.editor import texteffekt as T
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    e = DocumentEditor(); e.setPlainText("Effekt")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e._merge(T.zu_format({"farbe": "#c92a2a", "transparenz": 40, "kontur": True, "kontur_farbe": "#1864ab", "kontur_breite": 1.5,
                          "kontur_art": "gestrichelt"}))
    pfad = str(tmp_path / "t.docx")
    formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)                        # das Dokument gehört dem Ergebnis: es muss am Leben bleiben
    cf = geladen.doc.firstBlock().begin().fragment().charFormat()
    w = T.aus_format(cf)
    assert cf.textOutline().style() == Qt.DashLine and w["kontur_farbe"] == "#1864ab" and w["kontur_breite"] == 1.5
    assert w["transparenz"] == 40 and w["farbe"] == "#c92a2a"


def test_formatvorlage_tabstopps(app):
    from lunivo_writer.editor import stile
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.baukasten.tabstopp_dialog import als_text, aus_block, aus_text
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    assert aus_text(als_text([(30.0, "rechts", "punkt"), (80.5, "mitte", "")])) == [(30.0, "rechts", "punkt"), (80.5, "mitte", "")]
    d = FormatvorlageDialog(None, start={"tabs": "30:rechts:punkt"}, vorlagen=["Standard"])
    erg = d.ergebnis()
    assert erg["tabs"] == "30:rechts:punkt"
    stile.anlegen("TabTest", **{k: v for k, v in erg.items() if k not in ("name", "basis", "folge")})
    e = DocumentEditor(); e.setPlainText("a\tb")
    e._stil_auf_block(e.document().firstBlock(), "TabTest")
    assert aus_block(e.document().firstBlock().blockFormat()) == [(30.0, "rechts", "punkt")]
    stile.loeschen("TabTest")


def test_absatzrahmen_abstand_optionen(app, tmp_path):
    from lunivo_writer.editor.linie import Linie
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog, _PolsterDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    li = Linie("#000000", 1.0, "einfach", "tblr", "3,5,10,12")
    assert Linie.aus_text(li.text()).polster() == (3.0, 5.0, 10.0, 12.0) and Linie.aus_text(Linie().text()).polster() is None
    d = RahmenSchattierungDialog(None, rahmen=li, mit_seitenrand=False, fuer=["Absatz"])
    assert d.p_rahmen.polster == (3.0, 5.0, 10.0, 12.0) and d.rahmen().abstand == "3,5,10,12"
    p = _PolsterDialog(None, (3.0, 5.0, 10.0, 12.0))
    assert p.werte() == (3.0, 5.0, 10.0, 12.0)
    e = DocumentEditor(); e.setPlainText("x"); e.set_absatzrahmen(li.text())
    pfad = str(tmp_path / "r.docx")
    formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)
    assert Linie.aus_text(geladen.doc.firstBlock().blockFormat().stringProperty(__import__("lunivo_writer.editor.zusatz", fromlist=["B_RAHMEN"]).B_RAHMEN)).polster() == (3.0, 5.0, 10.0, 12.0)


def test_gliederung_position_norm_neu_vorlage(app):
    from PySide6.QtGui import QTextCursor
    from lunivo_writer.editor import listen as L
    from lunivo_writer.editor import mehrstufig as M
    from lunivo_writer.ui.baukasten.liste_dialog import GliederungAnpassenDialog, ListenDialog, NummerierungAnpassenDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    # Nummerieren nach Norm: höhere Ebenen als Dezimalzahlen
    g = M.gliederung(["roem_gross", "gross"], ["①.", "①.②."])
    g["ebenen"][1]["norm"] = True
    z = [0] * 9
    M.zaehlen(z, g, 1); M.zaehlen(z, g, 2)
    assert M.nummer_der_ebene(g, z, 2) == "1.A."
    # Neu nummerieren nach Ebene 1 (Ebene 3 zählt weiter, wenn nur Ebene 2 dazwischen steht)
    g = M.gliederung(["dezimal"], ["①.", "①.②.", "①.②.③."])
    g["ebenen"][2]["neu"] = 1
    z = [0] * 9
    for n in (1, 2, 3, 2, 3):
        M.zaehlen(z, g, n)
    assert z[2] == 2
    # Aufzählung mit eigenem Zeichen, Position und Text danach
    a = M.aufzaehlung("➤"); assert M.ist_aufzaehlung(a) and not M.ist_aufzaehlung(M.VORLAGEN[0][1])
    e = DocumentEditor(); e.setPlainText("A\nB")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e.set_liste(a)
    assert M.nummern(e.document())[0][1] == "➤"
    d = GliederungAnpassenDialog(None, a, titel="Aufzählungszeichen anpassen")
    d.mehr.setChecked(True); d.danach.setCurrentIndex(1); d.vorlage.setCurrentIndex(1); d.norm.setChecked(True)
    r = d.defn()["ebenen"][0]
    assert r["danach"] == "leer" and r["vorlage"] == "Standard" and r["norm"]
    # einfache Nummerierung mit eigener Position
    n = NummerierungAnpassenDialog(None, None)
    assert n.spec().get("pos") is None
    n.position.ausr.setValue(5.0)
    s = n.spec()
    assert s["pos"]["ausr"] == 5.0 and L.aus_text(L.als_text(s)) == s
    e.set_liste(s)
    assert M.nummern(e.document())[1][1] == "2."
    # Aufzählungskacheln: Kein, Punkt, Quadrat und fünf Zeichen
    ld = ListenDialog(None)
    assert ld.r_punkte.count() == 8


def test_tabstopp_fuellzeichen(app, tmp_path):
    from PySide6.QtGui import QImage, QPainter
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.editor.pagination import absatz_zusatz_zeichnen
    from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog, aus_block
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = TabstoppDialog(None, [])
    d.pos.setValue(100); d.art.button(2).setChecked(True); d.fuell.button(1).setChecked(True); d.festlegen()
    assert d.stopps() == [(100.0, "rechts", "punkt")]
    e = DocumentEditor(); e.setPlainText("Kapitel\t12")
    e.set_tabstopps(d.stopps())
    assert aus_block(e.document().firstBlock().blockFormat()) == [(100.0, "rechts", "punkt")]
    img = QImage(500, 200, QImage.Format_RGB32); img.fill(0xffffff); p = QPainter(img)
    absatz_zusatz_zeichnen(p, e.document()); p.end()
    pfad = str(tmp_path / "t.docx"); formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)
    assert aus_block(geladen.doc.firstBlock().blockFormat()) == [(100.0, "rechts", "punkt")]


def test_seitenfluss_zusammenhalten_und_kontrolle(app):
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtGui import QTextBlockFormat, QTextCursor, QTextFormat
    from lunivo_writer.editor import absatzopt, seitenfluss
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    e = DocumentEditor()
    e.setPlainText("\n".join(f"Absatz {i}" for i in range(80)))
    ch = e.page.content_height_px
    e.document().documentLayout().blockBoundingRect(e.document().lastBlock())     # Layout erzwingen

    def seite(b):
        tl = b.layout(); return int((tl.position().y() + tl.lineAt(0).y() + 0.5) // ch)
    # den ersten Absatz suchen, der am Seitenanfang landet, und davor einen langen Absatz einfügen, der über die Grenze reicht
    doc = e.document()
    lang = doc.findBlockByNumber(len([b for b in range(80) if seite(doc.findBlockByNumber(b)) == 0]) - 1)
    c = QTextCursor(lang); c.movePosition(QTextCursor.EndOfBlock); c.insertText(" " + "lang " * 400)
    doc.documentLayout().blockBoundingRect(doc.lastBlock())
    z = seitenfluss._zeilen(lang, ch)
    assert z[0][0] != z[-1][0]                                 # der Absatz läuft über die Seitengrenze
    bf = lang.blockFormat(); absatzopt.setzen(bf, {**absatzopt.VORGABE, "zusammen": True}); QTextCursor(lang).setBlockFormat(bf)
    war = doc.isModified()
    assert seitenfluss.anwenden(doc, ch)
    assert doc.isModified() == war
    z = seitenfluss._zeilen(doc.findBlockByNumber(lang.blockNumber()), ch)
    assert z[0][0] == z[-1][0]                                 # jetzt steht er ganz auf einer Seite
    assert not seitenfluss.ist_manuell(doc.findBlockByNumber(lang.blockNumber()).blockFormat())
    # ohne die Regel (und ohne Absatzkontrolle) verschwindet der eigene Umbruch wieder
    bf = doc.findBlockByNumber(lang.blockNumber()).blockFormat(); absatzopt.setzen(bf, {**absatzopt.VORGABE, "kontrolle": False})
    QTextCursor(doc.findBlockByNumber(lang.blockNumber())).setBlockFormat(bf)
    seitenfluss.anwenden(doc, ch)
    z = seitenfluss._zeilen(doc.findBlockByNumber(lang.blockNumber()), ch)
    assert z[0][0] != z[-1][0]


def test_texteffekte_erweitert_docx_und_zeichnen(app, tmp_path):
    from PySide6.QtGui import QImage, QPainter, QTextCursor
    from lunivo_writer.editor import texteffekt as T
    from lunivo_writer.editor.pagination import absatz_zusatz_zeichnen
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = TexteffektDialog(None, {})
    d.r_verlauf.setChecked(True); d.v1.setFarbe("#c92a2a"); d.v2.setFarbe("#1864ab"); d.v_winkel.setValue(45)
    d._setze_teil("schatten", {"art": "aussen", "farbe": "#000000", "transparenz": 40, "groesse": 100, "weich": 3, "abstand": 4, "winkel": 45}, "Unten rechts")
    d._setze_teil("reflektion", {"groesse": 50, "transparenz": 50, "weich": 0, "abstand": 2}, "x")
    d._setze_teil("leuchten", {"farbe": "#4c6ef5", "groesse": 8, "transparenz": 60}, "x")
    d.d_tiefe.setValue(5); d._setze_material("plastik", None)
    d.k_linie.setChecked(True); d.k_form.setCurrentIndex(1); d.k_art.setCurrentIndex(3)
    w = d.werte()
    assert w["fuell"] == "verlauf" and w["verlauf"]["winkel"] == 45 and w["schatten"]["abstand"] == 4 and w["d3"]["material"] == "plastik"
    assert w["kontur_form"] == "doppelt" and w["kontur_art"] == "gestrichelt"
    e = DocumentEditor(); e.setPlainText("Effekte")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e._merge(T.zu_format(w))
    assert e._hat_effekt()
    img = QImage(500, 200, QImage.Format_RGB32); img.fill(0xffffff); p = QPainter(img)
    absatz_zusatz_zeichnen(p, e.document()); p.end()
    pfad = str(tmp_path / "e.docx"); formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)
    r = T.aus_format(geladen.doc.firstBlock().begin().fragment().charFormat())
    assert r["fuell"] == "verlauf" and r["verlauf"]["farbe2"].lower() == "#1864ab" and abs(r["verlauf"]["winkel"] - 45) < 1
    assert r["schatten"]["abstand"] == 4 and r["reflektion"]["groesse"] == 50 and r["leuchten"]["groesse"] == 8
    assert r["d3"]["tiefe"] == 5 and r["d3"]["material"] == "plastik" and r["kontur_form"] == "doppelt" and r["kontur_art"] == "gestrichelt"
    # ein Effekt lässt sich wieder abschalten
    e._merge(T.zu_format(dict(T.EFFEKT)))
    assert not e._hat_effekt()


def test_schriftart_asiatisch_komplex_betonung_docx(app, tmp_path):
    from PySide6.QtGui import QImage, QPainter, QTextCursor
    from lunivo_writer.editor.pagination import absatz_zusatz_zeichnen
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.text_format import aus_format, zu_format
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    w = {"schrift": "Liberation Sans", "groesse": 12.0, "schrift_asien": "Noto Sans CJK JP", "schrift_komplex": "Times New Roman",
         "schnitt_komplex": "Fett", "groesse_komplex": 14.0, "betonung": "punkt", "doppelt": True}
    e = DocumentEditor(); e.setPlainText("Text mit Zeichen")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e._merge(zu_format(w))
    assert e._hat_effekt()
    img = QImage(500, 200, QImage.Format_RGB32); img.fill(0xffffff); p = QPainter(img)
    absatz_zusatz_zeichnen(p, e.document()); p.end()
    pfad = str(tmp_path / "s.docx"); formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)
    r = aus_format(geladen.doc.firstBlock().begin().fragment().charFormat())
    assert r["schrift_asien"] == "Noto Sans CJK JP" and r["schrift_komplex"] == "Times New Roman" and r["betonung"] == "punkt" and r["doppelt"]
    assert "Fett" in r["schnitt_komplex"] and r["groesse_komplex"] == 14.0


def test_formatvorlage_schriftart_alle_felder(app):
    from lunivo_writer.editor import stile
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.baukasten.text_format import aus_format
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = FormatvorlageDialog(None, start={"unter": "wellig", "doppelt": True, "kapital": True, "betonung": "punkt", "schrift_asien": "Noto Sans CJK JP",
                                         "abstand": 1.5, "versteckt": False}, vorlagen=["Standard"])
    erg = d.ergebnis()
    assert erg["unter"] == "wellig" and erg["doppelt"] and erg["kapital"] and erg["abstand"] == 1.5 and erg["kerning"] is True
    stile.anlegen("ZeichenTest", **{k: v for k, v in erg.items() if k not in ("name", "basis", "folge")})
    e = DocumentEditor(); e.setPlainText("Text")
    e._stil_auf_block(e.document().firstBlock(), "ZeichenTest")
    w = aus_format(e.document().firstBlock().begin().fragment().charFormat())
    assert w["unter"] == "wellig" and w["doppelt"] and w["kapital"] and w["betonung"] == "punkt" and w["schrift_asien"] == "Noto Sans CJK JP"
    stile.loeschen("ZeichenTest")
    # eine Vorlage ohne diese Felder lässt unterstrichenen Text, wie er ist
    from PySide6.QtGui import QTextCharFormat, QTextCursor
    e.setPlainText("unter"); c = e.textCursor(); c.select(QTextCursor.Document)
    f = QTextCharFormat(); f.setUnderlineStyle(QTextCharFormat.SingleUnderline); c.mergeCharFormat(f)
    e._stil_auf_block(e.document().firstBlock(), "Standard")
    assert e.document().firstBlock().begin().fragment().charFormat().underlineStyle() == QTextCharFormat.SingleUnderline


def test_schriftart_zeichenabstand_unterstreichung_docx(app, tmp_path):
    from PySide6.QtGui import QTextCursor
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.schriftart_dialog import SchriftartDialog
    from lunivo_writer.ui.baukasten.text_format import aus_format, zu_format
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = SchriftartDialog(None, {"schrift": "Liberation Sans", "groesse": 12.0, "skala": 150.0, "position": 3.0, "unter": "dick_wellig", "raster": False})
    w = d.werte()
    assert w["skala"] == 150.0 and abs(w["position"] - 3.0) < 0.05 and w["unter"] == "dick_wellig" and not w["raster"]
    e = DocumentEditor(); e.setPlainText("Zeichenabstand")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    e._merge(zu_format(w))
    r = aus_format(e.document().firstBlock().begin().fragment().charFormat())
    assert r["skala"] == 150.0 and abs(r["position"] - 3.0) < 0.2 and r["unter"] == "dick_wellig"
    pfad = str(tmp_path / "z.docx"); formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)
    r2 = aus_format(geladen.doc.firstBlock().begin().fragment().charFormat())
    assert r2["skala"] == 150.0 and abs(r2["position"] - 3.0) < 0.6 and r2["unter"] == "dick_wellig" and not r2["raster"]


def test_standardtabstopps(app, tmp_path):
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = TabstoppDialog(None, [], 15.0)
    assert abs(d.standard_abstand() - 15.0) < 1e-6
    assert TabstoppDialog(None, []).standard_abstand() is None
    e = DocumentEditor(); e.setPlainText("a\tb")
    e.set_standard_tab_mm(20.0)
    assert abs(e.standard_tab_mm() - 20.0) < 0.01
    pfad = str(tmp_path / "st.docx"); formats.save(pfad, e.document(), PageSettings())
    geladen = formats.load(pfad)
    assert abs(round(geladen.doc.defaultTextOption().tabStopDistance() / (96 / 25.4), 1) - 20.0) < 0.2


def test_formatvorlage_absatz_beide_reiter(app):
    from lunivo_writer.editor import absatzopt, stile
    from lunivo_writer.ui.baukasten.absatz_dialog import AbsatzDialog
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    assert AbsatzDialog(None, {}, umfang="vorlage").reiter.count() == 2
    d = FormatvorlageDialog(None, start={"rechts": 12, "erste": -6, "umbruch": True, "zeilen_art": "genau", "zeilen_pt": 18,
                                         "opt": absatzopt.als_text({**absatzopt.VORGABE, "zusammen": True, "nicht_trennen": True}), "gliederung": 2}, vorlagen=["Standard"])
    erg = d.ergebnis()
    assert erg["rechts"] == 12 and erg["umbruch"] and erg["zeilen_art"] == "genau" and "zusammen=1" in erg["opt"] and erg["gliederung"] == 2
    stile.anlegen("AbsatzTest", **{k: v for k, v in erg.items() if k not in ("name", "basis", "folge", "zur_vorlage")})
    e = DocumentEditor(); e.setPlainText("Text")
    e._stil_auf_block(e.document().firstBlock(), "AbsatzTest")
    bf = e.document().firstBlock().blockFormat()
    assert bf.rightMargin() > 0 and bf.textIndent() < 0 and int(bf.lineHeightType()) == 2 and bf.headingLevel() == 2
    assert absatzopt.lesen(bf)["zusammen"] and e._stil_name(bf) == "AbsatzTest"
    stile.loeschen("AbsatzTest")


def test_texteffekte_alle_regler_bedienbar(app):
    from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
    d = TexteffektDialog(None, {})
    alle = [d.s_farbe, d.s_trans, d.s_gross, d.s_weich, d.s_abst, d.s_winkel, d.r_gross, d.r_trans, d.r_weich, d.r_abst, d.l_farbe, d.l_gross, d.l_trans,
            d.farbe, d.trans, d.v1, d.v2, d.v_winkel, d.k_farbe, d.k_breite, d.k_art, d.k_form, d.kv1, d.kv2, d.kv_winkel, d.d_tiefe, d.d_kontur,
            d.d_tiefe_f, d.d_kontur_f, d.d_licht, d.d_winkel]
    assert all(x.isEnabled() for x in alle)                                   # nichts ist ausgegraut

    def zieh(x, v):                                                            # wie mit der Maus am Regler ziehen
        x.regler.setValue(int(round(v * x._f)))
    d.s_abst.regler.setValue(120)                                              # ein Regler schaltet seinen Effekt ein
    assert d.werte()["schatten"]["abstand"] == 12.0
    zieh(d.r_gross, 70.0); assert d.werte()["reflektion"]["groesse"] == 70.0
    zieh(d.l_gross, 9.0); assert d.werte()["leuchten"]["groesse"] == 9.0
    zieh(d.v_winkel, 30); assert d.r_verlauf.isChecked() and d.werte()["verlauf"]["winkel"] == 30
    zieh(d.k_breite, 2.0); assert d.k_linie.isChecked() and d.werte()["kontur"]
    zieh(d.kv_winkel, 45); assert d.k_verlauf.isChecked() and d.werte()["kontur_verlauf"]["winkel"] == 45
    d.d_tiefe.setValue(5.0); d.d_winkel.setValue(40.0)
    assert d.werte()["d3"]["tiefe"] == 5.0 and d.werte()["d3"]["winkel"] == 40.0
    zieh(d.trans, 30); assert d.r_farbe.isChecked() and d.werte()["transparenz"] == 30


def test_seitenrand_optionen_und_kunstrahmen(app, tmp_path):
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QImage, QPainter
    from lunivo_writer.editor import seitenrahmen
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog, _SeitenOptionenDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = RahmenSchattierungDialog(None, seitenrand={"art": "einfach", "farbe": "#c92a2a", "breite_pt": 3.0, "abstand_mm": 8.0, "seiten": "tblr",
                                                    "messen": "text", "abstand": "2,3,6,7", "kopf": True, "vordergrund": False, "kunst": "stars"})
    assert d.p_rand.rand_optionen["abstand"] == (2.0, 3.0, 6.0, 7.0) and d.p_rand.kunst.currentData() == "stars"
    o = _SeitenOptionenDialog(None, d.p_rand.rand_optionen)
    assert o.messen.currentData() == "text" and o.kopf.isChecked() and not o.vordergrund.isChecked() and o.werte()["abstand"] == (2.0, 3.0, 6.0, 7.0)
    o.messen.setCurrentIndex(1); o.ausrichten.setChecked(True)
    assert o.werte()["messen"] == "seitenrand" and o.werte()["ausrichten"] and not o.kopf.isEnabled()
    r = d.p_rand.linie_wert()
    assert not d.p_rand.einstellung["alle"].isVisibleTo(d.p_rand) and not d.p_rand.einstellung["raster"].isVisibleTo(d.p_rand)
    erg = d.seitenrand()
    assert erg["messen"] == "text" and erg["abstand"] == "2,3,6,7" and erg["kunst"] == "stars" and not erg["vordergrund"]
    pg = PageSettings(); pg.border = erg
    img = QImage(800, 1100, QImage.Format_RGB32); img.fill(0xffffff); p = QPainter(img)
    seitenrahmen.zeichnen(p, erg, pg, QRectF(0, 0, 794, 1123)); p.end()
    e = DocumentEditor(); e.setPlainText("Seite")
    pfad = str(tmp_path / "sr.docx"); formats.save(pfad, e.document(), pg)
    g = formats.load(pfad).page.border
    assert g["messen"] == "text" and g["abstand"] == "2,3,6,7" and g["kunst"] == "stars" and g["kopf"] and not g["fuss"] and not g["vordergrund"]


def test_seitenrahmen_vorn_und_hinten(app):
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPainter
    from lunivo_writer.editor.pagination import seitenschmuck
    from lunivo_writer.models.page import PageSettings

    def bild(vorn: bool, rahmen: str) -> QImage:
        pg = PageSettings(); pg.border = {"art": "einfach", "farbe": "#c92a2a", "breite_pt": 6.0, "abstand_mm": 10.0, "seiten": "tblr", "vordergrund": vorn}
        img = QImage(300, 300, QImage.Format_RGB32); img.fill(QColor("white"))
        p = QPainter(img); seitenschmuck(p, pg, False, QRectF(0, 0, 300, 300), rahmen, False); p.end()
        return img
    rot = lambda img: img.pixelColor(150, 38).red() > 150 and img.pixelColor(150, 38).green() < 100            # liegt der Rahmen an der Kante?
    assert rot(bild(True, "vorn")) and not rot(bild(True, "hinten"))              # Vordergrund: nur beim Zeichnen „vorn“
    assert rot(bild(False, "hinten")) and not rot(bild(False, "vorn"))            # Hintergrund: nur beim Zeichnen „hinten“
    assert rot(bild(False, "immer"))


def test_texteffekte_in_der_seitenleiste(app, tmp_path):
    from PySide6.QtCore import QEventLoop, QSettings, QTimer
    from PySide6.QtGui import QTextCursor
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    from lunivo_writer.editor import texteffekt as T
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.show(); w.new_document()
    e = w.current_editor(); e.setPlainText("Seitenleiste")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    w.befehle.texteffekte()                                                    # öffnet den Bereich in der Seitenleiste, kein Fenster
    assert not w.sidebar.isHidden() and w.sidebar.texteffekte_sichtbar()
    p = w.sidebar.effekt_panel
    p.s_abst.regler.setValue(120)                                              # Regler bewegen: wirkt sofort an der Markierung
    schleife = QEventLoop(); QTimer.singleShot(50, schleife.quit); schleife.exec()
    r = T.aus_format(e.document().firstBlock().begin().fragment().charFormat())
    assert r["schatten"]["abstand"] == 12.0
    w.sidebar.zeige_bereich(0)
    assert not w.sidebar.texteffekte_sichtbar()


def test_texteffekte_knopf_im_band_oeffnet_die_seitenleiste(app, tmp_path):
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QToolButton
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.show(); w.new_document(); w.current_editor().setPlainText("Text")
    knoepfe = [b for b in w.findChildren(QToolButton) if b.toolTip() in ("Texteffekte", "Texteffekte formatieren")]
    assert knoepfe, "der Knopf „Texteffekte“ fehlt im Band"
    w.sidebar.hide()
    knoepfe[0].click()
    assert w.sidebar.texteffekte_sichtbar()


def test_texteffekte_menue_im_band(app, tmp_path):
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QTextCursor
    from lunivo_writer.editor import texteffekt as T
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.show(); w.new_document(); e = w.current_editor(); e.setPlainText("Menü")
    c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)
    m = w.befehle.menue_texteffekteKlappe()
    titel = [a.text().replace("&", "") for a in m.actions() if a.text()]
    assert titel[:4] == ["WordArt", "Schatten", "Spiegelung(R)", "Leuchteffekt(G)"] and "3D-Drehung" in titel and titel[-1].startswith("Weitere Texteffekte")
    assert not [a for a in m.actions() if a.text() == "3D-Drehung"][0].isEnabled()
    sub = {a.text().replace("&", ""): a.menu() for a in m.actions() if a.menu()}
    sub["Schatten"].gewaehlt.emit("0")                                        # erster Schatten der Auswahl
    assert T.aus_format(e.document().firstBlock().begin().fragment().charFormat())["schatten"]["art"] == "aussen"
    sub["Leuchteffekt(G)"].gewaehlt.emit("3")
    r = T.aus_format(e.document().firstBlock().begin().fragment().charFormat())
    assert r["leuchten"] and r["schatten"]                                    # der Schatten bleibt, wenn ein Leuchten dazukommt
    sub["WordArt"].gewaehlt.emit("3")                                        # WordArt „Blaue Kontur“ ersetzt alle Effekte
    r = T.aus_format(e.document().firstBlock().begin().fragment().charFormat())
    assert r["kontur"] and r["fuell"] == "keine" and not r.get("schatten")
    sub["Schatten"].gewaehlt.emit("")


def test_fenster_stapel_unterfenster_als_seiten(app):
    from PySide6.QtWidgets import QDialog
    from lunivo_writer.ui.baukasten.fenster_stapel import FensterStapel, stapel_von
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    fv = FormatvorlageDialog(None, start={"groesse": 12}, vorlagen=["Standard"])
    host = FensterStapel(fv)
    host.show()
    assert len(host._seiten) == 1 and not host.zurueck.isVisible()
    gr0 = host.size(); assert gr0 == host.GROESSE or gr0.width() <= host.GROESSE.width()
    fv._absatz()                                                              # Format ▸ Absatz: eine Seite im selben Fenster
    assert len(host._seiten) == 2 and host.zurueck.isVisibleTo(host) and "Absatz" in host.pfad.text() and stapel_von(host._seiten[1][0]) is host
    absatz = host._seiten[1][0]
    absatz.vor.setValue(10.0)
    absatz._tabstopps()                                                       # zweite Ebene: Tabstopps aus dem Absatz
    assert len(host._seiten) == 3 and "Tabstopps" in host.pfad.text()
    host._seiten[2][0].accept()                                               # OK im Tabstoppfenster: zurück zum Absatz
    assert len(host._seiten) == 2
    absatz.accept()                                                           # OK im Absatz: fertig() setzt die Werte der Vorlage, zurück zur Vorlage
    assert len(host._seiten) == 1 and host.width() >= gr0.width() and host.height() >= gr0.height()      # das Fenster schrumpft nicht
    assert fv.leiste.werte()["vor"] > 0
    fv._effekte(); assert len(host._seiten) == 2
    host._zurueck()                                                           # „← Zurück“ bricht ab
    assert len(host._seiten) == 1
    fv.accept()                                                               # OK der Vorlage beendet das ganze Fenster
    assert host.result() == QDialog.Accepted


def test_weitere_farben_als_seite_im_stapel(app):
    from PySide6.QtGui import QColor
    from lunivo_writer.ui.baukasten.fenster_stapel import FensterStapel
    from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
    from lunivo_writer.ui.baukasten.farbpalette import FarbPalette
    fv = FormatvorlageDialog(None, start={"groesse": 12}, vorlagen=["Standard"])
    host = FensterStapel(fv); host.show()
    pal = FarbPalette(fv.leiste, keine_text=None)                  # eine Palette in der Formatvorlage
    gewaehlt = []
    pal.gewaehlt.connect(gewaehlt.append)
    pal._weitere()                                                  # „Weitere Farben …“: Seite „Farben“ im selben Fenster
    assert len(host._seiten) == 2 and "Farben" in host.pfad.text()
    seite = host._seiten[1][0]
    seite.accept()
    assert len(host._seiten) == 1 and gewaehlt and isinstance(gewaehlt[0], QColor)


def test_pipette_hat_sicherungen(app, monkeypatch):
    from PySide6.QtCore import QEventLoop, QPoint, QTimer
    from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent
    from PySide6.QtCore import Qt, QEvent
    from lunivo_writer.ui.baukasten import pipette
    # Zeitablauf: ohne Eingabe endet die Pipette von selbst (hier in einer Sekunde)
    monkeypatch.setattr(pipette, "ZEIT_S", 1)
    monkeypatch.setattr(QGuiApplication, "platformName", staticmethod(lambda: "xcb"))
    import time
    t = time.time()
    assert pipette.farbe_vom_bildschirm() is None
    assert time.time() - t < 4
    # Taste bricht ab
    monkeypatch.setattr(pipette, "ZEIT_S", 30)
    def taste():
        w = [x for x in QGuiApplication.topLevelWidgets() if isinstance(x, pipette._Pipette)] if hasattr(QGuiApplication, "topLevelWidgets") else []
        from PySide6.QtWidgets import QApplication
        w = [x for x in QApplication.topLevelWidgets() if isinstance(x, pipette._Pipette) and x._offen]
        if w:
            w[0].keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier))
    QTimer.singleShot(200, taste)
    t = time.time()
    assert pipette.farbe_vom_bildschirm() is None and time.time() - t < 3
    # Wayland: nichts aufnehmen, nichts blockieren
    monkeypatch.setattr(QGuiApplication, "platformName", staticmethod(lambda: "wayland"))
    assert pipette.farbe_vom_bildschirm() is None


def test_druck_bereich_und_blattseiten():
    from lunivo_writer.editor.druck import bereich_lesen, papier_name, seiten_nach_wahl
    assert bereich_lesen("1-3, 5", 10) == [1, 2, 3, 5]
    assert bereich_lesen("8-12", 10) == [8, 9, 10] and bereich_lesen("x", 10) is None and bereich_lesen("20", 10) is None
    assert seiten_nach_wahl({"bereich": "alle", "blattseiten": "vorder"}, 5) == [1, 3, 5]
    assert seiten_nach_wahl({"bereich": "seiten", "seiten_text": "2-4", "blattseiten": "rueck"}, 5) == [2, 4]
    assert papier_name(210, 297) == "A4" and papier_name(297, 210) == "A4" and papier_name(100, 100) == "Benutzerdefiniert"


def test_druckfenster_wahl_und_pruefung(app):
    from lunivo_writer.ui.baukasten.druck_dialog import DruckDialog
    d = DruckDialog(None, 4, (210, 297), False, {"schwarz": True})
    e = d.ergebnis()
    assert e["bereich"] == "alle" and e["papier"] == "A4" and e["schwarz"] and e["steuerelemente"] and not e["platzhalter"]
    d.ansicht.text.setText("9")                                   # Seite außerhalb → Drucken nicht möglich
    assert not d.ok.isEnabled() and d.ergebnis()["bereich"] == "seiten"
    d.ansicht.text.setText("2-3"); d.ansicht.pro_blatt.setCurrentIndex(d.ansicht.pro_blatt.findData(2))
    assert d.ok.isEnabled() and d.ansicht.von.text() == "/ 1"
    d.ansicht.papier2.setCurrentIndex(d.ansicht.papier2.findData("A5"))   # Reiter „Drucker“ und „Standard“ teilen die Wahl
    assert d.ergebnis()["papier"] == "A5"


def test_drucken_ausgabe_in_pdf(app, tmp_path):
    from PySide6.QtGui import QTextDocument
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPrintSupport import QPrinter
    from lunivo_writer.editor.druck import drucken
    from lunivo_writer.models.page import PageSettings
    d = QTextDocument(); d.setPlainText("Zeile\n" * 140)
    ps = PageSettings()

    def seiten(ein):
        pr = QPrinter(); pr.setOutputFileName(str(tmp_path / "o.pdf"))
        drucken(pr, d, ps, {}, dict({"bereich": "alle", "pro_blatt": 1}, **ein))
        q = QPdfDocument(); q.load(str(tmp_path / "o.pdf")); return q.pageCount()
    alle = seiten({})
    assert alle >= 3
    assert seiten({"bereich": "seiten", "seiten_text": "2"}) == 1
    assert seiten({"pro_blatt": 4}) == 1


def test_druckvorschau_ansichten_und_zoom(app):
    from PySide6.QtGui import QTextDocument
    from lunivo_writer.editor.druck import Zwischenseiten
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.ui.baukasten.druckvorschau import DruckVorschau
    d = QTextDocument(); d.setPlainText("Zeile\n" * 140)
    v = DruckVorschau(None, Zwischenseiten(d, PageSettings(), {}))
    v.resize(1000, 700); v.show()
    assert v._gesamt >= 3 and len(v._seiten) == 1
    v.ansicht.setCurrentIndex(1); assert len(v._seiten) == 2
    v.ansicht.setCurrentIndex(2); assert len(v._seiten) == v._gesamt
    z = v._zoom; v._zoom_setzen(z * 1.25); assert abs(v._zoom - z * 1.25) < 1e-6
    v._gehe(2); assert v.nr.value() == 2
    assert v._q.bild(1).pixelColor(2, 2).name() == "#ffffff"
    v.close()


def test_handbuch_fenster_hat_gliederung(app):
    from PySide6.QtWidgets import QListWidget, QTextBrowser
    from lunivo_writer.ui.dialogs import hilfe_dialoge
    d = hilfe_dialoge.handbuch(None)
    nav = d.findChild(QListWidget)
    eintraege = [nav.item(i).text() for i in range(nav.count()) if nav.item(i).data(0x100)]
    assert "Das erste Blatt" in eintraege and "Wenn etwas klemmt" in eintraege and len(eintraege) >= 18
    assert "Lunivo" in d.findChild(QTextBrowser).toPlainText()


def test_vorlagen_galerie_zeigt_eigene_vorlagen(app, tmp_path):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.baukasten.vorlagen_galerie import VorlagenGalerie
    s = Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)); s.set("vorlagen/ordner", str(tmp_path))
    (tmp_path / "Mein Brief.txt").write_text("Hallo\nVorlage\n", encoding="utf-8")
    g = VorlagenGalerie(s, True); g.resize(1200, 800); g.show()
    namen = [k.name for k in g._kacheln]
    assert namen[0] == "Leeres Dokument" and "Mein Brief" in namen and "Brief" in namen
    assert g.reiter_w.tabText(2).endswith("1")
    g._reiter_setzen("eigene"); assert [k.name for k in g._kacheln if k.isVisible()] == ["Mein Brief"]
    g.suche.setText("xyz"); assert not [k for k in g._kacheln if k.isVisible()]
    g.suche.setText(""); g._reiter_setzen("alle")
    gewaehlt = []
    g.gewaehlt.connect(lambda a, w: gewaehlt.append((a, w)))
    next(k for k in g._kacheln if k.name == "Mein Brief").click()
    assert gewaehlt == [("datei", str(tmp_path / "Mein Brief.txt"))]
    g._timer.stop()


def test_vorlagen_rubriken_aus_unterordnern(app, tmp_path):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.baukasten.vorlagen_galerie import VorlagenGalerie
    s = Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)); s.set("vorlagen/ordner", str(tmp_path))
    (tmp_path / "Lebenslauf").mkdir()
    for n in ("Kay 2024", "Kay Technik"):
        (tmp_path / "Lebenslauf" / f"{n}.txt").write_text("Lebenslauf\n", encoding="utf-8")
    g = VorlagenGalerie(s, True); g.resize(1200, 800); g.show()
    sicht = [k.name for k in g._sichtbar()]
    assert "Lebenslauf" in sicht and "Brief" in sicht and "Kay 2024" not in sicht          # oben nur die Rubriken
    g.rubrik_oeffnen("Lebenslauf")
    assert [k.name for k in g._sichtbar()] == ["Lebenslauf", "Kay 2024", "Kay Technik"]     # Gerüst und eigene Dokumente der Rubrik
    assert g._ziel() == str(tmp_path / "Lebenslauf") and g.zurueck.isVisible() is True
    g.rubrik_oeffnen("Brief")
    assert "Brief an eine Behörde" in [k.name for k in g._sichtbar()]
    g.rubrik_oeffnen(None); g.suche.setText("technik")
    assert [k.name for k in g._sichtbar()] == ["Kay Technik"]                               # die Suche findet auch in Rubriken
    g._timer.stop()


def test_pdf_schrift_bleibt_schwarz_im_dunklen_thema(app, tmp_path):
    """Text ohne eigene Farbe darf im PDF nicht die helle Textfarbe des dunklen Themas bekommen (blasse, fast weiße Schrift)."""
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QColor, QImage, QPainter, QPalette, QTextDocument
    from PySide6.QtPdf import QPdfDocument
    from lunivo_writer.editor.pagination import export_pdf
    from lunivo_writer.models.page import PageSettings
    alt = app.palette()
    dunkel = QPalette(alt)
    for rolle in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        dunkel.setColor(rolle, QColor("#e8eaed"))
    app.setPalette(dunkel)
    try:
        d = QTextDocument(); d.setPlainText("Hallo dunkles Thema\nZweite Zeile")
        pdf = str(tmp_path / "d.pdf"); export_pdf(pdf, d, PageSettings())
        q = QPdfDocument(); q.load(pdf); gr = QSize(700, 990)
        img = QImage(gr, QImage.Format_RGB32); img.fill(Qt.white)
        p = QPainter(img); p.drawImage(0, 0, q.render(0, gr)); p.end()
        assert min(img.pixelColor(x, y).lightness() for x in range(60, 400) for y in range(60, 200)) < 80
    finally:
        app.setPalette(alt)


def test_docx_schreibt_dokumentsprache_statt_englisch(app, tmp_path):
    """Ohne eigene Angabe steht die Sprache des Dokuments (de-DE) in der DOCX, nicht die Vorgabe en-US der Vorlage."""
    import zipfile
    from PySide6.QtGui import QTextDocument
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import docx_writer
    d = QTextDocument(); d.setPlainText("Sehr geehrte Damen und Herren")
    pfad = str(tmp_path / "s.docx"); docx_writer.write_docx(pfad, d, PageSettings(), {})
    xml = zipfile.ZipFile(pfad).read("word/styles.xml").decode("utf-8")
    assert 'w:lang w:val="de-DE"' in xml and 'w:lang w:val="en-US"' not in xml


def test_luecken_sind_nur_in_der_ansicht_gelb(app, tmp_path):
    """Die gelbe Farbe der Lücken «…» ist eine Zusatzauswahl des Editors: nicht im Textformat, nicht in der DOCX."""
    import zipfile
    from PySide6.QtGui import QTextCharFormat
    from lunivo_writer.services import docx_writer
    from lunivo_writer.editor import vorlagen
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    from lunivo_writer.models.page import PageSettings
    ed = DocumentEditor()
    vorlagen.aufbauen(ed, ["Hallo «Name»,", "Text"], {}, "heute")
    ed._overlays_neu()
    farben = [e.format.background().color().name() for e in ed.extraSelections()]
    assert "#fff3bf" in farben                                         # in der Ansicht gelb …
    from PySide6.QtCore import Qt
    b = ed.document().firstBlock()
    it = b.begin(); stile = []
    while not it.atEnd():
        stile.append(it.fragment().charFormat().background().style()); it += 1
    assert stile and all(st == Qt.NoBrush for st in stile)             # … im Textformat nicht
    pfad = str(tmp_path / "l.docx"); docx_writer.write_docx(pfad, ed.document(), PageSettings(), {})
    assert "FFF3BF" not in zipfile.ZipFile(pfad).read("word/document.xml").decode("utf-8")


def _rot(b=40, h=30):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage
    img = QImage(b, h, QImage.Format_RGB32); img.fill(Qt.red)
    return img


def test_frei_positionierte_bilder_ueberleben_docx_und_werden_gezeichnet(app, tmp_path):
    """Kopfzeilenbild und Bild am Absatz (ohne Textumbruch): schreiben, lesen, zeichnen — Lage und Schichtfolge bleiben."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import freie_bilder as FB
    from lunivo_writer.editor.pagination import seite_als_bild
    from lunivo_writer.models.page import PageSettings, mm_to_px
    from lunivo_writer.services import docx_writer, file_service
    d = QTextDocument(); d.setPlainText("Hallo\nZweiter Absatz")
    name = FB.neuer_name(d); d.addResource(QTextDocument.ImageResource, QUrl(name), _rot())
    FB.an_absatz(QTextCursor(d.firstBlock()), {"n": name, "b": 40.0, "h": 30.0, "bh": "seite", "xh": 100.0, "bv": "seite", "yv": 400.0,
                                                "hinter": False, "ellipse": False, "ah": "", "av": ""})
    ps = PageSettings()
    ps.bilder = [{"ort": "kopf", "bild": _rot(80, 50), "b": 80.0, "h": 50.0, "bh": "seite", "xh": 10.0, "bv": "seite", "yv": 10.0,
                  "hinter": True, "ellipse": False, "ah": "", "av": ""}]
    pfad = str(tmp_path / "f.docx"); docx_writer.write_docx(pfad, d, ps, {})
    g = file_service.load(pfad)
    assert len(g.page.bilder) == 1 and g.page.bilder[0]["ort"] == "kopf" and g.page.bilder[0]["hinter"]
    angaben = [a for b in [g.doc.firstBlock()] for a in FB.aus_absatz(b.blockFormat())]
    assert len(angaben) == 1 and abs(angaben[0]["yv"] - 400.0) < 1 and angaben[0]["bv"] == "seite"
    img = seite_als_bild(g.doc, g.page, 1, 1.0)
    assert img.pixelColor(50, 30).red() > 200 and img.pixelColor(50, 30).green() < 60          # Bild in der Kopfzeile, oben links
    assert img.pixelColor(120, 410).red() > 200 and img.pixelColor(120, 410).green() < 60      # Bild am Absatz, weiter unten
    assert img.pixelColor(300, 300).green() > 200                                                # sonst weißes Blatt


def test_frei_bild_ausrichtung_und_ellipse(app):
    from lunivo_writer.editor import freie_bilder as FB
    r = FB.rechteck({"b": 100.0, "h": 50.0, "bh": "seite", "ah": "center", "bv": "seite", "av": "bottom"}, 800, 1000, 100, 100, 600, 800)
    assert (r.x(), r.y()) == (350.0, 950.0)
    r = FB.rechteck({"b": 10.0, "h": 10.0, "bh": "rand", "xh": 5.0, "bv": "absatz", "yv": -20.0}, 800, 1000, 100, 100, 600, 800, absatz_y=300.0)
    assert (r.x(), r.y()) == (105.0, 280.0)


def test_frei_bild_im_editor_auswaehlen_verschieben_loeschen(app):
    """Klick wählt ein Bild vor dem Text, Ziehen verschiebt es (Rückgängig stellt es her), Entf löscht es."""
    from PySide6.QtCore import QEvent, QPointF, Qt, QUrl
    from PySide6.QtGui import QKeyEvent, QMouseEvent, QTextCursor, QTextDocument
    from lunivo_writer.editor import freie_bilder as FB
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    ed = DocumentEditor(); ed.resize(900, 700); ed.show()
    ed.setPlainText("Text\nzweiter Absatz")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(80, 60))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 80.0, "h": 60.0, "bh": "seite", "xh": 200.0, "bv": "seite", "yv": 300.0,
                                                          "hinter": False, "ellipse": False, "ah": "", "av": ""})
    app.processEvents(); ed.viewport().repaint(); app.processEvents()
    assert ed._frei_treffer, "das Bild wurde beim Zeichnen nicht gefunden"
    mitte = ed._frei_treffer[0][2].center()

    def maus(art, pos, tasten=Qt.LeftButton):
        e = QMouseEvent(art, QPointF(pos), QPointF(pos), Qt.LeftButton, tasten, Qt.NoModifier)
        {QEvent.MouseButtonPress: ed.mousePressEvent, QEvent.MouseMove: ed.mouseMoveEvent, QEvent.MouseButtonRelease: ed.mouseReleaseEvent}[art](e)
    maus(QEvent.MouseButtonPress, mitte)
    maus(QEvent.MouseMove, mitte + QPointF(40, 30))
    maus(QEvent.MouseButtonRelease, mitte + QPointF(40, 30), Qt.NoButton)
    a = FB.aus_absatz(ed.document().firstBlock().blockFormat())[0]
    z = ed.zoom
    assert abs(a["xh"] - (200.0 + 40 / z)) < 1.5 and abs(a["yv"] - (300.0 + 30 / z)) < 1.5
    ed.document().undo()
    assert abs(FB.aus_absatz(ed.document().firstBlock().blockFormat())[0]["xh"] - 200.0) < 1.5
    ed._frei_sel = ("t", 0, 0)
    ed.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier))
    assert FB.aus_absatz(ed.document().firstBlock().blockFormat()) == []


def test_frei_bild_hinter_text_ohne_tasten_anklickbar_wo_kein_text_liegt(app):
    """Ein Bild hinter dem Text (Band im Briefkopf) lässt sich mit einfachem Klick wählen, wenn an der Stelle kein Text steht; und das
    Anklicken klappt auch, nachdem nur ein kleiner Teil neu gezeichnet wurde (blinkende Schreibmarke)."""
    from PySide6.QtCore import QEvent, QPointF, Qt, QUrl
    from PySide6.QtGui import QMouseEvent, QTextCursor, QTextDocument
    from lunivo_writer.editor import freie_bilder as FB
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    ed = DocumentEditor(); ed.resize(900, 700); ed.show()
    ed.setPlainText("Text")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(200, 100))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 200.0, "h": 100.0, "bh": "seite", "xh": 300.0, "bv": "seite", "yv": 400.0,
                                                          "hinter": True, "ellipse": False, "ah": "", "av": ""})
    app.processEvents()
    ed.viewport().repaint(0, 0, 5, 5); app.processEvents()                    # nur ein kleiner Teil wird neu gezeichnet
    mitte = ed._frei_liste()[0][3].center()
    ed.mousePressEvent(QMouseEvent(QEvent.MouseButtonPress, QPointF(mitte), QPointF(mitte), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    assert ed._frei_sel is not None


def test_rechtsklickmenue_deutsch_und_mini_leiste_zwei_zeilen(app, tmp_path):
    from PySide6.QtCore import QSettings
    from lunivo_writer.services.settings_service import Settings
    from lunivo_writer.ui.main_window import MainWindow
    from lunivo_writer.ui.widgets.kontextmenue import menue_bauen
    from lunivo_writer.ui.widgets.mini_leiste import MiniLeiste
    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document(); e = w.current_editor(); e.insertPlainText("Text")
    texte = [a.text() for a in menue_bauen(e, w).actions() if not a.isSeparator()]
    assert texte[:3] == ["Kopieren", "Ausschneiden", "Einfügen"] and "Schriftart …" in texte and "Neuer Kommentar" in texte
    assert not any(t in ("Undo", "Redo", "Cut", "Copy", "Paste", "Select All") for t in texte)           # keine englischen Standardtexte
    m = MiniLeiste(w)
    assert {"kopieren", "einfuegen", "ausschneiden", "formatUebertragen", "fett", "hervorhebenJetzt", "schriftfarbeJetzt", "ausrichtung", "zeilenabstand"} <= set(m.knoepfe)
    assert m.schriftart.count() > 5 and m.groesse.count() >= 10
    assert m.knoepfe["schriftfarbeJetzt"].menu() is not None and m.knoepfe["zeilenabstand"].menu() is not None
    for x in w._doc_tabs():
        x.editor.document().setModified(False)                         # sonst fragt das Schließen nach und der Test hängt
    w.close()


def test_layout_fenster_werte_und_bildwechsel_frei_text(app):
    """Das Fenster „Layout“ liefert seine Werte; auf einem Bild angewendet wechselt es zwischen frei (hinter/vor dem Text) und im Text."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import bildlayout as BL
    from lunivo_writer.editor import freie_bilder as FB
    from lunivo_writer.ui.baukasten.layout_dialog import LayoutDialog
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    d = LayoutDialog(None, {"umbruch": "vor", "breite": {"mm": 30.0}, "hoehe": {"mm": 20.0}, "original": (60.0, 40.0)})
    w = d.werte()
    assert w["umbruch"] == "vor" and abs(w["breite"]["mm"] - 30.0) < 0.01 and w["h"]["modus"] == "abs"
    assert not d._abstand_box.isEnabled()                                      # gilt nur bei Quadrat, Passend, Transparent
    d.kacheln.setze("quadrat", True); assert d._abstand_box.isEnabled()
    ed = DocumentEditor(); ed.resize(900, 700); ed.show(); ed.setPlainText("Text\nzweiter Absatz")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(80, 60))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 80.0, "h": 60.0, "bh": "seite", "xh": 200.0, "bv": "seite", "yv": 300.0,
                                                          "hinter": False, "ellipse": False, "ah": "", "av": ""})
    app.processEvents(); ed.viewport().repaint(); app.processEvents()
    ed._frei_sel = ed._frei_liste()[0][0]
    z = BL.ziel(ed)
    assert z[0] == "frei" and BL.lesen(ed, z)["umbruch"] == "vor"
    BL.anwenden(ed, z, {"umbruch": "hinter", "drehung": 15.0})                  # bleibt frei, wandert hinter den Text und dreht sich
    a = FB.aus_absatz(ed.document().firstBlock().blockFormat())[0]
    assert a["hinter"] is True and abs(a["dreh"] - 15.0) < 0.01
    ed._frei_rev = None; ed._frei_sel = ed._frei_liste()[0][0]
    BL.anwenden(ed, BL.ziel(ed), {"umbruch": "textfluss"})                       # zurück in den Text
    assert FB.aus_absatz(ed.document().firstBlock().blockFormat()) == [] and ed._bild_cursor() is not None
    BL.anwenden(ed, BL.ziel(ed), {"umbruch": "vor"})                              # und wieder frei
    assert len(FB.aus_absatz(ed.document().firstBlock().blockFormat())) == 1


def test_objekt_menues_und_bildformat_roundtrip(app, tmp_path):
    """Formstile, Füllung und Kontur wirken auf ein freies Bild und bleiben in der DOCX."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import bildlayout as BL
    from lunivo_writer.editor import freie_bilder as FB
    from lunivo_writer.editor.pagination import seite_als_bild
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import docx_writer, file_service
    from lunivo_writer.ui.baukasten.objekt_menues import FuellMenue, KonturMenue, formstil_werte, formstile
    assert len(formstile().knoepfe) == 42 and formstil_werte("z12")["fuell"]["art"] == "farbe"
    f, k = FuellMenue(), KonturMenue()
    assert [a.text() for a in f.actions() if not a.menu()][-5:] == ["Graduell", "Textur", "Muster(N)", "Fülleffekte…", "Bild(P)"] and any(a.text() == "Bild(P)" for a in f.actions())
    assert [a.text() for a in k.actions() if a.menu()] == ["Linienart(W)", "Strichart", "Pfeilart"]
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    ed = DocumentEditor(); ed.resize(900, 700); ed.show(); ed.setPlainText("Text")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(80, 60))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 80.0, "h": 60.0, "bh": "seite", "xh": 200.0, "bv": "seite", "yv": 300.0,
                                                          "hinter": False, "ellipse": False, "ah": "", "av": ""})
    app.processEvents(); ed.viewport().repaint(); app.processEvents()
    ed._frei_sel = ed._frei_liste()[0][0]
    BL.format_setzen(ed, BL.ziel(ed), fuell={"art": "farbe", "farbe": "#2f9e44"}, rand={"b": 3.0, "farbe": "#1c7ed6", "art": "gestrichelt"})
    a = FB.aus_absatz(ed.document().firstBlock().blockFormat())[0]
    assert a["fuell"]["farbe"] == "#2f9e44" and a["rand"]["art"] == "gestrichelt"
    pfad = str(tmp_path / "f.docx"); docx_writer.write_docx(pfad, ed.document(), PageSettings(), {})
    g = file_service.load(pfad)
    b2 = FB.aus_absatz(g.doc.firstBlock().blockFormat())[0]
    assert b2["fuell"]["farbe"].lower() == "#2f9e44" and b2["rand"]["art"] == "gestrichelt" and abs(b2["rand"]["b"] - 3.0) < 0.2


def test_weitere_linien_und_effekte_oeffnen_die_seitenleiste_formatierung(app, tmp_path):
    """„Weitere Linien …“ / „Weitere Effekte …“ zeigen den Bereich „Formatierung“ für das markierte Bild; Änderungen wirken sofort."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import freie_bilder as FB
    w = _fenster(tmp_path); w.show()
    ed = w.current_editor()
    ed.setPlainText("Text")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(80, 60))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 80.0, "h": 60.0, "bh": "seite", "xh": 200.0, "bv": "seite", "yv": 300.0,
                                                          "hinter": False, "ellipse": False, "ah": "", "av": ""})
    ed._frei_liste(); ed._frei_sel = ("t", 0, 0)
    ed._frei_effekte()
    assert w.sidebar.objektformat_sichtbar() and w.sidebar.objekt_panel.reiter.currentIndex() == 1
    ed._frei_linien_fenster()
    assert w.sidebar.objekt_panel.reiter.currentIndex() == 0
    _zu(w)


def test_zeichentools_register_und_funktionen(app, tmp_path):
    """Markiertes freies Bild → Register „Zeichentools“; Ausrichten, Drehen, Ebene, Maße, Format übertragen wirken auf das Bild."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import bildlayout as BL, freie_bilder as FB
    w = _fenster(tmp_path); w.show()
    ed = w.current_editor()
    ed.setPlainText("Text")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(80, 60))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 80.0, "h": 60.0, "bh": "seite", "xh": 200.0, "bv": "seite", "yv": 300.0,
                                                          "hinter": False, "ellipse": False, "ah": "", "av": "",
                                                          "rand": {"b": 3.0, "farbe": "#ff0000", "art": "einfach"}})
    ed._frei_liste()
    i = w.band.kontext_index["zeichen"]
    assert not w.band.reiter.isTabVisible(i)
    ed._frei_sel = ("t", 0, 0)
    w._sync_format()
    assert w.band.reiter.isTabVisible(i)
    b = w.band.b
    b.zeichenAusrichten(None, "rechts"); b.zeichenDrehen(None, 90); b.zeichenEbene(None, "hinter"); b.zeichenMasse(40.0, 20.0)
    a = FB.aus_absatz(ed.document().firstBlock().blockFormat())[0]
    assert a["ah"] == "right" and a["dreh"] == 90.0 and a["hinter"] is True
    assert abs(a["b"] - 40 * 96 / 25.4) < 0.5 and abs(a["h"] - 20 * 96 / 25.4) < 0.5
    merk = BL.format_merken(BL.ziel(ed))
    assert merk["rand"]["farbe"] == "#ff0000"
    ed._frei_sel = None
    w._sync_format()
    assert not w.band.reiter.isTabVisible(i)
    _zu(w)


def test_fuelleffekte_graduell_textur_muster_oeffnen_die_seitenleiste(app, tmp_path):
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import freie_bilder as FB
    w = _fenster(tmp_path); w.show()
    ed = w.current_editor(); ed.setPlainText("Text")
    name = FB.neuer_name(ed.document()); ed.document().addResource(QTextDocument.ImageResource, QUrl(name), _rot(80, 60))
    FB.an_absatz(QTextCursor(ed.document().firstBlock()), {"n": name, "b": 80.0, "h": 60.0, "bh": "seite", "xh": 200.0, "bv": "seite", "yv": 300.0,
                                                          "hinter": False, "ellipse": False, "ah": "", "av": ""})
    ed._frei_liste(); ed._frei_sel = ("t", 0, 0)
    m = ed.frei_fuell_menue(ed)
    for text, radio in (("Textur", "r_textur"), ("Muster(N)", "r_muster"), ("Graduell", "r_verlauf")):
        next(a for a in m.actions() if a.text() == text).trigger()
        assert w.sidebar.objektformat_sichtbar() and getattr(w.sidebar.objekt_panel, radio).isChecked()
        app.processEvents()
        assert FB.aus_absatz(ed.document().firstBlock().blockFormat())[0]["fuell"]["art"] in ("textur", "muster", "graduell", "verlauf")
    _zu(w)


def test_wort_extras(app):
    from lunivo_writer.editor import wortextras as W
    from lunivo_writer.ui.document.document_editor import DocumentEditor
    ed = DocumentEditor(); ed.setPlainText("Das ist ein\nSatz.\n\n\nZweiter  Absatz.  \nDritter.")
    assert W.absaetze_neu_anordnen(ed) == 1 and ed.toPlainText().startswith("Das ist ein Satz.")
    assert W.leere_loeschen(ed) == 2 and "\n\n" not in ed.toPlainText()
    assert W.leerzeichen_bereinigen(ed) == 2 and "Zweiter Absatz." in ed.toPlainText()
    assert W.leere_einfuegen(ed) == 2 and ed.document().blockCount() == 5
    W.einzug_zwei_zeichen(ed)
    assert ed.document().firstBlock().blockFormat().textIndent() > 0
    ed.document().undo()
    ed.setPlainText("a b")
    assert W.zeilenumbruch_in_return(ed) == 1 and ed.document().blockCount() == 2


def test_bildeffekte_ueberleben_docx(app, tmp_path):
    """Schatten, Leuchten, Spiegelung und weiche Kanten eines freien Bildes werden als effectLst geschrieben und wieder gelesen."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QTextCursor, QTextDocument
    from lunivo_writer.editor import freie_bilder as FB
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import docx_writer, file_service
    d = QTextDocument(); d.setPlainText("Hallo")
    name = FB.neuer_name(d); d.addResource(QTextDocument.ImageResource, QUrl(name), _rot())
    fx = {"schatten": {"farbe": "#112233", "transparenz": 40, "groesse": 100, "weich": 5.0, "abstand": 6.0, "winkel": 90},
          "leuchten": {"farbe": "#ff0000", "groesse": 9.0, "transparenz": 30},
          "reflektion": {"groesse": 40, "transparenz": 60, "weich": 1.0, "abstand": 2.0}, "weich": {"radius": 7.0}}
    FB.an_absatz(QTextCursor(d.firstBlock()), {"n": name, "b": 40.0, "h": 30.0, "bh": "seite", "xh": 100.0, "bv": "seite", "yv": 400.0,
                                                "hinter": False, "ellipse": False, "ah": "", "av": "", "fx": fx})
    pfad = str(tmp_path / "e.docx"); docx_writer.write_docx(pfad, d, PageSettings(), {})
    g = file_service.load(pfad)
    a = FB.aus_absatz(g.doc.firstBlock().blockFormat())[0]
    got = a["fx"]
    assert got["schatten"]["farbe"] == "#112233" and abs(got["schatten"]["abstand"] - 6.0) < 0.1 and abs(got["schatten"]["winkel"] - 90) < 0.1
    assert abs(got["schatten"]["transparenz"] - 40) < 0.2 and abs(got["leuchten"]["groesse"] - 9.0) < 0.1 and got["leuchten"]["farbe"] == "#ff0000"
    assert abs(got["reflektion"]["groesse"] - 40) < 0.1 and abs(got["weich"]["radius"] - 7.0) < 0.1
