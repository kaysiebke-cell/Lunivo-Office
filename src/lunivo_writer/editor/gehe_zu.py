"""„Gehe zu“: Sprungziele im Dokument — Seite, Zeile (Absatz), Überschrift, Textmarke, Kommentar, Fußnote, Endnote, Tabelle, Bild,
Beschriftung, Abschnitt. Die Dialogoberfläche steht in ui/dialogs/gehe_zu_dialog.py."""
from __future__ import annotations

from PySide6.QtGui import QTextTable

from lunivo_writer.editor import verweise
from lunivo_writer.editor.zusatz import P_KOMMENTAR, P_NOTE

NUMMERN = ("Seite", "Zeile")                                    # man gibt eine Zahl ein
LISTEN = ("Überschrift", "Textmarke", "Beschriftung", "Kommentar", "Fußnote", "Endnote", "Tabelle", "Bild", "Abschnitt")
ARTEN = NUMMERN + LISTEN


def _kurz(t: str, n: int = 60) -> str:
    t = " ".join(t.split())
    return t if len(t) <= n else t[: n - 1] + "…"


def _fragmente(doc):
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid():
                yield f
            it += 1
        b = b.next()


def _tabellen(rahmen):
    for k in rahmen.childFrames():
        if isinstance(k, QTextTable):
            yield k
        yield from _tabellen(k)


def maximum(ed, art: str) -> int:
    """Obergrenze für Seite und Zeile."""
    return max(1, ed.page_count) if art == "Seite" else max(1, ed.document().blockCount())


def seitenstart(ed, n: int) -> int:
    n = max(1, min(n, max(1, ed.page_count)))
    breaks = ed.seitenwechsel
    return 0 if n == 1 or not breaks else breaks[min(n - 2, len(breaks) - 1)]


def zeilenstart(ed, n: int) -> int:
    b = ed.document().findBlockByNumber(max(0, min(n, ed.document().blockCount()) - 1))
    return b.position()


def ziele(ed, art: str) -> list[tuple[str, int]]:
    """[(Beschriftung, Position)] für die Listen-Arten."""
    doc = ed.document()
    if art == "Überschrift":
        return [(z["text"], z["pos"]) for z in verweise.querverweis_ziele(ed) if z["art"] == "Überschrift"]
    if art == "Textmarke":
        return [(d["name"], d["von"]) for d in verweise.lesezeichen_liste(ed)]
    if art == "Beschriftung":
        return [(f"{k['label']}: {_kurz(k['text'])}", k["pos"]) for k in verweise.beschriftungen_liste(ed)]
    if art == "Kommentar":
        gesehen: dict[int, int] = {}
        for f in _fragmente(doc):
            cf = f.charFormat()
            if cf.hasProperty(P_KOMMENTAR):
                gesehen.setdefault(int(cf.property(P_KOMMENTAR)), f.position())
        k = getattr(ed, "kommentare", {}) or {}
        return [(f"Kommentar {i}: {_kurz((k.get(kid) or k.get(str(kid)) or {}).get('text', ''))}".rstrip(": "), pos)
                for i, (kid, pos) in enumerate(sorted(gesehen.items(), key=lambda x: x[1]), start=1)]
    if art in ("Fußnote", "Endnote"):
        kenn = "f:" if art == "Fußnote" else "e:"
        out = []
        for f in _fragmente(doc):
            cf = f.charFormat()
            if cf.hasProperty(P_NOTE) and cf.stringProperty(P_NOTE).startswith(kenn):
                out.append((f"{art} {len(out) + 1}", f.position()))
        return out
    if art == "Tabelle":
        return [(f"Tabelle {i}: {t.rows()} × {t.columns()}", t.firstPosition()) for i, t in enumerate(
            sorted(_tabellen(doc.rootFrame()), key=lambda t: t.firstPosition()), start=1)]
    if art == "Bild":
        return [(f"Bild {i}", f.position()) for i, f in enumerate((f for f in _fragmente(doc) if f.charFormat().isImageFormat()), start=1)]
    if art == "Abschnitt":
        return [("Abschnitt 1 (das ganze Dokument)", 0)]
    return []


def springen(ed, pos: int) -> None:
    from PySide6.QtGui import QTextCursor
    c = QTextCursor(ed.document())
    c.setPosition(max(0, min(pos, ed.document().characterCount() - 1)))
    ed.setTextCursor(c)
    ed.ensureCursorVisible()
    ed.setFocus()
