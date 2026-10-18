# Prüfbogen ↔ native Fassung

Erzeugt von `werkzeug/pruefbogen-abgleich.py` aus dem Prüfkatalog (415 Punkte). **✅ 141 · ◐ 30 · ⬜ 244**. ✅ = Befehl/Funktion vorhanden (einzeln getestet nur, wo `tests/` es belegt); ◐ = teilweise oder anders gelöst; ⬜ = offen.
Die Bilder des Bogens (bindend, 1 zu 1) liegen unter `doku/native-qt/pruefbogen/bilder/`.

## DATEI

- ✅ Neu — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Öffnen — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Zuletzt geöffnet — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ⬜ Neu aus Vorlage — nicht übertragen
- ⬜ Vorlagenordner — nicht übertragen
- ✅ Speichern — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Speichern unter — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Drucken — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)  _(Web-Fassung: fertig)_
- ✅ Druckvorschau — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Als PDF exportieren — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ◐ Druckereinstellungen — Drucken öffnet den Systemdialog; Dokumentinformationen nur lesend
- ◐ Dokumenteigenschaften — Drucken öffnet den Systemdialog; Dokumentinformationen nur lesend
- ✅ Umbenennen — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ✅ Optionen (F9) — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ✅ Schließen — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Beenden — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ⬜ Hilfe > Handbuch — nicht übertragen
- ⬜ Hilfe > Tastenkürzel — nicht übertragen
- ⬜ Hilfe > Erweiterungen — nicht übertragen
- ✅ Hilfe > Über Lunivo Office — ☰-Menü ▸ Hilfe ▸ Über

## MENÜ UND SCHNELLZUGRIFF

- ◐ Kein Datei-Reiter mehr — Widerspruch: die neue Struktur („1. DATEI“) hat einen Datei-Reiter — beides ist vorhanden
- ✅ ☰ Menü links vor den Reitern — widgets/menue_tafel.py, widgets/register_band.py
- ◐ ☰ Menü auch am Anfang der Symbolleiste — widgets/symbolleisten.py gebaut, noch nicht als Oberfläche wählbar
- ✅ Tafel mit zwei Spalten — widgets/menue_tafel.py, widgets/register_band.py
- ✅ Untermenü füllt die rechte Spalte, kein eigenes Fenster — widgets/menue_tafel.py, widgets/register_band.py
- ✅ Liste zuletzt verwendeter Dateien rechts — widgets/menue_tafel.py, widgets/register_band.py
- ✅ × nimmt einen Eintrag aus der Liste — widgets/menue_tafel.py, widgets/register_band.py
- ✅ ↻ holt die Liste neu — widgets/menue_tafel.py, widgets/register_band.py
- ⬜ Als Bild exportieren (PNG) — nicht übertragen  _(Web-Fassung: teil)_
- ⬜ Dokumentverschlüsselung — nicht übertragen  _(Web-Fassung: fertig)_
- ✅ Schnellzugriff in der Reiterzeile — widgets/menue_tafel.py, widgets/register_band.py

## START > Zwischenablage

- ✅ Einfügen — Band: Start ▸ Zwischenablage  _(Web-Fassung: fertig)_
- ✅ Einfügen ohne Formatierung — Band: Start ▸ Zwischenablage  _(Web-Fassung: fertig)_
- ✅ Ausschneiden — Band: Start ▸ Zwischenablage
- ✅ Kopieren — Band: Start ▸ Zwischenablage
- ✅ Format übertragen — Band: Start ▸ Zwischenablage  _(Web-Fassung: fertig)_
- ✅ Verlauf > Rückgängig — Schnellzugriff (wie im Bogen: dort statt im Reiter)  _(Web-Fassung: fertig)_
- ✅ Verlauf > Wiederholen — Schnellzugriff (wie im Bogen: dort statt im Reiter)  _(Web-Fassung: fertig)_

## START > Schriftart

- ✅ Schriftart — Felder im Band (widgets/register_band.py)
- ✅ Schriftgröße — Felder im Band (widgets/register_band.py)
- ✅ Schrift vergrößern — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Schrift verkleinern — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Formatierung löschen — Band: Start ▸ Schriftart
- ✅ Fett — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Kursiv — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Unterstrichen — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Durchgestrichen — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Hochgestellt — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Tiefgestellt — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Hervorheben — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Schriftfarbe — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ✅ Groß-/Kleinschreibung — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_
- ⬜ Unterstreichungsart — nicht übertragen  _(Web-Fassung: fertig)_
- ⬜ Texteffekte — Band: Start ▸ Schriftart  _(Web-Fassung: fertig)_

## START > Absatz

- ✅ Aufzählung — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_
- ✅ Nummerierung — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_
- ✅ Einzug verringern — Band: Start ▸ Absatz ▸ Einzug & Listenebene  _(Web-Fassung: fertig)_
- ✅ Einzug vergrößern — Band: Start ▸ Absatz ▸ Einzug & Listenebene  _(Web-Fassung: fertig)_
- ✅ Listenebene erhöhen — Band: Start ▸ Absatz ▸ Einzug & Listenebene
- ✅ Listenebene verringern — Band: Start ▸ Absatz ▸ Einzug & Listenebene
- ✅ Linksbündig — Band: Start ▸ Absatz
- ✅ Zentriert — Band: Start ▸ Absatz
- ✅ Rechtsbündig — Band: Start ▸ Absatz
- ✅ Blocksatz — Band: Start ▸ Absatz
- ✅ Zeilenabstand — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_
- ✅ Sortieren — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_
- ✅ Steuerzeichen — Band: Start ▸ Absatz

