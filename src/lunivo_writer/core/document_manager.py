"""Dokumentverwaltung ohne Oberfläche: Laden, Speichern, automatische Sicherung, Wiederherstellung, zuletzt benutzte Dateien.

Das Hauptfenster ruft diese Klasse auf und kümmert sich selbst nur um Dialoge (Kennwort, Fehlermeldungen, Hinweise).
"""
from __future__ import annotations

import os

from lunivo_writer.services import file_service as formats
from lunivo_writer.services import recovery
from lunivo_writer.services.settings_service import Settings


class DocumentManager:
    def __init__(self, settings: Settings):
        self.settings = settings

    # ---- Laden und Speichern -------------------------------------------------------------------------
    def laden(self, path: str, kennwort: str | None = None):
        """Liest eine Datei; Fehler (DocumentIOError, PasswortNoetig) gehen an den Aufrufer."""
        return formats.load(path, kennwort)

    def meta_fuer_speichern(self, meta: dict) -> dict:
        """Dokument-Metadaten plus Einstellungen: Codierung, Verfasser (Benutzername oder gelöscht)."""
        m = dict(meta)
        m["codierung"] = self.settings.get("speichern/codierung", "UTF-8")
        if self.settings.get_bool("sicherheit/personendaten_weg", False) or not self.settings.get_bool("benutzer/verwenden", True):
            m["author"] = ""
        elif self.settings.get("benutzer/name", ""):
            m["author"] = self.settings.get("benutzer/name", "")
        return m

    def speichern(self, path: str, dokument, seite, meta: dict):
        """Schreibt das Dokument; gibt den Bericht über nicht Übernommenes zurück."""
        return formats.save(path, dokument, seite, self.meta_fuer_speichern(meta))

    # ---- Zuletzt benutzt -------------------------------------------------------------------------------
    def zuletzt(self) -> list[str]:
        return self.settings.recent()

    def gelesen(self, path: str) -> None:
        self.settings.set("last_dir", os.path.dirname(path))
        self.settings.add_recent(path)

    def vergessen(self, path: str) -> None:
        self.settings.remove_recent(path)

    # ---- Sicherung und Wiederherstellung ---------------------------------------------------------------
    def sichern(self, tabs) -> None:
        """Automatische Sicherung aller geänderten Dokumente. Fehler stören die Arbeit nie."""
        if not self.settings.get_bool("sicherung/aktiv", True):
            return
        for t in tabs:
            if not t.is_modified():
                continue
            docx_path, _ = recovery.paths(t.token)
            try:
                formats.save(docx_path, t.editor.document(), t.page, t.meta)
                recovery.write_meta(t.token, t.path or "", t.title)
                if self.settings.get_bool("sicherung/staende", False):
                    recovery.zwischenstand(t.token, t.title, self.settings.get_int("sicherung/tage", 7))
            except Exception:
                pass

    def wiederherstellbar(self, offene_token: set):
        return recovery.pending(exclude=offene_token)

    def verwerfen(self, token) -> None:
        recovery.discard(token)
