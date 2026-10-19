"""Reiter „Datei“ (die Backstage-Ansicht ersetzt das Band; die Gruppen bleiben als Vorlage für Menüs und Symbolleisten)."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


DATEI = {"name": "Datei", "gruppen": [
    {"name": "Neu", "knoepfe": [_k("neu", "Leeres Dokument", "neu", True),
                                _k("vorlage", "Aus Vorlage erstellen", "neuAusVorlage"),
                                _k("lupe", "Vorlagen durchsuchen", "vorlagenDurchsuchen")]},
    {"name": "Öffnen", "knoepfe": [_k("oeffnen", "Öffnen", "oeffnen", True),
                                   _k("zuletzt", "Zuletzt verwendete Dokumente", klappe="zuletzt")]},
    {"name": "Speichern", "knoepfe": [_k("speichern", "Speichern", "speichern", True),
                                      _k("speichern", "Speichern unter", "speichernUnter"),
                                      _k("kopie", "Kopie speichern", "kopieSpeichern")]},
    {"name": "Exportieren", "knoepfe": [_k("pdf", "Als PDF exportieren", "speichernPdf", True),
                                        _k("ausdatei", "Als DOCX exportieren", "exportierenDocx"),
                                        _k("ausdatei", "Als DOC exportieren (optional)", "exportierenDoc"),
                                        _k("//", "x"),
                                        _k("ausdatei", "Als RTF exportieren", "exportierenRtf"),
                                        _k("notiz", "Als TXT exportieren", "exportierenTxt"),
                                        _k("buch", "Als ODT exportieren", "exportierenOdt"),
                                        _k("bild", "Als Bild exportieren (PNG)", "exportierenPng")]},
    {"name": "Drucken", "knoepfe": [_k("drucken", "Drucken", "drucken", True),
                                    _k("vorschau", "Druckvorschau", "vorschau"),
                                    _k("drucker2", "Drucker auswählen", "druckerWaehlen"),
                                    _k("//", "x"),
                                    _k("abschnitt", "Seitenbereich", "druckerWaehlen"),
                                    _k("einstellungen", "Druckeinstellungen", "druckerWaehlen")]},
    {"name": "Dokument", "knoepfe": [_k("inhalt", "Dokumentinformationen", "eigenschaften", True),
                                     _k("sperren", "Dokument schützen", "dokumentSchuetzen"),
                                     _k("verknuepft", "Dokument teilen (optional)", "dokumentTeilen"),
                                     _k("//", "x"),
                                     _k("buch", "Mit WPS Writer öffnen", "mitWpsOeffnen"),
                                     _k("buch", "Mit LibreOffice öffnen", "mitLibreOfficeOeffnen")]},
    {"name": "Programm", "knoepfe": [_k("optionen", "Optionen / Einstellungen", "w.optionenOeffnen", True),
                                     _k("schliessen", "Schließen", "schliessen")]},
]}


def bauen(register: dict) -> dict:
    return DATEI
