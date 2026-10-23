"""Befehle: Ansicht, Fenster, Zoom."""
from __future__ import annotations

import os
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QMessageBox


class AnsichtBefehle:
    """Befehle des Bandes: Ansicht, Fenster, Zoom. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Ansicht ---------------------------------------------------------------------------------------------------------------
    def handbuch(self, k=None):
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.handbuch(self.w).show()


    def tastenHilfe(self, k=None):
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.tastenkuerzel(self.w).show()


    def erweiterungen(self, k=None):
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.erweiterungen(self.w).show()


    def vorlagenWaehlen(self, k=None): self.w.neu_aus_vorlage()


    def vorlagenOrdner(self, k=None):
        import os
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from lunivo_writer.editor import vorlagen
        o = vorlagen.vorlagenordner(self.w.settings)
        os.makedirs(o, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(o))


    def menueleisteZeigen(self, k=None):
        self.w.toggle_menubar()


    def an_menueleisteZeigen(self): return self.w.menubar_wanted


    def registerAnpassen(self, k=None):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import RegisterAnpassenDialog
        if RegisterAnpassenDialog(self.w, self.w.settings, self.w.band.daten).exec():
            self.w.neu_bauen_band()


    def schnellzugriffAnpassen(self, k=None):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import SchnellzugriffDialog, lade_json
        from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand
        akt = lade_json(self.w.settings, "ui/schnellzugriff", None)
        if akt is None:
            akt = [a for _s, _n, a in RegisterBand.SCHNELL]
        if SchnellzugriffDialog(self.w, self.w.settings, RegisterBand.SCHNELL_ALLE, akt).exec():
            self.w.neu_bauen_band()


    def symbolTauschen(self, k=None, name=None):
        """Symbol austauschen (Ansicht ▸ Oberfläche, Optionen — und Rechtsklick auf einen Knopf, dann mit dessen Symbol)."""
        from PySide6.QtCore import QTimer
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import SymbolTauschenDialog
        d = SymbolTauschenDialog(self.w, self.w.settings, name)
        d.exec()
        if d.geaendert:
            QTimer.singleShot(0, self.w.neu_bauen_band)             # nicht mitten im Klick auf den Knopf, der gerade neu gebaut wird


    def benutzeroberflaeche(self, k=None):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import OberflaecheDialog
        d = OberflaecheDialog(self.w, self.w.settings)
        if d.exec():
            self.w.oberflaeche_aendern(d.wahl(), d.menue.isChecked())


    def leistenZeigen(self, k=None):
        neu = "register" if self.w.settings.get("ui/oberflaeche", "register") == "symbolleisten" else "symbolleisten"
        self.w.oberflaeche_aendern(neu, self.w.menubar_wanted)


    def an_leistenZeigen(self): return self.w.settings.get("ui/oberflaeche", "register") == "symbolleisten"


    def vorlagenZurueck(self, k=None):
        if QMessageBox.question(self.w, "Vorlagen zurücksetzen",
                                "Register, Schnellzugriff und ausgetauschte Symbole auf die Vorgabe zurücksetzen?") != QMessageBox.Yes:
            return
        for key in ("ui/register_plan", "ui/schnellzugriff", "ui/symbol_tausch", "ui/oberflaeche"):
            self.w.settings.remove(key)
        self.w._symbole_anwenden()
        self.w.neu_bauen_band()


    # ---- Fenster ---------------------------------------------------------------------------
    def neuesFenster(self, k=None): self.w.neues_fenster()

    def fensterNebeneinander(self, k=None): self.w.fenster_anordnen("nebeneinander")

    def fensterUntereinander(self, k=None): self.w.fenster_anordnen("untereinander")

    def fensterKacheln(self, k=None): self.w.fenster_anordnen("kacheln")


    def fensterListe(self, k=None):
        self._popup(self.w.fensterliste_menue())


    # ---- Dokumentansichten ----------------------------------------------------------------
    def w_setzeLayout(self, k=None, art="blatt"):
        t = self.w.current_tab()
        if t:
            if art != "blatt" and t.editor.gliederung:
                self.gliederung()
            t.set_layout(art)
            self.w.band.aktualisieren(True)


    def w_layoutJetzt(self, k=None):
        t = self.w.current_tab()
        return t.layout_art if t else "blatt"


    def gliederung(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        if t.layout_art != "blatt":
            t.set_layout("blatt")
        t.editor.set_gliederung(not t.editor.gliederung)
        self.w.statusBar().showMessage(
            "Gliederung: nur Überschriften. Alt+Umschalt+←/→ ändert die Ebene." if t.editor.gliederung else "Gliederung beendet.", 5000)


    def an_gliederung(self):
        t = self.w.current_tab()
        return bool(t and t.editor.gliederung)


    # ---- Lineale ---------------------------------------------------------------------------
    def linealZeigen(self, k=None):
        self.w.settings.set("ansicht/lineal", not self.w.settings.get_bool("ansicht/lineal", False))
        self.w.lineale_anwenden()


    def linealHochZeigen(self, k=None):
        self.w.settings.set("ansicht/lineal_hoch", not self.w.settings.get_bool("ansicht/lineal_hoch", False))
        self.w.lineale_anwenden()


    def an_linealZeigen(self): return self.w.settings.get_bool("ansicht/lineal", False)

    def an_linealHochZeigen(self): return self.w.settings.get_bool("ansicht/lineal_hoch", False)


    # ---- Zoom ---------------------------------------------------------------------------
    def _zoom_um(self, faktor):
        if self.ed:
            self.ed.set_zoom(self.ed.zoom * faktor)


    def groesser(self, k=None): self._zoom_um(1.1)

    def kleiner(self, k=None): self._zoom_um(1 / 1.1)


    def normal(self, k=None):
        if self.ed:
            self.ed.set_zoom(1.0)


    def zoomBreite(self, k=None):
        t = self.w.current_tab()
        if t:
            t.zoom_breite()


    def zoomSeite(self, k=None):
        t = self.w.current_tab()
        if t:
            t.zoom_seite()


    def zoomStufe(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.ui.dialogs.dokument_dialoge import ZoomDialog
        d = ZoomDialog(self.w, self.ed.zoom)
        if d.exec():
            art, wert = d.ergebnis()
            if art == "breite":
                self.zoomBreite()
            elif art == "seite":
                self.zoomSeite()
            else:
                self.ed.set_zoom(wert)


    def lesehilfe(self, k=None):
        from lunivo_writer.ui.dialogs.lesehilfe_dialog import LesehilfeDialog
        d = LesehilfeDialog(self.w)
        d.zeige_unter(k if hasattr(k, "mapToGlobal") else None)
        self._lh = d


    def ausblenden(self, k=None):
        """Markierten Text als „ausgeblendet“ formatieren (Strg+Umschalt+H)."""
        if self.ed:
            self.ed.set_versteckt(not self.ed.ist_versteckt())


    def an_ausblenden(self): return bool(self.ed) and self.ed.ist_versteckt()


    def versteckteZeigen(self, k=None):
        self.w.settings.set("ui/versteckt_zeigen", not self.w.settings.get_bool("ui/versteckt_zeigen", False))
        self.w.versteckt_anwenden()


    def an_versteckteZeigen(self): return self.w.settings.get_bool("ui/versteckt_zeigen", False)


    def silbenfarben(self, k=None):
        from lunivo_writer.editor import silbenfarben as S
        k = S.konfig_lesen(self.w.settings)
        self.w.settings.set("lesehilfe/silben/an", not k["an"])
        self.w.silbenfarben_anwenden()
        self.w.statusBar().showMessage("Silben werden farbig angezeigt." if not k["an"] else "Silbenfarben aus.", 4000)


    def an_silbenfarben(self):
        from lunivo_writer.editor import silbenfarben as S
        return S.konfig_lesen(self.w.settings)["an"]


    def silbenEinstellen(self, k=None):
        from lunivo_writer.ui.dialogs.silben_dialog import SilbenDialog
        SilbenDialog(self.w).exec()


    # ==== Ansicht ==========================================================================================================================
    def markenZeigen(self, k=None):
        if self.ed:
            self.w.set_marken(not self.ed.marken)


    def an_markenZeigen(self): return bool(self.ed) and self.ed.marken


    def navigation(self, k=None):
        self.w.toggle_navigation()


    def an_navigation(self): return self.w.navigation.isVisible()
