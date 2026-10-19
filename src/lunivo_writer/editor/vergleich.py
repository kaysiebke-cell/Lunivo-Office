"""Dokumente vergleichen und zusammenführen — das Ergebnis sind verfolgte Änderungen (einfügen/löschen, mit Autor und Datum).

Vergleichen: Das Ausgangsdokument bleibt als Text und Formatierung erhalten; was das andere Dokument anders hat, steht als verfolgte
Änderung darin. Es wird nach Absätzen ausgerichtet und in ähnlichen Absätzen wortweise verglichen.
Zusammenführen: mehrere überarbeitete Fassungen desselben Ausgangsdokuments mit je eigenem Autor in einem Dokument; überschneiden sich
zwei Löschungen/Ersetzungen verschiedener Autoren, gilt die erste, die andere wird als Konflikt gemeldet.

Grenzen: Es werden Text und Absätze verglichen, keine Formatänderungen und keine Tabellenstruktur (Zellentext wie Absätze); ein
zusammengeführter Absatz erscheint als gelöscht + neu. Bereits verfolgte Änderungen im Ausgangsdokument bleiben unberührt."""
from __future__ import annotations

import difflib
import re
from datetime import datetime

from PySide6.QtGui import QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment

from lunivo_writer.editor.zusatz import P_AENDERUNG, P_AUTOR, P_DATUM

TOKEN = re.compile(r"\s+|\w+|[^\w\s]", re.UNICODE)
AEHNLICH = 0.4


def _absaetze(doc: QTextDocument) -> list:
    out, b = [], doc.firstBlock()
    while b.isValid():
        out.append(b)
        b = b.next()
    return out


def ops_bestimmen(basis: QTextDocument, andere: QTextDocument, autor: str) -> list[dict]:
    """Änderungen von `basis` nach `andere` als Operationen auf den Absätzen von `basis`."""
    a, b = _absaetze(basis), _absaetze(andere)
    ta, tb = [x.text() for x in a], [x.text() for x in b]
    ops: list[dict] = []

    def loeschen(i):
        if ta[i]:
            ops.append({"art": "del", "absatz": i, "von": 0, "bis": len(ta[i]), "autor": autor})
        else:
            ops.append({"art": "delleer", "absatz": i, "von": 0, "bis": 0, "autor": autor})

    def einfuegen_vor(i, j):
        ops.append({"art": "insblock", "absatz": i, "von": -1, "bis": -1, "autor": autor, "quelle": b[j]})

    def wortweise(i, j):
        wa, wb = TOKEN.findall(ta[i]), TOKEN.findall(tb[j])
        pos = [0]
        for w in wa:
            pos.append(pos[-1] + len(w))
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            g = (autor, i, i1) if tag == "replace" else None              # eine Ersetzung gilt ganz oder gar nicht
            if tag in ("delete", "replace"):
                ops.append({"art": "del", "absatz": i, "von": pos[i1], "bis": pos[i2], "autor": autor, "gruppe": g})
            if tag in ("insert", "replace"):
                ops.append({"art": "ins", "absatz": i, "von": pos[i2], "bis": pos[i2], "text": "".join(wb[j1:j2]), "autor": autor, "gruppe": g})

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            for i in range(i1, i2):
                loeschen(i)
        elif tag == "insert":
            for j in range(j1, j2):
                einfuegen_vor(i1, j)
        else:                                                            # replace: Absätze paarweise wortweise, Reste ganz
            n = min(i2 - i1, j2 - j1)
            for k in range(n):
                i, j = i1 + k, j1 + k
                if difflib.SequenceMatcher(None, ta[i], tb[j], autojunk=False).ratio() >= AEHNLICH:
                    wortweise(i, j)
                else:
                    loeschen(i)
                    einfuegen_vor(i + 1, j)
            for i in range(i1 + n, i2):
                loeschen(i)
            for j in range(j1 + n, j2):
                einfuegen_vor(i2, j)
    return ops


def _bereich(op: dict, ta_len: dict) -> tuple[int, int]:
    return (0, 10 ** 9) if op["art"] in ("delleer",) else (op["von"], op["bis"])


def zusammenlegen(listen: list[list[dict]]) -> tuple[list[dict], list[str]]:
    """Operationen mehrerer Autoren vereinen; überschneidende Löschungen verschiedener Autoren → die erste gilt, die andere ist Konflikt."""
    ops: list[dict] = []
    konflikte: list[str] = []
    verworfen: set = set()
    for liste in listen:
        for op in liste:
            if op.get("gruppe") is not None and op["gruppe"] in verworfen:
                continue
            if op["art"] in ("del", "delleer"):
                v, b = _bereich(op, {})
                clash = next((o for o in ops if o["art"] in ("del", "delleer") and o["absatz"] == op["absatz"] and o["autor"] != op["autor"]
                              and v < max(_bereich(o, {})[1], _bereich(o, {})[0] + 1) and _bereich(o, {})[0] < max(b, v + 1)), None)
                if clash:
                    konflikte.append(f"Absatz {op['absatz'] + 1}: Änderung von {op['autor']} überschneidet sich mit der von {clash['autor']} — es gilt {clash['autor']}.")
                    if op.get("gruppe") is not None:
                        verworfen.add(op["gruppe"])
                    continue
            ops.append(op)
    return ops, konflikte


