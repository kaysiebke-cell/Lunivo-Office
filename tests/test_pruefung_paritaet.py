"""Die Python-Prüfung muss dieselben Funde liefern wie oberflaeche/js/pruefung.js."""
import importlib.util
import json
import os
import shutil
import subprocess

import pytest

from native_qt.services import pruefung

HIER = os.path.dirname(os.path.abspath(__file__))
SAETZE = [
    "hiermit lege ich Widerspruch gegen Ihren Bescheid ein. Ich glaube das das nicht stimmt.",
    "Wir hat im letzten Monat keine Zahlung erhalten, weil der Antrag noch nicht bearbeitet hat.",
    "Seid gestern ist alles anders.  Ihr seit nett.",
    "Das ist größer wie ich dachte. Er ist älter wie sie.",
    "Ich denke das er kommt aber er kommt nicht",
    "Ich hoffe,dass es klappt .Danke",
    "Das Wort steht steht doppelt da. Peter's Auto ist da.",
    "vieleicht kommt er shcon morgen. Termien sind wichtig.",
    "Beim schreiben passieren Fehler. Zum neuen Haus gehen wir.",
    "Dieser Satz ist sehr lang und enthält viele Wörter die niemand braucht und die man auch streichen könnte weil sie nur den Lesefluss stören und am Ende doch nichts aussagen als dass sie da sind.",
    "Mit freundlichen Grüßen",
    "Siehe kaysiebke-cell/schreibhilfe. Git ist toll. Mail an max@beispiel.de. Danke.",
    "Ich bin dem Haus gegangen. Du hast ein Auto gekauft aber ich nicht.",
    "z. B. kann man das so machen. Ca. 5 Stück.",
    "Zahnriemenspanner-Kettenrolle ist ein langes Wort.",
]


def js(fälle):
    node = shutil.which("node")
    if not node:
        pytest.skip("node nicht installiert")
    r = subprocess.run([node, os.path.join(HIER, "vergleich_pruefung.js")], input="\n".join(json.dumps(f) for f in fälle),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return [json.loads(z) for z in r.stdout.splitlines()]


def py(text, gelernt):
    return [{k: f[k] for k in ("von", "bis", "alt", "neu", "grund", "art")}
            for f in pruefung.finde_probleme(text, gelernt)]


def test_python_equals_javascript():
    leer = {"woerter": {}, "inRuhe": {}}
    fälle = [{"text": s, "gelernt": leer} for s in SAETZE]
    fälle.append({"text": "Das Vieleicht und Wiederspruch.", "gelernt": {"woerter": {"vieleicht": "vielleicht"}, "inRuhe": {}}})
    fälle.append({"text": "Meyr kam heute.", "gelernt": {"woerter": {}, "inRuhe": {"meyr": True}}})
    js_ergebnis = js(fälle)
    for f, j in zip(fälle, js_ergebnis):
        assert py(f["text"], f["gelernt"]) == j, f["text"]
    # und es wird tatsächlich etwas gefunden (kein stiller Gleichstand aus lauter Leere)
    assert sum(len(j) for j in js_ergebnis) >= 15
