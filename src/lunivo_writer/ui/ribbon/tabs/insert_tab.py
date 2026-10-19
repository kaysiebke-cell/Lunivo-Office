"""Reiter „Einfügen“ in der Anordnung von WPS Office: Seiten, Tabelle, Bild/Formen/Diagramm, Kommentar, Kopf- und Fußzeile,
Text, Symbole, Hyperlink mit Querverweis und Lesezeichen, Formulare. Was WPS dort nicht hat, steht in „Weitere“."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import alle, k as _k, uebrige


def bauen(register: dict) -> dict:
    tab = next(t for t in register["register"] if t["name"] == "Einfügen")
    kn = alle(tab)
    benutzt: set = set()

    def nimm(name, **kw):
        benutzt.add(name)
        return dict(kn[name], **kw)

    kommentar = next(e for t in register["register"] if t["name"] == "Überprüfen" for g in t["gruppen"]
                     for e in g["knoepfe"] if e.get("tun") == "kommentar")
    formulare = _k("formfeld", "Formulare", gross=True, menue=[
        {"name": "Textfeld", "tun": "formTextfeld"}, {"name": "Auswahlliste", "tun": "formAuswahl"},
        {"name": "Datumsfeld", "tun": "formDatum"}, {"name": "Kontrollkästchen", "tun": "formKasten"},
        {"name": "Schaltfläche", "tun": "formKnopf"}, {"trenner": True}, {"name": "Felder zurücksetzen", "tun": "formLeeren"}])
    gruppen = [
        {"name": "Seiten", "reihenfolge": True, "knoepfe": [
            nimm("Deckblatt", gross=True), nimm("Leere Seite", gross=True), nimm("Seitenumbruch", gross=True)]},
        {"name": "Tabellen", "reihenfolge": True, "knoepfe": [
            nimm("Tabelle einfügen", gross=True), nimm("Schnelltabelle", text=True), nimm("Eigenschaften", text=True)]},
        {"name": "Illustrationen", "reihenfolge": True, "knoepfe": [
            nimm("Bild", gross=True), nimm("Formen", gross=True), nimm("Diagramm", text=True), nimm("SmartArt", text=True)]},
        {"name": "Kommentar", "reihenfolge": True, "knoepfe": [dict(kommentar, name="Kommentar", gross=True)]},
        {"name": "Kopf- und Fußzeile", "reihenfolge": True, "knoepfe": [
            nimm("Kopf- und Fußzeile", gross=True), nimm("Seitenzahl", gross=True),
            _k("wasserzeichen", "Wasserzeichen", "wasserzeichen", True)]},
        {"name": "Text", "reihenfolge": True, "knoepfe": [
            nimm("Textfeld", gross=True), nimm("WordArt", gross=True), nimm("Datum und Uhrzeit", gross=True),
            nimm("Initiale", text=True), nimm("Text aus Datei", text=True)]},
        {"name": "Symbole", "reihenfolge": True, "knoepfe": [nimm("Sonderzeichen", gross=True), nimm("Formel", gross=True)]},
        {"name": "Links", "reihenfolge": True, "knoepfe": [
            nimm("Hyperlink", gross=True), nimm("Querverweis", text=True), nimm("Lesezeichen / Textmarke", text=True)]},
        {"name": "Formulare", "reihenfolge": True, "knoepfe": [formulare]},
    ]
    rest = [dict(e, gross=False, text=True) for e in uebrige(tab, benutzt)]
    if rest:
        gruppen.append({"name": "Weitere", "reihenfolge": True, "knoepfe": rest})
    return dict(tab, gruppen=gruppen)
