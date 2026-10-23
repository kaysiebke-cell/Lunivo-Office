"""Befehle: KI, Vorlesen."""
from __future__ import annotations

from PySide6.QtWidgets import QMenu


class KIBefehle:
    """Befehle des Bandes: KI, Vorlesen. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- KI: eigene Assistenten ----------------------------------------------------------------------------------------
    def w_assistentErstellen(self, k=None):
        """„Schnelle KI-Aktion erstellen“ — dasselbe wie „Eigenen Assistenten erstellen“: ein Eintrag in der Liste der Assistenten."""
        from lunivo_writer.ui.dialogs.ki_dialoge import SchnelleAktionDialog
        d = SchnelleAktionDialog(self.w)
        if d.exec():
            e = self.w.ki.konfig.assistent_hinzufuegen(*d.werte())
            self.w.ki.geaendert.emit()
            self.w.statusBar().showMessage(f"Aktion „{e['name']}“ angelegt (KI ▸ Eigene Assistenten).", 5000)


    def menue_assistenten(self):
        """Das Menü „KI-Aktionen“: die eigenen Schnellen KI-Aktionen, neue anlegen, entfernen und alle bisherigen Ergebnisse."""
        m = QMenu()

        def fuellen():
            m.clear()
            liste = self.w.ki.konfig["assistenten"]
            for a in liste:
                m.addAction(a["name"], lambda _=False, a=a: self.w.ki.assistent(a))
            if not liste:
                m.addAction("Noch keine eigenen KI-Aktionen").setEnabled(False)
            m.addSeparator()
            m.addAction("Neue Schnelle KI-Aktion …", self.w_assistentErstellen)
            if liste:
                entf = m.addMenu("KI-Aktion entfernen")
                for a in liste:
                    entf.addAction(a["name"], lambda _=False, a=a: (self.w.ki.konfig.assistent_entfernen(a["id"]), self.w.ki.geaendert.emit()))
            m.addSeparator()
            m.addAction("Alle Ergebnisse anzeigen", self.w_kiErgebnisse)
        m.aboutToShow.connect(fuellen)
        fuellen()
        return m


    def menue_silbenTrennungMenue(self):
        """Zur Silbentrennung: wo man die Trennstriche sieht (die Bearbeitungsansicht zeigt sie nicht) und die Einstellungen."""
        m = QMenu()
        m.addAction("Trennstriche in der Druckvorschau ansehen", self.silbentrennungVorschau)
        m.addAction("Einstellungen der Silbentrennung …", lambda: self.w.show_options("sprache"))
        return m


    def silbentrennungVorschau(self, k=None):
        self.tun("vorschau")


    def menue_silbenMenue(self):
        m = QMenu()
        m.addAction("Silben einstellen …", self.silbenEinstellen)
        return m


    # ==== Vorlesen ==================================================================================================
    def vorlesen(self, k=None):
        self.w.vorlesen(ab_hier=False)


    def vorlesenAbSatz(self, k=None):
        self.w.vorlesen(ab_hier=True)


    def vorlesenStopp(self, k=None):
        from lunivo_writer.services import vorlesen as v
        v.beenden()
        self.w.lbl_msg.setText("Vorlesen angehalten.")


    def stimmeWaehlen(self, k=None):
        self.w.stimme_waehlen()


    # ==== KI ========================================================================================================
    def kiKorrektur(self, k=None): self.w.ki.korrigieren()

    def kiVorschlaege(self, k=None):
        self.w.sidebar._funde_zeigen(); self.w.ki.vorschlaege_holen()

    def kiUmformulieren(self, k=None): self.w.ki.text_aktion("umformulieren")

    def kiZusammenfassen(self, k=None):
        self.w.sidebar._funde_zeigen(); self.w.ki.zusammenfassen()

    def w_kiUebersetzen(self, k=None): self.w.ki.uebersetzen()                      # Markierung → ersetzen, sonst Übersetzung zeigen

    def w_kiUebersetzenErsetzen(self, k=None): self.w.ki.uebersetzen(modus="ersetzen")

    def w_kiUebersetzenZeigen(self, k=None): self.w.ki.uebersetzen(modus="zeigen")


    def menue_uebersetzenMenue(self):
        m = QMenu()
        m.addAction("Markierung im Text ersetzen", self.w_kiUebersetzenErsetzen)
        m.addAction("Übersetzung in Schreibhilfe und Chat zeigen", self.w_kiUebersetzenZeigen)
        m.addSeparator()
        m.addAction("Sprache wählen …", self.w_kiSprache)
        return m


    def kiEntwerfen(self, k=None): self.w.chat_oeffnen("Entwirf einen Text zu folgendem Anliegen: ")

    def w_chatUmschalten(self, k=None): self.w.chat_oeffnen("")

    def _ki_einstellungen(self, reiter: int) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
        ausfuehren(KIEinstellungenDialog(self.w, reiter))


    def w_kiEinstellungen(self, k=None): self._ki_einstellungen(0)

    def w_kiKonfiguration(self, k=None): self._ki_einstellungen(1)

    def w_kiSprache(self, k=None): self._ki_einstellungen(2)

    def w_eigenenAnbieterHinzufuegen(self, k=None): self._ki_einstellungen(0)


    def w_kiErgebnisse(self, k=None):
        from lunivo_writer.ui.dialogs.ki_dialoge import ErgebnisseDialog
        ErgebnisseDialog(self.w).exec()


    def kiTextInBild(self, k=None): self.w.ki.bild_aus_text()

    def kiTextAktion(self, k=None, aktion="verbessern"): self.w.ki.text_aktion(aktion)
