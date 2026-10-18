"""Symbole: dieselben 24×24-Strichzeichnungen wie im alten Programm (Lucide, ISC), mit Qt gerendert."""
from __future__ import annotations

import json
import os

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

_HIER = os.path.dirname(os.path.abspath(__file__))
_PFADE: dict | None = None
_CACHE: dict = {}
STRICH = 1.7
FAKTOR = 1.0          # Größe der Symbole (Optionen ▸ Darstellung)


_ORIGINAL: dict | None = None


def pfade_original() -> dict:
    """Die mitgelieferten Symbole, ohne Austausch."""
    global _ORIGINAL
    if _ORIGINAL is None:
        with open(os.path.join(_HIER, "..", "resources", "symbole.json"), encoding="utf-8") as fh:
            _ORIGINAL = json.load(fh)
    return _ORIGINAL


def pfade() -> dict:
    global _PFADE
    if _PFADE is None:
        _PFADE = dict(pfade_original())
    return _PFADE


def uebersteuern(tausch: dict) -> None:
    """Austausch {Symbolname: Katalogname} anwenden (Ansicht ▸ Symbol austauschen); leere Zuordnung stellt alles zurück."""
    global _PFADE
    _PFADE = dict(pfade_original())
    kat = katalog()
    for alt, neu in (tausch or {}).items():
        if alt in _PFADE and neu in kat:
            _PFADE[alt] = kat[neu]
    leeren()


_KATALOG: dict | None = None


def katalog() -> dict:
    """Alle 1800 Lucide-Symbole (Name → 24×24-Pfad) — für Piktogramm einfügen und Symbol austauschen."""
    global _KATALOG
    if _KATALOG is None:
        with open(os.path.join(_HIER, "..", "resources", "symbolkatalog.json"), encoding="utf-8") as fh:
            _KATALOG = json.load(fh)
    return _KATALOG


def katalog_bild(name: str, px: int = 96, farbe: str = "#1f2328", strich: float = 1.7) -> QImage:
    img = QImage(px, px, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    d = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{farbe}" stroke-width="{strich}" '
         f'stroke-linecap="round" stroke-linejoin="round"><path d="{katalog()[name]}"/></svg>').encode()
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(d)).render(p, QRectF(0, 0, px, px))
    p.end()
    return img


def hat(name: str) -> bool:
    return name in pfade()


def _svg(pfad: str, farbe: str) -> bytes:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{farbe}" '
            f'stroke-width="{STRICH}" stroke-linecap="round" stroke-linejoin="round"><path d="{pfad}"/></svg>').encode()


def _pixmap(name: str, farbe: str, px: int) -> QPixmap:
    key = (name, farbe, px)
    if key in _CACHE:
        return _CACHE[key]
    ratio = 2
    img = QImage(px * ratio, px * ratio, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    r = QSvgRenderer(QByteArray(_svg(pfade()[name], farbe)))
    p = QPainter(img)
    r.render(p, QRectF(0, 0, px * ratio, px * ratio))
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(ratio)
    _CACHE[key] = pm
    return pm


def icon(name: str, px: int = 20) -> QIcon:
    px = max(10, int(round(px * FAKTOR)))
    """Symbol in den Farben der aktuellen Palette (hell/dunkel), ausgegraut wenn deaktiviert."""
    if not hat(name):
        return QIcon()
    pal = QApplication.palette()
    normal = pal.color(QPalette.ButtonText).name()
    off = pal.color(QPalette.Disabled, QPalette.ButtonText).name()
    ic = QIcon()
    ic.addPixmap(_pixmap(name, normal, px), QIcon.Normal)
    ic.addPixmap(_pixmap(name, off, px), QIcon.Disabled)
    return ic


def leeren() -> None:
    _CACHE.clear()
