<<<<<<< HEAD
"""Phase 13 Lesson 10 - MCP resources and prompts in the notes server.

Extends the Lesson 07 server with:
  - resources/list, resources/read for per-note URIs
  - resources/subscribe + notifications/resources/updated
  - prompts/list, prompts/get with argument rendering
  - a dynamic notes://recent resource

Stdlib; in-process dispatch (no transport), focuses on the new messages.

Run: python code/main.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable


NOTES: dict[str, dict] = {
    "note-1": {"title": "MCP primitives", "body": "tools, resources, prompts"},
    "note-2": {"title": "Transport layer", "body": "stdio and Streamable HTTP"},
    "note-3": {"title": "Sampling loop", "body": "server asks client for LLM"},
    "note-4": {"title": "Tasks", "body": "call-now fetch-later async"},
    "note-5": {"title": "Apps", "body": "ui:// interactive resources"},
}


SUBSCRIPTIONS: set[str] = set()
NOTIFICATIONS: list[dict] = []


def emit_notification(method: str, params: dict) -> None:
    NOTIFICATIONS.append({"jsonrpc": "2.0", "method": method, "params": params})


def update_note(nid: str, new_body: str) -> None:
    if nid in NOTES:
        NOTES[nid]["body"] = new_body
        if f"notes://{nid}" in SUBSCRIPTIONS:
            emit_notification("notifications/resources/updated",
                              {"uri": f"notes://{nid}"})
        if "notes://recent" in SUBSCRIPTIONS:
            emit_notification("notifications/resources/updated",
                              {"uri": "notes://recent"})


def handle_resources_list(params: dict) -> dict:
    res = [
        {"uri": f"notes://{nid}", "name": n["title"],
         "mimeType": "text/markdown", "description": n["body"][:60]}
        for nid, n in NOTES.items()
    ]
    res.append({
        "uri": "notes://recent",
        "name": "Recent notes",
        "mimeType": "application/json",
        "description": "Latest five notes (dynamic)",
    })
    return {"resources": res}


def handle_resources_read(params: dict) -> dict:
    uri = params["uri"]
    if uri == "notes://recent":
        recent = list(NOTES.items())[-5:]
        return {"contents": [{"uri": uri, "mimeType": "application/json",
                              "text": json.dumps([{"id": k, **v} for k, v in recent])}]}
    nid = uri.replace("notes://", "")
    if nid not in NOTES:
        raise ValueError(f"not found: {uri}")
    n = NOTES[nid]
    return {"contents": [{"uri": uri, "mimeType": "text/markdown",
                          "text": f"# {n['title']}\n\n{n['body']}"}]}


def handle_resources_subscribe(params: dict) -> dict:
    SUBSCRIPTIONS.add(params["uri"])
    return {}


def handle_resources_unsubscribe(params: dict) -> dict:
    SUBSCRIPTIONS.discard(params["uri"])
    return {}


PROMPTS = [
    {
        "name": "review_note",
        "description": "Produce a critique of a note with concrete improvements.",
        "arguments": [
            {"name": "note_id", "description": "Id of the note to review", "required": True},
            {"name": "style", "description": "'concise' or 'thorough'", "required": False},
        ],
    },
    {
        "name": "summarize_tag",
        "description": "Write a one-paragraph summary of all notes with a given tag.",
        "arguments": [
            {"name": "tag", "description": "Tag to aggregate", "required": True},
        ],
    },
]


def handle_prompts_list(params: dict) -> dict:
    return {"prompts": PROMPTS}


def handle_prompts_get(params: dict) -> dict:
    name = params["name"]
    args = params.get("arguments", {})
    if name == "review_note":
        nid = args.get("note_id", "")
        style = args.get("style", "thorough")
        note = NOTES.get(nid, {"title": "?", "body": "(missing)"})
        return {
            "description": f"Review note {nid} ({style})",
            "messages": [
                {"role": "user", "content": {"type": "text",
                    "text": f"You are reviewing a note ({style} mode). Title: {note['title']}.\nBody:\n{note['body']}\n\nProduce improvements."}},
            ],
        }
    if name == "summarize_tag":
        tag = args.get("tag", "")
        return {
            "description": f"Summarize notes tagged {tag!r}",
            "messages": [
                {"role": "user", "content": {"type": "text",
                    "text": f"Summarize the notes tagged {tag!r} in one paragraph."}},
            ],
        }
    raise ValueError(f"unknown prompt: {name}")


HANDLERS: dict[str, Callable] = {
    "resources/list": handle_resources_list,
    "resources/read": handle_resources_read,
    "resources/subscribe": handle_resources_subscribe,
    "resources/unsubscribe": handle_resources_unsubscribe,
    "prompts/list": handle_prompts_list,
    "prompts/get": handle_prompts_get,
}


def dispatch(method: str, params: dict) -> dict:
    if method not in HANDLERS:
        raise ValueError(f"unknown method: {method}")
    return HANDLERS[method](params)


def demo() -> None:
    print("=" * 72)
    print("PHASE 13 LESSON 10 - RESOURCES AND PROMPTS")
    print("=" * 72)

    print("\n1) resources/list")
    r = dispatch("resources/list", {})
    for item in r["resources"][:3]:
        print(f"  {item['uri']:22s}  {item['name']}")

    print("\n2) resources/read notes://note-1")
    r = dispatch("resources/read", {"uri": "notes://note-1"})
    print(f"  mimeType: {r['contents'][0]['mimeType']}")
    print(f"  body: {r['contents'][0]['text'][:60]}...")

    print("\n3) resources/read notes://recent (dynamic)")
    r = dispatch("resources/read", {"uri": "notes://recent"})
    print(f"  count: {len(json.loads(r['contents'][0]['text']))}")

    print("\n4) subscribe to note-1 and update")
    dispatch("resources/subscribe", {"uri": "notes://note-1"})
    print(f"  subscriptions: {list(SUBSCRIPTIONS)}")
    update_note("note-1", "UPDATED body content")
    print(f"  notifications emitted: {len(NOTIFICATIONS)}")
    print(f"  last = {NOTIFICATIONS[-1]}")

    print("\n5) prompts/list")
    r = dispatch("prompts/list", {})
    for p in r["prompts"]:
        print(f"  /{p['name']:15s}  args={[a['name'] for a in p['arguments']]}")

    print("\n6) prompts/get review_note note_id=note-1 style=concise")
    r = dispatch("prompts/get", {"name": "review_note",
                                 "arguments": {"note_id": "note-1", "style": "concise"}})
    print(f"  description: {r['description']}")
    print(f"  user msg: {r['messages'][0]['content']['text'][:80]}...")

    print("\n--- decision rule recap ---")
    print("  tool      -> user wants to search / filter / mutate")
    print("  resource  -> user wants to include data as context")
    print("  prompt    -> user wants a re-runnable multi-step workflow")


def main() -> None:
    demo()


if __name__ == "__main__":
    main()
=======
"""Runnable companion to docs/zh.md for MCP protocol version 2026-07-28.
Official resources contract: https://modelcontextprotocol.io/specification/2026-07-28/server/resources
Official prompts contract: https://modelcontextprotocol.io/specification/2026-07-28/server/prompts
Official subscription contract: https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions
The simulator keeps transport details small so the wire invariants remain visible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = "2026-07-28"
SERVER_INFO = {"name": "lesson-resource-server", "version": "2.0.0"}

