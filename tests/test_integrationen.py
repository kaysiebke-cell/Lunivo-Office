import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from native_qt.integrations import languagetool
from native_qt.services import vorlesen


class _LT(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
        body = json.dumps({"matches": [{"offset": 4, "length": 3, "message": "Falsch",
                                        "replacements": [{"value": "bin"}]}]}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a): pass


def test_languagetool_antwort_wird_umgesetzt(monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), _LT)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        funde = languagetool.pruefe("Ich bim da", port=port)       # Fake-Server — echtes LanguageTool ist hier nicht getestet
    finally:
        srv.shutdown()
    assert funde[0]["alt"] == "bim" and funde[0]["neu"] == "bin" and "LanguageTool" in funde[0]["grund"]


def test_languagetool_fehlt_ist_ein_klarer_fehler(monkeypatch, tmp_path):
    monkeypatch.setattr(languagetool, "ordner", lambda: str(tmp_path))
    monkeypatch.setattr(languagetool, "laeuft", lambda port=8081: False)
    with pytest.raises(languagetool.LanguageToolFehler):
        languagetool.starten()


def test_vorlesen_ohne_dienst_meldet_klar(monkeypatch):
    monkeypatch.setattr(vorlesen, "verfuegbar", lambda: False)
    with pytest.raises(vorlesen.VorlesenFehler):
        vorlesen.lies_vor("Hallo")


def test_vorlesen_spd_befehl(monkeypatch):
    gesehen = {}
    monkeypatch.setattr(vorlesen, "verfuegbar", lambda: True)
    monkeypatch.setattr(vorlesen, "piper_da", lambda: False)
    monkeypatch.setattr(vorlesen, "beenden", lambda: None)

    class P:
        def poll(self): return 0
    monkeypatch.setattr(vorlesen.subprocess, "Popen", lambda cmd, **k: gesehen.setdefault("cmd", cmd) and P())
    assert vorlesen.lies_vor("Hallo Welt", "", 20)
    assert gesehen["cmd"][:2] == ["spd-say", "-l"] and "20" in gesehen["cmd"] and gesehen["cmd"][-1] == "Hallo Welt"
    assert vorlesen.lies_vor("   ") is False


def test_wps_nur_ehrlich(monkeypatch):
    from native_qt.integrations import wps
    monkeypatch.setattr(wps.shutil, "which", lambda n: None)
    assert not wps.verfuegbar() and wps.oeffnen("/x.docx") is False
    gesehen = {}
    monkeypatch.setattr(wps.shutil, "which", lambda n: "/usr/bin/wps" if n == "wps" else None)
    monkeypatch.setattr(wps.subprocess, "Popen", lambda cmd, **k: gesehen.setdefault("cmd", cmd))
    assert wps.oeffnen("/x.docx") and gesehen["cmd"] == ["/usr/bin/wps", "/x.docx"]
