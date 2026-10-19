"""Dateiformate über LibreOffice (soffice, ohne Fenster)."""
import os
import shutil
import subprocess
import tempfile


def soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def umwandeln(quelle, ziel_endung, ziel_ordner=None, filter_=None):
    """Wandelt `quelle` in das Format `ziel_endung` um; gibt den Pfad zurück."""
    prog = soffice()
    if not prog:
        raise RuntimeError("LibreOffice (soffice) ist nicht installiert.")
    ordner = ziel_ordner or tempfile.mkdtemp(prefix="lunivo-")
    profil = tempfile.mkdtemp(prefix="lunivo-profil-")
    ziel = ziel_endung if not filter_ else "%s:%s" % (ziel_endung, filter_)
    try:
        subprocess.run(
            [prog, "-env:UserInstallation=file://" + profil, "--headless",
             "--convert-to", ziel, "--outdir", ordner, quelle],
            check=True, capture_output=True, timeout=180)
    finally:
        shutil.rmtree(profil, ignore_errors=True)
    basis = os.path.splitext(os.path.basename(quelle))[0]
    ergebnis = os.path.join(ordner, basis + "." + ziel_endung)
    if not os.path.exists(ergebnis):
        raise RuntimeError("Die Umwandlung hat keine Datei erzeugt.")
    return ergebnis


def html_aus_datei(pfad):
    """docx/odt/doc/rtf -> HTML-Text"""
    ordner = tempfile.mkdtemp(prefix="lunivo-")
    try:
        ergebnis = umwandeln(pfad, "html", ordner, "XHTML:XHTML Writer File:UTF8")
    except Exception:
        ergebnis = umwandeln(pfad, "html", ordner)
    try:
        with open(ergebnis, encoding="utf-8", errors="replace") as f:
            return f.read()
    finally:
        shutil.rmtree(ordner, ignore_errors=True)


def html_in_datei(html_text, ziel, endung):
    """HTML-Text -> docx/odt/pdf an `ziel`."""
    ordner = tempfile.mkdtemp(prefix="lunivo-")
    try:
        quelle = os.path.join(ordner, "dokument.html")
        with open(quelle, "w", encoding="utf-8") as f:
            f.write(html_text)
        filter_ = {"docx": "MS Word 2007 XML", "odt": "writer8",
                   "pdf": "writer_web_pdf_Export", "rtf": "Rich Text Format", "png": "writer_png_Export"}.get(endung)
        ergebnis = umwandeln(quelle, endung, ordner, filter_)
        shutil.move(ergebnis, ziel)
    finally:
        shutil.rmtree(ordner, ignore_errors=True)
