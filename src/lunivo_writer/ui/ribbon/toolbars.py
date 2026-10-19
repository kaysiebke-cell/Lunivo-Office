"""Oberfläche „Symbolleisten“: ☰ Menü + obere Leiste (Datei/Dokument) + untere Leiste (Text) + Zusammenhangsleiste.

Gleiche Schnittstelle
wie RegisterBand (aktualisieren, kontext, felder, menue_knopf), damit das Fenster beide gleich behandeln kann.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox, QFontComboBox, QFrame, QHBoxLayout, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.widgets import icons
from lunivo_writer.ui.contextual.image_tools import BILDTOOLS, FORMTOOLS
from lunivo_writer.ui.contextual.table_tools import TABELLENTOOLS
from lunivo_writer.ui.ribbon.ribbon_bar import NICHT_DA, STILE_KATALOG

T = "trenner"
# (Symbol, Tooltip, Aktion)
OBEN = [
    ("neu", "Neu (Strg+N)", "neu"), ("oeffnen", "Öffnen (Strg+O)", "oeffnen"), ("speichern", "Speichern (Strg+S)", "speichern"),
    ("unter", "Speichern unter", "speichernUnter"), T,
    ("drucken", "Drucken (Strg+P)", "drucken"), ("vorschau", "Druckvorschau", "vorschau"),
    ("pdf", "Als PDF exportieren", "speichernPdf"), T,
    ("kleben", "Einfügen (Strg+V)", "einfuegen"), ("ohneformat", "Einfügen ohne Formatierung", "einfuegenOhne"),
    ("schere", "Ausschneiden (Strg+X)", "ausschneiden"), ("kopie", "Kopieren (Strg+C)", "kopieren"),
    ("pinsel", "Format übertragen", "formatUebertragen"), ("zurueck", "Rückgängig (Strg+Z)", "rueckgaengig"),
    ("vor", "Wiederholen (Strg+Y)", "wiederholen"), T,
    ("lupe", "Suchen und Ersetzen (Strg+F)", "suchen"), T,
    ("haken", "Prüfen (F7)", "rechtschreibung"), ("gruendlich", "Gründlich prüfen", "gruendlichPruefen"), T,
    ("umbruch", "Seitenumbruch (Strg+Enter)", "seitenumbruch"), ("tabelle", "Tabelle einfügen", "tabelleRaster"),
    ("bild", "Bild", "bild"), ("stift", "Formen", "formenGalerie"), ("saeule", "Diagramm", "diagramm"), T,
    ("kette", "Hyperlink", "hyperlink"), ("kopfz", "Kopfzeile", "kopfFussZeigen"), ("fussz", "Fußzeile", "fusszeileBearbeiten"),
    ("seitenzahl", "Seitenzahl", "seitenzahlKlappe"), T,
    ("textrahmen", "Textfeld", "textfeld"), ("omega", "Sonderzeichen", "sonderzeichen"), T,
    ("verfolgt", "Änderungen verfolgen", "verfolgen"), ("notiz", "Neuer Kommentar", "kommentar"), T,
    ("optionen", "Optionen (F9)", "w.optionenOeffnen"),
]
UNTEN_A = [("groesserA", "Schrift vergrößern", "schriftGroesser"), ("kleinerA", "Schrift verkleinern", "schriftKleiner"),
           ("radierer", "Formatierung löschen", "schlicht"), T,
           ("F", "Fett (Strg+B)", "fett"), ("K", "Kursiv (Strg+I)", "kursiv"), ("U", "Unterstrichen (Strg+U)", "unter"),
           ("S", "Durchgestrichen", "durch"), ("hoch", "Hochgestellt", "hoch"), ("tief", "Tiefgestellt", "tief"),
           ("marker", "Hervorheben", "hervorhebenJetzt"), ("farbe", "Schriftfarbe", "schriftfarbeJetzt"),
           ("Aa", "Groß-/Kleinschreibung", "schreibweise"), ("unterart", "Unterstreichungsart", "unterstrichArt"),
           ("texteffekt", "Texteffekte", "effekt"), T,
           ("punkte", "Aufzählung", "punkte"), ("zahlen", "Nummerierung", "zahlen"), ("weniger", "Einzug verringern", "einzugWeniger"),
           ("mehr", "Einzug vergrößern", "einzugMehr"), ("ebeneHoch", "Listenebene erhöhen", "ebeneHoeher"),
           ("ebeneTief", "Listenebene verringern", "ebeneTiefer"), ("links", "Linksbündig", "links"),
           ("mitte", "Zentriert", "mitte"), ("rechts", "Rechtsbündig", "rechts"), ("block", "Blocksatz", "block")]
UNTEN_B = [("rahmen", "Absatzrahmen", "absatzRahmen"), ("toenung", "Absatzschattierung", "absatzSchattierung"),
           ("sortieren", "Sortieren", "sortieren"), ("steuerzeichen", "Steuerzeichen", "steuerzeichenZeigen")]
ZEILENABSTAENDE = [("1.0", "1,0"), ("1.15", "1,15"), ("1.5", "1,5"), ("2.0", "2,0"), ("2.5", "2,5"), ("3.0", "3,0")]
GROESSEN = [8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72]
# Zeichen, die gar kein Symbol sind (F K U S) — als Buchstabe gezeigt
BUCHSTABEN = {"F": ("F", "bold"), "K": ("K", "italic"), "U": ("U", "underline"), "S": ("S", "strike")}


class Symbolleisten(QWidget):
    def __init__(self, befehle):
        super().__init__()
        self.b = befehle
        self.knoepfe: list[tuple[QToolButton, str | None, bool]] = []
        self.schalter: list[tuple[QToolButton, str]] = []
        self.felder: dict[str, QWidget] = {}
        self.kontext_index: dict = {}
        self.fehlend: list[str] = []
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 2, 6, 2)
        v.setSpacing(2)
        self.menue_knopf = QToolButton()
        self.menue_knopf.setText("☰ Menü ▾")
        self.menue_knopf.setAutoRaise(True)
        z1 = self._zeile(v)
        z1.addWidget(self.menue_knopf)
        self._trenner(z1)
        self._fuellen(z1, OBEN)
        z1.addStretch(1)
        z2 = self._zeile(v)
        stil = QComboBox(); stil.addItems(["Fließtext"] + [n for n in STILE_KATALOG if n not in ("Standard", "Kein Abstand")])
        stil.setFixedWidth(130)
        font = QFontComboBox(); font.setFixedWidth(160)
        groesse = QComboBox(); groesse.setEditable(True); groesse.setFixedWidth(60)
        groesse.addItems([str(x) for x in GROESSEN])
        self.felder.update(stil=stil, font=font, groesse=groesse)
        for w in (font, groesse):
            z2.addWidget(w)
        self._fuellen(z2, UNTEN_A)
        abstand = QComboBox()
        for wert, name in ZEILENABSTAENDE:
            abstand.addItem("Zeilen " + name, float(wert))
        abstand.addItem("Mehr…", "mehr")
        abstand.setFixedWidth(100)
        abstand.activated.connect(lambda _: self._abstand(abstand))
        z2.addWidget(abstand)
        self._fuellen(z2, UNTEN_B)
        self._trenner(z2)
        z2.addWidget(stil)
        z2.addStretch(1)
        self.zusammenhang = QWidget()
        self.z3 = QHBoxLayout(self.zusammenhang)
        self.z3.setContentsMargins(0, 0, 0, 0)
        self.z3.setSpacing(0)
        v.addWidget(self.zusammenhang)
        self.zusammenhang.hide()
        self._kontext_name = None
        linie = QFrame(); linie.setFrameShape(QFrame.HLine); linie.setFrameShadow(QFrame.Sunken)
        v.addWidget(linie)

    def _zeile(self, v) -> QHBoxLayout:
        h = QHBoxLayout(); h.setSpacing(0); h.setContentsMargins(0, 0, 0, 0)
        v.addLayout(h)
        return h

    def _trenner(self, h):
        s = QFrame(); s.setFrameShape(QFrame.VLine); s.setFrameShadow(QFrame.Sunken)
        h.addWidget(s)

    def _fuellen(self, h: QHBoxLayout, liste):
        for e in liste:
            if e == T:
                self._trenner(h)
                continue
            sym, tip, akt = e
            h.addWidget(self._knopf(sym, tip, akt))

    def _knopf(self, sym: str, tip: str, akt: str, haken: bool = False) -> QToolButton:
        k = QToolButton()
        k.setAutoRaise(True)
        a = QAction(k)
        if icons.hat(sym):
            a.setIcon(icons.icon(sym, 18))
            k.setIconSize(QSize(18, 18))
            k.setToolButtonStyle(Qt.ToolButtonIconOnly)
        else:
            a.setText(BUCHSTABEN.get(sym, (sym,))[0])
            f = k.font()
            if sym == "F": f.setBold(True)
            if sym == "K": f.setItalic(True)
            if sym == "U": f.setUnderline(True)
            if sym == "S": f.setStrikeOut(True)
            k.setFont(f)
            k.setMinimumWidth(28)
        a.setToolTip(tip)
        k.setDefaultAction(a)
        k.setToolTip(tip)
        ok = self.b.hat(akt)
        if ok:
            a.triggered.connect(lambda _=False, t=akt, kk=k: (self.b.tun(t, kk), self.aktualisieren()))
            if haken or self.b.zustand(akt) is not None:
                a.setCheckable(True)
                self.schalter.append((k, akt))
        else:
            k.setProperty("fehlt", True)
            k.setEnabled(False)
            k.setToolTip(NICHT_DA.format(tip.split(" (")[0]))
            self.fehlend.append(akt)
        self.knoepfe.append((k, akt, akt not in ("neu", "oeffnen", "w.optionenOeffnen")))
        return k

    def _abstand(self, box: QComboBox):
        w = box.currentData()
        if w == "mehr":
            self.b.w.paragraph_dialog()
        elif self.b.ed:
            self.b.ed.set_line_spacing(float(w))

    # ---- gleiche Schnittstelle wie RegisterBand ----------------------------------------------
    def kontext(self, name: str, sichtbar: bool) -> None:
        if name not in ("tabelle", "bild", "form"):
            return
        if sichtbar and self._kontext_name != name:
            self._kontext_name = name
            while self.z3.count():
                it = self.z3.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            plan = TABELLENTOOLS if name == "tabelle" else FORMTOOLS if name == "form" else BILDTOOLS
            for g in plan["gruppen"]:
                for e in g["knoepfe"]:
                    if e.get("symbol") == "//":
                        continue
                    if e.get("klappe") and not e.get("tun"):
                        fn = getattr(self.b, "menue_" + e["klappe"], None)
                        if fn:
                            kn = QToolButton(); kn.setAutoRaise(True); kn.setPopupMode(QToolButton.InstantPopup)
                            kn.setIcon(icons.icon(e["symbol"], 18)); kn.setToolTip(e["name"])
                            kn.setMenu(fn())
                            self.z3.addWidget(kn)
                        continue
                    if not e.get("tun"):
                        continue
                    self.z3.addWidget(self._knopf(e["symbol"], e["name"], e["tun"]))
                self._trenner(self.z3)
            self.z3.addStretch(1)
            self.zusammenhang.show()
        elif not sichtbar and self._kontext_name == name:
            self._kontext_name = None
            self.zusammenhang.hide()

    def aktualisieren(self, hat_dokument: bool | None = None) -> None:
        for k, name in self.schalter:
            a = k.defaultAction()
            a.blockSignals(True)
            a.setChecked(bool(self.b.zustand(name)))
            a.blockSignals(False)
        if hat_dokument is not None:
            for k, name, braucht in self.knoepfe:
                if braucht and not k.property("fehlt"):
                    k.setEnabled(hat_dokument)
