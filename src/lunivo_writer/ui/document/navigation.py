"""Die linke Seitenleiste: Suchen und ersetzen, Kommentare, Überschriften, Änderungen, Noten und Vorlesen — jedes als Feld mit Titel, Menü und ✕.

Die schmale Leiste mit den Symbolen links davon baut das Hauptfenster (``_leiste_links``); ein Klick auf ein Symbol zeigt das Feld, ein zweiter schließt es.
Alles, was hier geschieht, ruft die Funktionen des Editors (Suchen, Kommentare, Änderungen, Noten) und dieselben Befehle wie das Band (Vorlesen)."""
from __future__ import annotations

import datetime

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QActionGroup, QFont, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QPlainTextEdit, QPushButton, QScrollArea,
    QStackedWidget, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.panel_rahmen import PanelRahmen

SEITEN = ("suche", "kommentare", "ueberschriften", "aenderungen", "noten", "vorlesen")
TABS = SEITEN                                                             # alter Name
TITEL = {"suche": "Suchen und ersetzen", "kommentare": "Kommentare", "ueberschriften": "Überschriften", "aenderungen": "Änderungen",
         "noten": "Noten", "vorlesen": "Vorlesen"}
SORTIERUNG = (("neu", "Neueste zuerst"), ("alt", "Älteste zuerst"), ("az", "Verfasser (A–Z)"), ("za", "Verfasser (Z–A)"),
              ("oben", "Von oben"), ("unten", "Von unten"))
ANZEIGE = (("offen", "Offen"), ("geloest", "Gelöst"), ("alle", "Alle"))
SCHRIFT = (("klein", "Klein", 9.0), ("mittel", "Mittelgroß", 10.5), ("gross", "Groß", 13.0))
GRENZE = 5000                                                              # mehr Treffer zählen wir nicht


def _datum(iso: str) -> str:
    try:
        return datetime.datetime.fromisoformat(iso).astimezone().strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso or ""


class KommentarKarte(QFrame):
    """Ein Kommentar: Verfasser, Datum, Text und Zeigen / Bearbeiten / Gelöst / Löschen; beim Bearbeiten steht der Text in einem Eingabefeld."""

    def __init__(self, b: dict, k: dict, ed, aktualisieren, pt: float = 11.5, bearbeiten: bool = False, speichern=None, abbrechen=None, bearbeite_los=None):
        super().__init__()
        from lunivo_writer.editor.zusatz import kommentar_farbe
        from lunivo_writer.ui.widgets.flow_layout import FlowLayout
        self.setObjectName("kommentarKarte")
        geloest = bool(k.get("geloest"))
        farbe = kommentar_farbe(geloest)                                  # orange Kreis wie in der alten Fassung, gelöste grau
        self.setStyleSheet("QFrame#kommentarKarte { border: 1px solid palette(midlight); border-radius: 8px; background: rgba(128,128,128,0.06); }"
                           "QFrame#kommentarKarte QLabel { border: none; background: transparent; }")
        v = QVBoxLayout(self); v.setContentsMargins(10, 8, 10, 8); v.setSpacing(6)
        kopf = QHBoxLayout(); kopf.setSpacing(8)
        ini = QLabel((k.get("initialen") or (k.get("autor") or "?")[:1]).upper()[:2]); ini.setAlignment(Qt.AlignCenter); ini.setFixedSize(26, 26)
        ini.setStyleSheet(f"background: {farbe}; color: white; font-weight: bold; border-radius: 13px;")
        kopf.addWidget(ini)
        name = QLabel(k.get("autor", "?")); f = name.font(); f.setBold(True); f.setPointSizeF(pt); name.setFont(f)
        kopf.addWidget(name, 1)
        datum = QLabel(_datum(k.get("datum", ""))); datum.setStyleSheet("color: palette(mid);"); fd = datum.font(); fd.setPointSizeF(max(8.0, pt - 3)); datum.setFont(fd)
        kopf.addWidget(datum)
        v.addLayout(kopf)
        kid = int(b["wert"])
        self.kid = kid
        if bearbeiten:
            self.eingabe = QPlainTextEdit(k.get("text", "")); self.eingabe.setMinimumHeight(90)
            fe = self.eingabe.font(); fe.setPointSizeF(pt); self.eingabe.setFont(fe)
            v.addWidget(self.eingabe)
            z = QHBoxLayout(); z.setSpacing(6)
            ok = QPushButton("Speichern"); ok.clicked.connect(lambda: speichern(kid, self.eingabe.toPlainText().strip()))
            ab = QPushButton("Abbrechen"); ab.clicked.connect(lambda: abbrechen())
            z.addWidget(ok); z.addWidget(ab); z.addStretch(1)
            v.addLayout(z)
            return
        text = QLabel(k.get("text", "")); text.setWordWrap(True); text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ft = text.font(); ft.setPointSizeF(pt); text.setFont(ft)
        if geloest:
            text.setStyleSheet("color: palette(mid); text-decoration: line-through;")
        v.addWidget(text)
        feld = QWidget(); z = QHBoxLayout(feld); z.setContentsMargins(0, 0, 0, 0); z.setSpacing(5)                  # eine Zeile, die Knöpfe knapp geschnitten
        feld.setStyleSheet("QPushButton { padding: 4px 8px; font-size: 9pt; }")
        zeigen = QPushButton("Zeigen"); zeigen.clicked.connect(lambda: (ed.select_range(b["von"], b["bis"]), ed.ensureCursorVisible(), ed.setFocus()))
        bearb = QPushButton("Bearbeiten"); bearb.clicked.connect(lambda: bearbeite_los(kid))
        loesen = QPushButton("Wieder öffnen" if geloest else "Gelöst")
        loesen.clicked.connect(lambda: (ed.kommentar_geloest(kid, not geloest), aktualisieren()))
        weg = QPushButton("Löschen"); weg.clicked.connect(lambda: (ed.kommentar_loeschen(kid), aktualisieren()))
        for b_ in (zeigen, bearb, loesen, weg):
            z.addWidget(b_)
        z.addStretch(1)
        v.addWidget(feld)


