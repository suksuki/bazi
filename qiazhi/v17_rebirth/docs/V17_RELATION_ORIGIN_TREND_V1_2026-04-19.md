# V17 关系来源趋势验收看板（自动化）

生成时间：2026-04-19

目的：在不触发现有规则时，验证关系类插件的 `origin_type` 与 `match_ratio` 在变体压力下是否符合先验优先级口径（`natal` > `luck_background` > `mixed` > `runtime_pair` > `flow_trigger` > `flow_only` > `unknown`），用于关系来源层的回归与自动化告警。

## 执行命令

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi
python3 v17_rebirth/scripts/relation_origin_trend_report.py
```

## 最近一次快照

- case_count: `50`
- relation_fact_total: `92`
- priority_violations: `0`

说明：本次快照未检测到高优先级来源命中度低于低优先级来源的回归告警。

## 生成协议

脚本采集两组合成样本并生成变体：

- `v17_rebirth.scripts.calibrate_synthetic_relation_cases.CASES`
- `v17_rebirth.scripts.calibrate_synthetic_sanhe_cases.CASES`

对每个样本输出 2 组强度变体（0.95、1.05）并按 index 加入来源改写变体（`natal` / `luck_background` / `flow_trigger`），用于验证来源口径是否稳定。

## 关键检查项

- `origin_summary`：按来源统计命中数、占比、平均/最大 `match_ratio` 与来源乘子
- `plugin_distribution`：按插件统计命中数与平均/最大 `match_ratio`
- `compliance.priority_violations`：检测是否出现同插件内高优先级来源 `match_ratio` 持续低于低优先级来源

## 后续接入建议

1. 将该脚本接入 `v17_rebirth/scripts/run_automated_tests.sh` 的后续“关系口径”阶段（可选）
2. 在后续新增关系类插件（六合、六冲、六害、六合神煞等）后，把测试目录下新增样本补充进两个 `CASE` 源集合
3. 将 `violation_count>0` 作为 `CI` 失败条件之一
