"""Vorführung: „Neue Formatvorlage“ mit allen Unterfenstern in EINEM Fenster (Fenster-Stapel), ohne die Anwendung.

    .venv/bin/python werkzeug/stapel-demo.py

Format ▾ öffnet Schriftart, Absatz, Tabstopps, Rahmen, Nummerierung, Texteffekte und Verknüpfung als Seite im selben Fenster; darin wieder
Tabstopps (aus Absatz), Texteffekte (aus Schriftart), Anpassen (aus Nummerierung) und die Optionen (aus Rahmen). „OK“ kehrt zur vorigen Seite
zurück, „← Zurück“ bricht die Seite ab. Der Code liegt in ``ui/baukasten/fenster_stapel.py``; ohne diese Datei öffnen sich die Fenster wie bisher einzeln.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PySide6.QtWidgets import QApplication

from lunivo_writer.ui.theme import apply_theme
from lunivo_writer.ui.baukasten.fenster_stapel import FensterStapel
from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog


def main() -> None:
    app = QApplication(sys.argv)
    apply_theme(app, "dark")
    fv = FormatvorlageDialog(None, start={"groesse": 12, "fett": True, "vor": 6, "nach": 6}, vorlagen=["Standard", "Überschrift 1", "Überschrift 2"])
    host = FensterStapel(fv)
    ok = host.exec()
    print("OK" if ok else "Abgebrochen", fv.ergebnis() if ok else "")


if __name__ == "__main__":
    main()
