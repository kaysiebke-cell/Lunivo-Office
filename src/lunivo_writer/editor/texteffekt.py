"""Texteffekte, die Lunivo zeichnet: Füllung des Textes (Farbe, Transparenz) und Kontur (Farbe, Breite, Linienart).

Ein Effekt ist ``{"fuell": "farbe"|"keine", "farbe": "#rrggbb"|"", "transparenz": 0…100, "kontur": bool, "kontur_farbe": "#rrggbb",
"kontur_breite": pt, "kontur_art": Schlüssel aus ``KONTUR_ARTEN``}``. Als Text (für eine Formatvorlage): ``transparenz|kontur_farbe|breite|art``
(leer = kein Effekt; die Füllfarbe steht bei der Vorlage in ihrem Feld „farbe“). Schatten, Spiegelung, Leuchten und 3D gibt es nicht,
weil Qt sie am Text nicht zeichnet.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QTextCharFormat, QTextFormat

KONTUR_ARTEN = {"einfach": ("Durchgezogen", Qt.SolidLine), "gepunktet": ("Gepunktet", Qt.DotLine), "gestrichelt": ("Gestrichelt", Qt.DashLine),
                "strichpunkt": ("Strich-Punkt", Qt.DashDotLine), "strichpunktpunkt": ("Strich-Punkt-Punkt", Qt.DashDotDotLine)}
EFFEKT = {"fuell": "farbe", "farbe": "", "transparenz": 0, "kontur": False, "kontur_farbe": "#000000", "kontur_breite": 0.75, "kontur_art": "einfach"}


def zu_format(w: dict) -> QTextCharFormat:
    """Zeichenformat, das den Effekt zeichnet (zum Anwenden im Editor und für Vorschauen)."""
    w = {**EFFEKT, **w}
    f = QTextCharFormat()
    if w["fuell"] == "keine":
        f.setForeground(QColor(0, 0, 0, 0))
    elif w["farbe"] or w["transparenz"]:
        c = QColor(w["farbe"] or "#000000")
        c.setAlphaF(1.0 - w["transparenz"] / 100)
        f.setForeground(c)
    if w["kontur"]:
        p = QPen(QColor(w["kontur_farbe"]), max(0.1, w["kontur_breite"]) / 0.75, KONTUR_ARTEN.get(w["kontur_art"], KONTUR_ARTEN["einfach"])[1])
    else:
        p = QPen(Qt.NoPen)
    f.setTextOutline(p)
    return f


def aus_format(cf: QTextCharFormat) -> dict:
    w = dict(EFFEKT)
    if cf.hasProperty(QTextFormat.ForegroundBrush) and cf.foreground().style() != Qt.NoBrush:
        c = cf.foreground().color()
        if c.alpha() == 0:
            w["fuell"] = "keine"
        else:
            w["farbe"] = c.name(); w["transparenz"] = round(100 - c.alphaF() * 100)
    p = cf.textOutline()
    if p.style() != Qt.NoPen:
        w["kontur"] = True; w["kontur_farbe"] = p.color().name(); w["kontur_breite"] = round(p.widthF() * 0.75, 2)
        w["kontur_art"] = next((k for k, v in KONTUR_ARTEN.items() if v[1] == p.style()), "einfach")
    return w


def als_text(w: dict | None) -> str:
    """Nur Transparenz und Kontur; ``""`` wenn weder noch."""
    if not w or not (w.get("kontur") or w.get("transparenz")):
        return ""
    return f"{int(w.get('transparenz', 0))}|{w['kontur_farbe'] if w.get('kontur') else ''}|{w.get('kontur_breite', 0.75):g}|{w.get('kontur_art', 'einfach')}"


def aus_text(text: str | None, farbe: str = "") -> dict | None:
    t = (text or "").split("|")
    if len(t) != 4:
        return None
    try:
        return {**EFFEKT, "farbe": farbe, "transparenz": int(t[0]), "kontur": bool(t[1]), "kontur_farbe": t[1] or "#000000",
                "kontur_breite": float(t[2]), "kontur_art": t[3] if t[3] in KONTUR_ARTEN else "einfach"}
    except ValueError:
        return None
