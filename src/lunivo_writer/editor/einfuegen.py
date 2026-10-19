"""Einfügen: Formen, WordArt, Diagramme, Piktogramme, Formeln, Schnelltabellen, Deckblätter, Text aus Datei.

Formen, WordArt, Diagramme und Piktogramme entstehen als Bild (mit Alternativtext) — sie sind im Dokument nicht
nachträglich als Zeichnung bearbeitbar; in DOCX landen sie als normales Bild.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QUrl
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetricsF, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF,
    QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment, QTextFormat, QTextImageFormat, QTextLength,
    QTextTableFormat,
)

from lunivo_writer.services.docx_reader import STYLE_PROP

FORMEN = ["Rechteck", "Abgerundetes Rechteck", "Ellipse", "Dreieck", "Raute", "Pfeil nach rechts", "Stern", "Sprechblase", "Linie"]


def qimage_einfuegen(ed, img: QImage, alt: str = "", art: str | None = None, daten: dict | None = None) -> None:
    """Bild an der Schreibmarke einfügen. art/daten (Form, WordArt, Diagramm, …) bleiben am Bild, damit es sich wieder bearbeiten
    lässt; „Zeichnungsobjekte drucken“ kann solche Bilder weglassen."""
    name = f"obj-{id(img)}-{ed.document().revision()}"
    ed.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
    w = float(img.width())
    maxw = ed.page.content_width_px
    scale = min(1.0, maxw / w) if w else 1.0
    f = QTextImageFormat()
    f.setName(name); f.setWidth(img.width() * scale); f.setHeight(img.height() * scale)
    if alt:
        f.setProperty(STYLE_PROP + 1, alt)
    if art:
        import json as _json
        from lunivo_writer.editor.zusatz import P_OBJEKT
        f.setProperty(P_OBJEKT, _json.dumps({"art": art, "daten": daten or {}}, ensure_ascii=False, separators=(",", ":")))
    ed.textCursor().insertImage(f)
    ed.document().setModified(True)


def _leer(w: int, h: int) -> QImage:
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    return img


# ---- Formen ---------------------------------------------------------------------------------------------------
def form_bild(art: str, breite: int = 240, hoehe: int = 140, fuell: str = "#4a8fd8", linie: str = "#1f3864",
              strich: float = 2.0, text: str = "") -> QImage:
    img = _leer(breite, hoehe)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(linie)); pen.setWidthF(strich); pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(QColor(fuell)) if fuell else Qt.NoBrush)
    r = QRectF(strich, strich, breite - 2 * strich, hoehe - 2 * strich)
    if art == "Rechteck":
        p.drawRect(r)
    elif art == "Abgerundetes Rechteck":
        p.drawRoundedRect(r, 16, 16)
    elif art == "Ellipse":
        p.drawEllipse(r)
    elif art == "Dreieck":
        p.drawPolygon(QPolygonF([QPointF(r.center().x(), r.top()), QPointF(r.right(), r.bottom()), QPointF(r.left(), r.bottom())]))
    elif art == "Raute":
        p.drawPolygon(QPolygonF([QPointF(r.center().x(), r.top()), QPointF(r.right(), r.center().y()),
                                 QPointF(r.center().x(), r.bottom()), QPointF(r.left(), r.center().y())]))
    elif art == "Pfeil nach rechts":
        h4 = r.height() / 4
        p.drawPolygon(QPolygonF([QPointF(r.left(), r.top() + h4), QPointF(r.right() - r.width() * .3, r.top() + h4),
                                 QPointF(r.right() - r.width() * .3, r.top()), QPointF(r.right(), r.center().y()),
                                 QPointF(r.right() - r.width() * .3, r.bottom()), QPointF(r.right() - r.width() * .3, r.bottom() - h4),
                                 QPointF(r.left(), r.bottom() - h4)]))
    elif art == "Stern":
        c, ra, ri = r.center(), min(r.width(), r.height()) / 2, min(r.width(), r.height()) / 4.6
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = ra if i % 2 == 0 else ri
            pts.append(QPointF(c.x() + rad * math.cos(ang), c.y() + rad * math.sin(ang)))
        p.drawPolygon(QPolygonF(pts))
    elif art == "Sprechblase":
        koerper = QRectF(r.left(), r.top(), r.width(), r.height() * 0.78)
        pfad = QPainterPath()
        pfad.addRoundedRect(koerper, 14, 14)
        spitze = QPainterPath()
        spitze.addPolygon(QPolygonF([QPointF(r.left() + r.width() * .2, koerper.bottom() - 1),
                                     QPointF(r.left() + r.width() * .12, r.bottom()),
                                     QPointF(r.left() + r.width() * .36, koerper.bottom() - 1)]))
        p.drawPath(pfad.united(spitze))
    elif art == "Linie":
        p.drawLine(QPointF(r.left(), r.center().y()), QPointF(r.right(), r.center().y()))
    if text:
        p.setPen(QColor("#ffffff" if QColor(fuell).lightness() < 140 else "#000000"))
        f = p.font(); f.setPointSizeF(12); p.setFont(f)
        p.drawText(r, Qt.AlignCenter | Qt.TextWordWrap, text)
    p.end()
    return img


# ---- WordArt --------------------------------------------------------------------------------------------------------
WORDART_STILE = ["Verlauf", "Schatten", "Umriss", "Regenbogen", "Welle"]


def wordart_bild(text: str, stil: str = "Verlauf", schrift: str = "Liberation Sans", pt: int = 48, farbe: str = "#2f6fb5") -> QImage:
    f = QFont(schrift); f.setPointSizeF(pt); f.setBold(True)
    fm = QFontMetricsF(f)
    b, h = int(fm.horizontalAdvance(text)) + 40, int(fm.height()) + 40
    img = _leer(b, h)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    pfad = QPainterPath()
    pfad.addText(20, 20 + fm.ascent(), f, text)
    if stil == "Welle":
        pfad2 = QPainterPath()
        for poly in pfad.toSubpathPolygons():
            neu = QPolygonF([QPointF(pt_.x(), pt_.y() + math.sin(pt_.x() / 18) * h * 0.08) for pt_ in poly])
            pfad2.addPolygon(neu)
        pfad = pfad2
    if stil == "Schatten":
        p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 90))
        p.translate(4, 4); p.drawPath(pfad); p.translate(-4, -4)
    if stil == "Umriss":
        pen = QPen(QColor(farbe)); pen.setWidthF(2.2); p.setPen(pen); p.setBrush(Qt.NoBrush)
    else:
        p.setPen(Qt.NoPen)
        g = QLinearGradient(0, 0, 0 if stil != "Regenbogen" else b, h if stil != "Regenbogen" else 0)
        if stil == "Regenbogen":
            for i, c in enumerate(("#e03131", "#f08c00", "#ffd43b", "#2f9e44", "#1971c2", "#7048a8")):
                g.setColorAt(i / 5, QColor(c))
        else:
            g.setColorAt(0, QColor(farbe).lighter(150)); g.setColorAt(1, QColor(farbe).darker(150))
        p.setBrush(QBrush(g))
    p.drawPath(pfad)
    p.end()
    return img


# ---- Diagramm --------------------------------------------------------------------------------------------------------
DIAGRAMMARTEN = ["Säulen", "Balken", "Linie", "Kreis"]


def diagramm_bild(art: str, titel: str, kategorien: list[str], reihen: dict[str, list[float]], b: int = 640, h: int = 400) -> QImage:
    from PySide6.QtCharts import (
        QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QHorizontalBarSeries, QLineSeries, QPieSeries, QValueAxis,
    )
    ch = QChart()
    ch.setTitle(titel)
    ch.setAnimationOptions(QChart.NoAnimation)
    if art == "Kreis":
        s = QPieSeries()
        erste = next(iter(reihen.values()), [])
        for k, v in zip(kategorien, erste):
            sl = s.append(f"{k} ({v:g})", float(v))
            sl.setLabelVisible(True)
        ch.addSeries(s)
    elif art in ("Säulen", "Balken"):
        s = QBarSeries() if art == "Säulen" else QHorizontalBarSeries()
        for name, werte in reihen.items():
            bs = QBarSet(name)
            for v in werte:
                bs.append(float(v))
            s.append(bs)
        ch.addSeries(s)
        ax = QBarCategoryAxis(); ax.append(kategorien)
        ay = QValueAxis()
        from PySide6.QtCore import Qt as _Qt
        ch.addAxis(ax, _Qt.AlignBottom if art == "Säulen" else _Qt.AlignLeft)
        ch.addAxis(ay, _Qt.AlignLeft if art == "Säulen" else _Qt.AlignBottom)
        s.attachAxis(ax); s.attachAxis(ay)
    else:
        from PySide6.QtCore import Qt as _Qt
        ax = QBarCategoryAxis(); ax.append(kategorien); ay = QValueAxis()
        ch.addAxis(ax, _Qt.AlignBottom); ch.addAxis(ay, _Qt.AlignLeft)
        for name, werte in reihen.items():
            ls = QLineSeries(); ls.setName(name)
            for i, v in enumerate(werte):
                ls.append(i, float(v))
            ch.addSeries(ls)
            ls.attachAxis(ax); ls.attachAxis(ay)
    ch.legend().setVisible(art != "Kreis" or True)
    view = QChartView(ch)
    view.resize(b, h)
    view.setRenderHint(QPainter.Antialiasing)
    img = QImage(b, h, QImage.Format_ARGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    view.render(p)
    p.end()
    return img


# ---- Piktogramm -------------------------------------------------------------------------------------------------------
def piktogramm_bild(name: str, px: int = 96, farbe: str = "#1f2328") -> QImage:
    from lunivo_writer.ui.widgets import icons
    return icons.katalog_bild(name, px, farbe, 1.7 if px < 128 else 1.5)


# ---- Formel -----------------------------------------------------------------------------------------------------------------
_GRIECH = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "theta": "θ", "lambda": "λ", "mu": "μ",
           "pi": "π", "rho": "ρ", "sigma": "σ", "phi": "φ", "omega": "ω", "Delta": "Δ", "Sigma": "Σ", "Omega": "Ω",
           "infty": "∞", "sum": "∑", "int": "∫", "partial": "∂", "pm": "±", "leq": "≤", "geq": "≥", "neq": "≠", "approx": "≈",
           "times": "×", "cdot": "·", "to": "→", "in": "∈", "forall": "∀", "exists": "∃"}


def formel_teile(text: str) -> list[tuple[str, str]]:
    """Einfache Schreibweise → [(Text, "normal"|"hoch"|"tief")]:  a^2  x_{12}  sqrt(x)  frac(a,b)  \\alpha"""
    import re
    t = re.sub(r"\\([A-Za-z]+)", lambda m: _GRIECH.get(m.group(1), m.group(0)), text)
    t = re.sub(r"sqrt\(([^()]*)\)", r"√(\1)", t)
    t = re.sub(r"frac\(([^(),]*),([^()]*)\)", r"(\1)⁄(\2)", t)
    teile: list[tuple[str, str]] = []
    i = 0
    puffer = ""
    while i < len(t):
        ch = t[i]
        if ch in "^_" and i + 1 < len(t):
            if t[i + 1] == "{":
                j = t.find("}", i + 2)
                j = len(t) if j < 0 else j
                inhalt, naechst = t[i + 2:j], j + 1
            else:
                inhalt, naechst = t[i + 1], i + 2
            if puffer:
                teile.append((puffer, "normal")); puffer = ""
            teile.append((inhalt, "hoch" if ch == "^" else "tief"))
            i = naechst
        else:
            puffer += ch; i += 1
    if puffer:
        teile.append((puffer, "normal"))
    return teile


def formel_einfuegen(ed, text: str) -> None:
    c = ed.textCursor()
    c.beginEditBlock()
    for stueck, art in formel_teile(text):
        f = QTextCharFormat()
        f.setFontFamilies(["DejaVu Serif", "Liberation Serif"]); f.setFontItalic(True)
        if art == "hoch":
            f.setVerticalAlignment(QTextCharFormat.AlignSuperScript)
        elif art == "tief":
            f.setVerticalAlignment(QTextCharFormat.AlignSubScript)
        c.insertText(stueck, f)
    c.insertText(" ", QTextCharFormat())
    c.endEditBlock()
    ed.setTextCursor(c)
    ed.document().setModified(True)


# ---- Schnelltabellen -----------------------------------------------------------------------------------------------------------
def _tabelle(ed, zeilen: list[list[str]], kopf: bool = True, breit: bool = True):
    tf = QTextTableFormat()
    tf.setCellPadding(4); tf.setCellSpacing(0); tf.setBorder(0.5); tf.setBorderCollapse(True)
    tf.setWidth(QTextLength(QTextLength.PercentageLength, 100 if breit else 60))
    if kopf:
        tf.setHeaderRowCount(1)
    c = ed.textCursor()
    t = c.insertTable(len(zeilen), max(len(z) for z in zeilen), tf)
    for r, z in enumerate(zeilen):
        for k, v in enumerate(z):
            cell = t.cellAt(r, k)
            cc = cell.firstCursorPosition()
            f = QTextCharFormat()
            if kopf and r == 0:
                f.setFontWeight(QFont.Bold)
                cf = cell.format()
                cf.setBackground(QBrush(QColor("#e7eef8")))
                cell.setFormat(cf)
            cc.insertText(v, f)
    ed.setTextCursor(t.cellAt(0, 0).firstCursorPosition())
    ed.document().setModified(True)


SCHNELLTABELLEN = ["Tabelle mit Kopfzeile (3 × 4)", "Zwei Spalten", "Kalender (Monat)", "Matrix (3 × 3)", "Zeitplan"]


def schnelltabelle(ed, name: str) -> None:
    if name.startswith("Tabelle mit Kopfzeile"):
        _tabelle(ed, [["Spalte 1", "Spalte 2", "Spalte 3"]] + [["", "", ""] for _ in range(3)])
    elif name == "Zwei Spalten":
        _tabelle(ed, [["Begriff", "Erklärung"]] + [["", ""] for _ in range(4)])
    elif name.startswith("Kalender"):
        import calendar
        import datetime
        h = datetime.date.today()
        tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        zeilen = [tage]
        for woche in calendar.Calendar(0).monthdayscalendar(h.year, h.month):
            zeilen.append([str(d) if d else "" for d in woche])
        _tabelle(ed, zeilen)
    elif name.startswith("Matrix"):
        _tabelle(ed, [["", "A", "B"], ["A", "", ""], ["B", "", ""]], kopf=True)
    else:
        _tabelle(ed, [["Zeit", "Was", "Wer"]] + [["", "", ""] for _ in range(5)])


# ---- Deckblatt ----------------------------------------------------------------------------------------------------------------
DECKBLATT_VORLAGEN = ["Schlicht", "Mit Linie", "Zentriert"]


def deckblatt_einfuegen(ed, vorlage: str, titel: str, untertitel: str, autor: str, datum: str) -> None:
    c = QTextCursor(ed.document())
    c.beginEditBlock()
    c.setPosition(0)
    zentriert = vorlage in ("Zentriert", "Mit Linie")
    teile = [(titel, 30, True, 120), (untertitel, 16, False, 6), ("", 12, False, 160), (autor, 13, False, 4), (datum, 12, False, 4)]
    for text, pt, fett, abstand in teile:
        bf = QTextBlockFormat()
        bf.setTopMargin(abstand)
        bf.setAlignment(Qt.AlignHCenter if zentriert else Qt.AlignLeft)
        cf = QTextCharFormat()
        cf.setFontPointSize(pt); cf.setFontWeight(QFont.Bold if fett else QFont.Normal)
        c.insertBlock(bf, cf)
        c.insertText(text, cf)
        if vorlage == "Mit Linie" and fett:
            bf2 = QTextBlockFormat(); bf2.setAlignment(Qt.AlignHCenter)
            c.insertBlock(bf2, QTextCharFormat()); c.insertText("─" * 24, QTextCharFormat())
    bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
    c.insertBlock(bf, QTextCharFormat())
    c.endEditBlock()
    ed.document().setModified(True)


# ---- Text aus Datei ---------------------------------------------------------------------------------------------------------------
def text_aus_datei(ed, pfad: str):
    from lunivo_writer.services import file_service as formats
    geladen = formats.load(pfad)
    quelle = geladen.doc
    ziel = ed.document()
    # Bilder aus dem fremden Dokument mitnehmen
    b = quelle.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().isImageFormat():
                name = f.charFormat().toImageFormat().name()
                res = quelle.resource(QTextDocument.ImageResource, QUrl(name))
                if res is not None:
                    ziel.addResource(QTextDocument.ImageResource, QUrl(name), res)
            it += 1
        b = b.next()
    c = ed.textCursor()
    c.insertFragment(QTextDocumentFragment(quelle))
    ed.setTextCursor(c)
    ed.document().setModified(True)
    return geladen.report


# ---- Datum und Uhrzeit ----------------------------------------------------------------------------------------------------------------
DATUMSFORMATE = ["dd.MM.yyyy", "d. MMMM yyyy", "dddd, d. MMMM yyyy", "dd.MM.yy", "yyyy-MM-dd", "HH:mm", "HH:mm:ss",
                 "dd.MM.yyyy HH:mm", "d. MMMM yyyy, HH:mm 'Uhr'"]


def datum_text(fmt: str, sprache: str = "de_DE") -> str:
    from PySide6.QtCore import QDateTime, QLocale
    return QLocale(sprache).toString(QDateTime.currentDateTime(), fmt)


# ---- Initiale -------------------------------------------------------------------------------------------------------------------------------
def initiale(ed, zeilen: int = 3) -> bool:
    """Erster Buchstabe des Absatzes groß (Hängende Initiale ist mit Qt nicht möglich — er steht in der Zeile)."""
    c = ed.textCursor()
    c.movePosition(QTextCursor.StartOfBlock)
    if not c.block().text().strip():
        return False
    c.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
    f = QTextCharFormat()
    f.setFontPointSize((ed.document().defaultFont().pointSizeF() or 11) * zeilen * 1.4)
    f.setFontWeight(QFont.Bold)
    c.mergeCharFormat(f)
    ed.document().setModified(True)
    return True


def textfeld(ed, text: str = "Text hier eingeben") -> None:
    """Ein Textfeld als einzellige Tabelle mit Rahmen (frei schwebende Textfelder kennt Qt nicht)."""
    tf = QTextTableFormat()
    tf.setCellPadding(8); tf.setCellSpacing(0); tf.setBorder(1.5); tf.setBorderCollapse(True)
    tf.setWidth(QTextLength(QTextLength.PercentageLength, 50))
    tf.setBorderBrush(QBrush(QColor("#1f3864")))
    t = ed.textCursor().insertTable(1, 1, tf)
    t.cellAt(0, 0).firstCursorPosition().insertText(text)
    ed.setTextCursor(t.cellAt(0, 0).firstCursorPosition())
    ed.document().setModified(True)


# ---- Bild bearbeiten (Farbe, Zuschneiden, Drehen) -----------------------------------------------------------------------
ORIGINAL_PROP = STYLE_PROP + 3            # Name der unveränderten Bild-Ressource


def _bild_cursor(ed):
    c = ed._bild_cursor()
    return c


def bild_ersetzen(ed, wandle) -> bool:
    """wandle(QImage) → QImage; das Bild im Text wird durch das Ergebnis ersetzt (Anzeigebreite bleibt, Seitenverhältnis folgt)."""
    c = ed._bild_cursor()
    if c is None:
        return False
    f = c.charFormat().toImageFormat()
    alt_name = f.name()
    img = ed.document().resource(QTextDocument.ImageResource, QUrl(alt_name))
    img = QImage(img) if img is not None else QImage(alt_name)
    if img.isNull():
        return False
    neu = wandle(img)
    if neu is None or neu.isNull():
        return False
    orig = f.property(ORIGINAL_PROP) if f.hasProperty(ORIGINAL_PROP) else alt_name
    name = f"bild-{id(neu)}-{ed.document().revision()}"
    ed.document().addResource(QTextDocument.ImageResource, QUrl(name), neu)
    faktor = (f.width() / img.width()) if f.width() and img.width() else 1.0
    f.setName(name)
    f.setWidth(neu.width() * faktor); f.setHeight(neu.height() * faktor)
    f.setProperty(ORIGINAL_PROP, orig)
    c.setCharFormat(f)
    ed.document().setModified(True)
    return True


def bild_original(ed) -> bool:
    c = ed._bild_cursor()
    if c is None:
        return False
    f = c.charFormat().toImageFormat()
    if not f.hasProperty(ORIGINAL_PROP):
        return False
    orig = f.property(ORIGINAL_PROP)
    img = ed.document().resource(QTextDocument.ImageResource, QUrl(orig))
    if img is None:
        return False
    img = QImage(img)
    faktor = (f.width() / QImage(ed.document().resource(QTextDocument.ImageResource, QUrl(f.name()))).width()) if f.width() else 1.0
    f.setName(orig); f.setWidth(img.width() * faktor); f.setHeight(img.height() * faktor)
    c.setCharFormat(f)
    ed.document().setModified(True)
    return True


def farbe_anwenden(img: QImage, modus: str) -> QImage:
    if modus in ("Graustufen", "Sepia", "Schwarzweiß"):
        g = img.convertToFormat(QImage.Format_Grayscale8).convertToFormat(QImage.Format_ARGB32)
        if modus == "Sepia":
            p = QPainter(g)
            p.setCompositionMode(QPainter.CompositionMode_Multiply)
            p.fillRect(g.rect(), QColor("#d9b98a"))
            p.end()
            return g
        if modus == "Schwarzweiß":
            return img.convertToFormat(QImage.Format_Mono, Qt.ThresholdDither).convertToFormat(QImage.Format_ARGB32)
        return g
    if modus in ("Heller", "Dunkler"):
        out = img.convertToFormat(QImage.Format_ARGB32)
        p = QPainter(out)
        farbe = QColor(255, 255, 255, 70) if modus == "Heller" else QColor(0, 0, 0, 70)
        p.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        p.fillRect(out.rect(), farbe)
        p.end()
        return out
    return img


def zuschneiden(img: QImage, links: int, oben: int, rechts: int, unten: int) -> QImage:
    r = QRectF(links, oben, img.width() - links - rechts, img.height() - oben - unten).toRect()
    return img.copy(r) if r.width() > 0 and r.height() > 0 else img


def drehen(img: QImage, art: str) -> QImage:
    from PySide6.QtGui import QTransform
    if art == "rechts":
        return img.transformed(QTransform().rotate(90))
    if art == "links":
        return img.transformed(QTransform().rotate(-90))
    if art == "horizontal":
        return img.mirrored(True, False)
    if art == "vertikal":
        return img.mirrored(False, True)
    return img
