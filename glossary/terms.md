# AI Engineering Glossary

## A

### Agent
- **What people say:** "一个能自己思考、自己行动的自主 AI"
- **What it actually means:** 一个 while 循环：LLM 决定下一步调哪个工具，执行它，看结果，然后重复
- **Why it's called that:** Borrowed from philosophy — an "agent" is anything that can act in the world. In AI, it just means "LLM + tools + loop"

### Attention
- **What people say:** "AI 怎么聚焦到重要的部分上"
- **What it actually means:** 一种机制：每个 token 都对所有其他 token 的 value 算加权和，权重取决于它们有多相关（通过 query 和 key 向量的点积算出来）
- **Why it's called that:** The 2017 paper "Attention Is All You Need" named it by analogy to human selective attention

### Alignment
- **What people say:** "让 AI 安全"
- **What it actually means:** 一个技术难题：让 AI 系统的行为匹配人类的意图、价值观和偏好，包括设计者没预料到的边缘情况

### Autoregressive
- **What people say:** "AI 一次生成一个词"
- **What it actually means:** 一种模型，基于前面所有 token 来预测下一个 token，再把这个预测喂回去作为下一步的输入。GPT、LLaMA 和 Claude 都是自回归的。

### Activation Function
- **What people say:** "层与层之间那个非线性的东西"
- **What it actually means:** 在每个线性层之后施加的一个函数，用来引入非线性。没有它，再多线性层叠起来也会塌缩成一个线性变换。ReLU、GELU 和 SiLU 最常见。这个选择直接影响训练时梯度能不能流动。

### Adam (Optimizer)
- **What people say:** "默认的优化器"
- **What it actually means:** 自适应矩估计（Adaptive Moment Estimation）。把动量（一阶矩）和每个参数的自适应学习率（二阶矩）结合起来。对早期步数有偏差修正。不用怎么调，在大多数任务上都好使。

### AdamW
- **What people say:** "Adam 但更好"
- **What it actually means:** 带解耦权重衰减的 Adam。标准 Adam 里，L2 正则会被每个参数的自适应学习率缩放，这不是你想要的。AdamW 把权重衰减直接施加到权重上，跟梯度统计量无关。训练 transformer 的默认优化器。

### Autograd
- **What people say:** "自动求梯度"
- **What it actually means:** 一个系统，记录张量上的操作，并通过反向模式微分自动算梯度。PyTorch 的 autograd 是边跑边建计算图（动态图），JAX 则用函数变换（grad）。正是它让反向传播变得实用——你只写前向传播，框架替你算出所有导数。

## B

### Batch Size
- **What people say:** "一次处理多少个样本"
- **What it actually means:** 在更新权重前，一次前向/反向传播里处理的训练样本数。批越大，梯度估计越稳，但占内存越多。典型值：训练时 32-512，推理时更大。批大小和学习率相互关联——批翻倍，学习率也翻倍（线性缩放规则）。

### Backpropagation
- **What people say:** "神经网络怎么学习"
- **What it actually means:** 一种算法，通过在网络里反向施加链式法则，算出每个权重对误差贡献了多少，然后按比例调整权重
- **Why it's called that:** Errors propagate backward from output to input, layer by layer

## C

### Context Window
- **What people say:** "AI 能记住多少东西"
- **What it actually means:** 一次 API 调用里能装下的最大 token 数（输入 + 输出）。不是记忆——它是个固定大小的缓冲区，每次调用都会清空

### Chain of Thought (CoT)
- **What people say:** "让 AI 一步一步思考"
- **What it actually means:** 一种提示技巧，让模型把推理步骤展示出来，从而提升多步问题的准确率，因为每一步都为下一个 token 的生成提供了条件

### CNN (Convolutional Neural Network)
- **What people say:** "图像 AI"
- **What it actually means:** 一种神经网络，用卷积操作（在输入上滑动滤波器）来检测局部模式。卷积层堆叠起来，能检测越来越复杂的特征：边缘、纹理、物体。

