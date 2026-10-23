"""Grundgerüst für kleine Dialoge: Formular, optionale Vorschau, OK/Abbrechen und Zusatzknöpfe wie „Entfernen“."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPalette, QPen
from PySide6.QtWidgets import QApplication, QDialog, QFormLayout, QHBoxLayout, QLayout, QPushButton, QVBoxLayout, QWidget, QWidgetItem



class _KnopfLayout(QLayout):
    """Zusatzknöpfe links, „Abbrechen“ und „OK“ rechts — in einer Zeile, wenn sie nebeneinander passen; sonst stehen die Zusatzknöpfe (umbrechend) darüber."""
    KNOPF_B, ABSTAND, ZEILE_H = 120, 10, 34

    def __init__(self):
        super().__init__()
        self._extras: list = []
        self._haupt: list = []

    def extra(self, widget) -> None:
        self.addChildWidget(widget); self._extras.append(QWidgetItem(widget)); self.invalidate()

    def haupt(self, widget) -> None:
        self.addChildWidget(widget); self._haupt.append(QWidgetItem(widget)); self.invalidate()

    def addItem(self, item) -> None:
        self._extras.append(item)

    def count(self) -> int:
        return len(self._extras) + len(self._haupt)

    def itemAt(self, i: int):
        alle = self._extras + self._haupt
        return alle[i] if 0 <= i < len(alle) else None

    def takeAt(self, i: int):
        alle = self._extras + self._haupt
        if not 0 <= i < len(alle):
            return None
        it = alle[i]
        (self._extras if it in self._extras else self._haupt).remove(it)
        return it

    def hasHeightForWidth(self) -> bool:
        return True

    def sizeHint(self) -> QSize:
        return QSize(self.minimumSize().width(), self.heightForWidth(10000))

    def minimumSize(self) -> QSize:
        b = len(self._haupt) * self.KNOPF_B + max(0, len(self._haupt) - 1) * self.ABSTAND
        e = max((i.minimumSize().width() for i in self._extras), default=0)
        return QSize(max(b, e), self.ZEILE_H)

    def heightForWidth(self, w: int) -> int:
        return self._plan(w)[1]

    def setGeometry(self, r: QRect) -> None:
        super().setGeometry(r)
        for item, x, y, bw in self._plan(r.width())[0]:
            item.setGeometry(QRect(r.x() + x, r.y() + y, bw, self.ZEILE_H))

    def _plan(self, w: int):
        a = self.ABSTAND
        breiten = [max(i.sizeHint().width(), i.minimumSize().width()) for i in self._extras]
        eb = sum(breiten) + a * max(0, len(breiten) - 1)
        hb = len(self._haupt) * self.KNOPF_B + max(0, len(self._haupt) - 1) * a
        out, y = [], 0
        if self._extras and eb + a + hb > w:                              # zu eng für eine Zeile: Zusatzknöpfe oben, umbrechend
            x = 0
            for it, bw in zip(self._extras, breiten):
                if x > 0 and x + bw > w:
                    x = 0; y += self.ZEILE_H + a
                out.append((it, x, y, min(bw, w))); x += bw + a
            y += self.ZEILE_H + a
            hoehe = y + self.ZEILE_H
        else:
            x = 0
            for it, bw in zip(self._extras, breiten):
                out.append((it, x, 0, bw)); x += bw + a
            hoehe = self.ZEILE_H
        x = w - hb
        for it in self._haupt:
            out.append((it, max(0, x), y, self.KNOPF_B)); x += self.KNOPF_B + a
        return out, hoehe


class Knopfzeile(QWidget):
    """Die Knopfzeile unten in jedem Fenster — der einzige Ort, der sie baut: links Zusatzknöpfe, rechts „Abbrechen“ und „OK“ (gleich breit).
    Passen alle nebeneinander, stehen sie in einer Zeile; sonst rücken die Zusatzknöpfe in eine Zeile darüber.
    ``nur_ok`` lässt „Abbrechen“ weg, ``schliessen`` macht aus dem einen Knopf „Schließen“."""

    def __init__(self, dialog: QDialog, *links: QPushButton, bei_ok: Callable | None = None, ok_text: str = "OK",
                 abbrechen_text: str = "Abbrechen", nur_ok: bool = False, schliessen: bool = False):
        super().__init__()
        self.dialog = dialog
        self.zeile = _KnopfLayout(); self.setLayout(self.zeile)
        self.zeile.setProperty("schmal_nein", True)                          # ein fertiger Baustein: der Notbehelf `schmal_machen` darf ihn nicht umbauen
        for k in links:
            self.zusatz_knopf(k)
        if schliessen:
            ok_text, nur_ok, bei_ok = "Schließen", True, dialog.reject
        self.abbrechen, self.ok = QPushButton(abbrechen_text), QPushButton(ok_text)
        self.ok.setDefault(True)
        self.abbrechen.setIcon(_symbol("kreuz")); self.ok.setIcon(_symbol("haken"))
        for k in (self.abbrechen, self.ok):                                  # wie in der Vorlage: breite Knöpfe mit Symbol
            k.setIconSize(QSize(16, 16))
        self.abbrechen.clicked.connect(dialog.reject); self.ok.clicked.connect(bei_ok or dialog.accept)
        if not nur_ok:
            self.zeile.haupt(self.abbrechen)
        self.zeile.haupt(self.ok)

    def zusatz_knopf(self, k: QPushButton) -> QPushButton:
        self.zeile.extra(k)
        return k

    def zusatz(self, text: str, aktion: Callable | None = None, *, schliesst: bool = True) -> QPushButton:
        """Knopf neben OK/Abbrechen (z. B. „Entfernen“); ``schliesst`` beendet das Fenster mit OK."""
        k = QPushButton(text)
        def klick():
            if aktion:
                aktion()
            if schliesst:
                self.dialog.accept()
        k.clicked.connect(klick)
        return self.zusatz_knopf(k)


def knopfzeile(dialog: QDialog, *links: QPushButton, **kw) -> Knopfzeile:
    """Eine Knopfzeile für ``dialog`` (zum Einsetzen in ein Layout); Wahlmöglichkeiten wie bei ``Knopfzeile``."""
    return Knopfzeile(dialog, *links, **kw)


def fussleiste(dialog: QDialog, layout, *links: QPushButton, bei_ok: Callable | None = None, ok_text: str = "OK",
               abbrechen_text: str = "Abbrechen", nur_ok: bool = False) -> QPushButton:
    """Knopfzeile unten ins ``layout`` setzen. Gibt den OK-Knopf zurück (``bei_ok`` ersetzt ``accept``, z. B. zum Prüfen vor dem Schließen)."""
    z = Knopfzeile(dialog, *links, bei_ok=bei_ok, ok_text=ok_text, abbrechen_text=abbrechen_text, nur_ok=nur_ok)
    layout.addWidget(z)
    return z.ok


def _symbol(art: str):
    """Das Symbol auf „Abbrechen“ (Kreuz) und „OK“ (Haken)."""
    from PySide6.QtGui import QColor, QIcon, QPixmap
    pm = QPixmap(16, 16); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    pal = QApplication.palette().color(QPalette.ButtonText)
    p.setPen(QPen(pal, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if art == "kreuz":
        p.drawLine(3, 3, 13, 13); p.drawLine(13, 3, 3, 13)
    else:
        p.drawLine(2, 9, 6, 13); p.drawLine(6, 13, 14, 3)
    p.end()
    return QIcon(pm)


class VorschauFlaeche(QWidget):
    """Weißes Blatt, auf das der Dialog mit ``zeichne(painter, rect)`` seine Vorschau malt."""

    def __init__(self, zeichne: Callable[[QPainter, QRect], None], hoehe: int = 120, flaeche: bool = True):
        """``flaeche=False``: kein weißes Feld mit Rand; ``zeichne`` malt direkt auf den Fensterhintergrund (z. B. ein einzelnes Blatt)."""
        super().__init__()
        self._zeichne = zeichne
        self._flaeche = flaeche
        self.setMinimumHeight(hoehe)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._flaeche:
            p.fillRect(self.rect(), Qt.white)
            p.setPen(self.palette().mid().color()); p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        self._zeichne(p, self.rect().adjusted(8, 8, -8, -8))


class DialogRahmen(QDialog):
    """Unterklassen füllen ``self.form`` (``zeile(...)``) und liefern ``ergebnis()``. Wer sich ändert, ruft ``aktualisieren()``."""

    def __init__(self, parent=None, titel: str = "", vorschau: Callable[[QPainter, QRect], None] | None = None):
        super().__init__(parent)
        self.setWindowTitle(titel)
        v = QVBoxLayout(self)
        self.form = QFormLayout()
        v.addLayout(self.form)
        self.vorschau = VorschauFlaeche(vorschau) if vorschau else None
        if self.vorschau:
            v.addWidget(self.vorschau)
        self.knoepfe = Knopfzeile(self)
        v.addWidget(self.knoepfe)

    def zeile(self, beschriftung: str, widget) -> None:
        self.form.addRow(beschriftung, widget)

    def zusatzknopf(self, text: str, aktion: Callable | None = None, *, schliesst: bool = True) -> QPushButton:
        """Knopf neben OK/Abbrechen (z. B. „Entfernen“); ``schliesst`` beendet den Dialog mit OK."""
        return self.knoepfe.zusatz(text, aktion, schliesst=schliesst)

    def aktualisieren(self, *_) -> None:
        if self.vorschau:
            self.vorschau.update()

    def ergebnis(self):
        raise NotImplementedError
