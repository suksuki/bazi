# Qiazhi 审计字段速查表

适用范围：`/api/v1/analyze-seed`、`/api/v1/final-verdict`、`StreamBoard` 审计侧栏。

## 1) Physics 链路（analyze-seed）

- 后端返回：`physics_tensor.audit_log`
  - `skill_id`
  - `skill_version`
  - `rule_version`
  - `param_version_id`
  - `trace`
- 后端返回：`physics_tensor.confidence`（`0.0~1.0`）
- 后端返回：`physics_tensor.evidence`（字符串数组）
- 后端返回：`physics_tensor.meta.runtime_physics_config`（请求级热注入后的生效参数）

前端映射：

- `useStreamBoardController` -> `physicsAudit`
- `useStreamBoardController` -> `physicsConfidence`
- `useStreamBoardController` -> `physicsEvidence`
- `StreamBoard` -> `Lab Console`（前端滑块配置，随请求进入 `physics_config`）
- `AuditSidebar` 摘要行：
  - `param: ...`
  - `physics confidence: ...`

## 2) Final Verdict 链路（final-verdict）

- 后端返回：`audit_log`
  - `skill_id`
  - `skill_version`
  - `rule_version`
  - `param_version_id`
  - `trace.generated_version_id`

前端映射：

- `generateFinalVerdict()` 返回 `auditLog`
- `onExecuteDecision()` 追加 Auditor 审计事件：
  - `final_verdict_version_id`
  - `skill_id`
  - `rule_version`
  - 其余 `audit_log` 字段

## 2.1 Blind Work 链路（L2）

- 后端返回：`work_vector`
  - `work_vectors[]`：
    - `type`, `detail`, `direction`
    - `tomb_state`, `tomb_lock_rate`, `potential_energy_locked`
    - `unlock_source`, `unlock_confidence`, `unlock_failed`
    - `released_energy`, `unlock_gain`, `backfire_risk`
    - `risk_factor`, `expected_work`, `net_effect`
  - 汇总字段：
    - `potential_energy_locked`
    - `released_energy`
    - `unlock_gain`
    - `backfire_risk`
    - `risk_ratio`
    - `work_expectation`
    - `net_effect`
    - `morphing_hints`

前端映射：

- `generateFinalVerdict()` 返回 `workVector`
- `DecisionInbox` 展示“盲派做功链路图（L2）”：
  - `触发 -> 释放 -> 损耗 -> 净值`
  - 净值为正显示青蓝色，净值为负显示暗橙色
  - `unlock_failed` 为真时显示断裂链路提示
- `TenGodNumericList` 展示墓库状态标签：
  - `[Locked xx%]`（来自 `Lab Console.TOMB_LOCK_RATE`）
  - `[Released]`（当 `work_vector.released_energy > 0`）

## 2.2 Structure Candidates V0（L2 收割起手式）

- 后端返回：`structure_candidates_v0`
  - `self_abs`
  - `root_score`
  - `candidates[]`（`name/state/match_score/morphing_hints/reason`）
  - `hud`（`stable_pct/follower_pct/leap_pct`）

前端映射：

- `generateFinalVerdict()` 返回 `structureCandidatesV0`
- `DecisionInbox` 展示“格局态射仪表盘（V0）”：
  - 正格倾向 %
  - 从格倾向 %
  - 跃迁倾向 %

## 2.3 Structure Final Decision V0（L2 终审）

- 后端返回：`structure_final_decision_v0`
  - `primary_structure`
  - `primary_structure_humanized`
  - `primary_structure_status`
  - `decision_confidence`
  - `logical_reasoning_chain[]`
  - `rollback_triggers[]`
  - `stability_risk`
  - `utility_god[]`
  - `obstacle_god[]`
  - `climate_adjustment`

前端映射：

- `generateFinalVerdict()` 返回 `structureFinalDecisionV0`
- `DecisionInbox` 展示 “L2 格局终审结果（V0）”：
  - 格局名（主标题）
  - 置信度进度条
  - 理由链
  - 回滚触发器清单

## 2.4 Nomenclature Thresholds（命名阈值协议）

- `STRONG_STRUCTURE` 命名优先级（由高到低）：
  - `Self_Abs > 20` 且 `heterogeneous_abs <= 1.0` 且 `Work_Net >= 1.0`
    - `从旺/专旺格`
  - `Self_Abs > 15` 且 `month_deity == 比肩`
    - `建禄格（气盈格）`
  - `Self_Abs > 15` 且 `month_deity == 劫财`
    - `月劫格（争夺态）`
  - `Self_Abs > 5` 且 `Work_Net < 1.0`
    - `身强无依格`
- 异类干扰审计（Heterogeneous Interference Audit）：
  - 当异类（财/官/食伤）`Abs > 1.0` 时，必须拦截“专旺”命名，回落到“身强正格/身强无依”路径。

## 3) 审计闭环检查清单

- `analyze-seed` 必含：`physics_tensor.confidence` + `physics_tensor.evidence`
- `final-verdict` 必含：`audit_log`
- `final-verdict` 建议含：`work_vector`（L2 做功审计）
- 若 `backfire_risk > unlock_gain * 0.5`：应出现 `[DANGEROUS_TURBULENCE]`
- `AuditSidebar` 不展开 JSON 时可看到：
  - physics 置信度摘要
  - final verdict 版本与规则版本摘要
