"""Textumbruch um Bilder: Bilder, die links oder rechts stehen und vom Text umflossen werden.

Qt kennt das als „schwebendes Bild“: Das Bild steht als Zeichen im Absatz, dazu legt Qt einen unsichtbaren Rahmen
(QTextFrame mit FloatLeft/FloatRight) an, um den der Text läuft. Angelegt wird das über den HTML-Import (`float`), weil
QTextCursor dafür keine eigene Schnittstelle hat. Ein schwebendes Bild gehört zum Absatz, in dem es steht — es steht immer
am Absatzanfang (wie der Anker in Word).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextBlockFormat, QTextCursor, QTextDocument, QTextFrame, QTextFrameFormat, QTextImageFormat

from ..document_io.docx_reader import STYLE_PROP

ORIGINAL_PROP = STYLE_PROP + 3
ABSTAND_PX = 8.0
SEITEN = {QTextFrameFormat.FloatLeft: "links", QTextFrameFormat.FloatRight: "rechts"}


def _rahmen(frame: QTextFrame):
    for k in frame.childFrames():
        yield k
        yield from _rahmen(k)


def schwebende_rahmen(doc: QTextDocument) -> dict[int, QTextFrame]:
    """{Position des Bildzeichens: Rahmen} für alle schwebenden Bilder des Dokuments."""
    return {f.firstPosition() - 1: f for f in _rahmen(doc.rootFrame())
            if f.frameFormat().position() in SEITEN}


def schwebend(doc: QTextDocument, pos: int) -> str | None:
    """„links“ / „rechts“, wenn das Bild an Position pos schwebt; sonst None (Bild steht in der Zeile)."""
    f = schwebende_rahmen(doc).get(pos)
    return SEITEN.get(f.frameFormat().position()) if f is not None else None


def _gemerkt(neu: QTextImageFormat, alt: QTextImageFormat) -> None:
    for k in (STYLE_PROP + 1, ORIGINAL_PROP):
        if alt.hasProperty(k):
            neu.setProperty(k, alt.property(k))


def schwebend_einfuegen(doc: QTextDocument, blockpos: int, f: QTextImageFormat, seite: str) -> None:
    """Fügt das Bild f am Anfang des Absatzes bei blockpos als schwebendes Bild ein (seite: „links“ | „rechts“)."""
    c = QTextCursor(doc)
    c.setPosition(blockpos)
    css = "left" if seite == "links" else "right"
    c.insertHtml(f'<img src="{f.name()}" width="{f.width():.0f}" height="{f.height():.0f}" style="float:{css}">')
    c.setPosition(blockpos)
    c.setPosition(blockpos + 1, QTextCursor.KeepAnchor)
    neu = c.charFormat().toImageFormat()
    _gemerkt(neu, f)
    c.setCharFormat(neu)
    r = schwebende_rahmen(doc).get(blockpos)
    if r is not None:
        ff = r.frameFormat()
        ff.setMargin(ABSTAND_PX)
        r.setFrameFormat(ff)


def umbruch_setzen(ed, modus: str) -> bool:
    """Das markierte Bild: modus „zeile“ (mit Text in Zeile), „links“ oder „rechts“ (vom Text umflossen)."""
    c = ed._bild_cursor()
    if c is None:
        return False
    doc = ed.document()
    pos = c.selectionStart()
    aktuell = schwebend(doc, pos) or "zeile"
    if modus == "oben_unten":                                     # eigene, zentrierte Zeile: Text davor und danach, nichts daneben
        if aktuell != "zeile":
            umbruch_setzen(ed, "zeile")
            c = ed._bild_cursor()
            pos = c.selectionStart()
        c = QTextCursor(doc)
        c.beginEditBlock()
        c.setPosition(pos)
        b = doc.findBlock(pos)
        if pos > b.position():
            c.insertBlock()                                        # Text davor bleibt im alten Absatz
            pos += 1
        c.setPosition(pos + 1)
        if c.position() < doc.findBlock(pos).position() + doc.findBlock(pos).length() - 1:
            c.insertBlock()                                        # Text danach beginnt einen neuen Absatz
        bf = QTextBlockFormat(doc.findBlock(pos).blockFormat())
        bf.setAlignment(Qt.AlignHCenter)
        QTextCursor(doc.findBlock(pos)).setBlockFormat(bf)
        c.endEditBlock()
        sel = QTextCursor(doc)
        sel.setPosition(pos)
        sel.setPosition(pos + 1, QTextCursor.KeepAnchor)
        ed.setTextCursor(sel)
        doc.setModified(True)
        return True
    if aktuell == modus:
        return True
    f = c.charFormat().toImageFormat()
    if aktuell != "zeile" and modus != "zeile":                     # nur die Seite wechseln
        r = schwebende_rahmen(doc)[pos]
        ff = r.frameFormat()
        ff.setPosition(QTextFrameFormat.FloatLeft if modus == "links" else QTextFrameFormat.FloatRight)
        r.setFrameFormat(ff)
        doc.setModified(True)
        return True
    c.beginEditBlock()
    c.removeSelectedText()
    if modus == "zeile":
        k = QTextCursor(doc)
        k.setPosition(pos)
        k.insertImage(f)
        neu = pos
    else:
        neu = doc.findBlock(pos).position()
        schwebend_einfuegen(doc, neu, f, modus)
    c.endEditBlock()
    sel = QTextCursor(doc)
    sel.setPosition(neu)
    sel.setPosition(neu + 1, QTextCursor.KeepAnchor)
    ed.setTextCursor(sel)
    doc.setModified(True)
    return True
