"""Reiter „Verweise“ (in register.json „Referenzen“) in der Anordnung von WPS Office: Inhaltsverzeichnis, Fuß- und Endnoten
mit Vorher/Nächste, Beschriftung mit Abbildungsverzeichnis und Querverweis, Indexeintrag, Seriendruck; Zitate und Literatur bleiben."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import alle, k as _k, uebrige


def bauen(register: dict) -> dict:
    tab = dict(next(t for t in register["register"] if t["name"] == "Referenzen"), name="Verweise")
    kn = alle(tab)
    benutzt: set = set()

    def nimm(name, **kw):
        benutzt.add(name)
        return dict(kn[name], **kw)

    zitate = next(g for g in tab["gruppen"] if g["name"] == "Zitate und Literatur")
    for e in zitate["knoepfe"]:
        benutzt.add(e["name"])
    gruppen = [
        {"name": "Inhaltsverzeichnis", "reihenfolge": True, "knoepfe": [
            nimm("Inhaltsverzeichnis", gross=True), nimm("Verzeichnisse aktualisieren", gross=True)]},
        {"name": "Fußnoten", "reihenfolge": True, "knoepfe": [
            nimm("Fußnote", gross=True), nimm("Endnote", gross=True),
            nimm("Vorige Note", text=True), nimm("Nächste Note", text=True), nimm("Notenbereich", text=True)]},
        {"name": "Beschriftungen", "reihenfolge": True, "knoepfe": [
            nimm("Beschriftung", gross=True), nimm("Abbildungsverzeichnis", text=True), nimm("Querverweis", text=True)]},
        {"name": "Index", "reihenfolge": True, "knoepfe": [
            nimm("Indexeintrag", gross=True), nimm("Stichwortverzeichnis", text=True)]},
        dict(zitate, reihenfolge=True, knoepfe=[dict(e, gross=(i == 0), text=(i > 0)) for i, e in enumerate(zitate["knoepfe"])]),
        {"name": "Seriendruck", "reihenfolge": True, "knoepfe": [
            _k("serie", "Seriendruck", "seriendruck", True)]},
    ]
    rest = [dict(e, gross=False, text=True) for e in uebrige(tab, benutzt)]
    if rest:
        gruppen.append({"name": "Weitere", "reihenfolge": True, "knoepfe": rest})
    return dict(tab, gruppen=gruppen)
