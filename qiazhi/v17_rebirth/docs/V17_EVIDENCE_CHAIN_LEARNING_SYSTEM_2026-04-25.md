# V17 Evidence Chain Learning System

Date: 2026-04-25

## 1. Positioning

证据链不是调试面板，而是 V17 自我学习系统的原始素材层。

它负责把一次命盘判断拆成可回放、可审计、可学习的结构化记录：

1. 系统为什么生成这条 evidence / claim。
2. 命理师为什么确认、否定、观察或要求复核。
3. 哪些真实样盘可以沉淀为 benchmark candidate。
4. 这些信号更像参数门槛问题、证据质量问题、运流归因问题，还是 LLM 表达问题。

证据链只产生学习素材和学习候选，不直接修改运行时参数、插件配置、Prompt 发布状态或静态 benchmark 文件。

## 2. Product Layers

### 2.1 User Readable Layer

普通用户只看到简明断语、必要依据摘要和可展开解释。

默认不暴露插件细节、Decision Inbox、参数族、学习候选和调试信息，避免把命盘页变成工程后台。

### 2.2 Practitioner Work Layer

命理师账号进入专业证据链工作台，可以对单条证据提交：

- `confirm`：证据成立，可作为正样本。
- `reject`：证据不成立，优先作为反例或错判素材。
- `watch`：边界不稳，进入观察样本。
- `review`：需要更高阶复核，进入专家审计素材。

命理师可以补充理由，并把证据沉淀为真实案例或 `benchmark_candidate`。

### 2.3 Learning Governance Layer

系统把反馈和案例聚合为学习候选：

- 归因到 `parameter_family`。
- 汇总贡献者等级、反馈意图、学习价值、边界标签和错判类型。
- 输出 `manual_review_required` 候选。
- 由 manager/admin 审计为 `watch / approved_for_experiment / rejected`。
- 准入实验后只进入 dry-run / shadow-run 队列。
- 只有通过 synthetic + practitioner benchmark、scorecard 和 admin 发布审批后，才允许进入人工发布讨论。

当前 API 仍固定返回 `applied=false`，不自动写参数。

## 3. Material Contract

证据链反馈和案例 payload 应携带以下轻量契约：

```json
{
  "material_protocol": "v17.evidence.learning_material.v1",
  "feedback_intent": "positive_support | false_positive_or_wrong_claim | boundary_observation | needs_expert_review",
  "learning_value": "benchmark_positive | counterexample | boundary_case | review_gap | case_evidence",
  "learning_tags": ["evidence_type:pattern", "needs_counterexample"],
  "boundary_tags": ["detail:root_profile", "无羊刃支"],
  "parameter_family_hint": "classical.pattern.yangren_jiasha.v1"
}
```

字段含义：

- `feedback_intent`：命理师这次操作的审计意图。
- `learning_value`：这条素材对学习系统的价值类型。
- `learning_tags`：用于聚合、筛选和运营的结构化标签。
- `boundary_tags`：描述为什么这条证据处于边界、误判或复核状态。
- `parameter_family_hint`：插件或证据来源线索，供后端归因器辅助推断。

## 4. Current Implementation

已落地链路：

- `evidence_bundle` 生成统一证据项。
- `practitioner_feedback` 记录证据级反馈、理由、置信度、角色和 payload。
- `practitioner_cases` 记录真实样盘、边界标签、错判类型、来源反馈和 benchmark seed。
- `practitioner_learning_candidates` 聚合反馈和案例，输出学习候选。
- `practitioner_learning_reviews` 记录 manager/admin 候选审计。
- `practitioner_learning_experiments` 生成 dry-run 实验队列。
- `practitioner_learning_scorecards` 和 `practitioner_learning_releases` 记录评分与发布审批。

本轮新增：

- 前端证据链反馈自动写入 `v17.evidence.learning_material.v1` payload。
- 案例沉淀自动带上 `learning_value` 与 `learning_tags`。
- 学习候选聚合展示 `learning_values / feedback_intents / learning_tags / boundary_tags`。

## 5. Guardrails

必须长期保持：

- 单条反馈不改参数。
- 多条反馈只生成学习候选，不改参数。
- 案例状态更新不改静态 benchmark 文件。
- `approved_for_experiment` 只代表准入 shadow run，不代表发布。
- scorecard 的 `promote` 必须同时通过 synthetic/practitioner benchmark 且无退化。
- admin 发布记录仍只留痕，当前不自动写配置。

## 6. Next Steps

1. 在证据链 UI 增加筛选：强证据、候选、反例、边界、需复核。
2. 在命理师账本中展示学习素材字段，方便运营筛选。
3. 把 accepted benchmark candidate 转入长期 practitioner benchmark 的人工导出流程。
4. 让 LLM Analyst 只基于这些结构化素材生成学习候选解释，不直接改 evidence 或参数。
