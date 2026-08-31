<<<<<<< HEAD
# MCP Apps——经由 `ui://` 的交互式 UI 资源

> 纯文本工具输出给 agent 能展示的东西封了顶。MCP Apps（SEP-1724，2026 年 1 月 26 日正式）让一个工具返回沙箱化的交互式 HTML，内联渲染在 Claude Desktop、ChatGPT、Cursor、Goose 和 VS Code 里。仪表盘、表单、地图、3D 场景，全经由一个扩展。本课走一遍 `ui://` 资源 scheme、`text/html;profile=mcp-app` MIME、iframe 沙箱的 postMessage 协议，以及让 server 渲染 HTML 所附带的安全表面。

**类型：** Build
**语言：** Python（标准库，UI 资源发射器）、HTML（示例 app）
**前置要求：** 阶段 13 · 07（MCP server）、阶段 13 · 10（resources）
**预计时间：** ~75 分钟

## 学习目标

- 从一个工具调用返回一个 `ui://` 资源，并设正确的 MIME 和元数据。
- 用 `_meta.ui.resourceUri`、`_meta.ui.csp` 和 `_meta.ui.permissions` 声明一个工具关联的 UI。
- 为 UI 到宿主的通信实现 iframe 沙箱的 postMessage JSON-RPC。
- 应用 CSP 和 permissions-policy 默认值，抵御 UI 发起的攻击。

## 问题背景

一个 2025 年代的 `visualize_timeline` 工具能返回"这是按时间顺序组织的 14 条笔记：……"。那是一段话。用户真正想要的是那个交互式时间线。在 MCP Apps 之前，选项是：client 特定的 widget API（Claude artifacts、OpenAI Custom GPT HTML），或者根本没 UI。

MCP Apps（SEP-1724，2026 年 1 月 26 日发布）把契约标准化了。一个工具结果含一个 `resource`，其 URI 是 `ui://...`，其 MIME 是 `text/html;profile=mcp-app`。宿主把它渲染在一个沙箱化的 iframe 里，配一个受限的 CSP，除非显式授予否则无网络访问。iframe 里的 UI 经由一个微型 postMessage JSON-RPC 方言向宿主发消息。

每个兼容的 client（Claude Desktop、ChatGPT、Goose、VS Code）都以同样的方式渲染同一个 `ui://` 资源。一个 server、一个 HTML 包、通用的 UI。

## 核心概念

### `ui://` 资源 scheme

一个工具返回：

```json
{
  "content": [
    {"type": "text", "text": "Here is your notes timeline:"},
    {"type": "ui_resource", "uri": "ui://notes/timeline"}
  ],
  "_meta": {
    "ui": {
      "resourceUri": "ui://notes/timeline",
      "csp": {
        "defaultSrc": "'self'",
        "scriptSrc": "'self' 'unsafe-inline'",
        "connectSrc": "'self'"
      },
      "permissions": []
    }
  }
}
```

宿主随后对 `ui://notes/timeline` URI 调 `resources/read`，拿回：

```json
{
  "contents": [{
    "uri": "ui://notes/timeline",
    "mimeType": "text/html;profile=mcp-app",
    "text": "<!doctype html>..."
  }]
}
```

### iframe 沙箱

宿主把 HTML 渲染在一个沙箱化的 `<iframe>` 里，配：

- `sandbox="allow-scripts allow-same-origin"`（或按 server 声明更严）
- server 声明的 CSP 经由响应头应用。
- 没有 cookie，没有来自宿主源的 localStorage。
- 网络访问限于 CSP 里的 `connectSrc`。

### postMessage 协议

iframe 经由 `window.postMessage` 与宿主通信。一个微型 JSON-RPC 2.0 方言：

始终把 `targetOrigin` 钉到对端的确切源，并在接收侧处理任何载荷前，按白名单校验 `event.origin`。这个通道两侧都绝不要用 `"*"`——body 里携带的是工具调用和资源读取。

```js
// iframe 到宿主  (钉到宿主源)
window.parent.postMessage({
  jsonrpc: "2.0",
  id: 1,
  method: "host.callTool",
  params: { name: "notes_update", arguments: { id: "note-14", title: "..." } }
}, "https://host.example.com");

// 宿主到 iframe  (钉到 iframe 源)
iframe.contentWindow.postMessage({
  jsonrpc: "2.0",
  id: 1,
  result: { content: [...] }
}, "https://iframe.example.com");

// 两侧的接收方
window.addEventListener("message", (event) => {
  if (event.origin !== "https://expected-peer.example.com") return;
  // 可以安全处理 event.data
});
```

