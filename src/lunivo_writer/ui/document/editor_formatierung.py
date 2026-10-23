"""Zeichen- und Absatzformat, Einfügen, Suchen."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat, QTextImageFormat, QTextListFormat, QTextTableFormat, QTextLength
from lunivo_writer.services.docx_reader import LH_PROPORTIONAL, STYLE_PROP
from lunivo_writer.editor.zusatz import P_VERSTECKT
from lunivo_writer.models.page import mm_to_px, px_to_mm
from lunivo_writer.editor import stile
from lunivo_writer.editor.zusatz import abstand_davor_px
from lunivo_writer.core.farben import Farbe


class FormatierungBaustein:
    """Zeichen- und Absatzformat, Einfügen, Suchen. Baustein von ``DocumentEditor`` (siehe ``lunivo_writer/ui/document/document_editor.py``)."""


    # ---- Zeichenformat -----------------------------------------------------
    def _merge(self, fmt: QTextCharFormat) -> None:
        cur = self.textCursor()
        cur.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)


    def toggle_bold(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontWeight(QFont.Bold if on else QFont.Normal); self._merge(f)


    def toggle_italic(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontItalic(on); self._merge(f)


    def toggle_underline(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontUnderline(on); self._merge(f)


    def set_underline_style(self, stil) -> None:
        f = QTextCharFormat()
        f.setUnderlineStyle(stil)
        self._merge(f)


    def set_outline(self, an: bool) -> None:
        f = QTextCharFormat()
        f.setTextOutline(QPen(QColor(Farbe.SCHWARZ)) if an else QPen(Qt.NoPen))
        self._merge(f)


    def set_letter_spacing(self, px: float) -> None:
        f = QTextCharFormat()
        f.setFontLetterSpacingType(QFont.AbsoluteSpacing)
        f.setFontLetterSpacing(px)
        self._merge(f)


    def set_capitalization(self, cap) -> None:
        f = QTextCharFormat()
        f.setFontCapitalization(cap)
        self._merge(f)


    def toggle_strike(self, on: bool) -> None:
        f = QTextCharFormat(); f.setFontStrikeOut(on); self._merge(f)


    def set_script(self, kind: str | None) -> None:
        f = QTextCharFormat()
        f.setVerticalAlignment({"sup": QTextCharFormat.AlignSuperScript,
                                "sub": QTextCharFormat.AlignSubScript}.get(kind, QTextCharFormat.AlignNormal))
        self._merge(f)


    def set_font_family(self, family: str) -> None:
        f = QTextCharFormat(); f.setFontFamilies([family]); self._merge(f)


    def set_font_size(self, pt: float) -> None:
        if pt > 0:
            f = QTextCharFormat(); f.setFontPointSize(pt); self._merge(f)


    def grow_font(self, delta: float) -> None:
        cur = self.textCursor()
        size = cur.charFormat().fontPointSize() or self.document().defaultFont().pointSizeF() or 11
        self.set_font_size(max(1.0, min(400.0, size + delta)))


    def set_text_color(self, color: QColor | None) -> None:
        f = QTextCharFormat()
        f.setForeground(QBrush(color) if color else QBrush(Qt.NoBrush))
        if color is None:
            f.clearProperty(QTextFormat.ForegroundBrush)
        self._merge(f)


    def set_highlight(self, color: QColor | None) -> None:
        f = QTextCharFormat()
        if color:
            f.setBackground(QBrush(color))
        else:
            f.setBackground(QBrush(Qt.NoBrush))
        self._merge(f)


    def change_case(self, mode: str) -> None:
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        txt = cur.selectedText()
        new = {"upper": txt.upper(), "lower": txt.lower(), "title": txt.title()}[mode]
        if new != txt:
            cur.insertText(new)


    def clear_formatting(self) -> None:
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        cur.beginEditBlock()
        cur.setCharFormat(QTextCharFormat())
        bf = QTextBlockFormat()
        cur.setBlockFormat(bf)
        cur.endEditBlock()


    # ---- Absatz ---------------------------------------------------------------
    def _block_merge(self, fn) -> None:
        cur = self.textCursor()
        cur.beginEditBlock()
        start, end = sorted((cur.anchor(), cur.position()))
        c = QTextCursor(self.document()); c.setPosition(start)
        blk = c.block()
        while blk.isValid() and blk.position() <= end:
            cc = QTextCursor(blk)
            bf = cc.blockFormat()
            fn(bf)
            cc.setBlockFormat(bf)
            blk = blk.next()
        cur.endEditBlock()


    def set_alignment(self, al: Qt.AlignmentFlag) -> None:
        def f(bf):
            bf.setAlignment(al)
            if (al & Qt.AlignHCenter) and self.opt("schreibhilfe/akZentriert", True):
                bf.setTextIndent(0)               # „Bei zentriertem Ausrichten Erstzeileneinzug löschen“
        self._block_merge(f)


    def change_indent(self, delta_mm: float) -> None:
        d = mm_to_px(delta_mm)
        self._block_merge(lambda bf: bf.setLeftMargin(max(0.0, bf.leftMargin() + d)))


    def set_page_break_before(self, an: bool) -> None:
        from lunivo_writer.editor.zusatz import B_AUTOUMBRUCH

        def f(bf):
            bf.clearProperty(B_AUTOUMBRUCH)                 # ein selbst gesetzter Umbruch ersetzt einen, den Lunivo eingefügt hatte
            bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore if an else QTextFormat.PageBreak_Auto)
        self._block_merge(f)


    def set_indents(self, left_mm: float, right_mm: float, first_mm: float) -> None:
        def f(bf):
            bf.setLeftMargin(mm_to_px(left_mm)); bf.setRightMargin(mm_to_px(right_mm))
            bf.setTextIndent(mm_to_px(first_mm))
        self._block_merge(f)


    def standard_tab_mm(self) -> float:
        """Standardtabstopps des Dokuments (Abstand in mm)."""
        return round(px_to_mm(self.document().defaultTextOption().tabStopDistance()), 2)


    def set_standard_tab_mm(self, mm: float) -> None:
        if mm <= 0:
            return
        opt = self.document().defaultTextOption()
        opt.setTabStopDistance(mm_to_px(mm))
        self.document().setDefaultTextOption(opt)
        self.document().setModified(True)
        self.viewport().update()


    def set_absatzopt(self, w: dict) -> None:
        """Absatzoptionen (Umbruchregeln, Zeilenumbruch, Zeichenabstand, Raster) der markierten Absätze setzen."""
        from lunivo_writer.editor import absatzopt
        self._block_merge(lambda bf: absatzopt.setzen(bf, w))


    def set_tabstopps(self, stopps) -> None:
        """Tabstopps als Liste aus (Millimeter, Ausrichtung, Füllzeichen) setzen."""
        from lunivo_writer.ui.baukasten.tabstopp_dialog import zu_block
        self._block_merge(lambda bf: zu_block(bf, stopps))
        self.viewport().update()


    def set_line_spacing(self, factor: float) -> None:
        self._block_merge(lambda bf: bf.setLineHeight(factor * 100, LH_PROPORTIONAL))


    def set_line_height(self, art: str, wert: float) -> None:
        """Zeilenabstand: ``faktor`` (Vielfaches), ``mindestens`` oder ``genau`` (Punkt)."""
        if art == "faktor":
            self.set_line_spacing(wert); return
        typ = {"genau": 2, "mindestens": 3}[art]                 # QTextBlockFormat.FixedHeight / MinimumHeight
        self._block_merge(lambda bf: bf.setLineHeight(wert / 0.75, typ))


    def set_paragraph_spacing(self, before_pt: float, after_pt: float) -> None:
        def f(bf):
            bf.setTopMargin(before_pt / 0.75); bf.setBottomMargin(after_pt / 0.75)
        self._block_merge(f)


    def toggle_list(self, kind: str, style=None) -> None:
        cur = self.textCursor()
        style = style if style is not None else (
            QTextListFormat.ListDisc if kind == "bullet" else QTextListFormat.ListDecimal)
        lst = cur.currentList()
        if lst and lst.format().style() == style:
            cur.beginEditBlock()
            blk = cur.block()
            lst.remove(blk)
            bf = cur.blockFormat(); bf.setIndent(0); bf.setLeftMargin(0); cur.setBlockFormat(bf)
            cur.endEditBlock()
            return
        fmt = QTextListFormat(); fmt.setStyle(style); fmt.setIndent(1)
        cur.createList(fmt)


    def list_remove(self, nur_qt: bool = False) -> None:
        """Aufzählung/Nummerierung vom Absatz an der Schreibmarke (bzw. der Auswahl) nehmen."""
        if not nur_qt:
            self.set_mehrstufig(None)
        cur = self.textCursor()
        cur.beginEditBlock()
        von, bis = sorted((cur.anchor(), cur.position()))
        c = QTextCursor(self.document()); c.setPosition(von)
        blk = c.block()
        while blk.isValid() and blk.position() <= bis:
            lst = blk.textList()
            if lst:
                lst.remove(blk)
                cc = QTextCursor(blk); bf = cc.blockFormat(); bf.setIndent(0); bf.setLeftMargin(0); cc.setBlockFormat(bf)
            blk = blk.next()
        cur.endEditBlock()


    def list_level(self, delta: int) -> None:
        m = self._mehrstufig_am_zeiger()
        if m:                                                    # mehrstufige Liste: die Ebene der markierten Absätze ändern
            from lunivo_writer.editor import mehrstufig
            from lunivo_writer.editor.zusatz import B_MEHRSTUFIG

            def f(bf):
                w = mehrstufig.aus_block(bf.stringProperty(B_MEHRSTUFIG)) if bf.hasProperty(B_MEHRSTUFIG) else None
                if w:
                    n = max(1, min(mehrstufig.EBENEN, w[0] + delta))
                    bf.setProperty(B_MEHRSTUFIG, mehrstufig.block_wert(n, w[1]))
            self._block_merge(f); mehrstufig.einrichten_alle(self.document()); self.viewport().update()
            return
        cur = self.textCursor()
        lst = cur.currentList()
        if not lst:
            return
        fmt = lst.format()
        fmt.setIndent(max(1, min(9, fmt.indent() + delta)))
        lst.setFormat(fmt)


    def apply_style(self, name: str) -> None:
        """Formatvorlage auf alle Absätze der Markierung (oder den Absatz am Zeiger) anwenden."""
        cur = self.textCursor()
        cur.beginEditBlock()
        von, bis = sorted((cur.anchor(), cur.position()))
        c = QTextCursor(self.document()); c.setPosition(von)
        blk = c.block()
        while blk.isValid() and blk.position() <= bis:
            self._stil_auf_block(blk, name)
            blk = blk.next()
        cur.endEditBlock()
        self.setFocus()


    def _stil_auf_block(self, blk, name: str) -> None:
        d = stile.definition(name)
        cc = QTextCursor(blk)
        bf = cc.blockFormat()
        level = d["ebene"]
        bf.setHeadingLevel(level)
        key = d.get("key")
        if key:
            bf.setProperty(STYLE_PROP, key)
        else:
            bf.clearProperty(STYLE_PROP)
        bf.setTopMargin(d["vor"] / 0.75); bf.setBottomMargin(d["nach"] / 0.75)
        if d.get("zeilen_art") in ("genau", "mindestens"):
            bf.setLineHeight(d.get("zeilen_pt", 12.0) / 0.75, 2 if d["zeilen_art"] == "genau" else 3)
        elif d.get("zeilen"):
            bf.setLineHeight(d["zeilen"] * 100, LH_PROPORTIONAL)
        if d.get("rechts"):
            bf.setRightMargin(mm_to_px(d["rechts"]))
        if d.get("erste"):
            bf.setTextIndent(mm_to_px(d["erste"]))
        if d.get("rtl"):
            bf.setLayoutDirection(Qt.RightToLeft)
        if d.get("umbruch"):
            bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
        if d.get("gliederung") and d.get("key"):                    # Gliederungsebene einer eigenen Vorlage: Überschriftsebene (Qt kennt 1 bis 6)
            bf.setHeadingLevel(min(6, int(d["gliederung"])))
        if d.get("opt"):
            from lunivo_writer.editor import absatzopt
            absatzopt.setzen(bf, absatzopt.aus_text(d["opt"]))
        if d.get("einzug"):
            bf.setLeftMargin(mm_to_px(d["einzug"]))
        if d["ausr"]:
            bf.setAlignment({"links": Qt.AlignLeft, "mitte": Qt.AlignHCenter, "rechts": Qt.AlignRight, "block": Qt.AlignJustify}[d["ausr"]])
        if d.get("rahmen"):
            from lunivo_writer.editor.zusatz import B_RAHMEN
            bf.setProperty(B_RAHMEN, d["rahmen"])
        if d.get("muster") or d.get("fuell"):
            from lunivo_writer.editor import muster as M
            from lunivo_writer.editor.zusatz import B_MUSTER
            fuell = d.get("fuell") or None
            if d.get("muster"):
                bf.setBackground(M.pinsel(d["muster"], d.get("musterfarbe") or Farbe.SCHWARZ, fuell))
                bf.setProperty(B_MUSTER, M.als_text(d["muster"], d.get("musterfarbe") or Farbe.SCHWARZ, fuell))
            else:
                bf.setBackground(QBrush(QColor(fuell)))
        cc.setBlockFormat(bf)
        if d.get("tabs"):
            from lunivo_writer.ui.baukasten.tabstopp_dialog import aus_text as tabs_aus, zu_block
            bf = QTextCursor(blk).blockFormat(); zu_block(bf, tabs_aus(d["tabs"]))
            QTextCursor(blk).setBlockFormat(bf)
        if d.get("liste"):
            self._liste_auf_block(blk, d["liste"])
        sel = QTextCursor(blk)
        sel.movePosition(QTextCursor.StartOfBlock)
        sel.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        f = self._zeichen_der_vorlage(d)
        sel.mergeCharFormat(f)
        if d.get("versteckt"):
            f2 = QTextCharFormat(); f2.setProperty(P_VERSTECKT, 1); sel.mergeCharFormat(f2)
        if d.get("effekt"):
            from lunivo_writer.editor import texteffekt
            e = texteffekt.aus_text(d["effekt"], d.get("farbe", ""))
            if e:
                sel.mergeCharFormat(texteffekt.zu_format(e))
        self._ebene_der_vorlage(blk, name)


    def _zeichen_der_vorlage(self, d: dict) -> QTextCharFormat:
        """Das Zeichenformat einer Vorlage (alle Felder des Fensters „Schriftart“). Was die Vorlage nicht setzt, bleibt in der Auswahl, wie es ist."""
        from lunivo_writer.editor.zusatz import P_BETONUNG, P_DOPPELT, P_FONT_ASIEN, P_FONT_KOMPLEX, P_RASTER
        from lunivo_writer.ui.baukasten.text_format import ZEICHEN, zu_format
        zw = {k: d.get(k, v) for k, v in ZEICHEN.items()}
        f = zu_format(zw)
        if not zw["groesse"]:
            f.setFontPointSize(self.document().defaultFont().pointSizeF() or 11)
        Q = QTextFormat
        for schluessel, props in ((("unter",), (Q.TextUnderlineStyle,)), (("unterfarbe",), (Q.TextUnderlineColor,)),
                                  (("durch", "doppelt"), (Q.FontStrikeOut,)), (("hoch", "tief"), (Q.TextVerticalAlignment,)),
                                  (("kapital", "gross"), (Q.FontCapitalization,)), (("abstand",), (Q.FontLetterSpacingType, Q.FontLetterSpacing)),
                                  (("kerning", "kern_ab"), (Q.FontKerning,)), (("skala",), (Q.FontStretch,)), (("position",), (Q.TextBaselineOffset,)),
                                  (("raster",), (P_RASTER,)), (("doppelt",), (P_DOPPELT,)), (("betonung",), (P_BETONUNG,)),
                                  (("schrift_asien",), (P_FONT_ASIEN,)), (("schrift_komplex",), (P_FONT_KOMPLEX,))):
            if all(zw[k] == ZEICHEN[k] for k in schluessel):
                for pr in props:
                    f.clearProperty(pr)
        if not (zw["schrift"] or zw["schrift_asien"] or zw["schrift_komplex"]):
            f.clearProperty(Q.FontFamilies)
        return f


    def _ebene_der_vorlage(self, blk, name: str) -> None:
        """„Verbinden mit Formatvorlage“ (Gliederung anpassen): ein Absatz mit dieser Vorlage gehört zur verbundenen Ebene der Gliederung."""
        from lunivo_writer.editor import mehrstufig
        from lunivo_writer.editor.zusatz import B_MEHRSTUFIG
        b = blk.previous()
        defn = None
        while b.isValid():                                       # die nächste Gliederung davor, sonst die erste im Dokument
            if b.blockFormat().hasProperty(B_MEHRSTUFIG):
                w = mehrstufig.aus_block(b.blockFormat().stringProperty(B_MEHRSTUFIG))
                defn = w[1] if w else None
                break
            b = b.previous()
        if defn is None:
            return
        for i, e in enumerate(defn["ebenen"]):
            if e.get("vorlage") == name:
                c = QTextCursor(blk); bf = c.blockFormat()
                bf.setProperty(B_MEHRSTUFIG, mehrstufig.block_wert(i + 1, defn)); c.setBlockFormat(bf)
                mehrstufig.einrichten_alle(self.document())
                return


    def stil_tasten(self) -> None:
        """Die Tastenkombinationen der Formatvorlagen (nur gültig, solange der Editor den Fokus hat)."""
        from PySide6.QtGui import QKeySequence, QShortcut
        for s in getattr(self, "_stil_kurz", []):
            s.setEnabled(False); s.deleteLater()
        self._stil_kurz = []
        for n in stile.namen():
            t = stile.definition(n).get("taste", "")
            if t:
                sc = QShortcut(QKeySequence(t), self); sc.setContext(Qt.WidgetShortcut)
                sc.activated.connect(lambda n=n: self.apply_style(n))
                self._stil_kurz.append(sc)


    def _liste_auf_block(self, blk, text: str) -> None:
        """Absatz einer Formatvorlage mit Liste: aufeinanderfolgende Absätze mit derselben Liste zählen gemeinsam."""
        from lunivo_writer.editor import listen
        spec = listen.aus_text(text)
        if spec is None:
            return
        if "ebenen" in spec:
            from lunivo_writer.editor.mehrstufig import block_wert
            from lunivo_writer.editor.zusatz import B_MEHRSTUFIG
            c = QTextCursor(blk); bf = c.blockFormat()
            bf.setProperty(B_MEHRSTUFIG, block_wert(1, spec))
            c.setBlockFormat(bf)
            from lunivo_writer.editor import mehrstufig
            mehrstufig.einrichten_alle(self.document())
            return
        fmt = listen.zu_format(spec)
        vor = blk.previous().textList() if blk.previous().isValid() else None
        if vor is not None and listen.aus_format(vor.format()) == {k: v for k, v in spec.items() if k != "zeichen"}:
            vor.add(blk)
            self._nummern_zeichen(vor, spec.get("zeichen"))
        else:
            self._nummern_zeichen(QTextCursor(blk).createList(fmt), spec.get("zeichen"))


    def liste_spec(self):
        """Die Liste des Absatzes an der Schreibmarke (siehe ``editor.listen``) oder None."""
        from lunivo_writer.editor import listen, mehrstufig
        m = self._mehrstufig_am_zeiger()
        if m:
            return m[1]
        l = self.textCursor().currentList()
        return listen.aus_format(l.format()) if l else None


    def _mehrstufig_am_zeiger(self):
        """(Ebene, Gliederung) des Absatzes an der Schreibmarke, wenn er zu einer mehrstufigen Liste gehört."""
        from lunivo_writer.editor import mehrstufig
        from lunivo_writer.editor.zusatz import B_MEHRSTUFIG
        bf = self.textCursor().blockFormat()
        return mehrstufig.aus_block(bf.stringProperty(B_MEHRSTUFIG)) if bf.hasProperty(B_MEHRSTUFIG) else None


    def set_mehrstufig(self, defn, ebene_nr: int | None = None) -> None:
        """Die markierten Absätze in eine mehrstufige Liste setzen (``defn=None``: herausnehmen). Der Text rückt ein, die Nummer steht davor."""
        from lunivo_writer.editor import mehrstufig
        from lunivo_writer.editor.zusatz import B_MEHRSTUFIG

        def f(bf):
            alt = mehrstufig.aus_block(bf.stringProperty(B_MEHRSTUFIG)) if bf.hasProperty(B_MEHRSTUFIG) else None
            if defn is None:
                if alt:
                    bf.clearProperty(B_MEHRSTUFIG); bf.setLeftMargin(0); bf.setTextIndent(0)
                return
            n = ebene_nr or (alt[0] if alt else 1)
            bf.setProperty(B_MEHRSTUFIG, mehrstufig.block_wert(n, defn))
        if defn is not None:
            self.list_remove(nur_qt=True)
        self._block_merge(f)
        mehrstufig.einrichten_alle(self.document())
        self.viewport().update()


    def set_liste(self, spec) -> None:
        """Liste setzen: ändert die Liste des Absatzes (alle ihre Absätze) oder legt für die Auswahl eine neue an; None nimmt sie weg."""
        from lunivo_writer.editor import listen
        if spec is None:
            self.list_remove(); return
        if "ebenen" in spec:
            self.set_mehrstufig(spec); return
        if spec.get("pos"):                              # eigene Position der Nummer: Lunivo zeichnet sie selbst (wie bei der Gliederung)
            from lunivo_writer.editor import mehrstufig
            self.set_mehrstufig(mehrstufig.als_mehrstufig(spec)); return
        self.set_mehrstufig(None)
        cur = self.textCursor()
        lst = cur.currentList()
        if lst:
            lst.setFormat(listen.zu_format(spec, lst.format().indent()))
        else:
            lst = cur.createList(listen.zu_format(spec))
        self._nummern_zeichen(lst, spec.get("zeichen"))


    @staticmethod
    def _nummern_zeichen(lst, zeichen) -> None:
        """Schrift der Nummern: Qt zeichnet sie mit dem Zeichenformat des Absatzes."""
        if not zeichen:
            return
        from lunivo_writer.ui.baukasten.text_format import zu_format
        for i in range(lst.count()):
            c = QTextCursor(lst.item(i))
            f = zu_format(zeichen)
            if not zeichen.get("farbe"):
                f.clearProperty(QTextFormat.ForegroundBrush)
            if not zeichen.get("groesse"):
                f.clearProperty(QTextFormat.FontPointSize)
            if not zeichen.get("schrift"):
                f.clearProperty(QTextFormat.FontFamilies)
            c.mergeBlockCharFormat(f)


    def stil_neu_anwenden(self, name: str) -> int:
        """Nach „Formatvorlagen verwalten“: alle Absätze dieser Vorlage im Dokument neu formatieren."""
        n = 0
        cur = QTextCursor(self.document())
        cur.beginEditBlock()
        blk = self.document().firstBlock()
        while blk.isValid():
            if self._stil_name(blk.blockFormat()) == name:
                self._stil_auf_block(blk, name); n += 1
            blk = blk.next()
        cur.endEditBlock()
        return n


    @staticmethod
    def _stil_name(bf) -> str:
        key = bf.property(STYLE_PROP) if bf.hasProperty(STYLE_PROP) else None
        if key and str(key).startswith(stile.PRAEFIX):                # eine eigene Vorlage geht vor der Überschriftsebene, die sie setzen kann
            return stile.key_zu_name(str(key)) or "Standard"
        lvl = bf.headingLevel()
        if lvl in (1, 2, 3):
            return f"Überschrift {lvl}"
        for pfad in ("Title", "Subtitle", "Quote", "No Spacing"):
            if key == pfad:
                return stile.key_zu_name(pfad)
        if key and str(key).startswith(stile.PRAEFIX):
            return stile.key_zu_name(str(key)) or "Standard"
        return "Standard"


    def stil_aus_auswahl(self) -> dict:
        """Definition für eine neue Formatvorlage nach dem Absatz, in dem die Schreibmarke steht."""
        from lunivo_writer.editor import texteffekt
        from lunivo_writer.editor.listen import als_text
        from lunivo_writer.ui.baukasten.tabstopp_dialog import als_text as tabs_text, aus_block
        c = self.textCursor()
        bf, cf = c.blockFormat(), c.charFormat()
        ausr = {Qt.AlignHCenter: "mitte", Qt.AlignRight: "rechts", Qt.AlignJustify: "block"}
        a = next((v for k, v in ausr.items() if bf.alignment() & k), "")
        fam = cf.fontFamilies()
        return {"groesse": round(cf.fontPointSize(), 1) if cf.fontPointSize() > 0 else 0, "fett": cf.fontWeight() >= 600,
                "kursiv": cf.fontItalic(), "farbe": cf.foreground().color().name() if cf.foreground().style() != Qt.NoBrush and cf.hasProperty(QTextFormat.ForegroundBrush) else "",
                "schrift": fam[0] if fam else "", "vor": round(abstand_davor_px(bf) * 0.75, 1), "nach": round(bf.bottomMargin() * 0.75, 1), "ausr": a,
                **self._rahmen_felder(), "liste": als_text(self.liste_spec()),
                "effekt": texteffekt.als_text(texteffekt.aus_format(cf)),
                "tabs": tabs_text(aus_block(bf)), **self._zeichen_felder(cf), **self._absatz_felder(bf)}


    @staticmethod
    def _absatz_felder(bf) -> dict:
        """Die Felder des Fensters „Absatz“ (außer Ausrichtung, Einzug links, Abstände), als Felder einer Formatvorlage."""
        from lunivo_writer.editor import absatzopt, seitenfluss
        lart = {2: "genau", 3: "mindestens"}.get(int(bf.lineHeightType()), "faktor")
        return {"rechts": round(px_to_mm(bf.rightMargin()), 1), "erste": round(px_to_mm(bf.textIndent()), 1), "rtl": bf.layoutDirection() == Qt.RightToLeft,
                "umbruch": seitenfluss.ist_manuell(bf), "zeilen_art": lart, "zeilen_pt": round(bf.lineHeight() * 0.75, 1) if lart != "faktor" else 12.0,
                "gliederung": 0, "opt": absatzopt.als_text(absatzopt.lesen(bf))}


    def _zeichen_felder(self, cf) -> dict:
        """Die Felder des Fensters „Schriftart“ (ohne Schrift, Größe, Schnitt, Farbe) eines Zeichenformats, als Felder einer Formatvorlage."""
        from lunivo_writer.ui.baukasten.text_format import aus_format
        w = aus_format(cf)
        keys = ("unter", "unterfarbe", "durch", "doppelt", "hoch", "tief", "kapital", "gross", "abstand", "kerning", "betonung", "schrift_asien", "schnitt_asien",
                "groesse_asien", "schrift_komplex", "schnitt_komplex", "groesse_komplex", "skala", "position", "kern_ab", "raster")
        return {**{k: w[k] for k in keys}, "versteckt": cf.hasProperty(P_VERSTECKT)}


    def _rahmen_felder(self) -> dict:
        """Rahmen und Schattierung des Absatzes an der Schreibmarke als Felder einer Formatvorlage."""
        l = self.absatzrahmen()
        fuell, muster = self.absatzschatten()
        return {"rahmen": l.text() if l else "", "fuell": fuell or "", "muster": muster[0] if muster else "",
                "musterfarbe": muster[1] if muster else ""}


    def stil_entfernen(self, name: str) -> int:
        """Eine gelöschte eigene Vorlage: die Absätze behalten ihr Aussehen, verlieren aber die Zuordnung."""
        n = 0
        cur = QTextCursor(self.document())
        cur.beginEditBlock()
        blk = self.document().firstBlock()
        while blk.isValid():
            if blk.blockFormat().hasProperty(STYLE_PROP) and blk.blockFormat().property(STYLE_PROP) == stile.PRAEFIX + name:
                c = QTextCursor(blk); bf = c.blockFormat(); bf.clearProperty(STYLE_PROP); c.setBlockFormat(bf); n += 1
            blk = blk.next()
        cur.endEditBlock()
        return n


    def current_style(self) -> str:
        return self._stil_name(self.textCursor().blockFormat())


    # ---- Einfügen ----------------------------------------------------------------
    def insert_page_break(self) -> None:
        cur = self.textCursor()
        bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
        cur.insertBlock(bf)


    def insert_column_break(self) -> None:
        from lunivo_writer.editor.zusatz import B_SPALTE
        cur = self.textCursor()
        bf = QTextBlockFormat(); bf.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore); bf.setProperty(B_SPALTE, 1)
        cur.insertBlock(bf)


    def insert_table(self, rows: int, cols: int, borders: bool = True) -> None:
        tf = QTextTableFormat()
        tf.setCellPadding(4); tf.setCellSpacing(0)
        tf.setBorder(0.5 if borders else 0); tf.setBorderCollapse(True)
        tf.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        t = self.textCursor().insertTable(rows, cols, tf)
        self.setTextCursor(t.cellAt(0, 0).firstCursorPosition())


    def insert_image(self, path: str) -> bool:
        img = QImage(path)
        if img.isNull():
            return False
        name = f"bild-{id(img)}-{self.document().revision()}"
        self.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
        w = float(img.width())
        maxw = self.page.content_width_px
        if w > maxw:
            scale = maxw / w
        else:
            scale = 1.0
        f = QTextImageFormat(); f.setName(name)
        f.setWidth(img.width() * scale); f.setHeight(img.height() * scale)
        self.textCursor().insertImage(f)
        return True


    def insert_link(self, url: str, text: str | None = None) -> None:
        cur = self.textCursor()
        f = QTextCharFormat()
        f.setAnchor(True); f.setAnchorHref(url)
        f.setForeground(QBrush(QColor("#0563C1"))); f.setFontUnderline(True)
        if cur.hasSelection():
            cur.mergeCharFormat(f)
        else:
            cur.insertText(text or url, f)


    # ---- Suchen/Ersetzen ---------------------------------------------------------------
    def find_text(self, text: str, backwards=False, case=False, whole=False) -> bool:
        if not text:
            return False
        flags = QTextDocument.FindFlag(0)
        if backwards:
            flags |= QTextDocument.FindBackward
        if case:
            flags |= QTextDocument.FindCaseSensitively
        if whole:
            flags |= QTextDocument.FindWholeWords
        if self.find(text, flags):
            return True
        # Umbruch am Dokumentende/-anfang
        cur = self.textCursor()
        cur.movePosition(QTextCursor.End if backwards else QTextCursor.Start)
        self.setTextCursor(cur)
        return self.find(text, flags)


    def replace_current(self, find: str, repl: str, case=False) -> bool:
        cur = self.textCursor()
        sel = cur.selectedText()
        if cur.hasSelection() and (sel == find or (not case and sel.lower() == find.lower())):
            fmt = QTextCharFormat(self._format_am_anfang(cur))              # die Formatierung des ersetzten Textes bleibt (Schrift, fett, kursiv …)
            cur.insertText(repl, fmt)
            return True
        return False


    @staticmethod
    def _format_am_anfang(cur: QTextCursor) -> QTextCharFormat:
        """Das Zeichenformat des ersten Zeichens der Markierung (``charFormat()`` eines Cursors mit Markierung wäre das davor)."""
        c = QTextCursor(cur)
        c.setPosition(cur.selectionStart())
        c.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        return c.charFormat()


    def replace_all(self, find: str, repl: str, case=False, whole=False) -> int:
        if not find:
            return 0
        flags = QTextDocument.FindFlag(0)
        if case:
            flags |= QTextDocument.FindCaseSensitively
        if whole:
            flags |= QTextDocument.FindWholeWords
        doc = self.document()
        cur = QTextCursor(doc)
        cur.beginEditBlock()
        n = 0
        pos = 0
        while True:
            found = doc.find(find, pos, flags)
            if found.isNull():
                break
            found.insertText(repl, QTextCharFormat(self._format_am_anfang(found)))
            pos = found.position()
            n += 1
        cur.endEditBlock()
        return n
