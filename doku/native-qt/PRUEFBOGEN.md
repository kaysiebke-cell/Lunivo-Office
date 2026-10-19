# Prüfbogen ↔ native Fassung

Erzeugt von `werkzeug/pruefbogen-abgleich.py` aus dem Prüfkatalog (415 Punkte). **✅ 324 · ◐ 66 · ⬜ 25**. ✅ = Befehl/Funktion vorhanden (einzeln getestet nur, wo `tests/` es belegt); ◐ = teilweise oder anders gelöst; ⬜ = offen.
Die Bilder des Bogens (bindend, 1 zu 1) liegen unter `doku/native-qt/pruefbogen/bilder/`.

## DATEI

- ✅ Neu — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Öffnen — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Zuletzt geöffnet — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ✅ Neu aus Vorlage — editor/vorlagen.py + widgets/vorlagen_dialog.py: 10 mitgelieferte Gerüste mit Lücken, eigene Vorlagen aus dem Ordner (test_vorlagen)
- ✅ Vorlagenordner — editor/vorlagen.py + widgets/vorlagen_dialog.py: 10 mitgelieferte Gerüste mit Lücken, eigene Vorlagen aus dem Ordner (test_vorlagen)
- ✅ Speichern — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Speichern unter — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Drucken — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Druckvorschau — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Als PDF exportieren — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ◐ Druckereinstellungen — Drucken öffnet den Systemdialog; Dokumentinformationen nur lesend
- ◐ Dokumenteigenschaften — Drucken öffnet den Systemdialog; Dokumentinformationen nur lesend
- ✅ Umbenennen — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ✅ Optionen (F9) — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ✅ Schließen — Datei-Reiter, ☰-Menü, Schnellzugriff; windows/main_window.py (test_main_window)
- ✅ Beenden — ☰-Menü (widgets/menue_tafel.py), Optionen F9
- ◐ Hilfe > Handbuch — Handbuch (Markdown) im Hilfefenster
- ✅ Hilfe > Tastenkürzel — widgets/hilfe_dialoge.py (test_vorlagen: Hilfe-Dialoge und Funktionstasten)
- ✅ Hilfe > Erweiterungen — widgets/hilfe_dialoge.py (test_vorlagen: Hilfe-Dialoge und Funktionstasten)
- ✅ Hilfe > Über Lunivo Office — ☰-Menü ▸ Hilfe ▸ Über

## MENÜ UND SCHNELLZUGRIFF

- ◐ Kein Datei-Reiter mehr — Widerspruch: die neue Struktur („1. DATEI“) hat einen Datei-Reiter — beides ist vorhanden
- ✅ ☰ Menü links vor den Reitern — widgets/menue_tafel.py, widgets/register_band.py
- ✅ ☰ Menü auch am Anfang der Symbolleiste — Ansicht ▸ Oberfläche ▸ Benutzeroberfläche: Symbolleisten (widgets/symbolleisten.py, test_main_window)
- ✅ Tafel mit zwei Spalten — widgets/menue_tafel.py, widgets/register_band.py
- ✅ Untermenü füllt die rechte Spalte, kein eigenes Fenster — widgets/menue_tafel.py, widgets/register_band.py
- ✅ Liste zuletzt verwendeter Dateien rechts — widgets/menue_tafel.py, widgets/register_band.py
- ✅ × nimmt einen Eintrag aus der Liste — widgets/menue_tafel.py, widgets/register_band.py
- ✅ ↻ holt die Liste neu — widgets/menue_tafel.py, widgets/register_band.py
- ✅ Als Bild exportieren (PNG) — befehle.exportierenPng: eine PNG je Seite (test_werkzeuge)
- ✅ Dokumentverschlüsselung — Datei ▸ Dokument schützen: DOCX-Verschlüsselung mit msoffcrypto-tool (test_formats, test_werkzeuge)
- ✅ Schnellzugriff in der Reiterzeile — widgets/menue_tafel.py, widgets/register_band.py

## START > Zwischenablage

- ✅ Einfügen — Band: Start ▸ Zwischenablage
- ⬜ Einfügen ohne Formatierung — (noch nicht zugeordnet)
- ✅ Ausschneiden — Band: Start ▸ Zwischenablage
- ✅ Kopieren — Band: Start ▸ Zwischenablage
- ✅ Format übertragen — Band: Start ▸ Zwischenablage
- ✅ Verlauf > Rückgängig — Schnellzugriff (wie im Bogen: dort statt im Reiter)
- ✅ Verlauf > Wiederholen — Schnellzugriff (wie im Bogen: dort statt im Reiter)

## START > Schriftart

- ✅ Schriftart — Felder im Band (widgets/register_band.py)
- ✅ Schriftgröße — Felder im Band (widgets/register_band.py)
- ✅ Schrift vergrößern — Band: Start ▸ Schriftart
- ✅ Schrift verkleinern — Band: Start ▸ Schriftart
- ✅ Formatierung löschen — Band: Start ▸ Schriftart
- ✅ Fett — Band: Start ▸ Schriftart
- ✅ Kursiv — Band: Start ▸ Schriftart
- ✅ Unterstrichen — Band: Start ▸ Schriftart
- ✅ Durchgestrichen — Band: Start ▸ Schriftart
- ✅ Hochgestellt — Band: Start ▸ Schriftart
- ✅ Tiefgestellt — Band: Start ▸ Schriftart
- ✅ Hervorheben — Band: Start ▸ Schriftart
- ✅ Schriftfarbe — Band: Start ▸ Schriftart
- ✅ Groß-/Kleinschreibung — Band: Start ▸ Schriftart
- ✅ Unterstreichungsart — befehle.menue_unterstrichKlappe (Einfach, gestrichelt, gepunktet, Strich-Punkt, Wellenlinie); DOCX-Roundtrip getestet (test_docx_roundtrip)
- ✅ Texteffekte — Band: Start ▸ Schriftart