## START > Absatzlayout

- ✅ Zeilenabstand — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_
- ◐ Einzug genau — Absatz-Dialog (widgets/dialogs.py) — einfacher als das Vorlagenbild (zwei Karteireiter, Vorschau)  _(Web-Fassung: fertig)_
- ⬜ Absatzrahmen — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_
- ✅ Absatzschattierung — Band: Start ▸ Absatz  _(Web-Fassung: fertig)_

## START > Einstellungen

- ✅ Optionen — Datei-Reiter / ☰ / F9

## START > Stile & Bearbeiten

- ✅ Formatvorlage auswählen — Stilkatalog + Feld im Band
- ⬜ Formatvorlagen verwalten — nicht übertragen
- ✅ Suchen — Band: Start ▸ Bearbeiten  _(Web-Fassung: fertig)_
- ✅ Ersetzen — Band: Start ▸ Bearbeiten  _(Web-Fassung: fertig)_
- ✅ Suchen und Ersetzen — Band: Start ▸ Bearbeiten  _(Web-Fassung: fertig)_
- ✅ Alles auswählen — Band: Start ▸ Bearbeiten
- ⬜ Objekte auswählen — Band: Start ▸ Bearbeiten

## EINFÜGEN

- ⬜ Deckblatt — Band: Einfügen ▸ Seiten
- ✅ Leere Seite — Band: Einfügen ▸ Seiten  _(Web-Fassung: fertig)_
- ✅ Seitenumbruch — Band: Einfügen ▸ Seiten, Seitenlayout ▸ Seite einrichten ▸ Umbrüche  _(Web-Fassung: fertig)_
- ✅ Tabelle einfügen — Band: Einfügen ▸ Tabellen  _(Web-Fassung: fertig)_
- ⬜ Schnelltabelle — Band: Einfügen ▸ Tabellen
- ⬜ Tabellenblatt — Band: Einfügen ▸ Tabellen
- ✅ Bild — Band: Einfügen ▸ Illustrationen  _(Web-Fassung: teil)_
- ⬜ Zeichnen — nicht übertragen  _(Web-Fassung: fertig)_
- ⬜ Diagramm — Band: Einfügen ▸ Illustrationen  _(Web-Fassung: fertig)_
- ⬜ Bildschirmfoto — Band: Einfügen ▸ Illustrationen
- ⬜ SmartArt — Band: Einfügen ▸ Illustrationen  _(Web-Fassung: fertig)_
- ⬜ Piktogramm — Band: Einfügen ▸ Illustrationen
- ⬜ WordArt — Band: Einfügen ▸ Illustrationen  _(Web-Fassung: fertig)_
- ✅ Hyperlink — Band: Einfügen ▸ Links
- ⬜ Lesezeichen / Textmarke — Band: Einfügen ▸ Links  _(Web-Fassung: fertig)_
- ⬜ Querverweis — Band: Einfügen ▸ Links, Verweise ▸ Beschriftungen  _(Web-Fassung: fertig)_
- ✅ Kopfzeile — Dialoge (widgets/dialogs.py), PDF/Druck/DOCX getestet  _(Web-Fassung: fertig)_
- ✅ Fußzeile — Dialoge (widgets/dialogs.py), PDF/Druck/DOCX getestet  _(Web-Fassung: fertig)_
- ✅ Seitenzahl — Band: Einfügen ▸ Kopf- und Fußzeile  _(Web-Fassung: fertig)_
- ⬜ Textfeld — Band: Einfügen ▸ Text  _(Web-Fassung: fertig)_
- ⬜ Textbaustein — nicht übertragen  _(Web-Fassung: fertig)_
- ⬜ Schnellbaustein — nicht übertragen  _(Web-Fassung: fertig)_
- ⬜ Initiale — Band: Einfügen ▸ Text  _(Web-Fassung: teil)_
- ◐ Datum — Datum einfügen; Fenster mit Formatliste/Sprache fehlt  _(Web-Fassung: fertig)_
- ◐ Uhrzeit — Datum einfügen; Fenster mit Formatliste/Sprache fehlt  _(Web-Fassung: fertig)_
- ⬜ Text aus Datei — Band: Einfügen ▸ Text  _(Web-Fassung: fertig)_
- ✅ Sonderzeichen — Band: Einfügen ▸ Symbole
- ⬜ Formel — Band: Einfügen ▸ Symbole  _(Web-Fassung: fertig)_

## SEITENLAYOUT

