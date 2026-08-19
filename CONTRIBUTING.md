# 贡献指南

课程、翻译、修复、产出物——都欢迎。一个 PR 只做一件事，评审更快，贡献者计数和署名也能正确归属。

## 重要：README 和 ROADMAP 喂给网站

`site/build.js` 会解析 `README.md`、`ROADMAP.md` 和 `glossary/terms.md` 来生成 `site/data.js`。任何动到这些文件的 PR，都必须保持下面两类格式完好：

- 阶段标题，采用 `### Phase N: Name \`X lessons\`` 形式，或
  `<details><summary><b>Phase N — Name</b> ... <code>X lessons</code> ... <em>Description</em></summary>` 形式。
- 课程表格采用 `| # | Lesson | Type | Lang |` 的列结构（顶点项目表格则是
  `| # | Project | Combines | Lang |`）。`Lang` 列可以是纯文本（`Python, TypeScript`），也可以是早期的 emoji 旗标
  （`🐍 🟦 🦀 🟣 ⚛️`）；两者对解析器是等价的。
- ROADMAP 的状态字符（`✅`、`🚧`、`⬚`）出现在阶段标题和课程行上。
  不要把它们换成文字——解析器是按这几个确切字符来识别的。

编辑这些文件后运行 `node site/build.js`；如果你的改动在结构上是安全的，`git diff site/data.js`
应该只显示时间戳的变化。

## 贡献方式

### 1. 新增一节课程

每节课程位于 `phases/XX-phase-name/NN-lesson-name/`，结构如下：

```
NN-lesson-name/
├── code/           至少一个可运行的实现
├── notebook/       用于实验的 Jupyter notebook（可选）
├── docs/
│   └── en.md       课程文档（必需）
└── outputs/        本节课产出的提示词、技能或智能体（如适用）
```

**课程文档格式**（`en.md`）：

```markdown
# Lesson Title

> One-line motto — the core idea in one sentence.

## The Problem

Why does this matter? What can't you do without this?

## The Concept

Explain with diagrams, visuals, and intuition. Code comes later.

## Build It

Step-by-step implementation from scratch.

## Use It

Now use a real framework or library to do the same thing.

## Ship It

The prompt, skill, agent, or tool this lesson produces.

## Exercises

1. Exercise one
2. Exercise two
3. Challenge exercise
```

### 2. 新增一份翻译

在任意课程的 `docs/` 文件夹里新建一个文件：

```
docs/
├── en.md    （英文——始终必需）
├── zh.md    （中文）
├── ja.md    （日文）
├── es.md    （西班牙文）
├── hi.md    （印地文）
└── ...
```

保持与英文版相同的结构。翻译内容，不要翻译代码。

### 3. 新增一个产出物

如果某节课程应该产出一个可复用的提示词、技能、智能体或 MCP 服务器：

1. 在课程的 `outputs/` 文件夹里创建它
2. 在顶层 `outputs/` 索引中加一条引用

**提示词格式：**

```markdown
---
name: prompt-name
description: What this prompt does
phase: 14
lesson: 01
---

[System prompt or template here]
```

**技能格式：**

```markdown
---
name: skill-name
description: What this skill teaches
version: 1.0.0
phase: 14
lesson: 01
tags: [agents, loops]
---

[Skill content here]
```

### 4. 修复缺陷或改进现有课程

- 修复跑不起来的代码
- 改进讲解
- 加上更好的图示
- 更新过时的信息

### 5. 新增练习或项目

随时欢迎更多练习和项目，尤其是那些把多个阶段串联起来的。

## 规范

- **代码必须能跑。** 每个代码文件都应该用列出的依赖无报错地执行。
- **代码里不写注释。** 代码应当自解释。讲解放到文档里。
- **用最适合的语言。** 别在 TypeScript 或 Rust 更合适的地方硬塞 Python。
- **先从零实现。** 在展示框架版本之前，总是先用第一性原理把概念实现一遍。
- **保持实用。** 理论服务于实践，而不是反过来。
- **拒绝 AI 流水线产物。** 像人一样写作。直接了当。砍掉废话。

## 提交 Pull Request 的流程

1. Fork 本仓库
2. 创建一个特性分支（`git checkout -b add-lesson-phase3-gradient-descent`）
3. 做你的改动
4. 确保所有代码都能跑
5. 提交一个带清晰描述的 pull request

## 行为准则

参见 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。友善、乐于助人、建设性。

## 风格

- 直白的行文。砍掉废话。贴合本手册的语气，而不是营销文案。
- 标题里不放装饰性 emoji。Lang 列的 emoji 旗标是唯一例外，而且只因为解析器会映射它们。
- 代码按课程里列出的依赖原样可运行。
- 先从零实现，框架其次。