UI 可调用的宿主侧方法：

- `host.callTool(name, arguments)`——调用一个 server 工具。
- `host.readResource(uri)`——读一个 MCP resource。
- `host.getPrompt(name, arguments)`——取一个 prompt 模板。
- `host.close()`——关闭这个 UI。

每个调用仍走 MCP 协议，并继承 server 的权限。

### 权限

`_meta.ui.permissions` 列表请求额外能力：

- `camera`——访问用户的摄像头（用于扫描文档的 UI）。
- `microphone`——语音输入。
- `geolocation`——位置。
- `network:*`——比单靠 `connectSrc` 更宽的网络访问。

每个权限都是用户在 UI 渲染前看到的一个提示。

### 安全风险

iframe 里的 HTML 仍是 HTML。新的攻击表面：

- **经由 UI 的 prompt 注入。** 一个恶意 server UI 能展示看起来像 system 消息的文本来骗用户。宿主渲染应当显眼地把 server UI 和宿主 UI 区分开。
- **经由 `connectSrc` 的外泄。** 如果 CSP 允许 `connect-src: *`，UI 能把数据发往任何地方。默认应该严格。
- **点击劫持。** UI 覆盖在宿主 chrome 上。宿主必须防住 z-index 操纵并强制不透明度规则。
- **抢焦点。** UI 拿走键盘焦点并捕获下一条消息。宿主必须拦截。

阶段 13 · 15 作为 MCP 安全的一部分深入讲这些；本课只是引入它们。

### `ui/initialize` 握手

iframe 加载后，它经由 postMessage 发 `ui/initialize`：

```json
{"jsonrpc": "2.0", "id": 0, "method": "ui/initialize",
 "params": {"theme": "dark", "locale": "en-US", "sessionId": "..."}}
```

宿主用能力和一个会话 token 响应。UI 在随后每个宿主调用上用那个会话 token。

### AppRenderer / AppFrame SDK 基元

ext-apps SDK 暴露两个便利基元：

- `AppRenderer`（server 侧）——包一个 React / Vue / Solid 组件，发出一个带正确 MIME 和元数据的 `ui://` 资源。
- `AppFrame`（client 侧）——接收资源，挂载 iframe，并居中调停 postMessage。

你可以用这些，也可以手搓 HTML 和 JSON-RPC。

### 生态状态

MCP Apps 于 2026 年 1 月 26 日发布。截至 2026 年 4 月的 client 支持：

- **Claude Desktop。** 自 2026 年 1 月起完全支持。
- **ChatGPT。** 经由 Apps SDK 完全支持（同一底层 MCP Apps 协议）。
- **Cursor。** Beta；经设置启用。
- **VS Code。** 仅 Insider 构建。
- **Goose。** 完全支持。
- **Zed、Windsurf。** 已列入路线图。

生产里的 server：仪表盘、地图可视化、数据表、图表构建器、沙箱 IDE 预览。

```figure
t3-ui-sandbox
```

## 实际使用

`code/main.py` 在 notes server 上扩展出一个 `visualize_timeline` 工具，返回一个 `ui://notes/timeline` 资源，外加一个对该 URI 的 `resources/read` 处理器，它返回一个小而完整、带 SVG 时间线的 HTML 包。HTML 用标准库模板化——没有构建系统。postMessage 在 JS 注释里勾画，因为标准库驱动不了浏览器。

要看什么：

- 工具响应上的 `_meta.ui` 携带 resourceUri、CSP、permissions。
- HTML 无网络访问就渲染；所有数据都内联了。
- JS 经由 `window.parent.postMessage` 调 `host.callTool`（有文档但在这个标准库 demo 里是惰性的）。

## 拿去用

本课产出 `outputs/skill-mcp-apps-spec.md`。给定一个会受益于交互式 UI 的工具，这个 skill 产出完整的 MCP Apps 契约：`ui://` URI、CSP、permissions、postMessage 入口点，以及一份安全清单。

## 练习

1. 跑 `code/main.py`，检视发出的 HTML。直接在浏览器里打开这个 HTML；验证 SVG 渲染。然后勾画 UI 用来调 `host.callTool("notes_update", ...)` 的 postMessage 契约。

2. 收紧 CSP：移除 `'unsafe-inline'`，用一个基于 nonce 的脚本策略。HTML 生成代码里有什么变化？

