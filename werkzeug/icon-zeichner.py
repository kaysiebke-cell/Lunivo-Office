#!/usr/bin/env python3
"""Icon-Zeichner — ein kleines Programm, um eigene Symbole für Lunivo zu zeichnen (24 × 24, Strichzeichnung wie die Lucide-Symbole).

Zeichnen: Linie · Pfad (Klick für Klick, Doppelklick oder Enter beendet) · Rechteck · Kreis · Radierer.
Unten steht das Ergebnis als Pfaddaten: Die kopiert man in Lunivo unter „Symbol austauschen ▸ Eigene Zeichnung …“.
Starten:  python3 werkzeug/icon-zeichner.py   (braucht nur PySide6)
"""
from __future__ import annotations

import math
import os
import re
import sys

from PySide6.QtCore import QByteArray, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QFontDatabase, QKeySequence, QPainter, QPainterPath, QPainterPathStroker, QPen, QPixmap, QTransform
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout, QInputDialog, QLabel, QMainWindow, QMessageBox, QPlainTextEdit,
    QPushButton, QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

RASTER = 24          # Zeichenfläche: 24 × 24 Einheiten
MASSTAB = 20         # Bildpunkte je Einheit


def zahl(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class Form:
    """Eine gezeichnete Form: Art, Punkte (in Einheiten), Eckenradius, geschlossen."""

    def __init__(self, art: str, punkte: list[QPointF], radius: float = 0.0, geschlossen: bool = False, text: str = ""):
        self.art, self.punkte, self.radius, self.geschlossen, self.text = art, list(punkte), radius, geschlossen, text

    def pfad_text(self) -> str:
        p = self.punkte
        if self.art == "roh":
            return self.text
        if self.art in ("linie", "pfad"):
            t = f"M{zahl(p[0].x())} {zahl(p[0].y())}" + "".join(f"L{zahl(q.x())} {zahl(q.y())}" for q in p[1:])
            return t + ("Z" if self.geschlossen and len(p) > 2 else "")
        if self.art == "rechteck":
            x0, y0 = min(p[0].x(), p[1].x()), min(p[0].y(), p[1].y())
            w, h = abs(p[1].x() - p[0].x()), abs(p[1].y() - p[0].y())
            r = min(self.radius, w / 2, h / 2)
            if r <= 0:
                return f"M{zahl(x0)} {zahl(y0)}h{zahl(w)}v{zahl(h)}h{zahl(-w)}Z"
            a = f"A{zahl(r)} {zahl(r)} 0 0 1 "
            return (f"M{zahl(x0 + r)} {zahl(y0)}H{zahl(x0 + w - r)}{a}{zahl(x0 + w)} {zahl(y0 + r)}V{zahl(y0 + h - r)}"
                    f"{a}{zahl(x0 + w - r)} {zahl(y0 + h)}H{zahl(x0 + r)}{a}{zahl(x0)} {zahl(y0 + h - r)}V{zahl(y0 + r)}"
                    f"{a}{zahl(x0 + r)} {zahl(y0)}Z")
        r = math.hypot(p[1].x() - p[0].x(), p[1].y() - p[0].y())                         # kreis
        cx, cy = p[0].x(), p[0].y()
        return f"M{zahl(cx - r)} {zahl(cy)}A{zahl(r)} {zahl(r)} 0 1 0 {zahl(cx + r)} {zahl(cy)}A{zahl(r)} {zahl(r)} 0 1 0 {zahl(cx - r)} {zahl(cy)}Z"

    def qpfad(self) -> QPainterPath:
        p = QPainterPath()
        pts = self.punkte
        if self.art in ("linie", "pfad"):
            p.moveTo(pts[0])
            for q in pts[1:]:
                p.lineTo(q)
            if self.geschlossen and len(pts) > 2:
                p.closeSubpath()
        elif self.art == "rechteck":
            r = QRectF(pts[0], pts[1]).normalized()
            rad = min(self.radius, r.width() / 2, r.height() / 2)
            p.addRoundedRect(r, rad, rad) if rad > 0 else p.addRect(r)
        else:
            rad = math.hypot(pts[1].x() - pts[0].x(), pts[1].y() - pts[0].y())
            p.addEllipse(pts[0], rad, rad)
        return p


class Zeichenflaeche(QWidget):
    def __init__(self, fenster):
        super().__init__()
        self.f = fenster
        self.formen: list[Form] = []
        self.rueck: list[list[Form]] = []
        self.wieder: list[list[Form]] = []
        self.werkzeug = "pfad"
        self.aktuell: Form | None = None          # Form, die gerade entsteht
        self.maus: QPointF | None = None
        self.setFixedSize(RASTER * MASSTAB, RASTER * MASSTAB)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    # ---- Umrechnung -------------------------------------------------------------------------------------------------
    def einheit(self, pos) -> QPointF:
        s = self.f.schritt.value()
        x = min(RASTER, max(0, round(pos.x() / MASSTAB / s) * s))
        y = min(RASTER, max(0, round(pos.y() / MASSTAB / s) * s))
        return QPointF(x, y)

    def merke(self) -> None:
        self.rueck.append([Form(f.art, f.punkte, f.radius, f.geschlossen, f.text) for f in self.formen])
        self.wieder.clear()

    def geaendert(self) -> None:
        self.update()
        self.f.ausgabe_neu()

    # ---- Eingaben ---------------------------------------------------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.beende_pfad()
            return
        if e.button() != Qt.LeftButton:
            return
        p = self.einheit(e.position())
        if self.werkzeug == "radierer":
            self.radiere(e.position())
        elif self.werkzeug == "pfad":
            if self.aktuell is None:
                self.aktuell = Form("pfad", [p, p], geschlossen=self.f.geschlossen.isChecked())
            else:
                self.aktuell.punkte[-1] = p
                self.aktuell.punkte.append(p)
        elif self.aktuell is None:
            self.aktuell = Form(self.werkzeug, [p, p], radius=self.f.radius.value())
        self.update()

    def mouseMoveEvent(self, e):
        self.maus = self.einheit(e.position())
        if self.aktuell is not None:
            self.aktuell.punkte[-1] = self.maus
        self.f.statusBar().showMessage(f"x {zahl(self.maus.x())}   y {zahl(self.maus.y())}")
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.aktuell is not None and self.werkzeug in ("linie", "rechteck", "kreis"):
            a = self.aktuell
            self.aktuell = None
            if a.punkte[0] != a.punkte[1]:
                self.merke()
                self.formen.append(a)
                self.geaendert()
            self.update()

    def mouseDoubleClickEvent(self, e):
        if self.werkzeug == "pfad":
            self.beende_pfad()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.beende_pfad()
        elif e.key() == Qt.Key_Escape:
            self.aktuell = None
            self.update()
        else:
            super().keyPressEvent(e)

    def beende_pfad(self) -> None:
        a = self.aktuell
        if a is None or self.werkzeug != "pfad":
            return
        a.punkte.pop()                                         # der Punkt unter der Maus gehört nicht dazu
        while len(a.punkte) > 1 and a.punkte[-1] == a.punkte[-2]:
            a.punkte.pop()
        self.aktuell = None
        if len(a.punkte) >= 2:
            self.merke()
            self.formen.append(a)
            self.geaendert()
        self.update()

    def radiere(self, pos) -> None:
        breite = max(10.0, self.f.staerke.value() * MASSTAB)
        for f in reversed(self.formen):
            st = QPainterPathStroker()
            st.setWidth(breite)
            if f.art == "roh":
                getroffen = self.roh_getroffen(f, pos)
            else:
                getroffen = st.createStroke(self.skaliert(f.qpfad())).contains(pos)
            if getroffen:
                self.merke()
                self.formen.remove(f)
                self.geaendert()
                return

    def roh_renderer(self, f: Form) -> QSvgRenderer:
        farbe = "#e6e9ec"
        return QSvgRenderer(QByteArray((f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{farbe}" '
                                        f'stroke-width="{zahl(self.f.staerke.value())}" stroke-linecap="round" stroke-linejoin="round">'
                                        f'<path id="p" d="{f.text}"/></svg>').encode()))

    def zeichne_roh(self, p: QPainter, f: Form) -> None:
        self.roh_renderer(f).render(p, QRectF(0, 0, RASTER * MASSTAB, RASTER * MASSTAB))

    def roh_getroffen(self, f: Form, pos) -> bool:
        r = self.roh_renderer(f)
        b = r.boundsOnElement("p")                                   # in Einheiten
        return QRectF(b.x() * MASSTAB, b.y() * MASSTAB, b.width() * MASSTAB, b.height() * MASSTAB).adjusted(-8, -8, 8, 8).contains(pos)

    def skaliert(self, p: QPainterPath) -> QPainterPath:
        return QTransform.fromScale(MASSTAB, MASSTAB).map(p)

    # ---- Befehle ----------------------------------------------------------------------------------------------------
    def zurueck(self):
        if self.rueck:
            self.wieder.append(self.formen)
            self.formen = self.rueck.pop()
            self.geaendert()

    def vor(self):
        if self.wieder:
            self.rueck.append(self.formen)
            self.formen = self.wieder.pop()
            self.geaendert()

    def leeren(self):
        if self.formen:
            self.merke()
            self.formen = []
            self.geaendert()

    # ---- Zeichnen ---------------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1f2225"))
        for i in range(RASTER + 1):
            fest = i % 12 == 0
            p.setPen(QPen(QColor("#4a5058" if fest else "#33383e"), 1.5 if fest else 1))
            p.drawLine(i * MASSTAB, 0, i * MASSTAB, RASTER * MASSTAB)
            p.drawLine(0, i * MASSTAB, RASTER * MASSTAB, i * MASSTAB)
        rand = QColor("#5a6370"); rand.setAlpha(120)                              # 2 Einheiten Rand, wie bei Lucide
        p.setPen(QPen(rand, 1, Qt.DashLine))
        p.drawRect(2 * MASSTAB, 2 * MASSTAB, 20 * MASSTAB, 20 * MASSTAB)
        stift = QPen(QColor("#e6e9ec"), self.f.staerke.value() * MASSTAB, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(stift)
        p.setBrush(Qt.NoBrush)
        for f in self.formen:
            if f.art == "roh":
                self.zeichne_roh(p, f)
            else:
                p.drawPath(self.skaliert(f.qpfad()))
        if self.aktuell is not None:
            vor = QPen(QColor("#4a8fd8"), self.f.staerke.value() * MASSTAB, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(vor)
            p.drawPath(self.skaliert(self.aktuell.qpfad()))
            p.setPen(QPen(QColor("#ffffff"), 5))
            for q in self.aktuell.punkte[:-1]:
                p.drawPoint(QPointF(q.x() * MASSTAB, q.y() * MASSTAB))
        if self.maus is not None:
            p.setPen(QPen(QColor("#4a8fd8"), 7))
            p.drawPoint(QPointF(self.maus.x() * MASSTAB, self.maus.y() * MASSTAB))
        p.end()


class Fenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Icon-Zeichner")
        mitte = QWidget()
        h = QHBoxLayout(mitte)
        self.setCentralWidget(mitte)
        # Einstellungen müssen vor der Fläche stehen (sie liest sie beim Zeichnen)
        self.schritt = QDoubleSpinBox(); self.schritt.setRange(0.25, 2); self.schritt.setSingleStep(0.25); self.schritt.setValue(1)
        self.staerke = QDoubleSpinBox(); self.staerke.setRange(0.5, 4); self.staerke.setSingleStep(0.25); self.staerke.setValue(2)
        self.radius = QDoubleSpinBox(); self.radius.setRange(0, 12); self.radius.setSingleStep(0.5); self.radius.setValue(0)
        self.geschlossen = QCheckBox("Pfad schließen")
        self.flaeche = Zeichenflaeche(self)
        h.addWidget(self.flaeche)
        rechts = QVBoxLayout()
        h.addLayout(rechts)
        form = QFormLayout()
        form.addRow("Raster (Einheiten)", self.schritt)
        form.addRow("Strichstärke", self.staerke)
        form.addRow("Ecken Rechteck", self.radius)
        form.addRow(self.geschlossen)
        rechts.addLayout(form)
        self.staerke.valueChanged.connect(self.flaeche.geaendert)
        self.vorschau = []
        zeile = QHBoxLayout()
        for px in (16, 24, 32, 48):
            l = QLabel(); l.setFixedSize(px + 12, px + 12); l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet("background: #2a2e32; border-radius: 6px;")
            self.vorschau.append((px, l)); zeile.addWidget(l)
        rechts.addLayout(zeile)
        self.reiter = QTabWidget()
        self.text = QPlainTextEdit(); self.text.setReadOnly(True)               # nur die Pfaddaten — für „Eigene Zeichnung …“ in Lunivo
        self.code = QPlainTextEdit(); self.code.setReadOnly(True)               # die ganze SVG-Datei, wie im Lucide Studio
        for feld in (self.text, self.code):
            feld.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
            feld.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.reiter.addTab(self.text, "Pfaddaten")
        self.reiter.addTab(self.code, "SVG-Code")
        self.reiter.setMinimumHeight(180)
        rechts.addWidget(self.reiter, 1)
        for beschriftung, fn in (("Code laden … (SVG oder Pfaddaten einfügen)", self.lade_code), ("Pfaddaten kopieren", self.kopiere_pfad), ("Als SVG kopieren", self.kopiere_svg),
                                 ("SVG speichern …", self.speichere)):
            b = QPushButton(beschriftung); b.clicked.connect(fn); rechts.addWidget(b)
        rechts.addStretch(1)
        # Werkzeuge
        leiste = QToolBar("Werkzeuge"); leiste.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea, leiste)
        gruppe = QActionGroup(self)
        for schl, text in (("linie", "Linie"), ("pfad", "Pfad"), ("rechteck", "Rechteck"), ("kreis", "Kreis"), ("radierer", "Radierer")):
            a = QAction(text, self, checkable=True)
            a.setChecked(schl == "pfad")
            a.triggered.connect(lambda _=False, s=schl: self.waehle(s))
            gruppe.addAction(a); leiste.addAction(a)
        leiste.addSeparator()
        for text, fn, kuerzel in (("Zurück", self.flaeche.zurueck, QKeySequence.Undo), ("Wieder", self.flaeche.vor, QKeySequence.Redo),
                                  ("Alles löschen", self.flaeche.leeren, None)):
            a = QAction(text, self); a.triggered.connect(lambda _=False, fn=fn: fn())
            if kuerzel is not None:
                a.setShortcut(kuerzel)
            leiste.addAction(a)
        self.statusBar().showMessage("Pfad: Klick für Klick, Doppelklick, Enter oder rechte Maustaste beendet. Esc bricht ab.")
        self.ausgabe_neu()

    def waehle(self, schl: str) -> None:
        self.flaeche.beende_pfad()
        self.flaeche.werkzeug = schl
        self.flaeche.aktuell = None
        self.flaeche.setFocus()

    # ---- Ergebnis ---------------------------------------------------------------------------------------------------
    def pfaddaten(self) -> str:
        return "".join(f.pfad_text() for f in self.flaeche.formen)

    def svg(self, farbe: str = "currentColor") -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{farbe}" '
                f'stroke-width="{zahl(self.staerke.value())}" stroke-linecap="round" stroke-linejoin="round">\n'
                + (f'  <path d="{self.pfaddaten()}" />\n' if self.flaeche.formen else "") + '</svg>\n')

    def ausgabe_neu(self) -> None:
        self.text.setPlainText(self.pfaddaten())
        self.code.setPlainText(self.svg())
        daten = QByteArray(self.svg("#e6e9ec").encode())
        for px, l in self.vorschau:
            pm = QPixmap(px, px); pm.fill(Qt.transparent)
            q = QPainter(pm); QSvgRenderer(daten).render(q); q.end()
            l.setPixmap(pm)

    def lade_code(self) -> None:
        """SVG-Code oder Pfaddaten einfügen (z. B. aus lucide.dev) — sie kommen als Form auf die Fläche und lassen sich ergänzen."""
        text, ok = QInputDialog.getMultiLineText(self, "Code laden", "SVG-Datei oder nur die Pfaddaten (d=\"…\"):")
        if not ok or not text.strip():
            return
        pfade = re.findall(r'\bd\s*=\s*"([^"]+)"', text)
        d = " ".join(pfade) if pfade else (text.strip() if "<" not in text else "")
        if not d:
            QMessageBox.information(self, "Code laden", "Darin steht kein Pfad (d=\"…\").")
            return
        sw = re.search(r'stroke-width\s*=\s*"([0-9.]+)"', text)
        if sw:                                                    # die Strichstärke der Datei übernehmen
            self.staerke.setValue(float(sw.group(1)))
        anderes = re.findall(r"<(rect|circle|ellipse|line|polyline|polygon)\b", text)
        f = self.flaeche
        f.merke()
        f.formen.append(Form("roh", [], text=" ".join(d.split())))
        f.geaendert()
        if anderes:
            QMessageBox.information(self, "Code laden", "Übernommen sind nur die Pfade. Nicht übernommen: " + ", ".join(sorted(set(anderes))) + ".")

    def kopiere_pfad(self) -> None:
        QApplication.clipboard().setText(self.pfaddaten())
        self.statusBar().showMessage("Pfaddaten kopiert — in Lunivo bei „Eigene Zeichnung …“ einfügen.", 5000)

    def kopiere_svg(self) -> None:
        QApplication.clipboard().setText(self.svg())
        self.statusBar().showMessage("SVG kopiert.", 4000)

    def speichere(self) -> None:
        pfad, _ = QFileDialog.getSaveFileName(self, "SVG speichern", os.path.expanduser("~/mein-symbol.svg"), "SVG (*.svg)")
        if pfad:
            with open(pfad, "w", encoding="utf-8") as fh:
                fh.write(self.svg())
            self.statusBar().showMessage(f"Gespeichert: {pfad}", 5000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = Fenster()
    w.show()
    sys.exit(app.exec())
