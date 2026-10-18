"""Inhaltsverzeichnis aus den Überschriften (Stile „Überschrift 1–3“).

Die Zeilen sind gewöhnliche Absätze mit rechtem Tabstopp und einer Markierung, an der
„Verzeichnisse aktualisieren“ sie wiederfindet. In DOCX werden sie als normale Absätze
mit Tabstopp gespeichert (kein Word-Feld).
"""
from __future__ import annotations

from PySide6.QtGui import QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextOption

from ..document_io.docx_reader import STYLE_PROP
from .page import mm_to_px
from .pagination import paginated_copy

TOC_PROP = STYLE_PROP + 2          # "kopf" | "zeile"


def _ueberschriften(doc):
    b = doc.firstBlock()
    while b.isValid():
        lvl = b.blockFormat().headingLevel()
        if 1 <= lvl <= 3 and b.text().strip() and b.blockFormat().property(TOC_PROP) is None:
            yield lvl, b.text().strip(), b.position()
        b = b.next()


def _seiten(editor, positionen):
    kopie = paginated_copy(editor.document(), editor.page, editor.noten)
    ch = editor.page.content_height_px
    out = []
    for pos in positionen:
        blk = kopie.findBlock(pos)
        r = kopie.documentLayout().blockBoundingRect(blk)
        out.append(int(r.top() // ch) + 1)
    return out


def _zeilen(editor):
    ue = list(_ueberschriften(editor.document()))
    seiten = _seiten(editor, [p for _l, _t, p in ue]) if ue else []
    return [(l, t, s) for (l, t, _p), s in zip(ue, seiten)]


def _schreibe(cur: QTextCursor, editor, zeilen) -> None:
    breite = editor.page.content_width_px
    kopf = QTextBlockFormat()
    kopf.setProperty(TOC_PROP, "kopf")
    kopf.setBottomMargin(6)
    cf = QTextCharFormat()
    cf.setFontWeight(QFont.Bold)
    cf.setFontPointSize(14)
    cur.insertBlock(kopf, cf)
    cur.insertText("Inhaltsverzeichnis", cf)
    for lvl, text, seite in zeilen:
        bf = QTextBlockFormat()
        bf.setProperty(TOC_PROP, "zeile")
        bf.setLeftMargin(mm_to_px(6) * (lvl - 1))
        bf.setTabPositions([QTextOption.Tab(breite, QTextOption.RightTab)])
        cur.insertBlock(bf, QTextCharFormat())
        cur.insertText(f"{text}\t{seite}")


def verzeichnis_einfuegen(editor) -> int:
    zeilen = _zeilen(editor)
    if not zeilen:
        return 0
    cur = editor.textCursor()
    cur.beginEditBlock()
    if cur.block().text():
        cur.movePosition(QTextCursor.EndOfBlock)
    _schreibe(cur, editor, zeilen)
    cur.endEditBlock()
    # Seitenzahlen nach dem Einfügen (das Verzeichnis selbst schiebt den Text)
    verzeichnis_aktualisieren(editor)
    return len(zeilen)


def verzeichnis_aktualisieren(editor) -> int:
    doc = editor.document()
    first = last = None
    b = doc.firstBlock()
    while b.isValid():
        if b.blockFormat().property(TOC_PROP) is not None:
            first = first or b
            last = b
        b = b.next()
    if first is None:
        return 0
    cur = QTextCursor(doc)
    cur.setPosition(first.position())
    cur.setPosition(last.position() + last.length() - 1, QTextCursor.KeepAnchor)
    cur.beginEditBlock()
    cur.removeSelectedText()
    zeilen = _zeilen(editor)
    # erste (leere) Zeile als Kopf wiederverwenden
    cur.setBlockFormat(QTextBlockFormat())
    cur.setBlockCharFormat(QTextCharFormat())
    # Kopf in den bestehenden Block schreiben
    kopf = QTextBlockFormat()
    kopf.setProperty(TOC_PROP, "kopf")
    kopf.setBottomMargin(6)
    cf = QTextCharFormat()
    cf.setFontWeight(QFont.Bold)
    cf.setFontPointSize(14)
    cur.setBlockFormat(kopf)
    cur.insertText("Inhaltsverzeichnis", cf)
    breite = editor.page.content_width_px
    for lvl, text, seite in zeilen:
        bf = QTextBlockFormat()
        bf.setProperty(TOC_PROP, "zeile")
        bf.setLeftMargin(mm_to_px(6) * (lvl - 1))
        bf.setTabPositions([QTextOption.Tab(breite, QTextOption.RightTab)])
        cur.insertBlock(bf, QTextCharFormat())
        cur.insertText(f"{text}\t{seite}")
    cur.endEditBlock()
    return len(zeilen)
