"""Die KI-Ebene: Korrigieren, Vorschläge, Übersetzen, Zusammenfassen, Text bearbeiten, Chat.

Freiwillig und nach außen nur auf ausdrücklichen Knopfdruck:
  · Ollama — läuft auf diesem Rechner (127.0.0.1:11434), der Text verlässt das Gerät nicht.
  · Claude — Anthropic-API, nur mit eigenem Schlüssel und nur nach Ihrer Zustimmung (siehe KIKonfig.claude_erlaubt).
  · Eigener Anbieter — OpenAI-kompatible Schnittstelle unter einer von Ihnen eingetragenen Adresse.
Schlüssel stehen nie im Quelltext, sondern in einer Datei mit Zugriff nur für den Benutzer (0600).
"""
from __future__ import annotations

import json
import os
import re
import difflib
import urllib.error
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
OLLAMA_MARKE, EIGEN_MARKE = "ollama:", "eigen:"
LERN_SCHWELLE = 5
ZETTEL_GRENZE = 300

EMPFAENGER = {
    "egal": "Lass den Tonfall genau so, wie er im Text steht: Förmliches bleibt förmlich, Lockeres bleibt locker. "
            "Ändere die Wortwahl nur da, wo sie falsch ist.",
    "Amt": "Der Text geht an eine Behörde — Amt, Jobcenter, Krankenkasse, Versicherung, Gericht. Halte den Tonfall "
           "durchgehend förmlich und höflich: Siezen, vollständige Sätze, keine Umgangssprache, keine Abkürzungen "
           "mitten im Satz. Sachlich bleiben auch dort, wo der Text ärgerlich klingt — der Vorwurf darf inhaltlich "
           "stehen bleiben, aber im ruhigen Ton. Stehen Anrede, Betreff oder ein Aktenzeichen schon da, bring sie in "
           "die übliche Form; fehlen sie, erfinde sie nicht.",
    "Arbeit": "Der Text geht an jemanden aus dem Beruf — Chefin, Kollege, Kundschaft. Höflich und knapp: keine "
              "Ausschmückung, keine Floskelketten, aber auch nicht schroff. Ob geduzt oder gesiezt wird, entscheidet "
              "der Text — dreh das nicht um.",
    "Freunde": "Der Text geht an jemanden, den man kennt — Familie, Freundin, Nachbar. Duzen, freundlich und "
               "zugewandt, kurze Sätze, ruhig so, wie man redet. Nicht flapsig und nicht anbiedernd. Emojis, "
               "Ausrufezeichen und Anreden wie „Hey“ bleiben stehen.",
    "Forum": "Der Text wird öffentlich gelesen — Forum, Kommentar, Bewertung, soziales Netz. Er muss auch für Fremde "
             "verständlich sein, die die Vorgeschichte nicht kennen: klare Sätze, Absätze statt eines Blocks. Geduzt "
             "wird, wie es dort üblich ist. Nicht belehrend — eine deutliche Meinung darf deutlich bleiben, aber ohne "
             "Beleidigung.",
    "Bewerbung": "Der Text ist eine Bewerbung oder gehört dazu. Siezen, förmlich, aber nicht steif. Selbstbewusst "
                 "ohne Angeberei: klare Aussagesätze statt „ich würde gerne“ und statt Floskelketten. Erfinde keine "
                 "Fähigkeiten, keine Stationen und keine Zahlen dazu.",
}
SPRACHEN = ["Englisch", "Deutsch", "Türkisch", "Russisch", "Ukrainisch", "Polnisch", "Rumänisch", "Arabisch",
            "Französisch", "Spanisch", "Italienisch", "Griechisch", "Niederländisch", "Portugiesisch"]
MODELLE_FEST = [("claude-opus-5", "Beste Qualität · Opus 5"), ("claude-sonnet-5", "Mittelweg · Sonnet 5"),
                ("claude-haiku-4-5", "Günstig & schnell · Haiku 4.5")]
PREISE = {"claude-opus-5": (5, 25), "claude-sonnet-5": (3, 15), "claude-haiku-4-5": (1, 5)}   # Dollar je Million Token
TEXT_AKTIONEN = [("verbessern", "Verbessern"), ("umformulieren", "Umformulieren"), ("kuerzen", "Kürzen"),
                 ("erweitern", "Erweitern"), ("professioneller", "Professioneller formulieren"),
                 ("einfacher", "Einfacher formulieren"), ("ton-freundlich", "Tonalität: Freundlich"),
                 ("ton-foermlich", "Tonalität: Förmlich"), ("ton-sachlich", "Tonalität: Sachlich"),
                 ("ton-locker", "Tonalität: Locker"), ("ton-bestimmt", "Tonalität: Bestimmt")]
_AKTION_SATZ = {
    "verbessern": "Verbessere den folgenden Text — klarer und natürlicher, ohne den Sinn zu ändern.",
    "umformulieren": "Formuliere den folgenden Text um — derselbe Sinn, andere Worte und Sätze.",
    "kuerzen": "Kürze den folgenden Text deutlich — nur das Wichtigste bleibt.",
    "erweitern": "Erweitere den folgenden Text um sinnvolle Einzelheiten, ohne abzuschweifen.",
    "professioneller": "Formuliere den folgenden Text professioneller und sachlicher.",
    "einfacher": "Formuliere den folgenden Text einfacher — kurze Sätze, geläufige Wörter.",
    "ton-freundlich": "Ändere die Tonalität des folgenden Textes zu freundlich und zugewandt.",
    "ton-foermlich": "Ändere die Tonalität des folgenden Textes zu förmlich.",
    "ton-sachlich": "Ändere die Tonalität des folgenden Textes zu sachlich und neutral.",
    "ton-locker": "Ändere die Tonalität des folgenden Textes zu locker und ungezwungen.",
    "ton-bestimmt": "Ändere die Tonalität des folgenden Textes zu bestimmt und klar.",
}
ANBIETER_TAGS = [("text", "Text"), ("bilder", "Bilder"), ("einbettungen", "Einbettungen"), ("audio", "Audioverarbeitung"),
                 ("moderation", "Inhaltsmoderation"), ("echtzeit", "Echtzeitaufgaben"),
                 ("programmieren", "Hilfe zum Programmieren"), ("visuell", "Visuelle Analyse")]
