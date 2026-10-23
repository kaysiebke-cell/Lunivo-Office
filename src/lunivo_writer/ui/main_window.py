"""Hauptfenster: Menüleiste, Schnellzugriff, Ribbon, Dokumentreiter, Statusleiste."""
from __future__ import annotations

import os

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QFont, QKeySequence, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox, QWidget

from lunivo_writer import __version__
from lunivo_writer.editor import stile
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ai.ai_service import KIDienst
from lunivo_writer.proofing.proofing_service import WritingAssistant
from lunivo_writer.core.document_manager import DocumentManager
from lunivo_writer.ui.statusbar.status_bar import StatusBar
from lunivo_writer.ui.document.document_tabs import DocTabs
from lunivo_writer.ui.document.document_area import DocumentTab
from lunivo_writer.ui.document.navigation import NavigationPanel
from lunivo_writer.ui.sidebar.sidebar import SchreibhilfePanel
from lunivo_writer.core.commands import Befehle

from lunivo_writer.ui.hauptfenster.dateien import DateienBaustein
from lunivo_writer.ui.hauptfenster.bearbeiten import BearbeitenBaustein
from lunivo_writer.ui.hauptfenster.oberflaeche import OberflaecheBaustein
from lunivo_writer.ui.hauptfenster.backstage_steuerung import BackstageBaustein
MARGIN_PRESETS = {
    "Normal (2,5 cm)": (25, 25, 25, 25),
    "Schmal (1,3 cm)": (12.7, 12.7, 12.7, 12.7),
    "Mittel (1,9 cm)": (19.1, 19.1, 19.1, 19.1),
    "Breit (5,1 cm links/rechts)": (25.4, 25.4, 50.8, 50.8),
}




class MainWindow(DateienBaustein, BearbeitenBaustein, OberflaecheBaustein, BackstageBaustein, QMainWindow):
    lesehilfe_geaendert = Signal()                  # Lesestufe, Papier, Abstände, Zeilenfokus, Silben farbig: Seitenleiste und Optionen ziehen nach


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
        self.leer = QWidget()                      # nur der graue Arbeitsgrund, solange kein Dokument offen ist
        self.leer.setBackgroundRole(QPalette.Dark)
        self.leer.setAutoFillBackground(True)
        self.docs.stack.insertWidget(0, self.leer)
        self.docs.stack.setCurrentWidget(self.leer)
        self.assistant = WritingAssistant(self.settings, parent=self)
        self.assistant.status.connect(lambda t: self.lbl_msg.setText(t))
        self.ki = KIDienst(self.assistant, self)
        self.ki.status.connect(lambda t: self.lbl_msg.setText(t))
        self.ki.geaendert.connect(lambda: hasattr(self, "band") and self.ki_schnell_zeigen())
        from lunivo_writer.ui.dialogs import dokument_dialoge as _dlg
        _dlg.set_einheit(self.settings.get("ui/masseinheit", "Millimeter"))
        from lunivo_writer.ui.widgets.live_vorschau import LiveVorschau
        self.vorschau = LiveVorschau(self)
        self.dokumente = DocumentManager(self.settings)
        self.befehle = Befehle(self)
        self._build_actions()
        self._zusatz_kuerzel()
        self._build_status()
        stile.laden(self.settings.get("stile/aenderungen", ""))
        stile.laden_neu(self.settings.get("stile/eigene", ""))
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
        self.navigation = NavigationPanel(self.current_editor, self)
        self.navigation.aktion = self._nav_aktion
        self.navigation.hide()
        mitte.addWidget(self._leiste_links())
        mitte.addWidget(self.navigation)
        mitte.addWidget(self.docs.stack, 1)
        mitte.addWidget(self.sidebar)
        mitte.addWidget(self._leiste_rechts())
        self.arbeit.setLayout(mitte)
        lay.addWidget(self.arbeit, 1)
        from lunivo_writer.ui.document.noten_feld import NotenFeld
        self.noten_feld = NotenFeld(self.current_editor)
        self.noten_feld.geaendert.connect(lambda: self.navigation.aktualisieren())
        lay.addWidget(self.noten_feld)
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
        self.settings.clear_recent()


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
        self.docs.stack.setCurrentWidget(self.current_tab() if has else self.leer)
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
        e.freiAuswahlGeaendert.connect(self._sync_later)
        from lunivo_writer.ui.widgets.schweb_knopf import SchwebKnopf
        tab._chat_knopf = SchwebKnopf(tab, "chat", "KI-Chat", lambda: self.chat_oeffnen(""))
        self.sidebar.bereich_geaendert.connect(lambda *_: self._chat_knopf_pruefen())
        e.formatChanged.connect(self._effekt_sync)
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
        e.noteAngeklickt.connect(lambda art, nid: self.noten_feld.oeffnen(art, nid))
        e.set_marken(self.settings.get_bool("ui/marken", False))
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
        self.band.kontext("zeichen", bool(e) and getattr(e, "_frei_sel", None) is not None)
        self._zeichen_masse(e)
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


    # ---- Backstage (Reiter „Datei“) ------------------------------------------------------------------------------
    _letzter_reiter = 1

    _bs_zeit = 0.0


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
        """Die Optionen stehen in der Datei-Ansicht („☰ Menü ▸ Erweiterte Einstellungen“); ohne Register-Band als Fenster."""
        if hasattr(self.band, "reiter") and hasattr(self.band, "stapel"):
            self.backstage_oeffnen("optionen", seite)
            return
        from lunivo_writer.ui.dialogs.optionen import OptionenDialog
        d = OptionenDialog(self, seite)
        d.exec()
        self.ki.geaendert.emit()


    def toggle_fullscreen(self, on: bool):
        self.showFullScreen() if on else self.showNormal()


    def about(self):
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.ueber(self, __version__).exec()
