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

from PySide6.QtCore import QRectF, QSettings, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QPushButton,
    QSpinBox, QTabWidget, QGroupBox, QVBoxLayout, QWidget,
)

import copy

from lunivo_writer.editor import listen as L
from lunivo_writer.editor import mehrstufig as M
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche
from lunivo_writer.ui.baukasten.listen_symbole import liste_zeichner
from lunivo_writer.ui.baukasten.mass_feld import spin

PLATZHALTER = "①"
_SCHLUESSEL = "listen/benutzer"
_KACHEL = QSize(120, 84)


def benutzerlisten() -> list[dict]:
    try:
        d = json.loads(str(QSettings().value(_SCHLUESSEL, "[]") or "[]"))
        return [L.liste(x["stil"], x["praefix"], x["suffix"], x["start"]) for x in d if x.get("stil") in L.STILE]
    except (ValueError, KeyError, TypeError):
        return []


def _merke(listen: list[dict]) -> None:
    QSettings().setValue(_SCHLUESSEL, json.dumps(listen, ensure_ascii=False))


def _bild(spec: dict | None, groesse: QSize = _KACHEL) -> QIcon:
    pm = QPixmap(groesse); pm.fill(QColor("white"))
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(0, 0, groesse.width(), groesse.height())
    if spec is None:
        p.setPen(QColor("#343a40")); p.drawText(r, Qt.AlignCenter, "Kein")
    else:
        liste_zeichner(L.marke(spec))(p, r.adjusted(0, 14, 0, -14))
    p.end()
    return QIcon(pm)


def _raster(eintraege: list[dict | None], bild=None) -> QListWidget:
    w = QListWidget(); w.setViewMode(QListView.IconMode); w.setResizeMode(QListView.Adjust); w.setMovement(QListView.Static)
    w.setIconSize(_KACHEL); w.setGridSize(QSize(_KACHEL.width() + 14, _KACHEL.height() + 12)); w.setSpacing(2)
    w.setMinimumHeight(2 * (_KACHEL.height() + 12) + 8)
    for s in eintraege:
        it = QListWidgetItem((bild or _bild)(s), ""); it.setData(Qt.UserRole, s)
        w.addItem(it)
    return w


