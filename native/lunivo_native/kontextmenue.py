"""Die rechte Maustaste, wie im WPS Writer (doku/oberflaeche.md, bilder/rechtsklick.png):
oben eine schwebende Formatleiste, darunter ein Menü mit Bild links und Tastenkombination rechts.
Was gerade nicht geht, steht grau da, statt zu fehlen."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

from . import befehle, schreibhilfe, symbole


def _zeile(text, symbol=None, taste="", pfeil=False, haken=False, fett=False):
    k = Gtk.Box(spacing=10)
    if symbole.gibt_es(symbol or ""):
        k.append(symbole.Symbol(symbol, 16))
    else:
        k.append(Gtk.Label(label="✓" if haken else " ", width_chars=2))
    l = Gtk.Label(label=text, xalign=0, hexpand=True)
    if fett:
        l.add_css_class("t-fett")
    k.append(l)
    if taste:
        t = Gtk.Label(label=taste, xalign=1)
        t.add_css_class("dim-label")
        t.add_css_class("klein-text")
        k.append(t)
    if pfeil:
        k.append(Gtk.Label(label="›"))
    return k


class Kontextmenue(Gtk.Popover):
    def __init__(self, fenster, dok, x, y):
        super().__init__()
        self.w = fenster
        self.d = dok
        self.set_parent(dok.ansicht)
        self.set_has_arrow(False)
        self.set_halign(Gtk.Align.START)
        self.add_css_class("kontextmenue")
        r = Gdk.Rectangle()
        r.x, r.y, r.width, r.height = int(x), int(y), 1, 1
        self.set_pointing_to(r)
        self.connect("closed", lambda *_: GLib.idle_add(self.unparent))
        self.stapel = Gtk.Stack()
        self.stapel.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_child(self.stapel)
        self.stapel.add_named(self._haupt(x, y), "haupt")
        for name, eintraege in self._untermenues().items():
            self.stapel.add_named(self._unterseite(name, eintraege), name)

    # ------------------------------------------------------------ Hilfen
    def _tun(self, name, arg=None):
        self.popdown()
        GLib.idle_add(lambda: befehle.ausfuehren(self.w, name, arg) and False)

    def _knopf(self, inhalt, fn, aktiv=True):
        b = Gtk.Button()
        b.add_css_class("flat")
        b.set_child(inhalt)
        b.set_sensitive(aktiv)
        b.connect("clicked", lambda *_: fn())
        return b

    # ------------------------------------------------------------ schwebende Formatleiste
    def _formatleiste(self):
        d, w = self.d, self.w
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.add_css_class("miniformat")
        z1 = Gtk.Box(spacing=4)
        fam = Gtk.DropDown.new_from_strings(w.familien)
        fam.set_size_request(150, -1)
        aktuell = next((t[4:] for t in d.tippen if t.startswith("fam:")), d.vorgabe_schrift)
        if aktuell in w.familien:
            fam.set_selected(w.familien.index(aktuell))
        fam.connect("notify::selected", lambda s, *_: d.wert_setzen("fam:", "fam:" + w.familien[s.get_selected()]))
        gr = Gtk.DropDown.new_from_strings(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36", "48", "72"])
        gr.connect("notify::selected", lambda s, *_: d.wert_setzen("size:", "size:" + s.get_selected_item().get_string()))
        z1.append(fam)
        z1.append(gr)
        for sym, tipp, bef in (("groesserA", "Schrift vergrößern", "schrift_groesser"), ("kleinerA", "Schrift verkleinern", "schrift_kleiner")):
            z1.append(self._knopf(symbole.Symbol(sym, 16), lambda b=bef: self._tun(b)))
        box.append(z1)
        z2 = Gtk.Box(spacing=2)
        for text, bef, stil in (("F", "fett", "t-fett"), ("K", "kursiv", "t-kursiv"), ("U", "unter", "t-unter")):
            l = Gtk.Label(label=text)
            l.add_css_class(stil)
            z2.append(self._knopf(l, lambda b=bef: self._tun(b)))
        z2.append(self._knopf(symbole.Symbol("marker", 16), lambda: self._tun("hervorheben_jetzt")))
        z2.append(self._knopf(symbole.Symbol("schriftfarbe", 16), lambda: self._tun("schriftfarbe_jetzt")))
        z2.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        for sym, bef in (("links", "links"), ("mitte", "mitte"), ("rechts", "rechts"), ("block", "block")):
            z2.append(self._knopf(symbole.Symbol(sym, 16), lambda b=bef: self._tun(b)))
        z2.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        z2.append(self._knopf(symbole.Symbol("pinsel", 16), lambda: self._tun("format_uebertragen")))
        box.append(z2)
        return box

    # ------------------------------------------------------------ Hauptseite
    def _wort_fund(self, x, y):
        """Der Fund der Schreibhilfe, der unter dem Mauszeiger liegt (auch ohne vorherige Prüfung)."""
        d = self.d
        ok, it = d.ansicht.get_iter_at_location(*d.ansicht.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(x), int(y)))
        if not ok:
            return None, None
        pos = it.get_offset()
        try:
            text = d.text()
            for f in schreibhilfe.pruefen(text):
                if f["von"] <= pos <= f["bis"]:
                    return f, text
        except Exception:
            pass
        return None, None

    def _haupt(self, x, y):
        d, w = self.d, self.w
        sel = bool(d.puffer.get_selection_bounds())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("klappliste")
        box.append(self._formatleiste())
        menue = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        menue.add_css_class("kontextliste")
        fund, text = self._wort_fund(x, y)
        if fund is not None and fund.get("neu") is not None:
            kopf = Gtk.Label(label="Schreibweise" if fund.get("wortEbene") else "Regel", xalign=0)
            kopf.add_css_class("dim-label")
            kopf.add_css_class("klein-text")
            kopf.set_margin_start(12)
            menue.append(kopf)
            neu = fund["neu"]
            menue.append(self._knopf(_zeile(neu if neu else "(entfernen)", fett=True),
                                     lambda: (self.popdown(), d.bereich_ersetzen(fund["von"], fund["bis"], neu))))
            if fund.get("wortEbene"):
                wort = fund["alt"]
                menue.append(self._knopf(_zeile("Wort ins Gedächtnis aufnehmen", haken=True),
                                         lambda: (self.popdown(), d._rs_merken(wort))))
            menue.append(Gtk.Separator())
        menue.append(self._knopf(_zeile("Kopieren", "kopie", "Strg+C"), lambda: self._tun("kopieren"), sel))
        menue.append(self._knopf(_zeile("Ausschneiden", "schere", "Strg+X"), lambda: self._tun("ausschneiden"), sel))
        menue.append(self._knopf(_zeile("Einfügen", "kleben", "Strg+V"), lambda: self._tun("einfuegen")))
        menue.append(self._knopf(_zeile("Einfügen ohne Formatierung", "ohneformat"), lambda: self._tun("einfuegen_ohne")))
        menue.append(Gtk.Separator())
        for name, sym in (("Absatz", "einzug"), ("Aufzählung und Nummerierung", "punkte"), ("Formatvorlage", "stil")):
            menue.append(self._knopf(_zeile(name, sym, pfeil=True), lambda n=name: self.stapel.set_visible_child_name(n)))
        menue.append(Gtk.Separator())
        menue.append(self._knopf(_zeile("Hyperlink…", "kette", "Strg+K"), lambda: self._tun("hyperlink")))
        menue.append(self._knopf(_zeile("Kommentar einfügen", "notiz"), lambda: self._tun("kommentar")))
        menue.append(Gtk.Separator())
        menue.append(self._knopf(_zeile("Thesaurus", "thesaurus"), lambda: self._tun("thesaurus")))
        menue.append(self._knopf(_zeile("Rechtschreibung und Grammatik", "haken", "F7"), lambda: self._tun("pruefen")))
        box.append(menue)
        return box

    # ------------------------------------------------------------ Untermenüs
    def _untermenues(self):
        d = self.d
        return {
            "Absatz": [("Linksbündig", "links"), ("Zentriert", "mitte"), ("Rechtsbündig", "rechts"), ("Blocksatz", "block"),
                       "-", ("Einzug vergrößern", "einzug_mehr"), ("Einzug verringern", "einzug_weniger"),
                       ("Genaues Maß…", "einzug_genau"), "-", ("Sortieren", "sortieren")],
            "Aufzählung und Nummerierung": [("Aufzählung", "punkte"), ("Nummerierung", "zahlen"), "-",
                                            ("Listenebene erhöhen", "ebene_hoeher"), ("Listenebene verringern", "ebene_tiefer")],
            "Formatvorlage": [(n, "stil", n) for n in ("Fließtext", "Titel", "Untertitel", "Überschrift 1", "Überschrift 2",
                                                       "Überschrift 3", "Zitat", "Code")],
        }

    def _unterseite(self, name, eintraege):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("klappliste")
        box.add_css_class("kontextliste")
        zurueck = Gtk.Button()
        zurueck.add_css_class("flat")
        zurueck.set_child(Gtk.Label(label="‹  " + name, xalign=0))
        zurueck.connect("clicked", lambda *_: self.stapel.set_visible_child_name("haupt"))
        box.append(zurueck)
        box.append(Gtk.Separator())
        for e in eintraege:
            if e == "-":
                box.append(Gtk.Separator())
                continue
            text, bef = e[0], e[1]
            arg = e[2] if len(e) > 2 else None
            if bef == "stil":
                box.append(self._knopf(_zeile(text), lambda n=text: (self.popdown(), self.d.stil_setzen(n))))
            else:
                box.append(self._knopf(_zeile(text), lambda b=bef, a=arg: self._tun(b, a)))
        return box


def zeigen(fenster, dok, x, y):
    if not dok.puffer.get_selection_bounds():
        ok, it = dok.ansicht.get_iter_at_location(*dok.ansicht.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(x), int(y)))
        if ok:
            dok.puffer.place_cursor(it)
    m = Kontextmenue(fenster, dok, x, y)
    m.popup()
    return m
