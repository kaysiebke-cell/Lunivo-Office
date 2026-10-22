"""Der Editor: QTextEdit mit Seitenbreite, Formatierungsbefehlen und Seitenzählung."""
from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, QPointF, QRect, QRectF, QSizeF, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import (
    QAbstractTextDocumentLayout, QBrush, QColor, QDragMoveEvent, QDropEvent, QFont, QImage, QMouseEvent, QPainter, QPalette, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor,
    QTextDocument, QTextFormat, QTextFrameFormat, QTextImageFormat, QTextListFormat,
    QTextTableFormat, QTextLength, QTextDocumentFragment, QTextOption,
)
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QScrollArea, QTextEdit

from lunivo_writer.services.docx_reader import LH_PROPORTIONAL, STYLE_PROP
from lunivo_writer.editor import sprechblasen as SB
from lunivo_writer.editor.anzeige_extra import VersteckterText, aenderungszeilen, feldbereiche
from lunivo_writer.editor.zusatz import P_VERSTECKT
from lunivo_writer.models.page import PageSettings, mm_to_px, px_to_mm
from lunivo_writer.proofing.autokorrektur import kleinste_aenderung
from lunivo_writer.editor.pagination import bind_layout, paginated_copy
from lunivo_writer.editor import stile
from lunivo_writer.editor.zusatz import abstand_davor_px
from lunivo_writer.ui.document.freie_bilder_bedienung import FreieBilderMixin
from lunivo_writer.ui.document.zusatz_editor import ZusatzMixin

BLATT_ABSTAND_PX = 32            # grauer Zwischenraum zwischen zwei Blättern (bei 100 % Zoom)

STYLES = dict.fromkeys(stile.NAMEN)       # nur die eingebauten; selbst angelegte: stile.namen()            # Namen der Formatvorlagen (Definitionen: editor/stile.py)


EINFUEGE_MODI = ["Quellformatierung beibehalten", "Zielformatierung verwenden", "Nur Text"]


def _ziel_fragment(html: str, standard: QFont):
    """HTML einfügen, aber Schriftart, -größe, Farben und Hintergründe des Ziels behalten (Fett, Kursiv, Verweise bleiben)."""
    from PySide6.QtGui import QBrush
    d = QTextDocument()
    d.setHtml(html)
    c = QTextCursor(d)
    c.select(QTextCursor.Document)
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            fr = it.fragment()
            if fr.isValid() and not fr.charFormat().isImageFormat():
                f = QTextCharFormat(fr.charFormat())
                f.clearProperty(QTextFormat.FontFamilies); f.clearProperty(QTextFormat.FontFamily)
                f.clearProperty(QTextFormat.FontPointSize); f.clearProperty(QTextFormat.FontPixelSize)
                f.clearForeground(); f.clearBackground()
                k = QTextCursor(d); k.setPosition(fr.position()); k.setPosition(fr.position() + fr.length(), QTextCursor.KeepAnchor)
                k.setCharFormat(f)
            it += 1
        b = b.next()
    return QTextDocumentFragment(d)


