"""Reiter Einfügen: Seiten, Tabellen, Illustrationen, Links, Kopf-/Fußzeile, Text, Symbole."""
import datetime
import os
import re
import shutil
import subprocess
import tempfile

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk  # noqa: E402

from . import befehl, klappe, hilfen
from .. import grafik, html_io, objekte, symbole


def _d(w):
    return w.dok()


# ================================================================ Seiten
@befehl("seitenumbruch")
def _seitenumbruch(w, _=None):
    d = _d(w)
    if not d:
        return
    d.puffer.begin_user_action()
    it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
    if not it.starts_line():
        d.puffer.insert(it, "\n")
    o = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_offset()
    d.puffer.insert_at_cursor("⁂ Seitenumbruch ⁂\n")
    d.puffer.apply_tag(html_io.tag_holen(d.puffer, "umbruch"), d.puffer.get_iter_at_offset(o),
                       d.puffer.get_iter_at_offset(o + len("⁂ Seitenumbruch ⁂\n")))
    d.puffer.end_user_action()


@befehl("leere_seite")
def _leere_seite(w, quer=False):
    d = _d(w)
    if not d:
        return
    _seitenumbruch(w)
    d.puffer.insert_at_cursor("\n")
    _seitenumbruch(w)
    w.status("Leere Seite (%s) eingefügt." % ("Querformat" if quer else "Hochformat"))


@befehl("deckblatt")
def _deckblatt(w, _=None):
    d = _d(w)
    if not d:
        return

    def ok(v):
        titel, unter, autor, datum = v
        d.puffer.begin_user_action()
        d.puffer.place_cursor(d.puffer.get_start_iter())
        o = 0
        teile = [("\n\n\n\n", None), (titel + "\n", "st:Titel"), (unter + "\n\n", "st:Untertitel"),
                 ("\n\n\n", None), (autor + "\n", "al-center"), (datum + "\n", "al-center")]
        for text, tag in teile:
            von = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_offset()
            d.puffer.insert_at_cursor(text)
            d.puffer.apply_tag(html_io.tag_holen(d.puffer, "al-center"), d.puffer.get_iter_at_offset(von),
                               d.puffer.get_iter_at_offset(von + len(text)))
            if tag and tag != "al-center":
                d.puffer.apply_tag(html_io.tag_holen(d.puffer, tag), d.puffer.get_iter_at_offset(von),
                                   d.puffer.get_iter_at_offset(von + len(text)))
        d.puffer.end_user_action()
        _seitenumbruch(w)
    hilfen.frage(w, "Deckblatt", [("Titel", "Titel des Dokuments"), ("Untertitel", "Untertitel"),
                                  ("Verfasser", w.werte.get("benutzer", "")),
                                  ("Datum", datetime.date.today().strftime("%d.%m.%Y"))], ok,
                 "Das Deckblatt wird am Anfang des Dokuments eingefügt.")


# ================================================================ Tabellen
def _tabelle_einfuegen(w, zeilen, spalten, daten=None):
    d = _d(w)
    if d:
        d.objekt_einfuegen(daten or objekte.tabelle_daten(zeilen, spalten), eigener_absatz=True)


@klappe("tabelle_raster")
def _tabelle_raster(w, pop):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(8)
    info = Gtk.Label(label="Tabelle einfügen", xalign=0)
    box.append(info)
    gitter = Gtk.Grid(row_spacing=2, column_spacing=2)
    felder = {}

    def hover(zeile, spalte):
        info.set_text("%d × %d Tabelle" % (zeile, spalte))
        for (r, c), b in felder.items():
            (b.add_css_class if r <= zeile and c <= spalte else b.remove_css_class)("suggested-action")
    for r in range(1, 9):
        for c in range(1, 11):
            b = Gtk.Button()
            b.set_size_request(20, 20)
            ctrl = Gtk.EventControllerMotion()
            ctrl.connect("enter", lambda *_a, r=r, c=c: hover(r, c))
            b.add_controller(ctrl)
            b.connect("clicked", lambda _b, r=r, c=c: (pop.popdown(), _tabelle_einfuegen(w, r, c)))
            gitter.attach(b, c, r, 1, 1)
            felder[(r, c)] = b
    box.append(gitter)
    mehr = Gtk.Button(label="Tabelle einfügen …")
    mehr.add_css_class("flat")
    mehr.connect("clicked", lambda *_: (pop.popdown(), _tabelle_dialog(w)))
    box.append(mehr)
    return box


def _tabelle_dialog(w):
    def ok(v):
        _tabelle_einfuegen(w, max(1, int(hilfen.zahl(v[0], 3))), max(1, int(hilfen.zahl(v[1], 3))))
    hilfen.frage(w, "Tabelle einfügen", [("Zeilen", "3"), ("Spalten", "3")], ok)


