"""Frei positionierte Bilder im Editor: zeichnen, anklicken, verschieben, in der Größe ändern, löschen (siehe editor/freie_bilder.py).

Ein Klick auf ein Bild vor dem Text wählt es aus (Strg+Alt+Klick: auch eines hinter dem Text, zum Beispiel das Band im Briefkopf);
Ziehen verschiebt, die Griffe an den Ecken und Kanten ändern die Größe (an den Ecken bleibt das Seitenverhältnis, mit Umschalt frei),
Entf löscht, Esc hebt die Auswahl auf. Bilder in der Kopf-/Fußzeile gehören zum Blatt, Bilder im Text zu einem Absatz.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QTextCursor

from lunivo_writer.editor import freie_bilder as FB
from lunivo_writer.editor.zusatz import B_BILDANKER

from lunivo_writer.core.farben import Farbe
GRIFF = 9.0                                                  # Seitenlänge eines Griffs in Bildschirmpunkten
GRIFFE = {"nw": (0, 0), "n": (0.5, 0), "ne": (1, 0), "e": (1, 0.5), "se": (1, 1), "s": (0.5, 1), "sw": (0, 1), "w": (0, 0.5)}
ROT_ABSTAND = 24.0                                           # Drehgriff: so weit über der Oberkante des Rahmens
CURSOR = {"rot": Qt.PointingHandCursor, "nw": Qt.SizeFDiagCursor, "se": Qt.SizeFDiagCursor, "ne": Qt.SizeBDiagCursor, "sw": Qt.SizeBDiagCursor,
          "n": Qt.SizeVerCursor, "s": Qt.SizeVerCursor, "e": Qt.SizeHorCursor, "w": Qt.SizeHorCursor}


class FreieBilderMixin:
    @property
    def _frei_sel(self):
        return self.__dict__.get("_frei_sel_wert")

    @_frei_sel.setter
    def _frei_sel(self, wert) -> None:
        alt = self.__dict__.get("_frei_sel_wert")
        self.__dict__["_frei_sel_wert"] = wert
        if alt != wert and hasattr(self, "freiAuswahlGeaendert"):
            self.freiAuswahlGeaendert.emit()

    def _frei_init(self) -> None:
        self._frei_treffer: list[tuple] = []                  # (Schlüssel, Angabe, Rechteck im Editor, hinter, Blatt-Nr.)
        self._frei_sel = None                                 # Schlüssel des gewählten Bildes
        self._frei_vorlaeufig: dict = {}                      # Schlüssel → Angabe während des Ziehens
        self._frei_zug = None                                 # (Art, Griff, Start, Angabe zu Beginn, Rechteck zu Beginn, Blatt)
        self._frei_cursor_gesetzt = False

    # ---- Zeichnen ------------------------------------------------------------------------------------------------------
    @staticmethod
    def _frei_schluessel(a: dict) -> tuple:
        return ("t", a["_blk"], a["_idx"]) if "_blk" in a else ("k", id(a))

    def _frei_liste(self) -> list[tuple]:
        """Alle frei positionierten Bilder aller Blätter: (Schlüssel, Angabe, Bild, Rechteck im Editor, hinter, Blatt-Nr.). Unabhängig davon, was
        gerade gezeichnet wird (ein Zeichenvorgang für die blinkende Schreibmarke berührt nur einen kleinen Teil)."""
        doc, g, z = self.document(), self._sp_geo(), self.zoom
        if not hasattr(self, "_frei_treffer"):
            self._frei_init()
        if getattr(self, "_frei_rev", None) != doc.revision():
            self._frei_rev, self._frei_hat = doc.revision(), FB.hat_bilder(doc)
        if not (self.page.bilder or self._frei_hat):
            return []
        schl = (doc.revision(), z, id(self.page), doc.pageCount(), len(self.page.bilder), tuple(sorted(map(repr, self._frei_vorlaeufig.items()))))
        if getattr(self, "_frei_schl", None) != schl[:4]:
            roh = FB.koerper_index(doc, g["ch"], g["n"])
            self._frei_idx = {k: [(a, y / z, sp) for a, y, sp in v] for k, v in roh.items()}
            self._frei_schl = schl[:4]
        if getattr(self, "_frei_liste_schl", None) == schl:
            return self._frei_liste_wert
        liste = []
        for k in range(self._blatt_anzahl()):
            oben = self.blatt_oben(k)
            for a, bild, r in FB.objekte_der_seite(self.page, doc, k + 1, self._frei_idx):
                key = self._frei_schluessel(a)
                if key in self._frei_vorlaeufig:                      # wird gerade gezogen
                    a = self._frei_vorlaeufig[key]
                    r = QRectF(*self._frei_rechteck(a, k + 1))
                liste.append((key, a, bild, QRectF(r.x() * z, oben + r.y() * z, r.width() * z, r.height() * z), bool(a.get("hinter")), k + 1))
        self._frei_liste_schl, self._frei_liste_wert = schl, liste
        self._frei_treffer = [(key, a, r, hinten, n) for key, a, bild, r, hinten, n in liste]
        return liste

    def _frei_zeichnen(self, p: QPainter, sicht: QRectF, hinter: bool) -> None:
        """Bilder der sichtbaren Blätter, hinter (``hinter``) oder vor dem Text; die vorderen zeichnen auch die Auswahl."""
        z = self.zoom
        for key, a, bild, r, hinten, n in self._frei_liste():
            if hinten != hinter or not r.intersects(sicht):
                continue
            p.save(); p.translate(r.x(), r.y()); p.scale(z, z)
            FB.bild_zeichnen(p, bild, QRectF(0, 0, r.width() / z, r.height() / z), bool(a.get("ellipse")), a.get("rand"), float(a.get("dreh", 0.0)), a.get("fuell"), a.get("_fuellbild") or (a.get("fuell") or {}).get("bild"), a.get("fx"))
            p.restore()
        if not hinter and self._frei_sel is not None:
            for key, a, bild, r, hinten, n in self._frei_liste():
                if key == self._frei_sel and r.intersects(sicht):
                    self._frei_auswahl_zeichnen(p, r)

    def _frei_rechteck(self, a: dict, n: int):
        from lunivo_writer.models.page import mm_to_px
        pg = self.page
        r = FB.rechteck(a, mm_to_px(pg.width_mm), mm_to_px(pg.height_mm), mm_to_px(pg.margin_left_mm), mm_to_px(pg.margin_top_mm),
                        pg.content_width_px, pg.content_height_px, a.get("_ay", 0.0), a.get("_sx"), n)
        return r.x(), r.y(), r.width(), r.height()

    KNOPF = 30.0                                              # Kantenlänge einer Schaltfläche neben dem Bild
    KNOEPFE = ("layout", "formstile", "fuell", "kontur")         # von oben nach unten, wie in der Vorlage

    def _frei_knopf_rects(self, r: QRectF) -> dict[str, QRectF]:
        """Die Schaltflächen rechts neben dem Bild: oben der Minus-Knopf (klappt sie ein), darunter Layoutoptionen, Formstile, Füllung, Kontur."""
        x = r.right() + 12
        out = {"minus": QRectF(x + 5, r.top(), 20, 20)}
        if getattr(self, "_frei_knoepfe_offen", True):
            for i, k in enumerate(self.KNOEPFE):
                out[k] = QRectF(x, r.top() + 32 + i * 40, self.KNOPF, self.KNOPF)
        return out

    def _frei_auswahl_zeichnen(self, p: QPainter, r: QRectF) -> None:
        from lunivo_writer.ui.baukasten.umbruch_symbole import umbruch_zeichner
        from lunivo_writer.ui.widgets import icons
        offen = getattr(self, "_frei_knoepfe_offen", True)
        p.save(); p.setRenderHint(QPainter.Antialiasing)
        for name, k in self._frei_knopf_rects(r).items():
            p.setPen(QPen(QColor(Farbe.GRAU_HELL), 1)); p.setBrush(QColor("white"))
            if name == "minus":
                p.drawEllipse(k); p.setPen(QPen(QColor("#495057"), 1.6))
                p.drawLine(int(k.left() + 5), int(k.center().y()), int(k.right() - 5), int(k.center().y()))
                if not offen:
                    p.drawLine(int(k.center().x()), int(k.top() + 5), int(k.center().x()), int(k.bottom() - 5))
                continue
            p.drawRoundedRect(k, 4, 4)
            inner = k.adjusted(5, 5, -5, -5)
            if name == "layout":
                umbruch_zeichner("quadrat")(p, k.adjusted(4, 4, -4, -4))
            elif name == "formstile":
                p.drawPixmap(inner.toRect(), self._frei_dunkel("pinsel"))
            elif name == "fuell":
                p.drawPixmap(inner.adjusted(0, -2, 0, -3).toRect(), self._frei_dunkel("farbe"))
                p.fillRect(QRectF(inner.left(), inner.bottom() - 2, inner.width(), 3), QColor("#f2c200"))
            else:                                                  # Kontur: ein Rahmen
                p.setPen(QPen(QColor("#1c3faa"), 2)); p.setBrush(Qt.NoBrush); p.drawRoundedRect(inner.adjusted(1, 1, -1, -1), 2, 2)
        p.restore()
        p.save()
        pen = QPen(QColor("#1c7ed6"), 1.5, Qt.DashLine)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawRect(r)
        p.setPen(QPen(QColor("#1c7ed6"), 1)); p.setBrush(QColor("white"))
        for name in GRIFFE:
            c = self._frei_griff_mitte(r, name)
            p.drawRect(QRectF(c.x() - GRIFF / 2, c.y() - GRIFF / 2, GRIFF, GRIFF))
        rc = self._frei_griff_mitte(r, "rot")                     # der Drehgriff über der Mitte der Oberkante
        p.setPen(QPen(QColor("#1c7ed6"), 1)); p.drawLine(QPointF(rc.x(), r.top()), QPointF(rc.x(), rc.y() + GRIFF / 2))
        p.setBrush(QColor("white")); p.drawEllipse(rc, GRIFF / 2 + 1, GRIFF / 2 + 1)
        p.setPen(QPen(QColor("#1c7ed6"), 1.4)); p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(rc.x() - 2.5, rc.y() - 2.5, 5, 5), 40 * 16, 280 * 16)
        p.restore()

    @staticmethod
    def _frei_dunkel(name: str):
        """Das Symbol dunkel gefärbt: die Knöpfe am Bild sind immer weiß, auch im dunklen Design (dort wären die Symbole sonst hell auf weiß)."""
        from PySide6.QtGui import QPixmap
        from lunivo_writer.ui.widgets import icons
        pm = icons.icon(name, 20).pixmap(20, 20)
        p = QPainter(pm); p.setCompositionMode(QPainter.CompositionMode_SourceIn); p.fillRect(pm.rect(), QColor(Farbe.TINTE)); p.end()
        return pm

    @staticmethod
    def _frei_griff_mitte(r: QRectF, name: str) -> QPointF:
        if name == "rot":
            return QPointF(r.center().x(), r.top() - ROT_ABSTAND)
        fx, fy = GRIFFE[name]
        return QPointF(r.left() + r.width() * fx, r.top() + r.height() * fy)

    # ---- Treffer -------------------------------------------------------------------------------------------------------
    def _frei_griff_bei(self, pos: QPointF):
        if self._frei_sel is None:
            return None, None
        for key, a, r, hinten, n in self._frei_treffer:
            if key == self._frei_sel:
                for name in (*GRIFFE, "rot"):
                    c = self._frei_griff_mitte(r, name)
                    if abs(pos.x() - c.x()) <= GRIFF and abs(pos.y() - c.y()) <= GRIFF:
                        return name, (key, a, r, hinten, n)
                return None, (key, a, r, hinten, n) if r.contains(pos) else None
        return None, None

    def _frei_text_bei(self, pos: QPointF) -> bool:
        """Liegt an dieser Stelle Text? Dann gehört der Klick dem Text, nicht einem Bild dahinter."""
        try:
            x, y = self._sp_doc(pos.x(), pos.y())
            return self.document().documentLayout().hitTest(QPointF(x, y), Qt.ExactHit) >= 0
        except Exception:                                                  # noqa: BLE001
            return False

    def _frei_bild_bei(self, pos: QPointF, auch_hinten: bool):
        for t in reversed(self._frei_treffer):                      # zuletzt gezeichnet = oben
            if (auch_hinten or not t[3]) and t[2].contains(pos):
                return t
        return None

    # ---- Maus ----------------------------------------------------------------------------------------------------------
    def _frei_maus(self, e, art: str) -> bool:
        """True, wenn das Ereignis ein Bild betrifft und der Editor es nicht weiter behandeln soll."""
        if not hasattr(self, "_frei_treffer"):
            self._frei_init()
        self._frei_liste()
        if not self._frei_treffer or self.isReadOnly():
            if art == "press" and self._frei_sel is not None:
                self._frei_sel = None; self.viewport().update()
            return False
        pos = e.position()
        if art == "press" and e.button() == Qt.LeftButton and self._frei_sel is not None:
            for key, a, r, hinten, n in self._frei_treffer:
                if key == self._frei_sel:
                    for name, k in self._frei_knopf_rects(r).items():                            # die Schaltflächen neben dem Bild
                        if k.contains(pos):
                            self._frei_knopf(name, e.globalPosition().toPoint())
                            return True
        if art == "press" and e.button() == Qt.LeftButton:
            griff, treffer = self._frei_griff_bei(pos)
            if treffer is None or (griff is None and not treffer[2].contains(pos)):
                # Bilder hinter dem Text: mit Strg+Alt, oder wenn an der Stelle kein Text liegt (zum Beispiel das Band im Briefkopf)
                treffer = self._frei_bild_bei(pos, bool(e.modifiers() & Qt.ControlModifier and e.modifiers() & Qt.AltModifier)
                                              or not self._frei_text_bei(pos))
                griff = None
            if treffer is None:
                if self._frei_sel is not None:
                    self._frei_sel = None; self.viewport().update()
                return False
            key, a, r, hinten, n = treffer
            merk = getattr(self, "_frei_format_merk", None)
            if merk is not None and key != self._frei_sel:                    # „Format übertragen“ wartet auf das Zielbild
                self._frei_format_merk = None
                self._frei_sel = key
                from lunivo_writer.editor import bildlayout as BL
                BL.format_uebertragen(self, BL.ziel(self), merk)
                self.viewport().setCursor(Qt.IBeamCursor)
                return True
            self._frei_sel = key
            if hasattr(self.window(), "objektformat_folgen"):
                self.window().objektformat_folgen()
            self._frei_zug = ("drehen" if griff == "rot" else "groesse" if griff else "bewegen", griff, pos, dict(a), QRectF(r), n)
            self.viewport().update()
            return True
        if art == "move":
            if self._frei_zug is not None and e.buttons() & Qt.LeftButton:
                self._frei_ziehen(e)
                return True
            griff, treffer = self._frei_griff_bei(pos)
            if griff:
                self.viewport().setCursor(CURSOR[griff]); self._frei_cursor_gesetzt = True
            elif treffer is not None or self._frei_bild_bei(pos, not self._frei_text_bei(pos)) is not None:
                self.viewport().setCursor(Qt.SizeAllCursor); self._frei_cursor_gesetzt = True      # das Bild lässt sich anfassen
            elif self._frei_cursor_gesetzt:
                self.viewport().setCursor(Qt.IBeamCursor); self._frei_cursor_gesetzt = False
            return False
        if art == "release" and self._frei_zug is not None:
            self._frei_ablegen()
            return True
        return False

    def _frei_ziehen(self, e) -> None:
        art, griff, start, a0, r0, n = self._frei_zug
        z = self.zoom
        if art == "drehen":                                                  # Drehgriff: der Winkel zeigt von der Mitte zur Maus
            import math
            m = r0.center()
            w = math.degrees(math.atan2(e.position().x() - m.x(), m.y() - e.position().y())) % 360.0
            if e.modifiers() & Qt.ShiftModifier:
                w = round(w / 15.0) * 15.0 % 360.0
            self._frei_vorlaeufig[self._frei_sel] = {**a0, "dreh": round(w, 1)}
            self.viewport().update()
            return
        dx, dy = (e.position().x() - start.x()) / z, (e.position().y() - start.y()) / z
        r = QRectF(r0.x() / z, 0, r0.width() / z, r0.height() / z)          # Blattkoordinaten: x wie im Editor, y wird unten ergänzt
        oben = self.blatt_oben(n - 1)
        r.moveTop((r0.y() - oben) / z)
        if art == "bewegen":
            r.translate(dx, dy)
        else:
            verhaeltnis = r.width() / max(1.0, r.height())
            frei = bool(e.modifiers() & Qt.ShiftModifier) or griff in ("n", "s", "e", "w")
            l, t, rr, b = r.left(), r.top(), r.right(), r.bottom()
            if "w" in griff:
                l = min(l + dx, rr - 8)
            if "e" in griff:
                rr = max(rr + dx, l + 8)
            if "n" in griff:
                t = min(t + dy, b - 8)
            if "s" in griff:
                b = max(b + dy, t + 8)
            if not frei:                                                     # Ecke: Seitenverhältnis halten, Breite bestimmt die Höhe
                breite = rr - l
                hoehe = breite / verhaeltnis
                if "n" in griff:
                    t = b - hoehe
                else:
                    b = t + hoehe
            r = QRectF(l, t, rr - l, b - t)
        neu = FB.versatz_fuer(a0, r, self.page, n)
        self._frei_vorlaeufig[self._frei_sel] = neu
        self.viewport().update()

    def _frei_ablegen(self) -> None:
        zug, self._frei_zug = self._frei_zug, None
        neu = self._frei_vorlaeufig.pop(self._frei_sel, None)
        self._frei_vorlaeufig.clear()
        if neu is None:
            return                                                           # nur angeklickt
        if self._frei_sel[0] == "k":
            for a in self.page.bilder:
                if id(a) == self._frei_sel[1]:
                    a.update(FB.ohne_hilfsangaben(neu))
            self.document().setModified(True)
            self.pageApplied.emit()
        else:
            self._frei_absatz_aendern(neu["_blk"], neu["_idx"], FB.ohne_hilfsangaben(neu))
        self.viewport().update()

    def _frei_absatz_aendern(self, blk: int, idx: int, neu: dict | None) -> None:
        """Ändert (oder, mit ``neu=None``, entfernt) die Angabe ``idx`` am Absatz ``blk`` — als ein Schritt, den Rückgängig zurücknimmt."""
        b = self.document().findBlockByNumber(blk)
        if not b.isValid():
            return
        liste = FB.aus_absatz(b.blockFormat())
        if idx >= len(liste):
            return
        c = QTextCursor(b)
        c.beginEditBlock()
        if neu is None:
            liste.pop(idx)
        else:
            liste[idx] = neu
        bf = b.blockFormat()
        if liste:
            bf.setProperty(B_BILDANKER, json.dumps(liste, separators=(",", ":")))
        else:
            bf.clearProperty(B_BILDANKER)
        c.setBlockFormat(bf)
        c.endEditBlock()
        self.document().setModified(True)
        self._frei_rev = None

    # ---- Schaltflächen neben dem Bild -------------------------------------------------------------------------------------------
    def _frei_knopf(self, name: str, pos) -> None:
        if name == "minus":
            self._frei_knoepfe_offen = not getattr(self, "_frei_knoepfe_offen", True)
            self.viewport().update()
        elif name == "layout":
            self._frei_layout_popup(pos)
        elif name == "formstile":
            self._frei_formstile(pos)
        elif name == "fuell":
            self._frei_fuell(pos)
        elif name == "kontur":
            self._frei_kontur(pos)

    def _frei_wirken(self, **teile) -> None:
        from lunivo_writer.editor import bildlayout as BL
        BL.format_setzen(self, BL.ziel(self), **teile)

    def _frei_formstile(self, pos) -> None:
        m = self.frei_formstile_menue(self)
        m.popup(pos); self._frei_menue = m

    def frei_formstile_menue(self, parent=None, ed=None):
        E = ed or (lambda: self)                               # der Editor, auf den die Wahl wirkt (zur Wahlzeit, nicht zur Bauzeit)
        from lunivo_writer.ui.baukasten.objekt_menues import formstil_werte, formstile
        m = formstile(parent)
        m.gewaehlt.connect(lambda k: (lambda w: E()._frei_wirken(fuell=w["fuell"], rand=w["rand"]))(formstil_werte(k)) or m.close())
        m.fuss("Weitere Effekte(O)…", lambda: E()._frei_effekte())
        return m

    def _frei_effekte(self) -> None:
        """„Weitere Effekte …“: die Seitenleiste „Formatierung“ mit den Effekten."""
        fenster = self.window()
        if hasattr(fenster, "objektformat_seitenleiste"):
            fenster.objektformat_seitenleiste(1)

    def _frei_fuell(self, pos) -> None:
        m = self.frei_fuell_menue(self)
        m.popup(pos); self._frei_menue = m

    def frei_fuell_menue(self, parent=None, ed=None):
        E = ed or (lambda: self)                               # der Editor, auf den die Wahl wirkt (zur Wahlzeit, nicht zur Bauzeit)
        from PySide6.QtWidgets import QFileDialog
        from PySide6.QtGui import QImage
        from lunivo_writer.editor import bildlayout as BL
        from lunivo_writer.ui.baukasten.objekt_menues import FuellMenue
        m = FuellMenue(parent)
        m.gewaehlt.connect(lambda c: E()._frei_wirken(fuell=None if c is None else {"art": "farbe", "farbe": c.name()}))
        m.verlauf_gewaehlt.connect(lambda c: E()._frei_wirken(fuell={"art": "verlauf", "farbe": c.name()}))
        m.graduell_gewaehlt.connect(lambda d, h: E()._frei_wirken(fuell={"art": "graduell", "dunkel": d, "hell": h, "farbe": d}))
        m.muster_gewaehlt.connect(lambda k: E()._frei_wirken(fuell={"art": "muster", "key": k, "farbe": Farbe.TINTE, "grund": Farbe.WEISS}))
        m.textur_gewaehlt.connect(lambda k: E()._frei_wirken(fuell={"art": "textur", "key": k}))

        def bild():
            pfad, _ = QFileDialog.getOpenFileName(E().window(), "Bild als Füllung", "", "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
            if pfad:
                BL.fuellbild_setzen(E(), BL.ziel(E()), QImage(pfad))
        m.bild_gewaehlt.connect(bild)
        m.weitere_fuellung.connect(lambda art: E()._frei_fuell_fenster(art))
        return m

    def _frei_fuell_fenster(self, art: str) -> None:
        """„Fülleffekte“, „Weitere Farbverläufe/Texturen/Muster“: die Seitenleiste „Formatierung“ auf „Füllung und Linie“ mit dieser Füllungsart."""
        fenster = self.window()
        if hasattr(fenster, "objektformat_seitenleiste"):
            fenster.objektformat_seitenleiste(0, art)

    def _frei_kontur(self, pos) -> None:
        m = self.frei_kontur_menue(self)
        m.popup(pos); self._frei_menue = m

    def frei_kontur_menue(self, parent=None, ed=None):
        E = ed or (lambda: self)                               # der Editor, auf den die Wahl wirkt (zur Wahlzeit, nicht zur Bauzeit)
        from lunivo_writer.ui.baukasten.objekt_menues import KonturMenue
        m = KonturMenue(parent)
        m.gewaehlt.connect(lambda c: E()._frei_wirken(rand=None) if c is None else E()._frei_wirken(rand_teil={"farbe": c.name()}))
        m.breite_gewaehlt.connect(lambda pt: E()._frei_wirken(rand_teil={"b": pt * 96 / 72}))
        m.strich_gewaehlt.connect(lambda a: E()._frei_wirken(rand_teil={"art": a}))
        m.weitere_linien.connect(lambda: E()._frei_linien_fenster())
        return m

    def _frei_linien_fenster(self) -> None:
        """„Weitere Linien …“: die Seitenleiste „Formatierung“ auf dem Reiter „Füllung und Linie“ (Farbe, Breite, Strichart)."""
        fenster = self.window()
        if hasattr(fenster, "objektformat_seitenleiste"):
            fenster.objektformat_seitenleiste(0)

    # ---- Layout: Popup neben dem Bild und das Fenster ---------------------------------------------------------------------------
    def bild_layout_popup(self, global_pos) -> None:
        self._frei_layout_popup(global_pos)

    def _frei_layout_popup(self, global_pos) -> None:
        from lunivo_writer.editor import bildlayout as BL
        from lunivo_writer.ui.baukasten.layout_optionen import LayoutOptionen
        z = BL.ziel(self)
        if z is None:
            return
        w = BL.lesen(self, z)
        p = LayoutOptionen(self, w["umbruch"], bool(w.get("mit_text")))
        p.gewaehlt.connect(lambda art: BL.anwenden(self, BL.ziel(self), {"umbruch": art}) if BL.ziel(self) else None)
        p.verschieben.connect(lambda an: BL.anwenden(self, BL.ziel(self), {"mit_text": bool(an)}) if BL.ziel(self) else None)
        p.mehr.connect(self.bild_layout_dialog)
        p.zeigen_bei(global_pos)
        self._frei_popup = p

    def bild_layout_dialog(self) -> None:
        """Das Fenster „Layout“ für das markierte Bild (frei oder im Text)."""
        from lunivo_writer.editor import bildlayout as BL
        from lunivo_writer.ui.baukasten.layout_dialog import LayoutDialog
        z = BL.ziel(self)
        if z is None:
            return
        d = LayoutDialog(self.window(), BL.lesen(self, z))
        if d.exec():
            z = BL.ziel(self)
            if z is not None:
                BL.anwenden(self, z, d.werte())

    # ---- Tasten --------------------------------------------------------------------------------------------------------
    def _frei_taste(self, e) -> bool:
        if not hasattr(self, "_frei_treffer") or self._frei_sel is None or self.isReadOnly():
            return False
        if e.key() == Qt.Key_Escape:
            self._frei_sel = None; self.viewport().update()
            return True
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            key, self._frei_sel = self._frei_sel, None
            if key[0] == "k":
                self.page.bilder[:] = [a for a in self.page.bilder if id(a) != key[1]]
                self.document().setModified(True)
                self.pageApplied.emit()
            else:
                self._frei_absatz_aendern(key[1], key[2], None)
            self.viewport().update()
            return True
        return False
