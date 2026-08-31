<<<<<<< HEAD
"""Phase 13 Lesson 14 - MCP Apps (SEP-1724, 2026-01-26) ui:// resources.

visualize_timeline tool returns a ui://notes/timeline resource with inlined
HTML + SVG. The resources/read handler returns the full HTML bundle with a
CSP-sensible profile and a placeholder postMessage JSON-RPC client that calls
back to host.callTool.

Stdlib only. Run and inspect the emitted HTML.

Run: python code/main.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable


NOTES = [
    {"id": "note-1", "title": "MCP primitives", "created": "2026-01-10"},
    {"id": "note-2", "title": "Transport",       "created": "2026-02-03"},
    {"id": "note-3", "title": "Sampling",        "created": "2026-02-15"},
    {"id": "note-4", "title": "Async Tasks",     "created": "2026-03-01"},
    {"id": "note-5", "title": "Apps ui://",     "created": "2026-04-22"},
]


TIMELINE_CSP = {
    "default-src": "'self'",
    "script-src": "'self' 'unsafe-inline'",
    "connect-src": "'self'",
    "img-src": "'self' data:",
    "style-src": "'self' 'unsafe-inline'",
}


def timeline_html(notes: list[dict]) -> str:
    """Generate a self-contained HTML timeline. SVG + inline JS only."""
    points = ""
    for i, n in enumerate(notes):
        x = 40 + i * 110
        points += f'''<g transform="translate({x},80)">
    <circle r="7" fill="#2e7d32" stroke="#1a1a1a"/>
    <text y="-14" text-anchor="middle" font-size="10">{n["created"]}</text>
    <text y="28" text-anchor="middle" font-size="11" font-weight="600">{n["title"]}</text>
    </g>'''
    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Notes timeline</title>
<style>
 body {{ font-family: Georgia, serif; margin: 16px; }}
 h1 {{ font-size: 18px; }}
 .hint {{ color: #555; font-size: 11px; font-style: italic; }}
</style>
</head><body>
<h1>Notes timeline</h1>
<svg width="620" height="140" viewBox="0 0 620 140">
 <line x1="40" y1="80" x2="580" y2="80" stroke="#1a1a1a" stroke-width="1.5"/>
 {points}
</svg>
<p class="hint">click a node to call host.callTool("notes_open", {{id}})</p>
<script>
 // postMessage JSON-RPC client talking to the MCP host (Claude Desktop, etc.)
 let rid = 0;
 function hostCall(method, params) {{
   return new Promise(resolve => {{
     const id = ++rid;
     const handler = e => {{
       if (e.data && e.data.id === id) {{
         window.removeEventListener('message', handler);
         resolve(e.data.result);
       }}
     }};
     window.addEventListener('message', handler);
     window.parent.postMessage({{ jsonrpc: '2.0', id, method, params }}, '*');
   }});
 }}
 // host.callTool('notes_open', {{id: 'note-5'}}) would open note-5 in the host.
 // ui/initialize handshake
 window.parent.postMessage({{
   jsonrpc: '2.0', id: 0, method: 'ui/initialize',
   params: {{ theme: 'light', locale: 'en-US' }}
 }}, '*');
</script>
</body></html>
"""


def tool_visualize_timeline(args: dict) -> dict:
    return {
        "content": [
            {"type": "text", "text": "Notes timeline rendered below."},
            {"type": "ui_resource", "uri": "ui://notes/timeline"},
        ],
        "_meta": {
            "ui": {
                "resourceUri": "ui://notes/timeline",
                "csp": TIMELINE_CSP,
                "permissions": [],
            }
        },
        "isError": False,
    }


def resources_read(params: dict) -> dict:
    uri = params["uri"]
    if uri != "ui://notes/timeline":
        raise ValueError(f"unknown ui resource: {uri}")
    html = timeline_html(NOTES)
    return {
        "contents": [{
            "uri": uri,
            "mimeType": "text/html;profile=mcp-app",
            "text": html,
        }]
    }


def demo() -> None:
    print("=" * 72)
    print("PHASE 13 LESSON 14 - MCP APPS ui://")
    print("=" * 72)

    print("\n--- tools/call visualize_timeline ---")
    resp = tool_visualize_timeline({})
    print(json.dumps({k: v for k, v in resp.items() if k != "content"}, indent=2)[:400])
    for block in resp["content"]:
        kind = block["type"]
        summary = block.get("text") or block.get("uri")
        print(f"  content block [{kind}]: {summary}")

    print("\n--- resources/read ui://notes/timeline ---")
    r = resources_read({"uri": "ui://notes/timeline"})
    content = r["contents"][0]
    print(f"  mimeType: {content['mimeType']}")
    print(f"  html length: {len(content['text'])} bytes")
    print(f"  first 200 chars:\n{content['text'][:200]}")

    print("\n--- CSP applied ---")
    for k, v in TIMELINE_CSP.items():
        print(f"  {k:12s}: {v}")
    print("\n--- permissions: none requested ---")
    print("\n--- postMessage entrypoints available in the iframe ---")
    print("  host.callTool(name, args)")
    print("  host.readResource(uri)")
    print("  host.getPrompt(name, args)")
    print("  host.close()")


