<<<<<<< HEAD
---
name: check-understanding
version: 1.0.0
description: Phase quiz for AI Engineering from Scratch. Trigger with "quiz me", "test phase", "check my understanding", "do I know phase 3", or `/check-understanding <phase>`.
---

# Check Understanding

Test your knowledge of a completed phase from the AI Engineering from Scratch course.

## Activation

This skill activates when the user says things like:
- `/check-understanding 3` or `/check-understanding deep-learning`
- "quiz me on phase 2"
- "test phase 1"
- "check my understanding of transformers"
- "do I know phase 3"
- "am I ready for the next phase"

## Input

Accepts a phase number (0-19) or a phase name as argument. If no argument is provided, ask the user which phase they want to be tested on by listing all 20 phases.

## Phase Map

Map the argument to the correct phase directory under `phases/`:

| Input | Directory | Phase Name |
|-------|-----------|------------|
| 0, setup, tooling | `00-setup-and-tooling` | Setup & Tooling |
| 1, math, math-foundations | `01-math-foundations` | Math Foundations |
| 2, ml, ml-fundamentals | `02-ml-fundamentals` | ML Fundamentals |
| 3, deep-learning, dl | `03-deep-learning-core` | Deep Learning Core |
| 4, cv, computer-vision, vision | `04-computer-vision` | Computer Vision |
| 5, nlp | `05-nlp-foundations-to-advanced` | NLP -- Foundations to Advanced |
| 6, speech, audio | `06-speech-and-audio` | Speech & Audio |
| 7, transformers | `07-transformers-deep-dive` | Transformers Deep Dive |
| 8, generative, gen-ai, genai | `08-generative-ai` | Generative AI |
| 9, rl, reinforcement-learning | `09-reinforcement-learning` | Reinforcement Learning |
| 10, llms, llm, llms-from-scratch | `10-llms-from-scratch` | LLMs from Scratch |
| 11, llm-engineering, llm-eng | `11-llm-engineering` | LLM Engineering |
| 12, multimodal | `12-multimodal-ai` | Multimodal AI |
| 13, tools, protocols, mcp | `13-tools-and-protocols` | Tools & Protocols |
| 14, agents, agent-engineering | `14-agent-engineering` | Agent Engineering |
| 15, autonomous | `15-autonomous-systems` | Autonomous Systems |
| 16, multi-agent, swarms | `16-multi-agent-and-swarms` | Multi-Agent & Swarms |
| 17, infrastructure, production, infra | `17-infrastructure-and-production` | Infrastructure & Production |
| 18, ethics, safety, alignment | `18-ethics-safety-alignment` | Ethics, Safety & Alignment |
| 19, capstone, projects | `19-capstone-projects` | Capstone Projects |

## Procedure

### Step 1: Resolve the Phase

Parse the argument. If it is a number, validate it is between 0 and 19 inclusive. If the number is out of range, tell the user: "Phase [N] does not exist. Valid phases are 0-19." and show the full list for them to pick from. If it is a name or keyword, look it up in the Phase Map above. If the keyword does not match any entry in the map, tell the user: "Unknown phase '[keyword]'. Pick from the list below:" and present all 20 phases. If no argument is provided, ask the user to pick from the full list.

### Step 2: Read the Phase Content

Use Glob to find all lesson directories under `phases/<phase-dir>/`. For each lesson, read the `docs/en.md` file. These documents contain the teaching material you will generate questions from.

Read as many lesson docs as needed to cover the full breadth of the phase. If a phase has many lessons (15+), prioritize reading a representative spread: first few, middle, and last few.

### Step 3: Generate 8 Questions

Create exactly 8 multiple-choice questions drawn from the lesson content you just read:

**Questions 1-4: Conceptual (What/Why)**
These test understanding of ideas, definitions, and reasoning. Examples:
- "What is the purpose of X?"
- "Why does Y happen when Z?"
- "Which statement best describes the relationship between A and B?"
- "What problem does X solve?"

**Questions 5-8: Practical (How/Build)**
These test applied knowledge and implementation awareness. Examples:
- "How would you implement X?"
- "Which approach correctly solves Y?"
- "What is the correct order of steps to build Z?"
- "If you observe X during training, what should you do?"

Each question must have 3 or 4 answer options labeled A, B, C (and optionally D). Exactly one option is correct. The wrong options should be plausible but clearly incorrect to someone who studied the material.

Tag each question with the specific lesson it draws from (e.g., "Lesson 03: Matrix Transformations").

### Step 4: Present Questions One at a Time

Use the AskUserQuestion tool (or equivalent interactive prompt) to present each question individually. Format:

```
Question 1/8 (Conceptual) -- from Lesson 03: Matrix Transformations

What is the geometric interpretation of an eigenvalue?

A) The angle of rotation applied by the matrix
B) The factor by which the eigenvector is scaled during transformation
C) The determinant of the transformation matrix
D) The rank of the matrix after transformation
```

Wait for the user's answer before moving to the next question.

### Step 5: Track and Score

Keep a running tally:
- Total correct out of 8
- For each wrong answer, record: the question number, the user's answer, the correct answer, and which lesson it came from

