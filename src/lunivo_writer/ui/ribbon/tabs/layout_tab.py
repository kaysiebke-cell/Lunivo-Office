"""Reiter „Seitenlayout“ in der Anordnung von WPS Office: Designs, Ränder mit den vier Maßfeldern, Seite einrichten
(Orientierung, Größe, Spalten, Textrichtung, Umbrüche, Zeilennummern), Seitenhintergrund und Anordnen.
Einzug, Absatzabstand und Silbentrennung stehen wie bei WPS nicht hier, sondern unter Start ▸ Absatz und Schreibhilfe."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


def bauen(register: dict) -> dict:
    tab = next(t for t in register["register"] if t["name"] == "Seitenlayout")
    alt = {g["name"]: g for g in tab["gruppen"]}
    knopf = {k["name"]: k for g in tab["gruppen"] for k in g.get("knoepfe", [])}

    def mit(name, **kw):
        return dict(knopf[name], **kw)

    spalten = mit("Spalten", gross=True)
    menue = list(spalten["menue"])
    if not any(e.get("name") == "Vier" for e in menue):                  # 1 bis 4 Spalten
        menue.insert(3, {"name": "Vier", "tun": "spaltenSetzen:[4]", "haken": "w.spaltenJetzt"})
    spalten["menue"] = menue

    designs = {"name": "Designs", "reihenfolge": True, "knoepfe": [
        mit("Designs", gross=True), mit("Farben", text=True), mit("Schriftarten", symbol="Stil", text=True), mit("Effekte", gross=True)]}
    raender = {"name": "Ränder", "felder": "raender", "reihenfolge": True, "knoepfe": [mit("Ränder", gross=True)]}
    einrichten = {"name": "Seite einrichten", "pfeil": alt["Seite einrichten"].get("pfeil"), "reihenfolge": True, "knoepfe": [
        mit("Ausrichtung", gross=True), mit("Größe", gross=True), spalten, mit("Textrichtung", gross=True),
        mit("Umbrüche", text=True), mit("Zeilennummern", text=True)]}
    hintergrund = {"name": "Seitenhintergrund", "reihenfolge": True, "knoepfe": [
        mit("Seitenfarbe", gross=True), mit("Seitenränder", gross=True), mit("Wasserzeichen", gross=True)]}
    anordnen = {"name": "Anordnen", "reihenfolge": True, "knoepfe": [
        mit("Textfluss", gross=True), mit("Ausrichten", gross=True), mit("Gruppieren", text=True), mit("Drehen", text=True),
        _k("objekte", "Auswahlbereich", "objekteWaehlen", True)]}
    return dict(tab, gruppen=[designs, raender, einrichten, hintergrund, anordnen])
