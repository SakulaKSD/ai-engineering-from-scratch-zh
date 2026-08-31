<<<<<<< HEAD
"""Phase 13 Lesson 06 - MCP fundamentals, JSON-RPC 2.0 lifecycle walk.

Plays out the initialize -> tools/list -> tools/call sequence by hand with
stdlib JSON-RPC envelopes. No transport, no real server - just the message
shapes so you can compare to the 2025-11-25 spec line by line.

Run: python code/main.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = "2025-11-25"


@dataclass
class Message:
    raw: dict

    @property
    def kind(self) -> str:
        if "method" in self.raw and "id" not in self.raw:
            return "notification"
        if "method" in self.raw:
            return "request"
        if "result" in self.raw or "error" in self.raw:
            return "response"
        return "unknown"


def request(mid: int, method: str, params: dict | None = None) -> Message:
    body = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        body["params"] = params
    return Message(body)


def response(mid: int, result: Any) -> Message:
    return Message({"jsonrpc": "2.0", "id": mid, "result": result})


def error(mid: int, code: int, message: str, data: Any = None) -> Message:
    err: dict = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return Message({"jsonrpc": "2.0", "id": mid, "error": err})


def notification(method: str, params: dict | None = None) -> Message:
    body: dict = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    return Message(body)


def pretty(tag: str, msg: Message) -> None:
    arrow = {"request": ">>>", "response": "<<<",
             "notification": "-->", "unknown": "???"}[msg.kind]
    print(f"{tag} {arrow} [{msg.kind}]")
    print(json.dumps(msg.raw, indent=2))
    print()


CLIENT_INFO = {"name": "learner-client", "version": "1.0.0"}
SERVER_INFO = {"name": "notes-server", "version": "1.0.0"}

CLIENT_CAPS = {
    "roots": {"listChanged": True},
    "sampling": {},
    "elicitation": {},
}

SERVER_CAPS = {
    "tools": {"listChanged": True},
    "resources": {"subscribe": True, "listChanged": True},
    "prompts": {"listChanged": True},
}


TOOL_LIST = [
    {
        "name": "notes_search",
        "description": (
            "Use when the user searches for notes by keywords. "
            "Do not use for tag filters; use notes_list."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            "required": ["query"],
        },
    }
]


def run_sequence() -> None:
    print("=" * 72)
    print("PHASE 13 LESSON 06 - MCP LIFECYCLE WALK")
    print("=" * 72)
    print()

    print("--- PHASE 1: initialize ---")
    pretty("client", request(1, "initialize", {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": CLIENT_CAPS,
        "clientInfo": CLIENT_INFO,
    }))
    pretty("server", response(1, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": SERVER_CAPS,
        "serverInfo": SERVER_INFO,
    }))
    pretty("client", notification("notifications/initialized"))

    print("--- PHASE 2: operation ---")
    pretty("client", request(2, "tools/list"))
    pretty("server", response(2, {"tools": TOOL_LIST}))

    pretty("client", request(3, "tools/call", {
        "name": "notes_search",
        "arguments": {"query": "JSON-RPC", "limit": 5},
    }))
    pretty("server", response(3, {
        "content": [
            {"type": "text", "text": "Found 2 notes matching 'JSON-RPC':"},
            {"type": "text", "text": "- note-14 JSON-RPC 2.0 intro"},
            {"type": "text", "text": "- note-22 MCP handshake walkthrough"},
        ],
        "isError": False,
    }))

    pretty("server", notification("notifications/tools/list_changed"))

    print("--- PHASE 2 error example ---")
    pretty("client", request(4, "tools/call", {
        "name": "notes_delete",
        "arguments": {"id": "unknown"},
    }))
    pretty("server", error(4, -32601, "Method not found",
                           data={"tool": "notes_delete"}))

    print("--- PHASE 3: shutdown (transport-level, no JSON-RPC method) ---")
    print("  client closes stdio or HTTP session; server terminates.")


def main() -> None:
    run_sequence()
    print("\nsummary:")
    print(f"  protocolVersion  = {PROTOCOL_VERSION}")
    print(f"  client caps      = {list(CLIENT_CAPS.keys())}")
    print(f"  server caps      = {list(SERVER_CAPS.keys())}")
    print(f"  negotiated ops   = tools, resources (subscribe), prompts")
    print(f"                     + sampling (server-to-client), elicitation")


if __name__ == "__main__":
    main()
=======
"""Phase 13 Lesson 06: trace the stateless MCP request lifecycle.
Lesson: phases/13-tools-and-protocols/06-mcp-fundamentals/docs/zh.md
Specification: https://modelcontextprotocol.io/specification/2026-07-28/
Builds JSON-RPC requests, validates per-request metadata, and emits results.
Run: python3 main.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_VERSIONS = [PROTOCOL_VERSION]
VERSION_KEY = "io.modelcontextprotocol/protocolVersion"
CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"

CLIENT_INFO = {"name": "lesson-06-client", "version": "1.0.0"}
SERVER_INFO = {"name": "lesson-06-notes", "version": "1.0.0"}
SERVER_CAPABILITIES = {"tools": {"listChanged": False}}