### CUDA
- **What people say:** "GPU 编程"
- **What it actually means:** NVIDIA 的并行计算平台。让你能在成千上万个 GPU 核心上同时跑矩阵运算。PyTorch 和 TensorFlow 底层都用 CUDA。

### Chunking
- **What people say:** "把文档切成小块"
- **What it actually means:** 在嵌入用于检索之前，把文本切成段。块大小决定搜索结果的粒度。太小：丢上下文。太大：稀释相关性。常见策略：定长加重叠、按句子切、或语义切分。典型块大小：256-512 个 token，重叠 10-20%。

### Contrastive Learning
- **What people say:** "通过对比来学习"
- **What it actually means:** 在嵌入空间里把相似的样本对拉近、把不相似的样本对推远来训练。CLIP 就用这招：匹配的图文对对上不匹配的。

### Cosine Similarity
- **What people say:** "两个向量有多相似"
- **What it actually means:** 两个向量夹角的余弦：dot(a, b) / (||a|| * ||b||)。取值从 -1（相反）到 1（方向完全一致）。忽略长度，只看方向。嵌入和语义搜索的标准相似度指标。

### Cross-Entropy
- **What people say:** "分类用的损失"
- **What it actually means:** 衡量两个概率分布之间的差距。分类用：-sum(y_true * log(y_pred))。语言模型用：正确的下一个 token 的负对数概率。越低越好。困惑度不过就是 exp(交叉熵)。

## D

### Data Augmentation
- **What people say:** "制造更多训练数据"
- **What it actually means:** 给现有数据造修改过的副本（旋转图像、加噪声、改写文本），在不采集新数据的前提下增加训练集的多样性。能减少过拟合。

### Decoder
- **What people say:** "负责输出的那部分"
- **What it actually means:** 在 transformer 里，解码器用因果（掩码）自注意力，让每个位置只能关注更早的位置。GPT 是纯解码器。BERT 是纯编码器。T5 是编码器-解码器。

### Diffusion Model
- **What people say:** "从噪声里生成图像的 AI"
- **What it actually means:** 一种模型，训练它去逆转一个逐步加噪的过程——它学会预测并去除噪声，生成时从纯噪声开始，反复去噪

### DPO (Direct Preference Optimization)
- **What people say:** "更简单的 RLHF"
- **What it actually means:** 一种训练方法，完全跳过奖励模型——直接优化语言模型，让它在成对的人类偏好里更倾向于更好的那个回答

### Dropout
- **What people say:** "随机关掉一些神经元"
- **What it actually means:** 训练时随机把一部分激活值置零。逼网络不去依赖任何单个神经元。推理时关掉。简单但有效的正则化手段。

## E

### Eigenvalue
- **What people say:** "PCA 里那个数学概念"
- **What it actually means:** 对于矩阵 A，特征值 lambda 满足 Av = lambda*v（v 是某个向量）。它告诉你矩阵在那个方向上把向量缩放了多少。大特征值 = 数据中高方差的方向。

### Embedding
- **What people say:** "某种把词变成数字的 AI 魔法"
- **What it actually means:** 一个学出来的映射，把离散项（词、图像、用户）映到连续空间里的稠密向量，相似的项最终会靠在一起
- **Why it's called that:** The items are "embedded" in a geometric space where distance has meaning

### Encoder
- **What people say:** "负责输入的那部分"
- **What it actually means:** 在 transformer 里，编码器用双向自注意力，让每个位置能关注所有位置。BERT 是纯编码器。擅长理解类任务（分类、NER），但不擅长生成。

### Epoch
- **What people say:** "把数据过一遍"
- **What it actually means:** 就是字面意思。完整地过一遍训练集里的每个样本。多个 epoch = 把数据看了好几遍。epoch 越多学得可能越好，但有过拟合的风险。

## F

### Feature
- **What people say:** "数据里的一列"
- **What it actually means:** 数据的一个可测量的属性。在经典 ML 里，你手工构造特征。在深度学习里，网络从原始数据里自动学特征。

### Few-Shot
- **What people say:** "先给 AI 几个例子"
- **What it actually means:** 在让模型干活之前，在 prompt 里塞少量的输入-输出示例。通常 3-5 个。模型靠这些示例做模式匹配，搞清楚你想要的格式和行为。对比零样本（没例子）和微调（成千上万的例子烤进权重里）。

