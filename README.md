<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="bilder/lunivo-office-dunkel.png">
    <img src="bilder/lunivo-office.png" style="max-width: 100%; height: auto;" alt="Lunivo Writer Logo">
  </picture>
</p>

<p align="center">
  Was geschrieben wird, bleibt auf diesem Rechner.<br>
  Nichts geht hinaus, ohne dass du es selbst schickst.
</p>

# Lunivo Writer

Eine **native Textverarbeitung für Linux** (Python 3 + Qt 6 / PySide6) — keine Web-Oberfläche, kein Browser, kein Webserver.
**DOCX** ist das Hauptformat. Die **Schreibhilfe** sitzt fest an der Seite und sucht die Fehler, die ein Rechtschreibprüfer
**nicht** findet (das/dass, seit/seid, fehlende Kommas, zusammengetippte oder doppelte Wörter …). Dazu Lesehilfen für Menschen
mit Legasthenie (farbige Silben, Vorlesen, Lesefenster) und optional eine KI (Ollama lokal oder Claude), die nur auf
ausdrücklichen Wunsch etwas verschickt.

Nicht *für* Menschen mit Legasthenie gebaut, sondern *von* einem. Kein Konto, keine Anmeldung, kein Internet nötig.

## Starten

```bash
sudo apt install python3 python3-venv libxcb-cursor0 libegl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0
./starten-qt.sh                 # legt beim ersten Mal eine eigene Umgebung (.venv) an und startet
./starten-qt.sh --eintrag       # zusätzlich ein Menüeintrag
./starten-qt.sh --test          # Tests
```

Genaueres, optionale Teile (LibreOffice, LanguageTool, Piper-Stimme, Leseschriften, Ollama): [doku/native-qt/INSTALLATION.md](doku/native-qt/INSTALLATION.md).

## Oberfläche

* Reiterleiste **Datei · Start · Einfügen · Seitenlayout · Verweise · Überprüfen · Schreibhilfe · Ansicht**; „Datei“ öffnet die
  Backstage-Ansicht. Kontext-Reiter (Tabelle, Bild, Form, Kopf-/Fußzeile) erscheinen bei Bedarf.
* Hell und dunkel, Symbole im Fluent-Stil, Schreibhilfe-Seitenleiste mit KI-Chat.
* Spalten (1–4) live auf der Seite, Fußnoten am Seitenfuß, Sprechblasen für Kommentare, Formularfelder, Serienbriefe, PDF mit
  Lesezeichen.

## Dokumentation

| | |
|---|---|
| [doku/native-qt/README.md](doku/native-qt/README.md) | Aufbau des Programms |
| [doku/native-qt/BERICHT.md](doku/native-qt/BERICHT.md) | Stand, ehrlich: was geht, was nicht, was ungetestet ist |
| [doku/native-qt/PRUEFBOGEN.md](doku/native-qt/PRUEFBOGEN.md) | Abgleich mit dem Prüfbogen (415 Punkte) |
| [doku/native-qt/INSTALLATION.md](doku/native-qt/INSTALLATION.md) | Installation und optionale Bausteine |

## Hinweis zur Geschichte

Das Projekt begann als Web-Oberfläche (HTML/JavaScript mit GTK-Fenster). Diese Fassung liegt nur noch im Zweig `main` bzw. in
der Git-Geschichte; dieser Zweig (`native-qt6-port`) enthält ausschließlich die native Qt-Fassung. Die Rechtschreib-Regeln
(`native_qt/resources/daten/regeln.txt`) und das Wörterbuch stammen von dort.

Lizenz: siehe [LICENSE](LICENSE). Symbole: Fluent UI System Icons (Microsoft, MIT) und Lucide (ISC), siehe `native_qt/resources/`.
