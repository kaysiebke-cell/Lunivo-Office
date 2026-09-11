"""Vorschau-Server fuer die Oberflaeche — nur zum Entwickeln.

`python3 -m http.server` schickt Last-Modified und sonst nichts. Der
Browser legt programm.js (rund 500 kB) dann in den Zwischenspeicher und
holt es nicht wieder — eine Aenderung war im Fenster nicht zu sehen,
obwohl die Datei laengst neu war. Das kostete eine halbe Stunde Suche an
der falschen Stelle.

Deshalb dieser Server: derselbe wie der eingebaute, nur mit
„Cache-Control: no-store". Er gehoert zum Werkzeug, nicht zum Programm —
start.py liefert die Oberflaeche im Betrieb selbst aus.
"""
import functools
import http.server
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
ORDNER = os.path.join(os.path.dirname(HIER), "oberflaeche")


class OhneZwischenspeicher(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    handler = functools.partial(OhneZwischenspeicher, directory=ORDNER)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print("Vorschau auf http://127.0.0.1:%d — ohne Zwischenspeicher" % port)
        server.serve_forever()


if __name__ == "__main__":
    main()
