"""Eine Linie als Wert: Farbe, Stärke, Art und (für Absatzrahmen) die Seiten, auf denen sie steht.

Gespeichert wird sie als Text ``farbe|pt|art`` und, wenn nicht alle vier Seiten gemeint sind, ``|seiten`` dahinter —
``t`` oben, ``b`` unten, ``l`` links, ``r`` rechts, ``h`` die Linie zwischen zwei Absätzen. Ohne vierten Teil gelten alle vier
Seiten, so bleiben ältere Dateien gültig.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

LINIENBREITEN = (0.25, 0.5, 0.75, 1.0, 1.5, 2.25, 3.0, 4.5, 6.0)                       # pt
ALLE_SEITEN = "tblr"


def _bauen() -> dict:
    """Die Linienarten der Auswahl „Formatvorlage“: Schlüssel → (Name, Strichart, DOCX-Wert, Bahnen, wellig).

    Eine Bahn ist (Abstand von der Mitte, Dicke), beides in Linienbreiten. Mehrfachlinien sind mehrere Bahnen nebeneinander."""
    a = {"einfach": ("Einfach", Qt.SolidLine, "single", [(0, 1.0)], False),
         "gepunktet": ("Gepunktet", Qt.DotLine, "dotted", [(0, 1.0)], False),
         "fein_gestrichelt": ("Fein gestrichelt", (3.0, 2.0), "dashSmallGap", [(0, 1.0)], False),
         "gestrichelt": ("Gestrichelt", Qt.DashLine, "dashed", [(0, 1.0)], False),
         "strichpunkt": ("Strich-Punkt", Qt.DashDotLine, "dotDash", [(0, 1.0)], False),
         "strichpunktpunkt": ("Strich-Punkt-Punkt", Qt.DashDotDotLine, "dotDotDash", [(0, 1.0)], False),
         "doppelt": ("Doppelt", Qt.SolidLine, "double", [(-1.0, 0.34), (1.0, 0.34)], False),
         "dreifach": ("Dreifach", Qt.SolidLine, "triple", [(-1.7, 0.3), (0, 0.3), (1.7, 0.3)], False)}
    for gross, name, wert in ((1.0, "eng", "Small"), (1.7, "mittel", "Medium"), (2.5, "weit", "Large")):
        spanne = 0.3 + gross + 1.0
        a[f"duenn_dick_{name}"] = (f"Dünn–dick ({name})", Qt.SolidLine, f"thinThick{wert}Gap",
                                   [(-spanne / 2 + 0.15, 0.3), (spanne / 2 - 0.5, 1.0)], False)
        a[f"dick_duenn_{name}"] = (f"Dick–dünn ({name})", Qt.SolidLine, f"thickThin{wert}Gap",
                                   [(-spanne / 2 + 0.5, 1.0), (spanne / 2 - 0.15, 0.3)], False)
        bis = 0.3 + gross + 1.0 + gross + 0.3
        a[f"duenn_dick_duenn_{name}"] = (f"Dünn–dick–dünn ({name})", Qt.SolidLine, f"thinThickThin{wert}Gap",
                                         [(-bis / 2 + 0.15, 0.3), (0, 1.0), (bis / 2 - 0.15, 0.3)], False)
    a["wellig"] = ("Wellenlinie", Qt.SolidLine, "wave", [(0, 1.0)], True)
    a["doppelwellig"] = ("Doppelte Wellenlinie", Qt.SolidLine, "doubleWave", [(-1.1, 0.45), (1.1, 0.45)], True)
    return a


STILE = _bauen()
LINIENARTEN = {k: (v[0], v[1]) for k, v in STILE.items()}                              # Name und Strichart (wie bisher)
_VON_DOCX = {v[2]: k for k, v in STILE.items()}


def docx_wert(art: str) -> str:
    """Wert von ``w:val`` für eine Linienart (unbekannt: einfach)."""
    return STILE.get(art, STILE["einfach"])[2]


def art_aus_docx(wert: str | None) -> str:
    return _VON_DOCX.get(wert or "", "einfach")


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
        """QPen der Linie (bei Mehrfachlinien die Gesamtbreite); ``massstab`` rechnet pt in Bildpunkte um (96/72 am Bildschirm, mal Zoom)."""
        p = QPen(QColor(self.farbe), max(0.6, self.breite_pt * massstab))
        p.setStyle(LINIENARTEN.get(self.art, LINIENARTEN["einfach"])[1] if not isinstance(STILE.get(self.art, STILE["einfach"])[1], tuple) else Qt.SolidLine)
        return p

    def _bahn_stift(self, w: float, dicke: float, strich) -> QPen:
        p = QPen(QColor(self.farbe), max(0.6, w * dicke))
        if isinstance(strich, tuple):
            p.setDashPattern(list(strich))
        else:
            p.setStyle(strich)
        p.setCapStyle(Qt.FlatCap)
        return p

    def zeichne(self, p: QPainter, x1: float, y1: float, x2: float, y2: float, massstab: float = 1.0) -> None:
        """Eine einzelne Linie in ihrer Art: einfach, gestrichelt, mehrfach (Bahnen nebeneinander) oder wellig."""
        _n, strich, _d, bahnen, wellig = STILE.get(self.art, STILE["einfach"])
        w = max(0.6, self.breite_pt * massstab)
        laenge = math.hypot(x2 - x1, y2 - y1)
        if laenge <= 0:
            return
        nx, ny = -(y2 - y1) / laenge, (x2 - x1) / laenge
        for versatz, dicke in bahnen:
            ox, oy = nx * versatz * w, ny * versatz * w
            p.setPen(self._bahn_stift(w, dicke, strich))
            if not wellig:
                p.drawLine(QPointF(x1 + ox, y1 + oy), QPointF(x2 + ox, y2 + oy))
                continue
            amp, lam = max(1.2, w * 0.9), max(6.0, w * 6)                       # Wellenlinie: Sinus entlang der Linie
            ux, uy = (x2 - x1) / laenge, (y2 - y1) / laenge
            pts, t = [], 0.0
            while t <= laenge:
                d = amp * math.sin(2 * math.pi * t / lam)
                pts.append(QPointF(x1 + ox + ux * t + nx * d, y1 + oy + uy * t + ny * d))
                t += 1.0
            p.drawPolyline(pts)

    def rahmen_zeichnen(self, p: QPainter, r: QRectF, massstab: float = 1.0, innen_y=()) -> None:
        """Zeichnet die gemeinten Seiten eines Rechtecks in der Linienart. ``innen_y``: Höhen der Linien zwischen Absätzen
        (nur wenn ``h`` gesetzt ist)."""
        p.setBrush(Qt.NoBrush)
        if "t" in self.seiten:
            self.zeichne(p, r.left(), r.top(), r.right(), r.top(), massstab)
        if "b" in self.seiten:
            self.zeichne(p, r.left(), r.bottom(), r.right(), r.bottom(), massstab)
        if "l" in self.seiten:
            self.zeichne(p, r.left(), r.top(), r.left(), r.bottom(), massstab)
        if "r" in self.seiten:
            self.zeichne(p, r.right(), r.top(), r.right(), r.bottom(), massstab)
        if "h" in self.seiten:
            for y in innen_y:
                self.zeichne(p, r.left(), y, r.right(), y, massstab)
