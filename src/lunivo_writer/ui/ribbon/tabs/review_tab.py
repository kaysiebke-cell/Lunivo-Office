"""Reiter „Überprüfen“: Wörter zählen, Kommentare, Änderungen verfolgen, Vergleichen/Zusammenführen, Schützen.

Alles zu Rechtschreibung, Sprache, Prüfung und KI steht im Reiter „Schreibhilfe“ (Menü „Dokumentprüfung“) und in der Seitenleiste.
"""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import alle, k as _k


def bauen(register: dict) -> dict:
    tab = next(t for t in register["register"] if t["name"] == "Überprüfen")
    kn = alle(tab)
    gruppen = [{"name": "Dokument", "reihenfolge": True, "knoepfe": [dict(kn["Wörter zählen"], gross=True)]}]
    gruppen += [g for g in tab["gruppen"] if g["name"] in ("Kommentare", "Änderungen", "Schützen")]
    gruppen.append({"name": "Vergleichen", "reihenfolge": True, "knoepfe": [
        _k("kopie", "Vergleichen …", "dokumenteVergleichen", True),
        _k("zusammenfassen", "Zusammenführen …", "dokumenteZusammenfuehren", True)]})
    return dict(tab, gruppen=gruppen)
