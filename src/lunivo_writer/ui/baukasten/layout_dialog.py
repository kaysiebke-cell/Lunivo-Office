"""Das Fenster „Layout“ für Bilder und Formen: Position, Textumbruch, Größe — nach der Vorlage (WPS).

    d = LayoutDialog(parent, werte)
    if d.exec(): neu = d.werte()

``werte`` und der Rückgabewert sind ein Wörterbuch (siehe ``STANDARD``); das Fenster verändert nichts selbst. Wer es aufruft
(``editor/bildlayout.py``), liest die Werte vom Bild und schreibt sie zurück. Alle Längen sind in Millimetern; angezeigt wird in der
Einheit der Oberfläche über ``EinheitFeld``.
"""
from __future__ import annotations

import copy

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
                               QRadioButton, QTabWidget, QVBoxLayout, QWidget)

from lunivo_writer.ui.baukasten.dialog_rahmen import fussleiste
from lunivo_writer.ui.baukasten.kachel_feld import KachelFeld
from lunivo_writer.ui.baukasten.mass_feld import EinheitFeld
from lunivo_writer.ui.baukasten.umbruch_symbole import ARTEN, umbruch_zeichner

BEZUG_H = [("spalte", "Spalte"), ("rand", "Seitenrand"), ("seite", "Seite")]
BEZUG_V = [("absatz", "Absatz"), ("rand", "Seitenrand"), ("seite", "Seite")]
AUSR_H = [("links", "Links"), ("zentriert", "Zentriert"), ("rechts", "Rechts")]
AUSR_V = [("oben", "Oben"), ("zentriert", "Zentriert"), ("unten", "Unten")]
BUCH = [("innen", "Innen"), ("aussen", "Außen")]
ZEILEN = [("beide", "Beide Seiten"), ("links", "Nur links"), ("rechts", "Nur rechts"), ("groesste", "Nur größte Seite")]
UMFLIESSEND = ("quadrat", "passend", "transparent")                 # nur hier gelten „Zeilenumbruch“ und „Abstand zum Text“

STANDARD = {
    "umbruch": "textfluss", "zeilen": "beide", "abstand": {"oben": 0.0, "unten": 0.0, "links": 3.4, "rechts": 3.4},
    "h": {"modus": "abs", "ausr": "links", "buch": "innen", "bezug_ausr": "spalte", "bezug_buch": "rand", "mm": 0.0, "bezug_abs": "spalte",
          "proz": 0.0, "bezug_rel": "seite"},
    "v": {"modus": "abs", "ausr": "oben", "bezug_ausr": "seite", "mm": 0.0, "bezug_abs": "absatz", "proz": 0.0, "bezug_rel": "seite"},
    "mit_text": False, "ueberlappen": True, "verankern": False,
    "breite": {"modus": "abs", "mm": 40.0, "proz": 0.0, "bezug": "seite"}, "hoehe": {"modus": "abs", "mm": 40.0, "proz": 0.0, "bezug": "seite"},
    "drehung": 0.0, "sperren": False, "skal_original": True, "original": (40.0, 40.0),
}


def _combo(eintraege, aktuell) -> QComboBox:
    c = QComboBox()
    for schl, text in eintraege:
        c.addItem(text, schl)
    c.setCurrentIndex(max(0, c.findData(aktuell)))
    return c


