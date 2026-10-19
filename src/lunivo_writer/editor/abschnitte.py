"""Abschnitte: Seiteneinrichtung, die mitten im Dokument wechseln kann.

Modell wie in DOCX, nur umgekehrt notiert: Ein Absatz mit B_ABSCHNITT ist der LETZTE Absatz eines Abschnitts; sein Wert (JSON) beschreibt
den Abschnitt, der danach beginnt — Beginn („naechste“, „fortlaufend“, „gerade“, „ungerade“) und Seiteneinrichtung. Der erste
Abschnitt hat keinen eigenen Eintrag, seine Einrichtung ist die des Dokuments (`ed.page`).

Grenze: Die Bearbeitungsansicht zeigt alle Abschnitte in der Seitengeometrie des ersten (Qt-Dokumente haben genau eine Seitengröße);
Seitenansicht, Druck, PDF und DOCX kennen die Maße jedes Abschnitts."""
from __future__ import annotations

import dataclasses
import json

from PySide6.QtGui import QTextCursor, QTextFormat

from lunivo_writer.models.page import HeaderFooter, PageSettings

B_ABSCHNITT = QTextFormat.UserProperty + 35

TYPEN = {"naechste": "Nächste Seite", "fortlaufend": "Fortlaufend", "gerade": "Gerade Seite", "ungerade": "Ungerade Seite"}
DOCX_TYP = {"naechste": "nextPage", "fortlaufend": "continuous", "gerade": "evenPage", "ungerade": "oddPage"}
VOM_DOCX = {v: k for k, v in DOCX_TYP.items()}


# ---- Seiteneinrichtung <-> JSON ----------------------------------------------------------------------------------
def seite_zu_dict(ps: PageSettings) -> dict:
    return dataclasses.asdict(ps)


def seite_aus_dict(d: dict) -> PageSettings:
    ps = PageSettings()
    for f in dataclasses.fields(PageSettings):
        if f.name not in d:
            continue
        v = d[f.name]
        if f.name in ("header", "footer", "first_header", "first_footer") and isinstance(v, dict):
            v = HeaderFooter(v.get("text", ""), v.get("align", "center"))
        setattr(ps, f.name, v)
    return ps


def eintrag(typ: str, ps: PageSettings) -> str:
    return json.dumps({"typ": typ, "seite": seite_zu_dict(ps)}, ensure_ascii=False, separators=(",", ":"))


def lesen(blockformat) -> tuple[str, PageSettings] | None:
    if not blockformat.hasProperty(B_ABSCHNITT):
        return None
    try:
        d = json.loads(blockformat.property(B_ABSCHNITT))
        return d.get("typ", "naechste"), seite_aus_dict(d.get("seite", {}))
    except (ValueError, TypeError):
        return None


# ---- Abfragen ----------------------------------------------------------------------------------------------------
def umbrueche(doc) -> list[tuple[int, str, PageSettings]]:
    """[(Blocknummer, Beginn, Einrichtung des folgenden Abschnitts)] in Dokumentreihenfolge."""
    out = []
    b = doc.firstBlock()
    while b.isValid():
        e = lesen(b.blockFormat())
        if e:
            out.append((b.blockNumber(), e[0], e[1]))
        b = b.next()
    return out


def anzahl(doc) -> int:
    return len(umbrueche(doc)) + 1


def index_bei(doc, position: int) -> int:
    """Nummer (0-basiert) des Abschnitts, in dem die Position liegt."""
    nr = doc.findBlock(position).blockNumber()
    return sum(1 for n, _t, _p in umbrueche(doc) if n < nr)


def einrichtung(doc, basis: PageSettings, index: int) -> PageSettings:
    """Einrichtung des Abschnitts `index` (0 = Dokumenteinrichtung); verknüpfte Kopf-/Fußzeilen werden vom Vorgänger übernommen."""
    ab = umbrueche(doc)
    ps = basis.copy()
    for k in range(min(index, len(ab))):
        neu = ab[k][2].copy()
        if neu.kopf_verknuepft:
            neu.header, neu.first_header, neu.diff_first = ps.header.__class__(ps.header.text, ps.header.align), \
                HeaderFooter(ps.first_header.text, ps.first_header.align), ps.diff_first
        if neu.fuss_verknuepft:
            neu.footer, neu.first_footer = HeaderFooter(ps.footer.text, ps.footer.align), HeaderFooter(ps.first_footer.text, ps.first_footer.align)
        ps = neu
    return ps


def alle_einrichtungen(doc, basis: PageSettings) -> list[tuple[str, PageSettings]]:
    """[(Beginn, Einrichtung)] für jeden Abschnitt (der erste mit Beginn „naechste“)."""
    ab = umbrueche(doc)
    out = [("naechste", basis.copy())]
    for k in range(len(ab)):
        out.append((ab[k][1], einrichtung(doc, basis, k + 1)))
    return out


def beginn(doc, index: int) -> int:
    """Zeichenposition, an der Abschnitt `index` beginnt."""
    if index <= 0:
        return 0
    ab = umbrueche(doc)
    b = doc.findBlockByNumber(ab[min(index, len(ab)) - 1][0]).next()
    return b.position() if b.isValid() else doc.characterCount() - 1


def ende(doc, index: int) -> int:
    ab = umbrueche(doc)
    if index >= len(ab):
        return doc.characterCount() - 1
    b = doc.findBlockByNumber(ab[index][0])
    return b.position() + b.length() - 1