### Fine-tuning
- **What people say:** "用你的数据训练 AI"
- **What it actually means:** 从一个预训练模型的权重出发，在更小的、特定任务的数据集上继续训练。只更新已有权重，不会从零加入新知识

### Function Calling
- **What people say:** "能用工具的 AI"
- **What it actually means:** 一种让 LLM 请求执行外部函数的结构化方式。你用 JSON Schema 描述定义工具，模型输出一个结构化 JSON 对象，指明调哪个函数、传什么参数，你的代码执行它，结果再返回给模型。和 agent 不是一回事——函数调用是机制，agent 是那个循环。

## G

### Guardrails
- **What people say:** "给 AI 的安全过滤器"
- **What it actually means:** 围绕 LLM 的输入/输出校验层，用来检测并拦截有害内容、提示注入企图、PII 泄露或跑题的回答。通常是一条流水线：输入过滤 -> LLM -> 输出过滤。可以是规则驱动（正则、关键词表）或模型驱动（一个给安全性打分的分类器）。

### GPT
- **What people say:** "ChatGPT" 或 "那个 AI"
- **What it actually means:** 生成式预训练 Transformer（Generative Pre-trained Transformer）——一种特定架构，用纯解码器 transformer 在大规模文本语料上训练，来预测下一个 token
- **Why it's called that:** Generative (produces text), Pre-trained (trained once on large data, then adapted), Transformer (the architecture)

### GAN (Generative Adversarial Network)
- **What people say:** "两个 AI 互相对抗"
- **What it actually means:** 一个生成器网络试图造出逼真的数据，一个判别器网络试图分辨真假。它们一起训练：生成器越来越会骗判别器，判别器越来越会识别假货。

### Gradient
- **What people say:** "斜率"
- **What it actually means:** 一个偏导数向量，指向最陡上升的方向。在 ML 里，你朝梯度的反方向走（梯度下降）来最小化损失。

### Gradient Descent
- **What people say:** "AI 怎么变强"
- **What it actually means:** 一种优化算法，朝着最陡地减小损失函数的方向调整参数，就像在高维地形里往山下走

## H

### Hyperparameter
- **What people say:** "你要调的设置"
- **What it actually means:** 训练前设定、用来控制训练过程本身的值：学习率、批大小、层数、dropout 比例。和模型参数（权重）不同，这些不是从数据里学出来的。

### Hallucination
- **What people say:** "AI 在撒谎" 或 "在瞎编"
- **What it actually means:** 模型生成了听起来像模像样、但既不基于训练数据也不基于给定上下文的文本——它是在补全模式，不是在检索事实

## I

### Inference
- **What people say:** "跑 AI"
- **What it actually means:** 用训练好的模型对新数据做预测。不发生权重更新。这就是你在生产里干的事：送进输入，拿到输出。

### Inductive Bias
- **What people say:** 没听过
- **What it actually means:** 烤进模型架构里的那些假设。CNN 假设局部模式重要（卷积）。RNN 假设顺序重要（顺序处理）。Transformer 假设一切都可能和一切相关（注意力）。合适的偏置能让模型用更少的数据学得更快。

### JAX
- **What people say:** "谷歌的 ML 框架"
- **What it actually means:** 一个兼容 NumPy 的库，加上了自动微分（grad）、JIT 编译（jit）、自动向量化（vmap）和多设备并行（pmap）。和 PyTorch 的面向对象风格不同，JAX 是纯函数式的——没有隐藏状态，没有原地修改。Google DeepMind 用它做了 AlphaFold、Gemini 和大规模研究。

## K

### KV Cache
- **What people say:** "让推理更快"
- **What it actually means:** 自回归生成时，把之前 token 的 key 和 value 矩阵缓存起来，这样每一步就不用重算。拿内存换速度。快速 LLM 推理的关键。

## L

### Latent Space
- **What people say:** "隐藏的表示"
- **What it actually means:** 一个压缩过的、学出来的表示空间，相似的输入会映到相近的点。自编码器、VAE 和扩散模型都在潜在空间里干活。它比输入低维，但抓住了重要的结构。