SCHNELL = {
    "Zweispaltige Liste": [["Begriff", "Erklärung"], ["", ""], ["", ""], ["", ""]],
    "Terminplan": [["Uhrzeit", "Thema", "Ort"], ["09:00", "", ""], ["10:30", "", ""], ["12:00", "Mittagspause", ""]],
    "Preisliste": [["Position", "Menge", "Einzelpreis", "Summe"], ["", "", "", ""], ["", "", "", ""], ["", "", "Gesamt", ""]],
    "Wochenplan": [["", "Mo", "Di", "Mi", "Do", "Fr"], ["Vormittag", "", "", "", "", ""], ["Nachmittag", "", "", "", "", ""]],
    "Vergleich": [["", "Möglichkeit A", "Möglichkeit B"], ["Vorteile", "", ""], ["Nachteile", "", ""], ["Kosten", "", ""]],
}


@befehl("schnelltabelle")
def _schnelltabelle(w, _=None):
    _schnelltab(w, "Zweispaltige Liste")


def _schnelltab(w, name):
    z = SCHNELL[name]
    _tabelle_einfuegen(w, len(z), len(z[0]), objekte.tabelle_daten(len(z), len(z[0]), [list(r) for r in z]))


@klappe("schnelltabelle_klappe")
def _schnelltabelle_klappe(w, pop):
    return hilfen.liste(pop, [(n, (lambda n=n: _schnelltab(w, n))) for n in SCHNELL] +
                        ["-", ("Kalender (aktueller Monat)", lambda: _kalender(w))])


