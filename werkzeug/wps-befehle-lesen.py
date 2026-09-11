#!/usr/bin/env python3
"""Die Befehle des WPS Writer auslesen.

WARUM DIESES WERKZEUG. Wir bauen Lunivo nach dem Vorbild des WPS Writer,
und bisher kam das Vorbild aus Bildschirmfotos. Ein Foto zeigt, was auf
dem Bildschirm Platz hat — nicht, was das Programm kann. Kay hat
vorgeschlagen, statt dessen im Programm selbst nachzusehen, und das war
der bessere Weg: Aus zwei Dateien kamen ueber fuenfhundert Befehle.

WO ES STEHT. WPS Office liegt unter /opt/kingsoft/wps-office/office6/.
Seine Beschriftungen stecken in den Qt-Sprachdateien unter mui/<sprache>/:
wps.qm ist der Writer, et.qm die Tabellenkalkulation, wpp.qm die
Praesentation, kso.qm das Gemeinsame. Die deutschen Ordner sind bei einer
frischen Installation leer — die englischen sind es, die zaehlen.

WIE GELESEN WIRD. Eine .qm-Datei ist ein Binaerformat; die Zeichenketten
stehen als UTF-16 (big endian) darin. Wir suchen also nach Laeufen von
Null-Byte-plus-Zeichen. Das erste Zeichen eines Fundes ist oft ein
Laengenbyte, das als Buchstabe durchkommt — deshalb wird vorn abgeschnitten.

Das ist Lesen, nicht Kopieren: Wir uebernehmen keine Dateien und keinen
Code, sondern sehen nach, welche Befehle es gibt, und entscheiden dann
selbst, welche davon in Lunivo gehoeren und wie sie dort heissen.
"""
import os
import re
import sys

WPS = "/opt/kingsoft/wps-office/office6/mui/en_US"

GRUPPEN = {
    "TABELLEN": (
        r"(?i)\b(table|cell|row|column|merge|split|gridline)\b",
        r"(?i)chart|series|axis|smartart|pivot|mail|sql|database|formula|\(|%|<",
    ),
    "DOKUMENTENSTEUERUNG": (
        r"(?i)\b(section|break|header|footer|page setup|watermark|protect"
        r"|track changes|restrict|navigation|outline|bookmark)\b",
        r"(?i)chart|mail|pdf|\(|%|<|error|cannot|failed",
    ),
}


def zeichenketten(weg):
    """Die lesbaren UTF-16-Laeufe einer .qm-Datei."""
    with open(weg, "rb") as datei:
        roh = datei.read()
    gefunden = set()
    for fund in re.finditer(rb"(?:\x00[\x20-\x7e]){3,90}", roh):
        wort = fund.group().decode("utf-16-be", "ignore")
        wort = re.sub(r"^[^A-Za-z]+", "", wort).strip().replace("&", "")
        if 3 <= len(wort) <= 52 and re.match(r"^[A-Z]", wort):
            gefunden.add(wort)
    return gefunden


def main():
    if not os.path.isdir(WPS):
        print("WPS Office liegt nicht unter " + WPS, file=sys.stderr)
        print("Ohne die Installation gibt es hier nichts zu lesen.", file=sys.stderr)
        return 1

    alle = set()
    for name in ("wps.qm", "wpstips.qm"):
        weg = os.path.join(WPS, name)
        if os.path.isfile(weg):
            alle |= zeichenketten(weg)

    for titel, (nimm, lass) in GRUPPEN.items():
        nimm = re.compile(nimm)
        lass = re.compile(lass)
        treffer = sorted(w for w in alle if nimm.search(w) and not lass.search(w))
        print("=== %s (%d) ===" % (titel, len(treffer)))
        for wort in treffer:
            print(wort)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
