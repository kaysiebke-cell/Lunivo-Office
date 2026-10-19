![Nolphin File Manager – two windows, on the left with a file preview, on the right with the GID projects, the Nolphin icon in the middle. Below the slogan: The function comes to you – not the other way round.](docs/bilder/titelbild-en.png)

# Nolphin

**Ein nativer Linux-Dateimanager für Linux Mint Cinnamon, lauffähig auch unter XFCE und MATE – mit einem festen rechten Arbeitsbereich für Vorschau, Eigenschaften, Archive, Terminal, Git und Paketbau.**

Nolphin ist ein eigenständiger Dateimanager auf Basis von Nemo 6.7.7 (GTK3, C11). Er wurde vollständig in **Nolphin** umbenannt und um eigene Funktionen erweitert. Die Hauptansicht bleibt sichtbar, während rechts daneben die jeweils gewählte Funktion bedient wird – ohne zusätzliche Fenster.

> **Hinweis:** Nolphin ist ein unabhängiges Open-Source-Projekt und kein offizielles Projekt von Linux Mint.

![Nolphin: links die Orte, in der Mitte die Dateien des Ordners „Bilder“, rechts der Arbeitsbereich mit den Ordner-Informationen](docs/bilder/uebersicht.png)

---

## Projektphilosophie

**Die Funktion kommt zur Datei – nicht umgekehrt.**

Wer mit technischen Dateien arbeitet, wechselt sonst ständig zwischen Dateimanager, Terminal und Zusatzprogrammen. Nolphin holt diese Werkzeuge in das Hauptfenster.

* **Ehrlich statt vorgetäuscht:** Fehlt ein Hilfsprogramm oder ein Vorschau-Backend, zeigt Nolphin das an, statt eine Funktion zu simulieren.
* **Vertraute Bedienung:** Die klassische Nemo-Bedienung bleibt erhalten.
* **Nur Belegtes ist fertig:** Diese README beschreibt den Stand des Codes. Als „umgesetzt“ gilt, was im Code vorhanden ist, als „getestet“ nur, was die Meson-Tests abdecken.

---

## Schnellstart

Aus dem Quellcode bauen und direkt aus dem Build-Verzeichnis starten:

```bash
meson setup build
ninja -C build
env GSETTINGS_SCHEMA_DIR="$(pwd)/build/libnolphin-private" \
    LD_LIBRARY_PATH="$(pwd)/build/libnolphin-extension" \
    ./build/src/nolphin
```

Mit **F11** blendest du den rechten Arbeitsbereich ein, mit **F4** das Terminal. Der Arbeitsbereich ist mindestens 400 Pixel breit (Standard 480); die Breite lässt sich mit dem Teiler ändern und wird gemerkt.

Voraussetzungen, Installation und Tests: siehe [Bauen und Installieren](docs/bauen-und-installieren.md).

---

## Highlights

