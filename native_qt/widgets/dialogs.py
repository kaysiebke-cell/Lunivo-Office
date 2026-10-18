"""Kleine Dialoge: Seite einrichten, Absatz, Kopf-/Fußzeile, Tabelle, Suchen/Ersetzen."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
    QWidget,
)

from ..editor.page import PAPER_MM, HeaderFooter, PageSettings


def _spin(value: float, lo=0.0, hi=500.0, suffix=" mm", step=1.0, decimals=1) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi); s.setSuffix(suffix); s.setSingleStep(step); s.setDecimals(decimals); s.setValue(value)
    return s


class PageSetupDialog(QDialog):
    def __init__(self, page: PageSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seite einrichten")
        self.page = page.copy()
        form = QFormLayout()
        self.paper = QComboBox(); self.paper.addItems(list(PAPER_MM) + ["Benutzerdefiniert"])
        self.paper.setCurrentText(page.paper_name())
        self.orient = QComboBox(); self.orient.addItems(["Hochformat", "Querformat"])
        self.orient.setCurrentIndex(1 if page.landscape else 0)
        self.top = _spin(page.margin_top_mm); self.bottom = _spin(page.margin_bottom_mm)
        self.left = _spin(page.margin_left_mm); self.right = _spin(page.margin_right_mm)
        form.addRow("Papierformat", self.paper); form.addRow("Ausrichtung", self.orient)
        form.addRow("Rand oben", self.top); form.addRow("Rand unten", self.bottom)
        form.addRow("Rand links", self.left); form.addRow("Rand rechts", self.right)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)

    def result_page(self) -> PageSettings:
        p = self.page
        if self.paper.currentText() in PAPER_MM:
            p.width_mm, p.height_mm = sorted(PAPER_MM[self.paper.currentText()])
        else:
            p.width_mm, p.height_mm = sorted((p.width_mm, p.height_mm))
        p.set_orientation(self.orient.currentIndex() == 1)
        p.margin_top_mm, p.margin_bottom_mm = self.top.value(), self.bottom.value()
        p.margin_left_mm, p.margin_right_mm = self.left.value(), self.right.value()
        return p

    def accept(self) -> None:
        p = self.result_page()
        if p.margin_left_mm + p.margin_right_mm >= p.width_mm - 20 or \
                p.margin_top_mm + p.margin_bottom_mm >= p.height_mm - 20:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Seite einrichten", "Die Ränder lassen zu wenig Platz für Text.")
            return
        super().accept()


class ParagraphDialog(QDialog):
    def __init__(self, left=0.0, right=0.0, first=0.0, before=0.0, after=0.0, line=1.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Absatz")
        form = QFormLayout()
        self.left = _spin(left, 0, 300); self.right = _spin(right, 0, 300); self.first = _spin(first, -300, 300)
        self.before = _spin(before, 0, 200, " pt"); self.after = _spin(after, 0, 200, " pt")
        self.line = _spin(line, 0.5, 5.0, " ×", 0.05, 2)
        for lab, w in (("Einzug links", self.left), ("Einzug rechts", self.right),
                       ("Erste Zeile", self.first), ("Abstand vor", self.before),
                       ("Abstand nach", self.after), ("Zeilenabstand", self.line)):
            form.addRow(lab, w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)


class HeaderFooterDialog(QDialog):
    def __init__(self, title: str, hf: HeaderFooter, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.text = QPlainTextEdit(hf.text)
        self.text.setPlaceholderText("Text eingeben. {PAGE} = Seitenzahl, {PAGES} = Seitenanzahl")
        self.align = QComboBox(); self.align.addItems(["Links", "Zentriert", "Rechts"])
        self.align.setCurrentIndex({"left": 0, "center": 1, "right": 2}.get(hf.align, 1))
        b = QPushButton("Seitenzahl einfügen")
        b.clicked.connect(lambda: self.text.insertPlainText("{PAGE}"))
        lay = QVBoxLayout(self)
        lay.addWidget(self.text); 
        row = QHBoxLayout(); row.addWidget(QLabel("Ausrichtung")); row.addWidget(self.align); row.addWidget(b)
        lay.addLayout(row)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def value(self) -> HeaderFooter:
        return HeaderFooter(self.text.toPlainText().strip("\n"),
                            ["left", "center", "right"][self.align.currentIndex()])


class TableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tabelle einfügen")
        self.rows = QSpinBox(); self.rows.setRange(1, 200); self.rows.setValue(3)
        self.cols = QSpinBox(); self.cols.setRange(1, 30); self.cols.setValue(3)
        self.borders = QCheckBox("Rahmenlinien"); self.borders.setChecked(True)
        form = QFormLayout(); form.addRow("Zeilen", self.rows); form.addRow("Spalten", self.cols)
        form.addRow("", self.borders)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self); lay.addLayout(form); lay.addWidget(bb)


class FindReplaceDialog(QDialog):
    """Nicht-modal: bleibt offen, während man im Dokument arbeitet."""
    def __init__(self, get_editor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Suchen und Ersetzen")
        self.get_editor = get_editor
        self.find = QLineEdit(); self.repl = QLineEdit()
        self.case = QCheckBox("Groß-/Kleinschreibung beachten"); self.whole = QCheckBox("Ganze Wörter")
        self.msg = QLabel("")
        g = QGridLayout(self)
        g.addWidget(QLabel("Suchen nach"), 0, 0); g.addWidget(self.find, 0, 1, 1, 3)
        g.addWidget(QLabel("Ersetzen durch"), 1, 0); g.addWidget(self.repl, 1, 1, 1, 3)
        g.addWidget(self.case, 2, 0, 1, 2); g.addWidget(self.whole, 2, 2, 1, 2)
        for i, (t, fn) in enumerate((("Weitersuchen", self.next), ("Zurück", self.prev),
                                     ("Ersetzen", self.replace_one), ("Alle ersetzen", self.replace_all))):
            b = QPushButton(t); b.clicked.connect(fn); g.addWidget(b, 3, i)
        g.addWidget(self.msg, 4, 0, 1, 4)
        self.find.returnPressed.connect(self.next)

    def show_with_selection(self) -> None:
        ed = self.get_editor()
        if ed and ed.textCursor().hasSelection():
            self.find.setText(ed.textCursor().selectedText())
        self.show(); self.raise_(); self.activateWindow(); self.find.setFocus(); self.find.selectAll()

    def _ed(self):
        ed = self.get_editor()
        if ed is None:
            self.msg.setText("Kein Dokument geöffnet.")
        return ed

    def next(self):
        ed = self._ed()
        if ed:
            ok = ed.find_text(self.find.text(), False, self.case.isChecked(), self.whole.isChecked())
            self.msg.setText("" if ok else "Nicht gefunden.")

    def prev(self):
        ed = self._ed()
        if ed:
            ok = ed.find_text(self.find.text(), True, self.case.isChecked(), self.whole.isChecked())
            self.msg.setText("" if ok else "Nicht gefunden.")

    def replace_one(self):
        ed = self._ed()
        if ed:
            ed.replace_current(self.find.text(), self.repl.text(), self.case.isChecked())
            self.next()

    def replace_all(self):
        ed = self._ed()
        if ed:
            n = ed.replace_all(self.find.text(), self.repl.text(), self.case.isChecked(), self.whole.isChecked())
            self.msg.setText(f"{n} Ersetzung(en).")
