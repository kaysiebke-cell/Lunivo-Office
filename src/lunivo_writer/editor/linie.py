"""Eine Linie als Wert: Farbe, Stärke, Art und (für Absatzrahmen) die Seiten, auf denen sie steht.

Gespeichert wird sie als Text ``farbe|pt|art`` und, wenn nicht alle vier Seiten gemeint sind, ``|seiten`` dahinter —
``t`` oben, ``b`` unten, ``l`` links, ``r`` rechts, ``h`` die Linie zwischen zwei Absätzen. Ohne vierten Teil gelten alle vier
Seiten, so bleiben ältere Dateien gültig.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

LINIENBREITEN = (0.25, 0.5, 0.75, 1.0, 1.5, 2.25, 3.0, 4.5, 6.0)                       # pt
LINIENARTEN = {"einfach": ("Einfach", Qt.SolidLine), "gestrichelt": ("Gestrichelt", Qt.DashLine),
               "gepunktet": ("Gepunktet", Qt.DotLine), "strichpunkt": ("Strich-Punkt", Qt.DashDotLine),
               "doppelt": ("Doppelt", Qt.SolidLine)}
ALLE_SEITEN = "tblr"


@dataclass
class Linie:
    farbe: str = "#000000"
    breite_pt: float = 1.0
    art: str = "einfach"
    seiten: str = ALLE_SEITEN

    def text(self) -> str:
        basis = f"{self.farbe}|{self.breite_pt:g}|{self.art}"
        return basis if self.seiten == ALLE_SEITEN else f"{basis}|{self.seiten}"

    @classmethod
    def aus_text(cls, text: str | None) -> "Linie | None":
        if not text:
            return None
        t = text.split("|")
        try:
            return cls(t[0] or "#000000", float(t[1]) if len(t) > 1 and t[1] else 1.0, t[2] if len(t) > 2 and t[2] else "einfach",
                       t[3] if len(t) > 3 else ALLE_SEITEN)
        except ValueError:
            return None

    def mit_seiten(self, seiten: str) -> "Linie":
        return Linie(self.farbe, self.breite_pt, self.art, "".join(s for s in "tblrh" if s in seiten))

    def stift(self, massstab: float = 1.0) -> QPen:
        """QPen; ``massstab`` rechnet pt in Bildpunkte um (96/72 am Bildschirm, mal Zoom)."""
        p = QPen(QColor(self.farbe), max(0.6, self.breite_pt * massstab))
        p.setStyle(LINIENARTEN.get(self.art, LINIENARTEN["einfach"])[1])
        return p

    def zeichne(self, p: QPainter, x1: float, y1: float, x2: float, y2: float, massstab: float = 1.0) -> None:
        """Eine einzelne Linie; „doppelt“ als zwei dünne Striche nebeneinander."""
        s = self.stift(massstab)
        if self.art == "doppelt":
            d = max(1.0, s.widthF())
            s.setWidthF(max(0.5, d / 3)); p.setPen(s)
            waag = abs(y2 - y1) < abs(x2 - x1)
            dx, dy = (0, d) if waag else (d, 0)
            p.drawLine(int(x1 - dx), int(y1 - dy), int(x2 - dx), int(y2 - dy))
            p.drawLine(int(x1 + dx), int(y1 + dy), int(x2 + dx), int(y2 + dy))
        else:
            p.setPen(s); p.drawLine(int(x1), int(y1), int(x2), int(y2))

    def rahmen_zeichnen(self, p: QPainter, r: QRectF, massstab: float = 1.0, innen_y=()) -> None:
        """Zeichnet die gemeinten Seiten eines Rechtecks; „doppelt“ mit zweitem Rahmen innen. ``innen_y``: Höhen der Linien
        zwischen Absätzen (nur wenn ``h`` gesetzt ist)."""
        s = self.stift(massstab)
        p.setPen(s); p.setBrush(Qt.NoBrush)
        lagen = [0.0] + ([s.widthF() * 3] if self.art == "doppelt" else [])
        for g in lagen:
            rr = r.adjusted(g, g, -g, -g)
            if "t" in self.seiten:
                p.drawLine(rr.topLeft(), rr.topRight())
            if "b" in self.seiten:
                p.drawLine(rr.bottomLeft(), rr.bottomRight())
            if "l" in self.seiten:
                p.drawLine(rr.topLeft(), rr.bottomLeft())
            if "r" in self.seiten:
                p.drawLine(rr.topRight(), rr.bottomRight())
            if "h" in self.seiten:
                for y in innen_y:
                    p.drawLine(QPointF(rr.left(), y), QPointF(rr.right(), y))
