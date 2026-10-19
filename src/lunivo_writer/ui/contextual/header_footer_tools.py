"""Kontext-Reiter „Kopf- und Fußzeilentools“."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


KOPFFUSS = {"name": "Kopf- und Fußzeilentools", "kontext": "kopffuss", "gruppen": [
    {"name": "Entwurf", "knoepfe": [_k("kopfz", "Kopfzeile bearbeiten", "kopfFussZeigen", True),
                                    _k("fussz", "Fußzeile bearbeiten", "fusszeileBearbeiten", True),
                                    _k("seitenzahl", "Seitenzahl einfügen", "seitenzahlKlappe"),
                                    _k("kopffuss", "Erste Seite anders", "ersteSeiteAnders"),
                                    _k("kopffuss", "Gerade/ungerade Seiten unterschiedlich", "geradeUngerade"),
                                    _k("schliessen", "Kopf- und Fußzeile schließen", "kopfFussSchliessen")]}]}
