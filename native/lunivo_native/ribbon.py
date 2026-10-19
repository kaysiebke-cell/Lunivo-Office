"""Das Band: Reiter, Gruppen, Knöpfe — gebaut aus ribbon_daten.SPEC.

Ein Knopf erscheint nur, wenn sein Befehl in befehle/ wirklich vorhanden ist.
So gibt es keinen Knopf ohne Funktion; was noch fehlt, steht in UMFANG.md."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango  # noqa: E402

from . import befehle, ribbon_daten, symbole
from .ribbon_daten import K, ZEILE, FELDER, KATALOG, RAENDER


class Band(Gtk.Box):
    def __init__(self, fenster):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.fenster = fenster
        self.haken_knoepfe = []        # (Knopf, Zustandsname)
        self._sperre = False
        self.add_css_class("register")

        self.reiterleiste = Gtk.Box(spacing=2)
        self.reiterleiste.add_css_class("register-reiter")
        self.stapel = Gtk.Stack()
        self.stapel.set_transition_type(Gtk.StackTransitionType.NONE)
        self.reiter_knoepfe = {}
        self.vorn = Gtk.Box()
        self.vorn.add_css_class("register-vorn")

        for name, gruppen in ribbon_daten.SPEC:
            seite = self._reiter_bauen(gruppen)
            if seite is None:
                continue
            self.stapel.add_named(seite, name)
            b = Gtk.ToggleButton(label=name)
            b.add_css_class("flat")
            b.add_css_class("reiterknopf")
            b.connect("toggled", self._reiter_gewaehlt, name)
            dk = Gtk.GestureClick()
            dk.set_button(1)
            dk.connect("pressed", lambda g, n, x, y: n == 2 and self._doppelklick())
            b.add_controller(dk)
            self.reiterleiste.append(b)
            self.reiter_knoepfe[name] = b
        # Werkzeug-Reiter: nur sichtbar, wenn ihr Kontext besteht
        self.werkzeug_knoepfe = {}                  # Kontext -> Knopf
        for name, kontext, gruppen in ribbon_daten.WERKZEUGE:
            seite = self._reiter_bauen(gruppen)
            if seite is None:
                continue
            self.stapel.add_named(seite, name)
            b = Gtk.ToggleButton(label=name)
            b.add_css_class("flat")
            b.add_css_class("reiterknopf")
            b.add_css_class("werkzeugreiter")
            b.set_visible(False)
            b.connect("toggled", self._reiter_gewaehlt, name)
            self.reiterleiste.append(b)
            self.reiter_knoepfe[name] = b
            self.werkzeug_knoepfe[kontext] = b
        erster = next(iter(self.reiter_knoepfe), None)
        if erster:
            self.zeige(erster)

    # ----------------------------------------------------------- Reiter
    def zeige(self, name):
        if name not in self.reiter_knoepfe:
            return
        self._sperre = True
        for n, b in self.reiter_knoepfe.items():
            b.set_active(n == name)
        self._sperre = False
        self.stapel.set_visible_child_name(name)
        self.fenster.werte["reiter"] = name

    def _doppelklick(self):
        """Doppelklick auf einen Reiter klappt das Band zu und wieder auf (Option „Doppelklick blendet das Band aus“)."""
        if self.fenster.werte.get("opt", {}).get("ansicht|Doppelklick blendet das Band aus", True):
            self.stapel.set_visible(not self.stapel.get_visible())

    def _reiter_gewaehlt(self, knopf, name):
        if self._sperre:
            return
        if knopf.get_active():
            self.zeige(name)
        else:
            knopf.set_active(True)

    def _reiter_bauen(self, gruppen):
        zeile = Gtk.Box(spacing=0)
        zeile.add_css_class("band")
        rolle = Gtk.ScrolledWindow()
        rolle.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        rolle.set_propagate_natural_height(False)
        rolle.set_min_content_height(100)
        rolle.set_max_content_height(100)
        rolle.set_vexpand(False)
        hat = False
        for name, inhalt, mehr in gruppen:
            g = self._gruppe_bauen(name, inhalt, mehr)
            if g is None:
                continue
            if hat:
                zeile.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
            zeile.append(g)
            hat = True
        if not hat:
            return None
        rolle.set_child(zeile)
        return rolle

    def _gruppe_bauen(self, name, inhalt, mehr):
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        kasten.add_css_class("gruppe")
        if inhalt == KATALOG:
            mitte = self._katalog()
        elif inhalt == RAENDER:
            mitte = self._raender()
        else:
            mitte = self._knoepfe(inhalt)
        if mitte is None:
            return None
        mitte.set_vexpand(True)
        mitte.set_valign(Gtk.Align.CENTER)
        kasten.append(mitte)
        kopf = Gtk.Box()
        titel = Gtk.Label(label=name.upper())
        titel.add_css_class("gruppenname")
        titel.set_hexpand(True)
        titel.set_halign(Gtk.Align.CENTER)
        kopf.append(titel)
        if mehr and befehle.gibt_es(mehr):
            pfeil = Gtk.Button()
            pfeil.add_css_class("flat")
            pfeil.add_css_class("gruppenpfeil")
            pfeil.set_child(symbole.Symbol("pfeilrechts", 12) if symbole.gibt_es("pfeilrechts") else Gtk.Label(label="↘"))
            pfeil.set_tooltip_text(name + " …")
            pfeil.connect("clicked", lambda *_: befehle.ausfuehren(self.fenster, mehr))
            kopf.append(pfeil)
        kasten.append(kopf)
        return kasten

    # ----------------------------------------------------------- Knöpfe
    def _knoepfe(self, eintraege):
        gross, klein_zeilen = [], [[]]
        for e in eintraege:
            if e == ZEILE:
                klein_zeilen.append([])
                continue
            if e == FELDER:
                klein_zeilen[-1].append(FELDER)
                continue
            if not self._verfuegbar(e):
                continue
            if e.gross:
                gross.append(e)
            else:
                klein_zeilen[-1].append(e)
        explizite_zeilen = len([z for z in klein_zeilen if z]) > 1 or any(z and z[0] == FELDER for z in klein_zeilen)
        box = Gtk.Box(spacing=2)
        box.set_valign(Gtk.Align.CENTER)
        for e in gross:
            box.append(self._knopf(e, True))
        klein = [e for z in klein_zeilen for e in z]
        if klein:
            gitter = Gtk.Grid(row_spacing=2, column_spacing=2)
            gitter.set_valign(Gtk.Align.CENTER)
            if explizite_zeilen:
                for r, z in enumerate([z for z in klein_zeilen if z]):
                    c = 0
                    for e in z:
                        if e == FELDER:
                            gitter.attach(self._felder(), c, r, 8, 1)
                            c += 8
                        else:
                            gitter.attach(self._knopf(e, False), c, r, 1, 1)
                            c += 1
            else:
                zeilen = 3 if len(klein) > 3 else len(klein)
                zeilen = max(zeilen, 1)
                for i, e in enumerate(klein):
                    gitter.attach(self._knopf(e, False), i // zeilen, i % zeilen, 1, 1)
            box.append(gitter)
        if not gross and not klein:
            return None
        return box

    def _verfuegbar(self, k):
        if not isinstance(k, K):
            return True
        pruefe = [k.aktion[0] if isinstance(k.aktion, tuple) else k.aktion] if k.aktion else []
        if k.klappe:
            pruefe.append(k.klappe)
        if k.menue:
            return all(m == "-" or befehle.gibt_es(m[1]) for m in k.menue)
        return bool(pruefe) and all(befehle.gibt_es(p) or befehle.gibt_klappe(p) for p in pruefe)

    def _inhalt(self, k, gross):
        groesse = 34 if gross else 22
        if k.symbol and symbole.gibt_es(k.symbol):
            bild = symbole.Symbol(k.symbol, groesse)
        else:
            bild = Gtk.Label(label=k.text or k.name[:2])
            bild.add_css_class("textsymbol")
            if k.name in ("Fett",):
                bild.add_css_class("t-fett")
            elif k.name == "Kursiv":
                bild.add_css_class("t-kursiv")
            elif k.name == "Unterstrichen":
                bild.add_css_class("t-unter")
        if not gross:
            return bild
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        kasten.append(bild)
        beschr = Gtk.Label(label=k.name)
        beschr.set_wrap(True)
        beschr.set_wrap_mode(Pango.WrapMode.WORD)
        beschr.set_justify(Gtk.Justification.CENTER)
        beschr.set_lines(2)
        beschr.set_ellipsize(Pango.EllipsizeMode.END)
        beschr.set_max_width_chars(16)
        beschr.set_width_chars(9)
        beschr.add_css_class("knopfname")
        kasten.append(beschr)
        return kasten

    def _knopf(self, k, gross):
        hat_haken = bool(k.haken)
        haupt = Gtk.ToggleButton() if hat_haken else Gtk.Button()
        haupt.add_css_class("flat")
        haupt.add_css_class("bandknopf")
        haupt.add_css_class("gross" if gross else "klein")
        haupt.set_child(self._inhalt(k, gross))
        haupt.set_tooltip_text(k.name)
        arg = None
        aktion = k.aktion
        if isinstance(aktion, tuple):
            aktion, arg = aktion
        # K(..., "thema", "auto") legt das Argument als drittes Positionsargument ab
        if isinstance(k.klappe, str) is False and k.klappe is not None:
            pass

        if k.menue:
            return self._menueknopf(k, haupt, gross)
        if k.klappe and not aktion:
            return self._klappenknopf(k, haupt, gross)

        if hat_haken:
            self.haken_knoepfe.append((haupt, k.haken))
            haupt.connect("toggled", lambda b, a=aktion, ar=arg: (not self._sperre) and befehle.ausfuehren(self.fenster, a, ar))
        else:
            haupt.connect("clicked", lambda b, a=aktion, ar=arg: befehle.ausfuehren(self.fenster, a, ar))
        if k.klappe:
            return self._geteilt(haupt, k, gross)
        return haupt

    def _klappe_popover(self, k, anker):
        pop = Gtk.Popover()
        pop.set_parent(anker)
        pop.set_has_arrow(False)
        pop.set_autohide(True)
        inhalt = befehle.klappe_bauen(self.fenster, k.klappe, pop)
        if inhalt is None:
            return None
        pop.set_child(inhalt)
        return pop

    def _klappenknopf(self, k, haupt, gross):
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL if gross else Gtk.Orientation.HORIZONTAL)
        mb = Gtk.MenuButton()
        mb.add_css_class("flat")
        mb.add_css_class("bandknopf")
        mb.set_child(self._inhalt(k, gross))
        mb.set_tooltip_text(k.name)
        mb.set_always_show_arrow(not gross)
        mb.set_create_popup_func(lambda m: self._popover_an(m, k))
        if gross:
            wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            wrap.append(mb)
            return wrap
        return mb

    def _popover_an(self, mb, k):
        pop = Gtk.Popover()
        pop.set_has_arrow(False)
        inhalt = befehle.klappe_bauen(self.fenster, k.klappe, pop)
        if inhalt is None:
            return
        pop.set_child(inhalt)
        mb.set_popover(pop)

    def _geteilt(self, haupt, k, gross):
        kasten = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL if not gross else Gtk.Orientation.VERTICAL)
        kasten.add_css_class("linked")
        kasten.append(haupt)
        mb = Gtk.MenuButton()
        mb.add_css_class("flat")
        mb.add_css_class("klappenpfeil")
        mb.set_icon_name("pan-down-symbolic")
        mb.set_tooltip_text(k.name + " – mehr")
        mb.set_create_popup_func(lambda m: self._popover_an(m, k))
        kasten.append(mb)
        return kasten

    def _menueknopf(self, k, haupt, gross):
        mb = Gtk.MenuButton()
        mb.add_css_class("flat")
        mb.add_css_class("bandknopf")
        mb.add_css_class("gross" if gross else "klein")
        mb.set_child(self._inhalt(k, gross))
        mb.set_tooltip_text(k.name)
        pop = Gtk.Popover()
        pop.set_has_arrow(False)
        liste = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        liste.add_css_class("klappliste")
        for m in k.menue:
            if m == "-":
                liste.append(Gtk.Separator())
                continue
            text, a = m[0], m[1]
            arg = m[2] if len(m) > 2 else None
            b = Gtk.Button(label=text)
            b.add_css_class("flat")
            b.set_halign(Gtk.Align.FILL)
            b.get_child().set_xalign(0)
            b.connect("clicked", lambda _b, a=a, ar=arg, p=pop: (p.popdown(), befehle.ausfuehren(self.fenster, a, ar)))
            liste.append(b)
        pop.set_child(liste)
        mb.set_popover(pop)
        return mb

    # ----------------------------------------------------------- Sonderfelder
    def _felder(self):
        return befehle.felder_bauen(self.fenster)

    def _katalog(self):
        return befehle.katalog_bauen(self.fenster)

    def _raender(self):
        return befehle.raender_bauen(self.fenster)

    def kontext_setzen(self, kontexte):
        """Zeigt die Werkzeug-Reiter, deren Kontext gerade besteht, und blendet die übrigen aus."""
        for kontext, knopf in self.werkzeug_knoepfe.items():
            sichtbar = kontext in kontexte
            if knopf.get_visible() != sichtbar:
                knopf.set_visible(sichtbar)
                if not sichtbar and knopf.get_active():
                    self.zeige("Start")

    # ----------------------------------------------------------- Zustand
    def auffrischen(self):
        self._sperre = True
        try:
            for knopf, name in self.haken_knoepfe:
                an = bool(self.fenster.zustand(name))
                if knopf.get_active() != an:
                    knopf.set_active(an)
        finally:
            self._sperre = False
