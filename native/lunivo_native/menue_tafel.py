"""Das ☰-Menü wie im Original (dateiTafelPunkte): links die Punkte, rechts das Untermenü
oder — wenn nichts offen ist — die Liste der zuletzt verwendeten Dateien."""
import os

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from . import befehle

STRICH = "-"

# (Name, Befehl, Argument, Taste) · (Name, [Untermenü-Einträge]) · STRICH
PUNKTE = [
    ("Neu", [("Leeres Dokument", "neu", None, "Strg+N"), ("Neu aus Vorlage", "vorlagen_waehlen", None, ""),
             ("Vorlagenordner", "vorlagen_ordner", None, "")]),
    ("Öffnen", "oeffnen", None, "Strg+O"),
    ("Speichern", "speichern", None, "Strg+S"),
    ("Speichern unter", [("Speichern unter …", "speichern_unter", None, "Strg+Umschalt+S"),
                         ("Umbenennen", "umbenennen", None, "")]),
    ("Als PDF exportieren", "speichern_pdf", None, ""),
    ("Als Bild exportieren", "speichern_bild", None, ""),
    ("Drucken", [("Drucken …", "drucken", None, "Strg+P"), ("Druckvorschau", "vorschau", None, "")]),
    STRICH,
    ("Dokumentverschlüsselung", [("Verschlüsselung …", "optionen", "sicherheit", ""),
                                 ("Eigenschaften …", "eigenschaften", None, "")]),
    STRICH,
    ("Hilfe", [("Handbuch", "handbuch", None, ""), ("Tastenkürzel", "tasten_hilfe", None, ""),
               ("Erweiterungen", "erweiterungen", None, ""), ("Über Lunivo Office", "ueber", None, "")]),
    ("Optionen", "optionen", None, "F9"),
    ("Beenden", "beenden", None, ""),
]


def _zeile(text, taste="", pfeil=False):
    k = Gtk.Box(spacing=8)
    l = Gtk.Label(label=text, xalign=0, hexpand=True)
    k.append(l)
    if taste:
        t = Gtk.Label(label=taste, xalign=1)
        t.add_css_class("dim-label")
        t.add_css_class("klein-text")
        k.append(t)
    if pfeil:
        k.append(Gtk.Label(label="›"))
    return k


class MenueTafel(Gtk.Popover):
    def __init__(self, fenster):
        super().__init__()
        self.fenster = fenster
        self.set_has_arrow(False)
        self.set_halign(Gtk.Align.START)          # links bündig unter dem Knopf, nicht mittig
        self.set_position(Gtk.PositionType.BOTTOM)
        self.add_css_class("menuetafel")
        haupt = Gtk.Box(spacing=0)
        self.links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.links.set_size_request(250, -1)
        self.links.add_css_class("klappliste")
        self.rechts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.rechts.set_size_request(300, 280)
        for r in ("start", "end", "top", "bottom"):
            getattr(self.rechts, "set_margin_" + r)(10)
        self.punkte = []
        for p in PUNKTE:
            if p == STRICH:
                self.links.append(Gtk.Separator())
                continue
            unter = isinstance(p[1], list)
            b = Gtk.Button()
            b.add_css_class("flat")
            b.set_child(_zeile(p[0], "" if unter else p[3], unter))
            ctrl = Gtk.EventControllerMotion()
            ctrl.connect("enter", lambda *_a, p=p: self._geh_ueber(p))
            b.add_controller(ctrl)
            b.connect("clicked", lambda _b, p=p: self._klick(p))
            self.links.append(b)
            self.punkte.append(b)
        haupt.append(self.links)
        haupt.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        haupt.append(self.rechts)
        self.set_child(haupt)
        self.connect("show", lambda *_: self._zuletzt_zeigen())

    def _leeren(self):
        k = self.rechts.get_first_child()
        while k:
            n = k.get_next_sibling()
            self.rechts.remove(k)
            k = n

    def _ausfuehren(self, name, arg):
        self.popdown()
        GLib.idle_add(lambda: befehle.ausfuehren(self.fenster, name, arg) and False)

    def _geh_ueber(self, p):
        if isinstance(p[1], list):
            self._unter_zeigen(p)
        else:
            self._zuletzt_zeigen()

    def _klick(self, p):
        if isinstance(p[1], list):
            self._unter_zeigen(p)
        else:
            self._ausfuehren(p[1], p[2])

    def _unter_zeigen(self, p):
        self._leeren()
        t = Gtk.Label(label=p[0], xalign=0)
        t.add_css_class("dim-label")
        self.rechts.append(t)
        for text, name, arg, taste in p[1]:
            b = Gtk.Button()
            b.add_css_class("flat")
            b.set_child(_zeile(text, taste))
            b.connect("clicked", lambda _b, n=name, a=arg: self._ausfuehren(n, a))
            self.rechts.append(b)

    def _zuletzt_zeigen(self):
        self._leeren()
        kopf = Gtk.Box(spacing=6)
        t = Gtk.Label(label="Liste zuletzt verwendeter Dateien", xalign=0, hexpand=True)
        t.add_css_class("dim-label")
        kopf.append(t)
        neu = Gtk.Button(label="↻")
        neu.add_css_class("flat")
        neu.set_tooltip_text("Liste auffrischen")
        neu.connect("clicked", lambda *_: self._zuletzt_zeigen())
        kopf.append(neu)
        self.rechts.append(kopf)
        liste = [p for p in self.fenster.werte.get("zuletzt", []) if os.path.exists(p)]
        if not liste:
            l = Gtk.Label(label="Noch nichts geöffnet.", xalign=0)
            l.set_margin_top(8)
            self.rechts.append(l)
        for p in liste[:10]:
            zeile = Gtk.Box(spacing=4)
            b = Gtk.Button(hexpand=True)
            b.add_css_class("flat")
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            col.append(Gtk.Label(label=os.path.basename(p), xalign=0))
            ort = Gtk.Label(label=os.path.dirname(p), xalign=0)
            ort.add_css_class("dim-label")
            ort.add_css_class("klein-text")
            col.append(ort)
            b.set_child(col)
            b.connect("clicked", lambda _b, p=p: (self.popdown(), self.fenster.datei_oeffnen(p)))
            weg = Gtk.Button(label="×")
            weg.add_css_class("flat")
            weg.set_tooltip_text("Aus der Liste nehmen (die Datei bleibt liegen)")
            weg.connect("clicked", lambda _b, p=p: (self.fenster.werte.__setitem__(
                "zuletzt", [x for x in self.fenster.werte.get("zuletzt", []) if x != p]), self._zuletzt_zeigen()))
            zeile.append(b)
            zeile.append(weg)
            self.rechts.append(zeile)
