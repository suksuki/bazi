# V40-RC2 Policy Registry Persistence

Date: 2026-07-01

## 核心原则

V40 是命理高迭代系统，不是低容错工程审批系统。训练后的策略默认直接生效，让系统在真实反馈中快速变聪明；同时保留回滚点和 impact diff，保证试错后能补救。

简单说：训练后直接生效，发现偏差就用下一轮训练或回滚补救。

```text
default: train -> active immediately
guardrail: keep previous active registry + impact diff + rollback pointer
forbidden: mutate chart facts or let LLM become decision authority
```

## 本轮目标

把 BatchTrainerV1 生成的新策略从“响应里的临时对象”推进到 V40 当前有效策略：

```text
TrainingLabelEvent / TrainingAttribution
→ BatchTrainerV1
→ Active TrainablePolicyRegistry
→ v40_trainable_policy_registries
→ Admin read model
→ RuntimeResult.policy_version_used
```

## 已实现

新增：

```text
v40_trainable_policy_registries
POST /api/v40/training/policy-registries
GET /api/v40/training/policy-registries
GET /api/v40/training/policy-registries/active
BatchTrainerV1Request.persist_registry
RuntimeRequest.policy_version_used
RuntimeResult.policy_version_used
/admin/v40/api/policy-registries
```

## 生效与补救

`BatchTrainerV1Request.persist_registry=true` 是默认值。训练后：

- 新 `TrainablePolicyRegistry.active=true`。
- 旧 active registry 自动变为 history。
- 新 registry 保存 `previous_registry_id / previous_policy_version`。
- `TrainingImpactDiff` 默认保存，用于补救、复盘和回滚判断。
- runtime 默认读取当前 active policy version，写入 `policy_version_used`。

仍然禁止：

- 不改四柱、大运、流年、紫微信息等事实。
- 不让 LLM 参与训练决策。
- 不让 LLM 成为最终命理裁决者。

## 为什么重要

之前训练链路能产出候选策略，但候选策略没有进入长期存储，也没有成为当前 runtime 策略。现在每次训练可直接生效，同时 runtime 会记录 `policy_version_used`，后续 Acceptance Window 可以做：

```text
baseline policy
vs
active trained policy
```

并明确候选策略对 verdict / advice / probe / expression acceptance 的影响。

## 下一步

1. Acceptance Window 展示 `previous_policy vs active_policy` before/after diff。
2. Admin 支持从 replay batch 选择样本运行 BatchTrainerV1。
3. 增加一键回滚到 `previous_registry_id` 的补救动作。
4. 真实命例窗口验证 active policy 是否提高命理结果质量。
