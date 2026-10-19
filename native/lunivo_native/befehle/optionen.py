"""Optionen — dieselben Seiten wie in der alten Einstellungsseite (Leichter lesen · Wie im WPS Writer · Nur bei Lunivo).

Aufbau, Beschriftungen und Erklärungen stehen in daten/optionen.json (aus der alten Oberfläche gelesen).
Jede Einstellung wird in werte["opt"]["<seite>|<name>"] gemerkt und sofort angewendet (WIRKUNG)."""
import json
import os
import subprocess
import threading

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk  # noqa: E402

from . import befehl, befehle_ausfuehren, hilfen
from .. import einstellungen, html_io, pfade, schreibhilfe, sprachdienste

_DATEN = None
GRUPPEN = [
    ("Leichter lesen", [("lesehilfe", "Lesehilfe"), ("schriften", "Schriftarten"), ("sprache", "Sprache"),
                        ("pruefung", "Rechtschreibprüfung")]),
    ("Wie im WPS Writer", [("ansicht", "Ansicht"), ("bearbeiten", "Bearbeiten"), ("speichern", "Allgemein und Speichern"),
                           ("sicherung", "Sicherungseinstellungen"), ("pfade", "Speicherort für Dateien"),
                           ("verfolgen", "Änderungen verfolgen"), ("pdf", "In PDF exportieren"),
                           ("benutzer", "Benutzerinformationen"), ("drucken", "Drucken"), ("sicherheit", "Sicherheit"),
                           ("band", "Menüband anpassen"), ("schnellzugriff", "Symbolleiste für den Schnellzugriff")]),
    ("Nur bei Lunivo", [("ki", "Schreibhilfe und KI"), ("gedaechtnis", "Gedächtnis"), ("erweitert", "Erweitert")]),
]
SPRACHEN = {"Deutsch": "de_DE", "Deutsch (Österreich)": "de_AT", "Deutsch (Schweiz)": "de_CH", "Englisch": "en_US"}
PAPIERTON = {"Weiß": "#FFFFFF", "Creme": "#FFF8E1", "Sandgrau": "#EDEAE4", "Blassgelb": "#FFFBCC", "Blassblau": "#E8F1FA",
             "Blassgrün": "#E9F5EC", "Blassrosa": "#FDEBEB"}
ABSTAND = ["normal", "etwas mehr", "deutlich mehr", "sehr viel"]
FORMATE = {"OpenDocument-Text (.odt)": "odt", "Microsoft Word (.docx)": "docx", "Rich Text (.rtf)": "rtf",
           "Webseite (.html)": "html", "Nur Text (.txt)": "txt"}


def daten():
    global _DATEN
    if _DATEN is None:
        with open(os.path.join(os.path.dirname(__file__), "..", "daten", "optionen.json"), encoding="utf-8") as f:
            _DATEN = json.load(f)
    return _DATEN


def holen(w, seite, name, standard=None):
    return w.werte.setdefault("opt", {}).get("%s|%s" % (seite, name), standard)


def _dok_alle(w):
    return w.alle_dokumente()


# ================================================================ Wirkungen: was eine Einstellung auslöst
def _lesehilfe_aus_opt(w):
    l = w.werte.setdefault("lesehilfe", {})
    ton = holen(w, "lesehilfe", "Papierton", "Weiß")
    l["hintergrund"] = PAPIERTON.get(ton, "#FFFFFF")
    l["buchstabenabstand"] = [0, 0.5, 1.0, 1.6][ABSTAND.index(holen(w, "lesehilfe", "Buchstabenabstand", "normal"))]
    l["zeilenabstand"] = [1.0, 1.25, 1.5, 1.9][ABSTAND.index(holen(w, "lesehilfe", "Zeilenluft", "normal"))]
    from .schreibhilfe_tab import lesehilfe_anwenden
    for d in _dok_alle(w):
        lesehilfe_anwenden(w, d)


def _stufe(w, wert):
    voreinst = {"Standard": ("Weiß", "normal", "normal"), "Leichter lesen": ("Creme", "etwas mehr", "etwas mehr"),
                "Sehr leicht lesen": ("Blassgelb", "deutlich mehr", "deutlich mehr")}
    ton, bu, ze = voreinst[wert]
    o = w.werte.setdefault("opt", {})
    o["lesehilfe|Papierton"], o["lesehilfe|Buchstabenabstand"], o["lesehilfe|Zeilenluft"] = ton, bu, ze
    _lesehilfe_aus_opt(w)


