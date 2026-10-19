"""Sendungen: Umschlag, Etiketten, Seriendruck (mit Feldern, Adressblock, Regeln), Formularfelder."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QBrush, QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment, QTextFormat,
    QTextLength, QTextTableFormat,
)

from lunivo_writer.models.page import PageSettings, mm_to_px

P_REGEL = QTextFormat.UserProperty + 30          # "Feld|Wert|dann|sonst" — Regel im Serienbrief
FELD_FARBE = "#d0ebff"
REGEL_FARBE = "#ffe8cc"

UMSCHLAEGE = {"DIN lang (220 × 110 mm)": (220, 110), "C6 (162 × 114 mm)": (162, 114), "C5 (229 × 162 mm)": (229, 162),
              "C4 (324 × 229 mm)": (324, 229)}
ETIKETTEN = {"70 × 37 mm — 24 Stück (3 × 8)": (3, 8, 70, 37), "70 × 42,3 mm — 21 Stück (3 × 7)": (3, 7, 70, 42.3),
             "70 × 50,8 mm — 15 Stück (3 × 5)": (3, 5, 70, 50.8), "105 × 42,3 mm — 14 Stück (2 × 7)": (2, 7, 105, 42.3),
             "105 × 148 mm — 4 Stück (2 × 2)": (2, 2, 105, 148)}


# ---- Umschlag und Etiketten -----------------------------------------------------------------------------------
def umschlag_aufbauen(ed, format_name: str, absender: str, empfaenger: str) -> PageSettings:
    b, h = UMSCHLAEGE[format_name]
    pg = PageSettings(width_mm=b, height_mm=h, margin_top_mm=12, margin_bottom_mm=10, margin_left_mm=15, margin_right_mm=12)
    doc = ed.document()
    doc.clear()
    c = QTextCursor(doc)
    f = QTextCharFormat(); f.setFontPointSize(8)
    bf = QTextBlockFormat()
    c.setBlockFormat(bf); c.setBlockCharFormat(f)
    c.insertText(" ".join(z.strip() for z in absender.splitlines() if z.strip()), f)
    bf2 = QTextBlockFormat()
    bf2.setTopMargin(mm_to_px(max(10, h * 0.2))); bf2.setLeftMargin(mm_to_px(b * 0.42))
    f2 = QTextCharFormat(); f2.setFontPointSize(12)
    c.insertBlock(bf2, f2)
    c.insertText(" ".join(z.strip() for z in empfaenger.splitlines() if z.strip()), f2)
    return pg


def etiketten_aufbauen(ed, bogen: str, text: str, gleich: bool) -> PageSettings:
    sp, ze, b, h = ETIKETTEN[bogen]
    pg = PageSettings(margin_top_mm=8, margin_bottom_mm=8, margin_left_mm=5, margin_right_mm=5)
    doc = ed.document()
    doc.clear()
    zeilen = [z.strip() for z in text.splitlines() if z.strip()]
    tf = QTextTableFormat()
    tf.setCellPadding(mm_to_px(2)); tf.setCellSpacing(0); tf.setBorder(0)
    tf.setColumnWidthConstraints([QTextLength(QTextLength.FixedLength, mm_to_px(b))] * sp)
    c = QTextCursor(doc)
    t = c.insertTable(ze, sp, tf)
    n = 0
    for r in range(ze):
        for k in range(sp):
            cell = t.cellAt(r, k)
            cc = cell.firstCursorPosition()
            inhalt = " ".join(zeilen) if gleich else (zeilen[n] if n < len(zeilen) else "")
            f = QTextCharFormat(); f.setFontPointSize(10)
            cc.insertText(inhalt, f)
            n += 1
    # feste Zeilenhöhe: je Zelle ein Absatz mit Mindesthöhe wird mit Qt nicht garantiert — Abstand setzt die Höhe
    for r in range(ze):
        for k in range(sp):
            cc = t.cellAt(r, k).firstCursorPosition()
            bf = cc.blockFormat()
            bf.setBottomMargin(max(0.0, mm_to_px(h) - mm_to_px(2) * 2 - 14 * (len(zeilen) if gleich else 1)))
            cc.setBlockFormat(bf)
    return pg


# ---- Serienbrief -------------------------------------------------------------------------------------------------------------
def tabelle_lesen(roh: str):
    zeilen = [z for z in re.split(r"\r?\n", roh) if z.strip()]
    if len(zeilen) < 2:
        return None
    tr = "\t" if "\t" in zeilen[0] else (";" if ";" in zeilen[0] else ",")
    spalten = [s.strip() for s in zeilen[0].split(tr)]
    saetze = []
    for z in zeilen[1:]:
        w = [x.strip() for x in z.split(tr)]
        saetze.append({n: (w[i] if i < len(w) else "") for i, n in enumerate(spalten)})
    return spalten, saetze


FELD = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def felder_im_text(doc: QTextDocument) -> list[str]:
    return sorted(set(m.group(1) for m in FELD.finditer(doc.toPlainText())))


def feld_einfuegen(ed, name: str) -> None:
    f = QTextCharFormat(); f.setBackground(QBrush(QColor(FELD_FARBE)))
    ed.textCursor().insertText("{{" + name + "}}", f)
    ed.document().setModified(True)


def adressblock_einfuegen(ed, was: str) -> None:
    c = ed.textCursor()
    c.beginEditBlock()

    def feld(n):
        f = QTextCharFormat(); f.setBackground(QBrush(QColor(FELD_FARBE))); c.insertText("{{" + n + "}}", f)

    def text(t):
        c.insertText(t, QTextCharFormat())
    if was in ("adresse", "beides"):
        feld("Name"); c.insertText(" ", QTextCharFormat()); feld("Straße"); c.insertText(" ", QTextCharFormat())
        feld("PLZ"); text(" "); feld("Ort")
    if was == "beides":
        c.insertBlock(); c.insertBlock()
    if was in ("gruss", "beides"):
        text("Sehr geehrte"); feld("Anrede"); text(" "); feld("Name"); text(",")
    c.endEditBlock()
    ed.setTextCursor(c)
    ed.document().setModified(True)


def regel_einfuegen(ed, feld: str, wert: str, dann: str, sonst: str) -> None:
    f = QTextCharFormat(); f.setBackground(QBrush(QColor(REGEL_FARBE)))
    f.setProperty(P_REGEL, "|".join(x.replace("|", "/") for x in (feld, wert, dann, sonst)))
    ed.textCursor().insertText(dann, f)
    ed.document().setModified(True)


def _satz_einsetzen(doc: QTextDocument, satz: dict) -> None:
    # Regeln zuerst: sie entscheiden anhand eines Feldes, welcher Text stehen bleibt
    stuecke = []
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_REGEL):
                stuecke.append((f.position(), f.position() + f.length(), f.charFormat().stringProperty(P_REGEL), f.charFormat()))
            it += 1
        b = b.next()
    for von, bis, regel, cf in reversed(stuecke):
        feld, wert, dann, sonst = (regel.split("|") + ["", "", "", ""])[:4]
        text = dann if (satz.get(feld, "").strip() == wert.strip()) else sonst
        c = QTextCursor(doc)
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        nf = QTextCharFormat(cf)
        nf.setBackground(QBrush(Qt.NoBrush)); nf.clearProperty(P_REGEL)
        c.insertText(text, nf)
    for name, wert in satz.items():
        c = QTextCursor(doc)
        muster = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*\}\}")
        text = doc.toPlainText()
        for m in reversed(list(muster.finditer(text))):
            c.setPosition(m.start()); c.setPosition(m.end(), QTextCursor.KeepAnchor)
            nf = c.charFormat(); nf.setBackground(QBrush(Qt.NoBrush))
            c.insertText(str(wert), nf)


def brief_fuer(vorlage: QTextDocument, satz: dict) -> QTextDocument:
    d = vorlage.clone()
    _satz_einsetzen(d, satz)
    return d


def serienbrief_erzeugen(quelle: QTextDocument, saetze: list[dict], ziel: QTextDocument) -> int:
    """Alle Briefe in EIN Dokument, durch Seitenumbrüche getrennt."""
    ziel.clear()
    c = QTextCursor(ziel)
    for i, satz in enumerate(saetze):
        d = brief_fuer(quelle, satz)
        _ressourcen(d, ziel)
        if i:
            bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
            c.insertBlock(bf, QTextCharFormat())
        c.insertFragment(QTextDocumentFragment(d))
    return len(saetze)


def _ressourcen(quelle: QTextDocument, ziel: QTextDocument) -> None:
    b = quelle.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isImageFormat():
                n = f.charFormat().toImageFormat().name()
                r = quelle.resource(QTextDocument.ImageResource, QUrl(n))
                if r is not None:
                    ziel.addResource(QTextDocument.ImageResource, QUrl(n), r)
            it += 1
        b = b.next()


# ---- Formular ------------------------------------------------------------------------------------------------------------------
KASTEN_LEER, KASTEN_VOLL = "☐", "☒"


def form_textfeld(ed, text: str = "Text eingeben") -> None:
    f = QTextCharFormat()
    f.setBackground(QBrush(QColor("#f1f3f5"))); f.setUnderlineStyle(QTextCharFormat.DotLine)
    ed.textCursor().insertText(f"[ {text} ]", f)
    ed.document().setModified(True)


def form_kasten(ed, beschriftung: str = "Auswahl") -> None:
    c = ed.textCursor()
    f = QTextCharFormat(); f.setFontPointSize((ed.document().defaultFont().pointSizeF() or 11) * 1.3)
    c.insertText(KASTEN_LEER, f)
    c.insertText(" " + beschriftung, QTextCharFormat())
    ed.document().setModified(True)


def form_knopf(ed, aufschrift: str) -> None:
    f = QTextCharFormat()
    f.setBackground(QBrush(QColor("#dee2e6"))); f.setFontWeight(QFont.Bold)
    ed.textCursor().insertText(f"  {aufschrift or 'Schaltfläche'}  ", f)
    ed.document().setModified(True)


def kasten_umschalten(ed, pos: int) -> bool:
    """Klick auf ein Kontrollkästchen ☐/☒ wechselt den Zustand."""
    for p in (pos, pos - 1):
        if p < 0:
            continue
        c = QTextCursor(ed.document())
        c.setPosition(p); c.setPosition(p + 1, QTextCursor.KeepAnchor)
        t = c.selectedText()
        if t in (KASTEN_LEER, KASTEN_VOLL):
            c.insertText(KASTEN_VOLL if t == KASTEN_LEER else KASTEN_LEER, c.charFormat())
            return True
    return False
