"""Ausgeblendeter Text, Feldcodes, Zeichnungsobjekte, Änderungsbalken, Kreiszahlen, Kopf-/Fußzeilen-Tipp, Objektanker."""
import zipfile

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPdfWriter, QTextCharFormat, QTextCursor
from PySide6.QtTest import QTest

from native_qt.document_io import formats
from native_qt.editor import anzeige_extra as AX
from native_qt.editor import einfuegen as E
from native_qt.editor.editor_widget import DocumentEditor
from native_qt.editor.page import HeaderFooter, PageSettings
from native_qt.editor.pagination import paginated_copy, render, seite_als_bild
from native_qt.editor.zusatz import P_AENDERUNG, P_AUTOR, P_DATUM, P_FELD, P_OBJEKT, P_VERSTECKT


def _text(ed, text="Eins zwei drei vier"):
    ed.setPlainText(text)
    return ed


def test_ausgeblendeter_text_anzeige_druck_docx(app, tmp_path):
    ed = _text(DocumentEditor())
    c = ed.textCursor(); c.setPosition(5); c.setPosition(9, QTextCursor.KeepAnchor); ed.setTextCursor(c)    # „zwei“
    ed.set_versteckt(True)
    assert ed.ist_versteckt()
    assert ed.toPlainText() == "Eins zwei drei vier"                           # Text bleibt unangetastet
    fm = ed.document().firstBlock().layout().formats()
    assert any(r.format.fontPointSize() < 1 for r in fm)                       # in der Anzeige winzig und durchsichtig
    ed.set_versteckt_zeigen(True)
    zeigen = ed.document().firstBlock().layout().formats()
    assert any(r.format.underlineStyle() == QTextCharFormat.DotLine for r in zeigen)      # grau, gepunktet unterstrichen
    ed.set_versteckt_zeigen(False)
    # Druck/Seitenzählung: ohne ausgeblendeten Text, außer die Option verlangt ihn
    assert "zwei" not in paginated_copy(ed.document(), PageSettings()).toPlainText()
    assert "zwei" in paginated_copy(ed.document(), PageSettings(), versteckt=True).toPlainText()
    # DOCX: w:vanish, und wieder gelesen
    pfad = str(tmp_path / "v.docx")
    formats.save(pfad, ed.document(), PageSettings())
    assert "<w:vanish" in zipfile.ZipFile(pfad).read("word/document.xml").decode()
    neu = formats.load(pfad).doc
    assert AX._bereiche(neu, P_VERSTECKT) and neu.toPlainText().strip() == "Eins zwei drei vier"
    ed.set_versteckt(False)
    assert not ed.ist_versteckt()


