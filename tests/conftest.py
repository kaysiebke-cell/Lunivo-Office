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
    return a
