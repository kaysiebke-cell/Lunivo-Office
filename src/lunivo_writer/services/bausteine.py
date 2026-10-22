"""Textbausteine: markierter Text mit Formatierung unter einem Namen merken und später einfügen."""
from __future__ import annotations

import json
import os

from PySide6.QtGui import QTextDocumentFragment

from lunivo_writer.editor.textdaten import daten_zu_fragment, fragment_zu_daten
from lunivo_writer.services.settings_service import data_dir


def _pfad() -> str:
    return os.path.join(data_dir(), "bausteine.json")


def laden() -> list[dict]:
    try:
        with open(_pfad(), encoding="utf-8") as fh:
            d = json.load(fh)
        return [b for b in d if isinstance(b, dict) and b.get("name") and (b.get("absaetze") or b.get("text"))]
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


def standard() -> list[dict]:
    """Die mitgelieferten Bausteine (Briefe, Bewerbungen …); sie lassen sich einfügen, aber nicht ändern."""
    try:
        from lunivo_writer.core import paths
        with open(os.path.join(paths.RESSOURCEN, "bausteine_standard.json"), encoding="utf-8") as fh:
            return [dict(b, standard=True) for b in json.load(fh)]
    except (OSError, ValueError, ImportError):
        return []


def alle() -> list[dict]:
    """Mitgelieferte und eigene Bausteine (Eigene zuletzt)."""
    return standard() + laden()


def finde_kuerzel(kuerzel: str) -> dict | None:
    """Der Baustein zu einem Kürzel (Eigene gehen vor den mitgelieferten)."""
    k = (kuerzel or "").strip()
    return next((b for b in reversed(alle()) if k and b.get("kuerzel") == k), None) if k else None


def hinzufuegen(name: str, fragment: QTextDocumentFragment, kuerzel: str = "") -> None:
    liste = [b for b in laden() if b["name"] != name]
    liste.append({"name": name, "kuerzel": (kuerzel or "").strip(), "absaetze": fragment_zu_daten(fragment), "text": fragment.toPlainText()})
    speichern(liste)


def entfernen(name: str) -> None:
    speichern([b for b in laden() if b["name"] != name])


def einfuegen(cursor, baustein: dict) -> None:
    """Fügt den Baustein mit seiner Formatierung ein; ein alter Eintrag ohne Absatzdaten kommt als einfacher Text."""
    if baustein.get("absaetze"):
        cursor.insertFragment(daten_zu_fragment(baustein["absaetze"]))
    else:
        cursor.insertText(baustein.get("text", ""))
