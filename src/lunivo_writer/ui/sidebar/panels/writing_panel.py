"""Bereich „Schreibhilfe“ der Seitenleiste: die Karten für Funde, Vorschläge und Hinweise."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.ui.widgets import icons

FARBE = {"fehler": "#e8590c", "tipp": "#1c7ed6", "hinweis": "#868e96"}


# Marke oben auf der Karte: Schrift, Hintergrund (nach der Vorlage der ersten Fassung)
MARKE = {"fehler": ("SICHER FALSCH", "#d9a03a", "#1d1a12"), "tipp": ("KOMMT DRAUF AN", "#2f6fb5", "#ffffff"),
         "hinweis": ("NUR ZUM NACHDENKEN", "#6b7280", "#ffffff")}
KARTE = "{name} {{ border: 1px solid palette(midlight); border-radius: 10px; background: rgba(128, 128, 128, 0.07); }}"


def marke(art: str) -> QLabel:
    text, grund, schrift = MARKE.get(art, MARKE["hinweis"])
    m = QLabel(text)
    m.setStyleSheet(f"background: {grund}; color: {schrift}; border: none; border-radius: 3px; padding: 2px 8px; "
                    "font-size: 8pt; font-weight: 700; letter-spacing: 0.5px;")
    return m


class FundKarte(QFrame):
    def __init__(self, fund: dict, assistent, parent=None):
        super().__init__(parent)
        self.fund, self.a = fund, assistent
        self.setObjectName("FundKarte")
        self.setStyleSheet(KARTE.format(name="QFrame#FundKarte"))
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 12, 12)
        v.setSpacing(6)
        kopf = QHBoxLayout(); kopf.setContentsMargins(0, 0, 0, 0)
        kopf.addWidget(marke(fund["art"])); kopf.addStretch(1)
        v.addLayout(kopf)
        if fund["art"] != "hinweis" and fund["neu"] != "":
            t = md_label(f"~~{md_escape(fund['zeigeAlt'])}~~  →  **{md_escape(fund['zeigeNeu'])}**")
        else:
            t = text_label(f"„{fund['zeigeAlt'][:80]}“" if fund["alt"] else "")
        t.setStyleSheet("border: none; background: transparent; font-size: 11pt;")
        v.addWidget(t)
        g = QLabel(fund["grund"])
        g.setWordWrap(True)
        g.setStyleSheet("color: palette(mid); font-size: 9pt; border: none; background: transparent;")
        v.addWidget(g)
        z = QHBoxLayout()
        z.setSpacing(8)
        zeigen = QPushButton("Zeigen")
        zeigen.clicked.connect(self._zeigen)
        z.addWidget(zeigen)
        if fund["art"] != "hinweis" and fund["neu"] != "":
            b = QPushButton("Ändern")
            b.clicked.connect(lambda: self.a.aendern(self.fund))
            z.addWidget(b)
        z.addStretch(1)
        from lunivo_writer.services import vorlesen
        if vorlesen.verfuegbar():
            ohr = QPushButton()
            ohr.setIcon(icons.icon("vorlesen", 16)); ohr.setFlat(True); ohr.setCursor(Qt.PointingHandCursor)
            ohr.setToolTip("Das Wort anhören")
            ohr.clicked.connect(self._hoeren)
            z.addWidget(ohr)
        v.addLayout(z)

    def _zeigen(self):
        ed = self.a.editor
        if ed is not None:
            ed.select_range(self.fund["von"], self.fund["bis"])
            ed.setFocus()

    def _hoeren(self):
        from lunivo_writer.services import vorlesen
        f = self.fund
        vorlesen.lies_vor(f["zeigeNeu"] if f["art"] != "hinweis" and f["neu"] else f["zeigeAlt"])

    def mousePressEvent(self, e):
        self._zeigen()
        super().mousePressEvent(e)


class VorschlagKarte(QFrame):
    def __init__(self, v: dict, dienst, panel):
        super().__init__()
        self.v, self.d, self.p = v, dienst, panel
        self.setObjectName("VorschlagKarte")
        self.setStyleSheet(KARTE.format(name="QFrame#VorschlagKarte"))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 8, 6)
        sicher = f" · Sicherheit {round(v['konfidenz'] * 100)} %" if "konfidenz" in v else ""
        g = QLabel(v.get("grund", "") + sicher)
        g.setStyleSheet("color: palette(mid); font-size: 9pt;")
        g.setWordWrap(True)
        t = md_label(f"~~{md_escape(v['alt'])}~~\n\n**{md_escape(v['neu'])}**")
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
        self.setObjectName("HinweisKarte")
        self.setStyleSheet(KARTE.format(name="QFrame#HinweisKarte"))
        lay = QVBoxLayout(self)
        t = text_label(titel, fett=True, umbruch=False)
        body = text_label(text, auswaehlbar=True)
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