def _zeile(g: QGridLayout, r: int, radio: QRadioButton, *rest) -> None:
    g.addWidget(radio, r, 0)
    for i, w in enumerate(rest):
        g.addWidget(w, r, i + 1)


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
class LayoutDialog(PanelFaehig, QDialog):
    def __init__(self, parent=None, werte: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Layout")
        w = copy.deepcopy(STANDARD)
        for k, v in (werte or {}).items():
            if isinstance(v, dict) and isinstance(w.get(k), dict):
                w[k].update(v)
            else:
                w[k] = v
        self._w = w
        v = QVBoxLayout(self)
        self.reiter = QTabWidget(); v.addWidget(self.reiter)
        self._position(w); self._umbruch(w); self._groesse(w)
        self.ok = fussleiste(self, v)
        self._pruefen()

    # ---- Reiter Position ---------------------------------------------------------------------------------------------------
    def _achse(self, titel: str, w: dict, waagerecht: bool) -> dict:
        box = QGroupBox(titel); g = QGridLayout(box); g.setColumnStretch(2, 1)
        grp = QButtonGroup(self)
        ausr_liste, bezug = (AUSR_H, BEZUG_H) if waagerecht else (AUSR_V, BEZUG_V)
        f: dict = {}
        r = 0
        f["r_ausr"] = QRadioButton("Ausrichtung")
        f["ausr"] = _combo(ausr_liste, w["ausr"])
        f["bezug_ausr"] = _combo(bezug, w["bezug_ausr"])
        _zeile(g, r, f["r_ausr"], f["ausr"], QLabel("relativ zu"), f["bezug_ausr"]); r += 1
        if waagerecht:
            f["r_buch"] = QRadioButton("Buchlayout")
            f["buch"] = _combo(BUCH, w["buch"])
            f["bezug_buch"] = _combo([("rand", "Seitenrand"), ("seite", "Seite")], w["bezug_buch"])
            _zeile(g, r, f["r_buch"], f["buch"], QLabel("von"), f["bezug_buch"]); r += 1
        f["r_abs"] = QRadioButton("Absolute Position")
        f["mm"] = EinheitFeld(w["mm"], -2000.0, 2000.0, ("mm", "cm", "in", "pt"))
        f["bezug_abs"] = _combo(bezug, w["bezug_abs"])
        _zeile(g, r, f["r_abs"], f["mm"], QLabel("Rechts von" if waagerecht else "unterhalb"), f["bezug_abs"]); r += 1
        f["r_rel"] = QRadioButton("Relative Position")
        f["proz"] = QDoubleSpinBox(); f["proz"].setRange(-100, 200); f["proz"].setSuffix(" %"); f["proz"].setValue(w["proz"])
        f["bezug_rel"] = _combo([b for b in bezug if b[0] != "absatz"], w["bezug_rel"])
        _zeile(g, r, f["r_rel"], f["proz"], QLabel("relativ zu" if waagerecht else "gemessen von"), f["bezug_rel"])
        radios = [k for k in ("r_ausr", "r_buch", "r_abs", "r_rel") if k in f]
        for k in radios:
            grp.addButton(f[k])
        modus = {"ausr": "r_ausr", "buch": "r_buch", "abs": "r_abs", "rel": "r_rel"}.get(w["modus"], "r_abs")
        f.get(modus, f["r_abs"]).setChecked(True)
        f["box"] = box
        for k in radios:
            f[k].toggled.connect(lambda _=False, f=f: self._achse_ein(f))
        self._achse_ein(f)
        return f

    @staticmethod
    def _achse_ein(f: dict) -> None:
        """Nur die Felder der gewählten Zeile sind bedienbar (wie in der Vorlage)."""
        for radio, felder in (("r_ausr", ("ausr", "bezug_ausr")), ("r_buch", ("buch", "bezug_buch")), ("r_abs", ("mm", "bezug_abs")),
                              ("r_rel", ("proz", "bezug_rel"))):
            if radio in f:
                for k in felder:
                    f[k].setEnabled(f[radio].isChecked())

    def _position(self, w: dict) -> None:
        seite = QWidget(); v = QVBoxLayout(seite)
        self.h = self._achse("Horizontal", w["h"], True); self.v = self._achse("Vertikal", w["v"], False)
        v.addWidget(self.h["box"]); v.addWidget(self.v["box"])
        opt = QGroupBox("Optionen"); g = QGridLayout(opt)
        self.mit_text = QCheckBox("Objekt mit Text verschieben"); self.mit_text.setChecked(w["mit_text"])
        self.ueberlappen = QCheckBox("Überlappen zulassen"); self.ueberlappen.setChecked(w["ueberlappen"])
        self.verankern = QCheckBox("Verankern"); self.verankern.setChecked(w["verankern"])
        tabelle = QCheckBox("Layout in Tabellenzelle"); tabelle.setChecked(True); tabelle.setEnabled(False)       # wie in der Vorlage grau
        g.addWidget(self.mit_text, 0, 0); g.addWidget(self.ueberlappen, 0, 1); g.addWidget(self.verankern, 1, 0); g.addWidget(tabelle, 1, 1)
        v.addWidget(opt); v.addStretch(1)
        self.reiter.addTab(seite, "Position")

    # ---- Reiter Textumbruch ------------------------------------------------------------------------------------------------
    def _umbruch(self, w: dict) -> None:
        seite = QWidget(); v = QVBoxLayout(seite)
        box = QGroupBox("Umbruchart"); bv = QVBoxLayout(box)
        self.kacheln = KachelFeld(spalten=4, groesse=QSize(44, 44))
        for schl, text in ARTEN:
            self.kacheln.hinzu(schl, text, umbruch_zeichner(schl))
        self.kacheln.setze(w["umbruch"]); self.kacheln.gewaehlt.connect(lambda _k: self._pruefen())
        bv.addWidget(self.kacheln); v.addWidget(box)
        zb = QGroupBox("Zeilenumbruch"); zh = QHBoxLayout(zb)
        self.zeilen = {}
        gr = QButtonGroup(self)
        for schl, text in ZEILEN:
            r = QRadioButton(text); r.setChecked(w["zeilen"] == schl); gr.addButton(r); zh.addWidget(r); self.zeilen[schl] = r
        v.addWidget(zb); self._zeilen_box = zb
        ab = QGroupBox("Abstand zum Text"); ag = QGridLayout(ab)
        self.abstand = {}
        for i, (schl, text) in enumerate((("oben", "Oben"), ("links", "Links"), ("unten", "Unten"), ("rechts", "Rechts"))):
            f = EinheitFeld(w["abstand"][schl], 0.0, 200.0, ("mm", "cm", "in", "pt"))
            self.abstand[schl] = f
            ag.addWidget(QLabel(text), i % 2, (i // 2) * 2); ag.addWidget(f, i % 2, (i // 2) * 2 + 1)
        v.addWidget(ab); self._abstand_box = ab; v.addStretch(1)
        self.reiter.addTab(seite, "Textumbruch")

    # ---- Reiter Größe ------------------------------------------------------------------------------------------------------
    def _mass(self, titel: str, w: dict) -> dict:
        box = QGroupBox(titel); g = QGridLayout(box); g.setColumnStretch(2, 1)
        f = {"r_abs": QRadioButton("Absolut"), "mm": EinheitFeld(w["mm"], 1.0, 3000.0, ("mm", "cm", "in", "pt")),
             "r_rel": QRadioButton("Relativ"), "proz": QDoubleSpinBox(), "bezug": _combo([("seite", "Seite"), ("rand", "Seitenrand")], w["bezug"])}
        f["proz"].setRange(1, 1000); f["proz"].setSuffix(" %"); f["proz"].setValue(w["proz"] or 100)
        gr = QButtonGroup(self); gr.addButton(f["r_abs"]); gr.addButton(f["r_rel"])
        (f["r_rel"] if w["modus"] == "rel" else f["r_abs"]).setChecked(True)
        _zeile(g, 0, f["r_abs"], f["mm"]); _zeile(g, 1, f["r_rel"], f["proz"], QLabel("relativ zu"), f["bezug"])

        def ein(_=False, f=f):
            f["mm"].setEnabled(f["r_abs"].isChecked()); f["proz"].setEnabled(f["r_rel"].isChecked()); f["bezug"].setEnabled(f["r_rel"].isChecked())
        f["r_abs"].toggled.connect(ein); ein()
        f["box"] = box
        return f

    def _groesse(self, w: dict) -> None:
        seite = QWidget(); v = QVBoxLayout(seite)
        self.hoehe = self._mass("Höhe", w["hoehe"]); self.breite = self._mass("Breite", w["breite"])
        v.addWidget(self.hoehe["box"]); v.addWidget(self.breite["box"])
        d = QGroupBox("Drehen"); dh = QHBoxLayout(d)
        self.drehung = QDoubleSpinBox(); self.drehung.setRange(-360, 360); self.drehung.setSuffix(" °"); self.drehung.setValue(w["drehung"])
        dh.addWidget(QLabel("Drehung:")); dh.addWidget(self.drehung); dh.addStretch(1); v.addWidget(d)
        s = QGroupBox("Skalieren"); sg = QGridLayout(s)
        self.skal_h = QDoubleSpinBox(); self.skal_b = QDoubleSpinBox()
        for x in (self.skal_h, self.skal_b):
            x.setRange(1, 1000); x.setSuffix(" %"); x.setValue(100)
        sg.addWidget(QLabel("Höhe:"), 0, 0); sg.addWidget(self.skal_h, 0, 1); sg.addWidget(QLabel("Breite:"), 0, 2); sg.addWidget(self.skal_b, 0, 3)
        self.sperren = QCheckBox("Seitenverhältnis sperren"); self.sperren.setChecked(w["sperren"])
        self.skal_original = QCheckBox("Relativ zur Originalbildgröße"); self.skal_original.setChecked(w["skal_original"])
        sg.addWidget(self.sperren, 1, 0, 1, 4); sg.addWidget(self.skal_original, 2, 0, 1, 4)
        v.addWidget(s)
        o = QGroupBox("Originalgröße"); og = QGridLayout(o)
        self._orig_b, self._orig_h = w["original"]
        self.orig_text = QLabel(); og.addWidget(self.orig_text, 0, 0)
        zur = QPushButton("Zurücksetzen"); zur.clicked.connect(self._zuruecksetzen); og.addWidget(zur, 0, 1, Qt.AlignRight)
        v.addWidget(o); v.addStretch(1)
        self.reiter.addTab(seite, "Größe")
        self._skal_nachziehen(); self._orig_anzeigen()
        for e in (self.hoehe["mm"], self.breite["mm"]):
            e.valueChanged.connect(lambda _=0: self._groesse_geaendert())
        self.skal_h.valueChanged.connect(lambda _=0: self._skal_geaendert(True)); self.skal_b.valueChanged.connect(lambda _=0: self._skal_geaendert(False))

    def _orig_anzeigen(self) -> None:
        f = self.hoehe["mm"]._faktor()
        kurz = self.hoehe["mm"].einheit.currentText()
        self.orig_text.setText(f"Höhe: {self._orig_h * f:.2f} {kurz}      Breite: {self._orig_b * f:.2f} {kurz}")

    def _skal_nachziehen(self) -> None:
        """Die Skalierung in Prozent aus der aktuellen Größe im Verhältnis zur Originalgröße."""
        self._block = True
        self.skal_h.setValue(round(self.hoehe["mm"].value() / max(0.1, self._orig_h) * 100, 1))
        self.skal_b.setValue(round(self.breite["mm"].value() / max(0.1, self._orig_b) * 100, 1))
        self._block = False

    _block = False

    def _groesse_geaendert(self) -> None:
        if not self._block:
            self._skal_nachziehen()

    def _skal_geaendert(self, hoehe: bool) -> None:
        if self._block:
            return
        self._block = True
        if self.sperren.isChecked():
            (self.skal_b if hoehe else self.skal_h).setValue((self.skal_h if hoehe else self.skal_b).value())
        self.hoehe["mm"].setValue(self._orig_h * self.skal_h.value() / 100); self.breite["mm"].setValue(self._orig_b * self.skal_b.value() / 100)
        self._block = False

    def _zuruecksetzen(self) -> None:
        self._block = True
        self.hoehe["mm"].setValue(self._orig_h); self.breite["mm"].setValue(self._orig_b); self.drehung.setValue(0)
        self.skal_h.setValue(100); self.skal_b.setValue(100)
        self._block = False

    def _pruefen(self) -> None:
        """Zeilenumbruch und Abstand zum Text gelten nur bei Quadrat, Passend und Transparent."""
        an = self.kacheln.aktuell() in UMFLIESSEND
        self._zeilen_box.setEnabled(an); self._abstand_box.setEnabled(an)
        frei = self.kacheln.aktuell() in ("hinter", "vor")
        self.mit_text.setEnabled(not frei)

    # ---- Ergebnis ----------------------------------------------------------------------------------------------------------
    @staticmethod
    def _achse_lesen(f: dict) -> dict:
        modus = "ausr" if f["r_ausr"].isChecked() else "buch" if f.get("r_buch") is not None and f["r_buch"].isChecked() else \
            "rel" if f["r_rel"].isChecked() else "abs"
        out = {"modus": modus, "ausr": f["ausr"].currentData(), "bezug_ausr": f["bezug_ausr"].currentData(), "mm": f["mm"].value(),
               "bezug_abs": f["bezug_abs"].currentData(), "proz": f["proz"].value(), "bezug_rel": f["bezug_rel"].currentData()}
        if "buch" in f:
            out["buch"] = f["buch"].currentData(); out["bezug_buch"] = f["bezug_buch"].currentData()
        return out

    @staticmethod
    def _mass_lesen(f: dict) -> dict:
        return {"modus": "rel" if f["r_rel"].isChecked() else "abs", "mm": f["mm"].value(), "proz": f["proz"].value(), "bezug": f["bezug"].currentData()}

    def werte(self) -> dict:
        return {"umbruch": self.kacheln.aktuell() or "textfluss", "zeilen": next((k for k, r in self.zeilen.items() if r.isChecked()), "beide"),
                "abstand": {k: f.value() for k, f in self.abstand.items()}, "h": self._achse_lesen(self.h), "v": self._achse_lesen(self.v),
                "mit_text": self.mit_text.isChecked(), "ueberlappen": self.ueberlappen.isChecked(), "verankern": self.verankern.isChecked(),
                "breite": self._mass_lesen(self.breite), "hoehe": self._mass_lesen(self.hoehe), "drehung": self.drehung.value(),
                "sperren": self.sperren.isChecked(), "skal_original": self.skal_original.isChecked(), "original": (self._orig_b, self._orig_h)}
