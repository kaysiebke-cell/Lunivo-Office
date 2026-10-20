"""Das ☰ Menü: links die Datei-Befehle, rechts der Inhalt (zuletzt verwendete Dateien oder die Punkte eines Untermenüs)."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from lunivo_writer.ui.baukasten.beschriftung import md_escape, md_label, text_label
from lunivo_writer.ui.baukasten.datei_symbole import datei_symbol


# Symbole der Menüpunkte aus dem Icon-Theme des Systems (Freedesktop-Namen); was das Theme nicht kennt, bleibt ohne Symbol
_MENUE_SYMBOLE = {
    "Neu": "document-new", "Neu aus Vorlage": "document-new", "Öffnen": "document-open", "Speichern": "document-save",
    "Speichern unter": "document-save-as", "Drucken": "document-print", "Druckvorschau": "document-print-preview",
    "Druckereinstellungen": "document-page-setup", "Dokumenteigenschaften": "document-properties", "Umbenennen": "document-edit",
    "Schließen": "window-close", "Hilfe": "help-browser", "Optionen": "preferences-system", "Beenden": "application-exit",
    "Vorlagenordner": "folder-templates", "Zuletzt geöffnet": "document-open-recent",
}


def _menue_symbol(name: str) -> QIcon:
    if name == "Als PDF exportieren":
        return datei_symbol(".pdf")
    return QIcon.fromTheme(_MENUE_SYMBOLE.get(name, ""))


def _datum(pfad: str) -> str:
    """Änderungsdatum der Datei für die Liste „Zuletzt verwendet“ (leer, wenn es sie nicht mehr gibt)."""
    try:
        return datetime.fromtimestamp(os.path.getmtime(pfad)).strftime("%d.%m. %H:%M")
    except OSError:
        return "nicht mehr da"


class MenueTafel(QFrame):
    def __init__(self, punkte: list, befehle, fenster):
        super().__init__(fenster, Qt.Popup)
        self.setFrameShape(QFrame.StyledPanel)
        self.punkte, self.b, self.w = punkte, befehle, fenster
        h = QHBoxLayout(self)
        h.setContentsMargins(6, 6, 6, 6)
        h.setSpacing(12)
        self.links = QVBoxLayout()
        self.links.setSpacing(0)
        host = QWidget()
        host.setLayout(self.links)
        host.setFixedWidth(250)
        h.addWidget(host)
        self.rechts = QVBoxLayout()
        self.rechts.setAlignment(Qt.AlignTop)
        rh = QWidget()
        rh.setLayout(self.rechts)
        rh.setFixedWidth(330)
        h.addWidget(rh)
        for p in punkte:
            if p.get("trenner"):
                s = QFrame(); s.setFrameShape(QFrame.HLine); s.setFrameShadow(QFrame.Sunken)
                self.links.addWidget(s)
                continue
            name = p["name"]
            taste = p.get("taste", "")
            b = QPushButton(f"{name}" + ("   ›" if p.get("unter") or name == "Zuletzt geöffnet" else ""))
            sym = _menue_symbol(name)
            if not sym.isNull():
                b.setIcon(sym); b.setIconSize(QSize(22, 22))
            b.setFlat(True)
            b.setStyleSheet("text-align: left; padding: 5px 8px;")
            if taste:
                b.setToolTip(taste)
            ok = bool(p.get("unter")) or name in ("Optionen", "Zuletzt geöffnet") or (p.get("tun") and self.b.hat(p["tun"]))
            if p.get("tun") and not self.b.hat(p["tun"]) and name != "Optionen":
                ok = False
            b.setEnabled(bool(ok))
            if not ok:
                b.setToolTip(f"{name} — in der nativen Fassung noch nicht umgesetzt")
            b.clicked.connect(lambda _=False, pp=p: self._klick(pp))
            b.installEventFilter(self)
            b._punkt = p
            self.links.addWidget(b)
        self.links.addStretch(1)
        self._zeige_zuletzt()

    def eventFilter(self, obj, ev):
        from PySide6.QtCore import QEvent
        if ev.type() == QEvent.Enter and hasattr(obj, "_punkt"):
            p = obj._punkt
            if p.get("unter"):
                self._zeige_unter(p)
            elif p["name"] == "Zuletzt geöffnet" or not p.get("tun"):
                self._zeige_zuletzt()
            else:
                self._zeige_zuletzt()
        return super().eventFilter(obj, ev)

    def _leeren(self):
        while self.rechts.count():
            it = self.rechts.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def _zeige_zuletzt(self):
        self._leeren()
        kopf = QHBoxLayout()
        t = text_label("Zuletzt verwendete Dokumente", fett=True, umbruch=False)
        kopf.addWidget(t)
        kopf.addStretch(1)
        r = QToolButton(); r.setText("↻"); r.setAutoRaise(True); r.setToolTip("Liste neu holen")
        r.clicked.connect(self._zeige_zuletzt)
        kopf.addWidget(r)
        kw = QWidget(); kw.setLayout(kopf)
        self.rechts.addWidget(kw)
        items = self.w.settings.recent()
        if not items:
            self.rechts.addWidget(QLabel("Noch keine Dokumente geöffnet."))
        for pfad in items[:10]:
            z = QHBoxLayout()
            b = QPushButton(f"{os.path.basename(pfad)}\n{os.path.dirname(pfad)}")
            b.setIcon(datei_symbol(pfad)); b.setIconSize(QSize(28, 28))
            b.setFlat(True)
            b.setStyleSheet("text-align: left; padding: 3px 6px; font-size: 9pt;")
            b.clicked.connect(lambda _=False, p=pfad: (self.close(), self.w.open_path(p)))
            x = QToolButton(); x.setText("×"); x.setAutoRaise(True)
            x.setToolTip("Aus der Liste nehmen — die Datei bleibt liegen")
            x.clicked.connect(lambda _=False, p=pfad: (self.w.settings.remove_recent(p), self._zeige_zuletzt()))
            datum = text_label(_datum(pfad), umbruch=False)
            datum.setStyleSheet("color: palette(mid); font-size: 9pt;")
            z.addWidget(b, 1); z.addWidget(datum); z.addWidget(x)
            zw = QWidget(); zw.setLayout(z)
            self.rechts.addWidget(zw)

    def _zeige_unter(self, p: dict):
        self._leeren()
        self.rechts.addWidget(text_label(p["name"], fett=True, umbruch=False))
        for u in p["unter"]:
            if u.get("trenner"):
                continue
            b = QPushButton(u["name"])
            if u.get("datei"):                                     # Dateiformat: Symbol aus dem Icon-Theme des Systems
                b.setIcon(datei_symbol(u["datei"])); b.setIconSize(QSize(24, 24))
            b.setFlat(True)
            b.setStyleSheet("text-align: left; padding: 4px 8px;")
            ok = bool(u.get("tun")) and self.b.hat(u["tun"])
            b.setEnabled(ok)
            if not ok:
                b.setToolTip(f"{u['name']} — in der nativen Fassung noch nicht umgesetzt")
            b.clicked.connect(lambda _=False, t=u.get("tun"): (self.close(), self.b.tun(t)))
            self.rechts.addWidget(b)

    def _klick(self, p: dict):
        if p.get("unter"):
            self._zeige_unter(p)
            return
        self.close()
        if p["name"] == "Optionen":
            self.w.show_options()
        elif p.get("tun") and self.b.hat(p["tun"]):
            self.b.tun(p["tun"])

    def zeigen_unter(self, widget):
        self.adjustSize()
        self.move(widget.mapToGlobal(QPoint(0, widget.height())))
        self.show()
