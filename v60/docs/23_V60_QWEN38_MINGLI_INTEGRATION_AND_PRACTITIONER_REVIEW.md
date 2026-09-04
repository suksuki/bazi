# V60 Qwen3.8 命理接入、低延迟重构与命理师视角评审

状态：`IMPLEMENTED / LOCAL_RUNTIME_READY / OWNER_REVIEW_REQUIRED / PUBLICATION_BLOCKED`

日期：2026-08-15

## 1. 本文解决什么问题

本文是 2026-08-15 Qwen3.8-27B 接入过程的合并记录，覆盖：

1. 恢复此前“高级命理师系统方法蒸馏”的真实项目基线；
2. 核对新模型、服务端和官方调用方式；
3. 判断 Qwen3.8 是否能返回、为何慢、参数是否配错；
4. 用同一命理合同与 Gemma4 对照；
5. 按 Owner 决策把用户路径从大而全 Prompt 重构为一次一个专问；
6. 把模型暴露出的错误蒸馏为本地规则、数据合同和回归；
7. 从命理师审稿角度判断 Qwen3.8 到底提升了多少。

本文不把模型卡跑分等同于命理资格，不把本地 Normalizer 修正后的安全结果冒充模型
独立能力，也不把合成命盘结论冒充真人应事准确率。

## 2. 恢复后的项目目标

此前项目训练的首要对象不是某个 LLM 权重，而是阿布知命本地系统：

```text
确定性命盘事实
→ 本地 Case Packet 与方法候选
→ 本地 LLM 给出原始判断／文字
→ 开发期教师与 Codex 审读差异
→ 提炼方法卡、事实检查、反证、Normalizer、Schema、Gold 与测试
→ Owner／专业复核决定是否准入
→ 本地候选在合成单变量命盘上重跑
→ 上线后由本地系统 + 本地 LLM 独立运行
```

因此，“蒸馏”首先是系统方法蒸馏，不要求每次调用付费 OpenAI API，也不等同于把教师
回答复制为正式命理结论。当前产品运行依赖只有确定性本地系统与本地 Qwen；开发会话中的
教师审读不进入普通用户 Runtime。

## 3. 新模型与服务端核验

### 3.1 真实部署

本轮实际访问：

```text
Ollama endpoint   http://dblife.com:11888
Ollama version    0.32.13
model             qwen3.8:27b
digest            22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643
quantization      Q4_K_M
loaded size       about 17.4 GB
```

模型可以正常返回。服务端对 `system` 指令有效；早期“system 可能被丢弃”的怀疑经过
矛盾指令测试后被否定。真正需要处理的是本地 Ollama 模型模板只有 `{{ .Prompt }}`，不能
假设它自动应用 Hugging Face tokenizer 中的 Qwen3.8 ChatML thinking 开关。

另一个性能事实是：改变 `num_ctx` 会让 Ollama 重载 Runner，本轮观察到约 8 秒额外成本。
因此生产配置必须固定上下文，不应为每个专问动态切换窗口。

### 3.2 官方模型信息

