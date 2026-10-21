"""Die Schreibhilfe-Seitenleiste: Prüfen, Wellen/Vorhersage/AutoKorr, Funde, „Für wen?“, KI-Knöpfe."""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (QCheckBox, 
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QToolButton, QMenu, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.proofing.vorhersage import EMPFAENGER
from lunivo_writer.ui.sidebar.panels.writing_panel import FundKarte, HinweisKarte, VorschlagKarte
from lunivo_writer.ui.widgets.flow_layout import FlowLayout

CHIP = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 3px 12px; color: palette(window-text); }"
        "QPushButton:checked { background: #2f6fb5; color: white; border-color: #2f6fb5; }")
CHIP_GRUEN = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 0px; font-weight: bold; color: palette(window-text); }"
              "QPushButton:checked { background: #2f9e75; color: white; border-color: #2f9e75; }")
LEER = ("Nichts gefunden. Das heißt nicht, dass alles richtig ist — die Schreibhilfe sucht nur die Fehler, "
        "die ein Rechtschreibprüfer nicht finden kann.")
HILFE = """**Welche Hilfe wann?**

**Wellen** — während Sie schreiben, werden Fundstellen unterschlängelt: orange = sicher falsch, blau = kommt auf den Zusammenhang an, grau = nur zum Nachdenken.

**Vorhersage** — nach drei Buchstaben erscheinen passende Wörter. Tab oder Eingabe übernimmt das markierte.

**AutoKorr** — bessert das Offensichtliche, sobald ein Wort fertig ist: „ statt ", Gedankenstrich, Auslassungszeichen, Satzanfang, Wochentage.

**Prüfen** — prüft den ganzen Text gründlich und listet jeden Fund mit Begründung auf. Sie entscheiden: Ändern oder Lassen.

**KI** — freiwillig; ohne Schlüssel oder Ollama auf diesem Rechner bleibt sie aus. Der Text verlässt den Rechner nie ohne Ihr Zutun."""


