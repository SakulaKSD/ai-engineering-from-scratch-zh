<<<<<<< HEAD
// Phase 13 Lesson 07 — toy MCP server, in TypeScript, stdlib only.
//
// Implements the 2025-11-25 spec's core flow:
//   initialize, tools/list, tools/call, resources/list, resources/read,
//   prompts/list, prompts/get, plus notifications/initialized.
//
// Spec references:
//   MCP 2025-11-25       https://modelcontextprotocol.io/specification/2025-11-25
//   JSON-RPC 2.0         https://www.jsonrpc.org/specification
//
// Not a production server: no auth, no Streamable HTTP transport (Lesson 09),
// no subscriptions. But the wire shape is spec-shaped; any MCP client can
// handshake and call the three notes tools.
//
// Run demo:        npx tsx code/main.ts --demo
// Pipe JSON-RPC:   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | npx tsx code/main.ts

import { randomUUID } from "node:crypto";
import { createInterface } from "node:readline";

const PROTOCOL_VERSION = "2025-11-25";
const SERVER_INFO = { name: "notes-lesson-07", version: "1.0.0" };

type Note = { title: string; body: string; tag: string };

const NOTES: Record<string, Note> = {
  "note-1": { title: "MCP overview", body: "Primitives, lifecycle, JSON-RPC.", tag: "mcp" },
  "note-2": { title: "Function calling", body: "Provider shapes diff by envelope.", tag: "api" },
  "note-3": { title: "Tool schemas", body: "Atomic beats monolithic.", tag: "design" },
};

type JsonSchema = {
  type?: string;
  properties?: Record<string, JsonSchema>;
  required?: string[];
  minimum?: number;
  maximum?: number;
};

type ToolDescriptor = {
  name: string;
  description: string;
  inputSchema: JsonSchema;
  annotations?: { readOnlyHint?: boolean; idempotentHint?: boolean; destructiveHint?: boolean };
};

const TOOLS: ToolDescriptor[] = [
  {
    name: "notes_list",
    description:
      "Use when the user wants all notes or a filtered list by tag. Do not use to read a note body.",
    inputSchema: {
      type: "object",
      properties: { tag: { type: "string" } },
      required: [],
    },
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  {
    name: "notes_search",
    description:
      "Use when the user searches notes by content keywords. Do not use for tag filters.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        limit: { type: "integer", minimum: 1, maximum: 50 },
      },
      required: ["query"],
    },
    annotations: { readOnlyHint: true },
  },
  {
    name: "notes_create",
    description: "Use when the user writes a new note. Do not use to edit existing ones.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        body: { type: "string" },
        tag: { type: "string" },
      },
      required: ["title", "body"],
    },
    annotations: { destructiveHint: false, idempotentHint: false },
  },
];

const PROMPTS = [
  {
    name: "review_note",
    description: "Produce a critique of a note with concrete improvements.",
    arguments: [
      { name: "note_id", description: "The id of the note to review", required: true },
    ],
  },
];

type ContentBlock =
  | { type: "text"; text: string }
  | { type: "resource"; resource: { uri: string; text: string } };

type ToolArgs = Record<string, unknown>;

function execNotesList(args: ToolArgs): ContentBlock[] {
  const tag = args.tag as string | undefined;
  const items: Array<{ id: string; title: string; tag: string }> = [];
  for (const [id, note] of Object.entries(NOTES)) {
    if (tag && note.tag !== tag) continue;
    items.push({ id, title: note.title, tag: note.tag });
  }
  return [{ type: "text", text: JSON.stringify(items) }];
}

function execNotesSearch(args: ToolArgs): ContentBlock[] {
  const q = String(args.query).toLowerCase();
  const limit = (args.limit as number | undefined) ?? 10;
  const hits: Array<{ id: string; title: string }> = [];
  for (const [id, n] of Object.entries(NOTES)) {
    if (n.title.toLowerCase().includes(q) || n.body.toLowerCase().includes(q)) {
      hits.push({ id, title: n.title });
    }
  }
  return [{ type: "text", text: JSON.stringify(hits.slice(0, limit)) }];
}

