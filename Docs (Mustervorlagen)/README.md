<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="bilder/lunivo-office-dunkel.png">
    <img src="bilder/lunivo-office.png"
         style="max-width: 100%; height: auto;"
         alt="Lunivo-Office Logo">
  </picture>
</p>

<p align="center">
  <strong>Ein Raum für Worte.</strong><br>
  Was geschrieben wird, bleibt auf diesem Rechner.<br>
  Nichts geht hinaus, ohne dass du es selbst schickst.
</p>

<hr>

Ein Schreibprogramm wie LibreOffice Writer oder Word — mit einer **Schreibhilfe**,
die auch typische Fehler erkennt, die ein normaler Rechtschreibprüfer nicht
findet:

    das / dass       seit / seid       wider / wieder
    „wir hat"  →  „wir haben"          „größer wie"  →  „größer als"

Nicht *für* Menschen mit Legasthenie gebaut, sondern *von* einem —
[wie es dazu kam](doku/ENTSTEHUNG.md).

Kein Konto, keine Anmeldung, kein Internet nötig.

![Lunivo-Office mit einem Brief im Blatt und der Schreibhilfe rechts an der Seite](bilder/uebersicht.png)

## Dokumentation

- [ENTSTEHUNG](doku/ENTSTEHUNG.md) — Entstehung und Herkunft
- [FUNKTIONEN](doku/FUNKTIONEN.md) — Funktionen und Grenzen
- [SCHREIBHILFE](doku/SCHREIBHILFE.md) — Prüfen und Schreibhilfe
- [VORLAGEN](doku/VORLAGEN.md) — Vorlagen und Platzhalter
- [VORLESEN](doku/VORLESEN.md) — Vorlesen und Stimmen
- [LESEHILFE](doku/LESEHILFE.md) — Lesen und Darstellung
- [KI](doku/KI.md) — optionale KI
- [DRUCKEN](doku/DRUCKEN.md) — Drucken
- [BENUTZEROBERFLAECHE](doku/BENUTZEROBERFLAECHE.md) — Oberfläche
- [INSTALLATION](doku/INSTALLATION.md) — Starten und zusätzliche Komponenten
- [SCHRIFTEN](doku/SCHRIFTEN.md) — Schriften zum leichteren Lesen
- [AUFBAU](doku/AUFBAU.md) — Projektstruktur
- [MITMACHEN](doku/MITMACHEN.md) — Mitmachen
- [RICHTUNG](doku/RICHTUNG.md) — wohin das Projekt gehen soll
- [LIZENZ](doku/LIZENZ.md) — Lizenzen

## Starten

    ./starten.sh

Gebraucht wird GTK mit WebKit:

    sudo apt install python3-gi gir1.2-webkit2-4.1

## Mach mit

Dieses Projekt sucht Leute — **nicht in erster Linie Programmierer.**

Wenn dir Schreiben schwerfällt, bist du hier die wichtigste Person.

[Erzähl, woran du hängenbleibst](../../issues/new?template=erfahrung.yml)
· [Etwas geht nicht](../../issues/new?template=fehler.yml)
· [Etwas fehlt](../../issues/new?template=wunsch.yml)
· [Reden statt melden](../../discussions)

## Lizenz

[MIT](LICENSE) — benutzen, ändern und weitergeben ist erlaubt, auch gewerblich.