## START > Absatz

- ✅ Aufzählung — Band: Start ▸ Absatz
- ✅ Nummerierung — Band: Start ▸ Absatz
- ✅ Einzug verringern — Band: Start ▸ Absatz ▸ Einzug & Listenebene
- ✅ Einzug vergrößern — Band: Start ▸ Absatz ▸ Einzug & Listenebene
- ✅ Listenebene erhöhen — Band: Start ▸ Absatz ▸ Einzug & Listenebene
- ✅ Listenebene verringern — Band: Start ▸ Absatz ▸ Einzug & Listenebene
- ✅ Linksbündig — Band: Start ▸ Absatz
- ✅ Zentriert — Band: Start ▸ Absatz
- ✅ Rechtsbündig — Band: Start ▸ Absatz
- ✅ Blocksatz — Band: Start ▸ Absatz
- ✅ Zeilenabstand — Band: Start ▸ Absatz
- ✅ Sortieren — Band: Start ▸ Absatz
- ✅ Steuerzeichen — Band: Start ▸ Absatz

## START > Absatzlayout

- ✅ Zeilenabstand — Band: Start ▸ Absatz
- ✅ Einzug genau — Absatz-Dialog mit zwei Karteireitern und Vorschau; „Absatz nicht trennen“ u. ä. sind Qt-bedingt gesperrt
- ✅ Absatzrahmen — B_RAHMEN: Editor, PDF/Druck und DOCX pBdr (test_werkzeuge, mit LibreOffice geprüft)
- ✅ Absatzschattierung — Band: Start ▸ Absatz

## START > Einstellungen

- ✅ Optionen — Datei-Reiter / ☰ / F9

## START > Stile & Bearbeiten

- ✅ Formatvorlage auswählen — Stilkatalog + Feld im Band
- ✅ Formatvorlagen verwalten — editor/stile.py + StileVerwaltenDialog; wirkt auf alle Absätze der Vorlage (test_editor)
- ✅ Suchen — Band: Start ▸ Suchen ▸ Suchen oder ersetzen
- ✅ Ersetzen — Band: Start ▸ Suchen ▸ Suchen oder ersetzen
- ⬜ Suchen und Ersetzen — (noch nicht zugeordnet)
- ✅ Alles auswählen — Band: Start ▸ Auswählen ▸ Auswählen
- ✅ Objekte auswählen — befehle.objekteWaehlen (test_main_window)

## EINFÜGEN

- ✅ Deckblatt — editor/einfuegen.py, storage/bausteine.py (test_einfuegen)
- ✅ Leere Seite — Band: Einfügen ▸ Seiten
- ✅ Seitenumbruch — Band: Einfügen ▸ Seiten, Seitenlayout ▸ Seite einrichten ▸ Umbrüche
- ✅ Tabelle einfügen — Band: Einfügen ▸ Tabellen
- ✅ Schnelltabelle — editor/einfuegen.py, storage/bausteine.py (test_einfuegen)
- ⬜ Tabellenblatt — ausgeschlossen: nur Textverarbeitung (Vorgabe des Projekts)
- ✅ Bild — Band: Einfügen ▸ Illustrationen
- ◐ Zeichnen — entsteht als Bild mit Alternativtext (Formen, Verläufe, QtCharts) — nachträglich nicht als Zeichnung/Diagramm bearbeitbar (test_einfuegen)
- ◐ Diagramm — entsteht als Bild mit Alternativtext (Formen, Verläufe, QtCharts) — nachträglich nicht als Zeichnung/Diagramm bearbeitbar (test_einfuegen)
- ◐ Bildschirmfoto — ganzer Bildschirm oder Bereich (befehle.screenshot); nur der Einfügeweg ist getestet, nicht die Aufnahme am echten Bildschirm
- ⬜ SmartArt — nicht übertragen (Grafik-Vorlagen; keine Entsprechung in Qt)
- ✅ Piktogramm — befehle.piktogramm: 1800 Lucide-Symbole als Bild mit Alternativtext (test_einfuegen)
- ◐ WordArt — entsteht als Bild mit Alternativtext (Formen, Verläufe, QtCharts) — nachträglich nicht als Zeichnung/Diagramm bearbeitbar (test_einfuegen)
- ✅ Hyperlink — Band: Einfügen ▸ Links
- ✅ Lesezeichen / Textmarke — Band: Einfügen ▸ Links
- ✅ Querverweis — Band: Einfügen ▸ Links, Verweise ▸ Beschriftungen
- ✅ Kopfzeile — Dialoge (widgets/dialogs.py), PDF/Druck/DOCX getestet
- ✅ Fußzeile — Dialoge (widgets/dialogs.py), PDF/Druck/DOCX getestet
- ✅ Seitenzahl — Band: Einfügen ▸ Kopf- und Fußzeile
- ◐ Textfeld — einzellige Tabelle mit Rahmen; frei schwebende Textfelder kennt Qt nicht
- ✅ Textbaustein — editor/einfuegen.py, storage/bausteine.py (test_einfuegen)
- ✅ Schnellbaustein — editor/einfuegen.py, storage/bausteine.py (test_einfuegen)
- ◐ Initiale — erster Buchstabe vergrößert in der Zeile; hängende Initiale kennt Qt nicht
- ◐ Datum — Datum einfügen; Fenster mit Formatliste/Sprache fehlt
- ◐ Uhrzeit — Datum einfügen; Fenster mit Formatliste/Sprache fehlt
- ✅ Text aus Datei — editor/einfuegen.py, storage/bausteine.py (test_einfuegen)
- ✅ Sonderzeichen — Band: Einfügen ▸ Symbole
- ◐ Formel — einfache Schreibweise (hoch/tief, Wurzel, Bruch, Griechisch) als Text mit Formatierung; kein Formeleditor wie in Word

