# Lunivo Language Bridge – Korrekturarchitektur

## Ziel

Die Rechtschreibprüfung, Grammatikprüfung, AutoKorrektur und KI-Korrektur dürfen nicht mehr unabhängig voneinander arbeiten.

Lunivo benötigt eine zentrale Sprachinstanz:

```text
                         LUNIVO LANGUAGE BRIDGE
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              Sprachkontext               Dokumentkontext
                    │                           │
          ┌─────────┼─────────┐        ┌───────┼────────┐
          │         │         │        │       │        │
      Regeldaten Benutzerwörter Sprache Version Prüfstatus
          │         │         │        │       │        │
          └─────────┴─────────┴────────┴───────┴────────┘
                                  │
                         ZENTRALE PRÜFUNG
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
       Rechtschreibung        Grammatik                KI
       SpellingEngine        GrammarEngine          AIEngine
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                         ZUSAMMENFÜHRUNG
                                  │
                                  ▼
                         EINHEITLICHER
                         FEHLERSTATUS
                                  │
                                  ▼
                              DOKUMENT
```

Die Language Bridge besitzt den zentralen Zustand und koordiniert die Prüfer. Die eigentliche Prüfungslogik bleibt in den jeweiligen Prüfern bzw. Engines.

---

# 1. Zentrale Quelle für Sprachregeln

Die bestehende Datei

```text
oberflaeche/daten/regeln.js
```

bleibt die zentrale Quelle für die Lunivo-Sprachregeln.

Dort vorhandene Daten werden **nicht dupliziert**.

Dazu gehören insbesondere:

* `WOERTERBUCH`
* `KEIN_HAUPTWORT`
* `FUERWOERTER`
* `DENK_ZEITWOERTER`
* `DENK_ZEITWOERTER_ENG`
* `DASS_EIGENSCHAFTEN`
* `FOLGT_NEBENSATZ_ZUSAETZLICH`
* `ZEITANGABEN`
* `STEIGERUNGEN`
* `NEBENSATZ_WOERTER`
* `KEIN_KOMMA_DAVOR`
* `ZEITWOERTER`
* weitere vorhandene Regeldaten

`regeln.js` ist damit die gemeinsame Regelquelle für die vorhandenen Prüfungen.

Die Language Bridge importiert bzw. erhält Zugriff auf diese Daten. Sie erstellt keine zweite Kopie des Wörterbuchs.

---

# 2. Neue zentrale Instanz

Neue Datei:

```text
oberflaeche/js/language-bridge.js
```

Die Language Bridge ist die zentrale Schnittstelle zwischen Dokument, Sprachprüfung und KI.

Sie verwaltet mindestens:

```text
LanguageBridge
│
├── Sprache
├── Dokumenttext
├── Dokumentversion
├── Regeldaten
├── Benutzerwörter
├── Ignorierte Wörter
├── Akzeptierte Korrekturen
├── Aktive Fehler
├── Korrekturvorschläge
├── Prüfstatus
├── Prüfungs-ID
└── invalidierte Bereiche
```

Die Bridge besitzt den Zustand.

Die einzelnen Prüfer besitzen die Prüfungslogik.

```text
LanguageBridge
      │
      ├── SpellingEngine
      ├── GrammarEngine
      └── AIEngine
```

Dadurch wird verhindert, dass jeder Prüfer einen eigenen Sprachzustand aufbaut.

---

# 3. Einheitlicher Sprachkontext

Alle Prüfer müssen denselben Sprachkontext verwenden.

Beispiel:

```js
{
    language: 'de-DE',
    documentVersion: 0,
    text: '',
    userWords: [],
    ignoredWords: [],
    acceptedCorrections: [],
    issues: [],
    invalidatedRanges: [],
    checking: false,
    checkId: 0
}
```

Die Sprache wird nicht mehr nur für eine einzelne Prüfung gesetzt.

Wenn der Benutzer

```text
Sprache für Korrekturhilfen…
```

ändert, informiert diese Änderung die komplette Language Bridge.

Damit verwenden:

* Rechtschreibung
* Grammatik
* AutoKorrektur
* KI

dieselbe Spracheinstellung.

Eine Änderung der Sprache invalidiert vorhandene Prüfergebnisse.