class SchreibhilfePanel(QWidget):
    _ollama_gefunden = Signal(list)
    bereich_geaendert = Signal(int)

    def __init__(self, assistent, parent=None):
        super().__init__(parent)
        self.a = assistent
        self.setMinimumWidth(300)
        self.setMaximumWidth(420)
        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(0, 0, 0, 0)
        aussen.setSpacing(0)
        self.stapel = QStackedWidget()
        aussen.addWidget(self.stapel, 1)
        seite0 = QWidget()
        self.stapel.addWidget(seite0)
        v = QVBoxLayout(seite0)
        v.setContentsMargins(14, 12, 14, 10)
        v.setSpacing(8)
        # Kopf: Titel, die drei Schalter der Schreibbrücke (We/Vo/Ko), rechts „Prüfen“
        kopf = QHBoxLayout()
        kopf.setSpacing(6)
        titel = QHBoxLayout()
        titel.setSpacing(0)
        for teil, farbe in (("Schreib", None), (" | ", "#2f6fb5"), ("hilfe", None)):
            t = text_label(teil, fett=True, pt=12, umbruch=False)
            if farbe:
                t.setStyleSheet(f"color: {farbe};")
            titel.addWidget(t)
        kopf.addLayout(titel)
        self.chips = {}
        for key, kurz, name, lang in (
                ("wellen", "We", "Wellen", "Rote Wellenlinien unter unbekannten Wörtern"),
                ("vorhersage", "Vo", "Vorhersage", "Wortvorhersage ab drei Buchstaben"),
                ("autokorr", "Ko", "AutoKorr", "AutoKorrektur beim Tippen")):
            b = QPushButton(kurz)
            b.setCheckable(True)
            b.setChecked(self.a.an(key))
            b.setToolTip(f"{name} — {lang} — {'an' if b.isChecked() else 'aus'}")
            b.setFixedSize(40, 26)
            b.setStyleSheet(CHIP_GRUEN)
            b.toggled.connect(lambda on, k=key, b=b, n=name, l=lang: (self.a.setze(k, on), b.setToolTip(f"{n} — {l} — {'an' if on else 'aus'}")))
            self.chips[key] = b
            kopf.addWidget(b)
        kopf.addStretch(1)
        self.pruefen = QPushButton("Prüfen")
        self.pruefen.clicked.connect(lambda: self.a.pruefen(True))
        kopf.addWidget(self.pruefen)
        v.addLayout(kopf)
        s = QLabel("Sucht die Fehler, die ein Rechtschreibprüfer nicht finden kann.")
        s.setWordWrap(True)
        s.setStyleSheet("color: palette(mid);")
        v.addWidget(s)
        self._einfuehrung = [s]
        zl = QHBoxLayout()
        l = QPushButton("Welche Hilfe wann?")
        l.setFlat(True); l.setCursor(Qt.PointingHandCursor)
        l.setStyleSheet("QPushButton { border: none; background: transparent; padding: 0; color: #6ea8e0; text-decoration: underline; }")
        l.clicked.connect(self.welche_hilfe)
        zl.addWidget(l)
        zl.addStretch(1)
        v.addLayout(zl)
        self._einfuehrung.append(l)
        self.liste = QVBoxLayout()
        self.liste.setSpacing(6)
        host = QWidget()
        host.setLayout(self.liste)
        self.meldung = QLabel("Noch nicht geprüft.")
        self.meldung.setWordWrap(True)
        self.meldung.setStyleSheet("color: palette(mid); padding: 8px;")
        self.liste.addWidget(self.meldung)
        self.liste.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        sc.setWidget(host)
        v.addWidget(sc, 1)
        self.alle = QPushButton("Alle sicheren Fehler ändern")
        self.alle.clicked.connect(self._alle)
        self.alle.hide()
        v.addWidget(self.alle)
        # Für wen?
        linie = QFrame()
        linie.setFrameShape(QFrame.HLine)
        linie.setFrameShadow(QFrame.Sunken)
        v.addWidget(linie)
        cap = QLabel("FÜR WEN?")
        cap.setStyleSheet("font-size: 8pt; color: palette(mid); letter-spacing: 1px;")
        v.addWidget(cap)
        fl = QWidget()
        fll = FlowLayout(fl)
        self.gruppe = QButtonGroup(self)
        for name in EMPFAENGER:
            b = QPushButton(name)
            b.setCheckable(True)
            b.setStyleSheet(CHIP)
            b.setChecked(name == self.a.thema)
            b.clicked.connect(lambda _=False, n=name: self.a.setze_thema(n))
            self.gruppe.addButton(b)
            fll.addWidget(b)
        v.addWidget(fl)
        self.worum = QLineEdit()
        self.worum.setPlaceholderText("Worum geht's? (freiwillig)")
        self.worum.setMaxLength(300)
        self.worum.setStyleSheet("QLineEdit { border: none; border-bottom: 1px dashed #c77d2e; background: transparent; "
                                 "padding: 5px 0; }")
        pal = self.worum.palette(); pal.setColor(QPalette.PlaceholderText, QColor("#c98a3d")); self.worum.setPalette(pal)
        v.addWidget(self.worum)
        ki = QHBoxLayout()
        self.ki_knoepfe = []
        for text in ("KI-Korrektur", "Vorschläge", "Nach Englisch"):
            b = QPushButton(text)
            b.setEnabled(False)
            ki.addWidget(b)
            self.ki_knoepfe.append(b)
        v.addLayout(ki)
        self.ki_info = QLabel("")
        self.ki_info.setWordWrap(True)
        self.ki_info.setStyleSheet("color: palette(mid); font-size: 9pt;")
        v.addWidget(self.ki_info)
        self.ki_aktion = QPushButton("")
        self._ki_fn = None
        self.ki_aktion.clicked.connect(lambda: self._ki_fn() if self._ki_fn else None)
        self.ki_aktion.hide()
        v.addWidget(self.ki_aktion)
        self.a.fundeGeaendert.connect(self.zeige)
        self.a.schalterGeaendert.connect(self._schalter_nachziehen)
        self.a.themaGeaendert.connect(self._thema_nachziehen)
        self._ollama_gefunden.connect(self._ollama_da)
        self._seite_ki = QScrollArea()
        self._seite_ki.setWidgetResizable(True)
        self._seite_ki.setFrameShape(QFrame.NoFrame)
        self.stapel.addWidget(self._seite_ki)

    # ---- KI ------------------------------------------------------------------------------------
    def verbinde_ki(self, dienst, fenster) -> None:
        self.ki, self.fenster = dienst, fenster
        k, v_, e_ = self.ki_knoepfe
        k.clicked.connect(dienst.korrigieren)
        v_.clicked.connect(dienst.vorschlaege_holen)
        e_.clicked.connect(lambda: dienst.uebersetzen())
        self.worum.textChanged.connect(dienst.zettel)
        dienst.vorschlaege.connect(self.zeige_vorschlaege)
        dienst.hinweis.connect(self.zeige_hinweis)
        dienst.laeuft.connect(lambda an: self.ki_aktualisieren(an))
        dienst.geaendert.connect(self.ki_aktualisieren)
        self.ki_aktualisieren()
        QTimer.singleShot(300, self._ollama_pruefen)

    # ---- Verbindung mit den Optionen: was dort (oder anderswo) umgestellt wird, steht hier sofort richtig -----------------------
    def _schalter_nachziehen(self, name: str, an: bool) -> None:
        b = self.chips.get(name)
        if b is not None and b.isChecked() != an:
            b.blockSignals(True); b.setChecked(an); b.blockSignals(False)
            b.setToolTip(b.toolTip().rsplit(" — ", 1)[0] + (" — an" if an else " — aus"))

    def _thema_nachziehen(self, name: str) -> None:
        for b in self.gruppe.buttons():
            if b.text() == name and not b.isChecked():
                b.setChecked(True)

    def ki_aktualisieren(self, laeuft: bool = False) -> None:
        ok = self.ki.verfuegbar()
        for b in self.ki_knoepfe:
            b.setEnabled(ok and not laeuft)
        self.ki_knoepfe[2].setText("Nach " + self.ki.konfig["sprache"])
        if ok:
            ziel = self.ki.ki.schickt_nach_aussen()
            self.ki_info.setText("Die KI läuft auf diesem Rechner — der Text verlässt ihn nicht." if ziel is None
                                 else f"Beim Drücken geht der Text an „{ziel}“ (nur nach Ihrer Zustimmung).")
            self.ki_aktion.hide()
        else:
            self.ki_info.setText("Die drei Knöpfe sind grau, weil kein KI-Schlüssel gespeichert ist. "
                                 "Ollama auf diesem Rechner geht ohne Schlüssel und ohne Geld.")
            self.ki_aktion.setText("Einrichten …")
            self._ki_fn = lambda: self.fenster.show_options("ki")
            self.ki_aktion.show()

    def _ollama_pruefen(self) -> None:
        from PySide6.QtCore import QRunnable, QThreadPool

        panel = self

        class _O(QRunnable):
            def run(s_):
                try:
                    panel._ollama_gefunden.emit(panel.ki.ki.ollama_modelle())
                except Exception:
                    pass
        if not hasattr(self, "_ollama_gefunden"):
            return
        QThreadPool.globalInstance().start(_O())

    def _ollama_da(self, modelle: list) -> None:
        if self.ki.verfuegbar() or not modelle:
            return
        m = modelle[0]
        self.ki_info.setText("Auf diesem Rechner läuft Ollama — damit gehen die Knöpfe ohne Schlüssel und ohne Geld.")
        self.ki_aktion.setText(f"{m} nehmen")
        self._ki_fn = lambda: (self.ki.konfig.setze("modell", "ollama:" + m), self.ki_aktualisieren())
        self.ki_aktion.show()

    def zeige_vorschlaege(self, lst: list) -> None:
        self._karten_leeren()
        if not lst:
            self._leer("Die KI findet nichts, was sich leichter sagen ließe.")
            return
        for i, v in enumerate(lst):
            self.liste.insertWidget(i, VorschlagKarte(v, self.ki, self))

    def zeige_hinweis(self, titel: str, text: str, cent) -> None:
        self._karten_leeren()
        self.liste.insertWidget(0, HinweisKarte(titel, text, cent, self.fenster, self))

    def _karten_leeren(self) -> None:
        while self.liste.count() > 1:
            it = self.liste.takeAt(0)
            if it.widget():
                it.widget().hide(); it.widget().setParent(None); it.widget().deleteLater()

    def _leer(self, text: str) -> None:
        m = QLabel(text); m.setWordWrap(True)
        m.setStyleSheet("color: palette(mid); padding: 8px;")
        self.liste.insertWidget(0, m)

    # ---- Texteffekte formatieren (Eigenschaften-Bereich, nur sichtbar, solange der Benutzer ihn gerufen hat)
    effekt_panel = None

    def _formatierung_host(self, panel_klasse, menue_text: str, werte: dict):
        """Der gemeinsame Rahmen der Bereiche „Formatierung“: Kopf mit „Formatierung ▾“, Anheften und Schließen, darunter das Panel."""
        host = QWidget()
        v = QVBoxLayout(host); v.setContentsMargins(12, 10, 12, 10); v.setSpacing(8)
        kopf = QHBoxLayout(); kopf.setSpacing(4) # wie in der Vorlage: „Formatierung ▾“, rechts Anheften und Schließen
        titel = QToolButton(); titel.setText("Formatierung"); titel.setPopupMode(QToolButton.InstantPopup); titel.setAutoRaise(True)
        titel.setToolButtonStyle(Qt.ToolButtonTextOnly)
        menue = QMenu(titel); menue.addAction(menue_text); titel.setMenu(menue)
        kopf.addWidget(titel); kopf.addStretch(1)
        anheften = QToolButton(); anheften.setText("⚲"); anheften.setCheckable(True); anheften.setAutoRaise(True)
        anheften.setToolTip("Anheften: der Bereich folgt der Markierung und bleibt offen")
        zu = QToolButton(); zu.setText("✕"); zu.setAutoRaise(True); zu.setToolTip("Schließen"); zu.clicked.connect(lambda: self.zeige_bereich(0))
        kopf.addWidget(anheften); kopf.addWidget(zu)
        v.addLayout(kopf)
        panel = panel_klasse(host, werte)
        v.addWidget(panel, 1)
        return host, panel, anheften

    def zeige_texteffekte(self, werte: dict, anwenden) -> None:
        """„Texteffekte formatieren“ in der Seitenleiste zeigen. ``anwenden(werte)`` wird bei jeder Änderung gerufen — die Wirkung ist sofort sichtbar."""
        from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektPanel
        if self.effekt_panel is None:
            host, self.effekt_panel, self.effekt_anheften = self._formatierung_host(TexteffektPanel, "Texteffekte formatieren", werte)
            self._effekt_seite = host
            self._effekt_index = self.stapel.addWidget(host)
        else:
            try:
                self.effekt_panel.geaendert.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.effekt_panel.setze({**werte})
        self.effekt_panel.geaendert.connect(anwenden)
        self.zeige_bereich(self._effekt_index)

    # ---- Formatierung eines Bildes oder einer Form (Reiter „Füllung und Linie“, „Effekte“) ----------------------------------------------
    objekt_panel = None

    def zeige_objektformat(self, werte: dict, anwenden, reiter: int = 0, bild_wunsch=None) -> None:
        """„Formatierung“ für das markierte Bild zeigen; ``reiter``: 0 = Füllung und Linie, 1 = Effekte. ``anwenden(werte)`` kommt bei jeder Änderung."""
        from lunivo_writer.ui.baukasten.objektformat_panel import ObjektFormatPanel
        if self.objekt_panel is None:
            host, self.objekt_panel, self.objekt_anheften = self._formatierung_host(ObjektFormatPanel, "Objekt formatieren", werte)
            self._objekt_index = self.stapel.addWidget(host)
        else:
            for sig in (self.objekt_panel.geaendert, self.objekt_panel.bild_gewuenscht):
                try:
                    sig.disconnect()
                except (RuntimeError, TypeError):
                    pass
            self.objekt_panel.setze({**werte})
        self.objekt_panel.geaendert.connect(anwenden)
        if bild_wunsch is not None:
            self.objekt_panel.bild_gewuenscht.connect(bild_wunsch)
        self.objekt_panel.reiter.setCurrentIndex(reiter)
        self.zeige_bereich(self._objekt_index)

    def objektformat_sichtbar(self) -> bool:
        return self.objekt_panel is not None and self.stapel.currentIndex() == self._objekt_index and not self.isHidden()

    def aktualisiere_objektformat(self, werte: dict) -> None:
        from PySide6.QtWidgets import QApplication
        f = QApplication.focusWidget()
        if self.objekt_panel is not None and not (f is not None and self.objekt_panel.isAncestorOf(f)):
            self.objekt_panel.setze(werte)

    def texteffekte_sichtbar(self) -> bool:
        return self.effekt_panel is not None and self.stapel.currentIndex() == self._effekt_index and not self.isHidden()

    def aktualisiere_texteffekte(self, werte: dict) -> None:
        """Die Werte des Panels an die Markierung anpassen (wenn der Benutzer gerade nicht darin bedient)."""
        from PySide6.QtWidgets import QApplication
        f = QApplication.focusWidget()
        if self.effekt_panel is not None and not (f is not None and self.effekt_panel.isAncestorOf(f)):
            self.effekt_panel.setze(werte)

    def zeige_bereich(self, i: int) -> None:
        """0 = Schreibhilfe, 1 = KI-Chat."""
        self.stapel.setCurrentIndex(i)
        self.bereich_geaendert.emit(i)

    def setze_bereiche(self, band, ki_gruppen: list) -> None:
        """Den KI-Bereich aus den Gruppen des Reiters Schreibhilfe bauen (Chat und KI-Gruppen)."""
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        zurueck = QPushButton("Zur Schreibhilfe")
        zurueck.clicked.connect(lambda: self.zeige_bereich(0))
        lay.addWidget(zurueck)
        from lunivo_writer.ui.sidebar.panels.ai_panel import ChatPanel
        self.chat = ChatPanel(self.ki, self.fenster)
        lay.addWidget(self.chat, 1)
        for g in ki_gruppen:
            lay.addWidget(band.gruppe_widget(g))
        self._seite_ki.setWidget(host)

    def zeige(self, funde: list) -> None:
        while self.liste.count() > 1:
            it = self.liste.takeAt(0)
            if it.widget():
                it.widget().hide()
                it.widget().setParent(None)
                it.widget().deleteLater()
        if not funde:
            self.meldung = QLabel(LEER if self.a._geprueft_rev >= 0 else "Noch nicht geprüft.")
            self.meldung.setWordWrap(True)
            self.meldung.setStyleSheet("color: palette(mid); padding: 8px;")
            self.liste.insertWidget(0, self.meldung)
        for i, f in enumerate(funde):
            self.liste.insertWidget(i, FundKarte(f, self.a))
        self.alle.setVisible(any(f["art"] == "fehler" and f["neu"] for f in funde))
        for w in self._einfuehrung:                                 # mit Funden steht die Liste ganz oben, wie in der ersten Fassung
            w.setVisible(not funde)

    def _alle(self):
        n = self.a.alle_aendern()
        self.a.status.emit(f"{n} Korrektur(en) übernommen.")

    def welche_hilfe(self):
        m = QMessageBox(self)
        m.setWindowTitle("Welche Hilfe wann?")
        m.setTextFormat(Qt.MarkdownText)
        m.setText(HILFE)
        m.exec()
