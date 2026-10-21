"""Füllzeichen vor Tabstopps (Punkte, Striche, Linie): Qt kennt sie nicht, Lunivo zeichnet sie selbst.

Am Absatz steht ``B_TABFUELL`` (``"Position in px:Füllzeichen;…"``); ``zeichnen`` füllt die Strecke jedes Tabzeichens bis zu seinem Tabstopp
(Editor und PDF rufen es zusammen mit den Rahmen und Nummern auf).
"""
from __future__ import annotations

# Schlüssel → (Name im Fenster, Zeichen, DOCX-Wert)
FUELL = {"": ("1 Ohne", "", "none"), "punkt": ("2 .....", ".", "dot"), "strich": ("3 ----", "-", "hyphen"),
         "linie": ("4 ____", "_", "underscore"), "mitte": ("5 ······", "·", "middleDot")}


def lesen(bf) -> dict[float, str]:
    """Position (px) → Füllzeichen-Schlüssel eines Absatzformats."""
    from lunivo_writer.editor.zusatz import B_TABFUELL
    aus = {}
    if bf.hasProperty(B_TABFUELL):
        for teil in bf.stringProperty(B_TABFUELL).split(";"):
            try:
                p, f = teil.split(":")
                if f in FUELL and f:
                    aus[float(p)] = f
            except ValueError:
                continue
    return aus


def setzen(bf, fuell: dict[float, str]) -> None:
    from lunivo_writer.editor.zusatz import B_TABFUELL
    teile = [f"{p:.2f}:{f}" for p, f in sorted(fuell.items()) if f]
    if teile:
        bf.setProperty(B_TABFUELL, ";".join(teile))
    else:
        bf.clearProperty(B_TABFUELL)


def aus_docx(wert: str | None) -> str:
    return next((k for k, v in FUELL.items() if k and v[2] == wert), "")


def zeichnen(p, d) -> None:
    """Füllzeichen in die Tabstrecken der Absätze zeichnen. Koordinaten: Dokument."""
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QFontMetricsF, QPen
    from lunivo_writer.editor.zusatz import B_TABFUELL
    b = d.firstBlock()
    while b.isValid():
        bf = b.blockFormat()
        if bf.hasProperty(B_TABFUELL) and b.isVisible() and b.layout() is not None:
            fuell = lesen(bf)
            text = b.text()
            tl = b.layout()
            frag = b.begin()
            cf = frag.fragment().charFormat() if not frag.atEnd() else b.charFormat()
            fm = QFontMetricsF(cf.font())
            for i, ch in enumerate(text):
                if ch != "\t":
                    continue
                zeile = tl.lineForTextPosition(i)
                if not zeile.isValid():
                    continue
                x0, x1 = zeile.cursorToX(i)[0], zeile.cursorToX(i + 1)[0]
                if x1 - x0 < 4:
                    continue
                # das Tabzeichen springt zum ersten Tabstopp hinter seinem Anfang (bei rechten und zentrierten endet die Strecke davor)
                pos = next((t.position for t in sorted(bf.tabPositions(), key=lambda t: t.position) if t.position > x0 + 1), None)
                stopp = next((f for q, f in fuell.items() if pos is not None and abs(q - pos) < 0.05), None)
                if not stopp:
                    continue
                zeichen = FUELL[stopp][1]
                basis = tl.position().x(); y = tl.position().y() + zeile.y() + zeile.ascent()
                p.save(); p.setFont(cf.font()); p.setPen(QPen(cf.foreground().color() if cf.foreground().style() else p.pen().color()))
                if zeichen == "_":
                    p.drawLine(QPointF(basis + x0 + 1, y + 1), QPointF(basis + x1 - 1, y + 1))
                else:                                       # Zeichen mit festem Abstand, rechtsbündig ans Tabziel
                    w = fm.horizontalAdvance(zeichen) * (1.8 if zeichen in ".·" else 1.0)
                    n = int((x1 - x0 - 4) // max(1.0, w))
                    for k in range(n):
                        p.drawText(QPointF(basis + x1 - 2 - (n - k) * w, y), zeichen)
                p.restore()
        b = b.next()
