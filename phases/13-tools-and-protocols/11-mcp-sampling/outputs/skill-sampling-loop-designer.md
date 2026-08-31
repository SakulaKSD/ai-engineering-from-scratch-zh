<<<<<<< HEAD
---
name: sampling-loop-designer
description: Design a server-hosted agent loop using MCP sampling with the right modelPreferences, rate limits, and safety confirmations.
version: 1.0.0
phase: 13
lesson: 11
tags: [mcp, sampling, agent-loop, model-preferences]
---

Given a server-side algorithm that needs LLM reasoning (research, summarization, planning, triage), design an MCP sampling-based implementation.

Produce:

1. Loop structure. Number each sampling round, state the prompt shape, and the expected output type.
2. `modelPreferences` per round. Weight cost / speed / intelligence (sum 1.0) per round. A "pick files" round leans cost; a "synthesize" round leans intelligence.
3. Rate limit. Set `max_samples_per_tool` per invocation; justify the number.
4. Safety hooks. State where the client should show a confirmation dialog and what the refusal path does.
5. SEP-1577 inclusion. Decide whether to use tools inside sampling; if yes, flag drift risk and specify the tool list.

Hard rejects:
- Any loop without a rate limit. Loop bombs and resource theft risk.
- Any loop that sets `includeContext: "allServers"`. Cross-server leakage.
- Any loop where the server asks the client to generate content that is then fed back as a tool input without user confirmation. Confused-deputy vector.

Refusal rules:
- If the server has its own LLM credentials, ask whether sampling is actually needed; direct calls may be simpler.
- If the use case is a single one-shot tool call, refuse to design a sampling loop; sampling is for multi-round reasoning.
- If the user asks for a sampling loop that hides its intent from the end user, refuse categorically (covert sampling).

Output: a one-page design with the loop steps, modelPreferences per round, rate limit, and safety checklist. End with a note flagging any SEP-1577 (tools-in-sampling) drift risk relevant to the design.
=======
---
name: sampling-loop-designer
description: Migrate model-assisted MCP tools to direct inference or stateless 2026-07-28 MRTR with bounded compatibility sampling.
version: 2.0.0
phase: 13
lesson: 11
tags: [mcp, mrtr, sampling, stateless, migration]
---

为面向协议 revision `2026-07-28` 的 MCP server 设计 model-assisted behavior。

先做一个决定：server 能否直接集成 model provider？新设计中 Sampling 已弃用。除非使用 client model 与 credentials 是明确 product requirement，否则优先 direct integration。

产出：

1. 架构决策。选择 direct inference 或兼容性 Sampling，并说明原因。
2. Discovery 契约。展示带精确 `supportedVersions`、已声明 capabilities、`ttlMs` 和 `cacheScope` 的 `server/discover`。如果声明 tools，包含必需的确定性 `tools/list` descriptors，且有有效 object `inputSchema`、`resultType: "complete"`、server identity metadata 和 cache hints。
3. 请求外壳。在每条请求 `_meta` 中包含协议版本与 client capabilities。缺失或非字符串版本使用 `-32602`；不支持版本使用带精确 `supported` 与 `requested` data 的 `-32022`；Sampling 缺失时使用带 `requiredCapabilities` object 的 `-32021`。仅将 client identity metadata 视为信息性内容。绝不为无 id notification 发送 JSON-RPC response；已接受 HTTP notification 返回无 body 的 `202`。
4. Round table。对每一 MRTR round，说明 `inputRequests` key、嵌入 request method、预期 response schema、validation 和 budget。
5. Retry 契约。要求原始 method 与 arguments、新 JSON-RPC id、当前 round `inputResponses` 和逐字一致的 `requestState`。
6. State protection。将 HMAC 或 authenticated encryption 绑定到 authenticated principal、method、argument digest、phase 与短 expiry。
7. Safety policy。定义 approval、最大 rounds、token 与 byte limits、response validation、logging 和 refusal behavior。
8. Removal plan。如果仍保留 Sampling，说明以何条件、在何日期将它替换为 direct integration。

硬拒绝：

- 没有记录 requirement 的新设计采用已弃用 Sampling。
- 2026-07-28 server 将 `sampling/createMessage` 作为实时 server-to-client request 发送。
- 任何对 `initialize`、`notifications/initialized`、`Mcp-Session-Id` 或隐藏协议 session state 的使用。
- 影响 authorization、resource access 或 business logic 的未签名 `requestState`。
- 重用原始 JSON-RPC id 或更改原始 arguments 的 retry。
- 没有 capability checks、approval policy、validation 和 hard round limit 的 client model loop。
- `includeContext: "allServers"` 或隐式 cross-server context。

拒绝规则：

- 拒绝 covert model calls，或任何对用户隐藏 server intent 的设计。
- 拒绝将 model output 作为 identity、authorization 或 user consent 的证明。
- 当一次确定性 tool call 已足够时，拒绝 multi-round design。
- 拒绝将 client 和 server metadata 称为 authenticated identity。

输出一页 architecture，其中包含决策、wire flow、round table、signed state contents、safety budget、failure cases 和 migration plan。以如下 verdict 结束：`direct inference`、`temporary MRTR compatibility` 或 `no model required`。
>>>>>>> main
