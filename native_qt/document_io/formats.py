"""Eine Stelle für alle Dateiformate: laden und speichern nach Endung."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from PySide6.QtGui import QFont, QTextBlockFormat, QTextCursor, QTextDocument, QTextDocumentWriter

from ..editor.page import PageSettings
from . import docx_reader, docx_writer
from .report import DocumentIOError, IOReport

OPEN_FILTER = "Dokumente (*.docx *.txt);;Word-Dokument (*.docx);;Textdatei (*.txt);;Alle Dateien (*)"
SAVE_FILTERS = {
    ".docx": "Word-Dokument (*.docx)",
    ".txt": "Textdatei (*.txt)",
    ".odt": "OpenDocument-Text (*.odt) — nur Export",
}


@dataclass
class Loaded:
    doc: QTextDocument
    page: PageSettings
    meta: dict
    report: IOReport


def ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def load(path: str) -> Loaded:
    if not os.path.isfile(path):
        raise DocumentIOError(f"Die Datei „{path}“ existiert nicht.")
    e = ext(path)
    if e == ".docx":
        doc, page, meta, rep = docx_reader.read_docx(path)
        return Loaded(doc, page, meta, rep)
    if e in (".txt", ".text", ""):
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as ex:
            raise DocumentIOError(f"Datei nicht lesbar: {ex.strerror or ex}") from ex
        for enc in ("utf-8-sig", "cp1252"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = raw.decode("latin-1")
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        f = QFont("Liberation Sans")
        f.setPointSizeF(11)
        doc.setDefaultFont(f)
        QTextCursor(doc).insertText(text.replace("\r\n", "\n"))
        doc.setModified(False)
        return Loaded(doc, PageSettings(), {}, IOReport())
    raise DocumentIOError(
        f"Das Format „{e or 'ohne Endung'}“ kann noch nicht geöffnet werden. "
        "Unterstützt: DOCX, TXT.")


def _has_rich_content(doc: QTextDocument) -> bool:
    b = doc.firstBlock()
    while b.isValid():
        if b.textList() is not None or b.blockFormat().headingLevel():
            return True
        it = b.begin()
        while not it.atEnd():
            cf = it.fragment().charFormat()
            if cf.isImageFormat() or cf.fontWeight() > 400 or cf.fontItalic() or cf.fontUnderline():
                return True
            it += 1
        b = b.next()
    return doc.rootFrame().childFrames() != []


def save(path: str, doc: QTextDocument, page: PageSettings, meta: dict | None = None) -> IOReport:
    e = ext(path)
    if e == ".docx":
        return docx_writer.write_docx(path, doc, page, meta)
    rep = IOReport()
    if e == ".txt":
        if _has_rich_content(doc):
            rep.warn("Als Textdatei gehen Formatierung, Listen, Tabellen und Bilder verloren.")
        if not page.header.is_empty() or not page.footer.is_empty():
            rep.warn("Kopf- und Fußzeile werden in der Textdatei nicht gespeichert.")
        _atomic_write(path, doc.toPlainText().replace(" ", "\n").encode("utf-8"))
        return rep
    if e == ".odt":
        rep.warn("ODT wird exportiert (Text, Formatierung, Tabellen, Bilder). "
                 "Seitenrand, Kopf- und Fußzeile sind darin noch nicht enthalten.")
        w = QTextDocumentWriter(path, b"ODF")
        if not w.write(doc):
            raise DocumentIOError("Die ODT-Datei konnte nicht geschrieben werden.")
        return rep
    raise DocumentIOError(f"Das Format „{e}“ kann nicht gespeichert werden.")


def _atomic_write(path: str, data: bytes) -> None:
    folder = os.path.dirname(os.path.abspath(path))
    try:
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except OSError as ex:
        raise DocumentIOError(f"Speichern nicht möglich: {ex.strerror or ex}") from ex
