"""Gemeinsame Kleinigkeiten der Befehls-Bausteine."""
from __future__ import annotations

from lunivo_writer.ui.baukasten import farb_symbol

_farbfeld = farb_symbol


class FreiMenue:
    """Die Menüs des Reiters Zeichentools: dieselben Baukasten-Menüs wie neben dem Bild, wirken aber auf den Editor, der bei der Wahl aktuell ist."""

    @staticmethod
    def formstile(cmd):
        from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin as F
        return F.frei_formstile_menue(None, None, lambda: cmd.ed)

    @staticmethod
    def fuell(cmd):
        from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin as F
        return F.frei_fuell_menue(None, None, lambda: cmd.ed)

    @staticmethod
    def kontur(cmd):
        from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin as F
        return F.frei_kontur_menue(None, None, lambda: cmd.ed)
