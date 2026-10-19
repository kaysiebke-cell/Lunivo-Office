# Der Aufbau des Projekts

Welche Datei was tut.

    main.py              startet das Programm aus dem Projektordner
    starten-qt.sh        legt beim ersten Mal die Umgebung an, startet, schreibt den Menüeintrag
    stimme-holen.sh      holt Piper und die Stimme „Thorsten“ (freiwillig)
    schrift-holen.sh     holt Schriften zum leichteren Lesen (freiwillig)
    pyproject.toml       Paket, Abhängigkeiten, Testeinstellungen

    src/lunivo_writer/   das Programm — Python 3 und Qt-Widgets (PySide6), kein Browser
      app.py             der Einstieg
      core/              Anwendungskern: application.py (Start/Ende), document_manager.py
                         (Laden, Speichern, Sicherung, zuletzt benutzt), commands.py (jeder Knopf → seine Funktion)
      ui/                alles, was im Fenster zu sehen ist
        main_window.py   das Hauptfenster — koordiniert nur
        backstage.py     der Reiter „Datei“ als Backstage-Ansicht
        ribbon/          das Band: ribbon_bar.py, plan.py, tabs/ (ein Modul je Reiter), Symbolleisten
        document/        der Editor, das Blatt, die Dokumentreiter, Lineal, Navigation
        sidebar/         die rechte Seitenleiste: Schreibhilfe-Karten und KI-Chat
        contextual/      Tabellen-, Bild-, Form- und Kopf-/Fußzeilenwerkzeuge
        dialogs/         Optionen und alle Dialoge
        statusbar/       die Statuszeile
        widgets/         Symbole, Live-Vorschau, Minisymbolleiste
      editor/            was das Dokument kann: Seitenumbruch, PDF/Druck, Fußnoten, Stile, Formularfelder
      models/            Seiteneinrichtung, Bericht über nicht Übernommenes
      services/          Dateien (DOCX, ODT, DOC, RTF …), Einstellungen, Sicherung, Vorlesen, LibreOffice/LanguageTool
      ai/                Claude und Ollama, Aufgaben, Gedächtnis
      proofing/          die Prüfung, Phonetik, Wortvorhersage, Autokorrektur, Silben
      resources/         register.json (das Band), regeln.json, themenwoerter.json, woerter.txt (355.324 Wörter)

    assets/              icons/ (Fluent- und Lucide-Zeichnungen), images/ (Logo und Bildschirmfotos),
                         symbole/varianten/ (das Programm-Symbol in vier Entwürfen), fonts/
    docs/                diese Dokumentation (BERICHT, PRUEFBOGEN, INSTALLATION, die Mini-Dateien)
    werkzeug/            Abgleich-Skripte: Prüfbogen gegen das Programm
    tests/               automatische Tests (pytest, ohne Bildschirm)

Ausführlicher steht alles in [README.md](README.md) (Aufbau der Qt-Fassung) und in [LIESMICH.md](LIESMICH.md).

---

[← Zurück zum README](../README.md)
