"""Reiter Referenzen: Inhaltsverzeichnis, Fußnoten, Zitate, Beschriftungen, Index."""
import re

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from . import befehl, hilfen
from .. import html_io


def _d(w):
    return w.dok()


# ================================================================ Inhaltsverzeichnis
def _toc_zeilen(d):
    z = []
    for ebene, text, nr in d.ueberschriften():
        z.append(("%s ........ %d" % (text, d.seite_der_zeile(nr)), (ebene - 1) * 24))
    return z


@befehl("inhaltsverzeichnis")
def _inhalt(w, _=None):
    d = _d(w)
    if not d:
        return
    z = _toc_zeilen(d)
    if not z:
        return w.meldung("Inhaltsverzeichnis", "Es gibt noch keine Überschriften. Formatieren Sie Titel mit „Überschrift 1–3“ (Start ▸ Stile).")
    d.verzeichnis_schreiben("toc", "Inhaltsverzeichnis", z)
    w.status("Inhaltsverzeichnis eingefügt (%d Einträge)." % len(z))


@befehl("verzeichnisse_aktualisieren")
def _aktualisieren(w, _=None):
    d = _d(w)
    if not d:
        return
    n = 0
    if d.hat_verzeichnis("toc"):
        d.verzeichnis_schreiben("toc", "Inhaltsverzeichnis", _toc_zeilen(d))
        n += 1
    if d.hat_verzeichnis("abb"):
        _abb_schreiben(d)
        n += 1
    if d.hat_verzeichnis("lit"):
        _lit_schreiben(w, d)
        n += 1
    if d.hat_verzeichnis("idx"):
        _idx_schreiben(d)
        n += 1
    w.status("%d Verzeichnis(se) aktualisiert." % n if n else "Keine Verzeichnisse im Dokument.")


# ================================================================ Fußnoten / Endnoten
def _note_einfuegen(w, art):
    d = _d(w)
    if not d:
        return
    titel = "Fußnoten" if art == "fn" else "Endnoten"

    def ok(v):
        text = v[0].strip()
        if not text:
            return
        # laufende Nummer = Anzahl der Verweise dieser Art + 1
        nr = len(_verweise(d, art)) + 1
        d.puffer.begin_user_action()
        o = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_offset()
        d.puffer.insert_at_cursor(str(nr))
        for t in ("hoch", "%s:%d" % (art, nr)):
            d.puffer.apply_tag(html_io.tag_holen(d.puffer, t), d.puffer.get_iter_at_offset(o), d.puffer.get_iter_at_offset(o + len(str(nr))))
        # Notenbereich am Ende
        ende = d.puffer.get_end_iter()
        marke = html_io.tag_holen(d.puffer, "noten:" + art)
        if not ende.starts_tag(marke) and not _hat_bereich(d, art):
            d.puffer.insert(d.puffer.get_end_iter(), "\n" + "─" * 20 + "\n" + titel + "\n")
        d.puffer.insert(d.puffer.get_end_iter(), "%d  %s\n" % (nr, text))
        n_ende = d.puffer.get_end_iter().get_offset()
        zeile_start = n_ende - len("%d  %s\n" % (nr, text))
        d.puffer.apply_tag(marke, d.puffer.get_iter_at_offset(zeile_start), d.puffer.get_end_iter())
        d.puffer.end_user_action()
    hilfen.frage(w, "Fußnote" if art == "fn" else "Endnote", [("Text der Note", "")], ok)


def _hat_bereich(d, art):
    tag = d.puffer.get_tag_table().lookup("noten:" + art)
    if tag is None:
        return False
    it = d.puffer.get_start_iter()
    return it.starts_tag(tag) or it.forward_to_tag_toggle(tag)


def _verweise(d, art):
    """[(Offset)] aller Verweismarken der Art 'fn' oder 'en' in Textreihenfolge."""
    erg = []
    namen = [t for t in html_io.zeichen_namen(d.puffer) if t.startswith(art + ":")]
    for n in sorted(namen, key=lambda s: int(s.split(":")[1])):
        tag = d.puffer.get_tag_table().lookup(n)
        it = d.puffer.get_start_iter()
        if it.starts_tag(tag) or it.forward_to_tag_toggle(tag):
            erg.append(it.get_offset())
    return erg


@befehl("fussnote")
def _fussnote(w, _=None):
    _note_einfuegen(w, "fn")


@befehl("endnote")
def _endnote(w, _=None):
    _note_einfuegen(w, "en")


def _note_springen(w, vor):
    d = _d(w)
    if not d:
        return
    pos = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_offset()
    alle = sorted(_verweise(d, "fn") + _verweise(d, "en"))
    if not alle:
        return w.status("Keine Noten im Dokument.")
    kand = [o for o in alle if (o > pos if vor else o < pos)]
    ziel = (kand[0] if vor else kand[-1]) if kand else (alle[0] if vor else alle[-1])
    it = d.puffer.get_iter_at_offset(ziel)
    d.puffer.place_cursor(it)
    d.ansicht.scroll_to_iter(it, 0.1, True, 0, 0.3)


