"""Menü-Liste: Zeilen mit Symbol, Text, Tastenkürzel, Haken und Untermenü — überall dieselbe Gestalt."""
from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu


class MenueListe(QMenu):
    """Ein Menü, das Zeilen einheitlich aufbaut. Nicht Mögliches bleibt grau sichtbar statt zu fehlen."""

    def eintrag(self, text: str, aktion: Callable | None = None, *, symbol: QIcon | None = None, kuerzel: str = "",
                haken: bool | None = None, aktiv: bool = True, tip: str = "", daten=None) -> QAction:
        a = QAction(text + ("\t" + kuerzel if kuerzel else ""), self)
        if symbol is not None:
            a.setIcon(symbol)
        if haken is not None:
            a.setCheckable(True); a.setChecked(haken)
        a.setEnabled(aktiv)
        if tip:
            a.setToolTip(tip)
        if daten is not None:
            a.setData(daten)
        if aktion is not None:
            a.triggered.connect(lambda _c=False, f=aktion: f())
        self.addAction(a)
        return a

    def untermenue(self, text: str, symbol: QIcon | None = None, aktiv: bool = True) -> "MenueListe":
        m = MenueListe(text, self)
        if symbol is not None:
            m.setIcon(symbol)
        m.setEnabled(aktiv)
        self.addMenu(m)
        return m

    def trenner(self):
        return self.addSeparator()

    @classmethod
    def aus_liste(cls, zeilen, parent=None) -> "MenueListe":
        """Baut ein Menü aus einer Beschreibung: ``"-"`` = Trennlinie, sonst ein Wörterbuch mit text, aktion, symbol,
        kuerzel, haken, aktiv, tip und optional ``untermenue`` (wieder eine Liste)."""
        m = cls(parent)
        m._fuellen(zeilen)
        return m

    def _fuellen(self, zeilen) -> None:
        for z in zeilen:
            if z == "-":
                self.trenner(); continue
            z = dict(z)
            if "untermenue" in z:
                self.untermenue(z["text"], z.get("symbol"), z.get("aktiv", True))._fuellen(z["untermenue"])
            else:
                self.eintrag(z["text"], z.get("aktion"), symbol=z.get("symbol"), kuerzel=z.get("kuerzel", ""),
                             haken=z.get("haken"), aktiv=z.get("aktiv", True), tip=z.get("tip", ""), daten=z.get("daten"))
