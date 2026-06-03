---
name: mcp-auth-wiring
description: 立起生产级 MCP 授权（RFC 8414、CIMD、7591、8707、7636 PKCE、9728、9207）——protected-resource 元数据、入册、JWKS 刷新，以及逐请求 token 校验。
version: 1.1.0
phase: 13
lesson: 18
tags: [mcp, oauth, cimd, dcr, jwks, rfc8414, rfc7591, rfc8707, rfc7636, rfc9728, rfc9207]
---

给定一个 MCP server 配置和一组 IdP 能力，输出构成一个生产级 MCP 授权层的鉴权表面和拒绝规则。

输入：

- `mcp_resource_url`——规范 resource URL（最具体的标识符；仅当用来区分共置的 server 时才保留 path），用作 `aud`，也用作 protected-resource 元数据的 `resource` 值。
- `idp_metadata_url`——IdP 的 `/.well-known/oauth-authorization-server`（或 OpenID Connect Discovery）URL。
- `idp_capabilities`——观察到的 `code_challenge_methods_supported`、`grant_types_supported`、`client_id_metadata_document_supported`（CIMD）、`registration_endpoint`（DCR）、`response_types_supported`、`authorization_response_iss_parameter_supported`（RFC 9207）的值。
- `tools`——MCP 工具列表，以及每个工具所需的 scope。

产出：

1. **拒绝门禁。** 任一硬性条件不满足就拒绝接线并停止：
   - `code_challenge_methods_supported` 里缺 `S256`（PKCE 没有降级模式）。
   - `grant_types_supported` 里缺 `authorization_code`。
   - `response_types_supported` 不是恰好 `["code"]`。
   - 不存在任何入册路径：预注册的 `client_id`、`client_id_metadata_document_supported: true`（CIMD）、`registration_endpoint`（DCR）三者一个都没有。任意一个就够——单单缺 DCR 不再构成拒绝（2025-11-25 把 DCR 降级为 `MAY`；CIMD 是首选默认）。

2. **Protected-resource 元数据文档**（RFC 9728），供 MCP server 在 `/.well-known/oauth-protected-resource` 发布。包含 `resource`、`authorization_servers`（issuer allow-list）、`scopes_supported`、`bearer_methods_supported: ["header"]`。

3. **HTTP 端点。**
   - `GET /.well-known/oauth-protected-resource`——返回 (2) 里的文档。
   - `POST /mcp`（MCP transport）——在任何工具分发之前跑 token 校验。
   - （仅 DCR 路径）`POST /register`——注册器，前面带一道限流检查。

4. **后台作业 + 例程。**
   - 一个计划 JWKS 刷新，把 `jwks_uri` 重新拉进缓存 `{keys, fetched_at}`。幂等；绝不铸密钥。AS 轮换；resource server 只刷新。默认 `0 */6 * * *`；对高轮换 IdP 收紧到 `*/15 * * * *`。
   - 一个 `validate` 例程——检查 `iss` allow-list、对照缓存的 JWKS 校验签名、`aud == mcp_resource_url`、`exp`、所需 scope。
   - 一条 step-up 签发路径——仅当工具列表里包含被某个用户起初未授予的 scope 把守的操作时才需要。

5. **缓存方案。** 每个被接受的 issuer 一条、以 `issuer` 为键的条目，持有 `{keys, fetched_at}`。记录读取模式：校验器读缓存，在 `kid` 未命中时兜底一次同步刷新（重新拉取，不是轮换——重新拉取是幂等的，无法被变成一个密钥创建 DoS）。

6. **Scope 映射。** 把每个工具映射到它所需的 scope。输出一张表：
   `| tool | required_scope | rationale |`。把破坏性工具归到它们自己的 scope 下；绝不把读 scope 重用给写工具。

7. **运行时拒绝规则**（校验器必须把这些编码进去）：
   - 当 `aud != mcp_resource_url` 时拒绝 → 401 `Bearer error="invalid_token", error_description="audience mismatch", resource_metadata="<prm_url>"`。
   - 当 `iss not in authorization_servers` 时拒绝。
   - 当兜底重新拉取一次后 `kid` 仍不在缓存的 JWKS 里时拒绝。
   - 当所需 scope 缺失时拒绝 → 403 `Bearer error="insufficient_scope", scope="<required>", resource_metadata="<prm_url>"`。
   - 拒绝任何没有 `code_verifier` 或 `resource` 参数的 token 请求。

硬性拒绝（下列一律不接线——拒绝请求并写明原因）：

- 以明文存储 `client_secret`。public client 用 `token_endpoint_auth_method: none`；confidential client 用 `private_key_jwt`。静态存储里和注册响应日志里都不留明文共享 secret。
- 在校验器上跳过 `aud` 检查。受众绑定（access-token 权限收窄）正是 RFC 8707 + RFC 9728 存在的全部理由。
- 把 JWKS 缓存未命中兜底接到一个"轮换并铸新"而不是重新拉取。它永远产生不出那个缺失的 `kid`，还会让攻击者掌控的 `kid` 值逼出无上限的密钥创建。兜底必须是幂等的刷新。
- 允许无 PKCE 的 authorization code 请求。OAuth 2.1 禁止它；校验器必须拒绝任何所存 authorization-code 记录里缺 `code_challenge` 的 `/token` 交换。
- 在没有刷新作业的情况下缓存 JWKS。要么计划刷新一起交付，要么这套鉴权表面不部署。
- 在没有 allow-list 的情况下信任 `iss` claim。任何接受来自任意 `iss` 的 token 的校验器，都让攻击者能立起自己的 IdP 并伪造 token。
- 把入站的 MCP token 转发给上游 API（token 透传）。如果 MCP server 调上游 API，它必须拿自己一个单独的 token；透传会制造 confused-deputy 问题。
- 以明文存储 `registration_access_token`。静态哈希存储；每次更新时要求呈递明文。

输出：一页纸的方案，含 protected-resource 文档、所选入册路径（CIMD / 预注册 / DCR）、HTTP 端点、JWKS 刷新作业、缓存方案、scope 映射表，以及编码进去的运行时拒绝规则。最后以针对所选 IdP 最可能浮现的那个单一部署阻塞缺口收尾——通常是 CIMD 是否已被支持，对企业 SSO 则退回到 DCR 可用性这一点。
