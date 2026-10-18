"""Eine Stelle für alle Dateiformate: laden und speichern nach Endung."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from PySide6.QtGui import QFont, QTextBlockFormat, QTextCursor, QTextDocument, QTextDocumentWriter

from ..editor.page import PageSettings
from . import docx_reader, docx_writer
from .report import DocumentIOError, IOReport

OPEN_FILTER = ("Dokumente (*.docx *.odt *.doc *.rtf *.txt);;Word-Dokument (*.docx);;OpenDocument-Text (*.odt);;"
               "Word 97–2003 (*.doc);;Rich Text (*.rtf);;Textdatei (*.txt);;Alle Dateien (*)")
LIBREOFFICE_FORMATE = (".odt", ".doc", ".rtf", ".dot", ".dotx", ".docm", ".wps", ".fodt")
SAVE_FILTERS = {
    ".docx": "Word-Dokument (*.docx)",
    ".txt": "Textdatei (*.txt)",
    ".odt": "OpenDocument-Text (*.odt)",
    ".doc": "Word 97–2003 (*.doc)",
    ".rtf": "Rich Text (*.rtf)",
    ".html": "Webseite (*.html)",
}
WEB_CODIERUNGEN = ["UTF-8", "ISO-8859-1", "ISO-8859-15", "Windows-1252", "UTF-16"]


@dataclass
class Loaded:
    doc: QTextDocument
    page: PageSettings
    meta: dict
    report: IOReport


def ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def _verschluesselt(path: str) -> bool:
    try:
        with open(path, "rb") as fh:
            return fh.read(4) == b"\xd0\xcf\x11\xe0"
    except OSError:
        return False


def _entschluesseln(path: str, kennwort: str | None, ziel: str) -> None:
    from .report import PasswortNoetig
    if not kennwort:
        raise PasswortNoetig()
    try:
        import msoffcrypto
    except ImportError as ex:
        raise DocumentIOError("Zum Öffnen kennwortgeschützter Dokumente wird das Paket „msoffcrypto-tool“ gebraucht "
                              "(pip install msoffcrypto-tool).") from ex
    try:
        with open(path, "rb") as fh, open(ziel, "wb") as out:
            f = msoffcrypto.OfficeFile(fh)
            f.load_key(password=kennwort)
            f.decrypt(out)
    except Exception as ex:                      # falsches Kennwort oder beschädigt
        raise PasswortNoetig(falsch=True) from ex


def load(path: str, kennwort: str | None = None) -> Loaded:
    if not os.path.isfile(path):
        raise DocumentIOError(f"Die Datei „{path}“ existiert nicht.")
    e = ext(path)
    if e == ".docx":
        if _verschluesselt(path):
            with tempfile.TemporaryDirectory(prefix="lunivo-") as tmp:
                klar = os.path.join(tmp, "klar.docx")
                _entschluesseln(path, kennwort, klar)
                doc, page, meta, rep = docx_reader.read_docx(klar)
            meta["kennwort"] = kennwort
            return Loaded(doc, page, meta, rep)
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
    if e in LIBREOFFICE_FORMATE:
        _kopf_pruefen(path, e)
        from ..integrations import libreoffice
        docx_pfad, tmp = libreoffice.in_docx(path)
        try:
            doc, page, meta, rep = docx_reader.read_docx(docx_pfad)
        finally:
            tmp.cleanup()
        rep.warn(f"„{os.path.basename(path)}“ wurde über LibreOffice nach DOCX umgewandelt und dann gelesen; "
                 "beim Speichern als DOCX gilt das umgewandelte Format.")
        return Loaded(doc, page, meta, rep)
    raise DocumentIOError(
        f"Das Format „{e or 'ohne Endung'}“ kann nicht geöffnet werden. Unterstützt: DOCX, ODT, DOC, RTF, TXT.")


_MAGIC = {".odt": b"PK", ".dotx": b"PK", ".docm": b"PK", ".fodt": b"<?xml", ".doc": b"\xd0\xcf\x11\xe0",
          ".dot": b"\xd0\xcf\x11\xe0", ".rtf": b"{\\rtf"}


def _kopf_pruefen(path: str, e: str) -> None:
    """LibreOffice öffnet notfalls alles als Text — ein kaputtes Dokument soll aber als kaputt gemeldet werden."""
    soll = _MAGIC.get(e)
    if not soll:
        return
    try:
        with open(path, "rb") as fh:
            kopf = fh.read(len(soll))
    except OSError as ex:
        raise DocumentIOError(f"Datei nicht lesbar: {ex.strerror or ex}") from ex
    if kopf != soll:
        raise DocumentIOError(f"Die Datei ist kein gültiges {e[1:].upper()}-Dokument oder beschädigt.")


def _has_rich_content(doc: QTextDocument) -> bool:
    b = doc.firstBlock()
    while b.isValid():
        if b.textList() is not None or b.blockFormat().headingLevel():
            return True
        it = b.begin()
        while not it.atEnd():
            cf = it.fragment().charFormat()
            if cf.isImageFormat() or cf.fontWeight() > 400 or cf.fontItalic() or cf.underlineStyle() != cf.UnderlineStyle.NoUnderline:
                return True
            it += 1
        b = b.next()
    return doc.rootFrame().childFrames() != []


def save(path: str, doc: QTextDocument, page: PageSettings, meta: dict | None = None) -> IOReport:
    e = ext(path)
    if e == ".docx":
        kw = (meta or {}).get("kennwort")
        if not kw:
            return docx_writer.write_docx(path, doc, page, meta)
        try:
            import msoffcrypto
        except ImportError as ex:
            raise DocumentIOError("Zum Verschlüsseln wird das Paket „msoffcrypto-tool“ gebraucht.") from ex
        with tempfile.TemporaryDirectory(prefix="lunivo-") as tmp:
            klar = os.path.join(tmp, "klar.docx")
            rep = docx_writer.write_docx(klar, doc, page, meta)
            enc = os.path.join(tmp, "enc.docx")
            with open(klar, "rb") as fh, open(enc, "wb") as out:
                msoffcrypto.OfficeFile(fh).encrypt(kw, out)
            with open(enc, "rb") as fh:
                _atomic_write(path, fh.read())
        return rep
    rep = IOReport()
    if e == ".txt":
        if _has_rich_content(doc):
            rep.warn("Als Textdatei gehen Formatierung, Listen, Tabellen und Bilder verloren.")
        if not page.header.is_empty() or not page.footer.is_empty():
            rep.warn("Kopf- und Fußzeile werden in der Textdatei nicht gespeichert.")
        _atomic_write(path, doc.toPlainText().replace(" ", "\n").encode("utf-8"))
        return rep
    if e in (".html", ".htm"):
        cod = (meta or {}).get("codierung") or "UTF-8"
        try:
            "".encode(cod)
        except LookupError:
            raise DocumentIOError(f"Die Codierung „{cod}“ ist unbekannt.")
        html = doc.toHtml()
        if "<head>" in html:
            html = html.replace("<head>", f'<head><meta charset="{cod}">', 1)
        rep.warn("Als Webseite gehen Seitenränder, Kopf-/Fußzeile und Seitenumbrüche verloren.")
        try:
            data = html.encode(cod)
        except UnicodeEncodeError:
            raise DocumentIOError(f"Der Text enthält Zeichen, die in {cod} nicht darstellbar sind. Bitte UTF-8 wählen.")
        _atomic_write(path, data)
        return rep
    if e in (".odt", ".doc", ".rtf"):
        from ..integrations import libreoffice
        if libreoffice.verfuegbar():
            with tempfile.TemporaryDirectory(prefix="lunivo-") as tmp:
                zwischen = os.path.join(tmp, "dokument.docx")
                docx_writer.write_docx(zwischen, doc, page, meta)
                libreoffice.aus_docx(zwischen, path)
            rep.warn(f"{e[1:].upper()} wurde über LibreOffice aus der DOCX-Fassung erzeugt. "
                     "Die Treue zum Original hängt von LibreOffice ab.")
            return rep
        if e != ".odt":
            raise DocumentIOError(f"{e[1:].upper()} braucht LibreOffice zum Umwandeln; es ist nicht installiert.")
        rep.warn("ODT wurde ohne LibreOffice über Qt geschrieben (Text, Formatierung, Tabellen, Bilder). "
                 "Seitenrand, Kopf- und Fußzeile sind darin nicht enthalten.")
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
