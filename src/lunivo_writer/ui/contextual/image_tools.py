"""Kontext-Reiter „Bildtools“ und „Form- und WordArt-Tools“."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


BILDTOOLS = {"name": "Bildtools", "kontext": "bild", "gruppen": [
    {"name": "Format: Größe", "knoepfe": [
        _k("bild", "Größe und Seitenverhältnis …", "bildGroesse", True),
        _k("einpassen", "Auf Seitenbreite", "bildBreite"),
        _k("bild", "Originalgröße", "bildOriginal")]},
    {"name": "Beschreibung", "knoepfe": [_k("notiz", "Alternativtext …", "bildAltText", True)]},
    {"name": "Bearbeiten", "knoepfe": [_k("kanteKeine", "Bild entfernen", "bildEntfernen"),
                                       _k("bild", "Zuschneiden", "bildZuschneiden"),
                                       _k("farbe", "Helligkeit / Kontrast / Farbe", "bildFarbe"),
                                       _k("textflussumbruch", "Textumbruch / Position", "anordnen")]},
]}

FORMTOOLS = {"name": "Form- und WordArt-Tools", "kontext": "form", "gruppen": [
    {"name": "Format", "knoepfe": [_k("stift", "Formvorlagen", "formVorlagen", True),
                                    _k("toenung", "Formfüllung", "formFuellung"),
                                    _k("linie", "Formkontur", "formKontur"),
                                    _k("anordnen", "Anordnen / Gruppieren", "gruppieren")]}]}
