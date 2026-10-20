"""Zahlenfeld mit Maßeinheit: intern immer Millimeter, angezeigt in der gewählten Einheit (Optionen ▸ Speichern)."""
from __future__ import annotations

from PySide6.QtWidgets import QDoubleSpinBox


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
