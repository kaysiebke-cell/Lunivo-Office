"""Wort-Extras: Absätze aufräumen — über die Markierung, ohne Markierung über das ganze Dokument. Jede Handlung ist ein Schritt für Rückgängig.

Texte in Tabellen bleiben unberührt; leere Absätze, Bilder und Zeilenumbrüche werden dort gesucht, wo sie im Fließtext stehen."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor

ZEILENUMBRUCH = " "
SATZENDE = tuple(".!?:;…\"“”»«)")


def _bloecke(ed) -> list:
    """Die Absätze der Markierung (ohne Markierung: alle) außerhalb von Tabellen, in Dokumentreihenfolge."""
    doc = ed.document()
    c = ed.textCursor()
    if c.hasSelection():
        b, ende = doc.findBlock(c.selectionStart()), doc.findBlock(c.selectionEnd()).blockNumber()
    else:
        b, ende = doc.firstBlock(), doc.blockCount()
    out = []
    while b.isValid() and b.blockNumber() <= ende:
        if QTextCursor(b).currentTable() is None:
            out.append(b)
        b = b.next()
    return out


def _leer(b) -> bool:
    """Ein Absatz ohne Zeichen und ohne Bild."""
    return b.length() <= 1


def _schritt(ed, arbeit) -> int:
    """Führt ``arbeit(doc, bloecke)`` als einen Rückgängig-Schritt aus. → Zahl der Änderungen."""
    c = QTextCursor(ed.document())
    c.beginEditBlock()
    try:
        return arbeit(ed.document(), _bloecke(ed)) or 0
    finally:
        c.endEditBlock()


def leere_loeschen(ed) -> int:
    def arbeit(doc, bloecke):
        n = 0
        for b in reversed(bloecke):
            if _leer(b) and b.next().isValid():
                c = QTextCursor(b); c.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor); c.removeSelectedText(); n += 1
        return n
    return _schritt(ed, arbeit)


def leere_einfuegen(ed) -> int:
    def arbeit(doc, bloecke):
        n = 0
        for b in reversed(bloecke):
            nxt = b.next()
            if not _leer(b) and nxt.isValid() and not _leer(nxt) and QTextCursor(nxt).currentTable() is None:
                c = QTextCursor(b); c.movePosition(QTextCursor.EndOfBlock); c.insertBlock(); n += 1
        return n
    return _schritt(ed, arbeit)


def zeilenumbruch_in_return(ed) -> int:
    def arbeit(doc, bloecke):
        n = 0
        for b in reversed(bloecke):
            while (i := b.text().rfind(ZEILENUMBRUCH)) >= 0:
                c = QTextCursor(doc); c.setPosition(b.position() + i); c.setPosition(b.position() + i + 1, QTextCursor.KeepAnchor)
                c.removeSelectedText(); c.insertBlock(); n += 1
                b = doc.findBlock(b.position())
        return n
    return _schritt(ed, arbeit)


def absaetze_neu_anordnen(ed) -> int:
    """Absätze, die mitten im Satz enden (hartes Return in einem Satz, etwa aus PDF-Text), werden zu einem Absatz."""
    def arbeit(doc, bloecke):
        n = 0
        for b in reversed(bloecke):
            nxt = b.next()
            t = b.text().rstrip()
            if t and not t.endswith(SATZENDE) and nxt.isValid() and nxt.text().strip() and QTextCursor(nxt).currentTable() is None \
                    and not b.textList() and not nxt.textList() and b.blockFormat().headingLevel() == 0:
                c = QTextCursor(b); c.movePosition(QTextCursor.EndOfBlock); c.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                c.insertText(" "); n += 1
        return n
    return _schritt(ed, arbeit)


def leerzeichen_bereinigen(ed) -> int:
    """Doppelte Leerzeichen und Leerzeichen am Anfang und Ende der Absätze entfernen."""
    import re

    def arbeit(doc, bloecke):
        n = 0
        for b in reversed(bloecke):
            t = b.text()
            for m in reversed(list(re.finditer(r"^[ \t]+|[ \t]+$|(?<=\S)[ ]{2,}", t))):
                a, e = m.start(), m.end()
                c = QTextCursor(doc); c.setPosition(b.position() + a); c.setPosition(b.position() + e, QTextCursor.KeepAnchor)
                if m.group().strip() == "" and a > 0 and e < len(t):          # mitten im Satz bleibt ein Leerzeichen
                    c.setPosition(b.position() + a + 1)
                    c.setPosition(b.position() + e, QTextCursor.KeepAnchor)
                c.removeSelectedText(); n += 1
        return n
    return _schritt(ed, arbeit)


def einzug_zwei_zeichen(ed) -> int:
    """Erstzeileneinzug um zwei Zeichen der Schriftgröße des Absatzes."""
    def arbeit(doc, bloecke):
        n = 0
        for b in bloecke:
            if _leer(b) or b.textList():
                continue
            pt = b.charFormat().fontPointSize() or doc.defaultFont().pointSizeF() or 11.0
            bf = b.blockFormat(); bf.setTextIndent(2 * pt * 96 / 72)
            QTextCursor(b).setBlockFormat(bf); n += 1
        return n
    return _schritt(ed, arbeit)


def smart_anordnen(ed) -> int:
    """Leerzeichen bereinigen, leere Absätze löschen, Erstzeileneinzug um zwei Zeichen."""
    return leerzeichen_bereinigen(ed) + leere_loeschen(ed) + einzug_zwei_zeichen(ed)


AKTIONEN = [("Absätze neu anordnen", absaetze_neu_anordnen), ("Smart-Anordnen", smart_anordnen),
            ("Zeilenumbruch in Absatz (Return) umwandeln", zeilenumbruch_in_return),
            ("Absatzeinzug um 2 Zeichen", einzug_zwei_zeichen), ("Leerzeichen bereinigen", leerzeichen_bereinigen),
            ("Leere Absätze einfügen", leere_einfuegen), ("Leere Absätze löschen", leere_loeschen)]
