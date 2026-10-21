"""Regler und Schrittfeld für Dialoge.

``SchiebeFeld(0, 100, " %")``: der Wert steht über dem Regler, links und rechts davon je ein Knopf „−“ und „+“ (wie die Regler im Fenster „Texteffekte“).
``SchrittFeld(0, 60, " pt")``: ein Zahlenfeld mit „−“ links und „+“ rechts. Beide haben ``value()``, ``setValue()`` und ``valueChanged``.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QSlider, QToolButton, QVBoxLayout, QWidget


def _knopf(text: str) -> QToolButton:
    k = QToolButton(); k.setText(text); k.setAutoRaise(False); k.setFixedSize(26, 26); k.setAutoRepeat(True)
    return k


class SchrittFeld(QWidget):
    valueChanged = Signal(float)

    def __init__(self, lo: float = 0.0, hi: float = 100.0, suffix: str = "", schritt: float = 1.0, nachkomma: int = 0, wert: float = 0.0):
        super().__init__()
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        self.feld = QDoubleSpinBox(); self.feld.setRange(lo, hi); self.feld.setDecimals(nachkomma); self.feld.setSingleStep(schritt)
        self.feld.setSuffix(suffix); self.feld.setButtonSymbols(QDoubleSpinBox.NoButtons); self.feld.setAlignment(Qt.AlignCenter); self.feld.setMinimumWidth(80)
        minus, plus = _knopf("−"), _knopf("+")
        minus.clicked.connect(lambda: self.feld.stepBy(-1)); plus.clicked.connect(lambda: self.feld.stepBy(1))
        h.addWidget(minus); h.addWidget(self.feld, 1); h.addWidget(plus)
        self.feld.setValue(wert)
        self.feld.valueChanged.connect(self.valueChanged)

    def value(self) -> float:
        return self.feld.value()

    def setValue(self, v: float) -> None:
        self.feld.setValue(v)


class SchiebeFeld(QWidget):
    valueChanged = Signal(float)

    def __init__(self, lo: float = 0.0, hi: float = 100.0, suffix: str = "", schritt: float = 1.0, nachkomma: int = 0, wert: float = 0.0):
        super().__init__()
        self._f = 10 ** nachkomma; self._suffix = suffix; self._nk = nachkomma; self._schritt = schritt
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        self.anzeige = QLabel(); self.anzeige.setStyleSheet("color: palette(mid); font-size: 8pt;"); v.addWidget(self.anzeige)
        h = QHBoxLayout(); h.setSpacing(4); h.setContentsMargins(0, 0, 0, 0)
        self.regler = QSlider(Qt.Horizontal); self.regler.setRange(int(lo * self._f), int(hi * self._f))
        minus, plus = _knopf("−"), _knopf("+")
        minus.clicked.connect(lambda: self.setValue(self.value() - schritt, melden=True)); plus.clicked.connect(lambda: self.setValue(self.value() + schritt, melden=True))
        h.addWidget(minus); h.addWidget(self.regler, 1); h.addWidget(plus)
        v.addLayout(h)
        self.setValue(wert)
        self.regler.valueChanged.connect(lambda x: self._zeige(x / self._f, True))

    def _zeige(self, w: float, melden: bool) -> None:
        self.anzeige.setText(f"{w:.{self._nk}f}".replace(".", ",") + self._suffix)
        if melden:
            self.valueChanged.emit(w)

    def value(self) -> float:
        return self.regler.value() / self._f

    def setValue(self, v: float, melden: bool = False) -> None:
        self.regler.blockSignals(True); self.regler.setValue(int(round(v * self._f))); self.regler.blockSignals(False)
        self._zeige(self.value(), melden)
