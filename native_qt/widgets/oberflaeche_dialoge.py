"""Oberfläche anpassen: Register (Reiter) auswählen und ordnen, Schnellzugriff, Symbole austauschen, Oberfläche wählen."""
from __future__ import annotations

import json

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QRadioButton, QVBoxLayout,
)

from . import icons
from .reiterplan import plan

IMMER = ("Datei",)          # dieser Reiter lässt sich nicht ausblenden


def lade_json(settings, key: str, standard):
    try:
        v = json.loads(settings.get(key, "") or "null")
        return standard if v is None else v
    except ValueError:
        return standard


class RegisterAnpassenDialog(QDialog):
    """Reiter ein-/ausblenden und umordnen — wie „Menüband anpassen“ in WPS."""

    def __init__(self, parent, settings, daten: dict):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Register anpassen")
        self.resize(420, 460)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Haken = Reiter wird gezeigt. Mit den Pfeilen ändern Sie die Reihenfolge."))
        self.liste = QListWidget()
        v.addWidget(self.liste)
        namen = [r["name"] for r in plan(daten) if not r.get("kontext")]
        cfg = lade_json(settings, "ui/register_plan", {})
        reihenfolge = [n for n in cfg.get("reihenfolge", []) if n in namen] + [n for n in namen if n not in cfg.get("reihenfolge", [])]
        versteckt = set(cfg.get("versteckt", []))
        for n in reihenfolge:
            it = QListWidgetItem(n)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked if n in versteckt else Qt.Checked)
            if n in IMMER:
                it.setFlags(it.flags() & ~Qt.ItemIsUserCheckable)
            self.liste.addItem(it)
        z = QHBoxLayout()
        for text, d in (("▲ Nach oben", -1), ("▼ Nach unten", 1)):
            b = QPushButton(text); b.clicked.connect(lambda _=False, d=d: self._schieben(d)); z.addWidget(b)
        v.addLayout(z)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._speichern); bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _schieben(self, d: int):
        i = self.liste.currentRow(); j = i + d
        if i < 0 or not 0 <= j < self.liste.count():
            return
        it = self.liste.takeItem(i)
        self.liste.insertItem(j, it)
        self.liste.setCurrentRow(j)

    def _speichern(self):
        namen = [self.liste.item(i).text() for i in range(self.liste.count())]
        versteckt = [self.liste.item(i).text() for i in range(self.liste.count())
                     if self.liste.item(i).checkState() == Qt.Unchecked and self.liste.item(i).text() not in IMMER]
        self.settings.set("ui/register_plan", json.dumps({"reihenfolge": namen, "versteckt": versteckt}))
        self.accept()


class SchnellzugriffDialog(QDialog):
    """Welche Knöpfe in der Schnellzugriffsleiste neben dem ☰-Menü stehen."""

    def __init__(self, parent, settings, alle: list[tuple[str, str, str]], aktuell: list[str]):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Symbolleiste für den Schnellzugriff")
        self.resize(420, 480)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Haken = Knopf steht in der Schnellzugriffsleiste."))
        self.liste = QListWidget()
        v.addWidget(self.liste)
        for sym, name, aktion in alle:
            it = QListWidgetItem(icons.icon(sym, 18), name)
            it.setData(Qt.UserRole, aktion)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if aktion in aktuell else Qt.Unchecked)
            self.liste.addItem(it)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._speichern); bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _speichern(self):
        gewaehlt = [self.liste.item(i).data(Qt.UserRole) for i in range(self.liste.count())
                    if self.liste.item(i).checkState() == Qt.Checked]
        self.settings.set("ui/schnellzugriff", json.dumps(gewaehlt))
        self.accept()


