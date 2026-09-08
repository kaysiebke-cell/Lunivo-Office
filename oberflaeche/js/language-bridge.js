// ============================================================
// LANGUAGE BRIDGE — Zentrale Sprachprüfungs-Engine für Lunivo
// ============================================================
//
// Die Language Bridge koordiniert ALLE Sprachprüfungen zentral:
// - Rechtschreibung (SpellingEngine)
// - Grammatik (GrammarEngine)
// - KI-Korrekturen (AIEngine)
//
// Sie besitzt den EINZIGEN Sprachzustand und verhindert parallele,
// unabhängige Fehler- und Wörterbuch-Verwaltung.
//
// Wichtig: regeln.js wird NICHT dupliziert. Die Bridge hat nur
// Zugriff darauf, nicht eine Kopie.
// ============================================================

'use strict';

class LanguageBridge {
  constructor(rulesData = {}) {
    // ====== CONTEXT (Sprach- und Dokumentkontext) ======
    this.language = 'de-DE';
    this.documentVersion = 0;
    this.documentText = '';
    this.checkId = 0;
    this.nextCheckId = 1;

    // ====== STATE (Zentraler Zustand) ======
    this.userWords = new Set();           // Benutzerwörter (akzeptiert)
    this.ignoredWords = new Set();        // Ignorierte Wörter
    this.acceptedCorrections = new Map(); // {issueId → appliedSuggestion}
    this.issues = [];                     // Alle erkannten Fehler
    this.invalidatedRanges = [];          // Zu erneuernde Bereiche
    this.status = 'idle';                 // idle | scheduled | checking | ready | stale | error
    this.statusDetails = {};              // {documentVersion, checkId, error?}

    // ====== SHARED RULES (Referenz auf zentrale Regeln, KEINE KOPIE) ======
    this.rulesData = rulesData;

    // ====== ENGINES ======
    this.spellingEngine = new SpellingEngine(this);
    this.grammarEngine = new GrammarEngine(this);
    this.aiEngine = new AIEngine(this);

    // ====== DEBOUNCING (für inkrementelle Prüfung) ======
    this.debounceTimer = null;
    this.debounceDelay = 500; // ms

    // ====== PERSISTENCE ======
    this.storagePrefix = 'sp.language-';
    this._loadFromStorage();
  }

  // ====== STORAGE ======
  _loadFromStorage() {
    try {
      const words = localStorage.getItem(this.storagePrefix + 'userWords');
      if (words) this.userWords = new Set(JSON.parse(words));

      const ignored = localStorage.getItem(this.storagePrefix + 'ignoredWords');
      if (ignored) this.ignoredWords = new Set(JSON.parse(ignored));

      const accepted = localStorage.getItem(this.storagePrefix + 'acceptedCorrections');
      if (accepted) this.acceptedCorrections = new Map(JSON.parse(accepted));
    } catch (e) {
      console.warn('Language Bridge storage load failed:', e);
    }
  }

  _saveToStorage() {
    try {
      localStorage.setItem(this.storagePrefix + 'userWords',
        JSON.stringify([...this.userWords]));
      localStorage.setItem(this.storagePrefix + 'ignoredWords',
        JSON.stringify([...this.ignoredWords]));
      localStorage.setItem(this.storagePrefix + 'acceptedCorrections',
        JSON.stringify([...this.acceptedCorrections]));
    } catch (e) {
      console.warn('Language Bridge storage save failed:', e);
    }
  }

  // ====== LANGUAGE ======
  setLanguage(language) {
    if (this.language === language) return;
    this.language = language;
    this.invalidate();
  }

  getLanguage() {
    return this.language;
  }

  // ====== DOCUMENT ======
  setDocument(text) {
    this.documentText = text;
    this.documentVersion++;
    this.invalidate();
  }

  updateDocument(text, startPos = 0, endPos = null) {
    this.documentText = text;
    this.documentVersion++;

    if (endPos === null || endPos <= startPos) {
      endPos = Math.min(this.documentText.length, startPos + 200);
    }

    this.invalidate(startPos, endPos);
  }

  getDocumentText() {
    return this.documentText;
  }

  getDocumentVersion() {
    return this.documentVersion;
  }