def _uebriger_text(w, wert):
    stufe = {"gleich lassen": "#E6E9EC", "etwas blasser": "#B8BDC2", "deutlich blasser": "#8A9096"}[wert]
    for d in _dok_alle(w):
        t = html_io.tag_holen(d.puffer, "dimm")
        c = Gdk.RGBA()
        c.parse(stufe if wert != "gleich lassen" else "#9AA3AB")
        t.set_property("foreground-rgba", c)


def _befehl_wenn(name, w, an):
    """Schaltet einen Schalter-Befehl nur, wenn der Zustand nicht schon stimmt."""
    if bool(w.werte["an"].get(name, False)) != bool(an):
        befehle_ausfuehren(w, name)


def _sprache(w, wert):
    k = SPRACHEN.get(wert, "de_DE")
    w.werte["sprache"] = k
    for d in _dok_alle(w):
        d._rs_sprache = k
        if w.werte["an"].get("rechtschreibung"):
            d.rechtschreibung(True, k)


def _autokorr_regel(schluessel):
    def f(w, wert):
        for d in _dok_alle(w):
            d.autokorr_regeln[schluessel] = bool(wert)
    return f


def _bedienung_schrift(w, wert):
    w.bedienung_skalieren(int(wert))


def _rueckgaengig(w, wert):
    for d in _dok_alle(w):
        d.puffer.set_max_undo_levels(int(wert))


def _benutzer(w, wert):
    pass


WIRKUNG = {
    "lesehilfe|Wie leicht soll es zu lesen sein?": _stufe,
    "lesehilfe|Papierton": lambda w, v: _lesehilfe_aus_opt(w),
    "lesehilfe|Buchstabenabstand": lambda w, v: _lesehilfe_aus_opt(w),
    "lesehilfe|Zeilenluft": lambda w, v: _lesehilfe_aus_opt(w),
    "lesehilfe|Übriger Text": _uebriger_text,
    "lesehilfe|Zeilenfokus": lambda w, v: _befehl_wenn("zeilenfokus", w, v),
    "lesehilfe|Silbentrennung": lambda w, v: _befehl_wenn("silbentrennung", w, v),
    "sprache|Silbentrennung": lambda w, v: _befehl_wenn("silbentrennung", w, v),
    "lesehilfe|Rechtschreibung während der Eingabe prüfen": lambda w, v: _befehl_wenn("rechtschreibung", w, v),
    "sprache|Rechtschreibung während der Eingabe": lambda w, v: _befehl_wenn("rechtschreibung", w, v),
    "pruefung|Rechtschreibung während der Eingabe prüfen": lambda w, v: _befehl_wenn("rechtschreibung", w, v),
    "sprache|Sprache für die Prüfung": _sprache,
    "pruefung|Sprache für die Prüfung": _sprache,
    "schriften|Schrift": lambda w, v: w.werte.__setitem__("schriftart", v),
    "schriften|Größe": lambda w, v: w.werte.__setitem__("groesse", int(str(v).split()[0])),
    "ansicht|Lineal": lambda w, v: _befehl_wenn("lineal", w, v) or [d.lineal_zeigen(v) for d in _dok_alle(w)],
    "ansicht|Vertikales Lineal": lambda w, v: [d.lineal_hoch_zeigen(v) for d in _dok_alle(w)] and w.werte["an"].__setitem__("lineal_hoch", v),
    "ansicht|Navigationsbereich": lambda w, v: (w.navigation.set_visible(bool(v)), v and w.navigation_auffrischen()),
    "ansicht|Textbegrenzungen": lambda w, v: ([d.begrenzungen_zeigen(v) for d in _dok_alle(w)], w.werte["an"].__setitem__("textbegrenzungen", v)),
    "ansicht|Gitternetzlinien": lambda w, v: ([d.netz_zeigen(v) for d in _dok_alle(w)], w.werte["an"].__setitem__("netzlinien", v)),
    "ansicht|Statusleiste": lambda w, v: w.status_leiste.set_visible(bool(v)),
    "ansicht|Seitenleiste beim Start": lambda w, v: w.werte.__setitem__("schreibhilfe", bool(v)),
    "ansicht|Helligkeit": lambda w, v: (w.werte.__setitem__("thema", {"Wie das System": "auto", "Immer hell": "light", "Immer dunkel": "dark"}[v]),
                                        w.hell_dunkel_anwenden(), w.band_auffrischen()),
    "ansicht|Schrift der Bedienung": _bedienung_schrift,
    "ansicht|Doppelklick blendet das Band aus": lambda w, v: None,
    "ansicht|Strg+Klick folgt einem Verweis": lambda w, v: None,
    "ansicht|Alle anzeigen": lambda w, v: [d.steuerzeichen(bool(v)) for d in _dok_alle(w)],
    "bearbeiten|Maximale Rückgängig-Schritte": _rueckgaengig,
    "bearbeiten|AutoKorrektur": lambda w, v: [setattr(d, "autokorrektur_an", bool(v)) for d in _dok_alle(w)] and w.werte["an"].__setitem__("autokorrektur", bool(v)),
    "bearbeiten|Typografische Anführungszeichen": _autokorr_regel("anfuehrung"),
    "bearbeiten|Gedankenstriche": _autokorr_regel("striche"),
    "bearbeiten|Auslassungspunkte": _autokorr_regel("punkte"),
    "bearbeiten|Jeden Satz mit einem Großbuchstaben beginnen": _autokorr_regel("satzanfang"),
    "bearbeiten|Wochentage immer großschreiben": _autokorr_regel("wochentage"),
    "bearbeiten|Feststelltaste korrigieren": _autokorr_regel("feststell"),
    "bearbeiten|Wortvorhersage": lambda w, v: [setattr(d, "vorhersage_an", bool(v)) for d in _dok_alle(w)] and w.werte["an"].__setitem__("vorhersage", bool(v)),
    "speichern|Beim Start das zuletzt geschriebene Dokument öffnen": lambda w, v: w.werte.__setitem__("start_zuletzt", bool(v)),
    "sicherung|Sicherungskopie beim Speichern": lambda w, v: w.werte.__setitem__("sicherung_kopie", bool(v)),
    "verfolgen|Änderungen verfolgen": lambda w, v: _befehl_wenn("verfolgen", w, v),
    "verfolgen|Markup anzeigen": lambda w, v: _befehl_wenn("markup_aus", w, not v) if False else _markup(w, v),
    "verfolgen|Name des Bearbeiters": lambda w, v: w.werte.__setitem__("benutzer_name", v),
    "ki|Für wen der Text ist": lambda w, v: w.schreibhilfe.ziel_setzen(v),
}


