"""Bearbeiten, Einfügen, Seite."""
from __future__ import annotations

from lunivo_writer.editor.zusatz import abstand_davor_px
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
from lunivo_writer.models.page import px_to_mm
from lunivo_writer.ui.baukasten import weitere_farben
from lunivo_writer.ui.dialogs.dokument_dialoge import PageSetupDialog
from lunivo_writer.core.farben import Farbe
from lunivo_writer.ui.hauptfenster.gemeinsam import _QuickInfo


class BearbeitenBaustein:
    """Bearbeiten, Einfügen, Seite. Baustein von ``MainWindow`` (siehe ``lunivo_writer/ui/main_window.py``)."""


    # ==== Bearbeiten/Einfügen ===================================================================
    def paste_plain(self):
        e = self.current_editor()
        if e:
            t = QApplication.clipboard().text()
            if t:
                e.textCursor().insertText(t)


    def choose_color(self):
        c = weitere_farben(self, Qt.black, "Schriftfarbe")
        if c is not None:
            self._ed(lambda e: e.set_text_color(c))


    def choose_highlight(self):
        c = weitere_farben(self, QColor("yellow"), "Texthervorhebungsfarbe")
        if c is not None:
            self._ed(lambda e: e.set_highlight(c))


    def paragraph_dialog(self):
        e = self.current_editor()
        if not e:
            return
        from lunivo_writer.editor import absatzopt, seitenfluss
        from lunivo_writer.ui.baukasten.absatz_dialog import AbsatzDialog
        from lunivo_writer.ui.baukasten.tabstopp_dialog import aus_block
        bf = e.textCursor().blockFormat()
        lh = bf.lineHeight() / 100 if bf.lineHeightType() == 1 and bf.lineHeight() else 1.0
        lart = {2: "genau", 3: "mindestens"}.get(int(bf.lineHeightType()), "faktor")
        lpt = round(bf.lineHeight() * 0.75, 1) if lart != "faktor" else 12.0
        al = bf.alignment()
        rtl = bf.layoutDirection() == Qt.RightToLeft
        d = AbsatzDialog(self, {
            "ausr": "mitte" if al & Qt.AlignHCenter else "rechts" if al & Qt.AlignRight else "block" if al & Qt.AlignJustify else "links",
            "rtl": rtl, "einzug": px_to_mm(bf.leftMargin()), "rechts": px_to_mm(bf.rightMargin()),
            "erste": px_to_mm(bf.textIndent()), "vor": abstand_davor_px(bf) * 0.75, "nach": bf.bottomMargin() * 0.75, "zeilen": lh,
            "zeilen_art": lart, "zeilen_pt": lpt, "ebene": bf.headingLevel(), "opt": absatzopt.lesen(bf),
            "umbruch": seitenfluss.ist_manuell(bf), "tabs": aus_block(bf)})
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        if ausfuehren(d):
            w = d.werte()
            if w["ebene"] != bf.headingLevel():                       # die Gliederungsebene ist die Überschriftsebene des Absatzes
                e.apply_style("Standard" if not w["ebene"] else f"Überschrift {w['ebene']}")
            e.set_alignment({"mitte": Qt.AlignHCenter, "rechts": Qt.AlignRight, "block": Qt.AlignJustify}.get(w["ausr"], Qt.AlignLeft))
            e.set_page_break_before(w["umbruch"])
            e.set_absatzopt(w["opt"])
            e.set_indents(w["einzug"], w["rechts"], w["erste"])
            e.set_paragraph_spacing(w["vor"], w["nach"])
            e.set_line_height(w["zeilen_art"], w["zeilen"] if w["zeilen_art"] == "faktor" else w["zeilen_pt"])
            e.set_tabstopps(w["tabs"])
            if w["rtl"] != rtl:
                e.toggle_rtl()


    def tabstopp_dialog(self):
        e = self.current_editor()
        if not e:
            return
        from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog, aus_block
        d = TabstoppDialog(self, aus_block(e.textCursor().blockFormat()))
        if d.exec():
            e.set_tabstopps(d.stopps())


    def _lesehilfe_auf(self, e):
        from lunivo_writer.ui.dialogs.lesehilfe_dialog import PAPIERTOENE
        s = self.settings
        e.set_lesehilfe(PAPIERTOENE.get(s.get("lesehilfe/papier", "Weiß"), Farbe.WEISS),
                        float(s.get("lesehilfe/buchstaben", 0)), float(s.get("lesehilfe/wort", 0)))
        e.set_zeilenluft(float(s.get("lesehilfe/zeilenluft", 1.0)))
        e.set_zeilenfokus(s.get_bool("lesehilfe/zeilenfokus", False))
        e.set_lesefokus({"etwas": 1.05, "deutlich": 1.10}.get(str(s.get("lesehilfe/groesser", "keine")), 1.0),
                        {"etwas": 0.62, "deutlich": 0.38}.get(str(s.get("lesehilfe/zurueck", "keine")), 1.0))
        e.setAcceptDrops(s.get_bool("bearbeiten/ziehen", True))          # Text mit der Maus verschieben
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
        if e is None:
            self.lesehilfe_geaendert.emit()


    def lineale_anwenden(self, tab=None):
        h = self.settings.get_bool("ansicht/lineal", False)
        v = self.settings.get_bool("ansicht/lineal_hoch", False)
        for t in ([tab] if tab is not None else self._doc_tabs()):
            t.zeige_lineale(h, v)
        self.band.aktualisieren(self.current_tab() is not None)


    def formatzeichen_anwenden(self, e=None):
        """Formatierungszeichen für Reiter: Absatzmarken und Leerzeichen/Tabstopps getrennt (Optionen ▸ Ansicht)."""
        from PySide6.QtGui import QTextOption
        alt = self.settings.get_bool("ui/steuerzeichen", False)            # früherer gemeinsamer Schalter
        absatz = self.settings.get_bool("ui/marken_absatz", alt)
        leer = self.settings.get_bool("ui/marken_leer", alt)
        self.marks_on = absatz or leer
        for ed in ([e] if e is not None else [t.editor for t in self._doc_tabs()]):
            opt = ed.document().defaultTextOption()
            fl = opt.flags()
            fl = fl | QTextOption.ShowLineAndParagraphSeparators if absatz else fl & ~QTextOption.ShowLineAndParagraphSeparators
            fl = fl | QTextOption.ShowTabsAndSpaces if leer else fl & ~QTextOption.ShowTabsAndSpaces
            opt.setFlags(fl)
            ed.document().setDefaultTextOption(opt)


    def marken_setzen(self, absatz: bool | None = None, leer: bool | None = None):
        """Absatzmarken und/oder Leerzeichen und Tabstopps ein- oder ausschalten (None = unverändert)."""
        alt = self.settings.get_bool("ui/steuerzeichen", False)
        a = self.settings.get_bool("ui/marken_absatz", alt) if absatz is None else absatz
        l = self.settings.get_bool("ui/marken_leer", alt) if leer is None else leer
        self.settings.set("ui/marken_absatz", a); self.settings.set("ui/marken_leer", l)
        self.settings.set("ui/steuerzeichen", a or l)
        self.formatzeichen_anwenden()
        if hasattr(self, "a_marks"):
            self.a_marks.blockSignals(True); self.a_marks.setChecked(a or l); self.a_marks.blockSignals(False)


    def ansicht_optionen_anwenden(self):
        """Statusleiste, QuickInfo, Bedienschrift, Symbolgröße — aus den Optionen."""
        self.statusBar().setVisible(self.settings.get_bool("ui/statusleiste", True))
        app = QApplication.instance()
        if getattr(self, "_quickinfo", None) is None:
            self._quickinfo = _QuickInfo()
        self._quickinfo.an = self.settings.get_bool("ui/quickinfo", True)
        app.removeEventFilter(self._quickinfo)
        if not self._quickinfo.an:                    # nur solange QuickInfo aus ist, sonst prüft er jedes Ereignis des Programms
            app.installEventFilter(self._quickinfo)
        fam = self.settings.get("ui/bedienschrift", "")
        gr = self.settings.get_int("ui/bedienschrift_groesse", 0)
        prozent = self.settings.get_int("ui/bedien_prozent", 100)
        if getattr(self, "_app_font0", None) is None:
            self._app_font0 = QFont(app.font())                       # die Schrift des Systems, Grundlage für die Prozente
        f = QFont(self._app_font0)
        if fam:
            f.setFamily(fam)
        if gr:
            f.setPointSize(gr)
        elif prozent != 100:
            f.setPointSizeF(max(6.0, self._app_font0.pointSizeF() * prozent / 100))
        if f != app.font():
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
        self.lesehilfe_geaendert.emit()


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
        if ok:
            self.lbl_msg.setText("Vorlesen …")
        else:
            QMessageBox.information(self, "Vorlesen", "Es gibt nichts zum Vorlesen. Schreiben Sie etwas oder markieren Sie eine Stelle.")


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
        if self.navigation.isVisible():
            self.navigation.hide()
        else:
            self.navigation.show()
            self.navigation.zeige_tab(self.navigation.zuletzt)


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
        from lunivo_writer.ui import theme
        self.settings.set("theme", wahl)
        theme.WEICH = self.settings.get_bool("ui/weich", False)
        apply_theme(QApplication.instance(), wahl)
        icons.leeren()
        self.neu_bauen_band()


    def _bereiche_bauen(self):
        self.sidebar.setze_bereiche()
        self.ki_schnell_zeigen()


    def _chat_knopf_pruefen(self) -> None:
        """Der schwebende KI-Chat-Knopf ist weg, solange der Chat in der Seitenleiste offen ist."""
        offen = self.sidebar.isVisible() and self.sidebar.stapel.currentIndex() == 1
        for t in self._doc_tabs():
            k = getattr(t, "_chat_knopf", None)
            if k is not None:
                k.setVisible(not offen)


    def ki_schnell_zeigen(self) -> None:
        """Die Schnellen KI-Aktionen mit Zugriff „Schnellzugriff“ in der Schnellzugriffsleiste zeigen."""
        if hasattr(self.band, "ki_schnell"):
            self.band.ki_schnell([a for a in self.ki.konfig["assistenten"] if a.get("zugriff") == "schnell"], self.ki.assistent)


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
