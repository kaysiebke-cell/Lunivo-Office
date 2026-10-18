"""Der Editor: QTextEdit mit Seitenbreite, Formatierungsbefehlen und Seitenzählung."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import (
    QBrush, QColor, QFont, QImage, QPainter, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor,
    QTextDocument, QTextFormat, QTextFrameFormat, QTextImageFormat, QTextListFormat,
    QTextTableFormat, QTextLength,
)
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QScrollArea, QTextEdit

from ..document_io.docx_reader import LH_PROPORTIONAL, STYLE_PROP
from .page import PageSettings, mm_to_px
from ..services.autokorrektur import kleinste_aenderung
from .pagination import bind_layout, paginated_copy
from . import stile
from .zusatz_editor import ZusatzMixin

STYLES = dict.fromkeys(stile.NAMEN)            # Namen der Formatvorlagen (Definitionen: editor/stile.py)


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
        self.kontext_hook = None          # Rückruf(menü, position): ergänzt das Rechtsklick-Menü
        self.opt = lambda name, std=True: std      # Rückruf: Schalter aus den Optionen
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
        self.apply_page(self.page)

    # ---- Dokument und Seite ---------------------------------------------
    def _verbinde_groesse(self) -> None:
        self.document().documentLayout().documentSizeChanged.connect(self._passe_hoehe_an)

    def _passe_hoehe_an(self, *_):
        h = int(self.document().size().height()) + 4
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
        else:
            ff.setTopMargin(mm_to_px(page.margin_top_mm))
            ff.setBottomMargin(mm_to_px(page.margin_bottom_mm))
            ff.setLeftMargin(mm_to_px(page.margin_left_mm))
            ff.setRightMargin(mm_to_px(page.margin_right_mm))
            root.setFrameFormat(ff)
            self.setFixedWidth(int(mm_to_px(page.width_mm) * self.zoom) + 2)
        self._passe_hoehe_an()
        self._timer.start()
        self.pageApplied.emit()

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
        self._paged = paginated_copy(self.document(), self.page, self.noten)
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
        if self._paged is None:
            return 1
        pos = min(self.textCursor().position(), max(0, self._paged.characterCount() - 1))
        blk = self._paged.findBlock(pos)
        if not blk.isValid():
            return 1
        rect = self._paged.documentLayout().blockBoundingRect(blk)
        ch = self.page.content_height_px
        return max(1, min(self._pages, int(rect.top() // ch) + 1))

    def _cursor_moved(self) -> None:
        self.pageInfoChanged.emit(self.current_page(), self._pages)
        self.formatChanged.emit()

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
        m.exec(e.globalPos())
        m.deleteLater()

    def _cursor_at(self, pos: int) -> QTextCursor:
        c = QTextCursor(self.document())
        c.setPosition(pos)
        return c

    def mouseReleaseEvent(self, e) -> None:
        super().mouseReleaseEvent(e)
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
        super().paintEvent(e)
        vp = self.viewport()
        p = QPainter(vp)
        self._schmuck_zeichnen(p)
        if self.gitter:
            self._gitter_zeichnen(p)
        if not self.web and self._hat_rahmen():
            from .pagination import absatzrahmen_zeichnen
            p.save()
            p.translate(0, -self.verticalScrollBar().value())
            absatzrahmen_zeichnen(p, self.document(), self.zoom)
            p.restore()
        if self.page.zeilennummern and not self.web:
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
        if self._breaks and not self.web:
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
        super().keyPressEvent(e)
        t = e.text()
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
        super().insertFromMimeData(source)
