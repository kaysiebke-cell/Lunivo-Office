"""Kleine Dialoge: Seite einrichten, Absatz, Kopf-/Fußzeile, Tabelle, Suchen/Ersetzen."""
from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
    QWidget,
)

from lunivo_writer.models.page import PAPER_MM, HeaderFooter, PageSettings
from lunivo_writer.ui.baukasten import DialogRahmen, FarbFeld, Linie, LinienWahl
from lunivo_writer.ui.baukasten.mass_feld import EINHEITEN, MassSpin as _MassSpin, einheit, set_einheit, spin as _spin  # noqa: F401


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
class PageSetupDialog(PanelFaehig, QDialog):
    def __init__(self, page: PageSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seite einrichten")
        self.page = page.copy()
        form = QFormLayout()
        self.paper = QComboBox(); self.paper.addItems(list(PAPER_MM) + ["Benutzerdefiniert"])
        self.paper.setCurrentText(page.paper_name())
        self.orient = QComboBox(); self.orient.addItems(["Hochformat", "Querformat"])
        self.orient.setCurrentIndex(1 if page.landscape else 0)
        self.top = _spin(page.margin_top_mm); self.bottom = _spin(page.margin_bottom_mm)
        self.left = _spin(page.margin_left_mm); self.right = _spin(page.margin_right_mm)
        form.addRow("Papierformat", self.paper); form.addRow("Ausrichtung", self.orient)
        form.addRow("Rand oben", self.top); form.addRow("Rand unten", self.bottom)
        form.addRow("Rand links", self.left); form.addRow("Rand rechts", self.right)
        self.spalten = QSpinBox(); self.spalten.setRange(1, 4); self.spalten.setValue(max(1, int(page.spalten)))
        self.spalten_abstand = _spin(page.spalten_abstand_mm, 2, 40)
        self.spalten_linie = QCheckBox("Linie zwischen den Spalten"); self.spalten_linie.setChecked(page.spalten_linie)
        form.addRow("Spalten", self.spalten); form.addRow("Abstand der Spalten", self.spalten_abstand)
        form.addRow("", self.spalten_linie)
        bb = knopfzeile(self)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)

    def result_page(self) -> PageSettings:
        p = self.page
        if self.paper.currentText() in PAPER_MM:
            p.width_mm, p.height_mm = sorted(PAPER_MM[self.paper.currentText()])
        else:
            p.width_mm, p.height_mm = sorted((p.width_mm, p.height_mm))
        p.set_orientation(self.orient.currentIndex() == 1)
        p.margin_top_mm, p.margin_bottom_mm = self.top.value(), self.bottom.value()
        p.margin_left_mm, p.margin_right_mm = self.left.value(), self.right.value()
        p.spalten, p.spalten_abstand_mm, p.spalten_linie = self.spalten.value(), self.spalten_abstand.value(), self.spalten_linie.isChecked()
        return p

    def accept(self) -> None:
        p = self.result_page()
        if p.margin_left_mm + p.margin_right_mm >= p.width_mm - 20 or \
                p.margin_top_mm + p.margin_bottom_mm >= p.height_mm - 20:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Seite einrichten", "Die Ränder lassen zu wenig Platz für Text.")
            return
        super().accept()


