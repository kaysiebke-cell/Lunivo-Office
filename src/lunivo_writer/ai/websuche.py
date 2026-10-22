"""Websuche für den KI-Chat: Treffer holen und als Quellenliste an die Frage hängen.

Anbieter: SearXNG (eigene oder öffentliche Instanz, JSON-Ausgabe) und Brave Search (API-Schlüssel). Die Frage verlässt den Rechner nur, wenn der Benutzer
die Websuche eingeschaltet hat; bei einer Instanz auf diesem Rechner bleibt sie lokal."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

ANBIETER = [("searxng", "SearXNG (Adresse der Instanz)"), ("brave", "Brave Search (API-Schlüssel)")]
VORGABE = {"an": False, "anbieter": "searxng", "url": "", "schluessel": "", "anzahl": 5}


def suche(einst: dict, frage: str, zeit: float = 15.0) -> list[dict]:
    """[{titel, url, text}] zur Frage; Fehler werden als Ausnahme gemeldet (OSError, ValueError)."""
    n = max(1, min(10, int(einst.get("anzahl", 5))))
    q = urllib.parse.quote(frage[:300])
    if einst.get("anbieter") == "brave":
        if not einst.get("schluessel"):
            raise ValueError("Für Brave Search fehlt der API-Schlüssel.")
        req = urllib.request.Request(f"https://api.search.brave.com/res/v1/web/search?q={q}&count={n}",
                                     headers={"X-Subscription-Token": einst["schluessel"], "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=zeit) as r:
            d = json.loads(r.read().decode("utf-8"))
        return [{"titel": x.get("title", ""), "url": x.get("url", ""), "text": x.get("description", "")} for x in (d.get("web") or {}).get("results", [])[:n]]
    url = (einst.get("url") or "").strip().rstrip("/")
    if not url:
        raise ValueError("Für SearXNG fehlt die Adresse der Instanz.")
    req = urllib.request.Request(f"{url}/search?q={q}&format=json", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=zeit) as r:
        d = json.loads(r.read().decode("utf-8"))
    return [{"titel": x.get("title", ""), "url": x.get("url", ""), "text": x.get("content", "")} for x in d.get("results", [])[:n]]


def als_text(treffer: list[dict]) -> str:
    """Die Treffer als Quellenliste für die Anweisung an die KI."""
    return "\n".join(f"[{i}] {t['titel']} — {t['url']}\n{t['text']}" for i, t in enumerate(treffer, 1))