[Qwen3.8-27B 官方模型卡](https://huggingface.co/Qwen/Qwen3.8-27B)与仓库配置确认：

| 项目 | 官方值 |
| --- | ---: |
| 参数量 | 27B dense |
| Transformer 层数 | 64 |
| Hidden dimension | 5120 |
| Attention heads / KV heads | 24 / 4 |
| Intermediate dimension | 17,408 |
| Vocabulary | 248,320 |
| 原生上下文 | 262,144 tokens |
| 可扩展上下文 | 1,000,000 tokens，需相应 serving 配置 |

模型默认 thinking。官方非思考模式推荐：

```text
temperature        0.7
top_p              0.8
top_k              20
min_p              0.0
presence_penalty   1.5
repetition_penalty 1.0
enable_thinking    false
```

官方 tokenizer template 在 `enable_thinking=false` 时为 assistant generation 预填：

```text
<think>

</think>

```

Ollama 的 [`/api/generate`](https://docs.ollama.com/api/generate) 支持 `raw`、`think`、
`stream`、`keep_alive` 与运行参数。Focused Runtime 使用 `raw=true` 自己渲染官方
ChatML 非思考模板，避免依赖当前 Ollama 模型内过于简单的模板。

## 4. 为什么原来的调用很慢

原有严格 Agent 让模型一次完成整盘结构化判断：根气、旺衰、格局、方法卡、主次解释、
反证、人生领域和岁运都进入一个 JSON Schema。它适合 DEV 资格审计，不适合用户每次点开
命理枝时等待。

旧路径的主要成本不是“文字回答”本身，而是：

- 输入 Packet 和 Schema 超过一万 token；
- 输出上限约六千 token；
- 27B Q4_K_M 的长输出解码较慢；
- 严格 JSON 必须完成后才能校验和投射；
- 五问串行原型会把五次延迟相加。

本轮实测，继续删减大 Prompt 并不能显著改变严格 Agent 约 190 秒的耗时。Owner 随后明确
了更适合产品的原则：不要一次贪大；每次问一个具体问题；LLM 原文可由本地系统二次整理；
训练重点是本地方法与返回文字，而不是把全部确定性约束塞进 Prompt。

## 5. 最终形成的双 Runtime 分工

### 5.1 严格整盘 Agent：DEV 资格与方法研究

```text
model               qwen3.8:27b
calls               1 whole-chart structured call
think               false
temperature         0
top_p / top_k       0.95 / 20
num_ctx             24576
num_predict         6000
output              JSON Schema
publication         false
```

这条路径保留完整审计合同，用来判断候选是否真的独立完成方法卡、主次决胜和反证，不再
承担普通用户首屏文字。

### 5.2 Focused Runtime：用户按需断命

```text
model               qwen3.8:27b
generation mode     one focus per request
output              short natural text
think               false
temperature         0.7
top_p / top_k       0.8 / 20
min_p               0
presence_penalty    1.5
repeat_penalty      1.0
num_ctx             4096
num_predict         320
seed                42
keep_alive          30m
stream              false
prompt transport    raw official ChatML non-thinking
```

五个专问依次为：

```text
STRUCTURE
→ LIFE_IMAGE_PERSONALITY
→ CAREER_WEALTH
→ RELATIONSHIP_FAMILY
→ TIMING
```

产品一次只请求用户当前选择的主题。`STRUCTURE` 是其余四问唯一依赖；生命意象、事业财富、
关系家庭和时间层互不强迫生成。旧五问批量入口只保留给 DEV 教师批处理。

当前短回答使用 `stream=false`，让服务器在一次完整短答上执行事实检查、归一化和追加封存；
页面会立即显示“阿布正在判断”。如果未来要进一步降低体感首字延迟，可以增加经过服务端
边界保护的 NDJSON/SSE 投射，但它不会减少模型实际计算量。

## 6. 产品与数据层改造

### 6.1 不可变专问记录

每次专问都形成 `v60.mingli-focused-pass-record.001`，绑定：

- Case、Chart、LifeCase、Reading 与 Packet；
- 模型名、Digest、Provider Profile 与 Prompt Hash；
- Focus 与结构总纲依赖 Hash；
- 输入／输出 token、模型耗时；
- 原始文本、归一化文本与本地复核码。

PostgreSQL 表禁止原地 update/delete。相同谱系与配置命中缓存时直接重放；模型、Prompt、
Normalizer、Reading 或结构总纲变化都会形成新记录，不会把历史结果改义。

### 6.2 API 与 Summary

新增产品入口：

```text
POST /api/v60/mingli/stage/focused-pass
```

浏览器只收到归一化文本，不收到原始教师材料。Reading Summary `.008` 表达：

```text
NOT_GENERATED / PARTIAL / READY
```

迁移：

```text
0048_mingli_focused_readings
0049_mingli_progressive_focused_passes
Foundation v60.foundation.041
```

### 6.3 UI 行为

- 第一次只显示“先断原局总纲”；
- 点击后立即显示忙碌状态；
- 结构完成后才开放其余层；
- 每层只生成缺失的当前专问；
- 事业／财富与关系／家庭是两个独立动作；
- 刷新后从 append-only 记录恢复，不重复调用模型；
- 原局复核风险会传播到依赖层的可见状态。

## 7. 从模型错误蒸馏出的本地能力

本地 Normalizer 不负责偷偷改写成“标准命理答案”。它只做可证明的格式清理、坐标核验和
复核标记，保留模型原文供 DEV 审读。Qwen3.8 真实输出新增或强化了以下错误类型：

| 复核族 | 真实暴露的问题 |
| --- | --- |
| 月令坐标 | 把月干甲木写成“月令七杀甲木” |
| 判型越权 | 在证据不足时直接声称从财、从势或唯一用法 |
| 时间范围泄漏 | 原局专问越界谈岁运，或把时间成员写成既成作用 |
| 关系作用越界 | 把午子冲成员关系扩大为确定的财星动荡、路径断裂 |
| 藏干／支数坐标 | 写错藏干位置、地支数量或作用对象 |
| 五行因果冲突 | 使用与已知五行生克不一致的因果句 |
| 传记推断 | 从无印等局部信号直接编造原生家庭经历 |
| 心理／灾祸推断 | 把焦虑、疾病、灾祸等高风险内容说成确定事实 |
| 绝对化表达 | 使用“一定、必然、唯有”等超过证据强度的断语 |

这些差异进入 Normalizer `.003`、回归测试和可见 Review 状态。它们是本地系统学到的资产，
不是要求 Qwen 每次在 Prompt 中背诵更长的禁令。

## 8. 真实延迟

同一合法合成命盘、Qwen3.8:27B Q4_K_M、Focused Profile `.005`：

| 专问 | 输入 token | 输出 token | 首次墙钟时间 |
| --- | ---: | ---: | ---: |
| 原局总纲 | 826 | 191 | 14.8s |
| 生命意象／性情 | 556 | 102 | 8.1s |
| 事业／财富 | 627 | 160 | 13.0s |
| 关系／家庭 | 649 | 128 | 10.7s |
| 大运／流年 | 668 | 220 | 16.2s |
| 相同专问缓存重放 | — | — | 9ms |

对照：

| 路径 | 墙钟时间 |
| --- | ---: |
| 旧五问串行原型 | 109.6s |
| 严格整盘资格 Agent | 约 190.9s |
| 当前产品单次专问 | 8.1–16.2s |

Focused 重构解决的是产品工作量和等待路径，不证明底层 Qwen 推理吞吐已经变快。官方也
建议高吞吐生产服务使用最新 SGLang、vLLM 或 TokenSpeed；若并发量上升，应单独评估迁移，
而不是继续无限削减命理上下文。

## 9. 与 Gemma4 的同尺结果

两模型使用相同 Suite Definition、Evaluator `.008`、DEV Gold `.005` 和盲断合同：

```text
Qwen3.8 run  v60-mingli-synthetic-suite-run-150c896e9c1fe901408e
Gemma4 run   v60-mingli-synthetic-suite-run-ea54d9e849a422f02ea3
```

| 候选 | Hold | Changed pass | 结果 | 模型独立 | 平均 Reading |
| --- | ---: | ---: | --- | --- | ---: |
| Qwen3.8:27B | 6/6 | 41 | `PRODUCT_SAFE_MODEL_FAIL` | `FAIL` | 191.6s |
| Gemma4 | 6/6 | 37 | `PRODUCT_SAFE_MODEL_FAIL` | `FAIL` | 88.3s |

Qwen3.8 在这轮没有触发 Gemma4 的：

- `SERVER_REPAIR:DAY_MASTER_REGIME`；
- `SERVER_REPAIR:WORK_PATH_FORM`；
- 原始判型一致性和 PRIMARY 路径绑定的对应失败。

但 Qwen3.8 仍然触发：

- 四个变体的 `HYPOTHESIS_DECISION` 修正；
- 四个变体的 H1 方法卡修正；
- 三个变体的 H2 方法卡修正；
- 两组实验的可执行主次翻转失败；
- 第二／第三藏干实验的方法反证和正文范围失败。

因此 Changed pass 从 37 到 41 是可信的小幅结构进步；它不是高级命理师资格跃迁。速度上
Qwen 严格整盘约为 Gemma4 的 2.17 倍，Gemma4 仍是明确的低延迟比较／回退候选。

## 10. 命理师视角评审

以下评分是“按高级命理师审稿标准对当前有限样本的工程评审”，不是公认行业量表，也不是
真人应事准确率。分数只用来表达相对位置：`5` 表示能协助但必须逐条审稿，`7` 表示可在
受限范围较稳定独立判断，`8+` 才接近本项目所称高级命理师。

| 专业维度 | Gemma4 | Qwen3.8 | 当前判断 |
| --- | ---: | ---: | --- |
| 基础取数与坐标意识 | 4.5–5.0 | 5.5–6.5 | Qwen 少了根气／路径格式修正，但仍会混淆月令与月干 |
| 旺衰、格局与承载 | 4.0–4.8 | 5.0–5.8 | Qwen 入口更稳，却仍会证据不足直判从财 |
| 做功路径与主次决胜 | 4.0–4.8 | 4.8–5.6 | Qwen 表达更完整，四变体仍需主次决胜修正 |
| 反证与翻盘条件 | 3.8–4.5 | 4.0–4.8 | 两者都没有稳定给出可执行反证，提升很小 |
| 象法与可读表达 | 5.0–6.0 | 6.5–7.5 | Qwen 更像人在断，意象、节奏和具体性明显更好 |
| 事实边界与克制 | 4.0–4.8 | 4.3–5.2 | Qwen 仍会编心理、家庭和确定灾祸，需要本地复核 |
| 岁运应期 | 约 4.0 | 约 4.0–4.5 | 当前样本不足，Qwen 仍会把关系成员直接扩大成事件 |
| 综合独立断命能力 | 4.2–4.8 | 5.2–5.9 | 从不稳定初断助手提升为更有用的审稿型助手 |

### 10.1 提升到底有多大

从命理师角度，当前最诚实的结论是：

> Qwen3.8 相比 Gemma4 提升约一档，综合专业可用性可估为 20%–30% 的提升；文字与取象
> 提升更明显，可能达到 30%–40%，但真正决定高级命理师水平的反证、主次决胜、格局边界
> 和应期克制只提升约 10%–20%。

它不是从“初级命理师”直接变成“高级命理师”，更接近从“容易跑偏的结构化学徒”变成
“有较好语感、能给出可用初稿，但必须由系统和专业审稿收口的中级助手”。

### 10.2 为什么读起来会觉得进步很大

Qwen3.8 更容易形成完整、连贯、有命理意象的中文段落，也更能接受一次一个具体问题。
这会显著提高第一印象。但是命理专业水平不只看“像不像”，还要检查：

1. 月令、藏干、十神和宫位有没有取错；
2. 旺衰与格局是否由全局证据推出；
3. 主线是否真的胜过竞争解释；
4. 什么条件会让当前判断翻转；
5. 原局、运、年是否混层；
6. 关系成员是否被误写成已发生作用；
7. 是否从命盘直接编造心理、家庭、疾病或灾祸。

Qwen 在第 1–3 项已有进步，在第 4–7 项仍不足。这就是“看起来进步大，资格进步中等”的
原因。

## 11. 月令坐标泛化与教师裁判修正

为验证前述“月令与月干仍会混淆”是否能在陌生盘上改善，系统新增第八个合法 A/B 实验和
第五个 DEV Suite：

```text
experiment  v60-mingli-synthetic-experiment-4355419cf3ec29abc246
suite       v60-mingli-synthetic-suite-f1d255f320067d119d27
A           庚午 / 己卯 / 壬午 / 丙午
B           庚午 / 己卯 / 壬午 / 辛亥
```

月令始终是月支卯，月干己才是正官，卯中乙为伤官。A 无根，庚偏印只进入资源竞争；B 以
`hour支藏壬` 取得第一藏干有效根，同时新增辛正印明透。完整时柱也改变财、印、藏干、同支
关系与起运边界，所以本实验只检验坐标纪律和整盘重算，不做单根因果断言。

这一次 Qwen 的主要命理结构表现明显更好：原文写“壬水生于卯月”，没有把己正官叫作
月令；A 给出无根、`UNRESOLVED`，B 给出亥中壬根、`ORDINARY_WEAK`；两盘还分别重编译出
三张与两张候选，并通过唯一主次、排除项、反证、翻转和主路径绑定。严格调用仍很重：

| 变体 | 输入 token | 输出 token | 墙钟时间 |
| --- | ---: | ---: | ---: |
| A | 12,013 | 4,643 | 187.812s |
| B | 10,883 | 4,788 | 202.063s |
| 合计 | 22,896 | 9,431 | 389.875s |

首轮 Evaluator `.009` 将运行
`v60-mingli-synthetic-run-adad4f4f971bd6cdcb2d` 判为 `PASS`。教师逐项读取 raw output
后否定了这个过于乐观的裁判结果：A/B 的四项假设都写
`judgment=SUPPORTED`，但各自方法裁决汇总与模型自己的 `adjudication` 都是
`CONDITIONAL`。本地归一化已经把它们降为 `WORKS_IF / PARTIAL`，旧评尺却没有把这类
原始确定性冲突计入模型失败，也没有要求对应 repair receipt。

Evaluator `.010` 因此加入 raw judgment coherence 复算。对同一份 sealed raw output 的
append-only replay 约 `0.25s`，没有再次调用 Qwen，也没有改 Prompt：

```text
experiment run  v60-mingli-synthetic-run-5eb1438b1dee74c3395e
suite run       v60-mingli-synthetic-suite-run-0ca2f52f7628e6987f7f
changed / hold  27 / 3
outcome         PRODUCT_SAFE_MODEL_FAIL
independence    FAIL
runner errors   0
```

修正后的失败只落在 A/B 的原始判断一致性与修复回执；月令坐标、根／印分离、判型、候选
重编译和主路径均通过。命理师口径应据此更新为：Qwen 对结构事实和方法比较已经有一轮可信
进步，但仍会把“条件成立”说成“已经支持”。这是结论强度与执业克制问题，不能由文字流畅
掩盖，也不能因为本地系统修好了就算模型学会。

这轮不改变前面的有限样本相对估计，也不解锁 `QUALIFICATION / HOLDOUT`。它改变的是本地
裁判：今后模型自己的方法裁决、aggregate adjudication 与最终 judgment 必须同强度，否则
产品可经本地系统降级，模型独立资格仍判失败。

## 12. 当前正式结论

### 已经成立

- Qwen3.8:27B 可以通过 `dblife.com:11888` 稳定返回；
- 官方非思考调用参数和模板已经正确接入；
- Qwen3.8 是本地 Focused Reading 和严格 DEV Agent 的首选候选；
- Gemma4 保留为显式比较与低延迟回退，不静默混用；
- 用户断命已经应用到产品：按主题一次一问、追加保存、刷新恢复；
- 本地系统已经开始从真实 Qwen 错误中蒸馏复核能力；
- 第八个陌生盘上，Qwen 已独立通过月令／月干分离、根气、判型、候选重编译和主路径门；
- Evaluator `.010` 已能识别“原始写支持、实际只条件成立”的确定性冲突；
- 三段式 DEV 探针已经把判型、候选比较和结论强度拆开，并由本地系统重算集合与强度；
- 同一壬水 A/B 的三段运行降至 `141.994s / 13,918 tokens`，缓存重放低于 `0.1s`；
- 普通产品运行不依赖 OpenAI API。

### 仍未成立

- Qwen3.8 尚未通过模型独立资格；
- Qwen3.8 的结论强度仍会高于其自身方法证据，需要本地降级与教师复核；
- 三段探针中的候选 ruling 仍由 Qwen 作出，提示词压缩后 A 的 aggregate 发生变化，
  尚未获得专业 Gold 稳定性；
- 当前输出不能宣称高级命理师正式结论；
- 合成结构实验不能证明真人应事准确率；
- Normalizer 把结果收稳不等于模型已经学会；
- `publication_allowed` 与 canonical fact write 继续关闭。

## 13. 下一阶段专业优先级

1. 已完成三段式 DEV 基础链；下一步为候选 ruling 建立独立教师审阅与专业 Gold，而不是
   继续扩大 Prompt；
2. 严格整盘调用继续只作最终同尺资格考试，不能用拆分后的局部通过冒充整盘独立通过；
3. 用陌生盘继续测月令／月干、藏干身份和判型边界，并记录同 Prompt／跨 Prompt 稳定性；
4. 专门训练“为什么主解释胜出”以及可执行翻盘条件；
5. 建立原局、运、年三层不混用的岁运保持盘；
6. 增加关系成员与实际作用分离的对抗盘；
7. 用长期 LifeCase 验证应事，不用合成结构分数替代现实校准；
8. 达到模型独立与专业复核双通过后，再由 Owner 决定是否开放发布；
9. 产品单主题若仍超过体验目标，优先做安全流式投射或评估 vLLM/SGLang；DEV 候选段则
   继续蒸馏局部方法，不恢复大 Prompt。

## 14. 实施与验证凭证

关键实现：

- `backend/src/abu_v60/mingli/focused_reading_runtime.py`
- `backend/src/abu_v60/mingli/focused_reading_contracts.py`
- `backend/src/abu_v60/mingli/focused_pass_service.py`
- `backend/src/abu_v60/mingli/focused_pass_store.py`
- `backend/src/abu_v60/mingli/reading_summary.py`
- `backend/src/abu_v60/mingli/synthetic_coordinate_discipline.py`
- `backend/src/abu_v60/mingli/synthetic_decision_integrity.py`
- `backend/src/abu_v60/mingli/synthetic_experiment_evaluator.py`
- `backend/src/abu_v60/mingli/synthetic_regime_evaluator.py`
- `backend/src/abu_v60/mingli/synthetic_distillation_contracts.py`
- `backend/src/abu_v60/mingli/synthetic_distillation_logic.py`
- `backend/src/abu_v60/mingli/synthetic_distillation_runtime.py`
- `backend/src/abu_v60/mingli/synthetic_distillation_service.py`
- `backend/src/abu_v60/mingli/synthetic_distillation_store.py`
- `backend/src/abu_v60/api/mingli_stage.py`
- `web/src/components/MingliFocusedReadingLayer.tsx`
- `web/src/mingliFocusedValidation.ts`
- `db/migrations/versions/0048_mingli_focused_readings.py`
- `db/migrations/versions/0049_mingli_progressive_focused_passes.py`
- `db/migrations/versions/0050_mingli_month_coordinates.py`
- `db/migrations/versions/0051_mingli_raw_judgment_coherence.py`
- `db/migrations/versions/0052_mingli_distillation_runs.py`
- `tools/run_mingli_synthetic_distillation.py`

最终验证：

```text
Backend full suite                    475 PASS
Ruff                                  PASS
Runtime Architecture                  PASS
Source maintainability                PASS
TypeScript typecheck                  PASS
Vite production build                 PASS
Database Foundation                   v60.foundation.044 READY
Local Runtime :8060                   READY
Current public Focused Profile         v60.model-serving.mingli-focused-text.008
Current public Focused Normalizer      v60.mingli-focused-normalizer.006
2026-09-04 real Qwen focused response  16.305s final / 25.478s cold prior
Identical append-only cache replay     9ms
Strict month-coordinate Qwen pair      389.875s
Three-pass month-coordinate Qwen pair  141.994s
Three-pass pair tokens                 13,918
Identical three-pass pair replay       <0.1s
Evaluator .010 sealed-output replay    ~0.25s
Database migration head               0052_mingli_distillation_runs
```

## 15. 三段式蒸馏实测与教师结论

三段运行绑定同一 Qwen digest、Provider Profile
`v60.model-serving.qwen38-27b-mingli-distillation.001`、Prompt Hash
`bd5dfb9618cc7bc1d7ddec1d53ea6ebc1509cf5b1ce9c669bde44321a36d79ca`：

| 变体 | 输入 | 输出 | 总 token | 时长 | Run |
| --- | ---: | ---: | ---: | ---: | --- |
| A | 6,251 | 1,425 | 7,676 | 69.684s | `v60-mingli-distillation-run-544e86ed8e20b6fd7aa1` |
| B | 4,804 | 1,438 | 6,242 | 72.310s | `v60-mingli-distillation-run-fc8da8a2364ea2a6c2ee` |

A 原生判型为 `FALSE_FOLLOW_COMPETITION / WEAK`，B 为
`ORDINARY_WEAK / WEAK`，根坐标、印比竞争和月令坐标全部通过。模型最终 certainty 与
本地 aggregate 映射一致，因此没有再出现严格整盘中的“方法只条件成立、最终却写支持”。

但这还不是完整的教师通过。候选段压缩前的 A 把 E015/E016 汇总为
`SUPPORTED/BROKEN`，当前 Prompt 下变成 `BROKEN/BROKEN`；当前 B 为
`SUPPORTED/BROKEN`。本地系统能证明每个 aggregate 是按模型逐项 ruling 正确计算出来的，
却不能在没有专业 Gold 时证明那些 ruling 本身正确。按照高级命理师审稿标准，这一差异
必须保留为“专业稳定性待审”，不能因为两次 `DEV_PASS` 就提升前文的 5.2–5.9 综合评分。

因此本轮结论是：拆题方向正确，速度和确定性收口都有实质进步；下一刀应落在候选方法的
教师标注与反例，不是继续扩写上下文。严格整盘资格、产品 Focused Reading 和三段 DEV
探针维持三个不同用途，不互相冒充。

本文与以下正本共同生效：

- [`17_V60_MINGLI_STAGE_AND_SYNCHRONIZED_NARRATION.md`](17_V60_MINGLI_STAGE_AND_SYNCHRONIZED_NARRATION.md)
- [`18_V60_MINGLI_AGENT_DECISION_AND_BUILD.md`](18_V60_MINGLI_AGENT_DECISION_AND_BUILD.md)
- [`19_V60_MINGLI_COGNITIVE_SYSTEM_CONSTITUTION_V1.md`](19_V60_MINGLI_COGNITIVE_SYSTEM_CONSTITUTION_V1.md)
- [`20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md`](20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md)
- [`21_V60_SYNTHETIC_MINGLI_TRAINING_DESIGN_BRIEF.md`](21_V60_SYNTHETIC_MINGLI_TRAINING_DESIGN_BRIEF.md)
- [`22_V60_V128_EXPERIENCE_INTEGRATION.md`](22_V60_V128_EXPERIENCE_INTEGRATION.md)

若旧文档中的“当前 Gemma4 默认／Qwen3.8 尚未接入”与本文冲突，该句只作为当时历史记录，
当前模型政策以本文和 Runtime Manifest 为准。历史 sealed run、Hash 与当时评估语义保持
不可变。
