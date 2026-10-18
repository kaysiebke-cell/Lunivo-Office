"""Ein geöffnetes Dokument: Editor auf grauem Arbeitsgrund, Pfad, Meta, Wiederherstellungs-Kennung."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from ..document_io.formats import Loaded
from ..editor.editor_widget import DocumentEditor
from ..editor.page import PageSettings
from ..storage import recovery


class DocumentTab(QScrollArea):
    def __init__(self, loaded: Loaded | None = None, path: str | None = None, title: str | None = None):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setBackgroundRole(self.backgroundRole().Dark)
        holder = QWidget()
        holder.setBackgroundRole(holder.backgroundRole().Dark)
        holder.setAutoFillBackground(True)
        lay = QHBoxLayout(holder)
        lay.setContentsMargins(24, 16, 24, 16)
        self.editor = DocumentEditor()
        self.editor.setStyleSheet("QTextEdit { background: white; color: black; }")
        lay.addStretch(1)
        lay.addWidget(self.editor)
        lay.addStretch(1)
        self.setWidget(holder)
        self.path = path
        self.title = title or (os.path.basename(path) if path else "Unbenannt")
        self.meta: dict = {}
        self.token = recovery.new_token()
        self.untitled = path is None
        if loaded is not None:
            self.editor.set_document_and_page(loaded.doc, loaded.page)
            self.meta = loaded.meta
        self.editor.document().setDefaultFont(self.editor.document().defaultFont())

    @property
    def page(self) -> PageSettings:
        return self.editor.page

    def is_modified(self) -> bool:
        return self.editor.document().isModified()

    def set_path(self, path: str) -> None:
        self.path = path
        self.untitled = False
        self.title = os.path.basename(path)
