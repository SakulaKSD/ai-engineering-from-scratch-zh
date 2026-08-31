<<<<<<< HEAD
# Skills 与 Agent SDK——Anthropic Skills、AGENTS.md、OpenAI Apps SDK

> MCP 说"存在哪些工具"。Skills 说"怎么做一个任务"。2026 年的栈把两者分层叠在一起。Anthropic 的 Agent Skills（开放标准，2025 年 12 月）以 SKILL.md 交付，带渐进式披露。OpenAI 的 Apps SDK 是 MCP 加 widget 元数据。AGENTS.md（如今在 6 万+ 个 repo 里）坐在 repo 根，作为项目级 agent 上下文。本课点名各自覆盖什么，并构建一个能跨 agent 流转的极简 SKILL.md + AGENTS.md 包。

**类型：** Learn
**语言：** Python（标准库，SKILL.md 解析器与加载器）
**前置要求：** 阶段 13 · 07（MCP server）
**预计时间：** ~45 分钟

## 学习目标

- 区分三个层：AGENTS.md（项目上下文）、SKILL.md（可复用知识）、MCP（工具）。
- 写一个带 YAML frontmatter 和渐进式披露的 SKILL.md。
- 以文件系统方式把 skill 加载进一个 agent 运行时。
- 把一个 skill 和一个 MCP server、一个 AGENTS.md 组合起来，让一个包在 Claude Code、Cursor 和 Codex 里都能用。

## 问题背景

一个工程师把一套写发布说明的工作流提炼成一个多步 prompt："读最近合入的 PR。按领域分组。各自摘要。按团队风格写一条 changelog 条目。发到 Slack 草稿。"他们把它放进了团队的一个 Notion 文档。

现在他们想从 Claude Code、Cursor 和 Codex CLI 用这个工作流。每个 agent 加载指令的方式不同：Claude Code 的 slash-command、Cursor 的 rule、Codex 的 `.codex.md`。工程师把工作流拷了三遍，维护三份。

AGENTS.md 和 SKILL.md 一起修掉这个：

- **AGENTS.md** 坐在 repo 根。每个兼容的 agent 在会话开始时读它。"这个项目怎么运作？有什么约定？哪些命令跑测试？"
- **SKILL.md** 是一个可移植的包：YAML frontmatter（name、description）+ markdown 正文 + 可选资源。支持 skill 的 agent 按名字按需加载它们。
- **MCP**（阶段 13 · 06-14）处理 skill 需要调用的工具。

三个层，一个可移植的产物。

## 核心概念

### AGENTS.md（agents.md）

2025 年底上线，到 2026 年 4 月被 6 万+ 个 repo 采纳。repo 根一个文件。格式：

```markdown
# Project: my-service

## Conventions
- TypeScript with strict mode.
- Use Pydantic for models on the Python side.
- Tests run with `pnpm test`.

## Build and run
- `pnpm dev` for local dev server.
- `pnpm build` for production bundle.
```

agent 在会话开始时读这个，用它来为那个项目校准自己的行为。2026 年每个编码 agent 都支持 AGENTS.md：Claude Code、Cursor、Codex、Copilot Workspace、opencode、Windsurf、Zed。

### SKILL.md 格式

Anthropic 的 Agent Skills（2025 年 12 月作为开放标准发布）：