## SEITENLAYOUT

- ✅ Seitenränder — Band: Seitenlayout ▸ Seitenhintergrund
- ✅ Ausrichtung — Band: Seitenlayout ▸ Seite einrichten
- ✅ Papierformat — Reiter Seitenlayout ▸ Größe (Befehle.w_setzePapier)
- ✅ Spalten — 1–4 Spalten live im Editor (editor_widget._sp_*), Seitenansicht, Druck, PDF, DOCX w:cols/Spaltenumbruch (test_spalten_editor, test_werkzeuge; mit LibreOffice geprüft). Gilt für das ganze Dokument; bei mehreren Spalten wirkt ein Seitenumbruch wie ein Spaltenumbruch
- ✅ Umbruch > Seitenumbruch — Band: Einfügen ▸ Seiten, Seitenlayout ▸ Seite einrichten ▸ Umbrüche
- ✅ Umbruch > Spaltenumbruch — 1–4 Spalten live im Editor (editor_widget._sp_*), Seitenansicht, Druck, PDF, DOCX w:cols/Spaltenumbruch (test_spalten_editor, test_werkzeuge; mit LibreOffice geprüft). Gilt für das ganze Dokument; bei mehreren Spalten wirkt ein Seitenumbruch wie ein Spaltenumbruch
- ◐ Umbruch > Abschnittsumbruch — nur „Nächste Seite“ (Seitenumbruch); Abschnitte kennt Qt nicht
- ✅ Einzug — Band: Seitenlayout ▸ Absatz
- ✅ Absatzabstand — Band: Seitenlayout ▸ Absatz
- ✅ Zeilennummern — Band: Seitenlayout ▸ Seite einrichten
- ◐ Silbentrennung — pyphen setzt weiche Trennstellen in Seitenansicht, Druck, PDF; DOCX autoHyphenation (test_werkzeuge). Die Bearbeitungsansicht zeigt keine Trennstriche
- ◐ Textumbruch — Bild links/rechts vom Text umflossen oder in eigener Zeile (editor/umbruch.py, DOCX wp:anchor wrapSquare, test_werkzeuge); „Hinter/vor dem Text“ und freie Position fehlen
- ✅ Seitenfarbe — Band: Seitenlayout ▸ Seitenhintergrund
- ✅ Wasserzeichen — Band: Seitenlayout ▸ Seitenhintergrund
- ✅ Seitenrahmen — befehle.seitenrahmen, pagination.seitenschmuck, DOCX pgBorders (test_docx_roundtrip, test_pdf)
- ◐ Bild/Objekt anordnen — nur Ausrichten und Drehen/Spiegeln (Bildtools); kein Gruppieren, keine Ebenen

## REFERENZEN

- ✅ Inhaltsverzeichnis — Band: Verweise ▸ Inhaltsverzeichnis
- ✅ Verzeichnisse aktualisieren — Band: Verweise ▸ Inhaltsverzeichnis
- ✅ Fußnote — echte DOCX-Fuß-/Endnoten (gelesen und geschrieben, mit LibreOffice geprüft); Fußnoten am Seitenfuß in Seitenansicht, Druck und PDF (bei mehreren Spalten gesammelt am Ende)
- ✅ Endnote — echte DOCX-Fuß-/Endnoten (gelesen und geschrieben, mit LibreOffice geprüft); Fußnoten am Seitenfuß in Seitenansicht, Druck und PDF (bei mehreren Spalten gesammelt am Ende)
- ✅ Nächste Note — Band: Verweise ▸ Fußnoten
- ✅ Vorige Note — Band: Verweise ▸ Fußnoten
- ✅ Notenbereich — Band: Verweise ▸ Fußnoten
- ✅ Zitat einfügen — Band: Verweise ▸ Zitate und Literatur
- ✅ Neue Quelle — Band: Verweise ▸ Zitate und Literatur
- ✅ Quellen verwalten — Band: Verweise ▸ Zitate und Literatur
- ✅ Zitierweise — Band: Verweise ▸ Zitate und Literatur
- ✅ Literaturverzeichnis — Band: Verweise ▸ Zitate und Literatur
- ✅ Beschriftung — Band: Verweise ▸ Beschriftungen
- ✅ Abbildungsverzeichnis — Band: Verweise ▸ Beschriftungen
- ✅ Querverweis — Band: Einfügen ▸ Links, Verweise ▸ Beschriftungen
- ✅ Indexeintrag — Band: Verweise ▸ Index
- ✅ Stichwortverzeichnis — Band: Verweise ▸ Index

## ÜBERPRÜFEN

- ✅ Prüfen — Band: Schreibhilfe ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Gründlich prüfen — Band: Schreibhilfe ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Rechtschreibung — Band: Überprüfen ▸ Dokumentprüfung
- ✅ Thesaurus — Band: Schreibhilfe ▸ Sprache, Überprüfen ▸ Dokumentprüfung
- ✅ Wörter zählen — Band: Überprüfen ▸ Dokumentprüfung
- ✅ Korrektursprache — Band: Überprüfen ▸ Sprache
- ✅ Barrierefreiheit prüfen — Band: Überprüfen ▸ Barrierefreiheit
- ✅ Neuer Kommentar — Band: Überprüfen ▸ Kommentare
- ✅ Nächster Kommentar — Band: Überprüfen ▸ Kommentare
- ✅ Voriger Kommentar — Band: Überprüfen ▸ Kommentare
- ✅ Kommentar löschen — Band: Überprüfen ▸ Kommentare
- ✅ Alle Kommentare löschen — Band: Überprüfen ▸ Kommentare
- ✅ Änderungen verfolgen — Band: Überprüfen ▸ Änderungen
- ✅ Markup anzeigen — Band: Überprüfen ▸ Änderungen
- ✅ Überarbeitungsbereich — Band: Überprüfen ▸ Änderungen
- ✅ Änderung annehmen — Band: Überprüfen ▸ Änderungen
- ✅ Änderung ablehnen — Band: Überprüfen ▸ Änderungen
- ✅ Nächste Änderung — Band: Überprüfen ▸ Änderungen
- ✅ Vorige Änderung — Band: Überprüfen ▸ Änderungen
- ✅ Alle annehmen — Band: Überprüfen ▸ Änderungen
- ✅ Alle verwerfen — Band: Überprüfen ▸ Änderungen
- ✅ Bearbeitung sperren — Band: Überprüfen ▸ Schützen

