"""MCP-Server (Model Context Protocol) über die Standard-Ein-/Ausgabe: Werkzeuge auflisten und aufrufen.

Ein Server ist ein Programm, das der Benutzer selbst einträgt (``befehl``, etwa „npx -y @modelcontextprotocol/server-filesystem ~/Dokumente“).
Gesprochen wird JSON-RPC 2.0, je Nachricht eine Zeile. Lunivo startet den Server nur für die Dauer einer Frage."""
from __future__ import annotations

import json
import queue
import shlex
import subprocess
import threading

ZEIT = 25.0                                    # Sekunden je Antwort des Servers


class McpFehler(Exception):
    pass


class McpClient:
    def __init__(self, befehl: str):
        try:
            teile = shlex.split(befehl)
        except ValueError as e:
            raise McpFehler(f"Der Befehl ist nicht lesbar: {e}")
        if not teile:
            raise McpFehler("Es ist kein Befehl eingetragen.")
        try:
            self.p = subprocess.Popen(teile, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        except OSError as e:
            raise McpFehler(f"Der Server startet nicht: {e.strerror or e}")
        self.q: queue.Queue = queue.Queue()
        self.nr = 0
        threading.Thread(target=self._lesen, daemon=True).start()
        self._senden({"jsonrpc": "2.0", "id": self._neu(), "method": "initialize",
                      "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "Lunivo Writer", "version": "1"}}})
        self._antwort(self.nr)
        self._senden({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _neu(self) -> int:
        self.nr += 1
        return self.nr

    def _lesen(self) -> None:
        for zeile in self.p.stdout:
            try:
                self.q.put(json.loads(zeile))
            except ValueError:
                continue                                      # Ausgaben, die kein JSON sind, überspringen
        self.q.put(None)

    def _senden(self, nachricht: dict) -> None:
        try:
            self.p.stdin.write(json.dumps(nachricht) + "\n"); self.p.stdin.flush()
        except (OSError, ValueError):
            raise McpFehler("Der Server antwortet nicht mehr.")

    def _antwort(self, nr: int) -> dict:
        while True:
            try:
                m = self.q.get(timeout=ZEIT)
            except queue.Empty:
                raise McpFehler("Der Server hat zu lange gebraucht.")
            if m is None:
                raise McpFehler("Der Server hat sich beendet.")
            if m.get("id") == nr:
                if "error" in m:
                    raise McpFehler(str((m["error"] or {}).get("message", "Fehler des Servers")))
                return m.get("result") or {}

    def werkzeuge(self) -> list[dict]:
        """[{name, description, inputSchema}] des Servers."""
        self._senden({"jsonrpc": "2.0", "id": self._neu(), "method": "tools/list", "params": {}})
        return self._antwort(self.nr).get("tools", [])

    def aufrufen(self, name: str, argumente: dict) -> str:
        self._senden({"jsonrpc": "2.0", "id": self._neu(), "method": "tools/call", "params": {"name": name, "arguments": argumente or {}}})
        r = self._antwort(self.nr)
        text = "\n".join(t.get("text", "") for t in r.get("content", []) if t.get("type") == "text")
        return ("Fehler des Werkzeugs: " + text) if r.get("isError") else text

    def schliessen(self) -> None:
        try:
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.terminate()
            self.p.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            self.p.kill()


def pruefen(befehl: str) -> list[dict]:
    """Verbindung testen: die Werkzeuge des Servers (für „Testen“ im Fenster KI-Einstellungen)."""
    c = McpClient(befehl)
    try:
        return c.werkzeuge()
    finally:
        c.schliessen()
