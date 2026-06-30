# V40 Phase 39: User Surface Beta Readiness

Date: 2026-06-30

## 目标

把用户侧页面从“功能存在”提升为“可验收的 beta surface”。

新增：

```text
GET /api/v40/surface/beta-readiness
User UI surface readiness indicator
```

## Beta 验收项

用户侧必须同时满足：

- report first：先形成测算报告。
- conversation after report：智能对话在报告之后独立发生。
- feedback to training：用户反馈进入训练素材。
- practitioner calibration：命理师校准只影响训练素材。
- admin separated：主系统页面不暴露 Admin。
- no silent fallback：模型不可用时明确提示，不伪造智能表达。

## 页面呈现

页面只展示用户能理解的轻状态：

```text
报告优先 · 可继续追问
```

不把工程检查项、训练事件名、production weight 等控制面语言暴露给普通用户。

## 边界

- readiness endpoint 只读。
- 不写 V30。
- 不写 V40 production。
- 不启动训练。
- 不激活权重。

## 完成度更新

Phase 39 后，V40 当前估算：

```text
overall: ~75%
architecture: ~92%
user beta: ~68%
training validation: ~76%
v30 replacement: ~55%
```

## 下一步

Phase 40:

```text
V30 replacement readiness closeout
```
