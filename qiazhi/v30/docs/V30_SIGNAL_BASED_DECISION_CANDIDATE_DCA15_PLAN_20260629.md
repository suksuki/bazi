# V30 DCA-15 Signal-Based DecisionCandidate Builder 执行计划

更新时间：2026-06-29

## 本轮目标

DCA-15 的目标是让 `DecisionCandidate` 开始感知 `Signal Registry`，但本轮只执行兼容模式：

```text
DiagnosisClaim
-> BaziSignal
-> signal-aware DecisionCandidate
-> DecisionVerdict
```

本轮不改变现有裁决结果：

- 不改变 claim score。
- 不改变 candidate 排序。
- 不改变 `DecisionVerdict` 数量。
- 不改变 `assertion_level`。
- 不让 Signal Registry 直接替代 Decision Engine。

本轮只是让每个 `DecisionCandidate` 能回答：

```text
我来自哪些 signal？
这些 signal 属于哪些 source_type/source_module？
是否已经绑定 DiagnosisClaim signal？
是否已经有 path / portrait / rule / ranked decision 等旁证？
兼容模式下是否修改了分数？
```

## 新增能力

新增：

```text
v30/production/candidate_builder.py
```

职责：

- 从 `SignalRegistry` 中为每个 `claim_id` 找到相关 signal。
- 优先绑定 `DiagnosisClaim` signal。
- 继续把 `DiagnosisPath / DiagnosisPortrait / MatchedRule / RankedDecision / MacroDimension` 作为 supporting signal。
- 输出 `source_signal_ids` 和 `signal_source_summary`。
- 明确 `score_mutation_allowed = False`。

## DecisionCandidate 增补字段

在 `v30.brain.contracts.DecisionCandidate` 增补：

- `source_signal_ids`
- `signal_source_summary`
- `candidate_builder`

这些字段只用于审计和下一阶段迁移，不改变现有候选结构的核心字段。

## DecisionEngine 增补

`build_decision_result(...)` 增补可选参数：

```python
signal_registry: dict[str, object] | None = None
candidate_builder_mode: str = "compatibility"
```

兼容模式下：

```text
DecisionCandidate.confidence 仍来自 claim_scores
DecisionCandidate.score_components 仍来自原逻辑
DecisionCandidate.evidence_refs 仍来自原逻辑
SignalRegistry 只补充 source_signal_ids / signal_source_summary / builder trace
```

## Central Reading State 接入

`build_central_reading_state(...)` 在调用 `build_decision_result` 前，基于现有 diagnosis 和 ranked decisions 构建一份 decision-facing signal registry：

```text
diagnosis -> BaziSignal
ranked_decisions -> BaziSignal
build_signal_registry
build_decision_result(..., signal_registry=registry)
```

这份 registry 只服务 DCA-15 candidate binding。完整 production sidecar 仍由 runtime 后置旁路生成。

## 验收标准

1. 现有 DCA 测试不退化。
2. smoke runtime 的 `DecisionVerdict` 数量保持不变。
3. `DecisionCandidate` 中出现 `source_signal_ids`。
4. `DecisionCandidate.candidate_builder.score_mutation_allowed` 为 `False`。
5. `DecisionEngineResult.candidate_builder_summary.mode` 为 `compatibility`。
6. `DecisionVerdict.trace` 能看到 signal-aware candidate 的摘要。
7. LLM 仍然不能覆盖 Verdict。

## 下一阶段

DCA-15 后续增强模式再做：

```text
Signal Registry -> Candidate Builder 聚合权重
ConflictResolver 独立化
rule/path/portrait/macro signals 逐步参与 candidate confidence
命理师选择反馈进入 branch weight
```

当前不做这些。

## 本轮执行结果

执行状态：DCA-15 兼容模式已完成。

新增代码：

- `v30/production/candidate_builder.py`

更新代码：

- `v30/brain/contracts.py`
  - `DecisionCandidate` 增补 `source_signal_ids / signal_source_summary / candidate_builder`。
  - `DecisionEngineResult` 增补 `candidate_builder_summary`。
- `v30/brain/decision_engine.py`
  - `build_decision_result(...)` 增补可选 `signal_registry` 和 `candidate_builder_mode`。
  - 兼容模式下仍使用原 `claim_scores` 作为 confidence 和排序来源。
  - Verdict trace 增补 signal-aware candidate 摘要。
- `v30/brain/reading_engine.py`
  - 在构建 `DecisionResult` 前，根据 `diagnosis + ranked_decisions` 创建 decision-facing signal registry。
  - `CentralReadingState` 增补 `decision_signal_registry` 和 `candidate_builder_summary`。
- `v30/production/__init__.py`
  - 导出 `build_signal_candidate_support`。

新增测试：

- `tests/unit/test_signal_based_decision_candidate_builder.py`

当前 smoke 观察：

```text
DecisionVerdict count: 9
candidate_builder_summary.mode: compatibility
decision_signal_registry.signal_count: 239
claims_with_direct_signal_count: 80
first_candidate.source_signal_ids: 90
score_mutation_allowed: False
score_mutated: False
```

已验证：

```text
../.venv312/bin/python -m py_compile \
  v30/brain/contracts.py \
  v30/brain/decision_engine.py \
  v30/brain/reading_engine.py \
  v30/production/candidate_builder.py \
  tests/unit/test_signal_based_decision_candidate_builder.py

../.venv312/bin/pytest \
  tests/unit/test_signal_based_decision_candidate_builder.py \
  tests/unit/test_decision_centered_architecture.py \
  tests/unit/test_production_signal_registry.py -q
```

验证结果：

```text
11 passed
```

只读 API smoke：

```text
POST /api/v30/readings -> 200
GET /api/v30/readings/{reading_id} -> DecisionVerdict 9, builder compatibility
GET /api/v30/readings/{reading_id}/production-audit -> 200, signal_count 279
```

边界仍成立：

- Signal Registry 只绑定 candidate，不改 score。
- `DecisionCandidate.confidence` 仍来自 `claim_scores`。
- `DecisionVerdict` 数量和 assertion level 不因 DCA-15 兼容模式改变。
- LLM 仍不能覆盖 Verdict。
- 完整 production sidecar 仍在 runtime 后置旁路生成。

## 后续增强追记

2026-06-29 追记：DCA-15 的 `ConflictResolver 独立化` 已完成基础落地，详见 `V30_CONFLICT_RESOLVER_DCA15_ENHANCEMENT_PLAN_20260629.md`。

当前新增：

- `v30.brain.conflict_resolver`
- `DecisionEngineResult.conflict_resolver_summary`
- `DecisionEngineResult.conflict_resolver_audit`
- `CentralReadingState.conflict_resolver_summary`
- `CentralReadingState.conflict_resolver_audit`

仍保持 compatibility：

- 不改 candidate score。
- 不改 Verdict 数量。
- 不让 Signal Registry 或 LLM 直接替代 Decision Engine。
- 当前组合专项测试更新为 14 passed。
