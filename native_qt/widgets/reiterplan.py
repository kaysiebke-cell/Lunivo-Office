"""Die Reiterleiste nach der Struktur „LUNIVO WRITER“ (Datei, Start, Einfügen, Seitenlayout, Verweise,
Überprüfen, KI, Ansicht + kontextabhängige Register).

Start, Einfügen, Seitenlayout, Verweise (= altes „Referenzen“), Überprüfen und Ansicht kommen unverändert
aus dem alten Register (register.json). Datei, KI und die Kontext-Register sind hier beschrieben.
Die alten Gruppen des Reiters „Schreibhilfe“ stehen in der rechten Seitenleiste (Bereich „Schreibhilfe“);
„Sendungen“ ist in der Struktur nicht vorgesehen und bleibt in register.json erhalten.
"""
from __future__ import annotations


def _k(symbol, name, tun=None, gross=False, **kw):
    e = {"symbol": symbol, "name": name, "gross": gross}
    if tun:
        e["tun"] = tun
    e.update(kw)
    return e


DATEI = {"name": "Datei", "gruppen": [
    {"name": "Neu", "knoepfe": [_k("neu", "Leeres Dokument", "neu", True),
                                _k("vorlage", "Aus Vorlage erstellen", "neuAusVorlage"),
                                _k("lupe", "Vorlagen durchsuchen", "vorlagenDurchsuchen")]},
    {"name": "Öffnen", "knoepfe": [_k("oeffnen", "Öffnen", "oeffnen", True),
                                   _k("zuletzt", "Zuletzt verwendete Dokumente", klappe="zuletzt")]},
    {"name": "Speichern", "knoepfe": [_k("speichern", "Speichern", "speichern", True),
                                      _k("speichern", "Speichern unter", "speichernUnter"),
                                      _k("kopie", "Kopie speichern", "kopieSpeichern")]},
    {"name": "Exportieren", "knoepfe": [_k("pdf", "Als PDF exportieren", "speichernPdf", True),
                                        _k("ausdatei", "Als DOCX exportieren", "exportierenDocx"),
                                        _k("ausdatei", "Als DOC exportieren (optional)", "exportierenDoc"),
                                        _k("//", "x"),
                                        _k("ausdatei", "Als RTF exportieren", "exportierenRtf"),
                                        _k("notiz", "Als TXT exportieren", "exportierenTxt"),
                                        _k("buch", "Als ODT exportieren", "exportierenOdt")]},
    {"name": "Drucken", "knoepfe": [_k("drucken", "Drucken", "drucken", True),
                                    _k("vorschau", "Druckvorschau", "vorschau"),
                                    _k("drucker2", "Drucker auswählen", "druckerWaehlen"),
                                    _k("//", "x"),
                                    _k("abschnitt", "Seitenbereich", "druckerWaehlen"),
                                    _k("einstellungen", "Druckeinstellungen", "druckerWaehlen")]},
    {"name": "Dokument", "knoepfe": [_k("inhalt", "Dokumentinformationen", "eigenschaften", True),
                                     _k("sperren", "Dokument schützen", "dokumentSchuetzen"),
                                     _k("verknuepft", "Dokument teilen (optional)", "dokumentTeilen"),
                                     _k("//", "x"),
                                     _k("buch", "Mit WPS Writer öffnen", "mitWpsOeffnen"),
                                     _k("buch", "Mit LibreOffice öffnen", "mitLibreOfficeOeffnen")]},
    {"name": "Programm", "knoepfe": [_k("optionen", "Optionen / Einstellungen", "w.optionenOeffnen", True),
                                     _k("schliessen", "Schließen", "schliessen")]},
]}

KI = {"name": "KI", "gruppen": [
    {"name": "KI-Schreibwerkzeuge", "knoepfe": [_k("ki", "Text entwerfen", "kiEntwerfen", True),
                                                _k("zusammenfassen", "Text umformulieren", "kiUmformulieren"),
                                                _k("zusammenfassen", "Text zusammenfassen", "kiZusammenfassen"),
                                                _k("uebersetzen", "Text übersetzen", "w.kiUebersetzen")]},
    {"name": "Korrektur", "knoepfe": [_k("assistent", "KI-Korrektur", "kiKorrektur", True),
                                      _k("vorschlag", "Verbesserungsvorschläge", "kiVorschlaege", True)]},
    {"name": "Seitenleiste", "knoepfe": [_k("tafel", "Schreibhilfe-Seitenleiste", "tafelZeigen", True),
                                         _k("chat", "KI-Chat", "w.chatUmschalten", True)]},
    {"name": "Einrichten", "knoepfe": [_k("assistent", "Eigenen Assistenten erstellen", "w.assistentErstellen"),
                                       _k("kombination", "Eigenen Anbieter hinzufügen", "w.eigenenAnbieterHinzufuegen"),
                                       _k("zahnrad", "KI-Konfiguration", "w.kiKonfiguration")]},
]}

