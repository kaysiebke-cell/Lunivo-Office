"""Reiter Überprüfen: Prüfung, Rechtschreibung, Thesaurus, Kommentare, Änderungen, Schutz."""
import datetime
import re
import threading

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk  # noqa: E402

from . import befehl, klappe, hilfen
from .. import html_io, schreibhilfe, sprachdienste


def _d(w):
    return w.dok()


# ================================================================ Gründlich prüfen
@befehl("gruendlich_pruefen")
def _gruendlich(w, _=None):
    d = _d(w)
    if not d:
        return
    w.seitenleiste.set_visible(True)
    text = d.text()
    sprache = w.werte.get("sprache", "de_DE")
    eigene = set(w.werte.get("eigene_woerter", []))
    w.status("Prüfe gründlich …")
    w.schreibhilfe.pruef_knopf.set_sensitive(False)

    def arbeit():
        try:
            funde = schreibhilfe.pruefen(text)
            if schreibhilfe._eigene_pruefung() is None:       # ohne die eigene Prüfung: Wörterbuch dazu
                for a, b, wort, vor in sprachdienste.pruefen(text, sprache, eigene):
                    funde.append({"von": a, "bis": b, "alt": wort, "neu": vor[0] if vor else None,
                                  "zeigeAlt": wort, "zeigeNeu": ", ".join(vor[:3]) or "(kein Vorschlag)",
                                  "grund": "Rechtschreibung: „%s“" % wort, "art": "fehler"})
            funde.sort(key=lambda f: f["von"])
            GLib.idle_add(_fertig, w, d, text, funde, None)
        except Exception as e:
            GLib.idle_add(_fertig, w, d, text, [], str(e))
    threading.Thread(target=arbeit, daemon=True).start()


def _fertig(w, d, text, funde, fehler):
    from .schreibhilfe_tab import _fertig as basis
    basis(w, d, text, funde, fehler)


# ================================================================ Rechtschreibung
def _rs_anwenden(w):
    an = w.schalten("rechtschreibung", w.werte["an"].get("rechtschreibung", False))
    for d in w.alle_dokumente():
        d.rechtschreibung(an, w.werte.get("sprache", "de_DE"), w.werte.get("eigene_woerter", []))


@befehl("rechtschreibung")
def _rechtschreibung(w, _=None):
    an = not w.werte["an"].get("rechtschreibung", False)
    w.werte["an"]["rechtschreibung"] = an
    for d in w.alle_dokumente():
        d.rechtschreibung(an, w.werte.get("sprache", "de_DE"), w.werte.get("eigene_woerter", []))
    w.band_auffrischen()
    w.status("Rechtschreibprüfung %s." % ("ein" if an else "aus"))


def sprachwahl_eintraege(w):
    eintr = []
    for kuerzel, name in sprachdienste.sprachen_da():
        def setze(k=kuerzel):
            w.werte["sprache"] = k
            for d in w.alle_dokumente():
                d.rechtschreibung(w.werte["an"].get("rechtschreibung", False), k)
            w.status("Korrektursprache: %s" % k)
        eintr.append(((("✓ " if w.werte.get("sprache", "de_DE") == kuerzel else "") + name), setze))
    return eintr


@befehl("pruefsprache")
def _pruefsprache(w, _=None):
    eintr = sprachwahl_eintraege(w)
    if not eintr:
        return w.meldung("Korrektursprache", "Es sind keine Wörterbücher (Hunspell) installiert.")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Korrektursprache")
    dlg.set_buttons([e[0] for e in eintr] + ["Abbrechen"])
    dlg.set_cancel_button(len(eintr))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(eintr):
            eintr[n][1]()
    dlg.choose(w, None, fertig)


@klappe("pruefung_klappe")
def _pruefung_klappe(w, pop):
    return hilfen.liste(pop, sprachwahl_eintraege(w))


