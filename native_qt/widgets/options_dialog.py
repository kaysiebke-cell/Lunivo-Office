from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QVBoxLayout

THEMES = [("system", "Wie das System"), ("light", "Hell"), ("dark", "Dunkel")]


class OptionsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optionen")
        self.s = settings
        self.theme = QComboBox()
        for key, label in THEMES:
            self.theme.addItem(label, key)
        i = self.theme.findData(settings.get("theme", "system"))
        self.theme.setCurrentIndex(max(0, i))
        self.autosave = QSpinBox(); self.autosave.setRange(10, 3600); self.autosave.setSuffix(" s")
        self.autosave.setValue(settings.get_int("autosave_seconds", 60))
        form = QFormLayout(); form.addRow("Darstellung", self.theme)
        form.addRow("Automatische Sicherung alle", self.autosave)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)

    def accept(self):
        self.s.set("theme", self.theme.currentData())
        self.s.set("autosave_seconds", self.autosave.value())
        super().accept()
