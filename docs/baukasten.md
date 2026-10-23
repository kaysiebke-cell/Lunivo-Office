# Der Baukasten der Oberfläche

`src/lunivo_writer/ui/baukasten/` — Bausteine, die an vielen Stellen wiederkehren. **Ein Baustein, viele Aufrufer:**
Er kennt nur seinen eigenen Wert und meldet ihn (Signal oder Rückgabewert). Was damit geschieht — Schriftfarbe,
Schattierung, Seitenfarbe, Rahmen, Füllung —, entscheidet der Aufrufer.

| Datei | Baustein | Meldet |
|---|---|---|
| `farben.py` | Daten: 10 Themenfarben mit je 5 Abstufungen, 10 Standardfarben, „zuletzt benutzt“ (QSettings) | — |
| `farbpalette.py` | `FarbPalette` (Popup), `FarbFeld` (Knopf für Dialoge), `FarbKnopf` (geteilter Knopf fürs Band), `weitere_farben()` (Fenster „Farben“, siehe `farbwaehler.py`: Standard · Benutzerdefiniert · Erweitert, Farbmodell RGB/HSV/HSL, Hex, Neu/Aktuell) | `gewaehlt(QColor \| None)`, `ueberfahren`, `verlassen` |
| `linien.py` | `Linie` (Farbe, pt, Art), `LinienWahl` (Zeile aus Art, Stärke, Farbe), `RahmenMenue` (unten, oben, links, rechts, kein, alle, außen, innen) | `geaendert(Linie)`, `gewaehlt(RahmenSeiten, schluessel)` |
| `menue_liste.py` | `MenueListe`: Zeilen mit Symbol, Kürzel, Haken, Untermenü, auch aus einer Beschreibung (`aus_liste`) | `triggered` je Zeile |
| `raster_auswahl.py` | `RasterAuswahl`: Kacheln mit „Mehr …“-Fuß (Aufzählung, Vorlagen, Ränder, Deckblätter) | `gewaehlt(schluessel)` |
| `zellen_raster.py` | `ZellenRaster`: Zellen überfahren, „3 × 4 Tabelle“ lesen, klicken; mit `fuss()` weitere Einträge darunter | `gewaehlt(zeilen, spalten)` |
| `listen_symbole.py` | `liste_zeichner()`: Vorschaubild einer Aufzählungs- oder Nummerierungsart für die Kachel-Auswahl | — |
| `mass_feld.py` | `MassSpin`: Zahl mit Maßeinheit (intern mm), `set_einheit()` | `valueChanged` |
| `dialog_rahmen.py` | `DialogRahmen`: Formular, optionale Vorschau, OK/Abbrechen, Zusatzknöpfe („Entfernen“) | `ergebnis()` |

## Regeln

1. **Ein Popup liefert einen Wert** — `QColor` oder `None` („Keine Farbe“). Es kennt den Aufrufer nicht.
2. **Popups wirken sofort, Dialoge haben Vorschau und OK/Abbrechen.**
3. **„Keine“ und „Zuletzt benutzt“ stehen immer an derselben Stelle.**
4. **Nicht Mögliches bleibt grau sichtbar**, statt zu fehlen.
5. **Nichts nachbauen:** Wer eine Farbe braucht, nimmt `FarbPalette`/`FarbFeld`/`weitere_farben`, wer eine Linie braucht,
   `LinienWahl`/`Linie`, wer ein Maß braucht, `MassSpin`.

## Wer den Baukasten benutzt

- **Band** (`core/commands.py`): Schriftfarbe, Hervorheben, Seitenfarbe, Absatz- und Tabellenschattierung, Formfüllung,
  Formkontur — alle über `_farbmenue()` bzw. `FarbPalette`. Die Live-Vorschau hängt an `ueberfahren`/`verlassen`.
- **Dialoge:** Wasserzeichen und Seitenrahmen (`DialogRahmen`, `FarbFeld`, `LinienWahl`, mit Vorschau), Formen/WordArt
  (`FarbFeld`), Silben farbig, Seite einrichten und Absatz (`MassSpin`).

## Neues Fenster oder neue Farbstelle

```python
from lunivo_writer.ui.baukasten import DialogRahmen, FarbFeld, LinienWahl, Linie

class MeinDialog(DialogRahmen):
    def __init__(self, parent):
        super().__init__(parent, "Mein Dialog", vorschau=self._male)
        self.farbe = FarbFeld("#1971c2", "Füllfarbe", keine_text="Keine Füllung")
        self.linie = LinienWahl(Linie("#000000", 1.0, "einfach"))
        self.zeile("Füllung", self.farbe); self.zeile("Linie", self.linie)
        self.farbe.farbeGeaendert.connect(self.aktualisieren); self.linie.geaendert.connect(self.aktualisieren)

    def _male(self, painter, rect): ...
    def ergebnis(self): return {"fuell": self.farbe.farbe, "linie": self.linie.linie().text()}
```

