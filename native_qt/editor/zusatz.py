"""Zusatzdaten am Text: Kommentare, Fuß-/Endnoten, nachverfolgte Änderungen.

Sie hängen als eigene Eigenschaften am Zeichenformat (QTextCharFormat) und überleben so Bearbeiten, Rückgängig und
Kopieren innerhalb des Dokuments. Die Texte der Kommentare und Noten liegen in `meta` (siehe DocumentTab):

    meta["kommentare"] = {id: {"autor", "initialen", "datum", "text"}}
    meta["noten"]      = {"f": {id: text}, "e": {id: text}}      # Fußnoten, Endnoten
"""
from __future__ import annotations

from PySide6.QtGui import QTextFormat

P_KOMMENTAR = QTextFormat.UserProperty + 20      # int: Kommentar-Id
P_NOTE = QTextFormat.UserProperty + 21           # "f:3" | "e:2": Art und Id der Note
P_AENDERUNG = QTextFormat.UserProperty + 22      # "ins" | "del"
P_AUTOR = QTextFormat.UserProperty + 23
P_DATUM = QTextFormat.UserProperty + 24          # ISO-Text

ROEMISCH = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
            (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def roemisch(n: int) -> str:
    s = ""
    for w, r in ROEMISCH:
        while n >= w:
            s += r; n -= w
    return s


def neue_id(vorhanden) -> int:
    return max([int(k) for k in vorhanden] + [0]) + 1


def leere_meta() -> dict:
    return {"kommentare": {}, "noten": {"f": {}, "e": {}}}