def _markup(w, an):
    if bool(w.werte["an"].get("markup_aus", False)) == bool(an):
        befehle_ausfuehren(w, "markup_umschalten")


def anwenden(w, schluessel, wert):
    w.werte.setdefault("opt", {})[schluessel] = wert
    f = WIRKUNG.get(schluessel)
    if f:
        try:
            f(w, wert)
        except Exception as e:
            w.status("Einstellung konnte nicht angewendet werden: %s" % e)


def anfangswert(w, seite, f):
    """Der gerade gültige Wert: aus dem Programm, wenn es ihn dort gibt, sonst der gemerkte oder der Vorgabewert."""
    gemerkt = holen(w, seite, f["n"])
    n = f["n"]
    zustand = {"Lineal": "lineal", "Vertikales Lineal": "lineal_hoch", "Navigationsbereich": "navigation",
               "Textbegrenzungen": "textbegrenzungen", "Gitternetzlinien": "netzlinien", "Zeilenfokus": "zeilenfokus",
               "Silbentrennung": "silbentrennung", "Änderungen verfolgen": "verfolgen", "AutoKorrektur": "autokorrektur",
               "Wortvorhersage": "vorhersage"}
    if n in zustand and f["t"] == "schalter":
        return bool(w.zustand(zustand[n]))
    if n.startswith("Rechtschreibung während der Eingabe") and f["t"] == "schalter":
        return bool(w.werte["an"].get("rechtschreibung", True))
    if n == "Markup anzeigen":
        return not w.werte["an"].get("markup_aus", False)
    if n == "Statusleiste":
        return bool(w.status_leiste.get_visible())
    if n == "Seitenleiste beim Start":
        return bool(w.werte.get("schreibhilfe", True))
    if n == "Schrift" and seite == "schriften":
        return w.werte["schriftart"]
    if n == "Größe" and seite == "schriften":
        return "%d pt" % w.werte["groesse"]
    if n == "Helligkeit":
        return {"auto": "Wie das System", "light": "Immer hell", "dark": "Immer dunkel"}.get(w.werte.get("thema", "dark"))
    if n == "Sprache für die Prüfung":
        return next((k for k, v in SPRACHEN.items() if v == w.werte.get("sprache", "de_DE")), "Deutsch")
    if n == "Beim Start das zuletzt geschriebene Dokument öffnen":
        return bool(w.werte.get("start_zuletzt", True))
    if n == "Sicherungskopie beim Speichern":
        return bool(w.werte.get("sicherung_kopie", True))
    if n == "Name des Bearbeiters":
        return w.werte.get("benutzer_name", "Ich")
    if n == "Für wen der Text ist":
        return w.werte.get("zielgruppe", "egal")
    if n == "Dateien als Standard speichern":
        return next((k for k, v in FORMATE.items() if v == w.werte.get("standardformat", "docx")), "Microsoft Word (.docx)")
    if gemerkt is not None:
        return gemerkt
    return f.get("v")


