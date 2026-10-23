"""Die Grundfarben des Programms mit Namen — der eine Ort, an dem ein Farbwert steht.

Wer eine Farbe braucht, schreibt ``Farbe.AKZENT`` statt ``"#2f6fb5"``. Ändert sich ein Farbton, ändert er sich hier und überall zugleich.
Die Namen sagen, wofür die Farbe da ist, nicht, wie sie aussieht. Die Farbtafeln des Designs (hell/dunkel) stehen in ``ui/theme.py``.
"""
from __future__ import annotations


class Farbe:
    SCHWARZ = "#000000"
    WEISS = "#ffffff"
    TINTE = "#343a40"               # dunkle Schrift und Striche auf hellem Grund
    TINTE_DUNKEL = "#212529"
    GRAU = "#868e96"                # gedämpft: Rahmen, Hinweise, Platzhalter
    GRAU_HELL = "#adb5bd"
    AKZENT = "#2f6fb5"              # die Hauptfarbe (Knöpfe, Auswahl) auf hellem Grund
    AKZENT_DUNKEL = "#4a8fd8"       # dieselbe Hauptfarbe auf dunklem Grund
    BLAU = "#4c6ef5"                # Bilder, Füllungen im Objektformat
    ROT = "#c92a2a"
    ORANGE = "#e8590c"
    GRUEN = "#2f9e44"
