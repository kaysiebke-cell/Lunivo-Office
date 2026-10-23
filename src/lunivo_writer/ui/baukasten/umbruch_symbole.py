"""Die Bildchen für den Textumbruch um ein Bild (wie im WPS): Textzeilen in Grau, das Bild als blaues Feld.

    f = umbruch_zeichner("quadrat")        # f(QPainter, QRectF) zeichnet das Bildchen in das Rechteck
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

# Schlüssel → Beschriftung, in der Reihenfolge des Reiters „Textumbruch“
from lunivo_writer.core.farben import Farbe
ARTEN = [("quadrat", "Quadrat"), ("passend", "Passend"), ("transparent", "Transparent"), ("obenunten", "Oben und Unten"),
         ("hinter", "Hinter den Text"), ("vor", "Vor dem Text"), ("textfluss", "Im Textfluss")]
BILD = QColor(Farbe.BLAU)
ZEILEN = 7


def umbruch_zeichner(art: str) -> Callable[[QPainter, QRectF], None]:
    def zeichne(p: QPainter, r: QRectF) -> None:
        p.save()
        pal = QColor(110, 118, 130)
        z_h = r.height() / (ZEILEN * 2 - 1)                          # Zeilenhöhe = Lücke
        bild = QRectF(r.left() + r.width() * 0.3, r.top() + r.height() * 0.28, r.width() * 0.32, r.height() * 0.42)

        def zeile(i: int, von: float = 0.0, bis: float = 1.0, farbe: QColor = pal) -> None:
            y = r.top() + z_h * (2 * i) + z_h / 2
            p.setPen(QPen(farbe, max(1.2, z_h * 0.7), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(int(r.left() + r.width() * (0.08 + 0.84 * von)), int(y), int(r.left() + r.width() * (0.08 + 0.84 * bis)), int(y))

        def feld(farbe: QColor = BILD) -> None:
            p.setPen(Qt.NoPen); p.setBrush(farbe); p.drawRoundedRect(bild, 2, 2)

        for i in range(ZEILEN):
            y0, y1 = r.top() + z_h * 2 * i, r.top() + z_h * (2 * i + 1)
            neben = y1 > bild.top() - 1 and y0 < bild.bottom() + 1                       # liegt die Zeile auf Höhe des Bildes?
            if art in ("quadrat", "passend", "transparent") and neben:
                links, rechts = (bild.left() - r.left() - r.width() * 0.04) / r.width(), (bild.right() - r.left() + r.width() * 0.04) / r.width()
                zeile(i, 0.0, max(0.0, (links - 0.08) / 0.84)); zeile(i, min(1.0, (rechts - 0.08) / 0.84), 1.0)
            elif art == "obenunten" and neben:
                continue
            else:
                zeile(i, 0.0, 1.0, pal if art != "hinter" else QColor(90, 96, 108))
        if art == "hinter":
            feld(QColor(76, 110, 245, 140))
        elif art == "textfluss":
            feld()
        else:
            feld()
        p.restore()
    return zeichne
