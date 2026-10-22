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

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QIcon, QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat
from lunivo_writer.models.page import HeaderFooter
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QLineEdit, QMenu, QMessageBox

from lunivo_writer.editor.linie import Linie
from lunivo_writer.ui.baukasten import FarbPalette, RahmenMenue, RasterAuswahl, ZellenRaster, farb_symbol, liste_zeichner, weitere_farben

_farbfeld = farb_symbol


class FreiMenue:
    """Die Menüs des Reiters Zeichentools: dieselben Baukasten-Menüs wie neben dem Bild, wirken aber auf den Editor, der bei der Wahl aktuell ist."""

    @staticmethod
    def formstile(cmd):
        from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin as F
        return F.frei_formstile_menue(None, None, lambda: cmd.ed)

    @staticmethod
    def fuell(cmd):
        from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin as F
        return F.frei_fuell_menue(None, None, lambda: cmd.ed)

    @staticmethod
    def kontur(cmd):
        from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin as F
        return F.frei_kontur_menue(None, None, lambda: cmd.ed)


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

    def inhalteEinfuegen(self, k=None):
        """„Inhalte einfügen …“: aus den Formaten der Zwischenablage eines wählen (mit Formatierung, nur Text, Bild)."""
        if not self.ed:
            return
        from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QListWidget, QVBoxLayout, QLabel
        md = QApplication.clipboard().mimeData()
        optionen = []
        if md.hasText() or md.hasUrls() or md.formats():
            optionen.append(("Mit Formatierung", "formatiert"))
        if md.hasText():
            optionen.append(("Unformatierter Text", "text"))
        if md.hasImage():
            optionen.append(("Bild", "bild"))
        if not optionen:
            return
        d = QDialog(self.w); d.setWindowTitle("Inhalte einfügen"); d.resize(320, 220)
        v = QVBoxLayout(d); v.addWidget(QLabel("Als:"))
        liste = QListWidget(); v.addWidget(liste, 1)
        for text, art in optionen:
            liste.addItem(text); liste.item(liste.count() - 1).setData(0x100, art)
        liste.setCurrentRow(0); liste.itemDoubleClicked.connect(lambda _: d.accept())
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(d.accept); bb.rejected.connect(d.reject); v.addWidget(bb)
        if not d.exec() or liste.currentItem() is None:
            return
        art = liste.currentItem().data(0x100)
        if art == "text":
            self.w.paste_plain()
        elif art == "bild":
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QTextDocument, QTextImageFormat
            img = QApplication.clipboard().image()
            name = f"einfuegen-{id(img)}"
            self.ed.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
            f = QTextImageFormat(); f.setName(name); f.setWidth(min(img.width(), 480)); f.setHeight(img.height() * min(img.width(), 480) / max(1, img.width()))
            self.ed.textCursor().insertImage(f)
        else:
            self.ed.paste()

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
        if self.ed: self.ed.set_text_color(QColor(getattr(self, "_schriftfarbe", "#c92a2a")))

    def menue_schriftfarbeKlappe(self):
        def setze(c):
            self._schriftfarbe = c.name() if c else "#000000"
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

    _LISTENARTEN = {
        "disc": ("Punkt", "bullet", QTextListFormat.ListDisc, "disc"), "circle": ("Kreis", "bullet", QTextListFormat.ListCircle, "circle"),
        "square": ("Quadrat", "bullet", QTextListFormat.ListSquare, "square"),
        "dezimal": ("1. 2. 3.", "number", QTextListFormat.ListDecimal, "1.|2.|3."),
        "klein": ("a. b. c.", "number", QTextListFormat.ListLowerAlpha, "a.|b.|c."),
        "gross": ("A. B. C.", "number", QTextListFormat.ListUpperAlpha, "A.|B.|C."),
        "roem_klein": ("i. ii. iii.", "number", QTextListFormat.ListLowerRoman, "i.|ii.|iii."),
        "roem_gross": ("I. II. III.", "number", QTextListFormat.ListUpperRoman, "I.|II.|III."),
    }

    def _listenraster(self, art: str, titel: str, schluessel: tuple[str, ...]) -> RasterAuswahl:
        """Bild-Raster für Aufzählungs- bzw. Nummerierungsarten; die gerade benutzte Art ist hervorgehoben."""
        l = self.ed.textCursor().currentList() if self.ed else None
        aktuell = next((k for k in schluessel if l and l.format().style() == self._LISTENARTEN[k][2]), None)
        r = RasterAuswahl(self.w, titel=titel, spalten=3, groesse=QSize(48, 40))
        r.kachel("keine", "Keine", liste_zeichner(None), aktuell=l is None)
        for k in schluessel:
            text, _kind, _stil, marke = self._LISTENARTEN[k]
            r.kachel(k, text, liste_zeichner(marke), aktuell=k == aktuell)
        r.gewaehlt.connect(self._liste_waehlen)
        r.fuss("Weitere Aufzählungszeichen …" if art == "bullet" else "Weitere Nummerierungen …",
               lambda: self.listeDialog("aufzaehlung" if art == "bullet" else "nummerierung"))
        return r

    def _liste_waehlen(self, schluessel: str) -> None:
        if not self.ed:
            return
        if schluessel == "keine":
            self.ed.list_remove()
            return
        _text, kind, stil, _marke = self._LISTENARTEN[schluessel]
        l = self.ed.textCursor().currentList()
        if l and l.format().style() == stil:                 # schon diese Art: nichts umschalten
            return
        self.ed.toggle_list(kind, stil)

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
        return self._listenraster("bullet", "Aufzählungszeichen", ("disc", "circle", "square"))

    def menue_nummerierungKlappe(self):
        return self._listenraster("number", "Nummerierung", ("dezimal", "klein", "gross", "roem_klein", "roem_gross"))

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

    def _jetzt_pruefen(self) -> None:
        """Prüfen (F7): ohne Text eine deutliche Rückmeldung statt einer leeren Seitenleiste."""
        if not self.ed or not self.ed.toPlainText().strip():
            QMessageBox.information(self.w, "Prüfen", "Es steht noch kein Text da, den ich prüfen könnte.")
            return
        self.w.assistant.pruefen(True)

    def rechtschreibung(self, k=None):
        self._jetzt_pruefen()

    def w_pruefen(self, k=None):
        self._jetzt_pruefen()

    def gruendlichPruefen(self, k=None):
        self.w.assistant.gruendlich()

    def wellen(self, k=None):
        """Rote Wellenlinien beim Schreiben an/aus (derselbe Schalter wie „We“ in der Seitenleiste und in „Welche Hilfe wann“)."""
        self.w.assistant.setze("wellen", not self.w.assistant.an("wellen"))

    def an_wellen(self): return self.w.assistant.an("wellen")

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
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.handbuch(self.w).show()

    def tastenHilfe(self, k=None):
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.tastenkuerzel(self.w).show()

    def erweiterungen(self, k=None):
        from lunivo_writer.ui.dialogs import hilfe_dialoge
        hilfe_dialoge.erweiterungen(self.w).show()

    def vorlagenWaehlen(self, k=None): self.w.neu_aus_vorlage()

    def vorlagenOrdner(self, k=None):
        import os
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from lunivo_writer.editor import vorlagen
        o = vorlagen.vorlagenordner(self.w.settings)
        os.makedirs(o, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(o))

    def menueleisteZeigen(self, k=None):
        self.w.toggle_menubar()

    def an_menueleisteZeigen(self): return self.w.menubar_wanted

    def registerAnpassen(self, k=None):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import RegisterAnpassenDialog
        if RegisterAnpassenDialog(self.w, self.w.settings, self.w.band.daten).exec():
            self.w.neu_bauen_band()

    def schnellzugriffAnpassen(self, k=None):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import SchnellzugriffDialog, lade_json
        from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand
        akt = lade_json(self.w.settings, "ui/schnellzugriff", None)
        if akt is None:
            akt = [a for _s, _n, a in RegisterBand.SCHNELL]
        if SchnellzugriffDialog(self.w, self.w.settings, RegisterBand.SCHNELL_ALLE, akt).exec():
            self.w.neu_bauen_band()

    def symbolTauschen(self, k=None, name=None):
        """Symbol austauschen (Ansicht ▸ Oberfläche, Optionen — und Rechtsklick auf einen Knopf, dann mit dessen Symbol)."""
        from PySide6.QtCore import QTimer
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import SymbolTauschenDialog
        d = SymbolTauschenDialog(self.w, self.w.settings, name)
        d.exec()
        if d.geaendert:
            QTimer.singleShot(0, self.w.neu_bauen_band)             # nicht mitten im Klick auf den Knopf, der gerade neu gebaut wird

    def benutzeroberflaeche(self, k=None):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import OberflaecheDialog
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
    def w_speichernAls(self, k=None, ext=".docx"): self.w.save_as_format(ext)
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

    _rahmen_stil = Linie("#000000", 0.75, "einfach")          # Linie, die ein neuer Rahmen aus dem Menü bekommt

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

    # ==== Einfügen ===========================================================================================================
    def leereSeite(self, k=None, quer=False):
        if self.ed:
            self.ed.insert_page_break(); self.ed.insert_page_break()

    def sonderzeichen(self, k=None):
        from lunivo_writer.ui.dialogs.sonderzeichen import SonderzeichenDialog
        e = self.ed
        if e:
            d = SonderzeichenDialog(self.w, lambda z: e.insertPlainText(z))
            d.show()
            self._sz = d

    def inhaltsverzeichnis(self, k=None):
        if self.ed:
            from lunivo_writer.editor.verzeichnis import verzeichnis_einfuegen
            n = verzeichnis_einfuegen(self.ed)
            if not n:
                QMessageBox.information(self.w, "Inhaltsverzeichnis", "Im Dokument gibt es keine Überschriften. "
                                        "Formatieren Sie Überschriften mit den Stilen „Überschrift 1–3“.")

    def verzeichnisseAktualisieren(self, k=None):
        if self.ed:
            from lunivo_writer.editor.verzeichnis import verzeichnis_aktualisieren
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
    def _bild_einfuegen(self, img, alt, art=None, daten=None):
        from lunivo_writer.editor import einfuegen as E
        E.qimage_einfuegen(self.ed, img, alt, art, daten)

    def formenGalerie(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import einfuegen as E
        m = QMenu()
        for f in E.FORMEN:
            m.addAction(f, lambda _=False, f=f: self._bild_einfuegen(E.form_bild(f), f"Form: {f}", "form", {"form": f}))
        m.addSeparator()
        m.addAction("Weitere Formen und Farben …", self.zeichnen)
        self._popup(m)

    def zeichnen(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import FormDialog
            d = FormDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), f"Form: {d.art.currentText()}", "form", d.daten())

    def smartart(self, k=None):
        if self.ed:
            from lunivo_writer.editor import smartart as SA
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import SmartArtDialog
            d = SmartArtDialog(self.w)
            if d.exec():
                SA.einfuegen(self.ed, d.daten())

    def smartartText(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import smartart as SA
        from lunivo_writer.ui.dialogs.einfuegen_dialoge import SmartArtDialog
        daten = SA.daten_der_auswahl(self.ed)
        if daten is None:
            self.w.statusBar().showMessage("Bitte zuerst ein SmartArt-Bild auswählen (Schreibmarke davor oder Bild markieren).", 5000)
            return
        d = SmartArtDialog(self.w, daten)
        if d.exec():
            SA.aendern(self.ed, **d.daten())

    def menue_smartartLayout(self):
        from lunivo_writer.editor import smartart as SA
        m = QMenu()
        for n in SA.LAYOUTS:
            m.addAction(n, lambda _=False, n=n: self.ed and SA.aendern(self.ed, layout=n))
        return m

    def menue_smartartFarben(self):
        from lunivo_writer.editor import smartart as SA
        m = QMenu()
        for n, f in SA.FARBEN.items():
            m.addAction(_farbfeld(f[0]), n, lambda _=False, n=n: self.ed and SA.aendern(self.ed, farben=n))
        return m

    def wordart(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import WordArtDialog
            d = WordArtDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), "WordArt: " + d.text.text(), "wordart", {"text": d.text.text()})

    def diagramm(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import DiagrammDialog
            d = DiagrammDialog(self.w)
            if d.exec():
                self._bild_einfuegen(d.bild(), f"{d.art.currentText()}diagramm: {d.titel.text()}", "diagramm", {"art": d.art.currentText(), "titel": d.titel.text()})

    def piktogramm(self, k=None):
        if self.ed:
            from lunivo_writer.editor import einfuegen as E
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import PiktogrammDialog
            d = PiktogrammDialog(self.w)
            if d.exec():
                n, farbe = d.ergebnis()
                if n:
                    self._bild_einfuegen(E.piktogramm_bild(n, 96, farbe), f"Piktogramm: {n}", "piktogramm", {"name": n, "farbe": farbe})

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
        from lunivo_writer.ui.dialogs.bildschirmfoto import BereichWahl
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
            from lunivo_writer.editor import einfuegen as E
            E.textfeld(self.ed)

    def initiale(self, k=None):
        if self.ed:
            from lunivo_writer.editor import einfuegen as E
            if not E.initiale(self.ed):
                self.w.statusBar().showMessage("Der Absatz ist leer.", 3000)

    def textAusDatei(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.services import file_service as formats
        from lunivo_writer.models.report import DocumentIOError
        from lunivo_writer.editor import einfuegen as E
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
            from lunivo_writer.editor import einfuegen as E
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import FormelDialog
            d = FormelDialog(self.w)
            if d.exec() and d.eingabe.text().strip():
                E.formel_einfuegen(self.ed, d.eingabe.text())

    def schnelltabelle(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import einfuegen as E
        m = QMenu()
        for n in E.SCHNELLTABELLEN:
            m.addAction(n, lambda _=False, n=n: E.schnelltabelle(self.ed, n))
        self._popup(m)

    def deckblatt(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import einfuegen as E
        from lunivo_writer.ui.dialogs.einfuegen_dialoge import DeckblattDialog
        d = DeckblattDialog(self.w, self.w.settings.get("benutzer/name", ""))
        if d.exec():
            E.deckblatt_einfuegen(self.ed, d.vorlage.currentText(), d.titel.text(), d.unter.text(), d.autor.text(), d.datum.text())

    def datumUhrzeit(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import DatumDialog
            d = DatumDialog(self.w)
            if d.exec() and d.ergebnis():
                self.ed.textCursor().insertText(d.ergebnis())
                self.ed.document().setModified(True)

    def textbaustein(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.einfuegen_dialoge import BausteinDialog
            BausteinDialog(self.w, self.ed).exec()

    def textbausteine(self, k=None):
        self.textbaustein()

    def schnellbaustein(self, k=None):
        """F3: steht vor der Schreibmarke ein Kürzel, kommt der Baustein sofort; sonst die Liste aller Bausteine zum Auswählen."""
        if not self.ed:
            return
        from PySide6.QtGui import QTextCursor
        from lunivo_writer.services import bausteine
        c = self.ed.textCursor()
        if not c.hasSelection():
            w = QTextCursor(c); w.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
            b = bausteine.finde_kuerzel(w.selectedText())
            if b is not None:
                w.removeSelectedText(); bausteine.einfuegen(w, b); self.ed.document().setModified(True)
                return
        m = QMenu()
        for titel, liste in (("Eigene", bausteine.laden()), ("Standard", bausteine.standard())):
            if not liste:
                continue
            m.addSection(titel)
            for b in liste:
                m.addAction(b["name"] + (f"   [{b['kuerzel']}]" if b.get("kuerzel") else ""),
                            lambda _=False, b=b: (bausteine.einfuegen(self.ed.textCursor(), b), self.ed.document().setModified(True)))
        m.addSeparator()
        m.addAction("Textbausteine verwalten …", self.textbaustein)
        self._popup(m)

    # ---- Bild, Tabelle, Schrift, Seite: der Rest der Werkzeug-Reiter ----------------------------------------------
    def bildFarbe(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from lunivo_writer.editor import einfuegen as E
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
        from lunivo_writer.editor import einfuegen as E
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
        from lunivo_writer.editor import einfuegen as E
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
        from lunivo_writer.editor.pagination import seiten_bilder
        pfad, _ = QFileDialog.getSaveFileName(self.w, "Als Bild exportieren", os.path.splitext(t.title)[0] + ".png", "PNG-Bild (*.png)")
        if not pfad:
            return
        basis, _e = os.path.splitext(pfad)
        bilder = list(seiten_bilder(t.editor.document(), t.page, t.editor.noten, self.w.ausgabe_ppi() / 96))
        n = len(bilder)
        for i, img, _ps in bilder:
            img.save(basis + (f"-{i}" if n > 1 else "") + ".png", "PNG")
        self.w.statusBar().showMessage(f"{n} Seite{'n' if n != 1 else ''} als PNG gespeichert: {basis}…", 6000)

    # ---- KI: eigene Assistenten ----------------------------------------------------------------------------------------
    def w_assistentErstellen(self, k=None):
        """„Schnelle KI-Aktion erstellen“ — dasselbe wie „Eigenen Assistenten erstellen“: ein Eintrag in der Liste der Assistenten."""
        from lunivo_writer.ui.dialogs.ki_dialoge import SchnelleAktionDialog
        d = SchnelleAktionDialog(self.w)
        if d.exec():
            e = self.w.ki.konfig.assistent_hinzufuegen(*d.werte())
            self.w.ki.geaendert.emit()
            self.w.statusBar().showMessage(f"Aktion „{e['name']}“ angelegt (KI ▸ Eigene Assistenten).", 5000)

    def menue_assistenten(self):
        """Das Menü „KI-Aktionen“: die eigenen Schnellen KI-Aktionen, neue anlegen, entfernen und alle bisherigen Ergebnisse."""
        m = QMenu()

        def fuellen():
            m.clear()
            liste = self.w.ki.konfig["assistenten"]
            for a in liste:
                m.addAction(a["name"], lambda _=False, a=a: self.w.ki.assistent(a))
            if not liste:
                m.addAction("Noch keine eigenen KI-Aktionen").setEnabled(False)
            m.addSeparator()
            m.addAction("Neue Schnelle KI-Aktion …", self.w_assistentErstellen)
            if liste:
                entf = m.addMenu("KI-Aktion entfernen")
                for a in liste:
                    entf.addAction(a["name"], lambda _=False, a=a: (self.w.ki.konfig.assistent_entfernen(a["id"]), self.w.ki.geaendert.emit()))
            m.addSeparator()
            m.addAction("Alle Ergebnisse anzeigen", self.w_kiErgebnisse)
        m.aboutToShow.connect(fuellen)
        fuellen()
        return m

    def menue_silbenTrennungMenue(self):
        """Zur Silbentrennung: wo man die Trennstriche sieht (die Bearbeitungsansicht zeigt sie nicht) und die Einstellungen."""
        m = QMenu()
        m.addAction("Trennstriche in der Druckvorschau ansehen", self.silbentrennungVorschau)
        m.addAction("Einstellungen der Silbentrennung …", lambda: self.w.show_options("sprache"))
        return m

    def silbentrennungVorschau(self, k=None):
        self.tun("vorschau")

    def menue_silbenMenue(self):
        m = QMenu()
        m.addAction("Silben einstellen …", self.silbenEinstellen)
        return m

    # ---- Sendungen --------------------------------------------------------------------------------------------
    # ---- Vergleichen und Zusammenführen ---------------------------------------------------------------------------------------
    def _fassung_laden(self, pfad: str):
        from lunivo_writer.services import file_service as formats
        try:
            return formats.load(pfad).doc
        except Exception as e:                                  # unlesbare Datei: melden, nicht abbrechen
            QMessageBox.warning(self.w, "Datei lesen", f"„{os.path.basename(pfad)}“ lässt sich nicht lesen:\n{e}")
            return None

    def _ergebnis_blatt(self, titel: str, ziel, page):
        from lunivo_writer.editor.sendungen import _ressourcen
        from PySide6.QtGui import QTextDocumentFragment
        t = self._neues_blatt(titel)
        d = t.editor.document()
        _ressourcen(ziel, d)
        d.clear()
        QTextCursor(d).insertFragment(QTextDocumentFragment(ziel))
        t.editor.page_settings_changed(page.copy())
        t.editor.document().setModified(True)
        return t

    def dokumenteVergleichen(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        from lunivo_writer.editor import vergleich as V
        pfad, _ = QFileDialog.getOpenFileName(self.w, "Mit welchem Dokument vergleichen?", self.w.settings.get("last_dir", os.path.expanduser("~")),
                                              "Dokumente (*.docx *.odt *.txt *.md);;Alle Dateien (*)")
        if not pfad:
            return
        andere = self._fassung_laden(pfad)
        if andere is None:
            return
        autor = os.path.splitext(os.path.basename(pfad))[0]
        ziel, st = V.vergleichen(t.editor.document(), andere, autor)
        self._ergebnis_blatt(f"Vergleich — {t.title} ↔ {autor}", ziel, t.page)
        self.w.statusBar().showMessage(
            (f"Vergleich fertig: {st['eingefuegt']} Zeichen eingefügt, {st['geloescht']} gelöscht (Überprüfen ▸ Änderungen: annehmen oder ablehnen)."
             if st["operationen"] else "Die beiden Dokumente haben denselben Text."), 9000)

    def dokumenteZusammenfuehren(self, k=None):
        t = self.w.current_tab()
        if not t:
            return
        from lunivo_writer.editor import vergleich as V
        pfade, _ = QFileDialog.getOpenFileNames(self.w, "Überarbeitete Fassungen auswählen (jede Datei ist ein Autor)",
                                                self.w.settings.get("last_dir", os.path.expanduser("~")),
                                                "Dokumente (*.docx *.odt *.txt *.md);;Alle Dateien (*)")
        fassungen = []
        for p in pfade:
            d = self._fassung_laden(p)
            if d is not None:
                fassungen.append((os.path.splitext(os.path.basename(p))[0], d))
        if not fassungen:
            return
        ziel, st, konflikte = V.zusammenfuehren(t.editor.document(), fassungen)
        self._ergebnis_blatt(f"Zusammenführung — {t.title}", ziel, t.page)
        msg = f"{len(fassungen)} Fassungen zusammengeführt: {st['eingefuegt']} Zeichen eingefügt, {st['geloescht']} gelöscht."
        if konflikte:
            msg += f" {len(konflikte)} Konflikt(e) — die erste Fassung gilt."
            QMessageBox.information(self.w, "Konflikte beim Zusammenführen", "\n".join(konflikte[:30]))
        self.w.statusBar().showMessage(msg, 9000)

    def _neues_blatt(self, titel: str):
        self.w.new_document()
        t = self.w.current_tab()
        t.title = titel
        self.w._update_tab_titles()
        return t

    def umschlag(self, k=None):
        from lunivo_writer.editor import sendungen as S
        from lunivo_writer.ui.dialogs.sendungen_dialoge import UmschlagDialog
        b = self.w.benutzerdaten()
        absender = "\n".join(x for x in (b["name"], b["strasse"], b["plz_ort"]) if x)
        d = UmschlagDialog(self.w, absender)
        if d.exec():
            t = self._neues_blatt("Umschlag")
            pg = S.umschlag_aufbauen(t.editor, d.format.currentText(), d.absender.toPlainText(), d.empfaenger.toPlainText())
            t.editor.page_settings_changed(pg)
            self.w.statusBar().showMessage(f"Umschlag im Format {d.format.currentText()} angelegt.", 5000)

    def etiketten(self, k=None):
        from lunivo_writer.editor import sendungen as S
        from lunivo_writer.ui.dialogs.sendungen_dialoge import EtikettenDialog
        d = EtikettenDialog(self.w)
        if d.exec():
            t = self._neues_blatt("Etiketten")
            pg = S.etiketten_aufbauen(t.editor, d.bogen.currentText(), d.text.toPlainText(), d.gleich.currentIndex() == 0)
            t.editor.page_settings_changed(pg)
            self.w.statusBar().showMessage("Bogen angelegt.", 5000)

    def seriendruckfeld(self, k=None):
        if self.ed:
            from lunivo_writer.editor import sendungen as S
            n, ok = QInputDialog.getText(self.w, "Seriendruckfeld", "Feldname (muss in der Kopfzeile der Empfängerliste stehen):", text="Name")
            if ok and n.strip():
                S.feld_einfuegen(self.ed, n.strip().replace("{", "").replace("}", ""))

    def adressblock(self, k=None):
        if self.ed:
            from lunivo_writer.editor import sendungen as S
            namen = {"Adressblock (Name, Straße, Ort)": "adresse", "Grußzeile (Anrede + Name)": "gruss", "Adressblock und Grußzeile": "beides"}
            n, ok = QInputDialog.getItem(self.w, "Adressblock und Grußzeile", "Einfügen:", list(namen), 0, False)
            if ok:
                S.adressblock_einfuegen(self.ed, namen[n])

    def seriendruckregel(self, k=None):
        if self.ed:
            from lunivo_writer.editor import sendungen as S
            from lunivo_writer.ui.dialogs.sendungen_dialoge import RegelDialog
            d = RegelDialog(self.w)
            if d.exec() and d.feld.text().strip():
                S.regel_einfuegen(self.ed, d.feld.text().strip(), d.wert.text().strip(), d.dann.text(), d.sonst.text())

    def seriendruck(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import sendungen as S
        from lunivo_writer.ui.dialogs.sendungen_dialoge import SeriendruckDialog
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
        from lunivo_writer.editor import sendungen as S
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

    def _form_dialog(self, art: str):
        if not self.ed:
            return
        from lunivo_writer.editor import formular as FO
        from lunivo_writer.ui.dialogs.formular_dialog import FormFeldDialog
        d = FormFeldDialog(self.w, art)
        if d.exec():
            m = d.meta()
            FO.einfuegen(self.ed, m)
            if art == "kasten" and m.get("beschriftung"):
                self.ed.textCursor().insertText(" " + m["beschriftung"])

    def formTextfeld(self, k=None): self._form_dialog("text")
    def formAuswahl(self, k=None): self._form_dialog("auswahl")

    def tabstopps(self, k=None): self.w.tabstopp_dialog()

    def geheZu(self, k=None, art="Seite"):
        if self.ed:
            from lunivo_writer.ui.dialogs.gehe_zu_dialog import GeheZuDialog
            GeheZuDialog(self.w, self.ed, art).exec()

    def vollbild(self, k=None): self.w.a_fullscreen.trigger()
    def an_vollbild(self): return self.w.isFullScreen()
    def formDatum(self, k=None): self._form_dialog("datum")
    def formKasten(self, k=None): self._form_dialog("kasten")
    def formKnopf(self, k=None): self._form_dialog("knopf")

    def formLeeren(self, k=None):
        if self.ed:
            from lunivo_writer.editor import formular as FO
            n = FO.alle_zuruecksetzen(self.ed)
            self.w.statusBar().showMessage(f"{n} Formularfeld{'er' if n != 1 else ''} zurückgesetzt.", 4000)

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
        from lunivo_writer.proofing.barrierefreiheit import pruefe
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
            self.pruefsprache_setzen(self.SPRACHEN[namen.index(n)][0])

    def pruefsprache_aktuell(self) -> str:
        t = self.w.current_tab()
        return (t.meta.get("sprache") if t is not None else "") or self.w.settings.get("pruefsprache", "de-DE")

    def pruefsprache_setzen(self, kennung: str) -> None:
        """Die Sprache des Dokuments für die Korrekturhilfen (wird in der Datei vermerkt) — vom Band und vom Fenster „KI-Einstellungen“ benutzt."""
        n = dict(self.SPRACHEN).get(kennung, kennung)
        if self.w.current_tab() is not None:
            self.w.current_tab().meta["sprache"] = kennung
            if self.ed:
                self.ed.document().setModified(True)
        self.w.settings.set("pruefsprache", kennung)
        self.w.statusBar().showMessage(f"Dokumentsprache: {n}.", 4000)

    # ---- Verweise: Beschriftungen, Textmarken, Querverweise, Index, Zitate -------------------------------------
    def beschriftung(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.ui.dialogs.verweise_dialoge import BeschriftungDialog
        d = BeschriftungDialog(self.w)
        if d.exec():
            verweise.beschriftung_einfuegen(self.ed, d.label.currentText(), d.text.text().strip(), oben=d.pos.currentIndex() == 1)

    def _verzeichnis(self, art, titel, leer):
        if not self.ed:
            return
        from lunivo_writer.editor.verzeichnis import verzeichnis_einfuegen
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
            from lunivo_writer.ui.dialogs.verweise_dialoge import TextmarkeDialog
            TextmarkeDialog(self.w, self.ed).exec()

    def querverweis(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.ui.dialogs.verweise_dialoge import QuerverweisDialog
        d = QuerverweisDialog(self.w, self.ed)
        if d.exec():
            ziel, wie = d.ergebnis()
            if ziel:
                verweise.querverweis_einfuegen(self.ed, ziel, wie)

    def indexEintrag(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        c = self.ed.textCursor()
        vorschlag = c.selectedText() if c.hasSelection() else ""
        t, ok = QInputDialog.getText(self.w, "Indexeintrag", "Stichwort:", text=vorschlag)
        if ok and t.strip() and not verweise.index_markieren(self.ed, t.strip()):
            self.w.statusBar().showMessage("Bitte Text markieren oder in ein Wort klicken.", 4000)

    def quelleNeu(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.ui.dialogs.verweise_dialoge import QuelleDialog
        d = QuelleDialog(self.w)
        if d.exec():
            q = d.ergebnis(); q["tag"] = verweise.quelle_tag(self.ed.quellen, q)
            self.ed.quellen.append(q); self.ed.document().setModified(True)

    def quellenVerwalten(self, k=None):
        if self.ed:
            from lunivo_writer.ui.dialogs.verweise_dialoge import QuellenDialog
            QuellenDialog(self.w, self.ed).exec()

    def zitat(self, k=None):
        if not self.ed:
            return
        from lunivo_writer.editor import verweise
        from lunivo_writer.editor.literatur import eintrag
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
        from lunivo_writer.editor.literatur import ZITIERWEISEN
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
        """Neuer Kommentar: das Feld „Kommentare“ links öffnet sich mit dem Eingabefeld; ohne Markierung oder Wort gibt es keinen Anker."""
        if self.ed:
            c = self.ed.textCursor()
            if not c.hasSelection() and not self.ed.document().findBlock(c.position()).text().strip():
                self.w.statusBar().showMessage("Zum Kommentieren Text markieren oder in ein Wort klicken.", 4000)
                return
            self.w.navigation._neu_zeigen()

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
        """Neue Note: das Zeichen kommt in den Text, unten öffnet sich das Notenfeld mit dem Cursor darin."""
        if self.ed:
            self.w.noten_feld.oeffnen(art, self.ed.note_neu(art, ""))

    def fussnote(self, k=None): self._note("f", "Fußnote einfügen")
    def endnote(self, k=None): self._note("e", "Endnote einfügen")
    def noteWeiter(self, k=None):
        if self.ed: self.ed.note_springen(1)

    def noteZurueck(self, k=None):
        if self.ed: self.ed.note_springen(-1)

    def notenZeigen(self, k=None): self.w.zeige_navigation("noten")

    def note_bearbeiten(self, art, nid):
        if self.ed:
            self.w.noten_feld.oeffnen(art, nid)

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
        from lunivo_writer.ui.dialogs.dokument_dialoge import ZoomDialog
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
        from lunivo_writer.ui.dialogs.lesehilfe_dialog import LesehilfeDialog
        d = LesehilfeDialog(self.w)
        d.zeige_unter(k if hasattr(k, "mapToGlobal") else None)
        self._lh = d

    def ausblenden(self, k=None):
        """Markierten Text als „ausgeblendet“ formatieren (Strg+Umschalt+H)."""
        if self.ed:
            self.ed.set_versteckt(not self.ed.ist_versteckt())

    def an_ausblenden(self): return bool(self.ed) and self.ed.ist_versteckt()

    def versteckteZeigen(self, k=None):
        self.w.settings.set("ui/versteckt_zeigen", not self.w.settings.get_bool("ui/versteckt_zeigen", False))
        self.w.versteckt_anwenden()

    def an_versteckteZeigen(self): return self.w.settings.get_bool("ui/versteckt_zeigen", False)

    def silbenfarben(self, k=None):
        from lunivo_writer.editor import silbenfarben as S
        k = S.konfig_lesen(self.w.settings)
        self.w.settings.set("lesehilfe/silben/an", not k["an"])
        self.w.silbenfarben_anwenden()
        self.w.statusBar().showMessage("Silben werden farbig angezeigt." if not k["an"] else "Silbenfarben aus.", 4000)

    def an_silbenfarben(self):
        from lunivo_writer.editor import silbenfarben as S
        return S.konfig_lesen(self.w.settings)["an"]

    def silbenEinstellen(self, k=None):
        from lunivo_writer.ui.dialogs.silben_dialog import SilbenDialog
        SilbenDialog(self.w).exec()

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
        def setze(col):
            e, c, t = self._tab()
            if t:
                cell = t.cellAt(c)
                f = cell.format()
                f.setBackground(QBrush(col)) if col else f.clearBackground()
                cell.setFormat(f)
        return self._farbmenue(setze, "Keine Schattierung")

    # Tabellenformatvorlagen und Formatoptionen
    def menue_tabelleVorlagen(self):
        from lunivo_writer.editor import tabellenstil as TS
        m = QMenu()
        for n, (kopf, _s, streifen, _r) in TS.VORLAGEN.items():
            m.addAction(_farbfeld(kopf or streifen or "#ffffff"), n, lambda _=False, n=n: self._tabelle_vorlage(n))
        return m

    def _tabelle_vorlage(self, name):
        from lunivo_writer.editor import tabellenstil as TS
        e, c, t = self._tab()
        if t:
            o = self.tabellenOptionen
            e.textCursor().beginEditBlock()
            TS.anwenden(t, name, o["kopf"], o["streifen"], o["spalte"])
            e.textCursor().endEditBlock()
            self._tabellen_vorlage_name = name
            e.document().setModified(True)

    tabellenOptionen = {"kopf": True, "streifen": True, "spalte": False}

    def _tabellen_option(self, key):
        self.tabellenOptionen[key] = not self.tabellenOptionen[key]
        n = getattr(self, "_tabellen_vorlage_name", None)
        if n:
            self._tabelle_vorlage(n)

    def tabelleKopfzeile(self, k=None): self._tabellen_option("kopf")
    def tabelleStreifen(self, k=None): self._tabellen_option("streifen")
    def tabelleErsteSpalte(self, k=None): self._tabellen_option("spalte")
    def an_tabelleKopfzeile(self): return self.tabellenOptionen["kopf"]
    def an_tabelleStreifen(self): return self.tabellenOptionen["streifen"]
    def an_tabelleErsteSpalte(self): return self.tabellenOptionen["spalte"]

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

    # ---- Form- und WordArt-Tools --------------------------------------------------------------------------------------------
    FARBEN = ("#4a8fd8", "#6bbf59", "#f4a259", "#e5645f", "#ffd43b", "#ced4da", "#495057", "#ffffff", "#000000")

    def _form_farbe(self, feld: str, titel: str):
        c = weitere_farben(self.w, "#4a8fd8", titel)
        if c is not None:
            self._form_aendern(**{feld: c.name()})

    def _form_aendern(self, **kw):
        from lunivo_writer.editor import formen
        if not (self.ed and formen.aendern(self.ed, **kw)):
            self.w.lbl_msg.setText("Bitte zuerst eine Form auswählen (Schreibmarke vor der Form oder Form markieren).")

    def menue_formFuellung(self):
        m = FarbPalette(self.w, keine_text="Keine Füllung", start="#4a8fd8", titel="Füllfarbe")
        m.gewaehlt.connect(lambda c: self._form_aendern(fuell=c.name() if c is not None else ""))
        return m

    def menue_formKontur(self):
        m = FarbPalette(self.w, keine_text=None, start="#4a8fd8", titel="Linienfarbe")
        m.gewaehlt.connect(lambda c: self._form_aendern(linie=c.name()))
        m.addSeparator()
        st = m.addMenu("Linienstärke")
        for w in (0.5, 1.0, 2.0, 3.0, 5.0, 8.0):
            st.addAction(f"{w:g} pt".replace(".", ","), lambda _=False, w=w: self._form_aendern(strich=w))
        return m

    def menue_formVorlagen(self):
        from lunivo_writer.editor import formen
        m = QMenu()
        for n, fu, li, _st in formen.VORLAGEN:
            m.addAction(_farbfeld(fu or "#ffffff"), n, lambda _=False, n=n: self._form_vorlage(n))
        return m

    def _form_vorlage(self, name):
        from lunivo_writer.editor import formen
        if not (self.ed and formen.vorlage(self.ed, name)):
            self.w.lbl_msg.setText("Bitte zuerst eine Form auswählen.")

    def formText(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from lunivo_writer.editor import formen
        o = formen.objekt(f) or {}
        akt = o.get("daten", {}).get("text", "")
        t, ok = QInputDialog.getText(self.w, "Text in der Form", "Text:", text=akt)
        if ok:
            self._form_aendern(text=t)

    # ---- Zeichentools (Kontext-Reiter für frei positionierte Bilder und Formen) --------------------------------------------------
    def _zeichen(self):
        """(Editor, Ziel) des markierten Bildes oder (Editor, None)."""
        from lunivo_writer.editor import bildlayout as BL
        e = self.ed
        return (e, BL.ziel(e)) if e else (None, None)

    def _zeichen_edit(self):
        return self.ed

    def menue_zeichenFormstile(self):
        return FreiMenue.formstile(self)

    def menue_zeichenFuellung(self):
        return FreiMenue.fuell(self)

    def menue_zeichenGliederung(self):
        return FreiMenue.kontur(self)

    def menue_zeichenAusrichten(self):
        m = QMenu()
        for schl, text in (("links", "Links ausrichten"), ("mitte", "Waagerecht zentrieren"), ("rechts", "Rechts ausrichten"),
                           ("oben", "Oben ausrichten"), ("mittig", "Senkrecht zentrieren"), ("unten", "Unten ausrichten")):
            m.addAction(text, lambda _=False, s=schl: self.zeichenAusrichten(None, s))
        return m

    def menue_zeichenDrehen(self):
        m = QMenu()
        m.addAction("Um 90° nach rechts drehen", lambda: self.zeichenDrehen(None, 90))
        m.addAction("Um 90° nach links drehen", lambda: self.zeichenDrehen(None, -90))
        m.addAction("Drehung zurücksetzen", lambda: self.zeichenDrehen(None, 0))
        return m

    def menue_zeichenEbene(self):
        m = QMenu()
        m.addAction("Vor den Text", lambda: self.zeichenEbene(None, "vor"))
        m.addAction("Hinter den Text", lambda: self.zeichenEbene(None, "hinter"))
        return m

    def wortExtras(self, k=None):
        """Wort-Extras: Absätze aufräumen (Markierung, sonst das ganze Dokument)."""
        from lunivo_writer.editor import wortextras as W
        if not self.ed:
            return
        m = QMenu()
        for text, f in W.AKTIONEN:
            m.addAction(text, lambda _=False, t=text, f=f: self._wort_extra(t, f))
        self._popup(m)

    def _wort_extra(self, text, f):
        n = f(self.ed)
        self.w.statusBar().showMessage(f"{text}: {n} Stelle(n) geändert." if n else f"{text}: nichts zu ändern.", 5000)

    def zeichenEffekte(self, k=None):
        e, z = self._zeichen()
        if z is not None:
            e._frei_effekte()

    def zeichenFormatUebertragen(self, k=None):
        from lunivo_writer.editor import bildlayout as BL
        e, z = self._zeichen()
        merk = BL.format_merken(z)
        if merk is None:
            self.w.statusBar().showMessage("Format übertragen: erst ein freies Bild oder eine Form markieren.", 4000)
            return
        e._frei_format_merk = merk
        self.w.statusBar().showMessage("Jetzt das Bild anklicken, das dieses Format bekommen soll.", 6000)

    def zeichenAusrichten(self, k=None, wie="links"):
        from lunivo_writer.editor import bildlayout as BL
        e, z = self._zeichen()
        BL.ausrichten(e, z, wie)

    def zeichenDrehen(self, k=None, grad=90):
        from lunivo_writer.editor import bildlayout as BL
        e, z = self._zeichen()
        if z is not None and z[0] == "frei":
            BL.frei_aendern(e, z, dreh=0.0) if grad == 0 else BL.drehen(e, z, float(grad))

    def zeichenEbene(self, k=None, wo="vor"):
        from lunivo_writer.editor import bildlayout as BL
        e, z = self._zeichen()
        BL.ebene(e, z, wo == "vor")

    def zeichenVorn(self, k=None): self.zeichenEbene(None, "vor")
    def zeichenHinten(self, k=None): self.zeichenEbene(None, "hinter")

    def zeichenUmbruch(self, k=None):
        e, z = self._zeichen()
        if z is not None:
            e._frei_layout_popup(QCursor.pos())

    def zeichenLayout(self, k=None):
        e, z = self._zeichen()
        if z is not None:
            e.bild_layout_dialog()

    def zeichenMasse(self, breite_mm=None, hoehe_mm=None):
        from lunivo_writer.editor import bildlayout as BL
        e, z = self._zeichen()
        BL.masse_setzen(e, z, breite_mm, hoehe_mm)

    def gruppieren(self, k=None):
        from lunivo_writer.editor import formen
        if self.ed:
            r = formen.gruppieren(self.ed)
            self.w.lbl_msg.setText(r or "Formen gruppiert.")

    def gruppeAufheben(self, k=None):
        from lunivo_writer.editor import formen
        if self.ed:
            r = formen.gruppe_aufheben(self.ed)
            self.w.lbl_msg.setText(r or "Gruppierung aufgehoben.")

    def bildGroesse(self, k=None):
        e, f = self._bild()
        if f is None:
            return
        from lunivo_writer.ui.dialogs.dokument_dialoge import BildGroesseDialog
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
        from lunivo_writer.editor import umbruch as U
        aktuell = U.schwebend(e.document(), e._bild_cursor().selectionStart()) or "zeile"
        m = QMenu()
        for modus, text in (("zeile", "Mit Text in Zeile"), ("links", "Links, Text umfließt"), ("rechts", "Rechts, Text umfließt"),
                             ("oben_unten", "Oben und unten (eigene Zeile)")):
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
        from lunivo_writer.services import vorlesen as v
        v.beenden()
        self.w.lbl_msg.setText("Vorlesen angehalten.")

    def stimmeWaehlen(self, k=None):
        self.w.stimme_waehlen()

    # ==== KI ========================================================================================================
    def kiKorrektur(self, k=None): self.w.ki.korrigieren()
    def kiVorschlaege(self, k=None):
        self.w.sidebar._funde_zeigen(); self.w.ki.vorschlaege_holen()
    def kiUmformulieren(self, k=None): self.w.ki.text_aktion("umformulieren")
    def kiZusammenfassen(self, k=None):
        self.w.sidebar._funde_zeigen(); self.w.ki.zusammenfassen()
    def w_kiUebersetzen(self, k=None): self.w.ki.uebersetzen()                      # Markierung → ersetzen, sonst Übersetzung zeigen
    def w_kiUebersetzenErsetzen(self, k=None): self.w.ki.uebersetzen(modus="ersetzen")
    def w_kiUebersetzenZeigen(self, k=None): self.w.ki.uebersetzen(modus="zeigen")

    def menue_uebersetzenMenue(self):
        m = QMenu()
        m.addAction("Markierung im Text ersetzen", self.w_kiUebersetzenErsetzen)
        m.addAction("Übersetzung in Schreibhilfe und Chat zeigen", self.w_kiUebersetzenZeigen)
        m.addSeparator()
        m.addAction("Sprache wählen …", self.w_kiSprache)
        return m

    def kiEntwerfen(self, k=None): self.w.chat_oeffnen("Entwirf einen Text zu folgendem Anliegen: ")
    def w_chatUmschalten(self, k=None): self.w.chat_oeffnen("")
    def _ki_einstellungen(self, reiter: int) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
        ausfuehren(KIEinstellungenDialog(self.w, reiter))

    def w_kiEinstellungen(self, k=None): self._ki_einstellungen(0)
    def w_kiKonfiguration(self, k=None): self._ki_einstellungen(1)
    def w_kiSprache(self, k=None): self._ki_einstellungen(2)
    def w_eigenenAnbieterHinzufuegen(self, k=None): self._ki_einstellungen(0)

    def w_kiErgebnisse(self, k=None):
        from lunivo_writer.ui.dialogs.ki_dialoge import ErgebnisseDialog
        ErgebnisseDialog(self.w).exec()

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
        from lunivo_writer.services.integrations import wps
        self._extern(wps.oeffnen, "WPS Writer")

    def mitLibreOfficeOeffnen(self, k=None):
        from lunivo_writer.services.integrations import wps
        self._extern(wps.mit_libreoffice_oeffnen, "LibreOffice")
