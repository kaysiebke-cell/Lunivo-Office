# Language Bridge Integration Plan

## Ziel
Die **Language Bridge** in das laufende `programm.js` integrieren, ohne es zu brechen.

## Status: READY
- ✅ language-bridge.js: Vollständig implementiert
- ✅ language-bridge.test.js: 15 Tests (lokal lauffähig)
- ⏳ programm.js: Schrittweise Migration

---

## PHASE 1: Vorbereitung (Keine Breaking Changes)

### 1a. Language Bridge laden
In `oberflaeche/index.html`, VOR `programm.js`:
```html
<script src="js/language-bridge.js"></script>
<script src="js/programm.js"></script>
```

### 1b. Globale Instanz erstellen
Ganz oben in `programm.js` (nach den bestehenden Variablen):

```javascript
// ---- Language Bridge (neu) ----
let LanguageBridgeInstance = null;

function initLanguageBridge() {
  LanguageBridgeInstance = new LanguageBridge(REGELDATEN);
  console.log('✓ Language Bridge initialized');
}
```

Aufrufen in der `main()` oder `window.addEventListener('load')`:
```javascript
window.addEventListener('load', () => {
  initLanguageBridge();
  // ... rest des startup
});
```

### 1c. Tests lokal prüfen
```bash
cd oberflaeche/js
node language-bridge.test.js
```

**Ergebnis:** Language Bridge lädt, tut aber noch nichts. Das Programm funktioniert noch genauso.

---

## PHASE 2: Schrittweise Migration (Pro Feature)

### 2a. Dokumentänderungen melden
Immer wenn das Dokument ändert, melde es der Bridge:

**VORHER (in programm.js, z.B. in `Dokument.setzeInhalt`):**
```javascript
feld.innerHTML = inhalt;
merkeText(); // Bestehend
```

**NACHHER:**
```javascript
feld.innerHTML = inhalt;
if (LanguageBridgeInstance) {
  LanguageBridgeInstance.setDocument(feld.innerText);
}
merkeText();
```

**Größe:** ~20 Zeilen Änderung an 5-10 Stellen in programm.js
**Risiko:** Niedrig (Bridge tut noch nichts)

### 2b. Fehler-Anzeige auf Bridge-Ergebnisse umschalten
Die roten Wellenlinien zeigen jetzt Bridge-Fehler statt Browser-Fehler.

**Bestehender Code (vermutlich in B.rechtschreibung):**
```javascript
B.rechtschreibung = () => {
  feld.spellcheck = !feld.spellcheck;
  // ...
};
```

**NACHHER:**
```javascript
B.rechtschreibung = () => {
  if (LanguageBridgeInstance) {
    showLanguageIssues = !showLanguageIssues;
    LanguageBridgeInstance.debounceDelay = showLanguageIssues ? 500 : 0;
    feld.spellcheck = false; // Bridge ist jetzt die Quelle
  } else {
    feld.spellcheck = !feld.spellcheck; // Fallback
  }
};
```

Dann im Editor: Fehler nicht aus Browser-Spellcheck, sondern aus `LanguageBridgeInstance.getActiveIssues()` anzeigen.

**Größe:** ~50 Zeilen
**Risiko:** Mittel (aber das Programm läuft weiter)

### 2c. Benutzerwörter synchronisieren
Wenn der Benutzer ein Wort akzeptiert, speichere es:

```javascript
function acceptIssueFromUI(issueId) {
  if (LanguageBridgeInstance) {
    LanguageBridgeInstance.acceptIssue(issueId);
  }
}

function ignoreIssueFromUI(issueId) {
  if (LanguageBridgeInstance) {
    LanguageBridgeInstance.ignoreIssue(issueId);
  }
}
```

**Größe:** ~15 Zeilen
**Risiko:** Niedrig

---

## PHASE 3: Engines Ausarbeiten

### 3a. SpellingEngine vollständig
Basierend auf regeln.js WOERTERBUCH gegen echtes Wörterbuch (woerter.txt).

