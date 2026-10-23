"""Befehle: Externe Programme."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox


class ExternBefehle:
    """Befehle des Bandes: Externe Programme. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ==== Externe Programme (Steuerung einer installierten Anwendung, keine Integration) ==========================
    def _extern(self, fn, name):
        t = self.w.current_tab()
        if not t:
            return
        if not t.path or t.is_modified():
            QMessageBox.information(self.w, name, "Bitte das Dokument zuerst speichern.")
            return
        if not fn(t.path):
            QMessageBox.information(self.w, name, f"{name} ist auf diesem Rechner nicht installiert.")


    def mitWpsOeffnen(self, k=None):
        from lunivo_writer.services.integrations import wps
        self._extern(wps.oeffnen, "WPS Writer")


    def mitLibreOfficeOeffnen(self, k=None):
        from lunivo_writer.services.integrations import wps
        self._extern(wps.mit_libreoffice_oeffnen, "LibreOffice")
