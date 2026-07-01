# V40-RC2: Mingli Depth Migration

Date: 2026-07-01

## 核心判断

V40 当前不应该继续追求“架构完成度”，而应该进入：

```text
命理纵深迁移 + 真实验收
```

当前应拆成两个指标：

```text
Architecture Completion: ~98%
Mingli Depth Index: ~50-65%
```

框架已经站住，下一步要把 V30 的命理资产萃取进 V40 原生链路：

```text
Engine
→ RuntimeSignal
→ Decision
→ Advice
→ Probe
→ Training
→ Evaluation
```

## 新指标

新增：

```text
GET /api/v40/project/mingli-depth-index
```

六个维度：

| Domain | 含义 |
| --- | --- |
| Fact Depth | 排盘事实深度 |
| Signal Depth | 信号覆盖深度 |
| Domain Depth | 领域判断深度 |
| Probe Depth | 现实校准深度 |
| Training Depth | 训练闭环深度 |
| Evaluation Depth | 验收案例深度 |

## 优先级

```text
P0: Real Case Bank / Acceptance Window
P1: Bazi Fact Engine Pro
P2: V30 Mingli Asset Migration Pipeline
P3: Domain Verdict Adapters
P4: Hidden Factor Probe Engine
P5: Knowledge / Portrait enrichment
```

## P0: Real Case Bank / Acceptance Window

第一版目标：

```text
100-200 个高质量案例
```

Case 类型：

- Golden Case：命理师标注案例。
- Regression Case：V30/V40 已表现稳定案例。
- Synthetic Case：结构覆盖案例。
- Real Feedback Case：真实用户反馈案例。
- Edge Case：容易过度断言的复杂盘。

每个 case 至少包含：

```text
birth_input / 四柱
用户问题
topic / domain
已知现实反馈
expected_signals
expected_branches
expected_verdicts
expected_advice
expected_probes
allowed_assertions
forbidden_assertions
common_failure_modes
```

验收不追求“标准答案”，而是约束：

```text
可以说什么
不能说什么
必须谨慎什么
应该追问什么
建议应该落在哪个方向
```

## P1: Bazi Fact Engine Pro

只产出：

```text
facts
features
evidence seeds
```

必须支持：

- 公历/农历转换。
- 节气定月。
- 真太阳时选项。
- 时区/出生地策略。
- 四柱排盘。
- 大运起运。
- 流年注入。
- 十神映射。
- 藏干。
- 合冲刑害破。
- 基础五行能量。

不允许：

- 不判断财运好坏。
- 不输出 Advice。
- 不下 Verdict。
- 不被训练改写排盘事实。
- 不绑定 LLM。

## P2: V30 Mingli Asset Migration Pipeline

迁移不是搬代码，而是萃取命理资产：

```text
V30 asset
→ Plain JSON DTO
→ Asset Classifier
→ V40 Adapter
→ RuntimeSignal / KnowledgeCard / ProbeTemplate / TrainingRule
→ Evaluation Gate
→ Candidate Enablement
```

分层：

| Tier | V30 来源 | V40 目标 |
| --- | --- | --- |
| T0 | `core`, `evidence`, `ten_god_energy` | facts / evidence / RuntimeSignal |
| T1 | `rules`, `diagnosis/rule_matcher`, `feature_engine` | RuntimeSignal / CandidateSeed |
| T2 | `structure`, `mainline`, `path_engine` | PathSignal / GraphSignal / ConflictSignal |
| T3 | `portrait`, `portrait_engine` | low-weight PortraitSignal |
| T4 | `knowledge` | KnowledgeCard / ExplanationBasis |
| T5 | `questions`, `dialogue_chain`, `text_options` | ProbeTemplate / ConversationSeed |

## P3: Domain Verdict Adapters

第一批领域：

```text
wealth
career
relationship
health_pressure
family
useful_god
luck_timing
```

每个 adapter 输出：

```text
DomainCandidate
DomainBranch
DomainVerdictHint
DomainAdviceSeed
DomainProbeCandidate
DomainRiskBoundary
```

不能直接输出最终 Verdict，仍由 DecisionEngine 裁决。

## P4: Hidden Factor Probe Engine

Probe 必须能更新结构，不只是聊天问题。

链路：

```text
DomainBranch / Conflict / AdviceGap
→ ProbeCandidate
→ ConversationSurface
→ UserAnswer
→ AnswerSignal
→ HiddenAttributeUpdate
→ TrainingLabelEvent
→ LocalOverlay
→ 后续 Verdict / Advice / Conversation
```

第一批 hidden attributes：

```text
wealth_manifestation_mode
wealth_capture_ability
wealth_leakage_pattern
partnership_money_effect
career_path_mode
authority_pressure_source
platform_support_level
relationship_binding_mode
emotional_security_pattern
mobility_opportunity_mode
support_system_strength
stress_recovery_pattern
```

## 硬原则

- 不直接 import V30，只通过 plain JSON DTO。
- V30 rules 不直接生成 Verdict，只生成 RuntimeSignal / CandidateSeed / Evidence。
- V30 knowledge 不直接裁决，只生成 KnowledgeCard / ExplanationBasis。
- V30 portrait 不直接输出用户断语，只生成低权重 PortraitSignal。
- 所有迁移资产必须有 evidence_ref、domain、claim_key、confidence、assertion_hint、max_assertion_level。
- 所有迁移资产先 `sidecar`，再 `evaluating`，最后 `enabled`。
- 每次迁移必须跑 before/after diff。
- 训练结果必须说明影响了哪些 signal / candidate / verdict / advice / probe。
- 不允许迁移后提升 overclaim rate。

## 下一步

Sprint 1:

```text
Acceptance Window + Migration Gate
```
