from PySide6.QtGui import QTextCursor

from lunivo_writer.editor import abschnitte as AB
from lunivo_writer.models.page import PageSettings
from lunivo_writer.ui.document.document_editor import DocumentEditor


def _ed(text="Eins\nZwei\nDrei"):
    ed = DocumentEditor()
    ed.setPlainText(text)
    return ed


def _cursor_bei(ed, pos):
    c = QTextCursor(ed.document()); c.setPosition(pos); return c


def test_einfuegen_zaehlen_index_entfernen(app):
    ed = _ed()
    doc, basis = ed.document(), PageSettings()
    assert AB.anzahl(doc) == 1
    c = _cursor_bei(ed, 4)                                  # Ende von „Eins“
    assert AB.einfuegen(doc, c, "naechste", basis) == 1
    assert AB.anzahl(doc) == 2
    assert AB.index_bei(doc, 0) == 0 and AB.index_bei(doc, doc.characterCount() - 2) == 1
    c2 = _cursor_bei(ed, doc.characterCount() - 1)
    AB.einfuegen(doc, c2, "fortlaufend", basis)
    assert [t for _n, t, _p in AB.umbrueche(doc)] == ["naechste", "fortlaufend"]
    # Einrichtung ändern: Abschnitt 2 quer
    ps = AB.einrichtung(doc, basis, 1); ps.set_orientation(True)
    assert AB.setzen(doc, 1, ps, "gerade")
    assert AB.einrichtung(doc, basis, 1).landscape and not AB.einrichtung(doc, basis, 0).landscape
    assert AB.umbrueche(doc)[0][1] == "gerade"
    assert AB.beginn(doc, 1) == doc.findBlockByNumber(AB.umbrueche(doc)[0][0] + 1).position()
    assert AB.entfernen(doc, 1) and AB.anzahl(doc) == 2


def test_teilen_im_alten_absatz_behaelt_umbruch(app):
    ed = _ed("Alpha Beta")
    doc, basis = ed.document(), PageSettings()
    AB.einfuegen(doc, _cursor_bei(ed, len("Alpha Beta")), "naechste", basis)
    n_vorher = AB.umbrueche(doc)
    # mitten im Absatz mit Umbruch noch einmal teilen
    AB.einfuegen(doc, _cursor_bei(ed, 5), "fortlaufend", basis)
    typen = [t for _n, t, _p in AB.umbrueche(doc)]
    assert typen == ["fortlaufend", "naechste"] and len(n_vorher) == 1


def test_docx_rundreise_mit_abschnitten(app, tmp_path):
    import docx as D
    from lunivo_writer.models.page import HeaderFooter
    from lunivo_writer.services import file_service as formats
    ed = _ed("Erster Abschnitt\nZweiter Abschnitt\nDritter Abschnitt")
    doc, basis = ed.document(), PageSettings()
    basis.header = HeaderFooter("Kopf eins", "left")
    AB.einfuegen(doc, _cursor_bei(ed, len("Erster Abschnitt")), "naechste", basis)
    p2 = AB.einrichtung(doc, basis, 1); p2.set_orientation(True); p2.margin_left_mm = 40
    p2.header = HeaderFooter("Kopf quer", "right"); p2.kopf_verknuepft = False
    AB.setzen(doc, 1, p2)
    c = _cursor_bei(ed, doc.characterCount() - 1)
    AB.einfuegen(doc, c, "fortlaufend", basis)
    p3 = AB.einrichtung(doc, basis, 2); p3.spalten = 2; p3.kopf_verknuepft = True
    AB.setzen(doc, 2, p3, "fortlaufend")
    pfad = str(tmp_path / "s.docx")
    formats.save(pfad, doc, basis)
    d = D.Document(pfad)
    assert len(d.sections) == 3
    assert d.sections[1].page_width.mm > d.sections[1].page_height.mm            # Abschnitt 2 quer
    assert d.sections[0].page_width.mm < d.sections[0].page_height.mm
    assert d.sections[2].start_type.name == "CONTINUOUS"
    assert d.sections[2].header.is_linked_to_previous
    neu = formats.load(pfad)
    ab = AB.umbrueche(neu.doc)
    assert [t for _n, t, _p in ab] == ["naechste", "fortlaufend"]
    e1, e2 = AB.einrichtung(neu.doc, neu.page, 1), AB.einrichtung(neu.doc, neu.page, 2)
    assert e1.landscape and abs(e1.margin_left_mm - 40) < 0.1 and e1.header.text == "Kopf quer"
    assert e2.spalten == 2 and e2.header.text == "Kopf quer"                      # verknüpft: Kopfzeile vom Vorgänger
    assert not neu.page.landscape and neu.page.header.text == "Kopf eins"


def _dreiteiler(app):
    ed = _ed("Hochformat eins\nQuerformat zwei\nHochformat drei")
    doc, basis = ed.document(), PageSettings()
    AB.einfuegen(doc, _cursor_bei(ed, len("Hochformat eins")), "naechste", basis)
    quer = AB.einrichtung(doc, basis, 1); quer.set_orientation(True)
    AB.setzen(doc, 1, quer)
    AB.einfuegen(doc, _cursor_bei(ed, doc.findBlockByNumber(2).position() + len("Querformat zwei")), "naechste", basis)
    AB.setzen(doc, 2, basis.copy())                         # Abschnitt 3 wieder hoch
    return ed, doc, basis


