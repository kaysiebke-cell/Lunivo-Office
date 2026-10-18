#!/usr/bin/env python3
"""Wandelt oberflaeche/daten/symbolkatalog.js (Lucide, 24×24-Pfade) in native_qt/resources/symbolkatalog.json um.

Das JSON wird vom nativen Programm beim ersten Gebrauch geladen (Piktogramm einfügen, Symbol austauschen)."""
import json
import os
import re

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
quelle = open(os.path.join(WURZEL, "oberflaeche/daten/symbolkatalog.js"), encoding="utf-8").read()
katalog = {}
for m in re.finditer(r'^"([^"]+)":\s*"([^"]*)",?\s*$', quelle, re.M):
    katalog[m.group(1)] = m.group(2)
ziel = os.path.join(WURZEL, "native_qt/resources/symbolkatalog.json")
json.dump(katalog, open(ziel, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(katalog), "Symbole →", ziel)