### Step 6: Show Results

After all 8 questions, display the score and grade:

**7-8 correct: Mastered**
If the phase is 19 (Capstone Projects): "You have mastered the final phase. Congratulations, you have completed the entire curriculum."
Otherwise: "You have a strong grasp of Phase N. You are ready to move on to Phase N+1: [next phase name]."

**5-6 correct: Almost**
"Solid foundation. Review these specific areas before moving on:"
Then list the lessons tied to the missed questions.

**3-4 correct: Developing**
"You are building understanding but need to revisit some lessons:"
Then list each missed question with the lesson to re-read.

**0-2 correct: Start Over**
"This phase needs more time. Work through the lessons again from the beginning, focusing on:"
Then list all missed topics.

### Step 7: Wrong Answer Breakdown

For every question the user got wrong, show:

```
Question N: [question text, abbreviated]
Your answer: B
Correct answer: C -- [the correct option text]
Why: [1-2 sentence explanation of why C is correct]
Review: Lesson NN -- [lesson name] (phases/<phase-dir>/NN-<lesson-slug>/docs/en.md)
```

### Step 8: What Next?

End by offering three choices:

1. **Retake this quiz** -- generate a fresh set of 8 questions from the same phase
2. **Try another phase** -- pick a different phase to test
3. **Explain a topic** -- ask about any concept from the questions you missed

Wait for the user's choice and act accordingly.

## Rules

- Avoid repeating questions on retakes until the question pool is exhausted. Once exhausted, reshuffle or rephrase questions for subsequent retakes.
- Questions must be directly grounded in the lesson docs, not general knowledge.
- Do not show the correct answer until after the user responds.
- Keep question text concise. One or two sentences max.
- Wrong options must be plausible. No joke answers.
- If a phase has no lesson docs written yet (no `en.md` files found), tell the user: "Phase N does not have lesson content yet. Pick a completed phase to quiz on."
=======
---
name: check-understanding
version: 1.0.0
description: AI Engineering from Scratch 的阶段测验。用于“给我测验一下”、“测试阶段”、“检查我的理解”、“我掌握第 3 阶段了吗”，也支持 "quiz me", "test phase", "check my understanding", "do I know phase 3" 或 `/check-understanding <phase>`。
---

# 检查理解程度

测试学习者对 AI Engineering from Scratch 已完成阶段的掌握情况。

## 触发方式

当用户说出类似下面的话时启用此 skill：

- `/check-understanding 3` 或 `/check-understanding deep-learning`
- “测验一下我对第 2 阶段的掌握情况”
- “测试第 1 阶段”
- “检查我对 transformer 的理解”
- “我掌握第 3 阶段了吗”
- “我准备好进入下一阶段了吗”

## 输入

接受阶段编号（0-19）或阶段名称作为参数。如果没有参数，列出全部 20 个阶段，并询问用户希望测试哪一阶段。

## 阶段映射

将参数映射到 `phases/` 下正确的阶段目录：

| 输入 | 目录 | 阶段名称 |
|-------|-----------|------------|
| 0, setup, tooling | `00-setup-and-tooling` | 环境设置与工具 |
| 1, math, math-foundations | `01-math-foundations` | 数学基础 |
| 2, ml, ml-fundamentals | `02-ml-fundamentals` | 机器学习基础 |
| 3, deep-learning, dl | `03-deep-learning-core` | 深度学习核心 |
| 4, cv, computer-vision, vision | `04-computer-vision` | 计算机视觉 |
| 5, nlp | `05-nlp-foundations-to-advanced` | NLP：从基础到进阶 |
| 6, speech, audio | `06-speech-and-audio` | 语音与音频 |
| 7, transformers | `07-transformers-deep-dive` | Transformer 深入剖析 |
| 8, generative, gen-ai, genai | `08-generative-ai` | 生成式 AI |
| 9, rl, reinforcement-learning | `09-reinforcement-learning` | 强化学习 |
| 10, llms, llm, llms-from-scratch | `10-llms-from-scratch` | 从零构建 LLM |
| 11, llm-engineering, llm-eng | `11-llm-engineering` | LLM 工程 |
| 12, multimodal | `12-multimodal-ai` | 多模态 AI |
| 13, tools, protocols, mcp | `13-tools-and-protocols` | 工具与协议 |
| 14, agents, agent-engineering | `14-agent-engineering` | Agent 工程 |
| 15, autonomous | `15-autonomous-systems` | 自主系统 |
| 16, multi-agent, swarms | `16-multi-agent-and-swarms` | 多 Agent 与群体 |
| 17, infrastructure, production, infra | `17-infrastructure-and-production` | 基础设施与生产环境 |
| 18, ethics, safety, alignment | `18-ethics-safety-alignment` | 伦理、安全与对齐 |
| 19, capstone, projects | `19-capstone-projects` | 综合项目 |

## 流程

### 第 1 步：解析阶段