@befehl("note_weiter")
def _note_weiter(w, _=None):
    _note_springen(w, True)


@befehl("note_zurueck")
def _note_zurueck(w, _=None):
    _note_springen(w, False)


@befehl("noten_zeigen")
def _noten_zeigen(w, _=None):
    d = _d(w)
    if not d:
        return
    for art in ("fn", "en"):
        tag = d.puffer.get_tag_table().lookup("noten:" + art)
        if tag is not None:
            it = d.puffer.get_start_iter()
            if it.starts_tag(tag) or it.forward_to_tag_toggle(tag):
                d.puffer.place_cursor(it)
                d.ansicht.scroll_to_iter(it, 0.1, True, 0, 0.1)
                return
    w.status("Das Dokument hat keine Noten.")


# ================================================================ Quellen und Zitate
STILE = ["Autor Jahr", "Autor, Jahr, S.", "Nummer [1]", "Titel (Kurz)"]


def _quellen(d):
    return d.meta.setdefault("quellen", [])


def _zitat_text(d, q, stil):
    qs = _quellen(d)
    if stil == "Autor Jahr":
        return "(%s %s)" % (q["autor"], q.get("jahr", ""))
    if stil == "Autor, Jahr, S.":
        return "(%s, %s)" % (q["autor"], q.get("jahr", ""))
    if stil == "Nummer [1]":
        return "[%d]" % (qs.index(q) + 1)
    return "(%s)" % q.get("titel", "")[:30]


@befehl("quelle_neu")
def _quelle_neu(w, _=None):
    d = _d(w)
    if not d:
        return

    def ok(v):
        if not v[0].strip():
            return
        _quellen(d).append({"autor": v[0].strip(), "titel": v[1].strip(), "jahr": v[2].strip(),
                            "verlag": v[3].strip(), "ort": v[4].strip()})
        d.puffer.set_modified(True)
        w.status("Quelle gespeichert.")
    hilfen.frage(w, "Neue Quelle", [("Autor (Nachname, V.)", ""), ("Titel", ""), ("Jahr", ""), ("Verlag", ""), ("Ort", "")], ok)


@befehl("quellen_verwalten")
def _quellen_verwalten(w, _=None):
    d = _d(w)
    if not d:
        return
    qs = _quellen(d)
    dlg = Gtk.Window(transient_for=w, modal=True, title="Quellen verwalten")
    dlg.set_default_size(520, 380)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(12)
    dlg.set_child(box)
    liste = Gtk.ListBox()
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(liste)
    box.append(rolle)

    def fuellen():
        k = liste.get_first_child()
        while k:
            n = k.get_next_sibling()
            liste.remove(k)
            k = n
        for q in qs:
            liste.append(Gtk.Label(label="%s (%s): %s" % (q["autor"], q.get("jahr", ""), q.get("titel", "")), xalign=0))
    fuellen()
    zeile = Gtk.Box(spacing=6)
    weg = Gtk.Button(label="Ausgewählte löschen")

    def loeschen(*_):
        r = liste.get_selected_row()
        if r:
            qs.pop(r.get_index())
            d.puffer.set_modified(True)
            fuellen()
    weg.connect("clicked", loeschen)
    neu = Gtk.Button(label="Neue Quelle …")
    neu.connect("clicked", lambda *_: (dlg.close(), _quelle_neu(w)))
    zeile.append(neu)
    zeile.append(weg)
    box.append(zeile)
    dlg.present()


@befehl("zitierweise")
def _zitierweise(w, _=None):
    d = _d(w)
    if not d:
        return
    dlg = Gtk.AlertDialog()
    dlg.set_message("Zitierweise")
    dlg.set_detail("Aktuell: %s" % d.meta.get("zitierweise", STILE[0]))
    dlg.set_buttons(STILE + ["Abbrechen"])
    dlg.set_cancel_button(len(STILE))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(STILE):
            d.meta["zitierweise"] = STILE[n]
            d.puffer.set_modified(True)
            w.status("Zitierweise: " + STILE[n])
    dlg.choose(w, None, fertig)


@befehl("zitat")
def _zitat(w, _=None):
    d = _d(w)
    if not d:
        return
    qs = _quellen(d)
    if not qs:
        return _quelle_neu(w)
    dlg = Gtk.AlertDialog()
    dlg.set_message("Zitat einfügen")
    shown = qs[:7]
    dlg.set_buttons(["%s (%s)" % (q["autor"], q.get("jahr", "")) for q in shown] + ["Abbrechen"])
    dlg.set_cancel_button(len(shown))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(shown):
            d.text_einfuegen(_zitat_text(d, shown[n], d.meta.get("zitierweise", STILE[0])))
    dlg.choose(w, None, fertig)


