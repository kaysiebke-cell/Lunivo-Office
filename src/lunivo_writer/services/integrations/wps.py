"""WPS Office — nur die ehrliche Stufe: ein installiertes Programm aufrufen.

Geprüft (Stand der Recherche, siehe docs/BERICHT.md): Für WPS Writer unter Linux habe ich keine offiziell
dokumentierte, englischsprachige Automatisierungsschnittstelle gefunden. Es gibt (a) JSAPI-Erweiterungen laut
Entwicklerdokumentation auf open.wps.cn (chinesisch) und (b) das Drittprojekt „pywpsrpc“ (Python-Anbindung an eine
RPC-Schnittstelle von WPS, nur Linux). Beides wurde hier NICHT eingebaut: WPS ist auf dem Testrechner nicht
installiert, und eine Abhängigkeit von nicht offiziell zugesicherten Interna wäre fragil.

Was dieses Modul tut: erkennen, ob ein `wps`-Programm im Suchpfad liegt, und eine Datei darin öffnen
(`wps <datei>`). Das ist Steuerung einer installierten Anwendung — keine Integration.
"""
from __future__ import annotations

import shutil
import subprocess

KANDIDATEN = ("wps", "wpsoffice")


def finde_wps() -> str | None:
    for n in KANDIDATEN:
        p = shutil.which(n)
        if p:
            return p
    return None


def verfuegbar() -> bool:
    return finde_wps() is not None


def oeffnen(pfad: str) -> bool:
    """Öffnet die Datei in WPS Writer (eigener Prozess). False, wenn WPS nicht installiert ist."""
    p = finde_wps()
    if not p:
        return False
    subprocess.Popen([p, pfad], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return True


def mit_libreoffice_oeffnen(pfad: str) -> bool:
    from lunivo_writer.services.integrations import libreoffice
    s = libreoffice.finde_soffice()
    if not s:
        return False
    subprocess.Popen([s, "--writer", pfad], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return True
