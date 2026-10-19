"""Live-Vorschau: Beim Überfahren einer Formatvorlage, Schrift, Größe oder Farbe zeigt das Dokument das Ergebnis schon — ohne dass etwas
übernommen wird. Technik: Die Vorschau wird wirklich angewendet (ein Rückgängig-Schritt) und beim Verlassen wieder zurückgenommen;
Wiederholen-Schritte und der „geändert“-Zustand werden danach wiederhergestellt. Abschaltbar: Optionen ▸ Ansicht ▸ Live-Vorschau."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QComboBox, QFontComboBox


class LiveVorschau:
    def __init__(self, fenster):
        self.w = fenster
        self._ed = None
        self._schritte = 0
        self._modified = False
        self._format = None

    @property
    def aktiv(self) -> bool:
        return self._ed is not None

    def zeigen(self, anwenden) -> None:
        """anwenden(editor) wendet das Format an; es wird beim nächsten `ende()` zurückgenommen."""
        if not self.w.settings.get_bool("ui/live_vorschau", True):
            return
        self.ende()
        ed = self.w.current_editor()
        if ed is None or ed.isReadOnly():
            return
        doc = ed.document()
        vorher = doc.availableUndoSteps()
        self._ed, self._modified, self._format = ed, doc.isModified(), ed.currentCharFormat()
        try:
            anwenden(ed)
        except Exception:                                    # noqa: BLE001 — eine Vorschau darf nie etwas kaputt machen
            self._schritte = max(0, doc.availableUndoSteps() - vorher)
            self.ende()
            return
        self._schritte = max(0, doc.availableUndoSteps() - vorher)

    def ende(self) -> None:
        ed, self._ed = self._ed, None
        if ed is None:
            return
        try:
            doc = ed.document()
            for _ in range(self._schritte):
                doc.undo()
            if self._schritte:
                doc.clearUndoRedoStacks(QTextDocument.RedoStack)   # sonst würde Strg+Y die Vorschau „wiederholen“
            else:
                ed.setCurrentCharFormat(self._format)               # ohne Markierung ändert die Vorschau nur das Format am Zeiger
            doc.setModified(self._modified)
        except RuntimeError:                                         # Editor schon geschlossen
            pass
        self._schritte = 0


class Ueberfahren(QObject):
    """Event-Filter: Zeiger über dem Knopf → Vorschau, Zeiger weg oder Klick → Vorschau beenden."""

    def __init__(self, vorschau: LiveVorschau, anwenden):
        super().__init__()
        self.v, self.f = vorschau, anwenden

    def eventFilter(self, o, e):
        t = e.type()
        if t == QEvent.Enter:
            self.v.zeigen(self.f)
        elif t in (QEvent.Leave, QEvent.MouseButtonPress, QEvent.Hide):
            self.v.ende()
        return False


class VorschauCombo(QComboBox):
    """Auswahlfeld, dessen Einträge beim Überfahren (highlighted) als Vorschau gezeigt werden."""

    def __init__(self, vorschau_fn, ende_fn, parent=None):
        super().__init__(parent)
        self._ende = ende_fn
        self.highlighted.connect(lambda i: vorschau_fn(self.itemText(i)))

    def hidePopup(self) -> None:
        self._ende()
        super().hidePopup()


class VorschauFontCombo(QFontComboBox):
    def __init__(self, vorschau_fn, ende_fn, parent=None):
        super().__init__(parent)
        self._ende = ende_fn
        self.highlighted.connect(lambda i: vorschau_fn(self.itemText(i)))

    def hidePopup(self) -> None:
        self._ende()
        super().hidePopup()