3. 加第二个 UI 资源 `ui://notes/editor`，带一个就地编辑笔记的表单。用户提交时，iframe 调 `host.callTool("notes_update", ...)`。

4. 审计这个 UI 的攻击表面。恶意 server 可能在哪儿注入内容？iframe 沙箱防住什么，不防什么？

5. 读 SEP-1724 规范，找出 MCP Apps SDK 里一个这个玩具实现没用上的能力。（提示：组件级状态同步。）

## 关键术语

| 术语 | 大家嘴上怎么说 | 它实际是什么 |
|------|----------------|------------------------|
| MCP Apps | "交互式 UI 资源" | 2026-01-26 发布的 SEP-1724 扩展 |
| `ui://` | "App URI scheme" | UI 包的资源 scheme |
| `text/html;profile=mcp-app` | "那个 MIME" | MCP App HTML 的 content-type |
| Iframe sandbox | "渲染容器" | 浏览器对 UI 的沙箱化，配 CSP 和权限 |
| postMessage JSON-RPC | "UI 到宿主的线" | 用于宿主调用的微型 JSON-RPC-over-postMessage 方言 |
| `_meta.ui` | "工具-UI 绑定" | 把一个工具结果链接到一个 UI 资源的元数据 |
| CSP | "Content-Security-Policy" | 声明脚本、网络、样式的允许来源 |
| AppRenderer | "server SDK 基元" | 把一个框架组件转成一个 `ui://` 资源 |
| AppFrame | "client SDK 基元" | 居中调停 postMessage 的 iframe 挂载助手 |
| `ui/initialize` | "握手" | UI 到宿主的第一条 postMessage |

## 延伸阅读

