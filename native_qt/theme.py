"""Hell/Dunkel über Qt-Paletten (Stil „Fusion“) — keine Stylesheets für das Grundlayout."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


def apply_theme(app: QApplication, mode: str) -> None:
    _setze(app, mode)
    # Stylesheets mit palette(...) werden sonst nicht neu ausgewertet
    for w in app.allWidgets():
        ss = w.styleSheet()
        if ss and "palette(" in ss:
            w.setStyleSheet("")
            w.setStyleSheet(ss)


def _setze(app: QApplication, mode: str) -> None:
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
        p.setColor(QPalette.Light, QColor(70, 74, 80)); p.setColor(QPalette.Midlight, QColor(58, 62, 67))
        p.setColor(QPalette.Link, QColor(110, 168, 230)); p.setColor(QPalette.LinkVisited, QColor(170, 140, 220))
        p.setColor(QPalette.BrightText, QColor(255, 255, 255))
        p.setColor(QPalette.PlaceholderText, QColor(150, 156, 162))
        grau = QColor(125, 130, 136)
        for rolle in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            p.setColor(QPalette.Disabled, rolle, grau)
        p.setColor(QPalette.Disabled, QPalette.Base, QColor(40, 43, 47))
        p.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 86, 94))
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
