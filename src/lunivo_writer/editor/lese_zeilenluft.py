"""Zeilenluft der Lesehilfe: mehr Platz zwischen den Zeilen — nur in der Anzeige beim Bearbeiten, nie im Dokument.

Qt kennt den Zeilenabstand nur als Format des Absatzes. Darum bekommt jeder Absatz beim Bearbeiten den größeren Abstand und merkt sich seinen eigenen Wert
(``B_LUFT``). Gespeichert, gedruckt und als PDF ausgegeben wird immer ohne: ``bereinigte_kopie`` und ``zuruecknehmen`` stellen die Originalwerte her.
Beim Umstellen wird der Rückgängig-Verlauf des Dokuments geleert (Qt kann Formatänderungen sonst nicht am Verlauf vorbei setzen)."""
from __future__ import annotations

from PySide6.QtGui import QTextBlockFormat, QTextCursor, QTextDocument, QTextFormat

B_LUFT = QTextFormat.UserProperty + 49          # am Absatz: der ursprüngliche Zeilenabstand als „Art:Wert“
_EINZELN, _PROP = 0, 1                       # SingleHeight, ProportionalHeight (Qt verlangt hier Zahlen)


def _markiert(bf: QTextBlockFormat) -> bool:
    return bf.hasProperty(B_LUFT)


def aktiv(doc: QTextDocument) -> bool:
    """Trägt ein Absatz des Dokuments noch den Zusatzabstand der Lesehilfe?"""
    b = doc.firstBlock()
    while b.isValid():
        if _markiert(b.blockFormat()):
            return True
        b = b.next()
    return False


def _zuruecksetzen(bf: QTextBlockFormat) -> QTextBlockFormat:
    art, _, wert = str(bf.property(B_LUFT)).partition(":")
    bf.clearProperty(B_LUFT)
    bf.setLineHeight(float(wert), int(art))
    return bf


def _durchlaufen(doc: QTextDocument, aendern) -> int:
    n = 0
    c = QTextCursor(doc)
    c.beginEditBlock()
    b = doc.firstBlock()
    while b.isValid():
        neu = aendern(b.blockFormat())
        if neu is not None:
            QTextCursor(b).setBlockFormat(neu)
            n += 1
        b = b.next()
    c.endEditBlock()
    return n


def zuruecknehmen(doc: QTextDocument) -> int:
    """Jedem Absatz den ursprünglichen Zeilenabstand zurückgeben (ohne Rückgängig-Schritt, wenn das Dokument sonst nichts mehr davon weiß)."""
    return _durchlaufen(doc, lambda bf: _zuruecksetzen(bf) if _markiert(bf) else None)


def bereinigte_kopie(doc: QTextDocument) -> QTextDocument:
    """Eine Kopie ohne den Zusatzabstand zum Speichern oder Ausgeben; das bearbeitete Dokument bleibt unberührt."""
    d = doc.clone()
    zuruecknehmen(d)
    return d


def anwenden(doc: QTextDocument, faktor: float) -> None:
    """Zeilenluft ``faktor`` (1,0 = normal) für alle Absätze setzen; vorherige Werte werden zuerst zurückgenommen. Ändert nichts, wenn nichts zu tun ist."""
    faktor = max(1.0, float(faktor))
    if faktor == 1.0 and not aktiv(doc):
        return
    war_geaendert = doc.isModified()
    doc.setUndoRedoEnabled(False)                       # leert den Verlauf: die Änderung gehört nicht dazu
    try:
        zuruecknehmen(doc)
        if faktor > 1.0:
            def mehr(bf: QTextBlockFormat):
                art = bf.lineHeightType()
                if art not in (_EINZELN, _PROP):           # feste, Mindest- und Abstandshöhen bleiben, wie sie sind
                    return None
                basis = bf.lineHeight() if art == _PROP and bf.lineHeight() > 0 else 100.0
                bf.setProperty(B_LUFT, f"{art}:{bf.lineHeight()}")
                bf.setLineHeight(basis * faktor, _PROP)
                return bf
            _durchlaufen(doc, mehr)
    finally:
        doc.setUndoRedoEnabled(True)
        doc.setModified(war_geaendert)
