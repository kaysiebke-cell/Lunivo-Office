# Was WPS Writer bei Tabellen und Dokumentensteuerung kann

**Woher diese Liste stammt.** Nicht aus Bildschirmfotos und nicht aus dem
Gedächtnis, sondern aus dem Programm selbst. WPS Office liegt unter
`/opt/kingsoft/wps-office/office6/`, und seine Beschriftungen stehen in
den Qt-Sprachdateien `mui/en_US/wps.qm` und `wpstips.qm` — als UTF-16
zwischen den Daten. Die Auswertung lässt sich wiederholen:

```
python3 werkzeug/wps-befehle-lesen.py
```

Kay hat darauf bestanden, und er hatte recht: Aus den beiden Dateien
kamen **265 Befehle zu Tabellen** und **251 zur Dokumentensteuerung** —
mehr und genauer, als drei Fotos je hergeben.

Die englischen Namen sind die Originale. Dahinter steht, wie Lunivo es
nennt, oder dass es fehlt.

---

## Tabellen

### Was Lunivo hat

| WPS | Lunivo |
|---|---|
| Insert Table | Tabelle einfügen (mit Raster) |
| Table Properties | Eigenschaften der Tabelle |
| Insert Row Above / Below | Zeile darüber / darunter |
| Insert Column Left / Right | Spalte links / rechts |
| Delete Row / Column / Table | Zeile / Spalte / Tabelle löschen |
| Table Borders | Rahmen ein/aus |
| Header row | Erste Zeile als Kopf |
| Table Style | Vorlage (sechs Stück) |
| Cell Alignment | Ausrichtung |
| Cell Height / Width | Zellengröße |
| Move Table | Griff links oben, oder Tabelle nach oben/unten |
| Table Tools | Tabellenwerkzeuge (Reiter und Leiste) |

### Was fehlt — nach Dringlichkeit

1. **Merge Cells** — Zellen zusammenführen. Ohne sie lässt sich keine
   Überschrift über zwei Spalten bauen. Das braucht man ständig.
2. **Split Cells** — Zellen teilen. Die Gegenrichtung; beides gehört
   zusammen, sonst ist der erste Schritt nicht rückgängig zu machen.
3. **Convert Text to Table** / **Convert Table to Text** — wer eine Liste
   getippt hat, kommt sonst nicht weiter.
4. **AutoFit Column Width** / **Automatically adjust the table based on
   content** — Spalten an den Inhalt anpassen.
5. **Equal column width** / **Force equal column width** — alle Spalten
   gleich breit. Ein Klick statt Rechnen.
6. **View Table Gridlines** — Hilfslinien bei rahmenlosen Tabellen. Ohne
   sie schreibt man in ein unsichtbares Raster.
7. **Split Table** — eine Tabelle in zwei teilen.
8. **Repeat as header row at the top of each page** — die Kopfzeile auf
   jeder Seite wiederholen. Betrifft nur das Drucken, aber dort sehr.
9. **Select Row / Column / Cell / Table** — Auswahlbefehle.
10. **Allow row to break across pages** — ob eine Zeile umbrechen darf.

**Bewusst weggelassen:** *Draw Table* und *Table Eraser* (Tabelle mit dem
Stift zeichnen und radieren). Daran scheitern Leute in Word wie in WPS,
und das Raster kann dasselbe einfacher. *Multidiagonal Cell* ebenso — ein
Sonderfall aus dem chinesischen Formularwesen.

---

## Dokumentensteuerung

### Was Lunivo hat

| WPS | Lunivo |
|---|---|
| Page Setup | Seite einrichten |
| Header / Footer | Kopfzeile / Fußzeile |
| Page Break | Seitenumbruch |
| Column Break | Spaltenumbruch |
| Section Break | Abschnittswechsel |
| Watermark | Wasserzeichen |
| Track Changes | Änderungen verfolgen |
| Navigation Pane | Navigationsbereich |
| Outline | Gliederung |
| Restrict Editing | Bearbeitung sperren |

### Was fehlt — nach Dringlichkeit

1. **Bookmark** (Insert / Go to / Delete / Rename) — Textmarken. Lunivo
   hat ein Symbol dafür, aber keinen Befehl. In einem langen Schreiben
   ist das der Weg zurück an eine Stelle.
2. **Different first page header and footer** — erste Seite anders. Bei
   Briefen mit Briefkopf der Normalfall.
