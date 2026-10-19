"""Reiter Sendungen: Umschlag, Etiketten, Seriendruck, Formularfelder."""
import csv
import io
import re

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402

from . import befehl, klappe, hilfen
from .. import html_io, objekte


def _d(w):
    return w.dok()


def _absender(w):
    b = w.werte.get("benutzer", {})
    zeilen = [(b.get("vorname", "") + " " + b.get("nachname", "")).strip(), b.get("strasse", ""),
              (b.get("plz", "") + " " + b.get("ort", "")).strip()]
    return "\n".join(z for z in zeilen if z)


# ================================================================ Umschlag
@befehl("umschlag")
def _umschlag(w, _=None):
    dlg = Gtk.Window(transient_for=w, modal=True, title="Umschlag")
    dlg.set_default_size(460, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    fmt = Gtk.DropDown.new_from_strings(["DIN lang (220 × 110)", "C5 (229 × 162)", "C6 (162 × 114)"])
    box.append(fmt)
    box.append(Gtk.Label(label="Empfänger", xalign=0))
    emp = Gtk.TextView()
    emp.set_size_request(-1, 90)
    emp.get_buffer().set_text("Frau\nMaria Muster\nMusterstraße 1\n12345 Musterstadt")
    box.append(emp)
    box.append(Gtk.Label(label="Absender", xalign=0))
    ab = Gtk.TextView()
    ab.set_size_request(-1, 60)
    ab.get_buffer().set_text(_absender(w))
    box.append(ab)

    def ok(*_):
        def lesen(tv):
            b = tv.get_buffer()
            return b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        papier = ["dinlang", "c5", "c6"][fmt.get_selected()]
        d = w.neu()
        d.titel = "Umschlag"
        d.seite_setzen(papier=papier, quer=True, rand={"oben": 10, "unten": 10, "links": 12, "rechts": 12})
        d.puffer.set_text("")
        for text, tags in ((lesen(ab) + "\n\n\n", ("size:9",)), (lesen(emp), ("size:13", "ein:260"))):
            von = d.puffer.get_end_iter().get_offset()
            d.puffer.insert(d.puffer.get_end_iter(), text)
            for n in tags:
                d.puffer.apply_tag(html_io.tag_holen(d.puffer, n), d.puffer.get_iter_at_offset(von), d.puffer.get_end_iter())
        dlg.close()
    gut = Gtk.Button(label="Umschlag erstellen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


# ================================================================ Etiketten
FORMATE = {
    "3 × 8 — 70 × 36 mm (Zweckform L4730)": (3, 8, 70, 36, {"oben": 9, "unten": 9, "links": 0, "rechts": 0}),
    "3 × 7 — 63,5 × 38,1 mm (Avery L7160)": (3, 7, 63.5, 38.1, {"oben": 15, "unten": 15, "links": 7, "rechts": 7}),
    "2 × 4 — 99,1 × 67,7 mm (Avery L7165)": (2, 4, 99.1, 67.7, {"oben": 13, "unten": 13, "links": 5, "rechts": 5}),
    "2 × 7 — 99,1 × 38,1 mm (Avery L7163)": (2, 7, 99.1, 38.1, {"oben": 15, "unten": 15, "links": 5, "rechts": 5}),
}


@befehl("etiketten")
def _etiketten(w, _=None):
    dlg = Gtk.Window(transient_for=w, modal=True, title="Etiketten")
    dlg.set_default_size(460, 380)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    fmt = Gtk.DropDown.new_from_strings(list(FORMATE))
    box.append(fmt)
    box.append(Gtk.Label(label="Inhalt eines Etiketts (wird auf dem ganzen Bogen wiederholt)", xalign=0))
    tv = Gtk.TextView()
    tv.set_size_request(-1, 100)
    tv.get_buffer().set_text(_absender(w) or "Name\nStraße\nPLZ Ort")
    box.append(tv)
    nur_eins = Gtk.CheckButton(label="Nur das erste Etikett füllen")
    box.append(nur_eins)

    def ok(*_):
        sp, ze, bb, hh, rand = FORMATE[list(FORMATE)[fmt.get_selected()]]
        b = tv.get_buffer()
        text = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        zellen = [[(text if (not nur_eins.get_active() or (r == 0 and c == 0)) else "") for c in range(sp)] for r in range(ze)]
        d = w.neu()
        d.titel = "Etiketten"
        d.seite_setzen(papier="a4", quer=False, rand=rand)
        daten = objekte.tabelle_daten(ze, sp, zellen)
        daten["kopf"] = False
        daten["rand"] = False
        d.puffer.set_text("")
        d.objekt_einfuegen(daten)
        dlg.close()
    gut = Gtk.Button(label="Bogen erstellen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


# ================================================================ Seriendruck
def _serie(d):
    return d.meta.setdefault("serie", {"spalten": [], "daten": [], "datei": ""})


def _daten_aus_csv(text):
    try:
        dialekt = csv.Sniffer().sniff(text[:2000], delimiters=";,\t")
    except csv.Error:
        dialekt = csv.excel
        dialekt.delimiter = ";"
    zeilen = list(csv.reader(io.StringIO(text), dialekt))
    zeilen = [z for z in zeilen if any(x.strip() for x in z)]
    if not zeilen:
        return [], []
    return [x.strip() for x in zeilen[0]], [[x.strip() for x in z] + [""] * (len(zeilen[0]) - len(z)) for z in zeilen[1:]]


@befehl("seriendruck")
def _seriendruck(w, _=None):
    d = _d(w)
    if not d:
        return
    s = _serie(d)
    dlg = Gtk.Window(transient_for=w, modal=True, title="Seriendruck-Assistent")
    dlg.set_default_size(620, 520)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="1. Datenquelle: Tabelle (Kopfzeile = Feldnamen), Trennzeichen ; , oder Tab. "
                               "2. Felder mit „Seriendruckfeld“ in den Brief setzen. 3. Ergebnisse prüfen. 4. Fertigstellen.",
                         xalign=0, wrap=True))
    tv = Gtk.TextView()
    tv.set_monospace(True)
    vorgabe = ";".join(s["spalten"]) + "\n" + "\n".join(";".join(z) for z in s["daten"]) if s["spalten"] else \
        "Anrede;Vorname;Nachname;Straße;PLZ;Ort\nFrau;Maria;Muster;Musterstraße 1;12345;Musterstadt\nHerr;Max;Mustermann;Hauptstraße 5;54321;Beispielstadt"
    tv.get_buffer().set_text(vorgabe)
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(tv)
    box.append(rolle)
    zeile = Gtk.Box(spacing=6)
    laden = Gtk.Button(label="Aus Datei laden …")

    def aus_datei(*_):
        fd = Gtk.FileDialog(title="Datenquelle (CSV)")

        def fertig(fd, res):
            try:
                f = fd.open_finish(res)
            except GLib.Error:
                return
            try:
                with open(f.get_path(), encoding="utf-8-sig", errors="replace") as fh:
                    tv.get_buffer().set_text(fh.read())
                s["datei"] = f.get_path()
            except OSError as e:
                w.meldung("Datei nicht lesbar", str(e))
        fd.open(dlg, None, fertig)
    laden.connect("clicked", aus_datei)
    zeile.append(laden)
    box.append(zeile)

    def ok(*_):
        b = tv.get_buffer()
        kopf, daten = _daten_aus_csv(b.get_text(b.get_start_iter(), b.get_end_iter(), False))
        if not kopf:
            return w.meldung("Datenquelle leer", "Die erste Zeile muss die Feldnamen enthalten.")
        s["spalten"], s["daten"] = kopf, daten
        d.puffer.set_modified(True)
        w.status("Datenquelle: %d Felder, %d Datensätze. Felder über „Seriendruckfeld“ einfügen." % (len(kopf), len(daten)))
        dlg.close()
    gut = Gtk.Button(label="Übernehmen")
    gut.add_css_class("suggested-action")
    gut.connect("clicked", ok)
    box.append(gut)
    dlg.present()


def _feld_tag(name):
    return "feld:" + name


@befehl("seriendruckfeld")
def _seriendruckfeld(w, _=None):
    d = _d(w)
    if not d:
        return
    s = _serie(d)
    if not s["spalten"]:
        return _seriendruck(w)
    dlg = Gtk.AlertDialog()
    dlg.set_message("Seriendruckfeld einfügen")
    felder = s["spalten"][:7]
    dlg.set_buttons(felder + ["Abbrechen"])
    dlg.set_cancel_button(len(felder))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(felder):
            d.text_einfuegen("«%s»" % felder[n], (_feld_tag(felder[n]),))
    dlg.choose(w, None, fertig)


@befehl("adressblock")
def _adressblock(w, _=None):
    d = _d(w)
    if not d:
        return
    s = _serie(d)
    if not s["spalten"]:
        return _seriendruck(w)

    def hat(n):
        return n if n in s["spalten"] else None
    zeilen = [[hat("Anrede")], [hat("Vorname"), hat("Nachname")], [hat("Straße") or hat("Strasse")], [hat("PLZ"), hat("Ort")]]
    d.puffer.begin_user_action()
    for z in zeilen:
        felder = [f for f in z if f]
        for i, f in enumerate(felder):
            d.text_einfuegen("«%s»" % f, (_feld_tag(f),))
            if i < len(felder) - 1:
                d.text_einfuegen(" ")
        if felder:
            d.text_einfuegen("\n")
    d.puffer.end_user_action()


@befehl("seriendruckregel")
def _regel(w, _=None):
    d = _d(w)
    if not d:
        return
    s = _serie(d)
    if not s["spalten"]:
        return _seriendruck(w)

    def ok(v):
        feld, op, wert, dann, sonst = v
        if feld not in s["spalten"] or op not in ("=", "≠", "leer", "nicht leer"):
            return w.meldung("Regel", "Feld muss eine Spalte der Datenquelle sein; Vergleich: =, ≠, leer oder nicht leer.")
        txt = "«WENN %s %s %s: %s | %s»" % (feld, op, wert, dann, sonst)
        d.text_einfuegen(txt, ("regel:wenn",))
    hilfen.frage(w, "Seriendruck-Regel (WENN … DANN … SONST)", [("Feld", s["spalten"][0]), ("Vergleich (=, ≠, leer, nicht leer)", "="),
                                                                  ("Wert", ""), ("Dann einfügen", ""), ("Sonst einfügen", "")], ok)


def _regel_anwenden(text, s, satz):
    daten = dict(zip(s["spalten"], s["daten"][satz]))

    def wenn(m):
        feld, op, wert, dann, sonst = m.group(1), m.group(2), m.group(3).strip(), m.group(4).strip(), m.group(5).strip()
        ist = daten.get(feld, "")
        ok = {"=": ist == wert, "≠": ist != wert, "leer": not ist, "nicht leer": bool(ist)}[op]
        return dann if ok else sonst
    text = re.sub(r"«WENN (\S+) (=|≠|leer|nicht leer) ?([^:]*): ([^|]*)\|([^»]*)»", wenn, text)
    for k, v in daten.items():
        text = text.replace("«%s»" % k, v)
    return text


def _satz_text(d, satz):
    s = _serie(d)
    return _regel_anwenden(d.text(), s, satz)


@befehl("serien_vorschau")
def _vorschau(w, _=None):
    d = _d(w)
    if not d:
        return
    s = _serie(d)
    if not s["daten"]:
        return w.meldung("Seriendruck", "Noch keine Datenquelle (Sendungen ▸ Seriendruck-Assistent).")
    an = not w.werte["an"].get("serienvorschau", False)
    w.werte["an"]["serienvorschau"] = an
    w.band_auffrischen()
    if an:
        d._serie_original = d.text()
        d._serie_satz = 0
        _vorschau_zeigen(w, d)
        w.status("Vorschau: Datensatz 1 von %d (Strg+Pfeil oben/unten wechselt)." % len(s["daten"]))
    else:
        _vorschau_aus(w, d)


def _vorschau_zeigen(w, d):
    # Original sichern (HTML), Vorschau als reiner Text darüber legen
    if not hasattr(d, "_serie_html"):
        d._serie_html = html_io.puffer_in_html(d.puffer, "x", d.meta_aktuell())
    s = _serie(d)
    d._serie_satz = max(0, min(d._serie_satz, len(s["daten"]) - 1))
    neu = _regel_anwenden(d._serie_original, s, d._serie_satz)
    d._intern = True
    d.puffer.begin_irreversible_action()
    d.puffer.set_text(neu.replace("￼", ""))
    d.puffer.end_irreversible_action()
    d._intern = False
    d.ansicht.set_editable(False)


def _vorschau_aus(w, d):
    if hasattr(d, "_serie_html"):
        meta = d.meta
        html_io.html_in_puffer(d.puffer, d._serie_html)
        d.objekte_anbinden()
        d.meta = meta
        del d._serie_html
    d.ansicht.set_editable(True)
    w.status("Vorschau beendet.")


@befehl("seriendruck_fertig")
def _fertig(w, _=None):
    d = _d(w)
    if not d:
        return
    s = _serie(d)
    if not s["daten"]:
        return
    original = d._serie_original if hasattr(d, "_serie_original") and hasattr(d, "_serie_html") else d.text()
    neu = w.neu()
    neu.titel = "Serienbrief"
    teile = [_regel_anwenden(original, s, i) for i in range(len(s["daten"]))]
    from .einfuegen import _seitenumbruch
    neu.puffer.set_text(teile[0].replace("￼", ""))
    for t in teile[1:]:
        neu.puffer.place_cursor(neu.puffer.get_end_iter())
        w._neu_dok = neu
        neu.puffer.insert_at_cursor("\n⁂ Seitenumbruch ⁂\n")
        o = neu.puffer.get_end_iter().get_offset() - len("⁂ Seitenumbruch ⁂\n")
        neu.puffer.apply_tag(html_io.tag_holen(neu.puffer, "umbruch"), neu.puffer.get_iter_at_offset(o), neu.puffer.get_end_iter())
        neu.puffer.insert(neu.puffer.get_end_iter(), t.replace("￼", ""))
    w.status("%d Briefe in einem neuen Dokument erstellt." % len(teile))


# ================================================================ Formular
def _form(w, daten):
    d = _d(w)
    if d:
        d.objekt_einfuegen(daten)


@befehl("form_textfeld")
def _ftext(w, _=None):
    hilfen.frage(w, "Textfeld", [("Name des Feldes", "Name")], lambda v: _form(w, {"typ": "form_text", "name": v[0], "wert": "", "breite": 24}))


@befehl("form_kasten")
def _fkasten(w, _=None):
    hilfen.frage(w, "Kontrollkästchen", [("Beschriftung", "Ja")], lambda v: _form(w, {"typ": "form_kasten", "name": v[0], "an": False}))


@befehl("form_knopf")
def _fknopf(w, _=None):
    hilfen.frage(w, "Schaltfläche", [("Beschriftung", "Drucken")], lambda v: _form_knopf_neu(w, v[0]))


def _form_knopf_neu(w, name):
    d = _d(w)
    if not d:
        return
    from . import ausfuehren
    daten = {"typ": "form_knopf", "name": name}
    kleinname = name.lower()
    ziel = "drucken" if "druck" in kleinname else "speichern" if "speich" in kleinname else "neu" if "neu" in kleinname else None
    daten["klick"] = (lambda: ausfuehren(w, ziel)) if ziel else (lambda: w.status("Schaltfläche „%s“." % name))
    d.objekt_einfuegen(daten)