class NummerierungAnpassenDialog(QDialog):
    def __init__(self, parent=None, spec: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nummerierung anpassen")
        s = L.liste("dezimal") if not spec or L.STILE[spec["stil"]][1] else spec
        v = QVBoxLayout(self)
        g = QGridLayout(); g.setHorizontalSpacing(12)
        g.addWidget(QLabel("Zahlenformat:"), 0, 0, 1, 2)
        self.format = QLineEdit(); self.format.setToolTip(f"{PLATZHALTER} steht für die Nummer; davor und danach darf Text stehen")
        self.schrift = QPushButton("Schriftart …"); self.schrift.clicked.connect(self._schriftart)
        self._zeichen = dict(s.get("zeichen") or {})
        g.addWidget(self.format, 1, 0); g.addWidget(self.schrift, 1, 1)
        g.addWidget(QLabel("Zahlenformatvorlage:"), 2, 0); g.addWidget(QLabel("Beginnen mit:"), 2, 1)
        self.art = QComboBox()
        for k in L.STILE:
            if not L.STILE[k][1]:
                self.art.addItem(L.STILE[k][0], k)
        self.start = QSpinBox(); self.start.setRange(1, 9999)
        g.addWidget(self.art, 3, 0); g.addWidget(self.start, 3, 1)
        g.setColumnStretch(0, 1)
        v.addLayout(g)
        v.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 100); v.addWidget(self.vorschau)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet("color: #e8590c;"); v.addWidget(self.hinweis)
        zu = QHBoxLayout(); zu.addStretch(1)
        ab, self.ok = QPushButton("Abbrechen"), QPushButton("OK"); self.ok.setDefault(True)
        ab.clicked.connect(self.reject); self.ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(self.ok); v.addLayout(zu)
        self.format.setText(s["praefix"] + PLATZHALTER + s["suffix"])
        self.art.setCurrentIndex(max(0, self.art.findData(s["stil"]))); self.start.setValue(s["start"])
        for sig in (self.format.textChanged, self.art.currentIndexChanged, self.start.valueChanged):
            sig.connect(lambda *_: self._neu())
        self._neu()

    def spec(self) -> dict | None:
        t = self.format.text()
        if t.count(PLATZHALTER) != 1:
            return None
        a, b = t.split(PLATZHALTER)
        return L.liste(self.art.currentData(), a, b, self.start.value(), self._zeichen)

    def _schriftart(self) -> None:
        """Schriftart der Nummern: dasselbe Fenster wie im Band, mit den Feldern, die für Nummern gelten."""
        from lunivo_writer.ui.baukasten.schriftart_dialog import SchriftartDialog
        d = SchriftartDialog(self, {k: self._zeichen.get(k, v) for k, v in
                                    (("schrift", ""), ("fett", False), ("kursiv", False), ("groesse", 0.0), ("farbe", ""))}, umfang="vorlage")
        if d.exec():
            w = d.werte()
            self._zeichen = {k: w[k] for k in L.ZEICHEN_FELDER if w[k]}
            self._neu()

    def _neu(self) -> None:
        ok = self.spec() is not None
        self.hinweis.setText("" if ok else f"Das Zahlenformat braucht genau ein {PLATZHALTER} für die Nummer.")
        self.ok.setEnabled(ok)
        self.vorschau.update()

    def _male(self, p, rect) -> None:
        s = self.spec()
        if s:
            liste_zeichner(L.marke({**s, "start": 1}))(p, QRectF(rect).adjusted(40, 4, -40, -4))


def _gl_bild(defn: dict | None, groesse: QSize = _KACHEL) -> QIcon:
    """Kachel einer Gliederung: die Ebenen 1 bis 3 mit ihren Nummern."""
    if defn is None:
        return _bild(None, groesse)
    pm = QPixmap(groesse); pm.fill(QColor("white"))
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    zaehler = [0] * M.EBENEN
    f = p.font(); f.setPixelSize(10); p.setFont(f)
    for i, n in enumerate((1, 2, 2, 3)):
        M.zaehlen(zaehler, defn, n)
        t = M.nummer_der_ebene(defn, zaehler, n)
        y = 14 + i * 17
        x = 8 + (n - 1) * 8
        p.setPen(QColor("#343a40")); p.drawText(QRectF(x, y - 7, 40, 14), Qt.AlignVCenter | Qt.AlignLeft, t)
        p.setPen(QColor("#adb5bd")); p.drawLine(int(x + 38), y, groesse.width() - 8, y)
    p.end()
    return QIcon(pm)


