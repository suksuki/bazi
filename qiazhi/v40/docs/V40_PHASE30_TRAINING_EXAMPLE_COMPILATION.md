# V40 Phase 30: Training Example Compilation

Date: 2026-06-30

## 目标

Phase 28/29 已经让命理师校准动作形成：

```text
TrainingLabelEvent
LocalOverlay
```

本阶段把这些反馈材料编译成真正可训练、可验证的 `TrainingExampleV2`。

```text
reading_id
  -> persisted TrainingLabelEvent
  -> persisted LocalOverlay
  -> TrainingExampleV2
```

## 新增 API

```text
POST /api/v40/training/example-from-reading
GET  /api/v40/training/examples
```

`example-from-reading` 会读取指定 `reading_id` 下已保存的标签和本地 overlay，并生成：

- `label_events`
- `attribution_targets`
- `expected_update.scope=local_overlay_first`
- `expected_update.local_overlay_refs`
- `expected_update.global_update_requires_release_gate=true`

## 新增数据表

```text
v40_training_examples
```

训练样本可保存、可查询、可回放，但不直接修改生产权重。

## 边界

- 不写 V30。
- 不写 V40 production weight。
- 不改 chart facts。
- 不改当前 verdict / advice。
- 没有标签时拒绝生成样本，避免空训练。

## 测试

```text
tests/test_v40_phase30_training_example_compilation.py
```

覆盖：

- builder 携带 local overlay refs。
- API 从已保存的 label / overlay 编译并持久化样本。
- schema / repository / API 只使用 V40 表和 V40 endpoint。

## 下一步

1. Admin/Lab 展示训练样本数量、最近样本和覆盖主题。
2. Evaluation batch 可以消费 `TrainingExampleV2` 做回放。
3. Release gate 决定是否把一批样本提升为 candidate weight。
