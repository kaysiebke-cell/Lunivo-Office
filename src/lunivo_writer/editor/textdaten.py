"""Formatierten Text als einfache Daten (Absätze aus Textstücken) ablegen und wieder einfügen — für Textbausteine und Ähnliches.

Ein Absatz ist ``{"runs": [...], "ausr": "mitte"}``; ein Stück ``{"t": "Text", "fett": true, "kursiv": true, "unter": true, "durch": true,
"farbe": "#rrggbb", "marker": "#rrggbb", "pt": 12.0, "schrift": "Name", "hoch": true, "tief": true}`` — nur was gesetzt ist, steht drin.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment

_AUSR = {Qt.AlignHCenter: "mitte", Qt.AlignRight: "rechts", Qt.AlignJustify: "block"}
_AUSR_UMGEKEHRT = {v: k for k, v in _AUSR.items()}


def _stueck(f) -> dict:
    cf: QTextCharFormat = f.charFormat()
    r: dict = {"t": f.text()}
    if cf.fontWeight() >= QFont.Bold:
        r["fett"] = True
    if cf.fontItalic():
        r["kursiv"] = True
    if cf.fontUnderline():
        r["unter"] = True
    if cf.fontStrikeOut():
        r["durch"] = True
    if cf.foreground().style() != Qt.NoBrush:
        r["farbe"] = cf.foreground().color().name()
    if cf.background().style() != Qt.NoBrush:
        r["marker"] = cf.background().color().name()
    if cf.fontPointSize() > 0:
        r["pt"] = round(cf.fontPointSize(), 2)
    fam = cf.fontFamilies()
    if fam:
        r["schrift"] = fam[0] if isinstance(fam, list) else str(fam)
    if cf.verticalAlignment() == QTextCharFormat.AlignSuperScript:
        r["hoch"] = True
    elif cf.verticalAlignment() == QTextCharFormat.AlignSubScript:
        r["tief"] = True
    return r


def fragment_zu_daten(fragment: QTextDocumentFragment) -> list[dict]:
    d = QTextDocument()
    QTextCursor(d).insertFragment(fragment)
    absaetze = []
    blk = d.begin()
    while blk.isValid():
        runs = []
        it = blk.begin()
        while not it.atEnd():
            if it.fragment().isValid():
                runs.append(_stueck(it.fragment()))
            it += 1
        a: dict = {"runs": runs}
        name = _AUSR.get(blk.blockFormat().alignment() & Qt.AlignHorizontal_Mask)
        if name:
            a["ausr"] = name
        absaetze.append(a)
        blk = blk.next()
    return absaetze


def daten_zu_fragment(absaetze: list[dict]) -> QTextDocumentFragment:
    d = QTextDocument()
    c = QTextCursor(d)
    for i, a in enumerate(absaetze):
        if i:
            c.insertBlock()
        bf = QTextBlockFormat()
        bf.setAlignment(_AUSR_UMGEKEHRT.get(a.get("ausr"), Qt.AlignLeft))
        c.setBlockFormat(bf)
        for r in a.get("runs", []):
            cf = QTextCharFormat()
            if r.get("fett"):
                cf.setFontWeight(QFont.Bold)
            cf.setFontItalic(bool(r.get("kursiv"))); cf.setFontUnderline(bool(r.get("unter"))); cf.setFontStrikeOut(bool(r.get("durch")))
            if r.get("farbe"):
                cf.setForeground(QColor(r["farbe"]))
            if r.get("marker"):
                cf.setBackground(QColor(r["marker"]))
            if r.get("pt"):
                cf.setFontPointSize(float(r["pt"]))
            if r.get("schrift"):
                cf.setFontFamilies([r["schrift"]])
            if r.get("hoch"):
                cf.setVerticalAlignment(QTextCharFormat.AlignSuperScript)
            elif r.get("tief"):
                cf.setVerticalAlignment(QTextCharFormat.AlignSubScript)
            c.insertText(r.get("t", ""), cf)
    return QTextDocumentFragment(d)