class NavigationPanel(QWidget):
    zustandGeaendert = Signal()                  # sichtbar/unsichtbar oder anderes Feld — die Leiste links zeigt es an

    def __init__(self, get_editor, fenster=None):
        super().__init__()
        self.get_editor, self.fenster = get_editor, fenster
        self.settings = getattr(fenster, "settings", None)
        self.setFixedWidth(340)
        self.aktion = None                                                  # Rückruf (name, daten) → Hauptfenster
        self.zuletzt = "kommentare"
        self.sortierung = "neu"
        self.anzeige = "alle"
        self._bearbeite = None                                               # Kennung des Kommentars, der gerade bearbeitet wird
        self.liste: dict[str, QListWidget] = {}
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0)
        self.stapel = QStackedWidget(); v.addWidget(self.stapel)
        self._seiten: dict[str, PanelRahmen] = {}
        for key in SEITEN:
            r = getattr(self, "_bau_" + key)()
            r.schliessen.connect(self.hide)
            self._seiten[key] = r
            self.stapel.addWidget(r)
        self._t = QTimer(self); self._t.setSingleShot(True); self._t.setInterval(300); self._t.timeout.connect(self.aktualisieren)

    # ---- Steuerung ---------------------------------------------------------------------------------------------
    def zeige_tab(self, key: str) -> None:
        if key not in SEITEN:
            return
        self.zuletzt = key
        self.stapel.setCurrentWidget(self._seiten[key])
        self.aktualisieren()
        self.zustandGeaendert.emit()

    @property
    def aktuelle_seite(self) -> str:
        return next((k for k, r in self._seiten.items() if r is self.stapel.currentWidget()), "")

    def showEvent(self, e) -> None:
        super().showEvent(e); self.zustandGeaendert.emit()

    def hideEvent(self, e) -> None:
        super().hideEvent(e)
        ed = self.get_editor()
        if ed is not None:
            ed.set_suchtreffer([])                                       # die Suchmarkierung verschwindet mit dem Feld
        self.zustandGeaendert.emit()

    def spaeter(self) -> None:
        if self.isVisible():
            self._t.start()

    def aktualisieren(self) -> None:
        if self.aktuelle_seite == "suche" and self.suchfeld.text():
            self._zaehlen()
        self._ueberschriften()
        self._kommentare()
        self._aenderungen_und_noten()

    def anzahl(self, key: str) -> int:
        """Wie viele Einträge ein Feld gerade zeigt (für Tests und die Zähler)."""
        if key == "kommentare":
            return len(self._karten)
        return self.liste[key].count() if key in self.liste else 0

    # ---- Suchen und ersetzen ----------------------------------------------------------------------------------------
    def _bau_suche(self) -> PanelRahmen:
        r = PanelRahmen(TITEL["suche"])
        self.suchfeld = QLineEdit(); self.suchfeld.setPlaceholderText("Suchen"); self.suchfeld.setClearButtonEnabled(True)
        self.ersatzfeld = QLineEdit(); self.ersatzfeld.setPlaceholderText("Ersetzen durch")
        for f in (self.suchfeld, self.ersatzfeld):
            f.setMinimumHeight(34); r.inhalt.addWidget(f)
        zeile = QHBoxLayout()
        self.treffer = QLabel("Keine Suchergebnisse"); self.treffer.setStyleSheet("color: palette(mid);")
        zeile.addWidget(self.treffer, 1)
        self.hoch = QToolButton(); self.hoch.setText("▲"); self.hoch.setToolTip("Vorheriger Treffer"); self.hoch.setAutoRaise(True)
        self.runter = QToolButton(); self.runter.setText("▼"); self.runter.setToolTip("Nächster Treffer"); self.runter.setAutoRaise(True)
        for b in (self.hoch, self.runter):
            b.setFixedSize(30, 30); zeile.addWidget(b)
        r.inhalt.addLayout(zeile)
        knoepfe = QHBoxLayout()
        self.ersetzen = QPushButton("Ersetzen"); self.alle_ersetzen = QPushButton("Alle ersetzen")
        for b in (self.ersetzen, self.alle_ersetzen):
            b.setMinimumHeight(32); knoepfe.addWidget(b)
        knoepfe.addStretch(1)
        r.inhalt.addLayout(knoepfe)
        self.gross = QCheckBox("Groß-/Kleinschreibung beachten"); self.ganz = QCheckBox("Nur ganze Wörter")
        r.inhalt.addWidget(self.gross); r.inhalt.addWidget(self.ganz)
        r.inhalt.addStretch(1)
        self.suchfeld.textChanged.connect(lambda _t: self._zaehlen())
        self.gross.toggled.connect(lambda _a: self._zaehlen()); self.ganz.toggled.connect(lambda _a: self._zaehlen())
        self.suchfeld.returnPressed.connect(lambda: self._weiter(False))
        self.runter.clicked.connect(lambda: self._weiter(False)); self.hoch.clicked.connect(lambda: self._weiter(True))
        self.ersetzen.clicked.connect(self._ersetzen_eins); self.alle_ersetzen.clicked.connect(self._ersetzen_alle)
        return r

    def suche_zeigen(self, text: str = "") -> None:
        """Das Feld öffnen, die Markierung (oder ``text``) einsetzen und in das Suchfeld springen."""
        ed = self.get_editor()
        if not text and ed is not None and ed.textCursor().hasSelection():
            text = ed.textCursor().selectedText().replace(" ", " ")
        if text:
            self.suchfeld.setText(text)
        self.show(); self.zeige_tab("suche")
        self.suchfeld.setFocus(); self.suchfeld.selectAll()

    def _treffer_starts(self, ed) -> list[int]:
        text = self.suchfeld.text()
        if not text:
            return []
        flags = QTextDocument.FindFlag(0)
        if self.gross.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.ganz.isChecked():
            flags |= QTextDocument.FindWholeWords
        doc, pos, out = ed.document(), 0, []
        while len(out) < GRENZE:
            c = doc.find(text, pos, flags)
            if c.isNull():
                break
            out.append(c.selectionStart())
            pos = max(c.selectionEnd(), pos + 1)
        return out

    def _zaehlen(self) -> None:
        ed = self.get_editor()
        if ed is None or not self.suchfeld.text():
            self.treffer.setText("Keine Suchergebnisse")
            if ed is not None:
                ed.set_suchtreffer([])
            return
        starts = self._treffer_starts(ed)
        n = len(self.suchfeld.text())
        ed.set_suchtreffer([(s, s + n) for s in starts])                # alle Treffer im Text farbig
        if not starts:
            self.treffer.setText("Keine Suchergebnisse"); return
        sel = ed.textCursor()
        nr = sum(1 for s in starts if s < sel.selectionStart()) + (1 if sel.hasSelection() and sel.selectionStart() in starts else 0)
        self.treffer.setText(f"{nr} von {len(starts)}" if nr else f"{len(starts)} Treffer")

    def _weiter(self, rueckwaerts: bool) -> None:
        ed = self.get_editor()
        if ed is None or not self.suchfeld.text():
            return
        ok = ed.find_text(self.suchfeld.text(), rueckwaerts, self.gross.isChecked(), self.ganz.isChecked())
        if ok:
            ed.ensureCursorVisible()
            self._zaehlen()
        else:
            self.treffer.setText("Keine Suchergebnisse")

    def _ersetzen_eins(self) -> None:
        ed = self.get_editor()
        if ed is not None and self.suchfeld.text():
            if not ed.replace_current(self.suchfeld.text(), self.ersatzfeld.text(), self.gross.isChecked()):
                self._weiter(False)                       # nichts Passendes markiert: erst zum nächsten Treffer
                return
            self._weiter(False)

    def _ersetzen_alle(self) -> None:
        ed = self.get_editor()
        if ed is not None and self.suchfeld.text():
            n = ed.replace_all(self.suchfeld.text(), self.ersatzfeld.text(), self.gross.isChecked(), self.ganz.isChecked())
            self.treffer.setText(f"{n} Ersetzung(en)" if n else "Keine Suchergebnisse")

    # ---- Kommentare --------------------------------------------------------------------------------------------------
    def _bau_kommentare(self) -> PanelRahmen:
        m = QMenu(self)
        gs = QActionGroup(m); gs.setExclusive(True)
        for key, text in SORTIERUNG:
            a = m.addAction(text); a.setCheckable(True); a.setChecked(key == self.sortierung); gs.addAction(a)
            a.triggered.connect(lambda _=False, k=key: self._sortieren(k))
        m.addSeparator()
        sub = m.addMenu("Kommentare anzeigen")
        ga = QActionGroup(sub); ga.setExclusive(True)
        for key, text in ANZEIGE:
            a = sub.addAction(text); a.setCheckable(True); a.setChecked(key == self.anzeige); ga.addAction(a)
            a.triggered.connect(lambda _=False, k=key: self._anzeigen(k))
        m.addSeparator()
        sg2 = m.addMenu("Schriftgröße")
        gz = QActionGroup(sg2); gz.setExclusive(True)
        aktuell_k = self._einstellung("kommentare/schrift", "mittel")
        for key, text, _pt in SCHRIFT:
            a = sg2.addAction(text); a.setCheckable(True); a.setChecked(key == aktuell_k); gz.addAction(a)
            a.triggered.connect(lambda _=False, k=key: self._kommentar_schrift(k))
        m.addSeparator()
        m.addAction("Kommentar zum Dokument hinzufügen", self._neu_zeigen)
        r = PanelRahmen(TITEL["kommentare"], "⋯", m, knoepfe=(("＋", "Kommentar hinzufügen", self._neu_zeigen),))
        self._karten: list[KommentarKarte] = []
        host = QWidget(); self._karten_layout = QVBoxLayout(host); self._karten_layout.setContentsMargins(0, 0, 0, 0); self._karten_layout.setSpacing(8)
        self._karten_layout.addStretch(1)
        self.kommentar_leer = QLabel("Das Dokument enthält keine Kommentare."); self.kommentar_leer.setWordWrap(True)
        self.kommentar_leer.setStyleSheet("color: palette(mid);")
        self._karten_layout.insertWidget(0, self.kommentar_leer)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame); sc.setWidget(host)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        r.inhalt.addWidget(sc, 1)
        # Eingabe eines neuen Kommentars
        self.neu_feld = QFrame(); nv = QVBoxLayout(self.neu_feld); nv.setContentsMargins(0, 0, 0, 0); nv.setSpacing(6)
        self.neu_text = QPlainTextEdit(); self.neu_text.setPlaceholderText("Geben Sie Ihren Kommentar hier ein"); self.neu_text.setFixedHeight(80)
        nv.addWidget(self.neu_text)
        nz = QHBoxLayout()
        self.neu_ok = QPushButton("Kommentar hinzufügen"); self.neu_ok.setEnabled(False)
        ab = QPushButton("Abbrechen")
        nz.addWidget(self.neu_ok); nz.addWidget(ab); nz.addStretch(1)
        nv.addLayout(nz)
        self.neu_feld.hide()
        r.inhalt.addWidget(self.neu_feld)
        self.neu_text.textChanged.connect(lambda: self.neu_ok.setEnabled(bool(self.neu_text.toPlainText().strip())))
        self.neu_ok.clicked.connect(self._neu_speichern)
        ab.clicked.connect(self._neu_schliessen)
        return r

    def _kommentar_schrift(self, key: str) -> None:
        """Schriftgröße der Kommentare: in den Karten hier und in den Blasen am Seitenrand."""
        self._merke("kommentare/schrift", key)
        if self.fenster is not None:
            for t in self.fenster._doc_tabs():
                t.editor._blasen_cache = (None, [])
                t.editor.viewport().update()
                fl = getattr(t.editor, "_blasen_flaeche", None)
                if fl is not None:
                    fl.update()
        self._kommentare()

    def kommentar_bearbeiten(self, kid: int) -> None:
        """Den Kommentar in seiner Karte bearbeiten (Doppelklick auf die Blase oder „Bearbeiten“)."""
        self._bearbeite = kid
        self.show(); self.zeige_tab("kommentare")
        self._kommentare()
        for k in self._karten:
            if k.kid == kid and hasattr(k, "eingabe"):
                k.eingabe.setFocus()

    def _bearbeiten_speichern(self, kid: int, text: str) -> None:
        ed = self.get_editor()
        if ed is not None and text:
            ed.kommentar_text_setzen(kid, text)
        self._bearbeite = None
        self._kommentare()

    def _bearbeiten_abbrechen(self) -> None:
        self._bearbeite = None
        self._kommentare()

    def _sortieren(self, key: str) -> None:
        self.sortierung = key; self._kommentare()

    def _anzeigen(self, key: str) -> None:
        self.anzeige = key; self._kommentare()

    def _neu_zeigen(self) -> None:
        self.show(); self.zeige_tab("kommentare")
        self.neu_feld.show(); self.neu_text.setFocus()

    def _neu_schliessen(self) -> None:
        self.neu_text.clear(); self.neu_feld.hide()

    def _neu_speichern(self) -> None:
        ed = self.get_editor()
        text = self.neu_text.toPlainText().strip()
        if ed is None or not text:
            return
        if ed.kommentar_neu(text) is None:
            if self.fenster is not None:
                self.fenster.statusBar().showMessage("Zum Kommentieren Text markieren oder in ein Wort klicken.", 5000)
            return
        self._neu_schliessen()
        self._kommentare()

    def _kommentare(self) -> None:
        for k in self._karten:
            self._karten_layout.removeWidget(k); k.hide(); k.setParent(None); k.deleteLater()
        self._karten = []
        ed = self.get_editor()
        eintraege = []
        if ed is not None:
            for b in ed.kommentar_bereiche():
                k = ed.kommentare.get(int(b["wert"]))
                if k is None:
                    continue
                if self.anzeige == "offen" and k.get("geloest") or self.anzeige == "geloest" and not k.get("geloest"):
                    continue
                eintraege.append((b, k))
        schluessel = {"neu": (lambda e: e[1].get("datum", ""), True), "alt": (lambda e: e[1].get("datum", ""), False),
                      "az": (lambda e: e[1].get("autor", "").lower(), False), "za": (lambda e: e[1].get("autor", "").lower(), True),
                      "oben": (lambda e: e[0]["von"], False), "unten": (lambda e: e[0]["von"], True)}[self.sortierung]
        eintraege.sort(key=schluessel[0], reverse=schluessel[1])
        for i, (b, k) in enumerate(eintraege):
            from lunivo_writer.editor.sprechblasen import karten_pt
            karte = KommentarKarte(b, k, ed, self.aktualisieren, karten_pt(self._einstellung("kommentare/schrift", "mittel")),
                                   bearbeiten=int(b["wert"]) == self._bearbeite, speichern=self._bearbeiten_speichern,
                                   abbrechen=self._bearbeiten_abbrechen, bearbeite_los=self.kommentar_bearbeiten)
            self._karten_layout.insertWidget(i, karte)
            self._karten.append(karte)
        gesamt = len(ed.kommentare) if ed is not None else 0
        self.kommentar_leer.setVisible(not self._karten)
        self.kommentar_leer.setText("Das Dokument enthält keine Kommentare." if not gesamt else "Keine Kommentare in dieser Ansicht.")

    # ---- Überschriften -----------------------------------------------------------------------------------------------
    def _bau_ueberschriften(self) -> PanelRahmen:
        m = QMenu(self)
        m.addAction("Alle ausklappen", lambda: self.baum.expandAll())
        m.addAction("Alle einklappen", lambda: self.baum.collapseAll())
        ebene = m.addMenu("Auf Ebene erweitern")
        for n in range(1, 10):
            ebene.addAction(str(n), lambda _=False, n=n: self._ebene(n))
        m.addSeparator()
        sg = m.addMenu("Schriftgröße")
        grp = QActionGroup(sg); grp.setExclusive(True)
        aktuell = self._einstellung("navigation/schrift", "mittel")
        for key, text, _pt in SCHRIFT:
            a = sg.addAction(text); a.setCheckable(True); a.setChecked(key == aktuell); grp.addAction(a)
            a.triggered.connect(lambda _=False, k=key: self._schrift(k))
        self._umbruch = m.addAction("Lange Überschriften umbrechen"); self._umbruch.setCheckable(True)
        self._umbruch.setChecked(str(self._einstellung("navigation/umbrechen", "1")) in ("1", "true", "True"))
        self._umbruch.toggled.connect(self._umbrechen)
        r = PanelRahmen(TITEL["ueberschriften"], "⚙", m)
        self.baum = QTreeWidget(); self.baum.setHeaderHidden(True); self.baum.setFrameShape(QFrame.NoFrame)
        self.baum.itemClicked.connect(self._klick)
        self.baum.setUniformRowHeights(False)
        self._schrift(aktuell, speichern=False); self._umbrechen(self._umbruch.isChecked(), speichern=False)
        r.inhalt.addWidget(self.baum, 1)
        self.leer = QLabel("Dieses Dokument enthält keine Überschriften. Wenden Sie ein Überschriftenformat auf den Text an, damit er hier angezeigt wird.")
        self.leer.setWordWrap(True); self.leer.setStyleSheet("color: palette(mid);")
        r.inhalt.addWidget(self.leer)
        return r

    def _einstellung(self, key: str, std):
        return self.settings.get(key, std) if self.settings is not None else std

    def _merke(self, key: str, wert) -> None:
        if self.settings is not None:
            self.settings.set(key, wert)

    def _schrift(self, key: str, speichern: bool = True) -> None:
        pt = next((p for k, _t, p in SCHRIFT if k == key), 10.5)
        f = QFont(self.baum.font()); f.setPointSizeF(pt); self.baum.setFont(f)
        if speichern:
            self._merke("navigation/schrift", key)

    def _umbrechen(self, an: bool, speichern: bool = True) -> None:
        self.baum.setWordWrap(bool(an))
        self.baum.setTextElideMode(Qt.ElideNone if an else Qt.ElideRight)
        self.baum.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff if an else Qt.ScrollBarAsNeeded)
        if speichern:
            self._merke("navigation/umbrechen", "1" if an else "0")

    def _ebene(self, n: int) -> None:
        """Alles bis zur Ebene ``n`` aufklappen, tiefere Ebenen zuklappen."""
        def lauf(it, tiefe):
            for i in range(it.childCount()):
                kind = it.child(i)
                kind.setExpanded(tiefe + 1 < n)
                lauf(kind, tiefe + 1)
        wurzel = self.baum.invisibleRootItem()
        for i in range(wurzel.childCount()):
            top = wurzel.child(i); top.setExpanded(n > 1); lauf(top, 1)

    def _ueberschriften(self) -> None:
        self.baum.clear()
        ed = self.get_editor()
        if ed is None:
            self.leer.show()
            return
        eltern = {0: self.baum.invisibleRootItem()}
        b = ed.document().firstBlock()
        n = 0
        while b.isValid():
            lvl = b.blockFormat().headingLevel()
            if lvl and b.text().strip():
                it = QTreeWidgetItem([b.text().strip()])
                it.setData(0, Qt.UserRole, b.position())
                p = eltern.get(lvl - 1) or eltern[max(k for k in eltern if k < lvl)]
                p.addChild(it)
                eltern[lvl] = it
                for k in [k for k in eltern if k > lvl]:
                    del eltern[k]
                n += 1
            b = b.next()
        self.baum.expandAll()
        self.leer.setVisible(n == 0)

    def _klick(self, item, _col) -> None:
        ed = self.get_editor()
        if ed is not None:
            pos = item.data(0, Qt.UserRole)
            ed.select_range(pos, pos)
            ed.ensureCursorVisible()

    # ---- Änderungen und Noten ------------------------------------------------------------------------------------------
    def _bau_liste(self, key: str, knoepfe: tuple) -> PanelRahmen:
        r = PanelRahmen(TITEL[key])
        lw = QListWidget(); lw.setWordWrap(True); lw.setFrameShape(QFrame.NoFrame)
        lw.itemClicked.connect(lambda it, k=key: self._springe(k, it))
        r.inhalt.addWidget(lw, 1)
        reihe = QHBoxLayout()
        for text, name in knoepfe:
            b = QPushButton(text); b.setMinimumHeight(32)
            b.clicked.connect(lambda _=False, n=name, k=key: self._aktion(n, k))
            reihe.addWidget(b)
        reihe.addStretch(1)
        r.inhalt.addLayout(reihe)
        self.liste[key] = lw
        return r

    def _bau_aenderungen(self) -> PanelRahmen:
        return self._bau_liste("aenderungen", (("Annehmen", "aenderung_an"), ("Ablehnen", "aenderung_ab")))

    def _bau_noten(self) -> PanelRahmen:
        return self._bau_liste("noten", (("Bearbeiten …", "note_bearbeiten"), ("Löschen", "note_weg")))

    def _aenderungen_und_noten(self) -> None:
        ed = self.get_editor()
        for k in ("aenderungen", "noten"):
            self.liste[k].clear()
        if ed is None:
            return
        text_ges = ed.document().toPlainText()
        for b in ed.aenderungen():
            text = text_ges[b["von"]:b["bis"]]
            art = "Eingefügt" if b["wert"] == "ins" else "Gelöscht"
            it = QListWidgetItem(f"{art} von {b['cf'].stringProperty(0x100000 + 23) or '?'}: „{text[:50]}“")
            it.setData(Qt.UserRole, b)
            self.liste["aenderungen"].addItem(it)
        zaehler = {"f": 0, "e": 0}
        for s in ed.noten_stellen():
            zaehler[s["art"]] += 1
            txt = ed.noten[s["art"]].get(s["id"], "")
            it = QListWidgetItem(("Fußnote " if s["art"] == "f" else "Endnote ") + f"{zaehler[s['art']]}: {txt[:80]}")
            it.setData(Qt.UserRole, s)
            self.liste["noten"].addItem(it)

    def _springe(self, key, item) -> None:
        ed = self.get_editor()
        b = item.data(Qt.UserRole)
        if ed is not None and b:
            ed.select_range(b["von"], b["bis"])
            ed.ensureCursorVisible()
            ed.setFocus()

    def _aktion(self, name, key) -> None:
        it = self.liste[key].currentItem()
        if it is None or self.aktion is None:
            return
        self.aktion(name, it.data(Qt.UserRole))

    # ---- Vorlesen ------------------------------------------------------------------------------------------------------
    def _bau_vorlesen(self) -> PanelRahmen:
        r = PanelRahmen(TITEL["vorlesen"])
        if self.fenster is not None:
            from lunivo_writer.ui.baukasten.werkbank import Werkbank
            wb = Werkbank(self.fenster, "Lesen", nur={"vorlesen", "vorlesenAbSatz", "vorlesenStopp", "stimmeWaehlen"})
            r.inhalt.addWidget(wb, 1)
            self.vorlesen_zeilen = wb
        return r
