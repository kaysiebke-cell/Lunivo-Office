"""HTML <-> Gtk.TextBuffer.

Das Dokument liegt im Fenster als formatierter Text (Gtk.TextBuffer mit Tags)
und auf der Platte als HTML. HTML, weil das Programm bisher so gespeichert
hat und LibreOffice es lesen und schreiben kann (docx, odt, pdf).

Tag-Namen (so heißen die Tags im Puffer):
  b i u s            fett, kursiv, unterstrichen, durchgestrichen
  h1 h2 h3           Überschriften
  al-center  al-right  al-justify      Absatzausrichtung (links ist Vorgabe)
  fam:NAME           Schriftart
  size:N             Größe in Punkt
  col:#rrggbb        Schriftfarbe
"""

import html
import re
from html.parser import HTMLParser

from . import objekte as _obj

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Pango, Gdk  # noqa: E402

_ABSATZ_FEST = {"h1", "h2", "h3", "al-center", "al-right", "al-justify", "al-distribute"}
_ABSATZ_VORSATZ = ("ein:", "ers:", "rei:", "zl:", "sch:", "st:", "abs:", "rahmen:", "rtl")


class _AbsatzTags:
    """Menge aller Tags, die für den ganzen Absatz gelten."""
    def __contains__(self, name):
        return name in _ABSATZ_FEST or (isinstance(name, str) and name.startswith(_ABSATZ_VORSATZ))

    def __iter__(self):
        return iter(_ABSATZ_FEST)


ABSATZ_TAGS = _AbsatzTags()


def absatz_namen(puffer):
    """Die im Puffer vorhandenen Absatz-Tags."""
    namen = []
    puffer.get_tag_table().foreach(lambda t, _: namen.append(t.props.name) if t.props.name in ABSATZ_TAGS else None, None)
    return namen


STILE = {
    # Name: (Pango-Eigenschaften für den Tag, HTML-Element)
    "Fließtext": None,
    "Titel": ({"weight": Pango.Weight.BOLD, "scale": 2.2, "pixels_below_lines": 6}, "h1"),
    "Untertitel": ({"scale": 1.4, "style": Pango.Style.ITALIC, "pixels_below_lines": 6}, "p"),
    "Überschrift 1": ({"weight": Pango.Weight.BOLD, "scale": 1.8, "pixels_above_lines": 10, "pixels_below_lines": 4}, "h1"),
    "Überschrift 2": ({"weight": Pango.Weight.BOLD, "scale": 1.45, "pixels_above_lines": 8, "pixels_below_lines": 3}, "h2"),
    "Überschrift 3": ({"weight": Pango.Weight.BOLD, "scale": 1.2, "pixels_above_lines": 6, "pixels_below_lines": 2}, "h3"),
    "Zitat": ({"style": Pango.Style.ITALIC, "left_margin": 48, "right_margin": 48}, "blockquote"),
    "Code": ({"family": "monospace", "scale": 0.92}, "pre"),
    "Beschriftung": ({"scale": 0.85, "style": Pango.Style.ITALIC}, "p"),
    "Kein Abstand": ({"pixels_above_lines": 0, "pixels_below_lines": 0}, "p"),
}

# Eigene Formatvorlagen des Dokuments (Name -> Beschreibung); füllt der Editor beim Laden.
EIGENE_STILE = {}


def stil_eigenschaften(name):
    """Pango-Eigenschaften einer Vorlage (eingebaut oder eigen); eigene bauen auf ihrer Basis auf."""
    if name in EIGENE_STILE:
        s = EIGENE_STILE[name]
        eig = dict(stil_eigenschaften(s.get("basis", "Fließtext")))
        if s.get("fam"):
            eig["family"] = s["fam"]
        if s.get("groesse"):
            eig["size_points"] = float(s["groesse"])
        if s.get("fett"):
            eig["weight"] = Pango.Weight.BOLD
        if s.get("kursiv"):
            eig["style"] = Pango.Style.ITALIC
        if s.get("farbe"):
            c = Gdk.RGBA()
            c.parse(s["farbe"])
            eig["foreground_rgba"] = c
        if s.get("ausr") in ("center", "right", "justify"):
            eig["justification"] = {"center": Gtk.Justification.CENTER, "right": Gtk.Justification.RIGHT,
                                    "justify": Gtk.Justification.FILL}[s["ausr"]]
        if s.get("einzug"):
            eig["left_margin"] = int(s["einzug"])
        if s.get("vor") is not None:
            eig["pixels_above_lines"] = int(float(s["vor"]) * 1.33)
        if s.get("nach") is not None:
            eig["pixels_below_lines"] = int(float(s["nach"]) * 1.33)
        if s.get("zeilen"):
            eig["line_height"] = float(s["zeilen"])
        return eig
    eintrag = STILE.get(name)
    return dict(eintrag[0]) if eintrag else {}
ZEICHEN_TAGS_FEST = {"b", "i", "u", "s"}

BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "blockquote", "pre"}
UEBERSPRINGEN = {"style", "script", "head", "title"}


def zeichen_namen(puffer):
    """Die im Puffer vorhandenen Zeichen-Tags (alles, was nicht zum Absatz gehört)."""
    namen = []
    puffer.get_tag_table().foreach(
        lambda t, _: namen.append(t.props.name)
        if t.props.name and t.props.name not in ABSATZ_TAGS and t.props.name not in ("zoom", "grund", "steuer", "falsch", "dimm")
        else None, None)
    return namen


UL_PANGO = {"solid": Pango.Underline.SINGLE, "double": Pango.Underline.DOUBLE,
            "dotted": Pango.Underline.SINGLE, "dashed": Pango.Underline.SINGLE,
            "wavy": Pango.Underline.ERROR}


def tag_holen(puffer, name):
    """Gibt den Tag zurück, legt ihn bei Bedarf an."""
    tabelle = puffer.get_tag_table()
    tag = tabelle.lookup(name)
    if tag is not None:
        return tag
    if name == "b":
        tag = puffer.create_tag(name, weight=Pango.Weight.BOLD)
    elif name == "i":
        tag = puffer.create_tag(name, style=Pango.Style.ITALIC)
    elif name == "u":
        tag = puffer.create_tag(name, underline=Pango.Underline.SINGLE)
    elif name == "s":
        tag = puffer.create_tag(name, strikethrough=True)
    elif name == "h1":
        tag = puffer.create_tag(name, weight=Pango.Weight.BOLD, scale=1.8,
                                pixels_above_lines=10, pixels_below_lines=4)
    elif name == "h2":
        tag = puffer.create_tag(name, weight=Pango.Weight.BOLD, scale=1.45,
                                pixels_above_lines=8, pixels_below_lines=3)
    elif name == "h3":
        tag = puffer.create_tag(name, weight=Pango.Weight.BOLD, scale=1.2,
                                pixels_above_lines=6, pixels_below_lines=2)
    elif name == "al-center":
        tag = puffer.create_tag(name, justification=Gtk.Justification.CENTER)
    elif name == "al-right":
        tag = puffer.create_tag(name, justification=Gtk.Justification.RIGHT)
    elif name == "al-justify":
        tag = puffer.create_tag(name, justification=Gtk.Justification.FILL)
    elif name.startswith("fam:"):
        tag = puffer.create_tag(name, family=name[4:])
    elif name.startswith("size:"):
        tag = puffer.create_tag(name, size_points=float(name[5:]))
    elif name.startswith("col:"):
        farbe = Gdk.RGBA()
        if not farbe.parse(name[4:]):
            farbe.parse("#000000")
        tag = puffer.create_tag(name, foreground_rgba=farbe)
    elif name == "al-distribute":
        tag = puffer.create_tag(name, justification=Gtk.Justification.FILL)
    elif name == "hoch":
        tag = puffer.create_tag(name, rise=5 * Pango.SCALE, scale=0.72)
    elif name == "tief":
        tag = puffer.create_tag(name, rise=-3 * Pango.SCALE, scale=0.72)
    elif name == "umriss":
        tag = puffer.create_tag(name, underline=Pango.Underline.NONE, weight=Pango.Weight.HEAVY)
    elif name.startswith("ul:"):
        art, _, farbe = name[3:].partition(":")
        eig = {"underline": UL_PANGO.get(art, Pango.Underline.SINGLE)}
        rgba = Gdk.RGBA()
        if farbe and rgba.parse(farbe):
            eig["underline_rgba"] = rgba
        tag = puffer.create_tag(name, **eig)
    elif name == "eff:kapitael":
        tag = puffer.create_tag(name, variant=Pango.Variant.SMALL_CAPS)
    elif name == "eff:gesperrt":
        tag = puffer.create_tag(name, letter_spacing=2 * Pango.SCALE)
    elif name.startswith("hl:"):
        farbe = Gdk.RGBA()
        farbe.parse(name[3:])
        tag = puffer.create_tag(name, background_rgba=farbe)
    elif name.startswith("link:"):
        farbe = Gdk.RGBA()
        farbe.parse("#4A8FD8")
        tag = puffer.create_tag(name, foreground_rgba=farbe, underline=Pango.Underline.SINGLE)
    elif name.startswith("ein:"):
        tag = puffer.create_tag(name, left_margin=int(float(name[4:])), indent=0)
    elif name.startswith("ers:"):
        tag = puffer.create_tag(name, indent=int(float(name[4:])))
    elif name.startswith("rei:"):
        tag = puffer.create_tag(name, right_margin=int(float(name[4:])))
    elif name.startswith("zl:"):
        tag = puffer.create_tag(name, line_height=float(name[3:]))
    elif name.startswith("sch:"):
        farbe = Gdk.RGBA()
        farbe.parse(name[4:])
        tag = puffer.create_tag(name, paragraph_background_rgba=farbe)
    elif name.startswith("st:"):
        tag = puffer.create_tag(name, **stil_eigenschaften(name[3:]))
    elif name.startswith(("feld:", "regel:")):
        farbe = Gdk.RGBA()
        farbe.parse("#CFE3F7")
        tag = puffer.create_tag(name, background_rgba=farbe, foreground="#1B4A80")
    elif name.startswith(("marke:", "rahmen:")):
        tag = puffer.create_tag(name)
    elif name.startswith("kom:"):
        farbe = Gdk.RGBA()
        farbe.parse("#FFE08A")
        tag = puffer.create_tag(name, background_rgba=farbe)
    elif name == "ins":
        farbe = Gdk.RGBA()
        farbe.parse("#2E7D32")
        tag = puffer.create_tag(name, foreground_rgba=farbe, underline=Pango.Underline.SINGLE)
    elif name == "del":
        farbe = Gdk.RGBA()
        farbe.parse("#C62828")
        tag = puffer.create_tag(name, foreground_rgba=farbe, strikethrough=True)
    elif name == "falsch":
        farbe = Gdk.RGBA()
        farbe.parse("#E53935")
        tag = puffer.create_tag(name, underline=Pango.Underline.ERROR, underline_rgba=farbe)
    elif name == "dimm":
        farbe = Gdk.RGBA()
        farbe.parse("#9AA3AB")
        tag = puffer.create_tag(name, foreground_rgba=farbe)
    elif name == "steuer":
        tag = puffer.create_tag(name, show_spaces=Pango.ShowFlags.SPACES | Pango.ShowFlags.LINE_BREAKS)
    elif name == "umbruch":
        tag = puffer.create_tag(name, justification=Gtk.Justification.CENTER, foreground="#888888",
                                scale=0.8, editable=True)
    else:
        tag = puffer.create_tag(name)
    return tag


