"""Automatische Wiederherstellung.

Je offenem, geändertem Dokument liegt in <Datenordner>/recovery eine DOCX-Kopie
und eine kleine JSON-Datei (Originalpfad, Titel, Zeitpunkt). Beim sauberen
Schließen eines Dokuments wird beides gelöscht — nur das, was das Programm
selbst angelegt hat. Bleibt etwas liegen, war das Programm abgestürzt.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass

from .settings import data_dir


def recovery_dir() -> str:
    d = os.path.join(data_dir(), "recovery")
    os.makedirs(d, exist_ok=True)
    return d


@dataclass
class RecoveryEntry:
    token: str
    original: str
    title: str
    saved_at: float
    docx_path: str

    @property
    def meta_path(self) -> str:
        return os.path.join(recovery_dir(), self.token + ".json")


def new_token() -> str:
    return uuid.uuid4().hex


def paths(token: str) -> tuple[str, str]:
    d = recovery_dir()
    return os.path.join(d, token + ".docx"), os.path.join(d, token + ".json")


def write_meta(token: str, original: str, title: str) -> None:
    _, meta = paths(token)
    tmp = meta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"original": original, "title": title, "saved_at": time.time()}, fh)
    os.replace(tmp, meta)


def discard(token: str) -> None:
    for p in paths(token):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass
        except OSError:
            pass


def pending(exclude: set[str] | None = None) -> list[RecoveryEntry]:
    out = []
    d = recovery_dir()
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        token = name[:-5]
        if exclude and token in exclude:
            continue
        docx_path = os.path.join(d, token + ".docx")
        if not os.path.exists(docx_path):
            continue
        try:
            with open(os.path.join(d, name), encoding="utf-8") as fh:
                m = json.load(fh)
            out.append(RecoveryEntry(token, m.get("original", ""), m.get("title", "Dokument"),
                                     float(m.get("saved_at", 0)), docx_path))
        except (OSError, ValueError):
            continue
    return out
