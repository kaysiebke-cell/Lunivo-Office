"""Die Schreibhilfe: prüft im Hintergrund, hält den Stand, setzt Korrekturen ein.

Orientiert an language-bridge.js: Die Prüfung besitzt die Regeln, die Brücke den
Zustand — welche Fassung des Textes geprüft wurde, was angenommen oder
weggewinkt wurde. Ein spätes Ergebnis für einen längst geänderten Text wird
verworfen und neu angestoßen.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from ..storage.gelernt import Gelernt
from . import autokorrektur, pruefung, vorhersage

ART_REIHENFOLGE = {"fehler": 0, "tipp": 1, "hinweis": 2}


def zeige_leer(s: str) -> str:
    return s.replace(" ", "␣").replace("\n", "⏎")


class _Signale(QObject):
    fertig = Signal(int, list)


class _Lauf(QRunnable):
    def __init__(self, rev: int, text: str, gelernt: dict, signale: _Signale, schalter: dict | None = None):
        super().__init__()
        self.rev, self.text, self.gelernt, self.sig, self.schalter = rev, text, gelernt, signale, schalter

    def run(self):
        try:
            funde = pruefung.finde_probleme(self.text, self.gelernt, self.schalter)
        except Exception:        # Eine Prüfung, die abstürzt, darf das Schreiben nie stören
            funde = []
        self.sig.fertig.emit(self.rev, funde)


class WritingAssistant(QObject):
    fundeGeaendert = Signal(list)         # sichtbare Funde (ohne die weggewinkten)
    status = Signal(str)

    def __init__(self, settings, gelernt: Gelernt | None = None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.gelernt = gelernt or Gelernt()
        self.editor = None
        self.funde: list[dict] = []
        self._roh: list[dict] = []
        self._weg: set[tuple] = set()
        self._alle_weg: set[str] = set()            # Wörter, die im ganzen Dokument in Ruhe bleiben (nur diese Sitzung)
        self._geprueft_rev = -1
        self._laeuft = False
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._sig = _Signale()
        self._sig.fertig.connect(self._fertig)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(900)
        self._timer.timeout.connect(self.pruefen)
        self.thema = settings.get("schreibhilfe/thema", "egal")
        vorhersage.thema_aufnehmen(vorhersage.thema_woerter(self.thema)) if self.thema != "egal" else None

    # ---- Schalter ---------------------------------------------------------
    def an(self, name: str) -> bool:
        std = {"wellen": True, "vorhersage": True, "autokorr": True}.get(name, True)
        return self.settings.get_bool("schreibhilfe/" + name, std)

    def setze(self, name: str, wert: bool) -> None:
        self.settings.set("schreibhilfe/" + name, wert)
        if name == "wellen":
            if wert:
                self.pruefen()
            elif self.editor is not None:
                self.editor.set_wellen([])
        self.status.emit(f"{name.capitalize()} {'an' if wert else 'aus'}.")

    def setze_thema(self, name: str) -> None:
        self.thema = name
        self.settings.set("schreibhilfe/thema", name)
        if name != "egal":
            vorhersage.thema_aufnehmen(vorhersage.thema_woerter(name))

    def ak_an(self, name: str) -> bool:
        return self.settings.get_bool("schreibhilfe/" + name, autokorrektur.SCHALTER[name][0])

    # ---- Anbindung an den Editor ---------------------------------------------
    def attach(self, editor) -> None:
        if self.editor is editor:
            return
        self.editor = editor
        self._weg.clear()
        self._alle_weg.clear()                      # beim Wechsel des Dokuments fangen die Ausnahmen bei null an
        if editor is not None:
            editor.vorhersage = self.vorschlaege
            editor.autokorr = self.autokorr
            editor.kontext_hook = self.erweitere_menue
            self.anzeigen([])
            if self.an("wellen") and editor.document().characterCount() > 1:
                self._timer.start()
        else:
            self.anzeigen([])

    def dokument_geaendert(self) -> None:
        if self.an("wellen") and self.editor is not None:
            self._timer.start()

    # ---- Prüfen --------------------------------------------------------------------
    def pruefen(self) -> None:
        ed = self.editor
        if ed is None:
            return
        if self._laeuft:
            self._timer.start()
            return
        doc = ed.document()
        self._laeuft = True
        schalter = {k: self.settings.get_bool(k, True) for k in ("rsGrossIgnorieren", "rsZahlenIgnorieren", "rsPfadeIgnorieren")}
        self._pool.start(_Lauf(doc.revision(), doc.toPlainText(), self.gelernt.daten, self._sig, schalter))

    def _fertig(self, rev: int, roh: list) -> None:
        self._laeuft = False
        ed = self.editor
        if ed is None:
            return
        if rev != ed.document().revision():          # Text hat sich inzwischen geändert
            self._timer.start()
            return
        self._geprueft_rev = rev
        self._roh = roh
        n = ed.document().characterCount() - 1
        self._zeigen(f"{n} Zeichen geprüft, {len([f for f in roh if self._key(f) not in self._weg])} Funde.")

    def _key(self, f: dict) -> tuple:
        t = self.editor.document().toPlainText() if self.editor else ""
        return (f["alt"], f["neu"], f["grund"], t[max(0, f["von"] - 12):f["von"]])

    def _zeigen(self, meldung: str | None = None) -> None:
        sichtbar = [dict(f, zeigeAlt=zeige_leer(f["alt"]), zeigeNeu=zeige_leer(f["neu"]))
                    for f in self._roh if self._key(f) not in self._weg and f["alt"].lower() not in self._alle_weg]
        sichtbar.sort(key=lambda f: (ART_REIHENFOLGE.get(f["art"], 3), f["von"]))
        self.anzeigen(sichtbar)
        if meldung:
            self.status.emit(meldung)

    def anzeigen(self, funde: list) -> None:
        self.funde = funde
        if self.editor is not None:
            self.editor.set_wellen(funde if self.an("wellen") else [])
        self.fundeGeaendert.emit(funde)

    # ---- Rechtsklick-Menü ------------------------------------------------------------------
    def funde_an(self, pos: int) -> list[dict]:
        return [f for f in self.funde if f["von"] <= pos <= f["bis"] and f["von"] < f["bis"]]

    def erweitere_menue(self, menu, pos: int) -> None:
        """Ein Kopf, ein Vorschlag je Möglichkeit, drei Aktionen — wie im Prüfbogen (Kontextmenü für Fehler-Aktionen)."""
        ed = self.editor
        if ed is None or not self.an("wellen"):
            return
        gefunden = self.funde_an(pos)
        wort = self._wort_an(pos)
        vorschlaege: list[tuple[str, dict | None]] = []
        for f in gefunden:
            if f["neu"] and f["art"] != "hinweis":
                vorschlaege.append((f["neu"], f))
        if wort:
            from . import pruefung
            schon = {t for t, _f in vorschlaege}
            for k in pruefung.vorschlaege_fuer(wort[0], 6, self.gelernt.daten):
                if pruefung.uebernimm_schreibweise(wort[0], k) in schon:
                    continue
                vorschlaege.append((pruefung.uebernimm_schreibweise(wort[0], k), {"von": wort[1], "bis": wort[2], "alt": wort[0],
                                                                                    "neu": k, "wortEbene": True, "art": "tipp",
                                                                                    "grund": "Vorschlag"}))
        if not vorschlaege and not gefunden and not wort:
            return
        erste = menu.actions()[0] if menu.actions() else None
        from PySide6.QtGui import QAction, QFont
        neu = []
        if gefunden:
            k = QAction(gefunden[0]["grund"], menu); k.setEnabled(False); neu.append(k)
        for text, fund in vorschlaege:
            a = QAction(text, menu)
            f = a.font() if hasattr(a, "font") else QFont()
            f.setBold(True); a.setFont(f)
            a.triggered.connect(lambda _=False, fd=fund: self.aendern(fd))
            neu.append(a)
        if gefunden or vorschlaege or wort:
            ziel = gefunden[0] if gefunden else (vorschlaege[0][1] if vorschlaege else None)
            n1 = QAction("Einmal ignorieren", menu)
            n2 = QAction("Alle ignorieren", menu)
            if ziel is not None:
                n1.triggered.connect(lambda _=False, fd=ziel: self.lassen(fd))
                n2.triggered.connect(lambda _=False, fd=ziel: self.alle_ignorieren(fd["alt"]))
            else:
                n1.setEnabled(False); n2.setEnabled(False)
            neu += [n1, n2]
            if wort and not gefunden and vorschlaege == []:
                pass
            if wort:
                n3 = QAction("Zum Wörterbuch hinzufügen", menu)
                n3.triggered.connect(lambda _=False, w=wort[0]: self.zum_woerterbuch(w))
                neu.append(n3)
        for a in neu:
            menu.insertAction(erste, a)
        menu.insertSeparator(erste)

    def _wort_an(self, pos: int):
        """(Wort, von, bis), wenn an der Stelle ein Wort steht, das das Wörterbuch nicht kennt."""
        from . import pruefung
        text = self.editor.document().toPlainText()
        for m in pruefung.WORT_MUSTER.finditer(text):
            if m.start() <= pos <= m.end():
                w = m.group(0)
                if len(w) > 1 and w.lower() not in pruefung.lade_woerter() and not self.gelernt.daten["inRuhe"].get(w.lower()):
                    return w, m.start(), m.end()
        return None

    def alle_ignorieren(self, wort: str) -> None:
        self._alle_weg.add(wort.lower())
        self._zeigen()

    def zum_woerterbuch(self, wort: str) -> None:
        self.gelernt.daten["inRuhe"][wort.lower()] = True
        self.gelernt.speichern()
        self.pruefen()

    def ignorierte_wieder_pruefen(self) -> int:
        n = len(self._weg) + len(self._alle_weg)
        self._weg.clear(); self._alle_weg.clear()
        self._zeigen()
        return n

    # ---- Gründlich prüfen (eigene Regeln + LanguageTool, wenn eingerichtet) -------------------
    def gruendlich(self) -> None:
        from ..integrations import languagetool
        self.pruefen()
        if not languagetool.verfuegbar():
            self.status.emit("Gründlich: LanguageTool ist nicht eingerichtet — es gelten die eigenen Regeln. "
                             "Hinweise dazu: doku/native-qt/INSTALLATION.md")
            return
        ed = self.editor
        if ed is None:
            return
        text = ed.document().toPlainText()
        pool = QThreadPool.globalInstance()

        class _LT(QRunnable):
            def __init__(self, sig, rev):
                super().__init__(); self.sig, self.rev = sig, rev

            def run(self):
                try:
                    funde = languagetool.pruefe(text)
                except languagetool.LanguageToolFehler as e:
                    self.sig.fertig.emit(-1, [str(e)])
                    return
                self.sig.fertig.emit(self.rev, funde)

        self._lt_sig = _Signale()
        self._lt_sig.fertig.connect(self._lt_fertig)
        self.status.emit("LanguageTool prüft …")
        pool.start(_LT(self._lt_sig, ed.document().revision()))

    def _lt_fertig(self, rev: int, funde: list) -> None:
        if rev == -1:
            self.status.emit(str(funde[0]) if funde else "LanguageTool-Fehler.")
            return
        ed = self.editor
        if ed is None or rev != ed.document().revision():
            return
        belegt = [(f["von"], f["bis"]) for f in self._roh]
        neu = [f for f in funde if not any(f["von"] < b and a < f["bis"] for a, b in belegt)]
        self._roh = self._roh + neu
        self._zeigen(f"Gründlich geprüft: {len(neu)} zusätzliche Hinweise von LanguageTool.")

    # ---- Annehmen / weglassen ----------------------------------------------------------
    def aendern(self, fund: dict) -> bool:
        ed = self.editor
        if ed is None or not fund["neu"] and fund["art"] == "hinweis":
            return False
        if not ed.replace_range(fund["von"], fund["bis"], fund["neu"], erwartet=fund["alt"]):
            self.status.emit("Der Text hat sich an dieser Stelle geändert — bitte neu prüfen.")
            return False
        self.gelernt.gewaehlt(fund)
        self.pruefen()
        return True

    def lassen(self, fund: dict) -> None:
        self._weg.add(self._key(fund))
        self.gelernt.stehen_gelassen(fund)
        self._zeigen()

    def alle_aendern(self) -> int:
        n = 0
        for f in sorted((f for f in self.funde if f["art"] == "fehler" and f["neu"]), key=lambda f: -f["von"]):
            if self.editor.replace_range(f["von"], f["bis"], f["neu"], erwartet=f["alt"]):
                self.gelernt.gewaehlt(f)
                n += 1
        self.pruefen()
        return n

    # ---- Vorhersage und AutoKorrektur (vom Editor aufgerufen) --------------------------
    def vorschlaege(self, anfang: str) -> list[str]:
        if not self.an("vorhersage"):
            return []
        return vorhersage.faengt_an_mit(anfang, 8, self.gelernt.daten, vorhersage.thema_woerter(self.thema))

    def autokorr(self, text_vor_cursor: str) -> str:
        if not self.an("autokorr"):
            return text_vor_cursor
        return autokorrektur.korrigiere(text_vor_cursor, self.ak_an)
