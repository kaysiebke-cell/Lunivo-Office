"""Oberfläche anpassen: Register (Reiter) auswählen und ordnen, Schnellzugriff, Symbole austauschen, Oberfläche wählen."""
from __future__ import annotations

import json

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten import weitere_farben
from lunivo_writer.ui.widgets import icons
from lunivo_writer.ui.ribbon.plan import plan

IMMER = ("Datei",)          # dieser Reiter lässt sich nicht ausblenden


def lade_json(settings, key: str, standard):
    try:
        v = json.loads(settings.get(key, "") or "null")
        return standard if v is None else v
    except ValueError:
        return standard


class RegisterAnpassenDialog(QDialog):
    """Reiter ein-/ausblenden und umordnen — wie „Menüband anpassen“ in WPS."""

    def __init__(self, parent, settings, daten: dict):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Register anpassen")
        self.resize(420, 460)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Haken = Reiter wird gezeigt. Mit den Pfeilen ändern Sie die Reihenfolge."))
        self.liste = QListWidget()
        v.addWidget(self.liste)
        namen = [r["name"] for r in plan(daten) if not r.get("kontext")]
        cfg = lade_json(settings, "ui/register_plan", {})
        reihenfolge = [n for n in cfg.get("reihenfolge", []) if n in namen] + [n for n in namen if n not in cfg.get("reihenfolge", [])]
        from lunivo_writer.ui.ribbon.ribbon_bar import STANDARD_VERSTECKT
        versteckt = set(cfg["versteckt"] if "versteckt" in cfg else STANDARD_VERSTECKT)
        for n in reihenfolge:
            it = QListWidgetItem(n)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked if n in versteckt else Qt.Checked)
            if n in IMMER:
                it.setFlags(it.flags() & ~Qt.ItemIsUserCheckable)
            self.liste.addItem(it)
        z = QHBoxLayout()
        for text, d in (("▲ Nach oben", -1), ("▼ Nach unten", 1)):
            b = QPushButton(text); b.clicked.connect(lambda _=False, d=d: self._schieben(d)); z.addWidget(b)
        v.addLayout(z)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._speichern); bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _schieben(self, d: int):
        i = self.liste.currentRow(); j = i + d
        if i < 0 or not 0 <= j < self.liste.count():
            return
        it = self.liste.takeItem(i)
        self.liste.insertItem(j, it)
        self.liste.setCurrentRow(j)

    def _speichern(self):
        namen = [self.liste.item(i).text() for i in range(self.liste.count())]
        versteckt = [self.liste.item(i).text() for i in range(self.liste.count())
                     if self.liste.item(i).checkState() == Qt.Unchecked and self.liste.item(i).text() not in IMMER]
        self.settings.set("ui/register_plan", json.dumps({"reihenfolge": namen, "versteckt": versteckt}))
        self.accept()


class SchnellzugriffDialog(QDialog):
    """Welche Knöpfe in der Schnellzugriffsleiste neben dem ☰-Menü stehen."""

    def __init__(self, parent, settings, alle: list[tuple[str, str, str]], aktuell: list[str]):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Symbolleiste für den Schnellzugriff")
        self.resize(420, 480)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Haken = Knopf steht in der Schnellzugriffsleiste."))
        self.liste = QListWidget()
        v.addWidget(self.liste)
        for sym, name, aktion in alle:
            it = QListWidgetItem(icons.icon(sym, 18), name)
            it.setData(Qt.UserRole, aktion)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if aktion in aktuell else Qt.Unchecked)
            self.liste.addItem(it)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._speichern); bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _speichern(self):
        gewaehlt = [self.liste.item(i).data(Qt.UserRole) for i in range(self.liste.count())
                    if self.liste.item(i).checkState() == Qt.Checked]
        self.settings.set("ui/schnellzugriff", json.dumps(gewaehlt))
        self.accept()