TOOLS = [
    {
        "name": "notes_search",
        "description": "Search notes by keyword.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "notes_list",
        "description": "List note titles.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


@dataclass(frozen=True)
class Trace:
    kind: str
    method: str
    era: str
    detail: str


def request_meta(
    version: str = PROTOCOL_VERSION,
    capabilities: dict[str, Any] | None = None,
    include_client_info: bool = True,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        VERSION_KEY: version,
        CAPABILITIES_KEY: {} if capabilities is None else capabilities,
    }
    if include_client_info:
        meta[CLIENT_INFO_KEY] = CLIENT_INFO.copy()
    return meta


def make_request(
    request_id: int | str,
    method: str,
    params: dict[str, Any] | None = None,
    *,
    version: str = PROTOCOL_VERSION,
    capabilities: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body_params = dict(params or {})
    body_params["_meta"] = request_meta(version, capabilities)
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": body_params,
    }


def rpc_error(
    request_id: int | str | None,
    code: int,
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def complete_result(
    payload: dict[str, Any],
    *,
    ttl_ms: int | None = None,
    cache_scope: str | None = None,
) -> dict[str, Any]:
    result = {
        "resultType": "complete",
        **payload,
        "_meta": {SERVER_INFO_KEY: SERVER_INFO.copy()},
    }
    if ttl_ms is not None:
        result["ttlMs"] = ttl_ms
        result["cacheScope"] = cache_scope or "private"
    return result


def validate_request(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return rpc_error(request_id, -32600, "Invalid Request")
    params = message.get("params")
    if not isinstance(params, dict):
        return rpc_error(request_id, -32602, "params must be an object")
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        return rpc_error(request_id, -32602, "params._meta is required")
    version = meta.get(VERSION_KEY)
    if not isinstance(version, str):
        return rpc_error(request_id, -32602, f"{VERSION_KEY} is required")
    if version not in SUPPORTED_VERSIONS:
        return rpc_error(
            request_id,
            -32022,
            "Unsupported protocol version",
            {"requested": version, "supported": SUPPORTED_VERSIONS.copy()},
        )
    if not isinstance(meta.get(CAPABILITIES_KEY), dict):
        return rpc_error(request_id, -32602, f"{CAPABILITIES_KEY} is required")
    client_info = meta.get(CLIENT_INFO_KEY)
    if client_info is not None and (
        not isinstance(client_info, dict)
        or not isinstance(client_info.get("name"), str)
        or not isinstance(client_info.get("version"), str)
    ):
        return rpc_error(request_id, -32602, f"{CLIENT_INFO_KEY} is malformed")
    return None


def dispatch(message: dict[str, Any]) -> dict[str, Any] | None:
    if "id" not in message:
        return None
    invalid = validate_request(message)
    if invalid is not None:
        return invalid

    request_id = message["id"]
    method = message["method"]
    params = message["params"]
    if method == "server/discover":
        result = complete_result(
            {
                "supportedVersions": SUPPORTED_VERSIONS.copy(),
                "capabilities": SERVER_CAPABILITIES.copy(),
                "instructions": "Use notes_list for titles and notes_search for keywords.",
            },
            ttl_ms=3_600_000,
            cache_scope="public",
        )
    elif method == "tools/list":
        result = complete_result(
            {"tools": sorted(TOOLS, key=lambda tool: tool["name"])},
            ttl_ms=30_000,
            cache_scope="public",
        )
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name == "notes_list":
            text = "JSON-RPC notes, MCP metadata notes"
            result = complete_result(
                {"content": [{"type": "text", "text": text}], "isError": False}
            )
        elif name == "notes_search" and isinstance(arguments.get("query"), str):
            text = f"Found notes matching {arguments['query']!r}"
            result = complete_result(
                {"content": [{"type": "text", "text": text}], "isError": False}
            )
        else:
            result = complete_result(
                {
                    "content": [{"type": "text", "text": f"Unknown or invalid tool: {name}"}],
                    "isError": True,
                }
            )
    else:
        return rpc_error(request_id, -32601, f"Method not found: {method}")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def trace_message(message: dict[str, Any]) -> Trace:
    if "method" in message and "id" in message:
        method = str(message["method"])
        if method == "initialize":
            return Trace("request", method, "legacy", "connection-scoped handshake")
        params = message.get("params", {})
        meta = params.get("_meta", {}) if isinstance(params, dict) else {}
        if isinstance(meta, dict) and VERSION_KEY in meta and CAPABILITIES_KEY in meta:
            detail = f"version={meta[VERSION_KEY]} capabilities=current-request"
            return Trace("request", method, "modern", detail)
        return Trace("request", method, "invalid", "missing modern request metadata")
    if "result" in message or "error" in message:
        if "error" in message:
            return Trace("response", "error", "unknown", f"code={message['error']['code']}")
        result = message["result"]
        era = "modern" if result.get("resultType") else "legacy"
        return Trace("response", "result", era, f"resultType={result.get('resultType', 'absent')}")
    if "method" in message:
        return Trace("notification", str(message["method"]), "unknown", "no response expected")
    return Trace("unknown", "", "invalid", "not a JSON-RPC message")


def show(message: dict[str, Any]) -> None:
    trace = trace_message(message)
    print(f"[{trace.kind}/{trace.era}] {trace.method}: {trace.detail}")
    print(json.dumps(message, indent=2, sort_keys=True))


def main() -> None:
    requests = [
        make_request(1, "server/discover"),
        make_request(2, "tools/list"),
        make_request(
            3,
            "tools/call",
            {"name": "notes_search", "arguments": {"query": "JSON-RPC"}},
        ),
        make_request(4, "tools/list", version="2027-01-01"),
    ]
    print("MCP 2026-07-28 stateless request trace")
    for current in requests:
        print()
        show(current)
        response = dispatch(current)
        if response is not None:
            show(response)
    print("\nTransport closes. No protocol session was created or terminated.")


if __name__ == "__main__":
    main()
>>>>>>> main
