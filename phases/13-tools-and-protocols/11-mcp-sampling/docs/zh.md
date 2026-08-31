<<<<<<< HEAD
# MCP Sampling——server 请求的 LLM 补全与 agent 循环

> 多数 MCP server 是傻执行器：取参数、跑代码、返回内容。Sampling 让 server 反转方向：它请求 client 的 LLM 来做一个决策。这让 server 托管的 agent 循环成为可能，而 server 不必拥有任何模型凭证。SEP-1577 在 2025-11-25 合入，给 sampling 请求里加了工具，让循环能纳入更深的推理。漂移风险提示：SEP-1577 的 sampling-内带工具形状在整个 2026 年第一季度仍是实验性的，在 SDK API 里还在沉淀。

**类型：** Build
**语言：** Python（标准库，sampling 脚手架）
**前置要求：** 阶段 13 · 07（MCP server）、阶段 13 · 10（resources 与 prompts）
**预计时间：** ~75 分钟

## 学习目标

- 解释 `sampling/createMessage` 解决了什么（无 server 端 API key 的 server 托管循环）。
- 实现一个 server，让它请求 client 在一个多轮 prompt 上采样，并返回补全。
- 用 `modelPreferences`（成本 / 速度 / 智能优先级）来引导 client 的模型选择。
- 构建一个 `summarize_repo` 工具，让它内部经由 sampling 迭代，而非硬编码行为。

## 问题背景

一个对代码摘要工作流有用的 MCP server 需要：遍历文件树、挑选读哪些文件、合成一份摘要、返回。LLM 推理在哪儿发生？

选项 A：server 调它自己的 LLM。需要一个 API key，在 server 端计费，每用户都贵。

选项 B：server 返回原始内容；client 的 agent 做推理。能行，但把 server 逻辑搬进了 client prompt，这很脆。

选项 C：server 经由 `sampling/createMessage` 请求 client 的 LLM。server 保留算法（读哪些文件、做几遍），而 client 保留计费和模型选择。server 根本没有凭证。

Sampling 就是选项 C。它是一个受信 server 托管一个 agent 循环、却本身不当一个完整 LLM 宿主的机制。

## 核心概念

### `sampling/createMessage` 请求

