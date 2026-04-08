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
    - `released_energy`, `unlock_gain`, `backfire_risk`
    - `risk_factor`, `expected_work`, `net_effect`
  - 汇总字段：
    - `unlock_gain`
    - `backfire_risk`
    - `risk_ratio`
    - `work_expectation`
    - `net_effect`

前端映射：

- `generateFinalVerdict()` 返回 `workVector`
- `DecisionInbox` 展示“盲派做功链路图（L2）”：
  - `触发 -> 释放 -> 损耗 -> 净值`
  - 净值为正显示青蓝色，净值为负显示暗橙色

## 3) 审计闭环检查清单

- `analyze-seed` 必含：`physics_tensor.confidence` + `physics_tensor.evidence`
- `final-verdict` 必含：`audit_log`
- `final-verdict` 建议含：`work_vector`（L2 做功审计）
- `AuditSidebar` 不展开 JSON 时可看到：
  - physics 置信度摘要
  - final verdict 版本与规则版本摘要
