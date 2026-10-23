"""Backstage-Ansicht des Reiters „Datei“: links die Befehlsliste, rechts die Seite zum gewählten Befehl (wie in ONLYOFFICE).

Befehle ohne eigene Seite (Neu, Öffnen, Speichern, Schließen …) führen sofort aus und schließen die Ansicht; Seiten gibt es für
Zuletzt benutzte Dokumente, Speichern als (alle Ausgabeformate), Drucken, Schützen, Info und Öffnen mit …
"""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QStackedWidget,
    QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.datei_symbole import datei_symbol
from lunivo_writer.ui.widgets import icons

# (Schlüssel, Beschriftung, Symbol, Art: "seite" | "tun" | "trenner", Befehl)
from lunivo_writer.core.farben import Farbe
EINTRAEGE = [
    ("neu", "Neues Dokument erstellen", "neu", "tun", "neu"),
    ("vorlage", "Von Vorlage erstellen", "vorlage", "seite", None),
    ("oeffnen", "Öffnen", "oeffnen", "tun", "oeffnen"),
    ("zuletzt", "Zuletzt benutzte Dokumente öffnen", "zuletzt", "seite", None),
    ("-1", "", "", "trenner", None),
    ("speichern", "Speichern", "speichern", "tun", "speichern"),
    ("speichern_als", "Speichern als", "speichern", "seite", None),
    ("drucken", "Drucken", "drucken", "seite", None),
    ("schuetzen", "Schützen", "sperren", "seite", None),
    ("-2", "", "", "trenner", None),
    ("info", "Info", "inhalt", "seite", None),
    ("oeffnen_mit", "Öffnen mit …", "buch", "seite", None),
    ("ort", "Dateispeicherort öffnen", "oeffnen", "ort", None),
    ("-3", "", "", "trenner", None),
    ("schliessen", "Schließen", "schliessen", "tun", "schliessen"),
    ("-4", "", "", "trenner", None),
    ("optionen", "Erweiterte Einstellungen", "zahnrad", "seite", None),
    ("hilfe", "Hilfe", "buch", "seite", None),
]

EXPORTE = [("PDF-Dokument (.pdf)", "speichernPdf"), ("Word-Dokument (.docx)", "exportierenDocx"),
           ("Word 97–2003 (.doc, optional)", "exportierenDoc"), ("OpenDocument-Text (.odt)", "exportierenOdt"),
           ("Rich-Text-Format (.rtf)", "exportierenRtf"), ("Nur Text (.txt)", "exportierenTxt"),
           ("Bild der Seite (.png)", "exportierenPng")]

EXPORT_ENDUNG = {"speichernPdf": ".pdf", "exportierenDocx": ".docx", "exportierenDoc": ".doc", "exportierenOdt": ".odt",
                 "exportierenRtf": ".rtf", "exportierenTxt": ".txt", "exportierenPng": ".png"}

BREITE = 460

STIL = ('\nQWidget#bsLinks { background: palette(window); }\nQListWidget#bsListe { background: transparent; border: none; outline: none; }\nQListWidget#bsListe::item { padding: 10px 14px; border-left: 3px solid transparent; }\nQListWidget#bsListe::item:selected { background: palette(midlight); color: palette(window-text); border-left: 3px solid palette(highlight); }\nQListWidget#bsListe::item:hover:!selected { background: palette(midlight); }\nQWidget#bsRechts, QScrollArea#bsSeite, QScrollArea#bsSeite > QWidget > QWidget { background: palette(base); }\nQLabel#bsTitel { font-size: 17pt; }\nQWidget#optKopf { border-bottom: 1px solid palette(midlight); }\nQPushButton#optZurueck { border: none; background: transparent; font-size: 14pt; font-weight: 600; text-align: left; padding: 4px 6px; }\nQPushButton#optFertig { background: ' + Farbe.AKZENT + '; color: white; border: none; border-radius: 6px; padding: 9px 30px; font-weight: 600; }\nQPushButton#optFertig:hover { background: ' + Farbe.AKZENT_DUNKEL + '; }\nQLabel#bsGruppe { font-size: 11pt; font-weight: 600; }\nQLabel#bsHinweis { color: palette(mid); }\nQPushButton#bsKnopf { border: none; background: transparent; padding: 9px 12px; text-align: left; border-radius: 6px; }\nQPushButton#bsKnopf:hover:enabled { background: palette(midlight); }\nQPushButton#bsKnopf:disabled { color: palette(mid); }\n')


