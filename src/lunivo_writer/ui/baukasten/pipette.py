"""Die Pipette: eine Farbe vom Bildschirm aufnehmen.

    c = farbe_vom_bildschirm(parent)      # QColor oder None (abgebrochen, Zeit abgelaufen, oder der Bildschirm lässt sich nicht aufnehmen)

Ein Bild des Bildschirms liegt in einem Fenster ohne Rand über dem Bildschirm; unter dem Mauszeiger zeigt eine Anzeige die Farbe, ein Klick nimmt sie auf.
Damit das Fenster nie hängen bleibt, hat es mehrere Sicherungen: Es bricht von selbst ab nach ``ZEIT_S`` Sekunden, bei Esc oder irgendeiner Taste, bei
Rechts- oder Mittelklick, beim Verlust des Fokus, wenn es nach einer halben Sekunde keinen Fokus bekommen hat (z. B. unter Wayland) und beim Beenden des
Programms. Unter Wayland lässt sich der Bildschirm nicht aufnehmen: dort tut die Pipette nichts.
"""
from __future__ import annotations

from PySide6.QtCore import QEventLoop, QPoint, QRect, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

ZEIT_S = 10                                     # nach so vielen Sekunden bricht die Pipette von selbst ab
AKTIV = True                                    # False: der Eintrag „Pipette“ erscheint in keiner Farbpalette (Schalter zum Abschalten)


class _Pipette(QWidget):
    fertig = Signal(object)

    def __init__(self, bild: QPixmap, geometrie: QRect):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool)
        self._bild = bild
        self._img = bild.toImage()
        self._offen = True
        self._rest = ZEIT_S
        self.setGeometry(geometrie)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setCursor(Qt.CrossCursor); self.setMouseTracking(True)
        self._pos = QPoint(geometrie.width() // 2, geometrie.height() // 2)
        self._zeit = QTimer(self); self._zeit.timeout.connect(self._tick); self._zeit.start(1000)       # Sicherung: Abbruch nach ZEIT_S
        QTimer.singleShot(500, self._fokus_pruefen)                                                       # Sicherung: ohne Eingabefokus sofort weg
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._zustand)
            app.aboutToQuit.connect(lambda: self._ende(None))

    # ---- Sicherungen
    def _tick(self) -> None:
        self._rest -= 1
        self.update()
        if self._rest <= 0:
            self._ende(None)

    def _fokus_pruefen(self) -> None:
        if self._offen and not (self.isActiveWindow() or self.hasFocus()):
            self._ende(None)

    def _zustand(self, zustand) -> None:
        if zustand != Qt.ApplicationActive:
            self._ende(None)

    def focusOutEvent(self, e):
        self._ende(None)

    def _ende(self, farbe) -> None:
        if not self._offen:
            return
        self._offen = False
        self._zeit.stop()
        self.releaseMouse(); self.releaseKeyboard()
        self.hide()
        self.fertig.emit(farbe)
        self.close()

    # ---- Anzeige und Eingabe
    def _farbe_bei(self, p: QPoint) -> QColor:
        f = self._bild.devicePixelRatio()
        x, y = int(p.x() * f), int(p.y() * f)
        return QColor(self._img.pixel(x, y)) if self._img.rect().contains(x, y) else QColor("#000000")

    def paintEvent(self, _e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._bild)
        c = self._farbe_bei(self._pos)
        r = QRect(self._pos.x() + 18, self._pos.y() + 18, 250, 66)
        p.setPen(QPen(QColor("#212529"), 1)); p.setBrush(QColor("#ffffff")); p.drawRect(r)
        p.setBrush(c); p.drawRect(QRect(r.left() + 6, r.top() + 6, 32, 32))
        p.setPen(QColor("#212529"))
        p.drawText(QRect(r.left() + 44, r.top() + 4, 200, 34), Qt.AlignVCenter, c.name().upper())
        p.drawText(QRect(r.left() + 6, r.top() + 40, 240, 22), Qt.AlignVCenter, f"Klick: aufnehmen · Esc oder Rechtsklick: abbrechen ({self._rest} s)")

    def mouseMoveEvent(self, e):
        self._pos = e.position().toPoint(); self.update()

    def mouseReleaseEvent(self, e):
        self._ende(self._farbe_bei(e.position().toPoint()) if e.button() == Qt.LeftButton else None)

    def keyPressEvent(self, e):                       # jede Taste bricht ab, nicht nur Esc
        self._ende(None)


def farbe_vom_bildschirm(parent=None) -> QColor | None:
    """Die Farbe unter dem nächsten Linksklick (blockiert höchstens ``ZEIT_S`` Sekunden); None bei Abbruch, Zeitablauf oder wenn der Bildschirm nicht aufnehmbar ist."""
    if QGuiApplication.platformName().startswith("wayland"):      # Wayland erlaubt keine Bildschirmaufnahme: nichts aufnehmen, nichts blockieren
        return None
    schirm = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
    bild = schirm.grabWindow(0)
    if bild.isNull():
        return None
    w = _Pipette(bild, schirm.geometry())
    erg: list = []
    schleife = QEventLoop()
    w.fertig.connect(lambda c: (erg.append(c), schleife.quit()))
    QTimer.singleShot((ZEIT_S + 2) * 1000, schleife.quit)         # letzte Sicherung: die Schleife endet in jedem Fall
    w.show(); w.activateWindow(); w.setFocus()
    schleife.exec()
    try:
        if w._offen:
            w._ende(None)
    except RuntimeError:                                           # schon geschlossen und gelöscht
        pass
    return erg[0] if erg else None
