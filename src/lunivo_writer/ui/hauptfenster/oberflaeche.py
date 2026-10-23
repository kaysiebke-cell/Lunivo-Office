"""Oberfläche: Register oder Symbolleisten."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand, lade_register


class OberflaecheBaustein:
    """Oberfläche: Register oder Symbolleisten. Baustein von ``MainWindow`` (siehe ``lunivo_writer/ui/main_window.py``)."""


    # ---- Oberfläche: Register oder Symbolleisten, angepasst ----------------------------------------------------
    def _symbole_anwenden(self):
        from lunivo_writer.ui.widgets import icons
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import lade_json
        icons.uebersteuern(lade_json(self.settings, "ui/symbol_tausch", {}))


    def _band_erzeugen(self):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import lade_json
        from lunivo_writer.ui.ribbon.toolbars import Symbolleisten
        reg = RegisterBand(self.befehle, lade_register(), lade_json(self.settings, "ui/register_plan", {}),
                           lade_json(self.settings, "ui/schnellzugriff", None))
        if self.settings.get("ui/oberflaeche", "register") != "symbolleisten":
            return reg
        sym = Symbolleisten(self.befehle)
        sym.daten = reg.daten
        sym.gruppe_widget = reg.gruppe_widget            # die Seitenleiste baut ihre Gruppen weiter aus dem Register
        sym._reg = reg
        urspr = sym.aktualisieren

        def aktualisieren(hat=None, _u=urspr, _r=reg):
            _u(hat); _r.aktualisieren(hat)
        sym.aktualisieren = aktualisieren
        return sym


    def oberflaeche_aendern(self, art: str, menueleiste: bool):
        self.settings.set("ui/oberflaeche", art)
        if menueleiste != self.menubar_wanted:
            self.toggle_menubar()
        self.neu_bauen_band()


    def neu_bauen_band(self):
        optionen_offen = self.backstage.isVisible() and self.backstage.stapel.currentWidget() is self.backstage.seiten.get("optionen")
        unter = self.backstage.optionen_seite() if optionen_offen else None
        self._band_neu_bauen()
        if optionen_offen:                                         # Der Umbau (Design, Symbolgröße …) wirft niemanden aus den Optionen
            if hasattr(self.band, "reiter"):
                self.backstage_oeffnen("optionen", unter)
            else:                                                  # Symbolleisten-Oberfläche: kein Register, also Fenster
                self.backstage.hide(); self.arbeit.show()
                self.show_options(unter)


    def _band_neu_bauen(self):
        alt = self.band
        idx = self.band_lay.indexOf(alt)
        self.band = self._band_erzeugen()
        self.band.einklappbar = self.settings.get_bool("ui/band_doppelklick", True)
        self.band.menue_knopf.clicked.connect(self.show_main_menu)
        self.band_lay.insertWidget(idx, self.band)
        alt.setParent(None); alt.deleteLater()
        self._backstage_verbinden()
        self._verbinde_felder()
        self._bereiche_bauen()
        self._refresh_ui()
