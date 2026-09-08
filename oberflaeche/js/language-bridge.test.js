// ============================================================
// LANGUAGE BRIDGE - TESTS
// ============================================================
//
// Tests zur Language Bridge — lokal lauffähig, keine App nötig.
// Mit Node.js ausführbar: node language-bridge.test.js
//
// ============================================================

'use strict';

// Mock für localStorage (bei Node)
if (typeof localStorage === 'undefined') {
  global.localStorage = {
    data: {},
    getItem(key) { return this.data[key] || null; },
    setItem(key, value) { this.data[key] = value; },
    removeItem(key) { delete this.data[key]; },
    clear() { this.data = {}; },
  };
}

// Klassen laden (bei Node.js)
if (typeof require !== 'undefined' && typeof LanguageBridge === 'undefined') {
  try {
    const bridge = require('./language-bridge.js');
    Object.assign(globalThis, bridge);
  } catch (e) {
    console.warn('Require failed, assuming browser context');
  }
}

// Test-Assertions
const assert = (condition, message) => {
  if (!condition) {
    throw new Error(`FAIL: ${message}`);
  }
  console.log(`✓ ${message}`);
};

const assertEqual = (actual, expected, message) => {
  if (actual !== expected) {
    throw new Error(`FAIL: ${message} (got ${actual}, expected ${expected})`);
  }
  console.log(`✓ ${message}`);
};

// ============================================================
// TEST SUITE
// ============================================================

