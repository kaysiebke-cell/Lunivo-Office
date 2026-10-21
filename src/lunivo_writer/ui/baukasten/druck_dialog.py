"""Das Druckfenster: links die Vorschau des Blattes, rechts die Reiter „Standard“, „Lunivo-Office“ und „Drucker“.

    d = DruckDialog(parent, seiten=5, papier_mm=(210, 297), quer=False, start={...}, vorschau=lambda nummern, ein: [QImage, ...])
    if d.exec(): d.ergebnis()

``DruckAnsicht`` ist derselbe Inhalt ohne Knopfzeile (so liegt er auch im Menü unter „Drucken“). Der Baustein druckt nichts selbst;
``ergebnis()`` liefert die Wahl als Wörterbuch, der Aufrufer druckt (siehe ``editor/druck.py``).
"""
from __future__ import annotations

import math
from typing import Callable

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPalette
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QRadioButton, QSpinBox, QStyle, QTabWidget, QVBoxLayout, QWidget)

from lunivo_writer.editor.druck import PAPIER, PRO_BLATT, blatt_zeichnen, papier_name, seiten_nach_wahl
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste

KEIN_DRUCKER = "Kein Drucker eingerichtet"
KEIN_DRUCKER_HINWEIS = "Kein Drucker eingerichtet — es wird das Fenster des Systems geöffnet."
KOMMENTARE = [("Keine (nur das Dokument)", "keine"), ("Als Sprechblasen am Rand", "blasen")]
BLATTSEITEN = [("Alle Seiten", "alle"), ("Nur Vorderseiten (ungerade)", "vorder"), ("Nur Rückseiten (gerade)", "rueck")]
BEIDSEITIG = [("Aus", "aus"), ("Lange Kante", "lang"), ("Kurze Kante", "kurz")]
ZUSTAND = {0: "Bereit", 1: "Druckt", 2: "Fehler", 3: "Angehalten"}


def _kopf(text: str) -> QLabel:
    k = QLabel(text.upper())
    k.setStyleSheet("color: palette(mid); font-size: 8pt; font-weight: 600; letter-spacing: 1px; margin-top: 8px;")
    return k


def _drucker_liste() -> list:
    try:
        from PySide6.QtPrintSupport import QPrinterInfo
        return list(QPrinterInfo.availablePrinters())
    except Exception:
        return []


def _combo(eintraege, aktuell) -> QComboBox:
    c = QComboBox()
    for text, wert in eintraege:
        c.addItem(text, wert)
    i = c.findData(aktuell)
    c.setCurrentIndex(max(0, i))
    return c


