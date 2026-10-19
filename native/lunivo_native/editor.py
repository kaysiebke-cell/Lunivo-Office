"""Ein Dokument: Papierfläche mit Text, Formatierung, Suchen, Dateien."""
import os
import re

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, GObject, Gdk  # noqa: E402

from . import html_io, konvertieren, krypto, objekte, schreibhilfe, sprachdienste


# Marken, die nicht „weitergetippt“ werden: Umbruch, Verzeichnisse, Noten, Verweise, Kommentare, Änderungen.
_NICHT_VERERBT = ("umbruch", "ins", "del", "falsch", "dimm", "steuer", "zoom", "grund")
_NICHT_VERERBT_VORSATZ = ("verz:", "noten:", "link:", "marke:", "kom:", "idx:", "fn:", "en:", "feld:", "regel:")


def erbt(name):
    """Soll ein Tag auf neu getippten Text übergehen? (Fett, Größe, Farbe … ja; Umbruch, Verzeichnis, Link … nein)"""
    return bool(name) and name not in _NICHT_VERERBT and not name.startswith(_NICHT_VERERBT_VORSATZ)


class Dokument(Gtk.ScrolledWindow):
    __gsignals__ = {
        "geaendert": (GObject.SignalFlags.RUN_LAST, None, ()),
        "format-stand": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, vorgabe_schrift="Georgia", vorgabe_groesse=12):
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.add_css_class("arbeitsflaeche")
        self.pfad = None
        self.titel = "Unbenannt"
        self.zoom = 100
        self.vorgabe_schrift = vorgabe_schrift
        self.vorgabe_groesse = vorgabe_groesse
        self.tippen = set()          # Zeichenformat für den nächsten getippten Text
        self._sperre = False
        self._leere_zeile = None     # (Zeilennummer, Absatztags) für noch leere Zeile

        self.puffer = Gtk.TextBuffer()
        self.puffer.set_enable_undo(True)
        self.ansicht = Gtk.TextView.new_with_buffer(self.puffer)
        self.ansicht.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.ansicht.set_left_margin(56)
        self.ansicht.set_right_margin(56)
        self.ansicht.set_top_margin(48)
        self.ansicht.set_bottom_margin(64)
        self.ansicht.set_pixels_below_lines(4)
        self.ansicht.set_accepts_tab(True)
        self.ansicht.add_css_class("blatt")
        self.ansicht.set_hexpand(True)
        self.ansicht.set_vexpand(True)
        # Das Blatt: Kopfzeile, Text, Fußzeile auf weißem Papier in der Mitte, grauer Rand
        self.meta = {}
        self.kopf = self._randfeld("blatt-kopf")
        self.fuss = self._randfeld("blatt-fuss")
        self.blatt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.blatt.add_css_class("blattrahmen")
        self.ueberlagerung = Gtk.Overlay()
        self.ueberlagerung.set_child(self.ansicht)
        self.wz = Gtk.DrawingArea()
        self.wz.set_can_target(False)
        self.wz.set_draw_func(self._wasserzeichen_zeichnen)
        self.wz.set_visible(False)
        self.ueberlagerung.add_overlay(self.wz)
        self.deko = Gtk.DrawingArea()                 # Gitternetz und Textbegrenzungen
        self.deko.set_can_target(False)
        self.deko.set_draw_func(self._deko_zeichnen)
        self.deko_netz = False
        self.deko_ecken = False
        self.ueberlagerung.add_overlay(self.deko)
        self.puffer.connect("changed", lambda *_: self.deko.queue_draw())
        self.puffer.connect("notify::cursor-position", lambda *_: self.deko.queue_draw())
        self.lineal = Gtk.DrawingArea()
        self.lineal.set_content_height(26)
        self.lineal.set_draw_func(self._lineal_zeichnen)
        self._marke_gezogen = None
        zieh = Gtk.GestureDrag()
        zieh.connect("drag-begin", self._lineal_zieh_anfang)
        zieh.connect("drag-update", self._lineal_zieh)
        zieh.connect("drag-end", lambda *a: setattr(self, "_marke_gezogen", None))
        self.lineal.add_controller(zieh)
        self.lineal.set_visible(False)
        self.blatt.append(self.lineal)
        self.blatt.append(self.kopf)
        self.blatt.append(self.ueberlagerung)
        self.blatt.append(self.fuss)
        self.mitte = Gtk.Box()
        self.mitte.set_halign(Gtk.Align.CENTER)
        self.mitte.set_margin_top(18)
        self.mitte.set_margin_bottom(18)
        self.mitte.append(self.blatt)
        self.set_child(self.mitte)
        self.seite = {"papier": "a4", "quer": False, "seitenfarbe": "#FFFFFF", "rahmen": None,
                      "design": None,
                      "rand": {"oben": 25, "unten": 25, "links": 32, "rechts": 32},
                      "spalten": 1, "zeilennummern": False, "wasserzeichen": None}
        self._seitenfarbe_css = Gtk.CssProvider()
        self.blatt.get_style_context().add_provider(self._seitenfarbe_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

        self._im_einfuegen = False
        self.verfolgen_an = False
        self._intern = False
        self._rs_an = False
        self._rs_sprache = "de_DE"
        self._rs_eigene = set()
        self._rs_timer = 0
        self.autokorrektur_an = False
        self.autokorr_regeln = {"anfuehrung": True, "striche": True, "punkte": True, "satzanfang": False,
                                "wochentage": False, "feststell": False}
        self.strg_klick = True
        self.vorhersage_an = False
        self._vorschlag_pop = None
        self._vorschlaege = []
        taste = Gtk.EventControllerKey()
        taste.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        taste.connect("key-pressed", self._taste)
        self.ansicht.add_controller(taste)
        self.tabelle_aktiv = None            # (Anker, Zeile, Spalte), solange der Cursor in einer Tabellenzelle steht
        for tv in (self.ansicht,):
            fc = Gtk.EventControllerFocus()
            fc.connect("enter", lambda *_: self._fokus_text())
            tv.add_controller(fc)
        for tv, was in ((self.kopf, "kopf"), (self.fuss, "fuss")):
            fc = Gtk.EventControllerFocus()
            fc.connect("enter", lambda *_a, was=was: self._fokus_rand(was))
            tv.add_controller(fc)
        self.rand_aktiv = None
        self.puffer.connect("delete-range", self._vor_loeschen)
        rechts = Gtk.GestureClick()
        rechts.set_button(3)
        rechts.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        rechts.connect("pressed", self._rechtsklick)
        self.ansicht.add_controller(rechts)
        klick = Gtk.GestureClick()
        klick.set_button(1)
        klick.connect("released", self._link_geklickt)
        self.ansicht.add_controller(klick)
        self.puffer.connect("insert-text", lambda *a: setattr(self, "_im_einfuegen", True))
        self.puffer.connect_after("insert-text", self._nach_einfuegen)
        self._melde_id = 0
        self.puffer.connect("changed", self._geaendert_spaeter)
        self.puffer.connect("notify::cursor-position", self._cursor_bewegt)
        self.puffer.connect("mark-set", self._marke_gesetzt)
        self.zoom_setzen(100)

    # ------------------------------------------------------------ Grundlagen
    def _randfeld(self, klasse):
        tv = Gtk.TextView()
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.add_css_class(klasse)
        tv.set_visible(False)
        tv.set_hexpand(True)
        tv.get_buffer().connect("changed", lambda *_: (self.puffer.set_modified(True), self.emit("geaendert")))
        return tv

    def _geaendert_spaeter(self, *_):
        """„geändert“ wird erst gemeldet, wenn GTK mit dem Umbau des Puffers fertig ist (nicht mitten im Löschen eines Ankers)."""
        if not self._melde_id:
            self._melde_id = GLib.idle_add(self._melde)

    def _melde(self):
        self._melde_id = 0
        self.emit("geaendert")
        return False

    @property
    def geaendert(self):
        return self.puffer.get_modified()

    def anzeigename(self):
        return os.path.basename(self.pfad) if self.pfad else self.titel

    def text(self):
        """Der ganze Text; ein Objekt (Tabelle, Bild …) zählt als ein Zeichen (U+FFFC)."""
        return self.puffer.get_slice(self.puffer.get_start_iter(), self.puffer.get_end_iter(), True)

    def woerter(self):
        return len(self.text().split())

    # ------------------------------------------------------------ Laden/Speichern
    def laden(self, pfad, kennwort=None):
        endung = os.path.splitext(pfad)[1].lower()
        if endung in (".html", ".htm", ".xhtml"):
            with open(pfad, encoding="utf-8", errors="replace") as f:
                inhalt = f.read()
            if krypto.ist_verschluesselt(inhalt):
                if not kennwort:
                    raise krypto.KennwortNoetig()
                inhalt = krypto.entschluesseln(inhalt, kennwort)
                self.kennwort = kennwort
            html_io.html_in_puffer(self.puffer, inhalt)
        elif endung in (".txt", ".md", ""):
            with open(pfad, encoding="utf-8", errors="replace") as f:
                self.puffer.begin_irreversible_action()
                self.puffer.set_text(f.read())
                self.puffer.end_irreversible_action()
        elif endung in (".docx", ".doc", ".odt", ".rtf", ".fodt", ".ott", ".dotx"):
            html_io.html_in_puffer(self.puffer, konvertieren.html_aus_datei(pfad))
        else:
            raise RuntimeError("Dieses Format kann ich nicht öffnen: %s" % endung)
        self.pfad = pfad
        self.titel = os.path.basename(pfad)
        self.objekte_anbinden()
        self.meta_laden()
        self.puffer.set_modified(False)
        self.zoom_setzen(self.zoom)
        self.puffer.place_cursor(self.puffer.get_start_iter())

    def speichern_unter(self, pfad):
        endung = os.path.splitext(pfad)[1].lower()
        if endung in (".html", ".htm"):
            inhalt = html_io.puffer_in_html(self.puffer, self.anzeigename(), self.meta_aktuell())
            if getattr(self, "kennwort", None):
                inhalt = krypto.verschluesseln(inhalt, self.kennwort)
            self._schreiben(pfad, inhalt)
        elif endung in (".txt", ".md"):
            self._schreiben(pfad, self.text())
        elif endung in (".docx", ".odt", ".pdf", ".rtf", ".png"):
            konvertieren.html_in_datei(html_io.puffer_in_html(self.puffer, self.anzeigename(), self.meta_aktuell()),
                                       pfad, endung[1:])
        else:
            raise RuntimeError("Dieses Format kann ich nicht speichern: %s" % endung)
        return pfad

    def speichern(self, pfad=None, sicherungskopie=False):
        pfad = pfad or self.pfad
        if sicherungskopie and os.path.exists(pfad):
            import shutil
            try:
                shutil.copy2(pfad, pfad + "~")
            except OSError:
                pass
        self.speichern_unter(pfad)
        # nur Formate, in denen alles erhalten bleibt, gelten als „gespeichert"
        if os.path.splitext(pfad)[1].lower() in (".html", ".htm", ".docx", ".odt", ".rtf"):
            self.pfad = pfad
            self.titel = os.path.basename(pfad)
            self.puffer.set_modified(False)

    @staticmethod
    def _schreiben(pfad, inhalt):
        tmp = pfad + ".neu"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(inhalt)
        os.replace(tmp, pfad)

    # ------------------------------------------------------------ Zoom
    def zoom_setzen(self, prozent):
        self.zoom = max(40, min(300, int(prozent)))
        tag = html_io.tag_holen(self.puffer, "zoom")
        tag.set_property("scale", self.zoom / 100.0)
        self.puffer.apply_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())
        self._grundschrift()
        self.seite_anwenden()

    def _grundschrift(self):
        tag = html_io.tag_holen(self.puffer, "grund")
        tag.set_property("family", self.vorgabe_schrift)
        tag.set_property("size-points", float(self.vorgabe_groesse))
        tag.set_priority(0)
        self.puffer.apply_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())

    # ------------------------------------------------------------ Tippen mit Format
    def _nach_einfuegen(self, puffer, ort, text, laenge):
        self._im_einfuegen = False
        if self._rs_an:
            self._rs_planen()
        if not self._sperre and not self._intern:
            if self.autokorrektur_an:
                GLib.idle_add(self._autokorr, text)
            if self.vorhersage_an:
                GLib.idle_add(self._vorhersage_zeigen)
        if self._sperre:
            return
        self._sperre = True
        try:
            ende = ort.copy()
            anfang = ort.copy()
            anfang.backward_chars(len(text))
            puffer.apply_tag(html_io.tag_holen(puffer, "zoom"), anfang, ende)
            puffer.apply_tag(html_io.tag_holen(puffer, "grund"), anfang, ende)
            # Zeichentags vom Vorgabewert (tippen) setzen, andere entfernen
            for tag in list(anfang.get_tags()) + list(ende.get_tags()):
                pass
            fest = [t for t in self._zeichen_tags_im_bereich(anfang, ende)]
            for t in fest:
                if t not in self.tippen:
                    puffer.remove_tag_by_name(t, anfang, ende)
            for t in self.tippen:
                puffer.apply_tag(html_io.tag_holen(puffer, t), anfang, ende)
            if self.verfolgen_an and not self._intern:
                puffer.apply_tag(html_io.tag_holen(puffer, "ins"), anfang, ende)
            # Absatzformat (Ausrichtung) mit der Zeile mitführen
            zeile = anfang.copy()
            zeile.set_line_offset(0)
            if text == "\n":
                # Enter: Ausrichtung der Zeile davor erbt die neue Zeile; die
                # Überschrift nicht (nach einer Überschrift kommt Fließtext).
                vorige = {t for t in html_io.ABSATZ_TAGS
                          if t.startswith("al-") and zeile.has_tag(puffer.get_tag_table().lookup(t) or html_io.tag_holen(puffer, t))}
                for t in vorige:
                    puffer.apply_tag(html_io.tag_holen(puffer, t), anfang, ende)
                self._leere_zeile = (ende.get_line(), vorige) if vorige else None
            else:
                if self._leere_zeile and self._leere_zeile[0] == anfang.get_line():
                    schluss = ende.copy()
                    if not schluss.ends_line():
                        schluss.forward_to_line_end()
                    for t in self._leere_zeile[1]:
                        puffer.apply_tag(html_io.tag_holen(puffer, t), zeile, schluss)
                    self._leere_zeile = None
                for t in html_io.ABSATZ_TAGS:
                    tg = puffer.get_tag_table().lookup(t)
                    if tg is not None and zeile.has_tag(tg):
                        puffer.apply_tag(tg, anfang, ende)
        finally:
            self._sperre = False

    @staticmethod
    def _zeichen_tags_im_bereich(a, b):
        namen = set()
        it = a.copy()
        while it.compare(b) < 0:
            for t in it.get_tags():
                n = t.props.name
                if n and n not in html_io.ABSATZ_TAGS and erbt(n):
                    namen.add(n)
            if not it.forward_char():
                break
        return namen

    def _cursor_bewegt(self, *_):
        self._format_vom_cursor()

    def _marke_gesetzt(self, puffer, ort, marke):
        if marke.get_name() == "insert":
            self._format_vom_cursor()

    def _format_vom_cursor(self):
        # Während des Einfügens wandert der Cursor schon, der Text hat aber
        # noch kein Format — dann würde das gewählte Format verworfen.
        if self._sperre or self._im_einfuegen:
            return
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        # Format des Zeichens davor (wie in Textverarbeitungen üblich)
        probe = it.copy()
        if not probe.is_start() and not probe.starts_line():
            probe.backward_char()
        elif probe.is_end() and not probe.is_start():
            probe.backward_char()
        neu = set()
        for t in probe.get_tags():
            n = t.props.name
            if n and n not in html_io.ABSATZ_TAGS and erbt(n):
                neu.add(n)
        self.tippen = neu
        self.emit("format-stand")

    # ------------------------------------------------------------ Format anwenden
    def _bereich(self):
        gm = self.puffer.get_selection_bounds()
        return gm if gm else None

    def hat_format(self, name):
        sel = self._bereich()
        if sel:
            tag = self.puffer.get_tag_table().lookup(name)
            if tag is None:
                return False
            it = sel[0].copy()
            while it.compare(sel[1]) < 0:
                if not it.has_tag(tag):
                    return False
                it.forward_char()
            return True
        return name in self.tippen

    def umschalten(self, name):
        sel = self._bereich()
        tag = html_io.tag_holen(self.puffer, name)
        if sel:
            if self.hat_format(name):
                self.puffer.remove_tag(tag, *sel)
            else:
                self.puffer.apply_tag(tag, *sel)
        else:
            self.tippen ^= {name}
        self.puffer.set_modified(True)
        self.emit("format-stand")

    def wert_setzen(self, vorsatz, name):
        """Schriftart/Größe/Farbe: genau eines je Art. name=None entfernt."""
        sel = self._bereich()
        if sel:
            for t in self._alle_tags_mit(vorsatz):
                self.puffer.remove_tag_by_name(t, *sel)
            if name:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, name), *sel)
            self.puffer.set_modified(True)
        else:
            self.tippen = {t for t in self.tippen if not t.startswith(vorsatz)}
            if name:
                self.tippen.add(name)
        self.emit("format-stand")

    def _alle_tags_mit(self, vorsatz):
        namen = []
        def f(tag, _):
            n = tag.props.name
            if n and n.startswith(vorsatz):
                namen.append(n)
        self.puffer.get_tag_table().foreach(f, None)
        return namen

    def _zeilen(self):
        sel = self._bereich()
        if sel:
            a, b = sel[0].get_line(), sel[1].get_line()
            if sel[1].starts_line() and b > a:
                b -= 1
        else:
            a = b = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_line()
        return a, b

    def absatz_setzen(self, gruppe, name):
        """gruppe: 'al' (Ausrichtung) oder 'h' (Überschrift). name=None = normal."""
        a, b = self._zeilen()
        for n in range(a, b + 1):
            _, von = self.puffer.get_iter_at_line(n)
            bis = von.copy()
            if not bis.ends_line():
                bis.forward_to_line_end()
            bis.forward_char()      # Zeilenumbruch einschließen
            namen = [t for t in html_io.ABSATZ_TAGS if (t.startswith("al-") if gruppe == "al" else t.startswith("h"))]
            for t in namen:
                self.puffer.remove_tag(html_io.tag_holen(self.puffer, t), von, bis)
            if name:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, name), von, bis)
            if gruppe == "al" and von.is_end():
                # letzte, noch leere Zeile: Format merken, bis Text kommt
                self._leere_zeile = (n, {name} if name else set())
        self.puffer.set_modified(True)
        self.emit("format-stand")

    def absatz_tag_am_cursor(self):
        _, von = self.puffer.get_iter_at_line(self._zeilen()[0])
        return {t.props.name for t in von.get_tags() if t.props.name in html_io.ABSATZ_TAGS}

    _MARKEN = ("• ", "– ", "○ ", "■ ", "➤ ", "✓ ")

    def aufzaehlung(self, nummeriert=False, art=None):
        """Aufzählung/Nummerierung auf die gewählten Zeilen (nochmal = wieder weg)."""
        import re
        a, b = self._zeilen()
        zeilen = [self.puffer.get_iter_at_line(n)[1] for n in range(a, b + 1)]
        alle = all(self._marke_laenge(z) for z in zeilen)
        self.puffer.begin_user_action()
        for n in range(b, a - 1, -1):
            _, z = self.puffer.get_iter_at_line(n)
            laenge = self._marke_laenge(z)
            if laenge:
                ende = z.copy()
                ende.forward_chars(laenge)
                self.puffer.delete(z, ende)
            if alle and laenge and art is None:
                continue
            if nummeriert:
                self.puffer.insert(z, self._nummer(n - a + 1, art or "1"))
            else:
                self.puffer.insert(z, art or "• ")
        self.puffer.end_user_action()
        self.emit("format-stand")

    @staticmethod
    def _nummer(i, art):
        if art == "a":
            return "%s) " % chr(96 + (i - 1) % 26 + 1)
        if art == "A":
            return "%s. " % chr(64 + (i - 1) % 26 + 1)
        if art == "I":
            zahlen = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
            r, n = "", i
            for v, s in zahlen:
                while n >= v:
                    r += s
                    n -= v
            return r + ". "
        return "%d. " % i

    def _marke_laenge(self, zeile):
        import re
        ende = zeile.copy()
        ende.forward_chars(6)
        s = self.puffer.get_text(zeile, ende, False)
        for m in self._MARKEN:
            if s.startswith(m):
                return len(m)
        m = re.match(r"(\d+\. |[a-z]\) |[A-Z]\. |[IVX]+\. )", s)
        return len(m.group(0)) if m else 0

    def hat_liste(self, nummeriert):
        _, z = self.puffer.get_iter_at_line(self._zeilen()[0])
        l = self._marke_laenge(z)
        if not l:
            return False
        ende = z.copy()
        ende.forward_chars(l)
        erstes = self.puffer.get_text(z, ende, False)
        return (erstes in self._MARKEN) != nummeriert

    # ------------------------------------------------------------ Suchen/Ersetzen
    def _such_treffer(self, start, muster, flags, vorwaerts, ganz):
        while True:
            t = start.forward_search(muster, flags, None) if vorwaerts else start.backward_search(muster, flags, None)
            if not t or not ganz:
                return t
            vor = t[0].copy()
            davor = vor.backward_char() and vor.get_char().isalnum()
            danach = t[1].get_char().isalnum() if not t[1].is_end() else False
            if not davor and not danach:
                return t
            start = t[1] if vorwaerts else t[0]

    def treffer_zaehlen(self, muster, gross=False, ganz=False):
        if not muster:
            return 0
        flags = Gtk.TextSearchFlags.TEXT_ONLY | (0 if gross else Gtk.TextSearchFlags.CASE_INSENSITIVE)
        n, it = 0, self.puffer.get_start_iter()
        while True:
            t = self._such_treffer(it, muster, flags, True, ganz)
            if not t:
                return n
            n += 1
            it = t[1]

    def suchen(self, muster, vorwaerts=True, gross=False, ganz=False):
        if not muster:
            return False
        flags = Gtk.TextSearchFlags.TEXT_ONLY
        if not gross:
            flags |= Gtk.TextSearchFlags.CASE_INSENSITIVE
        sel = self._bereich()
        if vorwaerts:
            start = sel[1] if sel else self.puffer.get_iter_at_mark(self.puffer.get_insert())
            treffer = self._such_treffer(start, muster, flags, True, ganz)
            if not treffer:
                treffer = self._such_treffer(self.puffer.get_start_iter(), muster, flags, True, ganz)
        else:
            start = sel[0] if sel else self.puffer.get_iter_at_mark(self.puffer.get_insert())
            treffer = self._such_treffer(start, muster, flags, False, ganz)
            if not treffer:
                treffer = self._such_treffer(self.puffer.get_end_iter(), muster, flags, False, ganz)
        if treffer:
            self.puffer.select_range(treffer[0], treffer[1])
            self.ansicht.scroll_to_mark(self.puffer.get_insert(), 0.15, False, 0, 0)
            return True
        return False

    def ersetzen(self, muster, neu, gross=False, ganz=False):
        sel = self._bereich()
        if sel:
            gewaehlt = self.puffer.get_text(*sel, False)
            if (gewaehlt == muster) if gross else (gewaehlt.lower() == muster.lower()):
                self.puffer.begin_user_action()
                self.puffer.delete(*sel)
                self.puffer.insert_at_cursor(neu)
                self.puffer.end_user_action()
        return self.suchen(muster, True, gross, ganz)

    def alle_ersetzen(self, muster, neu, gross=False, ganz=False):
        if not muster:
            return 0
        flags = Gtk.TextSearchFlags.TEXT_ONLY
        if not gross:
            flags |= Gtk.TextSearchFlags.CASE_INSENSITIVE
        anzahl = 0
        self.puffer.begin_user_action()
        it = self.puffer.get_start_iter()
        while True:
            t = self._such_treffer(it, muster, flags, True, ganz)
            if not t:
                break
            marke = self.puffer.create_mark(None, t[0], True)
            self.puffer.delete(t[0], t[1])
            it = self.puffer.get_iter_at_mark(marke)
            self.puffer.insert(it, neu)
            it = self.puffer.get_iter_at_mark(marke)
            it.forward_chars(len(neu))
            self.puffer.delete_mark(marke)
            anzahl += 1
        self.puffer.end_user_action()
        return anzahl

    # ------------------------------------------------------------ Bereiche
    def bereich_waehlen(self, von, bis):
        self.puffer.select_range(self.puffer.get_iter_at_offset(von),
                                 self.puffer.get_iter_at_offset(bis))
        self.ansicht.scroll_to_mark(self.puffer.get_insert(), 0.2, False, 0, 0)
        self.ansicht.grab_focus()

    def bereich_ersetzen(self, von, bis, neu):
        a = self.puffer.get_iter_at_offset(von)
        b = self.puffer.get_iter_at_offset(bis)
        self.puffer.begin_user_action()
        self.puffer.delete(a, b)
        self.puffer.insert(self.puffer.get_iter_at_offset(von), neu)
        self.puffer.end_user_action()

    def auswahl_oder_alles(self):
        sel = self._bereich()
        if sel:
            return self.puffer.get_text(*sel, False), sel
        return self.text(), None

    # ------------------------------------------------------------ mehr Format (Reiter Start)
    def _ziel(self):
        """Auswahl; ohne Auswahl das Wort am Cursor (oder None)."""
        sel = self._bereich()
        if sel:
            return sel
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        a = it.copy()
        if not a.starts_word():
            a.backward_word_start()
        b = it.copy()
        if not b.ends_word():
            b.forward_word_end()
        return (a, b) if a.compare(b) < 0 else None

    def format_loeschen(self):
        sel = self._bereich() or (self.puffer.get_start_iter(), self.puffer.get_end_iter())
        for n in html_io.zeichen_namen(self.puffer):
            self.puffer.remove_tag(html_io.tag_holen(self.puffer, n), *sel)
        if not self._bereich():
            self.tippen = set()
        self.puffer.set_modified(True)
        self.emit("format-stand")

    def schreibweise(self, modus):
        ziel = self._ziel()
        if not ziel:
            return
        a, b = ziel
        von = a.get_offset()
        text = self.puffer.get_text(a, b, False)
        if modus == "gross":
            neu = text.upper()
        elif modus == "klein":
            neu = text.lower()
        elif modus == "woerter":
            neu = text.title()
        elif modus == "satz":
            neu = text[:1].upper() + text[1:].lower()
        else:                                           # wechseln
            neu = text.swapcase()
        self.puffer.begin_user_action()
        tags = [(t, c) for t, c in self._tags_je_zeichen(von, von + len(text))]
        self.puffer.delete(a, b)
        self.puffer.insert(self.puffer.get_iter_at_offset(von), neu)
        for i, namen in enumerate(tags):
            for n in namen[0]:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, n),
                                      self.puffer.get_iter_at_offset(von + i),
                                      self.puffer.get_iter_at_offset(von + i + 1))
        self.puffer.end_user_action()
        self.puffer.select_range(self.puffer.get_iter_at_offset(von), self.puffer.get_iter_at_offset(von + len(neu)))

    def _tags_je_zeichen(self, von, bis):
        for i in range(von, bis):
            it = self.puffer.get_iter_at_offset(i)
            yield ({t.props.name for t in it.get_tags() if t.props.name not in ("zoom", "grund", "steuer", "falsch", "dimm")}, None)

    def groesse_aendern(self, schritt):
        """Schrift vergrößern/verkleinern: nächste Stufe der Größenliste."""
        stufen = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72]
        aktuell = self.groesse_am_cursor()
        if schritt > 0:
            neu = next((s for s in stufen if s > aktuell + 0.01), stufen[-1])
        else:
            neu = next((s for s in reversed(stufen) if s < aktuell - 0.01), stufen[0])
        self.wert_setzen("size:", "size:%g" % neu)

    def groesse_am_cursor(self):
        for t in self.tippen:
            if t.startswith("size:"):
                return float(t[5:])
        return float(self.vorgabe_groesse)

    def format_kopieren(self):
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        if not it.starts_line() or it.is_end():
            probe = it.copy()
            if not probe.starts_line():
                probe.backward_char()
        else:
            probe = it
        self.format_gemerkt = ({t.props.name for t in probe.get_tags()
                                if t.props.name not in ("zoom", "grund", "steuer", "falsch", "dimm")})
        return bool(self.format_gemerkt is not None)

    def format_uebertragen(self):
        gemerkt = getattr(self, "format_gemerkt", None)
        sel = self._bereich()
        if gemerkt is None or not sel:
            return False
        for n in html_io.zeichen_namen(self.puffer):
            self.puffer.remove_tag(html_io.tag_holen(self.puffer, n), *sel)
        for n in gemerkt:
            if n not in html_io.ABSATZ_TAGS:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, n), *sel)
        self.puffer.set_modified(True)
        return True

    def absatz_tag_toggle(self, name, ersetzt_vorsatz=None):
        """Ein Absatz-Tag auf die gewählten Zeilen legen (ersetzt gleichartige)."""
        a, b = self._zeilen()
        for n in range(a, b + 1):
            _, von = self.puffer.get_iter_at_line(n)
            bis = von.copy()
            if not bis.ends_line():
                bis.forward_to_line_end()
            bis.forward_char()
            if ersetzt_vorsatz:
                for t in html_io.absatz_namen(self.puffer):
                    if t.startswith(ersetzt_vorsatz):
                        self.puffer.remove_tag_by_name(t, von, bis)
            if name:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, name), von, bis)
            if von.is_end():
                self._leere_zeile = (n, {name} if name else set())
        self.puffer.set_modified(True)
        self.emit("format-stand")

    def einzug_aendern(self, schritt_px):
        a, b = self._zeilen()
        for n in range(a, b + 1):
            self._zeilen_einzug(n, schritt_px)
        self.puffer.set_modified(True)

    def _zeilen_einzug(self, n, schritt):
        _, von = self.puffer.get_iter_at_line(n)
        aktuell = 0
        for t in von.get_tags():
            if (t.props.name or "").startswith("ein:"):
                aktuell = float(t.props.name[4:])
        bis = von.copy()
        if not bis.ends_line():
            bis.forward_to_line_end()
        bis.forward_char()
        for t in html_io.absatz_namen(self.puffer):
            if t.startswith("ein:"):
                self.puffer.remove_tag_by_name(t, von, bis)
        neu = max(0, aktuell + schritt)
        if neu:
            self.puffer.apply_tag(html_io.tag_holen(self.puffer, "ein:%d" % neu), von, bis)

    def eigene_stile(self):
        return self.meta.setdefault("vorlagen", {})

    def vorlage_anlegen(self, name, beschreibung):
        """Legt eine eigene Formatvorlage an (gehört zum Dokument und wandert mit ihm)."""
        self.eigene_stile()[name] = beschreibung
        html_io.EIGENE_STILE[name] = beschreibung
        tag = self.puffer.get_tag_table().lookup("st:" + name)
        if tag is not None:
            self.puffer.get_tag_table().remove(tag)
        self.puffer.set_modified(True)

    def vorlage_loeschen(self, name):
        self.eigene_stile().pop(name, None)
        html_io.EIGENE_STILE.pop(name, None)
        tag = self.puffer.get_tag_table().lookup("st:" + name)
        if tag is not None:
            self.puffer.remove_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())
        self.puffer.set_modified(True)

    def stil_setzen(self, name):
        a, b = self._zeilen()
        for n in range(a, b + 1):
            _, von = self.puffer.get_iter_at_line(n)
            bis = von.copy()
            if not bis.ends_line():
                bis.forward_to_line_end()
            bis.forward_char()
            for t in html_io.absatz_namen(self.puffer):
                if t.startswith("st:") or t in ("h1", "h2", "h3"):
                    self.puffer.remove_tag_by_name(t, von, bis)
            if name == "Standard":
                name = "Fließtext"
            if name != "Fließtext":
                if name.startswith("Überschrift "):
                    self.puffer.apply_tag(html_io.tag_holen(self.puffer, "h" + name[-1]), von, bis)
                else:
                    self.puffer.apply_tag(html_io.tag_holen(self.puffer, "st:" + name), von, bis)
        self.puffer.set_modified(True)
        self.emit("format-stand")

    def stil_am_cursor(self):
        _, von = self.puffer.get_iter_at_line(self._zeilen()[0])
        for t in von.get_tags():
            n = t.props.name or ""
            if n in ("h1", "h2", "h3"):
                return "Überschrift " + n[1]
            if n.startswith("st:"):
                return n[3:]
        return "Fließtext"

    def zeilen_sortieren(self, absteigend=False, typ="text"):
        a, b = self._zeilen()
        if a == b:
            a, b = 0, self.puffer.get_line_count() - 1
        _, von = self.puffer.get_iter_at_line(a)
        _, ende = self.puffer.get_iter_at_line(b)
        if not ende.ends_line():
            ende.forward_to_line_end()
        zeilen = self.puffer.get_text(von, ende, False).split("\n")
        if typ == "zahl":
            import re as _re

            def schluessel(z):
                m = _re.search(r"-?\d+(?:[.,]\d+)?", z)
                return (0, float(m.group().replace(",", "."))) if m else (1, 0.0)
            zeilen.sort(key=schluessel, reverse=absteigend)
        else:
            zeilen.sort(key=str.casefold, reverse=absteigend)
        o = von.get_offset()
        self.puffer.begin_user_action()
        self.puffer.delete(von, ende)
        self.puffer.insert(self.puffer.get_iter_at_offset(o), "\n".join(zeilen))
        self.puffer.end_user_action()

    def steuerzeichen(self, an):
        tag = html_io.tag_holen(self.puffer, "steuer")
        if an:
            self.puffer.apply_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())
        else:
            self.puffer.remove_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())
        self.steuer_an = an

    def text_einfuegen(self, text, tags=()):
        """Fügt Text an der Cursorstelle ein (ersetzt die Auswahl)."""
        self.puffer.begin_user_action()
        if self._bereich():
            self.puffer.delete_selection(True, True)
        von = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_offset()
        self.puffer.insert_at_cursor(text)
        for n in tags:
            self.puffer.apply_tag(html_io.tag_holen(self.puffer, n),
                                  self.puffer.get_iter_at_offset(von),
                                  self.puffer.get_iter_at_offset(von + len(text)))
        self.puffer.end_user_action()
        self.ansicht.grab_focus()

    # ------------------------------------------------------------ Seiten (Schätzung)
    SEITE_MM = (210.0, 297.0)

    def seite_stand(self):
        """(aktuelle Seite, Seitenzahl): Höhe des Textes geteilt durch die Textfläche einer Seite."""
        f = self.PX_MM * self.zoom / 100.0
        b, h = self.papier_mm()
        r = self.seite["rand"]
        flaeche = max((h - r["oben"] - r["unten"]) * f, 50)
        gesamt_h = max(self.ansicht.get_height() - self.ansicht.get_top_margin() - self.ansicht.get_bottom_margin(), 1)
        gesamt = max(1, int(-(-gesamt_h // flaeche)))
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        y = max(self.ansicht.get_iter_location(it).y - self.ansicht.get_top_margin(), 0)
        aktuell = min(gesamt, int(y // flaeche) + 1)
        return aktuell, gesamt

    # ------------------------------------------------------------ Objekte (Tabellen, Bilder …)
    def objekte_anbinden(self):
        """Baut zu allen Child-Ankern des Puffers (aus dem Laden) die Widgets."""
        for anker in getattr(self.puffer, "objekte", []):
            self._widget_an(anker)
        self.puffer.objekte = []

    def _widget_an(self, anker):
        w = objekte.widget_bauen(anker.daten, lambda: self.puffer.set_modified(True),
                                 lambda r, c, a=anker: self._tabellen_fokus(a, r, c))
        anker.widget = w
        self.ansicht.add_child_at_anchor(w, anker)

    def objekt_einfuegen(self, daten, eigener_absatz=False):
        """Fügt ein Objekt an der Cursorstelle ein."""
        self.puffer.begin_user_action()
        if self._bereich():
            self.puffer.delete_selection(True, True)
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        if eigener_absatz and not it.starts_line():
            self.puffer.insert(it, "\n")
            it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        anker = self.puffer.create_child_anchor(it)
        anker.daten = daten
        self._widget_an(anker)
        if eigener_absatz:
            self.puffer.insert(self.puffer.get_iter_at_mark(self.puffer.get_insert()), "\n")
        self.puffer.end_user_action()
        self.puffer.set_modified(True)
        return anker

    def alle_objekte(self):
        """[(Anker, Offset)] in Textreihenfolge."""
        gefunden = []
        it = self.puffer.get_start_iter()
        while True:
            a = it.get_child_anchor()
            if a is not None and hasattr(a, "daten"):
                gefunden.append((a, it.get_offset()))
            if not it.forward_char():
                break
        return gefunden

    def objekt_am_cursor(self):
        """Das Objekt rechts vom Cursor / in der Auswahl / links vom Cursor."""
        sel = self._bereich()
        it = sel[0].copy() if sel else self.puffer.get_iter_at_mark(self.puffer.get_insert())
        a = it.get_child_anchor()
        if a is not None and hasattr(a, "daten"):
            return a
        it2 = it.copy()
        if it2.backward_char():
            a = it2.get_child_anchor()
            if a is not None and hasattr(a, "daten"):
                return a
        return None

    def objekt_naechstes(self, rueckwaerts=False):
        alle = self.alle_objekte()
        if not alle:
            return None
        pos = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_offset()
        kandidaten = [x for x in alle if (x[1] < pos if rueckwaerts else x[1] >= pos + (1 if self.objekt_am_cursor() else 0))]
        a, o = (kandidaten[-1] if rueckwaerts else kandidaten[0]) if kandidaten else (alle[-1] if rueckwaerts else alle[0])
        self.puffer.select_range(self.puffer.get_iter_at_offset(o), self.puffer.get_iter_at_offset(o + 1))
        self.ansicht.scroll_to_mark(self.puffer.get_insert(), 0.2, False, 0, 0)
        return a

    def objekt_neu_zeichnen(self, anker):
        """Nach Änderung der Daten das Widget ersetzen."""
        w = getattr(anker, "widget", None)
        if w is not None and w.get_parent() is self.ansicht:
            self.ansicht.remove(w)                  # über das TextView lösen, nicht mit unparent(): sonst bleibt der alte Eintrag am Anker
        self._widget_an(anker)
        self.puffer.set_modified(True)

    # ------------------------------------------------------------ Seite einrichten
    PAPIER = {"a4": (210, 297), "a3": (297, 420), "a5": (148, 210), "b5": (176, 250), "letter": (216, 279),
              "legal": (216, 356), "dinlang": (220, 110), "c5": (229, 162), "c6": (162, 114)}
    PX_MM = 3.7795

    def papier_mm(self):
        b, h = self.PAPIER.get(self.seite["papier"], self.PAPIER["a4"])
        return (h, b) if self.seite["quer"] else (b, h)

    def seite_anwenden(self):
        s = self.seite
        b, h = self.papier_mm()
        f = self.PX_MM * self.zoom / 100.0
        self.blatt.set_size_request(int(b * f), -1)
        self.mitte.set_size_request(int(b * f), -1)
        r = s["rand"]
        self.ansicht.set_left_margin(int(r["links"] * f))
        self.ansicht.set_right_margin(int(r["rechts"] * f))
        self.ansicht.set_top_margin(int(r["oben"] * f * (0.5 if self.kopf.get_visible() else 1)))
        self.ansicht.set_bottom_margin(int(r["unten"] * f * (0.5 if self.fuss.get_visible() else 1)))
        for tv in (self.kopf, self.fuss):
            tv.set_left_margin(int(r["links"] * f))
            tv.set_right_margin(int(r["rechts"] * f))
            tv.set_top_margin(int(r["oben"] * f * 0.5) if tv is self.kopf else 6)
            tv.set_bottom_margin(6 if tv is self.kopf else int(r["unten"] * f * 0.5))
        rahmen = ""
        if s.get("rahmen"):
            r_ = s["rahmen"]
            rahmen = "box.blattrahmen { border: %dpx %s %s; }" % (r_.get("breite", 2), r_.get("stil", "solid"), r_.get("farbe", "#000000"))
        self._seitenfarbe_css.load_from_string(
            "box.blattrahmen, box.blattrahmen textview, box.blattrahmen textview text { background: %s; } %s" % (s["seitenfarbe"], rahmen))
        self.wz.set_visible(bool(s.get("wasserzeichen")))
        self.wz.queue_draw()
        self.emit("format-stand")

    def seite_setzen(self, **kw):
        for k, v in kw.items():
            if k == "rand":
                self.seite["rand"].update(v)
            else:
                self.seite[k] = v
        self.seite_anwenden()
        self.puffer.set_modified(True)

    def kopf_fuss_zeigen(self, kopf=None, fuss=None):
        if kopf is not None:
            self.kopf.set_visible(kopf)
        if fuss is not None:
            self.fuss.set_visible(fuss)
        self.seite_anwenden()
        self.puffer.set_modified(True)

    def kopf_fuss_an(self):
        return self.kopf.get_visible() or self.fuss.get_visible()

    # ------------------------------------------------------------ Metadaten ins Dokument
    def meta_aktuell(self):
        m = dict(self.meta)
        fenster = self.ansicht.get_root()
        opt = getattr(fenster, "werte", {}).get("opt", {}) if fenster is not None else {}
        if opt.get("sicherheit|Beim Speichern persönliche Daten aus den Dateieigenschaften entfernen") and m.get("eigenschaften"):
            m["eigenschaften"] = {k: v for k, v in m["eigenschaften"].items() if k not in ("Autor", "Firma", "Manager")}
        for schl, tv in (("kopf", self.kopf), ("fuss", self.fuss)):
            b = tv.get_buffer()
            t = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
            if tv.get_visible() or t:
                m[schl] = t
            else:
                m.pop(schl, None)
        m["seite"] = {"mm": list(self.papier_mm()), "papier": self.seite["papier"], "quer": self.seite["quer"],
                      "rand": self.seite["rand"], "farbe": self.seite["seitenfarbe"],
                      "spalten": self.seite["spalten"], "zeilennummern": self.seite["zeilennummern"],
                      "wasserzeichen": self.seite["wasserzeichen"], "rahmen": self.seite.get("rahmen"),
                      "design": self.seite.get("design")}
        return m

    def meta_laden(self):
        m = getattr(self.puffer, "meta", {}) or {}
        self.meta = {k: v for k, v in m.items() if k not in ("kopf", "fuss", "seite")}
        for schl, tv in (("kopf", self.kopf), ("fuss", self.fuss)):
            if m.get(schl) is not None:
                tv.get_buffer().set_text(m[schl])
                tv.set_visible(True)
        html_io.EIGENE_STILE.clear()
        html_io.EIGENE_STILE.update(self.meta.get("vorlagen", {}))
        s = m.get("seite")
        if s:
            self.seite["papier"] = s.get("papier", "a4")
            self.seite["quer"] = bool(s.get("quer"))
            self.seite["rand"].update(s.get("rand", {}))
            self.seite["seitenfarbe"] = s.get("farbe", "#FFFFFF")
            self.seite["spalten"] = s.get("spalten", 1)
            self.seite["zeilennummern"] = bool(s.get("zeilennummern"))
            self.seite["wasserzeichen"] = s.get("wasserzeichen")
            self.seite["rahmen"] = s.get("rahmen")
            self.seite["design"] = s.get("design")
        self.seite_anwenden()
        self.zeilennummern(self.seite["zeilennummern"])

    # ------------------------------------------------------------ Marken, Verweise, Links
    def marken(self):
        namen = [t[6:] for t in html_io.zeichen_namen(self.puffer) if t.startswith("marke:")]
        return sorted(namen)

    @staticmethod
    def _ueb_name(text):
        import re
        return "h-" + re.sub(r"\W+", "_", text.strip())[:40]

    def ueberschriften(self):
        """[(Ebene, Text, Zeilennummer)]"""
        erg = []
        for nr in range(self.puffer.get_line_count()):
            _, von = self.puffer.get_iter_at_line(nr)
            tags = {t.props.name for t in von.get_tags()}
            ebene = next((int(t[1]) for t in tags if t in ("h1", "h2", "h3")), 0)
            if "st:Titel" in tags:
                ebene = 1
            if ebene:
                ende = von.copy()
                if not ende.ends_line():
                    ende.forward_to_line_end()
                text = self.puffer.get_text(von, ende, False).strip()
                if text:
                    erg.append((ebene, text, nr))
        return erg

    def querverweis_ziele(self):
        ziele = [(m, m) for m in self.marken()]
        ziele += [(t, self._ueb_name(t)) for _e, t, _n in self.ueberschriften()]
        return ziele

    def springe_zu(self, ziel):
        tag = self.puffer.get_tag_table().lookup("marke:" + ziel)
        if tag is not None:
            it = self.puffer.get_start_iter()
            if it.starts_tag(tag) or it.forward_to_tag_toggle(tag):
                self.puffer.place_cursor(it)
                self.ansicht.scroll_to_iter(it, 0.1, True, 0, 0.1)
                return True
        for _e, t, nr in self.ueberschriften():
            if self._ueb_name(t) == ziel:
                _, it = self.puffer.get_iter_at_line(nr)
                self.puffer.place_cursor(it)
                self.ansicht.scroll_to_iter(it, 0.1, True, 0, 0.1)
                return True
        return False

    def link_am_punkt(self, x, y):
        ok, it = self.ansicht.get_iter_at_location(*self.ansicht.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(x), int(y)))
        if not ok:
            return None
        for t in it.get_tags():
            if (t.props.name or "").startswith("link:"):
                return t.props.name[5:]
        return None

    def _link_geklickt(self, geste, n, x, y):
        if self.strg_klick and not (geste.get_current_event_state() & Gdk.ModifierType.CONTROL_MASK):
            return
        ziel = self.link_am_punkt(x, y)
        if not ziel:
            return
        if ziel.startswith("#"):
            self.springe_zu(ziel[1:])
        else:
            Gtk.UriLauncher.new(ziel).launch(self.get_root(), None, None)

    # ------------------------------------------------------------ Wasserzeichen, Zeilennummern
    def _wasserzeichen_zeichnen(self, bereich, cr, b, h):
        wz = self.seite.get("wasserzeichen")
        if not wz:
            return
        import math
        cr.save()
        cr.translate(b / 2, h / 2)
        cr.rotate(-math.pi / 4 if wz.get("diagonal", True) else 0)
        cr.select_font_face(wz.get("schrift", "sans"), 0, 1)
        cr.set_font_size(wz.get("groesse", 110) * self.zoom / 100.0)
        r, g, bl = _hex_rgb(wz.get("farbe", "#999999"))
        cr.set_source_rgba(r, g, bl, wz.get("deckkraft", 0.22))
        ext = cr.text_extents(wz.get("text", ""))
        cr.move_to(-ext.width / 2 - ext.x_bearing, ext.height / 2)
        cr.show_text(wz.get("text", ""))
        cr.restore()

    def zeilennummern(self, an):
        self.seite["zeilennummern"] = bool(an)
        if an:
            if getattr(self, "_nummern", None) is None:
                self._nummern = Gtk.DrawingArea()
                self._nummern.set_content_width(44)
                self._nummern.set_draw_func(self._nummern_zeichnen)
                self.ansicht.get_vadjustment().connect("value-changed", lambda *_: self._nummern.queue_draw())
                self.puffer.connect("changed", lambda *_: self._nummern.queue_draw())
            self.ansicht.set_gutter(Gtk.TextWindowType.LEFT, self._nummern)
        elif getattr(self, "_nummern", None) is not None:
            self.ansicht.set_gutter(Gtk.TextWindowType.LEFT, None)

    def _nummern_zeichnen(self, bereich, cr, b, h):
        cr.set_source_rgba(0.45, 0.45, 0.45, 1)
        cr.set_font_size(11)
        ok, ersterit = True, self.ansicht.get_iter_at_location(0, 0)
        ok, it = ersterit if isinstance(ersterit, tuple) else (True, ersterit)
        n = it.get_line() if hasattr(it, "get_line") else 0
        for nr in range(max(n - 1, 0), self.puffer.get_line_count()):
            _, z = self.puffer.get_iter_at_line(nr)
            y, hh = self.ansicht.get_line_yrange(z)
            _, wy = self.ansicht.buffer_to_window_coords(Gtk.TextWindowType.LEFT, 0, y)
            if wy > h:
                break
            cr.move_to(b - 8 - 7 * len(str(nr + 1)), wy + hh / 2 + 4)
            cr.show_text(str(nr + 1))


    # ------------------------------------------------------------ Verzeichnisse, Seitenzahl je Zeile
    def seite_der_zeile(self, nr):
        f = self.PX_MM * self.zoom / 100.0
        b, h = self.papier_mm()
        r = self.seite["rand"]
        flaeche = max((h - r["oben"] - r["unten"]) * f, 50)
        _, z = self.puffer.get_iter_at_line(nr)
        y, _hh = self.ansicht.get_line_yrange(z)
        return int(max(y - self.ansicht.get_top_margin(), 0) // flaeche) + 1

    def verzeichnis_schreiben(self, art, titel, zeilen):
        """Ersetzt den Block mit Tag 'verz:<art>' oder fügt ihn an der Cursorstelle ein.
        zeilen: [(Text, Einzug_px)]"""
        tag = html_io.tag_holen(self.puffer, "verz:" + art)
        self.puffer.begin_user_action()
        a = self.puffer.get_start_iter()
        if a.starts_tag(tag) or a.forward_to_tag_toggle(tag):
            b = a.copy()
            b.forward_to_tag_toggle(tag)
            start = a.get_offset()
            self.puffer.delete(a, b)
            ziel = self.puffer.get_iter_at_offset(start)
            self.puffer.place_cursor(ziel)
        else:
            it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
            if not it.starts_line():
                self.puffer.insert(it, "\n")
        von = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_offset()
        self.puffer.insert_at_cursor(titel + "\n")
        self.puffer.apply_tag(html_io.tag_holen(self.puffer, "st:Untertitel"), self.puffer.get_iter_at_offset(von),
                              self.puffer.get_iter_at_offset(von + len(titel) + 1))
        for text, einzug in zeilen:
            o = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_offset()
            self.puffer.insert_at_cursor(text + "\n")
            if einzug:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, "ein:%d" % einzug), self.puffer.get_iter_at_offset(o),
                                      self.puffer.get_iter_at_offset(o + len(text) + 1))
        ende = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_offset()
        self.puffer.apply_tag(tag, self.puffer.get_iter_at_offset(von), self.puffer.get_iter_at_offset(ende))
        self.puffer.end_user_action()
        self.puffer.set_modified(True)

    def hat_verzeichnis(self, art):
        tag = self.puffer.get_tag_table().lookup("verz:" + art)
        if tag is None:
            return False
        it = self.puffer.get_start_iter()
        return it.starts_tag(tag) or it.forward_to_tag_toggle(tag)

    # ------------------------------------------------------------ Rechtschreibung beim Schreiben
    def rechtschreibung(self, an, sprache=None, eigene=None):
        self._rs_an = bool(an)
        if sprache:
            self._rs_sprache = sprache
        if eigene is not None:
            self._rs_eigene = set(eigene)
        tag = html_io.tag_holen(self.puffer, "falsch")
        if an:
            self._rs_planen(0)
        else:
            self.puffer.remove_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())

    def _rs_planen(self, verzoegerung=900):
        if self._rs_timer:
            GLib.source_remove(self._rs_timer)
        self._rs_timer = GLib.timeout_add(verzoegerung, self._rs_los)

    def _rs_los(self):
        self._rs_timer = 0
        text = self.text()
        import threading

        def arbeit():
            try:
                funde = [f for f in schreibhilfe.woerter_fehler(text) if f[2] not in self._rs_eigene]
            except Exception:
                funde = sprachdienste.pruefen(text, self._rs_sprache, self._rs_eigene)
            GLib.idle_add(self._rs_zeigen, text, funde)
        threading.Thread(target=arbeit, daemon=True).start()
        return False

    def _rs_zeigen(self, text, funde):
        if not self._rs_an or self.text() != text:
            return False
        tag = html_io.tag_holen(self.puffer, "falsch")
        self.puffer.remove_tag(tag, self.puffer.get_start_iter(), self.puffer.get_end_iter())
        for a, b, wort, _v in funde:
            self.puffer.apply_tag(tag, self.puffer.get_iter_at_offset(a), self.puffer.get_iter_at_offset(b))
        self.rs_anzahl = len(funde)
        return False

    def _rechtsklick(self, geste, n, x, y):
        """Rechte Maustaste: das Kontextmenü des Fensters (Formatleiste + Menü)."""
        fenster = self.get_root()
        if fenster is not None and hasattr(fenster, "werte"):
            geste.set_state(Gtk.EventSequenceState.CLAIMED)         # das Standardmenü von GTK bleibt zu
            from . import kontextmenue
            kontextmenue.zeigen(fenster, self, x, y)

    def _rs_merken(self, wort, nur_sitzung=False):
        self._rs_eigene.add(wort)
        fenster = self.get_root()
        if fenster is not None and not nur_sitzung:
            fenster.werte.setdefault("eigene_woerter", [])
            if wort not in fenster.werte["eigene_woerter"]:
                fenster.werte["eigene_woerter"].append(wort)
        self._rs_planen(0)

    # ------------------------------------------------------------ Änderungen verfolgen
    def _vor_loeschen(self, puffer, start, ende):
        if not self.verfolgen_an or self._intern:
            return
        ins = puffer.get_tag_table().lookup("ins")
        # eigene, noch nicht angenommene Einfügungen dürfen wirklich verschwinden
        it = start.copy()
        alles_ins = ins is not None
        while it.compare(ende) < 0:
            if ins is None or not it.has_tag(ins):
                alles_ins = False
                break
            it.forward_char()
        if alles_ins:
            return
        puffer.stop_emission_by_name("delete-range")
        self._intern = True
        try:
            puffer.apply_tag(html_io.tag_holen(puffer, "del"), start, ende)
            puffer.place_cursor(start)
        finally:
            self._intern = False
        puffer.set_modified(True)

    def aenderungen(self):
        """[(Offset_von, Offset_bis, 'ins'|'del')] in Textreihenfolge."""
        erg = []
        for art in ("ins", "del"):
            tag = self.puffer.get_tag_table().lookup(art)
            if tag is None:
                continue
            it = self.puffer.get_start_iter()
            while True:
                if not (it.starts_tag(tag) or it.forward_to_tag_toggle(tag)):
                    break
                if not it.has_tag(tag):
                    if not it.forward_to_tag_toggle(tag):
                        break
                    continue
                a = it.copy()
                b = it.copy()
                if not b.forward_to_tag_toggle(tag):
                    break
                erg.append((a.get_offset(), b.get_offset(), art))
                it = b
        return sorted(erg)

    def aenderung_bearbeiten(self, von, bis, art, annehmen):
        self._intern = True
        try:
            a = self.puffer.get_iter_at_offset(von)
            b = self.puffer.get_iter_at_offset(bis)
            if (art == "ins") == annehmen:
                self.puffer.remove_tag(html_io.tag_holen(self.puffer, art), a, b)     # bleibt stehen, ohne Markierung
            else:
                self.puffer.delete(a, b)                                              # verschwindet
        finally:
            self._intern = False
        self.puffer.set_modified(True)

    # ------------------------------------------------------------ AutoKorrektur
    _ERSATZ = {"(c)": "©", "(r)": "®", "(tm)": "™", "...": "…", "->": "→", "<-": "←", "=>": "⇒", "1/2": "½", "1/4": "¼", "3/4": "¾"}

    def _autokorr(self, text):
        if not self.autokorrektur_an or self._intern:
            return False
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        ende = it.get_offset()
        regeln = self.autokorr_regeln
        if text == '"' and regeln["anfuehrung"]:
            vor = self.puffer.get_iter_at_offset(max(ende - 2, 0)).get_char() if ende >= 2 else " "
            auf = vor in " \n(\t[" or ende == 1
            self._ersetze_zeichen(ende - 1, ende, "„" if auf else "“")
            return False
        if text == "'" and regeln["anfuehrung"]:
            vor = self.puffer.get_iter_at_offset(max(ende - 2, 0)).get_char() if ende >= 2 else " "
            self._ersetze_zeichen(ende - 1, ende, "‚" if vor in " \n(" else "’")
            return False
        if text not in (" ", "\n", ".", ",", ";", ":", "!", "?"):
            return False
        # Wort vor dem Zeichen
        a = self.puffer.get_iter_at_offset(max(ende - 1, 0))
        w_ende = a.get_offset()
        w_start = w_ende
        while w_start > 0:
            c = self.puffer.get_iter_at_offset(w_start - 1).get_char()
            if c in " \n\t":
                break
            w_start -= 1
        wort = self.puffer.get_text(self.puffer.get_iter_at_offset(w_start), self.puffer.get_iter_at_offset(w_ende), False)
        if not wort:
            return False
        neu = wort
        for k, v in self._ERSATZ.items():
            if k in neu and not (k == "..." and not regeln["punkte"]):
                neu = neu.replace(k, v)
        if wort == "--" and regeln["striche"]:
            neu = "–"
        if regeln["wochentage"] and neu.lower() in ("montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"):
            neu = neu.capitalize()
        if regeln["feststell"] and len(neu) > 3 and neu[0].islower() and neu[1:].isupper():
            neu = neu.capitalize()
        if len(neu) > 2 and neu[:2].isupper() and neu[2:].islower() and neu.isalpha():
            neu = neu[0] + neu[1:].lower()                      # ZWei → Zwei
        if neu and neu != wort:
            self._ersetze_zeichen(w_start, w_ende, neu)
        elif text == " " and regeln["satzanfang"] and wort[:1].isalpha() and wort[:1].islower() and w_start > 1:
            vor = self.puffer.get_text(self.puffer.get_iter_at_offset(max(w_start - 3, 0)), self.puffer.get_iter_at_offset(w_start), False)
            if re.search(r"[.!?]\s$", vor):
                self._ersetze_zeichen(w_start, w_start + 1, wort[0].upper())          # Satzanfang
        elif w_start == 0 and wort[:1].islower() and wort.isalpha() and text in (" ",) and len(wort) > 2:
            self._ersetze_zeichen(0, 1, wort[0].upper())
        return False

    def _ersetze_zeichen(self, von, bis, neu):
        self._intern = True
        try:
            a = self.puffer.get_iter_at_offset(von)
            b = self.puffer.get_iter_at_offset(bis)
            tags = [t.props.name for t in a.get_tags() if t.props.name not in ("zoom", "grund", "falsch")]
            cursor = self.puffer.get_iter_at_mark(self.puffer.get_insert()).get_offset()
            self.puffer.begin_user_action()
            self.puffer.delete(a, b)
            self.puffer.insert(self.puffer.get_iter_at_offset(von), neu)
            for t in tags:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, t), self.puffer.get_iter_at_offset(von),
                                      self.puffer.get_iter_at_offset(von + len(neu)))
            self.puffer.end_user_action()
            self.puffer.place_cursor(self.puffer.get_iter_at_offset(cursor + len(neu) - (bis - von)))
        finally:
            self._intern = False

    # ------------------------------------------------------------ Wortvorhersage
    _woerterbuch = None

    @classmethod
    def _woerter_laden(cls):
        if cls._woerterbuch is None:
            ws = set()
            try:
                with open("/usr/share/hunspell/de_DE.dic", encoding="utf-8", errors="replace") as f:
                    next(f, None)
                    for z in f:
                        wort = z.split("/")[0].strip()
                        if 4 <= len(wort) <= 24 and wort.isalpha():
                            ws.add(wort)
            except OSError:
                pass
            cls._woerterbuch = sorted(ws, key=str.lower)
        return cls._woerterbuch

    def _wortanfang(self):
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        ende = it.get_offset()
        start = ende
        while start > 0 and self.puffer.get_iter_at_offset(start - 1).get_char().isalpha():
            start -= 1
        return start, ende, self.puffer.get_text(self.puffer.get_iter_at_offset(start), it, False)

    def _vorhersage_zeigen(self):
        import bisect
        if not self.vorhersage_an:
            return False
        start, ende, praefix = self._wortanfang()
        self._vorhersage_verbergen()
        if len(praefix) < 3:
            return False
        p = praefix.lower()
        kand = []
        for wort in set(re.findall(r"[^\W\d_]{4,}", self.text())):
            if wort.lower().startswith(p) and wort.lower() != p:
                kand.append(wort)
        wb = self._woerter_laden()
        schluessel = [x.lower() for x in wb] if False else None
        i = bisect.bisect_left(wb, praefix, key=str.lower) if False else 0
        lo, hi = 0, len(wb)
        while lo < hi:
            mid = (lo + hi) // 2
            if wb[mid].lower() < p:
                lo = mid + 1
            else:
                hi = mid
        while lo < len(wb) and wb[lo].lower().startswith(p) and len(kand) < 12:
            if wb[lo].lower() != p:
                kand.append(wb[lo])
            lo += 1
        kand = sorted(set(kand), key=lambda x: (len(x), x.lower()))[:5]
        if not kand:
            return False
        if praefix[:1].isupper():
            kand = [k[0].upper() + k[1:] for k in kand]
        self._vorschlaege = kand
        pop = Gtk.Popover()
        pop.set_parent(self.ansicht)
        pop.set_autohide(False)
        pop.set_can_focus(False)
        pop.set_has_arrow(False)
        it = self.puffer.get_iter_at_mark(self.puffer.get_insert())
        r = self.ansicht.get_iter_location(it)
        x, y = self.ansicht.buffer_to_window_coords(Gtk.TextWindowType.WIDGET, r.x, r.y + r.height)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = x, y, 1, 1
        pop.set_pointing_to(rect)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for n, k in enumerate(kand):
            b = Gtk.Button(label=("%s     Tab" % k) if n == 0 else k)
            b.add_css_class("flat")
            b.set_can_focus(False)
            b.get_child().set_xalign(0)
            b.connect("clicked", lambda _b, k=k: self._vorschlag_nehmen(k))
            box.append(b)
        pop.set_child(box)
        pop.popup()
        self._vorschlag_pop = pop
        return False

    def _vorhersage_verbergen(self):
        if self._vorschlag_pop is not None:
            self._vorschlag_pop.popdown()
            self._vorschlag_pop.unparent()
            self._vorschlag_pop = None

    def _vorschlag_nehmen(self, wort):
        start, ende, _p = self._wortanfang()
        self._vorhersage_verbergen()
        self._ersetze_zeichen(start, ende, wort)
        self.ansicht.grab_focus()

    def _taste(self, ctrl, keyval, keycode, state):
        if self._vorschlag_pop is not None and self._vorschlaege:
            if keyval == Gdk.KEY_Tab:
                self._vorschlag_nehmen(self._vorschlaege[0])
                return True
            if keyval == Gdk.KEY_Escape:
                self._vorhersage_verbergen()
                return True
        return False

    # ------------------------------------------------------------ Ansichten: Lineal, Netz, Begrenzungen, Layout
    def _px_cm(self):
        return 10 * self.PX_MM * self.zoom / 100.0

    def lineal_zeigen(self, an):
        self.lineal.set_visible(bool(an))
        self.lineal.queue_draw()

    def lineal_hoch_zeigen(self, an):
        if an:
            if getattr(self, "_lineal_v", None) is None:
                self._lineal_v = Gtk.DrawingArea()
                self._lineal_v.set_content_width(22)
                self._lineal_v.set_draw_func(self._lineal_hoch_zeichnen)
                self.ansicht.get_vadjustment().connect("value-changed", lambda *_: self._lineal_v.queue_draw())
            self.ansicht.set_gutter(Gtk.TextWindowType.RIGHT, self._lineal_v)
        elif getattr(self, "_lineal_v", None) is not None:
            self.ansicht.set_gutter(Gtk.TextWindowType.RIGHT, None)

    def _lineal_zeichnen(self, bereich, cr, b, h):
        cr.set_source_rgba(0.93, 0.93, 0.93, 1)
        cr.rectangle(0, 0, b, h)
        cr.fill()
        r = self.seite["rand"]
        f = self.PX_MM * self.zoom / 100.0
        cr.set_source_rgba(0.75, 0.75, 0.75, 1)
        cr.rectangle(0, 0, r["links"] * f, h)
        cr.rectangle(b - r["rechts"] * f, 0, r["rechts"] * f, h)
        cr.fill()
        cr.set_source_rgba(0.25, 0.25, 0.25, 1)
        cr.set_font_size(10)
        cm = self._px_cm()
        n = 0
        x = 0.0
        while x < b:
            cr.move_to(x, h)
            cr.line_to(x, h - (10 if n % 2 == 0 else 5))
            cr.set_line_width(1)
            cr.stroke()
            if n % 2 == 0 and n > 0:
                cr.move_to(x + 2, h - 10)
                cr.show_text(str(n // 2))
            n += 1
            x += cm / 2
        # drei Marken: erste Zeile (oben), links und rechts (unten)
        pos = self._marken_positionen()
        cr.set_source_rgba(0.18, 0.43, 0.71, 1)
        x = pos["erst"]
        cr.move_to(x - 5, 1)
        cr.line_to(x + 5, 1)
        cr.line_to(x, 9)
        cr.fill()
        for name in ("links", "rechts"):
            x = pos[name]
            cr.move_to(x - 5, h - 1)
            cr.line_to(x + 5, h - 1)
            cr.line_to(x, h - 9)
            cr.fill()

    # Die drei Einzugsmarken des Lineals: erste Zeile, links, rechts (vom Satzspiegel aus gezählt, in px)
    def _lineal_werte(self):
        links = erst = rechts = 0.0
        _, von = self.puffer.get_iter_at_line(self._zeilen()[0])
        for t in von.get_tags():
            n = t.props.name or ""
            if n.startswith("ein:"):
                links = float(n[4:])
            elif n.startswith("ers:"):
                erst = float(n[4:])
            elif n.startswith("rei:"):
                rechts = float(n[4:])
        return links, erst, rechts

    def _lineal_x(self):
        """(x des Satzspiegels links, x rechts) im Lineal."""
        f = self.PX_MM * self.zoom / 100.0
        r = self.seite["rand"]
        b = self.papier_mm()[0] * f
        return r["links"] * f, b - r["rechts"] * f

    def _marken_positionen(self):
        x0, x1 = self._lineal_x()
        z = self.zoom / 100.0
        links, erst, rechts = self._lineal_werte()
        return {"erst": x0 + (links + erst) * z, "links": x0 + links * z, "rechts": x1 - rechts * z}

    def _lineal_zieh_anfang(self, geste, x, y):
        pos = self._marken_positionen()
        kandidaten = [(abs(x - p), n) for n, p in pos.items()]
        abstand, name = min(kandidaten)
        if y < 13 and abs(x - pos["erst"]) < 9:
            name = "erst"
        elif y >= 13 and abs(x - pos["links"]) < 9:
            name = "links"
        elif abs(x - pos["rechts"]) < 9:
            name = "rechts"
        elif abstand > 9:
            return
        self._marke_gezogen = name
        self._lineal_start = (x, self._lineal_werte())

    def _lineal_zieh(self, geste, dx, dy):
        if not self._marke_gezogen:
            return
        z = self.zoom / 100.0
        x_start, (links, erst, rechts) = self._lineal_start
        px = dx / z
        if self._marke_gezogen == "links":                     # die erste Zeile wandert mit
            neu_links = max(0, round(links + px))
            self._einzug_setzen(neu_links, erst - (neu_links - links) + erst * 0 if False else erst, rechts)
        elif self._marke_gezogen == "erst":
            self._einzug_setzen(links, round(erst + px), rechts)
        else:
            self._einzug_setzen(links, erst, max(0, round(rechts - px)))

    def _einzug_setzen(self, links, erst, rechts):
        a, b = self._zeilen()
        for n in range(a, b + 1):
            _, von = self.puffer.get_iter_at_line(n)
            bis = von.copy()
            if not bis.ends_line():
                bis.forward_to_line_end()
            bis.forward_char()
            for t in html_io.absatz_namen(self.puffer):
                if t.startswith(("ein:", "ers:", "rei:")):
                    self.puffer.remove_tag_by_name(t, von, bis)
            if links:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, "ein:%d" % links), von, bis)
            if erst:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, "ers:%d" % erst), von, bis)
            if rechts:
                self.puffer.apply_tag(html_io.tag_holen(self.puffer, "rei:%d" % rechts), von, bis)
        self.puffer.set_modified(True)
        self.lineal.queue_draw()

    def _lineal_hoch_zeichnen(self, bereich, cr, b, h):
        cr.set_source_rgba(0.93, 0.93, 0.93, 1)
        cr.rectangle(0, 0, b, h)
        cr.fill()
        cr.set_source_rgba(0.25, 0.25, 0.25, 1)
        cr.set_font_size(9)
        cm = self._px_cm()
        versatz = self.ansicht.get_vadjustment().get_value()
        n = int(versatz // (cm / 2))
        y = n * cm / 2 - versatz
        while y < h:
            cr.move_to(0, y)
            cr.line_to(8 if n % 2 == 0 else 4, y)
            cr.set_line_width(1)
            cr.stroke()
            if n % 2 == 0 and n > 0:
                cr.move_to(9, y + 3)
                cr.show_text(str(n // 2))
            n += 1
            y += cm / 2

    def netz_zeigen(self, an):
        self.deko_netz = bool(an)
        self.deko.queue_draw()

    def begrenzungen_zeigen(self, an):
        self.deko_ecken = bool(an)
        self.deko.queue_draw()

    def rahmen_setzen(self, kanten, art="solid", breite=1, farbe="#7C858E"):
        """Rahmen um die gewählten Absätze; kanten: Buchstaben aus o u l r, leer = kein Rahmen."""
        name = "rahmen:%s:%s:%g:%s" % (kanten, art, breite, farbe) if kanten else None
        self.absatz_tag_toggle(name, "rahmen:")
        self.deko.queue_draw()

    def _rahmen_zeichnen(self, cr, b):
        puffer = self.puffer
        n = puffer.get_line_count()
        i = 0
        while i < n:
            _, von = puffer.get_iter_at_line(i)
            namen = [t.props.name for t in von.get_tags() if t.props.name and t.props.name.startswith("rahmen:")]
            if not namen:
                i += 1
                continue
            j = i
            while j + 1 < n:
                _, nxt = puffer.get_iter_at_line(j + 1)
                if namen[0] not in [t.props.name for t in nxt.get_tags()]:
                    break
                j += 1
            _, kanten, art, breite, farbe = (namen[0].split(":", 4) + [""] * 5)[:5]
            _, ende = puffer.get_iter_at_line(j)
            if not ende.ends_line():
                ende.forward_to_line_end()
            r1 = self.ansicht.get_iter_location(von)
            r2 = self.ansicht.get_iter_location(ende)
            x0, y0 = self.ansicht.buffer_to_window_coords(Gtk.TextWindowType.WIDGET, 0, r1.y)
            _, y1 = self.ansicht.buffer_to_window_coords(Gtk.TextWindowType.WIDGET, 0, r2.y + r2.height)
            l = self.ansicht.get_left_margin() - 3
            r_ = b - self.ansicht.get_right_margin() + 3
            rgba = Gdk.RGBA()
            rgba.parse(farbe or "#7C858E")
            cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, 1)
            w_ = max(0.5, float(breite or 1))
            cr.set_line_width(w_)
            cr.set_dash({"dashed": [6, 3], "dotted": [1.5, 2.5]}.get(art, []))
            y0 -= 1
            y1 += 1
            kanten_linien = {"o": ((l, y0), (r_, y0)), "u": ((l, y1), (r_, y1)),
                             "l": ((l, y0), (l, y1)), "r": ((r_, y0), (r_, y1))}
            aussen = {"o": (0, -3), "u": (0, 3), "l": (-3, 0), "r": (3, 0)}
            for k in kanten:
                (xa, ya), (xb, yb) = kanten_linien.get(k, ((0, 0), (0, 0)))
                cr.move_to(xa, ya)
                cr.line_to(xb, yb)
                if art == "double":
                    dx, dy = aussen[k]
                    cr.move_to(xa + dx, ya + dy)
                    cr.line_to(xb + dx, yb + dy)
            cr.stroke()
            cr.set_dash([])
            i = j + 1

    def _deko_zeichnen(self, bereich, cr, b, h):
        self._rahmen_zeichnen(cr, b)
        if self.deko_netz:
            cr.set_source_rgba(0.3, 0.5, 0.8, 0.22)
            cr.set_line_width(1)
            cm = self._px_cm()
            x = 0.0
            while x < b:
                cr.move_to(x + .5, 0)
                cr.line_to(x + .5, h)
                x += cm
            y = 0.0
            while y < h:
                cr.move_to(0, y + .5)
                cr.line_to(b, y + .5)
                y += cm
            cr.stroke()
        if self.deko_ecken:
            cr.set_source_rgba(0.45, 0.45, 0.45, 0.9)
            cr.set_line_width(1.2)
            l, r_, o, u = (self.ansicht.get_left_margin(), b - self.ansicht.get_right_margin(),
                           self.ansicht.get_top_margin(), h - self.ansicht.get_bottom_margin())
            for x, y, dx, dy in ((l, o, 1, 1), (r_, o, -1, 1), (l, u, 1, -1), (r_, u, -1, -1)):
                cr.move_to(x + dx * 14, y)
                cr.line_to(x, y)
                cr.line_to(x, y + dy * 14)
            cr.stroke()

    def layout_setzen(self, art):
        """blatt: Papier in der Mitte · web: Text füllt die Breite"""
        self.layout = art
        web = art == "web"
        self.blatt.set_hexpand(web)
        self.mitte.set_hexpand(web)
        self.mitte.set_halign(Gtk.Align.FILL if web else Gtk.Align.CENTER)
        self.blatt.set_halign(Gtk.Align.FILL if web else Gtk.Align.CENTER)
        if web:
            self.blatt.set_size_request(-1, -1)
            self.mitte.set_size_request(-1, -1)
            self.ansicht.set_left_margin(24)
            self.ansicht.set_right_margin(24)
            self.ansicht.set_top_margin(16)
        else:
            self.seite_anwenden()


    # ------------------------------------------------------------ Kontext für die Werkzeug-Reiter
    def _tabellen_fokus(self, anker, r, c):
        if self._sperre:
            return
        self.tabelle_aktiv = (anker, r, c)
        self.rand_aktiv = None
        self.emit("format-stand")

    def _fokus_text(self):
        if self._sperre:
            return
        if self.tabelle_aktiv is not None or self.rand_aktiv is not None:
            self.tabelle_aktiv = None
            self.rand_aktiv = None
            self.emit("format-stand")

    def _fokus_rand(self, was):
        if self._sperre:
            return
        self.rand_aktiv = was
        self.tabelle_aktiv = None
        self.emit("format-stand")

    def kontexte(self):
        """Welche Werkzeug-Reiter jetzt etwas zu sagen haben: tabelle, bild, zeichnen, diagramm, smartart, gleichung, kopffuss."""
        k = set()
        if self.tabelle_aktiv is not None:
            k.add("tabelle")
        if self.rand_aktiv:
            k.add("kopffuss")
        a = self.objekt_am_cursor() if self.tabelle_aktiv is None and self.rand_aktiv is None else None
        if a is not None:
            d = a.daten
            q = d.get("quelle", {}) or {}
            if d["typ"] == "bild":
                k.add("bild")
            elif d["typ"] == "svg":
                if "diagramm" in q:
                    k.add("diagramm")
                elif "smartart" in q:
                    k.add("smartart")
                elif "formel" in q:
                    k.add("gleichung")
                else:
                    k.add("zeichnen")
            elif d["typ"] == "textfeld":
                k.add("zeichnen")
                k.add("text")
        return k


def _hex_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
