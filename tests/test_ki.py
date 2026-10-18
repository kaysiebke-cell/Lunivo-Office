import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from native_qt.services import ki as K


def konfig(tmp_path, **kw):
    k = K.KIKonfig(str(tmp_path / "ki.json"))
    k.d.update(kw)
    return k


class Handler(BaseHTTPRequestHandler):
    antwort = {}
    gesehen = []
    status = 200

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        Handler.gesehen.append((self.path, {k.lower(): v for k, v in self.headers.items()}, json.loads(self.rfile.read(n))))
        body = json.dumps(Handler.antwort).encode()
        self.send_response(Handler.status); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        body = json.dumps({"models": [{"name": "b:1"}, {"name": "a:2"}]}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a): pass


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    Handler.gesehen = []; Handler.status = 200
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_schluesseldatei_ist_privat(tmp_path):
    k = konfig(tmp_path); k.setze("apiKey", "geheim")
    assert oct(os.stat(k.pfad).st_mode & 0o777) == "0o600"
    assert K.KIKonfig(k.pfad)["apiKey"] == "geheim"


def test_anweisung_enthaelt_empfaenger_zettel_gedaechtnis(tmp_path):
    k = konfig(tmp_path, empfaenger="Amt", zettel="Es geht um eine Kürzung.")
    a = K.anweisung_korrektur(k, {"woerter": {"vieleicht": "vielleicht"}, "inRuhe": {"meyr": True}})
    assert "Behörde" in a and "Kürzung" in a and "vieleicht statt vielleicht" in a and "meyr" in a


def test_ollama_anfrage(tmp_path, server, monkeypatch):
    monkeypatch.setattr(K, "OLLAMA_URL", server)
    Handler.antwort = {"message": {"content": "<think>grübel</think>Hallo Welt"}}
    ki = K.KI(konfig(tmp_path, modell="ollama:qwen3:8b"))
    r = ki.korrigieren("hallo welt")
    assert r["text"] == "Hallo Welt"
    pfad, _kopf, body = Handler.gesehen[0]
    assert pfad == "/api/chat" and body["model"] == "qwen3:8b" and body["messages"][0]["role"] == "system"
    assert ki.schickt_nach_aussen() is None                      # lokal: nichts verlässt den Rechner


def test_claude_anfrage_schluessel_im_kopf_und_kosten(tmp_path, server, monkeypatch):
    monkeypatch.setattr(K, "CLAUDE_URL", server + "/v1/messages")
    Handler.antwort = {"content": [{"type": "text", "text": "Fertig"}], "model": "claude-sonnet-5",
                       "usage": {"input_tokens": 1000000, "output_tokens": 0}}
    k = konfig(tmp_path, modell="claude-sonnet-5", apiKey="sk-test")
    ki = K.KI(k)
    r = ki.zusammenfassen("langer text")
    assert r["text"] == "Fertig" and abs(r["cent"] - 300) < 1e-6
    assert Handler.gesehen[0][1]["x-api-key"] == "sk-test" and k["kosten"] > 0
    assert ki.schickt_nach_aussen() == "Anthropic (Claude)"


def test_claude_fehler_werden_uebersetzt(tmp_path, server, monkeypatch):
    monkeypatch.setattr(K, "CLAUDE_URL", server + "/v1/messages")
    Handler.status = 401; Handler.antwort = {"error": {"message": "invalid"}}
    r = K.KI(konfig(tmp_path, modell="claude-opus-5", apiKey="x")).korrigieren("a")
    assert "Schlüssel wird abgelehnt" in r["fehler"]
    Handler.status = 400; Handler.antwort = {"error": {"message": "Your credit balance is too low"}}
    assert "Guthaben" in K.KI(konfig(tmp_path, modell="claude-opus-5", apiKey="x")).korrigieren("a")["fehler"]


def test_ohne_schluessel_kein_netzzugriff(tmp_path):
    ki = K.KI(konfig(tmp_path, modell="claude-opus-5", apiKey=""))
    assert not ki.verfuegbar() and "kein Schlüssel" in ki.korrigieren("a")["fehler"]


def test_eigener_anbieter(tmp_path, server):
    k = konfig(tmp_path)
    a = k.anbieter_hinzufuegen("Test", server, "tok", "m1"); k.d["modell"] = "eigen:" + a["id"]
    Handler.antwort = {"choices": [{"message": {"content": "ok"}}]}
    ki = K.KI(k)
    assert ki.zusammenfassen("x")["text"] == "ok"
    assert Handler.gesehen[0][0] == "/chat/completions" and Handler.gesehen[0][1]["authorization"] == "Bearer tok"
    assert ki.schickt_nach_aussen() is None                       # localhost zählt als lokal


def test_vorschlaege_nur_zeichengenaue(tmp_path, server, monkeypatch):
    monkeypatch.setattr(K, "OLLAMA_URL", server)
    text = "Das ist ein sehr umständlich formulierter Satz. Kurz."
    Handler.antwort = {"message": {"content": json.dumps({"vorschlaege": [
        {"alt": "Das ist ein sehr umständlich formulierter Satz.", "neu": "Der Satz ist umständlich.", "grund": "kürzer"},
        {"alt": "Gibt es nicht im Text.", "neu": "x", "grund": "y"}]})}}
    r = K.KI(konfig(tmp_path, modell="ollama:m")).vorschlaege(text)
    assert len(r["vorschlaege"]) == 1


def test_diff_ersetzt_nur_geaendertes():
    alt = "Wir hat keine Zahlung.\nDanke"
    neu = "Wir haben keine Zahlung.\nDanke"
    ops, ganz, n = K.ersetze_ergebnis(alt, neu)
    assert not ganz and n == 1
    text = alt
    for von, bis, t in ops:                                       # von hinten nach vorn
        text = text[:von] + t + text[bis:]
    assert text == neu and len(ops) == 1 and ops[0][2] == "haben"


def test_diff_ungleiche_zeilen_tauscht_ganz():
    assert K.ersetze_ergebnis("a\nb", "a")[1] is True


def test_ollama_modelle(server, monkeypatch, tmp_path):
    monkeypatch.setattr(K, "OLLAMA_URL", server)
    assert K.KI(konfig(tmp_path)).ollama_modelle() == ["a:2", "b:1"]
