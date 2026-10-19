"""Die Symbole der alten Oberfläche (Lucide, ISC-Lizenz) als Gtk.Image.

Jedes Symbol ist ein Pfad im Feld 24 × 24, gezeichnet mit Strich ohne Füllung
(daten/symbole.json, aus oberflaeche/daten/symbole.js). Die Farbe folgt dem
hellen oder dunklen Thema; beim Wechsel zeichnen sich alle Symbole neu."""
import json
import os
import weakref

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Adw  # noqa: E402

_PFADE = {}
try:
    with open(os.path.join(os.path.dirname(__file__), "daten", "symbole.json"), encoding="utf-8") as f:
        _PFADE = json.load(f)
except (OSError, ValueError):
    pass

_alle = weakref.WeakSet()
_cache = {}


def gibt_es(name):
    return name in _PFADE


def _farbe():
    return "#E6E9EC" if Adw.StyleManager.get_default().get_dark() else "#2B2F33"


def textur(name, groesse, farbe=None):
    farbe = farbe or _farbe()
    schluessel = (name, groesse, farbe)
    if schluessel in _cache:
        return _cache[schluessel]
    pfad = _PFADE.get(name)
    if not pfad:
        return None
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="%d" height="%d" '
           'fill="none" stroke="%s" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
           '<path d="%s"/></svg>') % (groesse * 2, groesse * 2, farbe, pfad.replace('"', ""))
    try:
        lader = GdkPixbuf.PixbufLoader.new_with_type("svg")
        lader.write(svg.encode("utf-8"))
        lader.close()
        t = Gdk.Texture.new_for_pixbuf(lader.get_pixbuf())
    except GLib.Error:
        return None
    _cache[schluessel] = t
    return t


class Symbol(Gtk.Image):
    def __init__(self, name, groesse=20):
        super().__init__()
        self.name = name
        self.groesse = groesse
        self.set_pixel_size(groesse)
        self.auffrischen()
        _alle.add(self)

    def auffrischen(self):
        t = textur(self.name, self.groesse)
        if t is not None:
            self.set_from_paintable(t)


def alle_auffrischen(*_):
    _cache.clear()
    for s in list(_alle):
        s.auffrischen()


Adw.StyleManager.get_default().connect("notify::dark", alle_auffrischen)