function execNotesCreate(args: ToolArgs): ContentBlock[] {
  const id = `note-${randomUUID().replace(/-/g, "").slice(0, 6)}`;
  const body = String(args.body);
  NOTES[id] = {
    title: String(args.title),
    body,
    tag: (args.tag as string | undefined) ?? "",
  };
  return [
    { type: "text", text: `Created ${id}` },
    { type: "resource", resource: { uri: `notes://${id}`, text: body } },
  ];
}

const TOOL_EXECUTORS: Record<string, (args: ToolArgs) => ContentBlock[]> = {
  notes_list: execNotesList,
  notes_search: execNotesSearch,
  notes_create: execNotesCreate,
};

type JsonRpcRequest = {
  jsonrpc: "2.0";
  id?: number | string | null;
  method: string;
  params?: Record<string, unknown>;
};

type JsonRpcResponse = {
  jsonrpc: "2.0";
  id: number | string | null;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
};

function handleInitialize(): unknown {
  return {
    protocolVersion: PROTOCOL_VERSION,
    capabilities: {
      tools: { listChanged: false },
      resources: { listChanged: false, subscribe: false },
      prompts: { listChanged: false },
    },
    serverInfo: SERVER_INFO,
  };
}

function handleToolsList(): unknown {
  return { tools: TOOLS };
}

function handleToolsCall(params: Record<string, unknown>): unknown {
  const name = params.name as string;
  const args = (params.arguments as ToolArgs | undefined) ?? {};
  const exec = TOOL_EXECUTORS[name];
  if (!exec) {
    return { content: [{ type: "text", text: `unknown tool ${name}` }], isError: true };
  }
  try {
    return { content: exec(args), isError: false };
  } catch (err) {
    return { content: [{ type: "text", text: String(err) }], isError: true };
  }
}

function handleResourcesList(): unknown {
  const items = Object.entries(NOTES).map(([id, n]) => ({
    uri: `notes://${id}`,
    name: n.title,
    mimeType: "text/markdown",
  }));
  return { resources: items };
}

function handleResourcesRead(params: Record<string, unknown>): unknown {
  const uri = String(params.uri);
  const id = uri.replace("notes://", "");
  const n = NOTES[id];
  if (!n) throw new Error(`not found: ${uri}`);
  return {
    contents: [
      {
        uri,
        mimeType: "text/markdown",
        text: `# ${n.title}\n\n${n.body}\n\ntag: ${n.tag}`,
      },
    ],
  };
}

function handlePromptsList(): unknown {
  return { prompts: PROMPTS };
}

