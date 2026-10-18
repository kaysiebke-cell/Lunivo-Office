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
from PySide6.QtGui import QBrush, QColor, QCursor, QIcon, QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import QApplication, QColorDialog, QInputDialog, QMenu, QMessageBox

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

    def an_unter(self): return self._fmt().fontUnderline()

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
    def suchen(self, k=None):
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

    def datumUhrzeit(self, k=None):
        self.w.insert_date()

    # ---- Seitenlayout --------------------------------------------------------------------------------------------------
    def seitenraenderRahmen(self, k=None):
        self.w.page_setup()

    # ---- Überprüfen / Schreibhilfe --------------------------------------------------------------------------------------------
    def woerterZaehlen(self, k=None):
        self.w.word_count()

    def rechtschreibung(self, k=None):
        self.w.assistant.pruefen()

    def w_pruefen(self, k=None):
        self.w.assistant.pruefen()

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

    def w_optionenOeffnen(self, k=None):
        self.w.show_options()

    # ---- Ansicht ---------------------------------------------------------------------------------------------------------------
    def menueleisteZeigen(self, k=None):
        self.w.toggle_menubar()

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

    def seitenraender(self, k=None): self.w.page_setup()
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
        m.exec(QCursor.pos())

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

    # ---- Fenster ---------------------------------------------------------------------------
    def neuesFenster(self, k=None): self.w.neues_fenster()
    def fensterNebeneinander(self, k=None): self.w.fenster_anordnen("nebeneinander")
    def fensterUntereinander(self, k=None): self.w.fenster_anordnen("untereinander")
    def fensterKacheln(self, k=None): self.w.fenster_anordnen("kacheln")

    def fensterListe(self, k=None):
        self.w.fensterliste_menue().exec(QCursor.pos())

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
    def w_kiKonfiguration(self, k=None): self.w.show_options("ki")
    def w_eigenenAnbieterHinzufuegen(self, k=None): self.w.show_options("ki")
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
