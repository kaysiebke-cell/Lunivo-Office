# Umfang der GTK-Fassung

Aus dem alten Band (`oberflaeche/daten/register.js`) sind **183 Knöpfe** umgesetzt.
Was hier steht, ist **nicht** vorhanden und deshalb im Band auch nicht zu sehen (kein Knopf ohne Funktion):

- Seitenlayout ▸ Anordnen ▸ Gruppieren
- Ansicht ▸ Dokumentansichten ▸ Zwei Seiten

## Optionen (Menü ▸ Optionen, F9)

Aufbau, Beschriftungen und Erklärungen sind aus der alten Einstellungsseite übernommen (17 Seiten, `lunivo_native/daten/optionen.json`).
83 Einstellungen sind dort umgesetzt und wirken sofort. **Nicht übernommen**, weil es dafür hier noch nichts gibt:
Wortabstand, „Absatz beim Schreiben“, QuickInfo, Benutzeroberfläche „Symbolleisten“, Druckoptionen (Hervorhebungen, Textbegrenzungen,
Zuschnittsmarken, Feldfunktionen …), die Formatierungszeichen im Einzelnen, Kompatibilitätsoptionen, Sprechblasen der Überarbeitung,
automatische Listen im AutoFormat, „Tippen ersetzt die Auswahl“, Hyperlinks im PDF, Hohe Qualität, Hintergrundfarben drucken.

## Getestet (ausgeführt am 18.10.2026)

- Alle Befehle und Klappmenüs des Bands einzeln aufgerufen: 0 Fehler.
- Inhalt: Einfügen, Verzeichnisse, Kommentare, Änderungen verfolgen, Silbentrennung, Speichern/Laden als html, docx, odt, pdf: 24 von 24.
- Optionen: jede der 83 Einstellungen einmal geändert und zurückgesetzt: 0 Fehler.

## Nachtrag (Prüfkatalog-Angleichung)
- Neu: Dialoge „Unterstreichen“ (Linie/Farbe, gespeichert im Dokument), „Effekt“, „Sortieren“, „Absatz“ (Einzug/Abstand), „Als Bild exportieren“ (Jede Seite / Lange Grafik, Wasserzeichen, Qualität, Format, Ordner), „Eigenschaften“ (Allgemein / Zusammenfassung / Benutzerdefiniert) unter ☰ → Dokumentverschlüsselung, Sicherheit-Seite mit Hinweis und Datenschutzoptionen.
- Absatzrahmen sind echte Rahmen (ringsum, oben, unten, links, rechts; Linienart/Stärke/Farbe) und werden in HTML gespeichert.
- Farbtafeln nach WPS (Thema-Farben mit Abstufungen, Standardfarben, „Weitere Füllfarben“).
- Suchen/Ersetzen/Gehe zu sind ein Knopf „Suchen oder ersetzen“; die Suche sitzt in der linken Seitenleiste.
- Offen: gepunktete/gestrichelte Unterstreichung wird von GTK nur als einfache Linie gezeichnet; „Kennwort zum Ändern“, Abstand vor/nach im Absatz-Dialog (noch nicht gespeichert); Rest der Prüfkatalog-Bilder (Einfügen/Seitenlayout/Diagrammtools) noch nicht einzeln verglichen.
- SmartArt: Auswahlfenster mit Layout-Galerie, Vorschau und Beschreibung. Seitenrahmen: Auswahldialog (Breite, Linie, Farbe), Knopf heißt jetzt „Seitenrahmen“.
- Oberfläche rund 30 % größer (Schrift, Reiter, Menüs, Symbole).
