"""KI im Programm: Anfragen im Hintergrund, Zustimmung vor jedem Weg nach außen, Ergebnis ins Dokument."""
from __future__ import annotations

import os

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import QMessageBox

from lunivo_writer.services.settings_service import data_dir
from lunivo_writer.ai import ki as K


class _Sig(QObject):
    fertig = Signal(object, object)       # (Auftrag, Ergebnisdict)


class _Lauf(QRunnable):
    def __init__(self, auftrag, arbeit, sig):
        super().__init__()
        self.auftrag, self.arbeit, self.sig = auftrag, arbeit, sig

    def run(self):
        try:
            r = self.arbeit()
        except Exception as e:                    # eine abstürzende Anfrage darf das Schreiben nie stören
            r = {"fehler": f"Es hat nicht geklappt: {e}"}
        self.sig.fertig.emit(self.auftrag, r)


class KIDienst(QObject):
    status = Signal(str)
    laeuft = Signal(bool)
    vorschlaege = Signal(list)                # Liste von {alt, neu, grund}
    hinweis = Signal(str, str, object)        # Titel, Text, Kosten (cent) — Karte in der Seitenleiste
    chatAntwort = Signal(str, object)
    geaendert = Signal()                      # Einstellungen haben sich geändert

    def __init__(self, assistant, fenster, parent=None):
        super().__init__(parent)
        self.w = fenster
        self.assistant = assistant
        self.konfig = K.KIKonfig(os.path.join(data_dir(), "ki.json"))
        self.ki = K.KI(self.konfig, assistant.gelernt.daten)
        self._beschaeftigt = False
        self._pool = QThreadPool(self)
        self._sig = _Sig()
        self._sig.fertig.connect(self._fertig)
        self.konfig.d["empfaenger"] = assistant.thema

    # ---- Zustand ------------------------------------------------------------------
    def verfuegbar(self) -> bool:
        self.konfig.d["empfaenger"] = self.assistant.thema
        return self.ki.verfuegbar()

    def zettel(self, text: str) -> None:
        self.konfig.d["zettel"] = (text or "")[:K.ZETTEL_GRENZE]

    def _einwilligung(self, modell: str | None = None) -> bool:
        ziel = self.ki.schickt_nach_aussen(modell)
        if ziel is None:
            return True
        erlaubt = self.konfig["einwilligungen"] if "einwilligungen" in self.konfig.d else []
        if ziel in erlaubt:
            return True
        r = QMessageBox.question(
            self.w, "Text an einen Dienst senden?",
            f"Für diese Funktion wird der Text an „{ziel}“ im Internet gesendet.\n\n"
            "Er verlässt dann diesen Rechner. Auf diesem Rechner bleibt er nur, wenn Sie Ollama (lokal) wählen.\n\n"
            "Erlauben Sie das für diesen Dienst?")
        if r == QMessageBox.Yes:
            self.konfig.setze("einwilligungen", erlaubt + [ziel])
            return True
        return False

    # ---- Ablauf -------------------------------------------------------------------------
    def _eingabe(self):
        ed = self.w.current_editor()
        if ed is None:
            return None
        c = ed.textCursor()
        if c.hasSelection():
            von = min(c.anchor(), c.position())
            text = c.selectedText().replace(" ", "\n")
            return {"ed": ed, "text": text, "basis": von, "markiert": True, "rev": ed.document().revision()}
        text = ed.document().toPlainText().rstrip("\n")
        return {"ed": ed, "text": text, "basis": 0, "markiert": False, "rev": ed.document().revision()}

    def starte(self, meldung: str, arbeit, danach, eing: dict | None = None) -> None:
        """arbeit(text) → Ergebnisdict (im Hintergrund); danach(ergebnis, eingabe) im Hauptthread."""
        if self._beschaeftigt:
            return
        if not self.verfuegbar():
            self.status.emit("Dafür fehlt der KI-Schlüssel — oder Ollama auf diesem Rechner. Optionen ▸ Schreibhilfe und KI.")
            self.w.show_options("ki")
            return
        eing = eing or self._eingabe()
        if eing is None or not eing["text"].strip():
            self.status.emit("Es steht noch kein Text da.")
            return
        if not self._einwilligung():
            self.status.emit("Abgebrochen — es wurde nichts gesendet.")
            return
        self._beschaeftigt = True
        self.laeuft.emit(True)
        self.status.emit(f"Die KI liest die Markierung ({len(eing['text'])} Zeichen) …" if eing["markiert"] else meldung)
        self._pool.start(_Lauf((danach, eing), lambda: arbeit(eing["text"]), self._sig))

    def _fertig(self, auftrag, r) -> None:
        danach, eing = auftrag
        self._beschaeftigt = False
        self.laeuft.emit(False)
        if danach == "bild":
            self._bild_fertig(r, eing)
            return
        if danach == "chat":
            self.chatAntwort.emit("⚠ " + r["fehler"] if "fehler" in r else r["text"], r.get("cent"))
            return
        if "fehler" in r:
            self.status.emit(r["fehler"])
            return
        ed = eing["ed"]
        try:
            neu_rev = ed.document().revision()
        except RuntimeError:
            return
        if neu_rev != eing["rev"]:
            self.status.emit("Sie haben weitergeschrieben, während die KI gelesen hat. Ihre Antwort passt nicht mehr "
                             "zu dem, was jetzt dasteht — nichts wurde geändert. Noch einmal drücken fragt sie neu.")
            return
        danach(r, eing)

    # ---- Bild aus Text ------------------------------------------------------------------------
    def bild_aus_text(self, beschreibung: str | None = None) -> None:
        """Markierter Text (oder der übergebene) ist die Bildbeschreibung; das Bild tritt an die Stelle der Markierung."""
        if self._beschaeftigt:
            return
        ed = self.w.current_editor()
        if ed is None:
            return
        c = ed.textCursor()
        text = (beschreibung or (c.selectedText().replace(" ", "\n") if c.hasSelection() else "")).strip()
        if not text:
            self.status.emit("Erst einen Text markieren, der das Bild beschreibt.")
            return
        if not self.konfig["aufgaben"].get("bildgenerierung", "").startswith(K.EIGEN_MARKE):
            self.status.emit("Dafür fehlt ein Modell mit „Bilder“ — in der KI-Konfiguration eintragen.")
            self.w.befehle.w_kiKonfiguration()
            return
        if not self._einwilligung(self.konfig["aufgaben"]["bildgenerierung"]):
            self.status.emit("Abgebrochen — es wurde nichts gesendet.")
            return
        self._beschaeftigt = True
        self.laeuft.emit(True)
        self.status.emit("Die KI erzeugt das Bild …")
        eing = {"ed": ed, "beschreibung": text, "ersetzen": c.hasSelection()}
        self._pool.start(_Lauf(("bild", eing), lambda: self.ki.bild_erzeugen(text), self._sig))

    def _bild_fertig(self, r, eing) -> None:
        if "fehler" in r:
            self.status.emit(r["fehler"])
            return
        from PySide6.QtGui import QImage
        img = QImage.fromData(r["bild"])
        if img.isNull():
            self.status.emit("Der Anbieter hat etwas geschickt, das kein Bild ist.")
            return
        from lunivo_writer.editor import einfuegen as E
        ed = eing["ed"]
        if eing["ersetzen"] and ed.textCursor().hasSelection():
            ed.textCursor().removeSelectedText()
        E.qimage_einfuegen(ed, img, eing["beschreibung"][:200])
        self.status.emit("Bild eingefügt. Strg+Z macht es rückgängig.")

    # ---- Anwenden ---------------------------------------------------------------------------
    def _preis(self, cent) -> str:
        return (" · " + K.als_geld(cent)) if cent is not None else ""

    def _einsetzen(self, r, eing, ganz_text, markiert_text) -> None:
        if r["text"].strip() == eing["text"].strip():
            self.status.emit("Die KI hat nichts zu ändern gefunden." + self._preis(r.get("cent")))
            return
        ed = eing["ed"]
        ops, ganz, n = K.ersetze_ergebnis(eing["text"], r["text"])
        from PySide6.QtGui import QTextCursor
        sperre = QTextCursor(ed.document())
        sperre.beginEditBlock()
        try:
            for von, bis, t in ops:
                ed.replace_range(eing["basis"] + von, eing["basis"] + bis, t)
        finally:
            sperre.endEditBlock()
        self.assistant.pruefen()
        if eing["markiert"]:
            msg = markiert_text
        else:
            msg = ganz_text if ganz else f"{n} {'Absatz' if n == 1 else 'Absätze'} geändert."
        self.status.emit(msg + " Strg+Z macht es rückgängig." + self._preis(r.get("cent")))

    def korrigieren(self) -> None:
        self.ki.gelernt = self.assistant.gelernt.daten
        self.starte("Die KI liest den ganzen Text …", self.ki.korrigieren,
                    lambda r, e: self._einsetzen(r, e, "Korrigiert.", "Markierung korrigiert."))

    def uebersetzen(self, sprache: str | None = None) -> None:
        s = sprache or self.konfig["sprache"]
        self.starte(f"Wird nach {s} übersetzt …", lambda t: self.ki.uebersetzen(t, s),
                    lambda r, e: self._einsetzen(r, e, f"Nach {s} übersetzt.", f"Markierung nach {s} übersetzt."))

    def text_aktion(self, aktion: str) -> None:
        namen = dict(K.TEXT_AKTIONEN)
        n = namen.get(aktion, aktion)
        self.starte(f"„{n}“ …", lambda t: self.ki.text_aktion(t, aktion),
                    lambda r, e: self._einsetzen(r, e, n + ".", "Markierung: " + n + "."))

    def assistent(self, a: dict) -> None:
        """Eigener Assistent: ein Name und ein Prompt. Wirkung „ersetzen“ wie Korrigieren, „hinweis“ wie Zusammenfassen."""
        arbeit = lambda t: self.ki.eigener_assistent(t, a["prompt"])           # noqa: E731
        if a["modus"] == "ersetzen":
            self.starte(f"„{a['name']}“ …", arbeit, lambda r, e: self._einsetzen(r, e, a["name"] + ".", "Markierung: " + a["name"] + "."))
        else:
            self.starte(f"„{a['name']}“ …", arbeit, lambda r, e: self.hinweis.emit(a["name"], r["text"], r.get("cent")))

    def zusammenfassen(self) -> None:
        self.starte("Die KI fasst zusammen …", self.ki.zusammenfassen,
                    lambda r, e: self.hinweis.emit("Zusammenfassung", r["text"], r.get("cent")))

    def analyse(self) -> None:
        self.starte("Die KI liest den Text …", self.ki.text_analyse,
                    lambda r, e: self.hinweis.emit("Text- und Wortanalyse", r["text"], r.get("cent")))

    def vorschlaege_holen(self) -> None:
        def danach(r, e):
            lst = r.get("vorschlaege", [])
            self.vorschlaege.emit(lst)
            self.status.emit((f"{len(lst)} Vorschläge." if lst else "Die KI findet nichts, was sich leichter sagen ließe.")
                             + self._preis(r.get("cent")))
        self.starte("Die KI sucht Sätze, die sich leichter lesen ließen …", self.ki.vorschlaege, danach)

    def thesaurus(self, danach) -> None:
        """Synonyme zum Wort am Zeiger; danach(wort, woerter, von, bis) im Hauptthread."""
        ed = self.w.current_editor()
        if ed is None:
            return
        c = ed.textCursor()
        if not c.hasSelection():
            c.select(c.SelectionType.WordUnderCursor)
        wort = c.selectedText().strip()
        if not wort:
            self.status.emit("Erst ein Wort markieren oder den Zeiger hineinsetzen.")
            return
        von, bis = c.selectionStart(), c.selectionEnd()
        text = ed.document().toPlainText()
        umgebung = text[max(0, von - 120):bis + 120]
        eing = {"ed": ed, "text": umgebung, "basis": von, "markiert": False, "rev": ed.document().revision()}

        def fertig(r, e):
            lst = r.get("woerter", [])
            if not lst:
                self.status.emit("Dazu ist der KI nichts eingefallen." + self._preis(r.get("cent")))
                return
            danach(wort, lst, von, bis)
        self.starte(f"Suche Wörter für „{wort}“ …", lambda _t: self.ki.synonyme(wort, umgebung), fertig, eing)

    def vorschlag_einsetzen(self, v: dict) -> bool:
        ed = self.w.current_editor()
        if ed is None:
            return False
        text = ed.document().toPlainText()
        i = text.find(v["alt"])
        if i < 0:
            self.status.emit("Der Satz steht nicht mehr so im Text — nichts geändert.")
            return False
        return ed.replace_range(i, i + len(v["alt"]), v["neu"])

    # ---- Chat ----------------------------------------------------------------------------------
    def chat(self, verlauf: list) -> None:
        if self._beschaeftigt or not self.verfuegbar() or not self._einwilligung():
            if not self.verfuegbar():
                self.status.emit("Der Chat braucht einen KI-Schlüssel — oder Ollama. Optionen ▸ Schreibhilfe und KI.")
            return
        ed = self.w.current_editor()
        doc = ed.document().toPlainText() if ed else ""
        self._beschaeftigt = True
        self.laeuft.emit(True)
        self._pool.start(_Lauf(("chat", None), lambda: self.ki.chat(verlauf, doc), self._sig))
