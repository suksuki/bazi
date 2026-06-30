# V40 Phase 28: Practitioner Calibration Loop

Date: 2026-06-30

## 目标

Phase 27 已经把命理师专业视角挂到 `SurfaceBundle.surfaces[calibration].practitioner_lens`，但它只是展示层。本阶段把命理师点击动作接入训练闭环：

```text
Practitioner Lens Action
  -> TrainingLabelEvent
  -> LocalOverlay
  -> Training / Evaluation material
```

## 边界

- 不改四柱、大运、流年、紫微事实。
- 不改当前 verdict / advice。
- 不写 V40 production weight。
- 不写 V30 状态。
- 只产生本次 reading 可用的局部 overlay 和后续训练标签。

## 动作映射

| 动作 | 标签 | 作用 |
| --- | --- | --- |
| `more_like_this` | `supports` | 命理师认为该信号更贴合当前盘面或用户反馈 |
| `supporting_context` | `probe_helpful` | 作为辅助背景，不直接升格为断语 |
| `do_not_use_now` | `weakens` | 本次测算中降权或保留边界 |
| `ask_to_confirm` | `needs_probe` | 需要追问确认，不直接进入结论 |
| `user_mismatch` | `mismatch` | 用户反馈与信号不符，进入训练素材 |

## 新增模块

```text
v40/training/practitioner_lens.py
```

核心函数：

```text
build_practitioner_lens_action(...)
```

产出：

- `TrainingLabelEvent(source=practitioner_selection, local_only=true)`
- `LocalOverlay(expires_after_reading=true, global_update_allowed=false)`

## 新增 API

```text
POST /api/v40/calibration/practitioner-lens-action
GET  /api/v40/calibration/local-overlays
```

旧接口 `/api/v40/calibration/practitioner-selection` 暂时保留兼容，但新 surface 已指向 `practitioner-lens-action`。

## 新增数据表

```text
v40_local_overlays
```

该表只保存当前 reading 的局部校准覆盖，不是全局权重表。

## 测试

```text
tests/test_v40_phase28_practitioner_calibration_loop.py
```

覆盖：

- 命理师动作生成训练标签和局部 overlay。
- 普通用户 runtime 不能提交 practitioner lens action。
- schema / repository / API 只使用 V40 表和 V40 endpoint。

## 下一步

1. UI 接入 `practitioner-lens-action`，命理师点击后只局部更新专业视角。
2. Evaluation 将 `LocalOverlay + TrainingLabelEvent` 编译成可训练样本。
3. Release gate 再决定是否把大量本地反馈提升为候选全局权重。