# ================================================================ Darstellung der Seite
def _karte_zeile(w, seite, f, hinweis):
    t = f["t"]
    zeile = Gtk.Box(spacing=12)
    zeile.add_css_class("optzeile")
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, hexpand=True)
    name = Gtk.Label(label=f["n"], xalign=0, wrap=True)
    text.append(name)
    if f.get("h"):
        h = Gtk.Label(label=f["h"], xalign=0, wrap=True)
        h.add_css_class("dim-label")
        h.add_css_class("klein-text")
        text.append(h)
    zeile.append(text)
    schluessel = "%s|%s" % (seite, f["n"])
    start = anfangswert(w, seite, f)
    ctrl = None
    if t == "schalter":
        ctrl = Gtk.Switch(valign=Gtk.Align.CENTER)
        ctrl.set_active(bool(start))
        ctrl.connect("state-set", lambda s, an: (anwenden(w, schluessel, bool(an)), False)[1])
    elif t in ("auswahl", "radio"):
        if t == "radio" and len(f["o"]) <= 3:
            ctrl = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
            erster = None
            for o in f["o"]:
                b = Gtk.ToggleButton(label=o)
                b.add_css_class("chip")
                if erster:
                    b.set_group(erster)
                else:
                    erster = b
                b.set_active(o == start)
                b.connect("toggled", lambda b, o=o: b.get_active() and anwenden(w, schluessel, o))
                ctrl.append(b)
        else:
            ctrl = Gtk.DropDown.new_from_strings(f["o"])
            ctrl.set_valign(Gtk.Align.CENTER)
            if start in f["o"]:
                ctrl.set_selected(f["o"].index(start))
            ctrl.connect("notify::selected", lambda d, *_: anwenden(w, schluessel, f["o"][d.get_selected()]))
    elif t == "schriftwahl":
        ctrl = Gtk.DropDown.new_from_strings(w.familien)
        ctrl.set_valign(Gtk.Align.CENTER)
        if start in w.familien:
            ctrl.set_selected(w.familien.index(start))
        ctrl.connect("notify::selected", lambda d, *_: anwenden(w, schluessel, w.familien[d.get_selected()]))
    elif t in ("zahl", "range"):
        ctrl = Gtk.SpinButton.new_with_range(f.get("min", 0), f.get("max", 100), 1)
        ctrl.set_valign(Gtk.Align.CENTER)
        ctrl.set_value(float(start if start is not None else f.get("v", 0)))
        ctrl.connect("value-changed", lambda s: anwenden(w, schluessel, int(s.get_value())))
    elif t == "text":
        ctrl = Gtk.Entry(hexpand=False, valign=Gtk.Align.CENTER, width_chars=26)
        if f.get("unter"):
            ctrl.set_text(w.werte.setdefault(f["unter"], {}).get(f["schluessel"], ""))
            ctrl.connect("changed", lambda e: w.werte.setdefault(f["unter"], {}).__setitem__(f["schluessel"], e.get_text()))
        else:
            ctrl.set_text(str(start or ""))
            ctrl.connect("changed", lambda e: anwenden(w, schluessel, e.get_text()))
    elif t == "pfadtext":
        ctrl = Gtk.Label(label=f["v"], selectable=True, xalign=1)
        ctrl.add_css_class("dim-label")
    elif t == "ordner":
        ctrl = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        lab = Gtk.Label(label=w.werte.get("ordner_oeffnen") or "(Persönlicher Ordner)", xalign=0)
        lab.set_ellipsize(3)
        ctrl.append(lab)
        wahl = Gtk.Button(label="Wählen …")

        def waehlen(*_):
            fd = Gtk.FileDialog(title="Ordner zum Speichern")

            def fertig(fd, res):
                try:
                    o = fd.select_folder_finish(res)
                except GLib.Error:
                    return
                w.werte["ordner_oeffnen"] = o.get_path()
                lab.set_text(o.get_path())
            fd.select_folder(w, None, fertig)
        wahl.connect("clicked", waehlen)
        zur = Gtk.Button(label="Zurücksetzen")
        zur.connect("clicked", lambda *_: (w.werte.pop("ordner_oeffnen", None), lab.set_text("(Persönlicher Ordner)")))
        ctrl.append(wahl)
        ctrl.append(zur)
    elif t == "befehl":
        ctrl = Gtk.Button(label=f["knopf"], valign=Gtk.Align.CENTER)
        ctrl.connect("clicked", lambda *_: befehle_ausfuehren(w, f["befehl"]))
    elif t == "seite":
        ctrl = Gtk.Button(label="Öffnen", valign=Gtk.Align.CENTER)
        ctrl.connect("clicked", lambda *_: w._optionen_seite(f["ziel"]))
    elif t == "kennwort":
        d = w.dok()
        box = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        e = Gtk.Entry(visibility=False, placeholder_text="Kennwort", width_chars=18)
        setzen = Gtk.Button(label="Kennwort setzen")
        weg = Gtk.Button(label="Kennwort entfernen")
        stand = Gtk.Label(label="")
        stand.add_css_class("dim-label")

        def zeige():
            stand.set_text("Mit Kennwort geschützt." if d is not None and getattr(d, "kennwort", None) else
                           "Ohne Kennwort — die Datei ist im Klartext lesbar.")
        zeige()

        def los(neu):
            if d is None:
                return
            d.kennwort = neu or None
            d.puffer.set_modified(True)
            zeige()
        setzen.connect("clicked", lambda *_: (los(e.get_text()), e.set_text("")))
        weg.connect("clicked", lambda *_: los(None))
        for x in (e, setzen, weg):
            box.append(x)
        text.append(stand)
        ctrl = box
    elif t == "lesenschriften":
        ctrl = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        for n in ("OpenDyslexic", "Lexend", "Atkinson Hyperlegible"):
            b = Gtk.Button(label=n)
            if n in w.familien:
                b.connect("clicked", lambda _b, n=n: (w.werte.__setitem__("schriftart", n), w.status("Schrift für neue Dokumente: " + n)))
            else:
                b.set_sensitive(False)
                b.set_tooltip_text("Noch nicht geholt (Erweitert).")
            ctrl.append(b)
        holen_b = Gtk.Button(label="Jetzt holen …")
        holen_b.connect("clicked", lambda *_: _schriften_holen(w, holen_b))
        ctrl.append(holen_b)
    elif t == "gedaechtnis":
        ctrl = _gedaechtnis(w)
    if ctrl is not None:
        zeile.append(ctrl)
    # Erklärung beim Überfahren in die Fußzeile
    if f.get("h"):
        m = Gtk.EventControllerMotion()
        m.connect("enter", lambda *_: hinweis.set_text(f["h"]))
        zeile.add_controller(m)
    return zeile


