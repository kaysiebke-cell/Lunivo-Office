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
    def __init__(self, rev: int, text: str, gelernt: dict, signale: _Signale):
        super().__init__()
        self.rev, self.text, self.gelernt, self.sig = rev, text, gelernt, signale

    def run(self):
        try:
            funde = pruefung.finde_probleme(self.text, self.gelernt)
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
        if editor is not None:
            editor.vorhersage = self.vorschlaege
            editor.autokorr = self.autokorr
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
        self._pool.start(_Lauf(doc.revision(), doc.toPlainText(), self.gelernt.daten, self._sig))

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
                    for f in self._roh if self._key(f) not in self._weg]
        sichtbar.sort(key=lambda f: (ART_REIHENFOLGE.get(f["art"], 3), f["von"]))
        self.anzeigen(sichtbar)
        if meldung:
            self.status.emit(meldung)

    def anzeigen(self, funde: list) -> None:
        self.funde = funde
        if self.editor is not None:
            self.editor.set_wellen(funde if self.an("wellen") else [])
        self.fundeGeaendert.emit(funde)

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
