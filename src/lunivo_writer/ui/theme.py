"""Hell/Dunkel über Qt-Paletten (Stil „Fusion“) — keine Stylesheets für das Grundlayout."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


def apply_theme(app: QApplication, mode: str) -> None:
    _setze(app, mode)
    _stil(app)
    # Stylesheets mit palette(...) werden sonst nicht neu ausgewertet
    for w in app.allWidgets():
        ss = w.styleSheet()
        if ss and "palette(" in ss:
            w.setStyleSheet("")
            w.setStyleSheet(ss)


def _ist_dunkel(app: QApplication) -> bool:
    return app.palette().color(QPalette.Window).lightness() < 128


FARBEN = {
    False: dict(bg="#f3f4f6", flaeche="#ffffff", karte="#ffffff", tafel="#f3f4f6", feld="#ffffff", dokleiste="#f3f4f6", rand="#d9dde3",
                text="#1f2328", text2="#59616b", hover="#e6eaf0", akzent="#2f6fb5", weich="#d8e6f7", grau="#8a929c", griff="#c3c9d1",
                griff_h="#a9b1bb"),
    # Dunkel wie in der ersten Fassung (aus deinem Bildschirmfoto gemessen): Leisten und Band #2A2E32, Seitenleisten #26292D,
    # Knöpfe und Menüs #2F3338, Eingabefelder und Dokument-Reiterzeile wie die Fläche um das Blatt #1F2225, Ränder #3A3F45,
    # Schrift #E6E9EC, Nebenschrift #A7AFB7, Deaktiviertes #7C858E
    True: dict(bg="#2a2e32", flaeche="#2a2e32", karte="#2f3338", tafel="#26292d", feld="#1f2225", dokleiste="#1f2225", rand="#3a3f45",
               text="#e6e9ec", text2="#a7afb7", hover="#363b41", akzent="#4a8fd8", weich="#2f4966", grau="#7c858e", griff="#454b52",
               griff_h="#5a6169"),
}

QSS = """
QToolButton { border: none; border-radius: 5px; padding: 2px; background: transparent; }
QToolButton:hover { background: %(hover)s; }
QToolButton:pressed, QToolButton:checked { background: %(weich)s; }
QToolButton:disabled { color: %(grau)s; }
QToolButton::menu-button { border: none; width: 12px; border-top-right-radius: 5px; border-bottom-right-radius: 5px; }
QToolButton::menu-button:hover { background: %(hover)s; }
QPushButton { border: 1px solid %(rand)s; border-radius: 6px; padding: 5px 14px; background: %(karte)s; }
QPushButton:hover { background: %(hover)s; }
QPushButton:pressed { background: %(weich)s; }
QPushButton:disabled { color: %(grau)s; background: transparent; }
QPushButton:default { border-color: %(akzent)s; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit { border: 1px solid %(rand)s; border-radius: 6px; padding: 3px 6px;
    background: %(feld)s; selection-background-color: %(akzent)s; selection-color: white; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: %(akzent)s; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: url(%(pfeil_unten)s); width: 10px; height: 10px; }
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { border: none; width: 16px; background: transparent; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url(%(pfeil_oben)s); width: 8px; height: 8px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url(%(pfeil_unten)s); width: 8px; height: 8px; }
QScrollArea#bandSeite QScrollBar:horizontal { height: 6px; margin: 0; }
QScrollArea#bandSeite QScrollBar::handle:horizontal { margin: 0; border-radius: 3px; }
QComboBox QAbstractItemView { border: 1px solid %(rand)s; background: %(karte)s; selection-background-color: %(weich)s; selection-color: %(text)s; outline: 0; }
QMenu { background: %(karte)s; border: 1px solid %(rand)s; border-radius: 8px; padding: 5px; }
QMenu::item { padding: 6px 26px 6px 12px; border-radius: 5px; }
QMenu::item:selected { background: %(weich)s; color: %(text)s; }
QMenu::item:disabled { color: %(grau)s; }
QMenu::separator { height: 1px; background: %(rand)s; margin: 5px 8px; }
QToolTip { background: %(karte)s; color: %(text)s; border: 1px solid %(rand)s; padding: 4px 6px; }
QStatusBar { background: %(bg)s; border-top: 1px solid %(rand)s; }
QStatusBar::item { border: none; }
QScrollBar:vertical { width: 11px; background: transparent; margin: 0; }
QScrollBar:horizontal { height: 11px; background: transparent; margin: 0; }
QScrollBar::handle:vertical { background: %(griff)s; border-radius: 4px; min-height: 36px; margin: 2px; }
QScrollBar::handle:horizontal { background: %(griff)s; border-radius: 4px; min-width: 36px; margin: 2px; }
QScrollBar::handle:hover { background: %(griff_h)s; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; background: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QSlider::groove:horizontal { height: 4px; background: %(rand)s; border-radius: 2px; }
QSlider::sub-page:horizontal { background: %(akzent)s; border-radius: 2px; }
QSlider::handle:horizontal { background: %(karte)s; border: 2px solid %(akzent)s; width: 10px; height: 10px; margin: -6px 0; border-radius: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid %(grau)s; border-radius: 4px; background: %(karte)s; }
QCheckBox::indicator:checked { background: %(akzent)s; border-color: %(akzent)s; }
QGroupBox { border: 1px solid %(rand)s; border-radius: 8px; margin-top: 12px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: %(grau)s; }
QTreeWidget, QListWidget { border: 1px solid %(rand)s; border-radius: 6px; background: %(karte)s; outline: 0; }
QTreeWidget::item, QListWidget::item { padding: 4px; border-radius: 4px; }
QTreeWidget::item:selected, QListWidget::item:selected { background: %(weich)s; color: %(text)s; }
QTabBar#bandReiter { background: transparent; }
QTabBar#bandReiter::tab { background: transparent; border: none; border-bottom: 3px solid transparent;
    padding: 6px 14px 4px 14px; margin: 0 2px; }
QTabBar#bandReiter::tab { color: %(text2)s; }
QTabBar#bandReiter::tab:hover { background: %(hover)s; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar#bandReiter::tab:selected { color: %(akzent)s; font-weight: 600; border-bottom: 3px solid %(akzent)s; }
QTabBar#dokReiter::tab { background: transparent; border: none; padding: 7px 14px; margin: 0 1px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar#dokReiter::tab:hover { background: %(hover)s; }
QTabBar#dokReiter::close-button { image: url(%(x_bild)s); subcontrol-position: right; border-radius: 4px; padding: 2px; }
QTabBar#dokReiter::close-button:hover { background: %(hover)s; }
QTabBar#dokReiter::tab:selected { background: %(flaeche)s; font-weight: 600; }
QWidget#bandKopf { background: %(bg)s; }
QStackedWidget#bandStapel, QScrollArea#bandSeite, QScrollArea#bandSeite > QWidget > QWidget { background: %(flaeche)s; }
QWidget#dokLeiste { background: %(dokleiste)s; }
SchreibhilfePanel, SchreibhilfePanel QScrollArea, SchreibhilfePanel QScrollArea > QWidget > QWidget { background: %(tafel)s; }
"""


def _pfeile(farbe: str) -> tuple[str, str]:
    """Kleine Pfeile als SVG-Dateien (QSS kann nur Dateien einbinden)."""
    import os
    import tempfile
    ordner = os.path.join(tempfile.gettempdir(), "lunivo-writer-theme")
    os.makedirs(ordner, exist_ok=True)
    pfade = []
    for name, d in (("unten", "M2 4 L6 8 L10 4"), ("oben", "M2 8 L6 4 L10 8")):
        p = os.path.join(ordner, f"pfeil_{name}_{farbe.lstrip('#')}.svg")
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><path d="{d}" fill="none" '
                         f'stroke="{farbe}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
        pfade.append(p.replace("\\", "/"))
    return pfade[0], pfade[1]


def _kreuz(farbe: str) -> str:
    import os
    import tempfile
    ordner = os.path.join(tempfile.gettempdir(), "lunivo-writer-theme")
    os.makedirs(ordner, exist_ok=True)
    p = os.path.join(ordner, f"kreuz_{farbe.lstrip('#')}.svg")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><path d="M3 3 L9 9 M9 3 L3 9" fill="none" '
                     f'stroke="{farbe}" stroke-width="1.6" stroke-linecap="round"/></svg>')
    return p.replace("\\", "/")


def _stil(app: QApplication) -> None:
    f = dict(FARBEN[_ist_dunkel(app)])
    f["pfeil_unten"], f["pfeil_oben"] = _pfeile(f["text"])
    f["x_bild"] = _kreuz(f["grau"])
    app.setStyleSheet(QSS % f)


def _setze(app: QApplication, mode: str) -> None:
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    if mode == "dark":
        p = QPalette()
        bg, base, txt = QColor(42, 46, 50), QColor(31, 34, 37), QColor(230, 233, 236)      # Leiste, Fläche um das Blatt, Schrift
        p.setColor(QPalette.Window, bg); p.setColor(QPalette.WindowText, txt)
        p.setColor(QPalette.Base, base); p.setColor(QPalette.AlternateBase, QColor(47, 51, 56))
        p.setColor(QPalette.Text, txt); p.setColor(QPalette.Button, QColor(47, 51, 56))
        p.setColor(QPalette.ButtonText, txt); p.setColor(QPalette.ToolTipBase, base)
        p.setColor(QPalette.ToolTipText, txt); p.setColor(QPalette.Highlight, QColor(74, 143, 216))
        p.setColor(QPalette.HighlightedText, Qt_white()); p.setColor(QPalette.Mid, QColor(124, 133, 142))
        p.setColor(QPalette.Dark, QColor(31, 34, 37))
        p.setColor(QPalette.Light, QColor(70, 74, 80)); p.setColor(QPalette.Midlight, QColor(58, 63, 69))
        p.setColor(QPalette.Link, QColor(110, 168, 230)); p.setColor(QPalette.LinkVisited, QColor(170, 140, 220))
        p.setColor(QPalette.BrightText, QColor(255, 255, 255))
        p.setColor(QPalette.PlaceholderText, QColor(150, 156, 162))
        grau = QColor(125, 130, 136)
        for rolle in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            p.setColor(QPalette.Disabled, rolle, grau)
        p.setColor(QPalette.Disabled, QPalette.Base, QColor(38, 41, 45))
        p.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 86, 94))
        app.setPalette(p)
    elif mode == "light":
        p = QPalette()
        app.setPalette(app.style().standardPalette())
        pal = app.palette(); pal.setColor(QPalette.Dark, QColor(226, 229, 234)); app.setPalette(pal)
    else:
        app.setPalette(app.style().standardPalette())
        if _ist_dunkel(app):
            _setze(app, "dark")                                     # dunkles System: dieselbe Palette wie „Immer dunkel“
        else:
            pal = app.palette(); pal.setColor(QPalette.Dark, QColor(226, 229, 234)); app.setPalette(pal)


def Qt_white() -> QColor:
    return QColor(255, 255, 255)
