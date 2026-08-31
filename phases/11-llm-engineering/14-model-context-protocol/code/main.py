<<<<<<< HEAD
"""Minimal MCP server + in-process client round-trip.

The reference SDK is `mcp` on PyPI (install with `pip install mcp`). This file
does not import it so the demo runs on any Python 3.10+ without extra deps.
Instead it speaks raw JSON-RPC 2.0 over an in-memory pipe — the same wire
format an MCP stdio host uses — so you can see how tools, resources, and
prompts flow end to end.

Run with:
    python main.py
"""

from __future__ import annotations

import json
import queue
from dataclasses import dataclass
from typing import Any, Callable


PROTOCOL_VERSION = "2025-06-18"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]
    destructive: bool = False


@dataclass
class Resource:
    uri: str
    description: str
    handler: Callable[[], str]


@dataclass
class Prompt:
    name: str
    description: str
    arguments: list[str]
    handler: Callable[..., str]


class MCPServer:
    """Toy MCP server covering the three primitives and the discovery handshake."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: dict[str, Tool] = {}
        self.resources: dict[str, Resource] = {}
        self.prompts: dict[str, Prompt] = {}

    # Registration helpers -------------------------------------------------

    def tool(self, name: str, description: str, schema: dict[str, Any], *, destructive: bool = False):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = Tool(name, description, schema, fn, destructive)
            return fn
        return decorator

    def resource(self, uri: str, description: str):
        def decorator(fn: Callable[[], str]) -> Callable[[], str]:
            self.resources[uri] = Resource(uri, description, fn)
            return fn
        return decorator

    def prompt(self, name: str, description: str, arguments: list[str]):
        def decorator(fn: Callable[..., str]) -> Callable[..., str]:
            self.prompts[name] = Prompt(name, description, arguments, fn)
            return fn
        return decorator

    # JSON-RPC dispatch ----------------------------------------------------

    def handle(self, message: dict[str, Any]) -> dict[str, Any]:
        method = message.get("method")
        params = message.get("params") or {}
        request_id = message.get("id")

        try:
            if method == "initialize":
                result: Any = {
                    "protocolVersion": PROTOCOL_VERSION,
                    "serverInfo": {"name": self.name, "version": "0.1.0"},
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                }
            elif method == "tools/list":
                result = {"tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.input_schema,
                        "annotations": {"destructiveHint": t.destructive} if t.destructive else {},
                    }
                    for t in self.tools.values()
                ]}
            elif method == "tools/call":
                tool = self.tools[params["name"]]
                output = tool.handler(**params.get("arguments", {}))
                result = {"content": [{"type": "text", "text": json.dumps(output)}]}
            elif method == "resources/list":
                result = {"resources": [
                    {"uri": r.uri, "description": r.description} for r in self.resources.values()
                ]}
            elif method == "resources/read":
                res = self.resources[params["uri"]]
                result = {"contents": [{"uri": res.uri, "mimeType": "text/plain", "text": res.handler()}]}
            elif method == "prompts/list":
                result = {"prompts": [
                    {"name": p.name, "description": p.description, "arguments": [
                        {"name": a, "required": True} for a in p.arguments
                    ]}
                    for p in self.prompts.values()
                ]}
            elif method == "prompts/get":
                p = self.prompts[params["name"]]
                rendered = p.handler(**params.get("arguments", {}))
                result = {"messages": [{"role": "user", "content": {"type": "text", "text": rendered}}]}
            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"unknown method: {method}"}}
        except KeyError as e:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"missing key: {e}"}}

        return {"jsonrpc": "2.0", "id": request_id, "result": result}


class MCPClient:
    """In-memory client. Real clients read/write framed JSON over stdio or HTTP."""

    def __init__(self, server: MCPServer) -> None:
        self.server = server
        self._id = 0
        self.inbox: queue.SimpleQueue[dict[str, Any]] = queue.SimpleQueue()

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        message = {"jsonrpc": "2.0", "id": self._next_id(), "method": method, "params": params or {}}
        response = self.server.handle(message)
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response["result"]


# Build a demo server ------------------------------------------------------

server = MCPServer("demo-server")


@server.tool(
    name="add",
    description="Add two integers and return the sum.",
    schema={
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    },
)
def add(a: int, b: int) -> dict[str, int]:
    return {"sum": a + b}


@server.tool(
    name="delete_user",
    description="Delete a user by id. Mutating; requires approval.",
    schema={"type": "object", "properties": {"user_id": {"type": "integer"}}, "required": ["user_id"]},
    destructive=True,
)
def delete_user(user_id: int) -> dict[str, Any]:
    return {"deleted": user_id, "note": "simulated; real impl would hit DB"}


@server.resource("config://app", "Application config as JSON text.")
def app_config() -> str:
    return json.dumps({"env": "prod", "region": "us-east-1"})


@server.prompt("code_review", "Prompt the model to review code in a language.", ["language", "code"])
def code_review(language: str, code: str) -> str:
    return f"You are a senior {language} reviewer. Review for correctness and style:\n\n{code}"


# Drive it -----------------------------------------------------------------

def main() -> None:
    client = MCPClient(server)
    init = client.request("initialize", {"protocolVersion": PROTOCOL_VERSION, "clientInfo": {"name": "demo-client"}})
    print(f"Connected to {init['serverInfo']['name']} (protocol {init['protocolVersion']})")

    tools = client.request("tools/list")["tools"]
    print(f"\n{len(tools)} tool(s) discovered:")
    for t in tools:
        flag = " [destructive]" if t.get("annotations", {}).get("destructiveHint") else ""
        print(f"  - {t['name']}{flag}: {t['description']}")

    add_result = client.request("tools/call", {"name": "add", "arguments": {"a": 40, "b": 2}})
    print("\nCall add(40, 2) ->", add_result["content"][0]["text"])

    resources = client.request("resources/list")["resources"]
    print(f"\n{len(resources)} resource(s):")
    for r in resources:
        print(f"  - {r['uri']}: {r['description']}")

    config = client.request("resources/read", {"uri": "config://app"})
    print("\nRead config://app ->", config["contents"][0]["text"])

    prompt = client.request("prompts/get", {"name": "code_review", "arguments": {"language": "Python", "code": "x = 1\n"}})
    print("\nRender code_review prompt ->", prompt["messages"][0]["content"]["text"][:80], "...")


if __name__ == "__main__":
    main()
=======
"""Phase 11 Lesson 14: a stateless MCP server and in-process client.

