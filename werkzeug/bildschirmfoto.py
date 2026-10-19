#!/usr/bin/env python3
"""Nimmt ein Bildschirmfoto der Oberfläche auf — ohne Fenster auf dem Schirm.

    python3 werkzeug/bildschirmfoto.py --ziel bilder/uebersicht.png \
        --adresse http://localhost:8750/index.html \
        --js "…was vorher zu tun ist…"

Gerendert wird mit WebKit, also mit derselben Maschine, auf der das
Programm läuft — nicht mit einem anderen Browser, der Schriften und
Abstände anders setzt. Das Fenster ist eine Gtk.OffscreenWindow: Es wird
gezeichnet, aber niemand sieht es, und wer am Rechner sitzt, wird nicht
gestört.

Der Ablauf: Seite laden, warten, JavaScript ausführen, noch einmal warten,
Foto machen. Die zweite Wartezeit ist nötig, weil ein Klick im Programm
oft etwas anstößt, das erst im nächsten Bild fertig ist.
"""
import argparse
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2                # noqa: E402


def foto_machen(adresse, ziel, js, breite, hoehe, warten, nachwarten):
    stand = {"fehler": None}

    fenster = Gtk.OffscreenWindow()
    fenster.set_default_size(breite, hoehe)
    ansicht = WebKit2.WebView()
    ansicht.set_size_request(breite, hoehe)
    fenster.add(ansicht)
    fenster.show_all()

    def speichern(_ansicht, ergebnis):
        try:
            flaeche = ansicht.get_snapshot_finish(ergebnis)
            flaeche.write_to_png(ziel)
        except Exception as grund:                          # noqa: BLE001
            stand["fehler"] = str(grund)
        Gtk.main_quit()

    def schiessen():
        ansicht.get_snapshot(WebKit2.SnapshotRegion.VISIBLE,
                             WebKit2.SnapshotOptions.NONE, None, speichern)
        return False

    def nach_dem_js(_ansicht, _ergebnis):
        GLib.timeout_add(nachwarten, schiessen)

    def wenn_geladen():
        if js:
            try:
                ansicht.run_javascript(js, None, nach_dem_js)
            except Exception as grund:                      # noqa: BLE001
                stand["fehler"] = str(grund)
                Gtk.main_quit()
        else:
            schiessen()
        return False

    def geladen(_ansicht, ereignis):
        if ereignis == WebKit2.LoadEvent.FINISHED:
            GLib.timeout_add(warten, wenn_geladen)

    ansicht.connect("load-changed", geladen)
    ansicht.load_uri(adresse)

    # Nicht ewig warten, falls die Seite nie fertig wird.
    GLib.timeout_add(30000, lambda: (Gtk.main_quit(), False)[1])
    Gtk.main()
    return stand["fehler"]


def main():
    zettel = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    zettel.add_argument("--adresse", required=True)
    zettel.add_argument("--ziel", required=True)
    zettel.add_argument("--js", default="")
    zettel.add_argument("--breite", type=int, default=1500)
    zettel.add_argument("--hoehe", type=int, default=950)
    zettel.add_argument("--warten", type=int, default=1200,
                        help="Millisekunden nach dem Laden, vor dem JavaScript")
    zettel.add_argument("--nachwarten", type=int, default=700,
                        help="Millisekunden nach dem JavaScript, vor dem Foto")
    wahl = zettel.parse_args()

    fehler = foto_machen(wahl.adresse, wahl.ziel, wahl.js,
                         wahl.breite, wahl.hoehe, wahl.warten, wahl.nachwarten)
    if fehler:
        print("Ging nicht: %s" % fehler, file=sys.stderr)
        return 1
    print("%s geschrieben." % wahl.ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
