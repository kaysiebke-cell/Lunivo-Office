"""Reiter Start: Zwischenablage, Schriftart, Absatz, Stile, Bearbeiten."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Pango  # noqa: E402

from . import befehl, klappe, sonder, hilfen
from .. import html_io

SCHRIFTGROESSEN = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36", "48", "72"]


def _d(w):
    return w.dok()


# ================================================================ Zwischenablage
@befehl("einfuegen")
def _einfuegen(w, _=None):
    w.zwischenablage("paste")


@befehl("einfuegen_ohne")
def _einfuegen_ohne(w, _=None):
    d = _d(w)
    if not d:
        return

    def fertig(cb, res):
        try:
            text = cb.read_text_finish(res)
        except GLib.Error:
            return
        if text:
            d.text_einfuegen(text, tuple(sorted(d.tippen)))
    w.get_clipboard().read_text_async(None, fertig)


@klappe("einfuegen_klappe")
def _einfuegen_klappe(w, pop):
    return hilfen.liste(pop, [
        ("Einfügen", lambda: w.zwischenablage("paste")),
        ("Nur Text einfügen (ohne Formatierung)", lambda: _einfuegen_ohne(w)),
        ("Inhalt der Zwischenablage als Zitat", lambda: _einfuegen_zitat(w)),
    ])


def _einfuegen_zitat(w):
    d = _d(w)
    if not d:
        return

    def fertig(cb, res):
        try:
            text = cb.read_text_finish(res)
        except GLib.Error:
            return
        if text:
            d.text_einfuegen("\n" + text.strip() + "\n")
            d.stil_setzen("Zitat")
    w.get_clipboard().read_text_async(None, fertig)


@befehl("ausschneiden")
def _ausschneiden(w, _=None):
    w.zwischenablage("cut")


@befehl("kopieren")
def _kopieren(w, _=None):
    w.zwischenablage("copy")


@befehl("format_uebertragen")
def _format_uebertragen(w, _=None):
    d = _d(w)
    if not d:
        return
    if d.puffer.get_selection_bounds() and getattr(d, "format_gemerkt", None) is not None:
        d.format_uebertragen()
        w.status("Format übertragen.")
    else:
        d.format_kopieren()
        w.status("Format gemerkt – jetzt Text auswählen und noch einmal klicken.")


@klappe("wort_extras")
def _wort_extras(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [
        ("Wort auswählen", lambda: _wort_waehlen(w)),
        ("Absatz auswählen", lambda: _absatz_waehlen(w)),
        "-",
        ("Wort in Anführungszeichen setzen", lambda: _umschliessen(w, "„", "“")),
        ("Wort in Klammern setzen", lambda: _umschliessen(w, "(", ")")),
        ("Doppelte Leerzeichen entfernen", lambda: _leerzeichen(w)),
    ])


def _wort_waehlen(w):
    d = _d(w)
    z = d._ziel() if d else None
    if z:
        d.puffer.select_range(*z)


def _absatz_waehlen(w):
    d = _d(w)
    if not d:
        return
    it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
    a = it.copy()
    a.set_line_offset(0)
    b = it.copy()
    if not b.ends_line():
        b.forward_to_line_end()
    d.puffer.select_range(a, b)


def _umschliessen(w, auf, zu):
    d = _d(w)
    z = d._ziel() if d else None
    if not z:
        return
    a, b = z
    text = d.puffer.get_text(a, b, False)
    o = a.get_offset()
    d.puffer.begin_user_action()
    d.puffer.delete(a, b)
    d.puffer.insert(d.puffer.get_iter_at_offset(o), auf + text + zu)
    d.puffer.end_user_action()


def _leerzeichen(w):
    d = _d(w)
    if d:
        import re
        n = 0
        while d.alle_ersetzen("  ", " "):
            n += 1
            if n > 50:
                break
        w.status("Doppelte Leerzeichen entfernt.")


# ================================================================ Schriftart
STIL_NAMEN = ["Fließtext", "Überschrift 1", "Überschrift 2", "Überschrift 3", "Titel", "Untertitel", "Zitat", "Code",
              "Beschriftung", "Kein Abstand"]


@sonder("felder")
def _felder(w):
    box = Gtk.Box(spacing=4)
    w.stil_namen = list(STIL_NAMEN)
    w.stil_wahl = Gtk.DropDown.new_from_strings(w.stil_namen)
    w.stil_wahl.set_size_request(110, -1)
    w.stil_wahl.set_tooltip_text("Formatvorlage")
    w.stil_wahl.connect("notify::selected", w.stil_gewaehlt)
    box.append(w.stil_wahl)
    w.schrift_wahl = Gtk.DropDown.new_from_strings(w.familien)
    w.schrift_wahl.set_enable_search(True)
    w.schrift_wahl.set_expression(Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
    w.schrift_wahl.set_size_request(150, -1)
    w.schrift_wahl.connect("notify::selected", w.schrift_gewaehlt)
    w.groesse_wahl = Gtk.DropDown.new_from_strings(SCHRIFTGROESSEN)
    w.groesse_wahl.connect("notify::selected", w.groesse_gewaehlt)
    box.append(w.schrift_wahl)
    box.append(w.groesse_wahl)
    return box


@befehl("schrift_groesser")
def _schrift_groesser(w, _=None):
    d = _d(w)
    if d:
        d.groesse_aendern(+1)


@befehl("schrift_kleiner")
def _schrift_kleiner(w, _=None):
    d = _d(w)
    if d:
        d.groesse_aendern(-1)


@befehl("schlicht")
def _schlicht(w, _=None):
    d = _d(w)
    if d:
        d.format_loeschen()


@klappe("schreibweise_klappe")
def _schreibweise_klappe(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [
        ("Satzanfang großschreiben", lambda: d.schreibweise("satz")),
        ("kleinbuchstaben", lambda: d.schreibweise("klein")),
        ("GROSSBUCHSTABEN", lambda: d.schreibweise("gross")),
        ("Jedes Wort Großschreiben", lambda: d.schreibweise("woerter")),
        ("gROSS-/kLEINSCHREIBUNG UMKEHREN", lambda: d.schreibweise("wechseln")),
    ])


def _umschalt(name):
    def f(w, _=None):
        d = _d(w)
        if d:
            d.umschalten(name)
            d.ansicht.grab_focus()
    return f


for _n, _t in (("fett", "b"), ("kursiv", "i"), ("unter", "u"), ("durch", "s"),
               ("hoch", "hoch"), ("tief", "tief"), ("zeichenumriss", "umriss")):
    befehl(_n)(_umschalt(_t))


_LINIEN = [("solid", "durchgezogen"), ("double", "doppelt"), ("dotted", "gepunktet"),
           ("dashed", "gestrichelt"), ("wavy", "gewellt")]


def _unterstrich_setzen(w, art, farbe):
    d = _d(w)
    if not d:
        return
    sel = d._bereich()
    if sel:
        d.puffer.remove_tag_by_name("u", *sel)
    d.wert_setzen("ul:", "ul:%s:%s" % (art, farbe))
    d.ansicht.grab_focus()


def _unterstrich_fenster(w):
    d = _d(w)
    if not d:
        return
    hilfen.auswahl_fenster(
        w, "Unterstreichen",
        [("Linie", "wahl", [n for _k, n in _LINIEN], 0), ("Farbe", "farbe", "#111417")],
        lambda v: _unterstrich_setzen(w, _LINIEN[v[0]][0], v[1]))


@klappe("unterstrich_klappe")
def _unterstrich_klappe(w, pop):
    d = _d(w)
    eintraege = [(n, lambda k=k: _unterstrich_setzen(w, k, "")) for k, n in _LINIEN]
    eintraege += ["-", ("Unterstreichen …", lambda: _unterstrich_fenster(w)),
                  ("Unterstreichung entfernen", lambda: (d.wert_setzen("ul:", None), d.puffer.remove_tag_by_name("u", *d._bereich()) if d._bereich() else None))]
    return hilfen.liste(pop, eintraege)


def _farbe_setzen(w, vorsatz, wert):
    d = _d(w)
    if d:
        d.wert_setzen(vorsatz, (vorsatz + wert) if wert else None)
        d.ansicht.grab_focus()


@befehl("schriftfarbe_jetzt")
def _schriftfarbe_jetzt(w, _=None):
    _farbe_setzen(w, "col:", w.werte.get("letzte_schriftfarbe", "#B5563F"))


@klappe("schriftfarbe_klappe")
def _schriftfarbe_klappe(w, pop):
    def waehle(f):
        if f:
            w.werte["letzte_schriftfarbe"] = f
        _farbe_setzen(w, "col:", f)
    return hilfen.farbwahl(pop, hilfen.FARBEN, waehle, "Automatisch (schwarz)")


@befehl("hervorheben_jetzt")
def _hervorheben_jetzt(w, _=None):
    _farbe_setzen(w, "hl:", w.werte.get("letzte_hervorhebung", "#FFFF00"))


@klappe("hervorheben_klappe")
def _hervorheben_klappe(w, pop):
    def waehle(f):
        if f:
            w.werte["letzte_hervorhebung"] = f
        _farbe_setzen(w, "hl:", f)
    return hilfen.farbwahl(pop, hilfen.HELLE, waehle, "Keine Hervorhebung")


_EFFEKTE = [("kein Effekt", None), ("Kapitälchen", "eff:kapitael"), ("Gesperrt", "eff:gesperrt"),
            ("Umriss", "umriss"), ("Eingeschlossene Zeichen", "eingeschlossen")]


def _effekt_anwenden(w, nr):
    d = _d(w)
    if not d:
        return
    name = _EFFEKTE[nr][1]
    sel = d._bereich()
    if sel:
        for n in ("eff:kapitael", "eff:gesperrt", "umriss"):
            d.puffer.remove_tag_by_name(n, *sel)
    if name == "eingeschlossen":
        _eingeschlossen(w)
    elif name:
        d.umschalten(name)
    d.ansicht.grab_focus()


def _effekt_fenster(w):
    hilfen.auswahl_fenster(
        w, "Effekt", [("Effekt", "wahl", [n for n, _k in _EFFEKTE], 0)],
        lambda v: _effekt_anwenden(w, v[0]), text="Wirkt auf den markierten Text.")


@klappe("effekt_klappe")
def _effekt_klappe(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [
        ("Effekt …", lambda: _effekt_fenster(w)),
        "-",
        ("Eingeschlossene Zeichen (①②③)", lambda: _eingeschlossen(w)),
        ("Kapitälchen", lambda: _effekt_anwenden(w, 1)),
        ("Format löschen", lambda: d.format_loeschen()),
    ])


@befehl("schrift_mehr")
def _schrift_mehr(w, _=None):
    """Der Pfeil der Gruppe: Schriftdialog."""
    d = _d(w)
    if not d:
        return
    dlg = Gtk.FontDialog()
    dlg.set_title("Schriftart")

    def fertig(dlg, res):
        try:
            beschr = dlg.choose_face_finish(res)
        except GLib.Error:
            return
        fam = beschr.get_family().get_name() if hasattr(beschr, "get_family") else None
        if fam:
            d.wert_setzen("fam:", "fam:" + fam)
    dlg.choose_family(w, None, None, lambda dl, r: _fam_fertig(w, d, dl, r))


def _fam_fertig(w, d, dlg, res):
    try:
        fam = dlg.choose_family_finish(res)
    except GLib.Error:
        return
    if fam:
        d.wert_setzen("fam:", "fam:" + fam.get_name())


_KREIS = {**{c: chr(0x24B6 + i) for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")},
          **{c: chr(0x24D0 + i) for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
          **{str(i): chr(0x2460 + i - 1) for i in range(1, 10)}, "0": "⓪"}


def _eingeschlossen(w):
    d = _d(w)
    z = d._ziel() if d else None
    if not z:
        return
    a, b = z
    o = a.get_offset()
    text = "".join(_KREIS.get(c, c) for c in d.puffer.get_text(a, b, False))
    d.puffer.begin_user_action()
    d.puffer.delete(a, b)
    d.puffer.insert(d.puffer.get_iter_at_offset(o), text)
    d.puffer.end_user_action()


# ================================================================ Absatz
@befehl("punkte")
def _punkte(w, _=None):
    d = _d(w)
    if d:
        d.aufzaehlung(False)


@befehl("zahlen")
def _zahlen(w, _=None):
    d = _d(w)
    if d:
        d.aufzaehlung(True)


@klappe("aufzaehlung_klappe")
def _aufz_klappe(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [
        ("• Punkt", lambda: d.aufzaehlung(False, "• ")),
        ("– Strich", lambda: d.aufzaehlung(False, "– ")),
        ("○ Kreis", lambda: d.aufzaehlung(False, "○ ")),
        ("■ Quadrat", lambda: d.aufzaehlung(False, "■ ")),
        ("➤ Pfeil", lambda: d.aufzaehlung(False, "➤ ")),
        ("✓ Haken", lambda: d.aufzaehlung(False, "✓ ")),
    ])


@klappe("nummerierung_klappe")
def _num_klappe(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [
        ("1. 2. 3.", lambda: d.aufzaehlung(True, "1")),
        ("a) b) c)", lambda: d.aufzaehlung(True, "a")),
        ("A. B. C.", lambda: d.aufzaehlung(True, "A")),
        ("I. II. III.", lambda: d.aufzaehlung(True, "I")),
    ])


@befehl("einzug_mehr")
def _einzug_mehr(w, _=None):
    d = _d(w)
    if d:
        d.einzug_aendern(+36)


@befehl("einzug_weniger")
def _einzug_weniger(w, _=None):
    d = _d(w)
    if d:
        d.einzug_aendern(-36)


@befehl("ebene_hoeher")
def _ebene_hoeher(w, _=None):
    _einzug_mehr(w)


@befehl("ebene_tiefer")
def _ebene_tiefer(w, _=None):
    _einzug_weniger(w)


@befehl("einzug_genau")
def _einzug_genau(w, _=None):
    """Absatz-Dialog: Einzug links/rechts/erste Zeile, Abstand vor/nach (in mm bzw. pt)."""
    d = _d(w)
    if not d:
        return

    def ok(v):
        links, rechts, erste, vor, nach = (hilfen.zahl(x) for x in v)
        d.absatz_tag_toggle("ein:%d" % round(links * 3.78) if links else None, "ein:")
        d.absatz_tag_toggle("rei:%d" % round(rechts * 3.78) if rechts else None, "rei:")
        d.absatz_tag_toggle("ers:%d" % round(erste * 3.78) if erste else None, "ers:")
        a, b = d._zeilen()
        for n in range(a, b + 1):
            _, von = d.puffer.get_iter_at_line(n)
            bis = von.copy()
            bis.forward_to_line_end()
            bis.forward_char()
            for t in ("abs:vor", "abs:nach"):
                pass
        d.puffer.set_modified(True)
    hilfen.frage(w, "Absatz", [("Einzug links (mm)", "0"), ("Einzug rechts (mm)", "0"),
                               ("Erste Zeile (mm, negativ = hängend)", "0"), ("Abstand vor (pt)", "0"),
                               ("Abstand nach (pt)", "0")], ok,
                 "Einzug und Abstand des Absatzes. 0 entfernt die Einstellung.", "OK")


@befehl("sortieren")
def _sortieren(w, _=None):
    d = _d(w)
    if not d:
        return

    def los(v):
        d.zeilen_sortieren(absteigend=v[0] == 1, typ=["text", "zahl"][v[1]])
        w.status("Sortiert (%s)." % ("Z → A" if v[0] == 1 else "A → Z"))
    hilfen.auswahl_fenster(
        w, "Sortieren", [("Reihenfolge", "wahl", ["A → Z", "Z → A"], 0), ("Typ", "wahl", ["Text", "Zahl"], 0)],
        los, text="Die markierten Absätze werden sortiert.", okname="Sortieren")


@befehl("steuerzeichen")
def _steuer(w, _=None):
    d = _d(w)
    if d:
        d.steuerzeichen(not getattr(d, "steuer_an", False))


def _ausrichtung(name):
    def f(w, _=None):
        d = _d(w)
        if d:
            d.absatz_setzen("al", name)
    return f


for _n, _t in (("links", None), ("mitte", "al-center"), ("rechts", "al-right"),
               ("block", "al-justify"), ("verteilt", "al-distribute")):
    befehl(_n)(_ausrichtung(_t))


@klappe("zeilenabstand_klappe")
def _zeilenabstand_klappe(w, pop):
    d = _d(w)

    def setze(f):
        d.absatz_tag_toggle(None if f == 1 else "zl:%g" % f, "zl:")
    eintraege = [(t, (lambda f=f: setze(f))) for t, f in (
        ("Einfach (1,0)", 1.0), ("1,15", 1.15), ("Eineinhalb (1,5)", 1.5), ("Doppelt (2,0)", 2.0), ("Dreifach (3,0)", 3.0))]
    eintraege.append("-")
    eintraege.append(("Mehr …", lambda: hilfen.frage(
        w, "Zeilenabstand", [("Faktor", "1,3")], lambda v: setze(hilfen.zahl(v[0], 1.0)))))
    return hilfen.liste(pop, eintraege)


@klappe("absatz_schattierung")
def _absatz_schattierung(w, pop):
    d = _d(w)
    return hilfen.farbwahl(pop, hilfen.FARBEN,
                           lambda f: d.absatz_tag_toggle("sch:" + f if f else None, "sch:"),
                           "Keine Farbe", "Weitere Füllfarben …")


_RAHMEN_ARTEN = [("solid", "durchgezogen"), ("double", "doppelt"), ("dashed", "gestrichelt"), ("dotted", "gepunktet")]
_RAHMEN_KANTEN = [("oulr", "ringsum"), ("o", "oben"), ("u", "unten"), ("l", "links"), ("r", "rechts"),
                  ("ou", "oben und unten"), ("lr", "links und rechts")]


def _rahmen_fenster(w):
    d = _d(w)
    if not d:
        return
    hilfen.auswahl_fenster(
        w, "Rahmen und Linien",
        [("Rahmen", "wahl", [n for _k, n in _RAHMEN_KANTEN], 0),
         ("Linie", "wahl", [n for _k, n in _RAHMEN_ARTEN], 0),
         ("Stärke (pt)", "wahl", ["0,5", "1", "1,5", "2", "3"], 1),
         ("Farbe", "farbe", "#7C858E")],
        lambda v: d.rahmen_setzen(_RAHMEN_KANTEN[v[0]][0], _RAHMEN_ARTEN[v[1]][0],
                                  hilfen.zahl(["0,5", "1", "1,5", "2", "3"][v[2]], 1.0), v[3]))


@klappe("absatz_rahmen")
def _absatz_rahmen(w, pop):
    d = _d(w)
    return hilfen.liste(pop, [
        ("Untere Rahmenlinie", lambda: d.rahmen_setzen("u")),
        ("Obere Rahmenlinie", lambda: d.rahmen_setzen("o")),
        ("Linke Rahmenlinie", lambda: d.rahmen_setzen("l")),
        ("Rechte Rahmenlinie", lambda: d.rahmen_setzen("r")),
        "-",
        ("Kein Rahmen", lambda: d.rahmen_setzen("")),
        ("Alle Rahmenlinien", lambda: d.rahmen_setzen("oulr")),
        "-",
        ("Rahmen und Linien …", lambda: _rahmen_fenster(w)),
    ])


# ================================================================ Stile
KATALOG_KACHELN = [("Standard", "Fließtext"), ("Überschrift 1", "Überschrift 1"), ("Überschrift 2", "Überschrift 2"),
                   ("Überschrift 3", "Überschrift 3"), ("Titel", "Titel"), ("Untertitel", "Untertitel"),
                   ("Zitat", "Zitat"), ("Kein Abstand", "Kein Abstand")]


def _kachel(w, anzeige, stil):
    b = Gtk.Button()
    b.add_css_class("flat")
    b.add_css_class("stilknopf")
    kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    l1 = Gtk.Label(label="Aa")
    klasse = "stilprobe-" + stil.replace(" ", "").replace("ß", "ss").replace("ü", "ue").replace("Ü", "Ue")
    l1.add_css_class(klasse)
    l2 = Gtk.Label(label=anzeige)
    l2.add_css_class("kleinname")
    kasten.append(l1)
    kasten.append(l2)
    b.set_child(kasten)
    b.set_tooltip_text(anzeige)
    b.connect("clicked", lambda _b, n=stil: (w.dok() and w.dok().stil_setzen(n), w.dok() and w.dok().ansicht.grab_focus()))
    return b


@sonder("katalog")
def _katalog(w):
    """Acht Kacheln in zwei Zeilen — die Vorlage wird gezeigt, nicht benannt — und ein Pfeil, der alle aufklappt."""
    box = Gtk.Box(spacing=2)
    w.stil_knoepfe = {}
    gitter = Gtk.Grid(row_spacing=1, column_spacing=1)
    for i, (anzeige, stil) in enumerate(KATALOG_KACHELN):
        b = _kachel_mit(w, anzeige, stil)
        w.stil_knoepfe[stil] = b
        gitter.attach(b, i // 2, i % 2, 1, 1)
    box.append(gitter)
    pfeil = Gtk.MenuButton()
    pfeil.add_css_class("flat")
    pfeil.set_icon_name("pan-down-symbolic")
    pfeil.set_tooltip_text("Alle Formatvorlagen")
    pfeil.set_create_popup_func(lambda m: _katalog_popover(w, m))
    box.append(pfeil)
    return box


def _kachel_mit(w, anzeige, stil):
    b = Gtk.Button()
    b.add_css_class("flat")
    b.add_css_class("stilknopf")
    kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    l1 = Gtk.Label(label="Aa")
    l1.add_css_class("stilprobe-" + stil.replace(" ", "").replace("ß", "ss").replace("ü", "ue").replace("Ü", "Ue"))
    l2 = Gtk.Label(label=anzeige)
    l2.add_css_class("kleinname")
    kasten.append(l1)
    kasten.append(l2)
    b.set_child(kasten)
    b.set_tooltip_text(anzeige)
    b.connect("clicked", lambda _b: (_d(w) and _d(w).stil_setzen(stil), _d(w) and _d(w).ansicht.grab_focus()))
    return b


def _katalog_popover(w, menuknopf):
    pop = Gtk.Popover()
    pop.set_has_arrow(False)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box.add_css_class("klappliste")
    gitter = Gtk.Grid(row_spacing=2, column_spacing=2)
    d = _d(w)
    namen = [(a, s) for a, s in KATALOG_KACHELN] + [(n, n) for n in (sorted(d.eigene_stile()) if d else [])]
    for i, (anzeige, stil) in enumerate(namen):
        b = _kachel_mit(w, anzeige, stil)
        b.connect("clicked", lambda *_: pop.popdown())
        gitter.attach(b, i % 4, i // 4, 1, 1)
    box.append(gitter)
    box.append(Gtk.Separator())
    for text, bef in (("Neue Formatvorlage …", "vorlage_neu"), ("Formatvorlagen verwalten …", "vorlagen_verwalten"),
                      ("Formatvorlage löschen …", "vorlage_loeschen")):
        b = Gtk.Button()
        b.add_css_class("flat")
        l = Gtk.Label(label=text, xalign=0)
        b.set_child(l)
        b.connect("clicked", lambda _b, bef=bef: (pop.popdown(), GLib.idle_add(lambda: befehle_ausfuehren(w, bef) and False)))
        box.append(b)
    pop.set_child(box)
    menuknopf.set_popover(pop)


def befehle_ausfuehren(w, name):
    from . import ausfuehren
    return ausfuehren(w, name)


@befehl("vorlage_neu")
def _vorlage_neu(w, bearbeiten=None):
    d = _d(w)
    if not d:
        return
    alt = d.eigene_stile().get(bearbeiten, {}) if bearbeiten else {}
    dlg = Gtk.Window(transient_for=w, modal=True, title="Neue Formatvorlage" if not bearbeiten else "Formatvorlage ändern")
    dlg.set_default_size(560, -1)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(16)
    dlg.set_child(box)
    name = Gtk.Entry(text=bearbeiten or "", placeholder_text="Name, z. B. Anschrift")
    basen = [a for a, _ in KATALOG_KACHELN] + [n for n in d.eigene_stile() if n != bearbeiten]
    basis = Gtk.DropDown.new_from_strings(basen)
    if alt.get("basis"):
        for i, (a, s) in enumerate([(a, s) for a, s in KATALOG_KACHELN] + [(n, n) for n in d.eigene_stile() if n != bearbeiten]):
            if s == alt["basis"] or a == alt["basis"]:
                basis.set_selected(i)
    zeile = Gtk.Box(spacing=8)
    zeile.append(Gtk.Label(label="Name"))
    zeile.append(name)
    zeile.append(Gtk.Label(label="baut auf"))
    zeile.append(basis)
    box.append(zeile)
    # obere Leiste: Schrift
    z1 = Gtk.Box(spacing=6)
    fam = Gtk.DropDown.new_from_strings(["(wie Basis)"] + w.familien)
    if alt.get("fam") in w.familien:
        fam.set_selected(w.familien.index(alt["fam"]) + 1)
    gr = Gtk.SpinButton.new_with_range(0, 96, 1)
    gr.set_value(float(alt.get("groesse") or 0))
    gr.set_tooltip_text("Größe in pt (0 = wie Basis)")
    fett = Gtk.ToggleButton(label="F", active=bool(alt.get("fett")))
    kursiv = Gtk.ToggleButton(label="K", active=bool(alt.get("kursiv")))
    farbe = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog())
    from gi.repository import Gdk
    c = Gdk.RGBA()
    c.parse(alt.get("farbe") or "#000000")
    farbe.set_rgba(c)
    mit_farbe = Gtk.CheckButton(label="Farbe", active=bool(alt.get("farbe")))
    for x in (Gtk.Label(label="Schrift"), fam, gr, fett, kursiv, mit_farbe, farbe):
        z1.append(x)
    box.append(z1)
    # untere Leiste: Absatz
    z2 = Gtk.Box(spacing=6)
    ausr = Gtk.DropDown.new_from_strings(["links", "zentriert", "rechts", "Blocksatz"])
    ausr.set_selected({"center": 1, "right": 2, "justify": 3}.get(alt.get("ausr"), 0))
    zl = Gtk.SpinButton.new_with_range(0.8, 3.0, 0.1)
    zl.set_digits(1)
    zl.set_value(float(alt.get("zeilen") or 1.0))
    ez = Gtk.SpinButton.new_with_range(0, 100, 1)
    ez.set_value(float(alt.get("einzug") or 0) / 3.78)
    vor = Gtk.SpinButton.new_with_range(0, 60, 1)
    vor.set_value(float(alt.get("vor") or 0))
    nach = Gtk.SpinButton.new_with_range(0, 60, 1)
    nach.set_value(float(alt.get("nach") or 0))
    for t, x in (("Absatz", ausr), ("Zeilen", zl), ("Einzug mm", ez), ("vor pt", vor), ("nach pt", nach)):
        z2.append(Gtk.Label(label=t))
        z2.append(x)
    box.append(z2)
    vorschau = Gtk.Label(label="Aa  Beispieltext in dieser Vorlage", xalign=0)
    vorschau.set_margin_top(8)
    box.append(vorschau)
    css = Gtk.CssProvider()
    vorschau.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def beschreibung():
        return {"basis": next(s for a, s in [(a, s) for a, s in KATALOG_KACHELN] + [(n, n) for n in d.eigene_stile() if n != bearbeiten]
                              if a == basen[basis.get_selected()]),
                "fam": None if fam.get_selected() == 0 else w.familien[fam.get_selected() - 1],
                "groesse": gr.get_value() or None, "fett": fett.get_active(), "kursiv": kursiv.get_active(),
                "farbe": ("#%02x%02x%02x" % tuple(round(v * 255) for v in (farbe.get_rgba().red, farbe.get_rgba().green, farbe.get_rgba().blue)))
                if mit_farbe.get_active() else None,
                "ausr": ["left", "center", "right", "justify"][ausr.get_selected()], "zeilen": zl.get_value(),
                "einzug": ez.get_value() * 3.78, "vor": vor.get_value(), "nach": nach.get_value()}

    def auffrischen(*_):
        b_ = beschreibung()
        stil = "label { font-size: %spx; %s %s %s }" % (
            b_["groesse"] or 14, "font-weight: bold;" if b_["fett"] else "", "font-style: italic;" if b_["kursiv"] else "",
            ("color: %s;" % b_["farbe"]) if b_["farbe"] else "")
        css.load_from_string(stil)
    for x in (fam, gr, fett, kursiv, mit_farbe, farbe, ausr, zl, ez, vor, nach, basis):
        sig = "notify::selected" if isinstance(x, Gtk.DropDown) else "notify::rgba" if isinstance(x, Gtk.ColorDialogButton) else \
            "value-changed" if isinstance(x, Gtk.SpinButton) else "toggled"
        x.connect(sig, auffrischen)
    auffrischen()
    knoepfe = Gtk.Box(spacing=8, halign=Gtk.Align.END)
    abbr = Gtk.Button(label="Abbrechen")
    abbr.connect("clicked", lambda *_: dlg.close())
    ok = Gtk.Button(label="Speichern und anwenden")
    ok.add_css_class("suggested-action")

    def speichern(*_):
        n = name.get_text().strip()
        if not n or n in [a for a, _s in KATALOG_KACHELN]:
            return w.meldung("Name", "Bitte einen eigenen Namen wählen (nicht den einer eingebauten Vorlage).")
        if bearbeiten and bearbeiten != n:
            d.vorlage_loeschen(bearbeiten)
        d.vorlage_anlegen(n, beschreibung())
        d.stil_setzen(n)
        dlg.close()
    ok.connect("clicked", speichern)
    knoepfe.append(abbr)
    knoepfe.append(ok)
    box.append(knoepfe)
    dlg.present()


@befehl("vorlagen_verwalten")
def _vorlagen_verwalten(w, _=None):
    d = _d(w)
    if not d:
        return
    dlg = Gtk.Window(transient_for=w, modal=True, title="Formatvorlagen verwalten")
    dlg.set_default_size(420, 360)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Eigene Formatvorlagen dieses Dokuments. Sie wandern mit dem Reiter.", xalign=0, wrap=True))
    lb = Gtk.ListBox()
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(lb)
    box.append(rolle)

    def fuellen():
        k = lb.get_first_child()
        while k:
            n = k.get_next_sibling()
            lb.remove(k)
            k = n
        for n in sorted(d.eigene_stile()):
            lb.append(Gtk.Label(label=n, xalign=0))
        if not d.eigene_stile():
            lb.append(Gtk.Label(label="Noch keine eigene Vorlage.", xalign=0))
    fuellen()
    z = Gtk.Box(spacing=6)
    neu = Gtk.Button(label="Neu …")
    neu.connect("clicked", lambda *_: (dlg.close(), _vorlage_neu(w)))
    aend = Gtk.Button(label="Ändern …")

    def aendern(*_):
        r = lb.get_selected_row()
        if r and r.get_child().get_text() in d.eigene_stile():
            n = r.get_child().get_text()
            dlg.close()
            _vorlage_neu(w, n)
    aend.connect("clicked", aendern)
    weg = Gtk.Button(label="Löschen")

    def loeschen(*_):
        r = lb.get_selected_row()
        if r and r.get_child().get_text() in d.eigene_stile():
            d.vorlage_loeschen(r.get_child().get_text())
            fuellen()
    weg.connect("clicked", loeschen)
    for x in (neu, aend, weg):
        z.append(x)
    box.append(z)
    dlg.present()


@befehl("vorlage_loeschen")
def _vorlage_loeschen(w, _=None):
    d = _d(w)
    if not d:
        return
    namen = sorted(d.eigene_stile())
    if not namen:
        return w.meldung("Formatvorlage löschen", "Es gibt keine eigene Formatvorlage zum Löschen.")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Welche Formatvorlage löschen?")
    dlg.set_buttons(namen[:6] + ["Abbrechen"])
    dlg.set_cancel_button(len(namen[:6]))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(namen[:6]):
            d.vorlage_loeschen(namen[n])
    dlg.choose(w, None, fertig)


# ================================================================ Bearbeiten
@befehl("suchen")
def _suchen(w, _=None):
    w.suchleiste_zeigen(False)


@befehl("ersetzen")
def _ersetzen(w, _=None):
    w.suchleiste_zeigen(True)


@befehl("gehe_zu")
def _gehe_zu(w, _=None):
    d = _d(w)
    if not d:
        return

    def los(v):
        n = int(hilfen.zahl(v[0], 1))
        n = max(1, min(n, d.puffer.get_line_count()))
        _, it = d.puffer.get_iter_at_line(n - 1)
        d.puffer.place_cursor(it)
        d.ansicht.scroll_to_iter(it, 0.1, True, 0.0, 0.3)
        d.ansicht.grab_focus()
    hilfen.frage(w, "Gehe zu", [("Zeile (1–%d)" % d.puffer.get_line_count(), "1")], los, okname="Gehe zu")


@befehl("suchen_ersetzen")
def _suchen_ersetzen(w, _=None):
    w.suchleiste_zeigen(True)


@befehl("alles_markieren")
def _alles(w, _=None):
    d = _d(w)
    if d:
        d.puffer.select_range(d.puffer.get_start_iter(), d.puffer.get_end_iter())


@befehl("objekte_waehlen")
def _objekte(w, _=None):
    d = _d(w)
    if d:
        n = d.objekt_naechstes() if hasattr(d, "objekt_naechstes") else None
        w.status("Objekt ausgewählt." if n else "Keine Objekte (Bilder, Tabellen) im Dokument.")