def _schriften_holen(w, knopf):
    skript = os.path.join(pfade.PROJEKT, "schrift-holen.sh")
    if not os.path.exists(skript):
        return w.meldung("Schriften", "schrift-holen.sh fehlt im Projektordner.")
    knopf.set_sensitive(False)
    w.status("Schriften werden geholt …")

    def arbeit():
        lauf = subprocess.run(["bash", skript, "--alle"], capture_output=True, text=True, timeout=300)
        GLib.idle_add(lambda: (knopf.set_sensitive(True), w.meldung("Schriften", (lauf.stdout + lauf.stderr)[-800:] or "Fertig.")))
    threading.Thread(target=arbeit, daemon=True).start()


def _gedaechtnis(w):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    gelernt = schreibhilfe.gelernt()
    eigene = w.werte.get("eigene_woerter", [])
    box.append(Gtk.Label(label="%d gelernte Schreibweisen, %d eigene Wörter" % (len(gelernt["woerter"]), len(eigene)), xalign=0))
    lb = Gtk.ListBox()
    rolle = Gtk.ScrolledWindow(min_content_height=140)
    rolle.set_child(lb)
    box.append(rolle)

    def fuellen():
        k = lb.get_first_child()
        while k:
            n = k.get_next_sibling()
            lb.remove(k)
            k = n
        for falsch, richtig in sorted(gelernt["woerter"].items()):
            lb.append(Gtk.Label(label="%s  →  %s" % (falsch, richtig), xalign=0))
        for wort in w.werte.get("eigene_woerter", []):
            lb.append(Gtk.Label(label="%s  (gilt als richtig)" % wort, xalign=0))
        if not (gelernt["woerter"] or w.werte.get("eigene_woerter")):
            lb.append(Gtk.Label(label="Noch nichts gelernt. Jedes „Ändern“ bringt dem Programm etwas bei.", xalign=0))
    fuellen()
    z = Gtk.Box(spacing=6)
    sichern = Gtk.Button(label="⧉ Sichern")
    sichern.connect("clicked", lambda *_: (w.get_clipboard().set(json.dumps({"woerter": gelernt["woerter"], "eigene": w.werte.get("eigene_woerter", [])},
                                                                           ensure_ascii=False)), w.status("Gesichert — liegt in der Zwischenablage.")))
    spielen = Gtk.Button(label="⤓ Einspielen")

    def einspielen(*_):
        def fertig(cb, res):
            try:
                t = cb.read_text_finish(res)
                j = json.loads(t)
            except Exception:
                return w.meldung("Einspielen", "In der Zwischenablage steht kein gesichertes Gedächtnis.")
            n = 0
            for wort in j.get("eigene", []):
                if wort not in w.werte.setdefault("eigene_woerter", []):
                    w.werte["eigene_woerter"].append(wort)
                    n += 1
            w.status("Eingespielt: %d neue Wörter." % n)
            fuellen()
        w.get_clipboard().read_text_async(None, fertig)
    spielen.connect("clicked", einspielen)
    z.append(sichern)
    z.append(spielen)
    box.append(z)
    return box


