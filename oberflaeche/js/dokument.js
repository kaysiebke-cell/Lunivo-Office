/* ============================================================
   Das Dokument.

   Ein Schreibprogramm braucht mehr als ein Textfeld: Fett und Kursiv,
   Überschriften, Aufzählungen, ein Blatt mit Rand. Deshalb steht hier
   kein <textarea>, sondern ein beschreibbarer Bereich (contenteditable).

   Der Prüfer aus der App kennt aber nur einen einzigen langen Text mit
   Stellen darin („von 42 bis 47"). Zwischen beidem vermittelt dieses
   Stück: Es liest das Dokument als Text und merkt sich zu jedem Textstück,
   wo es im Dokument steht. Damit findet jeder Fund seinen Weg zurück —
   auch mitten in ein fett geschriebenes Wort hinein.

   Geändert wird über execCommand. Das gilt als altmodisch, hat hier aber
   einen Grund, den nichts anderes ersetzt: Nur so landet die Änderung im
   Rückgängig-Stapel des Browsers. Strg+Z nimmt eine Korrektur der
   Schreibhilfe genauso zurück wie einen Tippfehler.
   ============================================================ */
'use strict';

const Dokument = (() => {
  const feld = document.getElementById('dokument');

  /* Was einen Absatz beendet. Alles andere (fett, kursiv, Link) läuft im
     Text weiter, ohne Umbruch. */
  const BLOCK = /^(P|DIV|H1|H2|H3|H4|H5|H6|LI|UL|OL|BLOCKQUOTE|PRE|TABLE|TR|TD|TH|HR|FIGURE|FIGCAPTION)$/;

  /** Liest das Dokument als einen Text — und dazu die Karte, wo was steht. */
  function lies() {
    const karte = [];
    let text = '';
    let umbruchOffen = false;

    (function gehe(knoten) {
      for (const kind of knoten.childNodes) {
        if (kind.nodeType === Node.TEXT_NODE) {
          if (!kind.data) continue;
          if (umbruchOffen) { text += '\n'; umbruchOffen = false; }
          karte.push({ knoten: kind, von: text.length, bis: text.length + kind.data.length });
          text += kind.data;
        } else if (kind.nodeType === Node.ELEMENT_NODE) {
          const tag = kind.tagName;
          if (tag === 'BR') { text += '\n'; umbruchOffen = false; continue; }
          if (BLOCK.test(tag) && text) umbruchOffen = true;
          gehe(kind);
          if (BLOCK.test(tag) && text) umbruchOffen = true;
        }
      }
    })(feld);

    return { text, karte };
  }

  /** Zu einer Stelle im Text die Stelle im Dokument. */
  function punkt(karte, stelle) {
    let letzter = null;
    for (const e of karte) {
      if (stelle < e.von) break;
      if (stelle <= e.bis) return { knoten: e.knoten, versatz: stelle - e.von };
      letzter = e;
    }
    if (letzter) return { knoten: letzter.knoten, versatz: letzter.knoten.data.length };
    return { knoten: feld, versatz: 0 };
  }

  /** Aus zwei Stellen im Text ein Stück Dokument. */
  function bereich(karte, von, bis) {
    const a = punkt(karte, von);
    const b = punkt(karte, bis);
    const r = document.createRange();
    r.setStart(a.knoten, Math.min(a.versatz, a.knoten.length ?? 0));
    r.setEnd(b.knoten, Math.min(b.versatz, b.knoten.length ?? 0));
    return r;
  }

  function waehle(r) {
    const auswahl = window.getSelection();
    auswahl.removeAllRanges();
    auswahl.addRange(r);
  }

  /** Markiert eine Stelle und rollt sie ins Bild — der Knopf „Zeigen". */
  function zeige(von, bis) {
    const { karte } = lies();
    const r = bereich(karte, von, bis);
    feld.focus();
    waehle(r);
    const kasten = r.getBoundingClientRect();
    const flaeche = document.getElementById('arbeitsflaeche');
    const sicht = flaeche.getBoundingClientRect();
    if (kasten.top < sicht.top + 40 || kasten.bottom > sicht.bottom - 40) {
      flaeche.scrollTop += kasten.top - sicht.top - sicht.height / 3;
    }
  }

  /** Ersetzt eine Stelle. Über execCommand, damit Strg+Z sie zurückholt. */
  function ersetze(von, bis, neu) {
    const { text, karte } = lies();
    if (von < 0 || bis > text.length) return false;
    feld.focus();
    waehle(bereich(karte, von, bis));
    document.execCommand('insertText', false, neu);
    return true;
  }

  /* ------------------------------------------------------------
     Formatieren. Alles über execCommand — dieselbe Begründung wie oben:
     der Rückgängig-Stapel des Browsers.
     ------------------------------------------------------------ */
  function befehl(name, wert = null) {
    feld.focus();
    try { document.execCommand(name, false, wert); } catch (e) { /* kennt der Browser nicht */ }
    document.dispatchEvent(new CustomEvent('dokument:geaendert'));
  }

  /** Fragt, ob Fett/Kursiv/… gerade an ist — für die gedrückten Knöpfe. */
  function anGeschaltet(name) {
    try { return document.queryCommandState(name); } catch (e) { return false; }
  }

  /** In welchem Absatzformat steht der Zeiger gerade? */
  function absatzformat() {
    let k = window.getSelection().anchorNode;
    while (k && k !== feld) {
      if (k.nodeType === Node.ELEMENT_NODE && /^(P|H1|H2|H3|H4|LI|BLOCKQUOTE|PRE)$/.test(k.tagName)) {
        return k.tagName.toLowerCase();
      }
      k = k.parentNode;
    }
    return 'p';
  }

  /** Fügt etwas Fertiges ein — Datum, Sonderzeichen, Bild, Tabelle. */
  function einfuegen(html) {
    feld.focus();
    document.execCommand('insertHTML', false, html);
    document.dispatchEvent(new CustomEvent('dokument:geaendert'));
  }

  /** Setzt das ganze Dokument neu — beim Öffnen einer Datei. */
  function setzeInhalt(html) {
    feld.innerHTML = html || '<p><br></p>';
    if (!feld.firstChild) feld.innerHTML = '<p><br></p>';
    document.dispatchEvent(new CustomEvent('dokument:geaendert'));
  }

  const inhalt = () => feld.innerHTML;

  /** Zählt, was in der Statuszeile steht. */
  function zaehle() {
    const text = lies().text;
    const woerter = text.trim() ? text.trim().split(/\s+/).length : 0;
    return { zeichen: text.length, woerter };
  }

  return {
    feld, lies, bereich, punkt, waehle, zeige, ersetze,
    befehl, anGeschaltet, absatzformat, einfuegen, setzeInhalt, inhalt, zaehle,
  };
})();
