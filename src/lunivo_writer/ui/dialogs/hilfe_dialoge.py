"""Hilfe: Handbuch, Tastenkürzel, Erweiterungen."""
from __future__ import annotations

import os
from lunivo_writer.core import paths

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser,
                               QVBoxLayout)

from lunivo_writer.ui import kuerzel




from lunivo_writer.core.farben import Farbe
def _browser(parent, titel: str, breite=860, hoehe=640) -> tuple[QDialog, QTextBrowser, QVBoxLayout]:
    d = QDialog(parent)
    d.setWindowTitle(titel)
    d.resize(breite, hoehe)
    v = QVBoxLayout(d)
    b = QTextBrowser()
    b.setOpenExternalLinks(True)
    v.addWidget(b, 1)
    return d, b, v


GRUPPEN = [("Anfangen", ["Das erste Blatt", "Mehrere Dokumente", "Die Oberfläche einrichten", "Das ☰ Menü"]),
           ("Schreiben", ["Text und Gestaltung", "Die rechte Maustaste", "Formatvorlagen", "Die Seite"]),
           ("Was hilft", ["Die Schreibhilfe", "Für wen? — Themenwörter", "Die Lesehilfe", "Vorlesen"]),
           ("Bausteine", ["Textbausteine", "Eigene Bausteine", "Vorlagen"]),
           ("Heraus", ["Speichern", "Drucken"]),
           ("Nachschlagen", ["Woher es kommt", "Tastenkürzel", "Wo was liegt", "Wenn etwas klemmt"])]