def _seite_band(w):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.append(Gtk.Label(label="Welche Reiter im Band stehen.", xalign=0))
    b = Gtk.Button(label="Reiter wählen …")
    b.connect("clicked", lambda *_: befehle_ausfuehren(w, "register_anpassen"))
    box.append(b)
    return box


def _seite_schnell(w):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.append(Gtk.Label(label="Was im Schnellzugriff neben dem Menü steht.", xalign=0))
    angebot = [("neu", "Neu"), ("oeffnen", "Öffnen"), ("speichern", "Speichern"), ("speichern_pdf", "Als PDF exportieren"),
               ("drucken", "Drucken"), ("vorschau", "Druckvorschau"), ("rueckgaengig", "Rückgängig"), ("wiederholen", "Wiederholen"),
               ("pruefen", "Prüfen"), ("fett", "Fett"), ("kursiv", "Kursiv"), ("suchen", "Suchen")]
    aktiv = set(w.werte.get("schnellzugriff", ["oeffnen", "speichern", "speichern_pdf", "drucken", "vorschau", "rueckgaengig", "wiederholen"]))
    for k, t in angebot:
        c = Gtk.CheckButton(label=t, active=k in aktiv)

        def los(cb, k=k):
            (aktiv.add if cb.get_active() else aktiv.discard)(k)
            w.werte["schnellzugriff"] = [x for x, _t in angebot if x in aktiv]
            w.schnellzugriff_neu()
        c.connect("toggled", los)
        box.append(c)
    return box


