"""Der Editor: QTextEdit mit Seitenbreite, Formatierungsbefehlen und Seitenzählung."""
from __future__ import annotations

from PySide6.QtCore import QMimeData, QRect, QRectF, QSizeF, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPalette, QPen, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat, QTextFrameFormat, QTextImageFormat, QTextDocumentFragment
from PySide6.QtWidgets import QListWidget, QScrollArea, QTextEdit

from lunivo_writer.editor.anzeige_extra import VersteckterText
from lunivo_writer.models.page import PageSettings, mm_to_px
from lunivo_writer.editor.pagination import bind_layout
from lunivo_writer.editor import stile
from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin
from lunivo_writer.ui.document.zusatz_editor import ZusatzMixin

from lunivo_writer.core.farben import Farbe
from lunivo_writer.ui.document.editor_anzeige import AnzeigeBaustein
from lunivo_writer.ui.document.editor_spalten import SpaltenBaustein
from lunivo_writer.ui.document.editor_seiten import SeitenBaustein
from lunivo_writer.ui.document.editor_formatierung import FormatierungBaustein
from lunivo_writer.ui.document.editor_bilder import BilderBaustein
from lunivo_writer.ui.document.editor_schreibhilfe import SchreibhilfeBaustein

STYLES = dict.fromkeys(stile.NAMEN)       # nur die eingebauten; selbst angelegte: stile.namen()            # Namen der Formatvorlagen (Definitionen: editor/stile.py)


EINFUEGE_MODI = ["Quellformatierung beibehalten", "Zielformatierung verwenden", "Nur Text"]


def _ziel_fragment(html: str, standard: QFont):
    """HTML einfügen, aber Schriftart, -größe, Farben und Hintergründe des Ziels behalten (Fett, Kursiv, Verweise bleiben)."""
    from PySide6.QtGui import QBrush
    d = QTextDocument()
    d.setHtml(html)
    c = QTextCursor(d)
    c.select(QTextCursor.Document)
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            fr = it.fragment()
            if fr.isValid() and not fr.charFormat().isImageFormat():
                f = QTextCharFormat(fr.charFormat())
                f.clearProperty(QTextFormat.FontFamilies); f.clearProperty(QTextFormat.FontFamily)
                f.clearProperty(QTextFormat.FontPointSize); f.clearProperty(QTextFormat.FontPixelSize)
                f.clearForeground(); f.clearBackground()
                k = QTextCursor(d); k.setPosition(fr.position()); k.setPosition(fr.position() + fr.length(), QTextCursor.KeepAnchor)
                k.setCharFormat(f)
            it += 1
        b = b.next()
    return QTextDocumentFragment(d)




