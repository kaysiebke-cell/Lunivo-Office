"""Die Popups für ein markiertes Bild oder eine Form: Formstile, Füllung, Kontur (wie in der Vorlage).

    FuellMenue()    → gewaehlt(QColor | None), verlauf_gewaehlt(QColor), muster_gewaehlt(str)
    KonturMenue()   → gewaehlt(QColor | None), breite_gewaehlt(float pt), strich_gewaehlt(str), weitere_linien()
    formstile()     → RasterAuswahl mit 7 × 6 Stilen; gewaehlt(Schlüssel); ``formstil_werte(schluessel)`` übersetzt in Füllung und Kontur

Die Menüs bauen auf den vorhandenen Bausteinen auf (``FarbPalette``, ``RasterAuswahl``, ``Linie``, ``muster``) und ändern nichts am Objekt:
sie melden die Wahl, ``editor/bildlayout.py`` schreibt sie ins Bild.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu

from lunivo_writer.editor import muster as M
from lunivo_writer.editor.linie import LINIENBREITEN, Linie
from lunivo_writer.ui.baukasten.farbpalette import FarbPalette
from lunivo_writer.ui.baukasten.linien import linien_menue_zeile, linien_symbol
from lunivo_writer.ui.baukasten.raster_auswahl import RasterAuswahl

from lunivo_writer.editor.linie import OBJEKT_STRICHE as STRICHARTEN                        # die eine Liste der Strichlinien (editor/linie.py)
from lunivo_writer.core.farben import Farbe
STIL_FARBEN = [Farbe.TINTE_DUNKEL, "#4c9be8", "#f08c00", Farbe.GRAU, "#fcc419", "#3b5bdb", "#51cf66"]       # sieben Spalten der Vorlage
STIL_ZEILEN = ["hell", "voll", "voll2", "getoent", "kante", "dunkel"]


def _linien_symbol(art: str, breite: float, groesse: QSize = QSize(120, 16)) -> QIcon:
    return linien_symbol(art, groesse, Farbe.TINTE, breite)                # der vorhandene Baustein


def _textur(name: str, groesse: int = 26) -> QPixmap:
    """Eine kleine, selbst gezeichnete Textur (Vorschau und Füllung): ``papier``, ``granit``, ``holz``, ``stoff``, ``marmor``, ``sand``."""
    import random
    rnd = random.Random(name)
    pm = QPixmap(groesse, groesse)
    basis = {"papier": QColor("#f1ead8"), "granit": QColor("#9a9a9a"), "holz": QColor("#c8955a"), "stoff": QColor("#8aa4c8"),
             "marmor": QColor("#e6e6ea"), "sand": QColor("#e3cf9f")}[name]
    pm.fill(basis)
    p = QPainter(pm)
    for _ in range(groesse * 3):
        x, y = rnd.randrange(groesse), rnd.randrange(groesse)
        d = rnd.randint(-28, 28)
        p.setPen(QColor(max(0, min(255, basis.red() + d)), max(0, min(255, basis.green() + d)), max(0, min(255, basis.blue() + d))))
        if name == "holz":
            p.drawLine(0, y, groesse, y + rnd.randint(-1, 1))
        elif name == "stoff":
            p.drawLine(x, 0, x, groesse); p.drawLine(0, y, groesse, y)
        else:
            p.drawPoint(x, y)
    p.end()
    return pm


TEXTUREN = [("papier", "Papier"), ("granit", "Granit"), ("holz", "Holz"), ("stoff", "Stoff"), ("marmor", "Marmor"), ("sand", "Sand")]
GRADUELL = [("#e03131", "#ffc9c9"), ("#f08c00", "#ffe8cc"), ("#f2c200", "#fff3bf"), (Farbe.GRUEN, "#d3f9d8"), ("#1971c2", "#d0ebff"), ("#7048e8", "#e5dbff"),
            (Farbe.TINTE_DUNKEL, "#dee2e6"), (Farbe.GRAU, "#f8f9fa")]


def graduell_pixmap(dunkel: str, hell: str, w: int = 34, h: int = 24) -> QPixmap:
    from PySide6.QtGui import QLinearGradient
    pm = QPixmap(w, h); p = QPainter(pm)
    g = QLinearGradient(0, 0, 0, h); g.setColorAt(0, QColor(hell)); g.setColorAt(1, QColor(dunkel))
    p.fillRect(pm.rect(), g); p.end()
    return pm


class FuellMenue(FarbPalette):
    """Füllung wie in der Vorlage: Keine Farbe · Thema-Farben · Standard-Farben · Farbverlauf · Automatisch · Weitere Füllfarben · Pipette ·
    Graduell · Textur · Muster · Bild."""
    muster_gewaehlt = Signal(str)
    graduell_gewaehlt = Signal(str, str)        # dunkle, helle Farbe
    textur_gewaehlt = Signal(str)
    bild_gewaehlt = Signal()
    weitere_fuellung = Signal(str)              # „verlauf“, „textur“, „muster“: die Seitenleiste „Formatierung“ mit dieser Füllungsart öffnen

    def __init__(self, parent=None, start=None):
        super().__init__(parent, keine_text="Keine Farbe", start=start, titel="Füllfarbe", verlauf=True, verlauf_titel="Farbverlauf",
                         weitere_text="Weitere Füllfarben(M)…", automatisch="Automatisch", zuletzt=False)
        self.addSeparator()
        for text, art in (("Graduell", "verlauf"), ("Textur", "textur"), ("Muster(N)", "muster")):     # öffnen die Seitenleiste „Formatierung“
            self.addAction(text).triggered.connect(lambda _=False, a=art: (self.close(), self.weitere_fuellung.emit(a)))
        self.addAction("Fülleffekte…").triggered.connect(lambda: (self.close(), self.weitere_fuellung.emit("verlauf")))
        self.addAction("Bild(P)").triggered.connect(lambda: (self.close(), self.bild_gewaehlt.emit()))

    def _untermenue(self, text: str, icon: str) -> QMenu:
        m = self.addMenu(text)
        return m

    @staticmethod
    def _einsetzen(menue: QMenu, inhalt: RasterAuswahl) -> None:
        """Das Raster steht als Inhalt des Untermenüs."""
        from PySide6.QtWidgets import QWidgetAction
        a = QWidgetAction(menue); a.setDefaultWidget(inhalt._wid); menue.addAction(a)


class KonturMenue(FarbPalette):
    """Kontur wie in der Vorlage: Keine Linie · Thema-Farben · Standard-Farben · Farbverlauf · Weitere Linienfarben · Pipette · Linienart ▸ · Strichart ▸ · Pfeilart ▸."""
    breite_gewaehlt = Signal(float)
    strich_gewaehlt = Signal(str)
    weitere_linien = Signal()

    def __init__(self, parent=None, start=None):
        super().__init__(parent, keine_text="Keine Linie", start=start, titel="Linienfarbe", verlauf=True, verlauf_titel="Farbverlauf",
                         weitere_text="Weitere Linienfarben(M)…", zuletzt=False)
        self.verlauf_gewaehlt.connect(self.gewaehlt)               # in der Kontur ist der „Farbverlauf“ eine Reihe Farben
        self.addSeparator()
        art = self.addMenu("Linienart(W)")
        for b in LINIENBREITEN:                                    # „0,25 pt.“ und die Linie in dieser Stärke, wie in der Vorlage
            linien_menue_zeile(art, f"{b:g}".replace(".", ",") + " pt.", "einfach", b, lambda b=b: self.breite_gewaehlt.emit(b))
        art.addSeparator()
        art.addAction("Weitere Linien(M)…", self.weitere_linien.emit)
        strich = self.addMenu("Strichart")
        for schl, _name in STRICHARTEN:                            # nur die Linie in ihrer Art, ohne Text — alle Strichlinien des Bausteins ``Linie``
            linien_menue_zeile(strich, "", schl, 1.5, lambda s=schl: self.strich_gewaehlt.emit(s))
        pfeil = self.addMenu("Pfeilart"); pfeil.setEnabled(False)                # wie in der Vorlage: nur für Linien und Pfeile, nicht für Bilder


# ---- Formstile ----------------------------------------------------------------------------------------------------------------
def formstil_werte(schluessel: str) -> dict:
    """Füllung und Kontur des Stils ``z{Zeile}{Spalte}``: {"fuell": …, "rand": …} (leer = nicht ändern)."""
    zeile, spalte = int(schluessel[1]), int(schluessel[2])
    farbe = QColor(STIL_FARBEN[spalte])
    hell = QColor(farbe.red() + (255 - farbe.red()) * 0.8, farbe.green() + (255 - farbe.green()) * 0.8, farbe.blue() + (255 - farbe.blue()) * 0.8)
    if zeile == 0:                                         # weiß, Rand in der Farbe
        return {"fuell": None, "rand": {"b": 2.0, "farbe": farbe.name(), "art": "einfach"}}
    if zeile == 1:                                         # Fläche in der Farbe
        return {"fuell": {"art": "farbe", "farbe": farbe.name()}, "rand": None}
    if zeile == 2:                                         # Fläche und gleiche Kante, dicker
        return {"fuell": {"art": "farbe", "farbe": farbe.name()}, "rand": {"b": 3.0, "farbe": farbe.darker(130).name(), "art": "einfach"}}
    if zeile == 3:                                         # hell getönt
        return {"fuell": {"art": "farbe", "farbe": hell.name()}, "rand": {"b": 1.0, "farbe": farbe.name(), "art": "einfach"}}
    if zeile == 4:                                         # Verlauf
        return {"fuell": {"art": "verlauf", "farbe": farbe.name()}, "rand": None}
    return {"fuell": {"art": "farbe", "farbe": farbe.darker(160).name()}, "rand": {"b": 1.5, "farbe": farbe.name(), "art": "einfach"}}


def formstil_zeichner(schluessel: str):
    def zeichne(p: QPainter, r: QRectF) -> None:
        w = formstil_werte(schluessel)
        kachel = r.adjusted(2, 2, -2, -2)
        p.save(); p.setRenderHint(QPainter.Antialiasing)
        f = w["fuell"]
        if f:
            if f["art"] == "verlauf":
                from PySide6.QtGui import QLinearGradient
                g = QLinearGradient(kachel.topLeft(), kachel.bottomLeft()); g.setColorAt(0, QColor(f["farbe"]).lighter(150)); g.setColorAt(1, QColor(f["farbe"]))
                p.setBrush(g)
            else:
                p.setBrush(QColor(f["farbe"]))
        else:
            p.setBrush(QColor("white"))
        p.setPen(QPen(QColor(w["rand"]["farbe"]), min(3.0, w["rand"]["b"])) if w["rand"] else Qt.NoPen)
        p.drawRoundedRect(kachel, 4, 4)
        light = f is None or (f["art"] == "farbe" and QColor(f["farbe"]).lightness() > 170)
        p.setPen(QColor(Farbe.TINTE_DUNKEL) if light else QColor("white")); p.drawText(kachel, Qt.AlignCenter, "Abc")
        p.restore()
    return zeichne


def formstile(parent=None) -> RasterAuswahl:
    """Das Popup „Formstile“: sechs Zeilen zu sieben Stilen; ``gewaehlt`` meldet ``z{Zeile}{Spalte}``."""
    m = RasterAuswahl(parent, spalten=len(STIL_FARBEN), groesse=QSize(46, 32))
    for z in range(len(STIL_ZEILEN)):
        for s in range(len(STIL_FARBEN)):
            k = f"z{z}{s}"
            m.kachel(k, "Abc", formstil_zeichner(k))
    return m                                               # darunter steht „Weitere Effekte(O)…“ (``m.fuss``), wie in der Vorlage