class HeaderFooterDialog(PanelFaehig, QDialog):
    def __init__(self, title: str, hf: HeaderFooter, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.text = QPlainTextEdit(hf.text)
        self.text.setPlaceholderText("Text eingeben. {PAGE} = Seitenzahl, {PAGES} = Seitenanzahl")
        self.align = QComboBox(); self.align.addItems(["Links", "Zentriert", "Rechts"])
        self.align.setCurrentIndex({"left": 0, "center": 1, "right": 2}.get(hf.align, 1))
        b = QPushButton("Seitenzahl einfügen")
        b.clicked.connect(lambda: self.text.insertPlainText("{PAGE}"))
        lay = QVBoxLayout(self)
        lay.addWidget(self.text); 
        row = QHBoxLayout(); row.addWidget(QLabel("Ausrichtung")); row.addWidget(self.align); row.addWidget(b)
        lay.addLayout(row)
        bb = knopfzeile(self)
        lay.addWidget(bb)

    def value(self) -> HeaderFooter:
        return HeaderFooter(self.text.toPlainText().strip("\n"),
                            ["left", "center", "right"][self.align.currentIndex()])


class TableDialog(PanelFaehig, QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tabelle einfügen")
        self.rows = QSpinBox(); self.rows.setRange(1, 200); self.rows.setValue(3)
        self.cols = QSpinBox(); self.cols.setRange(1, 30); self.cols.setValue(3)
        self.borders = QCheckBox("Rahmenlinien"); self.borders.setChecked(True)
        form = QFormLayout(); form.addRow("Zeilen", self.rows); form.addRow("Spalten", self.cols)
        form.addRow("", self.borders)
        bb = knopfzeile(self)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)


class BildGroesseDialog(PanelFaehig, QDialog):
    def __init__(self, breite_px: float, hoehe_px: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bildgröße")
        self.verh = (hoehe_px / breite_px) if breite_px else 1.0
        self.b = _spin(breite_px * 25.4 / 96, 1, 2000)
        self.h = _spin(hoehe_px * 25.4 / 96, 1, 2000)
        self.fest = QCheckBox("Seitenverhältnis beibehalten"); self.fest.setChecked(True)
        self._sperre = False
        self.b.valueChanged.connect(self._b)
        self.h.valueChanged.connect(self._h)
        form = QFormLayout(); form.addRow("Breite", self.b); form.addRow("Höhe", self.h); form.addRow("", self.fest)
        bb = knopfzeile(self)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)

    def _b(self, v):
        if self.fest.isChecked() and not self._sperre:
            self._sperre = True; self.h.setValue(v * self.verh); self._sperre = False

    def _h(self, v):
        if self.fest.isChecked() and not self._sperre and self.verh:
            self._sperre = True; self.b.setValue(v / self.verh); self._sperre = False

    def breite_px(self): return self.b.value() * 96 / 25.4
    def hoehe_px(self): return self.h.value() * 96 / 25.4


class ZoomDialog(PanelFaehig, QDialog):
    """Ansicht ▸ Zoom: feste Stufen, Seitenbreite, ganze Seite oder eigener Wert."""
    STUFEN = (200, 150, 100, 75, 50, 25)

    def __init__(self, parent, aktuell: float):
        super().__init__(parent)
        from PySide6.QtWidgets import QButtonGroup, QRadioButton, QSpinBox
        self.setWindowTitle("Zoom")
        lay = QVBoxLayout(self)
        self.gruppe = QButtonGroup(self)
        self._art: dict[int, tuple[str, float]] = {}
        eintraege = [(f"{n} %", ("wert", n / 100)) for n in self.STUFEN] + \
                    [("Seitenbreite", ("breite", 0)), ("Ganze Seite", ("seite", 0))]
        for i, (text, art) in enumerate(eintraege):
            r = QRadioButton(text)
            self.gruppe.addButton(r, i)
            self._art[i] = art
            lay.addWidget(r)
            if art[0] == "wert" and abs(art[1] - aktuell) < 0.005:
                r.setChecked(True)
        eigen = QRadioButton("Eigener Wert:")
        self.gruppe.addButton(eigen, 100)
        self.spin = QSpinBox(); self.spin.setRange(10, 500); self.spin.setSuffix(" %")
        self.spin.setValue(int(round(aktuell * 100)))
        self.spin.valueChanged.connect(lambda _: eigen.setChecked(True))
        zeile = QHBoxLayout(); zeile.addWidget(eigen); zeile.addWidget(self.spin)
        lay.addLayout(zeile)
        if self.gruppe.checkedId() < 0:
            eigen.setChecked(True)
        bb = knopfzeile(self)
        lay.addWidget(bb)

    def ergebnis(self) -> tuple[str, float]:
        i = self.gruppe.checkedId()
        if i == 100 or i not in self._art:
            return "wert", self.spin.value() / 100
        return self._art[i]


class WasserzeichenDialog(PanelFaehig, DialogRahmen):
    def __init__(self, parent, aktuell: dict | None):
        a = aktuell or {}
        super().__init__(parent, "Wasserzeichen", self._male)
        self.text = QLineEdit(a.get("text", "ENTWURF"))
        self.knopf = FarbFeld(a.get("farbe", "#c0c0c0"), "Farbe")
        self.winkel = QSpinBox(); self.winkel.setRange(-90, 90); self.winkel.setValue(int(a.get("winkel", -45)))
        self.groesse = QSpinBox(); self.groesse.setRange(10, 300); self.groesse.setSuffix(" pt"); self.groesse.setValue(int(a.get("groesse_pt", 80)))
        for beschr, w in (("Text", self.text), ("Farbe", self.knopf), ("Drehung (Grad)", self.winkel), ("Größe", self.groesse)):
            self.zeile(beschr, w)
        self.entfernt = False
        self.zusatzknopf("Entfernen", lambda: setattr(self, "entfernt", True))
        self.text.textChanged.connect(self.aktualisieren); self.winkel.valueChanged.connect(self.aktualisieren)
        self.groesse.valueChanged.connect(self.aktualisieren); self.knopf.farbeGeaendert.connect(self.aktualisieren)

    @property
    def farbe(self) -> str:
        return self.knopf.farbe

    def _male(self, p, r) -> None:
        p.setPen(QColor(self.farbe)); f = p.font(); f.setPointSizeF(max(8.0, self.groesse.value() / 4)); f.setBold(True); p.setFont(f)
        p.translate(r.center()); p.rotate(self.winkel.value())
        p.drawText(QRect(-r.width() // 2, -r.height() // 2, r.width(), r.height()), Qt.AlignCenter, self.text.text())

    def ergebnis(self) -> dict | None:
        if self.entfernt or not self.text.text().strip():
            return None
        return {"text": self.text.text().strip(), "farbe": self.farbe, "winkel": self.winkel.value(), "groesse_pt": self.groesse.value()}