- ✅ Seitenränder — Band: Seitenlayout ▸ Seitenhintergrund  _(Web-Fassung: fertig)_
- ✅ Ausrichtung — Band: Seitenlayout ▸ Seite einrichten
- ✅ Papierformat — Reiter Seitenlayout ▸ Größe (Befehle.w_setzePapier)  _(Web-Fassung: fertig)_
- ⬜ Spalten — Band: Seitenlayout ▸ Seite einrichten
- ✅ Umbruch > Seitenumbruch — Band: Einfügen ▸ Seiten, Seitenlayout ▸ Seite einrichten ▸ Umbrüche  _(Web-Fassung: fertig)_
- ⬜ Umbruch > Spaltenumbruch — Band: Seitenlayout ▸ Seite einrichten ▸ Umbrüche
- ⬜ Umbruch > Abschnittsumbruch — Band: Seitenlayout ▸ Seite einrichten ▸ Umbrüche
- ✅ Einzug — Band: Seitenlayout ▸ Absatz
- ⬜ Absatzabstand — Band: Seitenlayout ▸ Absatz
- ⬜ Zeilennummern — Band: Seitenlayout ▸ Seite einrichten
- ⬜ Silbentrennung — Band: Seitenlayout ▸ Absatz, Seitenleiste ▸ Sprache  _(Web-Fassung: teil)_
- ⬜ Textumbruch — nicht übertragen
- ⬜ Seitenfarbe — Band: Seitenlayout ▸ Seitenhintergrund  _(Web-Fassung: fertig)_
- ⬜ Wasserzeichen — Band: Seitenlayout ▸ Seitenhintergrund
- ⬜ Seitenrahmen — nicht übertragen  _(Web-Fassung: fertig)_
- ⬜ Bild/Objekt anordnen — nicht übertragen  _(Web-Fassung: fertig)_

## REFERENZEN

- ✅ Inhaltsverzeichnis — Band: Verweise ▸ Inhaltsverzeichnis
- ✅ Verzeichnisse aktualisieren — Band: Verweise ▸ Inhaltsverzeichnis
- ⬜ Fußnote — Band: Verweise ▸ Fußnoten
- ⬜ Endnote — Band: Verweise ▸ Fußnoten
- ⬜ Nächste Note — Band: Verweise ▸ Fußnoten
- ⬜ Vorige Note — Band: Verweise ▸ Fußnoten
- ⬜ Notenbereich — Band: Verweise ▸ Fußnoten
- ⬜ Zitat einfügen — Band: Verweise ▸ Zitate und Literatur
- ⬜ Neue Quelle — Band: Verweise ▸ Zitate und Literatur
- ⬜ Quellen verwalten — Band: Verweise ▸ Zitate und Literatur
- ⬜ Zitierweise — Band: Verweise ▸ Zitate und Literatur
- ⬜ Literaturverzeichnis — Band: Verweise ▸ Zitate und Literatur
- ⬜ Beschriftung — Band: Verweise ▸ Beschriftungen
- ⬜ Abbildungsverzeichnis — Band: Verweise ▸ Beschriftungen
- ⬜ Querverweis — Band: Einfügen ▸ Links, Verweise ▸ Beschriftungen
- ⬜ Indexeintrag — Band: Verweise ▸ Index
- ⬜ Stichwortverzeichnis — Band: Verweise ▸ Index

## ÜBERPRÜFEN

- ✅ Prüfen — Band: Seitenleiste ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Gründlich prüfen — Band: Seitenleiste ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Rechtschreibung — Band: Überprüfen ▸ Dokumentprüfung
- ⬜ Thesaurus — Band: Seitenleiste ▸ Sprache, Überprüfen ▸ Dokumentprüfung
- ✅ Wörter zählen — Band: Überprüfen ▸ Dokumentprüfung
- ⬜ Korrektursprache — Band: Überprüfen ▸ Sprache  _(Web-Fassung: fertig)_
- ⬜ Barrierefreiheit prüfen — Band: Überprüfen ▸ Barrierefreiheit
- ⬜ Neuer Kommentar — Band: Überprüfen ▸ Kommentare
- ⬜ Nächster Kommentar — Band: Überprüfen ▸ Kommentare
- ⬜ Voriger Kommentar — Band: Überprüfen ▸ Kommentare
- ⬜ Kommentar löschen — Band: Überprüfen ▸ Kommentare
- ⬜ Alle Kommentare löschen — Band: Überprüfen ▸ Kommentare
- ⬜ Änderungen verfolgen — Band: Überprüfen ▸ Änderungen
- ⬜ Markup anzeigen — Band: Überprüfen ▸ Änderungen
- ⬜ Überarbeitungsbereich — Band: Überprüfen ▸ Änderungen
- ⬜ Änderung annehmen — Band: Überprüfen ▸ Änderungen
- ⬜ Änderung ablehnen — Band: Überprüfen ▸ Änderungen
- ⬜ Nächste Änderung — Band: Überprüfen ▸ Änderungen
- ⬜ Vorige Änderung — Band: Überprüfen ▸ Änderungen
- ⬜ Alle annehmen — Band: Überprüfen ▸ Änderungen
- ⬜ Alle verwerfen — Band: Überprüfen ▸ Änderungen
- ⬜ Bearbeitung sperren — Band: Überprüfen ▸ Schützen

## SCHREIBHILFE (Lunivo)

