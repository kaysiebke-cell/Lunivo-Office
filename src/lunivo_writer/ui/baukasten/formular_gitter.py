"""Formular, das sich der Breite anpasst — der Baustein für Felder in Zusatzfenstern (Seitenleiste) und in breiten Fenstern.

Statt Felder in feste Spalten eines ``QGridLayout`` zu setzen, nennt man nur, was zusammengehört:

    f = FormularGitter(gruppe)                       # Layout für eine Gruppe oder Seite
    f.zeile("Vor Text:", self.links)                 # Beschriftung + Feld
    f.zeile("Sondereinzug:", self.sonder)
    f.breit(self.rest_einzug)                        # ein Feld über die ganze Breite (Ankreuzfeld, Liste, Vorschau …)

Das Gitter entscheidet bei jeder Breite neu: reicht der Platz, stehen zwei Paare nebeneinander; sonst eines je Zeile mit der Beschriftung links;
ist es noch enger, steht die Beschriftung über dem Feld. Nichts wird abgeschnitten, kein seitliches Rollen. ``UmbruchSchalter`` ist ein
Ankreuzfeld, dessen langer Text in die nächste Zeile läuft.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (QHBoxLayout, QTabWidget, QCheckBox, QLabel, QLayout, QLayoutItem, QSizePolicy, QStyle, QStyleOptionButton, QWidget, QWidgetItem)

ABSTAND = 8
SPALTEN_ABSTAND = 16


class UmbruchSchalter(QCheckBox):
    """Ankreuzfeld, dessen Text bei Platzmangel umbricht (``QCheckBox`` selbst kann das nicht)."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        sp = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Minimum)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)

    def _indikator(self) -> int:
        o = QStyleOptionButton(); self.initStyleOption(o)
        return self.style().subElementRect(QStyle.SE_CheckBoxIndicator, o, self).right() + 8

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, breite: int) -> int:
        rand = self._indikator()
        r = self.fontMetrics().boundingRect(QRect(0, 0, max(40, breite - rand), 10000), Qt.TextWordWrap, self.text())
        return max(self.fontMetrics().height() + 6, r.height() + 6)

    def sizeHint(self) -> QSize:
        return QSize(self._indikator() + self.fontMetrics().horizontalAdvance(self.text()), self.heightForWidth(10000))

    def minimumSizeHint(self) -> QSize:
        return QSize(self._indikator() + 60, self.heightForWidth(self._indikator() + 60))

    def paintEvent(self, ev) -> None:
        p = QPainter(self)
        o = QStyleOptionButton(); self.initStyleOption(o)
        o.text = ""
        self.style().drawControl(QStyle.CE_CheckBox, o, p, self)
        rand = self._indikator()
        p.setPen(self.palette().color(self.foregroundRole() if self.isEnabled() else self.palette().ColorRole.WindowText))
        if not self.isEnabled():
            p.setPen(self.palette().color(self.palette().ColorGroup.Disabled, self.palette().ColorRole.WindowText))
        p.drawText(QRect(rand, 2, self.width() - rand, self.height() - 2), Qt.TextWordWrap | Qt.AlignTop | Qt.AlignLeft, self.text())


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


def abschnittstitel(text: str) -> QLabel:
    """Die Überschrift eines Abschnitts: klein, gedämpft, Großbuchstaben — überall gleich (Gruppen, Spalten, Bereiche in Fenstern)."""
    l = QLabel(text.rstrip(":").upper())
    l.setObjectName("abschnittTitel")
    l.setStyleSheet("color: palette(mid); font-size: 8pt; font-weight: 600;")
    return l


def mittig(widget: QWidget) -> QWidget:
    """Ein Element fester Größe (Vorschau, Farbraster …) in der Mitte der Breite."""
    host = QWidget()
    h = QHBoxLayout(host); h.setContentsMargins(0, 0, 0, 0)
    h.addStretch(1); h.addWidget(widget); h.addStretch(1)
    return host


class _Einheit:
    """Ein Paar (Beschriftung + Feld) oder ein breites Element."""

    def __init__(self, beschriftung: QLayoutItem | None, feld: QLayoutItem, reihe: list | None = None, gewichte: tuple | None = None):
        self.b, self.f = beschriftung, feld
        self.reihe, self.gewichte = reihe, gewichte                       # Felder mit der Beschriftung darüber: [(Beschriftung, Feld), …]


def _hoehe_bei(item: QLayoutItem, breite: int) -> int:
    if item.hasHeightForWidth():
        return item.heightForWidth(max(1, breite))
    return item.sizeHint().height()


def _natuerlich(item: QLayoutItem) -> int:
    return max(item.sizeHint().width(), item.minimumSize().width())


