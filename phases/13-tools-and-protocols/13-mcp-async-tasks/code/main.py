<<<<<<< HEAD
"""Phase 13 Lesson 13 - MCP async Tasks (SEP-1686) with durable state.

Simulates a long-running generate_report tool:
  - tools/call with _meta.task.required returns immediately with taskId
  - worker thread updates progress in a filesystem-backed task store
  - tasks/status polls progress
  - tasks/result returns the final payload
  - tasks/cancel signals the worker to stop
  - crash recovery marks in-flight tasks as failed on reload

Stdlib only.

Run: python code/main.py
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path


STORE_DIR = Path("/tmp/lesson-13-tasks")
STORE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Task:
    id: str
    state: str = "working"
    progress: float = 0.0
    total_ms: int = 0
    result: dict | None = None
    error: str | None = None
    ttl_ms: int = 900_000
    created_at: float = field(default_factory=time.time)
    cancel_requested: bool = False

    def persist(self) -> None:
        (STORE_DIR / f"{self.id}.json").write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, tid: str) -> "Task | None":
        p = STORE_DIR / f"{tid}.json"
        if not p.exists():
            return None
        data = json.loads(p.read_text())
        return cls(**data)


class TaskStore:
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.crash_recover()

    def crash_recover(self) -> None:
        for p in STORE_DIR.glob("*.json"):
            t = Task.load(p.stem)
            if t is None:
                continue
            if t.state == "working":
                t.state = "failed"
                t.error = "CRASH_RECOVERY"
                t.persist()
            self.tasks[t.id] = t

    def create(self, total_ms: int) -> Task:
        t = Task(id=f"tsk_{uuid.uuid4().hex[:12]}", total_ms=total_ms)
        t.persist()
        self.tasks[t.id] = t
        return t

    def update(self, tid: str, **changes) -> None:
        t = self.tasks[tid]
        for k, v in changes.items():
            setattr(t, k, v)
        t.persist()


STORE = TaskStore()


def worker_generate_report(task: Task, size: str) -> None:
    """Simulated 3-second report generation."""
    try:
        for step in range(30):
            if task.cancel_requested:
                STORE.update(task.id, state="cancelled")
                return
            time.sleep(0.1)
            STORE.update(task.id, progress=(step + 1) / 30)
        STORE.update(task.id, state="completed",
                     result={"content": [{"type": "text",
                                          "text": f"Report size={size} with 30 sections"}],
                             "isError": False})
    except Exception as e:
        STORE.update(task.id, state="failed", error=str(e))


def tools_call(name: str, args: dict, meta: dict | None = None) -> dict:
    if name != "generate_report":
        return {"isError": True,
                "content": [{"type": "text", "text": f"unknown tool {name}"}]}
    task_required = meta and meta.get("task", {}).get("required", False)
    if not task_required:
        # synchronous fallback path (could also be forbidden by the server)
        time.sleep(3.0)
        return {"isError": False,
                "content": [{"type": "text", "text": "Report generated synchronously"}]}
    task = STORE.create(total_ms=3000)
    threading.Thread(target=worker_generate_report,
                     args=(task, args.get("size", "medium")), daemon=True).start()
    return {"_meta": {"task": {"id": task.id, "state": task.state, "ttl": task.ttl_ms}}}


def tasks_status(tid: str) -> dict:
    t = STORE.tasks.get(tid)
    if not t:
        return {"error": "not found"}
    return {"taskId": tid, "state": t.state, "progress": round(t.progress, 2)}


def tasks_result(tid: str) -> dict:
    t = STORE.tasks.get(tid)
    if not t:
        return {"error": "not found"}
    if t.state != "completed":
        return {"error": f"not ready; state={t.state}"}
    return t.result or {}


def tasks_cancel(tid: str) -> dict:
    t = STORE.tasks.get(tid)
    if not t or t.state in {"completed", "failed", "cancelled"}:
        return {"taskId": tid, "state": t.state if t else "unknown"}
    STORE.update(tid, cancel_requested=True)
    return {"taskId": tid, "state": "cancelling"}


def demo() -> None:
    print("=" * 72)
    print("PHASE 13 LESSON 13 - MCP ASYNC TASKS (SEP-1686)")
    print("=" * 72)

    print("\n--- kick off generate_report as task ---")
    resp = tools_call("generate_report", {"size": "large"},
                      meta={"task": {"required": True}})
    tid = resp["_meta"]["task"]["id"]
    print(f"  task id: {tid}  state: {resp['_meta']['task']['state']}  "
          f"ttl: {resp['_meta']['task']['ttl']} ms")

    print("\n--- poll status until terminal ---")
    while True:
        status = tasks_status(tid)
        print(f"  state={status['state']:10s}  progress={status['progress']:.2f}")
        if status["state"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(0.5)

    print("\n--- fetch result ---")
    result = tasks_result(tid)
    print(f"  result: {result['content'][0]['text']}")

    print("\n--- cancellation demo ---")
    resp = tools_call("generate_report", {"size": "small"},
                      meta={"task": {"required": True}})
    tid2 = resp["_meta"]["task"]["id"]
    print(f"  spawned task {tid2}")
    time.sleep(0.4)
    cancel = tasks_cancel(tid2)
    print(f"  cancel request: {cancel}")
    while True:
        status = tasks_status(tid2)
        if status["state"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(0.3)
    print(f"  final state: {status}")

    print("\n--- crash recovery simulation ---")
    # write a fake task that claims to be working but has no worker
    fake = STORE.create(total_ms=1000)
    del STORE.tasks[fake.id]  # pretend process died
    # reload from disk
    store2 = TaskStore()
    recovered = store2.tasks.get(fake.id)
    print(f"  reloaded {fake.id} -> state={recovered.state}  error={recovered.error}")


if __name__ == "__main__":
    demo()
=======
"""Phase 13 Lesson 13: the stateless MCP Tasks extension.