class DocumentEditor(AnzeigeBaustein, SpaltenBaustein, SeitenBaustein, FormatierungBaustein, BilderBaustein, SchreibhilfeBaustein, FreieBilderMixin, ZusatzMixin, QTextEdit):
    pageInfoChanged = Signal(int, int)       # aktuelle Seite, Seitenzahl

    formatChanged = Signal()                 # Cursor-Format hat sich geändert

    zoomChanged = Signal(float)

    freiAuswahlGeaendert = Signal()           # ein frei positioniertes Bild wurde markiert oder die Markierung aufgehoben

    pageApplied = Signal()                    # Seiteneinrichtung oder Größe hat sich geändert


    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = PageSettings()
        self.stil_tasten()
        self.setAcceptRichText(True)
        self.setFrameShape(QTextEdit.NoFrame)          # das Blatt hat keinen Rahmen; es steht frei auf der Arbeitsfläche
        self.setUndoRedoEnabled(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.show_marks = False
        self.zoom = 1.0
        self.gitter = False
        self.web = False
        self._web_breite = 800
        self.gliederung = False
        self.zeilenfokus = False
        self.marken = False                # Textbegrenzungen (Eckmarken am Textrand)
        self.vorhersage = None            # Rückruf: Wortanfang → Liste von Vorschlägen
        self.autokorr = None              # Rückruf: Text vor dem Zeiger → korrigierter Text
        self.mini_hook = None             # Rückruf(editor, globalePosition, rechtsklick): Minisymbolleiste zeigen/verbergen
        self.kontext_hook = None          # Rückruf(menü, position): ergänzt das Rechtsklick-Menü
        self.opt = lambda name, std=True: std      # Rückruf: Schalter aus den Optionen
        self.opt_text = lambda name, std="": std   # Rückruf: Textwerte aus den Optionen
        self._wellen: list[dict] = []
        self._popup = QListWidget(None)
        self._popup.setWindowFlags(Qt.ToolTip)
        self._popup.setFocusPolicy(Qt.NoFocus)
        self._popup.itemClicked.connect(lambda it: self._vorschlag_nehmen(it.data(Qt.UserRole)))
        self._pages = 1
        self._extra_seiten = 0              # Blätter, die erst der Druck (Endnoten) anhängt
        self._lese_papier = ""              # Lesehilfe: Papierfarbe / Textfarbe überschreiben die Blattfarbe
        self._lese_text = ""
        self._breaks: list[int] = []
        self._paged: QTextDocument | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._recount)
        self.cursorPositionChanged.connect(self._cursor_moved)
        self.cursorPositionChanged.connect(lambda: self.zeilenfokus and self.viewport().update())
        self.currentCharFormatChanged.connect(lambda *_: self.formatChanged.emit())
        self.document().contentsChanged.connect(self._timer.start)
        self._fluss = QTimer(self); self._fluss.setSingleShot(True); self._fluss.setInterval(500)      # Umbruchregeln nach dem Tippen prüfen
        self._fluss.timeout.connect(self._seitenfluss)
        self._fluss_laeuft = False
        self._effekt_cache: bool | None = None
        self.document().contentsChanged.connect(lambda: setattr(self, "_effekt_cache", None))
        self.document().contentsChanged.connect(self._fluss_planen)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)       # die Seite wächst mit, der graue Grund scrollt
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cursorPositionChanged.connect(self._scroll_outer)
        self._verbinde_groesse()
        self._zusatz_init()
        self.versteckt_zeigen = False
        self._blasen_flaeche = None
        self._blasen_cache = (None, [])
        self._blasen_extra = 0
        self._versteckt_hl = VersteckterText(self.document())
        self._zeilen_cache = (-1, [])
        self._sp_caret = True
        self._sp_timer = QTimer(self)                  # Schreibmarke blinkt selbst, solange Spalten gezeichnet werden
        self._sp_timer.setInterval(530)
        self._sp_timer.timeout.connect(self._sp_blinken)
        self.cursorPositionChanged.connect(self._sp_neu_zeichnen)
        self.selectionChanged.connect(self._sp_neu_zeichnen)
        self.document().contentsChanged.connect(self._sp_neu_zeichnen)
        self.apply_page(self.page)


    # ---- Dokument und Seite ---------------------------------------------

    def _verbinde_groesse(self) -> None:
        self.document().documentLayout().documentSizeChanged.connect(self._passe_hoehe_an)


    def _passe_hoehe_an(self, *_):
        if self.web:
            h = int(self.document().size().height()) + 4
        else:
            g = self._sp_geo()
            h = int(g["top"] + self._blatt_anzahl() * (g["H"] + g["gap"]))
        if h != self.height():
            self.setFixedHeight(h)
        self.pageApplied.emit()


    def _blatt_anzahl(self) -> int:
        """Anzahl der Blätter: so viele, wie der Textfluss des Editors Seiten braucht (plus Noten-Seiten, die nur der Druck anhängt)."""
        n = max(1, int(self.page.spalten))
        return max(1, -(-max(1, self.document().pageCount()) // n)) + self._extra_seiten


    def _aussen(self):
        w = self.parent()
        while w is not None and not isinstance(w, QScrollArea):
            w = w.parent()
        return w


    def _scroll_outer(self) -> None:
        sa = self._aussen()
        if sa is None or sa.widget() is None:
            return
        r = self.cursorRect()
        pt = self.viewport().mapTo(sa.widget(), r.topLeft())
        sa.ensureVisible(pt.x(), pt.y() + r.height() // 2, 10, max(40, r.height() * 2))


    def set_document_and_page(self, doc: QTextDocument, page: PageSettings) -> None:
        self.setDocument(doc)
        self._versteckt_hl = VersteckterText(doc, self.versteckt_zeigen)
        self._verbinde_groesse()
        doc.setDocumentMargin(0)
        doc.contentsChanged.connect(self._timer.start)
        doc.contentsChanged.connect(self._fluss_planen)
        doc.contentsChanged.connect(lambda: setattr(self, "_effekt_cache", None))
        self._effekt_cache = None
        self._fluss.start()
        doc.contentsChange.connect(self._inhalt_geaendert)
        self.apply_page(page)
        doc.setModified(False)
        doc.clearUndoRedoStacks()


    def apply_page(self, page: PageSettings) -> None:
        self.page = page
        doc = self.document()
        self.seitenfarbe_anwenden()
        bind_layout(doc, self.zoom)
        doc.setDocumentMargin(0)

        root = doc.rootFrame()
        ff: QTextFrameFormat = root.frameFormat()

        if self.web:
            for setze in (
                ff.setTopMargin,
                ff.setBottomMargin,
                ff.setLeftMargin,
                ff.setRightMargin,
            ):
                setze(mm_to_px(8))
            root.setFrameFormat(ff)
            self.setFixedWidth(max(300, int(self._web_breite)))

        else:
            # Blattmodus: Die Ränder gehören zum Blatt, nicht zum Textfluss. Das Dokument wird auf die Textfläche
            # (Breite/Höhe ohne Ränder) umbrochen; jede Qt-Seite des Flusses wird auf ein eigenes Blatt gezeichnet.
            for setze in (
                ff.setTopMargin,
                ff.setBottomMargin,
                ff.setLeftMargin,
                ff.setRightMargin,
            ):
                setze(0)
            ff.setTopMargin(page.erste_seite_versatz_px())       # lange Kopfzeile: Text der ersten Seite beginnt darunter
            root.setFrameFormat(ff)
            self.setFixedWidth(int(mm_to_px(page.width_mm) * self.zoom))
            self._sp_einrichten()

        self._blasen_einrichten()

        if self.web:
            if self.lineWrapMode() != QTextEdit.WidgetWidth:
                self.setLineWrapMode(QTextEdit.WidgetWidth)
                self._sp_timer.stop()
            doc.setPageSize(QSizeF(max(300, self._web_breite), -1))

        self._recount()
        self._passe_hoehe_an()
        self._timer.start()
        self.pageApplied.emit()


    # ---- Sprechblasen ------------------------------------------------------------------------------------------------
    class _OptAdapter:
        """Gibt `sprechblasen.konfig_lesen` die Rückrufe des Editors statt einer Settings-Klasse."""
        def __init__(self, ed):
            self.ed = ed

        def get(self, name, std=None):
            return self.ed.opt_text(name, std if isinstance(std, str) else str(std if std is not None else ""))

        def get_bool(self, name, std=False):
            return self.ed.opt(name, std)


    def focusInEvent(self, e) -> None:
        super().focusInEvent(e)
        if self._blatt_aktiv():
            self._sp_timer.start()


    def mousePressEvent(self, e) -> None:
        if self._frei_maus(e, "press"):
            return
        super().mousePressEvent(self._maus_abgebildet(e))


    def dragMoveEvent(self, e) -> None:
        m = self._ziehen_abgebildet(e)
        super().dragMoveEvent(m)
        if m is not e:
            e.setDropAction(m.dropAction())
            e.setAccepted(m.isAccepted())


    def dropEvent(self, e) -> None:
        m = self._ziehen_abgebildet(e)
        super().dropEvent(m)
        if m is not e:
            e.setDropAction(m.dropAction())
            e.setAccepted(m.isAccepted())


    def mouseMoveEvent(self, e) -> None:
        if self._frei_maus(e, "move"):
            return
        zone = self._kopffuss_zone(e.position().y())
        if zone and not e.buttons() and self.opt("ui/kopffuss_tipp", True):
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(e.globalPosition().toPoint(), "Doppelklick bearbeitet die " + ("Kopfzeile" if zone == "kopf" else "Fußzeile"), self)
        super().mouseMoveEvent(self._maus_abgebildet(e))


    def mouseDoubleClickEvent(self, e) -> None:
        zone = self._kopffuss_zone(e.position().y())
        fenster = self.window()
        if zone and hasattr(fenster, "edit_header_footer"):
            fenster.edit_header_footer(zone == "kopf")
            return
        super().mouseDoubleClickEvent(self._maus_abgebildet(e))


    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._blasen_geometrie()
        if self._blatt_aktiv():
            g = self._sp_geo()
            ps = self.document().pageSize()
            if abs(ps.height() - g["ch"]) > 0.5 or abs(ps.width() - g["cb"]) > 0.5:
                self.document().setPageSize(QSizeF(g["cb"], g["ch"]))


    ZOOM_MIN, ZOOM_MAX = 0.1, 5.0


    def wheelEvent(self, e) -> None:
        if e.modifiers() & Qt.ControlModifier:
            self.set_zoom(self.zoom * (1.1 if e.angleDelta().y() > 0 else 1 / 1.1))
            e.accept()
            return
        e.ignore()                      # die Seite scrollt im grauen Grund


    def contextMenuEvent(self, e) -> None:
        from lunivo_writer.ui.widgets.kontextmenue import menue_bauen
        fenster = self.window()
        m = menue_bauen(self, fenster) if hasattr(fenster, "befehle") else self.createStandardContextMenu()
        if self.kontext_hook is not None:
            pos = self.cursorForPosition(e.pos()).position()
            self.kontext_hook(m, pos)
        from lunivo_writer.editor import bildlayout as BL
        if BL.ziel(self) is not None and not self.isReadOnly():
            m.addSeparator()
            m.addAction("Layout …", self.bild_layout_dialog)
        if self._bild_cursor() is not None and not self.isReadOnly():
            from lunivo_writer.editor import umbruch as U
            m.addSeparator()
            c = self._bild_cursor()
            aktuell = U.schwebend(self.document(), c.selectionStart()) or "zeile"
            for modus, text in (("zeile", "Bild: mit Text in Zeile"), ("links", "Bild: links, Text umfließt"),
                                ("rechts", "Bild: rechts, Text umfließt"),
                                ("oben_unten", "Bild: oben und unten (eigene Zeile)")):
                a = m.addAction(text, lambda _=False, modus=modus: U.umbruch_setzen(self, modus))
                a.setCheckable(True)
                a.setChecked(modus == aktuell)
        if self.textCursor().hasSelection() and not self.isReadOnly():
            m.addSeparator()
            a = m.addAction("Ausgeblendeter Text", lambda: self.set_versteckt(not self.ist_versteckt()))
            a.setCheckable(True)
            a.setChecked(self.ist_versteckt())
        ki = getattr(self.window(), "ki", None)
        if ki is not None and self.textCursor().hasSelection() and not self.isReadOnly():
            m.addSeparator()
            m.addAction("KI: Text in Bild", ki.bild_aus_text)
            aktionen = [a for a in ki.konfig["assistenten"] if a.get("zugriff", "kontext") == "kontext"]
            if aktionen:
                sub = m.addMenu("KI-Aktionen")
                for a in aktionen:
                    sub.addAction(a["name"], lambda _=False, a=a: ki.assistent(a))
        mini = self.mini_hook is not None and self.opt("ui/mini_rechtsklick", True) and not self.isReadOnly()
        if mini:
            self.mini_hook(self, e.globalPos(), True)
        m.exec(e.globalPos())
        m.deleteLater()
        if mini:
            self.mini_hook(None, None, True)


    def mouseReleaseEvent(self, e) -> None:
        if self._frei_maus(e, "release"):
            return
        if e.button() == Qt.MiddleButton and not self.opt("bearbeiten/mittlere_taste", True):
            e.accept()                                  # mittlere Maustaste fügt nichts ein (Optionen ▸ Bearbeiten)
            return
        super().mouseReleaseEvent(self._maus_abgebildet(e))
        if e.button() == Qt.LeftButton and self.opt("bearbeiten/wortweise", True) and self.textCursor().hasSelection():
            self._wortweise()
        if (e.button() == Qt.LeftButton and self.mini_hook is not None and self.textCursor().hasSelection()
                and not self.isReadOnly() and self.opt("ui/mini_auswahl", True) and not self._bild_cursor()):
            c = QTextCursor(self.textCursor())
            c.setPosition(c.selectionStart())
            self.mini_hook(self, self.viewport().mapToGlobal(self.cursorRect(c).topLeft()), False)
        if (e.modifiers() & Qt.ControlModifier) and self.opt("ui/strg_klick_link", True):
            href = self.anchorAt(e.pos())
            if href and href.startswith("#"):
                from lunivo_writer.editor.verweise import intern_springen
                intern_springen(self, href)
                return
            if href:
                from PySide6.QtCore import QUrl as _U
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(_U(href))
                return
        if e.button() == Qt.LeftButton and not self.textCursor().hasSelection() and not self.isReadOnly():
            from lunivo_writer.editor.sendungen import kasten_umschalten
            from lunivo_writer.editor import formular as FO
            pos = self.cursorForPosition(e.pos()).position()
            if FO.klick(self, pos, self.window()) or kasten_umschalten(self, pos):
                return
            if (n := self.note_an(pos)) is not None and self.cursorRect(self.cursorForPosition(e.pos())).adjusted(-6, 0, 6, 0).contains(e.pos()):
                self.noteAngeklickt.emit(*n)
        c = self.cursorForPosition(e.pos())
        c2 = QTextCursor(c)
        c2.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        if c2.charFormat().isImageFormat() and not self.textCursor().hasSelection():
            r = self.cursorRect(c)
            if abs(e.pos().x() - r.x()) < c2.charFormat().toImageFormat().width() + 2:
                self.setTextCursor(c2)


    def paintEvent(self, e) -> None:
        sp = self._blatt_aktiv()
        if sp:
            self._blatt_zeichnen(e)
        else:
            super().paintEvent(e)
        
        vp = self.viewport()
        p = QPainter(vp)

        is_dark = self.palette().color(QPalette.Window).lightness() < 128
        line_color = QColor(Farbe.GRAU_HELL) if is_dark else QColor(Farbe.GRAU)
        accent_color = QColor("#748ffc") if is_dark else QColor(Farbe.BLAU)
        strip_color = QColor("#2b2d30") if is_dark else QColor("#d9dee5")

        self._schmuck_zeichnen(p)
        if self.gitter:
            self._gitter_zeichnen(p)
        if not self.web and (self._hat_rahmen() or self._hat_mehrstufig() or self._hat_tabfuell() or self._hat_effekt()):
            from lunivo_writer.editor.pagination import absatz_zusatz_zeichnen
            if sp:
                g = self._sp_geo()
                for lp in range(max(1, self.document().pageCount())):
                    x0, y0 = self._sp_ursprung(lp)
                    p.save()
                    p.setClipRect(QRectF(x0 - 6, y0, g["cb"] + 12, g["ch"]))
                    p.translate(x0, y0 - lp * g["ch"])
                    absatz_zusatz_zeichnen(p, self.document(), self.zoom)
                    p.restore()
            else:
                p.save()
                p.translate(0, -self.verticalScrollBar().value())
                absatz_zusatz_zeichnen(p, self.document(), self.zoom)
                p.restore()
        if self.page.zeilennummern and not self.web and not self._mehrspaltig():
            self._zeilennummern_zeichnen(p)
        if self.marken and not self.web:
            g = self._sp_geo()
            L = 14
            p.setPen(QPen(line_color, 1))
            for k in range(self._blatt_anzahl()):
                oben = int(self.blatt_oben(k) + g["mt"])
                unten = int(self.blatt_oben(k) + g["H"] - g["mb"])
                # Eckmarken liegen außerhalb der Textfläche und zeigen von ihrer Ecke nach außen (wie in Word)
                for x, ox in ((int(g["ml"]), -1), (int(g["ml"] + g["cb"] * g["n"] + g["g"] * (g["n"] - 1)), 1)):
                    for y, oy in ((oben, -1), (unten, 1)):
                        p.drawLine(x, y, x + ox * L, y)
                        p.drawLine(x, y, x, y + oy * L)
        self._extras_zeichnen(p, sp)
        if sp and self._mehrspaltig() and self.page.spalten_linie:
            g = self._sp_geo()
            p.setPen(QPen(line_color, 1))
            for k in range(self._blatt_anzahl()):
                for j in range(1, g["n"]):
                    x = int(g["ml"] + j * (g["cb"] + g["g"]) - g["g"] / 2)
                    y0 = self.blatt_oben(k) + g["mt"]
                    p.drawLine(x, int(y0), x, int(y0 + g["ch"]))

        if self.zeilenfokus and self.hasFocus() and not self.textCursor().hasSelection():
            r = self.cursorRect()
            zeile = QRect(0, r.top() - 1, vp.width(), r.height() + 2)
            dunkel = QColor(self.palette().color(self.viewport().backgroundRole()))
            dunkel.setAlpha(170)
            p.setPen(Qt.NoPen)
            p.setBrush(dunkel)
            p.drawRect(QRect(0, 0, vp.width(), zeile.top()))
            p.drawRect(QRect(0, zeile.bottom() + 1, vp.width(), vp.height()))
        p.end()
        self._lese_wachstum_zeichnen()


    # ---- Schreibhilfe: Wellenlinien, Ersetzen, Vorhersage, AutoKorrektur -------------------
    WELLE = {"fehler": Farbe.ORANGE, "tipp": "#1c7ed6", "hinweis": Farbe.GRAU}


    def keyPressEvent(self, e) -> None:
        if self._frei_taste(e):
            return
        folge = self._folge_vorher(e)
        self._taste(e)
        if folge:
            self._folge_danach(*folge)


    def focusOutEvent(self, e) -> None:
        try:
            self._popup.hide()
        except RuntimeError:          # beim Beenden schon abgebaut
            pass
        super().focusOutEvent(e)


    # ---- Tastatur ----------------------------------------------------------------
    def insertFromMimeData(self, source) -> None:
        if source.hasImage() and not source.hasHtml():
            img = QImage(source.imageData())
            if not img.isNull():
                name = f"einfuegen-{self.document().revision()}"
                self.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
                f = QTextImageFormat(); f.setName(name)
                f.setWidth(min(img.width(), self.page.content_width_px)); f.setHeight(
                    img.height() * min(1.0, self.page.content_width_px / max(1, img.width())))
                self.textCursor().insertImage(f)
                return
        modus = self.opt_text("bearbeiten/einfuegen_standard", EINFUEGE_MODI[0])
        if not isinstance(modus, str) or modus not in EINFUEGE_MODI:
            modus = EINFUEGE_MODI[0]
        self._einfuegen_mit(source, modus, neu=True)


    def _einfuegen_mit(self, source, modus: str, neu: bool) -> None:
        """Einfügen als EIN Rückgängig-Schritt; danach bietet die kleine Schaltfläche die anderen Formen an (Optionen ▸ Bearbeiten)."""
        c = self.textCursor()
        c.beginEditBlock()
        start = c.selectionStart()
        c.removeSelectedText()
        if modus == "Nur Text" or not source.hasHtml():
            c.insertText(source.text() if source.hasText() else "")
        elif modus == "Zielformatierung verwenden":
            c.insertFragment(_ziel_fragment(source.html(), self.document().defaultFont()))
        else:
            c.insertFragment(QTextDocumentFragment.fromHtml(source.html()))
        ende = c.position()
        c.endEditBlock()
        self.setTextCursor(c)
        if neu and self.opt("bearbeiten/einfuegen_schaltflaeche", True) and ende > start and not self.isReadOnly():
            kopie = QMimeData()
            for f in source.formats():
                kopie.setData(f, source.data(f))
            self._einfuegen_schaltflaeche(kopie, start, ende, modus)


    def _einfuegen_schaltflaeche(self, quelle, start: int, ende: int, modus: str) -> None:
        from PySide6.QtWidgets import QMenu, QToolButton
        b = getattr(self, "_paste_btn", None)
        if b is None:
            b = self._paste_btn = QToolButton(self.viewport())
            b.setText("Einfügen ▾")
            b.setCursor(Qt.ArrowCursor)
            b.setPopupMode(QToolButton.InstantPopup)
            b.setStyleSheet("QToolButton { border: 1px solid palette(mid); border-radius: 4px; padding: 2px 6px; "
                            "background: palette(window); font-size: 8pt; }")
            self.cursorPositionChanged.connect(self._paste_btn_pruefen)
        self._paste_ende = ende
        m = QMenu(b)
        for name in EINFUEGE_MODI:
            a = m.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == modus)
            a.triggered.connect(lambda _=False, name=name: self._einfuegen_neu(quelle, start, name))
        b.setMenu(m)
        c = QTextCursor(self.document()); c.setPosition(ende)
        r = self.cursorRect(c)
        b.move(max(0, r.left()), r.bottom() + 2)
        b.adjustSize()
        b.show()


    def _einfuegen_neu(self, quelle, start: int, modus: str) -> None:
        c = QTextCursor(self.document())
        c.setPosition(start)
        c.setPosition(self._paste_ende, QTextCursor.KeepAnchor)
        self.setTextCursor(c)
        self._paste_btn.hide()
        self._einfuegen_mit(quelle, modus, neu=False)
        self._einfuegen_schaltflaeche(quelle, start, self.textCursor().position(), modus)


    def _paste_btn_pruefen(self) -> None:
        b = getattr(self, "_paste_btn", None)
        if b is not None and b.isVisible() and self.textCursor().position() != getattr(self, "_paste_ende", -1):
            b.hide()
