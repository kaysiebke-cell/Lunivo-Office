"""Neu aus Vorlage: die mitgelieferten Gerüste und die Dateien aus dem Vorlagenordner."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTabWidget, QVBoxLayout,
    QWidget,
)

from lunivo_writer.editor import vorlagen


class VorlagenDialog(QDialog):
    def __init__(self, parent, settings, kann_speichern: bool):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Neu aus Vorlage")
        self.resize(560, 460)
        self.auswahl = None            # ("geruest", dict) | ("datei", pfad)
        v = QVBoxLayout(self)
        self.tabs = QTabWidget(); v.addWidget(self.tabs)
        s1 = QWidget(); v1 = QVBoxLayout(s1)
        v1.addWidget(QLabel("Leere Gerüste: nur der Aufbau, in jeder Lücke steht, was dort hingehört. Tab springt zur nächsten Lücke."))
        self.geruest = QListWidget()
        for m in vorlagen.muster():
            it = QListWidgetItem(f"{m['name']} — {m['beschreibung']}"); it.setData(Qt.UserRole, m); self.geruest.addItem(it)
        self.geruest.itemDoubleClicked.connect(lambda _: self._ok())
        v1.addWidget(self.geruest)
        self.tabs.addTab(s1, "Gerüste")
        s2 = QWidget(); v2 = QVBoxLayout(s2)
        self.ordner_lab = QLabel(); self.ordner_lab.setWordWrap(True); v2.addWidget(self.ordner_lab)
        self.eigene = QListWidget(); self.eigene.itemDoubleClicked.connect(lambda _: self._ok()); v2.addWidget(self.eigene)
        z = QHBoxLayout()
        for text, fn in (("Ordner wählen …", self._ordner_waehlen), ("Ordner öffnen", self._ordner_oeffnen)):
            b = QPushButton(text); b.clicked.connect(fn); z.addWidget(b)
        if kann_speichern:
            b = QPushButton("Dokument als Vorlage speichern …"); b.clicked.connect(self._als_vorlage); z.addWidget(b)
        v2.addLayout(z)
        self.tabs.addTab(s2, "Meine Vorlagen")
        self.als_vorlage_gewuenscht = False
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok); bb.rejected.connect(self.reject); v.addWidget(bb)
        self._fuellen()

    def _fuellen(self):
        ordner = vorlagen.vorlagenordner(self.settings)
        self.ordner_lab.setText(f"Vorlagenordner: {ordner}")
        self.eigene.clear()
        liste = vorlagen.eigene_vorlagen(ordner)
        for p in liste:
            it = QListWidgetItem(os.path.basename(p)); it.setData(Qt.UserRole, p); self.eigene.addItem(it)
        if not liste:
            self.eigene.addItem("(Der Ordner enthält noch keine Vorlagen — .docx, .dotx, .odt oder .txt)")
            self.eigene.item(0).setFlags(Qt.NoItemFlags)

    def _ordner_waehlen(self):
        p = QFileDialog.getExistingDirectory(self, "Vorlagenordner", vorlagen.vorlagenordner(self.settings))
        if p:
            self.settings.set("vorlagen/ordner", p); self._fuellen()

    def _ordner_oeffnen(self):
        o = vorlagen.vorlagenordner(self.settings)
        os.makedirs(o, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(o))

    def _als_vorlage(self):
        self.als_vorlage_gewuenscht = True
        self.accept()

    def _ok(self):
        if self.tabs.currentIndex() == 0 and self.geruest.currentItem():
            self.auswahl = ("geruest", self.geruest.currentItem().data(Qt.UserRole))
        elif self.tabs.currentIndex() == 1 and self.eigene.currentItem() and self.eigene.currentItem().data(Qt.UserRole):
            self.auswahl = ("datei", self.eigene.currentItem().data(Qt.UserRole))
        if self.auswahl:
            self.accept()
