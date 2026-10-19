"""KI-Konfiguration: Aufgaben-Modellzuweisung, Liste der KI-Modelle, „Eigenen Anbieter hinzufügen“.

Der Anbieter wird hier festgelegt — in „KI-Konfiguration“ (Reiter Schreibhilfe/KI) oder in den Optionen.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ai import ki as K
from lunivo_writer.ui.widgets.flow_layout import FlowLayout


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
        t = QLabel("<b style='font-size:13pt'>%s</b>" % self.windowTitle())
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
        fll = FlowLayout(fl)
        self.tags = {}
        gesetzt = set(bestehend["verwendungFuer"]) if bestehend else {"text"}
        alle = QPushButton("Alle")
        alle.setCheckable(True)
        alle.setStyleSheet(_CHIP)
        alle.toggled.connect(lambda an: [b.setChecked(an) for b in self.tags.values()])
        fll.addWidget(alle)
        for key, name in K.ANBIETER_TAGS:
            b = QPushButton(name)
            b.setCheckable(True)
            b.setChecked(key in gesetzt)
            b.setStyleSheet(_CHIP)
            self.tags[key] = b
            fll.addWidget(b)
        v.addWidget(fl)
        bb = QDialogButtonBox()
        bb.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        self.ok = bb.addButton("Speichern" if bestehend else "Hinzufügen", QDialogButtonBox.AcceptRole)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
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


_CHIP = ("QPushButton { border: 1px solid palette(mid); border-radius: 11px; padding: 3px 12px; color: palette(window-text); }"
         "QPushButton:checked { background: #2f6fb5; color: white; border-color: #2f6fb5; }")


class ModellListeDialog(QDialog):
    """„Liste der KI-Modelle“: hinzufügen, bearbeiten, entfernen."""

    def __init__(self, fenster, konfig: K.KIKonfig):
        super().__init__(fenster)
        self.fenster, self.k = fenster, konfig
        self.setWindowTitle("Liste der KI-Modelle")
        self.setMinimumSize(480, 340)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("<b style='font-size:13pt'>Liste der KI-Modelle</b>"))
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
        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(self.accept)
        v.addWidget(bb)
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
        self._knoepfe()

    def _knoepfe(self, *_):
        an = self.liste.currentRow() >= 0
        self.bearb.setEnabled(an)
        self.weg.setEnabled(an)

    def _aktuell(self):
        it = self.liste.currentItem()
        return self.k.anbieter_holen(it.data(Qt.UserRole)) if it else None

    def _neu(self) -> None:
        if AnbieterDialog(self.fenster, self.k).exec():
            self._fuellen()

    def _bearbeiten(self) -> None:
        a = self._aktuell()
        if a and AnbieterDialog(self.fenster, self.k, a).exec():
            self._fuellen()

    def _entfernen(self) -> None:
        a = self._aktuell()
        if a and QMessageBox.question(self, "Entfernen", f"„{a['name']}“ aus der Liste entfernen?") == QMessageBox.Yes:
            self.k.anbieter_entfernen(a["id"])
            self._fuellen()


class KIKonfigurationDialog(QDialog):
    """Je Aufgabe ein Modell: Chatbot, Zusammenfassen, Übersetzung, Textanalyse, Bildgenerierung."""

    def __init__(self, fenster):
        super().__init__(fenster)
        self.fenster = fenster
        self.k = fenster.ki.konfig
        self.setWindowTitle("KI-Konfiguration")
        self.setMinimumWidth(560)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("<b style='font-size:13pt'>KI-Konfiguration</b>"))
        v.addWidget(QLabel("Fügen Sie hinzu und wählen Sie KI-Modelle für verschiedene Aufgaben aus."))
        self.f = QFormLayout()
        v.addLayout(self.f)
        self.felder: dict[str, QComboBox] = {}
        z = QHBoxLayout()
        a = QPushButton("KI-Modelle bearbeiten"); a.setFlat(True); a.setCursor(Qt.PointingHandCursor)
        b = QPushButton("Eigenen Anbieter hinzufügen"); b.setFlat(True); b.setCursor(Qt.PointingHandCursor)
        a.clicked.connect(self._liste)
        b.clicked.connect(self._neu)
        z.addWidget(a); z.addWidget(b); z.addStretch(1)
        v.addLayout(z)
        o = QPushButton("Einstellungen der Übersetzung"); o.setFlat(True); o.setCursor(Qt.PointingHandCursor)
        o.clicked.connect(lambda: fenster.show_options("sprache"))
        v.addWidget(o, 0, Qt.AlignLeft)
        bb = QDialogButtonBox()
        bb.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        bb.addButton("OK", QDialogButtonBox.AcceptRole)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
        self._aufbauen()

    def _aufbauen(self) -> None:
        alt = {a: c.currentData() for a, c in self.felder.items()}
        while self.f.rowCount():
            self.f.removeRow(0)
        self.felder.clear()
        modelle = self.k.alle_modelle()
        for aufgabe, name in K.AUFGABEN:
            c = QComboBox()
            c.addItem("Standard (KI-Modell der Optionen)", "")
            for m in modelle:
                if aufgabe == "bildgenerierung":           # nur Anbieter mit „Bilder“ — Claude und Text-Modelle kennen das nicht
                    if "bilder" not in m["verwendungFuer"] or not m["id"].startswith(K.EIGEN_MARKE):
                        continue
                c.addItem(m["name"] + ("  · lokal" if m["lokal"] else ""), m["id"])
            gewaehlt = alt.get(aufgabe, self.k["aufgaben"].get(aufgabe, ""))
            c.setCurrentIndex(max(0, c.findData(gewaehlt)))
            self.felder[aufgabe] = c
            self.f.addRow(name, c)

    def _liste(self) -> None:
        ModellListeDialog(self.fenster, self.k).exec()
        self._aufbauen()

    def _neu(self) -> None:
        if AnbieterDialog(self.fenster, self.k).exec():
            self._aufbauen()

    def _ok(self) -> None:
        for aufgabe, c in self.felder.items():
            self.k.aufgabe_setzen(aufgabe, c.currentData() or "")
        self.fenster.ki.geaendert.emit()
        self.accept()
