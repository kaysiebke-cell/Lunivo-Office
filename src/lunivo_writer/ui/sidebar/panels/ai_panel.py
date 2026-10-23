"""KI-Chat in der Seitenleiste (Bereich „KI“): mehrere Runden, der Dokumenttext geht als Auskunft mit."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QPlainTextEdit, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSlider, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ai import ki as K
from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label




from lunivo_writer.core.farben import Farbe
class ChatEingabe(QPlainTextEdit):
    """Mehrzeiliges Eingabefeld für den Chat: Enter schickt ab, Umschalt+Enter macht eine neue Zeile. ``text()``/``setText()`` wie beim Einzeiler."""
    abgeschickt = Signal()

    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Frage an die KI …")
        self.setMinimumHeight(110)
        self.setTabChangesFocus(True)

    def keyPressEvent(self, e) -> None:
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (e.modifiers() & Qt.ShiftModifier):
            self.abgeschickt.emit()
            return
        super().keyPressEvent(e)

    def text(self) -> str:
        return self.toPlainText()

    def setText(self, t: str) -> None:
        self.setPlainText(t)
        self.moveCursor(QTextCursor.End)


class ChatPanel(QWidget):
    """KI-Chat: Kopf („KI-Chat“, Einstellungen, Schließen), Verlauf, darunter Eingabe mit Senden; Bild und Neu als kleine Knöpfe.
    Ohne verbundenes Modell steht statt des Verlaufs der Hinweis „KI-Modell verbinden“ mit dem Weg zu den KI-Einstellungen."""
    zurueck = Signal()

    def __init__(self, dienst, fenster):
        super().__init__()
        self.d, self.w = dienst, fenster
        self.verlauf: list[dict] = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        kopf = QHBoxLayout()
        kopf.addWidget(text_label("KI-Chat", fett=True, pt=12, umbruch=False))
        kopf.addStretch(1)
        for zeichen, tipp, fn in (("⚙", "KI-Einstellungen", self._einstellungen), ("✕", "Zur Schreibhilfe", self.zurueck.emit)):
            b = QToolButton(); b.setText(zeichen); b.setAutoRaise(True); b.setToolTip(tipp)
            b.clicked.connect(lambda _=False, f=fn: f())
            kopf.addWidget(b)
        v.addLayout(kopf)
        # Hinweis, solange kein Modell verbunden ist
        self.hinweis = QWidget()
        hv = QVBoxLayout(self.hinweis); hv.setContentsMargins(0, 0, 0, 0)
        hv.addWidget(text_label("KI-Modell verbinden, um den KI-Chat zu aktivieren", fett=True))
        hb = QPushButton("KI-Einstellungen …"); hb.clicked.connect(self._einstellungen)
        hv.addWidget(hb, 0, Qt.AlignLeft)
        v.addWidget(self.hinweis)
        self.leer = QWidget()                                  # nimmt den Platz ein, solange nur der Hinweis dasteht
        v.addWidget(self.leer, 1)
        # Verlauf
        self.blasen = QVBoxLayout()
        self.blasen.setAlignment(Qt.AlignTop)
        host = QWidget(); host.setLayout(self.blasen)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(host); sc.setMinimumHeight(180); sc.setFrameShape(QFrame.NoFrame)
        self.scroll = sc
        v.addWidget(sc, 1)
        # Meine Aktionen: dieselbe Leiste wie in der Schreibhilfe
        from lunivo_writer.ui.baukasten.aktionen_leiste import AktionenLeiste
        self.aktionen = AktionenLeiste()
        self.aktionen.verbinde(dienst, fenster)
        v.addWidget(self.aktionen)
        dienst.aktionErgebnis.connect(self._aktion_ergebnis)
        # Eingabe
        self.eingabezeile = QWidget()
        ev = QVBoxLayout(self.eingabezeile); ev.setContentsMargins(0, 0, 0, 0); ev.setSpacing(4)
        self.eingabe = ChatEingabe()
        self.eingabe.abgeschickt.connect(self.senden)
        ev.addWidget(self.eingabe)
        self.tokens = QLabel("Tokens: 0"); self.tokens.setStyleSheet("color: palette(mid);"); self.tokens.setAlignment(Qt.AlignRight)
        self.tokens.setToolTip("Grobe Schätzung: etwa vier Zeichen je Token")
        self.eingabe.textChanged.connect(lambda: self.tokens.setText(f"Tokens: {(len(self.eingabe.text()) + 3) // 4}"))
        ev.addWidget(self.tokens)
        self._erweitert(ev)
        z2 = QHBoxLayout()
        senden = QPushButton("Senden"); senden.clicked.connect(self.senden)
        z2.addWidget(senden)
        bild = QPushButton("Bild"); bild.setFlat(True); bild.setToolTip("Aus dem Text im Feld (oder der Markierung) ein Bild erzeugen und einfügen")
        bild.clicked.connect(self._bild)
        neu = QPushButton("Leeren"); neu.setFlat(True); neu.setToolTip("Gespräch leeren"); neu.clicked.connect(self.leeren)
        z2.addWidget(bild); z2.addWidget(neu); z2.addStretch(1)
        ev.addLayout(z2)
        v.addWidget(self.eingabezeile)
        dienst.chatAntwort.connect(self._antwort)
        dienst.geaendert.connect(self.zustand)
        self.zustand()

    def _erweitert(self, ev: QVBoxLayout) -> None:
        """„Erweiterte Einstellungen anzeigen“: Modell (dieselbe Wahl wie in der Modellzuweisung), Länge, Temperatur, Top P, Stoppfolgen — in der KI-Konfiguration gespeichert."""
        from lunivo_writer.ui.dialogs.ki_dialoge import modell_combo
        k = self.d.konfig
        o = k.chat_optionen()
        self.mehr = QPushButton(); self.mehr.setFlat(True); self.mehr.setCursor(Qt.PointingHandCursor)
        ev.addWidget(self.mehr, 0, Qt.AlignLeft)
        self.erweitert = QWidget()
        ew = QVBoxLayout(self.erweitert); ew.setContentsMargins(0, 0, 0, 0); ew.setSpacing(4)
        ew.addWidget(text_label("Modell", fett=True))
        self.modell = modell_combo(k, "chatbot")
        self.modell.currentIndexChanged.connect(lambda: (k.aufgabe_setzen("chatbot", self.modell.currentData() or ""), self.d.geaendert.emit()))
        ew.addWidget(self.modell)

        def regler(titel: str, tipp: str, maximum: int, wert: int, anzeige, speichern):
            kopf = QHBoxLayout(); kopf.addWidget(text_label(titel, fett=True)); kopf.addStretch(1)
            zahl = QLabel(anzeige(wert)); kopf.addWidget(zahl)
            ew.addLayout(kopf)
            sl = QSlider(Qt.Horizontal); sl.setRange(0, maximum); sl.setValue(wert); sl.setToolTip(tipp)
            sl.valueChanged.connect(lambda v: (zahl.setText(anzeige(v)), speichern(v)))
            ew.addWidget(sl)
            return sl
        self.s_laenge = regler("Maximale Länge", "0 = Vorgabe des Anbieters", 4096, int(o["maxLaenge"]),
                               lambda v: str(v) if v else "Standard", lambda v: k.chat_setzen(maxLaenge=v))
        self.s_temp = regler("Temperatur", "Niedrig = sachlich und gleichbleibend, hoch = freier. Gilt für Ollama und eigene Anbieter.", 20,
                             int(round(float(o["temperatur"]) * 10)), lambda v: f"{v / 10:g}", lambda v: k.chat_setzen(temperatur=v / 10))
        self.s_top = regler("Top P", "Wie viele der wahrscheinlichsten Wörter zur Wahl stehen. Gilt für Ollama und eigene Anbieter.", 10,
                            int(round(float(o["topP"]) * 10)), lambda v: f"{v / 10:g}", lambda v: k.chat_setzen(topP=v / 10))
        ew.addWidget(text_label("Stoppfolgen", fett=True))
        self.stopp = QLineEdit(str(o["stopp"])); self.stopp.setPlaceholderText("durch Komma getrennt")
        self.stopp.textChanged.connect(lambda t: k.chat_setzen(stopp=t))
        ew.addWidget(self.stopp)
        self.direkt = QCheckBox("Antwort direkt ins Dokument einfügen"); self.direkt.setChecked(bool(o["direkt"]))
        self.direkt.toggled.connect(lambda an: k.chat_setzen(direkt=an))
        ew.addWidget(self.direkt)
        ev.addWidget(self.erweitert)

        def umschalten(an: bool) -> None:
            self.erweitert.setVisible(an)
            self.mehr.setText("Erweiterte Einstellungen ausblenden ▴" if an else "Erweiterte Einstellungen anzeigen ▾")
        self.mehr.clicked.connect(lambda: umschalten(not self.erweitert.isVisible()))
        umschalten(False)
        self.d.geaendert.connect(self._modelle_neu)

    def _modelle_neu(self) -> None:
        """Nach einer Änderung in den KI-Einstellungen die Modellliste dieser Auswahl neu füllen."""
        from lunivo_writer.ui.dialogs.ki_dialoge import modell_combo
        neu = modell_combo(self.d.konfig, "chatbot")
        self.modell.blockSignals(True)
        self.modell.clear()
        for i in range(neu.count()):
            self.modell.addItem(neu.itemText(i), neu.itemData(i))
        self.modell.setCurrentIndex(max(0, self.modell.findData(self.d.konfig["aufgaben"].get("chatbot", ""))))
        self.modell.blockSignals(False)

    def zustand(self) -> None:
        """Verlauf und Eingabe gibt es erst mit einem verbundenen Modell."""
        da = self.d.verfuegbar()
        self.hinweis.setVisible(not da)
        self.leer.setVisible(not da)
        self.scroll.setVisible(da)
        self.eingabezeile.setVisible(da)

    def _einstellungen(self) -> None:
        from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
        from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
        ausfuehren(KIEinstellungenDialog(self.w, 0))
        self.d.geaendert.emit()

    def _blase(self, text: str, ki: bool, cent=None) -> None:
        f = QFrame(); f.setFrameShape(QFrame.StyledPanel)
        f.setStyleSheet("QFrame { border-left: 4px solid %s; }" % (Farbe.AKZENT if ki else Farbe.GRAU))
        l = QVBoxLayout(f)
        t = text_label(text)
        t.setTextInteractionFlags(Qt.TextSelectableByMouse)
        l.addWidget(t)
        if ki and not text.startswith("⚠"):
            z = QHBoxLayout()
            for name, fn in (("Kopieren", lambda: QApplication.clipboard().setText(text)),
                             ("Einfügen", lambda: self._einfuegen(text)),
                             ("Ersetzen", lambda: self._ersetzen(text))):
                b = QPushButton(name); b.clicked.connect(fn); z.addWidget(b)
            if cent is not None:
                z.addWidget(QLabel(K.als_geld(cent)))
            l.addLayout(z)
        self.blasen.addWidget(f)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum() + 200)

    def _einfuegen(self, text):
        e = self.w.current_editor()
        if e is not None:
            e.textCursor().insertText(text)

    def _ersetzen(self, text):
        e = self.w.current_editor()
        if e is not None and e.textCursor().hasSelection():
            e.textCursor().insertText(text)
        else:
            self.w.lbl_msg.setText("Zum Ersetzen zuerst die Stelle im Text markieren.")

    def senden(self):
        t = self.eingabe.text().strip()
        if not t:
            return
        self.eingabe.clear()
        self.verlauf.append({"rolle": "mensch", "text": t})
        self._blase(t, False)
        self.d.chat(list(self.verlauf))

    def _bild(self):
        t = self.eingabe.text().strip()
        self.eingabe.clear()
        if t:
            self._blase("Bild: " + t, False)
        self.d.bild_aus_text(t or None)

    def _aktion_ergebnis(self, name: str, text: str, cent) -> None:
        """Das Ergebnis einer Schnellen KI-Aktion steht im Chat wie eine Antwort (und ist Teil des Gesprächs)."""
        self.verlauf.append({"rolle": "mensch", "text": f"Aktion „{name}“ auf den Text anwenden."})
        self.verlauf.append({"rolle": "ki", "text": text})
        self._blase(f"„{name}“: {text}", True, cent)

    def _antwort(self, text: str, cent) -> None:
        if not text.startswith("⚠"):
            self.verlauf.append({"rolle": "ki", "text": text})
        self._blase(text, True, cent)
        if self.direkt.isChecked() and not text.startswith("⚠"):
            self._einfuegen(text)

    def leeren(self):
        self.verlauf.clear()
        while self.blasen.count():
            it = self.blasen.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