- [MCP ext-apps — GitHub](https://github.com/modelcontextprotocol/ext-apps) — 参考实现与 SDK
- [MCP Apps specification 2026-01-26](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx) — 正式规范文档
- [MCP — Apps extension overview](https://modelcontextprotocol.io/extensions/apps/overview) — 高层文档
- [MCP blog — MCP Apps launch](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/) — 2026 年 1 月发布博文
- [MCP Apps API reference](https://apps.extensions.modelcontextprotocol.io/api/) — JSDoc 风格 SDK 参考
=======
# 无状态协议上的 MCP Apps

> 交互式结果仍是一场 MCP 工具和资源交换。2026-07-28 核心让这场交换自包含，而 Apps 扩展增加了沙箱化浏览器界面。

**类型：** Build
**语言：** Python
**前置要求：** 阶段 13 · 07（MCP server）、阶段 13 · 10（resources）
**预计时间：** ~75 分钟

## 学习目标

- 通过 `server/discover` 和每个请求的扩展能力声明 MCP Apps。
- 在调用工具之前，先在工具上声明一个 `ui://` 资源。
- 在 2026-07-28 无状态传输线上返回完整的工具和资源结果。
- 区分 Apps 的 `ui/initialize` 桥接消息与已移除的 MCP 核心握手。
- 应用源验证、沙箱、CSP 和最小权限原则。

## 问题背景

文本结果可以描述一条时间线，却不能把一条可供用户筛选、检查或操作的时间线交给他们。

MCP Apps 通过可选扩展解决展示问题。工具定义指向一个 `ui://` 资源。宿主可在工具运行前获取并审查该资源，在沙箱化 iframe 中渲染它，并通过 JSON-RPC 桥接调停所有 App 操作。

核心协议在 2026-07-28 发生变化。不要把 App 包进旧的连接生命周期：

- 不再有核心 `initialize` 请求或 `notifications/initialized` 通知。
- 不再有 `Mcp-Session-Id` 请求头。
- 每个请求都在 `params._meta` 中携带协议版本和 client 能力。
- server 实现 `server/discover`，供 client 检查版本、核心能力和扩展。
- 每个成功结果都有 `resultType` 区分字段。
- Streamable HTTP 每个请求只用一次 POST。现代 GET 和 DELETE 入口返回 405。

Apps 桥接仍有一个名为 `ui/initialize` 的方法。它属于 iframe 的 postMessage 方言，不会重新创建一个核心 MCP 会话。

## 核心概念

### 两种协议，一个功能

让各层职责明确：

1. MCP 核心承载 `server/discover`、`tools/list`、`tools/call`、`resources/list` 和 `resources/read`。
2. MCP Apps 扩展声明 UI，并定义 iframe 到宿主的桥接。
3. 浏览器沙箱规则限制 UI 能访问的范围。

扩展标识符是 `io.modelcontextprotocol/ui`。双方都要选择加入。client 在每个请求的能力对象中发送扩展支持：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {
          "io.modelcontextprotocol/ui": {}
        }
      },
      "io.modelcontextprotocol/clientInfo": {
        "name": "timeline-host",
        "version": "1.0.0"
      }
    }
  }
}
```

建议提供 `clientInfo` 用于诊断。它由 client 自行报告，并非授权身份。

### 渲染前先发现

server 的发现结果会声明该扩展：

```json
{
  "resultType": "complete",
  "supportedVersions": ["2026-07-28"],
  "capabilities": {
    "tools": {},
    "resources": {},
    "extensions": {
      "io.modelcontextprotocol/ui": {}
    }
  },
  "ttlMs": 300000,
  "cacheScope": "public",
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {
      "name": "timeline-app-server",
      "version": "2.0.0"
    }
  }
}
```

server 必须支持发现。client 无需在每次操作前都调用发现，因为每个操作都携带自身能力。

### 在工具定义上声明 UI

现代 Apps 契约在 `tools/list` 中将 UI 绑定到工具：

```json
{
  "name": "notes_timeline",
  "description": "Render a timeline of notes.",
  "inputSchema": {
    "type": "object",
    "properties": {}
  },
  "_meta": {
    "ui": {
      "resourceUri": "ui://notes/timeline.html"
    }
  }
}
```

这是刻意设计为调用前元数据。宿主可以在结果请求显示它之前预加载、缓存并审查 HTML 的安全性。兼容性代码可接受较旧的扁平元数据键，但新 server 应输出嵌套的 `_meta.ui.resourceUri` 形式。

当前核心中的 `tools/list` 可缓存。请包含确定性排序、`ttlMs` 和 `cacheScope`。当可见工具会随用户或 token 变化时，使用 `private`。

### 先返回数据，再让宿主绑定视图

工具调用返回普通内容加结构化数据：

```json
{
  "resultType": "complete",
  "content": [
    {"type": "text", "text": "Timeline ready."}
  ],
  "structuredContent": {
    "notes": [
      {"id": "note-1", "title": "Discover", "created": "2026-07-28"}
    ]
  },
  "isError": false
}
```

宿主已知道哪个视图属于该工具。不要为了重复 URI 而另造一个内容块。

### 将 App 作为资源提供

server 在发现中声明 `resources`，因而还实现了必需的 `resources/list` 操作。其确定性列表条目包括规范 URI、稳定名称、说明和 MIME 类型。该列表结果与确定性工具列表一样，包含 `resultType`、server 身份元数据、`ttlMs` 和 `cacheScope`。

宿主发送 `resources/read`。在 Streamable HTTP 上，请求为：

```text
POST /mcp
MCP-Protocol-Version: 2026-07-28
Mcp-Method: resources/read
Mcp-Name: ui://notes/timeline.html
```

请求头的值和 JSON-RPC body 必须一致。不一致即为协议错误 `-32020`。

结果包含 HTML 资源和缓存提示：

```json
{
  "resultType": "complete",
  "contents": [
    {
      "uri": "ui://notes/timeline.html",
      "mimeType": "text/html;profile=mcp-app",
      "text": "<!doctype html>...",
      "_meta": {
        "ui": {
          "csp": {
            "connectDomains": [],
            "resourceDomains": [],
            "frameDomains": [],
            "baseUriDomains": []
          },
          "permissions": {}
        }
      }
    }
  ],
  "ttlMs": 60000,
  "cacheScope": "public"
}
```

### 将 UI 资源作为可执行内容缓存

App 资源不能与普通文本等同。它的缓存条目可以执行桥接代码、渲染工具数据，并请求由宿主调停的操作。应以规范 `ui://` URI、被接纳的 server 身份和版本、资源内容摘要，以及当 `cacheScope` 为 private 时的授权上下文作为键。即使 URI 相同，也绝不要跨主体复用私有 App 资源，因为 HTML 或其策略元数据可能不同。

当 `ttlMs` 到期、工具的 `_meta.ui.resourceUri` 绑定改变、server 版本或接纳的描述符 pin 改变，或已确认的资源变更订阅提到该 URI 时，使该条目失效。重新挂载前重新获取资源并重新应用 CSP 和权限审查。不能只因新资源版本尚未加载，就让过期 iframe 保留更宽的权限。

### 在功能策略之前拒绝传输歧义

