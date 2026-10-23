"""Das Fenster „Tabstopps“ als Baustein: Position, Ausrichtung und Füllzeichen festlegen, löschen, alle löschen.

    d = TabstoppDialog(parent, [(25.0, "links", ""), (80.0, "rechts", "punkt")], standard_mm=12.5)     # Millimeter, Ausrichtung, Füllzeichen
    if d.exec(): d.stopps(), d.standard_abstand()                                    # dieselbe Liste, sortiert; der Standardabstand der Tabstopps

Das Fenster setzt keine Tabstopps; der Aufrufer (Absatz-Fenster, Editor, Formatvorlage) übernimmt die Liste (``zu_block`` / ``aus_block``).
Die Füllzeichen zeichnet Lunivo selbst (``editor/tabfuell.py``).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QRadioButton, QVBoxLayout,
)

from lunivo_writer.ui.baukasten.dialog_rahmen import fussleiste
from lunivo_writer.ui.baukasten.mass_feld import EinheitFeld, einheit

ARTEN = (("links", "Links"), ("mitte", "Zentriert"), ("rechts", "Rechts"), ("dezimal", "Dezimal"))


def aus_block(bf) -> list[tuple[float, str, str]]:
    """Die Tabstopps eines Absatzformats als Liste aus Millimetern, Ausrichtung und Füllzeichen."""
    from PySide6.QtGui import QTextOption
    from lunivo_writer.editor import tabfuell
    from lunivo_writer.models.page import px_to_mm
    art = {QTextOption.LeftTab: "links", QTextOption.CenterTab: "mitte", QTextOption.RightTab: "rechts", QTextOption.DelimiterTab: "dezimal"}
    fuell = tabfuell.lesen(bf)
    return [(round(px_to_mm(t.position), 1), art.get(t.type, "links"), next((f for p, f in fuell.items() if abs(p - t.position) < 0.05), ""))
            for t in bf.tabPositions()]


def zu_block(bf, stopps) -> None:
    """Tabstopps (mm, Ausrichtung, Füllzeichen) in ein Absatzformat schreiben."""
    from PySide6.QtGui import QTextOption
    from lunivo_writer.editor import tabfuell
    from lunivo_writer.models.page import mm_to_px
    art = {"links": QTextOption.LeftTab, "mitte": QTextOption.CenterTab, "rechts": QTextOption.RightTab, "dezimal": QTextOption.DelimiterTab}
    bf.setTabPositions([QTextOption.Tab(mm_to_px(m), art[a]) for m, a, _f in stopps])
    tabfuell.setzen(bf, {round(mm_to_px(m), 2): f for m, _a, f in stopps if f})


def als_text(stopps) -> str:
    """Tabstopps als Text für eine Formatvorlage: ``30.0:rechts:punkt;80.0:mitte:`` (leer = keine)."""
    return ";".join(f"{m:g}:{a}:{f}" for m, a, f in stopps)


def aus_text(text: str | None) -> list[tuple[float, str, str]]:
    from lunivo_writer.editor.tabfuell import FUELL
    arten = [k for k, _n in ARTEN]
    aus = []
    for teil in (text or "").split(";"):
        try:
            m, a, *f = teil.split(":")
            if a in arten:
                aus.append((float(m), a, f[0] if f and f[0] in FUELL else ""))
        except ValueError:
            continue
    return aus


def _text(mm: float, art: str, fuell: str = "") -> str:
    from lunivo_writer.editor.tabfuell import FUELL
    f, kurz = einheit()
    return f"{mm * f:.2f} {kurz}".replace(".", ",") + "  ·  " + dict(ARTEN)[art] + (f"  ·  {FUELL[fuell][1]}{FUELL[fuell][1]}{FUELL[fuell][1]}" if fuell else "")


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.formular_gitter import FlussLayout, FormularGitter, abschnittstitel
class TabstoppDialog(PanelFaehig, QDialog):
    def __init__(self, parent=None, stopps=(), standard_mm: float | None = None):
        """``standard_mm``: Standardabstand der Tabstopps des Dokuments (``None``: das Feld bleibt weg)."""
        super().__init__(parent)
        self.setWindowTitle("Tabstopps")
        self.resize(550, 340)
        self._stopps: list[tuple[float, str, str]] = sorted(((round(m, 1), a, f) for m, a, f in stopps), key=lambda x: x[0])
        self._geloescht: list[float] = []
        v = QVBoxLayout(self)
        kopf = FormularGitter(); kopf.setContentsMargins(0, 0, 0, 0)
        self.pos = EinheitFeld(0.0, 0.0, 1000.0, ("mm", "cm", "in", "pt"), leer_bei_null=True)
        self.standard = None
        felder = [("Tabstoppposition:", self.pos)]
        if standard_mm is not None:
            self.standard = EinheitFeld(standard_mm, 0.5, 200.0, ("Zeichen", "mm", "cm", "in", "pt"), "Zeichen")
            felder.append(("Standardtabstopps:", self.standard))
        kopf.reihe(*felder, gewichte=(3, 2))
        self.liste = QListWidget(); self.liste.setMinimumHeight(48); self.liste.setMaximumHeight(72)
        kopf.breit(self.liste)
        self.geloescht_text = QLabel(); self.geloescht_text.setWordWrap(True); self.geloescht_text.setAlignment(Qt.AlignTop)
        kopf.breit(self.geloescht_text)
        kopf.breit(abschnittstitel("Ausrichtung"))
        bh = FlussLayout(14); bh.setContentsMargins(0, 0, 0, 0)
        self.art = QButtonGroup(self)
        for i, k in enumerate(("dezimal", "links", "mitte", "rechts")):
            r = QRadioButton(dict(ARTEN)[k]); self.art.addButton(r, [a for a, _n in ARTEN].index(k)); bh.addWidget(r)
        self.art.button(0).setChecked(True)
        kopf.breit(bh)
        kopf.breit(abschnittstitel("Füllzeichen"))
        fg = FlussLayout(14); fg.setContentsMargins(0, 0, 0, 0)
        from lunivo_writer.editor.tabfuell import FUELL
        self.fuell = QButtonGroup(self)
        self._fuell_schluessel = list(FUELL)
        for i, k in enumerate(self._fuell_schluessel):
            r = QRadioButton(FUELL[k][0]); self.fuell.addButton(r, i); fg.addWidget(r)
        self.fuell.button(0).setChecked(True)
        kopf.breit(fg)
        v.addLayout(kopf)
        v.addStretch(1)
        self.b_fest, self.b_loesch = QPushButton("Festlegen"), QPushButton("Löschen")
        self.b_fest.clicked.connect(self.festlegen); self.b_loesch.clicked.connect(self.loeschen)
        b_alle = QPushButton("Alle löschen"); b_alle.clicked.connect(self.alle)
        fussleiste(self, v, self.b_fest, self.b_loesch, b_alle)
        self.liste.currentRowChanged.connect(self._zeile)
        self.pos.valueChanged.connect(self._knoepfe)
        self._fuellen()

    def _fuellen(self) -> None:
        self.liste.clear()
        self.liste.addItems([_text(m, a, f) for m, a, f in self._stopps])
        f, kurz = einheit()
        self.geloescht_text.setText("Zu löschende Tabstopps:\n" + ", ".join(f"{m * f:.2f}".replace(".", ",") + " " + kurz for m in self._geloescht))
        self.geloescht_text.setVisible(bool(self._geloescht))
        self._knoepfe()

    def _knoepfe(self, *_) -> None:
        self.b_fest.setEnabled(self.pos.value() > 0)
        self.b_loesch.setEnabled(self.liste.currentRow() >= 0)

    def _zeile(self, i: int) -> None:
        if 0 <= i < len(self._stopps):
            m, a, f = self._stopps[i]
            self.pos.setValue(m)
            self.art.button([k for k, _n in ARTEN].index(a)).setChecked(True)
            self.fuell.button(self._fuell_schluessel.index(f)).setChecked(True)
        self._knoepfe()

    def festlegen(self) -> None:
        m = round(self.pos.value(), 1)
        if m <= 0:
            return
        self._geloescht = [g for g in self._geloescht if g != m]
        neu = (m, ARTEN[self.art.checkedId()][0], self._fuell_schluessel[self.fuell.checkedId()])
        self._stopps = sorted([s for s in self._stopps if s[0] != m] + [neu], key=lambda x: x[0])
        self._fuellen()

    def loeschen(self) -> None:
        i = self.liste.currentRow()
        if 0 <= i < len(self._stopps):
            self._geloescht.append(self._stopps[i][0])
            del self._stopps[i]
            self._fuellen()

    def alle(self) -> None:
        self._geloescht += [m for m, _a, _f in self._stopps]
        self._stopps = []
        self._fuellen()

    def stopps(self) -> list[tuple[float, str, str]]:
        return list(self._stopps)

    def standard_abstand(self) -> float | None:
        """Der Standardabstand in Millimetern (``None``, wenn das Fenster ohne dieses Feld aufgerufen wurde)."""
        return self.standard.value() if self.standard is not None else None
