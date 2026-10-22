"""Alle Funktionen der Schreibhilfe an einer Stelle: Wo sie in der Seitenleiste („Werkbank“) und im Band stehen und welcher Befehl dahinter hängt.

Band (Reiter Schreibhilfe) und Seitenleiste lesen denselben Katalog; eine Funktion wird hier einmal beschrieben und erscheint überall, wo sie hingehört.
Art: „aktion“ (ein Klick tut etwas oder öffnet ein Fenster), „schalter“ (an/aus, zeigt den echten Zustand), „menue“ (öffnet ein Menü)."""
from __future__ import annotations

from dataclasses import dataclass

REITER = ("Prüfen", "Lesen", "Schreiben", "KI")


@dataclass(frozen=True)
class Funktion:
    name: str
    symbol: str
    tun: str = ""                  # Befehl (siehe core/commands.py)
    art: str = "aktion"
    kuerzel: str = ""              # Tastenkürzel, wie es in Knopf und Zeile steht
    reiter: str = ""               # Reiter der Seitenleiste ("" = nur im Band)
    gruppe: str = ""               # Gruppe im Band ("" = nur in der Seitenleiste)
    klappe: str = ""               # Menü am Knopf (Band) bzw. an der Zeile (Seitenleiste)
    gross: bool = False            # großer Knopf im Band
    hinweis: str = ""              # eine Zeile unter dem Namen in der Seitenleiste


KATALOG: tuple[Funktion, ...] = (
    # ---- Prüfen (die Funde stehen darüber; hier die Wege dahin)
    Funktion("Prüfen", "haken", "w.pruefen", kuerzel="F7", reiter="Prüfen", hinweis="Den ganzen Text prüfen"),
    Funktion("Gründlich prüfen", "gruendlich", "gruendlichPruefen", reiter="Prüfen", hinweis="Auch die Grammatik (LanguageTool)"),
    Funktion("Barrierefreiheit prüfen", "barrierefrei", "barrierefrei", reiter="Prüfen", hinweis="Bilder, Überschriften, Tabellen, Sprache"),
    Funktion("Welche Hilfe wann", "handbuch", "welcheHilfe", kuerzel="F6", reiter="Prüfen", hinweis="Die Stufen der Schreibhilfe erklärt"),
    # ---- Lesen
    Funktion("Lesehilfe …", "brille", "lesehilfe", reiter="Lesen", gruppe="Lesen", gross=True, hinweis="Papierton, Abstände, Zeilenluft, Fokus"),
    Funktion("Zeilenfokus", "zeile", "zeilenfokus", "schalter", reiter="Lesen", gruppe="Lesen", hinweis="Die Zeile, in der Sie schreiben, hervorheben"),
    Funktion("Lesemodus", "buch", "lesemodus", "schalter", "Strg+Umschalt+L", reiter="Lesen", gruppe="Lesen", hinweis="Nur lesen, nichts ändern"),
    Funktion("Silben farbig", "farbe", "silbenfarben", "schalter", reiter="Lesen", gruppe="Lesen", klappe="silbenMenue", hinweis="Silben abwechselnd gefärbt"),
    Funktion("Silben einstellen …", "zahnrad", "silbenEinstellen", reiter="Lesen"),
    Funktion("Vorlesen", "vorlesen", "vorlesen", kuerzel="F4", reiter="Lesen", hinweis="Den Text oder die Markierung hören"),
    Funktion("Ab hier vorlesen", "vorlesen", "vorlesenAbSatz", reiter="Lesen"),
    Funktion("Vorlesen anhalten", "halt", "vorlesenStopp", reiter="Lesen"),
    Funktion("Stimme und Tempo …", "stimme", "stimmeWaehlen", reiter="Lesen"),
    # ---- Schreiben
    Funktion("Wellenlinien", "wellen", "wellen", "schalter", reiter="Schreiben", gruppe="Beim Schreiben", hinweis="Rote Linien unter unbekannten Wörtern"),
    Funktion("Wortvorhersage", "Vorhersage", "vorhersage", "schalter", reiter="Schreiben", gruppe="Beim Schreiben", hinweis="Wörter ab drei Buchstaben vorschlagen"),
    Funktion("AutoKorrektur", "autokorr", "autokorrektur", "schalter", reiter="Schreiben", gruppe="Beim Schreiben", hinweis="Das Offensichtliche beim Tippen bessern"),
    Funktion("Textbausteine …", "baustein", "textbausteine", kuerzel="F3", reiter="Schreiben", hinweis="Briefe und Absätze fertig einfügen"),
    Funktion("Thesaurus", "woerterbuch", "thesaurus", reiter="Schreiben", gruppe="Sprache", hinweis="Ein anderes Wort für das markierte"),
    Funktion("Silbentrennung", "silben", "silbentrennung", "schalter", reiter="Schreiben", gruppe="Sprache", gross=True, klappe="silbenTrennungMenue",
             hinweis="Trennstriche in Druck, PDF und Vorschau"),
    Funktion("Sprache", "sprache", "w.kiSprache", reiter="Schreiben", gruppe="Sprache", hinweis="Prüfsprache und Übersetzungssprache"),
    Funktion("Korrektursprache …", "sprache", "pruefsprache", reiter="Schreiben"),
    # ---- KI
    Funktion("KI-Korrektur", "assistent", "kiKorrektur", kuerzel="F8", reiter="KI", hinweis="Ton und Verständlichkeit prüfen lassen"),
    Funktion("Verbesserungsvorschläge", "vorschlag", "kiVorschlaege", reiter="KI", hinweis="Sätze, die sich leichter lesen ließen"),
    Funktion("Übersetzen", "uebersetzen", "w.kiUebersetzen", reiter="KI", gruppe="Sprache", klappe="uebersetzenMenue",
             hinweis="Markierung ersetzen — ohne Markierung die Übersetzung zeigen"),
    Funktion("Übersetzung zeigen", "uebersetzen", "w.kiUebersetzenZeigen", reiter="KI", hinweis="In Schreibhilfe und Chat, der Text bleibt"),
    Funktion("Text entwerfen", "ki", "kiEntwerfen", reiter="KI", gruppe="KI", hinweis="Im KI-Chat einen Text schreiben lassen"),
    Funktion("Text umformulieren", "stift", "kiUmformulieren", reiter="KI", gruppe="KI", hinweis="Markierung oder ganzen Text anders sagen"),
    Funktion("Text zusammenfassen", "zusammenfassen", "kiZusammenfassen", reiter="KI", gruppe="KI", hinweis="Das Wichtigste in wenigen Sätzen"),
    Funktion("Text in Bild", "bild", "kiTextInBild", reiter="KI", gruppe="KI", hinweis="Aus der Markierung ein Bild erzeugen"),
    Funktion("KI-Chat", "chat", "w.chatUmschalten", reiter="KI", gruppe="KI", gross=True, hinweis="Fragen zum Text stellen"),
    Funktion("KI-Aktionen", "assistent", "", "menue", reiter="KI", gruppe="KI", klappe="assistenten", gross=True, hinweis="Deine Schnellen KI-Aktionen"),
    Funktion("KI-Einstellungen", "zahnrad", "w.kiEinstellungen", reiter="KI", gruppe="KI", gross=True, hinweis="Modelle, Sprache, MCP, Websuche"),
)


def fuer_reiter(reiter: str) -> list[Funktion]:
    return [f for f in KATALOG if f.reiter == reiter]


def fuer_gruppe(gruppe: str) -> list[Funktion]:
    return [f for f in KATALOG if f.gruppe == gruppe]
