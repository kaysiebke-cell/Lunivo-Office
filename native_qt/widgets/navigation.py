"""Navigationsbereich: die Überschriften des Dokuments als Baum; ein Klick springt dorthin."""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


class NavigationPanel(QWidget):
    def __init__(self, get_editor):
        super().__init__()
        self.get_editor = get_editor
        self.setFixedWidth(240)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 4, 8)
        v.addWidget(QLabel("<b>Überschriften</b>"))
        self.baum = QTreeWidget()
        self.baum.setHeaderHidden(True)
        self.baum.itemClicked.connect(self._klick)
        v.addWidget(self.baum, 1)
        self.leer = QLabel("Keine Überschriften. Formatieren Sie Text mit „Überschrift 1–3“.")
        self.leer.setWordWrap(True)
        self.leer.setStyleSheet("color: palette(mid);")
        v.addWidget(self.leer)
        self._t = QTimer(self)
        self._t.setSingleShot(True)
        self._t.setInterval(400)
        self._t.timeout.connect(self.aktualisieren)

    def spaeter(self):
        if self.isVisible():
            self._t.start()

    def aktualisieren(self):
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