## SCHREIBHILFE (Lunivo)

- ✅ Dokumentprüfung > Prüfen — Band: Schreibhilfe ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Dokumentprüfung > Gründlich prüfen — Band: Schreibhilfe ▸ Prüfen ▸ Dokumentprüfung, Überprüfen ▸ Dokumentprüfung
- ✅ Dokumentprüfung > Welche Hilfe wann — Band: Schreibhilfe ▸ Prüfen ▸ Dokumentprüfung
- ✅ Beim Schreiben > Rechtschreibprüfung — Band: Schreibhilfe ▸ Beim Schreiben
- ✅ Beim Schreiben > Wortvorhersage — Band: Schreibhilfe ▸ Beim Schreiben
- ✅ Beim Schreiben > AutoKorrektur — Band: Schreibhilfe ▸ Beim Schreiben
- ✅ Vorlesen > Vorlesen — Band: Schreibhilfe ▸ Vorlesen, Schreibhilfe ▸ Vorlesen ▸ Vorlesen
- ✅ Vorlesen > Ab hier vorlesen — Band: Schreibhilfe ▸ Vorlesen ▸ Vorlesen
- ✅ Vorlesen > Anhalten — Band: Schreibhilfe ▸ Vorlesen ▸ Vorlesen
- ✅ Vorlesen > Stimme und Tempo — Band: Schreibhilfe ▸ Vorlesen ▸ Vorlesen
- ⬜ KI > KI-Korrektur — (noch nicht zugeordnet)
- ✅ KI > Vorschläge — Seitenleiste / KI-Reiter (test_schreibhilfe)
- ✅ Anzeigen > Seitenleiste Schreibhilfe — Band: Schreibhilfe ▸ Anzeigen
- ✅ Anzeigen > Optionen — Seitenleiste / KI-Reiter (test_schreibhilfe)

## SENDUNGEN (Lunivo)

- ✅ Umschlag — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ✅ Etiketten — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ✅ Seriendruck-Assistent — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ✅ Seriendruckfeld — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ✅ Adressblock — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ✅ Regeln — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ✅ Ergebnisse anzeigen — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ◐ Formular > Textfeld — als formatierter Text ohne Funktion (Qt kennt keine Formularsteuerelemente)
- ✅ Formular > Kontrollkästchen — editor/sendungen.py + widgets/sendungen_dialoge.py (test_sendungen); Reiter „Sendungen“ ist nach Register anpassen sichtbar, sonst über die Menüleiste
- ◐ Formular > Schaltfläche — als formatierter Text ohne Funktion (Qt kennt keine Formularsteuerelemente)

## ANSICHT

- ✅ Drucklayout — Band: Ansicht ▸ Dokumentansichten
- ✅ Lesemodus — Band: Ansicht ▸ Dokumentansichten, Schreibhilfe ▸ Lesen
- ✅ Zwei Seiten — Band: Ansicht ▸ Dokumentansichten
- ✅ Weblayout — Band: Ansicht ▸ Dokumentansichten
- ✅ Gliederung — Band: Ansicht ▸ Dokumentansichten
- ✅ Lineal — Band: Ansicht ▸ Anzeigen
- ✅ Vertikales Lineal — Band: Ansicht ▸ Anzeigen
- ✅ Gitternetzlinien — Band: Ansicht ▸ Anzeigen
- ✅ Navigationsbereich — Band: Ansicht ▸ Anzeigen
- ✅ Textbegrenzungen — Band: Ansicht ▸ Anzeigen
- ✅ Seitenleiste Schreibhilfe — Band: Schreibhilfe ▸ Anzeigen
- ✅ Lesehilfe — Band: Schreibhilfe ▸ Lesen
- ✅ Zeilenfokus — Band: Schreibhilfe ▸ Lesen
- ✅ Vergrößern — Band: Ansicht ▸ Zoom
- ✅ Verkleinern — Band: Ansicht ▸ Zoom
- ✅ 100 % — Band: Ansicht ▸ Zoom
- ✅ Seitenbreite — Band: Ansicht ▸ Zoom
- ✅ Eine Seite — Band: Ansicht ▸ Zoom
- ✅ Zoom — Band: Ansicht ▸ Zoom
- ✅ Neues Fenster — Band: Ansicht ▸ Fenster
- ✅ Anordnen — Band: Ansicht ▸ Fenster
- ✅ Nebeneinander — Band: Ansicht ▸ Fenster, Ansicht ▸ Fenster ▸ Anordnen
- ✅ Untereinander — Band: Ansicht ▸ Fenster, Ansicht ▸ Fenster ▸ Anordnen
- ✅ Kacheln — Band: Ansicht ▸ Fenster, Ansicht ▸ Fenster ▸ Anordnen
- ✅ Fensterliste — Band: Ansicht ▸ Fenster
- ✅ Helligkeit > Wie das System — Band: Ansicht ▸ Helligkeit
- ✅ Helligkeit > Immer hell — Band: Ansicht ▸ Helligkeit
- ✅ Helligkeit > Immer dunkel — Band: Ansicht ▸ Helligkeit
- ✅ Oberfläche > Register anpassen — widgets/oberflaeche_dialoge.py, Ansicht ▸ Oberfläche (test_main_window)
- ✅ Oberfläche > Symbol austauschen — widgets/oberflaeche_dialoge.py, Ansicht ▸ Oberfläche (test_main_window)
- ✅ Oberfläche > Benutzeroberfläche — widgets/oberflaeche_dialoge.py, Ansicht ▸ Oberfläche (test_main_window)
- ✅ Oberfläche > Menüleiste — Band: Ansicht ▸ Oberfläche
- ✅ Oberfläche > Symbolleisten — widgets/oberflaeche_dialoge.py, Ansicht ▸ Oberfläche (test_main_window)
- ✅ Oberfläche > Vorlagen zurücksetzen — widgets/oberflaeche_dialoge.py, Ansicht ▸ Oberfläche (test_main_window)

