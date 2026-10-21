"""„Neue Formatvorlage“ als Baustein: Eigenschaften (Name, Typ, basiert auf, folgender Absatz), die Formatierungsleiste aus dem Band
(``TextFormatLeiste``), eine Vorschau mit vorhergehendem und folgendem Absatz und das Menü „Format“.

    d = FormatvorlageDialog(parent, start={"groesse": 11, ...}, vorlagen=["Standard", ...])
    if d.exec(): d.ergebnis()   # {"name", "basis", "folge", "groesse", "fett", ...}

Das Fenster legt nichts an; es liefert die Werte, der Aufrufer ruft ``stile.anlegen``.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QVBoxLayout, QWidget,
)

from lunivo_writer.editor import stile
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche, fussleiste
from lunivo_writer.ui.baukasten.farbpalette import weitere_farben
from lunivo_writer.ui.baukasten.mass_feld import MassSpin, spin
from lunivo_writer.ui.baukasten.text_format import TextFormatLeiste, zeichne_absaetze, zu_format

ZEICHEN_ZUSATZ = ("unter", "unterfarbe", "durch", "doppelt", "hoch", "tief", "kapital", "gross", "versteckt", "abstand", "kerning", "betonung", "schrift_asien",
                  "schnitt_asien", "groesse_asien", "schrift_komplex", "schnitt_komplex", "groesse_komplex", "skala", "position", "kern_ab", "raster")
ABSATZ_ZUSATZ = ("rechts", "erste", "rtl", "umbruch", "zeilen_art", "zeilen_pt", "gliederung", "opt")
RAHMEN_FELDER = ("rahmen", "fuell", "muster", "musterfarbe", "liste", "effekt", "tabs") + ZEICHEN_ZUSATZ + ABSATZ_ZUSATZ      # Felder, die nicht zur Leiste gehören
KEINE = "(keine)"
GLEICHE = "(dieselbe Vorlage)"


class FormatvorlageDialog(QDialog):
    def __init__(self, parent=None, *, start: dict | None = None, vorlagen: list[str] | None = None, name: str = "Formatvorlage1",
                 basis: str = "Standard", aendern: str | None = None, belegt=None, standard_tab_mm: float | None = None):
        """``aendern``: Name einer vorhandenen Vorlage — dann ist es das Fenster „Formatvorlage ändern“ (Name fest)."""
        super().__init__(parent)
        self.aendern = aendern
        self._tab_std = standard_tab_mm                              # Standardtabstopps des Dokuments (mm); nur hier einzustellen, gilt für das Dokument
        self._tab_std_neu = None
        self._belegt = belegt                                       # Funktion (Taste, eigener Name) → Name, der sie schon hat, oder None
        self._taste = (start or {}).get("taste", "")
        self.setWindowTitle("Formatvorlage ändern" if aendern else "Neue Formatvorlage")
        self.resize(614, 520)
        self._farbe = (start or {}).get("farbe", "")
        self._rs = {k: (start or {}).get(k, stile.VORLAGE[k]) for k in RAHMEN_FELDER}      # Rahmen und Schattierung (kein Feld der Leiste)
        v = QVBoxLayout(self)
        # --- Eigenschaften
        eig = QGroupBox("Eigenschaften"); f = QFormLayout(eig)
        self.name = QLineEdit(aendern or self._freier_name(name))
        self.name.setReadOnly(bool(aendern))
        self.typ = QComboBox(); self.typ.addItem("Absatz")
        namen = [n for n in (vorlagen if vorlagen is not None else stile.namen()) if n != aendern]
        self.basis = QComboBox(); self.basis.addItem(KEINE, ""); [self.basis.addItem("↵ " + n, n) for n in namen]
        self.folge = QComboBox(); self.folge.addItem(GLEICHE, ""); [self.folge.addItem("↵ " + n, n) for n in namen]
        f.addRow("Name:", self.name); f.addRow("Formatvorlagentyp:", self.typ)
        f.addRow("Formatvorlage basiert auf:", self.basis); f.addRow("Formatvorlage für folgenden Absatz:", self.folge)
        self.hinweis = QLabel(); self.hinweis.setStyleSheet("color: #e8590c;")
        f.addRow(self.hinweis)
        v.addWidget(eig)
        # --- Formatierung (dieselbe Leiste wie im Band)
        fo = QGroupBox("Formatierung"); fv = QVBoxLayout(fo)
        self.leiste = TextFormatLeiste()
        fv.addWidget(self.leiste)
        self.vorschau = VorschauFlaeche(self._male, 118)
        self._w: dict = {}
        fv.addWidget(self.vorschau)
        v.addWidget(fo)
        # --- Zur Vorlage hinzufügen, Knöpfe
        self.zur_vorlage = QCheckBox("Zur Vorlage hinzufügen")
        self.zur_vorlage.setToolTip("Die Formatvorlage auch für künftige Dokumente merken (sonst gilt sie nur, solange Lunivo läuft, und in den Dokumenten, die sie benutzen)")
        self.zur_vorlage.setVisible(not aendern)
        v.addWidget(self.zur_vorlage)
        self.format = QPushButton("Format ▾")
        m = QMenu(self.format)
        m.addAction("Schriftart …", self._schriftart); m.addAction("Absatz …", self._absatz); m.addAction("Tabstopps …", self._tabs); m.addAction("Rahmen …", self._rahmen); m.addAction("Nummerierung …", self._liste); m.addAction("Texteffekte …", self._effekte); m.addAction("Verknüpfung …", self._verknuepfung)
        self.format.setMenu(m)
        self.ok = fussleiste(self, v, self.format, bei_ok=self._ok)
        # --- Anfangswerte und Verdrahtung
        if aendern:
            e = stile._NEU.get(aendern, {})
            basis, start = e.get("basis", ""), stile.definition(aendern)
            self.folge.setCurrentIndex(max(0, self.folge.findData(e.get("folge", ""))))
            if aendern not in stile._NEU:                           # eingebaute Vorlagen haben weder Basis noch Folgevorlage
                self.basis.setEnabled(False); self.folge.setEnabled(False)
            self._farbe = start.get("farbe", "")
            self._rs = {k: start.get(k, stile.VORLAGE[k]) for k in RAHMEN_FELDER}
            self._taste = start.get("taste", "")
        self.basis.setCurrentIndex(max(0, self.basis.findData(basis if basis in namen else "")))
        self.leiste.setze({**stile.definition("Standard"), **(start or {})} if not start else start)
        if not self.leiste.werte()["groesse"]:
            self.leiste.groesse.setCurrentText("11")                # wie im WPS steht eine Größe da, nicht ein leeres Feld
        self.leiste.geaendert.connect(self._neu)
        self.basis.currentIndexChanged.connect(self._basis_geaendert)
        self.name.textChanged.connect(self._pruefen)
        self._neu(); self._pruefen()

    @staticmethod
    def _freier_name(wunsch: str) -> str:
        n, i = wunsch, 1
        base = wunsch.rstrip("0123456789") or "Formatvorlage"
        while stile.pruefe_name(n):
            i += 1
            n = f"{base}{i}"
            if i > 999:
                break
        return n

    # ---- Verhalten
    def _felder(self) -> dict:
        return {**self.leiste.werte(), "farbe": self._farbe, **self._rs}

    def _neu(self, *_) -> None:
        self._w = self._felder()
        self.vorschau.update()

    def _male(self, p, rect) -> None:
        """Vorhergehender Absatz (grau), Beispieltext in der Vorlage, folgender Absatz (grau)."""
        d = self._w
        grau = QTextCharFormat(); grau.setForeground(QColor("#868e96")); grau.setFontPointSize(7.5); grau.setFontFamilies(["Liberation Sans"])
        bf = QTextBlockFormat()
        bf.setTopMargin(max(0.0, d.get("vor", 0)) / 0.75); bf.setBottomMargin(max(0.0, d.get("nach", 0)) / 0.75)
        bf.setLeftMargin(max(0.0, d.get("einzug", 0)) * 3.78)
        if d.get("zeilen"):
            bf.setLineHeight(d["zeilen"] * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        bf.setAlignment({"mitte": Qt.AlignHCenter, "rechts": Qt.AlignRight, "block": Qt.AlignJustify}.get(d.get("ausr"), Qt.AlignLeft))
        f = zu_format({**d, "groesse": min(18.0, max(7.0, d.get("groesse") or 10.0)), "schrift": d.get("schrift") or "Liberation Sans"})
        f.setForeground(QColor(d.get("farbe") or "#111417"))
        if d.get("fuell") or d.get("muster"):
            from lunivo_writer.editor import muster as M
            bf.setBackground(M.pinsel(d["muster"], d.get("musterfarbe") or "#000000", d.get("fuell") or None) if d.get("muster")
                             else QColor(d["fuell"]))
        zeichne_absaetze(p, rect, [(QTextBlockFormat(), grau, "Vorhergehender Absatz " * 6), (bf, f, "Beispieltext " * 14),
                                   (QTextBlockFormat(), grau, "Folgender Absatz " * 6)])

    def _basis_geaendert(self) -> None:
        """Eine andere Basis: ihre Werte sind der neue Ausgangspunkt, was man vorher selbst geändert hat, bleibt dabei nicht stehen."""
        b = self.basis.currentData()
        if b:
            d = stile.definition(b)
            self._farbe = d.get("farbe", "")
            self._rs = {k: d.get(k, stile.VORLAGE[k]) for k in RAHMEN_FELDER}
            self.leiste.setze(d)
        self._neu()

    def _pruefen(self, *_) -> None:
        grund = None if self.aendern else stile.pruefe_name(self.name.text())
        self.hinweis.setText(grund or "")
        self.ok.setEnabled(grund is None)

    def _schriftart(self) -> None:
        """Format ▸ Schriftart …: dasselbe Fenster wie im Band, mit allen Feldern; die Vorlage merkt sie sich."""
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        from lunivo_writer.ui.baukasten.schriftart_dialog import ZEICHEN, SchriftartDialog
        w = self.leiste.werte()
        d = SchriftartDialog(self, {**ZEICHEN, **{k: self._rs[k] for k in ZEICHEN_ZUSATZ}, "schrift": w["schrift"], "groesse": w["groesse"], "fett": w["fett"],
                                    "kursiv": w["kursiv"], "farbe": self._farbe}, umfang="vorlage")

        def fertig() -> None:
            n = d.werte()
            self._farbe = n["farbe"]
            self._rs.update({k: n[k] for k in ZEICHEN_ZUSATZ})
            self.leiste.setze({**w, "schrift": n["schrift"], "groesse": n["groesse"], "fett": n["fett"], "kursiv": n["kursiv"]})
            self._neu()
        zeige_unter(self, d, fertig)

    def _absatz(self) -> None:
        """Format ▸ Absatz …: dasselbe Fenster wie im Band, mit beiden Reitern; die Vorlage merkt sich alle Felder (auch Tabstopps und Umbruchregeln)."""
        from lunivo_writer.editor import absatzopt
        from lunivo_writer.ui.baukasten.absatz_dialog import AbsatzDialog
        from lunivo_writer.ui.baukasten.tabstopp_dialog import als_text, aus_text
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        w, r = self.leiste.werte(), self._rs
        d = AbsatzDialog(self, {"ausr": w["ausr"] or "links", "einzug": w["einzug"], "vor": w["vor"], "nach": w["nach"], "zeilen": w["zeilen"] or 1.0,
                                "rechts": r["rechts"], "erste": r["erste"], "rtl": r["rtl"], "umbruch": r["umbruch"], "zeilen_art": r["zeilen_art"],
                                "zeilen_pt": r["zeilen_pt"], "ebene": r["gliederung"], "opt": absatzopt.aus_text(r["opt"]), "tabs": aus_text(r["tabs"])},
                        umfang="vorlage")

        def fertig() -> None:
            n = d.werte()
            self.leiste.setze({**w, "ausr": "" if n["ausr"] == "links" else n["ausr"], "einzug": n["einzug"], "vor": n["vor"], "nach": n["nach"], "zeilen": n["zeilen"]})
            self._rs.update({"rechts": n["rechts"], "erste": n["erste"], "rtl": n["rtl"], "umbruch": n["umbruch"], "zeilen_art": n["zeilen_art"],
                             "zeilen_pt": n["zeilen_pt"], "gliederung": n["ebene"], "opt": absatzopt.als_text(n["opt"]), "tabs": als_text(n["tabs"])})
            self._neu()
        zeige_unter(self, d, fertig)

    def _rahmen(self) -> None:
        """Format ▸ Rahmen …: das Fenster „Rahmen und Schattierung“ ohne den Reiter Seitenrand (der gehört nicht zu einer Vorlage)."""
        from lunivo_writer.editor.linie import Linie
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog
        r = self._rs
        d = RahmenSchattierungDialog(self, rahmen=Linie.aus_text(r["rahmen"]) if r["rahmen"] else None, fuell=r["fuell"] or None,
                                     muster=(r["muster"], r["musterfarbe"] or "#000000") if r["muster"] else None,
                                     mit_seitenrand=False, fuer=["Absatz"])

        def fertig() -> None:
            linie = d.rahmen()
            fuell, muster = d.schattierung()
            self._rs.update({"rahmen": linie.text() if linie is not None else "", "fuell": fuell or "",
                             "muster": muster[0] if muster else "", "musterfarbe": muster[1] if muster else ""})
            self._neu()
        zeige_unter(self, d, fertig)

    def _liste(self) -> None:
        """Format ▸ Nummerierung …: dasselbe Fenster wie im Band; die Vorlage merkt sich die gewählte Liste."""
        from lunivo_writer.editor import listen
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        from lunivo_writer.ui.baukasten.liste_dialog import ListenDialog
        d = ListenDialog(self, listen.aus_text(self._rs["liste"]))

        def fertig() -> None:
            self._rs["liste"] = listen.als_text(d.ergebnis())
            self._neu()
        zeige_unter(self, d, fertig)

    def _effekte(self) -> None:
        """Format ▸ Texteffekte …: Füllung (Farbe der Vorlage, Transparenz) und Kontur."""
        from lunivo_writer.editor import texteffekt
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
        w = texteffekt.aus_text(self._rs["effekt"], self._farbe) or {**texteffekt.EFFEKT, "farbe": self._farbe}
        if w["transparenz"] >= 100:
            w["fuell"] = "keine"
        d = TexteffektDialog(self, w)

        def fertig() -> None:
            n = d.werte()
            if n["fuell"] == "keine":
                n["transparenz"] = 100
            self._farbe = n["farbe"]
            self._rs["effekt"] = texteffekt.als_text(n)
            self._neu()
        zeige_unter(self, d, fertig)

    def _tabs(self) -> None:
        """Format ▸ Tabstopps …: dasselbe Fenster wie im Absatz; die Vorlage merkt sich die Tabstopps."""
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        from lunivo_writer.ui.baukasten.tabstopp_dialog import TabstoppDialog, als_text, aus_text
        d = TabstoppDialog(self, aus_text(self._rs["tabs"]), self._tab_std if self._tab_std is not None else 12.7)

        def fertig() -> None:
            self._rs["tabs"] = als_text(d.stopps())
            if d.standard_abstand():
                self._tab_std_neu = d.standard_abstand()
            self._neu()
        zeige_unter(self, d, fertig)

    def _verknuepfung(self) -> None:
        """Format ▸ Verknüpfung …: die Tastenkombination, die die Vorlage auf den Absatz anwendet."""
        from lunivo_writer.ui.baukasten.tasten_dialog import TastenDialog
        eigen = self.aendern or self.name.text()
        from lunivo_writer.ui.baukasten.fenster_stapel import zeige_unter
        d = TastenDialog(self, self._taste, belegt=(lambda t: self._belegt(t, eigen)) if self._belegt else None)
        zeige_unter(self, d, lambda: setattr(self, "_taste", d.taste()))

    def _ok(self) -> None:
        if self.aendern or stile.pruefe_name(self.name.text()) is None:
            self.accept()

    def ergebnis(self) -> dict:
        """Name, Basis, folgender Absatz und alle Felder der Vorlage."""
        w = self.leiste.werte()
        felder = {k: w[k] for k in ("schrift", "groesse", "fett", "kursiv", "ausr", "vor", "nach", "einzug", "zeilen")}
        felder["farbe"] = self._farbe
        felder.update(self._rs)
        felder["taste"] = self._taste
        if self._tab_std_neu:
            felder["tab_standard"] = self._tab_std_neu                         # gilt für das Dokument, nicht für die Vorlage (siehe Aufrufer)
        felder["zur_vorlage"] = self.zur_vorlage.isChecked() or bool(self.aendern)
        return {"name": " ".join(self.name.text().split()), "basis": self.basis.currentData() or "", "folge": self.folge.currentData() or "", **felder}
