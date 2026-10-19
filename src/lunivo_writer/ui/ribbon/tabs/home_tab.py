"""Reiter „Start“ in der Anordnung von WPS Office."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


def bauen(start: dict) -> dict:
    """Reiter Start in der Anordnung von WPS Office: Zwischenablage (Einfügen, Ausschneiden/Kopieren, Format übertragen), Schriftart mit
    Name und Größe in einer Zeile, Absatz, Stile, dann Wort-Extras, Suchen oder ersetzen, Auswählen und Einstellungen als große Knöpfe."""
    alt = {g["name"]: g for g in start["gruppen"]}
    ablage = {"name": "Zwischenablage", "reihenfolge": True, "knoepfe": [
        _k("kleben", "Einfügen", "einfuegen", True, klappe="einfuegenKlappe"),
        _k("schere", "Ausschneiden", "ausschneiden", text=True),
        _k("kopie", "Kopieren", "kopieren", text=True),
        _k("pinsel", "Format übertragen", "formatUebertragen", True)]}
    schrift = dict(alt["Schriftart"], felder="zeile")
    absatz = dict(alt["Absatz"])
    extras = {"name": "Extras", "reihenfolge": True, "knoepfe": [
        _k("wortextras", "Wort-Extras", "wortExtras", True)]}
    suchen = {"name": "Suchen", "reihenfolge": True, "knoepfe": [
        _k("lupe", "Suchen oder ersetzen", gross=True, menue=[{"name": "Suchen …", "tun": "suchen"},
                                                              {"name": "Ersetzen …", "tun": "ersetzen"},
                                                              {"name": "Gehe zu …", "tun": "geheZu"}])]}
    waehlen = {"name": "Auswählen", "reihenfolge": True, "knoepfe": [
        _k("objekte", "Auswählen", gross=True, menue=[{"name": "Alles auswählen", "tun": "allesMarkieren"},
                                                      {"name": "Objekte auswählen", "tun": "objekteWaehlen"}])]}
    einst = {"name": "Einstellungen", "reihenfolge": True, "knoepfe": [
        _k("zahnrad", "Einstellungen", gross=True, menue=[{"name": "Optionen …", "tun": "w.optionenOeffnen"}])]}
    return dict(start, gruppen=[ablage, schrift, absatz, alt["Stile"], extras, suchen, waehlen, einst])

