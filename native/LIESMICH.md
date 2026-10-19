# Lunivo-Office — native GTK4-Fassung

Eine echte Desktop-Anwendung (Python + GTK 4): kein Browser, kein WebKit, kein lokaler Webserver.
Das alte Programm (`start.py`, `oberflaeche/`) bleibt unverändert daneben liegen.

## Installieren

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 nodejs libreoffice-writer   # was fehlt, sagt das Skript
./native/installieren.sh
```

Danach steht „Lunivo-Office“ im Cinnamon-Menü (Büro) oder: `lunivo-office`.
Ohne Installation: `./native/lunivo-office-gtk`. Entfernen: `./native/installieren.sh --weg`.

## Was geht

- Reiter, Neu/Öffnen/Speichern (docx, odt, html, txt, rtf), Export als PDF/docx/odt/txt
- Formatierung: Fett, Kursiv, Unterstrichen, Durchgestrichen, Schriftart, Größe, Farbe,
  Ausrichtung, Überschriften, Aufzählung/Nummerierung, Rückgängig/Wiederholen
- Suchen und Ersetzen, Zoom, Drucken (GTK-Druckdialog)
- Schreibhilfe: die vorhandene Prüflogik (`oberflaeche/js/pruefung.js`) läuft über Node ohne Fenster;
  Funde anklicken, übernehmen oder ignorieren
- KI über Ollama (Korrektur, Zusammenfassen, Englisch); Modell aus der alten Einstellung übernommen

## Daten

- Beim ersten Start werden die Texte aus dem alten Speicher (`~/.local/share/schreibprogramm`) **nur gelesen**,
  vorher gesichert (`~/.local/share/lunivo-office-gtk/sicherungen/`) und als HTML-Dateien in
  `~/.local/share/lunivo-office-gtk/dokumente/` abgelegt.
- Einstellungen: `~/.config/lunivo-office/gtk-einstellungen.json`. Die alte `einstellungen.conf` wird nur gelesen.

## Noch nicht übernommen

Menüband mit allen Reitern, Tabellen, Bilder, Kopf-/Fußzeilen und Seitenumbrüche, Stile/Vorlagen,
Rechtschreibung über Hunspell, Vorlesen, LanguageTool. Die alte Fassung kann das weiterhin.
