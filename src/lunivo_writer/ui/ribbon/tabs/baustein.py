"""Baustein für die Reiterbeschreibungen: ein Knopf als Wörterbuch."""
from __future__ import annotations


def k(symbol, name, tun=None, gross=False, **kw):
    e = {"symbol": symbol, "name": name, "gross": gross}
    if tun:
        e["tun"] = tun
    e.update(kw)
    return e


def alle(tab: dict) -> dict:
    """Alle Knöpfe eines Reiters aus register.json nach Namen."""
    return {e["name"]: e for g in tab["gruppen"] for e in g.get("knoepfe", []) if e.get("name")}


def uebrige(tab: dict, benutzt: set) -> list:
    """Knöpfe des Reiters, die in der neuen Anordnung noch nicht vorkommen (damit keine Funktion verloren geht)."""
    return [e for g in tab["gruppen"] for e in g.get("knoepfe", [])
            if e.get("name") and e["name"] not in benutzt and not e.get("zeilenumbruch")]