class EigeneZeichnungDialog(QDialog):
    """„Eigene Zeichnung …“: eine SVG-Datei oder nur Pfaddaten hineinkopieren; die Vorschau zeichnet beim Tippen mit."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Eigene Zeichnung")
        self.wert: str | None = None
        v = QVBoxLayout(self)
        t = QLabel("Eigene Zeichnung"); f = t.font(); f.setBold(True); f.setPointSizeF(f.pointSizeF() + 2); t.setFont(f)
        v.addWidget(t)
        satz = QLabel("Eine SVG-Datei hier hineinkopieren — oder nur die Pfaddaten. Sie wird auf 24 × 24 gebracht und mittig eingepasst.")
        satz.setWordWrap(True); v.addWidget(satz)
        z = QHBoxLayout(); v.addLayout(z)
        self.feld = QPlainTextEdit(); self.feld.setPlaceholderText('<svg viewBox="0 0 24 24">…</svg>')
        self.feld.setMinimumSize(460, 170)
        z.addWidget(self.feld, 1)
        rechts = QVBoxLayout(); z.addLayout(rechts)
        self.bild = QLabel(); self.bild.setFixedSize(96, 96); self.bild.setAlignment(Qt.AlignCenter)
        self.bild.setStyleSheet("border: 1px solid palette(midlight); border-radius: 8px;")
        self.wort = QLabel("Noch nichts"); self.wort.setAlignment(Qt.AlignCenter); self.wort.setWordWrap(True); self.wort.setMaximumWidth(110)
        rechts.addWidget(self.bild); rechts.addWidget(self.wort); rechts.addStretch(1)
        self.gefuellt = QCheckBox("Gefüllt zeichnen (für Zeichnungen aus Flächen statt Strichen)")
        v.addWidget(self.gefuellt)
        zu = QHBoxLayout(); zu.addStretch(1)
        ab = QPushButton("Abbrechen"); ok = QPushButton("Übernehmen"); ok.setDefault(True)
        ab.clicked.connect(self.reject); ok.clicked.connect(self._ok)
        zu.addWidget(ab); zu.addWidget(ok)
        v.addLayout(zu)
        self.feld.textChanged.connect(self._schau); self.gefuellt.toggled.connect(self._schau)
        self._schau()

    def _schau(self) -> None:
        self.wert = icons.eigene_zeichnung(self.feld.toPlainText(), self.gefuellt.isChecked())
        if self.wert is None:
            self.bild.clear()
            self.wort.setText("Daraus wird keine Zeichnung." if self.feld.toPlainText().strip() else "Noch nichts")
            return
        farbe = self.palette().color(self.foregroundRole()).name()
        self.bild.setPixmap(QPixmap.fromImage(icons.pfad_bild(self.wert, 80, farbe)))
        self.wort.setText("So kommt sie in die Leiste.")

    def _ok(self) -> None:
        if self.wert is None:
            QMessageBox.information(self, "Eigene Zeichnung", "Daraus wird keine Zeichnung — steht wirklich eine SVG darin?")
            return
        self.accept()


class SymbolTauschenDialog(QDialog):
    """Ein Symbol austauschen — wie in der ersten Fassung: Getauscht wird die Zeichnung, nicht der Knopf; sie ändert sich überall,
    wo sie benutzt wird. Oben steht, wo das ist. Dazu Suche, 1800 Zeichnungen, eigene Zeichnung und Zurücksetzen."""
    GRENZE = 240
    SPALTEN = 7

    def __init__(self, parent, settings, name: str | None = None):
        super().__init__(parent)
        self.w, self.settings = parent, settings
        self.setWindowTitle("Symbol austauschen")
        self.setMinimumSize(520, 560)
        self.tausch = lade_json(settings, "ui/symbol_tausch", {})
        self._anfang = dict(self.tausch)
        self.geaendert = False
        namen = icons.pfade_original()
        self.welches = name if name in namen else next(iter(namen))
        v = QVBoxLayout(self)
        t = QLabel("Symbol austauschen"); f = t.font(); f.setBold(True); f.setPointSizeF(f.pointSizeF() + 2); t.setFont(f)
        v.addWidget(t)
        satz = QLabel("Getauscht wird die Zeichnung, nicht der Knopf — sie ändert sich überall, wo sie benutzt wird. Oben steht, wo das ist.")
        satz.setWordWrap(True); satz.setStyleSheet("color: palette(mid);"); v.addWidget(satz)
        kopf = QFrame(); kopf.setObjectName("tauschKopf")
        kopf.setStyleSheet("QFrame#tauschKopf { border: 1px solid palette(midlight); border-radius: 8px; }")
        kh = QHBoxLayout(kopf)
        self.jetzt = QLabel(); self.jetzt.setFixedSize(40, 40); self.jetzt.setAlignment(Qt.AlignCenter)
        self.wo = QLabel(); self.wo.setWordWrap(True)
        kh.addWidget(self.jetzt); kh.addWidget(self.wo, 1)
        v.addWidget(kopf)
        self.suche = QLineEdit(); self.suche.setClearButtonEnabled(True)
        self.suche.setPlaceholderText("Zeichnung suchen … (englisch: table, clock, save)")
        v.addWidget(self.suche)
        sc = QScrollArea(); sc.setWidgetResizable(True)
        self.gitter_halter = QWidget(); self.gitter = QGridLayout(self.gitter_halter)
        self.gitter.setSpacing(4); self.gitter.setAlignment(Qt.AlignTop)
        sc.setWidget(self.gitter_halter)
        v.addWidget(sc, 1)
        fuss = QHBoxLayout(); v.addLayout(fuss)
        self.b_eigene = QPushButton("Eigene Zeichnung …"); self.b_dieses = QPushButton("Dieses zurücksetzen"); self.b_alle = QPushButton("Alle zurücksetzen")
        for b in (self.b_eigene, self.b_dieses, self.b_alle):
            fuss.addWidget(b)
        fuss.addStretch(1)
        self.meldung = QLabel(); self.meldung.setStyleSheet("color: palette(mid);"); v.addWidget(self.meldung)
        zu = QHBoxLayout(); zu.addStretch(1)
        ab = QPushButton("Abbrechen"); fertig = QPushButton("Fertig"); fertig.setDefault(True)
        ab.clicked.connect(self._abbrechen); fertig.clicked.connect(self.accept)
        zu.addWidget(ab); zu.addWidget(fertig)
        v.addLayout(zu)
        self.suche.textChanged.connect(self._gitter_zeigen)
        self.b_eigene.clicked.connect(self._eigene)
        self.b_dieses.clicked.connect(self._dieses_zurueck)
        self.b_alle.clicked.connect(self._alle_zurueck)
        self._kopf_zeigen()
        self._gitter_zeigen()

    # ---- Kopf: welches Symbol, und wo es steht --------------------------------------------------------------------
    def _befehle(self) -> list[str]:
        namen: list[str] = []
        try:
            for r in plan(self.w.band.daten):
                for g in r.get("gruppen", []):
                    for k in g.get("knoepfe", []):
                        if k.get("symbol") == self.welches and k.get("name") and k["name"] not in namen:
                            namen.append(k["name"])
        except Exception:
            pass
        return namen

    def _kopf_zeigen(self) -> None:
        self.jetzt.setPixmap(icons.icon(self.welches, 32).pixmap(32, 32))
        b = self._befehle()
        self.wo.setText((", ".join(b[:4]) + (" und weitere" if len(b) > 4 else "")) if b else "Wird zurzeit nirgends im Register benutzt.")
        self.b_dieses.setEnabled(self.welches in self.tausch)

    # ---- Auswahl --------------------------------------------------------------------------------------------------
    def _gitter_zeigen(self) -> None:
        while self.gitter.count():
            it = self.gitter.takeAt(0)
            if it.widget():
                it.widget().hide(); it.widget().setParent(None); it.widget().deleteLater()
        wort = self.suche.text().strip().lower()
        gezeigt = gefunden = 0
        farbe = self.palette().color(self.foregroundRole()).name()
        for n, pfad in icons.katalog().items():
            if wort and wort not in n.lower():
                continue
            gefunden += 1
            if gezeigt >= self.GRENZE:
                continue
            k = QToolButton(); k.setFixedSize(52, 52); k.setToolTip(n); k.setAutoRaise(True)
            k.setIcon(QIcon(QPixmap.fromImage(icons.pfad_bild(pfad, 56, farbe)))); k.setIconSize(QSize(28, 28))
            k.clicked.connect(lambda _=False, n=n: self._waehle(n))
            self.gitter.addWidget(k, gezeigt // self.SPALTEN, gezeigt % self.SPALTEN)
            gezeigt += 1
        if not gefunden:
            self.gitter.addWidget(QLabel("Keine Zeichnung mit diesem Namen."), 0, 0, 1, self.SPALTEN)
        elif gefunden > self.GRENZE:
            self.gitter.addWidget(QLabel(f"{gefunden} gefunden, {self.GRENZE} gezeigt — die Suche genauer machen."),
                                  gezeigt // self.SPALTEN + 1, 0, 1, self.SPALTEN)

    # ---- Wirkung --------------------------------------------------------------------------------------------------
    def _anwenden(self, meldung: str) -> None:
        self.settings.set("ui/symbol_tausch", json.dumps(self.tausch))
        icons.uebersteuern(self.tausch)
        self.geaendert = True
        self._kopf_zeigen()
        self.meldung.setText(meldung)

    def _waehle(self, katalogname: str) -> None:
        self.tausch[self.welches] = katalogname
        self._anwenden(f"Symbol getauscht: {katalogname}.")

    def _eigene(self) -> None:
        d = EigeneZeichnungDialog(self)
        if d.exec() and d.wert:
            self.tausch[self.welches] = d.wert
            self._anwenden("Eigene Zeichnung übernommen.")

    def _dieses_zurueck(self) -> None:
        self.tausch.pop(self.welches, None)
        self._anwenden("Zurückgesetzt.")

    def _alle_zurueck(self) -> None:
        self.tausch = {}
        self._anwenden("Alle Symbole wieder wie ausgeliefert.")

    def _abbrechen(self) -> None:
        """Abbrechen nimmt zurück, was in diesem Fenster getauscht wurde."""
        if self.tausch != self._anfang:
            self.tausch = dict(self._anfang)
            self.settings.set("ui/symbol_tausch", json.dumps(self.tausch))
            icons.uebersteuern(self.tausch)
            self.geaendert = True
        self.reject()


class OberflaecheDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowTitle("Benutzeroberfläche")
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Wie sollen die Befehle angeordnet sein?"))
        self.reg = QRadioButton("Register (Menüband mit Reitern, wie in WPS Office)")
        self.sym = QRadioButton("Symbolleisten (zwei Zeilen mit Knöpfen)")
        (self.sym if settings.get("ui/oberflaeche", "register") == "symbolleisten" else self.reg).setChecked(True)
        v.addWidget(self.reg); v.addWidget(self.sym)
        self.menue = QCheckBox("Menüleiste zusätzlich anzeigen")
        self.menue.setChecked(settings.get_bool("ui/menueleiste", False))
        v.addWidget(self.menue)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)

    def wahl(self) -> str:
        return "symbolleisten" if self.sym.isChecked() else "register"


class StileVerwaltenDialog(QDialog):
    """Start ▸ Stile ▸ Formatvorlagen verwalten: ändern, wie eine Vorlage aussieht — wirkt auf jeden Absatz, der sie trägt."""

    def __init__(self, parent, speichern, anwenden, auswahl=None, entfernen=None, aktualisiert=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QFontComboBox, QFormLayout
        from lunivo_writer.editor import stile
        self.stile = stile
        self._speichern = speichern
        self._anwenden = anwenden
        self._auswahl, self._entfernen, self._aktualisiert = auswahl, entfernen, aktualisiert
        self._farbe = ""
        self.setWindowTitle("Formatvorlagen verwalten")
        self.resize(640, 420)
        h = QHBoxLayout(self)
        self.liste = QListWidget(); self.liste.setFixedWidth(170)
        for n in stile.namen():
            self.liste.addItem(n)
        h.addWidget(self.liste)
        rechts = QVBoxLayout(); h.addLayout(rechts, 1)
        f = QFormLayout(); rechts.addLayout(f)
        self.groesse = QDoubleSpinBox(); self.groesse.setRange(0, 200); self.groesse.setSpecialValueText("wie das Dokument"); self.groesse.setSuffix(" pt")
        self.fett = QCheckBox("Fett"); self.kursiv = QCheckBox("Kursiv")
        self.schrift = QFontComboBox(); self.schrift.setEditable(False)
        self.eigene_schrift = QCheckBox("Eigene Schriftart:")
        self.farbe = QPushButton("Automatisch"); self.farbe.clicked.connect(self._farbe_waehlen)
        self.vor = QDoubleSpinBox(); self.vor.setRange(0, 100); self.vor.setSuffix(" pt")
        self.nach = QDoubleSpinBox(); self.nach.setRange(0, 100); self.nach.setSuffix(" pt")
        self.ausr = QComboBox(); self.ausr.addItems(["wie bisher", "Links", "Zentriert", "Rechts", "Blocksatz"])
        f.addRow("Größe", self.groesse); f.addRow(self.fett); f.addRow(self.kursiv)
        f.addRow(self.eigene_schrift, self.schrift); f.addRow("Schriftfarbe", self.farbe)
        f.addRow("Abstand davor", self.vor); f.addRow("Abstand danach", self.nach); f.addRow("Ausrichtung", self.ausr)
        self.vorschau = QLabel("AaBbCc Beispieltext"); self.vorschau.setMinimumHeight(60)
        self.vorschau.setStyleSheet("background: white; color: black; border: 1px solid #adb5bd; padding: 6px;")
        rechts.addWidget(self.vorschau)
        z = QHBoxLayout()
        for text, fn in (("Übernehmen", self._uebernehmen), ("Diese Vorlage zurücksetzen", self._zurueck), ("Alle zurücksetzen", self._alle_zurueck)):
            b = QPushButton(text); b.clicked.connect(fn); z.addWidget(b)
        rechts.addLayout(z)
        z2 = QHBoxLayout()
        self.neu_knopf = QPushButton("Neue Vorlage aus der Auswahl …"); self.neu_knopf.clicked.connect(self._neu)
        self.neu_knopf.setEnabled(auswahl is not None)
        self.weg_knopf = QPushButton("Eigene Vorlage löschen"); self.weg_knopf.clicked.connect(self._weg)
        z2.addWidget(self.neu_knopf); z2.addWidget(self.weg_knopf)
        rechts.addLayout(z2)
        bb = QDialogButtonBox(QDialogButtonBox.Close); bb.rejected.connect(self.accept); rechts.addWidget(bb)
        self.liste.currentTextChanged.connect(self._lade)
        self.liste.setCurrentRow(0)
        for w in (self.groesse, self.vor, self.nach):
            w.valueChanged.connect(self._zeige)
        for w in (self.fett, self.kursiv, self.eigene_schrift):
            w.toggled.connect(self._zeige)
        self.schrift.currentFontChanged.connect(self._zeige)

    def _lade(self, name):
        if not name:
            return
        eigen = self.stile.ist_eigen(name)
        self.weg_knopf.setEnabled(eigen)
        d = self.stile.definition(name)
        self.groesse.setValue(d["groesse"]); self.fett.setChecked(d["fett"]); self.kursiv.setChecked(d["kursiv"])
        self.eigene_schrift.setChecked(bool(d["schrift"]))
        if d["schrift"]:
            self.schrift.setCurrentFont(__import__("PySide6.QtGui", fromlist=["QFont"]).QFont(d["schrift"]))
        self._farbe = d["farbe"]
        self.farbe.setText(self._farbe or "Automatisch")
        self.vor.setValue(d["vor"]); self.nach.setValue(d["nach"])
        self.ausr.setCurrentIndex({"": 0, "links": 1, "mitte": 2, "rechts": 3, "block": 4}[d["ausr"]])
        self._zeige()

    def _farbe_waehlen(self):
        c = weitere_farben(self, Qt.black, "Schriftfarbe")
        if c is not None:
            self._farbe = c.name(); self.farbe.setText(self._farbe); self._zeige()

    def _zeige(self, *_):
        from PySide6.QtGui import QFont
        f = QFont(self.schrift.currentFont().family() if self.eigene_schrift.isChecked() else self.font().family())
        f.setPointSizeF(self.groesse.value() or 11); f.setBold(self.fett.isChecked()); f.setItalic(self.kursiv.isChecked())
        self.vorschau.setFont(f)
        self.vorschau.setStyleSheet(f"background: white; color: {self._farbe or 'black'}; border: 1px solid #adb5bd; padding: 6px;")

    def _uebernehmen(self):
        n = self.liste.currentItem().text()
        self.stile.aendern(n, groesse=self.groesse.value(), fett=self.fett.isChecked(), kursiv=self.kursiv.isChecked(),
                           schrift=self.schrift.currentFont().family() if self.eigene_schrift.isChecked() else "",
                           farbe=self._farbe, vor=self.vor.value(), nach=self.nach.value(),
                           ausr=["", "links", "mitte", "rechts", "block"][self.ausr.currentIndex()])
        self._speichern()
        self._anwenden(n)

    def _neu(self):
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(self, "Neue Formatvorlage", "Name der Vorlage (sie übernimmt Schrift und Absatzformat des Absatzes, in dem die Schreibmarke steht):")
        if not ok:
            return
        grund = self.stile.anlegen(name, **self._auswahl())
        if grund:
            QMessageBox.warning(self, "Neue Formatvorlage", grund)
            return
        name = " ".join(name.split())
        self._speichern()
        self.liste.addItem(name)
        self.liste.setCurrentRow(self.liste.count() - 1)
        if self._aktualisiert:
            self._aktualisiert()

    def _weg(self):
        from PySide6.QtWidgets import QMessageBox
        n = self.liste.currentItem().text()
        if not self.stile.ist_eigen(n):
            return
        if QMessageBox.question(self, "Formatvorlage löschen", f"„{n}“ löschen? Absätze behalten ihr Aussehen, gelten aber wieder als „Standard“.") != QMessageBox.Yes:
            return
        if self._entfernen:
            self._entfernen(n)
        self.stile.loeschen(n)
        self._speichern()
        self.liste.takeItem(self.liste.currentRow())
        if self._aktualisiert:
            self._aktualisiert()

    def _zurueck(self):
        n = self.liste.currentItem().text()
        if self.stile.ist_eigen(n):
            return
        self.stile.zuruecksetzen(n); self._speichern(); self._lade(n); self._anwenden(n)

    def _alle_zurueck(self):
        self.stile.zuruecksetzen(); self._speichern()
        for n in self.stile.NAMEN:
            self._anwenden(n)
        self._lade(self.liste.currentItem().text())