验证顺序经过刻意安排。先验证 JSON-RPC 形状，并要求字符串协议元数据和对象类型的 client 能力映射。然后比较路由请求头和 body。只有之后才决定已匹配的协议版本是否受支持。这个顺序防止代理与 server 对不同请求作出解释。

| 条件 | HTTP | JSON-RPC 错误 |
|------|------|----------------|
| 请求头和 body 的版本、方法或名称不一致 | 400 | `-32020` |
| 请求头和 body 一致但版本不受支持 | 400 | `-32022`，其 `data` 必须恰为 `{"supported":["2026-07-28"],"requested":"<actual>"}` |
| `resources/read` 缺少 Apps 扩展能力 | 400 | `-32021`，其 `data.requiredCapabilities.extensions.io.modelcontextprotocol/ui` |
| 方法未知 | 404 | `-32601` |

JSON-RPC 通知没有 `id`，因此 server 绝不会为它发出 JSON-RPC 响应。被接受的 HTTP 通知返回 202 和空 body。错误可改变 HTTP 状态，但仍不能为通知创建 JSON-RPC 错误 body。

### 沙箱是边界，不是信任结论

宿主控制 iframe。App 无法直接读取宿主 cookie、本地存储或页面 DOM。所有特权工作都必须穿过桥接。

使用以下默认值：

- 先将所有 CSP 域名列表留空，只添加 App 所需的源。`connectDomains` 用于 fetch、XHR 和 WebSocket；`resourceDomains` 用于脚本、样式、图片和字体。
- 可行时打包代码和数据。
- 除非可见功能确有需要，否则不请求摄像头、麦克风或位置权限。
- 将 `postMessage` 固定到确切的对端源，并拒绝来自所有其他源的事件。
- 将工具参数、工具结果、资源文本和桥接消息视为不可信输入。
- 将用户同意保留在宿主中。iframe 不能批准它自己的后果性操作。

不要把教程中的固定 `sandbox` 属性复制到每个宿主中。宿主必须根据 App 的源模型和自身隔离设计选择标志。

允许的域仍是一条外泄路径。`connectDomains: ["https://api.example.com"]` 意味着在 App 内执行的任何脚本都可以将允许的数据发送到那里。精确的源匹配可避免目标混淆，却不能决定载荷是否恰当。默认保持连接访问为空，避免将 bearer token 放进 iframe；可行时让宿主代理狭窄操作，限制响应和请求大小，并审计哪次用户操作触发了每个出站请求。将 `resourceDomains` 与 `connectDomains` 分开处理；加载字体或脚本的许可不应授予任意数据上传。

### Apps 桥接有自己的生命周期

Apps 桥接是经由 `postMessage` 的 JSON-RPC 方言。它可以交换 `ui/initialize` 和 `ui/*` 通知，并可代理形似核心的方法，如 `tools/call`。

View 发送 `ui/initialize`，其中带有 `appInfo` 和一个 `appCapabilities` 对象。宿主返回它的能力和宿主上下文。只有在该响应之后，View 才发送 `ui/notifications/initialized`。宿主必须等待这条 Apps 通知后才能向 View 发送消息。

这个局部握手在一个 iframe 和一个宿主 frame 间创建桥接。它不会协商 MCP 协议版本、创建 server 状态或铸造传输会话。注意精确前缀：核心 `notifications/initialized` 已移除，而 Apps 的 `ui/notifications/initialized` 仍然存在。由桥接工具调用生成的核心请求是一个新的自包含请求，带有新的 JSON-RPC id 和完整请求元数据。

### 宿主上下文、操作和撤销

桥接初始化后，宿主仍是权威。View 只能通过宿主已声明的能力请求工具操作、导航、剪贴板使用或其他特权效果。宿主验证带类型的请求、当前用户、目标和参数，应用批准策略，并可拒绝请求。按钮点击和有效桥接消息只表达意图；两者都不授予权限。

将主题、尺寸和无障碍能力视为会变化的宿主上下文，而非一次性渲染输入：

- 应用宿主提供的颜色和排版 token，再响应主题或对比度偏好的变化。
- 让 View 报告期望尺寸，但让宿主限制并应用 iframe 尺寸，以免内容逃出布局或制造欺骗性覆盖层。
- 在 iframe 内保留键盘顺序、可见焦点、无障碍名称、屏幕阅读器状态、足够的对比度、缩放和减少动态效果行为。
- 调整尺寸和重新渲染后，重新测试宿主控件与 View 控件之间的焦点转移。

