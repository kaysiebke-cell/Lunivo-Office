"""Rahmen und Schattierung eines Absatzes: Seiten, Linie (Art, Stärke, Farbe), Füllfarbe, mit Vorschau."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QToolButton, QWidget

from lunivo_writer.editor.linie import Linie
from lunivo_writer.ui.baukasten import DialogRahmen, FarbFeld, LinienWahl, RahmenSeiten
from lunivo_writer.ui.baukasten.linien import rahmen_symbol

_SEITEN = (("t", "Oben", RahmenSeiten.OBEN), ("b", "Unten", RahmenSeiten.UNTEN), ("l", "Links", RahmenSeiten.LINKS),
           ("r", "Rechts", RahmenSeiten.RECHTS), ("h", "Zwischen Absätzen", RahmenSeiten.INNEN_H))


class AbsatzRahmenDialog(DialogRahmen):
    def __init__(self, parent, linie: Linie | None, schattierung: str | None = None, stil: Linie | None = None):
        super().__init__(parent, "Rahmen und Schattierung", self._male)
        basis = linie or stil or Linie("#000000", 0.75, "einfach")
        self.linie = LinienWahl(Linie(basis.farbe, basis.breite_pt, basis.art))
        self.schatt = FarbFeld(schattierung or "", "Schattierung", keine_text="Keine")
        self.knoepfe_seiten: dict[str, QToolButton] = {}
        reihe = QWidget(); h = QHBoxLayout(reihe); h.setContentsMargins(0, 0, 0, 0)
        for k, text, flagge in _SEITEN:
            b = QToolButton(); b.setCheckable(True); b.setIcon(rahmen_symbol(flagge)); b.setToolTip(text); b.setText(text)
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setChecked(bool(linie) and k in linie.seiten)
            b.toggled.connect(self.aktualisieren)
            self.knoepfe_seiten[k] = b; h.addWidget(b)
        voreinst = QWidget(); v = QHBoxLayout(voreinst); v.setContentsMargins(0, 0, 0, 0)
        for text, seiten in (("Kein", ""), ("Außen", "tblr"), ("Alle", "tblrh")):
            k = QPushButton(text); k.clicked.connect(lambda _c=False, s=seiten: self.setze_seiten(s)); v.addWidget(k)
        self.zeile("Einstellung", voreinst)
        self.zeile("Rahmen auf", reihe)
        self.zeile("Linie", self.linie)
        self.zeile("Schattierung", self.schatt)
        self.linie.geaendert.connect(self.aktualisieren)
        self.schatt.farbeGeaendert.connect(self.aktualisieren)

    def setze_seiten(self, seiten: str) -> None:
        for k, b in self.knoepfe_seiten.items():
            b.setChecked(k in seiten)

    def seiten(self) -> str:
        return "".join(k for k, _t, _f in _SEITEN if self.knoepfe_seiten[k].isChecked())

    def _male(self, p, r) -> None:
        li = self.linie.linie().mit_seiten(self.seiten())
        feld = QRectF(r).adjusted(30, 8, -30, -8)
        if self.schatt.farbe:
            p.fillRect(feld, QColor(self.schatt.farbe))
        p.setPen(Qt.NoPen); p.setBrush(QColor("#adb5bd"))
        zeilen = 3
        hoehe = feld.height() / (zeilen * 2)
        zwischen = []
        for i in range(zeilen):
            y = feld.top() + hoehe * (i * 2 + 0.5)
            p.drawRect(QRectF(feld.left() + 8, y, feld.width() - 16 - (i == zeilen - 1) * 40, hoehe * 0.8))
            if i:
                zwischen.append(feld.top() + hoehe * (i * 2 - 0.5))
        li.rahmen_zeichnen(p, feld, 96 / 72, zwischen)

    def ergebnis(self):
        """(Linie oder None, Schattierungsfarbe oder None)."""
        s = self.seiten()
        return (self.linie.linie().mit_seiten(s) if s else None, self.schatt.farbe or None)
