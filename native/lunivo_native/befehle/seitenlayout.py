"""Reiter Seitenlayout: Designs, Ränder, Seite einrichten, Absatz, Hintergrund, Anordnen."""
import base64

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib  # noqa: E402

from . import befehl, klappe, sonder, hilfen
from .. import html_io, objekte, sprachdienste


def _d(w):
    return w.dok()


# ================================================================ Designs
DESIGNS = {
    "Lunivo": {"schrift": "Georgia", "ueb": "#B5563F", "tabelle": "#F3DDD6"},
    "Sachlich": {"schrift": "Sans", "ueb": "#2F6FB5", "tabelle": "#D9E2F3"},
    "Klassisch": {"schrift": "Serif", "ueb": "#000000", "tabelle": "#E8E8E8"},
    "Natur": {"schrift": "Serif", "ueb": "#3E9C7A", "tabelle": "#DDEFE6"},
    "Kontrast": {"schrift": "Sans", "ueb": "#000000", "tabelle": "#FFE08A"},
}
FARBSCHEMEN = {"Terrakotta": "#B5563F", "Blau": "#2F6FB5", "Grün": "#3E9C7A", "Violett": "#674EA7",
               "Gold": "#C08A2E", "Graphit": "#434343"}


def _design_anwenden(w, d, schrift=None, farbe=None, tabelle=None):
    if schrift:
        d.vorgabe_schrift = schrift
        d._grundschrift()
    if farbe:
        for n in ("h1", "h2", "h3", "st:Titel", "st:Untertitel", "st:Überschrift 1", "st:Überschrift 2", "st:Überschrift 3"):
            t = html_io.tag_holen(d.puffer, n)
            from gi.repository import Gdk as _G
            c = _G.RGBA()
            c.parse(farbe)
            t.set_property("foreground-rgba", c)
    if tabelle:
        for a, _o in d.alle_objekte():
            if a.daten["typ"] == "tabelle":
                a.daten["kopffarbe"] = tabelle
                d.objekt_neu_zeichnen(a)
    d.seite["design"] = dict(d.seite.get("design") or {}, **{k: v for k, v in
                              {"schrift": schrift, "ueb": farbe, "tabelle": tabelle}.items() if v})
    d.puffer.set_modified(True)


@klappe("designs")
def _designs(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [(n, (lambda n=n: _design_anwenden(w, d, v["schrift"], v["ueb"], v["tabelle"])))
                              for n, v in DESIGNS.items()])


@klappe("farbschema")
def _farben(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [(n, (lambda f=f: _design_anwenden(w, d, None, f, None))) for n, f in FARBSCHEMEN.items()])


@klappe("design_schriften")
def _schriften(w, pop):
    d = _d(w)
    paare = [("Georgia", "Georgia (Serif)"), ("Serif", "Serif"), ("Sans", "Sans"), ("Monospace", "Monospace"),
             ("Ubuntu", "Ubuntu"), ("DejaVu Sans", "DejaVu Sans"), ("Liberation Serif", "Liberation Serif")]
    return hilfen.liste(pop, [(t, (lambda f=f: _design_anwenden(w, d, f))) for f, t in paare])


@klappe("design_effekte")
def _effekte(w, pop):
    d = _d(w)

    def unterstrichen(an):
        for n in ("h1", "h2", "h3"):
            d.puffer.get_tag_table().lookup(n) or html_io.tag_holen(d.puffer, n)
            d.puffer.get_tag_table().lookup(n).set_property("underline", html_io.Pango.Underline.SINGLE if an else html_io.Pango.Underline.NONE)
        d.puffer.set_modified(True)
    return hilfen.liste(pop, [("Überschriften schlicht", lambda: unterstrichen(False)),
                              ("Überschriften unterstrichen", lambda: unterstrichen(True))])


# ================================================================ Ränder
RAENDER = {
    "Normal": {"oben": 25, "unten": 25, "links": 32, "rechts": 32},
    "Schmal": {"oben": 13, "unten": 13, "links": 13, "rechts": 13},
    "Moderat": {"oben": 25, "unten": 25, "links": 19, "rechts": 19},
    "Breit": {"oben": 25, "unten": 25, "links": 51, "rechts": 51},
}


def _rand_setzen(w, name):
    d = _d(w)
    if d:
        d.seite_setzen(rand=dict(RAENDER[name]))
        w.status("Ränder: %s" % name)


def _rand_massstring(r):
    return "Oben: %d mm   Unten: %d mm   Links: %d mm   Rechts: %d mm" % (r["oben"], r["unten"], r["links"], r["rechts"])


