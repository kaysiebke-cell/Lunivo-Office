"""„Rahmen und Schattierung“ als Baustein: das Fenster mit den Karteireitern Rahmen, Seitenrand und Schattierung.

Wer ein Fenster zu Rahmen oder Füllung braucht (Absatz, später Tabelle und Zelle), ruft dieses auf und bekommt Werte zurück,
ohne selbst zu wissen, wie sie gespeichert werden:

    d = RahmenSchattierungDialog(parent, rahmen=Linie | None, fuell="#d0ebff" | None, muster=("pct25", "#000000") | None,
                                 seitenrand={"art": …} | None, fuer=["Absatz"], seite="rahmen")
    if d.exec(): d.rahmen(), d.schattierung(), d.seitenrand()

* Reiter **Rahmen**: Einstellung (Ohne · Kontur · Alle · Raster · Anpassen), Linienart, Farbe, Breite, Vorschau mit Kantenknöpfen
  (ein Klick auf die Fläche am Rand schaltet die Kante ebenso).
* Reiter **Seitenrand**: derselbe Aufbau für den Rahmen um die ganze Seite (nur rundherum), mit „Optionen …“ für den Abstand.
* Reiter **Schattierung**: Füllfarbe, Muster (Prozentraster, Linienmuster) mit Musterfarbe, Vorschau.

Die Farbpalette kommt aus ``FarbFeld`` (mit „Automatisch“ statt „Keine Farbe“), das Fenster „Weitere Farben …“ aus ``farbwaehler``.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTabWidget,
    QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.editor import muster as M
from lunivo_writer.editor.linie import LINIENBREITEN, STILE, Linie
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.linien import RahmenSeiten, rahmen_symbol

KANTEN = (("t", "Oben", RahmenSeiten.OBEN), ("b", "Unten", RahmenSeiten.UNTEN), ("l", "Links", RahmenSeiten.LINKS),
          ("r", "Rechts", RahmenSeiten.RECHTS), ("h", "Zwischen Absätzen", RahmenSeiten.INNEN_H))
HINWEIS = "Diagramm oder Schaltflächen klicken, um Rahmen hinzuzufügen"


def _kopf(text: str) -> QLabel:
    """Kleine Überschrift über einem Feld — dieselbe Schrift wie die Gruppen in den Optionen."""
    l = QLabel(text.rstrip(":").upper())
    l.setStyleSheet("color: palette(mid); font-size: 8pt; font-weight: 600; letter-spacing: 0.5px;")
    return l


def _einstellung_symbol(art: str, px: int = 28) -> QIcon:
    """Kleines Blatt mit Textzeilen und dem Rahmen, den die Einstellung setzt."""
    pm = QPixmap(px, px); pm.fill(Qt.transparent)
    p = QPainter(pm)
    r = QRectF(4, 4, px - 8, px - 8)
    p.setPen(Qt.NoPen); p.setBrush(QColor("#adb5bd"))
    for i in range(5):
        p.drawRect(QRectF(r.left() + 3, r.top() + 4 + i * (r.height() - 8) / 5, r.width() - 6 - (i == 4) * 6, 1.6))
    stark, blass = QPen(QColor("#e6e9ec"), 2), QPen(QColor("#868e96"), 1, Qt.DotLine)
    p.setBrush(Qt.NoBrush)
    if art == "kontur":
        p.setPen(stark); p.drawRect(r)
    elif art == "alle":
        p.setPen(stark); p.drawRect(r); p.drawLine(QPointF(r.left(), r.center().y()), QPointF(r.right(), r.center().y()))
        p.drawLine(QPointF(r.center().x(), r.top()), QPointF(r.center().x(), r.bottom()))
    elif art == "raster":
        p.setPen(blass); p.drawRect(r); p.drawLine(QPointF(r.left(), r.center().y()), QPointF(r.right(), r.center().y()))
        p.drawLine(QPointF(r.center().x(), r.top()), QPointF(r.center().x(), r.bottom()))
    elif art == "anpassen":
        p.setPen(blass); p.drawRect(r)
        p.setPen(stark); p.drawLine(r.topLeft(), r.bottomLeft()); p.drawLine(r.bottomLeft(), r.bottomRight())
    p.end()
    return QIcon(pm)


def _stil_symbol(art: str, groesse: QSize = QSize(150, 16)) -> QIcon:
    """Probe einer Linienart für die Liste „Formatvorlage“."""
    pm = QPixmap(groesse); pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    Linie("#e6e9ec", 1.5, art).zeichne(p, 3, groesse.height() / 2, groesse.width() - 3, groesse.height() / 2, 96 / 72)
    p.end()
    return QIcon(pm)


def _breite_symbol(pt: float, groesse: QSize = QSize(74, 12)) -> QIcon:
    pm = QPixmap(groesse); pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setPen(QPen(QColor("#e6e9ec"), max(1.0, pt * 96 / 72), Qt.SolidLine, Qt.FlatCap))
    p.drawLine(0, groesse.height() // 2, groesse.width(), groesse.height() // 2)
    p.end()
    return QIcon(pm)


def _muster_symbol(schluessel: str, px: int = 16) -> QIcon:
    pm = QPixmap(px, px); pm.fill(QColor("#ffffff"))
    p = QPainter(pm)
    if schluessel != "loeschen":
        p.drawTiledPixmap(0, 0, px, px, M.kachel(schluessel, "#000000", None))
    p.setPen(QColor("#868e96")); p.setBrush(Qt.NoBrush); p.drawRect(0, 0, px - 1, px - 1)
    p.end()
    return QIcon(pm)


# ------------------------------------------------------------------------------------------------------ Vorschau
class _Vorschau(QWidget):
    """Blatt mit zwei Absätzen aus grauen Zeilen; zeigt Rahmen und Füllung und schaltet Kanten per Klick."""
    kante = Signal(str)

    def __init__(self, kanten_klick: bool = True):
        super().__init__()
        self.setFixedSize(220, 160)
        self.seiten = ""
        self.linie = Linie()
        self.pinsel = None
        self.klick = kanten_klick
        self.mit_h = False                                        # Linie zwischen Absätzen schaltbar
        self.seitenrand: tuple[Linie, float] | None = None        # Rahmen um die Seite: (Linie, Abstand in mm)

    def _feld(self) -> QRectF:
        return QRectF(self.rect()).adjusted(46, 26, -46, -30)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), Qt.white)
        f = self._feld()
        if self.seitenrand is not None:
            li, mm = self.seitenrand
            a = max(4.0, mm * 1.2)
            Linie(li.farbe, li.breite_pt, li.art, self.seiten).rahmen_zeichnen(p, QRectF(self.rect()).adjusted(a, a, -a, -a), 96 / 72)
            f = QRectF(self.rect()).adjusted(a + 14, a + 14, -a - 14, -a - 14)
        if self.pinsel is not None:
            p.fillRect(f, self.pinsel)
        p.setPen(Qt.NoPen); p.setBrush(QColor("#adb5bd"))
        zeilen = 7
        h = f.height() / (zeilen + 1)
        luecke = self._luecke(f)
        for i in range(zeilen):
            if i == 3:
                continue
            y = f.top() + h * (i + 0.5) + (h * 0.5 if i > 3 else 0)
            p.drawRect(QRectF(f.left() + 6, y, f.width() - 12 - (i in (2, 6)) * 40, h * 0.42))
        if self.seiten and self.seitenrand is None:
            self.linie.mit_seiten(self.seiten).rahmen_zeichnen(p, f, 96 / 72, [luecke])
        p.end()

    @staticmethod
    def _luecke(f: QRectF) -> float:
        return f.top() + f.height() / 8 * 3.5

    def mousePressEvent(self, e):
        if not self.klick:
            return
        f, pos, tol = self._feld(), e.position(), 9
        if self.seitenrand is not None:                           # beim Seitenrand sind die Kanten die des Seitenrahmens
            a = max(4.0, self.seitenrand[1] * 1.2)
            f = QRectF(self.rect()).adjusted(a, a, -a, -a)
        if not f.adjusted(-tol, -tol, tol, tol).contains(pos):
            return
        if self.mit_h and self.seitenrand is None and abs(pos.y() - self._luecke(f)) < tol * 1.4 and f.left() < pos.x() < f.right():
            self.kante.emit("h"); return
        for k, d in (("t", abs(pos.y() - f.top())), ("b", abs(pos.y() - f.bottom())), ("l", abs(pos.x() - f.left())), ("r", abs(pos.x() - f.right()))):
            if d < tol:
                self.kante.emit(k); return



# --------------------------------------------------------------------------------------------------- Karteireiter
class _RahmenSeite(QWidget):
    """Einstellung · Linienart · Farbe · Breite · Vorschau mit Kantenknöpfen · Übernehmen für."""
    geaendert = Signal()

    def __init__(self, linie: Linie | None, *, seitenrand: bool = False, innen_h: bool = False, fuer: list[str] | None = None,
                 abstand_mm: float | None = None):
        super().__init__()
        self.seitenrand, self.innen_h = seitenrand, innen_h
        self.abstand_mm = abstand_mm if abstand_mm is not None else 8.0
        basis = linie or Linie("#000000", 0.75, "einfach")
        self.seiten = linie.seiten if linie else ""
        g = QGridLayout(self)
        g.setContentsMargins(14, 12, 14, 10); g.setHorizontalSpacing(20); g.setVerticalSpacing(5)
        # --- Einstellung
        g.addWidget(_kopf("Einstellung:"), 0, 0)
        spalte = QVBoxLayout(); spalte.setSpacing(2)
        self.einstellung: dict[str, QToolButton] = {}
        for art, text in (("ohne", "Ohne"), ("kontur", "Kontur"), ("alle", "Alle"), ("raster", "Raster"), ("anpassen", "Anpassen")):
            b = QToolButton(); b.setCheckable(True); b.setAutoExclusive(True); b.setText(text); b.setIcon(_einstellung_symbol("ohne" if art == "ohne" else art))
            b.setIconSize(QSize(28, 28)); b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon); b.setFixedWidth(118); b.setAutoRaise(True)
            b.setStyleSheet("QToolButton { text-align: left; padding: 3px 8px; border: 1px solid transparent; border-radius: 6px; }"
                            "QToolButton:checked { background: palette(midlight); border-color: palette(mid); }")
            b.clicked.connect(lambda _c=False, a=art: self._setze_einstellung(a))
            self.einstellung[art] = b
            spalte.addWidget(b)
        self.einstellung["raster"].setEnabled(False); self.einstellung["raster"].setToolTip("Nur für Tabellen")
        self.einstellung["alle"].setEnabled(innen_h)
        self.einstellung["alle"].setToolTip("" if innen_h else "Nur, wenn mehrere Absätze oder Tabellenzellen gemeint sind")
        spalte.addStretch(1)
        g.addLayout(spalte, 1, 0, 3, 1)
        # --- Linie
        g.addWidget(_kopf("Formatvorlage:"), 0, 1)
        self.arten = QListWidget(); self.arten.setIconSize(QSize(150, 16)); self.arten.setFixedWidth(180); self.arten.setFixedHeight(150)
        for k in STILE:
            it = QListWidgetItem(_stil_symbol(k), ""); it.setData(Qt.UserRole, k); it.setToolTip(STILE[k][0])
            self.arten.addItem(it)
        g.addWidget(self.arten, 1, 1)
        g.addWidget(_kopf("Farbe:"), 2, 1, Qt.AlignBottom)
        self.farbe = FarbFeld("" if basis.farbe in ("", "#000000") else basis.farbe, "Rahmenfarbe", keine_text="Automatisch")
        g.addWidget(self.farbe, 3, 1, Qt.AlignTop)
        self.breite = QComboBox(); self.breite.setIconSize(QSize(74, 12))
        for b in LINIENBREITEN:
            self.breite.addItem(_breite_symbol(b), f"{b:g}".replace(".", ",") + " Pt", b)
        g.addWidget(_kopf("Breite:"), 4, 1, Qt.AlignBottom)
        g.addWidget(self.breite, 5, 1, Qt.AlignTop)
        # --- Vorschau
        g.addWidget(_kopf("Vorschau"), 0, 2)
        hinweis = QLabel(HINWEIS); hinweis.setStyleSheet("color: palette(mid); font-size: 9pt;")
        g.addWidget(hinweis, 0, 3, 1, 2)
        self.vorschau = _Vorschau()
        self.vorschau.mit_h = innen_h
        kasten = QWidget(); kg = QGridLayout(kasten); kg.setContentsMargins(0, 0, 0, 0)
        self.kantenknoepfe: dict[str, QToolButton] = {}
        for k, text, flagge in KANTEN:
            if k == "h" and not innen_h:
                continue
            b = QToolButton(); b.setCheckable(True); b.setIcon(rahmen_symbol(flagge, 22)); b.setToolTip(text); b.setIconSize(QSize(22, 22))
            b.setAutoRaise(True); b.setFixedSize(30, 30)
            b.setStyleSheet("QToolButton { border: 1px solid palette(midlight); border-radius: 4px; }"
                            "QToolButton:hover { background: palette(midlight); border-color: palette(mid); }"
                            "QToolButton:checked { background: palette(mid); border-color: palette(highlight); }")
            b.toggled.connect(lambda an, k=k: self._kante(k, an))
            self.kantenknoepfe[k] = b
        links = QVBoxLayout(); links.setContentsMargins(0, 0, 0, 0)
        reihenfolge = [k for k in ("t", "h", "b") if k in self.kantenknoepfe]
        for i, k in enumerate(reihenfolge):
            links.addWidget(self.kantenknoepfe[k])
            if i < len(reihenfolge) - 1:
                links.addStretch(1)
        unten = QHBoxLayout(); unten.setContentsMargins(0, 0, 0, 0)
        unten.addWidget(self.kantenknoepfe["l"]); unten.addStretch(1); unten.addWidget(self.kantenknoepfe["r"])
        kg.setHorizontalSpacing(8); kg.setVerticalSpacing(6)
        kg.addLayout(links, 0, 0)
        kg.addWidget(self.vorschau, 0, 1)
        kg.addLayout(unten, 1, 1)
        g.addWidget(kasten, 1, 2, 4, 2, Qt.AlignTop | Qt.AlignLeft)
        self.vorschau.kante.connect(lambda k: self.kantenknoepfe[k].toggle() if k in self.kantenknoepfe else None)
        # --- Übernehmen für, Optionen
        g.addWidget(_kopf("Übernehmen für:"), 6, 2, 1, 2, Qt.AlignBottom)
        self.fuer = QComboBox(); self.fuer.addItems(fuer or ["Absatz"])
        g.addWidget(self.fuer, 7, 2, 1, 3)
        self.optionen = QPushButton("Optionen …"); self.optionen.setVisible(seitenrand)
        self.optionen.clicked.connect(self._optionen)
        g.addWidget(self.optionen, 8, 4, Qt.AlignRight)
        g.setRowStretch(9, 1); g.setColumnStretch(3, 1)
        # --- Anfangswerte, Verkabelung
        i = self.arten.row(next((self.arten.item(r) for r in range(self.arten.count()) if self.arten.item(r).data(Qt.UserRole) == basis.art), self.arten.item(0)))
        self.arten.setCurrentRow(i)
        self.breite.setCurrentIndex(min(range(self.breite.count()), key=lambda j: abs(self.breite.itemData(j) - basis.breite_pt)))
        self.arten.currentRowChanged.connect(lambda _r: self._neu())
        self.breite.currentIndexChanged.connect(lambda _i: self._neu())
        self.farbe.farbeGeaendert.connect(lambda _f: self._neu())
        self._zeige_seiten()

    # ---- Zustand
    def linie_wert(self) -> Linie:
        it = self.arten.currentItem()
        return Linie(self.farbe.farbe or "#000000", float(self.breite.currentData()), it.data(Qt.UserRole) if it else "einfach")

    def _setze_einstellung(self, art: str) -> None:
        if art == "ohne":
            self.seiten = ""
        elif art == "kontur":
            self.seiten = "tblr"
        elif art == "alle" and self.innen_h:
            self.seiten = "tblrh"
        self._zeige_seiten()

    def _kante(self, k: str, an: bool) -> None:
        s = set(self.seiten)
        (s.add if an else s.discard)(k)
        self.seiten = "".join(c for c in "tblrh" if c in s)
        self._zeige_seiten(von_knopf=True)

    def _zeige_seiten(self, von_knopf: bool = False) -> None:
        for k, b in self.kantenknoepfe.items():
            b.blockSignals(True); b.setChecked(k in self.seiten); b.blockSignals(False)
        gewaehlt = "ohne" if not self.seiten else "kontur" if self.seiten == "tblr" else "alle" if self.seiten == "tblrh" and self.innen_h else "anpassen"
        self.einstellung[gewaehlt].setChecked(True)
        self._neu()

    def _neu(self) -> None:
        v = self.vorschau
        v.seiten, v.linie = self.seiten, self.linie_wert()
        if self.seitenrand:
            v.seitenrand = (self.linie_wert(), self.abstand_mm)
        v.update()
        self.geaendert.emit()

    def _optionen(self) -> None:
        d = _AbstandDialog(self, self.abstand_mm)
        if d.exec():
            self.abstand_mm = d.wert()
            self._neu()


class _AbstandDialog(QDialog):
    """„Optionen …“ am Seitenrand: Abstand des Rahmens vom Seitenrand."""
    def __init__(self, parent, mm: float):
        super().__init__(parent)
        self.setWindowTitle("Rahmen- und Schattierungsoptionen")
        v = QVBoxLayout(self)
        z = QHBoxLayout(); z.addWidget(QLabel("Abstand vom Seitenrand"))
        self.feld = QDoubleSpinBox(); self.feld.setRange(2, 30); self.feld.setSuffix(" mm"); self.feld.setValue(mm)
        z.addWidget(self.feld); v.addLayout(z)
        zu = QHBoxLayout(); zu.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(ok); v.addLayout(zu)

    def wert(self) -> float:
        return self.feld.value()


class _SchattierungSeite(QWidget):
    """Ausfüllen (Farbe) · Muster (Art, Farbe) · Vorschau · Übernehmen für."""
    geaendert = Signal()

    def __init__(self, fuell: str | None, muster: tuple[str, str] | None, fuer: list[str] | None):
        super().__init__()
        g = QGridLayout(self); g.setContentsMargins(14, 12, 14, 10); g.setHorizontalSpacing(24); g.setVerticalSpacing(5)
        g.addWidget(_kopf("Ausfüllen"), 0, 0)
        self.fuell = FarbFeld(fuell or "", "Füllfarbe", keine_text="Keine Farbe")
        g.addWidget(self.fuell, 1, 0, Qt.AlignLeft)
        g.addWidget(_kopf("Muster"), 2, 0)
        kasten = QWidget(); kv = QVBoxLayout(kasten)
        kv.addWidget(_kopf("Formatvorlage:"))
        self.art = QComboBox(); self.art.setIconSize(QSize(16, 16)); self.art.setMaxVisibleItems(18)
        for k, name, _o in M.MUSTER:
            self.art.addItem(_muster_symbol(k), name, k)
        kv.addWidget(self.art)
        kv.addWidget(_kopf("Farbe:"))
        self.farbe = FarbFeld("" if not muster or muster[1] in ("", "#000000") else muster[1], "Musterfarbe", keine_text="Automatisch")
        kv.addWidget(self.farbe, 0, Qt.AlignLeft)
        kv.addStretch(1)
        g.addWidget(kasten, 3, 0)
        g.addWidget(_kopf("Vorschau"), 0, 1)
        self.vorschau = _Vorschau(kanten_klick=False)
        g.addWidget(self.vorschau, 1, 1, 3, 1, Qt.AlignTop)
        g.addWidget(_kopf("Übernehmen für:"), 4, 1, Qt.AlignBottom)
        self.fuer = QComboBox(); self.fuer.addItems(fuer or ["Absatz"])
        g.addWidget(self.fuer, 5, 1)
        g.setRowStretch(6, 1); g.setColumnStretch(1, 1)
        self.art.setCurrentIndex(max(0, self.art.findData(muster[0] if muster else "loeschen")))
        self.art.currentIndexChanged.connect(lambda _i: self._neu())
        self.fuell.farbeGeaendert.connect(lambda _f: self._neu())
        self.farbe.farbeGeaendert.connect(lambda _f: self._neu())
        self._neu()

    def werte(self) -> tuple[str | None, tuple[str, str] | None]:
        k = self.art.currentData()
        muster = None if k == "loeschen" else (k, self.farbe.farbe or "#000000")
        return (self.fuell.farbe or None), muster

    def _neu(self) -> None:
        fuell, muster = self.werte()
        self.farbe.setEnabled(muster is not None)
        self.vorschau.pinsel = M.pinsel(muster[0], muster[1], fuell) if muster else (M.pinsel("", "#000000", fuell) if fuell else None)
        self.vorschau.update()
        self.geaendert.emit()


# ---------------------------------------------------------------------------------------------------------- Fenster
class RahmenSchattierungDialog(QDialog):
    """Das Fenster „Rahmen und Schattierung“. Die Reiter und ihre Werte stehen oben in der Beschreibung des Bausteins."""

    def __init__(self, parent=None, *, rahmen: Linie | None = None, fuell: str | None = None, muster: tuple[str, str] | None = None,
                 seitenrand: dict | None = None, mit_seitenrand: bool = True, fuer: list[str] | None = None, innen_h: bool = True,
                 seite: str = "rahmen"):
        super().__init__(parent)
        self.setWindowTitle("Rahmen und Schattierung")
        self.resize(640, 400)
        v = QVBoxLayout(self)
        self.reiter = QTabWidget(); v.addWidget(self.reiter, 1)
        self.p_rahmen = _RahmenSeite(rahmen, innen_h=innen_h, fuer=fuer)
        self.reiter.addTab(self.p_rahmen, "Rahmen")
        self.p_rand = None
        if mit_seitenrand:
            sr = seitenrand or {}
            li = Linie(sr.get("farbe", "#000000"), float(sr.get("breite_pt", 1.0)), sr.get("art", "einfach"), sr.get("seiten", "tblr")) if seitenrand else None
            self.p_rand = _RahmenSeite(li, seitenrand=True, fuer=["Gesamtes Dokument"], abstand_mm=float(sr.get("abstand_mm", 8.0)))
            self.reiter.addTab(self.p_rand, "Seitenrand")
        self.p_schatt = _SchattierungSeite(fuell, muster, fuer)
        self.reiter.addTab(self.p_schatt, "Schattierung")
        self.reiter.setCurrentIndex({"rahmen": 0, "seitenrand": 1 if mit_seitenrand else 0}.get(seite, self.reiter.count() - 1))
        zu = QHBoxLayout(); zu.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(ok); v.addLayout(zu)

    # ---- Ergebnis
    def rahmen(self) -> Linie | None:
        s = self.p_rahmen.seiten
        return self.p_rahmen.linie_wert().mit_seiten(s) if s else None

    def schattierung(self) -> tuple[str | None, tuple[str, str] | None]:
        """(Füllfarbe oder None, (Musterschlüssel, Musterfarbe) oder None)."""
        return self.p_schatt.werte()

    def seitenrand(self) -> dict | None:
        if self.p_rand is None or not self.p_rand.seiten:
            return None
        li = self.p_rand.linie_wert()
        return {"art": li.art, "farbe": li.farbe, "breite_pt": li.breite_pt, "abstand_mm": self.p_rand.abstand_mm,
                "seiten": "".join(c for c in "tblr" if c in self.p_rand.seiten)}
