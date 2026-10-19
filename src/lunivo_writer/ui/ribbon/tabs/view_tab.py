"""Reiter „Ansicht“ in der Anordnung von WPS Office: Dokumentansichten (Vollbild, Lesemodus, Drucklayout, Weblayout), Navigationsbereich
mit den Anzeige-Schaltern, Zoom, Fenster; dazu Helligkeit und Oberfläche."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import alle, k as _k, uebrige


def bauen(register: dict) -> dict:
    tab = dict(next(t for t in register["register"] if t["name"] == "Ansicht"))
    tab["gruppen"] = [dict(g) for g in tab["gruppen"]]
    anz = next(g for g in tab["gruppen"] if g["name"] == "Anzeigen")
    if not any(e.get("tun") == "versteckteZeigen" for e in anz["knoepfe"]):
        anz["knoepfe"] = anz["knoepfe"] + [_k("vorschau", "Ausgeblendeter Text", "versteckteZeigen", haken=True)]
    kn = alle(tab)
    benutzt: set = set()

    def nimm(name, **kw):
        benutzt.add(name)
        return dict(kn[name], **kw)

    helligkeit = next(g for g in tab["gruppen"] if g["name"] == "Helligkeit")
    oberflaeche = next(g for g in tab["gruppen"] if g["name"] == "Oberfläche")
    for g in (helligkeit, oberflaeche):
        for e in g["knoepfe"]:
            benutzt.add(e["name"])
    gruppen = [
        {"name": "Dokumentansichten", "reihenfolge": True, "knoepfe": [
            _k("vollbild", "Vollbild", "vollbild", True, haken=True), nimm("Lesemodus", gross=True),
            nimm("Drucklayout", gross=True), nimm("Weblayout", gross=True), nimm("Gliederung", gross=True)]},
        {"name": "Anzeigen", "pfeil": anz.get("pfeil"), "reihenfolge": True, "knoepfe": [
            nimm("Navigationsbereich", gross=True), nimm("Lineal", text=True), nimm("Vertikales Lineal", text=True),
            nimm("Gitternetzlinien", text=True), nimm("Textbegrenzungen", text=True), nimm("Ausgeblendeter Text", text=True)]},
        {"name": "Zoom", "pfeil": "zoomStufe", "reihenfolge": True, "knoepfe": [
            nimm("Zoom", gross=True), nimm("100 %", text=True), nimm("Seitenbreite", text=True),
            nimm("Eine Seite", text=True), nimm("Zwei Seiten", text=True), nimm("Vergrößern", text=True), nimm("Verkleinern", text=True)]},
        dict(helligkeit, reihenfolge=True),
        {"name": "Fenster", "reihenfolge": True, "knoepfe": [
            nimm("Anordnen", gross=True), nimm("Neues Fenster", text=True), nimm("Fensterliste", text=True),
            nimm("Nebeneinander", text=True), nimm("Untereinander", text=True), nimm("Kacheln", text=True)]},
        dict(oberflaeche, reihenfolge=True),
    ]
    rest = [dict(e, gross=False, text=True) for e in uebrige(tab, benutzt)]
    if rest:
        gruppen.append({"name": "Weitere", "reihenfolge": True, "knoepfe": rest})
    return dict(tab, gruppen=gruppen)
