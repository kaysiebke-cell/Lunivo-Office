"""Die Fenster „Nummerierung und Aufzählungszeichen“ und „Nummerierung anpassen“ als Bausteine.

    d = ListenDialog(parent, aktuell=spec | None, seite="aufzaehlung" | "nummerierung")
    if d.exec(): d.ergebnis()          # spec (siehe ``editor.listen``) oder None = „Kein“

    d = NummerierungAnpassenDialog(parent, spec)
    if d.exec(): d.spec()

Die Fenster legen keine Liste an; der Aufrufer (Band, Editor, Formatvorlage) setzt das Ergebnis. Nur das steht darin, was Lunivo
zeichnen und speichern kann: Aufzählung mit Punkt, Kreis oder Quadrat, Nummerierung mit Zahlenart, Text davor und danach und Startzahl, mehrstufige Gliederung (1. / 1.1. / 1.1.1.) mit eigenem Zahlenformat je Ebene.
Eigene Formate merkt sich der Reiter „Benutzerdefinierte Liste“.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QEvent, QObject, QRectF, QSettings, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QPushButton,
    QSpinBox, QTabWidget, QGroupBox, QCheckBox, QSizePolicy, QVBoxLayout, QWidget,
)

import copy

from lunivo_writer.editor import listen as L
from lunivo_writer.editor import mehrstufig as M
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste
from lunivo_writer.ui.baukasten.listen_symbole import liste_zeichner
from lunivo_writer.ui.baukasten.mass_feld import EinheitFeld, spin

from lunivo_writer.core.farben import Farbe
PLATZHALTER = "①"
_SCHLUESSEL = "listen/benutzer"
_KACHEL = QSize(144, 102) # die Kacheln füllen das Raster wie in der Vorlage: vier je Zeile, jede mit Rahmen


def benutzerlisten() -> list[dict]:
    try:
        d = json.loads(str(QSettings().value(_SCHLUESSEL, "[]") or "[]"))
        return [L.liste(x["stil"], x["praefix"], x["suffix"], x["start"]) for x in d if x.get("stil") in L.STILE]
    except (ValueError, KeyError, TypeError):
        return []


def _merke(listen: list[dict]) -> None:
    QSettings().setValue(_SCHLUESSEL, json.dumps(listen, ensure_ascii=False))


def _rahmen(p: QPainter, groesse: QSize) -> None:
    p.setPen(QColor("#c4c9ce")); p.setBrush(Qt.NoBrush); p.drawRect(0, 0, groesse.width() - 1, groesse.height() - 1)


def _bild(spec: dict | None, groesse: QSize = _KACHEL) -> QIcon:
    pm = QPixmap(groesse); pm.fill(QColor("white"))
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(0, 0, groesse.width(), groesse.height())
    if spec is None:                                          # „Kein“: ein kleines Quadrat mit dem Wort darin
        q = QRectF(r.center().x() - 32, r.center().y() - 32, 64, 64)
        p.setPen(QColor("#6c757d")); p.drawRect(q)
        f = p.font(); f.setBold(True); p.setFont(f)
        p.setPen(QColor(Farbe.TINTE_DUNKEL)); p.drawText(q, Qt.AlignCenter, "Kein")
    else:
        liste_zeichner(L.marke(spec))(p, r.adjusted(0, 18, 0, -18))
    _rahmen(p, groesse)
    p.end()
    return QIcon(pm)


def _raster(eintraege: list[dict | None], bild=None) -> QListWidget:
    w = QListWidget(); w.setViewMode(QListView.IconMode); w.setResizeMode(QListView.Adjust); w.setMovement(QListView.Static)
    w.setIconSize(_KACHEL); w.setGridSize(QSize(_KACHEL.width() + 12, _KACHEL.height() + 8)); w.setSpacing(0)
    w.setMinimumHeight(2 * (_KACHEL.height() + 8) + 8)
    for s in eintraege:
        it = QListWidgetItem((bild or _bild)(s), ""); it.setData(Qt.UserRole, s)
        w.addItem(it)
    return w


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.formular_gitter import AngepassteReiter, FormularGitter, UmbruchSchalter, abschnittstitel
class _Zahlenformat(QWidget):
    """Zahlenformat, Zahlenart, Startzahl und „Schriftart …“ der Nummer — gemeinsam für „Nummerierung anpassen“ und „Gliederung anpassen“."""
    geaendert = Signal()

    def __init__(self, tipp: str, breit: bool = False):
        """``breit``: die Anordnung der Gliederung (Zahlenformat und Vorlage über die ganze Breite, „Beginnen mit“ in einer eigenen Zeile;
        „Schriftart …“ setzt der Aufrufer, z. B. neben die vorherige Ebene). Sonst die der einfachen Nummerierung."""
        super().__init__()
        g = FormularGitter(self); g.setContentsMargins(0, 0, 0, 0)
        self.format = QLineEdit(); self.format.setToolTip(tipp)
        self.schrift = QPushButton("Schriftart …"); self.schrift.clicked.connect(self._schriftart)
        self.zeichen: dict = {}
        self.art = QComboBox()
        for k, st in L.STILE.items():
            if not st[1]:
                self.art.addItem(st[0], k)
        self.start = QSpinBox(); self.start.setRange(1, 9999)
        if breit:
            g.reihe(("Zahlenformat:", self.format))
            g.reihe(("Zahlenformatvorlage:", self.art))
            g.zeile("Beginnen mit:", self.start)
        else:
            g.reihe(("Zahlenformat:", self.format))
            g.breit(self.schrift)
            g.reihe(("Zahlenformatvorlage:", self.art), ("Beginnen mit:", self.start), gewichte=(3, 1))
        self.format.textChanged.connect(lambda *_: self.geaendert.emit())
        self.art.currentIndexChanged.connect(lambda *_: self.geaendert.emit())
        self.start.valueChanged.connect(lambda *_: self.geaendert.emit())

    def setze(self, format: str, stil: str, start: int, zeichen: dict | None) -> None:
        for w in (self.format, self.art, self.start):
            w.blockSignals(True)
        self.format.setText(format); self.art.setCurrentIndex(max(0, self.art.findData(stil))); self.start.setValue(start)
        for w in (self.format, self.art, self.start):
            w.blockSignals(False)
        self.zeichen = dict(zeichen or {})

    def _schriftart(self) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        from lunivo_writer.ui.baukasten.schriftart_dialog import ZEICHEN, SchriftartDialog
        d = SchriftartDialog(self, {**ZEICHEN, **(self.zeichen or {})}, umfang="vorlage")

        def fertig() -> None:
            self.zeichen = L.zeichen_filtern(d.werte())
            self.geaendert.emit()
        zeige_unter(self, d, fertig)


class _Positionen(QWidget):
    """Nummernposition (Ausrichtung der Nummer, Abstand) und Textposition (Tabstopp-Leerstelle nach, Einzug bei) — gemeinsam für
    „Nummerierung anpassen“ und „Gliederung anpassen“. Werte in Millimetern."""
    geaendert = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0)
        g1 = QGroupBox("Nummernposition"); a = FormularGitter(g1); a.setContentsMargins(0, 6, 0, 2)
        self.art = QComboBox()
        for k, name in (("links", "Links"), ("mitte", "Zentriert"), ("rechts", "Rechts")):
            self.art.addItem(name, k)
        self.ausr = EinheitFeld(0.0, 0.0, 300.0, ("mm", "cm", "in", "pt"))
        a.breit(self.art); a.zeile("Ausrichtung:", self.ausr)
        g2 = QGroupBox("Textposition"); t = FormularGitter(g2); t.setContentsMargins(0, 6, 0, 2)
        self.tab = EinheitFeld(8.0, 0.0, 300.0, ("mm", "cm", "in", "pt")); self.einzug = EinheitFeld(8.0, 0.0, 300.0, ("mm", "cm", "in", "pt"))
        t.zeile("Tabstopp-Leerstelle nach:", self.tab); t.zeile("Einzug bei:", self.einzug)
        v.addWidget(g1); v.addWidget(g2)
        for sig in (self.art.currentIndexChanged, self.ausr.valueChanged, self.tab.valueChanged, self.einzug.valueChanged):
            sig.connect(lambda *_: self.geaendert.emit())

    def setze(self, ausr: float, art: str, tab: float, einzug: float) -> None:
        ws = (self.art, self.ausr, self.tab, self.einzug)
        for w in ws:
            w.blockSignals(True)
        self.art.setCurrentIndex(max(0, self.art.findData(art))); self.ausr.setValue(ausr); self.tab.setValue(tab); self.einzug.setValue(einzug)
        for w in ws:
            w.blockSignals(False)

    def werte(self) -> dict:
        return {"ausr": self.ausr.value(), "ausr_art": self.art.currentData(), "tab": self.tab.value(), "einzug": self.einzug.value()}


class NummerierungAnpassenDialog(PanelFaehig, QDialog):
    def __init__(self, parent=None, spec: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nummerierung anpassen"); self.resize(359, 403)
        s = L.liste("dezimal") if not spec or L.STILE[spec["stil"]][1] else spec
        v = QVBoxLayout(self)
        self.zf = _Zahlenformat(f"{PLATZHALTER} steht für die Nummer; davor und danach darf Text stehen")
        self.format, self.art, self.start, self.schrift = self.zf.format, self.zf.art, self.zf.start, self.zf.schrift
        v.addWidget(self.zf)
        vg = QGroupBox("Vorschau"); vh = QHBoxLayout(vg)
        self.vorschau = VorschauFlaeche(self._male, 190); self.vorschau.setFixedWidth(200) # schmal und in der Mitte, wie in der Vorlage
        vh.addStretch(1); vh.addWidget(self.vorschau); vh.addStretch(1)
        v.addWidget(vg)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet(('color: ' + Farbe.ORANGE + ';')); v.addWidget(self.hinweis)
        self.mehr = QPushButton("Erweitern"); self.mehr.setCheckable(True); self.mehr.toggled.connect(self._erweitern)
        self.ok = fussleiste(self, v, self.mehr)
        self.position = _Positionen(); v.addWidget(self.position); self.position.setVisible(False)
        pos = s.get("pos") or {}
        self.position.setze(pos.get("ausr", 0.0), pos.get("ausr_art", "links"), pos.get("tab", pos.get("einzug", 8.0)), pos.get("einzug", 8.0))
        self._pos_geaendert = bool(pos)
        self.zf.setze(s["praefix"] + PLATZHALTER + s["suffix"], s["stil"], s["start"], s.get("zeichen"))
        self.zf.geaendert.connect(self._neu)
        self.position.geaendert.connect(self._pos_neu)
        self._neu()

    def _erweitern(self, an: bool) -> None:
        self.mehr.setText("Reduzieren" if an else "Erweitern"); self.position.setVisible(an)
        self.adjustSize()

    def _pos_neu(self) -> None:
        self._pos_geaendert = True
        self._neu()

    def spec(self) -> dict | None:
        t = self.format.text()
        if t.count(PLATZHALTER) != 1:
            return None
        a, b = t.split(PLATZHALTER)
        return L.liste(self.art.currentData(), a, b, self.start.value(), self._zeichen, self.position.werte() if self._pos_geaendert else None)

    @property
    def _zeichen(self) -> dict:
        return self.zf.zeichen

    @_zeichen.setter
    def _zeichen(self, w: dict) -> None:
        self.zf.zeichen = w

    def _neu(self) -> None:
        ok = self.spec() is not None
        self.hinweis.setText("" if ok else f"Das Zahlenformat braucht genau ein {PLATZHALTER} für die Nummer.")
        self.ok.setEnabled(ok)
        self.vorschau.update()

    def _male(self, p, rect) -> None:
        """Vorschau wie in der Vorlage: oben und unten graue Balken, dazwischen drei Nummern mit je zwei schwarzen Zeilen."""
        s = self.spec()
        r = QRectF(rect)
        grau, schwarz = QPen(QColor("#9aa0a6"), 3), QPen(QColor("#111111"), 3)
        for y in (r.top() + 6, r.top() + 20):
            p.setPen(grau); p.drawLine(int(r.left() + 4), int(y), int(r.right() - 4), int(y))
        if s:
            marken = L.marke({**s, "start": 1}).split("|") if L.marke({**s, "start": 1}) else ["", "", ""]
            f = p.font(); f.setPixelSize(13); p.setFont(f)
            y = r.top() + 50
            for t in marken[:3]:
                p.setPen(QColor(Farbe.TINTE_DUNKEL)); p.drawText(QRectF(r.left() + 6, y - 9, 36, 18), Qt.AlignVCenter | Qt.AlignLeft, t)
                p.setPen(schwarz)
                p.drawLine(int(r.left() + 44), int(y), int(r.right() - 6), int(y))
                p.drawLine(int(r.left() + 6), int(y + 16), int(r.right() - 6), int(y + 16))
                y += 38
        for y in (r.bottom() - 20, r.bottom() - 6):
            p.setPen(grau); p.drawLine(int(r.left() + 4), int(y), int(r.right() - 4), int(y))


def _gl_bild(defn: dict | None, groesse: QSize = _KACHEL) -> QIcon:
    """Kachel einer Gliederung: die Ebenen 1 bis 3 mit ihren Nummern."""
    if defn is None:
        return _bild(None, groesse)
    if "ebenen" not in defn:
        return _bild(defn, groesse)
    pm = QPixmap(groesse); pm.fill(QColor("white"))
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    if M.ist_aufzaehlung(defn):                              # Aufzählung mit eigenem Zeichen: drei Zeilen mit dem Zeichen davor
        f = p.font(); f.setPixelSize(16); p.setFont(f)
        for i in range(3):
            y = groesse.height() / 2 - 24 + i * 24
            p.setPen(QColor(Farbe.TINTE)); p.drawText(QRectF(groesse.width() * 0.3, y - 10, 22, 20), Qt.AlignCenter, defn["ebenen"][0]["format"])
            p.setPen(QColor(Farbe.GRAU_HELL)); p.drawLine(int(groesse.width() * 0.3 + 30), int(y), int(groesse.width() * 0.3 + 90), int(y))
        _rahmen(p, groesse); p.end()
        return QIcon(pm)
    zaehler = [0] * M.EBENEN
    f = p.font(); f.setPixelSize(10); p.setFont(f)
    for i, n in enumerate((1, 2, 2, 3)):
        M.zaehlen(zaehler, defn, n)
        t = M.nummer_der_ebene(defn, zaehler, n)
        y = 22 + i * 24
        x = 14 + (n - 1) * 10
        p.setPen(QColor(Farbe.TINTE)); p.drawText(QRectF(x, y - 7, 40, 14), Qt.AlignVCenter | Qt.AlignLeft, t)
        p.setPen(QColor(Farbe.GRAU_HELL)); p.drawLine(int(x + 38), y, groesse.width() - 8, y)
    _rahmen(p, groesse)
    p.end()
    return QIcon(pm)


class GliederungAnpassenDialog(PanelFaehig, QDialog):
    """„Gliederung anpassen“ (auch „Aufzählungszeichen anpassen“): je Ebene Zahlenformat, Zahlenart, Startzahl, Schriftart, Position und Text,
    dazu Nummerieren nach Norm, Verbinden mit Formatvorlage, Text danach und Neu nummerieren nach."""

    def __init__(self, parent=None, defn: dict | None = None, *, titel: str = "Gliederung anpassen"):
        super().__init__(parent)
        self.setWindowTitle(titel); self.resize(718, 348)
        self._e = copy.deepcopy((defn or M.VORLAGEN[0][1])["ebenen"])
        self._ebene = 0
        v = QVBoxLayout(self)
        grp = QGroupBox("Zahlenformat"); g = FormularGitter(grp); g.setContentsMargins(0, 6, 0, 2)
        self.ebenen = QListWidget()                                          # die neun Ebenen in einer Reihe: spart Höhe und Breite
        self.ebenen.setFlow(QListView.LeftToRight); self.ebenen.setWrapping(False); self.ebenen.setSpacing(2)
        self.ebenen.setFixedHeight(40); self.ebenen.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.ebenen.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ebenen.addItems([str(i + 1) for i in range(M.EBENEN)])
        for i in range(self.ebenen.count()):
            self.ebenen.item(i).setSizeHint(QSize(30, 28)); self.ebenen.item(i).setTextAlignment(Qt.AlignCenter)
        g.reihe(("Ebene:", self.ebenen))
        self.zf = _Zahlenformat("① bis ⑨ stehen für die Nummern der Ebenen 1 bis 9", breit=True)
        self.format, self.art, self.start, self.schrift = self.zf.format, self.zf.art, self.zf.start, self.zf.schrift
        g.breit(self.zf)
        self.vorher = QComboBox()
        g.zeile("Vorherige Nummerierungsebene:", self.vorher)
        g.breit(self.schrift)
        v.addWidget(grp)
        v.addWidget(abschnittstitel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 150); v.addWidget(self.vorschau)
        self.mehr = QPushButton("Erweitern"); self.mehr.setCheckable(True); self.mehr.toggled.connect(self._erweitern)
        self.ok = fussleiste(self, v, self.mehr)
 # ---- erweiterter Teil (wie in der Vorlage unter „Reduzieren“)
        self.unten = QWidget(); ug = FormularGitter(self.unten); ug.setContentsMargins(0, 0, 0, 0)
        self.position = _Positionen(); ug.breit(self.position)
        self.norm = UmbruchSchalter("Nummerieren nach Norm")
        self.vorlage = QComboBox(); self.vorlage.addItem("(Keine Formatvorlage)", "")
        from lunivo_writer.editor import stile
        for n in stile.namen():
            self.vorlage.addItem(n, n)
        self.danach = QComboBox()
        for k, name in (("tab", "Tabstoppzeichen"), ("leer", "Leerzeichen"), ("nichts", "Nichts")):
            self.danach.addItem(name, k)
        self.neu = UmbruchSchalter("Neu nummerieren nach:"); self.neu_ebene = QComboBox()
        ug.breit(self.norm)
        ug.zeile("Verbinden mit Formatvorlage:", self.vorlage)
        ug.zeile("Text danach:", self.danach)
        ug.breit(self.neu); ug.breit(self.neu_ebene)
        v.addWidget(self.unten); self.unten.setVisible(False)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet(('color: ' + Farbe.ORANGE + ';')); v.addWidget(self.hinweis)
        self.ebenen.currentRowChanged.connect(self._wechsel)
        for sig in (self.zf.geaendert, self.position.geaendert, self.norm.toggled, self.vorlage.currentIndexChanged, self.danach.currentIndexChanged,
                    self.neu.toggled, self.neu_ebene.currentIndexChanged):
            sig.connect(lambda *_: self._lesen())
        self.vorher.activated.connect(self._vorher_gewaehlt)
        self.ebenen.setCurrentRow(0)

    def _erweitern(self, an: bool) -> None:
        self.mehr.setText("Reduzieren" if an else "Erweitern"); self.unten.setVisible(an)
        self.adjustSize()

    def _wechsel(self, i: int) -> None:
        if i < 0:
            return
        self._ebene = i
        e = self._e[i]
        gesperrt = (self.norm, self.vorlage, self.danach, self.neu, self.neu_ebene)
        for w in gesperrt:
            w.blockSignals(True)
        self.zf.setze(e["format"], e["stil"], e["start"], e.get("zeichen"))
        self.position.setze(e["ausr"], e.get("ausr_art", "links"), e.get("tab", e["einzug"]), e["einzug"])
        self.norm.setChecked(bool(e.get("norm"))); self.vorlage.setCurrentIndex(max(0, self.vorlage.findData(e.get("vorlage", ""))))
        self.danach.setCurrentIndex(max(0, self.danach.findData(e.get("danach", "tab"))))
        self.neu_ebene.clear()
        for k in range(i):
            self.neu_ebene.addItem(f"Ebene {k + 1}", k + 1)
        self.neu.setEnabled(i > 0); self.neu_ebene.setEnabled(i > 0 and e.get("neu") is not None)
        self.neu.setChecked(e.get("neu") is not None and i > 0)
        if e.get("neu") is not None and i > 0:
            self.neu_ebene.setCurrentIndex(max(0, self.neu_ebene.findData(e["neu"])))
        for w in gesperrt:
            w.blockSignals(False)
        self.vorher.clear(); self.vorher.addItem("")
        for k in range(i):
            self.vorher.addItem(f"Ebene {k + 1}", k)
        self.vorher.setEnabled(i > 0)
        self._pruefen()

    def _lesen(self) -> None:
        e = self._e[self._ebene]
        p = self.position.werte()
        e.update(format=self.format.text(), stil=self.art.currentData(), start=self.start.value(), ausr=p["ausr"], einzug=p["einzug"])
        for k, wert, vorgabe in (("tab", p["tab"], p["einzug"]), ("ausr_art", p["ausr_art"], "links"), ("danach", self.danach.currentData(), "tab"),
                                 ("vorlage", self.vorlage.currentData(), ""), ("norm", self.norm.isChecked(), False),
                                 ("neu", self.neu_ebene.currentData() if self.neu.isChecked() and self._ebene > 0 else None, None)):
            if wert == vorgabe or wert is None:
                e.pop(k, None)
            else:
                e[k] = wert
        self.neu_ebene.setEnabled(self._ebene > 0 and self.neu.isChecked())
        if self.zf.zeichen:
            e["zeichen"] = dict(self.zf.zeichen)
        else:
            e.pop("zeichen", None)
        self._pruefen()

    def _vorher_gewaehlt(self, _i: int) -> None:
        k = self.vorher.currentData()
        if k is None:
            return
        zeichen = M.PLATZHALTER[k]
        if zeichen not in self.format.text():
            self.format.setText(zeichen + "." + self.format.text()); self._lesen()

    def _pruefen(self) -> None:
        schlecht = [i + 1 for i, e in enumerate(self._e) if not e["format"]]
        self.hinweis.setText("" if not schlecht else f"Das Zahlenformat der Ebene {schlecht[0]} darf nicht leer sein.")
        self.ok.setEnabled(not schlecht)
        self.vorschau.update()

    def defn(self) -> dict:
        return {"ebenen": [M.ebene_aus(e) for e in self._e]}

    def _male(self, p, rect) -> None:
        """Die neun Ebenen mit ihren Nummern; die gewählte Ebene hat schwarze Linien, die anderen graue (wie in der Vorlage)."""
        d = self.defn()
        zaehler = [0] * M.EBENEN
        r = QRectF(rect).adjusted(10, 8, -10, -8)
        h = r.height() / (M.EBENEN + 1)
        f = p.font(); f.setPixelSize(max(8, int(h * 0.62))); p.setFont(f)
        y = r.top()
        for n in range(1, M.EBENEN + 1):
            M.zaehlen(zaehler, d, n)
            t = M.nummer_der_ebene(d, zaehler, n)
            e = d["ebenen"][n - 1]
            x = r.left() + e["ausr"] * 1.1
            aktuell = n - 1 == self._ebene
            p.setPen(QColor(Farbe.TINTE_DUNKEL)); p.drawText(QRectF(x, y, 120, h), Qt.AlignVCenter | Qt.AlignLeft, t)
            tx = max(r.left() + e.get("tab", e["einzug"]) * 1.1, x + p.fontMetrics().horizontalAdvance(t) + 5)
            pen = QPen(QColor("#111111" if aktuell else Farbe.GRAU_HELL), 3 if aktuell else 3); pen.setCapStyle(Qt.FlatCap)
            p.setPen(pen); p.drawLine(int(tx), int(y + h / 2), int(r.right()), int(y + h / 2))
            if aktuell:                                           # die zweite Zeile des gewählten Absatzes
                y += h * 0.9
                p.drawLine(int(r.left() + e["einzug"] * 1.1), int(y + h / 2), int(r.right()), int(y + h / 2))
            y += h


class _KachelFueller(QObject):
    """Ein Kachelraster füllt seine Breite mit drei Kacheln je Zeile (Größe folgt der Breite) und ist genau so hoch wie seine Zeilen."""

    def __init__(self, raster: QListWidget, spalten: int = 3):
        super().__init__(raster)
        self.r, self.spalten = raster, spalten
        raster.installEventFilter(self); raster.viewport().installEventFilter(self)      # auch die sichtbare Fläche: ihre Breite ist maßgebend
        raster.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); raster.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)       # die Höhe passt genau auf die Zeilen
        self._anpassen()

    def eventFilter(self, obj, ev) -> bool:
        try:
            if ev.type() == QEvent.Resize and obj in (self.r, self.r.viewport()):
                self._anpassen()
        except RuntimeError:                                       # das Raster wird gerade abgebaut
            pass
        return False

    def _anpassen(self) -> None:
        b = max(120, self.r.viewport().width() or self.r.width() - 4)
        zelle = (b - 6) // self.spalten
        icon = QSize(zelle - 8, int((zelle - 8) * 0.7))
        grid = QSize(zelle, icon.height() + 8)
        if self.r.gridSize() != grid:
            self.r.setIconSize(icon); self.r.setGridSize(grid)
        h = -(-self.r.count() // self.spalten) * grid.height() + 2 * self.r.frameWidth() + 6
        if self.r.height() != h:
            self.r.setFixedHeight(h)


class ListenDialog(PanelFaehig, QDialog):
    ALS_PANEL = True                                          # öffnet sich in der Seitenleiste (siehe zusatz_panel)

    def kompakt_machen(self) -> None:
        """Für die schmale Seitenleiste: kleinere Kacheln (drei je Zeile), Reiter zum Rollen, Fenster ohne feste Größe."""
        self._fueller = [_KachelFueller(w, 4) for w in (self.r_punkte, self.r_zahlen, self.r_gl)]       # vier Kacheln je Zeile, die ganze Breite ausgefüllt
        self.liste.setMinimumHeight(56); self.liste.setMaximumHeight(90); self.vorschau.setFixedHeight(84)
        self.reiter.setUsesScrollButtons(True); self.reiter.tabBar().setExpanding(False); self.reiter.tabBar().setElideMode(Qt.ElideNone)
        for i, (kurz, voll) in enumerate((("Aufzählung", "Aufzählungszeichen"), ("Nummern", "Nummerierung"), ("Gliederung", "Gliederung nummeriert"),
                                          ("Eigene", "Benutzerdefinierte Liste"))):
            self.reiter.setTabText(i, kurz); self.reiter.setTabToolTip(i, voll)
        self.setMinimumSize(0, 0)

    def passe_an(self, breite: int, hoehe: int) -> None:
        """Je breiter die Seitenleiste, desto mehr Kacheln je Zeile (vier bis sechs), damit die Auswahl ohne Rollen auskommt."""
        spalten = 6 if breite >= 520 else 5 if breite >= 420 else 4
        for f in getattr(self, "_fueller", []):
            f.spalten = spalten; f._anpassen()

    def __init__(self, parent=None, aktuell: dict | None = None, *, seite: str = "aufzaehlung"):
        super().__init__(parent)
        self.setWindowTitle("Nummerierung und Aufzählungszeichen"); self.resize(694, 435)
        self._benutzer = benutzerlisten()
        v = QVBoxLayout(self)
        self.reiter = AngepassteReiter(); v.addWidget(self.reiter, 1)
        self.r_punkte = _raster([None, L.liste("disc"), L.liste("square")] + [M.aufzaehlung(g) for g in M.GLYPHEN], bild=_gl_bild)
        self.r_zahlen = _raster([None] + [L.liste(*n) for n in L.NUMMERIERUNGEN])
        self.r_gl = _raster([None] + [g for _n, g in M.VORLAGEN], bild=_gl_bild)
        self.reiter.addTab(self.r_punkte, "Aufzählungszeichen"); self.reiter.addTab(self.r_zahlen, "Nummerierung")
        self.reiter.addTab(self.r_gl, "Gliederung nummeriert")
        # ---- Benutzerdefinierte Liste
        b = QWidget(); bg = FormularGitter(b); bg.setContentsMargins(10, 10, 10, 10)
        self.liste = QListWidget(); self.vorschau = VorschauFlaeche(self._male, 150)
        self.liste.setMinimumHeight(110)
        bg.reihe(("Benutzerdefinierte Liste:", self.liste), ("Listenvorschau:", self.vorschau))        # gleich breit wie in der Vorlage, schmal untereinander
        self.reiter.addTab(b, "Benutzerdefinierte Liste")
        self._fuelle_benutzer()
        # ---- Knöpfe
        self.anpassen = QPushButton("Anpassen …"); self.loeschen = QPushButton("Löschen")
        self.anpassen.clicked.connect(self._anpassen); self.loeschen.clicked.connect(self._loeschen)
        gruppe = QWidget(); gh = QHBoxLayout(gruppe); gh.setContentsMargins(0, 0, 0, 0)       # unter allen Reitern dieselbe Zeile, ohne Rahmen
        gh.addStretch(1); gh.addWidget(self.loeschen); gh.addWidget(self.anpassen)
        v.addWidget(gruppe)
        fussleiste(self, v)
        # ---- Anfangsauswahl
        for w in (self.r_punkte, self.r_zahlen, self.r_gl):
            w.setCurrentRow(0)
        if aktuell:
            raster = (self.r_punkte if M.ist_aufzaehlung(aktuell) else self.r_gl) if "ebenen" in aktuell \
                else self.r_punkte if L.STILE[aktuell["stil"]][1] else self.r_zahlen
            i = next((i for i in range(raster.count()) if raster.item(i).data(Qt.UserRole) == aktuell), None)
            if i is None and raster in (self.r_gl, self.r_punkte):
                self._eintragen_gl(aktuell, raster); i = raster.count() - 1
            elif i is None and raster is self.r_zahlen:              # ein eigenes Format: oben in die Auswahl der Nummerierung
                self._eintragen(aktuell); i = raster.count() - 1
            if i is not None:
                raster.setCurrentRow(i)
            self.reiter.setCurrentWidget(raster)
        else:
            self.reiter.setCurrentIndex({"nummerierung": 1}.get(seite, 0))
        self.reiter.currentChanged.connect(self._knoepfe)
        for w in (self.r_punkte, self.r_zahlen, self.r_gl, self.liste):
            w.currentRowChanged.connect(self._knoepfe)
        for w in (self.r_punkte, self.r_zahlen, self.r_gl):
            w.itemDoubleClicked.connect(lambda *_: self.accept())
        self._knoepfe()

    # ---- Benutzerdefiniert
    def _fuelle_benutzer(self) -> None:
        self.liste.clear()
        if not self._benutzer:
            self.liste.addItem("Keine Liste"); return
        for s in self._benutzer:
            it = QListWidgetItem(L.marke(s).replace("|", "  ")); it.setData(Qt.UserRole, s); self.liste.addItem(it)

    def _male(self, p, rect) -> None:
        it = self.liste.currentItem()
        s = it.data(Qt.UserRole) if it else None
        if s:
            liste_zeichner(L.marke(s))(p, QRectF(rect).adjusted(50, 10, -50, -10))
        else:
            p.setPen(QColor(Farbe.TINTE)); f = p.font(); f.setPointSize(18); p.setFont(f)
            p.drawText(QRectF(rect), Qt.AlignCenter, "Keine")

    def _eintragen(self, s: dict) -> None:
        """Ein selbst angepasstes Format kommt in den Reiter „Nummerierung“ und in die Liste der eigenen Formate."""
        it = QListWidgetItem(_bild(s), ""); it.setData(Qt.UserRole, s); self.r_zahlen.addItem(it)
        if s not in self._benutzer:
            self._benutzer.append(s); _merke(self._benutzer); self._fuelle_benutzer()

    def _eintragen_gl(self, d: dict, raster: QListWidget | None = None) -> None:
        it = QListWidgetItem(_gl_bild(d), ""); it.setData(Qt.UserRole, d); (raster or self.r_gl).addItem(it)

    def _aktuell(self) -> QWidget:
        return self.reiter.currentWidget()

    def _auswahl(self) -> dict | None:
        w = self._aktuell()
        it = w.currentItem() if isinstance(w, QListWidget) else self.liste.currentItem()
        return it.data(Qt.UserRole) if it else None

    def _knoepfe(self, *_) -> None:
        s = self._auswahl()
        self.anpassen.setEnabled(s is not None)
        self.loeschen.setVisible(self._aktuell() not in (self.r_punkte, self.r_zahlen, self.r_gl))
        self.loeschen.setEnabled(s is not None)
        self.vorschau.update()

    def _anpassen(self) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        s = self._auswahl()
        if s is not None and "ebenen" not in s and L.STILE[s["stil"]][1]:      # Punkt, Kreis, Quadrat: als eigenes Zeichen anpassen
            s = M.aufzaehlung({"disc": "●", "circle": "○", "square": "■"}[s["stil"]])
        if s is not None and "ebenen" in s:
            bullets = M.ist_aufzaehlung(s)
            g = GliederungAnpassenDialog(self, s, titel="Aufzählungszeichen anpassen" if bullets else "Gliederung anpassen")

            def fertig_gl() -> None:
                ziel = self.r_punkte if M.ist_aufzaehlung(g.defn()) else self.r_gl
                self._eintragen_gl(g.defn(), ziel)
                self.reiter.setCurrentWidget(ziel); ziel.setCurrentRow(ziel.count() - 1)
            zeige_unter(self, g, fertig_gl)
            return
        d = NummerierungAnpassenDialog(self, s)

        def fertig_nr() -> None:
            if d.spec():
                self._eintragen(d.spec())
                self.reiter.setCurrentWidget(self.r_zahlen); self.r_zahlen.setCurrentRow(self.r_zahlen.count() - 1)
        zeige_unter(self, d, fertig_nr)

    def _loeschen(self) -> None:
        s = self._auswahl()
        if s in self._benutzer:
            self._benutzer.remove(s); _merke(self._benutzer); self._fuelle_benutzer()
        self._knoepfe()

    def ergebnis(self) -> dict | None:
        """Die gewählte Liste, oder None bei „Kein“."""
        return self._auswahl()


def kachel_bild(spec: dict | None, groesse: QSize) -> QIcon:
    """Dieselbe Kachel wie im Fenster „Nummerierung und Aufzählungszeichen“, verkleinert für die Auswahl im Band."""
    pm = _gl_bild(spec).pixmap(_KACHEL).scaled(groesse, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return QIcon(pm)


def aufzaehlungen() -> list:
    """Die Aufzählungsarten der Auswahl: Punkt, Quadrat und die Zeichen ◆ ✤ ➤ ✓ ✧ (wie im Fenster)."""
    return [L.liste("disc"), L.liste("square")] + [M.aufzaehlung(g) for g in M.GLYPHEN]


def nummerierungen() -> list:
    return [L.liste(*n) for n in L.NUMMERIERUNGEN]