### Learning Rate
- **What people say:** "AI 学得多快"
- **What it actually means:** 一个标量，控制梯度下降时的步长。太高：越过最小值并发散。太低：收敛太慢或卡住。最重要的那个超参数。

### LLM (Large Language Model)
- **What people say:** "AI" 或 "大脑"
- **What it actually means:** 一个基于 transformer 的神经网络，训练它去预测序列里的下一个 token，参数量上十亿，在互联网规模的文本数据上训练

### LoRA (Low-Rank Adaptation)
- **What people say:** "高效微调"
- **What it actually means:** 不更新全部权重，而是在原权重旁边插入小的低秩矩阵。只训练这些小矩阵，把内存降低 10-100 倍

### Loss Function
- **What people say:** "AI 错得有多离谱"
- **What it actually means:** 一个函数，衡量预测输出和真实输出之间的差距。训练就是最小化这个函数。回归用 MSE，分类用交叉熵，嵌入用对比损失。损失函数的选择定义了对模型来说什么叫"好"。

## M

### Mixed Precision
- **What people say:** "提速的训练技巧"
- **What it actually means:** 前向传播和大多数操作用 float16（更快、更省内存），但梯度累加和权重更新保留 float32（更精确）。能拿到 2 倍加速，精度损失可忽略。

### MoE (Mixture of Experts)
- **What people say:** "模型只跑一部分"
- **What it actually means:** 一个有很多"专家"子网络的模型，路由机制把每个输入只送给少数几个专家。整个模型很大，但每次前向传播很便宜，因为大多数专家都被跳过了。Mixtral 和 GPT-4 用了这招。

### MCP (Model Context Protocol)
- **What people say:** "一种让 AI 用工具的方式"
- **What it actually means:** 一个开放协议（基于 stdio/HTTP 的 JSON-RPC），标准化了 AI 应用怎么连接外部数据源和工具，对工具、资源和 prompt 都有带类型的 schema

## N

### NaN (Not a Number)
- **What people say:** "训练崩了"
- **What it actually means:** 一个浮点值，表示未定义的结果（0/0，inf-inf）。训练里出现 NaN 损失通常意味着：学习率太高、梯度爆炸、对零取对数、或除以零。训练失败时永远第一个该查的东西。

### Normalization
- **What people say:** "缩放数据"
- **What it actually means:** 把值调到一个标准范围。批归一化在一个批内做归一化。层归一化跨特征做归一化。两者都能稳定训练，并允许更高的学习率。

## O

### Overfitting
- **What people say:** "模型把数据背下来了"
- **What it actually means:** 模型在训练数据上表现好，但在没见过的数据上表现差。它学的是噪声，不是信号。解法：更多数据、正则化（dropout、权重衰减）、提前停止、数据增强、更简单的模型。

### Optimizer
- **What people say:** "更新权重的那个东西"
- **What it actually means:** 一种算法，用梯度来更新模型参数。SGD 最简单。Adam 最常用。每种优化器特性不同：收敛速度、内存占用、对超参数的敏感程度。

## P

### Parameter
- **What people say:** "模型大小"
- **What it actually means:** 模型里一个可学习的值，通常是权重或偏置。"7B 参数"就是 70 亿个可学习的数。每个 float32 参数占 4 字节，所以 7B 参数 = 光是权重就要 28GB 内存。

### Perplexity
- **What people say:** "模型有多懵"
- **What it actually means:** 平均交叉熵损失的指数。越低越好。困惑度 10 意味着模型的不确定程度，相当于每一步都在 10 个 token 里均匀乱猜。

### Precision & Recall
- **What people say:** "准确率指标"
- **What it actually means:** 精确率 = 你标出来的项里，有多少是对的。召回率 = 所有对的项里，你找到了多少。它们会权衡：抓住每一封垃圾邮件（高召回）意味着更多误报（低精确）。F1 分数是它俩的调和平均。误报代价高时看精确率，漏报代价高时看召回率。

