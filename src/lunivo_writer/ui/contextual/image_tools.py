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
    {"name": "Formvorlagen", "knoepfe": [_k("stift", "Formvorlagen", klappe="formVorlagen", gross=True)]},
    {"name": "Formenstile", "knoepfe": [_k("toenung", "Formfüllung", klappe="formFuellung", text=True),
                                         _k("linie", "Formkontur", klappe="formKontur", text=True),
                                         _k("notiz", "Text in der Form …", "formText", text=True)]},
    {"name": "Anordnen", "knoepfe": [_k("gruppieren", "Gruppieren", "gruppieren", text=True),
                                     _k("gruppieren", "Gruppierung aufheben", "gruppeAufheben", text=True),
                                     _k("textflussumbruch", "Textumbruch / Position", "anordnen", text=True)]}]}


ZEICHENTOOLS = {"name": "Zeichentools", "kontext": "zeichen", "gruppen": [
    {"name": "Formstile", "knoepfe": [_k("stift", "Formstile", klappe="zeichenFormstile", gross=True),
                                      _k("toenung", "Formfüllung", klappe="zeichenFuellung", text=True),
                                      _k("linie", "Gliederung", klappe="zeichenGliederung", text=True),
                                      _k("texteffekt", "Formeffekte", "zeichenEffekte", text=True)]},
    {"name": "Format", "knoepfe": [_k("pinselchen", "Format übertragen", "zeichenFormatUebertragen", True)]},
    {"name": "Anordnen", "knoepfe": [_k("ausrichten", "Ausrichten", klappe="zeichenAusrichten", text=True),
                                     _k("gruppieren", "Gruppieren", "gruppieren", text=True),
                                     _k("objektdrehen", "Drehen", klappe="zeichenDrehen", text=True),
                                     _k("ebeneHoch", "Eine Ebene nach vorne", "zeichenVorn", text=True),
                                     _k("ebeneTief", "Eine Ebene nach hinten", "zeichenHinten", text=True),
                                     _k("textflussumbruch", "Textumbruch", "zeichenUmbruch", text=True)]},
    {"name": "Größe", "felder": "masse", "pfeil": "zeichenLayout", "knoepfe": []},
]}


SMARTARTTOOLS = {"name": "SmartArt-Tools", "kontext": "smartart", "gruppen": [
    {"name": "Inhalt", "knoepfe": [_k("notiz", "Text und Layout bearbeiten …", "smartartText", True)]},
    {"name": "Darstellung", "knoepfe": [_k("smartart", "Layout ändern", klappe="smartartLayout", gross=True),
                                         _k("farbe", "Farben ändern", klappe="smartartFarben", gross=True)]},
    {"name": "Position", "knoepfe": [_k("textflussumbruch", "Textumbruch / Position", "anordnen", text=True)]}]}
