"""Optionen: Menüband, Schnellzugriff, Sicherheit."""
from __future__ import annotations

import json
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
from lunivo_writer.ui.baukasten.beschriftung import md_label
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import _Seite


class BefehleSeiten:
    """Optionen: Menüband, Schnellzugriff, Sicherheit. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


    def _zwei_listen(self, p, links_kopf: str, rechts_kopf: str, hinzu: str, weg: str, kategorie: str):
        """Gerüst der Vorlage: links „Befehle auswählen“ (Auswahl, Suche, Liste), in der Mitte Hinzufügen/Entfernen, rechts die Liste
        der aktuellen Einträge mit Pfeilen. Gibt (links, rechts, suche, b_hinzu, b_weg, auf, ab, unten) zurück."""
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 8, 0, 0); g.setHorizontalSpacing(14); g.setVerticalSpacing(6)
        g.setColumnStretch(0, 5); g.setColumnStretch(2, 5)
        g.addWidget(QLabel(links_kopf), 0, 0)
        kopf = QHBoxLayout()
        auswahl = QComboBox(); auswahl.addItem(kategorie)
        suche = QLineEdit(); suche.setPlaceholderText("Befehl suchen"); suche.setClearButtonEnabled(True)
        kopf.addWidget(auswahl, 1); kopf.addWidget(suche, 1)
        g.addLayout(kopf, 1, 0)
        links = QListWidget(); links.setMinimumHeight(250); links.setIconSize(QSize(18, 18))
        g.addWidget(links, 2, 0)
        mitte = QVBoxLayout(); mitte.addStretch(1)
        b_hinzu = QPushButton(hinzu); b_weg = QPushButton(weg)
        mitte.addWidget(b_hinzu); mitte.addWidget(b_weg); mitte.addStretch(1)
        g.addLayout(mitte, 2, 1)
        g.addWidget(QLabel(rechts_kopf), 0, 2)
        rechts = QListWidget(); rechts.setMinimumHeight(250); rechts.setIconSize(QSize(18, 18))
        pf = QVBoxLayout()
        auf = QPushButton("▲"); ab = QPushButton("▼")
        for b in (auf, ab):
            b.setFixedWidth(34)
        pf.addStretch(1); pf.addWidget(auf); pf.addWidget(ab); pf.addStretch(1)
        rz = QHBoxLayout(); rz.addWidget(rechts, 1); rz.addLayout(pf)
        g.addLayout(rz, 1, 2, 2, 1)
        unten = QHBoxLayout(); unten.setContentsMargins(0, 4, 0, 0)
        g.addLayout(unten, 3, 0, 1, 3)
        p.lay.addWidget(w)
        return links, rechts, suche, b_hinzu, b_weg, auf, ab, unten


    @staticmethod
    def _schieben(liste: QListWidget, d: int) -> None:
        i = liste.currentRow(); j = i + d
        if i < 0 or not 0 <= j < liste.count():
            return
        it = liste.takeItem(i)
        liste.insertItem(j, it)
        liste.setCurrentRow(j)


    def _menueband(self, titel):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import IMMER, lade_json
        from lunivo_writer.ui.ribbon.plan import plan
        from lunivo_writer.ui.ribbon.ribbon_bar import STANDARD_VERSTECKT
        p = _Seite(self.w, titel)
        links, rechts, suche, b_hinzu, b_weg, auf, ab, unten = self._zwei_listen(
            p, "Register, die ausgeblendet sind", "Menüband anpassen", "Hinzufügen", "Entfernen", "Ausgeblendete Register")
        namen = [r["name"] for r in plan(self.w.band.daten) if not r.get("kontext") and r["name"] not in IMMER]
        cfg = lade_json(self.w.settings, "ui/register_plan", {})
        reihenfolge = [n for n in cfg.get("reihenfolge", []) if n in namen] + [n for n in namen if n not in cfg.get("reihenfolge", [])]
        versteckt = set(cfg["versteckt"] if "versteckt" in cfg else STANDARD_VERSTECKT)
        for n in reihenfolge:
            (links if n in versteckt else rechts).addItem(n)

        def speichern():
            sichtbar = [rechts.item(i).text() for i in range(rechts.count())]
            weg = [links.item(i).text() for i in range(links.count())]
            self.w.settings.set("ui/register_plan", json.dumps({"reihenfolge": sichtbar + weg, "versteckt": weg}))
            self._band_merken()

        def verschiebe(von, nach):
            it = von.currentItem()
            if it is None or (nach is links and it.text() in IMMER):
                return
            if nach is links and rechts.count() <= 1 and von is rechts:
                return                                           # mindestens ein Register bleibt
            von.takeItem(von.row(it)); nach.addItem(it); nach.setCurrentItem(it)
            speichern()
        b_hinzu.clicked.connect(lambda: verschiebe(links, rechts))
        b_weg.clicked.connect(lambda: verschiebe(rechts, links))
        links.itemDoubleClicked.connect(lambda _i: verschiebe(links, rechts))
        auf.clicked.connect(lambda: (self._schieben(rechts, -1), speichern()))
        ab.clicked.connect(lambda: (self._schieben(rechts, 1), speichern()))
        suche.textChanged.connect(lambda t: [links.item(i).setHidden(t.lower() not in links.item(i).text().lower())
                                             for i in range(links.count())])
        from PySide6.QtWidgets import QMenu
        unten.addWidget(QLabel("Tastenkombinationen:"))
        tk = QPushButton("Anzeigen …")
        tk.clicked.connect(lambda: __import__("lunivo_writer.ui.dialogs.hilfe_dialoge", fromlist=["x"]).tastenkuerzel(self.w).show())
        unten.addWidget(tk); unten.addStretch(1)
        unten.addWidget(QLabel("Anpassungen:"))
        zr = QPushButton("Zurücksetzen ▾")
        m = QMenu(zr)
        m.addAction("Nur das Menüband", lambda: (self.w.settings.remove("ui/register_plan"), self._band_merken(), self._band_jetzt()))
        m.addAction("Alle Anpassungen (Register, Schnellzugriff, Symbole) …", self.w.befehle.vorlagenZurueck)
        zr.setMenu(m)
        unten.addWidget(zr)
        f = p.gruppe("Aussehen")
        for text, fn in (("Benutzeroberfläche wählen …", self.w.befehle.benutzeroberflaeche),
                         ("Symbole austauschen …", self.w.befehle.symbolTauschen)):
            b = QPushButton(text); b.clicked.connect(lambda _=False, fn=fn: fn()); f.addRow(b)
        p.abschluss()
        return p


    def _schnellzugriff(self, titel):
        from lunivo_writer.ui.dialogs.oberflaeche_dialoge import lade_json
        from lunivo_writer.ui.ribbon.ribbon_bar import RegisterBand
        from lunivo_writer.ui.widgets import icons
        p = _Seite(self.w, titel)
        links, rechts, suche, b_hinzu, b_weg, auf, ab, unten = self._zwei_listen(
            p, "Befehle auswählen", "Derzeit angezeigte Optionen", "Hinzufügen >>", "<< Entfernen", "Häufig verwendete Befehle")
        alle = {aktion: (sym, name) for sym, name, aktion in RegisterBand.SCHNELL_ALLE}
        vorgabe = [a for _s, _n, a in RegisterBand.SCHNELL]

        def eintrag(aktion):
            sym, name = alle[aktion]
            it = QListWidgetItem(icons.icon(sym, 18), name)
            it.setData(Qt.UserRole, aktion)
            return it

        def fuellen(aktuell):
            links.clear(); rechts.clear()
            for a in aktuell:
                if a in alle:
                    rechts.addItem(eintrag(a))
            for a in alle:
                if a not in aktuell:
                    links.addItem(eintrag(a))
        fuellen(lade_json(self.w.settings, "ui/schnellzugriff", None) or vorgabe)

        def speichern():
            self.w.settings.set("ui/schnellzugriff", json.dumps([rechts.item(i).data(Qt.UserRole) for i in range(rechts.count())]))
            self._band_merken()

        def verschiebe(von, nach):
            it = von.currentItem()
            if it is None:
                return
            von.takeItem(von.row(it)); nach.addItem(it); nach.setCurrentItem(it)
            speichern()
        b_hinzu.clicked.connect(lambda: verschiebe(links, rechts))
        b_weg.clicked.connect(lambda: verschiebe(rechts, links))
        links.itemDoubleClicked.connect(lambda _i: verschiebe(links, rechts))
        rechts.itemDoubleClicked.connect(lambda _i: verschiebe(rechts, links))
        auf.clicked.connect(lambda: (self._schieben(rechts, -1), speichern()))
        ab.clicked.connect(lambda: (self._schieben(rechts, 1), speichern()))
        suche.textChanged.connect(lambda t: [links.item(i).setHidden(t.lower() not in links.item(i).text().lower())
                                             for i in range(links.count())])
        unten.addStretch(1)
        zr = QPushButton("Zurücksetzen")
        zr.clicked.connect(lambda: (self.w.settings.remove("ui/schnellzugriff"), fuellen(vorgabe), self._band_merken()))
        unten.addWidget(zr)
        p.abschluss()
        return p


    def _sicherheit(self, titel):
        p = _Seite(self.w, titel)
        t = self.w.current_tab()
        f = p.gruppe("Kennwortschutz")
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 4, 0, 4); g.setHorizontalSpacing(10); g.setVerticalSpacing(8)
        g.addWidget(QLabel("Dokumentkennwort"), 0, 0)
        k1 = QLineEdit(); k1.setEchoMode(QLineEdit.Password); k1.setPlaceholderText("Kennwort")
        k2 = QLineEdit(); k2.setEchoMode(QLineEdit.Password); k2.setPlaceholderText("Kennwort erneut eingeben")
        g.addWidget(k1, 0, 1); g.addWidget(k2, 0, 2)
        g.setColumnStretch(1, 1); g.setColumnStretch(2, 1)
        f.addRow(w)
        w.setProperty("optName", "Dokumentkennwort")
        stand = QLabel(); stand.setWordWrap(True)
        setzen = QPushButton("Kennwort setzen"); weg = QPushButton("Kennwort entfernen")
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(setzen); h.addWidget(weg); h.addStretch(1)
        f.addRow(zeile)
        f.addRow(stand)

        def zeige(meldung: str = ""):
            if not t:
                stand.setText("Kein Dokument geöffnet — das Kennwort gehört zum Dokument im aktuellen Fenster.")
            elif meldung:
                stand.setText(meldung)
            else:
                stand.setText("Das Dokument wird beim Speichern verschlüsselt." if t.meta.get("kennwort")
                              else "Ohne Kennwort — die Datei ist im Klartext lesbar.")
        for c in (k1, k2, setzen, weg):
            c.setEnabled(t is not None)

        def setze():
            if not k1.text():
                zeige("Bitte ein Kennwort eingeben."); return
            if k1.text() != k2.text():
                zeige("Die beiden Eingaben stimmen nicht überein."); return
            t.meta["kennwort"] = k1.text()
            t.editor.document().setModified(True)
            k1.clear(); k2.clear()
            zeige("Gesetzt — das Dokument wird ab dem nächsten Speichern verschlüsselt.")
        setzen.clicked.connect(setze)
        weg.clicked.connect(lambda: (t.meta.pop("kennwort", None), t.editor.document().setModified(True), k1.clear(), k2.clear(),
                                     zeige("Entfernt — gilt ab dem nächsten Speichern.")))
        zeige()
        warn = md_label("**Ein vergessenes Kennwort kann niemand wiederherstellen.** Bewahre es an einem sicheren Ort auf.")
        warn.setWordWrap(True); warn.setStyleSheet("color: palette(window-text);")
        f.addRow(warn)
        sperre = QCheckBox("Bearbeitung sperren")
        sperre.setChecked(bool(t and getattr(t, "gesperrt", False))); sperre.setEnabled(t is not None)
        sperre.toggled.connect(lambda on: t and on != bool(getattr(t, "gesperrt", False)) and self.w.toggle_sperre())
        f.addRow(sperre)
        f = p.gruppe("Datenschutz")
        p.haken(f, "sicherheit/markup_oeffnen", "Ausgeblendete Markups beim Öffnen anzeigen", True)
        p.haken(f, "sicherheit/personendaten_weg", "Beim Speichern persönliche Daten entfernen", False)
        p.abschluss()
        return p


    def _verfolgen(self, titel):
        p = _Seite(self.w, titel)
        f = p.gruppe("Änderungen verfolgen")
        b = QCheckBox("Änderungen im aktuellen Dokument verfolgen")
        e = self.w.current_editor()
        b.setChecked(bool(e and e.verfolgen)); b.setEnabled(e is not None)
        b.toggled.connect(lambda on: self.w.current_editor() and self.w.current_editor().set_verfolgen(on))
        f.addRow(b)
        m = QCheckBox("Markup anzeigen (Kommentare, Einfügungen, Löschungen)")
        m.setChecked(bool(e.markup) if e else True); m.setEnabled(e is not None)
        m.toggled.connect(lambda on: self.w.current_editor() and self.w.current_editor().set_markup(on))
        f.addRow(m)
        from lunivo_writer.editor import sprechblasen as SB
        from lunivo_writer.ui.document.zusatz_editor import DEL_STILE, FESTE_FARBEN, INS_STILE
        neu = lambda _=None: self.w.markup_neu()                                               # noqa: E731
        f = p.gruppe("Markup")
        p.auswahl(f, "aenderungen/ins_stil", "Einfügungen", INS_STILE, "Unterstrichen", neu)
        p.auswahl(f, "aenderungen/del_stil", "Löschvorgänge", DEL_STILE, "Durchgestrichen", neu)
        p.auswahl(f, "aenderungen/balken", "Geänderte Zeilen (Balken im Rand)", ["links", "rechts", "außen", "keine"], "links", neu)
        p.auswahl(f, "aenderungen/farbe", "Farbe", ["Nach Autor"] + list(FESTE_FARBEN), "Nach Autor", neu)
        f = p.gruppe("Sprechblasen")
        p.auswahl(f, "sprechblasen/verwenden", "Sprechblasen verwenden", SB.VERWENDEN, SB.STANDARD["verwenden"], neu)
        p.haken(f, "sprechblasen/empfohlen", "Empfohlene Breite verwenden (60 mm)", True, neu)
        p.zahl(f, "sprechblasen/breite_mm", "Bevorzugte Breite", 30, 120, 60, " mm", 1, neu)
        p.auswahl(f, "sprechblasen/rand", "Seitenrand", SB.RAND, "Rechts", neu)
        p.haken(f, "sprechblasen/linien", "Verbindungslinien zum Text anzeigen", True, neu)
        f = p.gruppe("Drucken (mit Sprechblasen)")
        p.haken(f, "sprechblasen/drucken", "Sprechblasen mitdrucken und exportieren", False)
        p.auswahl(f, "sprechblasen/ausrichtung", "Papierausrichtung", SB.AUSRICHTUNG, "Automatisch")
        p.hinweis("Einfügungen und Löschungen stehen in einer Farbe je Autor (oder in einer festen Farbe). Der Autor kommt aus "
                  "Optionen ▸ Benutzerinformationen. Änderungen und Kommentare werden in DOCX als echte Überarbeitungen gespeichert. "
                  "Beim Drucken mit Sprechblasen wird die Seite verkleinert, damit rechts oder links Platz für die Blasen bleibt.")
        p.abschluss()
        return p
