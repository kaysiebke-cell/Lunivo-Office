#!/usr/bin/env python3
"""Einstieg: python -m native_qt.main [Datei …]"""
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
    from .storage.settings import APP_NAME, APP_ORG, Settings
    from .theme import apply_theme
    from .windows.main_window import MainWindow

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
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