# Erweiterte Einstellungen des Chats: maxLaenge 0 = Vorgabe des Anbieters; temperatur/topP gelten für Ollama und eigene Anbieter
CHAT_VORGABE = {"maxLaenge": 0, "temperatur": 0.2, "topP": 1.0, "stopp": "", "direkt": False}
AUFGABEN = [("chatbot", "Chatbot"), ("zusammenfassen", "Zusammenfassen"), ("uebersetzung", "Übersetzung"),
            ("textanalyse", "Textanalyse"), ("bildgenerierung", "Bildgenerierung")]
# Bekannte Anbieter mit der Adresse, die sie selbst angeben (Claude fehlt bewusst: kein OpenAI-kompatibles /chat/completions)
ANBIETER_VORLAGEN = [("andere", "Andere", ""), ("ollama", "Ollama (auf diesem Rechner)", "http://localhost:11434/v1"),
                     ("openai", "OpenAI", "https://api.openai.com/v1"), ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1"),
                     ("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
                     ("mistral", "Mistral", "https://api.mistral.ai/v1"), ("groq", "Groq", "https://api.groq.com/openai/v1"),
                     ("deepseek", "DeepSeek", "https://api.deepseek.com/v1"), ("together", "Together AI", "https://api.together.xyz/v1")]
VORSCHLAG_BAUPLAN = {"type": "object", "properties": {"vorschlaege": {"type": "array", "items": {
    "type": "object", "properties": {"alt": {"type": "string"}, "neu": {"type": "string"}, "grund": {"type": "string"},
                                                                        "konfidenz": {"type": "number"}},
    "required": ["alt", "neu", "grund", "konfidenz"], "additionalProperties": False}}},
    "required": ["vorschlaege"], "additionalProperties": False}


# ---------------------------------------------------------------- Konfiguration (mit Schlüsseln, 0600)
class KIKonfig:
    def __init__(self, pfad: str):
        self.pfad = pfad
        self.d = {"modell": "claude-opus-5", "sprache": "Englisch", "empfaenger": "egal", "zettel": "",
                  "apiKey": "", "anbieter": [], "aufgaben": {}, "kosten": 0.0, "claude_erlaubt": False, "assistenten": [], "chat": {}, "mcp": [], "websuche": {}}
        try:
            with open(pfad, encoding="utf-8") as fh:
                self.d.update(json.load(fh))
        except (OSError, ValueError):
            pass

    def speichern(self) -> None:
        tmp = self.pfad + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self.d, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, self.pfad)
        os.chmod(self.pfad, 0o600)

    def __getitem__(self, k): return self.d[k]

    def setze(self, k, v) -> None:
        self.d[k] = v
        self.speichern()

    def anbieter_holen(self, id_: str):
        return next((a for a in self.d["anbieter"] if a["id"] == id_), None)

    def anbieter_hinzufuegen(self, name, url, schluessel, modell, verwendung=None) -> dict:
        import uuid
        e = {"id": "p" + uuid.uuid4().hex[:8]}
        self.d["anbieter"].append(e)
        return self.anbieter_aktualisieren(e["id"], name, url, schluessel, modell, verwendung)

    def anbieter_aktualisieren(self, id_, name, url, schluessel, modell, verwendung=None) -> dict | None:
        e = self.anbieter_holen(id_)
        if e is None:
            return None
        gueltig = {k for k, _ in ANBIETER_TAGS}
        e.update(name=(name or "").strip()[:60] or "Eigenes Modell", url=(url or "").strip().rstrip("/"),
                 schluessel=(schluessel or "").strip(), modell=(modell or "").strip(),
                 verwendungFuer=[t for t in (verwendung if verwendung is not None else e.get("verwendungFuer", ["text"])) if t in gueltig])
        self.speichern()
        return e

    def chat_optionen(self) -> dict:
        """Die erweiterten Einstellungen des KI-Chats (Länge, Temperatur, Top P, Stoppfolgen, Antwort direkt einfügen) mit ihren Vorgaben."""
        return {**CHAT_VORGABE, **(self.d.get("chat") or {})}

    def websuche_optionen(self) -> dict:
        from lunivo_writer.ai import websuche as W
        return {**W.VORGABE, **(self.d.get("websuche") or {})}

    def websuche_setzen(self, **teile) -> None:
        self.d["websuche"] = {**(self.d.get("websuche") or {}), **teile}
        self.speichern()

    def mcp_speichern(self, id_: str | None, name: str, befehl: str, an: bool = True) -> dict:
        """MCP-Server anlegen (``id_`` None) oder ändern."""
        import uuid
        e = next((m for m in self.d["mcp"] if m["id"] == id_), None) if id_ else None
        if e is None:
            e = {"id": "m" + uuid.uuid4().hex[:8]}
            self.d["mcp"].append(e)
        e.update(name=(name or "").strip()[:60] or "MCP-Server", befehl=(befehl or "").strip(), an=bool(an))
        self.speichern()
        return e

    def mcp_entfernen(self, id_: str) -> None:
        self.d["mcp"] = [m for m in self.d["mcp"] if m["id"] != id_]
        self.speichern()

    def chat_setzen(self, **teile) -> None:
        self.d["chat"] = {**(self.d.get("chat") or {}), **teile}
        self.speichern()

    def aufgabe_setzen(self, aufgabe: str, modell: str) -> None:
        if modell:
            self.d["aufgaben"][aufgabe] = modell
        else:
            self.d["aufgaben"].pop(aufgabe, None)
        self.speichern()

    def assistent_hinzufuegen(self, name: str, prompt: str, modus: str, zugriff: str = "kontext") -> dict:
        """Eine „Schnelle KI-Aktion“: ``modus`` = ersetzen | anhaengen | hinweis; ``zugriff`` = kontext (Rechtsklick-Menü) | schnell (Schnellzugriffsleiste)."""
        import uuid
        e = {"id": "a" + uuid.uuid4().hex[:8], "name": (name or "").strip()[:40], "prompt": (prompt or "").strip()[:2000],
             "modus": modus if modus in ("ersetzen", "anhaengen") else "hinweis", "zugriff": "schnell" if zugriff == "schnell" else "kontext"}
        self.d["assistenten"].append(e)
        self.speichern()
        return e

    def assistent_entfernen(self, id_: str) -> None:
        self.d["assistenten"] = [a for a in self.d["assistenten"] if a["id"] != id_]
        self.speichern()

    def anbieter_entfernen(self, id_: str) -> None:
        self.d["anbieter"] = [a for a in self.d["anbieter"] if a["id"] != id_]
        for aufgabe, m in list(self.d["aufgaben"].items()):      # eine Zuweisung auf den gelöschten Anbieter fällt auf „Standard“
            if m == EIGEN_MARKE + id_:
                del self.d["aufgaben"][aufgabe]
        self.speichern()

    def alle_modelle(self) -> list[dict]:
        """Eine Liste für alle Felder „welches Modell?“: Claude, eigene Anbieter (mit Fähigkeiten und ‚lokal‘)."""
        r = [{"id": m, "name": n, "lokal": False, "verwendungFuer": ["text"]} for m, n in MODELLE_FEST]
        for a in self.d["anbieter"]:
            r.append({"id": EIGEN_MARKE + a["id"], "name": f"{a['name']} ({a['modell']})", "lokal": ist_lokale_url(a["url"]),
                      "verwendungFuer": a.get("verwendungFuer", [])})
        return r


