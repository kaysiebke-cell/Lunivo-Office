"""Die Schreibhilfe-Seitenleiste: Prüfen, Wellen/Vorhersage/AutoKorr, Funde, „Für wen?“, KI-Knöpfe."""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from lunivo_writer.proofing.vorhersage import EMPFAENGER
from lunivo_writer.ui.sidebar.panels.writing_panel import FundKarte, HinweisKarte, VorschlagKarte
from lunivo_writer.ui.widgets.flow_layout import FlowLayout

CHIP = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 3px 12px; color: palette(window-text); }"
        "QPushButton:checked { background: #2f6fb5; color: white; border-color: #2f6fb5; }")
CHIP_GRUEN = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 0px; font-weight: bold; color: palette(window-text); }"
              "QPushButton:checked { background: #2f9e75; color: white; border-color: #2f9e75; }")
LEER = ("Nichts gefunden. Das heißt nicht, dass alles richtig ist — die Schreibhilfe sucht nur die Fehler, "
        "die ein Rechtschreibprüfer nicht finden kann.")
HILFE = """<b>Welche Hilfe wann?</b><br><br>
<b>Wellen</b> — während Sie schreiben, werden Fundstellen unterschlängelt: orange = sicher falsch, blau = kommt auf den Zusammenhang an, grau = nur zum Nachdenken.<br><br>
<b>Vorhersage</b> — nach drei Buchstaben erscheinen passende Wörter. Tab oder Eingabe übernimmt das markierte.<br><br>
<b>AutoKorr</b> — bessert das Offensichtliche, sobald ein Wort fertig ist: „ statt ", Gedankenstrich, Auslassungszeichen, Satzanfang, Wochentage.<br><br>
<b>Prüfen</b> — prüft den ganzen Text gründlich und listet jeden Fund mit Begründung auf. Sie entscheiden: Ändern oder Lassen.<br><br>
<b>KI</b> — freiwillig; ohne Schlüssel oder Ollama auf diesem Rechner bleibt sie aus. Der Text verlässt den Rechner nie ohne Ihr Zutun."""


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
        t = QLabel("<b style='font-size:12pt'>Schreib <span style='color:#2f6fb5'>|</span> hilfe</b>")
        t.setTextFormat(Qt.RichText)
        kopf.addWidget(t)
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
        zl = QHBoxLayout()
        l = QLabel("<a href='#' style='color:#6ea8e0'>Welche Hilfe wann?</a>")
        l.setTextFormat(Qt.RichText)
        l.linkActivated.connect(lambda _: self.welche_hilfe())
        zl.addWidget(l)
        zl.addStretch(1)
        v.addLayout(zl)
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

    def _alle(self):
        n = self.a.alle_aendern()
        self.a.status.emit(f"{n} Korrektur(en) übernommen.")

    def welche_hilfe(self):
        m = QMessageBox(self)
        m.setWindowTitle("Welche Hilfe wann?")
        m.setTextFormat(Qt.RichText)
        m.setText(HILFE)
        m.exec()
