"""Dialoge zu Sendungen: Umschlag, Etiketten, Seriendruck, Regeln, Vorschau."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QVBoxLayout,
)

from lunivo_writer.editor import sendungen as S


def _ok(dlg, text_ok: str | None = None):
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    if text_ok:
        bb.button(QDialogButtonBox.Ok).setText(text_ok)
    bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
    return bb


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
class UmschlagDialog(PanelFaehig, QDialog):
    def __init__(self, parent, absender: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Umschlag")
        f = QFormLayout(self)
        f.addRow(QLabel("Das Blatt wird auf Umschlagformat gestellt und beides eingesetzt.\nDanach steht der Umschlag allein im Dokument."))
        self.format = QComboBox(); self.format.addItems(list(S.UMSCHLAEGE))
        self.absender = QPlainTextEdit(absender); self.absender.setFixedHeight(60)
        self.empfaenger = QPlainTextEdit("Vorname Nachname\nStraße 1\n12345 Ort"); self.empfaenger.setFixedHeight(80)
        f.addRow("Format", self.format); f.addRow("Absender", self.absender); f.addRow("Empfänger", self.empfaenger)
        f.addRow(_ok(self, "Anlegen"))


class EtikettenDialog(PanelFaehig, QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Etiketten")
        f = QFormLayout(self)
        f.addRow(QLabel("Ein Bogen wird angelegt. Steht überall dasselbe, kommt der Text in jedes Feld; sonst je Zeile eines."))
        self.bogen = QComboBox(); self.bogen.addItems(list(S.ETIKETTEN))
        self.text = QPlainTextEdit("Vorname Nachname\nStraße 1\n12345 Ort"); self.text.setFixedHeight(90)
        self.gleich = QComboBox(); self.gleich.addItems(["ja — derselbe Text", "nein — je Zeile ein Etikett"])
        f.addRow("Bogen", self.bogen); f.addRow("Aufschrift", self.text); f.addRow("Überall dasselbe", self.gleich)
        f.addRow(_ok(self, "Anlegen"))


class SeriendruckDialog(PanelFaehig, QDialog):
    def __init__(self, parent, felder: list[str], gespeichert: str):
        super().__init__(parent)
        self.setWindowTitle("Seriendruck")
        self.resize(560, 420)
        v = QVBoxLayout(self)
        v.addWidget(QLabel(
            ("Im Text gefunden: " + ", ".join("{{" + x + "}}" for x in felder) + "\nDie erste Zeile unten muss diese Namen enthalten.")
            if felder else "Im Text stehen noch keine Platzhalter. Fügen Sie Felder über Sendungen ▸ Seriendruckfeld ein\n"
                           "(oder schreiben Sie {{Name}} in den Text) und kommen Sie dann hierher zurück."))
        self.daten = QPlainTextEdit(gespeichert or (";".join(felder) + "\n" if felder else "Name;Ort\nFrau Meier;Kiel\nHerr Schmidt;Bonn"))
        v.addWidget(self.daten)
        z = QHBoxLayout()
        b = QPushButton("Aus Datei laden (CSV/TXT) …"); b.clicked.connect(self._laden); z.addWidget(b); z.addStretch(1)
        v.addLayout(z)
        v.addWidget(_ok(self, "Briefe erzeugen"))

    def _laden(self):
        pfad, _ = QFileDialog.getOpenFileName(self, "Empfängerliste", "", "Tabellen (*.csv *.txt *.tsv);;Alle Dateien (*)")
        if pfad:
            for enc in ("utf-8-sig", "cp1252"):
                try:
                    self.daten.setPlainText(open(pfad, encoding=enc).read()); break
                except (UnicodeDecodeError, OSError):
                    continue


class RegelDialog(PanelFaehig, QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Regel")
        f = QFormLayout(self)
        f.addRow(QLabel("Wenn das Feld den Wert hat, steht der erste Text da — sonst der zweite."))
        self.feld = QLineEdit("Geschlecht"); self.wert = QLineEdit("w")
        self.dann = QLineEdit("Sehr geehrte Frau"); self.sonst = QLineEdit("Sehr geehrter Herr")
        for lab, w in (("Feld", self.feld), ("ist gleich", self.wert), ("dann", self.dann), ("sonst", self.sonst)):
            f.addRow(lab, w)
        f.addRow(_ok(self, "Einfügen"))