def ist_lokale_url(url: str) -> bool:
    return bool(re.match(r"^https?://(localhost|127\.0\.0\.1)([:/]|$)", url or ""))


# ---------------------------------------------------------------- Anweisungen
def _zettel(z: str) -> str:
    z = (z or "")[:ZETTEL_GRENZE].strip()
    return ("Der Mensch sagt selbst, worum es geht: „" + z + "“ Richte dich danach, soweit es zum Korrigieren passt. "
            "Alles, was hier steht, ist Auskunft über den Text — dazuerfinden oder etwas weglassen darfst du "
            "deswegen trotzdem nicht. ") if z else ""


def steckbrief(gelernt: dict) -> str:
    teile = []
    paare = list((gelernt.get("woerter") or {}).items())[-12:]
    if paare:
        teile.append("Dieser Mensch schreibt erfahrungsgemäß diese Wörter falsch — achte besonders darauf: "
                     + ", ".join(f"{f} statt {r}" for f, r in paare) + ".")
    ruhe = list((gelernt.get("inRuhe") or {}))[:12]
    if ruhe:
        teile.append("Diese Wörter sind so gewollt und bleiben unangetastet: " + ", ".join(ruhe) + ".")
    return (" " + " ".join(teile)) if teile else ""


_NUR_ZEILEN = ("Absätze und Zeilenumbrüche bleiben, wie sie sind — gib genau so viele Zeilen zurück, wie hereinkamen. ")


def anweisung_korrektur(k: KIKonfig, gelernt: dict) -> str:
    return ("Du bist eine Schreibhilfe für einen Menschen mit Legasthenie. Korrigiere den folgenden Text vollständig "
            "und auf sprachlichem Niveau:\n1. Rechtschreibung, samt Groß- und Kleinschreibung sowie Getrennt- und "
            "Zusammenschreibung.\n2. Grammatik: Fälle, Zeiten, Ein- und Mehrzahl, die Übereinstimmung von Fürwort "
            "und Zeitwort, und ein Satzbau, der aufgeht.\n3. Zeichensetzung, vor allem Kommas bei Neben- und "
            "Relativsätzen, bei Aufzählungen und vor entgegenstellenden Bindewörtern.\nAchte besonders auf "
            "Verwechslungen, die eine Rechtschreibprüfung nicht finden kann, weil beide Wörter existieren: "
            "das/dass, seit/seid, wider/wieder, wie/als, Ihnen/ihnen, End-/Ent-. Entscheide nach dem Sinn des "
            "Satzes. Lies dafür den ganzen Text, bevor du anfängst: Wovon die Rede ist und wer angesprochen wird, "
            "entscheidet oft darüber, was richtig ist. " + EMPFAENGER.get(k["empfaenger"], EMPFAENGER["egal"]) + " "
            + _zettel(k["zettel"]) + steckbrief(gelernt) + " Ändere nichts am Inhalt, erfinde nichts dazu und lasse "
            "nichts weg. " + _NUR_ZEILEN + "Der Text kann in jeder Sprache stehen; antworte in der Sprache des "
            "Textes. Antworte ausschließlich mit dem korrigierten Text: keine Erklärung, keine Anführungszeichen, "
            "keine Vorrede.")