  // ====== USER WORDS (Benutzerwörter) ======
  addUserWord(word) {
    if (!word || typeof word !== 'string' || word.trim() === '') return false;
    const normalized = word.toLowerCase().trim();
    if (this.userWords.has(normalized)) return false;
    this.userWords.add(normalized);
    this._saveToStorage();
    this.invalidate();
    return true;
  }

  removeUserWord(word) {
    if (!word) return false;
    const normalized = word.toLowerCase().trim();
    const removed = this.userWords.delete(normalized);
    if (removed) {
      this._saveToStorage();
      this.invalidate();
    }
    return removed;
  }

  isUserWord(word) {
    if (!word) return false;
    return this.userWords.has(word.toLowerCase().trim());
  }

  getUserWords() {
    return [...this.userWords];
  }

  // ====== IGNORED WORDS (Ignorierte Wörter) ======
  ignoreWord(word) {
    if (!word || typeof word !== 'string') return false;
    const normalized = word.toLowerCase().trim();
    if (this.ignoredWords.has(normalized)) return false;
    this.ignoredWords.add(normalized);
    this._saveToStorage();
    this.invalidate();
    return true;
  }

  unignoreWord(word) {
    if (!word) return false;
    const normalized = word.toLowerCase().trim();
    const removed = this.ignoredWords.delete(normalized);
    if (removed) {
      this._saveToStorage();
      this.invalidate();
    }
    return removed;
  }

  isIgnoredWord(word) {
    if (!word) return false;
    return this.ignoredWords.has(word.toLowerCase().trim());
  }

  // ====== ISSUES (Fehler-Management) ======
  addIssue(issue) {
    if (!issue || !issue.id) return false;

    // Eindeutigkeit: ID muss neu sein
    if (this.issues.some(i => i.id === issue.id)) return false;

    // Standardwerte für Issue
    issue.documentVersion = issue.documentVersion ?? this.documentVersion;
    issue.checkId = issue.checkId ?? this.checkId;
    issue.state = issue.state ?? 'active';
    issue.suggestions = issue.suggestions || [];
    issue.confidence = issue.confidence ?? 1.0;

    this.issues.push(issue);
    return true;
  }

  getIssue(issueId) {
    return this.issues.find(i => i.id === issueId) || null;
  }

  getIssues() {
    return [...this.issues];
  }

  getActiveIssues() {
    return this.issues.filter(i => i.state === 'active');
  }

  getIssuesByRange(startPos, endPos) {
    return this.issues.filter(i =>
      i.state === 'active' && i.start < endPos && i.end > startPos
    );
  }

  // ====== ISSUE STATE TRANSITIONS ======
  acceptIssue(issueId) {
    const issue = this.getIssue(issueId);
    if (!issue) return false;

    issue.state = 'accepted';

    // Wenn es ein Wort ist, als Benutzerwort speichern
    if (issue.type === 'word' && issue.text) {
      this.addUserWord(issue.text);
    }

    this._saveToStorage();
    return true;
  }

  ignoreIssue(issueId) {
    const issue = this.getIssue(issueId);
    if (!issue) return false;

    issue.state = 'ignored';

    // Fehler-Signatur speichern
    if (issue.type === 'word' && issue.text) {
      this.ignoreWord(issue.text);
    }

    this._saveToStorage();
    return true;
  }

  applyCorrection(issueId, suggestion) {
    const issue = this.getIssue(issueId);
    if (!issue) return false;
    if (!suggestion || typeof suggestion !== 'string') return false;

    issue.state = 'corrected';
    this.acceptedCorrections.set(issueId, suggestion);
    this._saveToStorage();
    return true;
  }

  // ====== INVALIDATION (Bereich neu prüfen) ======
  invalidate(startPos = 0, endPos = null) {
    if (endPos === null) {
      // Gesamtes Dokument invalidieren
      this.invalidatedRanges = [{start: 0, end: this.documentText.length}];
    } else {
      // Bereich erweitern (Sicherheitsbereich für Satzgrenzen)
      const expandBy = 200;
      const start = Math.max(0, startPos - expandBy);
      const end = Math.min(this.documentText.length, endPos + expandBy);

      // Ranges zusammenführen
      this.invalidatedRanges.push({start, end});
      this._mergeRanges();
    }

    this.status = 'stale';
    this._scheduleCheck();
  }

