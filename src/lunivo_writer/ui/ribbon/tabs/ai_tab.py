"""Reiter „Schreibhilfe“: Lesehilfe, Prüfen, Sprache, Bausteine und alle KI-Funktionen (kein eigener KI-Reiter)."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


KI = {"name": "KI", "gruppen": [
    {"name": "KI-Schreibwerkzeuge", "knoepfe": [_k("ki", "Text entwerfen", "kiEntwerfen", True),
                                                _k("zusammenfassen", "Text umformulieren", "kiUmformulieren"),
                                                _k("zusammenfassen", "Text zusammenfassen", "kiZusammenfassen"),
                                                _k("uebersetzen", "Text übersetzen", "w.kiUebersetzen"),
                                                _k("bild", "Text in Bild", "kiTextInBild")]},
    {"name": "Korrektur", "knoepfe": [_k("assistent", "KI-Korrektur", "kiKorrektur", True),
                                      _k("vorschlag", "Verbesserungsvorschläge", "kiVorschlaege", True)]},
    {"name": "Seitenleiste", "knoepfe": [_k("tafel", "Schreibhilfe-Seitenleiste", "tafelZeigen", True),
                                         _k("chat", "KI-Chat", "w.chatUmschalten", True)]},
    {"name": "Einrichten", "knoepfe": [_k("assistent", "Eigene Assistenten", klappe="assistenten", gross=True),
                                       _k("assistent", "Eigenen Assistenten erstellen", "w.assistentErstellen"),
                                       _k("kombination", "Eigenen Anbieter hinzufügen", "w.eigenenAnbieterHinzufuegen"),
                                       _k("zahnrad", "KI-Konfiguration", "w.kiKonfiguration")]},
]}


def bauen(register: dict) -> dict:
    sh = dict(next(t for t in register["register"] if t["name"] == "Schreibhilfe"))
    sh["gruppen"] = [dict(g) for g in sh["gruppen"]]
    lesen = next(g for g in sh["gruppen"] if g["name"] == "Lesen")
    if not any(k.get("tun") == "silbenfarben" for k in lesen["knoepfe"]):          # Lesehilfe für Legasthenie
        lesen["knoepfe"] = lesen["knoepfe"] + [_k("farbe", "Silben farbig", "silbenfarben", haken=True),
                                               _k("zahnrad", "Silben einstellen …", "silbenEinstellen")]
    vorhanden = {k.get("tun") for g in sh["gruppen"] for k in g["knoepfe"]}
    ki_gruppe = next((g for g in sh["gruppen"] if g["name"] == "KI"), None)
    for g in KI["gruppen"]:
        if g["name"] in ("Seitenleiste", "Korrektur"):           # beides steht schon in der Seitenleiste
            continue
        neu = [k for k in g["knoepfe"] if k.get("tun") not in vorhanden or not k.get("tun")]
        if g["name"] == "Einrichten" and ki_gruppe is not None:
            sh["gruppen"][sh["gruppen"].index(ki_gruppe)] = dict(ki_gruppe, knoepfe=ki_gruppe["knoepfe"] + neu)
        elif neu:
            ki_pos = sh["gruppen"].index(ki_gruppe) if ki_gruppe else len(sh["gruppen"])
            sh["gruppen"].insert(ki_pos, dict(g, knoepfe=neu))
    for g in sh["gruppen"]:                                   # Menü „Dokumentprüfung“: alles zur Rechtschreibung an einer Stelle
        g["knoepfe"] = [_pruefen_menue(e) if e.get("name") == "Dokumentprüfung" else e for e in g["knoepfe"]]
    return sh


def _pruefen_menue(e: dict) -> dict:
    e = {k: v for k, v in e.items() if k != "klappe"}
    e["menue"] = [
        {"name": "Prüfen", "tun": "w.pruefen"}, {"name": "Gründlich prüfen", "tun": "gruendlichPruefen"},
        {"name": "Rechtschreibung", "tun": "rechtschreibung"}, {"name": "Thesaurus", "tun": "thesaurus"},
        {"name": "Barrierefreiheit prüfen", "tun": "barrierefrei"}, {"name": "Welche Hilfe wann", "tun": "welcheHilfe"}, {"trenner": True},
        {"name": "Korrektursprache …", "tun": "pruefsprache"}]
    return e
