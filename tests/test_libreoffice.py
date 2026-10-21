import os

import docx
import pytest

from lunivo_writer.services import file_service as formats
from lunivo_writer.models.page import PageSettings, HeaderFooter
from lunivo_writer.services.integrations import libreoffice

pytestmark = pytest.mark.skipif(not libreoffice.verfuegbar(), reason="LibreOffice nicht installiert")


def _beispiel(tmp_path):
    d = docx.Document()
    d.add_heading("Überschrift", 1)
    p = d.add_paragraph("Normaler Text mit "); r = p.add_run("Fett"); r.bold = True
    d.add_paragraph("Punkt", style="List Bullet")
    t = d.add_table(rows=1, cols=2); t.cell(0, 0).text = "A"; t.cell(0, 1).text = "B"
    f = tmp_path / "q.docx"; d.save(f)
    return str(f)


@pytest.mark.parametrize("ext", [".odt", ".doc", ".rtf"])
def test_roundtrip_ueber_libreoffice(app, tmp_path, ext):
    l = formats.load(_beispiel(tmp_path))
    out = str(tmp_path / ("x" + ext))
    rep = formats.save(out, l.doc, l.page, l.meta)
    assert os.path.getsize(out) > 500 and any("Umwandlungsprogramm" in w for w in rep.warnings)
    back = formats.load(out)
    txt = back.doc.toPlainText()
    assert "Überschrift" in txt and "Normaler Text mit Fett" in txt and "Punkt" in txt
    assert any("Umwandlungsprogramm" in w for w in back.report.warnings)
    # Fett bleibt erhalten
    b = back.doc.find("Fett"); assert b.charFormat().fontWeight() >= 600
    assert back.doc.firstBlock().blockFormat().headingLevel() == 1


def test_kopfzeile_ueberlebt_odt(app, tmp_path):
    l = formats.load(_beispiel(tmp_path))
    page = l.page.copy(); page.footer = HeaderFooter("Seite {PAGE}", "center")
    out = str(tmp_path / "k.odt")
    formats.save(out, l.doc, page, l.meta)
    back = formats.load(out)
    assert "{PAGE}" in back.page.footer.text


def test_kaputte_datei(app, tmp_path):
    from lunivo_writer.models.report import DocumentIOError
    bad = tmp_path / "kaputt.odt"; bad.write_bytes(b"kein odt")
    with pytest.raises(DocumentIOError):
        formats.load(str(bad))
