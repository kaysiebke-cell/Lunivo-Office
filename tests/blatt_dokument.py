"""Mehrseitiges Testdokument: Überschriften, lange Absätze, Liste, Tabelle, Bild, manueller Seitenumbruch."""
from PySide6.QtGui import QColor, QImage, QTextCursor

LOREM = ("Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore "
         "magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. ") * 6


def fuelle(ed, kapitel=6):
    from lunivo_writer.editor import einfuegen as E
    c = ed.textCursor()
    for k in range(1, kapitel + 1):
        ed.setTextCursor(c)
        ed.insertPlainText(f"Kapitel {k}\n")
        b = ed.document().findBlockByNumber(ed.document().blockCount() - 2)
        ed.apply_style("Überschrift 1") if False else None
        for _ in range(3):
            ed.insertPlainText(LOREM + "\n")
        if k == 2:
            ed.insert_table(8, 3)
            ed.moveCursor(QTextCursor.End)
            ed.insertPlainText("\n")
        if k == 3:
            img = QImage(400, 300, QImage.Format_RGB32); img.fill(QColor("steelblue"))
            E.qimage_einfuegen(ed, img, "Bild")
            ed.insertPlainText("\n")
        if k == 4:
            ed.insert_page_break()
            ed.insertPlainText("Nach dem manuellen Seitenumbruch\n")
        c = ed.textCursor()
    # Überschriften formatieren
    d = ed.document()
    blk = d.firstBlock()
    while blk.isValid():
        if blk.text().startswith("Kapitel "):
            ed._stil_auf_block(blk, "Überschrift 1")
        blk = blk.next()
