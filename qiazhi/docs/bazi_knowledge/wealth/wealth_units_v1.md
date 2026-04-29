# Wealth Knowledge Units v1

This document is the human-readable source companion for the structured Bazi Knowledge Base seed.

Governance rules:

- Knowledge units are not runtime prediction rules.
- Knowledge units do not enter the Prediction Contract directly.
- Knowledge units may only generate feature mappings, sandbox rule candidates, or test cases.
- Sandbox candidates still require Rule Test Engine, Knowledge PR, reviewer approval, and activation before becoming active rules.
- Reviewed knowledge is immutable; changes require a new knowledge unit or deprecation.

Seed coverage:

- 财星强弱
- 财星透干 / 藏支
- 财星有根 / 无根
- 财库
- 财库冲开
- 财库被合
- 食伤生财
- 食伤太过泄身
- 官杀制约财富
- 印星克制食伤影响生财
- 比劫夺财
- 财旺身弱
- 身旺财弱
- 财官相生
- 大运引动财星
- 流年引动财库
- 合局导致财富稳定性变化
- 冲导致财富流动性变化
- 刑害导致财富风险
- 财在夫妻宫 / 家内家外位置影响财富来源

Canonical feature types:

- `wealth_strength`
- `wealth_vault_state`
- `wealth_vault_activation`
- `output_generate_wealth`
- `wealth_constraint`
- `peer_competition`
- `wealth_flow_activation`
- `wealth_stability`
- `wealth_risk`

## Core Wealth v1 reviewed units

The following five units are the canonical reviewed wealth cognition model.
They are intentionally small, composable, and feature-only. They do not produce
user conclusions and do not become active rules directly.

### Knowledge Unit: wealth.wealth_strength

Status: reviewed

Source: owner-reviewed classical bazi wealth model

Version: core_wealth_v1

#### Statement

财星代表资源获取与价值交换能力，其状态决定财富潜力基础。

#### Feature Mapping

- feature: `wealth_strength`
- inputs: `ten_god_mapping`, `root_strength`, `month_command`
- outputs:
- `wealth_strength_score (0-1)`
- `wealth_presence: none / latent / present / rooted / seasonally_supported`

#### Effect

- wealth_presence 越高 -> 财富潜力越高
- rooted / seasonally_supported -> 结构更稳定

#### Risk

- 财强身弱 -> 承载风险
- latent -> 机会难以转化

#### Uncertainty

- 依赖日主承载力
- 依赖结构引动

#### Conflict

- 印星抑制
- 比劫分夺

#### Confidence Prior

0.8

### Knowledge Unit: wealth.output_generate_wealth

Status: reviewed

Source: owner-reviewed classical bazi wealth model

Version: core_wealth_v1

#### Statement

食伤代表输出与创造，其与财的连接决定变现路径。

#### Feature Mapping

- feature: `output_generate_wealth`
- inputs: `ten_god_mapping`, `root_strength`, `strength_model`
- outputs:
- `output_strength_score`
- `output_to_wealth_link_strength`
- `conversion_path: direct / indirect / blocked / uncertain`

#### Effect

- output 上升 -> 赚钱机会增加
- conversion_path 决定收入方式

#### Risk

- 输出强但 blocked -> 有能力但无法变现
- 输出过旺 -> 泄身

#### Uncertainty

- 依赖财星是否存在
- 依赖结构支持

#### Conflict

- 印抑制输出
- 官杀限制表达

#### Confidence Prior

0.75

### Knowledge Unit: wealth.wealth_vault

Status: reviewed

Source: owner-reviewed classical bazi wealth model

Version: core_wealth_v1

#### Statement

墓库结构决定财富的储存、流动与释放方式。

#### Feature Mapping

- feature: `wealth_vault_state`
- inputs: `relation_hits`, `structure_effect_bundle`
- outputs:
- `vault_presence (true/false)`
- `vault_state: closed_storable / closed_inactive / opened_by_clash / locked_by_combination / blocked / conflicted`

#### Effect

- closed_storable -> 可积累
- opened_by_clash -> 流动性上升
- locked_by_combination -> 稳定性上升
- conflicted -> 不确定性上升

#### Risk

- 冲过强 -> 波动
- 合过强 -> 难变现

#### Uncertainty

- 合冲同时存在
- 依赖岁运触发

#### Conflict

- 冲 vs 合
- 多结构叠加

#### Confidence Prior

0.85

### Knowledge Unit: wealth.peer_competition

Status: reviewed

Source: owner-reviewed classical bazi wealth model

