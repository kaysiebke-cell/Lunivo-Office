"""Optionen: Ansicht und Darstellung."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QRadioButton, QPushButton, QSlider, QVBoxLayout, QWidget
from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import _Seite


class AnsichtSeiten:
    """Optionen: Ansicht und Darstellung. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


    THEMEN = (("light", "Hell"), ("dark", "Dunkel"), ("system", "Wie das System"))


    def _ansicht(self, titel):
        p = _Seite(self.w, titel)
        self._aussehen(p)
        f = p.gruppe("Anzeigen")
        p.haken(f, "ansicht/lineal", "Lineal", False, lambda _: self.w.lineale_anwenden())
        p.haken(f, "ui/statusleiste", "Statusleiste", True, lambda on: self.w.statusBar().setVisible(on))
        alle = QCheckBox("Absatzmarken und Leerzeichen zeigen")
        alle.setProperty("optName", alle.text()); alle.setMinimumHeight(32)

        def alle_stand():
            alt = p.s.get_bool("ui/steuerzeichen", False)
            an = p.s.get_bool("ui/marken_absatz", alt) and p.s.get_bool("ui/marken_leer", alt)
            alle.blockSignals(True); alle.setChecked(an); alle.blockSignals(False)
        alle_stand()
        alle.toggled.connect(lambda on: (self.w.marken_setzen(on, on), alle_stand()))
        f.addRow(alle)
        f = p.gruppe("Größe und Kontrast")
        self._darstellung(p, f)
        e = p.mehr()
        f = p.unter(e, "Weitere Anzeige")
        p.haken(f, "ansicht/lineal_hoch", "Vertikales Lineal", False, lambda _: self.w.lineale_anwenden())
        p.schalter(f, "Navigationsbereich", lambda: self.w.navigation.isVisible(), self.w.toggle_navigation)
        p.haken(f, "ui/marken", "Textbegrenzungen", False, self.w.set_marken)
        p.schalter(f, "Gitternetzlinien", lambda: bool(self.w.befehle.an_netzlinien()), lambda: self.w.befehle.netzlinien())
        p.haken(f, "ui/seitenleiste", "Seitenleiste beim Start", True)
        p.haken(f, "ui/quickinfo", "QuickInfo", True, lambda _: self.w.ansicht_optionen_anwenden())
        p.haken(f, "ui/live_vorschau", "Live-Vorschau", True, lambda _: self.w.vorschau.ende())
        p.haken(f, "ui/mini_auswahl", "Minisymbolleiste bei Auswahl", True)
        p.haken(f, "ui/objektanker", "Objektanker", True)
        p.haken(f, "ui/versteckt_zeigen", "Ausgeblendeter Text", False, lambda _: self.w.versteckt_anwenden())
        f = p.unter(e, "Formatierungszeichen einzeln")
        absatz, leer = QCheckBox("Absatzmarken"), QCheckBox("Leerzeichen und Tabstoppzeichen")
        for c in (absatz, leer):
            c.setProperty("optName", c.text()); c.setMinimumHeight(32)

        def stand():
            alt = p.s.get_bool("ui/steuerzeichen", False)
            for c, k in ((absatz, "ui/marken_absatz"), (leer, "ui/marken_leer")):
                c.blockSignals(True); c.setChecked(p.s.get_bool(k, alt)); c.blockSignals(False)
            alle_stand()
        stand()
        absatz.toggled.connect(lambda on: (self.w.marken_setzen(absatz=on), stand()))
        leer.toggled.connect(lambda on: (self.w.marken_setzen(leer=on), stand()))
        for c in (absatz, leer):
            f.addRow(c)
        f = p.unter(e, "Menüband")
        p.haken(f, "ui/band_doppelklick", "Doppelklick blendet das Band aus", True, lambda on: setattr(self.w.band, "einklappbar", on))
        p.haken(f, "ui/strg_klick_link", "Strg+Klick folgt einem Verweis", True)
        self._oberflaeche_wahl(p, f)
        p.aktion("Menüband anpassen", "Menüband anpassen …", lambda: self._anpassen("menueband"))
        p.aktion("Symbolleiste für den Schnellzugriff", "Schnellzugriff anpassen …", lambda: self._anpassen("schnellzugriff"))
        p.abschluss()
        return p


    def _aussehen(self, p):
        """Hell, Dunkel oder wie das System: drei große Schaltflächen, genau eine ist gewählt (kein ausgegrauter Zusatzschalter)."""
        f = p.gruppe("Aussehen")
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 6, 0, 6); h.setSpacing(10)
        gruppe = QButtonGroup(zeile)
        knoepfe: dict[str, QPushButton] = {}
        for schl, name in self.THEMEN:
            b = QPushButton(name)
            b.setObjectName("optWahl"); b.setCheckable(True); b.setMinimumHeight(48)
            b.setAccessibleName(name); b.setAccessibleDescription("Aussehen des Programms")
            b.setProperty("optName", "Hell, Dunkel (Aussehen)")
            gruppe.addButton(b); h.addWidget(b, 1)
            knoepfe[schl] = b

        def zeigen(_=None):
            jetzt = p.s.get("theme", "system")
            for schl, b in knoepfe.items():
                b.blockSignals(True); b.setChecked(schl == jetzt)
                b.setText(("✓  " if schl == jetzt else "") + dict(self.THEMEN)[schl]); b.blockSignals(False)
        for schl, b in knoepfe.items():
            b.clicked.connect(lambda _c=False, k=schl: (self.w.set_theme(k), zeigen()))
        zeigen()
        self._aussehen_zeigen = zeigen
        zeile.setProperty("optName", "Hell, Dunkel (Aussehen)")
        f.addRow(zeile)


    def _oberflaeche_wahl(self, p, f):
        oberfl = QWidget(); ov = QVBoxLayout(oberfl); ov.setContentsMargins(0, 6, 0, 8); ov.addWidget(QLabel("Benutzeroberfläche"))
        gr = QButtonGroup(oberfl)
        beschreibung = text_label("", umbruch=True)
        beschreibung.setStyleSheet("color: palette(window-text); font-size: 9pt;")
        texte = {"symbolleisten": "Menüleiste, darunter zwei Zeilen Symbole: alles ist sichtbar, nichts ist versteckt.",
                 "register": "Menüleiste oben, darunter Reiter: Start, Einfügen, Layout. Jeder Reiter hat seine eigenen Werkzeuge, in Gruppen mit Namen darunter."}
        aktuell = p.s.get("ui/oberflaeche", "register")
        for schl, name in (("symbolleisten", "Symbolleisten"), ("register", "In Registern")):
            r = QRadioButton(name); r.setChecked(schl == aktuell); r.setProperty("optName", "Benutzeroberfläche"); r.setMinimumHeight(32)
            gr.addButton(r); ov.addWidget(r)
            r.toggled.connect(lambda an, k=schl: an and (beschreibung.setText(texte[k]),
                                                         self.w.oberflaeche_aendern(k, self.w.menubar_wanted if k == "register" else True)))
        beschreibung.setText(texte.get(aktuell, ""))
        ov.addWidget(beschreibung)
        oberfl.setProperty("optName", "Benutzeroberfläche")
        f.addRow(oberfl)


    def _darstellung(self, p, f):
        """Schrift größer/kleiner, Weicher Kontrast, Größe der Symbole, Schrift der Bedienung."""
        kopf = QWidget(); v = QVBoxLayout(kopf); v.setContentsMargins(0, 6, 0, 8); v.setSpacing(8)
        v.addWidget(QLabel("Schrift im Text"))
        knoepfe = QHBoxLayout()
        klein, gross = QPushButton("A−  kleiner"), QPushButton("A+  größer")
        for k in (klein, gross):
            k.setMinimumHeight(32); knoepfe.addWidget(k)
        knoepfe.addStretch(1)
        v.addLayout(knoepfe)
        zeile = QHBoxLayout()
        probe = QLabel("So groß schreibst du.")
        probe.setObjectName("optVorschau")
        stand = QLabel()
        stand.setStyleSheet("color: palette(window-text); font-size: 9pt;")
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
        zoom_zeigen()
        kopf.setProperty("optName", "Schrift im Text")
        f.addRow(kopf)
        p.haken(f, "ui/weich", "Weicher Kontrast", False, lambda _: self.w.set_theme(self.w.settings.get("theme", "system")))
        p.wahl(f, "ui/icongroesse", "Größe der Symbole", [("Klein", "klein"), ("Mittel", "mittel"), ("Groß", "gross")], "mittel",
               lambda _: self.w.ansicht_optionen_anwenden())
        regler = QWidget(); rv = QVBoxLayout(regler); rv.setContentsMargins(0, 6, 0, 8); rv.addWidget(QLabel("Schrift der Bedienung"))
        rh = QHBoxLayout()
        sl = QSlider(Qt.Horizontal); sl.setRange(80, 140); sl.setSingleStep(5); sl.setPageStep(10); sl.setMinimumHeight(32)
        sl.setAccessibleName("Schrift der Bedienung in Prozent")
        sl.setValue(p.s.get_int("ui/bedien_prozent", 100))
        prozent = QLabel(f"{sl.value()} %"); prozent.setStyleSheet("color: palette(window-text);")

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
