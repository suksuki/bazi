# V40 Phase 7: Lab Read Model And Artifacts

更新时间：2026-06-30

## 目标

让 V40 的训练验证资产可以被 Admin/Lab 控制面和脚本稳定消费。

Phase 7 新增：

```text
GET /api/v40/lab/summary
scripts/v40_artifact_cli.py
data/golden_cases/seed_career.json
```

## Lab Summary

`/api/v40/lab/summary` 返回 V40 侧状态：

```text
runtime_records
evaluation_cases
evaluation_runs
training_label_events
training_impact_diffs
shadow_compare_runs
release_gates
```

以及最近的：

```text
latest_evaluation_runs
latest_training_impacts
latest_release_gates
```

它只读 V40 control-plane 状态，不读 V30，不写生产。

## Artifact CLI

导入 golden case：

```bash
python scripts/v40_artifact_cli.py import-cases --path data/golden_cases/seed_career.json
```

导出最近 evaluation cases：

```bash
python scripts/v40_artifact_cli.py export-cases --path /tmp/v40_cases.json --limit 100
```

查看 Lab summary：

```bash
python scripts/v40_artifact_cli.py lab-summary
```

## Seed Golden Case

第一条 seed 聚焦事业问题：

```text
今年事业适合稳定发展还是转型突破？
```

它要求系统输出：

```text
事业判断
稳定 / 突破边界
行动建议
风险规避
```

并禁止：

```text
保证升职发财
一定转型成功
```

## 下一阶段

Phase 8 已进入：

1. Synthetic case runner；
2. 多样本 batch evaluation；
3. 聚合 MetricSummary；
4. Candidate weight version 草案进入后续阶段；
5. Admin Console 独立前端读取 `/api/v40/lab/summary` 进入后续阶段。