# ---------------------------------------------------------------- HTML lesen

_STIL = re.compile(r"([a-zA-Z-]+)\s*:\s*([^;]+)")


def _stile(attr):
    return {k.lower(): v.strip() for k, v in _STIL.findall(attr or "")}


def _rgb_zu_hex(wert):
    wert = wert.strip().lower()
    if wert.startswith("#") and len(wert) in (4, 7):
        if len(wert) == 4:
            return "#" + "".join(c * 2 for c in wert[1:])
        return wert
    m = re.match(r"rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)", wert)
    if m:
        return "#%02x%02x%02x" % tuple(int(x) for x in m.groups())
    return None


class _Leser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stuecke = []          # (text, frozenset(tags))
        self.stapel = []           # je offenem Element: (name, hinzugefuegte tags)
        self.zeichen = []          # aktuelle Zeichentags (Liste, mit Mehrfachzählung)
        self.absatz = []           # aktuelle Absatztags
        self.ueberspringen = 0
        self.listen = []           # Stapel: ["ul"] oder ["ol", zähler]
        self.am_anfang_absatz = True
        self.hat_inhalt = False
        self.meta_json = None      # Inhalt von <script id="lunivo-meta">
        self.sammle = None         # ("meta"|"header"|"footer", [teile])
        self.tabelle = None        # beim Lesen einer <table>: {"zeilen": [...], "zelle": [...] oder None}
        self.textfeld = None

    def _objekt(self, daten):
        self.stuecke.append((_obj.OBJ, frozenset(self.absatz), daten))
        self.am_anfang_absatz = False
        self.hat_inhalt = True

    # -- Hilfen
    def _aktuelle(self):
        return frozenset(self.zeichen) | frozenset(self.absatz)

    def _text(self, text):
        if not text:
            return
        self.stuecke.append((text, self._aktuelle()))
        self.am_anfang_absatz = text.endswith("\n")
        self.hat_inhalt = True

    def _neue_zeile(self):
        if self.hat_inhalt and not self.am_anfang_absatz:
            self.stuecke.append(("\n", frozenset(self.absatz)))
            self.am_anfang_absatz = True

    # -- Ereignisse
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict(attrs)
        if tag == "script" and a.get("id") == "lunivo-meta":
            self.sammle = ("meta", [])
            self.ueberspringen += 1
            return
        if tag == "div" and a.get("title") in ("header", "footer") and self.sammle is None:
            self.sammle = (a["title"], [])
            self.stapel.append((tag, [], [], True))
            self.ueberspringen += 1
            return
        if self.sammle and self.sammle[0] in ("header", "footer") and self.ueberspringen:
            if tag == "sdfield":
                self.sammle[1].append("{Seiten}" if "DOCSTAT" in (a.get("type") or "").upper() else "{Seite}")
            elif tag in ("br", "p"):
                if self.sammle[1] and self.sammle[1][-1] != "\n":
                    self.sammle[1].append("\n")
            return
        if self.tabelle is not None:
            if tag == "tr":
                self.tabelle["zeilen"].append([])
            elif tag in ("td", "th"):
                if tag == "th":
                    self.tabelle["kopf"] = True
                    bg = _stile(a.get("style")).get("background-color")
                    if bg:
                        self.tabelle["kopffarbe"] = _rgb_zu_hex(bg) or self.tabelle.get("kopffarbe")
                self.tabelle["zelle"] = []
            elif tag == "br" and self.tabelle.get("zelle") is not None:
                self.tabelle["zelle"].append("\n")
            return
        if self.textfeld is not None:
            if tag == "br":
                self.textfeld["teile"].append("\n")
            return
        if tag == "table":
            self._neue_zeile()
            self.tabelle = {"zeilen": [], "zelle": None, "kopf": False, "rand": a.get("border", "1") != "0",
                            "ausr": a.get("data-ausr", "links")}
            return
        if tag == "div" and "textfeld" in (a.get("class") or ""):
            st = _stile(a.get("style"))
            bw = re.match(r"(\d+)", st.get("width", ""))
            self.textfeld = {"teile": [], "farbe": _rgb_zu_hex(st.get("background-color", "#fff")) or "#ffffff",
                             "rahmen": ("" if "none" in st.get("border", "") else (re.search(r"#[0-9a-fA-F]{3,8}", st.get("border", "")) or [None])[0] or "#444444"),
                             "breite": int(bw.group(1)) if bw else 260}
            if "transparent" in st.get("background-color", ""):
                self.textfeld["farbe"] = ""
            return
        if tag == "input" and not self.ueberspringen:
            art = (a.get("type") or "text").lower()
            if art == "checkbox":
                self._objekt({"typ": "form_kasten", "name": a.get("name", ""), "an": "checked" in a})
            elif art == "button":
                self._objekt({"typ": "form_knopf", "name": a.get("value", "")})
            elif art == "text":
                self._objekt({"typ": "form_text", "name": a.get("name", ""), "wert": a.get("value", ""), "breite": int(a.get("size", 24) or 24)})
            return
        if tag == "img" and not self.ueberspringen:
            d = _obj.aus_img_attr(a)
            if d:
                self._objekt(d)
            return
        if tag in UEBERSPRINGEN:
            self.ueberspringen += 1
            return
        if tag == "div" and "leereseite" in (a.get("class") or ""):
            self.ueberspringen += 1
            self.stapel.append((tag, [], [], True))
            return
        if self.ueberspringen:
            return
        if tag == "br":
            self.stuecke.append(("\n", frozenset(self.absatz)))
            self.am_anfang_absatz = True
            self.hat_inhalt = True
            return
        zeichen, absatz = [], []
        if tag in ("b", "strong"):
            zeichen.append("b")
        elif tag in ("i", "em"):
            zeichen.append("i")
        elif tag == "u":
            zeichen.append("u")
        elif tag == "del":
            zeichen.append("del")
        elif tag in ("s", "strike"):
            zeichen.append("s")
        elif tag == "sup":
            zeichen.append("hoch")
        elif tag == "sub":
            zeichen.append("tief")
        elif tag == "a" and a.get("href"):
            zeichen.append("link:" + a["href"])
        elif tag == "span" and a.get("data-t"):
            zeichen.append(a["data-t"])
        elif tag == "span" and a.get("id") and not a["id"].startswith("lunivo"):
            zeichen.append("marke:" + a["id"])
        elif tag == "span" and "kommentar" in (a.get("class") or "") and a.get("data-kom"):
            zeichen.append("kom:" + a["data-kom"])
        elif tag == "ins":
            zeichen.append("ins")
        elif tag == "del" and False:
            pass
        elif tag == "blockquote":
            absatz.append("st:Zitat")
        elif tag == "pre":
            absatz.append("st:Code")
        elif tag in ("h1", "h2", "h3"):
            absatz.append(tag)
        elif tag in ("h4", "h5", "h6"):
            absatz.append("h3")
        if tag in ("ul", "ol"):
            self._neue_zeile()
            self.listen.append([tag, 0])
        if tag in BLOCK:
            self._neue_zeile()
        if tag == "li":
            ebene = max(len(self.listen) - 1, 0)
            if self.listen and self.listen[-1][0] == "ol":
                self.listen[-1][1] += 1
                marke = "%d. " % self.listen[-1][1]
            else:
                marke = "• "
            self._text("    " * ebene + marke)
        stil = _stile(a.get("style"))
        ausr = stil.get("text-align") or a.get("align")
        if ausr and tag in BLOCK:
            ausr = ausr.lower()
            if ausr in ("center", "right"):
                absatz.append("al-" + ausr)
            elif ausr == "justify":
                absatz.append("al-justify")
        if tag in BLOCK and "page-break-before" in stil and "always" in stil["page-break-before"]:
            self._neue_zeile()
            self.stuecke.append(("⁂ Seitenumbruch ⁂\n", frozenset({"umbruch"})))
            self.am_anfang_absatz = True
            self.hat_inhalt = True
            self.ueberspringen += 1                  # Inhalt des Umbruch-Absatzes (<br>) ignorieren
            self.stapel.append((tag, [], [], True))
            return
        if "font-weight" in stil and (stil["font-weight"] in ("bold", "700", "800", "900")):
            zeichen.append("b")
        if stil.get("font-style") == "italic":
            zeichen.append("i")
        dekor = stil.get("text-decoration", "")
        if "underline" in dekor:
            m = re.search(r"underline\s+(solid|double|dotted|dashed|wavy)?\s*(#[0-9a-fA-F]{3,8})?", dekor)
            art = (m.group(1) if m else None) or "solid"
            farbe = (m.group(2) if m else None) or ""
            zeichen.append("u" if art == "solid" and not farbe else "ul:%s:%s" % (art, farbe))
        if "small-caps" in stil.get("font-variant", ""):
            zeichen.append("eff:kapitael")
        if stil.get("letter-spacing", "").startswith(("1", "2", "3")):
            zeichen.append("eff:gesperrt")
        if "line-through" in dekor:
            zeichen.append("s")
        bg = stil.get("background-color") or (stil.get("background") if stil.get("background", "").startswith(("#", "rgb")) else None)
        if bg:
            hx = _rgb_zu_hex(bg)
            if hx and hx not in ("#ffffff", "#fff"):
                (absatz if tag in BLOCK else zeichen).append(("sch:" if tag in BLOCK else "hl:") + hx)
        if tag in BLOCK:
            m = re.match(r"([\d.]+)\s*(px|pt|mm|cm)", stil.get("margin-left", "") or stil.get("padding-left", ""))
            if m and tag != "blockquote":
                px = float(m.group(1)) * {"px": 1, "pt": 1.333, "mm": 3.78, "cm": 37.8}[m.group(2)]
                if px > 1:
                    absatz.append("ein:%d" % round(px))
            kanten, rest = "", None
            for k, n in (("o", "border-top"), ("u", "border-bottom"), ("l", "border-left"), ("r", "border-right"), ("oulr", "border")):
                m = re.match(r"([\d.]+)(?:px|pt)?\s*(solid|double|dashed|dotted|groove|ridge)?\s*(#[0-9a-fA-F]{3,8})?", stil.get(n, ""))
                if m:
                    kanten += k
                    rest = rest or (m.group(1), m.group(2) or "solid", m.group(3) or "#7C858E")
            if kanten:
                kanten = "oulr" if "oulr" in kanten else kanten
                absatz.append("rahmen:%s:%s:%s:%s" % ((kanten,) + (rest[1], rest[0], rest[2])))
            ti = re.match(r"(-?[\d.]+)\s*(px|pt|mm|cm)", stil.get("text-indent", ""))
            if ti:
                px = float(ti.group(1)) * {"px": 1, "pt": 1.333, "mm": 3.78, "cm": 37.8}[ti.group(2)]
                if abs(px) > 1:
                    absatz.append("ers:%d" % round(px))
            mr = re.match(r"([\d.]+)\s*(px|pt|mm|cm)", stil.get("margin-right", ""))
            if mr:
                px = float(mr.group(1)) * {"px": 1, "pt": 1.333, "mm": 3.78, "cm": 37.8}[mr.group(2)]
                if px > 1:
                    absatz.append("rei:%d" % round(px))
            lh = re.match(r"([\d.]+)\s*$", stil.get("line-height", ""))
            if lh and abs(float(lh.group(1)) - 1.0) > 0.01:
                absatz.append("zl:%g" % float(lh.group(1)))
            if (a.get("class") or "") and tag == "p":
                for st in list(STILE) + list(EIGENE_STILE):
                    if st != "Fließtext" and re.sub(r"\W", "", st).lower() == re.sub(r"\W", "", a["class"]).lower():
                        absatz.append("st:" + st)
        if "font-family" in stil:
            fam = stil["font-family"].split(",")[0].strip().strip("'\"")
            if fam:
                zeichen.append("fam:" + fam)
        if "font-size" in stil:
            m = re.match(r"([\d.]+)\s*(pt|px)", stil["font-size"])
            if m:
                pt = float(m.group(1)) * (0.75 if m.group(2) == "px" else 1)
                zeichen.append("size:%g" % round(pt, 1))
        if "color" in stil:
            hx = _rgb_zu_hex(stil["color"])
            if hx and hx != "#000000":
                zeichen.append("col:" + hx)
        if tag == "font":
            if a.get("face"):
                zeichen.append("fam:" + a["face"].split(",")[0].strip())
            if a.get("color"):
                hx = _rgb_zu_hex(a["color"])
                if hx:
                    zeichen.append("col:" + hx)
        self.stapel.append((tag, zeichen, absatz, False))
        self.zeichen.extend(zeichen)
        self.absatz.extend(absatz)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "script" and self.sammle and self.sammle[0] == "meta":
            self.meta_json = "".join(self.sammle[1])
            self.sammle = None
            self.ueberspringen = max(self.ueberspringen - 1, 0)
            return
        if self.sammle and self.sammle[0] in ("header", "footer") and tag == "div":
            for i in range(len(self.stapel) - 1, -1, -1):
                if self.stapel[i][0] == "div" and self.stapel[i][3]:
                    self.stapel.pop(i)
                    break
            art, teile = self.sammle
            self.sammle = None
            self.ueberspringen = max(self.ueberspringen - 1, 0)
            self.kopf_fuss = getattr(self, "kopf_fuss", {})
            self.kopf_fuss[art] = "".join(teile).strip("\n")
            return
        if self.tabelle is not None:
            if tag in ("td", "th") and self.tabelle.get("zelle") is not None:
                text = re.sub(r"[ \t\r\n]+", " ", "".join(self.tabelle["zelle"])).strip() if False else "".join(self.tabelle["zelle"]).strip()
                if self.tabelle["zeilen"]:
                    self.tabelle["zeilen"][-1].append(text)
                self.tabelle["zelle"] = None
            elif tag == "table":
                t = self.tabelle
                self.tabelle = None
                zeilen = [z for z in t["zeilen"] if z]
                if zeilen:
                    n = max(len(z) for z in zeilen)
                    zeilen = [z + [""] * (n - len(z)) for z in zeilen]
                    d = _obj.tabelle_daten(len(zeilen), n, zeilen)
                    d["kopf"], d["rand"], d["ausr"] = t["kopf"], t["rand"], t.get("ausr", "links")
                    d["kopffarbe"] = t.get("kopffarbe", "#D9E2F3")
                    self._objekt(d)
                    self.stuecke.append(("\n", frozenset()))
                    self.am_anfang_absatz = True
            return
        if self.textfeld is not None:
            if tag == "div":
                t = self.textfeld
                self.textfeld = None
                d = _obj.textfeld_daten("".join(t["teile"]).strip(), t["farbe"], t["rahmen"])
                d["breite"] = t["breite"]
                self._objekt(d)
                self.stuecke.append(("\n", frozenset()))
                self.am_anfang_absatz = True
            return
        if tag in UEBERSPRINGEN:
            self.ueberspringen = max(self.ueberspringen - 1, 0)
            return
        # passendes offenes Element suchen
        for i in range(len(self.stapel) - 1, -1, -1):
            if self.stapel[i][0] == tag:
                _, zeichen, absatz, uebersprungen = self.stapel.pop(i)
                if uebersprungen:
                    self.ueberspringen = max(self.ueberspringen - 1, 0)
                    return
                if self.ueberspringen:
                    return
                if tag in BLOCK:
                    # Absatzende: Zeilenumbruch mit den Absatztags
                    if self.hat_inhalt and not self.am_anfang_absatz:
                        self.stuecke.append(("\n", frozenset(self.absatz)))
                        self.am_anfang_absatz = True
                for t in zeichen:
                    if t in self.zeichen:
                        self.zeichen.remove(t)
                for t in absatz:
                    if t in self.absatz:
                        self.absatz.remove(t)
                break
        if tag in ("ul", "ol") and self.listen:
            self.listen.pop()

    def handle_data(self, data):
        if self.sammle:
            if self.sammle[0] == "meta":
                self.sammle[1].append(data)
            elif self.sammle[0] in ("header", "footer"):
                self.sammle[1].append(re.sub(r"\s+", " ", data))
            return
        if self.ueberspringen:
            return
        if self.tabelle is not None:
            if self.tabelle.get("zelle") is not None:
                self.tabelle["zelle"].append(re.sub(r"\s+", " ", data))
            return
        if self.textfeld is not None:
            self.textfeld["teile"].append(re.sub(r"\s+", " ", data))
            return
        # Quelltext-Zeilenumbrüche sind Leerraum, kein Absatz
        data = re.sub(r"\s+", " ", data)
        if self.am_anfang_absatz:
            data = data.lstrip(" ")
        if data:
            self._text(data)


