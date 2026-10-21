"""Mehrstufige Nummerierung („Gliederung nummeriert“: 1. / 1.1. / 1.1.1.), von Lunivo selbst gezeichnet.

Qt kennt nur einfache Listen; die Nummer der übergeordneten Ebene kann es nicht voranstellen. Darum trägt jeder Absatz einer
mehrstufigen Liste die Eigenschaft ``B_MEHRSTUFIG`` (``"ebene|JSON"``) und Lunivo zeichnet die Nummer vor den Text (Editor und PDF
rufen ``nummern_zeichnen``). Der Text steht mit Einzug „Einzug bei“ ab dieser Ebene, die Nummer beginnt bei „Ausrichtung“.

Eine Gliederung ist ``{"ebenen": [9 × {"stil", "format", "start", "ausr", "einzug", "zeichen"?}]}``. ``format`` ist das Zahlenformat mit
den Platzhaltern ①…⑨ für die Nummern der Ebenen 1…9 („①.②.“ = 1.1.). ``ausr`` und ``einzug`` sind Millimeter.
"""
from __future__ import annotations

import json

from lunivo_writer.editor.listen import STILE, ZEICHEN_FELDER

PLATZHALTER = "①②③④⑤⑥⑦⑧⑨"
EBENEN = 9


def nummer_text(stil: str, n: int) -> str:
    """Die Zahl ``n`` in der Zahlenart ``stil`` (dezimal, klein, gross, roem_klein, roem_gross)."""
    if stil == "dezimal" or stil not in STILE:
        return str(n)
    if stil in ("klein", "gross"):
        s = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(97 + r) + s
        return s if stil == "klein" else s.upper()
    zahlen = ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"), (10, "x"),
              (9, "ix"), (5, "v"), (4, "iv"), (1, "i"))
    s = ""
    for w, z in zahlen:
        while n >= w:
            s += z; n -= w
    return s if stil == "roem_klein" else s.upper()


def ebene(stil: str = "dezimal", format: str = "①.", start: int = 1, ausr: float = 0.0, einzug: float = 8.0, zeichen: dict | None = None) -> dict:
    d = {"stil": stil, "format": format, "start": max(1, int(start)), "ausr": float(ausr), "einzug": float(einzug)}
    z = {k: zeichen[k] for k in ZEICHEN_FELDER if zeichen and zeichen.get(k)}
    if z:
        d["zeichen"] = z
    return d


def gliederung(stile: list[str], formate: list[str]) -> dict:
    """9 Ebenen aus je einer Zahlenart und einem Zahlenformat; Ausrichtung und Einzug wachsen mit der Ebene."""
    return {"ebenen": [ebene(stile[min(i, len(stile) - 1)], formate[min(i, len(formate) - 1)], 1, i * 7.0, i * 7.0 + 9.0)
                       for i in range(EBENEN)]}


def _alle(zahlenart: str, suffix: str) -> dict:
    """Ebene n zeigt „1.1.n“ : ``①.②.…``"""
    return gliederung([zahlenart], ["".join(PLATZHALTER[k] + "." for k in range(i + 1)) if suffix == "." else
                                    ".".join(PLATZHALTER[k] for k in range(i + 1)) for i in range(EBENEN)])


# Die Vorlagen des Reiters „Gliederung nummeriert“ (ohne „Kein“); Name für die Kachel
VORLAGEN = (
    ("1. / 1.1. / 1.1.1.", _alle("dezimal", ".")),
    ("1 / 1.1 / 1.1.1", _alle("dezimal", "")),
    ("I. / A. / 1. / a) / i)", gliederung(["roem_gross", "gross", "dezimal", "klein", "roem_klein"],
                                         ["①.", "②.", "③.", "④)", "⑤)", "⑥.", "⑦.", "⑧)", "⑨)"])),
    ("A. / A.A. / A.A.A.", _alle("gross", ".")),
    ("i. / i.i. / i.i.i.", _alle("roem_klein", ".")),
    ("1) / a) / i)", gliederung(["dezimal", "klein", "roem_klein"], ["①)", "②)", "③)", "④)", "⑤)", "⑥)", "⑦)", "⑧)", "⑨)"])),
)


def als_text(defn: dict) -> str:
    return "g:" + json.dumps(defn, ensure_ascii=False, separators=(",", ":"))


