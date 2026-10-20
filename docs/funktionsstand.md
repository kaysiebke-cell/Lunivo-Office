# Funktionsstand des Bandes

Geschrieben von `werkzeug/funktionspruefung.py`; jeder Knopf und Menüpunkt wird in vier Lagen gedrückt (Text markiert, vorformatierter Text, Zeiger in der Tabelle, Bild markiert). Stand: 20.10.2026. **Reiter Ansicht fehlt noch** (siehe unten).

| Reiter | wirkt | Dialog | Menü | keine Wirkung | fehlt | Fehler |
|---|---|---|---|---|---|---|
| Abschnitt | 31 | 6 | 0 | 1 | 1 | 1 |
| Einfügen | 11 | 25 | 3 | 0 | 1 | 0 |
| Referenzen | 0 | 0 | 0 | 0 | 0 | 0 |
| Schreibhilfe | 18 | 20 | 1 | 1 | 1 | 0 |
| Seitenlayout | 32 | 13 | 3 | 1 | 2 | 1 |
| Sendungen | 0 | 0 | 0 | 0 | 0 | 0 |
| Start | 89 | 10 | 1 | 1 | 1 | 0 |
| Überprüfen | 14 | 4 | 0 | 0 | 0 | 0 |

## Was nicht (richtig) geht

### Abschnitt
#### Fehler (1)

- Abschnitt ▸ Orientierung ▸ Querformat — `TypeError: Befehle.w_querJetzt() takes 1 positional argument but 2 were given`

#### fehlt (1)

- Abschnitt ▸ Gerade und ungerade Seiten sind unterschiedlich

#### keine Wirkung (1)

- Abschnitt ▸ Ränder ▸ Normal
### Einfügen
#### fehlt (1)

- Einfügen ▸ Tabellenblatt
### Referenzen

### Schreibhilfe
#### fehlt (1)

- Schreibhilfe ▸ Textbausteine ▸ Bausteine verwalten…

#### keine Wirkung (1)

- Schreibhilfe ▸ Dokumentprüfung ▸ Rechtschreibung

#### grau (1)

- Schreibhilfe ▸ Eigene Assistenten ▸ Noch keine eigenen Assistenten

#### Dialog mit OK bestätigt: nichts verändert (1)

- Schreibhilfe ▸ Text in Bild — KIKonfigurationDialog: KI-Konfiguration
### Seitenlayout
#### Fehler (1)

- Seitenlayout ▸ Ausrichtung ▸ Querformat — `TypeError: Befehle.w_querJetzt() takes 1 positional argument but 2 were given`

#### fehlt (2)

- Seitenlayout ▸ Effekte
- Seitenlayout ▸ Umbrüche ▸ Textflussumbruch

#### keine Wirkung (1)

- Seitenlayout ▸ Ausrichtung ▸ Hochformat
### Sendungen

### Start
#### fehlt (1)

- Start ▸ Wort-Extras

#### keine Wirkung (1)

- Start ▸ Weitere Formatvorlagen

#### Dialog mit OK bestätigt: nichts verändert (1)

- Start ▸ Stile — StileVerwaltenDialog: Formatvorlagen verwalten
### Überprüfen

