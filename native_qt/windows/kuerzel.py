"""Tastenkürzel — eine Tabelle für die Hilfe und für die Kürzel, die nicht an einer Aktion des Fensters hängen."""
from __future__ import annotations

# (Gruppe, [(Taste, Beschreibung)])
HILFE = [
    ("Dokumente", [("Strg+N", "Neues Dokument"), ("Strg+W", "Schließen"), ("Strg+Tab", "Nächstes Dokument"),
                   ("Strg+Umschalt+Tab", "Voriges Dokument"), ("Strg+O", "Öffnen"), ("Strg+S", "Speichern"),
                   ("Strg+Umschalt+S", "Speichern unter"), ("Strg+P", "Drucken"), ("Strg+Q", "Beenden")]),
    ("Schreiben", [("Strg+Z", "Rückgängig"), ("Strg+Y", "Wiederholen"), ("Strg+B", "Fett"), ("Strg+I", "Kursiv"),
                   ("Strg+U", "Unterstrichen"), ("Strg+K", "Hyperlink"), ("Strg+F", "Suchen"), ("Strg+H", "Ersetzen"),
                   ("Strg+A", "Alles auswählen"), ("Strg+Enter", "Seitenumbruch"), ("Strg+L / E / R / J", "Links / Zentriert / Rechts / Blocksatz"),
                   ("Strg++ / Strg+− / Strg+0", "Ansicht größer / kleiner / 100 %"), ("Strg+1 … 6", "Wortvorschlag nehmen"),
                   ("F3", "Textbaustein einfügen"), ("Tab", "Zur nächsten Lücke «…» (sonst Einzug)"), ("Strg+Klick", "Hyperlink öffnen")]),
    ("Ansicht", [("F11", "Vollbild"), ("Strg+Umschalt+8", "Formatierungszeichen"), ("Strg+Umschalt+N", "Navigationsbereich"),
                 ("Strg+Umschalt+L", "Lesemodus"), ("Strg+Mausrad", "Zoom"), ("Alt+Umschalt+←/→", "Gliederung: Ebene ändern")]),
    ("Hilfe und Prüfung", [("F4", "Vorlesen"), ("F5", "Seitenleiste ein/aus"), ("F6", "Welche Hilfe wann"), ("F7", "Prüfen"),
                           ("F8", "KI-Korrektur"), ("F9", "Optionen")]),
]


def als_html() -> str:
    h = ""
    for gruppe, zeilen in HILFE:
        h += f"<h3>{gruppe}</h3><table cellpadding='3'>"
        for taste, text in zeilen:
            h += f"<tr><td><code>{taste}</code></td><td>{text}</td></tr>"
        h += "</table>"
    return h
