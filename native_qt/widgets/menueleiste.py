"""Menüleiste aus der alten Menüstruktur (MENUES in programm.js → register.json „menues“)."""
from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

NICHT_DA = "{} — in der nativen Fassung noch nicht umgesetzt"
TASTEN = {"Strg": "Ctrl", "Umschalt": "Shift", "Alt": "Alt"}


def _taste(t: str) -> str:
    for de, en in TASTEN.items():
        t = t.replace(de, en)
    return t.replace("−", "-")


def baue_menueleiste(mb: QMenuBar, menues: list, befehle) -> int:
    """Füllt die Menüleiste. → Anzahl der Menüpunkte ohne nativen Befehl."""
    fehlend = 0

    def fuellen(menu: QMenu, punkte: list):
        nonlocal fehlend
        for p in punkte:
            if p.get("trenner"):
                menu.addSeparator()
            elif p.get("unter"):
                fuellen(menu.addMenu(p["name"]), p["unter"])
            elif p.get("unter_dynamisch"):
                m = menu.addMenu(p["name"])
                if p["name"] == "Fenster":
                    m.aboutToShow.connect(lambda m=m: _fenster_menue(m, befehle))
            else:
                a = QAction(p["name"], menu)
                t = p.get("tun")
                if p["name"] == "Optionen":
                    a.triggered.connect(lambda: befehle.w.show_options())
                elif t and t != "eigen" and befehle.hat(t):
                    a.triggered.connect(lambda _=False, t=t: befehle.tun(t))
                else:
                    a.setEnabled(False)
                    a.setToolTip(NICHT_DA.format(p["name"]))
                    fehlend += 1
                if p.get("taste"):
                    a.setText(p["name"] + "\t" + p["taste"])
                menu.addAction(a)

    for m in menues:
        fuellen(mb.addMenu(m["name"]), m["punkte"])
    return fehlend


def _fenster_menue(m: QMenu, befehle) -> None:
    m.clear()
    w = befehle.w
    for i, t in enumerate(w._doc_tabs()):
        a = m.addAction(("● " if t.is_modified() else "") + t.title)
        a.setCheckable(True)
        a.setChecked(t is w.current_tab())
        a.triggered.connect(lambda _=False, t=t: w.docs.setCurrentWidget(t))
    m.addSeparator()
    m.addAction("Neues Dokument", w.new_document)
    m.addAction("Dokument schließen", lambda: w.close_tab(w.docs.currentIndex()))
