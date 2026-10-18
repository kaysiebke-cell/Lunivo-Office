"""Silben farbig: Lesehilfe für Menschen mit Legasthenie.

Jede Silbe eines Wortes wird abwechselnd in einer anderen Farbe gezeigt. Das ist reine Anzeige (ein QSyntaxHighlighter): der Text,
die Formatierung und die gespeicherte Datei bleiben unverändert. Die Silben sind deutsche Sprechsilben (services/silben_de.py: Regeln für Vokalkerne und
Konsonanten, Wortbausteine aus den pyphen-Mustern); die Lesehilfe gilt nur für deutschen Text.
Einstellbar ist alles, was beim Lesen stört oder hilft: Farben, Darstellung, Mindestlänge, einsilbige Wörter, nur der aktuelle Absatz.
"""
from __future__ import annotations

import re
from PySide6.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat

PALETTEN = {
    "Blau / Rot": ["#1f5fbf", "#c92a2a"],
    "Blau / Orange": ["#1f5fbf", "#d9480f"],
    "Grün / Violett": ["#2b8a3e", "#862e9c"],
    "Dunkelblau / Braun": ["#1b3a6b", "#8a4b14"],
    "Drei Farben (Blau, Rot, Grün)": ["#1f5fbf", "#c92a2a", "#2b8a3e"],
    "Eigene Farben": None,
}
DARSTELLUNGEN = ["Schriftfarbe", "Hintergrund (Marker)", "Schriftfarbe und Hintergrund"]
BEISPIEL = ("Die Silbenfarben helfen beim Lesen: Wörter wie Schmetterling, Wanderung und Computertastatur "
            "werden in ihre Teile zerlegt.")
STANDARD = {"an": False, "palette": "Blau / Rot", "eigene": ["#1f5fbf", "#c92a2a", "#2b8a3e"], "anzahl_eigene": 2,
            "darstellung": "Schriftfarbe", "fett": False, "einsilbig": True, "neu_pro_wort": True, "mindestens": 4,
            "nur_absatz": False, "drucken": False, "sprache": "de_DE"}
_WORT = re.compile(r"[^\W\d_]{2,}", re.UNICODE)


def konfig_lesen(settings) -> dict:
    """Die Einstellungen (settings: Settings des Programms) als Wörterbuch mit allen Schlüsseln."""
    k = dict(STANDARD)
    g = lambda n: "lesehilfe/silben/" + n                                          # noqa: E731
    k["an"] = settings.get_bool(g("an"), STANDARD["an"])
    pal = settings.get(g("palette"), STANDARD["palette"])
    k["palette"] = pal if pal in PALETTEN else STANDARD["palette"]
    eig = [c for c in str(settings.get(g("eigene"), ",".join(STANDARD["eigene"]))).split(",") if QColor(c).isValid()]
    k["eigene"] = (eig + STANDARD["eigene"])[:3]
    k["anzahl_eigene"] = min(3, max(2, int(settings.get(g("anzahl_eigene"), 2))))
    d = settings.get(g("darstellung"), STANDARD["darstellung"])
    k["darstellung"] = d if d in DARSTELLUNGEN else STANDARD["darstellung"]
    for n in ("fett", "einsilbig", "neu_pro_wort", "nur_absatz", "drucken"):
        k[n] = settings.get_bool(g(n), STANDARD[n])
    k["mindestens"] = min(10, max(2, int(settings.get(g("mindestens"), STANDARD["mindestens"]))))
    k["sprache"] = settings.get(g("sprache"), settings.get("silben/sprache", "de_DE"))
    return k


def konfig_speichern(settings, k: dict) -> None:
    for n, v in k.items():
        if n == "eigene":
            v = ",".join(v)
        settings.set("lesehilfe/silben/" + n, v)


def farben(k: dict) -> list[str]:
    pal = PALETTEN.get(k["palette"])
    return list(pal) if pal else list(k["eigene"][:k["anzahl_eigene"]])


def verfuegbar(sprache: str = "de_DE") -> bool:
    """Die Regeln brauchen nichts außer Python; pyphen verbessert nur die Wortgrenzen in Zusammensetzungen."""
    return True


def silben(wort: str, sprache: str = "de_DE") -> tuple[str, ...]:
    """Das Wort in deutsche Sprechsilben (ein Eintrag, wenn es sich nicht teilen lässt)."""
    from ..services.silben_de import silben as _silben
    return _silben(wort)


def _formate(k: dict) -> list[QTextCharFormat]:
    out = []
    for hexfarbe in farben(k):
        f = QTextCharFormat()
        c = QColor(hexfarbe)
        if k["darstellung"] in ("Schriftfarbe", "Schriftfarbe und Hintergrund"):
            f.setForeground(QBrush(c))
        if k["darstellung"] in ("Hintergrund (Marker)", "Schriftfarbe und Hintergrund"):
            t = QColor(c)
            t.setAlpha(60)
            f.setBackground(QBrush(t))
        if k["fett"]:
            f.setFontWeight(QFont.Bold)
        out.append(f)
    return out


class SilbenFarben(QSyntaxHighlighter):
    """Färbt die Silben im Anzeige-Layout des Dokuments ein; verändert weder Text noch Formatierung."""

    def __init__(self, doc, konfig: dict, aktueller_block=None):
        super().__init__(doc)
        self.k = dict(konfig)
        self._aktuell = aktueller_block or (lambda: -1)
        self._f = _formate(self.k)
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        k = self.k
        if k["nur_absatz"] and self.currentBlock().blockNumber() != self._aktuell():
            return
        z = 0
        n = len(self._f)
        for m in _WORT.finditer(text):
            w = m.group()
            teile = silben(w, k["sprache"]) if len(w) >= k["mindestens"] else (w,)
            if len(teile) == 1 and not k["einsilbig"]:
                continue
            if k["neu_pro_wort"]:
                z = 0
            pos = m.start()
            for t in teile:
                self.setFormat(pos, len(t), self._f[z % n])
                pos += len(t)
                z += 1

    def neu_konfigurieren(self, konfig: dict) -> None:
        self.k = dict(konfig)
        self._f = _formate(self.k)
        self.rehighlight()
