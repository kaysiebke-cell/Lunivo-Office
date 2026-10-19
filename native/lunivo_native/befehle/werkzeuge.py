"""Werkzeug-Reiter: Tabellen-, Bild-, Zeichen-, Diagramm-, SmartArt-, Gleichungs- und Kopf-/Fußzeilenwerkzeuge.
Sie wirken auf das, was gerade den Fokus hat (Tabellenzelle, gewähltes Objekt, Kopf- oder Fußzeile)."""
import re

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from . import befehl, klappe, hilfen
from .. import grafik, objekte


def _d(w):
    return w.dok()


# ================================================================ Tabellen
def _tab(w):
    d = _d(w)
    if d is None or d.tabelle_aktiv is None:
        return None
    anker, r, c = d.tabelle_aktiv
    return d, anker, r, c, anker.daten


def _neu_zeichnen(d, anker, r, c):
    d.objekt_neu_zeichnen(anker)
    z = anker.daten.get("_zellen", {})
    r = min(r, len(anker.daten["zellen"]) - 1)
    c = min(c, len(anker.daten["zellen"][0]) - 1)
    GLib.idle_add(lambda: (z.get((r, c)) and z[(r, c)].grab_focus()) and False)


def _tabelle_aktion(fn):
    def f(w, arg=None):
        t = _tab(w)
        if not t:
            return w.status("Cursor in eine Tabellenzelle setzen.")
        d, anker, r, c, daten = t
        r2, c2 = fn(daten, r, c, arg) or (r, c)
        _neu_zeichnen(d, anker, r2, c2)
    return f


def _zeile_oben(daten, r, c, _):
    daten["zellen"].insert(r, [""] * len(daten["zellen"][0]))
    return r, c


def _zeile_unten(daten, r, c, _):
    daten["zellen"].insert(r + 1, [""] * len(daten["zellen"][0]))
    return r + 1, c


def _spalte_links(daten, r, c, _):
    for z in daten["zellen"]:
        z.insert(c, "")
    return r, c


def _spalte_rechts(daten, r, c, _):
    for z in daten["zellen"]:
        z.insert(c + 1, "")
    return r, c + 1


def _zeile_weg(daten, r, c, _):
    if len(daten["zellen"]) > 1:
        daten["zellen"].pop(r)
    return max(r - 1, 0), c


def _spalte_weg(daten, r, c, _):
    if len(daten["zellen"][0]) > 1:
        for z in daten["zellen"]:
            z.pop(c)
    return r, max(c - 1, 0)


def _sortieren(daten, r, c, _):
    kopf = 1 if daten.get("kopf") else 0
    teil = daten["zellen"][kopf:]

    def schluessel(z):
        t = z[c].replace(",", ".")
        try:
            return (0, float(t), "")
        except ValueError:
            return (1, 0.0, z[c].casefold())
    teil.sort(key=schluessel)
    daten["zellen"][kopf:] = teil
    return r, c


def _kopfzeile(daten, r, c, _):
    daten["kopf"] = not daten.get("kopf", False)


def _rahmen(daten, r, c, _):
    daten["rand"] = not daten.get("rand", True)


def _ausrichten(daten, r, c, art):
    daten["ausr"] = art or "links"


for _n, _f in (("tabelle_zeile_oben", _zeile_oben), ("tabelle_zeile_unten", _zeile_unten),
               ("tabelle_spalte_links", _spalte_links), ("tabelle_spalte_rechts", _spalte_rechts),
               ("tabelle_zeile_weg", _zeile_weg), ("tabelle_spalte_weg", _spalte_weg),
               ("tabelle_sortieren", _sortieren), ("tabelle_kopfzeile", _kopfzeile),
               ("tabelle_rahmen", _rahmen), ("tabelle_ausrichten", _ausrichten)):
    befehl(_n)(_tabelle_aktion(_f))


@befehl("tabelle_breite")
def _tabelle_breite(w, _=None):
    t = _tab(w)
    if not t:
        return w.status("Cursor in eine Tabellenzelle setzen.")
    d, anker, r, c, daten = t

    def ok(v):
        daten["breite_zeichen"] = max(3, int(hilfen.zahl(v[0], 10)))
        _neu_zeichnen(d, anker, r, c)
    hilfen.frage(w, "Spaltenbreite", [("Breite in Zeichen", daten.get("breite_zeichen", 10))], ok, "Gilt für alle Spalten der Tabelle.")


