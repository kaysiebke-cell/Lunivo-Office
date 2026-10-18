"""Beschriftungen, Textmarken, Querverweise, Stichwörter und Zitate — Funktionen am Editor."""
from __future__ import annotations

import re

from PySide6.QtGui import QBrush, QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor

from .literatur import zitat
from .zusatz import B_CAP, P_FELD, P_INDEX, P_ZITAT


# ---- Beschriftungen ---------------------------------------------------------------------------------------
def beschriftung_einfuegen(ed, label: str, text: str, oben: bool = False) -> None:
    doc = ed.document()
    c = ed.textCursor()
    c.beginEditBlock()
    tab = c.currentTable()
    if tab is not None:
        if oben and tab.firstPosition() > 0:
            c.setPosition(tab.firstPosition() - 1)
            c.movePosition(QTextCursor.EndOfBlock)
        else:
            c.setPosition(tab.lastPosition() + 1)
            c.movePosition(QTextCursor.EndOfBlock)
            if c.block().text():
                c.insertBlock()
            else:
                pass
    else:
        c.movePosition(QTextCursor.EndOfBlock)
    bf = QTextBlockFormat()
    bf.setProperty(B_CAP, label)
    bf.setTopMargin(4); bf.setBottomMargin(8)
    cf = QTextCharFormat()
    cf.setFontItalic(True); cf.setFontPointSize(9); cf.setForeground(QBrush(QColor("#44546a")))
    if c.block().text() or tab is None:
        c.insertBlock(bf, cf)
    else:
        c.setBlockFormat(bf); c.setBlockCharFormat(cf)
    c.insertText(label + " ", cf)
    nf = QTextCharFormat(cf)
    nf.setProperty(P_FELD, f"SEQ {label} \\* ARABIC")
    c.insertText("0", nf)
    if text:
        c.insertText(": " + text, cf)
    c.endEditBlock()
    ed.setTextCursor(c)
    beschriftungen_nummerieren(ed)
    ed.document().setModified(True)


def beschriftungen_nummerieren(ed) -> None:
    zaehler: dict[str, int] = {}
    doc = ed.document()
    arbeit = []
    b = doc.firstBlock()
    while b.isValid():
        if b.blockFormat().hasProperty(B_CAP):
            label = b.blockFormat().property(B_CAP)
            zaehler[label] = zaehler.get(label, 0) + 1
            it = b.begin()
            while not it.atEnd():
                f = it.fragment()
                if f.isValid() and f.charFormat().hasProperty(P_FELD) and f.charFormat().stringProperty(P_FELD).upper().startswith("SEQ"):
                    if f.text() != str(zaehler[label]):
                        arbeit.append((f.position(), f.position() + f.length(), str(zaehler[label]), f.charFormat()))
                    break
                it += 1
        b = b.next()
    if arbeit:
        c = QTextCursor(doc)
        c.beginEditBlock()
        for von, bis, neu, fmt in reversed(arbeit):
            c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
            c.insertText(neu, fmt)
        c.endEditBlock()


def beschriftungen_liste(ed) -> list[dict]:
    out = []
    b = ed.document().firstBlock()
    while b.isValid():
        if b.blockFormat().hasProperty(B_CAP) and b.text().strip():
            out.append({"label": b.blockFormat().property(B_CAP), "text": b.text().strip(), "pos": b.position(), "block": b})
        b = b.next()
    return out


# ---- Textmarken ------------------------------------------------------------------------------------------------
def lesezeichen_liste(ed) -> list[dict]:
    """[{name, von, bis}] — zusammenhängende Textstücke mit demselben Namen."""
    out: dict[str, dict] = {}
    b = ed.document().firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isAnchor() and not f.charFormat().anchorHref():
                for n in f.charFormat().anchorNames():
                    d = out.setdefault(n, {"name": n, "von": f.position(), "bis": f.position() + f.length()})
                    d["bis"] = max(d["bis"], f.position() + f.length())
                    d["von"] = min(d["von"], f.position())
            it += 1
        b = b.next()
    return sorted(out.values(), key=lambda d: d["von"])


_NAME = re.compile(r"^[A-Za-zÄÖÜäöüß][A-Za-z0-9ÄÖÜäöüß_]{0,39}$")


def lesezeichen_name_gueltig(name: str) -> bool:
    return bool(_NAME.match(name))


def lesezeichen_setzen(ed, name: str) -> bool:
    c = ed.textCursor()
    if not c.hasSelection():
        c.select(QTextCursor.WordUnderCursor)
        if not c.hasSelection():
            return False
    if any(d["name"] == name for d in lesezeichen_liste(ed)):
        lesezeichen_loeschen(ed, name)
    von, bis = c.selectionStart(), c.selectionEnd()
    c.beginEditBlock()
    stuecke = []
    b = ed.document().findBlock(von)
    while b.isValid() and b.position() < bis:
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.position() < bis and f.position() + f.length() > von:
                stuecke.append((max(f.position(), von), min(f.position() + f.length(), bis), f.charFormat()))
            it += 1
        b = b.next()
    for a, z, cf in stuecke:
        neu = QTextCharFormat(cf)
        neu.setAnchor(True)
        neu.setAnchorNames(list(cf.anchorNames()) + [name] if cf.isAnchor() else [name])
        cc = QTextCursor(ed.document()); cc.setPosition(a); cc.setPosition(z, QTextCursor.KeepAnchor)
        cc.setCharFormat(neu)
    c.endEditBlock()
    ed.document().setModified(True)
    return True