@sonder("raender")
def _raender_galerie(w):
    box = Gtk.Box(spacing=4)
    for n, r in RAENDER.items():
        b = Gtk.Button()
        b.add_css_class("flat")
        k = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        k.append(Gtk.Label(label=n))
        l = Gtk.Label(label="%d / %d / %d / %d" % (r["oben"], r["unten"], r["links"], r["rechts"]))
        l.add_css_class("knopfname")
        k.append(l)
        b.set_child(k)
        b.set_tooltip_text(_rand_massstring(r))
        b.connect("clicked", lambda _b, n=n: _rand_setzen(w, n))
        box.append(b)
    return box


@klappe("raender_klappe")
def _raender_klappe(w, pop):
    d = _d(w)
    eintr = [("%s — %s" % (n, _rand_massstring(r)), (lambda n=n: _rand_setzen(w, n))) for n, r in RAENDER.items()]
    eintr += ["-", ("Benutzerdefinierte Seitenränder …", lambda: _seitenraender(w))]
    return hilfen.liste(pop, eintr)


@befehl("seitenraender")
def _seitenraender(w, _=None):
    d = _d(w)
    if not d:
        return
    r = d.seite["rand"]

    def ok(v):
        d.seite_setzen(rand={"oben": hilfen.zahl(v[0], 25), "unten": hilfen.zahl(v[1], 25),
                             "links": hilfen.zahl(v[2], 32), "rechts": hilfen.zahl(v[3], 32)})
    hilfen.frage(w, "Seitenränder", [("Oben (mm)", "%g" % r["oben"]), ("Unten (mm)", "%g" % r["unten"]),
                                     ("Links (mm)", "%g" % r["links"]), ("Rechts (mm)", "%g" % r["rechts"])], ok)


# ================================================================ Seite einrichten
@befehl("ausrichtung")
def _ausrichtung(w, art=None):
    d = _d(w)
    if d:
        d.seite_setzen(quer=(art == "quer"))
        w.status("Seite: %s." % ("Querformat" if art == "quer" else "Hochformat"))


PAPIERNAMEN = [("a4", "A4 — 210 × 297 mm"), ("a3", "A3 — 297 × 420 mm"), ("a5", "A5 — 148 × 210 mm"),
               ("b5", "B5 — 176 × 250 mm"), ("letter", "Letter — 216 × 279 mm"), ("legal", "Legal — 216 × 356 mm"),
               ("dinlang", "Umschlag DIN lang — 220 × 110 mm"), ("c5", "Umschlag C5 — 229 × 162 mm"),
               ("c6", "Umschlag C6 — 162 × 114 mm")]


@klappe("papier_klappe")
def _papier(w, pop):
    d = _d(w)
    eintr = [(t, (lambda k=k: d.seite_setzen(papier=k))) for k, t in PAPIERNAMEN]
    eintr += ["-", ("Weitere Papierformate …", lambda: _papier_frei(w))]
    return hilfen.liste(pop, eintr)


def _papier_frei(w):
    d = _d(w)
    if not d:
        return

    def ok(v):
        b, h = hilfen.zahl(v[0], 210), hilfen.zahl(v[1], 297)
        if b < 50 or h < 50:
            return
        d.PAPIER["eigen"] = (b, h)
        d.seite_setzen(papier="eigen")
    hilfen.frage(w, "Papierformat", [("Breite (mm)", "210"), ("Höhe (mm)", "297")], ok)


@befehl("spalten_setzen")
def _spalten(w, n=1):
    d = _d(w)
    if d:
        d.seite_setzen(spalten=int(n or 1))
        w.status("Spalten werden beim Export und Druck berücksichtigt; in der Bearbeitungsansicht läuft der Text einspaltig.")


@befehl("spalten_mehr")
def _spalten_mehr(w, _=None):
    hilfen.frage(w, "Spalten", [("Anzahl", "2")], lambda v: _spalten(w, max(1, min(6, int(hilfen.zahl(v[0], 2))))))


@klappe("textrichtung_klappe")
def _textrichtung(w, pop):
    d = _d(w)

    def setze(rtl):
        d.ansicht.set_direction(Gtk.TextDirection.RTL if rtl else Gtk.TextDirection.LTR)
        d.puffer.set_modified(True)
    return hilfen.liste(pop, [("Links nach rechts", lambda: setze(False)), ("Rechts nach links", lambda: setze(True))])


@befehl("spaltenumbruch")
def _spaltenumbruch(w, _=None):
    from .einfuegen import _seitenumbruch
    _seitenumbruch(w)


@befehl("textflussumbruch")
def _textfluss_umbruch(w, _=None):
    d = _d(w)
    if d:
        d.text_einfuegen(" ")


