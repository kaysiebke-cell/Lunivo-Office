/* ============================================================
   Die zwei Handgriffe, die jeder Prüflauf braucht.

   Sie standen in jeder Prüfdatei noch einmal. Das ist in JavaScript
   nicht bloß doppelt, sondern gefährlich: Werden zwei solche Dateien je
   zusammen geladen, überschreibt die spätere die frühere still.
   ============================================================ */
'use strict';

function pruefhelferBauen() {
  const stand = { bestanden: 0, gefehlt: 0 };

  const stimmt = (bedingung, was) => {
    if (!bedingung) {
      console.error('  FEHLT: ' + was);
      stand.gefehlt++;
      process.exitCode = 1;
      return;
    }
    stand.bestanden++;
    console.log('  ok   ' + was);
  };

  const gleich = (ist, soll, was) =>
    stimmt(ist === soll, was + (ist === soll ? ''
      : '  (ist ' + JSON.stringify(ist) + ', soll ' + JSON.stringify(soll) + ')'));

  const schluss = () => {
    console.log('\n' + stand.bestanden + ' Prüfungen bestanden'
      + (stand.gefehlt ? ' — ' + stand.gefehlt + ' nicht.' : '.') + '\n');
  };

  return { stimmt, gleich, schluss, stand };
}

module.exports = { pruefhelferBauen };
