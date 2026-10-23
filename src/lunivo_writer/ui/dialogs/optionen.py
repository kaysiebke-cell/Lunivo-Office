"""Optionen — das Fenster hinter „☰ Menü ▸ Optionen“ (F9): sechs Seiten in einer flachen Liste, oben eine Suche.

Lesen · Anzeige · Schreiben · Speichern · Drucken und PDF · Name und KI. Jede Seite zeigt nur das Häufige; der Rest steht unter
„Weitere Einstellungen“ (eingeklappt, mit der Tastatur erreichbar). Werte gelten sofort. Konzept: ``docs/konzept-optionen.md``.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QCheckBox, QDialog, QFrame, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QScrollArea,
                               QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from lunivo_writer.core.farben import Farbe
from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.ui.baukasten.einklappgruppe import EinklappGruppe
from lunivo_writer.ui.dialogs.optionen_seiten.ansicht import AnsichtSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.datei import DateiSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.befehle import BefehleSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import erklaerung as _erklaerung
from lunivo_writer.ui.dialogs.optionen_seiten.lesen import LesenSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.lunivo import LunivoSeiten
from lunivo_writer.ui.dialogs.optionen_seiten.name_ki import NameKiSeiten

ERKLAERUNG_LEER = "Zeig auf eine Einstellung — hier steht, was sie tut."

STIL = ('\nQWidget#optLinks { background: palette(window); border-right: 1px solid palette(midlight); }\nQTreeWidget#optNavigation { background: transparent; border: none; outline: none; }\nQTreeWidget#optNavigation::item { padding: 8px 10px; margin: 1px 8px 1px 0; border-radius: 6px; color: palette(window-text); }\nQTreeWidget#optNavigation::item:selected { background: ' + Farbe.AKZENT + '; color: white; font-weight: 600; }\nQTreeWidget#optNavigation::item:hover:!selected { background: palette(midlight); }\nQScrollArea#optSeite, QScrollArea#optSeite > QWidget > QWidget { background: transparent; border: none; }\nQGroupBox { border: 1px solid palette(midlight); border-radius: 10px; margin-top: 26px; padding: 8px 10px 8px 10px; background: transparent; }\nQGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 2px; padding: 0; color: palette(window-text); font-size: 8pt; font-weight: 600; }\nQWidget#optPaar { border-bottom: 1px solid palette(midlight); }\nQLabel#optErklaerung { color: palette(window-text); font-style: italic; padding: 12px 24px; border-top: 1px solid palette(midlight); }\nQFrame#optSchriftkarte { border: 1px solid palette(midlight); border-radius: 8px; }\nQLabel#optVorschau { background: white; color: #111417; border-radius: 6px; padding: 16px 20px; }\nQLabel#optHinweis { color: palette(window-text); font-size: 9pt; padding-left: 26px; }\nQPushButton#optWahl { border: 1px solid palette(mid); border-radius: 8px; padding: 8px 14px; }\nQPushButton#optWahl:checked { background: ' + Farbe.AKZENT + '; color: white; font-weight: 600; border-color: ' + Farbe.AKZENT + '; }\nQPushButton#optWahl:focus { border: 2px solid palette(highlight); }\nQToolButton:focus { border: 2px solid palette(highlight); border-radius: 4px; }\n')

SEITEN = (("lesen", "Lesen"), ("anzeige", "Anzeige"), ("schreiben", "Schreiben"), ("speichern", "Speichern"),
          ("drucken", "Drucken und PDF"), ("ki", "Name und KI"))

# Frühere Seitennamen (Aufrufe aus Menü, Hilfe und Tests) führen auf die neue Seite; manche öffnen dort gleich den passenden Bereich.
ALIAS = {"lesehilfe": "lesen", "schriften": "schreiben", "sprache": "schreiben", "rechtschreibung": "schreiben", "bearbeiten": "schreiben",
         "gedaechtnis": "schreiben", "ansicht": "anzeige", "menueband": "anzeige", "schnellzugriff": "anzeige", "sicherung": "speichern",
         "speicherort": "speichern", "sicherheit": "speichern", "verfolgen": "speichern", "pdf": "drucken", "benutzer": "ki", "erweitert": "ki"}
AUFKLAPPEN = {"ki": "KI einrichten", "erweitert": "Was zusätzlich", "gedaechtnis": "Weitere", "schriften": "Weitere",
              "menueband": "Menüband", "schnellzugriff": "Menüband", "sicherheit": "Weitere", "verfolgen": "Weitere"}


class OptionenAnsicht(LesenSeiten, AnsichtSeiten, DateiSeiten, BefehleSeiten, LunivoSeiten, NameKiSeiten, QWidget):
    """Alle Optionen als Ansicht (Liste und Suche links, Seite rechts) — sie steht in der Datei-Ansicht („☰ Menü ▸ Erweiterte
    Einstellungen“) und im Dialog `OptionenDialog`. Werte gelten sofort."""


    def __init__(self, fenster, seite: str | None = None):
        super().__init__()
        self.w = fenster
        self.setStyleSheet(STIL)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        links = QWidget(); links.setFixedWidth(250); links.setObjectName("optLinks"); links.setAttribute(Qt.WA_StyledBackground, True)
        lv = QVBoxLayout(links); lv.setContentsMargins(8, 8, 8, 8); lv.setSpacing(6)
        self.suche = QLineEdit()
        self.suche.setPlaceholderText("Einstellung suchen …"); self.suche.setToolTip("Suchen (Strg+F)")
        self.suche.setClearButtonEnabled(True)
        self.suche.setMinimumHeight(32)
        self.suche.setAccessibleName("Einstellung suchen")
        self.treffer = QListWidget(); self.treffer.setMaximumHeight(240); self.treffer.hide()
        self.treffer.setAccessibleName("Suchergebnisse")
        self.baum = QTreeWidget()
        self.baum.setObjectName("optNavigation")
        self.baum.setHeaderHidden(True)
        self.baum.setRootIsDecorated(False)
        self.baum.setIndentation(0)
        self.baum.setFocusPolicy(Qt.StrongFocus)
        self.baum.setAccessibleName("Seiten der Optionen")
        lv.addWidget(self.suche); lv.addWidget(self.treffer); lv.addWidget(self.baum, 1)
        self.stapel = QStackedWidget()
        self.stapel.setMinimumWidth(520)
        self.stapel.setMaximumWidth(860)
        h.addWidget(links)
        self.scroll = sc = QScrollArea(); sc.setObjectName("optSeite"); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        halter = QWidget(); hl = QHBoxLayout(halter); hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.stapel); hl.addStretch(1)                      # Seite links, nicht über die ganze Breite gezogen
        sc.setWidget(halter)
        rechts = QWidget(); rv = QVBoxLayout(rechts); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(0)
        rv.addWidget(sc, 1)
        self.erklaerzeile = text_label(ERKLAERUNG_LEER, umbruch=True)
        self.erklaerzeile.setObjectName("optErklaerung")
        rv.addWidget(self.erklaerzeile)
        h.addWidget(rechts, 1)
        self.knoten: dict[str, QTreeWidgetItem] = {}
        bauer = {"lesen": self._lesehilfe, "anzeige": self._ansicht, "schreiben": self._schreiben, "speichern": self._speichern,
                 "drucken": self._drucken, "ki": self._name_ki}
        for key, titel in SEITEN:
            it = QTreeWidgetItem([titel])
            it.setData(0, Qt.UserRole, key)
            it.setData(0, Qt.AccessibleDescriptionRole, f"Seite {len(self.knoten) + 1} von {len(SEITEN)}")
            self.baum.addTopLevelItem(it)
            self.knoten[key] = it
            self.stapel.addWidget(bauer[key](titel))
            it.setData(0, Qt.UserRole + 1, self.stapel.count() - 1)
        self.baum.currentItemChanged.connect(lambda cur, _p: cur and cur.data(0, Qt.UserRole + 1) is not None
                                             and self.stapel.setCurrentIndex(cur.data(0, Qt.UserRole + 1)))
        for wid in self.stapel.findChildren(QWidget):                 # Zeigen auf eine Einstellung erklärt sie unten
            wid.installEventFilter(self)
        self.suche.installEventFilter(self)
        self.suche.textChanged.connect(self._suchen)
        self.suche.returnPressed.connect(lambda: self.treffer.count() and self._springe(self.treffer.item(0)))
        self.treffer.itemActivated.connect(self._springe)
        self.treffer.itemClicked.connect(self._springe)
        sc_f = QShortcut(QKeySequence.Find, self); sc_f.setContext(Qt.WidgetWithChildrenShortcut)
        sc_f.activated.connect(lambda: (self.suche.setFocus(), self.suche.selectAll()))
        self._index: list[tuple[str, str, str, QWidget]] = []
        self._index_bauen()
        self.gehe_zu(seite or "lesen")


    def eventFilter(self, obj, ev):
        if obj is self.suche:
            if ev.type() == QEvent.KeyPress and ev.key() == Qt.Key_Down and self.treffer.count():
                self.treffer.setFocus(); self.treffer.setCurrentRow(0)
                return True
            return super().eventFilter(obj, ev)
        if ev.type() in (QEvent.Enter, QEvent.FocusIn) and isinstance(obj, QWidget):
            w = obj
            while w is not None and not w.property("optName"):
                w = w.parentWidget()
            if w is not None:
                self._erklaere(str(w.property("optName")))
        elif ev.type() == QEvent.Leave:
            self.erklaerzeile.setText(ERKLAERUNG_LEER)
        return super().eventFilter(obj, ev)


    def _erklaere(self, name: str) -> None:
        satz = _erklaerung(name)
        self.erklaerzeile.setText(f"{name} — {satz}" if satz else ERKLAERUNG_LEER)


    def gehe_zu(self, key: str):
        """Eine Seite zeigen; frühere Seitennamen führen auf die neue Seite und klappen dort den passenden Bereich auf."""
        seite = ALIAS.get(key, key)
        self.baum.setCurrentItem(self.knoten.get(seite) or self.knoten["lesen"])
        zeigen = getattr(self, "_aussehen_zeigen", None)
        if zeigen is not None:
            zeigen()                                                  # Hell/Dunkel kann inzwischen anderswo umgestellt worden sein
        vorn = AUFKLAPPEN.get(key)
        if vorn:
            for e in self.stapel.currentWidget().findChildren(EinklappGruppe):
                if e.titel.startswith(vorn):
                    e.ausklappen(True)


    # ---- Suche: findet jede Einstellung, auch die eingeklappten, und springt hin --------------------------------------------------------
    def _index_bauen(self) -> None:
        for key, titel in SEITEN:
            seite = self.stapel.widget(self.knoten[key].data(0, Qt.UserRole + 1))
            gesehen: set[str] = set()
            for w in seite.findChildren(QWidget):
                text = str(w.property("optName") or "")
                if not text and isinstance(w, QCheckBox):
                    text = w.text()
                if text and text.lower() not in gesehen:
                    gesehen.add(text.lower())
                    self._index.append((key, titel, text, w))


    def _suchen(self, q: str) -> None:
        q = q.strip().lower()
        self.treffer.clear()
        if not q:
            self.treffer.hide()
            return
        for key, titel, text, w in self._index:
            if q in text.lower() or q in _erklaerung(text).lower():
                it = QListWidgetItem(f"{text}  ·  {titel}")
                it.setData(Qt.UserRole, (key, w))
                self.treffer.addItem(it)
        if not self.treffer.count():
            self.treffer.addItem(QListWidgetItem("Nichts gefunden"))
            self.treffer.item(0).setFlags(Qt.NoItemFlags)
        self.treffer.show()


    def _springe(self, it: QListWidgetItem) -> None:
        ziel = it.data(Qt.UserRole)
        if not ziel:
            return
        key, w = ziel
        self.gehe_zu(key)
        p = w.parentWidget()
        while p is not None:
            if isinstance(p, EinklappGruppe):
                p.ausklappen(True)
            p = p.parentWidget()

        def zeigen():
            self.scroll.ensureWidgetVisible(w, 0, 60)
            fokus = w if w.focusPolicy() != Qt.NoFocus else next((c for c in w.findChildren(QWidget) if c.focusPolicy() != Qt.NoFocus), None)
            if fokus is not None:
                fokus.setFocus()
        QTimer.singleShot(60, zeigen)


    # ---- Befehlslisten (Menüband, Schnellzugriff): zwei Listen mit Hinzufügen / Entfernen, wie in der Vorlage ---------------------------
    def _band_merken(self) -> None:
        """Die Änderung steht in den Einstellungen; das Band wird beim Verlassen der Seite neu gebaut (nicht bei jedem Klick)."""
        self._band_neu = True


    def _band_jetzt(self, *_a) -> None:
        if getattr(self, "_band_neu", False):
            self._band_neu = False
            QTimer.singleShot(0, self.w.neu_bauen_band)


    def hideEvent(self, ev):
        self._band_jetzt()
        super().hideEvent(ev)


class OptionenDialog(QDialog):
    """Die Optionen als eigenes Fenster (für Aufrufe außerhalb der Datei-Ansicht); gleicher Inhalt wie `OptionenAnsicht`."""

    def __init__(self, fenster, seite: str | None = None):
        super().__init__(fenster)
        self.setWindowTitle("Optionen")
        self.resize(1000, 680)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 8)
        self.ansicht = OptionenAnsicht(fenster, seite)
        self.baum, self.stapel, self.knoten, self.gehe_zu = self.ansicht.baum, self.ansicht.stapel, self.ansicht.knoten, self.ansicht.gehe_zu
        v.addWidget(self.ansicht, 1)
        v.addWidget(knopfzeile(self, ok_text="Fertig", nur_ok=True))