def html_in_puffer(puffer, quelle):
    """Ersetzt den Inhalt des Puffers durch den HTML-Text."""
    leser = _Leser()
    try:
        leser.feed(quelle)
        leser.close()
    except Exception:
        pass
    import json as _json
    puffer.meta = {}
    if leser.meta_json:
        try:
            puffer.meta = _json.loads(leser.meta_json)
        except ValueError:
            pass
    for art, text in getattr(leser, "kopf_fuss", {}).items():
        puffer.meta.setdefault("kopf" if art == "header" else "fuss", text)
    stuecke = leser.stuecke
    # letzte Zeilenumbrüche nicht doppeln: ein Dokument endet ohne leere Zeile
    while stuecke and stuecke[-1][0] == "\n":
        stuecke.pop()
    puffer.begin_irreversible_action()
    puffer.set_text("")
    puffer.objekte = []
    for stueck in stuecke:
        text, tags = stueck[0], stueck[1]
        daten = stueck[2] if len(stueck) > 2 else None
        von = puffer.get_end_iter().get_offset()
        if daten is not None:
            anker = puffer.create_child_anchor(puffer.get_end_iter())
            anker.daten = daten
            puffer.objekte.append(anker)
        else:
            puffer.insert(puffer.get_end_iter(), text)
        for name in tags:
            puffer.apply_tag(tag_holen(puffer, name),
                             puffer.get_iter_at_offset(von),
                             puffer.get_end_iter())
    puffer.end_irreversible_action()
    puffer.set_modified(False)