NOTES = {
    "notes://note-2": {
        "name": "Release checklist",
        "description": "Checks to run before publishing",
        "mimeType": "text/markdown",
        "text": "# Release\n\n- Run tests\n- Confirm the tag",
    },
    "notes://note-1": {
        "name": "Architecture decision",
        "description": "Why the service uses a stateless protocol boundary",
        "mimeType": "text/markdown",
        "text": "# Decision\n\nKeep protocol requests self-contained.",
    },
}

PROMPTS = {
    "release_brief": {
        "title": "Draft a release brief",
        "description": "Turn release facts into a concise user-facing brief",
        "arguments": [
            {"name": "audience", "description": "Who will read the brief", "required": True}
        ],
    },
    "review_note": {
        "title": "Review a note",
        "description": "Review one note for a named concern",
        "arguments": [
            {"name": "uri", "description": "The note resource URI", "required": True},
            {"name": "focus", "description": "The review focus", "required": False},
        ],
    },
}


class RpcError(Exception):
    def __init__(self, code: int, message: str, data: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}

    def as_json(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data:
            error["data"] = self.data
        return error


def request_meta(client_name: str = "lesson-client") -> dict[str, Any]:
    return {
        "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientInfo": {"name": client_name, "version": "1.0.0"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def response_meta() -> dict[str, Any]:
    return {"io.modelcontextprotocol/serverInfo": SERVER_INFO.copy()}


def complete(**payload: Any) -> dict[str, Any]:
    return {"resultType": "complete", **payload, "_meta": response_meta()}


def validate_request_meta(params: dict[str, Any]) -> None:
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        raise RpcError(-32602, "Missing request metadata")
    requested = meta.get("io.modelcontextprotocol/protocolVersion")
    if not isinstance(requested, str):
        raise RpcError(-32602, "Missing or invalid protocol version")
    if requested != PROTOCOL_VERSION:
        raise RpcError(
            -32022,
            "Unsupported protocol version",
            {"supported": [PROTOCOL_VERSION], "requested": requested},
        )
    if not isinstance(meta.get("io.modelcontextprotocol/clientCapabilities"), dict):
        raise RpcError(-32602, "Missing client capabilities")


def server_discover(_: dict[str, Any]) -> dict[str, Any]:
    return complete(
        supportedVersions=[PROTOCOL_VERSION],
        capabilities={
            "resources": {"listChanged": True, "subscribe": True},
            "prompts": {"listChanged": True},
        },
        instructions="Read notes by URI and let users select review prompts.",
        ttlMs=3_600_000,
        cacheScope="public",
    )


def resources_list(_: dict[str, Any]) -> dict[str, Any]:
    resources = [
        {key: value[key] for key in ("name", "description", "mimeType")} | {"uri": uri}
        for uri, value in sorted(NOTES.items())
    ]
    return complete(resources=resources, ttlMs=300_000, cacheScope="public")


def resources_read(params: dict[str, Any]) -> dict[str, Any]:
    uri = params.get("uri")
    if not isinstance(uri, str) or uri not in NOTES:
        raise RpcError(-32602, "Unknown or invalid resource URI", {"uri": uri})
    note = NOTES[uri]
    return complete(
        contents=[{"uri": uri, "mimeType": note["mimeType"], "text": note["text"]}],
        ttlMs=60_000,
        cacheScope="private",
    )


def prompts_list(_: dict[str, Any]) -> dict[str, Any]:
    prompts = [{"name": name, **definition} for name, definition in sorted(PROMPTS.items())]
    return complete(prompts=prompts, ttlMs=600_000, cacheScope="public")


def prompts_get(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})
    if name not in PROMPTS or not isinstance(arguments, dict):
        raise RpcError(-32602, "Unknown prompt or invalid arguments", {"name": name})
    if name == "review_note":
        uri = arguments.get("uri")
        if uri not in NOTES:
            raise RpcError(-32602, "review_note requires a known resource URI", {"uri": uri})
        focus = arguments.get("focus", "correctness")
        text = f"Review the resource {uri} for {focus}. Cite the URI in every finding."
    else:
        audience = arguments.get("audience")
        if not isinstance(audience, str) or not audience.strip():
            raise RpcError(-32602, "release_brief requires audience")
        text = f"Draft a release brief for {audience}. Separate verified facts from open questions."
    return complete(
        description=PROMPTS[name]["description"],
        messages=[{"role": "user", "content": {"type": "text", "text": text}}],
    )


SUPPORTED_NOTIFICATION_FIELDS = {
    "promptsListChanged",
    "resourcesListChanged",
    "resourceSubscriptions",
}


@dataclass(frozen=True)
class SubscriptionStream:
    subscription_id: int | str
    notifications: dict[str, Any]

    def _meta(self) -> dict[str, Any]:
        return {"io.modelcontextprotocol/subscriptionId": self.subscription_id}

    def acknowledged(self) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": "notifications/subscriptions/acknowledged",
            "params": {"_meta": self._meta(), "notifications": self.notifications},
        }

    def resource_updated(self, uri: str) -> dict[str, Any] | None:
        if uri not in self.notifications.get("resourceSubscriptions", []):
            return None
        return {
            "jsonrpc": "2.0",
            "method": "notifications/resources/updated",
            "params": {"_meta": self._meta(), "uri": uri},
        }

    def resources_list_changed(self) -> dict[str, Any] | None:
        if not self.notifications.get("resourcesListChanged"):
            return None
        return {
            "jsonrpc": "2.0",
            "method": "notifications/resources/list_changed",
            "params": {"_meta": self._meta()},
        }

    def prompts_list_changed(self) -> dict[str, Any] | None:
        if not self.notifications.get("promptsListChanged"):
            return None
        return {
            "jsonrpc": "2.0",
            "method": "notifications/prompts/list_changed",
            "params": {"_meta": self._meta()},
        }

    def close(self) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": self.subscription_id,
            "result": {
                "resultType": "complete",
                "_meta": self._meta() | response_meta(),
            },
        }