def test_pdf_hat_je_abschnitt_eigene_seitengroesse(app, tmp_path):
    from pypdf import PdfReader
    from lunivo_writer.editor.pagination import export_pdf
    ed, doc, basis = _dreiteiler(app)
    pfad = str(tmp_path / "a.pdf")
    n = export_pdf(pfad, doc, basis)
    r = PdfReader(pfad)
    assert n == 3 and len(r.pages) == 3
    groessen = [(round(float(p.mediabox.width)), round(float(p.mediabox.height))) for p in r.pages]
    assert groessen[0] == groessen[2] and groessen[1] == (groessen[0][1], groessen[0][0])       # Seite 2 quer
    assert "Querformat zwei" in " ".join(r.pages[1].extract_text().split()) and "Hochformat drei" in " ".join(r.pages[2].extract_text().split())


def test_pdf_seitenzahlen_laufen_durch_und_leerseite(app, tmp_path):
    from pypdf import PdfReader
    from lunivo_writer.editor.pagination import export_pdf
    from lunivo_writer.models.page import HeaderFooter
    ed, doc, basis = _dreiteiler(app)
    basis.footer = HeaderFooter("Seite {PAGE} von {PAGES}", "center")
    ab = AB.umbrueche(doc)
    AB.setzen(doc, 2, (lambda q: (setattr(q, "fuss_verknuepft", True), q)[1])(basis.copy()))
    p2 = AB.einrichtung(doc, basis, 1); p2.fuss_verknuepft = True
    AB.setzen(doc, 1, p2, "ungerade")                      # Abschnitt 2 beginnt auf ungerader Seite: nach Seite 1 → Leerseite 2, Inhalt auf 3
    pfad = str(tmp_path / "b.pdf")
    n = export_pdf(pfad, doc, basis)
    r = PdfReader(pfad)
    texte = [" ".join(p.extract_text().split()) for p in r.pages]
    assert n == len(r.pages) == 4
    assert "Seite 1 von 4" in texte[0] and "Querformat" in texte[2] and "Seite 3 von 4" in texte[2]
    assert "Hochformat" not in texte[1] and "Querformat" not in texte[1]
    assert "Seite 4 von 4" in texte[3]
    assert len(ab) == 2


def test_fortlaufend_gleiche_geometrie_ohne_seitenwechsel(app, tmp_path):
    from pypdf import PdfReader
    from lunivo_writer.editor.pagination import export_pdf
    ed = _ed("Eins\nZwei")
    doc, basis = ed.document(), PageSettings()
    AB.einfuegen(doc, _cursor_bei(ed, 4), "fortlaufend", basis)
    pfad = str(tmp_path / "c.pdf")
    assert export_pdf(pfad, doc, basis) == 1
    t = PdfReader(pfad).pages[0].extract_text()
    assert "Eins" in t and "Zwei" in t


def test_seitenbilder_und_zaehlung(app):
    from lunivo_writer.editor.pagination import seiten_bilder, seitenzahl
    ed, doc, basis = _dreiteiler(app)
    bilder = list(seiten_bilder(doc, basis, None, 0.3))
    assert [n for n, _i, _p in bilder] == [1, 2, 3]
    assert bilder[1][1].width() > bilder[1][1].height() > 0 and bilder[0][1].width() < bilder[0][1].height()
    assert seitenzahl(doc, basis) == 3
    ed.apply_page(basis)
    ed._recount()
    assert ed.page_count == 3                          # Streifen: je Abschnitt eine Seite (Seitenwechsel nach dem Umbruch)


def test_editor_befehle_und_seiteneinrichtung_je_abschnitt(app):
    ed = _ed("Eins\nZwei")
    c = ed.textCursor(); c.setPosition(4); ed.setTextCursor(c)
    assert ed.abschnitt_einfuegen("naechste") == 1
    assert ed.abschnitt_nr() == 1
    pg = ed.abschnitt_seite(); pg.set_orientation(True); pg.spalten = 2
    ed.page_settings_changed(pg)                              # gilt nur für Abschnitt 2
    assert ed.abschnitt_seite().landscape and ed.abschnitt_seite().spalten == 2
    assert not ed.page.landscape and ed.page.spalten == 1
    assert ed.abschnitt_gehe(0) and ed.abschnitt_nr() == 0 and not ed.abschnitt_seite().landscape
    assert ed.abschnitt_entfernen() and AB.anzahl(ed.document()) == 1
    from lunivo_writer.editor import gehe_zu as G
    assert len(G.ziele(ed, "Abschnitt")) == 1


def test_gehe_zu_abschnitt_liste(app):
    from lunivo_writer.editor import gehe_zu as G
    ed, doc, basis = _dreiteiler(app)
    z = G.ziele(ed, "Abschnitt")
    assert [t.split(" (")[0] for t, _p in z] == ["Abschnitt 1", "Abschnitt 2", "Abschnitt 3"]
    assert z[0][1] == 0 and z[1][1] < z[2][1]