  _mergeRanges() {
    if (this.invalidatedRanges.length <= 1) return;

    const sorted = this.invalidatedRanges.sort((a, b) => a.start - b.start);
    const merged = [];

    for (const range of sorted) {
      if (merged.length === 0) {
        merged.push(range);
      } else {
        const last = merged[merged.length - 1];
        if (range.start <= last.end) {
          last.end = Math.max(last.end, range.end);
        } else {
          merged.push(range);
        }
      }
    }

    this.invalidatedRanges = merged;
  }

  // ====== DEBOUNCED CHECKING ======
  _scheduleCheck() {
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => this.check(), this.debounceDelay);
  }

  // ====== CHECK (Prüfung starten) ======
  async check() {
    if (this.status === 'checking') return;

    this.status = 'checking';
    this.checkId = this.nextCheckId++;

    this.statusDetails = {
      documentVersion: this.documentVersion,
      checkId: this.checkId,
    };

    try {
      // Alte Fehler entfernen, die nicht mehr aktuell sind
      this._purgeStaleIssues();

      // Bereichsprüfung oder Vollprüfung
      if (this.invalidatedRanges.length > 0) {
        await this._checkRanges();
      } else {
        await this._checkAll();
      }

      this.status = 'ready';
      this.invalidatedRanges = [];
    } catch (error) {
      this.status = 'error';
      this.statusDetails.error = error.message;
      console.error('Language Bridge check failed:', error);
    }
  }

  async _checkRanges() {
    for (const range of this.invalidatedRanges) {
      // Alte Fehler in diesem Bereich entfernen
      this.issues = this.issues.filter(i =>
        i.state !== 'active' || i.end <= range.start || i.start >= range.end
      );

      // Neue Prüfungen
      const text = this.documentText.substring(range.start, range.end);

      const spellingIssues = await this.spellingEngine.check(text, range.start);
      const grammarIssues = await this.grammarEngine.check(text, range.start);

      this.issues.push(...spellingIssues, ...grammarIssues);
    }

    // Asynchrone KI-Prüfung im Hintergrund (nicht auf sie warten)
    this._checkWithAI();
  }

  async _checkAll() {
    // Fehler zurücksetzen
    this.issues = this.issues.filter(i => i.state !== 'active');

    // Alle Prüfer parallel
    const spellingIssues = await this.spellingEngine.check(this.documentText, 0);
    const grammarIssues = await this.grammarEngine.check(this.documentText, 0);

    this.issues.push(...spellingIssues, ...grammarIssues);

    // Asynchrone KI-Prüfung im Hintergrund
    this._checkWithAI();
  }

  async _checkWithAI() {
    // KI läuft async, nicht blockierend
    this.aiEngine.check(this.documentText, 0)
      .then(issues => {
        // Nur übernehmen, wenn noch aktuell
        if (this.documentVersion === this.statusDetails.documentVersion &&
            this.checkId === this.statusDetails.checkId) {
          this.issues.push(...issues);
        }
      })
      .catch(error => {
        console.warn('AI check failed (non-blocking):', error);
      });
  }

  _purgeStaleIssues() {
    const maxAge = 5; // Versionen
    this.issues = this.issues.filter(i => {
      if (i.state === 'active') {
        return i.documentVersion >= this.documentVersion - maxAge;
      }
      return true;
    });
  }

  // ====== STATUS ======
  getStatus() {
    return {
      status: this.status,
      documentVersion: this.documentVersion,
      checkId: this.checkId,
      activeIssueCount: this.getActiveIssues().length,
      userWordCount: this.userWords.size,
      error: this.statusDetails.error || null,
    };
  }

  // ====== CONTEXT (für Engines) ======
  getContext() {
    return {
      language: this.language,
      documentVersion: this.documentVersion,
      documentText: this.documentText,
      checkId: this.checkId,
      userWords: this.userWords,
      ignoredWords: this.ignoredWords,
      rulesData: this.rulesData,
    };
  }
}

// ============================================================
// SPELLING ENGINE
// ============================================================

class SpellingEngine {
  constructor(bridge) {
    this.bridge = bridge;
  }

