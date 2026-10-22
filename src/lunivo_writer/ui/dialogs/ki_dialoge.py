"""KI-Konfiguration: Aufgaben-Modellzuweisung, Liste der KI-Modelle, „Eigenen Anbieter hinzufügen“.

Der Anbieter wird hier festgelegt — in „KI-Konfiguration“ (Reiter Schreibhilfe/KI) oder in den Optionen.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
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
        t = text_label(self.windowTitle(), fett=True, pt=13, umbruch=False)
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
        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(self.accept)
        v.addWidget(bb)


def modell_combo(konfig: K.KIKonfig, aufgabe: str, gewaehlt: str | None = None) -> QComboBox:
    """Die Auswahl „welches Modell für diese Aufgabe?“ — dieselbe in der Modellzuweisung und in den erweiterten Einstellungen des Chats."""
    c = QComboBox()
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
        o = QPushButton("Einstellungen der Übersetzung"); o.setFlat(True); o.setCursor(Qt.PointingHandCursor)
        o.clicked.connect(lambda: fenster.show_options("sprache"))
        v.addWidget(o, 0, Qt.AlignLeft)
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
        bb = QDialogButtonBox()
        bb.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        bb.addButton("OK", QDialogButtonBox.AcceptRole)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _ok(self) -> None:
        self.zuweisung.uebernehmen()
        self.accept()


REITER = ("KI-Modelle", "Modellzuweisung", "MCP-Server", "Websuche")


class KIEinstellungenDialog(QDialog):
    """Das eine Fenster für alles zur KI: verbundene Modelle, Modellzuweisung, MCP-Server und Websuche.

    Dieselbe Konfiguration (``KIKonfig``) wie in der Seitenleiste der Schreibhilfe, im KI-Chat und in den Optionen. Bis ein Modell verbunden ist,
    sind „Modellzuweisung“, „MCP-Server“ und „Websuche“ grau; die beiden letzten sind noch nicht freigeschaltet."""

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
        # 3 und 4: noch nicht freigeschaltet
        for n in REITER[2:]:
            p = QWidget(); pv = QVBoxLayout(p); pv.addWidget(QLabel(n + " ist noch nicht freigeschaltet.")); pv.addStretch(1)
            self.stapel.addWidget(p)
        bb = QDialogButtonBox()
        bb.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        bb.addButton("OK", QDialogButtonBox.AcceptRole)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
        self.reiter.currentChanged.connect(self.stapel.setCurrentIndex)
        self.freischalten()
        self.reiter.setCurrentIndex(start if self.reiter.isTabEnabled(start) else 0)

    def freischalten(self) -> None:
        """Ohne verbundenes Modell ist nur der erste Reiter bedienbar; MCP-Server und Websuche bleiben grau."""
        da = self.fenster.ki.verfuegbar()
        self.reiter.setTabEnabled(1, da)
        for i in (2, 3):
            self.reiter.setTabEnabled(i, False)
            self.reiter.setTabToolTip(i, "Noch nicht freigeschaltet.")
        if not da:
            self.reiter.setTabToolTip(1, "Erst ein KI-Modell verbinden.")

    def neues_modell(self) -> None:
        if AnbieterDialog(self.fenster, self.k).exec():
            self.liste._fuellen()
            self.zuweisung.aufbauen()
            self.fenster.ki.geaendert.emit()
            self.freischalten()

    def _ok(self) -> None:
        self.zuweisung.uebernehmen()
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
        bb = QDialogButtonBox()
        bb.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        self.ok = bb.addButton("Erstellen", QDialogButtonBox.AcceptRole)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
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
        bb = QDialogButtonBox()
        self.kopieren = bb.addButton("Kopieren", QDialogButtonBox.ActionRole)
        self.einfuegen = bb.addButton("Einfügen", QDialogButtonBox.ActionRole)
        bb.addButton("Schließen", QDialogButtonBox.RejectRole)
        bb.rejected.connect(self.reject)
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
