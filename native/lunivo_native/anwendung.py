"""Gtk.Application: startet das Fenster, übernimmt beim ersten Start die alten Texte."""
import os
import sys

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib, Adw  # noqa: E402

from . import einstellungen, fenster, migration, pfade


class Anwendung(Adw.Application):
    def __init__(self):
        super().__init__(application_id="de.lunivo.Office",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.werte = None
        self.fenster = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        pfade.anlegen()
        self.werte = einstellungen.lesen()

    def _fenster(self):
        if self.fenster is None:
            self.fenster = fenster.Fenster(self, self.werte)
            self._erster_start()
        return self.fenster

    def _erster_start(self):
        f = self.fenster
        offen = [p for p in self.werte.get("offen", []) if os.path.exists(p)]
        uebernommen = []
        if not self.werte.get("migriert"):
            try:
                uebernommen, sicherung = migration.uebernehmen()
            except Exception as e:                       # nie am Start scheitern
                uebernommen, sicherung = [], None
                f.meldung("Übernahme der alten Texte fehlgeschlagen", str(e))
            self.werte["migriert"] = True
            einstellungen.schreiben(self.werte)
            if uebernommen:
                offen = uebernommen + offen
                GLib.idle_add(f.meldung, "Texte aus dem alten Programm übernommen",
                              "%d Text(e) wurden übernommen und als Reiter geöffnet.\n"
                              "Der alte Speicher ist unverändert und gesichert unter:\n%s" % (len(uebernommen), sicherung))
        if not self.werte.get("start_zuletzt", True):
            offen = uebernommen
        for p in offen:
            f.datei_oeffnen(p)
        self._entwuerfe_wiederherstellen(f)
        if f.reiter.get_n_pages() == 0:
            f.neu()

    def _entwuerfe_wiederherstellen(self, f):
        """Entwürfe eines abgestürzten Laufs (Prozess existiert nicht mehr) wieder öffnen."""
        import json
        o = os.path.join(pfade.DATEN, "entwuerfe")
        if not os.path.isdir(o):
            return
        gefunden = 0
        for n in sorted(os.listdir(o)):
            if not n.endswith(".html"):
                continue
            pid = n.split("-")[0]
            if pid.isdigit() and os.path.exists("/proc/%s" % pid):
                continue
            base = os.path.join(o, n[:-5])
            try:
                meta = json.load(open(base + ".json", encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
            d = f.datei_oeffnen(base + ".html")
            if d:
                d.pfad = meta.get("pfad")
                d.titel = (meta.get("titel") or "Wiederhergestellt") + " (Entwurf)"
                d.puffer.set_modified(True)
                f._titel_auffrischen(d)
                gefunden += 1
            for ext in (".html", ".json"):
                try:
                    os.remove(base + ext)
                except OSError:
                    pass
        if gefunden:
            GLib.idle_add(f.meldung, "Entwürfe wiederhergestellt",
                          "%d nicht gespeicherte Dokument(e) aus dem letzten Lauf wurden wieder geöffnet." % gefunden)

    def do_activate(self):
        self._fenster().present()

    def do_open(self, dateien, n, hinweis):
        f = self._fenster()
        for d in dateien:
            f.datei_oeffnen(d.get_path())
        f.present()


def main():
    return Anwendung().run(sys.argv)
