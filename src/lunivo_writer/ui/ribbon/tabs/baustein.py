"""Baustein für die Reiterbeschreibungen: ein Knopf als Wörterbuch."""
from __future__ import annotations


def k(symbol, name, tun=None, gross=False, **kw):
    e = {"symbol": symbol, "name": name, "gross": gross}
    if tun:
        e["tun"] = tun
    e.update(kw)
    return e
