/* ============================================================
   Dateien: öffnen, speichern, drucken.

   Vier Formate, und für jedes einen Grund:

     .odt   das Format von LibreOffice und OpenOffice. Wer den Text
            weiterreicht, reicht ihn so weiter.
     .fodt  dasselbe, nur als eine einzige XML-Datei ohne Verpackung.
            Nützlich, wenn etwas schiefgeht: Man kann hineinsehen.
     .html  öffnet sich in Word, im Browser, überall.
     .txt   nur die Wörter, ohne alles. Für Formulare im Netz.

   Die .odt wird ohne Zusammenpressen gepackt. Das macht die Datei etwas
   größer und den Code deutlich kleiner — und jedes Programm, das .odt
   liest, kommt damit zurecht: Der Eintrag „mimetype" muss ohnehin
   unverpackt ganz vorn stehen.
   ============================================================ */
'use strict';

const Dateien = (() => {

  /* ---------- Werkzeug: ZIP ohne Zusammenpressen ---------- */

  const CRC_TABELLE = (() => {
    const t = new Uint32Array(256);
    for (let i = 0; i < 256; i++) {
      let c = i;
      for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[i] = c >>> 0;
    }
    return t;
  })();

  function crc32(bytes) {
    let c = 0xFFFFFFFF;
    for (let i = 0; i < bytes.length; i++) c = CRC_TABELLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  const roh = (s) => new TextEncoder().encode(s);

  function packe(eintraege) {
    const teile = [];
    const verzeichnis = [];
    let stelle = 0;

    for (const [name, inhalt] of eintraege) {
      const daten = typeof inhalt === 'string' ? roh(inhalt) : inhalt;
      const nameRoh = roh(name);
      const summe = crc32(daten);

      const kopf = new DataView(new ArrayBuffer(30));
      kopf.setUint32(0, 0x04034b50, true);
      kopf.setUint16(4, 20, true);            // Fassung
      kopf.setUint16(8, 0, true);             // 0 = unverpackt abgelegt
      kopf.setUint32(14, summe, true);
      kopf.setUint32(18, daten.length, true);
      kopf.setUint32(22, daten.length, true);
      kopf.setUint16(26, nameRoh.length, true);
      teile.push(new Uint8Array(kopf.buffer), nameRoh, daten);

      const eintrag = new DataView(new ArrayBuffer(46));
      eintrag.setUint32(0, 0x02014b50, true);
      eintrag.setUint16(4, 20, true);
      eintrag.setUint16(6, 20, true);
      eintrag.setUint16(10, 0, true);
      eintrag.setUint32(16, summe, true);
      eintrag.setUint32(20, daten.length, true);
      eintrag.setUint32(24, daten.length, true);
      eintrag.setUint16(28, nameRoh.length, true);
      eintrag.setUint32(42, stelle, true);
      verzeichnis.push(new Uint8Array(eintrag.buffer), nameRoh);

      stelle += 30 + nameRoh.length + daten.length;
    }

    const laenge = verzeichnis.reduce((s, t) => s + t.length, 0);
    const ende = new DataView(new ArrayBuffer(22));
    ende.setUint32(0, 0x06054b50, true);
    ende.setUint16(8, eintraege.length, true);
    ende.setUint16(10, eintraege.length, true);
    ende.setUint32(12, laenge, true);
    ende.setUint32(16, stelle, true);

    return new Blob([...teile, ...verzeichnis, new Uint8Array(ende.buffer)],
                    { type: 'application/vnd.oasis.opendocument.text' });
  }

  /** Holt eine Datei aus einem ZIP heraus. */
  async function auspacken(puffer, gesucht) {
    const sicht = new DataView(puffer);
    const bytes = new Uint8Array(puffer);
    let stelle = 0;
    while (stelle + 30 <= bytes.length && sicht.getUint32(stelle, true) === 0x04034b50) {
      const art = sicht.getUint16(stelle + 8, true);
      const gross = sicht.getUint32(stelle + 18, true);
      const nameLaenge = sicht.getUint16(stelle + 26, true);
      const zusatz = sicht.getUint16(stelle + 28, true);
      const name = new TextDecoder().decode(bytes.subarray(stelle + 30, stelle + 30 + nameLaenge));
      const von = stelle + 30 + nameLaenge + zusatz;
      const daten = bytes.subarray(von, von + gross);
      if (name === gesucht) {
        if (art === 0) return new TextDecoder().decode(daten);
        if (typeof DecompressionStream === 'undefined') {
          throw new Error('Diese Datei ist zusammengepresst; dieses Fenster kann das nicht auspacken. '
                          + 'In LibreOffice als .fodt speichern und die noch einmal öffnen.');
        }
        const strom = new Blob([daten]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
        return new Response(strom).text();
      }
      stelle = von + gross;
    }
    throw new Error(gesucht + ' steht nicht in der Datei.');
  }

  /* ---------- HTML → ODF ---------- */

  const x = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  const AUSRICHTUNG = { left: 'Links', center: 'Mitte', right: 'Rechts', justify: 'Block' };

  /* Für jede Auszeichnung eine eigene Vorlage. Verschachtelt ergibt das
     fett-und-kursiv, ohne dass es dafür eine dritte Vorlage bräuchte. */
  const AUSZEICHNUNG = { B: 'Fett', STRONG: 'Fett', I: 'Kursiv', EM: 'Kursiv',
                         U: 'Unterstrichen', S: 'Durchgestrichen', STRIKE: 'Durchgestrichen' };

  /* ------------------------------------------------------------
     Schriftart und Schriftgröße.

     Fett und Kursiv haben je eine feste Vorlage — bei der Schrift geht das
     nicht: „DejaVu Sans in 14 pt" ist eine von vielen Möglichkeiten, und
     welche vorkommen, weiß man erst, wenn der Text fertig ist. ODF sieht
     dafür automatische Vorlagen vor: für jede vorkommende Kombination eine,
     durchnummeriert als T1, T2, T3. Genau so macht es LibreOffice auch.

     Ohne das hier ging die Schrift beim Speichern verloren — man wählte aus
     fünfhundert Schriften eine aus, und in der Datei stand wieder die
     Standardschrift.
     ------------------------------------------------------------ */
  let textVorlagen;      // „Schrift|Größe" → „T1"
  let textVorlagenXml;
  let benutzteSchriften;

  function textVorlage(familie, groesse) {
    const schluessel = familie + '|' + groesse;
    if (textVorlagen.has(schluessel)) return textVorlagen.get(schluessel);

    const name = 'T' + (textVorlagen.size + 1);
    textVorlagen.set(schluessel, name);
    if (familie) benutzteSchriften.add(familie);
    textVorlagenXml += '<style:style style:name="' + name + '" style:family="text">'
      + '<style:text-properties'
      + (familie ? ' style:font-name="' + x(familie) + '"' : '')
      + (groesse ? ' fo:font-size="' + x(groesse) + '"' : '')
      + '/></style:style>';
    return name;
  }

  /* Der Browser schreibt die Schrift als <font face="…"> und die Größe als
     <span style="font-size:14pt">. Beides kann auch übereinanderliegen. */
  function schriftAmKnoten(el) {
    let familie = '';
    let groesse = '';

    if (el.tagName === 'FONT') familie = el.getAttribute('face') || '';
    if (el.style) {
      familie = familie || (el.style.fontFamily || '').replace(/^["']|["']$/g, '');
      // Nur Punktangaben: Was der Browser in Pixeln ausrechnet, hat in einer
      // Datei für den Druck nichts verloren.
      if (/pt$/.test(el.style.fontSize)) groesse = el.style.fontSize;
    }
    return { familie, groesse };
  }

  function odfInhalt(knoten) {
    let aus = '';
    for (const kind of knoten.childNodes) {
      if (kind.nodeType === Node.TEXT_NODE) {
        aus += x(kind.data).replace(/ {2,}/g, (l) => '<text:s text:c="' + l.length + '"/>');
      } else if (kind.nodeType === Node.ELEMENT_NODE) {
        if (kind.tagName === 'BR') { aus += '<text:line-break/>'; continue; }
        const vorlage = AUSZEICHNUNG[kind.tagName];
        const innen = odfInhalt(kind);
        if (vorlage) {
          aus += '<text:span text:style-name="' + vorlage + '">' + innen + '</text:span>';
          continue;
        }
        const { familie, groesse } = schriftAmKnoten(kind);
        aus += (familie || groesse)
          ? '<text:span text:style-name="' + textVorlage(familie, groesse) + '">'
            + innen + '</text:span>'
          : innen;
      }
    }
    return aus;
  }

  function odfAbsatz(el) {
    const stil = AUSRICHTUNG[el.style.textAlign] || 'Standard';
    const innen = odfInhalt(el) || '';
    const ebene = /^H([1-4])$/.exec(el.tagName);
    if (ebene) {
      return '<text:h text:style-name="Ueberschrift_' + ebene[1] + '" text:outline-level="'
             + ebene[1] + '">' + innen + '</text:h>';
    }
    return '<text:p text:style-name="' + stil + '">' + innen + '</text:p>';
  }

  function odfListe(el) {
    let aus = '<text:list>';
    for (const punkt of el.children) {
      if (punkt.tagName !== 'LI') continue;
      aus += '<text:list-item><text:p text:style-name="Standard">' + odfInhalt(punkt) + '</text:p></text:list-item>';
    }
    return aus + '</text:list>';
  }

  function odfKoerper(html) {
    const hilfe = document.createElement('div');
    hilfe.innerHTML = html;
    let aus = '';
    for (const el of hilfe.children) {
      if (el.tagName === 'UL' || el.tagName === 'OL') aus += odfListe(el);
      else aus += odfAbsatz(el);
    }
    return aus || '<text:p text:style-name="Standard"/>';
  }

  const KOPF =
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<office:document-content'
    + ' xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    + ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
    + ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
    + ' xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"'
    // svg: nur für die Schriftnamen — ohne diese Zeile weist LibreOffice die
    // Datei als fehlerhaft zurück, sobald eine Schrift darin vorkommt.
    + ' xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"'
    + ' office:version="1.2">';

  const VORLAGEN = [
    ['Links', 'start'], ['Mitte', 'center'], ['Rechts', 'end'], ['Block', 'justify'],
  ].map(([n, a]) => '<style:style style:name="' + n + '" style:family="paragraph"'
                    + ' style:parent-style-name="Standard"><style:paragraph-properties'
                    + ' fo:text-align="' + a + '"/></style:style>').join('')
    + [['Ueberschrift_1', '18pt'], ['Ueberschrift_2', '15pt'], ['Ueberschrift_3', '13pt'],
       ['Ueberschrift_4', '12pt']]
      .map(([n, g]) => '<style:style style:name="' + n + '" style:family="paragraph"'
                       + ' style:parent-style-name="Heading"><style:text-properties fo:font-size="'
                       + g + '" fo:font-weight="bold"/></style:style>').join('')
    + '<style:style style:name="Fett" style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>'
    + '<style:style style:name="Kursiv" style:family="text"><style:text-properties fo:font-style="italic"/></style:style>'
    + '<style:style style:name="Unterstrichen" style:family="text"><style:text-properties'
    + ' style:text-underline-style="solid" style:text-underline-width="auto"/></style:style>'
    + '<style:style style:name="Durchgestrichen" style:family="text"><style:text-properties'
    + ' style:text-line-through-style="solid"/></style:style>';

  /* Der Körper zuerst: Erst beim Durchgehen zeigt sich, welche Schriften
     überhaupt vorkommen — und die Vorlagen dafür müssen im fertigen XML
     davor stehen.

     Beide Dateiarten gehen durch diese eine Stelle. Als „.fodt" seinen
     eigenen Bauplan hatte, fehlten dort die Schriften — und schlimmer: Wer
     zuerst als .fodt speicherte, traf auf einen Sammler, den noch niemand
     angelegt hatte. Einmal bauen, zweimal verpacken. */
  function odfTeile(html) {
    textVorlagen = new Map();
    textVorlagenXml = '';
    benutzteSchriften = new Set();

    const koerper = odfKoerper(html);

    const schriften = benutzteSchriften.size
      ? '<office:font-face-decls>'
        + [...benutzteSchriften].map((f) =>
            '<style:font-face style:name="' + x(f) + '" svg:font-family="' + x(f) + '"/>').join('')
        + '</office:font-face-decls>'
      : '';

    return { koerper, schriften, vorlagen: VORLAGEN + textVorlagenXml };
  }

  const inhaltXml = (html) => {
    const teile = odfTeile(html);
    return KOPF + teile.schriften
      + '<office:automatic-styles>' + teile.vorlagen + '</office:automatic-styles>'
      + '<office:body><office:text>' + teile.koerper + '</office:text></office:body>'
      + '</office:document-content>';
  };

  const MANIFEST =
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"'
    + ' manifest:version="1.2">'
    + '<manifest:file-entry manifest:full-path="/" manifest:version="1.2"'
    + ' manifest:media-type="application/vnd.oasis.opendocument.text"/>'
    + '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
    + '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
    + '</manifest:manifest>';

  const STILE =
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<office:document-styles'
    + ' xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
    + ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
    + ' office:version="1.2"><office:styles/></office:document-styles>';

  const odt = (html) => packe([
    ['mimetype', 'application/vnd.oasis.opendocument.text'],
    ['META-INF/manifest.xml', MANIFEST],
    ['styles.xml', STILE],
    ['content.xml', inhaltXml(html)],
  ]);

  /* Dieselbe XML, nur alles in einer Datei — ohne Verpackung. */
  const fodt = (html) => {
    const teile = odfTeile(html);
    return '<?xml version="1.0" encoding="UTF-8"?>\n'
      + '<office:document'
      + ' xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
      + ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
      + ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
      + ' xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"'
      + ' xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"'
      + ' office:version="1.2" office:mimetype="application/vnd.oasis.opendocument.text">'
      + teile.schriften
      + '<office:automatic-styles>' + teile.vorlagen + '</office:automatic-styles>'
      + '<office:body><office:text>' + teile.koerper + '</office:text></office:body>'
      + '</office:document>';
  };

  /* ---------- ODF → HTML ---------- */

  function odfLies(xmlText) {
    const baum = new DOMParser().parseFromString(xmlText, 'application/xml');
    if (baum.querySelector('parsererror')) throw new Error('Die Datei ist beschädigt.');

    const stile = new Map();
    /* Die Textvorlagen: Schriftart, Größe und die Auszeichnungen. LibreOffice
       nennt sie T1, T2, T3 — die Namen sagen nichts, es zählt, was darin
       steht. Ohne diese Tabelle käme eine Datei aus LibreOffice hier ohne
       jede Schriftangabe an, und die eigene ginge beim nächsten Öffnen
       wieder verloren. */
    const textStile = new Map();

    for (const s of baum.getElementsByTagNameNS('*', 'style')) {
      const name = s.getAttribute('style:name') || s.getAttributeNS('*', 'name');
      if (!name) continue;

      const absatz = s.getElementsByTagNameNS('*', 'paragraph-properties')[0];
      const wie = absatz && (absatz.getAttribute('fo:text-align') || absatz.getAttributeNS('*', 'text-align'));
      if (wie) stile.set(name, { start: 'left', end: 'right', center: 'center', justify: 'justify' }[wie] || '');

      const text = s.getElementsByTagNameNS('*', 'text-properties')[0];
      if (!text) continue;
      const hole = (mit, ohne) => text.getAttribute(mit) || text.getAttributeNS('*', ohne) || '';
      const eigen = {
        familie: hole('style:font-name', 'font-name'),
        groesse: hole('fo:font-size', 'font-size'),
        fett:    /bold|[6-9]00/.test(hole('fo:font-weight', 'font-weight')),
        kursiv:  /italic|oblique/.test(hole('fo:font-style', 'font-style')),
        unter:   !!hole('style:text-underline-style', 'text-underline-style').replace('none', ''),
        durch:   !!hole('style:text-line-through-style', 'text-line-through-style').replace('none', ''),
      };
      if (eigen.familie || eigen.groesse || eigen.fett || eigen.kursiv || eigen.unter || eigen.durch) {
        textStile.set(name, eigen);
      }
    }

    const holeStil = (el) => el.getAttribute('text:style-name') || el.getAttributeNS('*', 'style-name') || '';
    const AUS = { Fett: 'b', Kursiv: 'i', Unterstrichen: 'u', Durchgestrichen: 's' };

    function innen(knoten) {
      let aus = '';
      for (const kind of knoten.childNodes) {
        if (kind.nodeType === Node.TEXT_NODE) { aus += x(kind.data); continue; }
        if (kind.nodeType !== Node.ELEMENT_NODE) continue;
        const name = kind.localName;
        if (name === 'line-break') { aus += '<br>'; continue; }
        if (name === 's') { aus += '&nbsp;'.repeat(+(kind.getAttribute('text:c') || 1)); continue; }
        if (name === 'tab') { aus += ' '; continue; }
        if (name === 'span') {
          const stil = holeStil(kind);
          const tag = AUS[stil];
          if (tag) { aus += '<' + tag + '>' + innen(kind) + '</' + tag + '>'; continue; }

          /* Keine der vier festen Vorlagen — dann steht in der Tabelle, was
             gemeint ist: eine Schrift, eine Größe, oder beides. */
          const eigen = textStile.get(stil);
          if (!eigen) { aus += innen(kind); continue; }

          let innerhalb = innen(kind);
          if (eigen.fett)   innerhalb = '<b>' + innerhalb + '</b>';
          if (eigen.kursiv) innerhalb = '<i>' + innerhalb + '</i>';
          if (eigen.unter)  innerhalb = '<u>' + innerhalb + '</u>';
          if (eigen.durch)  innerhalb = '<s>' + innerhalb + '</s>';

          const teile = [];
          if (eigen.familie) teile.push('font-family:' + eigen.familie.replace(/[;"']/g, ''));
          if (/^[\d.]+pt$/.test(eigen.groesse)) teile.push('font-size:' + eigen.groesse);
          aus += teile.length
            ? '<span style="' + teile.join(';') + '">' + innerhalb + '</span>'
            : innerhalb;
          continue;
        }
        aus += innen(kind);
      }
      return aus;
    }

    const koerper = baum.getElementsByTagNameNS('*', 'text')[0];
    if (!koerper) throw new Error('In der Datei steht kein Text.');

    let html = '';
    (function gehe(el) {
      for (const kind of el.children) {
        const name = kind.localName;
        if (name === 'p') {
          const wie = stile.get(holeStil(kind));
          html += '<p' + (wie ? ' style="text-align:' + wie + '"' : '') + '>'
                + (innen(kind) || '<br>') + '</p>';
        } else if (name === 'h') {
          const ebene = Math.min(4, +(kind.getAttribute('text:outline-level') || 1));
          html += '<h' + ebene + '>' + (innen(kind) || '<br>') + '</h' + ebene + '>';
        } else if (name === 'list') {
          /* Nicht jede Liste ist eine Aufzählung: LibreOffice steckt auch
             Überschriften in eine, wenn die Kapitelnummerierung an ist.
             Wer das übersieht, bekommt aus „Widerspruch" einen
             Aufzählungspunkt — genau das ist beim ersten Rückweg aus einer
             Word-Datei passiert. Also erst nachsehen, was darin steht. */
          const hatUeberschrift = kind.getElementsByTagNameNS('*', 'h').length > 0;
          if (hatUeberschrift) {
            gehe(kind);
          } else {
            html += '<ul>';
            for (const punkt of kind.children) html += '<li>' + innen(punkt) + '</li>';
            html += '</ul>';
          }
        } else if (name === 'section' || name === 'list-item') {
          gehe(kind);
        }
      }
    })(koerper);

    return html || '<p><br></p>';
  }

  /* ============================================================
     LibreOffice als Motor im Hintergrund

     Für .docx und PDF gibt es keinen ehrlichen Eigenbau. Die Filter, die
     eine Word-Datei richtig lesen, sind das Ergebnis von Jahrzehnten — und
     LibreOffice liegt ohnehin auf diesem Rechner. Also reicht das Fenster
     die Datei hinüber und nimmt das Ergebnis entgegen.

     Der Weg führt über start.py, nicht von hier aus direkt: Eine Seite darf
     kein Programm auf dem Rechner starten, und das ist auch gut so.

     Läuft das Programm ausnahmsweise im Browser statt im eigenen Fenster,
     gibt es diesen Weg nicht. Dann sagt es das — statt stillschweigend eine
     kaputte Datei zu schreiben.
     ============================================================ */
  let motorDa = null;              // null = noch nicht gefragt

  async function umwandeln(rohdaten, von, nach) {
    const antwort = await fetch('umwandeln?von=' + encodeURIComponent(von)
                              + '&nach=' + encodeURIComponent(nach),
                                { method: 'POST', body: rohdaten });
    if (!antwort.ok) {
      let grund = 'Fehler ' + antwort.status;
      try { grund = (await antwort.json()).fehler || grund; } catch (e) { /* egal */ }
      motorDa = antwort.status !== 501;
      throw new Error(grund);
    }
    motorDa = true;
    return antwort.blob();
  }

  /* Ob es den Motor gibt, entscheidet, ob die Menüpunkte für Word und PDF
     überhaupt anzubieten sind. Gefragt wird einmal, mit einem winzigen
     Dokument — eine Antwort ist verlässlicher als eine Vermutung. */
  async function motorPruefen() {
    if (motorDa !== null) return motorDa;
    try {
      await umwandeln(new Blob([fodt('<p>.</p>')]), 'fodt', 'txt');
      motorDa = true;
    } catch (e) {
      motorDa = /nicht installiert/.test(e.message) ? false : motorDa;
      if (motorDa === null) motorDa = false;
    }
    return motorDa;
  }

  /* ---------- Hinein und hinaus ---------- */

  const alsAbsaetze = (text) => text.split(/\r?\n/)
    .map((z) => '<p>' + (x(z) || '<br>') + '</p>').join('');

  /* ============================================================
     Fremde Dateien hereinholen

     Word-Dateien gehen den Weg über HTML, nicht über flaches ODF. Der
     Unterschied ist groß: LibreOffice übersetzt das Layout selbst — Tabellen,
     Farben, Einzüge, Zeilenabstände, Bilder —, während der ODF-Leser weiter
     unten nur Absätze, Überschriften und ein paar Auszeichnungen kennt. Was
     er nicht kennt, fällt weg, und genau das ließ Briefe aus Word hier falsch
     aussehen.

     Der Preis: LibreOffice schickt ein ganzes Stilblatt mit. Das darf nicht
     einfach in die Seite — es würde auch die Menüs und die Seitenleiste
     umfärben. Deshalb wird jede Regel auf das Blatt eingeschränkt.
     ============================================================ */
  const UEBER_MOTOR = ['.docx', '.doc', '.rtf', '.odf', '.dotx', '.docm', '.dot'];

  /* Die Seitenränder aus der zuletzt geöffneten Datei — das Programm nebenan
     holt sie sich von hier und stellt das Blatt danach ein. */
  let letzteSeite = null;

  /* Jede Regel gilt nur noch innerhalb des Blattes. Aus „p.western { … }"
     wird „.dokument p.western { … }". */
  function stileEinschraenken(css) {
    const seite = {};

    /* @page trägt die Seitenränder. Als Regel nützt sie hier nichts — als
       Angabe für das Blatt aber sehr wohl. */
    css = css.replace(/@page[^{]*\{([^}]*)\}/gi, (ganz, innen) => {
      for (const [name, schluessel] of [['margin-top', 'oben'], ['margin-bottom', 'unten'],
                                        ['margin-left', 'links'], ['margin-right', 'rechts']]) {
        const treffer = new RegExp(name + '\\s*:\\s*([\\d.]+)\\s*cm', 'i').exec(innen);
        if (treffer) seite[schluessel] = Math.round(parseFloat(treffer[1]) * 10);
      }
      return '';
    });

    const regeln = [];
    for (const stueck of css.split('}')) {
      const teile = stueck.split('{');
      if (teile.length !== 2) continue;
      const wahl = teile[0].trim();
      let koerper = teile[1].trim();
      /* Verschachtelte Blöcke wie @media lassen sich so nicht sauber
         zerlegen — sie fliegen ganz heraus. In einem Brief steht nichts,
         was davon abhinge. */
      if (!wahl || !koerper || wahl.startsWith('@') || wahl.includes('<')) continue;

      /* LibreOffice schreibt den Seitenrand ein zweites Mal in die
         Grundregel für Absätze: „p { margin-left: 2cm }". Das Blatt hat
         seinen Rand aber schon. Beides zusammen rückte jede Zeile doppelt
         ein — der Text stünde viel zu weit rechts.

         Bei einer Regel, die nur ein Element nennt, ist der linke und rechte
         Abstand also der Seitenrand und muss weg. Steht eine Klasse dabei
         („p.western"), ist es ein wirklicher Einzug und bleibt. */
      const nurElement = /^[a-z0-9]+$/i.test(wahl);
      if (nurElement) {
        koerper = koerper.replace(/(^|;)\s*margin-(left|right)\s*:[^;]*/gi, '$1');
        /* Und dasselbe mit der Ausrichtung: „p { text-align: start }" ist
           keine Angabe aus dem Dokument, sondern LibreOffices Grundwert. Als
           Regel schlägt sie aber jedes align-Attribut — der Blocksatz eines
           Absatzes ging so verloren. */
        koerper = koerper.replace(/(^|;)\s*text-align\s*:[^;]*/gi, '$1');
      }

      regeln.push(wahl.split(',').map((w) => '.dokument ' + w.trim()).join(',')
                  + '{' + koerper + '}');
    }
    return { css: regeln.join('\n'), seite };
  }

  /* Alles, was nicht Text ist, fliegt heraus: Skripte, fremde Verweise,
     eingebettete Fenster. Die Datei kommt von irgendwoher. */
  function htmlSaeubern(rohText) {
    const baum = new DOMParser().parseFromString(rohText, 'text/html');

    let css = '';
    for (const block of baum.querySelectorAll('style')) css += block.textContent + '\n';
    const { css: eingeschraenkt, seite } = stileEinschraenken(css);
    letzteSeite = Object.keys(seite).length ? seite : null;

    let blatt = document.getElementById('importstile');
    if (!blatt) {
      blatt = document.createElement('style');
      blatt.id = 'importstile';
      document.head.appendChild(blatt);
    }
    blatt.textContent = eingeschraenkt;

    baum.querySelectorAll('script,style,link,meta,iframe,object,embed,base,form').forEach((e) => e.remove());

    /* LibreOffice schreibt Ausrichtung und Farben als Attribute: align,
       bgcolor. Attribute haben aber weniger Gewicht als jede Stilregel —
       das mitgelieferte Stilblatt hätte sie überstimmt. Als eigene Angabe am
       Element behalten sie ihr Gewicht. */
    for (const el of baum.querySelectorAll('[align],[bgcolor],[valign]')) {
      const wie = el.getAttribute('align');
      if (wie && /^(left|right|center|justify)$/i.test(wie) && !/text-align/i.test(el.style.cssText)) {
        el.style.textAlign = wie.toLowerCase();
      }
      const farbe = el.getAttribute('bgcolor');
      if (farbe && /^#?[0-9a-f]{3,8}$/i.test(farbe) && !el.style.backgroundColor) {
        el.style.backgroundColor = farbe.startsWith('#') ? farbe : '#' + farbe;
      }
      const senkrecht = el.getAttribute('valign');
      if (senkrecht && /^(top|middle|bottom)$/i.test(senkrecht)) {
        el.style.verticalAlign = senkrecht.toLowerCase();
      }
    }
    for (const el of baum.querySelectorAll('*')) {
      for (const eigenschaft of [...el.attributes]) {
        const name = eigenschaft.name.toLowerCase();
        if (name.startsWith('on')) { el.removeAttribute(eigenschaft.name); continue; }
        if ((name === 'href' || name === 'src') && /^\s*javascript:/i.test(eigenschaft.value)) {
          el.removeAttribute(eigenschaft.name);
        }
      }
    }
    return baum.body.innerHTML || '<p><br></p>';
  }

  /** Liest eine Datei und gibt das Dokument als HTML zurück. */
  async function oeffne(datei) {
    const name = datei.name.toLowerCase();
    letzteSeite = null;

    const ueber = UEBER_MOTOR.find((endung) => name.endsWith(endung));
    if (ueber) {
      const fertig = await umwandeln(datei, ueber.slice(1), 'html');
      return htmlSaeubern(await fertig.text());
    }

    /* „.ott" ist eine ODF-Vorlage — innen dieselbe content.xml wie in einer
       .odt. Ohne diese Zeile fiel sie durch bis zum Textleser und stand als
       Zeichensalat im Blatt. */
    if (name.endsWith('.odt') || name.endsWith('.ott')) {
      return odfLies(await auspacken(await datei.arrayBuffer(), 'content.xml'));
    }
    if (name.endsWith('.fodt') || name.endsWith('.xml')) return odfLies(await datei.text());
    if (name.endsWith('.html') || name.endsWith('.htm')) return htmlSaeubern(await datei.text());
    return alsAbsaetze(await datei.text());
  }

  const HTML_HUELLE = (html) =>
    '<!DOCTYPE html>\n<html lang="de"><head><meta charset="UTF-8">'
    + '<style>body{font-family:Georgia,serif;font-size:12pt;max-width:17cm;margin:2cm auto}</style>'
    + '</head><body>\n' + html + '\n</body></html>\n';

  /** Baut aus dem Dokument die Datei zum Sichern. */
  function baue(endung, html, text) {
    if (endung === 'odt')  return odt(html);
    if (endung === 'fodt') return new Blob([fodt(html)], { type: 'application/xml' });
    if (endung === 'html') return new Blob([HTML_HUELLE(html)], { type: 'text/html' });
    return new Blob([text], { type: 'text/plain' });
  }

  /* Was dieses Programm selbst nicht schreiben kann, schreibt LibreOffice.
     Der Umweg führt über flaches ODF: Das kennt dieses Programm genau, und
     LibreOffice liest es ohne Verlust. */
  /* „odt" steht mit in der Liste, obwohl dieses Programm es selbst schreiben
     kann: Über LibreOffice bleiben auch Tabellen und Bilder erhalten. Gibt es
     den Motor nicht, fällt das Speichern auf den eigenen Schreiber zurück —
     dann eben ohne Tabellen, aber es geht. */
  const MIT_MOTOR = { docx: 'docx', doc: 'doc', rtf: 'rtf', pdf: 'pdf', epub: 'epub', odt: 'odt' };

  const brauchtMotor = (endung) => Object.hasOwn(MIT_MOTOR, endung);

  /* Der Weg hinaus geht über HTML, nicht über den eigenen ODF-Schreiber.
     Der kennt keine Tabellen und keine Bilder: Wer eine Word-Datei mit
     Tabelle öffnete, ein Wort änderte und speicherte, hatte die Tabelle
     hinterher verloren. LibreOffice liest die Seite so, wie sie im Blatt
     steht, und setzt sie vollständig um. */
  async function baueMitMotor(endung, html) {
    const zwischen = new Blob([HTML_HUELLE(html)], { type: 'text/html' });
    return umwandeln(zwischen, 'html', MIT_MOTOR[endung]);
  }

  /** Reicht die Datei an den Rechner weiter. */
  function gib(blob, name) {
    const adresse = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = adresse;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(adresse), 30000);
  }

  /* Das mitgelieferte Stilblatt gehört zum Dokument, nicht zum Programm:
     Ohne es sähe derselbe Brief nach einem Neustart wieder anders aus.
     Deshalb lässt es sich von außen lesen und zurückgeben. */
  const stileLesen = () => {
    const blatt = document.getElementById('importstile');
    return blatt ? blatt.textContent : '';
  };

  const stileSetzen = (css) => {
    let blatt = document.getElementById('importstile');
    if (!blatt) {
      blatt = document.createElement('style');
      blatt.id = 'importstile';
      document.head.appendChild(blatt);
    }
    blatt.textContent = css || '';
  };

  /* Für das Einbetten von Tabellenblättern: Das Programm reicht die Datei
     roh an LibreOffice weiter und liest das Ergebnis selbst wieder ein. */
  const umwandelnRoh = (rohdaten, von, nach) => umwandeln(rohdaten, von, nach);
  const odfAlsHtml = (xml) => odfLies(xml);

  return { oeffne, baue, gib, baueMitMotor, brauchtMotor, motorPruefen,
           seiteZuletzt: () => letzteSeite, stileLesen, stileSetzen,
           umwandelnRoh, odfAlsHtml };
})();