# --------------------------------------------------------------- HTML schreiben

def _tags_an(iterator):
    return frozenset(t.props.name for t in iterator.get_tags()
                     if t.props.name and t.props.name not in ("zoom", "grund", "steuer", "falsch", "dimm"))


def _huelle(name):
    """(öffnend, schließend) für ein Zeichentag"""
    if name == "hoch":
        return "<sup>", "</sup>"
    if name == "tief":
        return "<sub>", "</sub>"
    if name.startswith("hl:"):
        return '<span style="background-color:%s">' % name[3:], "</span>"
    if name.startswith("link:"):
        return '<a href="%s">' % html.escape(name[5:], quote=True), "</a>"
    if name.startswith(("verz:", "fn:", "en:", "noten:", "idx:", "feld:", "regel:")):
        return '<span data-t="%s">' % html.escape(name, quote=True), "</span>"
    if name.startswith("marke:"):
        return '<span id="%s">' % html.escape(name[6:], quote=True), "</span>"
    if name.startswith("kom:"):
        return '<span class="kommentar" data-kom="%s">' % html.escape(name[4:], quote=True), "</span>"
    if name == "ins":
        return '<ins>', "</ins>"
    if name == "del":
        return '<del>', "</del>"
    if name == "b":
        return "<b>", "</b>"
    if name == "i":
        return "<i>", "</i>"
    if name == "u":
        return "<u>", "</u>"
    if name.startswith("ul:"):
        teile = name.split(":", 2)
        farbe = teile[2] if len(teile) > 2 else ""
        return '<span style="text-decoration:underline %s %s">' % (teile[1], farbe), "</span>"
    if name == "eff:kapitael":
        return '<span style="font-variant:small-caps">', "</span>"
    if name == "eff:gesperrt":
        return '<span style="letter-spacing:2px">', "</span>"
    if name == "s":
        return "<s>", "</s>"
    if name.startswith("fam:"):
        return '<span style="font-family:\'%s\'">' % html.escape(name[4:], quote=True), "</span>"
    if name.startswith("size:"):
        return '<span style="font-size:%spt">' % name[5:], "</span>"
    if name.startswith("col:"):
        return '<span style="color:%s">' % name[4:], "</span>"
    return "", ""


