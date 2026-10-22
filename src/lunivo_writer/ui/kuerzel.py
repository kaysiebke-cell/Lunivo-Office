"""Tastenkürzel — eine Tabelle für die Hilfe und für die Kürzel, die nicht an einer Aktion des Fensters hängen."""
from __future__ import annotations

# (Gruppe, [(Taste, Beschreibung)])
HILFE = [
    ("Dokumente", [("Strg+N", "Neues Dokument"), ("Strg+W", "Schließen"), ("Strg+Tab", "Nächstes Dokument"),
                   ("Strg+Umschalt+Tab", "Voriges Dokument"), ("Strg+O", "Öffnen"), ("Strg+S", "Speichern"),
                   ("Strg+Umschalt+S", "Speichern unter"), ("Strg+P", "Drucken"), ("Strg+Q", "Beenden")]),
    ("Schreiben", [("Strg+Z", "Rückgängig"), ("Strg+Y", "Wiederholen"), ("Strg+B", "Fett"), ("Strg+I", "Kursiv"),
                   ("Strg+U", "Unterstrichen"), ("Strg+K", "Hyperlink"), ("Strg+D", "Fenster Schriftart"), ("Strg+Alt+V", "Inhalte einfügen"), ("Strg+Alt+F", "Fußnote einfügen"), ("Strg+Alt+D", "Endnote einfügen"), ("Strg+F", "Suchen"), ("Strg+H", "Ersetzen"),
                   ("Strg+A", "Alles auswählen"), ("Strg+Enter", "Seitenumbruch"), ("Strg+L / E / R / J", "Links / Zentriert / Rechts / Blocksatz"),
                   ("Strg++ / Strg+− / Strg+0", "Ansicht größer / kleiner / 100 %"), ("Strg+1 … 6", "Wortvorschlag nehmen"),
                   ("F3", "Textbaustein einfügen"), ("Tab", "Zur nächsten Lücke «…» (sonst Einzug)"), ("Strg+Klick", "Hyperlink öffnen")]),
    ("Ansicht", [("F11", "Vollbild"), ("Strg+Umschalt+8", "Formatierungszeichen"), ("Strg+Umschalt+N", "Navigationsbereich"),
                 ("Strg+Umschalt+L", "Lesemodus"), ("Strg+Mausrad", "Zoom"), ("Alt+Umschalt+←/→", "Gliederung: Ebene ändern")]),
    ("Hilfe und Prüfung", [("F4", "Vorlesen"), ("F5", "Seitenleiste ein/aus"), ("F6", "Welche Hilfe wann"), ("F7", "Prüfen"),
                           ("F8", "KI-Korrektur"), ("F9", "Optionen")]),
]


def als_markdown() -> str:
    """Die Tabelle als Markdown — das zeigt der Hilfe-Dialog über ``QTextBrowser.setMarkdown``."""
    t = ""
    for gruppe, zeilen in HILFE:
        t += f"### {gruppe}\n\n| Taste | Wirkung |\n|---|---|\n"
        for taste, text in zeilen:
            t += f"| `{taste}` | {text} |\n"
        t += "\n"
    return t
