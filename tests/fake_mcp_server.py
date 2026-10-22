"""Ein winziger MCP-Server für die Tests: Werkzeug „echo“ (JSON-RPC über stdin/stdout)."""
import json
import sys

for zeile in sys.stdin:
    m = json.loads(zeile)
    if "id" not in m:
        continue
    if m["method"] == "initialize":
        r = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "fake", "version": "1"}}
    elif m["method"] == "tools/list":
        r = {"tools": [{"name": "echo", "description": "Gibt den Text zurück", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}
    elif m["method"] == "tools/call":
        r = {"content": [{"type": "text", "text": "ECHO:" + m["params"]["arguments"].get("text", "")}]}
    else:
        r = {}
    print(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": r}), flush=True)