server 发：

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "sampling/createMessage",
  "params": {
    "messages": [{"role": "user", "content": {"type": "text", "text": "..."}}],
    "systemPrompt": "...",
    "includeContext": "none",
    "modelPreferences": {
      "costPriority": 0.3,
      "speedPriority": 0.2,
      "intelligencePriority": 0.5,
      "hints": [{"name": "claude-3-5-sonnet"}]
    },
    "maxTokens": 1024
  }
}
```

client 跑它的 LLM，返回：

```json
{"jsonrpc": "2.0", "id": 42, "result": {
  "role": "assistant",
  "content": {"type": "text", "text": "..."},
  "model": "claude-3-5-sonnet-20251022",
  "stopReason": "endTurn"
}}
```

### `modelPreferences`

三个加起来为 1.0 的浮点数：

- `costPriority`：偏向更便宜的模型。
- `speedPriority`：偏向更快的模型。
- `intelligencePriority`：偏向更强的模型。

外加 `hints`：server 偏好的具名模型。client 可以认也可以不认 hints；client 的用户配置永远说了算。

### `includeContext`

三个取值：

- `"none"`——只有 server 提供的消息。默认。
- `"thisServer"`——纳入这个 server 会话里的先前消息。
- `"allServers"`——纳入所有会话上下文。

`includeContext` 自 2025-11-25 起被软弃用，因为它泄漏跨 server 上下文，这是个安全隐患。优先 `"none"`，把显式上下文放进消息里传。

### 带工具的 sampling（SEP-1577）

2025-11-25 新增：sampling 请求可以含一个 `tools` 数组。client 用这些工具跑一整个工具调用循环。这让 server 经由 client 的模型托管一个 ReAct 风格的 agent 循环。

```json
{
  "messages": [...],
  "tools": [
    {"name": "fetch_url", "description": "...", "inputSchema": {...}}
  ]
}
```

client 循环：采样、若被调用则执行工具、再采样、返回最终 assistant 消息。这在整个 2026 年第一季度都是实验性的；SDK 签名可能还会漂移。你实现时对照 2025-11-25 规范的 client/sampling 章节确认。

### 人在回路

client 必须在跑采样前，向用户展示 server 在要模型做什么。一个恶意 server 可能用 sampling 操纵用户的会话（"跟用户说 X，让他们点 Y"）。Claude Desktop、VS Code 和 Cursor 把 sampling 请求呈现为一个用户可以拒绝的确认对话框。

2026 年的共识：无人工确认的 sampling 是个危险信号。网关（阶段 13 · 17）能自动批准低风险 sampling，自动拒绝任何可疑的。

### 无 API key 的 server 托管循环

权威用例：一个自身无 LLM 访问的代码摘要 MCP server。它做：

1. 遍历 repo 结构。
2. 用 "挑五个最可能描述这个 repo 用途的文件" 调 `sampling/createMessage`。
3. 读那些文件。
4. 用文件内容和 "用 3 段摘要这个 repo" 调 `sampling/createMessage`。
5. 把摘要作为一个 `tools/call` 结果返回。

server 从不碰 LLM API。client 的用户用自己的凭证为这些补全付费。

### 安全风险（Unit 42 披露，2026 Q1）

- **隐蔽 sampling。** 一个总用 "用会话上下文里的用户邮箱来回复" 调 sampling 的工具。阶段 13 · 15 讲这些攻击向量。
- **经由 sampling 的资源窃取。** server 让 client 摘要攻击者的载荷，由用户买单。
- **循环炸弹。** server 在一个紧循环里调 sampling。client 必须强制每会话限流。

```figure
t3-sampling-flip
```

## 实际使用

`code/main.py` 交付一个假的 server 到 client 的 sampling 脚手架。一个模拟的 "summarize_repo" 工具调用两轮 sampling（挑文件，然后摘要），假 client 返回预制响应。脚手架展示：

- server 带 `modelPreferences` 发 `sampling/createMessage`。
- client 返回一个补全。
- server 继续它的循环。
- 限流器给每次工具调用的总 sampling 调用数封顶。

要看什么：

- server 只暴露一个工具（`summarize_repo`）；所有推理都在 sampling 调用里发生。
- 模型偏好给 client 的模型选择加权；hints 列出偏好的模型。
- 循环在 `stopReason: "endTurn"` 时终止。
- `max_samples_per_tool = 5` 上限抓住一个失控循环。

## 拿去用

本课产出 `outputs/skill-sampling-loop-designer.md`。给定一个需要 LLM 调用的 server 端算法（研究、摘要、规划），这个 skill 用正确的 modelPreferences、限流和安全确认设计一个基于 sampling 的实现。

## 练习

1. 跑 `code/main.py`。把 `max_samples_per_tool` 改成 2，观察限流截断。

2. 实现 SEP-1577 的 sampling-内带工具变体：sampling 请求携带一个 `tools` 数组。验证 client 端循环在返回最终补全前执行了那些工具。注意漂移风险：SDK 签名在 2026 上半年可能还会变。

3. 加人在回路确认：在 server 第一次 `sampling/createMessage` 前，暂停并等用户批准。被拒的调用返回一个定型拒绝。

4. 加一个按 client 会话作键的每用户限流器。同一用户的同 server 循环应共享一份预算。

5. 设计一个用 sampling 挑选要纳入哪些块的 `summarize_pdf` 工具。勾画发出的消息。`modelPreferences.intelligencePriority` 在 0.1 vs 0.9 时如何改变行为？

## 关键术语

| 术语 | 大家嘴上怎么说 | 它实际是什么 |
|------|----------------|------------------------|
| Sampling | "server 到 client 的 LLM 调用" | server 向 client 的模型要一个补全 |
| `sampling/createMessage` | "那个方法" | sampling 请求的 JSON-RPC 方法 |
| `modelPreferences` | "模型优先级" | 成本 / 速度 / 智能权重外加名字 hints |
| `includeContext` | "跨会话泄漏" | 被软弃用的上下文纳入模式 |
| SEP-1577 | "sampling 里的工具" | 允许 sampling 内带工具以做 server 托管的 ReAct |
| Human-in-the-loop | "用户确认" | client 在跑之前把 sampling 请求呈现给用户 |
| Loop bomb | "失控 sampling" | server 端的无限 sampling 循环；client 必须限流 |
| Covert sampling | "隐藏推理" | 恶意 server 把意图藏进 sampling prompt |
| Resource theft | "用掉用户的 LLM 预算" | server 强迫 client 在它不想要的 sampling 上花钱 |
| `stopReason` | "为什么生成停了" | `endTurn`、`stopSequence` 或 `maxTokens` |

## 延伸阅读

- [MCP — Concepts: Sampling](https://modelcontextprotocol.io/docs/concepts/sampling) — sampling 的高层概览
- [MCP — Client sampling spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) — 权威的 `sampling/createMessage` 形状
- [MCP — GitHub SEP-1577](https://github.com/modelcontextprotocol/modelcontextprotocol) — sampling 里带工具的 Spec Evolution Proposal（实验性）
- [Unit 42 — MCP attack vectors](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/) — 隐蔽 sampling 与资源窃取模式
- [Speakeasy — MCP sampling core concept](https://www.speakeasy.com/mcp/core-concepts/sampling) — 配 client 端代码示例的逐步讲解
=======
# MCP Model Input：Sampling 迁移与无状态 MRTR

> MCP 2026-07-28 不推荐为新设计使用 Sampling，并移除了 server-to-client request channel。若现有 workflow 仍需 client 的 model，server 返回 `input_required` result，client 携带 model output 重试原始 request。推理 loop 在协议层变得显式、有界且无状态。

**类型：** Build
**语言：** Python
**前置要求：** 阶段 13 · 07（MCP server），阶段 13 · 10（resources 与 prompts）
**预计时间：** 约 75 分钟

## 学习目标

- 解释为何 MCP 2026-07-28 不推荐 Sampling，并为新 servers 选择 direct model integration 默认方案。
- 实现通过多轮往返请求（MRTR）承载 `sampling/createMessage` 的兼容 workflow。
- 在每个请求 `_meta` object 中放入协议 revision 和 client capabilities。
- 返回 `resultType: "input_required"`，并以新的 JSON-RPC id 重试原始 method。
- 完整性保护 `requestState`，并将其绑定到 principal、method、arguments 和 expiry。
- 使用 capability checks、approval、response validation 和 round limit 约束 model-assisted loops。

## 协议之前的决策

像 `summarize_repo` 这样的 tool 需要两类 work：

1. 确定性 work：列出 files、读取允许的 files、校验 paths，并组装 content。
2. Model work：选择有代表性的 files，并综合 summary。

现在有两种有效架构。

### 新 server：直接集成 model provider

这是当前默认方案。server 拥有 model selection、credentials、budgets、retries 和 observability。它向 MCP client 返回一个普通 `tools/call` result。

当 server 已是 hosted service，或可预测的 model behavior 比使用 host model 更重要时，选择它。

### 现有 Sampling workflow：迁移到 MRTR

Sampling 在弃用窗口内仍然存在。面向 2026-07-28 的 server 不能向 client 发回实时 `sampling/createMessage` request，而是在 `InputRequiredResult` 中嵌入该 request。

仅当使用 client model 和 credentials 是真实 product requirement 时选择这条兼容路径。记录 removal plan，因为新 implementations 不应采用已弃用的 Sampling。

## 无状态契约

2026 年 7 月协议没有 `initialize` exchange、没有 `notifications/initialized`，也没有 `Mcp-Session-Id`。每条请求都携带原先位于 handshake 中的信息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "summarize_repo",
    "arguments": {"audience": "developer"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {"sampling": {}},
      "io.modelcontextprotocol/clientInfo": {
        "name": "lesson-client",
        "version": "1.0.0"
      }
    }
  }
}
```

