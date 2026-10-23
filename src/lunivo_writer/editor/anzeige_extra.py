"""Anzeige- und Druckhilfen: ausgeblendeter Text, Feldschattierung, Feldcodes, Zeichnungsobjekte, geänderte Zeilen, Objektanker."""
from __future__ import annotations

from PySide6.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextDocument

from lunivo_writer.editor.zusatz import P_AENDERUNG, P_FELD, P_OBJEKT, P_VERSTECKT


# ---- Ausgeblendeter Text ---------------------------------------------------------------------------------------------
from lunivo_writer.core.farben import Farbe
class VersteckterText(QSyntaxHighlighter):
    """Ausgeblendeter Text (Eigenschaft P_VERSTECKT) wird nur in der Anzeige unsichtbar gemacht (winzige, durchsichtige Schrift)
    oder — bei „Ausgeblendeten Text anzeigen“ — grau und gepunktet unterstrichen gezeigt. Der Text selbst bleibt unangetastet."""

    def __init__(self, doc, zeigen: bool = False):
        super().__init__(doc)
        self.zeigen = zeigen

    def setze_zeigen(self, an: bool) -> None:
        if an != self.zeigen:
            self.zeigen = an
            self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        b = self.currentBlock()
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(P_VERSTECKT):
                von = f.position() - b.position()
                fmt = QTextCharFormat()
                if self.zeigen:
                    fmt.setForeground(QBrush(QColor(Farbe.GRAU)))
                    fmt.setUnderlineStyle(QTextCharFormat.DotLine)
                    fmt.setUnderlineColor(QColor(Farbe.GRAU))
                else:
                    fmt.setFontPointSize(0.5)
                    fmt.setForeground(QBrush(QColor(0, 0, 0, 0)))
                    fmt.setFontLetterSpacing(0)
                self.setFormat(von, f.length(), fmt)
            it += 1


def _bereiche(d: QTextDocument, prop: int):
    """[(von, bis, wert)] zusammenhängender Zeichenbereiche mit der Eigenschaft prop."""
    out = []
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().hasProperty(prop):
                v, e = f.position(), f.position() + f.length()
                w = f.charFormat().property(prop)
                if out and out[-1][1] == v and out[-1][2] == w:
                    out[-1] = (out[-1][0], e, w)
                else:
                    out.append((v, e, w))
            it += 1
        b = b.next()
    return out


def versteckte_entfernen(d: QTextDocument) -> int:
    """Löscht den ausgeblendeten Text aus der KOPIE (Druck, PDF, Seitenzählung). → Anzahl gelöschter Bereiche."""
    n = 0
    for von, bis, _w in reversed(_bereiche(d, P_VERSTECKT)):
        c = QTextCursor(d)
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        c.removeSelectedText()
        n += 1
    return n


# ---- Felder ----------------------------------------------------------------------------------------------------------
def feldcodes_einsetzen(d: QTextDocument) -> int:
    """„Feldfunktionen drucken“: an die Stelle des Ergebnisses tritt der Feldcode in geschweiften Klammern."""
    n = 0
    for von, bis, code in reversed(_bereiche(d, P_FELD)):
        c = QTextCursor(d)
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        f = QTextCharFormat(c.charFormat())
        c.insertText("{ " + str(code).strip() + " }", f)
        n += 1
    return n


def feldbereiche(d: QTextDocument) -> list[tuple[int, int]]:
    return [(v, e) for v, e, _w in _bereiche(d, P_FELD)]


# ---- Zeichnungsobjekte -----------------------------------------------------------------------------------------------
def zeichnungen_entfernen(d: QTextDocument) -> int:
    """„Zeichnungsobjekte drucken“ aus: Formen, WordArt, Diagramme und SmartArt (Bilder mit P_OBJEKT) fehlen im Ausdruck."""
    stellen = []
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            cf = f.charFormat() if f.isValid() else None
            if cf is not None and cf.isImageFormat() and cf.hasProperty(P_OBJEKT):
                stellen.append((f.position(), f.length()))
            it += 1
        b = b.next()
    for pos, ln in reversed(stellen):
        c = QTextCursor(d)
        c.setPosition(pos); c.setPosition(pos + ln, QTextCursor.KeepAnchor)
        c.removeSelectedText()
    return len(stellen)


# ---- Geänderte Zeilen ------------------------------------------------------------------------------------------------
def aenderungszeilen(d: QTextDocument) -> list[tuple[float, float]]:
    """Senkrechte Bereiche (oben, unten) in Dokumentkoordinaten aller Zeilen, in denen verfolgte Änderungen stehen."""
    lay = d.documentLayout()
    lay.documentSize()                                  # Layout erzwingen, sonst haben die Zeilen noch keine Position
    zeilen = set()
    for von, bis, _w in _bereiche(d, P_AENDERUNG):
        pos = von
        while pos < bis:
            b = d.findBlock(pos)
            if not b.isValid() or b.layout() is None:
                break
            ln = b.layout().lineForTextPosition(pos - b.position())
            if ln.isValid():
                top = lay.blockBoundingRect(b).top() + ln.y()
                zeilen.add((round(top, 1), round(top + ln.height(), 1)))
                nxt = b.position() + ln.textStart() + ln.textLength()
            else:
                nxt = b.position() + b.length()
            pos = max(nxt, pos + 1)
    return sorted(zeilen)
