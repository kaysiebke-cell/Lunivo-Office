"""Fenster in einem Fenster: Unterfenster öffnen sich als Seite im selben Fenster statt als neues Fenster darüber.

    host = FensterStapel(FormatvorlageDialog(...))     # das erste Fenster ist die unterste Seite
    host.exec()

Ein Unterfenster ruft ``zeige_unter(self, dialog, fertig)``. Liegt der Aufrufer in einem ``FensterStapel``, legt sich ``dialog`` als nächste Seite
darüber (oben „← Zurück“ und der Pfad der Fenster). „OK“ des Unterfensters ruft ``fertig()`` und kehrt zur vorigen Seite zurück, „Abbrechen“ oder „← Zurück“
kehrt ohne ``fertig`` zurück. Ohne ``FensterStapel`` öffnet sich ``dialog`` wie bisher mit ``exec()`` — die Fenster funktionieren also allein und im Stapel.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QStackedWidget, QToolButton, QVBoxLayout, QWidget


class FensterStapel(QDialog):
    GROESSE = QSize(830, 670)             # feste Größe des ganzen Stapels: das größte Unterfenster (Rahmen, Texteffekte, Absatz …) passt hinein, nichts springt

    def __init__(self, wurzel: QDialog, parent=None):
        super().__init__(parent)
        self.wurzel = wurzel
        self.setWindowTitle(wurzel.windowTitle())
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        self.kopf = QWidget(); kh = QHBoxLayout(self.kopf); kh.setContentsMargins(10, 6, 10, 6); kh.setSpacing(10)
        self.zurueck = QToolButton(); self.zurueck.setText("←  Zurück"); self.zurueck.setAutoRaise(True)
        self.zurueck.clicked.connect(self._zurueck)
        self.pfad = QLabel(); self.pfad.setStyleSheet("color: palette(mid);")
        kh.addWidget(self.zurueck); kh.addWidget(self.pfad, 1)
        v.addWidget(self.kopf)
        self.stapel = QStackedWidget(); v.addWidget(self.stapel, 1)
        from PySide6.QtGui import QGuiApplication
        schirm = QGuiApplication.primaryScreen().availableGeometry() if QGuiApplication.primaryScreen() else None
        gr = QSize(self.GROESSE)
        if schirm is not None:                                            # auf kleinen Bildschirmen nicht größer als der Bildschirm
            gr = QSize(min(gr.width(), schirm.width() - 40), min(gr.height(), schirm.height() - 60))
        self.resize(gr)
        self._seiten: list[tuple[QDialog, Callable | None, QSize]] = []
        self.oeffne(wurzel)

    # ---- Seiten
    def oeffne(self, d: QDialog, fertig: Callable | None = None) -> None:
        """Ein Fenster als oberste Seite einlegen; ``fertig()`` wird nach „OK“ gerufen."""
        vorher = self.size()
        d.setWindowFlags(Qt.Widget)
        d.setModal(False)
        self._seiten.append((d, fertig, vorher))
        self.stapel.addWidget(d); self.stapel.setCurrentWidget(d)
        d.show()
        d.finished.connect(lambda r, d=d: self._beendet(d, r))
        mind = d.minimumSizeHint()                                   # nur der wirkliche Mindestbedarf der Seite, nicht ihre Wunschgröße als einzelnes Fenster
        kopf = self.kopf.sizeHint().height()
        # Das Fenster hat von Anfang an eine feste Größe und wächst nur, wenn eine Seite wirklich mehr braucht; es schrumpft nie und springt nicht
        self.resize(max(self.width(), mind.width()), max(self.height(), mind.height() + kopf))
        self._kopf_neu()

    def _beendet(self, d: QDialog, ergebnis: int) -> None:
        i = next((k for k, s in enumerate(self._seiten) if s[0] is d), None)
        if i is None:
            return
        if i == 0:                                                       # die unterste Seite beendet das ganze Fenster
            self._seiten.clear()
            self.done(ergebnis)
            return
        _d, fertig, vorher = self._seiten.pop(i)
        self.stapel.removeWidget(d)
        d.deleteLater()
        self.stapel.setCurrentWidget(self._seiten[-1][0])
        self._kopf_neu()
        if ergebnis == QDialog.Accepted and fertig is not None:
            fertig()

    def _zurueck(self) -> None:
        if len(self._seiten) > 1:
            self._seiten[-1][0].reject()

    def _kopf_neu(self) -> None:
        self.zurueck.setVisible(len(self._seiten) > 1)
        self.pfad.setText("  ›  ".join(s[0].windowTitle() for s in self._seiten) if len(self._seiten) > 1 else "")
        self.kopf.setVisible(len(self._seiten) > 1)


def ausfuehren(d: QDialog) -> bool:
    """``d`` als oberstes Fenster eines Stapels zeigen und warten (wie ``d.exec()``): seine Unterfenster öffnen sich als Seiten im selben Fenster.
    → True nach „OK“. ``d`` bleibt danach lesbar (``d.werte()`` …); der Wirt hängt an ``d`` und lebt so lange wie dieses."""
    host = FensterStapel(d, d.parentWidget())
    d._stapel_wirt = host
    return host.exec() == QDialog.Accepted


def stapel_von(w: QWidget | None) -> FensterStapel | None:
    while w is not None:
        if isinstance(w, FensterStapel):
            return w
        w = w.parentWidget()
    return None


def zeige_unter(elter: QWidget, d: QDialog, fertig: Callable) -> None:
    """``d`` als Unterfenster von ``elter`` zeigen; ``fertig()`` läuft nach „OK“. Im ``FensterStapel`` als Seite, sonst als Fenster mit ``exec``."""
    host = stapel_von(elter)
    if host is not None:
        host.oeffne(d, fertig)
    elif d.exec():
        fertig()
