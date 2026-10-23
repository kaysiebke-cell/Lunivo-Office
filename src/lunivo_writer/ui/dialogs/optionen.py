"""Optionen — das Fenster hinter „☰ Menü ▸ Optionen“ (F9), aufgebaut in drei Zweigen:
Leichter lesen · Allgemein · Nur bei Lunivo. Links der Baum, rechts die Seite.

Was hier steht, wirkt. Was noch keine Wirkung hat, steht je Seite unter „Noch nicht umgesetzt“,
damit nichts stillschweigend verschwindet.
"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.core import paths

from lunivo_writer.core.farben import Farbe
ERKLAERUNG_LEER = "Zeig auf eine Einstellung — hier steht, was sie tut."
_ERKLAERUNGEN: dict | None = None


def _erklaerung(name: str) -> str:
    """Der Satz zu einer Einstellung (aus resources/daten/optionen_erklaerungen.json); leer, wenn es keinen gibt."""
    global _ERKLAERUNGEN
    if _ERKLAERUNGEN is None:
        try:
            with open(os.path.join(paths.RESSOURCEN, "daten", "optionen_erklaerungen.json"), encoding="utf-8") as fh:
                _ERKLAERUNGEN = json.load(fh)
        except (OSError, ValueError):
            _ERKLAERUNGEN = {}
    n = " ".join(name.split())
    if n in _ERKLAERUNGEN:
        return _ERKLAERUNGEN[n]
    return next((v for k, v in _ERKLAERUNGEN.items() if len(k) >= 8 and (n.startswith(k) or k.startswith(n))), "")






STIL = ('\nQTreeWidget#optNavigation { background: transparent; border: none; outline: none; }\nQTreeWidget#optNavigation::item { padding: 6px 10px; margin: 1px 8px 1px 0; border-radius: 6px; color: palette(mid); }\nQTreeWidget#optNavigation::item:selected { background: ' + Farbe.AKZENT + '; color: white; font-weight: 600; }\nQTreeWidget#optNavigation::item:hover:!selected { background: palette(midlight); }\nQTreeWidget#optNavigation::branch, QTreeWidget#optNavigation::branch:selected { background: transparent; }\nQScrollArea#optSeite, QScrollArea#optSeite > QWidget > QWidget { background: transparent; border: none; }\nQGroupBox { border: 1px solid palette(midlight); border-radius: 10px; margin-top: 26px; padding: 8px 10px 8px 10px; background: transparent; }\nQGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 2px; padding: 0; color: palette(mid); font-size: 8pt; font-weight: 600; }\nQWidget#optPaar { border-bottom: 1px solid palette(midlight); }\nQLabel#optErklaerung { color: palette(mid); font-style: italic; padding: 12px 24px; border-top: 1px solid palette(midlight); }\nQFrame#optSchriftkarte { border: 1px solid palette(midlight); border-radius: 8px; }\nQLabel#optVorschau { background: white; color: #111417; border-radius: 6px; padding: 16px 20px; }\n')




from lunivo_writer.ui.dialogs.optionen_seiten.lesen import LesenSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.ansicht import AnsichtSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.datei import DateiSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.befehle import BefehleSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.lunivo import LunivoSeiten
from PySide6.QtWidgets import QDialog
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile


class OptionenAnsicht(LesenSeiten, AnsichtSeiten, DateiSeiten, BefehleSeiten, LunivoSeiten, QWidget):
    """Alle Optionen als Ansicht (Navigation links, Seite rechts) — sie steht in der Datei-Ansicht („☰ Menü ▸ Erweiterte
    Einstellungen“) und im Dialog `OptionenDialog`. Werte gelten sofort."""


    def __init__(self, fenster, seite: str | None = None):
        super().__init__()
        self.w = fenster
        self.setStyleSheet(STIL)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        self.baum = QTreeWidget()
        self.baum.setObjectName("optNavigation")
        self.baum.setHeaderHidden(True)
        self.baum.setRootIsDecorated(True)
        self.baum.setIndentation(14)
        self.baum.setFocusPolicy(Qt.NoFocus)
        self.baum.setFixedWidth(250)
        self.stapel = QStackedWidget()
        self.stapel.setMinimumWidth(520)
        self.stapel.setMaximumWidth(860)
        h.addWidget(self.baum)
        sc = QScrollArea(); sc.setObjectName("optSeite"); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        halter = QWidget(); hl = QHBoxLayout(halter); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.stapel); hl.addStretch(1)                      # Seite links, nicht über die ganze Breite gezogen
        sc.setWidget(halter)
        rechts = QWidget(); rv = QVBoxLayout(rechts); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(0)
        rv.addWidget(sc, 1)
        self.erklaerzeile = text_label(ERKLAERUNG_LEER, umbruch=True)
        self.erklaerzeile.setObjectName("optErklaerung")
        rv.addWidget(self.erklaerzeile)
        h.addWidget(rechts, 1)
        self.knoten: dict[str, QTreeWidgetItem] = {}
        zweige = [
            ("Leichter lesen", [("lesehilfe", "Lesehilfe", self._lesehilfe), ("schriften", "Schriftarten", self._schriften),
                                ("sprache", "Sprache", self._sprache), ("rechtschreibung", "Rechtschreibprüfung", self._rechtschreibung)]),
            ("Allgemein", [("ansicht", "Ansicht", self._ansicht), ("bearbeiten", "Bearbeiten", self._bearbeiten),
                                   ("speichern", "Allgemein und Speichern", self._speichern),
                                   ("sicherung", "Sicherungseinstellungen", self._sicherung),
                                   ("speicherort", "Speicherort für Dateien", self._speicherort),
                                   ("verfolgen", "Änderungen verfolgen", self._verfolgen),
                                   ("pdf", "In PDF exportieren", self._pdf),
                                   ("benutzer", "Benutzerinformationen", self._benutzer),
                                   ("drucken", "Drucken", self._drucken),
                                   ("sicherheit", "Sicherheit", self._sicherheit),
                                   ("menueband", "Menüband anpassen", self._menueband),
                                   ("schnellzugriff", "Symbolleiste für den Schnellzugriff", self._schnellzugriff)]),
            ("Nur bei Lunivo", [("ki", "Schreibhilfe und KI", self._ki), ("gedaechtnis", "Gedächtnis", self._gedaechtnis),
                                ("erweitert", "Erweitert", self._erweitert)]),
        ]
        for zweig, seiten in zweige:
            z = QTreeWidgetItem([zweig])
            z.setFlags(z.flags() & ~Qt.ItemIsSelectable)
            f = z.font(0); f.setBold(True); f.setPointSizeF(max(7.5, f.pointSizeF() - 1.5)); f.setCapitalization(QFont.AllUppercase)
            z.setFont(0, f)
            z.setForeground(0, self.palette().mid())
            self.baum.addTopLevelItem(z)
            for key, titel, bauer in seiten:
                it = QTreeWidgetItem([titel])
                it.setData(0, Qt.UserRole, key)
                z.addChild(it)
                self.knoten[key] = it
                self.stapel.addWidget(bauer(titel))
                it.setData(0, Qt.UserRole + 1, self.stapel.count() - 1)
        self.baum.expandAll()
        self.baum.itemClicked.connect(lambda it, _c: it.parent() is None and it.setExpanded(not it.isExpanded()))   # Gruppen auf-/zuklappen
        self.baum.currentItemChanged.connect(lambda cur, _p: cur and cur.data(0, Qt.UserRole + 1) is not None
                                             and self.stapel.setCurrentIndex(cur.data(0, Qt.UserRole + 1)))
        for wid in self.stapel.findChildren(QWidget):                 # Zeigen auf eine Einstellung erklärt sie unten
            wid.installEventFilter(self)
        self.gehe_zu(seite or "lesehilfe")


    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Enter, QEvent.FocusIn) and isinstance(obj, QWidget):
            w = obj
            while w is not None and not w.property("optName"):
                w = w.parentWidget()
            if w is not None:
                self._erklaere(str(w.property("optName")))
        elif ev.type() == QEvent.Leave:
            self.erklaerzeile.setText(ERKLAERUNG_LEER)
        return super().eventFilter(obj, ev)


    def _erklaere(self, name: str) -> None:
        satz = _erklaerung(name)
        self.erklaerzeile.setText(f"{name} — {satz}" if satz else ERKLAERUNG_LEER)


    def gehe_zu(self, key: str):
        it = self.knoten.get(key) or self.knoten["lesehilfe"]
        self.baum.setCurrentItem(it)


    # ---- Befehlslisten (Menüband, Schnellzugriff): zwei Listen mit Hinzufügen / Entfernen, wie in der Vorlage ---------------------------
    def _band_merken(self) -> None:
        """Die Änderung steht in den Einstellungen; das Band wird beim Verlassen der Seite neu gebaut (nicht bei jedem Klick)."""
        self._band_neu = True


    def _band_jetzt(self, *_a) -> None:
        if getattr(self, "_band_neu", False):
            self._band_neu = False
            QTimer.singleShot(0, self.w.neu_bauen_band)


    def hideEvent(self, ev):
        self._band_jetzt()
        super().hideEvent(ev)


class OptionenDialog(QDialog):
    """Die Optionen als eigenes Fenster (für Aufrufe außerhalb der Datei-Ansicht); gleicher Inhalt wie `OptionenAnsicht`."""

    def __init__(self, fenster, seite: str | None = None):
        super().__init__(fenster)
        self.setWindowTitle("Optionen")
        self.resize(1000, 680)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 8)
        self.ansicht = OptionenAnsicht(fenster, seite)
        self.baum, self.stapel, self.knoten, self.gehe_zu = self.ansicht.baum, self.ansicht.stapel, self.ansicht.knoten, self.ansicht.gehe_zu
        v.addWidget(self.ansicht, 1)
        v.addWidget(knopfzeile(self, ok_text="Fertig", nur_ok=True))
