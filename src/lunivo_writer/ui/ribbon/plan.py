"""Die Reiterleiste nach der Struktur „LUNIVO WRITER“: Datei, Start, Einfügen, Seitenlayout, Verweise, Überprüfen,
Schreibhilfe, Ansicht (+ „Sendungen“ nach Register anpassen) und die Kontext-Reiter für Tabellen, Bilder/Formen und Kopf-/Fußzeile.

Jeder Reiter hat sein Modul unter ribbon/tabs/ bzw. contextual/; hier werden sie in der Reihenfolge der Struktur zusammengesetzt.
Die Prüfungen der Schreibhilfe stehen zusätzlich in der rechten Seitenleiste.
"""
from __future__ import annotations

from lunivo_writer.ui.contextual.header_footer_tools import KOPFFUSS
from lunivo_writer.ui.contextual.image_tools import BILDTOOLS, FORMTOOLS
from lunivo_writer.ui.contextual.table_tools import TABELLENTOOLS
from lunivo_writer.ui.ribbon.tabs import (ai_tab, file_tab, home_tab, insert_tab, layout_tab, mailings_tab, references_tab,
                                          review_tab, section_tab, view_tab)


def plan(register: dict) -> list[dict]:
    """Die Reiter in der Reihenfolge der Struktur; Kontext-Register stehen am Ende (zunächst verborgen)."""
    start = home_tab.bauen(next(t for t in register["register"] if t["name"] == "Start"))
    reiter = [file_tab.bauen(register), start, insert_tab.bauen(register), layout_tab.bauen(register),
              references_tab.bauen(register), review_tab.bauen(register), ai_tab.bauen(register), view_tab.bauen(register),
              section_tab.bauen(register), mailings_tab.bauen(register)]
    return reiter + [TABELLENTOOLS, BILDTOOLS, FORMTOOLS, KOPFFUSS]
