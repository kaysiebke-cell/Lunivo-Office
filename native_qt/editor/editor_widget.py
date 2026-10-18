"""Der Editor: QTextEdit mit Seitenbreite, Formatierungsbefehlen und Seitenzählung."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import (
    QBrush, QColor, QFont, QImage, QPainter, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor,
    QTextDocument, QTextFormat, QTextFrameFormat, QTextImageFormat, QTextListFormat,
    QTextTableFormat, QTextLength,
)
from PySide6.QtWidgets import QListWidget, QTextEdit

from ..document_io.docx_reader import LH_PROPORTIONAL, STYLE_PROP
from .page import PageSettings, mm_to_px
from ..services.autokorrektur import kleinste_aenderung
from .pagination import bind_layout, paginated_copy

# Formatvorlagen: Name → (Überschriftsebene, Punktgröße, fett, kursiv)
STYLES = {
    "Standard": (0, None, False, False),
    "Überschrift 1": (1, 20, True, False),
    "Überschrift 2": (2, 16, True, False),
    "Überschrift 3": (3, 14, True, False),
    "Titel": (0, 26, False, False),
    "Untertitel": (0, 15, False, True),
    "Zitat": (0, None, False, True),
}
STYLE_KEY = {"Titel": "Title", "Untertitel": "Subtitle", "Zitat": "Quote"}


class DocumentEditor(QTextEdit):
    pageInfoChanged = Signal(int, int)       # aktuelle Seite, Seitenzahl
    formatChanged = Signal()                 # Cursor-Format hat sich geändert

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = PageSettings()
        self.setAcceptRichText(True)
        self.setFrameShape(QTextEdit.NoFrame)
        self.setUndoRedoEnabled(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.show_marks = False
        self.zeilenfokus = False
        self.marken = True                 # Textbegrenzungen (Eckmarken am Textrand)
        self.vorhersage = None            # Rückruf: Wortanfang → Liste von Vorschlägen
        self.autokorr = None              # Rückruf: Text vor dem Zeiger → korrigierter Text
        self._wellen: list[dict] = []
        self._popup = QListWidget(None)
        self._popup.setWindowFlags(Qt.ToolTip)
        self._popup.setFocusPolicy(Qt.NoFocus)
        self._popup.itemClicked.connect(lambda it: self._vorschlag_nehmen(it.text()))
        self._pages = 1
        self._paged: QTextDocument | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._recount)
        self.cursorPositionChanged.connect(self._cursor_moved)
        self.cursorPositionChanged.connect(lambda: self.zeilenfokus and self.viewport().update())
        self.currentCharFormatChanged.connect(lambda *_: self.formatChanged.emit())
        self.document().contentsChanged.connect(self._timer.start)
        self.apply_page(self.page)

    # ---- Dokument und Seite ---------------------------------------------
    def set_document_and_page(self, doc: QTextDocument, page: PageSettings) -> None:
        self.setDocument(doc)
        doc.setDocumentMargin(0)
        doc.contentsChanged.connect(self._timer.start)
        self.apply_page(page)
        doc.setModified(False)
        doc.clearUndoRedoStacks()

    def apply_page(self, page: PageSettings) -> None:
        self.page = page
        doc = self.document()
        bind_layout(doc)
        doc.setDocumentMargin(0)
        root = doc.rootFrame()
        ff: QTextFrameFormat = root.frameFormat()
        ff.setTopMargin(mm_to_px(page.margin_top_mm))
        ff.setBottomMargin(mm_to_px(page.margin_bottom_mm))
        ff.setLeftMargin(mm_to_px(page.margin_left_mm))
        ff.setRightMargin(mm_to_px(page.margin_right_mm))
        root.setFrameFormat(ff)
        self.setFixedWidth(int(mm_to_px(page.width_mm)) + 2)
        self._timer.start()

    def page_settings_changed(self, page: PageSettings) -> None:
        self.apply_page(page)
        self.document().setModified(True)

    # ---- Seitenzählung -----------------------------------------------------
    def _recount(self) -> None:
        self._paged = paginated_copy(self.document(), self.page)
        self._pages = max(1, self._paged.pageCount())
        self._cursor_moved()

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
        self._block_merge(lambda bf: bf.setAlignment(al))

    def change_indent(self, delta_mm: float) -> None:
        d = mm_to_px(delta_mm)
        self._block_merge(lambda bf: bf.setLeftMargin(max(0.0, bf.leftMargin() + d)))

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
        level, size, bold, italic = STYLES[name]
        cur = self.textCursor()
        cur.beginEditBlock()
        bf = cur.blockFormat()
        bf.setHeadingLevel(level)
        if name in STYLE_KEY:
            bf.setProperty(STYLE_PROP, STYLE_KEY[name])
        else:
            bf.clearProperty(STYLE_PROP)
        bf.setTopMargin(12 if level == 1 else 8 if level else 0)
        bf.setBottomMargin(6 if level else 0)
        cur.setBlockFormat(bf)
        sel = QTextCursor(cur.block())
        sel.movePosition(QTextCursor.StartOfBlock)
        sel.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        f = QTextCharFormat()
        f.setFontWeight(QFont.Bold if bold else QFont.Normal)
        f.setFontItalic(italic)
        f.setFontPointSize(size or self.document().defaultFont().pointSizeF() or 11)
        sel.mergeCharFormat(f)
        cur.endEditBlock()
        self.setFocus()

    def current_style(self) -> str:
        bf = self.textCursor().blockFormat()
        lvl = bf.headingLevel()
        if lvl in (1, 2, 3):
            return f"Überschrift {lvl}"
        key = bf.property(STYLE_PROP) if bf.hasProperty(STYLE_PROP) else None
        for k, v in STYLE_KEY.items():
            if v == key:
                return k
        return "Standard"

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
        self.textCursor().insertTable(rows, cols, tf)

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
        if self.marken:
            ml, mt = int(mm_to_px(self.page.margin_left_mm)), int(mm_to_px(self.page.margin_top_mm))
            mr = int(mm_to_px(self.page.margin_right_mm))
            y = mt - self.verticalScrollBar().value()
            p.setPen(QPen(QColor("#868e96"), 1))
            L, x2 = 14, vp.width() - mr
            for x, dx in ((ml, 1), (x2, -1)):
                p.drawLine(x, y - 1, x + dx * L, y - 1)
                p.drawLine(x - dx, y - L, x - dx, y - 1)
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

    def set_wellen(self, funde: list) -> None:
        self._wellen = funde
        sel = []
        n = self.document().characterCount()
        for f in funde:
            if f["bis"] > n or f["von"] >= f["bis"]:
                continue
            c = QTextCursor(self.document())
            c.setPosition(f["von"]); c.setPosition(f["bis"], QTextCursor.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setUnderlineStyle(QTextCharFormat.WaveUnderline)
            fmt.setUnderlineColor(QColor(self.WELLE.get(f["art"], "#868e96")))
            sel.append(QTextEdit.ExtraSelection())
            sel[-1].cursor = c
            sel[-1].format = fmt
        self.setExtraSelections(sel)

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
        self._popup.addItems([v.capitalize() if gross else v for v in vs])
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
        if self._popup.isVisible():
            k = e.key()
            if k in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter):
                it = self._popup.currentItem()
                if it:
                    self._vorschlag_nehmen(it.text()); e.accept(); return
            if k == Qt.Key_Escape:
                self._popup.hide(); e.accept(); return
            if k in (Qt.Key_Down, Qt.Key_Up):
                r = self._popup.currentRow() + (1 if k == Qt.Key_Down else -1)
                self._popup.setCurrentRow(max(0, min(self._popup.count() - 1, r))); e.accept(); return
        super().keyPressEvent(e)
        t = e.text()
        if t and t in " .,;:!?\n\r":
            self._popup.hide()
            self._autokorr_anwenden()
        elif t and (t.isalpha() or e.key() == Qt.Key_Backspace):
            self._vorschlaege_zeigen()
        else:
            self._popup.hide()

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
