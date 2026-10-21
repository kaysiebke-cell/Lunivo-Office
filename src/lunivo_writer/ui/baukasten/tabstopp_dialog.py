"""Das Fenster „Tabstopps“ als Baustein: Position und Ausrichtung festlegen, löschen, alle löschen.

    d = TabstoppDialog(parent, [(25.0, "links"), (80.0, "rechts")])     # Position in mm, Ausrichtung ``ARTEN``
    if d.exec(): d.stopps()                                              # dieselbe Liste, sortiert

Das Fenster setzt keine Tabstopps; der Aufrufer (Absatz-Fenster, Editor) übernimmt die Liste. Füllzeichen und Standardabstand
gibt es nicht, weil Qt sie nicht zeichnet.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QGroupBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QRadioButton, QVBoxLayout,
)

from lunivo_writer.ui.baukasten.mass_feld import MassSpin, einheit

ARTEN = (("links", "Links"), ("mitte", "Zentriert"), ("rechts", "Rechts"), ("dezimal", "Dezimal"))


def aus_qt(tabs) -> list[tuple[float, str]]:
    """Die Tabstopps eines Absatzformats (QTextOption.Tab) als Liste aus Millimetern und Ausrichtung."""
    from PySide6.QtGui import QTextOption
    from lunivo_writer.models.page import px_to_mm
    art = {QTextOption.LeftTab: "links", QTextOption.CenterTab: "mitte", QTextOption.RightTab: "rechts", QTextOption.DelimiterTab: "dezimal"}
    return [(round(px_to_mm(t.position), 1), art.get(t.type, "links")) for t in tabs]


def zu_qt(stopps) -> list:
    from PySide6.QtGui import QTextOption
    from lunivo_writer.models.page import mm_to_px
    art = {"links": QTextOption.LeftTab, "mitte": QTextOption.CenterTab, "rechts": QTextOption.RightTab, "dezimal": QTextOption.DelimiterTab}
    return [QTextOption.Tab(mm_to_px(m), art[a]) for m, a in stopps]


def _text(mm: float, art: str) -> str:
    f, kurz = einheit()
    return f"{mm * f:.2f} {kurz}".replace(".", ",") + "  ·  " + dict(ARTEN)[art]


class TabstoppDialog(QDialog):
    def __init__(self, parent=None, stopps=()):
        super().__init__(parent)
        self.setWindowTitle("Tabstopps")
        self.setMinimumWidth(520)
        self._stopps: list[tuple[float, str]] = sorted(((round(m, 1), a) for m, a in stopps), key=lambda x: x[0])
        self._geloescht: list[float] = []
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Tabstoppposition:"))
        z = QHBoxLayout()
        self.pos = MassSpin(); self.pos.setRange(0, 1000); self.pos.setDecimals(1); self.pos.setSingleStep(1.0)
        self.pos.setSpecialValueText(" ")                           # leer, solange nichts eingetragen ist
        z.addWidget(self.pos, 1)
        z.addStretch(2)
        v.addLayout(z)
        m = QHBoxLayout()
        self.liste = QListWidget(); self.liste.setMinimumHeight(110)
        m.addWidget(self.liste, 3)
        self.geloescht_text = QLabel(); self.geloescht_text.setWordWrap(True); self.geloescht_text.setAlignment(Qt.AlignTop)
        m.addWidget(self.geloescht_text, 2)
        v.addLayout(m)
        box = QGroupBox("Ausrichtung"); bh = QHBoxLayout(box)
        self.art = QButtonGroup(self)
        for i, k in enumerate(("dezimal", "links", "mitte", "rechts")):
            r = QRadioButton(dict(ARTEN)[k]); self.art.addButton(r, [a for a, _n in ARTEN].index(k)); bh.addWidget(r)
        self.art.button(0).setChecked(True)
        v.addWidget(box)
        h = QHBoxLayout()
        self.b_fest, self.b_loesch = QPushButton("Festlegen"), QPushButton("Löschen")
        self.b_fest.clicked.connect(self.festlegen); self.b_loesch.clicked.connect(self.loeschen)
        b_alle = QPushButton("Alle löschen"); b_alle.clicked.connect(self.alle)
        for b in (self.b_fest, self.b_loesch, b_alle):
            h.addWidget(b)
        h.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        h.addWidget(ab); h.addWidget(ok)
        v.addLayout(h)
        self.liste.currentRowChanged.connect(self._zeile)
        self.pos.valueChanged.connect(self._knoepfe)
        self._fuellen()

    def _fuellen(self) -> None:
        self.liste.clear()
        self.liste.addItems([_text(m, a) for m, a in self._stopps])
        f, kurz = einheit()
        self.geloescht_text.setText(("Zu löschende Tabstopps:\n" + ", ".join(f"{m * f:.2f}".replace(".", ",") + " " + kurz
                                                                              for m in self._geloescht)) if self._geloescht else "")
        self._knoepfe()

    def _knoepfe(self, *_) -> None:
        self.b_fest.setEnabled(self.pos.value() > 0)
        self.b_loesch.setEnabled(self.liste.currentRow() >= 0)

    def _zeile(self, i: int) -> None:
        if 0 <= i < len(self._stopps):
            m, a = self._stopps[i]
            self.pos.setValue(m)
            self.art.button([k for k, _n in ARTEN].index(a)).setChecked(True)
        self._knoepfe()

    def festlegen(self) -> None:
        m = round(self.pos.value(), 1)
        if m <= 0:
            return
        self._geloescht = [g for g in self._geloescht if g != m]
        self._stopps = sorted([s for s in self._stopps if s[0] != m] + [(m, ARTEN[self.art.checkedId()][0])], key=lambda x: x[0])
        self._fuellen()

    def loeschen(self) -> None:
        i = self.liste.currentRow()
        if 0 <= i < len(self._stopps):
            self._geloescht.append(self._stopps[i][0])
            del self._stopps[i]
            self._fuellen()

    def alle(self) -> None:
        self._geloescht += [m for m, _a in self._stopps]
        self._stopps = []
        self._fuellen()

    def stopps(self) -> list[tuple[float, str]]:
        return list(self._stopps)
