"""Seiteneinrichtung: Papier, Ränder, Ausrichtung, Kopf- und Fußzeile.

Alle Maße in Millimetern. Umrechnung in Bildpunkte (96 dpi) nur hier.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PX_PER_MM = 96.0 / 25.4

PAPER_MM = {
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "A3": (297.0, 420.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
}


def mm_to_px(mm: float) -> float:
    return mm * PX_PER_MM


def px_to_mm(px: float) -> float:
    return px / PX_PER_MM


@dataclass
class HeaderFooter:
    """Text mit Platzhalter {PAGE} und {PAGES}. Ausrichtung: left|center|right."""
    text: str = ""
    align: str = "center"

    def is_empty(self) -> bool:
        return not self.text.strip()


@dataclass
class PageSettings:
    width_mm: float = 210.0
    height_mm: float = 297.0
    margin_top_mm: float = 25.0
    margin_bottom_mm: float = 25.0
    margin_left_mm: float = 32.0
    margin_right_mm: float = 32.0
    header: HeaderFooter = field(default_factory=HeaderFooter)
    footer: HeaderFooter = field(default_factory=HeaderFooter)
    color: str = ""                      # Seitenfarbe als „#rrggbb“; leer = keine
    border: dict | None = None           # {"farbe": "#000000", "breite_pt": 1.0, "art": Linienart (editor/linie.py), "abstand_mm": 8.0, "seiten": "tblr"}
    watermark: dict | None = None        # {"text": …, "farbe": "#c0c0c0", "winkel": -45, "groesse_pt": 80}
    zeilennummern: bool = False
    diff_first: bool = False                 # „Erste Seite anders“
    first_header: HeaderFooter = field(default_factory=HeaderFooter)
    first_footer: HeaderFooter = field(default_factory=HeaderFooter)
    spalten: int = 1                         # Textspalten (Seitenansicht, Druck, PDF; die Bearbeitungsansicht bleibt einspaltig)
    spalten_abstand_mm: float = 10.0
    spalten_linie: bool = False              # Trennlinie zwischen den Spalten
    silbentrennung: bool = False             # automatische Silbentrennung (Seitenansicht, Druck, PDF; DOCX: autoHyphenation)
    silben_sprache: str = "de_DE"
    kopf_verknuepft: bool = False            # Abschnitt ab dem zweiten: Kopfzeile wie im vorigen Abschnitt
    bilder: list = field(default_factory=list)   # frei positionierte Bilder in Kopf-/Fußzeilen (siehe editor/freie_bilder.py)
    fuss_verknuepft: bool = False

    @property
    def landscape(self) -> bool:
        return self.width_mm > self.height_mm

    def set_orientation(self, landscape: bool) -> None:
        if landscape != self.landscape:
            self.width_mm, self.height_mm = self.height_mm, self.width_mm

    def set_paper(self, name: str) -> None:
        w, h = PAPER_MM[name]
        if self.landscape:
            w, h = h, w
        self.width_mm, self.height_mm = w, h

    def paper_name(self) -> str:
        a, b = sorted((self.width_mm, self.height_mm))
        for name, (w, h) in PAPER_MM.items():
            if abs(a - w) < 1.0 and abs(b - h) < 1.0:
                return name
        return "Benutzerdefiniert"

    @property
    def content_width_px(self) -> float:
        return mm_to_px(self.width_mm - self.margin_left_mm - self.margin_right_mm)

    @property
    def content_height_px(self) -> float:
        return mm_to_px(self.height_mm - self.margin_top_mm - self.margin_bottom_mm)

    def copy(self) -> "PageSettings":
        import dataclasses
        return dataclasses.replace(
            self, header=HeaderFooter(self.header.text, self.header.align), footer=HeaderFooter(self.footer.text, self.footer.align),
            border=dict(self.border) if self.border else None, watermark=dict(self.watermark) if self.watermark else None,
            first_header=HeaderFooter(self.first_header.text, self.first_header.align),
            first_footer=HeaderFooter(self.first_footer.text, self.first_footer.align), bilder=list(self.bilder))

    @property
    def spalten_breite_px(self) -> float:
        """Breite einer Textspalte (bei einer Spalte: die ganze Textbreite)."""
        n = max(1, int(self.spalten))
        return (self.content_width_px - mm_to_px(self.spalten_abstand_mm) * (n - 1)) / n
