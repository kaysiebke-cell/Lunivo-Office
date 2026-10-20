"""Hilfe: Handbuch, Tastenkürzel, Erweiterungen."""
from __future__ import annotations

import os
from lunivo_writer.core import paths

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout

from lunivo_writer.ui import kuerzel




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
    with open(os.path.join(paths.RESSOURCEN, "handbuch.md"), encoding="utf-8") as fh:
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
    b.setMarkdown(kuerzel.als_markdown())
    bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(d.reject); v.addWidget(bb)
    return d


def erweiterungen(parent) -> QDialog:
    from lunivo_writer.services.integrations import languagetool, libreoffice, wps
    from lunivo_writer.services import vorlesen
    from lunivo_writer.services.settings_service import data_dir
    d, b, v = _browser(parent, "Erweiterungen", 720, 640)

    def zeile(name, ok, wo, wie):
        return f"| **{name}** | {'✅ ' + wo if ok else '⬜ nicht eingerichtet'} | {wie} |\n"
    lo = libreoffice.finde_soffice()
    text = "## Angebundene Programme\n\n| Programm | Stand | Wie |\n|---|---|---|\n"
    text += zeile("LibreOffice", bool(lo), f"`{lo}`" if lo else "", "ODT/DOC/RTF-Umwandlung: `sudo apt install libreoffice-writer`")
    text += zeile("LanguageTool", languagetool.verfuegbar(), "bereit", "gründliche Prüfung (Java): in INSTALLATION.md beschrieben")
    text += zeile("Sprachausgabe", bool(vorlesen.piper_da() or vorlesen.spd_da()),
                  "Piper" if vorlesen.piper_da() else "speech-dispatcher", "`sudo apt install speech-dispatcher`")
    try:
        text += zeile("WPS Office", bool(wps.finde_wps()), f"`{wps.finde_wps()}`", "wird nur als installierte Anwendung gestartet, nicht als Bibliothek")
    except Exception:
        pass
    text += f"\nDaten: `{data_dir()}`\n"
    pfad = os.path.join(paths.WURZEL, "docs", "INSTALLATION.md")
    if os.path.exists(pfad):
        text += "\n" + open(pfad, encoding="utf-8").read()
    b.setMarkdown(text)
    bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(d.reject); v.addWidget(bb)
    return d
