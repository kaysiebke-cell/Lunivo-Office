# Der Aufbau der Optionen

Quelle: `src/lunivo_writer/ui/dialogs/optionen.py`, Seiten in `optionen_seiten/`. Konzept und Begründung: [konzept-optionen.md](konzept-optionen.md).

Das Optionen-Fenster geht mit **F9** auf, oder über *Datei ▸ Optionen*. Links oben die **Suche** (Strg+F), darunter eine
flache Liste mit **sechs Seiten**, rechts die Seite. Jede Seite zeigt das Häufige; der Rest steht unter *Weitere Einstellungen*
(eingeklappt, mit Tab und Leertaste erreichbar). Änderungen gelten sofort.

**Hell und Dunkel** stehen ganz oben auf der Seite *Anzeige* (Hell · Dunkel · Wie das System, genau eine ist gewählt). Schneller
geht es ohne Optionen: **Strg+Umschalt+D**, *Ansicht ▸ Hell/Dunkel wechseln* oder der Knopf in der Statusleiste.

Als eigenes Fenster (aus *Weitere Einstellungen* der Seiten *Anzeige* und *Speichern*): Menüband anpassen, Symbolleiste für den
Schnellzugriff, Kennwort und Datenschutz, Änderungen verfolgen.

Frühere Seitennamen (`lesehilfe`, `ki`, `sprache` …) führen auf die neue Seite und klappen dort den passenden Bereich auf.

## Die Seiten

Auf *Lesen* kommt vor den Gruppen die **Lesestufe** (drei Voreinstellungen mit Vorschau).

### Lesen

**Sichtbar**

- *Leichter lesen*
  - Papierton
  - Buchstabenabstand
  - Wortabstand
  - Zeilenluft
- *Beim Schreiben*
  - Zeilenfokus
  - Absatz beim Schreiben
  - Übriger Text
- *Vorlesen*
  - Den Text hören

**Weitere Einstellungen (eingeklappt)**

- *Silben farbig (Lesehilfe für Legasthenie)*
  - Silben farbig anzeigen
- *Silbentrennung*
  - Sprache der Silbentrennung

### Anzeige

**Sichtbar**

- *Aussehen*
  - Hell, Dunkel (Aussehen)
- *Anzeigen*
  - Lineal
  - Statusleiste
  - Absatzmarken und Leerzeichen zeigen
- *Größe und Kontrast*
  - Schrift im Text
  - Weicher Kontrast
  - Größe der Symbole
  - Schrift der Bedienung

**Weitere Einstellungen (eingeklappt)**

- *Weitere Anzeige*
  - Vertikales Lineal
  - Navigationsbereich
  - Textbegrenzungen
  - Gitternetzlinien
  - Seitenleiste beim Start
  - QuickInfo
  - Live-Vorschau
  - Minisymbolleiste bei Auswahl
  - Objektanker
  - Ausgeblendeter Text
- *Formatierungszeichen einzeln*
  - Absatzmarken
  - Leerzeichen und Tabstoppzeichen
- *Menüband*
  - Doppelklick blendet das Band aus
  - Strg+Klick folgt einem Verweis
  - Benutzeroberfläche
  - Menüband anpassen
  - Symbolleiste für den Schnellzugriff

### Schreiben

**Sichtbar**

- *Schrift für neuen Text*
  - Schrift
  - Größe
- *Prüfen*
  - Rechtschreibung während der Eingabe prüfen
  - Grammatik mitprüfen
  - Silbentrennung
  - Sprache für die Prüfung und Übersetzen nach
- *AutoKorrektur*
  - Wortvorhersage

**Weitere Einstellungen (eingeklappt)**

- *AutoKorrektur: Groß- und Kleinschreibung*
  - Jeden Satz mit einem Großbuchstaben beginnen
  - Wochentage immer großschreiben
  - Unbeabsichtigtes Verwenden der fESTSTELLTASTE korrigieren
  - Englische Ordnungszahlen hochstellen
- *AutoKorrektur: Zeichen*
  - Gerade Anführungszeichen durch typografische ersetzen
  - Zwei Bindestriche durch einen Gedankenstrich ersetzen
  - Drei Punkte durch ein Auslassungszeichen ersetzen
  - Internet- und Netzwerkpfade durch Hyperlinks ersetzen
- *AutoKorrektur: Einzüge und Leerzeichen*
  - Leerzeichen am Absatzanfang mit Erstzeileneinzug
  - Leerzeichenformat am Ende rechtsbündiger Zeilen anpassen
  - Bei zentriertem Ausrichten Erstzeileneinzug löschen
  - Tabulator und Rücktaste setzen den Einzug
