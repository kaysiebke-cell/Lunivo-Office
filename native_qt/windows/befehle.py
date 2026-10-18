"""Befehle des Bandes: Aktionsname aus register.json → Funktion.

Ein Name, den es hier nicht gibt, bleibt im Band sichtbar, aber ausgegraut — mit dem Hinweis,
dass er in der nativen Fassung noch fehlt. So entsteht die Liste dessen, was noch zu tun ist,
von selbst (siehe `fehlende()`), und nichts steht als Attrappe da.

Konvention: Methode `name(self, knopf=None)`; `w.xyz` heißt `w_xyz`.
Zustand eines Schalters: Methode `an_name(self) -> bool`.
Klappe (Pfeilmenü): Methode `menue_name(self) -> QMenu`.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QIcon, QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat
from ..editor.page import HeaderFooter
from PySide6.QtWidgets import QApplication, QColorDialog, QFileDialog, QInputDialog, QLineEdit, QMenu, QMessageBox

PALETTE = ["#000000", "#c92a2a", "#e8590c", "#f08c00", "#2f9e44", "#1098ad", "#1971c2", "#6741d9",
           "#c2255c", "#868e96", "#ffec99", "#b2f2bb", "#a5d8ff", "#eebefa", "#ffffff"]


def _farbfeld(c: str) -> QIcon:
    pm = QPixmap(14, 14)
    pm.fill(QColor(c))
    return QIcon(pm)


class Befehle:
    def __init__(self, win):
        self.w = win

    # ---- Hilfen --------------------------------------------------------------------
    @property
    def ed(self):
        return self.w.current_editor()

    @staticmethod
    def _teile(name: str):
        """'w.setzePapier:["a4"]' → ('w_setzePapier', ['a4'])"""
        basis, _, rest = name.partition(":")
        return basis.replace(".", "_"), (json.loads(rest) if rest else [])

    def hat(self, name: str) -> bool:
        return callable(getattr(self, self._teile(name)[0], None))

    def tun(self, name: str, knopf=None):
        basis, args = self._teile(name)
        f = getattr(self, basis, None)
        if callable(f):
            return f(knopf, *args)

    def zustand(self, name: str):
        basis, _ = self._teile(name)
        f = getattr(self, "an_" + basis, None)
        return bool(f()) if callable(f) else None

    def haken_wert(self, item: dict) -> bool | None:
        """Haken eines Menüpunkts: Zustandsfrage des Menüeintrags (z. B. w.randVorgabeJetzt) gegen sein Argument."""
        g = item.get("haken")
        if not isinstance(g, str):
            return None
        f = getattr(self, self._teile(g)[0], None)
        if not callable(f):
            return None
        wert = f()
        _, args = self._teile(item.get("tun", ""))
        n = item.get("name")
        if g.endswith("querJetzt"):
            return bool(wert) if n == "Querformat" else not wert
        return (wert == args[0]) if args else bool(wert)

    def klappe(self, name: str):
        f = getattr(self, "menue_" + name.replace(".", "_"), None)
        return f() if callable(f) else None

    def _popup(self, menue) -> None:
        """Menü an der Mausposition zeigen (eigene Stelle, damit Tests es abfangen können)."""
        menue.exec(QCursor.pos())

    def fehlende(self, namen) -> list[str]:
        return sorted(n for n in namen if not self.hat(n))

    def _fmt(self):
        e = self.ed
        return e.textCursor().charFormat() if e else QTextCharFormat()

    # ---- Zwischenablage ------------------------------------------------------------------
    def einfuegen(self, k=None):
        if self.ed: self.ed.paste()

    def einfuegenOhne(self, k=None):
        self.w.paste_plain()

    def menue_einfuegenKlappe(self):
        m = QMenu()
        m.addAction("Einfügen", self.einfuegen)
        m.addAction("Einfügen ohne Formatierung", self.einfuegenOhne)
        return m

    def ausschneiden(self, k=None):
        if self.ed: self.ed.cut()

    def kopieren(self, k=None):
        if self.ed: self.ed.copy()

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
        m = QMenu()
        for t, st in (("Einfach", QTextCharFormat.SingleUnderline), ("Gestrichelt", QTextCharFormat.DashUnderline),
                      ("Gepunktet", QTextCharFormat.DotLine), ("Strich-Punkt", QTextCharFormat.DashDotLine),
                      ("Wellenlinie", QTextCharFormat.WaveUnderline)):
            m.addAction(t, lambda _=False, st=st: self.ed and self.ed.set_underline_style(st))
        m.addSeparator()
        m.addAction("Keine Unterstreichung", lambda: self.ed and self.ed.set_underline_style(QTextCharFormat.NoUnderline))
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

    def effekt(self, k=None):
        if not self.ed:
            return
        m = QMenu()
        m.addAction("Kapitälchen", lambda: self.ed.set_capitalization(QFont.SmallCaps))
        m.addAction("Großbuchstaben (Anzeige)", lambda: self.ed.set_capitalization(QFont.AllUppercase))
        m.addAction("Normal", lambda: self.ed.set_capitalization(QFont.MixedCase))
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

    def _farbmenue(self, setzen, ohne_text):
        m = QMenu()
        for c in PALETTE:
            m.addAction(_farbfeld(c), c, lambda _=False, c=c: self.ed and setzen(QColor(c)))
        m.addSeparator()
        m.addAction(ohne_text, lambda: self.ed and setzen(None))
        m.addAction("Weitere Farben …", lambda: self._farbe_waehlen(setzen))
        return m

    def _farbe_waehlen(self, setzen):
        c = QColorDialog.getColor(Qt.black, self.w, "Farbe")
        if c.isValid() and self.ed:
            setzen(c)

    def schriftfarbeJetzt(self, k=None):
        if self.ed: self.ed.set_text_color(QColor(getattr(self, "_schriftfarbe", "#c92a2a")))

    def menue_schriftfarbeKlappe(self):
        def setze(c):
            self._schriftfarbe = c.name() if c else "#000000"
            self.ed.set_text_color(c)
        return self._farbmenue(setze, "Automatisch")

    def hervorhebenJetzt(self, k=None):
        if self.ed: self.ed.set_highlight(QColor(getattr(self, "_marker", "#ffec99")))

    def menue_hervorhebenKlappe(self):
        def setze(c):
            self._marker = c.name() if c else "#ffec99"
            self.ed.set_highlight(c)
        return self._farbmenue(setze, "Keine Hervorhebung")

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

    def menue_aufzaehlungKlappe(self):
        m = QMenu()
        for t, s in (("● Punkt", QTextListFormat.ListDisc), ("○ Kreis", QTextListFormat.ListCircle), ("■ Quadrat", QTextListFormat.ListSquare)):
            m.addAction(t, lambda _=False, s=s: self.ed and self.ed.toggle_list("bullet", s))
        return m

    def menue_nummerierungKlappe(self):
        m = QMenu()
        for t, s in (("1. 2. 3.", QTextListFormat.ListDecimal), ("a. b. c.", QTextListFormat.ListLowerAlpha),
                     ("A. B. C.", QTextListFormat.ListUpperAlpha), ("i. ii. iii.", QTextListFormat.ListLowerRoman),
                     ("I. II. III.", QTextListFormat.ListUpperRoman)):
            m.addAction(t, lambda _=False, s=s: self.ed and self.ed.toggle_list("number", s))
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
        for f in (1.0, 1.15, 1.5, 2.0, 2.5, 3.0):
            m.addAction(f"{f:g}".replace(".", ","), lambda _=False, f=f: self.ed and self.ed.set_line_spacing(f))
        m.addSeparator()
        m.addAction("Absatz …", self.w.paragraph_dialog)
        return m

    def steuerzeichenZeigen(self, k=None):
        self.w.a_marks.toggle() if hasattr(self.w, "a_marks") else None

    def an_steuerzeichenZeigen(self): return self.w.marks_on

    # ---- Bearbeiten -----------------------------------------------------------------------------------------
    def suchen(self, k=None, *_):
        self.w.find_dialog_show()

    ersetzen = suchen
    w_sucheZeigen = suchen

    def allesMarkieren(self, k=None):
        if self.ed: self.ed.selectAll()

    # ---- Einfügen -------------------------------------------------------------------------------------------------
    def seitenumbruch(self, k=None):
        if self.ed: self.ed.insert_page_break()

    def tabelleRaster(self, k=None):
        self.w.insert_table()

    def bild(self, k=None):
        self.w.insert_image()

    def hyperlink(self, k=None):
        self.w.insert_link()

    def kopfFussZeigen(self, k=None):
        self.w.edit_header_footer(True)

    def menue_seitenzahlKlappe(self):
        m = QMenu()
        m.addAction("Seitenzahl in die Fußzeile", self.w.insert_page_number)
        return m

    def seitenzahlKlappe(self, k=None):
        self.w.insert_page_number()


    # ---- Seitenlayout --------------------------------------------------------------------------------------------------
    def seitenraenderRahmen(self, k=None, *_):
        self.w.page_setup()

    # ---- Überprüfen / Schreibhilfe --------------------------------------------------------------------------------------------
    def woerterZaehlen(self, k=None):
        self.w.word_count()

    def rechtschreibung(self, k=None):
        self.w.assistant.pruefen(True)

    def w_pruefen(self, k=None):
        self.w.assistant.pruefen(True)

    def gruendlichPruefen(self, k=None):
        self.w.assistant.gruendlich()

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

    # ---- Ansicht ---------------------------------------------------------------------------------------------------------------
    def handbuch(self, k=None):
        from ..widgets import hilfe_dialoge
        hilfe_dialoge.handbuch(self.w).show()

    def tastenHilfe(self, k=None):
        from ..widgets import hilfe_dialoge
        hilfe_dialoge.tastenkuerzel(self.w).show()

    def erweiterungen(self, k=None):
        from ..widgets import hilfe_dialoge
        hilfe_dialoge.erweiterungen(self.w).show()

    def vorlagenWaehlen(self, k=None): self.w.neu_aus_vorlage()

    def vorlagenOrdner(self, k=None):
        import os
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from ..editor import vorlagen
        o = vorlagen.vorlagenordner(self.w.settings)
        os.makedirs(o, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(o))

    def menueleisteZeigen(self, k=None):
        self.w.toggle_menubar()

    def an_menueleisteZeigen(self): return self.w.menubar_wanted

    def registerAnpassen(self, k=None):
        from ..widgets.oberflaeche_dialoge import RegisterAnpassenDialog
        if RegisterAnpassenDialog(self.w, self.w.settings, self.w.band.daten).exec():
            self.w.neu_bauen_band()

    def schnellzugriffAnpassen(self, k=None):
        from ..widgets.oberflaeche_dialoge import SchnellzugriffDialog, lade_json
        from ..widgets.register_band import RegisterBand
        akt = lade_json(self.w.settings, "ui/schnellzugriff", None)
        if akt is None:
            akt = [a for _s, _n, a in RegisterBand.SCHNELL]
        if SchnellzugriffDialog(self.w, self.w.settings, RegisterBand.SCHNELL_ALLE, akt).exec():
            self.w.neu_bauen_band()

    def symbolTauschen(self, k=None):
        from ..widgets.oberflaeche_dialoge import SymbolTauschenDialog
        SymbolTauschenDialog(self.w, self.w.settings).exec()
        self.w.neu_bauen_band()

    def benutzeroberflaeche(self, k=None):
        from ..widgets.oberflaeche_dialoge import OberflaecheDialog
        d = OberflaecheDialog(self.w, self.w.settings)
        if d.exec():
            self.w.oberflaeche_aendern(d.wahl(), d.menue.isChecked())

    def leistenZeigen(self, k=None):
        neu = "register" if self.w.settings.get("ui/oberflaeche", "register") == "symbolleisten" else "symbolleisten"
        self.w.oberflaeche_aendern(neu, self.w.menubar_wanted)

    def an_leistenZeigen(self): return self.w.settings.get("ui/oberflaeche", "register") == "symbolleisten"

    def vorlagenZurueck(self, k=None):
        if QMessageBox.question(self.w, "Vorlagen zurücksetzen",
                                "Register, Schnellzugriff und ausgetauschte Symbole auf die Vorgabe zurücksetzen?") != QMessageBox.Yes:
            return
        for key in ("ui/register_plan", "ui/schnellzugriff", "ui/symbol_tausch", "ui/oberflaeche"):
            self.w.settings.remove(key)
        self.w._symbole_anwenden()
        self.w.neu_bauen_band()

    # ---- Datei (☰-Menü und Schnellzugriff) ----------------------------------------------------------------
    def neu(self, k=None): self.w.new_document()
    def oeffnen(self, k=None): self.w.open_dialog()
    def speichern(self, k=None): self.w.save()
    def speichernUnter(self, k=None): self.w.save_as()
    def speichernPdf(self, k=None): self.w.export_pdf_dialog()
    def drucken(self, k=None): self.w.print_dialog()
    def vorschau(self, k=None): self.w.print_preview()
    def eigenschaften(self, k=None): self.w.show_info()
    def umbenennen(self, k=None): self.w.rename_document()
    def schliessen(self, k=None): self.w.close_tab(self.w.docs.currentIndex())
    def beenden(self, k=None): self.w.close()
    def ueber(self, k=None): self.w.about()
    def rueckgaengig(self, k=None):
        if self.ed: self.ed.undo()
    def wiederholen(self, k=None):
        if self.ed: self.ed.redo()

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
        p = t.page
        ist = tuple(round(x) for x in (p.margin_top_mm, p.margin_bottom_mm, p.margin_left_mm, p.margin_right_mm))
        for art, v in self.RAND.items():
            if ist == v:
                return art
        return ""

    def seitenraender(self, k=None, *_): self.w.page_setup()
    seitenraenderRahmen = seitenraender

    def w_setzePapier(self, k, art):
        b, h = self.PAPIER[art]
        self.w._page_change(lambda p: (setattr(p, "width_mm", min(b, h) if not p.landscape else max(b, h)),
                                       setattr(p, "height_mm", max(b, h) if not p.landscape else min(b, h))))

    def w_papierJetzt(self):
        t = self.w.current_tab()
        if not t:
            return ""
        a, b = sorted((round(t.page.width_mm), round(t.page.height_mm)))
        for art, (x, y) in self.PAPIER.items():
            if (a, b) == tuple(sorted((x, y))):
                return art
        return ""

    def w_querJetzt(self):
        t = self.w.current_tab()
        return bool(t) and t.page.landscape

    def querformat(self, k=None):
        t = self.w.current_tab()
        if t:
            self.w.set_orientation(not t.page.landscape)

    def w_setzeThema(self, k, wahl):
        self.w.set_theme(wahl)

    def w_themaJetzt(self):
        return self.w.settings.get("theme", "system")

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
        m = QMenu()
        def setze(c):
            if self.ed:
                self.ed._block_merge(lambda bf: bf.setBackground(QBrush(c)) if c else bf.clearBackground())
        for c in ("#fff3bf", "#d3f9d8", "#d0ebff", "#ffe3e3", "#e9ecef"):
            m.addAction(_farbfeld(c), "Schattierung " + c, lambda _=False, c=c: setze(QColor(c)))
        m.addSeparator()
        m.addAction("Keine Schattierung", lambda: setze(None))
        return m

    RAHMEN_STUFEN = [("Dünn (0,75 pt)", 0.75, "einfach"), ("Mittel (1,5 pt)", 1.5, "einfach"), ("Dick (3 pt)", 3.0, "einfach"),
                     ("Doppelt", 1.0, "doppelt")]

    def menue_absatzRahmen(self):
        m = QMenu()
        for text, pt, art in self.RAHMEN_STUFEN:
            m.addAction(text, lambda _=False, pt=pt, art=art: self.ed and self.ed.set_absatzrahmen(f"#000000|{pt}|{art}"))
        m.addAction("Farbe wählen …", self.absatzRahmen)
        m.addSeparator()
        m.addAction("Kein Rahmen", lambda: self.ed and self.ed.set_absatzrahmen(None))
        return m

    def absatzRahmen(self, k=None):
        if not self.ed:
            return
        c = QColorDialog.getColor(Qt.black, self.w, "Rahmenfarbe")
        if c.isValid():
            self.ed.set_absatzrahmen(f"{c.name()}|1.5|einfach")

    def stileVerwalten(self, k=None):
        from ..editor import stile
        from ..widgets.oberflaeche_dialoge import StileVerwaltenDialog

        def speichern():
            self.w.settings.set("stile/aenderungen", stile.als_json())

        def anwenden(name):
            for t in self.w._doc_tabs():
                t.editor.stil_neu_anwenden(name)
        StileVerwaltenDialog(self.w, speichern, anwenden).exec()

    # ==== Einfügen ===========================================================================================================
    def leereSeite(self, k=None, quer=False):
        if self.ed:
            self.ed.insert_page_break(); self.ed.insert_page_break()

    def sonderzeichen(self, k=None):
        from ..widgets.sonderzeichen import SonderzeichenDialog
        e = self.ed
        if e:
            d = SonderzeichenDialog(self.w, lambda z: e.insertPlainText(z))
            d.show()
            self._sz = d

    def inhaltsverzeichnis(self, k=None):
        if self.ed:
            from ..editor.verzeichnis import verzeichnis_einfuegen
            n = verzeichnis_einfuegen(self.ed)
            if not n:
                QMessageBox.information(self.w, "Inhaltsverzeichnis", "Im Dokument gibt es keine Überschriften. "
                                        "Formatieren Sie Überschriften mit den Stilen „Überschrift 1–3“.")

    def verzeichnisseAktualisieren(self, k=None):
        if self.ed:
            from ..editor.verzeichnis import verzeichnis_aktualisieren
            verzeichnis_aktualisieren(self.ed)

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

    # ---- Seitenhintergrund -------------------------------------------------------------------
    def _seite_aendern(self, **felder):
        e = self.ed
        if not e:
            return
        pg = e.page.copy()
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
        from ..widgets.dialogs import WasserzeichenDialog
        d = WasserzeichenDialog(self.w, self.ed.page.watermark)
        if d.exec():
            self._seite_aendern(watermark=d.ergebnis())

    def seitenrahmen(self, k=None):
        if not self.ed:
            return
        from ..widgets.dialogs import SeitenrahmenDialog
        d = SeitenrahmenDialog(self.w, self.ed.page.border)
        if d.exec():
            self._seite_aendern(border=d.ergebnis())

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
        from ..editor.pagination import _trenner
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

    def an_textrichtung(self):
        return bool(self.ed and self.ed.textCursor().blockFormat().layoutDirection() == Qt.RightToLeft)

    DESIGNS = {"Office": ("Liberation Sans", "Liberation Sans", "#1f3864"),
               "Klassisch": ("Liberation Serif", "Liberation Serif", "#000000"),
               "Modern": ("DejaVu Sans", "DejaVu Sans", "#2f6fb5"),
               "Zeitung": ("Liberation Serif", "Liberation Sans", "#222222"),
               "Dezent": ("Liberation Sans", "Liberation Sans", "#555555")}
    FARBSCHEMEN = {"Blau": "#2f6fb5", "Grün": "#2f9e75", "Rot": "#c92a2a", "Violett": "#7048a8", "Orange": "#e8590c", "Grau": "#495057"}
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

    def designSchriften(self, k=None):
        if self.ed and (n := self._wahl("Schriftarten", self.SCHRIFTPAARE)):
            f, h = self.SCHRIFTPAARE[n]
            self.ed.apply_design(f, h, None)

    # ---- Einfügen: Illustrationen, Text, Symbole, Tabellen, Seiten ----------------------------------------------------
    def _bild_einfuegen(self, img, alt):
        from ..editor import einfuegen as E
        E.qimage_einfuegen(self.ed, img, alt)

    def formenGalerie(self, k=None):
        if not self.ed:
            return
        from ..editor import einfuegen as E
        m = QMenu()
        for f in E.FORMEN:
            m.addAction(f, lambda _=False, f=f: self._bild_einfuegen(E.form_bild(f), f"Form: {f}"))
        m.addSeparator()
        m.addAction("Weitere Formen und Farben …", self.zeichnen)
        self._popup(m)

    def zeichnen(self, k=None):
        if self.ed:
            from ..widgets.einfuegen_dialoge import FormDialog
            d = FormDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), f"Form: {d.art.currentText()}")

    def wordart(self, k=None):
        if self.ed:
            from ..widgets.einfuegen_dialoge import WordArtDialog
            d = WordArtDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), "WordArt: " + d.text.text())

    def diagramm(self, k=None):
        if self.ed:
            from ..widgets.einfuegen_dialoge import DiagrammDialog
            d = DiagrammDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), f"{d.art.currentText()}diagramm: {d.titel.text()}")

    def piktogramm(self, k=None):
        if self.ed:
            from ..editor import einfuegen as E
            from ..widgets.einfuegen_dialoge import PiktogrammDialog
            d = PiktogrammDialog(self.w)
            if d.exec():
                n, farbe = d.ergebnis()
                if n:
                    self._bild_einfuegen(E.piktogramm_bild(n, 96, farbe), f"Piktogramm: {n}")

    def screenshot(self, k=None):
        if not self.ed:
            return
        antwort = QMessageBox(QMessageBox.Question, "Bildschirmfoto", "Was soll aufgenommen werden?", QMessageBox.NoButton, self.w)
        ganz = antwort.addButton("Ganzer Bildschirm", QMessageBox.AcceptRole)
        bereich = antwort.addButton("Bereich wählen …", QMessageBox.AcceptRole)
        antwort.addButton("Abbrechen", QMessageBox.RejectRole)
        antwort.exec()
        if antwort.clickedButton() not in (ganz, bereich):
            return
        nur_bereich = antwort.clickedButton() is bereich
        from PySide6.QtCore import QTimer
        self.w.hide()
        QTimer.singleShot(500, lambda: self._aufnehmen(nur_bereich))

    def _aufnehmen(self, nur_bereich: bool):
        pm = QApplication.primaryScreen().grabWindow(0)
        if not nur_bereich:
            self.w.show()
            self._foto_einfuegen(pm)
            return
        from ..widgets.bildschirmfoto import BereichWahl
        self._wahl = BereichWahl(pm)
        self._wahl.fertig.connect(self._bereich_fertig)
        self._wahl.showFullScreen()

    def _bereich_fertig(self, pm):
        self.w.show()
        self._foto_einfuegen(pm)

    def _foto_einfuegen(self, pm):
        if pm is not None and not pm.isNull() and self.ed:
            self._bild_einfuegen(pm.toImage(), "Bildschirmfoto")

    def textfeld(self, k=None):
        if self.ed:
            from ..editor import einfuegen as E
            E.textfeld(self.ed)

    def initiale(self, k=None):
        if self.ed:
            from ..editor import einfuegen as E
            if not E.initiale(self.ed):
                self.w.statusBar().showMessage("Der Absatz ist leer.", 3000)

    def textAusDatei(self, k=None):
        if not self.ed:
            return
        from ..document_io import formats
        from ..document_io.report import DocumentIOError
        from ..editor import einfuegen as E
        pfad, _ = QFileDialog.getOpenFileName(self.w, "Text aus Datei einfügen", self.w.settings.get("last_dir", ""), formats.OPEN_FILTER)
        if not pfad:
            return
        try:
            rep = E.text_aus_datei(self.ed, pfad)
        except DocumentIOError as e:
            QMessageBox.warning(self.w, "Einfügen nicht möglich", str(e))
            return
        self.w._show_report(rep, "Hinweise zur eingefügten Datei", "beim Einfügen")

    def formel(self, k=None):
        if self.ed:
            from ..editor import einfuegen as E
            from ..widgets.einfuegen_dialoge import FormelDialog
            d = FormelDialog(self.w)
            if d.exec() and d.eingabe.text().strip():
                E.formel_einfuegen(self.ed, d.eingabe.text())

    def schnelltabelle(self, k=None):
        if not self.ed:
            return
        from ..editor import einfuegen as E
        m = QMenu()
        for n in E.SCHNELLTABELLEN:
            m.addAction(n, lambda _=False, n=n: E.schnelltabelle(self.ed, n))
        self._popup(m)

    def deckblatt(self, k=None):
        if not self.ed:
            return
        from ..editor import einfuegen as E
        from ..widgets.einfuegen_dialoge import DeckblattDialog
        d = DeckblattDialog(self.w, self.w.settings.get("benutzer/name", ""))
        if d.exec():
            E.deckblatt_einfuegen(self.ed, d.vorlage.currentText(), d.titel.text(), d.unter.text(), d.autor.text(), d.datum.text())

    def datumUhrzeit(self, k=None):
        if self.ed:
            from ..widgets.einfuegen_dialoge import DatumDialog
            d = DatumDialog(self.w)
            if d.exec() and d.ergebnis():
                self.ed.textCursor().insertText(d.ergebnis())
                self.ed.document().setModified(True)

    def textbaustein(self, k=None):
        if self.ed:
            from ..widgets.einfuegen_dialoge import BausteinDialog
            BausteinDialog(self.w, self.ed).exec()

    def schnellbaustein(self, k=None):
        if not self.ed:
            return
        from ..storage import bausteine
        m = QMenu()
        liste = bausteine.laden()
        for b in liste:
            m.addAction(b["name"], lambda _=False, b=b: (bausteine.einfuegen(self.ed.textCursor(), b), self.ed.document().setModified(True)))
        if not liste:
            m.addAction("Noch keine Bausteine — Einfügen ▸ Textbaustein").setEnabled(False)
        m.addSeparator()
        m.addAction("Textbausteine verwalten …", self.textbaustein)
        self._popup(m)

    # ---- Bild, Tabelle, Schrift, Seite: der Rest der Werkzeug-Reiter ----------------------------------------------
    def bildFarbe(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from ..editor import einfuegen as E
        modi = ["Original", "Graustufen", "Schwarzweiß", "Sepia", "Heller", "Dunkler"]
        n, ok = QInputDialog.getItem(self.w, "Bildfarbe", "Darstellung:", modi, 0, False)
        if ok:
            if n == "Original":
                E.bild_original(e)
            else:
                E.bild_ersetzen(e, lambda img, n=n: E.farbe_anwenden(img, n))

    def bildZuschneiden(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from ..editor import einfuegen as E
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QSpinBox
        d = QDialog(self.w); d.setWindowTitle("Bild zuschneiden")
        form = QFormLayout(d)
        sp = {}
        for name in ("Links", "Oben", "Rechts", "Unten"):
            w = QSpinBox(); w.setRange(0, 5000); w.setSuffix(" px"); sp[name] = w; form.addRow(name + " abschneiden", w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(d.accept); bb.rejected.connect(d.reject)
        form.addRow(bb)
        if d.exec():
            E.bild_ersetzen(e, lambda img: E.zuschneiden(img, sp["Links"].value(), sp["Oben"].value(), sp["Rechts"].value(), sp["Unten"].value()))

    def objektDrehen(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from ..editor import einfuegen as E
        namen = {"90° nach rechts": "rechts", "90° nach links": "links", "Horizontal spiegeln": "horizontal", "Vertikal spiegeln": "vertikal"}
        n, ok = QInputDialog.getItem(self.w, "Drehen", "Bild:", list(namen), 0, False)
        if ok:
            E.bild_ersetzen(e, lambda img: E.drehen(img, namen[n]))

    def objektAusrichten(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        namen = {"Links": Qt.AlignLeft, "Zentriert": Qt.AlignHCenter, "Rechts": Qt.AlignRight}
        n, ok = QInputDialog.getItem(self.w, "Ausrichten", "Bild im Text:", list(namen), 0, False)
        if ok:
            e.set_alignment(namen[n])

    def abschnittsumbruch(self, k=None, art="NextPage"):
        if not self.ed:
            return
        if art == "NextPage":
            self.ed.insert_page_break()
        else:
            self.w.statusBar().showMessage("Abschnitte kennt die native Fassung nicht — nur „Nächste Seite“ (Seitenumbruch) ist möglich.", 6000)

    def schriftartMehr(self, k=None):
        if not self.ed:
            return
        from PySide6.QtWidgets import QFontDialog
        cf = self._fmt()
        start = cf.font() if cf.fontFamilies() else self.ed.document().defaultFont()      # (cf.fontFamily() stürzt in PySide ab)
        ok, font = QFontDialog.getFont(start, self.w, "Schriftart")
        if ok:
            f = QTextCharFormat()
            f.setFontFamilies([font.family()]); f.setFontPointSize(font.pointSizeF())
            f.setFontWeight(font.weight()); f.setFontItalic(font.italic())
            f.setFontStrikeOut(font.strikeOut())
            f.setUnderlineStyle(QTextCharFormat.SingleUnderline if font.underline() else QTextCharFormat.NoUnderline)
            self.ed._merge(f)

    def papierformatFenster(self, k=None): self.w.page_setup()
    def fusszeileBearbeiten(self, k=None): self.w.edit_header_footer(False)

    def kopfFussSchliessen(self, k=None):
        self.w.statusBar().showMessage("Kopf- und Fußzeile werden über Dialoge bearbeitet — es gibt nichts zu schließen.", 4000)

    def ersteSeiteAnders(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        pg = t.page.copy()
        pg.diff_first = not pg.diff_first
        if pg.diff_first and pg.first_header.is_empty() and pg.first_footer.is_empty():
            pg.first_header = HeaderFooter(); pg.first_footer = HeaderFooter()
        t.editor.page_settings_changed(pg)

    def an_ersteSeiteAnders(self):
        t = self.w.current_tab()
        return bool(t and t.page.diff_first)

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
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(d.accept); bb.rejected.connect(d.reject)
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

    # ---- Datei: Vorlagen, Schutz, Bildexport ---------------------------------------------------------------------
    def neuAusVorlage(self, k=None): self.w.neu_aus_vorlage()
    def vorlagenDurchsuchen(self, k=None): self.w.neu_aus_vorlage()

    def dokumentSchuetzen(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        wahl = ["Kennwort zum Öffnen setzen / ändern …", "Kennwort entfernen", "Bearbeitung sperren / freigeben"]
        n, ok = QInputDialog.getItem(self.w, "Dokument schützen", "Was soll geschehen?", wahl, 0, False)
        if not ok:
            return
        if n == wahl[2]:
            self.w.toggle_sperre()
        elif n == wahl[1]:
            t.meta.pop("kennwort", None); t.editor.document().setModified(True)
            self.w.statusBar().showMessage("Kennwort entfernt — gilt ab dem nächsten Speichern.", 5000)
        else:
            a, ok = QInputDialog.getText(self.w, "Kennwort", "Neues Kennwort:", QLineEdit.Password)
            if ok and a:
                b, ok = QInputDialog.getText(self.w, "Kennwort", "Zur Bestätigung noch einmal:", QLineEdit.Password)
                if ok and a == b:
                    t.meta["kennwort"] = a; t.editor.document().setModified(True)
                    self.w.statusBar().showMessage("Das Dokument wird beim Speichern verschlüsselt (DOCX).", 5000)
                elif ok:
                    QMessageBox.information(self.w, "Kennwort", "Die Eingaben stimmen nicht überein.")

    def exportierenPng(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        import os
        from ..editor.pagination import paginated_copy, seite_als_bild
        pfad, _ = QFileDialog.getSaveFileName(self.w, "Als Bild exportieren", os.path.splitext(t.title)[0] + ".png", "PNG-Bild (*.png)")
        if not pfad:
            return
        basis, _e = os.path.splitext(pfad)
        d = paginated_copy(t.editor.document(), t.page, t.editor.noten)
        n = max(1, d.pageCount())
        for i in range(1, n + 1):
            img = seite_als_bild(t.editor.document(), t.page, i, 1.5, d)
            img.save(basis + (f"-{i}" if n > 1 else "") + ".png", "PNG")
        self.w.statusBar().showMessage(f"{n} Seite{'n' if n != 1 else ''} als PNG gespeichert: {basis}…", 6000)

    # ---- KI: eigene Assistenten ----------------------------------------------------------------------------------------
    def w_assistentErstellen(self, k=None):
        from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit as _LE, QPlainTextEdit
        d = QDialog(self.w); d.setWindowTitle("Eigenen Assistenten erstellen")
        form = QFormLayout(d)
        name = _LE(); prompt = QPlainTextEdit(); prompt.setPlaceholderText("Was soll die KI mit dem Text tun? z. B. „Prüfe die genannten Fakten und nenne Zweifel.“")
        modus = QComboBox(); modus.addItems(["Ergebnis als Karte zeigen (hinweis)", "Text ersetzen (ersetzen)"])
        for lab, w in (("Name", name), ("Anweisung", prompt), ("Wirkung", modus)):
            form.addRow(lab, w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(d.accept); bb.rejected.connect(d.reject)
        form.addRow(bb)
        if d.exec() and name.text().strip() and prompt.toPlainText().strip():
            self.w.ki.konfig.assistent_hinzufuegen(name.text(), prompt.toPlainText(), "ersetzen" if modus.currentIndex() == 1 else "hinweis")
            self.w.statusBar().showMessage(f"Assistent „{name.text().strip()}“ angelegt (KI ▸ Eigene Assistenten).", 5000)

    def menue_assistenten(self):
        m = QMenu()

        def fuellen():
            m.clear()
            liste = self.w.ki.konfig["assistenten"]
            for a in liste:
                m.addAction(a["name"], lambda _=False, a=a: self.w.ki.assistent(a))
            if not liste:
                m.addAction("Noch keine eigenen Assistenten").setEnabled(False)
            m.addSeparator()
            m.addAction("Neuen Assistenten erstellen …", self.w_assistentErstellen)
            if liste:
                entf = m.addMenu("Assistenten entfernen")
                for a in liste:
                    entf.addAction(a["name"], lambda _=False, a=a: self.w.ki.konfig.assistent_entfernen(a["id"]))
        m.aboutToShow.connect(fuellen)
        fuellen()
        return m

    # ---- Sendungen --------------------------------------------------------------------------------------------
    def _neues_blatt(self, titel: str):
        self.w.new_document()
        t = self.w.current_tab()
        t.title = titel
        self.w._update_tab_titles()
        return t

    def umschlag(self, k=None):
        from ..editor import sendungen as S
        from ..widgets.sendungen_dialoge import UmschlagDialog
        b = self.w.benutzerdaten()
        absender = "\n".join(x for x in (b["name"], b["strasse"], b["plz_ort"]) if x)
        d = UmschlagDialog(self.w, absender)
        if d.exec():
            t = self._neues_blatt("Umschlag")
            pg = S.umschlag_aufbauen(t.editor, d.format.currentText(), d.absender.toPlainText(), d.empfaenger.toPlainText())
            t.editor.page_settings_changed(pg)
            self.w.statusBar().showMessage(f"Umschlag im Format {d.format.currentText()} angelegt.", 5000)

    def etiketten(self, k=None):
        from ..editor import sendungen as S
        from ..widgets.sendungen_dialoge import EtikettenDialog
        d = EtikettenDialog(self.w)
        if d.exec():
            t = self._neues_blatt("Etiketten")
            pg = S.etiketten_aufbauen(t.editor, d.bogen.currentText(), d.text.toPlainText(), d.gleich.currentIndex() == 0)
            t.editor.page_settings_changed(pg)
            self.w.statusBar().showMessage("Bogen angelegt.", 5000)

    def seriendruckfeld(self, k=None):
        if self.ed:
            from ..editor import sendungen as S
            n, ok = QInputDialog.getText(self.w, "Seriendruckfeld", "Feldname (muss in der Kopfzeile der Empfängerliste stehen):", text="Name")
            if ok and n.strip():
                S.feld_einfuegen(self.ed, n.strip().replace("{", "").replace("}", ""))

    def adressblock(self, k=None):
        if self.ed:
            from ..editor import sendungen as S
            namen = {"Adressblock (Name, Straße, Ort)": "adresse", "Grußzeile (Anrede + Name)": "gruss", "Adressblock und Grußzeile": "beides"}
            n, ok = QInputDialog.getItem(self.w, "Adressblock und Grußzeile", "Einfügen:", list(namen), 0, False)
            if ok:
                S.adressblock_einfuegen(self.ed, namen[n])

    def seriendruckregel(self, k=None):
        if self.ed:
            from ..editor import sendungen as S
            from ..widgets.sendungen_dialoge import RegelDialog
            d = RegelDialog(self.w)
            if d.exec() and d.feld.text().strip():
                S.regel_einfuegen(self.ed, d.feld.text().strip(), d.wert.text().strip(), d.dann.text(), d.sonst.text())

    def seriendruck(self, k=None):
        if not self.ed:
            return
        from ..editor import sendungen as S
        from ..widgets.sendungen_dialoge import SeriendruckDialog
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
        from ..editor import sendungen as S
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

    def formTextfeld(self, k=None):
        if self.ed:
            from ..editor import sendungen as S
            S.form_textfeld(self.ed)

    def formKasten(self, k=None):
        if self.ed:
            from ..editor import sendungen as S
            S.form_kasten(self.ed)

    def formKnopf(self, k=None):
        if self.ed:
            from ..editor import sendungen as S
            t, ok = QInputDialog.getText(self.w, "Schaltfläche", "Aufschrift:", text="Absenden")
            if ok:
                S.form_knopf(self.ed, t.strip())

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
        from ..services.barrierefreiheit import pruefe
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
            kennung = self.SPRACHEN[namen.index(n)][0]
            self.w.current_tab().meta["sprache"] = kennung
            self.w.settings.set("pruefsprache", kennung)
            self.ed.document().setModified(True)
            self.w.statusBar().showMessage(f"Dokumentsprache: {n}.", 4000)

    # ---- Verweise: Beschriftungen, Textmarken, Querverweise, Index, Zitate -------------------------------------
    def beschriftung(self, k=None):
        if not self.ed:
            return
        from ..editor import verweise
        from ..widgets.verweise_dialoge import BeschriftungDialog
        d = BeschriftungDialog(self.w)
        if d.exec():
            verweise.beschriftung_einfuegen(self.ed, d.label.currentText(), d.text.text().strip(), oben=d.pos.currentIndex() == 1)

    def _verzeichnis(self, art, titel, leer):
        if not self.ed:
            return
        from ..editor.verzeichnis import verzeichnis_einfuegen
        if verzeichnis_einfuegen(self.ed, art) == 0:
            QMessageBox.information(self.w, titel, leer)

    def abbildungsverzeichnis(self, k=None):
        self._verzeichnis("abb", "Abbildungsverzeichnis", "Es gibt keine Beschriftungen „Abbildung“. Fügen Sie sie über Verweise ▸ Beschriftung ein.")

    def stichwortverzeichnis(self, k=None):
        self._verzeichnis("index", "Stichwortverzeichnis", "Es sind keine Stichwörter markiert. Verwenden Sie Verweise ▸ Indexeintrag.")

    def literaturverzeichnis(self, k=None):
        self._verzeichnis("lit", "Literaturverzeichnis", "Es sind keine Quellen angelegt (Verweise ▸ Neue Quelle).")

    def textmarke(self, k=None):
        if self.ed:
            from ..widgets.verweise_dialoge import TextmarkeDialog
            TextmarkeDialog(self.w, self.ed).exec()

    def querverweis(self, k=None):
        if not self.ed:
            return
        from ..editor import verweise
        from ..widgets.verweise_dialoge import QuerverweisDialog
        d = QuerverweisDialog(self.w, self.ed)
        if d.exec():
            ziel, wie = d.ergebnis()
            if ziel:
                verweise.querverweis_einfuegen(self.ed, ziel, wie)

    def indexEintrag(self, k=None):
        if not self.ed:
            return
        from ..editor import verweise
        c = self.ed.textCursor()
        vorschlag = c.selectedText() if c.hasSelection() else ""
        t, ok = QInputDialog.getText(self.w, "Indexeintrag", "Stichwort:", text=vorschlag)
        if ok and t.strip() and not verweise.index_markieren(self.ed, t.strip()):
            self.w.statusBar().showMessage("Bitte Text markieren oder in ein Wort klicken.", 4000)

    def quelleNeu(self, k=None):
        if not self.ed:
            return
        from ..editor import verweise
        from ..widgets.verweise_dialoge import QuelleDialog
        d = QuelleDialog(self.w)
        if d.exec():
            q = d.ergebnis(); q["tag"] = verweise.quelle_tag(self.ed.quellen, q)
            self.ed.quellen.append(q); self.ed.document().setModified(True)

    def quellenVerwalten(self, k=None):
        if self.ed:
            from ..widgets.verweise_dialoge import QuellenDialog
            QuellenDialog(self.w, self.ed).exec()

    def zitat(self, k=None):
        if not self.ed:
            return
        from ..editor import verweise
        from ..editor.literatur import eintrag
        if not self.ed.quellen:
            QMessageBox.information(self.w, "Zitat", "Es sind noch keine Quellen angelegt. Verwenden Sie „Neue Quelle“.")
            return
        namen = [eintrag(q, self.ed.zitierweise) for q in self.ed.quellen]
        n, ok = QInputDialog.getItem(self.w, "Zitat einfügen", "Quelle:", namen, 0, False)
        if ok:
            verweise.zitat_einfuegen(self.ed, self.ed.quellen[namen.index(n)])

    def zitierweise(self, k=None):
        if not self.ed:
            return
        from ..editor.literatur import ZITIERWEISEN
        n, ok = QInputDialog.getItem(self.w, "Zitierweise", "Zitierweise:", ZITIERWEISEN, ZITIERWEISEN.index(self.ed.zitierweise) if self.ed.zitierweise in ZITIERWEISEN else 0, False)
        if ok:
            self.ed.zitierweise = n
            self.ed._meta["zitierweise"] = n
            self.ed.document().setModified(True)

    # ---- Kommentare, Noten, Änderungen ---------------------------------------------------------------
    def _text_abfragen(self, titel, frage, vorgabe=""):
        t, ok = QInputDialog.getMultiLineText(self.w, titel, frage, vorgabe)
        return t.strip() if ok and t.strip() else None

    def kommentar(self, k=None):
        if self.ed and (t := self._text_abfragen("Neuer Kommentar", "Kommentar:")):
            if self.ed.kommentar_neu(t) is None:
                self.w.statusBar().showMessage("Zum Kommentieren Text markieren oder in ein Wort klicken.", 4000)
            else:
                self.w.zeige_navigation("kommentare")

    def kommentarWeiter(self, k=None):
        if self.ed: self.ed.kommentar_springen(1)

    def kommentarZurueck(self, k=None):
        if self.ed: self.ed.kommentar_springen(-1)

    def kommentarWeg(self, k=None):
        if self.ed and (kid := self.ed.kommentar_am_cursor()) is not None:
            self.ed.kommentar_loeschen(kid)
        else:
            self.w.statusBar().showMessage("Der Zeiger steht in keinem Kommentar.", 4000)

    def kommentareAlleWeg(self, k=None):
        if self.ed and self.ed.kommentare and QMessageBox.question(
                self.w, "Kommentare", "Alle Kommentare im Dokument löschen?") == QMessageBox.Yes:
            self.ed.kommentare_alle_loeschen()

    def _note(self, art, titel):
        if self.ed and (t := self._text_abfragen(titel, "Text der Note:")):
            self.ed.note_neu(art, t)

    def fussnote(self, k=None): self._note("f", "Fußnote einfügen")
    def endnote(self, k=None): self._note("e", "Endnote einfügen")
    def noteWeiter(self, k=None):
        if self.ed: self.ed.note_springen(1)

    def noteZurueck(self, k=None):
        if self.ed: self.ed.note_springen(-1)

    def notenZeigen(self, k=None): self.w.zeige_navigation("noten")

    def note_bearbeiten(self, art, nid):
        if self.ed and (t := self._text_abfragen("Note bearbeiten", "Text der Note:", self.ed.noten[art].get(nid, ""))):
            self.ed.noten[art][nid] = t
            self.ed.document().setModified(True)
            self.w.navigation.aktualisieren()

    def verfolgen(self, k=None):
        if self.ed:
            self.ed.set_verfolgen(not self.ed.verfolgen)
            self.w.statusBar().showMessage("Änderungen werden verfolgt." if self.ed.verfolgen else "Verfolgung beendet.", 3000)

    def an_verfolgen(self): return bool(self.ed and self.ed.verfolgen)

    def markupUmschalten(self, k=None):
        if self.ed: self.ed.set_markup(not self.ed.markup)

    def an_markupUmschalten(self): return bool(self.ed and self.ed.markup)
    def ueberarbeitungsbereich(self, k=None): self.w.zeige_navigation("aenderungen")

    def aenderungAnnehmen(self, k=None): self._aend_am_cursor(True)
    def aenderungAblehnen(self, k=None): self._aend_am_cursor(False)

    def _aend_am_cursor(self, annehmen):
        if not self.ed:
            return
        b = self.ed.aenderung_am_cursor() or self.ed.aenderung_springen(1)
        if b:
            self.ed.aenderung_annehmen(b, annehmen)
            self.ed.aenderung_springen(1)

    def aenderungWeiter(self, k=None):
        if self.ed: self.ed.aenderung_springen(1)

    def aenderungZurueck(self, k=None):
        if self.ed: self.ed.aenderung_springen(-1)

    def aenderungenUebernehmen(self, k=None):
        if self.ed: self.w.statusBar().showMessage(f"{self.ed.alle_aenderungen(True)} Änderungen angenommen.", 4000)

    def aenderungenVerwerfen(self, k=None):
        if self.ed: self.w.statusBar().showMessage(f"{self.ed.alle_aenderungen(False)} Änderungen abgelehnt.", 4000)

    # ---- Fenster ---------------------------------------------------------------------------
    def neuesFenster(self, k=None): self.w.neues_fenster()
    def fensterNebeneinander(self, k=None): self.w.fenster_anordnen("nebeneinander")
    def fensterUntereinander(self, k=None): self.w.fenster_anordnen("untereinander")
    def fensterKacheln(self, k=None): self.w.fenster_anordnen("kacheln")

    def fensterListe(self, k=None):
        self._popup(self.w.fensterliste_menue())

    # ---- Dokumentansichten ----------------------------------------------------------------
    def w_setzeLayout(self, k=None, art="blatt"):
        t = self.w.current_tab()
        if t:
            if art != "blatt" and t.editor.gliederung:
                self.gliederung()
            t.set_layout(art)
            self.w.band.aktualisieren(True)

    def w_layoutJetzt(self, k=None):
        t = self.w.current_tab()
        return t.layout_art if t else "blatt"

    def gliederung(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        if t.layout_art != "blatt":
            t.set_layout("blatt")
        t.editor.set_gliederung(not t.editor.gliederung)
        self.w.statusBar().showMessage(
            "Gliederung: nur Überschriften. Alt+Umschalt+←/→ ändert die Ebene." if t.editor.gliederung else "Gliederung beendet.", 5000)

    def an_gliederung(self):
        t = self.w.current_tab()
        return bool(t and t.editor.gliederung)

    # ---- Lineale ---------------------------------------------------------------------------
    def linealZeigen(self, k=None):
        self.w.settings.set("ansicht/lineal", not self.w.settings.get_bool("ansicht/lineal", False))
        self.w.lineale_anwenden()

    def linealHochZeigen(self, k=None):
        self.w.settings.set("ansicht/lineal_hoch", not self.w.settings.get_bool("ansicht/lineal_hoch", False))
        self.w.lineale_anwenden()

    def an_linealZeigen(self): return self.w.settings.get_bool("ansicht/lineal", False)
    def an_linealHochZeigen(self): return self.w.settings.get_bool("ansicht/lineal_hoch", False)

    # ---- Zoom ---------------------------------------------------------------------------
    def _zoom_um(self, faktor):
        if self.ed:
            self.ed.set_zoom(self.ed.zoom * faktor)

    def groesser(self, k=None): self._zoom_um(1.1)
    def kleiner(self, k=None): self._zoom_um(1 / 1.1)

    def normal(self, k=None):
        if self.ed:
            self.ed.set_zoom(1.0)

    def zoomBreite(self, k=None):
        t = self.w.current_tab()
        if t:
            t.zoom_breite()

    def zoomSeite(self, k=None):
        t = self.w.current_tab()
        if t:
            t.zoom_seite()

    def zoomStufe(self, k=None):
        if not self.ed:
            return
        from ..widgets.dialogs import ZoomDialog
        d = ZoomDialog(self.w, self.ed.zoom)
        if d.exec():
            art, wert = d.ergebnis()
            if art == "breite":
                self.zoomBreite()
            elif art == "seite":
                self.zoomSeite()
            else:
                self.ed.set_zoom(wert)

    def lesehilfe(self, k=None):
        from ..widgets.lesehilfe_dialog import LesehilfeDialog
        d = LesehilfeDialog(self.w)
        d.show()
        self._lh = d

    # ==== Ansicht ==========================================================================================================================
    def markenZeigen(self, k=None):
        if self.ed:
            self.w.set_marken(not self.ed.marken)

    def an_markenZeigen(self): return bool(self.ed) and self.ed.marken

    def navigation(self, k=None):
        self.w.toggle_navigation()

    def an_navigation(self): return self.w.navigation.isVisible()

    # ==== Datei (Reiter) =======================================================================================================
    def kopieSpeichern(self, k=None): self.w.save_copy()
    def exportierenDocx(self, k=None): self.w.export_as(".docx")
    def exportierenOdt(self, k=None): self.w.export_as(".odt")
    def exportierenTxt(self, k=None): self.w.export_as(".txt")
    def druckerWaehlen(self, k=None): self.w.print_dialog()

    def menue_zuletzt(self):
        m = QMenu()
        items = self.w.settings.recent()
        if not items:
            m.addAction("(keine)").setEnabled(False)
        for pfad in items:
            m.addAction(os.path.basename(pfad), lambda _=False, p=pfad: self.w.open_path(p)).setToolTip(pfad)
        return m

    # ==== Tabellentools (Kontext) ===================================================================================================
    def _tab(self):
        e = self.ed
        if not e:
            return None, None, None
        c = e.textCursor()
        t = c.currentTable()
        return (e, c, t) if t else (e, c, None)

    def tabelleZeileOben(self, k=None):
        e, c, t = self._tab()
        if t: t.insertRows(t.cellAt(c).row(), 1)

    def tabelleZeileUnten(self, k=None):
        e, c, t = self._tab()
        if t: t.insertRows(t.cellAt(c).row() + 1, 1)

    def tabelleSpalteLinks(self, k=None):
        e, c, t = self._tab()
        if t: t.insertColumns(t.cellAt(c).column(), 1)

    def tabelleSpalteRechts(self, k=None):
        e, c, t = self._tab()
        if t: t.insertColumns(t.cellAt(c).column() + 1, 1)

    def tabelleZeileLoeschen(self, k=None):
        e, c, t = self._tab()
        if t and t.rows() > 1: t.removeRows(t.cellAt(c).row(), 1)
        elif t: self.tabelleLoeschen()

    def tabelleSpalteLoeschen(self, k=None):
        e, c, t = self._tab()
        if t and t.columns() > 1: t.removeColumns(t.cellAt(c).column(), 1)
        elif t: self.tabelleLoeschen()

    def tabelleLoeschen(self, k=None):
        e, c, t = self._tab()
        if t:
            first = t.firstCursorPosition().position() - 1
            last = t.lastCursorPosition().position() + 1
            cc = QTextCursor(e.document())
            cc.setPosition(max(0, first)); cc.setPosition(min(last, e.document().characterCount() - 1), QTextCursor.KeepAnchor)
            cc.removeSelectedText()

    def tabelleVerbinden(self, k=None):
        e, c, t = self._tab()
        if t and c.hasSelection(): t.mergeCells(c)

    def tabelleTeilen(self, k=None):
        e, c, t = self._tab()
        if t:
            cell = t.cellAt(c)
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:
                t.splitCell(cell.row(), cell.column(), 1, 1)

    def tabelleRahmen(self, k=None):
        e, c, t = self._tab()
        if t:
            f = t.format(); f.setBorder(0 if f.border() > 0 else 0.5); t.setFormat(f)

    def an_tabelleRahmen(self):
        e, c, t = self._tab()
        return bool(t) and t.format().border() > 0

    def menue_tabelleSchattierung(self):
        m = QMenu()
        def setze(col):
            e, c, t = self._tab()
            if t:
                cell = t.cellAt(c)
                f = cell.format()
                f.setBackground(QBrush(col)) if col else f.clearBackground()
                cell.setFormat(f)
        for col in ("#fff3bf", "#d3f9d8", "#d0ebff", "#ffe3e3", "#e9ecef"):
            m.addAction(_farbfeld(col), col, lambda _=False, col=col: setze(QColor(col)))
        m.addAction("Keine Schattierung", lambda: setze(None))
        return m

    def _zelle_ausrichten(self, wo):
        e, c, t = self._tab()
        if t:
            cell = t.cellAt(c)
            f = cell.format().toTableCellFormat()
            f.setVerticalAlignment(wo)
            cell.setFormat(f)

    def zelleOben(self, k=None): self._zelle_ausrichten(QTextCharFormat.AlignTop)
    def zelleMitte(self, k=None): self._zelle_ausrichten(QTextCharFormat.AlignMiddle)
    def zelleUnten(self, k=None): self._zelle_ausrichten(QTextCharFormat.AlignBottom)

    # ==== Bildtools (Kontext) =========================================================================================================
    def _bild(self):
        e = self.ed
        if not e:
            return None, None
        f = e.bild_format()
        return (e, f) if f is not None else (e, None)

    def bildGroesse(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from ..widgets.dialogs import BildGroesseDialog
        d = BildGroesseDialog(f.width(), f.height(), self.w)
        if d.exec():
            e.bild_setzen(width=d.breite_px(), height=d.hoehe_px())

    def bildBreite(self, k=None):
        e, f = self._bild()
        if f is not None and f.width():
            r = f.height() / f.width()
            b = e.page.content_width_px
            e.bild_setzen(width=b, height=b * r)

    def anordnen(self, k=None):
        """Textumbruch / Position: Bild mit Text in der Zeile oder links/rechts vom Text umflossen."""
        e, f = self._bild()
        if f is None:
            self.w.statusBar().showMessage("Erst ein Bild anklicken.", 4000)
            return
        from ..editor import umbruch as U
        aktuell = U.schwebend(e.document(), e._bild_cursor().selectionStart()) or "zeile"
        m = QMenu()
        for modus, text in (("zeile", "Mit Text in Zeile"), ("links", "Links, Text umfließt"), ("rechts", "Rechts, Text umfließt")):
            a = m.addAction(text, lambda _=False, modus=modus: U.umbruch_setzen(e, modus))
            a.setCheckable(True)
            a.setChecked(modus == aktuell)
        self._popup(m)

    def bildOriginal(self, k=None):
        e, f = self._bild()
        if f is not None:
            img = e.document().resource(2, QUrl(f.name()))
            if img is not None and not img.isNull():
                e.bild_setzen(width=img.width(), height=img.height())

    def bildAltText(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        akt = f.property(0x100000 + 0x101 + 1) if f.hasProperty(0x100000 + 0x101 + 1) else ""
        t, ok = QInputDialog.getText(self.w, "Alternativtext", "Beschreibung des Bildes:", text=akt or "")
        if ok:
            e.bild_setzen(alt=t)

    def bildEntfernen(self, k=None):
        e, f = self._bild()
        if f is not None:
            e.textCursor().removeSelectedText()

    def exportierenRtf(self, k=None): self.w.export_as(".rtf")
    def exportierenDoc(self, k=None): self.w.export_as(".doc")

    # ==== Vorlesen ==================================================================================================
    def vorlesen(self, k=None):
        self.w.vorlesen(ab_hier=False)

    def vorlesenAbSatz(self, k=None):
        self.w.vorlesen(ab_hier=True)

    def vorlesenStopp(self, k=None):
        from ..services import vorlesen as v
        v.beenden()
        self.w.lbl_msg.setText("Vorlesen angehalten.")

    def stimmeWaehlen(self, k=None):
        self.w.stimme_waehlen()

    # ==== KI ========================================================================================================
    def kiKorrektur(self, k=None): self.w.ki.korrigieren()
    def kiVorschlaege(self, k=None):
        self.w.sidebar.zeige_bereich(0); self.w.ki.vorschlaege_holen()
    def kiUmformulieren(self, k=None): self.w.ki.text_aktion("umformulieren")
    def kiZusammenfassen(self, k=None):
        self.w.sidebar.zeige_bereich(0); self.w.ki.zusammenfassen()
    def w_kiUebersetzen(self, k=None): self.w.ki.uebersetzen()
    def kiEntwerfen(self, k=None): self.w.chat_oeffnen("Entwirf einen Text zu folgendem Anliegen: ")
    def w_chatUmschalten(self, k=None): self.w.chat_oeffnen("")
    def w_kiKonfiguration(self, k=None):
        from ..widgets.ki_dialoge import KIKonfigurationDialog
        KIKonfigurationDialog(self.w).exec()

    def w_eigenenAnbieterHinzufuegen(self, k=None):
        from ..widgets.ki_dialoge import AnbieterDialog
        if AnbieterDialog(self.w, self.w.ki.konfig).exec():
            self.w.ki.geaendert.emit()

    def kiTextInBild(self, k=None): self.w.ki.bild_aus_text()
    def kiTextAktion(self, k=None, aktion="verbessern"): self.w.ki.text_aktion(aktion)

    # ==== Externe Programme (Steuerung einer installierten Anwendung, keine Integration) ==========================
    def _extern(self, fn, name):
        t = self.w.current_tab()
        if not t:
            return
        if not t.path or t.is_modified():
            QMessageBox.information(self.w, name, "Bitte das Dokument zuerst speichern.")
            return
        if not fn(t.path):
            QMessageBox.information(self.w, name, f"{name} ist auf diesem Rechner nicht installiert.")

    def mitWpsOeffnen(self, k=None):
        from ..integrations import wps
        self._extern(wps.oeffnen, "WPS Writer")

    def mitLibreOfficeOeffnen(self, k=None):
        from ..integrations import wps
        self._extern(wps.mit_libreoffice_oeffnen, "LibreOffice")
