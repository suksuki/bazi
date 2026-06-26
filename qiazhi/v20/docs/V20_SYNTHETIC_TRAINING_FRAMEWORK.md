# V20 合成数据训练框架

更新时间：2026-05-12

## 目标

V20 不训练 LLM 本体，而是训练自己的八字系统：

```text
规则是否成立
-> 特征是否识别
-> 画像是否贴合当前盘
-> 推荐问题是否聚焦
-> 问题链是否有前后逻辑
-> 不同角色是否进入不同互动流程
-> LLM 是否只解释已验证上下文
```

合成训练的核心价值是把“感觉准不准”变成可回放、可比较、可失败的工程评估。

## 借鉴框架

V20 采用组合式训练框架，不把核心交给自由 Agent。

| 借鉴方向 | V20 用法 | 边界 |
| --- | --- | --- |
| Property-Based Testing | 用结构约束自动生成大量合成盘，验证规则性质。 | 只验证命理系统输出，不生成规则真值。 |
| Metamorphic Testing | 改变一个结构条件，要求输出发生可解释变化。 | 用于边界和反例，不替代命理规则审查。 |
| Evals Framework | 把规则、画像、问题、DAG、角色视图做成可重复 eval。 | 不只评 LLM，也评完整 runtime。 |
| Contextual Bandit | 学习在某个上下文下推荐哪个问题或下一步按钮。 | 只调问题/互动/表达，不调核心规则。 |
| Great Expectations | 把训练数据和 runtime 输出做成 expectation suite 和验证报告。 | 只做质量门槛，不直接激活候选。 |

## 总架构

```text
SyntheticBaziCase DSL
-> Case Generator
-> Deterministic Runtime Replay
-> Evaluator Suite
   -> RuleEvaluator
   -> FeatureEvaluator
   -> PortraitEvaluator
   -> QuestionEvaluator
   -> QuestionDAGEvaluator
   -> RoleViewEvaluator
   -> LLMAnswerEvaluator
-> Candidate Policy Generator
-> Synthetic Validation
-> Historical Replay
-> Policy Version Registry
-> Runtime Pointer
```

## SyntheticBaziCase DSL

合成案例不应该只保存四柱，还要保存结构目标、期望输出和禁止输出。

```yaml
case_id: wealth_visible_weak_dm_001
case_type: portrait_question_case
target_pattern: 财星可见但日主承接不足

constraints:
  day_master_strength: weak
  wealth_visible: true
  resource_support: low
  peer_support: low
  time_layer_trigger: optional

expect:
  rules_include:
    - 财星可见但承接需扶助
  portraits_include:
    - 资源承接
    - 财星压力
  questions_include:
    - 先看能不能承接
    - 财运节奏是否需要资源支持
  role_views:
    guest:
      forbid_stage:
        - review
    analyst:
      require_stage:
        - review

forbid:
  portraits:
    - 财旺发财
  answers:
    - 断定发财
```

稳定字段：

```text
case_id
case_type
target_pattern
chart_constraints
chart_input
time_context
expected_facts
expected_features
expected_rules
expected_portraits
expected_questions
expected_dag_path
expected_role_views
negative_expectations
quality_gates
```

## Metamorphic Case Pair

八字系统特别适合成对验证：

```text
base_case:
  target_pattern: 伤官见官无印
  expect:
    portraits_include: [冲突, 压力]

mutated_case:
  mutation: 加入印星缓冲
  expect:
    portraits_include: [印星缓冲, 转化]
  forbid:
    portraits: [单纯冲突]
```

这种方式验证系统是否理解条件变化，而不是只背一个标签。

## Evaluator Suite

| Evaluator | 评估对象 | 失败类型 |
| --- | --- | --- |
| `RuleEvaluator` | 规则命中、反例、子条件。 | 漏触发、误触发、过宽。 |
| `FeatureEvaluator` | 强弱、五行、十神、地支、时间层。 | 结构漏识别、边界错配。 |
| `PortraitEvaluator` | 画像轴、主题、置信度、边界。 | 套标签、过度断语、主题偏移。 |
| `QuestionEvaluator` | 推荐问题标题、领域、角色适配。 | 不像用户问题、术语堆叠、脱离主线。 |
| `QuestionDAGEvaluator` | entry/focus/structure/timing/review/observe/advice/closure。 | 下一步发散、重复、跳阶段。 |
| `RoleViewEvaluator` | guest/user/analyst/admin 投影。 | 角色泄露、深度错配、权限错配。 |
| `LLMAnswerEvaluator` | LLM practitioner answer。 | 创造事实、越过边界、忽略当前盘证据。 |

