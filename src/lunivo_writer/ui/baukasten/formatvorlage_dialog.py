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
    QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QVBoxLayout, QWidget,
)

from lunivo_writer.editor import stile
from lunivo_writer.ui.baukasten.dialog_rahmen import VorschauFlaeche
from lunivo_writer.ui.baukasten.farbpalette import weitere_farben
from lunivo_writer.ui.baukasten.mass_feld import MassSpin, spin
from lunivo_writer.ui.baukasten.text_format import TextFormatLeiste, zeichne_absaetze, zu_format

RAHMEN_FELDER = ("rahmen", "fuell", "muster", "musterfarbe", "liste", "effekt")      # Felder, die nicht zur Leiste gehören
KEINE = "(keine)"
GLEICHE = "(dieselbe Vorlage)"


class FormatvorlageDialog(QDialog):
    def __init__(self, parent=None, *, start: dict | None = None, vorlagen: list[str] | None = None, name: str = "Formatvorlage1",
                 basis: str = "Standard", aendern: str | None = None, belegt=None):
        """``aendern``: Name einer vorhandenen Vorlage — dann ist es das Fenster „Formatvorlage ändern“ (Name fest)."""
        super().__init__(parent)
        self.aendern = aendern
        self._belegt = belegt                                       # Funktion (Taste, eigener Name) → Name, der sie schon hat, oder None
        self._taste = (start or {}).get("taste", "")
        self.setWindowTitle("Formatvorlage ändern" if aendern else "Neue Formatvorlage")
        self.setMinimumWidth(560)
        self._farbe = (start or {}).get("farbe", "")
        self._rs = {k: (start or {}).get(k, "") for k in RAHMEN_FELDER}      # Rahmen und Schattierung (kein Feld der Leiste)
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
        # --- Knöpfe
        zu = QHBoxLayout()
        self.format = QPushButton("Format ▾")
        m = QMenu(self.format)
        m.addAction("Schriftart …", self._schriftart); m.addAction("Absatz …", self._absatz); m.addAction("Rahmen …", self._rahmen); m.addAction("Nummerierung …", self._liste); m.addAction("Texteffekte …", self._effekte); m.addAction("Verknüpfung …", self._verknuepfung)
        self.format.setMenu(m)
        zu.addWidget(self.format); zu.addStretch(1)
        ab, self.ok = QPushButton("Abbrechen"), QPushButton("OK"); self.ok.setDefault(True)
        ab.clicked.connect(self.reject); self.ok.clicked.connect(self._ok)
        zu.addWidget(ab); zu.addWidget(self.ok)
        v.addLayout(zu)
        # --- Anfangswerte und Verdrahtung
        if aendern:
            e = stile._NEU.get(aendern, {})
            basis, start = e.get("basis", ""), stile.definition(aendern)
            self.folge.setCurrentIndex(max(0, self.folge.findData(e.get("folge", ""))))
            if aendern not in stile._NEU:                           # eingebaute Vorlagen haben weder Basis noch Folgevorlage
                self.basis.setEnabled(False); self.folge.setEnabled(False)
            self._farbe = start.get("farbe", "")
            self._rs = {k: start.get(k, "") for k in RAHMEN_FELDER}
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
            self._rs = {k: d.get(k, "") for k in RAHMEN_FELDER}
            self.leiste.setze(d)
        self._neu()

    def _pruefen(self, *_) -> None:
        grund = None if self.aendern else stile.pruefe_name(self.name.text())
        self.hinweis.setText(grund or "")
        self.ok.setEnabled(grund is None)

    def _schriftart(self) -> None:
        """Format ▸ Schriftart …: dasselbe Fenster wie im Band, aber nur mit den Feldern, die eine Vorlage kennt."""
        from lunivo_writer.ui.baukasten.schriftart_dialog import SchriftartDialog
        w = self.leiste.werte()
        d = SchriftartDialog(self, {"schrift": w["schrift"], "groesse": w["groesse"], "fett": w["fett"], "kursiv": w["kursiv"], "farbe": self._farbe},
                             umfang="vorlage")
        if d.exec():
            n = d.werte()
            self._farbe = n["farbe"]
            self.leiste.setze({**w, "schrift": n["schrift"], "groesse": n["groesse"], "fett": n["fett"], "kursiv": n["kursiv"]})
            self._neu()

    def _absatz(self) -> None:
        """Format ▸ Absatz …: dasselbe Fenster wie im Band, aber nur mit den Feldern, die eine Vorlage kennt."""
        from lunivo_writer.ui.baukasten.absatz_dialog import AbsatzDialog
        w = self.leiste.werte()
        d = AbsatzDialog(self, {"ausr": w["ausr"] or "links", "einzug": w["einzug"], "vor": w["vor"], "nach": w["nach"],
                                "zeilen": w["zeilen"] or 1.0}, umfang="vorlage")
        if d.exec():
            n = d.werte()
            self.leiste.setze({**w, "ausr": "" if n["ausr"] == "links" else n["ausr"], "einzug": n["einzug"], "vor": n["vor"], "nach": n["nach"], "zeilen": n["zeilen"]})
            self._neu()

    def _rahmen(self) -> None:
        """Format ▸ Rahmen …: das Fenster „Rahmen und Schattierung“ ohne den Reiter Seitenrand (der gehört nicht zu einer Vorlage)."""
        from lunivo_writer.editor.linie import Linie
        from lunivo_writer.ui.baukasten.rahmen_schattierung import RahmenSchattierungDialog
        r = self._rs
        d = RahmenSchattierungDialog(self, rahmen=Linie.aus_text(r["rahmen"]) if r["rahmen"] else None, fuell=r["fuell"] or None,
                                     muster=(r["muster"], r["musterfarbe"] or "#000000") if r["muster"] else None,
                                     mit_seitenrand=False, fuer=["Absatz"])
        if d.exec():
            linie = d.rahmen()
            fuell, muster = d.schattierung()
            self._rs.update({"rahmen": linie.text() if linie is not None else "", "fuell": fuell or "",
                             "muster": muster[0] if muster else "", "musterfarbe": muster[1] if muster else ""})
            self._neu()

    def _liste(self) -> None:
        """Format ▸ Nummerierung …: dasselbe Fenster wie im Band; die Vorlage merkt sich die gewählte Liste."""
        from lunivo_writer.editor import listen
        from lunivo_writer.ui.baukasten.liste_dialog import ListenDialog
        d = ListenDialog(self, listen.aus_text(self._rs["liste"]))
        if d.exec():
            self._rs["liste"] = listen.als_text(d.ergebnis())
            self._neu()

    def _effekte(self) -> None:
        """Format ▸ Texteffekte …: Füllung (Farbe der Vorlage, Transparenz) und Kontur."""
        from lunivo_writer.editor import texteffekt
        from lunivo_writer.ui.baukasten.texteffekt_dialog import TexteffektDialog
        w = texteffekt.aus_text(self._rs["effekt"], self._farbe) or {**texteffekt.EFFEKT, "farbe": self._farbe}
        if w["transparenz"] >= 100:
            w["fuell"] = "keine"
        d = TexteffektDialog(self, w)
        if d.exec():
            n = d.werte()
            if n["fuell"] == "keine":
                n["transparenz"] = 100
            self._farbe = n["farbe"]
            self._rs["effekt"] = texteffekt.als_text(n)
            self._neu()

    def _verknuepfung(self) -> None:
        """Format ▸ Verknüpfung …: die Tastenkombination, die die Vorlage auf den Absatz anwendet."""
        from lunivo_writer.ui.baukasten.tasten_dialog import TastenDialog
        eigen = self.aendern or self.name.text()
        d = TastenDialog(self, self._taste, belegt=(lambda t: self._belegt(t, eigen)) if self._belegt else None)
        if d.exec():
            self._taste = d.taste()

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
        return {"name": " ".join(self.name.text().split()), "basis": self.basis.currentData() or "", "folge": self.folge.currentData() or "", **felder}
