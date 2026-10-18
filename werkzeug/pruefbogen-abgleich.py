#!/usr/bin/env python3
"""Gleicht den Prüfbogen (415 Punkte) mit der nativen Fassung ab → doku/native-qt/PRUEFBOGEN.md.

Quelle: doku/native-qt/pruefbogen/pruefbogen.json (aus dem Artefakt „Prüfkatalog WPS Writer + Lunivo Office“).
Status je Punkt:  ✅ umgesetzt   ◐ teilweise / anders gelöst   ⬜ offen
Die Zuordnung steht in doku/native-qt/pruefbogen/zuordnung.json (von Hand gepflegt, jede Zeile mit „wo“).
Punkte ohne Eintrag werden automatisch über den Namen im Band (Befehle.hat) zugeordnet.
"""
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, WURZEL)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
from native_qt.widgets.reiterplan import plan  # noqa: E402
from native_qt.windows.befehle import Befehle  # noqa: E402

B = Befehle(None)
bogen = json.load(open(os.path.join(WURZEL, "doku/native-qt/pruefbogen/pruefbogen.json"), encoding="utf-8"))
reg = json.load(open(os.path.join(WURZEL, "native_qt/resources/register.json"), encoding="utf-8"))
zpfad = os.path.join(WURZEL, "doku/native-qt/pruefbogen/zuordnung.json")
zuordnung = json.load(open(zpfad, encoding="utf-8")) if os.path.exists(zpfad) else {}


def norm(s: str) -> str:
    s = s.replace("*", "").strip().lower()
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^a-zäöüß0-9]+", "", s)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9äöüß]+", "-", s.lower())


def namen(e):
    r = []
    for k in ("tun", "klappe"):
        if e.get(k):
            r.append(e[k])
    for m in e.get("menue", []):
        r += namen(m)
    return r


# Name im Band → fertig?
band = {}
alle = plan(reg)
for t in alle:
    for g in t["gruppen"]:
        for e in g.get("knoepfe", []):
            if e.get("hinweis") or e.get("symbol") == "//" or not e.get("name"):
                continue
            ns = namen(e)
            fertig = bool(ns) and any(B.hat(n) or callable(getattr(B, "menue_" + n.split(":")[0].replace(".", "_"), None)) for n in ns)
            band.setdefault(norm(e["name"]), []).append((t["name"], g["name"], fertig))
            for m in e.get("menue", []):
                if m.get("name"):
                    mf = bool(m.get("tun")) and B.hat(m["tun"])
                    band.setdefault(norm(m["name"]), []).append((t["name"], g["name"] + " ▸ " + e["name"], mf))

zeilen, zaehl = [], {"✅": 0, "◐": 0, "⬜": 0}
for k in bogen["items"]:
    cat = k["cat"]
    zeilen.append(f"\n## {cat}\n")
    for it in k["items"]:
        schl = f"{cat}|{it.rstrip('*')}"
        z = zuordnung.get(schl)
        if z:
            st, wo = z["status"], z.get("wo", "")
        else:
            n = norm(it.split(">")[-1])
            treffer = band.get(n) or band.get(norm(it))
            if treffer:
                st = "✅" if any(t[2] for t in treffer) else "⬜"
                wo = "Band: " + ", ".join(sorted({f"{a} ▸ {b}" for a, b, _ in treffer}))[:120]
            else:
                st, wo = "⬜", "(noch nicht zugeordnet)"
        zaehl[st] += 1
        ki = bogen["ki_stand"].get(slug(cat) + "|" + slug(it.rstrip("*")).strip("-"), {}).get("stand", "")
        zeilen.append(f"- {st} {it.rstrip('*')} — {wo}" + (f"  _(Web-Fassung: {ki})_" if ki else ""))
kopf = (f"# Prüfbogen ↔ native Fassung\n\nErzeugt von `werkzeug/pruefbogen-abgleich.py` aus dem Prüfkatalog "
        f"(415 Punkte). **✅ {zaehl['✅']} · ◐ {zaehl['◐']} · ⬜ {zaehl['⬜']}**. "
        "✅ = Befehl/Funktion vorhanden (einzeln getestet nur, wo `tests/` es belegt); "
        "◐ = teilweise oder anders gelöst; ⬜ = offen.\n"
        "Die Bilder des Bogens (bindend, 1 zu 1) liegen unter `doku/native-qt/pruefbogen/bilder/`.\n")
open(os.path.join(WURZEL, "doku/native-qt/PRUEFBOGEN.md"), "w", encoding="utf-8").write(kopf + "\n".join(zeilen) + "\n")
print(zaehl)
