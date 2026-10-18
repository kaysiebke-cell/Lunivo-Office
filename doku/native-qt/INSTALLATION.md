# Installation unter Linux Mint

## Kern (genügt zum Schreiben, Speichern als DOCX, Drucken, PDF)
```bash
sudo apt install python3 python3-venv libxcb-cursor0 libegl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0
./starten-qt.sh
```
Das Skript legt `.venv` im Projektordner an und installiert `PySide6`, `python-docx` und `msoffcrypto-tool` (Kennwortschutz) aus `requirements.txt`.
Das System-Python bleibt unberührt. Fehlt `python3-venv`, nennt das Skript den passenden `apt`-Befehl.

## Optional
| Wofür | Wie | Ohne |
|---|---|---|
| ODT/DOC/RTF öffnen und speichern | `sudo apt install libreoffice-writer` | DOCX/TXT gehen weiter, ODT-Export über Qt (ohne Kopf-/Fußzeile) |
| Gründliche Prüfung (Grammatik) | LanguageTool entpacken nach `~/.local/share/<App>/languagetool` und `sudo apt install default-jre` | eigene Regeln bleiben aktiv |
| Vorlesen | `sudo apt install speech-dispatcher` oder `./stimme-holen.sh` (Piper) | Meldung „keine Sprachausgabe“ |
| KI lokal | Ollama installieren, `ollama pull <modell>` | KI-Knöpfe bleiben grau |
| KI Claude | eigener Schlüssel unter Optionen ▸ Schreibhilfe und KI | KI-Knöpfe bleiben grau |
| Leseschriften | `./schrift-holen.sh` | normale Schriften |

`<App>` = Anwendungsdatenordner (steht unter Optionen ▸ Erweitert; üblicherweise `~/.local/share/Lunivo Writer`).

## Deinstallation
`./starten-qt.sh --weg` entfernt den Menüeintrag. Danach den Projektordner (inkl. `.venv`) löschen. Dokumente werden nie
angefasst. Einstellungen und Gelerntes liegen unter `~/.config/Lunivo` und `~/.local/share/Lunivo Writer` — erst auf
Ihren Wunsch löschen.

## Speicherorte
Einstellungen: `~/.config/Lunivo/Lunivo Writer.conf` · Gelerntes: `gelernt.json` · KI-Daten und Schlüssel: `ki.json`
(nur für Sie lesbar) · Absturzsicherung: `recovery/` · alles im Anwendungsdatenordner.
