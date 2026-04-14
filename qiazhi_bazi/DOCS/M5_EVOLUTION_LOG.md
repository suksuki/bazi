# M5 EVOLUTION LOG

## Phase-1 Bootstrap

- baseline_tag: `v12.92-GOLD-MASTER`
- source_table: `arbiter_preference_ledger`
- selection_rule: `preference_tier == GOLD`
- objective: 提取第一批「裁决者确认样本」用于 M5 偏好学习。

## GOLD Sample Features (Batch-1)

- lineage gate: 仅接受 `HTN_DRIVEN` 血统链路。
- sovereignty: `confirmed_facts.weight == 1.0` 视为最高优先证据。
- seed short-codes focus: `high_lock`, `marriage_clash`, `system_stress`。
- htn path completeness: 记录完整 `plan`，缺失路径样本降级为候选集。

## Monitoring

- dashboard API: `GET /api/v1/brain/m5-gold-stats`
- metrics:
  - `gold_total`
  - `recent_sync_time`
  - `top3_assimilated_seeds`
  - `current_entropy_reduction`

## Notes

- 本日志用于 M5 第一阶段「逻辑偏好提取」留痕；后续迭代追加批次统计与训练回放结果。
