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
    return {"kommentare": {}, "noten": {"f": {}, "e": {}}, "quellen": [], "zitierweise": "APA"}

P_FELD = QTextFormat.UserProperty + 26           # Feldanweisung, z. B. "SEQ Abbildung \* ARABIC"; der Text ist das Feldergebnis
P_INDEX = QTextFormat.UserProperty + 27          # Stichwort für das Stichwortverzeichnis
P_ZITAT = QTextFormat.UserProperty + 28          # Tag der zitierten Quelle
P_VERSTECKT = QTextFormat.UserProperty + 32      # 1: ausgeblendeter Text (DOCX w:vanish)
P_OBJEKT = QTextFormat.UserProperty + 33         # am Bild: JSON {"art": "form|wordart|diagramm|smartart|formel|piktogramm", "daten": {…}}

# Absatz-Eigenschaften (QTextBlockFormat); STYLE_PROP = UserProperty + 1 gehört den Formatvorlagen
B_TOC = QTextFormat.UserProperty + 2             # "kopf" | "zeile1".."zeile3" — Teil eines Verzeichnisses
B_ART = QTextFormat.UserProperty + 3             # "toc" | "abb" | "tab" | "index" | "lit"
B_CAP = QTextFormat.UserProperty + 4             # Beschriftung: Bezeichnung ("Abbildung", "Tabelle", …)

BESCHRIFTUNGEN = ("Abbildung", "Tabelle", "Gleichung")

B_NOTENZIEL = QTextFormat.UserProperty + 7       # "e:3": Absatz ist der Text einer Endnote (Sprungziel in der PDF)
B_SPALTE = QTextFormat.UserProperty + 6          # 1: Spaltenumbruch vor diesem Absatz (ein Seitenumbruch der Spaltenseite)
B_RAHMEN = QTextFormat.UserProperty + 5          # Absatzrahmen: "farbe|breite_pt|art" und ggf. "|seiten" (siehe editor/linie.py)
B_ANKER = QTextFormat.UserProperty + 8           # 1: leerer Hilfsabsatz vor einem schwebenden Bild (Anker, wird nicht gespeichert)
B_MUSTER = QTextFormat.UserProperty + 9           # Schattierungsmuster: "schlüssel|musterfarbe|füllfarbe" (siehe editor/muster.py)
B_MEHRSTUFIG = QTextFormat.UserProperty + 36      # Absatz einer mehrstufigen Liste: "ebene|JSON der Gliederung" (siehe editor/mehrstufig.py)
