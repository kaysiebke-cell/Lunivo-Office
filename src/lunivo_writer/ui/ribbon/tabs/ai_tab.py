"""Reiter „Schreibhilfe“: Lesen, Prüfen, Beim Schreiben, Vorlesen, Sprache, Bausteine, KI und Anzeigen — jede Funktion einmal, jede mit eigenem Symbol.

Die Knöpfe kommen aus ``ui/schreibhilfe_katalog.py`` (derselbe Katalog wie die Werkbank in der Seitenleiste); nur die Menüknöpfe Dokumentprüfung, Vorlesen und
Textbausteine sowie die Seitenleiste kommen aus register.json."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k
from lunivo_writer.ui.schreibhilfe_katalog import fuer_gruppe


def _knoepfe(gruppe: str) -> list[dict]:
    """Die Band-Knöpfe einer Gruppe: erst die kleinen, dann die großen."""
    out = []
    for f in sorted(fuer_gruppe(gruppe), key=lambda f: f.gross):
        kw = {"klappe": f.klappe} if f.klappe else {}
        if f.art == "schalter":
            kw["haken"] = True
        out.append(_k(f.symbol, f.name.removesuffix(" …"), f.tun or None, f.gross, text=not f.gross, **kw))
    return out


def _pruefen_menue(e: dict) -> dict:
    """Das eine Prüfmenü: wann geprüft wird (F7), gründlich, mit KI (F8), Hilfen und die Sprache des Dokuments."""
    e = {k: v for k, v in e.items() if k != "klappe"}
    e["menue"] = [
        {"name": "Prüfen", "tun": "w.pruefen"}, {"name": "Gründlich prüfen", "tun": "gruendlichPruefen"},
        {"name": "KI-Korrektur", "tun": "kiKorrektur"}, {"name": "Verbesserungsvorschläge", "tun": "kiVorschlaege"}, {"trenner": True},
        {"name": "Barrierefreiheit prüfen", "tun": "barrierefrei"}, {"name": "Welche Hilfe wann", "tun": "welcheHilfe"}, {"trenner": True},
        {"name": "Korrektursprache …", "tun": "pruefsprache"}]
    return e


def bauen(register: dict) -> dict:
    sh = dict(next(t for t in register["register"] if t["name"] == "Schreibhilfe"))
    reg = {k["name"]: dict(k) for g in sh["gruppen"] for k in g["knoepfe"]}
    pfeile = {g["name"]: g.get("pfeil") for g in sh["gruppen"]}

    def gruppe(name: str, knoepfe: list, **kw) -> dict:
        g = {"name": name, "knoepfe": knoepfe}
        g.update({k: v for k, v in kw.items() if v})
        return g
    sh["gruppen"] = [
        gruppe("Lesen", _knoepfe("Lesen"), pfeil=pfeile.get("Lesen")),
        gruppe("Prüfen", [_pruefen_menue(reg["Dokumentprüfung"])]),
        gruppe("Beim Schreiben", _knoepfe("Beim Schreiben")),
        gruppe("Vorlesen", [reg["Vorlesen"]]),
        gruppe("Sprache", _knoepfe("Sprache"), pfeil="w.kiSprache"),
        gruppe("Bausteine", [reg["Textbausteine"]]),
        gruppe("KI", _knoepfe("KI")),
        gruppe("Anzeigen", [reg["Seitenleiste Schreibhilfe"]]),
    ]
    return sh
