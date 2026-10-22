"""„Meine Aktionen“: die Schnellen KI-Aktionen (Eigene Assistenten) als Knöpfe — in der Seitenleiste der Schreibhilfe und im KI-Chat dieselbe Leiste.

Die Liste kommt aus der einen KI-Konfiguration (``KIKonfig.assistenten``), dieselbe wie im Band, im Rechtsklick-Menü und in den Optionen. Wer dort eine Aktion
anlegt oder entfernt, sieht sie hier sofort."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from lunivo_writer.ui.widgets.flow_layout import FlowLayout


class AktionenLeiste(QWidget):
    def __init__(self):
        super().__init__()
        self.dienst = None
        self.fenster = None
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(4)
        self.titel = QLabel("Meine Aktionen"); self.titel.setStyleSheet("color: palette(mid); font-size: 9pt;")
        v.addWidget(self.titel)
        self.feld = QWidget()
        self.fluss = FlowLayout(self.feld)
        v.addWidget(self.feld)
        self.knoepfe: list[QPushButton] = []

    def verbinde(self, dienst, fenster) -> None:
        self.dienst, self.fenster = dienst, fenster
        dienst.geaendert.connect(self.fuellen)
        dienst.laeuft.connect(lambda _an: self.zustand())
        self.fuellen()

    def fuellen(self) -> None:
        """Die Knöpfe neu aufbauen: je Aktion einer, dazu „＋ Neue Aktion“."""
        for b in self.knoepfe:
            self.fluss.removeWidget(b); b.hide(); b.setParent(None); b.deleteLater()
        self.knoepfe = []
        for a in self.dienst.konfig["assistenten"]:
            b = QPushButton(a["name"]); b.setToolTip(a["prompt"][:200])
            b.clicked.connect(lambda _=False, a=a: self.dienst.assistent(a))
            self.fluss.addWidget(b); self.knoepfe.append(b)
        neu = QPushButton("＋ Neue Aktion"); neu.setFlat(True)
        neu.clicked.connect(lambda: self.fenster.befehle.tun("w.assistentErstellen"))
        self.fluss.addWidget(neu); self.knoepfe.append(neu)
        self.zustand()

    def zustand(self) -> None:
        """Die Aktionen laufen nur mit verbundenem Modell und nicht, solange die KI schon arbeitet; „Neue Aktion“ geht immer."""
        frei = self.dienst.verfuegbar() and not self.dienst._beschaeftigt
        for b in self.knoepfe[:-1]:
            b.setEnabled(frei)
