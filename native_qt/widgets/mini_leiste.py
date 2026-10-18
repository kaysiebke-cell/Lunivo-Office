"""Minisymbolleiste: schwebende Leiste mit den häufigsten Formaten über der Auswahl oder am Rechtsklick.

Optionen ▸ Ansicht: „Minisymbolleiste bei Auswahl“ und „Minisymbolleiste bei Rechtsklick“. Die Knöpfe rufen dieselben Befehle wie das Band.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QToolButton

from . import icons

KNOEPFE = [("fett", "Fett"), ("kursiv", "Kursiv"), ("unter", "Unterstrichen"), ("durch", "Durchgestrichen"),
           None, ("schriftGroesser", "Schrift vergrößern"), ("schriftKleiner", "Schrift verkleinern"),
           ("hervorhebenJetzt", "Hervorheben"), ("schriftfarbeJetzt", "Schriftfarbe"),
           None, ("links", "Linksbündig"), ("mitte", "Zentriert"), ("rechts", "Rechtsbündig"), ("punkte", "Aufzählung")]


def _symbole() -> dict[str, str]:
    from .register_band import lade_register
    out = {}

    def lauf(o):
        if isinstance(o, dict):
            if isinstance(o.get("tun"), str) and o.get("symbol"):
                out.setdefault(o["tun"], o["symbol"])
            for v in o.values():
                lauf(v)
        elif isinstance(o, list):
            for x in o:
                lauf(x)
    lauf(lade_register())
    return out


class MiniLeiste(QFrame):
    def __init__(self, fenster):
        super().__init__(fenster, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.w = fenster
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setObjectName("miniLeiste")
        self.setStyleSheet("#miniLeiste { background: palette(window); border: 1px solid palette(mid); border-radius: 6px; }"
                           "QToolButton { border: none; border-radius: 4px; padding: 3px; }"
                           "QToolButton:hover { background: palette(midlight); }"
                           "QToolButton:checked { background: palette(highlight); }")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 3, 4, 3)
        lay.setSpacing(1)
        self.knoepfe: dict[str, QToolButton] = {}
        sym = _symbole()
        for k in KNOEPFE:
            if k is None:
                t = QFrame()
                t.setFrameShape(QFrame.VLine)
                t.setFrameShadow(QFrame.Sunken)
                lay.addWidget(t)
                continue
            tun, tip = k
            b = QToolButton()
            b.setIcon(icons.icon(sym.get(tun, ""), 18))
            if b.icon().isNull():                                  # Fett/Kursiv/Unterstrichen sind im Band Buchstaben, keine Symbole
                b.setText({"fett": "F", "kursiv": "K", "unter": "U"}.get(tun, tip[:1]))
                f = b.font()
                f.setBold(tun == "fett"); f.setItalic(tun == "kursiv"); f.setUnderline(tun == "unter")
                b.setFont(f)
                b.setMinimumWidth(26)
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.NoFocus)
            b.setCheckable(self.w.befehle.zustand(tun) is not None)
            b.clicked.connect(lambda _=False, tun=tun: self._tun(tun))
            lay.addWidget(b)
            self.knoepfe[tun] = b
        self._ed = None

    def _tun(self, tun: str) -> None:
        self.w.befehle.tun(tun)
        self.aktualisieren()
        if self._ed is not None:
            self._ed.setFocus()

    def aktualisieren(self) -> None:
        for tun, b in self.knoepfe.items():
            z = self.w.befehle.zustand(tun)
            if z is not None:
                b.setChecked(bool(z))

    def zeigen(self, editor, global_pos: QPoint, rechtsklick: bool = False) -> None:
        """Über global_pos zeigen (am Rechtsklick darunter, neben dem Menü); verschwindet bei Tastendruck oder Auswahlende."""
        unter = rechtsklick
        self._rechtsklick = rechtsklick
        self._ed = editor
        self.aktualisieren()
        self.adjustSize()
        x = global_pos.x() - self.width() // 2
        y = global_pos.y() + (18 if unter else -self.height() - 8)
        scr = QApplication.screenAt(global_pos)
        if scr is not None:
            g = scr.availableGeometry()
            x = max(g.left(), min(x, g.right() - self.width()))
            y = max(g.top(), min(y, g.bottom() - self.height()))
        self.move(x, y)
        self.show()
        if not hasattr(editor, "_mini_filter"):
            editor._mini_filter = _Zu(self, editor)
            editor.installEventFilter(editor._mini_filter)
            editor.cursorPositionChanged.connect(lambda: self._pruefen(editor))
            editor.selectionChanged.connect(lambda: self._pruefen(editor))

    def _pruefen(self, editor) -> None:
        if self.isVisible() and self._ed is editor and not editor.textCursor().hasSelection() and not self._rechtsklick:
            self.hide()

    _rechtsklick = False


class _Zu(QObject):
    """Schließt die Leiste bei Tastendruck, Mausrad und Fokusverlust des Editors."""

    def __init__(self, leiste: MiniLeiste, editor):
        super().__init__(editor)
        self.l = leiste

    def eventFilter(self, o, e):
        if e.type() in (QEvent.KeyPress, QEvent.Wheel, QEvent.FocusOut, QEvent.Hide) and self.l.isVisible():
            self.l.hide()
        return False