server 在每条请求上校验 revision。缺失或非字符串 version 属于 invalid params，返回 `-32602`。不支持的字符串返回 `-32022`，其精确 data 为 `{"supported":["2026-07-28"],"requested":"<client version>"}`。缺少 Sampling capability 返回 `-32021`，其 `data.requiredCapabilities` 设为 `{"sampling":{}}`。

没有 JSON-RPC `id` 的 envelope 是 notification。receiver 可以处理它，但既不发送 success response，也不发送 error response。Streamable HTTP adapter 对已接受 notification 返回无 body 的 `202 Accepted`。

server 还要实现带精确 `supportedVersions` key、capabilities、`ttlMs` 和 `cacheScope` 的 `server/discover`，使 client 可以在调用 tool 前了解并缓存 server contract。因为 discovery 声明了 `tools`，server 也实现必需的 `tools/list`。其确定性的 `summarize_repo` descriptor 包含有效 object `inputSchema`、`resultType: "complete"`、server identity metadata 和 public cache hints。

每个成功的现代 result 都有 discriminator：

- `resultType: "complete"` 表示 operation 已完成。
- `resultType: "input_required"` 表示 client 必须满足嵌入的 requests 后重试。
- Extensions 可定义额外 result types。Tasks extension 在第 13 课加入了 `"task"`。