class Backstage(QWidget):
    schliessen = Signal()

    def __init__(self, fenster):
        super().__init__()
        self.w = fenster
        self.setStyleSheet(STIL)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        links = QWidget()
        links.setObjectName("bsLinks")
        links.setFixedWidth(340)
        ll = QVBoxLayout(links)
        ll.setContentsMargins(0, 8, 0, 8)
        zurueck = QPushButton(icons.icon("voriges", 18), "  Zurück zum Dokument")
        zurueck.setObjectName("bsKnopf")
        zurueck.setCursor(Qt.PointingHandCursor)
        zurueck.clicked.connect(self.schliessen)
        ll.addWidget(zurueck)
        self.liste = QListWidget()
        self.liste.setObjectName("bsListe")
        self.liste.setIconSize(QSize(20, 20))
        self.liste.setFocusPolicy(Qt.NoFocus)
        ll.addWidget(self.liste, 1)
        lay.addWidget(links)
        self._links = links                                          # bei den Optionen ausgeblendet
        self.rechts = QWidget()
        self.rechts.setObjectName("bsRechts")
        rl = QVBoxLayout(self.rechts)
        rl.setContentsMargins(0, 0, 0, 0)
        self.stapel = QStackedWidget()
        rl.addWidget(self.stapel)
        lay.addWidget(self.rechts, 1)
        self.zeilen: dict[str, QListWidgetItem] = {}
        for schl, text, sym, art, _b in EINTRAEGE:
            it = QListWidgetItem(text)
            if sym:
                it.setIcon(icons.icon(sym if icons.hat(sym) else "zahnrad", 20))
            if art == "trenner":
                it.setFlags(Qt.NoItemFlags)
                it.setSizeHint(QSize(10, 14))
                it.setText("")
            self.zeilen[schl] = it
            self.liste.addItem(it)
        self.liste.itemClicked.connect(self._gewaehlt)
        self.seiten: dict[str, QWidget] = {}
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.schliessen.emit)
        self._frischen_sich_selbst = True

    # ---- Aufbau der Seiten (bei jedem Öffnen frisch, damit Zahlen und Listen stimmen) ----------------------------
    def oeffnen(self, seite: str = "zuletzt", unter: str | None = None):
        """``unter``: bei „optionen“ die Seite der Optionen, die gleich offen sein soll (z. B. „ki“)."""
        self._optionen_unter = unter
        self._links.show()
        while self.stapel.count():
            w = self.stapel.widget(0)
            self.stapel.removeWidget(w)
            w.deleteLater()
        self.seiten.clear()
        haben_dok = self.w.current_tab() is not None
        for schl in ("speichern", "speichern_als", "drucken", "schuetzen", "info", "oeffnen_mit", "ort", "schliessen"):
            self.zeilen[schl].setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable if haben_dok else Qt.NoItemFlags)
        bauer = {"zuletzt": self._zuletzt, "speichern_als": self._speichern_als, "drucken": self._drucken, "vorlage": self._vorlage,
                 "hilfe": self._hilfe, "schuetzen": self._schuetzen, "info": self._info, "oeffnen_mit": self._oeffnen_mit, "optionen": self._optionen}
        for schl, f in bauer.items():
            seite_w = f()
            self.seiten[schl] = seite_w
            self.stapel.addWidget(seite_w)
        if seite not in self.seiten or (not haben_dok and seite not in ("zuletzt", "optionen")):
            seite = "zuletzt"
        self._zeigen(seite)

    def optionen_seite(self) -> str | None:
        """Schlüssel der Optionenseite, die gerade offen ist (z. B. „ansicht“)."""
        a = getattr(self.seiten.get("optionen"), "_ansicht", None)
        it = a.baum.currentItem() if a is not None else None
        return it.data(0, 0x100) if it is not None else None

    def _optionen(self) -> QWidget:
        """Platzhalter: die Optionen werden erst gebaut, wenn die Seite zum ersten Mal gezeigt wird."""
        ph = QWidget()
        QVBoxLayout(ph).setContentsMargins(0, 0, 0, 0)
        ph._ansicht = None
        return ph

    def _optionen_zeigen(self) -> None:
        from lunivo_writer.ui.dialogs.optionen import OptionenAnsicht
        ph = self.seiten["optionen"]
        self._links.hide()                                           # die Optionen füllen die ganze Breite; das Menü ist für die Dauer weg
        if ph._ansicht is None:
            v = ph.layout()
            kopf = QWidget(); kopf.setObjectName("optKopf")
            kh = QHBoxLayout(kopf); kh.setContentsMargins(14, 10, 14, 10)
            zurueck = QPushButton("←   Optionen")
            zurueck.setObjectName("optZurueck"); zurueck.setFlat(True); zurueck.setCursor(Qt.PointingHandCursor)
            zurueck.setToolTip("Optionen verlassen")
            zurueck.clicked.connect(self.schliessen)
            kh.addWidget(zurueck); kh.addStretch(1)
            ph._ansicht = OptionenAnsicht(self.w, getattr(self, "_optionen_unter", None))
            fuss = QWidget(); fh = QHBoxLayout(fuss); fh.setContentsMargins(24, 10, 24, 14)
            fertig = QPushButton("Fertig"); fertig.setObjectName("optFertig"); fertig.setCursor(Qt.PointingHandCursor)
            fertig.clicked.connect(self.schliessen)
            fh.addStretch(1); fh.addWidget(fertig)
            ph._kopf, ph._fertig, ph._zurueck = kopf, fertig, zurueck
            v.addWidget(kopf); v.addWidget(ph._ansicht, 1); v.addWidget(fuss)
        elif getattr(self, "_optionen_unter", None):
            ph._ansicht.gehe_zu(self._optionen_unter)

    def _zeigen(self, schl: str):
        if schl == "optionen":
            self._optionen_zeigen()
        elif schl == "drucken":
            self._drucken_zeigen()
        elif schl == "vorlage":
            self._vorlage_zeigen()
        self.stapel.setCurrentWidget(self.seiten[schl])
        self.liste.setCurrentItem(self.zeilen[schl])

    def _gewaehlt(self, it: QListWidgetItem):
        schl = next(k for k, v in self.zeilen.items() if v is it)
        art, befehl = next((e[3], e[4]) for e in EINTRAEGE if e[0] == schl)
        if art == "seite":
            self._zeigen(schl)
        elif art == "tun":
            self.schliessen.emit()
            self.w.befehle.tun(befehl)
        elif art == "ort":
            t = self.w.current_tab()
            if t and t.path and os.path.exists(t.path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(os.path.abspath(t.path))))
            else:
                self.w.statusBar().showMessage("Das Dokument ist noch nicht gespeichert — es gibt noch keinen Speicherort.", 5000)

    # ---- Bausteine -------------------------------------------------------------------------------------------
    def _seite(self, titel: str) -> tuple[QScrollArea, QVBoxLayout]:
        sa = QScrollArea()
        sa.setObjectName("bsSeite")
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        inh = QWidget()
        v = QVBoxLayout(inh)
        v.setContentsMargins(44, 36, 44, 24)
        v.setSpacing(8)
        t = QLabel(titel)
        t.setObjectName("bsTitel")
        v.addWidget(t)
        v.addSpacing(14)
        sa.setWidget(inh)
        return sa, v

    @staticmethod
    def _gruppe(v: QVBoxLayout, text: str, hinweis: str = ""):
        v.addSpacing(8)
        g = QLabel(text)
        g.setObjectName("bsGruppe")
        v.addWidget(g)
        if hinweis:
            h = QLabel(hinweis)
            h.setObjectName("bsHinweis")
            h.setWordWrap(True)
            v.addWidget(h)

    def _knopf(self, v: QVBoxLayout, text: str, befehl: str, icon: str | None = None, schliessen: bool = True,
               datei: str | None = None):
        k = QPushButton(text)
        k.setObjectName("bsKnopf")
        sym = datei_symbol(datei) if datei else None
        if sym is not None and not sym.isNull():                       # Dateiformat: Symbol des Systems statt unseres
            k.setIcon(sym); k.setIconSize(QSize(22, 22))
        elif icon and icons.hat(icon):
            k.setIcon(icons.icon(icon, 18))
        k.setEnabled(self.w.befehle.hat(befehl))
        k.setCursor(Qt.PointingHandCursor)
        k.setFixedWidth(BREITE)                               # alle Zeilen gleich breit, keine Kästen
        k.clicked.connect(lambda _=False, b=befehl: (self.schliessen.emit() if schliessen else None, self.w.befehle.tun(b)))
        v.addWidget(k)
        return k

    # ---- Seiten ------------------------------------------------------------------------------------------------
    def _zuletzt(self):
        sa, v = self._seite("Zuletzt verwendete öffnen")
        pfade = self.w.settings.recent()
        if not pfade:
            h = QLabel("Noch keine Dokumente geöffnet.")
            h.setObjectName("bsHinweis")
            v.addWidget(h)
        for p in pfade:
            k = QPushButton()
            k.setObjectName("bsKnopf")
            k.setCursor(Qt.PointingHandCursor)
            k.setText(os.path.basename(p))
            k.setToolTip(p)                                          # den Pfad zeigt nur der Tooltip
            sym = datei_symbol(p)                                    # Symbol des Dateiformats aus dem Icon-Theme des Systems
            k.setIcon(sym if not sym.isNull() else icons.icon("ausdatei", 28))
            k.setIconSize(QSize(28, 28))
            k.setEnabled(os.path.exists(p))
            k.clicked.connect(lambda _=False, p=p: (self.schliessen.emit(), self.w.open_path(p)))
            v.addWidget(k)
        if pfade:
            leer = QPushButton("Liste leeren")
            leer.setObjectName("bsKnopf")
            leer.setFixedWidth(BREITE)
            leer.clicked.connect(lambda: (self.w._clear_recent(), self.oeffnen("zuletzt")))
            v.addSpacing(8); v.addWidget(leer)
        v.addStretch(1)
        return sa

    def _speichern_als(self):
        sa, v = self._seite("Speichern als")
        self._gruppe(v, "Dokument", "Das Dokument unter neuem Namen oder als Kopie speichern.")
        self._knopf(v, "Speichern unter …", "speichernUnter", "speichern")
        self._knopf(v, "Kopie speichern …", "kopieSpeichern", "kopie")
        self._gruppe(v, "Exportieren", "Die Ausgabe wird als Datei geschrieben; das geöffnete Dokument bleibt unverändert.")
        for text, b in EXPORTE:
            self._knopf(v, text, b, "pdf" if b == "speichernPdf" else "ausdatei", datei=EXPORT_ENDUNG.get(b))
        v.addStretch(1)
        return sa

    def _vorlage(self) -> QWidget:
        """Platzhalter: die Galerie mit den Vorschauen wird erst gebaut, wenn die Seite gezeigt wird."""
        ph = QWidget()
        QVBoxLayout(ph).setContentsMargins(0, 0, 0, 0)
        ph._ansicht = None
        return ph

    def _vorlage_zeigen(self) -> None:
        from lunivo_writer.ui.baukasten.vorlagen_galerie import VorlagenGalerie
        ph = self.seiten["vorlage"]
        if ph._ansicht is None:
            g = VorlagenGalerie(self.w.settings, self.w.current_tab() is not None, self.w.benutzerdaten())
            g.gewaehlt.connect(lambda art, wert: (self.schliessen.emit(), self.w.neu_aus_wahl(art, wert)))
            g.als_vorlage.connect(lambda ziel: (self.schliessen.emit(), self.w.als_vorlage_speichern(ziel or None)))
            ph.layout().addWidget(g); ph._ansicht = g
        else:
            ph._ansicht.neu_lesen()

    def _drucken(self) -> QWidget:
        """Platzhalter: das Druckfenster samt Vorschau wird erst gebaut, wenn die Seite gezeigt wird."""
        ph = QWidget()
        QVBoxLayout(ph).setContentsMargins(0, 0, 0, 0)
        ph._ansicht = None
        return ph

    def _drucken_zeigen(self) -> None:
        ph = self.seiten["drucken"]
        t = self.w.current_tab()
        if ph._ansicht is not None or t is None:
            return
        v = ph.layout()
        ph._ansicht = self.w.druck_ansicht(t)
        v.addWidget(ph._ansicht, 1)
        fuss = QHBoxLayout(); fuss.setContentsMargins(14, 8, 14, 12)
        hilfe = QPushButton("Hilfe"); hilfe.clicked.connect(self.w.druck_hilfe)
        drucken = QPushButton("Drucken"); drucken.setObjectName("optFertig"); drucken.setDefault(True); drucken.setCursor(Qt.PointingHandCursor)
        drucken.setMinimumSize(100, 34); hilfe.setMinimumHeight(34)
        drucken.clicked.connect(lambda: (self.schliessen.emit(), self.w.drucke_nach_wahl(t, ph._ansicht.ergebnis())))
        ph._ansicht.geaendert.connect(lambda: drucken.setEnabled(ph._ansicht.gueltig()))
        fuss.addWidget(hilfe); fuss.addStretch(1); fuss.addWidget(drucken)
        v.addLayout(fuss)

    def _hilfe(self):
        sa, v = self._seite("Hilfe")
        self._knopf(v, "Handbuch", "handbuch", "buch")
        self._knopf(v, "Tastenkürzel", "tastenHilfe", "tasten")
        self._knopf(v, "Erweiterungen", "erweiterungen", "zahnrad")
        self._knopf(v, "Über Lunivo Writer", "ueber", "inhalt")
        v.addStretch(1)
        return sa

    def _schuetzen(self):
        sa, v = self._seite("Datei schützen")
        self._gruppe(v, "Mit Kennwort", "Verschlüsseln Sie dieses Dokument mit einem Kennwort. Das Kennwort wird beim nächsten Speichern wirksam.")
        self._knopf(v, "Kennwort hinzufügen / ändern …", "dokumentSchuetzen", "sperren")
        self._gruppe(v, "Bearbeitung", "Bearbeitung sperren oder freigeben — wirkt in diesem Fenster.")
        self._knopf(v, "Bearbeitung sperren / freigeben", "dokumentSchuetzen", "sperren")
        self._gruppe(v, "Mit Signatur", "Digitale Signaturen sind in dieser Fassung nicht enthalten.")
        k = QPushButton("Digitale Signatur hinzufügen")
        k.setObjectName("bsKnopf")
        k.setEnabled(False)
        k.setFixedWidth(BREITE)
        v.addWidget(k)
        v.addStretch(1)
        return sa

    def _info(self):
        sa, v = self._seite("Informationen zum Dokument")
        t = self.w.current_tab()
        if t is None:
            h = QLabel("Kein Dokument geöffnet.")
            h.setObjectName("bsHinweis")
            v.addWidget(h)
            v.addStretch(1)
            return sa
        ed = t.editor
        text = ed.document().toPlainText()
        absaetze = sum(1 for z in text.split("\n") if z.strip())
        groesse = os.path.getsize(t.path) if t.path and os.path.exists(t.path) else None
        self._gruppe(v, "Allgemein")
        for name, wert in (("Name", t.title), ("Ort", t.path or "noch nicht gespeichert"),
                           ("Größe", f"{groesse / 1024:.1f} KB" if groesse is not None else "–"),
                           ("Papier", f"{t.page.paper_name()} {'quer' if t.page.landscape else 'hoch'}")):
            self._zeile(v, name, QLabel(str(wert)))
        self._gruppe(v, "Statistiken")
        for name, wert in (("Seiten", ed.page_count), ("Absätze", absaetze), ("Wörter", ed.word_count()),
                           ("Zeichen", len(text.replace(" ", "").replace("\n", ""))), ("Zeichen mit Leerzeichen", len(text.replace("\n", "")))):
            self._zeile(v, name, QLabel(str(wert)))
        self._gruppe(v, "Eigenschaften", "Werden mit dem Dokument gespeichert (DOCX: Titel und Verfasser).")
        for schl, name in (("author", "Verfasser"), ("title", "Titel")):
            e = QLineEdit(t.meta.get(schl, "") or "")
            e.setFixedWidth(320)
            e.editingFinished.connect(lambda e=e, s=schl, t=t: self._meta_setzen(t, s, e.text()))
            self._zeile(v, name, e)
        v.addStretch(1)
        return sa

    def _meta_setzen(self, t, schl: str, wert: str):
        if (t.meta.get(schl, "") or "") != wert:
            t.meta[schl] = wert
            t.editor.document().setModified(True)

    @staticmethod
    def _zeile(v: QVBoxLayout, name: str, feld: QWidget):
        row = QHBoxLayout()
        n = QLabel(name)
        n.setFixedWidth(190)
        row.addWidget(n)
        row.addWidget(feld)
        row.addStretch(1)
        v.addLayout(row)

    def _oeffnen_mit(self):
        sa, v = self._seite("Öffnen mit …")
        self._gruppe(v, "Teilen")
        self._knopf(v, "Dokument teilen (optional)", "dokumentTeilen", "verknuepft")
        v.addStretch(1)
        return sa
