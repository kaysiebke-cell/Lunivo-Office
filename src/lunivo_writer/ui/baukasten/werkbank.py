"""Werkbank: die Funktionen eines Reiters der Schreibhilfe als große, selbsterklärende Zeilen (Symbol, Name, Hinweis, Tastenkürzel, bei Schaltern „an/aus“).

Die Zeilen kommen aus ``ui/schreibhilfe_katalog.py`` und rufen dieselben Befehle wie das Band. Nichts ist grau ohne Weg weiter: Fehlt etwas (Text, KI), führt der Klick
in das passende Fenster oder erklärt es — die Befehle selbst sorgen dafür."""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from lunivo_writer.ui.schreibhilfe_katalog import Funktion, fuer_reiter
from lunivo_writer.ui.widgets import icons

from lunivo_writer.core.farben import Farbe
ZEILE = (('QFrame#funktionsZeile { border: 1px solid palette(midlight); border-radius: 8px; background: transparent; }QFrame#funktionsZeile:hover { background: palette(alternate-base); border-color: palette(mid); }QFrame#funktionsZeile:focus { border: 2px solid ' + Farbe.AKZENT + '; }'))
AN = "background: #2f9e75; color: white; border-radius: 11px; padding: 2px 10px; font-weight: bold;"
AUS = "background: transparent; color: palette(mid); border: 1px solid palette(mid); border-radius: 11px; padding: 2px 10px;"


class FunktionsZeile(QFrame):
    """Eine große, anklickbare Zeile; mit Tastatur bedienbar (Tab, Leertaste oder Eingabe) und mit Fokusrahmen."""
    clicked = Signal()

    def __init__(self, f: Funktion, fenster):
        super().__init__()
        self.setObjectName("funktionsZeile")
        self.f, self.fenster = f, fenster
        self.setStyleSheet(ZEILE)
        self.setMinimumHeight(54)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(f.name)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        h = QHBoxLayout(self); h.setContentsMargins(12, 6, 12, 6); h.setSpacing(12)
        sym = QLabel(); sym.setFixedWidth(28); sym.setAttribute(Qt.WA_TransparentForMouseEvents)
        if icons.hat(f.symbol):
            sym.setPixmap(icons.icon(f.symbol, 22).pixmap(22, 22))
            sym.setProperty("symbolName", f.symbol); sym.setProperty("symbolPx", 22)       # Farbwechsel: Symbol neu beziehen (icons.alle_neu)
        h.addWidget(sym)
        mitte = QVBoxLayout(); mitte.setSpacing(0)
        self.titel = QLabel(f.name); ft = self.titel.font(); ft.setBold(True); self.titel.setFont(ft)
        self.untertitel = QLabel(f.hinweis); self.untertitel.setStyleSheet("color: palette(mid); font-size: 9pt;"); self.untertitel.setWordWrap(True)
        for w in (self.titel, self.untertitel):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
        mitte.addWidget(self.titel)
        if f.hinweis:
            mitte.addWidget(self.untertitel)
        h.addLayout(mitte, 1)
        if f.kuerzel:
            k = QLabel(f.kuerzel); k.setStyleSheet("color: palette(mid); font-size: 8pt; border: 1px solid palette(midlight); border-radius: 3px; padding: 0 5px;")
            k.setAttribute(Qt.WA_TransparentForMouseEvents); h.addWidget(k)
        self.zustand = QLabel(); self.zustand.setAttribute(Qt.WA_TransparentForMouseEvents)
        if f.art == "schalter":
            h.addWidget(self.zustand)
        elif f.art == "menue":
            pf = QLabel("▾"); pf.setAttribute(Qt.WA_TransparentForMouseEvents); h.addWidget(pf)
        self.setToolTip(f.hinweis or f.name)
        self.clicked.connect(self._los)
        self.aktualisieren()

    def mouseReleaseEvent(self, e) -> None:
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()

    def keyPressEvent(self, e) -> None:
        if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(e)

    def _los(self) -> None:
        b = self.fenster.befehle
        if self.f.art == "menue":
            m = b.klappe(self.f.klappe)
            if m is not None:
                m.popup(self.mapToGlobal(QPoint(0, self.height())))
                self._menue = m
            return
        b.tun(self.f.tun, self)
        self.aktualisieren()

    def aktualisieren(self) -> None:
        if self.f.art == "schalter":
            an = bool(self.fenster.befehle.zustand(self.f.tun))
            self.zustand.setText("an" if an else "aus"); self.zustand.setStyleSheet(AN if an else AUS)
            self.setAccessibleDescription("an" if an else "aus")
        if self.f.tun == "w.kiUebersetzen":
            self.untertitel.setText("Nach " + self.fenster.ki.konfig["sprache"])


class Werkbank(QScrollArea):
    """Die Zeilen eines Reiters; ``oben`` (optional) ist ein Widget über den Zeilen, etwa ein Hinweis."""

    def __init__(self, fenster, reiter: str, oben: QWidget | None = None, nur: set | None = None):
        super().__init__()
        self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget(); v = QVBoxLayout(host); v.setContentsMargins(14, 10, 14, 10); v.setSpacing(6)
        if oben is not None:
            v.addWidget(oben)
        self.zeilen = [FunktionsZeile(f, fenster) for f in fuer_reiter(reiter) if nur is None or f.tun in nur]
        for z in self.zeilen:
            v.addWidget(z)
        v.addStretch(1)
        self.setWidget(host)

    def aktualisieren(self) -> None:
        for z in self.zeilen:
            z.aktualisieren()
