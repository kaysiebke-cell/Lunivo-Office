# Aufbau

start.py             Fenster, Server, Schriften, LibreOffice, Vorlesen
    starten.sh           startet es und schreibt den Menüeintrag
    stimme-holen.sh      holt Piper und die Stimme „Thorsten“ (freiwillig)
    schrift-holen.sh     holt Schriften zum leichteren Lesen (freiwillig)

    oberflaeche/         alles, was im Fenster zu sehen ist
      index.html         die Oberfläche
      css/programm.css   das Aussehen
      js/programm.js     Menüs, Werkzeuge, Seitenleiste, Statuszeile
      js/dokument.js     das Dokument: lesen, zeigen, ersetzen, formatieren
      js/dateien.js      öffnen und speichern
      js/pruefung.js     die Prüfung, Phonetik, Wortvorhersage
      js/ki.js           Claude und Ollama, Gedächtnis, Sicherung
      js/einstellungen.js  die Einstellungsseite
      daten/regeln.js    der Wortschatz der Prüfung
      daten/woerter.txt  355.321 deutsche Wörter
      daten/symbole.js   die 150 Zeichnungen der Knöpfe
      daten/symbolkatalog.js  1801 Zeichnungen zur Auswahl (erst bei Bedarf geladen)

    werkzeug/            nichts davon lädt das Programm — Werkzeug für die Werkstatt
      symbole.html       den Symbolkatalog durchsehen, im Browser öffnen
      katalog-bauen.py   baut den Katalog aus einem Ordner voller .svg neu
      svg-zu-pfad.py     rechnet <circle>, <rect>, <line> in einen Pfad um
      bildschirmfoto.py  nimmt die Bilder für dieses README auf

    doku/                ENTSTEHUNG, RICHTUNG und das ausführliche LIESMICH
    symbole/             das Symbol als SVG und in allen Größen
    bilder/              Logo, Marke und die Bildschirmfotos

Ausführlicher steht alles in [LIESMICH.md](doku/LIESMICH.md).
