"""Optionen: Name und KI, dazu die Werkzeug-Fenster (Menüband, Schnellzugriff, Kennwort, Änderungen verfolgen)."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QScrollArea, QVBoxLayout

from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import _Seite


class NameKiSeiten:
    """Optionen: Name und KI. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""

    # Werkzeuge, die keine Einstellung sind: eigenes Fenster statt eigener Seite in der Liste
    FENSTER = {"menueband": ("Menüband anpassen", "_menueband"), "schnellzugriff": ("Symbolleiste für den Schnellzugriff", "_schnellzugriff"),
               "sicherheit": ("Kennwort und Datenschutz", "_sicherheit"), "verfolgen": ("Änderungen verfolgen", "_verfolgen")}


    def _name_ki(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Wer schreibt")
        f.addRow("Name", p.eingabe("benutzer/name", "Name (Autor in DOCX-Dokumenten)"))
        f.addRow("Initialen", p.eingabe("benutzer/initialen", "z. B. KS"))
        p.haken(f, "benutzer/verwenden", "Diese Benutzerinformationen verwenden", True)
        e = p.mehr("Adresse für Briefe und Datenschutz")
        f = p.unter(e, "Adresse")
        p.felder(f, [("benutzer/strasse", "Straße und Hausnummer"), ("benutzer/plz_ort", "PLZ und Ort"), ("benutzer/ort", "Ort (für „Ort, Datum“)"),
                     ("benutzer/telefon", "Telefon"), ("benutzer/mail", "E-Mail")])
        p.zeile(f, "Bleibt auf diesem Rechner und geht nie mit einem Text an die KI.")
        p.haken(f, "sicherheit/personendaten_weg", "Beim Speichern persönliche Daten entfernen", False)
        e = p.mehr("KI einrichten (Schlüssel, Modelle, Verbrauch)")
        e.innen.addWidget(self._ki(""))
        e = p.mehr("Was zusätzlich geholt wurde")
        e.innen.addWidget(self._erweitert(""))
        p.abschluss()
        return p


    def _anpassen(self, key: str) -> None:
        """Eines der Werkzeuge als Fenster zeigen; das Band wird danach neu gebaut, wenn es sich geändert hat."""
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        titel, bauer = self.FENSTER[key]
        d = QDialog(self)
        d.setWindowTitle(titel)
        d.resize(920, 660)
        v = QVBoxLayout(d)
        v.setContentsMargins(12, 12, 12, 8)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QScrollArea.NoFrame)
        sc.setWidget(getattr(self, bauer)(""))
        v.addWidget(sc, 1)
        v.addWidget(knopfzeile(d, ok_text="Fertig", nur_ok=True))
        ausfuehren(d)
        self._band_jetzt()
