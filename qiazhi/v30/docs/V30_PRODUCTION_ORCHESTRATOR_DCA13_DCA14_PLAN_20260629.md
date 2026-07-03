# V30 Production Orchestrator DCA-13 / DCA-14 执行计划

更新时间：2026-06-29

## 本轮目标

本轮只执行第一阶段：

```text
DCA-13 Module Audit
DCA-14 Signal Registry V1
```

这是旁路审计，不改变当前测算结果：

- 不替换现有 `DecisionEngine`。
- 不改变 `DecisionVerdict`。
- 不改变 `FinalSynthesis`。
- 不改变用户侧 `reading_surface`。
- 不让 LLM 获得裁决权。

本轮只回答一个核心问题：

```text
每个模块到底产出了什么？
哪些产出进入了 Verdict / FinalSynthesis / UI？
哪些只在 runtime 中存在？
哪些模块可能是候选、孤岛、训练专用或调试专用？
```

## 架构修正

采纳本轮讨论后的六点修正：

- `BaziSignal` 使用 `V30Model`，不使用 dataclass。
- 原始 `BaziSignal` 只描述模块产出本身，不包含 `consumed_by / runtime_used / user_output_bound`。
- 消费关系由 `SignalUsageAudit` 和 `ModuleAuditEntry` 计算。
- 所有 `source_type / polarity / assertion_level_hint / topic / domain / status` 使用受控枚举或兼容映射。
- `RoleKey` 兼容现有 `guest / user / practitioner / analyst / admin / lab`。
- `StagePoint` adapter 可以存在，但默认只做 presentation/sidebar 审计，不作为 Decision Engine 输入。

## 新增模块

新增目录：

```text
v30/production/
  __init__.py
  contracts.py
  signal_registry.py
  adapters.py
  orchestrator.py
  module_audit.py
```

职责：

| 文件 | 职责 |
|---|---|
| `contracts.py` | 定义 `BaziSignal`、`SignalUsageAudit`、`ModuleAuditEntry`、`ProductionSidecar` 和受控枚举 |
| `signal_registry.py` | 注册、查询、分组、校验 signal |
| `adapters.py` | 将现有 `FeatureEvidence / DiagnosisClaim / DiagnosisPath` 等结构适配成 `BaziSignal` |
| `orchestrator.py` | 从 runtime payload 旁路构建 `ProductionSidecar` |
| `module_audit.py` | 计算 signal 使用情况、模块状态和推荐动作 |

## 第一阶段 Adapter 范围

先接入以下现有结构，不改原模块逻辑：

- `FeatureEvidence`
- `MatchedRule`
- `DiagnosisFeature`
- `DiagnosisPath`
- `DiagnosisPortrait`
- `DiagnosisClaim`
- `RankedDecision`
- `MacroDimensionSignal`
- `StagePoint`

## runtime 接入

在 runtime 返回前附加 production sidecar：

```text
runtime.question_plan.policy_effect.production_signal_registry
runtime.question_plan.policy_effect.production_usage_audit
runtime.question_plan.policy_effect.production_module_audit
runtime.question_plan.policy_effect.production_audit_summary
```

注意：

- 只新增旁路数据。
- 不改变 `answer_result`。
- 不改变 `central_reading_state.decision_verdicts`。
- 不改变 `final_synthesis`。

## 调试出口

新增只读 API：

```text
GET /api/v30/readings/{reading_id}/production-audit
```

返回：

- registry summary
- signal registry
- usage audit
- module audit
- production audit summary

该接口面向 Admin/debug，暂不进入普通用户 UI。

## 验收标准

1. smoke runtime 能正常创建。
2. `DecisionVerdict` 数量和 `assertion_level` 不因 sidecar 改变。
3. 每个 runtime 生成 `SignalRegistry`。
4. 每个 runtime 生成 `ModuleAudit`。
5. 审计能看到每个模块的 `produced_count / signal_count / output_bound_count`。
6. 审计能识别 `runtime_used` 但未进入用户结果的模块。
7. 审计能识别 presentation-only 的 `StagePoint`。
8. 所有关键分类字段使用受控枚举或兼容映射。
9. LLM 仍然只负责表达，不参与生产审计裁决。

## 后续阶段

本轮完成后，后续再进入：

```text
DCA-15 Signal-based DecisionCandidate Builder
DCA-16 AdviceEngine V1
DCA-17 OutputContract + UI Role Projection
DCA-18 Training Impact Trace
```

当前不跳步。

## 本轮执行结果

执行状态：已完成第一阶段最小落地。

新增代码：

- `v30/production/contracts.py`
- `v30/production/signal_registry.py`
- `v30/production/adapters.py`
- `v30/production/orchestrator.py`
- `v30/production/module_audit.py`
- `v30/production/__init__.py`

接入点：

- `v30/runtime.py`
  - 新增 `_attach_production_sidecar(runtime)`。
  - 初始 runtime、隐藏属性刷新、用户回答刷新后都会附加 production sidecar。
  - sidecar 写入 `question_plan.policy_effect`：
    - `production_sidecar`
    - `production_signal_registry`
    - `production_usage_audit`
    - `production_module_audit`
    - `production_audit_summary`
- `v30/api/app.py`
  - 新增只读接口：`GET /api/v30/readings/{reading_id}/production-audit`。
  - 该接口会现场用完整 `reading_surface` 和可选 `thinking_projection` 重建审计结果，不写库、不改命盘、不改 Verdict。

新增测试：

- `tests/unit/test_production_signal_registry.py`

当前 smoke 观察：

```text
production_signal_registry: ready
signal_count: 279
module_count: 8
DecisionVerdict count: 9
endpoint: /api/v30/readings/{reading_id}/production-audit 200
```

已验证：

```text
../.venv312/bin/python -m py_compile \
  v30/production/contracts.py \
  v30/production/signal_registry.py \
  v30/production/adapters.py \
  v30/production/module_audit.py \
  v30/production/orchestrator.py \
  v30/runtime.py \
  v30/api/app.py \
  tests/unit/test_production_signal_registry.py

../.venv312/bin/pytest \
  tests/unit/test_production_signal_registry.py \
  tests/unit/test_decision_centered_architecture.py -q
```

验证结果：

```text
8 passed
```

边界仍成立：

- `BaziSignal` 不包含 `consumed_by / runtime_used / user_output_bound`。
- `SignalUsageAudit` 单独计算消费状态。
- `ModuleAuditEntry` 单独汇总模块产出责任。
- `StagePoint` adapter 只作为 presentation/sidebar 审计信号，不作为 Decision Engine 输入。
- `DecisionEngine`、`DecisionVerdict`、`FinalSynthesis` 没有被 production sidecar 替换。