## Contextual Bandit 用法

Contextual Bandit 只用于交互策略，不用于命理真值。

```text
context:
  role_key
  question_stage
  primary_mainline_key
  portrait_axes
  user_preference_summary
  answered_question_ids

action:
  next_question_id
  next_choice_group
  portrait_axis_to_show

reward:
  click
  followup
  session_completion
  practitioner_accept
  low_fallback
```

允许影响：

- 推荐问题排序。
- 问题链下一步。
- 画像展示顺序。
- 回答表达长度和术语密度。

禁止影响：

- 四柱事实。
- 强弱事实。
- 十神关系。
- 用神真值。
- 核心规则成立条件。

## 训练产物

每次训练必须输出三类报告：

```text
coverage_report
failure_report
candidate_report
```

候选产物必须版本化：

```text
training_artifact
candidate_policy
synthetic_validation_result
replay_comparison
policy_version
runtime_pointer
```

runtime 只读取 `runtime_pointer`，不直接读取原始训练报告。

## 当前系统落点

| 当前模块 | 下一步接入 |
| --- | --- |
| `interaction/question_seed_registry.py` | 作为 `QuestionEvaluator` 和 DAG 冷启动问题源。 |
| `interaction/role_question_click.py` | 作为 contextual bandit 的 interaction signal。 |
| `learning/role_question_click_training.py` | 已扩展为角色问题链 reward 训练输入，只生成候选建议。 |
| `learning/role_view_policy_candidates.py` | 接收 role/dag evaluator 的候选策略。 |
| `learning/role_view_policy_replay.py` | 增加 DAG path replay。 |
| `role_view/runtime_pointer.py` | 继续作为 runtime 策略指针，不直接消费原始点击。 |
| `scripts/run_synthetic_case_suite.py` | 跑 synthetic replay/evaluator，默认 summary + 限量用于快速暴露差距。 |
| `scripts/run_question_dag_training.py` | 生成问题链 DAG 候选策略，可写本地训练 artifact。 |
| `scripts/run_role_interaction_training.py` | 生成角色互动候选策略，可写本地训练 artifact。 |
| `scripts/run_training_iteration.py` | 已串起 synthetic coverage、synthetic replay、DAG training、role interaction training。 |

## 新主线任务计划

### T1：SyntheticBaziCase Schema

- 定义 `SyntheticBaziCase`、`ExpectedRuntimeOutput`、`NegativeExpectation`。
- 支持 JSON/YAML fixture。
- 覆盖规则、画像、问题、DAG、角色视图。

验收：

- 10 个最小合成案例可被 loader 读取。
- schema 不包含用户隐私和自由文本训练字段。

### T2：Runtime Replay Harness

- 输入 `SyntheticBaziCase`。
- 跑现有 runtime。
- 保存 actual result 的规则、画像、问题、角色视图和 answer context。

验收：

- dry-run 不写 runtime。
- 输出可被 evaluator 消费。

### T3：Evaluator Suite 第一版

- 实现 rule、portrait、question、role view 四个 evaluator。
- 后续再加 DAG 和 LLM answer evaluator。

验收：

- 能输出 pass/fail、failure reason、case id、expected/actual 摘要。

### T4：Question DAG Model

- 定义 `QuestionNode`、`ChoiceOption`、`NextQuestionRule`。
- 将现有推荐问题映射到 stage。
- guest/user/analyst/admin 拥有不同默认路径。

验收：

- 普通用户不进入 review。
- 命理师能进入 review。
- admin 能进入 observe。

### T4.5：Question Feedback Interaction

- 定义 `QuestionReviewAction`、`QuestionReviewReason`、`QuestionReviewSignal`。
- 命理师/admin 对问题质量做结构化审核。
- 反馈信号用于问题模板、角色适配、DAG 路径和排序候选。

验收：

- 可标记通过、改写、降权、合并、删除。
- 可标记角色不匹配、主线不匹配、术语过重、重复、发散。
- 反馈信号不直接改 runtime，只进入 candidate policy。

### T5：DAG Training

