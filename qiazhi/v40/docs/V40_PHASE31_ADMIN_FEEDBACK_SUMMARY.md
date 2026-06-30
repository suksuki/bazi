# V40 Phase 31: Admin Feedback Summary

Date: 2026-06-30

## 目标

Phase 30 已经可以把反馈编译为训练样本。本阶段把这条闭环放进独立 Admin Control Plane 的只读摘要里。

Admin 页面现在突出：

- `training_label_events`
- `local_overlays`
- `training_examples`

并展示最近的训练样本和本地 overlay。

## UI 变更

`/admin/v40` 新增：

```text
Training Feedback
```

该 section 从 `/api/v40/lab/summary` 读取：

- `counts.training_label_events`
- `counts.local_overlays`
- `counts.training_examples`
- `latest_training_examples`
- `latest_local_overlays`

## 边界

- Admin 页面仍然是独立服务。
- 只读展示，不启动训练。
- 不写生产权重。
- 不写 V30。
- 不把 Admin 功能塞回 `/v40/ui` 主系统。

## 测试

```text
tests/test_v40_phase31_admin_feedback_summary.py
```

覆盖：

- Admin 页面显示 Training Feedback。
- 页面包含 label / overlay / example 三类核心计数。
- 页面引用 latest training examples / local overlays。
- 页面不暴露 production write 文案。