App 打开期间能力可能被撤销：用户切换账户、策略改变、server 被隔离，或宿主收紧同意范围。应在操作时检查能力和授权，而非只在 `ui/initialize` 时检查。撤销时，拒绝待处理的特权调用，停止不再符合策略的网络活动，清除敏感的已渲染状态；当 UI 资源本身不再被接纳时，重新挂载或回退到文本。View 必须将拒绝视作正常结果，不能不断重试直到宿主让步。

### 回退是契约的一部分

支持 Apps 的 server 仍可服务未声明 UI 扩展的宿主：

- 在 `tools/list` 中返回同一工具，但不带 `_meta.ui`。
- 为 `tools/call` 保留有用的文本结果。
- 对该 UI 的 `resources/read` 以缺少能力错误拒绝。
- 决定工具是否完成时，绝不假设 iframe 存在。

```figure
t3-ui-sandbox
```

## 动手构建

`code/main.py` 构建了一个不依赖 SDK 的小型进程内协议模型。它验证当前请求信封和 Streamable HTTP 路由值，通过 `server/discover` 声明 Apps，列出工具和资源，执行工具，并提供一个自包含 HTML 资源。

该模型接收已解析的 body 和路由请求头。它不是完整 HTTP adapter，也不解析 `Content-Type` 或 `Accept`。请使用第 09 课中的完整 Streamable HTTP adapter；它要求 `Content-Type: application/json` 和同时包含 `application/json` 与 `text/event-stream` 的 `Accept` 值。

运行它：

```bash
cd phases/13-tools-and-protocols/14-mcp-apps
python3 code/main.py
PYTHONPATH=code python3 -m unittest discover code/tests -v
```

检查输出中的五项：

1. 每次调用都相互独立。
2. 每个请求都带有 `_meta` 能力。
3. `resources/list` 在读取任何资源前返回稳定描述符。
4. 每个结果都有 `resultType` 和 server 身份元数据。
5. 不出现核心会话标识符。

## 实际使用

从 `server/discover` 开始。确认 `io.modelcontextprotocol/ui` 出现在 server 扩展映射中。然后调用两次 `tools/list`：一次带 Apps 能力，一次不带。第一个响应声明资源。第二个仍是可用的纯文本工具。

读取 `ui://notes/timeline.html`。在 HTML 中搜索 `hostOrigin` 和 `event.origin` guard。这两行是桥接未使用通配符目标的最低限度可见证据。

## 拿去用

本课交付 `outputs/skill-mcp-apps-spec.md`。在编写框架代码前，用它审查 App 契约。它要求作者说明当前核心信封、扩展协商、回退、UI 资源、缓存策略、CSP、权限、桥接方法和同意边界。

## 练习

1. 将 client 能力改为空扩展映射。确认 `tools/list` 保留工具但移除 UI 绑定。
2. 发送 `Mcp-Name: ui://notes/other.html`，但 body 读取时间线。确认错误为 `-32020`。
3. 将资源改为 `cacheScope: private`。描述能证明此设置合理的用户特定条件。
4. 将脚本移至 `https://static.example.com/app.js`。将该源添加到 `resourceDomains`，并解释新增的供应链风险。
5. 添加一个 `notes_open` 工具，让按钮点击经由宿主路由。将用户批准保留在宿主中。

## 关键术语

| 术语 | 含义 |
|------|---------|
| MCP Apps | 用于由 MCP 宿主渲染交互式 HTML 的可选扩展 |
| `io.modelcontextprotocol/ui` | 由双方声明的扩展标识符 |
| `ui://` | App UI 模板的资源 scheme |
| `text/html;profile=mcp-app` | MCP App HTML 的 MIME 类型 |
| `server/discover` | 当前用于协议和能力发现的 RPC |
| `resources/list` | server 声明资源时必需的资源列表方法 |
| `resultType` | 现代成功结果所需的区分字段 |
| `ui/initialize` | 第一条 Apps 桥接请求，与已移除的核心初始化分离 |
| `ui/notifications/initialized` | 宿主响应后发送的 Apps View 就绪通知 |
| CSP | 限制脚本、样式、图片和网络源的浏览器策略 |
| 文本回退 | 未支持 Apps 的宿主仍保留的工具行为 |

## 延伸阅读

- [MCP 2026-07-28 base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic)
- [MCP Apps overview](https://modelcontextprotocol.io/extensions/apps/overview)
- [MCP Apps build guide](https://modelcontextprotocol.io/extensions/apps/build)
- [Official extension support matrix](https://modelcontextprotocol.io/extensions/client-matrix)
>>>>>>> main
