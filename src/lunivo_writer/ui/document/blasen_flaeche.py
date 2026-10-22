"""Die Fläche neben der Seite, auf der die Sprechblasen des Editors stehen (Kommentare, verfolgte Änderungen)."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from lunivo_writer.editor import sprechblasen as SB


class BlasenFlaeche(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.ed = editor
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)
        self._treffer: list[tuple[QRectF, SB.Blase]] = []

    def grundfarbe(self) -> QColor:
        """Der Grund der Fläche ist derselbe wie rund um das Blatt (der Hintergrund des Dokumentfensters) — der Streifen ist also nicht zu sehen, nur die Blasen darauf."""
        from PySide6.QtGui import QGuiApplication, QPalette
        halter = self.ed.parentWidget()
        if halter is not None:
            return halter.palette().color(halter.backgroundRole())
        return QGuiApplication.palette().color(QPalette.Dark)

    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), self.grundfarbe())
        self._treffer = []
        layout = self.ed.blasen_layout(self.width())
        if not layout:
            p.end()
            return
        font = QFont(self.ed.font())
        font.setPixelSize(max(7, int(SB.blasen_px(self.ed.opt_text("kommentare/schrift", "mittel")) * self.ed.zoom)))
        rechts = self.ed.blasen_rand() == "Rechts"
        for bl, r, y_text in layout:
            if r.bottom() < e.rect().top() - 4 or r.top() > e.rect().bottom() + 4:
                self._treffer.append((r, bl))
                continue
            if self.ed.blasen_linien():
                SB.verbindung(p, bl, 0 if rechts else self.width(), y_text, r, rechts)
            SB.zeichnen(p, bl, r, font)
            self._treffer.append((r, bl))
        p.end()

    def _blase_bei(self, pos: QPointF):
        for r, bl in self._treffer:
            if r.contains(pos):
                return bl
        return None

    def mousePressEvent(self, e) -> None:
        for r, bl in self._treffer:
            if bl.kid is not None and r.contains(e.position()) and SB.menue_rect(r).contains(e.position()):
                self._menue(bl, e.globalPosition().toPoint())          # das Zeichen „☰“: Bearbeiten, Gelöst, Löschen
                return
        bl = self._blase_bei(e.position())
        if bl is not None:
            self.ed.select_range(bl.von, bl.bis)
            self.ed.setFocus()

    def _menue(self, bl, pos) -> None:
        from PySide6.QtWidgets import QMenu
        k = self.ed.kommentare.get(bl.kid, {})
        geloest = bool(k.get("geloest"))
        m = QMenu(self)
        m.addAction("Bearbeiten", lambda: self.ed.kommentar_bearbeiten(bl.kid))
        m.addAction("Wieder öffnen" if geloest else "Als gelöst markieren", lambda: self.ed.kommentar_geloest(bl.kid, not geloest))
        m.addSeparator()
        m.addAction("Löschen", lambda: self.ed.kommentar_loeschen(bl.kid))
        m.exec(pos)

    def mouseDoubleClickEvent(self, e) -> None:
        bl = self._blase_bei(e.position())
        if bl is not None and bl.kid is not None:
            self.ed.kommentar_bearbeiten(bl.kid)