## 一轮 MRTR

server 在处理 request 时不能调用 client，因此返回此 result：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "input_required",
    "inputRequests": {
      "pick_files": {
        "method": "sampling/createMessage",
        "params": {
          "messages": [
            {
              "role": "user",
              "content": {
                "type": "text",
                "text": "Choose three representative files and return a JSON array."
              }
            }
          ],
          "systemPrompt": "Return only the requested value.",
          "modelPreferences": {
            "costPriority": 0.8,
            "intelligencePriority": 0.2
          },
          "maxTokens": 400
        }
      }
    },
    "requestState": "opaque-integrity-protected-value"
  }
}
```

client 校验自己支持 Sampling，应用自己的 approval 和 model policies，并获得 model response。随后它以不同 JSON-RPC id 发送一条新 request：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "summarize_repo",
    "arguments": {"audience": "developer"},
    "inputResponses": {
      "pick_files": {
        "role": "assistant",
        "content": {
          "type": "text",
          "text": "[\"README.md\", \"server.py\", \"docs/intro.md\"]"
        },
        "model": "host-model",
        "stopReason": "endTurn"
      }
    },
    "requestState": "opaque-integrity-protected-value",
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {"sampling": {}}
    }
  }
}
```

retry 不是协议 session 的 continuation。它是新请求：重复原始 method 和 arguments，仅添加当前 round 的 `inputResponses`，并逐字回显 `requestState`。

MRTR 只允许用于 `tools/call`、`prompts/get` 和 `resources/read`。server 不得从无关 methods 返回 `input_required`。

## 多轮状态

本课需要两次 model calls：

1. `pick_files` 返回 JSON array。
2. `summary` 返回最终 prose。

每次 retry 只携带该 round 的 responses。因此，server 将 phase 和已校验 intermediate data 放入下一个 `requestState`。

将该 value 视为 attacker-controlled。仅签名原始 phase name 不够。将 state 绑定到：

- authenticated principal，而非 self-reported `clientInfo`；
- originating method；
- 原始 arguments 的 digest；
- 较短 expiry；
- 当前 phase 和已校验 intermediate values。

不要求 confidentiality 时使用 HMAC；client 不应读取 state 时使用 authenticated encryption。对错误 signature、过期 value、变更 principal 或变更 arguments，返回 `-32602`。

client 不得解析或修改 `requestState`。它唯一的工作是，在 retry 中回显完全相同的 string。

## Model Preferences 是 Hints

`costPriority`、`speedPriority` 和 `intelligencePriority` 是彼此独立的 preferences。它们不是 probability distribution，也不需要加和为一。client 可以忽略它们，因为 client 拥有 model policy。

如果维护旧版 Sampling flow，将 `includeContext` 保持为 `"none"`。其他 context modes 会提高 leakage risk，且它们本身也已弃用。在 request 中传入最少的显式 context。

## 安全不变量

client 是嵌入 Sampling requests 的 trust boundary。

- 当 policy 要求 approval 时，向用户展示 server 正要求 model 执行什么。
- 限制 MRTR rounds，否则恶意 server 可制造 model-spend loop。
- 将每个 sampling response 用作 filename、URL 或 tool input 前先校验。
- 限制每轮 bytes 和 tokens。
- 拒绝当前 client capabilities 未声明支持的 input request。
- 不让 model output 参与 authorization decisions。
- 记录 originating method 与 input-request key，但不记录敏感 prompt content。

