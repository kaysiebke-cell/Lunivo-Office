"""Dateien, Vorlagen, Wiederherstellung."""
from __future__ import annotations

import os
from datetime import datetime
from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QFont, QKeySequence
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QLineEdit, QMenu, QMessageBox
from lunivo_writer.editor import stile
from lunivo_writer.services import file_service as formats
from lunivo_writer.models.report import DocumentIOError, IOReport, PasswortNoetig
from lunivo_writer.models.page import PageSettings
from lunivo_writer.editor.pagination import export_pdf
from lunivo_writer.ui.document.document_area import DocumentTab


class DateienBaustein:
    """Dateien, Vorlagen, Wiederherstellung. Baustein von ``MainWindow`` (siehe ``lunivo_writer/ui/main_window.py``)."""


    # ==== Dateien ======================================================================
    def new_document(self):
        tab = DocumentTab()
        from PySide6.QtGui import QTextDocument
        d = QTextDocument()
        f = QFont(self.settings.get("standard/schrift", "Liberation Sans"))
        f.setPointSizeF(float(self.settings.get("standard/groesse", 11)))
        d.setDefaultFont(f)
        tab.editor.set_document_and_page(d, PageSettings())
        self._add_tab(tab)


    def _add_tab(self, tab: DocumentTab):
        self._connect_tab(tab)
        tab.editor.setReadOnly(self.lesemodus)
        i = self.tabs.addTab(tab, self._tab_title(tab))
        self.tabs.setCurrentIndex(i)
        self._update_tab_titles()
        tab.editor.setFocus()


    def open_dialog(self):
        start = self.settings.get("last_dir", os.path.expanduser("~"))
        paths, _ = QFileDialog.getOpenFileNames(self, "Dokument öffnen", start, formats.OPEN_FILTER)
        for p in paths:
            self.open_path(p)


    def open_path(self, path: str) -> bool:
        path = os.path.abspath(path)
        for i, t in enumerate(self._doc_tabs()):
            if t.path == path:
                self.tabs.setCurrentWidget(t); return True
        kennwort = None
        while True:
            try:
                loaded = self.dokumente.laden(path, kennwort)
                break
            except PasswortNoetig as e:
                kennwort, ok = QInputDialog.getText(
                    self, "Kennwort", ("Falsches Kennwort. " if e.falsch else "") +
                    f"„{os.path.basename(path)}“ ist geschützt.\nKennwort:", QLineEdit.Password)
                if not ok:
                    return False
                continue
            except DocumentIOError as e:
                loaded, fehler = None, e
                break
        if loaded is None:
            QMessageBox.warning(self, "Öffnen nicht möglich", f"{os.path.basename(path)}\n\n{fehler}")
            self.dokumente.vergessen(path)
            return False
        tab = DocumentTab(loaded, path)
        self._add_tab(tab)
        if not self.settings.get_bool("sicherheit/markup_oeffnen", True):
            tab.editor.set_markup(False)
        if stile.als_json_neu() != self.settings.get("stile/eigene", ""):       # das Dokument brachte eigene Formatvorlagen mit
            self.settings.set("stile/eigene", stile.als_json_neu())
            getattr(self.band, "stile_aktualisieren", lambda: None)()
        self.dokumente.gelesen(path)
        self._show_report(loaded.report, f"Hinweise zu „{os.path.basename(path)}“", "beim Öffnen")
        return True


    def _show_report(self, rep: IOReport, title: str, when: str):
        if rep:
            QMessageBox.information(self, title,
                                    f"Nicht alles konnte {when} übernommen werden:\n\n• " + "\n• ".join(rep.warnings))


    def save(self) -> bool:
        t = self.current_tab()
        return self._save_tab(t) if t else False


    def _save_tab(self, tab: DocumentTab) -> bool:
        if tab.path is None or formats.ext(tab.path) not in (".docx", ".txt"):
            return self._save_tab_as(tab)
        return self._write(tab, tab.path)


    def save_as(self) -> bool:
        t = self.current_tab()
        return self._save_tab_as(t) if t else False


    def save_as_format(self, ext: str) -> bool:
        """Speichern unter mit festem Dateiformat (Untermenü „Speichern unter ▸“); das Dokument gehört danach zur neuen Datei."""
        t = self.current_tab()
        if not t:
            return False
        path = self._ask_path(t, "Speichern unter", only=ext)
        if not path or not self._write(t, path):
            return False
        t.set_path(path)
        self.settings.add_recent(path)
        self._update_tab_titles()
        return True


    def _ask_path(self, tab: DocumentTab, title: str, only: str | None = None) -> str | None:
        folder = os.path.dirname(tab.path) if tab.path else (self.settings.get("speichern/ordner", "") or
                                                             self.settings.get("last_dir", os.path.expanduser("~")))
        base = os.path.splitext(tab.title)[0] or "Unbenannt"
        if only:
            flt = formats.SAVE_FILTERS[only]; default = only
        else:
            standard = self.settings.get("speichern/standard", ".docx")
            flt = ("Word-Dokument (*.docx);;Textdatei (*.txt)" if standard != ".txt"
                   else "Textdatei (*.txt);;Word-Dokument (*.docx)")
            default = standard if standard in (".docx", ".txt") else ".docx"
        path, chosen = QFileDialog.getSaveFileName(self, title, os.path.join(folder, base + default), flt)
        if not path:
            return None
        if not os.path.splitext(path)[1]:
            path += ".txt" if "txt" in chosen else default
        return path


    def _save_tab_as(self, tab: DocumentTab) -> bool:
        path = self._ask_path(tab, "Speichern unter")
        if not path:
            return False
        if not self._write(tab, path):
            return False
        tab.set_path(path)
        self.settings.add_recent(path)
        self._update_tab_titles()
        return True


    def _write(self, tab: DocumentTab, path: str, mark_saved: bool = True) -> bool:
        try:
            rep = self.dokumente.speichern(path, tab.editor.document(), tab.page, tab.meta)
        except DocumentIOError as e:
            QMessageBox.critical(self, "Speichern fehlgeschlagen", str(e)); return False
        if mark_saved:
            tab.editor.document().setModified(False)
            self.dokumente.verwerfen(tab.token)
        self.statusBar().showMessage(f"Gespeichert: {path}", 4000)
        self._show_report(rep, "Hinweise zum Speichern", "beim Speichern")
        return True


    def save_copy(self):
        self.export_as(".docx", title="Kopie speichern")


    def export_as(self, ext: str, title: str | None = None):
        t = self.current_tab()
        if not t:
            return
        path = self._ask_path(t, title or "Exportieren", only=ext)
        if path:
            self._write(t, path, mark_saved=False)


    def export_pdf_dialog(self):
        t = self.current_tab()
        if not t:
            return
        folder = os.path.dirname(t.path) if t.path else os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(self, "Als PDF exportieren",
                                              os.path.join(folder, os.path.splitext(t.title)[0] + ".pdf"),
                                              "PDF-Dokument (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            autor = self.dokumente.meta_fuer_speichern(t.meta).get("author", "") if self.settings.get_bool("pdf/eigenschaften", True) else ""
            lz = None
            sg = self.settings.get_bool
            if sg("pdf/lz_ueberschriften", False) or sg("pdf/lz_textmarken", False) or sg("pdf/lz_andere", False):
                lz = {"ueberschriften": sg("pdf/lz_ueberschriften", False), "textmarken": sg("pdf/lz_textmarken", False),
                      "andere": sg("pdf/lz_andere", False)}
            komm = None
            if sg("pdf/kommentare", False):
                komm = {kid: f'{k.get("autor", "")}: {k.get("text", "")}'.strip(": ") for kid, k in t.editor.kommentare.items()}
            n = export_pdf(path, t.editor.document(), t.page, os.path.splitext(t.title)[0], autor, t.editor.noten, lz,
                           self._silben_fuer_druck(), komm,
                           {k: v for k, v in self.druckoptionen().items()
                            if k in ("versteckt", "felder_code", "zeichnungen", "balken", "hervorhebungen", "textmarken", "textgrenzen", "zuschnitt",
                                     "notenlinks", "blasen", "nur_formular")})
        except Exception as e:  # PDF-Ausgabe darf das Programm nicht beenden
            QMessageBox.critical(self, "PDF-Export fehlgeschlagen", str(e)); return
        self.statusBar().showMessage(f"PDF gespeichert ({n} Seiten): {path}", 5000)
        if self.settings.get_bool("pdf/oeffnen", False):
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))


    def druck_start(self) -> dict:
        """Letzte Wahl im Druckfenster; Hintergrund, Grafik und Leerseiten teilen sich die Schalter mit den Optionen."""
        g, gb = self.settings.get, self.settings.get_bool
        start = {"hintergrund": gb("drucken/hintergrund", True), "zeichnungen": gb("drucken/zeichnungen", True), "leere": gb("drucken/leere", True),
                 "drucker": g("drucken/dlg_drucker", ""), "kopien": 1, "sortieren": gb("drucken/dlg_sortieren", True),
                 "platzhalter": gb("drucken/dlg_platzhalter", False), "steuerelemente": gb("drucken/dlg_steuerelemente", True),
                 "kommentare": g("drucken/dlg_kommentare", "keine"), "schwarz": gb("drucken/dlg_schwarz", False),
                 "vorschau": gb("drucken/dlg_vorschau", True), "beidseitig": g("drucken/dlg_beidseitig", "aus")}
        return start


    def druck_merken(self, e: dict) -> None:
        for k in ("hintergrund", "zeichnungen", "leere"):
            self.settings.set(f"drucken/{k}", e[k])
        for k in ("drucker", "sortieren", "platzhalter", "steuerelemente", "kommentare", "schwarz", "vorschau", "beidseitig"):
            self.settings.set(f"drucken/dlg_{k}", e[k])


    def druck_vorschau(self, t):
        from lunivo_writer.editor.druck import optionen_aus, vorschau_bild

        def bilder(nummern, ein):
            opt = optionen_aus(self.druckoptionen(), ein, t.editor.noten)
            return vorschau_bild(t.editor.document(), t.page, opt, t.editor.noten, nummern)
        return bilder


    def _druck_args(self, t) -> dict:
        from lunivo_writer.editor.pagination import seitenzahl
        start = self.druck_start()
        if self.settings.get("drucken/vorgabe", "Alle Seiten") == "Aktuelle Seite":
            start.update(bereich="seiten", seiten_text=str(t.editor.current_page()))
        ps = t.page
        return dict(seiten=seitenzahl(t.editor.document(), ps, t.editor.noten), papier_mm=(ps.width_mm, ps.height_mm), quer=bool(ps.landscape),
                    start=start, auswahl=t.editor.textCursor().hasSelection(), vorschau=self.druck_vorschau(t))


    def druck_ansicht(self, t, parent=None):
        """Das Druckfenster ohne Knopfzeile (Menü ▸ Drucken, zweite Spalte)."""
        from lunivo_writer.ui.baukasten.druck_dialog import DruckAnsicht
        a = DruckAnsicht(parent=parent, **self._druck_args(t))
        a.eigenschaften.connect(lambda name: self._drucker_eigenschaften(a, name))
        return a


    def print_dialog(self):
        """Drucken (Strg+P, Schnellzugriff, Druckvorschau): die Seite „Drucken“ im Menü, kein eigenes Fenster."""
        if self.current_tab():
            self.backstage_oeffnen("drucken")


    def druckfenster(self):
        """Dasselbe als eigenes Fenster (für Aufrufer ohne Menü)."""
        t = self.current_tab()
        if not t:
            return
        from lunivo_writer.ui.baukasten.druck_dialog import DruckDialog
        dlg = DruckDialog(self, hilfe=self.druck_hilfe, **self._druck_args(t))
        dlg.ansicht.eigenschaften.connect(lambda name: self._drucker_eigenschaften(dlg.ansicht, name))
        if not dlg.exec():
            return
        self.drucke_nach_wahl(t, dlg.ergebnis())


    def druck_hilfe(self):
        QMessageBox.information(self, "Drucken", "Links sehen Sie das Blatt, wie es gedruckt wird. Rechts wählen Sie Drucker, Seiten, Kopien und Papier; "
                                "auf „Lunivo-Office“ stehen die Inhalte des Dokuments.")


    def drucke_nach_wahl(self, t, e: dict) -> None:
        """Druckt das Blatt `t` nach der Wahl `e` (Druckfenster oder Menü ▸ Drucken)."""
        from PySide6.QtPrintSupport import QPrinterInfo
        from lunivo_writer.editor.druck import drucken
        self.druck_merken(e)
        info = QPrinterInfo.printerInfo(e["drucker"]) if e["drucker"] else QPrinterInfo()
        pr = QPrinter(info, QPrinter.HighResolution if self.settings.get_bool("drucken/hoch", True) else QPrinter.ScreenResolution) \
            if not info.isNull() else self._neuer_drucker()
        if not e["drucker"]:                                           # kein Drucker eingerichtet: das Fenster des Systems übernimmt
            if not QPrintDialog(pr, self).exec():
                return
        self._vor_dem_drucken(t)
        n = drucken(pr, t.editor.document(), t.page, self.druckoptionen(), e, t.editor.noten)
        self.statusBar().showMessage(f"An den Drucker gesendet ({n} Blatt)." if n else "Keine Seiten zum Drucken.", 4000)


    def _drucker_eigenschaften(self, dlg, name: str) -> None:
        from PySide6.QtPrintSupport import QPrinterInfo
        pr = QPrinter(QPrinterInfo.printerInfo(name))
        sys_dlg = QPrintDialog(pr, self)
        sys_dlg.setOption(QPrintDialog.PrintPageRange, False)
        if sys_dlg.exec():
            dlg.drucker_setzen(pr.copyCount(), {QPrinter.DuplexLongSide: "lang", QPrinter.DuplexShortSide: "kurz"}.get(pr.duplex(), "aus"))


    def print_preview(self):
        t = self.current_tab()
        if not t:
            return
        from lunivo_writer.editor.druck import Zwischenseiten, optionen_aus
        from lunivo_writer.ui.baukasten.druckvorschau import DruckVorschau
        opt = optionen_aus(self.druckoptionen(), self.druck_start(), t.editor.noten)
        dlg = DruckVorschau(self, Zwischenseiten(t.editor.document(), t.page, opt, t.editor.noten))
        dlg.drucken.connect(lambda: QTimer.singleShot(0, self.print_dialog))
        dlg.showMaximized()
        dlg.exec()


    def ausgabe_ppi(self) -> int:
        """Standard-Ausgabeziel: Auflösung für „Als Bild exportieren“."""
        try:
            return int(str(self.settings.get("ausgabe/ppi", "150")).split()[0])
        except (ValueError, IndexError):
            return 150


    def druckoptionen(self) -> dict:
        return {"umgekehrt": self.settings.get_bool("drucken/umgekehrt", False),
                "duplex": self.settings.get("drucken/duplex", "alle"),
                "hintergrund": self.settings.get_bool("drucken/hintergrund", True),
                "leere": self.settings.get_bool("drucken/leere", True),
                "hervorhebungen": self.settings.get_bool("drucken/hervorhebungen", True),
                "textmarken": self.settings.get_bool("drucken/textmarken", False),
                "textgrenzen": self.settings.get_bool("drucken/textgrenzen", False),
                "zuschnitt": self.settings.get_bool("drucken/zuschnitt", False),
                "silbenfarben": self._silben_fuer_druck(),
                "versteckt": self.settings.get_bool("drucken/versteckt", False),
                "felder_code": self.settings.get_bool("drucken/felder_code", False),
                "zeichnungen": self.settings.get_bool("drucken/zeichnungen", True),
                "balken": self.settings.get("aenderungen/balken", "links"),
                "notenlinks": self.settings.get_bool("pdf/notenlinks", True),
                "blasen": self._blasen_fuer_druck(),
                "nur_formular": self.settings.get_bool("drucken/nur_formular", False)}


    def _blasen_fuer_druck(self):
        from lunivo_writer.editor import sprechblasen as SB
        e = self.current_editor()
        k = SB.konfig_lesen(self.settings)
        if e is None or not self.settings.get_bool("sprechblasen/drucken", False) or not SB.aktiv(k):
            return None
        if not e.kommentare and not (k["verwenden"] == "Immer" and e.aenderungen()):
            return None
        return {"konfig": k, "kommentare": dict(e.kommentare)}


    def _silben_fuer_druck(self):
        from lunivo_writer.editor import silbenfarben as S
        k = S.konfig_lesen(self.settings)
        return dict(k, nur_absatz=False) if k["an"] and k["drucken"] else None


    def _neuer_drucker(self):
        return QPrinter(QPrinter.HighResolution if self.settings.get_bool("drucken/hoch", True) else QPrinter.ScreenResolution)


    def _vor_dem_drucken(self, tab):
        """„Felder vor dem Drucken aktualisieren“: Verzeichnisse neu rechnen."""
        if self.settings.get_bool("drucken/felder", True):
            from lunivo_writer.editor.verzeichnis import verzeichnis_aktualisieren
            verzeichnis_aktualisieren(tab.editor)


    def reiter_menue(self, index: int, pos) -> None:
        """Kontextmenü am Dokumentreiter."""
        w = self.tabs.widget(index) if index >= 0 else None
        if not isinstance(w, DocumentTab):
            return
        m = QMenu(self)
        m.addAction("Schließen", lambda: self.close_tab(index))
        m.addAction("Andere schließen", lambda: self._reiter_schliessen(w, nur_andere=True))
        m.addAction("Alle schließen", lambda: self._reiter_schliessen(w, nur_andere=False))
        m.addSeparator()
        m.addAction("Speichern", lambda: (self.tabs.setCurrentIndex(index), self._save_tab(w)))
        pfad = m.addAction("Pfad kopieren", lambda: QApplication.clipboard().setText(w.path))
        ordner = m.addAction("Ordner öffnen", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(w.path))))
        pfad.setEnabled(bool(w.path)); ordner.setEnabled(bool(w.path))
        m.exec(pos)


    def _reiter_schliessen(self, behalten, nur_andere: bool) -> None:
        for i in range(self.tabs.count() - 1, -1, -1):
            t = self.tabs.widget(i)
            if isinstance(t, DocumentTab) and not (nur_andere and t is behalten):
                if not self.close_tab(i):
                    return


    def close_tab(self, index: int) -> bool:
        w = self.tabs.widget(index)
        if not isinstance(w, DocumentTab):
            return False
        if w.is_modified():
            self.tabs.setCurrentIndex(index)
            box = QMessageBox(QMessageBox.Question, "Ungespeicherte Änderungen",
                              f"Möchten Sie die Änderungen an „{w.title}“ speichern?",
                              QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, self)
            box.button(QMessageBox.Save).setText("Speichern")
            box.button(QMessageBox.Discard).setText("Nicht speichern")
            box.button(QMessageBox.Cancel).setText("Abbrechen")
            r = box.exec()
            if r == QMessageBox.Cancel:
                return False
            if r == QMessageBox.Save and not self._save_tab(w):
                return False
        self.dokumente.verwerfen(w.token)
        self.tabs.removeTab(index)
        w.deleteLater()
        self._refresh_ui()
        return True


    def _zusatz_kuerzel(self):
        """Kürzel ohne eigene Aktion (Tabelle in windows/kuerzel.py zeigt sie in der Hilfe)."""
        from PySide6.QtGui import QShortcut
        b = self.befehle
        tabelle = [("F3", b.schnellbaustein), ("F4", b.vorlesen), ("F5", self.toggle_sidebar), ("F6", b.welcheHilfe),
                   ("F7", lambda: self.assistant.pruefen(True)), ("F8", b.kiKorrektur),
                   ("Ctrl++", b.groesser), ("Ctrl+-", b.kleiner), ("Ctrl+0", b.normal),
                   ("Ctrl+D", b.schriftartMehr), ("Ctrl+Alt+V", b.inhalteEinfuegen),
                   ("Ctrl+Alt+F", b.fussnote), ("Ctrl+Alt+D", b.endnote),
                   ("Ctrl+Shift+H", b.ausblenden), ("Ctrl+Tab", lambda: self._tab_weiter(1)), ("Ctrl+Shift+Tab", lambda: self._tab_weiter(-1))]
        self._kuerzel = []
        for taste, fn in tabelle:
            sc = QShortcut(QKeySequence(taste), self)
            sc.setContext(Qt.WindowShortcut)
            sc.activated.connect(fn)
            self._kuerzel.append(sc)


    def _tab_weiter(self, d: int):
        n = self.tabs.count()
        if n > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + d) % n)


    # ==== Vorlagen ==================================================================
    def benutzerdaten(self) -> dict:
        g = self.settings.get
        return {k: g(f"benutzer/{k}", "") or "" for k in ("name", "initialen", "strasse", "plz_ort", "ort", "telefon", "mail")}


    def neu_aus_vorlage(self):
        """Die Seite „Neu“ im Menü: alle Vorlagen als Blätter mit Vorschau."""
        self.backstage_oeffnen("vorlage")


    def neu_aus_wahl(self, art: str, wert) -> None:
        """Legt ein neues Dokument nach der Wahl auf der Seite „Neu“ an: leer, ein Gerüst oder eine Abschrift einer Vorlagendatei."""
        if art == "leer":
            self.new_document()
        elif art == "geruest":
            from lunivo_writer.editor import vorlagen
            from PySide6.QtCore import QDate, QLocale
            self.new_document()
            t = self.current_tab()
            t.title = wert["name"]
            self._update_tab_titles()
            vorlagen.aufbauen(t.editor, wert["zeilen"], self.benutzerdaten(), QLocale("de_DE").toString(QDate.currentDate(), "d. MMMM yyyy"))
        else:
            try:
                geladen = formats.load(wert)
            except DocumentIOError as e:
                QMessageBox.warning(self, "Vorlage", str(e)); return
            tab = DocumentTab(geladen, None, title=os.path.splitext(os.path.basename(wert))[0])
            self._add_tab(tab)
            tab.editor.document().setModified(True)
            self._show_report(geladen.report, "Hinweise zur Vorlage", "beim Öffnen")


    def als_vorlage_speichern(self, ordner: str | None = None):
        """Legt das Blatt als Vorlage ab: im Vorlagenordner oder (``ordner``) in einer seiner Rubriken."""
        t = self.current_tab()
        if not t:
            return
        from lunivo_writer.editor import vorlagen
        ordner = ordner or vorlagen.vorlagenordner(self.settings)
        os.makedirs(ordner, exist_ok=True)
        pfad, _ = QFileDialog.getSaveFileName(self, "Als Vorlage speichern", os.path.join(ordner, os.path.splitext(t.title)[0] + ".docx"),
                                              "Word-Dokument (*.docx)")
        if pfad:
            if not pfad.lower().endswith(".docx"):
                pfad += ".docx"
            self._write(t, pfad, mark_saved=False)


    # ==== Wiederherstellung ================================================================
    def autosave_now(self):
        self.dokumente.sichern(self._doc_tabs())


    def offer_recovery(self):
        open_tokens = {t.token for t in self._doc_tabs()}
        entries = self.dokumente.wiederherstellbar(open_tokens)
        if not entries:
            return
        names = "\n".join(f"• {e.title} ({datetime.fromtimestamp(e.saved_at):%d.%m.%Y %H:%M})" for e in entries)
        box = QMessageBox(QMessageBox.Question, "Wiederherstellung",
                          f"Lunivo Writer wurde nicht ordnungsgemäß beendet. Gesicherte Dokumente:\n\n{names}\n\n"
                          "Wiederherstellen?", QMessageBox.Yes | QMessageBox.No, self)
        box.button(QMessageBox.Yes).setText("Wiederherstellen"); box.button(QMessageBox.No).setText("Verwerfen")
        if box.exec() == QMessageBox.Yes:
            for e in entries:
                try:
                    loaded = self.dokumente.laden(e.docx_path)
                except DocumentIOError:
                    continue
                tab = DocumentTab(loaded, None, title=f"Wiederhergestellt – {e.title}")
                tab.token = e.token
                tab.editor.document().setModified(True)
                self._add_tab(tab)
        else:
            for e in entries:
                self.dokumente.verwerfen(e.token)
