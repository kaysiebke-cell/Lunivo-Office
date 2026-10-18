"""Hell/Dunkel über Qt-Paletten (Stil „Fusion“) — keine Stylesheets für das Grundlayout."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


def apply_theme(app: QApplication, mode: str) -> None:
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    if mode == "dark":
        p = QPalette()
        bg, base, txt = QColor(45, 48, 52), QColor(32, 34, 37), QColor(228, 231, 234)
        p.setColor(QPalette.Window, bg); p.setColor(QPalette.WindowText, txt)
        p.setColor(QPalette.Base, base); p.setColor(QPalette.AlternateBase, bg)
        p.setColor(QPalette.Text, txt); p.setColor(QPalette.Button, bg)
        p.setColor(QPalette.ButtonText, txt); p.setColor(QPalette.ToolTipBase, base)
        p.setColor(QPalette.ToolTipText, txt); p.setColor(QPalette.Highlight, QColor(74, 143, 216))
        p.setColor(QPalette.HighlightedText, Qt_white()); p.setColor(QPalette.Mid, QColor(140, 146, 152))
        p.setColor(QPalette.Dark, QColor(24, 26, 28))
        app.setPalette(p)
    elif mode == "light":
        p = QPalette()
        p.setColor(QPalette.Dark, QColor(150, 154, 158))
        app.setPalette(app.style().standardPalette())
        pal = app.palette(); pal.setColor(QPalette.Dark, QColor(150, 154, 158)); app.setPalette(pal)
    else:
        app.setPalette(app.style().standardPalette())


def Qt_white() -> QColor:
    return QColor(255, 255, 255)
