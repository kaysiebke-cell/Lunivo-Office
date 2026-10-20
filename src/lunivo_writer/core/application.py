"""Anwendungsstart: QApplication einrichten, Einstellungen und Theme laden, Hauptfenster zeigen, sauber beenden."""
from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

from lunivo_writer.services.settings_service import APP_NAME, APP_ORG, Settings
from lunivo_writer.ui.main_window import MainWindow
from lunivo_writer.ui.theme import apply_theme


class LunivoApplication:
    def __init__(self, argv: list[str]):
        self.argv = argv
        self.app = QApplication(argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setOrganizationName(APP_ORG)
        self.app.setDesktopFileName("lunivo-writer")
        self.settings = Settings()
        from lunivo_writer.ui import theme
        theme.WEICH = self.settings.get_bool("ui/weich", False)
        apply_theme(self.app, self.settings.get("theme", "system"))
        self.fenster = MainWindow(self.settings)

    def start(self) -> int:
        win = self.fenster
        win.show()
        dateien = [a for a in self.argv[1:] if not a.startswith("-")]
        for f in dateien:
            win.open_path(f)
        if not dateien:
            win.offer_recovery()
        if not dateien and win.tabs.count() == 0 and self.settings.get_bool("start/letztes_oeffnen", False):
            import os
            letztes = next((p for p in self.settings.recent() if os.path.exists(p)), None)     # zuletzt geschriebenes Dokument
            if letztes:
                win.open_path(letztes)
        if win.tabs.count() == 0:                    # keine Startseite: das Programm beginnt mit einem leeren Blatt
            win.new_document()
        rc = self.app.exec()
        self._abbauen()
        return rc

    def _abbauen(self) -> None:
        """Fenster vor dem Interpreter-Ende abbauen: PySide räumt sonst in falscher Reihenfolge ab (Heap-Fehler beim Beenden)."""
        self.fenster.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.fenster = None
