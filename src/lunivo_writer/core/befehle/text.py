"""Befehle: Zeichen und Absatz."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import QMenu, QMessageBox
from lunivo_writer.editor.linie import Linie
from lunivo_writer.ui.baukasten import FarbPalette, RahmenMenue, RasterAuswahl, ZellenRaster
from lunivo_writer.core.farben import Farbe


class TextBefehle:
    """Befehle des Bandes: Zeichen und Absatz. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Schriftart ---------------------------------------------------------------------------
    def schriftGroesser(self, k=None):
        if self.ed: self.ed.grow_font(1)


    def schriftKleiner(self, k=None):
        if self.ed: self.ed.grow_font(-1)


    groesser = schriftGroesser

    kleiner = schriftKleiner


    def schlicht(self, k=None):
        if self.ed: self.ed.clear_formatting()


    def fett(self, k=None):
        if self.ed: self.ed.toggle_bold(not self.an_fett())


    def an_fett(self): return self._fmt().fontWeight() >= 600


    def kursiv(self, k=None):
        if self.ed: self.ed.toggle_italic(not self.an_kursiv())


    def an_kursiv(self): return self._fmt().fontItalic()


    def unter(self, k=None):
        if self.ed: self.ed.toggle_underline(not self.an_unter())


    def an_unter(self): return self._fmt().underlineStyle() != QTextCharFormat.NoUnderline


    def menue_unterstrichKlappe(self):
        from lunivo_writer.ui.baukasten.text_format import UNTERSTREICHUNG, unter_format
        m = QMenu()
        for k, t in UNTERSTREICHUNG[1:]:                              # dieselben Arten wie im Fenster „Schriftart“
            m.addAction(t, lambda _=False, k=k: self.ed and self.ed._merge(unter_format(k)))
        m.addSeparator()
        m.addAction("Keine Unterstreichung", lambda: self.ed and self.ed._merge(unter_format("")))
        return m


    def objekteWaehlen(self, k=None):
        """Springt zum nächsten Bild im Text und markiert es (dann erscheinen die Bildtools)."""
        e = self.ed
        if not e:
            return
        doc = e.document()
        start = e.textCursor().selectionEnd()
        for runde in (0, 1):
            b = doc.findBlock(start) if runde == 0 else doc.firstBlock()
            while b.isValid():
                it = b.begin()
                while not it.atEnd():
                    fr = it.fragment()
                    if fr.isValid() and fr.charFormat().isImageFormat() and (runde == 1 or fr.position() >= start):
                        c = QTextCursor(doc); c.setPosition(fr.position()); c.setPosition(fr.position() + 1, QTextCursor.KeepAnchor)
                        e.setTextCursor(c); e.setFocus()
                        return
                    it += 1
                b = b.next()
        self.w.statusBar().showMessage("Im Dokument gibt es keine Bilder.", 4000)


    def zeichenumriss(self, k=None):
        if self.ed:
            self.ed.set_outline(not self.an_zeichenumriss())


    def an_zeichenumriss(self): return self._fmt().textOutline().style() != Qt.NoPen


    def texteffekte(self, k=None):
        """„Texteffekte formatieren“ in der rechten Seitenleiste: die Änderungen wirken sofort an der Markierung, solange der Bereich offen ist."""
        if not self.ed:
            return
        self.w.texteffekte_seitenleiste()


    def _effekt_setzen(self, **teile) -> None:
        """Einen Teil der Texteffekte der Markierung ersetzen (Wert ``None`` nimmt ihn weg); die übrigen Effekte bleiben."""
        if not self.ed:
            return
        from lunivo_writer.editor import texteffekt
        w = texteffekt.aus_format(self._fmt())
        for k, v in teile.items():
            if v is None:
                w.pop(k, None)
            else:
                w[k] = v
        self.ed._merge(texteffekt.zu_format(w))


    def menue_texteffekteKlappe(self):
        """Menü am Knopf „Texteffekte“ wie in der Vorlage: WordArt, Schatten, Spiegelung, Leuchteffekt (je mit Bildchen zum Anklicken), 3D-Drehung und
        Transformieren (nur für Formen und Textfelder, hier ausgegraut), „Weitere Texteffekte …“ öffnet die Seitenleiste."""
        from lunivo_writer.editor import texteffekt, textfx
        from lunivo_writer.ui.baukasten.voreinstellung_menue import VoreinstellungMenue
        m = QMenu()

        def untermenue(titel: str, keine: tuple | None) -> VoreinstellungMenue:
            u = VoreinstellungMenue(m, keine=keine); u.setTitle(titel); m.addMenu(u)
            return u
        wa = untermenue("WordArt", None)
        vor = textfx.wordart_vorgaben()
        wa.abschnitt("Formatvorlage", [(str(i), textfx.wordart_icon(w, (56, 44)), n) for i, (n, w) in enumerate(vor)], 6)
        wa.gewaehlt.connect(lambda k: self.ed and self.ed._merge(texteffekt.zu_format({**texteffekt.EFFEKT, **vor[int(k)][1]})))
        sc = untermenue("Schatten", ("Kein Schatten", textfx.voreinstellung_icon({})))
        sv = textfx.schatten_vorgaben()
        for abschnitt in ("Außen", "Innen", "Perspektive"):
            sc.abschnitt(abschnitt, [(str(i), textfx.voreinstellung_icon({"schatten": s}), n) for i, (a, n, s) in enumerate(sv) if a == abschnitt], 3)
        sc.gewaehlt.connect(lambda k: self._effekt_setzen(schatten=sv[int(k)][2] if k else None))
        sp = untermenue("Spiegelung(&R)", ("Keine Spiegelung", textfx.voreinstellung_icon({})))
        rv = textfx.reflektion_vorgaben()
        sp.abschnitt("Spiegelungsvarianten", [(str(i), textfx.voreinstellung_icon({"reflektion": r}), n) for i, (n, r) in enumerate(rv)], 3)
        sp.gewaehlt.connect(lambda k: self._effekt_setzen(reflektion=rv[int(k)][1] if k else None))
        le = untermenue("Leuchteffekt(&G)", ("Kein Leuchteffekt", textfx.voreinstellung_icon({})))
        lv = textfx.leuchten_vorgaben()
        le.abschnitt("Leuchtvarianten", [(str(i), textfx.voreinstellung_icon({"leuchten": g}), n) for i, (n, g) in enumerate(lv)], 6)
        le.gewaehlt.connect(lambda k: self._effekt_setzen(leuchten=lv[int(k)][1] if k else None))
        for titel in ("3D-Drehung", "Transformieren"): # wie in der Vorlage: nur für Formen und Textfelder, sonst ausgegraut
            a = m.addMenu(titel); a.setEnabled(False)
        m.addSeparator()
        m.addAction("Weitere Texteffekte(&O) …", self.texteffekte)
        return m


    def texteffekteFenster(self, k=None):
        """Dasselbe als eigenes Fenster (mit „OK“), wie es das Schriftart-Fenster und die Formatvorlage benutzen."""
        if not self.ed:
            return
        from lunivo_writer.editor import texteffekt
        from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
        d = TexteffektDialog(self.w, texteffekt.aus_format(self._fmt()))
        if d.exec():
            self.ed._merge(texteffekt.zu_format(d.werte()))


    def effekt(self, k=None):
        if not self.ed:
            return
        m = QMenu()
        m.addAction("Kapitälchen", lambda: self.ed.set_capitalization(QFont.SmallCaps))
        m.addAction("Großbuchstaben (Anzeige)", lambda: self.ed.set_capitalization(QFont.AllUppercase))
        m.addAction("Normal", lambda: self.ed.set_capitalization(QFont.MixedCase))
        m.addSeparator()
        m.addAction("Texteffekte …", self.texteffekte)
        m.addSeparator()
        for t, px in (("Zeichenabstand: eng", -1.0), ("Zeichenabstand: normal", 0.0), ("Zeichenabstand: weit", 2.0),
                      ("Zeichenabstand: sehr weit", 4.0)):
            m.addAction(t, lambda _=False, px=px: self.ed.set_letter_spacing(px))
        self._popup(m)


    def durch(self, k=None):
        if self.ed: self.ed.toggle_strike(not self.an_durch())


    def an_durch(self): return self._fmt().fontStrikeOut()


    def hoch(self, k=None):
        if self.ed: self.ed.set_script(None if self.an_hoch() else "sup")


    def an_hoch(self): return self._fmt().verticalAlignment() == QTextCharFormat.AlignSuperScript


    def tief(self, k=None):
        if self.ed: self.ed.set_script(None if self.an_tief() else "sub")


    def an_tief(self): return self._fmt().verticalAlignment() == QTextCharFormat.AlignSubScript


    def schreibweise(self, k=None):
        if self.ed: self.ed.change_case("upper")


    def menue_schreibweiseKlappe(self):
        m = QMenu()
        for t, mode in (("GROSSBUCHSTABEN", "upper"), ("kleinbuchstaben", "lower"), ("Jedes Wort Groß", "title")):
            m.addAction(t, lambda _=False, md=mode: self.ed and self.ed.change_case(md))
        return m


    def _farbmenue(self, setzen, ohne_text, vorschau=None):
        """Die gemeinsame Farbpalette; ``setzen`` bekommt eine QColor oder None („keine“)."""
        m = FarbPalette(self.w, keine_text=ohne_text)
        m.gewaehlt.connect(lambda c: self.ed and setzen(c))
        if vorschau is not None:                              # Live-Vorschau beim Überfahren der Farben
            m.ueberfahren.connect(lambda c: self.w.vorschau.zeigen(lambda e: vorschau(c)))
            m.verlassen.connect(self.w.vorschau.ende)
            m.aboutToHide.connect(self.w.vorschau.ende)
        return m


    def schriftfarbeJetzt(self, k=None):
        if self.ed: self.ed.set_text_color(QColor(getattr(self, "_schriftfarbe", Farbe.ROT)))


    def menue_schriftfarbeKlappe(self):
        def setze(c):
            self._schriftfarbe = c.name() if c else Farbe.SCHWARZ
            self.ed.set_text_color(c)
        return self._farbmenue(setze, "Automatisch", lambda c: self.ed.set_text_color(c))


    def hervorhebenJetzt(self, k=None):
        if self.ed: self.ed.set_highlight(QColor(getattr(self, "_marker", "#ffec99")))


    def menue_hervorhebenKlappe(self):
        def setze(c):
            self._marker = c.name() if c else "#ffec99"
            self.ed.set_highlight(c)
        return self._farbmenue(setze, "Keine Hervorhebung", lambda c: self.ed.set_highlight(c))


    # ---- Absatz ---------------------------------------------------------------------------------------
    def punkte(self, k=None):
        if self.ed: self.ed.toggle_list("bullet")


    def an_punkte(self):
        l = self.ed.textCursor().currentList() if self.ed else None
        return bool(l) and l.format().style() in (QTextListFormat.ListDisc, QTextListFormat.ListCircle, QTextListFormat.ListSquare)


    def zahlen(self, k=None):
        if self.ed: self.ed.toggle_list("number")


    def an_zahlen(self):
        l = self.ed.textCursor().currentList() if self.ed else None
        return bool(l) and l.format().style() == QTextListFormat.ListDecimal


    def _listenraster(self, art: str, titel: str) -> RasterAuswahl:
        """Auswahl der Aufzählungs- bzw. Nummerierungsarten: dieselben Kacheln und Listen wie im Fenster „Nummerierung und Aufzählungszeichen“."""
        from lunivo_writer.ui.baukasten.liste_dialog import aufzaehlungen, kachel_bild, nummerierungen
        arten = aufzaehlungen() if art == "bullet" else nummerierungen()
        aktuell = self.ed.liste_spec() if self.ed else None
        r = RasterAuswahl(self.w, titel=titel, spalten=4, groesse=QSize(96, 68))
        r.kachel("keine", "Keine", kachel_bild(None, QSize(96, 68)), aktuell=aktuell is None)
        for i, spec in enumerate(arten):
            r.kachel(str(i), "", kachel_bild(spec, QSize(96, 68)), aktuell=aktuell == spec)
        r.gewaehlt.connect(lambda k: self._liste_setzen(None if k == "keine" else arten[int(k)]))
        r.fuss("Weitere Aufzählungszeichen …" if art == "bullet" else "Weitere Nummerierungen …",
               lambda: self.listeDialog("aufzaehlung" if art == "bullet" else "nummerierung"))
        return r


    def _liste_setzen(self, spec) -> None:
        if self.ed:
            self.ed.set_liste(spec)


    def listeDialog(self, seite: str = "aufzaehlung"):
        """Fenster „Nummerierung und Aufzählungszeichen“ (Baukasten); das Ergebnis gilt für den Absatz an der Schreibmarke."""
        if not self.ed:
            return
        from lunivo_writer.ui.baukasten.liste_dialog import ListenDialog
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        d = ListenDialog(self.w, self.ed.liste_spec(), seite=seite)
        if ausfuehren(d):
            self.ed.set_liste(d.ergebnis())


    def menue_aufzaehlungKlappe(self):
        return self._listenraster("bullet", "Aufzählungszeichen")


    def menue_nummerierungKlappe(self):
        return self._listenraster("number", "Nummerierung")


    def menue_tabelleKlappe(self):
        """Tabelle einfügen wie bei WPS: Zellen überfahren, klicken; darunter der Dialog und die Schnelltabellen."""
        m = ZellenRaster(self.w)
        m.gewaehlt.connect(lambda z, s: self.ed and self.ed.insert_table(z, s))
        m.fuss("Tabelle einfügen …", self.tabelleRaster)
        m.addAction("Schnelltabelle …", self.schnelltabelle)
        return m


    def einzugMehr(self, k=None):
        if self.ed: self.ed.change_indent(10)


    def einzugWeniger(self, k=None):
        if self.ed: self.ed.change_indent(-10)


    def einzugGenau(self, k=None):
        self.w.paragraph_dialog()


    def ebeneHoeher(self, k=None):
        if self.ed: self.ed.list_level(1)


    def ebeneTiefer(self, k=None):
        if self.ed: self.ed.list_level(-1)


    def links(self, k=None):
        if self.ed: self.ed.set_alignment(Qt.AlignLeft)


    def an_links(self): return bool(self.ed) and bool(self.ed.alignment() & Qt.AlignLeft)


    def mitte(self, k=None):
        if self.ed: self.ed.set_alignment(Qt.AlignHCenter)


    def an_mitte(self): return bool(self.ed) and bool(self.ed.alignment() & Qt.AlignHCenter)


    def rechts(self, k=None):
        if self.ed: self.ed.set_alignment(Qt.AlignRight)


    def an_rechts(self): return bool(self.ed) and bool(self.ed.alignment() & Qt.AlignRight)


    def block(self, k=None):
        if self.ed: self.ed.set_alignment(Qt.AlignJustify)


    def an_block(self): return bool(self.ed) and bool(self.ed.alignment() & Qt.AlignJustify)


    def menue_zeilenabstandKlappe(self):
        m = QMenu()
        for f in (1.0, 1.5, 2.0, 2.5, 3.0):                         # wie in der Vorlage; alles andere im Fenster Absatz (dort auch „Tabstopps …“)
            m.addAction(f"{f:g}".replace(".", ","), lambda _=False, f=f: self.ed and self.ed.set_line_spacing(f))
        m.addAction("Mehr …", self.w.paragraph_dialog)
        return m


    def steuerzeichenZeigen(self, k=None):
        self.w.a_marks.toggle() if hasattr(self.w, "a_marks") else None


    def an_steuerzeichenZeigen(self): return self.w.marks_on


    # ==== Start: weitere Absatz-/Zeichenbefehle ==================================================================
    def verteilt(self, k=None):
        if self.ed: self.ed.set_alignment(Qt.AlignJustify)


    def formatUebertragen(self, k=None):
        e = self.ed
        if not e:
            return
        if getattr(self, "_pinsel", None) is None:
            self._pinsel = QTextCharFormat(e.textCursor().charFormat())
            self.w.lbl_msg.setText("Format aufgenommen — jetzt Text markieren, um es zu übertragen.")
        else:
            c = e.textCursor()
            if c.hasSelection():
                c.mergeCharFormat(self._pinsel)
            self._pinsel = None
            self.w.lbl_msg.setText("Format übertragen.")


    def an_formatUebertragen(self): return getattr(self, "_pinsel", None) is not None


    def sortieren(self, k=None):
        e = self.ed
        if not e:
            return
        c = e.textCursor()
        if not c.hasSelection():
            QMessageBox.information(self.w, "Sortieren", "Bitte zuerst mehrere Absätze markieren.")
            return
        a, b = sorted((c.anchor(), c.position()))
        doc = e.document()
        bl = doc.findBlock(a)
        blocks = []
        while bl.isValid() and bl.position() <= b:
            blocks.append(bl); bl = bl.next()
        if len(blocks) < 2:
            return
        texte = [x.text() for x in blocks]
        auf = texte != sorted(texte, key=str.lower)
        neu = sorted(texte, key=str.lower, reverse=not auf)
        c.beginEditBlock()
        for blk, t in zip(blocks, neu):
            cc = QTextCursor(blk)
            cc.movePosition(QTextCursor.StartOfBlock)
            cc.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            cc.insertText(t)
        c.endEditBlock()


    def menue_absatzSchattierung(self):
        def setze(c):
            self.ed.set_absatzschatten(c.name() if c else None)
        m = self._farbmenue(setze, "Keine Schattierung")
        m.zusatz_eintrag("Rahmen und Schattierung …", lambda: self.absatzRahmen(seite="schattierung"))
        return m


    _rahmen_stil = Linie(Farbe.SCHWARZ, 0.75, "einfach")          # Linie, die ein neuer Rahmen aus dem Menü bekommt


    def menue_absatzRahmen(self):
        m = RahmenMenue(self.w, innen="h", mehr=self.absatzRahmen)
        m.gewaehlt.connect(lambda _s, k: self._rahmen_seite(k))
        return m


    def _rahmen_seite(self, schluessel: str) -> None:
        """Eintrag des Rahmen-Menüs: einzelne Seiten ein-/ausschalten, alle, außen oder keine."""
        if not self.ed:
            return
        aktuell = self.ed.absatzrahmen()
        seiten = set(aktuell.seiten) if aktuell else set()
        if schluessel == "kein":
            seiten = set()
        elif schluessel == "alle":
            seiten = set("tblrh")
        elif schluessel == "aussen":
            seiten = set("tblr")
        else:
            k = {"unten": "b", "oben": "t", "links": "l", "rechts": "r", "innen_h": "h"}[schluessel]
            seiten ^= {k}
        basis = aktuell or self._rahmen_stil
        self.ed.set_absatzrahmen(basis.mit_seiten("".join(seiten)).text() if seiten else None)


    def absatzRahmen(self, k=None, seite: str = "rahmen"):
        """Fenster „Rahmen und Schattierung“ (Reiter Rahmen · Seitenrand · Schattierung); ``seite`` wählt den Reiter."""
        if not self.ed:
            return
        from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        fuell, muster = self.ed.absatzschatten()
        alt_rand = self.ed.page.border
        d = RahmenSchattierungDialog(self.w, rahmen=self.ed.absatzrahmen(), fuell=fuell, muster=muster, seitenrand=alt_rand,
                                     fuer=["Absatz"], seite=seite)
        if not ausfuehren(d):
            return
        linie = d.rahmen()
        if linie is not None:
            self._rahmen_stil = linie.mit_seiten("tblr")
        self.ed.set_absatzrahmen(linie.text() if linie is not None else None)
        self.ed.set_absatzschatten(*d.schattierung())
        if d.seitenrand() != alt_rand:
            self._seite_aendern(border=d.seitenrand())


    def _stile_fertig(self) -> None:
        """Nach jeder Änderung an den Vorlagen: Galerie neu füllen, Tastenkombinationen der Vorlagen in allen Dokumenten neu setzen."""
        getattr(self.w.band, "stile_aktualisieren", lambda: None)()
        for t in self.w._doc_tabs():
            t.editor.stil_tasten()


    def _taste_belegt(self, taste: str, eigene: str | None = None) -> str | None:
        """Name dessen, was die Tastenkombination schon hat (Befehl im Fenster oder andere Vorlage), sonst None."""
        from PySide6.QtGui import QAction, QKeySequence
        from lunivo_writer.editor import stile
        seq = QKeySequence(taste)
        for a in self.w.findChildren(QAction):
            if any(s == seq for s in a.shortcuts()):
                return a.text().replace("&", "").replace(" …", "").strip() or taste
        for n in stile.namen():
            if n != eigene and stile.definition(n).get("taste") == taste:
                return f"Formatvorlage „{n}“"
        return None


    def neueFormatvorlage(self, k=None):
        """Fenster „Neue Formatvorlage“ (Baukasten); die Werte kommen vom Absatz an der Schreibmarke."""
        from lunivo_writer.editor import stile
        from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        d = FormatvorlageDialog(self.w, start=(self.ed.stil_aus_auswahl() if self.ed else None), belegt=self._taste_belegt,
                                standard_tab_mm=self.ed.standard_tab_mm() if self.ed else None)
        if not ausfuehren(d):
            return
        erg = d.ergebnis()
        std = erg.pop("tab_standard", None)
        if self.ed and std:
            self.ed.set_standard_tab_mm(std)
        merken = erg.pop("zur_vorlage", True)                 # „Zur Vorlage hinzufügen“: auch für künftige Dokumente speichern
        grund = stile.anlegen(erg.pop("name"), basis=erg.pop("basis"), folge=erg.pop("folge"), **erg)
        if grund:
            QMessageBox.warning(self.w, "Neue Formatvorlage", grund)
            return
        if merken:
            self.w.settings.set("stile/eigene", stile.als_json_neu())
        self._stile_fertig()


    def formatvorlageAendern(self, name: str):
        """Rechtsklick auf eine Vorlage in der Galerie ▸ Ändern …: dasselbe Fenster, der Name steht fest."""
        from lunivo_writer.editor import stile
        from lunivo_writer.ui.baukasten.formatvorlage_dialog import FormatvorlageDialog
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        d = FormatvorlageDialog(self.w, aendern=name, belegt=self._taste_belegt, standard_tab_mm=self.ed.standard_tab_mm() if self.ed else None)
        if not ausfuehren(d):
            return
        erg = d.ergebnis()
        std = erg.pop("tab_standard", None)
        if self.ed and std:
            self.ed.set_standard_tab_mm(std)
        erg.pop("zur_vorlage", None)
        erg.pop("name"); basis, folge = erg.pop("basis"), erg.pop("folge")
        if stile.ist_eigen(name):
            stile.loeschen(name)
            stile.anlegen(name, basis=basis, folge=folge, **erg)
        else:
            stile.aendern(name, **erg)
        self.w.settings.set("stile/aenderungen", stile.als_json())
        self.w.settings.set("stile/eigene", stile.als_json_neu())
        for t in self.w._doc_tabs():
            t.editor.stil_neu_anwenden(name)
        self._stile_fertig()


    def formatvorlageLoeschen(self, name: str):
        from lunivo_writer.editor import stile
        if not stile.ist_eigen(name):
            return
        if QMessageBox.question(self.w, "Formatvorlage löschen", f"„{name}“ löschen? Absätze behalten ihr Aussehen, gelten aber wieder als „Standard“.") != QMessageBox.Yes:
            return
        for t in self.w._doc_tabs():
            t.editor.stil_entfernen(name)
        stile.loeschen(name)
        self.w.settings.set("stile/eigene", stile.als_json_neu())
        self._stile_fertig()


    vorlageNeu = neueFormatvorlage                                  # Menüleiste ▸ Start ▸ Stile ▸ Neue Formatvorlage …
