"""SmartArt: Listen, Prozesse, Hierarchien, Zyklen und Pyramiden aus einem eingerückten Text.

Das Objekt ist ein Bild mit gespeicherten Daten (P_OBJEKT, art „smartart“): Layout, Text und Farbschema. Es lässt sich jederzeit
umstellen und neu schreiben, auch nach dem Speichern als DOCX und erneutem Öffnen in Lunivo Writer.
Grenze: In DOCX steht es als Bild (Titel „lunivo:…“); Word und LibreOffice zeigen das Bild, bearbeiten es aber nicht als SmartArt."""
from __future__ import annotations

import json
import math

from PySide6.QtCore import QPointF, QRectF, Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPolygonF, QTextCursor, QTextDocument, QTextImageFormat

from lunivo_writer.editor.zusatz import P_OBJEKT

LAYOUTS = ["Liste", "Prozess", "Hierarchie", "Zyklus", "Pyramide"]
FARBEN = {"Blau": ("#2f6fb5", "#5b9bd5", "#a9c9ea"), "Grün": ("#2d8a4e", "#5fb877", "#b4dfc0"), "Orange": ("#e67700", "#f4a259", "#fbd5ae"),
          "Grau": ("#495057", "#868e96", "#ced4da"), "Bunt": ("#2f6fb5", "#e67700", "#2d8a4e")}
MUSTER = {"Liste": "Erster Punkt\nZweiter Punkt\nDritter Punkt", "Prozess": "Planen\nUmsetzen\nPrüfen\nAbschließen",
          "Hierarchie": "Leitung\n  Team A\n    Aufgabe 1\n  Team B", "Zyklus": "Idee\nEntwurf\nTest\nStart", "Pyramide": "Spitze\nMitte\nBasis"}


