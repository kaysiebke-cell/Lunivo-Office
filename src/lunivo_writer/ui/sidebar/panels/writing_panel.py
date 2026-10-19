"""Bereich „Schreibhilfe“ der Seitenleiste: die Karten für Funde, Vorschläge und Hinweise."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

FARBE = {"fehler": "#e8590c", "tipp": "#1c7ed6", "hinweis": "#868e96"}


class FundKarte(QFrame):
    def __init__(self, fund: dict, assistent, parent=None):
        super().__init__(parent)
        self.fund, self.a = fund, assistent
        self.setFrameShape(QFrame.StyledPanel)
        farbe = FARBE.get(fund["art"], "#868e96")
        self.setStyleSheet(f"FundKarte {{ border-left: 4px solid {farbe}; }}")
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 6, 8, 6)
        v.setSpacing(3)
        g = QLabel(fund["grund"])
        g.setWordWrap(True)
        g.setStyleSheet("color: palette(mid); font-size: 9pt;")
        v.addWidget(g)
        if fund["art"] != "hinweis" and fund["neu"] != "":
            t = QLabel(f"<s>{_esc(fund['zeigeAlt'])}</s> → <b>{_esc(fund['zeigeNeu'])}</b>")
        else:
            t = QLabel(f"„{_esc(fund['zeigeAlt'])[:80]}“" if fund["alt"] else "")
        t.setTextFormat(Qt.RichText)
        t.setWordWrap(True)
        v.addWidget(t)
        z = QHBoxLayout()
        z.addStretch(1)
        if fund["art"] != "hinweis" and fund["neu"] != "":
            b = QPushButton("Ändern")
            b.clicked.connect(lambda: self.a.aendern(self.fund))
            z.addWidget(b)
        b2 = QPushButton("Lassen")
        b2.clicked.connect(lambda: self.a.lassen(self.fund))
        z.addWidget(b2)
        v.addLayout(z)

    def mousePressEvent(self, e):
        ed = self.a.editor
        if ed is not None:
            ed.select_range(self.fund["von"], self.fund["bis"])
        super().mousePressEvent(e)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class VorschlagKarte(QFrame):
    def __init__(self, v: dict, dienst, panel):
        super().__init__()
        self.v, self.d, self.p = v, dienst, panel
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("VorschlagKarte { border-left: 4px solid #2f9e75; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 8, 6)
        sicher = f" · Sicherheit {round(v['konfidenz'] * 100)} %" if "konfidenz" in v else ""
        g = QLabel(v.get("grund", "") + sicher)
        g.setStyleSheet("color: palette(mid); font-size: 9pt;")
        g.setWordWrap(True)
        t = QLabel(f"<s>{_esc(v['alt'])}</s><br><b>{_esc(v['neu'])}</b>")
        t.setTextFormat(Qt.RichText); t.setWordWrap(True)
        lay.addWidget(g); lay.addWidget(t)
        z = QHBoxLayout(); z.addStretch(1)
        b1 = QPushButton("Einsetzen"); b1.clicked.connect(self._einsetzen)
        b2 = QPushButton("Lassen"); b2.clicked.connect(self._lassen)
        z.addWidget(b1); z.addWidget(b2); lay.addLayout(z)

    def _lassen(self):
        self.d.assistant.gelernt.ki_vermerken(self.v, False)
        self._weg()

    def _einsetzen(self):
        if self.d.vorschlag_einsetzen(self.v):
            self.d.assistant.gelernt.ki_vermerken(self.v, True)
            self._weg()

    def _weg(self, abgelehnt: bool = False):
        self.hide(); self.setParent(None); self.deleteLater()


class HinweisKarte(QFrame):
    """Antworten, die den Text nicht ersetzen sollen (Zusammenfassung, Analyse)."""
    def __init__(self, titel, text, cent, fenster, panel):
        super().__init__()
        self.text, self.w = text, fenster
        self.setFrameShape(QFrame.StyledPanel)
        lay = QVBoxLayout(self)
        t = QLabel(f"<b>{_esc(titel)}</b>")
        t.setTextFormat(Qt.RichText)
        body = QLabel(_esc(text).replace("\n", "<br>"))
        body.setTextFormat(Qt.RichText); body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(t); lay.addWidget(body)
        z = QHBoxLayout()
        for name, fn in (("Kopieren", self._kopieren), ("Am Ende einfügen", self._ende), ("Schließen", self._weg)):
            b = QPushButton(name); b.clicked.connect(fn); z.addWidget(b)
        lay.addLayout(z)

    def _kopieren(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.text)

    def _ende(self):
        e = self.w.current_editor()
        if e is not None:
            c = e.textCursor(); c.movePosition(c.MoveOperation.End); c.insertBlock(); c.insertText(self.text)

    def _weg(self):
        self.hide(); self.setParent(None); self.deleteLater()
