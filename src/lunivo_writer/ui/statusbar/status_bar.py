"""Statusleiste: Meldung, Wörter/Zeichen, Seite, Zoom (− Regler + Anzeige)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QSlider, QStatusBar, QToolButton


class StatusBar(QStatusBar):
    zoom_kleiner = Signal()
    zoom_groesser = Signal()
    zoom_stufe = Signal()
    zoom_geaendert = Signal(int)          # Prozent, vom Regler

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(True)
        self.lbl_msg = QLabel("")
        self.addWidget(self.lbl_msg, 1)
        self.lbl_words = QLabel("0 Wörter, 0 Zeichen")
        self.lbl_page = QLabel("Seite 1 von 1")
        for w in (self.lbl_words, self.lbl_page):
            w.setContentsMargins(10, 0, 10, 0)
            self.addPermanentWidget(w)
        self.zoom_minus = QToolButton(); self.zoom_minus.setText("−"); self.zoom_minus.setAutoRaise(True)
        self.zoom_plus = QToolButton(); self.zoom_plus.setText("+"); self.zoom_plus.setAutoRaise(True)
        self.zoom_regler = QSlider(Qt.Horizontal); self.zoom_regler.setRange(10, 500); self.zoom_regler.setValue(100)
        self.zoom_regler.setFixedWidth(120)
        self.lbl_zoom = QToolButton(); self.lbl_zoom.setText("100 %"); self.lbl_zoom.setAutoRaise(True)
        self.lbl_zoom.setToolTip("Zoom …"); self.lbl_zoom.setMinimumWidth(52)
        self.zoom_minus.clicked.connect(self.zoom_kleiner)
        self.zoom_plus.clicked.connect(self.zoom_groesser)
        self.lbl_zoom.clicked.connect(self.zoom_stufe)
        self.zoom_regler.valueChanged.connect(self.zoom_geaendert)
        for w in (self.zoom_minus, self.zoom_regler, self.zoom_plus, self.lbl_zoom):
            self.addPermanentWidget(w)

    def meldung(self, text: str) -> None:
        self.lbl_msg.setText(text)

    def zaehler(self, woerter: int, zeichen: int) -> None:
        self.lbl_words.setText(f"{woerter} Wörter, {zeichen} Zeichen")

    def seite(self, aktuell: int | None, gesamt: int | None) -> None:
        self.lbl_page.setText("Seite – von –" if aktuell is None else f"Seite {aktuell} von {gesamt}")

    def zoom_zeigen(self, faktor: float) -> None:
        self.lbl_zoom.setText(f"{round(faktor * 100)} %")
        self.zoom_regler.blockSignals(True)
        self.zoom_regler.setValue(int(round(faktor * 100)))
        self.zoom_regler.blockSignals(False)