- *Prüfung im Einzelnen*
  - Immer Korrekturvorschläge unterbreiten
  - Wörter in GROSSBUCHSTABEN ignorieren
  - Wörter mit Zahlen ignorieren
  - Internet- und Netzwerkpfade ignorieren
  - Weggewinkte Funde wieder anzeigen
  - Gründlich prüfen
- *AutoFormat*
  - Automatisch nummerierte Listen
  - Aufzählungen erkennen
  - Zahl automatisch im Kreis
- *Bearbeiten und Einfügen*
  - Wortweise markieren
  - Text mit der Maus verschieben
  - Tippen ersetzt die Auswahl
  - Schaltfläche nach dem Einfügen
  - Mittlere Maustaste fügt ein
  - Standardeinfügeformat
- *Eigenes Wörterbuch und gelernte Schreibweisen*
  - Gelernte Schreibweisen

### Speichern

**Sichtbar**

- *Speichern*
  - Dateien als Standard speichern
  - Ordner zum Speichern
  - Maßeinheit
- *Sicherung*
  - Wann gesichert wird
  - Abstand (Minuten)

**Weitere Einstellungen (eingeklappt)**

- *Weiteres zum Speichern*
  - Beim Start das zuletzt geschriebene Dokument öffnen
  - Bilder in der Datei nicht komprimieren
  - Standard-Ausgabeziel
  - Eigene Vorlagen
- *Zwischenstände*
  - Aufbewahren (Tage)
  - Zwischenstände löschen
- *Gedächtnis und Wörterbuch sichern*
  - Sichern und zurückholen
  - Einstellungsdatei
- *Dokument schützen und Änderungen*
  - Kennwort, Bearbeitung sperren, Datenschutz
  - Änderungen verfolgen: Markup, Farben, Sprechblasen

### Drucken und PDF

**Sichtbar**

- *Drucken*
  - Hohe Qualität
  - Hintergrundfarben und -bilder drucken
- *PDF*
  - PDF nach dem Export öffnen
  - Überschriften als Lesezeichen

**Weitere Einstellungen (eingeklappt)**

- *Drucken im Einzelnen*
  - Womit das Druckfenster aufgeht
  - Umgekehrte Reihenfolge
  - Zeichnungsobjekte drucken
  - Leere Seiten mitdrucken
  - Felder vor dem Drucken aktualisieren
  - Ausgeblendeter Text
- *PDF im Einzelnen*
  - Kommentare als PDF-Notizen mitnehmen
  - Dokumenteigenschaften (Autor) in das PDF übernehmen
  - Textmarken übernehmen

### Name und KI

**Sichtbar**

- *Wer schreibt*
  - Name
  - Initialen
  - Diese Benutzerinformationen verwenden

**Weitere Einstellungen (eingeklappt)**

- *Adresse*
  - Straße und Hausnummer
  - PLZ und Ort
  - Ort (für „Ort, Datum“)
  - Telefon
  - E-Mail
  - Beim Speichern persönliche Daten entfernen
- *Prüfung und KI*
  - Chatbot
  - Zusammenfassen
  - Übersetzung
  - Textanalyse
  - Bildgenerierung
  - API-Schlüssel
  - KI-Modell
  - Eigene Anbieter
  - Eigene Assistenten
  - Für wen der Text ist


## Wo finde ich was?

Alphabetisch, mit Seite und Gruppe. Oder in den Optionen oben in die Suche tippen.

