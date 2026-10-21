"""Das Rechtsklick-Menü des Textes, deutsch und in der Reihenfolge der Vorlage: Zwischenablage, Format übertragen, Schriftart, Absatz,
Aufzählung, Hyperlink, Kommentar. Darunter stehen die Punkte, die nur dort etwas bewirken (Bild, markierter Text, KI).

Die Befehle sind dieselben wie im Band (``fenster.befehle``); das Menü hat keine eigene Logik, es ruft sie nur.
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QMenu

from lunivo_writer.ui.widgets import icons


def _symbole() -> dict[str, str]:
    from lunivo_writer.ui.widgets.mini_leiste import _symbole as lade
    return lade()


def menue_bauen(editor, fenster) -> QMenu:
    """Das Menü für den Editor ``editor`` des Fensters ``fenster``; der Aufrufer zeigt es und löscht es danach."""
    b = fenster.befehle
    sym = _symbole()
    m = QMenu(editor)
    lesen = editor.isReadOnly()
    auswahl = editor.textCursor().hasSelection()

    def punkt(text: str, tun=None, taste: str = "", icon: str = "", an: bool = True, aktion=None):
        a = m.addAction(text)
        name = icon or (sym.get(tun, "") if isinstance(tun, str) else "")
        if name and icons.hat(name):
            a.setIcon(icons.icon(name, 16))
        if taste:
            a.setShortcut(QKeySequence(taste)); a.setShortcutVisibleInContextMenu(True)
        a.setEnabled(an)
        a.triggered.connect(aktion if aktion is not None else (lambda _=False, t=tun: b.tun(t)))
        return a

    punkt("Kopieren", "kopieren", "Ctrl+C", "kopie", auswahl)
    punkt("Ausschneiden", "ausschneiden", "Ctrl+X", "schere", auswahl and not lesen)
    punkt("Einfügen", "einfuegen", "Ctrl+V", "kleben", editor.canPaste() and not lesen)
    punkt("Einfügen ohne Formatierung", "einfuegenOhne", "", "", editor.canPaste() and not lesen)
    punkt("Inhalte einfügen …", "inhalteEinfuegen", "Ctrl+Alt+V", "", editor.canPaste() and not lesen)
    m.addSeparator()
    punkt("Format übertragen", "formatUebertragen", "", "pinsel", not lesen)
    m.addSeparator()
    punkt("Schriftart …", "schriftartMehr", "Ctrl+D", "", not lesen)
    punkt("Absatz …", None, "", "absatzlayout", not lesen, aktion=fenster.paragraph_dialog)
    punkt("Aufzählungszeichen und Nummerierung …", None, "", "", not lesen, aktion=lambda: b.listeDialog())
    m.addSeparator()
    punkt("Hyperlink …", "hyperlink", "Ctrl+K", "kette", not lesen)
    punkt("Neuer Kommentar", "kommentar", "", "notiz", not lesen)
    m.addSeparator()
    punkt("Alles auswählen", None, "Ctrl+A", "", True, aktion=editor.selectAll)
    return m