class DruckAnsicht(QWidget):
    """Vorschau links, Reiter rechts. ``geaendert`` kommt bei jeder Änderung der Wahl."""
    geaendert = Signal()
    eigenschaften = Signal(str)                                   # Name des Druckers → der Aufrufer öffnet dessen Einstellungen

    def __init__(self, seiten: int, papier_mm: tuple[float, float] = (210, 297), quer: bool = False, start: dict | None = None, *,
                 auswahl: bool = False, vorschau: Callable[[list[int], dict], list[QImage]] | None = None, parent=None):
        super().__init__(parent)
        s = start or {}
        self._seiten, self._vorschau, self._blatt = max(1, seiten), vorschau, 0
        self._cache: dict = {}
        self._sync = False
        self._drucker = _drucker_liste()
        hoch = (min(papier_mm), max(papier_mm))
        v = QHBoxLayout(self); v.setContentsMargins(0, 14, 0, 0); v.setSpacing(0)

        # ---- links: Vorschau -------------------------------------------------------------------------------------------
        links = QVBoxLayout(); links.setContentsMargins(14, 12, 14, 12)
        self.flaeche = VorschauFlaeche(self._zeichnen, 380, flaeche=False)
        links.addWidget(self.flaeche, 1)
        unten = QHBoxLayout()
        self.zeigen = QCheckBox("Vorschau"); self.zeigen.setChecked(bool(s.get("vorschau", True)))
        unten.addWidget(self.zeigen); unten.addStretch(1)
        self.nav = []
        st = self.style()
        for sp, tip, f in ((QStyle.SP_MediaSkipBackward, "Erstes Blatt", lambda: self._gehe(0)),
                           (QStyle.SP_MediaSeekBackward, "Voriges Blatt", lambda: self._gehe(self._blatt - 1))):
            k = QPushButton(); k.setIcon(st.standardIcon(sp)); k.setToolTip(tip); k.clicked.connect(f); self.nav.append(k); unten.addWidget(k)
        self.nr = QSpinBox(); self.nr.setMinimum(1); self.nr.valueChanged.connect(lambda n: self._gehe(n - 1))
        self.von = QLabel("/ 1")
        unten.addWidget(self.nr); unten.addWidget(self.von)
        for sp, tip, f in ((QStyle.SP_MediaSeekForward, "Nächstes Blatt", lambda: self._gehe(self._blatt + 1)),
                           (QStyle.SP_MediaSkipForward, "Letztes Blatt", lambda: self._gehe(10 ** 6))):
            k = QPushButton(); k.setIcon(st.standardIcon(sp)); k.setToolTip(tip); k.clicked.connect(f); self.nav.append(k); unten.addWidget(k)
        for k in self.nav:
            k.setFlat(True); k.setFixedWidth(30)
        links.addLayout(unten)
        lw = QWidget(); lw.setLayout(links); lw.setFixedWidth(384)
        v.addWidget(lw)

        # ---- rechts: Reiter ----------------------------------------------------------------------------------------------
        self.reiter = QTabWidget(); self.reiter.setDocumentMode(True)
        v.addWidget(self.reiter, 1)
        self._standard(s, hoch, quer, auswahl)
        self._programm(s)
        self._druckerseite(s)
        self.reiter.setCurrentIndex(max(0, min(2, int(s.get("reiter", 0)))))
        self._verdrahten()
        self._timer = QTimer(self); self._timer.setSingleShot(True); self._timer.setInterval(250); self._timer.timeout.connect(self._neu_laden)
        self._aenderung()

    # ---- Reiter „Standard“ ----------------------------------------------------------------------------------------------
    def _standard(self, s, hoch, quer, auswahl):
        w = QWidget(); f = QVBoxLayout(w); f.setContentsMargins(20, 6, 20, 12); f.setSpacing(8)
        f.addWidget(_kopf("Drucker"))
        z = QHBoxLayout(); z.addWidget(QLabel("Name"))
        self.name = QComboBox()
        if self._drucker:
            for p in self._drucker:
                self.name.addItem(p.printerName(), p.printerName())
            i = self.name.findData(s.get("drucker", ""))
            self.name.setCurrentIndex(i if i >= 0 else max(0, next((j for j, p in enumerate(self._drucker) if p.isDefault()), 0)))
        else:
            self.name.addItem(KEIN_DRUCKER, "")
        z.addWidget(self.name, 1)
        self.eig = QPushButton("Eigenschaften…"); self.eig.setEnabled(bool(self._drucker))
        z.addWidget(self.eig); f.addLayout(z)
        zz = QHBoxLayout(); zz.addWidget(QLabel("Status:")); self.status = QLabel(); self.status.setWordWrap(True)
        zz.addWidget(self.status, 1); f.addLayout(zz)

        f.addWidget(_kopf("Bereich und Kopien"))
        self.alle = QRadioButton("Alle Seiten"); self.auswahl = QRadioButton("Auswahl"); self.seiten = QRadioButton("Seiten:")
        self.auswahl.setEnabled(auswahl)
        gruppe = QButtonGroup(self); [gruppe.addButton(b) for b in (self.alle, self.auswahl, self.seiten)]
        self.text = QLineEdit(s.get("seiten_text", "")); self.text.setPlaceholderText("1-3, 5")
        (self.seiten if s.get("bereich") == "seiten" else self.alle).setChecked(True)
        f.addWidget(self.alle); f.addWidget(self.auswahl)
        zs = QHBoxLayout(); zs.addWidget(self.seiten); zs.addWidget(self.text, 1); f.addLayout(zs)
        zk = QHBoxLayout(); zk.addWidget(QLabel("Anzahl der Kopien"))
        self.kopien = QSpinBox(); self.kopien.setRange(1, 999); self.kopien.setValue(int(s.get("kopien", 1)))
        zk.addWidget(self.kopien); zk.addStretch(1); f.addLayout(zk)
        self.sortieren = QCheckBox("Sortieren"); self.sortieren.setChecked(bool(s.get("sortieren", True))); f.addWidget(self.sortieren)
        zb = QHBoxLayout(); zb.addWidget(QLabel("Blattseiten"))
        self.blattseiten = _combo(BLATTSEITEN, s.get("blattseiten", "alle")); zb.addStretch(1); zb.addWidget(self.blattseiten); f.addLayout(zb)

        f.addWidget(_kopf("Seitenlayout"))
        self.papier = self._papier_combo(s.get("papier") or papier_name(*hoch))
        self.lage = _combo([("Hochformat", False), ("Querformat", True)], bool(s.get("quer", quer)))
        self.pro_blatt = _combo([(str(n), n) for n in PRO_BLATT], int(s.get("pro_blatt", 1)))
        for text, c in (("Papiergröße", self.papier), ("Ausrichtung", self.lage), ("Seiten pro Blatt", self.pro_blatt)):
            z = QHBoxLayout(); z.addWidget(QLabel(text)); z.addStretch(1); z.addWidget(c); f.addLayout(z)
        f.addStretch(1)
        self.reiter.addTab(w, "Standard")

    @staticmethod
    def _papier_combo(aktuell: str) -> QComboBox:
        c = QComboBox()
        for n in PAPIER:
            c.addItem(n, n)
        if aktuell not in PAPIER:
            c.addItem(aktuell, aktuell)
        c.setCurrentIndex(c.findData(aktuell))
        return c

    # ---- Reiter „Lunivo-Office“ ------------------------------------------------------------------------------------------
    def _programm(self, s):
        w = QWidget(); f = QVBoxLayout(w); f.setContentsMargins(20, 6, 20, 12); f.setSpacing(8)
        f.addWidget(_kopf("Inhalt"))

        def haken(text, schl, vorgabe):
            c = QCheckBox(text); c.setChecked(bool(s.get(schl, vorgabe))); f.addWidget(c); return c
        self.hintergrund = haken("Seitenhintergrund", "hintergrund", True)
        self.zeichnungen = haken("Bilder und andere Grafikobjekte", "zeichnungen", True)
        self.platzhalter = haken("Textplatzhalter", "platzhalter", False)
        self.steuer = haken("Steuerelemente", "steuerelemente", True)
        z = QHBoxLayout(); z.addWidget(QLabel("Kommentare")); z.addStretch(1)
        self.kommentare = _combo(KOMMENTARE, s.get("kommentare", "keine")); z.addWidget(self.kommentare); f.addLayout(z)
        f.addWidget(_kopf("Farbe"))
        self.schwarz = haken("Text schwarz drucken", "schwarz", False)
        f.addWidget(_kopf("Seiten"))
        self.leere = haken("Leere Seiten mitdrucken", "leere", True)
        f.addStretch(1)
        self.reiter.addTab(w, "Lunivo-Office")

    # ---- Reiter „Drucker“ ------------------------------------------------------------------------------------------------
    def _druckerseite(self, s):
        w = QWidget(); f = QVBoxLayout(w); f.setContentsMargins(20, 6, 20, 12); f.setSpacing(8)
        f.addWidget(_kopf("Drucker"))
        g = QGridLayout(); g.setHorizontalSpacing(24)
        self.info = {}
        for i, k in enumerate(("Name", "Status", "Typ", "Ort", "Kommentar")):
            g.addWidget(QLabel(k + ":"), i, 0)
            self.info[k] = QLabel("—"); self.info[k].setWordWrap(True); g.addWidget(self.info[k], i, 1)
        g.setColumnStretch(1, 1); f.addLayout(g)
        f.addWidget(_kopf("Papier"))
        self.papier2 = self._papier_combo(self.papier.currentData())
        self.lage2 = _combo([("Hochformat", False), ("Querformat", True)], self.lage.currentData())
        self.beidseitig = _combo(BEIDSEITIG, s.get("beidseitig", "aus"))
        for text, c in (("Papiergröße", self.papier2), ("Ausrichtung", self.lage2), ("Beidseitig", self.beidseitig)):
            z = QHBoxLayout(); z.addWidget(QLabel(text)); z.addStretch(1); z.addWidget(c); f.addLayout(z)
        f.addWidget(_kopf("Gerät"))
        self.geraet = QLabel(); self.geraet.setWordWrap(True); f.addWidget(self.geraet)
        f.addStretch(1)
        self.reiter.addTab(w, "Drucker")

    # ---- Verdrahtung ---------------------------------------------------------------------------------------------------
    def _verdrahten(self):
        for a, b in ((self.papier, self.papier2), (self.lage, self.lage2)):      # dieselbe Wahl auf beiden Reitern
            a.currentIndexChanged.connect(lambda _=0, a=a, b=b: self._gleich(a, b))
            b.currentIndexChanged.connect(lambda _=0, a=a, b=b: self._gleich(b, a))
        self.name.currentIndexChanged.connect(self._drucker_gewaehlt)
        self.eig.clicked.connect(lambda: self.eigenschaften.emit(self.name.currentData() or ""))
        self.text.textChanged.connect(lambda _t: (self.seiten.setChecked(True), self._aenderung()))
        for c in (self.alle, self.auswahl, self.seiten):
            c.toggled.connect(lambda _=False: self._aenderung())
        for c in (self.blattseiten, self.pro_blatt, self.kommentare, self.beidseitig):
            c.currentIndexChanged.connect(lambda _=0: self._aenderung())
        for c in (self.hintergrund, self.zeichnungen, self.platzhalter, self.steuer, self.schwarz, self.leere, self.sortieren, self.zeigen):
            c.toggled.connect(lambda _=False: self._aenderung())
        self.kopien.valueChanged.connect(lambda _=0: self._aenderung())
        self.reiter.currentChanged.connect(lambda _=0: self.geaendert.emit())
        self._drucker_gewaehlt()

    def _gleich(self, von: QComboBox, nach: QComboBox):
        if self._sync:
            return
        self._sync = True
        nach.setCurrentIndex(nach.findData(von.currentData()))
        self._sync = False
        self._aenderung()

    def _drucker_gewaehlt(self, *_):
        p = next((p for p in self._drucker if p.printerName() == self.name.currentData()), None)
        if p is None:
            self.status.setText(KEIN_DRUCKER_HINWEIS)
            for k in self.info:
                self.info[k].setText("—")
            self.geraet.setText("Erst einen Drucker wählen.")
            return
        zustand = ZUSTAND.get(int(getattr(p.state(), "value", p.state())), "Bereit")
        self.status.setText(zustand)
        for k, t in (("Name", p.printerName()), ("Status", zustand), ("Typ", p.makeAndModel()), ("Ort", p.location()), ("Kommentar", p.description())):
            self.info[k].setText(t or "—")
        farbe = "Farbe" if getattr(p, "supportedColorModes", None) and len(p.supportedColorModes()) > 1 else "Schwarzweiß oder Farbe"
        duplex = "Beidseitiger Druck möglich" if len(p.supportedDuplexModes()) > 1 else "Nur einseitiger Druck"
        self.geraet.setText(f"{farbe} · {duplex}")
        self.beidseitig.setEnabled(len(p.supportedDuplexModes()) > 1)
        self._aenderung()

    def drucker_setzen(self, kopien: int, beidseitig: str) -> None:
        """Nach den Einstellungen des Systems: Kopien und Beidseitig übernehmen."""
        self.kopien.setValue(max(1, kopien))
        self.beidseitig.setCurrentIndex(max(0, self.beidseitig.findData(beidseitig)))

    # ---- Wahl lesen ------------------------------------------------------------------------------------------------------
    def ergebnis(self) -> dict:
        b = PAPIER.get(self.papier.currentData())
        return {"drucker": self.name.currentData() or "", "bereich": "seiten" if self.seiten.isChecked() else ("auswahl" if self.auswahl.isChecked() else "alle"),
                "seiten_text": self.text.text().strip(), "kopien": self.kopien.value(), "sortieren": self.sortieren.isChecked(),
                "blattseiten": self.blattseiten.currentData(), "papier": self.papier.currentData(), "papier_mm": b, "quer": bool(self.lage.currentData()),
                "pro_blatt": self.pro_blatt.currentData(), "hintergrund": self.hintergrund.isChecked(), "zeichnungen": self.zeichnungen.isChecked(),
                "platzhalter": self.platzhalter.isChecked(), "steuerelemente": self.steuer.isChecked(), "kommentare": self.kommentare.currentData(),
                "schwarz": self.schwarz.isChecked(), "leere": self.leere.isChecked(), "beidseitig": self.beidseitig.currentData(),
                "vorschau": self.zeigen.isChecked(), "reiter": self.reiter.currentIndex()}

    def gueltig(self) -> bool:
        """Ein eigener Seitenbereich muss mindestens eine Seite treffen."""
        return bool(seiten_nach_wahl(self.ergebnis(), self._seiten))

    # ---- Vorschau --------------------------------------------------------------------------------------------------------
    def _blatt_mm(self) -> tuple[float, float]:
        b, h = PAPIER.get(self.papier.currentData(), (210, 297))
        return (h, b) if self.lage.currentData() else (b, h)

    def _blaetter(self) -> list[list[int]]:
        e = self.ergebnis()
        nummern = seiten_nach_wahl(e, self._seiten)
        k = int(e["pro_blatt"])
        return [nummern[i:i + k] for i in range(0, len(nummern), k)] or [[]]

    def _aenderung(self):
        n = len(self._blaetter())
        self._blatt = min(self._blatt, n - 1)
        self.nr.blockSignals(True); self.nr.setMaximum(n); self.nr.setValue(self._blatt + 1); self.nr.blockSignals(False)
        self.von.setText(f"/ {n}")
        self.flaeche.setVisible(self.zeigen.isChecked())
        self.flaeche.update()
        self._timer.start()
        self.geaendert.emit()

    def _gehe(self, i: int):
        self._blatt = max(0, min(i, len(self._blaetter()) - 1))
        self.nr.blockSignals(True); self.nr.setValue(self._blatt + 1); self.nr.blockSignals(False)
        self._neu_laden()

    def _neu_laden(self):
        if not (self._vorschau and self.zeigen.isChecked()):
            return
        nummern = self._blaetter()[self._blatt]
        e = self.ergebnis()
        schl = (tuple(nummern), e["hintergrund"], e["zeichnungen"], e["platzhalter"], e["steuerelemente"], e["schwarz"], e["leere"], e["kommentare"])
        if schl not in self._cache:
            self._cache[schl] = self._vorschau(nummern, e) if nummern else []
            if len(self._cache) > 24:
                self._cache.pop(next(iter(self._cache)))
        self._bilder = self._cache[schl]
        self.flaeche.update()

    def _zeichnen(self, p: QPainter, r) -> None:
        b, h = self._blatt_mm()
        rand_oben, rand_links = 24, 30                                  # Platz für die Maße über und links vom Blatt
        f = min((r.width() - rand_links - 10) / b, (r.height() - rand_oben - 10) / h)
        blatt = QRectF(rand_links + (r.width() - rand_links - b * f) / 2, rand_oben + (r.height() - rand_oben - h * f) / 2, b * f, h * f)
        p.setPen(self.palette().color(QPalette.Mid))
        p.drawText(QRectF(blatt.left(), 0, blatt.width(), rand_oben - 4), Qt.AlignCenter, f"{b:g} mm ({self.papier.currentData()})")
        p.save(); p.translate(rand_links - 8, blatt.center().y()); p.rotate(-90)
        p.drawText(QRectF(-60, -10, 120, 20), Qt.AlignCenter, f"{h:g} mm"); p.restore()
        p.fillRect(blatt.translated(2, 3), QColor(0, 0, 0, 60))
        p.fillRect(blatt, Qt.white)
        bilder = getattr(self, "_bilder", [])
        if bilder and self.zeigen.isChecked():
            blatt_zeichnen(p, blatt, bilder, int(self.pro_blatt.currentData()), rand=1.0 if self.pro_blatt.currentData() > 1 else 0.0)


