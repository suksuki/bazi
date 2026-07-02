# V40 Phase 60 Lens Discussion Notes

Date: 2026-07-02

This file temporarily records ongoing design discussion before it is merged into the formal Phase 60 / Phase 61 mainline plan.

## Discussion 1: Practitioner Lens Must Stay A Calibrator

Source: user discussion attachment on 2026-07-02.

### Core Judgment

Practitioner Lens must not become:

```text
free editor
full signal table
admin tuning console
another mingli runtime
```

It should be:

```text
断项选择器
+ 影响预览
+ 本轮校准
+ 训练标签
```

The product boundary is:

```text
系统负责生成候选断项
命理师负责选择主次和确认分支
用户负责通过 Probe 确认现实事件
DecisionEngine 负责重算本轮报告
Training 系统负责沉淀选择
```

### Seven Lens Principles

1. Practitioner can calibrate interpretation, not chart facts.
2. Practitioner selects human-readable assertion candidates, not raw runtime signals.
3. Only critical divergence points should ask for practitioner attention.
4. Selection first creates current-reading `LocalOverlayPatch`, not global rule mutation.
5. Every selectable candidate must show an impact preview.
6. Every selection must be undoable and comparable against the system's original judgment.
7. Practitioner Lens stays on the same Reading page; it is not a separate reading page.

### Candidate Board Scope

The candidate board should focus on key assertion pools:

```text
命局骨架:
  身强 / 身弱候选
  格局候选
  用神候选
  忌神候选
  主做功路径
  结构风险

领域断项:
  财富
  事业
  感情
  健康压力

大运流年断项:
  年份变化候选
  可能领域
  触发依据
  建议追问
```

### Product Actions

User-facing practitioner actions should remain product-language:

```text
采为主断
作为辅助
暂不采用
需要追问确认
用户反馈不符
添加备注
```

Internal mapping can remain:

```text
adopt / support / downweight / ask_more / mismatch / note
```

### Required Guardrails

The Lens should avoid turning into a button wall:

```text
每个领域只能有一个主断
副断最多 1-2 个
全局锚点最多 2 个
年份候选最多确认 3 个
互斥断项必须提示冲突并要求取舍
```

### Needs Practitioner Attention

Practitioner attention should be generated only when useful:

```text
DecisionVerdict = mixed
主分支和备选分支分数接近
用神/忌神候选影响多个领域
大运流年出现多个应期候选
用户反馈“不像”
Probe 回答和系统原判冲突
八字和紫微信号冲突
Advice 方向依赖某个未确认断项
```

It should not trigger for:

```text
confirmed / supported with little counter-evidence
low-impact details
pure expression issues
items with no actionable choice
evidence too weak to become a candidate
```

### Probe And Lens Loop

When the practitioner chooses `需要追问确认`, the system should create a real Probe card. After user answer:

```text
Probe answer
  -> TimelineEventSignal / AnswerSignal / HiddenAttributeUpdate
  -> Lens update
  -> LocalOverlayPatch
  -> RevisedReadingDiff
  -> TrainingLabelEvent
```

For timing questions, use a two-step probe:

```text
1. 年份定位: 哪一年最明显？
2. 事件类型: 那一年主要是哪类变化？
```

### Implementation Notes To Reconcile With Current Phase 60

Already present in current V40:

- `SystemAssertionCandidate`
- `MingliCandidateBoard`
- Probe V2 fields
- `ask_to_confirm` opens a visible Probe card
- current-reading training label and local overlay path

Still to design before implementation:

- `NeedsPractitionerAttention` scoring and filtering.
- One-primary-per-domain guardrail.
- Global-anchor limit.
- Conflict prompt for mutually exclusive candidates.
- `PractitionerSelection` / `LocalOverlayPatch` / `RevisedReadingDiff` explicit contracts.
- Undo and compare with system initial judgment.
- Two-step timeline probe flow.

## Pending

Second discussion received and recorded below. Next step is to decide whether to promote this into a Phase 61 implementation plan.