function handlePromptsGet(params: Record<string, unknown>): unknown {
  if (params.name !== "review_note") throw new Error("unknown prompt");
  const args = (params.arguments as Record<string, unknown> | undefined) ?? {};
  const id = String(args.note_id ?? "");
  const body = NOTES[id]?.body ?? "(not found)";
  return {
    description: "Review the note and propose concrete improvements.",
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Review this note and propose improvements:\n\n${body}`,
        },
      },
    ],
  };
}

const HANDLERS: Record<string, (params: Record<string, unknown>) => unknown> = {
  initialize: handleInitialize,
  "tools/list": handleToolsList,
  "tools/call": handleToolsCall,
  "resources/list": handleResourcesList,
  "resources/read": handleResourcesRead,
  "prompts/list": handlePromptsList,
  "prompts/get": handlePromptsGet,
};

function dispatch(msg: JsonRpcRequest): JsonRpcResponse | null {
  const method = msg.method;
  if (msg.id === undefined) return null;
  const id = msg.id;
  const handler = HANDLERS[method];
  if (!handler) {
    return {
      jsonrpc: "2.0",
      id,
      error: { code: -32601, message: `Method not found: ${method}` },
    };
  }
  try {
    const result = handler(msg.params ?? {});
    return { jsonrpc: "2.0", id, result };
  } catch (err) {
    return {
      jsonrpc: "2.0",
      id,
      error: { code: -32603, message: String(err) },
    };
  }
}

function serveStdio(): void {
  const rl = createInterface({ input: process.stdin, terminal: false });
  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    let msg: JsonRpcRequest;
    try {
      msg = JSON.parse(trimmed) as JsonRpcRequest;
    } catch (err) {
      process.stderr.write(`parse error: ${String(err)}\n`);
      process.stdout.write(
        JSON.stringify({
          jsonrpc: "2.0",
          id: null,
          error: { code: -32700, message: "Parse error", data: String(err) },
        }) + "\n",
      );
      return;
    }
    const resp = dispatch(msg);
    if (resp) process.stdout.write(JSON.stringify(resp) + "\n");
  });
}

function demo(): void {
  console.log("=".repeat(72));
  console.log("PHASE 13 LESSON 07 - MCP SERVER DEMO (TypeScript port, no transport)");
  console.log("=".repeat(72));

  const scenarios: JsonRpcRequest[] = [
    { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: PROTOCOL_VERSION } },
    { jsonrpc: "2.0", id: 2, method: "tools/list" },
    {
      jsonrpc: "2.0",
      id: 3,
      method: "tools/call",
      params: { name: "notes_search", arguments: { query: "MCP" } },
    },
    { jsonrpc: "2.0", id: 4, method: "resources/list" },
    {
      jsonrpc: "2.0",
      id: 5,
      method: "resources/read",
      params: { uri: "notes://note-1" },
    },
    {
      jsonrpc: "2.0",
      id: 6,
      method: "tools/call",
      params: {
        name: "notes_create",
        arguments: { title: "Session notes", body: "Built it.", tag: "mcp" },
      },
    },
    {
      jsonrpc: "2.0",
      id: 7,
      method: "prompts/get",
      params: { name: "review_note", arguments: { note_id: "note-1" } },
    },
    {
      jsonrpc: "2.0",
      id: 8,
      method: "tools/call",
      params: { name: "no_such_tool", arguments: {} },
    },
  ];

  for (const msg of scenarios) {
    console.log("\n>>>", msg.method);
    const resp = dispatch(msg);
    console.log(JSON.stringify(resp, null, 2).slice(0, 400));
  }
}

function main(): void {
  if (process.argv.includes("--demo")) {
    demo();
  } else {
    serveStdio();
  }
}

main();
=======
// Phase 13 Lesson 07: a stateless MCP server over stdio.
// Lesson: phases/13-tools-and-protocols/07-building-an-mcp-server/docs/zh.md
// Specification: https://modelcontextprotocol.io/specification/2026-07-28/
// Implements discovery, three server primitives, and per-request validation.
// Run: npx tsx main.ts --demo

import { randomUUID } from "node:crypto";
import { createInterface } from "node:readline";

const PROTOCOL_VERSION = "2026-07-28";
const SUPPORTED_VERSIONS = [PROTOCOL_VERSION];
const VERSION_KEY = "io.modelcontextprotocol/protocolVersion";
const CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities";
const CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo";
const SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo";

const CLIENT_INFO = { name: "lesson-07-client", version: "1.0.0" };
const SERVER_INFO = { name: "notes-lesson-07", version: "2.0.0" };
const SERVER_CAPABILITIES = {
  tools: { listChanged: false },
  resources: { listChanged: false, subscribe: false },
  prompts: { listChanged: false },
};

type JsonObject = Record<string, any>;
type Note = { title: string; body: string; tag: string };
type JsonRpcRequest = {
  jsonrpc: "2.0";
  id?: number | string;
  method: string;
  params?: JsonObject;
};
type JsonRpcResponse = {
  jsonrpc: "2.0";
  id: number | string | null;
  result?: JsonObject;
  error?: { code: number; message: string; data?: unknown };
};

const NOTES: Record<string, Note> = {
  "note-1": { title: "MCP overview", body: "Stateless requests and JSON-RPC.", tag: "mcp" },
  "note-2": { title: "Function calling", body: "Provider envelopes differ.", tag: "api" },
  "note-3": { title: "Tool schemas", body: "Atomic tools are easier to route.", tag: "design" },
};

const TOOLS: JsonObject[] = [
  {
    name: "notes_search",
    description: "Search note titles and bodies by keyword.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        limit: { type: "integer", minimum: 1, maximum: 50 },
      },
      required: ["query"],
    },
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  {
    name: "notes_create",
    description: "Create a new note.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        body: { type: "string" },
        tag: { type: "string" },
      },
      required: ["title", "body"],
    },
    annotations: { destructiveHint: false, idempotentHint: false },
  },
  {
    name: "notes_list",
    description: "List notes, optionally filtered by tag.",
    inputSchema: {
      type: "object",
      properties: { tag: { type: "string" } },
      required: [],
    },
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
];

const PROMPTS: JsonObject[] = [
  {
    name: "review_note",
    description: "Critique a note and propose concrete improvements.",
    arguments: [{ name: "note_id", description: "Note identifier", required: true }],
  },
];

class RpcProblem extends Error {
  readonly code: number;
  readonly data?: unknown;

  constructor(
    code: number,
    message: string,
    data?: unknown,
  ) {
    super(message);
    this.code = code;
    this.data = data;
  }
}

function isValidRequestId(value: unknown): value is number | string {
  return typeof value === "string" || (typeof value === "number" && Number.isSafeInteger(value));
}

function requestMeta(version = PROTOCOL_VERSION, capabilities: JsonObject = {}): JsonObject {
  return {
    [VERSION_KEY]: version,
    [CAPABILITIES_KEY]: capabilities,
    [CLIENT_INFO_KEY]: { ...CLIENT_INFO },
  };
}

function makeRequest(
  id: number | string,
  method: string,
  params: JsonObject = {},
  version = PROTOCOL_VERSION,
): JsonRpcRequest {
  return {
    jsonrpc: "2.0",
    id,
    method,
    params: { ...params, _meta: requestMeta(version) },
  };
}

function rpcError(
  id: number | string | null,
  code: number,
  message: string,
  data?: unknown,
): JsonRpcResponse {
  const error: { code: number; message: string; data?: unknown } = { code, message };
  if (data !== undefined) error.data = data;
  return { jsonrpc: "2.0", id, error };
}

function complete(
  payload: JsonObject,
  cache?: { ttlMs: number; cacheScope: "private" | "public" },
): JsonObject {
  return {
    resultType: "complete",
    ...payload,
    ...(cache ?? {}),
    _meta: { [SERVER_INFO_KEY]: { ...SERVER_INFO } },
  };
}

function validateRequest(message: JsonRpcRequest): void {
  if (message.jsonrpc !== "2.0" || typeof message.method !== "string") {
    throw new RpcProblem(-32600, "Invalid Request");
  }
  const requestId: unknown = message.id;
  if (requestId !== undefined && !isValidRequestId(requestId)) {
    throw new RpcProblem(-32600, "id must be a string or integer");
  }
  const params = message.params;
  if (!params || typeof params !== "object" || Array.isArray(params)) {
    throw new RpcProblem(-32602, "params must be an object");
  }
  const meta = params._meta;
  if (!meta || typeof meta !== "object" || Array.isArray(meta)) {
    throw new RpcProblem(-32602, "params._meta is required");
  }
  const requested = meta[VERSION_KEY];
  if (typeof requested !== "string") {
    throw new RpcProblem(-32602, `${VERSION_KEY} is required`);
  }
  if (!SUPPORTED_VERSIONS.includes(requested)) {
    throw new RpcProblem(-32022, "Unsupported protocol version", {
      requested,
      supported: [...SUPPORTED_VERSIONS],
    });
  }
  const capabilities = meta[CAPABILITIES_KEY];
  if (!capabilities || typeof capabilities !== "object" || Array.isArray(capabilities)) {
    throw new RpcProblem(-32602, `${CAPABILITIES_KEY} is required`);
  }
  const clientInfo = meta[CLIENT_INFO_KEY];
  if (
    clientInfo !== undefined &&
    (!clientInfo ||
      typeof clientInfo !== "object" ||
      typeof clientInfo.name !== "string" ||
      typeof clientInfo.version !== "string")
  ) {
    throw new RpcProblem(-32602, `${CLIENT_INFO_KEY} is malformed`);
  }
}

function executeList(arguments_: JsonObject): JsonObject[] {
  const tag = arguments_.tag;
  const items = Object.entries(NOTES)
    .sort(([left], [right]) => left.localeCompare(right))
    .filter(([, note]) => !tag || note.tag === tag)
    .map(([id, note]) => ({ id, title: note.title, tag: note.tag }));
  return [{ type: "text", text: JSON.stringify(items) }];
}

function executeSearch(arguments_: JsonObject): JsonObject[] {
  if (typeof arguments_.query !== "string" || !arguments_.query) {
    throw new Error("query must be a non-empty string");
  }
  const limit = arguments_.limit ?? 10;
  if (!Number.isInteger(limit) || limit < 1 || limit > 50) {
    throw new Error("limit must be an integer from 1 through 50");
  }
  const query = arguments_.query.toLowerCase();
  const hits = Object.entries(NOTES)
    .sort(([left], [right]) => left.localeCompare(right))
    .filter(([, note]) => note.title.toLowerCase().includes(query) || note.body.toLowerCase().includes(query))
    .map(([id, note]) => ({ id, title: note.title }))
    .slice(0, limit);
  return [{ type: "text", text: JSON.stringify(hits) }];
}

function executeCreate(arguments_: JsonObject): JsonObject[] {
  if (typeof arguments_.title !== "string" || typeof arguments_.body !== "string") {
    throw new Error("title and body must be strings");
  }
  const id = `note-${randomUUID().replaceAll("-", "").slice(0, 6)}`;
  NOTES[id] = {
    title: arguments_.title,
    body: arguments_.body,
    tag: typeof arguments_.tag === "string" ? arguments_.tag : "",
  };
  return [
    { type: "text", text: `Created ${id}` },
    { type: "resource", resource: { uri: `notes://${id}`, text: arguments_.body } },
  ];
}

