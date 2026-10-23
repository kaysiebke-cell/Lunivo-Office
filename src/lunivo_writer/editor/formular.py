"""Formularfelder (Inhaltssteuerelemente): Textfeld, Auswahlliste, Datum, Kontrollkästchen, Schaltfläche.

Ein Feld ist ein Textstück mit der Zeicheneigenschaft P_FORM (JSON: Art, Name, Optionen …); sein Text ist der eingegebene Wert. In DOCX werden
Felder als Inhaltssteuerelemente (`w:sdt`) gespeichert und wieder gelesen. „Nur Formulardaten drucken“ druckt nur die Feldinhalte (für
vorgedruckte Formulare); der übrige Text, Bilder und Seitenschmuck fehlen im Ausdruck.
"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat

from lunivo_writer.core.farben import Farbe
P_FORM = QTextFormat.UserProperty + 34
ARTEN = ("text", "auswahl", "datum", "kasten", "knopf")
KASTEN_LEER, KASTEN_VOLL = "☐", "☒"
AKTIONEN = ["Keine", "Drucken", "Als PDF exportieren", "Felder zurücksetzen"]
DATUMSFORMAT = "dd.MM.yyyy"
PLATZHALTER_FARBE = Farbe.GRAU


from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
def meta(art: str, name: str = "", **kw) -> dict:
    m = {"art": art, "name": name}
    m.update({k: v for k, v in kw.items() if v not in (None, "")})
    return m


def meta_text(m: dict) -> str:
    return json.dumps(m, ensure_ascii=False, separators=(",", ":"))


def meta_lesen(s: str) -> dict | None:
    try:
        m = json.loads(s)
        return m if isinstance(m, dict) and m.get("art") in ARTEN else None
    except (TypeError, ValueError):
        return None


def _format(m: dict, leer: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    m = {k: v for k, v in m.items() if k != "leer"}
    f.setProperty(P_FORM, meta_text(dict(m, leer=True) if leer else m))
    if leer:
        f.setForeground(QBrush(QColor(PLATZHALTER_FARBE)))
    if m["art"] == "knopf":
        f.setFontWeight(QFont.Bold)
        f.setBackground(QBrush(QColor("#dee2e6")))
    if m["art"] == "kasten":
        f.setFontPointSize(14)
    return f


def einfuegen(ed, m: dict, wert: str | None = None) -> None:
    """Feld an der Schreibmarke (oder anstelle der Markierung) einfügen."""
    art = m["art"]
    if art == "kasten":
        text, leer = (KASTEN_VOLL if wert == "1" else KASTEN_LEER), False
    elif art == "knopf":
        text, leer = f"  {m.get('aufschrift') or 'Schaltfläche'}  ", False
    elif art == "auswahl":
        opt = m.get("optionen") or []
        text, leer = (wert or m.get("platzhalter") or "Auswahl treffen"), not wert
        if wert is None and opt and not m.get("platzhalter"):
            text, leer = "Auswahl treffen", True
    elif art == "datum":
        text, leer = (wert or m.get("platzhalter") or "Datum wählen"), not wert
    else:
        text, leer = (wert or m.get("platzhalter") or "Text eingeben"), not wert
    c = ed.textCursor()
    c.insertText(text, _format(m, leer))
    c.setCharFormat(QTextCharFormat())                     # was danach getippt wird, gehört nicht mehr zum Feld
    ed.setTextCursor(c)
    ed.document().setModified(True)


def bereiche(doc: QTextDocument) -> list[tuple[int, int, dict]]:
    """[(von, bis, Feld-Daten)] aller Felder; zusammenhängende Stücke mit gleichen Daten sind ein Feld."""
    out: list[tuple[int, int, str]] = []
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_FORM):
                s = f.charFormat().stringProperty(P_FORM)
                v, e = f.position(), f.position() + f.length()
                if out and out[-1][1] == v and out[-1][2] == s:
                    out[-1] = (out[-1][0], e, s)
                else:
                    out.append((v, e, s))
            it += 1
        b = b.next()
    res = []
    for v, e, s in out:
        m = meta_lesen(s)
        if m:
            res.append((v, e, m))
    return res


def feld_an(doc: QTextDocument, pos: int):
    for v, e, m in bereiche(doc):
        if v <= pos <= e:
            return v, e, m
    return None


def _ersetzen(ed, v: int, e: int, m: dict, text: str, leer: bool = False) -> None:
    c = QTextCursor(ed.document())
    c.setPosition(v); c.setPosition(e, QTextCursor.KeepAnchor)
    c.insertText(text, _format(m, leer))
    ed.document().setModified(True)


def wert_von(doc: QTextDocument, v: int, e: int) -> str:
    c = QTextCursor(doc)
    c.setPosition(v); c.setPosition(e, QTextCursor.KeepAnchor)
    return c.selectedText()


def klick(ed, pos: int, fenster=None) -> bool:
    """Klick in ein Feld: Kontrollkästchen wechselt, Auswahl zeigt die Liste, Text und Datum fragen nach dem Wert, die Schaltfläche löst
    ihre Aktion aus. → True, wenn der Klick ein Feld getroffen hat."""
    from PySide6.QtWidgets import QInputDialog, QMenu
    treffer = feld_an(ed.document(), pos)
    if treffer is None:
        return False
    v, e, m = treffer
    art = m["art"]
    if art == "kasten":
        voll = wert_von(ed.document(), v, e) == KASTEN_VOLL
        _ersetzen(ed, v, e, m, KASTEN_LEER if voll else KASTEN_VOLL)
    elif art == "auswahl":
        menu = QMenu(ed)
        for o in m.get("optionen") or []:
            menu.addAction(o, lambda _=False, o=o: _ersetzen(ed, v, e, m, o))
        if not menu.isEmpty():
            menu.exec(ed.viewport().mapToGlobal(ed.cursorRect(_c(ed, v)).bottomLeft()))
    elif art == "datum":
        from PySide6.QtCore import QDate
        from PySide6.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout
        d = QDialog(ed.window())
        d.setWindowTitle(m.get("name") or "Datum")
        kal = QCalendarWidget()
        aktuell = QDate.fromString(wert_von(ed.document(), v, e), DATUMSFORMAT)
        kal.setSelectedDate(aktuell if aktuell.isValid() else QDate.currentDate())
        bb = knopfzeile(d)
        lay = QVBoxLayout(d); lay.addWidget(kal); lay.addWidget(bb)
        if d.exec():
            _ersetzen(ed, v, e, m, kal.selectedDate().toString(DATUMSFORMAT))
    elif art == "text":
        alt = "" if _ist_leer(ed.document(), v) else wert_von(ed.document(), v, e)
        t, ok = QInputDialog.getText(ed.window(), m.get("name") or "Textfeld", m.get("name") or "Wert:", text=alt)
        if ok:
            if t:
                _ersetzen(ed, v, e, m, t)
            else:
                _ersetzen(ed, v, e, m, m.get("platzhalter") or "Text eingeben", leer=True)
    elif art == "knopf":
        _knopf_aktion(ed, m, fenster or ed.window())
    return True


def _c(ed, pos: int) -> QTextCursor:
    c = QTextCursor(ed.document())
    c.setPosition(pos)
    return c


def _ist_leer(doc: QTextDocument, pos: int) -> bool:
    c = QTextCursor(doc)
    c.setPosition(pos + 1)
    m = meta_lesen(c.charFormat().stringProperty(P_FORM))
    return bool(m and m.get("leer"))


def _knopf_aktion(ed, m: dict, fenster) -> None:
    a = m.get("aktion", "Keine")
    if a == "Felder zurücksetzen":
        alle_zuruecksetzen(ed)
    elif a == "Drucken" and hasattr(fenster, "print_dialog"):
        fenster.print_dialog()
    elif a == "Als PDF exportieren" and hasattr(fenster, "export_pdf_dialog"):
        fenster.export_pdf_dialog()


def alle_zuruecksetzen(ed) -> int:
    """Alle Felder auf ihren Anfangswert (Platzhalter, leeres Kästchen) zurücksetzen."""
    n = 0
    c = QTextCursor(ed.document())
    c.beginEditBlock()
    for v, e, m in reversed(bereiche(ed.document())):
        if m["art"] == "kasten":
            _ersetzen(ed, v, e, m, KASTEN_LEER)
        elif m["art"] in ("text", "auswahl", "datum"):
            ph = m.get("platzhalter") or {"text": "Text eingeben", "auswahl": "Auswahl treffen", "datum": "Datum wählen"}[m["art"]]
            _ersetzen(ed, v, e, m, ph, leer=True)
        else:
            continue
        n += 1
    c.endEditBlock()
    return n


def daten(doc: QTextDocument) -> list[tuple[str, str]]:
    """[(Name, Wert)] aller Felder mit Wert (ohne Platzhalter und Schaltflächen)."""
    out = []
    for v, e, m in bereiche(doc):
        if m["art"] == "knopf" or m.get("leer"):
            continue
        w = wert_von(doc, v, e)
        out.append((m.get("name") or m["art"], "ja" if (m["art"] == "kasten" and w == KASTEN_VOLL) else
                    ("" if m["art"] == "kasten" else w)))
    return out


def nur_formulardaten(d: QTextDocument) -> int:
    """„Nur Formulardaten drucken“ in der KOPIE: Text außerhalb der Felder wird unsichtbar, Bilder und Hintergründe entfallen."""
    # Bilder entfernen
    stellen = []
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isImageFormat():
                stellen.append((f.position(), f.length()))
            it += 1
        b = b.next()
    for pos, ln in reversed(stellen):
        c = QTextCursor(d); c.setPosition(pos); c.setPosition(pos + ln, QTextCursor.KeepAnchor); c.removeSelectedText()
    felder = [(v, e) for v, e, _m in bereiche(d)]
    unsichtbar = QTextCharFormat()
    unsichtbar.setForeground(QBrush(QColor(0, 0, 0, 0)))
    unsichtbar.setBackground(QBrush(Qt.NoBrush))
    unsichtbar.setUnderlineStyle(QTextCharFormat.NoUnderline)
    frei, pos = [], 0
    for v, e in sorted(felder):
        if v > pos:
            frei.append((pos, v))
        pos = max(pos, e)
    frei.append((pos, max(pos, d.characterCount() - 1)))
    for v, e in frei:
        if e > v:
            c = QTextCursor(d); c.setPosition(v); c.setPosition(e, QTextCursor.KeepAnchor); c.mergeCharFormat(unsichtbar)
    sichtbar = QTextCharFormat()
    sichtbar.setForeground(QBrush(QColor(Farbe.SCHWARZ)))
    sichtbar.setBackground(QBrush(Qt.NoBrush))
    for v, e in felder:
        c = QTextCursor(d); c.setPosition(v); c.setPosition(e, QTextCursor.KeepAnchor); c.mergeCharFormat(sichtbar)
    return len(felder)
