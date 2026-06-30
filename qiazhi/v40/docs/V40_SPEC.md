# V40 Spec

更新时间：2026-06-30

## 定位

V40 不是推倒 V30 重写命理能力，而是新建一个独立隔离的运行时骨架：

```text
V40 = Evaluation-First Multi-Engine Product Runtime
```

V30 继续作为当前生产线维护；V40 作为新目录、新数据库、新协议、新运行时骨架启动。V30 成熟模块只能通过 migration-only importer 和 DTO 迁移，不能在 V40 runtime 里直接交叉引用、混用配置、共用数据库表或复用运行缓存。

## 硬隔离边界

| 项目 | V40 边界 |
| --- | --- |
| 目录 | `qiazhi/v40` |
| Python package | `v40` |
| API prefix | `/api/v40` |
| Admin prefix | `/admin/v40` |
| UI prefix | `/v40/ui` |
| Runtime dir | `qiazhi/v40/.runtime` |
| Postgres database | `qiazhi_v40` |
| Postgres table prefix | `v40_` |
| Redis prefix | `v40:` |
| Env file | `.env.v40.local` / `.env.v40.example` |
| Import boundary | V40 runtime 禁止 import `v30.*`；迁移只允许通过显式 migration importer 和可测试的 DTO。 |

## 第一性原则

1. V40 contract-first。
2. V40 evaluation-first：先定义什么叫“算得好”，再谈训练。
3. V40 新骨架，V30 成熟能力通过 migration importer 迁移。
4. 不训练 chart facts：四柱、干支、十神基础映射、地支藏干、排盘事实、大运流年事实不可被训练修改。
5. CentralBrain 不直接下断语，只做调度、状态、反馈归因、训练路由和质量门。
6. DecisionEngine 是唯一 Verdict 生成者。
7. LLM 负责 Expression、Dialogue、Thinking，不做命理裁决，不改 Verdict。
8. ProductProjection + LLMExpressionPipelineV2 + SurfaceOrchestrator 是用户体验主链。
9. Admin Control Plane 和 Evaluation & Training Spine 从第一天进入 V40。
10. 所有训练更新必须可回放、可解释、可验证、可回滚。

## V40 运行时架构

```text
User / Case Input
  -> Intent / Topic Router
  -> CentralBrain EnginePlan
  -> EngineManager
      -> BaziEngine
      -> ZiweiEngine
      -> RealityProbeEngine
  -> EngineRunResult
  -> SignalRegistry
  -> DecisionEngine
  -> Verdict
  -> AdvicePlan
  -> ProductProjection
  -> LLMExpressionPipelineV2
  -> AcceptanceV2 / Repair / Salvage
  -> FinalUserVisibleProjection
  -> SurfaceOrchestrator
      -> ReadingSurface
      -> CalibrationSurface
      -> ConversationSurface
      -> ThinkingSurface
  -> Role Projection
      -> Guest / User / Practitioner / Admin
```

训练验证闭环：

```text
Surface Output / Feedback / Practitioner Calibration / Real Outcome
  -> TrainingLabelEvent
  -> Training Attribution
  -> Local Overlay or Global Candidate Update
  -> TrainingImpactDiff
  -> Golden Case / Synthetic / Regression / Shadow Validation
  -> Release Gate
  -> Versioned Config / Rollback
```

## V40 优先级

| 优先级 | 任务 | 目标 |
| --- | --- | --- |
| P0 | Evaluation Contract | 定义评测样本、指标、门禁和输出质量合约。 |
| P1 | Golden Case Bank | 建立高质量命例、命理师标注、现实反馈和禁止断语边界。 |
| P2 | TrainingLabelEvent | 把用户回答、命理师选择、Admin 标注、现实结果统一成可归因事件。 |
| P3 | TrainingImpactDiff | 每次训练必须说明改变了哪些权重、阈值、Verdict、Advice、Probe。 |
| P4 | Release Gate | Fact、Golden Case、Overclaim、Advice、Probe、LLM、Leakage 门禁。 |
| P5 | Local / Global Learning | 单用户反馈先入 Local Overlay；聚合审核后才进入 Global Weight Version。 |
| P6 | Multi-Engine Runtime | Bazi 主引擎，Ziwei Domain Lens，Reality Probe 校准。 |
| P7 | ProductProjection / LLMExpression | 用户可读表达、对话、Thinking 和泄漏防护。 |

