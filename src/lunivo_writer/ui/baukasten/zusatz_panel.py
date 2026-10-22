"""Zusatzfenster in der Seitenleiste: ein Fenster (zum Beispiel „Nummerierung und Aufzählungszeichen“) öffnet sich nicht über dem Text, sondern als Seite
in der Seitenleiste — genau so lange, wie man die Einstellung bearbeitet, danach ist die Seitenleiste wieder wie vorher.

Die Breite der Seitenleiste ändert sich nie: der Inhalt bekommt einen Rollbereich ohne seitliche Leiste und passt sich an (``kompakt_machen()`` des Fensters,
falls vorhanden). Bedienung ohne Maus: der Fokus steht gleich im Fenster, Esc bricht ab, Tab läuft durch die Felder.

    seitenleiste.zusatz_ausfuehren(dialog)     # wie dialog.exec(): wartet, → True nach „OK“
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEventLoop, Qt
from PySide6.QtWidgets import QDialog, QFrame, QSizePolicy, QHBoxLayout, QLabel, QScrollArea, QStackedWidget, QToolButton, QVBoxLayout, QWidget


class ZusatzPanel(QWidget):
    """Die Seite in der Seitenleiste. Unterfenster (``zeige_unter``) legen sich als weitere Seite darüber, mit „← Zurück“."""
    ist_stapel = True

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)                 # der Inhalt bestimmt nie die Breite der Seitenleiste
        self.setMinimumWidth(0)
        self.verfuegbar = 360                                                          # Breite für den Inhalt in Pixeln (setzt die Seitenleiste)
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        kopf = QWidget(); h = QHBoxLayout(kopf); h.setContentsMargins(10, 8, 8, 8); h.setSpacing(4)
        self.zurueck = QToolButton(); self.zurueck.setText("←"); self.zurueck.setToolTip("Zurück"); self.zurueck.setAccessibleName("Zurück")
        self.zurueck.setAutoRaise(True); self.zurueck.setFixedSize(30, 30); self.zurueck.clicked.connect(self._zurueck)
        self.titel = QLabel(); self.titel.setWordWrap(True)
        f = self.titel.font(); f.setBold(True); f.setPointSizeF(f.pointSizeF() + 1); self.titel.setFont(f)
        zu = QToolButton(); zu.setText("✕"); zu.setToolTip("Schließen (Esc)"); zu.setAccessibleName("Schließen"); zu.setAutoRaise(True)
        zu.setFixedSize(30, 30); zu.clicked.connect(self._schliessen)
        h.addWidget(self.zurueck); h.addWidget(self.titel, 1); h.addWidget(zu)
        v.addWidget(kopf)
        linie = QFrame(); linie.setFrameShape(QFrame.HLine); linie.setFrameShadow(QFrame.Plain); linie.setStyleSheet("color: palette(midlight);")
        v.addWidget(linie)
        self.stapel = QStackedWidget(); v.addWidget(self.stapel, 1)
        self._seiten: list[tuple[QDialog, Callable | None]] = []

    # ---- Seiten
    def oeffne(self, d: QDialog, fertig: Callable | None = None) -> None:
        d.setWindowFlags(Qt.Widget); d.setModal(False)
        if hasattr(d, "kompakt_machen"):
            d.kompakt_machen()
        d.setMinimumSize(0, 0)
        from lunivo_writer.ui.baukasten.schmal import schmal_machen
        breite = self.verfuegbar
        for _ in range(6):                                                              # was nicht in die Breite der Seitenleiste passt, bricht um
            schmal_machen(d, breite)
            zuviel = d.minimumSizeHint().width() - self.verfuegbar - 12
            if zuviel <= 0:
                break
            breite -= max(24, zuviel)
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.NoFrame)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)                       # nie seitlich rollen: die Breite der Seitenleiste bleibt
        sa.setWidget(d)
        sa.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding); sa.setMinimumWidth(0)
        self._seiten.append((d, fertig))
        self.stapel.addWidget(sa); self.stapel.setCurrentWidget(sa)
        d.show()
        d.finished.connect(lambda r, d=d: self._beendet(d, r))
        self._kopf_neu()
        d.setFocus(Qt.OtherFocusReason)
        d.focusNextChild()

    def _beendet(self, d: QDialog, ergebnis: int) -> None:
        i = next((k for k, s in enumerate(self._seiten) if s[0] is d), None)
        if i is None or i == 0:
            return                                                                      # die unterste Seite beendet der Aufrufer (zusatz_ausfuehren)
        _d, fertig = self._seiten.pop(i)
        sa = d.parentWidget().parentWidget() if d.parentWidget() is not None else None
        self.stapel.setCurrentIndex(self.stapel.count() - 2 if self.stapel.count() > 1 else 0)
        for k in range(self.stapel.count()):
            w = self.stapel.widget(k)
            if isinstance(w, QScrollArea) and w.widget() is d:
                self.stapel.removeWidget(w); w.takeWidget(); w.deleteLater(); break
        d.deleteLater()
        self._kopf_neu()
        if ergebnis == QDialog.Accepted and fertig is not None:
            fertig()

    def _zurueck(self) -> None:
        if len(self._seiten) > 1:
            self._seiten[-1][0].reject()

    def _schliessen(self) -> None:
        if self._seiten:
            self._seiten[-1][0].reject()

    def _kopf_neu(self) -> None:
        self.zurueck.setVisible(len(self._seiten) > 1)
        self.titel.setText(self._seiten[-1][0].windowTitle() if self._seiten else "")
        self.setAccessibleName(self.titel.text())

    def raeumen(self) -> None:
        while self.stapel.count():
            w = self.stapel.widget(0)
            self.stapel.removeWidget(w)
            if isinstance(w, QScrollArea) and w.widget() is not None:
                w.takeWidget()
            w.deleteLater()
        self._seiten.clear()


def ausfuehren_in(seite: ZusatzPanel, d: QDialog, vorher: Callable, nachher: Callable) -> bool:
    """``d`` als unterste Seite von ``seite`` zeigen und warten (wie ``d.exec()``). ``vorher()`` zeigt die Seitenleiste, ``nachher()`` stellt sie zurück."""
    schleife = QEventLoop()
    ergebnis = []
    d.finished.connect(lambda r: (ergebnis.append(r), schleife.quit()))
    vorher()
    seite.oeffne(d)
    schleife.exec()
    seite.raeumen()
    d.setParent(None)
    nachher()
    return bool(ergebnis) and ergebnis[0] == QDialog.Accepted


def leiste_fuer(d: QDialog):
    """Die Seitenleiste, in der ``d`` sich zeigen soll — oder None (dann wie bisher als Fenster): Panels aus, kein Hauptfenster, oder ein anderes Fenster hält schon den Fokus."""
    from PySide6.QtWidgets import QApplication
    el = d.parentWidget()
    if el is None or QApplication.activeModalWidget() is not None:
        return None
    fenster = el.window()
    arbeit = getattr(fenster, "arbeit", None)
    if not fenster.isVisible() or (arbeit is not None and arbeit.isHidden()):         # zum Beispiel bei geöffneter Datei-Ansicht: die Seitenleiste wäre verdeckt
        return None
    leiste = getattr(fenster, "sidebar", None)
    if leiste is None or not hasattr(leiste, "zusatz_ausfuehren"):
        return None
    st = getattr(fenster, "settings", None)
    if st is not None and not st.get_bool("ui/zusatz_panels", True):
        return None
    return leiste


class PanelFaehig:
    """Zusatzfenster (Einstellungen, die man selten braucht): ``exec()`` zeigt sie in der Seitenleiste statt über dem Text.
    ``class MeinDialog(PanelFaehig, QDialog)``; ein Fenster mit festem Platzbedarf kann ``kompakt_machen()`` anbieten."""
    ALS_PANEL = True

    def exec(self):
        leiste = leiste_fuer(self)
        if leiste is None:
            return super().exec()
        return QDialog.Accepted if leiste.zusatz_ausfuehren(self) else QDialog.Rejected
