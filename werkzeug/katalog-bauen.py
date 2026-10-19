#!/usr/bin/env python3
"""Baut oberflaeche/daten/symbolkatalog.js aus einem Ordner voller .svg-Dateien.

    git clone --depth 1 https://github.com/lucide-icons/lucide.git
    python3 werkzeug/katalog-bauen.py lucide/icons

Die Umrechnung macht svg-zu-pfad.py daneben: Aus <circle>, <rect> und
<line> wird ein einziger Pfad, weil das Programm genau einen setzt.
"""
import importlib.util
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location(
    "umbau", os.path.join(HIER, "svg-zu-pfad.py"))
umbau = importlib.util.module_from_spec(spec)
spec.loader.exec_module(umbau)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    ordner = sys.argv[1]
    katalog = {}
    for datei in sorted(os.listdir(ordner)):
        if not datei.endswith(".svg"):
            continue
        pfad = umbau.umbauen(open(os.path.join(ordner, datei), encoding="utf-8").read())
        if pfad:
            katalog[datei[:-4]] = pfad

    ziel = os.path.join(HIER, os.pardir, "oberflaeche", "daten", "symbolkatalog.js")
    kopf = open(ziel, encoding="utf-8").read().split("const SYMBOLKATALOG = ")[0]
    with open(ziel, "w", encoding="utf-8") as datei:
        datei.write(kopf + "const SYMBOLKATALOG = "
                    + json.dumps(katalog, ensure_ascii=False, indent=0, sort_keys=True)
                    + ";\n")
    print("%d Symbole nach %s geschrieben." % (len(katalog), ziel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
