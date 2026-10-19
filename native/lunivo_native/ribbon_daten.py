"""Das Register — Reiter und Gruppen des Bandes.

Eine Liste, kein Programm (wie oberflaeche/daten/register.js): Wer einen Knopf
hinzufügen will, schreibt eine Zeile.

    K(symbol, beschriftung, aktion, gross=False, haken=None, klappe=None, menue=None)

  aktion   Name eines Befehls (befehle/…) oder (Name, Argument)
  gross    großer Knopf oben in der Gruppe
  haken    Name eines Zustands (Fenster.zustand) → Knopf bleibt gedrückt
  klappe   Name einer Funktion, die unter dem Knopf eine Auswahl öffnet
  menue    feste Liste: (Beschriftung, Aktion[, Argument]) oder '-'

Besondere Einträge: ZEILE (neue Zeile im Gitter), FELDER (Schriftart + Größe),
KATALOG (Stile), RAENDER (Seitenrand-Auswahl)."""


class K:
    def __init__(self, symbol, name, aktion=None, gross=False, haken=None, klappe=None, menue=None, text=None):
        self.symbol, self.name, self.aktion = symbol, name, aktion
        self.gross, self.haken, self.klappe, self.menue, self.text = gross, haken, klappe, menue, text


ZEILE, FELDER, KATALOG, RAENDER = "//", "felder", "katalog", "raender"


def G(name, eintraege, mehr=None):
    return (name, eintraege, mehr)