## KONTEXTTABELLEN

- ◐ Tabellenwerkzeuge — Reiter erscheint in der Tabelle (test_tabellentools_wirken); ohne Tabellenformatvorlagen
- ⬜ Zeichentools — nicht übertragen
- ⬜ Diagrammtools — nicht übertragen
- ⬜ SmartArt-Tools — nicht übertragen
- ⬜ Gleichungswerkzeuge — nicht übertragen
- ◐ Kopf- und Fußzeilenwerkzeuge — Reiter mit „Erste Seite anders“ (PDF und DOCX); „Gerade/ungerade“ fehlt

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
- ⬜ Lunivo-Regeln verwenden statt Browser — (noch nicht zugeordnet)
- ✅ Benutzerwörter in Rechtschreibung beachten — services/pruefung.py (test_schreibhilfe)
- ◐ Ignorierte Wörter in Rechtschreibung beachten — inRuhe/weggewinkt beachtet; einheitliches Fund-dict
- ◐ Fehler als unified language-issue — inRuhe/weggewinkt beachtet; einheitliches Fund-dict

## LANGUAGE BRIDGE (Grammar Engine)

- ✅ Dieselbe Sprachkontext wie Spelling — gleiche Engine, regeln.json gelesen
- ✅ Grammatikregeln aus regeln.js nutzen — gleiche Engine, regeln.json gelesen
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
- ✅ Kontextmenü für Fehler-Aktionen — editor_widget.contextMenuEvent + WritingAssistant.erweitere_menue (test_schreibhilfe)
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

- ✅ Lineal — widgets/lineal.py: Millimeter, Ränder und Einzüge ziehbar (test_main_window)
- ✅ Vertikales Lineal — widgets/lineal.py: Millimeter, Ränder und Einzüge ziehbar (test_main_window)
- ✅ Navigationsbereich — Optionen ▸ Wie im WPS Writer ▸ Ansicht
- ✅ Textbegrenzungen — Optionen ▸ Wie im WPS Writer ▸ Ansicht
- ✅ Gitternetzlinien — befehle.netzlinien, editor._gitter_zeichnen
- ✅ Statusleiste — Optionen ▸ Wie im WPS Writer ▸ Ansicht (ui/statusleiste → ansicht_optionen_anwenden)
- ✅ Seitenleiste beim Start — Optionen ▸ Wie im WPS Writer ▸ Ansicht (ui/seitenleiste, main_window)
- ◐ QuickInfo — Qt zeigt Kurzinfos immer; kein Schalter
- ⬜ Live-Vorschau — nicht übertragen (in den Optionen als gesperrte Zeile sichtbar)
- ✅ Minisymbolleiste bei Auswahl — widgets/mini_leiste.py; ui/mini_auswahl, ui/mini_rechtsklick (test_schreibhilfe)
- ✅ Minisymbolleiste bei Rechtsklick — widgets/mini_leiste.py; ui/mini_auswahl, ui/mini_rechtsklick (test_schreibhilfe)
- ✅ Tipp für Kopf- bzw. Fußzeile — ui/kopffuss_tipp, ui/kopffuss_anzeigen: Kopf-/Fußzeile im Rand, Tipp und Doppelklick (editor_widget; test_anzeige_extra)

## OPTIONEN > Ansicht > Druckoptionen

- ✅ Hervorhebungen drucken — drucken/hervorhebungen, textgrenzen, zuschnitt, textmarken → pagination.render (test_werkzeuge)
- ✅ Textbegrenzungen drucken — drucken/hervorhebungen, textgrenzen, zuschnitt, textmarken → pagination.render (test_werkzeuge)
- ✅ Zuschnittsmarken anzeigen — drucken/hervorhebungen, textgrenzen, zuschnitt, textmarken → pagination.render (test_werkzeuge)
- ✅ Feldfunktionen drucken — drucken/felder_code (anzeige_extra.feldcodes_einsetzen), ui/feldschattierung (zusatz_editor._overlays_neu; test_anzeige_extra)
- ✅ Textmarken drucken — drucken/hervorhebungen, textgrenzen, zuschnitt, textmarken → pagination.render (test_werkzeuge)
- ✅ Feldschattierung — drucken/felder_code (anzeige_extra.feldcodes_einsetzen), ui/feldschattierung (zusatz_editor._overlays_neu; test_anzeige_extra)

## OPTIONEN > Ansicht > Formatierungszeichen

- ✅ Alle anzeigen — ui/steuerzeichen, toggle_marks (¶)
- ◐ Absatzmarken — Qt schaltet Absatzmarken, Leerzeichen und Tabs nur gemeinsam
- ◐ Leerzeichen — Qt schaltet Absatzmarken, Leerzeichen und Tabs nur gemeinsam
- ◐ Tabstoppzeichen — Qt schaltet Absatzmarken, Leerzeichen und Tabs nur gemeinsam
- ✅ Objektanker — ui/objektanker (⚓ neben umflossenen Bildern), P_VERSTECKT + VersteckterText, DOCX w:vanish (test_anzeige_extra)
- ✅ Ausgeblendeter Text — ui/objektanker (⚓ neben umflossenen Bildern), P_VERSTECKT + VersteckterText, DOCX w:vanish (test_anzeige_extra)

