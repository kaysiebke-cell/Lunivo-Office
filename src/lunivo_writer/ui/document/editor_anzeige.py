"""Anzeige: Sprechblasen, ausgeblendeter Text, Lesehilfe."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen, QTextCharFormat, QTextCursor, QTextOption
from PySide6.QtWidgets import QTextEdit
from lunivo_writer.editor import sprechblasen as SB
from lunivo_writer.editor.anzeige_extra import aenderungszeilen
from lunivo_writer.editor.zusatz import P_VERSTECKT
from lunivo_writer.models.page import mm_to_px
from lunivo_writer.core.farben import Farbe


class AnzeigeBaustein:
    """Anzeige: Sprechblasen, ausgeblendeter Text, Lesehilfe. Baustein von ``DocumentEditor`` (siehe ``lunivo_writer/ui/document/document_editor.py``)."""


    def blasen_konfig(self) -> dict:
        return SB.konfig_lesen(self._OptAdapter(self))


    def blasen_rand(self) -> str:
        return self.blasen_konfig()["rand"]


    def blasen_linien(self) -> bool:
        return self.blasen_konfig()["linien"]


    def _blasen_da(self) -> bool:
        k = self.blasen_konfig()
        if self.web or not SB.aktiv(k):
            return False
        if self.kommentare:
            return True
        return k["verwenden"] == "Immer" and bool(self.aenderungen())


    def _blasen_einrichten(self) -> None:
        """Seitenrand für die Blasen: Fläche neben der Seite (setViewportMargins), nur wenn es Blasen gibt."""
        k = self.blasen_konfig()
        extra = int((SB.breite_mm(k) + SB.LUECKE_MM) * mm_to_px(1) * self.zoom) if self._blasen_da() else 0
        self._blasen_extra = extra
        links = k["rand"] == "Links"
        self.setViewportMargins(extra if links else 0, 0, 0 if links else extra, 0)
        if not self.web:
            self.setFixedWidth(int(mm_to_px(self.page.width_mm) * self.zoom) + extra)
        if extra and self._blasen_flaeche is None:
            from lunivo_writer.ui.document.blasen_flaeche import BlasenFlaeche
            self._blasen_flaeche = BlasenFlaeche(self)
        if self._blasen_flaeche is not None:
            self._blasen_flaeche.setVisible(bool(extra))
        self._blasen_geometrie()


    def _blasen_geometrie(self) -> None:
        f = self._blasen_flaeche
        if f is None or not self._blasen_extra:
            return
        vp = self.viewport().geometry()
        if self.blasen_rand() == "Links":
            f.setGeometry(0, vp.top(), self._blasen_extra, vp.height())
        else:
            f.setGeometry(vp.right() + 1, vp.top(), self._blasen_extra, vp.height())
        f.update()


    def blasen_layout(self, breite: float) -> list:
        """[(Blase, Rechteck in der Blasenfläche, y der Textzeile)] — gestapelt, ohne sich zu überlappen."""
        rev = (self.document().revision(), id(self.kommentare), len(self.kommentare), round(breite), self.zoom)
        if self._blasen_cache[0] == rev:
            return self._blasen_cache[1]
        k = self.blasen_konfig()
        blasen = SB.sammeln(self.document(), self.kommentare, k["verwenden"])
        font = QFont(self.font()); font.setPixelSize(max(7, int(SB.blasen_px(self.opt_text("kommentare/schrift", "mittel")) * self.zoom)))
        w = max(60.0, breite - 12)
        anker, hoehen = [], []
        for bl in blasen:
            r = self.cursorRect(self._cursor_at(min(bl.von, self.document().characterCount() - 1)))
            anker.append(float(r.y()))
            hoehen.append(SB.messen(bl, w, font))
        unten = float(self.height())
        ys = SB.stapeln(anker, hoehen, unten)
        x = 6.0
        out = [(bl, QRectF(x, y, w, h), a + 8) for bl, y, h, a in zip(blasen, ys, hoehen, anker)]
        self._blasen_cache = (rev, out)
        return out


    def kommentar_bearbeiten(self, kid: int) -> None:
        """Doppelklick auf eine Blase: den Kommentar in der Karte links bearbeiten."""
        nav = getattr(self.window(), "navigation", None)
        if nav is not None:
            nav.kommentar_bearbeiten(kid)


    # ---- Ausgeblendeter Text -------------------------------------------------------------------------------------------
    def set_versteckt_zeigen(self, an: bool) -> None:
        self.versteckt_zeigen = an
        self._versteckt_hl.setze_zeigen(an)
        self._timer.start()


    def ist_versteckt(self) -> bool:
        c = self.textCursor()
        if not c.hasSelection():
            return c.charFormat().hasProperty(P_VERSTECKT)
        return all(f.charFormat().hasProperty(P_VERSTECKT) for f in self._fragmente_in(c.selectionStart(), c.selectionEnd()))


    def _fragmente_in(self, von: int, bis: int):
        b = self.document().findBlock(von)
        while b.isValid() and b.position() < bis:
            it = b.begin()
            while not it.atEnd():
                f = it.fragment()
                if f.isValid() and f.position() < bis and f.position() + f.length() > von:
                    yield f
                it += 1
            b = b.next()


    def set_versteckt(self, an: bool) -> None:
        """Markierung (oder Wort am Zeiger) als ausgeblendeten Text formatieren / zurücknehmen."""
        c = self.textCursor()
        if not c.hasSelection():
            c.select(QTextCursor.WordUnderCursor)
        if not c.hasSelection():
            return
        von, bis = c.selectionStart(), c.selectionEnd()
        c.beginEditBlock()
        for f in list(self._fragmente_in(von, bis)):
            a, e = max(von, f.position()), min(bis, f.position() + f.length())
            k = QTextCursor(self.document()); k.setPosition(a); k.setPosition(e, QTextCursor.KeepAnchor)
            fm = QTextCharFormat(f.charFormat())
            fm.setProperty(P_VERSTECKT, 1) if an else fm.clearProperty(P_VERSTECKT)
            k.setCharFormat(fm)
        c.endEditBlock()
        self._versteckt_hl.rehighlight()
        self.document().setModified(True)


    # ---- Anzeige: Zeilenfokus, Eckmarken, Lesehilfe --------------------------------------------------
    def set_zeilenfokus(self, an: bool) -> None:
        self.zeilenfokus = an
        self.viewport().update()


    def set_marken(self, an: bool) -> None:
        self.marken = an
        self.viewport().update()


    def set_lesehilfe(self, papier: str, buchstaben: float, wort: float) -> None:
        pk = QColor(papier) if papier else QColor()
        text_farbe = "black" if (not pk.isValid() or pk.lightness() >= 128) else Farbe.WEISS
        self._lese_papier = papier if pk.isValid() and papier.lower() not in ("white", Farbe.WEISS) else ""
        self._lese_text = text_farbe if self._lese_papier else ""
        self.setStyleSheet(f"QTextEdit {{ background: {papier or 'white'}; color: {text_farbe}; border: none; }}")
        self.viewport().update()
        f = QFont(self.document().defaultFont())
        f.setLetterSpacing(QFont.AbsoluteSpacing, buchstaben)
        f.setWordSpacing(wort)
        self.document().setDefaultFont(f)


    def set_zeilenluft(self, faktor: float) -> None:
        """Lesehilfe „Zeilenluft“: nur in dieser Anzeige; gespeichert und gedruckt wird ohne (editor/lese_zeilenluft.py)."""
        from lunivo_writer.editor import lese_zeilenluft as LZ
        if abs(getattr(self, "_lese_luft", 1.0) - faktor) < 1e-6 and (faktor == 1.0 or LZ.aktiv(self.document())):
            return
        self._lese_luft = float(faktor)
        LZ.anwenden(self.document(), faktor)
        self._timer.start()                                 # Seitenumbrüche neu berechnen


    # ---- Lesehilfe am Schirm: Absatz größer, Übriger Text blasser ---------------------------------------------------------
    # Wie in der ersten Fassung ändert das nichts am Dokument: Der Text wird nur anders gezeigt, gedruckt und gespeichert
    # wird er unverändert.
    def set_lesefokus(self, wachstum: float, blasse: float) -> None:
        """wachstum: 1,0 / 1,05 / 1,10 für den Absatz, in dem die Schreibmarke steht; blasse: 1,0 / 0,62 / 0,38 für den übrigen Text."""
        self._lese_wachstum, self._lese_blasse = max(1.0, float(wachstum)), min(1.0, float(blasse))
        if not getattr(self, "_lese_verbunden", False):
            self.cursorPositionChanged.connect(self._lese_neu)
            self.verticalScrollBar().valueChanged.connect(self._lese_neu)
            self._lese_verbunden = True
        self._lese_neu(erzwingen=True)


    def _lese_aktiv(self) -> bool:
        return getattr(self, "_lese_wachstum", 1.0) > 1.0 or getattr(self, "_lese_blasse", 1.0) < 1.0


    def _lese_neu(self, *_, erzwingen: bool = False) -> None:
        if not (self._lese_aktiv() or erzwingen):
            return
        if hasattr(self, "_overlays_neu"):
            self._overlays_neu()
        self.viewport().update()


    def _lese_blasse_auswahl(self) -> list:
        """Zusatzauswahl, die den Text außerhalb des aktuellen Absatzes in die Farbe des Papiers mischt (nur der sichtbare Bereich)."""
        b = getattr(self, "_lese_blasse", 1.0)
        aktuell = self.textCursor().block()
        if b >= 1.0 or not aktuell.isValid() or not aktuell.text().strip():
            return []                                       # in einer leeren Zeile tritt nichts zurück, sonst wäre alles nur blasser
        papier = QColor(self._lese_papier or Farbe.WEISS)
        text = QColor(self._lese_text or Farbe.SCHWARZ)
        farbe = QColor(round(text.red() * b + papier.red() * (1 - b)), round(text.green() * b + papier.green() * (1 - b)),
                       round(text.blue() * b + papier.blue() * (1 - b)))
        vp = self.viewport()
        blk = self.cursorForPosition(QPoint(0, 0)).block()
        ende = self.cursorForPosition(QPoint(max(0, vp.width() - 1), max(0, vp.height() - 1))).block().blockNumber()
        sel = []
        while blk.isValid() and blk.blockNumber() <= ende:
            if blk.blockNumber() != aktuell.blockNumber() and blk.text():
                c = QTextCursor(blk)
                c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                fmt = QTextCharFormat(); fmt.setForeground(farbe)
                e = QTextEdit.ExtraSelection(); e.cursor = c; e.format = fmt
                sel.append(e)
            blk = blk.next()
        return sel


    def _lese_wachstum_zeichnen(self) -> None:
        """Der Absatz an der Schreibmarke wird ein wenig größer gezeichnet (aus der Mitte, ohne den Umbruch zu ändern): sein
        Textlayout wird über das Original gelegt. Bei einer Auswahl, über Seiten- und Spaltenwechsel oder bei Tabellen unterbleibt es."""
        f = getattr(self, "_lese_wachstum", 1.0)
        c0 = self.textCursor()
        blk = c0.block()
        if f <= 1.0 or c0.hasSelection() or not blk.isValid() or not blk.text().strip() or blk.layout() is None or c0.currentTable():
            return
        lay = blk.layout()
        if lay.lineCount() == 0:
            return
        r0 = self.cursorRect(QTextCursor(blk))
        c1 = QTextCursor(blk); c1.movePosition(QTextCursor.EndOfBlock)
        r1 = self.cursorRect(c1)
        if r1.bottom() < r0.top() or r1.bottom() - r0.top() > 40 * lay.lineCount() + 40:
            return
        vp = self.viewport()
        if self._blatt_aktiv():
            g = self._sp_geo()
            breite = g["cb"]
            spalte = max(0, min(int(g["n"]) - 1, int((r0.x() - g["ml"]) // max(1.0, g["cb"] + g["g"]))))
            x0 = g["ml"] + spalte * (g["cb"] + g["g"])
            papier = QColor(self._lese_papier or self.page.color or "white")
        else:
            x0 = self.document().documentMargin()
            breite = vp.width() - 2 * x0
            papier = QColor(self._lese_papier or "white")
        feld = QRectF(x0, r0.top(), breite, r1.bottom() - r0.top() + 1)
        # QTextLayout.draw addiert die eigene Position im Dokument selbst; die Schreibmarke liefert die Stelle auf dem Schirm
        origin = QPointF(r0.x() - lay.lineAt(0).x() - lay.position().x(), r0.top() - lay.lineAt(0).y() - lay.position().y())
        p2 = QPainter(vp)
        p2.setClipRect(vp.rect())
        p2.fillRect(feld, papier)                                   # das Original darunter wegnehmen
        dreh = QPointF(feld.left(), feld.center().y())              # wächst vom linken Rand der Spalte aus, nicht in den Seitenrand
        p2.translate(dreh); p2.scale(f, f); p2.translate(-dreh)
        lay.draw(p2, origin)
        if self.hasFocus():
            lay.drawCursor(p2, origin, c0.positionInBlock())
        p2.end()


    def _aenderungszeilen_gecacht(self) -> list:
        rev = self.document().revision()
        if self._zeilen_cache[0] != rev:
            self._zeilen_cache = (rev, aenderungszeilen(self.document()) if (self._hat_zusatz or self.verfolgen) else [])
        return self._zeilen_cache[1]


    def _extras_zeichnen(self, p: QPainter, sp: bool) -> None:
        """Objektanker, Änderungsbalken, Kopf- und Fußzeile im Rand der Seite."""
        if self.web:
            return
        vp, z, pg = self.viewport(), self.zoom, self.page
        is_dark = self.palette().color(QPalette.Window).lightness() < 128
        line_color = QColor(Farbe.GRAU_HELL) if is_dark else QColor(Farbe.GRAU)
        accent_color = QColor("#748ffc") if is_dark else QColor(Farbe.BLAU)

        # Objektanker neben Bildern, die vom Text umflossen werden (bei sichtbaren Formatierungszeichen)
        marks = bool(self.document().defaultTextOption().flags() & QTextOption.ShowTabsAndSpaces)
        if marks and self.opt("ui/objektanker", True):
            from lunivo_writer.editor.umbruch import schwebende_rahmen
            ankern = schwebende_rahmen(self.document())
            if ankern:
                f = QFont(p.font()); f.setPointSizeF(max(7.0, 10 * z)); p.setFont(f)
                p.setPen(accent_color)
                for pos in ankern:
                    r = self.cursorRect(self._cursor_at(pos))
                    p.drawText(max(0, r.x() - int(18 * z)), r.y() + r.height() // 2, "⚓")
        # Abschnittsumbrüche: gestrichelte Linie mit Beschriftung unter dem letzten Absatz des Abschnitts
        if not self._mehrspaltig():
            from lunivo_writer.editor import abschnitte as AB
            for nr, typ, _ps in AB.umbrueche(self.document()):
                blk = self.document().findBlockByNumber(nr)
                c = QTextCursor(blk); c.movePosition(QTextCursor.EndOfBlock)
                r = self.cursorRect(c)
                if r.bottom() < -20 or r.top() > vp.height():
                    continue
                y = r.bottom() + int(3 * z)
                x0, x1 = int(mm_to_px(pg.margin_left_mm) * z), vp.width() - int(mm_to_px(pg.margin_right_mm) * z)
                p.setPen(QPen(accent_color, 1, Qt.DashLine))
                p.drawLine(x0, y, x1, y)
                f = QFont(p.font()); f.setPointSizeF(max(6.5, 8 * z)); p.setFont(f)
                txt = f"Abschnittsumbruch ({AB.TYPEN.get(typ, typ)})"
                p.setPen(accent_color)
                p.drawText(x0 + int(8 * z), y - int(2 * z), txt)
        # Geänderte Zeilen
        seite = self.opt_text("aenderungen/balken", "links")
        if seite in ("links", "rechts", "außen"):
            zeilen = self._aenderungszeilen_gecacht()
            if zeilen:
                p.setPen(QPen(QColor("#ff6b6b") if is_dark else QColor(Farbe.ROT), 1.6))
                for t, u in zeilen:
                    g = self._sp_geo()
                    vx, vy = self._sp_view(0, t)
                    x = vx + (g["cb"] + 8 * z if seite == "rechts" else -8 * z)
                    y0, y1 = vy, vy + (u - t)
                    p.drawLine(int(x), int(y0), int(x), int(y1))
        # Linien von den Sprechblasen zum Text: Textende bis zum Seitenrand (der Rest steht in der Blasenfläche)
        if self._blasen_extra and self.blasen_linien():
            rechts = self.blasen_rand() == "Rechts"
            for bl, r, y_text in self.blasen_layout(self._blasen_extra):
                pos = min(bl.bis, self.document().characterCount() - 1)
                blk = self.document().findBlock(pos)
                if blk.isValid() and blk.layout() is not None and blk.layout().lineCount():
                    ln = blk.layout().lineForTextPosition(max(0, pos - blk.position()))
                    pos = blk.position() + ln.textStart() + max(0, ln.textLength() - 1)       # Ende der Zeile, in der der Text endet
                rc = self.cursorRect(self._cursor_at(pos))
                p.setPen(QPen(QColor(bl.farbe), 1, Qt.DotLine))
                y = int(rc.y() + rc.height() / 2)
                p.drawLine(rc.x() + 4 if rechts else 0, y, vp.width() if rechts else rc.x(), y)
        # Kopf- und Fußzeile auf jedem Blatt (Lage wie im Druck: 8 mm unter dem oberen, 18 mm über dem unteren Blattrand)
        if self.opt("ui/kopffuss_anzeigen", True):
            from lunivo_writer.editor.pagination import _draw_hf
            g = self._sp_geo()
            ml, cw = mm_to_px(pg.margin_left_mm), pg.content_width_px
            ph = mm_to_px(pg.height_mm)
            base = QFont(self.font())
            p.setPen(line_color)
            for k in range(self._blatt_anzahl()):
                oben = self.blatt_oben(k)
                if oben > vp.height() or oben + g["H"] < 0:
                    continue
                kopf, fuss = (pg.first_header, pg.first_footer) if (k == 0 and pg.diff_first) else (pg.header, pg.footer)
                p.save()
                p.translate(0, oben)
                p.scale(z, z)
                _draw_hf(p, kopf, QRectF(ml, mm_to_px(8), cw, mm_to_px(10)), k + 1, self._pages, base)
                _draw_hf(p, fuss, QRectF(ml, ph - mm_to_px(18), cw, mm_to_px(10)), k + 1, self._pages, base)
                p.restore()
