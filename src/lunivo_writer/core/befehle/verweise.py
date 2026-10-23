"""Befehle: Verweise."""
from __future__ import annotations

from PySide6.QtWidgets import QInputDialog, QMessageBox


class VerweiseBefehle:
    """Befehle des Bandes: Verweise. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Verweise: Beschriftungen, Textmarken, Querverweise, Index, Zitate -------------------------------------
    def beschriftung(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.ui.dialogs.verweise_dialoge import BeschriftungDialog
        d = BeschriftungDialog(self.w)
        if d.exec():
            verweise.beschriftung_einfuegen(self.ed, d.label.currentText(), d.text.text().strip(), oben=d.pos.currentIndex() == 1)


    def _verzeichnis(self, art, titel, leer):
        if not self.ed:
            return
        from lunivo_writer.editor.verzeichnis import verzeichnis_einfuegen
        if verzeichnis_einfuegen(self.ed, art) == 0:
            QMessageBox.information(self.w, titel, leer)


    def abbildungsverzeichnis(self, k=None):
        self._verzeichnis("abb", "Abbildungsverzeichnis", "Es gibt keine Beschriftungen „Abbildung“. Fügen Sie sie über Verweise ▸ Beschriftung ein.")


    def stichwortverzeichnis(self, k=None):
        self._verzeichnis("index", "Stichwortverzeichnis", "Es sind keine Stichwörter markiert. Verwenden Sie Verweise ▸ Indexeintrag.")


    def literaturverzeichnis(self, k=None):
        self._verzeichnis("lit", "Literaturverzeichnis", "Es sind keine Quellen angelegt (Verweise ▸ Neue Quelle).")


    def textmarke(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.verweise_dialoge import TextmarkeDialog
            TextmarkeDialog(self.w, self.ed).exec()


    def querverweis(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.ui.dialogs.verweise_dialoge import QuerverweisDialog
        d = QuerverweisDialog(self.w, self.ed)
        if d.exec():
            ziel, wie = d.ergebnis()
            if ziel:
                verweise.querverweis_einfuegen(self.ed, ziel, wie)


    def indexEintrag(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        c = self.ed.textCursor()
        vorschlag = c.selectedText() if c.hasSelection() else ""
        t, ok = QInputDialog.getText(self.w, "Indexeintrag", "Stichwort:", text=vorschlag)
        if ok and t.strip() and not verweise.index_markieren(self.ed, t.strip()):
            self.w.statusBar().showMessage("Bitte Text markieren oder in ein Wort klicken.", 4000)


    def quelleNeu(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.ui.dialogs.verweise_dialoge import QuelleDialog
        d = QuelleDialog(self.w)
        if d.exec():
            q = d.ergebnis(); q["tag"] = verweise.quelle_tag(self.ed.quellen, q)
            self.ed.quellen.append(q); self.ed.document().setModified(True)


    def quellenVerwalten(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.verweise_dialoge import QuellenDialog
            QuellenDialog(self.w, self.ed).exec()


    def zitat(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.editor.literatur import eintrag
        if not self.ed.quellen:
            QMessageBox.information(self.w, "Zitat", "Es sind noch keine Quellen angelegt. Verwenden Sie „Neue Quelle“.")
            return
        namen = [eintrag(q, self.ed.zitierweise) for q in self.ed.quellen]
        n, ok = QInputDialog.getItem(self.w, "Zitat einfügen", "Quelle:", namen, 0, False)
        if ok:
            verweise.zitat_einfuegen(self.ed, self.ed.quellen[namen.index(n)])


    def zitierweise(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor.literatur import ZITIERWEISEN
        n, ok = QInputDialog.getItem(self.w, "Zitierweise", "Zitierweise:", ZITIERWEISEN, ZITIERWEISEN.index(self.ed.zitierweise) if self.ed.zitierweise in ZITIERWEISEN else 0, False)
        if ok:
            self.ed.zitierweise = n
            self.ed._meta["zitierweise"] = n
            self.ed.document().setModified(True)