def subscriptions_listen(request_id: int | str, params: dict[str, Any]) -> SubscriptionStream:
    requested = params.get("notifications")
    if not isinstance(requested, dict):
        raise RpcError(-32602, "subscriptions/listen requires a notifications filter")
    agreed: dict[str, Any] = {}
    for key in sorted(SUPPORTED_NOTIFICATION_FIELDS):
        value = requested.get(key)
        if key == "resourceSubscriptions" and value is not None:
            if not isinstance(value, list) or not all(isinstance(uri, str) for uri in value):
                raise RpcError(-32602, "resourceSubscriptions must be an array of URIs")
            agreed[key] = sorted(set(value))
        elif key != "resourceSubscriptions" and value is True:
            agreed[key] = True
    return SubscriptionStream(request_id, agreed)


HANDLERS = {
    "server/discover": server_discover,
    "resources/list": resources_list,
    "resources/read": resources_read,
    "prompts/list": prompts_list,
    "prompts/get": prompts_get,
}


def handle(request: dict[str, Any]) -> dict[str, Any] | SubscriptionStream | None:
    is_notification = "id" not in request
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})
    if not isinstance(params, dict):
        if is_notification:
            return None
        error = RpcError(-32602, "params must be an object")
        return {"jsonrpc": "2.0", "id": request_id, "error": error.as_json()}
    try:
        validate_request_meta(params)
        if is_notification:
            handler = HANDLERS.get(method)
            if handler is not None:
                handler(params)
            return None
        if method == "subscriptions/listen":
            if request_id is None:
                raise RpcError(-32602, "subscriptions/listen requires a request id")
            return subscriptions_listen(request_id, params)
        handler = HANDLERS.get(method)
        if handler is None:
            raise RpcError(-32601, "Method not found", {"method": method})
        return {"jsonrpc": "2.0", "id": request_id, "result": handler(params)}
    except RpcError as exc:
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "error": exc.as_json()}


def rpc_request(request_id: int, method: str, **params: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {**params, "_meta": request_meta()},
    }


def demo() -> list[dict[str, Any]]:
    transcript: list[dict[str, Any]] = []
    transcript.append(handle(rpc_request(0, "server/discover")))
    transcript.append(handle(rpc_request(1, "resources/list")))
    transcript.append(handle(rpc_request(2, "resources/read", uri="notes://note-1")))
    transcript.append(handle(rpc_request(3, "prompts/list")))
    transcript.append(
        handle(
            rpc_request(
                4,
                "prompts/get",
                name="review_note",
                arguments={"uri": "notes://note-1", "focus": "operational risk"},
            )
        )
    )
    stream = handle(
        rpc_request(
            5,
            "subscriptions/listen",
            notifications={
                "resourcesListChanged": True,
                "resourceSubscriptions": ["notes://note-1"],
            },
        )
    )
    assert isinstance(stream, SubscriptionStream)
    transcript.extend([stream.acknowledged(), stream.resource_updated("notes://note-1"), stream.close()])
    return [item for item in transcript if item is not None]


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
>>>>>>> main