def puffer_in_html(puffer, titel="Dokument", meta=None):
    start = puffer.get_start_iter()
    ende = puffer.get_end_iter()
    text = puffer.get_slice(start, ende, True)
    zeilen = []
    if text == "":
        absaetze = [(0, 0)]
    else:
        absaetze, pos = [], 0
        for teil in text.split("\n"):
            absaetze.append((pos, pos + len(teil)))
            pos += len(teil) + 1
    for von, bis in absaetze:
        # Absatztags am Zeilenanfang
        probe = puffer.get_iter_at_offset(von)
        absatz_tags = {t for t in _tags_an(probe) if t in ABSATZ_TAGS}
        lauf, offen, teile = von, [], []
        i = von
        while i < bis:
            if text[i] == _obj.OBJ:
                anker = puffer.get_iter_at_offset(i).get_child_anchor()
                dat = getattr(anker, "daten", None)
                teile.append(_obj.als_html(dat) if dat else "")
                i += 1
                continue
            it = puffer.get_iter_at_offset(i)
            tags = sorted(t for t in _tags_an(it) if t not in ABSATZ_TAGS)
            j = i + 1
            while j < bis and text[j] != _obj.OBJ and sorted(t for t in _tags_an(puffer.get_iter_at_offset(j))
                                                             if t not in ABSATZ_TAGS) == tags:
                j += 1
            stueck = html.escape(text[i:j])
            auf = "".join(_huelle(t)[0] for t in tags)
            zu = "".join(_huelle(t)[1] for t in reversed(tags))
            teile.append(auf + stueck + zu)
            i = j
        inhalt = "".join(teile) or "<br>"
        if "umbruch" in {t.props.name for t in puffer.get_iter_at_offset(von).get_tags()} and "umbruch" in _tags_an(puffer.get_iter_at_offset(von)):
            zeilen.append('<p style="page-break-before:always"><br></p>')
            continue
        if von + 1 == bis and text[von] == _obj.OBJ:
            dat = getattr(puffer.get_iter_at_offset(von).get_child_anchor(), "daten", None)
            if dat and dat["typ"] in ("tabelle", "textfeld"):
                zeilen.append(inhalt)
                continue
        name, klasse = "p", ""
        for h in ("h1", "h2", "h3"):
            if h in absatz_tags:
                name = h
        for t in absatz_tags:
            if t.startswith("st:") and t[3:] in STILE and STILE[t[3:]]:
                name = STILE[t[3:]][1] if name == "p" else name
                klasse = ' class="%s"' % re.sub(r"\W", "", t[3:])
            elif t.startswith("st:") and t[3:] in EIGENE_STILE:
                klasse = ' class="%s"' % re.sub(r"\W", "", t[3:])
        stile = []
        for ausr, css in (("al-center", "center"), ("al-right", "right"), ("al-justify", "justify"), ("al-distribute", "justify")):
            if ausr in absatz_tags:
                stile.append("text-align:%s" % css)
        for t in sorted(absatz_tags):
            if t.startswith("ein:"):
                stile.append("margin-left:%spx" % t[4:])
            elif t.startswith("ers:"):
                stile.append("text-indent:%spx" % t[4:])
            elif t.startswith("rei:"):
                stile.append("margin-right:%spx" % t[4:])
            elif t.startswith("zl:"):
                stile.append("line-height:%s" % t[3:])
            elif t.startswith("sch:"):
                stile.append("background-color:%s" % t[4:])
            elif t.startswith("rahmen:"):
                kanten, art, breite, farbe = (t[7:].split(":", 3) + ["solid", "1", "#7C858E"])[:4] if t.count(":") >= 4 else ("oulr", "solid", "1", "#7C858E")
                css = "%spx %s %s" % (breite, art, farbe)
                if set(kanten) == set("oulr"):
                    stile.append("border:" + css)
                else:
                    for k, n in (("o", "top"), ("u", "bottom"), ("l", "left"), ("r", "right")):
                        if k in kanten:
                            stile.append("border-%s:%s" % (n, css))
        stil = ' style="%s"' % ";".join(stile) if stile else ""
        zeilen.append("<%s%s%s>%s</%s>" % (name, klasse, stil, inhalt, name))
    import json as _json
    meta = meta or {}
    kopf = ""
    seite = meta.get("seite") or {}
    if seite:
        pw, ph = seite.get("mm", (210, 297))
        r = seite.get("rand", {})
        kopf += "<style>@page { size: %gmm %gmm; margin: %gmm %gmm %gmm %gmm }</style>" % (
            pw, ph, r.get("oben", 25), r.get("rechts", 32), r.get("unten", 25), r.get("links", 32))
    if meta:
        kopf += '<script type="application/json" id="lunivo-meta">%s</script>' % _json.dumps(
            meta, ensure_ascii=False).replace("</", "<\\/")
    vor, nach = "", ""
    if meta.get("kopf"):
        vor = '<div title="header">%s</div>\n' % _kopf_fuss_html(meta["kopf"])
    if meta.get("fuss"):
        nach = '\n<div title="footer">%s</div>' % _kopf_fuss_html(meta["fuss"])
    return ("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>%s</title>%s</head>\n<body>\n%s%s%s\n</body></html>\n"
            % (html.escape(titel), kopf, vor, "\n".join(zeilen), nach))


