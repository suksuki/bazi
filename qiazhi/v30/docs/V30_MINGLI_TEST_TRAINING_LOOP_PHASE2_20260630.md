# V30 命理测试与训练闭环 Phase 2

更新时间：2026-06-30

## 主线定位

Phase 1 已经把 Golden Case、Multi-Engine Training Example、ReadingQualityScore 和 MingliTrainingQualityGate 接成闭环。Phase 2 的目标是把“评分”变成“可迭代训练资产”：

```text
失败案例 -> Replay Queue
命理师标注 -> Training Label Projection
紫微案例 -> Ziwei Golden Case
现实回答 -> RealityProbe / Verdict Diff
```

本阶段仍然不改现有 `DecisionVerdict`，不写 production pointer，不让紫微参与最终裁决。

## Phase 2 范围

### 1. Failed Case Replay Queue

任何没有通过 Phase 1 Gate 的样本，必须进入 replay queue：

- 失败原因
- 优先级
- 建议重跑策略
- 需要修复的训练目标
- 是否禁止晋级

Replay Queue 是后续 synthetic replay 和真实命理师复核的入口。

### 2. Practitioner Label Projection

命理师标注不能改命盘事实，也不能直接改线上结论。它只形成训练投影：

- accepted / rejected verdict domains
- advice tags
- quality override
- correction notes
- trainable targets

这些投影后续用于策略优化、质量 diff 和 admin 回放。

### 3. Ziwei Golden Cases

紫微从 Phase 2 开始有独立 golden cases，但仍然只是 Domain Lens：

- 必须有 `ziwei_matched_rule_ids`
- 必须进入 SignalRegistry
- 必须可触发 probe candidate
- 决策权重仍为 0

测试目标不是“紫微断得准”，而是“紫微信号是否干净、可审计、能辅助追问”。

### 4. Reality Probe / Verdict Diff

现实回答与 Verdict 必须做 alignment/diff：

- user answer 支持哪些 domain
- 与当前 Verdict 是否一致
- 是否发现 contradiction
- 是否需要下一个 probe
- 是否生成 manifestation update

Reality Probe 影响显化权重和隐藏属性，不改 chart facts。

## 任务计划

- `MTL2-1`：新增 Phase 2 Markdown。
- `MTL2-2`：新增 Replay Queue 契约与 builder。
- `MTL2-3`：新增 PractitionerLabel 与 projection。
- `MTL2-4`：新增 Ziwei Golden Case 样例。
- `MTL2-5`：新增 RealityProbeVerdictDiff。
- `MTL2-6`：新增 Phase 2 Gate runner。
- `MTL2-7`：专项测试与文档索引更新。

本轮执行 `MTL2-1` 到 `MTL2-7`。

## 后续阶段

Phase 3：

- Replay Queue 接 synthetic replay gate
- Practitioner Label 接 Admin UI
- RealityProbe Diff 接真实用户对话链
- 518K shard 分布观察
- 策略 diff 和自动生效
