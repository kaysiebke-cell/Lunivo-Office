"""Die Druckvorschau als ganzes Fenster: oben Drucken…, Blattwechsel, Ansicht (Eine/Zwei/Alle Seiten), Zoom, Einpassen, Vorschau schließen.

    d = DruckVorschau(parent, quelle)          # quelle: editor.druck.Zwischenseiten
    d.drucken.connect(...)                     # „Drucken…“ schließt die Vorschau und meldet sich
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSpinBox, QStyle, QVBoxLayout, QWidget)

from lunivo_writer.core.farben import Farbe
ANSICHTEN = [("Eine Seite", 1), ("Zwei Seiten", 2), ("Alle Seiten", 0)]


class DruckVorschau(QDialog):
    drucken = Signal()

    def __init__(self, parent, quelle):
        super().__init__(parent)
        self.setWindowTitle("Lunivo-Office")
        self._q, self._zoom, self._n = quelle, 1.0, 1
        self._gesamt = max(1, quelle.anzahl())
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        leiste = QHBoxLayout(); leiste.setContentsMargins(12, 8, 12, 8); leiste.setSpacing(8)
        druck = QPushButton("Drucken…"); druck.setObjectName("optFertig"); druck.setMinimumHeight(32)
        druck.clicked.connect(lambda: (self.accept(), self.drucken.emit()))
        leiste.addWidget(druck); leiste.addSpacing(12)
        st = self.style()

        def knopf(sp, tip, f):
            k = QPushButton(); k.setIcon(st.standardIcon(sp)); k.setToolTip(tip); k.setFlat(True); k.setFixedWidth(32); k.clicked.connect(f)
            leiste.addWidget(k); return k
        knopf(QStyle.SP_MediaSkipBackward, "Erste Seite", lambda: self._gehe(1))
        knopf(QStyle.SP_MediaSeekBackward, "Vorige Seite", lambda: self._gehe(self._n - self._schritt()))
        self.nr = QSpinBox(); self.nr.setRange(1, self._gesamt); self.nr.valueChanged.connect(self._gehe)
        leiste.addWidget(self.nr); leiste.addWidget(QLabel(f"/ {self._gesamt}"))
        knopf(QStyle.SP_MediaSeekForward, "Nächste Seite", lambda: self._gehe(self._n + self._schritt()))
        knopf(QStyle.SP_MediaSkipForward, "Letzte Seite", lambda: self._gehe(self._gesamt))
        leiste.addSpacing(12)
        self.ansicht = QComboBox()
        for t, w in ANSICHTEN:
            self.ansicht.addItem(t, w)
        self.ansicht.currentIndexChanged.connect(lambda _=0: self._aufbauen())
        leiste.addWidget(self.ansicht); leiste.addSpacing(12)
        leiste.addWidget(self._zoomknopf("−", "Verkleinern", 1 / 1.25))
        self.prozent = QLabel("100 %"); self.prozent.setMinimumWidth(48); self.prozent.setAlignment(Qt.AlignCenter)
        leiste.addWidget(self.prozent)
        leiste.addWidget(self._zoomknopf("+", "Vergrößern", 1.25))
        ein = QPushButton("Einpassen"); ein.clicked.connect(self.einpassen); leiste.addWidget(ein)
        leiste.addStretch(1)
        zu = QPushButton("Vorschau schließen"); zu.clicked.connect(self.reject); leiste.addWidget(zu)
        v.addLayout(leiste)
        linie = QFrame(); linie.setFrameShape(QFrame.HLine); linie.setFrameShadow(QFrame.Sunken); v.addWidget(linie)
        self.flaeche = QScrollArea(); self.flaeche.setWidgetResizable(True); self.flaeche.setFrameShape(QFrame.NoFrame)
        v.addWidget(self.flaeche, 1)
        self.finished.connect(lambda _=0: self._q.schliessen())
        self.resize(1100, 800)

    def _zoomknopf(self, text, tip, faktor):
        k = QPushButton(text); k.setFlat(True); k.setFixedWidth(30); k.setToolTip(tip)
        k.clicked.connect(lambda: self._zoom_setzen(self._zoom * faktor))
        return k

    def _schritt(self) -> int:
        return max(1, int(self.ansicht.currentData() or 1))

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_erst", False):
            self._erst = True
            self.einpassen()

    def einpassen(self) -> None:
        """Zoom, bei dem die Seiten der Ansicht ganz ins Fenster passen (bei „Alle Seiten“ die Breite einer Seite)."""
        b, h = self._q.groesse_px(self._n)
        vp = self.flaeche.viewport().size()
        k = self._schritt() if self.ansicht.currentData() else 1
        self._zoom_setzen(max(0.1, min((vp.width() - 40) / (b * k + 16 * (k - 1)), (vp.height() - 60) / h if self.ansicht.currentData() else 9)))

    def _zoom_setzen(self, z: float) -> None:
        self._zoom = max(0.1, min(4.0, z))
        self.prozent.setText(f"{round(self._zoom * 100)} %")
        self._aufbauen()

    def _gehe(self, n: int) -> None:
        n = max(1, min(self._gesamt, n))
        if n == self._n and self._seiten:
            return
        self._n = n
        self.nr.blockSignals(True); self.nr.setValue(n); self.nr.blockSignals(False)
        self._aufbauen()

    _seiten: list = []

    def _aufbauen(self) -> None:
        modus = self.ansicht.currentData()
        zeigen = list(range(1, self._gesamt + 1)) if modus == 0 else list(range(self._n, min(self._gesamt, self._n + modus - 1) + 1))
        inhalt = QWidget(); h = QVBoxLayout(inhalt) if modus == 0 else QHBoxLayout(inhalt)
        h.setContentsMargins(20, 20, 20, 20); h.setSpacing(16); h.setAlignment(Qt.AlignCenter)
        self._seiten = []
        for n in zeigen:
            l = QLabel(); l.setPixmap(QPixmap.fromImage(self._q.bild(n, self._zoom))); l.setObjectName("vorschauSeite")
            l.setStyleSheet("QLabel#vorschauSeite { border: 1px solid " + ("#1c7ed6" if n == self._n else Farbe.GRAU) + "; }")
            h.addWidget(l, 0, Qt.AlignCenter); self._seiten.append(l)
        self.flaeche.setWidget(inhalt)
        if modus == 0 and self._n > 1:
            self.flaeche.ensureWidgetVisible(self._seiten[self._n - 1], 0, 0)
