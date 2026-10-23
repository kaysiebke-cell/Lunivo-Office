"""Befehle: Kommentare, Noten, Änderungen."""
from __future__ import annotations

from PySide6.QtWidgets import QInputDialog, QMessageBox


class KommentarBefehle:
    """Befehle des Bandes: Kommentare, Noten, Änderungen. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Kommentare, Noten, Änderungen ---------------------------------------------------------------
    def _text_abfragen(self, titel, frage, vorgabe=""):
        t, ok = QInputDialog.getMultiLineText(self.w, titel, frage, vorgabe)
        return t.strip() if ok and t.strip() else None


    def kommentar(self, k=None):
        """Neuer Kommentar: das Feld „Kommentare“ links öffnet sich mit dem Eingabefeld; ohne Markierung oder Wort gibt es keinen Anker."""
        if self.ed:
            c = self.ed.textCursor()
            if not c.hasSelection() and not self.ed.document().findBlock(c.position()).text().strip():
                self.w.statusBar().showMessage("Zum Kommentieren Text markieren oder in ein Wort klicken.", 4000)
                return
            self.w.navigation._neu_zeigen()


    def kommentarWeiter(self, k=None):
        if self.ed: self.ed.kommentar_springen(1)


    def kommentarZurueck(self, k=None):
        if self.ed: self.ed.kommentar_springen(-1)


    def kommentarWeg(self, k=None):
        if self.ed and (kid := self.ed.kommentar_am_cursor()) is not None:
            self.ed.kommentar_loeschen(kid)
        else:
            self.w.statusBar().showMessage("Der Zeiger steht in keinem Kommentar.", 4000)


    def kommentareAlleWeg(self, k=None):
        if self.ed and self.ed.kommentare and QMessageBox.question(
                self.w, "Kommentare", "Alle Kommentare im Dokument löschen?") == QMessageBox.Yes:
            self.ed.kommentare_alle_loeschen()


    def _note(self, art, titel):
        """Neue Note: das Zeichen kommt in den Text, unten öffnet sich das Notenfeld mit dem Cursor darin."""
        if self.ed:
            self.w.noten_feld.oeffnen(art, self.ed.note_neu(art, ""))


    def fussnote(self, k=None): self._note("f", "Fußnote einfügen")

    def endnote(self, k=None): self._note("e", "Endnote einfügen")

    def noteWeiter(self, k=None):
        if self.ed: self.ed.note_springen(1)


    def noteZurueck(self, k=None):
        if self.ed: self.ed.note_springen(-1)


    def notenZeigen(self, k=None): self.w.zeige_navigation("noten")


    def note_bearbeiten(self, art, nid):
        if self.ed:
            self.w.noten_feld.oeffnen(art, nid)


    def verfolgen(self, k=None):
        if self.ed:
            self.ed.set_verfolgen(not self.ed.verfolgen)
            self.w.statusBar().showMessage("Änderungen werden verfolgt." if self.ed.verfolgen else "Verfolgung beendet.", 3000)


    def an_verfolgen(self): return bool(self.ed and self.ed.verfolgen)


    def markupUmschalten(self, k=None):
        if self.ed: self.ed.set_markup(not self.ed.markup)


    def an_markupUmschalten(self): return bool(self.ed and self.ed.markup)

    def ueberarbeitungsbereich(self, k=None): self.w.zeige_navigation("aenderungen")


    def aenderungAnnehmen(self, k=None): self._aend_am_cursor(True)

    def aenderungAblehnen(self, k=None): self._aend_am_cursor(False)


    def _aend_am_cursor(self, annehmen):
        if not self.ed:
            return
        b = self.ed.aenderung_am_cursor() or self.ed.aenderung_springen(1)
        if b:
            self.ed.aenderung_annehmen(b, annehmen)
            self.ed.aenderung_springen(1)


    def aenderungWeiter(self, k=None):
        if self.ed: self.ed.aenderung_springen(1)


    def aenderungZurueck(self, k=None):
        if self.ed: self.ed.aenderung_springen(-1)


    def aenderungenUebernehmen(self, k=None):
        if self.ed: self.w.statusBar().showMessage(f"{self.ed.alle_aenderungen(True)} Änderungen angenommen.", 4000)


    def aenderungenVerwerfen(self, k=None):
        if self.ed: self.w.statusBar().showMessage(f"{self.ed.alle_aenderungen(False)} Änderungen abgelehnt.", 4000)
