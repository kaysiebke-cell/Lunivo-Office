"""Jeder Befehl des Registers wird einmal aufgerufen (Dialoge und Menüs werden abgebrochen): es darf nichts abstürzen."""
import json
import os

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage, QTextCursor
from PySide6.QtWidgets import QColorDialog, QDialog, QFileDialog, QInputDialog, QMenu, QMessageBox

from native_qt.editor import einfuegen as E
from native_qt.storage.settings import Settings
from native_qt.widgets.register_band import lade_register
from native_qt.windows.main_window import MainWindow


def _alle_befehle(daten) -> set[str]:
    namen = set()

    def lauf(o):
        if isinstance(o, dict):
            for k in ("tun", "klappe", "pfeil"):
                if isinstance(o.get(k), str):
                    namen.add(o[k])
            for v in o.values():
                lauf(v)
        elif isinstance(o, list):
            for x in o:
                lauf(x)
    lauf(daten)
    return namen


def test_alle_befehle_stuerzen_nicht_ab(app, tmp_path, monkeypatch):
    # alle Fenster, die auf Eingaben warten, werden von einem Wächter geschlossen (Abbrechen)
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from native_qt.windows.befehle import Befehle
    monkeypatch.setattr(Befehle, "_popup", lambda self, m: None)

    from PySide6.QtWidgets import QDialog, QMenu as _QMenu

    def waechter():
        # (QApplication.activeModalWidget() stürzt unter „offscreen“ bei QFontDialog ab — deshalb über die Fensterliste)
        for x in QApplication.topLevelWidgets():
            if isinstance(x, QDialog) and x.isVisible():
                x.reject()
            elif isinstance(x, _QMenu) and x.isVisible():
                x.close()
    uhr = QTimer(); uhr.setInterval(40); uhr.timeout.connect(waechter); uhr.start()

    w = MainWindow(Settings(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)))
    w.new_document(); w.resize(1380, 860); w.show()
    e = w.current_editor()
    e.insertPlainText("Überschrift\nEin Absatz mit Text zum Probieren.\nNoch ein Absatz.\n")
    img = QImage(30, 20, QImage.Format_RGB32); img.fill(0x3366aa)
    E.qimage_einfuegen(e, img, "Bild")
    e.insert_table(2, 2)
    namen = sorted(_alle_befehle(lade_register()) | {"w.optionenOeffnen"})
    ausgenommen = {"beenden", "schliessen", "neu", "oeffnen", "speichernPdf", "drucken", "vorschau", "screenshot", "ueber",
                   "tafelZeigen", "vorlesen", "vorlesenAbSatz", "kiKorrektur", "lesemodus", "w.chatUmschalten"}
    fehler = []
    for n in namen:
        if n in ausgenommen or n.startswith("w.set") or n.endswith("Jetzt") or not w.befehle.hat(n):
            continue
        # Zustände wiederherstellen: Text markieren, Zeiger in den Text
        c = e.textCursor(); c.setPosition(5); c.setPosition(12, QTextCursor.KeepAnchor); e.setTextCursor(c)
        try:
            w.befehle.tun(n)
        except Exception as ex:                                     # noqa: BLE001
            fehler.append(f"{n}: {type(ex).__name__}: {ex}")
    uhr.stop()
    assert not fehler, "\n".join(fehler)
    for t in w._doc_tabs():
        t.editor.document().setModified(False)
    w.close()
