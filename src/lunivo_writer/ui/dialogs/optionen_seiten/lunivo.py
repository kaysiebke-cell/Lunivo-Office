"""Optionen: KI, Gedächtnis, Erweitert."""
from __future__ import annotations

import json
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget
from lunivo_writer.ui.baukasten.beschriftung import text_label
from lunivo_writer.ai import ki as K
from lunivo_writer.services import vorlesen
from lunivo_writer.proofing.vorhersage import EMPFAENGER
from lunivo_writer.ui.dialogs.optionen_seiten.gemeinsam import LESESCHRIFTEN, _Seite


class LunivoSeiten:
    """Optionen: KI, Gedächtnis, Erweitert. Baustein von ``OptionenAnsicht`` (siehe ``lunivo_writer/ui/dialogs/optionen.py``)."""


    # ================= Nur bei Lunivo =================
    def _ki(self, titel):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        p = _Seite(self.w, titel)
        k = self.w.ki.konfig
        geaendert = self.w.ki.geaendert
        f = p.gruppe("Prüfung und KI")
        f.addRow(text_label("KI-Konfiguration", pt=11, umbruch=False))
        combos: dict[str, QComboBox] = {}

        def standard_name() -> str:
            mid = k["modell"]
            if not mid:
                return "(keines)"
            for m in k.alle_modelle():
                if m["id"] == mid:
                    return m["name"]
            return mid[len(K.OLLAMA_MARKE):] if mid.startswith(K.OLLAMA_MARKE) else mid

        def aufgaben_fuellen():
            for aufgabe, c in combos.items():
                c.blockSignals(True); c.clear()
                c.addItem(f"Standard ({standard_name()})", "")
                for m in k.alle_modelle():
                    if aufgabe == "bildgenerierung" and ("bilder" not in m["verwendungFuer"] or not m["id"].startswith(K.EIGEN_MARKE)):
                        continue
                    c.addItem(m["name"] + ("  · lokal" if m["lokal"] else ""), m["id"])
                c.setCurrentIndex(max(0, c.findData(k["aufgaben"].get(aufgabe, ""))))
                c.blockSignals(False)
        for aufgabe, name in K.AUFGABEN:
            c = QComboBox()
            combos[aufgabe] = c
            c.currentIndexChanged.connect(lambda _i, a=aufgabe, c=c: (k.aufgabe_setzen(a, c.currentData() or ""), geaendert.emit()))
            f.addRow(name, c)
        mb = QPushButton("KI-Modelle bearbeiten"); mb.setFlat(True); mb.setCursor(Qt.PointingHandCursor)
        mb.setStyleSheet("QPushButton { color: #5b9bd5; text-align: left; border: none; padding: 4px 0; }")
        f.addRow(mb)

        schluessel = QLineEdit(k["apiKey"]); schluessel.setEchoMode(QLineEdit.Password); schluessel.setPlaceholderText("sk-ant-…")
        schluessel.setProperty("optName", "API-Schlüssel")
        f.addRow("API-Schlüssel", schluessel)
        hinweis = QLabel(); hinweis.setStyleSheet("color: palette(window-text); font-size: 9pt;"); hinweis.setWordWrap(True)
        f.addRow(hinweis)
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 0, 0, 0)
        zeigen = QPushButton("Anzeigen"); zeigen.setCheckable(True)
        kopie = QPushButton("Kopieren")
        loeschen = QPushButton("Schlüssel löschen")
        erstellen = QPushButton("Schlüssel erstellen ↗"); erstellen.setFlat(True); erstellen.setCursor(Qt.PointingHandCursor)
        erstellen.setStyleSheet("QPushButton { color: #5b9bd5; border: none; }")
        for b in (zeigen, kopie, loeschen, erstellen):
            h.addWidget(b)
        h.addStretch(1)
        f.addRow(zeile)

        def schluessel_stand():
            hinweis.setText("Gespeichert in " + k.pfad + " (nur für dich lesbar). Bei Nutzung von Claude geht der Text an Anthropic — "
                            "vorher fragt das Programm um Erlaubnis." if k["apiKey"] else
                            "Kein Schlüssel — für das Modell auf diesem Rechner braucht es auch keinen.")
            for b in (zeigen, kopie, loeschen):
                b.setEnabled(bool(schluessel.text().strip()))
        schluessel.editingFinished.connect(lambda: (k.setze("apiKey", schluessel.text().strip()), schluessel_stand(), geaendert.emit()))
        schluessel.textChanged.connect(lambda _t: [b.setEnabled(bool(schluessel.text().strip())) for b in (zeigen, kopie, loeschen)])
        zeigen.toggled.connect(lambda an: (schluessel.setEchoMode(QLineEdit.Normal if an else QLineEdit.Password),
                                           zeigen.setText("Verbergen" if an else "Anzeigen")))
        kopie.clicked.connect(lambda: QApplication.clipboard().setText(schluessel.text().strip()))

        def loesche():
            if QMessageBox.question(self, "Schlüssel löschen", "Den gespeicherten Schlüssel wirklich löschen?") == QMessageBox.Yes:
                schluessel.clear(); k.setze("apiKey", ""); schluessel_stand(); geaendert.emit()
        loeschen.clicked.connect(loesche)
        erstellen.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.anthropic.com/settings/keys")))

        modell = QComboBox()
        f.addRow("KI-Modell", modell)

        def modell_fuellen():
            modell.blockSignals(True); modell.clear()
            modell.addItem("(keines)", "")
            for mid, name in K.MODELLE_FEST:
                modell.addItem(name, mid)
            for m in self.w.ki.ki.ollama_modelle():
                modell.addItem(f"Auf diesem Rechner: {m}", K.OLLAMA_MARKE + m)
            for a in k["anbieter"]:
                modell.addItem(f"{a['name']} ({a['modell']})", K.EIGEN_MARKE + a["id"])
            modell.setCurrentIndex(max(0, modell.findData(k["modell"])))
            modell.blockSignals(False)
        modell.currentIndexChanged.connect(lambda _i: (k.setze("modell", modell.currentData()), aufgaben_fuellen(), geaendert.emit()))

        anb = QWidget(); av = QVBoxLayout(anb); av.setContentsMargins(0, 4, 0, 4); av.setSpacing(6)
        anb.setProperty("optName", "Eigene Anbieter")
        f.addRow(QLabel("Eigene Anbieter"))
        f.addRow(anb)
        neuer = QPushButton("Anbieter hinzufügen …")
        f.addRow(neuer)

        def anbieter_fuellen():
            while av.count():
                it = av.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            if not k["anbieter"]:
                av.addWidget(QLabel("Noch keiner angelegt — Ollama, OpenAI, OpenRouter, Gemini, Mistral …"))
            for a in k["anbieter"]:
                z = QWidget(); zh = QHBoxLayout(z); zh.setContentsMargins(0, 0, 0, 0)
                teile = [a["modell"], "Lokaler Anbieter" if K.ist_lokale_url(a["url"]) else "Über das Internet"]
                zh.addWidget(QLabel(f"{a['name']}  ·  {' · '.join(t for t in teile if t)}"), 1)
                eb = QPushButton("Entfernen")
                eb.clicked.connect(lambda _=False, i=a["id"]: (k.anbieter_entfernen(i), alles_neu(), geaendert.emit()))
                zh.addWidget(eb)
                av.addWidget(z)

        def alles_neu():
            aufgaben_fuellen(); modell_fuellen(); anbieter_fuellen()

        def anbieter_neu():
            from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
            from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
            ausfuehren(KIEinstellungenDialog(self.w, 0))
            alles_neu(); geaendert.emit()

        def modelle_bearbeiten():
            from lunivo_writer.ui.baukasten.fenster_stapel import ausfuehren
            from lunivo_writer.ui.dialogs.ki_dialoge import KIEinstellungenDialog
            ausfuehren(KIEinstellungenDialog(self.w, 0))
            alles_neu(); geaendert.emit()
        neuer.clicked.connect(anbieter_neu)
        mb.clicked.connect(modelle_bearbeiten)

        f.addRow(QLabel("Eigene Assistenten"))
        ass = QWidget(); sv = QVBoxLayout(ass); sv.setContentsMargins(0, 4, 0, 4); sv.setSpacing(6)
        ass.setProperty("optName", "Eigene Assistenten")
        f.addRow(ass)
        na = QPushButton("Neuen Assistenten erstellen …")
        f.addRow(na)

        def assistenten_fuellen():
            while sv.count():
                it = sv.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            if not k["assistenten"]:
                sv.addWidget(QLabel("Noch keiner angelegt."))
            for a in k["assistenten"]:
                z = QWidget(); zh = QHBoxLayout(z); zh.setContentsMargins(0, 0, 0, 0)
                zh.addWidget(QLabel(a["name"]), 1)
                eb = QPushButton("Entfernen")
                eb.clicked.connect(lambda _=False, i=a["id"]: (k.assistent_entfernen(i), assistenten_fuellen()))
                zh.addWidget(eb)
                sv.addWidget(z)
        na.clicked.connect(lambda: (self.w.befehle.w_assistentErstellen(), assistenten_fuellen()))

        wen = QComboBox(); wen.addItems(EMPFAENGER)
        wen.setCurrentText(self.w.assistant.thema)
        wen.currentTextChanged.connect(self.w.assistant.setze_thema)
        self.w.assistant.themaGeaendert.connect(lambda t: wen.currentText() != t and (wen.blockSignals(True), wen.setCurrentText(t), wen.blockSignals(False)))
        f.addRow("Für wen der Text ist", wen)

        verbrauch = QWidget(); vh = QHBoxLayout(verbrauch); vh.setContentsMargins(0, 2, 0, 2)
        vh.addWidget(QLabel("Verbrauch"))
        vh.addWidget(QLabel("Noch nichts verbraucht." if not k["kosten"] else f"Bisherige Kosten: {K.als_geld(k['kosten'])}"))
        auf = QPushButton("Guthaben aufladen ↗"); auf.setFlat(True); auf.setCursor(Qt.PointingHandCursor)
        auf.setStyleSheet("QPushButton { color: #5b9bd5; border: none; }")
        auf.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.anthropic.com/settings/billing")))
        vh.addWidget(auf); vh.addStretch(1)
        f.addRow(verbrauch)
        alles_neu(); assistenten_fuellen(); schluessel_stand()
        self.w.ki.geaendert.connect(lambda: (aufgaben_fuellen(), modell_fuellen(), anbieter_fuellen()))
        p.abschluss()
        return p


    def _gedaechtnis(self, titel):
        from PySide6.QtWidgets import QFileDialog, QListWidget
        p = _Seite(self.w, titel)
        g = self.w.assistant.gelernt
        f = p.gruppe("Gelernte Schreibweisen")
        zeile = QWidget(); h = QHBoxLayout(zeile); h.setContentsMargins(0, 2, 0, 2)
        lab = QLabel(); lab.setStyleSheet("color: palette(window-text);")
        vergessen = QPushButton("vergessen")
        h.addWidget(lab, 1); h.addWidget(vergessen)
        f.addRow(zeile)
        zeile.setProperty("optName", "Gelernte Schreibweisen")
        liste = QListWidget(); liste.setMinimumHeight(120); liste.setAccessibleName("Gelernte Schreibweisen")

        def fuellen():
            d = g.daten
            lab.setText(f"{len(d['woerter'])} eigene Schreibweisen · {len(d['inRuhe'])} Wörter in Ruhe gelassen")
            liste.clear()
            for alt, neu in sorted(d["woerter"].items()):
                liste.addItem(f"{alt} → {neu}")
            for w_ in sorted(d["inRuhe"]):
                liste.addItem(f"{w_} (in Ruhe lassen)")
            vergessen.setEnabled(bool(d["woerter"] or d["inRuhe"] or d["gezeigt"] or d["ki"]))
        f.addRow(liste)
        eb = QPushButton("Markierten Eintrag entfernen")

        def eintrag_weg():
            it = liste.currentItem()
            if not it:
                return
            t = it.text()
            if " → " in t:
                g.daten["woerter"].pop(t.split(" → ")[0], None)
            else:
                g.daten["inRuhe"].pop(t.replace(" (in Ruhe lassen)", ""), None)
            g.speichern(); fuellen(); self.w.assistant.pruefen(voll=True)
        eb.clicked.connect(eintrag_weg)

        def weg():
            if QMessageBox.question(self, "Vergessen", "Wirklich alles Gelernte löschen?") == QMessageBox.Yes:
                g.vergessen(); fuellen(); self.w.assistant.pruefen(voll=True)
        vergessen.clicked.connect(weg)

        def sichern():
            pfad, _ = QFileDialog.getSaveFileName(self, "Gelerntes sichern", "gelernt.json", "JSON (*.json)")
            if pfad:
                try:
                    with open(pfad, "w", encoding="utf-8") as fh:
                        json.dump(g.daten, fh, ensure_ascii=False, indent=1)
                except OSError as ex:
                    QMessageBox.warning(self, "Sichern", f"Das ging nicht: {ex}")

        def einspielen():
            pfad, _ = QFileDialog.getOpenFileName(self, "Gelerntes einspielen", "", "JSON (*.json)")
            if not pfad:
                return
            try:
                with open(pfad, encoding="utf-8") as fh:
                    neu = json.load(fh)
                for key in g.daten:
                    if isinstance(neu.get(key), dict):
                        g.daten[key].update(neu[key])
            except (OSError, ValueError) as ex:
                QMessageBox.warning(self, "Einspielen", f"Das ging nicht: {ex}")
                return
            g.speichern(); fuellen(); self.w.assistant.pruefen(voll=True)
        z2 = QWidget(); h2 = QHBoxLayout(z2); h2.setContentsMargins(0, 2, 0, 2)
        b1 = QPushButton("Sichern"); b2 = QPushButton("Einspielen")
        b1.clicked.connect(sichern); b2.clicked.connect(einspielen)
        h2.addWidget(b1); h2.addWidget(b2); h2.addWidget(eb); h2.addStretch(1)
        f.addRow(z2)
        fuellen()
        p.hinweis("Das Gedächtnis liegt als Datei auf diesem Rechner und wird nur auf deinen Wunsch an eine KI mitgeschickt (als Steckbrief).")
        p.abschluss()
        return p


    def _erweitert(self, titel):
        from lunivo_writer.services.integrations import languagetool, libreoffice
        from lunivo_writer.services.settings_service import data_dir
        p = _Seite(self.w, titel)

        def groesse(pfad) -> str:
            gesamt = 0
            if pfad and os.path.exists(pfad):
                if os.path.isfile(pfad):
                    gesamt = os.path.getsize(pfad)
                for wurzel, _d, dateien in os.walk(pfad):
                    for n in dateien:
                        try:
                            gesamt += os.path.getsize(os.path.join(wurzel, n))
                        except OSError:
                            pass
            mb = gesamt / 1048576
            return "" if not gesamt else (f"{mb:.0f} MB" if mb >= 10 else f"{mb:.1f} MB".replace(".", ","))

        soffice = libreoffice.finde_soffice()
        lo_pfad = os.path.dirname(os.path.realpath(soffice)) if soffice else ""
        lt = languagetool.jar_finden()
        _prog, piper = vorlesen.piper_programm()
        stimmen = vorlesen.piper_stimmen() if piper else []
        schriften = [n for n in LESESCHRIFTEN if n in QFontDatabase.families()]
        schr_ordner = os.path.expanduser("~/.local/share/fonts/lunivo-office")
        karten = [
            ("Umwandlungsprogramm", "ODT, DOC, RTF und EPUB", bool(soffice), lo_pfad, "nicht installiert"),
            ("LanguageTool", "„Gründlich prüfen“ — Grammatik über die eigenen Regeln hinaus", bool(lt), languagetool.ordner(), "./… holen"),
            (f"Stimmen zum Vorlesen ({len(stimmen)})", "aufgenommene Stimmen statt der blechernen des Systems", bool(stimmen), piper, "stimme-holen.sh"),
            (f"Schriften zum leichteren Lesen ({len(schriften)})", ", ".join(schriften) or "OpenDyslexic, Lexend, Atkinson Hyperlegible",
             bool(schriften), schr_ordner, "schrift-holen.sh"),
        ]
        f = p.gruppe("Was zusätzlich geholt wurde")
        for name, beschr, da, pfad, fehlt in karten:
            k = QFrame(); k.setObjectName("optSchriftkarte")
            h = QHBoxLayout(k); h.setContentsMargins(12, 10, 12, 10)
            badge = QLabel("DA" if da else "—")
            badge.setAlignment(Qt.AlignCenter); badge.setFixedWidth(36)
            badge.setStyleSheet("background: %s; color: white; border-radius: 4px; font-weight: 700; font-size: 8pt; padding: 3px;"
                                % ("#3aa57a" if da else "#6b7280"))
            h.addWidget(badge, 0, Qt.AlignTop)
            v = QVBoxLayout(); v.setSpacing(2)
            v.addWidget(text_label(name, fett=True, umbruch=False))
            b = QLabel(beschr if da else f"{beschr} — nicht vorhanden ({fehlt})")
            b.setWordWrap(True); b.setStyleSheet("color: palette(window-text); font-style: italic;")
            v.addWidget(b)
            h.addLayout(v, 1)
            gr = QLabel(groesse(pfad) if da else ""); gr.setStyleSheet("color: palette(window-text); font-size: 9pt;")
            h.addWidget(gr, 0, Qt.AlignTop)
            f.addRow(k)
        f = p.gruppe("Daten")
        p.zeile(f, data_dir())
        p.abschluss()
        return p