---

# 4. Klare API der Language Bridge

Die Language Bridge sollte eine eindeutige öffentliche Schnittstelle besitzen.

Beispiel:

```js
LanguageBridge.setLanguage(language)

LanguageBridge.setDocument(text)

LanguageBridge.updateDocument(text, range)

LanguageBridge.invalidate(range)

LanguageBridge.check()

LanguageBridge.checkRange(start, end)

LanguageBridge.acceptIssue(issueId)

LanguageBridge.ignoreIssue(issueId)

LanguageBridge.applyCorrection(issueId, suggestion)

LanguageBridge.addUserWord(word)

LanguageBridge.removeUserWord(word)

LanguageBridge.getIssues()

LanguageBridge.getActiveIssues()

LanguageBridge.getContext()

LanguageBridge.getStatus()
```

`programm.js` greift möglichst nur über diese Schnittstelle auf den Sprachstatus zu.

---

# 5. Einheitlicher Fehlerstatus

Jeder erkannte Fehler wird intern einheitlich dargestellt.

Beispiel:

```js
{
    id: 'language-issue-123',
    source: 'spelling',
    type: 'word',
    start: 125,
    end: 134,
    text: 'wiederspiegeln',
    suggestions: [
        'widerspiegeln'
    ],
    confidence: 1,
    documentVersion: 15,
    checkId: 42,
    state: 'active'
}
```

Mögliche Quellen:

```text
spelling
grammar
ai
```

Mögliche Zustände:

```text
active
accepted
ignored
corrected
```

Damit wissen alle Systeme, ob ein Fehler bereits bekannt, akzeptiert, ignoriert oder korrigiert wurde.

---

# 6. Fehler-Lebenszyklus

Für jeden Fehler muss eindeutig festgelegt sein, was mit ihm passiert.

```text
                 erkannt
                    │
                    ▼
                 active
               /    │    \
              /     │     \
             ▼      ▼      ▼
        accepted  ignored corrected
                         │
                         ▼
                    neu prüfen
```

Ein Fehler darf nicht einfach nur aus der Oberfläche entfernt werden.

Bei einer Aktion muss auch der interne Zustand aktualisiert werden.

Nicht mehr relevante Fehler dürfen aus dem aktiven Fehlerbestand entfernt werden, wenn die betroffene Dokumentversion veraltet ist oder der Bereich erneut geprüft wurde.

---

# 7. Rechtschreibung

Die bisherige Funktion

```js
B.rechtschreibung()
```

schaltet aktuell das native Browser-Spellchecking über

```js
feld.spellcheck
```

ein oder aus.

Das ist problematisch, weil der Browser damit unabhängig von Lunivos eigenen Regeln arbeitet.

## Neue Regel

Die native Browser-Rechtschreibprüfung darf nicht mehr die führende Fehlerquelle sein.

Bei den relevanten Editoren wird deshalb das native Spellchecking deaktiviert:

```js
feld.spellcheck = false;
```

Die führende Instanz ist:

```text
Dokument
   │
   ▼
LanguageBridge
   │
   ▼
SpellingEngine
   │
   ▼
einheitlicher Fehlerstatus
```

Die vorhandenen Lunivo-Regeldaten aus `regeln.js` werden weiterverwendet.

---

# 8. Rote Wellenlinien

Die Funktion

```text
Rote Wellenlinien
```

bleibt in der Oberfläche bestehen.

Sie steuert künftig ausschließlich die Anzeige der von Lunivo erkannten Fehler.

Nicht:

```text
Browser entscheidet
```

sondern:

```text
LanguageBridge
      │
      ▼
aktiver Fehler?
      │
      ▼
Anzeige erlaubt?
      │
      ▼
rote Wellenlinie
```

Die UI erzeugt dadurch keine eigene Fehlerlogik.

Die Wellenlinien sind ausschließlich eine Darstellung des zentralen Language-Bridge-Status.

---

# 9. Benutzerwörter

Benutzerwörter gehören zur Language Bridge.

Beispiel:

```text
Lunivo
OpenAI
Firmenname
Produktname
Eigenname
```

Wenn ein Wort vom Benutzer akzeptiert wurde:

```text
Wort
 │
 ▼
LanguageBridge
 │
 ▼
Benutzerwörter
 │
 ▼
nicht erneut als unbekannt melden
```

Ein Benutzerwort darf weder von der Rechtschreibung noch von der Grammatikprüfung erneut als unbekanntes Wort behandelt werden.

Es wird nicht in `regeln.js` geschrieben.

Damit bleibt:

```text
regeln.js
    = zentrale feste Sprachregeln

LanguageBridge
    = benutzerspezifischer Sprachzustand
```

---

# 10. Ignorierte Wörter und Fehler

Ignorierte Wörter bzw. ignorierte Fehler werden zentral gespeichert.

Beispiel:

```js
{
    word: 'Lunivo',
    language: 'de-DE'
}
```

oder bei einem konkreten Fehler:

```js
{
    issueSignature: 'spelling|wiederspiegeln|125|134',
    state: 'ignored'
}
```

Die genaue Persistenz kann später an die vorhandene Speicherlogik von Lunivo angebunden werden.

Wichtig ist, dass nicht jeder Prüfer seine eigene Ignore-Liste besitzt.

---

# 11. Grammatikprüfung

Die Grammatikprüfung verwendet ebenfalls die Language Bridge.

```text
Dokument
   │
   ▼
LanguageBridge
   │
   ├── Wortinformationen
   ├── Satzinformationen
   ├── Sprachkontext
   ├── Benutzerwörter
   └── vorhandene Regeldaten
            │
            ▼
       GrammarEngine
            │
            ▼
       LanguageBridge
```

Die Grammatikprüfung darf keine eigene parallele Sprachkonfiguration aufbauen.

Sie erhält Sprache und Kontext von der Bridge.

---

# 12. AutoKorrektur

Die bestehende

```text
AutoKorrektur
```

bleibt erhalten.

Sie arbeitet jedoch über denselben Sprachkontext.

Ablauf:

```text
Texteingabe
    │
    ▼
AutoKorrektur
    │
    ▼
Dokument geändert
    │
    ▼
LanguageBridge.updateDocument()
    │
    ▼
betroffenen Bereich invalidieren
    │
    ▼
Bereich neu prüfen
```

Nach einer AutoKorrektur muss die Language Bridge den tatsächlich geänderten Text kennen.

Dadurch bleibt der Fehlerstatus aktuell.

---

# 13. Dokumentänderungen und Debouncing

Nicht jede einzelne Tastatureingabe darf sofort eine vollständige Prüfung auslösen.

Stattdessen:

```text
Tastatureingabe
      │
      ▼
Dokumentänderung
      │
      ▼
LanguageBridge.updateDocument()
      │
      ▼
Bereich invalidieren
      │
      ▼
Debounce
      │
      ▼
betroffenen Bereich prüfen
```

Bei schnellen Eingaben werden mehrere Änderungen zusammengefasst.

Eine vollständige Dokumentprüfung bleibt weiterhin für

```text
Gründlich prüfen
```

möglich.

---

# 14. Betroffene Bereiche

Bei einer Änderung sollte möglichst nur der betroffene Bereich neu geprüft werden.

Beispiel:

```js
updateDocument(text, {
    start: 120,
    end: 135
});
```

Die Bridge erweitert den Bereich bei Bedarf um angrenzende Wörter oder Sätze.

Das ist wichtig, weil eine Änderung an einem Wort auch Auswirkungen auf:

* Satzgrenzen
* Kommas
* Grammatik
* Folgefehler

haben kann.

Daher darf die Bereichsprüfung intern einen Sicherheitsbereich verwenden.

---

# 15. Dokumentversion

Die Bridge führt eine Dokumentversion.

Beispiel:

```js
documentVersion: 15
```

Nach einer Änderung:

```js
documentVersion: 16
```

Prüfergebnisse gehören immer zu einer bestimmten Dokumentversion.

Beispiel:

```js
{
    id: 'language-issue-456',
    documentVersion: 15,
    ...
}
```

Wird das Dokument auf Version `16` geändert, dürfen Ergebnisse der Version `15` nicht ungeprüft auf den neuen Text angewendet werden.

---

# 16. Prüfungs-ID und asynchrone Ergebnisse

