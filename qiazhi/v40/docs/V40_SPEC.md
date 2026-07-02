# V40 Spec

更新时间：2026-07-02

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
11. Practitioner Lens 是同一测算页面上的命理师断项池，不是单独测算页，也不是 Admin。
12. Probe V2 必须绑定明确目标、选项和影响预览，不能只是宽泛追问。
13. 用户侧 `/v40/ui` 必须由显式状态机驱动：setup / running / report / conversation / practitioner。

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

Phase 60 adds the professional selection layer:

```text
ProductProjection
  -> SystemAssertionCandidate
  -> MingliCandidateBoard
  -> PractitionerSelection
  -> TrainingLabelEvent + LocalOverlay
  -> Probe V2 when evidence gain is useful
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
BaziChartFacts
BirthInputCanonical
ZiweiChartFacts
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
ConversationSeed
ConversationTurn
LLMExpressionTask
LLMExpressionResult
AcceptanceResult
ExpressionTelemetry
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

2026-06-30 Phase 11 已启动：

```text
docs/V40_PHASE11_ADMIN_AND_ACTIVATION_EXECUTION.md
```

本阶段新增 `WeightActivationExecution` 和独立 Admin/Lab 前端服务。候选权重可以在 approved review、rollback version 和显式确认语齐备时写入 V40 控制面 active 状态；这仍然只作用于 `qiazhi_v40` 的 `v40_*` 表，不写 V30，不改 chart facts。

2026-06-30 Phase 12 已启动：

```text
docs/V40_PHASE12_NATIVE_BAZI_AND_SYNTHETIC_CASES.md
```

本阶段新增 `BaziChartFacts`、`SyntheticCaseSeed`、V40 原生 Bazi engine skeleton 和 synthetic case generator。V40 可以在不读取 V30 runtime 的情况下，从已校准 chart facts 生成 signals、verdict、advice、probe 和 product projection，并进入 evaluation loop。

2026-06-30 Phase 13 已启动：

```text
docs/V40_PHASE13_NATIVE_DECISION_OUTPUT_RUNTIME.md
```

本阶段把 Phase 12 的临时产出拆成正式 runtime 链路：BaziEngine 只输出 facts/features/signals，SignalRegistry 收集素材，DecisionEngine 生成 branches/verdicts/advice/probes，ProductProjection 和 SurfaceBundle 负责用户端与命理师端展示。命理师校准通过 `TrainingLabelEvent(source=practitioner_selection)` 回流训练闭环，不直接改 chart facts、不直接写全局权重、不写 V30。

2026-06-30 Phase 14 已启动：

```text
docs/V40_PHASE14_NATIVE_BAZI_FACT_SIGNAL_ADAPTERS.md
```

本阶段新增 `v40/engines/bazi_adapters.py`，把显性十神、用神候选、原局/时运地支合冲和领域信号抽成原生 adapter。BaziEngine 仍只产出 facts/features/signals，不做最终裁决；DecisionEngine 可以用这些更具体的信号回答财运、关系、健康等主题问题，避免退回结构空话。

2026-06-30 Phase 15 已启动：

```text
docs/V40_PHASE15_NATIVE_BATCH_EVALUATION.md
```

本阶段新增 V40 native batch evaluation：从 synthetic seeds 一对一生成 native runtime、EvaluationCaseSpec、EvaluationRunResult、ReleaseGate 和 EvaluationBatchSummary。V40 因此可以直接评测原生引擎变更，不再只依赖 V30 DTO shadow compare。

2026-06-30 Phase 16 已启动：

```text
docs/V40_PHASE16_LLM_EXPRESSION_ACCEPTANCE.md
```

本阶段新增 LLM expression acceptance：从 RuntimeResult 生成 `LLMExpressionTask`，接收本地表达或外部 provider 文本为 `LLMExpressionResult`，再由 `AcceptanceResult` 扫描工程语言泄漏、越界断语、chart fact mutation 和 verdict mutation。LLM 仍只负责表达，不拥有 verdict authority。

2026-06-30 Phase 17 已启动：

```text
docs/V40_PHASE17_OLLAMA_EXPRESSION_PROVIDER.md
```

本阶段把 expression contract 接到真实 Ollama provider。`execution_mode=ollama` 会读取 V40 独立的 `V40_LLM_*` 配置，并按 V30 `ollama_native` thinking 链路调用 `/api/chat`：`think=true`、`messages=system+user`、`num_predict` 在 thinking 模式下至少 2400、timeout 至少 180 秒。返回 `LLMExpressionResult` 后仍必须通过 `AcceptanceResult`。如果模型不可用，API 明确返回不可用，不做本地表达 fallback。

本阶段同步修正 expression acceptance：LLM 可以把产品结论改写得更自然，但必须保留核心命理术语和建议语义。验收不再要求逐字模板匹配；它以允许断言的关键词/短语覆盖来判断是否保留 Verdict，同时继续硬拒绝工程语言泄漏、越界断语和 chart fact mutation。

2026-06-30 Phase 18 已启动：

```text
docs/V40_PHASE18_LLM_OBSERVABILITY_AND_EVALUATION.md
```

本阶段新增 `ExpressionTelemetry`，把表达层是否 accepted、provider/model、thinking trace 字数、repair reasons、leakage/overclaim hits 等记录为观测数据。`POST /api/v40/expression/from-runtime` 返回 telemetry；`EvaluationRunFromRuntimeRequest` 可携带 telemetry 并进入 `MetricSummary.expression_acceptance_rate` 与 `expression_thinking_trace_rate`。Release gate 的 LLM gate 现在同时要求无 LLM 边界违规且表达层通过 acceptance。

本阶段还新增 Ollama 模型发现：`GET /api/v40/expression/provider/ollama/models` 读取 `/api/tags`，Admin 通过 `/admin/v40/api/llm` 与 `/admin/v40/api/llm-models` 展示当前模型、effective thinking token/timeout 和模型列表。该能力只读，不写 V30，不写 V40 production。

2026-06-30 Phase 19 已启动：

```text
docs/V40_PHASE19_NATIVE_REPORT_RUNTIME.md
```

本阶段新增第一个产品侧 V40 测算入口：`POST /api/v40/readings/native-report`。它一次性运行 native Bazi runtime、expression、acceptance 和 telemetry，并把 `expression_task / expression_result / acceptance_result / expression_telemetry` 绑定回 `RuntimeResult`。调用者可以选择 `execution_mode=local|provider_text|ollama`；如果请求 Ollama 且模型不可用，接口返回 `503`，不使用本地 fallback。该入口仍不读 V30、不写 V30、不允许 LLM 改 Verdict、不允许 LLM 创建 chart facts。

2026-06-30 Phase 20 已启动：

```text
docs/V40_PHASE20_USER_REPORT_UI.md
```

本阶段新增第一个 V40 用户侧页面：`GET /v40/ui`。页面只保留最小 report-first 流程：输入四柱/大运/流年/问题，选择 `local` 或 `Gemma4`，调用 `POST /api/v40/readings/native-report`，优先展示 accepted report text，并显示 provider/model、thinking trace 字符数和 acceptance status。如果 Gemma4 不可用，页面展示模型错误，不做本地 fallback。

2026-06-30 Phase 21 已启动：

```text
docs/V40_PHASE21_CONVERSATION_SEEDS.md
```

本阶段新增 `ConversationSeed` 与 `v40/conversation/seeds.py`。native report 在 accepted report text 形成后，会基于 probes、verdicts 和 advice plans 生成最多三个下一问种子，并返回 `conversation_seeds` 与 `runtime.conversation_seeds`。`/v40/ui` 会把这些种子显示为“继续追问”按钮，保持 report first、dialogue invited、conversation separate。

2026-06-30 Phase 22 已启动：

```text
docs/V40_PHASE22_CONVERSATION_TURN_RUNTIME.md
```

本阶段新增 `ConversationTurn`、`v40/conversation/turns.py` 和 `POST /api/v40/conversation/turn`。用户点击种子问题或直接输入追问后，会以当前 accepted report 和 runtime 中的 verdict/advice/probe 为上下文生成一轮独立对话回答，并返回下一组 seeds。该对话 runtime 不重跑测算、不刷新 report、不写 V30、不写 V40 production，LLM 仍只负责表达和 dialogue，不拥有 verdict authority，也不能创建 chart facts。

2026-06-30 Phase 23 已启动：

```text
docs/V40_PHASE23_CONVERSATION_FEEDBACK_PERSISTENCE.md
```

本阶段新增 `v40_conversation_turns`、`save_conversation_turn / list_conversation_turns` 和 `v40/conversation/feedback.py`。每轮 `ConversationTurn` 可以转成 `TrainingLabelEvent(local_only=true)`，记录用户点击推荐追问或直接追问的反馈价值。`POST /api/v40/conversation/turn` 返回 `training_label`，并可通过 `persist=true` 保存对话，通过 `persist_training_label=true` 保存训练标签；默认仍不依赖数据库，且不写 V30、不写 V40 production weight、不改 chart facts。

2026-06-30 Phase 24 已启动：

```text
docs/V40_PHASE24_USER_SURFACE_PRODUCTIZATION.md
```

本阶段把用户侧定位收敛为 `report-first / conversation-after / feedback-to-training`。`/v40/ui` 增加主题选择，隐藏普通用户不需要看到的 provider/model/base URL/acceptance status/thinking 字符数，把状态翻译为“结构分析完成、表达已生成、可以继续追问”。报告和对话区新增轻反馈按钮，内部映射为 `TrainingLabelEvent(local_only=true)`，但用户不需要看到训练事件名。

2026-06-30 Phase 25 已启动：

```text
docs/V40_PHASE25_ZIWEI_DOMAIN_LENS_V1.md
```

本阶段新增 `ZiweiChartFacts` 和 `v40/engines/ziwei_native.py`。紫微在 V40 V1 中定位为 Domain Lens：可选传入 `ziwei_chart_facts` 后，runtime 会生成 `EngineRunResult(engine=ziwei)` 和 `RuntimeSignal(source=ziwei_engine)`，并进入 `MultiEngineRunResult / SignalRegistry`；但 `decision_weight=0`，DecisionEngine 在 Phase 25 会过滤紫微信号，不让它进入最终 verdict 输入。也就是说，紫微已经进入 V40 框架，但只作为旁路事实/信号和未来命理师视角，不与八字主引擎平权。

2026-06-30 Phase 26 已启动：

```text
docs/V40_PHASE26_ZIWEI_VALIDATION_SPINE.md
```

本阶段把紫微三阶段路线写入主线：V0 固定排盘事实，V1 进入 `SignalRegistry` 但 `decision_weight=0`，V2 才在验证后以 0.05-0.15 轻量参与 DecisionEngine。新增 `BirthInputCanonical`，明确 `can_run_ziwei` 与 `ziwei_input_quality`，避免系统只凭四柱硬跑紫微。`ZiweiChartFacts` 增加十二宫、四化、大限、流年字段；`ZiweiEngine` 增加专题宫位映射和 ProbeTrigger；Evaluation 新增 `ziwei_sidecar_signal_rate` 与 `cross_engine_topic_agreement_rate`，只做观测，不进入 release gate。

2026-06-30 Phase 27 已启动：

```text
docs/V40_PHASE27_PRACTITIONER_LENS.md
```

本阶段新增命理师专业视角 `practitioner_lens`，挂在 `SurfaceBundle.surfaces[calibration]`。普通用户只得到 `available=false`，命理师可以看到八字信号数量、紫微信号数量、同向主题、紫微旁路信号、紫微触发的 Probe、分支数量和人话校准动作。该视角不是 Admin，也不是第二份报告，不改 verdict、不改 chart facts、不写全局权重；后续校准动作会通过训练事件进入闭环。

2026-06-30 Phase 28 已启动：

```text
docs/V40_PHASE28_PRACTITIONER_CALIBRATION_LOOP.md
```

本阶段把命理师专业视角的动作接入训练闭环。`POST /api/v40/calibration/practitioner-lens-action` 会把 `more_like_this / supporting_context / do_not_use_now / ask_to_confirm / user_mismatch` 转换为 `TrainingLabelEvent(source=practitioner_selection, local_only=true)`，同时生成 `LocalOverlay(expires_after_reading=true, global_update_allowed=false)`。新增 `v40_local_overlays` 表和 `GET /api/v40/calibration/local-overlays`。该流程只记录本次 reading 的局部反馈和训练素材，不改命盘事实、不改当前 verdict、不写 V40 production weight、不写 V30 状态。

2026-06-30 Phase 29 已启动：

```text
docs/V40_PHASE29_PRACTITIONER_UI_CALIBRATION.md
```

本阶段把命理师校准闭环接入 `/v40/ui`。页面新增 `role_key` 选择，普通用户仍只看到报告、反馈和继续追问；命理师模式下，在报告形成后显示 `practitioner_lens` 校准面板。校准面板最多展示 6 条紫微旁路信号或分支候选，每个动作调用 `POST /api/v40/calibration/practitioner-lens-action`，只生成 `TrainingLabelEvent + LocalOverlay`，不会重跑报告、不会刷新对话、不会直接改 verdict 或 production weight。

2026-06-30 Phase 30 已启动：

```text
docs/V40_PHASE30_TRAINING_EXAMPLE_COMPILATION.md
```

本阶段新增训练样本编译层。`POST /api/v40/training/example-from-reading` 会从指定 `reading_id` 读取已保存的 `TrainingLabelEvent` 与 `LocalOverlay`，编译为 `TrainingExampleV2`，并可保存到 `v40_training_examples`。新增 `GET /api/v40/training/examples`。该样本只进入训练/验证材料链路，`expected_update.scope=local_overlay_first`，并明确 `global_update_requires_release_gate=true`；没有标签时拒绝生成样本，避免空训练。

2026-06-30 Phase 31 已启动：

```text
docs/V40_PHASE31_ADMIN_FEEDBACK_SUMMARY.md
```

本阶段把反馈闭环接入独立 Admin Control Plane 的只读摘要。`/admin/v40` 新增 `Training Feedback` section，展示 `training_label_events / local_overlays / training_examples` 三类计数，并列出最近的 `latest_training_examples` 与 `latest_local_overlays`。该控制面仍然只读，不启动训练、不写 production weight、不写 V30，也不把 Admin 功能塞回用户主系统。

2026-06-30 Phase 32 已启动：

```text
docs/V40_PHASE32_TRAINING_EXAMPLE_REPLAY.md
```

本阶段新增 `TrainingExampleReplayResult` 与 replay 运行时。`POST /api/v40/training/replay-example` 会把 `TrainingExampleV2` 与当前 `RuntimeResult` 对齐，检查反馈目标是否仍能在 signal / branch / verdict / advice / probe / projection / conversation seed / evidence refs 中找回，并计算 `target_coverage_rate`、`feedback_alignment_score`、正负反馈数量和 `needs_probe` 数量。新增 `v40_training_example_replays` 与 `GET /api/v40/training/example-replays`。Replay 是确定性评估，不让 LLM 当 judge，不改 verdict，不写 production weight，不写 V30。

2026-06-30 Phase 33 已启动：

```text
docs/V40_PHASE33_TRAINING_REPLAY_BATCH.md
```

本阶段新增 `TrainingReplayBatchSummary`。`POST /api/v40/training/replay-batches` 会聚合多条 `TrainingExampleReplayResult`，统计 replay 通过/复核/阻断数量、平均反馈对齐分、平均目标覆盖率和失败原因分布。新增 `v40_training_replay_batches` 与 `GET /api/v40/training/replay-batches`。推荐规则为：存在 blocked 则 reject，全部 passed 则 approve，其余 needs_review。该 approve 只表示反馈 replay 具备进入候选训练的资格，不发布生产权重。

2026-06-30 Phase 34 已启动：

```text
docs/V40_PHASE34_PROJECT_STATUS_DASHBOARD.md
```

本阶段新增 V40 项目完成度状态。`GET /api/v40/project/status` 会聚合 roadmap 与 `lab_summary.counts`，输出当前 phase、总体完成度、architecture / user_beta / training_validation / v30_replacement 四条主线进度、实时证据计数和下一步任务。`/admin/v40` 新增 `V40 Completion` 面板，并通过 `/admin/v40/api/project-status` 每 15 秒刷新一次。该状态只读，不启动训练、不写 production weight、不作为发布批准。

2026-06-30 Phase 35 已启动：

```text
docs/V40_PHASE35_REPLAY_BATCH_CANDIDATE_WEIGHT.md
```

本阶段把通过的 `TrainingReplayBatchSummary` 接入候选权重登记：`POST /api/v40/weights/candidates/from-replay-batch` 会生成 `GlobalWeightVersion(active=false)`，并可保存到 `v40_global_weight_versions`。该入口要求 replay batch 已 approve、不能允许 production write、且必须有 replay evidence；它只把训练反馈验证结果变成可审计的候选版本，不激活权重、不改用户报告、不写 V30。

2026-06-30 Phase 36 已启动：

```text
docs/V40_PHASE36_RELEASE_READINESS_EVIDENCE_BATCHES.md
```

本阶段新增 `build_release_readiness_from_evidence_batches` 与 `POST /api/v40/release-readiness/from-evidence-batches`，把 `EvaluationBatchSummary` 和 `TrainingReplayBatchSummary` 一起聚合进 `ReleaseReadinessSummary`。新入口要求 evaluation evidence 与 replay evidence 同时存在且都 approve，平均分达到阈值且没有失败原因时才 approve；缺任一证据只给 `needs_review`。旧 `from-batches` evaluation-only 接口保留兼容。

2026-06-30 Phase 37 已启动：

```text
docs/V40_PHASE37_ADMIN_CANDIDATE_RISK.md
```

本阶段新增 Admin 只读 read model：`GET /admin/v40/api/weight-risk`。它把候选权重、readiness 推荐、rollback version 和下一步动作合成 `ready / review / blocked` 风险摘要，并在 Admin 页面展示 `Candidate Risk` 面板。该能力只读，不激活权重、不写 V40 production、不写 V30。

2026-06-30 Phase 38 已启动：

```text
docs/V40_PHASE38_SHADOW_COMPARE_BATCH_RISK.md
```

本阶段新增 `ShadowCompareBatchSummary`、`build_shadow_compare_batch_summary` 与 `POST /api/v40/shadow-compare/batch`，允许一次提交多份 `V30ExportEnvelope` plain JSON DTO，批量生成 `ShadowCompareResult` 并汇总迁移风险。通过口径聚焦 import coverage、verdict topic overlap、product projection ready 和 leakage free；该流程仍不 import V30 runtime、不写 V30、不写 V40 production。

2026-06-30 Phase 39 已启动：

```text
docs/V40_PHASE39_USER_SURFACE_BETA_READINESS.md
```

本阶段新增 `GET /api/v40/surface/beta-readiness`，把用户侧 report-first、报告后追问、反馈入训练、命理师校准、Admin 分离和无静默 fallback 六项作为 beta readiness 检查。`/v40/ui` 顶部只显示“报告优先 · 可继续追问”这种用户可理解状态，不暴露工程检查项或 production weight 语言。

2026-06-30 Phase 40 已启动：

```text
docs/V40_PHASE40_V30_REPLACEMENT_READINESS.md
```

本阶段新增 `build_v30_replacement_readiness` 与 `GET /api/v40/project/v30-replacement-readiness`，把 shadow compare、evaluation/readiness、训练反馈回放、candidate weight 审计、用户侧 beta readiness 和 V40 隔离边界合成 V30 replacement candidate readiness。该接口只给候选替代状态，仍保留真实命例质量判断、最终产品验收和线上切换窗口三项人工确认。

2026-07-01 RC2 Policy Registry Persistence 已启动：

```text
docs/V40_RC2_POLICY_REGISTRY_PERSISTENCE.md
```

本阶段把 `BatchTrainerV1` 产出的 `TrainablePolicyRegistry` 接入 V40 持久化与 Admin 观察面，并按命理高迭代原则默认训练后直接生效。新增 `v40_trainable_policy_registries`、`POST /api/v40/training/policy-registries`、`GET /api/v40/training/policy-registries`、`GET /api/v40/training/policy-registries/active`、`BatchTrainerV1Request.persist_registry` 与 `/admin/v40/api/policy-registries`。同时 `RuntimeRequest / RuntimeResult` 增加 `policy_version_used`，用于记录本次测算采用的策略版本。该链路允许 active policy 快速迭代，但每次生效都保留 previous registry、previous policy 和 impact diff 作为回滚与补救依据；仍然不改命盘事实、不让 LLM 成为裁决者。

2026-06-30 Phase 41 已启动：

```text
docs/V40_PHASE41_PRODUCTION_CUTOVER_CHECKLIST.md
```

本阶段新增 `build_production_cutover_checklist` 与 `GET /api/v40/project/production-cutover-checklist`，把 V30 replacement candidate readiness、active weight、rollback、LLM 配置和 repository 配置合成 production beta cutover checklist。自动项全部 ready 时仍返回 `cutover_status=blocked_by_human_signoff`，明确系统不能自行切生产流量。

2026-06-30 Phase 42 已启动：

```text
docs/V40_PHASE42_RELEASE_CANDIDATE_AUDIT.md
```

本阶段新增 `build_release_candidate_audit` 与 `GET /api/v40/project/release-candidate-audit`，聚合 project status、surface beta readiness、V30 replacement readiness 和 production cutover checklist。自动审计全通过时返回 `automatic_audit_passed_human_signoff_required`，仍不切流量、不激活权重。

2026-06-30 Phase 43 已启动：

```text
docs/V40_PHASE43_PRODUCTION_SMOKE_HANDOFF.md
```

本阶段新增 `build_production_smoke` 与 `GET /api/v40/project/production-smoke`，聚合 project status、surface beta readiness、V30 replacement readiness、production cutover checklist 和 release candidate audit。通过时返回 `passed_handoff_ready`，含义是可以进入人工验收和交接，不表示已上线。

2026-06-30 Phase 44 已启动：

```text
docs/V40_PHASE44_FINAL_OPERATING_GUIDE.md
```

本阶段补齐最终操作手册，整理 Runtime/Admin/User UI 地址、实时完成度接口、自动验收接口、关键边界、人工验收项、回滚要求和建议验收顺序。V40 自动交付完成度提升到约 98%，剩余部分必须由真实命例验收和线上切换窗口完成。

2026-07-01 Phase 45 已启动：

```text
docs/V40_UI_PRODUCT_FLOW_SPEC.md
```

本阶段把 V40 用户侧 UI 和交互流程正式定稿为 `report-first + conversation-after + probe-when-needed + practitioner-as-lens`。普通用户主线是输入、核心报告、推荐追问、智能对话和反馈；深度校准以 Probe 卡片承载；命理师以 Practitioner Lens 抽屉进行分支、证据、反证和专业校准；未来人工复核必须经过 ConsentGrant 和匿名 case。该规格明确普通用户不暴露 provider/model/prompt/acceptance/policy/debug 语言，Admin 继续独立，所有有价值交互都进入结构化训练材料。`V40_UI_PRODUCT_FLOW_SPEC.md` 是后续用户侧 UI、Surface Projection、API Projection、移动端、Probe、Practitioner Lens 和反馈训练的产品运行合同。

2026-07-01 Phase 46 已启动：

```text
docs/V40_PHASE46_USER_PRODUCT_SHELL_RUNTIME.md
v40/api/user_ui.html
GET /v40/ui
```

本阶段把 Phase 45 合同落到真实用户页：`/v40/ui` 改为独立 `user_ui.html` 模板，输入区使用四柱天干地支选择器和折叠大运流年，不再暴露执行模式、角色下拉、provider/model、acceptance、policy、debug、telemetry 或 Admin 链接。Reading Surface 优先消费 `product_projection.verdict_cards/advice_cards`、`verdicts[].forbidden_assertions` 和 `probes`，渲染 VerdictHero、TopicCard、AdviceCard、RiskBoundary 与折叠推演摘要；Follow-up Hub 只在报告 accepted 后出现；Conversation 调用 `POST /api/v40/conversation/turn` 且不刷新报告；Probe 是独立校准卡，当前先把回答记录成本地训练标签；Practitioner Lens 作为右侧抽屉出现。Phase 46 曾用 `?role=practitioner` 临时开启命理师视角，Phase 49 已替换为 auth-derived session context。

2026-07-01 Phase 47 已启动：

```text
docs/V40_PHASE47_PROBE_ANSWER_RUNTIME.md
v40/contracts/probe.py
v40/probes/answer.py
POST /api/v40/probes/answer
```

本阶段把 Probe 回答从 UI 临时训练标签升级为正式运行时产物：`ProbeAnswerRequest` 消费当前 `RuntimeResult`、`probe_id`、用户选项或短答案，返回 `AnswerSignal`、`HiddenAttributeUpdate`、`TrainingLabelEvent`、`LocalOverlay`、`refined_advice_points` 和用户可读确认。`/v40/ui` 的 Probe 卡现在调用 `/api/v40/probes/answer`，不再直接把 Probe 答案简化成一条裸训练标签；`不太像` 反馈也可以在没有现成 ProbeCandidate 时形成 recovery hidden attribute，例如 `wealth.money_mode`。该链路不重跑报告、不改 verdict、不改 chart facts、不写生产权重、不写 V30。

2026-07-01 Phase 48 已启动：

```text
docs/V40_PHASE48_PROBE_AWARE_CONVERSATION_PLAN.md
ConversationTurnRequest.probe_answer_results
ConversationTurn.source_answer_signal_ids
ConversationTurn.source_hidden_attribute_update_ids
ConversationTurn.calibration_context
```

本阶段把 Phase 47 的 `ProbeAnswerResult` 接入后续智能对话上下文。`POST /api/v40/conversation/turn` 现在可以接收 `probe_answer_results`，conversation runtime 会把 `AnswerSignal.interpreted_claim`、`HiddenAttributeUpdate.value` 和 `ProbeAnswerResult.refined_advice_points` 放入 LLM prompt、local answer 和 `ConversationTurn` 源追踪字段。`/v40/ui` 在 Probe 回答后本地保存 result，后续追问会随请求带上这些校准结果。用户侧只看到“结合你刚才补充的线索……”这类自然语言，不暴露 AnswerSignal、HiddenAttributeUpdate、ProbeAnswerResult、TrainingLabelEvent 或 LocalOverlay。

2026-07-01 Phase 49 已启动：

```text
docs/V40_PHASE49_AUTH_DERIVED_ROLE_CONTEXT.md
UserAppSessionContext
GET /api/v40/session/context
```

本阶段把用户侧身份从临时 URL hook 收束到服务端会话上下文。`/v40/ui` 不再读取 `window.location.search`，也不再支持 `?role=practitioner`；页面启动时调用 `/api/v40/session/context`，再用返回的 `UserAppSessionContext` 决定普通用户、游客或命理师视角。主系统只保留 guest/user/practitioner 三种产品角色；admin 如果进入主系统，会被映射为特殊 practitioner，Admin Control Plane 继续独立，不进入用户侧流程。报告、Probe、智能对话和 Practitioner Lens 都使用 session role context 投影权限。

2026-07-01 Phase 50 已启动：

```text
docs/V40_PHASE50_USER_UI_VISUAL_QA.md
scripts/run_user_ui_visual_qa.py
```

本阶段把用户侧产品壳进入可重复视觉验收：脚本使用 Playwright 访问运行中的 `/v40/ui`，覆盖 desktop_user、desktop_practitioner、mobile_user 三种场景，生成 full-page PNG 和 `visual_qa_report.json`。验收重点是报告优先页面能打开、session role context 能切换命理师视角、Practitioner Lens 只在命理师身份出现、普通用户页面不泄漏 provider/model/prompt/acceptance/policy/debug/telemetry/admin 等工程词，并检查手机端明显横向溢出和控件文本溢出。该 QA 只观察用户表面，不改 runtime、训练权重或 V30 状态。

2026-07-01 Phase 51 已启动：

```text
docs/V40_PHASE51_CONSENT_REVIEW_QUEUE.md
ConsentGrant
AnonymizedCaseView
PractitionerReviewRequest
PractitionerReviewQueueItem
PractitionerReviewResult
POST /api/v40/consent/grants
POST /api/v40/practitioner/review-requests
GET  /api/v40/practitioner/review-queue
POST /api/v40/practitioner/review-results
```

本阶段建立用户授权与命理师审阅的最小合同层。`ConsentGrant` 明确用户是否允许 practitioner review、training feedback 和 anonymized case share；`AnonymizedCaseView` 只包含 verdict/advice/probe/evidence/signal 摘要，不返回 raw runtime、chart facts、出生时间、账号或联系方式；`PractitionerReviewResult` 只生成 `TrainingLabelEvent(local_only=true)`，不能直接改 verdict、chart facts、global weight 或 V30 状态。Phase 51 API 先返回合同产物，不做持久化和真实派单；Phase 52 已接入 review queue persistence 与 assignment。

2026-07-01 Phase 52 已启动：

```text
docs/V40_PHASE52_REVIEW_QUEUE_PERSISTENCE.md
v40_consent_grants
v40_practitioner_review_requests
v40_practitioner_review_queue
v40_practitioner_review_results
POST /api/v40/practitioner/review-queue/assign
```

本阶段把 Phase 51 的授权与命理师审阅合同接入 V40 独立 Postgres 仓储。`persist=true` 时，consent grants、review requests、queue items 和 review results 都会写入 `v40_` 表；`GET /api/v40/practitioner/review-queue` 读取持久化队列；assignment 只更新 queue item 与 request 的 `status/assigned_to_practitioner_ref` 元数据，不改 verdict、chart facts 或权重；review result persist 会同步保存内部 `TrainingLabelEvent(local_only=true)`，让命理师复核进入训练素材，但仍然 `writes_v40_production=false`、`writes_v30_state=false`。

2026-07-02 Phase 53 已启动：

```text
docs/V40_PHASE53_USER_CONSENT_REVIEW_UI.md
/v40/ui 命理师复核
POST /api/v40/consent/grants
POST /api/v40/practitioner/review-requests
```

本阶段把 Phase 52 的持久化审阅队列接入用户侧产品流。报告生成前不显示审阅入口；报告生成后，用户可以点击“授权复核”，前台先创建授权，再把当前 `RuntimeResult` 交给审阅请求构建器生成脱敏 case view 并写入 V40 队列。用户页面只显示授权和提交状态，不展示内部合同类型、Admin 控制面、provider/model/prompt/debug/telemetry 等工程信息；如果 V40 仓储不可用，页面必须提示稍后重试，不能假装已提交成功。此阶段不改 verdict、chart facts、signal registry、训练权重、V30 状态或生产权重。

2026-07-02 Phase 54 已启动：

```text
docs/V40_PHASE54_USER_ACCOUNT_PROFILE_FLOW.md
POST /api/v40/auth/register
POST /api/v40/auth/login
POST /api/v40/auth/logout
GET  /api/v40/auth/me
GET  /api/v40/profiles
POST /api/v40/profiles
PUT  /api/v40/profiles/{profile_id}
DELETE /api/v40/profiles/{profile_id}
```

本阶段把 `/v40/ui` 固化为用户产品流：注册/登录、多用户八字档案、选择档案测算、双引擎报告、Probe 校准和简洁一问一答。V30 多分步测算页面不作为 V40 普通用户主流程保留；V40 仍保留分阶段素材、证据、双引擎信号和命理师 Lens，但普通用户只看到“档案 -> 报告 -> 必要校准 -> 对话”。注册只允许 `user/practitioner`，admin 不能从主系统注册；用户、会话和档案全部写入 V40 独立表，不读写 V30。

2026-07-02 Phase 55 已启动：

```text
docs/V40_PHASE55_COMPACT_PROCESS_TICKER.md
/v40/ui processTicker
renderProcessLoading
renderProcessTicker
```

本阶段保留“不让普通用户参与 V30 多步页面”的产品判断，但在报告页增加三行可见推演流。用户点击开始测算后，会看到 `定盘 / 取象 / 合参` 三行打字机提示；报告返回后，这三行会根据真实 runtime 改写，展示日主、月令、大运流年、信号数量、紫微旁路与隐藏线索校准状态。该组件只做用户可读过程投影，不显示 provider/model/prompt/debug/Admin 信息，不提供可点击步骤，也不改变 verdict、chart facts、runtime 权重、V30 状态或生产权重。

2026-07-02 Phase 56 已启动：

```text
docs/V40_PHASE56_ADMIN_PROFILE_SYNC.md
qiazhi/v40/scripts/sync_v30_admin_profiles.py
admin / abcd1235
jerrydidi@gmail.com
```

本阶段把 V30 的固定 admin 习惯迁入 V40：用户侧登录名为 `admin`，邮箱为 `jerrydidi@gmail.com`，密码为 `abcd1235`，主系统角色投影为 `practitioner`。`/api/v40/auth/register` 仍不能注册 admin，也不能抢占内置 admin 邮箱。V30 中归属 `v20-admin/admin` 的 18 个八字档案通过 migration-only CLI 转为 V40 `BaziProfileRecord`，写入独立 `v40_user_accounts` 和 `v40_bazi_profiles`；迁移时允许调用 V30 确定性排盘函数生成四柱、大运、流年，但 V40 runtime 不直接读取或修改 V30 状态。

2026-07-02 Phase 57 已完成：

```text
docs/V40_PHASE57_PROCESS_FEEDBACK_AND_UI_REVIEW_BRIEF.md
/v40/ui processLoadingFrames
execution_mode=ollama
```

本阶段把报告等待态从“一次性三行提示”升级为持续轮转的三行打字机推演流。用户点击测算后，在 LLM 返回前页面会持续显示 `定盘 / 取象 / 合参` 三行过程，轮转覆盖四柱校验、十神用神、规则画像路径、八字主引擎、紫微旁路、智能表达层等阶段；报告返回后停止轮转，并用真实 runtime 结果改写三行摘要。用户侧报告和对话仍必须调用 LLM 表达路径：前台通过非可见字段发送 `execution_mode=ollama`，不暴露 provider/model/prompt/debug/Admin 信息；如果模型不可用，显示明确失败，不使用本地模板静默替代。

2026-07-02 Phase 58 已启动：

```text
docs/V40_PHASE58_HARD_LLM_AND_DIRECT_TRAINING_PRINCIPLES.md
NativeReadingReportRequest.execution_mode=ollama
ConversationTurnRequest.execution_mode=ollama
BatchTrainerV1 direct active policy
```

本阶段把两条主系统原则固化为硬合约：第一，没有 LLM 时产品运行时直接失败，API 返回明确错误，页面展示 LLM 故障，不允许本地模板静默 fallback；第二，训练和验证通过后直接生成并持久化 active policy registry，下一次测算立即读取新策略，不设置人工审核门。旧的 activation review/execution 链路仅保留为历史审计或 Lab 资料，不再代表 V40 主训练路径。保留 rollback pointer、TrainingImpactDiff、风险摘要和回放证据作为事后补救，不作为事前审批。

2026-07-02 Phase 59 UI 收敛 runtime 已启动：

```text
docs/V40_PHASE59_UI_PRODUCT_CONVERGENCE_PLAN.md
```

外部 UI review 已确认 V40 方向正确，但用户侧页面需要从“工程工作台”进一步收敛为“命理测试产品”。Phase 59 的主线是四层渐进披露：测算入口、测算报告、继续追问、校准/命理师 Lens。本阶段已把用户页首屏收敛为主题、当前命盘和开始测算；账号/档案进入顶部“我的命盘”抽屉；四柱、大运和流年进入折叠编辑区；报告优先展示核心判断、建议、风险和追问；Probe 收敛为“校准一问”的轻卡片；命理师 Lens 改为“专业视角”，仅命理师/admin 可见。

Phase 59 第二轮把命理师体验正式收敛为 `same Reading + RoleProjection + Contextual Practitioner Lens`：命理师不是另一个测算页面，而是同一份 Reading、Report、Conversation 和 Probe 上的专业增强层。专业视角默认收起，点击报告卡片或顶部“专业视角”后按当前主题聚焦，展示当前判断、分支、旁路证据、建议追问、人话校准动作和备注入口；普通用户永远不看到命理师动作，Admin debug 继续留在独立控制台。未来复核队列可以作为任务列表存在，但 case 详情仍打开同一个 V40 Reading UI。

Phase 59 第三轮把页面从“报告与对话同时铺满”收敛为 `report mode -> conversation mode`：报告刚生成时完整展示判断、建议、风险、校准一问和追问入口；用户点击追问或输入问题后，完整报告自动收起为核心判断摘要，并提供“查看完整报告”恢复动作，主区进入一问一答咨询流。Follow-up 从堆叠卡片改为轻量 chips，Probe 回答后折叠成“已校准”提示，顶部角色文案改为“命理师模式”，主页面不再强调 admin/email。

2026-07-02 Phase 62 历史报告与问答层级已启动：

```text
docs/V40_PHASE62_HISTORY_AND_CONVERSATION_LAYERING.md
```

本阶段把左侧栏从单纯输入区升级为用户侧测算记忆区：测算入口、当前命盘和历史报告同处左栏；生成报告后会写入当前账号/当前浏览器历史，点击历史项可以恢复报告和追问种子，不重新调用 LLM，不改命盘事实。进入智能对话后，主区只保留智能对话链、pending 等待项、推荐问题 chips 和输入框；报告、Probe、复核和报告态追问入口退出主区，由左侧历史报告承接查阅。问答以倒序 item 链显示，最新问题在最上方并展开，旧问题自动折叠；等待 Gemma 时显示 pending item，不生成本地替代回答。由于 `v40_runtime_records` 尚未携带用户 ownership contract，本阶段不开放全局后端历史报告列表，跨设备持久历史进入 Reading Revision / ownership contract 阶段。

2026-07-01 V40-RC2 已启动：

```text
docs/V40_RC2_MINGLI_DEPTH_MIGRATION_PLAN.md
docs/V40_RC2_ASSET_MIGRATION_GATE.md
docs/V40_RC2_MODULE_STATUS_AND_MIGRATION_MAP.md
docs/V40_RC2_TRAINABLE_RUNTIME_SPINE.md
docs/V40_RC2_HORIZONTAL_RUNTIME_CONTEXT.md
docs/V40_RC2_BATCH_TRAINER_V1.md
GET /api/v40/project/mingli-depth-index
GET /api/v40/project/module-migration-status
GET /api/v40/project/trainable-runtime-spine
GET /api/v40/project/horizontal-runtime-context
POST /api/v40/training/batch-trainer-v1
```

V40-RC2 不再以架构完成度作为唯一主指标，而是新增 `Mingli Depth Index`，拆分 Fact / Signal / Domain / Probe / Training / Evaluation 六个维度。下一阶段目标是把 V30 命理资产通过 plain JSON DTO 和 Asset Migration Gate 萃取进 V40 原生 Engine / RuntimeSignal / Decision / Advice / Probe / Training / Evaluation 链路。所有迁移资产先 sidecar，再 evaluating，最后 enabled；每批迁移必须跑 before/after diff，且不允许 overclaim rate 上升。

同时新增模块迁移状态 read model，明确 V40 原生模块、V30 可萃取资产、V40-RC2 必须新建模块和不迁移的旧模块。V30 runtime 直接复用数量固定为 0；可复用的是 V30 命理资产、算法口径和测试样本，必须通过 DTO / adapter / gate 进入 V40。

训练边界同步收敛为 `Trainable Runtime Spine`：事实型基础模块只验证不训练；判断型基础模块只能训练 `source_weight / rule_weight / path_weight / claim_score / conflict_policy / assertion_threshold / advice_priority / probe_voi / llm_acceptance` 等有限 policy unit。新增 `TrainableUnit / TrainablePolicyRegistry / TrainingAttribution`，并让 `RuntimeSignal.trainable_refs` 成为反馈归因入口。V40 是命理高迭代系统，训练后的 policy 默认直接成为 active policy；replay、golden/regression、overclaim、advice grounding、probe yield、leakage 和 LLM boundary gate 作为持续评估和补救依据，不作为每次试错前的重审批。

横向能力同步升格为 `Horizontal Runtime Context`：V40 是多语言、多角色、多终端、多引擎的可训练命理运行时。新增 `LocaleContext / RoleContext / ClientContext / EngineContext / EngineCapability / RuntimeContext / MingliTermDictionary / SurfaceSection`。多语言不靠前端翻译，角色不靠 UI 隐藏，手机端不只是压缩桌面端，多引擎不直接下 verdict。训练和评测必须能按 locale / role / client / engine_source 拆分。Admin 继续保持独立控制台和端口，只作为控制面、审计面、训练发布面存在。

BatchTrainerV1 已进入 RC2 主线：`TrainingLabelEvent + TrainingAttribution` 可以聚合成 active `TrainablePolicyRegistry` 和 `TrainingImpactDiff`。该 trainer 只调整有限 policy unit，跳过 fact refs，将 local-only feedback 降权，训练后直接生效，并通过 previous registry、previous policy 与 impact diff 支持回滚和补救；它不改变命盘事实，也不让 LLM 成为命理裁决者。

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