# ================================================================ Thesaurus
@befehl("thesaurus")
def _thesaurus(w, _=None):
    d = _d(w)
    z = d._ziel() if d else None
    if not z:
        return w.status("Cursor in ein Wort setzen oder ein Wort auswählen.")
    wort = d.puffer.get_text(*z, False).strip()
    von, bis = z[0].get_offset(), z[1].get_offset()
    gruppen = sprachdienste.synonyme(wort, w.werte.get("sprache", "de_DE"))
    if not gruppen:
        gruppen = sprachdienste.synonyme(wort.lower(), w.werte.get("sprache", "de_DE")) or sprachdienste.synonyme(wort.capitalize())
    dlg = Gtk.Window(transient_for=w, modal=True, title="Thesaurus: %s" % wort)
    dlg.set_default_size(420, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(12)
    dlg.set_child(box)
    if not gruppen:
        box.append(Gtk.Label(label="Zu „%s“ gibt es keinen Eintrag." % wort))
    liste = Gtk.ListBox()
    for art, syn in gruppen:
        for s in syn:
            liste.append(Gtk.Label(label=s, xalign=0))
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(liste)
    box.append(rolle)
    ok = Gtk.Button(label="Wort ersetzen")
    ok.add_css_class("suggested-action")

    def ersetzen(*_):
        r = liste.get_selected_row()
        if r:
            neu = re.sub(r"\s*\(.*?\)\s*", "", r.get_child().get_text()).strip(" .") or r.get_child().get_text()
            d.bereich_ersetzen(von, bis, neu)
            dlg.close()
    ok.connect("clicked", ersetzen)
    liste.connect("row-activated", lambda *_: ersetzen())
    box.append(ok)
    dlg.present()


# ================================================================ Wörter zählen
@befehl("woerter_zaehlen")
def _woerter(w, _=None):
    d = _d(w)
    if not d:
        return
    sel = d.puffer.get_selection_bounds()
    text = (d.puffer.get_slice(*sel, True) if sel else d.text()).replace("\ufffc", " ")
    woerter = text.split()
    saetze = len([s for s in re.split(r"[.!?]+(?:\s|$)", text) if s.strip()])
    absaetze = len([z for z in text.split("\n") if z.strip()])
    zeichen = len(text.replace("\n", ""))
    ohne = len("".join(text.split()))
    sekunden = int(len(woerter) / 200 * 60)
    w.meldung("Wörter zählen" + (" (Auswahl)" if sel else ""),
              "Wörter: %d\nZeichen (mit Leerzeichen): %d\nZeichen (ohne Leerzeichen): %d\nSätze: %d\nAbsätze: %d\n"
              "Seiten (geschätzt): %d\nLesezeit: etwa %d min %02d s" % (
                  len(woerter), zeichen, ohne, saetze, absaetze, d.seite_stand()[1], sekunden // 60, sekunden % 60))


# ================================================================ Barrierefreiheit
@befehl("barrierefrei")
def _barrierefrei(w, _=None):
    d = _d(w)
    if not d:
        return
    probleme, ok = [], []
    for a, _o in d.alle_objekte():
        if a.daten["typ"] in ("bild", "svg") and not (a.daten.get("alt") or "").strip():
            probleme.append("Bild ohne Alternativtext.")
        if a.daten["typ"] == "tabelle" and not a.daten.get("kopf"):
            probleme.append("Tabelle ohne Kopfzeile.")
    uebs = d.ueberschriften()
    letzte = 0
    for ebene, text, nr in uebs:
        if letzte and ebene > letzte + 1:
            probleme.append("Überschrift „%s“ überspringt eine Ebene (H%d nach H%d)." % (text[:30], ebene, letzte))
        letzte = ebene
    if not uebs and len(d.text()) > 1500:
        probleme.append("Langer Text ohne Überschriften – Gliederung hilft beim Navigieren.")
    for nr in range(d.puffer.get_line_count()):
        _, von = d.puffer.get_iter_at_line(nr)
        ende = von.copy()
        if not ende.ends_line():
            ende.forward_to_line_end()
        z = d.puffer.get_text(von, ende, False)
        if len(z.split()) > 120:
            probleme.append("Sehr langer Absatz in Zeile %d (%d Wörter)." % (nr + 1, len(z.split())))
        if re.search(r"\b(hier|mehr|klicken Sie)\b", z, re.I) and any((t.props.name or "").startswith("link:") for t in von.get_tags()):
            probleme.append("Linktext „hier“/„mehr“ in Zeile %d sagt nicht, wohin er führt." % (nr + 1))
    # Kontrast der Schriftfarben gegen die Seitenfarbe
    seite = d.seite.get("seitenfarbe", "#FFFFFF")
    for n in html_io.zeichen_namen(d.puffer):
        if n.startswith("col:") and _kontrast(n[4:], seite) < 4.5:
            probleme.append("Schriftfarbe %s hat zu wenig Kontrast zur Seitenfarbe." % n[4:])
    if not d.puffer.get_char_count():
        ok.append("Das Dokument ist leer.")
    if not probleme:
        ok.append("Keine Auffälligkeiten gefunden.")
    w.meldung("Barrierefreiheit prüfen", "\n".join(["• " + p for p in probleme] + ok))


def _lum(h):
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _kontrast(a, b):
    try:
        la, lb = _lum(a), _lum(b)
    except (ValueError, IndexError):
        return 21
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ================================================================ Kommentare
def _kommentare(d):
    return d.meta.setdefault("kommentare", {})


def _kom_tags(d):
    return sorted(t[4:] for t in html_io.zeichen_namen(d.puffer) if t.startswith("kom:"))


@befehl("kommentar")
def _kommentar(w, _=None):
    d = _d(w)
    if not d:
        return
    sel = d.puffer.get_selection_bounds() or d._ziel()
    if not sel:
        return w.status("Text auswählen, zu dem der Kommentar gehört.")

    def ok(v):
        if not v[0].strip():
            return
        kid = "k%d" % (max([int(k[1:]) for k in _kommentare(d)] + [0]) + 1)
        _kommentare(d)[kid] = {"text": v[0].strip(), "autor": w.werte.get("benutzer_name", "Ich"),
                               "zeit": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
        d.puffer.apply_tag(html_io.tag_holen(d.puffer, "kom:" + kid), *sel)
        d.puffer.set_modified(True)
        w.status("Kommentar eingefügt.")
    hilfen.frage(w, "Neuer Kommentar", [("Kommentar", "")], ok)


def _kom_orte(d):
    erg = []
    for kid in _kom_tags(d):
        tag = d.puffer.get_tag_table().lookup("kom:" + kid)
        it = d.puffer.get_start_iter()
        if it.starts_tag(tag) or it.forward_to_tag_toggle(tag):
            erg.append((it.get_offset(), kid))
    return sorted(erg)


def _kom_springen(w, vor):
    d = _d(w)
    if not d:
        return
    orte = _kom_orte(d)
    if not orte:
        return w.status("Keine Kommentare im Dokument.")
    pos = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_offset()
    kand = [o for o in orte if (o[0] > pos if vor else o[0] < pos)]
    o, kid = (kand[0] if vor else kand[-1]) if kand else (orte[0] if vor else orte[-1])
    it = d.puffer.get_iter_at_offset(o)
    d.puffer.place_cursor(it)
    d.ansicht.scroll_to_iter(it, 0.1, True, 0, 0.3)
    k = _kommentare(d).get(kid, {})
    w.status("%s (%s): %s" % (k.get("autor", ""), k.get("zeit", ""), k.get("text", "")))


@befehl("kommentar_weiter")
def _kom_weiter(w, _=None):
    _kom_springen(w, True)


@befehl("kommentar_zurueck")
def _kom_zurueck(w, _=None):
    _kom_springen(w, False)


@befehl("kommentar_liste")
def _kom_liste(w, _=None):
    d = _d(w)
    if not d:
        return
    orte = _kom_orte(d)
    if not orte:
        return w.meldung("Kommentare", "Das Dokument hat keine Kommentare.")
    zeilen = []
    for o, kid in orte:
        k = _kommentare(d).get(kid, {})
        zeilen.append("%s, %s:\n%s" % (k.get("autor", ""), k.get("zeit", ""), k.get("text", "")))
    w.meldung("Kommentare (%d)" % len(orte), "\n\n".join(zeilen))


@befehl("kommentar_weg")
def _kom_weg(w, _=None):
    d = _d(w)
    if not d:
        return
    it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
    for t in list(it.get_tags()):
        n = t.props.name or ""
        if n.startswith("kom:"):
            d.puffer.remove_tag_by_name(n, d.puffer.get_start_iter(), d.puffer.get_end_iter())
            _kommentare(d).pop(n[4:], None)
            d.puffer.set_modified(True)
            return w.status("Kommentar gelöscht.")
    w.status("Cursor steht nicht in einem kommentierten Text.")


@befehl("kommentare_alle_weg")
def _kom_alle_weg(w, _=None):
    d = _d(w)
    if not d:
        return
    for kid in _kom_tags(d):
        d.puffer.remove_tag_by_name("kom:" + kid, d.puffer.get_start_iter(), d.puffer.get_end_iter())
    _kommentare(d).clear()
    d.puffer.set_modified(True)
    w.status("Alle Kommentare gelöscht.")


# ================================================================ Änderungen verfolgen
@befehl("verfolgen")
def _verfolgen(w, _=None):
    d = _d(w)
    if not d:
        return
    an = not w.werte["an"].get("verfolgen", False)
    w.werte["an"]["verfolgen"] = an
    for x in w.alle_dokumente():
        x.verfolgen_an = an
    w.band_auffrischen()
    w.status("Änderungen werden %s." % ("verfolgt" if an else "nicht mehr verfolgt"))


@befehl("markup_umschalten")
def _markup(w, _=None):
    d = _d(w)
    if not d:
        return
    an = not w.werte["an"].get("markup_aus", False)
    w.werte["an"]["markup_aus"] = an
    for n, farbe in (("ins", None), ("del", None)):
        t = html_io.tag_holen(d.puffer, n)
        t.set_property("invisible", an and n == "del")
        if an and n == "ins":
            t.set_property("underline", html_io.Pango.Underline.NONE)
        elif n == "ins":
            t.set_property("underline", html_io.Pango.Underline.SINGLE)
    w.status("Markup %s." % ("ausgeblendet" if an else "sichtbar"))
    w.band_auffrischen()


def _aenderung_hier(d):
    it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
    for a, b, art in d.aenderungen():
        if a <= it.get_offset() <= b:
            return a, b, art
    return None


def _aenderung(w, annehmen):
    d = _d(w)
    if not d:
        return
    x = _aenderung_hier(d)
    if not x:
        return w.status("Cursor steht nicht in einer Änderung.")
    d.aenderung_bearbeiten(x[0], x[1], x[2], annehmen)
    w.status("Änderung %s." % ("angenommen" if annehmen else "abgelehnt"))


@befehl("aenderung_annehmen")
def _annehmen(w, _=None):
    _aenderung(w, True)


@befehl("aenderung_ablehnen")
def _ablehnen(w, _=None):
    _aenderung(w, False)


def _aenderung_springen(w, vor):
    d = _d(w)
    if not d:
        return
    liste = d.aenderungen()
    if not liste:
        return w.status("Keine Änderungen im Dokument.")
    pos = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_offset()
    kand = [x for x in liste if (x[0] > pos if vor else x[1] < pos)]
    a, b, _ = (kand[0] if vor else kand[-1]) if kand else (liste[0] if vor else liste[-1])
    d.puffer.select_range(d.puffer.get_iter_at_offset(a), d.puffer.get_iter_at_offset(b))
    d.ansicht.scroll_to_mark(d.puffer.get_insert(), 0.2, False, 0, 0)


@befehl("aenderung_weiter")
def _a_weiter(w, _=None):
    _aenderung_springen(w, True)


@befehl("aenderung_zurueck")
def _a_zurueck(w, _=None):
    _aenderung_springen(w, False)


def _alle(w, annehmen):
    d = _d(w)
    if not d:
        return
    n = 0
    while True:
        liste = d.aenderungen()
        if not liste:
            break
        a, b, art = liste[-1]
        d.aenderung_bearbeiten(a, b, art, annehmen)
        n += 1
        if n > 5000:
            break
    w.status("%d Änderungen %s." % (n, "angenommen" if annehmen else "verworfen"))


@befehl("aenderungen_uebernehmen")
def _alle_an(w, _=None):
    _alle(w, True)


@befehl("aenderungen_verwerfen")
def _alle_ab(w, _=None):
    _alle(w, False)


@befehl("ueberarbeitungsbereich")
def _bereich(w, _=None):
    d = _d(w)
    if not d:
        return
    liste = d.aenderungen()
    if not liste:
        return w.meldung("Überarbeitungsbereich", "Das Dokument hat keine verfolgten Änderungen.")
    z = []
    for a, b, art in liste:
        text = d.puffer.get_text(d.puffer.get_iter_at_offset(a), d.puffer.get_iter_at_offset(b), False)
        z.append("%s: „%s“" % ("Eingefügt" if art == "ins" else "Gelöscht", text[:80]))
    w.meldung("Überarbeitungsbereich (%d)" % len(liste), "\n".join(z))


# ================================================================ Schützen
@befehl("bearbeitung_sperren")
def _sperren(w, _=None):
    d = _d(w)
    if not d:
        return
    gesperrt = d.ansicht.get_editable()
    d.ansicht.set_editable(not gesperrt)
    d.ansicht.set_cursor_visible(not gesperrt)
    d.kopf.set_editable(not gesperrt)
    d.fuss.set_editable(not gesperrt)
    for a, _o in d.alle_objekte():
        wd = getattr(a, "widget", None)
        if wd is not None:
            wd.set_sensitive(not gesperrt)
    w.band_auffrischen()
    w.status("Bearbeitung gesperrt." if gesperrt else "Bearbeitung freigegeben.")
