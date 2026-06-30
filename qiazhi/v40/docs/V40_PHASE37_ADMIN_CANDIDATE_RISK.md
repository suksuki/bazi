# V40 Phase 37: Admin Candidate Risk Read Model

Date: 2026-06-30

## 目标

把候选权重从“原始列表”变成 Admin 可判断的发布风险摘要。

Phase 37 新增：

```text
GET /admin/v40/api/weight-risk
Admin Candidate Risk panel
```

## 为什么需要

Phase 35 已经能从 replay batch 登记 candidate weight。
Phase 36 已经能用 evaluation batch + replay batch 生成 release readiness。

但 Admin 如果只看到三张表：

```text
weights
readiness
activation reviews
```

仍然不知道：

- 这个候选权重来自哪次训练。
- 它有没有匹配到 readiness。
- readiness 是 approve / review / reject。
- 有没有 rollback version。
- 下一步能否进入显式激活审核。

Phase 37 把这些合成一个只读 read model。

## 风险等级

```text
ready
review
blocked
```

规则：

- readiness 匹配且 approve，并且有 `rollback_version_id` -> `ready`
- readiness 未匹配、仍需复核或缺 rollback -> `review`
- readiness reject / rollback -> `blocked`

## 输出字段

每个 candidate record 包含：

```text
weight_version_id
source_training_run_id
release_gate_id
active
rollback_version_id
readiness_id
readiness_recommendation
risk_level
reasons
next_action
```

## 边界

- Admin read model 只读。
- 不激活候选权重。
- 不写 V40 production。
- 不写 V30。
- 不改 chart facts。

## 完成度更新

Phase 37 后，V40 当前估算：

```text
overall: ~71%
architecture: ~90%
user beta: ~60%
training validation: ~74%
v30 replacement: ~48%
```

## 下一步

Phase 38:

```text
V30 shadow compare 扩大到真实运行样本，并把迁移风险纳入完成度。
```
