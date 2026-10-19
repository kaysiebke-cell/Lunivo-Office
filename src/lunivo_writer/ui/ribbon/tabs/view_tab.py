"""Reiter „Ansicht“: register.json plus Schalter für ausgeblendeten Text."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


def bauen(register: dict) -> dict:
    ans = dict(next(t for t in register["register"] if t["name"] == "Ansicht"))
    ans["gruppen"] = [dict(g) for g in ans["gruppen"]]
    anz = next(g for g in ans["gruppen"] if g["name"] == "Anzeigen")
    if not any(k.get("tun") == "versteckteZeigen" for k in anz["knoepfe"]):
        anz["knoepfe"] = anz["knoepfe"] + [_k("vorschau", "Ausgeblendeter Text", "versteckteZeigen", haken=True)]
    return ans
