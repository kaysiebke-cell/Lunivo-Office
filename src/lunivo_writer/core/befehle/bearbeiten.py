"""Befehle: Zwischenablage und Bearbeiten."""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMenu
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile


class BearbeitenBefehle:
    """Befehle des Bandes: Zwischenablage und Bearbeiten. Ein Baustein von ``Befehle`` (siehe ``core/commands.py``)."""


    # ---- Zwischenablage ------------------------------------------------------------------
    def einfuegen(self, k=None):
        if self.ed: self.ed.paste()


    def einfuegenOhne(self, k=None):
        self.w.paste_plain()


    def menue_einfuegenKlappe(self):
        m = QMenu()
        m.addAction("Einfügen", self.einfuegen)
        m.addAction("Einfügen ohne Formatierung", self.einfuegenOhne)
        return m


    def inhalteEinfuegen(self, k=None):
        """„Inhalte einfügen …“: aus den Formaten der Zwischenablage eines wählen (mit Formatierung, nur Text, Bild)."""
        if not self.ed:
            return
        from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QListWidget, QVBoxLayout, QLabel
        md = QApplication.clipboard().mimeData()
        optionen = []
        if md.hasText() or md.hasUrls() or md.formats():
            optionen.append(("Mit Formatierung", "formatiert"))
        if md.hasText():
            optionen.append(("Unformatierter Text", "text"))
        if md.hasImage():
            optionen.append(("Bild", "bild"))
        if not optionen:
            return
        d = QDialog(self.w); d.setWindowTitle("Inhalte einfügen"); d.resize(320, 220)
        v = QVBoxLayout(d); v.addWidget(QLabel("Als:"))
        liste = QListWidget(); v.addWidget(liste, 1)
        for text, art in optionen:
            liste.addItem(text); liste.item(liste.count() - 1).setData(0x100, art)
        liste.setCurrentRow(0); liste.itemDoubleClicked.connect(lambda _: d.accept())
        bb = knopfzeile(d); v.addWidget(bb)
        if not d.exec() or liste.currentItem() is None:
            return
        art = liste.currentItem().data(0x100)
        if art == "text":
            self.w.paste_plain()
        elif art == "bild":
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QTextDocument, QTextImageFormat
            img = QApplication.clipboard().image()
            name = f"einfuegen-{id(img)}"
            self.ed.document().addResource(QTextDocument.ImageResource, QUrl(name), img)
            f = QTextImageFormat(); f.setName(name); f.setWidth(min(img.width(), 480)); f.setHeight(img.height() * min(img.width(), 480) / max(1, img.width()))
            self.ed.textCursor().insertImage(f)
        else:
            self.ed.paste()


    def ausschneiden(self, k=None):
        if self.ed: self.ed.cut()


    def kopieren(self, k=None):
        if self.ed: self.ed.copy()


    # ---- Bearbeiten -----------------------------------------------------------------------------------------
    def suchen(self, k=None, *_):
        self.w.find_dialog_show()


    ersetzen = suchen

    w_sucheZeigen = suchen


    def allesMarkieren(self, k=None):
        if self.ed: self.ed.selectAll()
