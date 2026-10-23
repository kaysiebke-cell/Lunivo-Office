"""„Weitere Farben …“: das Fenster „Farben“ mit den Karteireitern Standard, Benutzerdefiniert und Erweitert.

Eine Farbe, drei Wege dorthin — Kachelraster, Farbfläche mit Helligkeitsleiste, Farbring mit Dreieck — und darunter
Farbmodell und Zahlenfelder. Rechts OK und Abbrechen, darunter „Neu“ gegen „Aktuell“. Alle drei Reiter und die Felder
hängen an einem gemeinsamen ``Modell``; wer eine Farbe ändert, ändert sie für alle.

Der Aufrufer bekommt über ``weitere_farben()`` (farbpalette.py) eine ``QColor`` oder ``None`` zurück.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QObject, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush, QColor, QConicalGradient, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF,
)
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QStyle, QTabWidget, QVBoxLayout, QWidget,
)

MODELLE = ("RGB", "HSV", "HSL")


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.ui.baukasten.formular_gitter import AngepassteReiter
class Modell(QObject):
    """Die gewählte Farbe, als Farbton/Sättigung/Wert gehalten (der Farbton geht bei Grau nicht verloren)."""
    geaendert = Signal()
    modus_geaendert = Signal()

    def __init__(self, start: QColor):
        super().__init__()
        self.modus = "RGB"
        self.h, self.s, self.v = 0.0, 0.0, 0.0
        self.setze(start, melden=False)

    def farbe(self) -> QColor:
        return QColor.fromHsvF(min(self.h, 0.9999), self.s, self.v)

    def setze(self, c: QColor, melden: bool = True) -> None:
        c = QColor(c)
        h, s, v, _ = c.getHsvF()
        if h >= 0:
            self.h = h
        self.s, self.v = s, v
        if melden:
            self.geaendert.emit()

    def setze_hsv(self, h: float | None = None, s: float | None = None, v: float | None = None) -> None:
        if h is not None:
            self.h = min(max(h, 0.0), 0.9999)
        if s is not None:
            self.s = min(max(s, 0.0), 1.0)
        if v is not None:
            self.v = min(max(v, 0.0), 1.0)
        self.geaendert.emit()


# ------------------------------------------------------------------------------------------------ Standard
class _Kacheln(QWidget):
    """Rundes Kachelraster: Farbton quer, oben hell und blass, unten dunkel; ganz unten die Graustufen."""
    bestaetigt = Signal()
    SPALTEN, ZEILEN, ZELLE, LUECKE = 17, 16, 14, 1

    def __init__(self, modell: Modell):
        super().__init__()
        self.m = modell
        self.skaliere(self.ZELLE)
        self.m.geaendert.connect(self.update)
        self.setMouseTracking(False)

    def skaliere(self, zelle: int) -> None:
        """Die Kacheln in dieser Größe (Bildpunkte) neu legen: so groß, wie Breite und Höhe der Seitenleiste es zulassen."""
        self.ZELLE = zelle
        self.LUECKE = 1 if zelle < 18 else 2
        schritt = self.ZELLE + self.LUECKE
        self.setFixedSize(self.SPALTEN * schritt + self.LUECKE, (self.ZEILEN + 2) * schritt + 14)
        self.kacheln: list[tuple[QRectF, QColor]] = []
        for z in range(self.ZEILEN):
            for s in range(self.SPALTEN):
                hell = z < 8
                farbe = QColor.fromHsvF((s / self.SPALTEN), (z + 1) / 8 if hell else 1.0, 1.0 if hell else 1.0 - (z - 7) / 10)
                self.kacheln.append((self._feld(s, z), farbe))
        for i in range(12):                                        # Graustufen, weiß bis schwarz
            g = 1.0 - i / 11
            self.kacheln.append((self._feld(2 + i, self.ZEILEN + 0.6), QColor.fromHsvF(0, 0, g)))
        self.update()

    def _feld(self, s: float, z: float) -> QRectF:
        schritt = self.ZELLE + self.LUECKE
        return QRectF(self.LUECKE + s * schritt, self.LUECKE + z * schritt, self.ZELLE, self.ZELLE)

    def _bei(self, pos) -> QColor | None:
        for r, f in self.kacheln:
            if r.contains(pos):
                return f
        return None

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        jetzt = self.m.farbe().name()
        for r, f in self.kacheln:
            p.setPen(Qt.NoPen); p.setBrush(f)
            p.drawRoundedRect(r, 3, 3)
            if f.name() == jetzt:
                p.setBrush(Qt.NoBrush); p.setPen(QPen(self.palette().highlight().color(), 2))
                p.drawRoundedRect(r.adjusted(-1.5, -1.5, 1.5, 1.5), 5, 5)
        p.end()

    def mousePressEvent(self, e):
        f = self._bei(e.position())
        if f is not None:
            self.m.setze(f)

    def mouseDoubleClickEvent(self, e):
        if self._bei(e.position()) is not None:
            self.bestaetigt.emit()


# ------------------------------------------------------------------------------------------ Benutzerdefiniert
class _Flaeche(QWidget):
    """Farbton quer, Sättigung von oben (voll) nach unten (grau)."""
    def __init__(self, modell: Modell):
        super().__init__()
        self.m = modell
        self.setFixedSize(285, 215)
        self.bild = QImage(self.width(), self.height(), QImage.Format_RGB32)
        for y in range(self.height()):
            for x in range(self.width()):
                self.bild.setPixelColor(x, y, QColor.fromHsvF(x / self.width(), 1 - y / (self.height() - 1), 1.0))
        self.m.geaendert.connect(self.update)

    def setGroesse(self, b: int, h: int) -> None:
        """Größe ändern und das Farbbild neu rechnen."""
        self.setFixedSize(b, h)
        self.bild = QImage(b, h, QImage.Format_RGB32)
        for y in range(h):
            for x in range(b):
                self.bild.setPixelColor(x, y, QColor.fromHsvF(x / b, 1 - y / max(1, h - 1), 1.0))
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.drawImage(0, 0, self.bild)
        x, y = self.m.h * self.width(), (1 - self.m.s) * (self.height() - 1)
        p.setPen(QPen(Qt.white, 2)); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(x, y), 6, 6)
        p.setPen(QPen(Qt.black, 1)); p.drawEllipse(QPointF(x, y), 7.5, 7.5)
        p.end()

    def _setze(self, pos) -> None:
        self.m.setze_hsv(h=pos.x() / self.width(), s=1 - pos.y() / (self.height() - 1))

    def mousePressEvent(self, e): self._setze(e.position())
    def mouseMoveEvent(self, e): self._setze(e.position())


class _Leiste(QWidget):
    """Helligkeit (Wert): oben hell, unten dunkel, mit Pfeil am rechten Rand."""
    def __init__(self, modell: Modell):
        super().__init__()
        self.m = modell
        self.setFixedSize(26, 215)
        self.m.geaendert.connect(self.update)

    def paintEvent(self, _e):
        p = QPainter(self)
        balken = QRectF(0, 0, 16, self.height())
        g = QLinearGradient(0, 0, 0, self.height()); g.setColorAt(0, Qt.white); g.setColorAt(1, Qt.black)
        p.fillRect(balken, QBrush(g))
        y = (1 - self.m.v) * (self.height() - 1)
        pfeil = QPolygonF([QPointF(25, y - 5), QPointF(25, y + 5), QPointF(18, y)])
        p.setPen(Qt.NoPen); p.setBrush(self.palette().text()); p.drawPolygon(pfeil)
        p.end()

    def _setze(self, pos) -> None:
        self.m.setze_hsv(v=1 - pos.y() / (self.height() - 1))

    def mousePressEvent(self, e): self._setze(e.position())
    def mouseMoveEvent(self, e): self._setze(e.position())


# ------------------------------------------------------------------------------------------------ Erweitert
class _Ring(QWidget):
    """Farbring (Farbton) mit Dreieck (Sättigung und Wert). Das Dreieck dreht mit: Die reine Farbe zeigt auf ihren Farbton."""
    AUSSEN, INNEN = 112.0, 90.0

    def __init__(self, modell: Modell):
        super().__init__()
        self.m = modell
        self.setFixedSize(270, 250)
        self.mitte = QPointF(self.width() / 2, self.height() / 2)
        self._ziehen = None                                      # "ring" oder "dreieck"
        self.m.geaendert.connect(self.update)

    def skaliere(self, k: float) -> None:
        """Ring und Dreieck im Maßstab ``k`` (1,0 = 270 × 250 Bildpunkte)."""
        self.AUSSEN, self.INNEN = 112.0 * k, 90.0 * k
        self.setFixedSize(int(270 * k), int(250 * k))
        self.mitte = QPointF(self.width() / 2, self.height() / 2)
        self.update()

    def _ecken(self) -> tuple[QPointF, QPointF, QPointF]:
        r = self.INNEN - 4
        t0 = self.m.h * 2 * math.pi
        def punkt(t): return QPointF(self.mitte.x() + r * math.sin(t), self.mitte.y() - r * math.cos(t))
        return punkt(t0), punkt(t0 + 2 * math.pi / 3), punkt(t0 + 4 * math.pi / 3)     # Farbe, Weiß, Schwarz

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QConicalGradient(self.mitte, 90)
        for i in range(0, 361, 10):
            g.setColorAt(min(i / 360, 1.0), QColor.fromHsvF(((360 - i) % 360) / 360, 1, 1))
        ring = QPainterPath(); ring.addEllipse(self.mitte, self.AUSSEN, self.AUSSEN); ring.addEllipse(self.mitte, self.INNEN, self.INNEN)
        p.setPen(Qt.NoPen); p.fillPath(ring, QBrush(g))
        t = self.m.h * 2 * math.pi                               # Marke auf dem Ring
        mr = (self.AUSSEN + self.INNEN) / 2
        mp = QPointF(self.mitte.x() + mr * math.sin(t), self.mitte.y() - mr * math.cos(t))
        p.setBrush(Qt.NoBrush); p.setPen(QPen(Qt.white, 2.5)); p.drawEllipse(mp, 7, 7)
        p.setPen(QPen(Qt.black, 1)); p.drawEllipse(mp, 8.5, 8.5)
        # Dreieck: Punkt für Punkt gemischt (a Farbe, b Weiß, c Schwarz)
        fa, fw, fk = self._ecken()
        links, oben = int(min(fa.x(), fw.x(), fk.x())) - 1, int(min(fa.y(), fw.y(), fk.y())) - 1
        rechts, unten = int(max(fa.x(), fw.x(), fk.x())) + 2, int(max(fa.y(), fw.y(), fk.y())) + 2
        bild = QImage(rechts - links, unten - oben, QImage.Format_ARGB32); bild.fill(Qt.transparent)
        reine = QColor.fromHsvF(min(self.m.h, 0.9999), 1, 1)
        for y in range(bild.height()):
            for x in range(bild.width()):
                a, b, c = self._schwerpunkt(QPointF(x + links, y + oben), fa, fw, fk)
                if a >= -0.01 and b >= -0.01 and c >= -0.01:
                    def kanal(wert: float) -> int: return min(255, max(0, round(255 * wert)))
                    bild.setPixelColor(x, y, QColor(kanal(a * reine.redF() + b), kanal(a * reine.greenF() + b), kanal(a * reine.blueF() + b)))
        spitze = QPainterPath(); spitze.addPolygon(QPolygonF([fa, fw, fk])); spitze.closeSubpath()
        p.setClipPath(spitze); p.drawImage(links, oben, bild); p.setClipping(False)
        p.setBrush(Qt.NoBrush); p.setPen(QPen(self.palette().mid().color(), 1)); p.drawPath(spitze)
        a, b = self.m.s * self.m.v, self.m.v * (1 - self.m.s)                     # Marke im Dreieck
        pos = QPointF(a * fa.x() + b * fw.x() + (1 - a - b) * fk.x(), a * fa.y() + b * fw.y() + (1 - a - b) * fk.y())
        p.setPen(QPen(Qt.white, 2)); p.drawEllipse(pos, 5, 5)
        p.setPen(QPen(Qt.black, 1)); p.drawEllipse(pos, 6.5, 6.5)
        p.end()

    @staticmethod
    def _schwerpunkt(q: QPointF, a: QPointF, b: QPointF, c: QPointF) -> tuple[float, float, float]:
        d = (b.y() - c.y()) * (a.x() - c.x()) + (c.x() - b.x()) * (a.y() - c.y())
        u = ((b.y() - c.y()) * (q.x() - c.x()) + (c.x() - b.x()) * (q.y() - c.y())) / d
        v = ((c.y() - a.y()) * (q.x() - c.x()) + (a.x() - c.x()) * (q.y() - c.y())) / d
        return u, v, 1 - u - v

    def _wirke(self, pos) -> None:
        dx, dy = pos.x() - self.mitte.x(), pos.y() - self.mitte.y()
        if self._ziehen == "ring":
            self.m.setze_hsv(h=(math.atan2(dx, -dy) / (2 * math.pi)) % 1.0)
        elif self._ziehen == "dreieck":
            a, b, c = self._schwerpunkt(pos, *self._ecken())
            a, b, c = max(a, 0.0), max(b, 0.0), max(c, 0.0)
            summe = (a + b + c) or 1.0
            a, b = a / summe, b / summe
            v = a + b
            self.m.setze_hsv(s=(a / v) if v > 0 else self.m.s, v=v)

    def mousePressEvent(self, e):
        d = math.hypot(e.position().x() - self.mitte.x(), e.position().y() - self.mitte.y())
        self._ziehen = "ring" if self.INNEN - 2 <= d <= self.AUSSEN + 2 else "dreieck" if d < self.INNEN - 2 else None
        self._wirke(e.position())

    def mouseMoveEvent(self, e):
        self._wirke(e.position())

    def mouseReleaseEvent(self, _e):
        self._ziehen = None


# ----------------------------------------------------------------------------------------- Farbmodell und Felder
class _Regler(QWidget):
    """Farbmodell (RGB, HSV, HSL), drei Zahlenfelder und die Schreibweise #rrggbb — gleich in allen Karteireitern."""
    def __init__(self, modell: Modell):
        super().__init__()
        self.m = modell
        g = QGridLayout(self); g.setContentsMargins(0, 0, 0, 0); g.setVerticalSpacing(8)
        self.modell_wahl = QComboBox(); self.modell_wahl.addItems(MODELLE)
        g.addWidget(QLabel("Farbmodell"), 0, 0); g.addWidget(self.modell_wahl, 0, 1, 1, 2)       # Zeile 1: Farbmodell und Hex, Zeile 2: die drei Zahlenfelder nebeneinander
        self.namen = [QLabel() for _ in range(3)]
        self.felder = [QSpinBox() for _ in range(3)]
        for i, (n, f) in enumerate(zip(self.namen, self.felder)):
            g.addWidget(n, 1, 2 * i); g.addWidget(f, 1, 2 * i + 1)
            f.valueChanged.connect(self._tippen)
        self.hex = QLineEdit(); self.hex.setMaxLength(7); self.hex.setPlaceholderText("#rrggbb")
        g.addWidget(QLabel("Hex"), 0, 3); g.addWidget(self.hex, 0, 4, 1, 2)
        for c in (1, 3, 5):
            g.setColumnStretch(c, 1)
        self.modell_wahl.currentTextChanged.connect(self._modus)
        self.hex.editingFinished.connect(self._hex)
        self.m.geaendert.connect(self.auffrischen)
        self.m.modus_geaendert.connect(self._modus_zeigen)
        self._modus_zeigen()

    def _modus(self, text: str) -> None:
        if text != self.m.modus:
            self.m.modus = text
            self.m.modus_geaendert.emit()

    def _modus_zeigen(self) -> None:
        self.modell_wahl.blockSignals(True); self.modell_wahl.setCurrentText(self.m.modus); self.modell_wahl.blockSignals(False)
        namen = {"RGB": ("Rot", "Grün", "Blau"), "HSV": ("Farbton", "Sättigung", "Wert"), "HSL": ("Farbton", "Sättigung", "Helligkeit")}[self.m.modus]
        grenzen = {"RGB": ((0, 255),) * 3, "HSV": ((0, 359), (0, 100), (0, 100)), "HSL": ((0, 359), (0, 100), (0, 100))}[self.m.modus]
        for n, f, name, (lo, hi) in zip(self.namen, self.felder, namen, grenzen):
            n.setText(name); f.blockSignals(True); f.setRange(lo, hi); f.blockSignals(False)
        self.auffrischen()

    def werte(self) -> tuple[int, int, int]:
        c = self.m.farbe()
        if self.m.modus == "RGB":
            return c.red(), c.green(), c.blue()
        if self.m.modus == "HSV":
            return round(self.m.h * 359), round(self.m.s * 100), round(self.m.v * 100)
        h, s, l, _ = c.getHslF()
        return round((h if h >= 0 else self.m.h) * 359), round(s * 100), round(l * 100)

    def auffrischen(self) -> None:
        for f, w in zip(self.felder, self.werte()):
            f.blockSignals(True); f.setValue(w); f.blockSignals(False)
        self.hex.setText(self.m.farbe().name())

    def _tippen(self) -> None:
        a, b, c = (f.value() for f in self.felder)
        if self.m.modus == "RGB":
            self.m.setze(QColor(a, b, c))
        elif self.m.modus == "HSV":
            self.m.setze_hsv(h=a / 359 * 0.9999, s=b / 100, v=c / 100)
        else:
            self.m.setze(QColor.fromHslF(min(a / 359, 0.9999), b / 100, c / 100))

    def _hex(self) -> None:
        t = self.hex.text().strip()
        c = QColor(t if t.startswith("#") else "#" + t)
        if c.isValid():
            self.m.setze(c)
        else:
            self.auffrischen()