| Einstellung | Wo sie steht |
|---|---|
| Absatz beim Schreiben | Lesen ▸ Beim Schreiben |
| Absatzmarken | Anzeige ▸ Formatierungszeichen einzeln (eingeklappt) |
| Absatzmarken und Leerzeichen zeigen | Anzeige ▸ Anzeigen |
| Abstand (Minuten) | Speichern ▸ Sicherung |
| API-Schlüssel | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Aufbewahren (Tage) | Speichern ▸ Zwischenstände (eingeklappt) |
| Aufzählungen erkennen | Schreiben ▸ AutoFormat (eingeklappt) |
| Ausgeblendeter Text | Anzeige ▸ Weitere Anzeige (eingeklappt) · Drucken und PDF ▸ Drucken im Einzelnen (eingeklappt) |
| Automatisch nummerierte Listen | Schreiben ▸ AutoFormat (eingeklappt) |
| Bei zentriertem Ausrichten Erstzeileneinzug löschen | Schreiben ▸ AutoKorrektur: Einzüge und Leerzeichen (eingeklappt) |
| Beim Speichern persönliche Daten entfernen | Name und KI ▸ Adresse (eingeklappt) |
| Beim Start das zuletzt geschriebene Dokument öffnen | Speichern ▸ Weiteres zum Speichern (eingeklappt) |
| Benutzeroberfläche | Anzeige ▸ Menüband (eingeklappt) |
| Bilder in der Datei nicht komprimieren | Speichern ▸ Weiteres zum Speichern (eingeklappt) |
| Bildgenerierung | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Buchstabenabstand | Lesen ▸ Leichter lesen |
| Chatbot | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Dateien als Standard speichern | Speichern ▸ Speichern |
| Den Text hören | Lesen ▸ Vorlesen |
| Diese Benutzerinformationen verwenden | Name und KI ▸ Wer schreibt |
| Dokumenteigenschaften (Autor) in das PDF übernehmen | Drucken und PDF ▸ PDF im Einzelnen (eingeklappt) |
| Doppelklick blendet das Band aus | Anzeige ▸ Menüband (eingeklappt) |
| Drei Punkte durch ein Auslassungszeichen ersetzen | Schreiben ▸ AutoKorrektur: Zeichen (eingeklappt) |
| E-Mail | Name und KI ▸ Adresse (eingeklappt) |
| Eigene Anbieter | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Eigene Assistenten | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Eigene Vorlagen | Speichern ▸ Weiteres zum Speichern (eingeklappt) |
| Einstellungsdatei | Speichern ▸ Gedächtnis und Wörterbuch sichern (eingeklappt) |
| Englische Ordnungszahlen hochstellen | Schreiben ▸ AutoKorrektur: Groß- und Kleinschreibung (eingeklappt) |
| Felder vor dem Drucken aktualisieren | Drucken und PDF ▸ Drucken im Einzelnen (eingeklappt) |
| Für wen der Text ist | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Gelernte Schreibweisen | Schreiben ▸ Eigenes Wörterbuch und gelernte Schreibweisen (eingeklappt) |
| Gerade Anführungszeichen durch typografische ersetzen | Schreiben ▸ AutoKorrektur: Zeichen (eingeklappt) |
| Gitternetzlinien | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Grammatik mitprüfen | Schreiben ▸ Prüfen |
| Größe | Schreiben ▸ Schrift für neuen Text |
| Größe der Symbole | Anzeige ▸ Größe und Kontrast |
| Gründlich prüfen | Schreiben ▸ Prüfung im Einzelnen (eingeklappt) |
| Hell, Dunkel (Aussehen) | Anzeige ▸ Aussehen |
| Hintergrundfarben und -bilder drucken | Drucken und PDF ▸ Drucken |
| Hohe Qualität | Drucken und PDF ▸ Drucken |
| Immer Korrekturvorschläge unterbreiten | Schreiben ▸ Prüfung im Einzelnen (eingeklappt) |
| Initialen | Name und KI ▸ Wer schreibt |
| Internet- und Netzwerkpfade durch Hyperlinks ersetzen | Schreiben ▸ AutoKorrektur: Zeichen (eingeklappt) |
| Internet- und Netzwerkpfade ignorieren | Schreiben ▸ Prüfung im Einzelnen (eingeklappt) |
| Jeden Satz mit einem Großbuchstaben beginnen | Schreiben ▸ AutoKorrektur: Groß- und Kleinschreibung (eingeklappt) |
| Kennwort, Bearbeitung sperren, Datenschutz | Speichern ▸ Dokument schützen und Änderungen (eingeklappt) |
| KI-Modell | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Kommentare als PDF-Notizen mitnehmen | Drucken und PDF ▸ PDF im Einzelnen (eingeklappt) |
| Leere Seiten mitdrucken | Drucken und PDF ▸ Drucken im Einzelnen (eingeklappt) |
| Leerzeichen am Absatzanfang mit Erstzeileneinzug | Schreiben ▸ AutoKorrektur: Einzüge und Leerzeichen (eingeklappt) |
| Leerzeichen und Tabstoppzeichen | Anzeige ▸ Formatierungszeichen einzeln (eingeklappt) |
| Leerzeichenformat am Ende rechtsbündiger Zeilen anpassen | Schreiben ▸ AutoKorrektur: Einzüge und Leerzeichen (eingeklappt) |
| Lineal | Anzeige ▸ Anzeigen |
| Live-Vorschau | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Maßeinheit | Speichern ▸ Speichern |
| Menüband anpassen | Anzeige ▸ Menüband (eingeklappt) |
| Minisymbolleiste bei Auswahl | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Mittlere Maustaste fügt ein | Schreiben ▸ Bearbeiten und Einfügen (eingeklappt) |
| Name | Name und KI ▸ Wer schreibt |
| Navigationsbereich | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Objektanker | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Ordner zum Speichern | Speichern ▸ Speichern |
| Ort (für „Ort, Datum“) | Name und KI ▸ Adresse (eingeklappt) |
| Papierton | Lesen ▸ Leichter lesen |
| PDF nach dem Export öffnen | Drucken und PDF ▸ PDF |
| PLZ und Ort | Name und KI ▸ Adresse (eingeklappt) |
| QuickInfo | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Rechtschreibung während der Eingabe prüfen | Schreiben ▸ Prüfen |
| Schaltfläche nach dem Einfügen | Schreiben ▸ Bearbeiten und Einfügen (eingeklappt) |
| Schrift | Schreiben ▸ Schrift für neuen Text |
| Schrift der Bedienung | Anzeige ▸ Größe und Kontrast |
| Schrift im Text | Anzeige ▸ Größe und Kontrast |
| Seitenleiste beim Start | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Sichern und zurückholen | Speichern ▸ Gedächtnis und Wörterbuch sichern (eingeklappt) |
| Silben farbig anzeigen | Lesen ▸ Silben farbig (Lesehilfe für Legasthenie) (eingeklappt) |
| Silbentrennung | Schreiben ▸ Prüfen |
| Sprache der Silbentrennung | Lesen ▸ Silbentrennung (eingeklappt) |
| Sprache für die Prüfung und Übersetzen nach | Schreiben ▸ Prüfen |
| Standard-Ausgabeziel | Speichern ▸ Weiteres zum Speichern (eingeklappt) |
| Standardeinfügeformat | Schreiben ▸ Bearbeiten und Einfügen (eingeklappt) |
| Statusleiste | Anzeige ▸ Anzeigen |
| Straße und Hausnummer | Name und KI ▸ Adresse (eingeklappt) |
| Strg+Klick folgt einem Verweis | Anzeige ▸ Menüband (eingeklappt) |
| Symbolleiste für den Schnellzugriff | Anzeige ▸ Menüband (eingeklappt) |
| Tabulator und Rücktaste setzen den Einzug | Schreiben ▸ AutoKorrektur: Einzüge und Leerzeichen (eingeklappt) |
| Telefon | Name und KI ▸ Adresse (eingeklappt) |
| Text mit der Maus verschieben | Schreiben ▸ Bearbeiten und Einfügen (eingeklappt) |
| Textanalyse | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Textbegrenzungen | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Textmarken übernehmen | Drucken und PDF ▸ PDF im Einzelnen (eingeklappt) |
| Tippen ersetzt die Auswahl | Schreiben ▸ Bearbeiten und Einfügen (eingeklappt) |
| Umgekehrte Reihenfolge | Drucken und PDF ▸ Drucken im Einzelnen (eingeklappt) |
| Unbeabsichtigtes Verwenden der fESTSTELLTASTE korrigieren | Schreiben ▸ AutoKorrektur: Groß- und Kleinschreibung (eingeklappt) |
| Vertikales Lineal | Anzeige ▸ Weitere Anzeige (eingeklappt) |
| Wann gesichert wird | Speichern ▸ Sicherung |
| Weggewinkte Funde wieder anzeigen | Schreiben ▸ Prüfung im Einzelnen (eingeklappt) |
| Weicher Kontrast | Anzeige ▸ Größe und Kontrast |
| Wochentage immer großschreiben | Schreiben ▸ AutoKorrektur: Groß- und Kleinschreibung (eingeklappt) |
| Womit das Druckfenster aufgeht | Drucken und PDF ▸ Drucken im Einzelnen (eingeklappt) |
| Wortabstand | Lesen ▸ Leichter lesen |
| Wortvorhersage | Schreiben ▸ AutoKorrektur |
| Wortweise markieren | Schreiben ▸ Bearbeiten und Einfügen (eingeklappt) |
| Wörter in GROSSBUCHSTABEN ignorieren | Schreiben ▸ Prüfung im Einzelnen (eingeklappt) |
| Wörter mit Zahlen ignorieren | Schreiben ▸ Prüfung im Einzelnen (eingeklappt) |
| Zahl automatisch im Kreis | Schreiben ▸ AutoFormat (eingeklappt) |
| Zeichnungsobjekte drucken | Drucken und PDF ▸ Drucken im Einzelnen (eingeklappt) |
| Zeilenfokus | Lesen ▸ Beim Schreiben |
| Zeilenluft | Lesen ▸ Leichter lesen |
| Zusammenfassen | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Zwei Bindestriche durch einen Gedankenstrich ersetzen | Schreiben ▸ AutoKorrektur: Zeichen (eingeklappt) |
| Zwischenstände löschen | Speichern ▸ Zwischenstände (eingeklappt) |
| Änderungen verfolgen: Markup, Farben, Sprechblasen | Speichern ▸ Dokument schützen und Änderungen (eingeklappt) |
| Überschriften als Lesezeichen | Drucken und PDF ▸ PDF |
| Übersetzung | Name und KI ▸ Prüfung und KI (eingeklappt) |
| Übriger Text | Lesen ▸ Beim Schreiben |

---

[← Zurück zum README](../README.md) · [Der Aufbau des Bandes](aufbau-band.md)