class _Lesefeld(QTextBrowser):
    """Der Text des Handbuchs in einer ruhigen Spalte: nicht breiter als ~780 px, die Spalte steht in der Mitte."""
    BREITE = 780

    def resizeEvent(self, e):
        super().resizeEvent(e)
        rand = max(28, (self.width() - self.BREITE) // 2)
        self.setViewportMargins(0, 0, 0, 0)
        self.document().setDocumentMargin(rand)


def _handbuch_gestalten(b: QTextBrowser) -> None:
    """Gibt dem Markdown-Text die Gestalt der Vorlage: Antiqua mit Luft, Überschriften, Tabellen ohne Gitter, Merkkästen, Tastenchips."""
    from PySide6.QtGui import QBrush, QColor, QFont, QPalette, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextFrameFormat, QTextLength, QTextTable
    d = b.document()
    pal = b.palette()
    stumm = pal.color(QPalette.PlaceholderText) if hasattr(QPalette, "PlaceholderText") else pal.color(QPalette.Mid)
    linie = pal.color(QPalette.Mid); linie.setAlpha(90)
    grund2 = QColor(pal.color(QPalette.Text)); grund2.setAlpha(18)
    akzent = pal.color(QPalette.Highlight)
    serif = QFont("Georgia"); serif.setStyleHint(QFont.Serif); serif.setPointSizeF(12.5)
    d.setDefaultFont(serif)
    c = QTextCursor(d)
    blk = d.begin()
    while blk.isValid():
        bf, cf = QTextBlockFormat(), QTextCharFormat()
        cur = QTextCursor(blk)
        ebene = blk.blockFormat().headingLevel()
        bf = blk.blockFormat()
        if ebene:
            bf.setTopMargin({1: 6, 2: 34, 3: 20}.get(ebene, 14)); bf.setBottomMargin({1: 4, 2: 10, 3: 6}.get(ebene, 6))
            cf.setFontPointSize({1: 30, 2: 21, 3: 15}.get(ebene, 13)); cf.setFontWeight(QFont.Bold)
            cf.setFontFamilies(["Georgia", "Liberation Serif", "serif"])
        else:
            bf.setLineHeight(128.0, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            if blk.blockFormat().intProperty(0x1080) == 0 and not blk.textList():
                bf.setBottomMargin(10)
        if blk.blockFormat().intProperty(0x1080):
            bf.setBackground(QBrush(grund2)); bf.setLeftMargin(10); bf.setRightMargin(6); bf.setTopMargin(4); bf.setBottomMargin(4)
            bf.setIndent(0)
        cur.setBlockFormat(bf)
        if ebene:
            cur.select(QTextCursor.BlockUnderCursor) if False else None
            cur2 = QTextCursor(blk); cur2.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor); cur2.mergeCharFormat(cf)
        blk = blk.next()
    # Tastenchips und Wege (Schrift mit fester Breite)
    blk = d.begin()
    while blk.isValid():
        it = blk.begin()
        while not it.atEnd():
            f = it.fragment()
            if f.isValid() and f.charFormat().fontFixedPitch():
                cur = QTextCursor(d); cur.setPosition(f.position()); cur.setPosition(f.position() + f.length(), QTextCursor.KeepAnchor)
                cf = QTextCharFormat(); cf.setBackground(QBrush(grund2)); cf.setFontFamilies(["DejaVu Sans Mono", "Liberation Mono", "monospace"]); cf.setFontPointSize(10.5)
                cur.mergeCharFormat(cf)
            it += 1
        blk = blk.next()
    # Tabellen: kein Gitter, nur feine Linien zwischen den Zeilen; leere Kopfzeile fällt weg
    tabellen = [fr for fr in d.rootFrame().childFrames() if isinstance(fr, QTextTable)]
    for t in tabellen:
        if all(not t.cellAt(0, k).firstCursorPosition().block().text().strip() for k in range(t.columns())):
            t.removeRows(0, 1)
        tf = t.format()
        tf.setBorder(0); tf.setCellPadding(9); tf.setCellSpacing(0); tf.setBorderCollapse(True)
        tf.setTopMargin(6); tf.setBottomMargin(14)
        tf.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        if t.columns() == 2:
            tf.setColumnWidthConstraints([QTextLength(QTextLength.PercentageLength, 34), QTextLength(QTextLength.PercentageLength, 66)])
        t.setFormat(tf)
        for r in range(t.rows()):
            for k in range(t.columns()):
                cell = t.cellAt(r, k); cf = cell.format().toTableCellFormat()
                cf.setBorder(0); cf.setBorderBrush(QBrush(linie)); cf.setBottomBorder(1); cf.setBottomBorderStyle(QTextFrameFormat.BorderStyle_Solid)
                cf.setBottomBorderBrush(QBrush(linie))
                cell.setFormat(cf)


def handbuch(parent) -> QDialog:
    """Das Handbuch: links die Gliederung (Gruppen, Abschnitte), rechts der Text. Er liegt als Markdown in resources/handbuch.md."""
    from PySide6.QtCore import QSize
    from PySide6.QtWidgets import QListWidget, QListWidgetItem
    d = QDialog(parent)
    d.setWindowTitle("Handbuch"); d.resize(1180, 780)
    h = QHBoxLayout(d); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
    nav = QListWidget(); nav.setFixedWidth(290); nav.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded); nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); nav.setFrameShape(QFrame.NoFrame); nav.setFocusPolicy(Qt.NoFocus)
    nav.setStyleSheet("QListWidget { background: palette(window); border-right: 1px solid palette(midlight); padding: 14px 8px; outline: none; }"
                      "QListWidget::item { padding: 4px 10px; border-radius: 5px; }"
                      "QListWidget::item:selected { background: palette(midlight); color: palette(window-text); }")
    rechts = QVBoxLayout(); rechts.setContentsMargins(0, 0, 0, 0); rechts.setSpacing(0)
    b = _Lesefeld(); b.setOpenExternalLinks(True); b.setFrameShape(QFrame.NoFrame)
    with open(os.path.join(paths.RESSOURCEN, "handbuch.md"), encoding="utf-8") as fh:
        b.setMarkdown(fh.read())
    _handbuch_gestalten(b)
    rechts.addWidget(b, 1)
    such = QLineEdit(); such.setPlaceholderText("Im Handbuch suchen …"); such.setClearButtonEnabled(True)
    such.setContentsMargins(0, 0, 0, 0)
    z = QHBoxLayout(); z.setContentsMargins(20, 8, 20, 10)
    z.addWidget(such, 1)
    zu = QPushButton("Schließen"); zu.clicked.connect(d.accept); z.addWidget(zu)
    rechts.addLayout(z)
    h.addWidget(nav); h.addLayout(rechts, 1)

    stellen = {}
    blk = b.document().begin()
    while blk.isValid():
        if blk.blockFormat().headingLevel() in (2, 3):
            stellen.setdefault(blk.text().strip(), blk)
            if blk.text().strip() == "Woher dieses Programm kommt":          # die Gliederung nennt es kürzer
                stellen.setdefault("Woher es kommt", blk)
        blk = blk.next()
    ueber_kopf = QListWidgetItem("Lunivo Writer\nEin Raum für Worte — das Handbuch"); ueber_kopf.setData(Qt.UserRole, "")
    f = ueber_kopf.font(); f.setBold(True); ueber_kopf.setFont(f); ueber_kopf.setSizeHint(QSize(0, 52))
    nav.addItem(ueber_kopf)
    for gruppe, titel in GRUPPEN:
        kopf = QListWidgetItem(gruppe.upper()); kopf.setFlags(Qt.NoItemFlags)
        f = kopf.font(); f.setPointSizeF(8); f.setBold(True); kopf.setFont(f); kopf.setSizeHint(QSize(0, 30))
        nav.addItem(kopf)
        for t in titel:
            if t in stellen:
                it = QListWidgetItem(t); it.setData(Qt.UserRole, t); nav.addItem(it)

    def springe(it):
        t = it.data(Qt.UserRole)
        if t == "":
            b.verticalScrollBar().setValue(0)
        elif t in stellen:
            lay = b.document().documentLayout()
            b.verticalScrollBar().setValue(int(lay.blockBoundingRect(stellen[t]).top()) - 8)
    nav.itemClicked.connect(springe)
    such.returnPressed.connect(lambda: b.find(such.text()) or (b.moveCursor(b.textCursor().Start), b.find(such.text())))
    return d


