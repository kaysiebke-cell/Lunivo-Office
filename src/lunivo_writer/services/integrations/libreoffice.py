"""LibreOffice als Umwandler (Adapter) — nur über die dokumentierte Kommandozeile.

    soffice --headless --convert-to <format> --outdir <ordner> <datei>

Das ist KEINE Einbettung und kein Zugriff auf Interna: LibreOffice wird als eigenes Programm gerufen, wenn
es installiert ist. Fehlt es, bleibt alles andere nutzbar (DOCX, TXT, ODT-Export über Qt).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from lunivo_writer.models.report import DocumentIOError
from lunivo_writer.services.settings_service import data_dir

TIMEOUT_S = 180
# Endung → Filtername für --convert-to
FILTER = {"docx": "docx:MS Word 2007 XML", "odt": "odt:writer8", "doc": "doc:MS Word 97",
          "rtf": "rtf:Rich Text Format", "txt": "txt:Text (encoded):UTF8"}


def finde_soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def verfuegbar() -> bool:
    return finde_soffice() is not None


def konvertiere(quelle: str, ziel_ext: str, ordner: str) -> str:
    """Wandelt `quelle` nach `ziel_ext` um (Ergebnis liegt in `ordner`). → Pfad der neuen Datei."""
    soffice = finde_soffice()
    if not soffice:
        raise DocumentIOError("Das Umwandlungsprogramm ist nicht installiert. Dieses Format braucht es "
                              "(Installation: sudo apt install libreoffice-writer).")
    profil = os.path.join(data_dir(), "lo-profil")
    os.makedirs(profil, exist_ok=True)
    try:
        lauf = subprocess.run(
            [soffice, "-env:UserInstallation=file://" + profil, "--headless", "--norestore",
             "--convert-to", FILTER.get(ziel_ext, ziel_ext), "--outdir", ordner, quelle],
            capture_output=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired as e:
        raise DocumentIOError("Das Umwandlungsprogramm hat zu lange gebraucht und wurde abgebrochen.") from e
    except OSError as e:
        raise DocumentIOError(f"Das Umwandlungsprogramm ließ sich nicht starten: {e.strerror or e}") from e
    ziel = os.path.join(ordner, os.path.splitext(os.path.basename(quelle))[0] + "." + ziel_ext)
    if not os.path.isfile(ziel):
        hinweis = (lauf.stderr or lauf.stdout or "").strip().splitlines()
        raise DocumentIOError("Die Umwandlung ergab nichts"
                              + (f": {hinweis[-1]}" if hinweis else "."))
    return ziel


def in_docx(pfad: str) -> tuple[str, tempfile.TemporaryDirectory]:
    """Datei → temporäre DOCX. Der Aufrufer behält das Verzeichnisobjekt, bis er fertig gelesen hat."""
    tmp = tempfile.TemporaryDirectory(prefix="lunivo-")
    return konvertiere(pfad, "docx", tmp.name), tmp


def aus_docx(docx_pfad: str, ziel_pfad: str) -> None:
    """DOCX → ODT/DOC/RTF nach `ziel_pfad` (atomar kopiert)."""
    ext = os.path.splitext(ziel_pfad)[1].lstrip(".").lower()
    with tempfile.TemporaryDirectory(prefix="lunivo-") as tmp:
        fertig = konvertiere(docx_pfad, ext, tmp)
        folder = os.path.dirname(os.path.abspath(ziel_pfad))
        try:
            fd, t = tempfile.mkstemp(dir=folder, suffix=".tmp")
            os.close(fd)
            shutil.copyfile(fertig, t)
            os.replace(t, ziel_pfad)
        except OSError as e:
            raise DocumentIOError(f"Speichern nicht möglich: {e.strerror or e}") from e
