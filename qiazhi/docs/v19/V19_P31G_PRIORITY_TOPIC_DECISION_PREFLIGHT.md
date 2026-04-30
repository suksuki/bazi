# V19 P31G 高优先专题 Decision + Preflight

## 定位

P31G 接在 P31F 后面，对 review packet 内的 22 条低风险候选规则写入逐条 decision ledger，并运行 approval preflight。

本阶段只做：

- 记录 item-scoped `approve_candidate` decision。
- 运行 approval preflight。
- 产出可审批前置检查结果。

本阶段不做：

- 执行 approval。
- 改 proposal 状态。
- 生成 rule version。
- Rule DB engine activation。
- 运行时回答变更。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31g_priority_topic_decision_preflight
```

## 当前结果

- review packet items：22
- decision records：22
- approve candidate：22
- approval preflight records：1
- preflight ready items：22
- failed checks：0
- approval execution mutation：false
- proposal status mutation：false
- version mutation：false
- runtime mutation：false

## 审批边界

P31G 的 `approve_candidate` 只是智能预审候选，不等于批准：

- proposal 仍停留在 `validation_ready`。
- 只有 P31H 或后续受控执行阶段才能把 proposal 变为 `approved`。
- 即便 proposal approved，也仍需 version/release/runtime gate，不能直接影响回答。

## 后续

P31H 可以在 preflight 全绿时执行 controlled approval，把候选规则 proposal 状态推进到 `approved`；仍不做版本发布和运行时启用。