Da die KI asynchron arbeitet, reicht die Dokumentversion alleine nicht immer aus.

Jeder Prüflauf erhält deshalb zusätzlich eine Prüfungs-ID:

```js
checkId: 42
```

Beispiel:

```js
{
    documentVersion: 15,
    checkId: 42,
    source: 'ai'
}
```

Kommt später ein KI-Ergebnis zurück, prüft die Language Bridge:

```text
Ist documentVersion noch aktuell?
        │
        ├── nein → Ergebnis verwerfen
        │
        └── ja
             │
             ▼
        checkId gültig?
             │
             ├── nein → Ergebnis verwerfen
             │
             └── ja → Ergebnis übernehmen
```

Damit können alte KI-Ergebnisse nicht versehentlich wieder im Dokument erscheinen.

---

# 17. KI-Korrektur

Die KI darf nicht unabhängig vom normalen Korrektursystem arbeiten.

Die KI erhält den gemeinsamen Kontext:

```text
LanguageBridge
      │
      ├── Sprache
      ├── Dokumenttext
      ├── Benutzerwörter
      ├── ignorierte Wörter
      ├── bekannte Fehler
      ├── akzeptierte Korrekturen
      └── vorhandene Korrekturvorschläge
             │
             ▼
          AIEngine
```

Die KI darf insbesondere kein Wort als Fehler behandeln, das von der Language Bridge als

```text
accepted
```

oder

```text
user word
```

markiert wurde.

Die KI erhält nur den Kontext, den sie für die aktuelle Prüfung benötigt.

---

# 18. KI-Vorschläge

KI-Vorschläge werden ebenfalls als normale Language-Bridge-Ergebnisse gespeichert.

Beispiel:

```js
{
    id: 'language-issue-456',
    source: 'ai',
    type: 'style',
    start: 200,
    end: 215,
    text: '...',
    suggestions: [
        '...'
    ],
    confidence: 0.82,
    documentVersion: 15,
    checkId: 42,
    state: 'active'
}
```

Damit kann die Oberfläche dieselbe Fehler-/Vorschlagsstruktur verwenden.

---

# 19. Keine unabhängigen KI-Zustände

Die KI darf keinen eigenen dauerhaften Fehlerbestand führen.

Nicht:

```text
KI
 ├── eigene Fehlerliste
 ├── eigene Sprache
 ├── eigene Benutzerwörter
 └── eigener Dokumentstatus
```

sondern:

```text
LanguageBridge
       │
       └── AIEngine
```

Die AIEngine liefert Ergebnisse.

Die Language Bridge entscheidet, ob diese Ergebnisse noch gültig sind und wie sie mit anderen Ergebnissen zusammengeführt werden.

---

# 20. Einheitlicher Prüfablauf

Bei einer vollständigen Prüfung:

```text
Gründlich prüfen
       │
       ▼
LanguageBridge.check()
       │
       ├── Sprache feststellen
       │
       ├── Dokumenttext übernehmen
       │
       ├── neue documentVersion feststellen
       │
       ├── Benutzerwörter berücksichtigen
       │
       ├── ignorierte Fehler berücksichtigen
       │
       ├── Prüfungs-ID erzeugen
       │
       ├── Rechtschreibung prüfen
       │
       ├── Grammatik prüfen
       │
       ├── KI prüfen
       │
       └── Ergebnisse zusammenführen
                    │
                    ▼
              Fehlerliste
                    │
                    ▼
                  UI
```

---

# 21. Fehlerzusammenführung

Wenn mehrere Prüfer dieselbe Textstelle melden:

```text
Rechtschreibung ─┐
Grammatik ───────┼──► LanguageBridge
KI ──────────────┘
```

werden die Ergebnisse zusammengeführt.

Die Bridge verwendet dabei mindestens:

```text
start
end
text
source
type
```

zur Identifikation zusammengehöriger Ergebnisse.

Beispiel:

```text
Rechtschreibung:
125–134

KI:
125–134
```

kann als derselbe betroffene Bereich behandelt werden.

Unterschiedliche Vorschläge können innerhalb eines gemeinsamen Fehlers zusammengeführt werden.

Dabei darf ein hochwertigerer Vorschlag nicht versehentlich durch einen schlechteren überschrieben werden.

