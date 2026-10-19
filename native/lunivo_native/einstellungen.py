"""Einstellungen als kleine JSON-Datei. Die alte einstellungen.conf wird nur
gelesen (Anbieter/Modell der KI, Name) und nie verändert."""
import json
import os

from . import pfade

VORGABE = {
    "zoom": 85,
    "schriftart": "Georgia",
    "groesse": 12,
    "schreibhilfe": True,
    "fenster": [1200, 800],
    "ki_modell": "",
    "ki_adresse": "http://localhost:11434",
    "offen": [],
    "migriert": False,
}


def lesen():
    werte = dict(VORGABE)
    try:
        with open(pfade.EINSTELLUNGEN, encoding="utf-8") as f:
            werte.update(json.load(f))
    except (OSError, ValueError):
        pass
    if not werte["ki_modell"]:
        modell, adresse = _ki_aus_alter_datei()
        if modell:
            werte["ki_modell"] = modell
            werte["ki_adresse"] = adresse or werte["ki_adresse"]
    return werte


def schreiben(werte):
    pfade.anlegen()
    tmp = pfade.EINSTELLUNGEN + ".neu"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(werte, f, ensure_ascii=False, indent=2)
    os.replace(tmp, pfade.EINSTELLUNGEN)


def _ki_aus_alter_datei():
    try:
        with open(pfade.ALTE_EINSTELLUNGEN, encoding="utf-8") as f:
            for zeile in f:
                if zeile.startswith("sp.anbieter="):
                    liste = json.loads(zeile.split("=", 1)[1])
                    if liste:
                        url = liste[0].get("url", "")
                        return liste[0].get("modell", ""), url.replace("/v1", "")
    except (OSError, ValueError):
        pass
    return "", ""
