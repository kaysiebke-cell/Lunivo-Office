"""Ein von LibreOffice erzeugtes DOCX (nicht von uns geschrieben) lässt sich lesen: Ausrichtung „start“, Fußnote, Kommentar,
nachverfolgte Änderungen, Textmarke, Tabelle."""
import subprocess

import pytest

from lunivo_writer.services import docx_reader
from lunivo_writer.editor import verweise
from lunivo_writer.ui.document.document_editor import DocumentEditor
from lunivo_writer.services.integrations import libreoffice

FODT = """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:dc="http://purl.org/dc/elements/1.1/" office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
<office:body><office:text>
<text:tracked-changes text:track-changes="false">
 <text:changed-region text:id="ct1"><text:insertion><office:change-info><dc:creator>Berta</dc:creator><dc:date>2026-03-04T10:00:00</dc:date></office:change-info></text:insertion></text:changed-region>
 <text:changed-region text:id="ct2"><text:deletion><office:change-info><dc:creator>Carl</dc:creator><dc:date>2026-03-05T11:00:00</dc:date></office:change-info><text:p>alt</text:p></text:deletion></text:changed-region>
</text:tracked-changes>
<text:h text:outline-level="1">Kapitel Eins</text:h>
<text:p>Text mit Fußnote<text:note text:id="ftn1" text:note-class="footnote"><text:note-citation>1</text:note-citation><text:note-body><text:p>Die Fußnote von LibreOffice.</text:p></text:note-body></text:note> und <office:annotation><dc:creator>Ann</dc:creator><dc:date>2026-01-02T03:04:05</dc:date><text:p>Kommentar von LO</text:p></office:annotation>kommentiertem Wort<office:annotation-end/>.</text:p>
<text:p>Vorher <text:change-start text:change-id="ct1"/>eingefügt<text:change-end text:change-id="ct1"/> und <text:change text:change-id="ct2"/> danach <text:bookmark text:name="Marke1"/>Ziel<text:bookmark-end text:name="Marke1"/>.</text:p>
<table:table table:name="T1"><table:table-column table:number-columns-repeated="2"/><table:table-row><table:table-cell><text:p>A1</text:p></table:table-cell><table:table-cell><text:p>B1</text:p></table:table-cell></table:table-row></table:table>
<text:p>Ende</text:p>
</office:text></office:body></office:document>
"""


def test_von_libreoffice_erzeugtes_docx_lesen(app, tmp_path):
    if not libreoffice.verfuegbar():
        pytest.skip("LibreOffice nicht installiert")
    (tmp_path / "t.fodt").write_text(FODT, encoding="utf-8")
    subprocess.run([libreoffice.finde_soffice(), "--headless", "--convert-to", "docx", "--outdir", str(tmp_path), str(tmp_path / "t.fodt")],
                   capture_output=True, timeout=120)
    d, p, meta, rep = docx_reader.read_docx(str(tmp_path / "t.docx"))          # früher: ValueError wegen w:jc="start"
    t = d.toPlainText()
    assert "Kapitel Eins" in t and "Text mit Fußnote1 und kommentiertem Wort." in t and "A1" in t and "Ende" in t
    assert list(meta["noten"]["f"].values()) == ["Die Fußnote von LibreOffice."]
    assert list(meta["kommentare"].values())[0]["text"] == "Kommentar von LO"
    e = DocumentEditor(); e.set_document_and_page(d, p); e.zusatz_binden(meta)
    arten = [(b["wert"], t[b["von"]:b["bis"]], b["cf"].stringProperty(0x100000 + 23)) for b in e.aenderungen()]
    assert arten == [("ins", "eingefügt", "Berta"), ("del", "alt", "Carl")]
    assert [t[b["von"]:b["bis"]] for b in e.kommentar_bereiche()] == ["kommentiertem Wort"]
    assert [m["name"] for m in verweise.lesezeichen_liste(e)] == ["Marke1"]
    assert not rep.warnings