- ✅ Dokumentprüfung > Prüfen — Band: Seitenleiste ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Dokumentprüfung > Gründlich prüfen — Band: Seitenleiste ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Dokumentprüfung > Welche Hilfe wann — Band: Seitenleiste ▸ Prüfen ▸ Dokumentprüfung
- ✅ Beim Schreiben > Rechtschreibprüfung — Band: Seitenleiste ▸ Beim Schreiben
- ✅ Beim Schreiben > Wortvorhersage — Band: Seitenleiste ▸ Beim Schreiben
- ✅ Beim Schreiben > AutoKorrektur — Band: Seitenleiste ▸ Beim Schreiben
- ✅ Vorlesen > Vorlesen — Band: Seitenleiste ▸ Vorlesen, Seitenleiste ▸ Vorlesen ▸ Vorlesen
- ✅ Vorlesen > Ab hier vorlesen — Band: Seitenleiste ▸ Vorlesen ▸ Vorlesen
- ✅ Vorlesen > Anhalten — Band: Seitenleiste ▸ Vorlesen ▸ Vorlesen
- ✅ Vorlesen > Stimme und Tempo — Band: Seitenleiste ▸ Vorlesen ▸ Vorlesen
- ✅ KI > KI-Korrektur — Band: KI ▸ Korrektur
- ✅ KI > Vorschläge — Seitenleiste / KI-Reiter (test_schreibhilfe)
- ✅ Anzeigen > Seitenleiste Schreibhilfe — Band: Seitenleiste ▸ Anzeigen  _(Web-Fassung: fertig)_
- ✅ Anzeigen > Optionen — Seitenleiste / KI-Reiter (test_schreibhilfe)

## SENDUNGEN (Lunivo)

- ⬜ Umschlag — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Etiketten — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Seriendruck-Assistent — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Seriendruckfeld — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Adressblock — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Regeln — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Ergebnisse anzeigen — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Formular > Textfeld — Band: Einfügen ▸ Text
- ⬜ Formular > Kontrollkästchen — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten
- ⬜ Formular > Schaltfläche — Reiter „Sendungen“ nicht in der neuen Struktur; Daten in register.json erhalten  _(Web-Fassung: fertig)_

## ANSICHT

- ⬜ Drucklayout — Band: Ansicht ▸ Dokumentansichten
- ✅ Lesemodus — Band: Ansicht ▸ Dokumentansichten, Seitenleiste ▸ Lesen
- ⬜ Zwei Seiten — Band: Ansicht ▸ Dokumentansichten
- ⬜ Weblayout — Band: Ansicht ▸ Dokumentansichten
- ⬜ Gliederung — Band: Ansicht ▸ Dokumentansichten
- ⬜ Lineal — Band: Ansicht ▸ Anzeigen
- ⬜ Vertikales Lineal — Band: Ansicht ▸ Anzeigen
- ⬜ Gitternetzlinien — Band: Ansicht ▸ Anzeigen  _(Web-Fassung: fertig)_
- ✅ Navigationsbereich — Band: Ansicht ▸ Anzeigen
- ✅ Textbegrenzungen — Band: Ansicht ▸ Anzeigen  _(Web-Fassung: fertig)_
- ✅ Seitenleiste Schreibhilfe — Band: Seitenleiste ▸ Anzeigen  _(Web-Fassung: fertig)_
- ✅ Lesehilfe — Band: Seitenleiste ▸ Lesen
- ✅ Zeilenfokus — Band: Seitenleiste ▸ Lesen
- ✅ Vergrößern — Band: Ansicht ▸ Zoom
- ✅ Verkleinern — Band: Ansicht ▸ Zoom
- ⬜ 100 % — Band: Ansicht ▸ Zoom
- ⬜ Seitenbreite — Band: Ansicht ▸ Zoom
- ⬜ Eine Seite — Band: Ansicht ▸ Zoom
- ⬜ Zoom — Band: Ansicht ▸ Zoom
- ⬜ Neues Fenster — Band: Ansicht ▸ Fenster
- ⬜ Anordnen — Band: Ansicht ▸ Fenster
- ⬜ Nebeneinander — Band: Ansicht ▸ Fenster, Ansicht ▸ Fenster ▸ Anordnen
- ⬜ Untereinander — Band: Ansicht ▸ Fenster, Ansicht ▸ Fenster ▸ Anordnen
- ⬜ Kacheln — Band: Ansicht ▸ Fenster, Ansicht ▸ Fenster ▸ Anordnen
- ⬜ Fensterliste — Band: Ansicht ▸ Fenster
- ✅ Helligkeit > Wie das System — Band: Ansicht ▸ Helligkeit
- ✅ Helligkeit > Immer hell — Band: Ansicht ▸ Helligkeit
- ✅ Helligkeit > Immer dunkel — Band: Ansicht ▸ Helligkeit
- ⬜ Oberfläche > Register anpassen — Band: Ansicht ▸ Oberfläche
- ⬜ Oberfläche > Symbol austauschen — Band: Ansicht ▸ Oberfläche
- ⬜ Oberfläche > Benutzeroberfläche — Band: Ansicht ▸ Oberfläche
- ✅ Oberfläche > Menüleiste — Band: Ansicht ▸ Oberfläche
- ⬜ Oberfläche > Symbolleisten — Band: Ansicht ▸ Oberfläche  _(Web-Fassung: fertig)_
- ⬜ Oberfläche > Vorlagen zurücksetzen — Band: Ansicht ▸ Oberfläche

## KONTEXTTABELLEN

- ◐ Tabellenwerkzeuge — Reiter erscheint in der Tabelle (test_tabellentools_wirken); ohne Tabellenformatvorlagen
- ⬜ Zeichentools — nicht übertragen  _(Web-Fassung: teil)_
- ⬜ Diagrammtools — nicht übertragen
- ⬜ SmartArt-Tools — nicht übertragen
- ⬜ Gleichungswerkzeuge — nicht übertragen  _(Web-Fassung: fertig)_
- ◐ Kopf- und Fußzeilenwerkzeuge — Reiter vorhanden, Kopf/Fuß über Dialog statt am Blatt  _(Web-Fassung: teil)_