* **Rechter Arbeitsbereich (F11):** ein fester Bereich für Vorschau, Eigenschaften, Archive, Terminal, Git, DEB-Ersteller, Massenumbenennung und die Werkzeuge unten – ohne zusätzliche Fenster.
* **GID-Projekte:** lokale Projektordner in der Seitenleiste; ein Klick zeigt die `README.md` des Projekts rechts im Arbeitsbereich – im Aussehen von GitHub, mit Tabellen, Aufgabenlisten, Bildern und aufklappbaren Abschnitten. Alles bleibt lokal.
* **Vorschau mit Medieninfos:** Bilder, **PDF** (Titel, Autor, Seiten, Seitengröße), **Video** und **Audio** (Dauer, Codec, Auflösung, Bildrate, Kanäle).
* **Metadaten:** **Bewertung (Sterne), Tags und Kommentar** direkt im Info-Panel.
* **Git direkt im Dateimanager:** Overlay-Symbole an den Dateien (hinzugefügt, geändert, unversioniert), Panel für Status, Speichern, Server-Abgleich, Verlauf und Unterschiede.
* **Archive:** Komprimieren, Entpacken, Prüfen und – im **Archiv-Manager** – Inhalt auflisten sowie Dateien hinzufügen, ersetzen und entfernen.
* **Handy-Austausch in beide Richtungen, verschlüsselt:** Ein Klick auf „Handy“ in der Seitenleiste (oder Datei ▸ Handy-Austausch) startet den Austausch: rechts erscheint ein QR-Code, in der Hauptansicht der Ordner `~/Handy`. Die Handy-App (eigenes Projekt [Nolphin Handy](https://github.com/kaysiebke-cell/nolphin-handy), eine optionale Erweiterung) scannt den Code und verbindet sich verschlüsselt nur mit diesem PC; sie lädt Dateien und Ordner (`Vom Handy`) und empfängt Dateien aus `Handy`. Dafür braucht der PC `openssl`. Siehe [Schnittstelle](docs/handy-austausch-api.md).
* **Werkzeuge:** Ordner **vergleichen und synchronisieren** (rsync, löscht nie), **Regeln anwenden**, **Duplikate finden**, **Versionen** einer Datei speichern und wiederherstellen.
* **Suche mit Operatoren:** im Dateinamen UND, ODER, NICHT, „exakt“ und Platzhalter, dazu reguläre Ausdrücke.
* **Mehrere Bereiche:** geteilte Ansicht mit bis zu vier Bereichen und **Arbeitsbereiche**, die Reiter, Teilung und Fenstergröße speichern.
* **Gehe zu:** Verlauf, häufig verwendete Orte und die Reiter des Fensters im Menü.
* **Hilfe (F1):** eine eingebaute Hilfe mit 20 Themen, Bildern, Tabellen und Themensuche; sie öffnet sich wie die Einstellungen im Hauptbereich. Die Texte liegen als Markdown unter `docs/hilfe/`.
* **Diagnose:** Protokolle, Systeminformationen, Plugin-Status und Fehlerbericht im Panel.
* **Einstellungen exportieren, importieren und zurücksetzen.**
* **DEB-Pakete erstellen:** Nolphin baut ein `.deb` selbst als `ar`-Archiv, ohne `dpkg-deb`.
* **Massenumbenennung:** Suchen/Ersetzen, Nummerierung und Groß-/Kleinschreibung mit Vorschau, rückgängig machbar.
* **CAD- und 3D-Erkennung:** STL, STEP/STP, FreeCAD `.FCStd` und weitere Formate.
* **Sicherheit:** Prüfsummen, GPG-Verschlüsselung, ACL-Verwaltung.
* **Papierkorb-Automatik** und **gespeicherte Dateiauswahlen**.
* **Nemo-Grundlagen:** Tabs, Symbol-, Listen- und Kompaktansicht, Fortschritt, Rückgängig, Netzwerk über GVfs.

---

## Dokumentation

| Nr. | Seite | Inhalt |
| --- | ----- | ------ |
| 1 | [Bauen und Installieren](docs/bauen-und-installieren.md) | Voraussetzungen, Bauen, Tests, Installation |
| 2 | [Der rechte Arbeitsbereich](docs/arbeitsbereich.md) | Panels für Vorschau, Eigenschaften, Archive, Terminal, Git und mehr – mit Bildern |
| 3 | [Funktionen im Detail](docs/funktionen.md) | Dateiverwaltung, Archive, Git, Werkzeuge, Suche, Handy-Austausch, GID-Projekte, Sicherheit |
| 3a | [Handy-Austausch: Analyse](docs/handy-austausch-analyse.md) | Ist-Zustand, Vergleich mit LocalSend, Warpinator und PairDrop, Verbindungsablauf, Sicherheit, Tests |
| 3b | [Handy-Austausch: Schnittstelle](docs/handy-austausch-api.md) | Verbindungslink und QR-Format, Wege, Fehlercodes, Verhalten der App |
| 4 | [Einstellungen und Anpassung](docs/einstellungen.md) | Einstellungsseiten, Layout-Editor, Export und Import |
| 5 | [Andere Desktops: XFCE und MATE](docs/andere-desktops.md) | Optionale Bibliotheken, Symbol-Ersatz, Teststand, bekannte Grenzen |
| 6 | [Nolphin und Nemo](docs/nolphin-und-nemo.md) | Vergleich und Einrichtung als Nemo-Ersatz |
| 7 | [Entwicklungsstand](docs/entwicklungsstand.md) | Was umgesetzt ist, was getestet wurde |
| 8 | [Projektstruktur](docs/projektstruktur.md) | Verzeichnisse, Schema, weitere Dokumente |
| 9 | [Fehler melden](docs/fehler-melden.md) | Vorlage für einen hilfreichen Bericht |

Die eingebaute Hilfe (**F1**) liegt als Markdown unter [docs/hilfe/](docs/hilfe/).

---

## Herkunft

Nolphin begann als Quellstand von **Nemo 6.7.7**, wurde umbenannt, strukturell angepasst und schrittweise um eigene Funktionen erweitert. Der Verlauf steht in der Git-Historie.

## Lizenz

**GPL-2.0-or-later**, siehe [COPYING](COPYING).

---

**Nolphin – Dateien verwalten. Informationen sehen. Mehr direkt erledigen.**
