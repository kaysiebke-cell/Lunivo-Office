"""Optionen: Ansicht und Darstellung."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QRadioButton, QPushButton, QSlider, QVBoxLayout, QWidget
from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import _Seite


class AnsichtSeiten:
    """Optionen: Ansicht und Darstellung. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


    # ================= Wie im WPS Writer =================
    def _ansicht(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Anzeigen")
        p.haken(f, "ansicht/lineal", "Lineal", False, lambda _: self.w.lineale_anwenden())
        p.haken(f, "ansicht/lineal_hoch", "Vertikales Lineal", False, lambda _: self.w.lineale_anwenden())
        p.schalter(f, "Navigationsbereich", lambda: self.w.navigation.isVisible(), self.w.toggle_navigation)
        p.haken(f, "ui/marken", "Textbegrenzungen", False, self.w.set_marken)
        p.schalter(f, "Gitternetzlinien", lambda: bool(self.w.befehle.an_netzlinien()), lambda: self.w.befehle.netzlinien())
        p.haken(f, "ui/statusleiste", "Statusleiste", True, lambda on: self.w.statusBar().setVisible(on))
        p.haken(f, "ui/seitenleiste", "Seitenleiste beim Start", True)
        p.haken(f, "ui/quickinfo", "QuickInfo", True, lambda _: self.w.ansicht_optionen_anwenden())
        p.haken(f, "ui/live_vorschau", "Live-Vorschau", True, lambda _: self.w.vorschau.ende())
        p.haken(f, "ui/mini_auswahl", "Minisymbolleiste bei Auswahl", True)
        p.haken(f, "ui/mini_rechtsklick", "Minisymbolleiste bei Rechtsklick", True)
        p.haken(f, "ui/kopffuss_tipp", "Tipp für Kopf- bzw. Fußzeile", True)
        f = p.gruppe("Druckoptionen")
        p.haken(f, "drucken/hervorhebungen", "Hervorhebungen drucken", True)
        p.haken(f, "drucken/textgrenzen", "Textbegrenzungen drucken", False)
        p.haken(f, "drucken/zuschnitt", "Zuschnittsmarken anzeigen", False)
        p.haken(f, "drucken/felder_code", "Feldfunktionen drucken", False)
        p.haken(f, "drucken/textmarken", "Textmarken drucken", False)
        p.wahl(f, "ui/feldschattierung", "Feldschattierung", [("Nie", "Nie"), ("Wenn ausgewählt", "Bei Auswahl"), ("Immer", "Immer")],
               "Bei Auswahl", lambda _: [t.editor._overlays_neu() for t in self.w._doc_tabs()])
        f = p.gruppe("Formatierungszeichen")
        alle, absatz, leer = QCheckBox("Alle anzeigen"), QCheckBox("Absatzmarken"), QCheckBox("Leerzeichen und Tabstoppzeichen")
        for c in (alle, absatz, leer):
            c.setProperty("optName", c.text())

        def stand():
            alt = p.s.get_bool("ui/steuerzeichen", False)
            a, l = p.s.get_bool("ui/marken_absatz", alt), p.s.get_bool("ui/marken_leer", alt)
            for c, v in ((alle, a and l), (absatz, a), (leer, l)):
                c.blockSignals(True); c.setChecked(v); c.blockSignals(False)

        def setze(a=None, l=None):
            self.w.marken_setzen(a, l)
            stand()
        stand()
        alle.toggled.connect(lambda on: setze(on, on))
        absatz.toggled.connect(lambda on: setze(absatz=on))
        leer.toggled.connect(lambda on: setze(leer=on))
        for c in (alle, absatz, leer):
            f.addRow(c)
        p.haken(f, "ui/objektanker", "Objektanker", True)
        p.haken(f, "ui/versteckt_zeigen", "Ausgeblendeter Text", False, lambda _: self.w.versteckt_anwenden())
        f = p.gruppe("Menübandoptionen")
        p.haken(f, "ui/band_doppelklick", "Doppelklick blendet das Band aus", True, lambda on: setattr(self.w.band, "einklappbar", on))
        p.haken(f, "ui/strg_klick_link", "Strg+Klick folgt einem Verweis", True)
        f = p.gruppe("Darstellung")
        self._darstellung(p, f)
        p.abschluss()
        return p


    def _darstellung(self, p, f):
        """Schrift und Helligkeit, Weicher Kontrast, Größe der Symbole, Schrift der Bedienung, Benutzeroberfläche."""
        kopf = QWidget(); v = QVBoxLayout(kopf); v.setContentsMargins(0, 6, 0, 8); v.setSpacing(8)
        v.addWidget(QLabel("Schrift und Helligkeit"))
        knoepfe = QHBoxLayout()
        klein, gross, hell = QPushButton("A−  kleiner"), QPushButton("A+  größer"), QPushButton("◐  Hell/Dunkel")
        for k in (klein, gross, hell):
            knoepfe.addWidget(k)
        knoepfe.addStretch(1)
        v.addLayout(knoepfe)
        zeile = QHBoxLayout()
        probe = QLabel("So groß schreibst du.")
        probe.setObjectName("optVorschau")
        stand = QLabel()
        stand.setStyleSheet("color: palette(mid); font-size: 9pt;")
        zeile.addWidget(probe); zeile.addWidget(stand); zeile.addStretch(1)
        v.addLayout(zeile)

        def zoom_zeigen():
            e = self.w.current_editor()
            z = e.zoom if e is not None else 1.0
            fnt = probe.font(); fnt.setPointSizeF(12 * z); probe.setFont(fnt)
            stand.setText(f"Schriftgröße: {round(z * 100)} %")

        def um(faktor):
            self.w.befehle._zoom_um(faktor)
            zoom_zeigen()
        klein.clicked.connect(lambda: um(1 / 1.1))
        gross.clicked.connect(lambda: um(1.1))
        hell.clicked.connect(lambda: self.w.set_theme("light" if QApplication.instance().palette().window().color().lightness() < 128 else "dark"))
        zoom_zeigen()
        kopf.setProperty("optName", "Schrift und Helligkeit")
        f.addRow(kopf)
        p.haken(f, "ui/weich", "Weicher Kontrast", False, lambda _: self.w.set_theme(self.w.settings.get("theme", "system")))
        p.wahl(f, "ui/icongroesse", "Größe der Symbole", [("Klein", "klein"), ("Mittel", "mittel"), ("Groß", "gross")], "mittel",
               lambda _: self.w.ansicht_optionen_anwenden())
        regler = QWidget(); rv = QVBoxLayout(regler); rv.setContentsMargins(0, 6, 0, 8); rv.addWidget(QLabel("Schrift der Bedienung"))
        rh = QHBoxLayout()
        sl = QSlider(Qt.Horizontal); sl.setRange(80, 140); sl.setSingleStep(5); sl.setPageStep(10)
        sl.setValue(p.s.get_int("ui/bedien_prozent", 100))
        prozent = QLabel(f"{sl.value()} %"); prozent.setStyleSheet("color: palette(mid);")

        def neu_wert(w):
            p.s.set("ui/bedien_prozent", w)
            prozent.setText(f"{w} %")
            if not sl.isSliderDown():
                self.w.ansicht_optionen_anwenden()
        sl.valueChanged.connect(neu_wert)
        sl.sliderReleased.connect(self.w.ansicht_optionen_anwenden)
        rh.addWidget(sl, 1); rh.addWidget(prozent)
        rv.addLayout(rh)
        regler.setProperty("optName", "Schrift der Bedienung")
        f.addRow(regler)
        oberfl = QWidget(); ov = QVBoxLayout(oberfl); ov.setContentsMargins(0, 6, 0, 8); ov.addWidget(QLabel("Benutzeroberfläche"))
        gr = QButtonGroup(oberfl)
        beschreibung = text_label("", umbruch=True)
        beschreibung.setStyleSheet("color: palette(mid); font-size: 9pt;")
        texte = {"symbolleisten": "Menüleiste, darunter zwei Zeilen Symbole: alles ist sichtbar, nichts ist versteckt.",
                 "register": "Menüleiste oben, darunter Reiter: Start, Einfügen, Layout. Jeder Reiter hat seine eigenen Werkzeuge, in Gruppen mit Namen darunter."}
        aktuell = p.s.get("ui/oberflaeche", "register")
        for schl, name in (("symbolleisten", "Symbolleisten"), ("register", "In Registern")):
            r = QRadioButton(name); r.setChecked(schl == aktuell); r.setProperty("optName", "Benutzeroberfläche")
            gr.addButton(r); ov.addWidget(r)
            r.toggled.connect(lambda an, k=schl: an and (beschreibung.setText(texte[k]),
                                                         self.w.oberflaeche_aendern(k, self.w.menubar_wanted if k == "register" else True)))
        beschreibung.setText(texte.get(aktuell, ""))
        ov.addWidget(beschreibung)
        oberfl.setProperty("optName", "Benutzeroberfläche")
        f.addRow(oberfl)