## LANGUAGE BRIDGE (Architektur)

- ✅ Zentrale Sprachkontext-Verwaltung — services/writing_assistant.py, storage/gelernt.py
- ✅ Dokumentversion-Tracking — QTextDocument.revision() — verworfen, wenn sich der Text änderte (test_ki_korrektur_ende_zu_ende)
- ◐ Prüfungs-ID-System — Revision statt Prüf-ID; Fund = dict; Zustände nur angenommen/weggewinkt
- ◐ Einheitlicher Fehlerstatus — Revision statt Prüf-ID; Fund = dict; Zustände nur angenommen/weggewinkt
- ◐ Fehler-Lebenszyklus (active/accepted/ignored/corrected) — Revision statt Prüf-ID; Fund = dict; Zustände nur angenommen/weggewinkt
- ✅ Keine parallelen Wörterbücher — services/writing_assistant.py, storage/gelernt.py
- ✅ Benutzerwörter zentral speichern — services/writing_assistant.py, storage/gelernt.py
- ◐ Ignorierte Wörter zentral speichern — Revision statt Prüf-ID; Fund = dict; Zustände nur angenommen/weggewinkt
- ✅ Akzeptierte Korrektionen speichern — services/writing_assistant.py, storage/gelernt.py

## LANGUAGE BRIDGE (Spelling Engine)

- ✅ Native Browser-Spellcheck deaktiviert — gegenstandslos: kein Browser
- ✅ Lunivo-Regeln verwenden statt Browser — services/pruefung.py (Parität zu pruefung.js getestet)
- ✅ Benutzerwörter in Rechtschreibung beachten — services/pruefung.py (Parität zu pruefung.js getestet)
- ◐ Ignorierte Wörter in Rechtschreibung beachten — inRuhe/weggewinkt beachtet; einheitliches Fund-dict
- ◐ Fehler als unified language-issue — inRuhe/weggewinkt beachtet; einheitliches Fund-dict

## LANGUAGE BRIDGE (Grammar Engine)

- ✅ Dieselbe Sprachkontext wie Spelling — gleiche Engine, regeln.js gelesen
- ✅ Grammatikregeln aus regeln.js nutzen — gleiche Engine, regeln.js gelesen
- ◐ Benutzerwörter in Grammatik beachten — gemeinsame Funde
- ◐ Fehler als unified language-issue — gemeinsame Funde

## LANGUAGE BRIDGE (AI Engine)

- ✅ Asynchrone KI-Requests mit Validierung — services/ki_dienst.py (Revision geprüft)
- ✅ Dokumentversion überprüfen — services/ki_dienst.py (Revision geprüft)
- ◐ CheckId überprüfen — Revision statt Check-ID
- ✅ Keine veralteten Ergebnisse akzeptieren — services/ki_dienst.py (Revision geprüft)
- ⬜ KI-Konfidenz-Score speichern — nicht übertragen

## LANGUAGE BRIDGE (Fehler-Zusammenführung)

- ◐ Mehrere Quellen für gleiche Position zusammenführen — LanguageTool-Funde ergänzen nur nicht überlappende (WritingAssistant._lt_fertig)
- ⬜ Konflikt-Auflösung nach Quelle/Konfidenz/Typ — nicht übertragen
- ◐ Hochwertige Vorschläge nicht überschreiben — LanguageTool-Funde ergänzen nur nicht überlappende (WritingAssistant._lt_fertig)
- ✅ Fehler-Signatur für Identify verwenden — WritingAssistant._key

## LANGUAGE BRIDGE (Invalidierung & Debouncing)

- ⬜ Bereichs-Invalidierung bei Änderungen — es wird der ganze Text neu geprüft
- ⬜ Sicherheitsbereich um geänderte Stelle — es wird der ganze Text neu geprüft
- ✅ Debouncing für schnelle Eingaben — Timer 900 ms; Gründlich prüfen
- ✅ Vollständige Prüfung möglich (Gründlich prüfen) — Timer 900 ms; Gründlich prüfen

## SCHREIBHILFE (Sidebar-Integration)

- ✅ Fehler aus Language Bridge anzeigen — widgets/schreibhilfe_panel.py, editor_widget.set_wellen
- ✅ Rote Wellenlinien aus Bridge-Status — widgets/schreibhilfe_panel.py, editor_widget.set_wellen
- ⬜ Kontextmenü für Fehler-Aktionen — Rechtsklick-Menü fehlt  _(Web-Fassung: fertig)_
- ✅ Fehler annehmen/ignorieren/korrigieren — widgets/schreibhilfe_panel.py, editor_widget.set_wellen
- ◐ Schalter 'Rote Wellenlinien' zeigt/versteckt nur — Schalter hält auch die Prüfung an

## SCHREIBHILFE (Menü-Integration)

