"""„Rahmen und Schattierung“ als Baustein: das Fenster mit den Karteireitern Rahmen, Seitenrand und Schattierung.

Wer ein Fenster zu Rahmen oder Füllung braucht (Absatz, später Tabelle und Zelle), ruft dieses auf und bekommt Werte zurück,
ohne selbst zu wissen, wie sie gespeichert werden:

    d = RahmenSchattierungDialog(parent, rahmen=Linie | None, fuell="#d0ebff" | None, muster=("pct25", Farbe.SCHWARZ) | None,
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
from PySide6.QtWidgets import (QSizePolicy, 
    QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTabWidget,
    QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.editor import muster as M
from lunivo_writer.editor.linie import LINIENBREITEN, STILE, Linie
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.linien import RahmenSeiten, rahmen_symbol
from lunivo_writer.ui.baukasten.mass_feld import _PT_MM, EinheitFeld

from lunivo_writer.core.farben import Farbe
KANTEN = (("t", "Oben", RahmenSeiten.OBEN), ("b", "Unten", RahmenSeiten.UNTEN), ("l", "Links", RahmenSeiten.LINKS),
          ("r", "Rechts", RahmenSeiten.RECHTS), ("h", "Zwischen Absätzen", RahmenSeiten.INNEN_H))
HINWEIS = "Diagramm oder Schaltflächen klicken, um Rahmen hinzuzufügen"


def _kopf(text: str) -> QLabel:
    """Kleine Überschrift über einem Feld — der Baustein ``abschnittstitel``."""
    return abschnittstitel(text)


def _einstellung_symbol(art: str, px: int = 28) -> QIcon:
    """Kleines Blatt mit Textzeilen und dem Rahmen, den die Einstellung setzt."""
    pm = QPixmap(px, px); pm.fill(Qt.transparent)
    p = QPainter(pm)
    r = QRectF(4, 4, px - 8, px - 8)
    p.setPen(Qt.NoPen); p.setBrush(QColor(Farbe.GRAU_HELL))
    for i in range(5):
        p.drawRect(QRectF(r.left() + 3, r.top() + 4 + i * (r.height() - 8) / 5, r.width() - 6 - (i == 4) * 6, 1.6))
    stark, blass = QPen(QColor("#e6e9ec"), 2), QPen(QColor(Farbe.GRAU), 1, Qt.DotLine)
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
    pm = QPixmap(px, px); pm.fill(QColor(Farbe.WEISS))
    p = QPainter(pm)
    if schluessel != "loeschen":
        p.drawTiledPixmap(0, 0, px, px, M.kachel(schluessel, Farbe.SCHWARZ, None))
    p.setPen(QColor(Farbe.GRAU)); p.setBrush(Qt.NoBrush); p.drawRect(0, 0, px - 1, px - 1)
    p.end()
    return QIcon(pm)


# ------------------------------------------------------------------------------------------------------ Vorschau
from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.formular_gitter import AngepassteReiter, FormularGitter, UmbruchSchalter, abschnittstitel, mittig
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
        r = self.rect()
        return QRectF(r).adjusted(r.width() * 0.21, r.height() * 0.16, -r.width() * 0.21, -r.height() * 0.19)       # wie bei 220 × 160: 46 / 26 / 30 Bildpunkte

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
        p.setPen(Qt.NoPen); p.setBrush(QColor(Farbe.GRAU_HELL))
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
        self.rand_optionen = {"messen": "text", "abstand": (1.0, 1.0, 4.0, 4.0), "ausrichten": False, "vordergrund": True, "kopf": False, "fuss": False}   # Seitenrand ▸ Optionen
        basis = linie or Linie(Farbe.SCHWARZ, 0.75, "einfach")
        self.seiten = linie.seiten if linie else ""
        v = QVBoxLayout(self); v.setContentsMargins(10, 8, 10, 6); v.setSpacing(6)
        # --- Einstellung: eine Reihe Symbole (der Name steht im Tipp)
        v.addWidget(abschnittstitel("Einstellung"))
        reihe = QHBoxLayout(); reihe.setSpacing(4)
        self.einstellung: dict[str, QToolButton] = {}
        for art, text in (("ohne", "Ohne"), ("kontur", "Kontur"), ("alle", "Alle"), ("raster", "Raster"), ("anpassen", "Anpassen")):
            b = QToolButton(); b.setCheckable(True); b.setAutoExclusive(True); b.setToolTip(text); b.setAccessibleName(text)
            b.setIcon(_einstellung_symbol("ohne" if art == "ohne" else art)); b.setIconSize(QSize(28, 28)); b.setFixedSize(40, 38); b.setAutoRaise(True)
            b.setStyleSheet("QToolButton { border: 1px solid transparent; border-radius: 6px; }"
                            "QToolButton:checked { background: palette(midlight); border-color: palette(mid); }")
            b.clicked.connect(lambda _c=False, a=art: self._setze_einstellung(a))
            self.einstellung[art] = b
            reihe.addWidget(b)
        reihe.addStretch(1)
        v.addLayout(reihe)
        self.einstellung["raster"].setEnabled(False); self.einstellung["raster"].setToolTip("Raster: nur für Tabellen")
        self.einstellung["alle"].setEnabled(innen_h)
        self.einstellung["alle"].setToolTip("Alle" if innen_h else "Alle: nur, wenn mehrere Absätze oder Tabellenzellen gemeint sind")
        if seitenrand:                                           # um eine Seite gibt es nur Ohne, Kontur und Anpassen
            self.einstellung["alle"].setVisible(False); self.einstellung["raster"].setVisible(False)
        # --- Vorschau mit Kantenknöpfen, daneben Farbe und Breite
        v.addWidget(abschnittstitel("Vorschau"))
        self.vorschau = _Vorschau(); self.vorschau.setFixedSize(184, 118); self.vorschau.setToolTip(HINWEIS)
        self.vorschau.mit_h = innen_h
        kasten = QWidget(); kg = QGridLayout(kasten); kg.setContentsMargins(0, 0, 0, 0)
        kg.setProperty("schmal_nein", True)                                              # die Kantenknöpfe stehen um die Vorschau: nicht umbrechen
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
        kg.setHorizontalSpacing(6); kg.setVerticalSpacing(4)
        kg.addLayout(links, 0, 0)
        kg.addWidget(self.vorschau, 0, 1)
        kg.addLayout(unten, 1, 1)
        kasten.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)                        # genau so groß wie Vorschau und Knöpfe: die unteren Knöpfe stehen unter den Rändern der Vorschau
        self.vorschau.kante.connect(lambda k: self.kantenknoepfe[k].toggle() if k in self.kantenknoepfe else None)
        rechts = QVBoxLayout(); rechts.setSpacing(2); rechts.setContentsMargins(0, 0, 0, 0)
        self.farbe = FarbFeld("" if basis.farbe in ("", Farbe.SCHWARZ) else basis.farbe, "Rahmenfarbe", keine_text="Automatisch")
        self.breite = QComboBox(); self.breite.setIconSize(QSize(40, 12))
        for b in LINIENBREITEN:
            self.breite.addItem(_breite_symbol(b, QSize(40, 12)), f"{b:g}".replace(".", ",") + " Pt", b)
        self.breite.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon); self.breite.setMinimumContentsLength(3)
        for w_ in (self.farbe, self.breite):
            w_.setMinimumWidth(0); w_.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        rechts.addWidget(_kopf("Farbe:")); rechts.addWidget(self.farbe)
        rechts.addWidget(_kopf("Breite:")); rechts.addWidget(self.breite)
        self.kunst = QComboBox()                                 # Art: Kunstrahmen aus Figuren statt einer Linie (nur um die Seite)
        from lunivo_writer.editor.seitenrahmen import KUNST
        for k, name in KUNST:
            self.kunst.addItem(name, k)
        self.kunst_kopf = _kopf("Art:")
        rechts.addWidget(self.kunst_kopf); rechts.addWidget(self.kunst); rechts.addStretch(1)
        self.kunst.setVisible(seitenrand); self.kunst_kopf.setVisible(seitenrand)
        self.kunst.currentIndexChanged.connect(lambda _i: self._neu())
        mitte = QHBoxLayout(); mitte.setSpacing(8); mitte.setProperty("schmal_nein", True)       # Vorschau und Farbe/Breite bleiben nebeneinander
        mitte.addWidget(kasten, 0, Qt.AlignTop); mitte.addLayout(rechts, 1)
        v.addLayout(mitte)
        # --- Linienart
        v.addWidget(abschnittstitel("Linienart"))
        self.arten = QListWidget(); self.arten.setIconSize(QSize(150, 16)); self.arten.setFixedHeight(104)
        for k in STILE:
            it = QListWidgetItem(_stil_symbol(k), ""); it.setData(Qt.UserRole, k); it.setToolTip(STILE[k][0])
            self.arten.addItem(it)
        v.addWidget(self.arten)
        # --- Übernehmen für, Optionen
        fuss = QHBoxLayout(); fuss.setSpacing(8)
        self.fuer = QComboBox(); self.fuer.addItems(fuer or ["Absatz"]); self.fuer.setToolTip("Übernehmen für")
        self.optionen = QPushButton("Optionen …")
        self.optionen.clicked.connect(self._optionen)
        self.polster = linie.polster() if linie and linie.polster() else (1.0, 1.0, 4.0, 4.0)    # Abstand zum Text: oben, unten, links, rechts (pt)
        fuss.addWidget(_kopf("Für:"), 0, Qt.AlignVCenter); fuss.addWidget(self.fuer, 1); fuss.addWidget(self.optionen)
        v.addLayout(fuss)
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
        ab = ",".join(f"{x:g}" for x in self.polster) if not self.seitenrand and self.polster != (1.0, 1.0, 4.0, 4.0) else ""
        return Linie(self.farbe.farbe or Farbe.SCHWARZ, float(self.breite.currentData()), it.data(Qt.UserRole) if it else "einfach", abstand=ab)

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

    def _abstand_vorschau(self) -> None:
        """Der Abstand, den die Vorschau des Seitenrahmens zeigt (in mm)."""
        o = self.rand_optionen
        self.abstand_mm = sum(o["abstand"]) / 4 / 72 * 25.4 if o["messen"] == "seitenrand" else 6.0

    def _optionen(self) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        if self.seitenrand:                              # Rahmen um die Seite: Abstand, Gemessen von, Optionen
            d = _SeitenOptionenDialog(self, self.rand_optionen, self.linie_wert())

            def fertig_seite() -> None:
                self.rand_optionen = d.werte()
                self._abstand_vorschau()
                self._neu()
            zeige_unter(self, d, fertig_seite)
            return
        d = _PolsterDialog(self, self.polster, self.linie_wert())      # Absatzrahmen: Abstand zum Text auf allen vier Seiten

        def fertig_absatz() -> None:
            self.polster = d.werte()
            self._neu()
        zeige_unter(self, d, fertig_absatz)


def _blatt_vorschau(p: QPainter, rect) -> tuple[QRectF, QRectF]:
    """Das Blatt der Optionen-Fenster: oben weiß, nach unten vom Feld abgeschnitten, darauf ein Textblock (die erste Zeile eingerückt).
    → (Blatt, Textblock) in Fensterkoordinaten."""
    r = QRectF(rect)
    blatt = QRectF(r.center().x() - 96, r.top(), 192, r.height() + 60)
    p.fillRect(blatt, QColor("white")); p.setPen(QColor("#c4c9ce")); p.drawRect(blatt)
    text = QRectF(blatt.left() + 32, blatt.top() + 32, 128, 70)
    p.setPen(QPen(QColor(Farbe.GRAU), 1.2))
    y, n = text.top(), 0
    while y < text.bottom() - 0.5:
        p.drawLine(int(text.left() + (42 if n == 0 else 0)), int(y), int(text.right()), int(y)); y += 5; n += 1
    return blatt, text


class _PolsterDialog(QDialog):
    """„Optionen …“ am Absatzrahmen: Abstand des Rahmens vom Text, oben, unten, links und rechts (mit Einheit), dazu eine Vorschau."""
    def __init__(self, parent, werte: tuple[float, float, float, float], linie: Linie | None = None):
        super().__init__(parent)
        self.setWindowTitle("Rahmen- und Schattierungsoptionen"); self.resize(345, 328); self.setMinimumSize(0, 0)
        self._linie = linie
        v = QVBoxLayout(self)
        v.addWidget(abschnittstitel("Vom Text"))
        g = FormularGitter()
        einh = ("pt", "mm", "cm", "in")
        self.felder = {}
        paare = []
        for name, schl, wert in (("Oben:", "o", werte[0]), ("Unten:", "u", werte[1]), ("Links:", "l", werte[2]), ("Rechts:", "r", werte[3])):
            f = EinheitFeld(wert * _PT_MM, 0.0, 31 * _PT_MM, einh, "pt"); self.felder[schl] = f
            paare.append((name, f))
            f.valueChanged.connect(lambda *_: self.vorschau.update())
        g.reihe(*paare)                                              # je nach Breite 2 bis 4 nebeneinander
        v.addLayout(g)
        v.addWidget(abschnittstitel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 150, flaeche=False); self.vorschau.setFixedHeight(150); v.addWidget(self.vorschau)
        v.addStretch(1)
        fussleiste(self, v)

    def werte(self) -> tuple[float, float, float, float]:
        f = self.felder
        return tuple(round(f[k].value() / _PT_MM, 2) for k in ("o", "u", "l", "r"))

    def _male(self, p, rect) -> None:
        """Ein Blatt mit Textzeilen; der Rahmen um den Absatz hat die eingestellten Abstände zum Text."""
        blatt, text = _blatt_vorschau(p, rect)
        o, u, l, rt = self.werte()
        k = 1.4                                                    # pt → Bildpunkte der Vorschau
        p.setPen(QPen(QColor(Farbe.TINTE_DUNKEL), 1)); p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(text.left() - l * k, text.top() - o * k, text.width() + (l + rt) * k, text.height() + (o + u) * k))


class _SeitenOptionenDialog(QDialog):
    """„Optionen …“ am Seitenrand: Abstand (vom Text oder vom Seitenrand), „Gemessen von“, die vier Optionen und eine Vorschau der Seite."""
    def __init__(self, parent, w: dict, linie: Linie | None = None):
        super().__init__(parent)
        self.setWindowTitle("Rahmen- und Schattierungsoptionen"); self.resize(635, 478); self.setMinimumSize(0, 0)
        v = QVBoxLayout(self)
        self.abstand_gruppe = abschnittstitel("Vom Text"); v.addWidget(self.abstand_gruppe)
        g = FormularGitter()
        einh = ("pt", "mm", "cm", "in")
        o, u, l, r = w["abstand"]
        self.felder = {}
        paare = []
        for name, schl, wert in (("Oben:", "o", o), ("Unten:", "u", u), ("Links:", "l", l), ("Rechts:", "r", r)):
            f = EinheitFeld(wert * _PT_MM, 0.0, 31 * _PT_MM, einh, "pt"); self.felder[schl] = f
            paare.append((name, f))
            f.valueChanged.connect(lambda *_: self.vorschau.update())
        g.reihe(*paare)
        self.messen = QComboBox(); self.messen.addItem("Text", "text"); self.messen.addItem("Seitenrand", "seitenrand")
        self.messen.setCurrentIndex(0 if w["messen"] == "text" else 1)
        self.messen.currentIndexChanged.connect(self._messen)
        g.reihe(("Gemessen von:", self.messen))
        v.addLayout(g)
        v.addWidget(abschnittstitel("Optionen"))
        self.ausrichten = UmbruchSchalter("Absatzrahmen und Tabellenränder am Seitenrand ausrichten"); self.ausrichten.setChecked(w["ausrichten"])
        self.vordergrund = UmbruchSchalter("Immer im Vordergrund anzeigen"); self.vordergrund.setChecked(w["vordergrund"])
        self.kopf = UmbruchSchalter("Kopfzeile umgeben"); self.kopf.setChecked(w["kopf"])
        self.fuss = UmbruchSchalter("Fußzeile umgeben"); self.fuss.setChecked(w["fuss"])
        og = FormularGitter()
        for c in (self.ausrichten, self.vordergrund, self.kopf, self.fuss):
            og.breit(c)
        v.addLayout(og)
        v.addWidget(abschnittstitel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 150, flaeche=False); self.vorschau.setFixedHeight(150); v.addWidget(self.vorschau)
        v.addStretch(1)
        self._linie = linie
        for c in (self.ausrichten, self.vordergrund, self.kopf, self.fuss):
            c.toggled.connect(lambda *_: self.vorschau.update())
        fussleiste(self, v)
        self._messen()

    def _messen(self, *_) -> None:
        text = self.messen.currentData() == "text"
        self.abstand_gruppe.setText("VOM TEXT" if text else "VOM SEITENRAND")
        self.kopf.setEnabled(text); self.fuss.setEnabled(text)             # Kopf- und Fußzeile gehören zum Text-Bezug
        self.vorschau.update()

    def werte(self) -> dict:
        f = self.felder
        return {"messen": self.messen.currentData(), "abstand": tuple(round(f[k].value() / _PT_MM, 2) for k in ("o", "u", "l", "r")),
                "ausrichten": self.ausrichten.isChecked(), "vordergrund": self.vordergrund.isChecked(), "kopf": self.kopf.isChecked(), "fuss": self.fuss.isChecked()}

    def _male(self, p, rect) -> None:
        """Ein Blatt mit Text; der Rahmen liegt je nach „Gemessen von“ um den Text oder am Blattrand."""
        blatt, text = _blatt_vorschau(p, rect)
        w = self.werte()
        o, u, l, rt = (x * 1.2 for x in w["abstand"])
        p.setPen(QPen(QColor(Farbe.TINTE_DUNKEL), 1)); p.setBrush(Qt.NoBrush)
        if w["messen"] == "text":
            p.drawRect(QRectF(text.left() - l, text.top() - o, text.width() + l + rt, text.height() + o + u))
        else:
            p.drawRect(QRectF(blatt.left() + l, blatt.top() + o, blatt.width() - l - rt, blatt.height() - o - u))


class _AbstandDialog(QDialog):
    """„Optionen …“ am Seitenrand: Abstand des Rahmens vom Seitenrand."""
    def __init__(self, parent, mm: float):
        super().__init__(parent)
        self.setWindowTitle("Rahmen- und Schattierungsoptionen")
        v = QVBoxLayout(self)
        z = QHBoxLayout(); z.addWidget(QLabel("Abstand vom Seitenrand"))
        self.feld = QDoubleSpinBox(); self.feld.setRange(2, 30); self.feld.setSuffix(" mm"); self.feld.setValue(mm)
        z.addWidget(self.feld); v.addLayout(z)
        fussleiste(self, v)

    def wert(self) -> float:
        return self.feld.value()


class _SchattierungSeite(QWidget):
    """Ausfüllen (Farbe) · Muster (Art, Farbe) · Vorschau · Übernehmen für."""
    geaendert = Signal()

    def __init__(self, fuell: str | None, muster: tuple[str, str] | None, fuer: list[str] | None):
        super().__init__()
        g = FormularGitter(self); g.setContentsMargins(10, 10, 10, 10)
        self.fuell = FarbFeld(fuell or "", "Füllfarbe", keine_text="Keine Farbe")
        self.art = QComboBox(); self.art.setIconSize(QSize(16, 16)); self.art.setMaxVisibleItems(18)
        for k, name, _o in M.MUSTER:
            self.art.addItem(_muster_symbol(k), name, k)
        self.farbe = FarbFeld("" if not muster or muster[1] in ("", Farbe.SCHWARZ) else muster[1], "Musterfarbe", keine_text="Automatisch")
        self.vorschau = _Vorschau(kanten_klick=False); self.vorschau.setFixedSize(190, 130)         # klein, in der Mitte
        self.fuer = QComboBox(); self.fuer.addItems(fuer or ["Absatz"])
        g.breit(abschnittstitel("Ausfüllen")); g.breit(self.fuell)
        g.breit(abschnittstitel("Muster")); g.reihe(("Formatvorlage:", self.art)); g.reihe(("Farbe:", self.farbe))
        g.breit(abschnittstitel("Vorschau")); g.breit(mittig(self.vorschau))
        g.reihe(("Übernehmen für:", self.fuer))
        self.art.setCurrentIndex(max(0, self.art.findData(muster[0] if muster else "loeschen")))
        self.art.currentIndexChanged.connect(lambda _i: self._neu())
        self.fuell.farbeGeaendert.connect(lambda _f: self._neu())
        self.farbe.farbeGeaendert.connect(lambda _f: self._neu())
        self._neu()

    def werte(self) -> tuple[str | None, tuple[str, str] | None]:
        k = self.art.currentData()
        muster = None if k == "loeschen" else (k, self.farbe.farbe or Farbe.SCHWARZ)
        return (self.fuell.farbe or None), muster

    def _neu(self) -> None:
        fuell, muster = self.werte()
        self.farbe.setEnabled(muster is not None)
        self.vorschau.pinsel = M.pinsel(muster[0], muster[1], fuell) if muster else (M.pinsel("", Farbe.SCHWARZ, fuell) if fuell else None)
        self.vorschau.update()
        self.geaendert.emit()


# ---------------------------------------------------------------------------------------------------------- Fenster
class RahmenSchattierungDialog(PanelFaehig, QDialog):
    """Das Fenster „Rahmen und Schattierung“. Die Reiter und ihre Werte stehen oben in der Beschreibung des Bausteins."""

    def __init__(self, parent=None, *, rahmen: Linie | None = None, fuell: str | None = None, muster: tuple[str, str] | None = None,
                 seitenrand: dict | None = None, mit_seitenrand: bool = True, fuer: list[str] | None = None, innen_h: bool = True,
                 seite: str = "rahmen"):
        super().__init__(parent)
        self.setWindowTitle("Rahmen und Schattierung")
        self.resize(783, 481)
        v = QVBoxLayout(self)
        self.reiter = AngepassteReiter(); v.addWidget(self.reiter, 1)
        self.p_rahmen = _RahmenSeite(rahmen, innen_h=innen_h, fuer=fuer)
        self.reiter.addTab(self.p_rahmen, "Rahmen")
        self.p_rand = None
        if mit_seitenrand:
            sr = seitenrand or {}
            li = Linie(sr.get("farbe", Farbe.SCHWARZ), float(sr.get("breite_pt", 1.0)), sr.get("art", "einfach"), sr.get("seiten", "tblr")) if seitenrand else None
            self.p_rand = _RahmenSeite(li, seitenrand=True, fuer=["Gesamtes Dokument"], abstand_mm=float(sr.get("abstand_mm", 8.0)))
            if seitenrand:                                                                  # Optionen des vorhandenen Seitenrahmens
                from lunivo_writer.editor.seitenrahmen import abstaende_pt
                self.p_rand.rand_optionen = {"messen": sr.get("messen", "seitenrand"), "abstand": abstaende_pt(sr), "ausrichten": bool(sr.get("ausrichten")),
                                             "vordergrund": sr.get("vordergrund", True), "kopf": bool(sr.get("kopf")), "fuss": bool(sr.get("fuss"))}
                self.p_rand.kunst.setCurrentIndex(max(0, self.p_rand.kunst.findData(sr.get("kunst", ""))))
                self.p_rand._abstand_vorschau()
            self.reiter.addTab(self.p_rand, "Seitenrand")
        self.p_schatt = _SchattierungSeite(fuell, muster, fuer)
        self.reiter.addTab(self.p_schatt, "Schattierung")
        self.reiter.setCurrentIndex({"rahmen": 0, "seitenrand": 1 if mit_seitenrand else 0}.get(seite, self.reiter.count() - 1))
        fussleiste(self, v)

    def passe_an(self, breite: int, hoehe: int) -> None:
        """Vorschau so groß, wie die Seitenleiste Platz hat (neben ihr stehen Farbe und Breite)."""
        for s in (self.p_rahmen, self.p_rand):
            if s is not None:
                s.vorschau.setFixedSize(*((184, 118) if breite >= 400 else (152, 104)))

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
        o = self.p_rand.rand_optionen
        erg = {"art": li.art, "farbe": li.farbe, "breite_pt": li.breite_pt, "abstand_mm": round(sum(o["abstand"]) / 4 / 72 * 25.4, 2),
               "seiten": "".join(c for c in "tblr" if c in self.p_rand.seiten), "messen": o["messen"], "abstand": ",".join(f"{x:g}" for x in o["abstand"]),
               "ausrichten": o["ausrichten"], "vordergrund": o["vordergrund"], "kopf": o["kopf"], "fuss": o["fuss"]}
        if self.p_rand.kunst.currentData():
            erg["kunst"] = self.p_rand.kunst.currentData()
        return erg
