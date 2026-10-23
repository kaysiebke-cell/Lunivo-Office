"""Abschnitte, Seitenzählung, Paginierung."""
from __future__ import annotations

from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QTextEdit
from lunivo_writer.models.page import PageSettings
from lunivo_writer.editor.pagination import paginated_copy


class SeitenBaustein:
    """Abschnitte, Seitenzählung, Paginierung. Baustein von ``DocumentEditor`` (siehe ``lunivo_writer/ui/document/document_editor.py``)."""


    # ---- Abschnitte ----------------------------------------------------------------------------------------------------
    def abschnitt_nr(self) -> int:
        from lunivo_writer.editor import abschnitte as AB
        return AB.index_bei(self.document(), self.textCursor().position())


    def abschnitt_seite(self, nr: int | None = None) -> PageSettings:
        """Kopie der Einrichtung des Abschnitts `nr` (Vorgabe: des aktuellen)."""
        from lunivo_writer.editor import abschnitte as AB
        return AB.einrichtung(self.document(), self.page, self.abschnitt_nr() if nr is None else nr)


    def abschnitt_einfuegen(self, typ: str = "naechste") -> int:
        from lunivo_writer.editor import abschnitte as AB
        c = self.textCursor()
        nr = AB.einfuegen(self.document(), c, typ, self.page)
        self.setTextCursor(c)
        self.document().setModified(True)
        self._recount()
        return nr


    def abschnitt_entfernen(self) -> bool:
        from lunivo_writer.editor import abschnitte as AB
        ok = AB.entfernen(self.document(), self.abschnitt_nr())
        if ok:
            self.document().setModified(True)
            self._recount()
            self.viewport().update()
        return ok


    def abschnitt_gehe(self, nr: int) -> bool:
        from lunivo_writer.editor import abschnitte as AB
        n = AB.anzahl(self.document())
        if not 0 <= nr < n:
            return False
        c = self.textCursor()
        c.setPosition(AB.beginn(self.document(), nr))
        self.setTextCursor(c)
        self.ensureCursorVisible()
        return True


    # ---- Seitenzählung & Echte Paginierung ----------------------------------
    def _recount(self) -> None:
        """Seitenzahl und Seitenwechsel neu bestimmen. Die Blätter selbst entstehen aus dem Textfluss des Editors; die
        Druckkopie liefert Seitenwechsel für „Gehe zu“ und die Seiten, die erst der Druck anhängt (Endnoten)."""
        live = self._blatt_anzahl() - self._extra_seiten
        if self.web:
            self._paged, self._breaks, self._pages, self._extra_seiten = None, [], 1, 0
        elif self._mehrspaltig():                      # die Spaltenseiten stammen aus dem Editor-Dokument selbst
            self._paged = None
            self._breaks = []
            self._pages = live
            self._extra_seiten = 0
        else:
            self._paged = paginated_copy(self.document(), self.page, self.noten, silben=False, einspaltig=True, versteckt=self.versteckt_zeigen, lese_luft=True)
            self._breaks = self._seitenwechsel(self._paged)
            druck = max(1, self._paged.pageCount())
            from lunivo_writer.editor import abschnitte as AB
            if AB.anzahl(self.document()) > 1:
                from lunivo_writer.editor.pagination import seitenzahl
                druck = max(1, seitenzahl(self.document(), self.page, self.noten))
            self._extra_seiten = max(0, druck - live)
            self._pages = live + self._extra_seiten
        self._passe_hoehe_an()
        self.viewport().update()
        self._cursor_moved()


    def _seitenwechsel(self, d: QTextDocument) -> list[int]:
        """Zeichenstellen, an denen eine neue Seite beginnt (erste Zeile der Seiten 2, 3, …)."""
        ch = self.page.content_height_px
        lay = d.documentLayout()
        stellen, seite = [], 0
        b = d.firstBlock()
        while b.isValid():
            tl = b.layout()
            if tl is not None and tl.lineCount():
                top = lay.blockBoundingRect(b).top()
                for i in range(tl.lineCount()):
                    ln = tl.lineAt(i)
                    k = int((top + ln.y() + 0.5) // ch)
                    if k > seite:
                        seite = k
                        stellen.append(b.position() + ln.textStart())
            b = b.next()
        return stellen


    @property
    def seitenwechsel(self) -> list[int]:
        return list(self._breaks)


    @property
    def page_count(self) -> int:
        return self._pages


    def current_page(self) -> int:
        """Blatt, auf dem die Schreibmarke steht (so, wie es im Editor angezeigt wird)."""
        if self.web:
            return 1
        g = self._sp_geo()
        r = QTextEdit.cursorRect(self)
        return max(1, min(self._pages, int((r.y() + 1.0) // g["ch"]) // g["n"] + 1))


    def _cursor_moved(self) -> None:
        try:
            self.pageInfoChanged.emit(self.current_page(), self._pages)
            self.formatChanged.emit()
        except RuntimeError:                           # beim Abbau ist das Widget schon weg
            return
        if self.opt_text("ui/feldschattierung", "Bei Auswahl") == "Bei Auswahl":
            self._zus_timer.start()
        hl = getattr(self, "_silben", None)
        if hl is not None and hl.k["nur_absatz"]:
            neu = self.textCursor().blockNumber()
            if neu != getattr(self, "_silben_block", -1):
                for n in (getattr(self, "_silben_block", -1), neu):
                    b = self.document().findBlockByNumber(n)
                    if b.isValid():
                        hl.rehighlightBlock(b)
                self._silben_block = neu


    def set_silbenfarben(self, konfig: dict | None) -> None:
        """Silben farbig (reine Anzeige, ändert das Dokument nicht); konfig None oder an=False schaltet ab."""
        from lunivo_writer.editor.silbenfarben import SilbenFarben
        hl = getattr(self, "_silben", None)
        if not konfig or not konfig["an"]:
            if hl is not None:
                hl.setDocument(None)
                self._silben = None
            return
        if hl is None:
            self._silben_block = self.textCursor().blockNumber()
            self._silben = SilbenFarben(self.document(), konfig, lambda: self.textCursor().blockNumber())
        else:
            hl.neu_konfigurieren(konfig)


    def word_count(self) -> int:
        return len(self.document().toPlainText().split())
