"""Galerie-Popup: Kacheln mit einer Textprobe in der jeweiligen Schrift und dem Namen darunter (Formatvorlagen, später Tabellen-
und Formenstile), in Spalten, mit Rollbalken und Aktionen darunter.

Das Popup kennt seinen Aufrufer nicht. Es meldet nur den Schlüssel der gewählten Kachel (``gewaehlt``) und welche gerade unter
der Maus liegt (``ueberfahren`` / ``verlassen``, für die Live-Vorschau).
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QLabel, QMenu, QPushButton, QScrollArea, QVBoxLayout, QWidget, QWidgetAction


class _Kachel(QWidget):
    klick = Signal(str)
    darueber = Signal(str)
    weg = Signal()
    kontext = Signal(str, object)

    def __init__(self, schluessel: str, name: str, probe: str, schrift: QFont, farbe: str | None, groesse: QSize, aktuell: bool, tipp: str):
        super().__init__()
        self.schluessel, self.name, self.probe, self.farbe, self.aktuell = schluessel, name, probe, farbe, aktuell
        self.setFixedSize(groesse)
        f = QFont(schrift)                                         # die Probe wird so klein, dass sie in die Kachel passt
        while f.pointSizeF() > 8 and QFontMetrics(f).horizontalAdvance(probe) > groesse.width() - 14:
            f.setPointSizeF(f.pointSizeF() - 0.5)
        self.schrift = f
        self.setToolTip(tipp or name)
        self.setCursor(Qt.PointingHandCursor)
        self._ueber = False

    def enterEvent(self, e):
        self._ueber = True; self.update(); self.darueber.emit(self.schluessel)

    def leaveEvent(self, e):
        self._ueber = False; self.update(); self.weg.emit()

    def contextMenuEvent(self, e):
        self.kontext.emit(self.schluessel, e.globalPos())

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.klick.emit(self.schluessel)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self._ueber or self.aktuell:
            hell = QColor(self.palette().highlight().color()); hell.setAlpha(55 if self._ueber else 30)
            p.setPen(QPen(self.palette().highlight().color(), 1.4 if self.aktuell else 1)); p.setBrush(hell)
            p.drawRoundedRect(r, 4, 4)
        text = QColor(self.farbe) if self.farbe else self.palette().color(self.foregroundRole())
        p.setPen(text); p.setFont(self.schrift)
        proberect = QRectF(4, 4, self.width() - 8, self.height() - 24)
        p.drawText(proberect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine, QFontMetrics(self.schrift).elidedText(self.probe, Qt.ElideRight, int(proberect.width())))
        f = QFont(self.font()); f.setPointSizeF(8.5); p.setFont(f)
        p.setPen(self.palette().color(self.foregroundRole()))
        p.drawText(QRectF(2, self.height() - 20, self.width() - 4, 18), Qt.AlignCenter,
                   QFontMetrics(f).elidedText(self.name, Qt.ElideRight, self.width() - 8))
        p.end()


class GalerieAuswahl(QMenu):
    """Meldet den Schlüssel der gewählten Kachel."""

    gewaehlt = Signal(str)
    ueberfahren = Signal(str)
    verlassen = Signal()
    kontext = Signal(str, object)            # Rechtsklick auf eine Kachel: Schlüssel, Bildschirmposition

    def __init__(self, parent=None, *, titel: str = "", spalten: int = 4, kachel: QSize = QSize(78, 56), zeilen_sichtbar: int = 6):
        super().__init__(parent)
        self._spalten, self._kachel, self._zeilen = spalten, kachel, zeilen_sichtbar
        self._n = 0
        self.kacheln: dict[str, _Kachel] = {}
        wid = QWidget()
        self._v = QVBoxLayout(wid)
        self._v.setContentsMargins(6, 6, 6, 6); self._v.setSpacing(6)
        if titel:
            t = QLabel(titel); t.setStyleSheet("color: palette(mid); font-size: 11px; padding: 0 2px;")
            self._v.addWidget(t)
        halter = QWidget()
        self._gitter = QGridLayout(halter)
        self._gitter.setContentsMargins(0, 0, 0, 0); self._gitter.setSpacing(2); self._gitter.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._rolle = QScrollArea(); self._rolle.setWidget(halter); self._rolle.setWidgetResizable(True)
        self._rolle.setFrameShape(QFrame.NoFrame)
        self._rolle.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._rolle.setFixedWidth(spalten * (kachel.width() + 2) + 18)
        self._rolle.setFixedHeight(zeilen_sichtbar * (kachel.height() + 2))
        self._v.addWidget(self._rolle)
        self._trenner = None
        a = QWidgetAction(self); a.setDefaultWidget(wid); self.addAction(a)

    def kachel(self, schluessel: str, name: str, schrift: QFont, *, probe: str = "AaBbCcD", farbe: str | None = None,
               aktuell: bool = False, tipp: str = "") -> None:
        k = _Kachel(schluessel, name, probe, schrift, farbe, self._kachel, aktuell, tipp)
        k.klick.connect(lambda s: (self.gewaehlt.emit(s), self.close()))
        k.darueber.connect(self.ueberfahren.emit); k.weg.connect(self.verlassen.emit); k.kontext.connect(self.kontext.emit)
        self._gitter.addWidget(k, self._n // self._spalten, self._n % self._spalten)
        self._n += 1
        zeilen = min(self._zeilen, -(-self._n // self._spalten))
        self._rolle.setFixedHeight(zeilen * (self._kachel.height() + 2) + 4)
        self.kacheln[schluessel] = k

    def aktion(self, text: str, fn: Callable, symbol: QIcon | None = None, *, haken: bool | None = None, aktiv: bool = True) -> QPushButton:
        """Zeile unter der Galerie (z. B. „Neue Formatvorlage …“); schließt das Popup und ruft ``fn``.
        ``haken`` (True/False) macht daraus einen Schalter mit Haken vorn; ``fn`` bekommt dann den neuen Zustand."""
        if self._trenner is None:
            self._trenner = QFrame(); self._trenner.setFrameShape(QFrame.HLine); self._trenner.setFrameShadow(QFrame.Sunken)
            self._v.addWidget(self._trenner)
        b = QPushButton(text); b.setFlat(True); b.setEnabled(aktiv)
        b.setStyleSheet("QPushButton { text-align: left; padding: 6px 8px; border: none; border-radius: 4px; }"
                        "QPushButton:hover:enabled { background: palette(midlight); }")
        b.setIconSize(QSize(18, 18))
        if haken is not None:
            b.setCheckable(True); b.setChecked(haken)
            haken_symbol = self._haken_symbol()
            leer = QPixmap(18, 18); leer.fill(Qt.transparent)
            zeige = lambda an: b.setIcon(haken_symbol if an else QIcon(leer))
            zeige(haken); b.toggled.connect(zeige)
            b.clicked.connect(lambda an: (self.verlassen.emit(), self.close(), fn(an)))
        else:
            if symbol is not None:
                b.setIcon(symbol)
            b.clicked.connect(lambda: (self.verlassen.emit(), self.close(), fn()))
        self._v.addWidget(b)
        return b

    @staticmethod
    def _haken_symbol() -> QIcon:
        pm = QPixmap(18, 18); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QApplication.palette().color(QPalette.WindowText), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawLine(3, 9, 7, 13); p.drawLine(7, 13, 15, 4)
        p.end()
        return QIcon(pm)
