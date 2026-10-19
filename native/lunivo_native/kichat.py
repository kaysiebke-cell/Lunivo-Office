"""KI-Chat als Seitenleiste."""
import threading

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from . import schreibhilfe


class KiChat(Gtk.Box):
    def __init__(self, fenster):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.fenster = fenster
        self.verlauf = []
        self.add_css_class("schreibhilfe")
        self.set_size_request(340, -1)
        for r in ("start", "end", "top", "bottom"):
            getattr(self, "set_margin_" + r)(10)
        kopf = Gtk.Box(spacing=6)
        t = Gtk.Label(use_markup=True, xalign=0, hexpand=True, label="<b>KI-Chat</b>")
        kopf.append(t)
        neu = Gtk.Button(label="Neu")
        neu.connect("clicked", lambda *_: self.leeren())
        kopf.append(neu)
        self.append(kopf)
        self.anzeige = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.anzeige.set_left_margin(6)
        self.anzeige.set_right_margin(6)
        rolle = Gtk.ScrolledWindow(vexpand=True)
        rolle.set_child(self.anzeige)
        self.rolle = rolle
        self.append(rolle)
        self.kontext = Gtk.CheckButton(label="Dokument als Zusammenhang mitgeben")
        self.append(self.kontext)
        zeile = Gtk.Box(spacing=6)
        self.eingabe = Gtk.Entry(placeholder_text="Frage an die KI …", hexpand=True)
        self.eingabe.connect("activate", self.senden)
        zeile.append(self.eingabe)
        b = Gtk.Button(label="Senden")
        b.add_css_class("suggested-action")
        b.connect("clicked", self.senden)
        zeile.append(b)
        self.append(zeile)
        self.tag_nutzer = self.anzeige.get_buffer().create_tag("nutzer", weight=700, foreground="#4A8FD8")
        self.tag_ki = self.anzeige.get_buffer().create_tag("ki", weight=700, foreground="#3E9C7A")

    def leeren(self):
        self.verlauf = []
        self.anzeige.get_buffer().set_text("")

    def _zeile(self, wer, text, tag):
        b = self.anzeige.get_buffer()
        o = b.get_end_iter().get_offset()
        b.insert(b.get_end_iter(), wer + ": ")
        b.apply_tag(tag, b.get_iter_at_offset(o), b.get_end_iter())
        b.insert(b.get_end_iter(), text + "\n\n")
        GLib.idle_add(lambda: self.rolle.get_vadjustment().set_value(self.rolle.get_vadjustment().get_upper()))

    def senden(self, *_):
        frage = self.eingabe.get_text().strip()
        if not frage:
            return
        w = self.fenster
        anbieter = schreibhilfe.anbieter_aktiv(w.werte)
        if not anbieter.get("modell"):
            return w.meldung("Kein KI-Modell", "Bitte unter Schreibhilfe ▸ KI-Konfiguration ein Modell wählen.")
        self.eingabe.set_text("")
        self._zeile("Sie", frage, self.tag_nutzer)
        system = w.werte.get("chat_system", "Du bist ein hilfreicher Schreibassistent. Antworte auf Deutsch, klar und kurz.")
        d = w.dok()
        if self.kontext.get_active() and d:
            system += "\n\nDas Dokument des Benutzers:\n" + d.text().replace("￼", "")[:8000]
        self.verlauf.append({"role": "user", "content": frage})
        nachrichten = [{"role": "system", "content": system}] + self.verlauf[-12:]
        w.status("KI antwortet …")

        def arbeit():
            try:
                antwort = schreibhilfe.chat(anbieter, nachrichten, 0.5)
                GLib.idle_add(self._fertig, antwort, None)
            except Exception as e:
                GLib.idle_add(self._fertig, "", str(e))
        threading.Thread(target=arbeit, daemon=True).start()

    def _fertig(self, antwort, fehler):
        if fehler:
            self._zeile("Fehler", fehler, self.tag_ki)
        else:
            self.verlauf.append({"role": "assistant", "content": antwort})
            self._zeile("KI", antwort, self.tag_ki)
        self.fenster.status("Bereit.")
