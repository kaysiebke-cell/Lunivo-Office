from PySide6.QtGui import QTextCursor

from lunivo_writer.proofing import fund, inkrement, pruefung
from lunivo_writer.proofing.proofing_service import WritingAssistant
from lunivo_writer.services.gelernt import Gelernt
from lunivo_writer.services.settings_service import Settings
from lunivo_writer.ui.document.document_editor import DocumentEditor

ABSATZ = "Das ist ein Sazt mit eienm Fehler und noch eine Satz ohne Komma weil es so ist.\n"


def test_verschieben_und_bereich():
    f = [{"von": 0, "bis": 3}, {"von": 10, "bis": 14}, {"von": 20, "bis": 25}]
    r = inkrement.verschieben(f, 8, 4, 6)             # an Position 8 vier Zeichen durch sechs ersetzt
    assert [(x["von"], x["bis"]) for x in r] == [(0, 3), (22, 27)]     # der Fund bei 10–14 liegt im Änderungsbereich → weg
    assert inkrement.schmutz_abbilden(None, 5, 0, 3) == (5, 8)
    assert inkrement.schmutz_abbilden((5, 8), 20, 0, 2) == (5, 22)
    t = "aaa\nbbb\nccc\nddd\neee"
    assert inkrement.pruefbereich(t, 9, 9) == (4, 15)  # Absatz ccc plus je ein Nachbarabsatz
    assert inkrement.pruefbereich(t, 0, 0, 0) == (0, 3)
    assert not inkrement.lohnt(500, 0, 10) and not inkrement.lohnt(5000, 0, 3000) and inkrement.lohnt(5000, 100, 400)


def test_konflikte_nach_konfidenz_art_quelle():
    a = {"von": 0, "bis": 5, "art": "fehler", "neu": "x", "quelle": "eigen", "konfidenz": 0.9, "grund": "a"}
    b = {"von": 3, "bis": 8, "art": "tipp", "neu": "y", "quelle": "languagetool", "konfidenz": 0.7, "grund": "b"}
    c = {"von": 20, "bis": 25, "art": "hinweis", "neu": "", "quelle": "languagetool", "konfidenz": 0.5, "grund": "c"}
    r = fund.loesen([b, a, c])
    assert [x["grund"] for x in r] == ["a", "c"]
    assert r[0]["verdraengt"][0]["quelle"] == "languagetool"
    assert fund.loesen([dict(b, konfidenz=0.95), a])[0]["grund"] == "b"           # höhere Konfidenz schlägt die Quelle
    assert fund.markieren([{"art": "tipp", "wortEbene": False}], "languagetool")[0]["konfidenz"] == 0.5
    assert fund.klemmen("2") == 1.0 and fund.klemmen(None) == 0.5


def test_inkrementell_gleich_ganz(app, tmp_path):
    ed = DocumentEditor()
    ed.setPlainText(ABSATZ * 40)
    a = WritingAssistant(Settings(), Gelernt(str(tmp_path / "g.json")))
    a.attach(ed)
    a.pruefen(voll=True)
    a._pool.waitForDone(); app.processEvents()
    assert a._voll
    # einen Absatz mittendrin ändern
    c = QTextCursor(ed.document()); c.setPosition(len(ABSATZ) * 20 + 4); c.insertText("verkerhrt ")
    assert a._schmutz is not None
    a.pruefen()
    assert a._region is not None                           # nur ein Teilbereich wird geprüft
    a._pool.waitForDone(); app.processEvents()
    text = ed.document().toPlainText()
    ganz = pruefung.finde_probleme(text, a.gelernt.daten)
    schluessel = lambda l: sorted((f["von"], f["bis"], f["alt"], f["neu"]) for f in l)
    assert schluessel(a._roh) == schluessel(ganz)
    assert all("quelle" in f and "konfidenz" in f for f in a._roh)