- 用用户点击、选择、追问和 synthetic interaction case 训练下一步策略候选。
- 候选只生成 artifact，不直接改 runtime。

验收：

- 生成 `next_question_policy` 候选。
- replay 能比较 baseline 与 candidate 的 DAG path。

### T6：Role Interaction Training

- 聚合 guest/user/analyst/admin 的问题点击、跳过、追问、校准。
- 生成 role view 候选策略。

验收：

- guest 入口更短。
- user 问题更聚焦。
- analyst 复核更结构化。
- admin 观测项可追溯来源。

### T7：Training Iteration Integration

- `run_training_iteration.py` 汇总 synthetic suite、DAG training、role interaction training。
- `run_training_iteration.py --synthetic-replay-limit 0` 可跑全量 synthetic replay；默认只跑轻量 replay，避免日常迭代拖慢。
- 输出统一训练报告。

验收：

- 最小 synthetic suite 默认 smoke 和全量 14 case 均可 `pass`。
- 当前覆盖：极端同气、全冲边界、多时间层、角色泄露防护。
- `synthetic_bazi_coverage_report()` 可机器读取 case type、domain、question、DAG stage、role 和 boundary capability 覆盖状态。
- `question_dag_coherence_report()` 可机器读取 DAG 合法转移、角色默认路径和禁止串线边界。
- `answer_safety_evaluator` 校验确定性/LLM 回答不出现断言词、内部标记泄露，并保留边界提示。
- `question_review_training` 已聚合命理师/admin 的结构化问题反馈信号，输出候选建议，不直接修改 runtime。
- `question_dag_training` 已消费 `question_review_training`，把反馈建议纳入 next-question candidate policy。
- `question_dag_policy_replay` 已离线比较 baseline/candidate，输出 coherence、coverage、transition support 和 review recommendation 风险，不直接修改 runtime。
- `question_dag_policy_promotion_gate` 已阻断默认自动上线；显式上线前必须通过 replay ready、score、risk 和 rollout switch。
- `role_question_click_training` 聚合 select/followup/skip/helpful/unhelpful/downrank 的 reward，不直接改 runtime pointer。
- `role_view_policy_replay` 已把 reward candidate 纳入离线 replay scoring，输出 offline score、版本比较和 A/B replay summary。
- `role_view_policy_calibration` 已输出 reward/A-B 观察和建议阈值，不直接修改 runtime。
- `role_view_policy_promotion_gate` 已阻断默认自动上线；显式激活时必须通过 replay、样本数、reward margin、offline score、A/B net lift、risk count、calibration thresholds 和 rollout switch。
- `role_view_runtime_pointer` 已支持 active pointer 激活/回滚，runtime 只读取指针，不直接消费原始训练报告。
- release smoke 可检查训练报告存在、候选来源可追溯、runtime pointer 未直接消费原始训练数据。

### T8：Learning Orchestrator V1

- `learning_orchestrator/job_schema.py` 定义 `fast`、`nightly`、`weekly`、`full` 四类学习任务。
- `nightly` 固定为 518,400 全量确定性 replay，不做全量 LLM。
- `weekly` 和 `full` 只允许 bounded LLM sample eval，用于回答边界抽检。
- `learning_orchestrator/dataset_plan.py` 统一声明 full corpus、synthetic suite 和 interaction ledger 来源。
- `learning_orchestrator/sharding.py` 统一声明分片、batch、checkpoint 和 resume 策略。
- `learning_orchestrator/run_plan.py` 输出 dataset -> shard replay -> evaluator -> candidate search -> replay compare -> promotion preflight 的统一计划。

验收：

- `/api/v20/learning/orchestrator/run-plan?job=nightly` 可读取夜间全量学习计划。
- `/api/v20/learning/run-plan` 已嵌入默认 nightly orchestrator 摘要。
- runtime pointer 不由 run plan 写入，只能由 replay/promotion 后的显式激活流程写入。
- 518K 只作为离线全量回放宇宙，不直接成为单盘画像真值。
- LLM 不训练本体，也不参与 518K 全量调用。

## 不做什么

- 不训练 LLM 本体。
- 不让用户点击直接改规则。
- 不让自由文本成为核心训练信号。
- 不让 518K 统计先验直接变成单盘画像真值。
- 不让 Agent 自由改 runtime 规则。
