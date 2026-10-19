"""Das ☰-Menü (und die Menüleiste): Datei + je Reiter eine Untergruppe, gebaut
aus denselben Befehlen wie das Band."""
import json

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib  # noqa: E402

from . import befehle, ribbon_daten
from .ribbon_daten import K

STRICH = "-"

# (Beschriftung, Befehl, Argument, Tastenkürzel) oder (Beschriftung, [Untermenü]) oder STRICH
DATEI = [
    ("Neu", "neu", None, "<Primary>n"),
    ("Öffnen", "oeffnen", None, "<Primary>o"),
    ("Zuletzt geöffnet", "zuletzt_oeffnen", None, None),
    ("Neu aus Vorlage", "vorlagen_waehlen", None, None),
    ("Vorlagenordner", "vorlagen_ordner", None, None),
    STRICH,
    ("Speichern", "speichern", None, "<Primary>s"),
    ("Speichern unter", "speichern_unter", None, "<Primary><Shift>s"),
    STRICH,
    ("Drucken", "drucken", None, "<Primary>p"),
    ("Druckvorschau", "vorschau", None, None),
    ("Als PDF exportieren", "speichern_pdf", None, None),
    ("Exportieren als Word (docx)", "exportieren", "docx", None),
    ("Exportieren als OpenDocument (odt)", "exportieren", "odt", None),
    ("Exportieren als Text", "exportieren", "txt", None),
    ("Druckereinstellungen", "drucker_einrichten", None, None),
    STRICH,
    ("Dokumenteigenschaften", "eigenschaften", None, None),
    ("Umbenennen", "umbenennen", None, None),
    STRICH,
    ("Schließen", "schliessen", None, "<Primary>w"),
    STRICH,
    ("Hilfe", [
        ("Handbuch", "handbuch", None, "F1"),
        ("Tastenkürzel", "tasten_hilfe", None, None),
        ("Erweiterungen", "erweiterungen", None, None),
        ("Über Lunivo Office", "ueber", None, None),
    ]),
    ("Optionen", "optionen", None, "F9"),
    ("Beenden", "beenden", None, "<Primary>q"),
]

# Kürzel, die nicht an ein Menü gebunden sind
ZUSATZ = [
    ("rueckgaengig", None, "<Primary>z"), ("wiederholen", None, "<Primary>y"),
    ("alles_markieren", None, "<Primary>a"), ("suchen", None, "<Primary>f"),
    ("ersetzen", None, "<Primary>h"),
    ("fett", None, "<Primary>b"), ("kursiv", None, "<Primary>i"), ("unter", None, "<Primary>u"),
    ("links", None, "<Primary>l"), ("mitte", None, "<Primary>e"), ("rechts", None, "<Primary>r"),
    ("block", None, "<Primary>j"), ("seitenumbruch", None, "<Primary>Return"),
    ("pruefen", None, "F7"), ("tafel_zeigen", None, "F8"), ("textbaustein", None, "F3"),
    ("groesser", None, "<Primary>plus"), ("kleiner", None, "<Primary>minus"),
    ("hyperlink", None, "<Primary>k"),
]

TASTEN = {}


def kennung(name, arg=None):
    return name if arg is None else "%s|%s" % (name, json.dumps(arg))


def _eintrag(menue, text, name, arg=None, taste=None):
    if not befehle.gibt_es(name):
        return False
    k = kennung(name, arg)
    item = Gio.MenuItem.new(text, None)
    item.set_action_and_target_value("win.befehl", GLib.Variant.new_string(k))
    menue.append_item(item)
    if taste:
        TASTEN.setdefault(k, []).append(taste)
    return True


def _datei(eintraege):
    m = Gio.Menu()
    abschnitt = Gio.Menu()
    for e in eintraege:
        if e == STRICH:
            if abschnitt.get_n_items():
                m.append_section(None, abschnitt)
                abschnitt = Gio.Menu()
            continue
        if isinstance(e[1], list):
            unter = _datei(e[1])
            if unter.get_n_items():
                abschnitt.append_submenu(e[0], unter)
            continue
        text, name, arg, taste = e
        _eintrag(abschnitt, text, name, arg, taste)
    if abschnitt.get_n_items():
        m.append_section(None, abschnitt)
    return m


_gesehen = {}


def _zaehler_name(name):
    """GTK legt Untermenüs unter ihrem Namen ab – gleiche Namen brauchen einen unsichtbaren Zusatz."""
    _gesehen[name] = _gesehen.get(name, -1) + 1
    return _gesehen[name]


def _reiter_menue(gruppen):
    m = Gio.Menu()
    for name, inhalt, _ in gruppen:
        if not isinstance(inhalt, list):
            continue
        g = Gio.Menu()
        for k in inhalt:
            if not isinstance(k, K):
                continue
            if k.menue:
                for e in k.menue:
                    if e != "-":
                        _eintrag(g, e[0], e[1], e[2] if len(e) > 2 else None)
            elif k.aktion:
                a, arg = (k.aktion if isinstance(k.aktion, tuple) else (k.aktion, None))
                _eintrag(g, k.name, a, arg)
        if g.get_n_items():
            m.append_submenu(name + "\u200b" * (_zaehler_name(name)), g)
    return m


def haupt_menue():
    befehle.alle_laden()
    TASTEN.clear()
    _gesehen.clear()
    for name, arg, taste in ZUSATZ:
        if befehle.gibt_es(name):
            TASTEN.setdefault(kennung(name, arg), []).append(taste)
    wurzel = Gio.Menu()
    wurzel.append_submenu("Datei", _datei(DATEI))
    for tab, gruppen in ribbon_daten.SPEC:
        sub = _reiter_menue(gruppen)
        if sub.get_n_items():
            wurzel.append_submenu(tab, sub)
    return wurzel
