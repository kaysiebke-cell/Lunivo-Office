"""Die Schreibhilfe-Seitenleiste: Prüfen, Funde, Für wen?, KI-Knöpfe."""
import threading

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from . import befehle, schreibhilfe

ZIELGRUPPEN = ["egal", "Amt", "Arbeit", "Freunde", "Forum", "Bewerbung"]


class Schreibhilfe(Gtk.Box):
    def __init__(self, fenster):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.fenster = fenster
        self.funde = []
        self.fund_dokument = None
        self.add_css_class("schreibhilfe")
        self.set_size_request(340, -1)
        for r in ("start", "end", "top", "bottom"):
            getattr(self, "set_margin_" + r)(10)

        # Kopf: „Schreib | hilfe“, die drei Marken (Wörter · Vorschläge · KI) und „Prüfen“
        kopf = Gtk.Box(spacing=6)
        t = Gtk.Label(use_markup=True, xalign=0, label="<b>Schreib</b> <span alpha='50%'>|</span> <b>hilfe</b>")
        kopf.append(t)
        self.marken = {}
        for kurz, tipp in (("We", "Wörter: Rechtschreibung beim Schreiben"), ("Vo", "Vorhersage: Wortvorschläge"),
                           ("Ko", "Korrektur: AutoKorrektur")):
            m = Gtk.ToggleButton(label=kurz)
            m.add_css_class("marke")
            m.set_tooltip_text(tipp)
            m.connect("toggled", self._marke, kurz)
            self.marken[kurz] = m
            kopf.append(m)
        kopf.append(Gtk.Box(hexpand=True))
        self.pruef_knopf = Gtk.Button(label="Prüfen")
        self.pruef_knopf.add_css_class("klein-knopf")
        self.pruef_knopf.connect("clicked", lambda *_: befehle.ausfuehren(fenster, "pruefen"))
        kopf.append(self.pruef_knopf)
        self.append(kopf)

        self.hinweis = Gtk.Label(label="Hier erscheinen die Funde der Schreibhilfe. Sie sucht die Fehler, die ein "
                                       "Rechtschreibprüfer nicht finden kann.", xalign=0, wrap=True)
        self.hinweis.add_css_class("dim-label")
        self.hinweis.add_css_class("klein-text")
        self.append(self.hinweis)

        self.fund_liste = Gtk.ListBox()
        self.fund_liste.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.fund_liste.add_css_class("fundliste")
        self.fund_liste.connect("row-selected", self._fund_gewaehlt)
        rolle = Gtk.ScrolledWindow(vexpand=True)
        rolle.set_child(self.fund_liste)
        self.append(rolle)

        aktionen = Gtk.Box(spacing=6)
        self.b_uebernehmen = Gtk.Button(label="Übernehmen")
        self.b_uebernehmen.add_css_class("klein-knopf")
        self.b_uebernehmen.connect("clicked", lambda *_: self._fund_uebernehmen())
        self.b_ignorieren = Gtk.Button(label="Ignorieren")
        self.b_ignorieren.add_css_class("klein-knopf")
        self.b_ignorieren.connect("clicked", lambda *_: self._fund_ignorieren())
        aktionen.append(self.b_uebernehmen)
        aktionen.append(self.b_ignorieren)
        self.append(aktionen)

        self.append(Gtk.Separator())
        fw = Gtk.Label(label="FÜR WEN?", xalign=0)
        fw.add_css_class("abschnitt")
        self.append(fw)
        gruppe = Gtk.FlowBox()
        gruppe.set_selection_mode(Gtk.SelectionMode.NONE)
        gruppe.set_max_children_per_line(8)
        gruppe.set_row_spacing(4)
        gruppe.set_column_spacing(4)
        erster = None
        self.ziel_knoepfe = {}
        for z in ZIELGRUPPEN:
            b = Gtk.ToggleButton(label=z)
            b.add_css_class("chip")
            if erster:
                b.set_group(erster)
            else:
                erster = b
            b.connect("toggled", lambda b, z=z: b.get_active() and fenster.werte.__setitem__("zielgruppe", z))
            if z == fenster.werte.get("zielgruppe", "egal"):
                b.set_active(True)
            self.ziel_knoepfe[z] = b
            gruppe.append(b)
        self.append(gruppe)
        self.worum = Gtk.Entry(placeholder_text="Worum geht’s? (freiwillig)")
        self.worum.add_css_class("worum")
        self.append(self.worum)
        ki = Gtk.Grid(row_spacing=4, column_spacing=4, column_homogeneous=True)
        self.ki_knoepfe = []
        for i, (text, a) in enumerate((("KI-Korrektur", "ki_korrektur"), ("Vorschläge", "ki_vorschlaege"),
                                       ("Nach Englisch", "ki_uebersetzen"), ("Zusammenfassen", "ki_kurz"))):
            b = Gtk.Button(label=text)
            b.add_css_class("ki-knopf")
            b.get_child().set_wrap(True)
            b.get_child().set_justify(Gtk.Justification.CENTER)
            b.connect("clicked", lambda _b, a=a: befehle.ausfuehren(fenster, a))
            self.ki_knoepfe.append(b)
            ki.attach(b, i, 0, 1, 1)
        self.append(ki)
        self.ki_hinweis = Gtk.Label(xalign=0, wrap=True)
        self.ki_hinweis.add_css_class("dim-label")
        self.ki_hinweis.add_css_class("klein-text")
        self.append(self.ki_hinweis)
        self.ki_auffrischen()

    def ki_auffrischen(self):
        """Die KI-Knöpfe sind grau, solange kein Modell gewählt ist (wie im Original)."""
        from . import schreibhilfe as sh
        a = sh.anbieter_aktiv(self.fenster.werte)
        bereit = bool(a.get("modell"))
        for b in self.ki_knoepfe:
            b.set_sensitive(bereit)
        self.ki_hinweis.set_text("" if bereit else
                                 "Die vier Knöpfe sind grau, weil noch kein Modell gewählt ist. Auf diesem Rechner läuft aber "
                                 "Ollama — damit gehen sie ohne Schlüssel und ohne Geld (Schreibhilfe ▸ KI-Konfiguration).")
        self.ki_hinweis.set_visible(not bereit)

    def _marke(self, knopf, kurz):
        if getattr(self, "_marken_sperre", False):
            return
        befehl = {"We": "rechtschreibung", "Vo": "vorhersage", "Ko": "autokorrektur"}[kurz]
        if bool(self.fenster.werte["an"].get(befehl, False)) != knopf.get_active():
            befehle.ausfuehren(self.fenster, befehl)

    def marken_auffrischen(self):
        self._marken_sperre = True
        for kurz, bef in (("We", "rechtschreibung"), ("Vo", "vorhersage"), ("Ko", "autokorrektur")):
            self.marken[kurz].set_active(bool(self.fenster.werte["an"].get(bef, False)))
        self._marken_sperre = False

    def ziel_setzen(self, ziel):
        if ziel in self.ziel_knoepfe:
            self.ziel_knoepfe[ziel].set_active(True)

    def zielgruppe(self):
        return self.fenster.werte.get("zielgruppe", "egal"), self.worum.get_text().strip()

    def leeren(self):
        k = self.fund_liste.get_first_child()
        while k:
            n = k.get_next_sibling()
            self.fund_liste.remove(k)
            k = n
        self.funde = []

    def zeigen(self, dok, funde):
        self.leeren()
        self.fund_dokument = dok
        self.funde = funde
        for f in funde:
            zeile = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            for r in ("top", "bottom"):
                getattr(box, "set_margin_" + r)(6)
            for r in ("start", "end"):
                getattr(box, "set_margin_" + r)(8)
            g = Gtk.Label(label=f.get("grund", ""), xalign=0, wrap=True)
            g.add_css_class("fund-fehler" if f.get("art") == "fehler" else "fund-tipp")
            box.append(g)
            if f.get("zeigeAlt") is not None:
                box.append(Gtk.Label(label="%s  →  %s" % (f.get("zeigeAlt", ""), f.get("zeigeNeu", "")),
                                     xalign=0, wrap=True))
            zeile.set_child(box)
            self.fund_liste.append(zeile)

    def _aktuell(self):
        z = self.fund_liste.get_selected_row()
        if z is None:
            return None, None
        i = z.get_index()
        return (i, self.funde[i]) if 0 <= i < len(self.funde) else (None, None)

    def _fund_gewaehlt(self, liste, zeile):
        i, f = self._aktuell()
        if f and self.fund_dokument:
            self.fund_dokument.bereich_waehlen(f["von"], f["bis"])

    def _fund_uebernehmen(self):
        i, f = self._aktuell()
        d = self.fund_dokument
        if f is None or d is None or f.get("neu") is None:
            return
        d.bereich_ersetzen(f["von"], f["bis"], f["neu"])
        self._entfernen(i, len(f["neu"]) - (f["bis"] - f["von"]), f["bis"])

    def _fund_ignorieren(self):
        i, f = self._aktuell()
        if f is not None:
            self._entfernen(i, 0, f["bis"])

    def _entfernen(self, i, delta, ab):
        self.funde.pop(i)
        for g in self.funde:
            if g["von"] >= ab:
                g["von"] += delta
                g["bis"] += delta
        z = self.fund_liste.get_row_at_index(i)
        if z:
            self.fund_liste.remove(z)
        self.fenster.status("%d Funde übrig." % len(self.funde))
