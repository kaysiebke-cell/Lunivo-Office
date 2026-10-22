"""Ein Fenster auf eine schmale Breite bringen (Seitenleiste), ohne dass etwas abgeschnitten wird oder seitlich gerollt werden muss.

Zeilen, die zu breit sind, brechen um: eine Reihe aus Feldern (``QHBoxLayout``) läuft als Fließzeile über mehrere Zeilen, eine Tabelle
(``QGridLayout``) bekommt mehr Zeilen. Beschriftung und Feld bleiben dabei zusammen. Die Reihenfolge zum Durchtabben bleibt dieselbe.

    schmal_machen(dialog, breite)      # umbrechen, was nicht passt
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QAbstractButton, QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLayout, QRadioButton, QSizePolicy, QWidget


class FlussLayout(QLayout):
    """Zeile, die umbricht (wie Text): Beschriftung und das Feld dahinter bleiben beisammen."""

    def __init__(self, abstand: int = 6):
        super().__init__()
        self._items: list = []
        self._abstand = abstand

    def addItem(self, item) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, i: int):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i: int):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, breite: int) -> int:
        return self._lege(QRect(0, 0, breite, 0), False)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._lege(rect, True)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        m = self.contentsMargins()
        b = max((i.minimumSize().width() for i in self._items), default=0)
        h = max((i.minimumSize().height() for i in self._items), default=0)
        return QSize(b + m.left() + m.right(), h + m.top() + m.bottom())

    def _gruppen(self) -> list[list]:
        """Beschriftung + nächstes Feld sind eine Einheit, alles andere steht für sich."""
        out, i = [], 0
        while i < len(self._items):
            it = self._items[i]
            if isinstance(it.widget(), QLabel) and i + 1 < len(self._items) and not isinstance(self._items[i + 1].widget(), QLabel):
                out.append([it, self._items[i + 1]]); i += 2
            else:
                out.append([it]); i += 1
        return out

    def _lege(self, rect: QRect, setzen: bool) -> int:
        m = self.contentsMargins()
        r = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, zeile = r.x(), r.y(), 0
        for g in self._gruppen():
            gb = sum(i.sizeHint().width() for i in g) + self._abstand * (len(g) - 1)
            gh = max(i.sizeHint().height() for i in g)
            if x > r.x() and x + gb > r.right() + 1:
                x = r.x(); y += zeile + self._abstand; zeile = 0
            if setzen:
                px = x
                for i in g:
                    w = i.sizeHint().width()
                    if len(g) == 1 and w > r.width():
                        w = r.width()
                    i.setGeometry(QRect(QPoint(px, y), QSize(w, i.sizeHint().height())))
                    px += w + self._abstand
            x += gb + self._abstand
            zeile = max(zeile, gh)
        return y + zeile - rect.y() + m.top() + m.bottom()


def _alle_layouts(w: QWidget) -> list[QLayout]:
    out: list[QLayout] = []

    def lauf(l: QLayout) -> None:
        if l in out:
            return
        out.append(l)
        for i in range(l.count()):
            sub = l.itemAt(i).layout()
            if sub is not None:
                lauf(sub)
    for x in [w] + w.findChildren(QWidget):
        if x.layout() is not None:
            lauf(x.layout())
    return out


def _breite(l: QLayout) -> int:
    n = l.count()
    m = l.contentsMargins()
    return sum(l.itemAt(i).sizeHint().width() for i in range(n)) + l.spacing() * max(0, n - 1) + m.left() + m.right()


def _zeile_zu_fluss(l: QHBoxLayout) -> None:
    eltern = l.parent()
    if not isinstance(eltern, QLayout):
        return
    fluss = FlussLayout(max(4, l.spacing() if l.spacing() >= 0 else 6))
    fluss.setContentsMargins(l.contentsMargins())
    items = []
    while l.count():
        items.append(l.takeAt(0))
    for it in items:
        if it.spacerItem() is not None:
            continue                                               # Dehnungen fallen weg: der Fluss füllt nicht auf
        fluss.addItem(it)
    i = eltern.indexOf(l)
    if isinstance(eltern, QGridLayout):
        r, c, rs, cs = eltern.getItemPosition(i)
        eltern.removeItem(l)
        eltern.addLayout(fluss, r, c, rs, cs)
    else:
        stretch = 0
        eltern.removeItem(l)
        eltern.insertLayout(i, fluss, stretch) if hasattr(eltern, "insertLayout") else None


def _tabelle_umbrechen(g: QGridLayout, avail: int) -> None:
    zeilen: dict[int, list] = {}
    for i in range(g.count()):
        r, c, rs, cs = g.getItemPosition(i)
        zeilen.setdefault(r, []).append((c, rs, cs, g.itemAt(i)))
    if any(rs > 1 for z in zeilen.values() for (_c, rs, _cs, _it) in z):                 # Spalten mit Feldern über mehrere Zeilen
        spacing = max(4, g.horizontalSpacing() if g.horizontalSpacing() >= 0 else 6)
        breiten: dict[int, int] = {}
        for z in zeilen.values():
            for (c, _rs, cs, it) in z:
                breiten[c] = max(breiten.get(c, 0), max(it.sizeHint().width(), it.minimumSize().width()) // max(1, cs))
        spalten = sorted(breiten)
        k, summe = 0, 0
        for c in spalten:                                                               # so viele Spalten nebeneinander, wie hineinpassen; der Rest darunter
            if k > 0 and summe + breiten[c] + spacing > avail:
                break
            summe += breiten[c] + spacing; k += 1
        bleibt = set(spalten[:k])
        alle = [(c, r, rs, cs, it) for r, z in zeilen.items() for (c, rs, cs, it) in z]
        for i in range(g.count() - 1, -1, -1):
            g.takeAt(i)
        letzte = 0
        for (c, r, rs, cs, it) in alle:
            if c in bleibt:
                g.addItem(it, r, c, rs, min(cs, k - spalten.index(c)))
                letzte = max(letzte, r + rs)
        n = letzte
        for (c, r, rs, cs, it) in sorted((t for t in alle if t[0] not in bleibt), key=lambda t: (t[0], t[1])):
            g.addItem(it, n, 0, 1, k)
            n += 1
        return
    for it in range(g.count() - 1, -1, -1):
        g.takeAt(it)
    spacing = max(4, g.horizontalSpacing() if g.horizontalSpacing() >= 0 else 6)
    nr = 0
    for r in sorted(zeilen):
        einheiten, i, items = [], 0, sorted(zeilen[r], key=lambda t: t[0])
        while i < len(items):
            c, rs, cs, it = items[i]
            if cs == 1 and isinstance(it.widget(), QLabel) and i + 1 < len(items) and not isinstance(items[i + 1][3].widget(), QLabel) and items[i + 1][2] == 1:
                einheiten.append([items[i], items[i + 1]]); i += 2
            else:
                einheiten.append([items[i]]); i += 1
        x, col, sub = 0, 0, 0
        for e in einheiten:
            b = sum(max(t[3].sizeHint().width(), t[3].minimumSize().width()) for t in e) + spacing * len(e)
            if x > 0 and x + b > avail:
                nr += 1; x, col = 0, 0
            for t in e:
                g.addItem(t[3], nr, col, 1, 1 if t[2] == 1 else t[2])
                col += t[2]
            x += b
        nr += 1


class _Umbruchtext(QLabel):
    """Der Text neben einem Ankreuzfeld, mit Zeilenumbruch; ein Klick darauf schaltet das Feld wie sonst der Text."""

    def __init__(self, knopf: QAbstractButton, text: str):
        super().__init__(text)
        self._knopf = knopf
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(40)
        self.setEnabled(knopf.isEnabled())
        knopf.installEventFilter(self)

    def eventFilter(self, obj, ev) -> bool:                       # grau, wenn das Feld grau ist
        if ev.type() == QEvent.EnabledChange:
            self.setEnabled(self._knopf.isEnabled())
        return False

    def mouseReleaseEvent(self, ev) -> None:
        if self._knopf.isEnabled() and ev.button() == Qt.LeftButton:
            self._knopf.click()
        super().mouseReleaseEvent(ev)


def _knopf_umbrechen(l: QLayout, k: QAbstractButton) -> None:
    text = k.text()
    k.setAccessibleName(text.replace("&", ""))
    k.setText("")
    k.setSizePolicy(QSizePolicy.Fixed, k.sizePolicy().verticalPolicy())
    host = QWidget()
    h = QHBoxLayout(host); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(4)
    t = _Umbruchtext(k, text)
    host.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
    l.replaceWidget(k, host)
    h.addWidget(k, 0, Qt.AlignTop); h.addWidget(t, 1)
    host.show(); k.show(); t.show()


def schmal_machen(d: QWidget, breite: int) -> None:
    """Alles in ``d``, was breiter als ``breite`` Pixel ist, umbrechen."""
    for lb in d.findChildren(QLabel):                                        # lange Texte laufen in die nächste Zeile statt über den Rand
        if not lb.wordWrap() and lb.pixmap().isNull() and lb.minimumSizeHint().width() > breite - 30:
            lb.setWordWrap(True)
            lb.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            lb.setMinimumWidth(40)
    for l in _alle_layouts(d):
        for i in range(l.count()):
            w = l.itemAt(i).widget()
            if isinstance(w, (QCheckBox, QRadioButton)) and w.text() and w.minimumSizeHint().width() > breite - 30:
                _knopf_umbrechen(l, w)
    for l in _alle_layouts(d):
        if isinstance(l, QGridLayout):
            if max(_breite_gitter(l), l.minimumSize().width()) > breite:
                _tabelle_umbrechen(l, breite)
        elif isinstance(l, QHBoxLayout) and l.parent() is not None and max(_breite(l), l.minimumSize().width()) > breite:
            _zeile_zu_fluss(l)


def _breite_gitter(g: QGridLayout) -> int:
    spalten: dict[int, int] = {}
    for i in range(g.count()):
        r, c, rs, cs = g.getItemPosition(i)
        if cs == 1:
            spalten[c] = max(spalten.get(c, 0), g.itemAt(i).sizeHint().width())
    m = g.contentsMargins()
    return sum(spalten.values()) + max(4, g.horizontalSpacing() if g.horizontalSpacing() >= 0 else 6) * max(0, len(spalten) - 1) + m.left() + m.right()
