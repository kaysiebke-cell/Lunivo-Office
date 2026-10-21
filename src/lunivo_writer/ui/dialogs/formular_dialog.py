"""Dialog zum Anlegen eines Formularfelds (Textfeld, Auswahlliste, Datum, Kontrollkästchen, Schaltfläche)."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout

from lunivo_writer.editor import formular as FO

TITEL = {"text": "Textfeld", "auswahl": "Auswahlliste", "datum": "Datumsfeld", "kasten": "Kontrollkästchen", "knopf": "Schaltfläche"}


class FormFeldDialog(QDialog):
    def __init__(self, fenster, art: str, bestehend: dict | None = None):
        super().__init__(fenster)
        self.art = art
        m = bestehend or {}
        self.setWindowTitle(TITEL[art] + " einfügen" if not bestehend else TITEL[art] + " bearbeiten")
        self.setMinimumWidth(420)
        f = QFormLayout()
        self.name = QLineEdit(m.get("name", ""))
        self.name.setPlaceholderText("z. B. Vorname")
        f.addRow("Name des Feldes", self.name)
        self.platz = QLineEdit(m.get("platzhalter", ""))
        self.beschriftung = QLineEdit(m.get("beschriftung", ""))
        self.liste = QPlainTextEdit("\n".join(m.get("optionen", [])))
        self.aufschrift = QLineEdit(m.get("aufschrift", "Absenden"))
        self.aktion = QComboBox(); self.aktion.addItems(FO.AKTIONEN); self.aktion.setCurrentText(m.get("aktion", "Keine"))
        if art in ("text", "auswahl", "datum"):
            self.platz.setPlaceholderText({"text": "Text eingeben", "auswahl": "Auswahl treffen", "datum": "Datum wählen"}[art])
            f.addRow("Hinweis im leeren Feld", self.platz)
        if art == "auswahl":
            self.liste.setPlaceholderText("Ein Eintrag pro Zeile")
            self.liste.setFixedHeight(90)
            f.addRow("Einträge", self.liste)
        if art == "kasten":
            f.addRow("Beschriftung daneben", self.beschriftung)
        if art == "knopf":
            f.addRow("Aufschrift", self.aufschrift)
            f.addRow("Aktion beim Klicken", self.aktion)
        v = QVBoxLayout(self)
        v.addLayout(f)
        info = QLabel("Felder werden in DOCX als Inhaltssteuerelemente gespeichert und lassen sich auch in anderen Textprogrammen ausfüllen.")
        info.setWordWrap(True)
        info.setStyleSheet("color: palette(mid);")
        v.addWidget(info)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _ok(self) -> None:
        if self.art == "auswahl" and not [z for z in self.liste.toPlainText().splitlines() if z.strip()]:
            self.liste.setFocus()
            return
        self.accept()

    def meta(self) -> dict:
        if self.art == "auswahl":
            return FO.meta("auswahl", self.name.text().strip(), platzhalter=self.platz.text().strip(),
                           optionen=[z.strip() for z in self.liste.toPlainText().splitlines() if z.strip()])
        if self.art == "kasten":
            return FO.meta("kasten", self.name.text().strip(), beschriftung=self.beschriftung.text().strip())
        if self.art == "knopf":
            return FO.meta("knopf", self.name.text().strip(), aufschrift=self.aufschrift.text().strip() or "Schaltfläche",
                           aktion=self.aktion.currentText())
        return FO.meta(self.art, self.name.text().strip(), platzhalter=self.platz.text().strip())