### Prompt Engineering
- **What people say:** "用对的方式跟 AI 说话"
- **What it actually means:** 设计输入文本，让它稳定地产出想要的输出——包括系统提示、少样本示例、格式说明和思维链触发语

### Prompt Injection
- **What people say:** "用文字黑掉 AI"
- **What it actually means:** 一种攻击，输入里的恶意文本覆盖了系统提示或指令。直接注入：用户打"忽略之前的指令"。间接注入：检索到的文档里藏着指令。相当于 LLM 版的 SQL 注入。没有彻底的解法——防御靠多层的输入校验、输出过滤和权限隔离。

## Q

### QLoRA
- **What people say:** "更省钱的 LoRA"
- **What it actually means:** 量化版 LoRA。把冻结的基座模型权重保持在 4 bit 精度（NF4 格式），同时用 16 bit 训练 LoRA 适配器。比标准 LoRA 再省 3-4 倍内存。一个用 LoRA 要 14GB 的 7B 模型，用 QLoRA 在 4-6GB 里就装得下。质量在大多数基准上跟全量微调差不超过 1%。

## R

### RAG (Retrieval-Augmented Generation)
- **What people say:** "能搜索的 AI"
- **What it actually means:** 一种模式：你从知识库里检索相关文档（用嵌入相似度），把它们塞进 prompt，让 LLM 基于这个上下文来回答
- **Why it's called that:** Retrieval (find documents) + Augmented (add to prompt) + Generation (LLM writes the answer)

### RLHF (Reinforcement Learning from Human Feedback)
- **What people say:** "他们怎么让 AI 变得有用的"
- **What it actually means:** 一条训练流水线：(1) 收集人类对模型输出的偏好，(2) 在这些偏好上训练一个奖励模型，(3) 用 PPO 优化 LLM，让它产出更高奖励的输出

### Quantization
- **What people say:** "把模型变小"
- **What it actually means:** 把模型权重的精度从 float32（4 字节）降到 int8（1 字节）或 int4（0.5 字节）。用一点点精度换 4-8 倍的内存节省和更快的推理。GPTQ、AWQ 和 GGUF 是常见格式。

### ReLU
- **What people say:** "激活函数"
- **What it actually means:** 修正线性单元：f(x) = max(0, x)。最简单的非线性激活。算起来快，对正值不饱和。到处都在用，因为它管用又便宜。变体：LeakyReLU、GELU、SiLU。

### ROUGE
- **What people say:** "摘要指标"
- **What it actually means:** Recall-Oriented Understudy for Gisting Evaluation。衡量生成文本和参考文本之间的重叠。ROUGE-1 数 unigram 命中，ROUGE-2 数 bigram 命中，ROUGE-L 找最长公共子序列。算起来便宜，但只衡量表面相似——两句意思相同但用词不同的话会得分很低。

## S

### Semantic Search
- **What people say:** "懂含义的智能搜索"
- **What it actually means:** 靠含义而非关键词匹配来找文档。把查询和所有文档嵌入到同一个向量空间，然后返回嵌入和查询嵌入最接近的文档。"payment failed" 能找到 "transaction declined"，哪怕它们一个词都不共享。由嵌入模型 + 向量数据库驱动。

### Streaming
- **What people say:** "看着回答一个词一个词蹦出来"
- **What it actually means:** LLM 边生成边发送 token，而不是等整个回答完成。用服务器发送事件（SSE）或 WebSocket 协议。把首个 token 的感知延迟从几秒降到几毫秒。生产级聊天界面的必备。每个分块包含一个增量（部分 token 或词）。

### Self-Attention
- **What people say:** "模型怎么决定该关注什么"
- **What it actually means:** 每个 token 算出 query、key 和 value 向量。两个 token 间的注意力权重 = 它们 query 和 key 的点积，缩放后过 softmax。输出 = value 向量的加权和。让每个 token 都能看到其他每个 token。

### SFT (Supervised Fine-Tuning)
- **What people say:** "教模型遵循指令"
- **What it actually means:** 在（指令，回答）对上微调一个预训练模型。模型学会在给定指令时生成回答。这就是把基座模型变成聊天模型的过程。