---

# 22. Konfliktauflösung

Wenn Prüfer unterschiedliche Ergebnisse liefern, muss die Bridge sie nachvollziehbar behandeln.

Beispiel:

```text
Rechtschreibung
   └── "widerspiegeln"

KI
   └── "widerspiegeln"
```

→ gleicher Vorschlag, zusammenführen.

Bei unterschiedlichen Vorschlägen:

```text
GrammarEngine
   └── Vorschlag A

AIEngine
   └── Vorschlag B
```

werden beide Vorschläge erhalten.

Die Bridge darf nicht einfach den zuletzt eingegangenen Vorschlag verwenden.

Die Priorität muss anhand von:

```text
Quelle
Konfidenz
Fehlertyp
```

bestimmt werden.

---

# 23. Korrektur

Bei einer Korrektur:

```text
Fehler auswählen
      │
      ▼
Korrektur übernehmen
      │
      ▼
LanguageBridge.applyCorrection()
      │
      ▼
Dokument ändern
      │
      ▼
documentVersion erhöhen
      │
      ▼
Fehler als corrected markieren
      │
      ▼
betroffenen Bereich invalidieren
      │
      ▼
Bereich erneut prüfen
```

Die Korrektur darf nicht nur die sichtbare Markierung entfernen.

Der interne Status muss ebenfalls aktualisiert werden.

---

# 24. Positionen nach Textänderungen

`start` und `end` beziehen sich immer auf eine bestimmte Dokumentversion.

Beispiel:

```js
{
    start: 125,
    end: 134,
    documentVersion: 15
}
```

Wird davor Text eingefügt, dürfen diese Positionen nicht blind weiterverwendet werden.

Es gibt deshalb zwei zulässige Strategien:

```text
A)
Positionen anhand der Textänderung verschieben

oder

B)
betroffene alten Ergebnisse invalidieren
und den Bereich neu prüfen
```

Für Lunivo ist B zunächst sicherer.

Damit wird verhindert, dass Fehler an falschen Textstellen angezeigt werden.

---

# 25. Fehler ignorieren

Wenn der Benutzer

```text
Ignorieren
```

verwendet, wird der Fehlerstatus gespeichert.

Beispiel:

```js
{
    id: 'language-issue-123',
    state: 'ignored'
}
```

Bei einer erneuten Prüfung darf derselbe Fehler nicht unmittelbar wieder erscheinen.

Die Ignore-Information wird anhand einer stabilen Fehler-Signatur gespeichert.

Beispiel:

```text
source + type + text
```

bzw. bei Bedarf zusätzlich:

```text
language
```

oder ein relevanter Kontext.

---

# 26. Akzeptieren

Wenn der Benutzer eine Korrektur bzw. einen Vorschlag akzeptiert:

```text
Vorschlag
    │
    ▼
LanguageBridge.acceptIssue()
    │
    ▼
accepted
```

Die Information kann für zukünftige Prüfungen berücksichtigt werden.

Ein akzeptiertes Benutzerwort wird zusätzlich als Benutzerwort gespeichert, wenn die Aktion semantisch bedeutet:

```text
Dieses Wort ist korrekt und soll zukünftig nicht gemeldet werden.
```

---

# 27. Keine parallelen Wörterbücher

Nicht erstellen:

```text
language-bridge-woerterbuch.js
```

und auch keine zweite Kopie von `WOERTERBUCH`.

Stattdessen:

```text
regeln.js
   │
   ▼
LanguageBridge
   │
   ├── SpellingEngine
   ├── GrammarEngine
   └── AIEngine
```

Die vorhandene gemeinsame Regelquelle bleibt erhalten.

---

# 28. Keine doppelte Prüfung

Nicht zulassen:

```text
Browser Spellcheck
       +
Lunivo Spellcheck
       +
KI Spellcheck
```

wenn alle drei unabhängig rote Fehler erzeugen.

Stattdessen:

```text
                    LanguageBridge
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
       SpellingEngine GrammarEngine  AIEngine
             │            │            │
             └────────────┼────────────┘
                          ▼
                    EIN FEHLERSTATUS
                          │
                          ▼
                           UI
```