SPEC = [
    ("Start", [
        G("Zwischenablage", [
            K("kleben", "Einfügen", "einfuegen", gross=True, klappe="einfuegen_klappe"),
            K("ohneformat", "Einfügen ohne Formatierung", "einfuegen_ohne"),
            K("schere", "Ausschneiden", "ausschneiden"),
            K("kopie", "Kopieren", "kopieren"),
            K("pinsel", "Format übertragen", "format_uebertragen"),
            K("wortextras", "Wort-Extras", None, klappe="wort_extras"),
        ]),
        G("Schriftart", [
            FELDER,
            K("groesserA", "Schrift vergrößern", "schrift_groesser"),
            K("kleinerA", "Schrift verkleinern", "schrift_kleiner"),
            K("radierer", "Formatierung löschen", "schlicht"),
            K("Aa", "Groß-/Kleinschreibung", None, klappe="schreibweise_klappe", text="Aa"),
            ZEILE,
            K(None, "Fett", "fett", haken="fett", text="F"),
            K(None, "Kursiv", "kursiv", haken="kursiv", text="K"),
            K(None, "Unterstrichen", "unter", haken="unter", text="U", klappe="unterstrich_klappe"),
            K("durchgestrichen", "Durchgestrichen", "durch", haken="durch"),
            K(None, "Hochgestellt", "hoch", haken="hoch", text="X²"),
            K(None, "Tiefgestellt", "tief", haken="tief", text="X₂"),
            K("umriss", "Zeichenumriss", "zeichenumriss", haken="umriss"),
            K("marker", "Hervorheben", "hervorheben_jetzt", klappe="hervorheben_klappe"),
            K("schriftfarbe", "Schriftfarbe", "schriftfarbe_jetzt", klappe="schriftfarbe_klappe"),
            K("eingeschlossen", "Texteffekte", None, klappe="effekt_klappe"),
        ], mehr="schrift_mehr"),
        G("Absatz", [
            K("punkte", "Aufzählung", "punkte", klappe="aufzaehlung_klappe", haken="punkte"),
            K("zahlen", "Nummerierung", "zahlen", klappe="nummerierung_klappe", haken="zahlen"),
            K("einzug", "Einzug & Listenebene", None, menue=[
                ("Einzug vergrößern", "einzug_mehr"),
                ("Einzug verringern", "einzug_weniger"),
                ("Genaues Maß…", "einzug_genau"),
                "-",
                ("Listenebene verringern", "ebene_tiefer"),
                ("Listenebene erhöhen", "ebene_hoeher"),
            ]),
            K("sortieren", "Sortieren", "sortieren"),
            K(None, "Steuerzeichen", "steuerzeichen", haken="steuerzeichen", text="¶"),
            ZEILE,
            K("links", "Linksbündig", "links", haken="al-links"),
            K("mitte", "Zentriert", "mitte", haken="al-center"),
            K("rechts", "Rechtsbündig", "rechts", haken="al-right"),
            K("block", "Blocksatz", "block", haken="al-justify"),
            K("verteilt", "Verteilt", "verteilt", haken="al-distribute"),
            K("abstand", "Zeilenabstand", None, klappe="zeilenabstand_klappe"),
            K("absatztoenung", "Absatzschattierung", None, klappe="absatz_schattierung"),
            K("absatzrahmen", "Absatzrahmen", None, klappe="absatz_rahmen"),
        ], mehr="einzug_genau"),
        G("Stile", KATALOG),
        G("Bearbeiten", [
            K("lupe", "Suchen oder ersetzen", None, gross=True, menue=[
                ("Suchen …", "suchen"), ("Ersetzen …", "ersetzen"), ("Gehe zu …", "gehe_zu")]),
            K("allesmark", "Alles auswählen", "alles_markieren"),
            K("objekte", "Objekte auswählen", "objekte_waehlen"),
        ]),
    ]),
    ("Einfügen", [
        G("Seiten", [
            K("deckblatt", "Deckblatt", "deckblatt", gross=True),
            K("leereseite", "Leere Seite", None, menue=[
                ("Hochformat", "leere_seite", False), ("Querformat", "leere_seite", True)]),
            K("umbruch", "Seitenumbruch", "seitenumbruch"),
        ]),
        G("Tabellen", [
            K("tabelle", "Tabelle einfügen", None, gross=True, klappe="tabelle_raster"),
            K("schnelltab", "Schnelltabelle", "schnelltabelle", klappe="schnelltabelle_klappe"),
            K("tabellenblatt", "Tabellenblatt", "tabellenblatt"),
            K("toenung", "Eigenschaften", "tabelle_eigenschaften"),
        ]),
        G("Illustrationen", [
            K("bild", "Bild", "bild", gross=True),
            K("stift", "Formen", None, gross=True, klappe="formen_galerie"),
            K("saeule", "Diagramm", "diagramm"),
            K("smartart", "SmartArt", "smartart"),
            K("wordart", "WordArt", "wordart"),
            ZEILE,
            K("stift", "Form mit eigener Farbe…", "zeichnen"),
            K("bildfoto", "Bildschirmfoto", "screenshot"),
            K("piktogramm", "Piktogramm", "piktogramm"),
        ]),
        G("Links", [
            K("kette", "Hyperlink", "hyperlink", gross=True),
            K("textmarke", "Lesezeichen / Textmarke", "textmarke"),
            K("querverweis", "Querverweis", "querverweis"),
        ]),
        G("Kopf- und Fußzeile", [
            K("kopffuss", "Kopf- und Fußzeile", "kopf_fuss_zeigen", gross=True, haken="kopffuss"),
            K("seitenzahl", "Seitenzahl", "seitenzahl", gross=True, klappe="seitenzahl_klappe"),
        ]),
        G("Text", [
            K("textrahmen", "Textfeld", "textfeld", gross=True),
            K("initiale", "Initial", "initiale"),
            K("datumuhrzeit", "Datum und Uhrzeit", "datum_uhrzeit", gross=True),
            K("ausdatei", "Text aus Datei", "text_aus_datei"),
        ]),
        G("Symbole", [
            K("omega", "Sonderzeichen", "sonderzeichen", gross=True),
            K("formel", "Gleichung", "formel"),
        ]),
    ]),
    ("Seitenlayout", [
        G("Designs", [
            K("toenung", "Designs", None, gross=True, klappe="designs"),
            K("farbe", "Farben", None, klappe="farbschema"),
            K(None, "Schriftarten", None, klappe="design_schriften", text="Aa"),
            K("texteffekt", "Effekte", None, klappe="design_effekte"),
        ]),
        G("Ränder", [K("raender", "Ränder", None, gross=True, klappe="raender_klappe")]),
        G("Seitenränder", RAENDER),
        G("Seite einrichten", [
            K("ausrichtung", "Ausrichtung", None, gross=True, menue=[
                ("Hochformat", "ausrichtung", "hoch"), ("Querformat", "ausrichtung", "quer")]),
            K("papiergroesse", "Papierformat", None, gross=True, klappe="papier_klappe"),
            K("spalten", "Spalten", None, menue=[
                ("Eins", "spalten_setzen", 1), ("Zwei", "spalten_setzen", 2),
                ("Drei", "spalten_setzen", 3), "-", ("Mehr Spalten…", "spalten_mehr")]),
            K("textrichtung", "Textrichtung", None, klappe="textrichtung_klappe"),
            K("umbruch", "Umbrüche", None, menue=[
                ("Seitenumbruch", "seitenumbruch"),
                ("Spaltenumbruch", "spaltenumbruch"),
                ("Textflussumbruch", "textflussumbruch"),
                "-",
                ("Abschnittsumbruch auf nächster Seite", "abschnittsumbruch", "NextPage"),
                ("Fortlaufender Abschnittsumbruch", "abschnittsumbruch", "Continuous"),
                ("Abschnittsumbruch (gerade Seite)", "abschnittsumbruch", "EvenPage"),
                ("Abschnittsumbruch auf ungerader Seite", "abschnittsumbruch", "OddPage")]),
            K("zeilennr", "Zeilennummern", None, klappe="zeilennummern_klappe"),
        ], mehr="seitenraender"),
        G("Absatz", [
            K("einzug", "Einzug", "einzug_genau", gross=True),
            K("abstand", "Absatzabstand", "absatzabstand"),
            K("trennung", "Silbentrennung", "silbentrennung", haken="silbentrennung"),
        ], mehr="einzug_genau"),
        G("Seitenhintergrund", [
            K("farbe", "Seitenfarbe", None, gross=True, klappe="seitenfarbe"),
            K("wasserzeichen", "Wasserzeichen", "wasserzeichen"),
            K("seitenrahmen", "Seitenrahmen", "seitenraender_rahmen"),
        ]),
        G("Anordnen", [
            K("anordnen", "Objektgröße", "anordnen", gross=True),
            K("ausrichten", "Ausrichten", None, klappe="objekt_ausrichten"),
            K("gruppieren", "Gruppieren", None, klappe="gruppieren"),
            K("objektdrehen", "Drehen", None, klappe="objekt_drehen"),
        ]),
    ]),
    ("Referenzen", [
        G("Inhaltsverzeichnis", [
            K("inhalt", "Inhaltsverzeichnis", "inhaltsverzeichnis", gross=True),
            K("haken", "Verzeichnisse aktualisieren", "verzeichnisse_aktualisieren"),
        ]),
        G("Fußnoten", [
            K("fussnote", "Fußnote", "fussnote", gross=True),
            K("endnote", "Endnote", "endnote", gross=True),
            K("vor", "Nächste Note", "note_weiter"),
            K("zurueck", "Vorige Note", "note_zurueck"),
            K("bereich", "Notenbereich", "noten_zeigen"),
        ]),
        G("Zitate und Literatur", [
            K("zitat", "Zitat einfügen", "zitat", gross=True),
            K("eintrag", "Neue Quelle", "quelle_neu"),
            K("anpassen", "Quellen verwalten", "quellen_verwalten"),
            K(None, "Zitierweise", "zitierweise", text="Stil"),
            K("inhalt", "Literaturverzeichnis", "literaturverzeichnis"),
        ]),
        G("Beschriftungen", [
            K("beschriftung", "Beschriftung", "beschriftung", gross=True),
            K("bild", "Abbildungsverzeichnis", "abbildungsverzeichnis"),
            K("querverweis", "Querverweis", "querverweis"),
        ]),
        G("Index", [
            K("eintrag", "Indexeintrag", "index_eintrag", gross=True),
            K("inhalt", "Stichwortverzeichnis", "stichwortverzeichnis"),
        ]),
    ]),
    ("Überprüfen", [
        G("Dokumentprüfung", [
            K("haken", "Prüfen", "pruefen", gross=True),
            K("gruendlich", "Gründlich prüfen", "gruendlich_pruefen", gross=True),
            K(None, "Rechtschreibung", "rechtschreibung", haken="rechtschreibung", text="Duden"),
            K("thesaurus", "Thesaurus", "thesaurus"),
            K("woerter", "Wörter zählen", "woerter_zaehlen"),
        ]),
        G("Sprache", [K("sprache", "Korrektursprache", "pruefsprache", gross=True)]),
        G("Barrierefreiheit", [K("barrierefrei", "Barrierefreiheit prüfen", "barrierefrei", gross=True)]),
        G("Kommentare", [
            K("notiz", "Neuer Kommentar", "kommentar", gross=True),
            K("vor", "Nächster Kommentar", "kommentar_weiter"),
            K("zurueck", "Voriger Kommentar", "kommentar_zurueck"),
            K("kommentarweg", "Kommentar löschen", "kommentar_weg"),
            K("kommentareweg", "Alle Kommentare löschen", "kommentare_alle_weg"),
        ]),
        G("Änderungen", [
            K("verfolgt", "Änderungen verfolgen", "verfolgen", gross=True, haken="verfolgen"),
            K("markup", "Markup anzeigen", "markup_umschalten", haken="markup"),
            K("bereich", "Überarbeitungsbereich", "ueberarbeitungsbereich"),
            K("annehmen", "Änderung annehmen", "aenderung_annehmen"),
            K("ablehnen", "Änderung ablehnen", "aenderung_ablehnen"),
            K("vor", "Nächste Änderung", "aenderung_weiter"),
            K("zurueck", "Vorige Änderung", "aenderung_zurueck"),
            K("alleAn", "Alle annehmen", "aenderungen_uebernehmen"),
            K("alleAb", "Alle verwerfen", "aenderungen_verwerfen"),
        ]),
        G("Schützen", [K("sperren", "Bearbeitung sperren", "bearbeitung_sperren", gross=True, haken="gesperrt")]),
    ]),
    ("Schreibhilfe", [
        G("Lesen", [
            K("brille", "Lesehilfe", "lesehilfe", gross=True),
            K("zeile", "Zeilenfokus", "zeilenfokus", haken="zeilenfokus"),
            K("buch", "Lesemodus", "lesemodus", haken="lesemodus"),
            K("groesserA", "Schrift zum Lesen", "schrift_zum_lesen"),
        ], mehr="lesehilfe"),
        G("Prüfen", [
            K("haken", "Dokumentprüfung", None, gross=True, menue=[
                ("Prüfen", "pruefen"), ("Gründlich prüfen", "gruendlich_pruefen"),
                "-", ("Welche Hilfe wann", "welche_hilfe")]),
        ]),
        G("Beim Schreiben", [
            K("wellen", "Rechtschreibprüfung", "rechtschreibung", haken="rechtschreibung",
              klappe="pruefung_klappe"),
            K(None, "Wortvorhersage", "vorhersage", haken="vorhersage", text="Vorhersage"),
            K("autokorr", "AutoKorrektur", "autokorrektur", haken="autokorrektur"),
        ]),
        G("Vorlesen", [
            K("vorlesen", "Vorlesen", None, gross=True, menue=[
                ("Vorlesen", "vorlesen"), ("Ab hier vorlesen", "vorlesen_ab_satz"),
                ("Anhalten", "vorlesen_stopp"), "-", ("Stimme und Tempo", "stimme_waehlen")]),
        ]),
        G("Sprache", [
            K("silben", "Silbentrennung", "silbentrennung", gross=True, haken="silbentrennung"),
            K("uebersetzen", "Übersetzen", "ki_uebersetzen"),
            K("woerterbuch", "Thesaurus", "thesaurus"),
            K("sprache", "Sprache und Prüfung", "optionen_sprache"),
        ], mehr="optionen_sprache"),
        G("Bausteine", [
            K("baustein", "Textbausteine", None, gross=True, menue=[
                ("Bausteine verwalten…", "textbausteine"),
                ("Schnellbaustein einfügen", "schnellbaustein")]),
        ]),
        G("KI", [
            K("chat", "KI-Chat", "chat_umschalten", gross=True),
            K("assistent", "Eigenen Assistenten erstellen", "assistent_erstellen", gross=True),
            K("assistent", "Eigenen Anbieter hinzufügen", "anbieter_hinzufuegen", gross=True),
            K("optionen", "KI-Konfiguration", "ki_konfiguration", gross=True),
        ]),
        G("Anzeigen", [K("tafel", "Seitenleiste Schreibhilfe", "tafel_zeigen", gross=True, haken="tafel")]),
    ]),
    ("Sendungen", [
        G("Erstellen", [
            K("kette", "Umschlag", "umschlag", gross=True),
            K("etiketten", "Etiketten", "etiketten", gross=True),
        ]),
        G("Seriendruck", [
            K("serie", "Seriendruck-Assistent", "seriendruck", gross=True),
            K("seriefeld", "Seriendruckfeld", "seriendruckfeld", gross=True),
            K("adressblock", "Adressblock", "adressblock"),
            K("eintrag", "Regeln", "seriendruckregel"),
        ]),
        G("Vorschau", [K("vorschau", "Ergebnisse anzeigen", "serien_vorschau", gross=True, haken="serienvorschau"),
                        K("haken", "Fertigstellen", "seriendruck_fertig", gross=True)]),
        G("Formular", [
            K("formfeld", "Textfeld", "form_textfeld", gross=True),
            K("kaestchen", "Kontrollkästchen", "form_kasten"),
            K("formknopf", "Schaltfläche", "form_knopf"),
        ]),
    ]),
    ("Ansicht", [
        G("Dokumentansichten", [
            K("blattansicht", "Drucklayout", "layout", gross=True),
            K("lesen", "Lesemodus", "lesemodus", gross=True, haken="lesemodus"),
            K("zweiblatt", "Zwei Seiten", "layout_doppelt"),
            K("fortlaufend", "Weblayout", "layout_web"),
            K("gliederung", "Gliederung", "gliederung"),
        ]),
        G("Anzeigen", [
            K("linealIcon", "Lineal", "lineal_zeigen", haken="lineal"),
            K("linealHochIcon", "Vertikales Lineal", "lineal_hoch_zeigen", haken="lineal_hoch"),
            K("netz", "Gitternetzlinien", "netzlinien", haken="netzlinien"),
            K("navigation", "Navigationsbereich", "navigation", haken="navigation"),
            K("ecken", "Textbegrenzungen", "marken_zeigen", haken="textbegrenzungen"),
        ]),
        G("Zoom", [
            K("lupe", "Vergrößern", "groesser", gross=True),
            K("kleinerLupe", "Verkleinern", "kleiner", gross=True),
            K(None, "100 %", "normal", text="100 %"),
            K("seitenbreite", "Seitenbreite", "zoom_breite"),
            K("eineSeite", "Eine Seite", "zoom_seite"),
            K(None, "Zoom", "zoom_stufe", text="%"),
        ], mehr="zoom_stufe"),
        G("Fenster", [
            K("neuesfenster", "Neues Fenster", "neues_fenster", gross=True),
            K("kacheln", "Anordnen", None, gross=True, menue=[
                ("Nebeneinander", "fenster_nebeneinander"),
                ("Untereinander", "fenster_untereinander"),
                ("Kacheln", "fenster_kacheln")]),
            K("fensterNeben", "Nebeneinander", "fenster_nebeneinander"),
            K("fensterUnter", "Untereinander", "fenster_untereinander"),
            K("kacheln", "Kacheln", "fenster_kacheln"),
            K("fensterliste", "Fensterliste", "fenster_liste"),
        ]),
        G("Helligkeit", [
            K("automatisch", "Wie das System", ("thema", "auto"), haken="thema-auto"),
            K("hell", "Immer hell", ("thema", "light"), haken="thema-hell"),
            K("dunkel", "Immer dunkel", ("thema", "dark"), haken="thema-dunkel"),
        ]),
        G("Oberfläche", [
            K("anpassen", "Register anpassen", "register_anpassen", gross=True),
            K("piktogramm", "Symbol austauschen", "symbol_tauschen"),
            K(None, "Benutzeroberfläche", "benutzeroberflaeche", text="Oberfläche"),
            K("menueleiste", "Menüleiste", "menueleiste_zeigen", haken="menueleiste"),
            K("leisten", "Symbolleisten", "leisten_zeigen", haken="leisten"),
            K("Zurück", "Vorlagen zurücksetzen", "vorlagen_zurueck"),
        ], mehr="register_anpassen"),
    ]),
]


