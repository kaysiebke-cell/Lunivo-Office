/* ============================================================
   Die Einstellungen als Datei.

   Der Speicher des Fensters bleibt, was er war: Dort wird gelesen und
   geschrieben, während gearbeitet wird — schnell und ohne Umweg. Nur war
   er auch alles, was es gab. Wer seine Einstellungen sichern, auf einen
   zweiten Rechner mitnehmen oder bloß nachsehen wollte, was eingestellt
   ist, kam nicht heran; und ein geleerter Speicher nahm sie mit.

   Deshalb gibt es ein Abbild in ~/.config/lunivo-office/einstellungen.conf
   — eine Zeile je Einstellung, von Hand zu lesen und zu ändern, an
   derselben Stelle, an der auch WPS seine ablegt.

   WARUM DIESE DATEI VOR ALLEN ANDEREN STEHT

   programm.js liest seine Werte beim Laden: „let lineal = Speicher.lies(…)"
   steht ganz oben und läuft, sobald die Datei da ist. Was danach aus einer
   Datei nachkäme, käme zu spät — das Lineal stünde schon.

   Deshalb wird hier synchron geholt, in einem Zug, bevor irgendein anderer
   Baustein etwas liest. Es ist der eigene Server auf 127.0.0.1: Die Antwort
   ist in Millisekunden da, und es geschieht genau einmal beim Start.

   WAS HINEINGEHÖRT

   Nur Einstellungen. Im selben Speicher liegen auch die Dokumente, die
   offenen Fenster und die Fehlerstände — die haben in einer
   Einstellungsdatei nichts zu suchen und machten sie unlesbar.
   ============================================================ */
'use strict';

const Einstellungsdatei = (() => {

/* Was keine Einstellung ist, sondern Inhalt oder Sitzung.

   Hier stand erst nur „sp.dok." — und das griff nicht: Bei mehreren
   Fenstern steht deren Nummer davor, „sp.f2.dok.1.inhalt". Der ganze
   Brieftext landete damit in der Einstellungsdatei. Alles mit einer
   Fensternummer gehört einem Fenster, nicht dem Programm; und Inhalt,
   Kopf- und Fußzeile sind das Dokument, auch ohne „dok." im Namen. */
const NICHT = [
  /^sp\.f\d+\./,                              /* alles eines Fensters   */
  /^sp\.dok\./, /^sp\.dokumente$/,             /* Dokumente             */
  /^sp\.fenster\./,                            /* offene Fenster        */
  /^sp\.(inhalt|kopfinhalt|fussinhalt|dateiname)$/,   /* der Text selbst */
];

const gehoertHinein = (schluessel) =>
  typeof schluessel === 'string'
  && schluessel.startsWith('sp.')
  && !NICHT.some((muster) => muster.test(schluessel));

function alles() {
  const werte = {};
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const schluessel = localStorage.key(i);
      if (gehoertHinein(schluessel)) werte[schluessel] = localStorage.getItem(schluessel);
    }
  } catch (e) { /* kein Speicher */ }
  return werte;
}

/* Beim Start: Was in der Datei steht, gilt.

   Sie ist das, woran jemand von Hand etwas ändern kann — und wer das tut,
   will es auch sehen. Steht dort nichts, bleibt der Speicher wie er ist,
   und beim ersten Schreiben entsteht die Datei aus ihm. So verliert
   niemand seine bisherigen Einstellungen.

   Ohne Server — etwa unter file:// — geschieht hier gar nichts, und das
   Programm arbeitet wie vorher allein mit dem Speicher. */
function holen() {
  let werte = null;
  try {
    const ruf = new XMLHttpRequest();
    ruf.open('GET', '/einstellungen', false);      /* synchron, siehe oben */
    ruf.send(null);
    if (ruf.status !== 200) return;
    werte = JSON.parse(ruf.responseText);
  } catch (e) { return; }
  if (!werte || typeof werte !== 'object') return;
  try {
    for (const name of Object.keys(werte)) {
      if (gehoertHinein(name) && typeof werte[name] === 'string') {
        localStorage.setItem(name, werte[name]);
      }
    }
  } catch (e) { /* voll */ }
}

/* Nicht bei jedem Schreiben, sondern einmal, wenn es zur Ruhe kommt. Beim
   Ziehen eines Einzugs schreibt der Speicher dutzendfach; ebenso oft die
   Datei anzufassen wäre zu spüren und brächte nichts. */
let uhr = null;
function merken() {
  if (uhr) clearTimeout(uhr);
  uhr = setTimeout(() => {
    uhr = null;
    try {
      fetch('/einstellungen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(alles()),
      }).catch(() => {});
    } catch (e) { /* ohne Server: der Speicher genügt */ }
  }, 800);
}

holen();

return { merken, holen, alles };
})();
