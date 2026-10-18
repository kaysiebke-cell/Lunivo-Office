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


def pfade() -> dict:
    global _PFADE
    if _PFADE is None:
        with open(os.path.join(_HIER, "..", "resources", "symbole.json"), encoding="utf-8") as fh:
            _PFADE = json.load(fh)
    return _PFADE


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