def _kalender(w):
    import calendar
    h = datetime.date.today()
    cal = calendar.Calendar(0)
    zeilen = [["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]]
    for wk in cal.monthdayscalendar(h.year, h.month):
        zeilen.append([str(t) if t else "" for t in wk])
    d = _d(w)
    if d:
        d.text_einfuegen("%s %d\n" % (calendar.month_name[h.month], h.year), ("b",))
        _tabelle_einfuegen(w, len(zeilen), 7, objekte.tabelle_daten(len(zeilen), 7, zeilen))


def _zelle_auswerten(blatt, ref, tiefe=0):
    """Tabellenblatt: Zelle in A1-Schreibweise → Zahl."""
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    if not m or tiefe > 20:
        raise ValueError(ref)
    sp = 0
    for ch in m.group(1):
        sp = sp * 26 + ord(ch) - 64
    zeile, spalte = int(m.group(2)), sp
    try:
        t = blatt[zeile][spalte]
    except IndexError:
        return 0.0
    return _auswerten(blatt, t, tiefe + 1)


def _auswerten(blatt, text, tiefe=0):
    t = (text or "").strip()
    if not t.startswith("="):
        try:
            return float(t.replace(",", "."))
        except ValueError:
            return 0.0
    ausdruck = t[1:].upper()

    def bereich(m):
        a, b = m.group(1), m.group(2)
        ma, mb = re.match(r"([A-Z]+)(\d+)", a), re.match(r"([A-Z]+)(\d+)", b)

        def sp(s):
            n = 0
            for ch in s:
                n = n * 26 + ord(ch) - 64
            return n
        z1, z2 = sorted((int(ma.group(2)), int(mb.group(2))))
        s1, s2 = sorted((sp(ma.group(1)), sp(mb.group(1))))
        refs = []
        for z in range(z1, z2 + 1):
            for s in range(s1, s2 + 1):
                name = ""
                n = s
                while n:
                    n, r = divmod(n - 1, 26)
                    name = chr(65 + r) + name
                refs.append("%s%d" % (name, z))
        return "[" + ",".join("_c('%s')" % r for r in refs) + "]"
    ausdruck = re.sub(r"([A-Z]+\d+):([A-Z]+\d+)", bereich, ausdruck)
    ausdruck = re.sub(r"(?<![A-Z_'])([A-Z]{1,2}\d+)(?![\w'])", r"_c('\1')", ausdruck)
    erlaubt = {"SUMME": lambda *a: sum(_flach(a)), "SUM": lambda *a: sum(_flach(a)),
               "MITTELWERT": lambda *a: sum(_flach(a)) / max(len(_flach(a)), 1),
               "AVERAGE": lambda *a: sum(_flach(a)) / max(len(_flach(a)), 1),
               "MIN": lambda *a: min(_flach(a)), "MAX": lambda *a: max(_flach(a)),
               "ANZAHL": lambda *a: len(_flach(a)), "RUNDEN": lambda x, n=0: round(x, int(n)),
               "_c": lambda r: _zelle_auswerten(blatt, r, tiefe)}
    if re.search(r"[^A-Z0-9_\[\]\(\)\+\-\*/\.,'\s%]", ausdruck):
        raise ValueError("Zeichen")
    return eval(compile(ausdruck.replace("^", "**"), "<formel>", "eval"), {"__builtins__": {}}, erlaubt)


def _flach(a):
    out = []
    for x in a:
        out.extend(_flach(x) if isinstance(x, (list, tuple)) else [x])
    return out


@befehl("tabellenblatt")
def _tabellenblatt(w, _=None):
    d = _d(w)
    if not d:
        return
    zeilen, spalten = 8, 5
    daten = objekte.tabelle_daten(zeilen + 1, spalten + 1)
    daten["blatt"] = True
    daten["zellen"][0] = [""] + [chr(65 + c) for c in range(spalten)]
    for r in range(1, zeilen + 1):
        daten["zellen"][r][0] = str(r)
    anker = d.objekt_einfuegen(daten, eigener_absatz=True)
    w.status("Tabellenblatt: Formeln beginnen mit =, z. B. =SUMME(B1:B3) oder =B1*C1. Mit Enter wird gerechnet.")
    _blatt_anbinden(daten)


def _blatt_anbinden(daten):
    zellen = daten.get("_zellen", {})

    def rechnen(*_):
        for (r, c), e in zellen.items():
            roh = daten["zellen"][r][c]
            if roh.startswith("=") and not e.has_focus():
                try:
                    v = _auswerten(daten["zellen"], roh)
                    e.set_placeholder_text("%g" % v)
                    e.set_tooltip_text(roh)
                    e.set_text("%g" % round(v, 6)) if False else None
                except Exception:
                    e.set_placeholder_text("#FEHLER")
    for (r, c), e in zellen.items():
        e.connect("activate", rechnen)
        e.connect("notify::has-focus", rechnen)


@befehl("tabelle_eigenschaften")
def _tabelle_eig(w, _=None):
    d = _d(w)
    a = d.objekt_am_cursor() if d else None
    if a is None or a.daten.get("typ") != "tabelle":
        return w.meldung("Keine Tabelle", "Stellen Sie den Cursor in oder vor die Tabelle (Tabelle mit Klick auf die Stelle davor markieren).")
    dat = a.daten
    dlg = Gtk.Window(transient_for=w, modal=True, title="Eigenschaften der Tabelle")
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="%d Zeilen × %d Spalten" % (len(dat["zellen"]), len(dat["zellen"][0])), xalign=0))
    rand = Gtk.CheckButton(label="Rahmenlinien", active=dat.get("rand", True))
    kopf = Gtk.CheckButton(label="Kopfzeile hervorheben", active=dat.get("kopf", True))
    box.append(rand)
    box.append(kopf)
    ausr = Gtk.DropDown.new_from_strings(["Links", "Mitte", "Rechts"])
    ausr.set_selected({"links": 0, "mitte": 1, "rechts": 2}.get(dat.get("ausr", "links"), 0))
    zl = Gtk.Box(spacing=8)
    zl.append(Gtk.Label(label="Textausrichtung"))
    zl.append(ausr)
    box.append(zl)
    farbe = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
    c = Gdk.RGBA()
    c.parse(dat.get("kopffarbe", "#D9E2F3"))
    farbe.set_rgba(c)
    fz = Gtk.Box(spacing=8)
    fz.append(Gtk.Label(label="Farbe der Kopfzeile"))
    fz.append(farbe)
    box.append(fz)
    aktionen = Gtk.Box(spacing=6)

    def aendern(fn):
        def f(*_):
            fn()
            d.objekt_neu_zeichnen(a)
            dlg.close()
            _tabelle_eig(w)
        return f

    def zeile_plus():
        dat["zellen"].append([""] * len(dat["zellen"][0]))

    def zeile_minus():
        if len(dat["zellen"]) > 1:
            dat["zellen"].pop()

    def spalte_plus():
        for z in dat["zellen"]:
            z.append("")

    def spalte_minus():
        if len(dat["zellen"][0]) > 1:
            for z in dat["zellen"]:
                z.pop()
    for text, fn in (("Zeile +", zeile_plus), ("Zeile −", zeile_minus), ("Spalte +", spalte_plus), ("Spalte −", spalte_minus)):
        b = Gtk.Button(label=text)
        b.connect("clicked", aendern(fn))
        aktionen.append(b)
    box.append(aktionen)
    ok = Gtk.Button(label="Übernehmen")
    ok.add_css_class("suggested-action")

    def uebernehmen(*_):
        dat["rand"] = rand.get_active()
        dat["kopf"] = kopf.get_active()
        dat["ausr"] = ["links", "mitte", "rechts"][ausr.get_selected()]
        rgba = farbe.get_rgba()
        dat["kopffarbe"] = "#%02x%02x%02x" % (round(rgba.red * 255), round(rgba.green * 255), round(rgba.blue * 255))
        d.objekt_neu_zeichnen(a)
        dlg.close()
    ok.connect("clicked", uebernehmen)
    box.append(ok)
    dlg.present()


# ================================================================ Illustrationen
@befehl("bild")
def _bild(w, _=None):
    d = _d(w)
    if not d:
        return
    dlg = Gtk.FileDialog(title="Bild einfügen")
    f = Gtk.FileFilter()
    f.set_name("Bilder")
    for m in ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp", "*.svg"):
        f.add_pattern(m)
    fl = Gio.ListStore.new(Gtk.FileFilter)
    fl.append(f)
    dlg.set_filters(fl)

    def fertig(dlg, res):
        try:
            datei = dlg.open_finish(res)
        except GLib.Error:
            return
        try:
            d.objekt_einfuegen(objekte.bild_daten(datei.get_path()))
        except Exception as e:
            w.meldung("Bild konnte nicht eingefügt werden", str(e))
    dlg.open(w, None, fertig)


