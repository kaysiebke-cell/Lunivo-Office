"""Die eine Farbpalette des Programms: Popup, Farbfeld für Dialoge und geteilter Knopf fürs Band.

Das Popup kennt seinen Aufrufer nicht — es meldet nur eine Farbe (oder ``None`` für „Keine Farbe“) und lässt den
Aufrufer damit tun, was er will: Schriftfarbe, Schattierung, Seitenfarbe, Rahmen, Füllung …
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QColorDialog, QGridLayout, QLabel, QMenu, QPushButton, QToolButton, QVBoxLayout, QWidget, QWidgetAction,
)

from lunivo_writer.ui.baukasten import farben as F


def weitere_farben(parent, start=None, titel: str = "Farbe") -> QColor | None:
    """„Weitere Farben …“: der Farbwähler des Systems. Gibt die Farbe zurück oder ``None`` bei Abbruch."""
    c = QColorDialog.getColor(QColor(start) if start else QColor(Qt.black), parent, titel)
    if not c.isValid():
        return None
    F.zuletzt_merken(c.name())
    return c


def farb_symbol(farbe: str | None, groesse: int = 14) -> QIcon:
    pm = QPixmap(groesse, groesse)
    pm.fill(QColor(farbe) if farbe else Qt.transparent)
    return QIcon(pm)


class _Kachel(QWidget):
    """Ein Farbfeld der Palette; meldet Überfahren und Klick an die Palette."""

    def __init__(self, palette: "FarbPalette", farbe: str, seite: int = 18):
        super().__init__()
        self._p, self.farbe, self._an = palette, farbe, False
        self.setFixedSize(seite, seite)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(farbe)

    def enterEvent(self, e):
        self._an = True; self.update(); self._p.ueberfahren.emit(QColor(self.farbe))

    def leaveEvent(self, e):
        self._an = False; self.update(); self._p.verlassen.emit()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self._p.waehle(QColor(self.farbe))

    def paintEvent(self, e):
        p = QPainter(self)
        r = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        p.fillRect(r, QColor(self.farbe))
        pal = self.palette()
        stift = QPen(pal.highlight().color() if self._an else pal.mid().color(), 2 if self._an else 1)
        p.setPen(stift); p.setBrush(Qt.NoBrush); p.drawRect(r)


class FarbPalette(QMenu):
    """Popup mit „Keine Farbe“, Themenfarben (Grundfarben + Abstufungen), Standardfarben, zuletzt Benutzten, „Weitere Farben …“."""

    gewaehlt = Signal(object)        # QColor — oder None für „Keine Farbe“
    ueberfahren = Signal(object)     # QColor unter der Maus (für Live-Vorschau)
    verlassen = Signal()

    def __init__(self, parent=None, *, keine_text: str | None = "Keine Farbe", start=None, titel: str = "Farbe",
                 zuletzt: bool = True, weitere: bool = True):
        super().__init__(parent)
        self._start, self._titel = start, titel
        wid = QWidget()
        v = QVBoxLayout(wid)
        v.setContentsMargins(6, 6, 6, 6); v.setSpacing(4)
        if keine_text:
            keine = QPushButton(keine_text); keine.setFlat(True); keine.setStyleSheet("text-align: left; padding: 4px 6px;")
            keine.setIcon(self._keine_symbol()); keine.clicked.connect(lambda: self.waehle(None))
            v.addWidget(keine)
        v.addWidget(self._titel_zeile("Themenfarben"))
        v.addLayout(self._raster(F.thema_raster()))
        v.addWidget(self._titel_zeile("Standardfarben"))
        v.addLayout(self._raster([list(F.STANDARD_FARBEN)]))
        letzte = F.zuletzt_laden() if zuletzt else []
        if letzte:
            v.addWidget(self._titel_zeile("Zuletzt benutzt"))
            v.addLayout(self._raster([letzte]))
        if weitere:
            mehr = QPushButton("Weitere Farben …"); mehr.setFlat(True); mehr.setStyleSheet("text-align: left; padding: 4px 6px;")
            mehr.clicked.connect(self._weitere)
            v.addWidget(mehr)
        a = QWidgetAction(self)
        a.setDefaultWidget(wid)
        self.addAction(a)

    @staticmethod
    def _titel_zeile(text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("color: palette(mid); font-size: 11px; padding-top: 2px;")
        return l

    @staticmethod
    def _keine_symbol() -> QIcon:
        pm = QPixmap(14, 14); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setPen(QPen(QColor("#c92a2a"), 1.5)); p.drawRect(1, 1, 11, 11); p.drawLine(1, 12, 12, 1); p.end()
        return QIcon(pm)

    def _raster(self, zeilen: list[list[str]]) -> QGridLayout:
        g = QGridLayout()
        g.setSpacing(2); g.setContentsMargins(0, 0, 0, 0)
        g.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        for z, zeile in enumerate(zeilen):
            for s, farbe in enumerate(zeile):
                g.addWidget(_Kachel(self, farbe), z, s)
        return g

    def waehle(self, farbe: QColor | None) -> None:
        """Farbe übernehmen: merken, melden, Popup schließen."""
        if farbe is not None:
            F.zuletzt_merken(farbe.name())
        self.gewaehlt.emit(farbe)
        self.close()

    def _weitere(self) -> None:
        self.close()
        c = weitere_farben(self.parentWidget(), self._start, self._titel)
        if c is not None:
            self.gewaehlt.emit(c)


class FarbFeld(QPushButton):
    """Knopf für Dialoge, der seine Farbe zeigt; ein Klick öffnet die Palette. ``farbe`` ist ein Hex-Text ('' = keine)."""

    farbeGeaendert = Signal(str)

    def __init__(self, farbe: str = "#000000", titel: str = "Farbe", keine_text: str | None = None, parent=None):
        super().__init__(parent)
        self.farbe, self.titel, self.keine_text = farbe, titel, keine_text
        self.clicked.connect(self._waehle)
        self._zeige()

    def setFarbe(self, farbe: str) -> None:
        self.farbe = farbe
        self._zeige()

    def _waehle(self) -> None:
        pal = FarbPalette(self, keine_text=self.keine_text, start=self.farbe or None, titel=self.titel)
        pal.gewaehlt.connect(self._uebernehmen)
        self._zeige_popup(pal)

    def _zeige_popup(self, pal: QMenu) -> None:
        pal.exec(self.mapToGlobal(QPoint(0, self.height())))

    def _uebernehmen(self, c: QColor | None) -> None:
        self.farbe = c.name() if c is not None else ""
        self._zeige()
        self.farbeGeaendert.emit(self.farbe)

    def _zeige(self) -> None:
        if not self.farbe:
            self.setText(self.keine_text or "Keine"); self.setStyleSheet("")
            return
        self.setText(self.farbe)
        hell = QColor(self.farbe).lightness() >= 140
        self.setStyleSheet(f"QPushButton {{ background: {self.farbe}; color: {'black' if hell else 'white'}; }}")


class FarbKnopf(QToolButton):
    """Geteilter Knopf fürs Band: Klick auf das Symbol wendet die letzte Farbe an, der Pfeil klappt die Palette auf."""

    angewendet = Signal(object)      # QColor oder None

    def __init__(self, symbol: QIcon | None = None, text: str = "", farbe: str = "#c92a2a", *, keine_text: str | None = "Keine Farbe",
                 titel: str = "Farbe", parent=None):
        super().__init__(parent)
        self._symbol, self.farbe, self._titel, self._keine = symbol, farbe, titel, keine_text
        self.setText(text); self.setToolTip(text or titel)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly if symbol else Qt.ToolButtonTextOnly)
        self.setIconSize(QSize(22, 22))
        self.clicked.connect(lambda: self.angewendet.emit(QColor(self.farbe)))
        self.menu_neu()
        self._balken()

    def menu_neu(self) -> None:
        pal = FarbPalette(self, keine_text=self._keine, start=self.farbe, titel=self._titel)
        pal.gewaehlt.connect(self._gewaehlt)
        self.setMenu(pal)
        self._palette = pal

    def _gewaehlt(self, c: QColor | None) -> None:
        if c is not None:
            self.farbe = c.name(); self._balken()
        self.angewendet.emit(c)
        self.menu_neu()                                   # „Zuletzt benutzt“ aktualisieren

    def _balken(self) -> None:
        if self._symbol is None:
            return
        pm = self._symbol.pixmap(22, 22)
        p = QPainter(pm); p.fillRect(2, pm.height() - 5, pm.width() - 4, 4, QColor(self.farbe)); p.end()
        self.setIcon(QIcon(pm))