Implements the 2026-07-28 request contract with per-request metadata,
server/discover, typed results, and the three server primitives. The transport
is in memory so the protocol remains visible and the demo stays stdlib-only.
Spec: https://modelcontextprotocol.io/specification/2026-07-28
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_VERSIONS = (PROTOCOL_VERSION,)
PROTOCOL_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]
    destructive: bool = False


@dataclass
class Resource:
    uri: str
    name: str
    description: str
    handler: Callable[[], str]


@dataclass
class Prompt:
    name: str
    description: str
    arguments: list[str]
    handler: Callable[..., str]


def request_metadata(
    *,
    client_name: str = "demo-client",
    client_version: str = "1.0.0",
    capabilities: dict[str, Any] | None = None,
    protocol_version: str = PROTOCOL_VERSION,
) -> dict[str, Any]:
    return {
        PROTOCOL_KEY: protocol_version,
        CLIENT_CAPABILITIES_KEY: capabilities or {},
        CLIENT_INFO_KEY: {"name": client_name, "version": client_version},
    }


class MCPServer:
    def __init__(self, name: str) -> None:
        self.name = name
        self.server_info = {"name": name, "version": "0.2.0"}
        self.tools: dict[str, Tool] = {}
        self.resources: dict[str, Resource] = {}
        self.prompts: dict[str, Prompt] = {}

    def tool(
        self,
        name: str,
        description: str,
        schema: dict[str, Any],
        *,
        destructive: bool = False,
    ):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = Tool(name, description, schema, fn, destructive)
            return fn

        return decorator

    def resource(self, uri: str, name: str, description: str):
        def decorator(fn: Callable[[], str]) -> Callable[[], str]:
            self.resources[uri] = Resource(uri, name, description, fn)
            return fn

        return decorator

    def prompt(self, name: str, description: str, arguments: list[str]):
        def decorator(fn: Callable[..., str]) -> Callable[..., str]:
            self.prompts[name] = Prompt(name, description, arguments, fn)
            return fn

        return decorator

    def _capabilities(self) -> dict[str, Any]:
        return {"tools": {}, "resources": {}, "prompts": {}}

    def _complete(self, payload: dict[str, Any], *, cacheable: bool = False) -> dict[str, Any]:
        result = {
            "resultType": "complete",
            **payload,
            "_meta": {SERVER_INFO_KEY: self.server_info},
        }
        if cacheable:
            result.update({"ttlMs": 30_000, "cacheScope": "private"})
        return result

    @staticmethod
    def _error(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    def _validate_metadata(self, params: dict[str, Any], request_id: Any) -> dict[str, Any] | None:
        metadata = params.get("_meta")
        if not isinstance(metadata, dict):
            return self._error(request_id, -32602, "params._meta is required")
        if PROTOCOL_KEY not in metadata:
            return self._error(request_id, -32602, f"{PROTOCOL_KEY} is required")
        version = metadata[PROTOCOL_KEY]
        if not isinstance(version, str):
            return self._error(request_id, -32602, f"{PROTOCOL_KEY} must be a string")
        if version not in SUPPORTED_VERSIONS:
            return self._error(
                request_id,
                -32022,
                "Unsupported protocol version",
                {"supported": list(SUPPORTED_VERSIONS), "requested": version},
            )
        if not isinstance(metadata.get(CLIENT_CAPABILITIES_KEY), dict):
            return self._error(request_id, -32602, "clientCapabilities must be an object")
        client_info = metadata.get(CLIENT_INFO_KEY)
        if client_info is not None and (
            not isinstance(client_info, dict)
            or not isinstance(client_info.get("name"), str)
            or not isinstance(client_info.get("version"), str)
        ):
            return self._error(request_id, -32602, "clientInfo must contain name and version")
        return None

    def handle(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return self._error(None, -32600, "request must be an object")

        request_id = message.get("id")
        if "id" not in message:
            return None
        if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            error_id = request_id if type(request_id) in (str, int) else None
            return self._error(error_id, -32600, "invalid JSON-RPC request")
        if type(request_id) not in (str, int):
            return self._error(None, -32600, "id must be a string or integer")

        method = message["method"]
        params = message.get("params", {})
        if not isinstance(params, dict):
            return self._error(request_id, -32602, "params must be an object")

        metadata_error = self._validate_metadata(params, request_id)
        if metadata_error:
            return metadata_error

        if method == "server/discover":
            result = self._complete(
                {
                    "supportedVersions": list(SUPPORTED_VERSIONS),
                    "capabilities": self._capabilities(),
                    "instructions": "Use add for arithmetic and request approval before delete_user.",
                },
                cacheable=True,
            )
        elif method == "tools/list":
            result = self._complete(
                {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.input_schema,
                            "annotations": (
                                {"destructiveHint": True} if tool.destructive else {}
                            ),
                        }
                        for tool in sorted(self.tools.values(), key=lambda item: item.name)
                    ]
                },
                cacheable=True,
            )
        elif method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in self.tools:
                return self._error(request_id, -32602, "missing or unknown tool name")
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                return self._error(request_id, -32602, "arguments must be an object")
            tool = self.tools[name]
            try:
                output = json.dumps(tool.handler(**arguments))
            except Exception:
                return self._error(request_id, -32603, "tool handler failed")
            result = self._complete(
                {"content": [{"type": "text", "text": output}], "isError": False}
            )
        elif method == "resources/list":
            result = self._complete(
                {
                    "resources": [
                        {
                            "uri": item.uri,
                            "name": item.name,
                            "description": item.description,
                        }
                        for item in sorted(self.resources.values(), key=lambda item: item.uri)
                    ]
                },
                cacheable=True,
            )
        elif method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str) or uri not in self.resources:
                return self._error(request_id, -32602, "missing or unknown resource URI")
            resource = self.resources[uri]
            try:
                text = resource.handler()
                if not isinstance(text, str):
                    raise TypeError("resource handler must return text")
            except Exception:
                return self._error(request_id, -32603, "resource handler failed")
            result = self._complete(
                {
                    "contents": [
                        {
                            "uri": resource.uri,
                            "mimeType": "text/plain",
                            "text": text,
                        }
                    ]
                },
                cacheable=True,
            )
        elif method == "prompts/list":
            result = self._complete(
                {
                    "prompts": [
                        {
                            "name": item.name,
                            "description": item.description,
                            "arguments": [
                                {"name": argument, "required": True}
                                for argument in item.arguments
                            ],
                        }
                        for item in sorted(self.prompts.values(), key=lambda item: item.name)
                    ]
                },
                cacheable=True,
            )
        elif method == "prompts/get":
            name = params.get("name")
            if not isinstance(name, str) or name not in self.prompts:
                return self._error(request_id, -32602, "missing or unknown prompt name")
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                return self._error(request_id, -32602, "arguments must be an object")
            prompt = self.prompts[name]
            try:
                rendered = prompt.handler(**arguments)
                if not isinstance(rendered, str):
                    raise TypeError("prompt handler must return text")
            except Exception:
                return self._error(request_id, -32603, "prompt handler failed")
            result = self._complete(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": rendered},
                        }
                    ]
                }
            )
        else:
            return self._error(request_id, -32601, f"unknown method: {method}")

        return {"jsonrpc": "2.0", "id": request_id, "result": result}


