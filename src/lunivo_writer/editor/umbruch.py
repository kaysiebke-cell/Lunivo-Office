"""Textumbruch um Bilder: Bilder, die links oder rechts stehen und vom Text umflossen werden.

Ein schwebendes Bild ist ein Rahmen (`QTextFrame` mit `FloatLeft`/`FloatRight`), in dem das Bild steht; der Text läuft darum herum.
Qt legt vor einem solchen Rahmen einen leeren Hilfsabsatz an. Er ist der Anker des Bildes: klein gesetzt (kaum sichtbar), mit
`B_ANKER` gekennzeichnet und wird beim Speichern nicht als Absatz geschrieben. Das Bild gehört zum Absatz, der dem Rahmen folgt —
es steht immer an dessen Anfang (wie der Anker in Word). Der Schlüssel eines Bildes ist die Position seines Zeichens im Rahmen.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextBlock, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextFrame, QTextFrameFormat, QTextImageFormat

from lunivo_writer.editor.zusatz import B_ANKER

ABSTAND_PX = 8.0
SEITEN = {QTextFrameFormat.FloatLeft: "links", QTextFrameFormat.FloatRight: "rechts"}


def _rahmen(frame: QTextFrame):
    for k in frame.childFrames():
        yield k
        yield from _rahmen(k)


def schwebende_rahmen(doc: QTextDocument) -> dict[int, QTextFrame]:
    """{Position des Bildzeichens: Rahmen} für alle schwebenden Bilder des Dokuments."""
    return {f.firstPosition(): f for f in _rahmen(doc.rootFrame()) if f.frameFormat().position() in SEITEN}


def schwebend(doc: QTextDocument, pos: int) -> str | None:
    """„links“ / „rechts“, wenn das Bild an Position pos schwebt; sonst None (Bild steht in der Zeile)."""
    f = schwebende_rahmen(doc).get(pos)
    return SEITEN.get(f.frameFormat().position()) if f is not None else None


def bild_im_rahmen(rahmen: QTextFrame) -> QTextImageFormat | None:
    """Das Bild, das in einem schwebenden Rahmen steht."""
    it = rahmen.begin()
    while not it.atEnd():
        blk = it.currentBlock()
        if blk.isValid():
            bit = blk.begin()
            while not bit.atEnd():
                if bit.fragment().isValid() and bit.fragment().charFormat().isImageFormat():
                    return bit.fragment().charFormat().toImageFormat()
                bit += 1
        it += 1
    return None


def ist_anker(blk: QTextBlock) -> bool:
    return blk.isValid() and blk.blockFormat().hasProperty(B_ANKER)


def schwebend_einfuegen(doc: QTextDocument, blockpos: int, f: QTextImageFormat, seite: str) -> int:
    """Fügt das Bild f vor dem Absatz bei blockpos als schwebendes Bild ein (seite: „links“ | „rechts“).
    Gibt die Position des Bildzeichens zurück."""
    c = QTextCursor(doc)
    c.beginEditBlock()
    c.setPosition(blockpos)
    breite = f.width()
    if not breite:
        bild = doc.resource(QTextDocument.ImageResource, f.name())
        breite = bild.width() if bild is not None and hasattr(bild, "width") else 100
    ff = QTextFrameFormat()
    ff.setPosition(QTextFrameFormat.FloatLeft if seite == "links" else QTextFrameFormat.FloatRight)
    ff.setBorder(0); ff.setPadding(0); ff.setMargin(ABSTAND_PX); ff.setWidth(breite)
    rahmen = c.insertFrame(ff)
    QTextCursor(rahmen).insertImage(QTextImageFormat(f))
    anker = doc.findBlock(rahmen.firstPosition() - 1)                  # der leere Absatz, den Qt vor dem Rahmen angelegt hat
    if anker.isValid() and not anker.text():
        ac = QTextCursor(anker)
        bf = QTextBlockFormat(anker.blockFormat())
        bf.setProperty(B_ANKER, 1); bf.setTopMargin(0); bf.setBottomMargin(0)
        ac.setBlockFormat(bf)
        cf = QTextCharFormat(); cf.setFontPointSize(1)
        ac.setBlockCharFormat(cf)
    c.endEditBlock()
    return rahmen.firstPosition()


def absatz_nach_rahmen(doc: QTextDocument, bildpos: int) -> QTextBlock:
    """Der Absatz, zu dem das schwebende Bild bei bildpos gehört (er folgt dem Rahmen)."""
    return doc.findBlock(schwebende_rahmen(doc)[bildpos].lastPosition() + 1)


def schwebend_entfernen(doc: QTextDocument, pos: int) -> int:
    """Nimmt das schwebende Bild bei pos samt Rahmen und Anker aus dem Dokument. Gibt die Stelle zurück, an der der Absatz
    jetzt beginnt (dort kann das Bild wieder in der Zeile eingesetzt werden)."""
    r = schwebende_rahmen(doc).get(pos)
    if r is None:
        return pos
    anker = doc.findBlock(r.firstPosition() - 1)
    von = anker.position() if ist_anker(anker) else r.firstPosition() - 1
    c = QTextCursor(doc)
    c.setPosition(von)
    c.setPosition(r.lastPosition() + 1, QTextCursor.KeepAnchor)
    c.removeSelectedText()
    return von


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
    if aktuell == "zeile":
        c.removeSelectedText()
    else:
        pos = schwebend_entfernen(doc, pos)                        # Rahmen und Anker weg; pos ist jetzt der Absatzanfang
    if modus == "zeile":
        k = QTextCursor(doc)
        k.setPosition(pos)
        k.insertImage(f)
        neu = pos
    else:
        neu = schwebend_einfuegen(doc, doc.findBlock(pos).position(), f, modus)
    c.endEditBlock()
    sel = QTextCursor(doc)
    sel.setPosition(neu)
    sel.setPosition(neu + 1, QTextCursor.KeepAnchor)
    ed.setTextCursor(sel)
    doc.setModified(True)
    return True
