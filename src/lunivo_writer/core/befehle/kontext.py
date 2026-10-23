"""Befehle: Kontext-Reiter: Tabelle, Bild, Formen, Zeichnen."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QBrush, QCursor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QInputDialog, QMenu
from lunivo_writer.ui.baukasten import FarbPalette, weitere_farben
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.core.farben import Farbe
from lunivo_writer.core.befehle.hilfen import FreiMenue, _farbfeld


class KontextBefehle:
    """Befehle des Bandes: Kontext-Reiter: Tabelle, Bild, Formen, Zeichnen. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


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
        bb = knopfzeile(d)
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
            m.addAction(_farbfeld(kopf or streifen or Farbe.WEISS), n, lambda _=False, n=n: self._tabelle_vorlage(n))
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
    FARBEN = (Farbe.AKZENT_DUNKEL, "#6bbf59", "#f4a259", "#e5645f", "#ffd43b", "#ced4da", "#495057", Farbe.WEISS, Farbe.SCHWARZ)


    def _form_farbe(self, feld: str, titel: str):
        c = weitere_farben(self.w, Farbe.AKZENT_DUNKEL, titel)
        if c is not None:
            self._form_aendern(**{feld: c.name()})


    def _form_aendern(self, **kw):
        from lunivo_writer.editor import formen
        if not (self.ed and formen.aendern(self.ed, **kw)):
            self.w.lbl_msg.setText("Bitte zuerst eine Form auswählen (Schreibmarke vor der Form oder Form markieren).")


    def menue_formFuellung(self):
        m = FarbPalette(self.w, keine_text="Keine Füllung", start=Farbe.AKZENT_DUNKEL, titel="Füllfarbe")
        m.gewaehlt.connect(lambda c: self._form_aendern(fuell=c.name() if c is not None else ""))
        return m


    def menue_formKontur(self):
        m = FarbPalette(self.w, keine_text=None, start=Farbe.AKZENT_DUNKEL, titel="Linienfarbe")
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
            m.addAction(_farbfeld(fu or Farbe.WEISS), n, lambda _=False, n=n: self._form_vorlage(n))
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