class GliederungAnpassenDialog(QDialog):
    """„Gliederung anpassen“: je Ebene Zahlenformat, Zahlenart, Startzahl, Schriftart der Nummer, Nummernposition und Einzug."""

    def __init__(self, parent=None, defn: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Gliederung anpassen"); self.setMinimumWidth(760)
        self._e = copy.deepcopy((defn or M.VORLAGEN[0][1])["ebenen"])
        self._ebene = 0
        v = QVBoxLayout(self)
        oben = QHBoxLayout()
        grp = QGroupBox("Zahlenformat"); g = QGridLayout(grp)
        self.ebenen = QListWidget(); self.ebenen.setFixedWidth(46)
        self.ebenen.addItems([str(i + 1) for i in range(M.EBENEN)])
        g.addWidget(QLabel("Ebene:"), 0, 0); g.addWidget(self.ebenen, 1, 0, 6, 1)
        g.addWidget(QLabel("Zahlenformat:"), 0, 1, 1, 2)
        self.format = QLineEdit(); self.format.setToolTip("① bis ⑨ stehen für die Nummern der Ebenen 1 bis 9")
        g.addWidget(self.format, 1, 1, 1, 2)
        g.addWidget(QLabel("Zahlenformatvorlage:"), 2, 1, 1, 2)
        self.art = QComboBox()
        for k, st in L.STILE.items():
            if not st[1]:
                self.art.addItem(st[0], k)
        g.addWidget(self.art, 3, 1, 1, 2)
        g.addWidget(QLabel("Beginnen mit:"), 4, 1); self.start = QSpinBox(); self.start.setRange(1, 9999); g.addWidget(self.start, 4, 2)
        g.addWidget(QLabel("Vorherige Nummerierungsebene:"), 5, 1, 1, 2)
        self.vorher = QComboBox(); self.schrift = QPushButton("Schriftart …")
        g.addWidget(self.vorher, 6, 1); g.addWidget(self.schrift, 6, 2)
        g.setColumnStretch(1, 1)
        oben.addWidget(grp, 3)
        vs = QVBoxLayout(); vs.addWidget(QLabel("Vorschau"))
        self.vorschau = VorschauFlaeche(self._male, 230); vs.addWidget(self.vorschau); oben.addLayout(vs, 2)
        v.addLayout(oben)
        zu = QHBoxLayout()
        self.mehr = QPushButton("Erweitern"); self.mehr.setCheckable(True); self.mehr.toggled.connect(self._erweitern)
        zu.addWidget(self.mehr); zu.addStretch(1)
        ab, self.ok = QPushButton("Abbrechen"), QPushButton("OK"); self.ok.setDefault(True)
        ab.clicked.connect(self.reject); self.ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(self.ok); v.addLayout(zu)
        self.position = QGroupBox("Position"); pg = QGridLayout(self.position)
        self.ausr = spin(0.0, 0.0, 200.0); self.einzug = spin(0.0, 0.0, 300.0)
        pg.addWidget(QLabel("Nummer beginnt bei:"), 0, 0); pg.addWidget(self.ausr, 0, 1)
        pg.addWidget(QLabel("Text beginnt bei (Einzug):"), 1, 0); pg.addWidget(self.einzug, 1, 1)
        v.addWidget(self.position); self.position.setVisible(False)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet("color: #e8590c;"); v.addWidget(self.hinweis)
        self.ebenen.currentRowChanged.connect(self._wechsel)
        for sig in (self.format.textEdited, self.art.currentIndexChanged, self.start.valueChanged, self.ausr.valueChanged, self.einzug.valueChanged):
            sig.connect(lambda *_: self._lesen())
        self.vorher.activated.connect(self._vorher_gewaehlt)
        self.schrift.clicked.connect(self._schriftart)
        self.ebenen.setCurrentRow(0)

    def _erweitern(self, an: bool) -> None:
        self.mehr.setText("Reduzieren" if an else "Erweitern"); self.position.setVisible(an)
        self.adjustSize()

    def _wechsel(self, i: int) -> None:
        if i < 0:
            return
        self._ebene = i
        e = self._e[i]
        for w in (self.format, self.art, self.start, self.ausr, self.einzug):
            w.blockSignals(True)
        self.format.setText(e["format"]); self.art.setCurrentIndex(max(0, self.art.findData(e["stil"])))
        self.start.setValue(e["start"]); self.ausr.setValue(e["ausr"]); self.einzug.setValue(e["einzug"])
        for w in (self.format, self.art, self.start, self.ausr, self.einzug):
            w.blockSignals(False)
        self.vorher.clear(); self.vorher.addItem("")
        for k in range(i):
            self.vorher.addItem(f"Ebene {k + 1}", k)
        self.vorher.setEnabled(i > 0)
        self._pruefen()

    def _lesen(self) -> None:
        e = self._e[self._ebene]
        e.update(format=self.format.text(), stil=self.art.currentData(), start=self.start.value(), ausr=self.ausr.value(), einzug=self.einzug.value())
        self._pruefen()

    def _vorher_gewaehlt(self, _i: int) -> None:
        k = self.vorher.currentData()
        if k is None:
            return
        zeichen = M.PLATZHALTER[k]
        if zeichen not in self.format.text():
            self.format.setText(zeichen + "." + self.format.text()); self._lesen()

    def _schriftart(self) -> None:
        from lunivo_writer.ui.baukasten.schriftart_dialog import SchriftartDialog
        z = self._e[self._ebene].get("zeichen") or {}
        d = SchriftartDialog(self, {k: z.get(k, v) for k, v in (("schrift", ""), ("fett", False), ("kursiv", False), ("groesse", 0.0), ("farbe", ""))},
                             umfang="vorlage")
        if d.exec():
            w = d.werte()
            neu = {k: w[k] for k in L.ZEICHEN_FELDER if w[k]}
            if neu:
                self._e[self._ebene]["zeichen"] = neu
            else:
                self._e[self._ebene].pop("zeichen", None)

    def _pruefen(self) -> None:
        schlecht = [i + 1 for i, e in enumerate(self._e) if M.PLATZHALTER[i] not in e["format"]]
        self.hinweis.setText("" if not schlecht else f"Das Zahlenformat der Ebene {schlecht[0]} braucht {M.PLATZHALTER[schlecht[0] - 1]} für die Nummer.")
        self.ok.setEnabled(not schlecht)
        self.vorschau.update()

    def defn(self) -> dict:
        return {"ebenen": [M.ebene(e["stil"], e["format"], e["start"], e["ausr"], e["einzug"], e.get("zeichen")) for e in self._e]}

    def _male(self, p, rect) -> None:
        d = self.defn()
        zaehler = [0] * M.EBENEN
        r = QRectF(rect).adjusted(8, 6, -8, -6)
        h = r.height() / M.EBENEN
        f = p.font(); f.setPixelSize(max(8, int(h * 0.7))); p.setFont(f)
        for n in range(1, M.EBENEN + 1):
            M.zaehlen(zaehler, d, n)
            t = M.nummer_der_ebene(d, zaehler, n)
            x = r.left() + d["ebenen"][n - 1]["ausr"] * 1.1
            y = r.top() + h * (n - 0.5)
            p.setPen(QColor("#343a40")); p.drawText(QRectF(x, y - h / 2, 100, h), Qt.AlignVCenter | Qt.AlignLeft, t)
            tx = r.left() + d["ebenen"][n - 1]["einzug"] * 1.1
            p.setPen(QColor("#adb5bd")); p.drawLine(int(max(tx, x + p.fontMetrics().horizontalAdvance(t) + 4)), int(y), int(r.right()), int(y))


class ListenDialog(QDialog):
    def __init__(self, parent=None, aktuell: dict | None = None, *, seite: str = "aufzaehlung"):
        super().__init__(parent)
        self.setWindowTitle("Nummerierung und Aufzählungszeichen"); self.resize(620, 400)
        self._benutzer = benutzerlisten()
        v = QVBoxLayout(self)
        self.reiter = QTabWidget(); v.addWidget(self.reiter, 1)
        self.r_punkte = _raster([None] + [L.liste(k) for k in L.AUFZAEHLUNGEN])
        self.r_zahlen = _raster([None] + [L.liste(*n) for n in L.NUMMERIERUNGEN])
        self.r_gl = _raster([None] + [g for _n, g in M.VORLAGEN], bild=_gl_bild)
        self.reiter.addTab(self.r_punkte, "Aufzählungszeichen"); self.reiter.addTab(self.r_zahlen, "Nummerierung")
        self.reiter.addTab(self.r_gl, "Gliederung nummeriert")
        # ---- Benutzerdefinierte Liste
        b = QWidget(); bg = QGridLayout(b)
        bg.addWidget(QLabel("Benutzerdefinierte Liste:"), 0, 0); bg.addWidget(QLabel("Listenvorschau:"), 0, 1)
        self.liste = QListWidget(); self.vorschau = VorschauFlaeche(self._male, 150)
        bg.addWidget(self.liste, 1, 0); bg.addWidget(self.vorschau, 1, 1)
        self.reiter.addTab(b, "Benutzerdefinierte Liste")
        self._fuelle_benutzer()
        # ---- Knöpfe
        zu = QHBoxLayout()
        self.anpassen = QPushButton("Anpassen …"); self.loeschen = QPushButton("Löschen")
        self.anpassen.clicked.connect(self._anpassen); self.loeschen.clicked.connect(self._loeschen)
        zu.addWidget(self.anpassen); zu.addWidget(self.loeschen); zu.addStretch(1)
        ab, ok = QPushButton("Abbrechen"), QPushButton("OK"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(ok); v.addLayout(zu)
        # ---- Anfangsauswahl
        for w in (self.r_punkte, self.r_zahlen, self.r_gl):
            w.setCurrentRow(0)
        if aktuell:
            raster = self.r_gl if "ebenen" in aktuell else self.r_punkte if L.STILE[aktuell["stil"]][1] else self.r_zahlen
            i = next((i for i in range(raster.count()) if raster.item(i).data(Qt.UserRole) == aktuell), None)
            if i is None and raster is self.r_gl:
                self._eintragen_gl(aktuell); i = raster.count() - 1
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
            p.setPen(QColor("#343a40")); f = p.font(); f.setPointSize(18); p.setFont(f)
            p.drawText(QRectF(rect), Qt.AlignCenter, "Keine")

    def _eintragen(self, s: dict) -> None:
        """Ein selbst angepasstes Format kommt in den Reiter „Nummerierung“ und in die Liste der eigenen Formate."""
        it = QListWidgetItem(_bild(s), ""); it.setData(Qt.UserRole, s); self.r_zahlen.addItem(it)
        if s not in self._benutzer:
            self._benutzer.append(s); _merke(self._benutzer); self._fuelle_benutzer()

    def _eintragen_gl(self, d: dict) -> None:
        it = QListWidgetItem(_gl_bild(d), ""); it.setData(Qt.UserRole, d); self.r_gl.addItem(it)

    def _aktuell(self) -> QWidget:
        return self.reiter.currentWidget()

    def _auswahl(self) -> dict | None:
        w = self._aktuell()
        it = w.currentItem() if isinstance(w, QListWidget) else self.liste.currentItem()
        return it.data(Qt.UserRole) if it else None

    def _knoepfe(self, *_) -> None:
        s = self._auswahl()
        zahl = s is not None and ("ebenen" in s or not L.STILE[s["stil"]][1])
        self.anpassen.setVisible(self._aktuell() is not self.r_punkte); self.anpassen.setEnabled(zahl)
        self.loeschen.setVisible(self._aktuell() not in (self.r_punkte, self.r_zahlen, self.r_gl))
        self.loeschen.setEnabled(s is not None)
        self.vorschau.update()

    def _anpassen(self) -> None:
        s = self._auswahl()
        if s is not None and "ebenen" in s:
            g = GliederungAnpassenDialog(self, s)
            if g.exec():
                self._eintragen_gl(g.defn())
                self.reiter.setCurrentWidget(self.r_gl); self.r_gl.setCurrentRow(self.r_gl.count() - 1)
            return
        d = NummerierungAnpassenDialog(self, s)
        if d.exec() and d.spec():
            self._eintragen(d.spec())
            self.reiter.setCurrentWidget(self.r_zahlen); self.r_zahlen.setCurrentRow(self.r_zahlen.count() - 1)

    def _loeschen(self) -> None:
        s = self._auswahl()
        if s in self._benutzer:
            self._benutzer.remove(s); _merke(self._benutzer); self._fuelle_benutzer()
        self._knoepfe()

    def ergebnis(self) -> dict | None:
        """Die gewählte Liste, oder None bei „Kein“."""
        return self._auswahl()
