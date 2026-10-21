"""Die mitgelieferten Gerüste (Brief, Bewerbung, Lebenslauf …) und eigene Vorlagen.

Ein Gerüst ist eine Liste von Zeilen (aus resources/vorlagenmuster.json):
    «Wort»  Lücke         ''  Leerzeile        '!Text'  fett        '#Text'  Titel
    '>Text' rechtsbündig  '@absender' / '@absender2' / '@ortdatum' / '@name' / @mail  aus den Benutzerdaten
Zeilen ohne Leerzeile dazwischen werden zu einem Absatz mit Zeilenumbrüchen.
"""
from __future__ import annotations

import json
import os
from lunivo_writer.core import paths
import re

from PySide6.QtGui import QBrush, QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtCore import Qt

LUECKE = re.compile("«[^«»]*»")
LUECKE_FARBE = "#fff3bf"


def muster() -> list[dict]:
    pfad = os.path.join(paths.RESSOURCEN, "vorlagenmuster.json")
    with open(pfad, encoding="utf-8") as fh:
        return json.load(fh)


def _benutzer_zeilen(b: dict, mit_name: bool) -> list[str]:
    z = []
    if mit_name:
        z.append(b.get("name") or "«Dein Name»")
    z.append(b.get("strasse") or "«Straße und Hausnummer»")
    z.append(b.get("plz_ort") or "«PLZ und Ort»")
    return z


def _ersetze(text: str, b: dict) -> str:
    return text.replace("@mail", b.get("mail") or "«E-Mail»").replace("@name", b.get("name") or "«Dein Name»")


def aufbauen(ed, zeilen: list[str], benutzer: dict, heute: str) -> None:
    """Schreibt das Gerüst in den (leeren) Editor und hebt die Lücken hervor."""
    doc: QTextDocument = ed.document()
    c = QTextCursor(doc)
    c.beginEditBlock()
    # Absätze bilden
    absaetze: list[tuple[str, list[str]]] = []          # (Art, Zeilen)
    puffer: list[str] = []

    def leeren():
        nonlocal puffer
        if puffer:
            absaetze.append(("text", puffer)); puffer = []
    for z in zeilen:
        if z == "":
            leeren(); absaetze.append(("leer", []))
        elif z[0] in "!#>":
            leeren(); absaetze.append(({"!": "fett", "#": "titel", ">": "rechts"}[z[0]], [_ersetze(z[1:], benutzer)]))
        elif z == "@absender":
            leeren(); absaetze.append(("text", _benutzer_zeilen(benutzer, True)))
        elif z == "@absender2":
            puffer.extend(_benutzer_zeilen(benutzer, False))
        elif z == "@ortdatum":
            leeren(); absaetze.append(("rechts", [f"{benutzer.get('ort') or '«Ort»'}, {heute}"]))
        elif z == "@name":
            leeren(); absaetze.append(("text", [benutzer.get("name") or "«Dein Name»"]))
        else:
            puffer.append(_ersetze(z, benutzer))
    leeren()
    erster = True
    for art, zs in absaetze:
        bf = QTextBlockFormat()
        cf = QTextCharFormat()
        if art == "rechts":
            bf.setAlignment(Qt.AlignRight)
        if art == "fett":
            cf.setFontWeight(QFont.Bold)
        if art == "titel":
            cf.setFontWeight(QFont.Bold); cf.setFontPointSize(20); bf.setBottomMargin(6)
        if erster:
            c.setBlockFormat(bf); c.setBlockCharFormat(cf); erster = False
        else:
            c.insertBlock(bf, cf)
        text = " ".join(zs)
        pos = 0
        for m in LUECKE.finditer(text):
            c.insertText(text[pos:m.start()], cf)
            lf = QTextCharFormat(cf); lf.setBackground(QBrush(QColor(LUECKE_FARBE)))
            c.insertText(m.group(0), lf)
            pos = m.end()
        c.insertText(text[pos:], cf)
    c.endEditBlock()
    c.setPosition(0)
    ed.setTextCursor(c)
    ed.document().setModified(True)


def naechste_luecke(doc: QTextDocument, von: int) -> tuple[int, int] | None:
    text = doc.toPlainText()
    m = LUECKE.search(text, von) or LUECKE.search(text, 0)
    return (m.start(), m.end()) if m else None


def luecken_entfernen(doc: QTextDocument) -> None:
    """Für den Druck: Lücken « … » verschwinden samt Klammern."""
    text = doc.toPlainText()
    for m in reversed(list(LUECKE.finditer(text))):
        c = QTextCursor(doc)
        c.setPosition(m.start()); c.setPosition(m.end(), QTextCursor.KeepAnchor)
        c.removeSelectedText()


# ---- eigene Vorlagen -------------------------------------------------------------------------------------------
ENDUNGEN = (".docx", ".dotx", ".odt", ".ott", ".txt")


def vorlagenordner(settings) -> str:
    return settings.get("vorlagen/ordner", "") or os.path.join(os.path.expanduser("~"), "Vorlagen")


def rubriken(ordner: str) -> tuple[dict[str, list[str]], list[str]]:
    """Der Vorlagenordner nach Rubriken: jeder Unterordner ist eine Rubrik (Name → Dateien); lose Dateien liegen im Ordner selbst."""
    rub: dict[str, list[str]] = {}
    try:
        for f in sorted(os.listdir(ordner)):
            pfad = os.path.join(ordner, f)
            if os.path.isdir(pfad) and not f.startswith("."):
                rub[f] = eigene_vorlagen(pfad)
    except OSError:
        pass
    return rub, eigene_vorlagen(ordner)


def eigene_vorlagen(ordner: str) -> list[str]:
    try:
        return sorted(os.path.join(ordner, f) for f in os.listdir(ordner) if f.lower().endswith(ENDUNGEN))
    except OSError:
        return []