# Werkzeug-Reiter: erscheinen nur, wenn sie etwas zu sagen haben (Name, Kontext, Gruppen)
WERKZEUGE = [
    ("Tabellenwerkzeuge", "tabelle", [
        G("Tabelle", [
            K("toenung", "Eigenschaften", "tabelle_eigenschaften", gross=True),
            K("sortieren", "Spalte sortieren", "tabelle_sortieren"),
            K("sperren", "Tabelle löschen", "tabelle_weg"),
        ]),
        G("Zeilen und Spalten", [
            K("tabelle", "Zeile darüber", "tabelle_zeile_oben", gross=True),
            K("tabelle", "Zeile darunter", "tabelle_zeile_unten", gross=True),
            K("spalte1", "Spalte links", "tabelle_spalte_links"),
            K("spalte2", "Spalte rechts", "tabelle_spalte_rechts"),
            K("kommentarweg", "Zeile löschen", "tabelle_zeile_weg"),
            K("kommentareweg", "Spalte löschen", "tabelle_spalte_weg"),
        ]),
        G("Zellengröße", [
            K("papiergroesse", "Spaltenbreite …", "tabelle_breite", gross=True),
            K("abstand", "Zeilenhöhe …", "tabelle_hoehe", gross=True),
        ]),
        G("Ausrichtung", [
            K("links", "Linksbündig", ("tabelle_ausrichten", "links")),
            K("mitte", "Zentriert", ("tabelle_ausrichten", "mitte")),
            K("rechts", "Rechtsbündig", ("tabelle_ausrichten", "rechts")),
        ]),
        G("Tabellenformatierung", [
            K("block", "Kopfzeile", "tabelle_kopfzeile", haken="tabelle_kopf", gross=True),
            K("rahmen", "Rahmenlinien", "tabelle_rahmen", haken="tabelle_rand", gross=True),
            K("farbe", "Farbe der Kopfzeile", None, klappe="tabelle_kopffarbe"),
        ]),
    ]),
    ("Zeichentools", "zeichnen", [
        G("Formen", [K("stift", "Form ändern", None, gross=True, klappe="zeichen_form")]),
        G("Füllung", [K("farbe", "Füllfarbe", None, gross=True, klappe="zeichen_fuellung")]),
        G("Kontur", [K("rahmen", "Randfarbe", None, gross=True, klappe="zeichen_rand")]),
        G("Anordnen", [
            K("objektdrehen", "Drehen", None, gross=True, klappe="objekt_drehen"),
            K("ausrichten", "Ausrichten", None, klappe="objekt_ausrichten"),
            K("sperren", "Löschen", "objekt_weg"),
        ]),
        G("Größe", [K("papiergroesse", "Größe …", "zeichen_groesse", gross=True)]),
    ]),
    ("Texttools", "text", [
        G("Schrift", [
            K(None, "Fett", "fett", haken="fett", text="F"), K(None, "Kursiv", "kursiv", haken="kursiv", text="K"),
            K("unter", "Unterstrichen", "unter", haken="unter"),
            K("schriftfarbe", "Textfüllung", "schriftfarbe_jetzt", klappe="schriftfarbe_klappe", gross=True),
        ]),
        G("Textkontur und Effekte", [
            K("umriss", "Textkontur", "zeichenumriss", gross=True, haken="umriss"),
            K("texteffekt", "Texteffekte", None, klappe="effekt_klappe", gross=True),
        ]),
        G("Absatz", [K("links", "Links", "links"), K("mitte", "Zentriert", "mitte"), K("rechts", "Rechts", "rechts")]),
    ]),
    ("Bildwerkzeuge", "bild", [
        G("Größe", [
            K("papiergroesse", "Breite …", "bild_breite", gross=True),
            K("einpassen", "Originalgröße", "bild_original"),
        ]),
        G("Anordnen", [
            K("objektdrehen", "Drehen", None, gross=True, klappe="objekt_drehen"),
            K("ausrichten", "Ausrichten", None, klappe="objekt_ausrichten"),
        ]),
        G("Barrierefreiheit", [K("barrierefrei", "Alternativtext …", "bild_alt", gross=True)]),
        G("Löschen", [K("sperren", "Bild löschen", "objekt_weg", gross=True)]),
    ]),
    ("Diagrammtools", "diagramm", [
        G("Diagrammentwurf", [K("beschriftung", "Titel …", "diagramm_titel", gross=True)]),
        G("Daten", [K("saeule", "Daten bearbeiten", "diagramm_daten", gross=True)]),
        G("Diagrammtyp", [
            K("blattansicht", "Diagrammart", None, gross=True, menue=[
                ("Säulen", "diagramm_art", "saeulen"), ("Linie", "diagramm_art", "linie"), ("Kreis", "diagramm_art", "kreis")]),
        ]),
        G("Formatierung", [K("sperren", "Löschen", "objekt_weg", gross=True)]),
    ]),
    ("SmartArt-Tools", "smartart", [
        G("SmartArt-Entwurf", [
            K("smartart", "Text bearbeiten", "smartart_text", gross=True),
            K("blattansicht", "Layout", None, gross=True, menue=[
                (n, "smartart_layout", n) for n in ("Liste", "Prozess", "Zyklus", "Hierarchie", "Pyramide", "Vergleich")]),
        ]),
        G("SmartArt-Format", [K("sperren", "Löschen", "objekt_weg", gross=True)]),
    ]),
    ("Gleichungswerkzeuge", "gleichung", [
        G("Formeleditor-Funktionen", [
            K("formel", "Formel bearbeiten", "gleichung_bearbeiten", gross=True),
            K("sperren", "Löschen", "objekt_weg", gross=True),
        ]),
    ]),
    ("Kopf- und Fußzeilenwerkzeuge", "kopffuss", [
        G("Kopfzeile", [K("kopffuss", "Kopfzeile entfernen", "kf_kopf_weg", gross=True)]),
        G("Fußzeile", [K("kopffuss", "Fußzeile entfernen", "kf_fuss_weg", gross=True)]),
        G("Seitenzahl", [
            K("seitenzahl", "Seitenzahl", "kf_seitenzahl", gross=True),
            K("seitenzahl", "Seite 1 von N", "kf_seiten", gross=True),
            K("datumuhrzeit", "Datum", "kf_datum", gross=True),
        ]),
        G("Navigation", [K("haken", "Zum Text", "kf_schliessen", gross=True)]),
    ]),
]
