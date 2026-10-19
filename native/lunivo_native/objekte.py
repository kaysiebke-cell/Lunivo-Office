"""Eingebettete Objekte im Text: Tabellen, Bilder, Vektorgrafiken (Formen, Diagramme …), Textfelder.

Jedes Objekt ist ein Wörterbuch (`daten`) mit "typ". Im Puffer steht an seiner Stelle ein
Child-Anker (Zeichen U+FFFC); das Widget baut `widget_bauen`, die HTML-Form `als_html`."""
import base64
import html
import re

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib  # noqa: E402

OBJ = "￼"


# ------------------------------------------------------------------ Bilder
def textur_aus_bytes(roh, svg=False):
    lader = GdkPixbuf.PixbufLoader.new_with_type("svg") if svg else GdkPixbuf.PixbufLoader()
    lader.write(roh)
    lader.close()
    return Gdk.Texture.new_for_pixbuf(lader.get_pixbuf())


def bild_daten(pfad, maxbreite=520):
    with open(pfad, "rb") as f:
        roh = f.read()
    svg = pfad.lower().endswith(".svg")
    mime = "image/svg+xml" if svg else {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                                         "gif": "image/gif", "bmp": "image/bmp", "webp": "image/webp"}.get(
        pfad.rsplit(".", 1)[-1].lower(), "image/png")
    t = textur_aus_bytes(roh, svg)
    b = min(t.get_width(), maxbreite)
    return {"typ": "bild", "b64": base64.b64encode(roh).decode(), "mime": mime, "breite": b,
            "alt": pfad.rsplit("/", 1)[-1]}


def svg_daten(svg_text, breite, hoehe, quelle=None, alt=""):
    return {"typ": "svg", "svg": svg_text, "breite": breite, "hoehe": hoehe, "quelle": quelle or {}, "alt": alt}


def tabelle_daten(zeilen, spalten, text=None):
    return {"typ": "tabelle", "zellen": text or [["" for _ in range(spalten)] for _ in range(zeilen)],
            "rand": True, "kopf": True, "kopffarbe": "#D9E2F3", "ausr": "links"}


def textfeld_daten(text="Textfeld", farbe="#FFFFFF", rahmen="#444444"):
    return {"typ": "textfeld", "text": text, "farbe": farbe, "rahmen": rahmen, "breite": 260}


# ------------------------------------------------------------------ Widgets
def widget_bauen(daten, geaendert=None, fokus=None):
    """Baut das Widget zu `daten`. `geaendert()` wird gerufen, wenn der Inhalt sich ändert."""
    typ = daten["typ"]
    meld = geaendert or (lambda: None)
    if typ == "bild":
        t = textur_aus_bytes(base64.b64decode(daten["b64"]), daten["mime"] == "image/svg+xml")
        return _bild_widget(t, daten)
    if typ == "svg":
        t = textur_aus_bytes(daten["svg"].encode("utf-8"), True)
        return _bild_widget(t, daten, daten.get("breite"), daten.get("hoehe"))
    if typ == "tabelle":
        return _tabelle_widget(daten, meld, fokus)
    if typ == "textfeld":
        return _textfeld_widget(daten, meld)
    if typ == "form_text":
        e = Gtk.Entry(text=daten.get("wert", ""), placeholder_text=daten.get("name", "Text"), width_chars=daten.get("breite", 24))
        e.set_tooltip_text(daten.get("name", ""))
        e.connect("changed", lambda en: (daten.__setitem__("wert", en.get_text()), meld()))
        return e
    if typ == "form_kasten":
        c = Gtk.CheckButton(label=daten.get("name", "Kontrollkästchen"), active=bool(daten.get("an")))
        c.connect("toggled", lambda cb: (daten.__setitem__("an", cb.get_active()), meld()))
        return c
    if typ == "form_knopf":
        b = Gtk.Button(label=daten.get("name", "Schaltfläche"))
        b.set_halign(Gtk.Align.START)
        b.connect("clicked", lambda _b: daten.get("klick") and daten["klick"]())
        return b
    return Gtk.Label(label="[Objekt]")


def _bild_widget(textur, daten, b=None, h=None):
    p = Gtk.Picture.new_for_paintable(textur)
    p.set_can_shrink(True)
    p.set_content_fit(Gtk.ContentFit.CONTAIN)
    breite = int(b or daten.get("breite") or textur.get_width())
    verh = textur.get_height() / max(textur.get_width(), 1)
    hoehe = int(h or breite * verh)
    p.set_size_request(breite, hoehe)
    p.set_tooltip_text(daten.get("alt", ""))
    p.set_halign(Gtk.Align.START)
    return p


def _tabelle_widget(daten, meld, fokus=None):
    gitter = Gtk.Grid()
    gitter.add_css_class("lunivo-tabelle")
    gitter.set_row_spacing(0)
    gitter.set_column_spacing(0)
    daten["_zellen"] = {}
    css = Gtk.CssProvider()
    rand = "1px solid #444" if daten.get("rand", True) else "1px solid transparent"
    css.load_from_string("entry.zelle { background: #FFFFFF; color: #111417; border: %s; border-radius: 0; "
                         "min-height: %dpx; padding: 2px 6px; box-shadow: none; outline: none; }"
                         "entry.zelle.kopf { background: %s; font-weight: bold; }" % (rand, int(daten.get("zeilenhoehe", 24)), daten.get("kopffarbe", "#D9E2F3")))
    for r, zeile in enumerate(daten["zellen"]):
        for c, text in enumerate(zeile):
            e = Gtk.Entry(text=text, hexpand=True)
            e.set_width_chars(int(daten.get("breite_zeichen", 10)))
            e.add_css_class("zelle")
            if r == 0 and daten.get("kopf"):
                e.add_css_class("kopf")
            e.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            e.set_alignment({"links": 0.0, "mitte": 0.5, "rechts": 1.0}.get(daten.get("ausr", "links"), 0.0))
            e.connect("changed", lambda en, r=r, c=c: (daten["zellen"][r].__setitem__(c, en.get_text()), meld()))
            if fokus:
                fc = Gtk.EventControllerFocus()
                fc.connect("enter", lambda *_a, r=r, c=c: fokus(r, c))
                e.add_controller(fc)
            gitter.attach(e, c, r, 1, 1)
            daten["_zellen"][(r, c)] = e
    gitter.set_halign(Gtk.Align.START)
    return gitter


