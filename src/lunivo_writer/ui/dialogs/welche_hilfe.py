"""„Welche Hilfe wann“: die Stufen der Schreibhilfe von der Wellenlinie bis zur KI, die Etiketten der Funde und ein Weg durch einen Brief.

Die Schalter der ersten Stufe sind dieselben wie in der Seitenleiste und in den Optionen (``assistant.setze``); „jetzt“ ruft den Befehl, den auch das Band und die
Tastenkürzel rufen."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from lunivo_writer.core.farben import Farbe
STUFEN = [
    # (Stufe, Titel, Kürzel, Frage, Hinweis rechts, Schalter | Befehl)
    (1, "Rote Wellenlinien", "", "Gibt es das Wort überhaupt?", "sofort beim Tippen", ("schalter", "wellen")),
    (1, "Wortvorhersage", "", "Wie ging das Wort weiter?", "ab drei Buchstaben", ("schalter", "vorhersage")),
    (1, "AutoKorrektur", "", "Bessert das Offensichtliche beim Tippen", "zum Beispiel „dass“ nach Komma", ("schalter", "autokorr")),
    (2, "Rechtsklick auf ein Wort", "", "Welches Wort war gemeint?", "sucht auch nach dem Klang", None),
    (3, "Prüfen", "F7", "Ist es das richtige Wort? das/dass, wider/wieder", "die Schreibhilfe rechts", ("tun", "w.pruefen")),
    (4, "Vorlesen", "F4", "Klingt der Satz rund?", "Stimmen aus dem System", ("tun", "vorlesen")),
    (5, "Gründlich prüfen", "", "Stimmt die Grammatik?", "LanguageTool, einmal 400 MB", ("tun", "gruendlichPruefen")),
    (6, "KI-Korrektur", "F8", "Versteht das jemand? Passt der Ton?", "Internet und Guthaben", ("tun", "kiKorrektur")),
]
ETIKETTEN = [("SICHER FALSCH", "#c77d2e", "white", "Da ist kein Zweifel.", "blind übernehmen"),
             ("KOMMT DRAUF AN", Farbe.AKZENT, "white", "Hängt vom Satz ab.", "kurz hinschauen"),
             ("ZUM NACHDENKEN", Farbe.GRAU, "white", "Nur ein Anstoß, keine Regel.", "oft übergehen")]
WEG = ["Schreiben, ohne auf die Wellenlinien zu achten.", "F7 drücken und „Alles Eindeutige übernehmen“ wählen.", "Die übrigen Karten einzeln durchgehen.",
       "F4 — einmal vorlesen lassen. Da fällt auf, was keine Regel findet.", "Nur wenn der Text sitzen muss: F8."]


def _kopf(text: str) -> QLabel:
    t = QLabel(text.upper()); t.setStyleSheet("color: palette(mid); letter-spacing: 1px; font-size: 9pt; padding-top: 6px;")
    return t


def _text(text: str) -> QLabel:
    t = QLabel(text); t.setWordWrap(True)
    return t


class HilfeWannDialog(QDialog):
    def __init__(self, fenster):
        super().__init__(fenster)
        self.fenster = fenster
        self.schalter: dict[str, QPushButton] = {}
        self.setWindowTitle("Welche Hilfe wann")
        self.resize(840, 720)
        v = QVBoxLayout(self)
        titel = QLabel("Welche Hilfe wann"); f = titel.font(); f.setBold(True); f.setPointSizeF(f.pointSizeF() + 3); titel.setFont(f)
        v.addWidget(titel)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        host = QWidget(); h = QVBoxLayout(host); h.setContentsMargins(0, 0, 8, 0); h.setSpacing(6)
        h.addWidget(_text("Jede Stufe ist langsamer als die darüber und klüger als sie. Fang oben an und geh nur so weit hinunter, wie du musst. "
                          "Die Stufen 1 bis 5 brauchen kein Internet und kein Konto."))
        h.addWidget(_kopf("Welche Hilfe wann"))
        karte = QFrame(); karte.setFrameShape(QFrame.StyledPanel); kv = QVBoxLayout(karte); kv.setContentsMargins(0, 0, 0, 0); kv.setSpacing(0)
        for i, zeile in enumerate(STUFEN):
            kv.addWidget(self._zeile(*zeile, trenner=i > 0))
        h.addWidget(karte)
        h.addWidget(_kopf("Wie sicher ein Fund ist"))
        h.addWidget(_text("Auch innerhalb von F7 gibt es Stufen. Jede Karte in der Seitenleiste trägt eins von drei Etiketten."))
        karte2 = QFrame(); karte2.setFrameShape(QFrame.StyledPanel); k2 = QVBoxLayout(karte2); k2.setContentsMargins(0, 0, 0, 0); k2.setSpacing(0)
        for i, (name, farbe, schrift, satz, rechts) in enumerate(ETIKETTEN):
            z = QWidget(); zh = QHBoxLayout(z); zh.setContentsMargins(12, 8, 12, 8)
            chip = QLabel(name); chip.setStyleSheet(f"background: {farbe}; color: {schrift}; font-weight: bold; font-size: 8pt; padding: 3px 10px; border-radius: 3px;")
            zh.addWidget(chip); zh.addWidget(QLabel(satz), 1)
            r = QLabel(rechts); r.setStyleSheet("color: palette(mid);"); zh.addWidget(r)
            k2.addWidget(z)
        h.addWidget(karte2)
        h.addWidget(_text("„Alles Eindeutige übernehmen“ fasst nur die erste Sorte an und lässt die anderen beiden in Ruhe. Wenn es eilt, ist das der eine Klick, den du brauchst."))
        h.addWidget(_kopf("Ein Weg durch einen Brief"))
        for n, s in enumerate(WEG, 1):
            h.addWidget(_text(f"{n}.  {s}"))
        h.addWidget(_text("Für einen Zettel an die Tür reicht Stufe 1. Für den Widerspruch ans Amt geht man bis 6."))
        h.addStretch(1)
        sc.setWidget(host)
        v.addWidget(sc, 1)
        u = QHBoxLayout(); u.addStretch(1)                                      # wie in der Vorlage: „Abbrechen“, dann „Schließen“ (die Hauptschaltfläche)
        ab = QPushButton("Abbrechen"); ab.clicked.connect(self.reject)
        zu = QPushButton("Schließen"); zu.setDefault(True); zu.clicked.connect(self.accept)
        u.addWidget(ab); u.addWidget(zu)
        v.addLayout(u)
        fenster.assistant.schalterGeaendert.connect(self._nachziehen)

    def _zeile(self, stufe, titel, kuerzel, frage, rechts, aktion, trenner: bool) -> QWidget:
        z = QWidget(); zh = QHBoxLayout(z); zh.setContentsMargins(12, 8, 12, 8); zh.setSpacing(12)
        n = QLabel(str(stufe)); n.setAlignment(Qt.AlignCenter); n.setFixedSize(26, 26)
        n.setStyleSheet(('background: ' + Farbe.AKZENT + '; color: white; font-weight: bold; border-radius: 13px;'))
        zh.addWidget(n)
        mitte = QVBoxLayout(); mitte.setSpacing(0)
        kopf = QHBoxLayout(); kopf.setSpacing(8)
        t = QLabel(titel); f = t.font(); f.setBold(True); t.setFont(f); kopf.addWidget(t)
        if kuerzel:
            k = QLabel(kuerzel); k.setStyleSheet("border: 1px solid palette(mid); border-radius: 3px; padding: 0 5px; font-size: 8pt;"); kopf.addWidget(k)
        kopf.addStretch(1)
        mitte.addLayout(kopf); mitte.addWidget(QLabel(frage))
        zh.addLayout(mitte, 1)
        r = QLabel(rechts); r.setStyleSheet("color: palette(mid);"); zh.addWidget(r)
        if aktion and aktion[0] == "schalter":
            b = QPushButton(); b.setCheckable(True); b.setFixedWidth(52)
            b.setChecked(self.fenster.assistant.an(aktion[1]))
            b.setStyleSheet("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 2px 8px; }"
                            "QPushButton:checked { background: #2f9e75; color: white; border-color: #2f9e75; }")
            b.setText("an" if b.isChecked() else "aus")
            b.toggled.connect(lambda an, name=aktion[1], b=b: (b.setText("an" if an else "aus"), self.fenster.assistant.setze(name, an)))
            self.schalter[aktion[1]] = b
            zh.addWidget(b)
        elif aktion:
            b = QPushButton("jetzt"); b.setStyleSheet(('QPushButton { border: 1px solid ' + Farbe.AKZENT + '; color: ' + Farbe.AKZENT + '; border-radius: 11px; padding: 2px 12px; }'))
            b.clicked.connect(lambda _=False, a=aktion[1]: (self.accept(), self.fenster.befehle.tun(a)))
            zh.addWidget(b)
        else:
            zh.addSpacing(52)
        if trenner:
            z.setStyleSheet("")
            w = QWidget(); wv = QVBoxLayout(w); wv.setContentsMargins(0, 0, 0, 0); wv.setSpacing(0)
            linie = QFrame(); linie.setFrameShape(QFrame.HLine); linie.setFrameShadow(QFrame.Sunken); linie.setStyleSheet("color: palette(mid);")
            wv.addWidget(linie); wv.addWidget(z)
            return w
        return z

    def _nachziehen(self, name: str, an: bool) -> None:
        b = self.schalter.get(name)
        if b is not None and b.isChecked() != an:
            b.blockSignals(True); b.setChecked(an); b.setText("an" if an else "aus"); b.blockSignals(False)