@befehl("tabelle_hoehe")
def _tabelle_hoehe(w, _=None):
    t = _tab(w)
    if not t:
        return w.status("Cursor in eine Tabellenzelle setzen.")
    d, anker, r, c, daten = t

    def ok(v):
        daten["zeilenhoehe"] = max(18, int(hilfen.zahl(v[0], 24)))
        _neu_zeichnen(d, anker, r, c)
    hilfen.frage(w, "Zeilenhöhe", [("Höhe in px", daten.get("zeilenhoehe", 24))], ok, "Gilt für alle Zeilen der Tabelle.")


@klappe("tabelle_kopffarbe")
def _kopffarbe(w, pop):
    t = _tab(w)
    if not t:
        return None
    d, anker, r, c, daten = t

    def setze(f):
        daten["kopffarbe"] = f or "#D9E2F3"
        _neu_zeichnen(d, anker, r, c)
    return hilfen.farbwahl(pop, ["#D9E2F3", "#F3DDD6", "#DDEFE6", "#FFE08A", "#E6E6E6", "#CFE3F7", "#FFFFFF", "#B6D7A8"], setze, "Standard")


@befehl("tabelle_weg")
def _tabelle_weg(w, _=None):
    t = _tab(w)
    if not t:
        return w.status("Cursor in eine Tabelle setzen.")
    d, anker = t[0], t[1]
    _objekt_loeschen(d, anker)


# ================================================================ Objekte allgemein
def _objekt(w):
    d = _d(w)
    a = d.objekt_am_cursor() if d else None
    return d, a


def _objekt_loeschen(d, anker):
    for a, offset in d.alle_objekte():
        if a is anker:
            w_ = getattr(anker, "widget", None)
            # Der Rückgängig-Verlauf von GTK kann einen Child-Anker nicht wiederherstellen; er ruht für diesen Schnitt.
            d.puffer.set_enable_undo(False)
            d._sperre = True                              # Cursor-Signale ruhen, während der Anker verschwindet
            try:
                d.puffer.delete(d.puffer.get_iter_at_offset(offset), d.puffer.get_iter_at_offset(offset + 1))
            finally:
                d._sperre = False
                d.puffer.set_enable_undo(True)
            d.puffer.set_modified(True)
            d.tabelle_aktiv = None
            d.emit("format-stand")
            return True
    return False


