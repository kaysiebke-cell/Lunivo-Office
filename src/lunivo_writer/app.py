#!/usr/bin/env python3
"""Einstieg: python -m lunivo_writer.app [Datei …]"""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 fehlt. Installieren mit:  ./starten-qt.sh   (legt eine eigene Umgebung an)\n"
              "oder:  pip install -r requirements.txt", file=sys.stderr)
        return 2
    from lunivo_writer.services.settings_service import APP_NAME, APP_ORG, Settings
    from lunivo_writer.ui.theme import apply_theme
    from lunivo_writer.ui.main_window import MainWindow

    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setDesktopFileName("lunivo-writer")
    settings = Settings()
    apply_theme(app, settings.get("theme", "system"))
    win = MainWindow(settings)
    win.show()
    files = [a for a in argv[1:] if not a.startswith("-")]
    for f in files:
        win.open_path(f)
    if not files:
        win.offer_recovery()
    rc = app.exec()
    # Fenster vor dem Interpreter-Ende abbauen: PySide räumt sonst in falscher Reihenfolge ab (Heap-Fehler beim Beenden)
    from PySide6.QtCore import QEvent
    win.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    del win
    return rc


if __name__ == "__main__":
    sys.exit(main())
