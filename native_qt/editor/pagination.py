"""Seitenaufteilung, PDF-Ausgabe und Drucken mit Kopf-/Fußzeile und Seitenzahlen.

Das Dokument wird bei 96 dpi gesetzt (wie im Editor); beim Ausgeben wird der
Maler auf die Auflösung des Ausgabegeräts hochgerechnet. So stimmt der
Seitenumbruch auf dem Bildschirm mit dem im PDF überein.
"""
from __future__ import annotations

from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import (
    QFont, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextCharFormat, QTextDocument, QTextFormat,
)
from PySide6.QtPrintSupport import QPrinter

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


def bind_layout(qdoc: QTextDocument) -> None:
    qdoc.documentLayout().setPaintDevice(layout_device())


def paginated_copy(qdoc: QTextDocument, page: PageSettings) -> QTextDocument:
    d = qdoc.clone()
    bind_layout(d)
    root = d.rootFrame()
    ff = root.frameFormat()
    ff.setMargin(0)
    root.setFrameFormat(ff)
    d.setDocumentMargin(0)
    d.setPageSize(QSizeF(page.content_width_px, page.content_height_px))
    return d


def page_count(qdoc: QTextDocument, page: PageSettings) -> int:
    return max(1, paginated_copy(qdoc, page).pageCount())


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


def _bf_ohne(bf):
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QBrush
    bf.setBackground(QBrush(_Qt.NoBrush))
    return bf


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
    d = paginated_copy(qdoc, page)
    if opt.get("hintergrund") is False:
        _ohne_hintergruende(d)
    total = max(1, d.pageCount())
    last = total if last is None else min(last, total)
    p = QPainter(device)
    s = (dpi or device.logicalDpiX()) / 96.0
    cw, ch = page.content_width_px, page.content_height_px
    ml, mt = mm_to_px(page.margin_left_mm), mm_to_px(page.margin_top_mm)
    pw, ph = mm_to_px(page.width_mm), mm_to_px(page.height_mm)
    base = qdoc.defaultFont()
    first_page = True
    liste = seiten_liste(total, first, last, opt)
    if opt.get("leere") is False:
        leer = _leere_seiten(d, page, total)
        liste = [n for n in liste if n not in leer] or liste[:1]
    for n in liste:
        if not first_page:
            device.newPage()
        first_page = False
        p.save()
        p.scale(s, s)
        _draw_hf(p, page.header, QRectF(ml, mm_to_px(8), cw, mm_to_px(10)), n, total, base)
        _draw_hf(p, page.footer, QRectF(ml, ph - mm_to_px(18), cw, mm_to_px(10)), n, total, base)
        p.translate(ml, mt)
        p.setClipRect(QRectF(0, 0, cw, ch))
        p.translate(0, -(n - 1) * ch)
        d.drawContents(p, QRectF(0, (n - 1) * ch, cw, ch))
        p.restore()
    p.end()
    return total


def _leere_seiten(d: QTextDocument, page: PageSettings, total: int) -> set[int]:
    ch = page.content_height_px
    mit_text = set()
    b = d.firstBlock()
    lay = d.documentLayout()
    while b.isValid():
        if b.text().strip(chr(0xfffc) + " \t\n") or b.text():
            r = lay.blockBoundingRect(b)
            mit_text.add(int(r.top() // ch) + 1)
        b = b.next()
    return {n for n in range(1, total + 1) if n not in mit_text}


def _page_layout(page: PageSettings) -> QPageLayout:
    size = QPageSize(QSizeF(min(page.width_mm, page.height_mm), max(page.width_mm, page.height_mm)),
                     QPageSize.Millimeter)
    orient = QPageLayout.Landscape if page.landscape else QPageLayout.Portrait
    return QPageLayout(size, orient, QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)


def export_pdf(path: str, qdoc: QTextDocument, page: PageSettings, title: str = "", author: str = "") -> int:
    from PySide6.QtCore import QByteArray
    w = QPdfWriter(path)
    w.setResolution(300)
    w.setPageLayout(_page_layout(page))
    if title:
        w.setTitle(title)
    w.setCreator("Lunivo Writer")
    if author:
        esc = author.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        w.setDocumentXmpMetadata(QByteArray(("<x:xmpmeta xmlns:x=\"adobe:ns:meta/\"><rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">"
                                             "<rdf:Description xmlns:dc=\"http://purl.org/dc/elements/1.1/\"><dc:creator><rdf:Seq><rdf:li>"
                                             + esc + "</rdf:li></rdf:Seq></dc:creator></rdf:Description></rdf:RDF></x:xmpmeta>").encode("utf-8")))
    return render(qdoc, page, w)


def print_document(printer: QPrinter, qdoc: QTextDocument, page: PageSettings, opt: dict | None = None) -> int:
    printer.setPageLayout(_page_layout(page))
    first, last = 1, None
    if printer.printRange() == QPrinter.PageRange and printer.fromPage():
        first, last = printer.fromPage(), printer.toPage() or None
    return render(qdoc, page, printer, first, last, opt=opt)