def _fuss(d: QDialog, v: QVBoxLayout) -> None:
    """Wie in der Vorlage: „Abbrechen“ und „Schließen“ rechts unten, beide schließen das Fenster."""
    z = QHBoxLayout(); z.addStretch(1)
    ab, zu = QPushButton("Abbrechen"), QPushButton("Schließen")
    zu.setObjectName("optFertig"); zu.setDefault(True)
    for k in (ab, zu):
        k.setMinimumHeight(34); k.clicked.connect(d.accept); z.addWidget(k)
    v.addSpacing(6); v.addLayout(z)


def _titel(text: str) -> QLabel:
    t = QLabel(text); f = t.font(); f.setPointSize(f.pointSize() + 3); f.setBold(True); t.setFont(f)
    return t


def _dialog(parent, titel: str, breite: int) -> tuple[QDialog, QVBoxLayout]:
    d = QDialog(parent); d.setWindowTitle(titel); d.setMinimumWidth(breite)
    v = QVBoxLayout(d); v.setContentsMargins(24, 22, 24, 18); v.setSpacing(8)
    v.addWidget(_titel(titel)); v.addSpacing(4)
    return d, v


def tastenkuerzel(parent) -> QDialog:
    """„Tastenkombinationen“: je Gruppe eine Überschrift, darunter zwei Kürzel mit Wirkung nebeneinander."""
    d, v = _dialog(parent, "Tastenkombinationen", 640)
    for gruppe, zeilen in kuerzel.HILFE:
        k = QLabel(gruppe.upper()); k.setStyleSheet("color: palette(mid); font-size: 8pt; font-weight: 600; letter-spacing: 1px; margin-top: 10px;")
        v.addWidget(k)
        g = QGridLayout(); g.setHorizontalSpacing(28); g.setVerticalSpacing(4)
        zeile, spalte = 0, 0
        for taste, text in zeilen:
            lang = len(taste) + len(text) > 44                           # lange Einträge bekommen die ganze Zeile
            if lang and spalte:
                zeile, spalte = zeile + 1, 0
            zelle = QHBoxLayout(); zelle.setSpacing(8)
            t = QLabel(taste); f = t.font(); f.setBold(True); t.setFont(f)
            zelle.addWidget(t); zelle.addWidget(QLabel(text)); zelle.addStretch(1)
            g.addLayout(zelle, zeile, spalte, 1, 2 if lang else 1)
            spalte += 2 if lang else 1
            if spalte >= 2:
                zeile, spalte = zeile + 1, 0
        g.setColumnStretch(0, 1); g.setColumnStretch(1, 1)
        v.addLayout(g)
    v.addStretch(1)
    _fuss(d, v)
    return d