class DruckDialog(QDialog):
    """Das Druckfenster mit Knopfzeile: Hilfe links, „Abbrechen“ und „Drucken“ rechts."""

    def __init__(self, parent, seiten: int, papier_mm: tuple[float, float] = (210, 297), quer: bool = False, start: dict | None = None, *,
                 auswahl: bool = False, vorschau=None, hilfe: Callable | None = None):
        super().__init__(parent)
        self.setWindowTitle("Drucken"); self.setModal(True); self.resize(940, 640)
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 12); v.setSpacing(0)
        self.ansicht = DruckAnsicht(seiten, papier_mm, quer, start, auswahl=auswahl, vorschau=vorschau)
        v.addWidget(self.ansicht, 1)
        h = QPushButton("Hilfe")
        if hilfe:
            h.clicked.connect(hilfe)
        fuss = QVBoxLayout(); fuss.setContentsMargins(14, 8, 14, 0)
        self.ok = fussleiste(self, fuss, h, ok_text="Drucken")
        v.addLayout(fuss)
        self.ansicht.geaendert.connect(self._pruefen)
        self._pruefen()

    def _pruefen(self):
        self.ok.setEnabled(self.ansicht.gueltig())

    def ergebnis(self) -> dict:
        return self.ansicht.ergebnis()
