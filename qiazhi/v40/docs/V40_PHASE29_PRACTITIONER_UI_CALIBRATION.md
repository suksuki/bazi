# V40 Phase 29: Practitioner UI Calibration

Date: 2026-06-30

## 目标

Phase 28 已经提供命理师校准动作 API。本阶段把它接入 `/v40/ui`：

```text
普通用户：只看报告、反馈、继续追问
命理师：在报告后额外看到校准面板
```

## UI 原则

- 主流程仍然是 report first。
- 智能对话仍然是独立 follow-up，不嵌入测算步骤。
- 命理师校准只在 `role_key=practitioner` 的 runtime 下显示。
- 点击校准动作不会重跑测算、不会刷新报告、不会改当前 verdict。
- 校准动作只调用 `POST /api/v40/calibration/practitioner-lens-action`。

## 交互

命理师模式下，页面展示最多 6 条可校准目标：

- 紫微旁路信号。
- 分支候选卡。

每条目标支持：

- 采为主断。
- 作为辅助。
- 暂不采用。
- 需要追问。
- 用户反馈不符。

提交后保存：

```text
TrainingLabelEvent(local_only=true)
LocalOverlay(expires_after_reading=true)
```

## 边界

- 不显示 Admin 功能。
- 不显示全局权重操作。
- 不显示数据库或训练工程语言。
- 不写 V30。
- 不写 V40 production weight。

## 测试

```text
tests/test_v40_phase29_practitioner_ui_calibration.py
```

覆盖：

- `/v40/ui` 暴露 practitioner role 选择。
- 页面包含 practitioner calibration panel。
- 页面调用 `practitioner-lens-action`。
- 页面没有暴露 Admin / production weight 操作入口。
