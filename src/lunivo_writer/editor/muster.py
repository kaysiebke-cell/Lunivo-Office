"""Schattierungsmuster (Rahmen und Schattierung ▸ Muster): Prozentraster und Linienmuster, wie Word und WPS sie kennen.

Ein Muster ist ein Schlüssel (``pct25``, ``dunkel_h`` …), eine Musterfarbe und eine Füllfarbe darunter. Gespeichert wird es
am Absatz als Text ``schlüssel|musterfarbe|füllfarbe``; gezeichnet als kleine Kachel (``QBrush`` mit Pixmap), in DOCX als
``w:shd`` mit ``w:val`` (``pct25``, ``horzStripe`` …), ``w:color`` und ``w:fill``.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPixmap

_BAYER = ((0, 32, 8, 40, 2, 34, 10, 42), (48, 16, 56, 24, 50, 18, 58, 26), (12, 44, 4, 36, 14, 46, 6, 38), (60, 28, 52, 20, 62, 30, 54, 22),
          (3, 35, 11, 43, 1, 33, 9, 41), (51, 19, 59, 27, 49, 17, 57, 25), (15, 47, 7, 39, 13, 45, 5, 37), (63, 31, 55, 23, 61, 29, 53, 21))

PROZENT = (5, 10, 12.5, 15, 20, 25, 30, 35, 37.5, 40, 45, 50, 55, 60, 62.5, 65, 70, 75, 80, 85, 87.5, 90, 95)
_LINIEN = (("dunkel_h", "Dunkle horizontale Linie", "horzStripe"), ("dunkel_v", "Dunkle vertikale Linie", "vertStripe"),
           ("dunkel_ab", "Dunkel abwärts", "diagStripe"), ("dunkel_auf", "Dunkel aufwärts", "reverseDiagStripe"),
           ("dunkel_raster", "Dunkler Raster", "horzCross"), ("dunkel_karo", "Dunkel Karo", "diagCross"),
           ("hell_h", "Helle horizontale Linie", "thinHorzStripe"), ("hell_v", "Helle vertikale Linie", "thinVertStripe"),
           ("hell_ab", "Hell abwärts", "thinDiagStripe"), ("hell_auf", "Hell aufwärts", "thinReverseDiagStripe"),
           ("hell_raster", "Heller Raster", "thinHorzCross"), ("hell_karo", "Hell Karo", "thinDiagCross"))


def _pct_name(p: float) -> str:
    return f"{p:g}".replace(".", ",") + "%"


# (Schlüssel, Anzeigename, OOXML-Wert) — in der Reihenfolge der Auswahlliste
MUSTER: list[tuple[str, str, str]] = (
    [("loeschen", "Löschen", "clear"), ("rein", "Rein(100%)", "solid")]
    + [(f"pct{p:g}".replace(".", "_"), _pct_name(p), f"pct{int(p)}") for p in PROZENT]
    + list(_LINIEN)
)
_NAME = {k: n for k, n, _o in MUSTER}
_OOXML = {k: o for k, _n, o in MUSTER}
_VON_OOXML = {o: k for k, _n, o in MUSTER}


def name_von(schluessel: str) -> str:
    return _NAME.get(schluessel, schluessel)


def ooxml_von(schluessel: str) -> str:
    return _OOXML.get(schluessel, "clear")


def schluessel_von_ooxml(wert: str | None) -> str | None:
    return _VON_OOXML.get(wert or "")


def _an(schluessel: str, x: int, y: int) -> bool:
    """Ist das Bildelement (x, y) der 8 × 8-Kachel in der Musterfarbe?"""
    if schluessel == "rein":
        return True
    if schluessel.startswith("pct"):
        p = float(schluessel[3:].replace("_", "."))
        return p * 64 / 100 > _BAYER[y][x]
    art, richtung = schluessel.split("_", 1)
    dick = art == "dunkel"
    breit = 3 if dick else 1
    waag, senk = y < breit, x < breit
    ab, auf = (x - y) % 8 < breit, (x + y) % 8 < breit
    return {"h": waag, "v": senk, "ab": ab, "auf": auf, "raster": waag or senk, "karo": ab or auf}[richtung]


def kachel(schluessel: str, muster: str = "#000000", fuell: str | None = None) -> QPixmap:
    """Eine 8 × 8-Kachel des Musters; ohne Füllfarbe bleibt der Grund durchsichtig."""
    bild = QImage(8, 8, QImage.Format_ARGB32)
    grund = QColor(fuell) if fuell else QColor(0, 0, 0, 0)
    vorn = QColor(muster)
    for y in range(8):
        for x in range(8):
            bild.setPixelColor(x, y, vorn if schluessel != "loeschen" and _an(schluessel, x, y) else grund)
    return QPixmap.fromImage(bild)


def pinsel(schluessel: str, muster: str = "#000000", fuell: str | None = None) -> QBrush:
    """Der Pinsel für den Hintergrund eines Absatzes (Muster über Füllfarbe)."""
    if schluessel in ("", "loeschen"):
        return QBrush(QColor(fuell)) if fuell else QBrush(Qt.NoBrush)
    return QBrush(kachel(schluessel, muster, fuell))


def als_text(schluessel: str, muster: str, fuell: str | None) -> str:
    return f"{schluessel}|{muster}|{fuell or ''}"


def aus_text(text: str | None) -> tuple[str, str, str | None] | None:
    if not text:
        return None
    t = text.split("|")
    if len(t) < 2 or not t[0] or t[0] not in _NAME:
        return None
    return t[0], t[1] or "#000000", (t[2] if len(t) > 2 and t[2] else None)
