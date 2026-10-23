"""Befehle des Bandes: Aktionsname aus register.json → Funktion.

Ein Name, den es hier nicht gibt, bleibt im Band sichtbar, aber ausgegraut — mit dem Hinweis,
dass er in der nativen Fassung noch fehlt. So entsteht die Liste dessen, was noch zu tun ist,
von selbst (siehe `fehlende()`), und nichts steht als Attrappe da.

Konvention: Methode `name(self, knopf=None)`; `w.xyz` heißt `w_xyz`.
Zustand eines Schalters: Methode `an_name(self) -> bool`.
Klappe (Pfeilmenü): Methode `menue_name(self) -> QMenu`.
"""
from __future__ import annotations

import json
from PySide6.QtGui import QCursor, QTextCharFormat
from lunivo_writer.core.befehle.ansicht import AnsichtBefehle
from lunivo_writer.core.befehle.bearbeiten import BearbeitenBefehle
from lunivo_writer.core.befehle.datei import DateiBefehle
from lunivo_writer.core.befehle.einfuegen import EinfuegenBefehle
from lunivo_writer.core.befehle.extern import ExternBefehle
from lunivo_writer.core.befehle.ki import KIBefehle
from lunivo_writer.core.befehle.kommentare import KommentarBefehle
from lunivo_writer.core.befehle.kontext import KontextBefehle
from lunivo_writer.core.befehle.pruefen import PruefenBefehle
from lunivo_writer.core.befehle.seite import SeiteBefehle
from lunivo_writer.core.befehle.text import TextBefehle
from lunivo_writer.core.befehle.verweise import VerweiseBefehle
from lunivo_writer.core.befehle.hilfen import FreiMenue, _farbfeld  # noqa: F401  (andere Module holen sie hier)


class Befehle(AnsichtBefehle, BearbeitenBefehle, DateiBefehle, EinfuegenBefehle, ExternBefehle, KIBefehle, KommentarBefehle, KontextBefehle, PruefenBefehle, SeiteBefehle, TextBefehle, VerweiseBefehle):
    """Alle Befehle des Bandes. Die Grundfunktionen (Aktion suchen, ausführen, Zustand) stehen hier, die Befehle selbst in ``core/befehle/*``."""

    def __init__(self, win):
        self.w = win


    # ---- Hilfen --------------------------------------------------------------------
    @property
    def ed(self):
        return self.w.current_editor()


    @staticmethod
    def _teile(name: str):
        """'w.setzePapier:["a4"]' → ('w_setzePapier', ['a4'])"""
        basis, _, rest = name.partition(":")
        return basis.replace(".", "_"), (json.loads(rest) if rest else [])


    def hat(self, name: str) -> bool:
        return callable(getattr(self, self._teile(name)[0], None))


    def tun(self, name: str, knopf=None):
        basis, args = self._teile(name)
        f = getattr(self, basis, None)
        if callable(f):
            return f(knopf, *args)


    def zustand(self, name: str):
        basis, _ = self._teile(name)
        f = getattr(self, "an_" + basis, None)
        return bool(f()) if callable(f) else None


    def haken_wert(self, item: dict) -> bool | None:
        """Haken eines Menüpunkts: Zustandsfrage des Menüeintrags (z. B. w.randVorgabeJetzt) gegen sein Argument."""
        g = item.get("haken")
        if not isinstance(g, str):
            return None
        f = getattr(self, self._teile(g)[0], None)
        if not callable(f):
            return None
        wert = f()
        _, args = self._teile(item.get("tun", ""))
        n = item.get("name")
        if g.endswith("querJetzt"):
            return bool(wert) if n == "Querformat" else not wert
        return (wert == args[0]) if args else bool(wert)


    def klappe(self, name: str):
        f = getattr(self, "menue_" + name.replace(".", "_"), None)
        return f() if callable(f) else None


    def _popup(self, menue) -> None:
        """Menü an der Mausposition zeigen (eigene Stelle, damit Tests es abfangen können)."""
        menue.exec(QCursor.pos())


    def fehlende(self, namen) -> list[str]:
        return sorted(n for n in namen if not self.hat(n))


    def _fmt(self):
        e = self.ed
        return e.textCursor().charFormat() if e else QTextCharFormat()