3. **Link to Previous Header / Footer** — Kopfzeile je Abschnitt eigen
   oder vom vorigen übernommen.
4. **Section Navigation** / **Section Management** — Abschnitte sehen und
   anspringen. Lunivo führt Abschnitte im Modell, zeigt sie aber nicht.
5. **Odd / Even Page Section Break** — Abschnitt auf gerader/ungerader
   Seite beginnen. Für beidseitigen Druck.
6. **Text Wrapping Break** — Zeilenumbruch ohne neuen Absatz.
7. **Outline Promote / Demote** — Überschriftenebene höher/tiefer. Die
   Gliederung zeigt Lunivo, ändern kann man sie dort nicht.
8. **Restart Each Section** — Nummerierung je Abschnitt neu.

---

[← Zurück zum README](../README.md) · [Der Aufbau der Optionen](aufbau-optionen.md)

---

## Bilder — nachgetragen am 12.09.2026

Kay: *„warum hast du nicht zu diesem Thema der Bildbearbeitung alles aus
dem WPS-Ordner?"* — Berechtigt. Das Werkzeug lag da, ich hatte es nur
für Tabellen benutzt. `werkzeug/wps-befehle-lesen.py` kennt jetzt auch
die Gruppe **BILDER UND OBJEKTE**.

### Was Lunivo hat

| WPS | Lunivo |
|---|---|
| Picture Tools | Reiter **Bildtools** |
| Insert Picture | Bild einfügen |
| Picture Size | Acht Griffe, dazu „Größe genau angeben" |
| Rotate · Rotate Left/Right 90 | Griff zum Drehen, in Fünf-Grad-Schritten |
| Crop by Shape | Elf Formen |
| Crop by Scale | Sechs Verhältnisse (1:1 bis 9:16) |
| Crop (Kante für Kante) | „Kante für Kante in Prozent…" |
| Reset Picture / Reset Size | Zuschnitt aufheben · Größe zurücksetzen |
| Wrap Text (Square, Tight, Top and Bottom, Behind, In Front) | Layoutoptionen, sechs Fassungen mit Bildchen |
| Lock anchor / Move with text | „Mit Text verschieben" / „Fester Text" |
| Picture Preview | Bild groß ansehen (1:1 · einpassen) |

### Was fehlt — nach Dringlichkeit

1. **Flip Horizontal / Flip Vertical** — spiegeln. Ein Zweizeiler über
   `transform: scaleX(-1)`, und man braucht es öfter, als man denkt.
2. **Rotate Left 90 / Right 90** — die zwei festen Knöpfe neben dem
   freien Drehgriff. Wer ein hochkant fotografiertes Blatt einfügt, will
   nicht zielen müssen.
3. **Bring Forward / Send Backward / Bring to Front / Send to Back** —
   die Ebenen. Lunivo kennt bisher nur „vor" und „hinter dem Text", nicht
   die Reihenfolge mehrerer Bilder untereinander.
4. **Alt-Text** (Alternativtext). Steht in WPS unter den Bildoptionen.
   Für ein Programm mit diesem Zweck gehört er eigentlich nach vorn: Er
   ist das, was das Vorlesen aus einem Bild machen kann.
5. **Set Transparent Color** — eine Farbe im Bild durchsichtig machen.
   Geht über einen SVG-Filter, ist aber ein eigenes Stück.
6. **Color · Grayscale · Black and White · Washout** — die vier
   Farbfassungen. Über CSS-Filter machbar: `grayscale(1)`,
   `contrast(...)`, `opacity(...)`.
7. **Brightness / Contrast** — Helligkeit und Kontrast, ebenfalls
   CSS-Filter.
8. **Picture Effects**: Shadow, Reflection, Glow, Soft Edges, Bevel.
   Schatten und weiche Kanten sind billig (`box-shadow`, `mask`), der
   Rest ist Zierde.
9. **Compress Pictures** — verkleinert die Datei. Lohnt erst, wenn
   jemand Fotos aus der Kamera einfügt.
10. **Group / Ungroup**, **Align Objects** — erst sinnvoll, wenn mehrere
    Objekte frei auf der Seite liegen können. Das können sie seit heute.

**Bewusst weggelassen:** *Convert Picture to Text* (Texterkennung — ein
eigenes Programm), die zwanzig *Shadow Styles* und *Artistic Effects*.
Nicht alles, was WPS hat, gehört in ein Programm für Menschen mit
Legasthenie.