def _jetzt() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _markieren(doc: QTextDocument, von: int, bis: int, art: str, autor: str, datum: str) -> None:
    c = QTextCursor(doc)
    c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
    f = QTextCharFormat()
    f.setProperty(P_AENDERUNG, art); f.setProperty(P_AUTOR, autor); f.setProperty(P_DATUM, datum)
    c.mergeCharFormat(f)


def anwenden(ziel: QTextDocument, ops: list[dict], datum: str | None = None) -> dict:
    """Operationen als verfolgte Änderungen in `ziel` schreiben (von hinten nach vorn, damit die Stellen stimmen)."""
    datum = datum or _jetzt()
    stat = {"eingefuegt": 0, "geloescht": 0}
    from lunivo_writer.editor.sendungen import _ressourcen

    def schluessel(op):
        return (op["absatz"], op["von"], 1 if op["art"] == "ins" else 0)

    for op in sorted(ops, key=schluessel, reverse=True):
        blk = ziel.findBlockByNumber(op["absatz"]) if op["absatz"] < ziel.blockCount() else None
        if op["art"] in ("del", "delleer"):
            if op["art"] == "del" and blk is not None:
                p = blk.position()
                bereich_frei = []                                 # bereits verfolgte Zeichen nicht überschreiben
                c = QTextCursor(ziel)
                for k in range(op["von"], op["bis"]):
                    c.setPosition(p + k + 1)
                    if not c.charFormat().hasProperty(P_AENDERUNG):
                        if bereich_frei and bereich_frei[-1][1] == p + k:
                            bereich_frei[-1][1] = p + k + 1
                        else:
                            bereich_frei.append([p + k, p + k + 1])
                for v, b in bereich_frei:
                    _markieren(ziel, v, b, "del", op["autor"], datum)
                    stat["geloescht"] += b - v
        elif op["art"] == "ins" and blk is not None:
            c = QTextCursor(ziel); c.setPosition(blk.position() + op["von"])
            start = c.position()
            c.insertText(op["text"], c.charFormat() if op["von"] else QTextCharFormat())
            _markieren(ziel, start, start + len(op["text"]), "ins", op["autor"], datum)
            stat["eingefuegt"] += len(op["text"])
        elif op["art"] == "insblock":
            quelle = op["quelle"]
            _ressourcen(quelle.document(), ziel)
            rc = QTextCursor(quelle)
            rc.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            frag = QTextDocumentFragment(rc)
            c = QTextCursor(ziel)
            if blk is not None:
                c.setPosition(blk.position())
                start = c.position()
                c.insertFragment(frag)
                laenge = c.position() - start
                c.insertBlock()
                neu = ziel.findBlock(start)
            else:                                                 # hinter dem letzten Absatz
                c.movePosition(QTextCursor.End)
                c.insertBlock()
                start = c.position()
                c.insertFragment(frag)
                laenge = c.position() - start
                neu = ziel.findBlock(start)
            bc = QTextCursor(neu); bc.setBlockFormat(quelle.blockFormat())
            if laenge:
                _markieren(ziel, start, start + laenge, "ins", op["autor"], datum)
            stat["eingefuegt"] += laenge
    return stat


def vergleichen(basis: QTextDocument, andere: QTextDocument, autor: str = "Vergleich") -> tuple[QTextDocument, dict]:
    ziel = basis.clone()
    ziel.setParent(None)                    # sonst stirbt die Kopie mit dem Ausgangsdokument
    ops = ops_bestimmen(ziel, andere, autor)
    stat = anwenden(ziel, ops)
    stat["operationen"] = len(ops)
    return ziel, stat


def zusammenfuehren(basis: QTextDocument, fassungen: list[tuple[str, QTextDocument]]) -> tuple[QTextDocument, dict, list[str]]:
    ziel = basis.clone()
    ziel.setParent(None)                    # sonst stirbt die Kopie mit dem Ausgangsdokument
    listen = [ops_bestimmen(ziel, doc, autor) for autor, doc in fassungen]
    ops, konflikte = zusammenlegen(listen)
    stat = anwenden(ziel, ops)
    stat["operationen"] = len(ops)
    return ziel, stat, konflikte