def anweisung_uebersetzung(sprache: str) -> str:
    return (f"Übersetze den folgenden Text nach {sprache}. Behalte Tonfall und Anrede bei: Ein Brief bleibt ein Brief, "
            "eine Nachricht an einen Freund bleibt locker. Übersetze sinngemäß und natürlich, nicht Wort für Wort. "
            f"Ist der Text schon auf {sprache}, gib ihn unverändert zurück. " + _NUR_ZEILEN +
            "Antworte ausschließlich mit der Übersetzung: keine Erklärung, keine Anführungszeichen, keine Vorrede.")


def anweisung_vorschlaege(k: KIKonfig) -> str:
    return ("Du bist eine Schreibhilfe für einen Menschen mit Legasthenie. Suche im folgenden Text die Sätze, die "
            "schwer zu lesen oder umständlich sind, und schlage für jeden eine klarere Fassung vor. Regeln: Ändere "
            "nichts am Inhalt und erfinde nichts dazu. " + EMPFAENGER.get(k["empfaenger"], EMPFAENGER["egal"]) + " "
            + _zettel(k["zettel"]) + "Benutze einfache, gebräuchliche Wörter und kurze Sätze. Der Text kann in jeder "
            "Sprache stehen. \"neu\" bleibt in der Sprache des Textes, \"grund\" schreibst du immer auf Deutsch. Nimm "
            "höchstens sechs Sätze, nur die, bei denen es wirklich hilft; ist der Text schon gut, nimm weniger oder "
            "keinen. \"alt\" ist der Satz zeichengenau aus dem Text — nicht kürzen, nicht glätten, nichts "
            "hinzufügen; er muss sich Zeichen für Zeichen im Text wiederfinden. \"konfidenz\" ist eine Zahl von 0 bis 1: wie sicher du bist, dass die neue Fassung besser ist und nichts am Inhalt ändert. \"neu\" ist die klarere Fassung, "
            "\"grund\" sagt in höchstens acht Wörtern, warum das leichter ist. Gibt es nichts zu verbessern, bleibt "
            "die Liste leer.")


ANWEISUNG_ZUSAMMENFASSUNG = (
    "Fasse den folgenden Text in eigenen Worten zusammen. Nenne nur die wichtigsten Aussagen, keine "
    "Nebensächlichkeiten. Halte dich an das, was im Text steht — erfinde nichts dazu und lass keine wichtige "
    "Aussage weg. Schreibe in ganzen Sätzen, nicht als Stichpunkte, so kurz wie möglich, aber verständlich für sich "
    "allein — auch für jemanden, der den Text selbst nicht gelesen hat. Der Text kann in jeder Sprache stehen; "
    "antworte in der Sprache des Textes. Antworte ausschließlich mit der Zusammenfassung: keine Erklärung, keine "
    "Anführungszeichen, keine Vorrede, keine Überschrift wie „Zusammenfassung:“.")
ANWEISUNG_ANALYSE = ("Analysiere diesen Text kurz: wie viele Wörter, welcher Tonfall, wie leicht lesbar für einen "
                     "Menschen mit Legasthenie, und was sich verbessern ließe. In wenigen, einfachen Sätzen. "
                     "Antworte in der Sprache des Textes.")


def anweisung_text_aktion(k: KIKonfig, aktion: str) -> str:
    return (_AKTION_SATZ.get(aktion, _AKTION_SATZ["verbessern"]) + " " + EMPFAENGER.get(k["empfaenger"], EMPFAENGER["egal"])
            + " " + _zettel(k["zettel"]) + "Ändere nichts am Sinn, erfinde nichts hinzu, was nicht sinngemäß schon "
            "dastand. " + _NUR_ZEILEN + "Der Text kann in jeder Sprache stehen; antworte in der Sprache des Textes. "
            "Antworte ausschließlich mit dem neuen Text: keine Erklärung, keine Anführungszeichen, keine Vorrede.")


# ---------------------------------------------------------------- Anfragen
def _nachrichten(text) -> list[dict]:
    if isinstance(text, list):
        return [{"role": "assistant" if z.get("rolle") == "ki" else "user", "content": z["text"]} for z in text]
    return [{"role": "user", "content": text}]


def ohne_gruebeln(roh: str) -> str:
    ohne = re.sub(r"<think>[\s\S]*?</think>", "", str(roh), flags=re.I)
    return ohne[ohne.rfind("</think>") + 8:] if "</think>" in ohne else ohne


def cent_fuer(modell: str, verbrauch: dict | None):
    if not verbrauch:
        return None
    name = next((k for k in PREISE if str(modell or "").startswith(k)), None)
    if not name:
        return None
    hin = (verbrauch.get("input_tokens", 0) + verbrauch.get("cache_read_input_tokens", 0)
           + verbrauch.get("cache_creation_input_tokens", 0))
    her = verbrauch.get("output_tokens", 0)
    p = PREISE[name]
    return (hin * p[0] + her * p[1]) / 1e6 * 100


def als_geld(cent) -> str:
    if cent is None:
        return ""
    return "unter 1 Cent" if cent < 1 else f"{cent / 100:.2f} $".replace(".", ",")


def _post(url: str, kopf: dict, body: dict, timeout: float):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"content-type": "application/json", **kopf}, method="POST")
    return urllib.request.urlopen(req, timeout=timeout)