@befehl("abschnittsumbruch")
def _abschnitt(w, art="NextPage"):
    d = _d(w)
    if not d:
        return
    if art in ("NextPage", "OddPage", "EvenPage"):
        from .einfuegen import _seitenumbruch
        _seitenumbruch(w)
        return
    d.puffer.begin_user_action()
    it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
    if not it.starts_line():
        d.puffer.insert(it, "\n")
    d.text_einfuegen("──── Abschnittsumbruch (fortlaufend) ────\n", ("al-center", "umbruch"))
    d.puffer.end_user_action()


@klappe("zeilennummern_klappe")
def _zeilennr(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [("Keine", lambda: d.zeilennummern(False)),
                              ("Fortlaufend", lambda: d.zeilennummern(True))])


# ================================================================ Absatz
@befehl("absatzabstand")
def _absatzabstand(w, _=None):
    d = _d(w)
    if not d:
        return

    def ok(v):
        vor, nach = hilfen.zahl(v[0]), hilfen.zahl(v[1])
        a, b = d._zeilen()
        for n in range(a, b + 1):
            _, von = d.puffer.get_iter_at_line(n)
            bis = von.copy()
            if not bis.ends_line():
                bis.forward_to_line_end()
            bis.forward_char()
            for t in html_io.absatz_namen(d.puffer):
                if t.startswith("abs:"):
                    d.puffer.remove_tag_by_name(t, von, bis)
            if vor or nach:
                name = "abs:%g:%g" % (vor, nach)
                tag = d.puffer.get_tag_table().lookup(name) or d.puffer.create_tag(
                    name, pixels_above_lines=int(vor * 1.33), pixels_below_lines=int(nach * 1.33))
                d.puffer.apply_tag(tag, von, bis)
        d.puffer.set_modified(True)
    hilfen.frage(w, "Absatzabstand", [("Vor dem Absatz (pt)", "0"), ("Nach dem Absatz (pt)", "8")], ok)


@befehl("silbentrennung")
def _silbentrennung(w, _=None):
    d = _d(w)
    if not d:
        return
    an = w.schalten("silbentrennung")
    puf = d.puffer
    text = d.text()
    n = 0
    puf.begin_user_action()
    if not an:
        # weiche Trennstriche entfernen (von hinten, damit die Stellen stimmen)
        for i in [i for i, c in enumerate(text) if c == "\u00ad"][::-1]:
            puf.delete(puf.get_iter_at_offset(i), puf.get_iter_at_offset(i + 1))
            n += 1
    else:
        sprache = w.werte.get("sprache", "de_DE")
        for m in reversed(list(sprachdienste.WORT.finditer(text))):
            alt = m.group(0)
            neu = sprachdienste.mit_trennung(alt, sprache)
            if neu == alt:
                continue
            for i in reversed([i for i, c in enumerate(neu) if c == "\u00ad"]):
                pos = m.start() + i - neu[:i].count("\u00ad")
                # Stelle in der Originalschreibweise: Zeichen davor ohne Striche zählen
                pos = m.start() + len(neu[:i].replace("\u00ad", ""))
                a_ = puf.get_iter_at_offset(pos)
                tags = [t.props.name for t in a_.get_tags() if t.props.name not in ("zoom", "grund")]
                puf.insert(a_, "\u00ad")
                for t in tags:
                    puf.apply_tag(html_io.tag_holen(puf, t), puf.get_iter_at_offset(pos), puf.get_iter_at_offset(pos + 1))
            n += 1
    puf.end_user_action()
    w.status("Silbentrennung %s (%d %s)." % ("ein" if an else "aus", n, "Wörter" if an else "Striche entfernt"))


# ================================================================ Seitenhintergrund
@klappe("seitenfarbe")
def _seitenfarbe(w, pop):
    d = _d(w)
    return hilfen.farbwahl(pop, ["#FFFFFF", "#FFF8E1", "#F5F0E6", "#E8F1FA", "#E9F5EC", "#F4E9F5", "#FDE9E9", "#EEEEEE",
                                 "#333333", "#1F2225"], lambda f: d.seite_setzen(seitenfarbe=f or "#FFFFFF"), "Keine Farbe (weiß)")


@befehl("wasserzeichen")
def _wasserzeichen(w, _=None):
    d = _d(w)
    if not d:
        return
    aktuell = d.seite.get("wasserzeichen") or {}

    def ok(v):
        text = v[0].strip()
        d.seite_setzen(wasserzeichen=({"text": text, "farbe": v[1] or "#999999", "groesse": int(hilfen.zahl(v[2], 110)),
                                       "deckkraft": 0.22, "diagonal": True} if text else None))
    hilfen.frage(w, "Wasserzeichen", [("Text (leer = entfernen)", aktuell.get("text", "ENTWURF")),
                                      ("Farbe", aktuell.get("farbe", "#999999")),
                                      ("Größe", aktuell.get("groesse", 110))], ok)


