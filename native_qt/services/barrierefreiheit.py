"""Barrierefreiheit prüfen — was Menschen mit Sehbehinderung den Text unlesbar macht."""
from __future__ import annotations

import re

from PySide6.QtGui import QColor

from ..document_io.docx_reader import STYLE_PROP


def _hell(c: QColor) -> float:
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c.red()) + 0.7152 * lin(c.green()) + 0.0722 * lin(c.blue())


def kontrast(vorne: QColor, hinten: QColor) -> float:
    a, b = _hell(vorne) + 0.05, _hell(hinten) + 0.05
    return max(a, b) / min(a, b)


def pruefe(editor) -> list[str]:
    doc = editor.document()
    funde: list[str] = []
    bilder_ohne = 0
    links_schlecht = 0
    farben: dict[str, int] = {}
    seite = QColor(editor.page.color or "#ffffff")
    b = doc.firstBlock()
    ebenen = []
    woerter = 0
    while b.isValid():
        lv = b.blockFormat().headingLevel()
        if lv and b.text().strip():
            ebenen.append(lv)
        woerter += len(b.text().split())
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid():
                cf = f.charFormat()
                if cf.isImageFormat():
                    alt = cf.toImageFormat().property(STYLE_PROP + 1) if cf.toImageFormat().hasProperty(STYLE_PROP + 1) else ""
                    if not (alt or "").strip():
                        bilder_ohne += 1
                elif f.text().strip():
                    fg = cf.foreground().color() if cf.foreground().style() != 0 else QColor("#000000")
                    hg = cf.background().color() if cf.background().style() != 0 else seite
                    if kontrast(fg, hg) < 4.5:
                        farben[fg.name()] = farben.get(fg.name(), 0) + 1
                    if cf.isAnchor() and cf.anchorHref() and re.match(r"^(hier|klick|mehr|link|weiter)", f.text().strip(), re.I):
                        links_schlecht += 1
            it += 1
        b = b.next()
    if bilder_ohne:
        funde.append(f"{bilder_ohne} {'Bild hat' if bilder_ohne == 1 else 'Bilder haben'} keine Beschreibung (Alternativtext). "
                     "Wer nicht sieht, erfährt nicht, was darauf ist.")
    sprung = sum(1 for i in range(1, len(ebenen)) if ebenen[i] - ebenen[i - 1] > 1)
    if sprung:
        funde.append(f"{sprung} {'übersprungene Ebene' if sprung == 1 else 'übersprungene Ebenen'} bei den Überschriften — "
                     "etwa Überschrift 1 direkt gefolgt von Überschrift 3.")
    if not ebenen and woerter > 150:
        funde.append("Der Text hat keine Überschriften. Ab etwa einer Seite fällt das Zurechtfinden schwer.")
    ohne_kopf = 0
    for t in _tabellen(doc):
        if t.format().headerRowCount() < 1:
            ohne_kopf += 1
    if ohne_kopf:
        funde.append(f"{ohne_kopf} {'Tabelle hat' if ohne_kopf == 1 else 'Tabellen haben'} keine Kopfzeile. "
                     "Ohne sie ist unklar, wofür eine Spalte steht.")
    if farben:
        n = sum(farben.values())
        funde.append(f"{n} {'Stelle ist' if n == 1 else 'Stellen sind'} zu blass — unter dem Verhältnis 4,5 zu 1, "
                     "das für Fließtext empfohlen wird.")
    if links_schlecht:
        funde.append("Ein Verweis heißt nur „hier“ oder „mehr“. Wer sich Verweise vorlesen lässt, hört das ohne Zusammenhang."
                     if links_schlecht == 1 else
                     f"{links_schlecht} Verweise heißen nur „hier“ oder „mehr“. Wer sich Verweise vorlesen lässt, hört das ohne Zusammenhang.")
    return funde


def _tabellen(doc):
    from PySide6.QtGui import QTextCursor, QTextTable
    gesehen = set()
    c = QTextCursor(doc)
    b = doc.firstBlock()
    while b.isValid():
        c.setPosition(b.position())
        t = c.currentTable()
        if t is not None and id(t) not in gesehen and t.firstPosition() >= 0:
            key = t.firstPosition()
            if key not in gesehen:
                gesehen.add(key)
                yield t
        b = b.next()
