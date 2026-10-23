"""Datei-Ansicht (Backstage)."""
from __future__ import annotations

import os
from datetime import datetime
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from lunivo_writer.models.page import HeaderFooter
from lunivo_writer.ui.dialogs.dokument_dialoge import HeaderFooterDialog, TableDialog
from lunivo_writer.ui.ribbon.menue_tafel import MenueTafel


from lunivo_writer.core.farben import Farbe
class BackstageBaustein:
    """Datei-Ansicht (Backstage). Baustein von ``MainWindow`` (siehe ``lunivo_writer/ui/main_window.py``)."""


    def _backstage_verbinden(self):
        r = getattr(self.band, "reiter", None)
        if r is None:
            return
        self.backstage.hide()
        self.arbeit.show()
        r.currentChanged.connect(self._reiter_gewechselt)
        r.tabBarClicked.connect(self._reiter_angeklickt)
        # Die Datei-Ansicht heißt „☰ Menü“ und steht ganz links vor dem Schnellzugriff; der Reiter „Datei“ bleibt dafür verborgen
        for i in range(r.count()):
            if r.tabText(i) == "Datei":
                r.setTabVisible(i, False)
        k = self.band.menue_knopf
        try:
            k.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        k.setText("☰ Menü"); k.setCheckable(True); k.setToolTip("Menü: Neu, Öffnen, Speichern, Drucken, Info, Einstellungen, Hilfe")
        k.setStyleSheet(('QToolButton { font-weight: 600; padding: 4px 12px; } QToolButton:checked { color: ' + Farbe.AKZENT_DUNKEL + '; }'))
        k.clicked.connect(self._menue_geklickt)
        r.currentChanged.connect(lambda i, kk=k: kk.setChecked(self._ist_datei(i)))


    def _menue_geklickt(self):
        """☰ Menü: öffnet die Datei-Ansicht, ein zweiter Klick schließt sie wieder."""
        r = self.band.reiter
        if self.backstage.isVisible():
            self.backstage_schliessen()
            return
        i = next((n for n in range(r.count()) if r.tabText(n) == "Datei"), None)
        if i is not None:
            r.setCurrentIndex(i)
        self.band.menue_knopf.setChecked(self.backstage.isVisible())


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


    def backstage_oeffnen(self, seite: str = "zuletzt", unter: str | None = None):
        import time
        self._bs_zeit = time.monotonic()
        for name in ("stapel", "linie"):                              # die Oberfläche „Symbolleisten“ hat nur eine Leiste, kein Band mit Reitern
            if hasattr(self.band, name):
                getattr(self.band, name).hide()
        self.arbeit.hide()
        self.backstage.oeffnen(seite, unter)
        self.backstage.show()
        if hasattr(self.band, "menue_knopf"):
            self.band.menue_knopf.setChecked(True)


    def backstage_zu(self):
        if not self.backstage.isVisible():
            return
        self.backstage.hide()
        self.arbeit.show()
        if hasattr(self.band, "stapel") and not self.band._eingeklappt:
            self.band.stapel.show()
        if hasattr(self.band, "linie"):
            self.band.linie.show()
        if hasattr(self.band, "menue_knopf"):
            self.band.menue_knopf.setChecked(False)
        self.ki.geaendert.emit()                                   # Einstellungen der Optionen übernehmen (KI, Anbieter …)


    def backstage_schliessen(self):
        r = self.band.reiter
        if self._ist_datei(r.currentIndex()):
            r.setCurrentIndex(self._letzter_reiter if not self._ist_datei(self._letzter_reiter) else 1)
        self.backstage_zu()


    def show_main_menu(self):
        daten = next(m for m in self.band.daten["menues"] if m["name"] == "Datei")
        self._tafel = MenueTafel(daten["punkte"], self.befehle, self)
        self._tafel.zeigen_unter(self.band.menue_knopf)


    def _leiste_links(self):
        """Schmale Leiste links: Suchen, Kommentare, Überschriften, Änderungen, Noten, Vorlesen. Ein Klick öffnet das Feld, ein zweiter schließt es."""
        from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout
        from lunivo_writer.ui.document.navigation import SEITEN, TITEL
        from lunivo_writer.ui.widgets import icons
        leiste = QFrame()
        leiste.setObjectName("leisteLinks")
        leiste.setFixedWidth(48)
        v = QVBoxLayout(leiste)
        v.setContentsMargins(4, 8, 4, 8)
        v.setSpacing(6)
        self._links = {}
        symbole = {"suche": "lupe", "kommentare": "notiz", "ueberschriften": "gliederung", "aenderungen": "verfolgt", "noten": "fussnote", "vorlesen": "vorlesen"}
        for key in SEITEN:
            b = QToolButton()
            icons.setze(b, symbole[key], 22); b.setIconSize(QSize(22, 22))
            b.setToolTip(TITEL[key]); b.setAccessibleName(TITEL[key])
            b.setCheckable(True)
            b.setFixedSize(38, 38)
            b.clicked.connect(lambda _=False, k=key: self._links_klick(k))
            v.addWidget(b)
            self._links[key] = b
        v.addStretch(1)
        self.navigation.zustandGeaendert.connect(self._links_sync)
        self._links_sync()
        return leiste


    def _links_klick(self, key: str):
        if self.navigation.isVisible() and self.navigation.aktuelle_seite == key:
            self.navigation.hide()
        else:
            self.navigation.show()
            if key == "suche":
                self.navigation.suche_zeigen()
            else:
                self.navigation.zeige_tab(key)
        self._links_sync()


    def _links_sync(self):
        sicht = self.navigation.isVisible()
        for key, b in self._links.items():
            b.setChecked(sicht and self.navigation.aktuelle_seite == key)


    def _leiste_rechts(self):
        """Schmale Leiste rechts: Die vier Reiter der Schreibhilfe (Prüfen, Lesen, Schreiben, KI) und der KI-Chat schalten die Seitenleiste um."""
        from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout
        from lunivo_writer.ui.widgets import icons
        leiste = QFrame()
        leiste.setObjectName("leisteRechts")
        leiste.setFixedWidth(48)
        v = QVBoxLayout(leiste)
        v.setContentsMargins(4, 8, 4, 8)
        v.setSpacing(6)
        self._rechts = {}
        for name, sym, tip in (("Prüfen", "haken", "Prüfen — die Funde der Schreibhilfe"), ("Lesen", "brille", "Lesen — Lesehilfe, Vorlesen"),
                               ("Schreiben", "stift", "Schreiben — Schalter, Textbausteine, Sprache"), ("KI", "assistent", "KI — Korrektur, Übersetzen, Aktionen"),
                               ("Chat", "chat", "KI-Chat")):
            b = QToolButton()
            icons.setze(b, sym, 22); b.setIconSize(QSize(22, 22))
            b.setToolTip(tip); b.setAccessibleName(name)
            b.setCheckable(True)
            b.setFixedSize(38, 38)
            b.clicked.connect(lambda _=False, n=name: self._rechts_klick(n))
            if name == "Chat":
                v.addSpacing(8)
            v.addWidget(b)
            self._rechts[name] = b
        v.addStretch(1)
        self.sidebar.bereich_geaendert.connect(lambda _i: self._rechts_sync())
        self._rechts_sync()
        return leiste


    def _rechts_klick(self, name: str):
        """Ein Knopf der Leiste: öffnet die Seitenleiste auf dem Reiter; ein zweiter Klick auf denselben Reiter schließt sie wieder."""
        ist_chat = name == "Chat"
        schon_da = (not self.sidebar.isHidden() and ((ist_chat and self.sidebar.stapel.currentIndex() == 1)
                    or (not ist_chat and self.sidebar.stapel.currentIndex() == 0 and self.sidebar.aktueller_reiter == name)))
        if schon_da:
            self.toggle_sidebar()
        else:
            if self.sidebar.isHidden():
                self.toggle_sidebar()
            self.sidebar.zeige_bereich(1) if ist_chat else self.sidebar.zeige_reiter(name)
        self._rechts_sync()


    def _rechts_sync(self):
        sicht = not self.sidebar.isHidden()
        i = self.sidebar.stapel.currentIndex()
        for name, b in self._rechts.items():
            an = sicht and ((name == "Chat" and i == 1) or (name != "Chat" and i == 0 and self.sidebar.aktueller_reiter == name))
            b.setChecked(an)


    def texteffekte_seitenleiste(self):
        """Den Bereich „Texteffekte formatieren“ in der Seitenleiste öffnen; Änderungen gelten sofort für die Markierung."""
        from lunivo_writer.editor import texteffekt
        if self.current_editor() is None:
            return
        if self.sidebar.isHidden():
            self.toggle_sidebar()

        def anwenden(w: dict):
            e = self.current_editor()
            if e is not None:
                e._merge(texteffekt.zu_format(w))
        self.sidebar.zeige_texteffekte(texteffekt.aus_format(self.befehle._fmt()), anwenden)


    def objektformat_seitenleiste(self, reiter: int = 0, fuellung: str | None = None) -> None:
        """Den Bereich „Formatierung“ für das markierte Bild in der Seitenleiste öffnen (Füllung und Linie, Effekte); Änderungen gelten sofort."""
        from PySide6.QtGui import QImage
        from PySide6.QtWidgets import QFileDialog
        from lunivo_writer.editor import bildlayout as BL
        e = self.current_editor()
        z = BL.ziel(e) if e is not None else None
        w = BL.format_lesen(e, z) if z is not None else None
        if w is None:
            return
        if self.sidebar.isHidden():
            self.toggle_sidebar()

        def anwenden(neu: dict):
            ed = self.current_editor()
            if ed is not None:
                BL.format_aus_panel(ed, BL.ziel(ed), neu)

        def bild():
            ed = self.current_editor()
            pfad, _ = QFileDialog.getOpenFileName(self, "Bild als Füllung", "", "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
            if ed is not None and pfad:
                BL.fuellbild_setzen(ed, BL.ziel(ed), QImage(pfad))
        self.sidebar.zeige_objektformat(w, anwenden, reiter, bild)
        if fuellung:
            self.sidebar.objekt_panel.fuellung_waehlen(fuellung)


    def _zeichen_masse(self, e) -> None:
        """Höhe und Breite im Reiter Zeichentools mit dem markierten Bild abgleichen."""
        f = self.band.felder
        if e is None or "bild_breite" not in f or getattr(e, "_frei_sel", None) is None:
            return
        from lunivo_writer.editor import bildlayout as BL
        m = BL.masse_lesen(e, BL.ziel(e))
        if m is None:
            return
        for schl, wert in (("bild_breite", m[0]), ("bild_hoehe", m[1])):
            sp = f[schl]
            if not sp.hasFocus() and abs(sp.value() - wert) > 0.05:
                sp.blockSignals(True); sp.setValue(wert); sp.blockSignals(False)
        f["bild_verhaeltnis"][0] = m[0] / max(0.1, m[1])


    def objektformat_folgen(self) -> None:
        """Wählt der Benutzer ein anderes Bild, zeigt der offene Bereich dessen Werte."""
        e = self.current_editor()
        if self.sidebar.objektformat_sichtbar() and e is not None:
            from lunivo_writer.editor import bildlayout as BL
            w = BL.format_lesen(e, BL.ziel(e))
            if w is not None:
                self.sidebar.aktualisiere_objektformat(w)


    def _effekt_sync(self):
        """Folgt die Markierung einer anderen Formatierung, zeigt der offene Bereich „Texteffekte“ deren Werte."""
        if self.sidebar.texteffekte_sichtbar() and self.current_editor() is not None:
            from lunivo_writer.editor import texteffekt
            self.sidebar.aktualisiere_texteffekte(texteffekt.aus_format(self.befehle._fmt()))


    def toggle_sidebar(self):
        on = self.sidebar.isHidden()
        self.sidebar.setVisible(on)
        self.settings.set("ui/seitenleiste", on)
        if hasattr(self, "_rechts"):
            self._rechts_sync()
        self._chat_knopf_pruefen()


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
        self.marken_setzen(on, on)


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
        """Strg+F / Strg+H: „Suchen und ersetzen“ als Feld in der linken Seitenleiste."""
        if self.current_editor():
            self.navigation.suche_zeigen()