def _textfeld_widget(daten, meld):
    rahmen = Gtk.Frame()
    tv = Gtk.TextView()
    tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    tv.get_buffer().set_text(daten.get("text", ""))
    tv.set_size_request(daten.get("breite", 260), 60)
    tv.set_left_margin(6)
    tv.set_right_margin(6)
    tv.set_top_margin(4)
    tv.set_bottom_margin(4)
    css = Gtk.CssProvider()
    css.load_from_string("textview.textfeld, textview.textfeld text { background: %s; color: #111417; }"
                         "frame.textfeld { border: %s; }" % (daten.get("farbe") or "transparent",
                                                             ("1px solid " + daten["rahmen"]) if daten.get("rahmen", "#444444") else "none"))
    tv.add_css_class("textfeld")
    rahmen.add_css_class("textfeld")
    for w in (tv, rahmen):
        w.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    tv.get_buffer().connect("changed", lambda b: (daten.__setitem__("text", b.get_text(b.get_start_iter(), b.get_end_iter(), False)), meld()))
    rahmen.set_child(tv)
    rahmen.set_halign(Gtk.Align.START)
    return rahmen


# ------------------------------------------------------------------ HTML
def als_html(daten):
    typ = daten["typ"]
    if typ == "bild":
        return '<img src="data:%s;base64,%s" width="%d" alt="%s">' % (
            daten["mime"], daten["b64"], daten.get("breite", 400), html.escape(daten.get("alt", ""), quote=True))
    if typ == "svg":
        b64 = base64.b64encode(daten["svg"].encode("utf-8")).decode()
        quelle = html.escape(_json(daten.get("quelle", {})), quote=True)
        return '<img src="data:image/svg+xml;base64,%s" width="%d" height="%d" alt="%s" data-lunivo="%s">' % (
            b64, daten.get("breite", 300), daten.get("hoehe", 200), html.escape(daten.get("alt", ""), quote=True), quelle)
    if typ == "tabelle":
        zeilen = []
        for r, zeile in enumerate(daten["zellen"]):
            zellen = []
            for c, t in enumerate(zeile):
                tag = "th" if (r == 0 and daten.get("kopf")) else "td"
                st = ""
                if tag == "th":
                    st = ' style="background-color:%s"' % daten.get("kopffarbe", "#D9E2F3")
                zellen.append("<%s%s>%s</%s>" % (tag, st, html.escape(t), tag))
            zeilen.append("<tr>%s</tr>" % "".join(zellen))
        rand = ' border="1"' if daten.get("rand", True) else ' border="0"'
        return '<table%s cellpadding="4" cellspacing="0" data-ausr="%s">%s</table>' % (
            rand, daten.get("ausr", "links"), "".join(zeilen))
    if typ == "textfeld":
        return '<div class="textfeld" style="border:%s;background-color:%s;width:%dpx;padding:4px">%s</div>' % (
            ("1px solid " + daten["rahmen"]) if daten.get("rahmen", "#444") else "none", daten.get("farbe") or "transparent", daten.get("breite", 260),
            html.escape(daten.get("text", "")).replace("\n", "<br>"))
    if typ == "form_text":
        return '<input type="text" name="%s" value="%s" size="%d">' % (
            html.escape(daten.get("name", ""), quote=True), html.escape(daten.get("wert", ""), quote=True), daten.get("breite", 24))
    if typ == "form_kasten":
        return '<input type="checkbox" name="%s"%s> %s' % (html.escape(daten.get("name", ""), quote=True),
                                                           " checked" if daten.get("an") else "", html.escape(daten.get("name", "")))
    if typ == "form_knopf":
        return '<input type="button" value="%s">' % html.escape(daten.get("name", ""), quote=True)
    return ""


def _json(o):
    import json
    return json.dumps(o, ensure_ascii=False, separators=(",", ":"))


def aus_img_attr(attr):
    """<img>-Attribute (dict) -> daten oder None."""
    src = attr.get("src", "")
    m = re.match(r"data:([\w/+.-]+);base64,(.*)", src, re.S)
    if not m:
        return None
    mime, b64 = m.group(1), m.group(2)
    breite = int(float(re.sub(r"[^\d.]", "", attr.get("width", "0")) or 0)) or 0
    if mime == "image/svg+xml":
        try:
            svg = base64.b64decode(b64).decode("utf-8")
        except Exception:
            return None
        import json
        quelle = {}
        if attr.get("data-lunivo"):
            try:
                quelle = json.loads(attr["data-lunivo"])
            except ValueError:
                pass
        hoehe = int(float(re.sub(r"[^\d.]", "", attr.get("height", "0")) or 0)) or 0
        return svg_daten(svg, breite or 300, hoehe or 200, quelle, attr.get("alt", ""))
    return {"typ": "bild", "b64": b64.strip(), "mime": mime, "breite": breite or 400, "alt": attr.get("alt", "")}
