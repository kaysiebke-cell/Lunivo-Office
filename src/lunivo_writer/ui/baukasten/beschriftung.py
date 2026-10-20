"""Beschriftungen ohne Auszeichnungssprache: Text mit Schrifteigenschaften oder Markdown (`Qt.MarkdownText`)."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

_MD_SONDER = re.compile(r"([\\`*_{}\[\]()#+\-.!|<>~&])")


def md_escape(text: str) -> str:
    """Sonderzeichen eines Textes für Markdown unschädlich machen (z. B. wenn er in `**…**` eingebettet wird)."""
    return _MD_SONDER.sub(r"\\\1", text)


def text_label(text: str, *, fett: bool = False, pt: float | None = None, durchgestrichen: bool = False,
               umbruch: bool = True, auswaehlbar: bool = False) -> QLabel:
    """Beschriftung aus reinem Text; Zeilenumbrüche des Textes bleiben erhalten."""
    l = QLabel(text)
    l.setTextFormat(Qt.PlainText)
    l.setWordWrap(umbruch)
    f = l.font()
    f.setBold(fett); f.setStrikeOut(durchgestrichen)
    if pt:
        f.setPointSizeF(pt)
    l.setFont(f)
    if auswaehlbar:
        l.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return l


def md_label(markdown: str, *, umbruch: bool = True) -> QLabel:
    """Beschriftung aus Markdown (fett, durchgestrichen, Absätze) — Qt zeigt es selbst an."""
    l = QLabel(markdown)
    l.setTextFormat(Qt.MarkdownText)
    l.setWordWrap(umbruch)
    return l
