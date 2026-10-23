"""Effekte für Bilder und Formen, die Lunivo selbst zeichnet: Schatten, Reflektion (Spiegelung), Leuchten und Weiche Kanten.

Die Werte stehen am Bild als ``fx`` (siehe ``VORGABE``); Längen in Punkt, Prozentwerte 0…100. ``unter_zeichnen`` malt Leuchten, Schatten und
Reflektion hinter das Bild, ``weiche_kanten`` liefert das Bild mit ausgeblendetem Rand. Beides arbeitet auf Bilddaten (Qt kennt diese Effekte
nicht); die Ergebnisse werden zwischengemerkt, damit das Blatt beim Rollen nicht jedes Mal neu rechnet.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath

from lunivo_writer.core.farben import Farbe
PX_PT = 96.0 / 72.0
# Dieselben Schlüssel wie bei den Texteffekten (editor/textfx.py), damit Voreinstellungen und Regler gemeinsam genutzt werden
VORGABE = {"schatten": {"farbe": Farbe.SCHWARZ, "transparenz": 60, "groesse": 100, "weich": 4.0, "abstand": 4.0, "winkel": 45},
           "reflektion": {"groesse": 50, "transparenz": 50, "weich": 0.5, "abstand": 0.0},
           "leuchten": {"farbe": Farbe.BLAU, "groesse": 8.0, "transparenz": 60},
           "weich": {"radius": 6.0}}
_MERK: dict = {}


def _merken(schluessel, bauen):
    if schluessel not in _MERK:
        if len(_MERK) > 48:
            _MERK.pop(next(iter(_MERK)))
        _MERK[schluessel] = bauen()
    return _MERK[schluessel]


def _maske(bild: QImage, groesse: tuple[int, int], ellipse: bool) -> QImage:
    """Die Form des Bildes (Alpha) in der gewünschten Größe: das Bild selbst, in einer Ellipse beschnitten, wenn ``ellipse``."""
    w, h = groesse
    out = QImage(w, h, QImage.Format_ARGB32_Premultiplied); out.fill(Qt.transparent)
    p = QPainter(out); p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform)
    if ellipse:
        pf = QPainterPath(); pf.addEllipse(QRectF(0, 0, w, h)); p.setClipPath(pf)
    p.drawImage(QRectF(0, 0, w, h), bild)
    p.end()
    return out


def _getoent(maske: QImage, farbe: QColor) -> QImage:
    out = QImage(maske)
    p = QPainter(out); p.setCompositionMode(QPainter.CompositionMode_SourceIn); p.fillRect(out.rect(), farbe); p.end()
    return out


def _weich(img: QImage, radius: float) -> QImage:
    """Weichzeichnen durch Verkleinern und Vergrößern (billig und gleichmäßig); der Rand muss vorher frei sein."""
    if radius < 1.0:
        return img
    f = max(2, int(radius))
    klein = img.scaled(max(1, img.width() // f), max(1, img.height() // f), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    klein = klein.scaled(max(1, klein.width() // 2 + 1), max(1, klein.height() // 2 + 1), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return klein.scaled(img.width(), img.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def weiche_kanten(bild: QImage, r: QRectF, ellipse: bool, radius_pt: float) -> QImage:
    """Das Bild mit weich auslaufendem Rand (Alpha nimmt zum Rand hin ab), in der Größe ``r``."""
    w, h = max(1, int(r.width())), max(1, int(r.height()))
    rad = radius_pt * PX_PT

    def bauen():
        m = _maske(bild, (w, h), ellipse)
        pad = int(rad * 2) + 2
        gross = QImage(w + 2 * pad, h + 2 * pad, QImage.Format_ARGB32_Premultiplied); gross.fill(Qt.transparent)
        p = QPainter(gross); p.drawImage(pad, pad, _getoent(m, QColor("white")).scaled(w, h)); p.end()      # die Form als weiße Fläche
        innen = QImage(gross.size(), QImage.Format_ARGB32_Premultiplied); innen.fill(Qt.transparent)
        q = QPainter(innen); q.drawImage(0, 0, gross); q.end()
        # Form verkleinern (Rand wegnehmen), dann weichzeichnen → Maske, die zum Rand hin ausläuft
        schmal = QImage(gross.size(), QImage.Format_ARGB32_Premultiplied); schmal.fill(Qt.transparent)
        q = QPainter(schmal); q.setRenderHint(QPainter.SmoothPixmapTransform)
        q.drawImage(QRectF(pad + rad, pad + rad, max(1.0, w - 2 * rad), max(1.0, h - 2 * rad)), _getoent(m, QColor("white")))
        q.end()
        weich = _weich(schmal, rad)
        out = QImage(w, h, QImage.Format_ARGB32_Premultiplied); out.fill(Qt.transparent)
        p = QPainter(out); p.setRenderHint(QPainter.SmoothPixmapTransform); p.drawImage(0, 0, m)
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn); p.drawImage(0, 0, weich.copy(pad, pad, w, h)); p.end()
        return out
    return _merken(("weich", id(bild), w, h, ellipse, round(radius_pt, 1)), bauen)


def _schatten_bild(bild: QImage, w: int, h: int, ellipse: bool, farbe: QColor, weich_px: float, faktor: float) -> tuple[QImage, int]:
    """(Bild des Schattens mit Rand ringsum, Randbreite): die getönte Form, um ``faktor`` skaliert und weichgezeichnet."""
    pad = int(weich_px * 2 + max(w, h) * max(0.0, faktor - 1.0) / 2) + 4
    m = _getoent(_maske(bild, (w, h), ellipse), farbe)
    gross = QImage(w + 2 * pad, h + 2 * pad, QImage.Format_ARGB32_Premultiplied); gross.fill(Qt.transparent)
    p = QPainter(gross); p.setRenderHint(QPainter.SmoothPixmapTransform)
    sw, sh = w * faktor, h * faktor
    p.drawImage(QRectF(pad + (w - sw) / 2, pad + (h - sh) / 2, sw, sh), m); p.end()
    return _weich(gross, weich_px), pad


def unter_zeichnen(p: QPainter, bild: QImage, r: QRectF, ellipse: bool, fx: dict) -> None:
    """Leuchten, Schatten und Reflektion hinter dem Bild (in der Reihenfolge der Schichten: Leuchten zuerst)."""
    w, h = max(1, int(r.width())), max(1, int(r.height()))
    p.save(); p.setRenderHint(QPainter.SmoothPixmapTransform)
    leu = fx.get("leuchten")
    if leu:
        c = QColor(leu.get("farbe", Farbe.BLAU)); c.setAlphaF(max(0.0, min(1.0, 1 - leu.get("transparenz", 60) / 100)))
        rad = float(leu.get("groesse", 8.0)) * PX_PT
        faktor = 1.0 + 2 * rad / max(w, h)

        def bauen_l():
            return _schatten_bild(bild, w, h, ellipse, c, rad * 0.9, faktor)
        img, pad = _merken(("leuchten", id(bild), w, h, ellipse, c.name(QColor.HexArgb), round(rad, 1)), bauen_l)
        from PySide6.QtCore import QPointF
        p.drawImage(QPointF(r.left() - pad, r.top() - pad), img)
    sch = fx.get("schatten")
    if sch:
        c = QColor(sch.get("farbe", Farbe.SCHWARZ)); c.setAlphaF(max(0.0, min(1.0, 1 - sch.get("transparenz", 60) / 100)))
        weich = float(sch.get("weich", 4.0)) * PX_PT
        faktor = max(0.2, sch.get("groesse", 100) / 100.0)

        def bauen_s():
            return _schatten_bild(bild, w, h, ellipse, c, weich, faktor)
        img, pad = _merken(("schatten", id(bild), w, h, ellipse, c.name(QColor.HexArgb), round(weich, 1), round(faktor, 2)), bauen_s)
        a = math.radians(float(sch.get("winkel", 45)))
        d = float(sch.get("abstand", 4.0)) * PX_PT
        from PySide6.QtCore import QPointF
        p.drawImage(QPointF(r.left() - pad + math.cos(a) * d, r.top() - pad + math.sin(a) * d), img)
    refl = fx.get("reflektion")
    if refl:
        hoehe = max(1, int(h * refl.get("groesse", 50) / 100.0))
        abst = float(refl.get("abstand", 0.0)) * PX_PT
        alpha0 = max(0.0, min(1.0, 1 - refl.get("transparenz", 50) / 100))

        def bauen_r():
            m = _maske(bild, (w, h), ellipse).mirrored(False, True).copy(0, 0, w, hoehe)     # gespiegelt, nur der obere Streifen
            out = QImage(w, hoehe, QImage.Format_ARGB32_Premultiplied); out.fill(Qt.transparent)
            q = QPainter(out); q.drawImage(0, 0, m)
            q.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            g = QLinearGradient(0, 0, 0, hoehe); g.setColorAt(0, QColor(0, 0, 0, int(255 * alpha0))); g.setColorAt(1, QColor(0, 0, 0, 0))
            q.fillRect(out.rect(), g); q.end()
            return out
        img = _merken(("refl", id(bild), w, h, ellipse, hoehe, round(alpha0, 2)), bauen_r)
        from PySide6.QtCore import QPointF
        p.drawImage(QPointF(r.left(), r.bottom() + abst), img)
    p.restore()