def test_feldcodes_zeichnungsobjekte_und_objektdaten(app, tmp_path):
    ed = _text(DocumentEditor(), "Abbildung 1 steht hier")
    c = QTextCursor(ed.document()); c.setPosition(10); c.setPosition(11, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setProperty(P_FELD, "SEQ Abbildung"); c.mergeCharFormat(f)
    d = paginated_copy(ed.document(), PageSettings())
    assert AX.feldcodes_einsetzen(d) == 1 and "{ SEQ Abbildung }" in d.toPlainText()
    assert AX.feldbereiche(ed.document()) == [(10, 11)]
    c = ed.textCursor(); c.movePosition(QTextCursor.End); ed.setTextCursor(c)
    img = QImage(30, 20, QImage.Format_RGB32); img.fill(QColor("tomato"))
    E.qimage_einfuegen(ed, img, "Form: Kreis", "form", {"form": "Kreis"})
    E.qimage_einfuegen(ed, img, "Foto")                                          # ein normales Bild ist kein Zeichnungsobjekt
    d2 = paginated_copy(ed.document(), PageSettings())
    assert d2.toPlainText().count("￼") == 2 and AX.zeichnungen_entfernen(d2) == 1 and d2.toPlainText().count("￼") == 1
    # Die Daten des Objekts überleben DOCX
    pfad = str(tmp_path / "o.docx")
    formats.save(pfad, ed.document(), PageSettings())
    assert 'title="lunivo:' in zipfile.ZipFile(pfad).read("word/document.xml").decode()
    neu = formats.load(pfad).doc
    b = neu.firstBlock(); gefunden = []
    it = b.begin()
    while not it.atEnd():
        cf = it.fragment().charFormat()
        if cf.isImageFormat() and cf.hasProperty(P_OBJEKT):
            gefunden.append(cf.property(P_OBJEKT))
        it += 1
    assert gefunden and '"art":"form"' in gefunden[0] and "Kreis" in gefunden[0]


def test_aenderungsbalken_im_druck_und_in_der_anzeige(app, tmp_path):
    ed = _text(DocumentEditor(), "Erste Zeile\nZweite Zeile mit Änderung\nDritte Zeile")
    c = QTextCursor(ed.document()); c.setPosition(18); c.setPosition(27, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setProperty(P_AENDERUNG, "ins"); f.setProperty(P_AUTOR, "Kay"); f.setProperty(P_DATUM, "2026-10-18")
    c.mergeCharFormat(f)
    pg = PageSettings()
    d = paginated_copy(ed.document(), pg)
    zeilen = AX.aenderungszeilen(d)
    assert len(zeilen) == 1 and zeilen[0][1] > zeilen[0][0]
    ohne = seite_als_bild(ed.document(), pg, 1, 1.0, d)
    img = QImage(seite_als_bild(ed.document(), pg, 1, 1.0, d))
    w = QPdfWriter(str(tmp_path / "b.pdf"))
    assert render(ed.document(), pg, w, opt={"balken": "links"}) == 1
    ed._hat_zusatz = True
    ed.opt_text = lambda n, s="": "links" if n == "aenderungen/balken" else s
    ed.show()
    bild = ed.grab().toImage()
    rot = sum(1 for x in range(60, 130) for y in range(0, 200)
              if QColor(bild.pixel(x, y)).red() > 180 and QColor(bild.pixel(x, y)).green() < 80)
    assert rot > 5                                                              # roter Balken neben der Zeile


def test_kreiszahl_und_rechtsbuendig(app):
    ed = DocumentEditor()
    ed.opt = lambda n, s=True: {"schreibhilfe/akKreiszahl": True, "schreibhilfe/akRechtsLeer": True}.get(n, s)
    ed.show()
    QTest.keyClicks(ed, "Punkt (3)")
    assert ed.toPlainText() == "Punkt ③"
    QTest.keyClicks(ed, " (21)")
    assert ed.toPlainText().endswith("(21)")                                    # nur 1 bis 20
    ed.setPlainText("rechts   ")
    ed.set_alignment(Qt.AlignRight)
    c = ed.textCursor(); c.movePosition(QTextCursor.End); ed.setTextCursor(c)
    QTest.keyClick(ed, Qt.Key_Return)
    assert ed.document().firstBlock().text() == "rechts" and ed.document().blockCount() == 2


def test_kopffuss_zone_tipp_und_objektanker(app, monkeypatch):
    from PySide6.QtGui import QTextOption
    from native_qt.editor import umbruch as U
    ed = _text(DocumentEditor(), "Text")
    pg = PageSettings(); pg.header = HeaderFooter("Mein Kopf", "center"); pg.footer = HeaderFooter("Seite {PAGE}", "right")
    ed.page_settings_changed(pg)
    ed.show()
    assert ed._kopffuss_zone(5) == "kopf" and ed._kopffuss_zone(ed.viewport().height() - 5) == "fuss" and ed._kopffuss_zone(300) == ""
    gerufen = []
    class F:  # Hauptfenster-Ersatz
        def edit_header_footer(self, kopf): gerufen.append(kopf)
    monkeypatch.setattr(ed, "window", lambda: F())
    from PySide6.QtGui import QMouseEvent
    ev = QMouseEvent(ev_t := __import__("PySide6.QtCore", fromlist=["QEvent"]).QEvent.MouseButtonDblClick, QPointF(100, 5), QPointF(100, 5),
                     Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    ed.mouseDoubleClickEvent(ev)
    assert gerufen == [True]
    # Objektanker: Bild umflossen + Formatierungszeichen → ein Anker wird gezeichnet (kein Absturz, Seite gerendert)
    ed.setPlainText("Absatz mit Bild")
    c = ed.textCursor(); c.setPosition(0); ed.setTextCursor(c)
    img = QImage(40, 30, QImage.Format_RGB32); img.fill(QColor("green")); E.qimage_einfuegen(ed, img, "x")
    c = ed.textCursor(); c.setPosition(0); ed.setTextCursor(c)
    assert U.umbruch_setzen(ed, "links")
    o = ed.document().defaultTextOption(); o.setFlags(o.flags() | QTextOption.ShowTabsAndSpaces); ed.document().setDefaultTextOption(o)
    assert ed.grab().toImage().width() > 0


def test_feldschattierung(app):
    ed = _text(DocumentEditor(), "Davor 7 danach")
    c = QTextCursor(ed.document()); c.setPosition(6); c.setPosition(7, QTextCursor.KeepAnchor)
    f = QTextCharFormat(); f.setProperty(P_FELD, "SEQ x"); c.mergeCharFormat(f)
    for modus, erwartet in (("Nie", 0), ("Immer", 1)):
        ed.opt_text = lambda n, s="", m=modus: m if n == "ui/feldschattierung" else s
        ed._overlays_neu()
        felder = [e for e in ed.extraSelections() if e.format.background().color().alpha() == 70]
        assert len(felder) == erwartet
    ed.opt_text = lambda n, s="": "Bei Auswahl" if n == "ui/feldschattierung" else s
    c = ed.textCursor(); c.setPosition(0); ed.setTextCursor(c); ed._overlays_neu()
    assert not [e for e in ed.extraSelections() if e.format.background().color().alpha() == 70]
    c.setPosition(7); ed.setTextCursor(c); ed._overlays_neu()                    # Zeiger im Feld
    assert [e for e in ed.extraSelections() if e.format.background().color().alpha() == 70]
