"""Die Python-Prüfung muss dieselben Funde liefern wie oberflaeche/js/pruefung.js des Zweigs `main`.

Läuft nur mit LUNIVO_ALT=<Pfad zu einem Checkout von main> und installiertem node; sonst übersprungen."""
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
    if not node or not os.environ.get("LUNIVO_ALT"):
        pytest.skip("Vergleich mit der alten JS-Prüfung: node und LUNIVO_ALT=<Checkout von main> nötig")
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


def _korpus():
    """Texte aus der Projektdokumentation, mit künstlich eingebauten Fehlern (feste Zufallszahlen)."""
    import glob
    import random
    import re
    random.seed(7)
    wurzel = os.path.dirname(HIER)
    texte = []
    for f in sorted(glob.glob(os.path.join(wurzel, "doku", "*.md"))) + [os.path.join(wurzel, "README.md")]:
        try:
            t = open(f, encoding="utf-8").read()
        except OSError:
            continue
        for z in re.split(r"\n\s*\n", t):
            z = re.sub(r"[`*#|>\-]+", " ", z).strip()
            if 20 < len(z) < 400:
                texte.append(z)
    random.shuffle(texte)
    ersetz = [("dass", "das"), ("das ", "dass "), (" seit ", " seid "), (" wie ", " als "), (", ", ","),
              (" und ", " und  "), ("Widerspruch", "Wiederspruch"), ("ist ", "ist ist "), (". ", ".")]

    def mut(s):
        for a, b in random.sample(ersetz, 3):
            if a in s:
                s = s.replace(a, b, 1)
        if random.random() < .3:
            s = s[0].lower() + s[1:]
        ws = s.split(" ")
        for _ in range(3):
            i = random.randrange(len(ws)); w = ws[i]; m = ""
            if len(w) > 4:
                k = random.randrange(1, len(w) - 1); m = random.choice(["del", "swap", "sub", "join"])
                if m == "del": w = w[:k] + w[k + 1:]
                elif m == "swap" and k + 2 <= len(w): w = w[:k] + w[k + 1] + w[k] + w[k + 2:]
                elif m == "sub": w = w[:k] + random.choice("aeiounrst") + w[k + 1:]
                ws[i] = w
            if m == "join" and i + 1 < len(ws):
                ws[i] = ws[i] + ws[i + 1]; ws[i + 1] = ""
        s = " ".join(ws)
        if random.random() < .2:
            s += " Sie sind ein Beispiel fuer http://x.de/y. und kaysiebke-cell/schreibhilfe. Git ist toll"
        return s
    fälle = []
    for t in texte[:700]:
        fälle.append({"text": t, "gelernt": {"woerter": {}, "inRuhe": {}}})
        fälle.append({"text": mut(t), "gelernt": {"woerter": {"vieleicht": "vielleicht"}, "inRuhe": {"meyr": True}}})
    return fälle


def test_python_equals_javascript_grosser_korpus():
    if not os.environ.get("LUNIVO_ALT"):
        pytest.skip("nur mit LUNIVO_ALT=<Checkout von main> und node")
    fälle = _korpus()
    assert len(fälle) >= 400
    js_ergebnis = js(fälle)
    abweichend = [f["text"][:80] for f, j in zip(fälle, js_ergebnis) if py(f["text"], f["gelernt"]) != j]
    assert abweichend == [], f"{len(abweichend)} von {len(fälle)} weichen ab, z. B. {abweichend[:3]}"
    assert sum(len(j) for j in js_ergebnis) > 200          # es wird wirklich etwas gefunden


def test_vorschlaege_und_phonetik_gleich_wie_javascript():
    import subprocess
    wörter = ["kwalität", "fileicht", "ferzeihung", "exdra", "vieleicht", "Halloch", "gemcht", "shcon", "wiederspruch",
              "bescheit", "antrg", "zahlnug", "mitlieder", "unterlagn", "fristen", "Meyer", "kwalitaet", "sähr", "ferzeihen",
              "hallo", "fileich", "tele", "verträg", "geerter", "dankeschön"]
    ein = "\n".join(json.dumps({"wort": w, "gelernt": {"woerter": {"halloch": "hallo"}, "inRuhe": {}}}) for w in wörter)
    node = shutil.which("node")
    if not node or not os.environ.get("LUNIVO_ALT"):
        pytest.skip("Vergleich mit der alten JS-Prüfung: node und LUNIVO_ALT=<Checkout von main> nötig")
    r = subprocess.run([node, os.path.join(HIER, "vergleich_vorschlaege.js")], input=ein, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    erg = [json.loads(z) for z in r.stdout.splitlines()]
    for w, j in zip(wörter, erg):
        assert pruefung.koelner_phonetik(w) == j["k"], w
        assert pruefung.klingt_wie(w) == j["kw"], w
        assert pruefung.vorschlaege_fuer(w, 6, {"woerter": {"halloch": "hallo"}}) == j["v"], w
