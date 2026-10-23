"""Bereich „Schreibhilfe“ der Seitenleiste: die Karten für Funde, Vorschläge und Hinweise."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.ui.widgets import icons

import re

from lunivo_writer.core.farben import Farbe
_LAUF = re.compile(r"(.)\1{5,}")


def kurz(text: str) -> str:
    """Lange gleiche Zeichenfolgen (viele Leerzeichen hintereinander) kurz zeigen: „␣×34“ — sonst wird die Karte breiter als die Seitenleiste."""
    return _LAUF.sub(lambda m: f"{m.group(1)}×{len(m.group(0))}", text)


FARBE = {"fehler": Farbe.ORANGE, "tipp": "#1c7ed6", "hinweis": Farbe.GRAU}


# Marke oben auf der Karte: Schrift, Hintergrund (nach der Vorlage der ersten Fassung)
MARKE = {"fehler": ("SICHER FALSCH", "#d9a03a", "#1d1a12"), "tipp": ("KOMMT DRAUF AN", Farbe.AKZENT, Farbe.WEISS),
         "hinweis": ("NUR ZUM NACHDENKEN", "#6b7280", Farbe.WEISS)}
KARTE = "{name} {{ border: 1px solid palette(midlight); border-radius: 10px; background: rgba(128, 128, 128, 0.07); }}"


def marke(art: str) -> QLabel:
    text, grund, schrift = MARKE.get(art, MARKE["hinweis"])
    m = QLabel(text)
    m.setStyleSheet(f"background: {grund}; color: {schrift}; border: none; border-radius: 3px; padding: 2px 8px; "
                    "font-size: 8pt; font-weight: 700; letter-spacing: 0.5px;")
    return m


class FundKarte(QFrame):
    def __init__(self, fund: dict, assistent, parent=None, dienst=None):
        super().__init__(parent)
        self.fund, self.a, self.d = fund, assistent, dienst
        self.setObjectName("FundKarte")
        self.setStyleSheet(KARTE.format(name="QFrame#FundKarte"))
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 12, 12)
        v.setSpacing(6)
        kopf = QHBoxLayout(); kopf.setContentsMargins(0, 0, 0, 0)
        kopf.addWidget(marke(fund["art"])); kopf.addStretch(1)
        v.addLayout(kopf)
        if fund["art"] != "hinweis" and fund["neu"] != "":
            t = md_label(f"~~{md_escape(kurz(fund['zeigeAlt']))}~~  →  **{md_escape(kurz(fund['zeigeNeu']))}**")
        else:
            t = text_label(f"„{kurz(fund['zeigeAlt'])[:80]}“" if fund["alt"] else "")
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
        from lunivo_writer.services import vorlesen
        if vorlesen.verfuegbar():                                        # gleich neben den anderen Knöpfen: immer sichtbar
            ohr = QPushButton()
            ohr.setIcon(icons.icon("vorlesen", 18)); ohr.setCursor(Qt.PointingHandCursor)
            ohr.setToolTip("Das Wort anhören"); ohr.setAccessibleName("Das Wort anhören")
            ohr.clicked.connect(self._hoeren)
            z.addWidget(ohr)
        if fund["art"] == "hinweis" and fund.get("stelle") and dienst is not None:           # ein Hinweis auf einen Satz: die KI macht einen Vorschlag
            self.vorschlag_knopf = QPushButton("Vorschlag")
            self.vorschlag_knopf.setToolTip("Die KI schreibt den Satz kürzer — Sie nehmen es an oder verwerfen es")
            self.vorschlag_knopf.clicked.connect(self._vorschlag_holen)
            z.addWidget(self.vorschlag_knopf)
        z.addStretch(1)
        self._aktionen = z
        v.addLayout(z)
        # Der Vorschlag der KI, erst sichtbar, wenn er da ist
        self.vorschlag_feld = QFrame(); self.vorschlag_feld.setStyleSheet("QFrame { border: none; background: transparent; }")
        vv = QVBoxLayout(self.vorschlag_feld); vv.setContentsMargins(0, 0, 0, 0); vv.setSpacing(6)
        self.vorschlag_text = QLabel(); self.vorschlag_text.setWordWrap(True); self.vorschlag_text.setStyleSheet("font-size: 11pt; font-weight: 600;")
        vv.addWidget(self.vorschlag_text)
        vz = QHBoxLayout(); vz.setSpacing(8)
        self.annehmen = QPushButton("Annehmen"); self.annehmen.clicked.connect(self._annehmen)
        self.verwerfen = QPushButton("Verwerfen"); self.verwerfen.clicked.connect(self._verwerfen)
        vz.addWidget(self.annehmen); vz.addWidget(self.verwerfen); vz.addStretch(1)
        vv.addLayout(vz)
        self.vorschlag_feld.hide()
        v.addWidget(self.vorschlag_feld)

    def _vorschlag_holen(self):
        self.vorschlag_knopf.setEnabled(False); self.vorschlag_knopf.setText("Die KI schreibt …")
        self.d.satz_vorschlag(self.fund, self._vorschlag_da)
        if not self.d._beschaeftigt:                       # es kam nicht zum Lauf (kein Modell, kein Text): der Knopf bleibt bedienbar
            self.vorschlag_knopf.setEnabled(True); self.vorschlag_knopf.setText("Vorschlag")

    def _vorschlag_da(self, v: dict):
        try:
            self._v = v
            self.vorschlag_text.setText(v["neu"])
            self.vorschlag_feld.show()
            self.vorschlag_knopf.hide()
        except RuntimeError:                                 # die Karte gibt es nicht mehr (die Funde wurden inzwischen neu geholt)
            pass

    def _annehmen(self):
        if self.d.vorschlag_einsetzen(self._v):
            self.d.assistant.gelernt.ki_vermerken(self._v, True)
            self.a.pruefen(voll=True)                        # der Hinweis verschwindet, wenn der Satz kürzer ist

    def _verwerfen(self):
        self.d.assistant.gelernt.ki_vermerken(self._v, False)
        self.vorschlag_feld.hide()
        self.vorschlag_knopf.setEnabled(True); self.vorschlag_knopf.setText("Vorschlag"); self.vorschlag_knopf.show()

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
        b1 = QPushButton("Annehmen"); b1.clicked.connect(self._einsetzen)
        b2 = QPushButton("Verwerfen"); b2.clicked.connect(self._lassen)
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
