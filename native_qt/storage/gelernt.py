"""Das Gedächtnis der Prüfung: was dieser Mensch korrigiert oder stehen gelassen hat.

Liegt als JSON im Datenordner und verlässt den Rechner nicht.
"""
from __future__ import annotations

import json
import os
import re

from .settings import data_dir

WORT = re.compile(r"^[A-Za-zÄÖÜäöüß-]+$")
RUHE_NACH = 2          # so oft stehen gelassen, dann gilt das Wort als gewollt


class Gelernt:
    def __init__(self, pfad: str | None = None):
        self.pfad = pfad or os.path.join(data_dir(), "gelernt.json")
        self.daten = {"woerter": {}, "inRuhe": {}, "zaehler": {}}
        self.laden()

    def laden(self) -> None:
        try:
            with open(self.pfad, encoding="utf-8") as fh:
                d = json.load(fh)
            for k in self.daten:
                if isinstance(d.get(k), dict):
                    self.daten[k] = d[k]
        except (OSError, ValueError):
            pass

    def speichern(self) -> None:
        try:
            tmp = self.pfad + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.daten, fh, ensure_ascii=False)
            os.replace(tmp, self.pfad)
        except OSError:
            pass

    @staticmethod
    def wort_ebene(fund: dict) -> bool:
        return bool(fund.get("wortEbene")) and bool(WORT.match(fund["alt"])) and \
            fund["neu"].strip() == fund["neu"] and fund["neu"] != ""

    def gewaehlt(self, fund: dict) -> None:
        if self.wort_ebene(fund):
            self.daten["woerter"][fund["alt"].lower()] = fund["neu"].lower()
            self.daten["inRuhe"].pop(fund["alt"].lower(), None)
            self.speichern()

    def stehen_gelassen(self, fund: dict) -> None:
        if self.wort_ebene(fund):
            k = fund["alt"].lower()
            z = self.daten["zaehler"].get(k, 0) + 1
            self.daten["zaehler"][k] = z
            if z >= RUHE_NACH:
                self.daten["inRuhe"][k] = True
            self.speichern()

    def vergessen(self) -> None:
        self.daten = {"woerter": {}, "inRuhe": {}, "zaehler": {}}
        self.speichern()
