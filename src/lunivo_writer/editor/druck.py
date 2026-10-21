"""Drucken nach den Einstellungen des Druckfensters: Seitenauswahl, Blattseiten, mehrere Seiten pro Blatt, anderes Papier.

Ohne Sonderwünsche geht die Ausgabe wie bisher unmittelbar an den Drucker (scharfe Schrift). Sobald mehrere Seiten auf ein Blatt
kommen oder das Papier vom Dokument abweicht, wird eine Zwischen-PDF mit denselben Optionen geschrieben, gerastert und auf das
Blatt gesetzt. Dieselbe Zwischen-PDF liefert die Vorschau im Druckfenster.
"""
from __future__ import annotations

import math
import os
import tempfile

from PySide6.QtCore import QRectF, QSizeF, Qt
from PySide6.QtGui import QImage, QPageLayout, QPageSize, QPainter

PAPIER = {"A3": (297, 420), "A4": (210, 297), "A5": (148, 210), "B5": (176, 250), "Letter": (216, 279), "Legal": (216, 356)}
PRO_BLATT = {1: (1, 1), 2: (2, 1), 4: (2, 2), 6: (3, 2), 9: (3, 3), 16: (4, 4)}


def papier_name(b_mm: float, h_mm: float) -> str:
    """„A4“ für 210 × 297 (mit 2 mm Toleranz, in beiden Lagen), sonst „Benutzerdefiniert“."""
    kurz, lang = sorted((b_mm, h_mm))
    for n, (b, h) in PAPIER.items():
        if abs(kurz - b) <= 2 and abs(lang - h) <= 2:
            return n
    return "Benutzerdefiniert"


def bereich_lesen(text: str, gesamt: int) -> list[int] | None:
    """„1-3, 5“ → [1, 2, 3, 5]. Seiten außerhalb 1..gesamt fallen weg; ungültige Eingabe oder nichts Übriges → None."""
    seiten: list[int] = []
    for teil in text.replace(";", ",").split(","):
        teil = teil.strip()
        if not teil:
            continue
        try:
            if "-" in teil:
                a, _, b = teil.partition("-")
                von, bis = (int(a) if a.strip() else 1), (int(b) if b.strip() else gesamt)
            else:
                von = bis = int(teil)
        except ValueError:
            return None
        if von > bis:
            von, bis = bis, von
        seiten += [n for n in range(max(1, von), min(gesamt, bis) + 1) if n not in seiten]
    return seiten or None


def seiten_nach_wahl(ein: dict, gesamt: int) -> list[int]:
    """Welche Seiten das Druckfenster meint (aufsteigend); ohne gültigen Bereich alle."""
    alle = list(range(1, gesamt + 1))
    if ein.get("bereich") == "seiten":
        alle = bereich_lesen(ein.get("seiten_text", ""), gesamt) or []
        alle.sort()
    wahl = ein.get("blattseiten", "alle")
    if wahl == "vorder":
        alle = [n for n in alle if n % 2 == 1]
    elif wahl == "rueck":
        alle = [n for n in alle if n % 2 == 0]
    return alle


