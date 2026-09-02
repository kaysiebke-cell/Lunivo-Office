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
import http.server
import json
import math
import mimetypes
import os
import re
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
# Der Ordner heißt weiter „schreibprogramm", obwohl das Programm inzwischen
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


HANDBUCH = "https://help.libreoffice.org/latest/de/text/swriter/main0000.html"


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
     ["*.odt", "*.fodt", "*.docx", "*.doc", "*.rtf", "*.html", "*.htm",
      "*.txt", "*.md", "*.xml", "*.odf", "*.dotx", "*.docm"]),
    ("Word-Dokumente (.docx, .doc, .rtf)", ["*.docx", "*.doc", "*.rtf", "*.dotx", "*.docm"]),
    ("ODF-Textdokumente (.odt, .fodt)", ["*.odt", "*.fodt", "*.odf"]),
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


def languagetool_fragen(text):
    """Gibt die Funde als schlichte Liste zurück — Stelle, Grund, Vorschlag."""
    languagetool_starten()

    ladung = urllib.parse.urlencode({
        "language": "de-DE",
        "text": text[:60000],
        # Was die Schreibhilfe selbst besser kann, muss hier nicht doppelt
        # kommen: Reine Rechtschreibung findet schon der Rechtschreibprüfer
        # des Systems, und Doppelfunde verwirren nur.
        "disabledCategories": "TYPOS",
    }).encode("utf-8")

    antwort = urllib.request.urlopen(
        urllib.request.Request("http://127.0.0.1:%d/v2/check" % LT_PORT, data=ladung),
        timeout=90)
    daten = json.loads(antwort.read().decode("utf-8"))

    funde = []
    for treffer in daten.get("matches", []):
        ersatz = treffer.get("replacements") or []
        funde.append({
            "von": treffer.get("offset", 0),
            "bis": treffer.get("offset", 0) + treffer.get("length", 0),
            "grund": treffer.get("message", ""),
            "vorschlag": (ersatz[0].get("value") if ersatz else ""),
        })
    return funde[:200]


# Was gerade vorgelesen wird. Ein zweites „Vorlesen" soll das erste ablösen
# und nicht danebenreden.
VORLESER = {"lauf": None}

# Eine Stimme, die nicht nach Maschine klingt.
#
# speech-dispatcher spricht auf den meisten Rechnern über espeak-ng, und das
# ist ein Formantsynthesizer: Er rechnet Laute zusammen, statt sie aus
# Aufnahmen zu setzen. Er KANN nicht menschlich klingen — das ist Bauart, nicht
# Einstellung, und seine hundert „Stimmen" ändern nur die Klangfarbe.
#
# Wer sich seinen Brief vorlesen lässt, um Fehler zu hören, hört bei espeak vor
# allem espeak. Piper ist ein neuronaler Synthesizer, läuft offline auf der CPU
# und braucht für viereinhalb Sekunden Ton eine Viertelsekunde. Liegt er da,
# spricht er; sonst bleibt es bei spd-say.
# Gesucht wird an zwei Stellen. Die Schreibhilfe holt dieselbe Stimme, und
# 90 MB ein zweites Mal zu laden wäre nur, um den Ordner passend zu benennen.
PIPER_ORTE = [
    os.path.join(DATEN, "piper"),
    os.path.expanduser("~/.local/share/schreibhilfe/piper"),
]


# Wie die Dateinamen auf Deutsch heißen. Wer „de_DE-eva_k-x_low" liest, weiß
# nicht, ob das eine Frau ist — und genau danach sucht man in einer Liste.
PIPER_NAMEN = {
    "de_DE-thorsten-medium":  "Thorsten (männlich)",
    "de_DE-thorsten-high":    "Thorsten, feiner (männlich)",
    "de_DE-thorsten-low":     "Thorsten, gröber (männlich)",
    "de_DE-karlsson-low":     "Karlsson (männlich)",
    "de_DE-pavoque-low":      "Pavoque (männlich)",
    "de_DE-kerstin-low":      "Kerstin (weiblich)",
    "de_DE-ramona-low":       "Ramona (weiblich)",
    "de_DE-eva_k-x_low":      "Eva (weiblich)",
    "de_DE-mls-medium":       "Gemischt (mehrere Sprecher)",
    "de_DE-thorsten_emotional-medium": "Thorsten mit Gefühl (männlich)",
}


def piper_programm():
    """Das Piper-Programm, wo immer es liegt — oder nichts."""
    for ort in PIPER_ORTE:
        programm = os.path.join(ort, "piper", "piper")
        if os.path.isfile(programm) and os.access(programm, os.X_OK):
            return programm, ort
    return None, None


def piper_stimmen():
    """Die eingerichteten Stimmen, mit lesbarem Namen. Beste zuerst.

    „high" vor „medium" vor „low": Die Stufe steckt im Dateinamen und sagt,
    wie fein das Modell rechnet. Wer die Liste aufklappt, soll oben das
    Beste finden und nicht die Reihenfolge des Alphabets.
    """
    programm, ort = piper_programm()
    if not programm:
        return []

    stufe = {"high": 0, "medium": 1, "low": 2, "x_low": 3}
    gefunden = []
    for datei in sorted(os.listdir(ort)):
        if not datei.endswith(".onnx"):
            continue
        kennung = datei[:-len(".onnx")]
        rang = stufe.get(kennung.rsplit("-", 1)[-1], 9)
        gefunden.append((rang, kennung,
                         PIPER_NAMEN.get(kennung, kennung.replace("de_DE-", ""))))

    gefunden.sort(key=lambda e: (e[0], e[2]))
    return [{"kennung": k, "name": n} for _, k, n in gefunden]


def piper_finden(kennung=""):
    """Programm und Stimmdatei — zur gewünschten Stimme oder zur ersten besten."""
    programm, ort = piper_programm()
    if not programm:
        return None, None

    if kennung:
        pfad = os.path.join(ort, kennung + ".onnx")
        if os.path.isfile(pfad):
            return programm, pfad

    stimmen = piper_stimmen()
    if not stimmen:
        return None, None
    return programm, os.path.join(ort, stimmen[0]["kennung"] + ".onnx")