Die KI darf natürlich zusätzliche Fehler bzw. Stilvorschläge liefern. Sie darf aber keinen zweiten unabhängigen Fehlerzustand erzeugen.

---

# 29. Zuständigkeiten

## `regeln.js`

Enthält:

```text
Sprachregeln
Wörterbuch
Grammatikregeln
gemeinsame Regeldaten
```

Es enthält keine UI-Zustände.

---

## `language-bridge.js`

Enthält:

```text
Sprachkontext
Dokumentkontext
Benutzerwörter
Ignorierte Wörter
Akzeptierte Korrekturen
Fehlerstatus
Prüfstatus
Dokumentversion
Prüfungs-ID
invalidierte Bereiche
Zusammenführung
Kommunikation zwischen Prüfern
```

Die Bridge ist der zentrale Besitzer des Sprachzustands.

---

## SpellingEngine

Verwendet:

```text
LanguageBridge-Kontext
regeln.js
Benutzerwörter
```

und liefert:

```text
spelling issues
```

---

## GrammarEngine

Verwendet:

```text
LanguageBridge-Kontext
regeln.js
Benutzerwörter
```

und liefert:

```text
grammar issues
```

---

## AIEngine

Verwendet:

```text
LanguageBridge-Kontext
Sprache
Dokumentversion
Prüfungs-ID
Benutzerwörter
bekannte Fehler
```

und liefert:

```text
ai issues
```

---

## `programm.js`

Enthält weiterhin:

```text
UI-Aktionen
Menüaktionen
Schalter
Dokumentaktionen
```

Die UI ruft die Language Bridge auf, anstatt eigene Sprachzustände zu verwalten.

---

# 30. Rote-Wellenlinien-Schalter

Der Schalter

```text
Rote Wellenlinien
```

ändert nicht den Fehlerbestand.

Er ändert nur die Darstellung:

```js
showLanguageIssues = true
```

oder:

```js
showLanguageIssues = false
```

Die Fehler bleiben intern erhalten.

Dadurch kann der Benutzer die Markierungen ausblenden und später wieder einblenden, ohne eine neue Prüfung durchführen zu müssen.

---

# 31. Prüfstatus

Die Bridge sollte einen zentralen Prüfstatus besitzen:

```text
idle
scheduled
checking
ready
stale
error
```

Beispiel:

```js
{
    status: 'checking',
    documentVersion: 15,
    checkId: 42
}
```

Bei einer Dokumentänderung:

```text
ready
  │
  ▼
stale
```

Nach erfolgreicher Prüfung:

```text
checking
   │
   ▼
ready
```

---

# 32. Fehler bei Prüfern

Wenn eine einzelne Engine fehlschlägt, darf dadurch nicht zwangsläufig der komplette Sprachstatus verloren gehen.

Beispiel:

```text
SpellingEngine  → OK
GrammarEngine   → OK
AIEngine        → Fehler
```

Die Bridge kann weiterhin die Ergebnisse von Rechtschreibung und Grammatik anzeigen.

Der KI-Status wird separat als fehlgeschlagen bzw. nicht verfügbar markiert.

---

# 33. Sicherheit bei asynchronen Prüfungen

Keine asynchrone Engine darf ein Ergebnis direkt in die Oberfläche schreiben.

Nicht:

```text
AI → UI
```

sondern:

```text
AI
 │
 ▼
LanguageBridge
 │
 ├── Version prüfen
 ├── checkId prüfen
 ├── Benutzerwörter prüfen
 ├── Ignore-Status prüfen
 └── Ergebnis zusammenführen
       │
       ▼
      UI
```

Damit bleibt die Bridge immer die zentrale Instanz.

---

# 34. Vollständige und inkrementelle Prüfung

Es gibt zwei Prüfarten.

## Inkrementell

Für normale Texteingabe:

```text
Dokumentänderung
       │
       ▼
betroffener Bereich
       │
       ▼
debounced Prüfung
```

## Vollständig

Für:

```text
Gründlich prüfen
```

wird das komplette Dokument geprüft.

Beide Wege verwenden dieselbe Language Bridge und denselben Fehlerstatus.

---

# 35. Zielstruktur