const TOOL_EXECUTORS: Record<string, (arguments_: JsonObject) => JsonObject[]> = {
  notes_create: executeCreate,
  notes_list: executeList,
  notes_search: executeSearch,
};

function handleDiscover(): JsonObject {
  return complete(
    {
      supportedVersions: [...SUPPORTED_VERSIONS],
      capabilities: structuredClone(SERVER_CAPABILITIES),
      instructions: "Use tools for note actions, resources for note bodies, and prompts for reviews.",
    },
    { ttlMs: 3_600_000, cacheScope: "public" },
  );
}

function handleToolsList(): JsonObject {
  return complete(
    { tools: [...TOOLS].sort((left, right) => left.name.localeCompare(right.name)) },
    { ttlMs: 60_000, cacheScope: "public" },
  );
}

function handleToolsCall(params: JsonObject): JsonObject {
  if (typeof params.name !== "string" || !params.arguments || typeof params.arguments !== "object") {
    throw new RpcProblem(-32602, "tools/call requires string name and object arguments");
  }
  const executor = TOOL_EXECUTORS[params.name];
  if (!executor) {
    return complete({
      content: [{ type: "text", text: `Unknown tool: ${params.name}` }],
      isError: true,
    });
  }
  try {
    return complete({ content: executor(params.arguments), isError: false });
  } catch (error) {
    return complete({ content: [{ type: "text", text: String(error) }], isError: true });
  }
}

