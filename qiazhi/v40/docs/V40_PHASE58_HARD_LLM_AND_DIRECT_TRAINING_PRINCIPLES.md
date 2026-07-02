# V40 Phase 58: Hard LLM And Direct Training Principles

Date: 2026-07-02

## Purpose

本阶段把两条产品级原则固化为 V40 runtime contract：

```text
1. 没有 LLM，产品运行时就是失败，不允许静默 fallback。
2. 训练和验证通过后直接调参系统并立即生效，不设置人工审核门。
```

这不是 UI 文案策略，而是运行时原则。V40 可以保留测试适配器、回滚和补救机制，但主产品链路不能把它们误用成“没有模型也能凑合输出”的替代路径。

## Hard Principle 1: LLM Is Required

用户侧报告、持续问答和智能表达默认必须走 Ollama / Gemma4：

- `NativeReadingReportRequest.execution_mode` 默认是 `ollama`。
- `ConversationTurnRequest.execution_mode` 默认是 `ollama`。
- `ExpressionFromRuntimeRequest.execution_mode` 默认是 `ollama`。
- `/v40/ui` 继续隐藏执行模式，不向普通用户暴露 provider/model/debug。
- 如果 Ollama/Gemma 不可用，API 返回 `503`，页面显示明确的 LLM 故障。
- 不生成本地模板替代文本。
- 不把 `local_expression_adapter` 当作产品 fallback。

LLM 的边界仍然不变：

```text
LLM 负责表达、对话语言、Thinking 展示和解释组织。
LLM 不创建四柱、大运、流年、紫微事实。
LLM 不改变 DecisionEngine 产出的 Verdict。
LLM 不写入训练权重或生产事实。
```

`local` 和 `provider_text` 只允许用于专项测试、离线合约测试或受控实验，不是产品运行时兜底。

## Hard Principle 2: Training Applies Immediately

V40 是高迭代命理系统。训练和验证的目标不是等审批，而是让系统快速吸收反馈：

```text
TrainingLabelEvent / Practitioner Calibration / Replay / Validation
  -> BatchTrainerV1
  -> active TrainablePolicyRegistry
  -> next runtime reads active policy
```

主路径规则：

- `BatchTrainerV1Request.persist_registry` 默认开启。
- `BatchTrainerV1Result.active_policy_applied` 默认为 `true`。
- 训练结果写入新的 active policy registry。
- 下一次 runtime 自动读取 active policy registry。
- 不需要人工审核、批准、发布按钮之后才生效。
- 事实型模块仍然不可训练：四柱、干支、十神基础映射、藏干、历法、大运流年、紫微宫位和星曜事实都不被改写。

保留的安全能力是事后补救，不是事前审核：

- 保留 previous registry。
- 保留 rollback pointer。
- 保留 TrainingImpactDiff。
- 保留风险摘要和回放证据。
- 质量变差时通过回滚或下一轮训练修正。

## Legacy Review Boundary

早期 Phase 10 / Phase 11 的 `WeightActivationReview` 和 `WeightActivationExecution` 属于历史显式激活链路，可作为 Admin/Lab 审计资料保留，但不再代表 V40 主训练路径。

新的主训练路径以 `BatchTrainerV1 + active TrainablePolicyRegistry` 为准。

## Runtime Acceptance Checklist

本阶段完成后，以下检查必须成立：

- 产品请求模型默认 `execution_mode=ollama`。
- 用户 UI 不出现 `execution_mode` 字段、provider/model 或本地适配器信息。
- LLM 失败时 API 直接 `503`，没有模板文本替代。
- `AcceptanceStatus` 不再包含 fallback 状态。
- BatchTrainerV1 输出 `approve`，并标记直接激活。
- BatchTrainerV1 API 默认持久化 active registry。
- 项目状态进入 Phase 58。

## Mainline Tasks

1. 固化产品 LLM 默认路径。
2. 清理 fallback 合约状态。
3. 固化训练后直接生效语义。
4. 更新 V40 spec、UI flow spec、README 和项目状态。
5. 增加专项测试，防止以后退回 local fallback 或审核门。

