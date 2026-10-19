"""Reiter „Abschnitt“ in der Anordnung von WPS Office.

Abschnitte (editor/abschnitte.py): hinzufügen (nächste Seite, fortlaufend, gerade, ungerade), löschen, vor/zurück, Navigation, eigene
Orientierung, Größe, Ränder, Spalten und Kopf-/Fußzeilen je Abschnitt, Kopf-/Fußzeile mit dem Vorgänger verknüpfen. Orientierung, Größe,
Ränder und Spalten gelten für den Abschnitt, in dem die Schreibmarke steht. Noch ausgegraut: „Gerade und ungerade Seiten unterschiedlich“.
"""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import alle, k as _k


def bauen(register: dict) -> dict:
    layout = alle(next(t for t in register["register"] if t["name"] == "Seitenlayout"))
    einfuegen = alle(next(t for t in register["register"] if t["name"] == "Einfügen"))
    umbrueche = layout["Umbrüche"]
    abschnitt_menue = [e for e in umbrueche["menue"] if e.get("tun", "").startswith("abschnittsumbruch")]
    gruppen = [
        {"name": "Navigation", "reihenfolge": True, "knoepfe": [
            _k("navigation", "Abschnittsnavigationsbereich", "abschnittNavigation", True)]},
        {"name": "Seite", "reihenfolge": True, "knoepfe": [
            dict(einfuegen["Deckblatt"], name="Deckblätter", gross=True), dict(layout["Ränder"], gross=True),
            dict(layout["Ausrichtung"], name="Orientierung", gross=True), dict(layout["Größe"], gross=True)]},
        {"name": "Abschnitte", "reihenfolge": True, "knoepfe": [
            _k("umbruch", "Abschnitt hinzufügen", gross=True, menue=abschnitt_menue),
            _k("kanteKeine", "Abschnitt löschen", "abschnittLoeschen", True),
            _k("zahnrad", "Abschnitt einrichten …", "abschnittEinstellungen", text=True),
            _k("zurueck", "Vorheriger Abschnitt", "abschnittVorher", text=True),
            _k("vor", "Nächster Abschnitt", "abschnittNaechster", text=True)]},
        {"name": "Kopf- und Fußzeile", "reihenfolge": True, "knoepfe": [
            _k("seitenzahl", "Seitenzahl", "seitenzahlKlappe", True, klappe="seitenzahlKlappe"),
            _k("kaestchen", "Erste Seite anders", "ersteSeiteAnders", text=True, haken=True),
            _k("kaestchen", "Gerade und ungerade Seiten sind unterschiedlich", "geradeUngerade", text=True, haken=True),
            _k("kopffuss", "Kopf- und Fußzeile", "kopfFussZeigen", True),
            _k("kette", "Link zu vorheriger Kopfzeile", "kopfVerknuepfen", text=True, haken=True),
            _k("kette", "Mit voriger Fußzeile verknüpfen", "fussVerknuepfen", text=True, haken=True)]},
        {"name": "Einstellungen", "reihenfolge": True, "knoepfe": [
            _k("zahnrad", "Einstellungen", gross=True, menue=[{"name": "Optionen …", "tun": "w.optionenOeffnen"}])]},
    ]
    return {"name": "Abschnitt", "gruppen": gruppen}
