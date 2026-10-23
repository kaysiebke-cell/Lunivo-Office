"""KI-Konfiguration: Aufgaben-Modellzuweisung, Liste der KI-Modelle, „Eigenen Anbieter hinzufügen“.

Der Anbieter wird hier festgelegt — in „KI-Konfiguration“ (Reiter Schreibhilfe/KI) oder in den Optionen.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.ai import ki as K
from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
from lunivo_writer.ui.baukasten.dialog_rahmen import knopfzeile
from lunivo_writer.ui.widgets.flow_layout import FlowLayout


from lunivo_writer.core.farben import Farbe
def _tags_text(a: dict) -> str:
    n = dict(K.ANBIETER_TAGS)
    return ", ".join(n[t] for t in a.get("verwendungFuer", []) if t in n)


class _Antwort(QObject):
    da = Signal(object)


class AnbieterDialog(QDialog):
    """Neuer oder zu bearbeitender Anbieter: Name, Vorlage, URL, Schlüssel, Modell (Liste vom Anbieter), Fähigkeiten."""

    def __init__(self, fenster, konfig: K.KIKonfig, bestehend: dict | None = None):
        super().__init__(fenster)
        self.k, self.alt = konfig, bestehend
        self.setWindowTitle("Modell bearbeiten" if bestehend else "Eigenen Anbieter hinzufügen")
        self.setMinimumWidth(560)
        v = QVBoxLayout(self)
        t = self._titel = text_label(self.windowTitle(), fett=True, pt=13, umbruch=False)
        v.addWidget(t)
        f = QFormLayout()
        self.name = QLineEdit(bestehend["name"] if bestehend else "")
        self.name.setPlaceholderText("Modellname")
        f.addRow("Modellname *", self.name)
        h = QLabel("Oben den Anbieter wählen — die URL füllt sich von selbst und lässt sich danach noch ändern. "
                   "Nur bei „Andere“ bleibt sie leer und will von Hand eingetragen werden.")
        h.setWordWrap(True)
        h.setStyleSheet("color: palette(mid);")
        f.addRow(h)
        self.vorlage = QComboBox()
        for key, name, url in K.ANBIETER_VORLAGEN:
            self.vorlage.addItem(name, url)
        self.url = QLineEdit(bestehend["url"] if bestehend else "")
        self.url.setPlaceholderText("https://…/v1")
        self.schluessel = QLineEdit(bestehend["schluessel"] if bestehend else "")
        self.schluessel.setEchoMode(QLineEdit.Password)
        self.schluessel.setPlaceholderText("Nicht erforderlich")
        f.addRow("Anbieter *", self.vorlage)
        f.addRow("URL *", self.url)
        f.addRow("Schlüssel", self.schluessel)
        self.modell = QComboBox()
        self.modell.setEditable(True)
        self.modell.setInsertPolicy(QComboBox.NoInsert)
        self.modell.lineEdit().setPlaceholderText("z. B. gpt-4o-mini")
        self.modell.setCurrentText(bestehend["modell"] if bestehend else "")
        self.stand = QLabel("")
        self.stand.setStyleSheet("color: palette(mid);")
        holen = QPushButton("Liste der Modelle aktualisieren")
        holen.setFlat(True)
        holen.setCursor(Qt.PointingHandCursor)
        holen.clicked.connect(lambda: self._holen(False))
        box = QVBoxLayout()
        box.addWidget(self.modell)
        z = QHBoxLayout()
        z.addWidget(holen)
        z.addWidget(self.stand, 1)
        box.addLayout(z)
        w = QWidget()
        w.setLayout(box)
        box.setContentsMargins(0, 0, 0, 0)
        f.addRow("Modell *", w)
        v.addLayout(f)
        v.addWidget(QLabel("Modell verwenden für"))
        fl = QWidget()
        self._chipgitter = QGridLayout(fl); self._chipgitter.setContentsMargins(0, 0, 0, 0); self._chipgitter.setSpacing(6)
        self.tags = {}
        gesetzt = set(bestehend["verwendungFuer"]) if bestehend else {"text"}
        alle = QPushButton("Alle")
        alle.setCheckable(True)
        alle.setStyleSheet(_CHIP)
        alle.toggled.connect(lambda an: [b.setChecked(an) for b in self.tags.values()])
        self._chips = [alle]
        for key, name in K.ANBIETER_TAGS:
            b = QPushButton(name)
            b.setCheckable(True)
            b.setChecked(key in gesetzt)
            b.setStyleSheet(_CHIP)
            self.tags[key] = b
            self._chips.append(b)
        self._chips_legen(3)
        from PySide6.QtWidgets import QSizePolicy
        fl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        v.addWidget(fl)
        z = knopfzeile(self, bei_ok=self._ok, ok_text="Speichern" if bestehend else "Hinzufügen")
        self.ok = z.ok
        v.addWidget(z)
        self._antwort = _Antwort()
        self._antwort.da.connect(self._geholt)
        self.vorlage.currentIndexChanged.connect(self._vorlage_gewaehlt)
        if bestehend:
            i = next((i for i in range(self.vorlage.count()) if self.vorlage.itemData(i) == bestehend["url"]), 0)
            self.vorlage.blockSignals(True)
            self.vorlage.setCurrentIndex(i)
            self.vorlage.blockSignals(False)
        elif not bestehend:
            self.vorlage.setCurrentIndex(1)           # Ollama ist die Vorbelegung

    def _chips_legen(self, spalten: int) -> None:
        """„Modell verwenden für“ als gleichmäßiges Raster (gleich breite Felder) statt einer Zeile, die irgendwo umbricht."""
        from PySide6.QtWidgets import QSizePolicy
        self._chipgitter.setProperty("schmal_nein", True)                         # das Raster bleibt, wie es ist (der Notbehelf der Seitenleiste bricht es sonst auf eine Spalte um)
        for b in self._chips:
            self._chipgitter.removeWidget(b)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for i, b in enumerate(self._chips):
            self._chipgitter.addWidget(b, i // spalten, i % spalten)
        for c in range(spalten):
            self._chipgitter.setColumnStretch(c, 1)

    def kompakt_machen(self) -> None:
        """In der Seitenleiste: der Titel steht schon im Kopf der Seite, und die Fähigkeiten stehen zu zweit nebeneinander."""
        self._titel.setVisible(False)
        self._chips_legen(2)

    def _vorlage_gewaehlt(self, i: int) -> None:
        url = self.vorlage.itemData(i)
        if self.vorlage.currentText() == "Andere":
            self.url.clear()
        else:
            self.url.setText(url)
            if not self.name.text().strip() or self.name.text() in [n for _, n, _ in K.ANBIETER_VORLAGEN]:
                self.name.setText(self.vorlage.currentText())
            self._holen(True)

    def _holen(self, still: bool) -> None:
        url, schl = self.url.text().strip(), self.schluessel.text().strip()
        if not url:
            if not still:
                self.stand.setText("Erst die URL eintragen.")
            return
        self.stand.setText("Wird geholt …")

        class _L(QRunnable):
            def run(s_):
                try:
                    r = {"namen": K.anbieter_modelle(url, schl)}
                except Exception as e:                  # Netz, Schlüssel, falsche Adresse — alles landet als Hinweis
                    r = {"fehler": str(e)}
                try:
                    self._antwort.da.emit(r)
                except RuntimeError:
                    pass                                # Dialog war schon zu
        QThreadPool.globalInstance().start(_L())

    def _geholt(self, r: dict) -> None:
        if "fehler" in r:
            self.stand.setText("Nicht abrufbar — Modell von Hand eintragen.")
            return
        namen = r["namen"]
        if not namen:
            self.stand.setText("Der Anbieter nennt keine Modelle.")
            return
        aktuell = self.modell.currentText()
        self.modell.clear()
        self.modell.addItems(namen)
        self.modell.setCurrentText(aktuell if aktuell in namen or aktuell else "")
        if not aktuell:
            self.modell.setCurrentIndex(-1)
            self.modell.lineEdit().setPlaceholderText("— Modell wählen —")
        self.stand.setText(f"{len(namen)} gefunden.")

    def _ok(self) -> None:
        if not self.name.text().strip() or not self.url.text().strip() or not self.modell.currentText().strip():
            QMessageBox.information(self, "Anbieter", "Name, URL und Modell werden gebraucht.")
            return
        werte = (self.name.text(), self.url.text(), self.schluessel.text(), self.modell.currentText(),
                 [k for k, b in self.tags.items() if b.isChecked()])
        if self.alt:
            self.k.anbieter_aktualisieren(self.alt["id"], *werte)
        else:
            self.k.anbieter_hinzufuegen(*werte)
        self.accept()


_CHIP = (('QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 3px 12px; color: palette(window-text); }QPushButton:checked { background: ' + Farbe.AKZENT + '; color: white; border-color: ' + Farbe.AKZENT + '; }'))


class ModellListe(QWidget):
    """Die Liste der verbundenen KI-Modelle: hinzufügen, bearbeiten, entfernen (im Fenster „KI-Einstellungen“ und als eigenes Fenster)."""

    def __init__(self, fenster, konfig: K.KIKonfig):
        super().__init__()
        self.fenster, self.k = fenster, konfig
        self.setMinimumSize(480, 240)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        z = QHBoxLayout()
        self.liste = QListWidget()
        z.addWidget(self.liste, 1)
        s = QVBoxLayout()
        self.neu = QToolButton(); self.neu.setText("+"); self.neu.setToolTip("Anbieter hinzufügen")
        self.bearb = QToolButton(); self.bearb.setText("✎"); self.bearb.setToolTip("Bearbeiten")
        self.weg = QToolButton(); self.weg.setText("🗑"); self.weg.setToolTip("Entfernen")
        for b in (self.neu, self.bearb, self.weg):
            s.addWidget(b)
        s.addStretch(1)
        z.addLayout(s)
        v.addLayout(z, 1)
        self.neu.clicked.connect(self._neu)
        self.bearb.clicked.connect(self._bearbeiten)
        self.weg.clicked.connect(self._entfernen)
        self.liste.currentRowChanged.connect(self._knoepfe)
        self.liste.itemDoubleClicked.connect(lambda _i: self._bearbeiten())
        self._fuellen()

    def _fuellen(self) -> None:
        self.liste.clear()
        for a in self.k["anbieter"]:
            teile = [a["modell"], _tags_text(a), "Lokaler Anbieter" if K.ist_lokale_url(a["url"]) else "Über das Internet"]
            it = QListWidgetItem(f"{a['name']}\n{' · '.join(t for t in teile if t)}")
            it.setData(Qt.UserRole, a["id"])
            self.liste.addItem(it)
        if self.liste.count():
            self.liste.setCurrentRow(0)                    # der erste Eintrag ist gewählt: ✎ und 🗑 sind sofort bedienbar
        self._knoepfe()

    def _knoepfe(self, *_):
        an = self.liste.currentRow() >= 0
        self.bearb.setEnabled(an)
        self.weg.setEnabled(an)

    def _aktuell(self):
        it = self.liste.currentItem()
        return self.k.anbieter_holen(it.data(Qt.UserRole)) if it else None

    def _neu(self) -> None:
        zeige_unter(self, AnbieterDialog(self.fenster, self.k), self._fuellen)

    def _bearbeiten(self) -> None:
        a = self._aktuell()
        if a:
            zeige_unter(self, AnbieterDialog(self.fenster, self.k, a), self._fuellen)

    def _entfernen(self) -> None:
        a = self._aktuell()
        if a and QMessageBox.question(self, "Entfernen", f"„{a['name']}“ aus der Liste entfernen?") == QMessageBox.Yes:
            self.k.anbieter_entfernen(a["id"])
            self._fuellen()


class ModellListeDialog(QDialog):
    """„Liste der KI-Modelle“ als eigenes Fenster (Optionen)."""

    def __init__(self, fenster, konfig: K.KIKonfig):
        super().__init__(fenster)
        self.setWindowTitle("Liste der KI-Modelle")
        v = QVBoxLayout(self)
        v.addWidget(text_label("Liste der KI-Modelle", fett=True, pt=13, umbruch=False))
        self.liste_widget = ModellListe(fenster, konfig)
        self._fuellen = self.liste_widget._fuellen
        v.addWidget(self.liste_widget, 1)
        v.addWidget(knopfzeile(self, nur_ok=True))


def modell_combo(konfig: K.KIKonfig, aufgabe: str, gewaehlt: str | None = None) -> QComboBox:
    """Die Auswahl „welches Modell für diese Aufgabe?“ — dieselbe in der Modellzuweisung und in den erweiterten Einstellungen des Chats."""
    c = QComboBox()
    c.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)       # lange Modellnamen machen das Feld nicht breiter als die Seitenleiste
    c.setMinimumContentsLength(12)
    c.addItem("Standard (KI-Modell der Optionen)", "")
    for m in konfig.alle_modelle():
        if aufgabe == "bildgenerierung":               # nur Anbieter mit „Bilder“ — Claude und Text-Modelle kennen das nicht
            if "bilder" not in m["verwendungFuer"] or not m["id"].startswith(K.EIGEN_MARKE):
                continue
        c.addItem(m["name"] + ("  · lokal" if m["lokal"] else ""), m["id"])
    g = konfig["aufgaben"].get(aufgabe, "") if gewaehlt is None else gewaehlt
    c.setCurrentIndex(max(0, c.findData(g)))
    return c


class ModellZuweisung(QWidget):
    """Je Aufgabe ein Modell: Chatbot, Zusammenfassen, Übersetzung, Textanalyse, Bildgenerierung."""

    def __init__(self, fenster):
        super().__init__()
        self.fenster = fenster
        self.k = fenster.ki.konfig
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(QLabel("Fügen Sie hinzu und wählen Sie KI-Modelle für verschiedene Aufgaben aus."))
        self.f = QFormLayout()
        v.addLayout(self.f)
        self.felder: dict[str, QComboBox] = {}
        v.addStretch(1)
        self.aufbauen()

    def aufbauen(self) -> None:
        alt = {a: c.currentData() for a, c in self.felder.items()}
        while self.f.rowCount():
            self.f.removeRow(0)
        self.felder.clear()
        for aufgabe, name in K.AUFGABEN:
            c = modell_combo(self.k, aufgabe, alt.get(aufgabe, self.k["aufgaben"].get(aufgabe, "")))
            self.felder[aufgabe] = c
            self.f.addRow(name, c)

    def uebernehmen(self) -> None:
        for aufgabe, c in self.felder.items():
            self.k.aufgabe_setzen(aufgabe, c.currentData() or "")
        self.fenster.ki.geaendert.emit()


class KIKonfigurationDialog(QDialog):
    """Die Modellzuweisung als eigenes Fenster (nur noch für Altaufrufe; im Alltag öffnet „KI-Einstellungen“)."""

    def __init__(self, fenster):
        super().__init__(fenster)
        self.setWindowTitle("KI-Konfiguration")
        self.setMinimumWidth(560)
        v = QVBoxLayout(self)
        v.addWidget(text_label("KI-Konfiguration", fett=True, pt=13, umbruch=False))
        self.zuweisung = ModellZuweisung(fenster)
        self.felder = self.zuweisung.felder
        v.addWidget(self.zuweisung)
        v.addWidget(knopfzeile(self, bei_ok=self._ok))

    def _ok(self) -> None:
        self.zuweisung.uebernehmen()
        self.accept()


class SprachListe(QListWidget):
    """Eine Sprachliste mit hohen Zeilen (wie das alte Fenster „Einstellungen der Übersetzung“); bedienbar wie eine Auswahl: ``currentData()``,
    ``currentText()``, ``setCurrentText()``, ``findData()``, ``setCurrentIndex()``."""

    def __init__(self, eintraege: list[tuple[str, str]]):
        super().__init__()
        for daten, text in eintraege:
            it = QListWidgetItem(text); it.setData(Qt.UserRole, daten); self.addItem(it)
        self.setStyleSheet("QListWidget { border: 1px solid palette(mid); border-radius: 6px; }"
                           "QListWidget::item { padding: 11px 14px; border-bottom: 1px solid palette(midlight); }"
                           "QListWidget::item:selected { background: palette(highlight); color: palette(highlighted-text); }"
                           "QListWidget::item:hover:!selected { background: palette(alternate-base); }")
        self.setMinimumHeight(260)

    def currentData(self):
        it = self.currentItem()
        return it.data(Qt.UserRole) if it else None

    def currentText(self) -> str:
        it = self.currentItem()
        return it.text() if it else ""

    def findData(self, daten) -> int:
        return next((i for i in range(self.count()) if self.item(i).data(Qt.UserRole) == daten), -1)

    def setCurrentIndex(self, i: int) -> None:
        self.setCurrentRow(i)
        if 0 <= i < self.count():
            self.scrollToItem(self.item(i))

    def setCurrentText(self, text: str) -> None:
        self.setCurrentIndex(next((i for i in range(self.count()) if self.item(i).text() == text), -1))


class SprachePanel(QWidget):
    """Die Sprachen der Schreibhilfe, nebeneinander: „Sprache für die Überprüfung“ (Sprache des Dokuments) und „Übersetzen nach“ (Ziel der KI-Übersetzung).
    Das Modell für die Übersetzung steht in der Modellzuweisung."""

    def __init__(self, fenster):
        super().__init__()
        self.fenster = fenster
        b = fenster.befehle
        v = QVBoxLayout(self); v.setContentsMargins(0, 8, 0, 0)
        z = self._spalten = QHBoxLayout(); z.setSpacing(24); self._spalten_w = []
        self.pruefung = SprachListe(list(b.SPRACHEN))
        self.pruefung.setCurrentIndex(max(0, self.pruefung.findData(b.pruefsprache_aktuell())))
        self.pruefung.setEnabled(fenster.current_tab() is not None)
        self.sprache = SprachListe([(n, n) for n in K.SPRACHEN])
        self.sprache.setCurrentText(fenster.ki.konfig["sprache"])
        for titel, unter, liste in (("Sprache für die Überprüfung", "Sprache des Dokuments — wird in der Datei vermerkt.", self.pruefung),
                                    ("Übersetzen nach", "Sprache für die KI-Übersetzung wählen.", self.sprache)):
            spalte = QWidget(); sp = QVBoxLayout(spalte); sp.setContentsMargins(0, 0, 0, 0); sp.setSpacing(4)
            sp.addWidget(text_label(titel, fett=True, pt=12, umbruch=False))
            hint = QLabel(unter); hint.setStyleSheet("color: palette(mid);"); sp.addWidget(hint)
            sp.addWidget(liste, 1)
            z.addWidget(spalte, 1); self._spalten_w.append(spalte)
        v.addLayout(z, 1)
        self._v = v
        h = QLabel("Die Schreibhilfe selbst prüft weiter auf Deutsch. Das Modell für die Übersetzung wählen Sie im Reiter „Modellzuweisung“ (Aufgabe „Übersetzung“).")
        h.setWordWrap(True); h.setStyleSheet("color: palette(mid);")
        v.addWidget(h)

    def kompakt_machen(self) -> None:
        """In der Seitenleiste: die zwei Listen untereinander statt nebeneinander, jede mit sechs sichtbaren Zeilen (der Rest rollt)."""
        neu = QVBoxLayout(); neu.setSpacing(10)                              # die Spalten wandern in ein neues, senkrechtes Layout
        self._v.removeItem(self._spalten)
        for w in self._spalten_w:
            neu.addWidget(w)
        self._v.insertLayout(0, neu)
        from PySide6.QtWidgets import QSizePolicy
        for l in (self.pruefung, self.sprache):
            l.setMinimumHeight(0); l.setFixedHeight(150); l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            l.setStyleSheet(l.styleSheet() + "QListWidget::item { padding: 6px 12px; border-bottom: 1px solid palette(midlight); }")
        for h in self.findChildren(QLabel):
            h.setWordWrap(True)
        self.layout().invalidate()

    def uebernehmen(self) -> None:
        if self.sprache.currentItem() is not None:
            self.fenster.ki.konfig.setze("sprache", self.sprache.currentText())
        if self.pruefung.isEnabled() and self.pruefung.currentData() and self.pruefung.currentData() != self.fenster.befehle.pruefsprache_aktuell():
            self.fenster.befehle.pruefsprache_setzen(self.pruefung.currentData())


class McpDialog(QDialog):
    """Ein MCP-Server: Name, Startbefehl, ein/aus; „Testen“ startet ihn kurz und zeigt seine Werkzeuge."""

    def __init__(self, fenster, e: dict | None = None):
        super().__init__(fenster)
        from PySide6.QtWidgets import QCheckBox
        self.setWindowTitle("MCP-Server bearbeiten" if e else "MCP-Server hinzufügen")
        self.setMinimumWidth(520)
        v = QVBoxLayout(self)
        f = QFormLayout()
        self.name = QLineEdit(e["name"] if e else ""); self.name.setPlaceholderText("Name")
        self.befehl = QLineEdit(e["befehl"] if e else "")
        self.befehl.setPlaceholderText("Startbefehl, z. B. npx -y @modelcontextprotocol/server-filesystem ~/Dokumente")
        f.addRow("Name *", self.name); f.addRow("Befehl *", self.befehl)
        v.addLayout(f)
        v.addWidget(QLabel("Der Server läuft auf diesem Rechner und startet nur während einer Chat-Frage. Jeder Werkzeugaufruf der KI wird vorher erfragt."))
        self.an = QCheckBox("Im KI-Chat verwenden"); self.an.setChecked(e["an"] if e else True)
        v.addWidget(self.an)
        self.stand = QLabel(""); self.stand.setWordWrap(True)
        t = QPushButton("Testen"); t.clicked.connect(self._testen)
        v.addWidget(t, 0, Qt.AlignLeft); v.addWidget(self.stand)
        v.addWidget(knopfzeile(self, bei_ok=self._ok, ok_text="Speichern"))

    def _testen(self) -> None:
        from lunivo_writer.ai import mcp as M
        try:
            w = M.pruefen(self.befehl.text())
            self.stand.setText(f"Verbunden — {len(w)} Werkzeug(e): " + ", ".join(t["name"] for t in w[:12]))
        except M.McpFehler as e:
            self.stand.setText(f"Nicht erreichbar: {e}")

    def _ok(self) -> None:
        if not self.name.text().strip() or not self.befehl.text().strip():
            QMessageBox.information(self, "MCP-Server", "Name und Befehl werden gebraucht.")
            return
        self.accept()

    def werte(self) -> tuple:
        return self.name.text(), self.befehl.text(), self.an.isChecked()


class McpListe(QWidget):
    """Die eingetragenen MCP-Server: hinzufügen, bearbeiten, entfernen."""

    def __init__(self, fenster, konfig: K.KIKonfig):
        super().__init__()
        self.fenster, self.k = fenster, konfig
        v = QVBoxLayout(self); v.setContentsMargins(0, 8, 0, 0)
        v.addWidget(QLabel("MCP-Server geben der KI im Chat Werkzeuge (Dateien lesen, Daten abfragen …). Gilt für Ollama und eigene Anbieter."))
        z = QHBoxLayout()
        self.liste = QListWidget(); z.addWidget(self.liste, 1)
        s = QVBoxLayout()
        self.neu = QToolButton(); self.neu.setText("+"); self.neu.setToolTip("Server hinzufügen")
        self.bearb = QToolButton(); self.bearb.setText("✎"); self.bearb.setToolTip("Bearbeiten")
        self.weg = QToolButton(); self.weg.setText("🗑"); self.weg.setToolTip("Entfernen")
        for b in (self.neu, self.bearb, self.weg):
            s.addWidget(b)
        s.addStretch(1); z.addLayout(s); v.addLayout(z, 1)
        self.neu.clicked.connect(self._neu); self.bearb.clicked.connect(self._bearbeiten); self.weg.clicked.connect(self._entfernen)
        self.liste.currentRowChanged.connect(self._knoepfe)
        self.liste.itemDoubleClicked.connect(lambda _i: self._bearbeiten())
        self.fuellen()

    def fuellen(self) -> None:
        self.liste.clear()
        for m in self.k["mcp"]:
            it = QListWidgetItem(f"{m['name']}{'' if m['an'] else '  (aus)'}\n{m['befehl']}")
            it.setData(Qt.UserRole, m["id"]); self.liste.addItem(it)
        if self.liste.count():
            self.liste.setCurrentRow(0)
        self._knoepfe()

    def _knoepfe(self, *_) -> None:
        an = self.liste.currentRow() >= 0
        self.bearb.setEnabled(an); self.weg.setEnabled(an)

    def _aktuell(self):
        it = self.liste.currentItem()
        return next((m for m in self.k["mcp"] if it and m["id"] == it.data(Qt.UserRole)), None)

    def _neu(self) -> None:
        d = McpDialog(self.fenster)
        zeige_unter(self, d, lambda: (self.k.mcp_speichern(None, *d.werte()), self.fuellen()))

    def _bearbeiten(self) -> None:
        m = self._aktuell()
        if m:
            d = McpDialog(self.fenster, m)
            zeige_unter(self, d, lambda: (self.k.mcp_speichern(m["id"], *d.werte()), self.fuellen()))

    def _entfernen(self) -> None:
        m = self._aktuell()
        if m and QMessageBox.question(self, "Entfernen", f"„{m['name']}“ aus der Liste entfernen?") == QMessageBox.Yes:
            self.k.mcp_entfernen(m["id"]); self.fuellen()


class WebsuchePanel(QWidget):
    """Websuche für den KI-Chat: Anbieter, Adresse oder Schlüssel, Zahl der Treffer. Ein: die Frage geht an den Suchanbieter."""

    def __init__(self, konfig: K.KIKonfig):
        super().__init__()
        from PySide6.QtWidgets import QCheckBox, QSpinBox
        from lunivo_writer.ai import websuche as W
        self.k = konfig
        o = konfig.websuche_optionen()
        v = QVBoxLayout(self); v.setContentsMargins(0, 8, 0, 0)
        self.an = QCheckBox("Websuche im KI-Chat verwenden"); self.an.setChecked(bool(o["an"]))
        v.addWidget(self.an)
        h = QLabel("Ist die Websuche an, geht Ihre Frage an den Suchanbieter (bei einer SearXNG-Instanz auf diesem Rechner bleibt sie hier). "
                   "Die Treffer werden der KI als Quellen mitgegeben.")
        h.setWordWrap(True); h.setStyleSheet("color: palette(mid);")
        v.addWidget(h)
        f = QFormLayout()
        self.anbieter = QComboBox()
        for schl, name in W.ANBIETER:
            self.anbieter.addItem(name, schl)
        self.anbieter.setCurrentIndex(max(0, self.anbieter.findData(o["anbieter"])))
        self.url = QLineEdit(o["url"]); self.url.setPlaceholderText("https://searx.example.org")
        self.schluessel = QLineEdit(o["schluessel"]); self.schluessel.setEchoMode(QLineEdit.Password)
        self.anzahl = QSpinBox(); self.anzahl.setRange(1, 10); self.anzahl.setValue(int(o["anzahl"]))
        f.addRow("Anbieter", self.anbieter); f.addRow("Adresse (SearXNG)", self.url); f.addRow("API-Schlüssel (Brave)", self.schluessel)
        f.addRow("Treffer", self.anzahl)
        v.addLayout(f)
        t = QPushButton("Testen"); t.clicked.connect(self._testen)
        self.stand = QLabel(""); self.stand.setWordWrap(True)
        v.addWidget(t, 0, Qt.AlignLeft); v.addWidget(self.stand); v.addStretch(1)

    def werte(self) -> dict:
        return {"an": self.an.isChecked(), "anbieter": self.anbieter.currentData(), "url": self.url.text().strip(),
                "schluessel": self.schluessel.text().strip(), "anzahl": self.anzahl.value()}

    def _testen(self) -> None:
        from lunivo_writer.ai import websuche as W
        try:
            t = W.suche(self.werte(), "Lunivo Writer")
            self.stand.setText(f"Verbunden — {len(t)} Treffer.")
        except (OSError, ValueError) as e:
            self.stand.setText(f"Nicht erreichbar: {getattr(e, 'reason', e)}")

    def uebernehmen(self) -> None:
        self.k.websuche_setzen(**self.werte())


REITER = ("KI-Modelle", "Modellzuweisung", "Sprache", "MCP-Server", "Websuche")


from lunivo_writer.ui.baukasten.zusatz_panel import PanelFaehig


class KIEinstellungenDialog(PanelFaehig, QDialog):
    """Das eine Fenster für alles zur KI: verbundene Modelle, Modellzuweisung, MCP-Server und Websuche.

    Dieselbe Konfiguration (``KIKonfig``) wie in der Seitenleiste der Schreibhilfe, im KI-Chat und in den Optionen. Bis ein Modell verbunden ist,
    sind alle übrigen Reiter grau."""

    def __init__(self, fenster, start: int = 0):
        super().__init__(fenster)
        from PySide6.QtWidgets import QStackedWidget, QTabBar
        self.fenster = fenster
        self.k = fenster.ki.konfig
        self.setWindowTitle("KI-Einstellungen")
        self.setMinimumSize(620, 520)
        v = QVBoxLayout(self)
        self.reiter = QTabBar(); self.reiter.setObjectName("bandReiter"); self.reiter.setExpanding(False)
        for n in REITER:
            self.reiter.addTab(n)
        v.addWidget(self.reiter)
        self.stapel = QStackedWidget()
        v.addWidget(self.stapel, 1)
        # 1 KI-Modelle
        seite = QWidget(); sv = QVBoxLayout(seite); sv.setContentsMargins(0, 8, 0, 0)
        sv.addWidget(QLabel("Verbinden Sie Ihre eigene KI-Quelle — entweder über den API-Schlüssel eines Anbieters oder ein lokal gehostetes Modell."))
        self.liste = ModellListe(fenster, self.k)
        sv.addWidget(self.liste, 1)
        neu = QPushButton("Neues KI-Modell verbinden …"); neu.clicked.connect(self.neues_modell)
        sv.addWidget(neu, 0, Qt.AlignLeft)
        self.stapel.addWidget(seite)
        # 2 Modellzuweisung
        z = QWidget(); zv = QVBoxLayout(z); zv.setContentsMargins(0, 8, 0, 0)
        self.zuweisung = ModellZuweisung(fenster)
        zv.addWidget(self.zuweisung)
        self.stapel.addWidget(z)
        # 3 Sprache, 4 MCP-Server, 5 Websuche
        self.sprache = SprachePanel(fenster)
        self.stapel.addWidget(self.sprache)
        self.mcp = McpListe(fenster, self.k)
        self.stapel.addWidget(self.mcp)
        self.websuche = WebsuchePanel(self.k)
        self.stapel.addWidget(self.websuche)
        v.addWidget(knopfzeile(self, bei_ok=self._ok))
        self.reiter.currentChanged.connect(self.stapel.setCurrentIndex)
        self.freischalten()
        self.reiter.setCurrentIndex(start if self.reiter.isTabEnabled(start) else 0)

    def kompakt_machen(self) -> None:
        """In der Seitenleiste: kurze Reiternamen (die langen stehen im Tipp), damit alle fünf nebeneinander passen."""
        for i, (kurz, voll) in enumerate((("Modelle", "KI-Modelle"), ("Zuweisung", "Modellzuweisung"), ("Sprache", "Sprache"), ("MCP", "MCP-Server"),
                                          ("Websuche", "Websuche"))):
            self.reiter.setTabText(i, kurz)
            if self.reiter.isTabEnabled(i):
                self.reiter.setTabToolTip(i, voll)
        self.reiter.setUsesScrollButtons(True); self.reiter.setElideMode(Qt.ElideNone)
        self.liste.setMinimumSize(0, 0)
        for l in self.stapel.widget(0).findChildren(QLabel):
            l.setWordWrap(True)
        self.sprache.kompakt_machen()

        def hoehe_der_seite(i: int) -> None:                                  # nur die gewählte Seite bestimmt die Höhe, die anderen zählen nicht mit
            from PySide6.QtWidgets import QSizePolicy
            for k in range(self.stapel.count()):
                w = self.stapel.widget(k); sp = w.sizePolicy()
                sp.setVerticalPolicy(QSizePolicy.Preferred if k == i else QSizePolicy.Ignored); w.setSizePolicy(sp)
            self.stapel.updateGeometry()
            e = self.stapel.parentWidget()
            while e is not None:
                if e.layout() is not None:
                    e.layout().invalidate()
                e = e.parentWidget()
        self.reiter.currentChanged.connect(hoehe_der_seite)
        hoehe_der_seite(self.reiter.currentIndex())
        self.setMinimumSize(0, 0)

    def freischalten(self) -> None:
        """Ohne verbundenes Modell ist nur der erste Reiter bedienbar; mit Modell (auch Ollama auf diesem Rechner) sind alle frei."""
        da = self.fenster.ki.verfuegbar()
        for i in (1, 2, 3, 4):
            self.reiter.setTabEnabled(i, da)
            self.reiter.setTabToolTip(i, "" if da else "Erst ein KI-Modell verbinden.")

    def neues_modell(self) -> None:
        def fertig():
            self.liste._fuellen()
            self.zuweisung.aufbauen()
            self.fenster.ki.geaendert.emit()
            self.freischalten()
        zeige_unter(self, AnbieterDialog(self.fenster, self.k), fertig)

    def _ok(self) -> None:
        self.zuweisung.uebernehmen()
        self.sprache.uebernehmen()
        self.websuche.uebernehmen()
        self.accept()


VORLAGEN_AKTION = [
    ("Übersetzen", "Übersetze den Text ins Englische."), ("Ton ändern", "Schreibe den Text in einem freundlicheren, höflichen Ton."),
    ("Professionelle Umschreibung", "Schreibe den Text professionell und sachlich um."),
    ("Zusammenfassung als Liste", "Fasse den Text als kurze Aufzählung zusammen."), ("Text vereinfachen", "Schreibe den Text in einfacher Sprache."),
    ("Text erweitern", "Erweitere den Text um passende Einzelheiten."), ("Grammatik korrigieren", "Korrigiere Grammatik und Rechtschreibung."),
    ("Kürzer machen", "Kürze den Text, ohne Wichtiges wegzulassen."), ("Länger machen", "Mache den Text ausführlicher."),
    ("Kernpunkte herausziehen", "Nenne die Kernpunkte des Textes."), ("Tabelle erstellen", "Fasse die Angaben des Textes in einer Tabelle zusammen."),
    ("Beispiele hinzufügen", "Ergänze passende Beispiele."), ("Einfach erklären", "Erkläre den Inhalt so, dass ihn ein Kind versteht.")]
ERGEBNIS_ARTEN = (("ersetzen", "Ersetzen (ersetzt den markierten Text durch das Ergebnis)"), ("anhaengen", "Anhängen (setzt das Ergebnis hinter den Text)"),
                  ("hinweis", "Als Hinweis zeigen (Karte in der Seitenleiste)"))


class SchnelleAktionDialog(QDialog):
    """„Schnelle KI-Aktion erstellen“: eine einmalige KI-Aufgabe mit Name, Anweisung, Ergebnisart und Zugriff.

    Speichert als „Eigener Assistent“ (``KIKonfig.assistenten``) — dieselbe Liste wie im Band und in den Optionen."""

    def __init__(self, fenster):
        super().__init__(fenster)
        from PySide6.QtWidgets import QPlainTextEdit, QRadioButton
        self.setWindowTitle("Schnelle KI-Aktion erstellen")
        self.setMinimumWidth(560)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Eine schnelle KI-Aktion führt einmalige KI-Aufgaben aus."))
        v.addWidget(text_label("Mit einer Vorlage beginnen", fett=True))
        fl = QWidget(); fll = FlowLayout(fl)
        self.chipfeld = fl
        self.chips = []
        for name, prompt in VORLAGEN_AKTION:
            b = QPushButton(name); b.setStyleSheet(_CHIP); b.clicked.connect(lambda _=False, n=name, p=prompt: self._vorlage(n, p))
            fll.addWidget(b); self.chips.append(b)
        v.addWidget(fl)
        self.mehr = QPushButton(); self.mehr.setFlat(True); self.mehr.setCursor(Qt.PointingHandCursor)
        self.mehr.clicked.connect(self._umschalten)
        v.addWidget(self.mehr, 0, Qt.AlignLeft)
        v.addWidget(text_label("Name *", fett=True))
        self.name = QLineEdit(); self.name.setPlaceholderText("Geben Sie einen kurzen Namen für die Aktion ein"); self.name.setMaxLength(40)
        v.addWidget(self.name)
        v.addWidget(text_label("Was soll die Aktion tun? *", fett=True))
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText("Beschreiben Sie die Aktion, die die KI ausführen soll, z. B. „Grammatik korrigieren“ oder „In einem formellen Ton umschreiben“")
        self.prompt.setMinimumHeight(90)
        v.addWidget(self.prompt)
        v.addWidget(text_label("Ergebnis anwenden als", fett=True))
        self.ergebnis = QComboBox()
        for schl, text in ERGEBNIS_ARTEN:
            self.ergebnis.addItem(text, schl)
        v.addWidget(self.ergebnis)
        v.addWidget(text_label("Zugriff von", fett=True))
        self.r_kontext = QRadioButton("Verfügbar über das Kontextmenü"); self.r_kontext.setChecked(True)
        self.r_schnell = QRadioButton("Schnellzugriff über die Symbolleiste")
        v.addWidget(self.r_kontext); v.addWidget(self.r_schnell)
        z = knopfzeile(self, bei_ok=self._ok, ok_text="Erstellen")
        self.ok = z.ok
        v.addWidget(z)
        self._alle = False
        self._umschalten()

    def _umschalten(self) -> None:
        """Erst die ersten sechs Vorlagen, mit „Alle anzeigen“ alle."""
        self._alle = not self._alle
        for i, b in enumerate(self.chips):
            b.setVisible(self._alle or i < 6)
        self.mehr.setText("Ausblenden" if self._alle else "Alle anzeigen")
        self.chipfeld.setMinimumHeight(self.chipfeld.layout().heightForWidth(max(300, self.width() - 24)))

    def _vorlage(self, name: str, prompt: str) -> None:
        self.name.setText(name)
        self.prompt.setPlainText(prompt)

    def _ok(self) -> None:
        if not self.name.text().strip() or not self.prompt.toPlainText().strip():
            QMessageBox.information(self, "Schnelle KI-Aktion", "Name und Beschreibung werden gebraucht.")
            return
        self.accept()

    def werte(self) -> tuple:
        return (self.name.text(), self.prompt.toPlainText(), self.ergebnis.currentData(), "schnell" if self.r_schnell.isChecked() else "kontext")


class ErgebnisseDialog(QDialog):
    """„Alle Ergebnisse anzeigen“: die KI-Antworten dieser Sitzung; Kopieren oder an der Schreibmarke einfügen."""

    def __init__(self, fenster):
        super().__init__(fenster)
        from PySide6.QtWidgets import QApplication, QPlainTextEdit
        self.fenster = fenster
        self.setWindowTitle("Alle Ergebnisse")
        self.setMinimumSize(640, 420)
        self.liste_daten = list(reversed(fenster.ki.ergebnisse))                     # neueste oben
        v = QVBoxLayout(self)
        z = QHBoxLayout()
        self.liste = QListWidget()
        for e in self.liste_daten:
            self.liste.addItem(f"{e['zeit']}  {e['titel']}")
        z.addWidget(self.liste, 1)
        self.text = QPlainTextEdit(); self.text.setReadOnly(True)
        z.addWidget(self.text, 2)
        v.addLayout(z, 1)
        if not self.liste_daten:
            v.addWidget(QLabel("In dieser Sitzung hat die KI noch nichts geliefert."))
        bb = knopfzeile(self, schliessen=True)
        self.kopieren = bb.zusatz_knopf(QPushButton("Kopieren"))
        self.einfuegen = bb.zusatz_knopf(QPushButton("Einfügen"))
        self.kopieren.clicked.connect(lambda: QApplication.clipboard().setText(self.text.toPlainText()))
        self.einfuegen.clicked.connect(self._einfuegen)
        v.addWidget(bb)
        self.liste.currentRowChanged.connect(self._zeigen)
        if self.liste_daten:
            self.liste.setCurrentRow(0)
        self._zeigen(self.liste.currentRow())

    def _zeigen(self, i: int) -> None:
        an = 0 <= i < len(self.liste_daten)
        self.text.setPlainText(self.liste_daten[i]["text"] if an else "")
        self.kopieren.setEnabled(an); self.einfuegen.setEnabled(an)

    def _einfuegen(self) -> None:
        e = self.fenster.current_editor()
        if e is not None and self.text.toPlainText():
            e.textCursor().insertText(self.text.toPlainText())