## OPTIONEN > Ansicht > Menübandoptionen

- ✅ Doppelklick blendet das Band aus — RegisterBand.einklappen_umschalten (test_main_window)
- ✅ Strg+Klick folgt einem Verweis — editor_widget.mouseReleaseEvent, ui/strg_klick_link

## OPTIONEN > Ansicht > Darstellung

- ✅ Schrift und Helligkeit — Optionen ▸ Wie im WPS Writer ▸ Ansicht (theme, ui/icongroesse, icons.FAKTOR)
- ✅ Größe der Symbole — Optionen ▸ Wie im WPS Writer ▸ Ansicht (theme, ui/icongroesse, icons.FAKTOR)
- ◐ Schrift der Bedienung — nur die Schriftgröße (ui/bedienschrift_groesse); Schriftart folgt dem System
- ✅ Benutzeroberfläche — Optionen ▸ Menüband anpassen ▸ Benutzeroberfläche wählen

## OPTIONEN > Bearbeiten > Bearbeitungsoptionen

- ✅ Wortweise markieren — bearbeiten/wortweise, editor_widget._wortweise (test_editor)
- ◐ Text mit der Maus verschieben — Qt-Standard (Ziehen und Ablegen), nicht abschaltbar
- ✅ Tippen ersetzt die Auswahl — bearbeiten/tippen_ersetzt (editor_widget.keyPressEvent)
- ⬜ Maximale Rückgängig-Schritte — Qt bietet keine Begrenzung des Rückgängig-Stapels pro Dokument

## OPTIONEN > Bearbeiten > AutoFormat

- ✅ Automatisch nummerierte Listen — autoformat/liste, autoformat/punkte (test_editor)
- ✅ Aufzählungen erkennen — autoformat/liste, autoformat/punkte (test_editor)
- ✅ Zahl automatisch im Kreis — schreibhilfe/akKreiszahl: (1) → ① bis (20) → ⑳ (editor._kreiszahl; test_anzeige_extra)

## OPTIONEN > Bearbeiten > AutoKorrektur

- ✅ AutoKorrektur — Band: Schreibhilfe ▸ Beim Schreiben
- ✅ Typografische Anführungszeichen — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ✅ Gedankenstriche — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ✅ Auslassungspunkte — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ✅ Jeden Satz mit einem Großbuchstaben beginnen — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ✅ Wochentage immer großschreiben — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ✅ Englische Ordnungszahlen hochstellen — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ✅ Feststelltaste korrigieren — services/autokorrektur.py, Optionen ▸ Bearbeiten (test_schreibhilfe)
- ◐ Internet- und Netzwerkpfade durch Hyperlinks ersetzen — editor_widget._autokorr_extras/keyPressEvent — verdrahtet, noch ohne eigenen Test
- ◐ Leerzeichen am Absatzanfang mit Erstzeileneinzug — editor_widget._autokorr_extras/keyPressEvent — verdrahtet, noch ohne eigenen Test
- ✅ Leerzeichenformat am Ende rechtsbündiger Zeilen anpassen — schreibhilfe/akRechtsLeer: Leerzeichen am Zeilenende rechtsbündiger Absätze fallen beim Umbruch weg (editor._rechts_leerzeichen_weg)
- ◐ Bei zentriertem Ausrichten Erstzeileneinzug löschen — editor_widget._autokorr_extras/keyPressEvent — verdrahtet, noch ohne eigenen Test
- ◐ Tabulator und Rücktaste setzen den Einzug — editor_widget._autokorr_extras/keyPressEvent — verdrahtet, noch ohne eigenen Test
- ✅ Wortvorhersage — Band: Schreibhilfe ▸ Beim Schreiben

## OPTIONEN > Bearbeiten > Ausschneiden und Einfügen

- ✅ Schaltfläche nach dem Einfügen — editor._einfuegen_mit/_einfuegen_schaltflaeche, bearbeiten/einfuegen_standard (test_editor)
- ◐ Mittlere Maustaste fügt ein — unter Linux/X11 durch Qt (Primärauswahl), nicht schaltbar
- ✅ Standardeinfügeformat — editor._einfuegen_mit/_einfuegen_schaltflaeche, bearbeiten/einfuegen_standard (test_editor)
- ✅ Ohne Formatierung einfügen — Befehle.einfuegenOhne

## OPTIONEN > Allgemein und Speichern > Speichern

- ✅ Dateien als Standard speichern — speichern/standard (DOCX/TXT), _ask_path

## OPTIONEN > Allgemein und Speichern > Schrift für neuen Text

- ✅ Schrift — standard/schrift, standard/groesse (new_document)
- ✅ Größe — standard/schrift, standard/groesse (new_document)

## OPTIONEN > Allgemein und Speichern > Allgemeine Optionen

- ✅ Maßeinheit — ui/masseinheit → dialogs._MassSpin (Seitenränder, Einzüge; intern mm)
- ◐ Bilder in der Datei nicht komprimieren — Bilder werden nie komprimiert; kein Schalter
- ⬜ Standard-Ausgabeziel — nicht übertragen

## OPTIONEN > Allgemein und Speichern > Webseite

- ✅ Webseitencodierung — speichern/codierung, formats.save(.html) (test_formats)

## OPTIONEN > Allgemein und Speichern > Kompatibilitätsoptionen

- ⬜ Seitenumbruch und Absatzmarke aufteilen — WPS-/Word-Altlayout; Qt hat keine Entsprechung
- ⬜ Hängenden Einzug nicht als Tabstopp verwenden — WPS-/Word-Altlayout; Qt hat keine Entsprechung
- ⬜ Nachstehende Leerstellen unterstreichen — WPS-/Word-Altlayout; Qt hat keine Entsprechung
- ⬜ Layout von Fußnoten wie Word 6/95/97 — WPS-/Word-Altlayout; Qt hat keine Entsprechung
- ⬜ Zeilenhöhe in Tabellen auf Rasterhöhe anpassen — WPS-/Word-Altlayout; Qt hat keine Entsprechung