def _lit_schreiben(w, d):
    z = []
    for i, q in enumerate(sorted(_quellen(d), key=lambda q: q["autor"].lower()), 1):
        z.append(("%s (%s): %s. %s%s." % (q["autor"], q.get("jahr", "o. J."), q.get("titel", ""),
                                          (q.get("ort", "") + ": ") if q.get("ort") else "", q.get("verlag", "")), 0))
    d.verzeichnis_schreiben("lit", "Literaturverzeichnis", z)


@befehl("literaturverzeichnis")
def _literatur(w, _=None):
    d = _d(w)
    if not d:
        return
    if not _quellen(d):
        return w.meldung("Literaturverzeichnis", "Es sind noch keine Quellen angelegt (Referenzen ▸ Neue Quelle).")
    _lit_schreiben(w, d)


# ================================================================ Beschriftungen
ARTEN = ["Abbildung", "Tabelle", "Formel", "Diagramm"]


def _beschriftungen(d):
    erg = []
    for nr in range(d.puffer.get_line_count()):
        _, von = d.puffer.get_iter_at_line(nr)
        if any((t.props.name or "") == "st:Beschriftung" for t in von.get_tags()):
            ende = von.copy()
            if not ende.ends_line():
                ende.forward_to_line_end()
            erg.append((d.puffer.get_text(von, ende, False), nr))
    return erg


@befehl("beschriftung")
def _beschriftung(w, _=None):
    d = _d(w)
    if not d:
        return

    def ok(v):
        art = v[0] if v[0] in ARTEN else "Abbildung"
        n = sum(1 for t, _ in _beschriftungen(d) if t.startswith(art)) + 1
        text = "%s %d: %s" % (art, n, v[1])
        it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
        a = d.objekt_am_cursor()
        d.puffer.begin_user_action()
        if not it.ends_line():
            it.forward_to_line_end()
            d.puffer.place_cursor(it)
        d.puffer.insert_at_cursor("\n" + text)
        d.puffer.end_user_action()
        d.stil_setzen("Beschriftung")
    hilfen.frage(w, "Beschriftung", [("Art (%s)" % ", ".join(ARTEN), "Abbildung"), ("Text", "")], ok)


def _abb_schreiben(d):
    z = [("%s ........ %d" % (t, d.seite_der_zeile(nr)), 0) for t, nr in _beschriftungen(d)]
    d.verzeichnis_schreiben("abb", "Abbildungsverzeichnis", z)


@befehl("abbildungsverzeichnis")
def _abbildungsverzeichnis(w, _=None):
    d = _d(w)
    if not d:
        return
    if not _beschriftungen(d):
        return w.meldung("Abbildungsverzeichnis", "Es gibt noch keine Beschriftungen (Referenzen ▸ Beschriftung).")
    _abb_schreiben(d)


# ================================================================ Index
@befehl("index_eintrag")
def _index_eintrag(w, _=None):
    d = _d(w)
    if not d:
        return
    sel = d.puffer.get_selection_bounds() or d._ziel()
    if not sel:
        return w.status("Wort auswählen oder Cursor in ein Wort setzen.")
    wort = d.puffer.get_text(*sel, False).strip()

    def ok(v):
        name = re.sub(r"[:\s]+", "_", v[0].strip())
        if name:
            d.puffer.apply_tag(html_io.tag_holen(d.puffer, "idx:" + name), *sel)
            d.puffer.set_modified(True)
            w.status("Indexeintrag „%s“ gesetzt." % v[0])
    hilfen.frage(w, "Indexeintrag", [("Eintrag", wort)], ok)


def _idx_schreiben(d):
    namen = sorted([t[4:] for t in html_io.zeichen_namen(d.puffer) if t.startswith("idx:")], key=str.casefold)
    z = []
    for n in namen:
        tag = d.puffer.get_tag_table().lookup("idx:" + n)
        seiten, it = set(), d.puffer.get_start_iter()
        while True:
            if it.starts_tag(tag) or it.forward_to_tag_toggle(tag):
                if it.starts_tag(tag):
                    seiten.add(d.seite_der_zeile(it.get_line()))
                if not it.forward_char():
                    break
            else:
                break
        z.append(("%s ........ %s" % (n.replace("_", " "), ", ".join(str(s) for s in sorted(seiten))), 0))
    d.verzeichnis_schreiben("idx", "Stichwortverzeichnis", z)


@befehl("stichwortverzeichnis")
def _stichwortverzeichnis(w, _=None):
    d = _d(w)
    if not d:
        return
    if not any(t.startswith("idx:") for t in html_io.zeichen_namen(d.puffer)):
        return w.meldung("Stichwortverzeichnis", "Es gibt noch keine Indexeinträge (Referenzen ▸ Indexeintrag).")
    _idx_schreiben(d)
