"""Der Editor: QTextEdit mit Seitenbreite, Formatierungsbefehlen und Seitenzählung."""
from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, QPointF, QRect, QRectF, QSizeF, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import (
    QAbstractTextDocumentLayout, QBrush, QColor, QFont, QImage, QMouseEvent, QPainter, QPalette, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor,
    QTextDocument, QTextFormat, QTextFrameFormat, QTextImageFormat, QTextListFormat,
    QTextTableFormat, QTextLength, QTextDocumentFragment, QTextOption,
)
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QScrollArea, QTextEdit

from ..document_io.docx_reader import LH_PROPORTIONAL, STYLE_PROP
from .anzeige_extra import VersteckterText, aenderungszeilen, feldbereiche
from .zusatz import P_VERSTECKT
from .page import PageSettings, mm_to_px
from ..services.autokorrektur import kleinste_aenderung
from .pagination import bind_layout, paginated_copy
from . import stile
from .zusatz_editor import ZusatzMixin

STYLES = dict.fromkeys(stile.NAMEN)            # Namen der Formatvorlagen (Definitionen: editor/stile.py)


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


class DocumentEditor(ZusatzMixin, QTextEdit):
    pageInfoChanged = Signal(int, int)       # aktuelle Seite, Seitenzahl
    formatChanged = Signal()                 # Cursor-Format hat sich geändert
    zoomChanged = Signal(float)
    pageApplied = Signal()                    # Seiteneinrichtung oder Größe hat sich geändert

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = PageSettings()
        self.setAcceptRichText(True)
        self.setFrameShape(QTextEdit.StyledPanel)
        self.setUndoRedoEnabled(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.show_marks = False
        self.zoom = 1.0
        self.gitter = False
        self.web = False
        self._web_breite = 800
        self.gliederung = False
        self.zeilenfokus = False
        self.marken = True                 # Textbegrenzungen (Eckmarken am Textrand)
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
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)       # die Seite wächst mit, der graue Grund scrollt
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cursorPositionChanged.connect(self._scroll_outer)
        self._verbinde_groesse()
        self._zusatz_init()
        self.versteckt_zeigen = False
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
        h = int(self.document().size().height()) + 4
        if self._spalten_aktiv():
            g = self._sp_geo()
            blaetter = max(1, -(-max(1, self.document().pageCount()) // g["n"]))
            h = int(g["mt"] + blaetter * g["ch"] + g["mb"]) + 4
        mind = 0 if self.web else int(mm_to_px(self.page.height_mm) * self.zoom)
        self.setFixedHeight(max(h, mind))
        self.pageApplied.emit()

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
        if self.web:                      # Weblayout: fortlaufender Text in Fensterbreite, kleine Ränder
            for setze in (ff.setTopMargin, ff.setBottomMargin, ff.setLeftMargin, ff.setRightMargin):
                setze(mm_to_px(8))
            root.setFrameFormat(ff)
            self.setFixedWidth(max(300, int(self._web_breite)))
        elif int(page.spalten) > 1:
            # Spalten: Text fließt in Spaltenbreite und wird auf Spaltenhöhe in „Spaltenseiten“ geteilt; paintEvent und die
            # Mausabbildung stellen sie nebeneinander auf das Blatt (siehe _sp_*).
            for setze in (ff.setTopMargin, ff.setBottomMargin, ff.setLeftMargin, ff.setRightMargin):
                setze(0)
            root.setFrameFormat(ff)
            self.setFixedWidth(int(mm_to_px(page.width_mm) * self.zoom) + 2)
            self._sp_einrichten()
        else:
            ff.setTopMargin(mm_to_px(page.margin_top_mm))
            ff.setBottomMargin(mm_to_px(page.margin_bottom_mm))
            ff.setLeftMargin(mm_to_px(page.margin_left_mm))
            ff.setRightMargin(mm_to_px(page.margin_right_mm))
            root.setFrameFormat(ff)
            self.setFixedWidth(int(mm_to_px(page.width_mm) * self.zoom) + 2)
        if not self._spalten_aktiv() and self.lineWrapMode() != QTextEdit.WidgetWidth:
            self.setLineWrapMode(QTextEdit.WidgetWidth)
            doc.setPageSize(QSizeF(self.viewport().width(), -1))
            self._sp_timer.stop()
            self.setAcceptDrops(True)
        self._passe_hoehe_an()
        self._timer.start()
        self.pageApplied.emit()

    # ---- Ausgeblendeter Text -------------------------------------------------------------------------------------------
    def set_versteckt_zeigen(self, an: bool) -> None:
        self.versteckt_zeigen = an
        self._versteckt_hl.setze_zeigen(an)
        self._timer.start()

    def ist_versteckt(self) -> bool:
        c = self.textCursor()
        if not c.hasSelection():
            return c.charFormat().hasProperty(P_VERSTECKT)
        return all(f.charFormat().hasProperty(P_VERSTECKT) for f in self._fragmente_in(c.selectionStart(), c.selectionEnd()))

    def _fragmente_in(self, von: int, bis: int):
        b = self.document().findBlock(von)
        while b.isValid() and b.position() < bis:
            it = b.begin()
            while not it.atEnd():
                f = it.fragment()
                if f.isValid() and f.position() < bis and f.position() + f.length() > von:
                    yield f
                it += 1
            b = b.next()

    def set_versteckt(self, an: bool) -> None:
        """Markierung (oder Wort am Zeiger) als ausgeblendeten Text formatieren / zurücknehmen."""
        c = self.textCursor()
        if not c.hasSelection():
            c.select(QTextCursor.WordUnderCursor)
        if not c.hasSelection():
            return
        von, bis = c.selectionStart(), c.selectionEnd()
        c.beginEditBlock()
        for f in list(self._fragmente_in(von, bis)):
            a, e = max(von, f.position()), min(bis, f.position() + f.length())
            k = QTextCursor(self.document()); k.setPosition(a); k.setPosition(e, QTextCursor.KeepAnchor)
            fm = QTextCharFormat(f.charFormat())
            fm.setProperty(P_VERSTECKT, 1) if an else fm.clearProperty(P_VERSTECKT)
            k.setCharFormat(fm)
        c.endEditBlock()
        self._versteckt_hl.rehighlight()
        self.document().setModified(True)

    # ---- Spalten im Editor -----------------------------------------------------------------------------------------
    def _spalten_aktiv(self) -> bool:
        return (not self.web) and int(self.page.spalten) > 1

    def _sp_geo(self) -> dict:
        z, pg = self.zoom, self.page
        n = max(1, int(pg.spalten))
        return {"n": n, "cb": round(pg.spalten_breite_px * z), "g": mm_to_px(pg.spalten_abstand_mm) * z,
                "ch": pg.content_height_px * z, "ml": mm_to_px(pg.margin_left_mm) * z, "mt": mm_to_px(pg.margin_top_mm) * z,
                "mb": mm_to_px(pg.margin_bottom_mm) * z}

    def _sp_einrichten(self) -> None:
        """Dokument in Spaltenbreite und -höhe legen: feste Zeilenbreite, damit QTextEdit die Seitenhöhe nicht wieder auf „endlos“ setzt."""
        g = self._sp_geo()
        self.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.setLineWrapColumnOrWidth(int(g["cb"]))
        self.document().setPageSize(QSizeF(g["cb"], g["ch"]))
        self.setAcceptDrops(False)                      # Ziehen und Ablegen kennt die Spaltenabbildung nicht
        if self.hasFocus():
            self._sp_timer.start()

    def _sp_view(self, dx: float, dy: float) -> tuple[float, float]:
        """Dokumentkoordinate (fortlaufender Fluss der Spaltenseiten) → Punkt auf dem Blatt."""
        g = self._sp_geo()
        lp = max(0, int((dy + 1.0) // g["ch"]))        # +1: Qt gibt Rechtecke ganzzahlig, die Seitengrenze liegt meist knapp darüber
        s, j = divmod(lp, g["n"])
        return g["ml"] + j * (g["cb"] + g["g"]) + dx, g["mt"] + s * g["ch"] + max(0.0, dy - lp * g["ch"])

    def _sp_doc(self, vx: float, vy: float) -> tuple[float, float]:
        """Punkt auf dem Blatt → Dokumentkoordinate; Punkte in Rändern und Lücken landen in der nächsten Spalte."""
        g = self._sp_geo()
        s = max(0, int((vy - g["mt"]) // g["ch"]))
        y_in = min(max(vy - g["mt"] - s * g["ch"], 0.0), g["ch"] - 1)
        j = min(g["n"] - 1, max(0, int((vx - g["ml"] + g["g"] / 2) // (g["cb"] + g["g"]))))
        dx = min(max(vx - (g["ml"] + j * (g["cb"] + g["g"])), 0.0), g["cb"])
        lp = s * g["n"] + j
        letzte = max(0, self.document().pageCount() - 1)
        if lp > letzte:
            return dx, self.document().size().height() - 1
        return dx, lp * g["ch"] + y_in

    def _sp_neu_zeichnen(self, *_) -> None:
        try:
            if self._spalten_aktiv():
                self._sp_caret = True
                self.viewport().update()
        except RuntimeError:                           # beim Abbau ist das Widget schon weg
            pass

    def _sp_blinken(self) -> None:
        if self._spalten_aktiv() and self.hasFocus():
            self._sp_caret = not self._sp_caret
            self.viewport().update()

    def focusInEvent(self, e) -> None:
        super().focusInEvent(e)
        if self._spalten_aktiv():
            self._sp_timer.start()

    def cursorRect(self, *args) -> QRect:
        r = super().cursorRect(*args)
        if self._spalten_aktiv():
            x, y = self._sp_view(r.x(), r.y())
            return QRect(int(x), int(y), r.width(), r.height())
        return r

    def cursorForPosition(self, pos: QPoint) -> QTextCursor:
        if self._spalten_aktiv():
            x, y = self._sp_doc(pos.x(), pos.y())
            pos = QPoint(int(x), int(y))
        return super().cursorForPosition(pos)

    def anchorAt(self, pos: QPoint) -> str:
        if self._spalten_aktiv():
            x, y = self._sp_doc(pos.x(), pos.y())
            pos = QPoint(int(x), int(y))
        return super().anchorAt(pos)

    def _maus_abgebildet(self, e):
        """Mausereignis mit Dokumentkoordinaten (nur bei Spalten); QTextEdit selbst rechnet in Dokumentkoordinaten."""
        if not self._spalten_aktiv():
            return e
        x, y = self._sp_doc(e.position().x(), e.position().y())
        return QMouseEvent(e.type(), QPointF(x, y), e.globalPosition(), e.button(), e.buttons(), e.modifiers())

    def mousePressEvent(self, e) -> None:
        super().mousePressEvent(self._maus_abgebildet(e))

    def _kopffuss_zone(self, y: float) -> str:
        """„kopf“ im oberen, „fuss“ im unteren Rand der Seite (nur Seitenansicht, nicht im Weblayout)."""
        if self.web:
            return ""
        z = self.zoom
        if y < mm_to_px(self.page.margin_top_mm) * z - 4:
            return "kopf"
        if y > self.viewport().height() - mm_to_px(self.page.margin_bottom_mm) * z + 4:
            return "fuss"
        return ""

    def mouseMoveEvent(self, e) -> None:
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
        if self._spalten_aktiv():
            g = self._sp_geo()
            ps = self.document().pageSize()
            if abs(ps.height() - g["ch"]) > 0.5 or abs(ps.width() - g["cb"]) > 0.5:
                self.document().setPageSize(QSizeF(g["cb"], g["ch"]))

    def _sp_zeichnen(self, e) -> None:
        """Text, Auswahl, Schreibmarke und Wellenlinien: jede Spaltenseite in ihre Spalte auf dem Blatt."""
        vp = self.viewport()
        p = QPainter(vp)
        p.fillRect(e.rect(), QColor(self.page.color or "white"))
        doc = self.document()
        lay = doc.documentLayout()
        g = self._sp_geo()
        ctx = QAbstractTextDocumentLayout.PaintContext()
        pal = QPalette(self.palette())
        pal.setColor(QPalette.Text, QColor("black"))
        ctx.palette = pal
        auswahl = []
        for es in self.extraSelections():
            a = QAbstractTextDocumentLayout.Selection()
            a.cursor, a.format = es.cursor, es.format
            auswahl.append(a)
        c = self.textCursor()
        if c.hasSelection():
            a = QAbstractTextDocumentLayout.Selection()
            a.cursor = c
            a.format.setBackground(self.palette().highlight())
            a.format.setForeground(self.palette().highlightedText())
            auswahl.append(a)
        ctx.selections = auswahl
        ctx.cursorPosition = c.position() if (self._sp_caret and self.hasFocus() and not c.hasSelection()
                                              and not self.isReadOnly()) else -1
        sicht = QRectF(e.rect())
        for lp in range(max(1, doc.pageCount())):
            s, j = divmod(lp, g["n"])
            x0, y0 = g["ml"] + j * (g["cb"] + g["g"]), g["mt"] + s * g["ch"]
            feld = QRectF(x0 - 6, y0, g["cb"] + 12, g["ch"])
            if not feld.intersects(sicht):
                continue
            p.save()
            p.setClipRect(feld)
            p.translate(x0, y0 - lp * g["ch"])
            ctx.clip = QRectF(-6, lp * g["ch"], g["cb"] + 12, g["ch"])
            lay.draw(p, ctx)
            p.restore()
        p.end()

    def set_web(self, an: bool) -> None:
        if an != self.web:
            self.web = an
            self.apply_page(self.page)
            self.viewport().update()

    def set_web_breite(self, px: int) -> None:
        if px != self._web_breite:
            self._web_breite = px
            if self.web:
                self.apply_page(self.page)

    def set_gliederung(self, an: bool) -> None:
        """Gliederungsansicht: nur Überschriften sind sichtbar; der Text dazwischen ist ausgeblendet (nicht gelöscht)."""
        self.gliederung = an
        b = self.document().firstBlock()
        while b.isValid():
            b.setVisible(not an or b.blockFormat().headingLevel() > 0)
            b = b.next()
        self.document().markContentsDirty(0, self.document().characterCount())
        self.viewport().update()

    def gliederung_ebene(self, delta: int) -> None:
        """Überschrift hoch-/herabstufen (Gliederung): Ebene 1..6, darüber/darunter wird sie zu Text/Titel."""
        c = self.textCursor()
        bf = c.blockFormat()
        lv = bf.headingLevel() + delta
        if bf.headingLevel() and 1 <= lv <= 6:
            self.apply_style(f"Überschrift {lv}")

    def set_zeilennummern(self, an: bool) -> None:
        self.page.zeilennummern = an
        self.viewport().update()

    def _zeilennummern_zeichnen(self, p: QPainter) -> None:
        vp = self.viewport()
        lay = self.document().documentLayout()
        f = p.font(); f.setPixelSize(max(7, int(9 * self.zoom))); p.setFont(f)
        p.setPen(QColor("#868e96"))
        ml = mm_to_px(self.page.margin_left_mm) * self.zoom
        oben = self.verticalScrollBar().value()
        nr = 0
        b = self.document().firstBlock()
        while b.isValid():
            if b.isVisible() and b.layout() is not None:
                top = lay.blockBoundingRect(b).top()
                for i in range(b.layout().lineCount()):
                    nr += 1
                    z = b.layout().lineAt(i)
                    y = top + z.y() - oben
                    if -20 < y < vp.height():
                        p.drawText(QRectF(ml - 52, y, 44, z.height()), Qt.AlignRight | Qt.AlignVCenter, str(nr))
            b = b.next()

    def apply_design(self, fliess: str | None = None, kopf: str | None = None, farbe: str | None = None) -> None:
        """Design: Schriftart für Text und Überschriften, Farbe der Überschriften — für das ganze Dokument."""
        doc = self.document()
        cur = QTextCursor(doc)
        cur.beginEditBlock()
        if fliess:
            f = doc.defaultFont(); f.setFamily(fliess); doc.setDefaultFont(f)
        b = doc.firstBlock()
        while b.isValid():
            kopf_block = b.blockFormat().headingLevel() > 0 or (
                b.blockFormat().hasProperty(STYLE_PROP) and b.blockFormat().property(STYLE_PROP) in ("title", "subtitle", "Title", "Subtitle"))
            fam = kopf if kopf_block and kopf else fliess
            if fam or (kopf_block and farbe):
                c = QTextCursor(b)
                c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cf = QTextCharFormat()
                if fam:
                    cf.setFontFamilies([fam])
                if kopf_block and farbe:
                    cf.setForeground(QColor(farbe))
                c.mergeCharFormat(cf)
            b = b.next()
        cur.endEditBlock()

    def set_absatzrahmen(self, wert: str | None) -> None:
        from .zusatz import B_RAHMEN

        def f(bf):
            if wert:
                bf.setProperty(B_RAHMEN, wert)
            else:
                bf.clearProperty(B_RAHMEN)
        self._block_merge(f)
        self.viewport().update()

    def toggle_rtl(self) -> None:
        rtl = self.textCursor().blockFormat().layoutDirection() == Qt.RightToLeft
        self._block_merge(lambda bf: bf.setLayoutDirection(Qt.LeftToRight if rtl else Qt.RightToLeft))

    def _hat_rahmen(self) -> bool:
        from .zusatz import B_RAHMEN
        b = self.document().firstBlock()
        while b.isValid():
            if b.blockFormat().hasProperty(B_RAHMEN):
                return True
            b = b.next()
        return False

    def set_gitter(self, an: bool) -> None:
        self.gitter = an
        self.viewport().update()

    def seitenspannen(self) -> list[tuple[int, int]]:
        """Senkrechte Bereiche (von, bis) jeder Seite im Editor, aus den Seitenwechseln."""
        if self._spalten_aktiv():
            g = self._sp_geo()
            blaetter = max(1, -(-max(1, self.document().pageCount()) // g["n"]))
            return [(0 if k == 0 else int(g["mt"] + k * g["ch"]),
                     int(g["mt"] + (k + 1) * g["ch"] + (g["mb"] if k == blaetter - 1 else 0))) for k in range(blaetter)]
        h = self.viewport().height() + self.verticalScrollBar().value()
        h = max(h, int(self.document().size().height()))
        starts = [0]
        n = self.document().characterCount()
        for pos in self._breaks:
            if pos < n:
                starts.append(self.cursorRect(self._cursor_at(pos)).top() - 3)
        return [(a, starts[i + 1] if i + 1 < len(starts) else h) for i, a in enumerate(starts)]

    def _schmuck_zeichnen(self, p: QPainter) -> None:
        pg, z = self.page, self.zoom
        if self.web or not (pg.border or pg.watermark):
            return
        from .pagination import seitenschmuck
        vp = self.viewport()
        for a, b in self.seitenspannen():
            if b < 0 or a > vp.height():
                continue
            p.save()
            p.scale(z, z)
            seitenschmuck(p, pg, False, QRectF(0, a / z, vp.width() / z, (b - a) / z))
            p.restore()

    def _gitter_zeichnen(self, p: QPainter) -> None:
        vp = self.viewport()
        schritt = mm_to_px(10) * self.zoom
        if schritt < 6:
            return
        c = QColor("#868e96"); c.setAlpha(70)
        p.setPen(QPen(c, 1))
        x = schritt
        while x < vp.width():
            p.drawLine(int(x), 0, int(x), vp.height()); x += schritt
        y = schritt
        while y < vp.height():
            p.drawLine(0, int(y), vp.width(), int(y)); y += schritt

    def seitenfarbe_anwenden(self) -> None:
        c = self.page.color or "white"
        self.setStyleSheet(f"QTextEdit {{ background: {c}; color: black; border: 1px solid #5c6166; }}")

    ZOOM_MIN, ZOOM_MAX = 0.1, 5.0

    def set_zoom(self, faktor: float) -> None:
        """Ansicht vergrößern/verkleinern. Das Dokument selbst (Schriftgrößen, Maße) bleibt unverändert."""
        faktor = max(self.ZOOM_MIN, min(self.ZOOM_MAX, round(faktor, 3)))
        if abs(faktor - self.zoom) < 1e-6:
            return
        self.zoom = faktor
        self.apply_page(self.page)
        self.viewport().update()
        self.zoomChanged.emit(faktor)

    def wheelEvent(self, e) -> None:
        if e.modifiers() & Qt.ControlModifier:
            self.set_zoom(self.zoom * (1.1 if e.angleDelta().y() > 0 else 1 / 1.1))
            e.accept()
            return
        e.ignore()                      # die Seite scrollt im grauen Grund

    def page_settings_changed(self, page: PageSettings) -> None:
        self.apply_page(page)
        self.document().setModified(True)

    # ---- Seitenzählung -----------------------------------------------------
    def _recount(self) -> None:
        if self._spalten_aktiv():                      # die Spaltenseiten stammen aus dem Editor-Dokument selbst
            g = self._sp_geo()
            self._paged = None
            self._breaks = []
            self._pages = max(1, -(-max(1, self.document().pageCount()) // g["n"]))
            self.viewport().update()
            self._cursor_moved()
            return
        self._paged = paginated_copy(self.document(), self.page, self.noten, silben=False, einspaltig=True, versteckt=self.versteckt_zeigen)   # wie die Bearbeitungsansicht umbricht: ohne Trennstriche
        self._pages = max(1, self._paged.pageCount())
        self._breaks = self._seitenwechsel(self._paged)
        self.viewport().update()
        self._cursor_moved()

    def _seitenwechsel(self, d: QTextDocument) -> list[int]:
        """Zeichenstellen, an denen eine neue Seite beginnt (erste Zeile der Seiten 2, 3, …)."""
        ch = self.page.content_height_px
        lay = d.documentLayout()
        stellen, seite = [], 0
        b = d.firstBlock()
        while b.isValid():
            tl = b.layout()
            if tl is not None and tl.lineCount():
                top = lay.blockBoundingRect(b).top()
                for i in range(tl.lineCount()):
                    ln = tl.lineAt(i)
                    k = int((top + ln.y() + 0.5) // ch)
                    if k > seite:
                        seite = k
                        stellen.append(b.position() + ln.textStart())
            b = b.next()
        return stellen

    @property
    def seitenwechsel(self) -> list[int]:
        return list(self._breaks)

    @property
    def page_count(self) -> int:
        return self._pages

    def current_page(self) -> int:
        if self._spalten_aktiv():
            g = self._sp_geo()
            r = QTextEdit.cursorRect(self)
            return max(1, min(self._pages, int((r.y() + 1.0) // g["ch"]) // g["n"] + 1))
        if self._paged is None:
            return 1
        pos = min(self.textCursor().position(), max(0, self._paged.characterCount() - 1))
        blk = self._paged.findBlock(pos)
        if not blk.isValid():
            return 1
        rect = self._paged.documentLayout().blockBoundingRect(blk)
        ch = self.page.content_height_px
        return max(1, min(self._pages, int((rect.top() + 0.5) // ch) + 1))

    def _cursor_moved(self) -> None:
        try:
            self.pageInfoChanged.emit(self.current_page(), self._pages)
            self.formatChanged.emit()
        except RuntimeError:                           # beim Abbau ist das Widget schon weg
            return
        if self.opt_text("ui/feldschattierung", "Bei Auswahl") == "Bei Auswahl":
            self._zus_timer.start()
        hl = getattr(self, "_silben", None)
        if hl is not None and hl.k["nur_absatz"]:
            neu = self.textCursor().blockNumber()
            if neu != getattr(self, "_silben_block", -1):
                for n in (getattr(self, "_silben_block", -1), neu):
                    b = self.document().findBlockByNumber(n)
                    if b.isValid():
                        hl.rehighlightBlock(b)
                self._silben_block = neu

    def set_silbenfarben(self, konfig: dict | None) -> None:
        """Silben farbig (reine Anzeige, ändert das Dokument nicht); konfig None oder an=False schaltet ab."""
        from .silbenfarben import SilbenFarben
        hl = getattr(self, "_silben", None)
        if not konfig or not konfig["an"]:
            if hl is not None:
                hl.setDocument(None)
                self._silben = None
            return
        if hl is None:
            self._silben_block = self.textCursor().blockNumber()
            self._silben = SilbenFarben(self.document(), konfig, lambda: self.textCursor().blockNumber())
        else:
            hl.neu_konfigurieren(konfig)

    def word_count(self) -> int:
        return len(self.document().toPlainText().split())

    # ---- Zeichenformat -----------------------------------------------------
    def _merge(self, fmt: QTextCharFormat) -> None:
        cur = self.textCursor()
        cur.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def toggle_bold(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontWeight(QFont.Bold if on else QFont.Normal); self._merge(f)

    def toggle_italic(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontItalic(on); self._merge(f)

    def toggle_underline(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontUnderline(on); self._merge(f)

    def set_underline_style(self, stil) -> None:
        f = QTextCharFormat()
        f.setUnderlineStyle(stil)
        self._merge(f)

    def set_outline(self, an: bool) -> None:
        f = QTextCharFormat()
        f.setTextOutline(QPen(QColor("#000000")) if an else QPen(Qt.NoPen))
        self._merge(f)

    def set_letter_spacing(self, px: float) -> None:
        f = QTextCharFormat()
        f.setFontLetterSpacingType(QFont.AbsoluteSpacing)
        f.setFontLetterSpacing(px)
        self._merge(f)

    def set_capitalization(self, cap) -> None:
        f = QTextCharFormat()
        f.setFontCapitalization(cap)
        self._merge(f)

    def toggle_strike(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontStrikeOut(on); self._merge(f)

    def set_script(self, kind: str | None) -> None:
        f = QTextCharFormat()
        f.setVerticalAlignment({"sup": QTextCharFormat.AlignSuperScript,
                                "sub": QTextCharFormat.AlignSubScript}.get(kind, QTextCharFormat.AlignNormal))
        self._merge(f)

    def set_font_family(self, family: str) -> None:
        f = QTextCharFormat(); f.setFontFamilies([family]); self._merge(f)

    def set_font_size(self, pt: float) -> None:
        if pt > 0:
            f = QTextCharFormat(); f.setFontPointSize(pt); self._merge(f)

    def grow_font(self, delta: float) -> None:
        cur = self.textCursor()
        size = cur.charFormat().fontPointSize() or self.document().defaultFont().pointSizeF() or 11
        self.set_font_size(max(1.0, min(400.0, size + delta)))

    def set_text_color(self, color: QColor | None) -> None:
        f = QTextCharFormat()
        f.setForeground(QBrush(color) if color else QBrush(Qt.NoBrush))
        if color is None:
            f.clearProperty(QTextFormat.ForegroundBrush)
        self._merge(f)

    def set_highlight(self, color: QColor | None) -> None:
        f = QTextCharFormat()
        if color:
            f.setBackground(QBrush(color))
        else:
            f.setBackground(QBrush(Qt.NoBrush))
        self._merge(f)

    def change_case(self, mode: str) -> None:
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        txt = cur.selectedText()
        new = {"upper": txt.upper(), "lower": txt.lower(), "title": txt.title()}[mode]
        if new != txt:
            cur.insertText(new)

    def clear_formatting(self) -> None:
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        cur.beginEditBlock()
        cur.setCharFormat(QTextCharFormat())
        bf = QTextBlockFormat()
        cur.setBlockFormat(bf)
        cur.endEditBlock()

    # ---- Absatz ---------------------------------------------------------------
    def _block_merge(self, fn) -> None:
        cur = self.textCursor()
        cur.beginEditBlock()
        start, end = sorted((cur.anchor(), cur.position()))
        c = QTextCursor(self.document()); c.setPosition(start)
        blk = c.block()
        while blk.isValid() and blk.position() <= end:
            cc = QTextCursor(blk)
            bf = cc.blockFormat()
            fn(bf)
            cc.setBlockFormat(bf)
            blk = blk.next()
        cur.endEditBlock()

    def set_alignment(self, al: Qt.AlignmentFlag) -> None:
        def f(bf):
            bf.setAlignment(al)
            if (al & Qt.AlignHCenter) and self.opt("schreibhilfe/akZentriert", True):
                bf.setTextIndent(0)               # „Bei zentriertem Ausrichten Erstzeileneinzug löschen“
        self._block_merge(f)

    def change_indent(self, delta_mm: float) -> None:
        d = mm_to_px(delta_mm)
        self._block_merge(lambda bf: bf.setLeftMargin(max(0.0, bf.leftMargin() + d)))

    def set_page_break_before(self, an: bool) -> None:
        def f(bf):
            bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore if an else QTextFormat.PageBreak_Auto)
        self._block_merge(f)

    def set_indents(self, left_mm: float, right_mm: float, first_mm: float) -> None:
        def f(bf):
            bf.setLeftMargin(mm_to_px(left_mm)); bf.setRightMargin(mm_to_px(right_mm))
            bf.setTextIndent(mm_to_px(first_mm))
        self._block_merge(f)

    def set_line_spacing(self, factor: float) -> None:
        self._block_merge(lambda bf: bf.setLineHeight(factor * 100, LH_PROPORTIONAL))

    def set_paragraph_spacing(self, before_pt: float, after_pt: float) -> None:
        def f(bf):
            bf.setTopMargin(before_pt / 0.75); bf.setBottomMargin(after_pt / 0.75)
        self._block_merge(f)

    def toggle_list(self, kind: str, style=None) -> None:
        cur = self.textCursor()
        style = style if style is not None else (
            QTextListFormat.ListDisc if kind == "bullet" else QTextListFormat.ListDecimal)
        lst = cur.currentList()
        if lst and lst.format().style() == style:
            cur.beginEditBlock()
            blk = cur.block()
            lst.remove(blk)
            bf = cur.blockFormat(); bf.setIndent(0); bf.setLeftMargin(0); cur.setBlockFormat(bf)
            cur.endEditBlock()
            return
        fmt = QTextListFormat(); fmt.setStyle(style); fmt.setIndent(1)
        cur.createList(fmt)

    def list_level(self, delta: int) -> None:
        cur = self.textCursor()
        lst = cur.currentList()
        if not lst:
            return
        fmt = lst.format()
        fmt.setIndent(max(1, min(9, fmt.indent() + delta)))
        lst.setFormat(fmt)

    def apply_style(self, name: str) -> None:
        """Formatvorlage auf alle Absätze der Markierung (oder den Absatz am Zeiger) anwenden."""
        cur = self.textCursor()
        cur.beginEditBlock()
        von, bis = sorted((cur.anchor(), cur.position()))
        c = QTextCursor(self.document()); c.setPosition(von)
        blk = c.block()
        while blk.isValid() and blk.position() <= bis:
            self._stil_auf_block(blk, name)
            blk = blk.next()
        cur.endEditBlock()
        self.setFocus()

    def _stil_auf_block(self, blk, name: str) -> None:
        d = stile.definition(name)
        cc = QTextCursor(blk)
        bf = cc.blockFormat()
        level = d["ebene"]
        bf.setHeadingLevel(level)
        key = d.get("key")
        if key:
            bf.setProperty(STYLE_PROP, key)
        else:
            bf.clearProperty(STYLE_PROP)
        bf.setTopMargin(d["vor"] / 0.75); bf.setBottomMargin(d["nach"] / 0.75)
        if d["ausr"]:
            bf.setAlignment({"links": Qt.AlignLeft, "mitte": Qt.AlignHCenter, "rechts": Qt.AlignRight, "block": Qt.AlignJustify}[d["ausr"]])
        cc.setBlockFormat(bf)
        sel = QTextCursor(blk)
        sel.movePosition(QTextCursor.StartOfBlock)
        sel.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        f = QTextCharFormat()
        f.setFontWeight(QFont.Bold if d["fett"] else QFont.Normal)
        f.setFontItalic(d["kursiv"])
        f.setFontPointSize(d["groesse"] or self.document().defaultFont().pointSizeF() or 11)
        if d["schrift"]:
            f.setFontFamilies([d["schrift"]])
        if d["farbe"]:
            f.setForeground(QColor(d["farbe"]))
        sel.mergeCharFormat(f)

    def stil_neu_anwenden(self, name: str) -> int:
        """Nach „Formatvorlagen verwalten“: alle Absätze dieser Vorlage im Dokument neu formatieren."""
        n = 0
        cur = QTextCursor(self.document())
        cur.beginEditBlock()
        blk = self.document().firstBlock()
        while blk.isValid():
            if self._stil_name(blk.blockFormat()) == name:
                self._stil_auf_block(blk, name); n += 1
            blk = blk.next()
        cur.endEditBlock()
        return n

    @staticmethod
    def _stil_name(bf) -> str:
        lvl = bf.headingLevel()
        if lvl in (1, 2, 3):
            return f"Überschrift {lvl}"
        key = bf.property(STYLE_PROP) if bf.hasProperty(STYLE_PROP) else None
        for pfad in ("Title", "Subtitle", "Quote", "No Spacing"):
            if key == pfad:
                return stile.key_zu_name(pfad)
        return "Standard"

    def current_style(self) -> str:
        return self._stil_name(self.textCursor().blockFormat())

    # ---- Einfügen ----------------------------------------------------------------
    def insert_page_break(self) -> None:
        cur = self.textCursor()
        bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
        cur.insertBlock(bf)

    def insert_column_break(self) -> None:
        from .zusatz import B_SPALTE
        cur = self.textCursor()
        bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore); bf.setProperty(B_SPALTE, 1)
        cur.insertBlock(bf)

    def insert_table(self, rows: int, cols: int, borders: bool = True) -> None:
        tf = QTextTableFormat()
        tf.setCellPadding(4); tf.setCellSpacing(0)
        tf.setBorder(0.5 if borders else 0); tf.setBorderCollapse(True)
        tf.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        t = self.textCursor().insertTable(rows, cols, tf)
        self.setTextCursor(t.cellAt(0, 0).firstCursorPosition())

    def insert_image(self, path: str) -> bool:
        img = QImage(path)
        if img.isNull():
            return False
        name = f"bild-{id(img)}-{self.document().revision()}"
        self.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
        w = float(img.width())
        maxw = self.page.content_width_px
        if w > maxw:
            scale = maxw / w
        else:
            scale = 1.0
        f = QTextImageFormat(); f.setName(name)
        f.setWidth(img.width() * scale); f.setHeight(img.height() * scale)
        self.textCursor().insertImage(f)
        return True

    def insert_link(self, url: str, text: str | None = None) -> None:
        cur = self.textCursor()
        f = QTextCharFormat()
        f.setAnchor(True); f.setAnchorHref(url)
        f.setForeground(QBrush(QColor("#0563C1"))); f.setFontUnderline(True)
        if cur.hasSelection():
            cur.mergeCharFormat(f)
        else:
            cur.insertText(text or url, f)

    # ---- Suchen/Ersetzen ---------------------------------------------------------------
    def find_text(self, text: str, backwards=False, case=False, whole=False) -> bool:
        if not text:
            return False
        flags = QTextDocument.FindFlag(0)
        if backwards:
            flags |= QTextDocument.FindBackward
        if case:
            flags |= QTextDocument.FindCaseSensitively
        if whole:
            flags |= QTextDocument.FindWholeWords
        if self.find(text, flags):
            return True
        # Umbruch am Dokumentende/-anfang
        cur = self.textCursor()
        cur.movePosition(QTextCursor.End if backwards else QTextCursor.Start)
        self.setTextCursor(cur)
        return self.find(text, flags)

    def replace_current(self, find: str, repl: str, case=False) -> bool:
        cur = self.textCursor()
        sel = cur.selectedText()
        if cur.hasSelection() and (sel == find or (not case and sel.lower() == find.lower())):
            cur.insertText(repl)
            return True
        return False

    def replace_all(self, find: str, repl: str, case=False, whole=False) -> int:
        if not find:
            return 0
        flags = QTextDocument.FindFlag(0)
        if case:
            flags |= QTextDocument.FindCaseSensitively
        if whole:
            flags |= QTextDocument.FindWholeWords
        doc = self.document()
        cur = QTextCursor(doc)
        cur.beginEditBlock()
        n = 0
        pos = 0
        while True:
            found = doc.find(find, pos, flags)
            if found.isNull():
                break
            found.insertText(repl)
            pos = found.position()
            n += 1
        cur.endEditBlock()
        return n

    # ---- Bilder im Text (Bildtools) -------------------------------------------------------------------
    def _bild_cursor(self):
        c = self.textCursor()
        if c.charFormat().isImageFormat() and c.hasSelection():
            return c
        # Zeiger direkt vor einem Bild?
        c2 = QTextCursor(c)
        c2.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        if c2.charFormat().isImageFormat():
            return c2
        return None

    def bild_format(self):
        c = self._bild_cursor()
        return c.charFormat().toImageFormat() if c is not None else None

    def bild_setzen(self, width=None, height=None, alt=None) -> None:
        c = self._bild_cursor()
        if c is None:
            return
        f = c.charFormat().toImageFormat()
        if width is not None:
            f.setWidth(width)
        if height is not None:
            f.setHeight(height)
        if alt is not None:
            f.setProperty(STYLE_PROP + 1, alt)
        c.setCharFormat(f)

    def contextMenuEvent(self, e) -> None:
        m = self.createStandardContextMenu()
        if self.kontext_hook is not None:
            pos = self.cursorForPosition(e.pos()).position()
            self.kontext_hook(m, pos)
        if self._bild_cursor() is not None and not self.isReadOnly():
            from . import umbruch as U
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
        mini = self.mini_hook is not None and self.opt("ui/mini_rechtsklick", True) and not self.isReadOnly()
        if mini:
            self.mini_hook(self, e.globalPos(), True)
        m.exec(e.globalPos())
        m.deleteLater()
        if mini:
            self.mini_hook(None, None, True)

    def _wortweise(self) -> None:
        """Wortweise markieren: eine mit der Maus gezogene Auswahl wird an Wortgrenzen erweitert."""
        c = self.textCursor()
        von, bis = c.selectionStart(), c.selectionEnd()
        if bis - von < 2 or c.selectedText() in ("\u2029",):
            return
        a = QTextCursor(self.document()); a.setPosition(von); a.movePosition(QTextCursor.StartOfWord)
        b = QTextCursor(self.document()); b.setPosition(bis)
        if not b.atBlockEnd() and b.positionInBlock() > 0 and self.document().characterAt(bis - 1).isalnum():
            b.movePosition(QTextCursor.EndOfWord)
        neu = QTextCursor(self.document())
        rueckwaerts = c.position() < c.anchor()
        neu.setPosition(b.position() if rueckwaerts else a.position())
        neu.setPosition(a.position() if rueckwaerts else b.position(), QTextCursor.KeepAnchor)
        self.setTextCursor(neu)

    def _cursor_at(self, pos: int) -> QTextCursor:
        c = QTextCursor(self.document())
        c.setPosition(pos)
        return c

    def mouseReleaseEvent(self, e) -> None:
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
                from .verweise import intern_springen
                intern_springen(self, href)
                return
            if href:
                from PySide6.QtCore import QUrl as _U
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(_U(href))
                return
        if e.button() == Qt.LeftButton and not self.textCursor().hasSelection() and not self.isReadOnly():
            from .sendungen import kasten_umschalten
            if kasten_umschalten(self, self.cursorForPosition(e.pos()).position()):
                return
        c = self.cursorForPosition(e.pos())
        c2 = QTextCursor(c)
        c2.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        if c2.charFormat().isImageFormat() and not self.textCursor().hasSelection():
            r = self.cursorRect(c)
            if abs(e.pos().x() - r.x()) < c2.charFormat().toImageFormat().width() + 2:
                self.setTextCursor(c2)

    # ---- Anzeige: Zeilenfokus, Eckmarken, Lesehilfe --------------------------------------------------
    def set_zeilenfokus(self, an: bool) -> None:
        self.zeilenfokus = an
        self.viewport().update()

    def set_marken(self, an: bool) -> None:
        self.marken = an
        self.viewport().update()

    def set_lesehilfe(self, papier: str, buchstaben: float, wort: float) -> None:
        self.setStyleSheet(f"QTextEdit {{ background: {papier}; color: black; }}")
        f = QFont(self.document().defaultFont())
        f.setLetterSpacing(QFont.AbsoluteSpacing, buchstaben)
        f.setWordSpacing(wort)
        self.document().setDefaultFont(f)

    def paintEvent(self, e) -> None:
        sp = self._spalten_aktiv()
        if sp:
            self._sp_zeichnen(e)
        else:
            super().paintEvent(e)
        vp = self.viewport()
        p = QPainter(vp)
        self._schmuck_zeichnen(p)
        if self.gitter:
            self._gitter_zeichnen(p)
        if not self.web and self._hat_rahmen():
            from .pagination import absatzrahmen_zeichnen
            if sp:
                g = self._sp_geo()
                for lp in range(max(1, self.document().pageCount())):
                    k, j = divmod(lp, g["n"])
                    x0, y0 = g["ml"] + j * (g["cb"] + g["g"]), g["mt"] + k * g["ch"]
                    p.save()
                    p.setClipRect(QRectF(x0 - 6, y0, g["cb"] + 12, g["ch"]))
                    p.translate(x0, y0 - lp * g["ch"])
                    absatzrahmen_zeichnen(p, self.document(), self.zoom)
                    p.restore()
            else:
                p.save()
                p.translate(0, -self.verticalScrollBar().value())
                absatzrahmen_zeichnen(p, self.document(), self.zoom)
                p.restore()
        if self.page.zeilennummern and not self.web and not sp:
            self._zeilennummern_zeichnen(p)
        if self.marken and not self.web:
            z = self.zoom
            ml, mt = int(mm_to_px(self.page.margin_left_mm) * z), int(mm_to_px(self.page.margin_top_mm) * z)
            mr = int(mm_to_px(self.page.margin_right_mm) * z)
            y = mt - self.verticalScrollBar().value()
            p.setPen(QPen(QColor("#868e96"), 1))
            L, x2 = 14, vp.width() - mr
            for x, dx in ((ml, 1), (x2, -1)):
                p.drawLine(x, y - 1, x + dx * L, y - 1)
                p.drawLine(x - dx, y - L, x - dx, y - 1)
        self._extras_zeichnen(p, sp)
        if sp:
            g = self._sp_geo()
            blaetter = max(1, -(-max(1, self.document().pageCount()) // g["n"]))
            if self.page.spalten_linie:
                p.setPen(QPen(QColor("#868e96"), 1))
                for k in range(blaetter):
                    for j in range(1, g["n"]):
                        x = int(g["ml"] + j * (g["cb"] + g["g"]) - g["g"] / 2)
                        p.drawLine(x, int(g["mt"] + k * g["ch"]), x, int(g["mt"] + (k + 1) * g["ch"]))
            p.setPen(QPen(QColor("#868e96"), 1, Qt.DashLine))
            f = p.font(); f.setPointSizeF(8); p.setFont(f)
            for k in range(1, blaetter):
                y = int(g["mt"] + k * g["ch"]) - 3
                p.drawLine(0, y, vp.width(), y)
                p.drawText(6, y - 2, f"Seite {k + 1}")
        elif self._breaks and not self.web:
            p.setPen(QPen(QColor("#868e96"), 1, Qt.DashLine))
            f = p.font(); f.setPointSizeF(8); p.setFont(f)
            n = self.document().characterCount()
            for k, pos in enumerate(self._breaks, start=2):
                if pos >= n:
                    continue
                r = self.cursorRect(self._cursor_at(pos))
                y = r.top() - 3
                if -20 < y < vp.height() + 20:
                    p.drawLine(0, y, vp.width(), y)
                    p.drawText(6, y - 2, f"Seite {k}")
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

    def _aenderungszeilen_gecacht(self) -> list:
        rev = self.document().revision()
        if self._zeilen_cache[0] != rev:
            self._zeilen_cache = (rev, aenderungszeilen(self.document()) if (self._hat_zusatz or self.verfolgen) else [])
        return self._zeilen_cache[1]

    def _extras_zeichnen(self, p: QPainter, sp: bool) -> None:
        """Objektanker, Änderungsbalken, Kopf- und Fußzeile im Rand der Seite."""
        if self.web:
            return
        vp, z, pg = self.viewport(), self.zoom, self.page
        # Objektanker neben Bildern, die vom Text umflossen werden (bei sichtbaren Formatierungszeichen)
        marks = bool(self.document().defaultTextOption().flags() & QTextOption.ShowTabsAndSpaces)
        if marks and self.opt("ui/objektanker", True):
            from .umbruch import schwebende_rahmen
            ankern = schwebende_rahmen(self.document())
            if ankern:
                f = QFont(p.font()); f.setPointSizeF(max(7.0, 10 * z)); p.setFont(f)
                p.setPen(QColor("#4c6ef5"))
                for pos in ankern:
                    r = self.cursorRect(self._cursor_at(pos))
                    p.drawText(max(0, r.x() - int(18 * z)), r.y() + r.height() // 2, "⚓")
        # Geänderte Zeilen
        seite = self.opt_text("aenderungen/balken", "links")
        if seite in ("links", "rechts", "außen"):
            zeilen = self._aenderungszeilen_gecacht()
            if zeilen:
                p.setPen(QPen(QColor("#c92a2a"), 1.6))
                for t, u in zeilen:
                    if sp:
                        g = self._sp_geo()
                        vx, vy = self._sp_view(0, t)
                        x = vx + (g["cb"] + 8 * z if seite == "rechts" else -8 * z)
                        y0, y1 = vy, vy + (u - t)
                    else:
                        x = (vp.width() - mm_to_px(pg.margin_right_mm) * z + 8 * z) if seite == "rechts" else mm_to_px(pg.margin_left_mm) * z - 8 * z
                        y0, y1 = t, u
                    p.drawLine(int(x), int(y0), int(x), int(y1))
        # Kopf- und Fußzeile (erste Seite oben, letzte unten)
        if self.opt("ui/kopffuss_anzeigen", True):
            kopf = pg.first_header if pg.diff_first else pg.header
            fuss = pg.footer
            f = QFont(p.font()); f.setPixelSize(max(6, int(11 * z))); p.setFont(f)
            p.setPen(QColor("#868e96"))
            ml, mr = mm_to_px(pg.margin_left_mm) * z, mm_to_px(pg.margin_right_mm) * z
            breite = vp.width() - ml - mr

            def zeile(hf, y):
                if hf.is_empty():
                    return
                text = hf.text.replace("{PAGE}", str(max(1, self.current_page()))).replace("{PAGES}", str(self._pages))
                fl = {"center": Qt.AlignHCenter, "right": Qt.AlignRight}.get(hf.align, Qt.AlignLeft)
                p.drawText(QRectF(ml, y, breite, 18 * z), int(fl | Qt.AlignVCenter), text)
            zeile(kopf, mm_to_px(8) * z)
            zeile(fuss, vp.height() - mm_to_px(8) * z - 18 * z)

    # ---- Schreibhilfe: Wellenlinien, Ersetzen, Vorhersage, AutoKorrektur -------------------
    WELLE = {"fehler": "#e8590c", "tipp": "#1c7ed6", "hinweis": "#868e96"}

    def cut(self) -> None:
        if self.verfolgen and self.textCursor().hasSelection():
            self.copy()
            c = self.textCursor()
            self._loesche_verfolgt(c.selectionStart(), c.selectionEnd(), ende=True)
            return
        super().cut()

    def set_wellen(self, funde: list) -> None:
        self._wellen = funde
        self._overlays_neu()

    def replace_range(self, von: int, bis: int, neu: str, erwartet: str | None = None) -> bool:
        c = QTextCursor(self.document())
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        if erwartet is not None and c.selectedText().replace("\u2029", "\n") != erwartet:
            return False
        fmt = QTextCharFormat(c.charFormat())
        c.insertText(neu, fmt) if neu else c.removeSelectedText()
        return True

    def select_range(self, von: int, bis: int) -> None:
        c = QTextCursor(self.document())
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        self.setTextCursor(c); self.ensureCursorVisible(); self.setFocus()

    def _wort_vor_cursor(self) -> str:
        c = self.textCursor()
        txt = c.block().text()[:c.positionInBlock()]
        i = len(txt)
        while i > 0 and (txt[i - 1].isalpha() or txt[i - 1] in "äöüßÄÖÜ"):
            i -= 1
        return txt[i:]

    def _vorschlaege_zeigen(self) -> None:
        if not self.vorhersage or self.textCursor().hasSelection():
            self._popup.hide(); return
        w = self._wort_vor_cursor()
        vs = self.vorhersage(w) if len(w) >= 3 else []
        if not vs:
            self._popup.hide(); return
        gross = w[:1].isupper()
        self._popup.clear()
        for i, v in enumerate(vs, start=1):
            wort = v.capitalize() if gross else v
            it = QListWidgetItem(f"{i}  {wort}" if i <= 6 else wort)
            it.setData(Qt.UserRole, wort)
            self._popup.addItem(it)
        self._popup.setCurrentRow(0)
        r = self.cursorRect()
        self._popup.resize(220, min(200, 22 * len(vs) + 6))
        self._popup.move(self.viewport().mapToGlobal(QPoint(r.left(), r.bottom() + 4)))
        self._popup.show()

    def _vorschlag_nehmen(self, wort: str) -> None:
        w = self._wort_vor_cursor()
        c = self.textCursor()
        c.beginEditBlock()
        c.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(w))
        c.insertText(wort + " ")
        c.endEditBlock()
        self.setTextCursor(c); self._popup.hide()

    def _autokorr_anwenden(self) -> None:
        if not self.autokorr:
            return
        c = self.textCursor()
        if c.hasSelection():
            return
        alt = c.block().text()[:c.positionInBlock()]
        neu = self.autokorr(alt)
        if neu == alt:
            return
        von, bis, ersatz = kleinste_aenderung(alt, neu)
        start = c.block().position()
        ed = QTextCursor(self.document())
        ed.setPosition(start + von); ed.setPosition(start + bis, QTextCursor.KeepAnchor)
        fmt = QTextCharFormat(ed.charFormat())
        ed.insertText(ersatz, fmt) if ersatz else ed.removeSelectedText()
        end = QTextCursor(self.document())
        end.setPosition(start + len(neu))
        self.setTextCursor(end)

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key_Tab and e.modifiers() == Qt.NoModifier and not self.isReadOnly() and not self.textCursor().currentTable():
            from .vorlagen import naechste_luecke
            ziel = naechste_luecke(self.document(), self.textCursor().selectionEnd())
            if ziel:
                self.select_range(*ziel)
                return
        if self.verfolgen and not self.isReadOnly() and self._verfolgte_taste(e):
            return
        if self.gliederung and (e.modifiers() & Qt.AltModifier) and (e.modifiers() & Qt.ShiftModifier) \
                and e.key() in (Qt.Key_Left, Qt.Key_Right):
            self.gliederung_ebene(-1 if e.key() == Qt.Key_Left else 1)
            return
        if self._popup.isVisible():
            k = e.key()
            if k in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter):
                it = self._popup.currentItem()
                if it:
                    self._vorschlag_nehmen(it.data(Qt.UserRole)); e.accept(); return
            if (e.modifiers() & Qt.ControlModifier) and Qt.Key_1.value <= k <= Qt.Key_6.value:        # Strg+1…6: Vorschlag nehmen
                n = k - Qt.Key_1.value
                if n < self._popup.count():
                    self._vorschlag_nehmen(self._popup.item(n).data(Qt.UserRole)); e.accept(); return
            if k == Qt.Key_Escape:
                self._popup.hide(); e.accept(); return
            if k in (Qt.Key_Down, Qt.Key_Up):
                r = self._popup.currentRow() + (1 if k == Qt.Key_Down else -1)
                self._popup.setCurrentRow(max(0, min(self._popup.count() - 1, r))); e.accept(); return
        c0 = self.textCursor()
        k = e.key()
        # Tab/Rücktaste setzen den Einzug (nur am Absatzanfang)
        if self.opt("schreibhilfe/akTabEinzug", True) and not c0.hasSelection() and c0.atBlockStart() \
                and not c0.currentList() and k in (Qt.Key_Tab, Qt.Key_Backspace):
            bf = c0.blockFormat()
            if k == Qt.Key_Tab:
                self.change_indent(10); e.accept(); return
            if bf.leftMargin() > 0:
                self.change_indent(-10); e.accept(); return
        # Tippen ersetzt die Auswahl — ist das abgeschaltet, wird hinter die Auswahl geschrieben
        if c0.hasSelection() and e.text() and e.text().isprintable() and not (e.modifiers() & (Qt.ControlModifier | Qt.AltModifier)) \
                and not self.opt("bearbeiten/tippen_ersetzt", True):
            c0.setPosition(max(c0.anchor(), c0.position())); self.setTextCursor(c0)
        if k in (Qt.Key_Return, Qt.Key_Enter) and self.opt("schreibhilfe/akRechtsLeer", False) and not c0.hasSelection() \
                and (c0.blockFormat().alignment() & Qt.AlignRight):
            self._rechts_leerzeichen_weg(c0)
        super().keyPressEvent(e)
        t = e.text()
        if t == ")" and self.opt("schreibhilfe/akKreiszahl", False):
            self._kreiszahl()
        if t == " " and self.opt("autoformat/liste", True):
            self._autoformat_liste()
        if t and t in " .,;:!?\n\r":
            self._popup.hide()
            self._autokorr_anwenden()
            if t == " ":
                self._autokorr_extras()
        elif t and (t.isalpha() or e.key() == Qt.Key_Backspace):
            self._vorschlaege_zeigen()
        else:
            self._popup.hide()

    def _rechts_leerzeichen_weg(self, c: QTextCursor) -> None:
        """AutoKorrektur: Leerzeichen am Ende einer rechtsbündigen Zeile würden den Text nach links schieben — sie werden entfernt."""
        b = c.block()
        roh = b.text()
        ohne = roh.rstrip(" \t")
        if ohne != roh:
            k = QTextCursor(self.document())
            k.setPosition(b.position() + len(ohne)); k.setPosition(b.position() + len(roh), QTextCursor.KeepAnchor)
            k.removeSelectedText()

    def _kreiszahl(self) -> None:
        """AutoKorrektur: „(1)“ … „(20)“ werden zu ① … ⑳ (Optionen ▸ Bearbeiten ▸ AutoKorrektur)."""
        c = self.textCursor()
        vor = c.block().text()[:c.positionInBlock()]
        import re as _re
        m = _re.search(r"\((\d{1,2})\)$", vor)
        if m and 1 <= int(m.group(1)) <= 20:
            k = QTextCursor(self.document())
            k.setPosition(c.block().position() + m.start()); k.setPosition(c.block().position() + m.end(), QTextCursor.KeepAnchor)
            k.insertText(chr(0x2460 + int(m.group(1)) - 1))

    def _autoformat_liste(self) -> None:
        """„1. “ / „1) “ am Absatzanfang → Nummerierung, „* “ / „- “ / „• “ → Aufzählung."""
        c = self.textCursor()
        if c.hasSelection() or c.currentList():
            return
        vor = c.block().text()[:c.positionInBlock()]
        import re as _re
        art = None
        if _re.fullmatch(r"\d{1,3}[.)] ", vor):
            art = "number"
        elif vor in ("* ", "- ", "• ") and self.opt("autoformat/punkte", True):
            art = "bullet"
        if art == "number" and not self.opt("autoformat/liste", True):
            return
        if art:
            c.beginEditBlock()
            c.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
            c.removeSelectedText()
            self.toggle_list(art)
            c.endEditBlock()

    def _autokorr_extras(self) -> None:
        """Netzadressen → Hyperlinks; Leerzeichen am Absatzanfang → Erstzeileneinzug."""
        c = self.textCursor()
        if c.hasSelection():
            return
        vor = c.block().text()[:c.positionInBlock()]
        import re as _re
        if self.opt("schreibhilfe/akPfade", True):
            m = _re.search(r"(https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.-]+)[ ]$", vor)
            if m:
                start = c.block().position() + m.start(1)
                end = c.block().position() + m.end(1)
                url = m.group(1)
                href = url if _re.match(r"https?://", url) else ("mailto:" + url if "@" in url else "http://" + url)
                cc = QTextCursor(self.document()); cc.setPosition(start); cc.setPosition(end, QTextCursor.KeepAnchor)
                f = QTextCharFormat(); f.setAnchor(True); f.setAnchorHref(href)
                f.setForeground(QBrush(QColor("#0563C1"))); f.setFontUnderline(True)
                cc.mergeCharFormat(f)
        if self.opt("schreibhilfe/akErstzeile", False) and _re.fullmatch(r"[ \t]{3,}", vor):
            cc = QTextCursor(self.document()); cc.setPosition(c.block().position())
            cc.setPosition(c.block().position() + len(vor), QTextCursor.KeepAnchor); cc.removeSelectedText()
            bf = QTextCursor(c.block()).blockFormat(); bf.setTextIndent(mm_to_px(10))
            QTextCursor(self.document().findBlock(c.block().position())).setBlockFormat(bf)

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
