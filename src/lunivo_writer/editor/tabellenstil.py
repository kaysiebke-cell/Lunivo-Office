"""Tabellenformatvorlagen und Formatoptionen (Kopfzeile, gebänderte Zeilen, erste Spalte).

Die Vorlage wird auf die Zellen angewendet (Füllung, Fettdruck, Rahmen) — nicht als lebende Verknüpfung: spätere Änderungen an
einzelnen Zellen bleiben erhalten, bis die Vorlage erneut angewendet wird. Alles wird als gewöhnliche DOCX-Zellenschattierung und
Fettschrift gespeichert, geht also bei DOCX nicht verloren."""
from __future__ import annotations

from PySide6.QtGui import QBrush, QColor, QTextCharFormat, QTextCursor, QTextTable

# Name: (Kopf-Füllung, Kopf-Schrift, Streifen-Füllung, Rahmen)
VORLAGEN = {
    "Gitternetz": (None, None, None, 0.5),
    "Einfach": (None, None, None, 0),
    "Blau": ("#2f6fb5", "#ffffff", "#e7f0fa", 0.5),
    "Grün": ("#2d8a4e", "#ffffff", "#e6f4ea", 0.5),
    "Orange": ("#e67700", "#ffffff", "#fff0e0", 0.5),
    "Grau": ("#495057", "#ffffff", "#f1f3f5", 0.5),
    "Hell": ("#dee2e6", "#000000", "#f8f9fa", 0),
}


def _zellen(t: QTextTable):
    done = set()
    for r in range(t.rows()):
        for c in range(t.columns()):
            cell = t.cellAt(r, c)
            k = (cell.row(), cell.column())
            if k not in done:
                done.add(k)
                yield r, c, cell


def _fett(cell, an: bool, farbe: str | None = None) -> None:
    c = cell.firstCursorPosition()
    c.setPosition(cell.lastCursorPosition().position(), QTextCursor.KeepAnchor)
    f = QTextCharFormat()
    f.setFontWeight(700 if an else 400)
    if farbe:
        f.setForeground(QColor(farbe))
    c.mergeCharFormat(f)


def anwenden(t: QTextTable, name: str, kopf: bool = True, streifen: bool = True, spalte: bool = False) -> bool:
    if name not in VORLAGEN:
        return False
    kopf_fill, kopf_schrift, streifen_fill, rahmen = VORLAGEN[name]
    fmt = t.format(); fmt.setBorder(rahmen); t.setFormat(fmt)
    for r, c, cell in _zellen(t):
        cf = cell.format().toTableCellFormat()
        ist_kopf = kopf and r == 0
        if ist_kopf and kopf_fill:
            cf.setBackground(QBrush(QColor(kopf_fill)))
        elif streifen and streifen_fill and (r - (1 if kopf else 0)) % 2 == 1:
            cf.setBackground(QBrush(QColor(streifen_fill)))
        else:
            cf.clearBackground()
        cell.setFormat(cf)
        fett = ist_kopf or (spalte and c == 0)
        if fett or c == 0 or r == 0:
            _fett(cell, fett, kopf_schrift if ist_kopf and kopf_fill else None)
    return True