## Absatzrahmen

Der Rahmen eines Absatzes steht als Text `farbe|pt|art` am Absatz (`B_RAHMEN`); ein vierter Teil nennt die Seiten, wenn nicht alle
vier gemeint sind: `t` oben, `b` unten, `l` links, `r` rechts, `h` zwischen zwei Absätzen (`editor/linie.py`, Klasse `Linie`).
Ohne vierten Teil gelten alle Seiten, ältere Dateien bleiben also gültig. Gezeichnet wird in `editor/pagination.py`, nach Word
gespeichert und gelesen als `w:pBdr` (`top`, `left`, `bottom`, `right`, `between`; Linienarten einfach, doppelt, gestrichelt,
gepunktet, Strich-Punkt).

- **Menü** (`RahmenMenue`): schaltet einzelne Seiten ein/aus, „Alle“, „Außen“, „Kein“; neue Rahmen übernehmen die zuletzt
  eingestellte Linie.
- **Fenster „Rahmen und Schattierung“** (`ui/baukasten/rahmen_schattierung.py`, Muster in `editor/muster.py`): Reiter Rahmen (Einstellung, Linienart, Farbe, Breite, Vorschau mit Kantenknöpfen), Seitenrand und Schattierung (Füllfarbe, 37 Muster, Musterfarbe). Gespeichert wird das Muster am Absatz (`B_MUSTER`) und in DOCX als `w:shd`.

## Fenster für Absatz, Schrift, Listen, Tasten und Effekte

Alle Fenster liefern Werte und formatieren selbst nichts; der Aufrufer (Band, Editor, Formatvorlage) setzt das Ergebnis. Die Knopfzeile
unten kommt überall von `fussleiste` (`dialog_rahmen.py`), Maße von `EinheitFeld` / `MassSpin` (`mass_feld.py`).

| Baustein | Datei | Was dahinter steckt |
|---|---|---|
| Absatz | `absatz_dialog.py` | Einzüge, Abstände, Zeilenabstand (Faktor, Mindestens, Genau), Gliederungsebene, Seitenumbruch, Absatzoptionen (`editor/absatzopt.py`); Umbruchregeln wirkt `editor/seitenfluss.py` |
| Tabstopps | `tabstopp_dialog.py` | Position, Ausrichtung, Füllzeichen (`editor/tabfuell.py`, gezeichnet), Standardtabstopps (`w:defaultTabStop`) |
| Schriftart | `schriftart_dialog.py` | alle Felder wie im WPS: asiatisch/westlich/komplex, Unterstreichungsarten, Betonungszeichen, Effekte, Zeichenabstand; Zeichnen der Extras in `editor/textfx.py` |
| Texteffekte | `texteffekt_dialog.py` | Füllung (Farbe, Verlauf), Kontur, Schatten, Reflektion, Leuchten, 3D; Zeichnen in `editor/textfx.py`, DOCX als `w14:*` in `editor/texteffekt.py` |
| Nummerierung | `liste_dialog.py` | Aufzählung, Nummerierung, mehrstufige Gliederung (`editor/mehrstufig.py`, selbst gezeichnet), Anpassen-Fenster |
| Tastenkombination | `tasten_dialog.py` | eine Tastenkombination aufnehmen, Belegung prüfen |
| Formatvorlage | `formatvorlage_dialog.py` | Name, Basis, Folgevorlage, Leiste, Format ▾ mit Schriftart, Absatz, Tabstopps, Rahmen, Nummerierung, Texteffekte, Verknüpfung |
| Hilfen | `schiebe_feld.py`, `voreinstellung_menue.py`, `pipette.py` | Regler mit Feld, Popup mit Bildchen in Abschnitten, Farbe vom Bildschirm |

Tests: `tests/test_baukasten.py`.

## Zusatzfenster in der Seitenleiste

Seltene Einstellungen (Absatz, Schriftart, Rahmen, Listen, Seite einrichten …) öffnen sich nicht über dem Text, sondern als Seite in der
Seitenleiste — nur solange man sie bearbeitet. Die Breite der Seitenleiste ändert sich nie; der Inhalt passt sich an.
Jeder Baustein macht genau eine Sache:

