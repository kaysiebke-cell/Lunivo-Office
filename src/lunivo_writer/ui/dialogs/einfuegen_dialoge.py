"""Dialoge zum Einfügen: Formen, WordArt, Diagramm, Piktogramm, Formel, Deckblatt, Datum, Textbausteine."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QColorDialog, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)

from lunivo_writer.editor import einfuegen as E
from lunivo_writer.services import bausteine


def _ok(dlg):
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
    return bb


class _Farbknopf(QPushButton):
    def __init__(self, farbe: str, titel: str = "Farbe"):
        super().__init__(farbe)
        self.farbe = farbe
        self.titel = titel
        self.clicked.connect(self._waehle)
        self._zeige()

    def _waehle(self):
        c = QColorDialog.getColor(QColor(self.farbe), self, self.titel)
        if c.isValid():
            self.farbe = c.name(); self._zeige()

    def _zeige(self):
        self.setText(self.farbe)
        self.setStyleSheet(f"QPushButton {{ background: {self.farbe}; color: {'white' if QColor(self.farbe).lightness() < 140 else 'black'}; }}")


class VorschauMixin:
    def _vorschau_bauen(self, layout):
        self.vorschau = QLabel(); self.vorschau.setMinimumHeight(120); self.vorschau.setAlignment(Qt.AlignCenter)
        self.vorschau.setStyleSheet("background: white; border: 1px solid #adb5bd;")
        layout.addWidget(self.vorschau)

    def _zeige(self, img):
        pm = QPixmap.fromImage(img)
        if pm.width() > 460:
            pm = pm.scaledToWidth(460, Qt.SmoothTransformation)
        self.vorschau.setPixmap(pm)


class FormDialog(QDialog, VorschauMixin):
    def __init__(self, parent, form: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Form einfügen")
        v = QVBoxLayout(self); f = QFormLayout(); v.addLayout(f)
        self.art = QComboBox(); self.art.addItems(E.FORMEN)
        if form:
            self.art.setCurrentText(form)
        self.fuell = _Farbknopf("#4a8fd8", "Füllfarbe"); self.linie = _Farbknopf("#1f3864", "Linienfarbe")
        self.breite = QSpinBox(); self.breite.setRange(20, 1200); self.breite.setValue(240)
        self.hoehe = QSpinBox(); self.hoehe.setRange(10, 1200); self.hoehe.setValue(140)
        self.strich = QDoubleSpinBox(); self.strich.setRange(0.5, 12); self.strich.setValue(2.0)
        self.text = QLineEdit()
        for lab, w in (("Form", self.art), ("Füllfarbe", self.fuell), ("Linienfarbe", self.linie), ("Breite (px)", self.breite),
                       ("Höhe (px)", self.hoehe), ("Linienstärke", self.strich), ("Text in der Form", self.text)):
            f.addRow(lab, w)
        self._vorschau_bauen(v)
        v.addWidget(_ok(self))
        for w in (self.art, self.breite, self.hoehe, self.strich, self.text):
            (w.currentTextChanged if isinstance(w, QComboBox) else w.textChanged if isinstance(w, QLineEdit) else w.valueChanged).connect(self.aktualisieren)
        self.fuell.clicked.connect(self.aktualisieren); self.linie.clicked.connect(self.aktualisieren)
        self.aktualisieren()

    def bild(self):
        return E.form_bild(self.art.currentText(), self.breite.value(), self.hoehe.value(), self.fuell.farbe, self.linie.farbe,
                           self.strich.value(), self.text.text())

    def daten(self):
        return {"form": self.art.currentText(), "fuell": self.fuell.farbe, "linie": self.linie.farbe,
                "strich": self.strich.value(), "text": self.text.text()}

    def aktualisieren(self, *_):
        self._zeige(self.bild())


class SmartArtDialog(QDialog, VorschauMixin):
    """SmartArt anlegen oder bearbeiten: Layout, Farben und der eingerückte Text (zwei Leerzeichen = eine Ebene tiefer)."""
    def __init__(self, parent, daten: dict | None = None):
        super().__init__(parent)
        from lunivo_writer.editor import smartart as SA
        self.SA = SA
        self.setWindowTitle("SmartArt")
        v = QVBoxLayout(self); f = QFormLayout(); v.addLayout(f)
        daten = daten or {}
        self.layout_ = QComboBox(); self.layout_.addItems(SA.LAYOUTS)
        self.layout_.setCurrentText(daten.get("layout", "Prozess"))
        self.farben = QComboBox(); self.farben.addItems(list(SA.FARBEN))
        self.farben.setCurrentText(daten.get("farben", "Blau"))
        self.text = QPlainTextEdit(daten.get("text") or SA.MUSTER[self.layout_.currentText()])
        self.text.setMinimumHeight(110)
        f.addRow("Layout", self.layout_); f.addRow("Farben", self.farben); f.addRow("Text (eine Zeile je Punkt)", self.text)
        self._vorschau_bauen(v)
        v.addWidget(_ok(self))
        self.layout_.currentTextChanged.connect(self._layout)
        self.farben.currentTextChanged.connect(self.aktualisieren)
        self.text.textChanged.connect(self.aktualisieren)
        self._eigener_text = bool(daten.get("text"))
        self.aktualisieren()

    def _layout(self, name):
        if not self._eigener_text or self.text.toPlainText() in self.SA.MUSTER.values():
            self.text.blockSignals(True); self.text.setPlainText(self.SA.MUSTER.get(name, "")); self.text.blockSignals(False)
        self.aktualisieren()

    def daten(self):
        return {"layout": self.layout_.currentText(), "farben": self.farben.currentText(), "text": self.text.toPlainText()}

    def aktualisieren(self, *_):
        self._zeige(self.SA.zeichnen(self.daten()))


class WordArtDialog(QDialog, VorschauMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("WordArt")
        v = QVBoxLayout(self); f = QFormLayout(); v.addLayout(f)
        self.text = QLineEdit("Ihr Text"); self.stil = QComboBox(); self.stil.addItems(E.WORDART_STILE)
        self.schrift = QLineEdit("Liberation Sans"); self.pt = QSpinBox(); self.pt.setRange(12, 200); self.pt.setValue(48)
        self.farbe = _Farbknopf("#2f6fb5")
        for lab, w in (("Text", self.text), ("Stil", self.stil), ("Schriftart", self.schrift), ("Größe (pt)", self.pt), ("Farbe", self.farbe)):
            f.addRow(lab, w)
        self._vorschau_bauen(v); v.addWidget(_ok(self))
        self.text.textChanged.connect(self.aktualisieren); self.stil.currentTextChanged.connect(self.aktualisieren)
        self.schrift.textChanged.connect(self.aktualisieren); self.pt.valueChanged.connect(self.aktualisieren)
        self.farbe.clicked.connect(self.aktualisieren)
        self.aktualisieren()

    def bild(self):
        return E.wordart_bild(self.text.text() or " ", self.stil.currentText(), self.schrift.text() or "Liberation Sans",
                              self.pt.value(), self.farbe.farbe)

    def aktualisieren(self, *_):
        self._zeige(self.bild())


class DiagrammDialog(QDialog, VorschauMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Diagramm")
        self.resize(560, 640)
        v = QVBoxLayout(self); f = QFormLayout(); v.addLayout(f)
        self.art = QComboBox(); self.art.addItems(E.DIAGRAMMARTEN); self.titel = QLineEdit("Diagramm")
        f.addRow("Art", self.art); f.addRow("Titel", self.titel)
        self.tab = QTableWidget(4, 3)
        self.tab.setHorizontalHeaderLabels(["Kategorie", "Reihe 1", "Reihe 2"])
        for r, (k, a, b) in enumerate((("Nord", 12, 9), ("Süd", 7, 11), ("Ost", 15, 6), ("West", 9, 13))):
            for c, val in enumerate((k, a, b)):
                self.tab.setItem(r, c, QTableWidgetItem(str(val)))
        v.addWidget(QLabel("Daten (Zeilen und Spalten lassen sich überschreiben):")); v.addWidget(self.tab)
        z = QHBoxLayout()
        for text, fn in (("Zeile +", lambda: self.tab.setRowCount(self.tab.rowCount() + 1)),
                         ("Zeile −", lambda: self.tab.setRowCount(max(1, self.tab.rowCount() - 1)))):
            b = QPushButton(text); b.clicked.connect(fn); b.clicked.connect(self.aktualisieren); z.addWidget(b)
        v.addLayout(z)
        self._vorschau_bauen(v); self.vorschau.setMinimumHeight(220); v.addWidget(_ok(self))
        self.art.currentTextChanged.connect(self.aktualisieren); self.titel.textChanged.connect(self.aktualisieren)
        self.tab.itemChanged.connect(self.aktualisieren)
        self.aktualisieren()

    def daten(self):
        kat, reihen = [], {"Reihe 1": [], "Reihe 2": []}
        for r in range(self.tab.rowCount()):
            k = self.tab.item(r, 0)
            kat.append(k.text() if k else "")
            for c, name in ((1, "Reihe 1"), (2, "Reihe 2")):
                it = self.tab.item(r, c)
                try:
                    reihen[name].append(float((it.text() if it else "0").replace(",", ".")))
                except ValueError:
                    reihen[name].append(0.0)
        return kat, reihen

    def bild(self):
        kat, reihen = self.daten()
        return E.diagramm_bild(self.art.currentText(), self.titel.text(), kat, reihen)

    def aktualisieren(self, *_):
        try:
            self._zeige(self.bild())
        except Exception:
            pass


class PiktogrammDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Piktogramm einfügen")
        self.resize(520, 520)
        from lunivo_writer.ui.widgets import icons
        v = QVBoxLayout(self)
        self.suche = QLineEdit(); self.suche.setPlaceholderText("Suchen (englische Symbolnamen, z. B. heart, home, star)")
        v.addWidget(self.suche)
        self.liste = QListWidget(); self.liste.setViewMode(QListWidget.IconMode); self.liste.setIconSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(40, 40))
        self.liste.setResizeMode(QListWidget.Adjust); self.liste.setGridSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(90, 70))
        self.liste.setUniformItemSizes(True); self.liste.itemDoubleClicked.connect(lambda _: self.accept())
        v.addWidget(self.liste)
        z = QHBoxLayout(); self.farbe = _Farbknopf("#1f2328"); z.addWidget(QLabel("Farbe:")); z.addWidget(self.farbe); z.addStretch(1); v.addLayout(z)
        v.addWidget(_ok(self))
        self.namen = sorted(icons.katalog())
        self.suche.textChanged.connect(self._fuellen)
        self.farbe.clicked.connect(lambda: self._fuellen(self.suche.text()))
        self._fuellen("")

    def _fuellen(self, q):
        from lunivo_writer.ui.widgets import icons
        self.liste.clear()
        q = (q or "").lower().strip()
        for n in self.namen:
            if q and q not in n.lower():
                continue
            if self.liste.count() >= 240:
                break
            from PySide6.QtGui import QIcon
            it = QListWidgetItem(QIcon(QPixmap.fromImage(icons.katalog_bild(n, 40, self.farbe.farbe))), n)
            it.setData(Qt.UserRole, n)
            self.liste.addItem(it)

    def ergebnis(self):
        it = self.liste.currentItem()
        return (it.data(Qt.UserRole), self.farbe.farbe) if it else (None, None)


class FormelDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Formel")
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Schreibweise: hoch  a^2 oder a^{n+1}  · tief  x_1  · Wurzel  sqrt(x)  · Bruch  frac(a,b)  · Griechisch  \\alpha \\pi \\Sigma  ·  \\infty \\leq \\geq \\neq \\pm \\times"))
        self.eingabe = QLineEdit("E = m c^2"); v.addWidget(self.eingabe)
        self.vorschau = QLabel(); self.vorschau.setStyleSheet("background: white; color: black; padding: 8px; font-size: 16pt; font-family: 'DejaVu Serif';")
        v.addWidget(self.vorschau); v.addWidget(_ok(self))
        self.eingabe.textChanged.connect(self._zeige); self._zeige()

    def _zeige(self, *_):
        html = ""
        for t, a in E.formel_teile(self.eingabe.text()):
            t = t.replace("&", "&amp;").replace("<", "&lt;")
            html += f"<sup>{t}</sup>" if a == "hoch" else f"<sub>{t}</sub>" if a == "tief" else t
        self.vorschau.setText(f"<i>{html}</i>")


class DeckblattDialog(QDialog):
    def __init__(self, parent, autor: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Deckblatt")
        f = QFormLayout(self)
        self.vorlage = QComboBox(); self.vorlage.addItems(E.DECKBLATT_VORLAGEN)
        self.titel = QLineEdit("Titel des Dokuments"); self.unter = QLineEdit(); self.autor = QLineEdit(autor)
        self.datum = QLineEdit(E.datum_text("d. MMMM yyyy"))
        for lab, w in (("Vorlage", self.vorlage), ("Titel", self.titel), ("Untertitel", self.unter), ("Autor", self.autor), ("Datum", self.datum)):
            f.addRow(lab, w)
        f.addRow(_ok(self))


class DatumDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Datum und Uhrzeit")
        v = QVBoxLayout(self)
        self.sprache = QComboBox(); self.sprache.addItems(["Deutsch", "Englisch"])
        v.addWidget(QLabel("Sprache:")); v.addWidget(self.sprache)
        self.liste = QListWidget(); v.addWidget(self.liste)
        self.sprache.currentIndexChanged.connect(self._fuellen)
        self.liste.itemDoubleClicked.connect(lambda _: self.accept())
        v.addWidget(_ok(self))
        self._fuellen()

    def _loc(self):
        return "de_DE" if self.sprache.currentIndex() == 0 else "en_GB"

    def _fuellen(self):
        self.liste.clear()
        for fmt in E.DATUMSFORMATE:
            it = QListWidgetItem(E.datum_text(fmt, self._loc())); it.setData(Qt.UserRole, fmt); self.liste.addItem(it)
        self.liste.setCurrentRow(0)

    def ergebnis(self) -> str:
        it = self.liste.currentItem()
        return it.text() if it else ""


class BausteinDialog(QDialog):
    def __init__(self, parent, ed):
        super().__init__(parent)
        self.ed = ed
        self.setWindowTitle("Textbausteine")
        self.resize(460, 420)
        v = QVBoxLayout(self)
        self.liste = QListWidget(); self.liste.itemDoubleClicked.connect(lambda _: self._einfuegen())
        v.addWidget(self.liste)
        z = QHBoxLayout()
        for text, fn in (("Einfügen", self._einfuegen), ("Markierung speichern …", self._neu), ("Löschen", self._weg)):
            b = QPushButton(text); b.clicked.connect(fn); z.addWidget(b)
        v.addLayout(z)
        bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(self.reject); v.addWidget(bb)
        self._fuellen()

    def _fuellen(self):
        self.liste.clear()
        for b in bausteine.laden():
            it = QListWidgetItem(f"{b['name']} — {b.get('text', '')[:50]}"); it.setData(Qt.UserRole, b); self.liste.addItem(it)

    def _neu(self):
        from PySide6.QtGui import QTextDocumentFragment
        from PySide6.QtWidgets import QInputDialog
        c = self.ed.textCursor()
        if not c.hasSelection():
            QMessageBox.information(self, "Textbaustein", "Bitte zuerst den Text markieren, der gemerkt werden soll.")
            return
        n, ok = QInputDialog.getText(self, "Textbaustein", "Name des Bausteins:")
        if ok and n.strip():
            bausteine.hinzufuegen(n.strip(), QTextDocumentFragment(c)); self._fuellen()

    def _weg(self):
        it = self.liste.currentItem()
        if it:
            bausteine.entfernen(it.data(Qt.UserRole)["name"]); self._fuellen()

    def _einfuegen(self):
        it = self.liste.currentItem()
        if it:
            bausteine.einfuegen(self.ed.textCursor(), it.data(Qt.UserRole)); self.ed.document().setModified(True); self.accept()
