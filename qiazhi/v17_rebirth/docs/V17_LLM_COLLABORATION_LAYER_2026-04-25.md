# V17 LLM Collaboration Layer

日期：2026-04-25
状态：Design Draft
上位约束：
- [V17 产品需求宪法](V17_PRODUCT_REQUIREMENTS_CONSTITUTION.md)
- [V17 产品路线与进化策略](V17_PRODUCT_ROADMAP_AND_EVOLUTION_STRATEGY_2026-04-25.md)
- [V17 大脑重构方案 V2.0](V17_BRAIN_REFACTOR_V2_2026-04-20.md)
- [V17 Prompt Engine 重构方案](V17_PROMPT_ENGINE_REFACTOR_2026-04-20.md)

## 1. 核心判断

V17 的 LLM 不应只作为“断语生成器”存在。

当前产品已经把普通用户主体验收敛为“短断语 + 可展开证据”，这是正确的消费侧形态；但系统总纲里的 LLM 目标更大：LLM 应成为受治理的推理协作者，帮助系统和命理师审阅证据、发现冲突、整理反馈和生成学习候选解释。

因此，LLM 在 V17 中分为四个角色：

1. `Weaver`：把已通过的证据和裁决翻译成短断语。
2. `Reviewer`：审阅证据链，指出强证据、候选证据、过度断言和缺口。
3. `Arbiter`：对 `PLAN / CONFLICT` 批次给出结构化仲裁建议。
4. `Analyst`：把命理师反馈、错判案例和回归结果归因到参数族、Prompt 表达或候选升降级策略。

这四个角色共享一个底线：LLM 只产出 `proposal / review / suggestion / narrative`，不得直接修改物理层、插件参数、权威裁决或线上配置。

## 2. 角色边界

### 2.1 Weaver

当前已落地。

职责：
- 生成 `掐指一算` 的短断语。
- 根据用户语言输出中文、英文或韩文。
- 保持短、准、克制。

禁止：
- 把候选格局写成定论。
- 生成没有 evidence 的强判断。
- 用长篇文本替代证据链。

### 2.2 Reviewer

下一阶段优先落地。

职责：
- 审阅 `evidence_bundle`。
- 判断每条证据是否足以支撑强断语。
- 标记 `候选应降级 / 需命理师复核 / 可进入账本 / 证据不足`。
- 生成命理师可快速校验的审阅摘要。

输出必须是结构化 JSON，不直接改写 evidence、claim 或 verdict。

### 2.3 Arbiter

已有 Prompt Contract 基础。

职责：
- 对 `DecisionBatch` 输出 `KEEP / DROP / ESCALATE`。
- 对 `ConflictBundle` 输出 `resolution_type / preferred_arbiter / winner_claim_ids / dropped_claim_ids / confidence`。
- 帮助系统判断冲突应该交给 `system / llm / user` 哪一路。

禁止：
- 按单条 decision 反复调用。
- 对高风险冲突自动落地。
- 输出自由散文作为执行依据。

### 2.4 Analyst

职责：
- 读取命理师反馈、真实案例、scorecard 和 release 记录。
- 归因失败属于 `参数门槛 / 候选升降级 / evidence 质量 / Prompt 表达 / UI 理解` 哪一类。
- 生成学习候选的解释草案。

禁止：
- 用 LLM 自评证明 LLM 自己正确。
- 直接生成可上线配置补丁。

## 3. 数据合同

### 3.1 Evidence Review Contract

`task_type = evidence_chain_review`

输入：
- `session_id`
- `chart_fingerprint`
- `evidence_summary`
- `evidence_items`
- `verdict_text`（可选）
- `reviewer_role`

输出：
- `review_version`
- `overall_status`: `supported / mixed / insufficient / needs_practitioner`
- `items[]`
  - `evidence_id`
  - `review_action`: `keep_strong / keep_candidate / downgrade_to_candidate / ask_practitioner / needs_more_evidence`
  - `reason`
  - `confidence`
  - `risk_flags[]`
- `summary`
  - `strong_count`
  - `candidate_count`
  - `risk_count`
  - `practitioner_review_required`

### 3.2 学习信号边界

LLM review 可以进入：
- Prompt 表达策略候选。
- evidence/claim 的人工复核排序。
- 命理师账本的审阅辅助摘要。
- 学习候选的解释字段。

LLM review 不可以直接进入：
- 物理层权重。
- 插件默认参数。
- authority 主裁决。
- release approval。

## 4. UI 落点

第一阶段放在 `运势分析 -> 证据链`：

- 基础排盘页仍只保留轻量证据入口。
- 证据链 section 内增加 `AI 复核` 按钮。
- 默认返回结构化审阅草案，命理师可以据此继续确认、否定、收录案例。
- 后续可把复核结果保存进账本，但第一阶段只做运行时辅助，不持久化。

## 5. 实施顺序

1. 新增 `evidence_chain_review` Prompt Contract。
2. 新增命理师权限接口 `/v17/auth/practitioner-evidence-review`。
3. 在证据链 UI 接入 AI 复核入口。
4. 后续接入真实 LLM 调用、缓存、审计日志和 prompt signature。
5. 再把 review 结果纳入学习治理的辅助信号。

## 6. 验收

- 普通用户看不到专业复核入口。
- 命理师在证据链里能触发结构化复核。
- 复核结果明确区分强证据、候选证据、需命理师复核和证据不足。
- API 不修改任何参数或 evidence 原文。
- 测试覆盖 contract、权限和接口响应。
