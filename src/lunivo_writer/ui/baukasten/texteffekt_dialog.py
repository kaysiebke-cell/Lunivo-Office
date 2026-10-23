"""Das Fenster „Texteffekte formatieren“ als Baustein: Reiter „Textfüllung und -kontur“ und „Effekte“ (Schatten, Reflektion, Leuchten, 3D-Format).

    d = TexteffektDialog(parent, werte)          # Wörterbuch wie in ``editor.texteffekt.EFFEKT``, dazu die Teile aus ``editor.textfx``
    if d.exec(): d.werte()                        # ``texteffekt.zu_format(werte)`` macht ein Zeichenformat daraus

Das Fenster formatiert nichts selbst: Der Editor (Schriftart-Fenster, Band) und die Formatvorlage rufen es auf und tun mit dem Ergebnis, was zu ihnen
gehört. Die Abschnitte klappen auf und zu; Schatten, Reflektion, Leuchten, Material und Beleuchtung haben Voreinstellungen zum Anklicken.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QScrollArea, QGridLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.editor import texteffekt as T
from lunivo_writer.editor import textfx as X
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste
from lunivo_writer.ui.baukasten.farbpalette import FarbFeld
from lunivo_writer.ui.baukasten.icon_reiter import IconReiter
from lunivo_writer.ui.baukasten.schiebe_feld import SchiebeFeld, SchrittFeld
from lunivo_writer.ui.baukasten.voreinstellung_menue import VoreinstellungMenue


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.formular_gitter import FormularGitter
from lunivo_writer.core.farben import Farbe
class Abschnitt(QWidget):
    """Aufklappbarer Abschnitt: Pfeil und Überschrift in Großbuchstaben links, optional ein Bedienelement rechts (z. B. die Voreinstellung)."""

    def __init__(self, titel: str, rechts: QWidget | None = None):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(6)
        kopf = QHBoxLayout()
        self.knopf = QToolButton(); self.knopf.setText(titel.upper()); self.knopf.setCheckable(True); self.knopf.setArrowType(Qt.RightArrow)
        self.knopf.setToolButtonStyle(Qt.ToolButtonTextBesideIcon); self.knopf.setAutoRaise(True)
        self.knopf.setStyleSheet("QToolButton { font-weight: 600; color: palette(highlight); border: none; padding: 2px 0; }")
        kopf.addWidget(self.knopf); kopf.addStretch(1)
        if rechts is not None:
            kopf.addWidget(rechts)
        v.addLayout(kopf)
        self.inhalt = QWidget(); self.gitter = FormularGitter(self.inhalt); self.gitter.setContentsMargins(18, 0, 0, 6)
        v.addWidget(self.inhalt); self.inhalt.setVisible(False)
        self.knopf.toggled.connect(self._umschalten)

    def _umschalten(self, an: bool) -> None:
        self.knopf.setArrowType(Qt.DownArrow if an else Qt.RightArrow); self.inhalt.setVisible(an)
        self.updateGeometry()
        p = self.parentWidget()
        while p is not None and not isinstance(p, QScrollArea):         # der Rollbereich muss die neue Höhe der Seite kennen
            if p.layout() is not None:
                p.layout().invalidate()
            p = p.parentWidget()
        if p is not None:
            p.widget().adjustSize()

    def zeile(self, text: str, widget: QWidget) -> None:
        self.gitter.zeile(text, widget)

    def breit(self, widget: QWidget) -> None:
        self.gitter.breit(widget)


def _linien_icon(art: str, form: str, groesse: QSize = QSize(86, 14)) -> QIcon:
    """Kachel der Linienauswahl: eine Linie in Strichart und Form."""
    pm = QPixmap(groesse); pm.fill(QColor("white"))
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    from PySide6.QtGui import QPainterPath
    pf = QPainterPath(); pf.moveTo(4, groesse.height() / 2); pf.lineTo(groesse.width() - 4, groesse.height() / 2)
    for f in X._kontur_pfade(pf, 1.6 if form == "einfach" else 1.2, form, art):
        p.fillPath(f, QColor("#1c7ed6"))
    p.end()
    return QIcon(pm)


class TexteffektPanel(QWidget):
    TITEL = ("TEXTFÜLLUNG UND -KONTUR", "EFFEKTE")                  # die Reiter; ein Objekt-Panel (objektformat_panel.py) setzt eigene
    """Der Inhalt von „Texteffekte formatieren“ als eigenes Widget: Reiter, Abschnitte, Regler. Es steckt im Fenster ``TexteffektDialog`` und in der rechten
    Seitenleiste. ``geaendert(werte)`` kommt bei jeder Änderung durch den Benutzer (nicht bei ``setze``), damit die Seitenleiste sofort anwenden kann."""
    geaendert = Signal(dict)

    def __init__(self, parent=None, werte: dict | None = None):
        super().__init__(parent)
        w = {**T.EFFEKT, **(werte or {})}
        self._fx = {k: dict(w[k]) for k in ("verlauf", "kontur_verlauf", "schatten", "reflektion", "leuchten", "d3") if w.get(k)}
        self._stumm = True
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0)
        self.reiter = IconReiter(); v.addWidget(self.reiter, 1)
        self.reiter.addTab(self._scroll(self._seite_fuellung(w)), self._tab_icon("A", True), self.TITEL[0])
        self.reiter.addTab(self._scroll(self._seite_effekte(w)), self._tab_icon("A", False), self.TITEL[1])
        self.setze(w)
        self._sichtbar()
        self._stumm = False

    @staticmethod
    def _scroll(seite: QWidget) -> QWidget:
        from PySide6.QtWidgets import QFrame
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.NoFrame); sa.setWidget(seite)
        return sa

    @staticmethod
    def _tab_icon(t: str, unterstrichen: bool) -> QIcon:
        pm = QPixmap(26, 26); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        f = QFont(); f.setPixelSize(18); p.setFont(f); p.setPen(QColor(Farbe.GRAU))
        p.drawText(QRectF(0, 0, 26, 22), Qt.AlignCenter, t)
        if unterstrichen:
            p.setPen(QColor(Farbe.BLAU)); p.drawLine(5, 24, 21, 24)
        p.end()
        return QIcon(pm)

    # ---- Seite 1: Füllung und Kontur
    def _seite_fuellung(self, w: dict) -> QWidget:
        seite = QWidget(); v = QVBoxLayout(seite); v.setSpacing(10)
        self.fuell_farbe_kopf = FarbFeld(w["farbe"], "Füllfarbe", keine_text="Keine Füllung", verlauf=True)
        self.fuell_farbe_kopf.setMinimumWidth(110)
        self.a_fuell = Abschnitt("Textfüllung", self.fuell_farbe_kopf)
        self.r_keine, self.r_farbe, self.r_verlauf = QRadioButton("Keine Füllung"), QRadioButton("Einfarbige Füllung"), QRadioButton("Farbverlauf")
        for r in (self.r_keine, self.r_farbe, self.r_verlauf):
            self.a_fuell.breit(r)
        self.farbe = FarbFeld(w["farbe"], "Füllfarbe", keine_text="Automatisch")
        self.trans = SchiebeFeld(0, 100, " %")
        self.f_einfarbig = QWidget(); fe = FormularGitter(self.f_einfarbig)               # nur bei „Einfarbige Füllung“ zu sehen
        fe.zeile("Farbe:", self.farbe); fe.zeile("Transparenz:", self.trans)
        self.v1, self.v2 = FarbFeld(Farbe.ROT, "Farbe 1"), FarbFeld("#1864ab", "Farbe 2")
        self.v_winkel = SchiebeFeld(0, 360, "°", 5)
        self.f_verlauf = QWidget(); fv = FormularGitter(self.f_verlauf)                    # nur bei „Farbverlauf“ zu sehen
        fv.zeile("Farbe 1:", self.v1); fv.zeile("Farbe 2:", self.v2); fv.zeile("Winkel:", self.v_winkel)
        self.a_fuell.breit(self.f_einfarbig); self.a_fuell.breit(self.f_verlauf)
        v.addWidget(self.a_fuell)
        # Kontur
        self.linie_knopf = QPushButton("Keine"); self.linie_knopf.setMinimumWidth(110)
        self.a_kontur = Abschnitt("Textkontur", self.linie_knopf)
        self.k_keine, self.k_linie, self.k_verlauf = QRadioButton("Keine Linie"), QRadioButton("Durchgezogene Linie"), QRadioButton("Farbverlaufslinie")
        for r in (self.k_keine, self.k_linie, self.k_verlauf):
            self.a_kontur.breit(r)
        self.k_farbe = FarbFeld(w["kontur_farbe"], "Konturfarbe")
        self.k_breite = SchiebeFeld(0.1, 20, " pt", 0.25, 2)
        self.k_art = QComboBox(); self.k_art.setIconSize(QSize(86, 14))
        for key, (name, _s, _d) in T.KONTUR_ARTEN.items():
            self.k_art.addItem(_linien_icon(key, "einfach"), name, key)
        self.k_form = QComboBox()
        for key, name in T.KONTUR_FORMEN:
            self.k_form.addItem(name, key)
        self.kv1, self.kv2 = FarbFeld(Farbe.ROT, "Konturfarbe 1"), FarbFeld("#1864ab", "Konturfarbe 2")
        self.kv_winkel = SchiebeFeld(0, 360, "°", 5)
        self.k_einfach = QWidget(); ke = FormularGitter(self.k_einfach)                    # nur bei „Durchgezogene Linie“ zu sehen
        ke.zeile("Farbe:", self.k_farbe); ke.zeile("Breite:", self.k_breite); ke.zeile("Linienart:", self.k_art); ke.zeile("Form:", self.k_form)
        self.k_vlauf = QWidget(); kv = FormularGitter(self.k_vlauf)                        # nur bei „Farbverlaufslinie“ zu sehen
        kv.zeile("Farbe 1:", self.kv1); kv.zeile("Farbe 2:", self.kv2); kv.zeile("Winkel:", self.kv_winkel)
        self.a_kontur.breit(self.k_einfach); self.a_kontur.breit(self.k_vlauf)
        v.addWidget(self.a_kontur)
        v.addStretch(1)
        self.linie_knopf.clicked.connect(self._linien_auswahl)
        self.fuell_farbe_kopf.farbeGeaendert.connect(self._kopffarbe)
        self.fuell_farbe_kopf.verlaufGewaehlt.connect(self._kopf_verlauf)
        self.farbe.farbeGeaendert.connect(lambda c: self.fuell_farbe_kopf.setFarbe(c))
        for r in (self.r_keine, self.r_farbe, self.r_verlauf, self.k_keine, self.k_linie, self.k_verlauf):
            r.toggled.connect(self._neu)
        # Jedes Feld ist bedienbar: wer es ändert, wählt damit die dazugehörige Füllung bzw. Linie
        for sig in (self.farbe.farbeGeaendert, self.trans.valueChanged):
            sig.connect(lambda *_: (self.r_farbe.setChecked(True), self._neu()))
        for sig in (self.v1.farbeGeaendert, self.v2.farbeGeaendert, self.v_winkel.valueChanged):
            sig.connect(lambda *_: (self.r_verlauf.setChecked(True), self._neu()))
        for sig in (self.k_farbe.farbeGeaendert, self.k_breite.valueChanged, self.k_art.currentIndexChanged, self.k_form.currentIndexChanged):
            sig.connect(lambda *_: (self.k_linie.setChecked(True) if not self.k_verlauf.isChecked() else None, self._neu()))
        for sig in (self.kv1.farbeGeaendert, self.kv2.farbeGeaendert, self.kv_winkel.valueChanged):
            sig.connect(lambda *_: (self.k_verlauf.setChecked(True), self._neu()))
        return seite

    def _kopffarbe(self, c: str) -> None:
        """Die Farbe im Kopf der Textfüllung: „Keine Füllung“ oder eine einfarbige Füllung."""
        if not c:
            self.r_keine.setChecked(True)
        else:
            self.r_farbe.setChecked(True); self.farbe.setFarbe(c)
        self._neu()

    def _kopf_verlauf(self, farbe: str) -> None:
        """„Graduelle Füllung“ im Farbmenü: Farbverlauf von hell nach dunkel in dieser Farbe."""
        c = QColor(farbe)
        self.v1.setFarbe(c.lighter(150).name()); self.v2.setFarbe(c.darker(140).name()); self.v_winkel.setValue(45)
        self.r_verlauf.setChecked(True)
        self._neu()

    def _linien_auswahl(self) -> None:
        m = VoreinstellungMenue(self, keine=("Keine Linie", None), kachel=QSize(86, 14))
        m._kopf("Keine Linie")
        eintraege = [(f"{art}|{form}|{br}", _linien_icon(art, form), f"{T.KONTUR_ARTEN[art][0]}, {dict(T.KONTUR_FORMEN)[form]}, {br} pt")
                     for art in T.KONTUR_ARTEN for form, br in (("einfach", 0.75), ("einfach", 2.25), ("doppelt", 2.25), ("dick_duenn", 2.25))]
        m.abschnitt("Voreingestellte Linie", eintraege, 4)
        m.gewaehlt.connect(self._linie_gewaehlt)
        self._menue_zeigen(m, self.linie_knopf)

    def _linie_gewaehlt(self, schluessel: str) -> None:
        if not schluessel:
            self.k_keine.setChecked(True); return
        art, form, br = schluessel.split("|")
        self.k_linie.setChecked(True)
        self.k_art.setCurrentIndex(self.k_art.findData(art)); self.k_form.setCurrentIndex(self.k_form.findData(form)); self.k_breite.setValue(float(br))

    # ---- Seite 2: Effekte
    def _voreinstellungs_knopf(self, text: str = "Keine") -> QPushButton:
        k = QPushButton(text); k.setMinimumWidth(110)
        return k

    def _seite_effekte(self, w: dict) -> QWidget:
        seite = QWidget(); v = QVBoxLayout(seite); v.setSpacing(10)
        # Schatten
        self.schatten_knopf = self._voreinstellungs_knopf()
        self.a_schatten = Abschnitt("Schatten", self.schatten_knopf)
        self.s_farbe = FarbFeld(Farbe.SCHWARZ, "Schattenfarbe")
        self.s_trans = SchiebeFeld(0, 100, " %"); self.s_gross = SchiebeFeld(0, 200, " %", 5)
        self.s_weich = SchiebeFeld(0, 30, " pt", 0.5, 1); self.s_abst = SchiebeFeld(0, 40, " pt", 0.5, 1); self.s_winkel = SchiebeFeld(0, 360, "°", 5)
        for t, x in (("Farbe", self.s_farbe), ("Transparenz", self.s_trans), ("Größe", self.s_gross), ("Weichzeichnen", self.s_weich),
                     ("Abstand", self.s_abst), ("Winkel", self.s_winkel)):
            self.a_schatten.zeile(t, x)
        v.addWidget(self.a_schatten)
        # Reflektion
        self.refl_knopf = self._voreinstellungs_knopf()
        self.a_refl = Abschnitt("Reflektion", self.refl_knopf)
        self.r_gross = SchiebeFeld(0, 100, " %"); self.r_trans = SchiebeFeld(0, 100, " %")
        self.r_weich = SchiebeFeld(0, 30, " pt", 0.5, 1); self.r_abst = SchiebeFeld(0, 40, " pt", 0.5, 1)
        for t, x in (("Größe", self.r_gross), ("Transparenz", self.r_trans), ("Weichzeichnen", self.r_weich), ("Abstand", self.r_abst)):
            self.a_refl.zeile(t, x)
        v.addWidget(self.a_refl)
        # Leuchten
        self.leucht_knopf = self._voreinstellungs_knopf()
        self.a_leucht = Abschnitt("Leuchten", self.leucht_knopf)
        self.l_farbe = FarbFeld(Farbe.BLAU, "Leuchtfarbe"); self.l_gross = SchiebeFeld(0, 40, " pt", 0.5, 1); self.l_trans = SchiebeFeld(0, 100, " %")
        for t, x in (("Farbe", self.l_farbe), ("Größe", self.l_gross), ("Transparenz", self.l_trans)):
            self.a_leucht.zeile(t, x)
        v.addWidget(self.a_leucht)
 # 3D-Format (wie in der Vorlage: Tiefe und Kontur je mit Farbe und Größe, Material, Beleuchtung mit Winkel, Zurücksetzen)
        self.a_3d = Abschnitt("3D-Format")
        self.d_tiefe_f = FarbFeld(Farbe.GRAU, "Farbe der Tiefe"); self.d_tiefe = self._schritt_feld(0, 60, " pt", 0.5, 1)
        self.d_kontur_f = FarbFeld(Farbe.TINTE, "Farbe der Kontur"); self.d_kontur = self._schritt_feld(0, 10, " pt", 0.25, 2)
        self.d_material = self._voreinstellungs_knopf("Matt"); self.d_licht = self._voreinstellungs_knopf("Neutral"); self.d_winkel = self._schritt_feld(0, 360, "°", 5, 1)
        for titel, farbe, gr in (("Tiefe", self.d_tiefe_f, self.d_tiefe), ("Kontur", self.d_kontur_f, self.d_kontur)):
            self.a_3d.breit(QLabel(titel))
            self.a_3d.breit(self._zweier(farbe, QLabel("Größe"), gr))
        self.a_3d.breit(QLabel("Material")); self.a_3d.breit(self._zweier(self.d_material))
        self.d_licht_titel = QLabel("Beleuchtung")
        self.a_3d.breit(self.d_licht_titel)
        self.d_winkel_titel = QLabel("Winkel")
        self.a_3d.breit(self._zweier(self.d_licht, self.d_winkel_titel, self.d_winkel))
        zr3 = QPushButton("Zurücksetzen"); zr3.clicked.connect(self._d3_zuruecksetzen); self.a_3d.breit(self._zweier(zr3))
        v.addWidget(self.a_3d)
        v.addStretch(1)
        self._material, self._licht = "matt", "neutral"
        self.schatten_knopf.clicked.connect(self._schatten_auswahl); self.refl_knopf.clicked.connect(self._refl_auswahl)
        self.leucht_knopf.clicked.connect(self._leucht_auswahl)
        self.d_material.clicked.connect(self._material_auswahl); self.d_licht.clicked.connect(self._licht_auswahl)
        # Jeder Regler ist bedienbar: wer einen Regler bewegt, schaltet den Effekt mit den angezeigten Werten ein
        for name, quellen in (("schatten", (self.s_farbe.farbeGeaendert, self.s_trans.valueChanged, self.s_gross.valueChanged, self.s_weich.valueChanged,
                                            self.s_abst.valueChanged, self.s_winkel.valueChanged)),
                              ("reflektion", (self.r_gross.valueChanged, self.r_trans.valueChanged, self.r_weich.valueChanged, self.r_abst.valueChanged)),
                              ("leuchten", (self.l_farbe.farbeGeaendert, self.l_gross.valueChanged, self.l_trans.valueChanged))):
            for sig in quellen:
                sig.connect(lambda *_, n=name: self._einschalten(n))
        for sig in (self.d_tiefe_f.farbeGeaendert, self.d_tiefe.valueChanged, self.d_kontur_f.farbeGeaendert, self.d_kontur.valueChanged,
                    self.d_winkel.valueChanged):
            sig.connect(lambda *_: self._neu())
        return seite

    @staticmethod
    def _schritt_feld(lo: float, hi: float, suffix: str, schritt: float, nk: int) -> QWidget:
        """Zahlenfeld mit Minus und Plus an den Seiten (wie die Größenfelder im 3D-Format des WPS)."""
        return SchrittFeld(lo, hi, suffix, schritt, nk)

    @staticmethod
    def _zweier(*teile: QWidget) -> QWidget:
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(10)
        for i, t in enumerate(teile):
            h.addWidget(t, 1 if i in (0, len(teile) - 1) else 0)
        return w

    def _d3_zuruecksetzen(self) -> None:
        self.d_tiefe.setValue(0); self.d_kontur.setValue(0); self.d_winkel.setValue(0)
        self.d_tiefe_f.setFarbe(Farbe.GRAU); self.d_kontur_f.setFarbe(Farbe.TINTE); self._setze_material("matt", "neutral")

    def _menue_zeigen(self, m: VoreinstellungMenue, knopf: QPushButton) -> None:
        m.exec(knopf.mapToGlobal(knopf.rect().bottomLeft()))

    def _schatten_auswahl(self) -> None:
        m = VoreinstellungMenue(self, keine=("Kein Schatten", X.voreinstellung_icon({})))
        vor = X.schatten_vorgaben()
        for abschnitt in ("Außen", "Innen", "Perspektive"):
            m.abschnitt(abschnitt, [(str(i), X.voreinstellung_icon({"schatten": s}), n) for i, (a, n, s) in enumerate(vor) if a == abschnitt], 3)
        m.gewaehlt.connect(lambda k: self._setze_teil("schatten", vor[int(k)][2] if k else None, vor[int(k)][1] if k else "Keine"))
        self._menue_zeigen(m, self.schatten_knopf)

    def _refl_auswahl(self) -> None:
        m = VoreinstellungMenue(self, keine=("Keine Spiegelung", X.voreinstellung_icon({})))
        vor = X.reflektion_vorgaben()
        m.abschnitt("Spiegelungsvarianten", [(str(i), X.voreinstellung_icon({"reflektion": r}, text="A"), n) for i, (n, r) in enumerate(vor)], 3)
        m.gewaehlt.connect(lambda k: self._setze_teil("reflektion", vor[int(k)][1] if k else None, vor[int(k)][0] if k else "Keine"))
        self._menue_zeigen(m, self.refl_knopf)

    def _leucht_auswahl(self) -> None:
        m = VoreinstellungMenue(self, keine=("Kein Leuchteffekt", X.voreinstellung_icon({})))
        vor = X.leuchten_vorgaben()
        m.abschnitt("Leuchtvarianten", [(str(i), X.voreinstellung_icon({"leuchten": g}), n) for i, (n, g) in enumerate(vor)], 6)
        m.gewaehlt.connect(lambda k: self._setze_teil("leuchten", vor[int(k)][1] if k else None, vor[int(k)][0] if k else "Keine"))
        self._menue_zeigen(m, self.leucht_knopf)

    def _material_auswahl(self) -> None:
        m = VoreinstellungMenue(self, keine=None)
        m.abschnitt("Material", [(k, X.voreinstellung_icon({"d3": {"tiefe": 4, "tiefe_farbe": Farbe.GRAU, "material": k}}), n) for k, n in X.MATERIAL], 3)
        m.gewaehlt.connect(lambda k: self._setze_material(k, None))
        self._menue_zeigen(m, self.d_material)

    def _licht_auswahl(self) -> None:
        m = VoreinstellungMenue(self, keine=None)
        m.abschnitt("Beleuchtung", [(k, X.voreinstellung_icon({"d3": {"tiefe": 4, "tiefe_farbe": Farbe.GRAU, "beleuchtung": k}}), n) for k, n in X.BELEUCHTUNG], 3)
        m.gewaehlt.connect(lambda k: self._setze_material(None, k))
        self._menue_zeigen(m, self.d_licht)

    def _setze_material(self, material: str | None, licht: str | None) -> None:
        if material:
            self._material = material; self.d_material.setText(dict(X.MATERIAL)[material])
        if licht:
            self._licht = licht; self.d_licht.setText(dict(X.BELEUCHTUNG)[licht])
        self._neu()

    def _setze_teil(self, name: str, wert: dict | None, text: str) -> None:
        """Eine Voreinstellung übernehmen: die Regler zeigen ihre Werte."""
        knopf = {"schatten": self.schatten_knopf, "reflektion": self.refl_knopf, "leuchten": self.leucht_knopf}[name]
        knopf.setText(text)
        if wert is None:
            self._fx.pop(name, None)
        else:
            self._fx[name] = dict(wert)
        self._teil_in_regler(name)
        self._neu()

    def _teil_in_regler(self, name: str) -> None:
        t = self._fx.get(name)
        if name == "schatten":
            t = t or {"farbe": Farbe.SCHWARZ, "transparenz": 50, "groesse": 100, "weich": 3, "abstand": 4, "winkel": 45}
            self.s_farbe.setFarbe(t["farbe"]); self.s_trans.setValue(t["transparenz"]); self.s_gross.setValue(t["groesse"])
            self.s_weich.setValue(t["weich"]); self.s_abst.setValue(t["abstand"]); self.s_winkel.setValue(t["winkel"])
        elif name == "reflektion":
            t = t or {"groesse": 50, "transparenz": 50, "weich": 0, "abstand": 0}
            self.r_gross.setValue(t["groesse"]); self.r_trans.setValue(t["transparenz"]); self.r_weich.setValue(t["weich"]); self.r_abst.setValue(t["abstand"])
        elif name == "leuchten":
            t = t or {"farbe": Farbe.BLAU, "groesse": 5, "transparenz": 60}
            self.l_farbe.setFarbe(t["farbe"]); self.l_gross.setValue(t["groesse"]); self.l_trans.setValue(t["transparenz"])

    # ---- Werte
    def setze(self, w: dict) -> None:
        """Werte ins Panel schreiben (ohne ``geaendert`` zu melden)."""
        alt, self._stumm = self._stumm, True
        try:
            self._setze(w)
        finally:
            self._stumm = alt

    def _setze(self, w: dict) -> None:
        self._fx = {k: dict(w[k]) for k in ("verlauf", "kontur_verlauf", "schatten", "reflektion", "leuchten", "d3") if w.get(k)}
        self._setze_fuellung(w)
        self._setze_effekte(w)
        self._neu()

    def _setze_fuellung(self, w: dict) -> None:
        for r in (self.r_keine, self.r_farbe, self.r_verlauf, self.k_keine, self.k_linie, self.k_verlauf):
            r.blockSignals(True)
        verl = "verlauf" in self._fx or w["fuell"] == "verlauf"
        self.r_keine.setChecked(w["fuell"] == "keine"); self.r_verlauf.setChecked(verl); self.r_farbe.setChecked(w["fuell"] == "farbe" and not verl)
        kv = "kontur_verlauf" in self._fx
        self.k_keine.setChecked(not w["kontur"]); self.k_verlauf.setChecked(bool(w["kontur"]) and kv); self.k_linie.setChecked(bool(w["kontur"]) and not kv)
        for r in (self.r_keine, self.r_farbe, self.r_verlauf, self.k_keine, self.k_linie, self.k_verlauf):
            r.blockSignals(False)
        self.farbe.setFarbe(w["farbe"]); self.fuell_farbe_kopf.setFarbe("" if w["fuell"] == "keine" else w["farbe"]); self.trans.setValue(w["transparenz"])
        vv = self._fx.get("verlauf", {"farbe1": Farbe.ROT, "farbe2": "#1864ab", "winkel": 90})
        self.v1.setFarbe(vv["farbe1"]); self.v2.setFarbe(vv["farbe2"]); self.v_winkel.setValue(vv["winkel"])
        kvv = self._fx.get("kontur_verlauf", {"farbe1": Farbe.ROT, "farbe2": "#1864ab", "winkel": 90})
        self.kv1.setFarbe(kvv["farbe1"]); self.kv2.setFarbe(kvv["farbe2"]); self.kv_winkel.setValue(kvv["winkel"])
        self.k_farbe.setFarbe(w["kontur_farbe"]); self.k_breite.setValue(w["kontur_breite"])
        self.k_art.setCurrentIndex(max(0, self.k_art.findData(w["kontur_art"]))); self.k_form.setCurrentIndex(max(0, self.k_form.findData(w.get("kontur_form", "einfach"))))

    def _setze_effekte(self, w: dict) -> None:
        for n in ("schatten", "reflektion", "leuchten"):
            self._teil_in_regler(n)
        d = self._fx.get("d3", {})
        self.d_tiefe_f.setFarbe(d.get("tiefe_farbe", Farbe.GRAU)); self.d_tiefe.setValue(d.get("tiefe", 0)); self.d_kontur_f.setFarbe(d.get("kontur_farbe", Farbe.TINTE))
        self.d_kontur.setValue(d.get("kontur", 0)); self.d_winkel.setValue(d.get("winkel", 0))
        self._setze_material(d.get("material", "matt"), d.get("beleuchtung", "neutral"))
        for n, k in (("schatten", self.schatten_knopf), ("reflektion", self.refl_knopf), ("leuchten", self.leucht_knopf)):
            k.setText("Vorhanden" if n in self._fx else "Keine")

    def werte(self) -> dict:
        w, fx = self._werte_fuellung()
        fx.update(self._werte_effekte())
        w.update(fx)
        return w

    def _werte_fuellung(self) -> tuple[dict, dict]:
        """(Werte der Füllung und Kontur, zusätzliche Schlüssel dazu: Verlauf, Konturverlauf, Konturform)."""
        verl = self.r_verlauf.isChecked()
        w = {"fuell": "keine" if self.r_keine.isChecked() else "farbe", "farbe": self.farbe.farbe, "transparenz": int(self.trans.value()),
             "kontur": not self.k_keine.isChecked(), "kontur_farbe": self.k_farbe.farbe or Farbe.SCHWARZ, "kontur_breite": self.k_breite.value(),
             "kontur_art": self.k_art.currentData()}
        fx = {}
        if verl:
            w["fuell"] = "verlauf"
            fx["verlauf"] = {"farbe1": self.v1.farbe or Farbe.SCHWARZ, "farbe2": self.v2.farbe or Farbe.WEISS, "winkel": self.v_winkel.value()}
        if self.k_verlauf.isChecked():
            fx["kontur_verlauf"] = {"farbe1": self.kv1.farbe or Farbe.SCHWARZ, "farbe2": self.kv2.farbe or Farbe.WEISS, "winkel": self.kv_winkel.value()}
        form = self.k_form.currentData()
        if form != "einfach" and w["kontur"]:
            fx["kontur_form"] = form
        return w, fx

    def _werte_effekte(self) -> dict:
        """Schatten, Reflektion, Leuchten und 3D mit den Werten der Regler (gemeinsam für Text und Objekte)."""
        fx = {k: v for k, v in self._fx.items() if k in ("schatten", "reflektion", "leuchten")}
        if "schatten" in fx:
            fx["schatten"] = {**fx["schatten"], "farbe": self.s_farbe.farbe or Farbe.SCHWARZ, "transparenz": self.s_trans.value(), "groesse": self.s_gross.value(),
                              "weich": self.s_weich.value(), "abstand": self.s_abst.value(), "winkel": self.s_winkel.value()}
        if "reflektion" in fx:
            fx["reflektion"] = {"groesse": self.r_gross.value(), "transparenz": self.r_trans.value(), "weich": self.r_weich.value(), "abstand": self.r_abst.value()}
        if "leuchten" in fx:
            fx["leuchten"] = {"farbe": self.l_farbe.farbe or Farbe.BLAU, "groesse": self.l_gross.value(), "transparenz": self.l_trans.value()}
        if self.d_tiefe.value() > 0 or self.d_kontur.value() > 0:
            fx["d3"] = {"tiefe": self.d_tiefe.value(), "tiefe_farbe": self.d_tiefe_f.farbe or Farbe.GRAU, "kontur": self.d_kontur.value(),
                        "kontur_farbe": self.d_kontur_f.farbe or Farbe.TINTE, "material": self._material, "beleuchtung": self._licht, "winkel": self.d_winkel.value()}
        return fx

    def _einschalten(self, name: str) -> None:
        """Ein Regler eines Effekts wurde bewegt: der Effekt ist damit an (mit den Werten, die die Regler zeigen)."""
        if name not in self._fx:
            self._fx[name] = {}
            {"schatten": self.schatten_knopf, "reflektion": self.refl_knopf, "leuchten": self.leucht_knopf}[name].setText("Eigene")
        self._neu()

    def _sichtbar(self) -> None:
        """Nur die Felder zeigen, die zur gewählten Füllung und Linie gehören (spart Höhe in der Seitenleiste). Das Objekt-Panel baut die Seite selbst und hat sie nicht."""
        if not hasattr(self, "f_einfarbig"):
            return
        self.f_einfarbig.setVisible(self.r_farbe.isChecked()); self.f_verlauf.setVisible(self.r_verlauf.isChecked())
        self.k_einfach.setVisible(self.k_linie.isChecked() or self.k_verlauf.isChecked())
        self.k_vlauf.setVisible(self.k_verlauf.isChecked())
        for a in (self.a_fuell, self.a_kontur):
            a.updateGeometry()

    def _neu(self, *_) -> None:
        self._sichtbar()
        if not self._stumm:
            QTimer.singleShot(0, self._melden)
        self.linie_knopf.setText("Keine" if self.k_keine.isChecked() else T.KONTUR_ARTEN[self.k_art.currentData()][0])

    def _melden(self) -> None:
        try:
            if not self._stumm:
                self.geaendert.emit(self.werte())
        except RuntimeError:                       # das Fenster wurde schon abgebaut, bevor die verzögerte Meldung kam
            pass

    def _male(self, p: QPainter, rect) -> None:
        w = self.werte()
        f = QFont("Liberation Sans"); f.setPixelSize(36); f.setBold(True)
        face = QColor(0, 0, 0, 0) if w["fuell"] == "keine" else QColor(w["farbe"] or "#111417")
        if w["fuell"] == "farbe" and w["transparenz"]:
            face.setAlphaF(1 - w["transparenz"] / 100)
        if w["fuell"] == "verlauf":
            face = QColor(w["verlauf"]["farbe1"])
        kontur = None
        if w["kontur"]:
            kontur = (QColor(w["kontur_farbe"]), w["kontur_breite"] * X.PX, w.get("kontur_form", "einfach"), w["kontur_art"])
        X.vorschau_zeichnen(p, QRectF(rect), "Beispieltext", f, {k: v for k, v in w.items() if k in ("verlauf", "kontur_verlauf", "kontur_form", "schatten", "reflektion", "leuchten", "d3")},
                            face, kontur)


class TexteffektDialog(PanelFaehig, QDialog):
    """Das Fenster „Texteffekte formatieren“: das Panel mit „OK“ (wie in der Vorlage; das Schließen-Kreuz bricht ab). Felder des Panels sind hier erreichbar."""

    def __init__(self, parent=None, werte: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Texteffekte formatieren")
        v = QVBoxLayout(self)
        self.panel = TexteffektPanel(self, werte)
        v.addWidget(self.panel, 1)
        self.resize(422, 558)
        fussleiste(self, v, nur_ok=True)

    def passe_an(self, breite: int, hoehe: int) -> None:
        """Die Seite nimmt die ganze Höhe der Seitenleiste: die Abschnitte rollen sonst in einem winzigen Streifen."""
        self.setMinimumHeight(max(300, hoehe - 20))                       # abzüglich Knopfzeile

    def __getattr__(self, name: str):
        if name == "panel":                                  # noch nicht gebaut: kein Umweg über das Panel
            raise AttributeError(name)
        return getattr(self.panel, name)
