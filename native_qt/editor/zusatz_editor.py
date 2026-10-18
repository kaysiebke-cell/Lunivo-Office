"""Editor-Seite von Kommentaren, Fuß-/Endnoten und Änderungsverfolgung (Mixin für DocumentEditor)."""
from __future__ import annotations

import datetime
import hashlib

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit

from .zusatz import P_AENDERUNG, P_AUTOR, P_DATUM, P_KOMMENTAR, P_NOTE, neue_id, roemisch

AUTOR_FARBEN = ["#c92a2a", "#1971c2", "#2f9e44", "#e8590c", "#7048a8", "#0b7285", "#a61e4d", "#5c940d"]


def autor_farbe(autor: str) -> QColor:
    h = int(hashlib.md5((autor or "?").encode()).hexdigest(), 16)
    return QColor(AUTOR_FARBEN[h % len(AUTOR_FARBEN)])


class ZusatzMixin:
    zusatzGeaendert = Signal()

    def _zusatz_init(self) -> None:
        self.kommentare: dict = {}
        self.noten: dict = {"f": {}, "e": {}}
        self.verfolgen = False
        self.markup = True
        self.autor = lambda: ("Unbekannt", "")
        self._zus_intern = False
        self._hat_zusatz = False
        self._zus_timer = QTimer(self)
        self._zus_timer.setSingleShot(True)
        self._zus_timer.setInterval(200)
        self._zus_timer.timeout.connect(self._overlays_neu)
        self.document().contentsChange.connect(self._inhalt_geaendert)

    def zusatz_binden(self, meta: dict) -> None:
        """Meta-Daten des Dokuments (Kommentartexte, Noten) mit dem Editor teilen."""
        self.kommentare = meta.setdefault("kommentare", {})
        self.noten = meta.setdefault("noten", {"f": {}, "e": {}})
        self.noten.setdefault("f", {}); self.noten.setdefault("e", {})
        self._hat_zusatz = bool(self.kommentare or self.noten["f"] or self.noten["e"]) or bool(self.aenderungen())
        self._overlays_neu()

    # ---- Suchen von Bereichen ----------------------------------------------------------------
    def _fragmente(self):
        b = self.document().firstBlock()
        while b.isValid():
            it = b.begin()
            while not it.atEnd():
                f = it.fragment()
                if f.isValid():
                    yield f
                it += 1
            b = b.next()

    def _bereiche(self, prop, schluessel=None) -> list[dict]:
        """Zusammenhängende Textstücke mit gleicher Eigenschaft: [{von, bis, wert, cf}]."""
        aus: list[dict] = []
        for f in self._fragmente():
            cf = f.charFormat()
            if not cf.hasProperty(prop):
                continue
            wert = cf.property(prop)
            key = schluessel(cf) if schluessel else wert
            v, bis = f.position(), f.position() + f.length()
            if aus and aus[-1]["bis"] == v and aus[-1]["key"] == key:
                aus[-1]["bis"] = bis
            else:
                aus.append({"von": v, "bis": bis, "wert": wert, "key": key, "cf": cf})
        return aus

    def kommentar_bereiche(self) -> list[dict]:
        return self._bereiche(P_KOMMENTAR)

    def aenderungen(self) -> list[dict]:
        return self._bereiche(P_AENDERUNG, lambda cf: (cf.stringProperty(P_AENDERUNG), cf.stringProperty(P_AUTOR),
                                                       cf.stringProperty(P_DATUM)))

    def noten_stellen(self) -> list[dict]:
        out = []
        for f in self._fragmente():
            cf = f.charFormat()
            if cf.hasProperty(P_NOTE):
                art, _, nid = cf.stringProperty(P_NOTE).partition(":")
                out.append({"von": f.position(), "bis": f.position() + f.length(), "art": art, "id": int(nid)})
        return out

    # ---- Eigenschaften setzen / entfernen -----------------------------------------------------
    def _bereich_format(self, von: int, bis: int, props: dict) -> None:
        c = QTextCursor(self.document())
        c.setPosition(von); c.setPosition(bis, QTextCursor.KeepAnchor)
        f = QTextCharFormat()
        for k, v in props.items():
            f.setProperty(k, v)
        self._zus_intern = True
        try:
            c.mergeCharFormat(f)
        finally:
            self._zus_intern = False

    def _eigenschaft_weg(self, prop, pred=lambda cf: True, von: int = 0, bis: int | None = None) -> None:
        doc = self.document()
        bis = doc.characterCount() if bis is None else bis
        stuecke = [(f.position(), f.position() + f.length(), f.charFormat()) for f in self._fragmente()
                   if f.charFormat().hasProperty(prop) and pred(f.charFormat()) and f.position() < bis and f.position() + f.length() > von]
        c = QTextCursor(doc)
        c.beginEditBlock()
        self._zus_intern = True
        try:
            for a, b, cf in reversed(stuecke):
                neu = QTextCharFormat(cf)
                neu.clearProperty(prop)
                if prop == P_AENDERUNG:
                    neu.clearProperty(P_AUTOR); neu.clearProperty(P_DATUM)
                c.setPosition(a); c.setPosition(b, QTextCursor.KeepAnchor)
                c.setCharFormat(neu)
        finally:
            self._zus_intern = False
            c.endEditBlock()

    # ---- Kommentare -------------------------------------------------------------------------------
    def kommentar_neu(self, text: str) -> int | None:
        c = self.textCursor()
        if not c.hasSelection():
            c.select(QTextCursor.WordUnderCursor)
            if not c.hasSelection():
                return None
        kid = neue_id(self.kommentare)
        name, init = self.autor()
        self.kommentare[kid] = {"autor": name, "initialen": init, "datum": datetime.datetime.now(datetime.timezone.utc)
                                .replace(microsecond=0).isoformat(), "text": text}
        self._bereich_format(c.selectionStart(), c.selectionEnd(), {P_KOMMENTAR: kid})
        self.document().setModified(True)
        self._hat_zusatz = True
        self._zus_geaendert()
        return kid

    def kommentar_loeschen(self, kid: int) -> None:
        self._eigenschaft_weg(P_KOMMENTAR, lambda cf: int(cf.property(P_KOMMENTAR)) == kid)
        self.kommentare.pop(kid, None)
        self.document().setModified(True)
        self._zus_geaendert()

    def kommentare_alle_loeschen(self) -> None:
        self._eigenschaft_weg(P_KOMMENTAR)
        self.kommentare.clear()
        self.document().setModified(True)
        self._zus_geaendert()

    def _springe(self, bereiche: list[dict], delta: int) -> dict | None:
        if not bereiche:
            return None
        pos = self.textCursor().selectionStart() if delta > 0 else self.textCursor().selectionStart()
        if delta > 0:
            kand = [b for b in bereiche if b["von"] > pos] or bereiche[:1]
            ziel = kand[0]
        else:
            kand = [b for b in bereiche if b["von"] < pos] or bereiche[-1:]
            ziel = kand[-1]
        self.select_range(ziel["von"], ziel["bis"])
        self.ensureCursorVisible()
        return ziel

    def kommentar_springen(self, delta: int):
        return self._springe(self.kommentar_bereiche(), delta)

    def kommentar_am_cursor(self) -> int | None:
        c = self.textCursor()
        for b in self.kommentar_bereiche():
            if b["von"] <= c.position() <= b["bis"]:
                return int(b["wert"])
        return None

    # ---- Fuß- und Endnoten -----------------------------------------------------------------------------
    def note_neu(self, art: str, text: str) -> int:
        nid = neue_id(self.noten[art])
        self.noten[art][nid] = text
        c = self.textCursor()
        c.clearSelection()
        f = QTextCharFormat()
        f.setVerticalAlignment(QTextCharFormat.AlignSuperScript)
        f.setProperty(P_NOTE, f"{art}:{nid}")
        c.insertText("?", f)
        self.setTextCursor(c)
        self._hat_zusatz = True
        self.noten_neu_nummerieren()
        self.document().setModified(True)
        self._zus_geaendert()
        return nid

    def noten_neu_nummerieren(self) -> None:
        stellen = self.noten_stellen()
        zaehler = {"f": 0, "e": 0}
        aenderungen = []
        for s in stellen:
            zaehler[s["art"]] += 1
            soll = str(zaehler[s["art"]]) if s["art"] == "f" else roemisch(zaehler[s["art"]])
            ist = self.document().toPlainText()[s["von"]:s["bis"]] if False else None
            aenderungen.append((s, soll))
        doc = self.document()
        c = QTextCursor(doc)
        c.beginEditBlock()
        self._zus_intern = True
        try:
            for s, soll in reversed(aenderungen):
                c.setPosition(s["von"]); c.setPosition(s["bis"], QTextCursor.KeepAnchor)
                if c.selectedText() != soll:
                    fmt = c.charFormat()
                    c.insertText(soll, fmt)
        finally:
            self._zus_intern = False
            c.endEditBlock()

    def note_loeschen(self, art: str, nid: int) -> None:
        for s in reversed(self.noten_stellen()):
            if s["art"] == art and s["id"] == nid:
                c = QTextCursor(self.document())
                c.setPosition(s["von"]); c.setPosition(s["bis"], QTextCursor.KeepAnchor)
                c.removeSelectedText()
        self.noten[art].pop(nid, None)
        self.noten_neu_nummerieren()
        self.document().setModified(True)
        self._zus_geaendert()

    def note_springen(self, delta: int):
        return self._springe(self.noten_stellen(), delta)

    # ---- Änderungsverfolgung -----------------------------------------------------------------------------
    def set_verfolgen(self, an: bool) -> None:
        self.verfolgen = an
        self._zus_geaendert()

    def _markiere_geloescht(self, von: int, bis: int) -> None:
        """Statt zu löschen als gelöscht kennzeichnen — eigener, noch nicht angenommener Einfügetext verschwindet wirklich."""
        name, _ = self.autor()
        c = QTextCursor(self.document())
        c.beginEditBlock()
        stuecke = [(f.position(), f.position() + f.length(), f.charFormat()) for f in self._fragmente()
                   if f.position() < bis and f.position() + f.length() > von]
        for a, b, cf in reversed(stuecke):
            a, b = max(a, von), min(b, bis)
            if cf.hasProperty(P_AENDERUNG) and cf.stringProperty(P_AENDERUNG) == "ins" and cf.stringProperty(P_AUTOR) == name:
                c.setPosition(a); c.setPosition(b, QTextCursor.KeepAnchor)
                self._zus_intern = True
                c.removeSelectedText()
                self._zus_intern = False
            elif not cf.hasProperty(P_AENDERUNG):
                self._bereich_format(a, b, {P_AENDERUNG: "del", P_AUTOR: name, P_DATUM: self._jetzt()})
        c.endEditBlock()
        self._hat_zusatz = True
        self._zus_geaendert()

    def _loesche_verfolgt(self, von: int, bis: int, ende: bool) -> bool:
        txt = self.document().toPlainText()[von:bis]
        if "\u2029" in txt or "\n" in txt or bis <= von:
            return False                          # über Absatzgrenzen: normal löschen
        self._markiere_geloescht(von, bis)
        c = self.textCursor()
        c.setPosition(bis if ende else von)
        self.setTextCursor(c)
        return True

    def _verfolgte_taste(self, e) -> bool:
        k = e.key()
        c = self.textCursor()
        if k in (Qt.Key_Backspace, Qt.Key_Delete) and not (e.modifiers() & (Qt.ControlModifier | Qt.AltModifier)):
            if c.hasSelection():
                return self._loesche_verfolgt(c.selectionStart(), c.selectionEnd(), ende=(k == Qt.Key_Delete))
            p = c.position()
            if k == Qt.Key_Backspace and p > 0:
                return self._loesche_verfolgt(p - 1, p, ende=False)
            if k == Qt.Key_Delete and p < self.document().characterCount() - 1:
                return self._loesche_verfolgt(p, p + 1, ende=True)
            return False
        if c.hasSelection() and e.text() and e.text().isprintable() and not (e.modifiers() & Qt.ControlModifier):
            a, b = c.selectionStart(), c.selectionEnd()
            if self._loesche_verfolgt(a, b, ende=True):
                return False                      # danach normal tippen: Text kommt hinter die gelöschte Stelle
        return False

    @staticmethod
    def _jetzt() -> str:
        return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _inhalt_geaendert(self, pos: int, entfernt: int, hinzu: int) -> None:
        if self._zus_intern:
            return
        if self.verfolgen and hinzu > 0 and entfernt == 0:
            name, _ = self.autor()
            doc = self.document()
            c = QTextCursor(doc)
            bis = min(pos + hinzu, doc.characterCount() - 1)
            if bis > pos:
                c.setPosition(pos); c.setPosition(bis, QTextCursor.KeepAnchor)
                if not c.charFormat().hasProperty(P_AENDERUNG) and not c.charFormat().hasProperty(P_NOTE):
                    c.joinPreviousEditBlock()
                    self._bereich_format(pos, bis, {P_AENDERUNG: "ins", P_AUTOR: name, P_DATUM: self._jetzt()})
                    c.endEditBlock()
                    self._hat_zusatz = True
        if self._hat_zusatz:
            self._zus_timer.start()
            QTimer.singleShot(0, self.zusatzGeaendert.emit)

    def aenderung_annehmen(self, b: dict, annehmen: bool = True) -> None:
        art = b["wert"]
        loeschen = (art == "del") == annehmen          # angenommene Löschung / abgelehnte Einfügung entfernen Text
        c = QTextCursor(self.document())
        c.beginEditBlock()
        if loeschen:
            self._zus_intern = True
            c.setPosition(b["von"]); c.setPosition(b["bis"], QTextCursor.KeepAnchor)
            c.removeSelectedText()
            self._zus_intern = False
        else:
            self._eigenschaft_weg(P_AENDERUNG, von=b["von"], bis=b["bis"])
        c.endEditBlock()
        self.document().setModified(True)
        self._zus_geaendert()

    def alle_aenderungen(self, annehmen: bool) -> int:
        n = 0
        for b in reversed(self.aenderungen()):
            self.aenderung_annehmen(b, annehmen)
            n += 1
        return n

    def aenderung_springen(self, delta: int):
        return self._springe(self.aenderungen(), delta)

    def aenderung_am_cursor(self) -> dict | None:
        p = self.textCursor().selectionStart()
        q = self.textCursor().selectionEnd()
        for b in self.aenderungen():
            if b["von"] <= p < b["bis"] or (q > b["von"] and p < b["bis"]):
                return b
        return None

    # ---- Anzeige --------------------------------------------------------------------------------------------
    def _zus_geaendert(self) -> None:
        self._overlays_neu()
        self.zusatzGeaendert.emit()

    def set_markup(self, an: bool) -> None:
        self.markup = an
        self._overlays_neu()

    def _overlays_neu(self) -> None:
        """Wellenlinien der Schreibhilfe plus Markup (Kommentare, Änderungen) als Zusatzauswahl — nichts davon landet im Format."""
        sel = []
        doc = self.document()
        n = doc.characterCount()
        for f in getattr(self, "_wellen", []):
            if f["bis"] > n or f["von"] >= f["bis"]:
                continue
            c = QTextCursor(doc)
            c.setPosition(f["von"]); c.setPosition(f["bis"], QTextCursor.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setUnderlineStyle(QTextCharFormat.WaveUnderline)
            fmt.setUnderlineColor(QColor(self.WELLE.get(f["art"], "#868e96")))
            e = QTextEdit.ExtraSelection(); e.cursor = c; e.format = fmt
            sel.append(e)
        if self.markup and (self._hat_zusatz or self.verfolgen):
            for b in self.kommentar_bereiche():
                c = QTextCursor(doc)
                c.setPosition(b["von"]); c.setPosition(b["bis"], QTextCursor.KeepAnchor)
                fmt = QTextCharFormat(); fmt.setBackground(QColor(255, 236, 153, 140))
                e = QTextEdit.ExtraSelection(); e.cursor = c; e.format = fmt
                sel.append(e)
            for b in self.aenderungen():
                c = QTextCursor(doc)
                c.setPosition(b["von"]); c.setPosition(b["bis"], QTextCursor.KeepAnchor)
                farbe = autor_farbe(b["cf"].stringProperty(P_AUTOR))
                fmt = QTextCharFormat(); fmt.setForeground(farbe)
                if b["wert"] == "del":
                    fmt.setFontStrikeOut(True)
                else:
                    fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline); fmt.setUnderlineColor(farbe)
                e = QTextEdit.ExtraSelection(); e.cursor = c; e.format = fmt
                sel.append(e)
        self.setExtraSelections(sel)