## OPTIONEN > Sicherungseinstellungen > Sicherung

- ✅ Wann gesichert wird — sicherung/aktiv, autosave_seconds, Pfadanzeige
- ✅ Abstand (Minuten) — sicherung/aktiv, autosave_seconds, Pfadanzeige
- ✅ Wo die Einstellungen liegen — sicherung/aktiv, autosave_seconds, Pfadanzeige

## OPTIONEN > Sicherungseinstellungen > Zwischenstände aufheben

- ◐ Wie lange (Tage) — sicherung/staende + sicherung/tage, recovery.zwischenstand — noch ohne eigenen Test
- ◐ Zwischenstände löschen — alte Stände werden automatisch gelöscht; kein Knopf

## OPTIONEN > Sicherungseinstellungen > Was im Speicher steht

- ◐ Sichern und zurückholen — ZIP mit Gedächtnis (ohne API-Schlüssel) — noch ohne eigenen Test

## OPTIONEN > Speicherort für Dateien > Speicherort für Dateien

- ✅ Ordner zum Speichern — speichern/ordner
- ✅ Eigene Vorlagen — vorlagen/ordner (Optionen ▸ Allgemein und Speichern)

## OPTIONEN > Änderungen verfolgen > Änderungen verfolgen

- ✅ Änderungen verfolgen — Optionen ▸ Änderungen verfolgen; editor/zusatz_editor.py (test_zusatz_editor)
- ✅ Markup anzeigen — Optionen ▸ Änderungen verfolgen; editor/zusatz_editor.py (test_zusatz_editor)

## OPTIONEN > Änderungen verfolgen > Markup

- ✅ Einfügungen — aenderungen/ins_stil, del_stil, farbe (zusatz_editor._overlays_neu)
- ✅ Löschvorgänge — aenderungen/ins_stil, del_stil, farbe (zusatz_editor._overlays_neu)
- ✅ Geänderte Zeilen — aenderungen/balken: Balken am Rand der Zeilen mit Änderungen (Anzeige und Druck)
- ✅ Farbe — aenderungen/ins_stil, del_stil, farbe (zusatz_editor._overlays_neu)

## OPTIONEN > Änderungen verfolgen > Sprechblasen

- ✅ Sprechblasen verwenden — editor/sprechblasen.py + widgets/blasen_flaeche.py: Blasen im Seitenrand mit Autor, Datum, Text und Linien; Optionen ▸ Änderungen verfolgen ▸ Sprechblasen (test_sprechblasen)
- ✅ Empfohlene Breite verwenden — editor/sprechblasen.py + widgets/blasen_flaeche.py: Blasen im Seitenrand mit Autor, Datum, Text und Linien; Optionen ▸ Änderungen verfolgen ▸ Sprechblasen (test_sprechblasen)
- ✅ Bevorzugte Breite (mm) — editor/sprechblasen.py + widgets/blasen_flaeche.py: Blasen im Seitenrand mit Autor, Datum, Text und Linien; Optionen ▸ Änderungen verfolgen ▸ Sprechblasen (test_sprechblasen)
- ✅ Seitenrand — editor/sprechblasen.py + widgets/blasen_flaeche.py: Blasen im Seitenrand mit Autor, Datum, Text und Linien; Optionen ▸ Änderungen verfolgen ▸ Sprechblasen (test_sprechblasen)
- ✅ Verbindungslinien zum Text anzeigen — editor/sprechblasen.py + widgets/blasen_flaeche.py: Blasen im Seitenrand mit Autor, Datum, Text und Linien; Optionen ▸ Änderungen verfolgen ▸ Sprechblasen (test_sprechblasen)

## OPTIONEN > Änderungen verfolgen > Drucken (mit Sprechblasen)

- ✅ Papierausrichtung — sprechblasen/ausrichtung: Automatisch, Beibehalten, Querformat; die Seite wird verkleinert neben die Blasen gesetzt (pagination.blasen_geometrie; Druck und PDF)

## OPTIONEN > In PDF exportieren > Exportoptionen

- ✅ Hyperlinks — Qt schreibt Link-Annotationen (geprüft mit pypdf)
- ✅ Überschriften als Lesezeichen — pagination.lesezeichen_sammeln + gliederung_schreiben (pypdf nach QPdfWriter; test_werkzeuge)
- ✅ Kommentare mitnehmen — pdf/kommentare → PDF-Notizen; pdf/notenlinks → Sprungverweise Marke ↔ Note (pypdf; test_werkzeuge, test_fussnoten)
- ✅ Dokumenteigenschaften mitnehmen — pdf/eigenschaften, pdf/oeffnen (export_pdf author)
- ✅ Verknüpfung von Fuß- und Endnoten — pdf/kommentare → PDF-Notizen; pdf/notenlinks → Sprungverweise Marke ↔ Note (pypdf; test_werkzeuge, test_fussnoten)
- ✅ Textmarken übernehmen — pagination.lesezeichen_sammeln + gliederung_schreiben (pypdf nach QPdfWriter; test_werkzeuge)
- ✅ Andere Formatvorlagen in Lesezeichen umwandeln — pdf/lz_andere: Titel, Untertitel, Zitat (test_werkzeuge)
- ⬜ Eigene Formatvorlagen in Lesezeichen umwandeln — es gibt keine selbst angelegten Formatvorlagen, nur das Ändern der vorhandenen
- ✅ PDF nach dem Export öffnen — pdf/eigenschaften, pdf/oeffnen (export_pdf author)

## OPTIONEN > Benutzerinformationen > Benutzerdaten

