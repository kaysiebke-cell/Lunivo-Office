"""KI-Chat in der Seitenleiste (Bereich „KI“): mehrere Runden, der Dokumenttext geht als Auskunft mit."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from lunivo_writer.ai import ki as K
from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label




class ChatPanel(QWidget):
    def __init__(self, dienst, fenster):
        super().__init__()
        self.d, self.w = dienst, fenster
        self.verlauf: list[dict] = []
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(text_label("KI-Chat", fett=True))
        self.blasen = QVBoxLayout()
        self.blasen.setAlignment(Qt.AlignTop)
        host = QWidget(); host.setLayout(self.blasen)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(host); sc.setMinimumHeight(180)
        self.scroll = sc
        v.addWidget(sc, 1)
        z = QHBoxLayout()
        self.eingabe = QLineEdit(); self.eingabe.setPlaceholderText("Frage an die KI … (z. B. „Was fehlt in diesem Brief noch?“)")
        self.eingabe.returnPressed.connect(self.senden)
        b = QPushButton("Senden"); b.clicked.connect(self.senden)
        bild = QPushButton("Bild"); bild.setToolTip("Aus dem Text im Feld (oder der Markierung) ein Bild erzeugen und einfügen")
        bild.clicked.connect(self._bild)
        neu = QPushButton("Neu"); neu.setToolTip("Gespräch leeren"); neu.clicked.connect(self.leeren)
        z.addWidget(self.eingabe, 1); z.addWidget(b); z.addWidget(bild); z.addWidget(neu)
        v.addLayout(z)
        dienst.chatAntwort.connect(self._antwort)

    def _blase(self, text: str, ki: bool, cent=None) -> None:
        f = QFrame(); f.setFrameShape(QFrame.StyledPanel)
        f.setStyleSheet("QFrame { border-left: 4px solid %s; }" % ("#2f6fb5" if ki else "#868e96"))
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

    def _antwort(self, text: str, cent) -> None:
        if not text.startswith("⚠"):
            self.verlauf.append({"rolle": "ki", "text": text})
        self._blase(text, True, cent)

    def leeren(self):
        self.verlauf.clear()
        while self.blasen.count():
            it = self.blasen.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