@befehl("seitenraender_rahmen")
def _seitenrahmen(w, _=None):
    d = _d(w)
    if not d:
        return
    aktuell = d.seite.get("rahmen") or {}

    arten = [("solid", "durchgezogen"), ("double", "doppelt"), ("dashed", "gestrichelt"), ("dotted", "gepunktet")]
    breiten = ["kein Rahmen", "1", "2", "3", "4", "6"]

    def ok(v):
        if v[0] == 0:
            d.seite_setzen(rahmen=None)
        else:
            d.seite_setzen(rahmen={"breite": int(breiten[v[0]]), "farbe": v[2], "stil": arten[v[1]][0]})
    start_b = breiten.index(str(aktuell.get("breite"))) if str(aktuell.get("breite")) in breiten else 0
    start_a = [a for a, _n in arten].index(aktuell.get("stil", "solid")) if aktuell.get("stil", "solid") in [a for a, _n in arten] else 0
    hilfen.auswahl_fenster(w, "Seitenrahmen",
                           [("Breite (px)", "wahl", breiten, start_b), ("Linie", "wahl", [n for _a, n in arten], start_a),
                            ("Farbe", "farbe", aktuell.get("farbe", "#000000"))], ok)


# ================================================================ Anordnen (Objekte)
@klappe("objekt_ausrichten")
def _obj_ausrichten(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [("Links", lambda: d.absatz_setzen("al", None)),
                              ("Zentriert", lambda: d.absatz_setzen("al", "al-center")),
                              ("Rechts", lambda: d.absatz_setzen("al", "al-right"))])


def _drehen(w, grad):
    d = _d(w)
    a = d.objekt_am_cursor() if d else None
    if a is None:
        return w.meldung("Kein Objekt gewählt", "Bild oder Grafik markieren (Zeichen davor markieren).")
    dat = a.daten
    if dat["typ"] == "bild":
        roh = base64.b64decode(dat["b64"])
        lader = GdkPixbuf.PixbufLoader()
        lader.write(roh)
        lader.close()
        pb = lader.get_pixbuf()
        winkel = {90: GdkPixbuf.PixbufRotation.CLOCKWISE, 180: GdkPixbuf.PixbufRotation.UPSIDEDOWN,
                  270: GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE}[grad]
        pb = pb.rotate_simple(winkel)
        ok, png = pb.save_to_bufferv("png", [], [])
        dat["b64"], dat["mime"] = base64.b64encode(png).decode(), "image/png"
        if grad in (90, 270):
            dat["breite"] = int(dat.get("breite", 400) * pb.get_width() / max(pb.get_height(), 1)) if False else dat["breite"]
    elif dat["typ"] == "svg":
        b, h = dat["breite"], dat["hoehe"]
        if grad in (90, 270):
            nb, nh = h, b
        else:
            nb, nh = b, h
        inner = dat["svg"].split(">", 1)[1].rsplit("</svg>", 1)[0]
        tr = {90: "translate(%d,0) rotate(90)" % nb, 180: "translate(%d,%d) rotate(180)" % (nb, nh),
              270: "translate(0,%d) rotate(270)" % nh}[grad]
        dat["svg"] = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><g transform="%s">%s</g></svg>'
                      % (nb, nh, nb, nh, tr, inner))
        dat["breite"], dat["hoehe"] = nb, nh
    else:
        return w.meldung("Drehen", "Nur Bilder und Grafiken lassen sich drehen.")
    d.objekt_neu_zeichnen(a)


@klappe("objekt_drehen")
def _obj_drehen(w, pop):
    return hilfen.liste(pop, [("Um 90° nach rechts drehen", lambda: _drehen(w, 90)),
                              ("Um 90° nach links drehen", lambda: _drehen(w, 270)),
                              ("Um 180° drehen", lambda: _drehen(w, 180))])


@befehl("anordnen")
def _anordnen(w, _=None):
    d = _d(w)
    a = d.objekt_am_cursor() if d else None
    if a is None:
        return w.meldung("Textfluss", "Kein Objekt gewählt.")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Objektbreite")
    dlg.set_detail("Breite in Pixeln ändern (Bilder und Grafiken behalten ihr Seitenverhältnis).")

    def ok(v):
        b = int(hilfen.zahl(v[0], a.daten.get("breite", 300)))
        if a.daten["typ"] in ("bild", "svg") and b > 10:
            verh = a.daten.get("hoehe", b) / max(a.daten.get("breite", b), 1) if a.daten["typ"] == "svg" else None
            a.daten["breite"] = b
            if verh:
                a.daten["hoehe"] = int(b * verh)
            d.objekt_neu_zeichnen(a)
        elif a.daten["typ"] == "textfeld":
            a.daten["breite"] = b
            d.objekt_neu_zeichnen(a)
    hilfen.frage(w, "Größe des Objekts", [("Breite (px)", a.daten.get("breite", 300))], ok)
