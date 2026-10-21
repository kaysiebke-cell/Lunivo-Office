"""Zahlenfeld mit Maßeinheit: intern immer Millimeter, angezeigt in der gewählten Einheit (Optionen ▸ Speichern)."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QWidget


# Maßeinheit der Oberfläche (Optionen ▸ Speichern): intern bleibt alles in Millimetern, nur die Anzeige wechselt.
EINHEITEN = {"Millimeter": (1.0, "mm"), "Zentimeter": (0.1, "cm"), "Zoll": (1 / 25.4, "in"),
             "Punkt": (72 / 25.4, "pt"), "Pica": (6 / 25.4, "pc")}
_einheit = "Millimeter"


def set_einheit(name: str) -> None:
    global _einheit
    _einheit = name if name in EINHEITEN else "Millimeter"


def einheit() -> tuple[float, str]:
    return EINHEITEN[_einheit]


class MassSpin(QDoubleSpinBox):
    """Wert in mm, Anzeige in der gewählten Maßeinheit; wer „mm“ eingibt oder „2 cm“ tippt, wird verstanden."""

    def textFromValue(self, v: float) -> str:
        f, kurz = einheit()
        return f"{v * f:.{2 if f != 1.0 else self.decimals()}f}".replace(".", ",") + " " + kurz

    def valueFromText(self, text: str) -> float:
        import re
        m = re.match(r"\s*(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z]*)", text)
        if not m:
            return self.value()
        zahl = float(m.group(1).replace(",", "."))
        f, kurz = einheit()
        eigene = {"mm": 1.0, "cm": 0.1, "in": 1 / 25.4, "zoll": 1 / 25.4, "pt": 72 / 25.4, "pc": 6 / 25.4}
        fak = eigene.get(m.group(2).lower(), f)
        return zahl / fak

    def validate(self, text, pos):
        from PySide6.QtGui import QValidator
        import re
        return (QValidator.Acceptable if re.match(r"^\s*-?\d*[.,]?\d*\s*[a-zA-Z]*\s*$", text) else QValidator.Invalid), text, pos


def spin(value: float, lo=0.0, hi=500.0, suffix=" mm", step=1.0, decimals=1) -> QDoubleSpinBox:
    s = MassSpin() if suffix == " mm" else QDoubleSpinBox()
    s.setRange(lo, hi); s.setSingleStep(step); s.setDecimals(decimals); s.setValue(value)
    if suffix != " mm":
        s.setSuffix(suffix)
    return s


# Einheiten des Feldes mit Einheiten-Auswahl: Name → (Faktor von mm, Kürzel, Nachkommastellen). 1 Zeichen = 1 Schriftgröße des Standardtexts (11 pt),
# 1 Zeile = 1,2 Schriftgrößen.
_PT_MM = 25.4 / 72
FELD_EINHEITEN = {"mm": (1.0, "mm", 1), "cm": (0.1, "cm", 2), "in": (1 / 25.4, "in", 2), "pt": (1 / _PT_MM, "pt", 1),
                  "Zeichen": (1 / (11 * _PT_MM), "Zeichen", 2), "Zeile": (1 / (13.2 * _PT_MM), "Zeilen", 2)}


class EinheitFeld(QWidget):
    """Zahlenfeld mit Einheiten-Auswahl daneben (wie „0 char ▾“ im WPS): der Wert ist immer in Millimetern, angezeigt wird er in der
    gewählten Einheit. ``value()`` / ``setValue()`` / ``valueChanged`` arbeiten in Millimetern."""
    valueChanged = Signal(float)

    def __init__(self, wert_mm: float = 0.0, lo: float = 0.0, hi: float = 500.0, einheiten=("mm", "cm", "in", "pt", "Zeichen"), start: str | None = None,
                 leer_bei_null: bool = False):
        super().__init__()
        self._mm = wert_mm
        self._lo, self._hi = lo, hi
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(4)
        self.zahl = QDoubleSpinBox(); self.zahl.setSingleStep(1.0)
        if leer_bei_null:
            self.zahl.setSpecialValueText(" ")            # leer, solange nichts eingetragen ist
        self.einheit = QComboBox()
        for k in einheiten:
            self.einheit.addItem(FELD_EINHEITEN[k][1], k)
        self.zahl.setMinimumWidth(60); self.einheit.setMinimumWidth(46); self.einheit.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon); self.einheit.setMinimumContentsLength(3)
        h.addWidget(self.zahl, 1); h.addWidget(self.einheit)
        k0 = start or einheit_name()
        self.einheit.setCurrentIndex(max(0, self.einheit.findData(k0)))
        self._zeige()
        self.zahl.valueChanged.connect(self._gelesen)
        self.einheit.currentIndexChanged.connect(lambda *_: self._zeige())

    def _faktor(self) -> float:
        return FELD_EINHEITEN[self.einheit.currentData()][0]

    def _zeige(self) -> None:
        f, _k, nk = FELD_EINHEITEN[self.einheit.currentData()]
        self.zahl.blockSignals(True)
        self.zahl.setDecimals(nk); self.zahl.setRange(self._lo * f, self._hi * f); self.zahl.setValue(self._mm * f)
        self.zahl.blockSignals(False)

    def _gelesen(self, v: float) -> None:
        self._mm = v / self._faktor()
        self.valueChanged.emit(self._mm)

    def value(self) -> float:
        return self._mm

    def setValue(self, mm: float) -> None:
        if abs(mm - self._mm) < 1e-9:
            return
        self._mm = mm; self._zeige()
        self.valueChanged.emit(mm)


def einheit_name() -> str:
    """Kürzel der Maßeinheit der Oberfläche (Optionen ▸ Speichern) als Schlüssel von ``FELD_EINHEITEN``."""
    return {"Millimeter": "mm", "Zentimeter": "cm", "Zoll": "in", "Punkt": "pt", "Pica": "mm"}.get(_einheit, "mm")