@befehl("objekt_weg")
def _objekt_weg(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return w.status("Kein Objekt gewählt.")
    _objekt_loeschen(d, a)


# ================================================================ Bilder
@befehl("bild_breite")
def _bild_breite(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return

    def ok(v):
        b = int(hilfen.zahl(v[0], a.daten.get("breite", 300)))
        if b < 16:
            return
        verh = (a.daten.get("hoehe", b) / max(a.daten.get("breite", b), 1)) if a.daten["typ"] == "svg" else None
        a.daten["breite"] = b
        if verh:
            a.daten["hoehe"] = int(b * verh)
        d.objekt_neu_zeichnen(a)
    hilfen.frage(w, "Breite des Bildes", [("Breite (px)", a.daten.get("breite", 300))], ok)


@befehl("bild_original")
def _bild_original(w, _=None):
    d, a = _objekt(w)
    if a is None or a.daten["typ"] != "bild":
        return
    import base64
    t = objekte.textur_aus_bytes(base64.b64decode(a.daten["b64"]), a.daten["mime"] == "image/svg+xml")
    a.daten["breite"] = t.get_width()
    d.objekt_neu_zeichnen(a)


@befehl("bild_alt")
def _bild_alt(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return

    def ok(v):
        a.daten["alt"] = v[0]
        d.puffer.set_modified(True)
        w.status("Alternativtext gesetzt.")
    hilfen.frage(w, "Alternativtext", [("Beschreibung", a.daten.get("alt", ""))], ok,
                 "Beschreibt das Bild für alle, die es nicht sehen können (Barrierefreiheit).")


# ================================================================ Zeichnungen, Diagramme, SmartArt, Gleichungen
def _svg_neu(d, a, svg, b=None, h=None):
    a.daten["svg"] = svg
    if b:
        a.daten["breite"], a.daten["hoehe"] = b, h
    d.objekt_neu_zeichnen(a)


def _form_neu(a, **kw):
    q = a.daten.setdefault("quelle", {})
    q.update(kw)
    q.setdefault("fuell", "#2F6FB5")
    q.setdefault("rand", "#1B4A80")
    q.setdefault("form", "Rechteck")
    return grafik.form(q["form"], q["fuell"], q["rand"], a.daten.get("breite", 160), a.daten.get("hoehe", 100), q.get("text", ""))


@klappe("zeichen_form")
def _zeichen_form(w, pop):
    d, a = _objekt(w)
    if a is None or a.daten["typ"] != "svg":
        return None
    return hilfen.liste(pop, [(n, (lambda n=n: _svg_neu(d, a, _form_neu(a, form=n)))) for n in grafik.FORMEN])


def _farbklappe(schluessel):
    def f(w, pop):
        d, a = _objekt(w)
        if a is None:
            return None
        if a.daten["typ"] == "textfeld":
            feld = "farbe" if schluessel == "fuell" else "rahmen"

            def setze(c):
                a.daten[feld] = c or ""
                d.objekt_neu_zeichnen(a)
            return hilfen.farbwahl(pop, hilfen.FARBEN, setze, "Keine Füllung" if feld == "farbe" else "Kein Rahmen")
        if a.daten["typ"] != "svg":
            return None
        return hilfen.farbwahl(pop, hilfen.FARBEN, lambda c: _svg_neu(d, a, _form_neu(a, **{schluessel: c or "#2F6FB5"})))
    return f


klappe("zeichen_fuellung")(_farbklappe("fuell"))
klappe("zeichen_rand")(_farbklappe("rand"))


@befehl("zeichen_groesse")
def _zeichen_groesse(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return

    def ok(v):
        b, h = int(hilfen.zahl(v[0], 160)), int(hilfen.zahl(v[1], 100))
        a.daten["breite"], a.daten["hoehe"] = b, h
        if a.daten["typ"] == "svg":
            _svg_neu(d, a, _form_neu(a), b, h)
        else:
            d.objekt_neu_zeichnen(a)
    hilfen.frage(w, "Größe", [("Breite (px)", a.daten.get("breite", 160)), ("Höhe (px)", a.daten.get("hoehe", 100))], ok)


def _diagramm_lesen(q):
    return q.get("kopf", ["Reihe"]), q.get("daten", [["A", 1]]), q.get("titel", "")


@befehl("diagramm_art")
def _diagramm_art(w, art=None):
    d, a = _objekt(w)
    if a is None:
        return
    q = a.daten.setdefault("quelle", {})
    q["diagramm"] = art or "saeulen"
    kopf, daten, titel = _diagramm_lesen(q)
    _svg_neu(d, a, grafik.diagramm(q["diagramm"], kopf, daten, titel))


@befehl("diagramm_titel")
def _diagramm_titel(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return
    q = a.daten.setdefault("quelle", {})

    def ok(v):
        q["titel"] = v[0]
        kopf, daten, titel = _diagramm_lesen(q)
        _svg_neu(d, a, grafik.diagramm(q.get("diagramm", "saeulen"), kopf, daten, titel))
    hilfen.frage(w, "Titel des Diagramms", [("Titel", q.get("titel", ""))], ok)


@befehl("diagramm_daten")
def _diagramm_daten(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return
    q = a.daten.setdefault("quelle", {})
    kopf, daten, titel = _diagramm_lesen(q)
    dlg = Gtk.Window(transient_for=w, modal=True, title="Diagrammdaten")
    dlg.set_default_size(480, 360)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Erste Zeile: Reihennamen. Danach je Zeile: Kategorie; Zahl; Zahl …", xalign=0, wrap=True))
    tv = Gtk.TextView(monospace=True)
    tv.get_buffer().set_text(";" + ";".join(kopf) + "\n" + "\n".join(";".join(str(x) for x in z) for z in daten))
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(tv)
    box.append(rolle)

    def ok(*_):
        b = tv.get_buffer()
        zeilen = [z for z in b.get_text(b.get_start_iter(), b.get_end_iter(), False).split("\n") if z.strip()]
        teile = [[t.strip() for t in re.split(r"[;\t]", z)] for z in zeilen]
        try:
            k2 = teile[0][1:]
            d2 = [[t[0]] + [hilfen.zahl(x) for x in t[1:len(k2) + 1]] for t in teile[1:]]
        except Exception as e:
            return w.meldung("Daten nicht lesbar", str(e))
        q["kopf"], q["daten"] = k2, d2
        _svg_neu(d, a, grafik.diagramm(q.get("diagramm", "saeulen"), k2, d2, q.get("titel", "")))
        dlg.close()
    gut = Gtk.Button(label="Übernehmen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


@befehl("smartart_text")
def _smartart_text(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return
    q = a.daten.setdefault("quelle", {})
    dlg = Gtk.Window(transient_for=w, modal=True, title="SmartArt-Text")
    dlg.set_default_size(380, 300)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Ein Eintrag pro Zeile:", xalign=0))
    tv = Gtk.TextView()
    tv.get_buffer().set_text("\n".join(q.get("eintraege", ["Eins", "Zwei", "Drei"])))
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(tv)
    box.append(rolle)

    def ok(*_):
        b = tv.get_buffer()
        q["eintraege"] = [z.strip() for z in b.get_text(b.get_start_iter(), b.get_end_iter(), False).split("\n") if z.strip()]
        _svg_neu(d, a, grafik.smartart(q.get("smartart", "Liste"), q["eintraege"]))
        dlg.close()
    gut = Gtk.Button(label="Übernehmen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


@befehl("smartart_layout")
def _smartart_layout(w, art=None):
    d, a = _objekt(w)
    if a is None:
        return
    q = a.daten.setdefault("quelle", {})
    q["smartart"] = art or "Liste"
    _svg_neu(d, a, grafik.smartart(q["smartart"], q.get("eintraege", ["Eins", "Zwei", "Drei"])))


@befehl("gleichung_bearbeiten")
def _gleichung(w, _=None):
    d, a = _objekt(w)
    if a is None:
        return
    q = a.daten.setdefault("quelle", {})

    def ok(v):
        try:
            svg, b, h = grafik.formel(v[0])
        except Exception as e:
            return w.meldung("Formel nicht lesbar", str(e))
        q["formel"] = v[0]
        _svg_neu(d, a, svg, b, h)
    hilfen.frage(w, "Formel", [("LaTeX", q.get("formel", ""))], ok, "z. B.  x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}")


# ================================================================ Kopf- und Fußzeile
def _rand_buffer(w):
    d = _d(w)
    tv = d.kopf if d and d.rand_aktiv == "kopf" else d.fuss if d else None
    return d, tv


@befehl("kf_seitenzahl")
def _kf_seitenzahl(w, _=None):
    d, tv = _rand_buffer(w)
    if tv is not None:
        tv.get_buffer().insert_at_cursor("{Seite}")


@befehl("kf_seiten")
def _kf_seiten(w, _=None):
    d, tv = _rand_buffer(w)
    if tv is not None:
        tv.get_buffer().insert_at_cursor("Seite {Seite} von {Seiten}")


@befehl("kf_datum")
def _kf_datum(w, _=None):
    import datetime
    d, tv = _rand_buffer(w)
    if tv is not None:
        tv.get_buffer().insert_at_cursor(datetime.date.today().strftime("%d.%m.%Y"))


@befehl("kf_kopf_weg")
def _kf_kopf_weg(w, _=None):
    d = _d(w)
    if d:
        d.kopf.get_buffer().set_text("")
        d.kopf_fuss_zeigen(False, None)
        d.rand_aktiv = None
        d.emit("format-stand")


@befehl("kf_fuss_weg")
def _kf_fuss_weg(w, _=None):
    d = _d(w)
    if d:
        d.fuss.get_buffer().set_text("")
        d.kopf_fuss_zeigen(None, False)
        d.rand_aktiv = None
        d.emit("format-stand")


@befehl("kf_schliessen")
def _kf_schliessen(w, _=None):
    d = _d(w)
    if d:
        d.rand_aktiv = None
        d.ansicht.grab_focus()
        d.emit("format-stand")