class DocumentEditor(FreieBilderMixin, ZusatzMixin, QTextEdit):
    pageInfoChanged = Signal(int, int)       # aktuelle Seite, Seitenzahl
    formatChanged = Signal()                 # Cursor-Format hat sich geändert
    zoomChanged = Signal(float)
    freiAuswahlGeaendert = Signal()           # ein frei positioniertes Bild wurde markiert oder die Markierung aufgehoben
    pageApplied = Signal()                    # Seiteneinrichtung oder Größe hat sich geändert

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = PageSettings()
        self.stil_tasten()
        self.setAcceptRichText(True)
        self.setFrameShape(QTextEdit.NoFrame)          # das Blatt hat keinen Rahmen; es steht frei auf der Arbeitsfläche
        self.setUndoRedoEnabled(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.show_marks = False
        self.zoom = 1.0
        self.gitter = False
        self.web = False
        self._web_breite = 800
        self.gliederung = False
        self.zeilenfokus = False
        self.marken = False                # Textbegrenzungen (Eckmarken am Textrand)
        self.vorhersage = None            # Rückruf: Wortanfang → Liste von Vorschlägen
        self.autokorr = None              # Rückruf: Text vor dem Zeiger → korrigierter Text
        self.mini_hook = None             # Rückruf(editor, globalePosition, rechtsklick): Minisymbolleiste zeigen/verbergen
        self.kontext_hook = None          # Rückruf(menü, position): ergänzt das Rechtsklick-Menü
        self.opt = lambda name, std=True: std      # Rückruf: Schalter aus den Optionen
        self.opt_text = lambda name, std="": std   # Rückruf: Textwerte aus den Optionen
        self._wellen: list[dict] = []
        self._popup = QListWidget(None)
        self._popup.setWindowFlags(Qt.ToolTip)
        self._popup.setFocusPolicy(Qt.NoFocus)
        self._popup.itemClicked.connect(lambda it: self._vorschlag_nehmen(it.data(Qt.UserRole)))
        self._pages = 1
        self._extra_seiten = 0              # Blätter, die erst der Druck (Endnoten) anhängt
        self._lese_papier = ""              # Lesehilfe: Papierfarbe / Textfarbe überschreiben die Blattfarbe
        self._lese_text = ""
        self._breaks: list[int] = []
        self._paged: QTextDocument | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._recount)
        self.cursorPositionChanged.connect(self._cursor_moved)
        self.cursorPositionChanged.connect(lambda: self.zeilenfokus and self.viewport().update())
        self.currentCharFormatChanged.connect(lambda *_: self.formatChanged.emit())
        self.document().contentsChanged.connect(self._timer.start)
        self._fluss = QTimer(self); self._fluss.setSingleShot(True); self._fluss.setInterval(500)      # Umbruchregeln nach dem Tippen prüfen
        self._fluss.timeout.connect(self._seitenfluss)
        self._fluss_laeuft = False
        self._effekt_cache: bool | None = None
        self.document().contentsChanged.connect(lambda: setattr(self, "_effekt_cache", None))
        self.document().contentsChanged.connect(self._fluss_planen)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)       # die Seite wächst mit, der graue Grund scrollt
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cursorPositionChanged.connect(self._scroll_outer)
        self._verbinde_groesse()
        self._zusatz_init()
        self.versteckt_zeigen = False
        self._blasen_flaeche = None
        self._blasen_cache = (None, [])
        self._blasen_extra = 0
        self._versteckt_hl = VersteckterText(self.document())
        self._zeilen_cache = (-1, [])
        self._sp_caret = True
        self._sp_timer = QTimer(self)                  # Schreibmarke blinkt selbst, solange Spalten gezeichnet werden
        self._sp_timer.setInterval(530)
        self._sp_timer.timeout.connect(self._sp_blinken)
        self.cursorPositionChanged.connect(self._sp_neu_zeichnen)
        self.selectionChanged.connect(self._sp_neu_zeichnen)
        self.document().contentsChanged.connect(self._sp_neu_zeichnen)
        self.apply_page(self.page)

    # ---- Dokument und Seite ---------------------------------------------

    def _verbinde_groesse(self) -> None:
        self.document().documentLayout().documentSizeChanged.connect(self._passe_hoehe_an)

    def _passe_hoehe_an(self, *_):
        if self.web:
            h = int(self.document().size().height()) + 4
        else:
            g = self._sp_geo()
            h = int(g["top"] + self._blatt_anzahl() * (g["H"] + g["gap"]))
        if h != self.height():
            self.setFixedHeight(h)
        self.pageApplied.emit()

    def _blatt_anzahl(self) -> int:
        """Anzahl der Blätter: so viele, wie der Textfluss des Editors Seiten braucht (plus Noten-Seiten, die nur der Druck anhängt)."""
        n = max(1, int(self.page.spalten))
        return max(1, -(-max(1, self.document().pageCount()) // n)) + self._extra_seiten

    def _aussen(self):
        w = self.parent()
        while w is not None and not isinstance(w, QScrollArea):
            w = w.parent()
        return w

    def _scroll_outer(self) -> None:
        sa = self._aussen()
        if sa is None or sa.widget() is None:
            return
        r = self.cursorRect()
        pt = self.viewport().mapTo(sa.widget(), r.topLeft())
        sa.ensureVisible(pt.x(), pt.y() + r.height() // 2, 10, max(40, r.height() * 2))

    def set_document_and_page(self, doc: QTextDocument, page: PageSettings) -> None:
        self.setDocument(doc)
        self._versteckt_hl = VersteckterText(doc, self.versteckt_zeigen)
        self._verbinde_groesse()
        doc.setDocumentMargin(0)
        doc.contentsChanged.connect(self._timer.start)
        doc.contentsChanged.connect(self._fluss_planen)
        doc.contentsChanged.connect(lambda: setattr(self, "_effekt_cache", None))
        self._effekt_cache = None
        self._fluss.start()
        doc.contentsChange.connect(self._inhalt_geaendert)
        self.apply_page(page)
        doc.setModified(False)
        doc.clearUndoRedoStacks()

    def apply_page(self, page: PageSettings) -> None:
        self.page = page
        doc = self.document()
        self.seitenfarbe_anwenden()
        bind_layout(doc, self.zoom)
        doc.setDocumentMargin(0)

        root = doc.rootFrame()
        ff: QTextFrameFormat = root.frameFormat()

        if self.web:
            for setze in (
                ff.setTopMargin,
                ff.setBottomMargin,
                ff.setLeftMargin,
                ff.setRightMargin,
            ):
                setze(mm_to_px(8))
            root.setFrameFormat(ff)
            self.setFixedWidth(max(300, int(self._web_breite)))

        else:
            # Blattmodus: Die Ränder gehören zum Blatt, nicht zum Textfluss. Das Dokument wird auf die Textfläche
            # (Breite/Höhe ohne Ränder) umbrochen; jede Qt-Seite des Flusses wird auf ein eigenes Blatt gezeichnet.
            for setze in (
                ff.setTopMargin,
                ff.setBottomMargin,
                ff.setLeftMargin,
                ff.setRightMargin,
            ):
                setze(0)
            ff.setTopMargin(page.erste_seite_versatz_px())       # lange Kopfzeile: Text der ersten Seite beginnt darunter
            root.setFrameFormat(ff)
            self.setFixedWidth(int(mm_to_px(page.width_mm) * self.zoom))
            self._sp_einrichten()

        self._blasen_einrichten()

        if self.web:
            if self.lineWrapMode() != QTextEdit.WidgetWidth:
                self.setLineWrapMode(QTextEdit.WidgetWidth)
                self._sp_timer.stop()
            doc.setPageSize(QSizeF(max(300, self._web_breite), -1))

        self._recount()
        self._passe_hoehe_an()
        self._timer.start()
        self.pageApplied.emit()

    # ---- Sprechblasen ------------------------------------------------------------------------------------------------
    class _OptAdapter:
        """Gibt `sprechblasen.konfig_lesen` die Rückrufe des Editors statt einer Settings-Klasse."""
        def __init__(self, ed):
            self.ed = ed

        def get(self, name, std=None):
            return self.ed.opt_text(name, std if isinstance(std, str) else str(std if std is not None else ""))

        def get_bool(self, name, std=False):
            return self.ed.opt(name, std)

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
        font = QFont(self.font()); font.setPixelSize(max(7, int(11 * self.zoom)))
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
        fenster = self.window()
        alt = self.kommentare.get(kid, {}).get("text", "")
        if hasattr(fenster, "befehle") and (t := fenster.befehle._text_abfragen("Kommentar bearbeiten", "Kommentar:", alt)) is not None:
            self.kommentare[kid]["text"] = t
            self.document().setModified(True)
            self._zus_geaendert()

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

    # ---- Spalten im Editor -----------------------------------------------------------------------------------------
    def _blatt_aktiv(self) -> bool:
        """Blattmodus (Drucklayout): echte Blätter mit Rand und Zwischenraum; nur das Weblayout ist ein Endlosfluss."""
        return not self.web

    def _mehrspaltig(self) -> bool:
        return (not self.web) and int(self.page.spalten) > 1

    def _sp_geo(self) -> dict:
        z, pg = self.zoom, self.page
        n = max(1, int(pg.spalten))
        gap = max(10.0, BLATT_ABSTAND_PX * z)
        return {"n": n, "cb": round(pg.spalten_breite_px * z), "g": mm_to_px(pg.spalten_abstand_mm) * z if n > 1 else 0.0,
                "ch": pg.content_height_px * z, "ml": mm_to_px(pg.margin_left_mm) * z, "mt": mm_to_px(pg.margin_top_mm) * z,
                "mb": mm_to_px(pg.margin_bottom_mm) * z,
                "H": mm_to_px(pg.height_mm) * z,              # Höhe eines Blattes
                "gap": gap,                                    # grauer Zwischenraum zwischen zwei Blättern
                "top": gap}                                    # grauer Streifen über dem ersten Blatt

    def blatt_oben(self, nr: int = 0) -> float:
        """y des oberen Randes von Blatt `nr` (0-basiert) im Editor — die Lineale richten sich danach."""
        g = self._sp_geo()
        return g["top"] + nr * (g["H"] + g["gap"])

    def _sp_ursprung(self, lp: int) -> tuple[float, float]:
        """Ecke links oben der Textspalte, in der die logische Seite `lp` des Textflusses steht (Editorkoordinaten)."""
        g = self._sp_geo()
        s, j = divmod(lp, g["n"])
        return g["ml"] + j * (g["cb"] + g["g"]), self.blatt_oben(s) + g["mt"]

    def _sp_einrichten(self) -> None:
        """Dokument in Spaltenbreite und -höhe legen: feste Zeilenbreite, damit QTextEdit die Seitenhöhe nicht wieder auf „endlos“ setzt."""
        g = self._sp_geo()
        self.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.setLineWrapColumnOrWidth(int(g["cb"]))
        self.document().setPageSize(QSizeF(g["cb"], g["ch"]))
        if self.hasFocus():
            self._sp_timer.start()

    def _sp_view(self, dx: float, dy: float) -> tuple[float, float]:
        """Dokumentkoordinate (fortlaufender Fluss der Spaltenseiten) → Punkt auf dem Blatt."""
        g = self._sp_geo()
        lp = max(0, int((dy + 1.0) // g["ch"]))        # +1: Qt gibt Rechtecke ganzzahlig, die Seitengrenze liegt meist knapp darüber
        x0, y0 = self._sp_ursprung(lp)
        return x0 + dx, y0 + max(0.0, dy - lp * g["ch"])

    def _sp_doc(self, vx: float, vy: float) -> tuple[float, float]:
        """Punkt auf dem Blatt → Dokumentkoordinate; Punkte in Rändern und Lücken landen in der nächsten Spalte."""
        g = self._sp_geo()
        s = max(0, int((vy - g["top"]) // (g["H"] + g["gap"])))
        y_in = min(max(vy - self.blatt_oben(s) - g["mt"], 0.0), g["ch"] - 1)      # Ränder und Lücken: nächste Textzeile
        j = min(g["n"] - 1, max(0, int((vx - g["ml"] + g["g"] / 2) // (g["cb"] + g["g"]))))
        dx = min(max(vx - (g["ml"] + j * (g["cb"] + g["g"])), 0.0), g["cb"])
        lp = s * g["n"] + j
        letzte = max(0, self.document().pageCount() - 1)
        if lp > letzte:
            return dx, self.document().size().height() - 1
        return dx, lp * g["ch"] + y_in

    def _sp_neu_zeichnen(self, *_) -> None:
        try:
            if self._blatt_aktiv():
                self._sp_caret = True
                self.viewport().update()
        except RuntimeError:                           # beim Abbau ist das Widget schon weg
            pass

    def _sp_blinken(self) -> None:
        if self._blatt_aktiv() and self.hasFocus():
            self._sp_caret = not self._sp_caret
            self.viewport().update()

    def focusInEvent(self, e) -> None:
        super().focusInEvent(e)
        if self._blatt_aktiv():
            self._sp_timer.start()

    def cursorRect(self, *args) -> QRect:
        r = super().cursorRect(*args)
        if self._blatt_aktiv():
            x, y = self._sp_view(r.x(), r.y())
            return QRect(int(x), int(y), r.width(), r.height())
        return r

    def cursorForPosition(self, pos: QPoint) -> QTextCursor:
        if self._blatt_aktiv():
            x, y = self._sp_doc(pos.x(), pos.y())
            pos = QPoint(int(x), int(y))
        return super().cursorForPosition(pos)

    def anchorAt(self, pos: QPoint) -> str:
        if self._blatt_aktiv():
            x, y = self._sp_doc(pos.x(), pos.y())
            pos = QPoint(int(x), int(y))
        return super().anchorAt(pos)

    def _maus_abgebildet(self, e):
        """Mausereignis mit Dokumentkoordinaten (nur bei Spalten); QTextEdit selbst rechnet in Dokumentkoordinaten."""
        if not self._blatt_aktiv():
            return e
        x, y = self._sp_doc(e.position().x(), e.position().y())
        return QMouseEvent(e.type(), QPointF(x, y), e.globalPosition(), e.button(), e.buttons(), e.modifiers())

    def mousePressEvent(self, e) -> None:
        if self._frei_maus(e, "press"):
            return
        super().mousePressEvent(self._maus_abgebildet(e))

    def _ziehen_abgebildet(self, e):
        """Ziehen/Ablegen: QTextEdit rechnet in Dokumentkoordinaten, der Editor zeigt aber Blätter → Position abbilden."""
        if not self._blatt_aktiv():
            return e
        x, y = self._sp_doc(e.position().x(), e.position().y())
        art = type(e)
        if art is QDropEvent:
            return QDropEvent(QPointF(x, y), e.possibleActions(), e.mimeData(), e.buttons(), e.modifiers())
        return QDragMoveEvent(QPoint(int(x), int(y)), e.possibleActions(), e.mimeData(), e.buttons(), e.modifiers())

    def dragMoveEvent(self, e) -> None:
        m = self._ziehen_abgebildet(e)
        super().dragMoveEvent(m)
        if m is not e:
            e.setDropAction(m.dropAction())
            e.setAccepted(m.isAccepted())

    def dropEvent(self, e) -> None:
        m = self._ziehen_abgebildet(e)
        super().dropEvent(m)
        if m is not e:
            e.setDropAction(m.dropAction())
            e.setAccepted(m.isAccepted())

    def _kopffuss_zone(self, y: float) -> str:
        """„kopf“ im oberen, „fuss“ im unteren Rand der Seite (nur Seitenansicht, nicht im Weblayout)."""
        if self.web:
            return ""
        g = self._sp_geo()
        if y < g["top"]:
            return ""
        s = int((y - g["top"]) // (g["H"] + g["gap"]))
        rel = y - self.blatt_oben(s)
        if rel > g["H"]:                                 # grauer Zwischenraum
            return ""
        if rel < g["mt"] - 4:
            return "kopf"
        if rel > g["H"] - g["mb"] + 4:
            return "fuss"
        return ""

    def mouseMoveEvent(self, e) -> None:
        if self._frei_maus(e, "move"):
            return
        zone = self._kopffuss_zone(e.position().y())
        if zone and not e.buttons() and self.opt("ui/kopffuss_tipp", True):
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(e.globalPosition().toPoint(), "Doppelklick bearbeitet die " + ("Kopfzeile" if zone == "kopf" else "Fußzeile"), self)
        super().mouseMoveEvent(self._maus_abgebildet(e))

    def mouseDoubleClickEvent(self, e) -> None:
        zone = self._kopffuss_zone(e.position().y())
        fenster = self.window()
        if zone and hasattr(fenster, "edit_header_footer"):
            fenster.edit_header_footer(zone == "kopf")
            return
        super().mouseDoubleClickEvent(self._maus_abgebildet(e))

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._blasen_geometrie()
        if self._blatt_aktiv():
            g = self._sp_geo()
            ps = self.document().pageSize()
            if abs(ps.height() - g["ch"]) > 0.5 or abs(ps.width() - g["cb"]) > 0.5:
                self.document().setPageSize(QSizeF(g["cb"], g["ch"]))

    def _arbeitsflaeche(self) -> QColor:
        """Grauer Arbeitsbereich zwischen und um die Blätter (gleich dem Grund hinter dem Editor)."""
        return self.palette().color(QPalette.Dark)

    def _blatt_zeichnen(self, e) -> None:
        """Arbeitsfläche, Blätter mit Schatten, dann Text, Auswahl, Schreibmarke und Wellenlinien: jede Seite des Textflusses
        in ihre Spalte auf ihrem Blatt."""
        vp = self.viewport()
        p = QPainter(vp)
        g = self._sp_geo()
        p.fillRect(e.rect(), self._arbeitsflaeche())
        papier = QColor(self._lese_papier or self.page.color or "white")
        sicht = QRectF(e.rect())
        for k in range(self._blatt_anzahl()):
            blatt = QRectF(0, self.blatt_oben(k), vp.width(), g["H"])
            if not blatt.adjusted(-2, -2, 6, 8).intersects(sicht):
                continue
            # weicher, mehrstufiger Schatten wie bei modernen Office-Programmen: nur nach unten, zu den Seiten hin ausblendend
            tiefe = max(4, int(9 * self.zoom))
            for i in range(tiefe, 0, -1):
                t = i / tiefe
                alpha = int(26 * (1 - t) ** 2 + 2)
                p.fillRect(QRectF(blatt.left() + i * 0.5, blatt.bottom(), blatt.width() - i, i), QColor(16, 24, 40, alpha))
            p.fillRect(blatt, papier)
        if self.page.border and not self.page.border.get("vordergrund", True):      # Seitenrahmen hinter dem Text
            from lunivo_writer.editor.pagination import seitenschmuck
            z = self.zoom
            for k in range(self._blatt_anzahl()):
                a = self.blatt_oben(k)
                if QRectF(0, a, vp.width(), g["H"]).intersects(sicht):
                    p.save(); p.scale(z, z)
                    seitenschmuck(p, self.page, False, QRectF(0, a / z, vp.width() / z, g["H"] / z), "hinten", False)
                    p.restore()
        self._frei_zeichnen(p, sicht, True)                                  # frei positionierte Bilder hinter dem Text
        doc = self.document()
        lay = doc.documentLayout()
        ctx = QAbstractTextDocumentLayout.PaintContext()
        pal = QPalette(self.palette())
        pal.setColor(QPalette.Text, QColor(self._lese_text or "black"))
        ctx.palette = pal
        auswahl = []
        for es in self.extraSelections():
            a = QAbstractTextDocumentLayout.Selection()
            a.cursor, a.format = es.cursor, es.format
            auswahl.append(a)
        c = self.textCursor()
        if c.hasSelection():
            a = QAbstractTextDocumentLayout.Selection()
            a.cursor = c
            a.format.setBackground(self.palette().highlight())
            a.format.setForeground(self.palette().highlightedText())
            auswahl.append(a)
        ctx.selections = auswahl
        ctx.cursorPosition = c.position() if (self._sp_caret and self.hasFocus() and not c.hasSelection()
                                              and not self.isReadOnly()) else -1
        for lp in range(max(1, doc.pageCount())):
            x0, y0 = self._sp_ursprung(lp)
            feld = QRectF(x0 - 6, y0, g["cb"] + 12, g["ch"])
            if not feld.intersects(sicht):
                continue
            p.save()
            p.setClipRect(feld)
            p.translate(x0, y0 - lp * g["ch"])
            ctx.clip = QRectF(-6, lp * g["ch"], g["cb"] + 12, g["ch"])
            lay.draw(p, ctx)
            p.restore()
        self._frei_zeichnen(p, sicht, False)                                 # … und davor (Foto, Unterschrift)
        p.end()

    def set_web(self, an: bool) -> None:
        if an != self.web:
            self.web = an
            self.apply_page(self.page)
            self.viewport().update()

    def set_web_breite(self, px: int) -> None:
        if px != self._web_breite:
            self._web_breite = px
            if self.web:
                self.apply_page(self.page)

    def set_gliederung(self, an: bool) -> None:
        """Gliederungsansicht: nur Überschriften sind sichtbar; der Text dazwischen ist ausgeblendet (nicht gelöscht)."""
        self.gliederung = an
        b = self.document().firstBlock()
        while b.isValid():
            b.setVisible(not an or b.blockFormat().headingLevel() > 0)
            b = b.next()
        self.document().markContentsDirty(0, self.document().characterCount())
        self.viewport().update()

    def gliederung_ebene(self, delta: int) -> None:
        """Überschrift hoch-/herabstufen (Gliederung): Ebene 1..6, darüber/darunter wird sie zu Text/Titel."""
        c = self.textCursor()
        bf = c.blockFormat()
        lv = bf.headingLevel() + delta
        if bf.headingLevel() and 1 <= lv <= 6:
            self.apply_style(f"Überschrift {lv}")

    def set_zeilennummern(self, an: bool) -> None:
        self.page.zeilennummern = an
        self.viewport().update()

    def _zeilennummern_zeichnen(self, p: QPainter) -> None:
        vp = self.viewport()
        lay = self.document().documentLayout()
        f = p.font(); f.setPixelSize(max(7, int(9 * self.zoom))); p.setFont(f)
        p.setPen(QColor("#868e96"))
        ml = mm_to_px(self.page.margin_left_mm) * self.zoom
        oben = self.verticalScrollBar().value()
        nr = 0
        b = self.document().firstBlock()
        while b.isValid():
            if b.isVisible() and b.layout() is not None:
                top = lay.blockBoundingRect(b).top()
                for i in range(b.layout().lineCount()):
                    nr += 1
                    z = b.layout().lineAt(i)
                    y = self._sp_view(0, top + z.y())[1]
                    if -20 < y < vp.height():
                        p.drawText(QRectF(ml - 52, y, 44, z.height()), Qt.AlignRight | Qt.AlignVCenter, str(nr))
            b = b.next()

    def apply_design(self, fliess: str | None = None, kopf: str | None = None, farbe: str | None = None) -> None:
        """Design: Schriftart für Text und Überschriften, Farbe der Überschriften — für das ganze Dokument."""
        doc = self.document()
        cur = QTextCursor(doc)
        cur.beginEditBlock()
        if fliess:
            f = doc.defaultFont(); f.setFamily(fliess); doc.setDefaultFont(f)
        b = doc.firstBlock()
        while b.isValid():
            kopf_block = b.blockFormat().headingLevel() > 0 or (
                b.blockFormat().hasProperty(STYLE_PROP) and b.blockFormat().property(STYLE_PROP) in ("title", "subtitle", "Title", "Subtitle"))
            fam = kopf if kopf_block and kopf else fliess
            if fam or (kopf_block and farbe):
                c = QTextCursor(b)
                c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cf = QTextCharFormat()
                if fam:
                    cf.setFontFamilies([fam])
                if kopf_block and farbe:
                    cf.setForeground(QColor(farbe))
                c.mergeCharFormat(cf)
            b = b.next()
        cur.endEditBlock()

    def set_absatzrahmen(self, wert: str | None) -> None:
        from lunivo_writer.editor.zusatz import B_RAHMEN

        def f(bf):
            if wert:
                bf.setProperty(B_RAHMEN, wert)
            else:
                bf.clearProperty(B_RAHMEN)
        self._block_merge(f)
        self.viewport().update()

    def absatzrahmen(self):
        """Der Rahmen des Absatzes an der Schreibmarke (bei Auswahl: des ersten Absatzes) als ``Linie``, sonst None."""
        from lunivo_writer.editor.linie import Linie
        from lunivo_writer.editor.zusatz import B_RAHMEN
        c = self.textCursor()
        bf = c.document().findBlock(min(c.position(), c.anchor())).blockFormat()
        return Linie.aus_text(bf.stringProperty(B_RAHMEN)) if bf.hasProperty(B_RAHMEN) else None

    def set_absatzschatten(self, fuell: str | None, muster: tuple[str, str] | None = None) -> None:
        """Füllung (und Muster darüber) der markierten Absätze; ``None`` und kein Muster nehmen sie weg."""
        from lunivo_writer.editor import muster as M
        from lunivo_writer.editor.zusatz import B_MUSTER

        def f(bf):
            bf.clearProperty(B_MUSTER)
            if muster:
                bf.setBackground(M.pinsel(muster[0], muster[1], fuell))
                bf.setProperty(B_MUSTER, M.als_text(muster[0], muster[1], fuell))
            elif fuell:
                bf.setBackground(QBrush(QColor(fuell)))
            else:
                bf.clearBackground()
        self._block_merge(f)
        self.viewport().update()

    def absatzschatten(self):
        """(Füllfarbe oder None, (Musterschlüssel, Musterfarbe) oder None) des Absatzes an der Schreibmarke."""
        from lunivo_writer.editor import muster as M
        from lunivo_writer.editor.zusatz import B_MUSTER
        c = self.textCursor()
        bf = c.document().findBlock(min(c.position(), c.anchor())).blockFormat()
        m = M.aus_text(bf.stringProperty(B_MUSTER)) if bf.hasProperty(B_MUSTER) else None
        if m:
            return m[2], (m[0], m[1])
        bg = bf.background()
        return (bg.color().name() if bg.style() != Qt.NoBrush and bg.color().isValid() else None), None

    def toggle_rtl(self) -> None:
        rtl = self.textCursor().blockFormat().layoutDirection() == Qt.RightToLeft
        self._block_merge(lambda bf: bf.setLayoutDirection(Qt.LeftToRight if rtl else Qt.RightToLeft))

    def _fluss_planen(self) -> None:
        if not self._fluss_laeuft:
            self._fluss.start()

    def _seitenfluss(self) -> None:
        """Umbruchregeln (Zusammenhalten, nicht vom nächsten Absatz trennen, Absatzkontrolle) auf die Seiten anwenden."""
        if self.web or self._fluss_laeuft:
            return
        from lunivo_writer.editor import seitenfluss
        self._fluss_laeuft = True
        try:
            if seitenfluss.anwenden(self.document(), self.page.content_height_px):
                self.viewport().update()
        finally:
            self._fluss_laeuft = False

    def _hat_effekt(self) -> bool:
        """Gibt es Textstücke mit Effekten, die Lunivo selbst zeichnet (Verlauf, Schatten, Spiegelung, Leuchten, 3D)? Das Ergebnis gilt bis zur nächsten Änderung."""
        if self._effekt_cache is not None:
            return self._effekt_cache
        from lunivo_writer.editor.textfx import hat_zeichen_effekt
        gefunden = False
        b = self.document().firstBlock()
        while b.isValid() and not gefunden:
            it = b.begin()
            while not it.atEnd():
                if hat_zeichen_effekt(it.fragment().charFormat()):
                    gefunden = True; break
                it += 1
            b = b.next()
        self._effekt_cache = gefunden
        return gefunden

    def _hat_tabfuell(self) -> bool:
        from lunivo_writer.editor.zusatz import B_TABFUELL
        b = self.document().firstBlock()
        while b.isValid():
            if b.blockFormat().hasProperty(B_TABFUELL):
                return True
            b = b.next()
        return False

    def _hat_mehrstufig(self) -> bool:
        from lunivo_writer.editor.zusatz import B_MEHRSTUFIG
        b = self.document().firstBlock()
        while b.isValid():
            if b.blockFormat().hasProperty(B_MEHRSTUFIG):
                return True
            b = b.next()
        return False

    def _hat_rahmen(self) -> bool:
        from lunivo_writer.editor.zusatz import B_RAHMEN
        b = self.document().firstBlock()
        while b.isValid():
            if b.blockFormat().hasProperty(B_RAHMEN):
                return True
            b = b.next()
        return False

    def set_gitter(self, an: bool) -> None:
        self.gitter = an
        self.viewport().update()

    def seitenspannen(self) -> list[tuple[int, int]]:
        """Senkrechte Bereiche (von, bis) jedes Blattes im Editor."""
        if self.web:
            h = self.viewport().height() + self.verticalScrollBar().value()
            return [(0, max(h, int(self.document().size().height())))]
        g = self._sp_geo()
        return [(int(self.blatt_oben(k)), int(self.blatt_oben(k) + g["H"])) for k in range(self._blatt_anzahl())]

    def _schmuck_zeichnen(self, p: QPainter) -> None:
        pg, z = self.page, self.zoom
        if self.web or not (pg.border or pg.watermark):
            return
        from lunivo_writer.editor.pagination import seitenschmuck
        vp = self.viewport()
        for a, b in self.seitenspannen():
            if b < 0 or a > vp.height():
                continue
            p.save()
            p.scale(z, z)
            seitenschmuck(p, pg, False, QRectF(0, a / z, vp.width() / z, (b - a) / z), "vorn")
            p.restore()

    def _gitter_zeichnen(self, p: QPainter) -> None:
        vp = self.viewport()
        schritt = mm_to_px(10) * self.zoom
        if schritt < 6:
            return
        c = QColor("#868e96"); c.setAlpha(70)
        p.setPen(QPen(c, 1))
        x = schritt
        while x < vp.width():
            p.drawLine(int(x), 0, int(x), vp.height()); x += schritt
        y = schritt
        while y < vp.height():
            p.drawLine(0, int(y), vp.width(), int(y)); y += schritt

    def seitenfarbe_anwenden(self) -> None:
        c = self.page.color or "white"
        # der Rahmen hat die Farbe der Arbeitsfläche: um das Blatt herum ist kein Strich zu sehen
        self.setStyleSheet("QTextEdit { background: palette(dark); color: black; border: none; }")

    ZOOM_MIN, ZOOM_MAX = 0.1, 5.0

    def set_zoom(self, faktor: float) -> None:
        """Ansicht vergrößern/verkleinern. Das Dokument selbst (Schriftgrößen, Maße) bleibt unverändert."""
        faktor = max(self.ZOOM_MIN, min(self.ZOOM_MAX, round(faktor, 3)))
        if abs(faktor - self.zoom) < 1e-6:
            return
        self.zoom = faktor
        self.apply_page(self.page)
        self.viewport().update()
        self.zoomChanged.emit(faktor)

    def wheelEvent(self, e) -> None:
        if e.modifiers() & Qt.ControlModifier:
            self.set_zoom(self.zoom * (1.1 if e.angleDelta().y() > 0 else 1 / 1.1))
            e.accept()
            return
        e.ignore()                      # die Seite scrollt im grauen Grund

    def page_settings_changed(self, page: PageSettings) -> None:
        """Seiteneinrichtung ändern — für den Abschnitt, in dem die Schreibmarke steht (der erste Abschnitt ist das Dokument)."""
        from lunivo_writer.editor import abschnitte as AB
        nr = self.abschnitt_nr()
        if nr > 0 and AB.setzen(self.document(), nr, page):
            self._recount()
            self.viewport().update()
        else:
            self.apply_page(page)
        self.document().setModified(True)

    # ---- Abschnitte ----------------------------------------------------------------------------------------------------
    def abschnitt_nr(self) -> int:
        from lunivo_writer.editor import abschnitte as AB
        return AB.index_bei(self.document(), self.textCursor().position())

    def abschnitt_seite(self, nr: int | None = None) -> PageSettings:
        """Kopie der Einrichtung des Abschnitts `nr` (Vorgabe: des aktuellen)."""
        from lunivo_writer.editor import abschnitte as AB
        return AB.einrichtung(self.document(), self.page, self.abschnitt_nr() if nr is None else nr)

    def abschnitt_einfuegen(self, typ: str = "naechste") -> int:
        from lunivo_writer.editor import abschnitte as AB
        c = self.textCursor()
        nr = AB.einfuegen(self.document(), c, typ, self.page)
        self.setTextCursor(c)
        self.document().setModified(True)
        self._recount()
        return nr

    def abschnitt_entfernen(self) -> bool:
        from lunivo_writer.editor import abschnitte as AB
        ok = AB.entfernen(self.document(), self.abschnitt_nr())
        if ok:
            self.document().setModified(True)
            self._recount()
            self.viewport().update()
        return ok

    def abschnitt_gehe(self, nr: int) -> bool:
        from lunivo_writer.editor import abschnitte as AB
        n = AB.anzahl(self.document())
        if not 0 <= nr < n:
            return False
        c = self.textCursor()
        c.setPosition(AB.beginn(self.document(), nr))
        self.setTextCursor(c)
        self.ensureCursorVisible()
        return True

    # ---- Seitenzählung & Echte Paginierung ----------------------------------
    def _recount(self) -> None:
        """Seitenzahl und Seitenwechsel neu bestimmen. Die Blätter selbst entstehen aus dem Textfluss des Editors; die
        Druckkopie liefert Seitenwechsel für „Gehe zu“ und die Seiten, die erst der Druck anhängt (Endnoten)."""
        live = self._blatt_anzahl() - self._extra_seiten
        if self.web:
            self._paged, self._breaks, self._pages, self._extra_seiten = None, [], 1, 0
        elif self._mehrspaltig():                      # die Spaltenseiten stammen aus dem Editor-Dokument selbst
            self._paged = None
            self._breaks = []
            self._pages = live
            self._extra_seiten = 0
        else:
            self._paged = paginated_copy(self.document(), self.page, self.noten, silben=False, einspaltig=True, versteckt=self.versteckt_zeigen)
            self._breaks = self._seitenwechsel(self._paged)
            druck = max(1, self._paged.pageCount())
            from lunivo_writer.editor import abschnitte as AB
            if AB.anzahl(self.document()) > 1:
                from lunivo_writer.editor.pagination import seitenzahl
                druck = max(1, seitenzahl(self.document(), self.page, self.noten))
            self._extra_seiten = max(0, druck - live)
            self._pages = live + self._extra_seiten
        self._passe_hoehe_an()
        self.viewport().update()
        self._cursor_moved()

    def _seitenwechsel(self, d: QTextDocument) -> list[int]:
        """Zeichenstellen, an denen eine neue Seite beginnt (erste Zeile der Seiten 2, 3, …)."""
        ch = self.page.content_height_px
        lay = d.documentLayout()
        stellen, seite = [], 0
        b = d.firstBlock()
        while b.isValid():
            tl = b.layout()
            if tl is not None and tl.lineCount():
                top = lay.blockBoundingRect(b).top()
                for i in range(tl.lineCount()):
                    ln = tl.lineAt(i)
                    k = int((top + ln.y() + 0.5) // ch)
                    if k > seite:
                        seite = k
                        stellen.append(b.position() + ln.textStart())
            b = b.next()
        return stellen

    @property
    def seitenwechsel(self) -> list[int]:
        return list(self._breaks)

    @property
    def page_count(self) -> int:
        return self._pages

    def current_page(self) -> int:
        """Blatt, auf dem die Schreibmarke steht (so, wie es im Editor angezeigt wird)."""
        if self.web:
            return 1
        g = self._sp_geo()
        r = QTextEdit.cursorRect(self)
        return max(1, min(self._pages, int((r.y() + 1.0) // g["ch"]) // g["n"] + 1))

    def _cursor_moved(self) -> None:
        try:
            self.pageInfoChanged.emit(self.current_page(), self._pages)
            self.formatChanged.emit()
        except RuntimeError:                           # beim Abbau ist das Widget schon weg
            return
        if self.opt_text("ui/feldschattierung", "Bei Auswahl") == "Bei Auswahl":
            self._zus_timer.start()
        hl = getattr(self, "_silben", None)
        if hl is not None and hl.k["nur_absatz"]:
            neu = self.textCursor().blockNumber()
            if neu != getattr(self, "_silben_block", -1):
                for n in (getattr(self, "_silben_block", -1), neu):
                    b = self.document().findBlockByNumber(n)
                    if b.isValid():
                        hl.rehighlightBlock(b)
                self._silben_block = neu

    def set_silbenfarben(self, konfig: dict | None) -> None:
        """Silben farbig (reine Anzeige, ändert das Dokument nicht); konfig None oder an=False schaltet ab."""
        from lunivo_writer.editor.silbenfarben import SilbenFarben
        hl = getattr(self, "_silben", None)
        if not konfig or not konfig["an"]:
            if hl is not None:
                hl.setDocument(None)
                self._silben = None
            return
        if hl is None:
            self._silben_block = self.textCursor().blockNumber()
            self._silben = SilbenFarben(self.document(), konfig, lambda: self.textCursor().blockNumber())
        else:
            hl.neu_konfigurieren(konfig)

    def word_count(self) -> int:
        return len(self.document().toPlainText().split())

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
        f.setTextOutline(QPen(QColor("#000000")) if an else QPen(Qt.NoPen))
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
                bf.setBackground(M.pinsel(d["muster"], d.get("musterfarbe") or "#000000", fuell))
                bf.setProperty(B_MUSTER, M.als_text(d["muster"], d.get("musterfarbe") or "#000000", fuell))
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
            cur.insertText(repl)
            return True
        return False

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
            found.insertText(repl)
            pos = found.position()
            n += 1
        cur.endEditBlock()
        return n

    # ---- Bilder im Text (Bildtools) -------------------------------------------------------------------
    def _bild_cursor(self):
        c = self.textCursor()
        if c.charFormat().isImageFormat() and c.hasSelection():
            return c
        # Zeiger direkt vor einem Bild?
        c2 = QTextCursor(c)
        c2.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        if c2.charFormat().isImageFormat():
            return c2
        return None

    def bild_format(self):
        c = self._bild_cursor()
        return c.charFormat().toImageFormat() if c is not None else None

    def bild_setzen(self, width=None, height=None, alt=None) -> None:
        c = self._bild_cursor()
        if c is None:
            return
        f = c.charFormat().toImageFormat()
        if width is not None:
            f.setWidth(width)
        if height is not None:
            f.setHeight(height)
        if alt is not None:
            f.setProperty(STYLE_PROP + 1, alt)
        c.setCharFormat(f)

    def contextMenuEvent(self, e) -> None:
        from lunivo_writer.ui.widgets.kontextmenue import menue_bauen
        fenster = self.window()
        m = menue_bauen(self, fenster) if hasattr(fenster, "befehle") else self.createStandardContextMenu()
        if self.kontext_hook is not None:
            pos = self.cursorForPosition(e.pos()).position()
            self.kontext_hook(m, pos)
        from lunivo_writer.editor import bildlayout as BL
        if BL.ziel(self) is not None and not self.isReadOnly():
            m.addSeparator()
            m.addAction("Layout …", self.bild_layout_dialog)
        if self._bild_cursor() is not None and not self.isReadOnly():
            from lunivo_writer.editor import umbruch as U
            m.addSeparator()
            c = self._bild_cursor()
            aktuell = U.schwebend(self.document(), c.selectionStart()) or "zeile"
            for modus, text in (("zeile", "Bild: mit Text in Zeile"), ("links", "Bild: links, Text umfließt"),
                                ("rechts", "Bild: rechts, Text umfließt"),
                                ("oben_unten", "Bild: oben und unten (eigene Zeile)")):
                a = m.addAction(text, lambda _=False, modus=modus: U.umbruch_setzen(self, modus))
                a.setCheckable(True)
                a.setChecked(modus == aktuell)
        if self.textCursor().hasSelection() and not self.isReadOnly():
            m.addSeparator()
            a = m.addAction("Ausgeblendeter Text", lambda: self.set_versteckt(not self.ist_versteckt()))
            a.setCheckable(True)
            a.setChecked(self.ist_versteckt())
        ki = getattr(self.window(), "ki", None)
        if ki is not None and self.textCursor().hasSelection() and not self.isReadOnly():
            m.addSeparator()
            m.addAction("KI: Text in Bild", ki.bild_aus_text)
            aktionen = [a for a in ki.konfig["assistenten"] if a.get("zugriff", "kontext") == "kontext"]
            if aktionen:
                sub = m.addMenu("KI-Aktionen")
                for a in aktionen:
                    sub.addAction(a["name"], lambda _=False, a=a: ki.assistent(a))
        mini = self.mini_hook is not None and self.opt("ui/mini_rechtsklick", True) and not self.isReadOnly()
        if mini:
            self.mini_hook(self, e.globalPos(), True)
        m.exec(e.globalPos())
        m.deleteLater()
        if mini:
            self.mini_hook(None, None, True)

    def _wortweise(self) -> None:
        """Wortweise markieren: eine mit der Maus gezogene Auswahl wird an Wortgrenzen erweitert."""
        c = self.textCursor()
        von, bis = c.selectionStart(), c.selectionEnd()
        if bis - von < 2 or c.selectedText() in ("\u2029",):
            return
        a = QTextCursor(self.document()); a.setPosition(von); a.movePosition(QTextCursor.StartOfWord)
        b = QTextCursor(self.document()); b.setPosition(bis)
        if not b.atBlockEnd() and b.positionInBlock() > 0 and self.document().characterAt(bis - 1).isalnum():
            b.movePosition(QTextCursor.EndOfWord)
        neu = QTextCursor(self.document())
        rueckwaerts = c.position() < c.anchor()
        neu.setPosition(b.position() if rueckwaerts else a.position())
        neu.setPosition(a.position() if rueckwaerts else b.position(), QTextCursor.KeepAnchor)
        self.setTextCursor(neu)

    def _cursor_at(self, pos: int) -> QTextCursor:
        c = QTextCursor(self.document())
        c.setPosition(pos)
        return c

    def mouseReleaseEvent(self, e) -> None:
        if self._frei_maus(e, "release"):
            return
        if e.button() == Qt.MiddleButton and not self.opt("bearbeiten/mittlere_taste", True):
            e.accept()                                  # mittlere Maustaste fügt nichts ein (Optionen ▸ Bearbeiten)
            return
        super().mouseReleaseEvent(self._maus_abgebildet(e))
        if e.button() == Qt.LeftButton and self.opt("bearbeiten/wortweise", True) and self.textCursor().hasSelection():
            self._wortweise()
        if (e.button() == Qt.LeftButton and self.mini_hook is not None and self.textCursor().hasSelection()
                and not self.isReadOnly() and self.opt("ui/mini_auswahl", True) and not self._bild_cursor()):
            c = QTextCursor(self.textCursor())
            c.setPosition(c.selectionStart())
            self.mini_hook(self, self.viewport().mapToGlobal(self.cursorRect(c).topLeft()), False)
        if (e.modifiers() & Qt.ControlModifier) and self.opt("ui/strg_klick_link", True):
            href = self.anchorAt(e.pos())
            if href and href.startswith("#"):
                from lunivo_writer.editor.verweise import intern_springen
                intern_springen(self, href)
                return
            if href:
                from PySide6.QtCore import QUrl as _U
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(_U(href))
                return
        if e.button() == Qt.LeftButton and not self.textCursor().hasSelection() and not self.isReadOnly():
            from lunivo_writer.editor.sendungen import kasten_umschalten
            from lunivo_writer.editor import formular as FO
            pos = self.cursorForPosition(e.pos()).position()
            if FO.klick(self, pos, self.window()) or kasten_umschalten(self, pos):
                return
        c = self.cursorForPosition(e.pos())
        c2 = QTextCursor(c)
        c2.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        if c2.charFormat().isImageFormat() and not self.textCursor().hasSelection():
            r = self.cursorRect(c)
            if abs(e.pos().x() - r.x()) < c2.charFormat().toImageFormat().width() + 2:
                self.setTextCursor(c2)

    # ---- Anzeige: Zeilenfokus, Eckmarken, Lesehilfe --------------------------------------------------
    def set_zeilenfokus(self, an: bool) -> None:
        self.zeilenfokus = an
        self.viewport().update()

    def set_marken(self, an: bool) -> None:
        self.marken = an
        self.viewport().update()

    def set_lesehilfe(self, papier: str, buchstaben: float, wort: float) -> None:
        pk = QColor(papier) if papier else QColor()
        text_farbe = "black" if (not pk.isValid() or pk.lightness() >= 128) else "#ffffff"
        self._lese_papier = papier if pk.isValid() and papier.lower() not in ("white", "#ffffff") else ""
        self._lese_text = text_farbe if self._lese_papier else ""
        self.setStyleSheet(f"QTextEdit {{ background: {papier or 'white'}; color: {text_farbe}; border: none; }}")
        self.viewport().update()
        f = QFont(self.document().defaultFont())
        f.setLetterSpacing(QFont.AbsoluteSpacing, buchstaben)
        f.setWordSpacing(wort)
        self.document().setDefaultFont(f)

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
        papier = QColor(self._lese_papier or "#ffffff")
        text = QColor(self._lese_text or "#000000")
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

    def paintEvent(self, e) -> None:
        sp = self._blatt_aktiv()
        if sp:
            self._blatt_zeichnen(e)
        else:
            super().paintEvent(e)
        
        vp = self.viewport()
        p = QPainter(vp)

        is_dark = self.palette().color(QPalette.Window).lightness() < 128
        line_color = QColor("#adb5bd") if is_dark else QColor("#868e96")
        accent_color = QColor("#748ffc") if is_dark else QColor("#4c6ef5")
        strip_color = QColor("#2b2d30") if is_dark else QColor("#d9dee5")

        self._schmuck_zeichnen(p)
        if self.gitter:
            self._gitter_zeichnen(p)
        if not self.web and (self._hat_rahmen() or self._hat_mehrstufig() or self._hat_tabfuell() or self._hat_effekt()):
            from lunivo_writer.editor.pagination import absatz_zusatz_zeichnen
            if sp:
                g = self._sp_geo()
                for lp in range(max(1, self.document().pageCount())):
                    x0, y0 = self._sp_ursprung(lp)
                    p.save()
                    p.setClipRect(QRectF(x0 - 6, y0, g["cb"] + 12, g["ch"]))
                    p.translate(x0, y0 - lp * g["ch"])
                    absatz_zusatz_zeichnen(p, self.document(), self.zoom)
                    p.restore()
            else:
                p.save()
                p.translate(0, -self.verticalScrollBar().value())
                absatz_zusatz_zeichnen(p, self.document(), self.zoom)
                p.restore()
        if self.page.zeilennummern and not self.web and not self._mehrspaltig():
            self._zeilennummern_zeichnen(p)
        if self.marken and not self.web:
            g = self._sp_geo()
            L = 14
            p.setPen(QPen(line_color, 1))
            for k in range(self._blatt_anzahl()):
                oben = int(self.blatt_oben(k) + g["mt"])
                unten = int(self.blatt_oben(k) + g["H"] - g["mb"])
                # Eckmarken liegen außerhalb der Textfläche und zeigen von ihrer Ecke nach außen (wie in Word)
                for x, ox in ((int(g["ml"]), -1), (int(g["ml"] + g["cb"] * g["n"] + g["g"] * (g["n"] - 1)), 1)):
                    for y, oy in ((oben, -1), (unten, 1)):
                        p.drawLine(x, y, x + ox * L, y)
                        p.drawLine(x, y, x, y + oy * L)
        self._extras_zeichnen(p, sp)
        if sp and self._mehrspaltig() and self.page.spalten_linie:
            g = self._sp_geo()
            p.setPen(QPen(line_color, 1))
            for k in range(self._blatt_anzahl()):
                for j in range(1, g["n"]):
                    x = int(g["ml"] + j * (g["cb"] + g["g"]) - g["g"] / 2)
                    y0 = self.blatt_oben(k) + g["mt"]
                    p.drawLine(x, int(y0), x, int(y0 + g["ch"]))

        if self.zeilenfokus and self.hasFocus() and not self.textCursor().hasSelection():
            r = self.cursorRect()
            zeile = QRect(0, r.top() - 1, vp.width(), r.height() + 2)
            dunkel = QColor(self.palette().color(self.viewport().backgroundRole()))
            dunkel.setAlpha(170)
            p.setPen(Qt.NoPen)
            p.setBrush(dunkel)
            p.drawRect(QRect(0, 0, vp.width(), zeile.top()))
            p.drawRect(QRect(0, zeile.bottom() + 1, vp.width(), vp.height()))
        p.end()
        self._lese_wachstum_zeichnen()

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
        line_color = QColor("#adb5bd") if is_dark else QColor("#868e96")
        accent_color = QColor("#748ffc") if is_dark else QColor("#4c6ef5")

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
                p.setPen(QPen(QColor("#ff6b6b") if is_dark else QColor("#c92a2a"), 1.6))
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

    # ---- Schreibhilfe: Wellenlinien, Ersetzen, Vorhersage, AutoKorrektur -------------------
    WELLE = {"fehler": "#e8590c", "tipp": "#1c7ed6", "hinweis": "#868e96"}

    def cut(self) -> None:
        if self.verfolgen and self.textCursor().hasSelection():
            self.copy()
            c = self.textCursor()
            self._loesche_verfolgt(c.selectionStart(), c.selectionEnd(), ende=True)
            return
        super().cut()

    def set_wellen(self, funde: list) -> None:
        self._wellen = funde
        self._overlays_neu()

    def replace_range(self, von: int, bis: int, neu: str, erwartet: str | None = None) -> bool:
        c = QTextCursor(self.document())
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        if erwartet is not None and c.selectedText().replace("\u2029", "\n") != erwartet:
            return False
        fmt = QTextCharFormat(c.charFormat())
        c.insertText(neu, fmt) if neu else c.removeSelectedText()
        return True

    def select_range(self, von: int, bis: int) -> None:
        c = QTextCursor(self.document())
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        self.setTextCursor(c); self.ensureCursorVisible(); self.setFocus()

    def _wort_vor_cursor(self) -> str:
        c = self.textCursor()
        txt = c.block().text()[:c.positionInBlock()]
        i = len(txt)
        while i > 0 and (txt[i - 1].isalpha() or txt[i - 1] in "äöüßÄÖÜ"):
            i -= 1
        return txt[i:]

    def _vorschlaege_zeigen(self) -> None:
        if not self.vorhersage or self.textCursor().hasSelection():
            self._popup.hide(); return
        w = self._wort_vor_cursor()
        vs = self.vorhersage(w) if len(w) >= 3 else []
        if not vs:
            self._popup.hide(); return
        gross = w[:1].isupper()
        self._popup.clear()
        for i, v in enumerate(vs, start=1):
            wort = v.capitalize() if gross else v
            it = QListWidgetItem(f"{i}  {wort}" if i <= 6 else wort)
            it.setData(Qt.UserRole, wort)
            self._popup.addItem(it)
        self._popup.setCurrentRow(0)
        r = self.cursorRect()
        self._popup.resize(220, min(200, 22 * len(vs) + 6))
        self._popup.move(self.viewport().mapToGlobal(QPoint(r.left(), r.bottom() + 4)))
        self._popup.show()

    def _vorschlag_nehmen(self, wort: str) -> None:
        w = self._wort_vor_cursor()
        c = self.textCursor()
        c.beginEditBlock()
        c.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(w))
        c.insertText(wort + " ")
        c.endEditBlock()
        self.setTextCursor(c); self._popup.hide()

    def _autokorr_anwenden(self) -> None:
        if not self.autokorr:
            return
        c = self.textCursor()
        if c.hasSelection():
            return
        alt = c.block().text()[:c.positionInBlock()]
        neu = self.autokorr(alt)
        if neu == alt:
            return
        von, bis, ersatz = kleinste_aenderung(alt, neu)
        start = c.block().position()
        ed = QTextCursor(self.document())
        ed.setPosition(start + von); ed.setPosition(start + bis, QTextCursor.KeepAnchor)
        fmt = QTextCharFormat(ed.charFormat())
        ed.insertText(ersatz, fmt) if ersatz else ed.removeSelectedText()
        end = QTextCursor(self.document())
        end.setPosition(start + len(neu))
        self.setTextCursor(end)

    def keyPressEvent(self, e) -> None:
        if self._frei_taste(e):
            return
        folge = self._folge_vorher(e)
        self._taste(e)
        if folge:
            self._folge_danach(*folge)

    def _folge_vorher(self, e):
        """Return am Ende eines Absatzes, dessen Vorlage einen „folgenden Absatz“ kennt → (Name der Folgevorlage, Absatznummer)."""
        if e.key() not in (Qt.Key_Return, Qt.Key_Enter) or self.isReadOnly() or (e.modifiers() & ~Qt.KeypadModifier):
            return None
        c = self.textCursor()
        if c.hasSelection() or not c.atBlockEnd() or c.currentTable():
            return None
        name = self._stil_name(c.blockFormat())
        folge = stile.definition(name).get("folge") if name else None
        return (folge, c.blockNumber()) if folge and folge != name else None

    def _folge_danach(self, folge: str, nr: int) -> None:
        c = self.textCursor()
        if c.blockNumber() == nr + 1:                                   # der neue Absatz bekommt die Folgevorlage
            self._stil_auf_block(c.block(), folge)

    def _taste(self, e) -> None:
        if e.key() == Qt.Key_Tab and e.modifiers() == Qt.NoModifier and not self.isReadOnly() and not self.textCursor().currentTable():
            from lunivo_writer.editor.vorlagen import naechste_luecke
            ziel = naechste_luecke(self.document(), self.textCursor().selectionEnd())
            if ziel:
                self.select_range(*ziel)
                return
        if self.verfolgen and not self.isReadOnly() and self._verfolgte_taste(e):
            return
        if self.gliederung and (e.modifiers() & Qt.AltModifier) and (e.modifiers() & Qt.ShiftModifier) \
                and e.key() in (Qt.Key_Left, Qt.Key_Right):
            self.gliederung_ebene(-1 if e.key() == Qt.Key_Left else 1)
            return
        if self._popup.isVisible():
            k = e.key()
            if k in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter):
                it = self._popup.currentItem()
                if it:
                    self._vorschlag_nehmen(it.data(Qt.UserRole)); e.accept(); return
            if (e.modifiers() & Qt.ControlModifier) and Qt.Key_1.value <= k <= Qt.Key_6.value:        # Strg+1…6: Vorschlag nehmen
                n = k - Qt.Key_1.value
                if n < self._popup.count():
                    self._vorschlag_nehmen(self._popup.item(n).data(Qt.UserRole)); e.accept(); return
            if k == Qt.Key_Escape:
                self._popup.hide(); e.accept(); return
            if k in (Qt.Key_Down, Qt.Key_Up):
                r = self._popup.currentRow() + (1 if k == Qt.Key_Down else -1)
                self._popup.setCurrentRow(max(0, min(self._popup.count() - 1, r))); e.accept(); return
        c0 = self.textCursor()
        k = e.key()
        # Tab/Rücktaste setzen den Einzug (nur am Absatzanfang)
        if self.opt("schreibhilfe/akTabEinzug", True) and not c0.hasSelection() and c0.atBlockStart() \
                and not c0.currentList() and k in (Qt.Key_Tab, Qt.Key_Backspace):
            bf = c0.blockFormat()
            if k == Qt.Key_Tab:
                self.change_indent(10); e.accept(); return
            if bf.leftMargin() > 0:
                self.change_indent(-10); e.accept(); return
        # Tippen ersetzt die Auswahl — ist das abgeschaltet, wird hinter die Auswahl geschrieben
        if c0.hasSelection() and e.text() and e.text().isprintable() and not (e.modifiers() & (Qt.ControlModifier | Qt.AltModifier)) \
                and not self.opt("bearbeiten/tippen_ersetzt", True):
            c0.setPosition(max(c0.anchor(), c0.position())); self.setTextCursor(c0)
        if k in (Qt.Key_Return, Qt.Key_Enter) and self.opt("schreibhilfe/akRechtsLeer", False) and not c0.hasSelection() \
                and (c0.blockFormat().alignment() & Qt.AlignRight):
            self._rechts_leerzeichen_weg(c0)
        super().keyPressEvent(e)
        t = e.text()
        if t == ")" and self.opt("schreibhilfe/akKreiszahl", False):
            self._kreiszahl()
        if t == " " and self.opt("autoformat/liste", True):
            self._autoformat_liste()
        if t and t in " .,;:!?\n\r":
            self._popup.hide()
            self._autokorr_anwenden()
            if t == " ":
                self._autokorr_extras()
        elif t and (t.isalpha() or e.key() == Qt.Key_Backspace):
            self._vorschlaege_zeigen()
        else:
            self._popup.hide()

    def _rechts_leerzeichen_weg(self, c: QTextCursor) -> None:
        """AutoKorrektur: Leerzeichen am Ende einer rechtsbündigen Zeile würden den Text nach links schieben — sie werden entfernt."""
        b = c.block()
        roh = b.text()
        ohne = roh.rstrip(" \t")
        if ohne != roh:
            k = QTextCursor(self.document())
            k.setPosition(b.position() + len(ohne)); k.setPosition(b.position() + len(roh), QTextCursor.KeepAnchor)
            k.removeSelectedText()

    def _kreiszahl(self) -> None:
        """AutoKorrektur: „(1)“ … „(20)“ werden zu ① … ⑳ (Optionen ▸ Bearbeiten ▸ AutoKorrektur)."""
        c = self.textCursor()
        vor = c.block().text()[:c.positionInBlock()]
        import re as _re
        m = _re.search(r"\((\d{1,2})\)$", vor)
        if m and 1 <= int(m.group(1)) <= 20:
            k = QTextCursor(self.document())
            k.setPosition(c.block().position() + m.start()); k.setPosition(c.block().position() + m.end(), QTextCursor.KeepAnchor)
            k.insertText(chr(0x2460 + int(m.group(1)) - 1))

    def _autoformat_liste(self) -> None:
        """„1. “ / „1) “ am Absatzanfang → Nummerierung, „* “ / „- “ / „• “ → Aufzählung."""
        c = self.textCursor()
        if c.hasSelection() or c.currentList():
            return
        vor = c.block().text()[:c.positionInBlock()]
        import re as _re
        art = None
        if _re.fullmatch(r"\d{1,3}[.)] ", vor):
            art = "number"
        elif vor in ("* ", "- ", "• ") and self.opt("autoformat/punkte", True):
            art = "bullet"
        if art == "number" and not self.opt("autoformat/liste", True):
            return
        if art:
            c.beginEditBlock()
            c.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
            c.removeSelectedText()
            self.toggle_list(art)
            c.endEditBlock()

    def _autokorr_extras(self) -> None:
        """Netzadressen → Hyperlinks; Leerzeichen am Absatzanfang → Erstzeileneinzug."""
        c = self.textCursor()
        if c.hasSelection():
            return
        vor = c.block().text()[:c.positionInBlock()]
        import re as _re
        if self.opt("schreibhilfe/akPfade", True):
            m = _re.search(r"(https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.-]+)[ ]$", vor)
            if m:
                start = c.block().position() + m.start(1)
                end = c.block().position() + m.end(1)
                url = m.group(1)
                href = url if _re.match(r"https?://", url) else ("mailto:" + url if "@" in url else "http://" + url)
                cc = QTextCursor(self.document()); cc.setPosition(start); cc.setPosition(end, QTextCursor.KeepAnchor)
                f = QTextCharFormat(); f.setAnchor(True); f.setAnchorHref(href)
                f.setForeground(QBrush(QColor("#0563C1"))); f.setFontUnderline(True)
                cc.mergeCharFormat(f)
        if self.opt("schreibhilfe/akErstzeile", False) and _re.fullmatch(r"[ \t]{3,}", vor):
            cc = QTextCursor(self.document()); cc.setPosition(c.block().position())
            cc.setPosition(c.block().position() + len(vor), QTextCursor.KeepAnchor); cc.removeSelectedText()
            bf = QTextCursor(c.block()).blockFormat(); bf.setTextIndent(mm_to_px(10))
            QTextCursor(self.document().findBlock(c.block().position())).setBlockFormat(bf)

    def focusOutEvent(self, e) -> None:
        try:
            self._popup.hide()
        except RuntimeError:          # beim Beenden schon abgebaut
            pass
        super().focusOutEvent(e)

    # ---- Tastatur ----------------------------------------------------------------
    def insertFromMimeData(self, source) -> None:
        if source.hasImage() and not source.hasHtml():
            img = QImage(source.imageData())
            if not img.isNull():
                name = f"einfuegen-{self.document().revision()}"
                self.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
                f = QTextImageFormat(); f.setName(name)
                f.setWidth(min(img.width(), self.page.content_width_px)); f.setHeight(
                    img.height() * min(1.0, self.page.content_width_px / max(1, img.width())))
                self.textCursor().insertImage(f)
                return
        modus = self.opt_text("bearbeiten/einfuegen_standard", EINFUEGE_MODI[0])
        if not isinstance(modus, str) or modus not in EINFUEGE_MODI:
            modus = EINFUEGE_MODI[0]
        self._einfuegen_mit(source, modus, neu=True)

    def _einfuegen_mit(self, source, modus: str, neu: bool) -> None:
        """Einfügen als EIN Rückgängig-Schritt; danach bietet die kleine Schaltfläche die anderen Formen an (Optionen ▸ Bearbeiten)."""
        c = self.textCursor()
        c.beginEditBlock()
        start = c.selectionStart()
        c.removeSelectedText()
        if modus == "Nur Text" or not source.hasHtml():
            c.insertText(source.text() if source.hasText() else "")
        elif modus == "Zielformatierung verwenden":
            c.insertFragment(_ziel_fragment(source.html(), self.document().defaultFont()))
        else:
            c.insertFragment(QTextDocumentFragment.fromHtml(source.html()))
        ende = c.position()
        c.endEditBlock()
        self.setTextCursor(c)
        if neu and self.opt("bearbeiten/einfuegen_schaltflaeche", True) and ende > start and not self.isReadOnly():
            kopie = QMimeData()
            for f in source.formats():
                kopie.setData(f, source.data(f))
            self._einfuegen_schaltflaeche(kopie, start, ende, modus)

    def _einfuegen_schaltflaeche(self, quelle, start: int, ende: int, modus: str) -> None:
        from PySide6.QtWidgets import QMenu, QToolButton
        b = getattr(self, "_paste_btn", None)
        if b is None:
            b = self._paste_btn = QToolButton(self.viewport())
            b.setText("Einfügen ▾")
            b.setCursor(Qt.ArrowCursor)
            b.setPopupMode(QToolButton.InstantPopup)
            b.setStyleSheet("QToolButton { border: 1px solid palette(mid); border-radius: 4px; padding: 2px 6px; "
                            "background: palette(window); font-size: 8pt; }")
            self.cursorPositionChanged.connect(self._paste_btn_pruefen)
        self._paste_ende = ende
        m = QMenu(b)
        for name in EINFUEGE_MODI:
            a = m.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == modus)
            a.triggered.connect(lambda _=False, name=name: self._einfuegen_neu(quelle, start, name))
        b.setMenu(m)
        c = QTextCursor(self.document()); c.setPosition(ende)
        r = self.cursorRect(c)
        b.move(max(0, r.left()), r.bottom() + 2)
        b.adjustSize()
        b.show()

    def _einfuegen_neu(self, quelle, start: int, modus: str) -> None:
        c = QTextCursor(self.document())
        c.setPosition(start)
        c.setPosition(self._paste_ende, QTextCursor.KeepAnchor)
        self.setTextCursor(c)
        self._paste_btn.hide()
        self._einfuegen_mit(quelle, modus, neu=False)
        self._einfuegen_schaltflaeche(quelle, start, self.textCursor().position(), modus)

    def _paste_btn_pruefen(self) -> None:
        b = getattr(self, "_paste_btn", None)
        if b is not None and b.isVisible() and self.textCursor().position() != getattr(self, "_paste_ende", -1):
            b.hide()
