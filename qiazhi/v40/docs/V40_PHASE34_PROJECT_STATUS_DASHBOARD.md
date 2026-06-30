# V40 Phase 34: Project Status Dashboard

Date: 2026-06-30

## 目标

让 V40 完成度成为系统内可观察状态，而不是口头估算。

本阶段新增：

```text
GET /api/v40/project/status
GET /admin/v40/api/project-status
Admin V40 Completion panel
```

## 完成度口径

当前分四条主线：

| Domain | 含义 |
| --- | --- |
| architecture | V40 合约、runtime、engine、decision、output、training spine |
| user_beta | 用户侧 report-first、conversation-after、命理师模式 |
| training_validation | label / overlay / example / replay / replay batch 闭环 |
| v30_replacement | V30 shadow compare、迁移验收、真实案例回归 |

总体完成度按权重聚合：

```text
architecture 30%
user_beta 20%
training_validation 30%
v30_replacement 20%
```

## 实时证据

`project/status` 会读取 `lab_summary.counts`，把以下 runtime artifacts 作为实时证据：

- `runtime_records`
- `training_label_events`
- `local_overlays`
- `training_examples`
- `training_example_replays`
- `training_replay_batches`
- `evaluation_batches`
- `release_readiness`
- `shadow_compare_runs`

如果数据库暂时不可用，接口仍返回 roadmap 基础状态，但 evidence counts 为空。

## Admin

`/admin/v40` 顶部新增：

```text
V40 Completion
```

显示：

- overall completion percent
- current phase
- four domain progress bars
- next step per domain

页面每 15 秒自动刷新一次。

## 边界

- 只读状态。
- 不写 V30。
- 不写 V40 production weight。
- 不启动训练。
- 不把完成度当成发布批准。

## 当前估算

Phase 34 完成后：

```text
overall: ~65%
architecture: ~84%
user beta: ~58%
training validation: ~64%
v30 replacement: ~45%
```

## 下一步

Phase 35:

```text
approved replay batch -> candidate weight prerequisite
```