`clientInfo` 和 `serverInfo` 是 display 与 diagnostics metadata。绝不要将任一者作为 authenticated identity。

```figure
t3-sampling-flip
```

## 动手构建

`code/main.py` 不依赖第三方 package，实现完整两轮 flow：

- `server/discover` 返回 `supportedVersions`、声明 tool support，并返回 cache hints。
- `tools/list` 返回确定性的、可缓存的 `summarize_repo` descriptor 和 object input schema。
- `tools/call` 校验逐请求 metadata。
- 第一个 result 嵌入用于 file selection 的 `sampling/createMessage`。
- 第一次 retry 校验 model result，并嵌入第二个 request。
- HMAC-protected `requestState` 在独立 requests 间携带 phase。
- 最终 result 使用 `resultType: "complete"`。

fake host model 让示例保持确定性。连接真实 host 时只替换 `fake_host_model`；server-side state machine 应保持确定性且可测试。

## 实际使用

从 repository root：

```bash
cd phases/13-tools-and-protocols/11-mcp-sampling/code
python3 main.py
python3 -m unittest discover tests -v
```

预期 checkpoints：

- Discovery 返回带 `ttlMs` 和 `cacheScope` 的 complete result。
- Tool discovery 返回相同的已排序 descriptor，其中有 `resultType`、server identity 和 cache hints。
- 缺少 capabilities 和不支持 versions 使用精确 `-32021` 与 `-32022` error data。
- 无 id notification 不产生 JSON-RPC response。
- Request ids 是 `[1, 2, 3]`，证明每轮 MRTR 独立。
- 前两个 results 是 `input_required`。
- 最终 result 是 `complete`，并包含 selected files 与 summary。
- 在 retry 中修改原始 arguments 会使 request-state check 失败。

## 拿去用

`outputs/skill-sampling-loop-designer.md` 现在是一份迁移 planner。它首先决定是否应移除 Sampling，改用 direct model integration。若需要兼容性，它会产出 MRTR rounds、state binding、capability gate、budget、validation 和 removal plan。

## 练习

1. 将 file-selection response 改为无效 JSON。确认 server 返回 `-32602`，而不是信任 model output。
2. 在第一条 call 与 retry 之间修改 `audience`。解释为何 sealed state 阻止跨请求复用。
3. 添加第三轮，让 host 批评 summary。将先前 summary 放在 signed state 中，并将整个 flow 限制为三轮。
4. 通过以 server-owned model adapter 替换 fake host callback 移除 Sampling。列出移交给 server 的 approval、billing 和 observability responsibilities。
5. 添加 expiry test，使用一个比 deadline 晚一秒的 state value。

## 关键术语

| 术语 | 在 2026-07-28 中的含义 |
|------|------------------------|
| Sampling | 已弃用的功能：要求 client model 提供 completion |
| MRTR | 当 request 需要 client input 时使用的无状态 retry pattern |
| `InputRequiredResult` | 带有 `resultType: "input_required"` 的 result |
| `inputRequests` | 由 server 分配的、嵌入 elicitation、sampling 或 roots requests 的 map |
| `inputResponses` | 以 `inputRequests` 相同 keys 组织的当前 round client results |
| `requestState` | client 原样回显、server 校验的不透明 server state |
| `resultType` | 现代 MCP results 的必需 discriminator |
| Direct model integration | 新 servers 需要 model inference 时推荐的替代方案 |
| Capability gate | 阻止发送 client 未声明支持的 embedded request 的规则 |
| Loop budget | 为 operation 允许的最大 rounds、tokens、bytes、time 和 spend |

## 旧版兼容性

固定在 2025-11-25 的 client 仍可通过 live connection 使用较早的 server-initiated `sampling/createMessage` flow。仅在 version-specific adapter 中保留该行为。不要将 sessionful path 作为 2026-07-28 server 的架构。

官方 SDKs 能够为较早 peers 转换现代 `input_required` handlers。该 shim 是 compatibility boundary，不是添加新 session-dependent logic 的许可。

## 延伸阅读

- [MCP 2026-07-28 Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [MCP Sampling deprecation](https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging)
- [MCP 2026-07-28 server discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
>>>>>>> main