## 不可训练层

这些对象不可被训练、LLM、反馈或 Admin 标注改写：

```text
四柱
干支
十神基础映射
地支藏干
排盘事实
大运流年事实
紫微宫位事实
星曜落宫事实
历法转换结果
```

## 可训练层

V40 训练只允许作用在：

```text
Signal source weight
Claim scoring
Conflict resolution
Assertion threshold
Advice priority
Probe VOI
LLM acceptance / expression policy
Surface leakage / readability policy
```

## 核心契约清单

V40 第一阶段只定义 contract，不写完整业务逻辑：

```text
RuntimeRequest
RuntimeResult
EngineRunRequest
EngineRunResult
RuntimeSignal
SignalRegistrySnapshot
DecisionInputBundle
DecisionVerdict
BranchCandidate
BranchCard
AdvicePlan
ProbeCandidate
ProductProjectionBundle
LLMExpressionTask
LLMExpressionResult
AcceptanceResult
SurfaceBundle
EvaluationCaseSpec
GoldenCase
TrainingLabelEvent
TrainingExampleV2
TrainingImpactDiff
ReleaseGateResult
LocalOverlay
GlobalWeightVersion
```

## V30 -> V40 Migration Map

| V30 能力 | V40 接入方式 | 初期策略 |
| --- | --- | --- |
| 八字排盘与事实层 | `BaziEngineImporter` | 只读 DTO 迁移，不重写算法，不在 V40 runtime 直接调用 V30。 |
| FeatureEvidence | `RuntimeSignal` importer | 保留 evidence refs 和 confidence。 |
| DiagnosisClaim | `RuntimeSignal` importer | 进入 SignalRegistry，不直接生成 Verdict。 |
| Rule / Portrait / Path | `RuntimeSignal` importer | 统一 source、topic、claim、evidence。 |
| DecisionEngine | `DecisionVerdict` importer + shadow compare | 初期输出尽量 shadow 接近 V30，不把 V30 DecisionEngine 放进 V40 主链。 |
| FinalSynthesis | `ProductProjection` importer | 不直接作为 V40 权威断语。 |
| LLM acceptance | `LLMExpressionPipelineV2` | 保留有效边界，重写生命周期。 |
| SurfaceOrchestrator | V40 native | 保留 V30 的 surface 分离原则。 |
| Admin / Evaluation | V40 native | 新 namespace、新数据库、新 job 记录。 |

## Shadow Compare

V40 alpha 必须能对同一个 case 同时运行：

```text
V30 runtime
V40 runtime
```

比较项目：

```text
Verdict 是否一致或更合理
AssertionLevel 是否退化
Advice 是否更清楚
Probe 是否减少重复
LLM 是否可见且不越权
Surface 是否干净
工程语言泄漏率是否接近 0
Golden Case 是否通过
Admin 是否可追踪每次输出
```

## V40 Alpha 最小验收标准

1. V40 可独立安装、启动、测试。
2. V40 不 import `v30.*` runtime 代码。
3. V40 不读写 V30 数据库、表、Redis key、runtime 文件。
4. V40 有完整 contract map。
5. V40 有 `EvaluationCaseSpec`、`TrainingLabelEvent`、`TrainingImpactDiff` 和 `ReleaseGateResult` 初版。
6. V40 可通过 migration importer 接收 V30 导出的 DTO 或 fixture，但 runtime 内部不直接依赖 V30。
7. V40 可以跑最小 shadow compare fixture。
8. 用户侧 ProductProjection 不泄漏工程语言。
9. Admin 可看到 evaluation/training/release gate 的只读结果。

## 当前执行状态

2026-06-30 Phase 1 已启动：

```text
docs/V40_PHASE1_CONTRACTS_AND_TRAINING_SPINE.md
```

本阶段已先落 contract-first 骨架、Evaluation & Training Spine 初版、V30 plain JSON DTO migration 边界和隔离测试。V40 仍不 import `v30.*`，不读取 V30 runtime，不共享 V30 database / Redis / runtime dir。

2026-06-30 Phase 2 已启动：

```text
docs/V40_PHASE2_MIGRATION_IMPORTER_AND_SHADOW_COMPARE.md
```