class SymbolTauschenDialog(QDialog):
    """Ein Symbol des Programms durch eines der 1800 Lucide-Symbole ersetzen."""

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Symbol austauschen")
        self.resize(720, 520)
        self.tausch = lade_json(settings, "ui/symbol_tausch", {})
        h = QHBoxLayout(self)
        links = QVBoxLayout(); rechts = QVBoxLayout()
        h.addLayout(links, 1); h.addLayout(rechts, 2)
        links.addWidget(QLabel("1. Welches Symbol?"))
        self.such_a = QLineEdit(); self.such_a.setPlaceholderText("Suchen …"); links.addWidget(self.such_a)
        self.alt = QListWidget(); self.alt.setIconSize(QSize(22, 22)); links.addWidget(self.alt)
        rechts.addWidget(QLabel("2. Wodurch? (Name auf Englisch, z. B. heart, printer, star)"))
        self.such_b = QLineEdit(); rechts.addWidget(self.such_b)
        self.neu = QListWidget(); self.neu.setViewMode(QListWidget.IconMode); self.neu.setIconSize(QSize(36, 36))
        self.neu.setGridSize(QSize(92, 66)); self.neu.setResizeMode(QListWidget.Adjust); rechts.addWidget(self.neu)
        z = QHBoxLayout()
        for text, fn in (("Austauschen", self._tauschen), ("Dieses Symbol zurücksetzen", self._zurueck)):
            b = QPushButton(text); b.clicked.connect(fn); z.addWidget(b)
        rechts.addLayout(z)
        bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(self.accept); rechts.addWidget(bb)
        self.such_a.textChanged.connect(self._fuelle_alt); self.such_b.textChanged.connect(self._fuelle_neu)
        self._fuelle_alt(""); self._fuelle_neu("")

    def _fuelle_alt(self, q):
        self.alt.clear()
        q = q.lower().strip()
        for n in sorted(icons.pfade_original()):
            if q and q not in n.lower():
                continue
            it = QListWidgetItem(icons.icon(n, 22), n + ("  →  " + self.tausch[n] if n in self.tausch else ""))
            it.setData(Qt.UserRole, n)
            self.alt.addItem(it)

    def _fuelle_neu(self, q):
        self.neu.clear()
        q = q.lower().strip()
        k = 0
        for n in sorted(icons.katalog()):
            if q and q not in n:
                continue
            it = QListWidgetItem(QIcon(QPixmap.fromImage(icons.katalog_bild(n, 36, "#444444"))), n)
            it.setData(Qt.UserRole, n)
            self.neu.addItem(it)
            k += 1
            if k >= 200:
                break

    def _tauschen(self):
        a, n = self.alt.currentItem(), self.neu.currentItem()
        if not a or not n:
            QMessageBox.information(self, "Symbol austauschen", "Links ein Symbol und rechts das neue wählen.")
            return
        self.tausch[a.data(Qt.UserRole)] = n.data(Qt.UserRole)
        self._speichern(); self._fuelle_alt(self.such_a.text())

    def _zurueck(self):
        a = self.alt.currentItem()
        if a and a.data(Qt.UserRole) in self.tausch:
            del self.tausch[a.data(Qt.UserRole)]
            self._speichern(); self._fuelle_alt(self.such_a.text())

    def _speichern(self):
        self.settings.set("ui/symbol_tausch", json.dumps(self.tausch))
        icons.uebersteuern(self.tausch)


class OberflaecheDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowTitle("Benutzeroberfläche")
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Wie sollen die Befehle angeordnet sein?"))
        self.reg = QRadioButton("Register (Menüband mit Reitern, wie in WPS Office)")
        self.sym = QRadioButton("Symbolleisten (zwei Zeilen mit Knöpfen, wie im früheren Lunivo)")
        (self.sym if settings.get("ui/oberflaeche", "register") == "symbolleisten" else self.reg).setChecked(True)
        v.addWidget(self.reg); v.addWidget(self.sym)
        self.menue = QCheckBox("Menüleiste zusätzlich anzeigen")
        self.menue.setChecked(settings.get_bool("ui/menueleiste", False))
        v.addWidget(self.menue)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)

    def wahl(self) -> str:
        return "symbolleisten" if self.sym.isChecked() else "register"
