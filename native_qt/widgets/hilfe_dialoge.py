"""Hilfe: Handbuch, Tastenkürzel, Erweiterungen."""
from __future__ import annotations

import os

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout

from ..windows import kuerzel

_HIER = os.path.dirname(os.path.abspath(__file__))
_WURZEL = os.path.abspath(os.path.join(_HIER, "..", ".."))


def _browser(parent, titel: str, breite=860, hoehe=640) -> tuple[QDialog, QTextBrowser, QVBoxLayout]:
    d = QDialog(parent)
    d.setWindowTitle(titel)
    d.resize(breite, hoehe)
    v = QVBoxLayout(d)
    b = QTextBrowser()
    b.setOpenExternalLinks(True)
    v.addWidget(b, 1)
    return d, b, v


def handbuch(parent) -> QDialog:
    d, b, v = _browser(parent, "Handbuch")
    with open(os.path.join(_HIER, "..", "resources", "handbuch.md"), encoding="utf-8") as fh:
        b.setMarkdown(fh.read())
    z = QHBoxLayout()
    such = QLineEdit(); such.setPlaceholderText("Im Handbuch suchen …")
    such.returnPressed.connect(lambda: b.find(such.text()) or (b.moveCursor(b.textCursor().Start), b.find(such.text())))
    z.addWidget(such)
    v.addLayout(z)
    bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(d.reject); v.addWidget(bb)
    return d


def tastenkuerzel(parent) -> QDialog:
    d, b, v = _browser(parent, "Tastenkürzel", 520, 640)
    b.setHtml(kuerzel.als_html())
    bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(d.reject); v.addWidget(bb)
    return d


def erweiterungen(parent) -> QDialog:
    from ..integrations import languagetool, libreoffice, wps
    from ..services import vorlesen
    from ..storage.settings import data_dir
    d, b, v = _browser(parent, "Erweiterungen", 720, 640)

    def zeile(name, ok, wo, wie):
        return f"<tr><td><b>{name}</b></td><td>{'✅ ' + wo if ok else '⬜ nicht eingerichtet'}</td><td>{wie}</td></tr>"
    lo = libreoffice.finde_soffice()
    html = "<h2>Angebundene Programme</h2><table cellpadding='4' border='0'>"
    html += zeile("LibreOffice", bool(lo), lo or "", "ODT/DOC/RTF-Umwandlung: <code>sudo apt install libreoffice-writer</code>")
    html += zeile("LanguageTool", languagetool.verfuegbar(), "bereit", "gründliche Prüfung (Java): in INSTALLATION.md beschrieben")
    html += zeile("Sprachausgabe", bool(vorlesen.piper_da() or vorlesen.spd_da()),
                  "Piper" if vorlesen.piper_da() else "speech-dispatcher", "<code>sudo apt install speech-dispatcher</code>")
    try:
        html += zeile("WPS Office", bool(wps.finde_wps()), str(wps.finde_wps()), "wird nur als installierte Anwendung gestartet, nicht als Bibliothek")
    except Exception:
        pass
    html += f"</table><p>Daten: <code>{data_dir()}</code></p>"
    b.setHtml(html)
    pfad = os.path.join(_WURZEL, "doku", "native-qt", "INSTALLATION.md")
    if os.path.exists(pfad):
        from PySide6.QtGui import QTextCursor, QTextDocument, QTextDocumentFragment
        md = QTextDocument()
        md.setMarkdown(open(pfad, encoding="utf-8").read())
        cur = QTextCursor(b.document())
        cur.movePosition(QTextCursor.End)
        cur.insertFragment(QTextDocumentFragment.fromHtml(md.toHtml()))
    bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(d.reject); v.addWidget(bb)
    return d