```text
oberflaeche/
│
├── daten/
│   ├── register.js
│   └── regeln.js
│
└── js/
    ├── programm.js
    ├── language-bridge.js
    ├── spelling-engine.js
    ├── grammar-engine.js
    └── ai-engine.js
```

Falls die bestehenden Prüfungen bereits in anderen Dateien liegen, müssen diese **nicht zwingend verschoben** werden.

Die Zielstruktur beschreibt die Verantwortlichkeiten, nicht zwingend eine sofortige physische Aufteilung aller bestehenden Dateien.

---

# 36. Zielarchitektur

```text
                       DOKUMENT
                          │
                          ▼
                  LanguageBridge
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   Regeldaten       Benutzerwörter     Sprache
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                  ZENTRALE PRÜFUNG
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
       Rechtschreibung  Grammatik      KI
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                  ZUSAMMENFÜHRUNG
                          │
                          ▼
                   FEHLERSTATUS
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
          Anzeigen      Korrigieren   Ignorieren
                          │
                          ▼
                     Dokument
                          │
                          ▼
                   neue Version
```

---

# 37. Wichtigste Änderung

Die entscheidende Änderung in Lunivo ist:

```text
VORHER

Browser
  └── eigene Rechtschreibung

Lunivo
  └── eigene Regeln

AutoKorrektur
  └── eigener Zustand

KI
  └── eigener Kontext
```

wird zu:

```text
NACHHER

                 LanguageBridge
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Rechtschreibung  Grammatik        KI
        │              │              │
        └──────────────┼──────────────┘
                       │
                 gemeinsamer
                 Sprachstatus
                       │
                       ▼
                    Dokument
```

Damit kommunizieren die Korrekturstufen miteinander, statt jeweils einen eigenen Fehlerzustand zu führen.

---

# 38. Grundprinzip

Die Architektur folgt künftig diesen Regeln:

```text
1. Eine zentrale Sprachinstanz
2. Eine zentrale Dokumentversion
3. Ein zentraler Fehlerstatus
4. Eine zentrale Benutzerwortverwaltung
5. Eine zentrale Ignore-Verwaltung
6. Eine gemeinsame Regelquelle
7. Keine parallelen Browser-Fehler
8. Keine unabhängigen KI-Fehlerzustände
9. Keine veralteten asynchronen Ergebnisse
10. UI erhält Fehler ausschließlich über die LanguageBridge
```

---

# 39. Ergebnis

Die Language Bridge ersetzt keine bestehenden Sprachregeln.

Sie verbindet die bereits vorhandenen Systeme.

Besonders wichtig:

* `regeln.js` bleibt erhalten.
* Kein zweites Wörterbuch.
* Native Browser-Rechtschreibung ist nicht mehr die führende Fehlerquelle.
* Rechtschreibung und Grammatik verwenden denselben Kontext.
* AutoKorrektur meldet Änderungen an die Bridge.
* KI erhält denselben Sprach- und Dokumentkontext.
* Benutzerwörter werden zentral berücksichtigt.
* Akzeptierte und ignorierte Fehler werden zentral gespeichert.
* Alle Prüfer liefern einen einheitlichen Fehlerstatus.
* Alte Prüfergebnisse können anhand der Dokumentversion verworfen werden.
* Asynchrone KI-Ergebnisse werden zusätzlich anhand einer Prüfungs-ID validiert.
* Rote Wellenlinien werden aus dem zentralen Lunivo-Status erzeugt.
* Das Ausblenden der Wellenlinien löscht keine Fehler.
* Änderungen invalidieren nur den betroffenen Bereich, soweit möglich.
* Vollständige Prüfungen bleiben über `Gründlich prüfen` möglich.
* Prüfer besitzen die Prüfungslogik, die Language Bridge besitzt den gemeinsamen Zustand.
* Fehler verschiedener Prüfer werden zusammengeführt.
* Unterschiedliche Vorschläge werden nicht versehentlich überschrieben.
* Fehlerpositionen gehören immer zu einer Dokumentversion.
* Es gibt keine unabhängigen parallelen Korrekturzustände.

Damit ist die Language Bridge nicht nur eine Verbindung zwischen den vorhandenen Prüfern, sondern die **zentrale Instanz für den gesamten Sprachprüfungs-Lebenszyklus von Lunivo**.

