"""Befehle des Bandes: Aktionsname aus register.json → Funktion.

Ein Name, den es hier nicht gibt, bleibt im Band sichtbar, aber ausgegraut — mit dem Hinweis,
dass er in der nativen Fassung noch fehlt. So entsteht die Liste dessen, was noch zu tun ist,
von selbst (siehe `fehlende()`), und nichts steht als Attrappe da.

Konvention: Methode `name(self, knopf=None)`; `w.xyz` heißt `w_xyz`.
Zustand eines Schalters: Methode `an_name(self) -> bool`.
Klappe (Pfeilmenü): Methode `menue_name(self) -> QMenu`.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap, QTextCharFormat, QTextListFormat
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

    def hat(self, name: str) -> bool:
        return callable(getattr(self, name.replace(".", "_"), None))

    def tun(self, name: str, knopf=None):
        f = getattr(self, name.replace(".", "_"), None)
        if callable(f):
            return f(knopf)

    def zustand(self, name: str):
        f = getattr(self, "an_" + name.replace(".", "_"), None)
        return bool(f()) if callable(f) else None

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

    def leereSeite(self, k=None):
        if self.ed:
            self.ed.insert_page_break(); self.ed.insert_page_break()

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

    gruendlichPruefen = w_pruefen

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
