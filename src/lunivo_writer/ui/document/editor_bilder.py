"""Bilder im Text."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor
from lunivo_writer.services.docx_reader import STYLE_PROP


class BilderBaustein:
    """Bilder im Text. Baustein von ``DocumentEditor`` (siehe ``lunivo_writer/ui/document/document_editor.py``)."""


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
