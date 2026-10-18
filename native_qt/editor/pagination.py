"""Seitenaufteilung, PDF-Ausgabe und Drucken mit Kopf-/Fußzeile und Seitenzahlen.

Das Dokument wird bei 96 dpi gesetzt (wie im Editor); beim Ausgeben wird der
Maler auf die Auflösung des Ausgabegeräts hochgerechnet. So stimmt der
Seitenumbruch auf dem Bildschirm mit dem im PDF überein.
"""
from __future__ import annotations

from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import (
    QFont, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat,
)
from PySide6.QtPrintSupport import QPrinter

from ..document_io.docx_reader import STYLE_PROP
from .zusatz import B_NOTENZIEL
from .page import PX_PER_MM, PageSettings, mm_to_px

_DEV = None


def layout_device() -> QImage:
    """Ein Gerät mit festen 96 dpi, an dem alle Dokumente gesetzt werden."""
    global _DEV
    if _DEV is None:
        _DEV = QImage(1, 1, QImage.Format_RGB32)
        _DEV.setDotsPerMeterX(round(96 / 0.0254))
        _DEV.setDotsPerMeterY(round(96 / 0.0254))
    return _DEV


_ZOOM_DEV: dict[int, QImage] = {}


def zoom_device(faktor: float) -> QImage:
    """Ein Gerät mit 96 dpi × Zoom: Text, Ränder, Tabellen und Bilder werden beim Setzen mitskaliert."""
    key = round(faktor * 1000)
    if key == 1000:
        return layout_device()
    d = _ZOOM_DEV.get(key)
    if d is None:
        d = QImage(1, 1, QImage.Format_RGB32)
        dpm = round(96 * key / 1000 / 0.0254)
        d.setDotsPerMeterX(dpm); d.setDotsPerMeterY(dpm)
        if len(_ZOOM_DEV) > 40:
            _ZOOM_DEV.clear()
        _ZOOM_DEV[key] = d
    return d


def bind_layout(qdoc: QTextDocument, faktor: float = 1.0) -> None:
    qdoc.documentLayout().setPaintDevice(zoom_device(faktor))


def noten_anhaengen(d: QTextDocument, noten: dict | None, arten: tuple = ("f", "e")) -> None:
    """Fuß- und Endnoten gesammelt am Textende (nur in der Kopie für Seitenzählung, PDF und Druck). Fußnoten stehen bei einer
    Spalte am Seitenfuß (fussnoten_am_seitenende) und werden dann hier nicht angehängt (arten=(„e“,))."""
    if not noten or not (noten.get("f") or noten.get("e")):
        return
    from .zusatz import P_NOTE, roemisch
    stellen = {"f": [], "e": []}
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_NOTE):
                art, _, nid = f.charFormat().stringProperty(P_NOTE).partition(":")
                stellen[art].append(int(nid))
            it += 1
        b = b.next()
    c = QTextCursor(d)
    c.movePosition(QTextCursor.End)
    from PySide6.QtGui import QTextBlockFormat
    for art, titel in (("f", "Fußnoten"), ("e", "Endnoten")):
        if not stellen[art] or art not in arten:
            continue
        c.insertBlock()
        kopf = QTextCharFormat(); kopf.setFontWeight(QFont.Bold); kopf.setFontPointSize(10)
        c.insertText("—" * 10 + " " + titel, kopf)
        for n, nid in enumerate(stellen[art], start=1):
            bf = QTextBlockFormat(); bf.setProperty(B_NOTENZIEL, f"{art}:{nid}")        # Sprungziel für die PDF-Verknüpfung
            c.insertBlock(bf)
            f = QTextCharFormat(); f.setFontPointSize(9)
            c.insertText(f"{n if art == 'f' else roemisch(n)}  {(noten.get(art, {}) or {}).get(nid, '')}", f)


_TRENNER = {}


def _trenner(sprache: str):
    """pyphen-Wörterbuch (zwischengespeichert); None, wenn pyphen oder die Sprache fehlt."""
    if sprache not in _TRENNER:
        try:
            import pyphen
            _TRENNER[sprache] = pyphen.Pyphen(lang=sprache, left=2, right=3) if sprache in pyphen.LANGUAGES else None
        except ImportError:
            _TRENNER[sprache] = None
    return _TRENNER[sprache]


_WORT = None


def silben_einfuegen(d: QTextDocument, sprache: str) -> int:
    """Fügt in einer KOPIE des Dokuments weiche Trennstriche (U+00AD) in lange Wörter ein; Qt bricht dort um und zeigt „-“.
    Überschriften, Wörter mit Ziffern/Sonderzeichen und Verweise bleiben unberührt. → Anzahl eingefügter Trennstellen."""
    global _WORT
    import re
    t = _trenner(sprache)
    if t is None:
        return 0
    if _WORT is None:
        _WORT = re.compile(r"[^\W\d_]{6,}", re.UNICODE)
    from PySide6.QtGui import QTextCursor
    n = 0
    b = d.firstBlock()
    while b.isValid():
        if b.blockFormat().headingLevel() == 0 and b.isVisible():
            text = b.text()
            stellen = []
            for m in _WORT.finditer(text):
                w = m.group()
                if w.isupper() or "\u00ad" in w:
                    continue
                for i in t.positions(w):
                    stellen.append(b.position() + m.start() + i)
            c = QTextCursor(d)
            for pos in reversed(stellen):                       # von hinten, damit die Stellen davor gültig bleiben
                c.setPosition(pos)
                c.insertText("\u00ad")
                n += 1
        b = b.next()
    return n


