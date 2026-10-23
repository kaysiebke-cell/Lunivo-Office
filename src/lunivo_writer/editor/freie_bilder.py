"""Frei positionierte Bilder: Bilder, die nicht im Text stehen, sondern an einer Stelle des Blattes (DOCX ``wp:anchor`` ohne Umbruch).

Sie kommen an zwei Orten vor:

* **im Text** — an einem Absatz verankert. Die Angaben stehen als JSON-Liste in der Absatz-Eigenschaft ``B_BILDANKER``
  (sie wandern mit dem Absatz, auch beim Kopieren und in die Kopie fürs Drucken); die Bilddaten liegen als Ressource
  ``frei-<n>`` im Dokument.
* **in Kopf- und Fußzeilen** — ``PageSettings.bilder``; jede Angabe trägt ihr Bild selbst (``bild``) und ``ort``:
  ``kopf`` | ``fuss`` | ``kopf1`` | ``fuss1`` (letztere nur auf der ersten Seite, wenn „Erste Seite anders“ gilt).

Eine Angabe (alle Maße in Bildpunkten, 96 dpi):
``b``, ``h`` Größe · ``bh`` Bezug waagerecht (``seite`` | ``rand`` | ``spalte``), ``xh`` Versatz, ``ah`` Ausrichtung (``left`` | ``center`` ·
``right`` | ``inside`` | ``outside`` oder leer) · ``bv`` Bezug senkrecht (``seite`` | ``rand`` | ``absatz``), ``yv``, ``av`` (``top`` | ``center`` |
``bottom``) · ``hinter`` hinter dem Text · ``ellipse`` Bild in einer Ellipse beschnitten.
Gezeichnet wird in Blattkoordinaten (Ursprung links oben); der Editor, der Druck, das PDF und die Vorschau benutzen dieselben Funktionen.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QRectF, QUrl
from PySide6.QtGui import QImage, QPainter, QPainterPath, QTextDocument

from lunivo_writer.editor.zusatz import B_BILDANKER

from lunivo_writer.core.farben import Farbe
EMU_PX = 9525.0                                              # 1 px bei 96 dpi


def emu_zu_px(emu) -> float:
    try:
        return float(emu) / EMU_PX
    except (TypeError, ValueError):
        return 0.0


# ---- Absatz-Eigenschaft -------------------------------------------------------------------------------------------------
def aus_absatz(bf) -> list[dict]:
    if not bf.hasProperty(B_BILDANKER):
        return []
    try:
        liste = json.loads(bf.stringProperty(B_BILDANKER))
        return [a for a in liste if isinstance(a, dict)]
    except (TypeError, ValueError):
        return []


def an_absatz(cursor, angabe: dict) -> None:
    """Hängt die Angabe an den Absatz des Cursors (mehrere Bilder an einem Absatz sind möglich)."""
    bf = cursor.blockFormat()
    liste = aus_absatz(bf) + [angabe]
    bf.setProperty(B_BILDANKER, json.dumps(liste, separators=(",", ":")))
    cursor.mergeBlockFormat(bf)


def hat_bilder(doc: QTextDocument) -> bool:
    """Gibt es im Text überhaupt einen Absatz mit frei positionierten Bildern? (billig genug für jeden Zeichenvorgang des Editors)"""
    b = doc.firstBlock()
    while b.isValid():
        if b.blockFormat().hasProperty(B_BILDANKER):
            return True
        b = b.next()
    return False


def bild_im_dokument(doc: QTextDocument, name: str) -> QImage | None:
    img = doc.resource(QTextDocument.ImageResource, QUrl(name))
    return img if isinstance(img, QImage) and not img.isNull() else None


def neuer_name(doc: QTextDocument) -> str:
    n = 1
    while doc.resource(QTextDocument.ImageResource, QUrl(f"frei-{n}")) is not None:
        n += 1
    return f"frei-{n}"


# ---- Bilddaten lesen (auch EMF mit eingebettetem Bild) ----------------------------------------------------------------------
def bild_aus_daten(blob: bytes) -> QImage:
    """Ein Bild aus Dateidaten. Qt kennt kein EMF; viele Word-Bilder (eingescannte Unterschriften) sind aber EMF-Hüllen um ein Bitmap
    (Aufzeichnung ``EMR_STRETCHDIBITS``) — das Bitmap wird herausgeholt. Echte Vektorzeichnungen bleiben unlesbar (leeres Bild)."""
    img = QImage()
    if img.loadFromData(blob):
        return img
    import struct
    if len(blob) < 44 or struct.unpack_from("<I", blob, 0)[0] != 1 or blob[40:44] != b" EMF":
        return QImage()
    pos = 0
    while pos + 8 <= len(blob):
        typ, groesse = struct.unpack_from("<II", blob, pos)
        if groesse < 8:
            break
        if typ == 81 and pos + 80 <= len(blob):                      # EMR_STRETCHDIBITS
            off_bmi, cb_bmi, off_bits, cb_bits = struct.unpack_from("<IIII", blob, pos + 48)
            bmi = blob[pos + off_bmi: pos + off_bmi + cb_bmi]
            bits = blob[pos + off_bits: pos + off_bits + cb_bits]
            if bmi and bits:
                kopf = b"BM" + struct.pack("<IHHI", 14 + len(bmi) + len(bits), 0, 0, 14 + len(bmi))
                if img.loadFromData(kopf + bmi + bits, "BMP"):
                    return img
        pos += groesse
    return QImage()


# ---- Zweifarbig („Duoton“) ------------------------------------------------------------------------------------------------
SCHEMA = {"tx1": Farbe.SCHWARZ, "dk1": Farbe.SCHWARZ, "bg1": Farbe.WEISS, "lt1": Farbe.WEISS, "tx2": "#1f497d", "dk2": "#1f497d", "bg2": "#eeece1",
          "lt2": "#eeece1", "accent1": "#4f81bd", "accent2": "#c0504d", "accent3": "#9bbb59", "accent4": "#8064a2", "accent5": "#4bacc6",
          "accent6": "#f79646"}


def farbe_aus_element(el, ns) -> "QColor":
    """Eine DrawingML-Farbe (srgbClr, prstClr, schemeClr) mit lumMod, lumOff, satMod, tint und shade. ``ns``: Namensräume für XPath."""
    from PySide6.QtGui import QColor
    tag = el.tag.rsplit("}", 1)[-1]
    wert = el.get("val") or ""
    if tag == "srgbClr":
        c = QColor("#" + wert)
    elif tag == "prstClr":
        c = QColor({"black": Farbe.SCHWARZ, "white": Farbe.WEISS}.get(wert, "#808080"))
    else:
        c = QColor(SCHEMA.get(wert, "#808080"))
    for m in el:
        name = m.tag.rsplit("}", 1)[-1]
        try:
            v = int(m.get("val") or 0) / 100000.0
        except ValueError:
            continue
        h, sa, l, al = c.hslHueF(), c.hslSaturationF(), c.lightnessF(), c.alphaF()
        if name == "lumMod":
            l = min(1.0, l * v)
        elif name == "lumOff":
            l = min(1.0, max(0.0, l + v))
        elif name == "satMod":
            sa = min(1.0, sa * v)
        elif name in ("tint", "shade"):
            ziel = 1.0 if name == "tint" else 0.0
            c = QColor.fromRgbF(*[min(1.0, max(0.0, x * v + ziel * (1 - v))) for x in (c.redF(), c.greenF(), c.blueF())])
            continue
        else:
            continue
        c = QColor.fromHslF(max(0.0, h), sa, l, al)
    return c


def duoton(img: QImage, dunkel, hell) -> QImage:
    """Das Bild in zwei Farben: Schwarz wird ``dunkel``, Weiß wird ``hell``, dazwischen Verlauf (DrawingML ``a:duotone``). Durchsicht bleibt."""
    from PySide6.QtGui import QColor, qRgb
    grau = img.convertToFormat(QImage.Format_Grayscale8)
    w, h = grau.width(), grau.height()
    roh = QImage(bytes(grau.constBits()), w, h, grau.bytesPerLine(), QImage.Format_Indexed8).copy()
    tabelle = []
    for i in range(256):
        t = i / 255.0
        tabelle.append(qRgb(round(dunkel.red() + (hell.red() - dunkel.red()) * t), round(dunkel.green() + (hell.green() - dunkel.green()) * t),
                            round(dunkel.blue() + (hell.blue() - dunkel.blue()) * t)))
    roh.setColorTable(tabelle)
    aus = roh.convertToFormat(QImage.Format_ARGB32)
    if img.hasAlphaChannel():
        aus.setAlphaChannel(img.convertToFormat(QImage.Format_ARGB32).getAlphaChannel() if hasattr(QImage, "getAlphaChannel") else
                            img.convertToFormat(QImage.Format_Alpha8))
    return aus


# ---- Lage auf dem Blatt ---------------------------------------------------------------------------------------------------
def rechteck(a: dict, blatt_b: float, blatt_h: float, ml: float, mt: float, inhalt_b: float, inhalt_h: float, absatz_y: float = 0.0,
             spalte_x: float | None = None, seite: int = 1) -> QRectF:
    """Das Rechteck des Bildes auf dem Blatt. ``absatz_y``: oberer Rand des Absatzes (Blattkoordinate), ``spalte_x``: linker Rand der Spalte."""
    b, h = float(a.get("b", 0)), float(a.get("h", 0))
    bezug = a.get("bh", "spalte")
    x0, bw = {"seite": (0.0, blatt_b), "rand": (ml, inhalt_b)}.get(bezug, (ml if spalte_x is None else spalte_x, inhalt_b))
    al = a.get("ah") or ""
    if al in ("inside", "outside"):                          # innen/außen: auf Seiten mit ungerader Nummer links = innen
        al = "left" if (al == "inside") == (seite % 2 == 1) else "right"
    if al == "center":
        x = x0 + (bw - b) / 2
    elif al == "right":
        x = x0 + bw - b
    elif al == "left":
        x = x0
    else:
        x = x0 + float(a.get("xh", 0))
    bezug = a.get("bv", "absatz")
    y0, bh_ = {"seite": (0.0, blatt_h), "rand": (mt, inhalt_h)}.get(bezug, (absatz_y, 0.0))
    av = a.get("av") or ""
    if av == "center":
        y = y0 + (bh_ - h) / 2
    elif av == "bottom":
        y = y0 + bh_ - h
    elif av == "top" and bezug != "absatz":
        y = y0
    else:
        y = y0 + float(a.get("yv", 0))
    return QRectF(x, y, b, h)


def fuell_pinsel(fuell: dict | None, r: QRectF, fuellbild: QImage | None = None):
    """Der Pinsel für die Füllung eines Bildes (hinter durchsichtigen Stellen): ``farbe``, ``verlauf``, ``graduell`` (zwei Farben), ``muster``,
    ``textur`` oder ``bild``. ``None``: keine Füllung."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QBrush, QColor, QLinearGradient
    if not fuell:
        return None
    art = fuell.get("art", "farbe")
    if art == "farbe":
        return QBrush(QColor(fuell["farbe"]))
    if art in ("verlauf", "graduell"):
        dunkel = QColor(fuell["farbe"]) if art == "verlauf" else QColor(fuell.get("dunkel", fuell.get("farbe")))
        hell = QColor(fuell["farbe"]).lighter(160) if art == "verlauf" else QColor(fuell.get("hell", Farbe.WEISS))
        g = QLinearGradient(r.topLeft(), r.bottomLeft()); g.setColorAt(0, hell); g.setColorAt(1, dunkel)
        return QBrush(g)
    if art == "muster":
        from lunivo_writer.editor import muster as M
        return M.pinsel(fuell.get("key", "rein"), fuell.get("farbe", Farbe.SCHWARZ), fuell.get("grund") or Farbe.WEISS)
    if art == "textur":
        from lunivo_writer.ui.baukasten.objekt_menues import _textur
        return QBrush(_textur(fuell.get("key", "papier"), 64))
    if art == "bild" and fuellbild is not None and not fuellbild.isNull():
        return QBrush(fuellbild.scaled(int(max(1, r.width())), int(max(1, r.height()))))
    return QBrush(Qt.NoBrush)