# ----------------------------------------------------------------------------------------------------- Fenster
class _Proben(QWidget):
    """Eine Fläche, oben „Neu“, unten „Aktuell“."""
    def __init__(self, modell: Modell, aktuell: QColor):
        super().__init__()
        self.m, self.alt = modell, QColor(aktuell)
        self.setFixedSize(72, 56)
        self.m.geaendert.connect(self.update)

    def paintEvent(self, _e):
        p = QPainter(self)
        h = self.height() // 2
        p.fillRect(0, 0, self.width(), h, self.m.farbe())
        p.fillRect(0, h, self.width(), self.height() - h, self.alt)
        p.setPen(QPen(self.palette().mid().color(), 1)); p.setBrush(Qt.NoBrush); p.drawRect(0, 0, self.width() - 1, self.height() - 1)
        p.end()


class FarbenDialog(PanelFaehig, QDialog):
    """Das Fenster „Farben“ (öffnet sich in der Seitenleiste). ``farbe()`` gibt nach OK die gewählte Farbe zurück."""

    def __init__(self, parent=None, start=None, titel: str = "Farben"):
        super().__init__(parent)
        self.setWindowTitle(titel if titel not in ("", "Farbe") else "Farben")
        ausgang = QColor(start) if start is not None and QColor(start).isValid() else QColor(Qt.black)
        self.m = Modell(ausgang)
        v = QVBoxLayout(self)
        self.reiter = AngepassteReiter()                                  # Standard braucht weniger Platz als Erweitert
        v.addWidget(self.reiter, 1)

        def seite(inhalt: QWidget, regler: bool) -> QWidget:
            w = QWidget(); sv = QVBoxLayout(w); sv.setContentsMargins(6, 8, 6, 6)
            sv.addWidget(inhalt, 0, Qt.AlignHCenter)
            if regler:
                sv.addWidget(_Regler(self.m))
            sv.addStretch(1)
            return w
        kacheln = self._kacheln = _Kacheln(self.m)
        kacheln.bestaetigt.connect(self.accept)
        flaeche = QWidget(); fh = QHBoxLayout(flaeche); fh.setContentsMargins(0, 0, 0, 0); fh.setSpacing(6)
        self._flaeche, self._leiste = _Flaeche(self.m), _Leiste(self.m)
        fh.addWidget(self._flaeche); fh.addWidget(self._leiste)
        self.reiter.addTab(seite(kacheln, False), "Standard")
        self.reiter.addTab(seite(flaeche, True), "Benutzerdefiniert")
        self._ring = _Ring(self.m)
        self.reiter.addTab(seite(self._ring, True), "Erweitert")
        # Neu und Aktuell: die Probe mit ihren Beschriftungen, mittig unter den Reitern
        probe = QHBoxLayout(); probe.setSpacing(8); probe.setContentsMargins(6, 0, 6, 0)
        probe.addStretch(1)                                                  # mittig unter den Farben
        probe.addWidget(_Proben(self.m, ausgang))
        namen = QVBoxLayout(); namen.addWidget(QLabel("Neu")); namen.addStretch(1); namen.addWidget(QLabel("Aktuell"))
        probe.addLayout(namen); probe.addStretch(1)
        v.addLayout(probe)
        v.addWidget(knopfzeile(self))

    def passe_an(self, breite: int, hoehe: int) -> None:
        """Das Standard-Raster so groß machen, wie die Seitenleiste Platz hat (Breite für 17 Spalten, Höhe für 18 Zeilen samt Reitern und Probe)."""
        k = self._kacheln
        zelle = min((breite - 24) // k.SPALTEN - 1, (hoehe - 190) // (k.ZEILEN + 2) - 1)
        k.skaliere(max(12, min(24, zelle)))
        h = max(150, min(340, hoehe - 235))                                         # Farbfläche und Leiste: die Höhe, die nach den zwei Reihen Felder und der Probe übrig bleibt
        self._leiste.setFixedHeight(h); self._flaeche.setGroesse(max(200, min(380, breite - 70)), h)
        self._ring.skaliere(max(0.7, min(1.5, (hoehe - 235) / 250, (breite - 24) / 270)))

    def farbe(self) -> QColor:
        return self.m.farbe()
