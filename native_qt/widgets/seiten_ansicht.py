"""Zwei-Seiten-Ansicht: die Seiten des Dokuments nebeneinander, so wie sie gedruckt werden (nur zum Ansehen)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget

from ..editor.page import mm_to_px
from ..editor.pagination import ausgabe_seiten, paginated_copy, seite_als_bild


class SeitenAnsicht(QWidget):
    def __init__(self, editor, breite: int):
        super().__init__()
        self.setBackgroundRole(self.backgroundRole().Dark)
        self.setAutoFillBackground(True)
        lay = QGridLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setHorizontalSpacing(16)
        lay.setVerticalSpacing(16)
        pg = editor.page
        faktor = max(0.25, min(1.2, (breite - 16 * 4) / 2 / mm_to_px(pg.width_mm)))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            d = paginated_copy(editor.document(), pg, editor.noten)
            self.seiten = ausgabe_seiten(d.pageCount(), pg)
            for n in range(1, self.seiten + 1):
                bild = seite_als_bild(editor.document(), pg, n, faktor, d)
                lab = QLabel()
                lab.setPixmap(QPixmap.fromImage(bild))
                lab.setFixedSize(bild.size())
                lab.setStyleSheet("border: 1px solid #5c6166;")
                lay.addWidget(lab, (n - 1) // 2, (n - 1) % 2, Qt.AlignTop | (Qt.AlignRight if n % 2 else Qt.AlignLeft))
        finally:
            QApplication.restoreOverrideCursor()
        lay.setRowStretch(lay.rowCount(), 1)
        lay.setColumnStretch(0, 1); lay.setColumnStretch(1, 1)
