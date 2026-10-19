/* Die Bildsteuerung durchspielen — jeder Griff, jeder Modus.

   WOZU. Kay musste bisher jeden Fehler selbst finden: Marken, die
   stehenblieben; Griffe, die neben dem Bild lagen; ein Ziehen, das der
   Browser abschnitt. Jeder einzelne waere hier aufgefallen.

   WIE ANWENDEN. Den Inhalt dieser Datei in die Entwicklerkonsole des
   laufenden Fensters einfuegen, oder ueber den Vorschau-Server mit dem
   Browserwerkzeug ausfuehren. Ausgegeben wird eine Liste aus OK und
   FEHLER.

   Sie prueft NICHT, ob etwas huebsch aussieht — nur, ob es tut, was
   draufsteht. */
(async () => {
  const warte = (ms) => new Promise((r) => setTimeout(r, ms));
  const feld = document.getElementById('dokument');
  const ergebnis = [];
  const pruefe = (name, bedingung, was) => {
    ergebnis.push((bedingung ? 'OK    ' : 'FEHLER') + '  ' + name
                  + (bedingung ? '' : '   → ' + was));
  };

  const BILD = 'data:image/svg+xml;base64,' + btoa(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="250">'
    + '<rect width="400" height="250" fill="#0B0B0F"/></svg>');

  const zeiger = (typ, ziel, x, y, id) => ziel.dispatchEvent(new PointerEvent(typ, {
    bubbles: true, cancelable: true, pointerId: id || 1,
    pointerType: 'mouse', clientX: x, clientY: y, isPrimary: true }));

  const aufbauen = async () => {
    feld.innerHTML = '<p>oben</p><p><img src="' + BILD + '"></p><p>unten</p>';
    await warte(250);
    const bild = feld.querySelector('img');
    /* Auswahl auf das Bild setzen, damit auch der Reiter Bildtools
       erscheint — ueber ihn laufen die Befehle ohne Griff. */
    const bereich = document.createRange();
    bereich.selectNode(bild);
    const aus = window.getSelection();
    aus.removeAllRanges();
    aus.addRange(bereich);
    aus.collapseToStart();
    zeiger('pointerover', bild, 0, 0);
    await warte(550);
    return bild;
  };

  const griff = (art) => document.querySelector('.bildgriff--' + art);
  const mitte = (el) => { const r = el.getBoundingClientRect();
                          return [r.x + r.width / 2, r.y + r.height / 2]; };

  /* 1 — Die Griffe erscheinen beim Hinfahren. */
  let bild = await aufbauen();
  pruefe('Griffe erscheinen beim Hinfahren',
         document.querySelectorAll('.bildgriff').length >= 11,
         'nur ' + document.querySelectorAll('.bildgriff').length);

  /* 2 — Sie sitzen auf dem Bild. */
  let r = bild.getBoundingClientRect();
  let [gx, gy] = mitte(griff('nw'));
  pruefe('Griff oben links sitzt auf der Bildecke',
         Math.abs(gx - r.left) < 3 && Math.abs(gy - r.top) < 3,
         'Griff ' + Math.round(gx) + ',' + Math.round(gy)
         + ' gegen Bild ' + Math.round(r.left) + ',' + Math.round(r.top));

  /* 3 — Die Ecke haelt das Seitenverhaeltnis. */
  const vorher = bild.getBoundingClientRect();
  let [sx, sy] = mitte(griff('se'));
  zeiger('pointerdown', griff('se'), sx, sy, 11);
  zeiger('pointermove', griff('se'), sx + 120, sy, 11);
  await warte(80);
  zeiger('pointerup', griff('se'), sx + 120, sy, 11);
  await warte(200);
  const nachher = bild.getBoundingClientRect();
  pruefe('Ecke zieht groesser', nachher.width > vorher.width + 40,
         Math.round(vorher.width) + ' auf ' + Math.round(nachher.width));
  pruefe('Ecke haelt das Seitenverhaeltnis',
         Math.abs(nachher.width / nachher.height
                  - vorher.width / vorher.height) < 0.05,
         (vorher.width / vorher.height).toFixed(3) + ' gegen '
         + (nachher.width / nachher.height).toFixed(3));

  /* 4 — Die rechte Kante aendert nur die Breite. */
  const vorKante = bild.getBoundingClientRect();
  let [ex, ey] = mitte(griff('e'));
  zeiger('pointerdown', griff('e'), ex, ey, 12);
  zeiger('pointermove', griff('e'), ex - 60, ey, 12);
  await warte(80);
  zeiger('pointerup', griff('e'), ex - 60, ey, 12);
  await warte(200);
  const nachKante = bild.getBoundingClientRect();
  pruefe('Rechte Kante laesst die Hoehe stehen',
         Math.abs(nachKante.height - vorKante.height) < 2,
         Math.round(vorKante.height) + ' auf ' + Math.round(nachKante.height));

  /* 5 — Das Bild laesst sich frei ziehen. */
  bild = await aufbauen();
  r = bild.getBoundingClientRect();
  zeiger('pointerdown', bild, r.x + 30, r.y + 30, 13);
  zeiger('pointermove', bild, r.x + 110, r.y + 90, 13);
  await warte(80);
  zeiger('pointerup', bild, r.x + 110, r.y + 90, 13);
  await warte(200);
  pruefe('Bild schwebt nach dem Ziehen',
         bild.classList.contains('bild--frei'), 'Klasse fehlt');
  pruefe('Bild hat eine Stelle bekommen',
         !!bild.style.left && !!bild.style.top,
         'links=' + bild.style.left + ' oben=' + bild.style.top);

  /* 6 — Es bleibt im Blatt. */
  r = bild.getBoundingClientRect();
  zeiger('pointerdown', bild, r.x + 30, r.y + 30, 14);
  zeiger('pointermove', bild, r.x + 5000, r.y + 5000, 14);
  await warte(100);
  zeiger('pointerup', bild, r.x + 5000, r.y + 5000, 14);
  await warte(200);
  const bogen = feld.getBoundingClientRect();
  const jetzt = bild.getBoundingClientRect();
  pruefe('Bild bleibt im Blatt',
         jetzt.left < bogen.right && jetzt.top < bogen.bottom,
         'Bild bei ' + Math.round(jetzt.left) + ',' + Math.round(jetzt.top));

  /* 7 — Drehen und Spiegeln vertragen sich. */
  bild = await aufbauen();
  /* Ueber die Leiste, nicht ueber B — dieselben Knoepfe, die auch ein
     Anwender drueckt. */
  const leistenKnopf = (teil) => [...document.querySelectorAll('#werkzeugleiste3 button')]
    .find((k) => k.title.indexOf(teil) > -1);
  const drehen = leistenKnopf('rechts drehen');
  const spiegeln = leistenKnopf('Waagerecht spiegeln');
  if (!drehen || !spiegeln) {
    pruefe('Drehen und Spiegeln stehen in der Leiste', false,
           'Knoepfe nicht gefunden');
  }
  if (drehen) drehen.click();
  await warte(150);
  if (spiegeln) spiegeln.click();
  await warte(150);
  pruefe('Spiegeln loescht die Drehung nicht',
         /rotate\(90deg\)/.test(bild.style.transform)
         && /scale\(-1/.test(bild.style.transform),
         bild.style.transform);

  /* 8 — Der Schnittmodus. */
  bild = await aufbauen();
  document.querySelector('.bildgriff--schnell-schnitt').click();
  await warte(300);
  pruefe('Schnittmodus schaltet ein',
         document.body.classList.contains('schneidet'), 'Klasse fehlt');
  pruefe('Acht Marken', document.querySelectorAll('.bildgriff--marke').length === 8,
         document.querySelectorAll('.bildgriff--marke').length + ' Marken');
  pruefe('Blasse Fassung dahinter', !!document.querySelector('.schnittschatten'),
         'fehlt');

  /* 9 — Die Marke sitzt am Ausschnitt und folgt beim Ziehen. */
  let [mx, my] = mitte(griff('se'));
  zeiger('pointerdown', griff('se'), mx, my, 15);
  zeiger('pointermove', griff('se'), mx - 70, my - 45, 15);
  await warte(100);
  const markeJetzt = mitte(griff('se'));
  zeiger('pointerup', griff('se'), mx - 70, my - 45, 15);
  await warte(200);
  pruefe('Schnitt wird gesetzt', /inset/.test(bild.style.clipPath),
         bild.style.clipPath || 'keiner');
  pruefe('Marke folgt dem Ausschnitt', Math.abs(markeJetzt[0] - mx) > 30,
         'Marke stand bei ' + Math.round(markeJetzt[0]) + ', Start ' + Math.round(mx));

  /* 10 — Verlassen raeumt auf.

     Verlassen heisst: woanders hinklicken. Nur mit der Maus wegfahren
     reicht nicht — dann ist das Bild immer noch gewaehlt, und in WPS
     bleiben die Marken ebenfalls stehen. */
  const absatz = feld.querySelectorAll('p')[2];
  absatz.dispatchEvent(new PointerEvent('pointerover',
    { bubbles: true, pointerId: 1, pointerType: 'mouse' }));
  const hin = document.createRange();
  hin.selectNodeContents(absatz);
  const s2 = window.getSelection();
  s2.removeAllRanges();
  s2.addRange(hin);
  s2.collapseToStart();
  await warte(550);
  pruefe('Griffe verschwinden beim Verlassen',
         document.querySelectorAll('.bildgriff').length === 0,
         document.querySelectorAll('.bildgriff').length + ' geblieben');
  pruefe('Schnittmodus endet mit',
         !document.body.classList.contains('schneidet'), 'noch an');
  pruefe('Blasse Fassung weg', !document.querySelector('.schnittschatten'),
         'noch da');

  /* 11 — Ein Klick waehlt aus, ohne das Bild zu loesen, und die
     Schnellknoepfe bleiben erreichbar. */
  bild = await aufbauen();
  let br = bild.getBoundingClientRect();
  zeiger('pointerdown', bild, br.x + 20, br.y + 20, 21);
  zeiger('pointerup', bild, br.x + 20, br.y + 20, 21);
  await warte(300);
  pruefe('Klick loest das Bild nicht aus dem Text',
         !bild.classList.contains('bild--frei'), 'es schwebt jetzt');
  /* Maus weit weg vom Blatt — die Griffe muessen bleiben, sonst kommt
     man nie an die Knoepfe. */
  document.body.dispatchEvent(new PointerEvent('pointerover',
    { bubbles: true, pointerId: 1, pointerType: 'mouse' }));
  feld.dispatchEvent(new PointerEvent('pointerleave',
    { bubbles: false, pointerId: 1, pointerType: 'mouse' }));
  await warte(400);
  pruefe('Griffe bleiben, wenn die Maus zu den Knoepfen wandert',
         document.querySelectorAll('.bildgriff--schnell').length === 3,
         document.querySelectorAll('.bildgriff--schnell').length + ' Knoepfe');
  const schnellKnopf = document.querySelector('.bildgriff--schnell-lupe');
  pruefe('Der Lupenknopf laesst sich erreichen',
         !!schnellKnopf && !schnellKnopf.hidden, 'fehlt oder versteckt');
  if (schnellKnopf) {
    schnellKnopf.click();
    await warte(300);
    pruefe('Die Lupe geht auf', !!document.querySelector('.bildschau'), 'keine Schau');
    const zu = document.querySelector('.bildschau__zu');
    if (zu) zu.click();
    await warte(200);
  }

  /* 12 — Der Zeiger ist frei. */
  pruefe('Kein gefangener Zeiger',
         !document.body.classList.contains('zieht-tabelle'), 'zieht-tabelle liegt an');

  feld.innerHTML = '<p><br></p>';
  return ergebnis.join('\n');
})();
