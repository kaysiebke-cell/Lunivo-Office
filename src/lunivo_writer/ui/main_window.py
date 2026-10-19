"""Hauptfenster: Menüleiste, Schnellzugriff, Ribbon, Dokumentreiter, Statusleiste."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QFont, QKeySequence, QTextFormat
from PySide6.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QFileDialog, QInputDialog, QLineEdit, QMainWindow, QMenu, QMessageBox, QWidget,
)

from lunivo_writer import __version__
from lunivo_writer.services import file_service as formats
from lunivo_writer.models.report import DocumentIOError, IOReport, PasswortNoetig
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.models.page import HeaderFooter, PageSettings, px_to_mm
from lunivo_writer.editor.pagination import export_pdf, print_document
from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ai.ai_service import KIDienst
from lunivo_writer.proofing.proofing_service import WritingAssistant
from lunivo_writer.core.document_manager import DocumentManager
from lunivo_writer.ui.statusbar.status_bar import StatusBar
from lunivo_writer.ui.dialogs.dokument_dialoge import FindReplaceDialog, HeaderFooterDialog, PageSetupDialog, ParagraphDialog, TableDialog
from lunivo_writer.ui.document.document_tabs import DocTabs
from lunivo_writer.ui.document.document_area import DocumentTab
from lunivo_writer.ui.ribbon.menue_tafel import MenueTafel
from lunivo_writer.ui.document.navigation import NavigationPanel
from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand, lade_register
from lunivo_writer.ui.sidebar.sidebar import SchreibhilfePanel
from lunivo_writer.ui.document.start_page import StartPage
from lunivo_writer.core.commands import Befehle

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
        scr = QApplication.primaryScreen().availableGeometry() if QApplication.primaryScreen() else None
        self.resize(min(1380, scr.width()) if scr else 1380, min(860, scr.height()) if scr else 860)
        self.marks_on = False
        self.lesemodus = False
        self.docs = DocTabs()
        self.docs.tabCloseRequested.connect(self.close_tab)
        self.docs.currentChanged.connect(self._tab_changed)
        self.docs.newRequested.connect(self.new_document)
        self.docs.kontextGewuenscht.connect(self.reiter_menue)
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
        self.ki = KIDienst(self.assistant, self)
        self.ki.status.connect(lambda t: self.lbl_msg.setText(t))
        from lunivo_writer.ui.dialogs import dokument_dialoge as _dlg
        _dlg.set_einheit(self.settings.get("ui/masseinheit", "Millimeter"))
        from lunivo_writer.ui.widgets.live_vorschau import LiveVorschau
        self.vorschau = LiveVorschau(self)
        self.dokumente = DocumentManager(self.settings)
        self.befehle = Befehle(self)
        self._build_actions()
        self._zusatz_kuerzel()
        self._build_status()
        from lunivo_writer.editor import stile
        stile.laden(self.settings.get("stile/aenderungen", ""))
        self.menubar_wanted = self.settings.get_bool("ui/menueleiste", False)
        self._symbole_anwenden()
        self.band = self._band_erzeugen()
        self.band.menue_knopf.clicked.connect(self.show_main_menu)
        self._build_menu()
        self.menuBar().setVisible(self.menubar_wanted)
        self.sidebar = SchreibhilfePanel(self.assistant)
        self.sidebar.verbinde_ki(self.ki, self)
        self._bereiche_bauen()
        self.sidebar.setVisible(self.settings.get_bool("ui/seitenleiste", True))
        central = QWidget()
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(self.docs.leiste)
        self.band_lay = lay
        lay.addWidget(self.band)
        mitte = QHBoxLayout(); mitte.setSpacing(0)
        self.arbeit = QWidget()
        mitte.setContentsMargins(0, 0, 0, 0)
        self.navigation = NavigationPanel(self.current_editor)
        self.navigation.aktion = self._nav_aktion
        self.navigation.hide()
        mitte.addWidget(self.navigation)
        mitte.addWidget(self.docs.stack, 1)
        mitte.addWidget(self.sidebar)
        mitte.addWidget(self._leiste_rechts())
        self.arbeit.setLayout(mitte)
        lay.addWidget(self.arbeit, 1)
        from lunivo_writer.ui.backstage import Backstage
        self.backstage = Backstage(self)
        self.backstage.schliessen.connect(self.backstage_schliessen)
        self.backstage.hide()
        lay.addWidget(self.backstage, 1)
        self._backstage_verbinden()
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
        self.ansicht_optionen_anwenden()
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
        self.a_tabs = A("Tabstopps …", self.tabstopp_dialog)
        self.a_goto = A("Gehe zu …", self.befehle.geheZu, "Ctrl+G")

        self.a_bold = A("F", self.befehle.fett, "Ctrl+B")
        self.a_italic = A("K", self.befehle.kursiv, "Ctrl+I")
        self.a_under = A("U", self.befehle.unter, "Ctrl+U")
        self.a_strike = A("S̶", self.befehle.durch, None)
        self.a_sup = A("x²", self.befehle.hoch, "Ctrl+Shift+=")
        self.a_sub = A("x₂", self.befehle.tief, "Ctrl+=")
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
        self.a_left = A("⯇", self.befehle.links, "Ctrl+L")
        self.a_center = A("☰", self.befehle.mitte, "Ctrl+E")
        self.a_right = A("⯈", self.befehle.rechts, "Ctrl+R")
        self.a_justify = A("≣", self.befehle.block, "Ctrl+J")
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
        self.a_lesemodus = A("Lesemodus", self.toggle_lesemodus, "Ctrl+Shift+L")
        self.a_navigation = A("Navigationsbereich", self.toggle_navigation, "Ctrl+Shift+N")
        for name, a in list(vars(self).items()):
            if name.startswith("a_") and isinstance(a, QAction):
                self.addAction(a)            # Tastenkürzel gelten auch bei verstecktem Menü

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
                  self.a_paste_plain, None, self.a_find, self.a_replace, self.a_goto, self.a_select_all):
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
        sb = StatusBar()
        self.setStatusBar(sb)
        self.statusleiste = sb
        self.lbl_msg, self.lbl_words, self.lbl_page, self.lbl_zoom = sb.lbl_msg, sb.lbl_words, sb.lbl_page, sb.lbl_zoom
        self.zoom_regler = sb.zoom_regler
        sb.zoom_kleiner.connect(lambda: self.befehle.kleiner())
        sb.zoom_groesser.connect(lambda: self.befehle.groesser())
        sb.zoom_stufe.connect(lambda: self.befehle.zoomStufe())
        sb.zoom_geaendert.connect(self._regler_bewegt)

    # ==== Hilfen ====================================================================
    def current_tab(self) -> DocumentTab | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, DocumentTab) else None

    def current_editor(self) -> DocumentEditor | None:
        t = self.current_tab()
        return t.editor if t else None

    def _ed(self, fn):
        self.vorschau.ende()
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
        self._zoom_anzeigen()
        self.assistant.attach(self.current_editor())

    def _regler_bewegt(self, v: int):
        e = self.current_editor()
        if e and abs(e.zoom * 100 - v) > 0.5:
            e.set_zoom(v / 100)

    def _zoom_anzeigen(self, f: float | None = None):
        e = self.current_editor()
        f = f if f is not None else (e.zoom if e else 1.0)
        self.statusleiste.zoom_zeigen(f)

    def _connect_tab(self, tab: DocumentTab):
        e = tab.editor
        e.zoomChanged.connect(lambda f, ed=e: ed is self.current_editor() and self._zoom_anzeigen(f))
        e.formatChanged.connect(self._sync_later)
        e.pageInfoChanged.connect(lambda *_: self._sync_status())
        e.document().modificationChanged.connect(lambda _m: self._update_tab_titles())
        e.document().contentsChanged.connect(self._sync_status)
        e.document().contentsChanged.connect(self.assistant.dokument_geaendert)
        e.document().contentsChanged.connect(self.navigation.spaeter)
        e.opt = lambda name, std=True: self.settings.get_bool(name, std)
        e.opt_text = lambda name, std="": self.settings.get(name, std)
        e.autor = self.autor_angaben
        e.mini_hook = self.mini_zeigen
        e.zusatzGeaendert.connect(self.navigation.spaeter)
        e.set_marken(self.settings.get_bool("ui/marken", True))
        self.formatzeichen_anwenden(e)
        self.lineale_anwenden(tab)
        self._lesehilfe_auf(e)
        felder = self.band.felder
        if felder and e is not None:
            pass

    def _sync_later(self):
        self._sync_timer.start()

    def _sync_format(self):
        e = self.current_editor()
        self.band.aktualisieren(e is not None)
        self.band.kontext("tabelle", bool(e) and e.textCursor().currentTable() is not None)
        bf = e.bild_format() if e else None
        from lunivo_writer.editor import formen
        art = (formen.objekt(bf) or {}).get("art") if bf is not None else None
        self.band.kontext("bild", bf is not None and art not in ("form", "gruppe", "smartart"))
        self.band.kontext("form", art in ("form", "gruppe"))
        self.band.kontext("smartart", art == "smartart")
        f = self.band.felder
        if e is None or not f:
            return
        cf = e.textCursor().charFormat()
        fam = cf.fontFamilies()[0] if cf.fontFamilies() else e.document().defaultFont().family()
        f["font"].blockSignals(True); f["font"].setCurrentFont(QFont(fam)); f["font"].blockSignals(False)
        size = cf.fontPointSize() or e.document().defaultFont().pointSizeF() or 11
        f["groesse"].blockSignals(True); f["groesse"].setEditText(f"{size:g}"); f["groesse"].blockSignals(False)
        t = self.current_tab()
        if t is not None and "rand_oben" in f:                       # Maßfelder im Reiter Seitenlayout
            p = t.page
            for schl, wert in (("oben", p.margin_top_mm), ("unten", p.margin_bottom_mm), ("links", p.margin_left_mm), ("rechts", p.margin_right_mm)):
                sp = f["rand_" + schl]
                if not sp.hasFocus():
                    sp.blockSignals(True); sp.setValue(wert); sp.blockSignals(False)
        st = e.current_style()
        f["stil"].blockSignals(True); f["stil"].setCurrentText("Fließtext" if st == "Standard" else st); f["stil"].blockSignals(False)

    def _sync_status(self):
        e = self.current_editor()
        if e is None:
            self.statusleiste.seite(None, None); self.statusleiste.zaehler(0, 0)
            return
        txt = e.document().toPlainText()
        self.statusleiste.seite(e.current_page(), e.page_count)
        self.statusleiste.zaehler(len(txt.split()), len(txt))

    def _verbinde_felder(self):
        f = self.band.felder
        if not f:
            return
        f["font"].activated.connect(lambda _: self._ed(lambda e: (e.set_font_family(f["font"].currentFont().family()), e.setFocus())))
        f["groesse"].activated.connect(self._size_chosen)
        f["groesse"].lineEdit().editingFinished.connect(self._size_chosen)
        f["stil"].activated.connect(lambda _: self.stil_anwenden(f["stil"].currentText()))

    def stil_anwenden(self, name: str):
        name = "Standard" if name == "Fließtext" else name
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
            self.dokumente.vergessen(path); self.start.set_recent(self.dokumente.zuletzt())
            return False
        tab = DocumentTab(loaded, path)
        self._add_tab(tab)
        self.dokumente.gelesen(path); self.start.set_recent(self.dokumente.zuletzt())
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
        folder = os.path.dirname(tab.path) if tab.path else (self.settings.get("speichern/ordner", "") or
                                                             self.settings.get("last_dir", os.path.expanduser("~")))
        base = os.path.splitext(tab.title)[0] or "Unbenannt"
        if only:
            flt = formats.SAVE_FILTERS[only]; default = only
        else:
            standard = self.settings.get("speichern/standard", ".docx")
            flt = ("Word-Dokument (*.docx);;Textdatei (*.txt);;Webseite (*.html)" if standard != ".txt"
                   else "Textdatei (*.txt);;Word-Dokument (*.docx);;Webseite (*.html)")
            default = standard if standard in (".docx", ".txt") else ".docx"
        path, chosen = QFileDialog.getSaveFileName(self, title, os.path.join(folder, base + default), flt)
        if not path:
            return None
        if not os.path.splitext(path)[1]:
            path += ".txt" if "txt" in chosen else ".html" if "html" in chosen else default
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

    def print_dialog(self):
        t = self.current_tab()
        if not t:
            return
        pr = self._neuer_drucker()
        dlg = QPrintDialog(pr, self)
        dlg.setOption(QPrintDialog.PrintPageRange, True)
        dlg.setMinMax(1, t.editor.page_count)
        if dlg.exec():
            self._vor_dem_drucken(t)
            print_document(pr, t.editor.document(), t.page, dict(self.druckoptionen(), noten=t.editor.noten))
            self.statusBar().showMessage("An den Drucker gesendet.", 4000)

    def print_preview(self):
        t = self.current_tab()
        if not t:
            return
        pr = self._neuer_drucker()
        dlg = QPrintPreviewDialog(pr, self)
        dlg.paintRequested.connect(lambda p: print_document(p, t.editor.document(), t.page, dict(self.druckoptionen(), noten=t.editor.noten)))
        dlg.resize(1000, 800)
        dlg.exec()

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
        from lunivo_writer.ui.dialogs.vorlagen_dialog import VorlagenDialog
        d = VorlagenDialog(self, self.settings, self.current_tab() is not None)
        if not d.exec():
            return
        if d.als_vorlage_gewuenscht:
            self.als_vorlage_speichern()
            return
        art, wert = d.auswahl
        if art == "geruest":
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

    def als_vorlage_speichern(self):
        t = self.current_tab()
        if not t:
            return
        from lunivo_writer.editor import vorlagen
        ordner = vorlagen.vorlagenordner(self.settings)
        os.makedirs(ordner, exist_ok=True)
        pfad, _ = QFileDialog.getSaveFileName(self, "Als Vorlage speichern", os.path.join(ordner, os.path.splitext(t.title)[0] + ".docx"),
                                              "Word-Dokument (*.docx)")
        if pfad:
            if not pfad.lower().endswith(".docx"):
                pfad += ".docx"
            self._write(t, pfad, mark_saved=False)

    # ==== Fenster ====================================================================
    @staticmethod
    def alle_fenster() -> list["MainWindow"]:
        return [w for w in QApplication.topLevelWidgets() if isinstance(w, MainWindow) and w.isVisible()]

    def neues_fenster(self):
        """Das aktuelle Dokument in einem zweiten Fenster öffnen (eigene Kopie, keine Synchronisation)."""
        t = self.current_tab()
        if t is None:
            w = MainWindow(self.settings); w.show(); return w
        if t.is_modified() or not t.path:
            r = QMessageBox.question(self, "Neues Fenster",
                                     "Das neue Fenster zeigt die gespeicherte Datei als eigene Kopie. Änderungen werden nicht zwischen "
                                     "den Fenstern abgeglichen.\n\nJetzt speichern und das Fenster öffnen?")
            if r != QMessageBox.Yes or not self.save():
                return None
        w = MainWindow(self.settings)
        w.show()
        w.open_path(t.path)
        return w

    def fenster_anordnen(self, art: str):
        fenster = self.alle_fenster()
        if len(fenster) < 2:
            self.statusBar().showMessage("Zum Anordnen werden mindestens zwei Fenster gebraucht (Ansicht ▸ Neues Fenster).", 5000)
            return
        r = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        n = len(fenster)
        if art == "nebeneinander":
            spalten, zeilen = n, 1
        elif art == "untereinander":
            spalten, zeilen = 1, n
        else:
            spalten = int(n ** 0.5 + 0.999); zeilen = (n + spalten - 1) // spalten
        bw, bh = r.width() // spalten, r.height() // zeilen
        for i, f in enumerate(fenster):
            f.showNormal()
            f.setGeometry(r.x() + (i % spalten) * bw, r.y() + (i // spalten) * bh, bw, bh)

    def fensterliste_menue(self) -> QMenu:
        m = QMenu()
        for f in self.alle_fenster():
            for t in f._doc_tabs():
                a = m.addAction(t.title + ("  (dieses Fenster)" if f is self else ""))
                a.triggered.connect(lambda _=False, f=f, t=t: (f.raise_(), f.activateWindow(), f.tabs.setCurrentWidget(t)))
        if m.isEmpty():
            m.addAction("Keine Dokumente geöffnet").setEnabled(False)
        return m

    def closeEvent(self, ev):
        for i in range(self.tabs.count() - 1, -1, -1):
            if isinstance(self.tabs.widget(i), DocumentTab) and not self.close_tab(i):
                ev.ignore(); return
        self.settings.set("window/geometry", self.saveGeometry())
        ev.accept()

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
        al = bf.alignment()
        ai = 1 if al & Qt.AlignHCenter else 2 if al & Qt.AlignRight else 3 if al & Qt.AlignJustify else 0
        d = ParagraphDialog(px_to_mm(bf.leftMargin()), px_to_mm(bf.rightMargin()), px_to_mm(bf.textIndent()),
                            bf.topMargin() * 0.75, bf.bottomMargin() * 0.75, lh, self, ai,
                            bool(bf.pageBreakPolicy() & QTextFormat.PageBreak_AlwaysBefore))
        if d.exec():
            e.set_alignment([Qt.AlignLeft, Qt.AlignHCenter, Qt.AlignRight, Qt.AlignJustify][d.align.currentIndex()])
            e.set_page_break_before(d.umbruch.isChecked())
            e.set_indents(d.left.value(), d.right.value(), d.first.value())
            e.set_paragraph_spacing(d.before.value(), d.after.value())
            e.set_line_spacing(d.line.value())

    def tabstopp_dialog(self):
        e = self.current_editor()
        if not e:
            return
        from lunivo_writer.ui.dialogs.tabstopp_dialog import TabstoppDialog
        d = TabstoppDialog(self, e.textCursor().blockFormat().tabPositions())
        if d.exec():
            e.set_tabstopps(d.ergebnis())

    def _lesehilfe_auf(self, e):
        from lunivo_writer.ui.dialogs.lesehilfe_dialog import PAPIERTOENE
        s = self.settings
        e.set_lesehilfe(PAPIERTOENE.get(s.get("lesehilfe/papier", "Weiß"), "#ffffff"),
                        float(s.get("lesehilfe/buchstaben", 0)), float(s.get("lesehilfe/wort", 0)))
        self.silbenfarben_anwenden(e)
        self.versteckt_anwenden(e)

    def mini_zeigen(self, ed, pos, rechtsklick: bool = False):
        from lunivo_writer.ui.widgets.mini_leiste import MiniLeiste
        if getattr(self, "_mini", None) is None:
            self._mini = MiniLeiste(self)
        if ed is None:
            self._mini.hide()
        else:
            self._mini.zeigen(ed, pos, rechtsklick)

    def markup_neu(self) -> None:
        """Markup- und Sprechblasen-Einstellungen haben sich geändert: Seitenrand für Blasen und Auszeichnung neu aufbauen."""
        for t in self._doc_tabs():
            t.editor.apply_page(t.editor.page)
            t.editor._overlays_neu()
            t.editor.viewport().update()

    def versteckt_anwenden(self, e=None):
        an = self.settings.get_bool("ui/versteckt_zeigen", False)
        for ed in ([e] if e is not None else [t.editor for t in self._doc_tabs()]):
            ed.set_versteckt_zeigen(an)

    def silbenfarben_anwenden(self, e=None):
        from lunivo_writer.editor import silbenfarben as S
        k = S.konfig_lesen(self.settings)
        for ed in ([e] if e is not None else [t.editor for t in self._doc_tabs()]):
            ed.set_silbenfarben(k)

    def lineale_anwenden(self, tab=None):
        h = self.settings.get_bool("ansicht/lineal", False)
        v = self.settings.get_bool("ansicht/lineal_hoch", False)
        for t in ([tab] if tab is not None else self._doc_tabs()):
            t.zeige_lineale(h, v)
        self.band.aktualisieren(self.current_tab() is not None)

    def formatzeichen_anwenden(self, e=None):
        """Formatierungszeichen für neue Reiter: Zustand aus Optionen (ui/steuerzeichen)."""
        from PySide6.QtGui import QTextOption
        an = self.settings.get_bool("ui/steuerzeichen", False)
        self.marks_on = an
        for ed in ([e] if e is not None else [t.editor for t in self._doc_tabs()]):
            opt = ed.document().defaultTextOption()
            fl = QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators
            opt.setFlags(opt.flags() | fl if an else opt.flags() & ~fl)
            ed.document().setDefaultTextOption(opt)

    def ansicht_optionen_anwenden(self):
        """Statusleiste, QuickInfo, Bedienschrift, Symbolgröße — aus den Optionen."""
        self.statusBar().setVisible(self.settings.get_bool("ui/statusleiste", True))
        app = QApplication.instance()
        fam = self.settings.get("ui/bedienschrift", "")
        gr = self.settings.get_int("ui/bedienschrift_groesse", 0)
        if fam or gr:
            f = app.font()
            if fam:
                f.setFamily(fam)
            if gr:
                f.setPointSize(gr)
            app.setFont(f)
        from lunivo_writer.ui.widgets import icons
        faktor = {"klein": 0.8, "mittel": 1.0, "gross": 1.3}.get(self.settings.get("ui/icongroesse", "mittel"), 1.0)
        if abs(icons.FAKTOR - faktor) > 1e-6:
            icons.FAKTOR = faktor
            icons.leeren()
            self.neu_bauen_band()

    def lesehilfe_anwenden(self):
        for t in self._doc_tabs():
            self._lesehilfe_auf(t.editor)

    def set_marken(self, an: bool):
        self.settings.set("ui/marken", an)
        for t in self._doc_tabs():
            t.editor.set_marken(an)

    def chat_oeffnen(self, vorlage: str):
        if not self.sidebar.isVisible():
            self.toggle_sidebar()
        self.sidebar.zeige_bereich(1)
        ch = getattr(self.sidebar, "chat", None)
        if ch is not None:
            ch.eingabe.setText(vorlage); ch.eingabe.setFocus()

    def vorlesen(self, ab_hier: bool):
        from lunivo_writer.services import vorlesen as v
        e = self.current_editor()
        if e is None:
            return
        c = e.textCursor()
        if c.hasSelection():
            text = c.selectedText().replace("\u2029", "\n")
        elif ab_hier:
            text = e.document().toPlainText()[c.position():]
        else:
            text = e.document().toPlainText()
        try:
            ok = v.lies_vor(text, self.settings.get("vorlesen/stimme", ""), self.settings.get_int("vorlesen/tempo", 0))
        except v.VorlesenFehler as ex:
            QMessageBox.information(self, "Vorlesen", str(ex))
            return
        self.lbl_msg.setText("Vorlesen …" if ok else "Nichts zum Vorlesen.")

    def stimme_waehlen(self):
        from lunivo_writer.services import vorlesen as v
        liste = v.stimmen()
        if not liste:
            QMessageBox.information(self, "Stimme", "Es ist keine Stimme eingerichtet. Siehe docs/INSTALLATION.md.")
            return
        namen = [s["name"] for s in liste]
        n, ok = QInputDialog.getItem(self, "Stimme wählen", "Stimme:", namen, 0, False)
        if ok:
            self.settings.set("vorlesen/stimme", liste[namen.index(n)]["kennung"])

    def _nav_aktion(self, name: str, b: dict):
        e = self.current_editor()
        if e is None:
            return
        if name == "kommentar_weg":
            e.kommentar_loeschen(int(b["wert"]))
        elif name == "aenderung_an":
            e.aenderung_annehmen(b, True)
        elif name == "aenderung_ab":
            e.aenderung_annehmen(b, False)
        elif name == "note_weg":
            e.note_loeschen(b["art"], b["id"])
        elif name == "note_bearbeiten":
            self.befehle.note_bearbeiten(b["art"], b["id"])
        self.navigation.aktualisieren()

    def zeige_navigation(self, tab: str):
        self.navigation.show()
        self.navigation.zeige_tab(tab)

    def autor_angaben(self) -> tuple[str, str]:
        name = self.settings.get("benutzer/name", "") or "Unbekannt"
        init = self.settings.get("benutzer/initialen", "") or "".join(w[0] for w in name.split()[:2]).upper()
        return name, init

    def toggle_navigation(self):
        self.navigation.setVisible(not self.navigation.isVisible())
        self.navigation.aktualisieren()

    def toggle_lesemodus(self):
        self.lesemodus = not self.lesemodus
        for w in (self.band, self.sidebar):
            w.setVisible(not self.lesemodus and (w is self.band or self.settings.get_bool("ui/seitenleiste", True)))
        for t in self._doc_tabs():
            t.editor.setReadOnly(self.lesemodus)
        self.lbl_msg.setText("Lesemodus — Tastenkürzel Strg+Umschalt+L oder Schreibhilfe ▸ Lesemodus beendet ihn."
                             if self.lesemodus else "")

    def set_theme(self, wahl: str):
        from lunivo_writer.ui.theme import apply_theme
        from lunivo_writer.ui.widgets import icons
        self.settings.set("theme", wahl)
        apply_theme(QApplication.instance(), wahl)
        icons.leeren()
        self.neu_bauen_band()

    def _bereiche_bauen(self):
        from lunivo_writer.ui.ribbon.tabs.ai_tab import KI
        self.sidebar.setze_bereiche(self.band, KI["gruppen"])

    # ---- Oberfläche: Register oder Symbolleisten, angepasst ----------------------------------------------------
    def _symbole_anwenden(self):
        from lunivo_writer.ui.widgets import icons
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import lade_json
        icons.uebersteuern(lade_json(self.settings, "ui/symbol_tausch", {}))

    def _band_erzeugen(self):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import lade_json
        from lunivo_writer.ui.ribbon.toolbars import Symbolleisten
        reg = RegisterBand(self.befehle, lade_register(), lade_json(self.settings, "ui/register_plan", {}),
                           lade_json(self.settings, "ui/schnellzugriff", None))
        if self.settings.get("ui/oberflaeche", "register") != "symbolleisten":
            return reg
        sym = Symbolleisten(self.befehle)
        sym.daten = reg.daten
        sym.gruppe_widget = reg.gruppe_widget            # die Seitenleiste baut ihre Gruppen weiter aus dem Register
        sym._reg = reg
        urspr = sym.aktualisieren

        def aktualisieren(hat=None, _u=urspr, _r=reg):
            _u(hat); _r.aktualisieren(hat)
        sym.aktualisieren = aktualisieren
        return sym

    def oberflaeche_aendern(self, art: str, menueleiste: bool):
        self.settings.set("ui/oberflaeche", art)
        if menueleiste != self.menubar_wanted:
            self.toggle_menubar()
        self.neu_bauen_band()

    def neu_bauen_band(self):
        alt = self.band
        idx = self.band_lay.indexOf(alt)
        self.band = self._band_erzeugen()
        self.band.einklappbar = self.settings.get_bool("ui/band_doppelklick", True)
        self.band.menue_knopf.clicked.connect(self.show_main_menu)
        self.band_lay.insertWidget(idx, self.band)
        alt.setParent(None); alt.deleteLater()
        self._backstage_verbinden()
        self._verbinde_felder()
        self._bereiche_bauen()
        self._refresh_ui()

    # ---- Backstage (Reiter „Datei“) ------------------------------------------------------------------------------
    _letzter_reiter = 1
    _bs_zeit = 0.0

    def _backstage_verbinden(self):
        r = getattr(self.band, "reiter", None)
        if r is None:
            return
        self.backstage.hide()
        self.arbeit.show()
        r.currentChanged.connect(self._reiter_gewechselt)
        r.tabBarClicked.connect(self._reiter_angeklickt)

    def _ist_datei(self, i: int) -> bool:
        r = self.band.reiter
        return 0 <= i < r.count() and r.tabText(i) == "Datei"

    def _reiter_gewechselt(self, i: int):
        if self._ist_datei(i):
            self.backstage_oeffnen()
        else:
            self._letzter_reiter = i
            self.backstage_zu()

    def _reiter_angeklickt(self, i: int):
        import time
        if self._ist_datei(i) and self.backstage.isVisible() and time.monotonic() - self._bs_zeit > 0.4:   # zweiter Klick schließt
            self.backstage_schliessen()

    def backstage_oeffnen(self, seite: str = "zuletzt"):
        import time
        self._bs_zeit = time.monotonic()
        self.band.stapel.hide()
        self.band.linie.hide()
        self.arbeit.hide()
        self.backstage.oeffnen(seite)
        self.backstage.show()

    def backstage_zu(self):
        if not self.backstage.isVisible():
            return
        self.backstage.hide()
        self.arbeit.show()
        if not self.band._eingeklappt:
            self.band.stapel.show()
        self.band.linie.show()

    def backstage_schliessen(self):
        r = self.band.reiter
        if self._ist_datei(r.currentIndex()):
            r.setCurrentIndex(self._letzter_reiter if not self._ist_datei(self._letzter_reiter) else 1)
        self.backstage_zu()

    def show_main_menu(self):
        daten = next(m for m in self.band.daten["menues"] if m["name"] == "Datei")
        self._tafel = MenueTafel(daten["punkte"], self.befehle, self)
        self._tafel.zeigen_unter(self.band.menue_knopf)

    def _leiste_rechts(self):
        """Schmale Leiste rechts: Chat und Schreibhilfe schalten die Seitenleiste um."""
        from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout
        from lunivo_writer.ui.widgets import icons
        leiste = QFrame()
        leiste.setObjectName("leisteRechts")
        leiste.setFixedWidth(44)
        v = QVBoxLayout(leiste)
        v.setContentsMargins(4, 8, 4, 8)
        v.setSpacing(6)
        self._rechts = {}
        for i, (sym, tip) in enumerate((("tafel", "Schreibhilfe"), ("chat", "KI-Chat"))):
            b = QToolButton()
            b.setIcon(icons.icon(sym, 20))
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setFixedSize(34, 34)
            b.clicked.connect(lambda _=False, i=i: self._rechts_klick(i))
            v.addWidget(b)
            self._rechts[i] = b
        v.addStretch(1)
        self.sidebar.bereich_geaendert.connect(lambda _i: self._rechts_sync())
        self._rechts_sync()
        return leiste

    def _rechts_klick(self, i: int):
        if not self.sidebar.isHidden() and self.sidebar.stapel.currentIndex() == i:
            self.toggle_sidebar()
        else:
            if self.sidebar.isHidden():
                self.toggle_sidebar()
            self.sidebar.zeige_bereich(i)
        self._rechts_sync()

    def _rechts_sync(self):
        sicht = not self.sidebar.isHidden()
        for i, b in self._rechts.items():
            b.setChecked(sicht and self.sidebar.stapel.currentIndex() == i)

    def toggle_sidebar(self):
        on = self.sidebar.isHidden()
        self.sidebar.setVisible(on)
        self.settings.set("ui/seitenleiste", on)
        if hasattr(self, "_rechts"):
            self._rechts_sync()

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

    def toggle_sperre(self):
        """Überprüfen ▸ Bearbeitung einschränken: Dokument schreibgeschützt (nur in dieser Sitzung)."""
        t = self.current_tab() if hasattr(self, "current_tab") else None
        if not t:
            return
        t.gesperrt = not getattr(t, "gesperrt", False)
        t.editor.setReadOnly(t.gesperrt or self.lesemodus)
        self.statusBar().showMessage("Bearbeitung gesperrt." if t.gesperrt else "Bearbeitung freigegeben.", 4000)

    def toggle_marks(self, on: bool):
        self.marks_on = on
        self.settings.set("ui/steuerzeichen", on)
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
        page = t.editor.abschnitt_seite()
        erste = False
        if page.diff_first:
            from PySide6.QtWidgets import QInputDialog
            w, ok = QInputDialog.getItem(self, "Kopf- und Fußzeile", "Welche Seiten?", ["Erste Seite", "Übrige Seiten"], 0, False)
            if not ok:
                return
            erste = w == "Erste Seite"
        if erste:
            hf = page.first_header if header else page.first_footer
        else:
            hf = page.header if header else page.footer
        d = HeaderFooterDialog(("Kopfzeile" if header else "Fußzeile") + (" (erste Seite)" if erste else ""), hf, self)
        if d.exec():
            if erste:
                if header:
                    page.first_header = d.value()
                else:
                    page.first_footer = d.value()
            elif header:
                page.header = d.value()
            else:
                page.footer = d.value()
            t.editor.page_settings_changed(page)

    def insert_page_number(self):
        t = self.current_tab()
        if not t:
            return
        page = t.editor.abschnitt_seite()
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
        p = t.editor.abschnitt_seite(); fn(p); t.editor.page_settings_changed(p)

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
        d = PageSetupDialog(t.editor.abschnitt_seite(), self)
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

    def show_options(self, seite: str | None = None):
        from lunivo_writer.ui.dialogs.optionen import OptionenDialog
        d = OptionenDialog(self, seite)
        d.exec()
        self.ki.geaendert.emit()

    def toggle_fullscreen(self, on: bool):
        self.showFullScreen() if on else self.showNormal()

    def about(self):
        QMessageBox.about(self, "Über Lunivo Writer",
                          f"Lunivo Writer {__version__}\nNative Textverarbeitung (Python, Qt 6 / PySide6).\n"
                          "Keine Webtechnik, kein Webserver. Dokumente bleiben auf diesem Rechner.")
