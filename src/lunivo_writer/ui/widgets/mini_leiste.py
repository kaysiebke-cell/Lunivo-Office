"""Minisymbolleiste: schwebende Leiste mit den häufigsten Formaten über der Auswahl oder am Rechtsklick.

Optionen ▸ Ansicht: „Minisymbolleiste bei Auswahl“ und „Minisymbolleiste bei Rechtsklick“. Die Knöpfe rufen dieselben Befehle wie das Band.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QHBoxLayout, QMenu, QToolButton, QVBoxLayout

from lunivo_writer.ui.widgets import icons

# Zwei Zeilen wie in der Vorlage. Eintrag: (Befehl, Tooltip, Art) — Art: "" (Knopf) · "klappe" (Pfeil mit Menü des Bandes) · "farbe" (Palette)
ZEILE1 = [("kopieren", "Kopieren", ""), ("einfuegen", "Einfügen", "klappe:menue_einfuegenKlappe"), "schriftart", "groesse",
          ("schriftGroesser", "Schrift vergrößern", ""), ("schriftKleiner", "Schrift verkleinern", "")]
ZEILE2 = [("ausschneiden", "Ausschneiden", ""), ("formatUebertragen", "Format übertragen", ""),
          ("fett", "Fett", ""), ("kursiv", "Kursiv", ""), ("unter", "Unterstrichen", ""),
          ("hervorhebenJetzt", "Hervorheben", "farbe:menue_hervorhebenKlappe"), ("schriftfarbeJetzt", "Schriftfarbe", "farbe:menue_schriftfarbeKlappe"),
          ("ausrichtung", "Ausrichtung", "klappe:_ausrichtung_menue"), ("zeilenabstand", "Zeilenabstand", "klappe:menue_zeilenabstandKlappe")]
GROESSEN = [8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]


def _symbole() -> dict[str, str]:
    from lunivo_writer.ui.ribbon.ribbon_bar import lade_register
    out = {}

    def lauf(o):
        if isinstance(o, dict):
            if isinstance(o.get("tun"), str) and o.get("symbol"):
                out.setdefault(o["tun"], o["symbol"])
            if isinstance(o.get("klappe"), str) and o.get("symbol"):
                out.setdefault(o["klappe"].replace("Klappe", ""), o["symbol"])
            for v in o.values():
                lauf(v)
        elif isinstance(o, list):
            for x in o:
                lauf(x)
    lauf(lade_register())
    out.setdefault("einfuegen", "kleben"); out.setdefault("kopieren", "kopie"); out.setdefault("ausschneiden", "schere")
    out.setdefault("formatUebertragen", "pinsel"); out.setdefault("ausrichtung", "links")
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
        v = QVBoxLayout(self)
        v.setContentsMargins(5, 4, 5, 4); v.setSpacing(2)
        self.knoepfe: dict[str, QToolButton] = {}
        self._menues: dict[str, str] = {}
        sym = _symbole()
        for zeile in (ZEILE1, ZEILE2):
            h = QHBoxLayout(); h.setSpacing(1)
            for k in zeile:
                if k == "schriftart":
                    self.schriftart = QComboBox(); self.schriftart.setFocusPolicy(Qt.NoFocus); self.schriftart.setFixedWidth(128)
                    self.schriftart.addItems(QFontDatabase.families()); self.schriftart.setMaxVisibleItems(18)
                    self.schriftart.textActivated.connect(lambda n: self._schrift(n))
                    h.addWidget(self.schriftart); continue
                if k == "groesse":
                    self.groesse = QComboBox(); self.groesse.setFocusPolicy(Qt.NoFocus); self.groesse.setFixedWidth(58)
                    self.groesse.addItems([f"{g:g}" for g in GROESSEN]); self.groesse.setMaxVisibleItems(16)
                    self.groesse.textActivated.connect(lambda t: self._groesse(t))
                    h.addWidget(self.groesse); continue
                tun, tip, art = k
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
                if art:                                                # Pfeil mit Menü; Klick auf das Symbol wirkt wie im Band
                    b.setPopupMode(QToolButton.MenuButtonPopup)
                    self._menues[tun] = art
                    self._menue_setzen(b, tun)
                if tun in ("ausrichtung", "zeilenabstand"):
                    b.clicked.connect(lambda _=False, b=b: b.showMenu())
                else:
                    b.clicked.connect(lambda _=False, tun=tun: self._tun(tun))
                h.addWidget(b)
                self.knoepfe[tun] = b
            h.addStretch(1)
            v.addLayout(h)
        self._ed = None

    def _ausrichtung_menue(self) -> QMenu:
        m = QMenu()
        for text, tun in (("Linksbündig", "links"), ("Zentriert", "mitte"), ("Rechtsbündig", "rechts"), ("Blocksatz", "block")):
            m.addAction(text, lambda _=False, t=tun: self._tun(t))
        return m

    def _menue_setzen(self, b: QToolButton, tun: str) -> None:
        """Das Menü ist dasselbe wie im Band (Einfügen, Farbpaletten mit „Zuletzt benutzt“ und Vorschau, Zeilenabstand); es entsteht nach jeder Wahl neu."""
        art, _, name = self._menues[tun].partition(":")
        quelle = self if name.startswith("_") else self.w.befehle
        m = getattr(quelle, name)()
        alt = getattr(b, "_menue_obj", None)
        b._menue_obj = m                                              # sonst räumt Python das Menü ab, bevor es sich öffnet
        b.setMenu(m)
        if alt is not None:
            alt.deleteLater()
        if hasattr(m, "gewaehlt"):
            m.gewaehlt.connect(lambda _c: self._nach_farbe(b, tun))
        m.aboutToHide.connect(lambda: QTimer.singleShot(0, lambda: self._menue_setzen(b, tun)))

    def _nach_farbe(self, b: QToolButton, tun: str) -> None:
        if self._ed is not None:
            self._ed.setFocus()

    def _schrift(self, name: str) -> None:
        if self._ed is not None:
            self._ed.set_font_family(name); self._ed.setFocus()

    def _groesse(self, text: str) -> None:
        try:
            if self._ed is not None:
                self._ed.set_font_size(float(text.replace(",", "."))); self._ed.setFocus()
        except ValueError:
            pass

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
        if self._ed is not None:                                      # Schrift und Größe an der Schreibmarke / in der Auswahl
            cf = self._ed.textCursor().charFormat()
            fam = (cf.fontFamilies() or [self._ed.document().defaultFont().family()])
            fam = fam[0] if isinstance(fam, list) else fam
            pt = cf.fontPointSize() or self._ed.document().defaultFont().pointSizeF()
            self.schriftart.blockSignals(True); self.groesse.blockSignals(True)
            i = self.schriftart.findText(str(fam))
            self.schriftart.setCurrentIndex(i) if i >= 0 else self.schriftart.setEditText(str(fam)) if self.schriftart.isEditable() else None
            self.groesse.setCurrentText(f"{pt:g}")
            self.schriftart.blockSignals(False); self.groesse.blockSignals(False)

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
        if e.type() == QEvent.FocusOut and e.reason() == Qt.PopupFocusReason:
            return False                                           # eine Palette der Leiste selbst ging auf: die Leiste bleibt
        if e.type() in (QEvent.KeyPress, QEvent.Wheel, QEvent.FocusOut, QEvent.Hide) and self.l.isVisible():
            self.l.hide()
        return False
