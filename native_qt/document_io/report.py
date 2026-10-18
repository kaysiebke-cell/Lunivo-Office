"""Bericht über das, was beim Öffnen/Speichern nicht verlustfrei ging."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IOReport:
    warnings: list[str] = field(default_factory=list)

    def warn(self, text: str) -> None:
        if text not in self.warnings:
            self.warnings.append(text)

    def __bool__(self) -> bool:
        return bool(self.warnings)


class DocumentIOError(Exception):
    """Datei nicht lesbar oder nicht schreibbar — Text ist für Anwender gedacht."""