```markdown
---
name: release-notes-writer
description: Write a changelog entry for the latest merged PRs following this project's style.
---

# Release notes writer

When invoked, run these steps:

1. List PRs merged since the last tag. Use `gh pr list --base main --state merged`.
2. Group by label: feature, fix, chore, docs.
3. For each PR in each group, write one line: `- <title> (#<num>)`.
4. Draft the release notes and stage them in CHANGELOG.md.

If the user says "ship", run `git tag vX.Y.Z` and `gh release create`.

## Notes

- Never include commits without a PR.
- Skip "chore" entries from the public changelog.
```

frontmatter 声明 skill 的身份。正文是 skill 加载时展示给模型的 prompt。

### 渐进式披露

Skill 可以引用 agent 仅在需要时才取的子资源。例子：

```
skills/
  release-notes-writer/
    SKILL.md
    style-guide.md
    template.md
    scripts/
      generate.sh
```

SKILL.md 说"风格规则见 style-guide.md"。agent 仅在 skill 正在运行时才拉 style-guide.md。这避免了用模型可能不需要的细节把 prompt 撑大。

### 文件系统发现

agent 运行时扫描已知目录寻找 SKILL.md 文件：

- `~/.anthropic/skills/*/SKILL.md`
- 项目的 `./skills/*/SKILL.md`
- `~/.claude/skills/*/SKILL.md`

加载靠文件夹名和 frontmatter 的 `name`。Claude Code、Anthropic Claude Agent SDK 和 SkillKit（跨 agent）都遵循这个模式。

### Anthropic Claude Agent SDK

`@anthropic-ai/claude-agent-sdk`（TypeScript）和 `claude-agent-sdk`（Python）在会话开始时加载 skill，把它们作为运行时内可调用的"agent"暴露。当用户触发某个 skill 时，agent 循环分发给它。

### OpenAI Apps SDK

2025 年 10 月上线；直接建在 MCP 上。把 OpenAI 之前的 Connectors 和 Custom GPT Actions 统一到单一开发者表面下。一个 Apps SDK app 是：

- 一个 MCP server（tools、resources、prompts）。
- 加给 ChatGPT UI 的 widget 元数据。
- 加一个可选的、给交互式表面用的 MCP Apps `ui://` 资源。

同样的协议，更丰富的 UX。

### 经由 SkillKit 的跨 agent 可移植性

SkillKit 这类工具和类似的跨 agent 分发层，把单个 SKILL.md 翻译成 32+ 个 AI agent（Claude Code、Cursor、Codex、Gemini CLI、OpenCode 等）各自的原生格式。一个事实标准；许多消费方。

### 三层栈

| 层 | 文件 | 何时加载 | 目的 |
|-------|------|-------------|---------|
| AGENTS.md | repo 根 | 会话开始 | 项目级约定 |
| SKILL.md | skills 目录 | skill 被触发 | 可复用工作流 |
| MCP server | 外部进程 | 需要工具时 | 可调用动作 |

三者都组合得起来：agent 在会话开始时读 AGENTS.md，用户触发一个 skill，skill 的指令含 MCP 工具调用，agent 经由一个 MCP client 分发。

```figure
t3-skill-layers
```

## 实际使用

`code/main.py` 交付一个标准库 SKILL.md 解析器和加载器。它在 `./skills/` 下发现 skill，解析 YAML frontmatter 加 markdown 正文，产出一个按 skill 名作键的 dict。它接着模拟一个按名字触发 `release-notes-writer` 的 agent 循环。

要看什么：

- YAML frontmatter 用一个极简标准库解析器解析（无 `pyyaml` 依赖）。
- skill 正文一字不差地存着；agent 在触发时把它前置到 system prompt。
- 渐进式披露经由一个 `read_subresource` 函数演示，它按需拉取被引用的文件。

## 拿去用

本课产出 `outputs/skill-agent-bundle.md`。给定一个工作流，这个 skill 产出组合的 SKILL.md + AGENTS.md + MCP-server 蓝图包，跨 agent 可移植。

## 练习

1. 跑 `code/main.py`。在 `skills/` 下加第二个 skill，确认加载器把它收进来。

2. 为本课程 repo 写一个 AGENTS.md。包含测试命令、风格约定，以及阶段 13 的心智模型。

3. 把你团队内部文档里的一个多步工作流移植进一个 SKILL.md。验证它在 Claude Code 里加载。

4. 手动把这个 skill 翻译成 Cursor 和 Codex 的原生 rule 格式。数格式之间的 diff——这就是 SkillKit 自动化的那个翻译表面。

5. 读 Anthropic Agent Skills 博文。找出 Claude Agent SDK 里一个本课加载器没覆盖的特性。（提示：agent 子调用。）

## 关键术语

| 术语 | 大家嘴上怎么说 | 它实际是什么 |
|------|----------------|------------------------|
| SKILL.md | "skill 文件" | YAML frontmatter 加 markdown 正文，由 agent 运行时加载 |
| AGENTS.md | "repo 根的 agent 上下文" | 会话开始时读的项目级约定文件 |
| Progressive disclosure | "懒加载子资源" | skill 正文引用仅在需要时才拉的文件 |
| Frontmatter | "顶部的 YAML block" | `---` 分隔符里的元数据（name、description） |
| Claude Agent SDK | "Anthropic 的 skill 运行时" | `@anthropic-ai/claude-agent-sdk`，加载 skill 并路由 |
| OpenAI Apps SDK | "MCP + widget 元数据" | OpenAI 建在 MCP 加 ChatGPT UI 钩子上的开发表面 |
| Skill discovery | "文件系统扫描" | 遍历已知目录找 SKILL.md，按名字作键 |
| Cross-agent portability | "一个 skill 多个 agent" | 经由 SkillKit 风格工具把一个 SKILL.md 翻译到 32+ 个 agent |
| Agent Skill | "可移植知识" | MCP 工具概念之外的可复用任务模板 |
| Apps SDK | "MCP 加 ChatGPT UI" | Connectors 和 Custom GPT 在 MCP 上统一 |

## 延伸阅读

- [Anthropic — Agent Skills announcement](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — 2025 年 12 月发布
- [Anthropic — Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — SKILL.md 格式参考
- [OpenAI — Apps SDK](https://developers.openai.com/apps-sdk) — 给 ChatGPT 的基于 MCP 的开发者平台
- [agents.md](https://agents.md/) — AGENTS.md 格式与采纳清单
- [Anthropic — anthropics/skills GitHub](https://github.com/anthropics/skills) — 官方 skill 示例
=======
# Agent Skills：可移植契约与运行时边界

> Skill 不是换了更好文件名的长 prompt。它是由指令、资源和可执行辅助工具组成的可发现包，通过运行时契约进入 agent 上下文。

**类型：** Build
**语言：** Python（标准库）
**前置要求：** 第 13 阶段 · 01（工具接口），第 13 阶段 · 05（工具 Schema 设计）
**预计时间：** 约 90 分钟

## 学习目标

- 定义 agent skill，并与 prompt、仓库指令、工具、hook、subagent 和插件区分开。
- 阅读可移植的 `SKILL.md` 契约，并把它与运行时专属扩展分开。
- 将发现、选择、激活、资源加载、工具使用和验证解释为不同生命周期阶段。
- 在运行时将 skill 包放入 agent 目录前验证它。
- 为具体任务选择 skill、MCP 工具、hook、subagent 或普通代码。

## 十分钟首次成功

先做这个，再读长篇解释。你会创建一个小 skill，将完整审查器 Bundle 安装到真实 agent host，调用它、验证结果，再移除它。这以可观察结果证明整个生命周期。

### 真实 host 实验的预检

真实 host 检查点需要 Node.js、`npx`、Python 3、一个选定的支持 skill 的 host，以及对安装器中所选项目或用户作用域的写入权限。先验证本地命令：

```bash
node --version
npx --version
python3 --version
```

安装前确定 host 与作用域。若有条件不可用，请在网站阅读本课，或继续下面的手动包练习。该替代练习能教授契约，却不能证明 host 发现、调用、Bundle 脚本执行或卸载行为。将这些观察标为待验证。

### 1. 从空工作目录开始

在任何存放学习工作的父目录中运行：

```bash
mkdir -p agent-skills-first-run
cd agent-skills-first-run
TARGET_ROOT="$(pwd -P)"
printf 'TARGET_ROOT=%s\n' "$TARGET_ROOT"
ls -A
```

最后一条命令不应输出任何内容。若它输出文件，请选择另一个空目录，让审查有清晰边界。

为第一个 skill 创建目录：

```bash
mkdir -p my-first-skill
```

创建内容如下的 `my-first-skill/SKILL.md`：

```markdown
---
name: my-first-skill
description: Turn rough meeting notes into a compact decision record when the user asks to capture a technical decision.
---

# Decision record

Extract the decision, context, alternatives, owner, and next review date.
If the notes do not contain a decision, ask one clarifying question instead
of inventing one.
```

验证文件创建在预期目录中：

```bash
test -f my-first-skill/SKILL.md
```

无输出且退出码为 0，表示文件存在。

### 2. 安装完整审查器 Bundle

保持在 `agent-skills-first-run` 并运行：

```bash
npx skills add fancyboi999/ai-engineering-from-scratch-zh --skill skill-contract-reviewer --full-depth
```

选择所用的 agent host 与作用域。安装器应列出 `skill-contract-reviewer` 和写入目标。此课的 skill 是带 references、脚本和资源的嵌套 Bundle，所以需要 `--full-depth`。

将 `SKILL_ROOT` 设为安装器报告的绝对目录。它必须包含已安装的 `SKILL.md`，不是课程源码目录，也不是当前工作区：

```bash
# Replace the placeholder with the destination printed by the installer.
SKILL_ROOT="$(cd "/absolute/path/to/skill-contract-reviewer" && pwd -P)"
test -f "$SKILL_ROOT/SKILL.md"
printf 'SKILL_ROOT=%s\n' "$SKILL_ROOT"
```

若 agent 会话已打开，请新开会话，或使用该 host 的 skill 重新扫描命令。不要假定每个 host 都会热加载目录。

### 3. 显式调用它

在已安装的 agent 中，以 `agent-skills-first-run` 为工作目录，使用 host 支持的语法：

| Host | 显式调用 |
|---|---|
| Codex | `skill-contract-reviewer`，或从 `/skills` 选择它，再提供审查请求 |
| Claude Code | `/skill-contract-reviewer` 后跟审查请求 |
| 可移植兜底方式 | `Use skill-contract-reviewer to review the target package.` |

在请求中使用 `SKILL_ROOT` 与 `TARGET_ROOT` 输出的绝对值。要求 host 执行前展开它们，并显示精确解析后的命令，而不是依赖进程工作目录的命令：

```text
Use skill-contract-reviewer to review <TARGET_ROOT>/my-first-skill. The installed bundle root is <SKILL_ROOT>. Run python3 <SKILL_ROOT>/scripts/check_skill.py <TARGET_ROOT>/my-first-skill. Before running it, show the fully resolved argv. Return the validation report, selected primitives, and one sentence for each selection. Include the resolved script path, resolved target path, cwd, argv, and exit code as execution evidence.
```

解析后的命令应如下，不能留下占位符：

```bash
python3 "/absolute/install/path/skill-contract-reviewer/scripts/check_skill.py" \
  "/absolute/workspace/path/agent-skills-first-run/my-first-skill"
```

成功结果具备三项属性：

1. Host 能按名称找到 `skill-contract-reviewer`。
2. 审查器读取包契约并运行随附验证器。
3. 响应包含样例无结构性错误的验证报告，以及有理由的原语选择。

执行证据还必须列出脚本路径、目标路径、cwd、精确参数向量和退出码。没有这些字段的流畅报告，无法证明已安装的配套脚本运行过。

若 host 报告 skill 不可用，检查安装目标，重新扫描或重启一次，再重试显式请求。不要为掩盖安装失败而重写 skill 描述。

### 4. 探测隐式选择

新开一个 agent turn，在不点名 skill 的情况下输入同一任务：

```text
Review <TARGET_ROOT>/my-first-skill as a reusable agent package and tell me whether its package contract is valid.
```

如果 host 会暴露所选 skills，记录它是否选择 `skill-contract-reviewer`。如果 host 不暴露路由信息，将隐式选择标为未验证。显式调用是可移植的兜底方式。

### 5. 清理

只移除已安装的审查器 Bundle：

```bash
npx skills remove skill-contract-reviewer
```

选择与安装时相同的 host 和作用域。重新扫描或新开会话后，对 `skill-contract-reviewer` 的显式请求应报告它不可用。保留 `my-first-skill` 供后续课程使用，或在完成 track 后移除实验目录。

## 问题背景

假设团队有可靠的发布工作流：它查找已合并变更，检查迁移说明，更新 changelog，运行打包命令，并产出审查清单。

将该工作流写成一个 prompt，复制很容易，运行却很难。它没有稳定标识、发现规则、资源边界、可测试的包形状，也回答不了基本问题：谁可调用它？模型何时应选择它？它能运行哪些脚本？哪些文件可信？上下文压缩后保留什么？

相反的错误是把每条可复用指令当作 skill。仓库约定、确定性自动化、外部工具、事件 hook 与被委派的 agent 解决不同问题。将它们都塞进 `SKILL.md`，会得到看似可移植、实则依赖某个 host 未文档化行为的目录。

第一项工程任务是分类。先决定产物是什么，再决定如何打包。

## 核心概念

### Skills 承载过程性知识

Agent skill 是以 `SKILL.md` 为入口的目录。入口文件包含 YAML frontmatter，后面跟 Markdown 指令。目录还可包含 references、脚本和资源。

```figure
skill-package-anatomy
```

可部署单元是整个目录，而非单独的 Markdown 文件。即使 frontmatter 能解析，复制出的 `SKILL.md` 缺少 references 也是损坏的包。

### 相邻抽象

| 产物 | 主要职责 | 何时加载或运行 | 不应冒充什么 |
|---|---|---|---|
| Prompt | 塑造一次模型交互 | 由应用或用户加入 | 带资源的版本化包 |
| 仓库指令 | 解释一个代码库的常设规则 | 编码运行时进入该作用域 | 可复用任务工作流 |
| Agent skill | 提供可复用过程性知识 | 显式或隐式激活 | 硬性授权边界 |
| MCP 工具 | 暴露有类型的远程能力 | 模型或应用调用它 | 详细操作流程 |
| Hook | 在事件发生时运行确定性逻辑 | 声明事件发生 | 概率性模型路由 |
| Subagent | 以独立上下文和状态委派工作 | 编排器创建或调用它 | 静态指令 Bundle |
| 插件 | 分发更大的运行时扩展 | Host 安装或启用它 | 可移植 skill 契约本身 |
| 学习型 skill 库 | 存储从经验发现的行为 | 策略检索既有程序或轨迹 | 基于标准的 `SKILL.md` 包 |

发布 skill 可以告诉 agent 如何检查发布；MCP server 可暴露发布注册表；Hook 可禁止直接 push；Subagent 可独立审计候选项。这些组件能组合，是因为它们保持不同职责。

### “skill”一词指代两种概念

研究系统有时把学得的程序、成功轨迹或环境专属策略片段称为 skill。Agent 能在探索中创建这些产物，按任务相似度检索、执行它们，并按反馈修订库。第 14 阶段 · 10 构建的是这类终身学习库。

本 mini-track 的 Agent Skill 不同。它是人工编写的包，带有声明的文件系统契约、目录元数据、渐进式披露、运行时中介的调用和 host 控制的工具。Agent 可以生成或改进它，但格式不要求学习。

| 维度 | Agent Skill 包 | 学习型 skill 库 |
|---|---|---|
| 基本单元 | `SKILL.md` 目录 | 程序、策略、轨迹或记忆记录 |
| 创建方式 | 人工编写、生成或策展 | 通常从环境经验发现 |
| 选择方式 | 目录描述加运行时策略 | 基于任务状态的检索或策略 |
| 执行方式 | 模型遵循指令并调用 host 工具 | 环境运行已存储的行为或代码产物 |
| 可移植性 | 包契约可跨兼容 host 使用 | 常绑定于一个环境和动作空间 |
| 评估 | 路由、产物、安全性与 host 兼容性 | 奖励、成功率、迁移性与库增长 |

两种概念都封装可复用能力。不能只因共享名字，就让它们共享实现层面的主张。

### 可移植核心

Agent Skills 规范要求两个 frontmatter 字段：

```yaml
---
name: release-readiness
description: Inspect a release candidate when the user asks whether a version is ready to publish.
---
```

`name` 是稳定标识符，必须符合规范命名规则并与父目录匹配。`description` 既是文档也是路由元数据，应说明 skill 做什么、何时适用。

可移植的可选字段：

| 字段 | 用途 | 可移植性说明 |
|---|---|---|
| `license` | 声明包条款 | 核心规范 |
| `compatibility` | 声明环境要求 | 核心规范 |
| `metadata` | 携带字符串值扩展数据 | 核心规范 |
| `allowed-tools` | 建议预先批准的工具 | 实验性；host 支持不同 |

Markdown 正文承载操作指令，应定义工作流、决策点、失败行为及支持资源的直接路径。

```markdown
# Release readiness

Use this workflow for a release candidate, not for ordinary development builds.

1. Read `references/release-policy.md`.
2. Run `python3 scripts/inspect_release.py --format json`.
3. Stop if the report contains a blocking failure.
4. Produce the checklist from `assets/release-checklist.md`.
5. Ask for approval before any publish or tag action.
```

### 运行时扩展是第二层

有些 host 接受额外 frontmatter 或配套配置。这些字段可能有用，但不会自动具备可移植性。

| 行为 | Host 扩展示例 | 可移植核心？ |
|---|---|:---:|
| 从模型路由中隐藏 skill，同时保留用户直接调用 | `disable-model-invocation` | 否 |
| 从用户命令菜单隐藏 skill，同时允许模型路由 | `user-invocable` | 否 |
| 在命令菜单显示参数帮助 | `argument-hint` | 否 |
| 在委派上下文运行 skill | `context`、`agent` | 否 |
| 固定模型或推理设置 | `model`、`effort` | 否 |
| 注册生命周期自动化 | `hooks` | 否 |
| 在 Codex 禁用隐式调用 | `agents/openai.yaml` 策略 | 否 |

把每项扩展视为适配器。无需它也要让核心工作流有效，记录兜底方式，并测试消费它的 host。运行时可能忽略未知字段、拒绝它，或仅保留它而不实现行为。

### Frontmatter 是可执行元数据

元数据会在读取 skill 正文前改变系统行为。

- 格式错误的 `name` 可能导致发现失败。
- 含糊的 `description` 可能将请求错误路由。
- 仅供人类使用的标记可能把 skill 从模型目录移除。
- 工具许可可改变 host 是否请求权限。
- 上下文设置可将执行移到独立 agent 会话。

像审查配置代码一样审查 frontmatter：验证它、为它版本化，并在 eval 中覆盖其行为。

### Skill 生命周期

```figure
skill-runtime-lifecycle
```

每个箭头都是有自身失败模式的边界。

1. **发现**在配置位置找到候选包。
2. **验证**在目录发布前拒绝格式错误或不安全的包。
3. **编目**暴露精简的 `name` 与 `description`，而非完整包。
4. **选择**决定该 skill 是否相关。
5. **激活**将正文加载到模型可见上下文。
6. **披露**只在分支需要时读取 references 或资源。
7. **执行**遵循 host 的权限与隔离规则使用工具。
8. **验证**独立于模型声明检查产出结果。

混淆这些阶段会形成错误心智模型。已发现的 skill 不等于已激活；已激活的 skill 不等于有权做其描述的一切；获准的工具调用也不等于结果正确。

### Skills 与工具相互正交

MCP 回答：“这个应用可调用哪些能力，它们的 Schema 是什么？”Skill 回答：“Agent 应如何处理这类任务？”

```figure
skill-tool-orthogonality
```

Skill 可提及工具，但实际能力注册表归 host 所有。若工具缺失，skill 应说明兜底方案或明确失败；绝不可暗示写上能力名称就会创建能力。

### Skills 与仓库指令的作用域不同

仓库指令描述的是已身处的环境：命令、约定、生成文件和边界。Skill 为可出现于许多仓库的任务提供可复用流程。

两者同时适用时，活跃用户请求与仓库规则会约束 skill。通用重构 skill 不得覆盖禁止编辑生成文件的仓库规则。

### Skills 不会彼此 import

一个 skill 可指示 agent 调用另一个，但这不是语言层面的 import。第二个 skill 仍须经过运行时发现、资格检查、激活、权限和上下文处理。

将跨 skill 依赖写成可观察工作流边：

```markdown
After producing the candidate changelog, invoke the `release-risk-review` skill.
Pass the candidate path and require a blocking or non-blocking verdict.
If that skill is unavailable, stop and report the missing dependency.
```

这样依赖可测试，也给 host 执行策略的机会。

## 动手构建

`code/main.py` 实现小型、面向标准的验证器和产物选择器。它只使用标准库，让每条规则都清晰可见。

验证器提供：

- `parse_frontmatter(text)`：将元数据与正文分开。
- `validate_skill_text(text, directory_name, allowed_runtime_extensions=())`：检查必填字段、命名、未知扩展、正文存在性和可移植限制。
- `ValidationIssue` 与 `SkillReport`：返回结构化证据而非不透明布尔值。
- `FrontmatterSyntaxError`：处理无法安全解释的输入。

选择器提供 `TaskShape` 和 `select_primitives(task)`，将任务需求映射到普通代码、仓库指令、skill、hook、subagent 或 MCP 工具。

运行实验：

```bash
cd "$(git rev-parse --show-toplevel)"
cd phases/13-tools-and-protocols/22-skills-and-agent-sdks
python3 code/main.py
python3 -m unittest discover -s code/tests -v
```

该命令块需要本地 clone，且须从 clone 内任意位置开始，让 `git rev-parse --show-toplevel` 能解析仓库根目录。

演示会为一个有效可移植 skill、一个 host 扩展 skill、一个无效包和若干任务形状决策打印 JSON。检查 issue 代码。包验证器应说明如何修复产物，而不替作者猜测。

### 验证顺序很重要

先验证开销低的结构事实，再验证更深的内容规则：

```figure
skill-validation-order
```

该顺序可避免次要错误掩盖最先损坏的不变量。

## 实际使用

写 skill 前，填写此决策卡：

| 问题 | 若为“是” | 可能的原语 |
|---|---|---|
| 是否需要跨多个步骤、可复用的模型判断？ | 流程稳定但决策会变化 | Skill |
| 是否必须在每次事件触发时执行？ | 漏掉一次也不可接受 | Hook 或应用代码 |
| 模型是否需要有类型化输入的外部能力？ | 操作位于模型上下文之外 | 工具或 MCP server |
| 工作是否需要隔离的上下文、状态或所有权？ | 独立 worker 返回有界结果 | Subagent |
| 指导是否专属于一个仓库？ | 它描述本地命令和约束 | 仓库指令 |
| 一次交互是否足够？ | 不需要包生命周期 | Prompt |

许多生产工作流会使用不止一行。该卡可避免某个产物假装提供所有属性。

## 拿去用

本课在 `outputs/` 下产出 `skill-contract-reviewer` Bundle，包含：

- 审查候选 skill 包的可移植 `SKILL.md`；
- 可移植契约与原语选择的参考清单；
- 确定性验证脚本；
- 覆盖 prompt、skill、工具、hook、普通代码和 subagent 的任务形状 fixture。

安装完整 Bundle，而非只安装入口文件：

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/install_skills.py /tmp/aiefs-skills --phase 13 --type skill
```

课程安装器会报告每个复制的第 13 阶段 skill，并写入 `/tmp/aiefs-skills/manifest.json`。这个干净目标检查包形状；上方首次成功循环在真实 host 中检查发现与调用。

后续课程深入每个生命周期阶段：第 24 课构建发现和渐进式披露；第 25 课构建调用策略与路由；第 26 课分离权限与沙箱；第 27 课把整包变成经评估的发布产物。

## 练习

1. 用 `TaskShape` 为自己团队的五个工作流分类。凡是选择多于一个原语，都要给出理由。
2. 添加边界测试，证明 500 字符的 `compatibility` 值通过，而 501 字符值作为规范错误失败。
3. 向 allowlist 添加一个运行时扩展。编写测试，证明同一文件仍可与只含可移植部分的 skill 区分。
4. 将 400 行 prompt 拆为 `SKILL.md`、一个 reference、一个脚本契约和一个输出模板。让每个文件只负责一种信息。
5. 为引用不可用 MCP 工具的 skill 设计失败响应。不要悄悄替换成权限更宽的工具。
6. 审查已有 skill，把每句标为路由、流程、策略、reference 指针或输出契约。移动不属于其中的内容。

## 关键术语

| 术语 | 常见说法 | 实际含义 |
|---|---|---|
| Agent skill | “保存下来的 prompt” | 含过程性指令和可选资源的可发现目录 |
| 可移植核心 | “每个运行时共有的字段” | Agent Skills 规范定义的契约 |
| 运行时扩展 | “额外 frontmatter” | 行为需要兼容适配器的 host 专属配置 |
| 激活 | “skill 已运行” | Skill 正文已进入模型可见上下文；执行可能稍后发生 |
| Skill 依赖 | “import 另一个 skill” | 具有可用性与策略检查、由运行时中介的调用边 |
| 工具契约 | “函数 Schema” | 一个能力的输入、输出、权限、副作用、错误与证据 |

## 延伸阅读

- [Agent Skills specification](https://agentskills.io/specification)：可移植目录和 frontmatter 契约。
- [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices)：范围、指令和资源组织。
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)：当前 Codex 的发现与调用行为。
- [Claude Code skills](https://code.claude.com/docs/en/skills)：某个运行时的调用、参数、工具与委派上下文扩展。
>>>>>>> main
