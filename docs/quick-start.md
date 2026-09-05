# Schnellstart

Kurzanleitung, um Lunivo‑Office schnell lauffähig zu bekommen.

1. Repository klonen

   git clone https://github.com/kaysiebke-cell/Lunivo-Office.git

2. Abhängigkeiten (Entwicklung)

   npm install

3. Anwendung starten

   ./starten.sh

   Beim ersten Start wird ein Menüeintrag angelegt. Falls du die Anwendung nur im Browser testen willst (Entwicklung):

   python3 -m http.server 8322
   # dann http://localhost:8322/ öffnen

Wichtige Hinweise

- Für die GTK/Python Starter‑Umgebung werden auf Debian/Ubuntu folgende Pakete benötigt:

  sudo apt install python3-gi gir1.2-webkit2-4.1

- Viele Funktionen (z. B. .docx → .pdf) nutzen LibreOffice im Hintergrund. LibreOffice kann optional (~700 MB) aus dem lokalen Ordner geladen werden; ist es nicht vorhanden, wird das System‑LibreOffice verwendet.

Weitere Informationen: docs/requirements.md