解析参数。若为数字，验证它是否在 0 到 19（含）之间。数字超出范围时，告诉用户：`阶段 [N] 不存在。有效阶段为 0-19。`然后展示完整列表供其选择。若为名称或关键词，在上方阶段映射中查找。关键词不匹配任何条目时，告诉用户：`未知阶段“[keyword]”。请从下面列表中选择：`，并展示全部 20 个阶段。未提供参数时，要求用户从完整列表中选择。

### 第 2 步：读取阶段内容

如果仓库已克隆（当前目录或其父目录存在 `phases/`），找出 `phases/<phase-dir>/` 下全部课程目录并读取每课的 `docs/zh.md`。如果未克隆，从 README 的 Contents 部分获取该阶段课程列表（获取 `https://raw.githubusercontent.com/fancyboi999/ai-engineering-from-scratch-zh/main/README.md`），再从同一 raw base URL 获取每课的 `docs/zh.md`。这些文档就是出题依据。

读取足够多的课程文档，以覆盖该阶段的完整广度。阶段课程很多（15+）时，优先读取具有代表性的分布：开头几课、中段几课和最后几课。

### 第 3 步：生成 8 道题

基于刚读取的课程内容，恰好生成 8 道选择题：

**第 1-4 题：概念题（是什么/为什么）**
这些题测试想法、定义和推理的理解。例如：
- “X 的目的是什么？”
- “Z 存在时为什么会发生 Y？”
- “哪项陈述最准确地描述了 A 与 B 的关系？”
- “X 解决了什么问题？”

**第 5-8 题：实践题（怎么做/构建）**
这些题测试应用知识和实现意识。例如：
- “你会如何实现 X？”
- “哪种方法能正确解决 Y？”
- “构建 Z 的正确步骤顺序是什么？”
- “若训练中观察到 X，应当怎么做？”

每题必须恰有 4 个选项，标记为 A、B、C、D，且只有一个正确选项。错误选项应当可信，但对认真学过材料的人应当明显不对。

给每道题标记其来源课程（例如“第 03 课：矩阵变换”）。

### 第 4 步：逐题展示

使用 AskUserQuestion 工具（或等效交互式提示）一次展示一道题。格式：

```text
第 1/8 题（概念题）——来自第 03 课：矩阵变换

特征值的几何解释是什么？

A) 矩阵施加的旋转角度
B) 特征向量在变换中被缩放的倍数
C) 变换矩阵的行列式
D) 变换后矩阵的秩
```

等待用户作答后，才进入下一题。

### 答案隔离

在学习者回答当前题目之前，正确选项和解释必须保持私密。回复格式提示中绝不使用真实答案字母、可能答案或生成的答案分布。若需要纯文本提示，必须严格使用：`请只回复一个字母：<A|B|C|D>。`

### 第 5 步：记录与评分

持续记录：
- 8 题中的正确总数
- 每道错题：题号、用户答案、正确答案及来源课程

### 第 6 步：展示结果

所有 8 题完成后，展示得分和评级：

**答对 7-8 题：已掌握**
若为第 19 阶段（综合项目）：`你已掌握第 19 阶段，也是最后一个阶段。`只有能够确认整个课程其余部分均已完成时（当前目录中的 `LEARNING.md` 路径表显示阶段 0-18 都是 Done 或 Skip），才能再加上 `恭喜，你已完成全部课程。`单次阶段测验不能证明整个课程已完成。
否则：`你对第 N 阶段掌握扎实，可以进入第 N+1 阶段：[下一阶段名称]。`

**答对 5-6 题：接近掌握**
`基础扎实。继续前请复习以下具体内容：`
随后列出错题关联的课程。

**答对 3-4 题：正在形成理解**
`你的理解正在建立，但还需回顾以下课程：`
随后列出每道错题及需重读的课程。

**答对 0-2 题：重新开始**
`这个阶段还需要更多时间。请从头重新学习课程，重点关注：`
随后列出所有未掌握的主题。

### 第 7 步：错题拆解

对用户答错的每一题，展示：

```text
第 N 题：[题目文本，缩写]
你的答案：B
正确答案：C —— [正确选项文本]
原因：[用 1-2 句解释 C 为什么正确]
复习：第 NN 课 —— [课程名称] (phases/<phase-dir>/NN-<lesson-slug>/docs/zh.md)
```

### 第 8 步：下一步做什么？

最后提供三个选择：

1. **重做本测验** —— 从同一阶段生成一组新的 8 道题
2. **测试另一阶段** —— 选择其他阶段测试
3. **解释一个主题** —— 询问任意错题涉及的概念

等待用户选择后再执行。

## 规则

- 重考时，在题库耗尽前避免重复题目。题库耗尽后，才可为后续重考重排或改写题目。
- 题目必须直接基于课程文档，不能基于通用知识。
- 用户回答之前，不展示正确答案。
- 学习者回答格式示例中不得出现真实答案字母；使用 `<A|B|C|D>` 作为占位符。
- 题目文本保持简洁，最多一两句话。
- 错误选项必须可信，不要设置玩笑答案。
- 若一个阶段尚无课程文档（找不到 `en.md` 文件），告诉用户：`第 N 阶段尚未提供课程内容。请选择已完成的阶段进行测验。`
>>>>>>> main
