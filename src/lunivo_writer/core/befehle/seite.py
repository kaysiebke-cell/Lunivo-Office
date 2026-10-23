"""Befehle: Seite, Abschnitte, Spalten."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from lunivo_writer.models.page import HeaderFooter
from PySide6.QtWidgets import QInputDialog, QMenu
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.core.farben import Farbe


class SeiteBefehle:
    """Befehle des Bandes: Seite, Abschnitte, Spalten. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""



    # ---- Seitenlayout --------------------------------------------------------------------------------------------------
    def seitenraenderRahmen(self, k=None, *_):
        self.w.page_setup()


    # ==== Seitenlayout =========================================================================================
    RAND = {"normal": (25, 25, 32, 32), "schmal": (13, 13, 13, 13), "moderat": (25, 25, 19, 19), "breit": (25, 25, 51, 51)}

    PAPIER = {"a4": (210, 297), "a3": (297, 420), "a5": (148, 210), "b5": (176, 250), "letter": (216, 279),
              "legal": (216, 356), "dinlang": (220, 110), "c5": (229, 162), "c6": (162, 114)}


    def w_setzeRandVorgabe(self, k, art):
        o, u, l, r = self.RAND[art]
        self.w.set_margins(o, u, l, r)


    def w_randVorgabeJetzt(self):
        t = self.w.current_tab()
        if not t:
            return ""
        p = t.editor.abschnitt_seite()
        ist = tuple(round(x) for x in (p.margin_top_mm, p.margin_bottom_mm, p.margin_left_mm, p.margin_right_mm))
        for art, v in self.RAND.items():
            if ist == v:
                return art
        return ""


    def seitenraender(self, k=None, *_): self.w.page_setup()


    # ---- Spalten (Seitenansicht, Druck, PDF; die Bearbeitungsansicht bleibt einspaltig) ----------------------------------------------
    def spaltenSetzen(self, k=None, n=1):
        self.w._page_change(lambda p: setattr(p, "spalten", int(n)))
        self.w.statusBar().showMessage("Eine Spalte." if int(n) == 1 else f"{int(n)} Spalten.", 4000)


    def w_spaltenJetzt(self):
        t = self.w.current_tab()
        return t.editor.abschnitt_seite().spalten if t else 1


    def spalten(self, k=None):
        self.w.page_setup()


    def spaltenumbruch(self, k=None):
        """Der Text danach beginnt in der nächsten Spalte (bei einer Spalte: auf der nächsten Seite)."""
        if self.ed:
            self.ed.insert_column_break()

    seitenraenderRahmen = seitenraender


    def w_setzePapier(self, k, art):
        b, h = self.PAPIER[art]
        self.w._page_change(lambda p: (setattr(p, "width_mm", min(b, h) if not p.landscape else max(b, h)),
                                       setattr(p, "height_mm", max(b, h) if not p.landscape else min(b, h))))


    def w_papierJetzt(self):
        t = self.w.current_tab()
        if not t:
            return ""
        a, b = sorted((round(t.editor.abschnitt_seite().width_mm), round(t.editor.abschnitt_seite().height_mm)))
        for art, (x, y) in self.PAPIER.items():
            if (a, b) == tuple(sorted((x, y))):
                return art
        return ""


    def w_querJetzt(self):
        t = self.w.current_tab()
        return bool(t) and t.editor.abschnitt_seite().landscape


    def w_setzeQuer(self, k=None, quer=True):
        """Hochformat (False) oder Querformat (True) für den Abschnitt am Zeiger."""
        if self.w.current_tab():
            self.w.set_orientation(bool(quer))


    def querformat(self, k=None):
        t = self.w.current_tab()
        if t:
            self.w.set_orientation(not t.editor.abschnitt_seite().landscape)


    def w_setzeThema(self, k, wahl):
        self.w.set_theme(wahl)


    def w_themaJetzt(self):
        return self.w.settings.get("theme", "system")


    # ---- Seitenhintergrund -------------------------------------------------------------------
    def _seite_aendern(self, **felder):
        e = self.ed
        if not e:
            return
        pg = e.abschnitt_seite()
        for k, v in felder.items():
            setattr(pg, k, v)
        e.page_settings_changed(pg)


    def menue_seitenfarbe(self):
        from PySide6.QtGui import QColor
        m = self._farbmenue(lambda c: self._seite_aendern(color=c.name() if c else ""), "Keine Farbe")
        return m


    def seitenfarbe(self, k=None):
        m = self.menue_seitenfarbe()
        self._popup(m)


    def wasserzeichen(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.ui.dialogs.dokument_dialoge import WasserzeichenDialog
        d = WasserzeichenDialog(self.w, self.ed.page.watermark)
        if d.exec():
            self._seite_aendern(watermark=d.ergebnis())


    def seitenrahmen(self, k=None):
        if not self.ed:
            return
        self.absatzRahmen(seite="seitenrand")                       # dasselbe Fenster, Reiter Seitenrand


    def netzlinien(self, k=None):
        if self.ed:
            self.ed.set_gitter(not self.ed.gitter)


    def an_netzlinien(self): return bool(self.ed and self.ed.gitter)


    # ---- Seitenlayout: Absatz, Zeilennummern, Textrichtung, Designs ---------------------------------------
    ABSATZABSTAND = [("Standard (0 / 0 pt)", 0, 0), ("Kompakt (0 / 4 pt)", 0, 4), ("Locker (0 / 10 pt)", 0, 10),
                     ("Luftig (6 / 12 pt)", 6, 12), ("Vor und nach 12 pt", 12, 12)]


    def absatzabstand(self, k=None):
        if not self.ed:
            return
        m = QMenu()
        for text, vor, nach in self.ABSATZABSTAND:
            m.addAction(text, lambda _=False, v=vor, n=nach: self._abstand_setzen(v, n))
        self._popup(m)


    def _abstand_setzen(self, vor, nach):
        e = self.ed
        if not e.textCursor().hasSelection():
            c = e.textCursor(); c.select(QTextCursor.Document); e.setTextCursor(c)       # ohne Markierung: ganzes Dokument
            e.set_paragraph_spacing(vor, nach)
            c.clearSelection(); e.setTextCursor(c)
        else:
            e.set_paragraph_spacing(vor, nach)


    def zeilennummern(self, k=None):
        if self.ed:
            self.ed.set_zeilennummern(not self.ed.page.zeilennummern)
            self.ed.document().setModified(True)


    def an_zeilennummern(self): return bool(self.ed and self.ed.page.zeilennummern)


    def silbentrennung(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor.pagination import _trenner
        pg = self.ed.page
        sprache = self.w.settings.get("silben/sprache", "de_DE")
        if _trenner(sprache) is None:
            self.w.statusBar().showMessage("Silbentrennung braucht das Paket „pyphen“ (pip install pyphen).", 6000)
            return
        pg.silbentrennung = not pg.silbentrennung
        pg.silben_sprache = sprache
        self.ed.page_settings_changed(pg)
        self.w.statusBar().showMessage(
            "Silbentrennung an — in Seitenansicht, Druck und PDF; die Bearbeitungsansicht zeigt keine Trennstriche."
            if pg.silbentrennung else "Silbentrennung aus.", 6000)


    def an_silbentrennung(self): return bool(self.ed and self.ed.page.silbentrennung)


    def textrichtung(self, k=None):
        if self.ed:
            self.ed.toggle_rtl()


    def textrichtungLinks(self, k=None):
        if self.ed and self.an_textrichtung():
            self.ed.toggle_rtl()


    def textrichtungRechts(self, k=None):
        if self.ed and not self.an_textrichtung():
            self.ed.toggle_rtl()


    def zeilenumbruch(self, k=None):
        """Zeilenumbruch ohne neuen Absatz (Umschalt+Enter)."""
        if self.ed:
            c = self.ed.textCursor()
            c.insertText("\u2028")
            self.ed.setTextCursor(c)


    def an_textrichtung(self):
        return bool(self.ed and self.ed.textCursor().blockFormat().layoutDirection() == Qt.RightToLeft)


    DESIGNS = {"Office": ("Liberation Sans", "Liberation Sans", "#1f3864"),
               "Klassisch": ("Liberation Serif", "Liberation Serif", Farbe.SCHWARZ),
               "Modern": ("DejaVu Sans", "DejaVu Sans", Farbe.AKZENT),
               "Zeitung": ("Liberation Serif", "Liberation Sans", "#222222"),
               "Dezent": ("Liberation Sans", "Liberation Sans", "#555555")}

    FARBSCHEMEN = {"Blau": Farbe.AKZENT, "Grün": "#2f9e75", "Rot": Farbe.ROT, "Violett": "#7048a8", "Orange": Farbe.ORANGE, "Grau": "#495057"}

    SCHRIFTPAARE = {"Sans / Sans": ("Liberation Sans", "Liberation Sans"), "Serif / Serif": ("Liberation Serif", "Liberation Serif"),
                    "Serif / Sans (Überschrift)": ("Liberation Serif", "Liberation Sans"),
                    "Sans / Serif (Überschrift)": ("Liberation Sans", "Liberation Serif"), "Mono": ("DejaVu Sans Mono", "DejaVu Sans Mono")}


    def _wahl(self, titel, namen):
        n, ok = QInputDialog.getItem(self.w, titel, titel + ":", list(namen), 0, False)
        return n if ok else None


    def designs(self, k=None):
        if self.ed and (n := self._wahl("Design", self.DESIGNS)):
            f, h, c = self.DESIGNS[n]
            self.ed.apply_design(f, h, c)


    def farbschema(self, k=None):
        if self.ed and (n := self._wahl("Farben", self.FARBSCHEMEN)):
            self.ed.apply_design(None, None, self.FARBSCHEMEN[n])


    def designEffekte(self, k=None):
        """Effekte des Designs: die Texteffekte (Schatten, Leuchten, Spiegelung …) für den markierten Text."""
        self.texteffekte(k)


    def designSchriften(self, k=None):
        if self.ed and (n := self._wahl("Schriftarten", self.SCHRIFTPAARE)):
            f, h = self.SCHRIFTPAARE[n]
            self.ed.apply_design(f, h, None)


    # ---- Abschnitte ------------------------------------------------------------------------------------------------------
    ABSCHNITT_ART = {"NextPage": "naechste", "Continuous": "fortlaufend", "EvenPage": "gerade", "OddPage": "ungerade"}


    def abschnittsumbruch(self, k=None, art="NextPage"):
        if not self.ed:
            return
        nr = self.ed.abschnitt_einfuegen(self.ABSCHNITT_ART.get(art, "naechste"))
        self.w.statusBar().showMessage(f"Abschnitt {nr + 1} beginnt hier (Einrichtung wie der vorige; Orientierung, Größe, Ränder gelten für den Abschnitt der Schreibmarke).", 7000)


    def abschnittLoeschen(self, k=None):
        if self.ed:
            ok = self.ed.abschnitt_entfernen()
            self.w.statusBar().showMessage("Abschnittsumbruch entfernt — die beiden Abschnitte sind einer (mit der Einrichtung des früheren)."
                                           if ok else "Das Dokument hat nur einen Abschnitt.", 6000)


    def abschnittVorher(self, k=None):
        if self.ed:
            self.ed.abschnitt_gehe(self.ed.abschnitt_nr() - 1)


    def abschnittNaechster(self, k=None):
        if self.ed:
            self.ed.abschnitt_gehe(self.ed.abschnitt_nr() + 1)


    def abschnittNavigation(self, k=None):
        self.geheZu(k, "Abschnitt")


    def abschnittEinstellungen(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        from lunivo_writer.editor import abschnitte as AB
        from lunivo_writer.ui.dialogs.dokument_dialoge import PageSetupDialog
        e = t.editor
        nr = e.abschnitt_nr()
        d = PageSetupDialog(e.abschnitt_seite(), self.w)
        d.setWindowTitle(f"Abschnitt {nr + 1} einrichten")
        if d.exec():
            e.page_settings_changed(d.result_page())
        if nr > 0:
            namen = list(AB.TYPEN.values())
            ab = AB.umbrueche(e.document())[nr - 1]
            gewaehlt, ok = QInputDialog.getItem(self.w, f"Abschnitt {nr + 1}", "Der Abschnitt beginnt:", namen,
                                                list(AB.TYPEN).index(ab[1]), False)
            if ok:
                typ = list(AB.TYPEN)[namen.index(gewaehlt)]
                AB.setzen(e.document(), nr, AB.einrichtung(e.document(), e.page, nr), typ)
                e.document().setModified(True)
                e._recount()


    def _kopf_link(self, was: str, an: bool | None = None):
        t = self.w.current_tab()
        if not t or t.editor.abschnitt_nr() == 0:
            return None
        pg = t.editor.abschnitt_seite()
        feld = "kopf_verknuepft" if was == "kopf" else "fuss_verknuepft"
        if an is None:
            return getattr(pg, feld)
        setattr(pg, feld, an)
        t.editor.page_settings_changed(pg)
        return an


    def kopfVerknuepfen(self, k=None):
        if self._kopf_link("kopf") is None:
            self.w.statusBar().showMessage("Der erste Abschnitt hat keinen Vorgänger.", 4000)
        else:
            self._kopf_link("kopf", not self._kopf_link("kopf"))


    def fussVerknuepfen(self, k=None):
        if self._kopf_link("fuss") is None:
            self.w.statusBar().showMessage("Der erste Abschnitt hat keinen Vorgänger.", 4000)
        else:
            self._kopf_link("fuss", not self._kopf_link("fuss"))


    def an_kopfVerknuepfen(self): return bool(self._kopf_link("kopf"))

    def an_fussVerknuepfen(self): return bool(self._kopf_link("fuss"))


    def schriftartMehr(self, k=None):
        if not self.ed:
            return
        """Fenster „Schriftart“ (Baukasten): Schrift, Schnitt, Größe, Farbe, Unterstreichung, Effekte, Zeichenabstand."""
        from lunivo_writer.ui.baukasten.schriftart_dialog import SchriftartDialog
        from lunivo_writer.ui.baukasten.text_format import aus_format, zu_format
        d0 = self.ed.document().defaultFont()
        w = aus_format(self._fmt(), d0.family(), d0.pointSizeF())
        w["versteckt"] = self.ed.ist_versteckt()
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        d = SchriftartDialog(self.w, w)
        if ausfuehren(d):
            neu = d.werte()
            if neu.pop("als_standard", False):                  # „Standard …“: Schrift und Größe für neue Dokumente merken
                if neu["schrift"]:
                    self.w.settings.set("standard/schrift", neu["schrift"])
                if neu["groesse"]:
                    self.w.settings.set("standard/groesse", neu["groesse"])
                self.w.statusBar().showMessage("Die Schrift gilt jetzt als Standard für neue Dokumente.", 5000)
            self.ed._merge(zu_format(neu))
            if "effekt" in neu:
                from lunivo_writer.editor import texteffekt
                self.ed._merge(texteffekt.zu_format(neu["effekt"]))
            if neu["versteckt"] != w["versteckt"]:
                self.ed.set_versteckt(neu["versteckt"])


    def papierformatFenster(self, k=None): self.w.page_setup()

    def fusszeileBearbeiten(self, k=None): self.w.edit_header_footer(False)


    def kopfFussSchliessen(self, k=None):
        self.w.statusBar().showMessage("Kopf- und Fußzeile werden über Dialoge bearbeitet — es gibt nichts zu schließen.", 4000)


    def ersteSeiteAnders(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        pg = t.editor.abschnitt_seite()
        pg.diff_first = not pg.diff_first
        if pg.diff_first and pg.first_header.is_empty() and pg.first_footer.is_empty():
            pg.first_header = HeaderFooter(); pg.first_footer = HeaderFooter()
        t.editor.page_settings_changed(pg)


    def an_ersteSeiteAnders(self):
        t = self.w.current_tab()
        return bool(t and t.editor.abschnitt_seite().diff_first)


    def tabelleEigenschaften(self, k=None):
        t = self.ed.textCursor().currentTable() if self.ed else None
        if t is None:
            return
        from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QSpinBox
        from PySide6.QtGui import QTextLength
        fm = t.format()
        d = QDialog(self.w); d.setWindowTitle("Tabelleneigenschaften")
        form = QFormLayout(d)
        breite = QSpinBox(); breite.setRange(10, 100); breite.setSuffix(" % der Textbreite"); breite.setValue(int(fm.width().rawValue()) if fm.width().type() == QTextLength.PercentageLength else 100)
        ausr = QComboBox(); ausr.addItems(["Links", "Zentriert", "Rechts"])
        ausr.setCurrentIndex(1 if fm.alignment() & Qt.AlignHCenter else 2 if fm.alignment() & Qt.AlignRight else 0)
        rand = QDoubleSpinBox(); rand.setRange(0, 10); rand.setSingleStep(0.25); rand.setValue(fm.border()); rand.setSuffix(" pt")
        pad = QDoubleSpinBox(); pad.setRange(0, 30); pad.setValue(fm.cellPadding()); pad.setSuffix(" px")
        kopf = QCheckBox("Erste Zeile ist Kopfzeile (wiederholt sich auf jeder Seite)"); kopf.setChecked(fm.headerRowCount() > 0)
        for lab, w in (("Breite", breite), ("Ausrichtung", ausr), ("Rahmenstärke", rand), ("Zellenabstand innen", pad)):
            form.addRow(lab, w)
        form.addRow(kopf)
        bb = knopfzeile(d)
        form.addRow(bb)
        if d.exec():
            fm.setWidth(QTextLength(QTextLength.PercentageLength, breite.value()))
            fm.setAlignment([Qt.AlignLeft, Qt.AlignHCenter, Qt.AlignRight][ausr.currentIndex()])
            fm.setBorder(rand.value()); fm.setCellPadding(pad.value()); fm.setHeaderRowCount(1 if kopf.isChecked() else 0)
            t.setFormat(fm)
            self.ed.document().setModified(True)


    def tabelleSortieren(self, k=None):
        c = self.ed.textCursor() if self.ed else None
        t = c.currentTable() if c else None
        if t is None:
            return
        cell = t.cellAt(c)
        namen = [f"Spalte {i + 1}" for i in range(t.columns())]
        n, ok = QInputDialog.getItem(self.w, "Tabelle sortieren", "Nach welcher Spalte?", namen, cell.column(), False)
        if not ok:
            return
        auf, ok = QInputDialog.getItem(self.w, "Tabelle sortieren", "Reihenfolge:", ["Aufsteigend", "Absteigend"], 0, False)
        if not ok:
            return
        spalte = namen.index(n)
        start = t.format().headerRowCount()
        zeilen = []
        for r in range(start, t.rows()):
            zeilen.append([t.cellAt(r, k_).firstCursorPosition().block().text() for k_ in range(t.columns())])

        def schluessel(z):
            v = z[spalte].strip().replace(",", ".")
            try:
                return (0, float(v), "")
            except ValueError:
                return (1, 0.0, v.casefold())
        zeilen.sort(key=schluessel, reverse=(auf == "Absteigend"))
        c.beginEditBlock()
        for i, z in enumerate(zeilen):
            for k_, text in enumerate(z):
                cc = t.cellAt(start + i, k_).firstCursorPosition()
                fmt = cc.charFormat()
                cc.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cc.insertText(text, fmt)
        c.endEditBlock()
        self.ed.document().setModified(True)