function handleResourcesList(): JsonObject {
  const resources = Object.entries(NOTES)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([id, note]) => ({
      uri: `notes://${id}`,
      name: note.title,
      mimeType: "text/markdown",
    }));
  return complete({ resources }, { ttlMs: 10_000, cacheScope: "private" });
}

function handleResourcesRead(params: JsonObject): JsonObject {
  if (typeof params.uri !== "string" || !params.uri.startsWith("notes://")) {
    throw new RpcProblem(-32602, "resources/read requires a notes:// URI");
  }
  const id = params.uri.slice("notes://".length);
  const note = NOTES[id];
  if (!note) throw new RpcProblem(-32602, "Resource not found", { uri: params.uri });
  return complete(
    {
      contents: [
        {
          uri: params.uri,
          mimeType: "text/markdown",
          text: `# ${note.title}\n\n${note.body}\n\ntag: ${note.tag}`,
        },
      ],
    },
    { ttlMs: 5_000, cacheScope: "private" },
  );
}

function handlePromptsList(): JsonObject {
  return complete(
    { prompts: [...PROMPTS].sort((left, right) => left.name.localeCompare(right.name)) },
    { ttlMs: 60_000, cacheScope: "public" },
  );
}

function handlePromptsGet(params: JsonObject): JsonObject {
  if (params.name !== "review_note") throw new RpcProblem(-32602, "Unknown prompt");
  const arguments_ = params.arguments;
  if (!arguments_ || typeof arguments_ !== "object" || typeof arguments_.note_id !== "string") {
    throw new RpcProblem(-32602, "note_id must name an existing note");
  }
  const note = NOTES[arguments_.note_id];
  if (!note) throw new RpcProblem(-32602, "note_id must name an existing note");
  return complete({
    description: "Review the note and propose concrete improvements.",
    messages: [
      {
        role: "user",
        content: { type: "text", text: `Review this note and propose improvements:\n\n${note.body}` },
      },
    ],
  });
}