Version: core_wealth_v1

#### Statement

比劫代表同类竞争与资源分配机制。

#### Feature Mapping

- feature: `peer_competition`
- inputs: `ten_god_mapping`, `strength_model`
- outputs:
- `peer_strength`
- `competition_pressure`
- `resource_distribution_risk`

#### Effect

- competition_pressure 上升 -> 竞争增强
- 适度 -> 合作机会

#### Risk

- competition_pressure 高 -> 收入不稳定
- distribution_risk 高 -> 财富分散

#### Uncertainty

- 合作 vs 竞争方向

#### Conflict

- 财星强 -> 可抵消
- 官杀 -> 约束竞争

#### Confidence Prior

0.7

### Knowledge Unit: wealth.constraint_structure

Status: reviewed

Source: owner-reviewed classical bazi wealth model

Version: core_wealth_v1

#### Statement

官杀代表规则、约束与结构压力，对财富路径产生规范或限制作用。

#### Feature Mapping

- feature: `wealth_constraint`
- inputs: `ten_god_mapping`, `strength_model`
- outputs:
- `constraint_strength`
- `constraint_effects: restrict_flexibility / stabilize_risk / pressure_income / formalize_path`

#### Effect

- stabilize_risk -> 风险降低
- pressure_income -> 收入受限

#### Risk

- 约束过强 -> 收入压制
- 约束过弱 -> 风险增加

#### Uncertainty

- 官杀与日主关系
- 是否形成制化

#### Conflict

- 食伤冲官
- 印化官杀

#### Confidence Prior

0.75

## Wealth Rule Test Candidate v1

Scope:

- 仅面向以下 5 条 reviewed Core Wealth Units：
  - `wealth.wealth_strength`
  - `wealth.output_generate_wealth`
  - `wealth.wealth_vault`
  - `wealth.peer_competition`
  - `wealth.constraint_structure`
- 为每条知识单元创建 sandbox rule candidate（`candidate_state == "sandbox"`，`status == "experimental"`）。
- 为每条候选创建 1 条最小合成测试样例（`source = "synthetic"`）。
- 为每条候选创建 1 个 draft Rule Test Suite（`status="draft"`，`version="v1"`）。
- 不执行活跃化（`activate`）、不直接进入正式预测链路；仅按 `sandbox candidate -> test -> PR -> activate` 走标准序列。

## Wealth Knowledge Integration v1 (Calibration Only)

Scope:

- Wealth Domain 默认 `knowledge_mode="baseline_only"`，现有 production 行为不变。
- 实验模式 `knowledge_mode="kb_augmented"` 会把 5 条 reviewed Core Wealth Units 转成 `wealth_evidence`。
- KB evidence 标记为 `source="wealth_kb_calibration_v1"` 与 `experimental=true`。
- 输出包含 baseline vs kb_augmented 对比：
  - wealth_type before / after
  - evidence_count before / after
  - KB source 是否进入解释依据
- 该模式不创建 active rule、不替换 `bootstrap.wealth.baseline`、不直接写 ledger。

## Wealth KB Calibration v2

Scope:

- 继续使用 `knowledge_mode="baseline_only"` / `knowledge_mode="kb_augmented"` 做离线校准对比。
- 覆盖 12 个典型财富结构样本：
  - 财旺身弱
  - 身旺财弱
  - 食伤生财明显
  - 食伤有但无法转财
  - 财库存在但未打开
  - 财库被冲
  - 财库被合
  - 比劫强
  - 官杀强
  - 合冲同时存在
  - 无财星
  - 运势引动
- 每个样本输出 baseline 与 kb_augmented 对比：
  - wealth_type before / after
  - evidence before / after
  - kb_evidence_count
  - changed_fields
  - expected_direction
  - is_reasonable
- 该校准仅验证 KB evidence 是否符合命理方向，不创建 active rule、不替换 bootstrap rule、不进入 production。

Template for future units:

```markdown
# Knowledge Unit: wealth.example

## Source
- Type: classical / owner / experience
- Reference: human-reviewed note

## Statement
Short structured statement.

## Conditions
- Required observable facts

## Feature Mapping
- feature_type:
- input_requirements:
- detection_logic:
- output_fields:
- effect_direction:
- confidence_weight:
- uncertainty_weight:

## Effects
- wealth:
- income_stability:
- risk:

## Risk
- Known risk factors

## Uncertainty
- Missing assumptions

## Conflicts
- Conflicting structures

## Status
- draft / reviewed / deprecated
```