| Baustein | Datei | Aufgabe |
|---|---|---|
| `PanelFaehig` | `zusatz_panel.py` | Markierung für ein Fenster: `exec()` zeigt es in der Seitenleiste (sonst wie bisher als Fenster) |
| `ZusatzPanel` | `zusatz_panel.py` | die Seite in der Seitenleiste: Kopf mit Titel und ✕, Rollbereich ohne seitliche Leiste, Unterfenster mit „←“ |
| `FormularGitter` | `formular_gitter.py` | Felder, die sich der Breite anpassen: `zeile(Beschriftung, Feld)`, `breit(Feld)`, `reihe((Beschr., Feld), …)`. Breit: zwei Paare nebeneinander; schmal: eines je Zeile; sehr schmal: Beschriftung über dem Feld |
| `AngepassteReiter` | `formular_gitter.py` | Reiter, deren Höhe dem gewählten Reiter folgt (kein leerer Platz unter kurzen Reitern) |
| `UmbruchSchalter` | `formular_gitter.py` | Ankreuzfeld, dessen langer Text umbricht |
| `FlussLayout` | `formular_gitter.py` | Reihe von Feldern, die wie Text umbricht (Beschriftung und Feld bleiben beisammen) |
| `schmal_machen` | `schmal.py` | **Notbehelf** für Fenster, die noch nicht aus Bausteinen gebaut sind: bricht zu breite Zeilen nachträglich um. Neue Fenster bauen mit `FormularGitter`, nicht darauf verlassen |

Ein Fenster, das aus einem offenen Zusatzfenster heraus aufgerufen wird (zum Beispiel „Farben“ aus „Rahmen und Schattierung“), legt sich als weitere Seite darüber (mit „←“); das darunter bleibt offen.

Neues Fenster: `class MeinDialog(PanelFaehig, QDialog)`, Felder in `FormularGitter`-Gruppen. Fertig umgebaut (alle Fenster der Seitenleiste außer Rahmen und Schattierung): Farben, Absatz, Schriftart, Tabstopps, Layout, Nummerierung, Gliederung, Texteffekte, Formatvorlage. Dazu KI-Einstellungen (`KIEinstellungenDialog`, `kompakt_machen()` kürzt die Reiternamen, die Sprachlisten stehen untereinander).

Platz in der Seitenleiste: Wer Größen der Seitenleiste braucht, bietet `passe_an(breite, hoehe)` an (`ZusatzPanel` ruft es mit `verfuegbar` und `verfuegbar_hoehe` auf, die die Seitenleiste aus ihrer echten Größe setzt); Beispiele: Farbraster, Rahmenvorschau, Kachelzahl der Nummerierung, Texteffekte. `AngepassteReiter` und der Stapel der KI-Einstellungen richten die Höhe nach der gewählten Seite. Prüfung: `test_seitenleisten_seiten_passen_in_echte_groesse`.
Auf dem Notbehelf nur noch: Rahmen und Schattierung (bewusst: Spalten mit Vorschau, `schmal_nein` schützt die Kantenknöpfe) und die kleinen Fenster mit `QFormLayout`.
Tests, die Fenster per Zeitgeber schließen, müssen auch die Fenster in der Seitenleiste finden (`tests/test_smoke_befehle.py`).

## Befehle nach Aufgaben

`core/commands.py` enthält nur noch die Grundfunktionen von `Befehle` (Aktion suchen, ausführen, Zustand). Die Befehle selbst stehen in
`core/befehle/`, je Aufgabe ein Baustein: `text` (Zeichen und Absatz), `bearbeiten`, `einfuegen`, `seite` (Seite, Abschnitte, Spalten),
`pruefen` (Schreibhilfe, Vergleichen), `ansicht`, `datei`, `verweise`, `kommentare`, `kontext` (Tabelle, Bild, Formen), `ki`, `extern`.
Ein neuer Befehl kommt in den Baustein seiner Aufgabe; `Befehle` setzt sie zusammen. Kein Baustein importiert `commands.py`.

## Aufbau der großen Klassen

Die drei großen Klassen sind nach Aufgaben in Bausteine (Mixins) geteilt. Die Hauptdatei behält Aufbau, Signale und Qt-Ereignisse
(`…Event`), die Bausteine die Aufgaben:

| Klasse | Hauptdatei | Bausteine |
|---|---|---|
| `Befehle` | `core/commands.py` (Grundfunktionen) | `core/befehle/*.py` |
| `MainWindow` | `ui/main_window.py` | `ui/hauptfenster/`: `dateien`, `bearbeiten`, `oberflaeche`, `backstage_steuerung` |
| `DocumentEditor` | `ui/document/document_editor.py` | `ui/document/editor_*.py`: `anzeige`, `spalten`, `seiten`, `formatierung`, `bilder`, `schreibhilfe` |
| `OptionenAnsicht` | `ui/dialogs/optionen.py` | `ui/dialogs/optionen_seiten/`: `lesen`, `ansicht`, `datei`, `befehle`, `lunivo` |

Regel: Ein neuer Befehl, eine neue Editor-Funktion oder eine neue Optionen-Seite kommt in den Baustein ihrer Aufgabe, nicht in die Hauptdatei.
Bausteine kennen die Hauptdatei nicht (kein Import zurück); Werte, die mehrere brauchen, stehen in `gemeinsam.py` des jeweiligen Ordners.