def piper_da():
    """Ist eine gute Stimme eingerichtet — und lässt sie sich abspielen?"""
    programm, _ = piper_finden()
    return bool(programm and (shutil.which("paplay") or shutil.which("aplay")))


def piper_tempo(tempo):
    """Das Tempo von spd-say (−100 bis 100) in Pipers Maß übersetzen.

    Piper rechnet umgekehrt: „length_scale" ist die Länge eines Lautes, größer
    heißt langsamer. 0 bleibt 1,0; −100 wird zu 1,5 und +100 zu 0,6.
    """
    t = max(-100, min(100, int(tempo or 0)))
    return 1.0 - t * (0.4 / 100) if t > 0 else 1.0 - t * (0.5 / 100)


def vorlesen_mit_piper(text, tempo, kennung=""):
    """Piper schreibt rohen Ton, das Abspielprogramm nimmt ihn direkt entgegen.

    Über eine Zwischendatei zu gehen hieße: erst den ganzen Brief rechnen, dann
    anfangen. So beginnt der Ton nach dem ersten Satz.
    """
    rate = "22050"      # steht so in de_DE-thorsten-medium.onnx.json
    if shutil.which("paplay"):
        abspielen = ["paplay", "--raw", "--rate=" + rate,
                     "--format=s16le", "--channels=1"]
    else:
        abspielen = ["aplay", "-q", "-r", rate, "-f", "S16_LE", "-c", "1",
                     "-t", "raw", "-"]

    programm, stimme = piper_finden(kennung)
    if not programm:
        return False
    sprechen = subprocess.Popen(
        [programm, "--model", stimme, "--output_raw",
         "--length_scale", "%.2f" % piper_tempo(tempo)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, start_new_session=True)
    ton = subprocess.Popen(abspielen, stdin=sprechen.stdout,
                           stderr=subprocess.DEVNULL, start_new_session=True)
    # Sonst bekäme piper kein SIGPIPE, wenn das Abspielen abbricht.
    sprechen.stdout.close()

    def fuettern():
        try:
            sprechen.stdin.write(text.encode("utf-8"))
            sprechen.stdin.close()
        except (OSError, ValueError):
            pass

    threading.Thread(target=fuettern, daemon=True).start()
    VORLESER["lauf"] = ton
    VORLESER["rechner"] = sprechen
    return True


def vorlesen(text, stimme, tempo):
    """Liest den Text vor — über den Sprachdienst des Systems.

    WebKit selbst kann es nicht: „speechSynthesis" gibt es dort nicht, und
    ohne Sprachausgabe fehlt einem Menschen mit Legasthenie das Wichtigste.
    Denn Fehler, über die das Auge beim Lesen hinweggeht, hört das Ohr sofort.

    Der Sprachdienst des Arbeitsplatzes kann es — hier wird er gefragt.
    """
    vorlesen_beenden()

    if not piper_da() and not shutil.which("spd-say"):
        raise FileNotFoundError(
            "Auf diesem Rechner ist keine Sprachausgabe eingerichtet "
            "(es fehlt speech-dispatcher).")

    # Nicht endlos: Ein ganzes Buch vorzulesen war nicht gemeint, und der
    # Dienst nimmt ohnehin nur begrenzt viel auf einmal.
    text = text.strip()[:20000]
    if not text:
        return False

    # Die guten Stimmen tragen ihre Kennung mit: „piper:de_DE-kerstin-low".
    # Ohne Angabe nimmt Piper seine erste — und wer eine espeak-Stimme
    # ausgesucht hat, bekommt die.
    if stimme.startswith("piper:"):
        return vorlesen_mit_piper(text, tempo, stimme[len("piper:"):])
    if piper_da() and not stimme:
        return vorlesen_mit_piper(text, tempo)

    befehl = ["spd-say", "-l", "de", "-w"]
    if stimme:
        befehl += ["-y", stimme]
    # Das Tempo geht von -100 bis 100; 0 ist das gewohnte.
    befehl += ["-r", str(max(-100, min(100, int(tempo or 0))))]
    befehl.append(text)

    VORLESER["lauf"] = subprocess.Popen(befehl, start_new_session=True)
    return True


def vorlesen_beenden():
    """Hält das Vorlesen an — auch das, was noch in der Warteschlange steht."""
    # Bei Piper sind es zwei Prozesse: einer rechnet, einer spielt ab. Nur den
    # zweiten anzuhalten hieße, dass der erste weiterrechnet und in ein totes
    # Rohr schreibt.
    for schluessel in ("lauf", "rechner"):
        vorgang = VORLESER.get(schluessel)
        VORLESER[schluessel] = None
        if vorgang and vorgang.poll() is None:
            try:
                vorgang.terminate()
                # Abholen, sonst bleibt ein Zombie stehen, bis zufällig das
                # nächste Vorlesen ihn einsammelt.
                vorgang.wait(timeout=2)
            except (OSError, subprocess.SubprocessError):
                pass
    if shutil.which("spd-say"):
        try:
            subprocess.run(["spd-say", "-C"], timeout=5)     # Warteschlange leeren
        except (OSError, subprocess.SubprocessError):
            pass


def stimmen_lesen():
    """Die deutschen Stimmen, die der Sprachdienst anbietet."""
    if not shutil.which("spd-say"):
        return []
    try:
        lauf = subprocess.run(["spd-say", "-L"], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.SubprocessError):
        return []

    stimmen = []
    for zeile in lauf.stdout.splitlines():
        teile = zeile.split()
        # Aufbau: NAME SPRACHE VARIANTE — uns interessiert nur Deutsch.
        if len(teile) >= 2 and teile[1] == "de":
            stimmen.append(teile[0])
    return stimmen[:60]


def teile_lesen():
    """Was zusätzlich geholt wurde und ob es da ist.

    Drei Dinge liegen außerhalb des Programms, weil sie zu groß sind. Nur
    der Rechner weiß, ob sie eingerichtet sind — die Seite kann in keinen
    Ordner sehen, und das ist auch gut so.
    """
    def groesse_von(*wege):
        summe = 0
        for weg in wege:
            if not weg or not os.path.exists(weg):
                continue
            if os.path.isfile(weg):
                summe += os.path.getsize(weg)
                continue
            for wurzel, _, dateien in os.walk(weg):
                for datei in dateien:
                    try:
                        summe += os.path.getsize(os.path.join(wurzel, datei))
                    except OSError:
                        pass
        return summe

    def lesbar(zahl):
        if zahl <= 0:
            return "—"
        if zahl >= 1024 ** 3:
            return "%.1f GB" % (zahl / 1024 ** 3)
        return "%d MB" % round(zahl / 1024 ** 2)

    stimmen = piper_stimmen()
    _, piper_ort = piper_programm()

    return [
        {
            "name": "LibreOffice",
            "wofuer": "Word-Dateien, PDF und EPUB",
            "holen": "wird beim ersten Bedarf geholt",
            "da": bool(motor_finden()),
            "groesse": lesbar(groesse_von(EIGENER_MOTOR)) if os.path.isdir(EIGENER_MOTOR)
                       else ("im System" if shutil.which("soffice") else "~700 MB"),
        },
        {
            "name": "LanguageTool",
            "wofuer": "„Gründlich prüfen\" — Grammatik über die eigenen Regeln hinaus",
            "holen": ("wird beim ersten Aufruf geholt" if shutil.which("java")
                      else "braucht Java — das fehlt auf diesem Rechner"),
            "da": os.path.isdir(LT_ORDNER) and bool(shutil.which("java")),
            "groesse": lesbar(groesse_von(LT_ORDNER)) if os.path.isdir(LT_ORDNER)
                       else "~400 MB",
        },
        {
            "name": "Stimmen zum Vorlesen"
                    + (" (%d)" % len(stimmen) if stimmen else ""),
            "wofuer": "aufgenommene Stimmen statt der blechernen des Systems",
            "holen": "./stimme-holen.sh",
            "da": bool(stimmen),
            "groesse": lesbar(groesse_von(piper_ort)) if piper_ort else "~90 MB",
        },
    ]


def ordner_waehlen():
    """Fragt nach einem Ordner — für „Pfade" in den Optionen."""
    antwort = {}
    fertig = threading.Event()

    def zeigen():
        dialog = Gtk.FileChooserDialog(title="Ordner zum Speichern",
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons("Abbrechen", Gtk.ResponseType.CANCEL,
                           "Wählen", Gtk.ResponseType.ACCEPT)
        dialog.set_current_folder(LETZTER_ORDNER["weg"] or os.path.expanduser("~"))
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            antwort["ordner"] = dialog.get_filename() or ""
        dialog.destroy()
        fertig.set()
        return False

    GLib.idle_add(zeigen)
    fertig.wait(300)
    return antwort.get("ordner", "")


def rechtschreibsprachen():
    """Die Sprachen, für die auf diesem Rechner ein Wörterbuch liegt.

    Gefragt wird enchant — dieselbe Schicht, die auch WebKit benutzt. Wer
    hunspell-de-de installiert hat, bekommt „de_DE"; wer nicht, bekommt eine
    leere Liste, und dann wird gar nicht erst eingeschaltet.
    """
    werkzeug = shutil.which("enchant-lsmod-2") or shutil.which("enchant-lsmod")
    if not werkzeug:
        return ["de_DE"]          # da ist etwas, es sagt nur keiner welches
    try:
        lauf = subprocess.run([werkzeug, "-list-dicts"], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ["de_DE"]

    alle = [zeile.split()[0] for zeile in lauf.stdout.splitlines() if zeile.strip()]
    # Deutsch zuerst, der Rest hinterher — die Reihenfolge entscheidet, welches
    # Wörterbuch WebKit bevorzugt.
    deutsch = [s for s in alle if s.startswith("de")]
    andere = [s for s in alle if not s.startswith("de")]
    for lieber in ("de_DE_frami", "de_DE"):
        if lieber in deutsch:
            deutsch.remove(lieber)
            deutsch.insert(0, lieber)
    return deutsch + andere


def rechtschreibung_einschalten(umgebung):
    """Rote Wellenlinien unter unbekannten Wörtern — im Fenster.

    Das Attribut spellcheck="true" im HTML genügt NICHT. WebKitGTK prüft
    von sich aus gar nicht; es muss am Kontext eingeschaltet und mit
    Sprachen versorgt werden. Ohne diese beiden Zeilen unterringelt das
    Fenster nichts, während dieselbe Seite in Chrome ringelt — ein
    Unterschied, den man lange sucht.

    Die Wörterbücher kommen aus dem System (hunspell über enchant). Fehlen
    sie, bleibt es aus: Eingeschaltet ohne Wörterbuch würde WebKit jedes
    zweite Wort anstreichen.
    """
    sprachen = rechtschreibsprachen()
    if not sprachen:
        return False
    try:
        umgebung.set_spell_checking_languages(sprachen)
        umgebung.set_spell_checking_enabled(True)
        return True
    except Exception:                                   # noqa: BLE001
        return False


def bildschirmfoto(was):
    """Nimmt den Bildschirm auf und gibt das Bild zurück.

    Eine Seite kommt an den Bildschirm nicht heran, und das ist gut so.
    Der Rechner selbst kann es — hier wird er gefragt.
    """
    werkzeug = None
    for name in ("gnome-screenshot", "spectacle", "import"):
        if shutil.which(name):
            werkzeug = name
            break
    if not werkzeug:
        raise FileNotFoundError(
            "Auf diesem Rechner ist kein Werkzeug für Bildschirmfotos installiert.")

    with tempfile.TemporaryDirectory(prefix="lunivo-office-bild-") as ordner:
        ziel = os.path.join(ordner, "foto.png")

        if werkzeug == "gnome-screenshot":
            befehl = ["gnome-screenshot", "-f", ziel]
            if was == "bereich":
                befehl.insert(1, "-a")
        elif werkzeug == "spectacle":
            befehl = ["spectacle", "-b", "-n", "-o", ziel,
                      "-r" if was == "bereich" else "-f"]
        else:                                               # import (ImageMagick)
            befehl = ["import", ziel] if was == "bereich" else ["import", "-window", "root", ziel]

        try:
            subprocess.run(befehl, timeout=120, capture_output=True)
        except (OSError, subprocess.SubprocessError) as grund:
            raise RuntimeError(str(grund))

        if not os.path.isfile(ziel):
            return b""
        with open(ziel, "rb") as datei:
            return datei.read()


def fenster_ordnen(wie):
    """Legt die Fenster des Programms nebeneinander, untereinander oder
    gekachelt. Die Maße kommen vom Bildschirm, nicht aus einer Annahme."""
    fenstern = fenster_lesen()
    if len(fenstern) < 2:
        return len(fenstern)

    try:
        masse = subprocess.run(["xdotool", "getdisplaygeometry"],
                               capture_output=True, encoding="utf-8", timeout=10)
        breite, hoehe = (int(z) for z in masse.stdout.split())
    except (OSError, subprocess.SubprocessError, ValueError):
        breite, hoehe = 1920, 1080

    # Etwas Platz unten für die Fensterleiste des Arbeitsplatzes.
    hoehe = int(hoehe * 0.94)
    zahl = len(fenstern)

    if wie == "untereinander":
        spalten, zeilen = 1, zahl
    elif wie == "kacheln":
        spalten = math.ceil(math.sqrt(zahl))
        zeilen = math.ceil(zahl / spalten)
    else:                                                   # nebeneinander
        spalten, zeilen = zahl, 1

    teil_breite = breite // spalten
    teil_hoehe = hoehe // zeilen

    for i, eintrag in enumerate(fenstern):
        x = (i % spalten) * teil_breite
        y = (i // spalten) * teil_hoehe
        try:
            subprocess.run(["wmctrl", "-i", "-r", eintrag["kennung"],
                            "-e", "0,%d,%d,%d,%d" % (x, y, teil_breite, teil_hoehe)],
                           timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
    return zahl


def dialog_oeffnen(nur=""):
    """Zeigt den Öffnen-Dialog mit Dateifiltern."""
    antwort = {}
    fertig = threading.Event()

    def zeigen():
        dialog = Gtk.FileChooserDialog(title="Öffnen", action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons("Abbrechen", Gtk.ResponseType.CANCEL,
                           "Öffnen", Gtk.ResponseType.ACCEPT)
        dialog.set_current_folder(LETZTER_ORDNER["weg"] or os.path.expanduser("~"))

        liste = TABELLEN_FILTER if nur == "tabellen" else OEFFNEN_FILTER
        for name, muster in liste:
            filter_ = Gtk.FileFilter()
            filter_.set_name(name)
            for einzeln in muster:
                filter_.add_pattern(einzeln)
                # Auch in GROSSSCHREIBUNG: „BRIEF.DOCX" ist dieselbe Datei.
                filter_.add_pattern(einzeln.upper())
            dialog.add_filter(filter_)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            antwort["pfad"] = dialog.get_filename()
        dialog.destroy()
        fertig.set()
        return False

    GLib.idle_add(zeigen)
    fertig.wait(600)
    return antwort


# Wohin zuletzt gespeichert werden durfte. Nur dieser eine Weg wird
# beschrieben, und nur einmal: Sonst könnte die Seite jede Datei auf dem
# Rechner überschreiben, indem sie einfach einen Pfad mitschickt.
SPEICHERZIEL = {"pfad": None}


def dialog_speichern(name, endung):
    """Zeigt den Speichern-Dialog mit Formatauswahl.

    Der Dialog gehört zum Arbeitsplatz, nicht zur Seite: Nur er kennt die
    Ordner des Menschen, seine Lesezeichen und die gewohnte Bedienung. Die
    Seite bekommt am Ende nur zurück, wohin und in welchem Format.

    Gezeigt werden muss er im Haupt-Faden von GTK — die Anfrage kommt aber
    aus einem Nebenfaden des Servers. Deshalb der Umweg über „idle_add" und
    das Warten auf ein Zeichen.
    """
    antwort = {}
    fertig = threading.Event()

    def zeigen():
        dialog = Gtk.FileChooserDialog(title="Speichern unter",
                                       action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons("Abbrechen", Gtk.ResponseType.CANCEL,
                           "Speichern", Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_folder(LETZTER_ORDNER["weg"] or os.path.expanduser("~"))
        dialog.set_current_name((name or "Unbenannt") + "." + endung)

        wahl = Gtk.ComboBoxText()
        for kuerzel, beschriftung in FORMAT_LISTE:
            wahl.append(kuerzel, beschriftung)
        wahl.set_active_id(endung if any(k == endung for k, _ in FORMAT_LISTE) else "odt")

        # Wer das Format wechselt, will nicht auch noch die Endung im Namen
        # von Hand nachziehen.
        def format_gewechselt(kasten):
            neu = kasten.get_active_id()
            jetzt = dialog.get_current_name() or ((name or "Unbenannt") + "." + neu)
            dialog.set_current_name(re.sub(r"\.[^.]*$", "", jetzt) + "." + neu)

        wahl.connect("changed", format_gewechselt)

        reihe = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        reihe.pack_start(Gtk.Label(label="Dateityp:"), False, False, 0)
        reihe.pack_start(wahl, True, True, 0)
        reihe.show_all()
        dialog.set_extra_widget(reihe)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            antwort["pfad"] = dialog.get_filename()
            antwort["endung"] = wahl.get_active_id()
        dialog.destroy()
        fertig.set()
        return False

    GLib.idle_add(zeigen)
    # Reichlich Zeit: Der Mensch sucht vielleicht erst einen Ordner.
    fertig.wait(600)
    return antwort


def fenster_lesen():
    """Die offenen Fenster dieses Programms.

    Der Fensterverwalter führt die Liste, nicht das Programm — mehrere
    Fenster wissen voneinander nichts. „wmctrl" fragt ihn danach.
    """
    try:
        lauf = subprocess.run(["wmctrl", "-l"], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []

    fenstern = []
    for zeile in lauf.stdout.splitlines():
        teile = zeile.split(None, 3)
        if len(teile) < 4:
            continue
        kennung, titel = teile[0], teile[3]
        # Drei Namen, weil drei Fassungen unterwegs sein können: das
        # Fenster dieser Fassung, eines der Fassung vor der Umbenennung,
        # und die Schreibhilfe daneben.
        if any(name in titel for name in
               ("Lunivo-Office", "Schreibprogramm", "Schreibhilfe")):
            fenstern.append({"kennung": kennung, "titel": titel})
    return fenstern


def schriften_lesen():
    """Die Schriftfamilien, die auf diesem Rechner liegen.

    Eine Seite darf von sich aus nicht wissen, welche Schriften installiert
    sind — sonst ließe sich am Muster der vorhandenen Schriften erkennen, wer
    da sitzt. Im eigenen Fenster ist das keine fremde Seite, sondern das
    eigene Programm; hier soll die Liste stehen, die auch LibreOffice zeigt.

    Gefragt wird fontconfig, nicht der Ordner: In /usr/share/fonts steht der
    Dateiname, und der ist nicht der Name der Schrift. „LiberationSerif-
    Regular.ttf" heißt für den Menschen „Liberation Serif".
    """
    try:
        # Das Encoding ausdrücklich: Ohne LANG in der Umgebung läse Python die
        # Ausgabe nach der Locale des Systems, und griechische, arabische oder
        # bengalische Schriftnamen kämen als Buchstabensalat an.
        lauf = subprocess.run(["fc-list", ":", "family"],
                              capture_output=True, timeout=10,
                              encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return []                                  # kein fontconfig: dann eben nicht

    familien = set()
    for zeile in lauf.stdout.splitlines():
        # Eine Schrift kann unter mehreren Namen laufen, durch Komma getrennt.
        # fc-list schützt dabei Sonderzeichen mit einem Rückstrich: Aus
        # „Butch & Sundance Two-Tone" wird „Butch & Sundance Two\\-Tone". Wer
        # den Rückstrich für einen Teil des Namens hält, wirft die Schrift
        # weg — und genau das ist hier passiert, ausgerechnet bei den
        # Schriften einer eigenen Sammlung.
        for name in zeile.split(","):
            name = re.sub(r"\\(.)", r"\1", name.strip())

            # Was danach noch einen Rückstrich trägt, ist keine Maskierung
            # mehr, sondern ein Fehler in der Schriftdatei: Manche tragen
            # ihren zweiten Namen unübersetzt als „\\u09ae\\u09bf…" in sich.
            # Solche Namen erkennt im Kasten niemand wieder. Steuerzeichen und
            # Namen ohne einen einzigen Buchstaben ebenso wenig.
            if (name and len(name) < 60 and name.isprintable()
                    and "\\" not in name
                    and any(zeichen.isalpha() for zeichen in name)):
                familien.add(name)

    return sorted(familien, key=lambda n: n.casefold())


# Wohin die Umwandlung ihre Zwischendateien legt und welches eigene Profil
# LibreOffice dabei benutzt. Das Profil ist wichtig: Läuft nebenher ein
# normales LibreOffice-Fenster, weigert sich ein zweiter Aufruf, mitzuarbeiten
# — er hängt sich an das laufende an und tut dann gar nichts. Mit eigenem
# Profil sind die beiden voneinander unabhängig.
UMWANDEL_PROFIL = os.path.join(ZWISCHEN, "loprofil")

# Wie der Ausgabefilter in LibreOffice heißt. Die Namen stammen aus
# LibreOffice selbst und sind keine Erfindung; wer sie ändert, bekommt
# „no export filter".
# Nur die Formate, die ihn wirklich brauchen. Ein Filter zu viel schadet:
# Mit „odt:writer8" kam aus einer Webseite ein Web-Dokument heraus statt eines
# Textdokuments — die Datei hieß .odt und war innen etwas anderes. Ohne Filter
# trifft LibreOffice hier die richtige Wahl von selbst.
FILTER = {
    "docx": "MS Word 2007 XML",
    "doc":  "MS Word 97",
    "rtf":  "Rich Text Format",
    "fodt": "OpenDocument Text Flat XML",
    "html": "HTML (StarWriter)",
    "epub": "EPUB",
}

# Woraus und wohin umgewandelt werden darf. Eine feste Liste, keine freie
# Angabe: Was hier hereinkommt, geht als Dateiname an ein anderes Programm.
FORMATE = {"odt", "fodt", "docx", "doc", "rtf", "html", "txt", "pdf", "epub", "odf",
           "xlsx", "xls", "ods", "csv", "fods", "dotx", "docm"}

# Mehr als das schreibt niemand in einem Brief. Die Grenze verhindert, dass
# ein Versehen den Arbeitsspeicher füllt.
GROESSTE_DATEI = 80 * 1024 * 1024


# Der eigene Motor, ausgepackt neben den übrigen Daten des Programms. Er
# wird bevorzugt: Dann hängt das Programm nicht davon ab, was auf dem Rechner
# gerade installiert ist — und ein Update des Systems nimmt ihm nichts weg.
EIGENER_MOTOR = os.path.join(DATEN, "libreoffice", "opt")


def motor_finden():
    """Erst der eigene, dann der des Systems, sonst nichts.

    Der eigene liegt unter …/opt/libreoffice<Fassung>/program/soffice. Die
    Fassungsnummer steht im Ordnernamen und ändert sich mit jedem Update —
    deshalb wird gesucht statt geraten.
    """
    if os.path.isdir(EIGENER_MOTOR):
        for eintrag in sorted(os.listdir(EIGENER_MOTOR), reverse=True):
            weg = os.path.join(EIGENER_MOTOR, eintrag, "program", "soffice")
            if os.access(weg, os.X_OK):
                return weg

    return shutil.which("soffice") or shutil.which("libreoffice")


def umwandeln(rohdaten, von, nach):
    """Gibt die umgewandelte Datei zurück — oder wirft eine Ausnahme.

    Die Arbeit macht LibreOffice selbst. Seine Filter für .docx und PDF sind
    das Ergebnis von Jahrzehnten; sie im eigenen Programm nachzubauen wäre
    aussichtslos. Also fragen wir es einfach.
    """
    if von not in FORMATE or nach not in FORMATE:
        raise ValueError("Dieses Format kenne ich nicht.")

    soffice = motor_finden()
    if not soffice:
        raise FileNotFoundError("LibreOffice ist nicht installiert.")

    with tempfile.TemporaryDirectory(prefix="lunivo-office-") as ordner:
        quelle = os.path.join(ordner, "dokument." + von)
        with open(quelle, "wb") as datei:
            datei.write(rohdaten)

        # Der Filter muss dastehen, sobald eine Webseite im Spiel ist.
        #
        # LibreOffice lädt eine HTML-Datei als „Writer/Web"-Dokument, und für
        # das kennt es von sich aus nur wenige Ausgabewege. Ohne ausdrücklichen
        # Filter meldet es bloß „no export filter" — und zwar auch dann, wenn
        # es das Format sehr wohl schreiben kann. Also wird es benannt.
        ziel = FILTER.get(nach, nach)
        if ziel != nach:
            ziel = nach + ":" + ziel

        lauf = subprocess.run(
            [soffice,
             "-env:UserInstallation=file://" + UMWANDEL_PROFIL,
             "--headless", "--norestore",
             "--convert-to", ziel, "--outdir", ordner, quelle],
            capture_output=True, encoding="utf-8", errors="replace",
            # Der erste Aufruf startet LibreOffice kalt — das dauert. Später
            # geht es in Sekunden.
            timeout=180)

        fertig = os.path.join(ordner, "dokument." + nach)
        if not os.path.isfile(fertig):
            hinweis = (lauf.stderr or lauf.stdout or "").strip().splitlines()
            raise RuntimeError(hinweis[-1] if hinweis else "Die Umwandlung ergab nichts.")

        if nach == "html":
            return bilder_einbetten(fertig, ordner)

        with open(fertig, "rb") as datei:
            return datei.read()


def bilder_einbetten(seite, ordner):
    """Bilder in die Webseite hineinschreiben, statt daneben zu legen.

    LibreOffice legt jedes Bild als eigene Datei neben die HTML-Datei und
    verweist darauf. Hier kommt aber nur die HTML-Datei an — die Bilder
    blieben im Papierkorb des Zwischenordners zurück, und im Dokument stünden
    leere Rahmen. Also wandern sie als Daten-Adresse in die Seite hinein.
    """
    with open(seite, "rb") as datei:
        text = datei.read().decode("utf-8", "replace")

    def ersetze(treffer):
        name = urllib.parse.unquote(treffer.group(2))
        weg = os.path.normpath(os.path.join(ordner, name))
        # Nur Dateien aus dem Zwischenordner — ein Verweis wie „../../etc"
        # hätte hier sonst Zugriff auf alles.
        if not weg.startswith(os.path.realpath(ordner) + os.sep) \
                and not weg.startswith(ordner + os.sep):
            return treffer.group(0)
        if not os.path.isfile(weg) or os.path.getsize(weg) > 12 * 1024 * 1024:
            return treffer.group(0)

        art = mimetypes.guess_type(weg)[0] or "image/png"
        with open(weg, "rb") as bild:
            daten = base64.b64encode(bild.read()).decode("ascii")
        return treffer.group(1) + "data:" + art + ";base64," + daten + treffer.group(3)

    # src="…" oder src='…', aber nichts, was schon eine Adresse ist
    text = re.sub(r'(src=")(?!data:|https?:)([^"]+)(")', ersetze, text)
    text = re.sub(r"(src=')(?!data:|https?:)([^']+)(')", ersetze, text)
    return text.encode("utf-8")


class Leise(http.server.SimpleHTTPRequestHandler):
    """Wie der eingebaute Server, nur ohne Zeile für jede Datei."""

    def log_message(self, format, *args):                   # noqa: A002
        pass

    def end_headers(self):
        """Nichts zwischenspeichern.

        Das Fenster ist kein Browser, der eine fremde Seite besucht — es zeigt
        die Dateien aus diesem Ordner. Werden sie geändert, muss die Änderung
        beim nächsten Start da sein. WebKit hielt sonst hartnäckig die alte
        Fassung fest: Der Ordner enthielt längst die Korrektur, im Fenster lief
        weiter der Fehler, und von außen sah beides gleich aus.
        """
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def translate_path(self, path):
        """Das Fenstersymbol liegt bei den anderen Symbolen, nicht bei der
        Oberfläche — es ist dasselbe Bild, das auch im Menü des Arbeitsplatzes
        steht. Ausgeliefert wird sonst nur der Oberflächen-Ordner; für diese
        eine Datei geht ein Weg daneben hinaus. Eine zweite Kopie im
        Oberflächen-Ordner wäre der einfachere Weg gewesen und ginge beim
        nächsten Wechsel des Logos schief: Dann stimmte eine von beiden nicht
        mehr, und niemand wüsste welche.
        """
        if path.split("?")[0] == "/icon.svg":
            return os.path.join(HIER, "symbole", "icon.svg")
        return super().translate_path(path)

    def do_GET(self):                                       # noqa: N802
        """Eine einzige Auskunft neben den Dateien: die Schriftliste.

        Sie ändert sich, wenn jemand eine Schrift nachinstalliert — deshalb
        wird sie bei jedem Start frisch geholt und nicht in eine Datei
        geschrieben, die dann veraltet.
        """
        # Die im Dialog gewählte Datei — und nur die, und nur einmal.
        if self.path.split("?")[0] == "/lesen":
            pfad = LESEZIEL["pfad"]
            LESEZIEL["pfad"] = None
            if not pfad or not os.path.isfile(pfad):
                self.fehler_melden(409, "Es wurde keine Datei gewählt.")
                return
            if os.path.getsize(pfad) > GROESSTE_DATEI:
                self.fehler_melden(413, "Die Datei ist zu groß.")
                return
            with open(pfad, "rb") as datei:
                ladung = datei.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(ladung)))
            self.end_headers()
            self.wfile.write(ladung)
            return

        # Die zuletzt benutzten Dateien — Namen und Ordner, keine ganzen Wege.
        if self.path.split("?")[0] == "/zuletzt":
            self.auskunft([{"name": os.path.basename(weg),
                            "ordner": os.path.dirname(weg)}
                           for weg in zuletzt_lesen()])
            return

        if self.path.split("?")[0] == "/teile":
            self.auskunft(teile_lesen())
            return

        if self.path.split("?")[0] == "/stimmen":
            ladung = json.dumps({
                "gut": piper_stimmen(),   # die natürlichen, beste zuerst
                "stimmen": stimmen_lesen(),
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(ladung)))
            self.end_headers()
            self.wfile.write(ladung)
            return

        if self.path.split("?")[0] == "/fenster":
            ladung = json.dumps(fenster_lesen()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(ladung)))
            self.end_headers()
            self.wfile.write(ladung)
            return

        if self.path.split("?")[0] == "/schriften.json":
            ladung = json.dumps(schriften_lesen()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(ladung)))
            self.end_headers()
            self.wfile.write(ladung)
            return
        super().do_GET()

    def do_POST(self):                                      # noqa: N802
        """Eine Datei hereinreichen, umgewandelt zurückbekommen.

        Nur von 127.0.0.1 erreichbar, und nur dieser eine Weg — es ist kein
        Dienst für andere, sondern die Verbindung zwischen dem Fenster und
        dem LibreOffice, das ohnehin auf diesem Rechner liegt.
        """
        adresse = urllib.parse.urlparse(self.path)

        # „Fenster → Neues Fenster": noch ein Fenster auf dasselbe Programm.
        # Der zweite Aufruf sieht, dass hier schon jemand liefert, und startet
        # keinen zweiten Server — er hängt sich an diesen.
        if adresse.path == "/neues-fenster":
            try:
                subprocess.Popen([sys.executable, os.path.join(HIER, "start.py")],
                                 start_new_session=True)
            except OSError as grund:
                self.fehler_melden(500, str(grund))
                return
            self.send_response(204)
            self.end_headers()
            return

        # „Fenster → Fenster wechseln": das gewählte nach vorn holen.
        if adresse.path == "/fenster-zeigen":
            kennung = (urllib.parse.parse_qs(adresse.query).get("kennung") or [""])[0]
            # Nur was wie eine Fensterkennung aussieht — sie geht an ein
            # anderes Programm weiter.
            if not re.fullmatch(r"0x[0-9a-fA-F]{4,12}", kennung):
                self.fehler_melden(400, "Das ist keine Fensterkennung.")
                return
            try:
                subprocess.run(["wmctrl", "-i", "-a", kennung], timeout=10)
            except (OSError, subprocess.SubprocessError) as grund:
                self.fehler_melden(500, str(grund))
                return
            self.send_response(204)
            self.end_headers()
            return

        # „Hilfe → Handbuch": im richtigen Browser, nicht in diesem Fenster.
        # Hier gehört das Dokument hin, nicht eine Webseite.
        if adresse.path == "/handbuch":
            try:
                subprocess.Popen(["xdg-open", HANDBUCH], start_new_session=True)
            except OSError as grund:
                self.fehler_melden(500, str(grund))
                return
            self.send_response(204)
            self.end_headers()
            return

        # „Gründlich prüfen": die zweite Meinung von LanguageTool.
        if adresse.path == "/languagetool":
            laenge = int(self.headers.get("Content-Length") or 0)
            text = self.rfile.read(laenge).decode("utf-8", "replace") if laenge else ""
            try:
                self.auskunft(languagetool_fragen(text))
            except FileNotFoundError as grund:
                self.fehler_melden(501, str(grund))
            except Exception as grund:                      # noqa: BLE001
                self.fehler_melden(500, str(grund))
            return

        # „Vorlesen": Der Sprachdienst des Arbeitsplatzes spricht.
        if adresse.path == "/vorlesen":
            wahl = urllib.parse.parse_qs(adresse.query)
            stimme = (wahl.get("stimme") or [""])[0]
            tempo = (wahl.get("tempo") or ["0"])[0]

            laenge = int(self.headers.get("Content-Length") or 0)
            text = self.rfile.read(laenge).decode("utf-8", "replace") if laenge else ""
            try:
                lief = vorlesen(text, stimme, tempo)
            except FileNotFoundError as grund:
                self.fehler_melden(501, str(grund))
                return
            except Exception as grund:                      # noqa: BLE001
                self.fehler_melden(500, str(grund))
                return
            self.auskunft({"spricht": lief})
            return

        if adresse.path == "/ordner-waehlen":
            self.auskunft({"ordner": ordner_waehlen()})
            return

        if adresse.path == "/vorlesen-stopp":
            vorlesen_beenden()
            self.auskunft({"spricht": False})
            return

        # „Bildschirmfoto": Das kann nur der Rechner, nicht die Seite.
        if adresse.path == "/bildschirmfoto":
            was = (urllib.parse.parse_qs(adresse.query).get("was") or ["ganz"])[0]
            try:
                bild = bildschirmfoto(was)
            except FileNotFoundError as grund:
                self.fehler_melden(501, str(grund))
                return
            except Exception as grund:                      # noqa: BLE001
                self.fehler_melden(500, str(grund))
                return
            if not bild:
                self.fehler_melden(400, "Es wurde nichts aufgenommen.")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(bild)))
            self.end_headers()
            self.wfile.write(bild)
            return

        # „Fenster anordnen": nebeneinander, untereinander, gekachelt.
        if adresse.path == "/fenster-ordnen":
            wie = (urllib.parse.parse_qs(adresse.query).get("wie") or ["nebeneinander"])[0]
            try:
                zahl = fenster_ordnen(wie)
            except Exception as grund:                      # noqa: BLE001
                self.fehler_melden(500, str(grund))
                return
            self.auskunft({"zahl": zahl})
            return

        # „Öffnen": der Dateibrowser des Systems, mit Filtern.
        if adresse.path == "/oeffnen-dialog":
            nur = (urllib.parse.parse_qs(adresse.query).get("nur") or [""])[0]
            ergebnis = dialog_oeffnen(nur)
            pfad = ergebnis.get("pfad")
            if not pfad or not os.path.isfile(pfad):
                LESEZIEL["pfad"] = None
                self.auskunft({"abgebrochen": True})
                return
            LESEZIEL["pfad"] = pfad
            LETZTER_ORDNER["weg"] = os.path.dirname(pfad)
            zuletzt_merken(pfad)
            self.auskunft({"pfad": pfad, "name": os.path.basename(pfad)})
            return

        # Einen Eintrag aus der Liste öffnen. Herein kommt eine Nummer, nie
        # ein Pfad — und die Nummer gilt nur, solange sie in die Liste passt.
        if adresse.path == "/zuletzt-oeffnen":
            liste = zuletzt_lesen()
            try:
                nummer = int((urllib.parse.parse_qs(adresse.query)
                              .get("nr") or ["-1"])[0])
            except ValueError:
                nummer = -1
            if nummer < 0 or nummer >= len(liste):
                LESEZIEL["pfad"] = None
                self.fehler_melden(404, "Die Datei steht nicht mehr in der Liste.")
                return
            pfad = liste[nummer]
            LESEZIEL["pfad"] = pfad
            LETZTER_ORDNER["weg"] = os.path.dirname(pfad)
            self.auskunft({"pfad": pfad, "name": os.path.basename(pfad)})
            return

        # „Speichern unter": Der Dialog fragt nach Ort und Format.
        if adresse.path == "/speichern-dialog":
            wahl = urllib.parse.parse_qs(adresse.query)
            name = (wahl.get("name") or ["Unbenannt"])[0]
            endung = (wahl.get("format") or ["odt"])[0].lower()
            ergebnis = dialog_speichern(os.path.basename(name), endung)

            if not ergebnis.get("pfad"):
                SPEICHERZIEL["pfad"] = None
                self.auskunft({"abgebrochen": True})
                return

            SPEICHERZIEL["pfad"] = ergebnis["pfad"]
            LETZTER_ORDNER["weg"] = os.path.dirname(ergebnis["pfad"])
            self.auskunft({"pfad": ergebnis["pfad"], "endung": ergebnis["endung"]})
            return

        # Und danach die fertige Datei dorthin schreiben.
        if adresse.path == "/schreiben":
            ziel = SPEICHERZIEL["pfad"]
            SPEICHERZIEL["pfad"] = None          # gilt nur dieses eine Mal
            if not ziel:
                self.fehler_melden(409, "Es wurde kein Ziel gewählt.")
                return

            laenge = int(self.headers.get("Content-Length") or 0)
            if laenge <= 0 or laenge > GROESSTE_DATEI:
                self.fehler_melden(413, "Die Datei ist zu groß oder leer.")
                return
            try:
                with open(ziel, "wb") as datei:
                    datei.write(self.rfile.read(laenge))
            except OSError as grund:
                self.fehler_melden(500, str(grund))
                return
            zuletzt_merken(ziel)
            self.auskunft({"pfad": ziel})
            return

        if adresse.path != "/umwandeln":
            self.send_error(404)
            return

        wahl = urllib.parse.parse_qs(adresse.query)
        von = (wahl.get("von") or ["odt"])[0].lower()
        nach = (wahl.get("nach") or ["pdf"])[0].lower()

        laenge = int(self.headers.get("Content-Length") or 0)
        if laenge <= 0 or laenge > GROESSTE_DATEI:
            self.fehler_melden(413, "Die Datei ist zu groß oder leer.")
            return

        try:
            ergebnis = umwandeln(self.rfile.read(laenge), von, nach)
        except FileNotFoundError as grund:
            self.fehler_melden(501, str(grund))
            return
        except subprocess.TimeoutExpired:
            self.fehler_melden(504, "LibreOffice hat zu lange gebraucht.")
            return
        except Exception as grund:                          # noqa: BLE001
            self.fehler_melden(400, str(grund))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(ergebnis)))
        self.end_headers()
        self.wfile.write(ergebnis)

    def auskunft(self, was):
        """Eine Antwort als JSON — für die Wege, die etwas zurückgeben."""
        ladung = json.dumps(was).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(ladung)))
        self.end_headers()
        self.wfile.write(ladung)

    def fehler_melden(self, nummer, satz):
        """Der Grund im Klartext, damit das Fenster ihn anzeigen kann —
        eine bloße Nummer sagt dem Menschen davor nichts."""
        ladung = json.dumps({"fehler": satz}).encode("utf-8")
        self.send_response(nummer)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(ladung)))
        self.end_headers()
        self.wfile.write(ladung)