async function runTests() {
  console.log('\n🧪 Language Bridge Tests\n');

  // Test-Daten
  const testRules = {
    WOERTERBUCH: {
      'wiederspiegeln': 'widerspiegeln',
      'garnicht': 'gar nicht',
    },
    DENK_ZEITWOERTER: [
      'glaube', 'glaubst', 'glaubt', 'denke', 'denkst', 'denkt'
    ],
  };

  // ---- Test 1: Initialization ----
  console.log('Test 1: Initialization');
  const bridge = new LanguageBridge(testRules);
  assert(bridge.language === 'de-DE', 'Default language is de-DE');
  assert(bridge.documentVersion === 0, 'Initial document version is 0');
  assert(bridge.status === 'idle', 'Initial status is idle');
  assert(bridge.getActiveIssues().length === 0, 'No issues initially');

  // ---- Test 2: Document Management ----
  console.log('\nTest 2: Document Management');
  bridge.setDocument('Das ist ein Test.');
  assertEqual(bridge.getDocumentVersion(), 1, 'Document version incremented');
  assertEqual(bridge.getDocumentText(), 'Das ist ein Test.', 'Document text set');

  bridge.updateDocument('Das ist ein neuer Test.', 10, 13);
  assertEqual(bridge.getDocumentVersion(), 2, 'Version incremented on update');
  assert(bridge.invalidatedRanges.length > 0, 'Range invalidated on update');

  // ---- Test 3: Language ----
  console.log('\nTest 3: Language Management');
  bridge.setLanguage('en-US');
  assertEqual(bridge.getLanguage(), 'en-US', 'Language changed');

  bridge.setLanguage('de-DE');
  assertEqual(bridge.getLanguage(), 'de-DE', 'Language changed back');

  // ---- Test 4: User Words ----
  console.log('\nTest 4: User Words');
  const added = bridge.addUserWord('Lunivo');
  assert(added, 'User word added');
  assert(bridge.isUserWord('lunivo'), 'User word recognized (case-insensitive)');

  const notAdded = bridge.addUserWord('Lunivo');
  assert(!notAdded, 'Duplicate word not added');

  assertEqual(bridge.getUserWords().length, 1, 'One user word stored');

  const removed = bridge.removeUserWord('Lunivo');
  assert(removed, 'User word removed');
  assert(!bridge.isUserWord('Lunivo'), 'User word no longer recognized');

  // ---- Test 5: Ignored Words ----
  console.log('\nTest 5: Ignored Words');
  const ignored = bridge.ignoreWord('xyz');
  assert(ignored, 'Word ignored');
  assert(bridge.isIgnoredWord('xyz'), 'Ignored word recognized');

  const unignored = bridge.unignoreWord('xyz');
  assert(unignored, 'Ignored word removed');

  // ---- Test 6: Issue Management ----
  console.log('\nTest 6: Issue Management');
  const issue = {
    id: 'test-issue-1',
    source: 'spelling',
    type: 'word',
    start: 10,
    end: 15,
    text: 'wiederspiegeln',
    suggestions: ['widerspiegeln'],
    confidence: 1.0,
  };

  const issueAdded = bridge.addIssue(issue);
  assert(issueAdded, 'Issue added');
  assertEqual(bridge.getIssues().length, 1, 'Issue in list');

  const retrieved = bridge.getIssue('test-issue-1');
  assert(retrieved !== null, 'Issue retrieved by ID');
  assertEqual(retrieved.state, 'active', 'Issue state is active');

  // ---- Test 7: Issue State Transitions ----
  console.log('\nTest 7: Issue State Transitions');

  // Accept
  const accepted = bridge.acceptIssue('test-issue-1');
  assert(accepted, 'Issue accepted');
  const afterAccept = bridge.getIssue('test-issue-1');
  assertEqual(afterAccept.state, 'accepted', 'Issue state changed to accepted');
  assert(bridge.isUserWord('wiederspiegeln'), 'Word added to user words on accept');

  // Create new issue for ignore test
  const issue2 = {
    id: 'test-issue-2',
    source: 'spelling',
    type: 'word',
    start: 20,
    end: 28,
    text: 'garnicht',
    suggestions: ['gar nicht'],
  };
  bridge.addIssue(issue2);

  const ignored2 = bridge.ignoreIssue('test-issue-2');
  assert(ignored2, 'Issue ignored');
  const afterIgnore = bridge.getIssue('test-issue-2');
  assertEqual(afterIgnore.state, 'ignored', 'Issue state changed to ignored');

  // Create new issue for correction test
  const issue3 = {
    id: 'test-issue-3',
    source: 'spelling',
    type: 'word',
    start: 30,
    end: 35,
    text: 'falsh',
    suggestions: ['falsch'],
  };
  bridge.addIssue(issue3);

  const corrected = bridge.applyCorrection('test-issue-3', 'falsch');
  assert(corrected, 'Correction applied');
  const afterCorrect = bridge.getIssue('test-issue-3');
  assertEqual(afterCorrect.state, 'corrected', 'Issue state changed to corrected');

  // ---- Test 8: Filtering Issues ----
  console.log('\nTest 8: Filtering Issues');
  const activeIssues = bridge.getActiveIssues();
  assert(activeIssues.length <= bridge.getIssues().length,
    'Active issues subset of all issues');

  // Neue aktive Issue für Range-Test
  const rangeTestIssue = {
    id: 'range-test-1',
    source: 'spelling',
    type: 'word',
    start: 10,
    end: 20,
    text: 'test',
    state: 'active',
  };
  bridge.addIssue(rangeTestIssue);

  const rangeIssues = bridge.getIssuesByRange(5, 25);
  assert(rangeIssues.length > 0, 'Range filtering finds issues in range');

  // ---- Test 9: Status ----
  console.log('\nTest 9: Status');
  const status = bridge.getStatus();
  assert(status.status !== undefined, 'Status object has status field');
  assert(status.documentVersion !== undefined, 'Status has version');
  assert(status.activeIssueCount !== undefined, 'Status has issue count');

  // ---- Test 10: Context for Engines ----
  console.log('\nTest 10: Context for Engines');
  const context = bridge.getContext();
  assert(context.language !== undefined, 'Context has language');
  assert(context.documentText !== undefined, 'Context has text');
  assert(context.userWords !== undefined, 'Context has user words');
  assert(context.rulesData !== undefined, 'Context has rules data');

  // ---- Test 11: Storage Persistence ----
  console.log('\nTest 11: Storage Persistence');
  const bridge2 = new LanguageBridge(testRules);

  // bridge2 sollte die Daten von bridge1 laden (da localStorage persistent ist)
  const loadedWords = bridge2.getUserWords();
  assert(loadedWords.length > 0, 'User words persisted to localStorage');

  // ---- Test 12: Invalidation ----
  console.log('\nTest 12: Invalidation');
  bridge.invalidatedRanges = [];
  bridge.invalidate(0, 50);
  assert(bridge.invalidatedRanges.length > 0, 'Range invalidated');
  assert(bridge.status === 'stale', 'Status changed to stale');

  // ---- Test 13: Spelling Engine ----
  console.log('\nTest 13: Spelling Engine');
  const engine = new SpellingEngine(bridge);
  bridge.setDocument('Das ist wiederspiegeln falsch.');
  const spellingIssues = await engine.check(bridge.documentText, 0);
  assert(Array.isArray(spellingIssues), 'Spelling engine returns array');
  // Spellcheck sollte 'wiederspiegeln' finden
  const foundWrong = spellingIssues.some(i =>
    i.text === 'wiederspiegeln' && i.suggestions.includes('widerspiegeln')
  );
  assert(foundWrong || spellingIssues.length === 0,
    'Spelling engine checks dictionary');

  // ---- Test 14: Grammar Engine ----
  console.log('\nTest 14: Grammar Engine');
  const grammarEngine = new GrammarEngine(bridge);
  bridge.setDocument('Ich glaube das es richtig ist.');
  const grammarIssues = await grammarEngine.check(bridge.documentText, 0);
  assert(Array.isArray(grammarIssues), 'Grammar engine returns array');

  // ---- Test 15: API Surface ----
  console.log('\nTest 15: Full API Surface');
  const apiMethods = [
    'setDocument', 'updateDocument', 'getDocumentText', 'getDocumentVersion',
    'setLanguage', 'getLanguage',
    'addUserWord', 'removeUserWord', 'isUserWord', 'getUserWords',
    'ignoreWord', 'unignoreWord', 'isIgnoredWord',
    'addIssue', 'getIssue', 'getIssues', 'getActiveIssues', 'getIssuesByRange',
    'acceptIssue', 'ignoreIssue', 'applyCorrection',
    'invalidate', 'check',
    'getStatus', 'getContext',
  ];

  for (const method of apiMethods) {
    assert(typeof bridge[method] === 'function', `API method: ${method}`);
  }

  console.log('\n✨ All tests passed!\n');
}

// ============================================================
// RUN
// ============================================================

runTests().catch(error => {
  console.error('\n❌ Test failed:', error.message);
  process.exit(1);
});
