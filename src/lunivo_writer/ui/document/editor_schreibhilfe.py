"""Schreibhilfe im Text."""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QBrush, QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QListWidgetItem
from lunivo_writer.models.page import mm_to_px
from lunivo_writer.proofing.autokorrektur import kleinste_aenderung
from lunivo_writer.editor import stile


class SchreibhilfeBaustein:
    """Schreibhilfe im Text. Baustein von ``DocumentEditor`` (siehe ``lunivo_writer/ui/document/document_editor.py``)."""


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


    def _folge_vorher(self, e):
        """Return am Ende eines Absatzes, dessen Vorlage einen „folgenden Absatz“ kennt → (Name der Folgevorlage, Absatznummer)."""
        if e.key() not in (Qt.Key_Return, Qt.Key_Enter) or self.isReadOnly() or (e.modifiers() & ~Qt.KeypadModifier):
            return None
        c = self.textCursor()
        if c.hasSelection() or not c.atBlockEnd() or c.currentTable():
            return None
        name = self._stil_name(c.blockFormat())
        folge = stile.definition(name).get("folge") if name else None
        return (folge, c.blockNumber()) if folge and folge != name else None


    def _folge_danach(self, folge: str, nr: int) -> None:
        c = self.textCursor()
        if c.blockNumber() == nr + 1:                                   # der neue Absatz bekommt die Folgevorlage
            self._stil_auf_block(c.block(), folge)


    def _taste(self, e) -> None:
        if e.key() == Qt.Key_Tab and e.modifiers() == Qt.NoModifier and not self.isReadOnly() and not self.textCursor().currentTable():
            from lunivo_writer.editor.vorlagen import naechste_luecke
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
