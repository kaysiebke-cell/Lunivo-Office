"""Kleine Bausteine für Befehle: Dialoge, Farbwahl, Auswahllisten."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

FARBEN = [
    "#000000", "#434343", "#666666", "#999999", "#CCCCCC", "#FFFFFF",
    "#B5563F", "#E06666", "#F6B26B", "#FFD966", "#93C47D", "#76A5AF",
    "#6FA8DC", "#8E7CC3", "#C27BA0", "#CC0000", "#E69138", "#F1C232",
    "#6AA84F", "#45818E", "#3D85C6", "#674EA7", "#A64D79", "#7F6000",
]
HELLE = ["#FFFF00", "#00FF00", "#00FFFF", "#FF00FF", "#FFD966", "#B6D7A8", "#A4C2F4", "#EA9999", "#D9D2E9", "#FCE5CD"]


THEMA = ["#FFFFFF", "#000000", "#E7E6E6", "#44546A", "#ED7D31", "#A5282C", "#1F4E79", "#548235", "#7030A0", "#BF9000"]
STANDARD = ["#C00000", "#FF0000", "#FFC000", "#FFFF00", "#92D050", "#00B050", "#00B0F0", "#0070C0", "#002060", "#7030A0"]


def _hex(c):
    return "#%02X%02X%02X" % (round(c.red * 255), round(c.green * 255), round(c.blue * 255))


def _abstufung(hex_, faktor):
    """Heller (faktor>0, zu Weiß) oder dunkler (faktor<0, zu Schwarz) — wie die Schattenreihen in WPS."""
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    if faktor >= 0:
        r, g, b = (round(x + (255 - x) * faktor) for x in (r, g, b))
    else:
        r, g, b = (round(x * (1 + faktor)) for x in (r, g, b))
    return "#%02X%02X%02X" % (r, g, b)


def _feld(farbe, pop, gewaehlt):
    feld = Gtk.Button()
    feld.add_css_class("farbfeld")
    css = Gtk.CssProvider()
    css.load_from_string("button { background: %s; min-width: 14px; min-height: 14px; padding: 0; border: 1px solid alpha(#888,0.5); border-radius: 0; }" % farbe)
    feld.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    feld.set_tooltip_text(farbe)
    feld.connect("clicked", lambda _b, f=farbe: (pop.popdown(), gewaehlt(f)))
    return feld


def farbwahl(pop, farben, gewaehlt, mit_keine=None, weitere="Weitere Farben …"):
    """Farbtafel wie in WPS: Keine Farbe · Thema-Farben mit Abstufungen · Standard-Farben · Weitere.
    gewaehlt(hex_oder_None) wird gerufen, dann schließt pop."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(8)
    if mit_keine:
        b = Gtk.Button(label=mit_keine)
        b.add_css_class("flat")
        b.get_child().set_xalign(0)
        b.connect("clicked", lambda *_: (pop.popdown(), gewaehlt(None)))
        box.append(b)
    wps = farben in (FARBEN, HELLE)
    if wps:
        kopf = Gtk.Label(label="Thema-Farben", xalign=0)
        kopf.add_css_class("dim-label")
        box.append(kopf)
        gitter = Gtk.Grid(row_spacing=2, column_spacing=2)
        for i, f in enumerate(THEMA):
            gitter.attach(_feld(f, pop, gewaehlt), i, 0, 1, 1)
        for zeile, faktor in enumerate((0.8, 0.6, 0.4, -0.25, -0.5), 1):
            for i, f in enumerate(THEMA):
                if f in ("#FFFFFF", "#000000"):
                    f = {0.8: "#F2F2F2", 0.6: "#D9D9D9", 0.4: "#BFBFBF", -0.25: "#A6A6A6", -0.5: "#7F7F7F"}[faktor] if f == "#FFFFFF" else \
                        {0.8: "#7F7F7F", 0.6: "#595959", 0.4: "#404040", -0.25: "#262626", -0.5: "#0D0D0D"}[faktor]
                else:
                    f = _abstufung(f, faktor)
                gitter.attach(_feld(f, pop, gewaehlt), i, zeile, 1, 1)
        box.append(gitter)
        kopf2 = Gtk.Label(label="Standard-Farben", xalign=0)
        kopf2.add_css_class("dim-label")
        box.append(kopf2)
        std = Gtk.Grid(column_spacing=2)
        for i, f in enumerate(STANDARD):
            std.attach(_feld(f, pop, gewaehlt), i, 0, 1, 1)
        box.append(std)
    else:
        gitter = Gtk.Grid(row_spacing=3, column_spacing=3)
        for i, f in enumerate(farben):
            gitter.attach(_feld(f, pop, gewaehlt), i % 5, i // 5, 1, 1)
        box.append(gitter)
    box.append(Gtk.Separator())
    andere = Gtk.Button(label=weitere)
    andere.add_css_class("flat")
    andere.get_child().set_xalign(0)

    def weiter(*_):
        pop.popdown()
        dlg = Gtk.ColorDialog()

        def fertig(d, res):
            try:
                c = d.choose_rgba_finish(res)
            except GLib.Error:
                return
            gewaehlt(_hex(c))
        dlg.choose_rgba(pop.get_root(), None, None, fertig)
    andere.connect("clicked", weiter)
    box.append(andere)
    return box


def liste(pop, eintraege):
    """eintraege: [(Beschriftung, Funktion)] oder '-'. Gibt ein Widget zurück."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.add_css_class("klappliste")
    for e in eintraege:
        if e == "-":
            box.append(Gtk.Separator())
            continue
        text, fn = e[0], e[1]
        b = Gtk.Button(label=text)
        b.add_css_class("flat")
        b.get_child().set_xalign(0)
        b.connect("clicked", lambda _b, fn=fn: (pop.popdown(), fn()))
        if len(e) > 2 and e[2]:
            b.set_tooltip_text(e[2])
        box.append(b)
    return box


def frage(fenster, titel, felder, ok, text="", okname="OK"):
    """Kleiner Dialog mit Eingabefeldern. felder: [(Name, Vorgabe)]; ok(werte_liste)."""
    dlg = Gtk.Window(transient_for=fenster, modal=True, title=titel)
    dlg.set_default_size(420, -1)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(16)
    if text:
        l = Gtk.Label(label=text, xalign=0, wrap=True)
        box.append(l)
    eingaben = []
    for name, vorgabe in felder:
        zeile = Gtk.Box(spacing=8)
        zeile.append(Gtk.Label(label=name, xalign=0, width_chars=16))
        e = Gtk.Entry(text=str(vorgabe), hexpand=True)
        e.set_activates_default(True)
        zeile.append(e)
        box.append(zeile)
        eingaben.append(e)
    knoepfe = Gtk.Box(spacing=8, halign=Gtk.Align.END)
    abbrechen = Gtk.Button(label="Abbrechen")
    abbrechen.connect("clicked", lambda *_: dlg.close())
    gut = Gtk.Button(label=okname)
    gut.add_css_class("suggested-action")

    def los(*_):
        werte = [e.get_text() for e in eingaben]
        dlg.close()
        ok(werte)
    gut.connect("clicked", los)
    knoepfe.append(abbrechen)
    knoepfe.append(gut)
    box.append(knoepfe)
    dlg.set_child(box)
    dlg.set_default_widget(gut)
    dlg.present()
    if eingaben:
        eingaben[0].grab_focus()
    return dlg


def auswahl_fenster(fenster, titel, zeilen, ok, text="", okname="Anwenden"):
    """Dialog wie in der Vorlage: Beschriftung links, Auswahlliste oder Farbfeld rechts.
    zeilen: [(Name, "wahl", [Texte], index)] oder [(Name, "farbe", "#hex")]; ok(werte)."""
    dlg = Gtk.Window(transient_for=fenster, modal=True, title=titel)
    dlg.set_default_size(400, -1)
    dlg.set_resizable(False)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(18)
    kopf = Gtk.Label(label=titel, xalign=0)
    kopf.add_css_class("title-4")
    box.append(kopf)
    if text:
        box.append(Gtk.Label(label=text, xalign=0, wrap=True))
    felder = []
    for z in zeilen:
        zeile = Gtk.Box(spacing=8)
        zeile.append(Gtk.Label(label=z[0], xalign=0, width_chars=14))
        if z[1] == "wahl":
            f = Gtk.DropDown.new_from_strings(z[2])
            f.set_selected(z[3] if len(z) > 3 else 0)
            f.set_hexpand(True)
        else:
            f = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
            c = Gdk.RGBA()
            c.parse(z[2])
            f.set_rgba(c)
            f.set_halign(Gtk.Align.START)
            f.set_hexpand(True)
        zeile.append(f)
        box.append(zeile)
        felder.append((z[1], f))
    knoepfe = Gtk.Box(spacing=8, halign=Gtk.Align.END)
    abbrechen = Gtk.Button(label="Abbrechen")
    abbrechen.connect("clicked", lambda *_: dlg.close())
    gut = Gtk.Button(label=okname)
    gut.add_css_class("suggested-action")

    def los(*_):
        werte = []
        for art, f in felder:
            if art == "wahl":
                werte.append(f.get_selected())
            else:
                c = f.get_rgba()
                werte.append("#%02x%02x%02x" % (round(c.red * 255), round(c.green * 255), round(c.blue * 255)))
        dlg.close()
        ok(werte)
    gut.connect("clicked", los)
    knoepfe.append(abbrechen)
    knoepfe.append(gut)
    box.append(knoepfe)
    dlg.set_child(box)
    dlg.set_default_widget(gut)
    dlg.present()
    return dlg


def zahl(wert, vorgabe=0.0):
    try:
        return float(str(wert).replace(",", "."))
    except ValueError:
        return vorgabe