def aus_text(text: str | None) -> dict | None:
    if not text or not text.startswith("g:"):
        return None
    try:
        d = json.loads(text[2:])
        e = d["ebenen"]
        if len(e) != EBENEN:
            return None
        return {"ebenen": [ebene(x["stil"], x["format"], x["start"], x["ausr"], x["einzug"], x.get("zeichen")) for x in e]}
    except (ValueError, KeyError, TypeError):
        return None


def block_wert(ebene_nr: int, defn: dict) -> str:
    return f"{ebene_nr}|{json.dumps(defn, ensure_ascii=False, separators=(',', ':'))}"


def aus_block(text: str) -> tuple[int, dict] | None:
    try:
        n, rest = text.split("|", 1)
        d = aus_text("g:" + rest)
        return (max(1, min(EBENEN, int(n))), d) if d else None
    except ValueError:
        return None


def nummer_der_ebene(defn: dict, zaehler: list[int], ebene_nr: int) -> str:
    """Die Nummer als Text für einen Absatz der Ebene ``ebene_nr`` (1…9) bei diesen Zählerständen."""
    f = defn["ebenen"][ebene_nr - 1]["format"]
    for i, ch in enumerate(PLATZHALTER):
        if ch in f:
            f = f.replace(ch, nummer_text(defn["ebenen"][i]["stil"], zaehler[i]) if i < ebene_nr else "")
    return f


def zaehlen(zaehler: list[int], defn: dict, ebene_nr: int) -> None:
    """Zählerstand nach einem Absatz der Ebene ``ebene_nr``: diese Ebene weiter, tiefere neu."""
    i = ebene_nr - 1
    zaehler[i] = defn["ebenen"][i]["start"] if zaehler[i] == 0 else zaehler[i] + 1
    for k in range(i + 1, EBENEN):
        zaehler[k] = 0


def nummern(d) -> list[tuple]:
    """[(Block, Nummerntext, Ebene, Beschreibung der Ebene)] aller Absätze mit ``B_MEHRSTUFIG`` in Dokumentreihenfolge."""
    from lunivo_writer.editor.zusatz import B_MEHRSTUFIG
    aus, zaehler = [], [0] * EBENEN
    b = d.firstBlock()
    while b.isValid():
        bf = b.blockFormat()
        if bf.hasProperty(B_MEHRSTUFIG) and b.isVisible():
            w = aus_block(bf.stringProperty(B_MEHRSTUFIG))
            if w:
                n, defn = w
                zaehlen(zaehler, defn, n)
                aus.append((b, nummer_der_ebene(defn, zaehler, n), n, defn["ebenen"][n - 1]))
        b = b.next()
    return aus


def nummern_zeichnen(p, d, faktor: float = 1.0) -> None:
    """Die Nummern der mehrstufigen Listen vor die Absätze zeichnen. Koordinaten: Dokument (wie ``absatzrahmen_zeichnen``)."""
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QFont, QTextLayout
    from lunivo_writer.models.page import mm_to_px
    lay = d.documentLayout()
    for b, text, n, e in nummern(d):
        tl = b.layout()
        if tl is None or tl.lineCount() == 0:
            continue
        z = tl.lineAt(0)
        frag = b.begin()
        cf = (frag.fragment().charFormat() if not frag.atEnd() else b.charFormat())
        f = QFont(cf.font())
        zc = e.get("zeichen") or {}
        if zc.get("schrift"):
            f.setFamily(zc["schrift"])
        if zc.get("groesse"):
            f.setPointSizeF(float(zc["groesse"]))
        if "fett" in zc:
            f.setBold(bool(zc["fett"]))
        if "kursiv" in zc:
            f.setItalic(bool(zc["kursiv"]))
        farbe = QColor(zc["farbe"]) if zc.get("farbe") else (cf.foreground().color() if cf.foreground().style() else QColor("black"))
        x = tl.position().x() + z.x() - mm_to_px(e["einzug"] - e["ausr"])
        ml = QTextLayout(text, f, lay.paintDevice())
        ml.beginLayout(); zeile = ml.createLine(); ml.endLayout()
        y = tl.position().y() + z.y() + z.ascent() - zeile.ascent()
        p.save(); p.setPen(farbe)
        ml.draw(p, QPointF(x, y))
        p.restore()
