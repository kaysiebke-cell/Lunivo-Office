"""Notenfeld unten im Fenster: hier schreibt man den Text einer Fuß- oder Endnote, direkt nach dem Einfügen oder nach einem Klick auf das Zeichen im Text.

Dieselbe Quelle wie das Feld „Noten“ links (`editor.noten[art][id]`): was hier getippt wird, steht sofort dort und in der Seitenansicht."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPlainTextEdit

from lunivo_writer.editor.zusatz import roemisch
from lunivo_writer.ui.baukasten.panel_rahmen import PanelRahmen


class _Eingabe(QPlainTextEdit):
    fertig = Signal()

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key_Escape:
            self.fertig.emit()
            return
        super().keyPressEvent(e)


class NotenFeld(PanelRahmen):
    """``get_editor``: liefert den aktuellen Editor. Zeigt sich mit `oeffnen(art, id)`, schließt mit ✕, Esc oder `zumachen()`."""
    geaendert = Signal()

    def __init__(self, get_editor):
        super().__init__("Fußnote")
        self.get_editor = get_editor
        self._art, self._nid = "f", 0
        self._lade = False
        self.eingabe = _Eingabe()
        self.eingabe.setFixedHeight(84)
        self.eingabe.setPlaceholderText("Text der Note …")
        self.eingabe.setAccessibleName("Text der Note")
        self.eingabe.textChanged.connect(self._getippt)
        self.eingabe.fertig.connect(self.zumachen)
        self.inhalt.addWidget(self.eingabe)
        PanelRahmen.schliessen.__get__(self).connect(self.zumachen)
        self.hide()

    def oeffnen(self, art: str, nid: int) -> None:
        ed = self.get_editor()
        if ed is None:
            return
        self._art, self._nid = art, nid
        nr = next((i for i, s in enumerate([s for s in ed.noten_stellen() if s["art"] == art], start=1) if s["id"] == nid), 0)
        zeichen = str(nr) if art == "f" else roemisch(nr)
        self.titel.setText(("Fußnote " if art == "f" else "Endnote ") + zeichen)
        self._lade = True
        self.eingabe.setPlainText(ed.noten[art].get(nid, ""))
        self._lade = False
        self.show()
        self.eingabe.setFocus()
        self.eingabe.moveCursor(self.eingabe.textCursor().MoveOperation.End)

    def _getippt(self) -> None:
        ed = self.get_editor()
        if self._lade or ed is None or self._nid not in ed.noten[self._art]:
            return
        ed.noten[self._art][self._nid] = self.eingabe.toPlainText()
        ed.document().setModified(True)
        ed.notentext_geaendert()
        self.geaendert.emit()

    def zumachen(self) -> None:
        self.hide()
        ed = self.get_editor()
        if ed is not None:
            ed.setFocus()