class KI:
    def __init__(self, konfig: KIKonfig, gelernt: dict | None = None):
        self.k = konfig
        self.gelernt = gelernt if gelernt is not None else {"woerter": {}, "inRuhe": {}}

    def modell(self, aufgabe: str | None = None) -> str:
        return (self.k["aufgaben"].get(aufgabe) if aufgabe else None) or self.k["modell"]

    def verfuegbar(self) -> bool:
        m = self.k["modell"]
        if m.startswith(EIGEN_MARKE):
            return self.k.anbieter_holen(m[len(EIGEN_MARKE):]) is not None
        return m.startswith(OLLAMA_MARKE) or bool(self.k["apiKey"])

    def schickt_nach_aussen(self, modell: str | None = None) -> str | None:
        """Name des Empfängers, wenn der Text das Gerät verlässt — sonst None."""
        m = modell or self.k["modell"]
        if m.startswith(OLLAMA_MARKE):
            return None
        if m.startswith(EIGEN_MARKE):
            a = self.k.anbieter_holen(m[len(EIGEN_MARKE):])
            return None if (a and ist_lokale_url(a["url"])) else (a["name"] if a else "einen eigenen Anbieter")
        return "Anthropic (Claude)"

    def anfrage(self, anweisung: str, text, bauplan=None, modell: str | None = None, optionen: dict | None = None) -> dict:
        m = modell or self.k["modell"]
        if m.startswith(EIGEN_MARKE):
            return self._eigen(self.k.anbieter_holen(m[len(EIGEN_MARKE):]), anweisung, text, bauplan, optionen)
        if m.startswith(OLLAMA_MARKE):
            return self._ollama(anweisung, text, bauplan, m[len(OLLAMA_MARKE):], optionen)
        return self._claude(anweisung, text, bauplan, m, optionen)

    @staticmethod
    def _stopp(optionen) -> list[str]:
        return [t.strip() for t in str((optionen or {}).get("stopp", "")).split(",") if t.strip()]

    def _claude(self, anweisung, text, bauplan, modell, optionen=None) -> dict:
        if not self.k["apiKey"]:
            return {"fehler": "Es ist kein Schlüssel gespeichert. Optionen ▸ Schreibhilfe und KI."}
        bitte = {"model": modell, "max_tokens": int((optionen or {}).get("maxLaenge") or 16000), "system": anweisung, "messages": _nachrichten(text)}
        if self._stopp(optionen):
            bitte["stop_sequences"] = self._stopp(optionen)                  # Temperatur und Top P gelten hier nicht (Claude regelt das selbst)
        ausgabe = {}
        if modell != "claude-haiku-4-5":
            ausgabe["effort"] = "low"
            bitte["thinking"] = {"type": "adaptive"}
        if bauplan:
            ausgabe["format"] = {"type": "json_schema", "schema": bauplan}
        if ausgabe:
            bitte["output_config"] = ausgabe
        try:
            with _post(CLAUDE_URL, {"x-api-key": self.k["apiKey"], "anthropic-version": "2023-06-01"}, bitte, 90) as r:
                daten = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            zusatz = ""
            try:
                zusatz = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
            except (ValueError, OSError):
                pass
            if re.search(r"credit balance", zusatz, re.I):
                return {"fehler": "Das Guthaben ist aufgebraucht. Bitte bei Anthropic aufladen."}
            texte = {401: "Der Schlüssel wird abgelehnt. Er wird bei der Erstellung nur einmal angezeigt — "
                          "vollständig kopiert? Sonst auf console.anthropic.com einen neuen anlegen.",
                     400: "Die Anfrage wurde abgelehnt.", 429: "Zu viele Anfragen. Bitte kurz warten und noch "
                     "einmal versuchen."}
            return {"fehler": texte.get(e.code, f"Fehler {e.code}") + (f" ({zusatz})" if zusatz else "")}
        except TimeoutError:
            return {"fehler": "Die KI hat zu lange gebraucht. Bitte noch einmal versuchen."}
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {"fehler": f"Es hat nicht geklappt: {getattr(e, 'reason', e)}"}
        if daten.get("stop_reason") == "refusal":
            return {"fehler": "Die KI wollte diesen Text nicht bearbeiten."}
        erg = "".join(b.get("text", "") for b in daten.get("content", []) if b.get("type") == "text").strip()
        if not erg:
            return {"fehler": "Es kam keine Antwort zurück."}
        return {"ergebnis": erg, "cent": cent_fuer(daten.get("model") or modell, daten.get("usage"))}

    def _ollama(self, anweisung, text, bauplan, modell, optionen=None) -> dict:
        if not modell:
            return {"fehler": "Es ist noch kein Modell gewählt. In den Optionen nachholen."}
        o = optionen or {}
        opt = {"temperature": float(o.get("temperatur", 0.2))}
        if o.get("topP") is not None:
            opt["top_p"] = float(o["topP"])
        if o.get("maxLaenge"):
            opt["num_predict"] = int(o["maxLaenge"])
        if self._stopp(o):
            opt["stop"] = self._stopp(o)
        bitte = {"model": modell, "stream": False, "options": opt, "think": False,
                 "messages": [{"role": "system", "content": anweisung}] + _nachrichten(text)}
        if bauplan:
            bitte["format"] = bauplan
        for _versuch in (1, 2):
            try:
                with _post(OLLAMA_URL + "/api/chat", {}, bitte, 600) as r:
                    daten = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                grund = ""
                try:
                    grund = e.read().decode("utf-8", "replace")
                except OSError:
                    pass
                if e.code == 400 and "think" in grund.lower() and "think" in bitte:
                    del bitte["think"]
                    continue
                if e.code == 404:
                    return {"fehler": f"Das Modell „{modell}“ liegt nicht auf diesem Rechner. Im Terminal holen: "
                                      f"ollama pull {modell}"}
                return {"fehler": f"Ollama meldet Fehler {e.code}" + (f" ({grund[:200]})" if grund else "")}
            except TimeoutError:
                return {"fehler": "Der eigene Rechner hat zu lange gebraucht. Ein kleineres Modell geht schneller."}
            except (urllib.error.URLError, OSError, ValueError):
                return {"fehler": f"Ollama ist unter {OLLAMA_URL} nicht zu erreichen. Läuft der Dienst?"}
        erg = ohne_gruebeln((daten.get("message") or {}).get("content", "")).strip()
        return {"ergebnis": erg} if erg else {"fehler": "Es kam keine Antwort zurück."}

    def _eigen(self, a, anweisung, text, bauplan, optionen=None) -> dict:
        if not a:
            return {"fehler": "Der gewählte Anbieter ist nicht mehr da. In den Optionen neu wählen oder anlegen."}
        if not a["modell"]:
            return {"fehler": f"Für „{a['name']}“ ist kein Modell eingetragen."}
        bitte = {"model": a["modell"], "messages": [{"role": "system", "content": anweisung}] + _nachrichten(text)}
        if optionen:
            if optionen.get("temperatur") is not None:
                bitte["temperature"] = float(optionen["temperatur"])
            if optionen.get("topP") is not None:
                bitte["top_p"] = float(optionen["topP"])
            if optionen.get("maxLaenge"):
                bitte["max_tokens"] = int(optionen["maxLaenge"])
            if self._stopp(optionen):
                bitte["stop"] = self._stopp(optionen)
        if bauplan:
            bitte["response_format"] = {"type": "json_schema", "json_schema": {"name": "antwort", "schema": bauplan,
                                                                              "strict": True}}
        kopf = {"authorization": "Bearer " + a["schluessel"]} if a["schluessel"] else {}
        try:
            with _post(a["url"] + "/chat/completions", kopf, bitte, 90) as r:
                daten = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"fehler": f"„{a['name']}“ meldet Fehler {e.code}"}
        except TimeoutError:
            return {"fehler": f"„{a['name']}“ hat zu lange gebraucht. Bitte noch einmal versuchen."}
        except (urllib.error.URLError, OSError, ValueError):
            return {"fehler": f"„{a['name']}“ ist unter {a['url']} nicht zu erreichen. Stimmt die URL?"}
        erg = ((daten.get("choices") or [{}])[0].get("message") or {}).get("content")
        return {"ergebnis": erg} if erg else {"fehler": "Es kam keine Antwort zurück."}

    # ---- die Anwendungen
    def _text(self, anweisung, text, aufgabe=None, optionen: dict | None = None) -> dict:
        r = self.anfrage(anweisung, text, None, self.modell(aufgabe), optionen)
        if "fehler" in r:
            return r
        self._kosten(r.get("cent"))
        return {"text": r["ergebnis"], "cent": r.get("cent")}

    def _kosten(self, cent) -> None:
        if cent:
            self.k.setze("kosten", self.k["kosten"] + cent)

    def korrigieren(self, text): return self._text(anweisung_korrektur(self.k, self.gelernt), text)
    def uebersetzen(self, text, sprache): return self._text(anweisung_uebersetzung(sprache), text, "uebersetzung")
    def zusammenfassen(self, text): return self._text(ANWEISUNG_ZUSAMMENFASSUNG, text, "zusammenfassen")
    def text_analyse(self, text): return self._text(ANWEISUNG_ANALYSE, text, "textanalyse")
    def eigener_assistent(self, text, prompt):
        return self._text(prompt, text)

    def text_aktion(self, text, aktion): return self._text(anweisung_text_aktion(self.k, aktion), text)

    werkzeug_frage = staticmethod(lambda name, argumente, server: False)      # vom KI-Dienst ersetzt: fragt den Benutzer vor jedem Werkzeugaufruf

    def chat(self, verlauf: list[dict], dokumenttext: str = "") -> dict:
        system = ("Du bist ein Schreibassistent in einem Textverarbeitungsprogramm und antwortest kurz und klar auf Deutsch. "
                  "Erfinde nichts dazu. " + EMPFAENGER.get(self.k["empfaenger"], EMPFAENGER["egal"]))
        if dokumenttext.strip():
            system += "\n\nDer Mensch arbeitet gerade an diesem Text:\n" + dokumenttext[:12000]
        notiz = ""
        ws = self.k.websuche_optionen()
        if ws["an"] and verlauf:
            from lunivo_writer.ai import websuche as W
            try:
                treffer = W.suche(ws, verlauf[-1]["text"])
                if treffer:
                    system += ("\n\nErgebnisse einer Websuche zur Frage (nenne die Nummer der Quelle, wenn du sie benutzt):\n" + W.als_text(treffer))
            except (OSError, ValueError) as e:
                notiz = f"(Die Websuche hat nicht geklappt: {getattr(e, 'reason', e)})\n\n"
        server = [m for m in self.k["mcp"] if m.get("an") and m.get("befehl")]
        modell = self.modell("chatbot")
        if server and (modell.startswith(EIGEN_MARKE) or modell.startswith(OLLAMA_MARKE)):
            r = self._chat_werkzeuge(system, verlauf, server, modell, self.k.chat_optionen())
        else:
            r = self._text(system, verlauf, "chatbot", self.k.chat_optionen())
        if notiz and "text" in r:
            r["text"] = notiz + r["text"]
        return r

    def _chat_werkzeuge(self, system: str, verlauf: list[dict], server: list[dict], modell: str, optionen: dict) -> dict:
        """Chat mit MCP-Werkzeugen über die OpenAI-kompatible Schnittstelle (Ollama und eigene Anbieter): das Modell darf Werkzeuge verlangen; jeder
        Aufruf wird erst nach Rückfrage beim Benutzer ausgeführt."""
        from lunivo_writer.ai import mcp as M
        if modell.startswith(EIGEN_MARKE):
            a = self.k.anbieter_holen(modell[len(EIGEN_MARKE):])
            if not a:
                return {"fehler": "Der gewählte Anbieter ist nicht mehr da."}
            url, name, kopf = a["url"] + "/chat/completions", a["modell"], ({"authorization": "Bearer " + a["schluessel"]} if a["schluessel"] else {})
        else:
            url, name, kopf = OLLAMA_URL + "/v1/chat/completions", modell[len(OLLAMA_MARKE):], {}
        clients, tools, wo = [], [], {}
        try:
            for sv in server:
                try:
                    c = M.McpClient(sv["befehl"])
                except M.McpFehler as e:
                    return {"fehler": f"MCP-Server „{sv['name']}“: {e}"}
                clients.append(c)
                for t in c.werkzeuge():
                    n = t["name"] if t["name"] not in wo else f"{sv['name']}_{t['name']}"
                    wo[n] = (c, t["name"], sv["name"])
                    tools.append({"type": "function", "function": {"name": n, "description": t.get("description", ""), "parameters": t.get("inputSchema") or {"type": "object", "properties": {}}}})
            nachrichten = [{"role": "system", "content": system}] + _nachrichten(verlauf)
            for _runde in range(6):
                bitte = {"model": name, "messages": nachrichten, "tools": tools, "temperature": float(optionen.get("temperatur", 0.2))}
                if optionen.get("topP") is not None:
                    bitte["top_p"] = float(optionen["topP"])
                if optionen.get("maxLaenge"):
                    bitte["max_tokens"] = int(optionen["maxLaenge"])
                with _post(url, kopf, bitte, 300) as r:
                    daten = json.loads(r.read().decode("utf-8"))
                msg = ((daten.get("choices") or [{}])[0].get("message")) or {}
                aufrufe = msg.get("tool_calls") or []
                if not aufrufe:
                    erg = ohne_gruebeln(msg.get("content") or "").strip()
                    return {"text": erg} if erg else {"fehler": "Es kam keine Antwort zurück."}
                nachrichten.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": aufrufe})
                for aufruf in aufrufe:
                    f = aufruf.get("function") or {}
                    try:
                        arg = json.loads(f.get("arguments") or "{}") if isinstance(f.get("arguments"), str) else (f.get("arguments") or {})
                    except ValueError:
                        arg = {}
                    ziel = wo.get(f.get("name", ""))
                    if ziel is None:
                        ergebnis = "Dieses Werkzeug gibt es nicht."
                    elif not self.werkzeug_frage(ziel[1], arg, ziel[2]):
                        ergebnis = "Der Benutzer hat den Aufruf abgelehnt."
                    else:
                        try:
                            ergebnis = ziel[0].aufrufen(ziel[1], arg)
                        except M.McpFehler as e:
                            ergebnis = f"Fehler: {e}"
                    nachrichten.append({"role": "tool", "tool_call_id": aufruf.get("id", ""), "content": str(ergebnis)[:8000]})
            return {"fehler": "Die KI hat zu viele Werkzeugaufrufe gebraucht. Bitte die Frage genauer stellen."}
        except M.McpFehler as e:
            return {"fehler": f"MCP: {e}"}
        except urllib.error.HTTPError as e:
            return {"fehler": f"Der Anbieter meldet Fehler {e.code} — unterstützt das Modell Werkzeuge?"}
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {"fehler": f"Es hat nicht geklappt: {getattr(e, 'reason', e)}"}
        finally:
            for c in clients:
                c.schliessen()

    def vorschlaege(self, text: str) -> dict:
        r = self.anfrage(anweisung_vorschlaege(self.k), text, VORSCHLAG_BAUPLAN, self.modell("textanalyse"))
        if "fehler" in r:
            return r
        self._kosten(r.get("cent"))
        try:
            daten = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", r["ergebnis"].strip()))
            lst = daten["vorschlaege"]
            assert isinstance(lst, list)
        except (ValueError, KeyError, AssertionError):
            return {"fehler": "Die Antwort kam nicht in der erwarteten Form."}
        # nur, was sich zeichengenau im Text wiederfindet, lässt sich einsetzen
        gut = [v for v in lst if isinstance(v, dict) and isinstance(v.get("alt"), str) and isinstance(v.get("neu"), str)
               and v["alt"].strip() and v["neu"].strip() and v["alt"] != v["neu"] and v["alt"] in text]
        from lunivo_writer.proofing.fund import klemmen
        for v in gut:                                   # Sicherheit des Modells (0…1), fehlt sie oder ist sie Unsinn: 0,5
            v["konfidenz"] = klemmen(v.get("konfidenz"))
            v["quelle"] = "ki"
        gut.sort(key=lambda v: -v["konfidenz"])
        return {"vorschlaege": gut, "cent": r.get("cent")}

    def synonyme(self, wort: str, umgebung: str = "") -> dict:
        """Wörter, die statt `wort` an dieser Stelle stehen könnten (Thesaurus — geht nur mit KI)."""
        anweisung = (f"Nenne gebräuchliche deutsche Wörter, die statt „{wort}“ an dieser Stelle stehen könnten. "
                     "Achte auf den Zusammenhang: Dasselbe Wort bedeutet je nach Satz Verschiedenes. "
                     "Nimm einfache, geläufige Wörter — dieser Text wird von einem Menschen mit Legasthenie geschrieben, "
                     "und ein seltenes Fremdwort hilft ihm nicht. Höchstens acht, jedes in der Form, in der es im Satz "
                     "stehen müsste. Fällt dir nichts Passendes ein, bleibt die Liste leer.")
        bauplan = {"type": "object", "properties": {"woerter": {"type": "array", "items": {"type": "string"}}},
                   "required": ["woerter"], "additionalProperties": False}
        r = self.anfrage(anweisung, umgebung or wort, bauplan)
        if "fehler" in r:
            return r
        self._kosten(r.get("cent"))
        try:
            daten = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", r["ergebnis"].strip()))
            lst = daten["woerter"]
            assert isinstance(lst, list)
        except (ValueError, KeyError, AssertionError):
            return {"fehler": "Die Antwort kam nicht in der erwarteten Form."}
        sauber = []
        for w in lst:
            if isinstance(w, str) and w.strip() and len(w) < 40 and w.strip().lower() != wort.lower() and w.strip() not in sauber:
                sauber.append(w.strip())
        return {"woerter": sauber[:8], "cent": r.get("cent")}

    def bild_erzeugen(self, beschreibung: str) -> dict:
        """Bild aus Text: nur eigene Anbieter mit „Bilder“, OpenAI-Schnittstelle POST <URL>/images/generations."""
        modell = self.k["aufgaben"].get("bildgenerierung", "")
        if not modell.startswith(EIGEN_MARKE):
            return {"fehler": "Dafür fehlt ein Anbieter mit „Bilder“ — in der KI-Konfiguration eintragen."}
        a = self.k.anbieter_holen(modell[len(EIGEN_MARKE):])
        if not a:
            return {"fehler": "Der gewählte Anbieter ist nicht mehr da. In der KI-Konfiguration neu wählen."}
        if not a["modell"]:
            return {"fehler": f"Für „{a['name']}“ ist kein Modell eingetragen."}
        kopf = {"authorization": "Bearer " + a["schluessel"]} if a["schluessel"] else {}
        try:
            with _post(a["url"] + "/images/generations", kopf,
                       {"model": a["modell"], "prompt": beschreibung, "n": 1, "size": "1024x1024"}, 90) as r:
                daten = json.loads(r.read().decode("utf-8"))
            e = (daten.get("data") or [{}])[0]
            if e.get("b64_json"):
                import base64
                return {"bild": base64.b64decode(e["b64_json"])}
            if e.get("url"):
                with urllib.request.urlopen(e["url"], timeout=90) as r2:
                    return {"bild": r2.read()}
            return {"fehler": f"„{a['name']}“ hat kein Bild zurückgegeben."}
        except urllib.error.HTTPError as e:
            zusatz = ""
            try:
                zusatz = (json.loads(e.read().decode("utf-8")).get("error") or {}).get("message", "")
            except (OSError, ValueError, AttributeError):
                pass
            return {"fehler": f"„{a['name']}“ meldet Fehler {e.code}" + (f" ({zusatz})" if zusatz else "")}
        except TimeoutError:
            return {"fehler": f"„{a['name']}“ hat zu lange gebraucht. Bitte noch einmal versuchen."}
        except (urllib.error.URLError, OSError, ValueError):
            return {"fehler": f"„{a['name']}“ ist unter {a['url']} nicht zu erreichen. Stimmt die URL?"}

    def ollama_modelle(self) -> list[str]:
        try:
            with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=3) as r:
                return sorted(m["name"] for m in json.loads(r.read().decode("utf-8")).get("models", []) if m.get("name"))
        except (OSError, ValueError, KeyError):
            return []


