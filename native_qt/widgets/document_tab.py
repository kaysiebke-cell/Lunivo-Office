"""Ein geöffnetes Dokument: Editor auf grauem Arbeitsgrund, Pfad, Meta, Wiederherstellungs-Kennung."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from ..document_io.formats import Loaded
from ..editor.editor_widget import DocumentEditor
from ..editor.page import PageSettings
from ..storage import recovery


class DocumentTab(QScrollArea):
    layout_geaendert = Signal(str)

    def __init__(self, loaded: Loaded | None = None, path: str | None = None, title: str | None = None):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setBackgroundRole(self.backgroundRole().Dark)
        holder = QWidget()
        holder.setBackgroundRole(holder.backgroundRole().Dark)
        holder.setAutoFillBackground(True)
        lay = QHBoxLayout(holder)
        lay.setContentsMargins(12, 12, 12, 12)
        self.editor = DocumentEditor()
        from .lineal import LinealH, LinealV
        spalte = QVBoxLayout(); spalte.setSpacing(0); spalte.setContentsMargins(0, 0, 0, 0)
        reihe = QHBoxLayout(); reihe.setSpacing(0); reihe.setContentsMargins(0, 0, 0, 0)
        self.lineal_h = LinealH(self.editor); self.lineal_v = LinealV(self.editor)
        self.lineal_h.hide(); self.lineal_v.hide()
        self.lineal_h.randGeaendert.connect(self._rand)
        self.lineal_v.randGeaendert.connect(self._rand)
        self.lineal_h.einzugGeaendert.connect(lambda l, r, f: self.editor.set_indents(l, r, f))
        links = QVBoxLayout(); links.setSpacing(0); links.setContentsMargins(0, 0, 0, 0)
        self._abstand = QWidget(); self._abstand.setFixedSize(1, 22); self._abstand.hide()
        links.addWidget(self._abstand); links.addWidget(self.lineal_v); links.addStretch(1)
        rechts = QVBoxLayout(); rechts.setSpacing(0); rechts.setContentsMargins(0, 0, 0, 0)
        rechts.addWidget(self.lineal_h); rechts.addWidget(self.editor); rechts.addStretch(1)
        reihe.addLayout(links); reihe.addLayout(rechts)
        lay.addStretch(1)
        lay.addLayout(reihe)
        lay.setAlignment(reihe, Qt.AlignTop)
        lay.addStretch(1)
        self.setWidget(holder)
        self._holder = holder
        self.layout_art = "blatt"
        self.path = path
        self.title = title or (os.path.basename(path) if path else "Unbenannt")
        self.meta: dict = {}
        self.token = recovery.new_token()
        self.untitled = path is None
        if loaded is not None:
            self.editor.set_document_and_page(loaded.doc, loaded.page)
            self.meta = loaded.meta
        self.editor.document().setDefaultFont(self.editor.document().defaultFont())
        self.editor.zusatz_binden(self.meta)

    def set_layout(self, art: str) -> None:
        """blatt (Drucklayout) | web (Weblayout) | doppelt (Zwei Seiten, nur Ansicht)."""
        from .seiten_ansicht import SeitenAnsicht
        if self.layout_art == "doppelt" and art != "doppelt":
            alt = self.takeWidget()
            if alt is not self._holder and alt is not None:
                alt.deleteLater()
            self.setWidget(self._holder)
            self._holder.show()
        self.layout_art = art
        self.editor.set_web(art == "web")
        if art == "web":
            self.editor.set_web_breite(self.viewport().width() - 24 - 22)
        if art == "doppelt":
            ansicht = SeitenAnsicht(self.editor, self.viewport().width())
            self.takeWidget()
            self._holder.hide()
            self.setWidget(ansicht)
        self.layout_geaendert.emit(art)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.layout_art == "web":
            self.editor.set_web_breite(self.viewport().width() - 24 - 22)

    def _rand(self, seite: str, mm: float) -> None:
        pg = self.editor.page.copy()
        setattr(pg, {"links": "margin_left_mm", "rechts": "margin_right_mm", "oben": "margin_top_mm",
                     "unten": "margin_bottom_mm"}[seite], mm)
        self.editor.page_settings_changed(pg)

    def zeige_lineale(self, waagerecht: bool, senkrecht: bool) -> None:
        self.lineal_h.setVisible(waagerecht)
        self.lineal_v.setVisible(senkrecht)
        self._abstand.setVisible(waagerecht)
        if waagerecht or senkrecht:
            self.lineal_h._neu(); self.lineal_v._neu()

    def zoom_breite(self) -> None:
        """Seitenbreite: die Seite füllt die Breite des Fensters."""
        from ..editor.page import mm_to_px
        frei = self.viewport().width() - 24 - 2
        self.editor.set_zoom(frei / mm_to_px(self.page.width_mm))

    def zoom_seite(self) -> None:
        """Eine Seite: die ganze Seite ist sichtbar."""
        from ..editor.page import mm_to_px
        b = (self.viewport().width() - 24 - 2) / mm_to_px(self.page.width_mm)
        h = (self.viewport().height() - 24 - 2) / mm_to_px(self.page.height_mm)
        self.editor.set_zoom(min(b, h))

    @property
    def page(self) -> PageSettings:
        return self.editor.page

    def is_modified(self) -> bool:
        return self.editor.document().isModified()

    def set_path(self, path: str) -> None:
        self.path = path
        self.untitled = False
        self.title = os.path.basename(path)