本阶段把 V30 plain JSON DTO 转为 V40 原生 `RuntimeSignal / DecisionVerdict / AdvicePlan / ProductProjectionBundle`，并生成只读 `ShadowCompareResult`。这里的 importer 是迁移工具，不是 V40 正式 runtime 主链依赖。

2026-06-30 Phase 3 已启动：

```text
docs/V40_PHASE3_API_AND_SCHEMA.md
```

本阶段新增独立 `/api/v40/health`、`/api/v40/contracts`、`/api/v40/shadow-compare` 和 `v40_*` schema 草案。服务只依赖 V40 contracts/migration/evaluation，不接 V30 runtime。

2026-06-30 Phase 4 已启动：

```text
docs/V40_PHASE4_REPOSITORY_HISTORY.md
```

本阶段新增 V40 local repository 和 shadow compare run history。API 可通过 `persist=true` 把 `RuntimeResult` 与 `ShadowCompareResult` 写入 `qiazhi_v40` 的 `v40_*` 表；默认 shadow compare 仍只做内存演练，不写生产结果。

2026-06-30 Phase 5 已启动：

```text
docs/V40_PHASE5_EVALUATION_TRAINING_REPOSITORY.md
```

本阶段新增 `EvaluationCaseSpec`、`TrainingLabelEvent`、`ReleaseGateResult` 的 V40 仓储与最小 API。它们进入质量闭环和 Admin/Lab 控制面，但仍不直接写生产权重，也不改变用户测算结果。

2026-06-30 Phase 6 已启动：

```text
docs/V40_PHASE6_EVALUATION_RUN_AND_IMPACT_DIFF.md
```

本阶段新增确定性 evaluation runner：`EvaluationCaseSpec + RuntimeResult` 生成 `MetricSummary / EvaluationRunResult / ReleaseGateResult`，并进一步生成 `TrainingImpactDiff`。LLM 不参与评测裁判，训练影响差异仍然只作为候选记录，不直接写生产权重。

2026-06-30 Phase 7 已启动：

```text
docs/V40_PHASE7_LAB_ARTIFACTS.md
```

本阶段新增 Lab read model、artifact CLI 和第一条 golden case seed。Admin/Lab 可以读取 V40 质量闭环状态，脚本可以导入/导出评测样本，仍然只操作 V40 数据库。

2026-06-30 Phase 8 已启动：

```text
docs/V40_PHASE8_BATCH_EVALUATION.md
```

本阶段新增 `EvaluationBatchSummary`、批量评测 API、batch repository 和 CLI。V40 可以对一组 case 一次性生成 run、release gate 和 batch summary，为后续 golden bank、synthetic runner 和大规模验证做准备。

2026-06-30 Phase 9 已启动：

```text
docs/V40_PHASE9_CANDIDATE_WEIGHT_VERSION.md
```

本阶段新增候选权重版本登记：通过 batch summary 和 release gate 来源生成 `GlobalWeightVersion(active=false)`。候选版本可追踪、可审计，但不会自动启用生产权重。

2026-06-30 Phase 10 已启动：

```text
docs/V40_PHASE10_RELEASE_READINESS_AND_ACTIVATION_REVIEW.md
```

本阶段新增 `ReleaseReadinessSummary` 与 `WeightActivationReview`。V40 可以聚合多个 batch 的 readiness，并记录候选权重激活审核结果；审核结果仍不执行激活，`activation_applied=false`。

## V40 不做的事

本阶段不做：

- 不直接重写八字核心算法。
- 不直接重写 V30 所有模块。
- 不把紫微与八字平权。
- 不让 LLM 做 Verdict。
- 不启动全自动全局训练。
- 不和 V30 共用数据库表、Redis 前缀、runtime 目录。
- 不把训练逻辑塞进 `brain/`；`brain` 只调度训练。

## 版本路线

```text
V30 = 当前生产线
V40 = 新架构分支
V40-alpha = Admin/Lab shadow only
V40-beta = 部分用户可见
V40-stable = 主线切换
```

切换条件：

```text
V40 能跑完整测算
V40 Verdict 不明显退化
工程语言泄漏率接近 0
LLM visible rate 达标
Probe 重复率下降
Surface 混乱问题解决
Golden Cases 通过
Admin 可追踪每次输出
训练变更可回滚
```