- ◐ Schreibhilfe-Register im Band — nach der neuen Struktur in der rechten Seitenleiste (Bereich „Schreibhilfe“)
- ✅ Prüfen-Knopf löst check() aus — Seitenleiste + Band
- ✅ Gründlich prüfen-Knopf für volle Prüfung — Seitenleiste + Band
- ✅ Welche Hilfe wann anzeigen — Seitenleiste + Band
- ◐ Beim Schreiben-Optionen — Optionen-Fenster, nicht alle Schalter des Vorbilds
- ◐ Vorlesen-Integration — services/vorlesen.py — nur mit Attrappe getestet
- ◐ KI-Korrektur-Optionen — Optionen-Fenster, nicht alle Schalter des Vorbilds
- ◐ Anzeigen-Optionen — Optionen-Fenster, nicht alle Schalter des Vorbilds

## DOKUMENTMODELL (Structure)

- ◐ Document-Klasse mit Sections — ein Abschnitt: PageSettings (Papier, Ränder, Kopf/Fuß); keine Spalten, keine mehreren Abschnitte
- ◐ Section mit Inhalt, Header, Footer — ein Abschnitt: PageSettings (Papier, Ränder, Kopf/Fuß); keine Spalten, keine mehreren Abschnitte
- ✅ DocumentContent mit Blocks — QTextDocument (Blöcke, Tabellen, Bilder)
- ◐ Block-Vererbung (Paragraph, Table, Image, Shape) — Absatz, Tabelle, Bild; keine Formen
- ◐ PageSetup mit Margins, PageSize, Columns — ein Abschnitt: PageSettings (Papier, Ränder, Kopf/Fuß); keine Spalten, keine mehreren Abschnitte

## DOKUMENTMODELL (Callbacks)

- ✅ Änderungs-Callbacks für Paragraph — Qt-Signal contentsChanged → WritingAssistant.dokument_geaendert
- ✅ Änderungs-Callbacks für Table — Qt-Signal contentsChanged → WritingAssistant.dokument_geaendert
- ✅ Änderungs-Callbacks für DocumentContent — Qt-Signal contentsChanged → WritingAssistant.dokument_geaendert
- ✅ Callbacks triggern Language Bridge Update — Qt-Signal contentsChanged → WritingAssistant.dokument_geaendert

## OPTIONEN > Ansicht > Anzeigen

- ⬜ Lineal — Band: Ansicht ▸ Anzeigen
- ⬜ Vertikales Lineal — Band: Ansicht ▸ Anzeigen
- ✅ Navigationsbereich — Band: Ansicht ▸ Anzeigen
- ✅ Textbegrenzungen — Band: Ansicht ▸ Anzeigen
- ⬜ Gitternetzlinien — Band: Ansicht ▸ Anzeigen
- ⬜ Statusleiste — (noch nicht zugeordnet)
- ⬜ Seitenleiste beim Start — (noch nicht zugeordnet)
- ⬜ QuickInfo — (noch nicht zugeordnet)
- ⬜ Live-Vorschau — (noch nicht zugeordnet)
- ⬜ Minisymbolleiste bei Auswahl — (noch nicht zugeordnet)
- ⬜ Minisymbolleiste bei Rechtsklick — (noch nicht zugeordnet)
- ⬜ Tipp für Kopf- bzw. Fußzeile — (noch nicht zugeordnet)

## OPTIONEN > Ansicht > Druckoptionen

- ⬜ Hervorhebungen drucken — (noch nicht zugeordnet)
- ⬜ Textbegrenzungen drucken — (noch nicht zugeordnet)
- ⬜ Zuschnittsmarken anzeigen — (noch nicht zugeordnet)
- ⬜ Feldfunktionen drucken — (noch nicht zugeordnet)
- ⬜ Textmarken drucken — (noch nicht zugeordnet)
- ⬜ Feldschattierung — (noch nicht zugeordnet)

## OPTIONEN > Ansicht > Formatierungszeichen

- ⬜ Alle anzeigen — (noch nicht zugeordnet)
- ⬜ Absatzmarken — (noch nicht zugeordnet)
- ⬜ Leerzeichen — (noch nicht zugeordnet)
- ⬜ Tabstoppzeichen — (noch nicht zugeordnet)
- ⬜ Objektanker — (noch nicht zugeordnet)
- ⬜ Ausgeblendeter Text — (noch nicht zugeordnet)

## OPTIONEN > Ansicht > Menübandoptionen

- ⬜ Doppelklick blendet das Band aus — (noch nicht zugeordnet)
- ⬜ Strg+Klick folgt einem Verweis — (noch nicht zugeordnet)

## OPTIONEN > Ansicht > Darstellung

- ⬜ Schrift und Helligkeit — (noch nicht zugeordnet)
- ⬜ Größe der Symbole — (noch nicht zugeordnet)
- ⬜ Schrift der Bedienung — (noch nicht zugeordnet)
- ⬜ Benutzeroberfläche — Band: Ansicht ▸ Oberfläche

## OPTIONEN > Bearbeiten > Bearbeitungsoptionen

- ⬜ Wortweise markieren — (noch nicht zugeordnet)
- ⬜ Text mit der Maus verschieben — (noch nicht zugeordnet)
- ⬜ Tippen ersetzt die Auswahl — (noch nicht zugeordnet)
- ⬜ Maximale Rückgängig-Schritte — (noch nicht zugeordnet)

## OPTIONEN > Bearbeiten > AutoFormat

- ⬜ Automatisch nummerierte Listen — (noch nicht zugeordnet)
- ⬜ Aufzählungen erkennen — (noch nicht zugeordnet)
- ⬜ Zahl automatisch im Kreis — (noch nicht zugeordnet)

