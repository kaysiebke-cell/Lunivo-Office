"""Textbausteine: markierter Text mit Formatierung unter einem Namen merken und später einfügen."""
from __future__ import annotations

import json
import os

from PySide6.QtGui import QTextDocumentFragment

from .settings import data_dir


def _pfad() -> str:
    return os.path.join(data_dir(), "bausteine.json")


def laden() -> list[dict]:
    try:
        with open(_pfad(), encoding="utf-8") as fh:
            d = json.load(fh)
        return [b for b in d if isinstance(b, dict) and b.get("name") and b.get("html")]
    except (OSError, ValueError):
        return []


def speichern(liste: list[dict]) -> None:
    try:
        tmp = _pfad() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(liste, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, _pfad())
    except OSError:
        pass


def hinzufuegen(name: str, fragment: QTextDocumentFragment) -> None:
    liste = [b for b in laden() if b["name"] != name]
    liste.append({"name": name, "html": fragment.toHtml(), "text": fragment.toPlainText()})
    speichern(liste)


def entfernen(name: str) -> None:
    speichern([b for b in laden() if b["name"] != name])


def einfuegen(cursor, baustein: dict) -> None:
    cursor.insertFragment(QTextDocumentFragment.fromHtml(baustein["html"]))
