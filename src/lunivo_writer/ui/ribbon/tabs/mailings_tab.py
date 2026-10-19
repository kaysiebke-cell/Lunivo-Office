"""Reiter „Sendungen“ (nur nach „Register anpassen“ sichtbar): Serienbriefe und Formulare."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


def bauen(register: dict) -> dict:
    sen = dict(next(t for t in register["register"] if t["name"] == "Sendungen"))
    sen["gruppen"] = [dict(g) for g in sen["gruppen"]]
    form = next(g for g in sen["gruppen"] if g["name"] == "Formular")
    if not any(k.get("tun") == "formAuswahl" for k in form["knoepfe"]):
        form["knoepfe"] = form["knoepfe"] + [_k("punkte", "Auswahlliste", "formAuswahl"), _k("datum", "Datumsfeld", "formDatum"),
                                              _k("schliessen", "Felder zurücksetzen", "formLeeren")]
    return sen
