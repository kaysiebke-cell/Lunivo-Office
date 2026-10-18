"""Verzeichnisse: Inhalt, Abbildungen, Tabellen, Stichwörter, Literatur.

Die Zeilen sind gewöhnliche Absätze mit rechtem Tabstopp und einer Markierung (B_TOC/B_ART), an der „Verzeichnisse
aktualisieren“ sie wiederfindet. In DOCX tragen sie die Word-Formatvorlagen „TOC Heading“, „TOC 1–3“, „Table of Figures“,
„Index 1“ und „Bibliography“ — beim Öffnen werden sie daran wiedererkannt (kein Word-Feld, aber aktualisierbar).
"""
from __future__ import annotations

from PySide6.QtGui import QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextOption

from .page import mm_to_px
from .pagination import paginated_copy
from .zusatz import B_ART, B_CAP, B_TOC, P_INDEX

ARTEN = {
    "toc": "Inhaltsverzeichnis",
    "abb": "Abbildungsverzeichnis",
    "tab": "Tabellenverzeichnis",
    "index": "Stichwortverzeichnis",
    "lit": "Literaturverzeichnis",
}


def _ueberschriften(doc):
    b = doc.firstBlock()
    while b.isValid():
        lvl = b.blockFormat().headingLevel()
        if 1 <= lvl <= 3 and b.text().strip() and b.blockFormat().property(B_TOC) is None:
            yield lvl, b.text().strip(), b.position()
        b = b.next()


def _beschriftungen(doc, label: str):
    b = doc.firstBlock()
    while b.isValid():
        if b.blockFormat().hasProperty(B_CAP) and b.blockFormat().property(B_CAP) == label and b.text().strip():
            yield 1, b.text().strip(), b.position()
        b = b.next()


def _stichwoerter(doc):
    """{Stichwort: [Positionen]} aus den markierten Textstellen."""
    out: dict[str, list[int]] = {}
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_INDEX):
                out.setdefault(f.charFormat().stringProperty(P_INDEX), []).append(f.position())
            it += 1
        b = b.next()
    return out


def _seiten(editor, positionen):
    kopie = paginated_copy(editor.document(), editor.page, editor.noten)
    ch = editor.page.content_height_px
    out = []
    for pos in positionen:
        blk = kopie.findBlock(pos)
        r = kopie.documentLayout().blockBoundingRect(blk)
        out.append(int(r.top() // ch) // max(1, int(editor.page.spalten)) + 1)
    return out


def zeilen_fuer(editor, art: str) -> list[tuple[int, str, str]]:
    """→ [(Ebene, Text, Seitenangabe)]"""
    doc = editor.document()
    if art == "toc":
        ue = list(_ueberschriften(doc))
        s = _seiten(editor, [p for _l, _t, p in ue]) if ue else []
        return [(l, t, str(n)) for (l, t, _p), n in zip(ue, s)]
    if art in ("abb", "tab"):
        ue = list(_beschriftungen(doc, "Abbildung" if art == "abb" else "Tabelle"))
        s = _seiten(editor, [p for _l, _t, p in ue]) if ue else []
        return [(l, t, str(n)) for (l, t, _p), n in zip(ue, s)]
    if art == "index":
        sw = _stichwoerter(doc)
        pos = [p for k in sorted(sw, key=str.casefold) for p in sw[k]]
        seiten = iter(_seiten(editor, pos)) if pos else iter(())
        out = []
        for k in sorted(sw, key=str.casefold):
            nr = sorted({next(seiten) for _ in sw[k]})
            out.append((1, k, ", ".join(map(str, nr))))
        return out
    if art == "lit":
        from .literatur import literaturverzeichnis
        return [(1, z, "") for z in literaturverzeichnis(editor.quellen, getattr(editor, "zitierweise", "APA"))]
    return []


def _schreibe(cur: QTextCursor, editor, art: str, zeilen, neuer_block: bool) -> None:
    breite = editor.page.content_width_px
    kopf = QTextBlockFormat()
    kopf.setProperty(B_TOC, "kopf")
    kopf.setProperty(B_ART, art)
    kopf.setBottomMargin(6)
    cf = QTextCharFormat()
    cf.setFontWeight(QFont.Bold)
    cf.setFontPointSize(14)
    if neuer_block:
        cur.insertBlock(kopf, cf)
    else:
        cur.setBlockFormat(kopf)
    cur.insertText(ARTEN[art], cf)
    for lvl, text, seite in zeilen:
        bf = QTextBlockFormat()
        bf.setProperty(B_TOC, f"zeile{lvl}")
        bf.setProperty(B_ART, art)
        if art == "toc":
            bf.setLeftMargin(mm_to_px(6) * (lvl - 1))
        if seite:
            bf.setTabPositions([QTextOption.Tab(breite, QTextOption.RightTab)])
        cur.insertBlock(bf, QTextCharFormat())
        cur.insertText(f"{text}\t{seite}" if seite else text)


def verzeichnis_einfuegen(editor, art: str = "toc") -> int:
    zeilen = zeilen_fuer(editor, art)
    if not zeilen:
        return 0
    cur = editor.textCursor()
    cur.beginEditBlock()
    if cur.block().text():
        cur.movePosition(QTextCursor.EndOfBlock)
    _schreibe(cur, editor, art, zeilen, True)
    cur.endEditBlock()
    verzeichnis_aktualisieren(editor)      # Seitenzahlen nach dem Einfügen (das Verzeichnis schiebt den Text)
    return len(zeilen)


def _bereiche(doc) -> list[tuple[str, int, int]]:
    """[(Art, erste Blockposition, letzte Blockposition)] zusammenhängender Verzeichnisblöcke."""
    out: list[list] = []
    b = doc.firstBlock()
    while b.isValid():
        if b.blockFormat().hasProperty(B_TOC):
            art = b.blockFormat().property(B_ART) or "toc"
            neu = b.blockFormat().property(B_TOC) == "kopf"
            if out and out[-1][0] == art and not neu and out[-1][3] == b.blockNumber() - 1:
                out[-1][2] = b.position(); out[-1][3] = b.blockNumber()
            else:
                out.append([art, b.position(), b.position(), b.blockNumber()])
        b = b.next()
    return [(a, p, q) for a, p, q, _n in out]


def verzeichnis_aktualisieren(editor) -> int:
    doc = editor.document()
    n = 0
    for art, von, bis in reversed(_bereiche(doc)):
        zeilen = zeilen_fuer(editor, art)
        cur = QTextCursor(doc)
        cur.beginEditBlock()
        cur.setPosition(von)
        letzter = doc.findBlock(bis)
        cur.setPosition(letzter.position() + letzter.length() - 1, QTextCursor.KeepAnchor)
        cur.removeSelectedText()
        cur.setBlockFormat(QTextBlockFormat())
        cur.setBlockCharFormat(QTextCharFormat())
        _schreibe(cur, editor, art, zeilen, False)
        cur.endEditBlock()
        n += len(zeilen)
    return n
