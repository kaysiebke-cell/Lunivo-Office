"""Einstellungen und Pfade (XDG, über QStandardPaths). Nichts liegt im Programmordner."""
from __future__ import annotations

import os

from PySide6.QtCore import QSettings, QStandardPaths

APP_ORG = "Lunivo"
APP_NAME = "Lunivo Writer"
MAX_RECENT = 12


def data_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    os.makedirs(base, exist_ok=True)
    return base


class Settings:
    """Dünne Hülle um QSettings mit festen Schlüsseln und Vorgaben."""

    def __init__(self, qsettings: QSettings | None = None):
        self.q = qsettings or QSettings(APP_ORG, APP_NAME)

    # Werte
    def get(self, key: str, default=None):
        return self.q.value(key, default)

    def set(self, key: str, value) -> None:
        self.q.setValue(key, value)
        self.q.sync()

    def get_bool(self, key: str, default: bool) -> bool:
        v = self.q.value(key, default)
        return v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes")

    def get_int(self, key: str, default: int) -> int:
        try:
            return int(self.q.value(key, default))
        except (TypeError, ValueError):
            return default

    # Zuletzt verwendete Dokumente
    def recent(self) -> list[str]:
        v = self.q.value("recent", [])
        if isinstance(v, str):
            v = [v]
        return [p for p in (v or []) if isinstance(p, str)]

    def add_recent(self, path: str) -> None:
        path = os.path.abspath(path)
        items = [p for p in self.recent() if p != path]
        items.insert(0, path)
        self.set("recent", items[:MAX_RECENT])

    def remove_recent(self, path: str) -> None:
        self.set("recent", [p for p in self.recent() if p != path])

    def clear_recent(self) -> None:
        self.set("recent", [])
