"""Das Gedächtnis der Prüfung: was dieser Mensch korrigiert oder stehen gelassen hat.

Liegt als JSON im Datenordner und verlässt den Rechner nicht.
"""
from __future__ import annotations

import json
import os
import re

from lunivo_writer.services.settings_service import data_dir

WORT = re.compile(r"^[A-Za-zÄÖÜäöüß-]+$")
LERN_SCHWELLE = 5      # so oft darf ein Fund bei ausdrücklichem „Prüfen“ angezeigt und nie geändert werden


class Gelernt:
    def __init__(self, pfad: str | None = None):
        self.pfad = pfad or os.path.join(data_dir(), "gelernt.json")
        self.daten = {"woerter": {}, "inRuhe": {}, "gezeigt": {}, "ki": {}}
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
            k = fund["alt"].lower()
            self.daten["woerter"][k] = fund["neu"]
            self.daten["gezeigt"].pop(k, None)          # angenommen ist das Gegenteil von ignoriert
            self.daten["inRuhe"].pop(k, None)
            self.speichern()

    def merke_gezeigt(self, funde: list) -> None:
        """Beim ausdrücklichen Prüfen: wer denselben Fund fünfmal stehen lässt, meint es so (Wort kommt in Ruhe).
        Die lebende Prüfung zählt nicht — sonst verschwänden Wellenlinien von selbst."""
        geaendert = False
        for f in funde:
            if not self.wort_ebene(f):
                continue
            k = f["alt"].lower()
            if self.daten["woerter"].get(k) or self.daten["inRuhe"].get(k):
                continue
            n = self.daten["gezeigt"].get(k, 0) + 1
            if n >= LERN_SCHWELLE:
                self.daten["inRuhe"][k] = True
                self.daten["gezeigt"].pop(k, None)
            else:
                self.daten["gezeigt"][k] = n
            geaendert = True
        if geaendert:
            self.speichern()

    def ki_vermerken(self, vorschlag: dict, angenommen: bool) -> None:
        """Die Sicherheit (konfidenz) eines KI-Vorschlags und ob er angenommen wurde — für die Trefferquote je Sicherheitsstufe.
        Es wird nur die Zahl gespeichert, nie der Text."""
        stufe = str(min(9, int(float(vorschlag.get("konfidenz", 0.5)) * 10)))
        e = self.daten["ki"].setdefault(stufe, {"angenommen": 0, "abgelehnt": 0})
        e["angenommen" if angenommen else "abgelehnt"] += 1
        self.speichern()

    def ki_trefferquote(self, stufe: int) -> float | None:
        e = self.daten["ki"].get(str(stufe))
        n = (e["angenommen"] + e["abgelehnt"]) if e else 0
        return e["angenommen"] / n if n else None

    def vergessen(self) -> None:
        self.daten = {"woerter": {}, "inRuhe": {}, "gezeigt": {}, "ki": {}}
        self.speichern()