## OPTIONEN > Bearbeiten > AutoKorrektur

- ✅ AutoKorrektur — Band: Seitenleiste ▸ Beim Schreiben
- ⬜ Typografische Anführungszeichen — (noch nicht zugeordnet)
- ⬜ Gedankenstriche — (noch nicht zugeordnet)
- ⬜ Auslassungspunkte — (noch nicht zugeordnet)
- ⬜ Jeden Satz mit einem Großbuchstaben beginnen — (noch nicht zugeordnet)
- ⬜ Wochentage immer großschreiben — (noch nicht zugeordnet)
- ⬜ Englische Ordnungszahlen hochstellen — (noch nicht zugeordnet)
- ⬜ Feststelltaste korrigieren — (noch nicht zugeordnet)
- ⬜ Internet- und Netzwerkpfade durch Hyperlinks ersetzen — (noch nicht zugeordnet)
- ⬜ Leerzeichen am Absatzanfang mit Erstzeileneinzug — (noch nicht zugeordnet)
- ⬜ Leerzeichenformat am Ende rechtsbündiger Zeilen anpassen — (noch nicht zugeordnet)
- ⬜ Bei zentriertem Ausrichten Erstzeileneinzug löschen — (noch nicht zugeordnet)
- ⬜ Tabulator und Rücktaste setzen den Einzug — (noch nicht zugeordnet)
- ✅ Wortvorhersage — Band: Seitenleiste ▸ Beim Schreiben

## OPTIONEN > Bearbeiten > Ausschneiden und Einfügen

- ⬜ Schaltfläche nach dem Einfügen — (noch nicht zugeordnet)
- ⬜ Mittlere Maustaste fügt ein — (noch nicht zugeordnet)
- ⬜ Standardeinfügeformat — (noch nicht zugeordnet)
- ⬜ Ohne Formatierung einfügen — (noch nicht zugeordnet)

## OPTIONEN > Allgemein und Speichern > Speichern

- ⬜ Dateien als Standard speichern — (noch nicht zugeordnet)

## OPTIONEN > Allgemein und Speichern > Schrift für neuen Text

- ⬜ Schrift — (noch nicht zugeordnet)
- ✅ Größe — Band: Seitenlayout ▸ Seite einrichten

## OPTIONEN > Allgemein und Speichern > Allgemeine Optionen

- ⬜ Maßeinheit — (noch nicht zugeordnet)
- ⬜ Bilder in der Datei nicht komprimieren — (noch nicht zugeordnet)
- ⬜ Standard-Ausgabeziel — (noch nicht zugeordnet)

## OPTIONEN > Allgemein und Speichern > Webseite

- ⬜ Webseitencodierung — (noch nicht zugeordnet)

## OPTIONEN > Allgemein und Speichern > Kompatibilitätsoptionen

- ⬜ Seitenumbruch und Absatzmarke aufteilen — (noch nicht zugeordnet)
- ⬜ Hängenden Einzug nicht als Tabstopp verwenden — (noch nicht zugeordnet)
- ⬜ Nachstehende Leerstellen unterstreichen — (noch nicht zugeordnet)
- ⬜ Layout von Fußnoten wie Word 6/95/97 — (noch nicht zugeordnet)
- ⬜ Zeilenhöhe in Tabellen auf Rasterhöhe anpassen — (noch nicht zugeordnet)

## OPTIONEN > Sicherungseinstellungen > Sicherung

- ⬜ Wann gesichert wird — (noch nicht zugeordnet)
- ⬜ Abstand (Minuten) — (noch nicht zugeordnet)
- ⬜ Wo die Einstellungen liegen — (noch nicht zugeordnet)

## OPTIONEN > Sicherungseinstellungen > Zwischenstände aufheben

- ⬜ Wie lange (Tage) — (noch nicht zugeordnet)
- ⬜ Zwischenstände löschen — (noch nicht zugeordnet)

## OPTIONEN > Sicherungseinstellungen > Was im Speicher steht

- ⬜ Sichern und zurückholen — (noch nicht zugeordnet)

## OPTIONEN > Speicherort für Dateien > Speicherort für Dateien

- ⬜ Ordner zum Speichern — (noch nicht zugeordnet)
- ⬜ Eigene Vorlagen — (noch nicht zugeordnet)

## OPTIONEN > Änderungen verfolgen > Änderungen verfolgen

- ⬜ Änderungen verfolgen — Band: Überprüfen ▸ Änderungen
- ⬜ Markup anzeigen — Band: Überprüfen ▸ Änderungen

## OPTIONEN > Änderungen verfolgen > Markup

- ⬜ Einfügungen — (noch nicht zugeordnet)
- ⬜ Löschvorgänge — (noch nicht zugeordnet)
- ⬜ Geänderte Zeilen — (noch nicht zugeordnet)
- ⬜ Farbe — (noch nicht zugeordnet)

## OPTIONEN > Änderungen verfolgen > Sprechblasen

- ⬜ Sprechblasen verwenden — (noch nicht zugeordnet)
- ⬜ Empfohlene Breite verwenden — (noch nicht zugeordnet)
- ⬜ Bevorzugte Breite (mm) — (noch nicht zugeordnet)
- ⬜ Seitenrand — (noch nicht zugeordnet)
- ⬜ Verbindungslinien zum Text anzeigen — (noch nicht zugeordnet)

