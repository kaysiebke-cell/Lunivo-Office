from __future__ import annotations

from PySide6.QtGui import (
    QTextDocument, QTextCursor, QTextFormat, QTextDocumentFragment,
)
from lunivo_writer.editor import stile

STYLES = dict.fromkeys(stile.NAMEN)  # nur die eingebauten

EINFUEGE_MODI = ["Quellformatierung beibehalten", "Zielformatierung verwenden", "Nur Text"]


def _ziel_fragment(html: str, standard) -> QTextDocumentFragment:
    """HTML einfügen, aber Schriftart, -größe, Farben und Hintergründe des Ziels behalten."""
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
                k = QTextCursor(d)
                k.setPosition(fr.position())
                k.setPosition(fr.position() + fr.length(), QTextCursor.KeepAnchor)
                k.setCharFormat(f)
            it += 1
        b = b.next()
    return QTextDocumentFragment(d)
