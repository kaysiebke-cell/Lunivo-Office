"""Sprechblasen: Kommentare und verfolgte Änderungen als Blasen im Seitenrand, mit Verbindungslinien zum Text.

Einstellungen (Optionen ▸ Änderungen verfolgen ▸ Sprechblasen), gelesen mit `konfig_lesen`:
  verwenden   „Nur für Kommentare“ | „Immer“ (auch Einfügungen/Löschungen) | „Nie“
  breite_mm   bevorzugte Breite;  empfohlen: die empfohlene Breite (60 mm) statt des eigenen Wertes
  rand        „Rechts“ | „Links“;  linien: Verbindungslinien zum Text
  ausrichtung Papierausrichtung beim Drucken mit Sprechblasen: „Automatisch“ | „Beibehalten“ | „Querformat“
Anzeige und Druck benutzen dieselben Zeichenfunktionen.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QTextDocument, QTextOption

from lunivo_writer.editor.zusatz import P_AENDERUNG, P_AUTOR, P_DATUM, P_KOMMENTAR

EMPFOHLENE_BREITE_MM = 60.0
STANDARD = {"verwenden": "Nur für Kommentare", "breite_mm": 60.0, "empfohlen": True, "rand": "Rechts", "linien": True,
            "ausrichtung": "Automatisch"}
VERWENDEN = ["Nur für Kommentare", "Immer", "Nie"]
RAND = ["Rechts", "Links"]
AUSRICHTUNG = ["Automatisch", "Beibehalten", "Querformat"]
LUECKE_MM = 3.0                       # Abstand zwischen Seite und Blasenfläche
AUTOR_FARBEN = ["#c92a2a", "#1971c2", "#2f9e44", "#e8590c", "#7048a8", "#0b7285", "#a61e4d", "#5c940d"]


def konfig_lesen(settings) -> dict:
    k = dict(STANDARD)
    g = lambda n: "sprechblasen/" + n                                      # noqa: E731
    v = settings.get(g("verwenden"), k["verwenden"])
    k["verwenden"] = v if v in VERWENDEN else k["verwenden"]
    try:
        k["breite_mm"] = min(120.0, max(30.0, float(settings.get(g("breite_mm"), k["breite_mm"]))))
    except (TypeError, ValueError):
        pass
    k["empfohlen"] = settings.get_bool(g("empfohlen"), k["empfohlen"])
    r = settings.get(g("rand"), k["rand"])
    k["rand"] = r if r in RAND else k["rand"]
    k["linien"] = settings.get_bool(g("linien"), k["linien"])
    a = settings.get(g("ausrichtung"), k["ausrichtung"])
    k["ausrichtung"] = a if a in AUSRICHTUNG else k["ausrichtung"]
    return k


def breite_mm(k: dict) -> float:
    return EMPFOHLENE_BREITE_MM if k["empfohlen"] else k["breite_mm"]


def aktiv(k: dict) -> bool:
    return k["verwenden"] != "Nie"


@dataclass
class Blase:
    von: int
    bis: int
    autor: str
    datum: str
    art: str                          # „kommentar“ | „ins“ | „del“
    text: str
    farbe: str
    kid: int | None = None


def autor_farbe(autor: str) -> str:
    import hashlib
    return AUTOR_FARBEN[int(hashlib.md5((autor or "?").encode()).hexdigest(), 16) % len(AUTOR_FARBEN)]


def _kuerzen(t: str, n: int = 90) -> str:
    t = " ".join(t.split())
    return t if len(t) <= n else t[: n - 1] + "…"


def sammeln(doc: QTextDocument, kommentare: dict, verwenden: str = "Nur für Kommentare") -> list[Blase]:
    """Alle Blasen des Dokuments in Textreihenfolge."""
    if verwenden == "Nie":
        return []
    kom: dict[int, list[int]] = {}
    aend: list[list] = []                       # [(art, autor, datum), von, bis]
    b = doc.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid():
                cf = f.charFormat()
                v, e = f.position(), f.position() + f.length()
                if cf.hasProperty(P_KOMMENTAR):
                    kid = int(cf.property(P_KOMMENTAR))
                    r = kom.setdefault(kid, [v, e])
                    r[0], r[1] = min(r[0], v), max(r[1], e)
                if verwenden == "Immer" and cf.hasProperty(P_AENDERUNG):
                    schl = (cf.stringProperty(P_AENDERUNG), cf.stringProperty(P_AUTOR), cf.stringProperty(P_DATUM))
                    if aend and aend[-1][0] == schl and aend[-1][2] == v:
                        aend[-1][2] = e
                    else:
                        aend.append([schl, v, e])
            it += 1
        b = b.next()
    text = doc.toPlainText()
    out: list[Blase] = []
    for kid, (v, e) in kom.items():
        k = kommentare.get(kid) or kommentare.get(str(kid)) or {}
        out.append(Blase(v, e, k.get("autor", ""), k.get("datum", ""), "kommentar", k.get("text", ""),
                         autor_farbe(k.get("autor", "")), kid))
    for (art, autor, datum), v, e in aend:
        if art in ("ins", "del"):
            out.append(Blase(v, e, autor, datum, art, ("Eingefügt: " if art == "ins" else "Gelöscht: ") + _kuerzen(text[v:e]),
                             autor_farbe(autor)))
    return sorted(out, key=lambda x: (x.von, x.bis))


def _kopf(bl: Blase) -> str:
    d = (bl.datum or "")[:10]
    return (bl.autor or "Unbekannt") + ((" · " + d) if d else "")


def messen(bl: Blase, breite: float, font: QFont) -> float:
    """Höhe der Blase bei gegebener Breite (alles in Bildpunkten des Zeichengeräts)."""
    kl = QFont(font); kl.setPixelSize(max(6, int(font.pixelSize() * 0.92)))
    fm = QFontMetricsF(font)
    fk = QFontMetricsF(kl)
    innen = max(10.0, breite - 14)
    r = fk.boundingRect(QRectF(0, 0, innen, 10000), int(Qt.TextWordWrap), bl.text or " ")
    return 8 + fm.height() + 3 + r.height() + 8


def stapeln(anker_y: list[float], hoehen: list[float], unten: float, abstand: float = 6.0) -> list[float]:
    """Obere Kanten der Blasen: so nah wie möglich an ihrem Anker, ohne sich zu überlappen (und nicht unter `unten`)."""
    ys: list[float] = []
    cur = -1e9
    for a, h in zip(anker_y, hoehen):
        y = max(a, cur)
        ys.append(y)
        cur = y + h + abstand
    # von unten nach oben zurückschieben, wenn die Spalte über das Seitenende hinausläuft
    ende = unten
    for i in range(len(ys) - 1, -1, -1):
        if ys[i] + hoehen[i] > ende:
            ys[i] = max(0.0, ende - hoehen[i])
        ende = ys[i] - abstand
    return ys


def zeichnen(p: QPainter, bl: Blase, r: QRectF, font: QFont) -> None:
    """Eine Blase zeichnen: Rand und Tönung in der Farbe des Autors, Kopfzeile fett, Text umbrochen."""
    p.save()
    c = QColor(bl.farbe)
    fuell = QColor(c); fuell.setAlpha(28)
    p.setBrush(fuell)
    p.setPen(QPen(c, 1.2))
    p.drawRoundedRect(r, 6, 6)
    fk = QFont(font); fk.setBold(True)
    p.setFont(fk)
    p.setPen(c)
    fm = QFontMetricsF(fk)
    p.drawText(QRectF(r.x() + 7, r.y() + 6, r.width() - 14, fm.height()), int(Qt.AlignLeft | Qt.AlignVCenter), _kopf(bl))
    kl = QFont(font); kl.setPixelSize(max(6, int(font.pixelSize() * 0.92)))
    p.setFont(kl)
    p.setPen(QColor("#222222"))
    opt = QTextOption(); opt.setWrapMode(QTextOption.WordWrap)
    p.drawText(QRectF(r.x() + 7, r.y() + 6 + fm.height() + 3, r.width() - 14, r.height() - fm.height() - 12), bl.text or "", opt)
    p.restore()


def verbindung(p: QPainter, bl: Blase, x_text: float, y_text: float, r: QRectF, rechts: bool) -> None:
    """Linie vom Text zur Blase: waagerecht aus dem Seitenrand, dann zur Mitte der Kopfzeile."""
    p.save()
    p.setPen(QPen(QColor(bl.farbe), 1))
    x_blase = r.left() if rechts else r.right()
    y_blase = r.top() + 12
    xm = x_blase - 10 if rechts else x_blase + 10
    p.drawLine(int(x_text), int(y_text), int(xm), int(y_text))
    p.drawLine(int(xm), int(y_text), int(x_blase), int(y_blase))
    p.restore()
