# V30 Multi-Engine Architecture 主线设计

更新时间：2026-06-30

## 当前主线 Review

V30 当前主线已经形成以下核心链路：

```text
八字事实 / 规则 / 画像 / 特征 / 做功路径
-> Signal Registry
-> Decision Engine
-> Final Synthesis
-> LLM Expression
-> 用户结果 / 智能对话 / 训练验证
```

已完成的关键基础：

- Decision-Centered Architecture：最终断语只能来自 `DecisionVerdict`。
- Production Orchestrator / Signal Registry：模块产出已经能结构化进入信号总线。
- Dialogue Chain：智能对话已经从测算步骤里拆出独立 surface。
- Text-to-Option / Practitioner Selection：分支、候选、选择和训练反馈已经有结构化入口。
- Ziwei Domain Lens：紫微 V1 已落标准、36 条领域规则、Probe 映射和旁路 adapter，决策权重为 0。

当前缺口不是缺模块，而是缺一个统一的“引擎调用层”。如果继续让中枢大脑直接调各种模块，后续八字、紫微、现实探针、合婚、风水、地点等能力会重新变成一团。

## 系统宪法

V30 正式进入 Multi-Engine Architecture：

```text
所有命理能力必须以 Engine 形式接入。
Engine 只能输出 Facts / Features / Signals / ProbeCandidates。
Engine 不允许直接输出最终用户断语。
所有 Signal 必须进入 SignalRegistry。
DecisionEngine 是唯一 Verdict 生成者。
CentralBrain 负责 EnginePlan、状态调度、Dialogue Chain 和训练路由。
LLM 只负责表达、解释、对话措辞和边界复核。
```

一句话：

```text
CentralBrain 决定问谁；DecisionEngine 决定能说什么。
```

## 目标架构

```text
Central Brain
  ↓
EnginePlan
  ↓
EngineManager
  ↓
BaziEngine / ZiweiEngine / RealityProbeEngine
  ↓
EngineRunResult
  ↓
SignalRegistry
  ↓
Module / Engine Audit
  ↓
DecisionEngine
  ↓
Advice / FinalSynthesis
  ↓
LLM Expression
  ↓
User Surface
```

## 引擎分工

| Engine | 定位 | 输出 | 是否裁决 |
| --- | --- | --- | --- |
| `BaziEngine` | Primary Engine | ChartContext、FeatureEvidence、结构、路径、规则、画像、BaziSignal | 否 |
| `ZiweiEngine` | Domain Lens Engine | ZiweiChart、ZiweiSignal、ProbeTriggerCandidate | 否 |
| `RealityProbeEngine` | Calibration Engine | ProbeCandidate、AnswerSignal、HiddenAttribute、ManifestationProfile | 否 |
| `DecisionEngine` | Verdict Judge | DecisionVerdict | 是 |
| `LLMAdapter` | Expression Adapter | 用户可读文字 | 否 |

## 第一阶段范围

本阶段只做薄抽象层，不改现有主链：

- 新增 `v30.engines.contracts`。
- 新增 `EnginePlan / EngineRunRequest / EngineRunResult / EngineAuditEntry`。
- 新增 `EngineManager`，负责按 plan 调 adapter 并注册 signals。
- 新增 `BaziEngine adapter`，包装现有 runtime，不重写八字。
- 新增 `ZiweiEngine adapter`，接 `v30.ziwei`，仅在明确匹配紫微 rule 时输出旁路 signal。
- 新增 `RealityProbeEngine adapter`，包装 hidden factor、question outcomes 和 dialogue probe。
- 新增专项测试，证明 Engine 层不会改变现有 `DecisionVerdict`。

## 调度策略 V1

### 初次完整测算

```text
必跑：BaziEngine
可跑：ZiweiEngine signal_sidecar
可跑：RealityProbeEngine probe_trigger
```

### 用户问财富、事业、关系、迁移、健康压力、田宅资产

```text
BaziEngine = primary_decision_source
ZiweiEngine = domain_lens_sidecar, weight 0
RealityProbeEngine = probe_if_conflict_or_low_confidence
```

### 八字 Verdict 强

紫微同向只作为辅助解释和命理师观察，不改变断语。

### 八字 Verdict mixed

紫微最有价值的作用是触发 Reality Probe，而不是直接裁决。

### 用户现实回答与紫微冲突

现实回答优先进入显化权重和隐藏属性校准；紫微信号保留为 latent / not_manifested / context_blocked，不直接说紫微错，也不强行覆盖用户现实。

## 权重策略

V1 固定：

```text
BaziEngine weight = 1.0
ZiweiEngine weight = 0.0
RealityProbeEngine weight = 0.4
LLM weight = 0.0
```

注意：RealityProbe 权重高于紫微，但仍不能改命盘事实，也不能绕过 DecisionEngine。

V2 才考虑：

```text
ZiweiEngine weight = 0.05 - 0.15
```

前提是通过 golden cases、Reality Probe 支持率、冲突分布和 518K 分布观察。

## 任务计划

- `ME-0`：文档化 Multi-Engine Architecture 和系统宪法。
- `ME-1`：新增 engine 契约和 EnginePlan。
- `ME-2`：新增 BaziEngine adapter，包装现有 runtime。
- `ME-3`：新增 ZiweiEngine adapter，接 Ziwei Domain Lens。
- `ME-4`：新增 RealityProbeEngine adapter，包装现实校准信号。
- `ME-5`：新增 EngineManager 和 EngineAudit。
- `ME-6`：专项测试，验证不改变 DecisionVerdict、不让紫微污染用户断语。
- `ME-7`：后续接 Admin/Lab engine audit 页面。
- `ME-8`：后续接 CentralBrain EnginePlan runtime 调度。

本轮执行 `ME-0` 到 `ME-6`。