def lesezeichen_loeschen(ed, name: str) -> None:
    doc = ed.document()
    c = QTextCursor(doc)
    c.beginEditBlock()
    stuecke = []
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isAnchor() and name in f.charFormat().anchorNames():
                stuecke.append((f.position(), f.position() + f.length(), f.charFormat()))
            it += 1
        b = b.next()
    for a, z, cf in reversed(stuecke):
        neu = QTextCharFormat(cf)
        rest = [n for n in cf.anchorNames() if n != name]
        if rest:
            neu.setAnchorNames(rest)
        else:
            neu.setAnchor(False); neu.setAnchorNames([])
        cc = QTextCursor(doc); cc.setPosition(a); cc.setPosition(z, QTextCursor.KeepAnchor)
        cc.setCharFormat(neu)
    c.endEditBlock()
    doc.setModified(True)


def lesezeichen_gehe(ed, name: str) -> bool:
    for d in lesezeichen_liste(ed):
        if d["name"] == name:
            ed.select_range(d["von"], d["bis"])
            ed.ensureCursorVisible()
            return True
    return False


def intern_springen(ed, href: str) -> bool:
    return href.startswith("#") and lesezeichen_gehe(ed, href[1:])


# ---- Querverweise -----------------------------------------------------------------------------------------------
def querverweis_ziele(ed) -> list[dict]:
    """Mögliche Ziele: Überschriften, Beschriftungen, Textmarken."""
    z = []
    b = ed.document().firstBlock()
    while b.isValid():
        lv = b.blockFormat().headingLevel()
        if lv and b.text().strip():
            z.append({"art": "Überschrift", "text": b.text().strip(), "pos": b.position(), "block": b.blockNumber()})
        b = b.next()
    for k in beschriftungen_liste(ed):
        z.append({"art": k["label"], "text": k["text"], "pos": k["pos"], "block": k["block"].blockNumber()})
    for d in lesezeichen_liste(ed):
        z.append({"art": "Textmarke", "text": d["name"], "pos": d["von"], "name": d["name"]})
    return z


def _marke_sichern(ed, ziel: dict) -> str:
    if "name" in ziel:
        return ziel["name"]
    blk = ed.document().findBlockByNumber(ziel["block"])
    name = f"Ziel_{ziel['block']}"
    if not any(d["name"] == name for d in lesezeichen_liste(ed)):
        c = QTextCursor(blk)
        c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        keep = ed.textCursor()
        ed.setTextCursor(c)
        lesezeichen_setzen(ed, name)
        ed.setTextCursor(keep)
    return name


def querverweis_einfuegen(ed, ziel: dict, wie: str) -> None:
    """wie: "text" (Überschrift/Beschriftung als Text), "nummer" (Bezeichnung und Nummer) oder "seite" (Seitenzahl)."""
    name = _marke_sichern(ed, ziel)
    if wie == "seite":
        from .verzeichnis import _seiten
        text = "Seite " + str(_seiten(ed, [ziel["pos"]])[0])
    elif wie == "nummer" and ziel["art"] in ("Abbildung", "Tabelle", "Gleichung"):
        m = re.match(r"^(\S+\s+\d+)", ziel["text"])
        text = m.group(1) if m else ziel["text"]
    else:
        text = ziel["text"]
    c = ed.textCursor()
    cf = QTextCharFormat()
    cf.setAnchor(True); cf.setAnchorHref("#" + name)
    cf.setForeground(QBrush(QColor("#0563C1"))); cf.setFontUnderline(True)
    c.insertText(text, cf)
    c.insertText(" ", QTextCharFormat())
    ed.setTextCursor(c)
    ed.document().setModified(True)


# ---- Stichwörter -------------------------------------------------------------------------------------------------------
def index_markieren(ed, term: str) -> bool:
    c = ed.textCursor()
    if not c.hasSelection():
        c.select(QTextCursor.WordUnderCursor)
    if not c.hasSelection():
        return False
    f = QTextCharFormat()
    f.setProperty(P_INDEX, term or c.selectedText())
    c.mergeCharFormat(f)
    ed.document().setModified(True)
    return True


# ---- Zitate ----------------------------------------------------------------------------------------------------------------
def zitat_einfuegen(ed, q: dict) -> None:
    nr = 1 + [x["tag"] for x in ed.quellen].index(q["tag"]) if q in ed.quellen else 1
    f = QTextCharFormat()
    f.setProperty(P_FELD, f"CITATION {q['tag']} \\l 1031")
    f.setProperty(P_ZITAT, q["tag"])
    c = ed.textCursor()
    c.insertText(zitat(q, ed.zitierweise, nr), f)
    c.insertText(" ", QTextCharFormat())
    ed.setTextCursor(c)
    ed.document().setModified(True)


def quelle_tag(quellen: list[dict], q: dict) -> str:
    """Eindeutiger Kurzname wie in Word (Nachname + Jahr)."""
    basis = re.sub(r"\W+", "", (q.get("autor", "").split(",")[0].split(";")[0] or q.get("titel", "Quelle")))[:20] or "Quelle"
    basis += re.sub(r"\D", "", q.get("jahr", ""))[:4]
    tag, i = basis, 2
    vorhanden = {x["tag"] for x in quellen}
    while tag in vorhanden:
        tag = f"{basis}{i}"; i += 1
    return tag