const HANDLERS: Record<string, (params: JsonObject) => JsonObject> = {
  "prompts/get": handlePromptsGet,
  "prompts/list": handlePromptsList,
  "resources/list": handleResourcesList,
  "resources/read": handleResourcesRead,
  "server/discover": handleDiscover,
  "tools/call": handleToolsCall,
  "tools/list": handleToolsList,
};

function dispatch(message: JsonRpcRequest): JsonRpcResponse | null {
  if (message.id === undefined) return null;
  const id = message.id;
  const errorId = isValidRequestId(id) ? id : null;
  try {
    validateRequest(message);
    const handler = HANDLERS[message.method];
    if (!handler) throw new RpcProblem(-32601, `Method not found: ${message.method}`);
    return { jsonrpc: "2.0", id, result: handler(message.params ?? {}) };
  } catch (error) {
    if (error instanceof RpcProblem) return rpcError(errorId, error.code, error.message, error.data);
    return rpcError(errorId, -32603, "Internal error", { detail: String(error) });
  }
}

function serveStdio(): void {
  const reader = createInterface({ input: process.stdin, terminal: false });
  reader.on("line", (line) => {
    if (!line.trim()) return;
    let response: JsonRpcResponse | null;
    try {
      const parsed = JSON.parse(line) as unknown;
      response =
        parsed !== null && typeof parsed === "object" && !Array.isArray(parsed)
          ? dispatch(parsed as JsonRpcRequest)
          : rpcError(null, -32600, "Invalid Request");
    } catch (error) {
      response = rpcError(null, -32700, "Parse error", { detail: String(error) });
    }
    if (response) process.stdout.write(`${JSON.stringify(response)}\n`);
  });
}

function demo(): void {
  const scenarios: JsonRpcRequest[] = [
    makeRequest(1, "server/discover"),
    makeRequest(2, "tools/list"),
    makeRequest(3, "resources/list"),
    makeRequest(4, "prompts/list"),
    makeRequest(5, "tools/call", { name: "notes_search", arguments: { query: "MCP" } }),
    makeRequest(6, "resources/read", { uri: "notes://note-1" }),
    makeRequest(7, "prompts/get", { name: "review_note", arguments: { note_id: "note-1" } }),
    makeRequest(8, "tools/list", {}, "2027-01-01"),
  ];
  console.log("MCP 2026-07-28 stateless notes server, TypeScript");
  for (const message of scenarios) {
    console.log(`\n${message.method} id=${message.id}`);
    console.log(JSON.stringify(dispatch(message), null, 2).slice(0, 700));
  }
}

if (process.argv.includes("--demo")) demo();
else serveStdio();
>>>>>>> main
