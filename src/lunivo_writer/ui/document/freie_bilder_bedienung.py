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

GRIFF = 9.0                                                  # Seitenlänge eines Griffs in Bildschirmpunkten
GRIFFE = {"nw": (0, 0), "n": (0.5, 0), "ne": (1, 0), "e": (1, 0.5), "se": (1, 1), "s": (0.5, 1), "sw": (0, 1), "w": (0, 0.5)}
CURSOR = {"nw": Qt.SizeFDiagCursor, "se": Qt.SizeFDiagCursor, "ne": Qt.SizeBDiagCursor, "sw": Qt.SizeBDiagCursor,
          "n": Qt.SizeVerCursor, "s": Qt.SizeVerCursor, "e": Qt.SizeHorCursor, "w": Qt.SizeHorCursor}


class FreieBilderMixin:
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

    def _frei_zeichnen(self, p: QPainter, sicht: QRectF, hinter: bool) -> None:
        """Bilder der sichtbaren Blätter, hinter (``hinter``) oder vor dem Text; die vorderen zeichnen auch die Auswahl."""
        doc, g, z = self.document(), self._sp_geo(), self.zoom
        if not hasattr(self, "_frei_treffer"):
            self._frei_init()
        if getattr(self, "_frei_rev", None) != doc.revision():
            self._frei_rev, self._frei_hat = doc.revision(), FB.hat_bilder(doc)
        if hinter:
            self._frei_treffer = []
        if not (self.page.bilder or self._frei_hat):
            return
        schl = (doc.revision(), z, id(self.page), doc.pageCount())
        if getattr(self, "_frei_schl", None) != schl:
            roh = FB.koerper_index(doc, g["ch"], g["n"])
            self._frei_idx = {k: [(a, y / z, sp) for a, y, sp in v] for k, v in roh.items()}
            self._frei_schl = schl
        vp = self.viewport()
        for k in range(self._blatt_anzahl()):
            oben = self.blatt_oben(k)
            if not QRectF(0, oben, vp.width(), g["H"]).intersects(sicht):
                continue
            alle = FB.objekte_der_seite(self.page, doc, k + 1, self._frei_idx)
            objekte = []
            for a, bild, r in alle:
                key = self._frei_schluessel(a)
                if key in self._frei_vorlaeufig:               # wird gerade gezogen
                    a = self._frei_vorlaeufig[key]
                    r = QRectF(*self._frei_rechteck(a, k + 1))
                objekte.append((key, a, bild, r))
            sicht_k = [o for o in objekte if bool(o[1].get("hinter")) == hinter]
            if sicht_k:
                p.save(); p.translate(0, oben); p.scale(z, z)
                for key, a, bild, r in sicht_k:
                    FB.bild_zeichnen(p, bild, r, bool(a.get("ellipse")), a.get("rand"))
                p.restore()
            for key, a, bild, r in sicht_k:
                if hinter:
                    self._frei_treffer.append((key, a, QRectF(r.x() * z, oben + r.y() * z, r.width() * z, r.height() * z), True, k + 1))
                else:
                    self._frei_treffer.append((key, a, QRectF(r.x() * z, oben + r.y() * z, r.width() * z, r.height() * z), False, k + 1))
        if not hinter and self._frei_sel is not None:
            for key, a, r, hinten, n in self._frei_treffer:
                if key == self._frei_sel:
                    self._frei_auswahl_zeichnen(p, r)

    def _frei_rechteck(self, a: dict, n: int):
        from lunivo_writer.models.page import mm_to_px
        pg = self.page
        r = FB.rechteck(a, mm_to_px(pg.width_mm), mm_to_px(pg.height_mm), mm_to_px(pg.margin_left_mm), mm_to_px(pg.margin_top_mm),
                        pg.content_width_px, pg.content_height_px, a.get("_ay", 0.0), a.get("_sx"), n)
        return r.x(), r.y(), r.width(), r.height()

    def _frei_auswahl_zeichnen(self, p: QPainter, r: QRectF) -> None:
        p.save()
        pen = QPen(QColor("#1c7ed6"), 1.5, Qt.DashLine)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawRect(r)
        p.setPen(QPen(QColor("#1c7ed6"), 1)); p.setBrush(QColor("white"))
        for name in GRIFFE:
            c = self._frei_griff_mitte(r, name)
            p.drawRect(QRectF(c.x() - GRIFF / 2, c.y() - GRIFF / 2, GRIFF, GRIFF))
        p.restore()

    @staticmethod
    def _frei_griff_mitte(r: QRectF, name: str) -> QPointF:
        fx, fy = GRIFFE[name]
        return QPointF(r.left() + r.width() * fx, r.top() + r.height() * fy)

    # ---- Treffer -------------------------------------------------------------------------------------------------------
    def _frei_griff_bei(self, pos: QPointF):
        if self._frei_sel is None:
            return None, None
        for key, a, r, hinten, n in self._frei_treffer:
            if key == self._frei_sel:
                for name in GRIFFE:
                    c = self._frei_griff_mitte(r, name)
                    if abs(pos.x() - c.x()) <= GRIFF and abs(pos.y() - c.y()) <= GRIFF:
                        return name, (key, a, r, hinten, n)
                return None, (key, a, r, hinten, n) if r.contains(pos) else None
        return None, None

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
        if not self._frei_treffer or self.isReadOnly():
            if art == "press" and self._frei_sel is not None:
                self._frei_sel = None; self.viewport().update()
            return False
        pos = e.position()
        if art == "press" and e.button() == Qt.LeftButton:
            griff, treffer = self._frei_griff_bei(pos)
            if treffer is None or (griff is None and not treffer[2].contains(pos)):
                treffer = self._frei_bild_bei(pos, bool(e.modifiers() & Qt.ControlModifier and e.modifiers() & Qt.AltModifier))
                griff = None
            if treffer is None:
                if self._frei_sel is not None:
                    self._frei_sel = None; self.viewport().update()
                return False
            key, a, r, hinten, n = treffer
            self._frei_sel = key
            self._frei_zug = ("groesse" if griff else "bewegen", griff, pos, dict(a), QRectF(r), n)
            self.viewport().update()
            return True
        if art == "move":
            if self._frei_zug is not None and e.buttons() & Qt.LeftButton:
                self._frei_ziehen(e)
                return True
            griff, treffer = self._frei_griff_bei(pos)
            if griff:
                self.viewport().setCursor(CURSOR[griff]); self._frei_cursor_gesetzt = True
            elif treffer is not None:
                self.viewport().setCursor(Qt.SizeAllCursor); self._frei_cursor_gesetzt = True
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
