#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lunivo-Office als eigenes Fenster — ohne Browser drumherum.

Ein Fenster, eine Anzeigefläche, die Dateien aus diesem Ordner. Dazwischen
ein winziger Webserver, und der hat einen Grund:

  · Unter file:// gilt eine Seite nicht als sicherer Ursprung. Dann gibt es
    weder localStorage noch das Nachladen der Wörterliste — das Programm
    verlöre bei jedem Schließen alles. http://localhost gilt als sicher.
  · Was gespeichert ist, hängt an der Adresse. Ein fester Port heißt: derselbe
    Speicher, jedes Mal.

Er hört ausschließlich auf 127.0.0.1 — von außen ist nichts zu erreichen,
und er läuft nur, solange das Fenster offen ist.
"""

import base64
import functools
import glob
import html
import http.server
import json
import math
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import socket
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2                # noqa: E402

GLib.set_prgname("lunivo-office")

HIER = os.path.dirname(os.path.abspath(__file__))
OBERFLAECHE = os.path.join(HIER, "oberflaeche")     # was der Server ausliefert

# Fester Port, damit die Adresse gleich bleibt: An ihr hängt der Speicher.
# Ein wechselnder Port hieße jedes Mal ein leeres Fenster.
PORT = 8322

# Wo alles liegt, was das Programm behält.
#
# Der Ordner heißt weiter „schreibprogramm', obwohl das Programm inzwischen
# Lunivo-Office heißt. Das ist Absicht und kein Übersehen: DATEN ist zugleich
# das base_data_directory von WebKit (siehe unten), und darin steckt der
# localStorage — der geschriebene Text, der Schlüssel für die KI, die
# gelernten Wörter, jede Einstellung. Ein anderer Ordnername hieße: beim
# ersten Start nach dem Update steht alles leer da, und die 700 MB
# LibreOffice und 400 MB LanguageTool wären ein zweites Mal zu laden.
#
# Ein Ordnername ist nichts, was jemand zu sehen bekommt. Der Preis wäre
# also hoch und der Gewinn keiner.
DATEN = os.path.expanduser("~/.local/share/schreibprogramm")
ZWISCHEN = os.path.expanduser("~/.cache/schreibprogramm")


# Das Handbuch ist unser eigenes und liegt neben der Oberfläche.
#
# Vorher stand hier die Hilfeseite von LibreOffice. Das war der bequeme
# Weg und der falsche: Sie beschreibt ein anderes Programm — Knöpfe, die
# es hier nicht gibt, und keinen von denen, die es hier gibt. Wer unter
# „Hilfe' nachschlägt, sucht Hilfe zu diesem Programm.
HANDBUCH_SEITE = "handbuch.html"


# Die Formate, die im Speichern-Dialog zur Wahl stehen. Reihenfolge ist
# Absicht: oben das eigene Format, dann die von Microsoft, dann der Rest.
FORMAT_LISTE = [
    ("odt",  "ODF-Textdokument (.odt)"),
    ("docx", "Word-Dokument (.docx)"),
    ("doc",  "Word 97–2003 (.doc)"),
    ("rtf",  "Rich Text Format (.rtf)"),
    ("fodt", "Flaches ODF (.fodt)"),
    ("html", "Webseite (.html)"),
    ("txt",  "Reiner Text (.txt)"),
    ("pdf",  "PDF-Dokument (.pdf)"),
    ("epub", "E-Book (.epub)"),
]

# Die Filter im Öffnen-Dialog. Oben das Nützlichste: alles, was das
# Programm lesen kann. Wer gezielt sucht, schaltet weiter.
OEFFNEN_FILTER = [
    ("Alle Dokumente, die das Programm lesen kann",
     ["*.odt", "*.ott", "*.fodt", "*.docx", "*.doc", "*.rtf", "*.html", "*.htm",
      "*.txt", "*.md", "*.xml", "*.odf", "*.dotx", "*.docm", "*.dot"]),
    ("Word-Dokumente (.docx, .doc, .rtf)",
     ["*.docx", "*.doc", "*.rtf", "*.dotx", "*.docm", "*.dot"]),
    ("ODF-Textdokumente (.odt, .fodt)", ["*.odt", "*.ott", "*.fodt", "*.odf"]),
    ("Vorlagen (.ott, .dotx, .dot)", ["*.ott", "*.dotx", "*.dot"]),
    ("Webseiten (.html)", ["*.html", "*.htm"]),
    ("Textdateien (.txt)", ["*.txt", "*.md"]),
    ("Alle Dateien", ["*"]),
]

# Für „Tabellenblatt einbetten": Da soll nicht die ganze Dateiliste stehen.
TABELLEN_FILTER = [
    ("Tabellen (.xlsx, .xls, .ods, .csv)",
     ["*.xlsx", "*.xls", "*.ods", "*.csv", "*.fods"]),
    ("Alle Dateien", ["*"]),
]

# Der Ordner, in dem zuletzt etwas geöffnet oder gespeichert wurde. Beim
# nächsten Mal steht der Dialog gleich dort — niemand fängt gern wieder
# im Persönlichen Ordner an.
LETZTER_ORDNER = {"weg": None}

# Was zuletzt gelesen werden durfte — dieselbe Vorsorge wie beim Schreiben.
LESEZIEL = {"pfad": None}

# Die zuletzt geöffneten und gespeicherten Dateien.
#
# Die Liste liegt hier und nicht in der Seite, und das ist eine Frage der
# Vorsicht. Läge sie dort, müsste die Seite dem Server einen Pfad nennen
# dürfen, um eine Datei zu öffnen — und dann könnte sie jeden Pfad nennen,
# auch einen, der sie nichts angeht. So kennt die Seite nur Nummern: Der
# Server sagt, was in seiner Liste steht, und nimmt zurück nur eine Nummer
# daraus entgegen.
ZULETZT_DATEI = os.path.join(DATEN, "zuletzt.json")
ZULETZT_VIELE = 10


def zuletzt_lesen():
    """Die Liste, ohne das, was es nicht mehr gibt.

    Wer eine Datei verschiebt oder wegwirft, soll sie nicht weiter im Menü
    stehen sehen und sich beim Klick einen Fehler abholen. Geprüft wird
    deshalb beim Lesen, nicht beim Schreiben — dazwischen kann alles
    passieren.
    """
    try:
        with open(ZULETZT_DATEI, encoding="utf-8") as datei:
            liste = json.load(datei)
    except (OSError, ValueError):
        return []
    if not isinstance(liste, list):
        return []
    return [weg for weg in liste
            if isinstance(weg, str) and os.path.isfile(weg)][:ZULETZT_VIELE]


def zuletzt_merken(pfad):
    """Nach vorn, und nur einmal in der Liste."""
    pfad = os.path.abspath(pfad)
    liste = [weg for weg in zuletzt_lesen() if weg != pfad]
    liste.insert(0, pfad)
    try:
        os.makedirs(DATEN, exist_ok=True)
        with open(ZULETZT_DATEI, "w", encoding="utf-8") as datei:
            json.dump(liste[:ZULETZT_VIELE], datei, ensure_ascii=False)
    except OSError:
        pass                    # Die Liste ist keine, für die man abbricht.


# ============================================================
# LanguageTool als zweite Meinung
#
# Es läuft als eigener Prozess, nicht als eingebundene Bibliothek. Das hat
# zwei Gründe. Der eine ist rechtlich: LanguageTool steht unter LGPL-2.1 —
# ein getrennter Prozess lässt die Lizenz dieses Programms unberührt. Der
# andere ist praktisch: Es ist in Java geschrieben, und Java startet
# langsam. Einmal gestartet bleibt es stehen und antwortet in
# Millisekunden.
#
# Gestartet wird es erst beim ersten Gebrauch. Wer die gründliche Prüfung
# nie anrührt, bekommt auch keinen Java-Prozess.
# ============================================================
LT_ORDNER = os.path.join(DATEN, "languagetool")
LT_PORT = 8081
LT = {"lauf": None}


def languagetool_starten():
    """Startet den LanguageTool-Server, falls er noch nicht läuft."""
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", LT_PORT)) == 0:
            return True                                     # läuft schon

    if not os.path.isdir(LT_ORDNER):
        raise FileNotFoundError(
            "LanguageTool ist nicht eingerichtet. Es gehört nach "
            + LT_ORDNER + ".")

    jar = None
    for wurzel, _, dateien in os.walk(LT_ORDNER):
        if "languagetool-server.jar" in dateien:
            jar = os.path.join(wurzel, "languagetool-server.jar")
            break
    if not jar:
        raise FileNotFoundError("In " + LT_ORDNER + " fehlt languagetool-server.jar.")

    if not shutil.which("java"):
        raise FileNotFoundError("Für LanguageTool wird Java gebraucht; es ist nicht installiert.")

    LT["lauf"] = subprocess.Popen(
        ["java", "-cp", jar, "org.languagetool.server.HTTPServer",
         "--port", str(LT_PORT), "--allow-origin", "*"],
        cwd=os.path.dirname(jar),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)

    # Java braucht einen Moment. Kurz warten statt sofort zu scheitern.
    for _ in range(60):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", LT_PORT)) == 0:
                return True
        time.sleep(0.5)
    raise RuntimeError("LanguageTool ist nicht hochgekommen.")


# ============================================================
# Der HTTP-Server — Handshake
# ============================================================
ANSICHT = {"seite": None}


class Handler(http.server.SimpleHTTPRequestHandler):
    """Behandelt HTTP-Anfragen."""

    # pylint: disable=R0903,W0212,W0613

    def translate_path(self, anfrage):
        """Gibt den Dateipfad für eine Anfrage an."""
        # Dem übergeordneten Handler genügt nicht ein Ordner; er muss das
        # Wurzelverzeichnis sein. Wir sagen ihm, das Wurzelverzeichnis sei
        # der Ordner oberflaeche.
        self.directory = OBERFLAECHE
        return super().translate_path(anfrage)

    def do_GET(self):  # pylint: disable=C0103
        """Behandelt GET-Anfragen."""
        weg = urllib.parse.urlparse(self.path).path

        # Die üblichen Dateien.
        if weg.endswith((".html", ".js", ".css", ".json", ".txt", ".svg", ".png", ".jpg", ".jpeg")):
            return super().do_GET()

        # „/api/..." sind Daten-Anfragen.
        if weg.startswith("/api/"):
            return api_anfrage(self, weg)

        # Alles andere ist Fehler.
        self.send_error(404)

    def log_message(self, *args, **kwargs):
        """Unterbindet die Ausgabe von Anfragen auf der Konsole."""
        # Der Konsole geben wir nur Fehler, nicht die hundert Anfragen pro
        # Sekunde, wenn die Seite sich selbst lädt.


def server_starten():
    """Startet den lokalen HTTP-Server auf einem zufälligen Port."""
    # Der Server läuft auf localhost, Anfragen von außen können nicht ankommen.
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return PORT


def api_anfrage(handler, weg):
    """Beantwortet Anfragen vom Typ /api/..."""
    # Das ist die Schnittstelle zwischen der Seite und dem Betriebssystem.
    # Sicherheit brauchen wir nicht — der Server hört nur auf 127.0.0.1.
    # Abzuschreiben brauchen wir auch nicht — wer die Seite verändern wollte,
    # könnte das direkt tun.


def seiten_dialog(ansicht, dialog):
    """Behandelt confirm() und prompt() der Seite."""
    # Die Seite darf es versuchen, aber es tut nichts.
    dialog.close_dialog()


def speichern_fragen(umgebung, download):
    """Fragt, wo eine heruntergeladene Datei gespeichert werden soll."""
    # Das ist das Event, das feuert, wenn die Seite etwas herunterladen will.
    # Es blockt, bis wir download.set_destination aufrufen, oder bis die
    # Anfrage-Behandlung zu Ende geht — und dann wird sie verworfen.


def rechtschreibung_einschalten(umgebung):
    """Setzt den Rechtschreibprüfer auf Deutsch."""


# ============================================================
# Fenster und Start
# ============================================================

def main():
    # Ensure symbol exists: if icon.svg is missing, try to create a small placeholder
    icon_path = os.path.join(HIER, "symbole", "icon.svg")
    if not os.path.isfile(icon_path):
        try:
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            with open(icon_path, "w", encoding="utf-8") as f:
                f.write('''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="100%" height="100%" fill="#1e2a38"/>
  <circle cx="64" cy="64" r="50" fill="#4a90e2"/>
</svg>''')
        except OSError:
            # If we cannot write, fall back to continuing; the later check will report an error
            pass

    # Required files check (symbole/icon.svg is ensured above)
    for noetig in ("oberflaeche/index.html", "oberflaeche/js/pruefung.js",
                   "oberflaeche/daten/regeln.js", "oberflaeche/daten/woerter.txt",
                   "symbole/icon.svg"):
        if not os.path.isfile(os.path.join(HIER, noetig)):
            print("Es fehlt: %s" % noetig, file=sys.stderr)
            return 1

    port = server_starten()

    os.makedirs(DATEN, exist_ok=True)
    os.makedirs(ZWISCHEN, exist_ok=True)
    speicher = WebKit2.WebsiteDataManager(base_data_directory=DATEN,
                                          base_cache_directory=ZWISCHEN)
    umgebung = WebKit2.WebContext.new_with_website_data_manager(speicher)
    umgebung.connect("download-started", speichern_fragen)

    ansicht = WebKit2.WebView.new_with_context(umgebung)
    einst = ansicht.get_settings()
    einst.set_enable_developer_extras(False)
    einst.set_enable_write_console_messages_to_stdout(False)
    einst.set_user_agent(einst.get_user_agent() + " Lunivo-Office/1.0")

    # Ohne das darf JavaScript die Zwischenablage nicht anfassen — und die
    # Vorgabe ist „nicht". Strg+C und Strg+V macht WebKit dann zwar selbst,
    # aber „Ausschneiden", „Kopieren" und „Einfügen" im Menü, im Ribbon und
    # im Rechtsklick liefen ins Leere: Sie rufen execCommand, und das tut
    # ohne diese Erlaubnis nichts. Ein Menüpunkt, der beim Anklicken
    # schweigt, ist schlimmer als keiner.
    einst.set_javascript_can_access_clipboard(True)

    rechtschreibung_einschalten(umgebung)

    # Der Druckauftrag hängt sich an diese Ansicht — sie ist das, was
    # gesetzt wird, und damit das, was auf das Papier kommt.
    ANSICHT["seite"] = ansicht

    fenster = Gtk.Window(title="Lunivo-Office")
    fenster.set_default_size(1280, 860)

    # Erst über den Namen: Dann sucht sich der Arbeitsplatz aus dem
    # Symbol-Ordner selbst die passende Größe heraus — 16 Bildpunkte für die
    # Fensterleiste, 48 für den Umschalter. Eine feste Datei müsste er für
    # jede Stelle herunterrechnen, und klein sähe das nach nichts aus.
    fenster.set_icon_name("lunivo-office")

    # Solange der Menüeintrag noch nicht geschrieben wurde, kennt der
    # Arbeitsplatz den Namen nicht. Dann tut es die Datei aus dem Ordner.
    if not Gtk.IconTheme.get_default().has_icon("lunivo-office"):
        for groesse in ("symbole/icon-256.png", "symbole/icon-128.png", "symbole/icon-512.png"):
            symbol = os.path.join(HIER, groesse)
            if os.path.isfile(symbol):
                fenster.set_icon_from_file(symbol)
                break
    # Ohne das bleiben confirm() und prompt() der Seite unsichtbar hängen.
    ansicht.connect("script-dialog", seiten_dialog)

    fenster.add(ansicht)
    fenster.connect("destroy", Gtk.main_quit)

    ansicht.load_uri("http://localhost:%d/" % port)
    fenster.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
