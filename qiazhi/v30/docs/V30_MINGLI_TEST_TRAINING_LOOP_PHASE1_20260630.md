# V30 命理测试与训练闭环 Phase 1

更新时间：2026-06-30

## 主线定位

当前系统已经有中枢大脑、Decision Engine、Signal Registry、Dialogue Chain、Multi-Engine Runtime 和紫微 Domain Lens。下一阶段不继续堆 UI，也不继续加新玄学模块，而是聚焦：

```text
命理测试是否能稳定产出
训练样本是否能反映真实命理质量
训练 Gate 是否能判断系统有没有变聪明
```

本阶段目标是把“会跑”推进到“可测、可训、可验证”。

## 当前问题

- 训练系统已经能存 `BrainTrainingExample`，但它偏中枢决策策略，不足以评价命理断语质量。
- Multi-Engine 已能汇总 Bazi / Ziwei / RealityProbe，但缺少训练样本 Builder，把 engine 贡献和最终 verdict 绑定起来。
- 命理质量还没有独立评分：结构、用神、财富、事业、关系、健康、时运、证据链、建议、过度断言、模板风险都需要评分。
- Golden Case 还没有成为主线输入，因此训练无法明确“这次测算到底对不对”。

## Phase 1 范围

本轮只做命理测试与训练闭环的第一层：

```text
Golden Case
-> Multi-Engine Run
-> Engine Training Example
-> Reading Quality Score
-> Mingli Quality Gate
```

暂不做：

- 大规模 518K full run
- Admin UI
- 自动写 production pointer
- 改动现有 DecisionVerdict
- 让紫微参与最终裁决

## 契约

### MingliGoldenCase

每个案例必须记录输入问题、目标领域、期望 Verdict 领域、期望建议方向、禁止断语、需要的 engine、可选紫微 rule id、可选现实探针回答和质量阈值。

Golden Case 是训练和验证的“试卷”，不是线上策略。

### EngineTrainingExample

把一次 Multi-Engine 测算产物整理成训练样本：

- EnginePlan
- 每个 engine 产出了多少 facts / features / signals / probes
- SignalRegistry 汇总
- DecisionVerdict 摘要
- ReadingQualityScore
- trainable targets
- blocked targets

训练样本允许训练权重、阈值、问题策略、表达质量，但禁止训练 chart facts、历法转换、排盘和 LLM 造事实。

### ReadingQualityScore

第一版评分维度：

- engine_signal_coverage
- verdict_domain_alignment
- evidence_binding
- advice_actionability
- forbidden_assertion_safety
- template_risk
- overclaim_risk
- reality_probe_alignment
- ziwei_sidecar_alignment

### MingliTrainingQualityGate

Gate 负责判断一轮命理训练是否可进入下一阶段：

```text
case_count >= min_case_count
average_quality >= threshold
failed_cases == 0 或可解释
chart_fact_mutation_allowed == False
production_policy_write_allowed == False
```

## 任务计划

- `MTL-1`：新增命理 Golden Case 契约和 Phase 1 样例库。
- `MTL-2`：新增 Multi-Engine Training Example Builder。
- `MTL-3`：新增 ReadingQualityScore。
- `MTL-4`：新增 MingliTrainingQualityGate。
- `MTL-5`：专项测试覆盖 golden cases、builder、quality score、gate。
- `MTL-6`：文档索引和主线状态同步。

本轮执行 `MTL-1` 到 `MTL-6`。

## 后续阶段

Phase 2：

- 接真实命理师标注
- 接 Admin 训练页 engine contribution / failed case diff
- 接 Ziwei golden cases
- 接 Reality Probe answer-verdict diff

Phase 3：

- 小样本 real replay
- synthetic replay gate
- 518K shard distribution gate
- 策略 diff 和自动生效
