"""Navigationsbereich links: Überschriften, Kommentare, Änderungen, Noten — ein Klick springt zur Stelle."""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

TABS = ("ueberschriften", "kommentare", "aenderungen", "noten")


class NavigationPanel(QWidget):
    def __init__(self, get_editor):
        super().__init__()
        self.get_editor = get_editor
        self.setFixedWidth(270)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 4, 8)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        v.addWidget(self.tabs)

        # Überschriften
        s1 = QWidget(); v1 = QVBoxLayout(s1); v1.setContentsMargins(0, 6, 0, 0)
        self.baum = QTreeWidget()
        self.baum.setHeaderHidden(True)
        self.baum.itemClicked.connect(self._klick)
        v1.addWidget(self.baum, 1)
        self.leer = QLabel("Keine Überschriften. Formatieren Sie Text mit „Überschrift 1–3“.")
        self.leer.setWordWrap(True)
        self.leer.setStyleSheet("color: palette(mid);")
        v1.addWidget(self.leer)
        self.tabs.addTab(s1, "Überschriften")

        # Kommentare, Änderungen, Noten
        self.liste = {}
        for key, titel, knoepfe in (
                ("kommentare", "Kommentare", (("Löschen", "kommentar_weg"),)),
                ("aenderungen", "Änderungen", (("Annehmen", "aenderung_an"), ("Ablehnen", "aenderung_ab"))),
                ("noten", "Noten", (("Bearbeiten …", "note_bearbeiten"), ("Löschen", "note_weg")))):
            s = QWidget(); v2 = QVBoxLayout(s); v2.setContentsMargins(0, 6, 0, 0)
            lw = QListWidget(); lw.setWordWrap(True)
            lw.itemClicked.connect(lambda it, k=key: self._springe(k, it))
            v2.addWidget(lw, 1)
            reihe = QHBoxLayout()
            for text, name in knoepfe:
                b = QPushButton(text)
                b.clicked.connect(lambda _=False, n=name, k=key: self._aktion(n, k))
                reihe.addWidget(b)
            v2.addLayout(reihe)
            self.liste[key] = lw
            self.tabs.addTab(s, titel)
        self.aktion = None            # Rückruf (name, daten) → Hauptfenster
        self._t = QTimer(self)
        self._t.setSingleShot(True)
        self._t.setInterval(300)
        self._t.timeout.connect(self.aktualisieren)

    def zeige_tab(self, key: str) -> None:
        self.tabs.setCurrentIndex(TABS.index(key))
        self.aktualisieren()

    def spaeter(self):
        if self.isVisible():
            self._t.start()

    def aktualisieren(self):
        self._ueberschriften()
        ed = self.get_editor()
        for k in ("kommentare", "aenderungen", "noten"):
            self.liste[k].clear()
        if ed is None:
            return
        for b in ed.kommentar_bereiche():
            k = ed.kommentare.get(int(b["wert"]), {})
            text = ed.document().toPlainText()[b["von"]:b["bis"]]
            it = QListWidgetItem(f"{k.get('autor', '?')}: {k.get('text', '')}\n→ „{text[:40]}“")
            it.setData(Qt.UserRole, b)
            self.liste["kommentare"].addItem(it)
        for b in ed.aenderungen():
            text = ed.document().toPlainText()[b["von"]:b["bis"]]
            art = "Eingefügt" if b["wert"] == "ins" else "Gelöscht"
            it = QListWidgetItem(f"{art} von {b['cf'].stringProperty(0x100000 + 23) or '?'}: „{text[:50]}“")
            it.setData(Qt.UserRole, b)
            self.liste["aenderungen"].addItem(it)
        zaehler = {"f": 0, "e": 0}
        for s in ed.noten_stellen():
            zaehler[s["art"]] += 1
            txt = ed.noten[s["art"]].get(s["id"], "")
            it = QListWidgetItem(("Fußnote " if s["art"] == "f" else "Endnote ") + f"{zaehler[s['art']]}: {txt[:80]}")
            it.setData(Qt.UserRole, s)
            self.liste["noten"].addItem(it)
        for i, k in enumerate(("kommentare", "aenderungen", "noten"), start=1):
            n = self.liste[k].count()
            self.tabs.setTabText(i, f"{['Kommentare', 'Änderungen', 'Noten'][i - 1]} ({n})" if n else ["Kommentare", "Änderungen", "Noten"][i - 1])

    def _springe(self, key, item):
        ed = self.get_editor()
        b = item.data(Qt.UserRole)
        if ed is not None and b:
            ed.select_range(b["von"], b["bis"])
            ed.ensureCursorVisible()
            ed.setFocus()

    def _aktion(self, name, key):
        it = self.liste[key].currentItem()
        if it is None or self.aktion is None:
            return
        self.aktion(name, it.data(Qt.UserRole))

    def _ueberschriften(self):
        self.baum.clear()
        ed = self.get_editor()
        if ed is None:
            self.leer.show()
            return
        eltern = {0: self.baum.invisibleRootItem()}
        b = ed.document().firstBlock()
        n = 0
        while b.isValid():
            lvl = b.blockFormat().headingLevel()
            if lvl and b.text().strip():
                it = QTreeWidgetItem([b.text().strip()])
                it.setData(0, Qt.UserRole, b.position())
                p = eltern.get(lvl - 1) or eltern[max(k for k in eltern if k < lvl)]
                p.addChild(it)
                eltern[lvl] = it
                for k in [k for k in eltern if k > lvl]:
                    del eltern[k]
                n += 1
            b = b.next()
        self.baum.expandAll()
        self.leer.setVisible(n == 0)

    def _klick(self, item, _col):
        ed = self.get_editor()
        if ed is not None:
            pos = item.data(0, Qt.UserRole)
            ed.select_range(pos, pos)
            ed.ensureCursorVisible()