## Discussion 2: Reading Revision Layer

Source: user discussion attachment on 2026-07-02.

### Core Judgment

Practitioner Lens needs a formal `Reading Revision / 判定版本管理系统`.

It is not a simple operation log. It version-controls:

```text
系统初判
Probe 回答
命理师选择
Local Overlay
重算结果
报告变化
训练标签
```

Without this layer:

```text
不知道当前报告为什么变成这样
命理师无法撤销或重选
每次都全量重跑，浪费资源，也难以训练归因
```

The rule is:

```text
不要让命理师直接改报告；
让命理师产生可追溯选择事件；
再由系统生成新的 ReadingRevision。
```

### Histories To Manage

V40 should manage at least three histories:

```text
1. 系统判定历史
   R0 系统初判
   R1 用户回答 Probe 后
   R2 命理师选择后
   R3 用户反馈“不太像”后

2. 命理师选择历史
   candidate_group
   action
   status: active / superseded / reverted
   note

3. 训练标签历史
   PractitionerSelection -> TrainingLabelEvent
   ProbeAnswer -> TrainingLabelEvent
   UserMismatch -> TrainingLabelEvent
```

普通用户只看简化提示；命理师看校准历史和差异；Admin 才看完整 event log、cache key、policy version 和 raw snapshot。

### Correct Runtime Flow

Practitioner actions must not directly rewrite report text.

```text
命理师选择断项
  -> PractitionerSelectionEvent
  -> LocalOverlayPatch
  -> DecisionEngine 局部重算
  -> ReadingRevision
  -> RevisedReadingDiff
  -> ProductProjection / LLMExpression
  -> 当前页面更新
```

This matches the V40 authority boundary:

```text
DecisionEngine owns verdict
LLM owns expression
Practitioner owns selection/calibration signal
Training owns later attribution
```

### Reselect And Restore

Reselect must not delete history.

```text
old selection -> superseded
new selection -> active
new ReadingRevision generated
```

Restore also creates a new revision:

```text
R4 恢复到 R1
```

No physical deletion of history.

### UI Contract

Lens should show current effective state first:

```text
当前版本：命理师校准后
[查看变化] [历史记录] [撤销]

财富分支当前生效：
主断：项目/客户型财运
辅助：合作分利风险
待确认：现实收入来源
```

History is folded:

```text
查看校准历史
  10:21 系统初判
  10:24 命理师选择
  10:26 用户回答 Probe
  10:28 系统更新
```

普通用户 should only see:

```text
报告已根据你的回答更新
命理师已复核此判断
```

### Low Impact Vs High Impact

Not every click should trigger full recomputation.

Low-impact selections can update immediately or with local domain recompute:

```text
财富分支从辅助改为主断
建议追问确认
某条建议暂不采用

impact_scope = wealth / advice_only / probe_only
```

High-impact selections should enter draft mode first:

```text
用神改了
忌神改了
主做功路径改了
身强身弱判断改了
大运主应方向改了

impact_scope = global_structure
```

High-impact flow:

```text
待应用校准
  -> show impact preview
  -> 应用本轮校准
  -> one recompute
```

### Layered Cache

Reading Revision also enables resource control. Suggested cache layers:

```text
Fact Cache:
  birth_input_hash + fact_standard_version

Signal Cache:
  chart_fact_hash + engine_policy_version + signal_rule_version

Decision Cache:
  signal_registry_hash + decision_policy_version + overlay_hash

Projection Cache:
  verdict_hash + role + locale + client_type

LLM Expression Cache:
  product_card_hash + locale + tone + model_version
```

Local recalculation should use `impact_scope`:

```text
global_structure
wealth
career
relationship
timing
advice_only
probe_only
```

### Proposed Contracts