def _svg_einfuegen(w, svg, breite, hoehe, quelle=None, alt=""):
    d = _d(w)
    if d:
        d.objekt_einfuegen(objekte.svg_daten(svg, breite, hoehe, quelle, alt))


@klappe("formen_galerie")
def _formen(w, pop):
    box = Gtk.FlowBox()
    box.set_max_children_per_line(5)
    box.set_selection_mode(Gtk.SelectionMode.NONE)
    for n in grafik.FORMEN:
        b = Gtk.Button()
        b.add_css_class("flat")
        svg = grafik.form(n, breite=60, hoehe=40)
        b.set_child(Gtk.Picture.new_for_paintable(objekte.textur_aus_bytes(svg.encode(), True)))
        b.get_child().set_size_request(60, 40)
        b.set_tooltip_text(n)
        b.connect("clicked", lambda _b, n=n: (pop.popdown(), _svg_einfuegen(w, grafik.form(n), 160, 100, {"form": n, "fuell": "#2F6FB5", "rand": "#1B4A80"}, n)))
        box.append(b)
    box.set_margin_start(8)
    box.set_margin_end(8)
    box.set_margin_top(8)
    box.set_margin_bottom(8)
    return box


@befehl("zeichnen")
def _zeichnen(w, _=None):
    dlg = Gtk.Window(transient_for=w, modal=True, title="Form mit eigener Farbe")
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    form = Gtk.DropDown.new_from_strings(grafik.FORMEN)
    fuell = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
    rand = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
    for btn, farbe in ((fuell, "#2F6FB5"), (rand, "#1B4A80")):
        c = Gdk.RGBA()
        c.parse(farbe)
        btn.set_rgba(c)
    text = Gtk.Entry(placeholder_text="Text in der Form (freiwillig)")
    breite = Gtk.Entry(text="160")
    hoehe = Gtk.Entry(text="100")
    for name, wid in (("Form", form), ("Füllfarbe", fuell), ("Randfarbe", rand), ("Text", text), ("Breite (px)", breite), ("Höhe (px)", hoehe)):
        z = Gtk.Box(spacing=8)
        l = Gtk.Label(label=name, xalign=0)
        l.set_size_request(100, -1)
        z.append(l)
        z.append(wid)
        box.append(z)

    def hx(c):
        r = c.get_rgba()
        return "#%02x%02x%02x" % (round(r.red * 255), round(r.green * 255), round(r.blue * 255))

    def ok(*_):
        n = grafik.FORMEN[form.get_selected()]
        b, h = int(hilfen.zahl(breite.get_text(), 160)), int(hilfen.zahl(hoehe.get_text(), 100))
        _svg_einfuegen(w, grafik.form(n, hx(fuell), hx(rand), b, h, text.get_text()), b, h,
                       {"form": n, "fuell": hx(fuell), "rand": hx(rand), "text": text.get_text()}, n)
        dlg.close()
    gut = Gtk.Button(label="Einfügen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


@befehl("diagramm")
def _diagramm(w, _=None):
    dlg = Gtk.Window(transient_for=w, modal=True, title="Diagramm")
    dlg.set_default_size(520, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    art = Gtk.DropDown.new_from_strings(["Säulen", "Linie", "Kreis"])
    titel = Gtk.Entry(placeholder_text="Titel")
    box.append(Gtk.Label(label="Daten (erste Zeile = Reihennamen, danach je Zeile: Kategorie; Zahl; Zahl …)", xalign=0, wrap=True))
    tv = Gtk.TextView()
    tv.get_buffer().set_text(";Reihe A;Reihe B\nJanuar;4;6\nFebruar;7;3\nMärz;5;8\nApril;9;4")
    tv.set_monospace(True)
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(tv)
    box.append(art)
    box.append(titel)
    box.append(rolle)

    def lesen():
        b = tv.get_buffer()
        zeilen = [z for z in b.get_text(b.get_start_iter(), b.get_end_iter(), False).split("\n") if z.strip()]
        teile = [[t.strip() for t in re.split(r"[;\t]", z)] for z in zeilen]
        kopf = teile[0][1:]
        daten = [[t[0]] + [hilfen.zahl(x) for x in t[1:len(kopf) + 1]] for t in teile[1:]]
        return kopf, daten

    def ok(*_):
        try:
            kopf, daten = lesen()
            a = ["saeulen", "linie", "kreis"][art.get_selected()]
            svg = grafik.diagramm(a, kopf, daten, titel.get_text())
        except Exception as e:
            return w.meldung("Daten nicht lesbar", str(e))
        _svg_einfuegen(w, svg, 460, 280, {"diagramm": a, "kopf": kopf, "daten": daten, "titel": titel.get_text()},
                       "Diagramm " + titel.get_text())
        dlg.close()
    gut = Gtk.Button(label="Einfügen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


_SMART_TEXT = {
    "Liste": "Zeigt nicht aufeinanderfolgende Informationen oder Gruppen von Informationen untereinander an.",
    "Prozess": "Zeigt die Schritte eines Ablaufs von links nach rechts, jeweils mit einem Pfeil verbunden.",
    "Zyklus": "Zeigt einen fortlaufenden Prozess, bei dem der letzte Schritt wieder zum ersten führt.",
    "Hierarchie": "Zeigt Beziehungen zwischen Ebenen: oben die Hauptidee, darunter die untergeordneten Punkte.",
    "Pyramide": "Zeigt proportionale oder aufeinander aufbauende Beziehungen, die nach oben schmaler werden.",
    "Vergleich": "Stellt zwei Gruppen von Informationen nebeneinander, um sie zu vergleichen.",
}


def _svg_textur(svg, breite, hoehe):
    from gi.repository import GdkPixbuf
    lader = GdkPixbuf.PixbufLoader.new_with_type("svg")
    lader.write(svg.encode("utf-8"))
    lader.close()
    pb = lader.get_pixbuf().scale_simple(breite, hoehe, GdkPixbuf.InterpType.BILINEAR)
    return Gdk.Texture.new_for_pixbuf(pb)


@befehl("smartart")
def _smartart(w, _=None):
    """SmartArt-Grafik auswählen: links die Layouts, rechts Vorschau, Beschreibung und Einträge."""
    dlg = Gtk.Window(transient_for=w, modal=True, title="SmartArt-Grafik auswählen")
    dlg.set_default_size(820, 460)
    haupt = Gtk.Box(spacing=0)
    links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(links, "set_margin_" + r)(14)
    kopf = Gtk.Label(label="Alle", xalign=0)
    kopf.add_css_class("heading")
    links.append(kopf)
    wahl = {"art": grafik.SMARTART[0]}
    rechts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    rechts.set_size_request(300, -1)
    for r in ("start", "end", "top", "bottom"):
        getattr(rechts, "set_margin_" + r)(14)
    vorschau = Gtk.Picture()
    vorschau.set_size_request(270, 150)
    name = Gtk.Label(xalign=0)
    name.add_css_class("heading")
    beschr = Gtk.Label(xalign=0, wrap=True)
    beschr.add_css_class("dim-label")
    tv = Gtk.TextView()
    tv.get_buffer().set_text("Idee\nPlanung\nUmsetzung\nErgebnis")
    rolle = Gtk.ScrolledWindow(vexpand=True, min_content_height=80)
    rolle.set_child(tv)
    rolle.set_has_frame(True)
    for x in (vorschau, name, beschr, Gtk.Label(label="Ein Eintrag pro Zeile:", xalign=0), rolle):
        rechts.append(x)

    def zeigen(art):
        wahl["art"] = art
        vorschau.set_paintable(_svg_textur(grafik.smartart(art, ["Text", "Text", "Text"], 520, 300), 270, 156))
        name.set_text(art)
        beschr.set_text(_SMART_TEXT.get(art, ""))
    gitter = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.SINGLE, max_children_per_line=3, min_children_per_line=3,
                         column_spacing=8, row_spacing=8, valign=Gtk.Align.START, vexpand=True)
    for art in grafik.SMARTART:
        bild = Gtk.Picture.new_for_paintable(_svg_textur(grafik.smartart(art, ["", "", ""], 520, 300), 130, 76))
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        kasten.append(bild)
        kasten.append(Gtk.Label(label=art))
        kasten.set_tooltip_text(art)
        gitter.append(kasten)
    gitter.connect("child-activated", lambda g, k: zeigen(grafik.SMARTART[k.get_index()]))
    gitter.connect("selected-children-changed", lambda g: [zeigen(grafik.SMARTART[k.get_index()]) for k in g.get_selected_children()])
    links.append(gitter)
    haupt.append(links)
    haupt.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
    haupt.append(rechts)

    def ok(*_):
        b = tv.get_buffer()
        eintraege = [z.strip() for z in b.get_text(b.get_start_iter(), b.get_end_iter(), False).split("\n") if z.strip()]
        a = wahl["art"]
        _svg_einfuegen(w, grafik.smartart(a, eintraege), 520, 220, {"smartart": a, "eintraege": eintraege}, "SmartArt " + a)
        dlg.close()
    gut = Gtk.Button(label="OK")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    rechts.append(gut)
    dlg.set_child(haupt)
    gitter.select_child(gitter.get_child_at_index(0))
    dlg.present()


@befehl("wordart")
def _wordart(w, _=None):
    def ok(v):
        svg, b, h = grafik.wordart(v[0] or "WordArt", v[1] if v[1] in grafik.WORTSTILE else "Verlauf", int(hilfen.zahl(v[2], 56)))
        _svg_einfuegen(w, svg, b, h, {"wordart": v[0]}, v[0])
    hilfen.frage(w, "WordArt", [("Text", "Lunivo"), ("Stil (%s)" % ", ".join(grafik.WORTSTILE), "Verlauf"), ("Größe", "56")], ok)


@befehl("piktogramm")
def _piktogramm(w, _=None):
    dlg = Gtk.Window(transient_for=w, modal=True, title="Piktogramm")
    dlg.set_default_size(520, 480)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(12)
    dlg.set_child(box)
    suche = Gtk.SearchEntry(placeholder_text="Suchen")
    box.append(suche)
    fb = Gtk.FlowBox()
    fb.set_max_children_per_line(10)
    fb.set_selection_mode(Gtk.SelectionMode.SINGLE)
    namen = sorted(symbole._PFADE)
    for n in namen:
        b = Gtk.Box()
        b.set_tooltip_text(n)
        b.append(symbole.Symbol(n, 28))
        fb.append(b)
    fb.set_filter_func(lambda ch: suche.get_text().lower() in (ch.get_child().get_tooltip_text() or "").lower())
    suche.connect("search-changed", lambda *_: fb.invalidate_filter())
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(fb)
    box.append(rolle)
    farbe = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
    c = Gdk.RGBA()
    c.parse("#2F6FB5")
    farbe.set_rgba(c)
    gr = Gtk.Entry(text="64")
    zl = Gtk.Box(spacing=8)
    zl.append(Gtk.Label(label="Farbe"))
    zl.append(farbe)
    zl.append(Gtk.Label(label="Größe (px)"))
    zl.append(gr)
    box.append(zl)

    def ok(*_):
        ch = fb.get_selected_children()
        if not ch:
            return
        n = ch[0].get_child().get_tooltip_text()
        r = farbe.get_rgba()
        svg, b, h = grafik.piktogramm(n, "#%02x%02x%02x" % (round(r.red * 255), round(r.green * 255), round(r.blue * 255)),
                                      int(hilfen.zahl(gr.get_text(), 64)))
        _svg_einfuegen(w, svg, b, h, {"piktogramm": n}, n)
        dlg.close()
    gut = Gtk.Button(label="Einfügen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


@befehl("screenshot")
def _screenshot(w, _=None):
    prog = shutil.which("gnome-screenshot")
    d = _d(w)
    if not prog or not d:
        return w.meldung("Bildschirmfoto", "gnome-screenshot ist nicht installiert.")
    ziel = os.path.join(tempfile.mkdtemp(prefix="lunivo-"), "foto.png")
    w.minimize()

    def los():
        try:
            subprocess.run([prog, "-a", "-f", ziel], timeout=120)
        finally:
            w.unminimize()
            w.present()
        if os.path.exists(ziel):
            d.objekt_einfuegen(objekte.bild_daten(ziel))
        return False
    GLib.timeout_add(700, los)
    w.status("Bereich auf dem Bildschirm aufziehen …")


# ================================================================ Links
@befehl("hyperlink")
def _hyperlink(w, _=None):
    d = _d(w)
    if not d:
        return
    sel = d.puffer.get_selection_bounds()
    text = d.puffer.get_text(*sel, False) if sel else ""
    a = d.objekt_am_cursor()

    def ok(v):
        anz, adr = v
        if not adr.strip():
            return
        if not re.match(r"^[a-z]+:|^#", adr):
            adr = ("mailto:" + adr) if "@" in adr and " " not in adr else "https://" + adr
        d.puffer.begin_user_action()
        if sel:
            for n in [t for t in html_io.zeichen_namen(d.puffer) if t.startswith("link:")]:
                d.puffer.remove_tag(html_io.tag_holen(d.puffer, n), *sel)
            d.puffer.apply_tag(html_io.tag_holen(d.puffer, "link:" + adr), *sel)
        else:
            d.text_einfuegen(anz or adr, ("link:" + adr,))
        d.puffer.end_user_action()
    hilfen.frage(w, "Hyperlink", [("Anzeigetext", text), ("Adresse", "https://")], ok,
                 "Mit Strg + Klick auf den Link wird er geöffnet.")


@befehl("textmarke")
def _textmarke(w, _=None):
    d = _d(w)
    if not d:
        return
    marken = d.marken()

    def ok(v):
        name = re.sub(r"\W+", "_", v[0].strip())
        if not name:
            return
        sel = d.puffer.get_selection_bounds()
        if not sel:
            it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
            sel = (it, it.copy())
            sel[1].forward_char()
        for n in [t for t in html_io.zeichen_namen(d.puffer) if t == "marke:" + name]:
            d.puffer.remove_tag_by_name(n, d.puffer.get_start_iter(), d.puffer.get_end_iter())
        d.puffer.apply_tag(html_io.tag_holen(d.puffer, "marke:" + name), *sel)
        d.puffer.set_modified(True)
        w.status("Textmarke „%s“ gesetzt." % name)
    hilfen.frage(w, "Lesezeichen / Textmarke", [("Name", "")], ok,
                 ("Vorhandene Marken: " + ", ".join(marken)) if marken else "Die Marke gilt für den ausgewählten Text.")


@befehl("querverweis")
def _querverweis(w, _=None):
    d = _d(w)
    if not d:
        return
    ziele = d.querverweis_ziele()
    if not ziele:
        return w.meldung("Querverweis", "Es gibt noch nichts, worauf verwiesen werden kann (Überschriften, Textmarken).")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Querverweis auf …")
    dlg.set_buttons([z[0][:60] for z in ziele[:7]] + ["Abbrechen"])
    dlg.set_cancel_button(len(ziele[:7]))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(ziele[:7]):
            text, ziel = ziele[n]
            d.text_einfuegen(text, ("link:#" + ziel,))
    dlg.choose(w, None, fertig)


# ================================================================ Kopf- und Fußzeile
@befehl("kopf_fuss_zeigen")
def _kopf_fuss(w, _=None):
    d = _d(w)
    if d:
        an = not d.kopf_fuss_an()
        d.kopf_fuss_zeigen(an, an)
        w.band_auffrischen()
        if an:
            d.kopf.grab_focus()


@klappe("seitenzahl_klappe")
def _seitenzahl_klappe(w, pop):
    d = _d(w)

    def setze(wo, ausr=None, vorlage="{Seite}"):
        if not d:
            return
        tv = d.kopf if wo == "kopf" else d.fuss
        tv.set_visible(True)
        d.seite_anwenden()
        b = tv.get_buffer()
        b.set_text(vorlage)
        tv.set_justification({"links": Gtk.Justification.LEFT, "mitte": Gtk.Justification.CENTER,
                              "rechts": Gtk.Justification.RIGHT}[ausr or "mitte"])
        d.puffer.set_modified(True)
    return hilfen.liste(pop, [
        ("Seitenende, Mitte", lambda: setze("fuss", "mitte")),
        ("Seitenende, rechts", lambda: setze("fuss", "rechts")),
        ("Seitenende, „Seite 1 von N“", lambda: setze("fuss", "mitte", "Seite {Seite} von {Seiten}")),
        ("Seitenanfang, rechts", lambda: setze("kopf", "rechts")),
        ("Seitenanfang, Mitte", lambda: setze("kopf", "mitte")),
        "-",
        ("An der Cursorstelle (Feld {Seite})", lambda: (d.text_einfuegen("{Seite}") if d else None)),
        ("Seitenzahl entfernen", lambda: _seitenzahl_weg(d)),
    ])


def _seitenzahl_weg(d):
    if not d:
        return
    for tv in (d.kopf, d.fuss):
        b = tv.get_buffer()
        t = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        b.set_text(t.replace("{Seite}", "").replace("{Seiten}", ""))


@befehl("seitenzahl")
def _seitenzahl(w, _=None):
    d = _d(w)
    if d:
        d.fuss.set_visible(True)
        d.seite_anwenden()
        d.fuss.get_buffer().set_text("{Seite}")
        d.fuss.set_justification(Gtk.Justification.CENTER)


# ================================================================ Text
@befehl("textfeld")
def _textfeld(w, _=None):
    d = _d(w)
    if d:
        sel = d.puffer.get_selection_bounds()
        text = d.puffer.get_text(*sel, False) if sel else "Text eingeben"
        d.objekt_einfuegen(objekte.textfeld_daten(text, "#FFF8E1", "#B5563F"), eigener_absatz=True)


@befehl("initiale")
def _initiale(w, _=None):
    """Initial: Zu Beginn eines Absatzes einen Großbuchstaben setzen (keine / eingezogen / im Rand)."""
    d = _d(w)
    if not d:
        return

    def ok(v):
        _, von = d.puffer.get_iter_at_line(d._zeilen()[0])
        ende = von.copy()
        ende.forward_char()
        for n in html_io.zeichen_namen(d.puffer):
            if n.startswith(("size:", "col:")) or (n == "b" and v[0] == 0):
                d.puffer.remove_tag_by_name(n, von, ende)
        if v[0] == 0:
            d.puffer.set_modified(True)
            return w.status("Initial entfernt.")
        zeilen = v[1] + 2
        gr = d.vorgabe_groesse * zeilen * 1.25
        for tag in (html_io.tag_holen(d.puffer, "size:%g" % gr), html_io.tag_holen(d.puffer, "b"),
                    html_io.tag_holen(d.puffer, "col:" + v[2])):
            d.puffer.apply_tag(tag, von, ende)
        d.puffer.set_modified(True)
        w.status("Initial gesetzt.")
    hilfen.auswahl_fenster(
        w, "Initial",
        [("Position", "wahl", ["Keine", "Eingezogen", "Im Rand"], 1),
         ("Höhe in Zeilen", "wahl", ["2", "3", "4", "5"], 1), ("Farbe", "farbe", "#B5563F")],
        ok, text="Zu Beginn eines Absatzes einen Großbuchstaben setzen.")


@befehl("datum_uhrzeit")
def _datum(w, _=None):
    d = _d(w)
    if not d:
        return
    jetzt = datetime.datetime.now()
    formate = ["%d.%m.%Y", "%d. %B %Y", "%A, %d. %B %Y", "%Y-%m-%d", "%H:%M", "%d.%m.%Y %H:%M", "%H:%M:%S"]
    eintraege = [(jetzt.strftime(f), (lambda f=f: d.text_einfuegen(datetime.datetime.now().strftime(f)))) for f in formate]
    dlg = Gtk.AlertDialog()
    dlg.set_message("Datum und Uhrzeit")
    texte = [e[0] for e in eintraege[:7]]
    dlg.set_buttons(texte + ["Abbrechen"])
    dlg.set_cancel_button(len(texte))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(texte):
            eintraege[n][1]()
    dlg.choose(w, None, fertig)


@befehl("text_aus_datei")
def _text_aus_datei(w, _=None):
    d = _d(w)
    if not d:
        return
    dlg = Gtk.FileDialog(title="Text aus Datei einfügen")

    def fertig(dlg, res):
        try:
            datei = dlg.open_finish(res)
        except GLib.Error:
            return
        pfad = datei.get_path()
        try:
            from .. import editor
            tmp = editor.Dokument()
            tmp.laden(pfad)
            d.text_einfuegen(tmp.text().replace("￼", ""))
        except Exception as e:
            w.meldung("Text konnte nicht eingefügt werden", str(e))
    dlg.open(w, None, fertig)


# ================================================================ Symbole
SONDERZEICHEN = {
    "Häufig": "äöüÄÖÜß€£¥§©®™°±×÷½¼¾¹²³«»„“‚‘’–—…•·†‡¶",
    "Lateinisch": "àáâãåæçèéêëìíîïñòóôõøùúûýÿšžčćđłńśźżőű",
    "Mathematik": "±×÷≠≈≤≥∞√∑∏∫∂∇∈∉⊂⊃∪∩∧∨¬∀∃∅ℕℤℚℝℂ‰",
    "Pfeile": "←↑→↓↔↕⇐⇒⇔↩↪⇄⇅➔➜➤➥",
    "Griechisch": "αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ",
    "Währung": "€$£¥¢₹₽₩₪฿₴₺",
    "Symbole": "★☆✓✔✗✘☐☑☒♠♣♥♦♪♫☀☁☂☎✉✂✎☺☹♀♂⚠☢☣❤",
    "Rahmen": "─│┌┐└┘├┤┬┴┼═║╔╗╚╝",
}


@befehl("sonderzeichen")
def _sonderzeichen(w, _=None):
    d = _d(w)
    dlg = Gtk.Window(transient_for=w, title="Sonderzeichen")
    dlg.set_default_size(520, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(10)
    dlg.set_child(box)
    kat = Gtk.DropDown.new_from_strings(list(SONDERZEICHEN))
    box.append(kat)
    fb = Gtk.FlowBox()
    fb.set_max_children_per_line(14)
    fb.set_selection_mode(Gtk.SelectionMode.NONE)
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(fb)
    box.append(rolle)
    vorschau = Gtk.Label(label="", xalign=0)

    def fuellen(*_):
        k = fb.get_first_child()
        while k:
            n = k.get_next_sibling()
            fb.remove(k)
            k = n
        for ch in SONDERZEICHEN[list(SONDERZEICHEN)[kat.get_selected()]]:
            b = Gtk.Button(label=ch)
            b.add_css_class("flat")
            b.set_tooltip_text("U+%04X" % ord(ch))
            b.connect("clicked", lambda _b, ch=ch: (d.text_einfuegen(ch) if d else None, vorschau.set_text("Eingefügt: " + ch + "  (U+%04X)" % ord(ch))))
            fb.append(b)
    kat.connect("notify::selected", fuellen)
    fuellen()
    box.append(vorschau)
    schliessen = Gtk.Button(label="Schließen")
    schliessen.connect("clicked", lambda *_: dlg.close())
    box.append(schliessen)
    dlg.present()


@befehl("formel")
def _formel(w, _=None):
    dlg = Gtk.Window(transient_for=w, modal=True, title="Formel")
    dlg.set_default_size(520, 360)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Formel in LaTeX-Schreibweise, z. B.  x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}", xalign=0, wrap=True))
    e = Gtk.Entry(text="E = m \\cdot c^2")
    box.append(e)
    bild = Gtk.Picture()
    bild.set_size_request(480, 120)
    box.append(bild)
    zustand = {}

    def vorschau(*_):
        try:
            svg, b, h = grafik.formel(e.get_text())
            bild.set_paintable(objekte.textur_aus_bytes(svg.encode(), True))
            bild.set_size_request(b, h)
            zustand["f"] = (svg, b, h)
        except Exception as ex:
            zustand.pop("f", None)
    e.connect("changed", vorschau)
    vorschau()

    def ok(*_):
        if "f" in zustand:
            svg, b, h = zustand["f"]
            _svg_einfuegen(w, svg, b, h, {"formel": e.get_text()}, e.get_text())
        dlg.close()
    gut = Gtk.Button(label="Einfügen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()
