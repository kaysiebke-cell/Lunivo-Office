"""Symbole für Dateiformate aus dem Icon-Theme des Systems (Freedesktop): Dateiname → MIME-Typ → Icon-Name."""
from __future__ import annotations

import os

from PySide6.QtCore import QMimeDatabase
from PySide6.QtGui import QIcon

RUECKFALL = ("x-office-document", "text-x-generic", "application-octet-stream")


def icon_namen(name: str) -> list[str]:
    """Die Namen, in der Reihenfolge, in der sie im Theme gesucht werden: der des MIME-Typs, sein allgemeiner, dann Rückfälle.
    ``name`` ist ein Dateiname („brief.docx“, ein Pfad) oder nur die Endung („.docx“)."""
    if name.startswith(".") and name.count(".") == 1:
        name = "datei" + name
    mt = QMimeDatabase().mimeTypeForFile(os.path.basename(name), QMimeDatabase.MatchMode.MatchExtension)
    return [n for n in (mt.iconName(), mt.genericIconName(), *RUECKFALL) if n]


def datei_symbol(name: str) -> QIcon:
    """Das Symbol des Dateiformats im aktuellen Icon-Theme (Mint-Y, Papirus …); leer, wenn das Theme keines kennt."""
    for n in icon_namen(name):
        ic = QIcon.fromTheme(n)
        if not ic.isNull():
            return ic
    return QIcon()
