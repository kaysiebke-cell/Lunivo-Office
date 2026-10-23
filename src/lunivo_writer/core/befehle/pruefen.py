"""Befehle: Überprüfen, Schreibhilfe, Vergleichen."""
from __future__ import annotations

import os
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox


class PruefenBefehle:
    """Befehle des Bandes: Überprüfen, Schreibhilfe, Vergleichen. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Überprüfen / Schreibhilfe --------------------------------------------------------------------------------------------
    def woerterZaehlen(self, k=None):
        self.w.word_count()


    def _jetzt_pruefen(self) -> None:
        """Prüfen (F7): ohne Text eine deutliche Rückmeldung statt einer leeren Seitenleiste."""
        if not self.ed or not self.ed.toPlainText().strip():
            QMessageBox.information(self.w, "Prüfen", "Es steht noch kein Text da, den ich prüfen könnte.")
            return
        self.w.assistant.pruefen(True)


    def rechtschreibung(self, k=None):
        self._jetzt_pruefen()


    def w_pruefen(self, k=None):
        self._jetzt_pruefen()


    def gruendlichPruefen(self, k=None):
        self.w.assistant.gruendlich()


    def wellen(self, k=None):
        """Rote Wellenlinien beim Schreiben an/aus (derselbe Schalter wie „We“ in der Seitenleiste und in „Welche Hilfe wann“)."""
        self.w.assistant.setze("wellen", not self.w.assistant.an("wellen"))


    def an_wellen(self): return self.w.assistant.an("wellen")


    def vorhersage(self, k=None):
        self.w.assistant.setze("vorhersage", not self.w.assistant.an("vorhersage"))


    def an_vorhersage(self): return self.w.assistant.an("vorhersage")


    def autokorrektur(self, k=None):
        self.w.assistant.setze("autokorr", not self.w.assistant.an("autokorr"))


    def an_autokorrektur(self): return self.w.assistant.an("autokorr")


    def tafelZeigen(self, k=None):
        self.w.toggle_sidebar()


    def welcheHilfe(self, k=None):
        self.w.sidebar.welche_hilfe()


    def w_optionenOeffnen(self, k=None, seite=None):
        self.w.show_options(seite) if seite else self.w.show_options()


    # ==== Schreibhilfe: Lesen =====================================================================================================
    def zeilenfokus(self, k=None):
        if self.ed:
            self.ed.set_zeilenfokus(not self.ed.zeilenfokus)


    def an_zeilenfokus(self): return bool(self.ed) and self.ed.zeilenfokus


    def bearbeitungSperren(self, k=None):
        self.w.toggle_sperre()


    def an_bearbeitungSperren(self):
        t = self.w.current_tab()
        return bool(t and getattr(t, "gesperrt", False))


    def lesemodus(self, k=None):
        self.w.toggle_lesemodus()


    def an_lesemodus(self): return self.w.lesemodus


    # ---- Sendungen --------------------------------------------------------------------------------------------
    # ---- Vergleichen und Zusammenführen ---------------------------------------------------------------------------------------
    def _fassung_laden(self, pfad: str):
        from lunivo_writer.services import file_service as formats
        try:
            return formats.load(pfad).doc
        except Exception as e:                                  # unlesbare Datei: melden, nicht abbrechen
            QMessageBox.warning(self.w, "Datei lesen", f"„{os.path.basename(pfad)}“ lässt sich nicht lesen:\n{e}")
            return None


    def _ergebnis_blatt(self, titel: str, ziel, page):
        from lunivo_writer.editor.sendungen import _ressourcen
        from PySide6.QtGui import QTextDocumentFragment
        t = self._neues_blatt(titel)
        d = t.editor.document()
        _ressourcen(ziel, d)
        d.clear()
        QTextCursor(d).insertFragment(QTextDocumentFragment(ziel))
        t.editor.page_settings_changed(page.copy())
        t.editor.document().setModified(True)
        return t


    def dokumenteVergleichen(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        from lunivo_writer.editor import vergleich as V
        pfad, _ = QFileDialog.getOpenFileName(self.w, "Mit welchem Dokument vergleichen?", self.w.settings.get("last_dir", os.path.expanduser("~")),
                                              "Dokumente (*.docx *.odt *.txt *.md);;Alle Dateien (*)")
        if not pfad:
            return
        andere = self._fassung_laden(pfad)
        if andere is None:
            return
        autor = os.path.splitext(os.path.basename(pfad))[0]
        ziel, st = V.vergleichen(t.editor.document(), andere, autor)
        self._ergebnis_blatt(f"Vergleich — {t.title} ↔ {autor}", ziel, t.page)
        self.w.statusBar().showMessage(
            (f"Vergleich fertig: {st['eingefuegt']} Zeichen eingefügt, {st['geloescht']} gelöscht (Überprüfen ▸ Änderungen: annehmen oder ablehnen)."
             if st["operationen"] else "Die beiden Dokumente haben denselben Text."), 9000)


    def dokumenteZusammenfuehren(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        from lunivo_writer.editor import vergleich as V
        pfade, _ = QFileDialog.getOpenFileNames(self.w, "Überarbeitete Fassungen auswählen (jede Datei ist ein Autor)",
                                                self.w.settings.get("last_dir", os.path.expanduser("~")),
                                                "Dokumente (*.docx *.odt *.txt *.md);;Alle Dateien (*)")
        fassungen = []
        for p in pfade:
            d = self._fassung_laden(p)
            if d is not None:
                fassungen.append((os.path.splitext(os.path.basename(p))[0], d))
        if not fassungen:
            return
        ziel, st, konflikte = V.zusammenfuehren(t.editor.document(), fassungen)
        self._ergebnis_blatt(f"Zusammenführung — {t.title}", ziel, t.page)
        msg = f"{len(fassungen)} Fassungen zusammengeführt: {st['eingefuegt']} Zeichen eingefügt, {st['geloescht']} gelöscht."
        if konflikte:
            msg += f" {len(konflikte)} Konflikt(e) — die erste Fassung gilt."
            QMessageBox.information(self.w, "Konflikte beim Zusammenführen", "\n".join(konflikte[:30]))
        self.w.statusBar().showMessage(msg, 9000)


    def _neues_blatt(self, titel: str):
        self.w.new_document()
        t = self.w.current_tab()
        t.title = titel
        self.w._update_tab_titles()
        return t


    def umschlag(self, k=None):
        from lunivo_writer.editor import sendungen as S
        from lunivo_writer.ui.dialogs.sendungen_dialoge import UmschlagDialog
        b = self.w.benutzerdaten()
        absender = "\n".join(x for x in (b["name"], b["strasse"], b["plz_ort"]) if x)
        d = UmschlagDialog(self.w, absender)
        if d.exec():
            t = self._neues_blatt("Umschlag")
            pg = S.umschlag_aufbauen(t.editor, d.format.currentText(), d.absender.toPlainText(), d.empfaenger.toPlainText())
            t.editor.page_settings_changed(pg)
            self.w.statusBar().showMessage(f"Umschlag im Format {d.format.currentText()} angelegt.", 5000)


    def etiketten(self, k=None):
        from lunivo_writer.editor import sendungen as S
        from lunivo_writer.ui.dialogs.sendungen_dialoge import EtikettenDialog
        d = EtikettenDialog(self.w)
        if d.exec():
            t = self._neues_blatt("Etiketten")
            pg = S.etiketten_aufbauen(t.editor, d.bogen.currentText(), d.text.toPlainText(), d.gleich.currentIndex() == 0)
            t.editor.page_settings_changed(pg)
            self.w.statusBar().showMessage("Bogen angelegt.", 5000)


    def seriendruckfeld(self, k=None):
        if self.ed:
            from lunivo_writer.editor import sendungen as S
            n, ok = QInputDialog.getText(self.w, "Seriendruckfeld", "Feldname (muss in der Kopfzeile der Empfängerliste stehen):", text="Name")
            if ok and n.strip():
                S.feld_einfuegen(self.ed, n.strip().replace("{", "").replace("}", ""))


    def adressblock(self, k=None):
        if self.ed:
            from lunivo_writer.editor import sendungen as S
            namen = {"Adressblock (Name, Straße, Ort)": "adresse", "Grußzeile (Anrede + Name)": "gruss", "Adressblock und Grußzeile": "beides"}
            n, ok = QInputDialog.getItem(self.w, "Adressblock und Grußzeile", "Einfügen:", list(namen), 0, False)
            if ok:
                S.adressblock_einfuegen(self.ed, namen[n])


    def seriendruckregel(self, k=None):
        if self.ed:
            from lunivo_writer.editor import sendungen as S
            from lunivo_writer.ui.dialogs.sendungen_dialoge import RegelDialog
            d = RegelDialog(self.w)
            if d.exec() and d.feld.text().strip():
                S.regel_einfuegen(self.ed, d.feld.text().strip(), d.wert.text().strip(), d.dann.text(), d.sonst.text())


    def seriendruck(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import sendungen as S
        from lunivo_writer.ui.dialogs.sendungen_dialoge import SeriendruckDialog
        d = SeriendruckDialog(self.w, S.felder_im_text(self.ed.document()), self.w.settings.get("serien/liste", ""))
        if not d.exec():
            return
        tab = S.tabelle_lesen(d.daten.toPlainText())
        if not tab:
            QMessageBox.information(self.w, "Seriendruck", "Dafür braucht es eine Kopfzeile und mindestens einen Empfänger.")
            return
        self.w.settings.set("serien/liste", d.daten.toPlainText())
        quelle = self.ed.document()
        seite = self.ed.page.copy()
        t = self._neues_blatt(self.w.current_tab().title + " — Seriendruck")
        n = S.serienbrief_erzeugen(quelle, tab[1], t.editor.document())
        t.editor.page_settings_changed(seite)
        self.w.statusBar().showMessage(f"{n} Briefe erzeugt (neues Dokument; die Vorlage bleibt unverändert).", 6000)


    def serienVorschau(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import sendungen as S
        roh = self.w.settings.get("serien/liste", "")
        tab = S.tabelle_lesen(roh) if roh else None
        if not tab:
            QMessageBox.information(self.w, "Vorschau", "Erst die Empfänger eingeben — Sendungen ▸ Seriendruck-Assistent.")
            return
        namen = [f"{i + 1}. " + ", ".join(list(s.values())[:2]) for i, s in enumerate(tab[1])]
        n, ok = QInputDialog.getItem(self.w, "Vorschau auf Ergebnisse", f"{len(namen)} Empfänger. Die Vorschau ersetzt den Text nicht:", namen, 0, False)
        if ok:
            d = S.brief_fuer(self.ed.document(), tab[1][namen.index(n)])
            QMessageBox.information(self.w, "Vorschau: " + n, d.toPlainText().strip()[:1200])


    def _form_dialog(self, art: str):
        if not self.ed:
            return
        from lunivo_writer.editor import formular as FO
        from lunivo_writer.ui.dialogs.formular_dialog import FormFeldDialog
        d = FormFeldDialog(self.w, art)
        if d.exec():
            m = d.meta()
            FO.einfuegen(self.ed, m)
            if art == "kasten" and m.get("beschriftung"):
                self.ed.textCursor().insertText(" " + m["beschriftung"])


    def formTextfeld(self, k=None): self._form_dialog("text")

    def formAuswahl(self, k=None): self._form_dialog("auswahl")


    def tabstopps(self, k=None): self.w.tabstopp_dialog()


    def geheZu(self, k=None, art="Seite"):
        if self.ed:
            from lunivo_writer.ui.dialogs.gehe_zu_dialog import GeheZuDialog
            GeheZuDialog(self.w, self.ed, art).exec()


    def vollbild(self, k=None): self.w.a_fullscreen.trigger()

    def an_vollbild(self): return self.w.isFullScreen()

    def formDatum(self, k=None): self._form_dialog("datum")

    def formKasten(self, k=None): self._form_dialog("kasten")

    def formKnopf(self, k=None): self._form_dialog("knopf")


    def formLeeren(self, k=None):
        if self.ed:
            from lunivo_writer.editor import formular as FO
            n = FO.alle_zuruecksetzen(self.ed)
            self.w.statusBar().showMessage(f"{n} Formularfeld{'er' if n != 1 else ''} zurückgesetzt.", 4000)


    # ---- Überprüfen: Thesaurus, Barrierefreiheit, Korrektursprache ------------------------------------------
    def thesaurus(self, k=None):
        ki = getattr(self.w, "ki", None)
        if not self.ed or ki is None:
            return

        def danach(wort, lst, von, bis):
            n, ok = QInputDialog.getItem(self.w, f"Wörter für „{wort}“", "Statt dessen:", lst, 0, False)
            if ok:
                self.ed.replace_range(von, bis, self._wie_geschrieben(wort, n))
        ki.thesaurus(danach)


    @staticmethod
    def _wie_geschrieben(alt: str, neu: str) -> str:
        return neu[:1].upper() + neu[1:] if alt[:1].isupper() else neu[:1].lower() + neu[1:]


    def barrierefrei(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.proofing.barrierefreiheit import pruefe
        funde = pruefe(self.ed)
        text = ("\n\n".join(f"{i}. {f}" for i, f in enumerate(funde, 1)) if funde else
                "Nichts gefunden. Bilder beschrieben, Überschriften der Reihe nach, Tabellen mit Kopfzeile, Schrift kräftig genug.")
        QMessageBox.information(self.w, "Barrierefreiheit", text)


    SPRACHEN = [("de-DE", "Deutsch"), ("de-AT", "Deutsch (Österreich)"), ("de-CH", "Deutsch (Schweiz)"), ("en-US", "Englisch"),
                ("en-GB", "Englisch (UK)"), ("fr-FR", "Französisch"), ("es-ES", "Spanisch"), ("it-IT", "Italienisch"),
                ("nl-NL", "Niederländisch"), ("pl-PL", "Polnisch"), ("ru-RU", "Russisch"), ("tr-TR", "Türkisch")]


    def pruefsprache(self, k=None):
        if not self.ed:
            return
        aktuell = self.w.current_tab().meta.get("sprache") or self.w.settings.get("pruefsprache", "de-DE")
        namen = [n for _k, n in self.SPRACHEN]
        start = next((i for i, (kk, _n) in enumerate(self.SPRACHEN) if kk == aktuell), 0)
        n, ok = QInputDialog.getItem(self.w, "Sprache für die Korrekturhilfen", "Sprache des Dokuments (wird in der Datei vermerkt).\n"
                                     "Die Schreibhilfe selbst prüft weiter auf Deutsch.", namen, start, False)
        if ok:
            self.pruefsprache_setzen(self.SPRACHEN[namen.index(n)][0])


    def pruefsprache_aktuell(self) -> str:
        t = self.w.current_tab()
        return (t.meta.get("sprache") if t is not None else "") or self.w.settings.get("pruefsprache", "de-DE")


    def pruefsprache_setzen(self, kennung: str) -> None:
        """Die Sprache des Dokuments für die Korrekturhilfen (wird in der Datei vermerkt) — vom Band und vom Fenster „KI-Einstellungen“ benutzt."""
        n = dict(self.SPRACHEN).get(kennung, kennung)
        if self.w.current_tab() is not None:
            self.w.current_tab().meta["sprache"] = kennung
            if self.ed:
                self.ed.document().setModified(True)
        self.w.settings.set("pruefsprache", kennung)
        self.w.statusBar().showMessage(f"Dokumentsprache: {n}.", 4000)
