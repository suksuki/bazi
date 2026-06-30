# V40 Phase 32: Training Example Replay

Date: 2026-06-30

## 目标

Phase 30 让反馈可以编译为 `TrainingExampleV2`。本阶段继续推进到可验证：

```text
TrainingExampleV2 + RuntimeResult
  -> TrainingExampleReplayResult
  -> replay score / recommendation
  -> persisted replay artifact
```

这一步回答一个关键问题：

```text
这条训练反馈能否被当前 runtime 找回、归因、回放？
```

## 新增合约

```text
TrainingExampleReplayResult
```

核心字段：

- `target_coverage_rate`
- `matched_target_ids`
- `missing_target_ids`
- `local_overlay_ref_count`
- `positive_label_count`
- `negative_label_count`
- `needs_probe_count`
- `feedback_alignment_score`
- `status`
- `recommendation`

## Replay 算法

Replay 会从 runtime 建立 target index：

- Signal
- Branch
- Verdict
- Advice
- Probe
- Product projection card
- Conversation seed
- Expression task/result
- Evidence refs / trainable targets

再与 `TrainingExampleV2.attribution_targets` 和每个 label 的 `target_ids` 对齐。

## 新增 API

```text
POST /api/v40/training/replay-example
GET  /api/v40/training/example-replays
```

## 新增表

```text
v40_training_example_replays
```

## 边界

- 不写 V30。
- 不写 V40 production weight。
- 不改 chart facts。
- 不改当前 verdict / advice。
- LLM 不参与 replay judge。
- 只有 replay 通过，才可作为候选训练材料进入下一层 batch/release gate。

## 测试

```text
tests/test_v40_phase32_training_example_replay.py
```

覆盖：

- target 存在时 replay passed。
- target 丢失时 replay review。
- API 可以持久化和查询 replay。
- schema / repository / API / manifest 只使用 V40 边界。

## 下一步

1. Admin/Lab 展示 replay 数量和最近 replay。
2. Replay batch summary 聚合多条 `TrainingExampleReplayResult`。
3. Candidate weight 只允许消费 replay passed 的训练样本。