def anbieter_modelle(url: str, schluessel: str = "") -> list[str]:
    """GET <URL>/models — so fragen OpenAI und die meisten OpenAI-kompatiblen Dienste (auch Ollama unter /v1)."""
    req = urllib.request.Request(url.rstrip("/") + "/models", headers={"accept": "application/json",
                                 **({"authorization": "Bearer " + schluessel} if schluessel else {})})
    with urllib.request.urlopen(req, timeout=6) as r:
        d = json.loads(r.read().decode("utf-8"))
    return sorted({m.get("id") or m.get("name") for m in (d.get("data") or d.get("models") or []) if isinstance(m, dict)} - {None})


# ---------------------------------------------------------------- Ergebnis ins Dokument: Wort-Diff
_STUECKE = re.compile(r"\s+|[^\s]+")


def aenderungen(alt: str, neu: str):
    """Welche Wörter haben sich geändert? → [{von, bis, text}] in „alt"-Zeichenstellen; None, wenn zu groß."""
    a, b = _STUECKE.findall(alt), _STUECKE.findall(neu)
    if len(a) * len(b) > 400000:
        return None
    pos = [0]
    for s in a:
        pos.append(pos[-1] + len(s))
    blocks = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            blocks.append({"von": pos[i1], "bis": pos[i2], "text": "".join(b[j1:j2])})
    return blocks


def ersetze_ergebnis(alt: str, neu: str):
    """→ (liste_von_ersetzungen (von, bis, text) von hinten nach vorn, ganz: bool, absaetze)."""
    az, nz = alt.split("\n"), neu.split("\n")
    if len(az) != len(nz):
        return [(0, len(alt), neu)], True, 0
    ops, stelle, geaendert = [], len(alt), 0
    for i in range(len(az) - 1, -1, -1):
        anfang = stelle - len(az[i])
        if az[i] != nz[i]:
            blocks = aenderungen(az[i], nz[i])
            if blocks is None:
                ops.append((anfang, stelle, nz[i]))
            else:
                for b in reversed(blocks):
                    ops.append((anfang + b["von"], anfang + b["bis"], b["text"]))
            geaendert += 1
        stelle = anfang - 1
    return ops, False, geaendert