### 3b. GrammarEngine vollständig
Alle Grammatik-Regeln aus programm.js in grammarEngine.js.

### 3c. AIEngine starten
KI-Integration (später).

---

## PHASE 4: Alte Systeme abbauen

### 4a. Browser-Spellcheck deaktivieren
```javascript
feld.spellcheck = false;
```

### 4b. Duplicate Code entfernen
Alte Rechtschreibungs-Funktionen in programm.js können gelöscht werden.

---

## File Changes Summary

### Neu erstellt:
- `oberflaeche/js/language-bridge.js` ✅
- `oberflaeche/js/language-bridge.test.js` ✅

### Zu ändern:
- `oberflaeche/index.html` — Script-Tag hinzufügen
- `oberflaeche/js/programm.js` — Dokumentänderungen melden
- `oberflaeche/js/programm.js` — Fehler-Anzeige umschalten (später)

### Zu erweitern:
- `oberflaeche/js/language-bridge.js` — Engines ausarbeiten

### Zu prüfen:
- `oberflaeche/daten/regeln.js` — NICHT kopiert, nur referenziert ✅
- `oberflaeche/daten/woerter.txt` — Wörterbuch-Zugriff vorbereiten

---

## Storage Strategy

Die Bridge speichert in **localStorage** unter `sp.language-*`:
- `sp.language-userWords` — Benutzerwörter (JSON Array)
- `sp.language-ignoredWords` — Ignorierte Wörter (JSON Array)
- `sp.language-acceptedCorrections` — Akzeptierte Korrektionen (JSON Map)

Das ist konsistent mit der bestehenden `sp.*`-Konvention und überschreibt nichts.

---

## Rollback Strategy

Falls etwas schiefgeht:
1. Language Bridge deaktivieren (Script-Tag auskommentieren)
2. Dokumentänderungen-Meldungen rückgängig machen
3. Browser-Spellcheck wieder aktivieren
4. localStorage clearen: `localStorage.clear()`

Das Programm funktioniert danach wieder wie vorher.

---

## Testplan

### Schritt 1: Unit Tests (local)
```bash
node oberflaeche/js/language-bridge.test.js
```

### Schritt 2: Integration Tests (in programm)
1. Programm starten
2. Text eingeben → Bridge muss Dokument erkennen
3. „Gründlich prüfen" klicken → Bridge läuft
4. Fehler anclicken → Benutzerwort/Ignorieren funktioniert
5. Speichern/Laden → Benutzerwörter bleiben

### Schritt 3: Regression Tests
- Alte Features funktionieren noch?
- Keine Crashes?
- localStorage nicht korrumpiert?

---

## Timeline

| Phase | Task | Effort | Days |
|-------|------|--------|------|
| 1 | Prepare (load script, init) | 30min | Today |
| 2a | Document sync | 1h | Day 1 |
| 2b | Error display | 2h | Day 2-3 |
| 2c | User words sync | 30min | Day 3 |
| 3a | SpellingEngine full | 3h | Day 4-5 |
| 3b | GrammarEngine full | 3h | Day 6-7 |
| 3c | AIEngine | varies | Day 8+ |
| 4 | Cleanup old code | 1h | After engines |

**Total: ~1.5 weeks for full integration**

---

## Success Criteria

- [ ] Tests pass (node language-bridge.test.js)
- [ ] Program starts without errors
- [ ] Document changes trigger Bridge checks
- [ ] Errors show correctly
- [ ] User words persist across sessions
- [ ] No regression in existing features
- [ ] Debouncing works (UI responsive)
- [ ] Old Browser-Spellcheck can be disabled

---

## Notes

- **Wichtig:** regeln.js wird NICHT kopiert/dupliziert
- **Wichtig:** programm.js bleibt funktionierend während Umstellungen
- **Optional:** Später können alte Fehlerbehandlungen gelöscht werden
- **Optional:** Später Menu-Struktur (WPS-Writer) hinzufügen