if __name__ == "__main__":
    demo()
=======
"""Phase 13 Lesson 14: MCP Apps on the MCP 2026-07-28 wire.
Lesson: phases/13-tools-and-protocols/14-mcp-apps/docs/zh.md
Spec: https://modelcontextprotocol.io/specification/2026-07-28
Models discovery, tools, resources, and a self-contained MCP Apps UI.
Lesson 09 owns the HTTP adapter; the UI pins its postMessage origin.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = "2026-07-28"
APPS_EXTENSION = "io.modelcontextprotocol/ui"
PROTOCOL_META = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_META = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"
SERVER_INFO = {"name": "timeline-app-server", "version": "2.0.0"}
RESOURCE_URI = "ui://notes/timeline.html"
RESOURCE_MIME = "text/html;profile=mcp-app"
HOST_ORIGIN = "https://host.example"

NOTES = [
    {"id": "note-1", "title": "Discover", "created": "2026-07-28"},
    {"id": "note-2", "title": "Per-request metadata", "created": "2026-07-29"},
    {"id": "note-3", "title": "MCP Apps", "created": "2026-07-30"},
]

APP_CSP = {
    "connectDomains": [],
    "resourceDomains": [],
    "frameDomains": [],
    "baseUriDomains": [],
}


@dataclass(frozen=True)
class ProtocolError(Exception):
    code: int
    message: str
    data: dict[str, Any] | None = None


def request_meta(*, apps: bool = True) -> dict[str, Any]:
    extensions = {APPS_EXTENSION: {}} if apps else {}
    return {
        PROTOCOL_META: PROTOCOL_VERSION,
        CLIENT_CAPABILITIES_META: {"extensions": extensions},
        CLIENT_INFO_META: {"name": "lesson-client", "version": "1.0.0"},
    }


def make_request(
    method: str,
    request_id: int,
    params: dict[str, Any] | None = None,
    *,
    apps: bool = True,
) -> tuple[dict[str, Any], dict[str, str]]:
    body_params = dict(params or {})
    body_params["_meta"] = request_meta(apps=apps)
    body = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": body_params}
    headers = {"MCP-Protocol-Version": PROTOCOL_VERSION, "Mcp-Method": method}
    if method in {"tools/call", "resources/read", "prompts/get"}:
        headers["Mcp-Name"] = str(body_params.get("name") or body_params.get("uri") or "")
    return body, headers


def timeline_html(notes: list[dict[str, str]]) -> str:
    items = "".join(
        "<li><button data-note='{}'>{}</button><time>{}</time></li>".format(
            html.escape(note["id"]),
            html.escape(note["title"]),
            html.escape(note["created"]),
        )
        for note in notes
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Notes timeline</title>
<style>body{{font:16px system-ui;margin:1rem}}li{{display:flex;gap:1rem;margin:.5rem}}</style>
</head><body><h1>Notes timeline</h1><ol>{items}</ol>
<script>
const hostOrigin = {json.dumps(HOST_ORIGIN)};
let nextId = 0;
function callTool(name, args) {{
  const id = ++nextId;
  window.parent.postMessage({{
    jsonrpc: "2.0", id, method: "tools/call",
    params: {{name, arguments: args}}
  }}, hostOrigin);
}}
window.addEventListener("message", (event) => {{
  if (event.origin !== hostOrigin || !event.data || event.data.jsonrpc !== "2.0") return;
  if (event.data.id === 0 && event.data.result) {{
    document.body.dataset.bridgeReady = "true";
    window.parent.postMessage({{
      jsonrpc: "2.0", method: "ui/notifications/initialized"
    }}, hostOrigin);
  }}
}});
document.querySelectorAll("button").forEach((button) => {{
  button.addEventListener("click", () => callTool("notes_open", {{id: button.dataset.note}}));
}});
// ui/initialize belongs to the Apps postMessage dialect, not MCP core initialization.
window.parent.postMessage({{
  jsonrpc: "2.0", id: 0, method: "ui/initialize",
  params: {{
    appInfo: {{name: "notes-timeline", version: "1.0.0"}},
    appCapabilities: {{}}
  }}
}}, hostOrigin);
</script></body></html>"""