class FormularGitter(QLayout):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._einheiten: list[_Einheit] = []
        self._flach: list[QLayoutItem] = []
        self.setContentsMargins(0, 0, 0, 0)

    # ---- Aufbau ----------------------------------------------------------------------------------------
    def _nimm(self, objekt) -> QLayoutItem:
        if isinstance(objekt, str):
            objekt = QLabel(objekt)
        if isinstance(objekt, QWidget):
            self.addChildWidget(objekt)
            it = QWidgetItem(objekt)
        else:
            self.addChildLayout(objekt)
            it = objekt
        self._flach.append(it)
        return it

    def zeile(self, beschriftung, feld) -> None:
        """Beschriftung (Text oder Widget) und das Feld (Widget oder Layout) dahinter."""
        b = self._nimm(beschriftung)
        if isinstance(beschriftung, str) or isinstance(beschriftung, QLabel):
            w = b.widget()
            if isinstance(w, QLabel):
                w.setWordWrap(False)
                if isinstance(feld, QWidget):
                    w.setBuddy(feld)
        self._einheiten.append(_Einheit(b, self._nimm(feld)))
        self.invalidate()

    def breit(self, objekt) -> None:
        self._einheiten.append(_Einheit(None, self._nimm(objekt)))
        self.invalidate()

    def reihe(self, *paare, gewichte: tuple | None = None) -> None:
        """Mehrere Felder nebeneinander, jedes mit der Beschriftung darüber: ``reihe(("Schriftart:", a), ("Größe:", b), gewichte=(3, 1))``.
        Zu eng für eine Zeile, brechen die Felder um (im Äußersten eines je Zeile)."""
        liste = []
        for b, f in paare:
            bi = self._nimm(b)
            if isinstance(bi.widget(), QLabel):
                bi.widget().setWordWrap(False)
            liste.append((bi, self._nimm(f)))
        self._einheiten.append(_Einheit(None, liste[0][1], liste, gewichte))
        self.invalidate()

    # ---- QLayout ---------------------------------------------------------------------------------------
    def addItem(self, item: QLayoutItem) -> None:                 # ``addWidget`` von QLayout: wie ``breit``
        self._flach.append(item)
        self._einheiten.append(_Einheit(None, item))

    def count(self) -> int:
        return len(self._flach)

    def itemAt(self, i: int):
        return self._flach[i] if 0 <= i < len(self._flach) else None

    def takeAt(self, i: int):
        if not 0 <= i < len(self._flach):
            return None
        it = self._flach.pop(i)
        self._einheiten = [e for e in self._einheiten if e.f is not it and e.b is not it]
        return it

    def hasHeightForWidth(self) -> bool:
        return True

    def sizeHint(self) -> QSize:
        m = self.contentsMargins()
        breit = max((_natuerlich(e.f) + (_natuerlich(e.b) + ABSTAND if e.b is not None else 0) for e in self._einheiten if e.reihe is None), default=0)
        return QSize(breit + m.left() + m.right(), self.heightForWidth(max(breit, 1) + m.left() + m.right()))

    def minimumSize(self) -> QSize:
        m = self.contentsMargins()
        schmal = max((max(e.f.minimumSize().width(), e.b.minimumSize().width() if e.b is not None else 0) for e in self._einheiten if e.reihe is None), default=0)
        for e in self._einheiten:
            for b, f in (e.reihe or []):
                schmal = max(schmal, b.minimumSize().width(), f.minimumSize().width())
        return QSize(schmal + m.left() + m.right(), 0)

    def heightForWidth(self, breite: int) -> int:
        m = self.contentsMargins()
        return self._plan(breite - m.left() - m.right())[1] + m.top() + m.bottom()

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        m = self.contentsMargins()
        r = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        for item, x, y, w, h in self._plan(r.width())[0]:
            item.setGeometry(QRect(r.x() + x, r.y() + y, w, h))

    # ---- die Anordnung ---------------------------------------------------------------------------------
    def _reihe_legen(self, e: _Einheit, breite: int, y: int, out: list) -> int:
        felder = e.reihe
        gew = list(e.gewichte or (1,) * len(felder))
        nat = [max(_natuerlich(b), min(_natuerlich(f), 260)) for b, f in felder]
        zeilen, akt, summe = [], [], 0
        for k, w in enumerate(nat):                                               # so viele wie passen in eine Zeile, der Rest darunter
            if akt and summe + w + SPALTEN_ABSTAND > breite:
                zeilen.append(akt); akt, summe = [], 0
            akt.append(k); summe += w + (SPALTEN_ABSTAND if len(akt) > 1 else 0)
        zeilen.append(akt)
        for z in zeilen:
            frei = breite - (len(z) - 1) * SPALTEN_ABSTAND
            tw = sum(gew[k] for k in z)
            x, hmax = 0, 0
            for n, k in enumerate(z):
                w = frei - sum(int(frei * gew[j] / tw) for j in z[:-1]) if n == len(z) - 1 else int(frei * gew[k] / tw)
                b, f = felder[k]
                hb = b.sizeHint().height(); hf = _hoehe_bei(f, w)
                out.append((b, x, y, w, hb)); out.append((f, x, y + hb + 2, w, hf))
                hmax = max(hmax, hb + 2 + hf); x += w + SPALTEN_ABSTAND
            y += hmax + ABSTAND
        return y

    def _plan(self, breite: int):
        """→ ([(Element, x, y, Breite, Höhe)], Gesamthöhe) bei dieser Breite."""
        paare = [e for e in self._einheiten if e.b is not None]
        bw = max((_natuerlich(e.b) for e in paare), default=0)                    # Breite der Beschriftungen
        fw = max((_natuerlich(e.f) for e in paare), default=0)                    # Breite, die ein Feld gern hätte
        wunsch = bw + ABSTAND + fw
        spalten = 2 if paare and 2 * wunsch + SPALTEN_ABSTAND <= breite else 1
        gestapelt = bool(paare) and wunsch > breite                               # zu eng für „Beschriftung links“: darüber
        out, y = [], 0
        i = 0
        n = len(self._einheiten)
        while i < n:
            e = self._einheiten[i]
            if e.reihe is not None:
                y = self._reihe_legen(e, breite, y, out); i += 1
                continue
            if e.b is None:                                                       # breites Element: eine ganze Zeile
                h = _hoehe_bei(e.f, breite)
                out.append((e.f, 0, y, breite, h)); y += h + ABSTAND; i += 1
                continue
            zeile = [e]
            while spalten == 2 and len(zeile) < 2 and i + len(zeile) < n and self._einheiten[i + len(zeile)].b is not None:
                zeile.append(self._einheiten[i + len(zeile)])
            sp = (breite - (len(zeile) - 1) * SPALTEN_ABSTAND) // len(zeile) if len(zeile) > 1 else breite
            hmax = 0
            plaetze = []
            for k, u in enumerate(zeile):
                x0 = k * (sp + SPALTEN_ABSTAND)
                if gestapelt:
                    hb = u.b.sizeHint().height()
                    hf = _hoehe_bei(u.f, sp)
                    plaetze.append((u.b, x0, 0, sp, hb)); plaetze.append((u.f, x0, hb + 2, sp, hf)); hmax = max(hmax, hb + 2 + hf)
                else:
                    fb = max(40, sp - bw - ABSTAND)
                    hf = _hoehe_bei(u.f, fb)
                    hb = u.b.sizeHint().height()
                    h = max(hb, hf)
                    plaetze.append((u.b, x0, (h - hb) // 2, bw, hb)); plaetze.append((u.f, x0 + bw + ABSTAND, 0, fb, hf)); hmax = max(hmax, h)
            for it, x, dy, w, h in plaetze:
                out.append((it, x, y + dy, w, h))
            y += hmax + ABSTAND
            i += len(zeile)
        return out, max(0, y - ABSTAND)


class AngepassteReiter(QTabWidget):
    """Reiter, deren Höhe dem gewählten Reiter folgt (ein ``QTabWidget`` richtet sich sonst nach dem höchsten und lässt kürzeren Reitern leeren Platz)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.currentChanged.connect(self._aktuelle_seite)

    def _aktuelle_seite(self, _i: int = 0) -> None:
        """Nur die gewählte Seite bestimmt die Höhe: die anderen zählen für das Layout nicht mit (sonst bleibt unter kürzeren Reitern leerer Platz)."""
        for k in range(self.count()):
            w = self.widget(k)
            sp = w.sizePolicy()
            sp.setVerticalPolicy(QSizePolicy.Preferred if k == self.currentIndex() else QSizePolicy.Ignored)
            w.setSizePolicy(sp)
        self.updateGeometry()
        e = self.parentWidget()
        while e is not None:                                      # die Layouts darüber merken sich sonst die Höhe des vorigen Reiters
            if e.layout() is not None:
                e.layout().invalidate()
            e = e.parentWidget()

    def tabInserted(self, index: int) -> None:
        super().tabInserted(index)
        self._aktuelle_seite()

    def _mass(self, minimum: bool) -> QSize:
        w = self.currentWidget()
        if w is None:
            return super().minimumSizeHint() if minimum else super().sizeHint()
        ws = w.minimumSizeHint() if minimum else w.sizeHint()
        h = max(ws.height(), w.minimumHeight())                                       # ein Reiter mit fester Höhe (zum Beispiel Kachelraster) gilt mit dieser
        if w.maximumHeight() < 16777215:
            h = min(h, w.maximumHeight())
        ws = QSize(ws.width(), h)
        tb = self.tabBar().sizeHint()
        return QSize(max(ws.width(), tb.width()) + 6, ws.height() + tb.height() + 8)

    def hasHeightForWidth(self) -> bool:
        w = self.currentWidget()
        return w is not None and w.hasHeightForWidth()

    def heightForWidth(self, breite: int) -> int:
        """Die Höhe der gewählten Seite bei dieser Breite (Seiten aus ``FormularGitter`` brechen um): so bleibt unter kürzeren Reitern kein leerer Platz."""
        w = self.currentWidget()
        tb = self.tabBar().sizeHint()
        return w.heightForWidth(max(1, breite - 6)) + tb.height() + 8

    def sizeHint(self) -> QSize:
        return self._mass(False)

    def minimumSizeHint(self) -> QSize:
        return self._mass(True)