def seite_bauen(w, kennung, hinweis):
    spalte = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    for r in ("start", "end"):
        getattr(spalte, "set_margin_" + r)(36)
    spalte.set_margin_top(18)
    spalte.set_margin_bottom(18)
    if kennung == "band":
        spalte.append(_seite_band(w))
    elif kennung == "schnellzugriff":
        spalte.append(_seite_schnell(w))
    else:
        for abschnitt in daten().get(kennung, []):
            kopf = Gtk.Label(label=abschnitt["kopf"].upper(), xalign=0)
            kopf.add_css_class("abschnitt")
            kopf.set_margin_top(10)
            spalte.append(kopf)
            karte = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            karte.add_css_class("optkarte")
            for i, f in enumerate(abschnitt["felder"]):
                if i:
                    karte.append(Gtk.Separator())
                karte.append(_karte_zeile(w, kennung, f, hinweis))
            spalte.append(karte)
    rolle = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
    rolle.set_child(spalte)
    return rolle


class Optionen(Gtk.Window):
    def __init__(self, w, seite=None):
        super().__init__(transient_for=w, title="Optionen")
        self.w = w
        self.set_default_size(980, 640)
        kopf = Gtk.HeaderBar()
        zurueck = Gtk.Button(label="←")
        zurueck.add_css_class("flat")
        zurueck.connect("clicked", lambda *_: self.close())
        kopf.pack_start(zurueck)
        t = Gtk.Label(label="Optionen")
        t.add_css_class("title-4")
        kopf.set_title_widget(t)
        self.set_titlebar(kopf)
        haupt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        mitte = Gtk.Box(vexpand=True)
        haupt.append(mitte)
        self.stack = Gtk.Stack()
        self.hinweis = Gtk.Label(label="Zeig auf eine Einstellung — hier steht, was sie tut.", xalign=0, wrap=True)
        self.hinweis.add_css_class("dim-label")
        self.liste = Gtk.ListBox()
        self.liste.add_css_class("navigation-sidebar")
        self.ids = []
        for gruppe, eintr in GRUPPEN:
            k = Gtk.ListBoxRow(selectable=False, activatable=False)
            l = Gtk.Label(label="▾  " + gruppe, xalign=0)
            l.add_css_class("heading")
            l.set_margin_top(12)
            l.set_margin_start(10)
            k.set_child(l)
            self.liste.append(k)
            self.ids.append(None)
            for kenn, name in eintr:
                zeile = Gtk.ListBoxRow()
                lb = Gtk.Label(label=name, xalign=0, wrap=True)
                lb.set_margin_start(22)
                lb.set_margin_top(5)
                lb.set_margin_bottom(5)
                zeile.set_child(lb)
                self.liste.append(zeile)
                self.ids.append(kenn)
                self.stack.add_named(seite_bauen(w, kenn, self.hinweis), kenn)
        self.liste.connect("row-selected", self._gewaehlt)
        links = Gtk.ScrolledWindow(vexpand=True)
        links.set_size_request(240, -1)
        links.set_child(self.liste)
        mitte.append(links)
        mitte.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        mitte.append(self.stack)
        fuss = Gtk.Box(spacing=10)
        fuss.set_margin_start(12)
        fuss.set_margin_end(12)
        fuss.set_margin_top(6)
        fuss.set_margin_bottom(6)
        self.hinweis.set_hexpand(True)
        fuss.append(self.hinweis)
        fertig = Gtk.Button(label="Fertig")
        fertig.add_css_class("suggested-action")
        fertig.connect("clicked", lambda *_: self.close())
        fuss.append(fertig)
        haupt.append(Gtk.Separator())
        haupt.append(fuss)
        self.set_child(haupt)
        self.zeige(seite or "lesehilfe")
        self.connect("close-request", lambda *_: (einstellungen.schreiben(w.werte), False)[1])

    def zeige(self, kennung):
        if kennung in self.ids:
            self.liste.select_row(self.liste.get_row_at_index(self.ids.index(kennung)))

    def _gewaehlt(self, liste, zeile):
        if zeile is not None and self.ids[zeile.get_index()]:
            self.stack.set_visible_child_name(self.ids[zeile.get_index()])


def oeffnen(w, seite=None):
    if getattr(w, "_optionen_fenster", None) is not None and w._optionen_fenster.get_visible():
        w._optionen_fenster.zeige(seite or "lesehilfe")
        w._optionen_fenster.present()
        return
    w._optionen_fenster = Optionen(w, seite)
    w._optionen_fenster.present()
    w._optionen_seite = lambda s: w._optionen_fenster.zeige(s)
