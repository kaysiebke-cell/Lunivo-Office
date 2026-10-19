# Lunivo Writer — Handbuch

Lunivo Writer ist eine Textverarbeitung für Linux. **DOCX** ist das Hauptformat. Was Sie schreiben, bleibt auf diesem Rechner;
ins Internet geht nur etwas, wenn Sie es ausdrücklich auslösen (KI-Funktionen) — das Programm fragt vorher.

## Aufbau des Fensters

* **Dokumentreiter** ganz oben: mehrere Dokumente nebeneinander, **+** öffnet ein neues.
* **Schnellzugriff** links neben der Reiterleiste: Öffnen, Speichern, Drucken, Rückgängig, Wiederholen.
* **Reiterleiste:** Datei · Start · Einfügen · Seitenlayout · Verweise · Überprüfen · Schreibhilfe · Ansicht. Reiter wie *Tabellentools*,
  *Bildtools* oder *Kopf- und Fußzeilentools* erscheinen nur, wenn Sie in einer Tabelle, an einem Bild oder in der Kopfzeile stehen.
* **Band** unter den Reitern: die Befehle des gewählten Reiters, in Gruppen. Doppelklick auf einen Reiter blendet das Band aus.
* **Seitenleiste rechts:** die Schreibhilfe und der KI-Chat. Die schmale Leiste daneben schaltet zwischen beiden um.
* **Statusleiste:** Wörter, Zeichen, Seite, Zoom.

## Datei (Backstage)

Ein Klick auf **Datei** ersetzt das Dokument durch die Backstage-Ansicht: links die Befehle, rechts die zugehörige Seite.

| Eintrag | Was geschieht |
|---|---|
| Neues Dokument erstellen · Von Vorlage erstellen · Öffnen | wie beschrieben; die Ansicht schließt sich |
| Zuletzt benutzte Dokumente | Liste der letzten Dateien, „Liste leeren“ |
| Speichern · Speichern als | DOCX; Speichern unter, Kopie, Export als PDF, DOCX, DOC, ODT, RTF, TXT, PNG |
| Drucken | Druckfenster, Vorschau, Druckerwahl |
| Schützen | Kennwort setzen/entfernen, Bearbeitung sperren |
| Info | Statistik, Verfasser und Titel |
| Öffnen mit … | WPS Writer oder LibreOffice, sofern installiert |
| Erweiterte Einstellungen | die Optionen |

Zurück zum Dokument: **Esc**, „Zurück zum Dokument“, ein zweiter Klick auf **Datei** oder ein anderer Reiter.

## Schreiben und Gestalten

* **Start:** Zwischenablage, Schriftart und -größe, Auszeichnungen (fett, kursiv, unterstrichen …), Absatz (Listen, Ausrichtung,
  Zeilenabstand), Stile, Suchen/Ersetzen.
* **Einfügen:** Seiten, Tabellen, Bilder, Formen, Links, Kopf- und Fußzeile, Seitenzahl, Textfeld, Datum, Sonderzeichen, Formeln.
* **Seitenlayout:** Ränder, Papier, Ausrichtung, **Spalten (1–4, live auf der Seite)**, Umbrüche, Seitenfarbe, Rahmen, Wasserzeichen.
* **Verweise:** Inhaltsverzeichnis, Fuß- und Endnoten (Fußnoten stehen am Seitenfuß), Beschriftungen, Querverweise, Zitate.
* **Überprüfen:** Rechtschreibung, Kommentare (als Sprechblasen am Rand), Änderungen verfolgen, Vergleichen, Schützen.
* **Ansicht:** Zoom, Lineal, Gitternetz, Seitenansichten, Hell/Dunkel, Register anpassen.

Die Auswahl in Schriftart-, Größen- und Farbfeldern zeigt beim Überfahren eine **Live-Vorschau** im Text.

## Schreibhilfe

Die Schreibhilfe prüft das, was ein Rechtschreibprüfer nicht findet: *das/dass*, *seit/seid*, *wider/wieder*, fehlende Kommas,
zusammengetippte oder doppelte Wörter, Satzanfänge. Rote Wellenlinien zeigen die Stellen; die Seitenleiste erklärt sie und bietet
**Ändern** oder **Lassen**.

* **We · Vo · Ko** schalten *Wellenlinien*, *Vorschläge* und *Korrektur* für dieses Dokument an oder aus.
* **Prüfen** prüft das ganze Dokument. Wer denselben Fund mehrmals stehen lässt, meint es so — das Wort kommt dann in Ruhe.
* **Für wen?** (egal, Amt, Arbeit, Freunde, Forum, Bewerbung) lenkt die Wortvorhersage auf passende Wörter.

## Lesehilfe (Reiter Schreibhilfe)

* **Lesehilfe:** größere Schrift, Zeilenfokus, ruhigere Darstellung.
* **Silben farbig:** Silben in wechselnden Farben, nur in der Anzeige — das Dokument bleibt unverändert; auch für Druck und PDF
  wählbar. **Silben einstellen …** legt Farben, Zahl der Farben und Wirkung fest.
* **Vorlesen:** mit Piper (offline) oder speech-dispatcher.

## KI (freiwillig)

Im Reiter *Schreibhilfe* und im KI-Chat der Seitenleiste: Text entwerfen, umformulieren, zusammenfassen, übersetzen, Text in Bild,
Korrektur und Verbesserungsvorschläge. Anbieter und Modelle legen Sie unter **KI-Konfiguration** fest (auch in den Optionen):
Ollama läuft lokal und braucht keinen Schlüssel; Claude oder ein eigener Anbieter brauchen einen Schlüssel, der nur in
`ki.json` im Datenordner liegt. Vor jedem Weg ins Internet fragt das Programm nach.

## Speichern und Sicherheit

* Gespeichert wird atomar: erst eine Temporärdatei, dann der Austausch — ein Absturz beschädigt die alte Datei nicht.
* Die automatische Sicherung (Wiederherstellung) legt in kurzen Abständen eine Kopie ab.
* Was beim Öffnen oder Speichern nicht übernommen werden kann (zum Beispiel bestimmte Formen), meldet ein Bericht — nichts
  verschwindet stillschweigend.

## Tastenkürzel (Auswahl)

| | |
|---|---|
| Strg+N · Strg+O · Strg+S | Neu · Öffnen · Speichern |
| Strg+P | Drucken |
| Strg+Z · Strg+Y | Rückgängig · Wiederholen |
| Strg+F · Strg+H | Suchen · Ersetzen |
| Strg+B · Strg+I · Strg+U | Fett · Kursiv · Unterstrichen |
| F9 | Optionen |

Die vollständige Liste: **Hilfe ▸ Tastenkürzel**.