class MCPClient:
    def __init__(self, server: MCPServer) -> None:
        self.server = server
        self._id = 0

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._id += 1
        request_params = dict(params or {})
        request_params["_meta"] = request_metadata()
        response = self.server.handle(
            {"jsonrpc": "2.0", "id": self._id, "method": method, "params": request_params}
        )
        if response is None:
            raise RuntimeError("request did not receive a response")
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response["result"]


server = MCPServer("demo-server")


@server.tool(
    "add",
    "Add two integers and return the sum.",
    {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    },
)
def add(a: int, b: int) -> dict[str, int]:
    return {"sum": a + b}


@server.tool(
    "delete_user",
    "Delete a user by id. Mutating; requires approval.",
    {
        "type": "object",
        "properties": {"user_id": {"type": "integer"}},
        "required": ["user_id"],
    },
    destructive=True,
)
def delete_user(user_id: int) -> dict[str, Any]:
    return {"deleted": user_id, "note": "simulated"}


@server.resource("config://app", "app-config", "Application config as JSON text.")
def app_config() -> str:
    return json.dumps({"env": "prod", "region": "us-east-1"})


@server.prompt("code_review", "Review code in a language.", ["language", "code"])
def code_review(language: str, code: str) -> str:
    return f"You are a senior {language} reviewer. Review for correctness and style:\n\n{code}"


def main() -> None:
    client = MCPClient(server)
    discovery = client.request("server/discover")
    info = discovery["_meta"][SERVER_INFO_KEY]
    print(f"Discovered {info['name']} (protocol {discovery['supportedVersions'][0]})")

    tools = client.request("tools/list")["tools"]
    print(f"\n{len(tools)} tool(s) discovered:")
    for tool in tools:
        flag = " [destructive]" if tool.get("annotations", {}).get("destructiveHint") else ""
        print(f"  - {tool['name']}{flag}: {tool['description']}")

    add_result = client.request("tools/call", {"name": "add", "arguments": {"a": 40, "b": 2}})
    print("\nCall add(40, 2) ->", add_result["content"][0]["text"])

    resources = client.request("resources/list")["resources"]
    print(f"\n{len(resources)} resource(s): {resources[0]['uri']}")
    config = client.request("resources/read", {"uri": "config://app"})
    print("Read config://app ->", config["contents"][0]["text"])

    prompt = client.request(
        "prompts/get",
        {"name": "code_review", "arguments": {"language": "Python", "code": "x = 1\n"}},
    )
    print("\nRender code_review prompt ->", prompt["messages"][0]["content"]["text"][:80])


if __name__ == "__main__":
    main()
>>>>>>> main
