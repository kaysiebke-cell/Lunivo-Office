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
DATEN = os.path.expanduser("~/.local/share/schreibprogramm")
ZWISCHEN = os.path.expanduser("~/.cache/schreibprogramm")

# Das Handbuch ist unser eigenes und liegt neben der Oberfläche.
HANDBUCH_SEITE = "handbuch.html"

# Die Formate, die im Speichern-Dialog zur Wahl stehen.
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

# Die Filter im Öffnen-Dialog.
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

LETZTER_ORDNER = {"weg": None}
LESEZIEL = {"pfad": None}

ZULETZT_DATEI = os.path.join(DATEN, "zuletzt.json")
ZULETZT_VIELE = 10

def zuletzt_lesen():
    """Die Liste, ohne das, was es nicht mehr gibt."""
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
        pass

# LanguageTool als zweite Meinung
LT_ORDNER = os.path.join(DATEN, "languagetool")
LT_PORT = 8081
LT = {"lauf": None}

def languagetool_starten():
    """Startet den LanguageTool-Server, falls er noch nicht läuft."""
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", LT_PORT)) == 0:
            return True

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

    for _ in range(60):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", LT_PORT)) == 0:
                return True
        time.sleep(0.5)
    raise RuntimeError("LanguageTool ist nicht hochgekommen.")

# Der HTTP-Server — Handshake
ANSICHT = {"seite": None}

class Handler(http.server.SimpleHTTPRequestHandler):
    """Behandelt HTTP-Anfragen."""

    # pylint: disable=R0903,W0212,W0613

    def translate_path(self, anfrage):
        """Gibt den Dateipfad für eine Anfrage an."""
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
        pass

def server_starten():
    """Startet den lokalen HTTP-Server auf einem zufälligen Port."""
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return PORT

def api_anfrage(handler, weg):
    """Beantwortet Anfragen vom Typ /api/..."""
    pass

def seiten_dialog(ansicht, dialog):
    """Behandelt confirm() und prompt() der Seite."""
    dialog.close_dialog()

def speichern_fragen(umgebung, download):
    """Fragt, wo eine heruntergeladene Datei gespeichert werden soll."""
    pass

def rechtschreibung_einschalten(umgebung):
    """Setzt den Rechtschreibprüfer auf Deutsch."""
    pass

# Fenster und Start

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

    einst.set_javascript_can_access_clipboard(True)

    rechtschreibung_einschalten(umgebung)

    ANSICHT["seite"] = ansicht

    fenster = Gtk.Window(title="Lunivo-Office")
    fenster.set_default_size(1280, 860)

    fenster.set_icon_name("lunivo-office")

    if not Gtk.IconTheme.get_default().has_icon("lunivo-office"):
        for groesse in ("symbole/icon-256.png", "symbole/icon-128.png", "symbole/icon-512.png"):
            symbol = os.path.join(HIER, groesse)
            if os.path.isfile(symbol):
                fenster.set_icon_from_file(symbol)
                break
    
    ansicht.connect("script-dialog", seiten_dialog)

    fenster.add(ansicht)
    fenster.connect("destroy", Gtk.main_quit)

    ansicht.load_uri("http://localhost:%d/" % port)
    fenster.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