- ✅ Wer schreibt — benutzer/name, benutzer/verwenden (_meta_fuer_speichern)
- ✅ Initialen — benutzer/initialen → Kommentare (main_window.autor_angaben)
- ✅ Diese Benutzerinformationen verwenden — benutzer/name, benutzer/verwenden (_meta_fuer_speichern)

## OPTIONEN > Drucken > Druckoptionen

- ⬜ Womit das Druckfenster aufgeht — nicht übertragen
- ◐ Hohe Qualität — pagination.render/print_document, main_window.druckoptionen — seiten_liste getestet, übrige nur verdrahtet
- ◐ Umgekehrte Reihenfolge — pagination.render/print_document, main_window.druckoptionen — seiten_liste getestet, übrige nur verdrahtet
- ✅ Zeichnungsobjekte drucken — drucken/zeichnungen, drucken/felder_code, drucken/versteckt → pagination.render (test_anzeige_extra)
- ◐ Hintergrundfarben und -bilder drucken — pagination.render/print_document, main_window.druckoptionen — seiten_liste getestet, übrige nur verdrahtet
- ◐ Leere Seiten mitdrucken — pagination.render/print_document, main_window.druckoptionen — seiten_liste getestet, übrige nur verdrahtet
- ◐ Felder vor dem Drucken aktualisieren — pagination.render/print_document, main_window.druckoptionen — seiten_liste getestet, übrige nur verdrahtet
- ✅ Feldfunktionen drucken — drucken/zeichnungen, drucken/felder_code, drucken/versteckt → pagination.render (test_anzeige_extra)
- ✅ Ausgeblendeter Text — drucken/zeichnungen, drucken/felder_code, drucken/versteckt → pagination.render (test_anzeige_extra)
- ✅ Autor der Kommentare und Überarbeitungen — sprechblasen/drucken: Blasen mit Autor und Datum im Ausdruck/PDF

## OPTIONEN > Drucken > Nur für das aktuelle Dokument

- ⬜ Nur Formulardaten drucken — Formulare nicht übertragen

## OPTIONEN > Drucken > Duplexdruck

- ✅ Blattvorderseite — drucken/duplex → seiten_liste (test_editor)
- ✅ Blattrückseite — drucken/duplex → seiten_liste (test_editor)

## OPTIONEN > Rechtschreibprüfung > Rechtschreibprüfung

- ◐ Sprache für die Prüfung — nur Deutsch
- ✅ Rechtschreibung während der Eingabe prüfen — Optionen ▸ Rechtschreibprüfung (test_schreibhilfe)
- ✅ Immer Korrekturvorschläge unterbreiten — schreibhilfe/vorschlaege → writing_assistant.erweitere_menue
- ◐ Grammatik mitprüfen — nur über „Gründlich prüfen“ mit LanguageTool (optional)
- ✅ Wörter in GROSSBUCHSTABEN ignorieren — Optionen ▸ Rechtschreibprüfung (test_schreibhilfe)
- ✅ Wörter mit Zahlen ignorieren — Optionen ▸ Rechtschreibprüfung (test_schreibhilfe)
- ✅ Internet- und Netzwerkpfade ignorieren — Optionen ▸ Rechtschreibprüfung (test_schreibhilfe)
- ✅ Weggewinkte Funde wieder anzeigen — Optionen ▸ Rechtschreibprüfung (test_schreibhilfe)

## OPTIONEN > Rechtschreibprüfung > Benutzerwörterbuch

- ✅ Was das Programm gelernt hat — Optionen ▸ Gedächtnis, storage/gelernt.py

## OPTIONEN > Sicherheit > Kennwortschutz

- ✅ Dokumentkennwort — formats.load/save mit msoffcrypto-tool (test_formats: Kennwort-Roundtrip)
- ◐ Bearbeitung sperren — nur für die Sitzung (main_window.toggle_sperre, test_main_window); kein Kennwort für die Freigabe

## OPTIONEN > Sicherheit > Datenschutz

- ◐ Ausgeblendete Markups beim Öffnen anzeigen — Markup ist beim Öffnen immer sichtbar (umschaltbar)
- ✅ Beim Speichern persönliche Daten entfernen — sicherheit/personendaten_weg (_meta_fuer_speichern)

## OPTIONEN > Schreibhilfe und KI > Prüfung und KI

- ✅ API-Schlüssel — Optionen ▸ Schreibhilfe und KI (test_ki; nur mit Attrappen gegen die echten Dienste getestet)
- ✅ KI-Modell — Optionen ▸ Schreibhilfe und KI (test_ki; nur mit Attrappen gegen die echten Dienste getestet)
- ✅ Für wen der Text ist — Optionen ▸ Schreibhilfe und KI (test_ki; nur mit Attrappen gegen die echten Dienste getestet)
- ✅ Verbrauch — Optionen ▸ Schreibhilfe und KI (test_ki; nur mit Attrappen gegen die echten Dienste getestet)
- ✅ Übersetzen — Band: Schreibhilfe ▸ Sprache

## OPTIONEN > Gedächtnis > Gedächtnis

- ✅ Gelernte Schreibweisen — Optionen ▸ Gedächtnis: Liste, Eintrag entfernen, alles vergessen

## OPTIONEN > Menüband anpassen

- ✅ Befehle auswählen — Register anpassen (ein-/ausblenden, ordnen)
- ✅ Menüband anpassen — Register anpassen (ein-/ausblenden, ordnen)

## OPTIONEN > Symbolleiste für den Schnellzugriff

- ✅ Befehle auswählen — Schnellzugriff anpassen (Haken je Befehl)
- ✅ Derzeit angezeigte Optionen — Schnellzugriff anpassen (Haken je Befehl)

## OPTIONEN > Erweitert > Erweitert

- ✅ Was zusätzlich geholt wurde — Optionen ▸ Erweitert (LibreOffice, LanguageTool, Sprachausgabe)
