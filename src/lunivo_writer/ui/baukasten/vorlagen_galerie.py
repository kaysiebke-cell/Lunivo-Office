"""Die Seite „Neu“: alle Vorlagen als Blätter mit kleiner Vorschau, darüber Reiter (Alle · Mitgeliefert · Meine Vorlagen) und ein Suchfeld.

    g = VorlagenGalerie(settings, kann_speichern=True)
    g.gewaehlt.connect(lambda art, wert: ...)      # art: "leer" | "geruest" (wert = Muster) | "datei" (wert = Pfad)
    g.als_vorlage.connect(...)                     # „Dieses Dokument als Vorlage behalten …“

Die Vorschauen entstehen nach und nach (ein Blatt je Takt), damit die Seite sofort da ist; fertige bleiben im Speicher.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QTabBar, QFileDialog, QFrame, QGridLayout, QInputDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QToolButton, QVBoxLayout,
                               QWidget)

from lunivo_writer.editor import vorlagen
from lunivo_writer.ui.widgets import icons

KACHEL = QSize(186, 243)
_VORSCHAU: dict[tuple, QPixmap] = {}                     # (Art, Schlüssel, Änderungszeit) → Bild, solange das Programm läuft


def _blatt_bild(doc, page) -> QPixmap:
    """Erste Seite eines Dokuments, auf Kachelbreite verkleinert."""
    from lunivo_writer.editor.pagination import seite_als_bild
    img = seite_als_bild(doc, page, 1, 0.8)
    return QPixmap.fromImage(img.scaled(KACHEL, Qt.KeepAspectRatio, Qt.SmoothTransformation))


def _geruest_bild(muster: dict, benutzer: dict) -> QPixmap:
    from PySide6.QtCore import QDate, QLocale
    from PySide6.QtWidgets import QTextEdit
    from lunivo_writer.models.page import PageSettings
    ed = QTextEdit()
    vorlagen.aufbauen(ed, muster["zeilen"], benutzer, QLocale("de_DE").toString(QDate.currentDate(), "d. MMMM yyyy"))
    from PySide6.QtGui import QBrush, QTextCharFormat, QTextCursor
    c = QTextCursor(ed.document()); c.select(QTextCursor.Document)
    f = QTextCharFormat(); f.setForeground(QBrush(QColor("#000000"))); f.setBackground(QBrush(Qt.NoBrush))
    c.mergeCharFormat(f)                                      # in der Vorschau sind die Lücken schlichter Text: lesbar, ohne Farbe und Gelb
    return _blatt_bild(ed.document(), PageSettings())


def _datei_bild(pfad: str) -> QPixmap:
    from lunivo_writer.services import file_service as formats
    g = formats.load(pfad)
    return _blatt_bild(g.doc, g.page)


class _Kachel(QToolButton):
    """Ein Blatt mit Name darunter; eine Rubrik zeigt zusätzlich ein Ordnerzeichen mit der Zahl ihrer Vorlagen."""

    def __init__(self, name: str, art: str, wert, schluessel: tuple, anzahl: int = 0):
        super().__init__()
        self.name, self.art, self.wert, self.schluessel, self.anzahl = name, art, wert, schluessel, anzahl
        self.gruppe = "geruest"
        self.setText(name); self.setToolTip(name)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon); self.setAutoRaise(True); self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(KACHEL); self.setFixedSize(KACHEL.width() + 12, KACHEL.height() + 44)
        self.setIcon(QIcon(self._platzhalter(art == "leer")))

    def _platzhalter(self, symbol: bool = False) -> QPixmap:
        pm = QPixmap(KACHEL); pm.fill(QColor("white"))
        if symbol:
            p = QPainter(pm); ic = icons.icon("neu", 56).pixmap(56, 56)
            p.setOpacity(0.35); p.drawPixmap((KACHEL.width() - 56) // 2, (KACHEL.height() - 56) // 2, ic); p.end()
        return pm

    def bild_setzen(self, pm: QPixmap) -> None:
        if self.art == "rubrik":
            pm = self._mit_ordnerzeichen(pm)
        self.setIcon(QIcon(pm))

    def _mit_ordnerzeichen(self, pm: QPixmap) -> QPixmap:
        """Eine Rubrik: das erste Blatt, dahinter angedeutet weitere, vorn ein Schild mit der Zahl."""
        out = QPixmap(KACHEL); out.fill(Qt.transparent)
        p = QPainter(out); p.setRenderHint(QPainter.Antialiasing)
        w, h = pm.width(), pm.height()
        vorn = pm.scaled(w - 16, h - 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        for dx, dy in ((16, 0), (8, 8)):                             # zwei Blätter dahinter, nur an der Kante zu sehen
            p.setPen(QColor("#adb5bd")); p.setBrush(QColor("#f1f3f5")); p.drawRect(dx, dy, vorn.width() - 1, vorn.height() - 1)
        p.drawPixmap(0, 16, vorn)
        p.setBrush(QColor(0, 0, 0, 190)); p.setPen(Qt.NoPen); p.drawRoundedRect(6, KACHEL.height() - 34, 58, 26, 6, 6)
        p.setPen(QColor("white")); p.drawText(6, KACHEL.height() - 34, 58, 26, Qt.AlignCenter, f"▣ {self.anzahl}")
        p.end()
        return out


class VorlagenGalerie(QWidget):
    gewaehlt = Signal(str, object)
    als_vorlage = Signal(str)                                 # Zielordner („“ = Vorlagenordner selbst)

    def __init__(self, settings, kann_speichern: bool, benutzer: dict | None = None, parent=None):
        super().__init__(parent)
        self.settings, self._benutzer = settings, benutzer or {}
        self._reiter, self._rubrik = "alle", None
        self._offen: list[_Kachel] = []
        v = QVBoxLayout(self); v.setContentsMargins(36, 28, 36, 0); v.setSpacing(10)
        kopf = QHBoxLayout(); kopf.setSpacing(10)
        self.zurueck = QPushButton("←  Neu"); self.zurueck.setFlat(True); self.zurueck.setCursor(Qt.PointingHandCursor)
        self.zurueck.clicked.connect(lambda: self.rubrik_oeffnen(None)); kopf.addWidget(self.zurueck)
        self.titel = QLabel("Neu"); f = self.titel.font(); f.setPointSizeF(f.pointSizeF() + 8); f.setBold(True); self.titel.setFont(f)
        kopf.addWidget(self.titel); kopf.addStretch(1)
        self.neue_rubrik = QPushButton("Neue Rubrik …"); self.neue_rubrik.clicked.connect(self._rubrik_anlegen); kopf.addWidget(self.neue_rubrik)
        v.addLayout(kopf)
        self.reiter_w = QTabBar(); self.reiter_w.setObjectName("bandReiter")            # dieselbe Gestalt wie die Register des Bandes
        self.reiter_w.setDrawBase(False); self.reiter_w.setExpanding(False); self.reiter_w.setCursor(Qt.PointingHandCursor)
        self.reiter_w.setFocusPolicy(Qt.NoFocus)
        self._schluessel = ("alle", "geruest", "eigene")
        for text in ("Alle", "Mitgeliefert", "Meine Vorlagen"):
            self.reiter_w.addTab(text)
        self.reiter_w.currentChanged.connect(lambda i: self._reiter_setzen(self._schluessel[i]))
        v.addWidget(self.reiter_w, 0, Qt.AlignLeft)
        linie = QFrame(); linie.setFrameShape(QFrame.HLine); linie.setFrameShadow(QFrame.Sunken); v.addWidget(linie)
        self.suche = QLineEdit(); self.suche.setPlaceholderText("Vorlage suchen"); self.suche.setClearButtonEnabled(True)
        self.suche.setFixedWidth(420); self.suche.setMinimumHeight(34); self.suche.textChanged.connect(self._anordnen)
        v.addWidget(self.suche)
        self.flaeche = QScrollArea(); self.flaeche.setWidgetResizable(True); self.flaeche.setFrameShape(QFrame.NoFrame)
        self.raster_w = QWidget(); self.raster = QGridLayout(self.raster_w); self.raster.setSpacing(18)
        self.raster.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.flaeche.setWidget(self.raster_w); v.addWidget(self.flaeche, 1)
        self.leer = QLabel(); self.leer.setWordWrap(True); self.leer.setStyleSheet("color: palette(mid);"); v.addWidget(self.leer)

        fuss = QHBoxLayout(); fuss.setContentsMargins(0, 8, 0, 12)
        hin = QLabel("Geöffnet wird immer eine Abschrift. Die Vorlage selbst bleibt, wie sie ist — auch nach dem dritten Brief.")
        hin.setStyleSheet("color: palette(mid);"); hin.setWordWrap(True); hin.setMinimumWidth(120); fuss.addWidget(hin, 1)   # darf umbrechen, sonst wird das Fenster breiter als der Schirm
        self.speichern = QPushButton("Dieses Dokument als Vorlage behalten …"); self.speichern.setEnabled(kann_speichern)
        self.speichern.clicked.connect(lambda: self.als_vorlage.emit(self._ziel()))
        waehlen = QPushButton("Vorlagenordner wählen …"); waehlen.clicked.connect(self._ordner_waehlen)
        oeffnen = QPushButton("Vorlagenordner öffnen"); oeffnen.clicked.connect(self._ordner_oeffnen)
        for k in (self.speichern, waehlen, oeffnen):
            k.setMinimumHeight(32); fuss.addWidget(k)
        v.addLayout(fuss)

        self._kacheln: list[_Kachel] = []
        self._timer = QTimer(self); self._timer.setInterval(15); self._timer.timeout.connect(self._naechstes_bild)
        self._daten_lesen()
        self._bauen()
        self._reiter_setzen("alle")

    # ---- Daten: Rubriken aus Gerüsten und Unterordnern ---------------------------------------------------------------------
    def _daten_lesen(self) -> None:
        self.ordner = vorlagen.vorlagenordner(self.settings)
        self.rubriken: dict[str, dict] = {}
        for m in vorlagen.muster():
            r = self.rubriken.setdefault(m.get("rubrik") or m["name"], {"geruest": [], "dateien": [], "pfad": None})
            r["geruest"].append(m)
        unter, self.lose = vorlagen.rubriken(self.ordner)
        for name, dateien in unter.items():
            gleich = next((n for n in self.rubriken if n.lower() == name.lower()), name)
            r = self.rubriken.setdefault(gleich, {"geruest": [], "dateien": [], "pfad": None})
            r["dateien"] += dateien; r["pfad"] = os.path.join(self.ordner, name)

    def _ziel(self) -> str:
        """Wohin „Dieses Dokument als Vorlage behalten“ ablegt: in die geöffnete Rubrik, sonst in den Vorlagenordner."""
        if self._rubrik is None:
            return ""
        r = self.rubriken.get(self._rubrik, {})
        return r.get("pfad") or os.path.join(self.ordner, self._rubrik)

    def _stempel(self, p: str) -> float:
        try:
            return os.path.getmtime(p)
        except OSError:
            return 0

    def _datei_kachel(self, p: str, gruppe: str = "eigene") -> _Kachel:
        k = _Kachel(os.path.splitext(os.path.basename(p))[0], "datei", p, ("datei", p, self._stempel(p)))
        k.gruppe = gruppe; k.clicked.connect(lambda _=False, p=p: self.gewaehlt.emit("datei", p))
        return k

    def _geruest_kachel(self, m: dict) -> _Kachel:
        k = _Kachel(m["name"], "geruest", m, ("geruest", m["name"]))
        k.clicked.connect(lambda _=False, m=m: self.gewaehlt.emit("geruest", m))
        return k

    def _bauen(self) -> None:
        for k in self._kacheln:
            k.deleteLater()
        self._kacheln = []
        self.suche_alle: list[_Kachel] = []                 # alle Vorlagen flach (für die Suche)
        leer = _Kachel("Leeres Dokument", "leer", None, ("leer",)); leer.clicked.connect(lambda: self.gewaehlt.emit("leer", None))
        self._kacheln.append(leer)
        n_g = n_e = 0
        for name, r in self.rubriken.items():
            n = len(r["geruest"]) + len(r["dateien"])
            k = _Kachel(name, "rubrik", name, ("rubrik", name, n, tuple(self._stempel(p) for p in r["dateien"])), n)
            k.gruppe = "gemischt" if r["geruest"] and r["dateien"] else ("geruest" if r["geruest"] else "eigene")
            k.clicked.connect(lambda _=False, n=name: self.rubrik_oeffnen(n))
            k.setToolTip(f"{name} — {n} Vorlage{'n' if n != 1 else ''}")
            self._kacheln.append(k)
            n_g += bool(r["geruest"]); n_e += bool(r["dateien"])
            r["kacheln"] = [self._geruest_kachel(m) for m in r["geruest"]] + [self._datei_kachel(p) for p in r["dateien"]]
            self.suche_alle += r["kacheln"]
        for p in self.lose:
            k = self._datei_kachel(p); self._kacheln.append(k); self.suche_alle.append(k); n_e += 1
        for i, text in enumerate((f"Alle  {len(self.rubriken) + len(self.lose) + 1}", f"Mitgeliefert  {n_g}", f"Meine Vorlagen  {n_e}")):
            self.reiter_w.setTabText(i, text)
        self._offen = [k for k in self._kacheln + self.suche_alle if k.art != "leer"]
        self._timer.start()

    def _naechstes_bild(self) -> None:
        while self._offen:
            k = self._offen.pop(0)
            try:
                if k.art == "rubrik":
                    r = self.rubriken.get(k.wert); erste = r["kacheln"][0] if r and r.get("kacheln") else None
                    if erste is None:
                        continue
                    pm = _VORSCHAU.get(erste.schluessel)
                    if pm is None:
                        pm = self._bild_fuer(erste); _VORSCHAU[erste.schluessel] = pm
                    k.bild_setzen(pm)
                    continue
                if k.schluessel not in _VORSCHAU:
                    _VORSCHAU[k.schluessel] = self._bild_fuer(k)
                    k.bild_setzen(_VORSCHAU[k.schluessel])
                    return
                k.bild_setzen(_VORSCHAU[k.schluessel])
            except Exception:                                     # eine Datei, die sich nicht lesen lässt, bleibt ein leeres Blatt
                continue
        self._timer.stop()

    def _bild_fuer(self, k: _Kachel) -> QPixmap:
        return _geruest_bild(k.wert, self._benutzer) if k.art == "geruest" else _datei_bild(k.wert)

    # ---- Anzeige ---------------------------------------------------------------------------------------------------
    def rubrik_oeffnen(self, name: str | None) -> None:
        self._rubrik = name
        self.suche.clear()
        self._anordnen()
        if name is not None:
            self._offen = [k for k in self.rubriken.get(name, {}).get("kacheln", []) if k.schluessel not in _VORSCHAU]
            self._timer.start()

    def _reiter_setzen(self, schl: str) -> None:
        self._reiter = schl
        i = self._schluessel.index(schl)
        if self.reiter_w.currentIndex() != i:
            self.reiter_w.setCurrentIndex(i)
            return                                                    # currentChanged ruft uns noch einmal auf
        self._anordnen()

    def _sichtbar(self) -> list[_Kachel]:
        text = self.suche.text().strip().lower()
        if self._rubrik is not None:
            return [k for k in self.rubriken.get(self._rubrik, {}).get("kacheln", []) if text in k.name.lower()]
        if text:                                                  # Suche im Überblick: alle Vorlagen, auch die in Rubriken
            return [k for k in self.suche_alle if text in k.name.lower()]
        wahl = {"alle": ("geruest", "eigene", "gemischt"), "geruest": ("geruest", "gemischt"), "eigene": ("eigene", "gemischt")}[self._reiter]
        return [k for k in self._kacheln if (k.art == "leer" and self._reiter == "alle") or (k.art != "leer" and k.gruppe in wahl)]

    def _anordnen(self, *_a) -> None:
        sicht = self._sichtbar()
        while self.raster.count():
            self.raster.takeAt(0)
        alle = self._kacheln + self.suche_alle
        for k in alle:
            k.setVisible(k in sicht)
        spalten = max(1, (max(self.width(), 600) - 100) // (KACHEL.width() + 30))
        for i, k in enumerate(sicht):
            self.raster.addWidget(k, i // spalten, i % spalten)
        in_rubrik = self._rubrik is not None
        self.zurueck.setVisible(in_rubrik); self.reiter_w.setVisible(not in_rubrik and not self.suche.text().strip())
        self.neue_rubrik.setVisible(not in_rubrik)
        self.titel.setText(self._rubrik if in_rubrik else "Neu")
        if sicht:
            self.leer.clear()
        elif in_rubrik:
            self.leer.setText(f"In „{self._rubrik}“ liegt noch nichts. Lege Dokumente in den Ordner {self._ziel()} (.docx, .dotx, .odt oder .txt) "
                              "— oder nimm „Dieses Dokument als Vorlage behalten …“.")
        elif self._reiter == "eigene" and not self.suche.text().strip():
            self.leer.setText(f"Der Ordner {self.ordner} enthält noch keine Vorlagen. Lege dort Dokumente ab, oder in Unterordnern als Rubriken "
                              "(zum Beispiel „Lebenslauf“) — oder nimm „Dieses Dokument als Vorlage behalten …“.")
        else:
            self.leer.setText("Nichts gefunden.")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._anordnen()

    # ---- Ordner ----------------------------------------------------------------------------------------------------
    def _rubrik_anlegen(self) -> None:
        name, ok = QInputDialog.getText(self, "Neue Rubrik", "Name der Rubrik (zum Beispiel „Lebenslauf“):")
        name = name.strip().replace("/", "-").replace("\\", "-") if ok else ""
        if not name or name.startswith("."):
            return
        os.makedirs(os.path.join(self.ordner, name), exist_ok=True)
        self.neu_lesen(); self.rubrik_oeffnen(next((n for n in self.rubriken if n.lower() == name.lower()), name))

    def _ordner_waehlen(self) -> None:
        p = QFileDialog.getExistingDirectory(self, "Vorlagenordner", vorlagen.vorlagenordner(self.settings))
        if p:
            self.settings.set("vorlagen/ordner", p); self.neu_lesen()

    def _ordner_oeffnen(self) -> None:
        o = self._ziel() or vorlagen.vorlagenordner(self.settings)
        os.makedirs(o, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(o))

    def neu_lesen(self) -> None:
        """Der Ordner wird bei jedem Öffnen der Seite neu gelesen."""
        gemerkt = self._rubrik
        self._daten_lesen(); self._bauen()
        self._rubrik = gemerkt if gemerkt in self.rubriken else None
        self._anordnen()