def ausgabe_seiten(logisch: int, page: PageSettings) -> int:
    """Seiten der Ausgabe: bei mehreren Spalten füllen je so viele „logische“ Spaltenseiten eine Blattseite."""
    return max(1, -(-max(1, logisch) // max(1, int(page.spalten))))


def paginated_copy(qdoc: QTextDocument, page: PageSettings, noten: dict | None = None, silben: bool | None = None,
                   einspaltig: bool = False, versteckt: bool = False, fussnoten: bool | str = True) -> QTextDocument:
    d = qdoc.clone()
    bind_layout(d)
    if not versteckt:                                   # ausgeblendeter Text zählt weder für Seiten noch für den Druck
        from .anzeige_extra import versteckte_entfernen
        versteckte_entfernen(d)
    am_fuss = fussnoten and _fussnoten_am_fuss(page, noten)
    noten_anhaengen(d, noten, ("e",) if am_fuss else ("f", "e"))
    if (page.silbentrennung if silben is None else silben):
        silben_einfuegen(d, page.silben_sprache)
    root = d.rootFrame()
    ff = root.frameFormat()
    ff.setMargin(0)
    root.setFrameFormat(ff)
    d.setDocumentMargin(0)
    d.setPageSize(QSizeF(page.content_width_px if einspaltig else page.spalten_breite_px, page.content_height_px))
    if am_fuss and fussnoten != "spaeter":                 # „spaeter“: render() ruft es nach den übrigen Änderungen selbst auf
        fussnoten_am_seitenende(d, page, noten)
    return d


def _fussnoten_am_fuss(page: PageSettings, noten: dict | None) -> bool:
    """Fußnoten am Seitenfuß gibt es bei einer Spalte; bei mehreren Spalten stehen sie gesammelt am Textende."""
    return bool(noten and noten.get("f")) and int(page.spalten) <= 1


def _fussnoten_stellen(d: QTextDocument) -> list[tuple[int, int, int]]:
    """[(Zeichenstelle, Fußnoten-Id, Länge)] in Textreihenfolge."""
    from .zusatz import P_NOTE
    out = []
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_NOTE):
                art, _, nid = f.charFormat().stringProperty(P_NOTE).partition(":")
                if art == "f":
                    out.append((f.position(), int(nid), f.length()))
            it += 1
        b = b.next()
    return out


def _zeilenbereiche(d: QTextDocument) -> list[tuple[float, float, int, int]]:
    """[(oben, unten, Zeichenstelle des Zeilenanfangs, Blocknummer)] aller Zeilen in Dokumentreihenfolge."""
    lay = d.documentLayout()
    out = []
    b = d.firstBlock()
    while b.isValid():
        tl = b.layout()
        if tl is not None and b.isVisible():
            top = lay.blockBoundingRect(b).top()
            for i in range(tl.lineCount()):
                ln = tl.lineAt(i)
                out.append((top + ln.y(), top + ln.y() + ln.height(), b.position() + ln.textStart(), b.blockNumber()))
        b = b.next()
    return out


def fussnoten_am_seitenende(d: QTextDocument, page: PageSettings, noten: dict) -> None:
    """Fußnoten unten auf der Seite, auf der ihre Marke steht (nur in der Kopie für Seitenzählung, Seitenansicht, PDF und Druck).

    Die Kopie wird so umbrochen, dass unter dem Text Platz für die Fußnoten der Seite bleibt: Reicht er nicht, wird vor der ersten
    Zeile, die nicht mehr passt, ein Seitenwechsel eingefügt (Absätze werden dabei geteilt). Das Ergebnis steht in
    `d._fussnoten` = {Seite (1-basiert): {"hoehe": px, "noten": [(y in px ab Textflächenanfang, QTextDocument)]}}."""
    from PySide6.QtGui import QTextBlockFormat
    ch, cw = page.content_height_px, page.content_width_px
    liste = (noten or {}).get("f", {}) or {}
    basis = d.defaultFont()
    kl = QFont(basis)
    kl.setPointSizeF(max(6.0, (basis.pointSizeF() if basis.pointSizeF() > 0 else 11.0) * 0.85))
    ABSTAND, TRENNER = 3.0, 12.0
    notendok: dict[int, QTextDocument] = {}

    def notendoc(nr: int, nid: int) -> QTextDocument:
        if nid not in notendok:
            nd = QTextDocument()
            nd.setDefaultFont(kl)
            nd.setDocumentMargin(0)
            nd.setPlainText(f"{nr}  {liste.get(nid, '')}")
            nd.setTextWidth(cw)
            nd.setPageSize(QSizeF(cw, -1))
            notendok[nid] = nd
        return notendok[nid]

    belegung: dict[int, list] = {}
    for _runde in range(60):
        d.documentLayout().documentSize()
        stellen = _fussnoten_stellen(d)
        zeilen = _zeilenbereiche(d)
        if not stellen or not zeilen:
            belegung = {}
            break
        starts = [z[2] for z in zeilen]
        import bisect
        belegung = {}
        for nr, (pos, nid, _l) in enumerate(stellen, start=1):
            i = max(0, bisect.bisect_right(starts, pos) - 1)
            seite = int((zeilen[i][0] + 0.5) // ch) + 1
            belegung.setdefault(seite, []).append((nr, nid))
        zu_hoch = None
        for seite, eintraege in sorted(belegung.items()):
            h = TRENNER + sum(notendoc(nr, nid).size().height() + ABSTAND for nr, nid in eintraege)
            if h >= ch * 0.85:
                continue                                           # eine Seite voller Fußnoten: Überlauf in Kauf nehmen
            grenze = seite * ch - h                                # untere Grenze des Textes dieser Seite
            erste = None
            for (o, u, pos, _bn) in zeilen:
                if (o + 0.5) // ch == seite - 1:
                    if erste is None:
                        erste = o
                    if u > grenze + 0.5 and o > erste + 0.5:
                        zu_hoch = pos
                        break
            if zu_hoch is not None:
                break
        if zu_hoch is None:
            break
        b = d.findBlock(zu_hoch)
        if zu_hoch == b.position():
            bf = b.blockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
            QTextCursor(b).setBlockFormat(bf)
        else:
            c = QTextCursor(d)
            c.setPosition(zu_hoch)
            neu = QTextBlockFormat(c.blockFormat())
            neu.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore); neu.setTopMargin(0); neu.setTextIndent(0)
            vorher = QTextBlockFormat(c.blockFormat()); vorher.setBottomMargin(0)
            QTextCursor(b).setBlockFormat(vorher)
            c.insertBlock(neu, c.charFormat())
    ergebnis: dict[int, dict] = {}
    for seite, eintraege in belegung.items():
        docs = [(nr, nid, notendoc(nr, nid)) for nr, nid in eintraege]
        h = TRENNER + sum(nd.size().height() + ABSTAND for _n, _i, nd in docs)
        y = seite * ch - h + TRENNER - (seite - 1) * ch
        platz = []
        for nr, nid, nd in docs:
            platz.append((y, nd, nid))
            y += nd.size().height() + ABSTAND
        ergebnis[seite] = {"hoehe": h, "noten": platz}
    d._fussnoten = ergebnis


def page_count(qdoc: QTextDocument, page: PageSettings) -> int:
    return ausgabe_seiten(paginated_copy(qdoc, page).pageCount(), page)


def _expand(text: str, n: int, total: int) -> str:
    return text.replace("{PAGE}", str(n)).replace("{PAGES}", str(total))


def _draw_hf(p: QPainter, hf, rect: QRectF, n: int, total: int, base: QFont) -> None:
    if hf.is_empty():
        return
    f = QFont(base)
    f.setPixelSize(13)
    p.setFont(f)
    flag = {"center": Qt.AlignHCenter, "right": Qt.AlignRight}.get(hf.align, Qt.AlignLeft)
    p.drawText(rect, int(flag | Qt.AlignVCenter | Qt.TextWordWrap), _expand(hf.text, n, total))


def _ohne_hintergruende(d: QTextDocument) -> None:
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QBrush, QTextCursor
    c = QTextCursor(d)
    c.select(QTextCursor.Document)
    f = QTextCharFormat(); f.setBackground(QBrush(_Qt.NoBrush)); c.mergeCharFormat(f)
    b = d.firstBlock()
    while b.isValid():
        bf = b.blockFormat()
        if bf.hasProperty(QTextFormat.BackgroundBrush):
            QTextCursor(b).setBlockFormat(_bf_ohne(bf))
        b = b.next()


def _ohne_hervorhebungen(d: QTextDocument) -> None:
    """Nur die Texthervorhebung (Marker) entfällt; Absatz- und Tabellenhintergründe bleiben."""
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QBrush, QTextCursor
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        stuecke = []
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().background().style() != _Qt.NoBrush and not f.charFormat().isImageFormat():
                stuecke.append((f.position(), f.position() + f.length()))
            it += 1
        for von, bis in stuecke:
            c = QTextCursor(d); c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
            fm = QTextCharFormat(); fm.setBackground(QBrush(_Qt.NoBrush)); c.mergeCharFormat(fm)
        b = b.next()


def _textmarken_klammern(d: QTextDocument) -> None:
    """„Textmarken drucken“: jede Textmarke steht in eckigen Klammern im Ausdruck."""
    from PySide6.QtGui import QTextCursor
    stellen = {}
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isAnchor() and not f.charFormat().anchorHref():
                for n in f.charFormat().anchorNames():
                    v, e = stellen.get(n, (f.position(), f.position() + f.length()))
                    stellen[n] = (min(v, f.position()), max(e, f.position() + f.length()))
            it += 1
        b = b.next()
    einfuegungen = sorted([(e, "]") for v, e in stellen.values()] + [(v, "[") for v, e in stellen.values()], reverse=True)
    for pos, z in einfuegungen:
        c = QTextCursor(d); c.setPosition(pos); c.insertText(z)


def _bf_ohne(bf):
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QBrush
    bf.setBackground(QBrush(_Qt.NoBrush))
    return bf


def seitenschmuck(p: QPainter, page: PageSettings, hintergrund: bool = True, flaeche=None) -> None:
    """Seitenfarbe, Seitenrahmen und Wasserzeichen. Koordinaten: Seite in 96-dpi-Bildpunkten, Ursprung links oben.
    `flaeche` (QRectF) überschreibt das Seitenrechteck — der Editor zeichnet damit jede Seite einzeln."""
    from PySide6.QtCore import QRectF as _R
    from PySide6.QtGui import QColor, QPen
    pw, ph = mm_to_px(page.width_mm), mm_to_px(page.height_mm)
    r = flaeche or _R(0, 0, pw, ph)
    p.save()
    if hintergrund and page.color:
        p.fillRect(r, QColor(page.color))
    b = page.border
    if b:
        a = mm_to_px(b.get("abstand_mm", 8.0))
        pen = QPen(QColor(b.get("farbe", "#000000")))
        pen.setWidthF(max(0.5, b.get("breite_pt", 1.0) * 96 / 72))
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRect(r.adjusted(a, a, -a, -a))
        if b.get("art") == "doppelt":
            g = a + pen.widthF() * 3
            p.drawRect(r.adjusted(g, g, -g, -g))
    w = page.watermark
    if w and w.get("text"):
        f = QFont("Liberation Sans")
        f.setPixelSize(max(8, int(w.get("groesse_pt", 80) * 96 / 72)))
        f.setBold(True)
        p.setFont(f)
        c = QColor(w.get("farbe", "#c0c0c0"))
        c.setAlpha(110)
        p.setPen(c)
        p.translate(r.center())
        p.rotate(w.get("winkel", -45))
        p.drawText(_R(-r.width(), -r.height() / 2, 2 * r.width(), r.height()), Qt.AlignCenter, w["text"])
    p.restore()


def seiten_liste(total: int, first: int, last: int, opt: dict | None) -> list[int]:
    """Welche Seiten in welcher Reihenfolge gedruckt werden (Duplex, umgekehrte Reihenfolge)."""
    seiten = list(range(first, last + 1))
    opt = opt or {}
    duplex = opt.get("duplex", "alle")
    if duplex == "vorder":
        seiten = [n for n in seiten if n % 2 == 1]
    elif duplex == "rueck":
        seiten = [n for n in seiten if n % 2 == 0]
    if opt.get("umgekehrt"):
        seiten.reverse()
    return seiten


def render(qdoc: QTextDocument, page: PageSettings, device, first: int = 1, last: int | None = None,
           dpi: int | None = None, opt: dict | None = None) -> int:
    """Zeichnet die Seiten first..last auf device (QPdfWriter/QPrinter). → Anzahl Seiten."""
    opt = opt or {}
    if opt.get("nur_formular"):                          # nur die Feldinhalte (für vorgedruckte Formulare): kein Seitenschmuck, keine Kopf-/Fußzeile
        from .page import HeaderFooter
        page = page.copy()
        page.border = None; page.watermark = None; page.color = ""
        page.header = HeaderFooter(); page.footer = HeaderFooter(); page.first_header = HeaderFooter(); page.first_footer = HeaderFooter()
        opt = dict(opt, hintergrund=False, textgrenzen=False, zuschnitt=False, balken=None, blasen=None)
    d = paginated_copy(qdoc, page, opt.get("noten"), versteckt=bool(opt.get("versteckt")), fussnoten="spaeter")
    from . import anzeige_extra as AX
    if opt.get("nur_formular"):
        from .formular import nur_formulardaten
        nur_formulardaten(d)
    if opt.get("felder_code"):
        AX.feldcodes_einsetzen(d)
    if opt.get("zeichnungen") is False:
        AX.zeichnungen_entfernen(d)
    if opt.get("luecken", True):
        from .vorlagen import luecken_entfernen
        luecken_entfernen(d)
    if opt.get("hintergrund") is False:
        _ohne_hintergruende(d)
    if opt.get("hervorhebungen") is False:
        _ohne_hervorhebungen(d)
    if opt.get("textmarken"):
        _textmarken_klammern(d)
    if opt.get("silbenfarben"):
        from .silbenfarben import SilbenFarben
        _hl = SilbenFarben(d, opt["silbenfarben"])             # bleibt bis zum Zeichnen am Leben (lokale Variable)
    if _fussnoten_am_fuss(page, opt.get("noten")):
        fussnoten_am_seitenende(d, page, opt["noten"])
    total = ausgabe_seiten(d.pageCount(), page)
    last = total if last is None else min(last, total)
    p = QPainter(device)
    s = (dpi or device.logicalDpiX()) / 96.0
    cw, ch = page.content_width_px, page.content_height_px
    ml, mt = mm_to_px(page.margin_left_mm), mm_to_px(page.margin_top_mm)
    pw, ph = mm_to_px(page.width_mm), mm_to_px(page.height_mm)
    base = qdoc.defaultFont()
    spalten = max(1, int(page.spalten))
    first_page = True
    balken = None
    if opt.get("balken") in ("links", "rechts", "außen") and d.characterCount() < 400000:
        balken = (opt["balken"], AX.aenderungszeilen(d))
    liste = seiten_liste(total, first, last, opt)
    if opt.get("leere") is False:
        leer = _leere_seiten(d, page, total)
        liste = [n for n in liste if n not in leer] or liste[:1]
    geo = blasen_geometrie(page, opt)
    pro_seite = _blasen_pro_seite(d, page, liste, opt["blasen"]) if geo else {}
    for n in liste:
        if not first_page:
            device.newPage()
        first_page = False
        p.save()
        p.scale(s, s)
        if geo:                                              # Seite verkleinert neben die Blasen setzen
            p.save()
            p.translate(geo["x_page"], 0)
            p.scale(geo["f"], geo["f"])
        zeichne_seite(p, d, page, n, total, base, opt.get("hintergrund") is not False, balken)
        if opt.get("textgrenzen") or opt.get("zuschnitt"):
            _druckmarken(p, page, bool(opt.get("textgrenzen")), bool(opt.get("zuschnitt")))
        if geo:
            p.restore()
            _blasen_zeichnen(p, pro_seite.get(n, []), geo)
        p.restore()
    p.end()
    if opt.get("lesezeichen") is not None:
        opt["lesezeichen_ergebnis"] = lesezeichen_sammeln(d, ch, liste, opt["lesezeichen"], spalten)
    if opt.get("kommentare"):
        opt["kommentare_ergebnis"] = kommentarstellen(d, ch, liste, opt["kommentare"], spalten)
    if opt.get("notenlinks"):
        opt["notenlinks_ergebnis"] = notenlinks_sammeln(d, page, liste)
    return total


def notenlinks_sammeln(d: QTextDocument, page: PageSettings, liste: list[int]) -> list[dict]:
    """Sprungverweise für die PDF: Marke → Note und Note → Marke (Fußnoten am Seitenfuß, Endnoten und gesammelte Noten am Textende).
    Jeder Eintrag: {seite, x, y, w, h} (Quelle, in px auf der Textfläche) und {ziel_seite, ziel_y}."""
    if int(page.spalten) > 1:
        return []
    from .zusatz import P_NOTE
    ch = page.content_height_px
    lay = d.documentLayout()
    fuss = getattr(d, "_fussnoten", None) or {}
    marken = {}
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_NOTE) and b.layout() is not None and b.layout().lineCount():
                art, _, nid = f.charFormat().stringProperty(P_NOTE).partition(":")
                rel = f.position() - b.position()
                ln = b.layout().lineForTextPosition(rel)
                if ln.isValid():
                    x1 = ln.cursorToX(rel)[0]
                    x2 = ln.cursorToX(rel + f.length())[0]
                    y = lay.blockBoundingRect(b).top() + ln.y()
                    lp = int((y + 0.5) // ch)
                    if lp + 1 in liste:
                        marken[(art, int(nid))] = {"seite": liste.index(lp + 1), "x": min(x1, x2), "y": y - lp * ch,
                                                   "w": abs(x2 - x1) + 2, "h": ln.height()}
            it += 1
        b = b.next()
    ziele = {}
    for seite, info in fuss.items():                                   # Fußnoten am Seitenfuß
        for y, nd, nid in info["noten"]:
            if seite in liste:
                ziele[("f", nid)] = {"seite": liste.index(seite), "y": y, "h": nd.size().height()}
    b = d.firstBlock()
    while b.isValid():                                                 # Endnoten (und Fußnoten, wenn sie gesammelt am Ende stehen)
        bf = b.blockFormat()
        if bf.hasProperty(B_NOTENZIEL):
            art, _, nid = str(bf.property(B_NOTENZIEL)).partition(":")
            top = lay.blockBoundingRect(b).top()
            lp = int((top + 0.5) // ch)
            if lp + 1 in liste:
                ziele[(art, int(nid))] = {"seite": liste.index(lp + 1), "y": top - lp * ch, "h": lay.blockBoundingRect(b).height()}
        b = b.next()
    out = []
    for key, m in marken.items():
        z = ziele.get(key)
        if z is None:
            continue
        out.append({"seite": m["seite"], "x": m["x"], "y": m["y"], "w": m["w"], "h": m["h"], "ziel_seite": z["seite"], "ziel_y": z["y"]})
        out.append({"seite": z["seite"], "x": 0, "y": z["y"], "w": page.content_width_px, "h": z["h"],
                    "ziel_seite": m["seite"], "ziel_y": m["y"]})
    return out


def kommentarstellen(d: QTextDocument, ch: float, liste: list[int], kommentare: dict, spalten: int = 1) -> list[tuple[int, float, str]]:
    """[(Seitenindex, y in px auf der Textfläche, Text)] für die PDF-Notizen. `kommentare` = {Kommentar-Id: Text}; die Stelle
    wird über die Eigenschaft P_KOMMENTAR in der Kopie gefunden (Zeichenstellen des Originals passen dort nicht mehr)."""
    from .zusatz import P_KOMMENTAR
    erste: dict[int, int] = {}
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_KOMMENTAR):
                erste.setdefault(int(f.charFormat().property(P_KOMMENTAR)), f.position())
            it += 1
        b = b.next()
    out = []
    for kid, text in kommentare.items():
        von = erste.get(int(kid))
        if von is None:
            continue
        b = d.findBlock(von)
        if not b.isValid() or b.layout() is None:
            continue
        zeile = b.layout().lineForTextPosition(von - b.position())
        y = d.documentLayout().blockBoundingRect(b).top() + (zeile.y() if zeile.isValid() else 0)
        logisch = int((y + 0.5) // ch) if ch else 0
        seite = logisch // spalten + 1
        if seite in liste:
            out.append((liste.index(seite), y - logisch * ch, text))
    return out


def lesezeichen_sammeln(d: QTextDocument, ch: float, liste: list[int], was: dict, spalten: int = 1) -> list[tuple[int, str, int]]:
    """[(Ebene, Titel, Seitenindex 0-basiert)] für die PDF-Gliederung: Überschriften und/oder Textmarken."""
    lay = d.documentLayout()
    out = []
    b = d.firstBlock()
    while b.isValid():
        seite = int((lay.blockBoundingRect(b).top() + 0.5) // ch) // spalten + 1 if ch else 1
        if seite in liste and b.isVisible():
            lv = b.blockFormat().headingLevel()
            if was.get("ueberschriften", True) and lv and b.text().strip():
                out.append((lv, b.text().strip(), liste.index(seite), b.position()))
            if was.get("andere") and b.text().strip() and b.blockFormat().hasProperty(STYLE_PROP) \
                    and b.blockFormat().property(STYLE_PROP) in ("title", "subtitle", "quote", "Title", "Subtitle", "Quote"):
                out.append((1, b.text().strip()[:120], liste.index(seite), b.position()))
            if was.get("textmarken"):
                it = b.begin()
                while not it.atEnd():
                    f = it.fragment()
                    if f.isValid() and f.charFormat().isAnchor() and not f.charFormat().anchorHref():
                        for n in f.charFormat().anchorNames():
                            if not any(o[1] == n and o[0] == 0 for o in out):
                                out.append((0, n, liste.index(seite), f.position()))
                    it += 1
        b = b.next()
    out.sort(key=lambda o: o[3])
    return [(lv, t, i) for lv, t, i, _p in out]


def gliederung_schreiben(pfad: str, eintraege: list[tuple[int, str, int]], kommentare=None, page: PageSettings | None = None,
                         links: list | None = None) -> None:
    """Schreibt Lesezeichen und Kommentare in die fertige PDF (QPdfWriter kann das nicht selbst) — mit pypdf."""
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter(clone_from=PdfReader(pfad))
    if kommentare and page is not None:
        from pypdf.annotations import Text
        ml, mt = mm_to_px(page.margin_left_mm) * 0.75, mm_to_px(page.margin_top_mm) * 0.75
        for seite, y, text in kommentare:
            if seite >= len(w.pages):
                continue
            hoehe = float(w.pages[seite].mediabox.height)
            oben = hoehe - mt - y * 0.75
            w.add_annotation(page_number=seite, annotation=Text(text=text, rect=(max(0, ml - 24), oben - 18, ml - 6, oben), open=False))
    if links and page is not None:
        from pypdf.annotations import Link
        from pypdf.generic import Fit
        ml, mt = mm_to_px(page.margin_left_mm) * 0.75, mm_to_px(page.margin_top_mm) * 0.75
        for k in links:
            if k["seite"] >= len(w.pages) or k["ziel_seite"] >= len(w.pages):
                continue
            hoehe = float(w.pages[k["seite"]].mediabox.height)
            x1 = ml + k["x"] * 0.75
            y2 = hoehe - mt - k["y"] * 0.75
            ziel_h = float(w.pages[k["ziel_seite"]].mediabox.height)
            w.add_annotation(page_number=k["seite"], annotation=Link(
                rect=(x1, y2 - k["h"] * 0.75, x1 + max(4.0, k["w"] * 0.75), y2), target_page_index=k["ziel_seite"],
                fit=Fit.xyz(left=ml, top=ziel_h - mt - max(0.0, k["ziel_y"] - 4) * 0.75, zoom=0)))
            ann = w.pages[k["seite"]]["/Annots"][-1].get_object()
            ziel = ann.get("/Dest")
            if ziel is not None and isinstance(ziel[0], int):
                ziel[0] = w.pages[int(ziel[0])].indirect_reference        # Verweise im Dokument zeigen auf die Seite selbst, nicht auf ihre Nummer
    eltern: dict[int, object] = {}
    for lv, titel, seite in eintraege:
        stufe = max(1, lv)                    # Textmarken (Ebene 0) stehen auf oberster Ebene
        vater = next((eltern[k] for k in range(stufe - 1, 0, -1) if k in eltern), None)
        eltern[stufe] = w.add_outline_item(titel, min(seite, len(w.pages) - 1), parent=vater)
        for k in [k for k in eltern if k > stufe]:
            del eltern[k]
    tmp = pfad + ".tmp"
    with open(tmp, "wb") as fh:
        w.write(fh)
    import os
    os.replace(tmp, pfad)


def _druckmarken(p: QPainter, page: PageSettings, grenzen: bool, zuschnitt: bool) -> None:
    """Textbegrenzungen (gestrichelter Rahmen um die Textfläche) und Zuschnittsmarken (Ecken) auf der gedruckten Seite."""
    from PySide6.QtGui import QColor, QPen
    cw, ch = page.content_width_px, page.content_height_px
    ml, mt = mm_to_px(page.margin_left_mm), mm_to_px(page.margin_top_mm)
    p.save()
    pen = QPen(QColor("#888888"))
    pen.setWidthF(0.7)
    if grenzen:
        pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(ml, mt, cw, ch))
    if zuschnitt:
        pen.setStyle(Qt.SolidLine)
        p.setPen(pen)
        l = mm_to_px(4)
        for x, y, dx, dy in ((ml, mt, -1, -1), (ml + cw, mt, 1, -1), (ml, mt + ch, -1, 1), (ml + cw, mt + ch, 1, 1)):
            p.drawLine(x + dx * 2, y, x + dx * (2 + l), y)
            p.drawLine(x, y + dy * 2, x, y + dy * (2 + l))
    p.restore()


def zeichne_seite(p: QPainter, d: QTextDocument, page: PageSettings, n: int, total: int, base: QFont,
                  hintergrund: bool = True, balken: tuple | None = None) -> None:
    """Eine Seite (Nummer n, 1-basiert) mit Seitenschmuck, Kopf-/Fußzeile und Text; Maßstab 96 dpi, Ursprung links oben."""
    cw, ch = page.content_width_px, page.content_height_px
    ml, mt = mm_to_px(page.margin_left_mm), mm_to_px(page.margin_top_mm)
    ph = mm_to_px(page.height_mm)
    seitenschmuck(p, page, hintergrund)
    kopf, fuss = (page.first_header, page.first_footer) if (n == 1 and page.diff_first) else (page.header, page.footer)
    _draw_hf(p, kopf, QRectF(ml, mm_to_px(8), cw, mm_to_px(10)), n, total, base)
    _draw_hf(p, fuss, QRectF(ml, ph - mm_to_px(18), cw, mm_to_px(10)), n, total, base)
    if page.zeilennummern and page.spalten <= 1:
        p.save()
        p.translate(ml, mt)
        p.translate(0, -(n - 1) * ch)
        _zeilennummern(p, d, n, ch, base)
        p.restore()
    fuss = getattr(d, "_fussnoten", None)
    if fuss and n in fuss and int(page.spalten) <= 1:                  # Fußnoten am Seitenfuß, mit kurzem Trennstrich
        from PySide6.QtGui import QColor, QPen
        p.save()
        p.translate(ml, mt)
        info = fuss[n]
        y0 = ch - info["hoehe"] + 6
        pen = QPen(QColor("#555555")); pen.setWidthF(0.6)
        p.setPen(pen)
        p.drawLine(0, int(y0), int(cw * 0.33), int(y0))
        for y, nd, _nid in info["noten"]:
            p.save()
            p.translate(0, y)
            nd.drawContents(p, QRectF(0, 0, cw, nd.size().height()))
            p.restore()
        p.restore()
    n_sp = max(1, int(page.spalten))
    cb = page.spalten_breite_px
    luecke = mm_to_px(page.spalten_abstand_mm)
    for j in range(n_sp):
        lp = (n - 1) * n_sp + j + 1                      # logische Spaltenseite, die in Spalte j dieser Blattseite steht
        if lp > d.pageCount():
            break
        p.save()
        p.translate(ml + j * (cb + luecke), mt)
        p.setClipRect(QRectF(-10, 0, cb + 20, ch))
        p.translate(0, -(lp - 1) * ch)
        d.drawContents(p, QRectF(0, (lp - 1) * ch, cb, ch))
        absatzrahmen_zeichnen(p, d)
        p.restore()
        if balken:                                          # Änderungsbalken neben den Zeilen mit verfolgten Änderungen
            seite_b, zeilen = balken
            rechts = seite_b == "rechts" or (seite_b == "außen" and n % 2 == 0)
            x = ml + j * (cb + luecke) + (cb + 6 if rechts else -6)
            from PySide6.QtGui import QColor, QPen
            p.save()
            pen = QPen(QColor("#c92a2a")); pen.setWidthF(1.4)
            p.setPen(pen)
            for t, u in zeilen:
                if int((t + 0.5) // ch) == lp - 1:
                    y0 = mt + t - (lp - 1) * ch
                    p.drawLine(int(x), int(y0), int(x), int(mt + min(u, lp * ch) - (lp - 1) * ch))
            p.restore()
    if n_sp > 1 and page.spalten_linie:
        from PySide6.QtGui import QColor, QPen
        p.save()
        pen = QPen(QColor("#888888")); pen.setWidthF(0.6)
        p.setPen(pen)
        for j in range(1, n_sp):
            x = ml + j * (cb + luecke) - luecke / 2
            p.drawLine(int(x), int(mt), int(x), int(mt + ch))
        p.restore()


def absatzrahmen_zeichnen(p: QPainter, d: QTextDocument, faktor: float = 1.0, polster: float = 4.0) -> None:
    """Rahmen um zusammenhängende Absätze mit gleichem B_RAHMEN. Koordinaten: Dokument (Layoutgerät); faktor = Zoom."""
    from PySide6.QtGui import QColor, QPen
    from .zusatz import B_RAHMEN
    lay = d.documentLayout()
    gruppen: list[list] = []
    b = d.firstBlock()
    while b.isValid():
        if b.blockFormat().hasProperty(B_RAHMEN) and b.isVisible():
            w = b.blockFormat().stringProperty(B_RAHMEN)
            if gruppen and gruppen[-1][0] == w and gruppen[-1][2] == b.blockNumber() - 1:
                gruppen[-1][1].append(b); gruppen[-1][2] = b.blockNumber()
            else:
                gruppen.append([w, [b], b.blockNumber()])
        b = b.next()
    for w, bloecke, _n in gruppen:
        farbe, _, rest = w.partition("|")
        pt, _, art = rest.partition("|")
        r = lay.blockBoundingRect(bloecke[0]).united(lay.blockBoundingRect(bloecke[-1]))
        pen = QPen(QColor(farbe or "#000000"))
        pen.setWidthF(max(0.6, float(pt or 1) * 96 / 72 * faktor))
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        pd = polster * faktor
        rr = r.adjusted(-pd, -pd + 1, pd, pd - 1)
        p.drawRect(rr)
        if art == "doppelt":
            g = pen.widthF() * 3
            p.drawRect(rr.adjusted(g, g, -g, -g))


def _zeilennummern(p: QPainter, d: QTextDocument, n: int, ch: float, base: QFont) -> None:
    """Fortlaufende Zeilennummern am linken Rand der Seite n (Koordinaten: Textfläche, auf die Seite verschoben)."""
    f = QFont(base)
    f.setPixelSize(9)
    p.setFont(f)
    p.setPen(Qt.gray)
    lay = d.documentLayout()
    nr = 0
    b = d.firstBlock()
    while b.isValid():
        if b.isVisible() and b.layout() is not None:
            top = lay.blockBoundingRect(b).top()
            for i in range(b.layout().lineCount()):
                nr += 1
                zeile = b.layout().lineAt(i)
                y = top + zeile.y()
                if (n - 1) * ch <= y < n * ch:
                    p.drawText(QRectF(-48, y, 42, zeile.height()), Qt.AlignRight | Qt.AlignVCenter, str(nr))
        b = b.next()


def seite_als_bild(qdoc: QTextDocument, page: PageSettings, n: int, faktor: float = 1.0, d: QTextDocument | None = None,
                   noten: dict | None = None) -> QImage:
    """Seite n als Bild (für die Zwei-Seiten-Ansicht und „Als Bild exportieren“)."""
    d = d or paginated_copy(qdoc, page, noten)
    total = ausgabe_seiten(d.pageCount(), page)
    w, h = int(mm_to_px(page.width_mm) * faktor), int(mm_to_px(page.height_mm) * faktor)
    img = QImage(w, h, QImage.Format_RGB32)
    img.fill(Qt.white)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.scale(faktor, faktor)
    zeichne_seite(p, d, page, n, total, qdoc.defaultFont())
    p.end()
    return img


def _leere_seiten(d: QTextDocument, page: PageSettings, total: int) -> set[int]:
    ch = page.content_height_px
    mit_text = set()
    b = d.firstBlock()
    lay = d.documentLayout()
    while b.isValid():
        if b.text().strip(chr(0xfffc) + " \t\n") or b.text():
            r = lay.blockBoundingRect(b)
            mit_text.add(int((r.top() + 0.5) // ch) // max(1, int(page.spalten)) + 1)
        b = b.next()
    return {n for n in range(1, total + 1) if n not in mit_text}


def blasen_geometrie(page: PageSettings, opt: dict | None) -> dict | None:
    """Platz für Sprechblasen beim Drucken: Die Seite wird verkleinert, daneben stehen die Blasen. → None ohne Blasen."""
    bd = (opt or {}).get("blasen")
    if not bd:
        return None
    from . import sprechblasen as SB
    k = bd["konfig"]
    pw, ph = mm_to_px(page.width_mm), mm_to_px(page.height_mm)
    bw, gap = mm_to_px(SB.breite_mm(k)), mm_to_px(SB.LUECKE_MM)

    def faktor(sw: float, sh: float) -> float:
        return min((sw - bw - gap) / pw, sh / ph)
    f_hoch = faktor(pw, ph)
    f_quer = faktor(ph, pw) if not page.landscape else f_hoch
    aus = k["ausrichtung"]
    quer = (not page.landscape) and (aus == "Querformat" or (aus == "Automatisch" and f_quer > f_hoch + 0.02))
    sw, sh = (ph, pw) if quer else (pw, ph)
    f = min(1.0, faktor(sw, sh))
    links = k["rand"] == "Links"
    x_page = bw + gap if links else 0.0
    return {"quer": quer, "f": f, "sw": sw, "sh": sh, "pw": pw, "x_page": x_page, "links": links,
            "x_blasen": 0.0 if links else pw * f + gap, "bw": bw, "mt": mm_to_px(page.margin_top_mm), "k": k}


def _blasen_pro_seite(d: QTextDocument, page: PageSettings, liste: list[int], bd: dict) -> dict[int, list]:
    """{Blattseite (1-basiert): [(Blase, y in px auf der Textfläche)]} — die Blasen stammen aus der Kopie selbst."""
    from . import sprechblasen as SB
    ch = page.content_height_px
    n_sp = max(1, int(page.spalten))
    lay = d.documentLayout()
    out: dict[int, list] = {}
    for bl in SB.sammeln(d, bd.get("kommentare", {}), bd["konfig"]["verwenden"]):
        b = d.findBlock(bl.von)
        if not b.isValid() or b.layout() is None:
            continue
        ln = b.layout().lineForTextPosition(bl.von - b.position())
        y = lay.blockBoundingRect(b).top() + (ln.y() if ln.isValid() else 0)
        lp = int((y + 0.5) // ch)
        out.setdefault(lp // n_sp + 1, []).append((bl, y - lp * ch))
    return out


def _blasen_zeichnen(p: QPainter, eintraege: list, geo: dict) -> None:
    from . import sprechblasen as SB
    if not eintraege:
        return
    font = QFont("Liberation Sans")
    font.setPixelSize(11)
    w, f = geo["bw"], geo["f"]
    hoehen = [SB.messen(bl, w, font) for bl, _y in eintraege]
    anker = [geo["mt"] * f + y * f for _bl, y in eintraege]
    ys = SB.stapeln(anker, hoehen, geo["sh"] - 12)
    kante = geo["x_page"] + (0 if geo["links"] else geo["pw"] * f)
    for (bl, _y), yy, h, a in zip(eintraege, ys, hoehen, anker):
        r = QRectF(geo["x_blasen"], yy, w, h)
        if geo["k"]["linien"]:
            SB.verbindung(p, bl, kante, a + 8, r, not geo["links"])
        SB.zeichnen(p, bl, r, font)


def _page_layout(page: PageSettings, quer: bool = False) -> QPageLayout:
    size = QPageSize(QSizeF(min(page.width_mm, page.height_mm), max(page.width_mm, page.height_mm)),
                     QPageSize.Millimeter)
    orient = QPageLayout.Landscape if (page.landscape or quer) else QPageLayout.Portrait
    return QPageLayout(size, orient, QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)


def export_pdf(path: str, qdoc: QTextDocument, page: PageSettings, title: str = "", author: str = "", noten: dict | None = None,
               lesezeichen: dict | None = None, silben: dict | None = None, kommentare: list | None = None,
               extra: dict | None = None) -> int:
    from PySide6.QtCore import QByteArray
    w = QPdfWriter(path)
    w.setResolution(300)
    geo = blasen_geometrie(page, extra)
    w.setPageLayout(_page_layout(page, bool(geo and geo["quer"])))
    if title:
        w.setTitle(title)
    w.setCreator("Lunivo Writer")
    if author:
        esc = author.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        w.setDocumentXmpMetadata(QByteArray(("<x:xmpmeta xmlns:x=\"adobe:ns:meta/\"><rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">"
                                             "<rdf:Description xmlns:dc=\"http://purl.org/dc/elements/1.1/\"><dc:creator><rdf:Seq><rdf:li>"
                                             + esc + "</rdf:li></rdf:Seq></dc:creator></rdf:Description></rdf:RDF></x:xmpmeta>").encode("utf-8")))
    opt = {"noten": noten} if noten else {}
    opt.update(extra or {})
    if lesezeichen:
        opt["lesezeichen"] = lesezeichen
    if silben:
        opt["silbenfarben"] = silben
    if kommentare:
        opt["kommentare"] = kommentare
    n = render(qdoc, page, w, opt=opt or None)
    if opt.get("lesezeichen_ergebnis") or opt.get("kommentare_ergebnis") or opt.get("notenlinks_ergebnis"):
        del w                                  # Datei schließen, bevor sie noch einmal geöffnet wird
        gliederung_schreiben(path, opt.get("lesezeichen_ergebnis") or [], opt.get("kommentare_ergebnis"), page,
                             opt.get("notenlinks_ergebnis"))
    return n


def print_document(printer: QPrinter, qdoc: QTextDocument, page: PageSettings, opt: dict | None = None) -> int:
    geo = blasen_geometrie(page, opt)
    printer.setPageLayout(_page_layout(page, bool(geo and geo["quer"])))
    first, last = 1, None
    if printer.printRange() == QPrinter.PageRange and printer.fromPage():
        first, last = printer.fromPage(), printer.toPage() or None
    return render(qdoc, page, printer, first, last, opt=opt)
