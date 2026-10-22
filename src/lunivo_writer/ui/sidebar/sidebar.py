"""Die Schreibhilfe-Seitenleiste: Prüfen, Wellen/Vorhersage/AutoKorr, Funde, „Für wen?“, KI-Knöpfe."""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (QCheckBox, QComboBox,
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QToolButton, QMenu, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.proofing.vorhersage import EMPFAENGER
from lunivo_writer.ui.sidebar.panels.writing_panel import FundKarte, HinweisKarte, VorschlagKarte
from lunivo_writer.ui.widgets.flow_layout import FlowLayout

WERK_REITER = ("QPushButton { border: none; border-bottom: 3px solid transparent; border-radius: 0; padding: 4px 6px; font-weight: bold; color: palette(mid); background: transparent; }"
               "QPushButton:checked { color: palette(window-text); border-bottom: 3px solid #2f6fb5; }"
               "QPushButton:hover { color: palette(window-text); }"
               "QPushButton:focus { border-bottom: 3px solid #2f6fb5; }")
CHIP = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 3px 12px; color: palette(window-text); }"
        "QPushButton:checked { background: #2f6fb5; color: white; border-color: #2f6fb5; }")
CHIP_GRUEN = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 0px; font-weight: bold; color: palette(window-text); }"
              "QPushButton:checked { background: #2f9e75; color: white; border-color: #2f9e75; }")
