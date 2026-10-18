// Liest oberflaeche/daten/register.js (und MENUES aus programm.js) und schreibt die Struktur als JSON:
// native_qt/resources/register.json — Reiter, Gruppen, Knöpfe, Symbole, Beschriftungen, Aktionsnamen.
// Entwicklungswerkzeug, braucht Node. Zur Laufzeit des Programms wird es nicht gebraucht.
const fs = require('fs'), path = require('path');
const wurzel = path.resolve(__dirname, '..');
const quelle = fs.readFileSync(path.join(wurzel, 'oberflaeche/daten/register.js'), 'utf8');

let rec;
const B = new Proxy({}, { get: (_, n) => { const f = (...a) => { rec.push(String(n)); }; f.nm = String(n); return f; } });
const w = new Proxy({}, { get: (_, n) => (...a) => { rec.push('w.' + String(n)); return false; } });

function aktion(a) {
  if (a === undefined || a === null || a === false) return null;
  if (typeof a === 'function') { rec = []; try { a({ getBoundingClientRect: () => ({}) }); } catch (e) {} return { tun: rec[0] || null }; }
  if (Array.isArray(a)) return { menue: a.map(eintrag) };
  if (typeof a === 'object') {
    const o = {};
    for (const k of Object.keys(a)) { rec = []; try { a[k]({}); } catch (e) {} o[k] = rec[0] || null; }
    return o;
  }
  return null;
}
function eintrag(e) {
  if (!Array.isArray(e)) return { text: String(e) };
  if (e[0] === '-' || e[0] === '//') return { trenner: true };
  const [name, a] = e;
  if (Array.isArray(a)) return { name, menue: a.map(eintrag) };
  return { name, ...aktion(a) };
}
function knopf(e) {
  if (typeof e === 'string') return { hinweis: e };
  if (e[0] === '//') return { zeilenumbruch: true };
  const [symbol, name, a, gross, haken] = e;
  const r = { symbol, name, gross: gross === 'gross' };
  const ak = aktion(a);
  if (ak) Object.assign(r, ak);
  if (typeof haken === 'function') r.haken = true;
  return r;
}

const reiter = new Function('B', 'w', quelle + '\nreturn REGISTER_BAUEN(B, w);')(B, w);
const aus = { register: reiter.map(([name, gruppen]) => ({
  name,
  gruppen: gruppen.map(([gname, inhalt, pfeil]) => {
    const g = { name: gname };
    if (typeof inhalt === 'string') { g.katalog = inhalt; }
    else {
      g.knoepfe = inhalt.filter((x) => x !== 'felder').map(knopf);
      if (inhalt[0] === 'felder') g.felder = true;
    }
    if (typeof pfeil === 'function') { rec = []; try { pfeil(); } catch (e) {} g.pfeil = rec[0] || null; }
    return g;
  }),
})) };

// Menüs aus programm.js
const prog = fs.readFileSync(path.join(wurzel, 'oberflaeche/js/programm.js'), 'utf8');
const i = prog.indexOf('const MENUES = [');
let tiefe = 0, j = prog.indexOf('[', i);
for (let k = j; k < prog.length; k++) {
  if (prog[k] === '[') tiefe++; else if (prog[k] === ']') { tiefe--; if (!tiefe) { j = k; break; } }
}
const text = prog.slice(prog.indexOf('[', i), j + 1);
const BM = new Proxy({}, { get: (_, n) => { const f = () => {}; f.nm = String(n); return f; } });
const wm = new Proxy({}, { get: (_, n) => () => false });
const stub = (n) => { const f = new Proxy(function () {}, { get: (_, k) => (k === 'nm' ? n : stub(n + '.' + String(k))), apply: () => stub(n + '()') }); return f; };
const scope = new Proxy({}, { has: (_, k) => typeof k === 'string' && k !== 'text', get: (_, k) => (k === Symbol.unscopables ? undefined : k === 'B' ? BM : k === 'strich' ? '-' : stub(String(k))) });
const menues = new Function('scope', 'with (scope) { return ' + text + '; }')(scope);
function menue(m) {
  if (m === '-') return { trenner: true };
  const o = { name: m.name };
  if (m.tun) o.tun = (typeof m.tun === 'function' && m.tun.nm) || 'eigen';
  if (m.taste) o.taste = m.taste;
  if (Array.isArray(m.unter)) o.unter = m.unter.map(menue); else if (m.unter) o.unter_dynamisch = true;
  return o;
}
aus.menues = menues.map(([name, punkte]) => ({ name, punkte: punkte.map(menue) }));
fs.mkdirSync(path.join(wurzel, 'native_qt/resources'), { recursive: true });
fs.writeFileSync(path.join(wurzel, 'native_qt/resources/register.json'), JSON.stringify(aus, null, 1));
console.log('Reiter:', aus.register.map((r) => r.name + ':' + r.gruppen.length).join(' '), '| Menüs:', aus.menues.map((m) => m.name).join(', '));
