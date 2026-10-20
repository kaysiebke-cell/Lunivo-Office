#!/usr/bin/env python3
"""Probiert jeden Knopf und jeden Menüpunkt des Bandes aus und schreibt auf, was wirklich passiert.

    .venv/bin/python werkzeug/funktionspruefung.py [--ziel docs/funktionsstand.md] [--reiter Start,Einfügen]

Läuft ohne Bildschirm (QT_QPA_PLATFORM=offscreen). Jeder Knopf wird in vier Lagen gedrückt — Text markiert, vorformatierter Text
markiert, Zeiger in einer Tabelle, Bild markiert — und das Dokument wird davor und danach verglichen. Dialoge werden abgebrochen (und, wenn sie aus
Lunivo selbst stammen, in einem zweiten Durchgang mit OK bestätigt). Das Ergebnis je Knopf:

  wirkt        das Dokument oder die Oberfläche hat sich verändert
  Dialog       ein Fenster ging auf (Titel steht dabei); mit OK: wirkt / keine Wirkung / Fehler
  Menü         ein Menü ging auf; seine Einträge werden einzeln geprüft
  Meldung      das Programm hat etwas gesagt (Statuszeile oder Hinweisfenster)
  keine Wirkung  nichts sichtbar passiert — kann ein Umschalter ohne Folge in dieser Lage sein, muss man ansehen
  Fehler       Python-Fehler beim Drücken
  fehlt        im Band grau mit „noch nicht umgesetzt“
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import traceback
from collections import OrderedDict

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(WURZEL, "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, QStandardPaths, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QImage, QTextCursor, QTextDocumentFragment  # noqa: E402

from lunivo_writer.editor.textdaten import fragment_zu_daten  # noqa: E402
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QMenu, QMessageBox, QStackedWidget, QTabBar,  # noqa: E402
                               QToolButton, QWidget)

# Befehle, die Dateien schreiben, andere Programme starten, drucken, ins Netz gehen oder das Fenster schließen
AUSGENOMMEN = {"beenden", "schliessen", "neu", "oeffnen", "speichern", "speichernUnter", "speichernPdf", "drucken", "vorschau",
               "screenshot", "ueber", "tafelZeigen", "vorlesen", "vorlesenAbSatz", "kiKorrektur", "lesemodus", "w.chatUmschalten",
               "w.optionenOeffnen"}
LAGEN = ("text", "formatiert", "tabelle", "bild")


class Pruefer:
    def __init__(self, tmp: str):
        from lunivo_writer.core.commands import Befehle
        from lunivo_writer.editor import einfuegen as E
        from lunivo_writer.services.settings_service import Settings
        from lunivo_writer.ui.main_window import MainWindow
        self.E, self.Befehle = E, Befehle
        self.fenster_log: list[str] = []
        self.menue_log: list[list[str]] = []
        self.befehle_log: list[str] = []
        self.fehler_log: list[str] = []
        self.modus_ok = False                                   # Wächter: Dialoge mit OK (True) oder Abbrechen (False) schließen

        orig_tun = Befehle.tun
        pruefer = self

        def tun(selbst, name, knopf=None):
            pruefer.befehle_log.append(name)
            if name in AUSGENOMMEN:
                return None
            return orig_tun(selbst, name, knopf)
        Befehle.tun = tun
        Befehle._popup = lambda selbst, m: pruefer.menue_log.append(pruefer._eintraege(m))
        sys.excepthook = lambda t, v, tb: pruefer.fehler_log.append("".join(traceback.format_exception_only(t, v)).strip())

        self.w = MainWindow(Settings(QSettings(os.path.join(tmp, "s.ini"), QSettings.IniFormat)))
        self.w.new_document(); self.w.resize(1500, 900); self.w.show()
        self.uhr = QTimer(); self.uhr.setInterval(30); self.uhr.timeout.connect(self._waechter); self.uhr.start()
        QApplication.instance().processEvents()

    # ---- Wächter für Fenster, die auf Eingaben warten -----------------------------------------------------------------------
    def _waechter(self):
        # Dialoge, die nach OK noch offen sind (etwa weil sie eine Warnung zeigten), werden nach einigen Takten abgebrochen
        for x in QApplication.topLevelWidgets():
            if isinstance(x, QDialog) and x.isVisible() and x.property("geprueft"):
                n = int(x.property("takte") or 0) + 1
                x.setProperty("takte", n)
                if n == 5:
                    self.fenster_log.append(f"{type(x).__name__}: {x.windowTitle()} (blieb nach OK offen)")
                    QTimer.singleShot(0, x.reject)
        sichtbar = [x for x in QApplication.topLevelWidgets() if isinstance(x, QDialog) and x.isVisible() and not x.property("geprueft")]
        fremd = [x for x in sichtbar if not type(x).__module__.startswith("lunivo_writer")]
        for x in (fremd or sichtbar):                              # zuerst Meldungs- und Dateifenster, erst dann Lunivos eigene Dialoge
            x.setProperty("geprueft", True)
            self.fenster_log.append(f"{type(x).__name__}: {x.windowTitle()}" + (f" — {x.text()[:80]}" if isinstance(x, QMessageBox) else ""))
            if self.modus_ok and x in sichtbar and x not in fremd:
                QTimer.singleShot(0, x.accept)                     # nicht im Wächter selbst: eine Warnung dabei muss er schließen können
            else:
                QTimer.singleShot(0, x.reject)
        for x in QApplication.topLevelWidgets():
            if isinstance(x, QMenu) and x.isVisible() and x.parent() is None:
                x.close()

    @staticmethod
    def _eintraege(m: QMenu, tiefe: int = 0) -> list[str]:
        out = []
        for a in m.actions():
            if a.isSeparator() or not a.text().strip():
                continue
            out.append(a.text().replace("&", "").split("\t")[0])
            if a.menu() is not None and tiefe < 3:
                out += ["  " + t for t in Pruefer._eintraege(a.menu(), tiefe + 1)]
        return out

    # ---- Beispieldokument und Lagen --------------------------------------------------------------------------------------
    @property
    def ed(self):
        return self.w.current_editor()

    def beispiel(self, lage: str):
        e = self.ed
        e.document().setModified(False)
        e.clear()
        e.setPlainText("Überschrift\nEin Absatz mit Text zum Probieren und Prüfen der Befehle.\nNoch ein Absatz mit mehr Wörtern darin.\n")
        c = e.textCursor(); c.movePosition(QTextCursor.End); e.setTextCursor(c)
        img = QImage(40, 24, QImage.Format_RGB32); img.fill(0x3366aa)
        self.E.qimage_einfuegen(e, img, "Bild")
        e.insert_table(2, 2)
        d = e.document()
        c = QTextCursor(d)
        if lage in ("text", "formatiert"):
            c.setPosition(14); c.setPosition(40, QTextCursor.KeepAnchor)
        elif lage == "tabelle":
            tab = next(iter(self._tabellen(d)))
            c = tab.cellAt(0, 0).firstCursorPosition()
        else:                                                    # Bild: das Zeichen des Bildes markieren
            c = QTextCursor(d)
            while not c.atEnd():
                c.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                if c.charFormat().isImageFormat():
                    break
                c.clearSelection()
        e.setTextCursor(c)
        if lage == "formatiert":
            self._vorformatieren(e)
        QApplication.instance().processEvents()

    @staticmethod
    def _vorformatieren(e):
        """Fett, kursiv, unterstrichen, durchgestrichen, Farbe, Marker, zentriert, eingerückt, Liste, Schattierung, Rahmen:
        damit auch Befehle, die etwas ausschalten, eine Wirkung zeigen."""
        from PySide6.QtGui import QBrush, QFont, QTextCharFormat
        from lunivo_writer.editor.zusatz import B_RAHMEN
        cf = QTextCharFormat()
        cf.setFontWeight(QFont.Bold); cf.setFontItalic(True); cf.setFontUnderline(True); cf.setFontStrikeOut(True)
        cf.setForeground(QColor("#c92a2a")); cf.setBackground(QColor("#ffec99")); cf.setFontPointSize(20)
        cf.setVerticalAlignment(QTextCharFormat.AlignSuperScript)
        c = e.textCursor(); c.mergeCharFormat(cf)
        bf = c.blockFormat()
        from PySide6.QtCore import Qt
        bf.setAlignment(Qt.AlignHCenter); bf.setLeftMargin(30); bf.setBackground(QBrush(QColor("#d0ebff")))
        bf.setProperty(B_RAHMEN, "#000000|1|einfach"); c.setBlockFormat(bf)
        e.setTextCursor(c)
        e.toggle_list("bullet")
        c = e.textCursor(); c.setPosition(14); c.setPosition(40, QTextCursor.KeepAnchor); e.setTextCursor(c)

    @staticmethod
    def _tabellen(d):
        from PySide6.QtGui import QTextTable
        b = d.firstBlock()
        while b.isValid():
            t = QTextCursor(b).currentTable()
            if t is not None:
                yield t
                return
            b = b.next()

    def schnappschuss(self):
        e, w = self.ed, self.w
        d = e.document()
        bloecke = []
        b = d.firstBlock()
        while b.isValid():
            bf = b.blockFormat()
            bloecke.append((bf.alignment(), bf.leftMargin(), bf.rightMargin(), bf.indent(), bf.topMargin(), bf.bottomMargin(),
                            bf.lineHeight(), bf.background().color().name() if bf.background().style() else "",
                            tuple(sorted((int(k), str(bf.property(k))) for k in bf.properties())),
                            b.textList().format().style() if b.textList() else None, b.isVisible()))
            b = b.next()
        c = e.textCursor()
        cb = QApplication.clipboard()
        sichtbar = hash(tuple((type(x).__name__, x.isVisible()) for x in w.findChildren(QWidget)))
        msg = getattr(getattr(w, "lbl_msg", None), "text", lambda: "")()
        return OrderedDict(dokument=repr(fragment_zu_daten(QTextDocumentFragment(d))), absaetze=repr(bloecke), auswahl=(c.anchor(), c.position()), zwischenablage=cb.text(), seiten=repr(getattr(e, "page", None)), zoom=getattr(e, "zoom", None),
                           gitter=getattr(e, "gitter", None), ui=sichtbar, tabs=len(w._doc_tabs()), vollbild=w.isFullScreen(),
                           msg=msg, status=w.statusBar().currentMessage(),
                           hell=QApplication.instance().palette().window().color().lightness())

    # ---- Ein Knopf --------------------------------------------------------------------------------------------------------
    def druecke(self, aktion, lage: str, ok: bool) -> dict:
        """Führt ``aktion()`` in einer Lage aus und beschreibt die Folgen."""
        self.modus_ok = ok
        self.beispiel(lage)
        QApplication.clipboard().setText("Zwischenablage")
        vorher = self.schnappschuss()
        n_fenster, n_menue, n_fehler, n_befehle = (len(self.fenster_log), len(self.menue_log), len(self.fehler_log), len(self.befehle_log))
        ergebnis = {"lage": lage, "fehler": None, "fenster": [], "menue": None, "befehle": [], "aenderung": [], "meldung": ""}
        try:
            aktion()
            for _ in range(4):
                QApplication.instance().processEvents()
        except Exception as ex:                                  # noqa: BLE001
            ergebnis["fehler"] = f"{type(ex).__name__}: {ex}"
        nachher = self.schnappschuss()
        ergebnis["fenster"] = self.fenster_log[n_fenster:]
        ergebnis["menue"] = self.menue_log[n_menue] if len(self.menue_log) > n_menue else None
        ergebnis["befehle"] = self.befehle_log[n_befehle:]
        if len(self.fehler_log) > n_fehler and not ergebnis["fehler"]:
            ergebnis["fehler"] = self.fehler_log[-1]
        ergebnis["aenderung"] = [k for k in vorher if vorher[k] != nachher[k] and k not in ("msg", "status")]
        if nachher["msg"] != vorher["msg"] or nachher["status"] != vorher["status"]:
            ergebnis["meldung"] = (nachher["msg"] or nachher["status"])[:90]
        return ergebnis

    def pruefe(self, aktion, pfad: str) -> dict:
        """Prüft einen Knopf in allen Lagen und fasst zusammen."""
        if os.environ.get("PRUEFUNG_VERFOLGEN"):
            print("  →", pfad, file=sys.stderr, flush=True)
        runden = [self.druecke(aktion, lage, False) for lage in LAGEN]
        fenster = sorted({f for r in runden for f in r["fenster"]})
        fehler = next((r["fehler"] for r in runden if r["fehler"]), None)
        menue = next((r["menue"] for r in runden if r["menue"] is not None), None)
        aend = sorted({a for r in runden for a in r["aenderung"]})
        meldung = next((r["meldung"] for r in runden if r["meldung"]), "")
        befehle = sorted({b for r in runden for b in r["befehle"]})
        ok_folge = None
        if fenster and any(f.startswith(("QMessageBox", "QFileDialog", "QColorDialog", "QFontDialog", "QInputDialog")) is False for f in fenster):
            ok_runden = [self.druecke(aktion, lage, True) for lage in LAGEN]
            ok_folge = {"fehler": next((r["fehler"] for r in ok_runden if r["fehler"]), None),
                        "aenderung": sorted({a for r in ok_runden for a in r["aenderung"]})}
        uebersprungen = any(b in AUSGENOMMEN for b in befehle)
        if fehler:
            urteil = "Fehler"
        elif fenster:
            urteil = "Dialog"
        elif menue is not None:
            urteil = "Menü"
        elif aend:
            urteil = "wirkt"
        elif meldung:
            urteil = "Meldung"
        elif uebersprungen:
            urteil = "übersprungen"
        else:
            urteil = "keine Wirkung"
        return {"pfad": pfad, "urteil": urteil, "fehler": fehler, "fenster": fenster, "menue": menue, "aenderung": aend,
                "meldung": meldung, "befehle": befehle, "ok": ok_folge}

    # ---- Das Band durchgehen ---------------------------------------------------------------------------------------------------
    def band_durchgehen(self, nur: set[str] | None):
        band = self.w.band
        leiste = band.findChild(QTabBar, "bandReiter")
        stapel = band.findChild(QStackedWidget, "bandStapel")
        ergebnisse = OrderedDict()
        for i in range(leiste.count()):
            name = leiste.tabText(i).strip()
            if not leiste.isTabVisible(i) and not name:
                continue
            if nur and name not in nur:
                continue
            leiste.setCurrentIndex(i)
            QApplication.instance().processEvents()
            seite = stapel.widget(i) if stapel is not None else None
            zeilen = []
            if seite is None:
                continue
            kennung = [(k.toolTip() or k.text()) for k in seite.findChildren(QToolButton) if k.toolTip() or k.text()]
            for nr, text in enumerate(kennung):
                # Manche Knöpfe bauen das Band neu auf (Oberfläche wechseln): Knöpfe deshalb jedes Mal frisch suchen
                try:
                    seite = stapel.widget(i)
                    jetzt = [k for k in seite.findChildren(QToolButton) if k.toolTip() or k.text()]
                except RuntimeError:                              # ein Knopf hat das ganze Band ersetzt: neu holen
                    leiste = self.w.band.findChild(QTabBar, "bandReiter")
                    stapel = self.w.band.findChild(QStackedWidget, "bandStapel")
                    leiste.setCurrentIndex(i)
                    seite = stapel.widget(i)
                    jetzt = [k for k in seite.findChildren(QToolButton) if k.toolTip() or k.text()]
                    zeilen.append({"pfad": f"{name} ▸ (nach {kennung[nr - 1].split(' — ')[0] if nr else 'Beginn'})", "name": "Band neu aufgebaut",
                                   "urteil": "Fehler", "fehler": "Der vorige Knopf hat das ganze Band ersetzt", "eintraege": []})
                k = jetzt[nr] if nr < len(jetzt) and (jetzt[nr].toolTip() or jetzt[nr].text()) == text else \
                    next((x for x in jetzt if (x.toolTip() or x.text()) == text), None)
                if k is None:
                    zeilen.append({"pfad": f"{name} ▸ {text.split(' — ')[0]}", "name": text.split(" — ")[0], "urteil": "Fehler",
                                   "fehler": "Knopf nach einem früheren Knopf nicht mehr da (Band neu aufgebaut)", "eintraege": []})
                    continue
                zeilen.append(self._knopf(k, name))
            ergebnisse[name] = zeilen
        return ergebnisse

    def _knopf(self, k: QToolButton, reiter: str) -> dict:
        name = (k.toolTip() or k.text()).split(" — ")[0].strip()
        pfad = f"{reiter} ▸ {name}"
        if k.property("fehlt"):
            return {"pfad": pfad, "urteil": "fehlt", "name": name, "eintraege": []}
        info = {"pfad": pfad, "name": name, "eintraege": []}
        menue = k.menu()                                          # vor dem Drücken merken: der Knopf kann das Band neu aufbauen
        if k.isEnabled():
            info.update(self.pruefe(k.click, pfad))
        else:
            info["urteil"] = "grau"
        if menue is not None:
            try:
                info["eintraege"] = self._menue_pruefen(menue, pfad)
            except RuntimeError:                                  # Menü gehörte zum alten Band
                info["fehler"] = info.get("fehler") or "Band wurde neu aufgebaut; Menü nicht mehr prüfbar"
            if info["urteil"] in ("keine Wirkung", "grau"):
                info["urteil"] = "Menü"
        return info

    def _menue_pruefen(self, menue: QMenu, pfad: str, tiefe: int = 0) -> list[dict]:
        out = []
        for a in menue.actions():
            if a.isSeparator() or not a.text().strip():
                continue
            text = a.text().replace("&", "").split("\t")[0]
            p = f"{pfad} ▸ {text}"
            if a.menu() is not None and tiefe < 3:
                out.append({"pfad": p, "name": text, "urteil": "Untermenü", "eintraege": self._menue_pruefen(a.menu(), p, tiefe + 1)})
                continue
            if "noch nicht umgesetzt" in a.toolTip():
                out.append({"pfad": p, "name": text, "urteil": "fehlt", "eintraege": []}); continue
            if not a.isEnabled():
                out.append({"pfad": p, "name": text, "urteil": "grau", "eintraege": []}); continue
            r = self.pruefe(a.trigger, p)
            r["name"] = text; r["eintraege"] = []
            out.append(r)
        return out


# ---- Bericht --------------------------------------------------------------------------------------------------------------------

def _flach(liste):
    for z in liste:
        yield z
        yield from _flach(z.get("eintraege", []))


def bericht(erg: OrderedDict) -> str:
    alle = [z for liste in erg.values() for z in _flach(liste)]
    zaehl = OrderedDict((u, 0) for u in ("wirkt", "Dialog", "Menü", "Untermenü", "Meldung", "übersprungen", "keine Wirkung", "grau", "fehlt", "Fehler"))
    for z in alle:
        zaehl[z.get("urteil", "?")] = zaehl.get(z.get("urteil", "?"), 0) + 1
    t = ["# Funktionsstand des Bandes", "",
         "Geschrieben von `werkzeug/funktionspruefung.py` (jeder Knopf und Menüpunkt wird in vier Lagen gedrückt: Text markiert, "
         "vorformatierter Text markiert, Zeiger in der Tabelle, Bild markiert).", "",
         "| Urteil | Anzahl |", "|---|---|"] + [f"| {u} | {n} |" for u, n in zaehl.items() if n] + [""]
    probleme = [z for z in alle if z.get("urteil") in ("Fehler", "fehlt", "keine Wirkung", "grau")]
    t += ["## Was nicht (richtig) geht", ""]
    for u in ("Fehler", "fehlt", "keine Wirkung", "grau"):
        sub = [z for z in probleme if z["urteil"] == u]
        if not sub:
            continue
        t += [f"### {u} ({len(sub)})", ""]
        for z in sub:
            extra = f" — `{z['fehler']}`" if u == "Fehler" and z.get("fehler") else ""
            t.append(f"- {z['pfad']}{extra}")
        t.append("")
    ok_fehler = [z for z in alle if z.get("ok") and z["ok"].get("fehler")]
    if ok_fehler:
        t += [f"### Dialog mit OK bestätigt: Fehler ({len(ok_fehler)})", ""] + [f"- {z['pfad']} — `{z['ok']['fehler']}`" for z in ok_fehler] + [""]
    ok_leer = [z for z in alle if z.get("ok") and not z["ok"].get("fehler") and not z["ok"]["aenderung"]]
    if ok_leer:
        t += [f"### Dialog mit OK bestätigt: nichts verändert ({len(ok_leer)})", ""] + [f"- {z['pfad']} — {', '.join(z['fenster'])}" for z in ok_leer] + [""]
    t += ["## Alles im Einzelnen", ""]
    for reiter, liste in erg.items():
        t += [f"### {reiter}", "", "| Knopf | Urteil | Einzelheiten |", "|---|---|---|"]
        for z in _flach(liste):
            tiefe = z["pfad"].count("▸") - 1
            einz = []
            if z.get("fenster"):
                einz.append("Fenster: " + "; ".join(z["fenster"])[:140])
            if z.get("aenderung"):
                einz.append("ändert: " + ", ".join(z["aenderung"]))
            if z.get("meldung"):
                einz.append("Meldung: " + z["meldung"])
            if z.get("fehler"):
                einz.append("Fehler: " + z["fehler"][:120])
            if z.get("ok"):
                einz.append("mit OK: " + (z["ok"]["fehler"] or ("ändert " + ", ".join(z["ok"]["aenderung"]) if z["ok"]["aenderung"] else "keine Wirkung")))
            if z.get("menue") and z["urteil"] == "Menü":
                einz.append(f"{len(z['menue'])} Einträge")
            t.append(f"| {'&nbsp;&nbsp;' * tiefe}{z['name']} | {z['urteil']} | {' · '.join(einz).replace('|', '/')} |")
        t.append("")
    return "\n".join(t)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ziel", default=os.path.join(WURZEL, "docs", "funktionsstand.md"))
    ap.add_argument("--reiter", default="", help="nur diese Reiter (Komma getrennt)")
    ap.add_argument("--verfolgen", action="store_true", help="jeden Knopf vor dem Drücken auf stderr nennen (findet hängende Knöpfe)")
    wahl = ap.parse_args()
    if wahl.verfolgen:
        os.environ["PRUEFUNG_VERFOLGEN"] = "1"
    app = QApplication.instance() or QApplication([])
    QStandardPaths.setTestModeEnabled(True)
    app.setApplicationName("lunivo-writer-pruefung"); app.setOrganizationName("lunivo-pruefung")
    with tempfile.TemporaryDirectory() as tmp:
        p = Pruefer(tmp)
        try:
            erg = p.band_durchgehen({r.strip() for r in wahl.reiter.split(",") if r.strip()} or None)
        except BaseException:                                   # noqa: BLE001 — der eigene excepthook würde es verschlucken
            traceback.print_exc()
            return 1
        p.uhr.stop()
        for t in p.w._doc_tabs():
            t.editor.document().setModified(False)
        p.w.close()
    text = bericht(erg)
    with open(wahl.ziel, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text.split("## Was nicht")[0])
    print(f"Bericht: {wahl.ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
