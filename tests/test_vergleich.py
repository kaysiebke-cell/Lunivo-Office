from PySide6.QtGui import QTextCursor, QTextDocument

from lunivo_writer.editor import vergleich as V
from lunivo_writer.editor.zusatz import P_AENDERUNG, P_AUTOR


def _doc(text):
    d = QTextDocument(); d.setPlainText(text); return d


def _spuren(d):
    """[(art, autor, text)] zusammenhängender verfolgter Stücke."""
    out = []
    b = d.firstBlock()
    while b.isValid():
        it = b.begin()
        while not it.atEnd():
            f = it.fragment()
            cf = f.charFormat()
            if cf.hasProperty(P_AENDERUNG):
                out.append((cf.stringProperty(P_AENDERUNG), cf.stringProperty(P_AUTOR), f.text()))
            it += 1
        b = b.next()
    return out


def _angenommen(d):
    return "\n".join("".join(f.text() for f in _frags(b) if f.charFormat().stringProperty(P_AENDERUNG) != "del") for b in _blocks(d))


def _blocks(d):
    b = d.firstBlock()
    while b.isValid():
        yield b; b = b.next()


def _frags(b):
    it = b.begin()
    while not it.atEnd():
        yield it.fragment(); it += 1


def test_vergleichen_wortweise(app):
    alt = _doc("Das ist ein Satz.\nZweiter Absatz bleibt.")
    neu = _doc("Das war ein guter Satz.\nZweiter Absatz bleibt.")
    erg, st = V.vergleichen(alt, neu, "Prüfer")
    s = _spuren(erg)
    assert ("del", "Prüfer", "ist") in s and ("ins", "Prüfer", "war") in s and ("ins", "Prüfer", "guter ") in s or any("guter" in t for _a, _b, t in s)
    assert _angenommen(erg) == neu.toPlainText()                  # alle Änderungen angenommen = die andere Fassung
    assert alt.toPlainText() == "Das ist ein Satz.\nZweiter Absatz bleibt."   # Ausgang unverändert


def test_vergleichen_absaetze_einfuegen_und_loeschen(app):
    alt = _doc("Eins\nZwei\nDrei")
    neu = _doc("Eins\nDrei\nVier")
    erg, st = V.vergleichen(alt, neu)
    assert _angenommen(erg).split("\n")[0] == "Eins"
    ang = [t for t in _angenommen(erg).split("\n") if t]
    assert ang == ["Eins", "Drei", "Vier"]
    assert any(a == "del" and "Zwei" in t for a, _b, t in _spuren(erg))
    assert any(a == "ins" and "Vier" in t for a, _b, t in _spuren(erg))


def test_gleiche_dokumente_keine_spuren(app):
    erg, st = V.vergleichen(_doc("Gleich\nbleibt"), _doc("Gleich\nbleibt"))
    assert _spuren(erg) == [] and st["operationen"] == 0


def test_zusammenfuehren_zwei_autoren_und_konflikt(app):
    basis = _doc("Der Hund läuft schnell.\nDie Katze schläft.")
    anna = _doc("Der Hund läuft sehr schnell.\nDie Katze schläft.")
    ben = _doc("Der Hund läuft schnell.\nDie Katze schläft tief.")
    erg, st, k = V.zusammenfuehren(basis, [("Anna", anna), ("Ben", ben)])
    autoren = {a for _t, a, _x in _spuren(erg)}
    assert autoren == {"Anna", "Ben"} and k == []
    assert _angenommen(erg) == "Der Hund läuft sehr schnell.\nDie Katze schläft tief."
    # gleiche Stelle, verschiedene Änderungen → Konflikt
    caro = _doc("Der Hund läuft langsam.\nDie Katze schläft.")
    erg2, st2, k2 = V.zusammenfuehren(basis, [("Anna", _doc("Der Hund läuft rasend.\nDie Katze schläft.")), ("Caro", caro)])
    assert len(k2) == 1 and "Anna" in k2[0]
    assert {a for _t, a, _x in _spuren(erg2)} == {"Anna"}


def test_ergebnis_blatt_und_docx_rundreise(app, tmp_path):
    """Das Vergleichsergebnis lässt sich als DOCX speichern; die verfolgten Änderungen (w:ins/w:del) bleiben mit Autor erhalten."""
    import zipfile
    from lunivo_writer.models.page import PageSettings
    from lunivo_writer.services import file_service as formats
    erg, st = V.vergleichen(_doc("Alt und gut."), _doc("Neu und gut."), "Prüferin")
    pfad = str(tmp_path / "v.docx")
    formats.save(pfad, erg, PageSettings())
    x = zipfile.ZipFile(pfad).read("word/document.xml").decode()
    assert "<w:del " in x and "<w:ins " in x and "Prüferin" in x
    neu = formats.load(pfad).doc
    assert {a for _t, a, _x in _spuren(neu)} == {"Prüferin"}
