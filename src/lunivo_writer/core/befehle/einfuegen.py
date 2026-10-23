"""Befehle: Einfügen."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QMessageBox
from lunivo_writer.core.befehle.hilfen import _farbfeld


class EinfuegenBefehle:
    """Befehle des Bandes: Einfügen. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Einfügen -------------------------------------------------------------------------------------------------
    def seitenumbruch(self, k=None):
        if self.ed: self.ed.insert_page_break()


    def tabelleRaster(self, k=None):
        self.w.insert_table()


    def bild(self, k=None):
        self.w.insert_image()


    def hyperlink(self, k=None):
        self.w.insert_link()


    def kopfFussZeigen(self, k=None):
        self.w.edit_header_footer(True)


    def menue_seitenzahlKlappe(self):
        m = QMenu()
        m.addAction("Seitenzahl in die Fußzeile", self.w.insert_page_number)
        return m


    def seitenzahlKlappe(self, k=None):
        self.w.insert_page_number()


    # ==== Einfügen ===========================================================================================================
    def leereSeite(self, k=None, quer=False):
        if self.ed:
            self.ed.insert_page_break(); self.ed.insert_page_break()


    def sonderzeichen(self, k=None):
        from lunivo_writer.ui.dialogs.sonderzeichen import SonderzeichenDialog
        e = self.ed
        if e:
            d = SonderzeichenDialog(self.w, lambda z: e.insertPlainText(z))
            d.show()
            self._sz = d


    def inhaltsverzeichnis(self, k=None):
        if self.ed:
            from lunivo_writer.editor.verzeichnis import verzeichnis_einfuegen
            n = verzeichnis_einfuegen(self.ed)
            if not n:
                QMessageBox.information(self.w, "Inhaltsverzeichnis", "Im Dokument gibt es keine Überschriften. "
                                        "Formatieren Sie Überschriften mit den Stilen „Überschrift 1–3“.")


    def verzeichnisseAktualisieren(self, k=None):
        if self.ed:
            from lunivo_writer.editor.verzeichnis import verzeichnis_aktualisieren
            verzeichnis_aktualisieren(self.ed)


    # ---- Einfügen: Illustrationen, Text, Symbole, Tabellen, Seiten ----------------------------------------------------
    def _bild_einfuegen(self, img, alt, art=None, daten=None):
        from lunivo_writer.editor import einfuegen as E
        E.qimage_einfuegen(self.ed, img, alt, art, daten)


    def formenGalerie(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import einfuegen as E
        m = QMenu()
        for f in E.FORMEN:
            m.addAction(f, lambda _=False, f=f: self._bild_einfuegen(E.form_bild(f), f"Form: {f}", "form", {"form": f}))
        m.addSeparator()
        m.addAction("Weitere Formen und Farben …", self.zeichnen)
        self._popup(m)


    def zeichnen(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import FormDialog
            d = FormDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), f"Form: {d.art.currentText()}", "form", d.daten())


    def smartart(self, k=None):
        if self.ed:
            from lunivo_writer.editor import smartart as SA
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import SmartArtDialog
            d = SmartArtDialog(self.w)
            if d.exec():
                SA.einfuegen(self.ed, d.daten())


    def smartartText(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import smartart as SA
        from lunivo_writer.ui.dialogs.einfuegen_dialoge import SmartArtDialog
        daten = SA.daten_der_auswahl(self.ed)
        if daten is None:
            self.w.statusBar().showMessage("Bitte zuerst ein SmartArt-Bild auswählen (Schreibmarke davor oder Bild markieren).", 5000)
            return
        d = SmartArtDialog(self.w, daten)
        if d.exec():
            SA.aendern(self.ed, **d.daten())


    def menue_smartartLayout(self):
        from lunivo_writer.editor import smartart as SA
        m = QMenu()
        for n in SA.LAYOUTS:
            m.addAction(n, lambda _=False, n=n: self.ed and SA.aendern(self.ed, layout=n))
        return m


    def menue_smartartFarben(self):
        from lunivo_writer.editor import smartart as SA
        m = QMenu()
        for n, f in SA.FARBEN.items():
            m.addAction(_farbfeld(f[0]), n, lambda _=False, n=n: self.ed and SA.aendern(self.ed, farben=n))
        return m


    def wordart(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import WordArtDialog
            d = WordArtDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), "WordArt: " + d.text.text(), "wordart", {"text": d.text.text()})


    def diagramm(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import DiagrammDialog
            d = DiagrammDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), f"{d.art.currentText()}diagramm: {d.titel.text()}", "diagramm", {"art": d.art.currentText(), "titel": d.titel.text()})


    def piktogramm(self, k=None):
        if self.ed:
            from lunivo_writer.editor import einfuegen as E
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import PiktogrammDialog
            d = PiktogrammDialog(self.w)
            if d.exec():
                n, farbe = d.ergebnis()
                if n:
                    self._bild_einfuegen(E.piktogramm_bild(n, 96, farbe), f"Piktogramm: {n}", "piktogramm", {"name": n, "farbe": farbe})


    def screenshot(self, k=None):
        if not self.ed:
            return
        antwort = QMessageBox(QMessageBox.Question, "Bildschirmfoto", "Was soll aufgenommen werden?", QMessageBox.NoButton, self.w)
        ganz = antwort.addButton("Ganzer Bildschirm", QMessageBox.AcceptRole)
        bereich = antwort.addButton("Bereich wählen …", QMessageBox.AcceptRole)
        antwort.addButton("Abbrechen", QMessageBox.RejectRole)
        antwort.exec()
        if antwort.clickedButton() not in (ganz, bereich):
            return
        nur_bereich = antwort.clickedButton() is bereich
        from PySide6.QtCore import QTimer
        self.w.hide()
        QTimer.singleShot(500, lambda: self._aufnehmen(nur_bereich))


    def _aufnehmen(self, nur_bereich: bool):
        pm = QApplication.primaryScreen().grabWindow(0)
        if not nur_bereich:
            self.w.show()
            self._foto_einfuegen(pm)
            return
        from lunivo_writer.ui.dialogs.bildschirmfoto import BereichWahl
        self._wahl = BereichWahl(pm)
        self._wahl.fertig.connect(self._bereich_fertig)
        self._wahl.showFullScreen()


    def _bereich_fertig(self, pm):
        self.w.show()
        self._foto_einfuegen(pm)


    def _foto_einfuegen(self, pm):
        if pm is not None and not pm.isNull() and self.ed:
            self._bild_einfuegen(pm.toImage(), "Bildschirmfoto")


    def textfeld(self, k=None):
        if self.ed:
            from lunivo_writer.editor import einfuegen as E
            E.textfeld(self.ed)


    def initiale(self, k=None):
        if self.ed:
            from lunivo_writer.editor import einfuegen as E
            if not E.initiale(self.ed):
                self.w.statusBar().showMessage("Der Absatz ist leer.", 3000)


    def textAusDatei(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.services import file_service as formats
        from lunivo_writer.models.report import DocumentIOError
        from lunivo_writer.editor import einfuegen as E
        pfad, _ = QFileDialog.getOpenFileName(self.w, "Text aus Datei einfügen", self.w.settings.get("last_dir", ""), formats.OPEN_FILTER)
        if not pfad:
            return
        try:
            rep = E.text_aus_datei(self.ed, pfad)
        except DocumentIOError as e:
            QMessageBox.warning(self.w, "Einfügen nicht möglich", str(e))
            return
        self.w._show_report(rep, "Hinweise zur eingefügten Datei", "beim Einfügen")


    def formel(self, k=None):
        if self.ed:
            from lunivo_writer.editor import einfuegen as E
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import FormelDialog
            d = FormelDialog(self.w)
            if d.exec() and d.eingabe.text().strip():
                E.formel_einfuegen(self.ed, d.eingabe.text())


    def schnelltabelle(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import einfuegen as E
        m = QMenu()
        for n in E.SCHNELLTABELLEN:
            m.addAction(n, lambda _=False, n=n: E.schnelltabelle(self.ed, n))
        self._popup(m)


    def deckblatt(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import einfuegen as E
        from lunivo_writer.ui.dialogs.einfuegen_dialoge import DeckblattDialog
        d = DeckblattDialog(self.w, self.w.settings.get("benutzer/name", ""))
        if d.exec():
            E.deckblatt_einfuegen(self.ed, d.vorlage.currentText(), d.titel.text(), d.unter.text(), d.autor.text(), d.datum.text())


    def datumUhrzeit(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import DatumDialog
            d = DatumDialog(self.w)
            if d.exec() and d.ergebnis():
                self.ed.textCursor().insertText(d.ergebnis())
                self.ed.document().setModified(True)


    def textbaustein(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import BausteinDialog
            BausteinDialog(self.w, self.ed).exec()


    def textbausteine(self, k=None):
        self.textbaustein()


    def schnellbaustein(self, k=None):
        """F3: steht vor der Schreibmarke ein Kürzel, kommt der Baustein sofort; sonst die Liste aller Bausteine zum Auswählen."""
        if not self.ed:
            return
        from PySide6.QtGui import QTextCursor
        from lunivo_writer.services import bausteine
        c = self.ed.textCursor()
        if not c.hasSelection():
            w = QTextCursor(c); w.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
            b = bausteine.finde_kuerzel(w.selectedText())
            if b is not None:
                w.removeSelectedText(); bausteine.einfuegen(w, b); self.ed.document().setModified(True)
                return
        m = QMenu()
        for titel, liste in (("Eigene", bausteine.laden()), ("Standard", bausteine.standard())):
            if not liste:
                continue
            m.addSection(titel)
            for b in liste:
                m.addAction(b["name"] + (f"   [{b['kuerzel']}]" if b.get("kuerzel") else ""),
                            lambda _=False, b=b: (bausteine.einfuegen(self.ed.textCursor(), b), self.ed.document().setModified(True)))
        m.addSeparator()
        m.addAction("Textbausteine verwalten …", self.textbaustein)
        self._popup(m)