def punkte(text: str) -> list[tuple[int, str]]:
    """[(Ebene, Text)] — die Ebene ergibt sich aus der Einrückung (je zwei Leerzeichen oder ein Tabulator)."""
    out = []
    for zeile in text.splitlines():
        if not zeile.strip():
            continue
        roh = zeile.replace("\t", "  ")
        out.append(((len(roh) - len(roh.lstrip(" "))) // 2, zeile.strip()))
    return out


def _farbe(daten: dict, ebene: int) -> QColor:
    f = FARBEN.get(daten.get("farben", "Blau"), FARBEN["Blau"])
    return QColor(f[min(ebene, 2)] if daten.get("farben") != "Bunt" else f[ebene % 3])


def _text_farbe(c: QColor) -> QColor:
    return QColor("#ffffff") if c.lightness() < 150 else QColor("#212529")


def _kasten(p: QPainter, r: QRectF, text: str, c: QColor, rund: float = 8) -> None:
    p.setPen(QPen(c.darker(125), 1.5)); p.setBrush(QBrush(c))
    p.drawRoundedRect(r, rund, rund)
    p.setPen(_text_farbe(c))
    f = QFont(p.font()); f.setPointSizeF(11); p.setFont(f)
    p.drawText(r.adjusted(6, 3, -6, -3), Qt.AlignCenter | Qt.TextWordWrap, text)


def _pfeil(p: QPainter, a: QPointF, b: QPointF, c: QColor) -> None:
    p.setPen(QPen(c, 2)); p.drawLine(a, b)
    w = math.atan2(b.y() - a.y(), b.x() - a.x())
    for d in (0.45, -0.45):
        p.drawLine(b, QPointF(b.x() - 9 * math.cos(w - d), b.y() - 9 * math.sin(w - d)))


def zeichnen(daten: dict) -> QImage:
    pts = punkte(daten.get("text", "")) or [(0, "…")]
    layout = daten.get("layout", "Liste")
    breite = 520
    if layout == "Liste":
        h = 16 + len(pts) * 46
        img = QImage(breite, h, QImage.Format_ARGB32); img.fill(Qt.transparent)
        p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
        for i, (e, t) in enumerate(pts):
            _kasten(p, QRectF(8 + e * 36, 8 + i * 46, breite - 16 - e * 36, 38), t, _farbe(daten, e))
    elif layout == "Prozess":
        je_zeile = 4
        zeilen = -(-len(pts) // je_zeile)
        bw = (breite - 16 - (min(len(pts), je_zeile) - 1) * 34) / min(len(pts), je_zeile)
        h = 16 + zeilen * 96
        img = QImage(breite, h, QImage.Format_ARGB32); img.fill(Qt.transparent)
        p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
        for i, (e, t) in enumerate(pts):
            z, s = divmod(i, je_zeile)
            r = QRectF(8 + s * (bw + 34), 8 + z * 96, bw, 80)
            _kasten(p, r, t, _farbe(daten, 0 if daten.get("farben") != "Bunt" else i))
            if i < len(pts) - 1 and s < je_zeile - 1:
                _pfeil(p, QPointF(r.right() + 4, r.center().y()), QPointF(r.right() + 30, r.center().y()), QColor("#868e96"))
    elif layout == "Hierarchie":
        # Blätter nebeneinander, Eltern mittig über ihren Kindern
        baum: list[dict] = []
        stack: list[dict] = []
        for e, t in pts:
            n = {"t": t, "e": e, "k": []}
            while stack and stack[-1]["e"] >= e:
                stack.pop()
            (stack[-1]["k"] if stack else baum).append(n)
            stack.append(n)
        tiefe = max(e for e, _t in pts) + 1
        blaetter = [0]

        def setze(n):
            if not n["k"]:
                n["x"] = blaetter[0]; blaetter[0] += 1
            else:
                for k in n["k"]:
                    setze(k)
                n["x"] = (n["k"][0]["x"] + n["k"][-1]["x"]) / 2
        for w in baum:
            setze(w)
        spalten = max(1, blaetter[0])
        bw = min(130.0, (breite - 16) / spalten - 8)
        h = 16 + tiefe * 78
        img = QImage(breite, h, QImage.Format_ARGB32); img.fill(Qt.transparent)
        p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
        raster = (breite - 16) / spalten

        def mal(n):
            r = QRectF(8 + n["x"] * raster + (raster - bw) / 2, 8 + n["e"] * 78, bw, 50)
            for k in n["k"]:
                kr = QRectF(8 + k["x"] * raster + (raster - bw) / 2, 8 + k["e"] * 78, bw, 50)
                p.setPen(QPen(QColor("#868e96"), 1.5))
                p.drawLine(QPointF(r.center().x(), r.bottom()), QPointF(kr.center().x(), kr.top()))
            _kasten(p, r, n["t"], _farbe(daten, n["e"]))
            for k in n["k"]:
                mal(k)
        for w in baum:
            mal(w)
    elif layout == "Zyklus":
        n = len(pts)
        durchm = 380
        img = QImage(breite, durchm + 16, QImage.Format_ARGB32); img.fill(Qt.transparent)
        p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
        mx, my, rad = breite / 2, (durchm + 16) / 2, (durchm - 90) / 2
        pos = [QPointF(mx + rad * 1.35 * math.cos(-math.pi / 2 + 2 * math.pi * i / n), my + rad * math.sin(-math.pi / 2 + 2 * math.pi * i / n))
               for i in range(n)]
        for i in range(n):
            a, b = pos[i], pos[(i + 1) % n]
            if n > 1:
                w = math.atan2(b.y() - a.y(), b.x() - a.x())
                _pfeil(p, QPointF(a.x() + 62 * math.cos(w), a.y() + 30 * math.sin(w)), QPointF(b.x() - 66 * math.cos(w), b.y() - 33 * math.sin(w)),
                       QColor("#868e96"))
        for i, (e, t) in enumerate(pts):
            _kasten(p, QRectF(pos[i].x() - 56, pos[i].y() - 26, 112, 52), t, _farbe(daten, i if daten.get("farben") == "Bunt" else 0), 26)
    else:                                                                   # Pyramide
        n = len(pts)
        zh = 54
        h = 16 + n * zh
        img = QImage(breite, h, QImage.Format_ARGB32); img.fill(Qt.transparent)
        p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
        mitte = breite / 2
        for i, (e, t) in enumerate(pts):
            oben, unten = 8 + i * zh, 8 + (i + 1) * zh - 4
            bo, bu = (i / n) * (breite - 16) / 2 + 0.0, ((i + 1) / n) * (breite - 16) / 2
            poly = QPolygonF([QPointF(mitte - bo, oben), QPointF(mitte + bo, oben), QPointF(mitte + bu, unten), QPointF(mitte - bu, unten)])
            c = _farbe(daten, i if daten.get("farben") == "Bunt" else min(i, 2))
            p.setPen(QPen(c.darker(125), 1.5)); p.setBrush(QBrush(c)); p.drawPolygon(poly)
            p.setPen(_text_farbe(c)); f = QFont(p.font()); f.setPointSizeF(11); p.setFont(f)
            p.drawText(QRectF(mitte - bu * 0.8, oben, bu * 1.6, unten - oben), Qt.AlignCenter | Qt.TextWordWrap, t)
    p.end()
    return img


def einfuegen(ed, daten: dict) -> None:
    from lunivo_writer.editor import einfuegen as E
    E.qimage_einfuegen(ed, zeichnen(daten), "SmartArt: " + daten.get("layout", "Liste") + " mit " + str(len(punkte(daten.get("text", "")))) + " Punkten",
                       "smartart", daten)


def daten_der_auswahl(ed) -> dict | None:
    f = ed.bild_format()
    if f is None or not f.hasProperty(P_OBJEKT):
        return None
    try:
        o = json.loads(f.property(P_OBJEKT))
    except (ValueError, TypeError):
        return None
    return dict(o.get("daten", {})) if o.get("art") == "smartart" else None


def aendern(ed, **felder) -> bool:
    """Daten des markierten SmartArt-Bildes ändern und neu zeichnen (Breite im Text bleibt, Seitenverhältnis folgt)."""
    c = ed._bild_cursor()
    d = daten_der_auswahl(ed)
    if c is None or d is None:
        return False
    d.update({k: v for k, v in felder.items() if v is not None})
    img = zeichnen(d)
    f = c.charFormat().toImageFormat()
    name = f"obj-{id(img)}-{ed.document().revision()}"
    ed.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
    breite = f.width() or img.width()
    f2 = QTextImageFormat(f)
    f2.setName(name); f2.setWidth(breite); f2.setHeight(breite * img.height() / img.width())
    f2.setProperty(P_OBJEKT, json.dumps({"art": "smartart", "daten": d}, ensure_ascii=False, separators=(",", ":")))
    f2.setProperty(0x100000 + 0x101 + 1, "SmartArt: " + d.get("layout", "Liste") + " mit " + str(len(punkte(d.get("text", "")))) + " Punkten")
    c.setCharFormat(f2)
    ed.document().setModified(True)
    return True