LEER = ("Nichts gefunden. Das heißt nicht, dass alles richtig ist — die Schreibhilfe sucht nur die Fehler, "
        "die ein Rechtschreibprüfer nicht finden kann.")
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
        w0 = QVBoxLayout(seite0); w0.setContentsMargins(0, 0, 0, 0); w0.setSpacing(0)
        # Werkbank: vier Reiter nach dem, was man gerade braucht — Prüfen (die Funde), Lesen, Schreiben, KI
        from lunivo_writer.ui.schreibhilfe_katalog import REITER
        leiste = QHBoxLayout(); leiste.setContentsMargins(10, 8, 10, 0); leiste.setSpacing(4)
        self.werk_reiter = QButtonGroup(self)
        self._werk_namen = list(REITER)
        for i, name in enumerate(REITER):
            b = QPushButton(name); b.setCheckable(True); b.setChecked(i == 0); b.setMinimumHeight(36); b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(WERK_REITER)
            self.werk_reiter.addButton(b, i); leiste.addWidget(b, 1)
        self._werk_leiste = QWidget(); self._werk_leiste.setLayout(leiste); self._werk_leiste.hide()      # die Reiter stehen in der Leiste rechts (Seitenleiste), nicht mehr oben: mehr Platz
        self.werk_stapel = QStackedWidget()
        w0.addWidget(self.werk_stapel, 1)
        self.werk_reiter.idClicked.connect(self.werk_stapel.setCurrentIndex)
        pruef_seite = QWidget()
        self.werk_stapel.addWidget(pruef_seite)
        v = QVBoxLayout(pruef_seite)
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
        self.chips = {}                                   # We/Vo/Ko stehen jetzt auf dem Reiter „Schreiben“ — hier bleibt mehr Platz für die Funde
        kopf.addStretch(1)
        l = QToolButton(); l.setText("?"); l.setAutoRaise(True); l.setCursor(Qt.PointingHandCursor); l.setFixedSize(30, 30)   # in der Titelzeile: spart eine Zeile
        l.setStyleSheet("QToolButton { font-weight: bold; font-size: 11pt; border: 1px solid palette(mid); border-radius: 15px; }"
                        "QToolButton:hover { background: palette(alternate-base); }")
        l.setToolTip("Welche Hilfe wann? (F6)"); l.setAccessibleName("Welche Hilfe wann")
        l.clicked.connect(self.welche_hilfe)
        kopf.addWidget(l)
        v.addLayout(kopf)
        self._einfuehrung = []
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
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)           # nie seitlich rollen müssen: alles auf der Karte (auch der Lautsprecher) bleibt erreichbar
        sc.setMinimumHeight(200)                                        # der Hauptinhalt: die Funde bekommen immer Platz, auch auf kleinen Bildschirmen
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
        # Eine Zeile statt zwei Reihen Chips: „Für wen?“ als Auswahl, daneben „Worum geht's?“ — der Platz gehört den Funden
        kontext = QHBoxLayout(); kontext.setSpacing(8)
        fw = QLabel("Für wen"); fw.setStyleSheet("color: palette(mid); font-size: 9pt;")
        self.thema = QComboBox()
        for name in EMPFAENGER:
            self.thema.addItem(name)
        self.thema.setCurrentText(self.a.thema)
        self.thema.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.thema.setToolTip("Für wen schreiben Sie? Danach richtet sich, was als Fehler zählt und welche Wörter vorgeschlagen werden.")
        self.thema.setAccessibleName("Für wen")
        self.thema.currentTextChanged.connect(self.a.setze_thema)
        self.worum = QLineEdit()
        self.worum.setPlaceholderText("Worum geht's? (freiwillig)")
        self.worum.setMaxLength(300)
        self.worum.setStyleSheet("QLineEdit { border: none; border-bottom: 1px dashed #c77d2e; background: transparent; "
                                 "padding: 5px 0; }")
        pal = self.worum.palette(); pal.setColor(QPalette.PlaceholderText, QColor("#c98a3d")); self.worum.setPalette(pal)
        kontext.addWidget(fw); kontext.addWidget(self.thema); kontext.addWidget(self.worum, 1)
        v.addLayout(kontext)
        # Unten, wo man nach dem Schreiben hinschaut: „Prüfen“ mit seiner Erklärung, darunter die beiden KI-Wege
        zk = QHBoxLayout(); zk.setSpacing(6)                          # eine Zeile: Prüfen · KI-Korrektur · Vorschläge
        self.pruefen = QPushButton("Prüfen")
        self.pruefen.setToolTip("Prüfen (F7) — sucht die Fehler, die ein Rechtschreibprüfer nicht finden kann")
        self.pruefen.clicked.connect(lambda: self.a.pruefen(True))
        self.ki_korrektur = QPushButton("KI-Korrektur"); self.ki_korrektur.setToolTip("KI-Korrektur (F8)")
        self.ki_vorschlaege = QPushButton("Vorschläge"); self.ki_vorschlaege.setToolTip("Verbesserungsvorschläge")
        for b_ in (self.pruefen, self.ki_korrektur, self.ki_vorschlaege):
            b_.setMinimumHeight(34); zk.addWidget(b_, 1)
        v.addLayout(zk)
        self.ki_info = QLabel("")                                        # steht auf dem Reiter KI, solange kein Modell verbunden ist
        self.ki_info.setWordWrap(True)
        self.ki_info.setStyleSheet("color: palette(mid);")
        self.ki_aktion = QPushButton("")
        self._ki_fn = None
        self.ki_aktion.clicked.connect(lambda: self._ki_fn() if self._ki_fn else None)
        self.a.fundeGeaendert.connect(self.zeige)
        self.a.schalterGeaendert.connect(self._schalter_nachziehen)
        self.a.themaGeaendert.connect(self._thema_nachziehen)
        self._ollama_gefunden.connect(self._ollama_da)
        self._seite_ki = QScrollArea()
        self._seite_ki.setWidgetResizable(True)
        self._seite_ki.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)        # der Chat passt sich der Breite an, nichts wird seitlich abgeschnitten
        self._seite_ki.setFrameShape(QFrame.NoFrame)
        self.stapel.addWidget(self._seite_ki)

    # ---- KI ------------------------------------------------------------------------------------
    def verbinde_ki(self, dienst, fenster) -> None:
        self.ki, self.fenster = dienst, fenster
        self._werk_bauen()
        self.ki_korrektur.clicked.connect(lambda: fenster.befehle.tun("kiKorrektur"))            # ohne KI führt der Klick in die KI-Einstellungen
        self.ki_vorschlaege.clicked.connect(lambda: fenster.befehle.tun("kiVorschlaege"))
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
        if self.thema.currentText() != name:
            self.thema.blockSignals(True); self.thema.setCurrentText(name); self.thema.blockSignals(False)

    def ki_aktualisieren(self, laeuft: bool = False) -> None:
        """Ohne Modell steht oben auf dem Reiter KI der Weg dorthin; die Zeilen selbst bleiben bedienbar (ein Klick führt in die KI-Einstellungen)."""
        ok = self.ki.verfuegbar()
        if ok:
            ziel = self.ki.ki.schickt_nach_aussen()
            info = ("Die KI läuft auf diesem Rechner — der Text verlässt ihn nicht." if ziel is None
                    else f"Beim Drücken geht der Text an „{ziel}“ (nur nach Ihrer Zustimmung).")
            for z in self.werk["KI"].zeilen:
                z.setToolTip((z.f.hinweis + " — " if z.f.hinweis else "") + info)
            self.ki_banner.hide()
        else:
            self.ki_info.setText("Es ist noch kein KI-Modell verbunden. Ollama auf diesem Rechner geht ohne Schlüssel und ohne Geld.")
            self.ki_aktion.setText("KI einrichten …")
            self._ki_fn = lambda: self.fenster.befehle.tun("w.kiEinstellungen")
            self.ki_banner.show()
        self.werkbank_aktualisieren()

    # ---- Werkbank --------------------------------------------------------------------------------
    def _werk_bauen(self) -> None:
        """Die Reiter Lesen, Schreiben und KI aus dem Katalog; der Reiter Prüfen sind die Funde plus die Wege dahin."""
        from lunivo_writer.ui.baukasten.werkbank import Werkbank
        self.ki_banner = QWidget()
        bl = QVBoxLayout(self.ki_banner); bl.setContentsMargins(0, 0, 0, 6)
        bl.addWidget(self.ki_info); bl.addWidget(self.ki_aktion)
        self.werk = {}
        for name in self._werk_namen[1:]:
            self.werk[name] = Werkbank(self.fenster, name, self.ki_banner if name == "KI" else None)
            self.werk_stapel.addWidget(self.werk[name])
        self.a.schalterGeaendert.connect(lambda *_: self.werkbank_aktualisieren())

    def werkbank_aktualisieren(self) -> None:
        for w in getattr(self, "werk", {}).values():
            w.aktualisieren()

    @property
    def aktueller_reiter(self) -> str:
        return self._werk_namen[self.werk_stapel.currentIndex()]

    def zeige_reiter(self, name: str) -> None:
        """Einen Reiter der Werkbank öffnen (und die Seitenleiste auf die Schreibhilfe stellen)."""
        i = self._werk_namen.index(name)
        self.werk_reiter.button(i).setChecked(True)
        self.werk_stapel.setCurrentIndex(i)
        self.zeige_bereich(0)

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
        self._funde_zeigen()
        if not lst:
            self._leer("Die KI findet nichts, was sich leichter sagen ließe.")
            return
        for i, v in enumerate(lst):
            self.liste.insertWidget(i, VorschlagKarte(v, self.ki, self))

    def _funde_zeigen(self) -> None:
        """Ergebnisse (Hinweise, Vorschläge, Übersetzung) erscheinen auf dem Reiter Prüfen — die Seitenleiste wird dafür geöffnet und umgestellt."""
        if self.isHidden() and hasattr(self.fenster, "toggle_sidebar"):
            self.fenster.toggle_sidebar()
        self.zeige_reiter("Prüfen")

    def zeige_hinweis(self, titel: str, text: str, cent) -> None:
        self._karten_leeren()
        self.liste.insertWidget(0, HinweisKarte(titel, text, cent, self.fenster, self))
        self._funde_zeigen()

    def _karten_leeren(self) -> None:
        while self.liste.count() > 1:
            it = self.liste.takeAt(0)
            w_ = it.widget()
            if w_ is not None:
                w_.hide(); w_.setParent(None); w_.deleteLater()

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

    def zusatz_ausfuehren(self, d) -> bool:
        """Ein Zusatzfenster als Seite hier in der Seitenleiste zeigen, solange man es bearbeitet (wie ``d.exec()``). Die Breite bleibt."""
        from lunivo_writer.ui.baukasten.zusatz_panel import ZusatzPanel, ausfuehren_in
        if getattr(self, "_zusatz", None) is not None:                       # es ist schon eines offen: das alte schließt
            self._zusatz._schliessen()
        seite = ZusatzPanel()
        seite.verfuegbar = max(300, min(self.width(), 420)) - 56                      # Seitenleiste ohne Ränder und Rollbalken
        self._zusatz = seite
        i = self.stapel.addWidget(seite)
        vorher = (self.stapel.currentIndex(), self.isHidden())

        def zeigen() -> None:
            if self.isHidden():
                self.show()
            self.stapel.setCurrentIndex(i)
            self.bereich_geaendert.emit(i)

        def zurueck() -> None:
            self.stapel.setCurrentIndex(vorher[0])
            self.stapel.removeWidget(seite); seite.deleteLater()
            self._zusatz = None
            if vorher[1]:
                self.hide()
            self.bereich_geaendert.emit(vorher[0])
        return ausfuehren_in(seite, d, zeigen, zurueck)

    def zeige_bereich(self, i: int) -> None:
        """0 = Schreibhilfe, 1 = KI-Chat."""
        self.stapel.setCurrentIndex(i)
        self.bereich_geaendert.emit(i)

    def setze_bereiche(self, band=None, ki_gruppen=None) -> None:
        """Den KI-Bereich bauen: nur der Chat (Verlauf, Eingabe) — alles andere steht im Reiter Schreibhilfe und im Fenster „KI-Einstellungen“."""
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        from lunivo_writer.ui.sidebar.panels.ai_panel import ChatPanel
        self.chat = ChatPanel(self.ki, self.fenster)
        self.chat.zurueck.connect(lambda: self.zeige_bereich(0))
        lay.addWidget(self.chat, 1)
        self._seite_ki.setWidget(host)

    def zeige(self, funde: list) -> None:
        while self.liste.count() > 1:
            it = self.liste.takeAt(0)
            w_ = it.widget()                                  # einmal holen: nach setParent(None) kennt der Eintrag sein Widget nicht mehr
            if w_ is not None:
                w_.hide()
                w_.setParent(None)
                w_.deleteLater()
        if not funde:
            self.meldung = QLabel(LEER if self.a._geprueft_rev >= 0 else "Noch nicht geprüft.")
            self.meldung.setWordWrap(True)
            self.meldung.setStyleSheet("color: palette(mid); padding: 8px;")
            self.liste.insertWidget(0, self.meldung)
        for i, f in enumerate(funde):
            self.liste.insertWidget(i, FundKarte(f, self.a, dienst=getattr(self, "ki", None)))
        self.alle.setVisible(any(f["art"] == "fehler" and f["neu"] for f in funde))
        for w in self._einfuehrung:                                 # mit Funden steht die Liste ganz oben, wie in der ersten Fassung
            w.setVisible(not funde)

    def _alle(self):
        n = self.a.alle_aendern()
        self.a.status.emit(f"{n} Korrektur(en) übernommen.")

    def welche_hilfe(self):
        from lunivo_writer.ui.dialogs.welche_hilfe import HilfeWannDialog
        HilfeWannDialog(self.fenster).exec()