TABELLENTOOLS = {"name": "Tabellentools", "kontext": "tabelle", "gruppen": [
    {"name": "Entwurf: Rahmen und Farbe", "knoepfe": [
        _k("rahmen", "Rahmenlinien ein/aus", "tabelleRahmen", True, haken=True),
        _k("toenung", "Zellenschattierung", klappe="tabelleSchattierung", gross=True)]},
    {"name": "Layout: Zeilen und Spalten", "knoepfe": [
        _k("kanteOben", "Zeile oberhalb einfügen", "tabelleZeileOben"),
        _k("kanteUnten", "Zeile unterhalb einfügen", "tabelleZeileUnten"),
        _k("kanteLinks", "Spalte links einfügen", "tabelleSpalteLinks"),
        _k("kanteRechts", "Spalte rechts einfügen", "tabelleSpalteRechts"),
        _k("//", "x"),
        _k("kanteKeine", "Zeile löschen", "tabelleZeileLoeschen"),
        _k("kanteKeine", "Spalte löschen", "tabelleSpalteLoeschen"),
        _k("kanteKeine", "Tabelle löschen", "tabelleLoeschen")]},
    {"name": "Zellen", "knoepfe": [
        _k("kanteAlle", "Zellen verbinden", "tabelleVerbinden"),
        _k("kanteInnen", "Zelle teilen", "tabelleTeilen"),
        _k("sortieren", "Tabelle sortieren", "tabelleSortieren")]},
    {"name": "Ausrichtung", "knoepfe": [
        _k("links", "Oben ausrichten", "zelleOben"),
        _k("mitte", "Mittig ausrichten", "zelleMitte"),
        _k("rechts", "Unten ausrichten", "zelleUnten")]},
]}

BILDTOOLS = {"name": "Bildtools", "kontext": "bild", "gruppen": [
    {"name": "Format: Größe", "knoepfe": [
        _k("bild", "Größe und Seitenverhältnis …", "bildGroesse", True),
        _k("einpassen", "Auf Seitenbreite", "bildBreite"),
        _k("bild", "Originalgröße", "bildOriginal")]},
    {"name": "Beschreibung", "knoepfe": [_k("notiz", "Alternativtext …", "bildAltText", True)]},
    {"name": "Bearbeiten", "knoepfe": [_k("kanteKeine", "Bild entfernen", "bildEntfernen"),
                                       _k("bild", "Zuschneiden", "bildZuschneiden"),
                                       _k("farbe", "Helligkeit / Kontrast / Farbe", "bildFarbe"),
                                       _k("textflussumbruch", "Textumbruch / Position", "anordnen")]},
]}

FORMTOOLS = {"name": "Form- und WordArt-Tools", "kontext": "form", "gruppen": [
    {"name": "Format", "knoepfe": [_k("stift", "Formvorlagen", "formVorlagen", True),
                                    _k("toenung", "Formfüllung", "formFuellung"),
                                    _k("linie", "Formkontur", "formKontur"),
                                    _k("anordnen", "Anordnen / Gruppieren", "gruppieren")]}]}

KOPFFUSS = {"name": "Kopf- und Fußzeilentools", "kontext": "kopffuss", "gruppen": [
    {"name": "Entwurf", "knoepfe": [_k("kopfz", "Kopfzeile bearbeiten", "kopfFussZeigen", True),
                                    _k("fussz", "Fußzeile bearbeiten", "fusszeileBearbeiten", True),
                                    _k("seitenzahl", "Seitenzahl einfügen", "seitenzahlKlappe"),
                                    _k("kopffuss", "Erste Seite anders", "ersteSeiteAnders"),
                                    _k("kopffuss", "Gerade/ungerade Seiten unterschiedlich", "geradeUngerade"),
                                    _k("schliessen", "Kopf- und Fußzeile schließen", "kopfFussSchliessen")]}]}


def plan(register: dict) -> list[dict]:
    """Die Reiter in der Reihenfolge der Struktur; Kontext-Register stehen am Ende (zunächst verborgen)."""
    nach = {t["name"]: t for t in register["register"]}
    verweise = dict(nach["Referenzen"], name="Verweise")
    reiter = [DATEI, nach["Start"], nach["Einfügen"], nach["Seitenlayout"], verweise, nach["Überprüfen"], KI,
              nach["Ansicht"]]
    return reiter + [TABELLENTOOLS, BILDTOOLS, FORMTOOLS, KOPFFUSS]


def schreibhilfe_gruppen(register: dict) -> list[dict]:
    """Die Gruppen des alten Reiters „Schreibhilfe“ ohne KI — sie stehen in der Seitenleiste."""
    s = next(t for t in register["register"] if t["name"] == "Schreibhilfe")
    return [g for g in s["gruppen"] if g["name"] != "KI"]