def blatt_zeichnen(p: QPainter, rect: QRectF, bilder: list[QImage], pro_blatt: int, rand: float = 0.0) -> None:
    """Setzt die Seitenbilder in einem Raster auf das Blatt; jedes wird ins eigene Feld eingepasst (Seitenverhältnis bleibt)."""
    sp, ze = PRO_BLATT.get(pro_blatt, (1, 1))
    if rect.width() > rect.height() and pro_blatt in (2, 6):        # Querblatt: Raster drehen
        sp, ze = ze, sp
    zw, zh = rect.width() / sp, rect.height() / ze
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    for i, img in enumerate(bilder[:sp * ze]):
        feld = QRectF(rect.left() + (i % sp) * zw + rand, rect.top() + (i // sp) * zh + rand, zw - 2 * rand, zh - 2 * rand)
        if img.isNull():
            continue
        f = min(feld.width() / img.width(), feld.height() / img.height())
        w, h = img.width() * f, img.height() * f
        p.drawImage(QRectF(feld.center().x() - w / 2, feld.center().y() - h / 2, w, h), img)


def optionen_aus(opt: dict, ein: dict, noten: dict | None = None) -> dict:
    """Die Ausgabeoptionen der Einstellungen, ergänzt um die Wahl im Druckfenster."""
    opt = dict(opt, noten=noten, duplex="alle", hintergrund=ein.get("hintergrund", True), zeichnungen=ein.get("zeichnungen", True),
               leere=ein.get("leere", True), platzhalter=ein.get("platzhalter", False), steuerelemente=ein.get("steuerelemente", True),
               schwarz=ein.get("schwarz", False))
    if ein.get("kommentare") != "blasen":
        opt["blasen"] = None
    return opt


def zwischen_pdf(qdoc, page, opt: dict, noten: dict | None, pfad: str) -> int:
    from lunivo_writer.editor.pagination import export_pdf
    return export_pdf(pfad, qdoc, page, noten=noten, extra=opt)


def pdf_seiten_bilder(pfad: str, breite_px: int, nummern: list[int]) -> list[QImage]:
    """Rastert Seiten (Nummern ab 1 in der Zwischen-PDF) auf die gewünschte Breite."""
    from PySide6.QtCore import QSize
    from PySide6.QtPdf import QPdfDocument
    pdf = QPdfDocument()
    pdf.load(pfad)
    out = []
    for n in nummern:
        if 0 <= n - 1 < pdf.pageCount():
            ps = pdf.pagePointSize(n - 1)
            h = int(breite_px * ps.height() / max(1.0, ps.width()))
            out.append(pdf.render(n - 1, QSize(breite_px, h)))
    pdf.close()
    return out


def vorschau_bild(qdoc, page, opt: dict, noten: dict | None, nummern: list[int], breite_px: int = 640) -> list[QImage]:
    """Die Seiten `nummern` (der Ausgabe, ab 1) so, wie die Optionen sie ausgeben — für die Vorschau."""
    fd, pfad = tempfile.mkstemp(suffix=".pdf", prefix="lunivo-druck-")
    os.close(fd)
    try:
        zwischen_pdf(qdoc, page, dict(opt, nur_seiten=None), noten, pfad)
        return pdf_seiten_bilder(pfad, breite_px, nummern)
    finally:
        try:
            os.remove(pfad)
        except OSError:
            pass


def drucken(printer, qdoc, page, opt: dict, ein: dict, noten: dict | None = None) -> int:
    """Druckt nach den Einstellungen `ein` (Ergebnis des Druckfensters). → Zahl der gedruckten Seiten."""
    from PySide6.QtPrintSupport import QPrinter
    from lunivo_writer.editor.pagination import print_document, seitenzahl
    gesamt = seitenzahl(qdoc, page, noten)
    seiten = seiten_nach_wahl(ein, gesamt)
    if not seiten:
        return 0
    opt = dict(optionen_aus(opt, ein, noten), nur_seiten=set(seiten))
    printer.setCopyCount(max(1, int(ein.get("kopien", 1))))
    printer.setCollateCopies(bool(ein.get("sortieren", True)))
    duplex = {"lang": QPrinter.DuplexLongSide, "kurz": QPrinter.DuplexShortSide}.get(ein.get("beidseitig", "aus"), QPrinter.DuplexNone)
    printer.setDuplex(duplex)
    pro_blatt = int(ein.get("pro_blatt", 1))
    b, h = ein.get("papier_mm") or (page.width_mm, page.height_mm)
    quer = bool(ein.get("quer", page.landscape))
    anders = pro_blatt > 1 or abs(min(b, h) - min(page.width_mm, page.height_mm)) > 1 or quer != bool(page.landscape)
    if not anders:
        printer.setPrintRange(QPrinter.PageRange)
        printer.setFromTo(min(seiten), max(seiten))
        print_document(printer, qdoc, page, opt)
        return len(seiten)
    kurz, lang = sorted((b, h))
    printer.setPageLayout(QPageLayout(QPageSize(QSizeF(kurz, lang), QPageSize.Millimeter),
                                      QPageLayout.Landscape if quer else QPageLayout.Portrait, printer.pageLayout().margins(), QPageLayout.Millimeter))
    fd, pfad = tempfile.mkstemp(suffix=".pdf", prefix="lunivo-druck-")
    os.close(fd)
    try:
        zwischen_pdf(qdoc, page, dict(opt, nur_seiten=set(seiten)), noten, pfad)
        folge = list(range(1, len(seiten) + 1))
        if opt.get("umgekehrt"):
            folge.reverse()
        p = QPainter(printer)
        feld = printer.pageRect(QPrinter.DevicePixel)
        breite = int(feld.width() / max(1, PRO_BLATT.get(pro_blatt, (1, 1))[0]))
        for i in range(0, len(folge), pro_blatt):
            if i:
                printer.newPage()
            blatt_zeichnen(p, QRectF(feld), pdf_seiten_bilder(pfad, breite, folge[i:i + pro_blatt]), pro_blatt, rand=feld.width() * 0.01 if pro_blatt > 1 else 0.0)
        p.end()
    finally:
        try:
            os.remove(pfad)
        except OSError:
            pass
    return math.ceil(len(seiten) / pro_blatt)


class Zwischenseiten:
    """Das Dokument einmal als Zwischen-PDF ausgegeben und geladen; jede Seite lässt sich in beliebiger Größe rastern (Druckvorschau)."""

    def __init__(self, qdoc, page, opt: dict, noten: dict | None = None):
        from PySide6.QtPdf import QPdfDocument
        fd, self._pfad = tempfile.mkstemp(suffix=".pdf", prefix="lunivo-vorschau-")
        os.close(fd)
        zwischen_pdf(qdoc, page, dict(opt, nur_seiten=None), noten, self._pfad)
        self._pdf = QPdfDocument()
        self._pdf.load(self._pfad)

    def anzahl(self) -> int:
        return self._pdf.pageCount()

    def groesse_px(self, n: int, zoom: float = 1.0) -> tuple[int, int]:
        """Größe der Seite n bei 96 dpi mal Zoom."""
        ps = self._pdf.pagePointSize(n - 1)
        return max(1, round(ps.width() * 96 / 72 * zoom)), max(1, round(ps.height() * 96 / 72 * zoom))

    def bild(self, n: int, zoom: float = 1.0) -> QImage:
        from PySide6.QtCore import QSize
        gr = QSize(*self.groesse_px(n, zoom))
        bild = QImage(gr, QImage.Format_RGB32); bild.fill(Qt.white)       # die PDF-Seite ist durchsichtig: aufs weiße Blatt legen
        p = QPainter(bild); p.drawImage(0, 0, self._pdf.render(n - 1, gr)); p.end()
        return bild

    def schliessen(self) -> None:
        self._pdf.close()
        try:
            os.remove(self._pfad)
        except OSError:
            pass
