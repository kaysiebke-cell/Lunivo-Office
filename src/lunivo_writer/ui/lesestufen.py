"""Die drei Lesestufen der Lesehilfe — gemeinsam für die Optionen und die rechte Seitenleiste.

Eine Stufe stellt Papierton, Buchstaben- und Wortabstand, „Absatz beim Schreiben“ und „Übriger Text“ auf einmal (wie in der ersten
Fassung). Der Zeilenfokus gehört nicht dazu: Er ist ein eigener Schalter, und wer ihn anhat, fällt deswegen nicht aus seiner Stufe.
"""
from __future__ import annotations

STUFEN = {
    "Standard": dict(papier="Weiß", buchstaben=0.0, wort=0.0, luft=1.0, groesser="keine", zurueck="keine",
                     text=["Weißes Blatt, normale Abstände, kein Absatzfokus. So, wie jedes andere Schreibprogramm es zeigt.",
                           "Vorgesehen für alle, die beim Lesen keine Hilfe brauchen."]),
    "Leichter lesen": dict(papier="Creme", buchstaben=0.45, wort=1.8, luft=1.15, groesser="etwas", zurueck="etwas",
                           text=["Cremefarbenes Blatt, etwas mehr Luft zwischen Buchstaben und Wörtern. Der Absatz, in dem du stehst, "
                                 "tritt hervor; die übrigen treten zurück — aber sie bleiben lesbar.",
                                 "Vorgesehen als der Normalfall dieses Programms."]),
    "Sehr leicht lesen": dict(papier="Gelblich", buchstaben=0.9, wort=3.6, luft=1.35, groesser="deutlich", zurueck="etwas",
                              text=["Blassgelbes Blatt, deutlich mehr Luft, starker Absatzfokus. Auf das Blatt passt weniger Text — "
                                    "das ist der Preis und der Zweck zugleich.",
                                    "Vorgesehen, wenn Lesen wirklich schwerfällt."]),
}
# Die Auswahlen der Felder — dieselben in den Optionen und im Fenster „Lesehilfe“ (Anzeige, Wert)
BUCHSTABEN = [("normal", 0.0), ("etwas mehr", 0.45), ("deutlich mehr", 0.9), ("sehr viel", 1.35)]
WORT = [("normal", 0.0), ("etwas mehr", 1.8), ("deutlich mehr", 3.6), ("sehr viel", 5.4)]
GROESSER = [("nicht vergrößern", "keine"), ("etwas größer", "etwas"), ("deutlich größer", "deutlich")]
ZURUECK = [("gleich lassen", "keine"), ("etwas blasser", "etwas"), ("deutlich blasser", "deutlich")]
ZEILENFOKUS = [("aus", False), ("die Zeile hervorheben", True)]
ZEILENLUFT = [("normal", 1.0), ("etwas mehr", 1.15), ("deutlich mehr", 1.35), ("sehr viel", 1.6)]      # nur beim Bearbeiten, nie im Dokument
EIGENE = ["Eigene Einstellung: Die Felder darunter stehen auf einer Mischung, die zu keiner der drei Stufen passt.",
          "Eine Stufe anklicken stellt alle Felder auf einmal um."]


def aktuell(s) -> str:
    """Name der Stufe, auf der die Einstellungen gerade stehen, oder „“ (eigene Einstellung)."""
    for name, st in STUFEN.items():
        if (str(s.get("lesehilfe/papier", "Weiß")) == st["papier"]
                and abs(float(s.get("lesehilfe/buchstaben", 0)) - st["buchstaben"]) < 0.01
                and abs(float(s.get("lesehilfe/wort", 0)) - st["wort"]) < 0.01
                and abs(float(s.get("lesehilfe/zeilenluft", 1.0)) - st["luft"]) < 0.01
                and str(s.get("lesehilfe/groesser", "keine")) == st["groesser"]
                and str(s.get("lesehilfe/zurueck", "keine")) == st["zurueck"]):
            return name
    return ""


def setze(s, name: str) -> None:
    """Schreibt die Werte der Stufe in die Einstellungen (angewendet wird mit ``MainWindow.lesehilfe_anwenden``)."""
    st = STUFEN[name]
    s.set("lesehilfe/stufe", name)
    s.set("lesehilfe/papier", st["papier"]); s.set("lesehilfe/buchstaben", st["buchstaben"]); s.set("lesehilfe/wort", st["wort"]); s.set("lesehilfe/zeilenluft", st["luft"])
    s.set("lesehilfe/groesser", st["groesser"]); s.set("lesehilfe/zurueck", st["zurueck"])
