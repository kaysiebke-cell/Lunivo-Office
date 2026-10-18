#!/usr/bin/env python3
"""Schreibt doku/native-qt/ABGLEICH.md: jeder Knopf des alten Registers — umgesetzt oder offen.

Aufruf:  python3 werkzeug/abgleich-native.py
Die Liste wird erzeugt, nicht von Hand gepflegt.
"""
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, WURZEL)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
from native_qt.windows.befehle import Befehle  # noqa: E402

b = Befehle(None)
reg = json.load(open(os.path.join(WURZEL, "native_qt/resources/register.json"), encoding="utf-8"))
zeilen, ok, offen = [], 0, 0


def namen(e):
    r = []
    for k in ("tun", "klappe"):
        if e.get(k):
            r.append(e[k])
    for m in e.get("menue", []):
        r += namen(m)
    return r


from native_qt.widgets.reiterplan import plan, schreibhilfe_gruppen  # noqa: E402
reiter = plan(reg) + [{'name': 'Seitenleiste: Schreibhilfe', 'gruppen': schreibhilfe_gruppen(reg)}]
for t in reiter:
    zeilen.append(f"\n## {t['name']}" + (" (Kontext-Register)" if t.get('kontext') else "") + "\n")
    for g in t["gruppen"]:
        zeilen.append(f"**{g['name']}**\n")
        if g.get("katalog"):
            zeilen.append("- ✅ Stilkatalog (Standard, Überschrift 1–3, Titel, Untertitel, Zitat, Kein Abstand)")
        for e in g.get("knoepfe", []):
            if e.get("hinweis") or e.get("zeilenumbruch") or e.get("symbol") == "//":
                continue
            ns = namen(e)
            fertig = bool(ns) and all(b.hat(n) or b.klappe(n) is not None for n in ns if not n.endswith("Klappe")) \
                if ns else False
            if e.get("menue"):
                fertig = any(b.hat(n) for n in ns)
            ok += fertig
            offen += not fertig
            zeilen.append(f"- {'✅' if fertig else '⬜'} {e['name']}" + ("" if fertig else f"  (`{', '.join(ns) or '—'}`)"))
        zeilen.append("")
kopf = (f"# Abgleich: altes Register ↔ native Qt-Fassung\n\n"
        f"Erzeugt von `werkzeug/abgleich-native.py`. **{ok} Knöpfe umgesetzt, {offen} offen.** "
        "Offene Knöpfe stehen im Programm sichtbar, aber ausgegraut da.\n")
out = os.path.join(WURZEL, "doku", "native-qt", "ABGLEICH.md")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(kopf + "\n".join(zeilen) + "\n")
print(ok, "umgesetzt,", offen, "offen →", out)
