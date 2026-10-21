"""„Formatierung“ für ein Bild oder eine Form in der rechten Seitenleiste: Reiter „Füllung und Linie“ und „Effekte“ (nach der Vorlage).

Der Baustein erbt vom Panel der Texteffekte: die Effekte (Schatten, Reflektion, Leuchten mit denselben Reglern und Voreinstellungen) sind dieselben,
nur Füllung und Linie gehören dem Objekt, und es kommen „Weiche Kanten“ dazu. ``werte()`` liefert

    {"fuell": {…} | None, "rand": {…} | None, "schatten": {…}, "reflektion": {…}, "leuchten": {…}, "weich": {"radius": pt}}

— genau die Angaben, die ``editor/freie_bilder.py`` am Bild kennt; wer das Panel einsetzt (``editor/bildlayout.py``), schreibt sie zurück.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QComboBox, QPushButton, QRadioButton, QVBoxLayout, QWidget

from lunivo_writer.editor import muster as M
from lunivo_writer.editor.linie import LINIENARTEN
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.linien import linien_symbol
from lunivo_writer.ui.baukasten.objekt_menues import TEXTUREN
from lunivo_writer.ui.baukasten.schiebe_feld import SchiebeFeld
from lunivo_writer.ui.baukasten.texteffekt_dialog import Abschnitt, TexteffektPanel
from lunivo_writer.ui.baukasten.voreinstellung_menue import VoreinstellungMenue

STRICHE = ["einfach", "gepunktet", "fein_gestrichelt", "gestrichelt", "strichpunkt", "strichpunktpunkt"]
WEICH_STUFEN = (1, 2.5, 5, 10, 25, 50)
LEER = {"fuell": None, "rand": None}


class ObjektFormatPanel(TexteffektPanel):
    TITEL = ("FÜLLUNG UND LINIE", "EFFEKTE")
    bild_gewuenscht = Signal()                    # „Bild …“ als Füllung: der Aufrufer fragt nach der Datei

    @staticmethod
    def _tab_icon(t: str, unterstrichen: bool):
        """Die Reiter-Bildchen: Farbeimer (Füllung und Linie) und ein Quadrat mit Funken (Effekte)."""
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
        from lunivo_writer.ui.widgets import icons
        pm = QPixmap(26, 26); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        if unterstrichen:
            p.drawPixmap(2, 0, icons.icon("farbe", 22).pixmap(22, 22))
            p.setPen(QColor("#4c6ef5")); p.drawLine(5, 24, 21, 24)
        else:
            p.setPen(QPen(QColor("#868e96"), 1.6)); p.drawRect(QRectF(4, 6, 14, 14))
            p.setPen(QPen(QColor("#4c6ef5"), 1.6)); p.drawLine(18, 2, 18, 8); p.drawLine(15, 5, 21, 5)
        p.end()
        return QIcon(pm)

    # ---- Seite 1: Füllung und Linie ------------------------------------------------------------------------------------------
    def _seite_fuellung(self, w: dict) -> QWidget:
        seite = QWidget(); v = QVBoxLayout(seite); v.setSpacing(10)
        self.fuell_farbe_kopf = FarbFeld("#4c6ef5", "Füllfarbe", keine_text="Keine Füllung", verlauf=True)
        self.fuell_farbe_kopf.setMinimumWidth(110)
        self.a_fuell = Abschnitt("Füllung", self.fuell_farbe_kopf)
        self.r_keine, self.r_farbe, self.r_verlauf = QRadioButton("Keine Füllung"), QRadioButton("Einfarbige Füllung"), QRadioButton("Farbverlauf")
        self.r_textur, self.r_muster = QRadioButton("Strukturfüllung"), QRadioButton("Musterfüllung")
        self.r_bild = QRadioButton("Bildfüllung")
        for r in (self.r_keine, self.r_farbe, self.r_verlauf, self.r_textur, self.r_muster, self.r_bild):
            self.a_fuell.breit(r)
        self.farbe = FarbFeld("#4c6ef5", "Füllfarbe", keine_text="Automatisch")
        self.a_fuell.zeile("Farbe:", self.farbe)
        self.v1, self.v2 = FarbFeld("#1864ab", "Dunkle Farbe"), FarbFeld("#d0ebff", "Helle Farbe")
        self.a_fuell.zeile("Farbe 1:", self.v1); self.a_fuell.zeile("Farbe 2:", self.v2)
        self.textur = QComboBox()
        for schl, name in TEXTUREN:
            self.textur.addItem(name, schl)
        self.a_fuell.zeile("Struktur:", self.textur)
        self.muster = QComboBox()
        for schl, name, _o in M.MUSTER:
            if schl != "loeschen":
                self.muster.addItem(M.name_von(schl), schl)
        self.m_farbe = FarbFeld("#343a40", "Musterfarbe")
        self.a_fuell.zeile("Muster:", self.muster); self.a_fuell.zeile("Musterfarbe:", self.m_farbe)
        self.bild_knopf = QPushButton("Bild wählen …"); self.bild_knopf.clicked.connect(self.bild_gewuenscht)
        self.a_fuell.zeile("Bild:", self.bild_knopf)
        v.addWidget(self.a_fuell)
        # Linie
        self.linie_knopf = QPushButton("Keine"); self.linie_knopf.setMinimumWidth(110)
        self.a_kontur = Abschnitt("Linie", self.linie_knopf)
        self.k_keine, self.k_linie = QRadioButton("Keine Linie"), QRadioButton("Durchgezogene Linie")
        for r in (self.k_keine, self.k_linie):
            self.a_kontur.breit(r)
        self.k_farbe = FarbFeld("#000000", "Linienfarbe")
        self.k_breite = SchiebeFeld(0.25, 20, " pt", 0.25, 2)
        self.k_art = QComboBox(); self.k_art.setIconSize(QSize(86, 14))
        for k in STRICHE:                                          # die Strichlinien des Bausteins „Linie“ als Bildchen, nicht als Text
            self.k_art.addItem(linien_symbol(k, QSize(86, 14)), "", k)
        self.a_kontur.zeile("Farbe:", self.k_farbe); self.a_kontur.zeile("Breite:", self.k_breite); self.a_kontur.zeile("Strichart:", self.k_art)
        v.addWidget(self.a_kontur)
        v.addStretch(1)
        self.linie_knopf.clicked.connect(self._linien_menue)
        self.fuell_farbe_kopf.farbeGeaendert.connect(self._kopffarbe)
        self.fuell_farbe_kopf.verlaufGewaehlt.connect(self._kopf_verlauf)
        for r in (self.r_keine, self.r_farbe, self.r_verlauf, self.r_textur, self.r_muster, self.r_bild, self.k_keine, self.k_linie):
            r.toggled.connect(self._neu)
        # Jedes Feld ist bedienbar: wer es ändert, wählt damit die dazugehörige Füllung bzw. Linie
        for sig, radio in ((self.farbe.farbeGeaendert, self.r_farbe), (self.v1.farbeGeaendert, self.r_verlauf), (self.v2.farbeGeaendert, self.r_verlauf),
                           (self.textur.currentIndexChanged, self.r_textur), (self.muster.currentIndexChanged, self.r_muster),
                           (self.m_farbe.farbeGeaendert, self.r_muster)):
            sig.connect(lambda *_, r=radio: (r.setChecked(True), self._neu()))
        for sig in (self.k_farbe.farbeGeaendert, self.k_breite.valueChanged, self.k_art.currentIndexChanged):
            sig.connect(lambda *_: (self.k_linie.setChecked(True), self._neu()))
        return seite

    def _kopffarbe(self, c: str) -> None:
        if not c:
            self.r_keine.setChecked(True)
        else:
            self.r_farbe.setChecked(True); self.farbe.setFarbe(c)
        self._neu()

    def _kopf_verlauf(self, farbe: str) -> None:
        from PySide6.QtGui import QColor
        c = QColor(farbe)
        self.v1.setFarbe(c.name()); self.v2.setFarbe(c.lighter(170).name()); self.r_verlauf.setChecked(True)
        self._neu()

    def _linien_menue(self) -> None:
        m = VoreinstellungMenue(self, keine=("Keine Linie", None), kachel=QSize(86, 14))
        m._kopf("Keine Linie")
        m.abschnitt("Strichart", [(k, linien_symbol(k, QSize(86, 14)), LINIENARTEN[k][0]) for k in STRICHE], 2)
        m.gewaehlt.connect(lambda k: self.k_keine.setChecked(True) if not k else (self.k_linie.setChecked(True), self.k_art.setCurrentIndex(self.k_art.findData(k))))
        m.exec(self.linie_knopf.mapToGlobal(self.linie_knopf.rect().bottomLeft()))

    def fuellung_waehlen(self, art: str) -> None:
        """Die Füllungsart wählen („verlauf“, „textur“, „muster“, „bild“ …); die Füllung gilt sofort, die Felder dazu sind bedienbar."""
        radio = {"keine": self.r_keine, "farbe": self.r_farbe, "verlauf": self.r_verlauf, "graduell": self.r_verlauf, "textur": self.r_textur,
                 "muster": self.r_muster, "bild": self.r_bild}.get(art)
        if radio is not None and not radio.isChecked():
            radio.setChecked(True)

    def _neu(self, *_) -> None:
        super()._neu()
        self.linie_knopf.setText("Keine" if self.k_keine.isChecked() else LINIENARTEN[self.k_art.currentData() or "einfach"][0])

    def _setze_fuellung(self, w: dict) -> None:
        f, r = w.get("fuell"), w.get("rand")
        art = (f or {}).get("art")
        radios = (self.r_keine, self.r_farbe, self.r_verlauf, self.r_textur, self.r_muster, self.r_bild, self.k_keine, self.k_linie)
        for x in radios:
            x.blockSignals(True)
        self.r_keine.setChecked(f is None); self.r_farbe.setChecked(art == "farbe"); self.r_verlauf.setChecked(art in ("verlauf", "graduell"))
        self.r_textur.setChecked(art == "textur"); self.r_muster.setChecked(art == "muster"); self.r_bild.setChecked(art == "bild")
        self.k_keine.setChecked(not r); self.k_linie.setChecked(bool(r))
        for x in radios:
            x.blockSignals(False)
        if f:
            if art == "farbe":
                self.farbe.setFarbe(f["farbe"])
            elif art in ("verlauf", "graduell"):
                self.v1.setFarbe(f.get("dunkel", f.get("farbe", "#1864ab"))); self.v2.setFarbe(f.get("hell", "#d0ebff"))
            elif art == "textur":
                self.textur.setCurrentIndex(max(0, self.textur.findData(f.get("key"))))
            elif art == "muster":
                self.muster.setCurrentIndex(max(0, self.muster.findData(f.get("key")))); self.m_farbe.setFarbe(f.get("farbe", "#343a40"))
        self.fuell_farbe_kopf.setFarbe(f.get("farbe", "") if art == "farbe" else "")
        if r:
            self.k_farbe.setFarbe(r.get("farbe", "#000000")); self.k_breite.setValue(r.get("b", 2.0) * 72 / 96)
            self.k_art.setCurrentIndex(max(0, self.k_art.findData(r.get("art", "einfach"))))

    def _werte_fuellung(self) -> tuple[dict, dict]:
        if self.r_keine.isChecked():
            fuell = None
        elif self.r_verlauf.isChecked():
            fuell = {"art": "graduell", "dunkel": self.v1.farbe or "#1864ab", "hell": self.v2.farbe or "#ffffff", "farbe": self.v1.farbe or "#1864ab"}
        elif self.r_textur.isChecked():
            fuell = {"art": "textur", "key": self.textur.currentData()}
        elif self.r_muster.isChecked():
            fuell = {"art": "muster", "key": self.muster.currentData(), "farbe": self.m_farbe.farbe or "#343a40", "grund": "#ffffff"}
        elif self.r_bild.isChecked():
            fuell = {"art": "bild", "unveraendert": True}                       # das Bild bleibt, wie es ist (der Aufrufer behält es)
        else:
            fuell = {"art": "farbe", "farbe": self.farbe.farbe or "#4c6ef5"}
        rand = None if self.k_keine.isChecked() else {"b": self.k_breite.value() * 96 / 72, "farbe": self.k_farbe.farbe or "#000000",
                                                         "art": self.k_art.currentData() or "einfach"}
        return {"fuell": fuell, "rand": rand}, {}

    # ---- Seite 2: Effekte (dieselben wie beim Text, dazu Weiche Kanten; 3D gibt es für Bilder nicht) -----------------------------------
    def _seite_effekte(self, w: dict) -> QWidget:
        seite = super()._seite_effekte(w)
        self.a_3d.setVisible(False)                                             # Extrusion lässt sich nur an Text zeichnen
        self.weich_knopf = self._voreinstellungs_knopf()
        self.a_weich = Abschnitt("Weiche Kanten", self.weich_knopf)
        self.w_radius = SchiebeFeld(0, 50, " pt", 0.5, 1)
        self.a_weich.zeile("Größe", self.w_radius)
        seite.layout().insertWidget(3, self.a_weich)                           # nach Schatten, Reflektion, Leuchten
        self._weich_an = False
        self.w_radius.valueChanged.connect(lambda *_: self._weich_einschalten())
        self.weich_knopf.clicked.connect(self._weich_menue)
        return seite

    def _weich_einschalten(self) -> None:
        if not self._weich_an:
            self._weich_an = True; self.weich_knopf.setText("Eigene")
        self._neu()

    def _weich_menue(self) -> None:
        from PySide6.QtGui import QIcon
        m = VoreinstellungMenue(self, keine=("Keine weichen Kanten", None))
        m._kopf("Keine weichen Kanten")
        m.abschnitt("Weiche Kanten", [(f"{s:g}", QIcon(), f"{s:g} pt") for s in WEICH_STUFEN], 3)

        def waehle(k: str) -> None:
            self._weich_an = bool(k)
            self.weich_knopf.setText(f"{k} pt" if k else "Keine")
            if k:
                self.w_radius.setValue(float(k))
            self._neu()
        m.gewaehlt.connect(waehle)
        m.exec(self.weich_knopf.mapToGlobal(self.weich_knopf.rect().bottomLeft()))

    def _setze_effekte(self, w: dict) -> None:
        super()._setze_effekte(w)
        wk = w.get("weich")
        self._weich_an = bool(wk)
        self.weich_knopf.setText("Keine" if not wk else "Eigene")
        self.w_radius.setValue((wk or {}).get("radius", 6.0))

    def _werte_effekte(self) -> dict:
        fx = super()._werte_effekte()
        fx.pop("d3", None)
        if getattr(self, "_weich_an", False):
            fx["weich"] = {"radius": self.w_radius.value()}
        return fx
