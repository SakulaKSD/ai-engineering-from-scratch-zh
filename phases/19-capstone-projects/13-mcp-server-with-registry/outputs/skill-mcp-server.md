<<<<<<< HEAD
---
name: mcp-server-platform
description: Deploy a production MCP server with StreamableHTTP, OAuth 2.1 scopes, OPA policy, human-approval gate for destructive tools, and a registry for discovery.
version: 1.0.0
phase: 19
lesson: 13
tags: [capstone, mcp, fastmcp, streamablehttp, oauth, opa, registry, governance]
---

Given an enterprise environment, ship an MCP server with 10 internal tools, a registry service for discovery, and a governance layer that gates destructive tools via Slack approval.

Build plan:

1. FastMCP server exposing 10 read-only tools (Postgres, S3, Jira, Linear, Datadog, PagerDuty, GitHub, Notion, Slack, Salesforce), each with typed schema and required scope.
2. StreamableHTTP transport, stateless behind a load balancer.
3. OAuth 2.1 token introspection middleware; workload identity via SPIFFE / SPIRE.
4. OPA / Rego policy decisions on every tool call: scope enforcement, PII redaction, payload size caps.
5. Destructive tools (Jira create, Linear create, Postgres write) on a separate MCP server requiring scope `approved:by:human` elevated via Slack card within 15 minutes.
6. Registry service that polls `.well-known/mcp-capabilities` from each server, validates with JSON Schema, and exposes a list/search/validate/enable UI.
7. Per-tenant JSONL audit log with Presidio PII redaction before write.
8. 100-client load test demonstrating horizontal scale; pass MCP conformance suite.

Assessment rubric:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Spec conformance | StreamableHTTP + capability manifest passes MCP conformance tests |
| 20 | Security | Scope enforcement, OPA coverage across every tool, secret hygiene |
| 20 | Observability | Per-tool-call audit log with PII redaction on write |
| 20 | Scale | 100-client load test with horizontal scale demonstration |
| 15 | Registry UX | Discover / validate / enable-disable workflow exercised |

Hard rejects:

- Servers that require stateful sessions (violates 2026 StreamableHTTP stateless contract).
- Single-server topology where destructive tools share the same auth surface as read-only.
- Audit logs that persist raw PII.
- Ignoring the capability manifest; registry integration is a hard requirement.

Refusal rules:

- Refuse to deploy without OAuth; anonymous access is disqualifying.
- Refuse to ship destructive tools without the Slack approval flow.
- Refuse to expose a tool whose scope or description is not in the capability manifest.

Output: a repo containing the two MCP servers (read-only + destructive), the registry service, the Slack approval integration, the OPA policies, the 100-client load-test harness, conformance-test results, and a write-up describing which tools you considered exposing but did not (and why) plus the top three OPA rules that caught near-misses during dry-run.
=======
---
name: mcp-server-platform
description: 设计一台面向 MCP 2026-07-28 的无状态服务器，具备 Registry 元数据、实时发现、授权、策略、审计和扩展性证据。
version: 2.0.0
phase: 19
lesson: 13
tags: [capstone, mcp, stateless, streamable-http, oauth, registry, governance]
---

面对内部平台需求，设计一台以协议修订版 `2026-07-28` 为目标的无状态 MCP 服务器和治理边界。

构建计划：

1. 一个 schema 有效的 `server.json`，其反向 DNS 名称符合发布者已经认证的命名空间。
2. 强制实现 `server/discover`，用于实时版本、capabilities、扩展和服务器身份。
3. 每个请求的 `_meta` 都带版本和 client capabilities；每个结果都带 `resultType` 和服务器身份。
4. 确定性的 `tools/list`，带 `ttlMs` 与 `cacheScope`。
5. 只接受 POST 的 Streamable HTTP，具备必需的版本、method 和 name headers；没有协议 sessions、GET stream、session DELETE 或 replay header。
6. 授权在每次调用时校验 issuer、audience、expiry 和 scopes。
7. 针对 actor、工具、目标和规范化 arguments 的策略。将高风险审批绑定到精确动作与 expiry，然后证明改动一个 argument 会拒绝重放。
8. 位于模型可见 context 之外的脱敏 audit 和 trace 证据。
9. 一个验证 `server.json`、probe `server/discover` 并报告元数据/运行时漂移的 Registry adapter。
10. 两个可互换副本和一个无需 session affinity 的并发负载 probe。

评估量表：

| 权重 | 标准 | 衡量方式 |
|:-:|---|---|
| 25 | 协议正确性 | 无状态信封、发现、结果、headers 和负向场景 |
| 20 | 授权 | issuer、audience、expiry、scope 和精确动作审批场景 |
| 15 | Registry 完整性 | 有效 `server.json`、实时 probe 和漂移报告 |
| 15 | 策略和安全 | 允许、拒绝、畸形、过期审批和敏感数据场景 |
| 15 | 规模 | 两个副本，无 affinity 依赖，另加取消和恢复 |
| 10 | 可审计性 | 脱敏的接收端 audit 和 trace 证据 |

硬性拒绝：

- 使用 `initialize`、`notifications/initialized` 或 `Mcp-Session-Id` 的当前 MCP 设计。
- 将 `server.json` 当作实时能力发现，或虚构 `.well-known/mcp-capabilities` 是 MCP 要求。
- 发布名称位于该发布者认证命名空间之外的服务器。
- 接受未校验 issuer 和 audience 或 resource 的 token。
- 将工具注释或聊天审批当作授权。
- 持久化 secrets 或原始敏感数据的 audit 记录。

拒绝规则：

- 拒绝仅凭本地模拟就声称生产就绪。
- 拒绝暴露没有策略和动作绑定审批证据的会改变状态工具。
- 拒绝发布指向无法验证实时发现的 endpoint 的元数据。

输出：一份构建计划和证据矩阵，覆盖发布元数据、实时发现、无状态 transport、工具 schemas、授权、策略、审批、审计和规模。以风险最高的边界，以及证明它会 fail closed 的精确失败测试结尾。
>>>>>>> main
