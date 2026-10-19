"""Reiter Ansicht: Zoom, Helligkeit, Anzeigen, Fenster."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Adw  # noqa: E402

from . import befehl, hilfen


def _zoom(w, wert):
    d = w.dok()
    if d:
        d.zoom_setzen(wert)
        w.werte["zoom"] = d.zoom
        w._zaehler()


@befehl("groesser")
def _groesser(w, _=None):
    d = w.dok()
    if d:
        _zoom(w, d.zoom + 10)


@befehl("kleiner")
def _kleiner(w, _=None):
    d = w.dok()
    if d:
        _zoom(w, d.zoom - 10)


@befehl("normal")
def _normal(w, _=None):
    _zoom(w, 100)


@befehl("zoom_breite")
def _breite(w, _=None):
    d = w.dok()
    if d:
        verfuegbar = max(w.reiter.get_width() - 60, 300)
        _zoom(w, int(verfuegbar * 100 / 794))


@befehl("zoom_seite")
def _seite(w, _=None):
    d = w.dok()
    if d:
        hoehe = max(w.reiter.get_height() - 40, 300)
        _zoom(w, int(hoehe * 100 / (794 * 297 / 210)))


@befehl("zoom_stufe")
def _stufe(w, _=None):
    d = w.dok()
    if d:
        hilfen.frage(w, "Zoom", [("Prozent", d.zoom)], lambda v: _zoom(w, int(hilfen.zahl(v[0], 100))))


@befehl("thema")
def _thema(w, art=None):
    w.werte["thema"] = art or "dark"
    w.hell_dunkel_anwenden()
    w.band_auffrischen()


@befehl("navigation")
def _navigation(w, _=None):
    w.navigation.set_visible(not w.navigation.get_visible())
    if w.navigation.get_visible():
        w.navigation_auffrischen()
    w.band_auffrischen()


@befehl("menueleiste_zeigen")
def _menueleiste(w, _=None):
    w.set_show_menubar(not w.get_show_menubar())
    w.werte["an"]["menueleiste"] = w.get_show_menubar()
    w.band_auffrischen()


@befehl("leisten_zeigen")
def _leisten(w, _=None):
    w.schnell.set_visible(not w.schnell.get_visible())
    w.werte["an"]["leisten"] = w.schnell.get_visible()
    w.band_auffrischen()


# ================================================================ Dokumentansichten
@befehl("layout")
def _layout(w, art="blatt"):
    art = art or "blatt"
    d = w.dok()
    if not d:
        return
    w.werte["layout"] = art
    for x in w.alle_dokumente():
        x.layout_setzen(art)
    w.status({"blatt": "Drucklayout", "doppelt": "Zwei Seiten nebeneinander", "web": "Weblayout"}.get(art, art))


@befehl("layout_web")
def _layout_web(w, _=None):
    _layout(w, "web")


@befehl("gliederung")
def _gliederung(w, _=None):
    if not w.navigation.get_visible():
        w.navigation.set_visible(True)
    w.navigation_auffrischen()
    w.band_auffrischen()
    w.status("Gliederung: Überschriften anklicken, um dorthin zu springen.")


# ================================================================ Anzeigen
@befehl("lineal_zeigen")
def _lineal(w, _=None):
    an = w.schalten("lineal")
    for d in w.alle_dokumente():
        d.lineal_zeigen(an)


@befehl("lineal_hoch_zeigen")
def _lineal_hoch(w, _=None):
    an = w.schalten("lineal_hoch")
    for d in w.alle_dokumente():
        d.lineal_hoch_zeigen(an)


@befehl("netzlinien")
def _netz(w, _=None):
    an = w.schalten("netzlinien")
    for d in w.alle_dokumente():
        d.netz_zeigen(an)


@befehl("marken_zeigen")
def _marken(w, _=None):
    an = w.schalten("textbegrenzungen")
    for d in w.alle_dokumente():
        d.begrenzungen_zeigen(an)


# ================================================================ Fenster
@befehl("neues_fenster")
def _neues_fenster(w, _=None):
    from ..fenster import Fenster
    f = Fenster(w.get_application(), w.werte)
    f.present()
    f.neu()


def _eigene_fenster(w):
    app = w.get_application()
    return [x for x in app.get_windows() if hasattr(x, "reiter")]


def _anordnen(w, wie):
    fenster = _eigene_fenster(w)
    anzeige = Gdk.Display.get_default()
    mon = anzeige.get_monitors().get_item(0)
    g = mon.get_geometry()
    n = len(fenster)
    import shutil
    import subprocess
    if shutil.which("wmctrl") is None:
        return w.meldung("Fenster anordnen", "wmctrl ist nicht installiert (sudo apt install wmctrl).")
    if n < 2:
        return w.status("Nur ein Fenster geöffnet – öffnen Sie mit Ansicht ▸ Neues Fenster ein zweites.")
    if wie == "neben":
        zellen = [(i * g.width // n, 0, g.width // n, g.height) for i in range(n)]
    elif wie == "unter":
        zellen = [(0, i * g.height // n, g.width, g.height // n) for i in range(n)]
    else:
        spalten = 2 if n <= 4 else 3
        zeilen = -(-n // spalten)
        zellen = [((i % spalten) * g.width // spalten, (i // spalten) * g.height // zeilen, g.width // spalten, g.height // zeilen)
                  for i in range(n)]
    for f, (x, y, b, h) in zip(fenster, zellen):
        titel = f.get_title()
        subprocess.run(["wmctrl", "-r", titel, "-b", "remove,maximized_vert,maximized_horz"], capture_output=True)
        subprocess.run(["wmctrl", "-r", titel, "-e", "0,%d,%d,%d,%d" % (x, y + 28, b - 8, h - 36)], capture_output=True)


@befehl("fenster_nebeneinander")
def _f_neben(w, _=None):
    _anordnen(w, "neben")


@befehl("fenster_untereinander")
def _f_unter(w, _=None):
    _anordnen(w, "unter")


@befehl("fenster_kacheln")
def _f_kacheln(w, _=None):
    _anordnen(w, "kacheln")


@befehl("fenster_liste")
def _f_liste(w, _=None):
    fenster = _eigene_fenster(w)
    dlg = Gtk.AlertDialog()
    dlg.set_message("Fensterliste")
    dlg.set_buttons([f.get_title() for f in fenster[:7]] + ["Schließen"])
    dlg.set_cancel_button(len(fenster[:7]))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except Exception:
            return
        if n < len(fenster[:7]):
            fenster[n].present()
    dlg.choose(w, None, fertig)


# ================================================================ Oberfläche
@befehl("register_anpassen")
def _register_anpassen(w, _=None):
    from .. import ribbon_daten
    dlg = Gtk.Window(transient_for=w, modal=True, title="Register anpassen")
    dlg.set_default_size(420, 460)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Welche Reiter sollen im Band stehen? (Wirkt sofort.)", xalign=0))
    versteckt = set(w.werte.setdefault("reiter_aus", []))
    for name, _g in ribbon_daten.SPEC:
        if name not in w.band.reiter_knoepfe:
            continue
        c = Gtk.CheckButton(label=name, active=name not in versteckt)

        def umschalten(btn, name=name):
            if btn.get_active():
                versteckt.discard(name)
            else:
                versteckt.add(name)
            w.werte["reiter_aus"] = sorted(versteckt)
            w.band.reiter_knoepfe[name].set_visible(btn.get_active())
            if not btn.get_active() and w.band.stapel.get_visible_child_name() == name:
                erster = next((n for n in w.band.reiter_knoepfe if n not in versteckt), None)
                if erster:
                    w.band.zeige(erster)
        c.connect("toggled", umschalten)
        box.append(c)
    ok = Gtk.Button(label="Fertig")
    ok.connect("clicked", lambda *_: dlg.close())
    box.append(ok)
    dlg.present()


@befehl("symbol_tauschen")
def _symbol_tauschen(w, _=None):
    from .. import symbole
    dlg = Gtk.Window(transient_for=w, modal=True, title="Symbol austauschen")
    dlg.set_default_size(460, 300)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Eigenen Strichzeichnungs-Pfad (SVG-Pfad im Feld 24 × 24) für ein Symbol festlegen.", xalign=0, wrap=True))
    name = Gtk.Entry(placeholder_text="Symbolname, z. B. kleben")
    pfad = Gtk.Entry(placeholder_text="M12 2 L22 12 L12 22 L2 12 Z")
    box.append(name)
    box.append(pfad)

    def ok(*_):
        n, p = name.get_text().strip(), pfad.get_text().strip()
        if n and p:
            symbole._PFADE[n] = p
            w.werte.setdefault("symbole_eigen", {})[n] = p
            symbole.alle_auffrischen()
            dlg.close()
    b = Gtk.Button(label="Übernehmen")
    b.add_css_class("suggested-action")
    b.connect("clicked", ok)
    box.append(b)
    dlg.present()


@befehl("benutzeroberflaeche")
def _benutzeroberflaeche(w, _=None):
    from .datei import _optionen
    _optionen(w, "ansicht")


@befehl("vorlagen_zurueck")
def _vorlagen_zurueck(w, _=None):
    dlg = Gtk.AlertDialog()
    dlg.set_message("Oberfläche zurücksetzen?")
    dlg.set_detail("Reiter, Schnellzugriff, Menüleiste und Helligkeit gehen auf den Auslieferungszustand zurück. Ihre Dokumente bleiben unberührt.")
    dlg.set_buttons(["Abbrechen", "Zurücksetzen"])
    dlg.set_cancel_button(0)

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except Exception:
            return
        if n == 1:
            for k in ("reiter_aus", "thema", "lesehilfe"):
                w.werte.pop(k, None)
            w.werte["an"].pop("menueleiste", None)
            w.werte["an"].pop("leisten", None)
            w.set_show_menubar(False)
            w.schnell.set_visible(True)
            for n_, b in w.band.reiter_knoepfe.items():
                b.set_visible(True)
            w.hell_dunkel_anwenden()
            w.band_auffrischen()
            w.status("Oberfläche zurückgesetzt.")
    dlg.choose(w, None, fertig)