def _kopf_fuss_html(text):
    ab = []
    for zeile in text.split("\n"):
        z = html.escape(zeile)
        z = z.replace("{Seite}", '<sdfield type=PAGE subtype=RANDOM format=PAGE>1</sdfield>')
        z = z.replace("{Seiten}", '<sdfield type=DOCSTAT subtype=PAGE format=PAGE>1</sdfield>')
        ab.append("<p>%s</p>" % (z or "<br>"))
    return "".join(ab)


def puffer_in_pango(puffer):
    """Pango-Markup des ganzen Textes (fürs Drucken)."""
    text = puffer.get_slice(puffer.get_start_iter(), puffer.get_end_iter(), True).replace(_obj.OBJ, " ")
    ausgabe, i, n = [], 0, len(text)
    while i < n:
        it = puffer.get_iter_at_offset(i)
        tags = sorted(_tags_an(it))
        j = i + 1
        while j < n and sorted(_tags_an(puffer.get_iter_at_offset(j))) == tags and text[j] != "\n" and text[i] != "\n":
            j += 1
        stueck = html.escape(text[i:j])
        attr = []
        for t in tags:
            if t == "b":
                attr.append('weight="bold"')
            elif t == "i":
                attr.append('style="italic"')
            elif t == "u":
                attr.append('underline="single"')
            elif t == "s":
                attr.append('strikethrough="true"')
            elif t == "h1":
                attr.append('weight="bold" size="xx-large"')
            elif t == "h2":
                attr.append('weight="bold" size="x-large"')
            elif t == "h3":
                attr.append('weight="bold" size="large"')
            elif t.startswith("fam:"):
                attr.append('font_family="%s"' % html.escape(t[4:], quote=True))
            elif t.startswith("size:"):
                attr.append('size="%d"' % int(float(t[5:]) * 1024))
            elif t.startswith("col:"):
                attr.append('foreground="%s"' % t[4:])
        ausgabe.append('<span %s>%s</span>' % (" ".join(attr), stueck) if attr else stueck)
        i = j
    return "".join(ausgabe)