### Softmax
- **What people say:** "把数字变成概率"
- **What it actually means:** softmax(x_i) = exp(x_i) / sum(exp(x_j))。把一个任意实数向量变成一个概率分布（全为正，加起来等于 1）。用在分类头、注意力权重，以及任何需要概率的地方。

### Swarm
- **What people say:** "一群 AI 智能体像蜜蜂一样协同干活"
- **What it actually means:** 多个智能体共享状态、通过消息传递来协调，涌现行为来自简单的个体规则，而非中央控制

## T

### System Prompt
- **What people say:** "AI 的指令"
- **What it actually means:** 对话开头的一条特殊消息，设定模型的行为、人设和约束。在用户消息之前处理。在大多数 UI 里对用户不可见。它定义模型该做什么、不该做什么、语气、格式偏好和领域聚焦。和用户提示不同——系统提示由开发者设定。

### Tensor
- **What people say:** "一个多维数组"
- **What it actually means:** 深度学习框架里最基础的数据结构。0 维张量是标量，1 维是向量，2 维是矩阵，3 维及以上是张量。在 PyTorch 和 JAX 里，张量会追踪自己的计算历史以做自动微分，可以放在 CPU 或 GPU 上。神经网络的所有输入、输出、权重和梯度都是张量。

### Token
- **What people say:** "一个词"
- **What it actually means:** 由分词器（比如 BPE）产出的子词单元（英文里通常 3-4 个字符）。"unbelievable" 可能是 3 个 token："un" + "believ" + "able"

### Temperature
- **What people say:** "创造力设置"
- **What it actually means:** 一个标量，在 softmax 之前除 logits。Temperature=1 是默认。越高 = 分布越平 = 输出越随机。越低 = 分布越尖 = 越确定。Temperature=0 就是 argmax（永远挑最可能的 token）。

### Transfer Learning
- **What people say:** "用一个预训练模型"
- **What it actually means:** 拿一个在某任务上训练好的模型，把它适配到另一个任务。早期层学到的是通用特征（边缘、句法模式），这些能迁移。只有后面的层需要特定任务的训练。这就是为什么你能把 BERT 微调到任何 NLP 任务上。

### Transformer
- **What people say:** "现代 AI 背后的那个架构"
- **What it actually means:** 一种神经网络架构，用自注意力（让每个位置都能关注其他每个位置）而非循环来处理序列，从而实现大规模并行化
- **Why it's called that:** It transforms input representations into output representations through attention layers

## U

### Underfitting
- **What people say:** "模型没在学"
- **What it actually means:** 模型太简单，抓不住数据里的模式。训练损失一直很高。解法：更多参数、更多层、更长训练、更少正则化、更好的特征。

## V

### VAE (Variational Autoencoder)
- **What people say:** "一种生成模型"
- **What it actually means:** 一种自编码器，通过逼迫编码器输出服从高斯分布来学出一个平滑的潜在空间。你可以从这个分布里采样并解码来生成新数据。重参数化技巧让它能通过反向传播训练。

### Vector Database
- **What people say:** "一种专给 AI 用的数据库"
- **What it actually means:** 一种数据库，专门优化存储向量（稠密浮点数组）并做快速近似最近邻搜索。是相似度搜索、RAG 和推荐系统里的核心操作。

## W

### Weight
- **What people say:** "模型学到的东西"
- **What it actually means:** 模型参数矩阵里的一个数。一个输入大小 768、输出大小 3072 的线性层有 768*3072 = 2,359,296 个权重。训练就是调整每个权重去最小化损失函数。

### Weight Decay
- **What people say:** "正则化"
- **What it actually means:** 往损失函数里加一个跟权重大小成正比的惩罚项。等价于 L2 正则化。防止权重涨得太大。典型值：0.01-0.1。

## Z

### Zero-Shot
- **What people say:** "不用训练"
- **What it actually means:** 把模型用在它没被明确训练过的任务上，prompt 里也没有特定任务的示例。模型靠预训练来泛化。之所以管用，是因为大模型见过的花样足够多，能应付新的任务格式。
