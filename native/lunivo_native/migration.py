"""Übernahme der Texte aus dem alten WebKit-Speicher.

Der alte Speicher wird nur gelesen (Datei im Nur-Lese-Modus) und vorher
komplett gesichert. Jeder gefundene Text landet als eigene HTML-Datei in
~/.local/share/lunivo-office-gtk/dokumente/."""
import glob
import json
import os
import re
import shutil
import sqlite3
import time

from . import pfade


def _text(wert):
    if isinstance(wert, (bytes, bytearray)):
        try:
            return bytes(wert).decode("utf-16-le")
        except UnicodeDecodeError:
            return bytes(wert).decode("utf-8", "replace")
    return wert


def _sichtbar(html):
    roh = re.sub(r"<[^>]+>", "", html)
    return roh.strip()


def sichern():
    """Kopiert den alten Speicher und die alte Einstellungsdatei."""
    ziel = os.path.join(pfade.SICHERUNGEN, time.strftime("alter-speicher-%Y-%m-%d_%H%M%S"))
    os.makedirs(ziel, exist_ok=True)
    if os.path.isdir(pfade.ALTER_SPEICHER):
        shutil.copytree(pfade.ALTER_SPEICHER, os.path.join(ziel, "localstorage"))
    if os.path.exists(pfade.ALTE_EINSTELLUNGEN):
        shutil.copy2(pfade.ALTE_EINSTELLUNGEN, ziel)
    return ziel


def alte_dokumente():
    """Liefert [(name, html)] aller nicht leeren Texte im alten Speicher."""
    gefunden, gesehen = [], set()
    for datei in glob.glob(os.path.join(pfade.ALTER_SPEICHER, "*.localstorage")):
        try:
            verb = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
            zeilen = verb.execute(
                "select key, value from ItemTable where key like 'sp.%inhalt' "
                "or key like 'sp.%dateiname'").fetchall()
            verb.close()
        except sqlite3.Error:
            continue
        werte = {k: _text(v) for k, v in zeilen}
        for k, v in werte.items():
            if not k.endswith(".inhalt") and k != "sp.inhalt":
                continue
            if ".kopf" in k or ".fuss" in k or k.startswith("sp.kopf") or k.startswith("sp.fuss"):
                continue
            try:
                html = json.loads(v)
            except ValueError:
                continue
            if not isinstance(html, str) or not _sichtbar(html):
                continue
            if html in gesehen:
                continue
            gesehen.add(html)
            name_schluessel = k[: -len("inhalt")] + "dateiname"
            try:
                name = json.loads(werte.get(name_schluessel, '"Unbenannt"'))
            except ValueError:
                name = "Unbenannt"
            gefunden.append((name or "Unbenannt", html))
    return gefunden


def uebernehmen():
    """Sichert, legt die Texte als Dateien an, gibt deren Pfade zurück."""
    pfade.anlegen()
    dokumente = alte_dokumente()
    if not dokumente:
        return [], None
    sicherung = sichern()
    pfadliste = []
    for i, (name, html) in enumerate(dokumente, 1):
        sauber = re.sub(r"[^\w .-]", "_", name).strip() or "Unbenannt"
        pfad = os.path.join(pfade.DOKUMENTE, "%s (übernommen %d).html" % (sauber, i))
        with open(pfad, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"></head><body>\n%s\n</body></html>\n" % html)
        pfadliste.append(pfad)
    return pfadliste, sicherung
