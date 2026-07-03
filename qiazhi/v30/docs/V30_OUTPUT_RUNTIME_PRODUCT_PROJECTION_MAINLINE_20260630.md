# V30 Output Runtime Product Projection Mainline

更新时间：2026-06-30

## 背景

最近几轮 review 暴露出同一个核心问题：V30 已经有 `SignalRegistry`、`DecisionContract`、`DecisionVerdict`、`ConflictResolver`、训练验证和 LLM 表达，但用户页面仍可能看到工程语言，命理师校准也会把内部策略 key 直接投影出来。

本轮把 ChatGPT 定稿建议收敛为一个产品运行时层：

```text
Internal Runtime Objects
-> ProductProjection
-> Product Cards
-> LLMExpression
-> Acceptance / Repair / Salvage
-> FinalUserVisibleProjection
-> SurfaceOrchestrator
```

当前阶段先落 `ProductProjection + Product Cards + LeakageGuard`，不重写 Decision Engine，不改变四柱、大运、流年、规则事实，不让 LLM 做最终命理裁决。

## 设计原则

1. `DecisionEngine` 仍是 Verdict 生成者。
2. `LLM` 负责用户可读表达、对话措辞和必要解释，不生成命盘事实，不替代裁决。
3. `ProductProjection` 只把内部 Verdict、Conflict、Probe、Advice 转成产品可消费卡片。
4. `LeakageGuard` 是用户侧输出闸门，阻断工程 key、训练字段、debug 语言和 raw runtime status。
5. 命理师模式看到的是可校准选项，不是内部调参接口。
6. 普通用户看到结论、建议、必要分支和追问入口，不看到权重工程、策略 key 和训练信号。

## 模块计划

| 阶段 | 状态 | 任务 |
| --- | --- | --- |
| OR-0 | Done | 文档化 Output Runtime Product Projection 主线，写入文档索引和主线状态。 |
| OR-1 | Done | 新增 `product_contracts.py`：统一 ProductVerdictCard、BranchCard、ProbeCard、AdviceCard、ConversationSeed 契约。 |
| OR-2 | Done | 新增 `branch_cards.py`：把 ConflictResolver audit 转成去重、角色化、人话化 BranchCard。 |
| OR-3 | Done | 新增 `leakage_guard.py`：扫描产品投影字符串，阻断策略 key、训练/debug/工程语言泄漏。 |
| OR-4 | Done | 新增 `product_projection.py`：生成 decision workbench 的产品投影，并兼容旧 `verdict_cards/conflict_cards`。 |
| OR-5 | Done | 接入 `client_model` 和 `projection_contract`，让用户/命理师页面都带 ProductProjection 合约与 leakage scan。 |
| OR-6 | Done | 专项测试覆盖用户泄漏、分支去重、命理师动作语义和投影合约。 |
| OR-7 | Pending | 下一阶段接 `LLMExpressionPipelineV2 + AcceptanceV2 + Repair/Salvage`，让最终中文表达也走产品投影闸门。 |

## 产出边界

`ProductProjection` 允许：

- 改写展示文案。
- 合并重复分支。
- 选择用户/命理师可见字段。
- 把内部证据变成 `断 / 策 / 证` 或卡片列表。
- 给命理师提供“更像这个表现 / 作为辅助参考 / 暂不采用 / 需要追问确认”。

`ProductProjection` 禁止：

- 改四柱、大运、流年、出生资料。
- 改规则事实、候选分数和 Verdict。
- 把 LLM 输出直接当 Verdict。
- 把 `keep_both_branches...`、`value_of_information`、`training_target`、`claim_key` 等内部 key 投影给用户。

## 后续任务

1. 接入 LLM 表达二阶段：`DecisionVerdict -> ProductProjection -> LLMExpression -> AcceptanceV2 -> ProductProjectionLeakageGuard`。
2. 把页面最终结论和智能对话回答统一改为 ProductProjection 后表达。
3. Admin Console 增加 ProductProjection leakage audit 和 repair/salvage 统计。
4. Evaluation Spine 增加用户可读性、工程语言泄漏率、分支卡可校准率指标。
