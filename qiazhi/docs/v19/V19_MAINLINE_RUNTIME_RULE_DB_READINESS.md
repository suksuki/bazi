# V19 Mainline Runtime Rule DB Readiness

## 目标

把运行时 Rule DB 中已经入库但尚未启用 adapter 的规则，按主线推进需要分成四类：

- `synthetic_gate_candidate`：低风险、结构事实完整、置信度足够，下一步进入合成门禁验证。
- `shadow_eval_candidate`：可用于影子评估，但暂不进入启用候选。
- `adapter_fact_gap`：缺少结构化事实或输入契约，需要先补 adapter facts。
- `blocked`：风险过高或归档边界，不进入运行时启用链路。

## 范围

这是只读审计，不启用规则，不修改 Rule DB，不改变用户回答。

## 主线位置

当前主线链路变为：

```text
知识库草案
→ Rule DB 入库
→ Rule Graph 路由
→ Runtime Rule DB readiness audit
→ 合成门禁验证
→ 可控启用 / 影子评估 / 回滚
```

## 合成验证要求

每条机制默认最少 8 个样本：

- 3 个正例
- 3 个反例
- 1 个时间层干扰例
- 1 个藏干或来源层干扰例

复杂机制可扩展到 10-12 个样本。

## 结果

新增：

- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_readiness_audit`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_readiness_regression`
- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_synthetic_gate_queue`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_synthetic_gate_queue_regression`
- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_synthetic_eval_dataset`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_synthetic_eval_regression`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_synthetic_route_regression`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_answer_guardrail_regression`
- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_controlled_activation_plan`
- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_rollback_manifest`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_controlled_activation_regression`
- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_isolated_canary_plan`
- `v19.synthetic_validation.rule_db_readiness.build_runtime_rule_db_isolated_canary_eval_dataset`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_isolated_canary_trial`
- `v19.synthetic_validation.rule_db_readiness.run_runtime_rule_db_isolated_canary_release_regression`

回归测试覆盖：

- 已启用规则不重复进入候选
- R1 完整规则进入合成门禁候选
- R2 完整规则进入影子评估候选
- 缺结构事实进入 adapter facts 缺口
- 高风险规则进入阻断
- 每个合成门禁候选生成 8 个验证样本槽位

## 合成门禁队列

`build_runtime_rule_db_synthetic_gate_queue` 会把就绪候选转为 eval dataset 计划：

- 3 个 `positive`
- 3 个 `negative`
- 1 个 `time_interference`
- 1 个 `hidden_source_interference`

这些样本只是验证槽位，不会自动判定通过，也不会启用规则。后续自动合成盘生成器会填充具体 chart fixture 与 expected signal。

## 合成 Eval Dataset

`build_runtime_rule_db_synthetic_eval_dataset` 会把门禁槽位转为可运行样本：

- `chart`：标准合成四柱 fixture
- `time_context`：时间层背景，时间干扰样本只作背景
- `expected_signal`：正例必须命中来源知识 ID
- `forbidden_signals`：非正例必须禁止来源知识 ID
- `condition_axes_expected`：标注每个条件轴是 satisfied 还是 blocked
- `forbidden_text`：禁止把结构信号写成发财、破财、必然、应期等断语

`run_runtime_rule_db_synthetic_eval_regression` 只验证数据集契约和门禁边界，`activation_updated_count` 固定为 0。

## 影子路由回归

`run_runtime_rule_db_synthetic_route_regression` 验证 eval dataset 的路由边界：

- 正例必须形成候选路由
- 非正例不能形成误命中路由
- 时间层干扰不能改写本命结构
- 藏干或来源层干扰不能替代透出/同层作用

这一步仍然不启用规则，只检查误触发和漏触发。

## 回答 Guardrail 回归

`run_runtime_rule_db_answer_guardrail_regression` 在影子路由通过后检查回答边界：

- 正例回答只能说明结构线索
- 非正例必须说明不能作为命中依据
- 禁止发财、破财、必然、应期等断语
- 禁止输出 `rule_id`、`signal_id`、`runtime_rule_db`、`engine_adapter_status` 等内部术语
- `activation_updated_count` 固定为 0

这一步用于进入受控启用计划前的最后文本门禁。

## 受控启用计划

`build_runtime_rule_db_controlled_activation_plan` 只生成计划，不启用规则：

- R0 进入 `ring0_canary`
- R1 进入 `ring1_internal`
- 每条候选必须通过 readiness、eval dataset、shadow route、answer guardrail
- 每条候选必须有 kill switch
- `engine_enabled_count`、`answer_mutation_count`、`activation_updated_count` 全部固定为 0

`build_runtime_rule_db_rollback_manifest` 为每条候选生成回滚项：

- 回滚动作：`disable_engine_and_remove_from_release_ring`
- 回滚后 engine 必须为 disabled
- 不修改回答，不修改运行时状态

`run_runtime_rule_db_controlled_activation_regression` 验证计划、回滚、ring 分配和 no-activation 边界。

## 隔离 Canary

`build_runtime_rule_db_isolated_canary_plan` 只选择 `ring0_canary` 候选进入隔离 canary：

- canary engine 只在内部信号路径启用
- production engine 固定 disabled
- 每个 canary 必须有 rollback 和 kill switch
- 不修改用户回答

`build_runtime_rule_db_isolated_canary_eval_dataset` 为每个 canary 生成 6 个样本：

- canary internal signal contract
- production route no-signal contract
- answer no-mutation contract
- forbidden text contract
- rollback execution contract
- kill switch contract

`run_runtime_rule_db_isolated_canary_release_regression` 验证隔离 canary 没有生产泄漏，且回滚/kill switch 都可用。