class McpAppServer:
    def _validate(self, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        if body.get("jsonrpc") != "2.0":
            raise ProtocolError(-32600, "Invalid Request")
        method = body.get("method")
        params = body.get("params")
        if not isinstance(method, str) or not isinstance(params, dict):
            raise ProtocolError(-32600, "Invalid Request")
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            raise ProtocolError(-32602, "request params._meta is required")
        requested_version = meta.get(PROTOCOL_META)
        if not isinstance(requested_version, str):
            raise ProtocolError(-32602, "protocolVersion must be a string")
        if not isinstance(meta.get(CLIENT_CAPABILITIES_META), dict):
            raise ProtocolError(-32602, "clientCapabilities is required on every request")
        if headers.get("MCP-Protocol-Version") != requested_version:
            raise ProtocolError(-32020, "MCP-Protocol-Version header does not match body")
        if headers.get("Mcp-Method") != method:
            raise ProtocolError(-32020, "Mcp-Method header does not match body")
        expected_name = params.get("name") or params.get("uri")
        if method in {"tools/call", "resources/read", "prompts/get"}:
            if headers.get("Mcp-Name") != expected_name:
                raise ProtocolError(-32020, "Mcp-Name header does not match body")
        if requested_version != PROTOCOL_VERSION:
            raise ProtocolError(
                -32022,
                "Unsupported protocol version",
                {"supported": [PROTOCOL_VERSION], "requested": requested_version},
            )
        return meta

    @staticmethod
    def _apps_enabled(meta: dict[str, Any]) -> bool:
        caps = meta[CLIENT_CAPABILITIES_META]
        extensions = caps.get("extensions", {})
        return (
            isinstance(extensions, dict)
            and isinstance(extensions.get(APPS_EXTENSION), dict)
        )

    @staticmethod
    def _success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        result = dict(result)
        result.setdefault("resultType", "complete")
        result.setdefault("_meta", {})[SERVER_INFO_META] = SERVER_INFO
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, error: ProtocolError) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": error.code, "message": error.message}
        if error.data is not None:
            payload["data"] = error.data
        return {"jsonrpc": "2.0", "id": request_id, "error": payload}

    @staticmethod
    def _error_status(error: ProtocolError) -> int:
        return 404 if error.code == -32601 else 400

    def handle(
        self,
        body: dict[str, Any],
        headers: dict[str, str],
        *,
        http_method: str = "POST",
    ) -> tuple[int, dict[str, Any] | None]:
        if http_method != "POST":
            return 405, None
        is_notification = "id" not in body
        try:
            meta = self._validate(body, headers)
            method = body["method"]
            params = body["params"]
            if method == "server/discover":
                result = {
                    "supportedVersions": [PROTOCOL_VERSION],
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "extensions": {APPS_EXTENSION: {}},
                    },
                    "ttlMs": 300_000,
                    "cacheScope": "public",
                }
            elif method == "tools/list":
                tool: dict[str, Any] = {
                    "name": "notes_timeline",
                    "description": "Render a timeline of notes.",
                    "inputSchema": {"type": "object", "properties": {}},
                }
                if self._apps_enabled(meta):
                    tool["_meta"] = {"ui": {"resourceUri": RESOURCE_URI}}
                result = {"tools": [tool], "ttlMs": 60_000, "cacheScope": "public"}
            elif method == "tools/call":
                if params.get("name") != "notes_timeline":
                    raise ProtocolError(-32602, "Unknown tool")
                result = {
                    "content": [{"type": "text", "text": "Timeline ready."}],
                    "structuredContent": {"notes": NOTES},
                    "isError": False,
                }
            elif method == "resources/list":
                result = {
                    "resources": [{
                        "uri": RESOURCE_URI,
                        "name": "notes-timeline",
                        "description": "Interactive notes timeline for MCP Apps hosts.",
                        "mimeType": RESOURCE_MIME,
                    }],
                    "ttlMs": 60_000,
                    "cacheScope": "public",
                }
            elif method == "resources/read":
                if params.get("uri") != RESOURCE_URI:
                    raise ProtocolError(-32602, "Unknown resource URI")
                if not self._apps_enabled(meta):
                    raise ProtocolError(
                        -32021,
                        "MCP Apps client capability is required",
                        {
                            "requiredCapabilities": {
                                "extensions": {APPS_EXTENSION: {}}
                            }
                        },
                    )
                result = {
                    "contents": [{
                        "uri": RESOURCE_URI,
                        "mimeType": RESOURCE_MIME,
                        "text": timeline_html(NOTES),
                        "_meta": {"ui": {"csp": APP_CSP, "permissions": {}}},
                    }],
                    "ttlMs": 60_000,
                    "cacheScope": "public",
                }
            else:
                raise ProtocolError(-32601, "Method not found")
            if is_notification:
                return 202, None
            return 200, self._success(body["id"], result)
        except ProtocolError as error:
            if is_notification:
                return self._error_status(error), None
            return self._error_status(error), self._error(body.get("id"), error)


def demo() -> None:
    server = McpAppServer()
    for request_id, (method, params) in enumerate(
        [
            ("server/discover", {}),
            ("tools/list", {}),
            ("tools/call", {"name": "notes_timeline", "arguments": {}}),
            ("resources/read", {"uri": RESOURCE_URI}),
        ],
        start=1,
    ):
        body, headers = make_request(method, request_id, params)
        status, response = server.handle(body, headers)
        summary = response.get("result", response.get("error"))
        print(f"{status} {method}: {json.dumps(summary)[:220]}")


if __name__ == "__main__":
    demo()
>>>>>>> main
