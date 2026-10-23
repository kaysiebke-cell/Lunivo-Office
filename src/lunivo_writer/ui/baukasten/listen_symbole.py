"""Kleine Vorschaubilder für Aufzählungs- und Nummerierungsarten (drei Zeilen mit Zeichen davor)."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter


from lunivo_writer.core.farben import Farbe
def liste_zeichner(marke: str | None):
    """``marke``: 'disc', 'circle', 'square' oder die Zeichenfolge der ersten drei Nummern (z. B. '1.|2.|3.'); None = Keine."""
    def zeichne(p: QPainter, r: QRectF) -> None:
        dunkel, grau = QColor(Farbe.TINTE), QColor(Farbe.GRAU_HELL)
        h = r.height() / 3
        for i in range(3):
            y = r.top() + h * i + h / 2
            if marke is None:
                p.setPen(grau); p.drawLine(int(r.left() + 6), int(y), int(r.right() - 6), int(y))
                continue
            x0 = r.left() + 6
            if marke in ("disc", "circle", "square"):
                p.setPen(dunkel); p.setBrush(dunkel if marke != "circle" else Qt.NoBrush)
                form = QRectF(x0, y - 3, 6, 6)
                p.drawEllipse(form) if marke != "square" else p.drawRect(form)
            else:
                f = QFont(p.font()); f.setPixelSize(max(8, int(h * 0.75))); p.setFont(f)
                p.setPen(dunkel); p.drawText(QRectF(x0 - 2, y - h / 2, 18, h), Qt.AlignVCenter | Qt.AlignLeft, marke.split("|")[i])
            p.setPen(grau); p.drawLine(int(x0 + 16), int(y), int(r.right() - 6), int(y))
    return zeichne
