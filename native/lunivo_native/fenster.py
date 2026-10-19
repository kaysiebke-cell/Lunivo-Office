"""Hauptfenster: Titelzeile mit Reitern, Menü, Schnellzugriff, Band, Seitenleisten, Statuszeile."""
import json
import os

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib, Gdk, Adw  # noqa: E402

from . import befehle, editor, einstellungen, krypto, menue_tafel, menues, pfade, ribbon, symbole
from .schreibhilfe_panel import Schreibhilfe


STYLE = """
@define-color grund #1F2225;
@define-color leiste #2A2E32;
@define-color tafel #26292D;
@define-color karte #2F3338;
@define-color rand #3A3F45;
@define-color schrift #E6E9EC;
@define-color schrift2 #A7AFB7;
@define-color blau #2F6FB5;

.lunivo-dunkel { background: @grund; color: @schrift; }
.lunivo-dunkel .register, .lunivo-dunkel .titelzeile, .lunivo-dunkel .statuszeile { background: @leiste; color: @schrift; }
.lunivo-dunkel .seitenleiste-schmal, .lunivo-dunkel .navigation, .lunivo-dunkel .schreibhilfe { background: @tafel; color: @schrift; }
.lunivo-dunkel .arbeitsflaeche { background: #1F2225; }
.lunivo-dunkel .band { background: @leiste; }
.lunivo-dunkel .gruppenname { color: @schrift2; }
.lunivo-dunkel .register-reiter button.reiterknopf:checked { background: transparent; color: #FFFFFF; box-shadow: inset 0 -2px @blau; }
.lunivo-dunkel .statuszeile { color: @schrift2; border-top: 1px solid @rand; }
.lunivo-dunkel separator { background: @rand; }
.lunivo-dunkel entry, .lunivo-dunkel dropdown > button { background: @karte; color: @schrift; }

.hell .register, .hell .titelzeile, .hell .statuszeile, .hell .band { background: #F3F4F6; }
.hell .arbeitsflaeche { background: #CFD3D8; }

.titelzeile { padding: 2px 8px; }
.titel-logo { font-size: 22.1px; font-weight: 300; margin-right: 12px; }
.register-reiter { padding: 0 10px; }
button.reiterknopf { padding: 7px 16px; border-radius: 0; min-height: 25px; }
button.werkzeugreiter { color: #D08A3E; }
.band { padding: 0 6px; min-height: 0; }
.gruppe { padding: 2px 6px 0 6px; }
.gruppenname { font-size: 11.7px; letter-spacing: 0.08em; padding: 1px 0 2px 0; }
button.bandknopf.gross { padding: 2px 4px; min-width: 60px; min-height: 0; }
button.bandknopf.klein { padding: 1px 4px; min-width: 24px; min-height: 25px; }
button.klappenpfeil { min-width: 17px; min-height: 15px; padding: 0; }
button.bandknopf { margin: 0; }
.knopfname { font-size: 14.3px; }
.textsymbol { font-size: 16.9px; min-width: 22px; }
.t-fett { font-weight: bold; }
.t-kursiv { font-style: italic; }
.t-unter { text-decoration: underline; }
.seitenleiste-schmal { padding: 6px 3px; }
.statuszeile { font-size: 15.6px; }
.statuszeile label { margin: 4px 0; }
textview.blatt, textview.blatt text { background: #FFFFFF; color: #111417; }
box.blattrahmen { box-shadow: 0 2px 8px rgba(0,0,0,.35); }
textview.blatt-kopf, textview.blatt-kopf text, textview.blatt-fuss, textview.blatt-fuss text { color: #777; font-size: 11px; }
textview.blatt-kopf { border-bottom: 1px dashed #aaa; }
textview.blatt-fuss { border-top: 1px dashed #aaa; }
.klappliste button { padding: 5px 14px; }
.stilknopf { min-width: 67px; padding: 0 4px; min-height: 0; }
.kleinname { font-size: 11.7px; opacity: 0.8; }
.stilprobe-KeinAbstand { font-size: 12px; }
.stilprobe-Fliesstext { font-size: 14px; }
.stilprobe-Titel { font-size: 18px; font-weight: bold; }
.stilprobe-Untertitel { font-size: 15px; font-style: italic; }
.stilprobe-Ueberschrift1 { font-size: 17px; font-weight: bold; }
.stilprobe-Ueberschrift2 { font-size: 15px; font-weight: bold; }
.stilprobe-Ueberschrift3 { font-size: 13px; font-weight: bold; }
.stilprobe-Zitat { font-size: 14px; font-style: italic; }
.stilprobe-Code { font-family: monospace; font-size: 13px; }
.fund-fehler { color: #E06666; font-weight: bold; }
.fund-tipp { color: #D08A3E; font-weight: bold; }
.blau-knopf { background: #2F6FB5; color: white; }

/* Das Original ist dichter: 15 px Schrift, flache Knöpfe, kleine Abstände. */
.lunivo-dunkel, .hell { font-size: 15.6px; }
.lunivo-dunkel button, .hell button { min-height: 28px; padding: 1px 8px; border-radius: 4px; }
.lunivo-dunkel button.flat, .hell button.flat { padding: 2px 6px; }
.lunivo-dunkel button.reiterknopf, .hell button.reiterknopf { padding: 5px 14px; min-height: 0; font-size: 15px; }
tabbar, tabbar > revealer > box, tabbar .box { background: transparent; box-shadow: none; border: none; }
tabbar tabbox { padding: 4px 0; }
.klein-text { font-size: 14.3px; }
.abschnitt { font-size: 13px; letter-spacing: 0.08em; opacity: 0.7; }
button.marke { min-height: 22px; min-width: 26px; padding: 0 7px; border-radius: 9px; font-size: 13px; font-weight: bold;
               background: #3E9C7A; color: #fff; border: none; }
button.marke:not(:checked) { background: transparent; color: #7C858E; border: 1px solid #4A5057; }
button.chip { min-height: 22px; padding: 1px 9px; border-radius: 12px; font-size: 14.3px; background: #2F3338; color: #E6E9EC; border: 1px solid #3A3F45; }
button.chip:checked { background: #2F6FB5; border-color: #2F6FB5; color: #fff; }
button.klein-knopf { min-height: 25px; padding: 0 10px; font-size: 14.3px; }
button.ki-knopf { min-height: 50px; font-size: 14.3px; background: #2F3338; border: 1px solid #3A3F45; border-radius: 6px; }
entry.worum { min-height: 25px; border: none; border-bottom: 1px dashed #C08A2E; border-radius: 0; background: transparent; color: #D08A3E; padding: 2px 0; }
list.fundliste { background: #2A2E32; border-radius: 4px; }
dropdown > button { min-height: 28px; }
.schreibhilfe { min-width: 360px; }
.miniformat { padding: 4px 6px; }
.kontextliste button { min-height: 32px; padding: 2px 12px; }
.kontextliste label { font-size: 16.9px; }
.optkarte { border: 1px solid @rand; border-radius: 8px; background: @tafel; }
.optzeile { padding: 8px 12px; }
popover.menuetafel button label, popover.menuetafel label { font-weight: normal; font-size: 16.9px; }
popover.menuetafel button { min-height: 35px; }
"""


