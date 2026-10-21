"""Umbruchregeln am Seitenende: „Diesen Absatz zusammenhalten“, „Nicht vom nächsten Absatz trennen“ und die Absatzkontrolle
(keine Schusterjungen und Hurenkinder).

Qt bricht Seiten Zeile für Zeile um und kennt diese Regeln nicht. Darum prüft ``anwenden`` nach dem Setzen des Textes, welche Absätze eine
Regel verletzen, und setzt vor ihnen einen eigenen Seitenumbruch (``PageBreak_AlwaysBefore`` mit der Kennung ``B_AUTOUMBRUCH``). Diese
Umbrüche kommen bei jeder Prüfung neu: erst werden alle alten entfernt, dann die nötigen gesetzt. Sie werden nicht in DOCX geschrieben,
zählen nicht als „Seitenumbruch oberhalb“ des Absatz-Fensters und verändern weder die Änderungsmarke noch den Rückgängig-Verlauf.
"""
from __future__ import annotations

from PySide6.QtGui import QTextBlockFormat, QTextCursor, QTextFormat

MAX_DURCHGAENGE = 4


def ist_manuell(bf) -> bool:
    """Ein Seitenumbruch oberhalb, den der Benutzer gesetzt hat (kein von Lunivo eingefügter)."""
    from lunivo_writer.editor.zusatz import B_AUTOUMBRUCH
    return bool(bf.pageBreakPolicy() & QTextFormat.PageBreak_AlwaysBefore) and not bf.hasProperty(B_AUTOUMBRUCH)


def _zeilen(b, ch: float) -> list[tuple[int, float, float]]:
    """(Seite, oben, unten) jeder Zeile des Absatzes."""
    tl = b.layout()
    aus = []
    if tl is None:
        return aus
    for i in range(tl.lineCount()):
        z = tl.lineAt(i)
        y = tl.position().y() + z.y()
        aus.append((int((y + 0.5) // ch), y, y + z.height()))
    return aus


def _verletzt(b, naechster, ch: float, w: dict) -> bool:
    z = _zeilen(b, ch)
    if not z:
        return False
    erste, letzte = z[0][0], z[-1][0]
    if erste != letzte:
        n_vorn = sum(1 for s, _a, _b in z if s == erste)
        n_hinten = sum(1 for s, _a, _b in z if s == letzte)
        hoehe = z[-1][2] - z[0][1]
        if hoehe > ch:                                   # länger als eine Seite: nicht zu retten
            return False
        if w["zusammen"]:
            return True
        if w["kontrolle"] and len(z) >= 2 and (n_vorn < 2 or n_hinten < 2):
            return True
    if w["nicht_trennen"] and naechster is not None and naechster.isValid():
        zn = _zeilen(naechster, ch)
        if zn and zn[0][0] != letzte and (z[-1][2] - z[0][1]) <= ch:
            return True
    return False


def _seitenanfang(doc, ch: float) -> bool:
    """Am Anfang einer Seite, die durch den Textfluss entsteht, entfällt der Abstand vor dem Absatz (wie in Word und LibreOffice). Nach einem
    Seitenumbruch, den der Benutzer gesetzt hat, und am Dokumentanfang bleibt er. Der eingestellte Wert steht in ``B_VORHER``."""
    from lunivo_writer.editor.zusatz import B_VORHER
    geaendert = False
    for _ in range(MAX_DURCHGAENGE + 2):
        schritt = False
        b = doc.firstBlock()
        while b.isValid():
            if not b.isVisible() or b.layout() is None:
                b = b.next(); continue
            bf = b.blockFormat()
            hat = bf.hasProperty(B_VORHER)
            if hat and bf.topMargin() > 0.01:                       # der Benutzer hat den Abstand inzwischen selbst geändert: vergessen
                bf.clearProperty(B_VORHER); QTextCursor(b).setBlockFormat(bf); hat = False; geaendert = schritt = True
                bf = b.blockFormat()
            soll = hat and bf.doubleProperty(B_VORHER) or bf.topMargin()
            z = _zeilen(b, ch)
            if z and soll > 0.01:
                seite, y = z[0][0], z[0][1]
                am_anfang = seite >= 1 and (y % ch) <= (bf.topMargin() + 1.0) and not ist_manuell(bf)
                if am_anfang and not hat:
                    bf.setProperty(B_VORHER, float(bf.topMargin())); bf.setTopMargin(0.0)
                    QTextCursor(b).setBlockFormat(bf); geaendert = schritt = True
                elif hat and not (seite >= 1 and (y % ch) <= 1.0 and not ist_manuell(bf)):
                    bf.setTopMargin(float(bf.doubleProperty(B_VORHER))); bf.clearProperty(B_VORHER)
                    QTextCursor(b).setBlockFormat(bf); geaendert = schritt = True
            b = b.next()
        if not schritt:
            break
    return geaendert


def anwenden(doc, ch: float) -> bool:
    """Umbruchregeln auf das Dokument anwenden (``ch`` = Höhe der Textfläche einer Seite in Bildpunkten). → True, wenn sich etwas geändert hat."""
    from lunivo_writer.editor import absatzopt
    from lunivo_writer.editor.zusatz import B_ABSATZOPT, B_AUTOUMBRUCH
    if ch <= 0:
        return False
    war_geaendert = doc.isModified()
    aenderung = False
    c = QTextCursor(doc)
    c.joinPreviousEditBlock()
    try:
        b = doc.firstBlock()
        while b.isValid():                                # alte eigene Umbrüche weg
            if b.blockFormat().hasProperty(B_AUTOUMBRUCH):
                bf = b.blockFormat(); bf.clearProperty(B_AUTOUMBRUCH); bf.setPageBreakPolicy(QTextBlockFormat.PageBreak_Auto)
                QTextCursor(b).setBlockFormat(bf); aenderung = True
            b = b.next()
        for _ in range(MAX_DURCHGAENGE):
            neue = []
            b = doc.firstBlock()
            while b.isValid():
                bf = b.blockFormat()
                w = absatzopt.lesen(bf)
                if not b.isVisible() or b.layout() is None:
                    b = b.next(); continue
                if _verletzt(b, b.next(), ch, w) and not (bf.pageBreakPolicy() & QTextFormat.PageBreak_AlwaysBefore):
                    z = _zeilen(b, ch)
                    if z and (z[0][1] % ch) > 1.0:        # steht schon ganz oben auf der Seite: nichts zu gewinnen
                        neue.append(b)
                b = b.next()
            if not neue:
                break
            for b in neue:
                bf = b.blockFormat(); bf.setPageBreakPolicy(QTextBlockFormat.PageBreak_AlwaysBefore); bf.setProperty(B_AUTOUMBRUCH, 1)
                QTextCursor(b).setBlockFormat(bf)
            aenderung = True
        aenderung |= _seitenanfang(doc, ch)
    finally:
        c.endEditBlock()
        doc.setModified(war_geaendert)
    return aenderung
