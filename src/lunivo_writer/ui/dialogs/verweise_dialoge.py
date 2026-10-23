"""Dialoge zu Verweisen: Beschriftung, Textmarken, Querverweis, Quellen."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QRadioButton, QVBoxLayout,
)

from lunivo_writer.editor import verweise
from lunivo_writer.editor.literatur import TYPEN, ZITIERWEISEN, eintrag
from lunivo_writer.editor.zusatz import BESCHRIFTUNGEN


def _knoepfe(dlg):
    return knopfzeile(dlg)


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
class BeschriftungDialog(PanelFaehig, QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Beschriftung einfügen")
        f = QFormLayout(self)
        self.label = QComboBox(); self.label.addItems(BESCHRIFTUNGEN)
        self.text = QLineEdit()
        self.pos = QComboBox(); self.pos.addItems(["Unter dem Objekt", "Über dem Objekt"])
        f.addRow("Bezeichnung", self.label); f.addRow("Text (nach der Nummer)", self.text); f.addRow("Position", self.pos)
        f.addRow(_knoepfe(self))


class TextmarkeDialog(PanelFaehig, QDialog):
    def __init__(self, parent, ed):
        super().__init__(parent)
        self.ed = ed
        self.setWindowTitle("Textmarke")
        v = QVBoxLayout(self)
        self.name = QLineEdit(); self.name.setPlaceholderText("Name (Buchstaben, Ziffern, _ ; beginnt mit Buchstaben)")
        v.addWidget(self.name)
        self.liste = QListWidget(); self.liste.itemDoubleClicked.connect(lambda _: self._gehe())
        v.addWidget(self.liste)
        z = QHBoxLayout()
        for text, fn in (("Hinzufügen", self._add), ("Löschen", self._del), ("Gehe zu", self._gehe)):
            b = QPushButton(text); b.clicked.connect(fn); z.addWidget(b)
        v.addLayout(z)
        bb = knopfzeile(self, schliessen=True); v.addWidget(bb)
        self._fuellen()

    def _fuellen(self):
        self.liste.clear()
        for d in verweise.lesezeichen_liste(self.ed):
            self.liste.addItem(d["name"])

    def _add(self):
        n = self.name.text().strip()
        if not verweise.lesezeichen_name_gueltig(n):
            QMessageBox.information(self, "Textmarke", "Der Name muss mit einem Buchstaben beginnen und darf nur Buchstaben, Ziffern und _ enthalten.")
            return
        if not verweise.lesezeichen_setzen(self.ed, n):
            QMessageBox.information(self, "Textmarke", "Bitte Text markieren oder in ein Wort klicken.")
            return
        self._fuellen()

    def _del(self):
        it = self.liste.currentItem()
        if it:
            verweise.lesezeichen_loeschen(self.ed, it.text()); self._fuellen()

    def _gehe(self):
        it = self.liste.currentItem()
        if it:
            verweise.lesezeichen_gehe(self.ed, it.text())


class QuerverweisDialog(PanelFaehig, QDialog):
    def __init__(self, parent, ed):
        super().__init__(parent)
        self.setWindowTitle("Querverweis")
        self.ziele = verweise.querverweis_ziele(ed)
        v = QVBoxLayout(self)
        self.art = QComboBox(); self.art.addItems(["Überschrift", "Abbildung", "Tabelle", "Gleichung", "Textmarke"])
        self.art.currentTextChanged.connect(self._fuellen)
        v.addWidget(self.art)
        self.liste = QListWidget(); v.addWidget(self.liste)
        self.wie = QButtonGroup(self)
        for i, t in enumerate(("Text / Überschrift", "Nur Bezeichnung und Nummer", "Seitenzahl")):
            r = QRadioButton(t); self.wie.addButton(r, i); v.addWidget(r)
            r.setChecked(i == 0)
        v.addWidget(_knoepfe(self))
        self._fuellen("Überschrift")

    def _fuellen(self, art):
        self.liste.clear()
        for z in self.ziele:
            if z["art"] == art:
                it = QListWidgetItem(z["text"][:80]); it.setData(Qt.UserRole, z); self.liste.addItem(it)

    def ergebnis(self):
        it = self.liste.currentItem()
        return (it.data(Qt.UserRole), ["text", "nummer", "seite"][self.wie.checkedId()]) if it else (None, None)


class QuelleDialog(PanelFaehig, QDialog):
    FELDER = [("autor", "Autor(en) — „Nachname, Vorname; …“"), ("titel", "Titel"), ("jahr", "Jahr"), ("verlag", "Verlag"),
              ("ort", "Ort"), ("url", "Adresse (URL)")]

    def __init__(self, parent, q: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Quelle")
        q = q or {}
        f = QFormLayout(self)
        self.typ = QComboBox(); self.typ.addItems(TYPEN); self.typ.setCurrentText(q.get("typ", "Buch"))
        f.addRow("Typ", self.typ)
        self.eingaben = {}
        for k, t in self.FELDER:
            e = QLineEdit(q.get(k, "")); self.eingaben[k] = e; f.addRow(t, e)
        f.addRow(_knoepfe(self))

    def ergebnis(self) -> dict:
        d = {k: e.text().strip() for k, e in self.eingaben.items()}
        d["typ"] = self.typ.currentText()
        return d


class QuellenDialog(PanelFaehig, QDialog):
    def __init__(self, parent, ed):
        super().__init__(parent)
        self.ed = ed
        self.setWindowTitle("Quellen verwalten")
        self.resize(560, 420)
        v = QVBoxLayout(self)
        self.liste = QListWidget(); v.addWidget(self.liste)
        z = QHBoxLayout()
        for text, fn in (("Neu …", self._neu), ("Bearbeiten …", self._bearb), ("Löschen", self._weg), ("Zitat einfügen", self._zitat)):
            b = QPushButton(text); b.clicked.connect(fn); z.addWidget(b)
        v.addLayout(z)
        bb = knopfzeile(self, schliessen=True); v.addWidget(bb)
        self._fuellen()

    def _fuellen(self):
        self.liste.clear()
        for q in self.ed.quellen:
            it = QListWidgetItem(eintrag(q, self.ed.zitierweise)); it.setData(Qt.UserRole, q["tag"]); self.liste.addItem(it)

    def _akt(self):
        it = self.liste.currentItem()
        return next((q for q in self.ed.quellen if it and q["tag"] == it.data(Qt.UserRole)), None)

    def _neu(self):
        d = QuelleDialog(self)
        if d.exec():
            q = d.ergebnis(); q["tag"] = verweise.quelle_tag(self.ed.quellen, q)
            self.ed.quellen.append(q); self.ed.document().setModified(True); self._fuellen()

    def _bearb(self):
        q = self._akt()
        if q:
            d = QuelleDialog(self, q)
            if d.exec():
                q.update(d.ergebnis()); self.ed.document().setModified(True); self._fuellen()

    def _weg(self):
        q = self._akt()
        if q:
            self.ed.quellen.remove(q); self.ed.document().setModified(True); self._fuellen()

    def _zitat(self):
        q = self._akt()
        if q:
            verweise.zitat_einfuegen(self.ed, q); self.accept()
