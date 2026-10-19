"""Wo das Programm seine Dateien ablegt."""
import os

CONF = os.path.expanduser("~/.config/lunivo-office")
DATEN = os.path.expanduser("~/.local/share/lunivo-office-gtk")
DOKUMENTE = os.path.join(DATEN, "dokumente")      # aus dem alten Programm übernommene Texte
SICHERUNGEN = os.path.join(DATEN, "sicherungen")
EINSTELLUNGEN = os.path.join(CONF, "gtk-einstellungen.json")
ALTE_EINSTELLUNGEN = os.path.join(CONF, "einstellungen.conf")
ALTER_SPEICHER = os.path.expanduser("~/.local/share/schreibprogramm/localstorage")
PROJEKT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRUEFER = os.path.join(PROJEKT, "native", "pruefer.js")


def anlegen():
    for p in (CONF, DATEN, DOKUMENTE, SICHERUNGEN):
        os.makedirs(p, exist_ok=True)
