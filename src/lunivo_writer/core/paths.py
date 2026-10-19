"""Orte der Programmdaten: Ressourcen im Paket, Symbole/Bilder/Schriften unter assets/."""
from __future__ import annotations

import os

PAKET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))           # …/src/lunivo_writer
RESSOURCEN = os.path.join(PAKET, "resources")
WURZEL = os.path.dirname(os.path.dirname(PAKET))                              # Projektordner
ASSETS = os.path.join(WURZEL, "assets") if os.path.isdir(os.path.join(WURZEL, "assets")) else os.path.join(PAKET, "assets")
SYMBOLE = os.path.join(ASSETS, "icons")