# ---- Ändern ------------------------------------------------------------------------------------------------------
def _setze(cursor: QTextCursor, wert: str | None) -> None:
    bf = cursor.blockFormat()
    if wert is None:
        bf.clearProperty(B_ABSCHNITT)
    else:
        bf.setProperty(B_ABSCHNITT, wert)
    cursor.setBlockFormat(bf)


def einfuegen(doc, cursor: QTextCursor, typ: str, basis: PageSettings) -> int:
    """Abschnittsumbruch an der Schreibmarke: der Absatz wird geteilt, der erste Teil beschließt den Abschnitt.
    Der neue Abschnitt übernimmt die Einrichtung des aktuellen. → Nummer des neuen Abschnitts."""
    index = index_bei(doc, cursor.position())
    aktuell = einrichtung(doc, basis, index)
    c = QTextCursor(cursor)
    c.beginEditBlock()
    vorher = c.blockFormat().property(B_ABSCHNITT) if c.blockFormat().hasProperty(B_ABSCHNITT) else None
    c.insertBlock()
    zweiter = QTextCursor(c)
    erster = QTextCursor(c)
    erster.movePosition(QTextCursor.PreviousBlock)
    _setze(erster, eintrag(typ, aktuell))
    _setze(zweiter, vorher)                              # der alte Umbruch beschließt jetzt den (neuen) zweiten Teil
    c.endEditBlock()
    cursor.setPosition(zweiter.position())
    return index + 1


def entfernen(doc, index: int) -> bool:
    """Den Umbruch am Ende von Abschnitt `index` entfernen (ist es der letzte, den davor): die beiden Abschnitte werden einer
    und behalten die Einrichtung des früheren."""
    ab = umbrueche(doc)
    if not ab:
        return False
    k = index if index < len(ab) else len(ab) - 1
    c = QTextCursor(doc.findBlockByNumber(ab[k][0]))
    c.beginEditBlock()
    _setze(c, None)
    c.endEditBlock()
    return True


def setzen(doc, index: int, ps: PageSettings, typ: str | None = None) -> bool:
    """Einrichtung (und Beginn) eines Abschnitts ab dem zweiten ändern; für den ersten gilt `ed.page`."""
    ab = umbrueche(doc)
    if index < 1 or index > len(ab):
        return False
    nr, alt_typ, _alt = ab[index - 1]
    c = QTextCursor(doc.findBlockByNumber(nr))
    _setze(c, eintrag(typ or alt_typ, ps))
    return True


# ---- Ausgabe: das Dokument in Teile mit je eigener Seitengeometrie zerlegen ----------------------------------------------
def _gleiche_geometrie(a: PageSettings, b: PageSettings) -> bool:
    return (abs(a.width_mm - b.width_mm) < .01 and abs(a.height_mm - b.height_mm) < .01 and a.spalten == b.spalten
            and abs(a.margin_left_mm - b.margin_left_mm) < .01 and abs(a.margin_right_mm - b.margin_right_mm) < .01
            and abs(a.margin_top_mm - b.margin_top_mm) < .01 and abs(a.margin_bottom_mm - b.margin_bottom_mm) < .01
            and abs(a.spalten_abstand_mm - b.spalten_abstand_mm) < .01 and a.spalten_linie == b.spalten_linie)


def teile(qdoc, basis: PageSettings) -> tuple[list[tuple[object, PageSettings, str]], list[str]]:
    """Für Seitenansicht, Druck und PDF: [(Dokument, Einrichtung, Beginn)] je Abschnitt und Hinweise.

    Ein „fortlaufender“ Umbruch zu einem Abschnitt mit gleicher Geometrie wird mit dem vorigen zu einem Teil (kein Seitenwechsel).
    Wechselt bei „fortlaufend“ die Geometrie (z. B. die Spaltenzahl), beginnt der Abschnitt in der Ausgabe auf einer neuen Seite —
    ein Seitenteil mit zwei Spaltenzahlen gibt es hier nicht."""
    if not umbrueche(qdoc):
        return [(qdoc, basis, "naechste")], []
    hinweise: list[str] = []
    einr = alle_einrichtungen(qdoc, basis)
    ranges: list[list] = []                              # [Beginn, Einrichtung, von-Abschnitt, bis-Abschnitt]
    for i, (typ, ps) in enumerate(einr):
        ps.color, ps.silbentrennung, ps.watermark = basis.color, basis.silbentrennung, basis.watermark
        if i and typ == "fortlaufend":
            if _gleiche_geometrie(ranges[-1][1], ps):
                ranges[-1][3] = i
                continue
            hinweise.append(f"Abschnitt {i + 1}: Ein fortlaufender Abschnittsumbruch mit anderer Seitengeometrie beginnt in der Ausgabe auf einer neuen Seite.")
        ranges.append([typ, ps, i, i])
    out = []
    for typ, ps, a, b in ranges:
        d = qdoc.clone()
        von, bis = beginn(qdoc, a), ende(qdoc, b)
        c = QTextCursor(d)
        c.setPosition(bis); c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor); c.removeSelectedText()
        if von:
            c.setPosition(0); c.setPosition(von, QTextCursor.KeepAnchor); c.removeSelectedText()
        blk = d.firstBlock()                             # die Umbruchmarken gehören zur Zerlegung, nicht zum Teil
        while blk.isValid():
            if blk.blockFormat().hasProperty(B_ABSCHNITT):
                cc = QTextCursor(blk); _setze(cc, None)
            blk = blk.next()
        out.append((d, ps, typ))
    return out, hinweise
