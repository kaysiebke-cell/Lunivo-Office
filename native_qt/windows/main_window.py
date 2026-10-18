"""Hauptfenster: Menüleiste, Schnellzugriff, Ribbon, Dokumentreiter, Statusleiste."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QKeySequence, QTextCursor
from PySide6.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QComboBox, QFileDialog, QFontComboBox, QInputDialog, QLabel,
    QMainWindow, QMenu, QMessageBox, QStatusBar, QTabWidget, QToolBar, QToolButton, QWidget,
)

from .. import __version__
from ..document_io import formats
from ..document_io.report import DocumentIOError, IOReport
from ..editor.editor_widget import STYLES, DocumentEditor
from ..editor.page import PAPER_MM, HeaderFooter, PageSettings, px_to_mm
from ..editor.pagination import export_pdf, print_document
from ..storage import recovery
from ..storage.settings import Settings
from ..services.writing_assistant import WritingAssistant
from ..widgets.dialogs import (
    FindReplaceDialog, HeaderFooterDialog, PageSetupDialog, ParagraphDialog, TableDialog,
)
from ..widgets.doc_tabs import DocTabs
from ..widgets.document_tab import DocumentTab
from ..widgets.menue_tafel import MenueTafel
from ..widgets.register_band import RegisterBand, lade_register
from ..widgets.schreibhilfe_panel import SchreibhilfePanel
from ..widgets.start_page import StartPage
from .befehle import Befehle

MARGIN_PRESETS = {
    "Normal (2,5 cm)": (25, 25, 25, 25),
    "Schmal (1,3 cm)": (12.7, 12.7, 12.7, 12.7),
    "Mittel (1,9 cm)": (19.1, 19.1, 19.1, 19.1),
    "Breit (5,1 cm links/rechts)": (25.4, 25.4, 50.8, 50.8),
}


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings | None = None):
        super().__init__()
        self.settings = settings or Settings()
        self.setWindowTitle("Lunivo Writer")
        self.resize(1280, 860)
        self.marks_on = False
        self.docs = DocTabs()
        self.docs.tabCloseRequested.connect(self.close_tab)
        self.docs.currentChanged.connect(self._tab_changed)
        self.docs.newRequested.connect(self.new_document)
        self.tabs = self.docs                      # gleiche Schnittstelle wie ein QTabWidget
        self.start = StartPage()
        self.start.newRequested.connect(self.new_document)
        self.start.openRequested.connect(self.open_dialog)
        self.start.openPath.connect(self.open_path)
        self.docs.stack.insertWidget(0, self.start)
        self.docs.stack.setCurrentWidget(self.start)
        self.find_dialog = FindReplaceDialog(self.current_editor, self)
        self.assistant = WritingAssistant(self.settings, parent=self)
        self.assistant.status.connect(lambda t: self.lbl_msg.setText(t))
        self.befehle = Befehle(self)
        self._build_actions()
        self._build_status()
        self.band = RegisterBand(self.befehle, lade_register())
        self.band.menue_knopf.clicked.connect(self.show_main_menu)
        self.menubar_wanted = self.settings.get_bool("ui/menueleiste", False)
        self._build_menu()
        self.menuBar().setVisible(self.menubar_wanted)
        self.sidebar = SchreibhilfePanel(self.assistant)
        self.sidebar.setVisible(self.settings.get_bool("ui/seitenleiste", True))
        central = QWidget()
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(self.docs.leiste)
        lay.addWidget(self.band)
        mitte = QHBoxLayout(); mitte.setSpacing(0)
        mitte.addWidget(self.docs.stack, 1)
        mitte.addWidget(self.sidebar)
        lay.addLayout(mitte, 1)
        self.setCentralWidget(central)
        geo = self.settings.get("window/geometry")
        if geo:
            self.restoreGeometry(geo)
        self.autosave = QTimer(self)
        self.autosave.timeout.connect(self.autosave_now)
        self.autosave.start(max(10, self.settings.get_int("autosave_seconds", 60)) * 1000)
        self.start.set_recent(self.settings.recent())
        self._sync_timer = QTimer(self)
        self._sync_timer.setSingleShot(True)
        self._sync_timer.setInterval(60)
        self._sync_timer.timeout.connect(self._sync_format)
        self._verbinde_felder()
        self._refresh_ui()

    # ==== Aktionen =======================================================
    def _act(self, text, slot=None, shortcut=None, checkable=False, tip=None) -> QAction:
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.setCheckable(checkable)
        if tip:
            a.setToolTip(tip + (f" ({a.shortcut().toString()})" if shortcut else ""))
        elif shortcut:
            a.setToolTip(f"{text} ({a.shortcut().toString()})")
        if slot:
            (a.toggled if checkable else a.triggered).connect(slot)
        return a

    def _build_actions(self):
        A = self._act
        self.a_new = A("Neu", self.new_document, "Ctrl+N")
        self.a_open = A("Öffnen …", self.open_dialog, "Ctrl+O")
        self.a_save = A("Speichern", self.save, "Ctrl+S")
        self.a_save_as = A("Speichern unter …", self.save_as, "Ctrl+Shift+S")
        self.a_save_copy = A("Kopie speichern …", self.save_copy)
        self.a_pdf = A("Als PDF exportieren …", self.export_pdf_dialog, "Ctrl+Shift+E")
        self.a_exp_docx = A("Als DOCX exportieren …", lambda: self.export_as(".docx"))
        self.a_exp_odt = A("Als ODT exportieren …", lambda: self.export_as(".odt"))
        self.a_exp_txt = A("Als TXT exportieren …", lambda: self.export_as(".txt"))
        self.a_print = A("Drucken …", self.print_dialog, "Ctrl+P")
        self.a_preview = A("Druckvorschau …", self.print_preview)
        self.a_info = A("Dokumentinformationen …", self.show_info)
        self.a_options = A("Optionen …", self.show_options, "F9")
        self.a_close = A("Schließen", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        self.a_quit = A("Beenden", self.close, "Ctrl+Q")

        self.a_undo = A("↶", lambda: self._ed(lambda e: e.undo()), "Ctrl+Z", tip="Rückgängig")
        self.a_redo = A("↷", lambda: self._ed(lambda e: e.redo()), "Ctrl+Y", tip="Wiederholen")
        self.a_cut = A("Ausschneiden", lambda: self._ed(lambda e: e.cut()), "Ctrl+X")
        self.a_copy = A("Kopieren", lambda: self._ed(lambda e: e.copy()), "Ctrl+C")
        self.a_paste = A("Einfügen", lambda: self._ed(lambda e: e.paste()), "Ctrl+V")
        self.a_paste_plain = A("Einfügen ohne Formatierung", self.paste_plain, "Ctrl+Shift+V")
        self.a_select_all = A("Alles auswählen", lambda: self._ed(lambda e: e.selectAll()), "Ctrl+A")
        self.a_find = A("Suchen …", self.find_dialog_show, "Ctrl+F")
        self.a_replace = A("Ersetzen …", self.find_dialog_show, "Ctrl+H")

        self.a_bold = A("F", lambda on: self._ed(lambda e: e.toggle_bold(on)), "Ctrl+B", True, "Fett")
        self.a_italic = A("K", lambda on: self._ed(lambda e: e.toggle_italic(on)), "Ctrl+I", True, "Kursiv")
        self.a_under = A("U", lambda on: self._ed(lambda e: e.toggle_underline(on)), "Ctrl+U", True, "Unterstrichen")
        self.a_strike = A("S̶", lambda on: self._ed(lambda e: e.toggle_strike(on)), None, True, "Durchgestrichen")
        self.a_sup = A("x²", lambda on: self._ed(lambda e: e.set_script("sup" if on else None)),
                       "Ctrl+Shift+=", True, "Hochgestellt")
        self.a_sub = A("x₂", lambda on: self._ed(lambda e: e.set_script("sub" if on else None)),
                       "Ctrl+=", True, "Tiefgestellt")
        f = self.a_bold.font() if False else None
        self.a_grow = A("A▲", lambda: self._ed(lambda e: e.grow_font(1)), "Ctrl+]", tip="Schrift vergrößern")
        self.a_shrink = A("A▼", lambda: self._ed(lambda e: e.grow_font(-1)), "Ctrl+[", tip="Schrift verkleinern")
        self.a_clear = A("Formatierung löschen", lambda: self._ed(lambda e: e.clear_formatting()))
        self.a_color = A("A", self.choose_color, tip="Schriftfarbe")
        self.a_highlight = A("Hervorheben", self.choose_highlight, tip="Texthervorhebungsfarbe")
        self.a_bullets = A("• Liste", lambda: self._ed(lambda e: e.toggle_list("bullet")), tip="Aufzählung")
        self.a_numbers = A("1. Liste", lambda: self._ed(lambda e: e.toggle_list("number")), tip="Nummerierung")
        self.a_indent_less = A("⇤", lambda: self._ed(lambda e: e.change_indent(-10)), tip="Einzug verkleinern")
        self.a_indent_more = A("⇥", lambda: self._ed(lambda e: e.change_indent(10)), tip="Einzug vergrößern")
        self.align_group = QActionGroup(self)
        self.a_left = A("⯇", lambda: self._ed(lambda e: e.set_alignment(Qt.AlignLeft)), "Ctrl+L", True, "Linksbündig")
        self.a_center = A("☰", lambda: self._ed(lambda e: e.set_alignment(Qt.AlignHCenter)), "Ctrl+E", True, "Zentriert")
        self.a_right = A("⯈", lambda: self._ed(lambda e: e.set_alignment(Qt.AlignRight)), "Ctrl+R", True, "Rechtsbündig")
        self.a_justify = A("≣", lambda: self._ed(lambda e: e.set_alignment(Qt.AlignJustify)), "Ctrl+J", True, "Blocksatz")
        for a in (self.a_left, self.a_center, self.a_right, self.a_justify):
            self.align_group.addAction(a)
        self.a_para = A("Absatz …", self.paragraph_dialog)
        self.a_marks = A("¶", self.toggle_marks, "Ctrl+Shift+8", True, "Formatierungszeichen ein-/ausblenden")

        self.a_pagebreak = A("Seitenumbruch", lambda: self._ed(lambda e: e.insert_page_break()), "Ctrl+Return")
        self.a_table = A("Tabelle …", self.insert_table)
        self.a_image = A("Bild …", self.insert_image)
        self.a_link = A("Hyperlink …", self.insert_link, "Ctrl+K")
        self.a_header = A("Kopfzeile …", lambda: self.edit_header_footer(True))
        self.a_footer = A("Fußzeile …", lambda: self.edit_header_footer(False))
        self.a_pagenum = A("Seitenzahl", self.insert_page_number)
        self.a_date = A("Datum", self.insert_date)
        self.a_pagesetup = A("Seite einrichten …", self.page_setup)
        self.a_wordcount = A("Wortanzahl", self.word_count)
        self.a_fullscreen = A("Vollbild", self.toggle_fullscreen, "F11", True)
        self.a_about = A("Über Lunivo Writer", self.about)

    # ==== Menü ============================================================
    def _build_menu(self):
        mb = self.menuBar()
        m = mb.addMenu("&Datei")
        m.addAction(self.a_new); m.addAction(self.a_open)
        self.recent_menu = m.addMenu("Zuletzt verwendete Dokumente")
        self.recent_menu.aboutToShow.connect(self._fill_recent)
        m.addSeparator()
        m.addAction(self.a_save); m.addAction(self.a_save_as); m.addAction(self.a_save_copy)
        ex = m.addMenu("Exportieren")
        for a in (self.a_pdf, self.a_exp_docx, self.a_exp_odt, self.a_exp_txt):
            ex.addAction(a)
        pr = m.addMenu("Drucken")
        pr.addAction(self.a_print); pr.addAction(self.a_preview)
        m.addSeparator()
        m.addAction(self.a_info); m.addAction(self.a_options)
        m.addSeparator()
        m.addAction(self.a_close); m.addAction(self.a_quit)
        e = mb.addMenu("&Bearbeiten")
        for a in (self.a_undo, self.a_redo, None, self.a_cut, self.a_copy, self.a_paste,
                  self.a_paste_plain, None, self.a_find, self.a_replace, self.a_select_all):
            e.addSeparator() if a is None else e.addAction(a)
        v = mb.addMenu("&Ansicht")
        v.addAction(self.a_marks); v.addAction(self.a_fullscreen)
        h = mb.addMenu("&Hilfe")
        h.addAction(self.a_about)

    def _fill_recent(self):
        self.recent_menu.clear()
        items = self.settings.recent()
        if not items:
            self.recent_menu.addAction("(leer)").setEnabled(False)
            return
        for p in items:
            a = self.recent_menu.addAction(os.path.basename(p))
            a.setToolTip(p)
            a.triggered.connect(lambda _=False, p=p: self.open_path(p))
        self.recent_menu.addSeparator()
        self.recent_menu.addAction("Liste leeren", self._clear_recent)

    def _clear_recent(self):
        self.settings.clear_recent(); self.start.set_recent([])

    # ==== Statusleiste ============================================================
    def _build_status(self):
        sb = QStatusBar(); self.setStatusBar(sb)
        sb.setSizeGripEnabled(True)
        self.lbl_msg = QLabel("")
        sb.addWidget(self.lbl_msg, 1)
        self.lbl_words = QLabel("0 Wörter, 0 Zeichen")
        self.lbl_page = QLabel("Seite 1 von 1")
        self.lbl_state = QLabel("")
        for w in (self.lbl_words, self.lbl_page):
            w.setContentsMargins(10, 0, 10, 0); sb.addPermanentWidget(w)

    # ==== Hilfen ====================================================================
    def current_tab(self) -> DocumentTab | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, DocumentTab) else None

    def current_editor(self) -> DocumentEditor | None:
        t = self.current_tab()
        return t.editor if t else None

    def _ed(self, fn):
        e = self.current_editor()
        if e is not None:
            fn(e)

    def _doc_tabs(self) -> list[DocumentTab]:
        return [self.tabs.widget(i) for i in range(self.tabs.count())
                if isinstance(self.tabs.widget(i), DocumentTab)]

    def _tab_title(self, tab: DocumentTab) -> str:
        return ("● " if tab.is_modified() else "") + tab.title

    def _update_tab_titles(self):
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, DocumentTab):
                self.tabs.setTabText(i, self._tab_title(w))
                self.tabs.setTabToolTip(i, w.path or "Noch nicht gespeichert")
        self._update_window_title()

    def _update_window_title(self):
        t = self.current_tab()
        self.setWindowTitle(f"{self._tab_title(t)} — Lunivo Writer" if t else "Lunivo Writer")

    def _tab_changed(self, _i):
        t = self.current_tab()
        self._refresh_ui()
        if t:
            t.editor.setFocus()
            t.editor._recount()

    def _refresh_ui(self):
        has = self.current_tab() is not None
        self.docs.stack.setCurrentWidget(self.current_tab() if has else self.start)
        self.band.aktualisieren(has)
        for a in (self.a_undo, self.a_redo):
            a.setEnabled(has)
        self._update_window_title()
        self._sync_format()
        self._sync_status()
        self.assistant.attach(self.current_editor())

    def _connect_tab(self, tab: DocumentTab):
        e = tab.editor
        e.formatChanged.connect(self._sync_later)
        e.pageInfoChanged.connect(lambda *_: self._sync_status())
        e.document().modificationChanged.connect(lambda _m: self._update_tab_titles())
        e.document().contentsChanged.connect(self._sync_status)
        e.document().contentsChanged.connect(self.assistant.dokument_geaendert)
        felder = self.band.felder
        if felder and e is not None:
            pass

    def _sync_later(self):
        self._sync_timer.start()

    def _sync_format(self):
        e = self.current_editor()
        self.band.aktualisieren(e is not None)
        f = self.band.felder
        if e is None or not f:
            return
        cf = e.textCursor().charFormat()
        fam = cf.fontFamilies()[0] if cf.fontFamilies() else e.document().defaultFont().family()
        f["font"].blockSignals(True); f["font"].setCurrentFont(QFont(fam)); f["font"].blockSignals(False)
        size = cf.fontPointSize() or e.document().defaultFont().pointSizeF() or 11
        f["groesse"].blockSignals(True); f["groesse"].setEditText(f"{size:g}"); f["groesse"].blockSignals(False)
        st = e.current_style()
        f["stil"].blockSignals(True); f["stil"].setCurrentText("Fließtext" if st == "Standard" else st); f["stil"].blockSignals(False)

    def _sync_status(self):
        e = self.current_editor()
        if e is None:
            self.lbl_page.setText("Seite – von –"); self.lbl_words.setText("0 Wörter, 0 Zeichen")
            return
        txt = e.document().toPlainText()
        self.lbl_page.setText(f"Seite {e.current_page()} von {e.page_count}")
        self.lbl_words.setText(f"{len(txt.split())} Wörter, {len(txt)} Zeichen")

    def _verbinde_felder(self):
        f = self.band.felder
        if not f:
            return
        f["font"].activated.connect(lambda _: self._ed(lambda e: (e.set_font_family(f["font"].currentFont().family()), e.setFocus())))
        f["groesse"].activated.connect(self._size_chosen)
        f["groesse"].lineEdit().editingFinished.connect(self._size_chosen)
        f["stil"].activated.connect(lambda _: self.stil_anwenden(f["stil"].currentText()))

    def stil_anwenden(self, name: str):
        name = "Standard" if name in ("Fließtext", "Kein Abstand") else name
        self._ed(lambda e: e.apply_style(name))

    def _size_chosen(self, *_):
        try:
            pt = float(self.band.felder["groesse"].currentText().replace(",", "."))
        except ValueError:
            return
        self._ed(lambda e: (e.set_font_size(pt), e.setFocus()))

    # ==== Dateien ======================================================================
    def new_document(self):
        tab = DocumentTab()
        from PySide6.QtGui import QTextDocument
        d = QTextDocument()
        f = QFont("Liberation Sans"); f.setPointSizeF(11); d.setDefaultFont(f)
        tab.editor.set_document_and_page(d, PageSettings())
        self._add_tab(tab)

    def _add_tab(self, tab: DocumentTab):
        self._connect_tab(tab)
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
        try:
            loaded = formats.load(path)
        except DocumentIOError as e:
            QMessageBox.warning(self, "Öffnen nicht möglich", f"{os.path.basename(path)}\n\n{e}")
            self.settings.remove_recent(path); self.start.set_recent(self.settings.recent())
            return False
        tab = DocumentTab(loaded, path)
        self._add_tab(tab)
        self.settings.set("last_dir", os.path.dirname(path))
        self.settings.add_recent(path); self.start.set_recent(self.settings.recent())
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

    def _ask_path(self, tab: DocumentTab, title: str, only: str | None = None) -> str | None:
        folder = os.path.dirname(tab.path) if tab.path else self.settings.get("last_dir", os.path.expanduser("~"))
        base = os.path.splitext(tab.title)[0] or "Unbenannt"
        if only:
            flt = formats.SAVE_FILTERS[only]; default = only
        else:
            flt = "Word-Dokument (*.docx);;Textdatei (*.txt)"; default = ".docx"
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
        self.settings.add_recent(path); self.start.set_recent(self.settings.recent())
        self._update_tab_titles()
        return True

    def _write(self, tab: DocumentTab, path: str, mark_saved: bool = True) -> bool:
        try:
            rep = formats.save(path, tab.editor.document(), tab.page, tab.meta)
        except DocumentIOError as e:
            QMessageBox.critical(self, "Speichern fehlgeschlagen", str(e)); return False
        if mark_saved:
            tab.editor.document().setModified(False)
            recovery.discard(tab.token)
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
            n = export_pdf(path, t.editor.document(), t.page, os.path.splitext(t.title)[0])
        except Exception as e:  # PDF-Ausgabe darf das Programm nicht beenden
            QMessageBox.critical(self, "PDF-Export fehlgeschlagen", str(e)); return
        self.statusBar().showMessage(f"PDF gespeichert ({n} Seiten): {path}", 5000)

    def print_dialog(self):
        t = self.current_tab()
        if not t:
            return
        pr = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(pr, self)
        dlg.setOption(QPrintDialog.PrintPageRange, True)
        dlg.setMinMax(1, t.editor.page_count)
        if dlg.exec():
            print_document(pr, t.editor.document(), t.page)
            self.statusBar().showMessage("An den Drucker gesendet.", 4000)

    def print_preview(self):
        t = self.current_tab()
        if not t:
            return
        pr = QPrinter(QPrinter.HighResolution)
        dlg = QPrintPreviewDialog(pr, self)
        dlg.paintRequested.connect(lambda p: print_document(p, t.editor.document(), t.page))
        dlg.resize(1000, 800)
        dlg.exec()

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
        recovery.discard(w.token)
        self.tabs.removeTab(index)
        w.deleteLater()
        self._refresh_ui()
        return True

    def closeEvent(self, ev):
        for i in range(self.tabs.count() - 1, -1, -1):
            if isinstance(self.tabs.widget(i), DocumentTab) and not self.close_tab(i):
                ev.ignore(); return
        self.settings.set("window/geometry", self.saveGeometry())
        ev.accept()

    # ==== Wiederherstellung ================================================================
    def autosave_now(self):
        for t in self._doc_tabs():
            if not t.is_modified():
                continue
            docx_path, _ = recovery.paths(t.token)
            try:
                formats.save(docx_path, t.editor.document(), t.page, t.meta)
                recovery.write_meta(t.token, t.path or "", t.title)
            except Exception:
                pass            # Sicherung darf nie die Arbeit stören

    def offer_recovery(self):
        open_tokens = {t.token for t in self._doc_tabs()}
        entries = recovery.pending(exclude=open_tokens)
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
                    loaded = formats.load(e.docx_path)
                except DocumentIOError:
                    continue
                tab = DocumentTab(loaded, None, title=f"Wiederhergestellt – {e.title}")
                tab.token = e.token
                tab.editor.document().setModified(True)
                self._add_tab(tab)
        else:
            for e in entries:
                recovery.discard(e.token)

    # ==== Bearbeiten/Einfügen ===================================================================
    def paste_plain(self):
        e = self.current_editor()
        if e:
            t = QApplication.clipboard().text()
            if t:
                e.textCursor().insertText(t)

    def choose_color(self):
        c = QColorDialog.getColor(Qt.black, self, "Schriftfarbe")
        if c.isValid():
            self._ed(lambda e: e.set_text_color(c))

    def choose_highlight(self):
        c = QColorDialog.getColor(QColor("yellow"), self, "Texthervorhebungsfarbe")
        if c.isValid():
            self._ed(lambda e: e.set_highlight(c))

    def paragraph_dialog(self):
        e = self.current_editor()
        if not e:
            return
        bf = e.textCursor().blockFormat()
        lh = bf.lineHeight() / 100 if bf.lineHeightType() == 1 and bf.lineHeight() else 1.0
        d = ParagraphDialog(px_to_mm(bf.leftMargin()), px_to_mm(bf.rightMargin()), px_to_mm(bf.textIndent()),
                            bf.topMargin() * 0.75, bf.bottomMargin() * 0.75, lh, self)
        if d.exec():
            e.set_indents(d.left.value(), d.right.value(), d.first.value())
            e.set_paragraph_spacing(d.before.value(), d.after.value())
            e.set_line_spacing(d.line.value())

    def show_main_menu(self):
        daten = next(m for m in self.band.daten["menues"] if m["name"] == "Datei")
        self._tafel = MenueTafel(daten["punkte"], self.befehle, self)
        self._tafel.zeigen_unter(self.band.menue_knopf)

    def toggle_sidebar(self):
        on = not self.sidebar.isVisible()
        self.sidebar.setVisible(on)
        self.settings.set("ui/seitenleiste", on)

    def toggle_menubar(self):
        self.menubar_wanted = not self.menubar_wanted
        self.menuBar().setVisible(self.menubar_wanted)
        self.settings.set("ui/menueleiste", self.menubar_wanted)

    def rename_document(self):
        t = self.current_tab()
        if not t or not t.path:
            QMessageBox.information(self, "Umbenennen", "Das Dokument ist noch nicht gespeichert.")
            return
        neu, ok = QInputDialog.getText(self, "Umbenennen", "Neuer Dateiname:", text=os.path.basename(t.path))
        if not ok or not neu.strip() or neu == os.path.basename(t.path):
            return
        ziel = os.path.join(os.path.dirname(t.path), neu.strip())
        if os.path.exists(ziel):
            QMessageBox.warning(self, "Umbenennen", "Eine Datei mit diesem Namen gibt es schon.")
            return
        try:
            os.rename(t.path, ziel)
        except OSError as e:
            QMessageBox.warning(self, "Umbenennen", f"Nicht möglich: {e.strerror or e}")
            return
        self.settings.remove_recent(t.path)
        t.set_path(ziel)
        self.settings.add_recent(ziel)
        self._update_tab_titles()

    def toggle_marks(self, on: bool):
        self.marks_on = on
        from PySide6.QtGui import QTextOption
        for t in self._doc_tabs():
            opt = t.editor.document().defaultTextOption()
            flags = QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators
            opt.setFlags(opt.flags() | flags if on else opt.flags() & ~flags)
            t.editor.document().setDefaultTextOption(opt)

    def insert_table(self):
        if not self.current_editor():
            return
        d = TableDialog(self)
        if d.exec():
            self._ed(lambda e: e.insert_table(d.rows.value(), d.cols.value(), d.borders.isChecked()))

    def insert_image(self):
        e = self.current_editor()
        if not e:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Bild einfügen", self.settings.get("last_dir", os.path.expanduser("~")),
                                              "Bilder (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;Alle Dateien (*)")
        if path and not e.insert_image(path):
            QMessageBox.warning(self, "Bild einfügen", "Die Datei ist kein lesbares Bild.")

    def insert_link(self):
        e = self.current_editor()
        if not e:
            return
        url, ok = QInputDialog.getText(self, "Hyperlink", "Adresse (z. B. https://…):")
        if ok and url.strip():
            e.insert_link(url.strip())

    def insert_date(self):
        self._ed(lambda e: e.textCursor().insertText(datetime.now().strftime("%d.%m.%Y")))

    def edit_header_footer(self, header: bool):
        t = self.current_tab()
        if not t:
            return
        page = t.page.copy()
        hf = page.header if header else page.footer
        d = HeaderFooterDialog("Kopfzeile" if header else "Fußzeile", hf, self)
        if d.exec():
            if header:
                page.header = d.value()
            else:
                page.footer = d.value()
            t.editor.page_settings_changed(page)

    def insert_page_number(self):
        t = self.current_tab()
        if not t:
            return
        page = t.page.copy()
        if page.footer.is_empty():
            page.footer = HeaderFooter("{PAGE}", "center")
        elif "{PAGE}" not in page.footer.text:
            page.footer.text += " {PAGE}"
        t.editor.page_settings_changed(page)

    def find_dialog_show(self):
        if self.current_editor():
            self.find_dialog.show_with_selection()

    # ==== Seite ==================================================================================
    def _page_change(self, fn):
        t = self.current_tab()
        if not t:
            return
        p = t.page.copy(); fn(p); t.editor.page_settings_changed(p)

    def set_margins(self, top, bottom, left, right):
        def f(p):
            p.margin_top_mm, p.margin_bottom_mm, p.margin_left_mm, p.margin_right_mm = top, bottom, left, right
        self._page_change(f)

    def set_orientation(self, landscape: bool):
        self._page_change(lambda p: p.set_orientation(landscape))

    def set_paper(self, name: str):
        self._page_change(lambda p: p.set_paper(name))

    def page_setup(self):
        t = self.current_tab()
        if not t:
            return
        d = PageSetupDialog(t.page, self)
        if d.exec():
            t.editor.page_settings_changed(d.result_page())

    # ==== Sonstiges ===============================================================================
    def word_count(self):
        e = self.current_editor()
        if not e:
            return
        txt = e.document().toPlainText()
        QMessageBox.information(self, "Wortanzahl",
                                f"Wörter: {len(txt.split())}\nZeichen (mit Leerzeichen): {len(txt)}\n"
                                f"Zeichen (ohne Leerzeichen): {len(''.join(txt.split()))}\n"
                                f"Absätze: {e.document().blockCount()}\nSeiten: {e.page_count}")

    def show_info(self):
        t = self.current_tab()
        if not t:
            return
        size = os.path.getsize(t.path) if t.path and os.path.exists(t.path) else None
        QMessageBox.information(self, "Dokumentinformationen",
                                f"Name: {t.title}\nOrt: {t.path or 'noch nicht gespeichert'}\n"
                                f"Größe: {f'{size/1024:.1f} KB' if size is not None else '–'}\n"
                                f"Papier: {t.page.paper_name()} {'quer' if t.page.landscape else 'hoch'}\n"
                                f"Seiten: {t.editor.page_count}   Wörter: {t.editor.word_count()}")

    def show_options(self):
        from ..widgets.options_dialog import OptionsDialog
        d = OptionsDialog(self.settings, self)
        if d.exec():
            self.autosave.start(max(10, self.settings.get_int("autosave_seconds", 60)) * 1000)
            QApplication.instance().setProperty("lunivo_apply_theme", True)
            from ..theme import apply_theme
            apply_theme(QApplication.instance(), self.settings.get("theme", "system"))

    def toggle_fullscreen(self, on: bool):
        self.showFullScreen() if on else self.showNormal()

    def about(self):
        QMessageBox.about(self, "Über Lunivo Writer",
                          f"Lunivo Writer {__version__}\nNative Textverarbeitung (Python, Qt 6 / PySide6).\n"
                          "Keine Webtechnik, kein Webserver. Dokumente bleiben auf diesem Rechner.")
