import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app():
    # Testmodus: Daten- und Einstellungsordner liegen getrennt von den echten des Benutzers
    QStandardPaths.setTestModeEnabled(True)
    a = QApplication.instance() or QApplication([])
    a.setApplicationName("lunivo-writer-test")
    a.setOrganizationName("lunivo-test")
    yield a
    # Aufräumen vor dem Beenden: sonst räumt PySide beim Interpreter-Ende Widgets in falscher Reihenfolge ab
    # und glibc meldet gelegentlich „malloc_consolidate(): unaligned fastbin chunk“.
    from PySide6.QtCore import QEvent
    for w in a.topLevelWidgets():
        w.deleteLater()
    a.sendPostedEvents(None, QEvent.DeferredDelete)
    a.processEvents()