Lesson: ../docs/zh.md
Extension: https://tasks.extensions.modelcontextprotocol.io/specification/draft/tasks
This example uses only Python's standard library.
Run: python3 main.py
"""

from __future__ import annotations

import json
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "2026-07-28"
PROTOCOL_META = "io.modelcontextprotocol/protocolVersion"
CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_META = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"
SUBSCRIPTION_ID_META = "io.modelcontextprotocol/subscriptionId"
TASKS_EXTENSION = "io.modelcontextprotocol/tasks"
TERMINAL_STATUSES = {"completed", "cancelled", "failed"}
TOOLS = [
    {
        "name": "generate_report",
        "description": "Generate a durable report that may require outline approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "enum": ["small", "medium", "large"],
                    "default": "medium",
                }
            },
            "required": [],
        },
    }
]


@dataclass
class McpError(Exception):
    code: int
    message: str
    data: dict[str, Any] | None = None


def request_meta(*, tasks: bool = True) -> dict[str, Any]:
    extensions = {TASKS_EXTENSION: {}} if tasks else {}
    return {
        PROTOCOL_META: PROTOCOL_VERSION,
        CAPABILITIES_META: {"extensions": extensions},
        CLIENT_INFO_META: {"name": "lesson-client", "version": "1.0.0"},
    }


def _server_meta() -> dict[str, Any]:
    return {SERVER_INFO_META: {"name": "tasks-demo", "version": "1.0.0"}}


def complete(**fields: Any) -> dict[str, Any]:
    return {"resultType": "complete", **fields, "_meta": _server_meta()}


def validate_request_meta(params: dict[str, Any]) -> dict[str, Any]:
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        raise McpError(-32602, "missing request _meta")
    requested_version = meta.get(PROTOCOL_META)
    if not isinstance(requested_version, str):
        raise McpError(-32602, "missing protocol version")
    if requested_version != PROTOCOL_VERSION:
        raise McpError(
            -32022,
            "unsupported protocol version",
            {"supported": [PROTOCOL_VERSION], "requested": requested_version},
        )
    capabilities = meta.get(CAPABILITIES_META)
    if not isinstance(capabilities, dict):
        raise McpError(-32602, "missing client capabilities")
    return meta


def require_tasks_extension(meta: dict[str, Any]) -> None:
    extensions = meta[CAPABILITIES_META].get("extensions")
    if not isinstance(extensions, dict) or TASKS_EXTENSION not in extensions:
        raise McpError(
            -32021,
            "missing required client capability",
            {"requiredCapabilities": {"extensions": {TASKS_EXTENSION: {}}}},
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


@dataclass
class Task:
    task_id: str
    owner: str
    operation: str
    status: str
    status_message: str
    created_at: str
    last_updated_at: str
    ttl_ms: int | None
    poll_interval_ms: int = 1_000
    stage: int = 0
    size: str = "medium"
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    input_requests: dict[str, Any] = field(default_factory=dict)
    issued_keys: list[str] = field(default_factory=list)

    def to_wire(self) -> dict[str, Any]:
        wire: dict[str, Any] = {
            "taskId": self.task_id,
            "status": self.status,
            "statusMessage": self.status_message,
            "createdAt": self.created_at,
            "lastUpdatedAt": self.last_updated_at,
            "ttlMs": self.ttl_ms,
            "pollIntervalMs": self.poll_interval_ms,
        }
        if self.status == "input_required":
            wire["inputRequests"] = self.input_requests
        elif self.status == "completed":
            wire["result"] = self.result
        elif self.status == "failed":
            wire["error"] = self.error
        return wire


class TaskStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.tasks: dict[str, Task] = {}
        self.reload()

    def reload(self) -> None:
        self.tasks = {}
        for path in sorted(self.directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            task = Task(**data)
            self.tasks[task.task_id] = task

    def persist(self, task: Task) -> None:
        path = self.directory / f"{task.task_id}.json"
        temporary = self.directory / f"{task.task_id}.tmp"
        temporary.write_text(
            json.dumps(asdict(task), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)
        self.tasks[task.task_id] = task

    def create(self, *, size: str, owner: str) -> Task:
        timestamp = utc_now()
        task = Task(
            task_id=f"tsk_{uuid.uuid4().hex[:12]}",
            owner=owner,
            operation="tools/call:generate_report",
            status="working",
            status_message="Preparing report outline.",
            created_at=timestamp,
            last_updated_at=timestamp,
            ttl_ms=900_000,
            size=size,
        )
        self.persist(task)
        return task

    def get(self, task_id: Any) -> Task:
        if not isinstance(task_id, str) or task_id not in self.tasks:
            raise McpError(-32602, "task not found")
        return self.tasks[task_id]

    def save(self, task: Task) -> None:
        task.last_updated_at = utc_now()
        self.persist(task)


class TaskService:
    def __init__(self, directory: Path) -> None:
        self.store = TaskStore(directory)

    def server_discover(self, params: dict[str, Any]) -> dict[str, Any]:
        validate_request_meta(params)
        return complete(
            supportedVersions=[PROTOCOL_VERSION],
            capabilities={
                "tools": {},
                "extensions": {TASKS_EXTENSION: {}},
            },
            ttlMs=300_000,
            cacheScope="public",
        )

    def tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        validate_request_meta(params)
        return complete(
            tools=sorted(TOOLS, key=lambda tool: tool["name"]),
            ttlMs=60_000,
            cacheScope="public",
        )

    def _owned_task(self, task_id: Any, *, principal: str) -> Task:
        task = self.store.get(task_id)
        if task.owner != principal:
            raise McpError(-32602, "task not found")
        return task

    def tools_call(self, params: dict[str, Any], *, principal: str) -> dict[str, Any]:
        meta = validate_request_meta(params)
        require_tasks_extension(meta)
        if params.get("name") != "generate_report":
            raise McpError(-32602, "unknown tool")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            raise McpError(-32602, "arguments must be an object")
        size = arguments.get("size", "medium")
        if size not in {"small", "medium", "large"}:
            raise McpError(-32602, "size must be small, medium, or large")

        task = self.store.create(size=size, owner=principal)
        return {"resultType": "task", **task.to_wire(), "_meta": _server_meta()}

    def tasks_get(self, params: dict[str, Any], *, principal: str) -> dict[str, Any]:
        meta = validate_request_meta(params)
        require_tasks_extension(meta)
        task = self._owned_task(params.get("taskId"), principal=principal)
        return complete(**task.to_wire())

    def tasks_update(self, params: dict[str, Any], *, principal: str) -> dict[str, Any]:
        meta = validate_request_meta(params)
        require_tasks_extension(meta)
        task = self._owned_task(params.get("taskId"), principal=principal)
        responses = params.get("inputResponses")
        if not isinstance(responses, dict):
            raise McpError(-32602, "inputResponses must be an object")

        if task.status == "input_required":
            answer = responses.get("approve_outline")
            if isinstance(answer, dict):
                action = answer.get("action")
                if action in {"decline", "cancel"}:
                    task.status = "cancelled"
                    task.status_message = "User did not approve the outline."
                    task.input_requests = {}
                    self.store.save(task)
                elif action == "accept" and isinstance(answer.get("content"), dict):
                    if answer["content"].get("approved") is True:
                        task.status = "working"
                        task.status_message = "Generating approved report."
                        task.stage = 2
                        task.input_requests = {}
                        self.store.save(task)
        return complete()

    def tasks_cancel(self, params: dict[str, Any], *, principal: str) -> dict[str, Any]:
        meta = validate_request_meta(params)
        require_tasks_extension(meta)
        task = self._owned_task(params.get("taskId"), principal=principal)
        if task.status not in TERMINAL_STATUSES:
            task.status = "cancelled"
            task.status_message = "Cancellation was acknowledged by the worker."
            task.input_requests = {}
            self.store.save(task)
        return complete()

    def advance_worker(self, task_id: str) -> Task:
        task = self.store.get(task_id)
        if task.status != "working":
            return task
        if task.stage == 0:
            key = "approve_outline"
            if key in task.issued_keys:
                raise RuntimeError("task input request key cannot be reused")
            task.issued_keys.append(key)
            task.input_requests = {
                key: {
                    "method": "elicitation/create",
                    "params": {
                        "mode": "form",
                        "message": "Approve the generated report outline?",
                        "requestedSchema": {
                            "type": "object",
                            "properties": {"approved": {"type": "boolean"}},
                            "required": ["approved"],
                        },
                    },
                }
            }
            task.status = "input_required"
            task.status_message = "Waiting for outline approval."
            task.stage = 1
        elif task.stage == 2:
            task.status = "completed"
            task.status_message = "Report completed."
            task.stage = 3
            task.result = complete(
                content=[
                    {
                        "type": "text",
                        "text": f"Generated {task.size} report with approved outline.",
                    }
                ],
                structuredContent={"size": task.size, "approved": True},
                isError=False,
            )
        self.store.save(task)
        return task

    def subscription_acknowledgement(
        self,
        task_ids: list[str],
        *,
        subscription_id: int | str,
        principal: str = "user-42",
    ) -> dict[str, Any]:
        accepted = [
            task_id
            for task_id in task_ids
            if task_id in self.store.tasks
            and self.store.tasks[task_id].owner == principal
        ]
        return {
            "jsonrpc": "2.0",
            "method": "notifications/subscriptions/acknowledged",
            "params": {
                "notifications": {"taskIds": accepted},
                "_meta": {SUBSCRIPTION_ID_META: subscription_id},
            },
        }

    def task_notification(
        self,
        task_id: str,
        *,
        subscription_id: int | str,
        principal: str = "user-42",
    ) -> dict[str, Any]:
        task = self._owned_task(task_id, principal=principal)
        return {
            "jsonrpc": "2.0",
            "method": "notifications/tasks",
            "params": {
                **task.to_wire(),
                "_meta": {SUBSCRIPTION_ID_META: subscription_id},
            },
        }

    def dispatch(
        self,
        request: dict[str, Any],
        *,
        principal: str = "user-42",
    ) -> dict[str, Any] | None:
        is_notification = "id" not in request
        request_id = request.get("id")
        try:
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise McpError(-32602, "params must be an object")
            method = request.get("method")
            if method == "server/discover":
                result = self.server_discover(params)
            elif method == "tools/list":
                result = self.tools_list(params)
            elif method == "tools/call":
                result = self.tools_call(params, principal=principal)
            elif method == "tasks/get":
                result = self.tasks_get(params, principal=principal)
            elif method == "tasks/update":
                result = self.tasks_update(params, principal=principal)
            elif method == "tasks/cancel":
                result = self.tasks_cancel(params, principal=principal)
            else:
                raise McpError(-32601, "method not found")
            if is_notification:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except McpError as exc:
            if is_notification:
                return None
            error: dict[str, Any] = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            return {"jsonrpc": "2.0", "id": request_id, "error": error}


def make_request(
    request_id: int,
    method: str,
    params: dict[str, Any],
    *,
    tasks: bool = True,
) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {**params, "_meta": request_meta(tasks=tasks)},
    }


def make_http_request(
    request_id: int,
    method: str,
    params: dict[str, Any],
    *,
    tasks: bool = True,
) -> tuple[dict[str, Any], dict[str, str]]:
    body = make_request(request_id, method, params, tasks=tasks)
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
        "Mcp-Method": method,
    }
    name: Any = None
    if method == "tools/call":
        name = body["params"].get("name")
    elif method in {"tasks/get", "tasks/update", "tasks/cancel"}:
        name = body["params"].get("taskId")
    if method == "tools/call" or method in {"tasks/get", "tasks/update", "tasks/cancel"}:
        if not isinstance(name, str) or not name:
            raise ValueError(f"{method} requires a name for Mcp-Name")
        headers["Mcp-Name"] = name
    return body, headers


def run_demo(directory: Path) -> tuple[TaskService, list[dict[str, Any]]]:
    service = TaskService(directory)
    transcript: list[dict[str, Any]] = []
    transcript.append(
        service.dispatch(
            make_request(0, "server/discover", {})
        )
    )
    created = service.dispatch(
        make_request(
            1,
            "tools/call",
            {"name": "generate_report", "arguments": {"size": "large"}},
        )
    )
    transcript.append(created)
    task_id = created["result"]["taskId"]

    service = TaskService(directory)
    transcript.append(
        service.dispatch(make_request(2, "tasks/get", {"taskId": task_id}))
    )
    service.advance_worker(task_id)
    needs_input = service.dispatch(
        make_request(3, "tasks/get", {"taskId": task_id})
    )
    transcript.append(needs_input)
    transcript.append(
        service.dispatch(
            make_request(
                4,
                "tasks/update",
                {
                    "taskId": task_id,
                    "inputResponses": {
                        "approve_outline": {
                            "action": "accept",
                            "content": {"approved": True},
                        }
                    },
                },
            )
        )
    )
    service.advance_worker(task_id)
    transcript.append(
        service.dispatch(make_request(5, "tasks/get", {"taskId": task_id}))
    )
    return service, transcript


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="lesson-13-tasks-") as directory:
        service, transcript = run_demo(Path(directory))
        for response in transcript:
            result = response["result"]
            print(
                f"id={response['id']} resultType={result['resultType']} "
                f"status={result.get('status', 'ack')}"
            )
        task_id = transcript[1]["result"]["taskId"]
        print(
            "notification:",
            json.dumps(
                service.task_notification(task_id, subscription_id="listen-demo"),
                indent=2,
            ),
        )


if __name__ == "__main__":
    main()
>>>>>>> main