def _stift(rand: dict):
    """Die Kontur eines Bildes als Stift (Stärke in Bildpunkten, Art wie bei den Linien)."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPen
    from lunivo_writer.editor.linie import STILE
    pen = QPen(QColor(rand.get("farbe", Farbe.WEISS)), float(rand.get("b", 1.0)))
    strich = STILE.get(rand.get("art", "einfach"), STILE["einfach"])[1]
    if isinstance(strich, tuple):
        pen.setDashPattern(list(strich))
    else:
        pen.setStyle(strich)
    return pen


def bild_zeichnen(p: QPainter, bild: QImage, r: QRectF, ellipse: bool = False, rand: dict | None = None, dreh: float = 0.0,
                  fuell: dict | None = None, fuellbild: QImage | None = None, fx: dict | None = None) -> None:
    """Bild in ``r``; ``ellipse``: in einer Ellipse beschnitten; ``rand``: {"b": px, "farbe": "#rrggbb", "art": Linienart} eine Linie um die Form;
    ``dreh``: Grad um die Mitte; ``fuell``: Füllung hinter dem Bild (siehe ``fuell_pinsel``)."""
    if bild is None or bild.isNull() or r.width() <= 0 or r.height() <= 0:
        return
    if dreh:                                                       # um die Mitte gedreht
        p.save(); p.translate(r.center()); p.rotate(dreh); p.translate(-r.center())
        bild_zeichnen(p, bild, r, ellipse, rand, 0.0, fuell, fuellbild, fx)
        p.restore()
        return
    if fx:                                                         # Leuchten, Schatten, Reflektion hinter dem Bild; Weiche Kanten am Bild selbst
        from lunivo_writer.editor import bildeffekte as E
        E.unter_zeichnen(p, bild, r, ellipse, fx)
        if fx.get("weich"):
            bild = E.weiche_kanten(bild, r, ellipse, float(fx["weich"].get("radius", 6.0)))
    p.save()
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setRenderHint(QPainter.Antialiasing)
    if ellipse:
        pfad = QPainterPath(); pfad.addEllipse(r)
        p.setClipPath(pfad)
    pinsel = fuell_pinsel(fuell, r, fuellbild)
    if pinsel is not None:
        p.fillRect(r, pinsel)
    p.drawImage(r, bild)
    p.restore()
    if rand:
        from PySide6.QtCore import Qt
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(_stift(rand))
        p.setBrush(Qt.NoBrush)
        k = float(rand.get("b", 1.0)) / 2
        (p.drawEllipse if ellipse else p.drawRect)(r.adjusted(k, k, -k, -k))
        p.restore()


# ---- Alle Bilder eines Blattes -----------------------------------------------------------------------------------------------
def koerper_index(d: QTextDocument, ch: float, ncol: int = 1) -> dict[int, list[tuple[dict, float, int]]]:
    """{Blatt (1-basiert): [(Angabe, y des Absatzes in der Spalte, Spalte)]} für die Bilder im Text. ``d`` ist der Textfluss
    (Spaltenseite = ``ch`` hoch), Absätze ohne Layout werden übersprungen."""
    out: dict[int, list[tuple[dict, float, int]]] = {}
    lay = d.documentLayout()
    b = d.firstBlock()
    while b.isValid():
        liste = aus_absatz(b.blockFormat())
        if liste and b.isVisible():
            r = lay.blockBoundingRect(b)
            oben = r.top()
            la = b.layout()
            if la is not None and la.lineCount():                    # beginnt die erste Zeile erst auf der nächsten Seite, gehört das Bild dorthin
                oben = max(oben, la.position().y() + la.lineAt(0).y())
            lp = max(0, int((oben + 1.0) // ch))
            for i, a in enumerate(liste):
                out.setdefault(lp // max(1, ncol) + 1, []).append((dict(a, _blk=b.blockNumber(), _idx=i), oben - lp * ch, lp % max(1, ncol)))
        b = b.next()
    return out


def objekte_der_seite(page, d: QTextDocument, n: int, index: dict) -> list[tuple[dict, QImage, QRectF]]:
    """Alle frei positionierten Bilder des Blattes ``n`` (1-basiert) mit ihrem Rechteck, in Blattkoordinaten (px)."""
    from lunivo_writer.models.page import mm_to_px
    bw, bh = mm_to_px(page.width_mm), mm_to_px(page.height_mm)
    ml, mt = mm_to_px(page.margin_left_mm), mm_to_px(page.margin_top_mm)
    cw, ch = page.content_width_px, page.content_height_px
    cb = page.spalten_breite_px
    luecke = mm_to_px(page.spalten_abstand_mm)
    liste: list[tuple[dict, QImage, QRectF]] = []
    erste = n == 1 and page.diff_first
    zulaessig = ("kopf1", "fuss1") if erste else ("kopf", "fuss")      # die erste Seite hat bei „Erste Seite anders“ ihre eigene Kopf-/Fußzeile
    for a in getattr(page, "bilder", None) or []:
        if a.get("ort", "kopf") not in zulaessig:
            continue
        bild = a.get("bild")
        if bild is not None:
            liste.append((a, bild, rechteck(a, bw, bh, ml, mt, cw, ch, 0.0, None, n)))
    for a, y, spalte in index.get(n, []):
        bild = bild_im_dokument(d, a.get("n", ""))
        if bild is not None:
            x = ml + spalte * (cb + luecke)
            a = dict(a, _ay=mt + y, _sx=x)
            if (a.get("fuell") or {}).get("art") == "bild":
                a["_fuellbild"] = bild_im_dokument(d, a["fuell"].get("n", ""))                         # Absatz-Oberkante und Spaltenrand merken (zum Verschieben nötig)
            liste.append((a, bild, rechteck(a, bw, bh, ml, mt, cw, ch, mt + y, x, n)))
    return liste


def versatz_fuer(a: dict, r: QRectF, page, n: int) -> dict:
    """Die Angaben ``xh``/``yv`` (ohne Ausrichtung), mit denen das Bild im Rechteck ``r`` steht — zum Verschieben und Verändern der Größe."""
    from lunivo_writer.models.page import mm_to_px
    bw, bh = mm_to_px(page.width_mm), mm_to_px(page.height_mm)
    ml, mt = mm_to_px(page.margin_left_mm), mm_to_px(page.margin_top_mm)
    null = dict(a, ah="", av="", xh=0.0, yv=0.0)
    basis = rechteck(null, bw, bh, ml, mt, page.content_width_px, page.content_height_px, a.get("_ay", 0.0), a.get("_sx"), n)
    return dict(a, ah="", av="", xh=r.x() - basis.x(), yv=r.y() - basis.y(), b=r.width(), h=r.height())


def ohne_hilfsangaben(a: dict) -> dict:
    return {k: v for k, v in a.items() if not k.startswith("_")}


def vorne_hinten(objekte, hinter: bool):
    return [o for o in objekte if bool(o[0].get("hinter")) == hinter]
