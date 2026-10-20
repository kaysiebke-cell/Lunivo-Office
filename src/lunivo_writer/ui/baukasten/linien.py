"""Linien: Stärke, Art, Farbe — als Wert, als Auswahlzeile für Dialoge und als Rahmen-Menü (unten, oben, links, rechts …)."""
from __future__ import annotations

from enum import Flag, auto

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QWidget

from lunivo_writer.editor.linie import ALLE_SEITEN, LINIENARTEN, LINIENBREITEN, Linie  # noqa: F401
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.menue_liste import MenueListe


def linien_symbol(art: str, groesse: QSize = QSize(56, 14), farbe: str = "#343a40") -> QIcon:
    pm = QPixmap(groesse); pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    Linie(farbe, 1.5, art).zeichne(p, 2, groesse.height() / 2, groesse.width() - 2, groesse.height() / 2, 96 / 72)
    p.end()
    return QIcon(pm)


class LinienWahl(QWidget):
    """Eine Zeile aus Art, Stärke und Farbe. Meldet jede Änderung als ``Linie``."""

    geaendert = Signal(object)

    def __init__(self, linie: Linie | None = None, *, arten=tuple(LINIENARTEN), breiten=LINIENBREITEN, parent=None):
        super().__init__(parent)
        linie = linie or Linie()
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0)
        self.art = QComboBox(); self.art.setIconSize(QSize(56, 14))
        for k in arten:
            self.art.addItem(linien_symbol(k), LINIENARTEN[k][0], k)
        self.breite = QComboBox()
        for b in breiten:
            self.breite.addItem(f"{b:g}".replace(".", ",") + " pt", b)
        self.farbe = FarbFeld(linie.farbe, "Linienfarbe")
        for w in (self.art, self.breite, self.farbe):
            h.addWidget(w)
        self.setLinie(linie)
        self.art.currentIndexChanged.connect(self._aend)
        self.breite.currentIndexChanged.connect(self._aend)
        self.farbe.farbeGeaendert.connect(lambda _f: self._aend())

    def setLinie(self, linie: Linie) -> None:
        i = self.art.findData(linie.art); self.art.setCurrentIndex(max(0, i))
        j = min(range(self.breite.count()), key=lambda k: abs(self.breite.itemData(k) - linie.breite_pt))
        self.breite.setCurrentIndex(j)
        self.farbe.setFarbe(linie.farbe)

    def linie(self) -> Linie:
        return Linie(self.farbe.farbe or "#000000", float(self.breite.currentData()), str(self.art.currentData()))

    def _aend(self) -> None:
        self.geaendert.emit(self.linie())


class RahmenSeiten(Flag):
    KEINE = 0
    OBEN = auto()
    UNTEN = auto()
    LINKS = auto()
    RECHTS = auto()
    INNEN_H = auto()
    INNEN_V = auto()
    AUSSEN = OBEN | UNTEN | LINKS | RECHTS
    ALLE = AUSSEN | INNEN_H | INNEN_V


RAHMEN_EINTRAEGE = (
    ("unten", "Rahmenlinie unten", RahmenSeiten.UNTEN), ("oben", "Rahmenlinie oben", RahmenSeiten.OBEN),
    ("links", "Rahmenlinie links", RahmenSeiten.LINKS), ("rechts", "Rahmenlinie rechts", RahmenSeiten.RECHTS),
    None,
    ("kein", "Kein Rahmen", RahmenSeiten.KEINE), ("alle", "Alle Rahmenlinien", RahmenSeiten.ALLE),
    ("aussen", "Rahmenlinien außen", RahmenSeiten.AUSSEN),
    ("innen_h", "Innere horizontale Rahmenlinie", RahmenSeiten.INNEN_H), ("innen_v", "Innere vertikale Rahmenlinie", RahmenSeiten.INNEN_V),
)


def rahmen_symbol(seiten: RahmenSeiten, groesse: int = 16) -> QIcon:
    """Kleines Quadrat, in dem nur die gemeinten Linien kräftig sind."""
    pm = QPixmap(groesse, groesse); pm.fill(Qt.transparent)
    p = QPainter(pm)
    r = QRectF(1.5, 1.5, groesse - 3, groesse - 3)
    pal = QApplication.palette()                       # Farben der Oberfläche — im dunklen Design sonst kaum zu sehen
    blass = QPen(pal.color(QPalette.Mid), 1, Qt.DotLine)
    stark = QPen(pal.color(QPalette.WindowText), max(2.0, groesse / 8), Qt.SolidLine, Qt.RoundCap)
    mitte_x, mitte_y = r.center().x(), r.center().y()
    for flagge, linie in ((RahmenSeiten.OBEN, (r.left(), r.top(), r.right(), r.top())), (RahmenSeiten.UNTEN, (r.left(), r.bottom(), r.right(), r.bottom())),
                          (RahmenSeiten.LINKS, (r.left(), r.top(), r.left(), r.bottom())), (RahmenSeiten.RECHTS, (r.right(), r.top(), r.right(), r.bottom())),
                          (RahmenSeiten.INNEN_H, (r.left(), mitte_y, r.right(), mitte_y)), (RahmenSeiten.INNEN_V, (mitte_x, r.top(), mitte_x, r.bottom()))):
        p.setPen(stark if flagge in seiten else blass)
        p.drawLine(*[int(v) for v in linie])
    p.end()
    return QIcon(pm)


class RahmenMenue(MenueListe):
    """Das Rahmen-Menü (Unten, Oben, Links, Rechts, Kein, Alle, Außen, Innen). Meldet die gewählten Seiten."""

    gewaehlt = Signal(object, str)         # RahmenSeiten, Schlüssel ('unten', 'alle', 'kein' …)

    def __init__(self, parent=None, *, innen: bool | str = True, mehr_text: str | None = "Rahmen und Schattierung …", mehr=None):
        """``innen``: True = beide inneren Linien (Tabelle), ``"h"`` = nur die waagerechte (Absätze), False = keine."""
        super().__init__(parent)
        erlaubt = {True: "hv", False: ""}.get(innen, innen)
        for e in RAHMEN_EINTRAEGE:
            if e is None:
                self.trenner(); continue
            schl, text, seiten = e
            if schl.startswith("innen_") and schl[-1] not in erlaubt:
                continue
            self.eintrag(text, lambda s=seiten, k=schl: self.gewaehlt.emit(s, k), symbol=rahmen_symbol(seiten))
        if mehr_text and mehr is not None:
            self.trenner()
            self.eintrag(mehr_text, mehr)