  async check(text, offset = 0) {
    const issues = [];
    const context = this.bridge.getContext();

    // Wörter splitten (einfache Tokenisierung)
    const words = text.match(/\b\w+\b/g) || [];
    let pos = 0;

    for (const word of words) {
      const wordPos = text.indexOf(word, pos);
      if (wordPos === -1) continue;

      const documentPos = offset + wordPos;

      // Prüfen gegen Wörterbuch und Benutzerwörter
      const issue = this._checkWord(word, documentPos, context);
      if (issue) issues.push(issue);

      pos = wordPos + word.length;
    }

    // Gegen Wörterbuch-Duplikate prüfen (wieder/wider, etc.)
    const dictIssues = this._checkDictionary(text, offset, context);
    issues.push(...dictIssues);

    return issues;
  }

  _checkWord(word, pos, context) {
    const lower = word.toLowerCase();

    // Ignoriert?
    if (context.ignoredWords.has(lower)) return null;

    // Benutzerwort?
    if (context.userWords.has(lower)) return null;

    // Großbuchstaben-Ignoranz (Akronyme, Eigennamen)
    if (word.match(/^[A-ZÄÖÜ]/)) return null;

    // Hier würde in einer echten Implementierung eine echte
    // Rechtschreibprüfung stattfinden (gegen ein Wörterbuch).
    // Für MVP: ignorieren.

    return null;
  }

  _checkDictionary(text, offset, context) {
    const issues = [];
    const dict = context.rulesData.WOERTERBUCH || {};

    for (const [wrong, correct] of Object.entries(dict)) {
      const regex = new RegExp('\\b' + wrong + '\\b', 'gi');
      let match;

      while ((match = regex.exec(text)) !== null) {
        const start = offset + match.index;
        const end = start + match[0].length;

        // Nicht ignoriert, nicht akzeptiert?
        if (context.ignoredWords.has(wrong.toLowerCase())) continue;

        issues.push({
          id: `spelling-${start}-${end}`,
          source: 'spelling',
          type: 'word',
          start,
          end,
          text: match[0],
          suggestions: [correct],
          confidence: 1.0,
          documentVersion: context.documentVersion,
          checkId: context.checkId,
          state: 'active',
        });
      }
    }

    return issues;
  }
}

// ============================================================
// GRAMMAR ENGINE
// ============================================================

class GrammarEngine {
  constructor(bridge) {
    this.bridge = bridge;
  }

  async check(text, offset = 0) {
    const issues = [];
    const context = this.bridge.getContext();

    // Beispiel: dass/das Unterscheidung
    const dassDasIssues = this._checkDassDas(text, offset, context);
    issues.push(...dassDasIssues);

    // Weitere Grammatik-Prüfungen können hier hinzu

    return issues;
  }

  _checkDassDas(text, offset, context) {
    const issues = [];
    const rules = context.rulesData;

    if (!rules.DENK_ZEITWOERTER) return issues;

    // Regex: "VERB [Words]* dass"
    const verbs = rules.DENK_ZEITWOERTER.join('|');
    const regex = new RegExp(
      `\\b(${verbs})\\b[^.!?]*?\\b(das)\\b`,
      'gi'
    );

    let match;
    while ((match = regex.exec(text)) !== null) {
      const dasPos = match.index + match[0].lastIndexOf('das');
      const start = offset + dasPos;
      const end = start + 3;

      // Könnte "dass" sein?
      issues.push({
        id: `grammar-das-dass-${start}`,
        source: 'grammar',
        type: 'dass-das',
        start,
        end,
        text: 'das',
        suggestions: ['dass'],
        confidence: 0.7,
        documentVersion: context.documentVersion,
        checkId: context.checkId,
        state: 'active',
      });
    }

    return issues;
  }
}

// ============================================================
// AI ENGINE (Stub für später)
// ============================================================

class AIEngine {
  constructor(bridge) {
    this.bridge = bridge;
  }

  async check(text, offset = 0) {
    // Stub: Wird später mit echter KI-Implementierung gefüllt
    return [];
  }
}

// ============================================================
// EXPORT
// ============================================================

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { LanguageBridge, SpellingEngine, GrammarEngine, AIEngine };
}
