"""Das Band (Register): Reiter → Gruppen → Knöpfe, gebaut aus resources/register.json.

register.json wird von werkzeug/register-exportieren.js aus oberflaeche/daten/register.js erzeugt —
dieselbe Liste, derselbe Aufbau wie im alten Programm. Was `Befehle` nicht kennt, steht ausgegraut da.
"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QComboBox, QFontComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMenu, QScrollArea,
    QSizePolicy, QStackedWidget, QTabBar, QToolButton, QVBoxLayout, QWidget,
)

from ..editor.editor_widget import STYLES
from . import icons

_HIER = os.path.dirname(os.path.abspath(__file__))
NICHT_DA = "{} — in der nativen Fassung noch nicht umgesetzt"
STILE_KATALOG = ["Standard", "Überschrift 1", "Überschrift 2", "Überschrift 3", "Titel", "Untertitel", "Zitat", "Kein Abstand"]
TEXTSYMBOLE = {"F": QFont.Bold, "K": None, "U": None}


def lade_register() -> dict:
    with open(os.path.join(_HIER, "..", "resources", "register.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _zweizeilig(text: str) -> str:
    if len(text) <= 12 or " " not in text:
        return text
    mitte = len(text) // 2
    i = min((i for i, c in enumerate(text) if c == " "), key=lambda i: abs(i - mitte))
    return text[:i] + "\n" + text[i + 1:]


class RegisterBand(QWidget):
    """Kopfzeile (☰, Schnellzugriff, Reiter) und darunter das Band des gewählten Reiters."""

    def __init__(self, befehle, daten: dict | None = None):
        super().__init__()
        self.b = befehle
        self.daten = daten or lade_register()
        self.schalter: list[tuple[QToolButton, str]] = []     # (Knopf, Aktionsname) für Haken
        self.knoepfe: list[tuple[QToolButton, str | None, bool]] = []   # (Knopf, Name, braucht Dokument)
        self.felder: dict[str, QWidget] = {}
        self.fehlend: list[str] = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.kopf = QHBoxLayout()
        self.kopf.setContentsMargins(6, 2, 6, 0)
        self.kopf.setSpacing(2)
        self.menue_knopf = QToolButton()
        self.menue_knopf.setText("☰ Menü ▾")
        self.menue_knopf.setAutoRaise(True)
        self.kopf.addWidget(self.menue_knopf)
        self.schnell = QHBoxLayout()
        self.schnell.setSpacing(0)
        self.kopf.addLayout(self.schnell)
        self._trenner()
        self.reiter = QTabBar()
        self.reiter.setDrawBase(False)
        self.reiter.setExpanding(False)
        self.kopf.addWidget(self.reiter, 1)
        lay.addLayout(self.kopf)
        self.stapel = QStackedWidget()
        self.stapel.setFixedHeight(112)
        lay.addWidget(self.stapel)
        linie = QFrame()
        linie.setFrameShape(QFrame.HLine)
        linie.setFrameShadow(QFrame.Sunken)
        lay.addWidget(linie)
        self._schnellzugriff()
        for r in self.daten["register"]:
            self._reiter(r)
        self.reiter.currentChanged.connect(self.stapel.setCurrentIndex)
        self.bandfehler = sorted(set(self.fehlend))

    def _trenner(self):
        s = QFrame()
        s.setFrameShape(QFrame.VLine)
        s.setFrameShadow(QFrame.Sunken)
        self.kopf.addWidget(s)

    # ---- Schnellzugriff -------------------------------------------------------------------------------
    SCHNELL = [("oeffnen", "Öffnen", "oeffnen"), ("speichern", "Speichern", "speichern"),
               ("pdf", "Als PDF exportieren", "speichernPdf"), ("drucken", "Drucken", "drucken"),
               ("vorschau", "Druckvorschau", "vorschau"), ("zurueck", "Rückgängig", "rueckgaengig"),
               ("vor", "Wiederholen", "wiederholen")]

    def _schnellzugriff(self):
        for sym, name, aktion in self.SCHNELL:
            k = QToolButton()
            k.setAutoRaise(True)
            k.setToolTip(name)
            k.setIcon(icons.icon(sym, 18))
            k.setIconSize(QSize(18, 18))
            k.clicked.connect(lambda _=False, a=aktion: self.b.tun(a))
            self.schnell.addWidget(k)
            self.knoepfe.append((k, aktion, sym in ("speichern", "pdf", "drucken", "vorschau", "zurueck", "vor")))

    # ---- Reiter und Gruppen -------------------------------------------------------------------------------
    def _reiter(self, r: dict):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        seite = QWidget()
        h = QHBoxLayout(seite)
        h.setContentsMargins(6, 2, 6, 0)
        h.setSpacing(0)
        for i, g in enumerate(r["gruppen"]):
            if i:
                s = QFrame()
                s.setFrameShape(QFrame.VLine)
                s.setFrameShadow(QFrame.Sunken)
                h.addWidget(s)
            h.addWidget(self._gruppe(g))
        h.addStretch(1)
        scroll.setWidget(seite)
        self.stapel.addWidget(scroll)
        self.reiter.addTab(r["name"])

    def _gruppe(self, g: dict) -> QWidget:
        rahmen = QWidget()
        v = QVBoxLayout(rahmen)
        v.setContentsMargins(8, 2, 8, 0)
        v.setSpacing(0)
        inhalt = QHBoxLayout()
        inhalt.setSpacing(4)
        inhalt.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        v.addLayout(inhalt, 1)
        if g.get("katalog"):
            inhalt.addWidget(self._stile())
        else:
            self._knoepfe(g, inhalt)
        fuss = QHBoxLayout()
        fuss.setContentsMargins(0, 0, 0, 0)
        t = QLabel(g["name"].upper())
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size: 7pt; color: palette(mid); letter-spacing: 1px;")
        fuss.addStretch(1)
        fuss.addWidget(t)
        if g.get("pfeil"):
            p = QToolButton()
            p.setText("↘")
            p.setAutoRaise(True)
            p.setFixedSize(14, 14)
            p.setStyleSheet("font-size: 7pt;")
            p.setToolTip(g["name"] + " — Einstellungen")
            p.clicked.connect(lambda _=False, a=g["pfeil"]: self.b.tun(a))
            p.setEnabled(self.b.hat(g["pfeil"]))
            if not self.b.hat(g["pfeil"]):
                self.fehlend.append(g["pfeil"])
            fuss.addWidget(p)
        fuss.addStretch(1)
        v.addLayout(fuss)
        return rahmen

    def _knoepfe(self, g: dict, inhalt: QHBoxLayout):
        eintraege = g["knoepfe"]
        if g.get("felder"):
            spalte = QVBoxLayout()
            spalte.setSpacing(2)
            stil = QComboBox()
            stil.setFixedWidth(150)
            stil.addItems(["Fließtext"] + [n for n in STYLES if n != "Standard"])
            font = QFontComboBox()
            font.setFixedWidth(150)
            groesse = QComboBox()
            groesse.setEditable(True)
            groesse.setFixedWidth(60)
            groesse.addItems([str(x) for x in (8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72)])
            for w in (stil, font, groesse):
                spalte.addWidget(w)
            inhalt.addLayout(spalte)
            self.felder.update(stil=stil, font=font, groesse=groesse)
        grosse = [e for e in eintraege if e.get("gross")]
        kleine = [e for e in eintraege if not e.get("gross") and not e.get("hinweis")]
        for e in grosse:
            inhalt.addWidget(self._knopf(e, True))
        # Zeilen: '//' beginnt eine neue; sonst zwei Zeilen, spaltenweise gefüllt
        zeilen, aktuell, explizit = [], [], False
        for e in eintraege:
            if e.get("zeilenumbruch"):
                explizit = True
                zeilen.append(aktuell)
                aktuell = []
            elif not e.get("gross") and not e.get("hinweis"):
                aktuell.append(e)
        zeilen.append(aktuell)
        gitter = QGridLayout()
        gitter.setSpacing(1)
        if explizit:
            for r, zeile in enumerate(zeilen):
                for c, e in enumerate(zeile):
                    gitter.addWidget(self._knopf(e, False), r, c)
        else:
            for i, e in enumerate(kleine):
                gitter.addWidget(self._knopf(e, False), i % 2, i // 2)
        if kleine:
            host = QWidget()
            host.setLayout(gitter)
            inhalt.addWidget(host, 0, Qt.AlignTop)

    def _stile(self) -> QWidget:
        host = QWidget()
        g = QGridLayout(host)
        g.setSpacing(1)
        g.setContentsMargins(0, 0, 0, 0)
        for i, name in enumerate(STILE_KATALOG):
            k = QToolButton()
            k.setAutoRaise(True)
            k.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            k.setText(f"Aa\n{name}")
            f = k.font()
            f.setPointSizeF(8)
            if name.startswith("Überschrift") or name == "Titel":
                f.setBold(True)
            if name in ("Untertitel", "Zitat"):
                f.setItalic(True)
            k.setFont(f)
            k.setFixedWidth(84)
            k.clicked.connect(lambda _=False, n=name: self.b.w.stil_anwenden(n))
            g.addWidget(k, i % 2, i // 2)
            self.knoepfe.append((k, None, True))
        return host

    def _knopf(self, e: dict, gross: bool) -> QToolButton:
        name = e["name"]
        sym = e.get("symbol", "")
        k = QToolButton()
        k.setAutoRaise(True)
        tun, klappe, menue = e.get("tun"), e.get("klappe"), e.get("menue")
        akt = QAction(k)
        akt.setText(sym if not icons.hat(sym) else name)
        akt.setToolTip(name)
        if icons.hat(sym):
            akt.setIcon(icons.icon(sym, 28 if gross else 18))
            k.setIconSize(QSize(28, 28) if gross else QSize(18, 18))
        k.setDefaultAction(akt)
        k.setToolTip(name)
        if not icons.hat(sym):
            f = k.font()
            if sym == "F":
                f.setBold(True)
            if sym == "K":
                f.setItalic(True)
            if sym == "U":
                f.setUnderline(True)
            k.setFont(f)
        if gross:
            k.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            k.setText(_zweizeilig(name))
            breit = max(k.fontMetrics().horizontalAdvance(z) for z in _zweizeilig(name).split("\n"))
            k.setMinimumWidth(max(56, breit + 22))
            k.setFixedHeight(68)
        elif icons.hat(sym):
            k.setToolButtonStyle(Qt.ToolButtonIconOnly)
        else:
            k.setMinimumWidth(40 if (klappe or menue) else 28)
        ok = False
        menu = None
        if menue:
            menu = QMenu(k)
            ok = self._menue_fuellen(menu, menue)
            k.setPopupMode(QToolButton.InstantPopup)
        elif klappe and self.b.klappe(klappe) is not None:
            menu = self.b.klappe(klappe)
            menu.setParent(k, Qt.Popup)
            k.setPopupMode(QToolButton.MenuButtonPopup if tun else QToolButton.InstantPopup)
            ok = True
        if menu is not None:
            k.setMenu(menu)
        if tun:
            ok = ok or self.b.hat(tun)
            akt.triggered.connect(lambda _=False, t=tun, kk=k: (self.b.tun(t, kk), self.aktualisieren()))
        elif not menu:
            ok = False
        if e.get("haken") or (tun and self.b.zustand(tun) is not None):
            akt.setCheckable(True)
            self.schalter.append((k, tun))
        for n in (tun, klappe):
            if n and not self.b.hat(n) and not (n == klappe and self.b.klappe(n) is not None):
                self.fehlend.append(n)
        if not ok:
            k.setProperty("fehlt", True)
            k.setEnabled(False)
            k.setToolTip(NICHT_DA.format(name))
        self.knoepfe.append((k, tun, True))
        return k

    def _menue_fuellen(self, menu: QMenu, items: list) -> bool:
        ok = False
        for it in items:
            if it.get("trenner"):
                menu.addSeparator()
            elif it.get("menue"):
                sub = menu.addMenu(it["name"])
                ok |= self._menue_fuellen(sub, it["menue"])
            elif it.get("name"):
                a = menu.addAction(it["name"])
                t = it.get("tun")
                if t and self.b.hat(t):
                    a.triggered.connect(lambda _=False, t=t: self.b.tun(t))
                    ok = True
                else:
                    a.setEnabled(False)
                    a.setToolTip(NICHT_DA.format(it["name"]))
                    if t:
                        self.fehlend.append(t)
        return ok

    # ---- Zustand -----------------------------------------------------------------------------------------------
    def aktualisieren(self, hat_dokument: bool | None = None):
        for k, name in self.schalter:
            z = self.b.zustand(name) if name else None
            a = k.defaultAction()
            a.blockSignals(True)
            a.setChecked(bool(z))
            a.blockSignals(False)
        if hat_dokument is not None:
            for k, name, braucht in self.knoepfe:
                if braucht and not k.property("fehlt"):
                    k.setEnabled(hat_dokument)