## OPTIONEN > Änderungen verfolgen > Drucken (mit Sprechblasen)

- ⬜ Papierausrichtung — (noch nicht zugeordnet)

## OPTIONEN > In PDF exportieren > Exportoptionen

- ⬜ Hyperlinks — (noch nicht zugeordnet)
- ⬜ Überschriften als Lesezeichen — (noch nicht zugeordnet)
- ⬜ Kommentare mitnehmen — (noch nicht zugeordnet)
- ⬜ Dokumenteigenschaften mitnehmen — (noch nicht zugeordnet)
- ⬜ Verknüpfung von Fuß- und Endnoten — (noch nicht zugeordnet)
- ⬜ Textmarken übernehmen — (noch nicht zugeordnet)
- ⬜ Andere Formatvorlagen in Lesezeichen umwandeln — (noch nicht zugeordnet)
- ⬜ Eigene Formatvorlagen in Lesezeichen umwandeln — (noch nicht zugeordnet)
- ⬜ PDF nach dem Export öffnen — (noch nicht zugeordnet)

## OPTIONEN > Benutzerinformationen > Benutzerdaten

- ⬜ Wer schreibt — (noch nicht zugeordnet)
- ⬜ Initialen — (noch nicht zugeordnet)
- ⬜ Diese Benutzerinformationen verwenden — (noch nicht zugeordnet)

## OPTIONEN > Drucken > Druckoptionen

- ⬜ Womit das Druckfenster aufgeht — (noch nicht zugeordnet)
- ⬜ Hohe Qualität — (noch nicht zugeordnet)
- ⬜ Umgekehrte Reihenfolge — (noch nicht zugeordnet)
- ⬜ Zeichnungsobjekte drucken — (noch nicht zugeordnet)
- ⬜ Hintergrundfarben und -bilder drucken — (noch nicht zugeordnet)
- ⬜ Leere Seiten mitdrucken — (noch nicht zugeordnet)
- ⬜ Felder vor dem Drucken aktualisieren — (noch nicht zugeordnet)
- ⬜ Feldfunktionen drucken — (noch nicht zugeordnet)
- ⬜ Ausgeblendeter Text — (noch nicht zugeordnet)
- ⬜ Autor der Kommentare und Überarbeitungen — (noch nicht zugeordnet)

## OPTIONEN > Drucken > Nur für das aktuelle Dokument

- ⬜ Nur Formulardaten drucken — (noch nicht zugeordnet)

## OPTIONEN > Drucken > Duplexdruck

- ⬜ Blattvorderseite — (noch nicht zugeordnet)
- ⬜ Blattrückseite — (noch nicht zugeordnet)

## OPTIONEN > Rechtschreibprüfung > Rechtschreibprüfung

- ⬜ Sprache für die Prüfung — (noch nicht zugeordnet)
- ⬜ Rechtschreibung während der Eingabe prüfen — (noch nicht zugeordnet)
- ⬜ Immer Korrekturvorschläge unterbreiten — (noch nicht zugeordnet)
- ⬜ Grammatik mitprüfen — (noch nicht zugeordnet)
- ⬜ Wörter in GROSSBUCHSTABEN ignorieren — (noch nicht zugeordnet)
- ⬜ Wörter mit Zahlen ignorieren — (noch nicht zugeordnet)
- ⬜ Internet- und Netzwerkpfade ignorieren — (noch nicht zugeordnet)
- ⬜ Weggewinkte Funde wieder anzeigen — (noch nicht zugeordnet)

## OPTIONEN > Rechtschreibprüfung > Benutzerwörterbuch

- ⬜ Was das Programm gelernt hat — (noch nicht zugeordnet)

## OPTIONEN > Sicherheit > Kennwortschutz

- ⬜ Dokumentkennwort — (noch nicht zugeordnet)
- ⬜ Bearbeitung sperren — Band: Überprüfen ▸ Schützen

## OPTIONEN > Sicherheit > Datenschutz

- ⬜ Ausgeblendete Markups beim Öffnen anzeigen — (noch nicht zugeordnet)
- ⬜ Beim Speichern persönliche Daten entfernen — (noch nicht zugeordnet)

## OPTIONEN > Schreibhilfe und KI > Prüfung und KI

- ⬜ API-Schlüssel — (noch nicht zugeordnet)
- ⬜ KI-Modell — (noch nicht zugeordnet)
- ⬜ Für wen der Text ist — (noch nicht zugeordnet)
- ⬜ Verbrauch — (noch nicht zugeordnet)
- ✅ Übersetzen — Band: Seitenleiste ▸ Sprache

## OPTIONEN > Gedächtnis > Gedächtnis

- ⬜ Gelernte Schreibweisen — (noch nicht zugeordnet)

## OPTIONEN > Menüband anpassen

- ⬜ Befehle auswählen — (noch nicht zugeordnet)
- ⬜ Menüband anpassen — (noch nicht zugeordnet)

## OPTIONEN > Symbolleiste für den Schnellzugriff

- ⬜ Befehle auswählen — (noch nicht zugeordnet)
- ⬜ Derzeit angezeigte Optionen — (noch nicht zugeordnet)

## OPTIONEN > Erweitert > Erweitert

- ⬜ Was zusätzlich geholt wurde — (noch nicht zugeordnet)