def server_starten():
    """Gibt den Port zurück, auf dem geliefert wird.

    Belegt wird gleich, nicht erst nachgefragt. Vorher stand hier ein Blick,
    ob schon jemand auf dem Port antwortet — und danach wurde entschieden.
    Zwischen Blick und Entscheidung liegt aber ein Augenblick, und in dem kann
    das andere Fenster zugehen: Dann glaubte dieses hier, es werde beliefert,
    und stand am Ende ohne Server da. Die Schriftliste blieb leer, Word und
    PDF gingen nicht, und neu laden ließ sich die Seite auch nicht.

    Ein Versuch, den Port zu belegen, beantwortet beide Fragen auf einmal:
    Klappt es, liefern wir selbst. Klappt es nicht, liefert wirklich jemand.

    Ein einziger Versuch reicht dafür aber nicht. Wer das Fenster schließt und
    gleich wieder öffnet, trifft den Port noch belegt — vom eigenen, gerade
    sterbenden Vorgänger. Dieses Fenster hielte ihn für ein anderes, das
    liefert, und bliebe leer zurück. Deshalb ein paar Anläufe über zwei
    Sekunden: Wer wirklich liefert, ist auch dann noch da.
    """
    aufgabe = functools.partial(Leise, directory=OBERFLAECHE)
    for _versuch in range(10):
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), aufgabe)
        except OSError:
            time.sleep(0.2)
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return PORT

    return PORT                                         # ein anderes Fenster liefert


def speichern_fragen(_umgebung, ladung):
    """„Speichern" im Menü schickt die Datei an den Rechner. In einem
    Browser landet sie im Download-Ordner; ein eigenes Fenster hat keinen.
    Also fragen wir, wohin — wie jedes Schreibprogramm es tut."""

    def ziel_waehlen(_ladung, vorschlag):
        dialog = Gtk.FileChooserDialog(
            title="Speichern unter", action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons("Abbrechen", Gtk.ResponseType.CANCEL,
                           "Speichern", Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(vorschlag or "Unbenannt.odt")
        dialog.set_current_folder(os.path.expanduser("~"))

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            ladung.set_destination("file://" + dialog.get_filename())
        else:
            ladung.cancel()
        dialog.destroy()
        return True

    ladung.connect("decide-destination", ziel_waehlen)


def main():
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
    fenster.add(ansicht)
    fenster.connect("destroy", Gtk.main_quit)

    ansicht.load_uri("http://localhost:%d/" % port)
    fenster.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