def _erweiterungen_liste() -> list[tuple[bool, str, str, str]]:
    from PySide6.QtGui import QFontDatabase
    from lunivo_writer.services import vorlesen
    from lunivo_writer.services.integrations import languagetool, libreoffice
    schriften = [f for f in ("OpenDyslexic", "Lexend", "Atkinson Hyperlegible") if f.lower() in {x.lower() for x in QFontDatabase.families()}]
    return [(bool(libreoffice.finde_soffice()), "Umwandlungsprogramm", "Alte Word-Dateien (DOC), ODT und RTF", "ca. 694 MB"),
            (bool(languagetool.verfuegbar()), "LanguageTool", "„Gründlich prüfen“ — Grammatik über die eigenen Regeln hinaus", "ca. 386 MB"),
            (bool(vorlesen.piper_da()), "Stimmen zum Vorlesen", "aufgenommene Stimmen statt der blechernen des Systems", "ca. 439 MB"),
            (len(schriften) == 3, f"Schriften zum leichteren Lesen ({len(schriften)}/3)", "OpenDyslexic, Lexend, Atkinson Hyperlegible", "ca. 1 MB")]


def erweiterungen(parent) -> QDialog:
    """„Erweiterungen“: jede Karte zeigt mit „DA“, ob der Teil schon geholt ist."""
    d, v = _dialog(parent, "Erweiterungen", 720)
    hin = QLabel("Drei Teile liegen außerhalb des Programms, weil sie zu groß sind. Sie werden geholt, wenn sie zum ersten Mal gebraucht werden — "
                 "und ohne sie läuft alles Übrige weiter: Schreiben, Prüfen.")
    hin.setWordWrap(True); v.addWidget(hin)
    for da, name, text, groesse in _erweiterungen_liste():
        karte = QFrame(); karte.setObjectName("erwKarte")
        karte.setStyleSheet("QFrame#erwKarte { border: 1px solid palette(midlight); border-radius: 8px; }")
        h = QHBoxLayout(karte); h.setContentsMargins(12, 10, 14, 10); h.setSpacing(12)
        b = QLabel("DA" if da else "—"); b.setAlignment(Qt.AlignCenter); b.setFixedSize(40, 26)
        b.setStyleSheet("background: %s; color: white; border-radius: 5px; font-weight: 700;" % ("#2f9e73" if da else Farbe.GRAU))
        mitte = QVBoxLayout(); mitte.setSpacing(2)
        n = QLabel(name); f = n.font(); f.setBold(True); n.setFont(f)
        t = QLabel(text); f = t.font(); f.setItalic(True); t.setFont(f); t.setStyleSheet("color: palette(mid);")
        mitte.addWidget(n); mitte.addWidget(t)
        h.addWidget(b); h.addLayout(mitte, 1)
        g = QLabel(groesse); g.setStyleSheet("color: palette(mid);"); h.addWidget(g, 0, Qt.AlignTop)
        v.addWidget(karte)
    fuss = QLabel("Erweiterungen von fremder Hand nimmt dieses Programm nicht an. Was es kann, steckt im Programm.")
    fuss.setWordWrap(True); v.addWidget(fuss)
    v.addStretch(1)
    _fuss(d, v)
    return d


def ueber(parent, version: str) -> QDialog:
    d, v = _dialog(parent, "Über Lunivo Writer", 460)
    for text in (f"Lunivo Writer {version}\nEin Raum für Worte",
                 "Die Prüfung und der Wortschatz stammen aus der Schreibhilfe.\nAlte Formate (DOC, ODT, RTF) wandelt ein Umwandlungsprogramm im Hintergrund.",
                 "Was geschrieben wird, bleibt auf diesem Rechner.\nNichts geht hinaus, ohne dass du es selbst schickst."):
        l = QLabel(text); l.setWordWrap(True); v.addWidget(l); v.addSpacing(6)
    v.addStretch(1)
    _fuss(d, v)
    return d
