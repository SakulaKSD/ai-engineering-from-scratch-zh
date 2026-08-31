<<<<<<< HEAD
---
name: mcp-apps-spec
description: Produce the full MCP Apps contract for a tool that needs an interactive UI resource.
version: 1.0.0
phase: 13
lesson: 14
tags: [mcp, apps, ui-resources, csp, iframe-sandbox]
---

Given a tool that would benefit from an interactive UI (timeline, form, dashboard, map, chart), produce the MCP Apps contract.

Produce:

1. `ui://` URI. One canonical name for the UI resource (e.g. `ui://notes/timeline`).
2. Tool result shape. `content[]` with `text` preamble and `ui_resource` block; `_meta.ui` populated.
3. CSP. Minimum allowlist for `default-src`, `script-src`, `connect-src`, `img-src`, `style-src`. Avoid `'unsafe-inline'` unless necessary.
4. Permissions list. Camera / mic / geolocation / network if needed; empty if not.
5. postMessage entry points. Which `host.*` calls the UI will make and what they return.
6. Security checklist. Distinguish-from-host, no clickjacking, strict connect-src, HTML sanitization if any user content is rendered.

Hard rejects:
- CSP with `default-src *`. Wide-open security risk.
- Any `permissions` request beyond what the UI actually uses. Minimum privilege.
- Any ui:// resource that loads external scripts. Bundle or refuse.
- Any UI that renders user-controlled HTML without sanitization. XSS vector.

Refusal rules:
- If the UI is just a static result, refuse to scaffold an App; return text content.
- If the tool would benefit from native host widgets (progress bars, confirmation dialogs), recommend those instead.
- If the host does not yet support MCP Apps (VS Code stable, Zed, Windsurf as of 2026-04), flag fallback-to-text path.

Output: a one-page contract with the `ui://` URI, tool result JSON, CSP, permissions, postMessage entry points, and a security checklist. End with one sentence on the minimum host that will render this UI.
=======
---
name: mcp-apps-spec
description: 在无状态 2026-07-28 协议上设计并审查 MCP App 契约。
version: 2.0.0
phase: 13
lesson: 14
tags: [mcp, apps, stateless, ui-resources, csp, sandbox]
---

给定一个可能需要交互式视图的 MCP 工具，产出一份与框架无关的契约。

## 所需输入

- 工具名称、参数、普通文本结果和结构化结果。
- 视图必须支持的用户交互。
- 数据敏感性，以及响应是否随授权上下文变化。
- 视图所需的浏览器权限和外部源。
- 未支持 Apps 的宿主的纯文本行为。

## 产出

1. 当前核心信封。展示 `2026-07-28`、每个请求的 `protocolVersion`、`clientCapabilities`、建议的 `clientInfo`、匹配的 `Mcp-Method` 和 `Mcp-Name` 请求头，以及 `resultType` 响应。
2. 发现条目。在 `server/discover` 中声明 `io.modelcontextprotocol/ui`，并使用保守的 `ttlMs` 和 `cacheScope`。
3. 工具声明。将嵌套的 `_meta.ui.resourceUri` 放在 `tools/list` 返回的工具上。不要等到 `tools/call` 才暴露 UI。
4. 资源契约。在 `resources/read` 前包含确定性的 `resources/list` 元数据。给出一个规范 `ui://` URI、稳定名称和说明、`text/html;profile=mcp-app`、缓存提示、CSP 域名列表（`connectDomains`、`resourceDomains`、`frameDomains`、`baseUriDomains`）以及最小权限对象。
5. 结果契约。无论宿主是否渲染 App，都返回有用的文本和结构化数据。
6. 桥接契约。列出每个 Apps `ui/*` 或被代理的方法、精确消息源、参数 schema、结果 schema 和宿主侧同意检查。
7. 回退。描述 client 省略 Apps 扩展能力时的工具和结果。
8. 验证表。覆盖路由前 HTTP 400 `-32020` 请求头不匹配、HTTP 400 `-32022` 及精确的受支持与请求版本数据、HTTP 400 `-32021` 及 `data.requiredCapabilities`、HTTP 404 `-32601`、202 空 body 通知、CSP 违反、不可信内容、未授权桥接调用和文本回退。
9. 传输边界。如果实现接收已解析的请求和请求头，应标明它是进程内协议模型，并连接到第 09 课的完整 Streamable HTTP adapter。真实 adapter 必须要求 JSON Content-Type 和一个同时包含 JSON 与 SSE 的 Accept 值。

## 硬性拒绝

- 将核心 `initialize`、`notifications/initialized` 或 `Mcp-Session-Id` 路径称作当前 MCP。
- 使用通配符 `postMessage` 目标源，或接收方跳过 `event.origin` 验证。
- 只在工具运行后才暴露 UI 绑定。
- 通配符 CSP 域名列表、无界网络源，或没有可见功能的权限。
- 插入用户控制的 HTML，却未定义净化边界。
- 将 iframe 点击视为宿主授权的后果性 UI 操作。
- server 声明资源却省略 `resources/list`。
- 为没有 `id` 的通知发送任何 JSON-RPC 响应 body。

## 兼容性边界

可将旧版扁平 UI 元数据作为回退读取，但新输出使用嵌套的 `_meta.ui.resourceUri`。只有明确作为 Apps postMessage 握手时，才允许 `ui/initialize`。它绝不替代已移除的 MCP 核心初始化。

## 输出格式

返回一份紧凑设计，使用这些标题：Core Wire、Discovery、Tool、Resource、Result、Bridge、Security、Fallback、Verification。最后写出风险最高的单项源、权限或同意假设。
>>>>>>> main