```text
ReadingRevision
  revision_id
  reading_id
  parent_revision_id
  revision_type: initial / probe_update / practitioner_update / restore / conversation_update
  summary
  active_overlay_id
  decision_snapshot_id
  surface_snapshot_id
  created_by_role
  created_at

PractitionerSelectionEvent
  selection_id
  reading_id
  revision_id
  candidate_id
  candidate_group_id
  action
  status: active / superseded / reverted
  note

LocalOverlayPatch
  overlay_id
  reading_id
  boost_candidate_ids
  suppress_candidate_ids
  locked_profile_keys
  selected_useful_god
  selected_avoid_god
  trigger_probe_ids
  add_allowed_assertions
  add_forbidden_assertions
  impact_scope

RevisedReadingDiff
  from_revision_id
  to_revision_id
  changed_domains
  changed_verdicts
  changed_advice
  changed_probes
  changed_risk_boundaries
  human_summary

ArtifactCacheRef
  artifact_id
  reading_id
  artifact_type: facts / signals / decision / surface / llm_expression
  cache_key
  policy_version
  created_at
```

### Revision Guardrails

```text
每个 candidate_group 只能有一个 active 主断
辅助可以 1-2 个
旧主断被重选后标记 superseded
每次 revision 必须有人话 summary
撤销生成新 revision，不删除历史
chart facts 不可改
单次命理师选择不直接改变全局训练权重
```

## Merged Direction After Discussion 1 + 2

The next architecture step should not add more Lens buttons. It should add a revision layer underneath the existing Candidate Board:

```text
CandidateBoard
  -> NeedsPractitionerAttention
  -> PractitionerSelectionEvent
  -> LocalOverlayPatch
  -> ReadingRevision
  -> RevisedReadingDiff
  -> partial ProductProjection / LLMExpression update
  -> TrainingLabelEvent
```

This keeps Practitioner Lens as:

```text
有限断项校准器
```

not:

```text
报告编辑器
后台调参台
全量信号工作台
```

## Proposed Phase 61 Task Draft

1. Add revision contracts: `ReadingRevision`, `PractitionerSelectionEvent`, `LocalOverlayPatch`, `RevisedReadingDiff`, `ArtifactCacheRef`.
2. Add `NeedsPractitionerAttention` scoring and filtering.
3. Add candidate guardrails:
   - one active primary per candidate group;
   - one to two auxiliaries;
   - global anchor limit;
   - mutually exclusive candidate prompt.
4. Add selection history:
   - active / superseded / reverted;
   - no physical delete;
   - human summary required.
5. Add revision timeline projection for Practitioner Lens:
   - current effective;
   - view diff;
   - folded history;
   - restore creates new revision.
6. Add impact-scope recompute contract:
   - low-impact local update;
   - high-impact draft and apply.
7. Add cache references as contracts and runtime metadata first; implementation can start with in-memory/cache-ref projection before storage persistence.
8. Keep ordinary user surface simple:
   - “报告已根据你的回答更新”;
   - “命理师已复核此判断”.

## Discussion 3: UI Flow Clean-Up Before More Functionality

Source: user discussion attachment on 2026-07-02.

### Core Judgment

Before implementing more Practitioner Lens revision features, V40 should stop feature stacking and clean rebuild the `/v40/ui` shell.

This does not rewrite V40:

```text
保留 V40 后端、API、训练闭环、LLM、DecisionEngine；
重构 /v40/ui 的信息架构、状态机、组件层级和视觉系统。
```

### State Machine

The UI should explicitly model:

```text
setup
running
report
conversation
practitioner
```

Each state must show only necessary surfaces.

### Cleanup Priority

```text
accountPanel + profilePanel -> 我的命盘 popover/drawer
readingForm -> full before reading, chart summary after reading
processTicker -> running only, folded after report
verdictHero + reportSurface -> one report structure
probeSurface -> lightweight one-question card
reviewSurface -> hidden until user requests practitioner review
followupHub -> chip row
conversationSurface -> only after explicit user follow-up
lensDrawer -> practitioner role only
```

### Phase Ordering Decision

Phase 61 should be UI shell cleanup first. Reading Revision / Selection History stays queued after the shell is clean, because the revision layer needs a calm UI surface to land properly.
