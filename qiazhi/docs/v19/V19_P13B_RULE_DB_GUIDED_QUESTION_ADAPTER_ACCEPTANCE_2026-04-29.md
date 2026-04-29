# V19 P13-B Rule DB Guided Question Adapter 验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

P13-B 的目标是让 V19 智能系统开始使用八字规则数据库生成用户引导问题。

重点：

```text
Rule DB 用于生成好问题
不是直接生成预测结论
```

合法链路：

```text
Bazi Rule DB
→ Structural Rule Signals
→ Guided Question Context
→ Dynamic Guided Questions
→ Oracle Question Builder
```

## 2. 已完成能力

### 2.1 后端 Guided Question Adapter

新增：

```text
v19/bazi_guided_questions.py
```

能力：

```text
- 读取 Bazi Rule DB
- 读取当前 chart / time_context
- 基于规则 category 与命盘事实生成 structural rule signals
- 将 signals 转成安全的动态引导问题
- 返回 guided_question_context
```

### 2.2 接入 API

已接入：

```text
/api/agent/structure
/api/agent/turn
```

返回新增字段：

```text
guided_question_context
```

结构：

```text
available
runtime_scope
rule_signal_count
question_count
signals
questions
guardrails
```

### 2.3 前端 Question Builder 动态合并

更新：

```text
v19/frontend/assets/oracle.js
```

能力：

```text
- 读取 guided_question_context.questions
- 合并静态 QUESTION_LIBRARY 与动态问题
- 动态问题支持 zh / en / ko label
- 点击动态问题后写入 message
- 动态问题仍可提交 helpful / not helpful 反馈
```

## 3. 当前支持的知识触发问题

### 3.1 墓库结构

触发条件：

```text
命盘出现辰 / 戌 / 丑 / 未
或大运 / 流年出现墓库地支
```

生成问题示例：

```text
这张命盘里的墓库结构，应该如何只按结构层阅读？
大运或流年出现墓库时，哪些部分只是时间背景而不是预测结论？
```

### 3.2 地支关系

触发条件：

```text
命盘或时间背景出现六合 / 六冲 / 三合等关系
```

生成问题示例：

```text
当前命盘或时间背景触发了哪些冲合关系，它们在结构层代表什么？
```

### 3.3 十神元数据

触发条件：

```text
Ten God rule DB record 可用
```

生成问题示例：

```text
十神标签在这里为什么只是关系元数据，而不是断语？
```

### 3.4 财富结构候选

触发条件：

```text
income_stability / wealth 相关规则可用
```

生成问题示例：

```text
财星、食伤、比劫这些财富结构候选，如何只作为收入稳定性的证据来源？
```

### 3.5 时间结构边界

触发条件：

```text
time_structure rule DB record 可用
```

生成问题示例：

```text
规则库中的时间结构为什么只用于引导提问，而不直接改变结果？
```

### 3.6 格局索引边界

触发条件：

```text
pattern_structure rule DB record 可用
```

生成问题示例：

```text
格局索引为什么现在只作为结构目录，而不是命运判断？
```

## 4. 护栏

后端返回：

```text
RULE_DB_GUIDES_QUESTIONS_ONLY
NO_RESULT_MUTATION
NO_FORTUNE
NO_TIME_AWARE_INFERENCE
```

前端继续过滤：

```text
未来财运
今年好坏
什么时候发财
fortune
future wealth
good luck
bad luck
```

## 5. 明确未做

本阶段没有做：

```text
- 不改变 income_stability
- 不改变 ResultCard
- 不改变 /oracle 主推理结果
- 不把 Time Context 变成预测
- 不让 LLM 决定问题
- 不让 R4 盲派/神煞/断语进入动态问题
```

## 6. 设计意义

这一步让 V19 从固定问题库进入：

```text
知识库驱动的智能引导提问
```

但仍保持：

```text
结构问题
边界问题
证据问题
非预测问题
```

## 7. 下一步建议

下一步可以进入：

```text
P13-C：Rule DB Structural Signal Panel
```

目标：

```text
在 Oracle / Lab 中展示当前有哪些 Rule DB signals 被触发
用户看到的是“为什么推荐这些问题”
不是“系统预测了什么”
```