class Fenster(Gtk.ApplicationWindow):
    def __init__(self, app, werte):
        super().__init__(application=app, title="Lunivo-Office")
        self.werte = werte
        self.werte.setdefault("an", {})
        self.set_default_size(*werte["fenster"])
        self.set_icon_name("lunivo-office")
        self._format_sperre = False
        self.familien = self._familien()
        self._baue_aktionen()
        self._baue_oberflaeche()
        self.hell_dunkel_anwenden()
        self.connect("close-request", self._schliessen_angefragt)
        self.reiter.connect("notify::selected-page", lambda *_: GLib.idle_add(self._dokument_gewechselt))
        self.reiter.connect("close-page", self._seite_schliessen)
        self._letzte_sicherung = 0
        from . import schreibhilfe as _sh
        _sh.OPT = self.werte.setdefault("opt", {})
        if self.werte.get("bedienung"):
            self.bedienung_skalieren(self.werte["bedienung"])
        GLib.timeout_add_seconds(15, self._autosicherung)

    # ============================================================= Grundlagen
    def _familien(self):
        fam = sorted({f.get_name() for f in Gtk.Widget.get_pango_context(self).get_font_map().list_families()},
                     key=str.lower)
        if self.werte["schriftart"] not in fam:
            fam.insert(0, self.werte["schriftart"])
        return fam

    def dok(self):
        seite = self.reiter.get_selected_page()
        return seite.get_child() if seite else None

    def alle_dokumente(self):
        return [self.reiter.get_nth_page(i).get_child() for i in range(self.reiter.get_n_pages())]

    def status(self, text):
        self.status_links.set_text(text)
        return False

    def meldung(self, titel, text):
        dlg = Gtk.AlertDialog()
        dlg.set_message(titel)
        dlg.set_detail(text)
        dlg.show(self)
        return False

    # ============================================================= Zustand (Haken im Band)
    def zustand(self, name):
        d = self.dok()
        if name in ("fett", "kursiv", "unter", "durch", "hoch", "tief", "umriss"):
            tag = {"fett": "b", "kursiv": "i", "unter": "u", "durch": "s", "hoch": "hoch",
                   "tief": "tief", "umriss": "umriss"}[name]
            return bool(d and d.hat_format(tag))
        if name.startswith("al-"):
            if not d:
                return False
            tags = d.absatz_tag_am_cursor()
            if name == "al-links":
                return not any(t.startswith("al-") for t in tags)
            return name in tags
        if name == "punkte":
            return bool(d and d.hat_liste(False))
        if name == "zahlen":
            return bool(d and d.hat_liste(True))
        if name == "steuerzeichen":
            return bool(d and getattr(d, "steuer_an", False))
        if name in ("tabelle_kopf", "tabelle_rand"):
            t = d.tabelle_aktiv if d else None
            return bool(t and t[0].daten.get("kopf" if name == "tabelle_kopf" else "rand", name == "tabelle_rand"))
        if name == "markup":
            return not self.werte["an"].get("markup_aus", False)
        if name == "tafel":
            return self.seitenleiste.get_visible()
        if name == "gesperrt":
            return bool(d and not d.ansicht.get_editable())
        if name == "navigation":
            return self.navigation.get_visible()
        if name == "menueleiste":
            return self.get_show_menubar()
        if name == "leisten":
            return self.schnell.get_visible()
        if name == "kopffuss":
            return bool(d and d.kopf_fuss_an())
        if name.startswith("thema-"):
            return self.werte.get("thema", "dark") == {"auto": "auto", "hell": "light", "dunkel": "dark"}[name[6:]]
        return bool(self.werte["an"].get(name, False))

    def schalten(self, name, wert=None):
        an = (not self.werte["an"].get(name, False)) if wert is None else wert
        self.werte["an"][name] = an
        self.band_auffrischen()
        return an

    def band_auffrischen(self):
        self.band.auffrischen()
        if hasattr(self, "schreibhilfe"):
            self.schreibhilfe.marken_auffrischen()

    # ============================================================= Aufbau
    def _baue_aktionen(self):
        a = Gio.SimpleAction.new("befehl", GLib.VariantType.new("s"))
        a.connect("activate", self._befehl_aktion)
        self.add_action(a)
        befehle.alle_laden()
        menues.haupt_menue()                 # füllt menues.TASTEN — erst danach lassen sich Kürzel anmelden
        for kennung, tasten in menues.TASTEN.items():
            self.get_application().set_accels_for_action("win.befehl('%s')" % kennung, tasten)

    def _befehl_aktion(self, _a, param):
        name, _, arg = param.get_string().partition("|")
        try:
            arg = json.loads(arg) if arg else None
        except ValueError:
            pass
        befehle.ausfuehren(self, name, arg)

    def hell_dunkel_anwenden(self):
        m = Adw.StyleManager.get_default()
        thema = self.werte.get("thema", "dark")
        m.set_color_scheme({"auto": Adw.ColorScheme.DEFAULT, "light": Adw.ColorScheme.FORCE_LIGHT,
                            "dark": Adw.ColorScheme.FORCE_DARK}.get(thema, Adw.ColorScheme.FORCE_DARK))
        dunkel = m.get_dark()
        self.remove_css_class("lunivo-dunkel")
        self.remove_css_class("hell")
        self.add_css_class("lunivo-dunkel" if dunkel else "hell")

    def _icon_knopf(self, sym, tipp, bef, groesse=18, kurz=None):
        b = Gtk.Button()
        b.add_css_class("flat")
        b.set_child(symbole.Symbol(sym, groesse) if symbole.gibt_es(sym) else Gtk.Label(label=kurz or tipp[:2]))
        b.set_tooltip_text(tipp)
        b.connect("clicked", lambda _b: befehle.ausfuehren(self, bef))
        return b

    def _baue_oberflaeche(self):
        # ---- Titelzeile: Name, Reiter, neuer Reiter
        kopf = Gtk.HeaderBar()
        kopf.add_css_class("titelzeile")
        logo = Gtk.Label(label="Lunivo-Office")
        logo.add_css_class("titel-logo")
        kopf.pack_start(logo)
        self.reiter = Adw.TabView()
        self.reiterleiste = Adw.TabBar()
        self.reiterleiste.set_view(self.reiter)
        self.reiterleiste.set_autohide(False)
        self.reiterleiste.set_expand_tabs(False)
        self.reiterleiste.set_hexpand(True)
        kopf.set_title_widget(self.reiterleiste)
        plus = Gtk.Button(icon_name="list-add-symbolic")
        plus.add_css_class("flat")
        plus.set_tooltip_text("Neues Dokument")
        plus.connect("clicked", lambda *_: self.neu())
        kopf.pack_start(plus)
        self.set_titlebar(kopf)

        haupt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(haupt)

        # ---- Zeile: Menü, Schnellzugriff, Reiter des Bandes, Schreibhilfe-Knopf
        self.band = ribbon.Band(self)
        zeile = Gtk.Box(spacing=2)
        zeile.add_css_class("register")
        self.menuknopf = Gtk.MenuButton()
        self.menuknopf.add_css_class("flat")
        self.menuknopf.set_label("☰  Menü")
        self.menue_tafel = menue_tafel.MenueTafel(self)
        self.menuknopf.set_popover(self.menue_tafel)
        zeile.append(self.menuknopf)
        zeile.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.schnell = Gtk.Box(spacing=0)
        self.schnellzugriff_neu()
        zeile.append(self.schnell)
        zeile.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.band.reiterleiste.set_hexpand(True)
        zeile.append(self.band.reiterleiste)
        self.schreibhilfe_knopf = self._icon_knopf("tafel", "Schreibhilfe", "tafel_zeigen", 16, "SH")
        self.schreibhilfe_knopf.add_css_class("blau-knopf")
        zeile.append(self.schreibhilfe_knopf)
        haupt.append(zeile)
        self.zeile_oben = zeile
        haupt.append(self.band.stapel)

        # ---- Mitte: linke Leiste | Navigation | Dokument | Schreibhilfe | rechte Leiste
        mitte = Gtk.Box()
        mitte.set_vexpand(True)
        links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        links.add_css_class("seitenleiste-schmal")
        for sym, tipp, bef in (("lupe", "Suchen", "suchen"), ("notiz", "Kommentare", "kommentar_liste"),
                               ("navigation", "Navigation", "navigation"), ("vorlesen", "Vorlesen", "vorlesen")):
            links.append(self._icon_knopf(sym, tipp, bef))
        mitte.append(links)

        # ---- Suchen und Ersetzen: Tafel in der linken Seitenleiste
        self.suchleiste = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.suchleiste.add_css_class("navigation")
        self.suchleiste.set_size_request(240, -1)
        self.suchleiste.set_hexpand(False)
        self.suchleiste.set_halign(Gtk.Align.START)
        for r in ("start", "end", "top", "bottom"):
            getattr(self.suchleiste, "set_margin_" + r)(0)
        self.suchleiste.set_search_mode = self.suchleiste.set_visible
        kopf_s = Gtk.Box(spacing=6)
        titel = Gtk.Label(label="Suchen und Ersetzen", xalign=0, hexpand=True)
        titel.set_margin_start(10)
        titel.set_margin_top(8)
        zu = Gtk.Button(icon_name="window-close-symbolic")
        zu.add_css_class("flat")
        zu.connect("clicked", lambda *_: self.suchleiste.set_visible(False))
        kopf_s.append(titel)
        kopf_s.append(zu)
        self.suchleiste.append(kopf_s)
        self.such_feld = Gtk.SearchEntry(placeholder_text="Suchen")
        self.ersetz_feld = Gtk.Entry(placeholder_text="Ersetzen durch")
        self.gross_knopf = Gtk.CheckButton(label="Groß-/Kleinschreibung beachten")
        self.ganz_knopf = Gtk.CheckButton(label="Nur ganze Wörter")
        for x in (self.such_feld, self.ersetz_feld):
            x.set_margin_start(10)
            x.set_margin_end(10)
            x.set_width_chars(10)
            x.set_max_width_chars(10)
        self.suchleiste.append(self.such_feld)
        self.suchleiste.append(self.ersetz_feld)
        zeile2 = Gtk.Box(spacing=6)
        zeile2.set_margin_start(10)
        zeile2.set_margin_end(10)
        self.such_stand = Gtk.Label(label="", xalign=0, hexpand=True)
        self.such_stand.add_css_class("dim-label")
        zeile2.append(self.such_stand)
        for sym, fn in (("go-up-symbolic", lambda *_: self._suchen(False)), ("go-down-symbolic", lambda *_: self._suchen(True))):
            kn = Gtk.Button(icon_name=sym)
            kn.connect("clicked", fn)
            zeile2.append(kn)
        self.suchleiste.append(zeile2)
        zeile3 = Gtk.Box(spacing=6)
        zeile3.set_margin_start(10)
        for text, fn in (("Ersetzen", lambda *_: self._ersetzen()), ("Alle ersetzen", lambda *_: self._alle_ersetzen())):
            kn = Gtk.Button(label=text)
            kn.connect("clicked", fn)
            zeile3.append(kn)
        self.suchleiste.append(zeile3)
        for c in (self.gross_knopf, self.ganz_knopf):
            c.set_margin_start(10)
            c.connect("toggled", lambda *_: self._such_stand_zeigen())
            self.suchleiste.append(c)
        self.such_feld.connect("activate", lambda *_: self._suchen(True))
        self.such_feld.connect("search-changed", lambda *_: (self._suchen(True, behalte=True), self._such_stand_zeigen()))
        esc = Gtk.EventControllerKey()
        esc.connect("key-pressed", lambda c, k, *_: (self.suchleiste.set_visible(False), True)[1] if k == 0xff1b else False)
        self.suchleiste.add_controller(esc)
        self.suchleiste.set_visible(False)
        mitte.append(self.suchleiste)
        self.navigation = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.navigation.add_css_class("navigation")
        self.navigation.set_size_request(240, -1)
        self.nav_liste = Gtk.ListBox()
        self.nav_liste.connect("row-activated", self._navigation_gewaehlt)
        rolle = Gtk.ScrolledWindow(vexpand=True)
        rolle.set_child(self.nav_liste)
        kopfl = Gtk.Label(label="Gliederung", xalign=0)
        kopfl.set_margin_start(10)
        kopfl.set_margin_top(8)
        self.navigation.append(kopfl)
        self.navigation.append(rolle)
        self.navigation.set_visible(False)
        self._nav_ziele = []
        mitte.append(self.navigation)
        self.teiler = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.teiler.set_hexpand(True)
        self.teiler.set_start_child(self.reiter)
        self.teiler.set_resize_start_child(True)
        self.teiler.set_shrink_start_child(False)
        self.schreibhilfe = Schreibhilfe(self)
        self.seitenleiste = self.schreibhilfe
        self.tafeln = Gtk.Box()                       # rechts: Schreibhilfe und (bei Bedarf) KI-Chat
        self.tafeln.append(self.schreibhilfe)
        self.teiler.set_end_child(self.tafeln)
        self.teiler.set_resize_end_child(False)
        self.teiler.set_shrink_end_child(False)
        mitte.append(self.teiler)
        rechts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rechts.add_css_class("seitenleiste-schmal")
        for sym, tipp, bef in (("chat", "KI-Chat", "chat_umschalten"), ("tafel", "Schreibhilfe", "tafel_zeigen")):
            rechts.append(self._icon_knopf(sym, tipp, bef))
        mitte.append(rechts)
        haupt.append(mitte)
        self.seitenleiste.set_visible(self.werte["schreibhilfe"])

        # ---- Statuszeile
        status = Gtk.Box(spacing=14)
        self.status_leiste = status
        status.add_css_class("statuszeile")
        self.status_links = Gtk.Label(label="Noch nicht geprüft.", xalign=0, hexpand=True)
        self.status_links.set_margin_start(12)
        self.status_zaehler = Gtk.Label(label="0 Wörter, 0 Zeichen")
        self.status_seite = Gtk.Label(label="Seite 1 von 1")
        status.append(self.status_links)
        status.append(self.status_zaehler)
        status.append(self.status_seite)
        for sym, tipp, bef in (("blattansicht", "Drucklayout", "layout"), ("gliederung", "Gliederung", "gliederung"),
                               ("fortlaufend", "Weblayout", "layout_web")):
            status.append(self._icon_knopf(sym, tipp, bef, 14, tipp[:1]))
        b = Gtk.Button(icon_name="view-fullscreen-symbolic")
        b.add_css_class("flat")
        b.set_tooltip_text("Vollbild")
        b.connect("clicked", lambda *_: self.fullscreen() if not self.is_fullscreen() else self.unfullscreen())
        status.append(b)
        minus = Gtk.Button(label="−")
        minus.add_css_class("flat")
        minus.connect("clicked", lambda *_: befehle.ausfuehren(self, "kleiner"))
        self.zoom_regler = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 40, 300, 5)
        self.zoom_regler.set_size_request(120, -1)
        self.zoom_regler.set_draw_value(False)
        self.zoom_regler.set_value(100)
        self.zoom_regler.connect("value-changed", self._zoom_regler)
        plusz = Gtk.Button(label="+")
        plusz.add_css_class("flat")
        plusz.connect("clicked", lambda *_: befehle.ausfuehren(self, "groesser"))
        self.status_zoom = Gtk.Label(label="100 %")
        self.status_zoom.set_width_chars(6)
        self.status_zoom.set_margin_end(12)
        for w in (minus, self.zoom_regler, plusz, self.status_zoom):
            status.append(w)
        haupt.append(status)

        css = Gtk.CssProvider()
        css.load_from_string(STYLE)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Adw.StyleManager.get_default().connect("notify::dark", lambda *_: self.hell_dunkel_anwenden())
        self.get_application().set_menubar(menues.haupt_menue())      # nur sichtbar, wenn die Menüleiste an ist
        self.set_show_menubar(self.werte["an"].get("menueleiste", False))
        self.schnell.set_visible(self.werte["an"].get("leisten", True) is not False)

    def bedienung_skalieren(self, prozent):
        """„Schrift der Bedienung“: Menüs, Leisten und Statuszeile (80 … 180 %)."""
        self.werte["bedienung"] = prozent
        if getattr(self, "_bedienung_css", None) is None:
            self._bedienung_css = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self._bedienung_css,
                                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
        px = 15.6 * prozent / 100.0
        self._bedienung_css.load_from_string(
            ".lunivo-dunkel, .hell { font-size: %.1fpx; } .knopfname { font-size: %.1fpx; } .gruppenname { font-size: %.1fpx; }"
            % (px, px * 0.92, px * 0.75))

    def schnellzugriff_neu(self):
        kind = self.schnell.get_first_child()
        while kind:
            n = kind.get_next_sibling()
            self.schnell.remove(kind)
            kind = n
        tabelle = {"neu": ("neu", "Neu"), "oeffnen": ("oeffnen", "Öffnen"), "speichern": ("speichern", "Speichern"),
                   "speichern_pdf": ("pdf", "Als PDF exportieren"),
                   "drucken": ("drucken", "Drucken"), "vorschau": ("vorschau", "Druckvorschau"),
                   "rueckgaengig": ("zurueck", "Rückgängig"), "wiederholen": ("vor", "Wiederholen"),
                   "pruefen": ("haken", "Prüfen"), "fett": (None, "Fett"), "kursiv": (None, "Kursiv"),
                   "suchen": ("lupe", "Suchen")}
        for bef in self.werte.get("schnellzugriff", ["oeffnen", "speichern", "speichern_pdf", "drucken", "vorschau",
                                                      "rueckgaengig", "wiederholen"]):
            if bef in tabelle:
                sym, tipp = tabelle[bef]
                self.schnell.append(self._icon_knopf(sym or "", tipp, bef, 16, tipp[:1]))

    # ============================================================= Dokumente
    def seite_hinzufuegen(self, dok):
        seite = self.reiter.append(dok)
        seite.set_title(dok.anzeigename())
        dok._seite = seite
        dok.connect("geaendert", lambda d: self._titel_auffrischen(d))
        dok.connect("format-stand", lambda d: d is self.dok() and self._format_zeigen())
        dok.zoom_setzen(self.werte.get("zoom", 85))
        self.dokument_einrichten(dok)
        self.reiter.set_selected_page(seite)
        dok.ansicht.grab_focus()
        self._titel_auffrischen(dok)
        return dok

    def dokument_einrichten(self, d):
        """Ein Dokument bekommt die gerade gültigen Schalter (Rechtschreibung, Lineal …)."""
        an = self.werte["an"]
        if an.get("rechtschreibung"):
            d.rechtschreibung(True, self.werte.get("sprache", "de_DE"), self.werte.get("eigene_woerter", []))
        d.autokorrektur_an = bool(an.get("autokorrektur"))
        d.vorhersage_an = bool(an.get("vorhersage"))
        d.verfolgen_an = bool(an.get("verfolgen"))
        d.lineal_zeigen(bool(an.get("lineal")))
        d.lineal_hoch_zeigen(bool(an.get("lineal_hoch")))
        d.netz_zeigen(bool(an.get("netzlinien")))
        d.begrenzungen_zeigen(bool(an.get("textbegrenzungen")))
        d.layout_setzen(self.werte.get("layout", "blatt"))
        if self.werte.get("lesehilfe"):
            from .befehle.schreibhilfe_tab import lesehilfe_anwenden
            lesehilfe_anwenden(self, d)
        if an.get("zeilenfokus"):
            from .befehle.schreibhilfe_tab import _fokus_verdrahten, _fokus_aktualisieren
            _fokus_verdrahten(d)
            d.fokus_an = True
            _fokus_aktualisieren(d)
        if self.werte.get("rand_standard"):
            d.seite["rand"].update(self.werte["rand_standard"])
            d.seite_anwenden()

    def neu(self, *_):
        d = editor.Dokument(self.werte["schriftart"], self.werte["groesse"])
        n = sum(1 for x in self.alle_dokumente() if not x.pfad) + 1
        d.titel = "Unbenannt %d" % n
        return self.seite_hinzufuegen(d)

    def datei_oeffnen(self, pfad, kennwort=None):
        for d in self.alle_dokumente():
            if d.pfad == pfad:
                self.reiter.set_selected_page(d._seite)
                return d
        d = editor.Dokument(self.werte["schriftart"], self.werte["groesse"])
        try:
            self.status("Öffne %s …" % os.path.basename(pfad))
            d.laden(pfad, kennwort)
        except krypto.KennwortNoetig:
            from .befehle import hilfen

            def ok(v):
                try:
                    self.datei_oeffnen(pfad, v[0])
                except Exception:
                    pass
            hilfen.frage(self, "Geschütztes Dokument", [("Kennwort", "")], ok,
                         "Dieses Dokument ist mit einem Kennwort verschlüsselt.", "Öffnen")
            return None
        except krypto.KennwortFalsch:
            self.meldung("Falsches Kennwort", "Das Dokument bleibt verschlossen.")
            return None
        except Exception as e:
            self.meldung("Das Öffnen hat nicht geklappt", str(e))
            return None
        self.seite_hinzufuegen(d)
        self.zuletzt_merken(pfad)
        self.status("Geöffnet: %s" % pfad)
        return d

    def zuletzt_merken(self, pfad):
        z = [p for p in self.werte.get("zuletzt", []) if p != pfad]
        self.werte["zuletzt"] = ([pfad] + z)[:12]

    def _titel_auffrischen(self, d):
        if not hasattr(d, "_seite"):
            return
        d._seite.set_title(("● " if d.geaendert else "") + d.anzeigename())
        if d is self.dok():
            self._titel_fenster()
            self._zaehler()

    def _titel_fenster(self):
        d = self.dok()
        self.set_title(("%s%s — Lunivo-Office" % ("*" if d.geaendert else "", d.anzeigename())) if d else "Lunivo-Office")

    def _zaehler(self):
        d = self.dok()
        if d:
            t = d.text()
            self.status_zaehler.set_text("%d Wörter, %d Zeichen" % (len(t.split()), len(t)))
            self.status_zoom.set_text("%d %%" % d.zoom)
            self.status_seite.set_text("Seite %d von %d" % d.seite_stand())
            self.zoom_regler.handler_block_by_func(self._zoom_regler)
            self.zoom_regler.set_value(d.zoom)
            self.zoom_regler.handler_unblock_by_func(self._zoom_regler)
            if self.navigation.get_visible():
                self.navigation_auffrischen()

    def _dokument_gewechselt(self):
        self.schreibhilfe.marken_auffrischen()
        self._titel_fenster()
        self._zaehler()
        self._format_zeigen()
        self.schreibhilfe.leeren()
        return False

    def _zoom_regler(self, regler):
        d = self.dok()
        if d and int(regler.get_value()) != d.zoom:
            d.zoom_setzen(int(regler.get_value()))
            self.werte["zoom"] = d.zoom
            self.status_zoom.set_text("%d %%" % d.zoom)

    # ------------------------------------------------------------ Schließen
    def tab_schliessen(self, d=None):
        d = d or self.dok()
        if d:
            self.reiter.close_page(d._seite)

    def _seite_schliessen(self, ansicht, seite):
        d = seite.get_child()
        if d.geaendert:
            def weiter():
                d.puffer.set_modified(False)
                self.reiter.close_page_finish(seite, True)
                self._mindestens_eins()

            def abbruch():
                self.reiter.close_page_finish(seite, False)
            self.frage_speichern(d, weiter, abbruch)
            return True
        GLib.idle_add(self._mindestens_eins)
        return False

    def _mindestens_eins(self):
        if self.reiter.get_n_pages() == 0:
            self.neu()
        return False

    def frage_speichern(self, d, weiter, abbruch=None):
        dlg = Gtk.AlertDialog()
        dlg.set_message("„%s“ speichern?" % d.anzeigename())
        dlg.set_detail("Ihre Änderungen gehen sonst verloren.")
        dlg.set_buttons(["Abbrechen", "Nicht speichern", "Speichern"])
        dlg.set_cancel_button(0)
        dlg.set_default_button(2)

        def fertig(dlg, res):
            try:
                wahl = dlg.choose_finish(res)
            except GLib.Error:
                wahl = 0
            if wahl == 1:
                weiter()
            elif wahl == 2:
                self.reiter.set_selected_page(d._seite)
                befehle.ausfuehren(self, "speichern_dann", weiter)
            elif abbruch:
                abbruch()
        dlg.choose(self, None, fertig)

    def _schliessen_angefragt(self, *_):
        for d in self.alle_dokumente():
            if d.geaendert:
                self.reiter.set_selected_page(d._seite)

                def weiter(d=d):
                    d.puffer.set_modified(False)
                    self.close()
                self.frage_speichern(d, weiter)
                return True
        self.werte["fenster"] = [self.get_width(), self.get_height()]
        self.werte["schreibhilfe"] = self.seitenleiste.get_visible()
        self.werte["offen"] = [d.pfad for d in self.alle_dokumente() if d.pfad]
        einstellungen.schreiben(self.werte)
        self.entwuerfe_loeschen()
        return False

    # ============================================================= Entwürfe gegen Absturz
    def _entwurfsordner(self):
        o = os.path.join(pfade.DATEN, "entwuerfe")
        os.makedirs(o, exist_ok=True)
        return o

    def _autosicherung(self):
        import time
        wann = self.werte.get("opt", {}).get("sicherung|Wann gesichert wird", "In festen Abständen")
        if wann == "Beim Schließen":
            return True
        minuten = 0.15 if wann.startswith("Laufend") else self.werte.get("opt", {}).get("sicherung|Abstand (Minuten)", 5)
        if time.time() - self._letzte_sicherung < minuten * 60:
            return True
        self._letzte_sicherung = time.time()
        for i, d in enumerate(self.alle_dokumente()):
            if not d.geaendert:
                continue
            try:
                from . import html_io
                inhalt = html_io.puffer_in_html(d.puffer, d.anzeigename(), d.meta_aktuell())
                meta = {"pfad": d.pfad, "titel": d.titel}
                base = os.path.join(self._entwurfsordner(), "%d-%d" % (os.getpid(), i))
                with open(base + ".html", "w", encoding="utf-8") as fh:
                    fh.write(inhalt)
                with open(base + ".json", "w", encoding="utf-8") as fh:
                    json.dump(meta, fh)
            except Exception:
                pass
        return True

    def entwuerfe_loeschen(self):
        o = self._entwurfsordner()
        for n in os.listdir(o):
            if n.startswith("%d-" % os.getpid()):
                try:
                    os.remove(os.path.join(o, n))
                except OSError:
                    pass

    # ============================================================= Bearbeiten
    def zwischenablage(self, was):
        d = self.dok()
        if not d:
            return
        cb = self.get_clipboard()
        if was == "copy":
            d.puffer.copy_clipboard(cb)
        elif was == "cut":
            d.puffer.cut_clipboard(cb, d.ansicht.get_editable())
        else:
            d.puffer.paste_clipboard(cb, None, d.ansicht.get_editable())

    def suchleiste_zeigen(self, ersetzen=False):
        self.suchleiste.set_visible(True)
        self.such_feld.grab_focus()
        d = self.dok()
        if d:
            sel = d.puffer.get_selection_bounds()
            if sel and "\n" not in d.puffer.get_text(*sel, False):
                self.such_feld.set_text(d.puffer.get_text(*sel, False))
        if ersetzen and self.such_feld.get_text():
            self.ersetz_feld.grab_focus()

    def _such_stand_zeigen(self):
        d = self.dok()
        m = self.such_feld.get_text()
        if not d or not m:
            self.such_stand.set_text("")
            return
        n = d.treffer_zaehlen(m, self.gross_knopf.get_active(), self.ganz_knopf.get_active())
        self.such_stand.set_text("%d Treffer" % n if n else "Keine Suchergebnisse")

    def _suchen(self, vorwaerts, behalte=False):
        d = self.dok()
        if not d:
            return
        muster = self.such_feld.get_text()
        if behalte:
            sel = d.puffer.get_selection_bounds()
            if sel:
                d.puffer.place_cursor(sel[0])
        if muster and not d.suchen(muster, vorwaerts, self.gross_knopf.get_active(), self.ganz_knopf.get_active()):
            self.status("„%s“ nicht gefunden." % muster)

    def _ersetzen(self):
        d = self.dok()
        if d:
            d.ersetzen(self.such_feld.get_text(), self.ersetz_feld.get_text(), self.gross_knopf.get_active(), self.ganz_knopf.get_active())

    def _alle_ersetzen(self):
        d = self.dok()
        if d:
            n = d.alle_ersetzen(self.such_feld.get_text(), self.ersetz_feld.get_text(), self.gross_knopf.get_active(), self.ganz_knopf.get_active())
            self.status("%d Stellen ersetzt." % n)

    # ============================================================= Format-Felder im Band
    def schrift_gewaehlt(self, *_):
        if self._format_sperre:
            return
        d = self.dok()
        if d:
            d.wert_setzen("fam:", "fam:" + self.familien[self.schrift_wahl.get_selected()])

    def stil_gewaehlt(self, *_):
        if self._format_sperre:
            return
        d = self.dok()
        if d:
            d.stil_setzen(self.stil_namen[self.stil_wahl.get_selected()])
            d.ansicht.grab_focus()

    def groesse_gewaehlt(self, *_):
        if self._format_sperre:
            return
        from .befehle.start import SCHRIFTGROESSEN
        d = self.dok()
        if d:
            d.wert_setzen("size:", "size:" + SCHRIFTGROESSEN[self.groesse_wahl.get_selected()])

    def _format_zeigen(self):
        d = self.dok()
        if not d:
            return
        self._format_sperre = True
        try:
            from .befehle.start import SCHRIFTGROESSEN
            if hasattr(self, "schrift_wahl"):
                fam = next((t[4:] for t in d.tippen if t.startswith("fam:")), d.vorgabe_schrift)
                if fam in self.familien:
                    self.schrift_wahl.set_selected(self.familien.index(fam))
                gr = next((t[5:] for t in d.tippen if t.startswith("size:")), str(d.vorgabe_groesse))
                gr = gr[:-2] if gr.endswith(".0") else gr
                if gr in SCHRIFTGROESSEN:
                    self.groesse_wahl.set_selected(SCHRIFTGROESSEN.index(gr))
            if hasattr(self, "stil_wahl"):
                namen = list(self.stil_namen[:10]) if False else None
                from .befehle.start import STIL_NAMEN
                alle = list(STIL_NAMEN) + sorted(d.eigene_stile())
                if alle != self.stil_namen:
                    self.stil_namen = alle
                    self.stil_wahl.set_model(Gtk.StringList.new(alle))
                aktuell = d.stil_am_cursor()
                if aktuell in self.stil_namen:
                    self.stil_wahl.set_selected(self.stil_namen.index(aktuell))
            self.band.auffrischen()
            self.band.kontext_setzen(d.kontexte())
            if hasattr(self, "stil_knoepfe"):
                aktuell = d.stil_am_cursor()
                for n, b in self.stil_knoepfe.items():
                    (b.add_css_class if n == aktuell else b.remove_css_class)("suggested-action")
        finally:
            self._format_sperre = False

    # ============================================================= Navigation
    def navigation_auffrischen(self):
        d = self.dok()
        kind = self.nav_liste.get_first_child()
        while kind:
            n = kind.get_next_sibling()
            self.nav_liste.remove(kind)
            kind = n
        self._nav_ziele = []
        if not d:
            return
        for nr in range(d.puffer.get_line_count()):
            _, von = d.puffer.get_iter_at_line(nr)
            tags = {t.props.name for t in von.get_tags()}
            ebene = next((int(t[1]) for t in tags if t in ("h1", "h2", "h3")), 0)
            if "st:Titel" in tags:
                ebene = 1
            if not ebene:
                continue
            ende = von.copy()
            if not ende.ends_line():
                ende.forward_to_line_end()
            text = d.puffer.get_text(von, ende, False).strip()
            if not text:
                continue
            zeile = Gtk.ListBoxRow()
            l = Gtk.Label(label=text, xalign=0)
            l.set_margin_start(8 + (ebene - 1) * 14)
            l.set_margin_top(4)
            l.set_margin_bottom(4)
            zeile.set_child(l)
            self.nav_liste.append(zeile)
            self._nav_ziele.append(nr)

    def _navigation_gewaehlt(self, liste, zeile):
        d = self.dok()
        if d and zeile is not None and zeile.get_index() < len(self._nav_ziele):
            nr = self._nav_ziele[zeile.get_index()]
            _, it = d.puffer.get_iter_at_line(nr)
            d.puffer.place_cursor(it)
            d.ansicht.scroll_to_iter(it, 0.1, True, 0, 0.1)
            d.ansicht.grab_focus()
